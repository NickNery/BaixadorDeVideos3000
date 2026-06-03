@echo off
cd /d "%~dp0"

if exist "ytdlp_gui_downloader.py" (
    pythonw "ytdlp_gui_downloader.py"
    if errorlevel 1 python "ytdlp_gui_downloader.py"
) else (
    echo Nao encontrei o arquivo ytdlp_gui_downloader.py nesta pasta.
    echo Pasta atual: %cd%
    pause
)
