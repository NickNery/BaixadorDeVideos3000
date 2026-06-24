@echo off
cd /d "%~dp0.."

if exist "python\src\ytdlp_gui_downloader.py" (
    where pythonw >nul 2>nul
    if not errorlevel 1 (
        start "" pythonw "python\src\ytdlp_gui_downloader.py"
        exit /b 0
    )

    start "" python "python\src\ytdlp_gui_downloader.py"
    exit /b 0
) else (
    echo Nao encontrei o arquivo python\src\ytdlp_gui_downloader.py nesta pasta.
    echo Pasta atual: %cd%
    pause
)
