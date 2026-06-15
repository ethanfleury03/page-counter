param(
    [string]$InstallDir = "$env:LOCALAPPDATA\Arrow\PageCountRIP",
    [string]$Repo = "ethanfleury03/page-counter"
)

$ErrorActionPreference = "Stop"

$installer = Join-Path $PSScriptRoot "install_page_counter.ps1"
if (-not (Test-Path $installer)) {
    throw "Could not find install_page_counter.ps1 next to this update script."
}

& $installer -InstallDir $InstallDir -Repo $Repo -NoDesktopShortcut

Write-Host "Page Count RIP updated. Existing printer_config.json was preserved."

