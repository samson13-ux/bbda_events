<!--
CE FICHIER EST LE MÉMOIRE EN COURS DE RÉDACTION (et non une note technique comme
les fichiers 01 à 07 de ce dossier, qui restent la « matière première »).

Consignes pour toute IA qui reprend ce projet (voir aussi AI_RULES.md, section 12) :
- Ce document doit être mis à jour À CHAQUE nouvelle étape de développement
  (nouveau "Prompt" du guide de dev terminé), sans attendre que l'utilisateur
  le demande explicitement.
- Chaque mise à jour de la Partie III (Résultats) doit inclure : un résumé de
  ce qui a été livré, une ou plusieurs captures d'écran/photos pertinentes
  (voir dossier `screenshots/`), et une mise à jour de la "Liste des figures".
- Le texte doit rester rédigé dans un style académique (phrases complètes,
  temps du récit cohérent, pas de listes à puces télégraphiques comme dans le
  journal technique) — reformuler, ne pas copier-coller brut depuis
  06-journal-de-bord-technique.md.
- Les passages encore incomplets sont marqués [À COMPLÉTER : ...] : ne pas les
  supprimer sans les remplacer par un contenu réel.
- Respecter les normes de forme du cours "Cours_Rédaction scientifique.pptx"
  (Université Aube Nouvelle, Initiation à la méthodologie de recherche) :
  Times New Roman 12-13, interligne 1,5, marges 2,5 à 3 cm, texte justifié,
  pagination en chiffres romains jusqu'au sommaire puis en chiffres arabes à
  partir de l'introduction. Ces normes s'appliquent à la mise en forme finale
  (Word/LibreOffice) ; ce fichier Markdown sert de brouillon de contenu.
-->

# MÉMOIRE DE FIN DE CYCLE
## Conception et développement d'une plateforme web de gestion et de suivi des déclarations d'événements culturels occasionnels au Bureau Burkinabè du Droit d'Auteur (BBDA)

*Brouillon en cours de rédaction — document vivant, complété au fur et à mesure de l'avancement du projet BBDA Events.*

---

## PREMIÈRE DE COUVERTURE / PAGE DE TITRE

