@echo off
chcp 65001 >nul 2>&1
title Compilation EXE - YouTube Downloader
cd /d "%~dp0.."

echo ================================================================
echo   Compilation en EXE (Windows)
echo ================================================================
echo.

set "PY=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\pip.exe"

if not exist "%PY%" (
    echo [ERREUR] Venv non trouve. Lancez run.bat une fois d'abord.
    pause
    exit /b 1
)

"%PY%" -c "import PyInstaller" >nul 2>&1
if ERRORLEVEL 1 (
    echo [!] PyInstaller non installe. Installation...
    "%PIP%" install pyinstaller
    if ERRORLEVEL 1 (
        echo [ERREUR] Impossible d'installer PyInstaller.
        pause
        exit /b 1
    )
)

echo [1/3] Nettoyage...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [2/3] Compilation en cours...
"%PY%" -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "YouTube-Downloader" ^
    --icon "scripts\icon.ico" ^
    --add-data "src;src" ^
    --add-data "version.py;." ^
    --collect-data customtkinter ^
    --collect-data customtkinter.windows ^
    --collect-data customtkinter.windows.widgets ^
    --collect-data customtkinter.windows.theme ^
    --collect-data customtkinter.color ^
    --hidden-import customtkinter ^
    --hidden-import customtkinter.windows ^
    --hidden-import customtkinter.windows.widgets ^
    --hidden-import customtkinter.windows.widgets.ctk_label ^
    --hidden-import customtkinter.windows.widgets.ctk_button ^
    --hidden-import customtkinter.windows.widgets.ctk_entry ^
    --hidden-import customtkinter.windows.widgets.ctk_textbox ^
    --hidden-import customtkinter.windows.widgets.ctk_progressbar ^
    --hidden-import customtkinter.windows.widgets.ctk_optionmenu ^
    --hidden-import customtkinter.windows.widgets.ctk_combobox ^
    --hidden-import customtkinter.windows.widgets.ctk_segmentedbutton ^
    --hidden-import customtkinter.windows.widgets.ctk_frame ^
    --hidden-import customtkinter.windows.theme.theme ^
    --hidden-import customtkinter.color ^
    --hidden-import yt_dlp ^
    --hidden-import pytubefix ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import PIL.ImageFilter ^
    --exclude-module Cryptodome ^
    --exclude-module OpenSSL ^
    --exclude-module curl_cffi ^
    --exclude-module secretstorage ^
    main.py

if ERRORLEVEL 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    pause
    exit /b 1
)

echo.
echo [3/3] Copie de version.txt...
echo YouTube Downloader > "dist\YouTube-Downloader\VERSION.txt"
type version.py >> "dist\YouTube-Downloader\VERSION.txt"

echo.
echo ================================================================
echo   COMPILATION TERMINEE
echo   Dossier : dist\YouTube-Downloader\
echo   EXE     : dist\YouTube-Downloader\YouTube-Downloader.exe
echo ================================================================
echo.
pause
