@echo off
cd /d "%~dp0.."

if exist "src\ytdlp_gui_downloader.py" (
    pythonw "src\ytdlp_gui_downloader.py"
    if errorlevel 1 python "src\ytdlp_gui_downloader.py"
) else (
    echo Nao encontrei o arquivo src\ytdlp_gui_downloader.py nesta pasta.
    echo Pasta atual: %cd%
    pause
)
