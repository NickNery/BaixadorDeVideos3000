@echo off
chcp 65001 >nul
setlocal

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "[Console]::OutputEncoding = [Text.Encoding]::UTF8; (Resolve-Path -LiteralPath '%~dp0..').Path"`) do set "ROOT=%%I"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "[Console]::OutputEncoding = [Text.Encoding]::UTF8; 'Z:\AUDIO VISUAL\ELEMENTOS DE EDI' + [char]0x00C7 + [char]0x00C3 + 'O\BaixadorDeVideos3000'"`) do set "DESTINO=%%I"

echo ==================================================
echo   SINCRONIZAR BAIXADOR DE VIDEOS 3000
echo ==================================================
echo.
echo Origem:  "%ROOT%"
echo Destino: "%DESTINO%"
echo.

if /I "%ROOT%"=="%DESTINO%" (
    echo [INFO] A origem e o destino sao a mesma pasta.
    echo [INFO] Nada precisa ser sincronizado neste local.
    echo.
    if "%BAIXADOR_SYNC_NO_PAUSE%"=="" pause
    exit /b 0
)

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
call :copyfile_optional "release\BaixadorDeVideos3000_Electron.exe"
call :copydir "assets"
if errorlevel 1 goto erro

call :copyfile "BaixadorDeVideos3000.vbs"
if errorlevel 1 goto erro
call :copyfile "BaixadorDeVideos3000.command"
if errorlevel 1 goto erro
call :copyfile_optional "BaixadorDeVideos3000_Electron.exe"
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
set "EXCLUDE_FILES="
if /I "%~1"=="release" set "EXCLUDE_FILES=/XF BaixadorDeVideos3000_Electron.exe"
robocopy "%ROOT%\%~1" "%DESTINO%\%~1" /E /R:2 /W:2 /NFL /NDL /NJH /NJS /XD node_modules dist-packages .venv __pycache__ %EXCLUDE_FILES% >nul
if %ERRORLEVEL% GEQ 8 (
    echo [ERRO] Falha ao sincronizar a pasta %~1.
    exit /b 1
)
exit /b 0

:copyfile
echo Copiando arquivo %~1...
if /I "%ROOT%\%~1"=="%DESTINO%\%~1" (
    echo [INFO] Arquivo %~1 ja esta no destino. Pulando.
    exit /b 0
)
copy /Y "%ROOT%\%~1" "%DESTINO%\%~1" >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Falha ao copiar o arquivo %~1.
    exit /b 1
)
exit /b 0

:copyfile_optional
echo Copiando arquivo %~1...
if /I "%ROOT%\%~1"=="%DESTINO%\%~1" (
    echo [INFO] Arquivo %~1 ja esta no destino. Pulando.
    exit /b 0
)
copy /Y "%ROOT%\%~1" "%DESTINO%\%~1" >nul 2>nul
if errorlevel 1 (
    echo [AVISO] Nao consegui copiar %~1 porque ele provavelmente esta aberto em outro computador.
    echo [AVISO] Feche o Baixador Electron e rode a sincronizacao novamente para atualizar esse arquivo.
    exit /b 0
)
exit /b 0

:erro
echo.
echo [ERRO] Sincronizacao interrompida.
echo Verifique a conexao com a unidade Z: e tente novamente.
echo.
if "%BAIXADOR_SYNC_NO_PAUSE%"=="" pause
exit /b 1
