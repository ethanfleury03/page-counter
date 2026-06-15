# Page Count RIP

Minimal Windows GUI for showing live print-job page count status.

Current prototype:

- Displays `Job ID`
- Displays `Job State`
- Displays job page count from Kareela `pages current/total` lines
- Auto-refreshes read-only SSH status against printer/controller Ethernet links
- Runs only allowlisted read commands
- Defaults to `192.168.100.200` with SSH `root/root`
- Parses current controller state from discovered Memjet/Duraflex logs
- Treats the `74858` printhead counter as lifetime diagnostic data, not job qty
- Locks onto the active Kareela job ID while a job is printing

## Run Locally

```bash
python3 -m pip install -r requirements.txt
python3 page_count_rip.py
```

Leave the window open before or during a print job. It refreshes automatically.
Use `Refresh Now` only for an immediate manual check.

## Optional Printer SSH Override

The app works without a config file. To override host, credentials, commands, or
log paths, copy the example config:

```bash
cp printer_config.example.json printer_config.json
```

Edit `printer_config.json`. Do not commit `printer_config.json`; it is
machine-specific.

## Build Windows EXE

Run this from the project folder on a Windows machine with Python installed:

```bat
build_windows.bat
```

The output should be:

```text
dist\PageCountRIP.exe
```

## Install On A Printer Computer

The easiest field install is the one-file setup script from the latest GitHub
release:

```text
PageCountRIP-Setup.bat
```

Download it from the latest release, run it, and it installs the app into the
current user's app data folder, preserves machine-specific config on updates,
and creates a desktop shortcut.

If you only have PowerShell available, this does the same thing:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
$url = "https://raw.githubusercontent.com/ethanfleury03/page-counter/main/install_page_counter.ps1"
$installer = "$env:TEMP\install_page_counter.ps1"
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $installer
powershell -NoProfile -ExecutionPolicy Bypass -File $installer
```

After that, launch:

```text
%LOCALAPPDATA%\Arrow\PageCountRIP\PageCountRIP.exe
```

To update later, run:

```text
%LOCALAPPDATA%\Arrow\PageCountRIP\update_page_counter.bat
```

## Current Data Hook

The parser currently reads:

- Printhead lifetime counter and printed media length from `/pes_client.log`, when present
- Live print/service state from `/var/log/pdl/pdl.log`
- Job ID, job state, `pages current/total`, completed pages, and media length from `/var/log/kareela/kareela.log`

Normal operator sequence:

1. Open `PageCountRIP.exe`.
2. Leave auto refresh enabled.
3. Start the print job in the normal printer/RIP software.
4. Watch `Job State` and `Job Page Count` update during and after the job.

Next live test is to run another small job and confirm the UI tracks progress
from `pages 0/1` to the final completed page count without manually refreshing.

The active job lock is stored in `last_job_state.json` on the print computer and
is intentionally not committed. Delete that file to clear the lock manually.
