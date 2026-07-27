"""Tests de la face publique : accueil, evenements, support,
contact et pages legales accessibles sans connexion (RM-090 a RM-093)."""

from datetime import datetime, timedelta

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Declaration, MessageContact, Notification, Organisateur, Utilisateur


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


def creer_evenement_public(app, promouvoir=True, statut="quittance_delivree", nom="Concert public"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(
            nom="Zongo", prenom="Aminata", email="orga_public@example.com", mot_de_passe=hachage, role="organisateur"
        )
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000002")
        db.session.add(organisateur)
        db.session.flush()
        declaration = Declaration(
            organisateur_id=organisateur.id,
            nom_demandeur="Zongo",
            prenom_demandeur="Aminata",
            qualite_demandeur="Organisateur",
            telephone="70000002",
            email="orga_public@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement=nom,
            nom_salle="Maison du Peuple",
            adresse="Avenue de la Nation",
            ville="Ouagadougou",
            date_evenement=datetime.utcnow() + timedelta(days=20),
            duree_heures=3,
            capacite_accueil=500,
            nature_diffusion="Musique vivante",
            promouvoir=promouvoir,
            statut=statut,
        )
        db.session.add(declaration)
        db.session.commit()
        return declaration.id


def test_accueil_accessible_sans_connexion(app, client):
    reponse = client.get("/")
    page = reponse.get_data(as_text=True)
    assert reponse.status_code == 200
    assert "BBDA Events" in page
    assert "Événements à venir" in page
    assert "Comment déclarer" in page


def test_accueil_affiche_evenements_publics(app, client):
    creer_evenement_public(app, nom="Concert Accueil")
    reponse = client.get("/")
    page = reponse.get_data(as_text=True)
    assert reponse.status_code == 200
    assert "Concert Accueil" in page
    assert "Voir tous les événements" in page


def test_evenements_sans_evenement_affiche_message_vide(app, client):
    reponse = client.get("/evenements")
    page = reponse.get_data(as_text=True)
    assert reponse.status_code == 200
    assert "Aucun événement à venir" in page


def test_evenement_promu_et_quittance_apparait_dans_le_listing(app, client):
    creer_evenement_public(app, nom="Festival Roog")
    reponse = client.get("/evenements")
    page = reponse.get_data(as_text=True)
    assert "Festival Roog" in page
    assert "Ouagadougou" in page


def test_evenement_non_public_n_apparait_pas(app, client):
    creer_evenement_public(app, promouvoir=False, statut="quittance_delivree", nom="Prive")
    reponse = client.get("/evenements")
    assert "Prive" not in reponse.get_data(as_text=True)


def test_evenement_sans_quittance_n_apparait_pas(app, client):
    creer_evenement_public(app, promouvoir=True, statut="nouvelle", nom="Pas encore paye")
    reponse = client.get("/evenements")
    assert "Pas encore paye" not in reponse.get_data(as_text=True)


def test_pages_support_et_legales_accessibles(app, client):
    for chemin in (
        "/support",
        "/contact",
        "/legal/confidentialite",
        "/legal/cgu",
        "/legal/politique-organisateur",
        "/legal/politique-public",
    ):
        assert client.get(chemin).status_code == 200


def test_formulaire_contact_enregistre_en_base(app, client):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        db.session.add(
            Utilisateur(nom="Admin", prenom="BBDA", email="admin_contact@bbda.bf", mot_de_passe=hachage, role="admin")
        )
        db.session.commit()

    reponse = client.post(
        "/contact",
        data={
            "nom": "Sawadogo Issa",
            "email": "issa@example.com",
            "sujet": "Question redevance",
            "message": "Bonjour, quel est le delai de traitement ?",
        },
        follow_redirects=False,
    )
    assert reponse.status_code == 302
    with app.app_context():
        message = MessageContact.query.first()
        assert message is not None
        assert message.sujet == "Question redevance"
        assert message.email == "issa@example.com"
        assert Notification.query.filter_by(type_notification="message_contact").count() == 1


def test_formulaire_contact_champs_manquants_rejete(app, client):
    reponse = client.post("/contact", data={"nom": "", "email": "", "sujet": "", "message": ""})
    assert reponse.status_code == 400
    with app.app_context():
        assert MessageContact.query.count() == 0


def test_detail_evenement_public_accessible(app, client):
    """RM-090 : un evenement promu avec quittance a une page de detail."""
    declaration_id = creer_evenement_public(app, nom="Concert detail")
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        declaration.description_publique = "Soiree live a Ouagadougou."
        declaration.contact_public = True
        db.session.commit()

    reponse = client.get(f"/evenements/{declaration_id}")
    page = reponse.get_data(as_text=True)
    assert reponse.status_code == 200
    assert "Concert detail" in page
    assert "Soiree live a Ouagadougou." in page
    assert "Événement autorisé par le BBDA" not in page
    assert "Quittance N°" not in page
    assert "70000002" in page


def test_detail_evenement_non_public_renvoie_404(app, client):
    """RM-090 : un evenement non public renvoie 404 (pas de fuite d'existence)."""
    declaration_id = creer_evenement_public(app, promouvoir=False, nom="Secret")
    assert client.get(f"/evenements/{declaration_id}").status_code == 404


def test_detail_evenement_sans_quittance_renvoie_404(app, client):
    declaration_id = creer_evenement_public(app, statut="nouvelle", nom="En attente")
    assert client.get(f"/evenements/{declaration_id}").status_code == 404


def test_page_billetterie_bientot_accessible(app, client):
    reponse = client.get("/billetterie-bientot")
    page = reponse.get_data(as_text=True)
    assert reponse.status_code == 200
    assert "bientôt disponible" in page.lower() or "Bientôt" in page
