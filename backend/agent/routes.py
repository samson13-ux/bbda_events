"""Routes agent.

Tableau de bord (Prompt 9) : declarations urgentes et en cours,
statistiques du jour/mois, alertes de surveillance et d'arrieres. Liste
filtrable des declarations et suivi des alertes de surveillance construits
en support direct du tableau de bord. Traitement d'une declaration —
historique de l'organisateur, fixation du montant, mise en attente
(Prompt 10) implemente. Confirmation de paiement et generation de la
quittance (Prompt 11) implementees, avec generation reelle du PDF
(Prompt 12). Un arriere est cree via le moteur de gestion des arrieres
(`backend/arrieres/moteur.py`, Prompt 14) en cas de paiement partiel, et
bloque automatiquement le compte de l'organisateur si le seuil est
franchi. Interface complete de gestion des arrieres et de la surveillance
(debloquer/bloquer un compte, envoyer les rappels, marquer/lever une
surveillance) implementee au Prompt 15.
"""

from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_

from backend.arrieres.moteur import (
    bloquer_compte,
    creer_arriere,
    debloquer_compte,
    lever_surveillance,
    marquer_surveillance,
    verifier_arriere,
    verifier_et_envoyer_rappels,
)
from backend.auth.decorators import role_required
from backend.exports.routes import generer_quittance
from backend.notifications.email_service import (
    notifier_evenement_publie,
    notifier_montant_fixe,
    notifier_quittance_disponible,
)
from backend.statuts import STATUTS_AFFICHAGE, STATUTS_EN_COURS_AGENT
from extensions import db
from models import AlerteSurveillance, Arriere, Declaration, EvaluationAgent, Organisateur, Paiement, Quittance, Utilisateur

from . import agent_bp

DECLARATIONS_PAR_PAGE = 20


def _statistiques_agent():
    """Nouvelles / en cours / payees aujourd'hui / quittances ce mois-ci
    (RM-004 cote agent)."""
    aujourdhui = datetime.utcnow().date()
    debut_mois = aujourdhui.replace(day=1)
    paiements_soldes = Paiement.query.filter_by(solde_apres=0).all()
    quittances = Quittance.query.all()
    return {
        "nouvelles": Declaration.query.filter_by(statut="nouvelle").count(),
        "en_cours": Declaration.query.filter(Declaration.statut.in_(STATUTS_EN_COURS_AGENT)).count(),
        "payees_aujourdhui": sum(1 for p in paiements_soldes if p.date_paiement.date() == aujourdhui),
        "quittances_ce_mois": sum(1 for q in quittances if q.date_delivrance.date() >= debut_mois),
    }


def _alertes_agent():
    """Comptes de surveillance non traites et organisateurs en difficulte
    (RM-073, RM-080 a RM-084)."""
    return {
        "surveillance_non_traitees": AlerteSurveillance.query.filter_by(traitee=False).count(),
        "organisateurs_en_difficulte": Organisateur.query.filter(Organisateur.statut_compte != "actif").count(),
    }


@agent_bp.route("/")
@role_required("agent", "admin")
def tableau_de_bord():
    """Espace agent : declarations a traiter en priorite, en cours de
    traitement, statistiques et alertes (RM-003, RM-004)."""
    declarations_nouvelles = (
        Declaration.query.filter_by(statut="nouvelle").order_by(Declaration.date_soumission.asc()).all()
    )
    declarations_en_cours = (
        Declaration.query.filter(Declaration.statut.in_(STATUTS_EN_COURS_AGENT))
        .order_by(Declaration.date_soumission.desc())
        .all()
    )

    return render_template(
        "agent/tableau_de_bord.html",
        declarations_nouvelles=declarations_nouvelles,
        declarations_en_cours=declarations_en_cours,
        statistiques=_statistiques_agent(),
        alertes=_alertes_agent(),
        statuts_affichage=STATUTS_AFFICHAGE,
    )


