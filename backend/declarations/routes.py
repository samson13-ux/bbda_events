"""Routes des declarations.

Tableau de bord organisateur, formulaire de nouvelle declaration avec
section Promotion publique, page de detail avec indicateur de visibilite
publique.
"""

import os
import uuid
from datetime import datetime

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename

from backend.auth.decorators import role_required
from backend.notifications.email_service import (
    notifier_confirmation_declaration,
    notifier_declaration_bloquee,
    notifier_nouvelle_declaration_bbda,
)
from backend.statuts import STATUTS_AFFICHAGE
from extensions import db
from models import Arriere, Declaration, ListeArtiste

from . import declarations_bp

COMPTES_BLOQUANTS = ("arriere", "bloque")
EXTENSIONS_AFFICHE = {".jpg", ".jpeg", ".png"}
# Signatures binaires (magic bytes) pour refuser les faux fichiers image.
SIGNATURES_AFFICHE = (
    (b"\xff\xd8\xff", ".jpg"),  # JPEG
    (b"\x89PNG\r\n\x1a\n", ".png"),  # PNG
)

CHAMPS_DECLARATION_REQUIS = (
    ("nom_demandeur", "Le nom du demandeur"),
    ("prenom_demandeur", "Le/les prénom(s) du demandeur"),
    ("telephone", "Le numéro de téléphone"),
    ("email", "L'adresse email"),
    ("nature_manifestation", "La nature de la manifestation"),
    ("nom_artiste_evenement", "Le nom de l'artiste ou de l'événement"),
    ("nom_salle", "Le nom de la salle / du lieu"),
    ("adresse", "L'adresse / secteur"),
    ("ville", "La ville"),
    ("date_evenement", "La date et l'heure de l'événement"),
    ("duree_heures", "La durée prévue"),
    ("capacite_accueil", "La capacité d'accueil"),
)


def _calculer_statistiques(declarations):
    """Compte total / nouvelles / en cours / quittances pour le tableau de
    bord (RM-004). 'En cours' regroupe tout statut non termine, c'est-a-dire
    tout sauf 'quittance_delivree'."""
    return {
        "total": len(declarations),
        "nouvelles": sum(1 for d in declarations if d.statut == "nouvelle"),
        "en_cours": sum(1 for d in declarations if d.statut != "quittance_delivree"),
        "quittances": sum(1 for d in declarations if d.statut == "quittance_delivree"),
    }


def _montant_arriere_actif(organisateur_id):
    """Somme des arrieres non regles de l'organisateur (RM-060 a RM-076)."""
    return (
        db.session.query(func.coalesce(func.sum(Arriere.montant_du), 0))
        .filter(Arriere.organisateur_id == organisateur_id, Arriere.statut == "en_attente")
        .scalar()
    )


@declarations_bp.route("/")
@role_required("organisateur")
def tableau_de_bord():
    """Espace personnel de l'organisateur connecte : statistiques et suivi
    de ses declarations (RM-002, RM-004)."""
    organisateur = current_user.organisateur
    declarations = (
        Declaration.query.filter_by(organisateur_id=organisateur.id)
        .order_by(Declaration.date_soumission.desc())
        .all()
    )

    return render_template(
        "declarations/tableau_de_bord.html",
        organisateur=organisateur,
        declarations=declarations,
        statistiques=_calculer_statistiques(declarations),
        montant_arriere=_montant_arriere_actif(organisateur.id),
        compte_bloque=organisateur.statut_compte in COMPTES_BLOQUANTS,
        statuts_affichage=STATUTS_AFFICHAGE,
    )


