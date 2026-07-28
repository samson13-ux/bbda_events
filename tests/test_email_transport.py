"""Tests envoi email : SMTP local et SendGrid prioritaire."""

from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from backend.notifications.email_service import _envoyer
from extensions import db
from models import Notification, Utilisateur


@pytest.fixture
def app_smtp():
    application = create_app("testing")
    application.config["SENDGRID_API_KEY"] = ""
    application.config["MAIL_USERNAME"] = "bbda.events@test.local"
    application.config["MAIL_PASSWORD"] = "app-password-test"
    application.config["MAIL_DEFAULT_SENDER"] = "bbda.events@test.local"
    application.config["MAIL_SUPPRESS_SEND"] = False
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def app_sendgrid():
    application = create_app("testing")
    application.config["SENDGRID_API_KEY"] = "SG.test-key"
    application.config["MAIL_USERNAME"] = "bbda.events@test.local"
    application.config["MAIL_DEFAULT_SENDER"] = "bbda.events@test.local"
    application.config["MAIL_SUPPRESS_SEND"] = False
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


def _notif(app):
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
    return notification


def test_envoyer_passe_par_smtp(app_smtp):
    with app_smtp.app_context():
        notification = _notif(app_smtp)
        with patch("backend.notifications.email_service.mail.send") as mock_send:
            _envoyer(notification, "dest@example.com", "<p>Hello</p>")
        assert notification.statut == "envoyee"
        assert mock_send.called


def test_envoyer_passe_par_sendgrid(app_sendgrid):
    with app_sendgrid.app_context():
        notification = _notif(app_sendgrid)
        reponse_mock = MagicMock()
        reponse_mock.status = 202
        reponse_mock.read.return_value = b""
        reponse_mock.__enter__.return_value = reponse_mock
        reponse_mock.__exit__.return_value = False
        with patch(
            "backend.notifications.email_service.urllib.request.urlopen",
            return_value=reponse_mock,
        ) as mock_open:
            _envoyer(notification, "dest@example.com", "<p>Hello</p>")
        assert notification.statut == "envoyee"
        assert "api.sendgrid.com" in mock_open.call_args[0][0].full_url
