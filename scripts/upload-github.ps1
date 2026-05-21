# One-shot: create GitHub repo (if needed) and push TaskPilot
# Usage:
#   Option A — after: gh auth login
#     .\scripts\upload-github.ps1
#   Option B — with token:
#     $env:GH_TOKEN = "ghp_your_token"
#     .\scripts\upload-github.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Owner = "MHussain414"
$Repo = "Taskpilot"
$Remote = "https://github.com/$Owner/$Repo.git"

function Get-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $temp = Join-Path $env:TEMP "gh-cli"
    $exe = Get-ChildItem -Path $temp -Recurse -Filter gh.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) { return $exe.FullName }
    Write-Host "[*] Downloading GitHub CLI..."
    New-Item -ItemType Directory -Force -Path $temp | Out-Null
    $zip = Join-Path $temp "gh.zip"
    Invoke-WebRequest -Uri "https://github.com/cli/cli/releases/download/v2.69.0/gh_2.69.0_windows_amd64.zip" -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $temp -Force
    return (Get-ChildItem -Path $temp -Recurse -Filter gh.exe | Select-Object -First 1).FullName
}

$gh = Get-Gh
Write-Host "[+] Using gh: $gh"

if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

if (-not (git remote get-url origin 2>$null)) {
    git remote add origin $Remote
} else {
    git remote set-url origin $Remote
}

$authOk = $false
& $gh auth status 2>$null
if ($LASTEXITCODE -eq 0) { $authOk = $true }

if (-not $authOk -and $env:GH_TOKEN) {
    $env:GH_TOKEN | & $gh auth login --with-token
    $authOk = $true
}

if (-not $authOk) {
    Write-Host ""
    Write-Host "GitHub login required. Run ONE of these:" -ForegroundColor Yellow
    Write-Host "  gh auth login"
    Write-Host "  OR set `$env:GH_TOKEN = 'ghp_...' and re-run this script"
    Write-Host ""
    & $gh auth login --hostname github.com --git-protocol https --web
    exit 1
}

Write-Host "[*] Creating repo $Owner/$Repo (skip if exists)..."
& $gh repo create "$Owner/$Repo" --public --description "AI Project Management Chat Module - Flask, AI priority, Kanban, team chat" --source . --remote origin --push 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[*] Repo may already exist — pushing..."
    git push -u origin main
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[+] SUCCESS: https://github.com/$Owner/$Repo" -ForegroundColor Green
} else {
    Write-Host "[!] Push failed. Create empty repo at https://github.com/new?name=$Repo then run: git push -u origin main" -ForegroundColor Red
}