def _valider_declaration(donnees):
    """Valide les champs du formulaire de declaration et retourne la liste
    (eventuellement vide) des messages d'erreur (RM-011, RM-012)."""
    erreurs = []

    for champ, libelle in CHAMPS_DECLARATION_REQUIS:
        if not donnees.get(champ, "").strip():
            erreurs.append(f"{libelle} est requis.")

    if donnees.get("qualite") == "Autre" and not donnees.get("qualite_autre", "").strip():
        erreurs.append("Précisez la qualité du demandeur.")

    if donnees.get("entree") not in ("payante", "gratuite"):
        erreurs.append("Indiquez si l'entrée est payante ou gratuite.")

    natures_diffusion = donnees.getlist("nature_diffusion")
    if not natures_diffusion:
        erreurs.append("Sélectionnez au moins une nature de diffusion musicale.")
    if "autres" in natures_diffusion and not donnees.get("nature_diffusion_autre", "").strip():
        erreurs.append("Précisez la nature de diffusion « Autres ».")

    date_evenement = _parser_date_evenement(donnees.get("date_evenement", ""))
    if donnees.get("date_evenement") and date_evenement is None:
        erreurs.append("La date de l'événement n'est pas valide.")
    elif date_evenement and date_evenement <= datetime.utcnow():
        erreurs.append("La date de l'événement doit être dans le futur.")

    for champ, libelle in (("duree_heures", "La durée prévue"), ("capacite_accueil", "La capacité d'accueil")):
        valeur = donnees.get(champ, "").strip()
        if valeur:
            try:
                if float(valeur) <= 0:
                    erreurs.append(f"{libelle} doit être un nombre positif.")
            except ValueError:
                erreurs.append(f"{libelle} doit être un nombre.")

    return erreurs


