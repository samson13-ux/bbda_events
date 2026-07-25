"""Tests du moteur de gestion des arrieres (Prompt 14) : verification/creation
d'arrieres, blocage automatique du compte au-dela du seuil, rappels
automatiques, blocage/deblocage manuel, surveillance des comptes, et
integration des arrieres dans la quittance (RM-060 a RM-084)."""

from datetime import datetime, timedelta

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import (
    AlerteSurveillance,
    Arriere,
    Declaration,
    EvaluationAgent,
    Notification,
    Organisateur,
    ParametresSysteme,
    Quittance,
    Utilisateur,
)

from backend.arrieres.moteur import (
    bloquer_compte,
    creer_arriere,
    debloquer_compte,
    integrer_arrieres_dans_quittance,
    lever_surveillance,
    marquer_compte_arriere,
    marquer_surveillance,
    verifier_arriere,
    verifier_connexion_surveillance,
    verifier_et_envoyer_rappels,
)


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


def creer_organisateur(app, email="orga_arr@example.com", statut_compte="actif"):
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


def creer_declaration(app, organisateur_id, statut="montant_fixe", tarif=5000, redevance=15000, agent_id=None):
    with app.app_context():
        declaration = Declaration(
            organisateur_id=organisateur_id,
            nom_demandeur="Ouedraogo",
            prenom_demandeur="Boubacar",
            qualite_demandeur="Organisateur",
            telephone="70000000",
            email="orga_arr@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Concert de test",
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
        db.session.flush()
        if agent_id is None:
            agent = Utilisateur.query.filter_by(role="agent").first()
            agent_id = agent.id if agent else None
        if agent_id:
            db.session.add(EvaluationAgent(declaration_id=declaration.id, agent_id=agent_id, tarif=tarif, redevance=redevance))
        db.session.commit()
        return declaration.id


def creer_agent(app, email="agent_arr@bbda.bf", role="agent"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        agent = Utilisateur(nom="Kabore", prenom="Issa", email=email, mot_de_passe=hachage, role=role)
        db.session.add(agent)
        db.session.commit()
        return agent.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_verifier_arriere_calcule_le_total_et_le_caractere_bloquant(app):
    """FONCTION 1 : montant_total_du, nombre_arrieres, bloquant (seuil par
    defaut 1000 FCFA en l'absence de parametre configure)."""
    organisateur_id = creer_organisateur(app)
    with app.app_context():
        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=600, date_echeance=datetime.utcnow()))
        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=500, date_echeance=datetime.utcnow()))
        db.session.commit()

        etat = verifier_arriere(organisateur_id)
        assert etat["montant_total_du"] == 1100
        assert etat["nombre_arrieres"] == 2
        assert etat["bloquant"] is True


def test_verifier_arriere_sous_le_seuil_non_bloquant(app):
    organisateur_id = creer_organisateur(app)
    with app.app_context():
        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=200, date_echeance=datetime.utcnow()))
        db.session.commit()

        etat = verifier_arriere(organisateur_id)
        assert etat["bloquant"] is False


def test_creer_arriere_fixe_echeance_a_j_plus_delai_et_bloque_le_compte(app):
    """FONCTION 2 (RM-062, RM-063, RM-073) : echeance a J+7 par defaut, et
    passage automatique du compte a 'arriere' si le seuil est franchi."""
    organisateur_id = creer_organisateur(app)
    declaration_id = creer_declaration(app, organisateur_id)

    with app.app_context():
        arriere = creer_arriere(declaration_id, 5000)
        db.session.commit()

        assert (arriere.date_echeance - datetime.utcnow()).days in (6, 7)
        assert Organisateur.query.get(organisateur_id).statut_compte == "arriere"


def test_creer_arriere_sous_le_seuil_ne_bloque_pas(app):
    organisateur_id = creer_organisateur(app)
    declaration_id = creer_declaration(app, organisateur_id)

    with app.app_context():
        creer_arriere(declaration_id, 500)
        db.session.commit()

        assert Organisateur.query.get(organisateur_id).statut_compte == "actif"


def test_verifier_et_envoyer_rappels_respecte_le_delai_entre_deux_relances(app):
    """FONCTION 3 (RM-070 a RM-072) : un arriere en retard recoit un rappel,
    mais pas deux fois dans le meme delai."""
    organisateur_id = creer_organisateur(app)
    with app.app_context():
        arriere_a_relancer = Arriere(
            organisateur_id=organisateur_id,
            montant_du=5000,
            date_echeance=datetime.utcnow() - timedelta(days=10),
            derniere_notification=None,
        )
        arriere_deja_relance = Arriere(
            organisateur_id=organisateur_id,
            montant_du=3000,
            date_echeance=datetime.utcnow() - timedelta(days=10),
            derniere_notification=datetime.utcnow() - timedelta(days=2),
        )
        arriere_pas_encore_echu = Arriere(
            organisateur_id=organisateur_id,
            montant_du=1000,
            date_echeance=datetime.utcnow() + timedelta(days=3),
        )
        db.session.add_all([arriere_a_relancer, arriere_deja_relance, arriere_pas_encore_echu])
        db.session.commit()

        nombre = verifier_et_envoyer_rappels()

        assert nombre == 1
        assert Notification.query.filter_by(type_notification="rappel_arriere").count() == 1
        assert arriere_a_relancer.derniere_notification is not None


