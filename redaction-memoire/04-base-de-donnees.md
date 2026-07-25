# Modèle de données — justification détaillée

> Source normative : `docs/DATABASE_SCHEMA.md` (schéma) et `models.py`
> (implémentation SQLAlchemy). 12 tables, MySQL/InnoDB, `utf8mb4`.

## 1. Vue d'ensemble du modèle relationnel

```
Utilisateur (1) ──── (1) Organisateur
                            │ (1)
                            │
                       Declaration (N)
                       ├── ListeArtiste (N)
                       ├── EvaluationAgent (1)
                       ├── Paiement (N)         ← plusieurs versements possibles
                       └── Quittance (1)

Organisateur (1) ──── (N) Arriere
Organisateur (1) ──── (N) AlerteSurveillance
Utilisateur  (1) ──── (N) Notification
ParametresSysteme (table de configuration, indépendante)
MessageContact (table indépendante, formulaire de contact public)
```

**Pourquoi séparer `Utilisateur` et `Organisateur` en deux tables (et pas une
seule) ?** `Utilisateur` porte tout ce qui concerne l'authentification (email,
mot de passe, rôle) et est **commun aux trois rôles** (organisateur, agent,
admin). `Organisateur` porte les informations métier spécifiques à ce rôle
(qualité du demandeur, téléphone, statut du compte vis-à-vis des arriérés).
Un agent ou un administrateur n'a pas besoin de ces colonnes. Cette séparation
évite des colonnes `NULL` en masse pour les rôles qui n'en ont pas besoin, et
respecte le principe de responsabilité unique appliqué aux données.

## 2. Détail table par table

### 1. `utilisateur`
Compte de connexion générique. `role` (organisateur / agent / admin)
détermine les permissions d'accès (voir `docs/ARCHITECTURE.md` §6). Le mot de
passe est **toujours stocké haché** (bcrypt, jamais en clair — exigence de
`AI_RULES.md` §5).

### 2. `organisateur`
Profil métier 1-1 avec un utilisateur de rôle `organisateur`.
`statut_compte` (actif / arriere / bloque / surveillance) est le levier
principal du **module de gestion des arriérés** : c'est ce champ qui
détermine si un organisateur peut soumettre une nouvelle déclaration
(RM-010, RM-074).

