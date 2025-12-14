@echo off
TITLE UltraYouTube Downloader Launcher
CLS

:: ----------------------------------------------------------------
:: 1. VERIFICATION DE PYTHON
:: ----------------------------------------------------------------

ECHO [Launcher] Verification de l'installation de Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [Launcher] Python n'est pas detecte.
    ECHO [Launcher] Tentative d'installation automatique (via Winget)...
    
    :: Vérification de Winget
    winget --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        ECHO [ERREUR] Winget est introuvable sur ce systeme.
        ECHO [ACTION] Veuillez installer Python manuellement ici : https://www.python.org/downloads/
        PAUSE
        EXIT /B
    )

    :: Installation de Python 3.12
    ECHO [Launcher] Telechargement et installation de Python 3.12...
    winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
    
    ECHO.
    ECHO [INFO] Installation terminee. Tentative de detection...
    
    :: Petit delai pour le systeme
    TIMEOUT /T 3 >nul
)


:: ----------------------------------------------------------------
:: 2. SELECTION DE L'EXECUTABLE PYTHON
:: ----------------------------------------------------------------
:: Par defaut on espere qu'il est dans le PATH
SET PYTHON_CMD=python

:: S'il n'est toujours pas dans le PATH (cas fréquent sans redémarrage), on cherche les chemins par défaut
%PYTHON_CMD% --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO [Launcher] Recherche de l'executable Python installe...
    
    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        SET PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) ELSE IF EXIST "%ProgramFiles%\Python312\python.exe" (
        SET PYTHON_CMD="%ProgramFiles%\Python312\python.exe"
    )
)

:: Derniere verification
%PYTHON_CMD% --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    CLS
    ECHO ================================================================
    ECHO [ERREUR] Python est installe mais pas encore detecte par le script.
    ECHO [ACTION] Veuillez simplement FERMER cette fenetre et relancer run.bat.
    ECHO ================================================================
    PAUSE
    EXIT /B
)

:: ----------------------------------------------------------------
:: 3. GESTION DU VENV ET LANCEMENT
:: ----------------------------------------------------------------

IF EXIST ".venv\Scripts\python.exe" (
    ECHO [Launcher] Environnement virtuel trouve.
    ECHO [Launcher] Lancement de l'application...
    ".venv\Scripts\python.exe" main.py
) ELSE (
    ECHO [Launcher] Premier lancement detecte !
    ECHO [Launcher] Creation de l'environnement virtuel (.venv)...
    %PYTHON_CMD% -m venv .venv
    
    ECHO [Launcher] Installation des dependances...
    ".venv\Scripts\pip.exe" install -r requirements.txt
    
    ECHO [Launcher] Configuration terminee. Lancement...
    ".venv\Scripts\python.exe" main.py
)

IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO [INFO] L'application s'est fermee.
    PAUSE
)
