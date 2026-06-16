import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from tkinter import Tk, messagebox


APP_TITLE = "Baixador de Videos 3000 - Electron"
NODE_URL = "https://nodejs.org/"


def find_app_dir():
    if getattr(sys, "frozen", False):
        current = Path(sys.executable).resolve().parent
    else:
        current = Path(__file__).resolve().parent

    candidates = [
        current,
        current.parent,
        current.parent.parent if current.name.lower() == "release" else current.parent,
        Path.cwd(),
    ]
    for candidate in candidates:
        if (candidate / "electron" / "package.json").exists():
            return candidate
    return current


APP_DIR = find_app_dir()
ELECTRON_DIR = APP_DIR / "electron"


def setup_tk():
    root = Tk()
    root.withdraw()
    return root


ROOT = setup_tk()


def info(message):
    messagebox.showinfo(APP_TITLE, message, parent=ROOT)


def error(message):
    messagebox.showerror(APP_TITLE, message, parent=ROOT)


def ask(message):
    return messagebox.askyesno(APP_TITLE, message, parent=ROOT)


def add_path(path):
    if path and Path(path).exists():
        paths = os.environ.get("PATH", "").split(os.pathsep)
        if str(path) not in paths:
            os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")


def refresh_node_path():
    for scope in ("ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(scope)
        if base:
            add_path(Path(base) / "nodejs")


def command_exists(name):
    refresh_node_path()
    return shutil.which(name) is not None


def resolve_command(*names):
    refresh_node_path()
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def run_checked(command, cwd=None, action="comando"):
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        output = completed.stdout.strip()
        if len(output) > 1800:
            output = output[-1800:]
        raise RuntimeError(f"Falha ao executar {action}.\n\n{output}")


def ensure_node():
    if command_exists("node") and (resolve_command("npm.cmd", "npm") is not None):
        return

    if not ask(
        "A versao Electron precisa do Node.js LTS e do npm para abrir pelo codigo fonte.\n\n"
        "Nao encontrei Node.js/npm neste computador.\n\n"
        "Deseja que eu instale automaticamente agora?"
    ):
        raise RuntimeError("Node.js nao instalado. Instale o Node.js LTS e abra novamente.")

    if not command_exists("winget"):
        webbrowser.open(NODE_URL)
        raise RuntimeError(
            "Nao encontrei o winget para instalar automaticamente.\n\n"
            "Abri o site do Node.js para instalacao manual."
        )

    info("Vou instalar o Node.js LTS agora. Isso pode demorar alguns minutos.")
    run_checked(
        [
            "winget",
            "install",
            "--id",
            "OpenJS.NodeJS.LTS",
            "-e",
            "--source",
            "winget",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ],
        action="instalacao do Node.js",
    )
    refresh_node_path()
    if not (command_exists("node") and (resolve_command("npm.cmd", "npm") is not None)):
        info("Node.js foi instalado, mas o Windows ainda nao atualizou o PATH.\n\nFeche e abra este .exe novamente.")
        raise SystemExit(0)


def ensure_dependencies():
    electron_cmd = ELECTRON_DIR / "node_modules" / ".bin" / "electron.cmd"
    if electron_cmd.exists():
        return

    if not ask(
        "As dependencias da versao Electron ainda nao estao instaladas nesta pasta.\n\n"
        "Deseja instalar agora com npm install?"
    ):
        raise RuntimeError("Dependencias Electron nao instaladas.")

    info("Vou instalar as dependencias Electron agora. Isso pode demorar alguns minutos.")
    npm_cmd = resolve_command("npm.cmd", "npm")
    if not npm_cmd:
        raise RuntimeError("Encontrei o Node.js, mas nao consegui localizar o npm.")
    run_checked([npm_cmd, "install"], cwd=ELECTRON_DIR, action="npm install")


def source_is_newer_than_build():
    main_build = ELECTRON_DIR / "dist" / "main" / "main.js"
    renderer_build = ELECTRON_DIR / "dist" / "renderer" / "index.html"
    if not main_build.exists() or not renderer_build.exists():
        return True

    sources = []
    sources.extend((ELECTRON_DIR / "src").rglob("*"))
    sources.extend(
        [
            ELECTRON_DIR / "package.json",
            ELECTRON_DIR / "vite.config.ts",
            ELECTRON_DIR / "tsconfig.json",
            ELECTRON_DIR / "tsconfig.main.json",
        ]
    )
    newest_source = max(path.stat().st_mtime for path in sources if path.is_file())
    oldest_build = min(main_build.stat().st_mtime, renderer_build.stat().st_mtime)
    return newest_source > oldest_build


def ensure_build():
    if not source_is_newer_than_build():
        return
    info("Vou preparar a versao Electron local agora.")
    npm_cmd = resolve_command("npm.cmd", "npm")
    if not npm_cmd:
        raise RuntimeError("Encontrei o Node.js, mas nao consegui localizar o npm.")
    run_checked([npm_cmd, "run", "build"], cwd=ELECTRON_DIR, action="npm run build")


def launch_electron():
    electron_cmd = ELECTRON_DIR / "node_modules" / ".bin" / "electron.cmd"
    subprocess.Popen([str(electron_cmd), "."], cwd=str(ELECTRON_DIR), env=os.environ.copy())


def main():
    if not ELECTRON_DIR.exists():
        raise RuntimeError(f"Nao encontrei a pasta Electron em:\n{ELECTRON_DIR}")

    ensure_node()
    ensure_dependencies()
    ensure_build()
    launch_electron()


try:
    main()
except SystemExit:
    raise
except Exception as exc:
    error(str(exc))
    raise SystemExit(1)
finally:
    try:
        ROOT.destroy()
    except Exception:
        pass
