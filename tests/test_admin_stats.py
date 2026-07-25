"""Tests des statistiques avancees administrateur (Prompt 17) : fonctions
de calcul dans admin/stats.py et page /admin/statistiques."""

from datetime import datetime, timedelta

import bcrypt
import pytest

from app import create_app
from backend.admin import stats as stats_admin
from extensions import db
from models import Arriere, Declaration, Organisateur, Paiement, Quittance, Utilisateur


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


def creer_admin(app, email="admin_stats@bbda.bf"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        admin = Utilisateur(nom="Traore", prenom="Awa", email=email, mot_de_passe=hachage, role="admin")
        db.session.add(admin)
        db.session.commit()
        return admin.id


def creer_organisateur_avec_declarations(app, email="orga_stats@example.com", nb=2, offset_quittance=0):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Ouedraogo", prenom="Boubacar", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000")
        db.session.add(organisateur)
        db.session.flush()

        agent = Utilisateur.query.filter_by(role="admin").first()
        if agent is None:
            agent = Utilisateur.query.filter_by(role="agent").first()
        if agent is None:
            agent = Utilisateur(nom="Agent", prenom="Test", email="agent_stats@bbda.bf", mot_de_passe=hachage, role="agent")
            db.session.add(agent)
            db.session.flush()

        natures = ["Concert", "Festival"]
        for i in range(nb):
            declaration = Declaration(
                organisateur_id=organisateur.id,
                nom_demandeur="Ouedraogo",
                prenom_demandeur="Boubacar",
                qualite_demandeur="Organisateur",
                telephone="70000000",
                email=email,
                nature_manifestation=natures[i % 2],
                nom_artiste_evenement=f"Evenement {i}",
                nom_salle="Salle Test",
                adresse="Adresse",
                ville="Ouagadougou",
                date_evenement=datetime(2026, 8, 1, 20, 0),
                duree_heures=3,
                capacite_accueil=100,
                nature_diffusion="Musique vivante",
                statut="quittance_delivree",
                date_soumission=datetime(2026, 3 + i, 10, 12, 0),
            )
            db.session.add(declaration)
            db.session.flush()
            db.session.add(
                Paiement(
                    declaration_id=declaration.id,
                    mode_paiement="especes",
                    montant_chiffres=10000 * (i + 1),
                    montant_lettres="Dix mille",
                    type_paiement="integral",
                    solde_apres=0,
                    confirme_par=agent.id,
                )
            )
            numero = offset_quittance + i + 1
            db.session.add(
                Quittance(
                    declaration_id=declaration.id,
                    agent_id=agent.id,
                    numero_quittance=f"{numero:07d}",
                    droit_annuel=10000 * (i + 1),
                    droit_arriere=0,
                    droit_exigible=10000 * (i + 1),
                    somme_totale_chiffres=10000 * (i + 1),
                    somme_totale_lettres="Dix mille",
                    date_delivrance=datetime(2026, 3 + i, 15, 12, 0),
                )
            )
        db.session.commit()
        return organisateur.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_get_declarations_par_mois(app):
    creer_admin(app)
    creer_organisateur_avec_declarations(app, nb=2)

    with app.app_context():
        resultat = stats_admin.get_declarations_par_mois(2026)
        assert resultat["Mars"] == 1
        assert resultat["Avril"] == 1
        assert resultat["Janvier"] == 0


def test_get_redevances_par_mois(app):
    creer_admin(app)
    creer_organisateur_avec_declarations(app, nb=2)

    with app.app_context():
        resultat = stats_admin.get_redevances_par_mois(2026)
        assert resultat["Mars"] == 10000
        assert resultat["Avril"] == 20000


def test_get_repartition_par_type(app):
    creer_admin(app)
    creer_organisateur_avec_declarations(app, nb=2)

    with app.app_context():
        resultat = stats_admin.get_repartition_par_type()
        assert resultat["Concert"] == 1
        assert resultat["Festival"] == 1


def test_get_top_organisateurs(app):
    creer_admin(app)
    creer_organisateur_avec_declarations(app, email="top1@example.com", nb=2, offset_quittance=0)
    creer_organisateur_avec_declarations(app, email="top2@example.com", nb=1, offset_quittance=10)

    with app.app_context():
        top = stats_admin.get_top_organisateurs(limit=10)
        assert len(top) == 2
        assert top[0]["nb_declarations"] == 2
        assert top[0]["total_paye"] == 30000


def test_get_stats_arrieres(app):
    creer_admin(app)
    organisateur_id = creer_organisateur_avec_declarations(app, email="arr@example.com", nb=1)

    with app.app_context():
        db.session.add(
            Arriere(
                organisateur_id=organisateur_id,
                montant_du=5000,
                date_echeance=datetime.utcnow() - timedelta(days=5),
            )
        )
        db.session.commit()

        stats = stats_admin.get_stats_arrieres()
        assert stats["total_du"] == 5000
        assert stats["nombre_organisateurs"] == 1
        assert stats["montant_moyen"] == 5000
        assert stats["plus_ancien"] is not None


def test_page_statistiques_accessible_admin(app, client):
    creer_admin(app)
    creer_organisateur_avec_declarations(app, nb=1)
    connecter(client, "admin_stats@bbda.bf")

    reponse = client.get("/admin/statistiques")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "Statistiques avancées" in page
    assert "Top organisateurs" in page
    assert "Boubacar" in page


def test_organisateur_ne_peut_pas_acceder_aux_statistiques(app, client):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Zongo", prenom="Aminata", email="orga_interdit@example.com", mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        db.session.add(Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000009"))
        db.session.commit()

    connecter(client, "orga_interdit@example.com")
    assert client.get("/admin/statistiques").status_code == 403
