"""Moteur de gestion des arrieres (creation, seuils, blocage, deblocage,
surveillance) — implementation complete des regles RM-060 a RM-084
(Prompt 14 du guide de dev).

Les parametres SEUIL_ARRIERE et DELAI_NOTIFICATION sont configurables par
l'administrateur (table `parametres_systeme`, voir docs/REGLES_METIER.md
§9, seedes par init_db.py) ; des valeurs par defaut sont utilisees si aucune
ligne n'existe encore en base (ex : environnement de test)."""

from datetime import datetime, timedelta

from backend.notifications.email_service import notifier_alerte_surveillance, notifier_rappel_arriere
from extensions import db
from models import AlerteSurveillance, Arriere, Organisateur, ParametresSysteme

SEUIL_ARRIERE_DEFAUT = 1000
DELAI_NOTIFICATION_DEFAUT = 7


def _parametre_numerique(cle, defaut):
    """Lit un parametre configurable en base, ou retourne la valeur par
    defaut si la cle n'existe pas encore (ou contient une valeur invalide)."""
    parametre = ParametresSysteme.query.filter_by(cle=cle).first()
    if parametre is None:
        return defaut
    try:
        return float(parametre.valeur)
    except (TypeError, ValueError):
        return defaut


def seuil_arriere():
    """Montant (FCFA) a partir duquel un arriere devient bloquant (RM-060)."""
    return _parametre_numerique("SEUIL_ARRIERE", SEUIL_ARRIERE_DEFAUT)


def delai_notification():
    """Delai (jours) entre deux rappels d'un meme arriere (RM-070, RM-071)."""
    return int(_parametre_numerique("DELAI_NOTIFICATION", DELAI_NOTIFICATION_DEFAUT))


def verifier_arriere(organisateur_id):
    """FONCTION 1 (RM-060, RM-073) : etat des arrieres actifs d'un
    organisateur.

    :return: dict {montant_total_du, nombre_arrieres, bloquant}
    """
    arrieres_actifs = Arriere.query.filter_by(organisateur_id=organisateur_id, statut="en_attente").all()
    montant_total_du = sum(a.montant_du for a in arrieres_actifs)
    return {
        "montant_total_du": montant_total_du,
        "nombre_arrieres": len(arrieres_actifs),
        "bloquant": montant_total_du >= seuil_arriere(),
    }


def creer_arriere(declaration_id, montant_du):
    """FONCTION 2 (RM-062, RM-063) : cree un arriere lie a une declaration
    (echeance a J+DELAI_NOTIFICATION), puis marque le compte 'en arriere'
    si le total des arrieres actifs franchit le seuil bloquant (RM-073)."""
    from models import Declaration

    declaration = Declaration.query.get(declaration_id)
    arriere = Arriere(
        organisateur_id=declaration.organisateur_id,
        declaration_id=declaration_id,
        montant_du=montant_du,
        date_echeance=datetime.utcnow() + timedelta(days=delai_notification()),
    )
    db.session.add(arriere)
    db.session.flush()

    if verifier_arriere(declaration.organisateur_id)["bloquant"]:
        marquer_compte_arriere(declaration.organisateur_id)

    return arriere


def verifier_et_envoyer_rappels():
    """FONCTION 3 (RM-070 a RM-072) : envoie un rappel par email pour chaque
    arriere en retard n'ayant pas ete relance depuis au moins
    DELAI_NOTIFICATION jours.

    :return: nombre de rappels effectivement envoyes.
    """
    maintenant = datetime.utcnow()
    delai = timedelta(days=delai_notification())
    arrieres_en_retard = Arriere.query.filter(
        Arriere.statut == "en_attente", Arriere.date_echeance < maintenant
    ).all()

    nombre_envoyes = 0
    for arriere in arrieres_en_retard:
        deja_relance_recemment = (
            arriere.derniere_notification is not None and (maintenant - arriere.derniere_notification) < delai
        )
        if deja_relance_recemment:
            continue
        notifier_rappel_arriere(arriere)
        arriere.derniere_notification = maintenant
        nombre_envoyes += 1

    db.session.commit()
    return nombre_envoyes


def marquer_compte_arriere(organisateur_id):
    """FONCTION 4 (RM-073) : signale automatiquement un compte dont
    l'arriere franchit le seuil bloquant."""
    organisateur = Organisateur.query.get(organisateur_id)
    organisateur.statut_compte = "arriere"


def bloquer_compte(organisateur_id):
    """FONCTION 5 (RM-075) : gel manuel d'un compte par un agent, apres
    relances restees sans effet."""
    organisateur = Organisateur.query.get(organisateur_id)
    organisateur.statut_compte = "bloque"


def debloquer_compte(organisateur_id):
    """FONCTION 6 (RM-075, RM-076) : reactive un compte et solde tous ses
    arrieres en attente."""
    organisateur = Organisateur.query.get(organisateur_id)
    organisateur.statut_compte = "actif"
    maintenant = datetime.utcnow()
    for arriere in Arriere.query.filter_by(organisateur_id=organisateur_id, statut="en_attente").all():
        arriere.statut = "regle"
        arriere.date_reglement = maintenant


def marquer_surveillance(organisateur_id, agent_id, commentaire=""):
    """FONCTION 7 (RM-080) : place un compte sous surveillance (cas :
    organisateur introuvable)."""
    organisateur = Organisateur.query.get(organisateur_id)
    organisateur.statut_compte = "surveillance"
    db.session.add(
        AlerteSurveillance(organisateur_id=organisateur_id, marque_par=agent_id, commentaire=commentaire or None)
    )


def lever_surveillance(organisateur_id, agent_id):
    """FONCTION 8 (RM-084) : leve la surveillance d'un compte et solde ses
    alertes encore non traitees."""
    organisateur = Organisateur.query.get(organisateur_id)
    organisateur.statut_compte = "actif"
    maintenant = datetime.utcnow()
    for alerte in AlerteSurveillance.query.filter_by(organisateur_id=organisateur_id, traitee=False).all():
        alerte.traitee = True
        alerte.date_traitement = maintenant
        alerte.traite_par = agent_id


def verifier_connexion_surveillance(organisateur_id):
    """FONCTION 9 (RM-081) : a appeler a chaque connexion d'un organisateur.
    Si son compte est sous surveillance, cree une nouvelle alerte et
    notifie tous les agents/administrateurs actifs.

    :return: True si le compte est sous surveillance, False sinon.
    """
    organisateur = Organisateur.query.get(organisateur_id)
    if organisateur is None or organisateur.statut_compte != "surveillance":
        return False

    db.session.add(AlerteSurveillance(organisateur_id=organisateur_id))
    notifier_alerte_surveillance(organisateur)
    return True


def integrer_arrieres_dans_quittance(quittance):
    """FONCTION 10 (RM-050 a RM-054) : reporte le montant des arrieres
    actifs de l'organisateur sur la quittance delivree."""
    etat = verifier_arriere(quittance.declaration.organisateur_id)
    quittance.droit_arriere = etat["montant_total_du"]
    quittance.droit_exigible = (quittance.droit_annuel or 0) + quittance.droit_arriere
