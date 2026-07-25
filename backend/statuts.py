"""Constantes partagees entre les blueprints declarations et agent.

Evite de dupliquer la correspondance statut -> (classe CSS, libelle) utilisee
a la fois cote organisateur (tableau de bord, detail) et cote agent
(tableau de bord, traitement).
"""

# (classe CSS du badge, libelle affiche) pour chaque statut de Declaration.statut.
STATUTS_AFFICHAGE = {
    "nouvelle": ("nouvelle", "Nouvelle"),
    "en_evaluation": ("en-evaluation", "En évaluation"),
    "montant_fixe": ("montant-fixe", "Montant fixé"),
    "paiement_en_attente": ("paiement-attente", "En attente de paiement"),
    "payee": ("payee", "Payée"),
    "quittance_delivree": ("quittance", "Quittance disponible"),
    "en_attente": ("attente-agent", "En attente (agent)"),
}

# Statuts consideres "en cours de traitement" par un agent (ni nouvelle, ni clos).
STATUTS_EN_COURS_AGENT = ("en_evaluation", "montant_fixe", "paiement_en_attente", "en_attente")
