@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  start "" ".venv\Scripts\python.exe" "desktop_companion.py"
) else (
  start "" python "desktop_companion.py"
)
