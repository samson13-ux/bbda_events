# Contexte et problématique

> Source principale : `guide/Protocole_Stage_V1.pdf`

## 1. La structure d'accueil : le BBDA

Le **Bureau Burkinabè du Droit d'Auteur (BBDA)** est l'institution publique
chargée, au Burkina Faso, de la protection et de la gestion collective des
droits d'auteur et des droits voisins. Concrètement, une de ses missions est de
**percevoir les redevances** dues par toute personne physique ou morale qui
exploite des œuvres protégées — ici, dans le cadre d'événements culturels
occasionnels (concerts, festivals, spectacles, galas...).

**Point clé à retenir pour la soutenance** : le BBDA gère deux catégories
d'utilisateurs d'œuvres protégées, avec deux processus totalement différents :

| | Utilisateurs permanents (bars, radios, TV) | Organisateurs occasionnels (notre projet) |
|---|---|---|
| Processus | **Demande d'autorisation préalable** avant exploitation | **Déclaration** de l'événement (pas d'autorisation à demander) |
| Fréquence | Exploitation continue | Événement ponctuel |
| Outil existant | Le BBDA a déjà une application dédiée | **Aucun outil numérique — tout est papier** |

C'est cette deuxième catégorie, non couverte par l'application existante du
BBDA, qui est le sujet du stage. **Ce point mérite d'être clairement posé dans
l'introduction du mémoire** : ce n'est pas une refonte de l'application
existante, c'est la couverture d'un processus jusque-là non numérisé.

## 2. Le problème : un circuit entièrement manuel

Le processus actuel, tel que décrit dans le protocole de stage, se déroule ainsi :

1. L'organisateur se déplace physiquement au BBDA.
2. Il remplit une **fiche de déclaration papier**.
3. Un agent du BBDA (à la **Direction de l'Exploitation, de la Perception et
   des Affaires Juridiques — DEPAJ**) analyse les informations et **fixe
   manuellement** le montant de la redevance sur une fiche d'évaluation.
4. L'organisateur paie et reçoit une **quittance physique**.

Conséquences identifiées dans le protocole :
- Délais de traitement allongés.
- Charge administrative importante pour les agents (ressaisie, calculs manuels,
  classement papier).
- **Absence de suivi centralisé** : pas de vision globale des paiements, et
  surtout pas de suivi automatisé des **arriérés** (redevances non payées).

C'est ce dernier point (traçabilité et recouvrement) qui motive directement deux
modules du projet : la gestion des arriérés et les notifications automatiques.

## 3. Objectif général du projet

> Concevoir et développer une plateforme web de gestion et de suivi des
> déclarations d'événements culturels occasionnels au BBDA, couvrant l'ensemble
> du processus depuis la déclaration de l'organisateur jusqu'à la délivrance de
> la quittance, en intégrant le suivi des paiements, la gestion des arriérés et
> un système de notifications automatiques.

## 4. Objectifs spécifiques

1. Analyser le processus actuel (papier → quittance).
2. Identifier les besoins fonctionnels et techniques des agents et des organisateurs.
3. Concevoir l'architecture fonctionnelle et technique (UML, modèle de données).
4. Développer un module de déclaration en ligne (organisateur).
5. Développer un espace agent (évaluation manuelle du montant, suivi des paiements).
6. Développer un système de notifications automatiques par email (WhatsApp
   explicitement repoussé — nécessite une API payante, donc hors périmètre du
   prototype).
7. Développer un module de gestion des arriérés (alertes, comptes sous surveillance).
8. Développer un module de génération automatique de quittance PDF.
9. Tester, valider, documenter dans le mémoire.

## 5. Hypothèses de recherche

Ce sont **les deux affirmations que le projet doit vérifier/illustrer** — un
jury peut demander "avez-vous vérifié votre hypothèse, et comment ?" :

**H1 —** La dématérialisation du processus de déclaration (basé sur la
déclaration, pas sur une autorisation préalable) permet de réduire
significativement les délais de traitement et la charge administrative des
agents, tout en améliorant la traçabilité des déclarations et des paiements.

**H2 —** La mise en place d'un système centralisé de gestion des arriérés,
avec alertes automatiques et mécanisme de blocage des comptes débiteurs,
facilite le recouvrement des redevances impayées et réduit les pertes
financières pour le BBDA.

**Pour la soutenance** : H1 se vérifie surtout par la comparaison
avant/après (délai de traitement papier vs plateforme, nombre d'étapes
manuelles supprimées). H2 se vérifie par les mécanismes concrets implémentés :
RM-060 à RM-076 (seuil d'arriéré, blocage automatique, alerte immédiate sur
compte sous surveillance) — voir [05-regles-metier.md](05-regles-metier.md).

## 6. Méthodologie (4 phases)

1. **Analyse** : observation du processus à la DEPAJ, entretiens agents,
   collecte des fiches papier (déclaration + évaluation).
2. **Conception** : modélisation UML (cas d'utilisation, classes, séquence,
   déploiement, activité), architecture MVC, conception de la base de données.
3. **Réalisation** : développement avec les technologies retenues, moteur de
   calcul (fixation manuelle, pas de calcul automatique — voir RM-030),
   tests fonctionnels.
4. **Validation et documentation** : tests avec cas réels, retours du maître
   de stage, rédaction du mémoire.

**Point d'attention méthodologique** : à la date de cette note, les
diagrammes UML formels (cas d'utilisation, classes, séquence) n'ont pas encore
été produits sous forme de schémas — seule la modélisation de données
(`docs/DATABASE_SCHEMA.md`) et les règles métier existent. C'est un livrable
à ne pas oublier avant la soutenance (section "Résultats attendus" du
protocole les mentionne explicitement).

## 7. Outils et technologies retenus (protocole, section 5.2)

| Catégorie | Choix |
|---|---|
| Backend | Python 3.13 + Flask |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Base de données | MySQL |
| Génération PDF | ReportLab |
| Architecture | MVC (Modèle-Vue-Contrôleur) |
| Modélisation UML | StarUML ou draw.io |
| Environnement | VS Code, XAMPP |
| Gestion de version | Git |

Voir [03-choix-techniques-et-architecture.md](03-choix-techniques-et-architecture.md)
pour la justification détaillée de chaque choix technique et comment il se
traduit concrètement dans le code.

## 8. Résultats attendus (protocole, section 6)

Liste servant de **check-list pour le mémoire final** — chaque item doit
correspondre à une section de résultats démontrable :

- [ ] Processus actuel analysé et documenté
- [x] Cahier des charges rédigé (`guide/CahierDesCharges_V2_BBDA_Events.docx`) — *validation par le maître de stage encore en attente*
- [ ] Diagrammes UML produits
- [ ] Module de déclaration en ligne développé et testé
- [ ] Espace agent développé (évaluation, validation, suivi paiements)
- [ ] Notifications automatiques par email opérationnelles
- [ ] Module de gestion des arriérés opérationnel
- [ ] Génération automatique de quittance PDF opérationnelle
- [ ] Tests fonctionnels réalisés et documentés
- [ ] Mémoire rédigé et soumis

*(Coché au fur et à mesure — voir l'état d'avancement réel dans
[06-journal-de-bord-technique.md](06-journal-de-bord-technique.md).)*
