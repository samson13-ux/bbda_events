"""Configurations Flask (developpement et production) pour BBDA Events."""

import os
import tempfile

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration commune a tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-remplacer")
    # Render fournit souvent postgres://... ; SQLAlchemy + psycopg veulent postgresql+psycopg://
    _database_url = os.environ.get("DATABASE_URL", "")
    if _database_url.startswith("postgres://"):
        _database_url = "postgresql+psycopg://" + _database_url[len("postgres://") :]
    elif _database_url.startswith("postgresql://"):
        _database_url = "postgresql+psycopg://" + _database_url[len("postgresql://") :]
    # URL externe Render (*.render.com) : SSL souvent obligatoire
    if _database_url and "render.com" in _database_url and "sslmode=" not in _database_url:
        _database_url += ("&" if "?" in _database_url else "?") + "sslmode=require"
    SQLALCHEMY_DATABASE_URI = _database_url or None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 Mo, cf. RM-023
    UPLOAD_FOLDER = os.path.join("frontend", "static", "uploads")
    QUITTANCE_FOLDER = os.path.join("frontend", "static", "quittances")

    # URL publique (tunnel Cloudflare / hebergement). Si defini, les liens
    # des emails pointent vers cette adresse au lieu de 127.0.0.1.
    # Exemple : https://xxxx.trycloudflare.com
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")


class DevelopmentConfig(Config):
    """Configuration utilisee en developpement local."""

    DEBUG = True


class ProductionConfig(Config):
    """Configuration utilisee en production (ex. PythonAnywhere)."""

    DEBUG = False
    # Evite les sessions / cookies cassés derrière HTTPS (PythonAnywhere, tunnels).
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuration utilisee par la suite de tests (SQLite en memoire)."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    # Empeche Flask-Mail de tenter un envoi SMTP reel pendant les tests
    # automatises (pas d'acces reseau garanti, et pas souhaitable).
    MAIL_SUPPRESS_SEND = True
    MAIL_USERNAME = "bbda.events@test.local"
    MAIL_DEFAULT_SENDER = "bbda.events@test.local"
    # Les PDF et uploads generes pendant les tests ne doivent pas polluer
    # les dossiers reels de developpement.
    QUITTANCE_FOLDER = os.path.join(tempfile.gettempdir(), "bbda_events_test_quittances")
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "bbda_events_test_uploads")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
