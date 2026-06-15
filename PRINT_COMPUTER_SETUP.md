# Print Computer Setup

Use this checklist for the first install on the computer connected to the printer/RIP.

## 1. Confirm Machine Details

- Windows version:
- Python version, if running from source:
- Printer/RIP/controller connection type:
- Expected controller IP address:
- Expected SSH username:
- Log file path or command, when known:

## 2. Preferred Install From GitHub Release

Use this path for normal printer computers. It does not require Python on the
printer computer.

Download and run this file from the latest GitHub release:

```text
PageCountRIP-Setup.bat
```

Release page:

```text
https://github.com/ethanfleury03/page-counter/releases/latest
```

If PowerShell is easier than downloading the setup file manually, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
$url = "https://raw.githubusercontent.com/ethanfleury03/page-counter/main/install_page_counter.ps1"
$installer = "$env:TEMP\install_page_counter.ps1"
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $installer
powershell -NoProfile -ExecutionPolicy Bypass -File $installer
```

Default install location:

```text
%LOCALAPPDATA%\Arrow\PageCountRIP
```

The installer creates `printer_config.json` if it does not already exist.
Future updates preserve that machine-specific config.

For later updates:

```bat
%LOCALAPPDATA%\Arrow\PageCountRIP\update_page_counter.bat
```

## 3. Install From Git For Development

Install Git for Windows if needed, then clone the repo:

```powershell
git clone https://github.com/ethanfleury03/page-counter.git
cd page-counter
```

For later updates:

```powershell
git pull
```

## 4. Run Prototype From Source

If Python is installed:

```powershell
python -m pip install -r requirements.txt
python page_count_rip.py
```

Expected result: a small "Page Count RIP" window opens and shows placeholder values.
Click `Test SSH Status` to connect to `192.168.100.200` as `root/root` and run
read-only status commands. The default status test tails likely printer logs
discovered on the controller, then parses the useful fields into a summary:

- `/pes_client.log`
- `/var/log/pdl/pdl.log`
- `/var/log/gymea/gymea.log`
- `/var/log/kareela/kareela.log`
- `/var/log/kenmare/kenmare.log`
- `/var/log/kirrawee/kirrawee.log`
- `/var/log/messages`

The summary currently includes job ID, job state, job page count from Kareela
`pages current/total` lines, completed pages, job media length, the printhead
lifetime counter as diagnostic data, printed media length, engine state,
ready/primed/capped state, last print/service timestamps, pages since last wipe,
active job lock state, and the latest Kareela activity marker found in the
tailed logs.

## 4. Optional Read-Only SSH Override

The app works without a config file. To override host, credentials, commands, or
log paths, copy the example config:

```powershell
Copy-Item printer_config.example.json printer_config.json
```

Edit `printer_config.json` with the printer Ethernet IP addresses and SSH credentials.

Click `Test SSH Status`.

This test only checks TCP port 22, logs in over SSH, and runs allowlisted read
commands from the config file. It does not send print jobs or fire hardware.

If SSH succeeds, save the output so we can identify the real status/log paths.

Best next test: click `Test SSH Status`, run a tiny scrap/calibration job with
the normal printer software, then click `Test SSH Status` again. Confirm the job
ID, state, `pages current/total`, and completed pages match the printer UI.

The app stores the active Kareela job lock in `last_job_state.json`. Delete that
file if the test machine needs a clean slate after an interrupted job.

## 5. Build Windows EXE Locally

From the project folder:

```bat
build_windows.bat
```

Expected output:

```text
dist\PageCountRIP.exe
```

## 6. Hardware/Network Checks

Before sending any real print commands:

- Confirm the existing production print workflow still works.
- Confirm this app opens without interfering with the printer software.
- Confirm the print computer can reach the controller IP.
- Confirm SSH credentials are available.
- Run only read/status/log checks first.

## 7. First Live Test

- Use scrap material.
- Use a tiny test job or calibration pattern.
- Keep the existing production software available as fallback.
- Record the job ID, expected page count, observed page count, and any log lines.

## Current Prototype Limits

- GUI can test read-only SSH connectivity.
- GUI parses the current controller status and Kareela job page-count lines.
- GUI does not send print jobs or hardware commands.
- Per-job page-count parsing is based on Kareela `GymeaJobQueueCtlr` and
  `PrintSessionMgr::notifyJobStatus()` lines.
