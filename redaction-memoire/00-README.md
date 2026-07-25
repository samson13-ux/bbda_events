# Dossier de rédaction — mode d'emploi

Ce dossier n'est **pas** le mémoire lui-même. C'est la matière première : à chaque
étape importante du projet (réflexion, décision, structuration, code), le contenu
utile à la rédaction est consigné ici, en détail, avec le "pourquoi" derrière
chaque choix — pas seulement le "quoi". L'objectif est double :

1. Te faire gagner du temps de rédaction (tu pars de texte déjà structuré, pas
   d'une page blanche).
2. Te préparer à défendre le projet à l'oral : chaque fichier explique les
   alternatives envisagées et pourquoi telle option a été retenue plutôt qu'une
   autre, ce qui correspond au type de question qu'un jury pose ("pourquoi avoir
   choisi X et pas Y ?").

## Comment ce dossier est organisé

| Fichier | Contenu | Section de mémoire correspondante (indicative) |
|---|---|---|
| [01-contexte-et-problematique.md](01-contexte-et-problematique.md) | Contexte BBDA, problème, objectifs, hypothèses, méthodologie (source : protocole de stage) | Introduction générale, Problématique |
| [02-analyse-des-documents-existants.md](02-analyse-des-documents-existants.md) | Inventaire des documents de préparation, incohérences trouvées et arbitrages rendus | Analyse de l'existant / Cahier des charges |
| [03-choix-techniques-et-architecture.md](03-choix-techniques-et-architecture.md) | Stack technique, architecture MVC, factory pattern, blueprints | Conception technique / Architecture |
| [04-base-de-donnees.md](04-base-de-donnees.md) | Modèle de données complet, justification table par table | Modélisation des données |
| [05-regles-metier.md](05-regles-metier.md) | Règles de gestion, arbitrages métier | Spécifications fonctionnelles |
| [06-journal-de-bord-technique.md](06-journal-de-bord-technique.md) | **Journal chronologique**, mis à jour à chaque session de travail | Réalisation / Mise en œuvre |
| [07-glossaire-et-references.md](07-glossaire-et-references.md) | Lexique métier + liste des sources | Annexes / Glossaire |
| [08-MEMOIRE.md](08-MEMOIRE.md) | **Le mémoire lui-même**, rédigé en style académique, avec captures d'écran | Document final (tous les chapitres) |

## Ce qui va se passer ensuite

Le fichier [06-journal-de-bord-technique.md](06-journal-de-bord-technique.md) va
continuer à grandir à chaque nouvelle étape de développement (Prompt 3, 4, 5...
du guide de dev). Les fichiers 03, 04 et 05 seront mis à jour eux aussi quand des
choix structurants nouveaux apparaissent (nouvelle route, nouvelle règle, etc.).
Les fichiers 01 et 02 sont plutôt stables — ils décrivent le point de départ du
projet.

**[08-MEMOIRE.md](08-MEMOIRE.md) est le mémoire en cours de rédaction**, et non
une note de travail : c'est le document destiné à être rendu et soutenu, rédigé
au fur et à mesure de l'avancement du projet, structuré selon le cours
« Initiation à la méthodologie de recherche » (Université Aube Nouvelle) fourni
par l'utilisateur, et illustré par les captures d'écran du dossier
`screenshots/`. Sa mise à jour à chaque étape de développement est automatique
(voir `AI_RULES.md`, section 12) et ne nécessite pas d'être redemandée par
l'utilisateur.
