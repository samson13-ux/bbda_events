# ARCHITECTURE.md — Architecture technique de BBDA Events

---

## 1. Vue d'ensemble

BBDA Events est une application web monolithique basée sur le pattern **MVC (Modèle-Vue-Contrôleur)** implémenté avec Flask Blueprints.

```
Navigateur (Client)
       ↕ HTTP
Flask (Serveur)
  ├── Routes (Contrôleur) → Blueprints
  ├── Models (Modèle)     → SQLAlchemy + MySQL
  └── Templates (Vue)     → Jinja2 + HTML/CSS/JS
```

---

## 2. Structure des dossiers

```
bbda_events/
│
├── AI_RULES.md               ← règles IA permanentes
├── README.md                 ← documentation principale
├── app.py                    ← factory Flask (create_app)
├── config.py                 ← configurations (dev/prod)
├── models.py                 ← tous les modèles SQLAlchemy
├── requirements.txt
├── init_db.py                ← initialisation BDD + données test
├── .env                      ← secrets (non versionné)
├── .env.example
├── .gitignore
│
├── docs/                     ← documentation technique
│   ├── ARCHITECTURE.md       ← ce fichier
│   ├── DATABASE_SCHEMA.md    ← schéma base de données
│   └── REGLES_METIER.md      ← règles métier
│
├── backend/                  ← logique Python/Flask
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py         ← inscription, connexion, déconnexion
│   ├── declarations/
│   │   ├── __init__.py
│   │   └── routes.py         ← formulaire, tableau de bord organisateur
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── routes.py         ← traitement déclarations, paiements
│   │   └── stats.py          ← calculs statistiques
│   ├── admin/
│   │   ├── __init__.py
│   │   └── routes.py         ← administration globale
│   ├── public/
│   │   ├── __init__.py
│   │   └── routes.py         ← face publique (accueil, événements, légal)
│   ├── arrieres/
│   │   ├── __init__.py
│   │   └── moteur.py         ← logique gestion des arriérés
│   ├── exports/
│   │   ├── __init__.py
│   │   ├── routes.py         ← route téléchargement PDF
│   │   └── pdf_generator.py  ← génération quittance ReportLab
│   └── notifications/
│       ├── __init__.py
│       └── email_service.py  ← envoi emails Flask-Mail
│
├── frontend/
│   ├── templates/            ← HTML Jinja2
│   │   ├── public/           ← pages publiques (accueil, événements...)
│   │   ├── auth/             ← inscription, connexion
│   │   ├── declarations/     ← formulaire, détail déclaration
│   │   ├── agent/            ← tableau de bord agent, traitement
│   │   └── admin/            ← administration
│   └── static/
│       ├── css/
│       ├── js/
│       ├── img/
│       ├── uploads/          ← affiches événements uploadées
│       └── quittances/       ← PDFs générés
│
├── database/
│   ├── schema.sql            ← CREATE TABLE (généré)
│   └── seeds.sql             ← données de test
│
└── tests/
    └── test_app.py
```

---

## 3. Blueprints Flask — Responsabilités

| Blueprint | Préfixe URL | Responsabilité |
|-----------|-------------|----------------|
| `public` | `/` | Face publique : accueil, événements, support, contact, légal |
| `auth` | `/auth` | Inscription, connexion, déconnexion |
| `declarations` | `/declarations` | Formulaire et suivi côté organisateur |
| `agent` | `/agent` | Traitement déclarations, paiements, arriérés |
| `admin` | `/admin` | Administration, paramètres, statistiques |
| `exports` | `/exports` | Téléchargement quittances PDF |

---

## 4. Flux de données principal

```
Organisateur soumet formulaire
         ↓
Route POST /declarations/nouvelle
         ↓
Validation des données
         ↓
Création Declaration en BDD (statut: nouvelle)
         ↓
notifications/email_service.py → email confirmation
         ↓
Agent reçoit dans /agent/dashboard
         ↓
Agent fixe montant → EvaluationAgent en BDD
         ↓
email_service.py → email montant à l'organisateur
         ↓
Agent confirme paiement → Paiement en BDD
         ↓
exports/pdf_generator.py → Quittance PDF générée
         ↓
Quittance en BDD + email à l'organisateur
         ↓
Si promouvoir=True → événement visible sur /evenements
```

---

## 5. Modèles et relations

```
Utilisateur ─────────── Organisateur (1-1)
                              │
                         Declaration (1-N)
                         ├── ListeArtiste (1-N)
                         ├── EvaluationAgent (1-1)
                         ├── Paiement (1-1)
                         └── Quittance (1-1)

Organisateur ──────────── Arriere (1-N)
Organisateur ──────────── AlerteSurveillance (1-N)

Utilisateur ───────────── Notification (1-N)
```

---

## 6. Sécurité et accès

```
/ (public)              → Tout le monde
/auth/*                 → Tout le monde
/declarations/*         → login_required_organisateur
/agent/*                → login_required_agent
/admin/*                → login_required_admin
/exports/quittance/*    → login_required_organisateur
```

---

## 7. Variables d'environnement requises

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Clé secrète Flask | `une-longue-chaine-aleatoire` |
| `DATABASE_URL` | URL connexion MySQL | `mysql+pymysql://root:@localhost:3306/bbda_events_db` |
| `MAIL_USERNAME` | Email Gmail dédié | `bbda.events@gmail.com` |
| `MAIL_PASSWORD` | Mot de passe application Gmail | `abcdefghijklmnop` |
| `FLASK_ENV` | Environnement | `development` |

---

## 8. Dépendances principales

```
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-login==0.6.3
flask-mail==0.9.1
bcrypt==4.1.2
reportlab==4.0.9
python-dotenv==1.0.0
pymysql==1.1.0
```

---

*Dernière mise à jour : Juillet 2026*
