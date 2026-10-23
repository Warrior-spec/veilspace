@echo off
setlocal
cd /d "%~dp0..\client"
call "..\scripts\flutter.cmd" build windows --release
if errorlevel 1 exit /b 1
echo Distribution: client\build\windows\x64\runner\Release
echo Keep the executable, DLL files, and data directory together.
