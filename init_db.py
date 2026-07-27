"""Initialise la base de donnees et insere un jeu de donnees de demonstration.

Cree les 12 tables (si absentes) puis seed des comptes, declarations, paiements,
quittances, arrieres et notifications couvrant tout le cycle de vie metier
decrit dans docs/REGLES_METIER.md — utile pour developper les tableaux de bord
sans attendre l'implementation complete des formulaires, et pour la demo de
soutenance.

Usage :
    python init_db.py            # cree les tables manquantes, seed si la base
                                  # est vide (ne duplique jamais les donnees)
    python init_db.py --reset    # supprime puis recree tout, avant de seeder
    python init_db.py --vide     # base neuve : tables + parametres + 1 admin
                                  # (aucune donnee de demo)
"""

import os
import sys
from datetime import datetime, timedelta

import bcrypt

from app import create_app
from extensions import db
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

MOT_DE_PASSE_DEMO = "password123"
EMAIL_ADMIN_BOOTSTRAP = "admin@bbda.bf"
LONGUEUR_MIN_ADMIN_PASSWORD = 10


def hacher_mot_de_passe(mot_de_passe):
    """Hache un mot de passe en clair avec bcrypt (AI_RULES.md §5)."""
    sel = bcrypt.gensalt()
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), sel).decode("utf-8")


def _est_environnement_production():
    return os.environ.get("FLASK_ENV") == "production" or bool(os.environ.get("RENDER"))


def mot_de_passe_bootstrap_admin():
    """Mot de passe admin : ADMIN_PASSWORD (env) ou demo locale uniquement."""
    depuis_env = (os.environ.get("ADMIN_PASSWORD") or "").strip()
    if depuis_env:
        if len(depuis_env) < LONGUEUR_MIN_ADMIN_PASSWORD:
            raise ValueError(
                f"ADMIN_PASSWORD trop court (minimum {LONGUEUR_MIN_ADMIN_PASSWORD} caractères)."
            )
        return depuis_env
    if _est_environnement_production():
        raise ValueError(
            "En production, ADMIN_PASSWORD est obligatoire pour créer/mettre à jour "
            "l'admin (minimum 10 caractères). Définis-le dans les variables Render."
        )
    return MOT_DE_PASSE_DEMO


def mettre_a_jour_mot_de_passe_admin():
    """Met a jour le mot de passe de admin@bbda.bf depuis ADMIN_PASSWORD."""
    nouveau = (os.environ.get("ADMIN_PASSWORD") or "").strip()
    if len(nouveau) < LONGUEUR_MIN_ADMIN_PASSWORD:
        raise ValueError(
            f"ADMIN_PASSWORD requis (minimum {LONGUEUR_MIN_ADMIN_PASSWORD} caractères)."
        )
    admin = Utilisateur.query.filter_by(email=EMAIL_ADMIN_BOOTSTRAP, role="admin").first()
    if admin is None:
        raise ValueError(f"Aucun admin trouvé pour {EMAIL_ADMIN_BOOTSTRAP}.")
    admin.mot_de_passe = hacher_mot_de_passe(nouveau)
    db.session.commit()
    print(f"Mot de passe mis à jour pour {EMAIL_ADMIN_BOOTSTRAP}.")


def creer_parametres_systeme():
    """Seed les parametres configurables par l'admin (REGLES_METIER.md §9)."""
    db.session.add_all(
        [
            ParametresSysteme(
                cle="SEUIL_ARRIERE",
                valeur="1000",
                description="Montant d'arriere (FCFA) a partir duquel un compte est bloque (RM-060, RM-073).",
            ),
            ParametresSysteme(
                cle="DELAI_NOTIFICATION",
                valeur="7",
                description="Delai en jours apres echeance avant envoi du rappel d'arriere (RM-070, RM-071).",
            ),
        ]
    )


