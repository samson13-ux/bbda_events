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
   - **Start Command** : laisse le `Procfile` (bootstrap + gunicorn production)
   - Plan **Free**

## Etape 3 — Variables d'environnement (Partie 1 securite)

Dans le Web Service → **Environment** :

| Cle | Valeur | Obligatoire |
|-----|--------|-------------|
| `FLASK_ENV` | `production` | Oui |
| `SECRET_KEY` | chaine aleatoire **≥ 24 caracteres** | Oui (sinon l'app refuse de demarrer) |
| `DATABASE_URL` | URL Postgres Render | Oui |
| `ADMIN_PASSWORD` | mot de passe admin fort **≥ 10 caracteres** | Oui pour creer/reset admin |
| `PUBLIC_BASE_URL` | `https://bbda-events.onrender.com` | Oui pour liens emails |
| `SENDGRID_API_KEY` | clé API SendGrid (`SG....`) | **Oui pour emails sur Render free** |
| `MAIL_USERNAME` | email **Single Sender vérifié** SendGrid | Oui (même adresse) |

### Emails

- **Local** : SMTP Gmail (`MAIL_USERNAME` + `MAIL_PASSWORD`) — intact.
- **Render free** : `SENDGRID_API_KEY` + `MAIL_USERNAME` (= Single Sender vérifié, **sans domaine**).
- Si `SENDGRID_API_KEY` est présent, SendGrid est utilisé ; sinon SMTP.

**Setup SendGrid rapide :**
1. Single Sender vérifié (déjà fait)
2. Settings → API Keys → Create API Key (permission **Mail Send**)
3. Render Environment : `SENDGRID_API_KEY` + `MAIL_USERNAME`
4. Admin → Paramètres → Envoyer le test

### Astuce DATABASE_URL

1. Ouvre ton service **PostgreSQL** (pas le Web Service)
2. Copie l’**Internal Database URL** (recommandé)  
3. Colle-la dans le Web Service → Environment → `DATABASE_URL`

L'app convertit automatiquement `postgres://` → `postgresql+psycopg://` et ajoute `sslmode=require` si besoin.

Si tu vois `SSL error: decryption failed or bad record mac` : redéploie, vérifie que Postgres est **Available**, et que `DATABASE_URL` est bien l’URL **Internal**.

## Etape 4 — Premier demarrage + admin

Le **Shell Render est payant** sur le plan gratuit.  
Le `Procfile` lance automatiquement :

```bash
python init_db.py --bootstrap
```

Cela cree les tables + l'admin **uniquement si la base est vide**.

### Nettoyer les donnees de test (base neuve, sans Shell)

**Important :** ne retire PAS la variable pendant le deploy. Attends **Live** + le log de succes.

1. Attends que le dernier commit soit deploye
2. Environment → ajoute :
   - `ADMIN_PASSWORD` (≥ 10 caracteres)
   - `RESET_BASE_JETON` = `nettoyer-lundi-1` (n'importe quel texte unique)
3. **Manual Deploy** → attends **Live**
4. Logs : cherche `RESET_BASE_JETON=... appliqué avec succès`
5. Ensuite seulement : **supprime** `RESET_BASE_JETON`
6. Connexion : `admin@bbda.bf` → affiche **SAMSON BBDA**

Pour un 2e nettoyage plus tard : change le jeton (`nettoyer-lundi-2`) puis redeploy.

## Partie 2 — durcissement (deja dans le code)

- CSRF sur tous les formulaires POST
- Rate-limit : connexion (10/min), inscription (8/min), contact (5/min)
- Uploads affiche : controle extension **et** contenu (magic bytes JPG/PNG)

## Checklist Partie 1 — avant les tests utilisateurs

- [ ] `SECRET_KEY` long et unique (pas la valeur d'exemple)
- [ ] `FLASK_ENV=production`
- [ ] `PUBLIC_BASE_URL` pointe vers l'URL Render HTTPS
- [ ] `ADMIN_PASSWORD` fort defini
- [ ] Mot de passe admin demarre (`password123`) **remplace** via reset one-shot ou ecran Paramètres
- [ ] `MAIL_USERNAME` defini (liens / contact)
- [ ] Connexion admin OK

- [ ] Connexion organisateur de test OK
- [ ] Deconnexion OK
- [ ] Accueil public OK apres cold start

## Etape 5 — Tester

Ouvre `https://bbda-events.onrender.com`

Sur le plan gratuit, le premier chargement apres inactivite peut prendre ~1 minute.

## Mises a jour

```bash
git add .
git commit -m "message"
git push
```

Render redéploie automatiquement. Le lien reste le meme.
