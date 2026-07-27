"""Routes d'administration.

Route de connexion (Prompt 4) : tableau de bord minimal, pour valider le
flux d'authentification. Espace administrateur complet implemente au Prompt 16 : statistiques
globales, gestion des comptes utilisateurs (organisateurs et agents), et
parametres systeme. Statistiques avancees (Prompt 17) : module
`admin/stats.py` et page `/admin/statistiques`.
"""

from datetime import datetime

import bcrypt
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import extract, func

from backend.arrieres.moteur import DELAI_NOTIFICATION_DEFAUT, SEUIL_ARRIERE_DEFAUT
from backend.auth.decorators import role_required
from backend.notifications.email_service import tester_envoi_email
from extensions import db
from models import (
    AlerteSurveillance,
    Arriere,
    Declaration,
    MessageContact,
    Organisateur,
    ParametresSysteme,
    Quittance,
    Utilisateur,
)

from . import admin_bp
from . import stats as stats_admin

NOMS_MOIS_FR = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


@admin_bp.route("/evenements-publics")
@role_required("admin")
def evenements_publics():
    """Liste des evenements visibles publiquement (RM-090) pour moderation."""
    evenements = (
        Declaration.query.filter_by(promouvoir=True, statut="quittance_delivree")
        .order_by(Declaration.date_evenement.desc())
        .all()
    )
    return render_template("admin/evenements_publics.html", evenements=evenements)


@admin_bp.route("/evenements-publics/<int:declaration_id>/depublier", methods=["POST"])
@role_required("admin")
def depublier_evenement(declaration_id):
    """RM-092 : retire un evenement de la face publique (promouvoir=False)."""
    declaration = Declaration.query.get_or_404(declaration_id)
    if not declaration.promouvoir or declaration.statut != "quittance_delivree":
        flash("Cet événement n'est pas actuellement publié.", "erreur")
        return redirect(url_for("admin.evenements_publics"))

    declaration.promouvoir = False
    db.session.commit()
    flash(
        f"Événement « {declaration.nom_artiste_evenement} » dépublié du site public.",
        "succes",
    )
    return redirect(url_for("admin.evenements_publics"))


def _statistiques_globales():
    """Chiffres cles pour les 4 cartes du tableau de bord administrateur."""
    total_redevances = db.session.query(func.coalesce(func.sum(Quittance.somme_totale_chiffres), 0)).scalar()
    arrieres_en_cours = (
        db.session.query(func.coalesce(func.sum(Arriere.montant_du), 0)).filter(Arriere.statut == "en_attente").scalar()
    )
    return {
        "total_declarations": Declaration.query.count(),
        "total_redevances": total_redevances,
        "arrieres_en_cours": arrieres_en_cours,
        "comptes_actifs": Utilisateur.query.filter_by(statut="actif").count(),
    }


def _declarations_par_mois(nombre_mois=6):
    """Nombre de declarations soumises, mois par mois, sur les
    `nombre_mois` derniers mois (mois courant inclus) — graphique en
    barres CSS du tableau de bord."""
    aujourdhui = datetime.utcnow()
    annee, mois = aujourdhui.year, aujourdhui.month
    mois_ordonnes = []
    for _ in range(nombre_mois):
        mois_ordonnes.append((annee, mois))
        mois -= 1
        if mois == 0:
            mois, annee = 12, annee - 1
    mois_ordonnes.reverse()

    resultats = []
    for annee_mois, numero_mois in mois_ordonnes:
        nombre = Declaration.query.filter(
            extract("year", Declaration.date_soumission) == annee_mois,
            extract("month", Declaration.date_soumission) == numero_mois,
        ).count()
        resultats.append({"libelle": f"{NOMS_MOIS_FR[numero_mois]} {annee_mois}", "valeur": nombre})

    maximum = max((r["valeur"] for r in resultats), default=0) or 1
    for resultat in resultats:
        resultat["pourcentage"] = round(resultat["valeur"] / maximum * 100)
    return resultats


@admin_bp.route("/")
@role_required("admin")
def tableau_de_bord():
    """Tableau de bord administrateur : statistiques globales, graphique
    des declarations par mois, et alertes de surveillance non traitees
    (RM-003)."""
    alertes = (
        AlerteSurveillance.query.filter_by(traitee=False).order_by(AlerteSurveillance.date_marquage.desc()).all()
    )
    return render_template(
        "admin/tableau_de_bord.html",
        statistiques=_statistiques_globales(),
        declarations_par_mois=_declarations_par_mois(),
        alertes=alertes,
    )


