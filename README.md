# Page Count RIP

Minimal Windows GUI for showing live print-job page count status.

Current prototype:

- Displays `Job ID`
- Displays `Total Pages Sent`
- Tests read-only SSH status against one or two printer/controller Ethernet links
- Runs only allowlisted read commands from `printer_config.json`

## Run Locally

```bash
python3 -m pip install -r requirements.txt
python3 page_count_rip.py
```

## Configure Printer SSH Status

Copy the example config:

```bash
cp printer_config.example.json printer_config.json
```

Edit `printer_config.json` with the two printer/controller Ethernet IPs and SSH usernames.
Do not commit `printer_config.json`; it is machine-specific.

Set passwords as environment variables so credentials are not stored in git:

```powershell
$env:PAGE_COUNT_RIP_PRINTER_1_PASSWORD="password for ethernet 1"
$env:PAGE_COUNT_RIP_PRINTER_2_PASSWORD="password for ethernet 2"
python page_count_rip.py
```

Then click `Test SSH Status`.

## Build Windows EXE

Run this from the project folder on a Windows machine with Python installed:

```bat
build_windows.bat
```

The output should be:

```text
dist\PageCountRIP.exe
```

## Next Data Hook

When sample logs are available, add the relevant paths to `log_paths` in
`printer_config.json`. The app will tail those files read-only.

After we identify the real job/page-count log format, plug the parser into:

```python
app.set_job_status(job_id, total_pages_sent)
```
