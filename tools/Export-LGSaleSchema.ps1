[CmdletBinding()]
param(
    [string]$ServerInstance,

    [string]$Database = "LGSaleOut",

    [string]$OutputPath,

    [PSCredential]$SqlCredential,

    [switch]$UseProjectEnvironment
)

$ErrorActionPreference = "Stop"
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($scriptDirectory)) {
    $scriptDirectory = (Resolve-Path ".\tools").Path
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $scriptDirectory "..\database\baseline\LGSaleOut_Schema.sql"
}

if ($UseProjectEnvironment) {
    $projectRoot = Split-Path -Parent $scriptDirectory
    $environmentPath = Join-Path $projectRoot ".env.local"
    if (-not (Test-Path -LiteralPath $environmentPath)) {
        throw ".env.local was not found at $environmentPath."
    }
    $settings = @{}
    foreach ($rawLine in Get-Content -LiteralPath $environmentPath -Encoding UTF8) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) { continue }
        $parts = $line.Split("=", 2)
        $settings[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
    $ServerInstance = "$($settings['LGSALEOUT_DB_HOST']),$($settings['LGSALEOUT_DB_PORT'])"
    $Database = $settings['LGSALEOUT_DB_NAME']
    $securePassword = ConvertTo-SecureString $settings['LGSALEOUT_DB_PASSWORD'] -AsPlainText -Force
    $SqlCredential = New-Object System.Management.Automation.PSCredential($settings['LGSALEOUT_DB_USER'], $securePassword)
}

if ([string]::IsNullOrWhiteSpace($ServerInstance)) {
    throw "Specify -ServerInstance, or use -UseProjectEnvironment."
}

Write-Host "[1/4] Loading SQL Server scripting components..." -ForegroundColor Cyan

function Import-SmoAssemblies {
    if ("Microsoft.SqlServer.Management.Smo.Server" -as [type]) {
        return
    }
    if (Get-Module -ListAvailable -Name SqlServer) {
        Import-Module SqlServer -ErrorAction Stop
        return
    }

    $candidateDirectories = @(
        "C:\Program Files (x86)\Microsoft SQL Server Management Studio 20\Common7\IDE",
        "C:\Program Files\Microsoft SQL Server Management Studio 20\Common7\IDE",
        "C:\Program Files (x86)\Microsoft SQL Server Management Studio 19\Common7\IDE",
        "C:\Program Files\Microsoft SQL Server Management Studio 19\Common7\IDE",
        "C:\Program Files\Microsoft SQL Server\160\SDK\Assemblies",
        "C:\Program Files\Microsoft SQL Server\160\COM"
    )
    $assemblyDirectory = $candidateDirectories |
        Where-Object { Test-Path (Join-Path $_ "Microsoft.SqlServer.Smo.dll") } |
        Select-Object -First 1
    if (-not $assemblyDirectory) {
        throw "SQL Server SMO was not found. Install SSMS 19/20 or the PowerShell SqlServer module."
    }

    $dependencyFiles = @(
        "System.Numerics.Vectors.dll",
        "System.Buffers.dll",
        "System.Memory.dll"
    )
    foreach ($dependencyFile in $dependencyFiles) {
        $dependencyPath = Join-Path $assemblyDirectory $dependencyFile
        if (Test-Path $dependencyPath) {
            [void][Reflection.Assembly]::LoadFrom($dependencyPath)
        }
    }
    $unsafePath = Join-Path $assemblyDirectory "Extensions\Application\System.Runtime.CompilerServices.Unsafe.dll"
    if (Test-Path $unsafePath) {
        [void][Reflection.Assembly]::LoadFrom($unsafePath)
    }

    $assemblyFiles = @(
        "Microsoft.SqlServer.Management.Sdk.Sfc.dll",
        "Microsoft.SqlServer.ConnectionInfo.dll",
        "Microsoft.SqlServer.SqlEnum.dll",
        "Microsoft.SqlServer.Smo.dll",
        "Microsoft.SqlServer.SmoExtended.dll"
    )
    foreach ($assemblyFile in $assemblyFiles) {
        $assemblyPath = Join-Path $assemblyDirectory $assemblyFile
        if (Test-Path $assemblyPath) {
            [void][Reflection.Assembly]::LoadFrom($assemblyPath)
        }
    }
}

