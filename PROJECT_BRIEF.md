# Page Count RIP

## Goal

Build a very lightweight Windows `.exe` GUI that shows live page-count status for a running print job.

Initial visible fields:

- Job ID
- Current printed page count
- Connection/status indicator

## Expected Workflow

1. Customer opens the small GUI.
2. App defaults to connecting to the printhead/controller at `192.168.100.200` over SSH.
3. App reads relevant logs during an active job.
4. App parses the current job ID and page count.
5. App refreshes the displayed count while the job runs.
6. Advanced settings allow overriding the IP/hostname for unusual installs.

## Key Requirement

SSH setup must be easy for customers. Avoid requiring command-line setup if possible.

## Open Questions

- What OS will the customer run the GUI on? Assumption: Windows.
- Confirm SSH target: expected default is printhead/controller at `192.168.100.200`.
- What credentials are available: username/password, private key, or both?
- Are logs local files reachable over SSH/SFTP, or do we need to run remote commands like `tail`?
- What does the log format look like for job start, page printed, page complete, job complete, and errors?
- Do customers need saved profiles for multiple printers/RIPs?
- Should page counts reset per job, or keep history?

## Likely Implementation

- Python + PySide6 or Tkinter for the GUI.
- Paramiko for SSH/SFTP log access.
- PyInstaller to package into a single Windows `.exe`.
- Default connection profile using `192.168.100.200`, with a small config file only for overrides.
- Optional encrypted credential storage using Windows Credential Manager.

## Feasibility

This should be straightforward if the logs contain a reliable page-progress signal. The hardest part is not the GUI; it is identifying a stable log pattern across customer environments and making SSH credentials simple without becoming insecure.
