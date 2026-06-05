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
