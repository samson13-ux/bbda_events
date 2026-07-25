"""Routes d'authentification : inscription (organisateur), connexion,
deconnexion. Implementation complete du Prompt 4 du guide de dev.

Regles metier appliquees ici : RM-001 a RM-005 (acces), RM-080/RM-081
(alerte immediate a la reconnexion d'un compte sous surveillance).
"""

import re

import bcrypt
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import OperationalError, ProgrammingError

from extensions import db
from models import Organisateur, Utilisateur

from backend.arrieres.moteur import verifier_connexion_surveillance

from . import auth_bp

REGEX_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

CHAMPS_INSCRIPTION_REQUIS = (
    ("nom", "Le nom"),
    ("prenom", "Le prénom"),
    ("qualite", "La qualité"),
    ("telephone", "Le téléphone"),
    ("email", "L'email"),
    ("password", "Le mot de passe"),
)

DESTINATION_PAR_ROLE = {
    "organisateur": "declarations.tableau_de_bord",
    "agent": "agent.tableau_de_bord",
    "admin": "admin.tableau_de_bord",
}


def _hacher(mot_de_passe):
    """Hache un mot de passe en clair avec bcrypt (AI_RULES.md §5)."""
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _mot_de_passe_valide(mot_de_passe_clair, hachage):
    """Verifie un mot de passe en clair contre son hachage bcrypt stocke."""
    return bcrypt.checkpw(mot_de_passe_clair.encode("utf-8"), hachage.encode("utf-8"))


def _valider_inscription(donnees):
    """Valide les champs du formulaire d'inscription et retourne la liste
    (eventuellement vide) des messages d'erreur."""
    erreurs = []

    for champ, libelle in CHAMPS_INSCRIPTION_REQUIS:
        if not donnees.get(champ, "").strip():
            erreurs.append(f"{libelle} est requis.")

    email = donnees.get("email", "").strip().lower()
    if email and not REGEX_EMAIL.match(email):
        erreurs.append("L'adresse email n'est pas valide.")
    elif email and Utilisateur.query.filter_by(email=email).first():
        erreurs.append("Un compte existe déjà avec cette adresse email.")

    mot_de_passe = donnees.get("password", "")
    if mot_de_passe and len(mot_de_passe) < 8:
        erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")
    if mot_de_passe and mot_de_passe != donnees.get("confirm", ""):
        erreurs.append("Les deux mots de passe ne correspondent pas.")

    if not donnees.get("cgu"):
        erreurs.append("Vous devez accepter les conditions générales d'utilisation.")

    return erreurs


@auth_bp.route("/inscription", methods=["GET", "POST"])
def inscription():
    """Cree un compte organisateur (seul role ouvert a l'auto-inscription,
    RM-002 : agent et admin sont crees par l'administration, pas via ce
    formulaire public)."""
    if request.method == "GET":
        return render_template("auth/inscription.html")

    erreurs = _valider_inscription(request.form)
    if erreurs:
        for message in erreurs:
            flash(message, "erreur")
        return render_template("auth/inscription.html", donnees=request.form), 400

    try:
        utilisateur = Utilisateur(
            nom=request.form["nom"].strip(),
            prenom=request.form["prenom"].strip(),
            email=request.form["email"].strip().lower(),
            mot_de_passe=_hacher(request.form["password"]),
            role="organisateur",
        )
        db.session.add(utilisateur)
        db.session.flush()  # obtenir utilisateur.id avant de creer le profil lie

        db.session.add(
            Organisateur(
                utilisateur_id=utilisateur.id,
                qualite=request.form["qualite"].strip(),
                telephone=request.form["telephone"].strip(),
            )
        )
        db.session.commit()
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        current_app.logger.exception("Inscription echouee (schema DB), tentative create_all")
        try:
            db.create_all()
        except Exception:
            current_app.logger.exception("create_all apres echec inscription")
        flash(
            "Erreur de base de données. Vérifie sur Render que Postgres est Available, "
            "puis réessaie dans une minute.",
            "erreur",
        )
        return render_template("auth/inscription.html", donnees=request.form), 503

    flash("Compte créé avec succès. Vous pouvez maintenant vous connecter.", "succes")
    return redirect(url_for("auth.connexion"))


def _signaler_reconnexion_surveillance(utilisateur):
    """RM-081 : delegue au moteur d'arrieres la detection d'une reconnexion
    sous surveillance (creation d'alerte + notification des agents)."""
    organisateur = utilisateur.organisateur
    if organisateur and verifier_connexion_surveillance(organisateur.id):
        db.session.commit()


@auth_bp.route("/connexion", methods=["GET", "POST"])
def connexion():
    """Authentifie un utilisateur (organisateur, agent ou admin) et le
    redirige vers son espace personnel selon son role."""
    if request.method == "GET":
        return render_template("auth/connexion.html")

    email = request.form.get("email", "").strip().lower()
    mot_de_passe = request.form.get("password", "")

    utilisateur = Utilisateur.query.filter_by(email=email).first()
    identifiants_valides = utilisateur is not None and _mot_de_passe_valide(mot_de_passe, utilisateur.mot_de_passe)

    if not identifiants_valides:
        flash("Email ou mot de passe incorrect.", "erreur")
        return render_template("auth/connexion.html"), 401

    if utilisateur.statut != "actif":
        flash("Ce compte est inactif. Contactez le BBDA.", "erreur")
        return render_template("auth/connexion.html"), 403

    login_user(utilisateur, remember=bool(request.form.get("remember")))

    if utilisateur.role == "organisateur":
        _signaler_reconnexion_surveillance(utilisateur)

    return redirect(url_for(DESTINATION_PAR_ROLE[utilisateur.role]))


@auth_bp.route("/supprimer-compte", methods=["GET", "POST"])
@login_required
def supprimer_compte():
    """Desactive le compte de l'organisateur connecte (soft-delete).

    Les agents/admins ne peuvent pas s'auto-supprimer ici : gestion via
    l'espace admin. Les declarations restent en base pour le BBDA.
    """
    if current_user.role != "organisateur":
        flash("Seuls les organisateurs peuvent supprimer leur compte depuis cet écran.", "erreur")
        return redirect(url_for(DESTINATION_PAR_ROLE.get(current_user.role, "public.accueil")))

    if request.method == "GET":
        return render_template("auth/supprimer_compte.html")

    if request.form.get("confirmation", "").strip().upper() != "SUPPRIMER":
        flash("Confirmation incorrecte. Tapez SUPPRIMER pour valider.", "erreur")
        return render_template("auth/supprimer_compte.html"), 400

    current_user.statut = "inactif"
    db.session.commit()
    logout_user()
    flash("Votre compte a été désactivé. Vous ne pouvez plus vous connecter.", "succes")
    return redirect(url_for("public.accueil"))


@auth_bp.route("/deconnexion")
@login_required
def deconnexion():
    """Termine la session de l'utilisateur connecte (RM-001 : la face
    publique reste accessible sans connexion apres deconnexion)."""
    logout_user()
    flash("Vous avez été déconnecté.", "succes")
    return redirect(url_for("public.accueil"))
