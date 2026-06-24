#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -x "$APP_DIR/launcher/Abrir_Baixador_Electron.command" ]; then
    exec "$APP_DIR/launcher/Abrir_Baixador_Electron.command"
fi

echo "Nao encontrei launcher/Abrir_Baixador_Electron.command nesta pasta."
read "?Pressione Enter para fechar..."
