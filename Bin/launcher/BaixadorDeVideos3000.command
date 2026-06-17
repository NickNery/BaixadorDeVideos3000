#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -x "$APP_DIR/launcher/Abrir_Baixador_YTDLP.command" ]; then
    exec "$APP_DIR/launcher/Abrir_Baixador_YTDLP.command"
fi

cd "$APP_DIR"

if [ -f "python/src/ytdlp_gui_downloader.py" ]; then
    if [ -x ".venv/bin/python" ]; then
        exec ".venv/bin/python" "python/src/ytdlp_gui_downloader.py"
    fi
    exec python3 "python/src/ytdlp_gui_downloader.py"
fi

echo "Nao encontrei python/src/ytdlp_gui_downloader.py nesta pasta."
read "?Pressione Enter para fechar..."
