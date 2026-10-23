@echo off
setlocal
if not exist "%~dp0..\.tools\flutter\bin\flutter.bat" (
  echo Flutter SDK is missing from .tools\flutter.
  exit /b 1
)
call "%~dp0..\.tools\flutter\bin\flutter.bat" %*