def _parser_date_evenement(valeur):
    """Convertit la valeur d'un champ datetime-local en objet datetime, ou
    None si le format est invalide."""
    try:
        return datetime.strptime(valeur, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _construire_nature_diffusion(donnees):
    """Assemble les cases cochees de la Section 3 en une chaine lisible
    (ex. 'Musique vivante, Autres : sound-system local')."""
    libelles = {"vivante": "Musique vivante", "mecanique": "Musique mécanique"}
    parties = [libelles[valeur] for valeur in donnees.getlist("nature_diffusion") if valeur in libelles]
    if "autres" in donnees.getlist("nature_diffusion"):
        parties.append(f"Autres : {donnees.get('nature_diffusion_autre', '').strip()}")
    return ", ".join(parties)


def _enregistrer_artistes(declaration_id, donnees):
    """Cree une ListeArtiste pour chaque ligne dynamique non vide de la
    Section 4 (nom d'artiste renseigne)."""
    noms = donnees.getlist("artiste_nom")
    disciplines = donnees.getlist("artiste_discipline")
    for nom, discipline in zip(noms, disciplines):
        if nom.strip():
            db.session.add(ListeArtiste(declaration_id=declaration_id, nom_artiste=nom.strip(), discipline=discipline.strip() or None))


def _extension_depuis_contenu(debut_fichier):
    """Retourne l'extension attendue selon les magic bytes, ou None."""
    for signature, extension in SIGNATURES_AFFICHE:
        if debut_fichier.startswith(signature):
            return extension
    return None


def _valider_et_sauver_affiche(fichier):
    """Valide et enregistre une affiche uploadee (JPG/PNG, max 2 Mo via
    MAX_CONTENT_LENGTH). Controle extension + contenu binaire (Partie 2)."""
    if fichier is None or not fichier.filename:
        return None

    nom_securise = secure_filename(fichier.filename)
    extension = os.path.splitext(nom_securise)[1].lower()
    if extension not in EXTENSIONS_AFFICHE:
        raise ValueError("L'affiche doit être une image JPG ou PNG.")

    debut = fichier.stream.read(16)
    fichier.stream.seek(0)
    extension_contenu = _extension_depuis_contenu(debut)
    if extension_contenu is None:
        raise ValueError(
            "Le fichier envoyé n'est pas une image JPG ou PNG valide "
            "(contenu incompatible)."
        )
    # L'extension du nom doit coincider avec le type reel du fichier.
    extension_declaree = ".jpg" if extension == ".jpeg" else extension
    if extension_declaree != extension_contenu:
        raise ValueError(
            "L'extension du fichier ne correspond pas à son contenu réel."
        )

    dossier = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(dossier, exist_ok=True)
    nom_fichier = f"affiche_{uuid.uuid4().hex}{extension_contenu}"
    chemin_absolu = os.path.join(dossier, nom_fichier)
    fichier.save(chemin_absolu)
    return f"uploads/{nom_fichier}"


def _declaration_proprietaire_ou_404(declaration_id):
    """RM-004 : declaration appartenant a l'organisateur connecte."""
    declaration = Declaration.query.get_or_404(declaration_id)
    if declaration.organisateur_id != current_user.organisateur.id:
        abort(404)
    return declaration


def _formdata_depuis_declaration(declaration):
    """Reconstitue un MultiDict compatible avec le formulaire (edition)."""
    nature = declaration.nature_diffusion or ""
    paires = [
        ("nom_demandeur", declaration.nom_demandeur),
        ("prenom_demandeur", declaration.prenom_demandeur),
        (
            "qualite",
            "Autre" if declaration.qualite_demandeur != "Organisateur" else "Organisateur",
        ),
        (
            "qualite_autre",
            declaration.qualite_demandeur if declaration.qualite_demandeur != "Organisateur" else "",
        ),
        ("telephone", declaration.telephone),
        ("email", declaration.email),
        ("nature_manifestation", declaration.nature_manifestation),
        ("nom_artiste_evenement", declaration.nom_artiste_evenement),
        ("nom_salle", declaration.nom_salle),
        ("adresse", declaration.adresse),
        ("ville", declaration.ville),
        ("date_evenement", declaration.date_evenement.strftime("%Y-%m-%dT%H:%M")),
        ("duree_heures", str(declaration.duree_heures)),
        ("capacite_accueil", str(declaration.capacite_accueil)),
        ("entree", "payante" if declaration.entree_payante else "gratuite"),
        ("autres_details", declaration.autres_details or ""),
        ("description_publique", declaration.description_publique or ""),
    ]
    if "Musique vivante" in nature:
        paires.append(("nature_diffusion", "vivante"))
    if "Musique mécanique" in nature or "Musique mecanique" in nature:
        paires.append(("nature_diffusion", "mecanique"))
    if "Autres :" in nature:
        paires.append(("nature_diffusion", "autres"))
        paires.append(("nature_diffusion_autre", nature.split("Autres :", 1)[1].strip()))
    if declaration.promouvoir:
        paires.append(("promouvoir", "on"))
    if declaration.contact_public:
        paires.append(("contact_public", "on"))
    return MultiDict(paires)


def _appliquer_donnees_declaration(declaration, donnees, affiche_path=None):
    """Met a jour les champs editables sans changer le statut (RM-015)."""
    qualite_autre = donnees.get("qualite_autre", "").strip()
    promouvoir = donnees.get("promouvoir") == "on"
    declaration.nom_demandeur = donnees["nom_demandeur"].strip()
    declaration.prenom_demandeur = donnees["prenom_demandeur"].strip()
    declaration.qualite_demandeur = (
        qualite_autre if donnees.get("qualite") == "Autre" else "Organisateur"
    )
    declaration.telephone = donnees["telephone"].strip()
    declaration.email = donnees["email"].strip().lower()
    declaration.nature_manifestation = donnees["nature_manifestation"].strip()
    declaration.nom_artiste_evenement = donnees["nom_artiste_evenement"].strip()
    declaration.nom_salle = donnees["nom_salle"].strip()
    declaration.adresse = donnees["adresse"].strip()
    declaration.ville = donnees["ville"].strip()
    declaration.date_evenement = _parser_date_evenement(donnees["date_evenement"])
    declaration.duree_heures = float(donnees["duree_heures"])
    declaration.capacite_accueil = int(float(donnees["capacite_accueil"]))
    declaration.entree_payante = donnees.get("entree") == "payante"
    declaration.nature_diffusion = _construire_nature_diffusion(donnees)
    declaration.autres_details = donnees.get("autres_details", "").strip() or None
    declaration.promouvoir = promouvoir
    declaration.description_publique = (
        donnees.get("description_publique", "").strip() or None if promouvoir else None
    )
    declaration.contact_public = donnees.get("contact_public") == "on" if promouvoir else False
    if not promouvoir:
        declaration.affiche_path = None
    elif affiche_path:
        declaration.affiche_path = affiche_path


def _construire_declaration(organisateur_id, donnees, affiche_path=None):
    """Construit (sans l'ajouter a la session) une Declaration a partir des
    donnees validees du formulaire, y compris les champs de promotion."""
    qualite_autre = donnees.get("qualite_autre", "").strip()
    promouvoir = donnees.get("promouvoir") == "on"
    return Declaration(
        organisateur_id=organisateur_id,
        nom_demandeur=donnees["nom_demandeur"].strip(),
        prenom_demandeur=donnees["prenom_demandeur"].strip(),
        qualite_demandeur=qualite_autre if donnees.get("qualite") == "Autre" else "Organisateur",
        telephone=donnees["telephone"].strip(),
        email=donnees["email"].strip().lower(),
        nature_manifestation=donnees["nature_manifestation"].strip(),
        nom_artiste_evenement=donnees["nom_artiste_evenement"].strip(),
        nom_salle=donnees["nom_salle"].strip(),
        adresse=donnees["adresse"].strip(),
        ville=donnees["ville"].strip(),
        date_evenement=_parser_date_evenement(donnees["date_evenement"]),
        duree_heures=float(donnees["duree_heures"]),
        capacite_accueil=int(float(donnees["capacite_accueil"])),
        entree_payante=(donnees.get("entree") == "payante"),
        nature_diffusion=_construire_nature_diffusion(donnees),
        autres_details=donnees.get("autres_details", "").strip() or None,
        promouvoir=promouvoir,
        description_publique=donnees.get("description_publique", "").strip() or None if promouvoir else None,
        affiche_path=affiche_path if promouvoir else None,
        contact_public=donnees.get("contact_public") == "on" if promouvoir else False,
        statut="nouvelle",
    )


@declarations_bp.route("/nouvelle", methods=["GET", "POST"])
@role_required("organisateur")
def nouvelle():
    """Formulaire de nouvelle declaration d'evenement (RM-010 a RM-014),
    avec option de promotion publique."""
    if current_user.organisateur.statut_compte in COMPTES_BLOQUANTS:
        flash("Votre compte est bloqué : vous ne pouvez pas soumettre de nouvelle déclaration.", "erreur")
        notifier_declaration_bloquee(current_user.organisateur)
        db.session.commit()
        return redirect(url_for("declarations.tableau_de_bord"))

    if request.method == "GET":
        return render_template("declarations/nouvelle.html")

    erreurs = _valider_declaration(request.form)
    affiche_path = None
    try:
        affiche_path = _valider_et_sauver_affiche(request.files.get("affiche"))
    except ValueError as erreur:
        erreurs.append(str(erreur))

    if erreurs:
        for message in erreurs:
            flash(message, "erreur")
        artistes_soumis = list(zip(request.form.getlist("artiste_nom"), request.form.getlist("artiste_discipline")))
        return render_template("declarations/nouvelle.html", donnees=request.form, artistes_soumis=artistes_soumis), 400

    declaration = _construire_declaration(current_user.organisateur.id, request.form, affiche_path=affiche_path)
    db.session.add(declaration)
    db.session.flush()  # obtenir declaration.id avant de creer les artistes lies

    _enregistrer_artistes(declaration.id, request.form)
    # Enregistrer d'abord la declaration : l'email ne doit pas faire echouer le formulaire.
    db.session.commit()
    try:
        notifier_confirmation_declaration(declaration)
        notifier_nouvelle_declaration_bbda(declaration)
        db.session.commit()
    except Exception:
        db.session.rollback()

    flash("Votre déclaration a bien été envoyée au BBDA. Vous recevrez une confirmation par email.", "succes")
    return redirect(url_for("declarations.tableau_de_bord"))


@declarations_bp.route("/<int:declaration_id>/modifier", methods=["GET", "POST"])
@role_required("organisateur")
def modifier(declaration_id):
    """RM-015 : correction d'une declaration encore au statut `nouvelle`."""
    declaration = _declaration_proprietaire_ou_404(declaration_id)
    if declaration.statut != "nouvelle":
        flash(
            "Cette déclaration ne peut plus être modifiée : elle est déjà prise en charge par le BBDA.",
            "erreur",
        )
        return redirect(url_for("declarations.detail", declaration_id=declaration.id))

    if request.method == "GET":
        artistes = [(a.nom_artiste, a.discipline or "") for a in declaration.artistes]
        return render_template(
            "declarations/nouvelle.html",
            donnees=_formdata_depuis_declaration(declaration),
            artistes_soumis=artistes,
            mode_edition=True,
            declaration=declaration,
            action_url=url_for("declarations.modifier", declaration_id=declaration.id),
            titre_formulaire=f"Modifier la déclaration n°{declaration.id}",
            libelle_bouton="Enregistrer les modifications",
        )

    erreurs = _valider_declaration(request.form)
    affiche_path = None
    try:
        affiche_path = _valider_et_sauver_affiche(request.files.get("affiche"))
    except ValueError as erreur:
        erreurs.append(str(erreur))

    if erreurs:
        for message in erreurs:
            flash(message, "erreur")
        artistes_soumis = list(
            zip(request.form.getlist("artiste_nom"), request.form.getlist("artiste_discipline"))
        )
        return (
            render_template(
                "declarations/nouvelle.html",
                donnees=request.form,
                artistes_soumis=artistes_soumis,
                mode_edition=True,
                declaration=declaration,
                action_url=url_for("declarations.modifier", declaration_id=declaration.id),
                titre_formulaire=f"Modifier la déclaration n°{declaration.id}",
                libelle_bouton="Enregistrer les modifications",
            ),
            400,
        )

    _appliquer_donnees_declaration(declaration, request.form, affiche_path=affiche_path)
    ListeArtiste.query.filter_by(declaration_id=declaration.id).delete()
    _enregistrer_artistes(declaration.id, request.form)
    db.session.commit()
    flash("Votre déclaration a été mise à jour.", "succes")
    return redirect(url_for("declarations.detail", declaration_id=declaration.id))


def _construire_frise(declaration):
    """Construit la frise chronologique (5 etapes fixes) affichee sur la
    page de detail : chaque etape est 'franchie' (vert) ou future (gris),
    avec le detail chiffre/date uniquement quand la donnee existe."""
    evaluation = declaration.evaluation
    quittance = declaration.quittance
    paiements = declaration.paiements
    dernier_paiement = max(paiements, key=lambda p: p.date_paiement) if paiements else None

    return [
        {
            "libelle": f"Déclaration soumise : {declaration.date_soumission.strftime('%d/%m/%Y')}",
            "franchie": True,
        },
        {"libelle": "En cours d'évaluation par le BBDA", "franchie": declaration.statut != "nouvelle"},
        {
            "libelle": (
                f"Montant fixé : {evaluation.montant_total:.0f} FCFA"
                if evaluation
                else "Montant fixé par un agent"
            ),
            "franchie": evaluation is not None,
        },
        {
            "libelle": (
                f"Paiement reçu : {dernier_paiement.date_paiement.strftime('%d/%m/%Y')}"
                if dernier_paiement
                else "Paiement reçu"
            ),
            "franchie": dernier_paiement is not None,
        },
        {"libelle": "Quittance délivrée", "franchie": quittance is not None},
    ]


@declarations_bp.route("/<int:declaration_id>")
@role_required("organisateur")
def detail(declaration_id):
    """Detail d'une declaration de l'organisateur connecte : frise
    chronologique, informations saisies, montant a payer et telechargement
    de la quittance le cas echeant (RM-030 a RM-054)."""
    declaration = Declaration.query.get_or_404(declaration_id)
    if declaration.organisateur_id != current_user.organisateur.id:
        abort(404)

    libelle_css, libelle = STATUTS_AFFICHAGE[declaration.statut]
    total_paye = sum(p.montant_chiffres for p in declaration.paiements)

    return render_template(
        "declarations/detail.html",
        declaration=declaration,
        libelle_statut=libelle,
        libelle_css=libelle_css,
        frise=_construire_frise(declaration),
        total_paye=total_paye,
    )
