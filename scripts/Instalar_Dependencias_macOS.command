#!/bin/zsh
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 nao foi encontrado. Instale pelo site python.org ou pelo Homebrew."
    read "?Pressione Enter para fechar..."
    exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade -r requirements.txt

python3 - <<'PY'
try:
    import certifi
    print("Certificados SSL configurados com certifi:")
    print(certifi.where())
except Exception as exc:
    print(f"Aviso: nao consegui localizar o certifi: {exc}")
PY

echo
echo "Dependencias instaladas."
read "?Pressione Enter para fechar..."
