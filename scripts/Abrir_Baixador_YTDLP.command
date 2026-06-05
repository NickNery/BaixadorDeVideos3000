#!/bin/zsh
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$APP_DIR/.venv/bin/python"

export PATH="$APP_DIR:$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$APP_DIR"

if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "src/ytdlp_gui_downloader.py"
elif command -v python3 >/dev/null 2>&1; then
    python3 "src/ytdlp_gui_downloader.py"
else
    echo "Python 3 nao foi encontrado. Rode o Instalador_Automatico_macOS.command."
    read "?Pressione Enter para fechar..."
fi
