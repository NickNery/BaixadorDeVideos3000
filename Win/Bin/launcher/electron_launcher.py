import os
import platform
import json
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from tkinter import Tk, messagebox


APP_TITLE = "Baixador de Videos 3000 - Electron"
ELECTRON_VERSION = "39.8.10"


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
LOG_DIR = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or Path.home()) / "BaixadorDeVideos3000" / "Logs"
LOG_FILE = LOG_DIR / "BaixadorDeVideos3000_Electron.log"
WINDOWS_CREATION_FLAGS = (
    subprocess.CREATE_NO_WINDOW
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
    else 0
)


def safe_working_dir():
    for value in (os.environ.get("TEMP"), os.environ.get("USERPROFILE"), os.environ.get("SystemRoot")):
        if value and Path(value).exists():
            return value
    return "C:\\Windows" if os.name == "nt" else str(Path.home())


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
    local_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.environ.get("TEMP") or str(Path.home())
    local_runtime = Path(local_base) / "BaixadorDeVideos3000" / "ElectronRuntime" / ELECTRON_VERSION
    candidates = [
        local_runtime / "electron.exe",
        local_runtime / "node_modules" / "electron" / "dist" / "electron.exe",
        local_runtime / "node_modules" / "electron" / "cli.js",
        ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe",
        ELECTRON_DIR / "node_modules" / "electron" / "cli.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def electron_download_url():
    machine = platform.machine().lower()
    if "arm64" in machine or "aarch64" in machine:
        arch = "arm64"
    elif machine in {"x86", "i386", "i686"}:
        arch = "ia32"
    else:
        arch = "x64"
    return f"https://github.com/electron/electron/releases/download/v{ELECTRON_VERSION}/electron-v{ELECTRON_VERSION}-win32-{arch}.zip"


def electron_runtime_dir():
    local_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.environ.get("TEMP") or str(Path.home())
    return Path(local_base) / "BaixadorDeVideos3000" / "ElectronRuntime" / ELECTRON_VERSION


def electron_package_version():
    package_file = ELECTRON_DIR / "node_modules" / "electron" / "package.json"
    try:
        return json.loads(package_file.read_text(encoding="utf-8")).get("version") or "runtime"
    except Exception:
        return "runtime"


def prepare_local_electron_exe():
    if os.name != "nt":
        return None

    source_dist = ELECTRON_DIR / "node_modules" / "electron" / "dist"
    source_exe = source_dist / "electron.exe"
    if not source_exe.exists():
        return None

    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or str(Path.home())
    target_dist = Path(base) / "BaixadorDeVideos3000" / "ElectronRuntime" / electron_package_version()
    target_exe = target_dist / "electron.exe"

    if not target_exe.exists() or target_exe.stat().st_size != source_exe.stat().st_size:
        append_log(f"[runtime electron] Copiando runtime para {target_dist}")
        shutil.copytree(source_dist, target_dist, dirs_exist_ok=True)

    return target_exe


def electron_runtime_ready():
    if os.name == "nt":
        return resolve_electron_cli() is not None
    return resolve_electron_cli() is not None


def append_log(message):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
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
        raise RuntimeError(
            "Nao encontrei o winget para instalar automaticamente.\n\n"
            "Abra o setup principal do Baixador para reparar a instalacao."
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

    prompt = "O runtime Electron ainda nao esta preparado neste computador.\n\nDeseja instalar agora?"
    if not ask(
        prompt
    ):
        raise RuntimeError("Dependencias Electron nao instaladas.")

    info("Vou baixar o runtime Electron oficial agora. Isso pode demorar alguns minutos.")
    runtime_dir = electron_runtime_dir()
    runtime_parent = runtime_dir.parent
    runtime_zip = runtime_parent / f"electron-runtime-{ELECTRON_VERSION}-win32.zip"
    runtime_parent.mkdir(parents=True, exist_ok=True)
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir, ignore_errors=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    append_log(f"[electron runtime] Baixando {electron_download_url()}")
    urllib.request.urlretrieve(electron_download_url(), runtime_zip)
    append_log(f"[electron runtime] Extraindo para {runtime_dir}")
    with zipfile.ZipFile(runtime_zip) as archive:
        root = runtime_dir.resolve()
        for member in archive.infolist():
            target = (runtime_dir / member.filename).resolve()
            if not target.is_relative_to(root):
                raise RuntimeError("Arquivo invalido dentro do pacote Electron.")
            archive.extract(member, runtime_dir)
    try:
        runtime_zip.unlink(missing_ok=True)
    except Exception:
        pass

    if not electron_runtime_ready():
        raise RuntimeError(
            "O runtime Electron foi baixado, mas o electron.exe nao apareceu.\n\n"
            "Isso normalmente acontece quando o download do Electron foi bloqueado ou interrompido.\n"
            f"Confira o log em:\n{LOG_FILE}"
        )


def source_is_newer_than_build():
    main_build = ELECTRON_DIR / "dist" / "main" / "main.js"
    renderer_build = ELECTRON_DIR / "dist" / "renderer" / "index.html"
    return not (main_build.exists() and renderer_build.exists())


def ensure_build():
    if not source_is_newer_than_build():
        return
    raise RuntimeError(
        "Nao encontrei o build da interface Electron em Bin\\electron\\dist.\n\n"
        "Atualize a pasta do programa e rode o setup novamente."
    )


def launch_electron():
    electron_cli = resolve_electron_cli()
    if not electron_cli:
        raise RuntimeError("Nao consegui localizar os arquivos do Electron depois da instalacao.")

    local_electron_exe = prepare_local_electron_exe()
    if local_electron_exe:
        electron_cli = local_electron_exe

    append_log(f"\n[abrir electron] app_dir={APP_DIR}")
    append_log(f"[abrir electron] electron_dir={ELECTRON_DIR}")
    append_log(f"[abrir electron] electron={electron_cli}")

    log_handle = LOG_FILE.open("a", encoding="utf-8", errors="replace")
    if electron_cli.suffix.lower() == ".exe":
        command = [str(electron_cli), "--disable-gpu", str(ELECTRON_DIR)]
    else:
        node_cmd = resolve_node_command()
        if not node_cmd:
            raise RuntimeError("Nao consegui localizar Node.js para abrir o Electron por cli.js.")
        command = [node_cmd, str(electron_cli), "--disable-gpu", str(ELECTRON_DIR)]

    process = subprocess.Popen(
        command,
        cwd=safe_working_dir(),
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
