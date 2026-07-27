"""Test du bouton admin d'envoi email de diagnostic."""

from unittest.mock import patch

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Utilisateur


@pytest.fixture
def app():
    application = create_app("testing")
    application.config["BREVO_API_KEY"] = "xkeysib-test"
    application.config["MAIL_USERNAME"] = "bbda.events@test.local"
    application.config["MAIL_DEFAULT_SENDER"] = "bbda.events@test.local"
    application.config["MAIL_SUPPRESS_SEND"] = False
    with application.app_context():
        db.create_all()
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        db.session.add(
            Utilisateur(
                nom="Admin",
                prenom="Test",
                email="admin@bbda.bf",
                mot_de_passe=hachage,
                role="admin",
            )
        )
        db.session.commit()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _connecter_admin(client):
    client.post(
        "/auth/connexion",
        data={"email": "admin@bbda.bf", "password": "password123"},
    )


def test_tester_email_affiche_succes(app, client):
    _connecter_admin(client)
    with patch("backend.admin.routes.tester_envoi_email", return_value=(True, "OK test")):
        reponse = client.post(
            "/admin/parametres/tester-email",
            data={"email_test": "dest@example.com"},
            follow_redirects=True,
        )
    page = reponse.get_data(as_text=True)
    assert reponse.status_code == 200
    assert "OK test" in page


def test_parametres_affiche_statut_brevo(app, client):
    _connecter_admin(client)
    page = client.get("/admin/parametres").get_data(as_text=True)
    assert "Test email" in page
    assert "configuré" in page
