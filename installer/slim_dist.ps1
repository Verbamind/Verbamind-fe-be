param(
    [string]$DistPath = "dist"
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "dist slimming - strip debug, caches, tests" -ForegroundColor Cyan

if (-not (Test-Path $DistPath)) {
    Write-Host "[ERROR] Directory not found: $DistPath" -ForegroundColor Red
    exit 1
}

function Get-DirSizeMB($path) {
    $bytes = (Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $bytes) { return 0 }
    return [math]::Round($bytes / 1MB, 2)
}

$distDirs = @(Get-ChildItem -Path $DistPath -Directory -Filter "*.dist")
if ($distDirs.Count -eq 0) {
    $distDirs = @(Get-ChildItem -Path $DistPath -Directory)
}

foreach ($dir in $distDirs) {
    $target = $dir.FullName
    $name = $dir.Name
    Write-Host ""
    Write-Host "Processing: $name" -ForegroundColor Yellow

    $initialSize = Get-DirSizeMB $target
    Write-Host ("  Initial: {0} MB" -f $initialSize)

    # 1. Delete .pdb files
    $pdbFiles = @(Get-ChildItem -Path $target -Recurse -Include *.pdb -File)
    if ($pdbFiles.Count -gt 0) {
        $pdbSize = Get-DirSizeMB $target
        $pdbFiles | Remove-Item -Force
        Write-Host ("  [.pdb] Removed {0} files" -f $pdbFiles.Count)
    }

    # 2. Delete .pyi type stubs
    $pyiFiles = @(Get-ChildItem -Path $target -Recurse -Include *.pyi -File)
    if ($pyiFiles.Count -gt 0) {
        $pyiFiles | Remove-Item -Force
        Write-Host ("  [.pyi] Removed {0} files" -f $pyiFiles.Count)
    }

    # 3. Delete __pycache__ directories
    $pycacheDirs = @(Get-ChildItem -Path $target -Recurse -Directory -Filter "__pycache__")
    if ($pycacheDirs.Count -gt 0) {
        $pycacheDirs | Remove-Item -Recurse -Force
        Write-Host ("  [__pycache__] Removed {0} dirs" -f $pycacheDirs.Count)
    }

    # 4. Delete test directories
    $testDirs = @(Get-ChildItem -Path $target -Recurse -Directory | Where-Object { $_.Name -match "^tests?$" })
    if ($testDirs.Count -gt 0) {
        $testDirs | Remove-Item -Recurse -Force
        Write-Host ("  [tests/] Removed {0} dirs" -f $testDirs.Count)
    }

    # 5. Delete .pyc files
    $pycFiles = @(Get-ChildItem -Path $target -Recurse -Include *.pyc -File)
    if ($pycFiles.Count -gt 0) {
        $pycFiles | Remove-Item -Force
        Write-Host ("  [.pyc] Removed {0} files" -f $pycFiles.Count)
    }

    # 6. Strip dist-info metadata
    $distInfoDirs = @(Get-ChildItem -Path $target -Recurse -Directory -Filter "*.dist-info")
    foreach ($infoDir in $distInfoDirs) {
        foreach ($fname in @("RECORD", "INSTALLER", "direct_url.json")) {
            $f = Join-Path $infoDir.FullName $fname
            if (Test-Path $f) { Remove-Item $f -Force }
        }
    }

    $finalSize = Get-DirSizeMB $target
    $saved = [math]::Round($initialSize - $finalSize, 2)
    Write-Host ("  Final: {0} MB (saved {1} MB)" -f $finalSize, $saved) -ForegroundColor Green
}

Write-Host ""
Write-Host "Slim complete" -ForegroundColor Green
