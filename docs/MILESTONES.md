# VeilSpace goals

Complete and verify one goal before moving to the next. The owner has authorized Git operations and pushes through CMD using their existing identity.

## 1. Project foundation — complete

- [x] Establish product scope and repository structure.
- [x] Add runnable FastAPI service and meaningful health/configuration checks.
- [x] Add shared Flutter UI source.
- [x] Verify backend installation, tests, and a live health request.
- [x] Record platform build availability and GitHub setup.

Acceptance: backend runs; source is organized; missing prerequisites and next steps are explicit. Compiled clients are not required for this foundation goal.

## 2. MySQL and authentication

- Finish Flutter SDK setup, generate platform runners, and verify platform build prerequisites.
- Create migrations for users, workspace memberships, documents, and revisions.
- Add password hashing, signup, login, expiring sessions, and logout.
- Enforce membership and ownership on every relevant endpoint.
- Connect Flutter login and verify with two different accounts.

Acceptance: two users can sign in; unauthorized requests and cross-owner modifications fail.

## 3. Document intake and private processing queue

- Add bounded manual uploads for DOCX, TXT, and text-based PDF.
- Keep originals in private staging; reject or hold unsupported/unreadable files.
- Extract text and create durable jobs with idempotency keys.
- Add My Files, Shared Files, and Pending API/client views.

Acceptance: originals cannot be retrieved by other members, and pending files never appear as published.

## 4. Detection, redaction, aliases, and cost limits

- Add rules and bounded AI assessment with protected server credentials.
- Introduce workspace-scoped consistent aliases without guessing ambiguous identity merges.
- Generate sanitized PDFs with underlying sensitive content removed.
- Review uncertain findings and verify output before publication.
- Add content/policy caching, request limits, usage reservations, and an application-enforced budget.

Acceptance: representative fictional documents redact correctly; repeat processing is cached; budget exhaustion holds publication.

## 5. Windows folder watching and revisions

- Select and remember one local folder.
- Debounce changes and wait for stable files before uploading.
- Skip unchanged content; retry bounded transient failures without duplicate revisions.
- Publish successful new versions while preserving the previous published revision during processing.

Acceptance: new file, edited file, rename, repeat save, and interrupted upload behave predictably.

## 6. Package, deploy, and submit

- Compile Windows distribution, Android APK, and web build.
- Configure one fixed HTTPS endpoint internally; no user server setup screen.
- Deploy Python worker/API and MySQL on the server with private disk storage.
- Test PC automatic upload, phone manual upload, and second-account web access.
- Finish team details, credits, README, demo video, and submission links.
- Perform the authorized final push before the event deadline.

Acceptance: tested installable apps, public working web deployment, and complete submission materials.