@agent_bp.route("/declarations")
@role_required("agent", "admin")
def declarations():
    """Liste filtrable / searchable / paginee des declarations."""
    statut_filtre = request.args.get("statut", "").strip() or None
    recherche = request.args.get("recherche", "").strip()
    page = request.args.get("page", 1, type=int) or 1

    requete = Declaration.query
    if statut_filtre:
        requete = requete.filter_by(statut=statut_filtre)
    if recherche:
        terme = f"%{recherche}%"
        requete = (
            requete.join(Organisateur, Declaration.organisateur_id == Organisateur.id)
            .join(Utilisateur, Organisateur.utilisateur_id == Utilisateur.id)
            .filter(
                or_(
                    Declaration.nom_artiste_evenement.ilike(terme),
                    Declaration.ville.ilike(terme),
                    Declaration.nom_salle.ilike(terme),
                    Utilisateur.nom.ilike(terme),
                    Utilisateur.prenom.ilike(terme),
                    Utilisateur.email.ilike(terme),
                )
            )
        )

    pagination = requete.order_by(Declaration.date_soumission.desc()).paginate(
        page=page, per_page=DECLARATIONS_PAR_PAGE, error_out=False
    )

    return render_template(
        "agent/declarations.html",
        declarations=pagination.items,
        pagination=pagination,
        statut_filtre=statut_filtre,
        recherche=recherche,
        statuts_affichage=STATUTS_AFFICHAGE,
    )


def _historique_organisateur(organisateur):
    """Total des declarations passees, total paye, arriere actuel et 5
    dernieres declarations d'un organisateur, pour la colonne droite de la
    page de traitement (RM-030 a RM-035)."""
    declarations = (
        Declaration.query.filter_by(organisateur_id=organisateur.id)
        .order_by(Declaration.date_soumission.desc())
        .all()
    )
    total_paye = sum(paiement.montant_chiffres for d in declarations for paiement in d.paiements)
    arriere_actuel = (
        db.session.query(func.coalesce(func.sum(Arriere.montant_du), 0))
        .filter(Arriere.organisateur_id == organisateur.id, Arriere.statut == "en_attente")
        .scalar()
    )
    return {
        "total_declarations": len(declarations),
        "total_paye": total_paye,
        "arriere_actuel": arriere_actuel,
        "cinq_dernieres": declarations[:5],
    }


@agent_bp.route("/declarations/<int:declaration_id>")
@role_required("agent", "admin")
def traiter_declaration(declaration_id):
    """Page de traitement d'une declaration : informations completes,
    historique de l'organisateur, formulaires de fixation du montant et de
    mise en attente (RM-030 a RM-035).

    Ouvrir cette page marque implicitement une declaration 'nouvelle' comme
    'en_evaluation' (un agent a commence a l'examiner)."""
    declaration = Declaration.query.get_or_404(declaration_id)
    if declaration.statut == "nouvelle":
        declaration.statut = "en_evaluation"
        db.session.commit()

    libelle_css, libelle = STATUTS_AFFICHAGE[declaration.statut]
    soldee = _declaration_soldee(declaration)
    return render_template(
        "agent/traitement.html",
        declaration=declaration,
        libelle_statut=libelle,
        libelle_css=libelle_css,
        historique=_historique_organisateur(declaration.organisateur),
        statuts_affichage=STATUTS_AFFICHAGE,
        soldee=soldee,
        montant_verrouille=_montant_verrouille(declaration),
        montant_deja_paye=_montant_deja_paye(declaration.id) if declaration.evaluation else 0,
        reste_du=_reste_du(declaration) if declaration.evaluation else 0,
    )


def _valider_montant(donnees):
    """Valide les champs du formulaire de fixation du montant."""
    erreurs = []
    for champ, libelle in (("tarif", "Le tarif"), ("redevance", "La redevance")):
        valeur = donnees.get(champ, "").strip()
        if not valeur:
            erreurs.append(f"{libelle} est requis.")
            continue
        try:
            if float(valeur) < 0:
                erreurs.append(f"{libelle} doit être positif ou nul.")
        except ValueError:
            erreurs.append(f"{libelle} doit être un nombre.")
    return erreurs


