# DATABASE_SCHEMA.md — Schéma de la base de données BBDA Events

---

## Informations générales

- **SGBD** : MySQL (local) ; PostgreSQL (production Render)
- **Base de données** : `bbda_events_db` (local)
- **Encodage** : `utf8mb4_unicode_ci`
- **Moteur** : InnoDB (MySQL)
- **Nombre de tables** : 12
- **Modèles code** : `models.py` (SQLAlchemy)
- **Règles métier** : `REGLES_METIER.md`

---

## Fonctionnement en lien avec le site (explications)

Cette section explique **en texte** comment la base fonctionne avec le site : qui fait quoi, quelles tables sont touchées, quelles relations existent. Ce n’est pas seulement la liste des colonnes : c’est le circuit métier → écrans → tables. Le détail technique colonne par colonne se trouve plus bas dans ce même fichier.

### Idée générale

Imagine la plateforme comme un **dossier administratif numérique**. Ce dossier, c’est une déclaration d’événement. Il naît quand un organisateur remplit le formulaire, puis il avance étape par étape : l’agent l’évalue, le paiement est enregistré, la quittance est délivrée. À chaque étape du site, une ou plusieurs lignes sont créées ou mises à jour dans la base.

Le fil conducteur ressemble à ceci : d’abord l’inscription crée un compte (`utilisateur`) et, pour un organisateur, un profil (`organisateur`) ; ensuite la déclaration crée le dossier (`declaration`) avec ses artistes (`liste_artiste`) et souvent un email journalisé (`notification`) ; puis l’agent fixe le montant dans `evaluation_agent` ; ensuite un ou plusieurs `paiement` sont enregistrés ; s’il reste de l’argent dû, un `arriere` apparaît ; enfin, quand tout est soldé, une `quittance` est créée et le dossier peut, si l’option a été cochée, apparaître sur la face publique.

Il n’y a pas trois bases différentes selon les rôles. Il y a **une seule base**, et trois façons de s’en servir. L’**organisateur** se connecte via `utilisateur` et possède un profil dans `organisateur` : il déclare des événements, suit ses dossiers et télécharge sa quittance. L’**agent** se connecte aussi via `utilisateur`, mais avec le rôle agent : il n’a pas de profil organisateur ; il évalue les dossiers, confirme les paiements reçus au guichet, et gère les arriérés ou la surveillance. L’**administrateur** est encore un `utilisateur` (rôle admin) : il crée les comptes agents, règle les paramètres système et consulte les statistiques globales.

### À quoi sert chaque table sur le site

La table `utilisateur` alimente les pages d’inscription, de connexion et de déconnexion. Elle stocke l’identité de connexion : nom, prénom, email, mot de passe (toujours sous forme de hash bcrypt, jamais en clair), le rôle (`organisateur`, `agent` ou `admin`) et le statut du compte (`actif` ou `inactif`). Un email ne peut appartenir qu’à un seul compte. C’est la porte d’entrée de toute session : Flask-Login recharge l’utilisateur à partir de l’identifiant stocké dans la session. Un agent ou un administrateur existe uniquement dans `utilisateur` : il n’a **pas** de ligne dans `organisateur`, car ce profil est réservé aux personnes qui organisent des événements.

La table `organisateur` est créée automatiquement quand quelqu’un s’inscrit comme organisateur sur le site public. Elle complète le compte de connexion avec des informations métier : la qualité (promoteur, association, directeur de salle…), le téléphone, et surtout le **statut du compte organisateur** (`actif`, `arriere`, `bloque`, `surveillance`). Ce statut-là n’est pas le même que le statut « actif / inactif » de `utilisateur` : il dit si l’organisateur peut encore déposer de nouvelles déclarations, s’il est endetté, bloqué, ou placé sous surveillance par un agent. La relation est un-pour-un : un utilisateur organisateur correspond à exactement un profil organisateur (`organisateur.utilisateur_id` → `utilisateur.id`).

