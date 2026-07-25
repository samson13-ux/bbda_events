# REGLES_METIER.md — Règles métier de BBDA Events

> Ce document décrit toutes les règles de fonctionnement de la plateforme.
> Toute modification de ces règles doit être validée par le maître de stage BBDA
> avant d'être implémentée dans le code.

---

## 1. Règles générales

### 1.1. Accès à la plateforme

| Règle | Description |
|-------|-------------|
| **RM-001** | La face publique (accueil, événements, support, contact, légal) est accessible sans connexion |
| **RM-002** | L'espace déclaration est accessible uniquement aux organisateurs connectés |
| **RM-003** | L'espace agent est accessible uniquement aux agents et administrateurs |
| **RM-004** | Un organisateur ne peut jamais accéder aux données d'un autre organisateur |
| **RM-005** | Un organisateur ne peut pas accéder aux routes `/agent/` ou `/admin/` |

---

## 2. Règles de déclaration

### 2.1. Soumission d'une déclaration

| Règle | Description |
|-------|-------------|
| **RM-010** | Un organisateur avec un arriéré supérieur ou égal au seuil (1 000 FCFA par défaut) ne peut pas soumettre de nouvelle déclaration |
| **RM-011** | Tous les champs obligatoires du formulaire doivent être remplis avant soumission |
| **RM-012** | La date de l'événement doit être dans le futur au moment de la déclaration |
| **RM-013** | Une déclaration soumise reçoit automatiquement le statut `nouvelle` |
| **RM-014** | Un email de confirmation est envoyé automatiquement à l'organisateur dès soumission |
| **RM-015** | Un organisateur peut modifier sa déclaration uniquement tant que le statut est `nouvelle` (avant prise en charge par un agent). Dès `en_evaluation` ou statut ultérieur, la modification est refusée |

### 2.2. Promotion publique

| Règle | Description |
|-------|-------------|
| **RM-020** | Un organisateur peut choisir de promouvoir son événement sur la face publique en cochant l'option dans le formulaire |
| **RM-021** | Un événement avec `promouvoir=True` n'est visible publiquement QUE si son statut est `quittance_delivree` |
| **RM-022** | Un événement non payé n'apparaît jamais dans le listing public, même si `promouvoir=True` |
| **RM-023** | L'upload d'affiche est limité aux formats JPG et PNG, taille maximale 2 Mo |
| **RM-024** | L'organisateur choisit explicitement si ses coordonnées sont visibles sur la page publique |
| **RM-025** | Un email de notification est envoyé à l'organisateur quand son événement devient visible publiquement |

---

## 3. Règles d'évaluation et de redevance

### 3.1. Fixation du montant

| Règle | Description |
|-------|-------------|
| **RM-030** | Le montant de la redevance est fixé **manuellement** par un agent BBDA — pas de calcul automatique |
| **RM-031** | L'agent fixe deux montants distincts : le **Tarif** et la **Redevance** |
| **RM-032** | Le montant total = Tarif + Redevance |
| **RM-033** | Une fois le montant fixé, l'organisateur reçoit un email avec le montant à payer et les instructions pour se présenter au BBDA |
| **RM-034** | Un agent peut mettre une déclaration `en_attente` avec un commentaire obligatoire |
| **RM-035** | Seul un agent ou un administrateur peut fixer ou modifier le montant d'une redevance |

### 3.2. Distinction Tarif / Redevance