def creer_utilisateurs():
    """Cree les comptes de demonstration : 1 admin, 2 agents, 4 organisateurs.

    :return: tuple (admin, liste_agents, liste_organisateurs)
    """
    mdp = hacher_mot_de_passe(MOT_DE_PASSE_DEMO)

    admin = Utilisateur(nom="Traore", prenom="Awa", email="admin@bbda.bf", mot_de_passe=mdp, role="admin")
    agent1 = Utilisateur(nom="Kabore", prenom="Issa", email="agent1@bbda.bf", mot_de_passe=mdp, role="agent")
    agent2 = Utilisateur(nom="Sawadogo", prenom="Fatou", email="agent2@bbda.bf", mot_de_passe=mdp, role="agent")
    db.session.add_all([admin, agent1, agent2])
    db.session.flush()  # obtenir les id avant de creer les profils organisateur

    donnees_organisateurs = [
        ("Ouedraogo", "Boubacar", "orga1@example.com", "Promoteur culturel", "70000001", "actif"),
        ("Zongo", "Aminata", "orga2@example.com", "Directrice de salle des fetes", "70000002", "actif"),
        ("Sanou", "Paul", "orga3@example.com", "Organisateur independant", "70000003", "surveillance"),
        ("Compaore", "Rasmata", "orga4@example.com", "Association culturelle", "70000004", "bloque"),
    ]
    organisateurs = []
    for nom, prenom, email, qualite, telephone, statut_compte in donnees_organisateurs:
        utilisateur = Utilisateur(nom=nom, prenom=prenom, email=email, mot_de_passe=mdp, role="organisateur")
        db.session.add(utilisateur)
        db.session.flush()
        organisateur = Organisateur(
            utilisateur_id=utilisateur.id,
            qualite=qualite,
            telephone=telephone,
            statut_compte=statut_compte,
        )
        db.session.add(organisateur)
        db.session.flush()
        organisateurs.append(organisateur)

    return admin, [agent1, agent2], organisateurs


def _dans(jours):
    """Retourne une date future de `jours` jours a partir d'aujourd'hui."""
    return datetime.utcnow() + timedelta(days=jours)


def _il_y_a(jours):
    """Retourne une date passee de `jours` jours avant aujourd'hui."""
    return datetime.utcnow() - timedelta(days=jours)


def creer_declaration(organisateur, statut, **champs):
    """Cree une declaration avec des valeurs par defaut realistes, surchargables
    via `champs` (ex. statut, promouvoir...)."""
    valeurs = dict(
        organisateur_id=organisateur.id,
        nom_demandeur=organisateur.utilisateur.nom,
        prenom_demandeur=organisateur.utilisateur.prenom,
        qualite_demandeur=organisateur.qualite,
        telephone=organisateur.telephone,
        email=organisateur.utilisateur.email,
        nature_manifestation="Concert",
        nom_artiste_evenement="Artiste de demonstration",
        nom_salle="Salle des fetes de Ouagadougou",
        adresse="Avenue Kwame Nkrumah",
        ville="Ouagadougou",
        date_evenement=_dans(30),
        duree_heures=3.5,
        capacite_accueil=500,
        entree_payante=True,
        nature_diffusion="Diffusion live avec sonorisation",
        statut=statut,
    )
    valeurs.update(champs)
    declaration = Declaration(**valeurs)
    db.session.add(declaration)
    db.session.flush()
    return declaration