La table `declaration` est la table centrale du site. Elle alimente le formulaire « Nouvelle déclaration », le tableau de bord de l’organisateur, l’écran de traitement de l’agent, et éventuellement la page publique d’un événement (seulement s’il est promu et quittancé). Chaque ligne décrit un événement occasionnel (identité du demandeur, salle, date, capacité, options de promotion, etc.). Le champ le plus important pour le fonctionnement du site est le **statut** du dossier : c’est lui qui décide ce que l’organisateur et l’agent ont le droit de faire. Un organisateur peut avoir plusieurs déclarations (relation un-pour-plusieurs via `declaration.organisateur_id`).

La table `liste_artiste` stocke les artistes saisis dans le formulaire. Une déclaration peut en avoir plusieurs. Si une déclaration était supprimée, ses lignes d’artistes partiraient avec elle (cascade).

La table `evaluation_agent` est écrite quand l’agent fixe le montant. L’agent saisit deux montants distincts : le **tarif** (référence barème BBDA) et la **redevance** (montant complémentaire selon le contexte). Le total dû se calcule en additionnant les deux. Une déclaration n’a qu’une évaluation (lien unique sur `declaration_id`). L’agent qui a saisi le montant est mémorisé via `agent_id`.

La table `paiement` enregistre la confirmation d’encaissement **après** le paiement réel au guichet du BBDA (pas de paiement en ligne dans le prototype). Une même déclaration peut recevoir plusieurs versements successifs. Chaque ligne mémorise le mode, le montant, le type intégral ou partiel, le solde restant après ce versement, et l’agent confirmateur.

La table `quittance` naît automatiquement lorsque le solde restant d’une déclaration atteint zéro. Le site génère un PDF, enregistre le numéro séquentiel, les montants et le chemin du fichier. Il n’y a **au plus qu’une** quittance par déclaration (relation un-pour-zéro-ou-un).

La table `arriere` est créée quand un paiement ne couvre pas tout le montant. Elle est rattachée à l’organisateur et, en général, à la déclaration d’origine. Si le cumul des sommes dues atteint ou dépasse le seuil configuré (par défaut 1 000 FCFA), le statut du compte organisateur évolue et les nouvelles déclarations sont refusées jusqu’à régularisation.

La table `alerte_surveillance` intervient quand un agent place un organisateur « sous surveillance ». Si cette personne se reconnecte ensuite, une alerte est créée pour les agents.

La table `notification` journalise chaque email automatique (confirmation, montant fixé, quittance, rappel d’arriéré, etc.). On enregistre d’abord la notification, ensuite on tente l’envoi. Si le mail échoue, le dossier métier n’est **pas** annulé.

La table `message_contact` reçoit les messages du formulaire public Contact. Elle est isolée : un visiteur n’a pas besoin d’avoir un compte.

La table `parametres_systeme` permet à l’admin de modifier des réglages sans redéployer le code, notamment le seuil d’arriéré bloquant (`SEUIL_ARRIERE`) et le délai lié aux rappels (`DELAI_NOTIFICATION`).

### Cycle de vie d’une déclaration (statut et comportement du site)

Le champ `declaration.statut` est le « feu de signalisation » du dossier. Quand l’organisateur soumet le formulaire, le statut devient `nouvelle` : il peut encore corriger sa déclaration. Dès qu’un agent ouvre le dossier, le statut passe à `en_evaluation` : l’organisateur ne modifie plus ; l’agent analyse et peut soit fixer le montant, soit mettre le dossier `en_attente` avec un commentaire obligatoire. Quand le montant est validé, le statut devient `montant_fixe`. Après un ou plusieurs paiements, si le solde tombe à zéro, le dossier passe à `payee` puis `quittance_delivree` avec génération du PDF. Seulement à ce moment-là, si la case promotion avait été cochée, l’événement peut apparaître sur `/evenements`. Sinon, même un événement « à promouvoir » reste invisible au public.

### Parcours complet : ce qui s’écrit en base

À l’**inscription**, le site crée une ligne `utilisateur` (rôle organisateur) puis une ligne `organisateur` liée : deux écritures, relation un-pour-un.

À la **nouvelle déclaration**, le site vérifie d’abord l’absence d’arriéré bloquant, puis crée la `declaration` au statut `nouvelle`, les lignes `liste_artiste`, et une `notification` de confirmation. L’affiche éventuelle est un fichier sur disque ; seule son adresse (`affiche_path`) est en base.

Au **traitement agent**, le statut évolue vers `en_evaluation` puis `montant_fixe` ; une ligne `evaluation_agent` mémorise tarif, redevance et l’agent ; une notification prévient l’organisateur.

