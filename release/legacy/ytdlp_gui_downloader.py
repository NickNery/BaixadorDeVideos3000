from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
APP_FILE = ROOT / "python" / "src" / "ytdlp_gui_downloader.py"

if not APP_FILE.exists():
    print("Nao encontrei python/src/ytdlp_gui_downloader.py.")
    input("Pressione Enter para fechar...")
    raise SystemExit(1)

sys.path.insert(0, str(APP_FILE.parent))
runpy.run_path(str(APP_FILE), run_name="__main__")