def creer_declarations_et_flux(agents, organisateurs):
    """Cree 7 declarations couvrant tout le cycle de vie metier (statuts de
    models.Declaration.statut), avec artistes, evaluations, paiements,
    quittances, arrieres, alertes et notifications associes."""
    agent1, agent2 = agents
    orga1, orga2, orga3, orga4 = organisateurs

    # 1. "nouvelle" : vient d'etre soumise, pas encore vue par un agent.
    decl_nouvelle = creer_declaration(
        orga1,
        "nouvelle",
        nature_manifestation="Soiree culturelle",
        nom_artiste_evenement="Floby",
        autres_details="Premiere edition, sponsor local recherche.",
    )
    db.session.add(ListeArtiste(declaration_id=decl_nouvelle.id, nom_artiste="Floby", discipline="Musique"))

    # 2. "en_evaluation" : un agent a commence l'examen, montant pas encore fixe.
    decl_evaluation = creer_declaration(
        orga1,
        "en_evaluation",
        nature_manifestation="Concert",
        nom_artiste_evenement="Amzy",
        capacite_accueil=800,
    )
    db.session.add(ListeArtiste(declaration_id=decl_evaluation.id, nom_artiste="Amzy", discipline="Musique urbaine"))

    # 3. "montant_fixe" : agent a fixe Tarif + Redevance (RM-030 a RM-033), en attente de paiement.
    decl_montant_fixe = creer_declaration(
        orga2,
        "montant_fixe",
        nature_manifestation="Spectacle de danse",
        nom_artiste_evenement="Compagnie Nakotoo",
        capacite_accueil=300,
    )
    db.session.add(
        ListeArtiste(declaration_id=decl_montant_fixe.id, nom_artiste="Compagnie Nakotoo", discipline="Danse")
    )
    db.session.add(
        EvaluationAgent(
            declaration_id=decl_montant_fixe.id,
            agent_id=agent1.id,
            tarif=15000,
            redevance=10000,
            commentaire="Tarif standard categorie salle moyenne + redevance affluence estimee.",
        )
    )

    # 4. "paiement_en_attente" : paiement partiel recu -> arriere cree automatiquement (RM-044).
    decl_partiel = creer_declaration(
        orga2,
        "paiement_en_attente",
        nature_manifestation="Concert",
        nom_artiste_evenement="Alif Naaba",
        capacite_accueil=1000,
    )
    db.session.add(ListeArtiste(declaration_id=decl_partiel.id, nom_artiste="Alif Naaba", discipline="Musique"))
    evaluation_partiel = EvaluationAgent(
        declaration_id=decl_partiel.id, agent_id=agent1.id, tarif=20000, redevance=15000
    )
    db.session.add(evaluation_partiel)
    db.session.flush()
    montant_total_partiel = evaluation_partiel.montant_total  # 35000
    premier_versement = 20000
    solde_restant = montant_total_partiel - premier_versement
    db.session.add(
        Paiement(
            declaration_id=decl_partiel.id,
            mode_paiement="especes",
            montant_chiffres=premier_versement,
            montant_lettres="Vingt mille francs CFA (20 000 FCFA)",
            type_paiement="partiel",
            solde_apres=solde_restant,
            confirme_par=agent1.id,
        )
    )
    db.session.add(
        Arriere(
            organisateur_id=orga2.id,
            declaration_id=decl_partiel.id,
            montant_du=solde_restant,
            date_echeance=_dans(7),  # J+7 apres fixation du montant (RM-063)
            statut="en_attente",
        )
    )

    # 5. "payee" : paiement integral recu, solde a zero, quittance pas encore generee (etat transitoire).
    decl_payee = creer_declaration(
        orga3,
        "payee",
        nature_manifestation="Projection cinema",
        nom_artiste_evenement="Collectif Cine Faso",
        capacite_accueil=200,
        entree_payante=False,
    )
    db.session.add(
        ListeArtiste(declaration_id=decl_payee.id, nom_artiste="Collectif Cine Faso", discipline="Cinema")
    )
    evaluation_payee = EvaluationAgent(declaration_id=decl_payee.id, agent_id=agent2.id, tarif=10000, redevance=5000)
    db.session.add(evaluation_payee)
    db.session.flush()
    db.session.add(
        Paiement(
            declaration_id=decl_payee.id,
            mode_paiement="orange_money",
            montant_chiffres=evaluation_payee.montant_total,
            montant_lettres="Quinze mille francs CFA (15 000 FCFA)",
            type_paiement="integral",
            solde_apres=0,
            confirme_par=agent2.id,
        )
    )

    # 6. "quittance_delivree" : cycle complet, evenement promu sur la face publique (RM-090).
    decl_quittance = creer_declaration(
        orga3,
        "quittance_delivree",
        nature_manifestation="Concert",
        nom_artiste_evenement="Mamane Barka",
        capacite_accueil=1200,
        promouvoir=True,
        description_publique="Une soiree exceptionnelle avec Mamane Barka, ouverte a tous.",
        contact_public=True,
    )
    db.session.add(
        ListeArtiste(declaration_id=decl_quittance.id, nom_artiste="Mamane Barka", discipline="Musique traditionnelle")
    )
    evaluation_quittance = EvaluationAgent(
        declaration_id=decl_quittance.id, agent_id=agent1.id, tarif=25000, redevance=20000
    )
    db.session.add(evaluation_quittance)
    db.session.flush()
    db.session.add(
        Paiement(
            declaration_id=decl_quittance.id,
            mode_paiement="cheque",
            numero_cheque="CHQ-001234",
            montant_chiffres=evaluation_quittance.montant_total,
            montant_lettres="Quarante-cinq mille francs CFA (45 000 FCFA)",
            type_paiement="integral",
            solde_apres=0,
            confirme_par=agent1.id,
        )
    )
    db.session.add(
        Quittance(
            declaration_id=decl_quittance.id,
            numero_quittance="0000001",
            droit_annuel=0,
            droit_arriere=0,
            droit_exigible=evaluation_quittance.montant_total,
            droits_type="Redevance evenement occasionnel",
            droits_montant=evaluation_quittance.montant_total,
            etiquettes_nombre=0,
            etiquettes_montant=0,
            penalites_type=None,
            penalites_montant=0,
            somme_totale_chiffres=evaluation_quittance.montant_total,
            somme_totale_lettres="Quarante-cinq mille francs CFA (45 000 FCFA)",
            agent_id=agent1.id,
        )
    )

    # 7. "en_attente" : agent met en attente avec commentaire obligatoire (RM-034), organisateur bloque.
    decl_en_attente = creer_declaration(
        orga4,
        "en_attente",
        nature_manifestation="Festival",
        nom_artiste_evenement="Multiples artistes",
        capacite_accueil=2000,
    )
    db.session.add(
        ListeArtiste(declaration_id=decl_en_attente.id, nom_artiste="Multiples artistes", discipline="Festival")
    )

    # Arriere bloquant sur orga4 (RM-073 : arriere >= seuil -> compte bloque).
    db.session.add(
        Arriere(
            organisateur_id=orga4.id,
            declaration_id=decl_en_attente.id,
            montant_du=12000,
            date_echeance=_il_y_a(3),
            statut="en_attente",
            derniere_notification=_il_y_a(1),
        )
    )

    # Alerte de surveillance non traitee sur orga3 (RM-080, RM-081).
    db.session.add(
        AlerteSurveillance(
            organisateur_id=orga3.id,
            marque_par=agent2.id,
            traitee=False,
            commentaire="Organisateur injoignable au telephone lors de la derniere relance.",
        )
    )

    return {
        "nouvelle": decl_nouvelle,
        "en_evaluation": decl_evaluation,
        "montant_fixe": decl_montant_fixe,
        "paiement_en_attente": decl_partiel,
        "payee": decl_payee,
        "quittance_delivree": decl_quittance,
        "en_attente": decl_en_attente,
    }


