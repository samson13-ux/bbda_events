# DATABASE_SCHEMA.md — Schéma de la base de données BBDA Events

---

## Informations générales

- **SGBD** : MySQL
- **Base de données** : `bbda_events_db`
- **Encodage** : `utf8mb4_unicode_ci`
- **Moteur** : InnoDB
- **Nombre de tables** : 12

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

### 1. `utilisateur`

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

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `utilisateur_id` | INT | FK, UNIQUE, NOT NULL | Lien vers utilisateur |
| `qualite` | VARCHAR(100) | NOT NULL | Qualité du demandeur |
| `telephone` | VARCHAR(20) | NOT NULL | Numéro de téléphone |
| `statut_compte` | ENUM | DEFAULT actif | actif / arriere / bloque / surveillance |

---

### 3. `declaration`

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

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Identifiant |
| `declaration_id` | INT | FK, NOT NULL | Lien vers déclaration |
| `nom_artiste` | VARCHAR(200) | NOT NULL | Nom de l'artiste |
| `discipline` | VARCHAR(100) | NULL | Discipline artistique |

---

### 5. `evaluation_agent`

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

*Dernière mise à jour : Juillet 2026*
