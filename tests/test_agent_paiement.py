"""Tests de la confirmation de paiement par l'agent (Prompt 11) :
paiement integral, paiement partiel (creation automatique d'un arriere),
generation de la quittance, validations, controle d'acces sur le statut
(RM-040 a RM-054)."""

from datetime import datetime

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Arriere, Declaration, EvaluationAgent, Notification, Organisateur, Paiement, Quittance, Utilisateur


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


def creer_declaration_avec_montant(app, statut="montant_fixe", email="orga@example.com", promouvoir=False):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
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
            promouvoir=promouvoir,
            statut=statut,
        )
        db.session.add(declaration)
        db.session.flush()

        agent = Utilisateur.query.filter_by(role="agent").first()
        db.session.add(
            EvaluationAgent(declaration_id=declaration.id, agent_id=agent.id, tarif=5000, redevance=15000)
        )
        db.session.commit()
        return declaration.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_formulaire_paiement_affiche_le_montant_a_percevoir(app, client):
    """Le formulaire affiche le total tarif + redevance calcule par
    l'agent au Prompt 10."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    reponse = client.get(f"/agent/declarations/{declaration_id}/paiement")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "20000FCFA" in page.replace(" ", "").replace("\xa0", "").replace("\n", "")


def test_formulaire_paiement_refuse_si_montant_non_fixe(app, client):
    """RM-040 : impossible d'encaisser une declaration dont le montant
    n'a pas encore ete fixe."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app, statut="en_evaluation")
    connecter(client, "agent@bbda.bf")

    reponse = client.get(f"/agent/declarations/{declaration_id}/paiement", follow_redirects=False)

    assert reponse.status_code == 302


def test_paiement_integral_genere_la_quittance(app, client):
    """RM-050 a RM-054 : un paiement integral passe le statut a
    'quittance_delivree', cree la quittance et notifie l'organisateur."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    reponse = client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "20000",
            "montant_lettres": "Vingt mille francs CFA",
            "type_paiement": "integral",
        },
        follow_redirects=False,
    )

    assert reponse.status_code == 302
    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.statut == "quittance_delivree"
        assert Quittance.query.filter_by(declaration_id=declaration_id).count() == 1
        assert Arriere.query.filter_by(declaration_id=declaration_id).count() == 0
        assert Notification.query.filter_by(type_notification="quittance_disponible").count() == 1


def test_second_paiement_refuse_si_deja_solde(app, client):
    """Un second encaissement sur une declaration deja quittee est refuse."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    donnees = {
        "mode_paiement": "especes",
        "montant_chiffres": "20000",
        "montant_lettres": "Vingt mille francs CFA",
        "type_paiement": "integral",
    }
    client.post(f"/agent/declarations/{declaration_id}/confirmer-paiement", data=donnees)
    reponse = client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data=donnees,
        follow_redirects=True,
    )

    page = reponse.get_data(as_text=True).lower()
    assert "déjà" in page or "deja" in page or "quittance" in page
    with app.app_context():
        assert Paiement.query.filter_by(declaration_id=declaration_id).count() == 1
        assert Quittance.query.filter_by(declaration_id=declaration_id).count() == 1


def test_refixer_montant_refuse_apres_paiement(app, client):
    """Apres quittance, impossible de re-valider le montant (evite un 2e cycle)."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "20000",
            "montant_lettres": "Vingt mille francs CFA",
            "type_paiement": "integral",
        },
    )
    reponse = client.post(
        f"/agent/declarations/{declaration_id}/fixer-montant",
        data={"tarif": "5000", "redevance": "15000"},
        follow_redirects=True,
    )

    page = reponse.get_data(as_text=True).lower()
    assert "déjà" in page or "deja" in page or "quittance" in page
    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "quittance_delivree"
        assert Notification.query.filter_by(type_notification="montant_fixe").count() == 0


def test_page_traitement_verrouillee_apres_paiement(app, client):
    """Le formulaire de fixation disparait apres encaissement."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")
    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "20000",
            "montant_lettres": "Vingt mille francs CFA",
            "type_paiement": "integral",
        },
    )

    reponse = client.get(f"/agent/declarations/{declaration_id}")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "verrouillés" in page or "verrouilles" in page or "Paiement déjà enregistré" in page
    assert 'name="tarif"' not in page
    assert "Valider et notifier" not in page


