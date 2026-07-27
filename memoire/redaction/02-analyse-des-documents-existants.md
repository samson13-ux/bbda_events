# Analyse de l'existant et arbitrages rendus

Avant de démarrer le développement, une phase d'analyse du dossier de
préparation (documents rédigés en amont : cahier des charges, schéma de base
de données, règles métier, guide de développement) a été menée. Cette analyse
a permis de détecter plusieurs **incohérences entre documents**, normales à ce
stade d'un projet (documents rédigés à des moments différents, certains non
encore validés par le maître de stage), et de trancher pour pouvoir avancer.

**Pourquoi ce chapitre est utile pour le mémoire** : il illustre une démarche
d'ingénierie logicielle rigoureuse (revue de cohérence documentaire avant
codage) et donne des réponses toutes prêtes si le jury demande "pourquoi
avez-vous fait ce choix technique précis ?".

## 1. Inventaire des documents de préparation

| Document | Rôle |
|---|---|
| `guide/Protocole_Stage_V1.pdf` | Cadrage académique officiel du stage (objectifs, hypothèses, méthodologie) |
| `guide/CahierDesCharges_V2_BBDA_Events.docx` | Spécifications fonctionnelles et techniques détaillées |
| `guide/Guide_Complet_Dev_BBDA_Events_V2.docx` | Suite de 20 prompts destinés à un assistant IA pour générer le code, étape par étape |
| `guide/cursor_comprehension.odt` | Échange de clarification (questions/réponses) mené en amont avec un assistant IA |
| `../docs/ARCHITECTURE.md` | Architecture technique cible (arborescence, blueprints, flux de données) |
| `../docs/DATABASE_SCHEMA.md` | Modèle de données détaillé (11 tables à l'origine, 12 après ajustement) |
| `../docs/REGLES_METIER.md` | Règles de gestion numérotées (RM-001 à RM-103) |
| `database/schema.sql` + `schema_diagram.pdf` | Script SQL et diagramme ER générés via dbdiagram.io |
| `../archives/../archives/AI_RULES.md` | Contraintes permanentes imposées à tout assistant IA travaillant sur le code |
| `images/*.jpg` | Photos d'une quittance BBDA physique réelle, utilisées comme référence pour PROMPT 12 (génération PDF) |

## 2. Incohérences détectées et arbitrages

### 2.1. Contradiction de stack technique

- `../archives/../archives/AI_RULES.md` et `../docs/ARCHITECTURE.md` imposent explicitement **Flask +
  Jinja2 + JavaScript vanilla**, avec interdiction de React/Vue.
- Le seul code présent dans le dossier était une **maquette Next.js/React**
  (`frontend-reference/`, générée via l'outil v0.app).

**Arbitrage retenu** : la maquette Next.js reste une **référence visuelle
uniquement** — elle sert à s'inspirer du design pour reconstruire les pages en
HTML/Jinja2. Le code React n'est pas conservé comme frontend final.

**Justification pour la soutenance** : le protocole de stage et le cahier des
charges, documents contractuels avec l'institution d'accueil, priment sur un
prototype visuel généré à titre exploratoire. De plus, une architecture Flask
monolithique (Jinja2 côté serveur) est plus simple à maintenir et à déployer
pour un environnement BBDA sans infrastructure Node.js, et correspond à la
stack validée dans le protocole officiel.

### 2.2. Le guide de développement se nomme "18 prompts" mais en contient 20

Le titre du document (`Guide_Complet_Dev_BBDA_Events_V2`) et l'en-tête de
chaque étape ("Étape X / 18") annoncent 18 prompts, mais le corps du document
va en réalité jusqu'au **Prompt 20** (ajout tardif des Prompts 18-19 sur la
face publique et 20 sur les tests/données de démonstration).
**Arbitrage** : traiter le guide comme un plan à 20 étapes, l'intitulé "18"
étant une coquille de version non mise à jour.

### 2.3. Clés étrangères inversées dans `database/schema.sql`

Le script SQL généré via dbdiagram.io comportait des clés étrangères dans le
mauvais sens (ex. `utilisateur.id → organisateur` au lieu de
`organisateur.utilisateur_id → utilisateur.id`), rendant ce script
non exécutable tel quel.

**Arbitrage retenu** : ne pas corriger ce script SQL à la main. Les modèles
définitifs sont écrits directement en **SQLAlchemy** (`models.py`), qui fait
foi. Le script SQL et son diagramme restent une référence historique du
brainstorming de modélisation, pas la source de vérité.

### 2.4. Absence de table pour les paramètres système

`../docs/REGLES_METIER.md` §9 mentionne des valeurs "paramétrables par
l'administrateur" (seuil d'arriéré, délai de rappel), mais le schéma de
données n'avait, à l'origine, aucune table pour les persister — elles
auraient été codées en dur.

