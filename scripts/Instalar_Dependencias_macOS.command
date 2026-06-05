#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
RUNTIME_HELPERS="$APP_DIR/scripts/macos_python_runtime.zsh"

cd "$APP_DIR"

if [ ! -f "$RUNTIME_HELPERS" ]; then
    echo "Nao encontrei scripts/macos_python_runtime.zsh."
    echo "Extraia o ZIP inteiro e rode o instalador novamente."
    read "?Pressione Enter para fechar..."
    exit 1
fi

source "$RUNTIME_HELPERS"

PYTHON_BIN="$(ensure_app_venv "$APP_DIR")"
install_app_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
try:
    import certifi
    print("Certificados SSL configurados com certifi:")
    print(certifi.where())
except Exception as exc:
    print(f"Aviso: nao consegui localizar o certifi: {exc}")
PY

chmod_app_commands "$APP_DIR"

echo
echo "Dependencias instaladas."
read "?Pressione Enter para fechar..."
