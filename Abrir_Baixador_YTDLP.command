#!/bin/zsh
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    python3 "ytdlp_gui_downloader.py"
else
    echo "Python 3 nao foi encontrado. Instale pelo site python.org ou pelo Homebrew."
    read "?Pressione Enter para fechar..."
fi
