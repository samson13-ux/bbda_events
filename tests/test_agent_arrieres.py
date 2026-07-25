"""Tests de l'interface agent de gestion des arrieres et de la surveillance
(Prompt 15) : debloquer/bloquer un compte, envoyer les rappels, marquer/lever
une surveillance, et affichage des listes (RM-060 a RM-084)."""

from datetime import datetime, timedelta

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import AlerteSurveillance, Arriere, Organisateur, Utilisateur


@pytest.fixture
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def creer_agent(app, email="agent_i15@bbda.bf", role="agent"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        agent = Utilisateur(nom="Kabore", prenom="Issa", email=email, mot_de_passe=hachage, role=role)
        db.session.add(agent)
        db.session.commit()
        return agent.id


def creer_organisateur(app, email="orga_i15@example.com", statut_compte="actif"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Ouedraogo", prenom="Boubacar", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000", statut_compte=statut_compte
        )
        db.session.add(organisateur)
        db.session.commit()
        return organisateur.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_page_arrieres_affiche_montant_du(app, client):
    """La liste des organisateurs en difficulte affiche le montant total du."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, statut_compte="arriere")
    with app.app_context():
        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=1500, date_echeance=datetime.utcnow()))
        db.session.commit()
    connecter(client, "agent_i15@bbda.bf")

    reponse = client.get("/agent/arrieres")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "1500" in page or "1 500" in page
    assert "Boubacar" in page


def test_debloquer_organisateur_reactive_le_compte_et_solde_les_arrieres(app, client):
    """POST /agent/arrieres/<id>/debloquer reactive le compte et solde ses
    arrieres en attente (RM-075, RM-076)."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, statut_compte="bloque")
    with app.app_context():
        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=2000, date_echeance=datetime.utcnow()))
        db.session.commit()
    connecter(client, "agent_i15@bbda.bf")

    reponse = client.post(f"/agent/arrieres/{organisateur_id}/debloquer", follow_redirects=False)

    assert reponse.status_code == 302
    with app.app_context():
        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte == "actif"
        assert all(a.statut == "regle" for a in Arriere.query.filter_by(organisateur_id=organisateur_id).all())


def test_bloquer_organisateur_gele_le_compte(app, client):
    """POST /agent/arrieres/<id>/bloquer gele manuellement le compte (RM-075)."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, statut_compte="arriere")
    connecter(client, "agent_i15@bbda.bf")

    client.post(f"/agent/arrieres/{organisateur_id}/bloquer")

    with app.app_context():
        assert Organisateur.query.get(organisateur_id).statut_compte == "bloque"


def test_envoyer_rappels_declenche_les_notifications(app, client):
    """POST /agent/arrieres/envoyer-rappels appelle le moteur et affiche le
    nombre de rappels envoyes (RM-070 a RM-072)."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, statut_compte="arriere")
    with app.app_context():
        db.session.add(
            Arriere(
                organisateur_id=organisateur_id,
                montant_du=2000,
                date_echeance=datetime.utcnow() - timedelta(days=10),
            )
        )
        db.session.commit()
    connecter(client, "agent_i15@bbda.bf")

    reponse = client.post("/agent/arrieres/envoyer-rappels", follow_redirects=True)
    page = reponse.get_data(as_text=True)

    assert "1 rappel" in page
    with app.app_context():
        arriere = Arriere.query.filter_by(organisateur_id=organisateur_id).first()
        assert arriere.derniere_notification is not None


def test_marquer_surveillance_sans_commentaire_rejete(app, client):
    """RM-080 : un commentaire est obligatoire pour marquer un compte sous
    surveillance."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, statut_compte="arriere")
    connecter(client, "agent_i15@bbda.bf")

    client.post(f"/agent/surveillance/{organisateur_id}/marquer", data={"commentaire": ""})

    with app.app_context():
        assert Organisateur.query.get(organisateur_id).statut_compte == "arriere"
        assert AlerteSurveillance.query.count() == 0


def test_marquer_surveillance_avec_commentaire(app, client):
    """RM-080 : marque le compte sous surveillance et cree l'alerte avec le
    commentaire fourni."""
    agent_id = creer_agent(app)
    organisateur_id = creer_organisateur(app)
    connecter(client, "agent_i15@bbda.bf")

    client.post(f"/agent/surveillance/{organisateur_id}/marquer", data={"commentaire": "Organisateur introuvable"})

    with app.app_context():
        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte == "surveillance"
        alerte = AlerteSurveillance.query.filter_by(organisateur_id=organisateur_id).first()
        assert alerte is not None
        assert alerte.commentaire == "Organisateur introuvable"
        assert alerte.marque_par == agent_id


def test_page_surveillance_liste_comptes_surveilles(app, client):
    """GET /agent/surveillance liste les comptes actuellement sous
    surveillance en plus des alertes non traitees."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, email="surveille_i15@example.com", statut_compte="surveillance")
    with app.app_context():
        db.session.add(AlerteSurveillance(organisateur_id=organisateur_id, commentaire="Test"))
        db.session.commit()
    connecter(client, "agent_i15@bbda.bf")

    reponse = client.get("/agent/surveillance")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "Boubacar" in page
    assert "Test" in page


def test_lever_surveillance_reactive_le_compte(app, client):
    """POST /agent/surveillance/<id>/lever reactive le compte et solde les
    alertes non traitees (RM-084)."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, statut_compte="surveillance")
    with app.app_context():
        db.session.add(AlerteSurveillance(organisateur_id=organisateur_id))
        db.session.commit()
    connecter(client, "agent_i15@bbda.bf")

    client.post(f"/agent/surveillance/{organisateur_id}/lever")

    with app.app_context():
        assert Organisateur.query.get(organisateur_id).statut_compte == "actif"
        assert AlerteSurveillance.query.filter_by(organisateur_id=organisateur_id, traitee=False).count() == 0


def test_organisateur_ne_peut_pas_gerer_les_arrieres(app, client):
    """RM-003 : un organisateur ne peut pas acceder aux routes de gestion
    des arrieres/surveillance reservees a l'agent."""
    organisateur_id = creer_organisateur(app, email="simple@example.com")
    connecter(client, "simple@example.com")

    assert client.get("/agent/arrieres").status_code in (302, 403)
    assert client.post(f"/agent/arrieres/{organisateur_id}/debloquer").status_code in (302, 403)
