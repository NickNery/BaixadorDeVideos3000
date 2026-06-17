#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ELECTRON_DIR="$APP_DIR/electron"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"
LOG_FILE="$APP_DIR/BaixadorDeVideos3000_Electron_macOS.log"

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

ensure_node() {
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        return
    fi

    if ! ask_yes_no "A versao Electron precisa do Node.js e npm. Nao encontrei neste Mac. Deseja instalar automaticamente?"; then
        echo "Node.js nao instalado." | tee -a "$LOG_FILE"
        exit 1
    fi

    if [ -f "$RUNTIME_HELPERS" ]; then
        source "$RUNTIME_HELPERS"
        ensure_homebrew
    elif ! command -v brew >/dev/null 2>&1; then
        open "https://nodejs.org/" || true
        error_dialog "Nao encontrei Homebrew para instalar Node.js. Abri o site do Node.js para instalacao manual."
        exit 1
    fi

    brew install node
}

electron_binary() {
    local candidates=(
        "$ELECTRON_DIR/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron"
        "$ELECTRON_DIR/node_modules/.bin/electron"
    )

    for candidate in "${candidates[@]}"; do
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

ensure_dependencies() {
    cd "$ELECTRON_DIR"
    if electron_binary >/dev/null 2>&1; then
        return
    fi

    if ! ask_yes_no "As dependencias da versao Electron ainda nao estao instaladas. Deseja rodar npm install agora?"; then
        echo "Dependencias Electron nao instaladas." | tee -a "$LOG_FILE"
        exit 1
    fi

    npm install 2>&1 | tee -a "$LOG_FILE"

    if ! electron_binary >/dev/null 2>&1 && [ -f "$ELECTRON_DIR/node_modules/electron/install.js" ]; then
        node "$ELECTRON_DIR/node_modules/electron/install.js" 2>&1 | tee -a "$LOG_FILE"
    fi

    if ! electron_binary >/dev/null 2>&1; then
        error_dialog "O npm terminou, mas o Electron do macOS nao apareceu. Veja o log em: $LOG_FILE"
        exit 1
    fi
}

build_is_old() {
    [ ! -f "$ELECTRON_DIR/dist/main/main.js" ] && return 0
    [ ! -f "$ELECTRON_DIR/dist/renderer/index.html" ] && return 0
    local newest_source
    newest_source="$(find "$ELECTRON_DIR/src" "$ELECTRON_DIR/package.json" "$ELECTRON_DIR/vite.config.ts" "$ELECTRON_DIR/tsconfig.json" "$ELECTRON_DIR/tsconfig.main.json" -type f -print0 | xargs -0 stat -f "%m" | sort -nr | head -n 1)"
    local oldest_build
    oldest_build="$(stat -f "%m" "$ELECTRON_DIR/dist/main/main.js" "$ELECTRON_DIR/dist/renderer/index.html" | sort -n | head -n 1)"
    [ "$newest_source" -gt "$oldest_build" ]
}

if [ ! -d "$ELECTRON_DIR" ]; then
    error_dialog "Nao encontrei a pasta electron dentro do projeto."
    exit 1
fi

touch "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "[$(date)] Abrindo Electron em $ELECTRON_DIR" >> "$LOG_FILE"

ensure_node
ensure_dependencies

cd "$ELECTRON_DIR"
if build_is_old; then
    npm run build 2>&1 | tee -a "$LOG_FILE"
fi

ELECTRON_BIN="$(electron_binary)"
"$ELECTRON_BIN" --disable-gpu "$ELECTRON_DIR" >> "$LOG_FILE" 2>&1 &
PID=$!
sleep 3

if ! kill -0 "$PID" >/dev/null 2>&1; then
    error_dialog "O Electron tentou abrir, mas fechou logo em seguida. Veja o log em: $LOG_FILE"
    exit 1
fi

info_dialog "Versao Electron aberta."
