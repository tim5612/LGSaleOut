$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $projectPath "Start-LGSale.ps1") -Development -Restart