- **Tarif** : montant de référence tiré du barème interne du BBDA (grille tarifaire par type/catégorie d'événement). Sert de base de calcul, saisie par l'agent au moment de l'évaluation.
- **Redevance** : montant complémentaire fixé par l'agent selon le contexte de l'événement (ex. capacité de la salle, affluence estimée). C'est la part variable au-dessus du tarif de base.
- **Montant total à payer** (RM-032) = Tarif + Redevance. C'est ce montant total qui est suivi dans le processus de paiement (RM-040 à RM-046) et sur lequel porte l'éventuel arriéré (section 6).

---

## 4. Règles de paiement

### 4.1. Confirmation du paiement

| Règle | Description |
|-------|-------------|
| **RM-040** | Le paiement est effectué **en personne au bureau BBDA** — pas de paiement en ligne pour le prototype |
| **RM-041** | L'agent confirme manuellement la réception du paiement dans l'application |
| **RM-042** | Modes de paiement acceptés : Espèces / Chèque (avec numéro) / Orange Money |
| **RM-043** | Un paiement peut être **intégral** (tout payé) ou **partiel** (avec reste à payer) |
| **RM-044** | Si le paiement est partiel, un arriéré est automatiquement créé pour le montant restant |
| **RM-045** | La quittance PDF est générée automatiquement dès que le solde restant dû atteint zéro (voir RM-047, RM-048) |
| **RM-046** | Un email de notification "Quittance disponible" est envoyé à l'organisateur |
| **RM-047** | Une déclaration peut recevoir **plusieurs paiements successifs** (versements). Le **solde restant dû** est recalculé à chaque nouveau versement (`solde restant = montant total − somme des paiements confirmés`) |
| **RM-048** | La quittance (RM-050) n'est générée qu'une fois le **solde restant atteint zéro** — un versement partiel ne déclenche jamais la génération de la quittance |

---

## 5. Règles de la quittance

### 5.1. Génération et contenu

| Règle | Description |
|-------|-------------|
| **RM-050** | La quittance est générée automatiquement — elle ne peut pas être créée manuellement |
| **RM-051** | Le numéro de quittance est séquentiel et unique (format : `0000001`, `0000002`...) |
| **RM-052** | La quittance reproduit fidèlement la structure du document physique BBDA |
| **RM-053** | La quittance est téléchargeable par l'organisateur depuis son espace personnel |
| **RM-054** | La quittance n'est jamais modifiable après génération |

---

## 6. Règles de gestion des arriérés

### 6.1. Détection et seuil

| Règle | Description |
|-------|-------------|
| **RM-060** | Le seuil d'arriéré bloquant est fixé par défaut à **1 000 FCFA** |
| **RM-061** | Ce seuil est paramétrable par l'administrateur depuis l'espace admin |
| **RM-062** | Un arriéré est créé automatiquement quand : (a) le paiement est partiel, ou (b) une redevance n'est pas réglée |
| **RM-063** | La date d'échéance d'un arriéré est fixée à **J+7** après la fixation du montant par l'agent |

### 6.2. Notifications et blocage

| Règle | Description |
|-------|-------------|
| **RM-070** | Un email de rappel est envoyé automatiquement **7 jours après la date d'échéance** si l'arriéré n'est pas réglé |
| **RM-071** | Le délai de 7 jours est paramétrable par l'administrateur |
| **RM-072** | Un rappel ne peut pas être envoyé deux fois dans un délai inférieur à 7 jours pour le même arriéré |
| **RM-073** | Tout compte avec un arriéré **supérieur ou égal au seuil** est automatiquement bloqué |
| **RM-074** | Un compte bloqué **ne peut pas soumettre de nouvelle déclaration** |
| **RM-075** | Le déblocage d'un compte est effectué **manuellement par un agent** après vérification du règlement |
| **RM-076** | Le déblocage marque automatiquement tous les arriérés de l'organisateur comme réglés |

### 6.3. Comptes sous surveillance

| Règle | Description |
|-------|-------------|
| **RM-080** | Un compte peut être marqué `sous surveillance` par un agent (cas : organisateur introuvable) |
| **RM-081** | Quand un compte `sous surveillance` se reconnecte, une **alerte immédiate** est envoyée à tous les agents et à l'administrateur |
| **RM-082** | L'alerte apparaît dans le tableau de bord agent avec un badge rouge distinctif |
| **RM-083** | L'alerte peut être marquée comme traitée par n'importe quel agent |
| **RM-084** | La surveillance peut être levée par un agent ou l'administrateur |

---

## 7. Règles de la face publique

### 7.1. Événements publics

| Règle | Description |
|-------|-------------|
| **RM-090** | Seuls les événements avec `promouvoir=True` ET `statut=quittance_delivree` apparaissent dans le listing public |
| **RM-091** | Un événement non autorisé par le BBDA (quittance non délivrée) n'est jamais public |
| **RM-092** | L'administrateur peut dépublier un événement si nécessaire (passage de `promouvoir` à `False`) |
| **RM-093** | La page de détail d'un événement renvoie une erreur 404 si l'événement n'est pas public |

---

## 8. Règles de notification

### 8.1. Emails automatiques

| Règle | Description |
|-------|-------------|
| **RM-100** | Chaque email envoyé est enregistré en base de données (table `notification`) |
| **RM-101** | En cas d'échec d'envoi, le statut de la notification passe à `echouee` — l'application ne plante pas |
| **RM-102** | Les emails sont envoyés en français uniquement |
| **RM-103** | L'adresse d'expédition est le compte Gmail dédié configuré dans `.env` |

---

## 9. Paramètres configurables par l'administrateur

Ces paramètres sont persistés en base de données dans la table `parametres_systeme`
(voir `docs/DATABASE_SCHEMA.md`) plutôt qu'en dur dans le code, afin d'être modifiables
depuis l'espace admin sans redéploiement.

| Paramètre | Valeur par défaut | Description |
|-----------|-------------------|-------------|
| `SEUIL_ARRIERE` | 1 000 FCFA | Montant d'arriéré à partir duquel un compte est bloqué |
| `DELAI_NOTIFICATION` | 7 jours | Délai après échéance avant envoi du rappel |

---

## 10. Perspectives d'évolution (hors périmètre prototype)

| Fonctionnalité | Description |
|----------------|-------------|
| Billetterie en ligne | Achat de billets via Orange Money / Moov Money API |
| Notifications WhatsApp | Via WhatsApp Business API |
| Application mobile | Android/iOS pour organisateurs et public |
| Scan QR codes | Validation des billets à l'entrée des événements |
| Directions régionales | Extension aux 13 directions régionales du BBDA |
| Langues nationales | Interface en mooré et dioula |

---

*Dernière mise à jour : Juillet 2026*
*Validé par : Maître de stage BBDA — À compléter après validation*
