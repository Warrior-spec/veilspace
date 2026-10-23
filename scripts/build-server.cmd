@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --name VeilSpaceServer --paths server --collect-all uvicorn --collect-all veilspace --distpath dist --workpath build\server --specpath build server\run_portable.py