Au **paiement**, l’agent confirme le versement guichet : une ligne `paiement` apparaît. Si le paiement est partiel, un `arriere` est créé. Si le solde tombe à zéro, une `quittance` est créée, le statut passe à `quittance_delivree`, et l’événement peut devenir public si `promouvoir` est vrai.

La **face publique** ne crée pas de table spéciale : elle filtre les déclarations où `promouvoir = true` et `statut = quittance_delivree`. Sinon, le détail public répond en 404.

L’**admin** crée un agent comme simple `utilisateur` (rôle agent, sans profil organisateur). Les statistiques sont des lectures agrégées. Les réglages mettent à jour `parametres_systeme`.

### Comment comprendre les relations

Une relation **un-pour-un** (utilisateur ↔ organisateur) signifie qu’à chaque compte organisateur correspond un seul profil, et inversement.

Une relation **un-pour-plusieurs** (organisateur ↔ déclarations, ou déclaration ↔ paiements) signifie qu’un parent peut avoir plusieurs enfants.

Une relation **un-pour-zéro-ou-un** (déclaration ↔ quittance) signifie que l’enfant est optionnel au début, puis unique quand il existe.

Les clés étrangères (colonnes `…_id`) sont le fil concret de ces relations. Sans elles, le site ne saurait pas afficher « mes déclarations » ni empêcher un organisateur de voir le dossier d’un autre.

### Ce qui n’est pas dans la base

Le PDF de quittance et l’affiche d’événement sont des fichiers sur le disque du serveur ; la base ne garde que les chemins. La session de connexion est gérée par Flask-Login à partir de l’id `utilisateur`. Le mot de passe en clair n’existe nulle part en base. Sur Render, si un PDF disparaît du disque éphémère, l’application peut le régénérer grâce aux données encore présentes dans `quittance` et `declaration`.

### Exemple concret raconté

Aminata s’inscrit : compte dans `utilisateur` et profil dans `organisateur`. Elle déclare un concert avec trois artistes : une `declaration` au statut `nouvelle`, trois `liste_artiste`, une notification. L’agent Issa fixe un tarif de 15 000 et une redevance de 5 000 : total 20 000 dans `evaluation_agent`. Aminata paie d’abord 12 000 au guichet : un `paiement` avec solde après 8 000 et un `arriere` de 8 000. Elle paie ensuite les 8 000 restants : second `paiement`, solde à zéro, création de la `quittance`, statut `quittance_delivree`. Si elle avait coché « promouvoir », le concert apparaît alors sur la page publique.

### Résumé en une phrase par table

La table `utilisateur` dit qui se connecte et avec quel rôle. La table `organisateur` dit quel est le profil métier et l’état du compte. La table `declaration` est le dossier événement et son avancement. La table `liste_artiste` liste les artistes rattachés au dossier. La table `evaluation_agent` fixe le montant BBDA (tarif + redevance). La table `paiement` enregistre les encaissements confirmés par l’agent. La table `quittance` est la preuve PDF une fois tout payé. La table `arriere` représente le reste dû qui peut bloquer le compte. La table `notification` journalise les emails automatiques. La table `alerte_surveillance` signale qu’un compte surveillé s’est reconnecté. La table `message_contact` stocke les messages du formulaire public Contact. La table `parametres_systeme` conserve les réglages admin (seuil, délais).

---

## Diagramme des relations

