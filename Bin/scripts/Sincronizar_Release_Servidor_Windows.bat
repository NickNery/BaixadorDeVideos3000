@echo off
chcp 65001 >nul
setlocal

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "[Console]::OutputEncoding = [Text.Encoding]::UTF8; (Resolve-Path -LiteralPath '%~dp0..\..').Path"`) do set "ROOT=%%I"
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

call :copydir "Bin"
if errorlevel 1 goto erro
call :copydir "setup"
if errorlevel 1 goto erro
call :copyfile "README.md"
if errorlevel 1 goto erro
call :copyfile "update_manifest.json"
if errorlevel 1 goto erro
call :clean_legacy_layout
if errorlevel 1 goto erro

echo.
echo [SUCESSO] Pasta do servidor sincronizada.
echo.
if "%BAIXADOR_SYNC_NO_PAUSE%"=="" pause
exit /b 0

:copydir
echo Sincronizando pasta %~1...
robocopy "%ROOT%\%~1" "%DESTINO%\%~1" /E /R:2 /W:2 /NFL /NDL /NJH /NJS /XD build node_modules dist-packages .venv __pycache__ /XF package-lock.json BaixadorDeVideos3000_Setup_Windows.exe.tmp >nul
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

:clean_legacy_layout
echo Limpando estrutura antiga da raiz...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$dest = (Resolve-Path -LiteralPath $env:DESTINO).Path; " ^
  "$oldDirs = @('python','electron','docs','scripts','release','assets','build','src'); " ^
  "$oldFiles = @('BaixadorDeVideos3000.vbs','BaixadorDeVideos3000.command','BaixadorDeVideos3000_Electron.exe','BaixadorDeVideos3000_Electron.command','requirements.txt'); " ^
  "foreach ($name in $oldDirs) { $path = Join-Path $dest $name; if (Test-Path -LiteralPath $path) { $resolved = (Resolve-Path -LiteralPath $path).Path; if ($resolved.StartsWith($dest, [StringComparison]::OrdinalIgnoreCase)) { Remove-Item -LiteralPath $resolved -Recurse -Force } } }; " ^
  "foreach ($name in $oldFiles) { $path = Join-Path $dest $name; if (Test-Path -LiteralPath $path) { $resolved = (Resolve-Path -LiteralPath $path).Path; if ($resolved.StartsWith($dest, [StringComparison]::OrdinalIgnoreCase)) { Remove-Item -LiteralPath $resolved -Force } } }"
if errorlevel 1 (
    echo [ERRO] Falha ao limpar a estrutura antiga.
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