function New-SmoServer {
    param([string]$Instance, [PSCredential]$Credential)

    if ($Credential) {
        $connection = New-Object Microsoft.SqlServer.Management.Common.ServerConnection
        $connection.ServerInstance = $Instance
        $connection.LoginSecure = $false
        $connection.Login = $Credential.UserName
        $connection.SecurePassword = $Credential.Password
        return New-Object Microsoft.SqlServer.Management.Smo.Server($connection)
    }

    return New-Object Microsoft.SqlServer.Management.Smo.Server($Instance)
}

Import-SmoAssemblies
Write-Host "[2/4] Connecting to $ServerInstance / $Database..." -ForegroundColor Cyan
$server = New-SmoServer -Instance $ServerInstance -Credential $SqlCredential
$server.ConnectionContext.Connect()

try {
    $db = $server.Databases[$Database]
    if (-not $db) {
        throw "Database [$Database] was not found on server [$ServerInstance]."
    }

    $tables = @($db.Tables | Where-Object { -not $_.IsSystemObject })
    if ($tables.Count -eq 0) {
        throw "Database [$Database] has no user tables to export."
    }

    $views = @($db.Views | Where-Object { -not $_.IsSystemObject })
    $procedures = @($db.StoredProcedures | Where-Object { -not $_.IsSystemObject })
    $functions = @($db.UserDefinedFunctions | Where-Object { -not $_.IsSystemObject })
    $databaseTriggers = @($db.Triggers | Where-Object { -not $_.IsSystemObject })
    $tableTriggers = @($tables | ForEach-Object { $_.Triggers } | Where-Object { -not $_.IsSystemObject })

    $urns = New-Object System.Collections.Generic.List[Microsoft.SqlServer.Management.Sdk.Sfc.Urn]
    foreach ($object in @($tables) + @($views) + @($procedures) + @($functions) + @($databaseTriggers)) {
        $urns.Add($object.Urn)
    }

    $scripter = New-Object Microsoft.SqlServer.Management.Smo.Scripter($server)
    $options = $scripter.Options
    $options.ScriptSchema = $true
    $options.ScriptData = $false
    $options.WithDependencies = $true
    $options.SchemaQualify = $true
    $options.IncludeHeaders = $true
    $options.IncludeDatabaseContext = $true
    $options.ScriptBatchTerminator = $true
    $options.AnsiFile = $false
    $options.DriAll = $true
    $options.Indexes = $true
    $options.Triggers = $true
    $options.FullTextIndexes = $true
    $options.NoCollation = $true
    $options.Permissions = $false
    $options.ExtendedProperties = $true

    $outputFullPath = [IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = Split-Path -Parent $outputFullPath
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null

    $scriptLines = @($scripter.Script($urns.ToArray()))
    Write-Host "[3/4] Writing schema-only SQL file..." -ForegroundColor Cyan
    $header = @(
        "/*",
        "  LGSaleOut schema-only baseline",
        "  Source: $ServerInstance / $Database",
        "  Generated: $([DateTimeOffset]::Now.ToString('yyyy-MM-dd HH:mm:ss zzz'))",
        "  Contains no table data, SQL logins, database users, or permissions.",
        "*/",
        ""
    )
    [IO.File]::WriteAllLines($outputFullPath, @($header) + $scriptLines, [Text.UTF8Encoding]::new($true))

    $scriptText = [IO.File]::ReadAllText($outputFullPath)
    $missingTriggers = @()
    foreach ($trigger in @($tableTriggers) + @($databaseTriggers)) {
        if ($scriptText.IndexOf($trigger.Name, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            $missingTriggers += "[$($trigger.Schema)].[$($trigger.Name)]"
        }
    }

    if ($missingTriggers.Count -gt 0) {
        Remove-Item -LiteralPath $outputFullPath -Force
        throw "Export validation failed. Missing triggers: $($missingTriggers -join ', '). The incomplete output was removed."
    }

    Write-Host "[4/4] All source triggers were found in the output." -ForegroundColor Cyan

    $summary = [pscustomobject]@{
        OutputPath = $outputFullPath
        Tables = $tables.Count
        Views = $views.Count
        StoredProcedures = $procedures.Count
        Functions = $functions.Count
        TableTriggers = $tableTriggers.Count
        DatabaseTriggers = $databaseTriggers.Count
        Bytes = (Get-Item -LiteralPath $outputFullPath).Length
    }
    $summary | Format-List
    Write-Host "Schema export and trigger validation completed." -ForegroundColor Green
}
finally {
    if ($server.ConnectionContext.IsOpen) {
        $server.ConnectionContext.Disconnect()
    }
}
