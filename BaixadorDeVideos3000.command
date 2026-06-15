#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -x "$SCRIPT_DIR/scripts/Abrir_Baixador_YTDLP.command" ]; then
    exec "$SCRIPT_DIR/scripts/Abrir_Baixador_YTDLP.command"
fi

cd "$SCRIPT_DIR"

if [ -f "src/ytdlp_gui_downloader.py" ]; then
    if [ -x ".venv/bin/python" ]; then
        exec ".venv/bin/python" "src/ytdlp_gui_downloader.py"
    fi
    exec python3 "src/ytdlp_gui_downloader.py"
fi

echo "Nao encontrei src/ytdlp_gui_downloader.py nesta pasta."
read "?Pressione Enter para fechar..."
