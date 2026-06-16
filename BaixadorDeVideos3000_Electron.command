#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -x "$SCRIPT_DIR/scripts/Abrir_Baixador_Electron.command" ]; then
    exec "$SCRIPT_DIR/scripts/Abrir_Baixador_Electron.command"
fi

echo "Nao encontrei scripts/Abrir_Baixador_Electron.command nesta pasta."
read "?Pressione Enter para fechar..."
