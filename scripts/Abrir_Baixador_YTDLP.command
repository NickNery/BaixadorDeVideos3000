#!/bin/zsh
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$APP_DIR/.venv/bin/python"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"

export PATH="$APP_DIR:$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$APP_DIR"

if [ -f "$RUNTIME_HELPERS" ]; then
    source "$RUNTIME_HELPERS"
    if ! python_is_usable_for_app "$VENV_PYTHON"; then
        echo "Preparando o Python correto para abrir a interface..."
        "$APP_DIR/scripts/Instalar_Dependencias_macOS.command"
    fi
fi

if [ ! -x "$VENV_PYTHON" ]; then
    echo "Python do aplicativo nao foi encontrado. Rode o Instalador_Automatico_macOS.command."
    read "?Pressione Enter para fechar..."
    exit 1
fi

"$VENV_PYTHON" "python/src/ytdlp_gui_downloader.py"
