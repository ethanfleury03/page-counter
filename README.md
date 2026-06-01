# Page Count RIP

Minimal Windows GUI for showing live print-job page count status.

Current prototype:

- Displays `Job ID`
- Displays lifetime page count when the controller exposes it
- Tests read-only SSH status against one or two printer/controller Ethernet links
- Runs only allowlisted read commands
- Defaults to `192.168.100.200` with SSH `root/root`
- Parses current controller state from discovered Memjet/Duraflex logs

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

## Current Data Hook

The parser currently reads:

- Lifetime page count and printed media length from `/pes_client.log`, when present
- Live print/service state from `/var/log/pdl/pdl.log`
- Service/activity markers from the tailed controller logs

Next live test is to compare the parsed status before and after a tiny scrap job
so we can identify the exact per-job page counter.
