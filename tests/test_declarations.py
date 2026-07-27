"""Tests du tableau de bord organisateur : statistiques, blocage
de compte en arriere, controle de propriete sur le detail d'une declaration
(RM-002, RM-004, RM-073)."""

import re
from datetime import datetime

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Declaration, Organisateur, Utilisateur


@pytest.fixture
def app():
    """Cree une instance d'application en configuration de test."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    """Client de test Flask pour effectuer des requetes HTTP simulees."""
    return app.test_client()


def creer_organisateur(app, email, statut_compte="actif", mot_de_passe="password123"):
    """Insere un compte organisateur directement en base et retourne son id."""
    with app.app_context():
        hachage = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Test", prenom="Orga", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000", statut_compte=statut_compte
        )
        db.session.add(organisateur)
        db.session.commit()
        return organisateur.id


def creer_declaration(app, organisateur_id, statut):
    """Insere une declaration minimale rattachee a un organisateur, avec le
    statut donne."""
    with app.app_context():
        declaration = Declaration(
            organisateur_id=organisateur_id,
            nom_demandeur="Test",
            prenom_demandeur="Orga",
            qualite_demandeur="Organisateur",
            telephone="70000000",
            email="orga@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Artiste Test",
            nom_salle="Salle Test",
            adresse="Adresse Test",
            ville="Ouagadougou",
            date_evenement=datetime(2026, 8, 1, 20, 0),
            duree_heures=3,
            capacite_accueil=100,
            nature_diffusion="Musique vivante",
            statut=statut,
        )
        db.session.add(declaration)
        db.session.commit()
        return declaration.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_statistiques_tableau_de_bord(app, client):
    """RM-004 : total, nouvelles, en cours et quittances sont bien comptes."""
    organisateur_id = creer_organisateur(app, "orga_stats@example.com")
    creer_declaration(app, organisateur_id, "nouvelle")
    creer_declaration(app, organisateur_id, "en_evaluation")
    creer_declaration(app, organisateur_id, "quittance_delivree")
    connecter(client, "orga_stats@example.com")

    reponse = client.get("/declarations/")

    assert reponse.status_code == 200
    page = reponse.get_data(as_text=True)
    valeurs = re.findall(r'carte-stat__valeur">(\d+)<', page)
    assert valeurs == ["3", "1", "2", "1"]  # total, nouvelles, en_cours, quittances


def test_compte_bloque_affiche_banniere_et_bloque_creation(app, client):
    """RM-073 : un compte en arriere/bloque voit la banniere de blocage et est
    redirige vers son tableau de bord s'il tente d'ouvrir le formulaire de
    nouvelle declaration (RM-010)."""
    organisateur_id = creer_organisateur(app, "orga_bloque@example.com", statut_compte="bloque")
    creer_declaration(app, organisateur_id, "en_attente")
    connecter(client, "orga_bloque@example.com")

    tableau = client.get("/declarations/")
    assert tableau.status_code == 200
    assert "Votre compte est bloqué" in tableau.get_data(as_text=True)

    formulaire = client.get("/declarations/nouvelle", follow_redirects=False)
    assert formulaire.status_code == 302
    assert formulaire.headers["Location"].endswith("/declarations/")


def test_compte_actif_peut_ouvrir_le_formulaire(app, client):
    """Un compte actif peut acceder au formulaire de nouvelle declaration."""
    creer_organisateur(app, "orga_actif@example.com")
    connecter(client, "orga_actif@example.com")

    reponse = client.get("/declarations/nouvelle")

    assert reponse.status_code == 200


def test_organisateur_ne_peut_pas_voir_declaration_dautrui(app, client):
    """Controle de propriete : une declaration qui n'appartient pas a
    l'organisateur connecte renvoie 404 (et non 403, pour ne pas confirmer
    son existence)."""
    autre_organisateur_id = creer_organisateur(app, "autre@example.com")
    declaration_id = creer_declaration(app, autre_organisateur_id, "nouvelle")
    creer_organisateur(app, "orga_test@example.com")
    connecter(client, "orga_test@example.com")

    reponse = client.get(f"/declarations/{declaration_id}")

    assert reponse.status_code == 404


def test_aucune_declaration_affiche_message_vide(app, client):
    """Un organisateur sans declaration voit le message d'etat vide."""
    creer_organisateur(app, "orga_vide@example.com")
    connecter(client, "orga_vide@example.com")

    reponse = client.get("/declarations/")

    assert "Aucune déclaration pour l'instant." in reponse.get_data(as_text=True)


def test_organisateur_peut_modifier_declaration_nouvelle(app, client):
    """RM-015 : une declaration `nouvelle` est editable par son proprietaire."""
    from datetime import timedelta

    organisateur_id = creer_organisateur(app, "orga_edit@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "nouvelle")
    connecter(client, "orga_edit@example.com")

    date_future = (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%dT%H:%M")
    reponse = client.post(
        f"/declarations/{declaration_id}/modifier",
        data={
            "nom_demandeur": "Test",
            "prenom_demandeur": "Orga",
            "qualite": "Organisateur",
            "telephone": "70000000",
            "email": "orga_edit@example.com",
            "nature_manifestation": "Festival",
            "nom_artiste_evenement": "Nom Modifie",
            "nom_salle": "Salle Test",
            "adresse": "Adresse Test",
            "ville": "Bobo-Dioulasso",
            "date_evenement": date_future,
            "duree_heures": "3",
            "capacite_accueil": "100",
            "entree": "gratuite",
            "nature_diffusion": ["vivante"],
        },
        follow_redirects=False,
    )
    assert reponse.status_code == 302

    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.nom_artiste_evenement == "Nom Modifie"
        assert declaration.ville == "Bobo-Dioulasso"
        assert declaration.statut == "nouvelle"


def test_organisateur_ne_peut_pas_modifier_apres_prise_en_charge(app, client):
    """RM-015 : statut autre que `nouvelle` refuse la modification."""
    organisateur_id = creer_organisateur(app, "orga_edit2@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "en_evaluation")
    connecter(client, "orga_edit2@example.com")

    reponse = client.get(f"/declarations/{declaration_id}/modifier", follow_redirects=False)
    assert reponse.status_code == 302
    assert f"/declarations/{declaration_id}" in reponse.headers["Location"]
