# Create TaskPilot-share.zip for sending to someone else
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ZipName = Join-Path $ProjectRoot "TaskPilot-share.zip"
$Staging = Join-Path $env:TEMP "TaskPilot-share-staging"

Write-Host "[*] Packaging TaskPilot from: $ProjectRoot"

if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
if (Test-Path $ZipName) { Remove-Item $ZipName -Force }

New-Item -ItemType Directory -Path $Staging | Out-Null

$ExcludeDirs = @('venv', '.venv', 'env', 'instance', '__pycache__', '.git', '.idea', '.vscode', 'node_modules')
$ExcludeFiles = @('.env', '*.db', '*.pyc', '_arena_login.html', '_arena.css', '_arena.js', 'TaskPilot-share.zip')

robocopy $ProjectRoot $Staging /E /XD $ExcludeDirs /XF $ExcludeFiles /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with code $LASTEXITCODE" }

# Ensure .env is never copied (secrets)
$envPath = Join-Path $Staging ".env"
if (Test-Path $envPath) { Remove-Item $envPath -Force }

Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $ZipName -Force
Remove-Item $Staging -Recurse -Force

$sizeMb = [math]::Round((Get-Item $ZipName).Length / 1MB, 2)
Write-Host ""
Write-Host "[+] Created: $ZipName ($sizeMb MB)"
Write-Host "[+] Send this file to your friend."
Write-Host "[+] They should read SETUP-FOR-RECIPIENT.md after unzipping."
Write-Host ""