[À COMPLÉTER PAR L'ÉTUDIANT — informations institutionnelles exactes]

- Nom de l'université / établissement : Université Aube Nouvelle *(à confirmer)*
- Filière / Licence : *(à préciser — Licence 3, à confirmer sur la base du cours de méthodologie fourni)*
- Titre du mémoire : Conception et développement d'une plateforme web de gestion et de suivi des déclarations d'événements culturels occasionnels au BBDA
- Présenté par : *(nom de l'étudiant)*
- Structure d'accueil du stage : Bureau Burkinabè du Droit d'Auteur (BBDA) — Direction de l'Exploitation, de la Perception et des Affaires Juridiques (DEPAJ)
- Maître de stage : *(nom, fonction)*
- Encadrant académique : *(nom, fonction)*
- Année académique : *(à préciser)*
- Date de soutenance : *(à préciser)*

*(Page de garde institutionnelle — logo de l'université, à retirer/adapter selon le modèle imposé par l'établissement, cf. cours de méthodologie, diapositive 23.)*

---

## DÉDICACE

[À COMPLÉTER PAR L'ÉTUDIANT — texte personnel, une page, généralement courte]

---

## REMERCIEMENTS

[À COMPLÉTER PAR L'ÉTUDIANT — remerciements à l'université, au maître de stage
BBDA, à l'encadrant académique, au personnel de la DEPAJ, à la famille/proches.
Rester sobre et sincère, éviter les formules trop génériques.]

---

## SOMMAIRE

*(Table des matières simplifiée à un ou deux niveaux, à régénérer automatiquement
lors de la mise en forme finale du document. Version indicative actuelle :)*

- Introduction générale
- Chapitre 1 : Cadre conceptuel et étude de l'existant
- Chapitre 2 : Matériel et méthodes
- Chapitre 3 : Présentation et analyse des résultats
- Conclusion générale
- Références bibliographiques
- Annexes

---

## LISTE DES FIGURES

*(Numérotation provisoire, un identifiant par capture d'écran déjà produite dans
`screenshots/`. À renuméroter dans l'ordre définitif d'apparition lors de la
mise en forme finale.)*

| N° | Fichier | Légende |
|---|---|---|
| 1 | `screenshots/07-accueil-v2.png` | Page d'accueil publique de la plateforme BBDA Events |
| 2 | `screenshots/02-inscription.png` | Formulaire d'inscription d'un organisateur |
| 3 | `screenshots/03-connexion.png` | Formulaire de connexion |
| 4 | `screenshots/08-flash-erreur.png` | Exemple de message d'erreur (compte inconnu) |
| 5 | `screenshots/09-dashboard-orga1.png` | Tableau de bord d'un organisateur avec déclarations en cours |
| 6 | `screenshots/10-dashboard-orga4-bloque.png` | Tableau de bord d'un organisateur au compte bloqué (bannière d'arriéré) |
| 7 | `screenshots/11-formulaire-concert.png` | Formulaire de déclaration d'un concert |
| 8 | `screenshots/12-formulaire-festival-artistes.png` | Formulaire de déclaration d'un festival avec plusieurs artistes |
| 9 | `screenshots/13-formulaire-erreurs.png` | Validation des erreurs de saisie sur le formulaire de déclaration |
| 10 | `screenshots/14-apres-soumission.png` | Confirmation après soumission d'une déclaration |
| 11 | `screenshots/15-detail-orga3-0.png` | Page de détail d'une déclaration — vue d'ensemble |
| 12 | `screenshots/15-detail-orga3-1.png` | Page de détail d'une déclaration — chronologie du traitement |
| 13 | `screenshots/16-detail-montant-fixe.png` | Détail d'une déclaration après fixation du montant par l'agent |
| 14 | `screenshots/17-dashboard-agent.png` | Tableau de bord de l'agent BBDA |
| 15 | `screenshots/18-agent-surveillance.png` | Liste des comptes organisateurs sous surveillance |
| 16 | `screenshots/19-agent-arrieres.png` | Liste des organisateurs en situation d'arriéré |
| 17 | `screenshots/20-agent-traitement.png` | Page de traitement d'une déclaration par l'agent (fixation du montant) |
| 18 | `screenshots/21-avant-validation-total.png` | Calcul en temps réel du montant total (tarif + redevance) |
| 19 | `screenshots/22-dashboard-agent-apres.png` | Tableau de bord agent après fixation du montant |
| 20 | `screenshots/23-dashboard-organisateur-apres.png` | Tableau de bord organisateur après fixation du montant |
| 21 | `screenshots/24-formulaire-paiement-vide.png` | Formulaire de confirmation de paiement (vierge) |
| 22 | `screenshots/25-formulaire-paiement-rempli.png` | Formulaire de confirmation de paiement rempli |
| 23 | `screenshots/26-dashboard-agent-apres-paiement.png` | Tableau de bord agent après encaissement du paiement |
| 24 | `screenshots/27-dossier-apres-paiement.png` | Détail de la déclaration après paiement (statut "quittance délivrée") |
| 25 | `screenshots/30-quittance-pdf-v3.png` | Quittance PDF générée automatiquement (version finale) |
| 26 | `screenshots/31-quittance-partiel.png` | Quittance PDF pour un paiement partiel (reste à payer) |
| 27 | `screenshots/32-detail-avec-bouton-telecharger.png` | Bouton de téléchargement de la quittance depuis l'espace organisateur |
| 28 | `screenshots/33-email-montant-fixe.png` | Email automatique envoyé à l'organisateur lors de la fixation du montant |
| 29 | `screenshots/34-detail-evenement-public.png` | Page de détail d'un événement sur la face publique |
| 30 | `screenshots/35-formulaire-promotion.png` | Section Promotion publique du formulaire de déclaration |

*(D'autres captures existent dans `screenshots/` — versions intermédiaires
01, 04, 05, 06, 28, 29 notamment — conservées comme preuves d'itération pour
la soutenance mais non reprises toutes dans le corps du texte.)*

---

# INTRODUCTION GÉNÉRALE

## Généralités sur le thème

La gestion collective des droits d'auteur consiste, pour une organisation
habilitée, à percevoir pour le compte des créateurs les redevances dues par
toute personne exploitant leurs œuvres, puis à leur en reverser le produit.
Au Burkina Faso, cette mission est assurée par le **Bureau Burkinabè du Droit
d'Auteur (BBDA)**, institution publique chargée de la protection et de la
gestion collective des droits d'auteur et des droits voisins. Le BBDA
distingue deux grandes catégories d'utilisateurs d'œuvres protégées : les
**utilisateurs permanents** (radios, télévisions, débits de boissons...), qui
exploitent des œuvres de manière continue et doivent obtenir une autorisation
préalable, et les **organisateurs d'événements culturels occasionnels**
(concerts, festivals, galas, spectacles...), qui doivent simplement déclarer
leur événement avant sa tenue. C'est cette seconde catégorie qui constitue le
périmètre du présent travail.

À ce jour, le BBDA dispose déjà d'un outil numérique dédié aux utilisateurs
permanents, mais le circuit de déclaration des événements occasionnels reste
**entièrement manuel et fondé sur des supports papier**, de la fiche de
déclaration remplie par l'organisateur jusqu'à la quittance délivrée après
paiement. C'est cette absence de couverture numérique qui a motivé le
stage à l'origine du présent mémoire, et qui a conduit à la conception d'une
plateforme baptisée **BBDA Events**.

## Justification du choix du sujet et motivations

Le choix de ce sujet répond à un besoin concret exprimé par la structure
d'accueil du stage : moderniser un processus administratif encore
intégralement papier, source de délais de traitement allongés et d'une
charge administrative importante pour les agents de la **Direction de
l'Exploitation, de la Perception et des Affaires Juridiques (DEPAJ)**. Sur le
plan personnel et académique, ce sujet permet de mobiliser des compétences en
conception de systèmes d'information (modélisation de données, architecture
logicielle), en développement web (back-end et front-end) et en gestion de
projet (recueil de besoins, arbitrages fonctionnels, tests), tout en
travaillant sur un cas réel à fort enjeu institutionnel : le recouvrement de
redevances qui bénéficient in fine aux créateurs burkinabè.

## Identification et formulation du problème

Le processus actuellement en vigueur au BBDA pour les événements occasionnels
se déroule de la manière suivante : l'organisateur se déplace physiquement au
siège du BBDA, remplit une fiche de déclaration papier, puis un agent de la
DEPAJ analyse les informations fournies et fixe manuellement, sur une fiche
d'évaluation, le montant de la redevance due (tarif de référence et
redevance complémentaire). Une fois le paiement effectué, l'organisateur
reçoit une quittance physique. Ce circuit entièrement manuel présente
plusieurs limites : des délais de traitement qui s'allongent avec le nombre
de dossiers, une charge de ressaisie et de classement papier importante pour
les agents, et surtout une **absence de suivi centralisé** qui empêche toute
vision globale des paiements effectués et tout suivi automatisé des
**arriérés** (redevances restées impayées, en tout ou en partie).

Le problème peut donc se formuler ainsi : *comment le BBDA peut-il fiabiliser,
accélérer et rendre traçable le traitement des déclarations d'événements
culturels occasionnels et le recouvrement des redevances associées, alors que
ce processus repose aujourd'hui intégralement sur des supports papier et des
opérations manuelles ?*

