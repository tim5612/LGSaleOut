param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$uploadRoot = Join-Path $repoRoot 'uploads'
$folders = @('task_photos', 'display_photos')
$files = @()
foreach ($folder in $folders) {
    $path = Join-Path $uploadRoot $folder
    if (-not (Test-Path -LiteralPath $path -PathType Container)) { continue }
    $resolved = (Resolve-Path -LiteralPath $path).Path
    if (-not $resolved.StartsWith($uploadRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Photo directory is outside this project's uploads: $resolved"
    }
    $files += Get-ChildItem -LiteralPath $resolved -File -Recurse -Force
}

Write-Host "Local photo files: $($files.Count)"
$files | ForEach-Object { Write-Host $_.FullName }
if (-not $Apply) {
    Write-Host 'Preview only. Stop LGSale and run EraseDummy.sql before using -Apply.'
    exit 0
}
foreach ($file in $files) {
    Remove-Item -LiteralPath $file.FullName -Force
}
Write-Host "Deleted $($files.Count) local photos. Directories and import files were retained."
