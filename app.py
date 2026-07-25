"""Point d'entree de l'application BBDA Events (factory pattern Flask)."""

import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import ProductionConfig, config_by_name
from extensions import csrf, db, limiter, login_manager, mail


def create_app(env=None):
    """Cree et configure l'instance Flask de l'application.

    :param env: nom de l'environnement ('development', 'production' ou 'testing').
        Si non fourni, lu depuis FLASK_ENV / FLASK_CONFIG, sinon Render→production.
    :return: instance Flask configuree, avec extensions et blueprints enregistres.
    """
    env = env or os.environ.get("FLASK_ENV") or os.environ.get("FLASK_CONFIG")
    # Render et proxies HTTPS : forcer production si l'env n'est pas explicite.
    if not env:
        env = "production" if os.environ.get("RENDER") else "development"

    if env == "production":
        ProductionConfig.valider_secret_key()

    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    app.config.from_object(config_by_name[env])

    # Derriere un tunnel HTTPS (Cloudflare) ou un reverse-proxy : respecter
    # le schema et le host publics pour les cookies et url_for(_external).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    import models  # noqa: F401 — enregistre les modeles et le user_loader

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["QUITTANCE_FOLDER"], exist_ok=True)

    _register_blueprints(app)
    _configurer_login_manager()
    _configurer_gestion_erreurs(app)
    _bootstrap_schema_si_besoin(app)

    return app


def _bootstrap_schema_si_besoin(app):
    """Sur Render (sans Shell), cree les tables + admin si la base est vide.

    Ne fait rien si des utilisateurs existent deja. Ignore en mode testing.
    """
    if app.config.get("TESTING"):
        return
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            app.logger.exception("Bootstrap create_all a echoue")
            return
        try:
            from models import Utilisateur

            if Utilisateur.query.first() is None:
                from init_db import seed_base_vide

                app.logger.info("Bootstrap : base vide, creation admin...")
                seed_base_vide()
        except ValueError as erreur:
            db.session.rollback()
            app.logger.error("Bootstrap admin refuse : %s", erreur)
        except Exception:
            # Ne bloque pas le demarrage : les logs Render montreront la cause.
            db.session.rollback()
            app.logger.exception("Bootstrap admin a echoue (verifie DATABASE_URL / Postgres Available)")
        finally:
            # Important avant un fork Gunicorn : ne pas laisser de connexion SSL
            # ouverte dans le process maitre (sinon "bad record mac").
            try:
                db.session.remove()
                db.engine.dispose()
            except Exception:
                pass


def _configurer_login_manager():
    """Configure la redirection Flask-Login pour les acces anonymes a une
    route protegee (RM-002, RM-003)."""
    login_manager.login_view = "auth.connexion"
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
    login_manager.login_message_category = "erreur"


def _configurer_gestion_erreurs(app):
    """Messages utilisateur pour les erreurs HTTP courantes."""
    from flask import flash, redirect, request, url_for
    from flask_wtf.csrf import CSRFError
    from werkzeug.exceptions import RequestEntityTooLarge

    @app.errorhandler(RequestEntityTooLarge)
    def _fichier_trop_volumineux(_erreur):
        """RM-023 : affiche trop lourde (> MAX_CONTENT_LENGTH, 2 Mo)."""
        flash(
            "Le fichier envoyé est trop volumineux. L'affiche doit être en JPG ou PNG "
            "et ne pas dépasser 2 Mo. Compressez l'image puis réessayez.",
            "erreur",
        )
        cible = request.referrer or url_for("declarations.nouvelle")
        return redirect(cible)

    @app.errorhandler(CSRFError)
    def _csrf_invalide(_erreur):
        flash(
            "Session de formulaire expirée ou invalide. Rechargez la page puis réessayez.",
            "erreur",
        )
        cible = request.referrer or url_for("public.accueil")
        return redirect(cible)

    @app.errorhandler(429)
    def _trop_de_requetes(_erreur):
        flash(
            "Trop de tentatives. Attendez une minute puis réessayez.",
            "erreur",
        )
        cible = request.referrer or url_for("public.accueil")
        return redirect(cible), 429


def _register_blueprints(app):
    """Enregistre tous les blueprints Flask du projet sur l'application."""
    from backend.admin import admin_bp
    from backend.agent import agent_bp
    from backend.auth import auth_bp
    from backend.declarations import declarations_bp
    from backend.exports import exports_bp
    from backend.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(declarations_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(exports_bp)


if __name__ == "__main__":
    create_app().run()