## Questions de recherche

- Question générale : dans quelle mesure la dématérialisation du processus de
  déclaration et de traitement des événements occasionnels peut-elle
  améliorer l'efficacité administrative du BBDA et la traçabilité des
  paiements ?
- Questions spécifiques :
  1. Quelles sont les étapes et les règles de gestion exactes du processus
     actuel de déclaration, d'évaluation et de paiement au BBDA ?
  2. Quelle architecture logicielle et quel modèle de données permettent de
     couvrir fidèlement ce processus tout en restant évolutifs ?
  3. Une plateforme web permet-elle de réduire les délais de traitement et de
     sécuriser le recouvrement des redevances, notamment via un mécanisme de
     suivi des arriérés et de notifications automatiques ?

## Énoncé des objectifs de recherche

**Objectif général.** Concevoir et développer une plateforme web de gestion
et de suivi des déclarations d'événements culturels occasionnels au BBDA,
couvrant l'ensemble du processus depuis la déclaration de l'organisateur
jusqu'à la délivrance de la quittance, en intégrant le suivi des paiements, la
gestion des arriérés et un système de notifications automatiques.

**Objectifs spécifiques.**
1. Analyser le processus actuel de déclaration, d'évaluation et de paiement
   des redevances au BBDA.
2. Identifier les besoins fonctionnels et techniques des agents de la DEPAJ
   et des organisateurs d'événements.
3. Concevoir l'architecture fonctionnelle et technique de la plateforme
   (modèle de données, règles métier, architecture logicielle).
4. Développer un module de déclaration en ligne pour les organisateurs.
5. Développer un espace agent permettant l'évaluation manuelle du montant dû
   et le suivi des paiements.
6. Développer un système de notifications automatiques par courrier
   électronique.
7. Développer un module de gestion des arriérés (alertes, mise sous
   surveillance des comptes débiteurs).
8. Développer un module de génération automatique de la quittance au format
   PDF.
9. Tester, valider et documenter l'ensemble de la plateforme développée.

## Formulation des hypothèses

**H1.** La dématérialisation du processus de déclaration — fondée sur une
simple déclaration de l'organisateur plutôt que sur une demande d'autorisation
préalable — permet de réduire significativement les délais de traitement et
la charge administrative des agents, tout en améliorant la traçabilité des
déclarations et des paiements.

**H2.** La mise en place d'un système centralisé de gestion des arriérés,
assorti d'alertes automatiques et d'un mécanisme de blocage des comptes
débiteurs, facilite le recouvrement des redevances impayées et réduit les
pertes financières pour le BBDA.

[À COMPLÉTER en fin de projet : confrontation explicite de H1 et H2 aux
résultats obtenus, dans la Conclusion générale.]

## Annonce du plan

Le présent mémoire s'articule en trois chapitres. Le premier chapitre pose le
cadre conceptuel du travail : il définit les notions clés mobilisées (droit
d'auteur, gestion collective, déclaration, redevance, quittance, arriéré) et
dresse l'état des lieux des outils existants au BBDA. Le deuxième chapitre
présente le matériel et la méthode : la démarche de collecte des besoins, les
choix techniques et architecturaux retenus, ainsi que la modélisation des
données et des règles de gestion. Le troisième chapitre présente et analyse
les résultats obtenus, module par module, avant une discussion critique de la
solution développée. Le mémoire se conclut par un bilan général, une
confrontation des hypothèses de recherche aux résultats obtenus, ainsi que des
perspectives d'amélioration.

---

# CHAPITRE 1 — CADRE CONCEPTUEL ET ÉTUDE DE L'EXISTANT

## 1.1 Définitions des concepts clés

Cette section reprend, en les développant, les définitions consignées dans le
glossaire de travail du projet (voir
[07-glossaire-et-references.md](07-glossaire-et-references.md)).

- **Bureau Burkinabè du Droit d'Auteur (BBDA)** : institution publique
  burkinabè chargée de la protection et de la gestion collective des droits
  d'auteur et des droits voisins ; elle perçoit, pour le compte des ayants
  droit, les redevances dues par les personnes physiques ou morales qui
  exploitent des œuvres protégées.
- **Direction de l'Exploitation, de la Perception et des Affaires Juridiques
  (DEPAJ)** : direction du BBDA en charge, notamment, du traitement des
  déclarations d'événements culturels occasionnels.
- **Événement culturel occasionnel** : manifestation ponctuelle (concert,
  festival, spectacle, gala...) donnant lieu à l'exploitation d'œuvres
  protégées, par opposition à l'exploitation permanente (radiodiffusion,
  débits de boissons avec diffusion musicale, etc.).
- **Déclaration** : acte par lequel un organisateur signale au BBDA la tenue
  prochaine d'un événement occasionnel ; contrairement aux utilisateurs
  permanents, l'organisateur occasionnel n'a pas à solliciter d'autorisation
  préalable, il déclare son événement.
- **Tarif** et **redevance** : le tarif est le montant de référence tiré du
  barème interne du BBDA selon le type d'événement ; la redevance est un
  montant complémentaire apprécié par l'agent selon le contexte spécifique de
  la manifestation (jauge, notoriété des artistes, prix des billets...) ; la
  somme des deux constitue le montant total dû par l'organisateur.
- **Quittance** : document délivré par le BBDA attestant du paiement de la
  redevance ; historiquement remise en main propre sur support papier, elle
  est produite au format PDF par la plateforme développée.
- **Arriéré** : partie de la redevance restée impayée après un paiement
  partiel, ou totalité de la redevance en l'absence de tout paiement.
- **Compte sous surveillance** : statut appliqué à un compte organisateur
  suspecté de fraude ou injoignable, destiné à déclencher une alerte
  automatique à sa prochaine connexion.

