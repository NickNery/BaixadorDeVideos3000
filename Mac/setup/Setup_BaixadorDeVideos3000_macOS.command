#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_APP_DIR="$SOURCE_ROOT/Bin"
ROOT_DIR="$HOME/Library/Application Support/BaixadorDeVideos3000/App"
APP_DIR="$ROOT_DIR/Bin"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"
LOG_DIR="$HOME/Library/Logs/BaixadorDeVideos3000"
LOG_FILE="$LOG_DIR/setup_macos.log"
DESKTOP_DIR="$HOME/Desktop"
TOTAL_STEPS=9
CURRENT_STEP=0
ELECTRON_VERSION="39.8.10"
ELECTRON_RUNTIME_DIR="$HOME/Library/Application Support/BaixadorDeVideos3000/ElectronRuntime/$ELECTRON_VERSION"

export PATH="$APP_DIR:$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

progress_step() {
    local message="$1"
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    local filled=$((percent / 5))
    local empty=$((20 - filled))
    local bar=""
    local i
    for ((i = 0; i < filled; i++)); do bar="${bar}#"; done
    for ((i = 0; i < empty; i++)); do bar="${bar}-"; done
    echo
    echo "[$bar] ${percent}% - $message" | tee -a "$LOG_FILE"
}

run_logged() {
    local message="$1"
    shift
    echo "> $message" | tee -a "$LOG_FILE"
    "$@" 2>&1 | tee -a "$LOG_FILE"
}

download_with_progress() {
    local url="$1"
    local target="$2"
    local label="$3"
    echo "> $label" | tee -a "$LOG_FILE"
    curl -L --progress-bar "$url" -o "$target" 2>&1 | tee -a "$LOG_FILE"
}

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

