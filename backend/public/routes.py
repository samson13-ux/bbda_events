"""Routes de la face publique (Prompts 18 et 19).

Accueil marketing, listing des evenements promus (RM-090 a RM-093),
page de detail, placeholder billetterie, support (FAQ), contact
(MessageContact), et pages legales.
"""

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import or_
from sqlalchemy.exc import ProgrammingError, OperationalError

from backend.notifications.email_service import notifier_message_contact
from extensions import db
from models import Declaration, MessageContact

from . import public_bp


def _evenements_publics(filtres=None):
    """Declarations visibles sur la face publique : promouvoir=True ET
    statut=quittance_delivree (RM-090, RM-091)."""
    requete = Declaration.query.filter_by(promouvoir=True, statut="quittance_delivree")
    if filtres:
        if filtres.get("ville"):
            requete = requete.filter(Declaration.ville.ilike(f"%{filtres['ville']}%"))
        if filtres.get("type"):
            requete = requete.filter_by(nature_manifestation=filtres["type"])
        if filtres.get("recherche"):
            terme = f"%{filtres['recherche']}%"
            requete = requete.filter(
                or_(
                    Declaration.nom_artiste_evenement.ilike(terme),
                    Declaration.nom_salle.ilike(terme),
                    Declaration.ville.ilike(terme),
                )
            )
    return requete.order_by(Declaration.date_evenement.asc()).all()


def _assurer_tables():
    """Recree les tables si Postgres a perdu le schema (plan free / redemarrage)."""
    try:
        db.create_all()
    except Exception:
        current_app.logger.exception("Impossible de recreer les tables")


@public_bp.route("/")
def accueil():
    """Page d'accueil publique style Veenue adaptee au BBDA."""
    return render_template("public/accueil.html")


@public_bp.route("/evenements")
def evenements():
    """Listing public des evenements culturels promus et autorises."""
    filtres = {
        "recherche": request.args.get("recherche", "").strip(),
        "ville": request.args.get("ville", "").strip(),
        "type": request.args.get("type", "").strip(),
    }
    types_disponibles = [
        "Concert",
        "Festival",
        "Spectacle",
        "Gala",
        "Soirée culturelle",
        "Exposition",
    ]
    try:
        liste = _evenements_publics(filtres)
    except (ProgrammingError, OperationalError):
        current_app.logger.exception("Lecture evenements publics echouee, tentative create_all")
        db.session.rollback()
        _assurer_tables()
        try:
            liste = _evenements_publics(filtres)
        except (ProgrammingError, OperationalError):
            db.session.rollback()
            flash(
                "Le catalogue est temporairement indisponible (base de données). "
                "Réessaie dans une minute.",
                "erreur",
            )
            liste = []
    return render_template(
        "public/evenements.html",
        evenements=liste,
        filtres=filtres,
        types_disponibles=types_disponibles,
    )


@public_bp.route("/evenements/<int:declaration_id>")
def detail_evenement(declaration_id):
    """Page de detail d'un evenement public (RM-090 a RM-093). Renvoie 404
    si l'evenement n'est pas promu ou n'a pas de quittance delivree."""
    declaration = Declaration.query.get_or_404(declaration_id)
    if not declaration.promouvoir or declaration.statut != "quittance_delivree":
        abort(404)
    return render_template("public/detail_evenement.html", evenement=declaration)


@public_bp.route("/billetterie-bientot")
def billetterie_bientot():
    """Placeholder de la future billetterie en ligne."""
    return render_template("public/billetterie_bientot.html")


@public_bp.route("/support")
def support():
    """FAQ et aide aux organisateurs."""
    return render_template("public/support.html")


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Formulaire de contact : enregistre un MessageContact en base."""
    if request.method == "POST":
        erreurs = []
        for champ, libelle in (("nom", "Le nom"), ("email", "L'email"), ("sujet", "Le sujet"), ("message", "Le message")):
            if not request.form.get(champ, "").strip():
                erreurs.append(f"{libelle} est requis.")
        if erreurs:
            for message in erreurs:
                flash(message, "erreur")
            return render_template("public/contact.html", donnees=request.form), 400

        message_contact = MessageContact(
            nom=request.form["nom"].strip(),
            email=request.form["email"].strip(),
            sujet=request.form["sujet"].strip(),
            message=request.form["message"].strip(),
        )
        db.session.add(message_contact)
        db.session.flush()
        notifier_message_contact(message_contact)
        db.session.commit()
        flash("Votre message a bien été envoyé. Le BBDA vous répondra dans les meilleurs délais.", "succes")
        return redirect(url_for("public.contact"))

    return render_template("public/contact.html")


@public_bp.route("/legal/confidentialite")
def confidentialite():
    """Politique de confidentialite BBDA."""
    return render_template("public/legal/confidentialite.html")


@public_bp.route("/legal/cgu")
def cgu():
    """Conditions generales d'utilisation."""
    return render_template("public/legal/cgu.html")


@public_bp.route("/legal/politique-organisateur")
def politique_organisateur():
    """Politique de l'organisateur."""
    return render_template("public/legal/politique_organisateur.html")


@public_bp.route("/legal/politique-public")
def politique_public():
    """Politique du public / spectateurs."""
    return render_template("public/legal/politique_public.html")
