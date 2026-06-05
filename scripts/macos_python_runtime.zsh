#!/bin/zsh

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

    echo "Homebrew nao foi encontrado." >&2
    echo "Ele sera instalado para baixar Python e ffmpeg automaticamente." >&2
    echo >&2
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    load_brew_shellenv
}

python_base_executable() {
    "$1" - <<'PY' 2>/dev/null
import sys
print(getattr(sys, "_base_executable", sys.executable))
PY
}

is_apple_command_line_tools_python() {
    local base_executable
    base_executable="$(python_base_executable "$1")"

    case "$base_executable" in
        /Library/Developer/CommandLineTools/*|/usr/bin/python3)
            return 0
            ;;
    esac

    return 1
}

python_tk_works() {
    "$1" - <<'PY' >/dev/null 2>&1
import tkinter as tk
root = tk.Tk()
root.withdraw()
root.update_idletasks()
root.destroy()
PY
}

python_is_usable_for_app() {
    local python_bin="$1"

    if [ -z "$python_bin" ] || [ ! -x "$python_bin" ]; then
        return 1
    fi

    if is_apple_command_line_tools_python "$python_bin"; then
        return 1
    fi

    python_tk_works "$python_bin"
}

install_homebrew_python() {
    ensure_homebrew

    echo "Instalando/atualizando Python pelo Homebrew..." >&2
    brew install python || brew upgrade python || true

    if ! find_usable_python >/dev/null 2>&1; then
        echo "Instalando suporte Tkinter para o Python..." >&2
        for formula in python-tk python-tk@3.14 python-tk@3.13 python-tk@3.12 python-tk@3.11; do
            brew install "$formula" >/dev/null 2>&1 && break
        done
    fi
}

find_usable_python() {
    load_brew_shellenv

    local candidates=()

    if command -v brew >/dev/null 2>&1; then
        local brew_prefix
        brew_prefix="$(brew --prefix 2>/dev/null)"
        candidates+=(
            "$brew_prefix/bin/python3"
            "$brew_prefix/opt/python/libexec/bin/python"
            "$brew_prefix/opt/python@3.14/bin/python3"
            "$brew_prefix/opt/python@3.13/bin/python3"
            "$brew_prefix/opt/python@3.12/bin/python3"
            "$brew_prefix/opt/python@3.11/bin/python3"
        )
    fi

    candidates+=(
        "/opt/homebrew/bin/python3"
        "/usr/local/bin/python3"
        "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
    )

    local path_python
    path_python="$(command -v python3 2>/dev/null || true)"
    if [ -n "$path_python" ]; then
        candidates+=("$path_python")
    fi

    local candidate
    local seen=""
    for candidate in "${candidates[@]}"; do
        if [ -z "$candidate" ] || [[ " $seen " == *" $candidate "* ]]; then
            continue
        fi
        seen="$seen $candidate"

        if python_is_usable_for_app "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

ensure_usable_python() {
    local python_bin
    python_bin="$(find_usable_python || true)"

    if [ -z "$python_bin" ]; then
        install_homebrew_python
        python_bin="$(find_usable_python || true)"
    fi

    if [ -z "$python_bin" ]; then
        echo >&2
        echo "[ERRO] Nao encontrei um Python com Tkinter funcionando." >&2
        echo "O Python do Command Line Tools da Apple foi ignorado porque pode travar o app." >&2
        echo "Instale o Python pelo Homebrew ou pelo python.org e rode este instalador novamente." >&2
        exit 1
    fi

    echo "$python_bin"
}

ensure_app_venv() {
    local app_dir="$1"
    local venv_dir="$app_dir/.venv"
    local python_bin="$venv_dir/bin/python"
    local base_python

    if [ -x "$python_bin" ] && python_is_usable_for_app "$python_bin"; then
        echo "$python_bin"
        return 0
    fi

    if [ -d "$venv_dir" ]; then
        echo "Removendo ambiente Python antigo/incompativel..." >&2
        rm -rf "$venv_dir"
    fi

    base_python="$(ensure_usable_python)"
    echo "Criando ambiente Python do aplicativo com:" >&2
    echo "$base_python" >&2
    "$base_python" -m venv "$venv_dir"

    if ! python_is_usable_for_app "$python_bin"; then
        echo >&2
        echo "[ERRO] O ambiente Python foi criado, mas o Tkinter ainda nao abriu corretamente." >&2
        echo "Rode este instalador novamente ou instale o Python do python.org." >&2
        exit 1
    fi

    echo "$python_bin"
}

install_app_dependencies() {
    local python_bin="$1"

    "$python_bin" -m pip install --upgrade pip
    "$python_bin" -m pip install --upgrade -r requirements.txt
}

chmod_app_commands() {
    local app_dir="$1"

    chmod +x "$app_dir/scripts/"*.command 2>/dev/null || true
    chmod +x "$app_dir/release/"*.command 2>/dev/null || true
}
