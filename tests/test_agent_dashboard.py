"""Tests du tableau de bord agent : declarations urgentes et en
cours, statistiques, alertes de surveillance et d'arrieres (RM-003, RM-004,
RM-073, RM-080 a RM-084)."""

from datetime import datetime

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import AlerteSurveillance, Declaration, Organisateur, Utilisateur


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


def creer_agent(app, email="agent@bbda.bf"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        agent = Utilisateur(nom="Kabore", prenom="Issa", email=email, mot_de_passe=hachage, role="agent")
        db.session.add(agent)
        db.session.commit()
        return agent.id


def creer_organisateur(app, email, statut_compte="actif"):
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


def creer_declaration(app, organisateur_id, statut):
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


def test_tableau_de_bord_agent_liste_bien_les_declarations(app, client):
    """Les declarations 'nouvelle' et 'en cours' apparaissent dans les bonnes
    sections, tous organisateurs confondus."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga@example.com")
    creer_declaration(app, organisateur_id, "nouvelle")
    creer_declaration(app, organisateur_id, "en_evaluation")
    creer_declaration(app, organisateur_id, "quittance_delivree")
    connecter(client, "agent@bbda.bf")

    reponse = client.get("/agent/")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert ">1<" in page  # une seule carte doit valoir 1 pour "nouvelles"


def test_alerte_surveillance_affichee_si_non_traitee(app, client):
    """RM-080 a RM-084 : une alerte non traitee declenche le bandeau et
    apparait dans /agent/surveillance."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga2@example.com")
    with app.app_context():
        db.session.add(AlerteSurveillance(organisateur_id=organisateur_id))
        db.session.commit()
    connecter(client, "agent@bbda.bf")

    tableau = client.get("/agent/")
    assert "compte(s) sous surveillance reconnecté(s)" in tableau.get_data(as_text=True)

    page_surveillance = client.get("/agent/surveillance")
    assert "Ouedraogo" in page_surveillance.get_data(as_text=True)


def test_traiter_alerte_la_retire_de_la_liste(app, client):
    """Marquer une alerte comme traitee la fait disparaitre de la liste."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga3@example.com")
    with app.app_context():
        alerte = AlerteSurveillance(organisateur_id=organisateur_id)
        db.session.add(alerte)
        db.session.commit()
        alerte_id = alerte.id
    connecter(client, "agent@bbda.bf")

    reponse = client.post(f"/agent/surveillance/{alerte_id}/traiter", follow_redirects=True)

    assert "Aucune alerte de surveillance en attente." in reponse.get_data(as_text=True)
    with app.app_context():
        assert AlerteSurveillance.query.get(alerte_id).traitee is True


def test_organisateur_en_arriere_affiche_dans_liste_agent(app, client):
    """RM-073 : un organisateur dont le compte n'est pas 'actif' apparait
    dans /agent/arrieres et declenche l'alerte du tableau de bord."""
    creer_agent(app)
    creer_organisateur(app, "orga4@example.com", statut_compte="bloque")
    connecter(client, "agent@bbda.bf")

    tableau = client.get("/agent/")
    assert "organisateur(s) avec arriéré non réglé" in tableau.get_data(as_text=True)

    page_arrieres = client.get("/agent/arrieres")
    assert "bloque" in page_arrieres.get_data(as_text=True)


def test_filtre_declarations_par_statut(app, client):
    """Le lien de la carte 'Nouvelles declarations' filtre correctement."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga5@example.com")
    creer_declaration(app, organisateur_id, "nouvelle")
    creer_declaration(app, organisateur_id, "payee")
    connecter(client, "agent@bbda.bf")

    reponse = client.get("/agent/declarations?statut=nouvelle")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "badge--nouvelle" in page
    assert "badge--payee" not in page


def test_organisateur_ne_peut_pas_acceder_espace_agent_dashboard(app, client):
    """RM-005 : un organisateur ne peut pas consulter le tableau de bord agent."""
    creer_organisateur(app, "orga6@example.com")
    connecter(client, "orga6@example.com")

    reponse = client.get("/agent/")

    assert reponse.status_code == 403
