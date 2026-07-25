"""Tests du blueprint d'authentification (Prompt 4) : inscription, connexion,
deconnexion, controle d'acces par role (RM-001 a RM-005)."""

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Organisateur, Utilisateur


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


def creer_utilisateur(app, role, email, mot_de_passe="password123", statut="actif", statut_compte="actif"):
    """Insere directement un utilisateur (et son profil organisateur si besoin)
    en base, sans passer par le formulaire d'inscription."""
    with app.app_context():
        hachage = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(
            nom="Test", prenom="Utilisateur", email=email, mot_de_passe=hachage, role=role, statut=statut
        )
        db.session.add(utilisateur)
        db.session.flush()
        if role == "organisateur":
            db.session.add(
                Organisateur(
                    utilisateur_id=utilisateur.id,
                    qualite="Organisateur",
                    telephone="70000000",
                    statut_compte=statut_compte,
                )
            )
        db.session.commit()
        return utilisateur.id


DONNEES_INSCRIPTION_VALIDES = {
    "nom": "Ouedraogo",
    "prenom": "Boubacar",
    "qualite": "Organisateur",
    "telephone": "70000001",
    "email": "nouveau@example.com",
    "password": "password123",
    "confirm": "password123",
    "cgu": "1",
}


def test_inscription_succes(app, client):
    """Un formulaire d'inscription valide cree un compte organisateur et
    redirige vers la connexion, sans jamais stocker le mot de passe en clair."""
    reponse = client.post("/auth/inscription", data=DONNEES_INSCRIPTION_VALIDES, follow_redirects=False)

    assert reponse.status_code == 302
    assert reponse.headers["Location"].endswith("/auth/connexion")

    with app.app_context():
        utilisateur = Utilisateur.query.filter_by(email="nouveau@example.com").first()
        assert utilisateur is not None
        assert utilisateur.role == "organisateur"
        assert utilisateur.mot_de_passe != "password123"
        assert utilisateur.organisateur is not None
        assert utilisateur.organisateur.telephone == "70000001"


def test_inscription_email_deja_utilise(app, client):
    """Une deuxieme inscription avec le meme email est refusee (pas de doublon)."""
    client.post("/auth/inscription", data=DONNEES_INSCRIPTION_VALIDES)

    reponse = client.post("/auth/inscription", data=DONNEES_INSCRIPTION_VALIDES)

    assert reponse.status_code == 400
    with app.app_context():
        assert Utilisateur.query.filter_by(email="nouveau@example.com").count() == 1


def test_inscription_champ_manquant(client):
    """Un champ obligatoire manquant est rejete (RM-011 : tous les champs
    obligatoires doivent etre remplis)."""
    donnees = dict(DONNEES_INSCRIPTION_VALIDES)
    donnees.pop("telephone")

    reponse = client.post("/auth/inscription", data=donnees)

    assert reponse.status_code == 400


def test_inscription_mots_de_passe_differents(client):
    """Une confirmation de mot de passe differente est rejetee."""
    donnees = dict(DONNEES_INSCRIPTION_VALIDES)
    donnees["confirm"] = "autrechose123"

    reponse = client.post("/auth/inscription", data=donnees)

    assert reponse.status_code == 400


def test_connexion_succes_redirige_selon_role(app, client):
    """Un organisateur qui se connecte est redirige vers son tableau de bord."""
    creer_utilisateur(app, "organisateur", "orga@example.com")

    reponse = client.post(
        "/auth/connexion", data={"email": "orga@example.com", "password": "password123"}, follow_redirects=False
    )

    assert reponse.status_code == 302
    assert reponse.headers["Location"].endswith("/declarations/")

    suite = client.get("/declarations/")
    assert suite.status_code == 200


def test_connexion_mot_de_passe_incorrect(app, client):
    """Un mauvais mot de passe est refuse."""
    creer_utilisateur(app, "organisateur", "orga2@example.com")

    reponse = client.post("/auth/connexion", data={"email": "orga2@example.com", "password": "mauvais"})

    assert reponse.status_code == 401


def test_connexion_compte_inactif_refusee(app, client):
    """Un compte desactive par l'administration ne peut pas se connecter."""
    creer_utilisateur(app, "organisateur", "inactif@example.com", statut="inactif")

    reponse = client.post("/auth/connexion", data={"email": "inactif@example.com", "password": "password123"})

    assert reponse.status_code == 403


def test_deconnexion_puis_acces_refuse(app, client):
    """Apres deconnexion, l'espace organisateur redemande une connexion."""
    creer_utilisateur(app, "organisateur", "orga3@example.com")
    client.post("/auth/connexion", data={"email": "orga3@example.com", "password": "password123"})

    client.get("/auth/deconnexion")
    reponse = client.get("/declarations/", follow_redirects=False)

    assert reponse.status_code == 302
    assert "/auth/connexion" in reponse.headers["Location"]


def test_organisateur_peut_supprimer_son_compte(app, client):
    """Un organisateur desactive son compte puis ne peut plus se reconnecter."""
    creer_utilisateur(app, "organisateur", "orga-del@example.com")
    client.post("/auth/connexion", data={"email": "orga-del@example.com", "password": "password123"})

    reponse = client.post(
        "/auth/supprimer-compte",
        data={"confirmation": "SUPPRIMER"},
        follow_redirects=False,
    )
    assert reponse.status_code == 302

    with app.app_context():
        utilisateur = Utilisateur.query.filter_by(email="orga-del@example.com").first()
        assert utilisateur.statut == "inactif"

    reponse = client.post(
        "/auth/connexion",
        data={"email": "orga-del@example.com", "password": "password123"},
    )
    assert reponse.status_code == 403


def test_organisateur_ne_peut_pas_acceder_espace_agent(app, client):
    """RM-005 : un organisateur ne peut pas acceder aux routes /agent/ ou /admin/."""
    creer_utilisateur(app, "organisateur", "orga4@example.com")
    client.post("/auth/connexion", data={"email": "orga4@example.com", "password": "password123"})

    reponse = client.get("/agent/")

    assert reponse.status_code == 403


def test_agent_peut_acceder_espace_agent(app, client):
    """RM-003 : l'espace agent est accessible aux agents (et aux administrateurs)."""
    creer_utilisateur(app, "agent", "agent@example.com")
    client.post("/auth/connexion", data={"email": "agent@example.com", "password": "password123"})

    reponse = client.get("/agent/")

    assert reponse.status_code == 200
