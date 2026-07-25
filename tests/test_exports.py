"""Tests de la generation et du telechargement de la quittance PDF
(Prompt 12, RM-050 a RM-054)."""

import os
from datetime import datetime

import bcrypt
import pytest

from app import create_app
from backend.exports.routes import generer_quittance
from extensions import db
from models import Declaration, EvaluationAgent, Organisateur, Paiement, Utilisateur


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


def creer_scenario_complet(app, email="orga@example.com"):
    """Cree un agent, un organisateur et une declaration avec evaluation +
    paiement, prete pour la generation de quittance."""
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        agent = Utilisateur(nom="Kabore", prenom="Issa", email="agent@bbda.bf", mot_de_passe=hachage, role="agent")
        db.session.add(agent)

        utilisateur = Utilisateur(nom="Ouedraogo", prenom="Boubacar", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000")
        db.session.add(organisateur)
        db.session.flush()

        declaration = Declaration(
            organisateur_id=organisateur.id,
            nom_demandeur="Ouedraogo",
            prenom_demandeur="Boubacar",
            qualite_demandeur="Organisateur",
            telephone="70000000",
            email=email,
            nature_manifestation="Concert",
            nom_artiste_evenement="Concert de test",
            nom_salle="Salle Test",
            adresse="Adresse Test",
            ville="Ouagadougou",
            date_evenement=datetime(2026, 8, 1, 20, 0),
            duree_heures=3,
            capacite_accueil=100,
            nature_diffusion="Musique vivante",
            statut="quittance_delivree",
        )
        db.session.add(declaration)
        db.session.flush()

        db.session.add(
            EvaluationAgent(declaration_id=declaration.id, agent_id=agent.id, tarif=5000, redevance=15000)
        )
        db.session.add(
            Paiement(
                declaration_id=declaration.id,
                mode_paiement="especes",
                montant_chiffres=20000,
                montant_lettres="Vingt mille francs CFA",
                type_paiement="integral",
                solde_apres=0,
                confirme_par=agent.id,
            )
        )
        db.session.commit()

        generer_quittance(declaration, agent)
        db.session.commit()
        return declaration.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_generer_quittance_cree_le_fichier_pdf(app):
    """generer_quittance() cree un fichier PDF reel sur disque et
    enregistre son chemin (RM-050 a RM-054)."""
    declaration_id = creer_scenario_complet(app)
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        chemin = declaration.quittance.fichier_pdf_path
        assert chemin is not None
        assert os.path.exists(chemin)
        assert chemin.endswith(".pdf")


def test_telechargement_quittance_par_le_proprietaire(app, client):
    """L'organisateur proprietaire peut telecharger sa quittance PDF."""
    declaration_id = creer_scenario_complet(app)
    connecter(client, "orga@example.com")

    reponse = client.get(f"/exports/quittance/{declaration_id}")

    assert reponse.status_code == 200
    assert reponse.content_type == "application/pdf"


def test_telechargement_refuse_a_un_autre_organisateur(app, client):
    """RM-054 : un organisateur ne peut pas telecharger la quittance d'un
    autre."""
    declaration_id = creer_scenario_complet(app)
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        autre = Utilisateur(nom="Zongo", prenom="Aminata", email="autre@example.com", mot_de_passe=hachage, role="organisateur")
        db.session.add(autre)
        db.session.flush()
        db.session.add(Organisateur(utilisateur_id=autre.id, qualite="Organisateur", telephone="70000009"))
        db.session.commit()
    connecter(client, "autre@example.com")

    reponse = client.get(f"/exports/quittance/{declaration_id}")

    assert reponse.status_code == 404


def test_telechargement_404_si_pas_de_quittance(app, client):
    """Impossible de telecharger une quittance qui n'existe pas encore."""
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Sanou", prenom="Paul", email="paul@example.com", mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000005")
        db.session.add(organisateur)
        db.session.flush()
        declaration = Declaration(
            organisateur_id=organisateur.id,
            nom_demandeur="Sanou",
            prenom_demandeur="Paul",
            qualite_demandeur="Organisateur",
            telephone="70000005",
            email="paul@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Sans quittance",
            nom_salle="Salle Test",
            adresse="Adresse Test",
            ville="Ouagadougou",
            date_evenement=datetime(2026, 8, 1, 20, 0),
            duree_heures=3,
            capacite_accueil=100,
            nature_diffusion="Musique vivante",
            statut="nouvelle",
        )
        db.session.add(declaration)
        db.session.commit()
        declaration_id = declaration.id
    connecter(client, "paul@example.com")

    reponse = client.get(f"/exports/quittance/{declaration_id}")

    assert reponse.status_code == 404


def test_numero_quittance_est_sequentiel_et_formate(app):
    """Le numero de quittance est sequentiel et formate sur 7 chiffres
    (ex: 0000001)."""
    declaration_id = creer_scenario_complet(app)
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.quittance.numero_quittance == "0000001"