## 1.2 Approche théorique et empirique

[À COMPLÉTER : revue de littérature académique — travaux publiés sur la
gestion collective des droits d'auteur, la dématérialisation des services
administratifs publics en Afrique de l'Ouest, et les systèmes d'information
de gestion appliqués au recouvrement de créances. Cette revue doit, comme
l'exige la méthodologie du cours suivi, présenter les auteurs par nom et
année de publication (pas de citation littérale systématique), et se conclure
par une brève évaluation critique de l'apport de chaque référence par rapport
à la problématique du présent mémoire — voir
[07-glossaire-et-references.md](07-glossaire-et-references.md) pour le format
des références déjà retenu.]

Sur le plan empirique, l'analyse s'appuie principalement sur trois documents
internes fournis en cadrage du stage : le protocole de stage
(`guide/Protocole_Stage_V1.pdf`), le cahier des charges détaillé
(`guide/CahierDesCharges_V2_BBDA_Events.docx`) et un guide de développement
séquencé en vingt étapes (`guide/Guide_Complet_Dev_BBDA_Events_V2.docx`). Le
détail de l'analyse de ces documents, y compris les incohérences relevées
entre eux et les arbitrages rendus, figure dans le document de travail
[02-analyse-des-documents-existants.md](02-analyse-des-documents-existants.md).

## 1.3 État des lieux : un processus sans couverture numérique

Le BBDA dispose déjà d'une application dédiée à la gestion des utilisateurs
permanents (radios, télévisions, débits de boissons), mais aucun outil
numérique équivalent n'existe pour les organisateurs d'événements
occasionnels : tout le circuit — déclaration, évaluation, paiement,
quittance — repose sur des fiches papier et un traitement manuel par les
agents de la DEPAJ. Ce constat, central pour situer la contribution du
présent travail, doit être posé clairement : il ne s'agit pas d'une refonte
de l'application existante du BBDA, mais de la couverture numérique d'un
processus jusque-là resté entièrement manuel.

---

# CHAPITRE 2 — MATÉRIEL ET MÉTHODES

## 2.1 Présentation de la structure d'accueil et du cadre de l'étude

Le stage s'est déroulé au sein du Bureau Burkinabè du Droit d'Auteur (BBDA),
et plus précisément au contact de la Direction de l'Exploitation, de la
Perception et des Affaires Juridiques (DEPAJ), service directement en charge
du traitement des déclarations d'événements occasionnels. [À COMPLÉTER :
présentation institutionnelle plus complète du BBDA — historique, missions
légales, organisation générale — et description du service d'accueil au sein
de la DEPAJ, dates précises du stage.]

## 2.2 Démarche méthodologique

Le travail a été conduit en quatre phases, conformément au protocole de
stage :

1. **Analyse** : observation du processus en vigueur à la DEPAJ, entretiens
   avec les agents, collecte des fiches papier de déclaration et
   d'évaluation utilisées en pratique.
2. **Conception** : modélisation du domaine (modèle de données relationnel,
   règles de gestion), définition de l'architecture logicielle.
3. **Réalisation** : développement itératif de la plateforme, module par
   module, suivant un guide de développement séquencé en vingt étapes
   (« prompts »), chaque étape faisant l'objet de tests automatisés et d'une
   vérification visuelle avant de passer à la suivante.
