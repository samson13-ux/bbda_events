# Glossaire et références

## Glossaire métier

| Terme | Définition |
|---|---|
| **BBDA** | Bureau Burkinabè du Droit d'Auteur — institution publique de gestion collective des droits d'auteur au Burkina Faso |
| **DEPAJ** | Direction de l'Exploitation, de la Perception et des Affaires Juridiques — direction du BBDA qui traite les déclarations d'événements occasionnels |
| **Événement occasionnel** | Manifestation culturelle ponctuelle (concert, festival, spectacle, gala...), par opposition à l'exploitation permanente d'œuvres (radio, TV, maquis) |
| **Déclaration** | Formulaire rempli par l'organisateur pour signaler un événement au BBDA — point de départ du processus, remplace la "demande d'autorisation" utilisée par les exploitants permanents |
| **Tarif** | Montant de référence tiré du barème interne du BBDA, fixé par l'agent selon le type d'événement |
| **Redevance** | Montant complémentaire fixé par l'agent selon le contexte spécifique de l'événement ; avec le Tarif, compose le montant total dû |
| **Quittance** | Document (physique historiquement, PDF dans la plateforme) attestant du paiement de la redevance |
| **Arriéré** | Montant dû non réglé (paiement partiel ou absent) |
| **Sous surveillance** | Statut de compte organisateur suspecté de fraude ou injoignable, déclenchant une alerte automatique à la reconnexion |
| **Promotion publique** | Option permettant à un organisateur d'afficher son événement sur la page publique du site, uniquement après délivrance de la quittance |

## Glossaire technique

| Terme | Définition |
|---|---|
| **MVC** | Modèle-Vue-Contrôleur — patron d'architecture séparant données (Modèle), présentation (Vue) et logique de traitement des requêtes (Contrôleur) |
| **Blueprint** | Mécanisme Flask pour regrouper un ensemble de routes liées (ex. toutes les routes `/agent/...`) dans un module réutilisable |
| **Factory pattern** (`create_app()`) | Fonction qui construit et configure l'application au lieu d'une instance globale — permet plusieurs configurations (dev/prod/test) |
| **ORM** (SQLAlchemy) | Object-Relational Mapping — représente les tables SQL sous forme de classes Python, évite d'écrire du SQL brut |
| **Migration/seed** | `init_db.py` (à venir, Prompt 3) — script qui crée les tables et insère des données de démonstration |
| **Blueprint sans route** (`arrieres`, `notifications`) | Module Python de logique interne, appelé par d'autres blueprints, mais n'exposant lui-même aucune URL |

## Références (fichiers sources du projet)

- `guide/Protocole_Stage_V1.pdf` — cadrage académique officiel
- `guide/CahierDesCharges_V2_BBDA_Events.docx` — spécifications détaillées
- `guide/Guide_Complet_Dev_BBDA_Events_V2.docx` — 20 prompts de développement
- `guide/cursor_comprehension.odt` — historique de clarification
- `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`, `docs/REGLES_METIER.md`
- `AI_RULES.md` — contraintes de développement permanentes
- `database/schema.sql`, `database/schema_diagram.pdf`
- `images/*.jpg` — photos de la quittance BBDA physique réelle

## Sigles utilisés dans le code / la base de données

| Sigle / code | Signification |
|---|---|
| `RM-XXX` | Numéro de règle métier (`docs/REGLES_METIER.md`) |
| `FCFA` | Franc CFA (monnaie) |
| `PK` / `FK` | Primary Key / Foreign Key (clé primaire / clé étrangère) |
