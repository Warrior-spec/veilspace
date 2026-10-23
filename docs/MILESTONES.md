# VeilSpace milestones

## 1. Foundation: complete

Public repository, Python service, Flutter platform projects, and initial health checks are ready. Work is pushed in separate checkpoints.

## 2. Portable server and toolchain: complete

The server executable initializes SQLite and private storage, serves the website, and prints connection URLs. Flutter is restored and the Windows client compiles. Android platform 36, build tools 36.0.0, and the checksum-verified NDK 27.0.12077973 are installed.

## 3. Authentication: implemented and verified

Signup, login, salted password hashes, opaque expiring sessions, and logout are implemented. Automated checks cover invalid credentials, session revocation, expiry, and two-account isolation. Client authentication tests pass. Public server authentication is verified.

## 4. Document intake: implemented and verified

Bounded DOCX, readable PDF, and UTF-8 TXT uploads enter a durable private processing queue. Original files have no download route. My Files, Shared Files, and Pending views are implemented. Tests verify invalid uploads, inaccessible originals, and owner-only modifications.

## 5. Redaction and cost limits: implemented and verified

Structured AI findings and rules produce regenerated sanitized PDFs. Exact normalized names reuse workspace aliases. Uncertain or unreadable files stay pending. A content cache, bounded input/output, one worker, a 100-request daily cap, and a default $1 conservative reservation allowance limit usage.

A live fictional document published with four redactions. A second account read only the sanitized result. An identical cross-account upload reused the cached assessment without another AI request. Automated checks also cover budget exhaustion and previous published revisions.

## 6. Windows folder uploads: implemented and checked

One folder is remembered per account. Files must be stable before upload. Unchanged files are skipped and failed uploads stop after three attempts until the file changes or the folder is selected again. A filesystem check verified automatic upload callbacks, edited revisions, stable source IDs, and unchanged-file skipping. Full user-interface testing remains part of final acceptance.

## 7. Packaging and submission: in progress

- [x] Compile and launch the Windows client.
- [x] Package and smoke-test the portable server.
- [x] Deploy and verify the public website and backend.
- [x] Verify public two-account redaction, reading, sharing, deduplication, and cache use.
- [x] Verify 27 backend tests, four client tests, and clean Flutter analysis.
- [x] Add registered team details, AI explanation, stack, local setup, deployment link, and resource credits to the README.
- [x] Finish NDK installation.
- [ ] Compile the Flutter APK.
- [ ] Install and test only VeilSpace on the paired Android phone.
- [ ] Complete a final Windows folder-upload demonstration against the public server.
- [ ] Publish the APK with an accessible link.
- [ ] Record a narrated 3 to 5 minute demo at 720p or higher.
- [ ] Add the public demo video link to the README and form.
- [ ] Test every submission link from a separate browser session or device.
- [ ] Have the team lead submit the organiser's Google Form once and save confirmation.

The guidelines accept a live web application as the deployment deliverable. If the APK is included, it must also be installed and tested on a real phone. Keep the backend live until results are announced on 24 October. Final code pushes must precede the organiser's deadline.
