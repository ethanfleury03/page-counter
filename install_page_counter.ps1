param(
    [string]$InstallDir = "$env:LOCALAPPDATA\Arrow\PageCountRIP",
    [string]$Repo = "ethanfleury03/page-counter",
    [switch]$NoDesktopShortcut
)

$ErrorActionPreference = "Stop"

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [string]$Description,
        [int]$Attempts = 3
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            return & $ScriptBlock
        } catch {
            if ($attempt -eq $Attempts) {
                throw
            }

            $delaySeconds = 2 * $attempt
            Write-Warning "${Description} failed on attempt ${attempt}/${Attempts}. Retrying in ${delaySeconds} seconds..."
            Start-Sleep -Seconds $delaySeconds
        }
    }
}

function Get-LatestReleaseZipUrl {
    param([string]$Repository)

    try {
        $release = Invoke-WithRetry -Description "GitHub latest-release lookup" -ScriptBlock {
            Invoke-RestMethod `
                -Headers @{ "User-Agent" = "PageCountRIP-Installer" } `
                -Uri "https://api.github.com/repos/$Repository/releases/latest"
        }
    } catch {
        Write-Warning "GitHub API latest-release lookup failed. Falling back to direct latest release download URL."
        return "https://github.com/$Repository/releases/latest/download/PageCountRIP-windows.zip"
    }

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
    Invoke-WithRetry -Description "Release zip download" -ScriptBlock {
        Invoke-WebRequest -UseBasicParsing -Uri $ZipUrl -OutFile $zipPath
    } | Out-Null
    Expand-Archive -Force -Path $zipPath -DestinationPath $extractDir

    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
    $files = @(
        "PageCountRIP.exe",
        "printer_config.example.json",
        "install_page_counter.bat",
        "install_page_counter.ps1",
        "update_page_counter.bat",
        "update_page_counter.ps1",
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
    } else {
        Update-ExistingConfig -ConfigPath $configPath
    }

    Remove-Item -Recurse -Force $tempRoot
}

function Update-ExistingConfig {
    param([string]$ConfigPath)

    try {
        $config = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
        $changed = $false

        if (-not $config.PSObject.Properties.Name.Contains("poll_interval_seconds") -or [int]$config.poll_interval_seconds -ne 1) {
            $config | Add-Member -NotePropertyName "poll_interval_seconds" -NotePropertyValue 1 -Force
            $changed = $true
        }

        if ($config.connections) {
            $connections = @($config.connections | Where-Object { $_.host -ne "192.168.100.201" })
            if ($connections.Count -ne @($config.connections).Count) {
                $config.connections = $connections
                $changed = $true
            }
        }

        if ($changed) {
            $json = ($config | ConvertTo-Json -Depth 8) + [Environment]::NewLine
            [System.IO.File]::WriteAllText($ConfigPath, $json, [System.Text.UTF8Encoding]::new($false))
        }
    } catch {
        Write-Warning "Could not update existing printer_config.json defaults: $($_.Exception.Message)"
    }
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
