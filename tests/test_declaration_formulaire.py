"""Tests du formulaire de nouvelle declaration (Prompt 7) : soumission
nominale, artistes lies (Festival), validation des champs obligatoires et
de la date, blocage d'un compte en arriere (RM-010 a RM-014)."""

from datetime import datetime, timedelta

import bcrypt
import pytest

from app import create_app
from extensions import db
from models import Declaration, ListeArtiste, Notification, Organisateur, Utilisateur


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


def creer_organisateur(app, email, statut_compte="actif", mot_de_passe="password123"):
    """Insere un compte organisateur directement en base et retourne son id."""
    with app.app_context():
        hachage = bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        utilisateur = Utilisateur(nom="Test", prenom="Orga", email=email, mot_de_passe=hachage, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id, qualite="Organisateur", telephone="70000000", statut_compte=statut_compte
        )
        db.session.add(organisateur)
        db.session.commit()
        return organisateur.id


def connecter(client, email, mot_de_passe="password123"):
    return client.post("/auth/connexion", data={"email": email, "password": mot_de_passe})


def _date_future():
    return (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M")


DONNEES_BASE = {
    "nom_demandeur": "Ouedraogo",
    "prenom_demandeur": "Boubacar",
    "qualite": "Organisateur",
    "telephone": "70000001",
    "email": "orga@example.com",
    "nature_manifestation": "Concert",
    "nom_artiste_evenement": "Floby",
    "nom_salle": "Salle des fetes",
    "adresse": "Avenue Kwame Nkrumah",
    "ville": "Ouagadougou",
    "duree_heures": "3",
    "capacite_accueil": "500",
    "entree": "payante",
    "nature_diffusion": "vivante",
}


def test_soumission_concert_nominale(app, client):
    """Une declaration de type Concert, champs valides, est enregistree avec
    le statut 'nouvelle' et une notification de confirmation est journalisee."""
    with app.app_context():
        hachage = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        db.session.add(
            Utilisateur(nom="Admin", prenom="BBDA", email="admin_decl@bbda.bf", mot_de_passe=hachage, role="admin")
        )
        db.session.commit()

    creer_organisateur(app, "orga@example.com")
    connecter(client, "orga@example.com")
    donnees = dict(DONNEES_BASE, date_evenement=_date_future())

    reponse = client.post("/declarations/nouvelle", data=donnees, follow_redirects=False)

    assert reponse.status_code == 302
    assert reponse.headers["Location"].endswith("/declarations/")
    with app.app_context():
        declaration = Declaration.query.filter_by(nom_artiste_evenement="Floby").first()
        assert declaration is not None
        assert declaration.statut == "nouvelle"
        assert declaration.nature_diffusion == "Musique vivante"
        assert Notification.query.filter_by(type_notification="confirmation_declaration").count() == 1
        assert Notification.query.filter_by(type_notification="nouvelle_declaration").count() == 1


def test_soumission_festival_avec_artistes(app, client):
    """Une declaration de type Festival avec 2 artistes cree bien 2
    ListeArtiste rattaches a la declaration."""
    creer_organisateur(app, "orga2@example.com")
    connecter(client, "orga2@example.com")
    donnees = dict(DONNEES_BASE, date_evenement=_date_future())
    donnees["email"] = "orga2@example.com"
    donnees["nature_manifestation"] = "Festival"
    donnees["nom_artiste_evenement"] = "Festival des Arts"
    donnees["artiste_nom"] = ["Floby", "Amzy"]
    donnees["artiste_discipline"] = ["Musique", "Musique urbaine"]

    client.post("/declarations/nouvelle", data=donnees)

    with app.app_context():
        declaration = Declaration.query.filter_by(nom_artiste_evenement="Festival des Arts").first()
        assert declaration is not None
        artistes = ListeArtiste.query.filter_by(declaration_id=declaration.id).all()
        assert len(artistes) == 2
        assert {a.nom_artiste for a in artistes} == {"Floby", "Amzy"}


def test_soumission_champs_manquants_rejetee(app, client):
    """Un champ obligatoire manquant est rejete avec un message d'erreur, et
    aucune declaration n'est creee (RM-011)."""
    creer_organisateur(app, "orga3@example.com")
    connecter(client, "orga3@example.com")
    donnees = dict(DONNEES_BASE, date_evenement=_date_future())
    donnees["email"] = "orga3@example.com"
    donnees.pop("ville")

    reponse = client.post("/declarations/nouvelle", data=donnees)

    assert reponse.status_code == 400
    with app.app_context():
        assert Declaration.query.count() == 0


def test_soumission_date_passee_rejetee(app, client):
    """RM-012 : la date de l'evenement doit etre dans le futur."""
    creer_organisateur(app, "orga4@example.com")
    connecter(client, "orga4@example.com")
    donnees = dict(DONNEES_BASE, date_evenement="2020-01-01T10:00")
    donnees["email"] = "orga4@example.com"

    reponse = client.post("/declarations/nouvelle", data=donnees)

    assert reponse.status_code == 400
    with app.app_context():
        assert Declaration.query.count() == 0


def test_compte_bloque_ne_peut_pas_soumettre(app, client):
    """RM-010 : un compte bloque est redirige sans pouvoir soumettre."""
    creer_organisateur(app, "orga5@example.com", statut_compte="bloque")
    connecter(client, "orga5@example.com")
    donnees = dict(DONNEES_BASE, date_evenement=_date_future())
    donnees["email"] = "orga5@example.com"

    reponse = client.post("/declarations/nouvelle", data=donnees, follow_redirects=False)

    assert reponse.status_code == 302
    with app.app_context():
        assert Declaration.query.count() == 0


def test_soumission_avec_promotion_publique(app, client):
    """Prompt 19 : cocher promouvoir enregistre description, contact et
    optionnellement une affiche."""
    from io import BytesIO

    creer_organisateur(app, "orga6@example.com")
    connecter(client, "orga6@example.com")
    donnees = dict(DONNEES_BASE, date_evenement=_date_future())
    donnees["email"] = "orga6@example.com"
    donnees["promouvoir"] = "on"
    donnees["description_publique"] = "Concert en plein air."
    donnees["contact_public"] = "on"
    donnees["affiche"] = (BytesIO(b"\xff\xd8\xff\xe0fakejpeg"), "affiche.jpg")

    reponse = client.post(
        "/declarations/nouvelle",
        data=donnees,
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert reponse.status_code == 302
    with app.app_context():
        declaration = Declaration.query.filter_by(email="orga6@example.com").first()
        assert declaration is not None
        assert declaration.promouvoir is True
        assert declaration.description_publique == "Concert en plein air."
        assert declaration.contact_public is True
        assert declaration.affiche_path is not None
        assert declaration.affiche_path.startswith("uploads/")


def test_soumission_affiche_extension_invalide_rejetee(app, client):
    """RM-023 : seules les images JPG/PNG sont acceptees comme affiche."""
    from io import BytesIO

    creer_organisateur(app, "orga7@example.com")
    connecter(client, "orga7@example.com")
    donnees = dict(DONNEES_BASE, date_evenement=_date_future())
    donnees["email"] = "orga7@example.com"
    donnees["promouvoir"] = "on"
    donnees["affiche"] = (BytesIO(b"%PDF-1.4"), "doc.pdf")

    reponse = client.post(
        "/declarations/nouvelle",
        data=donnees,
        content_type="multipart/form-data",
    )

    assert reponse.status_code == 400
    with app.app_context():
        assert Declaration.query.count() == 0


def test_fichier_trop_volumineux_affiche_message_clair(app, client):
    """RM-023 : un envoi > 2 Mo renvoie un message francais (pas l'erreur brute)."""
    creer_organisateur(app, "orga8@example.com")
    connecter(client, "orga8@example.com")

    reponse = client.post(
        "/declarations/nouvelle",
        data=b"x" * (2 * 1024 * 1024 + 100),
        content_type="multipart/form-data",
        headers={"Content-Length": str(2 * 1024 * 1024 + 100)},
        follow_redirects=True,
    )

    page = reponse.get_data(as_text=True)
    assert "trop volumineux" in page.lower() or "2 Mo" in page
