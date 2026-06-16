#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ELECTRON_DIR="$APP_DIR/electron"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"

ask_yes_no() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "button returned of (display dialog \"$message\" buttons {\"Cancelar\", \"Instalar\"} default button \"Instalar\" with icon note)" 2>/dev/null | grep -q "Instalar"
        return $?
    fi
    echo "$message"
    read "?Instalar agora? [s/N] " answer
    [[ "$answer" == "s" || "$answer" == "S" ]]
}

info_dialog() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "display dialog \"$message\" buttons {\"OK\"} default button \"OK\" with icon note" >/dev/null 2>&1 || true
    else
        echo "$message"
    fi
}

ensure_node() {
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        return
    fi

    if ! ask_yes_no "A versao Electron precisa do Node.js e npm. Nao encontrei neste Mac. Deseja instalar automaticamente?"; then
        echo "Node.js nao instalado."
        exit 1
    fi

    if [ -f "$RUNTIME_HELPERS" ]; then
        source "$RUNTIME_HELPERS"
        ensure_homebrew
    elif ! command -v brew >/dev/null 2>&1; then
        echo "Nao encontrei Homebrew para instalar Node.js."
        open "https://nodejs.org/" || true
        exit 1
    fi

    brew install node
}

ensure_dependencies() {
    cd "$ELECTRON_DIR"
    if [ -x "node_modules/.bin/electron" ]; then
        return
    fi

    if ! ask_yes_no "As dependencias da versao Electron ainda nao estao instaladas. Deseja rodar npm install agora?"; then
        echo "Dependencias Electron nao instaladas."
        exit 1
    fi

    npm install
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
    info_dialog "Nao encontrei a pasta electron dentro do projeto."
    exit 1
fi

ensure_node
ensure_dependencies

cd "$ELECTRON_DIR"
if build_is_old; then
    npm run build
fi

"$ELECTRON_DIR/node_modules/.bin/electron" "$ELECTRON_DIR" >/dev/null 2>&1 &
info_dialog "Versao Electron aberta."
