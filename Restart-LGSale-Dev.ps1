param(
    [switch]$Elevated
)

$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectPath ".venv\Scripts\python.exe"
$appPath = Join-Path $projectPath "LGSale.py"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "找不到 Python：$pythonPath"
}

$listenerPids = @(
    Get-NetTCPConnection -LocalPort 8097 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
)

if ($listenerPids.Count -gt 0) {
    try {
        $listenerPids | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction Stop
        }
    }
    catch {
        if ($Elevated) {
            throw "即使使用系統管理員權限，仍無法停止 8097 的舊程序：$($_.Exception.Message)"
        }

        $arguments = @(
            "-NoProfile"
            "-ExecutionPolicy", "Bypass"
            "-File", ('"' + $MyInvocation.MyCommand.Path + '"')
            "-Elevated"
        )
        Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
        exit
    }
}

$env:LGSALE_DEV_RELOAD = "1"
Set-Location -LiteralPath $projectPath

Write-Host "LGSale 測試服務啟動中：http://127.0.0.1:8097" -ForegroundColor Green
Write-Host "之後儲存 Python 程式會自動重載；要停止服務請關閉此視窗。" -ForegroundColor Cyan
Write-Host ""

& $pythonPath $appPath

Write-Host ""
Write-Host "服務已停止。按 Enter 關閉視窗。" -ForegroundColor Yellow
Read-Host
