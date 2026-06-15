# Page Count RIP

Minimal Windows GUI for showing live print-job page count status.

Current prototype:

- Displays `Job ID`
- Displays job page count from Kareela `pages current/total` lines
- Tests read-only SSH status against one or two printer/controller Ethernet links
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

Then click `Test SSH Status`.

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

The preferred field install is the packaged Windows release. It installs into the
current user's app data folder, preserves machine-specific config on updates, and
creates a desktop shortcut.

On the printer computer, run this in PowerShell:

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

Next live test is to run another small job and confirm the UI tracks progress
from `pages 0/1` to the final completed page count.

The active job lock is stored in `last_job_state.json` on the print computer and
is intentionally not committed. Delete that file to clear the lock manually.
