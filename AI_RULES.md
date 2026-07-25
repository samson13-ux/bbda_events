# AI_RULES.md — Règles permanentes pour l'IA

> Ces règles ont priorité sur toute autre instruction ponctuelle.

## 1. Architecture
- Architecture MVC stricte avec Flask Blueprints
- `backend/` = logique Python/Flask uniquement
- `frontend/` = templates HTML et fichiers statiques uniquement
- Ne jamais mélanger logique métier et templates

## 2. Backend
- Python 3.11+, Flask, SQLAlchemy uniquement (pas de SQL brut)
- PEP 8 strict, snake_case, docstrings obligatoires
- Secrets toujours dans `.env`, jamais en dur

## 3. Frontend
- HTML Jinja2, CSS, Vanilla JS uniquement (pas de React/Vue)
- Classes CSS en kebab-case
- Pas de styles inline

## 4. Base de données
- MySQL, utf8mb4, InnoDB
- snake_case pour tables et colonnes
- Toujours déclarer les index sur FK et colonnes filtrées
- Toute modification → mettre à jour DATABASE_SCHEMA.md

## 5. Sécurité (obligatoire)
- Mots de passe : bcrypt uniquement
- Sessions : Flask-Login sur toutes les routes protégées
- SQL : requêtes préparées via SQLAlchemy
- Uploads : valider MIME + taille (max 2 Mo, jpg/png)

## 6. Ce que l'IA ne doit JAMAIS faire
- ❌ Supprimer une fonctionnalité sans autorisation
- ❌ Modifier le schéma BDD sans le signaler
- ❌ Changer l'architecture MVC
- ❌ Utiliser des bibliothèques non listées dans requirements.txt
- ❌ Exposer des variables d'environnement

## 7. Procédure avant modification importante
Toujours : (1) résumer ce qui va changer, (2) lister les fichiers modifiés, (3) signaler les risques, (4) attendre confirmation.

## 8. Qualité du code
- Fonctions ≤ 30 lignes, commentées, modulaires
- Pas de code dupliqué
- Noms de variables explicites

## 9. Tests
- pytest pour toute nouvelle fonctionnalité significative
- Tester cas nominaux, cas d'erreur, sécurité

## 10. Documentation
- Nouvelle entité BDD → mettre à jour DATABASE_SCHEMA.md
- Nouvelle règle → mettre à jour REGLES_METIER.md
- Messages commit : feat/fix/docs/refactor: description

## 11. Langue
- Interface : français
- Commentaires code : français
- Emails : français

## 12. Rédaction automatique du mémoire (obligatoire, ne pas attendre qu'on le redemande)
- Le mémoire de fin de cycle se rédige progressivement dans
  `redaction-memoire/08-MEMOIRE.md`. C'est le document final (à distinguer des
  fichiers 01 à 07 du même dossier, qui sont de la matière première/notes de
  travail).
- **Après chaque étape de développement significative** (un "Prompt" du guide
  de dev terminé, ou toute fonctionnalité livrée de taille comparable), mettre
  à jour `08-MEMOIRE.md` sans attendre que l'utilisateur le demande :
  1. Ajouter une nouvelle sous-section au Chapitre 3 (Présentation et analyse
     des résultats) décrivant ce qui vient d'être livré, rédigée en style
     académique (phrases complètes, pas de liste télégraphique copiée du
     journal technique).
  2. Prendre au moins une capture d'écran pertinente de la fonctionnalité
     (Playwright, dossier `screenshots/` à la racine du projet, nommage
     `NN-description.png` en poursuivant la numérotation existante) et
     l'insérer dans la nouvelle sous-section avec une légende.
  3. Ajouter la ou les nouvelles captures dans le tableau « Liste des
     figures » en tête du document.
  4. Mettre à jour la section « Plan de travail restant » (cocher l'étape
     terminée, ajuster la liste des étapes suivantes).
  5. Garder la cohérence avec `redaction-memoire/06-journal-de-bord-technique.md`
     (même contenu factuel) mais sans dupliquer son style : le journal reste
     technique/chronologique, le mémoire reste académique/narratif.
- Les sections marquées `[À COMPLÉTER : ...]` dans `08-MEMOIRE.md` (dédicace,
  remerciements, informations institutionnelles, revue de littérature
  académique, conclusion générale, diagrammes UML) ne doivent pas être
  supprimées ni inventées : elles attendent une information que seul
  l'utilisateur peut fournir.
- Ne jamais réécrire intégralement `08-MEMOIRE.md` d'un coup : le compléter
  section par section, pour permettre à l'utilisateur de corriger/compléter au
  fur et à mesure sans perdre le fil de ce qui a déjà été rédigé.