@agent_bp.route("/declarations/<int:declaration_id>/fixer-montant", methods=["POST"])
@role_required("agent", "admin")
def fixer_montant(declaration_id):
    """Fixe (ou modifie, RM-035) le tarif et la redevance d'une declaration,
    puis notifie l'organisateur (RM-030 a RM-033)."""
    declaration = Declaration.query.get_or_404(declaration_id)

    if _montant_verrouille(declaration):
        flash(
            "Le montant ne peut plus être modifié : un versement a déjà été enregistré "
            "ou le dossier est soldé.",
            "erreur",
        )
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    erreurs = _valider_montant(request.form)
    if erreurs:
        for message in erreurs:
            flash(message, "erreur")
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    evaluation = declaration.evaluation
    if evaluation is None:
        evaluation = EvaluationAgent(declaration=declaration)
        db.session.add(evaluation)
    evaluation.agent_id = current_user.id
    evaluation.tarif = float(request.form["tarif"])
    evaluation.redevance = float(request.form["redevance"])
    evaluation.commentaire = request.form.get("commentaire", "").strip() or None
    evaluation.date_evaluation = datetime.utcnow()

    declaration.statut = "montant_fixe"
    db.session.commit()
    try:
        notifier_montant_fixe(declaration)
        db.session.commit()
    except Exception:
        db.session.rollback()

    flash("Montant fixé et organisateur notifié.", "succes")
    return redirect(url_for("agent.tableau_de_bord"))


@agent_bp.route("/declarations/<int:declaration_id>/mettre-en-attente", methods=["POST"])
@role_required("agent", "admin")
def mettre_en_attente(declaration_id):
    """Met une declaration en attente avec un commentaire obligatoire
    (RM-034)."""
    declaration = Declaration.query.get_or_404(declaration_id)

    if _montant_verrouille(declaration):
        flash(
            "Impossible de mettre en attente : un versement a déjà été enregistré "
            "ou le dossier est soldé.",
            "erreur",
        )
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    commentaire = request.form.get("commentaire", "").strip()

    if not commentaire:
        flash("Un commentaire est obligatoire pour mettre une déclaration en attente.", "erreur")
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    declaration.statut = "en_attente"
    declaration.commentaire_agent = commentaire
    db.session.commit()

    flash("Déclaration mise en attente.", "succes")
    return redirect(url_for("agent.tableau_de_bord"))


STATUTS_PRETS_PAIEMENT = ("montant_fixe", "paiement_en_attente")
STATUTS_DEJA_PAYES = ("payee", "quittance_delivree")
MESSAGE_DEJA_SOLDE = (
    "Cette déclaration a déjà un paiement enregistré et une quittance "
    "envoyée. Aucune nouvelle validation n'est possible."
)


def _montant_deja_paye(declaration_id):
    """Somme des versements deja encaisses sur la declaration."""
    return sum(p.montant_chiffres for p in Paiement.query.filter_by(declaration_id=declaration_id).all())


def _reste_du(declaration):
    """Montant encore exigible (total fixe - deja paye), jamais negatif."""
    if not declaration.evaluation:
        return 0.0
    return max(0.0, float(declaration.evaluation.montant_total) - _montant_deja_paye(declaration.id))


def _declaration_soldee(declaration):
    """True si le dossier est totalement regle (plus aucun encaissement possible).

    RM-047/048 : un versement partiel ne solde PAS le dossier ; seuls une
    quittance ou un reste du a zero bloquent de nouveaux paiements.
    """
    if declaration.statut in STATUTS_DEJA_PAYES:
        return True
    if Quittance.query.filter_by(declaration_id=declaration.id).first() is not None:
        return True
    if declaration.evaluation and _montant_deja_paye(declaration.id) > 0 and _reste_du(declaration) <= 0:
        return True
    return False


def _montant_verrouille(declaration):
    """True si tarif/redevance ne doivent plus etre modifies (versement deja enregistre)."""
    return _declaration_soldee(declaration) or (
        Paiement.query.filter_by(declaration_id=declaration.id).first() is not None
    )


