# VeilSpace demo

Document sharing with server-side redaction, consistent name aliases, revision tracking, and private pending files.

## Downloads

- **VeilSpace-Android.apk:** Flutter release build for ARM64 phones running Android 7.0 or later. Signed with the development key for hackathon sideloading.
- **VeilSpace-Windows.zip:** Windows app with its executable, runtime DLLs, and assets. Extract the entire ZIP and run `veilspace.exe`. Keep the supporting files together.
- **VeilSpaceServer.exe:** Portable Windows backend and website. Place a private `.env` with `OPENAI_API_KEY=...` beside it, run the executable, and approve its firewall prompt. The server creates its own SQLite database and private data directory.
- **SHA256SUMS.txt:** Checksums for the three downloads.

## Demo access

Website: http://91.124.98.60:8787

Email: `demo@demo.com`

Password: `demo12345678`

Use fictional documents. The native clients use the fixed demo server address. Keep that backend running for uploads, processing, and reading.

## Current limits

DOCX, readable PDF, and UTF-8 TXT inputs produce regenerated text PDFs. Original layout is not preserved. Unreadable or uncertain files remain private. The demo uses HTTP and does not guarantee complete detection of sensitive information.
