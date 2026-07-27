"""Tests de la page de traitement d'une declaration par l'agent :
ouverture qui passe 'nouvelle' en 'en_evaluation', historique de
l'organisateur, fixation/modification du montant, mise en attente
(RM-030 a RM-035)."""

from datetime import datetime

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Declaration, EvaluationAgent, Notification, Organisateur, Paiement, Utilisateur


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


def creer_organisateur(app, email):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Ouedraogo", prenom="Boubacar", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000")
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
            nom_artiste_evenement="Concert de jazz",
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


def test_ouverture_declaration_nouvelle_passe_en_evaluation(app, client):
    """Ouvrir une declaration 'nouvelle' la fait automatiquement passer a
    'en_evaluation'."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga1@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "nouvelle")
    connecter(client, "agent@bbda.bf")

    client.get(f"/agent/declarations/{declaration_id}")

    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "en_evaluation"


def test_fixer_montant_change_statut_et_notifie(app, client):
    """RM-030 a RM-033 : fixer le montant cree l'evaluation, passe le statut
    a 'montant_fixe' et journalise une notification pour l'organisateur."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga2@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "en_evaluation")
    connecter(client, "agent@bbda.bf")

    reponse = client.post(
        f"/agent/declarations/{declaration_id}/fixer-montant",
        data={"tarif": "5000", "redevance": "15000", "commentaire": "Tarif standard"},
        follow_redirects=False,
    )

    assert reponse.status_code == 302
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.statut == "montant_fixe"
        assert declaration.evaluation.tarif == 5000
        assert declaration.evaluation.redevance == 15000
        assert Notification.query.filter_by(type_notification="montant_fixe").count() == 1


def test_modifier_montant_existant_ne_duplique_pas(app, client):
    """RM-035 : re-soumettre le formulaire met a jour l'evaluation existante
    au lieu d'en creer une deuxieme."""
    agent_id = creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga3@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "montant_fixe")
    with app.app_context():
        db.session.add(EvaluationAgent(declaration_id=declaration_id, agent_id=agent_id, tarif=1000, redevance=1000))
        db.session.commit()
    connecter(client, "agent@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/fixer-montant", data={"tarif": "5000", "redevance": "15000"}
    )

    with app.app_context():
        assert EvaluationAgent.query.filter_by(declaration_id=declaration_id).count() == 1
        assert EvaluationAgent.query.filter_by(declaration_id=declaration_id).first().tarif == 5000


def test_fixer_montant_champ_manquant_rejete(app, client):
    """Un tarif ou une redevance manquants sont rejetes, sans changer le
    statut de la declaration."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga4@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "en_evaluation")
    connecter(client, "agent@bbda.bf")

    client.post(f"/agent/declarations/{declaration_id}/fixer-montant", data={"tarif": "5000", "redevance": ""})

    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "en_evaluation"


def test_mettre_en_attente_avec_commentaire(app, client):
    """RM-034 : un commentaire fourni met la declaration en attente et le
    conserve."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga5@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "en_evaluation")
    connecter(client, "agent@bbda.bf")

    reponse = client.post(
        f"/agent/declarations/{declaration_id}/mettre-en-attente",
        data={"commentaire": "Piece d'identite manquante"},
        follow_redirects=False,
    )

    assert reponse.status_code == 302
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.statut == "en_attente"
        assert declaration.commentaire_agent == "Piece d'identite manquante"


def test_mettre_en_attente_sans_commentaire_rejete(app, client):
    """RM-034 : le commentaire est obligatoire pour une mise en attente."""
    creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga6@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "en_evaluation")
    connecter(client, "agent@bbda.bf")

    client.post(f"/agent/declarations/{declaration_id}/mettre-en-attente", data={"commentaire": ""})

    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "en_evaluation"


def test_historique_organisateur_affiche_total_paye_et_arriere(app, client):
    """La colonne droite affiche le total deja paye par l'organisateur."""
    agent_id = creer_agent(app)
    organisateur_id = creer_organisateur(app, "orga7@example.com")
    declaration_id = creer_declaration(app, organisateur_id, "payee")
    with app.app_context():
        db.session.add(
            Paiement(
                declaration_id=declaration_id,
                mode_paiement="especes",
                montant_chiffres=20000,
                montant_lettres="Vingt mille francs CFA",
                type_paiement="integral",
                solde_apres=0,
                confirme_par=agent_id,
            )
        )
        db.session.commit()
    autre_declaration_id = creer_declaration(app, organisateur_id, "nouvelle")
    connecter(client, "agent@bbda.bf")

    reponse = client.get(f"/agent/declarations/{autre_declaration_id}")
    page = reponse.get_data(as_text=True)

    assert "20000 FCFA" in page
    assert "2 déclaration(s) passée(s)" in page
