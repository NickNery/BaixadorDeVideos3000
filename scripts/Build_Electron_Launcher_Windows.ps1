$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = "C:\Users\EDGE\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$buildRoot = Join-Path $root "build\electron-launcher"
$launcher = Join-Path $root "scripts\electron_launcher.py"
$icon = Join-Path $root "assets\favicon.ico"
$distExe = Join-Path $buildRoot "dist\BaixadorDeVideos3000_Electron.exe"
$rootExe = Join-Path $root "BaixadorDeVideos3000_Electron.exe"
$releaseExe = Join-Path $root "release\BaixadorDeVideos3000_Electron.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python de build nao encontrado: $python"
}
if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Launcher Electron nao encontrado: $launcher"
}

Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $buildRoot | Out-Null

& $python -m pip install --upgrade pyinstaller
& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name BaixadorDeVideos3000_Electron `
    --icon $icon `
    --distpath (Join-Path $buildRoot "dist") `
    --workpath (Join-Path $buildRoot "pyinstaller") `
    --specpath $buildRoot `
    $launcher

Copy-Item -LiteralPath $distExe -Destination $rootExe -Force
Copy-Item -LiteralPath $distExe -Destination $releaseExe -Force

Write-Host "Launcher Electron criado em:"
Write-Host $rootExe
Write-Host $releaseExe
