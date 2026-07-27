# Configure un lien public STABLE (meme URL a chaque demarrage).
# Utilise le domaine gratuit fixe de ngrok (pas besoin d'acheter un domaine).
#
# Usage :
#   powershell -ExecutionPolicy Bypass -File .\scripts\configurer_lien_stable.ps1
#
# Etapes manuelles (une seule fois) :
#   1. Creer un compte sur https://dashboard.ngrok.com/signup
#   2. Copier l'authtoken : https://dashboard.ngrok.com/get-started/your-authtoken
#   3. Claimer un domaine gratuit : https://dashboard.ngrok.com/domains
#      (ex. quit-easeful-unworn.ngrok-free.dev)

$ErrorActionPreference = "Stop"
$Racine = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Racine

# Rafraichir le PATH (apres installation winget, l'ancienne fenetre PowerShell ne voit pas ngrok)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host ""
Write-Host "=== BBDA Events : configuration du lien stable ===" -ForegroundColor Cyan
Write-Host ""

function Trouver-Ngrok {
    $local = Join-Path $Racine "tools\ngrok\ngrok.exe"
    if (Test-Path $local) { return $local }
    $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidats = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
    )
    foreach ($c in $candidats) {
        if (Test-Path $c) { return $c }
    }
    $trouve = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "ngrok.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    return $trouve
}

# 1) Installer ngrok
$ngrokExe = Trouver-Ngrok
if (-not $ngrokExe) {
    Write-Host "Installation de ngrok (winget)..." -ForegroundColor Yellow
    winget install --id Ngrok.Ngrok -e --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
    $ngrokExe = Trouver-Ngrok
    if (-not $ngrokExe) {
        Write-Host "ngrok introuvable. Ferme PowerShell, rouvre-le, puis relance ce script." -ForegroundColor Red
        exit 1
    }
}
Write-Host "ngrok OK : $ngrokExe" -ForegroundColor Green

# 2) Authtoken
Write-Host ""
Write-Host "Ouvre cette page, connecte-toi, copie ton Authtoken :" -ForegroundColor Yellow
Write-Host "  https://dashboard.ngrok.com/get-started/your-authtoken"
Write-Host ""
Write-Host "Astuce collage PowerShell : clic DROIT pour coller (Ctrl+V marche parfois mal)." -ForegroundColor Yellow
$token = Read-Host "Colle ton authtoken ngrok ici (ou Entree si deja configure)"
if ($token.Trim()) {
    & $ngrokExe config add-authtoken $token.Trim()
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Echec de l'enregistrement du token. Verifie qu'il est complet." -ForegroundColor Red
        exit 1
    }
    Write-Host "Authtoken enregistre." -ForegroundColor Green
}

# 3) Domaine fixe
Write-Host ""
Write-Host "Ouvre cette page et cree / claim un domaine gratuit :" -ForegroundColor Yellow
Write-Host "  https://dashboard.ngrok.com/domains"
Write-Host "Exemple : quit-easeful-unworn.ngrok-free.dev"
Write-Host ""
$domaine = Read-Host "Entre le domaine EXACT (sans https://)"
$domaine = $domaine.Trim().ToLower() -replace '^https?://', '' -replace '/$', ''
if (-not $domaine) {
    Write-Host "Domaine obligatoire." -ForegroundColor Red
    exit 1
}
if ($domaine -notmatch '\.ngrok(-free)?\.(app|dev)$') {
    Write-Host "Attention : le domaine gratuit finit souvent par .ngrok-free.dev ou .ngrok-free.app" -ForegroundColor Yellow
}

$lien = "https://$domaine"

# 4) Ecrire / mettre a jour .env
$envPath = Join-Path $Racine ".env"
if (-not (Test-Path $envPath)) {
    if (Test-Path (Join-Path $Racine ".env.example")) {
        Copy-Item (Join-Path $Racine ".env.example") $envPath
    } else {
        New-Item -Path $envPath -ItemType File | Out-Null
    }
}

$lignes = Get-Content $envPath
$cles = @{
    "TUNNEL_MODE" = "ngrok"
    "NGROK_DOMAIN" = $domaine
    "PUBLIC_BASE_URL" = $lien
}
$nouvelles = @()
$vues = @{}
foreach ($ligne in $lignes) {
    $remplacee = $false
    foreach ($cle in $cles.Keys) {
        if ($ligne -match "^\s*$cle\s*=") {
            $nouvelles += "$cle=$($cles[$cle])"
            $vues[$cle] = $true
            $remplacee = $true
            break
        }
    }
    if (-not $remplacee) { $nouvelles += $ligne }
}
foreach ($cle in $cles.Keys) {
    if (-not $vues.ContainsKey($cle)) {
        $nouvelles += "$cle=$($cles[$cle])"
    }
}
$nouvelles | Set-Content -Path $envPath -Encoding utf8

$lien | Set-Content -Path (Join-Path $Racine ".public_url") -Encoding utf8

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " LIEN STABLE CONFIGURE :" -ForegroundColor Green
Write-Host " $lien" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ce lien ne changera plus a chaque demarrage."
Write-Host "Pour lancer l'acces public :"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\demarrer_acces_public.ps1"
Write-Host ""
