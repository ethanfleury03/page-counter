# SSH Setup Options

## Customer Experience Goal

The customer should not need command-line SSH knowledge. Ideally they only enter/select:

- Connect/test button
- Optional advanced override for RIP/controller IP address or hostname
- Optional site/printer label if multiple profiles are needed later

## Known Constraint

Arrow expects the SSH username and password to be the same every time.

Default printhead/controller IP is expected to be `192.168.100.200` across most installs.

## Recommended MVP

Hardcode the SSH username and password in the app config/code for the first prototype, but only if the SSH account is tightly limited.

Customer flow:

1. Install/open the app.
2. App uses default host `192.168.100.200`.
3. Click `Test Connection`.
4. If connection fails, open `Advanced` and override host/IP.
5. App saves any override locally.
6. App connects automatically after that.

Required safeguards:

- SSH account must be read-only or least-privilege.
- Account should only be able to read the needed log file(s).
- Do not use an admin/root account.
- Prefer restricting commands to `tail`, `cat`, or SFTP read access if possible.
- Assume embedded credentials can be extracted from the `.exe`.

## Better Production Option

Use the same username, but generate a per-customer password or key during install/onboarding.

Customer flow remains simple:

1. Enter IP address.
2. Enter activation code or import a small config file.
3. App stores credentials using Windows Credential Manager.
4. App connects automatically after that.

Benefits:

- If one customer leaks/extracts credentials, it does not expose every deployment.
- Credentials can be rotated/revoked per customer.
- Still avoids asking customers to understand SSH.

## Simplest Secure-ish Option

Hardcode username, ask for password once, then save it in Windows Credential Manager.

This avoids embedding the password in the binary, but requires the installer/technician/customer to know the password once.

## Decision

For prototype: hardcode credentials and default host `192.168.100.200`; only ask for host/IP if the default fails.

For customer deployment: hardcode only if the remote SSH account is locked down to log-reading permissions. Otherwise use per-customer credentials or Windows Credential Manager.
