param(
    [string]$EmployeeNo = "S0128"
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python virtual environment not found: $python"
}

$listeners = Get-NetTCPConnection -LocalPort 8097 -State Listen -ErrorAction SilentlyContinue
if ($listeners) {
    $listenerPids = ($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
    throw "Port 8097 is used by PID $listenerPids. Run elevated PowerShell: Stop-Process -Id $listenerPids -Force"
}

$env:LGSALEOUT_RP_ID = "lgdeva.superb-supplies.com.tw"
$env:LGSALEOUT_ORIGIN = "https://lgdeva.superb-supplies.com.tw"
$env:LGSALEOUT_PORT = "8097"
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$secretBytes = New-Object byte[] 32
$rng.GetBytes($secretBytes)
$env:LGSALEOUT_SESSION_SECRET = ($secretBytes | ForEach-Object { $_.ToString("x2") }) -join ""
$rng.Dispose()

Set-Location -LiteralPath $projectDir

Write-Host "Creating a 15-minute invitation for $EmployeeNo" -ForegroundColor Cyan
& $python LGSale.py invite employee $EmployeeNo
if ($LASTEXITCODE -ne 0) { throw "Failed to create invitation" }

Write-Host "Starting test service at http://127.0.0.1:8097" -ForegroundColor Green
Write-Host "Keep this window open. Press Ctrl+C to stop." -ForegroundColor Yellow
& $python -m waitress --listen=127.0.0.1:8097 LGSale:app
