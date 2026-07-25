# BBDA Events

> Plateforme de déclaration, de gestion et de promotion des événements culturels occasionnels au BBDA

**Auteur** : FOFANA Samson — Licence Informatique, Option Programmation, U-AUBEN 2026  
**Structure d'accueil** : Bureau Burkinabè du Droit d'Auteur (BBDA)  
**Inspiré de** : Veenue.io

## Stack technique
- Backend : Python 3.x + Flask + SQLAlchemy
- Frontend : HTML5, CSS3, JavaScript
- BDD : MySQL
- PDF : ReportLab
- Emails : Flask-Mail

## Lancer le projet
```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # remplir les valeurs
python init_db.py
flask run
```

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Base de données](docs/DATABASE_SCHEMA.md)
- [Règles métier](docs/REGLES_METIER.md)
- [Règles IA](AI_RULES.md)
