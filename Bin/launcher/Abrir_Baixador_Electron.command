#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ELECTRON_DIR="$APP_DIR/electron"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"
LOG_FILE="$APP_DIR/BaixadorDeVideos3000_Electron_macOS.log"
ELECTRON_VERSION="39.8.10"
ELECTRON_RUNTIME_DIR="$HOME/Library/Application Support/BaixadorDeVideos3000/ElectronRuntime/$ELECTRON_VERSION"

export PATH="$APP_DIR:$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

escape_dialog_text() {
    printf "%s" "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

ask_yes_no() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "button returned of (display dialog \"$(escape_dialog_text "$message")\" buttons {\"Cancelar\", \"Instalar\"} default button \"Instalar\" with icon note)" 2>/dev/null | grep -q "Instalar"
        return $?
    fi
    echo "$message"
    read "?Instalar agora? [s/N] " answer
    [[ "$answer" == "s" || "$answer" == "S" ]]
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

download_with_progress() {
    local url="$1"
    local target="$2"
    local label="$3"
    echo "> $label" | tee -a "$LOG_FILE"
    curl -L --progress-bar "$url" -o "$target" 2>&1 | tee -a "$LOG_FILE"
}

electron_download_url() {
    local arch_name
    case "$(uname -m)" in
        arm64)
            arch_name="arm64"
            ;;
        x86_64|amd64)
            arch_name="x64"
            ;;
        *)
            arch_name="x64"
            ;;
    esac
    echo "https://github.com/electron/electron/releases/download/v$ELECTRON_VERSION/electron-v$ELECTRON_VERSION-darwin-$arch_name.zip"
}

electron_binary() {
    local candidate="$ELECTRON_RUNTIME_DIR/Electron.app/Contents/MacOS/Electron"
    if [ -x "$candidate" ]; then
        echo "$candidate"
        return 0
    fi
    return 1
}

ensure_dependencies() {
    cd "$ELECTRON_DIR"
    if electron_binary >/dev/null 2>&1; then
        return
    fi

    if ! ask_yes_no "O runtime Electron ainda nao esta preparado neste Mac. Deseja instalar agora?"; then
        echo "Dependencias Electron nao instaladas." | tee -a "$LOG_FILE"
        exit 1
    fi

    mkdir -p "$ELECTRON_RUNTIME_DIR"
    local electron_zip="$APP_DIR/electron-runtime-$ELECTRON_VERSION.zip"
    local extract_dir="$APP_DIR/electron-runtime-extract"
    local url
    url="$(electron_download_url)"

    echo "Instalacao Electron macOS sem npm: usando runtime oficial em $ELECTRON_RUNTIME_DIR" | tee -a "$LOG_FILE"
    rm -rf "$ELECTRON_RUNTIME_DIR/Electron.app" "$ELECTRON_RUNTIME_DIR/node_modules" "$ELECTRON_RUNTIME_DIR/package.json" "$ELECTRON_RUNTIME_DIR/package-lock.json"
    rm -rf "$ELECTRON_DIR/node_modules" "$ELECTRON_DIR/package-lock.json"
    rm -rf "$extract_dir"
    mkdir -p "$extract_dir"

    download_with_progress "$url" "$electron_zip" "Baixando Electron para macOS"
    unzip -q -o "$electron_zip" -d "$extract_dir" 2>&1 | tee -a "$LOG_FILE"
    if [ ! -d "$extract_dir/Electron.app" ]; then
        error_dialog "O arquivo do Electron foi baixado, mas Electron.app nao foi encontrado dentro dele. Veja o log em: $LOG_FILE"
        exit 1
    fi
    mv "$extract_dir/Electron.app" "$ELECTRON_RUNTIME_DIR/Electron.app"
    chmod +x "$ELECTRON_RUNTIME_DIR/Electron.app/Contents/MacOS/Electron" 2>/dev/null || true
    xattr -dr com.apple.quarantine "$ELECTRON_RUNTIME_DIR/Electron.app" 2>/dev/null || true
    rm -rf "$extract_dir" "$electron_zip"

    if ! electron_binary >/dev/null 2>&1; then
        error_dialog "O Electron do macOS nao apareceu depois da instalacao. Veja o log em: $LOG_FILE"
        exit 1
    fi
}

build_is_old() {
    [ ! -f "$ELECTRON_DIR/dist/main/main.js" ] && return 0
    [ ! -f "$ELECTRON_DIR/dist/renderer/index.html" ] && return 0
    return 1
}

if [ ! -d "$ELECTRON_DIR" ]; then
    error_dialog "Nao encontrei a pasta electron dentro do projeto."
    exit 1
fi

touch "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "[$(date)] Abrindo Electron em $ELECTRON_DIR" >> "$LOG_FILE"

ensure_dependencies

cd "$ELECTRON_DIR"
if build_is_old; then
    error_dialog "Nao encontrei o build da interface Electron em: $ELECTRON_DIR/dist. Atualize a pasta do programa e rode o setup novamente."
    exit 1
fi

ELECTRON_BIN="$(electron_binary)"
echo "[$(date)] Iniciando Electron em primeiro plano" >> "$LOG_FILE"
exec "$ELECTRON_BIN" --disable-gpu "$ELECTRON_DIR" >> "$LOG_FILE" 2>&1