```
┌─────────────────┐         ┌──────────────────┐
│   utilisateur   │ 1 ───── 1│   organisateur   │
│─────────────────│         │──────────────────│
│ id (PK)         │         │ id (PK)           │
│ nom             │         │ utilisateur_id FK │
│ prenom          │         │ qualite           │
│ email (unique)  │         │ telephone         │
│ mot_de_passe    │         │ statut_compte     │
│ role            │         └────────┬─────────┘
│ statut          │                  │ 1
│ date_inscription│                  │
└────────┬────────┘                  │ N
         │                  ┌────────┴─────────┐
         │ 1                │    declaration    │
         │                  │──────────────────│
         │ N                │ id (PK)           │
┌────────┴────────┐         │ organisateur_id FK│
│  notification   │         │ nom_demandeur     │
│─────────────────│         │ prenom_demandeur  │
│ id (PK)         │         │ qualite_demandeur │
│ destinataire_id │         │ telephone         │
│ type_notif      │         │ email             │
│ sujet           │         │ nature_manifest.  │
│ message         │         │ nom_artiste_event │
│ canal           │         │ nom_salle         │
│ date_envoi      │         │ adresse           │
│ statut          │         │ ville             │
└─────────────────┘         │ date_evenement    │
                            │ duree_heures      │
                            │ capacite_accueil  │
                            │ entree_payante    │
                            │ nature_diffusion  │
                            │ autres_details    │
                            │ promouvoir        │
                            │ description_pub.  │
                            │ affiche_path      │
                            │ contact_public    │
                            │ statut            │
                            │ date_soumission   │
                            │ date_modification │
                            └──────┬───────────┘
                                   │ 1
                    ┌──────────────┼──────────────┐
                    │              │              │
                    │ N            │ 1            │ N
         ┌──────────┴───┐  ┌──────┴──────┐  ┌───┴────────────┐
         │ liste_artiste│  │eval_agent   │  │   paiement     │
         │──────────────│  │─────────────│  │────────────────│
         │ id (PK)      │  │ id (PK)     │  │ id (PK)        │
         │ declaration_id│  │ decl_id FK  │  │ declaration_id │
         │ nom_artiste  │  │ agent_id FK │  │ mode_paiement  │
         │ discipline   │  │ tarif       │  │ numero_cheque  │
         └──────────────┘  │ redevance   │  │ montant_chiffr │
                           │ date_eval   │  │ montant_lettres│
                           │ commentaire │  │ type_paiement  │
                           └─────────────┘  │ solde_apres    │
                                            │ date_paiement  │
                                            │ confirme_par FK│
                                            └───────┬────────┘
                                                    │ N (soldé → 1 quittance)
                                            ┌───────┴────────┐
                                            │   quittance    │
                                            │────────────────│
                                            │ id (PK)        │
                                            │ declaration_id │
                                            │ numero_quittance│
                                            │ droit_annuel   │
                                            │ droit_arriere  │
                                            │ droit_exigible │
                                            │ droits_type    │
                                            │ droits_montant │
                                            │ etiq_nombre    │
                                            │ etiq_montant   │
                                            │ penal_type     │
                                            │ penal_montant  │
                                            │ somme_chiffres │
                                            │ somme_lettres  │
                                            │ date_delivrance│
                                            │ agent_id FK    │
                                            │ fichier_pdf    │
                                            └────────────────┘

┌──────────────────┐         ┌──────────────────────┐
│    organisateur  │ 1 ─── N │      arriere         │
│ (déjà défini)    │         │──────────────────────│
└──────────────────┘         │ id (PK)              │
         │                   │ organisateur_id FK    │
         │ 1                 │ declaration_id FK     │
         │                   │ montant_du            │
         │ N                 │ date_echeance         │
┌────────┴─────────┐         │ statut                │
│alerte_surveillance│         │ date_reglement        │
│──────────────────│         │ derniere_notification │
│ id (PK)          │         └──────────────────────┘
│ organisateur_id  │
│ date_marquage    │         ┌──────────────────────┐
│ marque_par FK    │         │   message_contact    │
│ traitee          │         │──────────────────────│
│ date_traitement  │         │ id (PK)              │
│ traite_par FK    │         │ nom                  │
│ commentaire      │         │ email                │
└──────────────────┘         │ sujet                │
                             │ message              │
                             │ date_envoi           │
                             │ traite               │
                             └──────────────────────┘
```

---

## Détail de chaque table

Ci-dessous : colonnes techniques. Les explications métier (lien avec le site) sont dans la section « Fonctionnement en lien avec le site » plus haut.

### 1. `utilisateur`

Compte de connexion (organisateur, agent ou admin). Alimente inscription / connexion. Un agent ou un admin n’a pas de ligne dans `organisateur`.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant unique |
| `nom` | VARCHAR(100) | NOT NULL | Nom de famille |
| `prenom` | VARCHAR(100) | NOT NULL | Prénom |
| `email` | VARCHAR(150) | UNIQUE, NOT NULL | Email de connexion |
| `mot_de_passe` | VARCHAR(255) | NOT NULL | Hash bcrypt |
| `role` | ENUM | NOT NULL | organisateur / agent / admin |
| `statut` | ENUM | DEFAULT actif | actif / inactif |
| `date_inscription` | DATETIME | DEFAULT NOW() | Date de création |