4. **Validation et documentation** : tests fonctionnels (unitaires et
   d'intégration bout-en-bout), retours du maître de stage, rédaction du
   présent mémoire.

[À COMPLÉTER : les diagrammes UML formels (cas d'utilisation, classes,
séquence, déploiement, activité) annoncés dans le protocole de stage restent
à produire — seuls le modèle de données relationnel
(`docs/DATABASE_SCHEMA.md`) et les règles métier (`docs/REGLES_METIER.md`,
`backend/statuts.py`) existent à ce stade. Il s'agit d'un livrable à ne pas
oublier avant la soutenance.]

## 2.3 Outils et choix techniques

| Catégorie | Choix retenu | Justification résumée |
|---|---|---|
| Langage / framework back-end | Python 3.13, Flask | Framework léger, non prescriptif, adapté à une architecture MVC explicite et à un périmètre fonctionnel maîtrisable en solo |
| Front-end | HTML5, CSS3, JavaScript vanilla | Pas de dépendance à un framework front lourd (React/Vue), conforme aux contraintes du cahier des charges et à la taille du projet |
| Base de données | MySQL (moteur InnoDB, encodage utf8mb4) | SGBD relationnel largement supporté, adapté à un modèle de données fortement relationnel (déclarations, paiements, arriérés) |
| ORM | SQLAlchemy | Évite l'écriture de SQL brut, sécurise les requêtes, facilite l'évolution du schéma |
| Authentification | Flask-Login + bcrypt | Gestion de session standard de l'écosystème Flask, hachage de mots de passe reconnu |
| Génération de documents | ReportLab | Génération programmatique de PDF avec un contrôle fin de la mise en page, nécessaire pour reproduire fidèlement la quittance papier existante |
| Notifications | Flask-Mail (journalisation interne en environnement de développement) | Intégration native à Flask ; en développement, les notifications sont consignées en base plutôt qu'effectivement envoyées, pour ne pas dépendre d'un compte SMTP réel |
| Architecture | MVC (Modèle-Vue-Contrôleur) avec Flask Blueprints et *factory pattern* | Sépare strictement logique métier (`backend/`) et présentation (`frontend/`), impose une organisation modulaire par domaine fonctionnel (auth, déclarations, agent, admin, exports, notifications) |
| Gestion de version | Git | Suivi de l'historique des modifications |
| Tests | pytest, Playwright (vérification visuelle) | Tests automatisés (unitaires et fonctionnels) et captures d'écran de non-régression |

La justification détaillée de chacun de ces choix, y compris les alternatives
écartées, est développée dans
[03-choix-techniques-et-architecture.md](03-choix-techniques-et-architecture.md).

## 2.4 Modélisation des données

Le modèle de données couvre les entités suivantes : utilisateurs
(`Utilisateur`), organisateurs (`Organisateur`), agents, déclarations
(`Declaration`), listes d'artistes associées à une déclaration
(`ListeArtiste`), évaluations réalisées par les agents (`EvaluationAgent`),
paiements (`Paiement`), quittances (`Quittance`), arriérés (`Arriere`) et
notifications (`Notification`). Chaque déclaration suit un cycle de statuts
explicite (*nouvelle → en_evaluation → montant_fixe → paiement_en_attente /
payee → quittance_delivree*, avec une bifurcation possible vers *en_attente*
lorsqu'un complément d'information est demandé par l'agent). Le détail
table par table, avec la justification de chaque choix de modélisation, est
consigné dans [04-base-de-donnees.md](04-base-de-donnees.md) et formalisé
dans `docs/DATABASE_SCHEMA.md`.

## 2.5 Règles de gestion

L'ensemble des règles métier appliquées par la plateforme (calcul du montant
dû, conditions de mise en attente, seuils de déclenchement des arriérés,
conditions de blocage d'un compte, règles d'accès aux quittances, etc.) est
numéroté (`RM-XXX`) et documenté de façon exhaustive dans
[05-regles-metier.md](05-regles-metier.md) et `docs/REGLES_METIER.md`. Ces
règles ont servi de spécification directe pour l'implémentation et pour les
tests automatisés associés à chaque module.

---

# CHAPITRE 3 — PRÉSENTATION ET ANALYSE DES RÉSULTATS

> Cette partie est rédigée **au fur et à mesure de l'avancement du
> développement** : chaque sous-section correspond à une étape ("Prompt") du
> guide de développement, dans l'ordre où elle a été réalisée. Les étapes
> restant à réaliser figurent en fin de chapitre sous forme de plan de
> travail (section 3.14).

## 3.1 Mise en place du socle applicatif et de la base de données

La première étape du développement a consisté à mettre en place le squelette
de l'application Flask selon le patron *factory* (`create_app()`), l'arbre de
dossiers imposé par les règles du projet (`backend/`, `frontend/`,
séparation stricte logique/présentation) et l'ensemble des blueprints
correspondant aux grands domaines fonctionnels (authentification,
déclarations, espace agent, espace administrateur, exports, notifications,
pages publiques). Un script `init_db.py` a ensuite été développé pour créer
les tables du schéma relationnel et les peupler avec un jeu de données de
démonstration réaliste (plusieurs organisateurs, agents, déclarations à
différents stades du cycle de traitement), indispensable pour tester chacune
des étapes suivantes dans des conditions proches du réel.

## 3.2 Authentification et contrôle d'accès

Un module d'authentification complet a été développé (inscription, connexion,
déconnexion) avec hachage des mots de passe par `bcrypt` et gestion de
session via `Flask-Login`. Un contrôle d'accès par rôle (organisateur, agent,
administrateur) restreint l'accès aux routes sensibles au moyen d'un
décorateur dédié (`role_required`).

