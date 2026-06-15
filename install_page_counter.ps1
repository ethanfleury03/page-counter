param(
    [string]$InstallDir = "$env:LOCALAPPDATA\Arrow\PageCountRIP",
    [string]$Repo = "ethanfleury03/page-counter",
    [switch]$NoDesktopShortcut
)

$ErrorActionPreference = "Stop"

function Get-LatestReleaseZipUrl {
    param([string]$Repository)

    $release = Invoke-RestMethod `
        -Headers @{ "User-Agent" = "PageCountRIP-Installer" } `
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
    Copy-Item -Force -Path (Join-Path $extractDir "PageCountRIP.exe") -Destination $TargetDir
    Copy-Item -Force -Path (Join-Path $extractDir "printer_config.example.json") -Destination $TargetDir
    Copy-Item -Force -Path (Join-Path $extractDir "install_page_counter.bat") -Destination $TargetDir
    Copy-Item -Force -Path (Join-Path $extractDir "install_page_counter.ps1") -Destination $TargetDir
    Copy-Item -Force -Path (Join-Path $extractDir "update_page_counter.bat") -Destination $TargetDir
    Copy-Item -Force -Path (Join-Path $extractDir "update_page_counter.ps1") -Destination $TargetDir
    Copy-Item -Force -Path (Join-Path $extractDir "PRINT_COMPUTER_SETUP.md") -Destination $TargetDir

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

if (-not $NoDesktopShortcut) {
    New-DesktopShortcut -TargetDir $InstallDir
}

Write-Host "Page Count RIP installed to: $InstallDir"
Write-Host "Run: $InstallDir\PageCountRIP.exe"
Write-Host "Config: $InstallDir\printer_config.json"
