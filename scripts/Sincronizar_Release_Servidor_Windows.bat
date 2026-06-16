@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0.."
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "[Console]::OutputEncoding = [Text.Encoding]::UTF8; 'Z:\AUDIO VISUAL\ELEMENTOS DE EDI' + [char]0x00C7 + [char]0x00C3 + 'O\BaixadorDeVideos3000'"`) do set "DESTINO=%%I"

echo ==================================================
echo   SINCRONIZAR BAIXADOR DE VIDEOS 3000
echo ==================================================
echo.
echo Origem:  "%ROOT%"
echo Destino: "%DESTINO%"
echo.

if not exist "%DESTINO%" (
    echo Criando pasta de destino...
    mkdir "%DESTINO%"
    if errorlevel 1 (
        echo.
        echo [ERRO] Nao consegui criar a pasta de destino.
        echo Verifique se a unidade Z: esta conectada.
        pause
        exit /b 1
    )
)

call :copydir "python"
if errorlevel 1 goto erro
call :copydir "electron"
if errorlevel 1 goto erro
call :copydir "docs"
if errorlevel 1 goto erro
call :copydir "scripts"
if errorlevel 1 goto erro
call :copydir "release"
if errorlevel 1 goto erro
call :copydir "assets"
if errorlevel 1 goto erro

call :copyfile "BaixadorDeVideos3000.vbs"
if errorlevel 1 goto erro
call :copyfile "BaixadorDeVideos3000.command"
if errorlevel 1 goto erro
call :copyfile "BaixadorDeVideos3000_Electron.exe"
if errorlevel 1 goto erro
call :copyfile "BaixadorDeVideos3000_Electron.command"
if errorlevel 1 goto erro
call :copyfile "README.md"
if errorlevel 1 goto erro
call :copyfile "update_manifest.json"
if errorlevel 1 goto erro

echo.
echo [SUCESSO] Pasta do servidor sincronizada.
echo.
if "%BAIXADOR_SYNC_NO_PAUSE%"=="" pause
exit /b 0

:copydir
echo Sincronizando pasta %~1...
robocopy "%ROOT%\%~1" "%DESTINO%\%~1" /E /R:2 /W:2 /NFL /NDL /NJH /NJS /XD node_modules dist dist-packages .venv __pycache__ >nul
if %ERRORLEVEL% GEQ 8 (
    echo [ERRO] Falha ao sincronizar a pasta %~1.
    exit /b 1
)
exit /b 0

:copyfile
echo Copiando arquivo %~1...
copy /Y "%ROOT%\%~1" "%DESTINO%\%~1" >nul
if errorlevel 1 (
    echo [ERRO] Falha ao copiar o arquivo %~1.
    exit /b 1
)
exit /b 0

:erro
echo.
echo [ERRO] Sincronizacao interrompida.
echo Verifique a conexao com a unidade Z: e tente novamente.
echo.
if "%BAIXADOR_SYNC_NO_PAUSE%"=="" pause
exit /b 1
