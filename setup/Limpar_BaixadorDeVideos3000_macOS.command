#!/bin/zsh
set -u
setopt NULL_GLOB

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_SUPPORT_ROOT="$HOME/Library/Application Support/BaixadorDeVideos3000"
APP_ROOT="$APP_SUPPORT_ROOT/App"
ELECTRON_RUNTIME_ROOT="$APP_SUPPORT_ROOT/ElectronRuntime"
CURRENT_ELECTRON_VERSION="39.8.10"
LOG_DIR="$HOME/Library/Logs/BaixadorDeVideos3000"
LOG_FILE="$LOG_DIR/cleanup_macos.log"
DOWNLOADS_DIR="$HOME/Downloads"
TRASH_DIR="$HOME/.Trash"

typeset -i REMOVED_KB=0
typeset -i TRASHED_KB=0
typeset -i TRASHED_COUNT=0

mkdir -p "$LOG_DIR" "$TRASH_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

escape_dialog_text() {
    printf "%s" "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

confirm_dialog() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "button returned of (display dialog \"$(escape_dialog_text "$message")\" buttons {\"Cancelar\", \"Limpar\"} default button \"Limpar\" cancel button \"Cancelar\" with icon caution)" 2>/dev/null | grep -q "Limpar"
        return $?
    fi
    echo "$message"
    read "?Continuar? [s/N] " answer
    [[ "$answer" == "s" || "$answer" == "S" ]]
}

choose_deep_cleanup() {
    local message="Deseja incluir caches gerais de instalacao?\n\nIsso limpa caches do pip, npm e Homebrew. Nenhum aplicativo sera removido, mas esses arquivos precisarao ser baixados novamente no futuro."
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "button returned of (display dialog \"$(escape_dialog_text "$message")\" buttons {\"Somente segura\", \"Incluir caches\"} default button \"Somente segura\" with icon note)" 2>/dev/null | grep -q "Incluir caches"
        return $?
    fi
    echo "$message"
    read "?Incluir caches gerais? [s/N] " answer
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

path_size_kb() {
    local target="$1"
    local value
    value="$(du -sk "$target" 2>/dev/null | awk 'NR == 1 {print $1}')"
    echo "${value:-0}"
}

format_kb() {
    awk -v kb="$1" 'BEGIN {
        if (kb >= 1048576) printf "%.2f GB", kb / 1048576;
        else if (kb >= 1024) printf "%.1f MB", kb / 1024;
        else printf "%d KB", kb;
    }'
}

safe_remove_path() {
    local target="$1"
    local allowed_root="$2"
    local size

    if [ -z "$target" ] || [ "$target" = "/" ] || [ "$target" = "$HOME" ]; then
        echo "[PROTEGIDO] Caminho recusado: $target"
        return
    fi
    if [[ "$target" != "$allowed_root" && "$target" != "$allowed_root/"* ]]; then
        echo "[PROTEGIDO] Fora da area permitida: $target"
        return
    fi
    if [ ! -e "$target" ]; then
        return
    fi

    size="$(path_size_kb "$target")"
    if /bin/rm -rf "$target"; then
        REMOVED_KB=$((REMOVED_KB + size))
        echo "[REMOVIDO] $target"
    else
        echo "[FALHA] Nao foi possivel remover: $target"
    fi
}

trash_path() {
    local source="$1"
    local name target stem suffix counter size

    [ -e "$source" ] || return
    case "$SCRIPT_DIR/" in
        "$source/"*)
            echo "[MANTIDO] Pacote atualmente em uso: $source"
            return
            ;;
    esac

    name="$(basename "$source")"
    target="$TRASH_DIR/$name"
    counter=1
    if [[ "$name" == *.* ]]; then
        stem="${name%.*}"
        suffix=".${name##*.}"
    else
        stem="$name"
        suffix=""
    fi
    while [ -e "$target" ]; do
        target="$TRASH_DIR/$stem ($counter)$suffix"
        counter=$((counter + 1))
    done

    size="$(path_size_kb "$source")"
    if mv "$source" "$target"; then
        TRASHED_KB=$((TRASHED_KB + size))
        TRASHED_COUNT=$((TRASHED_COUNT + 1))
        echo "[LIXEIRA] $source"
    else
        echo "[FALHA] Nao foi possivel mover para a Lixeira: $source"
    fi
}