def _synchroniser_arriere_declaration(declaration_id, reste):
    """Cree/met a jour ou regle l'arriere lie a cette declaration."""
    arriere = Arriere.query.filter_by(declaration_id=declaration_id, statut="en_attente").first()
    if reste <= 0:
        if arriere:
            arriere.statut = "regle"
            arriere.date_reglement = datetime.utcnow()
        return None
    if arriere:
        arriere.montant_du = reste
        return arriere
    return creer_arriere(declaration_id, reste)


@agent_bp.route("/declarations/<int:declaration_id>/paiement")
@role_required("agent", "admin")
def paiement(declaration_id):
    """Formulaire de confirmation du paiement d'une declaration dont le
    montant a deja ete fixe (RM-040 a RM-054)."""
    declaration = Declaration.query.get_or_404(declaration_id)
    if _declaration_soldee(declaration):
        flash(MESSAGE_DEJA_SOLDE, "erreur")
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))
    if declaration.statut not in STATUTS_PRETS_PAIEMENT:
        flash("Cette déclaration n'est pas prête pour un paiement.", "erreur")
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    reste = _reste_du(declaration)
    if reste <= 0:
        flash(MESSAGE_DEJA_SOLDE, "erreur")
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    return render_template(
        "agent/paiement.html",
        declaration=declaration,
        evaluation=declaration.evaluation,
        montant_deja_paye=_montant_deja_paye(declaration.id),
        reste_du=reste,
    )


def _valider_paiement(donnees, reste_du):
    """Valide les champs du formulaire et refuse tout depassement du reste du."""
    erreurs = []

    mode = donnees.get("mode_paiement")
    if mode not in ("especes", "cheque", "orange_money"):
        erreurs.append("Le mode de paiement est requis.")
    elif mode == "cheque" and not donnees.get("numero_cheque", "").strip():
        erreurs.append("Le numéro de chèque est requis pour un paiement par chèque.")

    montant = None
    montant_brut = donnees.get("montant_chiffres", "").strip()
    if not montant_brut:
        erreurs.append("Le montant perçu en chiffres est requis.")
    else:
        try:
            montant = float(montant_brut)
            if montant <= 0:
                erreurs.append("Le montant perçu doit être supérieur à zéro.")
            elif montant > reste_du + 0.01:
                erreurs.append(
                    f"Montant refusé : il dépasse le reste dû "
                    f"({reste_du:.0f} FCFA). Aucun paiement supplémentaire n'a été enregistré."
                )
        except ValueError:
            erreurs.append("Le montant perçu doit être un nombre.")

    if not donnees.get("montant_lettres", "").strip():
        erreurs.append("Le montant perçu en lettres est requis.")

    type_paiement = donnees.get("type_paiement")
    if type_paiement not in ("integral", "partiel"):
        erreurs.append("Le type de paiement est requis.")
    elif type_paiement == "integral" and montant is not None and montant + 0.01 < reste_du:
        erreurs.append(
            f"Pour un paiement intégral, le montant perçu doit être égal au reste dû "
            f"({reste_du:.0f} FCFA)."
        )
    elif type_paiement == "partiel":
        reste = donnees.get("reste_a_payer", "").strip()
        if not reste:
            erreurs.append("Le reste à payer est requis pour un paiement partiel.")
        else:
            try:
                reste_saisi = float(reste)
                if reste_saisi < 0:
                    erreurs.append("Le reste à payer doit être positif ou nul.")
                elif montant is not None and abs((montant + reste_saisi) - reste_du) > 0.01:
                    erreurs.append(
                        f"Incohérence : montant perçu + reste à payer doit égaler "
                        f"le reste dû ({reste_du:.0f} FCFA)."
                    )
                elif montant is not None and montant >= reste_du:
                    erreurs.append(
                        "Pour un paiement partiel, le montant perçu doit être "
                        "strictement inférieur au reste dû."
                    )
            except ValueError:
                erreurs.append("Le reste à payer doit être un nombre.")

    return erreurs


