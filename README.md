# Page Count RIP

Minimal Windows GUI for showing live print-job page count status.

Current prototype:

- Displays `Job ID`
- Displays `Total Pages Sent`
- Does not connect to SSH/logs yet

## Run Locally

```bash
python3 page_count_rip.py
```

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

When sample logs are available, plug the parser/SSH polling layer into:

```python
app.set_job_status(job_id, total_pages_sent)
```
