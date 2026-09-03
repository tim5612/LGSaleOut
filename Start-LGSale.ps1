param(
    [switch]$Hidden,
    [switch]$Development,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $projectPath ".env.local"
$pythonPath = Join-Path $projectPath ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $configPath)) {
    throw "找不到 .env.local。請複製 .env.example，並填入這台電腦的設定。"
}
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "找不到 Python 虛擬環境：$pythonPath。請先建立 .venv 並安裝 requirements.txt。"
}

foreach ($rawLine in Get-Content -LiteralPath $configPath -Encoding UTF8) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) { continue }
    $parts = $line.Split("=", 2)
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
        $value = $value.Substring(1, $value.Length - 2)
    }
    [Environment]::SetEnvironmentVariable($key, $value, "Process")
}

$requiredSettings = @(
    "LGSALEOUT_ENV", "LGSALEOUT_PORT", "LGSALEOUT_RP_ID", "LGSALEOUT_ORIGIN",
    "LGSALEOUT_DB_HOST", "LGSALEOUT_DB_PORT", "LGSALEOUT_DB_NAME",
    "LGSALEOUT_DB_USER", "LGSALEOUT_DB_PASSWORD"
)
foreach ($setting in $requiredSettings) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($setting, "Process"))) {
        throw ".env.local 缺少必要設定：$setting"
    }
}

$port = [int]$env:LGSALEOUT_PORT
$secretFileName = if ($env:LGSALEOUT_SESSION_SECRET_FILE) { $env:LGSALEOUT_SESSION_SECRET_FILE } else { ".lgsale-session-secret" }
$sessionSecretPath = if ([IO.Path]::IsPathRooted($secretFileName)) { $secretFileName } else { Join-Path $projectPath $secretFileName }
$legacySecretPath = Join-Path $projectPath ".lgdevb-session-secret"
if (-not (Test-Path -LiteralPath $sessionSecretPath)) {
    if (Test-Path -LiteralPath $legacySecretPath) {
        Copy-Item -LiteralPath $legacySecretPath -Destination $sessionSecretPath
    }
    else {
        $secretBytes = New-Object byte[] 32
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        $rng.GetBytes($secretBytes)
        $rng.Dispose()
        $newSessionSecret = ($secretBytes | ForEach-Object { $_.ToString("x2") }) -join ""
        Set-Content -LiteralPath $sessionSecretPath -Value $newSessionSecret -NoNewline
    }
}
$env:LGSALEOUT_SESSION_SECRET = (Get-Content -LiteralPath $sessionSecretPath -Raw).Trim()

$listenerPids = @(netstat.exe -ano -p tcp | Select-String ":$port\s+.*LISTENING\s+(\d+)$" | ForEach-Object { [int]$_.Matches[0].Groups[1].Value } | Select-Object -Unique)
if ($listenerPids.Count -gt 0) {
    if (-not $Restart) {
        throw "連接埠 $port 已被程序占用：$($listenerPids -join ', ')。若要重啟請使用 Restart-LGSale-Dev.ps1。"
    }
    foreach ($processId in $listenerPids) {
        Stop-Process -Id $processId -Force -ErrorAction Stop
    }
}

$safeEnvironmentName = $env:LGSALEOUT_ENV -replace '[^A-Za-z0-9_-]', '_'
$runtimePath = Join-Path $projectPath "runtime"
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
$logPath = Join-Path $runtimePath "$safeEnvironmentName.log"
$errorLogPath = Join-Path $runtimePath "$safeEnvironmentName.error.log"

Set-Location -LiteralPath $projectPath
Write-Host "$($env:LGSALEOUT_ENV) 啟動中：http://127.0.0.1:$port" -ForegroundColor Green
Write-Host "外部網址：$($env:LGSALEOUT_ORIGIN)" -ForegroundColor Cyan
Write-Host "資料庫：$($env:LGSALEOUT_DB_HOST):$($env:LGSALEOUT_DB_PORT)/$($env:LGSALEOUT_DB_NAME)" -ForegroundColor Cyan

if ($Development) {
    $env:LGSALE_DEV_RELOAD = "1"
    & $pythonPath (Join-Path $projectPath "LGSale.py")
    exit $LASTEXITCODE
}

if ($Hidden) {
    $process = Start-Process -FilePath $pythonPath `
        -ArgumentList @("-m", "waitress", "--listen=127.0.0.1:$port", "LGSale:app") `
        -WindowStyle Hidden -RedirectStandardOutput $logPath -RedirectStandardError $errorLogPath -PassThru
    Write-Output "$($env:LGSALEOUT_ENV) 已在背景啟動，PID $($process.Id)，Log：$runtimePath"
    exit
}

& $pythonPath -m waitress "--listen=127.0.0.1:$port" "LGSale:app"
exit $LASTEXITCODE
