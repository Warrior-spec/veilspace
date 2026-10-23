# VeilSpace

Document sharing with server-side redaction and consistent identity aliases.

**Team:** nexora

**Members:** Zaviyar Jawaid, Syed Ali Ayan, Muhammed Hassnain Dasti

**Theme:** Cybersecurity

[Live application](http://91.124.98.60:8787) | [Android APK](https://raw.githubusercontent.com/Warrior-spec/veilspace/main/downloads/VeilSpace-Android.apk) | [Source code](https://github.com/Warrior-spec/veilspace)

## Downloads

[GitHub release](https://github.com/Warrior-spec/veilspace/releases/tag/v0.1.0)

| Platform | Download |
| --- | --- |
| Android 7.0 or later, ARM64 | [VeilSpace-Android.apk](https://github.com/Warrior-spec/veilspace/releases/download/v0.1.0/VeilSpace-Android.apk) |
| Windows desktop app | [VeilSpace-Windows.zip](https://github.com/Warrior-spec/veilspace/releases/download/v0.1.0/VeilSpace-Windows.zip) |
| Portable Windows server | [VeilSpaceServer.exe](https://github.com/Warrior-spec/veilspace/releases/download/v0.1.0/VeilSpaceServer.exe) |

Extract the entire Windows ZIP and run `veilspace.exe`. Its DLLs and data directory must stay beside it. The Android demo APK uses the development signing key. Release assets include SHA256 checksums.

## Demo login

Use the same demo account on the website, Windows app, and Android app:

| Email | Password |
| --- | --- |
| `demo@demo.com` | `demo12345678` |

The login screen displays these credentials and provides a **Fill demo login** button. Use fictional documents in this shared demo account.

## Problem and AI

Teams often need to share useful documents that contain names, contact details, and identifiers. VeilSpace checks documents before publication, replaces detected private information with redactions or consistent identity aliases, and keeps unreadable or uncertain files private.

OpenAI `gpt-4.1-mini` receives extracted document text and returns structured sensitive text spans, categories, and a review flag. The server combines these findings with deterministic rules, generates a new sanitized PDF, and checks that known detected values are absent before publication. Identical extracted content reuses cached assessments.

## Why we built VeilSpace

We considered familiar AI projects such as a chatbot, image describer, or document analyzer. We chose document privacy because the useful outcome is a file that a team can actually share. Identifying sensitive information is only one step: the system must also remove it from the exported document, decide whether publication can proceed, preserve useful context, and handle later edits.

VeilSpace gives AI a specific role inside a larger application. The model identifies sensitive spans and flags uncertainty. Conventional extraction, deterministic rules, private storage, authentication, PDF generation, verification, revision tracking, and usage controls turn those findings into a working sharing workflow.

| Challenge | How VeilSpace handles it |
| --- | --- |
| Repeated manual checking | The Windows client watches a selected folder and uploads stable new or changed files while open. |
| Different document formats | The server extracts text from DOCX, readable PDF, and UTF-8 TXT files before assessment. |
| Removing information from the actual file | Sanitized text is used to generate a fresh PDF, and the output is checked for known detected values. |
| Keeping documents understandable | Exact normalized names reuse workspace aliases, so the same person can be followed across documents without exposing the original name. |
| Unreadable or uncertain content | Failed and uncertain revisions remain private in Pending instead of entering the shared library. |
| Documents changing after publication | Changed files become revisions, with the previous published version available while a replacement is processing. |
| Avoiding unnecessary API spending | Content caching, duplicate detection, bounded requests, and an atomic daily allowance reduce repeated assessments. Reading shared files does not call AI. |
| Making the result usable by a team | Authenticated members browse published documents through the website and shared client interface; owners control retry and deletion. |

The distinction is the complete path from a local file to a controlled, sanitized publication. Each component addresses a practical problem in that path. The prototype's limitations and current platform build status are documented below.

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

The live website and installable ARM64 Android APK are available at the links above. The narrated demo video link will be added when available. The public demo credentials above are also available for the submission form notes.

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
