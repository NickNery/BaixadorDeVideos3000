#!/bin/zsh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"

cd "$APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 nao foi encontrado."
    echo "Rode scripts/Instalador_Automatico_macOS.command para instalar tudo automaticamente."
    read "?Pressione Enter para fechar..."
    exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
    python3 -m venv "$VENV_DIR"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install --upgrade -r requirements.txt

"$PYTHON_BIN" - <<'PY'
try:
    import certifi
    print("Certificados SSL configurados com certifi:")
    print(certifi.where())
except Exception as exc:
    print(f"Aviso: nao consegui localizar o certifi: {exc}")
PY

chmod +x "$APP_DIR/scripts/"*.command 2>/dev/null || true
chmod +x "$APP_DIR/release/"*.command 2>/dev/null || true

echo
echo "Dependencias instaladas."
read "?Pressione Enter para fechar..."
