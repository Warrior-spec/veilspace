# Client

Shared Flutter application for Windows, Android, and web. Login and registration screens are implemented. Document uploads and synchronization are next.

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

The production API address is supplied internally at build time. Users have no server configuration screen. Web builds use their own origin unless a build override is supplied. Native development defaults to localhost.

Windows distribution includes the executable and its supporting files. Release signing credentials stay outside the repository.
