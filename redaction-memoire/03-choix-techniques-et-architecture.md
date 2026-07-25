# Choix techniques et architecture

## 1. Pourquoi une architecture MVC monolithique avec Flask ?

Le protocole de stage impose Flask + MySQL + rendu serveur (Jinja2). Au-delà de
la contrainte, ce choix se justifie techniquement pour ce projet :

- **Simplicité de déploiement** : un seul processus Python sert à la fois les
  pages HTML et les données, pas besoin d'une API séparée + un frontend séparé
  + leur synchronisation. Pertinent pour une infrastructure BBDA qui n'a pas
  de serveur Node.js dédié.
- **Périmètre fonctionnel** : le projet est avant tout un outil de gestion
  interne (agents) + un formulaire (organisateurs) + une vitrine publique
  simple. Pas de besoin d'application mobile native ni de SPA complexe — donc
  pas besoin de séparer front/back.
- **Cohérence avec le stage** : un développeur qui rejoint une petite
  structure (BBDA) doit pouvoir maintenir seul un monolithe Flask sans
  connaître un écosystème JavaScript en plus.

**Le pattern MVC appliqué au projet :**

| Couche | Rôle | Traduction dans le projet |
|---|---|---|
| **Modèle** | Représente les données et les règles de persistance | `models.py` (SQLAlchemy) |
| **Vue** | Présente les données à l'utilisateur | `frontend/templates/*.html` (Jinja2) |
| **Contrôleur** | Reçoit les requêtes HTTP, orchestre modèle et vue | `backend/<module>/routes.py` (Blueprints Flask) |

## 2. Le "factory pattern" — pourquoi `create_app()` plutôt qu'un `app` global

```python
# app.py
def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
    app.config.from_object(config_by_name[env])

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    import models  # enregistre les modeles et le user_loader
    _register_blueprints(app)
    return app
```

**Pourquoi ce choix plutôt qu'une instance Flask créée directement au niveau
module ?**

1. **Testabilité** : les tests automatisés (`tests/test_app.py`) peuvent créer
   une instance d'application isolée avec une configuration de test
   (base SQLite en mémoire) sans toucher à la vraie base MySQL. Un `app`
   global rendrait cela impossible sans hacks.
2. **Multi-configuration** : une seule fonction sait produire l'app en mode
   développement, production ou test, simplement en changeant l'argument
   passé à `config_by_name[env]`.
3. **Évite les imports circulaires** : les blueprints ont besoin d'objets
   comme `db` (SQLAlchemy) sans connaître l'application avant qu'elle
   n'existe — la factory permet d'enregistrer (`init_app`) les extensions
   après leur création, à un instant précis et maîtrisé.

C'est un pattern standard et documenté de Flask lui-même (section "Application
Factories" de la documentation officielle) — un bon argument de robustesse à
citer dans le mémoire.

## 3. `extensions.py` — pourquoi une séparation dédiée

```python
# extensions.py
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
```

Problème que ce fichier résout : `models.py` a besoin de l'objet `db` pour
définir les modèles, et les blueprints de `backend/` ont besoin de `db` pour
faire des requêtes. Si `db` était défini directement dans `app.py`, alors
`models.py` devrait importer `app.py`, qui lui-même importe `models.py` (via
la factory) → **import circulaire**, une erreur classique en Flask pour les
débutants. En isolant les instances d'extensions dans un module neutre
(`extensions.py`, qui n'importe rien du reste du projet), tous les autres
fichiers peuvent l'importer sans dépendance croisée.

## 4. Découpage en Blueprints — un contrôleur par responsabilité

| Blueprint | Préfixe URL | Responsabilité | Statut |
|---|---|---|---|
| `public` | `/` | Face publique (accueil, événements, contact...) | Squelette posé (route `/` fonctionnelle) |
| `auth` | `/auth` | Inscription, connexion, déconnexion | Squelette posé, logique à venir (Prompt 4) |
| `declarations` | `/declarations` | Formulaire + suivi organisateur | Squelette posé, logique à venir (Prompts 6-8) |
| `agent` | `/agent` | Traitement des déclarations, paiements | Squelette posé, logique à venir (Prompts 9-11, 15) |
| `admin` | `/admin` | Administration, paramètres, statistiques | Squelette posé, logique à venir (Prompt 16) |
| `exports` | `/exports` | Téléchargement des quittances PDF | Squelette posé, logique à venir (Prompt 12) |

Deux modules supplémentaires n'exposent **aucune route** — ce sont des
bibliothèques de logique interne, appelées par les blueprints ci-dessus :
- `backend/arrieres/moteur.py` — calcul et gestion des arriérés.
- `backend/notifications/email_service.py` — envoi des emails automatiques.

**Argument de conception à mettre en avant** : ce découpage traduit
directement le "qui fait quoi" du processus métier réel (organisateur déclare
→ agent évalue et encaisse → admin supervise → export produit un document).
Chaque acteur métier a un blueprint dédié avec ses propres permissions d'accès
(voir `docs/ARCHITECTURE.md` §6, table de sécurité/accès), ce qui rend le
contrôle d'accès simple à raisonner et à auditer.

## 5. Gestion de la configuration : Dev / Prod / Testing

```python
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-remplacer")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    ...

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
```

`DevelopmentConfig`/`ProductionConfig` étaient prévues dès `docs/ARCHITECTURE.md`.
`TestingConfig` a été ajoutée pendant le scaffolding : elle permet de lancer la
suite de tests automatisés sur une base **SQLite en mémoire** plutôt que sur la
vraie base MySQL/XAMPP — les tests sont donc rapides, ne polluent jamais les
données réelles, et peuvent tourner sans que XAMPP soit démarré.

## 6. Secrets et variables d'environnement

Conformément à `AI_RULES.md` ("secrets toujours dans `.env`, jamais en dur"),
aucune information sensible (mot de passe MySQL, mot de passe applicatif
Gmail, clé secrète Flask) n'est écrite dans le code. `.env.example` documente
la liste des variables attendues ; `.env` (réel, avec les vraies valeurs)
n'est jamais versionné (`.gitignore`).

## 7. Dépendances retenues (`requirements.txt`)

| Paquet | Rôle |
|---|---|
| `flask` | Framework web |
| `flask-sqlalchemy` | ORM (mapping objet-relationnel vers MySQL) |
| `flask-login` | Gestion des sessions utilisateur |
| `flask-mail` | Envoi d'emails (notifications) |
| `bcrypt` | Hachage sécurisé des mots de passe |
| `reportlab` | Génération de PDF (quittances) |
| `python-dotenv` | Chargement du fichier `.env` |
| `pymysql` | Pilote MySQL pour SQLAlchemy |
| `pytest` | Framework de tests automatisés |

## 8. État d'avancement de l'architecture (au 2026-07-15)

Ce qui existe et fonctionne : arborescence complète, factory Flask, 6
blueprints enregistrés, 12 modèles SQLAlchemy, connexion vérifiée à MySQL
(XAMPP), suite de tests automatisés (2/2 tests passants).

Ce qui reste à construire (Prompts 3 à 20 du guide de dev) : script
d'initialisation de la base (`init_db.py`) + données de démonstration,
logique d'authentification réelle, templates HTML de toutes les pages,
formulaire de déclaration, tableaux de bord organisateur/agent/admin, moteur
d'arriérés, service d'emails, génération PDF, statistiques, face publique
complète. Voir le détail chronologique dans
[06-journal-de-bord-technique.md](06-journal-de-bord-technique.md).
