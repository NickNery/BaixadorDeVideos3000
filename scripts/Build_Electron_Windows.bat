@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0..\electron"

where npm >nul 2>nul
if errorlevel 1 (
    echo Nao encontrei o npm.
    echo Instale o Node.js LTS em https://nodejs.org/ e tente novamente.
    pause
    exit /b 1
)

npm install
if errorlevel 1 exit /b 1

npm run package:win
if errorlevel 1 exit /b 1

echo.
echo Build Electron Windows concluido.
pause
