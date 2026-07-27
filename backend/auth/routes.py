"""Inscription, connexion et deconnexion.

Regles metier appliquees ici : RM-001 a RM-005 (acces), RM-080/RM-081
(alerte immediate a la reconnexion d'un compte sous surveillance).
"""

import re

import bcrypt
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.arrieres.moteur import verifier_connexion_surveillance
from backend.notifications.email_service import notifier_reinitialisation_mot_de_passe
from extensions import db, limiter
from models import Organisateur, Utilisateur

from . import auth_bp

DUREE_JETON_RESET_SECONDES = 3600
SEL_JETON_RESET = "bbda-reset-mdp"

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
@limiter.limit("8 per minute")
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


def _serializer_reset_mdp():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=SEL_JETON_RESET)


def _creer_jeton_reset(utilisateur_id):
    return _serializer_reset_mdp().dumps({"uid": utilisateur_id})


def _lire_jeton_reset(jeton):
    """Retourne l'id utilisateur ou None si jeton invalide/expire."""
    try:
        donnees = _serializer_reset_mdp().loads(jeton, max_age=DUREE_JETON_RESET_SECONDES)
    except (BadSignature, SignatureExpired):
        return None
    return donnees.get("uid")


@auth_bp.route("/mot-de-passe-oublie", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def mot_de_passe_oublie():
    """Demande un lien de reinitialisation (ne revele pas si l'email existe)."""
    if request.method == "GET":
        return render_template("auth/mot_de_passe_oublie.html")

    email = request.form.get("email", "").strip().lower()
    utilisateur = Utilisateur.query.filter_by(email=email, statut="actif").first()
    if utilisateur:
        jeton = _creer_jeton_reset(utilisateur.id)
        chemin = url_for("auth.reinitialiser_mot_de_passe", jeton=jeton)
        base = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
        lien = f"{base}{chemin}" if base else url_for(
            "auth.reinitialiser_mot_de_passe", jeton=jeton, _external=True
        )
        try:
            notifier_reinitialisation_mot_de_passe(utilisateur, lien)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Echec envoi reset mot de passe")

    flash(
        "Si un compte actif existe pour cet email, un lien de réinitialisation a été envoyé.",
        "succes",
    )
    return redirect(url_for("auth.connexion"))


@auth_bp.route("/reinitialiser-mot-de-passe/<jeton>", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def reinitialiser_mot_de_passe(jeton):
    """Choisit un nouveau mot de passe via le jeton email (valable 1 h)."""
    utilisateur_id = _lire_jeton_reset(jeton)
    if utilisateur_id is None:
        flash("Ce lien de réinitialisation est invalide ou a expiré.", "erreur")
        return redirect(url_for("auth.mot_de_passe_oublie"))

    utilisateur = Utilisateur.query.filter_by(id=utilisateur_id, statut="actif").first()
    if utilisateur is None:
        flash("Ce compte n'est plus disponible.", "erreur")
        return redirect(url_for("auth.connexion"))

    if request.method == "GET":
        return render_template("auth/reinitialiser_mot_de_passe.html", jeton=jeton)

    nouveau = request.form.get("nouveau_mot_de_passe", "")
    confirmation = request.form.get("confirmation", "")
    if len(nouveau) < 8:
        flash("Le mot de passe doit contenir au moins 8 caractères.", "erreur")
        return render_template("auth/reinitialiser_mot_de_passe.html", jeton=jeton), 400
    if nouveau != confirmation:
        flash("La confirmation ne correspond pas.", "erreur")
        return render_template("auth/reinitialiser_mot_de_passe.html", jeton=jeton), 400

    utilisateur.mot_de_passe = _hacher(nouveau)
    db.session.commit()
    flash("Mot de passe mis à jour. Vous pouvez vous connecter.", "succes")
    return redirect(url_for("auth.connexion"))


@auth_bp.route("/connexion", methods=["GET", "POST"])
@limiter.limit("10 per minute")
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
        flash(
            "Ce compte a été désactivé ou supprimé. Contactez le BBDA pour le réactiver.",
            "erreur",
        )
        return render_template("auth/connexion.html"), 403

    login_user(utilisateur, remember=True)

    if utilisateur.role == "organisateur":
        _signaler_reconnexion_surveillance(utilisateur)

    return redirect(url_for(DESTINATION_PAR_ROLE[utilisateur.role]))


@auth_bp.route("/parametres")
@login_required
def parametres():
    """Page parametres du compte (infos, mot de passe, suppression orga)."""
    return render_template(
        "auth/parametres.html",
        espace_url=url_for(DESTINATION_PAR_ROLE.get(current_user.role, "public.accueil")),
    )


@auth_bp.route("/changer-mot-de-passe", methods=["GET", "POST"])
@login_required
def changer_mot_de_passe():
    """Permet a tout utilisateur connecte de changer son mot de passe."""
    if request.method == "GET":
        return render_template("auth/changer_mot_de_passe.html")

    actuel = request.form.get("mot_de_passe_actuel", "")
    nouveau = request.form.get("nouveau_mot_de_passe", "")
    confirmation = request.form.get("confirmation", "")

    if not _mot_de_passe_valide(actuel, current_user.mot_de_passe):
        flash("Mot de passe actuel incorrect.", "erreur")
        return render_template("auth/changer_mot_de_passe.html"), 400

    if len(nouveau) < 8:
        flash("Le nouveau mot de passe doit contenir au moins 8 caractères.", "erreur")
        return render_template("auth/changer_mot_de_passe.html"), 400

    if nouveau != confirmation:
        flash("La confirmation ne correspond pas au nouveau mot de passe.", "erreur")
        return render_template("auth/changer_mot_de_passe.html"), 400

    if nouveau == actuel:
        flash("Le nouveau mot de passe doit être différent de l'actuel.", "erreur")
        return render_template("auth/changer_mot_de_passe.html"), 400

    current_user.mot_de_passe = _hacher(nouveau)
    db.session.commit()
    flash("Mot de passe mis à jour. Utilisez-le dès la prochaine connexion.", "succes")
    return redirect(url_for("auth.parametres"))


@auth_bp.route("/supprimer-compte", methods=["GET", "POST"])
@login_required
def supprimer_compte():
    """Desactive le compte de l'organisateur connecte (soft-delete).

    Les agents/admins ne peuvent pas s'auto-supprimer ici : gestion via
    l'espace admin. Les declarations restent en base pour le BBDA.
    Apres suppression, la connexion et une nouvelle inscription avec le
    meme email sont refusees tant que le BBDA ne reactive pas le compte.
    """
    if current_user.role != "organisateur":
        flash("Seuls les organisateurs peuvent supprimer leur compte depuis cet écran.", "erreur")
        return redirect(url_for(DESTINATION_PAR_ROLE.get(current_user.role, "public.accueil")))

    if request.method == "GET":
        return render_template("auth/supprimer_compte.html")

    if request.form.get("confirmer") != "oui":
        flash("Suppression annulée.", "info")
        return redirect(url_for("auth.parametres"))

    current_user.statut = "inactif"
    db.session.commit()
    logout_user()
    flash(
        "Votre compte a été supprimé. Vous ne pouvez plus vous connecter avec cet email.",
        "succes",
    )
    return redirect(url_for("public.accueil"))


@auth_bp.route("/deconnexion")
@login_required
def deconnexion():
    """Termine la session de l'utilisateur connecte (RM-001 : la face
    publique reste accessible sans connexion apres deconnexion)."""
    logout_user()
    flash("Vous avez été déconnecté.", "succes")
    return redirect(url_for("public.accueil"))