@agent_bp.route("/declarations/<int:declaration_id>/confirmer-paiement", methods=["POST"])
@role_required("agent", "admin")
def confirmer_paiement(declaration_id):
    """Enregistre un versement (integral ou partiel).

    RM-047/048 : quittance uniquement quand le solde restant atteint zero.
    Un paiement partiel cree/met a jour un arriere et laisse le dossier
    ouvert pour de prochains versements.
    """
    declaration = (
        Declaration.query.filter_by(id=declaration_id).with_for_update().first_or_404()
    )

    if _declaration_soldee(declaration) or _reste_du(declaration) <= 0:
        db.session.rollback()
        flash(MESSAGE_DEJA_SOLDE, "erreur")
        return redirect(url_for("agent.traiter_declaration", declaration_id=declaration_id))

    if declaration.statut not in STATUTS_PRETS_PAIEMENT:
        db.session.rollback()
        flash("Cette déclaration n'est pas prête pour un paiement.", "erreur")
        return redirect(url_for("agent.tableau_de_bord"))

    reste_du = _reste_du(declaration)
    erreurs = _valider_paiement(request.form, reste_du)
    if erreurs:
        db.session.rollback()
        for message in erreurs:
            flash(message, "erreur")
        return redirect(url_for("agent.paiement", declaration_id=declaration_id))

    type_paiement = request.form["type_paiement"]
    montant = float(request.form["montant_chiffres"])
    reste_a_payer = float(request.form["reste_a_payer"]) if type_paiement == "partiel" else 0.0

    db.session.add(
        Paiement(
            declaration_id=declaration.id,
            mode_paiement=request.form["mode_paiement"],
            numero_cheque=request.form.get("numero_cheque", "").strip() or None,
            montant_chiffres=montant,
            montant_lettres=request.form["montant_lettres"].strip(),
            type_paiement=type_paiement,
            solde_apres=reste_a_payer,
            confirme_par=current_user.id,
        )
    )
    db.session.flush()

    nouveau_reste = _reste_du(declaration)

    if nouveau_reste <= 0.01:
        # Dossier soldé : quittance + notification (RM-045, RM-048, RM-050).
        declaration.statut = "payee"
        db.session.flush()
        generer_quittance(declaration, current_user)
        declaration.statut = "quittance_delivree"
        _synchroniser_arriere_declaration(declaration.id, 0)
        db.session.commit()
        try:
            notifier_quittance_disponible(declaration)
            if declaration.promouvoir:
                notifier_evenement_publie(declaration)
            db.session.commit()
        except Exception:
            db.session.rollback()
        flash(
            "Paiement confirmé et quittance générée. La notification a été envoyée à l'organisateur.",
            "succes",
        )
    else:
        # Versement partiel : pas de quittance, dossier reste ouvert (RM-047).
        declaration.statut = "paiement_en_attente"
        _synchroniser_arriere_declaration(declaration.id, nouveau_reste)
        db.session.commit()
        flash(
            f"Versement partiel enregistré. Reste dû : {nouveau_reste:.0f} FCFA. "
            "La quittance ne sera générée qu'après règlement du solde.",
            "succes",
        )

    return redirect(url_for("agent.tableau_de_bord"))


def _dernier_rappel(organisateur_id):
    """Date du rappel le plus recent parmi les arrieres en attente d'un
    organisateur, ou None si aucun rappel n'a encore ete envoye."""
    dates = [
        a.derniere_notification
        for a in Arriere.query.filter_by(organisateur_id=organisateur_id, statut="en_attente").all()
        if a.derniere_notification
    ]
    return max(dates) if dates else None


@agent_bp.route("/arrieres")
@role_required("agent", "admin")
def arrieres():
    """Liste des organisateurs en difficulte, avec actions de gestion
    (debloquer, bloquer, marquer sous surveillance, rappels) — RM-060 a
    RM-076, s'appuyant sur le moteur d'arrieres du Prompt 14."""
    organisateurs = Organisateur.query.filter(Organisateur.statut_compte != "actif").all()
    lignes = [
        {
            "organisateur": organisateur,
            "montant_du": verifier_arriere(organisateur.id)["montant_total_du"],
            "dernier_rappel": _dernier_rappel(organisateur.id),
        }
        for organisateur in organisateurs
    ]
    return render_template("agent/arrieres.html", lignes=lignes)


