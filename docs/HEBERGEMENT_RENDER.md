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
| `SENDGRID_API_KEY` | clé API SendGrid | **Oui (recommandé) pour emails sur Render free** |
| `BREVO_API_KEY` | clé API Brevo | Alternative (parfois activation manuelle requise) |
| `MAIL_USERNAME` | email expéditeur vérifié chez SendGrid/Brevo | Oui |

### Emails sur Render free (important)

Depuis sept. 2025, Render **bloque le SMTP** (ports 25/465/587) sur le plan gratuit.
Gmail SMTP ne fonctionne donc plus depuis Render.

**Solution recommandée : SendGrid (gratuit)** — envoi par HTTPS, souvent utilisable le jour même :

1. Crée un compte sur https://signup.sendgrid.com  
2. **Settings → Sender Authentication → Single Sender Verification**  
   → ajoute ton Gmail → clique le lien de confirmation reçu  
3. **Settings → API Keys → Create API Key** (Full Access ou Mail Send) → copie `SG....`  
4. Dans Render → Environment :
   - `SENDGRID_API_KEY` = la clé  
   - `MAIL_USERNAME` = l’email vérifié Single Sender  
5. Si tu as encore `BREVO_API_KEY`, tu peux le laisser : **SendGrid est prioritaire**.  
6. Save and deploy  

**Alternative Brevo** : `BREVO_API_KEY` + sender vérifié. Certains comptes attendent une activation manuelle Brevo avant d’envoyer.

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

### Changer le mot de passe admin existant (sans Shell)

1. Ajoute / mets a jour `ADMIN_PASSWORD` (fort, ≥ 10 caracteres)
2. Ajoute temporairement `FORCE_ADMIN_PASSWORD_RESET=1`
3. **Manual Deploy** → attendre le succes
4. **Supprime** `FORCE_ADMIN_PASSWORD_RESET` (important)
5. Connecte-toi avec `admin@bbda.bf` + le nouveau mot de passe
6. Optionnel : **Paramètres → Changer mon mot de passe**

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
- [ ] `SENDGRID_API_KEY` + `MAIL_USERNAME` (email Single Sender vérifié) pour les notifications
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
