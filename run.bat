@echo off
TITLE UltraYouTube Downloader Launcher
CLS

REM 1. VERIFICATION DE PYTHON
ECHO [Launcher] Verification de l'installation de Python...

python --version >nul 2>&1
IF ERRORLEVEL 1 GOTO INSTALL_PYTHON
GOTO DETECT_PYTHON

:INSTALL_PYTHON
ECHO [Launcher] Python n'est pas detecte.
ECHO [Launcher] Tentative d'installation automatique...

winget --version >nul 2>&1
IF ERRORLEVEL 1 GOTO WINGET_ERROR

ECHO [Launcher] Telechargement et installation de Python 3.12...
winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements

ECHO.
ECHO [INFO] Installation terminee.
TIMEOUT /T 3 >nul
GOTO DETECT_PYTHON

:WINGET_ERROR
ECHO [ERREUR] Winget est introuvable.
ECHO [ACTION] Installez Python manuellement : https://www.python.org/downloads/
PAUSE
EXIT /B

:DETECT_PYTHON
REM 2. SELECTION DE L'EXECUTABLE PYTHON
SET PYTHON_CMD=python

%PYTHON_CMD% --version >nul 2>&1
IF NOT ERRORLEVEL 1 GOTO SETUP_VENV

ECHO [Launcher] Recherche de l'executable Python installe...

IF EXIST "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    SET PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    GOTO SETUP_VENV
)
IF EXIST "%ProgramFiles%\Python312\python.exe" (
    SET PYTHON_CMD="%ProgramFiles%\Python312\python.exe"
    GOTO SETUP_VENV
)

CLS
ECHO ================================================================
ECHO [ERREUR] Python introuvable.
ECHO [ACTION] Redemarrez l'ordinateur si vous venez de l'installer.
ECHO ================================================================
PAUSE
EXIT /B

:SETUP_VENV
REM 3. GESTION DU VENV ET LANCEMENT

IF EXIST ".venv\Scripts\python.exe" GOTO LAUNCH_APP

ECHO [Launcher] Premier lancement detecte !
ECHO [Launcher] Creation de l'environnement virtuel (.venv)...
%PYTHON_CMD% -m venv .venv
IF ERRORLEVEL 1 (
    ECHO [ERREUR] Echec de la creation du venv.
    PAUSE
    EXIT /B
)

ECHO [Launcher] Installation des dependances...
".venv\Scripts\pip.exe" install -r requirements.txt

:LAUNCH_APP
ECHO [Launcher] Lancement de l'application...
".venv\Scripts\python.exe" main.py

PAUSE