def test_marquer_bloquer_debloquer_compte(app):
    """FONCTIONS 4, 5, 6 : transitions manuelles/automatiques de statut, et
    soldes des arrieres au deblocage (RM-075, RM-076)."""
    organisateur_id = creer_organisateur(app)
    with app.app_context():
        marquer_compte_arriere(organisateur_id)
        db.session.commit()
        assert Organisateur.query.get(organisateur_id).statut_compte == "arriere"

        bloquer_compte(organisateur_id)
        db.session.commit()
        assert Organisateur.query.get(organisateur_id).statut_compte == "bloque"

        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=2000, date_echeance=datetime.utcnow()))
        db.session.commit()

        debloquer_compte(organisateur_id)
        db.session.commit()

        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte == "actif"
        assert all(a.statut == "regle" for a in Arriere.query.filter_by(organisateur_id=organisateur_id).all())


def test_marquer_et_lever_surveillance(app):
    """FONCTIONS 7, 8 (RM-080, RM-084) : mise sous surveillance et levee,
    avec traitement des alertes en attente."""
    organisateur_id = creer_organisateur(app)
    agent_id = creer_agent(app)

    with app.app_context():
        marquer_surveillance(organisateur_id, agent_id, commentaire="Organisateur injoignable")
        db.session.commit()

        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte == "surveillance"
        alerte = AlerteSurveillance.query.filter_by(organisateur_id=organisateur_id).first()
        assert alerte is not None
        assert alerte.marque_par == agent_id

        lever_surveillance(organisateur_id, agent_id)
        db.session.commit()

        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte == "actif"
        assert Organisateur.query.get(organisateur_id)
        assert AlerteSurveillance.query.filter_by(organisateur_id=organisateur_id, traitee=False).count() == 0


def test_verifier_connexion_surveillance_notifie_les_agents(app):
    """FONCTION 9 (RM-081) : une connexion sous surveillance cree une
    alerte et notifie tous les agents/administrateurs actifs."""
    creer_agent(app, "agent2@bbda.bf", role="agent")
    creer_agent(app, "admin2@bbda.bf", role="admin")
    organisateur_id = creer_organisateur(app, statut_compte="surveillance")

    with app.app_context():
        resultat = verifier_connexion_surveillance(organisateur_id)
        db.session.commit()

        assert resultat is True
        assert AlerteSurveillance.query.filter_by(organisateur_id=organisateur_id).count() == 1
        assert Notification.query.filter_by(type_notification="alerte_surveillance").count() == 2


def test_verifier_connexion_surveillance_compte_actif_ne_fait_rien(app):
    organisateur_id = creer_organisateur(app, statut_compte="actif")
    with app.app_context():
        assert verifier_connexion_surveillance(organisateur_id) is False
        assert AlerteSurveillance.query.count() == 0


def test_connexion_organisateur_sous_surveillance_declenche_lalerte_via_la_route(app, client):
    """Verifie le branchement reel dans auth/routes.py (integre par le
    Prompt 14 conformement au guide de dev)."""
    creer_agent(app, "agent3@bbda.bf", role="agent")
    creer_organisateur(app, email="surveille2@example.com", statut_compte="surveillance")

    connecter(client, "surveille2@example.com")

    with app.app_context():
        assert AlerteSurveillance.query.count() == 1
        assert Notification.query.filter_by(type_notification="alerte_surveillance").count() == 1


def test_integrer_arrieres_dans_quittance_additionne_les_arrieres_preexistants(app):
    """FONCTION 10 (RM-050 a RM-054) : la quittance reporte les arrieres
    preexistants dans droit_arriere/droit_exigible."""
    creer_agent(app, "agent_quittance@bbda.bf")
    organisateur_id = creer_organisateur(app)
    declaration_id = creer_declaration(app, organisateur_id)

    with app.app_context():
        db.session.add(Arriere(organisateur_id=organisateur_id, montant_du=3000, date_echeance=datetime.utcnow()))
        db.session.commit()

        declaration = Declaration.query.get(declaration_id)
        agent = Utilisateur.query.filter_by(role="agent").first()
        quittance = Quittance(
            declaration=declaration,
            agent=agent,
            numero_quittance="0000001",
            droit_annuel=20000,
            droit_arriere=0,
            droit_exigible=20000,
            somme_totale_chiffres=20000,
            somme_totale_lettres="Vingt mille francs CFA",
        )
        db.session.add(quittance)
        db.session.flush()

        integrer_arrieres_dans_quittance(quittance)

        assert quittance.droit_arriere == 3000
        assert quittance.droit_exigible == 23000


def test_paiement_partiel_bloque_automatiquement_le_compte_via_la_route(app, client):
    """Verifie le branchement reel dans agent/routes.py::confirmer_paiement :
    un reste a payer superieur au seuil bloque automatiquement le compte,
    sans compter deux fois l'arriere fraichement cree dans la quittance."""
    creer_agent(app, "agent4@bbda.bf", role="agent")
    organisateur_id = creer_organisateur(app, email="orga_partiel@example.com")
    declaration_id = creer_declaration(app, organisateur_id, tarif=5000, redevance=15000)
    connecter(client, "agent4@bbda.bf")

    client.post(
        f"/agent/declarations/{declaration_id}/confirmer-paiement",
        data={
            "mode_paiement": "especes",
            "montant_chiffres": "10000",
            "montant_lettres": "Dix mille francs CFA",
            "type_paiement": "partiel",
            "reste_a_payer": "10000",
        },
    )

    with app.app_context():
        organisateur = Organisateur.query.get(organisateur_id)
        assert organisateur.statut_compte == "arriere"

        declaration = Declaration.query.get(declaration_id)
        quittance = declaration.quittance
        assert quittance is not None
        # L'arriere de CETTE transaction (10000) ne doit pas etre compte
        # dans le droit_arriere de sa propre quittance (pas d'arriere
        # PRE-EXISTANT ici) : droit_exigible == montant_total de la
        # declaration (20000), pas 30000.
        assert quittance.droit_arriere == 0
        assert quittance.droit_exigible == 20000
