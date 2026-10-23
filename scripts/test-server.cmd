@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Create the virtual environment and install the project first. See README.md.
  exit /b 1
)
".venv\Scripts\python.exe" -m pytest %*
