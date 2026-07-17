@echo off
chcp 65001 >nul 2>&1
title YouTube Downloader - Compilation
cd /d "%~dp0"

:MENU
cls
echo ================================================================
echo        YouTube Downloader - Systeme de Compilation
echo ================================================================
echo.
echo   [1] Compiler en EXE (Windows, multi-fichiers, sans terminal)
echo   [2] Compiler en AppImage (Linux)
echo   [3] Quitter
echo.
echo ================================================================
set /p choice="Choix : "

if "%choice%"=="1" goto EXE
if "%choice%"=="2" goto APPIMAGE
if "%choice%"=="3" goto END
echo Choix invalide.
timeout /t 2 >nul
goto MENU

:EXE
call scripts\build_exe.bat
goto MENU

:APPIMAGE
echo ================================================================
echo   AppImage doit etre compile sur une machine Linux.
echo   Utilisez : bash scripts/build_appimage.sh
echo ================================================================
pause
goto MENU

:END
exit /b 0