@admin_bp.route("/statistiques")
@role_required("admin")
def statistiques():
    """Page de statistiques avancees (Prompt 17) : resume de l'annee,
    graphiques CSS (declarations, redevances, repartition par type),
    top organisateurs et synthese des arrieres."""
    annee = datetime.utcnow().year
    declarations = stats_admin.get_declarations_par_mois(annee)
    redevances = stats_admin.get_redevances_par_mois(annee)
    repartition = stats_admin.get_repartition_par_type()

    return render_template(
        "admin/statistiques.html",
        resume=stats_admin.resume_annee(annee),
        barres_declarations=stats_admin.barres_pour_graphique(declarations),
        barres_redevances=stats_admin.barres_pour_graphique(redevances),
        barres_repartition=stats_admin.barres_pour_graphique(repartition),
        top_organisateurs=stats_admin.get_top_organisateurs(limit=10),
        stats_arrieres=stats_admin.get_stats_arrieres(),
    )


@admin_bp.route("/utilisateurs")
@role_required("admin")
def utilisateurs():
    """Liste de tous les comptes, organisateurs et agents/admins separes
    pour l'affichage en deux onglets."""
    organisateurs = Organisateur.query.join(Utilisateur).order_by(Utilisateur.nom).all()
    agents = Utilisateur.query.filter(Utilisateur.role.in_(("agent", "admin"))).order_by(Utilisateur.nom).all()
    return render_template("admin/utilisateurs.html", organisateurs=organisateurs, agents=agents)


def _valider_nouvel_agent(donnees):
    erreurs = []
    for champ, libelle in (("nom", "Le nom"), ("prenom", "Le prénom"), ("email", "L'email")):
        if not donnees.get(champ, "").strip():
            erreurs.append(f"{libelle} est requis.")

    email = donnees.get("email", "").strip().lower()
    if email and Utilisateur.query.filter_by(email=email).first():
        erreurs.append("Un compte existe déjà avec cette adresse email.")

    mot_de_passe = donnees.get("mot_de_passe", "")
    if len(mot_de_passe) < 8:
        erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")

    return erreurs


