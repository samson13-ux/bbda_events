"""Statistiques avancees pour l'espace administrateur (Prompt 17).

Les fonctions de ce module sont purement calculatoires : elles n'ecrivent
jamais en base. Elles sont appelees depuis la route GET /admin/statistiques
et peuvent etre reutilisees dans d'autres vues (ex. exports futurs).
"""

from datetime import datetime

from sqlalchemy import extract, func

from extensions import db
from models import Arriere, Declaration, Organisateur, Quittance, Utilisateur

NOMS_MOIS = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


def get_declarations_par_mois(annee):
    """Nombre de declarations soumises par mois pour une annee donnee.

    :return: dict {nom_mois: nombre}, ex. {'Janvier': 12, 'Fevrier': 8, ...}
    """
    comptes = dict.fromkeys(NOMS_MOIS[1:], 0)
    resultats = (
        db.session.query(extract("month", Declaration.date_soumission), func.count(Declaration.id))
        .filter(extract("year", Declaration.date_soumission) == annee)
        .group_by(extract("month", Declaration.date_soumission))
        .all()
    )
    for numero_mois, nombre in resultats:
        comptes[NOMS_MOIS[int(numero_mois)]] = nombre
    return comptes


def get_redevances_par_mois(annee):
    """Somme des redevances percues (quittances delivrees) par mois pour
    une annee donnee.

    :return: dict {nom_mois: total_fcfa}
    """
    totaux = dict.fromkeys(NOMS_MOIS[1:], 0.0)
    resultats = (
        db.session.query(extract("month", Quittance.date_delivrance), func.coalesce(func.sum(Quittance.somme_totale_chiffres), 0))
        .filter(extract("year", Quittance.date_delivrance) == annee)
        .group_by(extract("month", Quittance.date_delivrance))
        .all()
    )
    for numero_mois, total in resultats:
        totaux[NOMS_MOIS[int(numero_mois)]] = float(total)
    return totaux


def get_repartition_par_type():
    """Repartition des declarations par nature de manifestation.

    :return: dict {type_evenement: nombre}, ex. {'Concert': 45, 'Festival': 12}
    """
    resultats = (
        db.session.query(Declaration.nature_manifestation, func.count(Declaration.id))
        .group_by(Declaration.nature_manifestation)
        .order_by(func.count(Declaration.id).desc())
        .all()
    )
    return {nature: nombre for nature, nombre in resultats}


def get_top_organisateurs(limit=10):
    """Les `limit` organisateurs les plus actifs (nombre de declarations).

    :return: liste de dicts {nom, prenom, nb_declarations, total_paye,
             derniere_declaration}
    """
    organisateurs = Organisateur.query.join(Utilisateur).all()
    classements = []
    for organisateur in organisateurs:
        declarations = organisateur.declarations
        if not declarations:
            continue
        total_paye = sum(paiement.montant_chiffres for d in declarations for paiement in d.paiements)
        derniere = max(declarations, key=lambda d: d.date_soumission)
        classements.append(
            {
                "nom": organisateur.utilisateur.nom,
                "prenom": organisateur.utilisateur.prenom,
                "nb_declarations": len(declarations),
                "total_paye": total_paye,
                "derniere_declaration": derniere.date_soumission,
            }
        )
    classements.sort(key=lambda c: (-c["nb_declarations"], -c["total_paye"]))
    return classements[:limit]


def get_stats_arrieres():
    """Synthese des arrieres en attente.

    :return: dict {total_du, nombre_organisateurs, montant_moyen, plus_ancien}
             `plus_ancien` est la date d'echeance la plus ancienne, ou None.
    """
    arrieres = Arriere.query.filter_by(statut="en_attente").all()
    if not arrieres:
        return {
            "total_du": 0.0,
            "nombre_organisateurs": 0,
            "montant_moyen": 0.0,
            "plus_ancien": None,
        }

    total_du = sum(a.montant_du for a in arrieres)
    organisateurs_distincts = {a.organisateur_id for a in arrieres}
    return {
        "total_du": total_du,
        "nombre_organisateurs": len(organisateurs_distincts),
        "montant_moyen": total_du / len(organisateurs_distincts),
        "plus_ancien": min(a.date_echeance for a in arrieres),
    }


def resume_annee(annee=None):
    """4 chiffres cles pour l'encadre de resume de l'annee en cours."""
    if annee is None:
        annee = datetime.utcnow().year

    declarations_totales = Declaration.query.filter(
        extract("year", Declaration.date_soumission) == annee
    ).count()
    redevances_percues = (
        db.session.query(func.coalesce(func.sum(Quittance.somme_totale_chiffres), 0))
        .filter(extract("year", Quittance.date_delivrance) == annee)
        .scalar()
    )
    arrieres = get_stats_arrieres()
    quittances_delivrees = Quittance.query.filter(extract("year", Quittance.date_delivrance) == annee).count()

    return {
        "annee": annee,
        "declarations_totales": declarations_totales,
        "redevances_percues": float(redevances_percues),
        "arrieres_en_cours": arrieres["total_du"],
        "quittances_delivrees": quittances_delivrees,
    }


def barres_pour_graphique(valeurs_par_cle):
    """Transforme un dict {libelle: valeur} en liste de lignes pretes pour
    le template graphique CSS (pourcentage relatif au max)."""
    maximum = max(valeurs_par_cle.values(), default=0) or 1
    return [
        {
            "libelle": libelle,
            "valeur": valeur,
            "pourcentage": round(float(valeur) / maximum * 100),
        }
        for libelle, valeur in valeurs_par_cle.items()
    ]