---

### 2. `organisateur`

Profil métier lié 1—1 à un `utilisateur` de rôle organisateur. Le `statut_compte` pilote le blocage / la surveillance côté site.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `utilisateur_id` | INT | FK, UNIQUE, NOT NULL | Lien vers utilisateur |
| `qualite` | VARCHAR(100) | NOT NULL | Qualité du demandeur |
| `telephone` | VARCHAR(20) | NOT NULL | Numéro de téléphone |
| `statut_compte` | ENUM | DEFAULT actif | actif / arriere / bloque / surveillance |

---

### 3. `declaration`

Dossier événement central. Le champ `statut` commande les droits organisateur / agent et l’éventuelle publication publique (avec `promouvoir`).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `organisateur_id` | INT | FK, NOT NULL | Lien vers organisateur |
| `nom_demandeur` | VARCHAR(100) | NOT NULL | Nom du demandeur |
| `prenom_demandeur` | VARCHAR(100) | NOT NULL | Prénom du demandeur |
| `qualite_demandeur` | VARCHAR(100) | NOT NULL | Qualité |
| `telephone` | VARCHAR(20) | NOT NULL | Téléphone |
| `email` | VARCHAR(150) | NOT NULL | Email |
| `nature_manifestation` | VARCHAR(100) | NOT NULL | Concert / Festival / etc. |
| `nom_artiste_evenement` | VARCHAR(200) | NOT NULL | Nom artiste ou événement |
| `nom_salle` | VARCHAR(200) | NOT NULL | Lieu de la manifestation |
| `adresse` | VARCHAR(200) | NOT NULL | Adresse |
| `ville` | VARCHAR(100) | NOT NULL | Ville |
| `date_evenement` | DATETIME | NOT NULL | Date et heure de l'événement |
| `duree_heures` | FLOAT | NOT NULL | Durée en heures |
| `capacite_accueil` | INT | NOT NULL | Nombre de places |
| `entree_payante` | BOOLEAN | DEFAULT FALSE | Entrée payante ou gratuite |
| `nature_diffusion` | VARCHAR(200) | NOT NULL | vivante / mécanique / autres |
| `autres_details` | TEXT | NULL | Informations complémentaires |
| `promouvoir` | BOOLEAN | DEFAULT FALSE | Promouvoir sur la face publique |
| `description_publique` | TEXT | NULL | Description pour la page publique |
| `affiche_path` | VARCHAR(300) | NULL | Chemin de l'affiche uploadée |
| `contact_public` | BOOLEAN | DEFAULT FALSE | Afficher le contact publiquement |
| `statut` | ENUM | DEFAULT nouvelle | nouvelle / en_evaluation / montant_fixe / paiement_en_attente / payee / quittance_delivree / en_attente |
| `date_soumission` | DATETIME | DEFAULT NOW() | Date de soumission |
| `date_modification` | DATETIME | DEFAULT NOW() | Dernière modification |
| `commentaire_agent` | TEXT | NULL | Motif saisi par l'agent lors d'une mise en attente (RM-034, Prompt 10) |

---

### 4. `liste_artiste`

Artistes saisis sur le formulaire de déclaration (plusieurs lignes possibles par dossier).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `declaration_id` | INT | FK, NOT NULL | Lien vers déclaration |
| `nom_artiste` | VARCHAR(200) | NOT NULL | Nom de l'artiste |
| `discipline` | VARCHAR(100) | NULL | Discipline artistique |

---

### 5. `evaluation_agent`

Montant fixé manuellement par l’agent : Tarif + Redevance. Une évaluation par déclaration (`declaration_id` unique).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `declaration_id` | INT | FK, UNIQUE, NOT NULL | Lien vers déclaration |
| `agent_id` | INT | FK, NOT NULL | Agent qui a évalué |
| `tarif` | FLOAT | NOT NULL | Tarif fixé (FCFA) |
| `redevance` | FLOAT | NOT NULL | Redevance fixée (FCFA) |
| `date_evaluation` | DATETIME | DEFAULT NOW() | Date d'évaluation |
| `commentaire` | TEXT | NULL | Commentaire de l'agent |

