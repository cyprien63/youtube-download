@echo off
chcp 65001 >nul 2>&1
title Compilation EXE - YouTube Downloader
cd /d "%~dp0.."

echo ================================================================
echo   Compilation en EXE (Windows)
echo ================================================================
echo.

REM Verification de PyInstaller
python -c "import PyInstaller" >nul 2>&1
if ERRORLEVEL 1 (
    echo [!] PyInstaller non installe. Installation en cours...
    pip install pyinstaller
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
python -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "YouTube-Downloader" ^
    --icon "NONE" ^
    --add-data "src;src" ^
    --add-data "version.py;." ^
    --hidden-import customtkinter ^
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
    --hidden-import customtkinter.windows.theme ^
    --hidden-import customtkinter.color_theme ^
    --hidden-import yt_dlp ^
    --hidden-import pytubefix ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import PIL.ImageFilter ^
    --collect-data customtkinter ^
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
