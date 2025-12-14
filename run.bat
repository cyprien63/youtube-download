@echo off
TITLE UltraYouTube Downloader Launcher
CLS

:: 1. Check if venv exists
IF EXIST ".venv\Scripts\python.exe" (
    ECHO [Launcher] Virtual Environment found.
    ".venv\Scripts\python.exe" main.py
) ELSE (
    ECHO [Launcher] No Virtual Environment found.
    ECHO [Launcher] Attempting to use global Python or create venv...
    
    :: Check if global python exists
    python --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        ECHO [ERROR] Python is not installed or not in PATH.
        PAUSE
        EXIT /B
    )

    :: Create venv automatically if missing
    ECHO [Launcher] Creating venv...
    python -m venv .venv
    
    ECHO [Launcher] Installing dependencies...
    ".venv\Scripts\pip.exe" install -r requirements.txt
    
    ECHO [Launcher] Launching App...
    ".venv\Scripts\python.exe" main.py
)

IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [Launcher] The application crashed or closed with an error.
    PAUSE
)
