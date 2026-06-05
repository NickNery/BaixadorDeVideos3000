#!/bin/zsh
set -e

cd "$(dirname "$0")/.."

BUILD_DIR="$PWD/build/macos"
VENV_DIR="$BUILD_DIR/venv"
DIST_DIR="$BUILD_DIR/dist"
YTDLP_BIN="$BUILD_DIR/yt-dlp"
APP_NAME="BaixadorDeVideos3000"
APP_PATH="$DIST_DIR/$APP_NAME.app"
DMG_PATH="$PWD/release/BaixadorDeVideos3000_macOS.dmg"
ICON_FILE="$PWD/assets/favicon.ico"
ICON_ICNS="$BUILD_DIR/AppIcon.icns"

echo "=================================================="
echo "  BUILD macOS - BAIXADOR DE VIDEOS 3000"
echo "=================================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 nao encontrado neste Mac de build."
    echo "Instale Python 3 ou rode scripts/Instalador_Automatico_macOS.command."
    exit 1
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR" "$PWD/release"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install pyinstaller pillow certifi imageio-ffmpeg

if [ -f "$ICON_FILE" ]; then
    ICONSET_DIR="$BUILD_DIR/AppIcon.iconset"
    mkdir -p "$ICONSET_DIR"
    "$VENV_DIR/bin/python" - "$ICON_FILE" "$ICONSET_DIR" <<'PY'
from pathlib import Path
import sys

from PIL import Image

icon_path = Path(sys.argv[1])
iconset_dir = Path(sys.argv[2])
source = Image.open(icon_path).convert("RGBA")

sizes = [16, 32, 128, 256, 512]
for size in sizes:
    source.resize((size, size), Image.LANCZOS).save(iconset_dir / f"icon_{size}x{size}.png")
    source.resize((size * 2, size * 2), Image.LANCZOS).save(iconset_dir / f"icon_{size}x{size}@2x.png")
PY
    if command -v iconutil >/dev/null 2>&1; then
        iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS" || true
    fi
fi

PYINSTALLER_ICON_ARGS=()
if [ -f "$ICON_ICNS" ]; then
    PYINSTALLER_ICON_ARGS=(--icon "$ICON_ICNS")
fi

echo "Baixando yt-dlp para macOS..."
curl -L "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos" -o "$YTDLP_BIN"
chmod +x "$YTDLP_BIN"

FFMPEG_BIN="$("$VENV_DIR/bin/python" - <<'PY'
import imageio_ffmpeg
print(imageio_ffmpeg.get_ffmpeg_exe())
PY
)"

"$VENV_DIR/bin/python" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "$APP_NAME" \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR/pyinstaller" \
    --specpath "$BUILD_DIR" \
    "${PYINSTALLER_ICON_ARGS[@]}" \
    --hidden-import certifi \
    --collect-data certifi \
    "src/ytdlp_gui_downloader.py"

cp "$YTDLP_BIN" "$APP_PATH/Contents/MacOS/yt-dlp"
cp "$FFMPEG_BIN" "$APP_PATH/Contents/MacOS/ffmpeg"
chmod +x "$APP_PATH/Contents/MacOS/yt-dlp" "$APP_PATH/Contents/MacOS/ffmpeg"

rm -f "$DMG_PATH"
hdiutil create \
    -volname "Baixador de Videos 3000" \
    -srcfolder "$APP_PATH" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

echo
echo "DMG criado em:"
echo "$DMG_PATH"