def creer_notifications(agents, organisateurs, declarations):
    """Cree quelques notifications-email deja journalisees, dont un echec
    (RM-100, RM-101)."""
    orga1, orga2, _orga3, orga4 = organisateurs

    db.session.add_all(
        [
            Notification(
                destinataire_id=orga1.utilisateur_id,
                type_notification="confirmation_soumission",
                sujet="Confirmation de votre declaration",
                message="Votre declaration a bien ete recue par le BBDA et sera examinee prochainement.",
                statut="envoyee",
            ),
            Notification(
                destinataire_id=orga2.utilisateur_id,
                type_notification="montant_fixe",
                sujet="Montant a payer pour votre evenement",
                message="Le montant de votre redevance a ete fixe. Merci de vous presenter au BBDA pour le reglement.",
                statut="envoyee",
            ),
            Notification(
                destinataire_id=declarations["quittance_delivree"].organisateur.utilisateur_id,
                type_notification="quittance_disponible",
                sujet="Votre quittance est disponible",
                message="Votre quittance est desormais disponible au telechargement depuis votre espace personnel.",
                statut="envoyee",
            ),
            Notification(
                destinataire_id=orga4.utilisateur_id,
                type_notification="rappel_arriere",
                sujet="Rappel : arriere non regle",
                message="Vous avez un arriere non regle. Merci de vous acquitter du montant du au plus vite.",
                statut="echouee",
            ),
        ]
    )


def creer_message_contact():
    """Cree un message de demonstration pour le formulaire de contact public."""
    db.session.add(
        MessageContact(
            nom="Jean Dupont",
            email="visiteur@example.com",
            sujet="Question sur la declaration d'un evenement",
            message="Bonjour, je souhaite organiser un concert le mois prochain, quelles sont les demarches ?",
        )
    )


def seed_base_vide():
    """Base neuve pour reprise manuelle des tests : parametres systeme +
    un seul compte admin (necessaire pour creer ensuite agents et orga).
    Aucune declaration, aucun organisateur, aucun evenement public."""
    creer_parametres_systeme()
    mot_de_passe = mot_de_passe_bootstrap_admin()
    mdp = hacher_mot_de_passe(mot_de_passe)
    admin = Utilisateur(
        nom="Traore",
        prenom="Awa",
        email=EMAIL_ADMIN_BOOTSTRAP,
        mot_de_passe=mdp,
        role="admin",
    )
    db.session.add(admin)
    db.session.commit()
    print("Base videe et reinitialisee (etat neuf).")
    print("  - Tables recrees")
    print("  - Parametres systeme (SEUIL_ARRIERE, DELAI_NOTIFICATION)")
    if mot_de_passe == MOT_DE_PASSE_DEMO:
        print(f"  - 1 admin bootstrap : {EMAIL_ADMIN_BOOTSTRAP} / {MOT_DE_PASSE_DEMO} (dev seulement)")
    else:
        print(f"  - 1 admin bootstrap : {EMAIL_ADMIN_BOOTSTRAP} / (mot de passe ADMIN_PASSWORD)")
    print("  - Aucun agent, organisateur, declaration ni evenement")
    print("Tu peux maintenant creer agents (espace admin) et organisateurs")
    print("(inscription publique) pour retester le parcours complet.")