**Arbitrage retenu** : ajout d'une 12ᵉ table, `parametres_systeme`
(clé/valeur), pour que ces réglages soient réellement modifiables depuis
l'espace admin sans redéploiement de code. Voir
[04-base-de-donnees.md](04-base-de-donnees.md#12-parametres_systeme).

### 2.5. Conflit sur la règle d'échéance des arriérés

Deux sources donnaient une règle différente pour la date d'échéance d'un
arriéré :
- `../docs/REGLES_METIER.md` (RM-063) : échéance = date de fixation du montant
  par l'agent **+ 7 jours**.
- Une note du chat de clarification (`cursor_comprehension.odt`) suggérait :
  échéance = après la date de l'événement.

**Arbitrage retenu** : la règle officielle documentée (RM-063, fixation + 7
jours) est retenue comme définitive. La mention alternative est considérée
obsolète.

### 2.6. Paiement partiel : à supporter réellement

Le chat de clarification laissait la question ouverte ("les paiements
partiels sont-ils courants dans la pratique du BBDA, ou juste à prévoir 'au
cas où' ?"). **Arbitrage retenu** : les supporter pleinement — une
déclaration peut recevoir plusieurs versements successifs, avec suivi du
solde restant dû (voir RM-047/RM-048 et la table `paiement` en relation 1-N).

### 2.7. Incohérences de nommage/structure de dossiers

- `bbda_docs/README.md` faisait des liens relatifs vers `../docs/...` en
  supposant que `../docs/` était imbriqué dans `bbda_docs/`, alors que c'était un
  dossier frère à la racine — liens cassés en pratique.
- Le dossier `base de donnée` (espace + accent, non standard pour un chemin
  de projet) ne correspondait pas au nom `database/` attendu par
  `../docs/ARCHITECTURE.md`.

**Arbitrage retenu** : réorganisation complète du dossier racine (voir
journal, session du 2026-07-15) — noms cohérents sans espace ni accent,
`README.md`/`../archives/../archives/AI_RULES.md` déplacés à la racine du projet (convention standard),
`../docs/` laissé en dossier frère (les liens deviennent alors corrects sans
modification).

### 2.8. Distinction Tarif / Redevance insuffisamment définie

`../docs/REGLES_METIER.md` (RM-031/032) mentionnait deux montants — Tarif et
Redevance — sans les définir clairement au-delà de "montants fixés par
l'agent". Le chat de clarification apportait une définition plus fine (tarif
= référence du barème interne, redevance = part complémentaire fixée selon le
contexte de l'événement) qui n'avait pas été formalisée dans la documentation
officielle.

**Arbitrage retenu** : cette distinction a été formalisée dans
`../docs/REGLES_METIER.md` §3.2 — voir [04-base-de-donnees.md](04-base-de-donnees.md)
et [05-regles-metier.md](05-regles-metier.md) pour le détail.

## 3. Ce qui reste à valider formellement

Points explicitement marqués "non validés" dans les documents sources, à ne
pas présenter comme définitifs dans le mémoire sans confirmation du maître de
stage :
- Les champs "Directeur de mémoire" et "Maître de stage" du protocole sont
  vides.
- `../docs/REGLES_METIER.md` se termine par *"Validé par : Maître de stage BBDA —
  À compléter après validation"*.
- Le cahier des charges a une section de signature (§17) non remplie.

**Recommandation pour le mémoire** : présenter les règles métier comme
"règles de gestion retenues pour le prototype, en cours de validation avec le
maître de stage" plutôt que comme un existant figé — cela reflète honnêtement
l'état du projet et anticipe une question de jury sur la méthodologie de
validation.
