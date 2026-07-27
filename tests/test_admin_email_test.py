"""Test email admin et chemin SMTP (sans fournisseurs tiers)."""

from unittest.mock import patch

import bcrypt
import pytest

from app import create_app
from backend.notifications.email_service import _envoyer
from extensions import db
from models import Notification, Utilisateur


@pytest.fixture
def app():
    application = create_app("testing")
    application.config["MAIL_USERNAME"] = "bbda.events@test.local"
    application.config["MAIL_PASSWORD"] = "app-password-test"
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


def test_envoyer_passe_par_smtp_flask_mail(app):
    with app.app_context():
        destinataire = Utilisateur(
            nom="Test",
            prenom="Mail",
            email="dest@example.com",
            mot_de_passe="x",
            role="organisateur",
        )
        db.session.add(destinataire)
        db.session.flush()
        notification = Notification(
            destinataire_id=destinataire.id,
            type_notification="test",
            sujet="Sujet test",
            message="Corps",
            canal="email",
            statut="en_attente",
        )
        db.session.add(notification)
        db.session.flush()

        with patch("backend.notifications.email_service.mail.send") as mock_send:
            _envoyer(notification, "dest@example.com", "<p>Hello</p>")

        assert notification.statut == "envoyee"
        assert mock_send.called


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


def test_parametres_affiche_statut_smtp(app, client):
    _connecter_admin(client)
    page = client.get("/admin/parametres").get_data(as_text=True)
    assert "Test email (SMTP Gmail)" in page
    assert "configuré" in page