install_program_files() {
    if [ ! -d "$SOURCE_APP_DIR" ]; then
        error_dialog "Nao encontrei a pasta Bin ao lado do setup. Baixe ou extraia o pacote completo e tente novamente."
        exit 1
    fi

    mkdir -p "$APP_DIR"
    if [ "$SOURCE_APP_DIR" = "$APP_DIR" ]; then
        echo "O programa ja esta na pasta local deste Mac." | tee -a "$LOG_FILE"
        return
    fi

    if [ -x /usr/bin/rsync ]; then
        run_logged "Copiando programa para este Mac" /usr/bin/rsync -rlt --delete \
            --exclude=.venv/ \
            --exclude=node_modules/ \
            --exclude=build/ \
            --exclude=doom/ \
            --exclude=ytdlp_gui_config.json \
            --exclude=release/yt-dlp \
            --exclude='*.log' \
            "$SOURCE_APP_DIR/" "$APP_DIR/"
    else
        run_logged "Copiando programa para este Mac" /usr/bin/ditto "$SOURCE_APP_DIR" "$APP_DIR"
    fi

    chmod +x "$APP_DIR/launcher/"*.command 2>/dev/null || true
    chmod +x "$APP_DIR/scripts/"*.command 2>/dev/null || true
    chmod +x "$APP_DIR/release/"*.command 2>/dev/null || true
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
    local log_dir="$HOME/Library/Logs/BaixadorDeVideos3000"
    local log_file="$log_dir/desktop_launchers.log"
    local script_file="$ROOT_DIR/build/$bundle_id.applescript"

    rm -rf "$desktop_app"
    mkdir -p "$ROOT_DIR/build"

    if command -v osacompile >/dev/null 2>&1; then
        cat > "$script_file" <<EOF
on run
    try
        set appDir to "$(escape_dialog_text "$APP_DIR")"
        set launcherPath to "$(escape_dialog_text "$launcher_path")"
        set logFile to "$(escape_dialog_text "$log_file")"
        set logDir to "$(escape_dialog_text "$log_dir")"
        set appName to "$(escape_dialog_text "$app_name")"
        set pathValue to appDir & ":" & appDir & "/.venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        set logMessage to "+[%Y-%m-%d %H:%M:%S] Abrindo " & appName & " via atalho .app"
        set shellCommand to "mkdir -p " & quoted form of logDir & "; export PATH=" & quoted form of pathValue & "; cd " & quoted form of appDir & "; chmod +x " & quoted form of launcherPath & " 2>/dev/null || true; echo '' >> " & quoted form of logFile & "; date " & quoted form of logMessage & " >> " & quoted form of logFile & "; exec /bin/zsh " & quoted form of launcherPath & " >> " & quoted form of logFile & " 2>&1"
        do shell script shellCommand
    on error errMsg number errNum
        display dialog "Nao consegui abrir " & appName & "." & return & return & errMsg & return & return & "Veja o log em:" & return & logFile buttons {"OK"} default button "OK" with icon stop
    end try
end run
EOF
        osacompile -o "$desktop_app" "$script_file"
    else
        mkdir -p "$desktop_app/Contents/MacOS" "$desktop_app/Contents/Resources"
        cat > "$desktop_app/Contents/MacOS/launcher" <<EOF
#!/bin/zsh
APP_DIR="$APP_DIR"
LOG_FILE="$log_file"
export PATH="\$APP_DIR:\$APP_DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
cd "\$APP_DIR"
chmod +x "$launcher_path" 2>/dev/null || true
echo "" >> "\$LOG_FILE"
echo "[\$(date)] Abrindo $app_name" >> "\$LOG_FILE"
exec /bin/zsh "$launcher_path" >> "\$LOG_FILE" 2>&1
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
    fi

    create_app_icon "$desktop_app" "$python_bin"
    local plist="$desktop_app/Contents/Info.plist"
    if [ -f "$plist" ] && [ -x /usr/libexec/PlistBuddy ]; then
        /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $app_name" "$plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $app_name" "$plist" 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :CFBundleName $app_name" "$plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleName string $app_name" "$plist" 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $bundle_id" "$plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string $bundle_id" "$plist" 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" "$plist" 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 10.15" "$plist" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 10.15" "$plist" 2>/dev/null || true
    fi
    xattr -dr com.apple.quarantine "$desktop_app" 2>/dev/null || true
    touch "$desktop_app"
}

