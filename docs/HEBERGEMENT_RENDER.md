# Hebergement BBDA Events sur Render (lien fixe)

## Prerequis

1. Code sur GitHub : `https://github.com/samson13-ux/bbda_events`
2. Compte Render lie a GitHub : https://render.com

## Etape 1 — Base Postgres

1. Dashboard Render → **New** → **PostgreSQL**
2. Name : `bbda-events-db`
3. Plan **Free**
4. Apres creation, copie la **Internal Database URL** (ou External)

## Etape 2 — Web Service

1. **New** → **Web Service**
2. Connecte le repo `samson13-ux/bbda_events`
3. Reglages :
   - **Runtime** : Python
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - Plan **Free**

## Etape 3 — Variables d'environnement

Dans le Web Service → **Environment** :

| Cle | Valeur |
|-----|--------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | longue chaine aleatoire |
| `DATABASE_URL` | URL Postgres Render (voir ci-dessous) |
| `MAIL_USERNAME` | ton email Gmail |
| `MAIL_PASSWORD` | mot de passe d'application |
| `PUBLIC_BASE_URL` | `https://TON-SERVICE.onrender.com` |

### Astuce DATABASE_URL

Render donne parfois `postgres://...`. SQLAlchemy prefere `postgresql://...`.
Si besoin, remplace le debut :

`postgres://` → `postgresql+psycopg://`

(ou `postgresql://` selon le driver installe).

## Etape 4 — Premier demarrage + admin

Le **Shell Render est payant** sur le plan gratuit.  
Le `Procfile` lance automatiquement au demarrage :

```bash
python init_db.py --bootstrap
```

Cela cree les tables + l'admin **uniquement si la base est vide**  
(ne detruit pas les donnees aux redeploiements suivants).

Admin : `admin@bbda.bf` / `password123`

## Etape 5 — Tester

Ouvre `https://TON-SERVICE.onrender.com`

Sur le plan gratuit, le premier chargement apres inactivite peut prendre ~1 minute.

## Mises a jour

```bash
git add .
git commit -m "message"
git push
```

Render redéploie automatiquement. Le lien reste le meme.
