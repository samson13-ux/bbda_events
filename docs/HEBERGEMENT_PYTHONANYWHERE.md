# Hebergement BBDA Events sur PythonAnywhere (lien fixe)

> Alternative a ngrok / Cloudflare : l'appli tourne **sur Internet**,
> avec une adresse du type `https://toncompte.pythonanywhere.com`
> qui **ne change pas**. Ton PC peut etre eteint.

## Pourquoi PythonAnywhere ?

- Lien fixe gratuit (compte Beginner)
- **MySQL** disponible (comme en local avec XAMPP)
- Pense pour Flask / etudiants
- Pas d'antivirus Windows qui bloque un tunnel

Contrepartie : apres une correction de code, il faut **recharger** l'appli
sur le dashboard (pas aussi instantane qu'en local).

## Etape 1 — Compte

1. Va sur https://www.pythonanywhere.com/registration/register/beginner/  
2. Cree un compte gratuit  
3. Note ton **username** (il fera partie du lien)

Ton lien sera : `https://TONUSERNAME.pythonanywhere.com`

## Etape 2 — Base MySQL

1. Onglet **Databases**  
2. Create a database (ex. `bbda_events`)  
3. Note :
   - host (souvent `TONUSERNAME.mysql.pythonanywhere-services.com`)
   - user (souvent `TONUSERNAME`)
   - password MySQL que tu choisis
   - nom complet de la base : `TONUSERNAME$bbda_events`

## Etape 3 — Code sur le serveur

### Option A — Git (recommande si le projet est sur GitHub)

Dans une **Bash console** PythonAnywhere :

```bash
cd ~
git clone https://github.com/TON_COMPTE/bbda_events.git
cd bbda_events
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install mysqlclient || pip install pymysql
```

### Option B — Upload ZIP

1. En local : zipper le projet (sans `venv/`)  
2. Onglet **Files** → Upload  
3. Dans Bash : `unzip ...` puis meme `venv` + `pip install`

## Etape 4 — Fichier `.env` sur PythonAnywhere

Dans `bbda_events/.env` (onglet Files → editeur) :

```env
SECRET_KEY=une-longue-chaine-aleatoire-differente
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST/USER$bbda_events
MAIL_USERNAME=ton@gmail.com
MAIL_PASSWORD=mot-de-passe-application
PUBLIC_BASE_URL=https://TONUSERNAME.pythonanywhere.com
```

Remplace USER, PASSWORD, HOST, TONUSERNAME par tes valeurs Databases.

## Etape 5 — Creer les tables + admin

Bash console :

```bash
cd ~/bbda_events
source venv/bin/activate
python init_db.py --vide
```

Compte admin : `admin@bbda.bf` / `password123`  
(change le mot de passe apres la premiere connexion)

## Etape 6 — Web app

1. Onglet **Web** → **Add a new web app**  
2. Manual configuration → Python 3.10 (ou 3.11)  
3. Source code : `/home/TONUSERNAME/bbda_events`  
4. Working directory : `/home/TONUSERNAME/bbda_events`  
5. Virtualenv : `/home/TONUSERNAME/bbda_events/venv`  
6. **WSGI configuration file** → ouvrir le fichier, remplacer par :

```python
import sys
path = "/home/TONUSERNAME/bbda_events"
if path not in sys.path:
    sys.path.insert(0, path)

from passenger_wsgi import application
```

7. **Static files** (important) :
   - URL : `/static/`  
   - Directory : `/home/TONUSERNAME/bbda_events/frontend/static/`

8. Bouton vert **Reload**

## Etape 7 — Tester

Ouvre : `https://TONUSERNAME.pythonanywhere.com`

## Apres une correction de code

```bash
cd ~/bbda_events
git pull   # si tu utilises Git
# ou re-upload les fichiers modifies
```

Puis onglet **Web** → **Reload**.

## Limites du compte gratuit

- Le site peut "s'endormir" apres inactivite (premier chargement un peu lent)
- Pas de domaine personnalise sans compte payant
- Suffisant pour tests telephone, jury, demo de stage

## Securite

- Ne committe jamais `.env`
- Change `SECRET_KEY` et le mot de passe admin
- Partage le lien seulement aux testeurs
