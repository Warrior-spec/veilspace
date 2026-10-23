@echo off
setlocal
cd /d "%~dp0..\client"
call "..\scripts\flutter.cmd" build apk --release --target-platform android-arm64
if errorlevel 1 exit /b 1
echo APK: client\build\app\outputs\flutter-apk\app-release.apk