---

### 6. `paiement`

Une déclaration peut avoir **plusieurs lignes de paiement** (versements successifs) —
la contrainte `UNIQUE` sur `declaration_id` a été retirée pour permettre le paiement
partiel en plusieurs fois (RM-047, RM-048). Le solde restant dû se calcule par
`montant total (RM-032) − SUM(montant_chiffres)` sur tous les paiements confirmés
de la déclaration ; `solde_apres` conserve ce solde au moment de chaque versement
à des fins d'audit/affichage, sans devoir le recalculer à chaque lecture.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `declaration_id` | INT | FK, NOT NULL | Lien vers déclaration (plusieurs paiements possibles) |
| `mode_paiement` | ENUM | NOT NULL | especes / cheque / orange_money |
| `numero_cheque` | VARCHAR(50) | NULL | Numéro si chèque |
| `montant_chiffres` | FLOAT | NOT NULL | Montant de ce versement, en chiffres (FCFA) |
| `montant_lettres` | VARCHAR(300) | NOT NULL | Montant de ce versement, en lettres |
| `type_paiement` | ENUM | DEFAULT integral | integral / partiel — indique si ce versement solde la déclaration |
| `solde_apres` | FLOAT | DEFAULT 0 | Solde restant dû après ce versement |
| `date_paiement` | DATETIME | DEFAULT NOW() | Date du paiement |
| `confirme_par` | INT | FK, NOT NULL | Agent confirmateur |

---

### 7. `quittance`

Preuve PDF créée automatiquement quand le solde de la déclaration atteint zéro. Une seule quittance par dossier.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `declaration_id` | INT | FK, UNIQUE, NOT NULL | Lien vers déclaration |
| `numero_quittance` | VARCHAR(20) | UNIQUE, NOT NULL | Numéro séquentiel (ex: 0049246) |
| `droit_annuel` | FLOAT | DEFAULT 0 | Droit annuel (FCFA) |
| `droit_arriere` | FLOAT | DEFAULT 0 | Droit arriéré (FCFA) |
| `droit_exigible` | FLOAT | DEFAULT 0 | Total exigible |
| `droits_type` | VARCHAR(100) | NULL | Type de droits |
| `droits_montant` | FLOAT | DEFAULT 0 | Montant des droits |
| `etiquettes_nombre` | INT | DEFAULT 0 | Nombre d'étiquettes |
| `etiquettes_montant` | FLOAT | DEFAULT 0 | Montant étiquettes |
| `penalites_type` | VARCHAR(100) | NULL | Type de pénalités |
| `penalites_montant` | FLOAT | DEFAULT 0 | Montant pénalités |
| `somme_totale_chiffres` | FLOAT | NOT NULL | Total payé en chiffres |
| `somme_totale_lettres` | VARCHAR(300) | NOT NULL | Total payé en lettres |
| `date_delivrance` | DATETIME | DEFAULT NOW() | Date de délivrance |
| `agent_id` | INT | FK, NOT NULL | Agent ayant délivré |
| `fichier_pdf_path` | VARCHAR(300) | NULL | Chemin du PDF généré |

---

### 8. `arriere`

Reste dû après un paiement partiel. Peut bloquer de nouvelles déclarations si le cumul dépasse le seuil admin.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `organisateur_id` | INT | FK, NOT NULL | Lien vers organisateur |
| `declaration_id` | INT | FK, NULL | Déclaration concernée |
| `montant_du` | FLOAT | NOT NULL | Montant dû (FCFA) |
| `date_echeance` | DATETIME | NOT NULL | Date limite de paiement |
| `statut` | ENUM | DEFAULT en_attente | en_attente / regle |
| `date_reglement` | DATETIME | NULL | Date du règlement |
| `derniere_notification` | DATETIME | NULL | Dernier rappel envoyé |

---

### 9. `notification`

