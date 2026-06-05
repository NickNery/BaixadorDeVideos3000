#!/bin/zsh
set -e

cd "$(dirname "$0")/.."

APP_DIR="$(pwd)"
LAUNCHER="$APP_DIR/scripts/Abrir_Baixador_YTDLP.command"
DESKTOP_LAUNCHER="$HOME/Desktop/Baixador de Videos 3000.command"

echo "=================================================="
echo "  INSTALADOR AUTOMATICO - BAIXADOR DE VIDEOS 3000"
echo "=================================================="
echo

ensure_homebrew() {
    if command -v brew >/dev/null 2>&1; then
        return
    fi

    echo "Homebrew nao foi encontrado."
    echo "Ele sera instalado para baixar Python e ffmpeg automaticamente."
    echo
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    if [ -x "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -x "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
}

if ! command -v python3 >/dev/null 2>&1; then
    ensure_homebrew
    echo "Instalando Python..."
    brew install python
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    ensure_homebrew
    echo "Instalando ffmpeg..."
    brew install ffmpeg
fi

echo "Instalando dependencias do aplicativo..."
python3 -m pip install --upgrade -r requirements.txt

chmod +x "$LAUNCHER"
chmod +x "$APP_DIR/scripts/Instalar_Dependencias_macOS.command"

cat > "$DESKTOP_LAUNCHER" <<EOF
#!/bin/zsh
cd "$APP_DIR"
python3 "src/ytdlp_gui_downloader.py"
EOF
chmod +x "$DESKTOP_LAUNCHER"

echo
echo "Instalacao concluida."
echo "Um atalho foi criado na Area de Trabalho:"
echo "$DESKTOP_LAUNCHER"
echo
echo "Abrindo o aplicativo..."
open "$DESKTOP_LAUNCHER"
