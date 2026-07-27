# Règles métier — synthèse et justification

> Source normative : `../docs/REGLES_METIER.md` (RM-001 à RM-103). Ce fichier
> reformule les règles par thème avec leur **raison d'être**, pour la partie
> "spécifications fonctionnelles" du mémoire.

## Tarif vs Redevance

Distinction ajoutée pendant l'arbitrage (§3.2 de `../docs/REGLES_METIER.md`) :

- **Tarif** : montant de référence tiré du **barème interne** du BBDA (grille
  tarifaire par type/catégorie d'événement). Base de calcul, saisie par
  l'agent lors de l'évaluation.
- **Redevance** : montant complémentaire fixé par l'agent selon le **contexte
  spécifique** de l'événement (capacité de la salle, affluence estimée...).
  Part variable au-dessus du tarif de base.
- **Montant total à payer** = Tarif + Redevance (RM-032). C'est ce total qui
  est suivi tout au long du processus de paiement et sur lequel porte
  l'éventuel arriéré.

**À expliquer en soutenance** : cette distinction en deux montants (plutôt
qu'un montant unique) reflète fidèlement comment un agent BBDA raisonne dans
la réalité — un socle standardisé + un ajustement au cas par cas — et se
retrouve telle quelle sur la quittance physique (champs `droit_annuel` /
`droits_montant` distincts).

## Accès à la plateforme (RM-001 à RM-005)

Quatre espaces cloisonnés par rôle : face publique (libre), organisateur
(déclarations), agent (traitement), admin (supervision). Un organisateur ne
peut jamais voir les données d'un autre organisateur, ni accéder aux routes
`/agent/` ou `/admin/`. **Raison** : confidentialité des informations
financières (montants de redevance) et respect du principe du moindre
privilège.

## Soumission d'une déclaration (RM-010 à RM-014)

Point le plus important à retenir : **RM-010 — un organisateur en arriéré
au-dessus du seuil ne peut pas soumettre de nouvelle déclaration**. C'est le
mécanisme central qui traduit l'hypothèse de recherche H2 (recouvrement des
impayés) en une contrainte fonctionnelle concrète : le blocage n'est pas
punitif dans l'absolu, il est directement lié à la fonction principale de
l'outil (déclarer un nouvel événement).

## Promotion publique (RM-020 à RM-025)

Un organisateur **choisit** de promouvoir son événement (opt-in, pas une
conséquence automatique de la déclaration). Règle de sécurité importante :
**RM-021/RM-022 — un événement n'est visible publiquement que si son statut
est `quittance_delivree`**, c'est-à-dire seulement une fois entièrement payé.
**Raison** : le BBDA ne veut jamais donner l'impression d'autoriser
publiquement un événement pour lequel la redevance n'a pas encore été
réglée — risque d'image institutionnelle.

## Évaluation et fixation du montant (RM-030 à RM-035)

**RM-030 — fixation manuelle, pas de calcul automatique.** Choix
volontairement conservateur pour le prototype : le barème réel de
tarification du BBDA (grille par type d'événement, capacité, etc.) est
complexe et évolutif ; automatiser ce calcul demanderait une modélisation
métier que le stage de 3 mois ne permet pas de valider avec certitude.
**Argument pour la soutenance** : c'est un choix assumé de "digitalisation du
processus" plutôt que de "réingénierie du processus" — l'outil fait gagner du
temps sur la circulation de l'information et le suivi, sans retirer à l'agent
son pouvoir de décision métier (qui reste responsable, humainement, du
montant fixé).

## Paiement (RM-040 à RM-048)

- **RM-040 — paiement uniquement en personne au bureau BBDA**, pas de
  paiement en ligne pour ce prototype (le protocole classe explicitement la
  billetterie en ligne comme perspective d'évolution hors périmètre).
- **RM-043/044 — paiement intégral ou partiel**, un arriéré étant créé
  automatiquement pour la part non réglée.
- **RM-047/048 — versements multiples possibles** (ajout formalisé lors de
  l'arbitrage) : le solde restant est recalculé à chaque versement ; la
  quittance n'est générée qu'une fois le solde à zéro. Voir
  [04-base-de-donnees.md](04-base-de-donnees.md#6-paiement--la-décision-de-modélisation-la-plus-significative)
  pour la traduction en base de données.

## Quittance (RM-050 à RM-054)

Génération **automatique uniquement** (jamais manuelle — RM-050), numéro
séquentiel unique, **jamais modifiable après génération** (RM-054) : ce sont
les garanties d'intégrité attendues d'un document faisant foi de paiement,
équivalentes aux garanties d'une quittance papier numérotée.

## Gestion des arriérés (RM-060 à RM-084)

Trois mécanismes emboîtés, à bien distinguer dans le mémoire :

1. **Seuil de blocage** (RM-060/061/073/074) : 1 000 FCFA par défaut,
   paramétrable, stocké dans `parametres_systeme`. Au-delà, le compte est
   automatiquement bloqué et ne peut plus déclarer.
2. **Rappels automatiques** (RM-070 à RM-072) : email de rappel 7 jours après
   échéance (délai lui aussi paramétrable), avec garde-fou anti-spam (pas
   deux rappels en moins de 7 jours pour le même arriéré).
3. **Comptes sous surveillance** (RM-080 à RM-084) : mécanisme distinct des
   arriérés, destiné aux cas de fraude ou d'organisateur introuvable — pas un
   niveau "pire" du blocage, mais une **autre situation à risque**
   (traçabilité/enquête plutôt que recouvrement financier). Génère une alerte
   immédiate visible par tous les agents dès la reconnexion du compte
   concerné.

**Point d'arbitrage à mentionner** : la règle d'échéance (RM-063, J+7 après
fixation du montant) a fait l'objet d'une clarification — voir
[02-analyse-des-documents-existants.md](02-analyse-des-documents-existants.md#25-conflit-sur-la-règle-déchéance-des-arriérés).

## Face publique (RM-090 à RM-093)

Redondant avec RM-021/022 par sécurité : même règle rappelée côté affichage
(`promouvoir=True` **ET** `statut=quittance_delivree`) — la page de détail
d'un événement non autorisé renvoie une 404, comme s'il n'existait pas (pas
de message d'erreur qui révélerait son existence).

## Notifications (RM-100 à RM-103)

Toute notification est **journalisée en base**, même en cas d'échec d'envoi
(`statut=echouee` plutôt qu'une exception qui ferait planter l'application).
Choix de robustesse classique : un problème SMTP externe (Gmail down, quota
dépassé) ne doit jamais bloquer le cœur métier (déclaration, paiement).

## Paramètres configurables (§9)

`SEUIL_ARRIERE` (1000 FCFA) et `DELAI_NOTIFICATION` (7 jours), désormais
persistés dans `parametres_systeme` plutôt qu'en dur dans le code — voir
[04-base-de-donnees.md](04-base-de-donnees.md#12-parametres_systeme).

## Hors périmètre du prototype (§10)

Explicitement écarté du stage de 3 mois, à mentionner dans le mémoire comme
"perspectives d'évolution" et non comme des manques : billetterie en ligne
(Orange/Moov Money), notifications WhatsApp (API payante), application
mobile, scan QR code, extension aux 13 directions régionales, interface en
langues nationales (mooré, dioula).
