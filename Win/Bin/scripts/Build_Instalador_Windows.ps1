$ErrorActionPreference = "Stop"

$binRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$repoRoot = Resolve-Path (Join-Path $binRoot "..")
$python = "C:\Users\EDGE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$buildRoot = Join-Path $repoRoot "build\windows"
$payload = Join-Path $buildRoot "payload"
$payloadBin = Join-Path $payload "Bin"
$setup = Join-Path $binRoot "release\BaixadorDeVideos3000_Setup_Windows.exe"
$setupGuiSource = Join-Path $repoRoot "setup\setup_installer.py"
$setupGuiExe = Join-Path $repoRoot "setup\Setup_BaixadorDeVideos3000_Windows.exe"
$setupGuiBuild = Join-Path $buildRoot "setup-gui"
$icon = Join-Path $binRoot "assets\favicon.ico"
$electronLauncherBuild = Join-Path $binRoot "scripts\Build_Electron_Launcher_Windows.ps1"
$electronLauncher = Join-Path $binRoot "launcher\BaixadorDeVideos3000_Electron.exe"
$pythonReleaseExe = Join-Path $binRoot "release\BaixadorDeVideos3000.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python de build nao encontrado: $python"
}

if (-not (Test-Path -LiteralPath $icon)) {
    throw "Icone nao encontrado: $icon"
}

if (Test-Path -LiteralPath $electronLauncherBuild) {
    powershell -NoProfile -ExecutionPolicy Bypass -File $electronLauncherBuild
}

Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $payload, $payloadBin, (Join-Path $binRoot "release") | Out-Null

& $python -m pip install --upgrade pyinstaller pillow certifi
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name BaixadorDeVideos3000 `
    --icon $icon `
    --distpath (Join-Path $buildRoot "dist") `
    --workpath (Join-Path $buildRoot "pyinstaller") `
    --specpath $buildRoot `
    --hidden-import certifi `
    --collect-data certifi `
    (Join-Path $binRoot "python\src\ytdlp_gui_downloader.py")

Copy-Item -LiteralPath (Join-Path $buildRoot "dist\BaixadorDeVideos3000.exe") -Destination $pythonReleaseExe -Force

if (Test-Path -LiteralPath $setupGuiSource) {
    New-Item -ItemType Directory -Force -Path $setupGuiBuild | Out-Null
    & $python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onefile `
        --name Setup_BaixadorDeVideos3000_Windows `
        --icon $icon `
        --distpath (Join-Path $setupGuiBuild "dist") `
        --workpath (Join-Path $setupGuiBuild "pyinstaller") `
        --specpath $setupGuiBuild `
        $setupGuiSource

    Copy-Item -LiteralPath (Join-Path $setupGuiBuild "dist\Setup_BaixadorDeVideos3000_Windows.exe") -Destination $setupGuiExe -Force
}

robocopy $binRoot $payloadBin /E /R:2 /W:2 /NFL /NDL /NJH /NJS `
    /XD build node_modules dist-packages .venv __pycache__ `
    /XF package-lock.json BaixadorDeVideos3000_Setup_Windows.exe Baixador_YTDLP_Windows_macOS.zip BaixadorDeVideos3000_Instalador_macOS.zip BaixadorDeVideos3000_macOS.dmg | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "Falha ao copiar a pasta Bin para o instalador."
}

Copy-Item -LiteralPath (Join-Path $repoRoot "README.md") -Destination (Join-Path $payload "README.md") -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "update_manifest.json") -Destination (Join-Path $payload "update_manifest.json") -Force

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

if exist "%~dp0Bin" robocopy "%~dp0Bin" "%TARGET%\Bin" /E /R:2 /W:2 /NFL /NDL /NJH /NJS /XD node_modules dist-packages .venv __pycache__ >nul
if exist "%~dp0README.md" copy /Y "%~dp0README.md" "%TARGET%\README.md" >nul
if exist "%~dp0update_manifest.json" copy /Y "%~dp0update_manifest.json" "%TARGET%\update_manifest.json" >nul

if "%BAIXADOR_SKIP_SHORTCUT%"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $shortcut=$shell.CreateShortcut((Join-Path $desktop 'Baixador de Videos 3000.lnk')); $shortcut.TargetPath='%TARGET%\Bin\launcher\BaixadorDeVideos3000.vbs'; $shortcut.WorkingDirectory='%TARGET%\Bin'; $shortcut.IconLocation='%TARGET%\Bin\assets\favicon.ico'; $shortcut.Description='Baixador de Videos 3000'; $shortcut.Save()"
    if exist "%TARGET%\Bin\launcher\BaixadorDeVideos3000_Electron.exe" powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $shortcut=$shell.CreateShortcut((Join-Path $desktop 'Baixador de Videos 3000 Electron.lnk')); $shortcut.TargetPath='%TARGET%\Bin\launcher\BaixadorDeVideos3000_Electron.exe'; $shortcut.WorkingDirectory='%TARGET%\Bin'; $shortcut.IconLocation='%TARGET%\Bin\assets\favicon.ico'; $shortcut.Description='Baixador de Videos 3000 Electron'; $shortcut.Save()"
)

if "%BAIXADOR_SKIP_LAUNCH%"=="" start "" "%TARGET%\Bin\launcher\BaixadorDeVideos3000.vbs"
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

powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $binRoot "scripts\Preparar_Distribuicao_Plataformas.ps1")
