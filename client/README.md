# Client

Shared Flutter application for Windows, Android, and web. Includes authentication, manual uploads, private and shared file libraries, processing status, revision tracking, and sanitized text reading. Windows also watches a selected folder while the app stays open.

Use `scripts\flutter.cmd` from the repository root to run the project-local SDK. From this directory:

```powershell
..\scripts\flutter.cmd pub get
..\scripts\flutter.cmd analyze
..\scripts\flutter.cmd run -d windows
```

Release builds:

```powershell
..\scripts\flutter.cmd build windows
..\scripts\flutter.cmd build apk --release
..\scripts\flutter.cmd build web
```

Users have no server configuration screen. Native builds use the fixed demo endpoint `http://91.124.98.60:8787`. Web builds use their own origin unless `--dart-define=VEILSPACE_API_ORIGIN=...` is supplied. That override also supports local development. The portable server bundles a separate lightweight web UI and does not require a Flutter web build.

Windows distribution includes the executable and its supporting files. Release signing credentials stay outside the repository.
