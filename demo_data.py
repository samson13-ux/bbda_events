"""Donnees de demonstration pour la soutenance.

Insere un jeu realiste (organisateurs burkinabe, declarations aux statuts
varies, evenements publics, arrieres, surveillance) sans ecraser une base
deja peuplee — sauf avec --reset.

Usage :
    python demo_data.py           # seed si la base est vide
    python demo_data.py --reset   # recreate tables + seed complet
"""

import os
import sys
from datetime import datetime, timedelta

from app import create_app
from extensions import db
from init_db import MOT_DE_PASSE_DEMO, hacher_mot_de_passe
from models import (
    AlerteSurveillance,
    Arriere,
    Declaration,
    EvaluationAgent,
    ListeArtiste,
    MessageContact,
    Notification,
    Organisateur,
    Paiement,
    ParametresSysteme,
    Quittance,
    Utilisateur,
)


def _creer_affiche_placeholder(app, nom_fichier):
    """Cree une petite image PNG unie comme affiche de demonstration."""
    png_minimal = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
        b"\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    dossier = app.config["UPLOAD_FOLDER"]
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)
    with open(chemin, "wb") as fichier:
        fichier.write(png_minimal)
    return f"uploads/{nom_fichier}"


def seed_soutenance(app):
    """Jeu etendu pour la soutenance : 5 organisateurs, 12 declarations,
    2 evenements publics avec affiche, arrieres et surveillance."""
    mdp = hacher_mot_de_passe(MOT_DE_PASSE_DEMO)

    admin = Utilisateur(nom="Traore", prenom="Awa", email="admin@bbda.bf", mot_de_passe=mdp, role="admin")
    agent1 = Utilisateur(nom="Kabore", prenom="Issa", email="agent1@bbda.bf", mot_de_passe=mdp, role="agent")
    agent2 = Utilisateur(nom="Sawadogo", prenom="Fatou", email="agent2@bbda.bf", mot_de_passe=mdp, role="agent")
    db.session.add_all([admin, agent1, agent2])
    db.session.flush()

    profils = [
        ("Ouedraogo", "Boubacar", "orga1@example.com", "Promoteur culturel", "70000001", "actif"),
        ("Zongo", "Aminata", "orga2@example.com", "Directrice de salle", "70000002", "actif"),
        ("Sanou", "Paul", "orga3@example.com", "Organisateur independant", "70000003", "surveillance"),
        ("Kabore", "Mariama", "orga4@example.com", "Association culturelle", "70000004", "arriere"),
        ("Ilboudo", "Seydou", "orga5@example.com", "Promoteur evenementiel", "70000005", "actif"),
    ]
    organisateurs = []
    for nom, prenom, email, qualite, tel, statut in profils:
        utilisateur = Utilisateur(nom=nom, prenom=prenom, email=email, mot_de_passe=mdp, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id, qualite=qualite, telephone=tel, statut_compte=statut
        )
        db.session.add(organisateur)
        db.session.flush()
        organisateurs.append(organisateur)

    db.session.add_all(
        [
            ParametresSysteme(cle="SEUIL_ARRIERE", valeur="1000", description="Seuil de blocage (FCFA)"),
            ParametresSysteme(cle="DELAI_NOTIFICATION", valeur="7", description="Delai rappel (jours)"),
        ]
    )

    affiche1 = _creer_affiche_placeholder(app, "demo_roog.png")
    affiche2 = _creer_affiche_placeholder(app, "demo_festival.png")
    maintenant = datetime.utcnow()

    declarations_specs = [
        (0, "nouvelle", "Concert Balafon", False, None, None),
        (0, "en_evaluation", "Spectacle Conte", False, None, None),
        (1, "montant_fixe", "Soiree Jazz Ouaga", True, None, "Jazz live au centre-ville"),
        (1, "paiement_en_attente", "Gala Solidarite", False, None, None),
        (2, "payee", "Exposition Art contemporain", False, None, None),
        (2, "quittance_delivree", "Concert Roog", True, affiche1, "Concert live a la Maison du Peuple"),
        (4, "quittance_delivree", "Festival des Arts", True, affiche2, "Festival pluridisciplinaire"),
        (3, "quittance_delivree", "Theatre populaire", False, None, None),
        (4, "nouvelle", "Soiree Hip-Hop", True, None, "Battle et concerts"),
        (0, "montant_fixe", "Concert Gospel", False, None, None),
        (1, "nouvelle", "Projection documentaire", False, None, None),
        (2, "en_evaluation", "Danse traditionnelle", False, None, None),
    ]

    for index, (orga_idx, statut, nom, promouvoir, affiche, description) in enumerate(declarations_specs):
        organisateur = organisateurs[orga_idx]
        declaration = Declaration(
            organisateur_id=organisateur.id,
            nom_demandeur=organisateur.utilisateur.nom,
            prenom_demandeur=organisateur.utilisateur.prenom,
            qualite_demandeur=organisateur.qualite,
            telephone=organisateur.telephone,
            email=organisateur.utilisateur.email,
            nature_manifestation="Festival" if "Festival" in nom else "Concert",
            nom_artiste_evenement=nom,
            nom_salle="Maison du Peuple" if index % 2 == 0 else "Salle des fetes de Ouaga",
            adresse="Avenue Kwame Nkrumah",
            ville="Ouagadougou" if index % 3 else "Bobo-Dioulasso",
            date_evenement=maintenant + timedelta(days=10 + index * 3),
            duree_heures=3,
            capacite_accueil=300 + index * 50,
            entree_payante=True,
            nature_diffusion="Musique vivante",
            promouvoir=promouvoir,
            description_publique=description,
            affiche_path=affiche,
            contact_public=promouvoir,
            statut=statut,
        )
        db.session.add(declaration)
        db.session.flush()

        if nom == "Festival des Arts":
            db.session.add_all(
                [
                    ListeArtiste(declaration_id=declaration.id, nom_artiste="Floby", discipline="Musique"),
                    ListeArtiste(declaration_id=declaration.id, nom_artiste="Amzy", discipline="Musique urbaine"),
                ]
            )

        if statut in ("montant_fixe", "paiement_en_attente", "payee", "quittance_delivree"):
            db.session.add(
                EvaluationAgent(
                    declaration_id=declaration.id,
                    agent_id=agent1.id,
                    tarif=5000,
                    redevance=15000 + index * 1000,
                    commentaire="Evaluation de demonstration",
                )
            )

        if statut in ("payee", "quittance_delivree"):
            db.session.add(
                Paiement(
                    declaration_id=declaration.id,
                    mode_paiement="especes",
                    montant_chiffres=20000 + index * 1000,
                    montant_lettres="Montant de demonstration",
                    type_paiement="integral",
                    solde_apres=0,
                    confirme_par=agent1.id,
                )
            )

        if statut == "quittance_delivree":
            montant = 20000 + index * 1000
            db.session.add(
                Quittance(
                    declaration_id=declaration.id,
                    numero_quittance=f"{index + 1:07d}",
                    droit_exigible=montant,
                    somme_totale_chiffres=montant,
                    somme_totale_lettres="Montant de demonstration",
                    agent_id=agent1.id,
                )
            )

    orga4 = organisateurs[3]
    declaration_arriere = Declaration.query.filter_by(organisateur_id=orga4.id).first()
    db.session.add(
        Arriere(
            organisateur_id=orga4.id,
            declaration_id=declaration_arriere.id if declaration_arriere else None,
            montant_du=25000,
            date_echeance=maintenant - timedelta(days=5),
            statut="en_attente",
        )
    )
    db.session.add(
        Arriere(
            organisateur_id=orga4.id,
            declaration_id=None,
            montant_du=5000,
            date_echeance=maintenant + timedelta(days=2),
            statut="en_attente",
        )
    )

    orga3 = organisateurs[2]
    db.session.add(
        AlerteSurveillance(
            organisateur_id=orga3.id,
            marque_par=agent1.id,
            commentaire="Reconnexions repetees apres rappels d'arriere (jeu de demo)",
            traitee=False,
        )
    )
    db.session.add(
        MessageContact(
            nom="Jean Kabore",
            email="visiteur@example.com",
            sujet="Demarche de declaration",
            message="Bonjour, quelles sont les etapes pour declarer un concert ?",
        )
    )
    db.session.add(
        Notification(
            destinataire_id=organisateurs[0].utilisateur_id,
            type_notification="confirmation_soumission",
            sujet="Confirmation de votre declaration",
            message="Votre declaration a bien ete recue par le BBDA.",
            statut="envoyee",
        )
    )

    db.session.commit()
    publics = Declaration.query.filter_by(promouvoir=True, statut="quittance_delivree").count()
    print("Donnees de soutenance inserees.")
    print("  - 1 admin, 2 agents, 5 organisateurs")
    print(f"  - 12 declarations dont {publics} evenements publics")
    print(f"  - Mot de passe commun : {MOT_DE_PASSE_DEMO}")
    print("  - Comptes : admin@bbda.bf, agent1@bbda.bf, orga1@example.com ...")


def main():
    """Point d'entree : seed soutenance, avec reset optionnel."""
    reset = "--reset" in sys.argv
    app = create_app()
    with app.app_context():
        if reset:
            print("Reset : suppression puis recreation des tables...")
            db.drop_all()
            db.create_all()
            seed_soutenance(app)
            return

        db.create_all()
        if Utilisateur.query.first() is not None:
            print("La base contient deja des donnees.")
            print("  - Pour la demo soutenance : python demo_data.py --reset")
            print("  - Pour une base neuve (1 admin) : python init_db.py --vide")
            return

        seed_soutenance(app)


if __name__ == "__main__":
    main()