![Formulaire d'inscription](../screenshots/02-inscription.png)

*Figure 2 — Formulaire d'inscription d'un organisateur.*

![Formulaire de connexion](../screenshots/03-connexion.png)

*Figure 3 — Formulaire de connexion.*

## 3.3 Page d'accueil publique

La page d'accueil publique présente la plateforme, ses fonctionnalités
principales et un accès direct aux formulaires d'inscription et de
connexion.

![Page d'accueil](../screenshots/07-accueil-v2.png)

*Figure 1 — Page d'accueil publique de la plateforme BBDA Events.*

## 3.4 Tableau de bord de l'organisateur

Chaque organisateur dispose d'un tableau de bord listant ses déclarations et
leur statut, avec un indicateur visuel (bannière) lorsque son compte présente
un arriéré bloquant la création de nouvelles déclarations (RM appliquée :
blocage conditionnel, voir [05-regles-metier.md](05-regles-metier.md)).

![Tableau de bord organisateur](../screenshots/09-dashboard-orga1.png)

*Figure 5 — Tableau de bord d'un organisateur avec déclarations en cours.*

![Compte bloqué pour arriéré](../screenshots/10-dashboard-orga4-bloque.png)

*Figure 6 — Tableau de bord d'un organisateur dont le compte est bloqué pour
cause d'arriéré, empêchant la création d'une nouvelle déclaration.*

## 3.5 Formulaire de déclaration d'un événement

Le formulaire de déclaration reprend l'ensemble des champs de la fiche papier
existante (identité du demandeur, nature de la manifestation, salle, date,
liste des artistes) avec un comportement dynamique en JavaScript vanilla
(affichage conditionnel de sections, ajout/suppression de lignes d'artistes)
et une validation à la fois côté client et côté serveur.

![Formulaire de déclaration d'un concert](../screenshots/11-formulaire-concert.png)

*Figure 7 — Formulaire de déclaration d'un concert.*

![Formulaire avec plusieurs artistes](../screenshots/12-formulaire-festival-artistes.png)

*Figure 8 — Formulaire de déclaration d'un festival avec plusieurs artistes.*

![Erreurs de validation](../screenshots/13-formulaire-erreurs.png)

*Figure 9 — Messages d'erreur affichés lors d'une saisie incomplète.*

## 3.6 Page de détail d'une déclaration

Une page de détail présente à l'organisateur l'état complet de sa déclaration
ainsi qu'une chronologie visuelle des étapes de traitement (déclaration
soumise, montant fixé, paiement effectué, quittance délivrée).

![Détail d'une déclaration](../screenshots/15-detail-orga3-0.png)

*Figure 11 — Page de détail d'une déclaration, vue d'ensemble.*

![Chronologie de traitement](../screenshots/15-detail-orga3-1.png)

*Figure 12 — Chronologie du traitement d'une déclaration.*

## 3.7 Tableau de bord de l'agent

L'agent BBDA dispose d'un tableau de bord de pilotage présentant des
indicateurs agrégés (nombre de déclarations par statut, montants perçus,
quittances délivrées) ainsi que des listes filtrables des déclarations à
traiter, des comptes sous surveillance et des organisateurs en situation
d'arriéré.

![Tableau de bord agent](../screenshots/17-dashboard-agent.png)

*Figure 14 — Tableau de bord de l'agent BBDA.*

![Comptes sous surveillance](../screenshots/18-agent-surveillance.png)

*Figure 15 — Liste des comptes organisateurs sous surveillance.*

![Organisateurs en arriéré](../screenshots/19-agent-arrieres.png)

*Figure 16 — Liste des organisateurs en situation d'arriéré.*

## 3.8 Traitement d'une déclaration et fixation du montant

L'ouverture d'une déclaration par un agent fait automatiquement basculer son
statut de « nouvelle » à « en évaluation ». L'agent dispose alors d'une vue
complète de la déclaration, de l'historique de l'organisateur (déclarations
passées, montant total déjà payé, arriéré courant), et d'un formulaire lui
permettant de fixer le tarif et la redevance, avec un calcul du montant total
recalculé en temps réel côté client. Un agent peut également mettre une
déclaration en attente en motivant sa décision par un commentaire, devenu
obligatoire après vérification (RM associée).

![Page de traitement d'une déclaration](../screenshots/20-agent-traitement.png)

*Figure 17 — Page de traitement d'une déclaration par l'agent.*

![Calcul du montant total](../screenshots/21-avant-validation-total.png)

*Figure 18 — Calcul en temps réel du montant total (tarif + redevance) avant
validation par l'agent.*

## 3.9 Confirmation du paiement

Une fois le montant fixé, l'agent peut enregistrer le paiement effectué par
l'organisateur (espèces, chèque ou Orange Money), en paiement intégral ou
partiel. En cas de paiement partiel, un arriéré est automatiquement créé avec
une échéance à sept jours, conformément aux règles de gestion du
recouvrement.

![Formulaire de paiement vierge](../screenshots/24-formulaire-paiement-vide.png)

*Figure 21 — Formulaire de confirmation de paiement.*

![Formulaire de paiement rempli](../screenshots/25-formulaire-paiement-rempli.png)

*Figure 22 — Formulaire de confirmation de paiement rempli pour un paiement
intégral par chèque.*

## 3.10 Génération automatique de la quittance PDF

La dernière étape du cycle de traitement d'une déclaration est la génération
automatique de la quittance, au format PDF, immédiatement après
l'enregistrement du paiement. La mise en page reproduit fidèlement le
formulaire physique du BBDA (en-tête avec logo officiel, encadré de
numérotation séquentielle, champs d'identification du demandeur et de
l'événement, tableau des droits/étiquettes/pénalités avec cases à cocher,
pied de page avec montant en lettres et signature de l'agent), à partir d'une
photographie d'une quittance réelle fournie en référence. Le fichier généré
est stocké côté serveur et son téléchargement, réservé au propriétaire de la
déclaration, est contrôlé par le même mécanisme de contrôle d'accès par rôle
que le reste de l'application.

![Quittance PDF générée](../screenshots/30-quittance-pdf-v3.png)

*Figure 25 — Quittance PDF générée automatiquement par la plateforme.*

![Quittance pour paiement partiel](../screenshots/31-quittance-partiel.png)

*Figure 26 — Quittance PDF dans le cas d'un paiement partiel (mention du
reste à payer).*

![Bouton de téléchargement](../screenshots/32-detail-avec-bouton-telecharger.png)

*Figure 27 — Accès au téléchargement de la quittance depuis l'espace
organisateur.*

## 3.11 Tests et validation

Chaque module développé a fait l'objet de tests automatisés avec `pytest`
(cas nominaux, cas d'erreur, contrôle d'accès), exécutés systématiquement
avant de passer à l'étape suivante du développement — la suite de tests
complète comptait 51 tests passants à l'issue de la mise en place de la
génération de quittance, 55 tests passants après l'ajout du module de
notifications par email (Prompt 13), 67 tests passants après la mise en
place du moteur de gestion des arriérés (Prompt 14), puis 76 tests passants
après l'ajout de l'interface agent de gestion des arriérés et de la
surveillance (Prompt 15), 86 tests passants après la mise en place de
l'espace administrateur (Prompt 16), 93 tests passants après l'ajout
des statistiques avancées (Prompt 17), puis environ 101 tests passants
après la face publique (Prompt 18). Au-delà des tests unitaires, un **test
d'intégration bout-en-bout** a été conduit avec Playwright afin de vérifier
que l'ensemble du parcours utilisateur fonctionne de façon cohérente une fois
tous les modules assemblés : inscription d'un organisateur, connexion,
soumission d'une déclaration, visibilité de la déclaration côté agent,
fixation du montant, confirmation du paiement, puis téléchargement effectif
de la quittance PDF générée. Ce test a validé le bon enchaînement des seize
étapes du parcours et confirmé la cohérence des données affichées à chaque
étape entre l'espace organisateur et l'espace agent.

## 3.12 Notifications automatiques par courrier électronique

Le circuit de traitement d'une déclaration déclenche, à chacune de ses
étapes clés, l'envoi automatique d'un courrier électronique à
l'organisateur concerné (confirmation de réception, montant fixé,
quittance disponible), ainsi qu'à l'attention des agents lorsqu'un compte
sous surveillance se reconnecte. Chaque notification est systématiquement
consignée dans la base de données avant toute tentative d'envoi, puis son
statut est mis à jour (envoyée ou échouée) selon le résultat effectif de la
connexion au serveur SMTP, sans qu'un échec d'envoi ne puisse jamais
interrompre le fonctionnement de la plateforme. L'envoi repose sur un
compte de messagerie dédié, avec un gabarit HTML commun reprenant
l'identité visuelle du BBDA.

![Exemple d'email de notification](../screenshots/33-email-montant-fixe.png)

*Figure 28 — Rendu de l'email automatique envoyé à l'organisateur lorsque le
montant de sa redevance est fixé par l'agent.*

## 3.13 Moteur de gestion des arriérés

La logique de détection et de traitement des arriérés de paiement, jusque-là
codée ponctuellement à l'intérieur des routes de confirmation de paiement et
de connexion, a été regroupée dans un module dédié et testable
indépendamment. Ce moteur implémente : le calcul de l'état d'arriéré d'un
organisateur (montant total dû, caractère bloquant par rapport à un seuil
paramétrable par l'administrateur, fixé à 1 000 FCFA par défaut) ; la
création d'un arriéré avec une échéance de règlement à sept jours et le
blocage automatique du compte concerné dès que ce seuil est franchi ; l'envoi
de rappels automatiques par courrier électronique aux organisateurs dont
l'échéance est dépassée, avec une règle de non-répétition (un rappel au plus
tous les sept jours pour un même arriéré) ; le blocage et le déblocage
manuels d'un compte par un agent, ce dernier soldant automatiquement les
arriérés en attente ; la mise sous surveillance d'un compte introuvable et la
levée de cette surveillance ; ainsi que le report des arriérés déjà existants
d'un organisateur dans le calcul du montant exigible de toute nouvelle
quittance délivrée. Cette centralisation permettra de réutiliser telle
quelle cette logique métier pour l'interface de gestion dédiée de l'agent,
prévue à l'étape suivante du développement.

## 3.14 Interface de gestion des arriérés et de la surveillance (agent)

L'agent dispose désormais d'une interface dédiée pour agir sur les comptes
organisateurs en difficulté, construite au-dessus du moteur d'arriérés :
une liste des comptes non actifs (arriéré, bloqué ou sous surveillance)
affichant le montant total dû et la date du dernier rappel envoyé, avec des
actions de déblocage, de blocage manuel et de mise sous surveillance
(motif obligatoire) directement depuis le tableau ; un bouton déclenchant
l'envoi groupé des rappels de paiement aux organisateurs en retard ; et une
page de surveillance distinguant les alertes récentes non traitées (compte
sous surveillance reconnecté) des comptes actuellement sous surveillance,
avec la possibilité de lever cette surveillance.

## 3.15 Espace administrateur

L'administrateur dispose désormais d'un espace dédié, distinct de celui de
l'agent, avec une barre latérale sombre : un tableau de bord présentant les
chiffres clés (déclarations totales, redevances perçues, arriérés en cours,
comptes actifs) et un graphique en barres CSS des déclarations sur les six
derniers mois ; une page de gestion des utilisateurs séparant organisateurs
et agents/administrateurs, permettant de créer un compte agent et d'activer
ou désactiver un compte ; et une page de paramètres où le seuil d'arriéré
bloquant et le délai avant rappel de notification sont modifiables sans
redéploiement, ces valeurs étant immédiatement reprises par le moteur
d'arriérés.

## 3.16 Statistiques avancées

Une page de statistiques dédiée complète le tableau de bord administrateur :
résumé de l'année en cours (déclarations, redevances perçues, arriérés,
quittances), graphiques en barres CSS sans bibliothèque externe
(déclarations et redevances mois par mois, répartition par type
d'événement), classement des organisateurs les plus actifs, et synthèse
des arriérés (montant total dû, nombre de débiteurs, montant moyen,
échéance la plus ancienne). Les calculs sont isolés dans un module
`admin/stats.py`, testable indépendamment des templates.

## 3.17 Face publique de promotion

La face publique, accessible sans connexion, propose une page d'accueil
orientee presentation de la plateforme (marque BBDA Events en signal
principal, parcours en trois etapes, solutions pour organisateurs, public et
BBDA), un listing des evenements culturels volontairement promus et
autorises (quittance delivree), une page Support (FAQ), un formulaire de
contact enregistre en base, et quatre pages legales (confidentialite, CGU,
politique organisateur, politique du public). Seuls les evenements
satisfaisant simultanement les conditions de promotion et de quittance
apparaissent dans le listing public.

## 3.18 Détail d'événement et module de promotion

Le module de promotion complète la face publique : l'organisateur peut, dès
la soumission de sa déclaration, cocher l'option de diffusion publique,
joindre une description, une affiche (JPG/PNG, 2 Mo maximum) et autoriser
l'affichage de ses coordonnées. Ces informations ne deviennent visibles sur
la page de détail publique (`/evenements/<id>`) qu'après délivrance de la
quittance, conformément à la règle RM-090. Un événement non promu ou non
quittancé renvoie une erreur 404, sans révéler son existence. Lors de la
confirmation du paiement, si l'événement est marqué pour promotion, une
notification spécifique informe l'organisateur que sa page est en ligne.
Depuis son espace, l'organisateur dispose d'un indicateur de visibilité
(non demandé, en attente de quittance, ou déjà visible avec lien). Une page
placeholder annonce la future billetterie en ligne, hors périmètre du
prototype.

![Page de détail d'un événement public](../screenshots/34-detail-evenement-public.png)

*Figure — Page de détail d'un événement culturel sur la face publique BBDA Events.*

![Section Promotion du formulaire](../screenshots/35-formulaire-promotion.png)

*Figure — Section « Promotion publique » du formulaire de nouvelle déclaration.*

## 3.19 Préparation de la soutenance

La dernière étape de développement a consisté à consolider la validation
automatisée et le matériel de présentation orale. Un fichier de tests
fonctionnels transverses (`tests/test_app.py`) rejoue les parcours critiques
(face publique, authentification, déclaration avec promotion, paiement,
publication, contrôle d'accès par rôle, arriérés). Un script
`demo_data.py` permet de recharger un jeu de données réaliste pour la
démonstration, distinct du mode « base neuve » (`init_db.py --vide`) utilisé
pour retester manuellement le système à partir d'un état vide. Un scénario
chronométré d'environ douze minutes et un jeu de questions-réponses destinés
au jury complètent la préparation (`docs/SCENARIO_SOUTENANCE.md`,
`docs/QUESTIONS_JURY.md`).

## 3.20 Discussion et limites à ce stade

[À COMPLÉTER : discussion critique de la solution — performances, ergonomie,
écarts éventuels avec le cahier des charges, retours du maître de stage,
limites du prototype (pas de billetterie réelle, pas de paiement en ligne).]

## 3.21 Plan de travail restant

À la date de rédaction de cette section, les étapes suivantes restent à
réaliser pour finaliser le mémoire :

- [x] Prompt 13 — Service d'envoi réel des notifications par courrier
      électronique (Flask-Mail)
- [x] Prompt 14 — Moteur de gestion avancée des arriérés
- [x] Prompt 15 — Interface de gestion des arriérés et de la surveillance
      côté agent
- [x] Prompt 16 — Espace administrateur complet
- [x] Prompt 17 — Statistiques et tableaux de pilotage
- [x] Prompt 18 — Face publique (accueil, événements, support, contact, légal)
- [x] Prompt 19 — Page détail événement + module promotion + upload affiche
- [x] Prompt 20 — Tests fonctionnels complets et données de démonstration en
      vue de la soutenance
- [ ] Production des diagrammes UML (cas d'utilisation, classes, séquence,
      déploiement, activité)
- [ ] Finalisation de la conclusion générale et des parties encore marquées
      [À COMPLÉTER] dans le présent mémoire

---

# CONCLUSION GÉNÉRALE

[À COMPLÉTER en fin de projet. La conclusion devra reprendre, conformément à
la méthodologie du cours suivi : (1) un rappel de l'objectif général, (2) les
principaux résultats obtenus au regard des objectifs spécifiques énoncés en
introduction, (3) une confrontation explicite des hypothèses H1 et H2 aux
résultats effectivement observés (comparaison avant/après pour H1 ; mécanismes
de recouvrement effectivement implémentés pour H2), (4) les apports du
travail, (5) ses limites (théoriques, empiriques, méthodologiques), et (6) des
perspectives d'évolution (notamment : envoi effectif des notifications,
paiement en ligne, tableau de bord statistique avancé, extension éventuelle
aux utilisateurs permanents). La conclusion doit rester synthétique et ne pas
laisser le lecteur sur une impression d'inachevé.]

---

# RÉFÉRENCES BIBLIOGRAPHIQUES

*(Format à respecter : Nom Initiale. (année). Titre. Éditeur/Revue, lieu —
voir cours de méthodologie, section « Références bibliographiques ».)*

## Sources institutionnelles et documents de cadrage du projet

- Bureau Burkinabè du Droit d'Auteur. *Protocole de stage — BBDA Events*
  (`guide/Protocole_Stage_V1.pdf`).
- Bureau Burkinabè du Droit d'Auteur. *Cahier des charges BBDA Events, V2*
  (`guide/CahierDesCharges_V2_BBDA_Events.docx`).
- Bureau Burkinabè du Droit d'Auteur. *Guide complet de développement BBDA
  Events, V2* (`guide/Guide_Complet_Dev_BBDA_Events_V2.docx`).
- Université Aube Nouvelle. *Initiation à la méthodologie de recherche —
  Cours de rédaction scientifique*, Licence 3, Tronc commun, janvier 2026
  (`Cours_Rédaction scientifique.pptx`).

## Documentation technique du projet

- `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`, `docs/REGLES_METIER.md`
- `AI_RULES.md` — règles de développement permanentes du projet
- `redaction-memoire/01` à `07` — documents de travail préparatoires au
  présent mémoire

## Références académiques

[À COMPLÉTER : revue de littérature académique sur la gestion collective des
droits d'auteur, la dématérialisation des services publics, les systèmes
d'information de gestion. Respecter le format imposé : ouvrages, articles et
sites internet regroupés en trois sous-parties distinctes, classées par ordre
alphabétique du nom du premier auteur.]

---

# ANNEXES

*(Plan des annexes à établir en fin de rédaction ; pagination séparée en
chiffres romains majuscules — I, II, III... — conformément à la méthodologie
du cours suivi.)*

- Annexe A — [À COMPLÉTER] Fiche de déclaration papier originale (photo/scan)
- Annexe B — [À COMPLÉTER] Fiche d'évaluation papier originale (photo/scan)
- Annexe C — [À COMPLÉTER] Photo de la quittance BBDA physique de référence
  (`images/*.jpg`)
- Annexe D — Extraits de code significatifs (ex. génération de la quittance
  PDF, moteur de calcul du montant)
- Annexe E — [À COMPLÉTER] Diagrammes UML (cas d'utilisation, classes,
  séquence, déploiement, activité)
- Annexe F — Captures d'écran complémentaires non reprises dans le corps du
  texte (dossier `screenshots/`, notamment les versions intermédiaires
  01, 04, 05, 06, 28, 29 et le sous-dossier `screenshots/integration/`)
- Annexe G — Journal de bord technique complet
  ([06-journal-de-bord-technique.md](06-journal-de-bord-technique.md))
