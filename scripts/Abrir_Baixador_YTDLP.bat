@echo off
cd /d "%~dp0.."

if exist "src\ytdlp_gui_downloader.py" (
    where pythonw >nul 2>nul
    if not errorlevel 1 (
        start "" pythonw "src\ytdlp_gui_downloader.py"
        exit /b 0
    )

    start "" python "src\ytdlp_gui_downloader.py"
    exit /b 0
) else (
    echo Nao encontrei o arquivo src\ytdlp_gui_downloader.py nesta pasta.
    echo Pasta atual: %cd%
    pause
)
