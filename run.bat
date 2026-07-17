@echo off
cd /d "%~dp0"
TITLE YouTube Downloader Launcher
CLS

REM 1. VERIFICATION DU VENV (prioritaire - pas besoin de Python systeme)
IF EXIST ".venv\Scripts\python.exe" GOTO LAUNCH_APP

REM 2. RECHERCHE DE PYTHON
ECHO [Launcher] Verification de Python...

REM Essai avec py.exe (launcher Python - installe avec Python)
py --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_CMD=py
    GOTO SETUP_VENV
)

REM Essai avec python direct
python --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_CMD=python
    GOTO SETUP_VENV
)

REM 3. RECHERCHE MANUELLE DES CHEMINS COURANTS
ECHO [Launcher] Recherche de Python dans les dossiers connus...

FOR %%V IN (313 312 311 310) DO (
    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        SET "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        GOTO SETUP_VENV
    )
    IF EXIST "%ProgramFiles%\Python%%V\python.exe" (
        SET "PYTHON_CMD=%ProgramFiles%\Python%%V\python.exe"
        GOTO SETUP_VENV
    )
)

REM 4. ESSAIE AVEC PY LAUNCHER SANS VERSION PRECISE
py -3 --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_CMD=py -3
    GOTO SETUP_VENV
)

REM 5. AUCUN PYTHON TROUVE - INSTALLATION
ECHO [Launcher] Python non detecte. Installation automatique...

ECHO [Launcher] Telechargement de Python 3.12...
set "INSTALLER_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
set "INSTALLER_FILE=%TEMP%\python_installer.exe"

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%INSTALLER_URL%' -OutFile '%INSTALLER_FILE%'"
IF ERRORLEVEL 1 GOTO INSTALL_ERROR

ECHO [Launcher] Installation en cours (1-2 minutes)...
"%INSTALLER_FILE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
IF ERRORLEVEL 1 GOTO INSTALL_ERROR

del "%INSTALLER_FILE%" 2>nul

ECHO [Launcher] Installation terminee. Redetection de Python...
timeout /t 2 >nul

REM Reessai apres installation
py --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_CMD=py
    GOTO SETUP_VENV
)
python --version >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET PYTHON_CMD=python
    GOTO SETUP_VENV
)

REM Derniere chance : chercher les chemins a nouveau
FOR %%V IN (313 312 311 310) DO (
    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        SET "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        GOTO SETUP_VENV
    )
)

GOTO INSTALL_ERROR

:INSTALL_ERROR
ECHO.
ECHO ================================================================
ECHO [ERREUR] Python introuvable.
ECHO [ACTION] Installez Python 3.12+ manuellement :
ECHO          https://www.python.org/downloads/
ECHO          Puis relancez ce script.
ECHO ================================================================
PAUSE
EXIT /B 1

:SETUP_VENV
REM 3. CREATION DU VENV
ECHO [Launcher] Python detecte : %PYTHON_CMD%
ECHO [Launcher] Creation de l'environnement virtuel...

%PYTHON_CMD% -m venv .venv
IF ERRORLEVEL 1 (
    ECHO [ERREUR] Echec de la creation du venv.
    PAUSE
    EXIT /B 1
)

ECHO [Launcher] Installation des dependances...
".venv\Scripts\pip.exe" install -r requirements.txt
IF ERRORLEVEL 1 (
    ECHO [ERREUR] Echec de l'installation des dependances.
    PAUSE
    EXIT /B 1
)

:LAUNCH_APP
ECHO [Launcher] Lancement de l'application...
".venv\Scripts\python.exe" main.py
IF ERRORLEVEL 1 (
    echo.
    echo [Launcher] L'application s'est terminee avec une erreur.
)
PAUSE
