@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -Command "$parts = (Get-Content -Raw -LiteralPath '%~f0') -split '# POWERSHELL_INSTALLER #', 2; Invoke-Expression $parts[1]"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo Page Count RIP setup failed.
  pause
  exit /b %RC%
)

echo.
echo Page Count RIP setup complete.
pause
exit /b 0

# POWERSHELL_INSTALLER #
$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:LOCALAPPDATA "Arrow\PageCountRIP"
$Repo = "ethanfleury03/page-counter"

function Get-LatestReleaseZipUrl {
    param([string]$Repository)

    $release = Invoke-RestMethod `
        -Headers @{ "User-Agent" = "PageCountRIP-Setup" } `
        -Uri "https://api.github.com/repos/$Repository/releases/latest"

    $asset = $release.assets | Where-Object { $_.name -eq "PageCountRIP-windows.zip" } | Select-Object -First 1
    if (-not $asset) {
        throw "Latest release for $Repository does not include PageCountRIP-windows.zip."
    }

    return $asset.browser_download_url
}

function Install-Release {
    param(
        [string]$ZipUrl,
        [string]$TargetDir
    )

    $tempRoot = Join-Path $env:TEMP ("PageCountRIP-" + [guid]::NewGuid().ToString("N"))
    $zipPath = Join-Path $tempRoot "PageCountRIP-windows.zip"
    $extractDir = Join-Path $tempRoot "extract"

    New-Item -ItemType Directory -Force -Path $tempRoot, $extractDir | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri $ZipUrl -OutFile $zipPath
    Expand-Archive -Force -Path $zipPath -DestinationPath $extractDir

    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
    $files = @(
        "PageCountRIP.exe",
        "printer_config.example.json",
        "install_page_counter.bat",
        "install_page_counter.ps1",
        "update_page_counter.bat",
        "update_page_counter.ps1",
        "PageCountRIP-Setup.bat",
        "PRINT_COMPUTER_SETUP.md"
    )

    foreach ($file in $files) {
        $source = Join-Path $extractDir $file
        if (Test-Path $source) {
            Copy-Item -Force -Path $source -Destination $TargetDir
        }
    }

    $configPath = Join-Path $TargetDir "printer_config.json"
    if (-not (Test-Path $configPath)) {
        Copy-Item -Path (Join-Path $TargetDir "printer_config.example.json") -Destination $configPath
    }

    Remove-Item -Recurse -Force $tempRoot
}

function New-DesktopShortcut {
    param([string]$TargetDir)

    $desktop = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktop "Page Count RIP.lnk"
    $exePath = Join-Path $TargetDir "PageCountRIP.exe"

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $TargetDir
    $shortcut.Description = "Page Count RIP"
    $shortcut.Save()
}

$zipUrl = Get-LatestReleaseZipUrl -Repository $Repo
Install-Release -ZipUrl $zipUrl -TargetDir $InstallDir
New-DesktopShortcut -TargetDir $InstallDir

Write-Host "Page Count RIP installed to: $InstallDir"
Write-Host "Run: $InstallDir\PageCountRIP.exe"
Write-Host "Config: $InstallDir\printer_config.json"
