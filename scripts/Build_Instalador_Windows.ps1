$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = "C:\Users\EDGE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$buildRoot = Join-Path $root "build\windows"
$payload = Join-Path $buildRoot "payload"
$setup = Join-Path $root "release\BaixadorDeVideos3000_Setup_Windows.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python de build nao encontrado: $python"
}

Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $payload | Out-Null

& $python -m pip install --upgrade pyinstaller pillow certifi
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name BaixadorDeVideos3000 `
    --distpath (Join-Path $buildRoot "dist") `
    --workpath (Join-Path $buildRoot "pyinstaller") `
    --specpath $buildRoot `
    --hidden-import certifi `
    --collect-data certifi `
    (Join-Path $root "src\ytdlp_gui_downloader.py")

Copy-Item -LiteralPath (Join-Path $buildRoot "dist\BaixadorDeVideos3000.exe") -Destination (Join-Path $payload "BaixadorDeVideos3000.exe") -Force
Copy-Item -LiteralPath (Join-Path $root "release\yt-dlp.exe") -Destination (Join-Path $payload "yt-dlp.exe") -Force
Copy-Item -LiteralPath (Join-Path $root "release\ffmpeg.exe") -Destination (Join-Path $payload "ffmpeg.exe") -Force
Copy-Item -LiteralPath (Join-Path $root "docs\Tutorial_BaixadorDeVideos3000.pdf") -Destination (Join-Path $payload "Tutorial_BaixadorDeVideos3000.pdf") -Force
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination (Join-Path $payload "README.md") -Force

@'
@echo off
chcp 65001 >nul
setlocal

if "%BAIXADOR_INSTALL_DIR%"=="" (
    set "TARGET=%LOCALAPPDATA%\BaixadorDeVideos3000"
) else (
    set "TARGET=%BAIXADOR_INSTALL_DIR%"
)

if not exist "%TARGET%" mkdir "%TARGET%"
if not exist "%TARGET%\docs" mkdir "%TARGET%\docs"

copy /Y "%~dp0BaixadorDeVideos3000.exe" "%TARGET%\BaixadorDeVideos3000.exe" >nul
copy /Y "%~dp0yt-dlp.exe" "%TARGET%\yt-dlp.exe" >nul
copy /Y "%~dp0ffmpeg.exe" "%TARGET%\ffmpeg.exe" >nul
copy /Y "%~dp0Tutorial_BaixadorDeVideos3000.pdf" "%TARGET%\docs\Tutorial_BaixadorDeVideos3000.pdf" >nul
copy /Y "%~dp0README.md" "%TARGET%\README.md" >nul

if "%BAIXADOR_SKIP_SHORTCUT%"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $shortcut=$shell.CreateShortcut((Join-Path $desktop 'Baixador de Videos 3000.lnk')); $shortcut.TargetPath='%TARGET%\BaixadorDeVideos3000.exe'; $shortcut.WorkingDirectory='%TARGET%'; $shortcut.Description='Baixador de Videos 3000'; $shortcut.Save()"
)

if "%BAIXADOR_SKIP_LAUNCH%"=="" start "" "%TARGET%\BaixadorDeVideos3000.exe"
exit /b 0
'@ | Set-Content -LiteralPath (Join-Path $payload "install_windows.bat") -Encoding ASCII

$comment = Join-Path $buildRoot "winrar_sfx_comment.txt"
@'
;The comment below contains SFX script commands

TempMode
Setup=install_windows.bat
Silent=1
Overwrite=1
Title=Baixador de Videos 3000
Text
Instalando Baixador de Videos 3000...
TextDone
Instalacao concluida.
'@ | Set-Content -LiteralPath $comment -Encoding ASCII

Remove-Item -LiteralPath $setup -Force -ErrorAction SilentlyContinue
Push-Location $payload
try {
    & "C:\Program Files\WinRAR\Rar.exe" a -r -ep1 "-sfxC:\Program Files\WinRAR\Default.SFX" "-z$comment" "$setup" *
} finally {
    Pop-Location
}

Write-Host "Instalador criado em: $setup"
