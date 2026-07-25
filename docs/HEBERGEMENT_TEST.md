# Acces public pour tests BBDA Events

## Recommandation actuelle : PythonAnywhere (lien fixe)

ngrok pose probleme sur cette machine (bloque par Windows Defender).  
Pour un **lien qui ne change pas** et un vrai hebergement :

→ Suivre **[HEBERGEMENT_PYTHONANYWHERE.md](HEBERGEMENT_PYTHONANYWHERE.md)**

Lien final du type : `https://toncompte.pythonanywhere.com`

## Secours rapide (PC allume) : tunnel Cloudflare

Si tu as besoin d'un acces **tout de suite** et que ton PC reste allume :

```powershell
cd C:\bbda_events
powershell -ExecutionPolicy Bypass -File .\scripts\demarrer_acces_public.ps1
```

Sans `NGROK_DOMAIN` valide, le script retombe sur Cloudflare (`trycloudflare.com`).  
**L'URL change a chaque lancement** — uniquement en secours.

Pour forcer ce mode, dans `.env` :

```env
TUNNEL_MODE=quick
```

## Autres clouds (plus tard)

| Service | Lien fixe | Remarque |
|---------|-----------|----------|
| **PythonAnywhere** | Oui | Meilleur pour Flask + MySQL etudiant |
| **Render** | Oui | Souvent Postgres (migration SQL) |
| **Railway** | Oui | Simple, parfois carte bancaire demandee |
| **Fly.io** | Oui | Un peu plus technique |

## Securite

- Ne committe jamais `.env` ni `.public_url`
- Change `SECRET_KEY` en production
