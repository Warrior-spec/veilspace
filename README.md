# VeilSpace

Document sharing with server-side redaction and consistent identity aliases.

## Applications

- Windows: upload new and changed files from a selected folder.
- Android and web: upload manually and browse shared documents.
- Supported inputs: DOCX, text-based PDF, and TXT.
- Sanitized output: PDF. Unreadable or uncertain documents remain pending.

The server supports signup, login, expiring sessions, and logout. The shared client includes login and registration screens. Document processing is under development.

## Portable server

Run `VeilSpaceServer.exe` from a writable folder. It creates `VeilSpaceData` beside itself, initializes SQLite, and prints connection URLs. Python and MySQL installations are not required on the target server.

Approve the Windows administrator prompt to let the launcher configure its inbound firewall rule. Provider firewalls and NAT may still need an inbound TCP rule for port 8787. The printed public address is a candidate, not a connectivity check. HTTPS is required before using real credentials or documents over the internet.

Keep the executable running. Keep the data folder when upgrading. Backups must use SQLite's backup API or be taken after stopping the server.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
scripts\test-server.cmd
scripts\run-server.cmd
```

Build the server:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[build]"
scripts\build-server.cmd
```

Output: `dist/VeilSpaceServer.exe`.

Flutter setup and builds: [client/README.md](client/README.md).

## Roadmap

[Milestones](docs/MILESTONES.md) | [Architecture](docs/ARCHITECTURE.md)

## Submission

Theme: Cybersecurity. Team details, deployment, APK, and demo links will be added before submission.

Resources: Flutter, FastAPI, SQLite, PyInstaller, and the OpenAI API. No datasets are included. The model and processing limits will be documented when assessment is implemented.
