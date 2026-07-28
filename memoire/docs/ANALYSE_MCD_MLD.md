# Document d’analyse — MCD / MLD (BBDA Events)

## 1. Objectif de l’analyse

Analyser le circuit des **événements culturels occasionnels** au BBDA afin de concevoir une base de données et une application web (BBDA Events) couvrant : déclaration → évaluation → paiement guichet → quittance → éventuelle promotion publique, avec suivi des arriérés.

## 2. Acteurs

- **Organisateur** : déclare un événement, suit son dossier, télécharge la quittance.
- **Agent BBDA** : évalue (tarif + redevance), confirme les paiements, gère arriérés / surveillance.
- **Administrateur** : crée les agents, paramètres, statistiques.
- **Public / visiteur** : consulte les événements promus et quittancés, envoie un message contact.

## 3. Règles de gestion essentielles (extrait)

- Un organisateur avec arriéré ≥ seuil (1 000 FCFA par défaut) ne peut plus déposer de nouvelle déclaration.
- Le montant est fixé manuellement (tarif + redevance).
- Paiement au guichet ; plusieurs versements possibles.
- Quittance générée seulement si solde = 0.
- Promotion publique visible seulement si `promouvoir` et quittance délivrée.

## 4. MCD — Modèle Conceptuel de Données

Le MCD décrit les **entités métier** et leurs **associations**, indépendamment du SGBD.

### Entités principales

- **UTILISATEUR** : compte de connexion (rôle organisateur / agent / admin).
- **ORGANISATEUR** : profil métier lié à un utilisateur organisateur.
- **DECLARATION** : dossier d’événement occasionnel (cœur du système).
- **LISTE_ARTISTE** : artistes rattachés à une déclaration.
- **EVALUATION_AGENT** : tarif et redevance fixés par un agent.
- **PAIEMENT** : versement(s) confirmé(s) au guichet.
- **QUITTANCE** : preuve PDF une fois le dossier soldé.
- **ARRIERE** : reste dû pouvant bloquer le compte.
- **NOTIFICATION** : journal des emails automatiques.
- **ALERTE_SURVEILLANCE** : signalement à la reconnexion d’un compte surveillé.
- **MESSAGE_CONTACT** : message du formulaire public.
- **PARAMETRES_SYSTEME** : réglages admin (seuil, délais).

### Associations (cardinalités)

- UTILISATEUR **(1,1)** — **(0,1)** ORGANISATEUR : un organisateur a un compte ; un agent/admin n’a pas de profil organisateur.
- ORGANISATEUR **(1,1)** — **(0,n)** DECLARATION : un organisateur peut déclarer plusieurs événements.
- DECLARATION **(1,1)** — **(0,n)** LISTE_ARTISTE.
- DECLARATION **(1,1)** — **(0,1)** EVALUATION_AGENT.
- DECLARATION **(1,1)** — **(0,n)** PAIEMENT.
- DECLARATION **(1,1)** — **(0,1)** QUITTANCE.
- ORGANISATEUR **(1,1)** — **(0,n)** ARRIERE.
- UTILISATEUR **(1,1)** — **(0,n)** NOTIFICATION.

### Diagramme MCD

Voir le fichier image : `memoire/docs/diagrammes/07-mcd.png`  
Source Mermaid : `07-mcd.mmd`

## 5. MLD — Modèle Logique de Données (résumé)

Passage du MCD vers des **tables** et clés :

- Chaque entité → une table.
- Association 1—n → clé étrangère du côté « n ».
- Association 1—1 → clé étrangère unique (ex. `organisateur.utilisateur_id`, `quittance.declaration_id`).
- Association 1—0,1 → même principe, ligne absente tant que non créée (évaluation, quittance).

Détail colonnes : `DATABASE_SCHEMA.md`.

## 6. Lien avec l’application

Le MCD / MLD se retrouve dans `models.py` (SQLAlchemy) et dans le fonctionnement du site (inscription → déclaration → évaluation → paiement → quittance).
