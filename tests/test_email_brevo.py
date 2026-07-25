"""Partie emails : envoi via API Brevo (HTTPS) quand BREVO_API_KEY est defini."""

from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from backend.notifications.email_service import _envoyer
from extensions import db
from models import Notification, Utilisateur


@pytest.fixture
def app():
    application = create_app("testing")
    application.config["BREVO_API_KEY"] = "xkeysib-test"
    application.config["MAIL_USERNAME"] = "bbda.events@test.local"
    application.config["MAIL_DEFAULT_SENDER"] = "bbda.events@test.local"
    application.config["MAIL_SUPPRESS_SEND"] = False
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


def test_envoi_passe_par_brevo_quand_cle_presente(app):
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

        reponse_mock = MagicMock()
        reponse_mock.status = 201
        reponse_mock.read.return_value = b"{}"
        reponse_mock.__enter__.return_value = reponse_mock
        reponse_mock.__exit__.return_value = False

        with patch("backend.notifications.email_service.urllib.request.urlopen", return_value=reponse_mock) as mock_open:
            _envoyer(notification, "dest@example.com", "<p>Hello</p>")

        assert notification.statut == "envoyee"
        assert mock_open.called
        requete = mock_open.call_args[0][0]
        assert "api.brevo.com/v3/smtp/email" in requete.full_url
        assert requete.headers.get("Api-key") == "xkeysib-test" or requete.get_header("Api-key") == "xkeysib-test"
