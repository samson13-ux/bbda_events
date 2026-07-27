# Demarre Flask + tunnel public pour les tests telephone.
# Usage : powershell -ExecutionPolicy Bypass -File .\scripts\demarrer_acces_public.ps1
#
# Modes (lus depuis .env) :
#   TUNNEL_MODE=ngrok     -> lien STABLE (NGROK_DOMAIN + PUBLIC_BASE_URL)
#   TUNNEL_MODE=quick     -> Cloudflare trycloudflare (URL change a chaque fois)
#   (defaut)              -> ngrok si NGROK_DOMAIN present, sinon quick

$ErrorActionPreference = "Stop"
$Racine = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Racine

# Rafraichir le PATH (apres installation winget)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host ""
Write-Host "=== BBDA Events : acces public ===" -ForegroundColor Cyan
Write-Host "Dossier : $Racine"
Write-Host ""

function Trouver-Ngrok {
    $local = Join-Path $Racine "tools\ngrok\ngrok.exe"
    if (Test-Path $local) { return $local }
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $trouve = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "ngrok.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    return $trouve
}

function Lire-Env {
    param([string]$Cle)
    if (-not (Test-Path ".env")) { return "" }
    foreach ($ligne in Get-Content ".env") {
        if ($ligne -match "^\s*$Cle\s*=\s*(.+)\s*$") {
            return $Matches[1].Trim().Trim('"')
        }
    }
    return ""
}

$TunnelMode = (Lire-Env "TUNNEL_MODE").ToLower()
$NgrokDomain = (Lire-Env "NGROK_DOMAIN").ToLower() -replace '^https?://', '' -replace '/$', ''
$PublicUrlEnv = (Lire-Env "PUBLIC_BASE_URL").TrimEnd('/')

if (-not $TunnelMode) {
    if ($NgrokDomain) { $TunnelMode = "ngrok" } else { $TunnelMode = "quick" }
}

# Liberer le port 5000
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.OwningProcess) {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Get-Process ngrok, cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

$python = Join-Path $Racine "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "venv introuvable. Cree d'abord l'environnement virtuel." -ForegroundColor Red
    exit 1
}

$lienPublic = $null
$tunnel = $null