def seed():
    """Insere le jeu de donnees complet dans une session unique."""
    creer_parametres_systeme()
    admin, agents, organisateurs = creer_utilisateurs()
    declarations = creer_declarations_et_flux(agents, organisateurs)
    creer_notifications(agents, organisateurs, declarations)
    creer_message_contact()
    db.session.commit()

    print("Jeu de donnees de demonstration insere avec succes.")
    print(f"  - 1 admin, {len(agents)} agents, {len(organisateurs)} organisateurs")
    print(f"  - {len(declarations)} declarations (une par statut du cycle de vie)")
    print(f"  - mot de passe de tous les comptes de demo : {MOT_DE_PASSE_DEMO}")
    print(f"  - admin : {admin.email}")


def _nettoyer_fichiers_generes(app):
    """Supprime les affiches uploadees et les PDF de quittance generes
    (garde les .gitkeep)."""
    import glob
    import os

    for dossier_cle in ("UPLOAD_FOLDER", "QUITTANCE_FOLDER"):
        dossier = app.config.get(dossier_cle)
        if not dossier or not os.path.isdir(dossier):
            continue
        for chemin in glob.glob(os.path.join(dossier, "*")):
            if os.path.isfile(chemin) and not chemin.endswith(".gitkeep"):
                os.remove(chemin)


def main():
    """Point d'entree du script : cree les tables, seed si necessaire."""
    reset = "--reset" in sys.argv
    vide = "--vide" in sys.argv
    # --bootstrap : pour Render (sans Shell payant). Cree les tables + 1 admin
    # si la base est vide. Ne supprime jamais les donnees existantes.
    bootstrap = "--bootstrap" in sys.argv
    set_admin_password = "--set-admin-password" in sys.argv
    # En bootstrap Render, preferer production pour valider SECRET_KEY.
    env_app = None
    if bootstrap or set_admin_password:
        if os.environ.get("RENDER") or os.environ.get("FLASK_ENV") == "production":
            env_app = "production"
    app = create_app(env_app)

    with app.app_context():
        if set_admin_password:
            try:
                mettre_a_jour_mot_de_passe_admin()
            except ValueError as erreur:
                raise SystemExit(str(erreur)) from erreur
            return

        if bootstrap:
            # One-shot Render : vider toute la base et garder seulement admin + parametres.
            if os.environ.get("FORCE_BASE_VIDE") == "1":
                print(
                    "FORCE_BASE_VIDE=1 : suppression de toutes les donnees, "
                    "puis base neuve (admin + parametres seulement)..."
                )
                db.drop_all()
                _nettoyer_fichiers_generes(app)
                db.create_all()
                try:
                    seed_base_vide()
                except ValueError as erreur:
                    raise SystemExit(str(erreur)) from erreur
                print(
                    "FORCE_BASE_VIDE appliqué. "
                    "IMPORTANT : retire FORCE_BASE_VIDE de Render après ce déploiement."
                )
                try:
                    db.session.remove()
                    db.engine.dispose()
                except Exception:
                    pass
                return

            db.create_all()
            if Utilisateur.query.first() is None:
                print("Bootstrap : base vide, creation admin uniquement...")
                try:
                    seed_base_vide()
                except ValueError as erreur:
                    raise SystemExit(str(erreur)) from erreur
            else:
                print("Bootstrap : base deja initialisee, rien a faire.")
            # Option one-shot Render (sans Shell) : forcer le nouveau MDP admin.
            if os.environ.get("FORCE_ADMIN_PASSWORD_RESET") == "1":
                try:
                    mettre_a_jour_mot_de_passe_admin()
                    print(
                        "FORCE_ADMIN_PASSWORD_RESET appliqué. "
                        "Retire cette variable de Render après le déploiement."
                    )
                except ValueError as erreur:
                    raise SystemExit(str(erreur)) from erreur
            return

        if reset or vide:
            mode = "vide (sans donnees de demo)" if vide else "reset + seed complet"
            print(f"Option --{'vide' if vide else 'reset'} : suppression puis recreation ({mode})...")
            db.drop_all()
            _nettoyer_fichiers_generes(app)

        db.create_all()

        if vide:
            seed_base_vide()
            return

        if not reset and Utilisateur.query.first() is not None:
            print("La base contient deja des donnees : seed ignore (utilisez --reset ou --vide).")
            return

        seed()


if __name__ == "__main__":
    main()
