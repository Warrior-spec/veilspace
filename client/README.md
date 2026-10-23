# Shared Flutter client

One source tree targets Windows, Android, and web. No server configuration screen is planned. The fixed production endpoint will be supplied internally when release builds are configured.

This milestone contains UI source only. It has no login, network access, upload, or folder watcher yet.

After installing Flutter and its platform build prerequisites, run from this directory:

```powershell
flutter create --platforms=windows,android,web --project-name veilspace .
flutter pub get
flutter analyze
flutter run -d windows
```

Generate platform runners before adding platform-specific integrations. Verify that the existing `lib/main.dart` is retained when generating runners.

Later release outputs:

```powershell
flutter build windows
flutter build apk --release
flutter build web
```

Windows distribution includes the executable and its supporting build files, not just a standalone `.exe`. Android release signing will be configured outside version control.