### 3. `declaration`
Le cœur du système — reproduit fidèlement les champs de la fiche de
déclaration papier existante (nom/prénom/qualité du demandeur, nature de la
manifestation, lieu, date, capacité d'accueil, diffusion vivante/mécanique...).
Deux groupes de champs à distinguer pour la soutenance :
- **Champs de déclaration** (obligatoires, remplis par l'organisateur).
- **Champs de promotion publique** (`promouvoir`, `description_publique`,
  `affiche_path`, `contact_public`) — optionnels, activés seulement si
  l'organisateur souhaite apparaître sur la face publique du site (RM-020 à RM-025).

`statut` trace le cycle de vie complet de la déclaration (voir diagramme
d'états ci-dessous).

### 4. `liste_artiste`
Relation 1-N avec `declaration` : un événement peut avoir plusieurs artistes
programmés, chacun avec sa discipline (musique, danse, théâtre...).

### 5. `evaluation_agent`
Enregistre la décision de l'agent : **Tarif** + **Redevance** (voir
définitions dans [05-regles-metier.md](05-regles-metier.md#tarif-vs-redevance)).
Relation 1-1 avec `declaration` (**une seule évaluation par déclaration** —
si l'agent doit corriger un montant, il modifie cette même ligne, il n'en crée
pas une nouvelle : pas d'historique de versions à ce stade du prototype).

### 6. `paiement` — la décision de modélisation la plus significative

**Choix initial du schéma (avant arbitrage)** : relation **1-1** avec
`declaration` (une seule ligne de paiement possible, avec un champ
`reste_a_payer`). Cela ne permettait pas d'enregistrer plusieurs versements.

**Choix retenu (après arbitrage, voir
[02-analyse-des-documents-existants.md](02-analyse-des-documents-existants.md#26-paiement-partiel--à-supporter-réellement))** :
relation **1-N** — une déclaration peut recevoir plusieurs paiements
(versements successifs). Chaque ligne `paiement` connaît son propre montant
(`montant_chiffres`) et le **solde restant après ce versement précis**
(`solde_apres`), calculé côté application comme :

```
solde restant = montant total (Tarif + Redevance) − somme des paiements confirmés
```

**Pourquoi stocker `solde_apres` plutôt que de le recalculer à chaque
lecture ?** C'est un compromis dénormalisation/performance classique : le
recalcul par `SUM()` reste toujours possible et fait foi en cas de doute, mais
conserver la valeur au moment du versement évite un recalcul à chaque
affichage de l'historique des paiements et sert de traçabilité/audit (on sait
exactement ce qu'il restait à payer après chaque versement, même si des
versements futurs sont ajoutés).

### 7. `quittance`
Générée automatiquement (jamais manuellement, RM-050) uniquement **quand le
solde atteint zéro** (RM-048) — donc potentiellement après plusieurs
paiements. Reproduit la structure du document physique BBDA (champs
`droit_annuel`, `droit_arriere`, `etiquettes_*`, `penalites_*` — vocabulaire
directement issu de la quittance papier réelle photographiée, voir
`images/*.jpg`). Le `numero_quittance` est séquentiel et unique (RM-051).

### 8. `arriere`
Une ligne par montant dû non réglé. `date_echeance` = date de fixation du
montant + 7 jours (RM-063, règle arbitrée — voir
[02-analyse-des-documents-existants.md](02-analyse-des-documents-existants.md#25-conflit-sur-la-règle-déchéance-des-arriérés)).
`declaration_id` est **nullable** : un arriéré est toujours lié à un
organisateur, mais reste rattachable même si la déclaration d'origine est
supprimée ou dans des cas de régularisation globale du compte.

### 9. `notification`
Journal de tous les emails envoyés (RM-100) — y compris les échecs d'envoi
(`statut = echouee`), pour que l'application ne plante jamais sur un problème
SMTP (RM-101). Utile aussi comme preuve d'envoi en cas de litige avec un
organisateur ("je n'ai jamais reçu l'email").

### 10. `alerte_surveillance`
Ligne créée quand un compte marqué "sous surveillance" (organisateur
introuvable, suspicion de fraude) se reconnecte — déclenche une alerte
immédiate visible par tous les agents et l'admin (RM-081, badge rouge au
tableau de bord).

### 11. `message_contact`
Table indépendante, sans lien avec le reste du modèle — simple formulaire de
contact de la face publique.

### 12. `parametres_systeme`
Ajoutée pendant l'arbitrage (absente du schéma d'origine). Stocke en base les
valeurs configurables par l'admin (`SEUIL_ARRIERE`, `DELAI_NOTIFICATION`) sous
forme clé/valeur, avec traçabilité de qui a modifié quoi et quand
(`modifie_par`, `date_modification`). **Argument de conception** : évite de
redéployer le code pour changer un seuil métier — décision purement
opérationnelle qui ne doit pas nécessiter l'intervention d'un développeur.

## 3. Diagrammes d'état (cycle de vie des entités)

### Déclaration
```
nouvelle → en_evaluation → montant_fixe → paiement_en_attente → payee → quittance_delivree
    ↓              ↓              ↓
en_attente    en_attente    en_attente
```

### Compte organisateur
```
actif ←→ arriere ←→ bloque
  ↕
surveillance
```

### Arriéré
```
en_attente → regle
```

## 4. Index et performance

Index déclarés (cf. `docs/DATABASE_SCHEMA.md` §"Index recommandés") sur
toutes les colonnes de recherche fréquente : `email` (connexion), `statut` et
`date_evenement` de `declaration` (tableaux de bord), `organisateur_id` et
`statut` de `arriere` (module arriérés), `statut` de `notification`,
`traitee` de `alerte_surveillance`. Choix guidé par `AI_RULES.md` §4
("toujours déclarer les index sur FK et colonnes filtrées").

## 5. Implémentation SQLAlchemy — extrait représentatif

```python
class Paiement(db.Model):
    __tablename__ = "paiement"

    id = db.Column(db.Integer, primary_key=True)
    declaration_id = db.Column(db.Integer, db.ForeignKey("declaration.id"), nullable=False, index=True)
    mode_paiement = db.Column(db.Enum("especes", "cheque", "orange_money", name="mode_paiement_enum"), nullable=False)
    montant_chiffres = db.Column(db.Float, nullable=False)
    type_paiement = db.Column(db.Enum("integral", "partiel", name="type_paiement_enum"), default="integral")
    solde_apres = db.Column(db.Float, default=0)
    ...
    declaration = db.relationship("Declaration", back_populates="paiements")
```

Point technique à savoir expliquer : `declaration_id` n'a **pas** de
contrainte `unique=True` (contrairement à `evaluation_agent.declaration_id`
ou `quittance.declaration_id`, qui restent en 1-1) — c'est précisément ce qui
autorise plusieurs lignes de paiement pour une même déclaration.
