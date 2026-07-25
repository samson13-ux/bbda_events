"""Tests fonctionnels consolides (Prompt 20) : parcours critiques pour la
soutenance — face publique, authentification, declarations, paiement,
promotion, securite par role et arrieres.
"""

from datetime import datetime, timedelta
from io import BytesIO

import bcrypt
import pytest

from app import create_app
from backend.arrieres.moteur import creer_arriere, debloquer_compte
from extensions import db
from models import (
    Declaration,
    EvaluationAgent,
    MessageContact,
    Organisateur,
    ParametresSysteme,
    Quittance,
    Utilisateur,
)


@pytest.fixture
def app():
    """Cree une instance d'application en configuration de test."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        db.session.add(
            ParametresSysteme(cle="SEUIL_ARRIERE", valeur="1000", description="Seuil")
        )
        db.session.add(
            ParametresSysteme(cle="DELAI_NOTIFICATION", valeur="7", description="Delai")
        )
        db.session.commit()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    """Client de test Flask pour effectuer des requetes HTTP simulees."""
    return app.test_client()


def _hacher(mot_de_passe="password123"):
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def creer_utilisateur(app, role, email, statut_compte="actif"):
    """Insere un utilisateur (et un profil organisateur si besoin)."""
    with app.app_context():
        utilisateur = Utilisateur(
            nom="Test", prenom="User", email=email, mot_de_passe=_hacher(), role=role
        )
        db.session.add(utilisateur)
        db.session.flush()
        organisateur_id = None
        if role == "organisateur":
            organisateur = Organisateur(
                utilisateur_id=utilisateur.id,
                qualite="Organisateur",
                telephone="70000000",
                statut_compte=statut_compte,
            )
            db.session.add(organisateur)
            db.session.flush()
            organisateur_id = organisateur.id
        db.session.commit()
        return utilisateur.id, organisateur_id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def date_future():
    return (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%dT%H:%M")


DONNEES_DECLARATION = {
    "nom_demandeur": "Ouedraogo",
    "prenom_demandeur": "Boubacar",
    "qualite": "Organisateur",
    "telephone": "70000001",
    "email": "orga@example.com",
    "nature_manifestation": "Concert",
    "nom_artiste_evenement": "Concert Test",
    "nom_salle": "Salle des fetes",
    "adresse": "Avenue de la Nation",
    "ville": "Ouagadougou",
    "duree_heures": "3",
    "capacite_accueil": "500",
    "entree": "payante",
    "nature_diffusion": "vivante",
}


# --- Face publique -----------------------------------------------------------


def test_accueil_accessible_sans_connexion(client):
    assert client.get("/").status_code == 200


def test_evenements_sans_donnees_affiche_message_vide(client):
    page = client.get("/evenements").get_data(as_text=True)
    assert "Aucun événement à venir" in page


def test_detail_evenement_non_public_renvoie_404(app, client):
    _, organisateur_id = creer_utilisateur(app, "organisateur", "orga_prive@example.com")
    with app.app_context():
        declaration = Declaration(
            organisateur_id=organisateur_id,
            nom_demandeur="X",
            prenom_demandeur="Y",
            qualite_demandeur="Organisateur",
            telephone="70000000",
            email="orga_prive@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Secret",
            nom_salle="Salle",
            adresse="Adr",
            ville="Ouaga",
            date_evenement=datetime.utcnow() + timedelta(days=10),
            duree_heures=2,
            capacite_accueil=100,
            nature_diffusion="Musique vivante",
            promouvoir=False,
            statut="quittance_delivree",
        )
        db.session.add(declaration)
        db.session.commit()
        declaration_id = declaration.id
    assert client.get(f"/evenements/{declaration_id}").status_code == 404


def test_contact_enregistre_message(app, client):
    reponse = client.post(
        "/contact",
        data={
            "nom": "Sawadogo",
            "email": "contact@example.com",
            "sujet": "Aide",
            "message": "Comment declarer ?",
        },
        follow_redirects=False,
    )
    assert reponse.status_code == 302
    with app.app_context():
        assert MessageContact.query.filter_by(email="contact@example.com").count() == 1


# --- Authentification --------------------------------------------------------


def test_inscription_valide(app, client):
    reponse = client.post(
        "/auth/inscription",
        data={
            "nom": "Kabore",
            "prenom": "Issa",
            "qualite": "Organisateur",
            "telephone": "70000011",
            "email": "nouveau@example.com",
            "password": "password123",
            "confirm": "password123",
            "cgu": "1",
        },
        follow_redirects=False,
    )
    assert reponse.status_code == 302
    with app.app_context():
        assert Utilisateur.query.filter_by(email="nouveau@example.com").count() == 1


def test_inscription_email_existant_refusee(app, client):
    creer_utilisateur(app, "organisateur", "deja@example.com")
    reponse = client.post(
        "/auth/inscription",
        data={
            "nom": "X",
            "prenom": "Y",
            "qualite": "Organisateur",
            "telephone": "70000012",
            "email": "deja@example.com",
            "password": "password123",
            "confirm": "password123",
            "cgu": "1",
        },
    )
    assert reponse.status_code == 400


def test_connexion_valide_redirige_organisateur(app, client):
    creer_utilisateur(app, "organisateur", "orga_ok@example.com")
    reponse = connecter(client, "orga_ok@example.com")
    assert reponse.status_code == 302
    assert "/declarations" in reponse.headers["Location"]


def test_route_protegee_sans_connexion_redirige(client):
    reponse = client.get("/declarations/", follow_redirects=False)
    assert reponse.status_code == 302
    assert "/auth/connexion" in reponse.headers["Location"]


# --- Declarations et parcours metier ----------------------------------------


def test_soumission_declaration_valide(app, client):
    creer_utilisateur(app, "organisateur", "orga@example.com")
    connecter(client, "orga@example.com")
    donnees = dict(DONNEES_DECLARATION, date_evenement=date_future())
    reponse = client.post("/declarations/nouvelle", data=donnees, follow_redirects=False)
    assert reponse.status_code == 302
    with app.app_context():
        declaration = Declaration.query.first()
        assert declaration is not None
        assert declaration.statut == "nouvelle"


def test_soumission_compte_bloque_refusee(app, client):
    creer_utilisateur(app, "organisateur", "bloque@example.com", statut_compte="bloque")
    connecter(client, "bloque@example.com")
    donnees = dict(DONNEES_DECLARATION, date_evenement=date_future())
    donnees["email"] = "bloque@example.com"
    reponse = client.post("/declarations/nouvelle", data=donnees, follow_redirects=False)
    assert reponse.status_code == 302
    with app.app_context():
        assert Declaration.query.count() == 0


def test_declaration_avec_promotion(app, client):
    creer_utilisateur(app, "organisateur", "orga@example.com")
    connecter(client, "orga@example.com")
    donnees = dict(DONNEES_DECLARATION, date_evenement=date_future())
    donnees["promouvoir"] = "on"
    donnees["description_publique"] = "Concert en plein air"
    donnees["contact_public"] = "on"
    donnees["affiche"] = (BytesIO(b"\xff\xd8\xff\xe0fake"), "affiche.jpg")
    client.post("/declarations/nouvelle", data=donnees, content_type="multipart/form-data")
    with app.app_context():
        declaration = Declaration.query.first()
        assert declaration.promouvoir is True
        assert declaration.description_publique == "Concert en plein air"
        assert declaration.affiche_path is not None


def test_parcours_montant_puis_paiement_et_publication(app, client):
    """Saisie montant agent → paiement → quittance → visible publiquement."""
    creer_utilisateur(app, "agent", "agent@bbda.bf")
    _, organisateur_id = creer_utilisateur(app, "organisateur", "orga@example.com")
    with app.app_context():
        agent = Utilisateur.query.filter_by(email="agent@bbda.bf").first()
        declaration = Declaration(
            organisateur_id=organisateur_id,
            nom_demandeur="Ouedraogo",
            prenom_demandeur="Boubacar",
            qualite_demandeur="Organisateur",
            telephone="70000001",
            email="orga@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Concert Public",
            nom_salle="Maison du Peuple",
            adresse="Avenue",
            ville="Ouagadougou",
            date_evenement=datetime.utcnow() + timedelta(days=20),
            duree_heures=3,
            capacite_accueil=400,
            nature_diffusion="Musique vivante",
            promouvoir=True,
            description_publique="Soiree live",
            statut="nouvelle",
        )
        db.session.add(declaration)
        db.session.commit()
        declaration_id = declaration.id
        agent_id = agent.id

    connecter(client, "agent@bbda.bf")
    client.post(
        f"/agent/declarations/{declaration_id}/fixer-montant",
        data={"tarif": "5000", "redevance": "15000", "commentaire": "OK"},
    )
    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "montant_fixe"
        assert EvaluationAgent.query.filter_by(declaration_id=declaration_id).count() == 1

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "20000",
            "montant_lettres": "Vingt mille francs CFA",
            "type_paiement": "integral",
        },
    )
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.statut == "quittance_delivree"
        assert Quittance.query.filter_by(declaration_id=declaration_id).count() == 1
        assert declaration.promouvoir is True

    page = client.get("/evenements").get_data(as_text=True)
    assert "Concert Public" in page
    assert client.get(f"/evenements/{declaration_id}").status_code == 200
    assert agent_id  # utilise pour eviter un warning flake si jamais


# --- Securite ----------------------------------------------------------------


def test_organisateur_ne_voit_pas_declaration_autrui(app, client):
    _, orga_a = creer_utilisateur(app, "organisateur", "a@example.com")
    creer_utilisateur(app, "organisateur", "b@example.com")
    with app.app_context():
        declaration = Declaration(
            organisateur_id=orga_a,
            nom_demandeur="A",
            prenom_demandeur="A",
            qualite_demandeur="Organisateur",
            telephone="70000001",
            email="a@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Prive A",
            nom_salle="Salle",
            adresse="Adr",
            ville="Ouaga",
            date_evenement=datetime.utcnow() + timedelta(days=10),
            duree_heures=2,
            capacite_accueil=50,
            nature_diffusion="Musique vivante",
            statut="nouvelle",
        )
        db.session.add(declaration)
        db.session.commit()
        declaration_id = declaration.id
    connecter(client, "b@example.com")
    assert client.get(f"/declarations/{declaration_id}").status_code == 404


def test_organisateur_interdit_espace_agent(app, client):
    creer_utilisateur(app, "organisateur", "orga@example.com")
    connecter(client, "orga@example.com")
    assert client.get("/agent/").status_code == 403


def test_agent_interdit_espace_admin(app, client):
    creer_utilisateur(app, "agent", "agent@bbda.bf")
    connecter(client, "agent@bbda.bf")
    assert client.get("/admin/").status_code == 403


# --- Arrieres ----------------------------------------------------------------


def test_arriere_au_dela_du_seuil_bloque_le_compte(app):
    _, organisateur_id = creer_utilisateur(app, "organisateur", "orga_arr@example.com")
    with app.app_context():
        agent = Utilisateur(nom="A", prenom="G", email="ag@bbda.bf", mot_de_passe=_hacher(), role="agent")
        db.session.add(agent)
        db.session.flush()
        declaration = Declaration(
            organisateur_id=organisateur_id,
            nom_demandeur="O",
            prenom_demandeur="B",
            qualite_demandeur="Organisateur",
            telephone="70000000",
            email="orga_arr@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="X",
            nom_salle="S",
            adresse="A",
            ville="Ouaga",
            date_evenement=datetime.utcnow() + timedelta(days=5),
            duree_heures=2,
            capacite_accueil=10,
            nature_diffusion="Musique vivante",
            statut="montant_fixe",
        )
        db.session.add(declaration)
        db.session.flush()
        db.session.add(
            EvaluationAgent(declaration_id=declaration.id, agent_id=agent.id, tarif=1000, redevance=4000)
        )
        db.session.commit()
        creer_arriere(declaration.id, 1500)
        db.session.commit()
        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte in ("arriere", "bloque")


def test_deblocage_remet_compte_actif(app):
    _, organisateur_id = creer_utilisateur(app, "organisateur", "orga_deb@example.com", statut_compte="bloque")
    with app.app_context():
        debloquer_compte(organisateur_id)
        db.session.commit()
        assert Organisateur.query.get(organisateur_id).statut_compte == "actif"
