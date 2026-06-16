@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0.." || (
    echo Nao consegui acessar a pasta do Baixador.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\scripts\Abrir_Baixador_Electron.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
