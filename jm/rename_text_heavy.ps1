$ErrorActionPreference = "Stop"
$workspace = "c:\Users\DELL\my-image-hosting\jm"
$jsonPath = Join-Path $workspace "image_classification.json"

# Read JSON
$jsonRaw = Get-Content -Path $jsonPath -Raw -Encoding UTF8
$json = $jsonRaw | ConvertFrom-Json
$textHeavy = @($json.text_heavy)

# Keywords sorted by length descending
$keywords = @(
    "背景故事",  # 4
    "实装示例",  # 4
    "玩法说明",  # 4
    "使用方式",  # 4
    "职位标准",  # 4
    "功能介绍",  # 4
    "商业模式",  # 4
    "技术原理",  # 4
    "选拔流程",  # 4
    "世界观",    # 3
    "介绍",      # 2
    "详情",      # 2
    "背景",      # 2
    "说明",      # 2
    "构造",      # 2
    "使用",      # 2
    "外观",      # 2
    "课程"       # 2
)

function Get-NewName {
    param([string]$filename)

    # Rule 1: if contains "设定", skip
    if ($filename.Contains("设定")) {
        return $filename
    }

    $ext = [System.IO.Path]::GetExtension($filename)
    $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($filename)

    # Find the last separator (_ or -) to determine the suffix
    $lastUnder = $nameWithoutExt.LastIndexOf('_')
    $lastDash = $nameWithoutExt.LastIndexOf('-')
    $lastSep = [Math]::Max($lastUnder, $lastDash)

    if ($lastSep -ge 0) {
        $prefix = $nameWithoutExt.Substring(0, $lastSep + 1)
        $suffix = $nameWithoutExt.Substring($lastSep + 1)
    } else {
        $prefix = ""
        $suffix = $nameWithoutExt
    }

    # Rule 2: check if suffix contains any keyword (longest first)
    foreach ($keyword in $keywords) {
        if ($suffix.Contains($keyword)) {
            if ($keyword -eq "背景故事") {
                # Replace "背景故事" with "设定", keeping trailing digits
                $regex = [regex]::new("背景故事(\d*)")
                $newSuffix = $regex.Replace($suffix, '设定$1', 1)
                return $prefix + $newSuffix + $ext
            }
            # Replace entire suffix with "设定"
            return $prefix + "设定" + $ext
        }
    }

    # Rule 3: append _设定 before extension
    return $nameWithoutExt + "_设定" + $ext
}

# First pass: compute all new names
$mapping = @()
for ($i = 0; $i -lt $textHeavy.Count; $i++) {
    $oldName = $textHeavy[$i]
    $newName = Get-NewName -filename $oldName
    $mapping += [PSCustomObject]@{
        OldName  = $oldName
        NewName  = $newName
        Skipped  = ($oldName -eq $newName)
        Conflict = $false
        NotFound = $false
        Note     = ""
    }
}

# Second pass: resolve conflicts
# Collect all "taken" names: skipped files, text_light, unanalyzed
$takenNames = [System.Collections.Generic.HashSet[string]]::new()
foreach ($m in $mapping) {
    if ($m.Skipped) {
        [void]$takenNames.Add($m.NewName)
    }
}
foreach ($name in $json.text_light) {
    [void]$takenNames.Add($name)
}
foreach ($name in $json.unanalyzed) {
    [void]$takenNames.Add($name)
}

# Also collect all old names of non-skipped files (they will be freed)
$willBeFreed = [System.Collections.Generic.HashSet[string]]::new()
foreach ($m in $mapping) {
    if (-not $m.Skipped) {
        [void]$willBeFreed.Add($m.OldName)
    }
}

foreach ($m in $mapping) {
    if ($m.Skipped) {
        continue
    }

    $newName = $m.NewName

    # Check conflict: in takenNames or file exists on disk (and not being freed)
    $needResolve = $takenNames.Contains($newName)
    if (-not $needResolve) {
        $targetPath = Join-Path $workspace $newName
        if (Test-Path -LiteralPath $targetPath) {
            # Only a conflict if the existing file is NOT being freed (i.e., not an old name of another text_heavy file)
            if (-not $willBeFreed.Contains($newName)) {
                $needResolve = $true
            }
        }
    }

    if ($needResolve) {
        $m.Conflict = $true
        $ext = [System.IO.Path]::GetExtension($newName)
        $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($newName)
        $counter = 2
        $candidateName = "${nameWithoutExt}${counter}${ext}"
        while ($takenNames.Contains($candidateName) -or `
              ((Test-Path -LiteralPath (Join-Path $workspace $candidateName)) -and -not $willBeFreed.Contains($candidateName))) {
            $counter++
            $candidateName = "${nameWithoutExt}${counter}${ext}"
        }
        $newName = $candidateName
        $m.NewName = $newName
        $m.Note = "suffix $counter"
    }

    [void]$takenNames.Add($newName)
}

# Third pass: rename files
$renamedFiles = @()
$skippedFiles = @()
$notFoundFiles = @()

foreach ($m in $mapping) {
    if ($m.Skipped) {
        $skippedFiles += $m
        continue
    }

    $oldPath = Join-Path $workspace $m.OldName

    if (-not (Test-Path -LiteralPath $oldPath)) {
        $m.NotFound = $true
        $notFoundFiles += $m
        continue
    }

    Rename-Item -LiteralPath $oldPath -NewName $m.NewName
    $renamedFiles += $m
}

# Update JSON
$newTextHeavy = @()
foreach ($m in $mapping) {
    if ($m.NotFound) {
        $newTextHeavy += $m.OldName
    } else {
        $newTextHeavy += $m.NewName
    }
}

$json.text_heavy = $newTextHeavy

# Save JSON with UTF-8 no BOM
$jsonString = $json | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($jsonPath, $jsonString, [System.Text.UTF8Encoding]::new($false))

# Output results
Write-Host ""
Write-Host "========== RENAMED FILES ($($renamedFiles.Count)) =========="
foreach ($m in $renamedFiles) {
    $note = if ($m.Conflict) { "  [CONFLICT: $($m.Note)]" } else { "" }
    Write-Host "  $($m.OldName)  ->  $($m.NewName)$note"
}

Write-Host ""
Write-Host "========== SKIPPED - already has 设定 ($($skippedFiles.Count)) =========="
foreach ($m in $skippedFiles) {
    Write-Host "  $($m.OldName)"
}

Write-Host ""
Write-Host "========== NOT FOUND ($($notFoundFiles.Count)) =========="
foreach ($m in $notFoundFiles) {
    Write-Host "  $($m.OldName)"
}

Write-Host ""
Write-Host "Summary: $($renamedFiles.Count) renamed, $($skippedFiles.Count) skipped, $($notFoundFiles.Count) not found"