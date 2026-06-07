[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$SourcePath,
    [string]$TargetDir,
    [string]$Branch = 'main'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Decode-Utf8 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Base64
    )

    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Base64))
}

$scriptRoot = if ($PSScriptRoot) {
    $PSScriptRoot
} else {
    Split-Path -Parent $MyInvocation.MyCommand.Path
}

if (-not $SourcePath) {
    $SourcePath = Join-Path 'F:\Develop\AI\sillytavern\dist' (Decode-Utf8 '5LiW55WM5Lmm57yW6L6R6ISa5pysXGluZGV4Lmpz')
}

if (-not $TargetDir) {
    $TargetDir = Join-Path $scriptRoot (Decode-Utf8 '5o+S5Lu2XOS4lueVjOS5pnBsdXM=')
}

function Get-GitPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $normalizedRepoRoot = $RepoRoot.TrimEnd('\', '/')
    $normalizedPath = $Path

    if ($normalizedPath.Length -le $normalizedRepoRoot.Length -or
        -not $normalizedPath.StartsWith($normalizedRepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside of repo root: $normalizedPath"
    }

    $relativePath = $normalizedPath.Substring($normalizedRepoRoot.Length).TrimStart('\', '/')
    return $relativePath -replace '\\', '/'
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Get-BackupFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Directory
    )

    $datePrefix = Get-Date -Format 'M.d'
    $defaultName = "${datePrefix}index.js"
    $defaultPath = Join-Path $Directory $defaultName

    if (-not (Test-Path -LiteralPath $defaultPath)) {
        return $defaultPath
    }

    $fallbackName = "{0}-{1}index.js" -f $datePrefix, (Get-Date -Format 'HHmmss')
    return (Join-Path $Directory $fallbackName)
}

$repoRoot = (Resolve-Path -LiteralPath $scriptRoot).Path
$resolvedSource = (Resolve-Path -LiteralPath $SourcePath).Path
$resolvedTargetDir = (Resolve-Path -LiteralPath $TargetDir).Path
$targetFile = Join-Path $resolvedTargetDir 'index.js'
$tempFile = Join-Path $resolvedTargetDir 'index.js.tmp'
$backupFile = Get-BackupFilePath -Directory $resolvedTargetDir
$commitMessage = "update worldbookplus $(Get-Date -Format 'yyyy-MM-dd_HHmmss')"

if (-not (Test-Path -LiteralPath $resolvedSource -PathType Leaf)) {
    throw "Source file not found: $resolvedSource"
}

if (-not (Test-Path -LiteralPath $resolvedTargetDir -PathType Container)) {
    throw "Target directory not found: $resolvedTargetDir"
}

Push-Location $repoRoot
try {
    if (Test-Path -LiteralPath $tempFile) {
        Remove-Item -LiteralPath $tempFile -Force
    }

    if ($PSCmdlet.ShouldProcess($resolvedSource, "Copy to temp file $tempFile")) {
        Copy-Item -LiteralPath $resolvedSource -Destination $tempFile -Force
    }

    if (Test-Path -LiteralPath $targetFile -PathType Leaf) {
        if ($PSCmdlet.ShouldProcess($targetFile, "Rename to backup $backupFile")) {
            Move-Item -LiteralPath $targetFile -Destination $backupFile
        }
    }

    if ($PSCmdlet.ShouldProcess($tempFile, "Move temp file to $targetFile")) {
        Move-Item -LiteralPath $tempFile -Destination $targetFile -Force
    }

    $targetGitPath = Get-GitPath -Path $targetFile -RepoRoot $repoRoot
    $backupGitPath = if (Test-Path -LiteralPath $backupFile -PathType Leaf) {
        Get-GitPath -Path $backupFile -RepoRoot $repoRoot
    } else {
        $null
    }

    $pathsToAdd = @($targetGitPath)
    if ($backupGitPath) {
        $pathsToAdd += $backupGitPath
    }

    if ($PSCmdlet.ShouldProcess('git index', 'Stage plugin update files')) {
        Invoke-External -Description 'git add' -Command {
            git add -- @pathsToAdd
        }
    }

    if ($PSCmdlet.ShouldProcess('git index', 'Create commit')) {
        Invoke-External -Description 'git commit' -Command {
            git commit -m $commitMessage
        }
    }

    if ($PSCmdlet.ShouldProcess("origin/$Branch", 'Push commit')) {
        Invoke-External -Description 'git push' -Command {
            git push origin $Branch
        }
    }

    Write-Host "Updated plugin from: $resolvedSource"
    Write-Host "Backup file: $backupFile"
    Write-Host "Current file: $targetFile"
    Write-Host "Commit message: $commitMessage"
}
finally {
    if (Test-Path -LiteralPath $tempFile) {
        Remove-Item -LiteralPath $tempFile -Force
    }

    Pop-Location
}
