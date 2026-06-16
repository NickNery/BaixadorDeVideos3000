import os
import shutil
import subprocess
import sys
import time
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
LOG_FILE = APP_DIR / "BaixadorDeVideos3000_Electron.log"
WINDOWS_CREATION_FLAGS = (
    subprocess.CREATE_NO_WINDOW
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
    else 0
)


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


def resolve_node_command():
    return resolve_command("node.exe", "node")


def resolve_npm_cli():
    node_cmd = resolve_node_command()
    if not node_cmd:
        return None

    node_path = Path(node_cmd).resolve()
    candidates = [
        node_path.parent / "node_modules" / "npm" / "bin" / "npm-cli.js",
        node_path.parent.parent / "node_modules" / "npm" / "bin" / "npm-cli.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_electron_cli():
    candidates = [
        ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe",
        ELECTRON_DIR / "node_modules" / "electron" / "cli.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def electron_runtime_ready():
    if os.name == "nt":
        return (ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe").exists()
    return resolve_electron_cli() is not None


def append_log(message):
    try:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(message.rstrip() + "\n")
    except Exception:
        pass


def read_recent_log(limit=1800):
    try:
        text = LOG_FILE.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""
    if len(text) > limit:
        return text[-limit:]
    return text


def run_checked(command, cwd=None, action="comando"):
    append_log(f"\n[{action}] {' '.join(str(part) for part in command)}")
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=WINDOWS_CREATION_FLAGS,
    )
    if completed.stdout:
        append_log(completed.stdout)
    if completed.returncode != 0:
        output = completed.stdout.strip()
        if len(output) > 1800:
            output = output[-1800:]
        raise RuntimeError(f"Falha ao executar {action}.\n\n{output}")


def ensure_node():
    if command_exists("node") and (resolve_npm_cli() is not None):
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
    if not (command_exists("node") and (resolve_npm_cli() is not None)):
        info("Node.js foi instalado, mas o Windows ainda nao atualizou o PATH.\n\nFeche e abra este .exe novamente.")
        raise SystemExit(0)


def ensure_dependencies():
    if electron_runtime_ready():
        return

    has_node_modules = (ELECTRON_DIR / "node_modules").exists()
    prompt = (
        "A instalacao do Electron parece incompleta nesta pasta.\n\n"
        "Deseja reparar agora com npm install?"
        if has_node_modules
        else "As dependencias da versao Electron ainda nao estao instaladas nesta pasta.\n\n"
        "Deseja instalar agora com npm install?"
    )
    if not ask(
        prompt
    ):
        raise RuntimeError("Dependencias Electron nao instaladas.")

    info("Vou instalar as dependencias Electron agora. Isso pode demorar alguns minutos.")
    node_cmd = resolve_node_command()
    npm_cli = resolve_npm_cli()
    if not node_cmd or not npm_cli:
        raise RuntimeError("Encontrei o Node.js, mas nao consegui localizar os arquivos do npm.")
    run_checked([node_cmd, str(npm_cli), "install"], cwd=ELECTRON_DIR, action="npm install")

    install_js = ELECTRON_DIR / "node_modules" / "electron" / "install.js"
    if not electron_runtime_ready() and install_js.exists():
        run_checked([node_cmd, str(install_js)], cwd=ELECTRON_DIR, action="reparo do Electron")

    if not electron_runtime_ready():
        raise RuntimeError(
            "As dependencias foram instaladas, mas o electron.exe nao apareceu.\n\n"
            "Isso normalmente acontece quando o download do Electron foi bloqueado ou interrompido.\n"
            f"Confira o log em:\n{LOG_FILE}"
        )


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
    node_cmd = resolve_node_command()
    npm_cli = resolve_npm_cli()
    if not node_cmd or not npm_cli:
        raise RuntimeError("Encontrei o Node.js, mas nao consegui localizar os arquivos do npm.")
    run_checked([node_cmd, str(npm_cli), "run", "build"], cwd=ELECTRON_DIR, action="npm run build")


def launch_electron():
    node_cmd = resolve_node_command()
    electron_cli = resolve_electron_cli()
    if not node_cmd or not electron_cli:
        raise RuntimeError("Nao consegui localizar os arquivos do Electron depois da instalacao.")

    append_log(f"\n[abrir electron] app_dir={APP_DIR}")
    append_log(f"[abrir electron] electron_dir={ELECTRON_DIR}")
    append_log(f"[abrir electron] electron={electron_cli}")

    log_handle = LOG_FILE.open("a", encoding="utf-8", errors="replace")
    if electron_cli.suffix.lower() == ".exe":
        command = [str(electron_cli), "."]
    else:
        command = [node_cmd, str(electron_cli), "."]

    process = subprocess.Popen(
        command,
        cwd=str(ELECTRON_DIR),
        env=os.environ.copy(),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=WINDOWS_CREATION_FLAGS,
    )
    log_handle.close()
    time.sleep(2)
    if process.poll() is not None and process.returncode != 0:
        output = read_recent_log()
        raise RuntimeError(
            "O Electron tentou abrir, mas fechou logo em seguida.\n\n"
            f"Log salvo em:\n{LOG_FILE}\n\n"
            f"{output}"
        )


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
