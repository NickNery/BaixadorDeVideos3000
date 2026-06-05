#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    APP_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../requirements.txt" ]; then
    APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    echo "Nao encontrei a pasta do Baixador de Videos 3000."
    echo "Extraia o ZIP inteiro e rode este instalador dentro da pasta extraida."
    read "?Pressione Enter para fechar..."
    exit 1
fi

cd "$APP_DIR"

VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
DESKTOP_DIR="$HOME/Desktop"
DESKTOP_APP="$DESKTOP_DIR/Baixador de Videos 3000.app"
ICON_FILE="$APP_DIR/assets/favicon.ico"

echo "=================================================="
echo "  INSTALADOR AUTOMATICO - BAIXADOR DE VIDEOS 3000"
echo "=================================================="
echo

load_brew_shellenv() {
    if [ -x "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -x "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
}

ensure_homebrew() {
    load_brew_shellenv

    if command -v brew >/dev/null 2>&1; then
        return
    fi

    echo "Homebrew nao foi encontrado."
    echo "Ele sera instalado para baixar Python e ffmpeg automaticamente."
    echo
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    load_brew_shellenv
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

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Criando ambiente Python do aplicativo..."
    python3 -m venv "$VENV_DIR"
fi

echo "Instalando dependencias do aplicativo..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install --upgrade -r requirements.txt

chmod +x "$APP_DIR/scripts/"*.command 2>/dev/null || true
chmod +x "$APP_DIR/release/"*.command 2>/dev/null || true

create_app_icon() {
    if [ ! -f "$ICON_FILE" ]; then
        return
    fi

    ICONSET_DIR="$APP_DIR/build/AppIcon.iconset"
    ICNS_FILE="$DESKTOP_APP/Contents/Resources/AppIcon.icns"

    rm -rf "$ICONSET_DIR"
    mkdir -p "$ICONSET_DIR" "$DESKTOP_APP/Contents/Resources"

    "$PYTHON_BIN" - "$ICON_FILE" "$ICONSET_DIR" <<'PY'
from pathlib import Path
import sys

from PIL import Image

icon_path = Path(sys.argv[1])
iconset_dir = Path(sys.argv[2])
source = Image.open(icon_path).convert("RGBA")

sizes = [16, 32, 128, 256, 512]
for size in sizes:
    source.resize((size, size), Image.LANCZOS).save(iconset_dir / f"icon_{size}x{size}.png")
    source.resize((size * 2, size * 2), Image.LANCZOS).save(iconset_dir / f"icon_{size}x{size}@2x.png")
PY

    if command -v iconutil >/dev/null 2>&1; then
        iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE" >/dev/null 2>&1 || true
    fi
}

create_desktop_app() {
    mkdir -p "$DESKTOP_APP/Contents/MacOS" "$DESKTOP_APP/Contents/Resources"

    cat > "$DESKTOP_APP/Contents/MacOS/launcher" <<EOF
#!/bin/zsh
APP_DIR="$APP_DIR"
PYTHON_BIN="\$APP_DIR/.venv/bin/python"
export PATH="\$APP_DIR:\$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
cd "\$APP_DIR"
exec "\$PYTHON_BIN" "src/ytdlp_gui_downloader.py"
EOF
    chmod +x "$DESKTOP_APP/Contents/MacOS/launcher"

    cat > "$DESKTOP_APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Baixador de Videos 3000</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>br.com.edgesolution.baixadordevideos3000</string>
    <key>CFBundleName</key>
    <string>Baixador de Videos 3000</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF

    create_app_icon
    touch "$DESKTOP_APP"
}

create_desktop_app

echo
echo "Instalacao concluida."
echo "Um icone foi criado na Area de Trabalho:"
echo "$DESKTOP_APP"
echo
echo "Abrindo o aplicativo..."
open "$DESKTOP_APP"
