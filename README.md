# VeilSpace

Document sharing with server-side redaction and consistent identity aliases.

**Team:** nexora

**Members:** Zaviyar Jawaid, Syed Ali Ayan, Muhammed Hassnain Dasti

**Theme:** Cybersecurity

[Live application](http://91.124.98.60:8787) | [Source code](https://github.com/Warrior-spec/veilspace)

## Problem and AI

Teams often need to share useful documents that contain names, contact details, and identifiers. VeilSpace checks documents before publication, replaces detected private information with redactions or consistent identity aliases, and keeps unreadable or uncertain files private.

OpenAI `gpt-4.1-mini` receives extracted document text and returns structured sensitive text spans, categories, and a review flag. The server combines these findings with deterministic rules, generates a new sanitized PDF, and checks that known detected values are absent before publication. Identical extracted content reuses cached assessments.

## Tech stack

Flutter and Dart clients, an HTML/CSS/JavaScript browser interface, Python FastAPI, SQLite, pypdf, ReportLab, and the OpenAI API. PyInstaller packages the server as a portable Windows executable.

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

The live website is deployed. Android APK packaging and the narrated demo recording are pending. The APK and demo video links will be added when available. Demo credentials belong in the submission form notes, not this public repository.

Resources: Flutter, FastAPI, SQLite, PyInstaller, pypdf, ReportLab, file_selector, and the OpenAI API. No datasets are included. Assessment uses `gpt-4.1-mini` with a 20,000-character input limit, a 2,048-token output limit, one worker, no automatic AI retries, at most 100 requests per UTC day, and a default $1 daily reservation allowance. Identical extracted content reuses cached assessments. Reservations are conservative application estimates, not provider billing totals.

Output is a regenerated text PDF. Original layout and images are not preserved. Scanned pages, encrypted PDFs, unsupported files, and uncertain assessments remain private. Pending originals remain in private staging until retried or deleted. Successful processing removes the original. Detection can miss sensitive information, so this is a hackathon prototype, not a certified privacy system.

## Credits

- [Flutter](https://flutter.dev/) and [file_selector](https://pub.dev/packages/file_selector), Flutter contributors.
- [FastAPI](https://fastapi.tiangolo.com/), Sebastian Ramirez and contributors.
- [SQLite](https://sqlite.org/), SQLite developers.
- [pypdf](https://pypdf.readthedocs.io/), pypdf contributors.
- [ReportLab](https://www.reportlab.com/), ReportLab and contributors.
- [PyInstaller](https://pyinstaller.org/), PyInstaller development team.
- [OpenAI API](https://platform.openai.com/docs/), OpenAI.

No training datasets or custom-trained models are included. Demo documents contain fictional identities and contact details.