ensure_ytdlp_macos() {
    local target="$APP_DIR/release/yt-dlp"
    mkdir -p "$APP_DIR/release"
    if [ -x "$target" ]; then
        echo "yt-dlp ja esta instalado." | tee -a "$LOG_FILE"
        return
    fi
    download_with_progress "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos" "$target" "Baixando yt-dlp"
    chmod +x "$target"
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

electron_binary_ready() {
    [ -x "$ELECTRON_RUNTIME_DIR/Electron.app/Contents/MacOS/Electron" ]
}

electron_build_ready() {
    [ -f "$APP_DIR/electron/dist/main/main.js" ] && [ -f "$APP_DIR/electron/dist/renderer/index.html" ]
}

prepare_electron() {
    if electron_binary_ready; then
        echo "Electron ja esta instalado." | tee -a "$LOG_FILE"
    else
        local electron_zip="$ROOT_DIR/setup/electron-runtime-$ELECTRON_VERSION.zip"
        local extract_dir="$ROOT_DIR/setup/electron-runtime-extract"
        local url
        url="$(electron_download_url)"

        echo "Instalacao Electron macOS sem npm: usando runtime oficial em $ELECTRON_RUNTIME_DIR" | tee -a "$LOG_FILE"
        mkdir -p "$ELECTRON_RUNTIME_DIR"
        rm -rf "$ELECTRON_RUNTIME_DIR/Electron.app" "$ELECTRON_RUNTIME_DIR/node_modules" "$ELECTRON_RUNTIME_DIR/package.json" "$ELECTRON_RUNTIME_DIR/package-lock.json"
        rm -rf "$APP_DIR/electron/node_modules" "$APP_DIR/electron/package-lock.json"
        rm -rf "$extract_dir"
        mkdir -p "$extract_dir"

        download_with_progress "$url" "$electron_zip" "Baixando Electron para macOS"
        run_logged "Extraindo Electron" unzip -q -o "$electron_zip" -d "$extract_dir"

        if [ ! -d "$extract_dir/Electron.app" ]; then
            error_dialog "O arquivo do Electron foi baixado, mas Electron.app nao foi encontrado dentro dele. Veja o log em: $LOG_FILE"
            exit 1
        fi

        mv "$extract_dir/Electron.app" "$ELECTRON_RUNTIME_DIR/Electron.app"
        chmod +x "$ELECTRON_RUNTIME_DIR/Electron.app/Contents/MacOS/Electron" 2>/dev/null || true
        xattr -dr com.apple.quarantine "$ELECTRON_RUNTIME_DIR/Electron.app" 2>/dev/null || true
        rm -rf "$extract_dir" "$electron_zip"
    fi
    if ! electron_binary_ready; then
        error_dialog "O Electron nao foi instalado corretamente. Veja o log em: $LOG_FILE"
        exit 1
    fi
    if electron_build_ready; then
        echo "Build Electron ja esta pronto." | tee -a "$LOG_FILE"
    else
        error_dialog "Nao encontrei o build da interface Electron em: $APP_DIR/electron/dist. Atualize a pasta do programa e rode o setup novamente."
        exit 1
    fi
}

main() {
    mkdir -p "$LOG_DIR" "$ROOT_DIR"
    touch "$LOG_FILE"

    selection="$(choose_shortcuts)"
    if [ "$selection" = "CANCEL" ]; then
        exit 0
    fi

    info_dialog "O setup vai preparar as dependencias. Isso pode demorar alguns minutos."

    progress_step "Instalando o programa neste Mac"
    install_program_files

    if [ ! -f "$RUNTIME_HELPERS" ]; then
        error_dialog "Nao encontrei $RUNTIME_HELPERS depois de copiar o programa. Veja o log em: $LOG_FILE"
        exit 1
    fi
    source "$RUNTIME_HELPERS"
    mkdir -p "$ROOT_DIR/setup"

    progress_step "Verificando Python do aplicativo"
    cd "$APP_DIR"
    PYTHON_BIN="$(ensure_app_venv "$APP_DIR")"

    progress_step "Verificando ffmpeg"
    if ! command -v ffmpeg >/dev/null 2>&1; then
        ensure_homebrew
        run_logged "Instalando ffmpeg" brew install ffmpeg
    else
        echo "ffmpeg ja esta instalado." | tee -a "$LOG_FILE"
    fi
    progress_step "Verificando yt-dlp"
    ensure_ytdlp_macos
    progress_step "Verificando dependencias Python"
    run_logged "Instalando/verificando dependencias Python" install_app_dependencies "$PYTHON_BIN"
    progress_step "Ajustando permissoes"
    chmod_app_commands "$APP_DIR"
    progress_step "Verificando Electron"
    prepare_electron
    progress_step "Criando atalhos"

    if [[ "$selection" == *"Python"* ]]; then
        create_desktop_app "Baixador de Videos 3000" "$APP_DIR/launcher/Abrir_Baixador_YTDLP.command" "br.com.edgesolution.baixadordevideos3000.python" "$PYTHON_BIN"
    fi
    if [[ "$selection" == *"Electron"* ]]; then
        create_desktop_app "Baixador de Videos 3000 Electron" "$APP_DIR/launcher/Abrir_Baixador_Electron.command" "br.com.edgesolution.baixadordevideos3000.electron" "$PYTHON_BIN"
    fi
    progress_step "Finalizando instalacao"

    info_dialog "Instalacao concluida. O programa foi instalado neste Mac e os atalhos selecionados foram criados na Area de Trabalho."
}

main "$@"
