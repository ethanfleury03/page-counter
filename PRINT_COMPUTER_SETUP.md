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
python page_count_rip.py
```

Expected result: a small "Page Count RIP" window opens and shows placeholder values.

## 4. Build Windows EXE

From the project folder:

```bat
build_windows.bat
```

Expected output:

```text
dist\PageCountRIP.exe
```

## 5. Hardware/Network Checks

Before sending any real print commands:

- Confirm the existing production print workflow still works.
- Confirm this app opens without interfering with the printer software.
- Confirm the print computer can reach the controller IP.
- Confirm SSH credentials are available.
- Run only read/status/log checks first.

## 6. First Live Test

- Use scrap material.
- Use a tiny test job or calibration pattern.
- Keep the existing production software available as fallback.
- Record the job ID, expected page count, observed page count, and any log lines.

## Current Prototype Limits

- Display-only GUI.
- No SSH connection yet.
- No live log parsing yet.
- `set_job_status(job_id, total_pages_sent)` is the integration point for the next hardware/log hook.