Journal des emails automatiques. Un échec d’envoi ne remet pas en cause le traitement métier du dossier.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `destinataire_id` | INT | FK, NOT NULL | Utilisateur destinataire |
| `type_notification` | VARCHAR(50) | NOT NULL | confirmation / montant_fixe / etc. |
| `sujet` | VARCHAR(200) | NOT NULL | Sujet de l'email |
| `message` | TEXT | NOT NULL | Corps du message |
| `canal` | VARCHAR(20) | DEFAULT email | email (WhatsApp en perspective) |
| `date_envoi` | DATETIME | DEFAULT NOW() | Date d'envoi |
| `statut` | ENUM | DEFAULT en_attente | en_attente / envoyee / echouee |

---

### 10. `alerte_surveillance`

Alerte créée quand un organisateur placé sous surveillance se reconnecte.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `organisateur_id` | INT | FK, NOT NULL | Compte surveillé |
| `date_marquage` | DATETIME | DEFAULT NOW() | Date de marquage |
| `marque_par` | INT | FK, NULL | Agent ayant marqué |
| `traitee` | BOOLEAN | DEFAULT FALSE | Alerte traitée ou non |
| `date_traitement` | DATETIME | NULL | Date de traitement |
| `traite_par` | INT | FK, NULL | Agent traiteur |
| `commentaire` | TEXT | NULL | Commentaire |

---

### 11. `message_contact`

Messages du formulaire public Contact (visiteur sans compte possible).

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `nom` | VARCHAR(100) | NOT NULL | Nom de l'expéditeur |
| `email` | VARCHAR(150) | NOT NULL | Email de l'expéditeur |
| `sujet` | VARCHAR(200) | NOT NULL | Sujet du message |
| `message` | TEXT | NOT NULL | Corps du message |
| `date_envoi` | DATETIME | DEFAULT NOW() | Date d'envoi |
| `traite` | BOOLEAN | DEFAULT FALSE | Message traité par le BBDA |

---

### 12. `parametres_systeme`

Stocke les valeurs configurables par l'administrateur listées dans
`docs/REGLES_METIER.md` §9 (`SEUIL_ARRIERE`, `DELAI_NOTIFICATION`, etc.), pour
qu'elles soient modifiables depuis l'espace admin sans redéploiement du code.

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `cle` | VARCHAR(100) | UNIQUE, NOT NULL | Nom du paramètre (ex: `SEUIL_ARRIERE`) |
| `valeur` | VARCHAR(300) | NOT NULL | Valeur du paramètre (stockée en texte, castée selon le besoin) |
| `description` | VARCHAR(300) | NULL | Explication du paramètre |
| `modifie_par` | INT | FK, NULL | Administrateur ayant fait la dernière modification |
| `date_modification` | DATETIME | DEFAULT NOW() | Date de dernière modification |

Valeurs seedées au démarrage (`init_db.py`) : `SEUIL_ARRIERE=1000`, `DELAI_NOTIFICATION=7`.

---

## Index recommandés

```sql
-- Recherches fréquentes sur email
CREATE INDEX idx_utilisateur_email ON utilisateur(email);

-- Filtrage par statut des déclarations
CREATE INDEX idx_declaration_statut ON declaration(statut);
CREATE INDEX idx_declaration_date ON declaration(date_evenement);
CREATE INDEX idx_declaration_organisateur ON declaration(organisateur_id);
CREATE INDEX idx_declaration_promouvoir ON declaration(promouvoir, statut);

-- Suivi des arriérés
CREATE INDEX idx_arriere_statut ON arriere(statut);
CREATE INDEX idx_arriere_organisateur ON arriere(organisateur_id);

-- Notifications
CREATE INDEX idx_notification_statut ON notification(statut);

-- Alertes surveillance
CREATE INDEX idx_alerte_traitee ON alerte_surveillance(traitee);
```

---

## Statuts et transitions

### Statuts d'une déclaration

```
nouvelle → en_evaluation → montant_fixe → paiement_en_attente → payee → quittance_delivree
    ↓              ↓              ↓
en_attente    en_attente    en_attente
```

### Statuts d'un compte organisateur

```
actif ←→ arriere ←→ bloque
  ↕
surveillance
```

### Statuts d'un arriéré

```
en_attente → regle
```

### Statuts d'une notification

```
en_attente → envoyee
           → echouee
```

---

*Dernière mise à jour : 28 juillet 2026 — ajout de la section « Fonctionnement en lien avec le site ». *
