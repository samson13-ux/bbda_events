# Diagrammes UML — BBDA Events

Dossier consultable pour le mémoire et la soutenance.

## Contenu

| Fichier PNG | Source Mermaid | Type UML |
|---|---|---|
| `01-cas-utilisation.png` | `01-cas-utilisation.mmd` | Cas d'utilisation |
| `02-classes.png` | `02-classes.mmd` | Diagramme de classes |
| `03-sequence-declaration.png` | `03-sequence-declaration.mmd` | Séquence — déclaration |
| `04-sequence-paiement-quittance.png` | `04-sequence-paiement-quittance.mmd` | Séquence — paiement / quittance |
| `05-activite.png` | `05-activite.mmd` | Activité — circuit complet |
| `06-deploiement.png` | `06-deploiement.mmd` | Déploiement |

## Régénérer les PNG

```bash
.\venv\Scripts\python.exe memoire\docs\diagrammes\rendre_png.py
```

## Emplacement dans le mémoire Word

- **Chapitre 2 — Matériel et méthodes** : cas d’utilisation, classes, activité, déploiement
- **Annexes** : séquences + reprise de l’ensemble

Ces figures sont aussi injectées automatiquement par  
`memoire/redaction/generer_memoire_word.py`.
