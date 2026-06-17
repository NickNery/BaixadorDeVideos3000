#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$ROOT_DIR/Bin"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"
LOG_FILE="$ROOT_DIR/setup/setup_macos.log"
DESKTOP_DIR="$HOME/Desktop"

export PATH="$APP_DIR:$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

escape_dialog_text() {
    printf "%s" "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

info_dialog() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "display dialog \"$(escape_dialog_text "$message")\" buttons {\"OK\"} default button \"OK\" with icon note" >/dev/null 2>&1 || true
    else
        echo "$message"
    fi
}

error_dialog() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "display dialog \"$(escape_dialog_text "$message")\" buttons {\"OK\"} default button \"OK\" with icon stop" >/dev/null 2>&1 || true
    else
        echo "$message"
    fi
}

choose_shortcuts() {
    if command -v osascript >/dev/null 2>&1; then
        osascript <<'OSA'
set chosenItems to choose from list {"Python", "Electron"} with title "Setup - Baixador de Videos 3000" with prompt "Quais atalhos voce quer criar na Area de Trabalho?" default items {"Python", "Electron"} with multiple selections allowed
if chosenItems is false then
    return "CANCEL"
end if
set AppleScript's text item delimiters to ","
return chosenItems as text
OSA
    else
        echo "Python,Electron"
    fi
}

create_app_icon() {
    local desktop_app="$1"
    local python_bin="$2"
    local icon_file="$APP_DIR/assets/app_icon.png"
    if [ ! -f "$icon_file" ]; then
        icon_file="$APP_DIR/assets/favicon.ico"
    fi
    if [ ! -f "$icon_file" ]; then
        return
    fi

    local iconset_dir="$ROOT_DIR/build/AppIcon.iconset"
    local icns_file="$desktop_app/Contents/Resources/AppIcon.icns"
    rm -rf "$iconset_dir"
    mkdir -p "$iconset_dir" "$desktop_app/Contents/Resources"

    "$python_bin" - "$icon_file" "$iconset_dir" <<'PY'
from pathlib import Path
import sys
from PIL import Image

icon_path = Path(sys.argv[1])
iconset_dir = Path(sys.argv[2])
source = Image.open(icon_path).convert("RGBA")
for size in [16, 32, 128, 256, 512]:
    source.resize((size, size), Image.LANCZOS).save(iconset_dir / f"icon_{size}x{size}.png")
    source.resize((size * 2, size * 2), Image.LANCZOS).save(iconset_dir / f"icon_{size}x{size}@2x.png")
PY

    if command -v iconutil >/dev/null 2>&1; then
        iconutil -c icns "$iconset_dir" -o "$icns_file" >/dev/null 2>&1 || true
    fi
}

create_desktop_app() {
    local app_name="$1"
    local launcher_path="$2"
    local bundle_id="$3"
    local python_bin="$4"
    local desktop_app="$DESKTOP_DIR/$app_name.app"

    rm -rf "$desktop_app"
    mkdir -p "$desktop_app/Contents/MacOS" "$desktop_app/Contents/Resources"

    cat > "$desktop_app/Contents/MacOS/launcher" <<EOF
#!/bin/zsh
APP_DIR="$APP_DIR"
export PATH="\$APP_DIR:\$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
cd "\$APP_DIR"
exec "$launcher_path"
EOF
    chmod +x "$desktop_app/Contents/MacOS/launcher"

    cat > "$desktop_app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>$app_name</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>$bundle_id</string>
    <key>CFBundleName</key>
    <string>$app_name</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>
EOF

    create_app_icon "$desktop_app" "$python_bin"
    touch "$desktop_app"
}

ensure_node() {
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        return
    fi
    ensure_homebrew
    brew install node
}

ensure_ytdlp_macos() {
    local target="$APP_DIR/release/yt-dlp"
    mkdir -p "$APP_DIR/release"
    if [ ! -x "$target" ]; then
        curl -L "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos" -o "$target"
        chmod +x "$target"
    fi
}

prepare_electron() {
    ensure_node
    cd "$APP_DIR/electron"
    if [ ! -x "node_modules/electron/dist/Electron.app/Contents/MacOS/Electron" ]; then
        npm install 2>&1 | tee -a "$LOG_FILE"
    fi
    if [ -f "node_modules/electron/install.js" ] && [ ! -x "node_modules/electron/dist/Electron.app/Contents/MacOS/Electron" ]; then
        node node_modules/electron/install.js 2>&1 | tee -a "$LOG_FILE"
    fi
    npm run build 2>&1 | tee -a "$LOG_FILE"
}

main() {
    if [ ! -d "$APP_DIR" ]; then
        error_dialog "Nao encontrei a pasta Bin. Extraia o ZIP inteiro e rode o setup novamente."
        exit 1
    fi
    if [ ! -f "$RUNTIME_HELPERS" ]; then
        error_dialog "Nao encontrei $RUNTIME_HELPERS."
        exit 1
    fi

    source "$RUNTIME_HELPERS"
    mkdir -p "$ROOT_DIR/setup"
    touch "$LOG_FILE"

    selection="$(choose_shortcuts)"
    if [ "$selection" = "CANCEL" ]; then
        exit 0
    fi

    info_dialog "O setup vai preparar as dependencias. Isso pode demorar alguns minutos."

    cd "$APP_DIR"
    PYTHON_BIN="$(ensure_app_venv "$APP_DIR")"

    ensure_homebrew
    if ! command -v ffmpeg >/dev/null 2>&1; then
        brew install ffmpeg
    fi
    ensure_ytdlp_macos
    install_app_dependencies "$PYTHON_BIN"
    chmod_app_commands "$APP_DIR"
    prepare_electron

    if [[ "$selection" == *"Python"* ]]; then
        create_desktop_app "Baixador de Videos 3000" "$APP_DIR/launcher/Abrir_Baixador_YTDLP.command" "br.com.edgesolution.baixadordevideos3000.python" "$PYTHON_BIN"
    fi
    if [[ "$selection" == *"Electron"* ]]; then
        create_desktop_app "Baixador de Videos 3000 Electron" "$APP_DIR/launcher/Abrir_Baixador_Electron.command" "br.com.edgesolution.baixadordevideos3000.electron" "$PYTHON_BIN"
    fi

    info_dialog "Instalacao concluida. Os atalhos selecionados foram criados na Area de Trabalho."
}

main "$@"
