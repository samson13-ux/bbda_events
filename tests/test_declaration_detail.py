"""Tests de la page de detail d'une declaration cote organisateur :
frise chronologique, encadre du montant a payer, bouton de telechargement de
la quittance, liste des artistes (RM-030 a RM-054)."""

from datetime import datetime

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Declaration, EvaluationAgent, ListeArtiste, Organisateur, Paiement, Quittance, Utilisateur


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


def creer_organisateur(app, email, mot_de_passe="password123"):
    """Insere un compte organisateur directement en base et retourne son id."""
    with app.app_context():
        hachage = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Test", prenom="Orga", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000")
        db.session.add(organisateur)
        db.session.commit()
        return organisateur.id


def creer_declaration(app, organisateur_id, statut, agent_id=None, promouvoir=False):
    """Insere une declaration minimale, avec un artiste lie, et retourne son id."""
    with app.app_context():
        declaration = Declaration(
            organisateur_id=organisateur_id,
            nom_demandeur="Test",
            prenom_demandeur="Orga",
            qualite_demandeur="Organisateur",
            telephone="70000000",
            email="orga@example.com",
            nature_manifestation="Festival",
            nom_artiste_evenement="Festival Test",
            nom_salle="Salle Test",
            adresse="Adresse Test",
            ville="Ouagadougou",
            date_evenement=datetime(2026, 8, 1, 20, 0),
            duree_heures=3,
            capacite_accueil=100,
            nature_diffusion="Musique vivante",
            promouvoir=promouvoir,
            statut=statut,
        )
        db.session.add(declaration)
        db.session.flush()
        db.session.add(ListeArtiste(declaration_id=declaration.id, nom_artiste="Floby", discipline="Musique"))
        db.session.commit()
        return declaration.id


def creer_agent(app, email="agent@bbda.bf"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        agent = Utilisateur(nom="Kabore", prenom="Issa", email=email, mot_de_passe=hachage, role="agent")
        db.session.add(agent)
        db.session.commit()
        return agent.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_declaration_nouvelle_seule_premiere_etape_franchie(app, client):
    """Une declaration au statut 'nouvelle' n'a que la 1ere etape de la
    frise en vert."""
    organisateur_id = creer_organisateur(app, "orga1@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "nouvelle")
    connecter(client, "orga1@example.com")

    reponse = client.get(f"/declarations/{declaration_id}")

    assert reponse.status_code == 200
    page = reponse.get_data(as_text=True)
    assert page.count("frise-etape--franchie") == 1
    assert "Floby" in page  # la liste des artistes est affichee (Festival)


def test_montant_fixe_affiche_encadre_et_frise(app, client):
    """RM-030 a RM-033 : une fois le montant fixe, l'encadre de paiement
    apparait et la frise montre 3 etapes franchies."""
    organisateur_id = creer_organisateur(app, "orga2@example.com")
    agent_id = creer_agent(app)
    declaration_id = creer_declaration(app, organisateur_id, "montant_fixe")
    with app.app_context():
        db.session.add(EvaluationAgent(declaration_id=declaration_id, agent_id=agent_id, tarif=15000, redevance=10000))
        db.session.commit()
    connecter(client, "orga2@example.com")

    reponse = client.get(f"/declarations/{declaration_id}")
    page = reponse.get_data(as_text=True)

    assert "Montant à payer" in page
    assert "25000 FCFA au total" in page
    assert page.count("frise-etape--franchie") == 3


def test_quittance_delivree_affiche_bouton_telechargement(app, client):
    """RM-050 : le bouton de telechargement n'apparait que si la quittance
    existe, et les 5 etapes de la frise sont franchies."""
    organisateur_id = creer_organisateur(app, "orga3@example.com")
    agent_id = creer_agent(app)
    declaration_id = creer_declaration(app, organisateur_id, "quittance_delivree")
    with app.app_context():
        db.session.add(EvaluationAgent(declaration_id=declaration_id, agent_id=agent_id, tarif=15000, redevance=10000))
        db.session.flush()
        db.session.add(
            Paiement(
                declaration_id=declaration_id,
                mode_paiement="especes",
                montant_chiffres=25000,
                montant_lettres="Vingt-cinq mille francs CFA",
                type_paiement="integral",
                solde_apres=0,
                confirme_par=agent_id,
            )
        )
        db.session.add(
            Quittance(
                declaration_id=declaration_id,
                numero_quittance="0000042",
                droit_exigible=25000,
                somme_totale_chiffres=25000,
                somme_totale_lettres="Vingt-cinq mille francs CFA",
                agent_id=agent_id,
            )
        )
        db.session.commit()
    connecter(client, "orga3@example.com")

    reponse = client.get(f"/declarations/{declaration_id}")
    page = reponse.get_data(as_text=True)

    assert "Télécharger ma quittance PDF" in page
    assert f"/exports/quittance/{declaration_id}" in page
    assert page.count("frise-etape--franchie") == 5


def test_declaration_autrui_renvoie_404(app, client):
    """404 (pas 403) si la declaration n'appartient pas a l'organisateur
    connecte."""
    autre_organisateur_id = creer_organisateur(app, "autre@example.com")
    declaration_id = creer_declaration(app, autre_organisateur_id, "nouvelle")
    creer_organisateur(app, "moi@example.com")
    connecter(client, "moi@example.com")

    reponse = client.get(f"/declarations/{declaration_id}")

    assert reponse.status_code == 404


def test_indicateur_visibilite_en_attente(app, client):
    """Promoteur sans quittance voit le message d'attente."""
    organisateur_id = creer_organisateur(app, "orga_promo@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "nouvelle", promouvoir=True)
    connecter(client, "orga_promo@example.com")

    page = client.get(f"/declarations/{declaration_id}").get_data(as_text=True)
    assert "Sera publié sur la page publique" in page


def test_indicateur_visibilite_publique(app, client):
    """Apres quittance, lien vers la page publique."""
    organisateur_id = creer_organisateur(app, "orga_visible@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "quittance_delivree", promouvoir=True)
    with app.app_context():
        agent_id = creer_agent(app)
        db.session.add(
            Quittance(
                declaration_id=declaration_id,
                numero_quittance="0000099",
                droit_exigible=20000,
                somme_totale_chiffres=20000,
                somme_totale_lettres="Vingt mille francs CFA",
                agent_id=agent_id,
            )
        )
        db.session.commit()
    connecter(client, "orga_visible@example.com")

    page = client.get(f"/declarations/{declaration_id}").get_data(as_text=True)
    assert "Visible publiquement" in page
    assert f"/evenements/{declaration_id}" in page