@agent_bp.route("/arrieres/<int:organisateur_id>/debloquer", methods=["POST"])
@role_required("agent", "admin")
def debloquer_organisateur(organisateur_id):
    """Reactive un compte et solde ses arrieres en attente (RM-075, RM-076)."""
    Organisateur.query.get_or_404(organisateur_id)
    debloquer_compte(organisateur_id)
    db.session.commit()

    flash("Compte débloqué et arriérés soldés.", "succes")
    return redirect(url_for("agent.arrieres"))


@agent_bp.route("/arrieres/<int:organisateur_id>/bloquer", methods=["POST"])
@role_required("agent", "admin")
def bloquer_organisateur(organisateur_id):
    """Gele manuellement un compte apres relances restees sans effet (RM-075)."""
    Organisateur.query.get_or_404(organisateur_id)
    bloquer_compte(organisateur_id)
    db.session.commit()

    flash("Compte bloqué.", "succes")
    return redirect(url_for("agent.arrieres"))


@agent_bp.route("/arrieres/envoyer-rappels", methods=["POST"])
@role_required("agent", "admin")
def envoyer_rappels():
    """Declenche l'envoi des rappels aux organisateurs en retard (RM-070 a
    RM-072)."""
    nombre = verifier_et_envoyer_rappels()

    flash(f"{nombre} rappel(s) envoyé(s).", "succes")
    return redirect(url_for("agent.arrieres"))


@agent_bp.route("/surveillance")
@role_required("agent", "admin")
def surveillance():
    """Alertes de surveillance non traitees et comptes actuellement sous
    surveillance (RM-080 a RM-084)."""
    alertes = (
        AlerteSurveillance.query.filter_by(traitee=False).order_by(AlerteSurveillance.date_marquage.desc()).all()
    )
    comptes_surveilles = Organisateur.query.filter_by(statut_compte="surveillance").all()
    return render_template("agent/surveillance.html", alertes=alertes, comptes_surveilles=comptes_surveilles)


@agent_bp.route("/surveillance/<int:alerte_id>/traiter", methods=["POST"])
@role_required("agent", "admin")
def traiter_alerte(alerte_id):
    """Marque une alerte de surveillance comme traitee par l'agent connecte."""
    alerte = AlerteSurveillance.query.get_or_404(alerte_id)
    alerte.traitee = True
    alerte.date_traitement = datetime.utcnow()
    alerte.traite_par = current_user.id
    db.session.commit()

    flash("Alerte marquée comme traitée.", "succes")
    return redirect(url_for("agent.surveillance"))


@agent_bp.route("/surveillance/<int:organisateur_id>/marquer", methods=["POST"])
@role_required("agent", "admin")
def marquer_organisateur_surveillance(organisateur_id):
    """Place un compte sous surveillance, avec un commentaire obligatoire
    expliquant le motif (RM-080)."""
    Organisateur.query.get_or_404(organisateur_id)
    commentaire = request.form.get("commentaire", "").strip()
    if not commentaire:
        flash("Un commentaire est obligatoire pour marquer un compte sous surveillance.", "erreur")
        return redirect(url_for("agent.arrieres"))

    marquer_surveillance(organisateur_id, current_user.id, commentaire=commentaire)
    db.session.commit()

    flash("Compte placé sous surveillance.", "succes")
    return redirect(url_for("agent.arrieres"))


@agent_bp.route("/surveillance/<int:organisateur_id>/lever", methods=["POST"])
@role_required("agent", "admin")
def lever_organisateur_surveillance(organisateur_id):
    """Leve la surveillance d'un compte et solde ses alertes en attente
    (RM-084)."""
    Organisateur.query.get_or_404(organisateur_id)
    lever_surveillance(organisateur_id, current_user.id)
    db.session.commit()

    flash("Surveillance levée.", "succes")
    return redirect(url_for("agent.surveillance"))
