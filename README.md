# VeilSpace

Document sharing with server-side redaction and consistent identity aliases.

## Applications

- Windows: upload new and changed files from a selected folder.
- Android and web: upload manually and browse shared documents.
- Supported inputs: DOCX, text-based PDF, and TXT.
- Sanitized output: PDF. Unreadable or uncertain documents remain pending.

Signup, login, uploads, revision tracking, shared libraries, and sanitized document reading are implemented. Windows watches one selected folder while the app is open. Android and web use manual uploads.

## Portable server

Place a private `.env` containing `OPENAI_API_KEY=...` beside `VeilSpaceServer.exe`, then run it from a writable folder. It creates `VeilSpaceData` beside itself, initializes SQLite, serves the website, and prints connection URLs. Python and MySQL installations are not required on the target server.

Approve the Windows administrator prompt to let the launcher configure its inbound firewall rule. Provider firewalls and NAT may still need an inbound TCP rule for port 8787. The printed public address is a candidate, not a connectivity check. The demo uses HTTP. Use fictional documents and demo credentials; deploy HTTPS before using private data.

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

Resources: Flutter, FastAPI, SQLite, PyInstaller, pypdf, ReportLab, file_selector, and the OpenAI API. No datasets are included. Assessment uses `gpt-4.1-mini` with a 20,000-character input limit, a 2,048-token output limit, one worker, no automatic AI retries, at most 100 requests per UTC day, and a default $1 daily reservation allowance. Identical extracted content reuses cached assessments. Reservations are conservative application estimates, not provider billing totals.

Output is a regenerated text PDF. Original layout and images are not preserved. Scanned pages, encrypted PDFs, unsupported files, and uncertain assessments remain private. Pending originals remain in private staging until retried or deleted. Successful processing removes the original. Detection can miss sensitive information, so this is a hackathon prototype, not a certified privacy system.
