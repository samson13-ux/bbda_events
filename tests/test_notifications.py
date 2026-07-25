"""Tests du module de notifications par email (Prompt 13) : envoi HTML reel
via Flask-Mail (suppresse en environnement de test), journalisation en base
avant envoi, mise a jour du statut apres tentative, et declenchement correct
des 6 fonctions depuis les routes concernees (RM-014, RM-033, RM-054, RM-081)."""

from datetime import datetime, timedelta

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Arriere, Notification, Organisateur, Utilisateur


@pytest.fixture
def app():
    """Cree une instance d'application en configuration de test (MAIL_SUPPRESS_SEND
    actif : aucun envoi SMTP reel n'est tente)."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def creer_organisateur(app, email, statut_compte="actif", mot_de_passe="password123"):
    with app.app_context():
        hachage = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Ouedraogo", prenom="Boubacar", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000", statut_compte=statut_compte
        )
        db.session.add(organisateur)
        db.session.commit()
        return organisateur.id


def creer_agent(app, email, role="agent"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Kabore", prenom="Agent", email=email, mot_de_passe=hachage, role=role)
        db.session.add(utilisateur)
        db.session.commit()
        return utilisateur.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_confirmation_declaration_est_envoyee_et_marquee(app, client):
    """La notification de confirmation de declaration passe au statut
    'envoyee' une fois la tentative SMTP effectuee (suppressee en test, donc
    aucune exception : le statut n'est jamais 'echouee' ici)."""
    creer_organisateur(app, "orga_confirm@example.com")
    connecter(client, "orga_confirm@example.com")
    donnees = {
        "nom_demandeur": "Ouedraogo",
        "prenom_demandeur": "Boubacar",
        "qualite": "Organisateur",
        "telephone": "70000001",
        "email": "orga_confirm@example.com",
        "nature_manifestation": "Concert",
        "nom_artiste_evenement": "Floby",
        "nom_salle": "Salle des fetes",
        "adresse": "Avenue Kwame Nkrumah",
        "ville": "Ouagadougou",
        "duree_heures": "3",
        "capacite_accueil": "500",
        "entree": "payante",
        "nature_diffusion": "vivante",
        "date_evenement": (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M"),
    }

    client.post("/declarations/nouvelle", data=donnees)

    with app.app_context():
        notification = Notification.query.filter_by(type_notification="confirmation_declaration").first()
        assert notification is not None
        assert notification.statut == "envoyee"
        assert "reçue avec succès" in notification.sujet


def test_declaration_bloquee_notifie_organisateur(app, client):
    """RM-010/RM-074 : tenter d'acceder au formulaire avec un compte bloque
    declenche la notification 'declaration_bloquee' (FONCTION 6)."""
    creer_organisateur(app, "orga_bloque@example.com", statut_compte="bloque")
    connecter(client, "orga_bloque@example.com")

    reponse = client.get("/declarations/nouvelle", follow_redirects=False)

    assert reponse.status_code == 302
    with app.app_context():
        notification = Notification.query.filter_by(type_notification="declaration_bloquee").first()
        assert notification is not None
        assert notification.statut == "envoyee"


def test_alerte_surveillance_notifie_les_agents(app, client):
    """RM-081 : la reconnexion d'un compte 'surveillance' notifie tous les
    agents/administrateurs actifs (FONCTION 5)."""
    creer_agent(app, "agent1@example.com", role="agent")
    creer_agent(app, "admin1@example.com", role="admin")
    creer_organisateur(app, "orga_surveille@example.com", statut_compte="surveillance")

    connecter(client, "orga_surveille@example.com")

    with app.app_context():
        alertes = Notification.query.filter_by(type_notification="alerte_surveillance").all()
        assert len(alertes) == 2
        assert all(a.statut == "envoyee" for a in alertes)
        destinataires = {a.destinataire.email for a in alertes}
        assert destinataires == {"agent1@example.com", "admin1@example.com"}


def test_rappel_arriere_journalise_et_envoye(app):
    """FONCTION 4 : notifier_rappel_arriere enregistre puis tente l'envoi
    d'un rappel pour un arriere donne (pas encore declenchee automatiquement,
    le moteur de gestion des arrieres est prevu au Prompt 14)."""
    from backend.notifications.email_service import notifier_rappel_arriere

    organisateur_id = creer_organisateur(app, "orga_arriere@example.com")
    with app.app_context():
        organisateur = Organisateur.query.get(organisateur_id)
        arriere = Arriere(
            organisateur_id=organisateur.id,
            montant_du=5000,
            date_echeance=datetime.utcnow() - timedelta(days=1),
        )
        db.session.add(arriere)
        db.session.flush()

        notifier_rappel_arriere(arriere)
        db.session.commit()

        notification = Notification.query.filter_by(type_notification="rappel_arriere").first()
        assert notification is not None
        assert notification.statut == "envoyee"
        assert "5 000" in notification.message or "5000" in notification.message
