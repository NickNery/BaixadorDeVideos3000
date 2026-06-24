#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR/electron"

if ! command -v npm >/dev/null 2>&1; then
    echo "Nao encontrei o npm."
    echo "Instale o Node.js LTS em https://nodejs.org/ e tente novamente."
    read "?Pressione Enter para fechar..."
    exit 1
fi

npm install
npm run package:mac

echo
echo "Build Electron macOS concluido."
read "?Pressione Enter para fechar..."
