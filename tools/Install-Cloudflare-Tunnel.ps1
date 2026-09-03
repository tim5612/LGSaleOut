param(
    [Parameter(Mandatory = $true)]
    [string]$ServiceName,
    [Parameter(Mandatory = $true)]
    [string]$SourceToken,
    [string]$CloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
)

$ErrorActionPreference = "Stop"
$targetDir = "C:\ProgramData\cloudflared"
$safeServiceName = $ServiceName -replace '[^A-Za-z0-9_-]', '_'
$targetToken = Join-Path $targetDir "token-$safeServiceName"

if (-not (Test-Path -LiteralPath $SourceToken)) { throw "找不到 Tunnel token 暫存檔：$SourceToken" }
if (-not (Test-Path -LiteralPath $CloudflaredPath)) { throw "找不到 cloudflared：$CloudflaredPath" }
if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) { throw "Windows 服務已存在：$ServiceName" }

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
Copy-Item -LiteralPath $SourceToken -Destination $targetToken -Force
& icacls.exe $targetToken /inheritance:r /grant:r "SYSTEM:F" "Administrators:F" | Out-Null

$binaryPath = ('"{0}" tunnel run --token-file "{1}"' -f $CloudflaredPath, $targetToken)
New-Service -Name $ServiceName -BinaryPathName $binaryPath -DisplayName $ServiceName -StartupType Automatic | Out-Null
Start-Service -Name $ServiceName
Get-Service -Name $ServiceName | Format-List Name,Status,StartType