def test_paiement_depassant_le_reste_du_est_refuse(app, client):
    """Un montant saisi superieur au reste du est rejete."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "50000",
            "montant_lettres": "Cinquante mille francs CFA",
            "type_paiement": "integral",
        },
    )

    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "montant_fixe"
        assert Paiement.query.filter_by(declaration_id=declaration_id).count() == 0


def test_formulaire_paiement_refuse_si_deja_quittance(app, client):
    """La page /paiement n'est plus accessible apres solde."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app, statut="quittance_delivree")
    with app.app_context():
        agent = Utilisateur.query.filter_by(role="agent").first()
        db.session.add(
            Quittance(
                declaration_id=declaration_id,
                numero_quittance="0000088",
                droit_exigible=20000,
                somme_totale_chiffres=20000,
                somme_totale_lettres="Vingt mille",
                agent_id=agent.id,
            )
        )
        # Remettre un statut "pret" artificiel pour verifier le garde-fou quittance
        Declaration.query.get(declaration_id).statut = "montant_fixe"
        db.session.commit()

    connecter(client, "agent@bbda.bf")
    reponse = client.get(f"/agent/declarations/{declaration_id}/paiement", follow_redirects=True)
    assert "déjà" in reponse.get_data(as_text=True).lower() or "solde" in reponse.get_data(as_text=True).lower()


def test_paiement_partiel_cree_un_arriere(app, client):
    """RM-044 : un paiement partiel cree automatiquement un arriere avec
    une echeance a 7 jours."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "cheque",
            "numero_cheque": "CHQ-001",
            "montant_chiffres": "10000",
            "montant_lettres": "Dix mille francs CFA",
            "type_paiement": "partiel",
            "reste_a_payer": "10000",
        },
    )

    with app.app_context():
        declaration = Declaration.query.get(declaration_id)
        assert declaration.statut == "quittance_delivree"
        arriere = Arriere.query.filter_by(declaration_id=declaration_id).first()
        assert arriere is not None
        assert arriere.montant_du == 10000
        assert (arriere.date_echeance - datetime.utcnow()).days in (6, 7)


def test_paiement_cheque_sans_numero_rejete(app, client):
    """Le numero de cheque est obligatoire quand le mode est 'cheque'."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "cheque",
            "montant_chiffres": "20000",
            "montant_lettres": "Vingt mille francs CFA",
            "type_paiement": "integral",
        },
    )

    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "montant_fixe"


def test_paiement_partiel_sans_reste_a_payer_rejete(app, client):
    """Le reste a payer est obligatoire quand le type est 'partiel'."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    connecter(client, "agent@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "10000",
            "montant_lettres": "Dix mille francs CFA",
            "type_paiement": "partiel",
        },
    )

    with app.app_context():
        assert Declaration.query.get(declaration_id).statut == "montant_fixe"


def test_organisateur_ne_peut_pas_confirmer_un_paiement(app, client):
    """RM-005 : seuls agent/admin peuvent confirmer un paiement."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app)
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Test", prenom="Orga", email="autre@example.com", mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        db.session.add(Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000009"))
        db.session.commit()
    connecter(client, "autre@example.com")

    reponse = client.get(f"/agent/declarations/{declaration_id}/paiement")

    assert reponse.status_code == 403


def test_paiement_evenement_promu_notifie_publication(app, client):
    """Prompt 19 : apres quittance, un evenement marque 'promouvoir'
    declenche une notification evenement_publie."""
    creer_agent(app)
    declaration_id = creer_declaration_avec_montant(app, promouvoir=True)
    connecter(client, "agent@bbda.bf")

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
        assert Notification.query.filter_by(type_notification="quittance_disponible").count() == 1
        assert Notification.query.filter_by(type_notification="evenement_publie").count() == 1