if ($TunnelMode -eq "ngrok") {
    if (-not $NgrokDomain -or $NgrokDomain -notmatch '\.ngrok') {
        Write-Host "TUNNEL_MODE=ngrok mais NGROK_DOMAIN invalide (valeur actuelle : '$NgrokDomain')." -ForegroundColor Red
        Write-Host "Corrige NGROK_DOMAIN dans .env (ex. quit-easeful-unworn.ngrok-free.dev)" -ForegroundColor Yellow
        exit 1
    }

    $ngrokExe = Trouver-Ngrok
    if (-not $ngrokExe) {
        Write-Host "ngrok introuvable. Lance configurer_lien_stable.ps1" -ForegroundColor Red
        exit 1
    }

    $lienPublic = if ($PublicUrlEnv) { $PublicUrlEnv } else { "https://$NgrokDomain" }
    $env:PUBLIC_BASE_URL = $lienPublic

    Write-Host "Mode lien STABLE (ngrok) : $lienPublic" -ForegroundColor Green
    Write-Host "Demarrage de Flask sur http://127.0.0.1:5000 ..." -ForegroundColor Yellow
    $flask = Start-Process -FilePath $python -ArgumentList "-m", "flask", "run", "--host=127.0.0.1", "--port=5000", "--reload" `
        -PassThru -WindowStyle Hidden -RedirectStandardOutput ".\.flask_public.log" -RedirectStandardError ".\.flask_public.err"

    Start-Sleep -Seconds 3
    if ($flask.HasExited) {
        Write-Host "Flask n'a pas demarre. Voir .flask_public.err" -ForegroundColor Red
        Get-Content ".\.flask_public.err" -ErrorAction SilentlyContinue
        exit 1
    }

    Write-Host "Demarrage du tunnel ngrok..." -ForegroundColor Yellow
    $tunnelOut = Join-Path $Racine ".tunnel.out.log"
    $tunnelErr = Join-Path $Racine ".tunnel.err.log"
    if (Test-Path $tunnelOut) { Remove-Item $tunnelOut -Force }
    if (Test-Path $tunnelErr) { Remove-Item $tunnelErr -Force }

    # Versions recentes : --url ; anciennes : --domain
    $argsNgrok = @("http", "--url=$NgrokDomain", "5000")
    $tunnel = Start-Process -FilePath $ngrokExe -ArgumentList $argsNgrok `
        -PassThru -WindowStyle Hidden -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelErr

    Start-Sleep -Seconds 4
    if ($tunnel.HasExited) {
        $errTxt = ""
        if (Test-Path $tunnelErr) { $errTxt = Get-Content $tunnelErr -Raw -ErrorAction SilentlyContinue }
        if ($errTxt -match 'unknown flag: --url') {
            $tunnel = Start-Process -FilePath $ngrokExe -ArgumentList @("http", "--domain=$NgrokDomain", "5000") `
                -PassThru -WindowStyle Hidden -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelErr
            Start-Sleep -Seconds 4
        }
    }
    if ($tunnel.HasExited) {
        Write-Host "ngrok s'est arrete. Voir .tunnel.err.log" -ForegroundColor Red
        Get-Content $tunnelErr -ErrorAction SilentlyContinue | Select-Object -Last 30
        Write-Host ""
        Write-Host "Si Windows bloque ngrok (virus/PUP) : autorise ngrok.exe dans Securite Windows." -ForegroundColor Yellow
        Write-Host "Si l'authtoken manque : configurer_lien_stable.ps1" -ForegroundColor Yellow
        Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
}
else {
    # Mode quick Cloudflare (URL change a chaque lancement)
    $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
    if (-not $cloudflared) {
        Write-Host "Installation de cloudflared (winget)..." -ForegroundColor Yellow
        winget install --id Cloudflare.cloudflared -e --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path", "User")
        $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
        if (-not $cloudflared) {
            Write-Host "cloudflared introuvable apres installation. Redemarre PowerShell." -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "Mode tunnel RAPIDE Cloudflare (URL differente a chaque fois)." -ForegroundColor Yellow
    Write-Host "Pour un lien FIXE : .\scripts\configurer_lien_stable.ps1" -ForegroundColor Yellow

    Write-Host "Demarrage de Flask sur http://127.0.0.1:5000 ..." -ForegroundColor Yellow
    $flask = Start-Process -FilePath $python -ArgumentList "-m", "flask", "run", "--host=127.0.0.1", "--port=5000", "--reload" `
        -PassThru -WindowStyle Hidden -RedirectStandardOutput ".\.flask_public.log" -RedirectStandardError ".\.flask_public.err"

    Start-Sleep -Seconds 3
    if ($flask.HasExited) {
        Write-Host "Flask n'a pas demarre. Voir .flask_public.err" -ForegroundColor Red
        Get-Content ".\.flask_public.err" -ErrorAction SilentlyContinue
        exit 1
    }

    Write-Host "Demarrage du tunnel Cloudflare..." -ForegroundColor Yellow
    $tunnelOut = Join-Path $Racine ".tunnel.out.log"
    $tunnelErr = Join-Path $Racine ".tunnel.err.log"
    if (Test-Path $tunnelOut) { Remove-Item $tunnelOut -Force }
    if (Test-Path $tunnelErr) { Remove-Item $tunnelErr -Force }

    $tunnel = Start-Process -FilePath "cloudflared" -ArgumentList "tunnel", "--url", "http://127.0.0.1:5000" `
        -PassThru -WindowStyle Hidden -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelErr

    for ($i = 0; $i -lt 45; $i++) {
        Start-Sleep -Seconds 1
        foreach ($fichier in @($tunnelErr, $tunnelOut)) {
            if (Test-Path $fichier) {
                $contenu = Get-Content $fichier -Raw -ErrorAction SilentlyContinue
                if ($contenu -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
                    $lienPublic = $Matches[0]
                    break
                }
            }
        }
        if ($lienPublic) { break }
    }

    if (-not $lienPublic) {
        Write-Host "Impossible d'obtenir l'URL du tunnel. Voir .tunnel.err.log" -ForegroundColor Red
        Get-Content $tunnelErr -ErrorAction SilentlyContinue | Select-Object -Last 20
        Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
        Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }

    $env:PUBLIC_BASE_URL = $lienPublic
    Write-Host "Reconfiguration de Flask avec l'URL publique..." -ForegroundColor Yellow
    Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    $flask = Start-Process -FilePath $python -ArgumentList "-m", "flask", "run", "--host=127.0.0.1", "--port=5000", "--reload" `
        -PassThru -WindowStyle Hidden -RedirectStandardOutput ".\.flask_public.log" -RedirectStandardError ".\.flask_public.err"
    Start-Sleep -Seconds 3
    if ($flask.HasExited) {
        Write-Host "Flask n'a pas redemarre. Voir .flask_public.err" -ForegroundColor Red
        Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
}

$lienPublic | Set-Content -Path (Join-Path $Racine ".public_url") -Encoding utf8

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " LIEN PUBLIC A PARTAGER :" -ForegroundColor Green
Write-Host " $lienPublic" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
if ($TunnelMode -eq "ngrok") {
    Write-Host "Lien STABLE : il restera le meme a chaque lancement." -ForegroundColor Green
    Write-Host "Les corrections de code sont visibles apres rechargement de la page (flask --reload)."
} else {
    Write-Host "Lien TEMPORAIRE : il changera au prochain demarrage."
    Write-Host "Pour un lien fixe : powershell -ExecutionPolicy Bypass -File .\scripts\configurer_lien_stable.ps1"
}
Write-Host ""
Write-Host "Utilise CE lien (telephone) - pas 127.0.0.1"
Write-Host "Ctrl+C pour arreter Flask + tunnel."
Write-Host ""

try {
    while ($true) {
        if ($flask.HasExited -or ($tunnel -and $tunnel.HasExited)) {
            Write-Host "Un des processus s'est arrete." -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Write-Host "Arret en cours..." -ForegroundColor Yellow
    if ($flask) { Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue }
    if ($tunnel) { Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue }
    Get-Process ngrok, cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Termine."
}
