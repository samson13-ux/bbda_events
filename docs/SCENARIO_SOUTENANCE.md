# Scénario de démonstration — BBDA Events (≈ 12 minutes)

> À répéter au moins 3 fois avant la soutenance. Chronométrer.

## Prérequis

- Serveur lancé : `python -m flask run` → http://127.0.0.1:5000  
- Soit base neuve (`python init_db.py --vide`) et comptes créés à la main,  
  soit données de soutenance (`python demo_data.py --reset`).

---

## Minute 0–2 — Face publique

1. Ouvrir `/` — présenter la marque BBDA Events, le slogan, le parcours en 3 étapes.  
2. Aller sur `/evenements` — expliquer la règle : **uniquement** les événements avec promotion **et** quittance.  
3. Ouvrir un détail d’événement (si données démo) ou montrer le message « aucun événement ».  
4. `/support` (FAQ) puis `/contact` — envoyer un message test.

## Minute 2–5 — Organisateur

1. `/auth/inscription` — créer un organisateur (ou se connecter).  
2. Tableau de bord — statistiques vides / en cours.  
3. **Nouvelle déclaration** : remplir le formulaire, cocher **Promotion publique**, ajouter une description (et une affiche si possible).  
4. Soumettre → message de confirmation + email (si SMTP configuré).  
5. Ouvrir le détail → frise chronologique + indicateur « sera publié après quittance ».

## Minute 5–8 — Agent BBDA

1. Se déconnecter, connexion `agent` (créé via admin ou démo).  
2. Tableau de bord agent — nouvelle déclaration visible.  
3. Ouvrir le dossier → **fixer le montant** (tarif + redevance).  
4. **Confirmer le paiement** (espèces, montant intégral).  
5. Montrer que la quittance est générée (PDF téléchargeable côté organisateur).

## Minute 8–10 — Publication

1. Retour organisateur → détail : indicateur « Visible publiquement » + lien.  
2. Face publique `/evenements` → l’événement apparaît.  
3. Page détail publique → infos événement, description, contact (si activé).

## Minute 10–12 — Admin et arriérés

1. Connexion **admin** → tableau de bord, utilisateurs, statistiques.  
2. (Optionnel) Créer un nouvel agent.  
3. Espace agent → **Arriérés** : montrer un compte bloqué / déblocage, ou créer un paiement partiel pour illustrer.  
4. Conclure : digitalisation du circuit papier sans changer le règlement au guichet.

---

## Points de bascule à verbaliser

- Pas de publication avant quittance (RM-090).  
- Compte bloqué si arriéré ≥ seuil (1000 FCFA par défaut).  
- Agents et admin ne s’inscrivent pas seuls : créés par l’administration.