collect_download_candidates() {
    local candidate
    [ -d "$DOWNLOADS_DIR" ] || return
    while IFS= read -r candidate; do
        trash_path "$candidate"
    done < <(
        find "$DOWNLOADS_DIR" -mindepth 1 -maxdepth 1 \
            \( -name 'BaixadorDeVideos3000*' \
            -o -name 'Baixador_YTDLP_Windows_macOS*' \
            -o -name 'Baixador de Videos 3000*' \) \
            -print 2>/dev/null
    )
}

clean_app_files() {
    local runtime log_file

    safe_remove_path "$APP_ROOT/build" "$APP_ROOT/build"
    safe_remove_path "$APP_ROOT/setup" "$APP_ROOT/setup"
    safe_remove_path "$APP_ROOT/Bin/electron-runtime-extract" "$APP_ROOT/Bin/electron-runtime-extract"

    if [ -d "$APP_ROOT/Bin" ]; then
        for runtime in "$APP_ROOT/Bin"/electron-runtime-*.zip; do
            [ -e "$runtime" ] || continue
            safe_remove_path "$runtime" "$APP_ROOT/Bin"
        done
    fi

    if [ -d "$ELECTRON_RUNTIME_ROOT" ]; then
        for runtime in "$ELECTRON_RUNTIME_ROOT"/*; do
            [ -e "$runtime" ] || continue
            if [ "$(basename "$runtime")" != "$CURRENT_ELECTRON_VERSION" ]; then
                safe_remove_path "$runtime" "$ELECTRON_RUNTIME_ROOT"
            fi
        done
    fi

    safe_remove_path "$ELECTRON_RUNTIME_ROOT/$CURRENT_ELECTRON_VERSION/node_modules" "$ELECTRON_RUNTIME_ROOT/$CURRENT_ELECTRON_VERSION"
    safe_remove_path "$ELECTRON_RUNTIME_ROOT/$CURRENT_ELECTRON_VERSION/package.json" "$ELECTRON_RUNTIME_ROOT/$CURRENT_ELECTRON_VERSION"
    safe_remove_path "$ELECTRON_RUNTIME_ROOT/$CURRENT_ELECTRON_VERSION/package-lock.json" "$ELECTRON_RUNTIME_ROOT/$CURRENT_ELECTRON_VERSION"

    safe_remove_path "$HOME/Library/Caches/BaixadorDeVideos3000" "$HOME/Library/Caches/BaixadorDeVideos3000"
    safe_remove_path "$HOME/Library/Caches/baixador-de-videos-3000-electron" "$HOME/Library/Caches/baixador-de-videos-3000-electron"

    for log_file in "$LOG_DIR"/*; do
        [ -e "$log_file" ] || continue
        [ "$log_file" = "$LOG_FILE" ] && continue
        safe_remove_path "$log_file" "$LOG_DIR"
    done
}

clean_shared_install_caches() {
    safe_remove_path "$HOME/Library/Caches/pip" "$HOME/Library/Caches/pip"
    safe_remove_path "$HOME/.npm/_cacache" "$HOME/.npm/_cacache"

    if command -v brew >/dev/null 2>&1; then
        echo "[HOMEBREW] Removendo downloads e versoes antigas..."
        brew cleanup --prune=all || true
    fi
}

main() {
    local deep_cleanup="nao"
    local removed_text trashed_text message

    if ! confirm_dialog "O limpador vai:\n\n- manter a instalacao atual e seus atalhos;\n- remover logs, temporarios e runtimes Electron antigos;\n- enviar ZIPs e copias repetidas da pasta Downloads para a Lixeira.\n\nNada fora das pastas do Baixador sera apagado sem uma segunda confirmacao."; then
        exit 0
    fi
    if choose_deep_cleanup; then
        deep_cleanup="sim"
    fi

    echo
    echo "=================================================="
    echo "  LIMPADOR - BAIXADOR DE VIDEOS 3000"
    echo "=================================================="
    echo "Inicio: $(date)"

    clean_app_files
    collect_download_candidates
    if [ "$deep_cleanup" = "sim" ]; then
        clean_shared_install_caches
    fi

    removed_text="$(format_kb "$REMOVED_KB")"
    trashed_text="$(format_kb "$TRASHED_KB")"
    message="Limpeza concluida.\n\nEspaco removido de caches e temporarios: $removed_text\nItens enviados para a Lixeira: $TRASHED_COUNT ($trashed_text)\n\nA instalacao atual foi preservada. Esvazie a Lixeira para liberar o espaco dos downloads antigos.\n\nLog: $LOG_FILE"
    echo
    echo "$message"
    info_dialog "$message"
}

main "$@"
