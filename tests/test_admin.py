"""Tests de l'espace administrateur : tableau de bord, gestion
des comptes utilisateurs (creation d'agent, activation/desactivation), et
parametres systeme (RM-002, RM-060 a RM-076, RM-090 a RM-103 §9)."""

import bcrypt
import pytest

from app import create_app
from extensions import db
from datetime import datetime, timedelta

from models import Declaration, MessageContact, Organisateur, ParametresSysteme, Utilisateur

from backend.arrieres.moteur import seuil_arriere


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


def creer_admin(app, email="admin_p16@bbda.bf"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        admin = Utilisateur(nom="Traore", prenom="Aicha", email=email, mot_de_passe=hachage, role="admin")
        db.session.add(admin)
        db.session.commit()
        return admin.id


def creer_organisateur(app, email="orga_p16@example.com"):
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Ouedraogo", prenom="Boubacar", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        db.session.add(Organisateur(utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000"))
        db.session.commit()
        return utilisateur.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def test_tableau_de_bord_admin_affiche_les_statistiques(app, client):
    """Le tableau de bord affiche le total des declarations et des comptes actifs."""
    creer_admin(app)
    creer_organisateur(app)
    connecter(client, "admin_p16@bbda.bf")

    reponse = client.get("/admin/")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "Déclarations totales" in page
    assert "Comptes actifs" in page


def test_page_utilisateurs_liste_organisateurs_et_agents(app, client):
    creer_admin(app)
    creer_organisateur(app, email="liste@example.com")
    connecter(client, "admin_p16@bbda.bf")

    reponse = client.get("/admin/utilisateurs")
    page = reponse.get_data(as_text=True)

    assert reponse.status_code == 200
    assert "Boubacar" in page
    assert "Aicha" in page  # l'admin lui-meme apparait dans l'onglet Agents


def test_creation_compte_agent(app, client):
    """RM-002 : l'administrateur peut creer un compte agent."""
    creer_admin(app)
    connecter(client, "admin_p16@bbda.bf")

    reponse = client.post(
        "/admin/utilisateurs/nouveau-agent",
        data={"nom": "Kabore", "prenom": "Issa", "email": "nouvel_agent@bbda.bf", "mot_de_passe": "password123"},
        follow_redirects=False,
    )

    assert reponse.status_code == 302
    with app.app_context():
        agent = Utilisateur.query.filter_by(email="nouvel_agent@bbda.bf").first()
        assert agent is not None
        assert agent.role == "agent"
        assert bcrypt.checkpw(b"password123", agent.mot_de_passe.encode("utf-8"))


def test_creation_compte_agent_email_deja_utilise_rejetee(app, client):
    creer_admin(app)
    connecter(client, "admin_p16@bbda.bf")

    reponse = client.post(
        "/admin/utilisateurs/nouveau-agent",
        data={"nom": "Kabore", "prenom": "Issa", "email": "admin_p16@bbda.bf", "mot_de_passe": "password123"},
        follow_redirects=True,
    )

    page = reponse.get_data(as_text=True)
    assert "existe déjà" in page
    with app.app_context():
        assert Utilisateur.query.filter_by(email="admin_p16@bbda.bf").count() == 1


def test_desactiver_puis_reactiver_un_compte(app, client):
    creer_admin(app)
    utilisateur_id = creer_organisateur(app, email="a_desactiver@example.com")
    connecter(client, "admin_p16@bbda.bf")

    client.post(f"/admin/utilisateurs/{utilisateur_id}/desactiver")
    with app.app_context():
        assert Utilisateur.query.get(utilisateur_id).statut == "inactif"

    # Un compte desactive ne peut plus se connecter (Utilisateur.is_active).
    deconnexion_client = client
    deconnexion_client.get("/auth/deconnexion")
    reponse_connexion = connecter(deconnexion_client, "a_desactiver@example.com")
    assert reponse_connexion.status_code == 403

    connecter(client, "admin_p16@bbda.bf")
    client.post(f"/admin/utilisateurs/{utilisateur_id}/activer")
    with app.app_context():
        assert Utilisateur.query.get(utilisateur_id).statut == "actif"


def test_admin_ne_peut_pas_se_desactiver_lui_meme(app, client):
    admin_id = creer_admin(app)
    connecter(client, "admin_p16@bbda.bf")

    client.post(f"/admin/utilisateurs/{admin_id}/desactiver")

    with app.app_context():
        assert Utilisateur.query.get(admin_id).statut == "actif"


