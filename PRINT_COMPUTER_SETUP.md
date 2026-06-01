# Print Computer Setup

Use this checklist for the first install on the computer connected to the printer/RIP.

## 1. Confirm Machine Details

- Windows version:
- Python version, if running from source:
- Printer/RIP/controller connection type:
- Expected controller IP address:
- Expected SSH username:
- Log file path or command, when known:

## 2. Install From Git

Install Git for Windows if needed, then clone the repo:

```powershell
git clone https://github.com/ethanfleury03/page-counter.git
cd page-counter
```

For later updates:

```powershell
git pull
```

## 3. Run Prototype From Source

If Python is installed:

```powershell
python -m pip install -r requirements.txt
python page_count_rip.py
```

Expected result: a small "Page Count RIP" window opens and shows placeholder values.
Click `Test SSH Status` to connect to `192.168.100.200` as `root/root` and run
read-only discovery commands.

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

## 5. Build Windows EXE

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
- GUI does not send print jobs or hardware commands.
- Live log parsing still needs the real job/page-count log format.
- `set_job_status(job_id, total_pages_sent)` is the integration point for the parser.
