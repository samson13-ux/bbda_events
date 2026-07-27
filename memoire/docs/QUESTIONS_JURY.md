# Questions probables du jury — BBDA Events

Réponses courtes à préparer pour l’oral (Prompt 20).

---

## 1. Pourquoi une architecture MVC avec Flask (et non une API + React) ?

Le cahier des charges et le protocole de stage privilégient une application web classique, déployable simplement chez le BBDA sans infrastructure Node.js. Flask + Jinja2 permet une architecture MVC claire (blueprints `auth`, `declarations`, `agent`, `admin`, `public`, `exports`), un rendu côté serveur, et une maintenance accessible aux équipes habituées au PHP/HTML. Le prototype Veenue (front riche) a servi d’inspiration visuelle, pas de contrainte technique.

## 2. Comment la sécurité est-elle assurée ?

- Mots de passe hachés avec **bcrypt** (jamais en clair).  
- Sessions via **Flask-Login** ; décorateur `role_required` pour séparateur organisateur / agent / admin.  
- Un organisateur ne peut pas voir le dossier d’un autre (404).  
- Uploads limités (JPG/PNG, 2 Mo) et nommés de façon sécurisée.  
- Secrets dans `.env` ; pas de SQL brut (SQLAlchemy).

## 3. Comment fonctionne la gestion des arriérés ?

En cas de paiement partiel, un **arriéré** est créé (échéance J+7). Si le cumul dû dépasse le **seuil** configurable (`SEUIL_ARRIERE`, défaut 1000 FCFA), le compte passe en statut bloquant : plus de nouvelle déclaration. L’agent peut rappeler, bloquer/débloquer, et mettre un compte sous **surveillance**. Les arriérés préexistants sont intégrés au calcul de la quittance.

## 4. Comment la quittance PDF est-elle générée ?

Après confirmation du paiement par l’agent, le module `exports` (ReportLab) produit un PDF numéroté, stocké sous `frontend/static/quittances/`, et l’organisateur peut le télécharger depuis son espace. Le statut passe à `quittance_delivree`.

## 5. Que se passe-t-il pour les notifications e-mail ?

Chaque notification est d’abord **journalisée en base** (`en_attente`), puis envoyée via Flask-Mail. En cas d’échec SMTP, le statut devient `echouee` sans faire planter le métier (déclaration, paiement). Types principaux : confirmation, montant fixé, quittance, rappel d’arriéré, événement publié.

## 6. Quelle est la logique de la face publique ?

Seuls les événements avec `promouvoir=True` **et** `statut=quittance_delivree` apparaissent dans `/evenements` et ont une page détail. Sinon : 404 (pas de fuite d’existence). L’organisateur opte pour la promotion à la déclaration ; la mise en ligne n’intervient qu’après paiement.

## 7. Quelles perspectives d’évolution ?

Hors périmètre du stage (3 mois) : billetterie en ligne (Orange/Moov Money), notifications WhatsApp, application mobile, QR code, extension aux directions régionales, langues nationales. Le placeholder `/billetterie-bientot` matérialise déjà cette perspective.