def test_parametres_affiche_les_valeurs_par_defaut(app, client):
    creer_admin(app)
    connecter(client, "admin_p16@bbda.bf")

    reponse = client.get("/admin/parametres")
    page = reponse.get_data(as_text=True)

    assert 'value="1000"' in page
    assert 'value="7"' in page


def test_enregistrer_parametres_modifie_le_seuil_utilise_par_le_moteur(app, client):
    """Le seuil enregistre depuis l'admin est immediatement utilise par le
    moteur d'arrieres (backend/arrieres/moteur.py)."""
    creer_admin(app)
    connecter(client, "admin_p16@bbda.bf")

    reponse = client.post(
        "/admin/parametres",
        data={"SEUIL_ARRIERE": "5000", "DELAI_NOTIFICATION": "10"},
        follow_redirects=False,
    )

    assert reponse.status_code == 302
    with app.app_context():
        assert ParametresSysteme.query.filter_by(cle="SEUIL_ARRIERE").first().valeur == "5000"
        assert seuil_arriere() == 5000


def test_enregistrer_parametres_champ_invalide_rejete(app, client):
    creer_admin(app)
    connecter(client, "admin_p16@bbda.bf")

    client.post("/admin/parametres", data={"SEUIL_ARRIERE": "abc", "DELAI_NOTIFICATION": "10"})

    with app.app_context():
        assert ParametresSysteme.query.filter_by(cle="SEUIL_ARRIERE").first() is None


def test_organisateur_ne_peut_pas_acceder_a_lespace_admin(app, client):
    creer_organisateur(app, email="simple_p16@example.com")
    connecter(client, "simple_p16@example.com")

    assert client.get("/admin/").status_code == 403
    assert client.get("/admin/utilisateurs").status_code == 403
    assert client.get("/admin/parametres").status_code == 403


def test_admin_voit_et_traite_les_messages_contact(app, client):
    """Les messages du formulaire public sont listes et marquables comme traites."""
    creer_admin(app)
    with app.app_context():
        db.session.add(
            MessageContact(
                nom="Visiteur Test",
                email="visiteur@example.com",
                sujet="Demande d aide",
                message="Comment declarer un concert ?",
            )
        )
        db.session.commit()
        message_id = MessageContact.query.first().id

    connecter(client, "admin_p16@bbda.bf")
    page = client.get("/admin/messages-contact").get_data(as_text=True)
    assert "Demande d aide" in page
    assert "Visiteur Test" in page
    assert "Non traité" in page

    client.post(f"/admin/messages-contact/{message_id}/traiter")
    with app.app_context():
        assert MessageContact.query.get(message_id).traite is True
    page = client.get("/admin/messages-contact?filtre=traites").get_data(as_text=True)
    assert "Traité" in page


def test_admin_peut_depublier_un_evenement_public(app, client):
    """RM-092 : l'admin retire un evenement du listing public."""
    creer_admin(app)
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(
            nom="Zongo", prenom="Amina", email="orga_pub@example.com", mot_de_passe=hachage, role="organisateur"
        )
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000099"
        )
        db.session.add(organisateur)
        db.session.flush()
        declaration = Declaration(
            organisateur_id=organisateur.id,
            nom_demandeur="Zongo",
            prenom_demandeur="Amina",
            qualite_demandeur="Organisateur",
            telephone="70000099",
            email="orga_pub@example.com",
            nature_manifestation="Concert",
            nom_artiste_evenement="Concert Admin Test",
            nom_salle="Salle",
            adresse="Adresse",
            ville="Ouagadougou",
            date_evenement=datetime.utcnow() + timedelta(days=10),
            duree_heures=2,
            capacite_accueil=100,
            nature_diffusion="Musique vivante",
            promouvoir=True,
            statut="quittance_delivree",
        )
        db.session.add(declaration)
        db.session.commit()
        declaration_id = declaration.id

    connecter(client, "admin_p16@bbda.bf")
    assert "Concert Admin Test" in client.get("/evenements").get_data(as_text=True)

    reponse = client.post(
        f"/admin/evenements-publics/{declaration_id}/depublier",
        follow_redirects=False,
    )
    assert reponse.status_code == 302

    page_evenements = client.get("/evenements").get_data(as_text=True)
    assert "Aucun événement à venir" in page_evenements
    assert 'carte-evenement' not in page_evenements
    with app.app_context():
        assert Declaration.query.get(declaration_id).promouvoir is False
