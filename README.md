# VeilSpace

A shared document workspace that processes Word, PDF, and text files before publishing sanitized copies to members.

**Status:** foundation only. Authentication, redaction, storage, and sync are planned; this version must not receive private documents.

## Product

- Windows: choose a watched folder; new and modified files upload automatically.
- Android APK and website: manually select files to upload.
- One fixed backend, with no server configuration in the user interface.
- One workspace with My Files, Shared Files, and Pending views.
- Server-side extraction, contextual AI detection, redaction, consistent identity aliases, and revision handling.
- Unreadable or uncertain documents remain pending instead of publishing.
- Initial inputs: `.docx`, text-based `.pdf`, and `.txt`. Legacy `.doc` and scanned PDFs are outside the initial scope.
- Published copies will be sanitized PDFs. Originals enter private temporary server storage, never the shared library.

## Stack

- Flutter: shared Windows, Android, and web client.
- FastAPI: processing API and worker, hosted on the Windows server.
- MySQL: users, memberships, documents, revisions, aliases, jobs, and usage reservations.
- Private server disk: staging and sanitized documents, outside the web root.

## Run the backend foundation

PowerShell, from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn veilspace.main:app --app-dir server --host 127.0.0.1 --port 8000
```

The `/health` route reports that the API is running. It does not claim that MySQL or the document pipeline is ready. Development API documentation is at `/docs`.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The application runs without credentials for this first milestone. Before later database and AI work, copy `.env.example` to `.env` and set server-only credentials. Never commit `.env`.

If an isolated editable build fails on this machine, install the build tools and locked development dependencies first, then install without build isolation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
```

Windows convenience commands: `scripts\run-server.cmd` and `scripts\test-server.cmd`.

## Client foundation

See [client/README.md](client/README.md). The checked-in Flutter source is a UI skeleton. Platform runners must be generated with Flutter before it can compile.

## Development milestones

See [docs/MILESTONES.md](docs/MILESTONES.md) for ordered goals and acceptance criteria, and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for processing and cost rules.

## GitHub workflow

Repository: https://github.com/Warrior-spec/veilspace

The owner has authorized Git operations and pushes through CMD using their existing local Git identity. Keep commits and pushes within the event's permitted period. Do not commit documents, tokens, generated binaries, or private configuration.

## Hackathon submission details to complete

- Theme: Cybersecurity.
- Team and member names: to be supplied.
- AI model and exact input/output: to be selected and documented after evaluation.
- Deployment, APK, and demo video links: to be added before submission.
- Dependencies, datasets, and other resource credits: finalize with the implementation.

No datasets or pre-trained local models are included in this foundation.