@admin_bp.route("/utilisateurs/nouveau-agent", methods=["POST"])
@role_required("admin")
def nouvel_agent():
    """Cree un compte agent (RM-002 : seul l'administrateur peut creer des
    comptes agent/admin, l'auto-inscription publique etant reservee aux
    organisateurs)."""
    erreurs = _valider_nouvel_agent(request.form)
    if erreurs:
        for message in erreurs:
            flash(message, "erreur")
        return redirect(url_for("admin.utilisateurs"))

    hachage = bcrypt.hashpw(request.form["mot_de_passe"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.session.add(
        Utilisateur(
            nom=request.form["nom"].strip(),
            prenom=request.form["prenom"].strip(),
            email=request.form["email"].strip().lower(),
            mot_de_passe=hachage,
            role="agent",
        )
    )
    db.session.commit()

    flash("Compte agent créé avec succès.", "succes")
    return redirect(url_for("admin.utilisateurs"))


@admin_bp.route("/utilisateurs/<int:utilisateur_id>/desactiver", methods=["POST"])
@role_required("admin")
def desactiver_utilisateur(utilisateur_id):
    """Desactive un compte (il ne peut plus se connecter, cf.
    Utilisateur.is_active)."""
    utilisateur = Utilisateur.query.get_or_404(utilisateur_id)
    if utilisateur.id == current_user.id:
        flash("Vous ne pouvez pas désactiver votre propre compte.", "erreur")
        return redirect(url_for("admin.utilisateurs"))

    utilisateur.statut = "inactif"
    db.session.commit()

    flash("Compte désactivé.", "succes")
    return redirect(url_for("admin.utilisateurs"))


@admin_bp.route("/utilisateurs/<int:utilisateur_id>/activer", methods=["POST"])
@role_required("admin")
def activer_utilisateur(utilisateur_id):
    """Reactive un compte precedemment desactive."""
    utilisateur = Utilisateur.query.get_or_404(utilisateur_id)
    utilisateur.statut = "actif"
    db.session.commit()

    flash("Compte réactivé.", "succes")
    return redirect(url_for("admin.utilisateurs"))


def _parametre_ou_defaut(cle, defaut):
    parametre = ParametresSysteme.query.filter_by(cle=cle).first()
    return parametre.valeur if parametre else str(defaut)


@admin_bp.route("/parametres", methods=["GET", "POST"])
@role_required("admin")
def parametres():
    """Affiche et sauvegarde les parametres systeme configurables
    (RM du §9 de docs/REGLES_METIER.md) : SEUIL_ARRIERE et
    DELAI_NOTIFICATION, utilises par le moteur d'arrieres du Prompt 14."""
    if request.method == "POST":
        erreurs = []
        for cle, libelle in (("SEUIL_ARRIERE", "Le seuil d'arriéré"), ("DELAI_NOTIFICATION", "Le délai de notification")):
            valeur = request.form.get(cle, "").strip()
            if not valeur:
                erreurs.append(f"{libelle} est requis.")
                continue
            try:
                if float(valeur) < 0:
                    erreurs.append(f"{libelle} doit être positif ou nul.")
            except ValueError:
                erreurs.append(f"{libelle} doit être un nombre.")

        if erreurs:
            for message in erreurs:
                flash(message, "erreur")
            return redirect(url_for("admin.parametres"))

        for cle in ("SEUIL_ARRIERE", "DELAI_NOTIFICATION"):
            parametre = ParametresSysteme.query.filter_by(cle=cle).first()
            if parametre is None:
                parametre = ParametresSysteme(cle=cle)
                db.session.add(parametre)
            parametre.valeur = request.form[cle].strip()
            parametre.modifie_par = current_user.id
            parametre.date_modification = datetime.utcnow()
        db.session.commit()

        flash("Paramètres enregistrés.", "succes")
        return redirect(url_for("admin.parametres"))

    return render_template(
        "admin/parametres.html",
        seuil_arriere=_parametre_ou_defaut("SEUIL_ARRIERE", SEUIL_ARRIERE_DEFAUT),
        delai_notification=_parametre_ou_defaut("DELAI_NOTIFICATION", DELAI_NOTIFICATION_DEFAUT),
        email_brevo_configure=bool((current_app.config.get("BREVO_API_KEY") or "").strip()),
        email_sendgrid_configure=bool((current_app.config.get("SENDGRID_API_KEY") or "").strip()),
        email_expediteur=(
            current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME") or ""
        ),
        email_canal=(
            "sendgrid"
            if (current_app.config.get("SENDGRID_API_KEY") or "").strip()
            else (
                "brevo"
                if (current_app.config.get("BREVO_API_KEY") or "").strip()
                else "smtp/aucun"
            )
        ),
    )


@admin_bp.route("/parametres/tester-email", methods=["POST"])
@role_required("admin")
def tester_email():
    """Envoie un email de test et affiche le resultat (diagnostic Brevo/SMTP)."""
    destinataire = request.form.get("email_test", "").strip() or current_user.email
    ok, detail = tester_envoi_email(destinataire)
    flash(detail, "succes" if ok else "erreur")
    return redirect(url_for("admin.parametres"))


@admin_bp.route("/messages-contact")
@role_required("admin")
def messages_contact():
    """Liste des messages recus via le formulaire de contact public."""
    filtre = request.args.get("filtre", "tous")
    requete = MessageContact.query.order_by(MessageContact.date_envoi.desc())
    if filtre == "non_traites":
        requete = requete.filter_by(traite=False)
    elif filtre == "traites":
        requete = requete.filter_by(traite=True)
    return render_template(
        "admin/messages_contact.html",
        messages=requete.all(),
        filtre=filtre,
        non_traites=MessageContact.query.filter_by(traite=False).count(),
    )


@admin_bp.route("/messages-contact/<int:message_id>/traiter", methods=["POST"])
@role_required("admin")
def traiter_message_contact(message_id):
    """Marque un message de contact comme traite."""
    message = MessageContact.query.get_or_404(message_id)
    message.traite = True
    db.session.commit()
    flash("Message marqué comme traité.", "succes")
    return redirect(url_for("admin.messages_contact", filtre=request.args.get("filtre", "tous")))


@admin_bp.route("/messages-contact/<int:message_id>/reouvrir", methods=["POST"])
@role_required("admin")
def reouvrir_message_contact(message_id):
    """Remet un message de contact en non traite."""
    message = MessageContact.query.get_or_404(message_id)
    message.traite = False
    db.session.commit()
    flash("Message remis en non traité.", "succes")
    return redirect(url_for("admin.messages_contact", filtre=request.args.get("filtre", "tous")))
