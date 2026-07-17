@echo off
chcp 65001 >nul 2>&1
title Compilation EXE - YouTube Downloader
cd /d "%~dp0.."

echo ================================================================
echo   Compilation en EXE (Windows)
echo ================================================================
echo.

REM Utiliser le Python du venv
set "PY=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\pip.exe"

if not exist "%PY%" (
    echo [ERREUR] Venv non trouve. Lancez run.bat une fois d'abord.
    pause
    exit /b 1
)

REM Verification de PyInstaller dans le venv
"%PY%" -c "import PyInstaller" >nul 2>&1
if ERRORLEVEL 1 (
    echo [!] PyInstaller non installe dans le venv. Installation...
    "%PIP%" install pyinstaller
    if ERRORLEVEL 1 (
        echo [ERREUR] Impossible d'installer PyInstaller.
        pause
        exit /b 1
    )
)

echo [1/3] Nettoyage des fichiers precedents...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [2/3] Compilation en cours...
"%PY%" -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "YouTube-Downloader" ^
    --icon "scripts\icon.ico" ^
    --add-data "src;src" ^
    --add-data "version.py;." ^
    --collect-all customtkinter ^
    --hidden-import yt_dlp ^
    --hidden-import pytubefix ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import PIL.ImageFilter ^
    main.py

if ERRORLEVEL 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    pause
    exit /b 1
)

echo.
echo [3/3] Copie de version.txt dans dist...
echo YouTube Downloader > "dist\YouTube-Downloader\VERSION.txt"
type version.py >> "dist\YouTube-Downloader\VERSION.txt"

echo.
echo ================================================================
echo   COMPILATION TERMINEE
echo   Dossier de sortie : dist\YouTube-Downloader\
echo   Executable        : dist\YouTube-Downloader\YouTube-Downloader.exe
echo ================================================================
echo.
pause
