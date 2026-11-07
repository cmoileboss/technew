@echo off
cd /d "%~dp0backend"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [WARN] backend\.venv introuvable, utilisation du Python du PATH.
)

python -m uvicorn app.main:app --port 8000 %*
