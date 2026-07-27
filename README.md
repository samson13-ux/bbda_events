# BBDA Events

> Plateforme de déclaration, de gestion et de promotion des événements culturels occasionnels au BBDA

**Auteur** : FOFANA Samson — Licence Informatique, Option Programmation, U-AUBEN 2026  
**Structure d'accueil** : Bureau Burkinabè du Droit d'Auteur (BBDA)

## Stack technique
- Backend : Python 3.x + Flask + SQLAlchemy
- Frontend : HTML5, CSS3, JavaScript
- BDD : PostgreSQL (Render) / MySQL (dev possible)
- PDF : ReportLab
- Emails : Flask-Mail / SendGrid

## Lancer le projet
```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # remplir les valeurs
python init_db.py
flask run
```

## Organisation du dépôt

| Emplacement | Rôle |
|---|---|
| Racine + `backend/` + `frontend/` + `tests/` | **Site** (indispensable au fonctionnement) |
| `memoire/` | Rédaction du mémoire, guides, captures, schéma BDD |
| `archives/` | Fichiers non nécessaires au site (scripts locaux, etc.) |

## Documentation (mémoire)
- [Architecture](memoire/docs/ARCHITECTURE.md)
- [Base de données](memoire/docs/DATABASE_SCHEMA.md)
- [Règles métier](memoire/docs/REGLES_METIER.md)
- [Mémoire](memoire/redaction/08-MEMOIRE.md)
