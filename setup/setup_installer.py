import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import BooleanVar, Text, Tk, messagebox
from tkinter import DoubleVar, StringVar
from tkinter import ttk


APP_TITLE = "Setup - Baixador de Videos 3000"
NODE_URL = "https://nodejs.org/"
ELECTRON_VERSION = "39.8.10"


def base_dir():
    if getattr(sys, "frozen", False):
        setup_dir = Path(sys.executable).resolve().parent
    else:
        setup_dir = Path(__file__).resolve().parent
    return setup_dir.parent


ROOT_DIR = base_dir()
BIN_DIR = ROOT_DIR / "Bin"
LAUNCHER_DIR = BIN_DIR / "launcher"
ELECTRON_DIR = BIN_DIR / "electron"
RELEASE_DIR = BIN_DIR / "release"
ASSETS_DIR = BIN_DIR / "assets"
PYTHON_REQUIREMENTS = BIN_DIR / "python" / "requirements.txt"
ICON_FILE = ASSETS_DIR / "favicon.ico"


def creation_flags():
    return subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0


def add_path_if_exists(path):
    if path and Path(path).exists():
        current = os.environ.get("PATH", "")
        values = current.split(os.pathsep)
        if str(path) not in values:
            os.environ["PATH"] = str(path) + os.pathsep + current


def refresh_path():
    if os.name != "nt":
        return
    machine_path = os.environ.get("Path", "")
    machine_env = os.environ.get("PATH", "")
    registry_machine = ""
    registry_user = ""
    try:
        registry_machine = os.popen(
            'powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable(\'Path\', \'Machine\')"'
        ).read().strip()
        registry_user = os.popen(
            'powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable(\'Path\', \'User\')"'
        ).read().strip()
    except Exception:
        pass
    add_path_if_exists(Path(os.environ.get("ProgramFiles", "")) / "nodejs")
    add_path_if_exists(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs")
    for value in (machine_path, machine_env, registry_machine, registry_user):
        if value:
            for item in value.split(os.pathsep):
                add_path_if_exists(item)


def resolve_command(*names):
    refresh_path()
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def resolve_node():
    return resolve_command("node.exe", "node")


def resolve_npm_cli():
    node = resolve_node()
    if not node:
        return None
    node_dir = Path(node).resolve().parent
    candidates = [
        node_dir / "node_modules" / "npm" / "bin" / "npm-cli.js",
        node_dir.parent / "node_modules" / "npm" / "bin" / "npm-cli.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def electron_runtime_ready():
    return any(path.exists() for path in electron_exe_candidates())


def electron_runtime_dir():
    base = (
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or os.environ.get("TEMP")
        or str(Path.home())
    )
    return Path(base) / "BaixadorDeVideos3000" / "ElectronRuntime" / ELECTRON_VERSION


def electron_exe_candidates():
    return [
        electron_runtime_dir() / "electron.exe",
        electron_runtime_dir() / "node_modules" / "electron" / "dist" / "electron.exe",
        ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe",
    ]


def electron_build_ready():
    main_build = ELECTRON_DIR / "dist" / "main" / "main.js"
    renderer_build = ELECTRON_DIR / "dist" / "renderer" / "index.html"
    return main_build.exists() and renderer_build.exists()


class InstallerApp:
    def __init__(self):
        self.root = Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("720x520")
        self.root.minsize(680, 480)
        self.root.configure(bg="#171717")

        self.python_shortcut = BooleanVar(value=True)
        self.electron_shortcut = BooleanVar(value=True)
        self.progress_value = DoubleVar(value=0)
        self.status_text = StringVar(value="Aguardando inicio da instalacao.")
        self.installing = False

        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#171717")
        style.configure("Panel.TFrame", background="#202020")
        style.configure("TLabel", background="#171717", foreground="#f7f7f7", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#171717", foreground="#ffffff", font=("Segoe UI", 18, "bold"))
        style.configure("Muted.TLabel", background="#171717", foreground="#b9b9b9", font=("Segoe UI", 10))
        style.configure("TCheckbutton", background="#171717", foreground="#f7f7f7", font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", "#171717")], foreground=[("active", "#ffffff")])
        style.configure("Accent.TButton", background="#0057ff", foreground="#ffffff", borderwidth=0, padding=(18, 10), font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#1f6bff")])
        style.configure("TButton", background="#2d2d2d", foreground="#ffffff", borderwidth=0, padding=(14, 9))

    def build_ui(self):
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Baixador de Videos 3000", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text="Este setup prepara as dependencias e cria os atalhos na area de trabalho.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(6, 22))

        options = ttk.Frame(main)
        options.pack(fill="x", pady=(0, 16))
        ttk.Checkbutton(options, text="Criar atalho da versao Python", variable=self.python_shortcut).pack(anchor="w", pady=4)
        ttk.Checkbutton(options, text="Criar atalho da versao Electron", variable=self.electron_shortcut).pack(anchor="w", pady=4)

        self.log_box = Text(
            main,
            height=11,
            bg="#101010",
            fg="#f2f2f2",
            insertbackground="#ffffff",
            relief="flat",
            padx=12,
            pady=12,
            font=("Consolas", 9),
        )
        self.log_box.pack(fill="both", expand=True)
        self.log("Pronto para instalar.")
        self.log(f"Pasta do programa: {ROOT_DIR}")

        progress_area = ttk.Frame(main)
        progress_area.pack(fill="x", pady=(14, 0))
        ttk.Label(progress_area, textvariable=self.status_text, style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        self.progress_bar = ttk.Progressbar(progress_area, variable=self.progress_value, maximum=100, mode="determinate")
        self.progress_bar.pack(fill="x")

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(16, 0))
        self.install_button = ttk.Button(actions, text="Instalar agora", style="Accent.TButton", command=self.start_install)
        self.install_button.pack(side="left")
        ttk.Button(actions, text="Fechar", command=self.root.destroy).pack(side="right")

    def log(self, text):
        self.log_box.insert("end", str(text).rstrip() + "\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def set_progress(self, value, status=None):
        self.progress_value.set(max(0, min(100, float(value))))
        if status:
            self.status_text.set(status)
            self.log(status)
        self.root.update_idletasks()

    def download_file(self, url, target, label, start=0, end=100):
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.set_progress(start, label)

        def hook(block_count, block_size, total_size):
            if total_size <= 0:
                return
            downloaded = min(block_count * block_size, total_size)
            fraction = downloaded / total_size
            self.progress_value.set(start + ((end - start) * fraction))
            self.status_text.set(f"{label} ({int(fraction * 100)}%)")
            self.root.update_idletasks()

        urllib.request.urlretrieve(url, target, hook)
        self.set_progress(end, f"{label} concluido.")

    def start_install(self):
        if self.installing:
            return
        self.installing = True
        self.install_button.configure(state="disabled")
        threading.Thread(target=self.install, daemon=True).start()

    def run(self, command, cwd=None, action="comando"):
        self.log(f"> {action}")
        env = os.environ.copy()
        completed = subprocess.run(
            [str(part) for part in command],
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags(),
        )
        if completed.stdout:
            for line in completed.stdout.splitlines()[-80:]:
                self.log(line)
        if completed.returncode != 0:
            raise RuntimeError(f"Falha ao executar {action}.")

    def run_npm(self, args, action):
        node = resolve_node()
        npm_cli = resolve_npm_cli()
        if not node or not npm_cli:
            raise RuntimeError("Nao consegui localizar Node.js/npm depois da verificacao.")

        node_dir = str(Path(node).resolve().parent)
        env = os.environ.copy()
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")

        self.log(f"> {action}")
        completed = subprocess.run(
            [node, str(npm_cli), *[str(arg) for arg in args]],
            cwd=str(electron_runtime_dir()),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags(),
        )
        if completed.stdout:
            for line in completed.stdout.splitlines()[-100:]:
                self.log(line)
        if completed.returncode != 0:
            raise RuntimeError(f"Falha ao executar {action}.")

    def run_node(self, args, cwd, action):
        node = resolve_node()
        if not node:
            raise RuntimeError("Nao consegui localizar Node.js depois da verificacao.")
        node_dir = str(Path(node).resolve().parent)
        env = os.environ.copy()
        env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
        self.run([node, *[str(arg) for arg in args]], cwd=cwd, action=action)

    def ensure_bin(self):
        self.set_progress(5, "Verificando pasta do programa...")
        if not BIN_DIR.exists():
            raise RuntimeError(f"Nao encontrei a pasta Bin em:\n{BIN_DIR}")
        if not ELECTRON_DIR.exists():
            raise RuntimeError(f"Nao encontrei a pasta Electron em:\n{ELECTRON_DIR}")
        self.set_progress(10, "Pasta Bin encontrada.")

    def ensure_node(self):
        if resolve_node() and resolve_npm_cli():
            self.set_progress(22, "Node.js e npm ja estao instalados.")
            self.log("Node.js e npm encontrados.")
            return

        winget = resolve_command("winget.exe", "winget")
        if not winget:
            webbrowser.open(NODE_URL)
            raise RuntimeError("Nao encontrei winget. Abri o site do Node.js para instalacao manual.")

        self.set_progress(18, "Instalando Node.js LTS...")
        self.run(
            [
                winget,
                "install",
                "--id",
                "OpenJS.NodeJS.LTS",
                "-e",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            action="instalacao do Node.js LTS",
        )
        refresh_path()
        if not (resolve_node() and resolve_npm_cli()):
            raise RuntimeError("Node.js foi instalado, mas ainda nao apareceu no PATH. Feche e abra este setup novamente.")
        self.set_progress(22, "Node.js e npm instalados.")

    def ensure_electron(self):
        self.ensure_node()

        if electron_runtime_ready():
            self.set_progress(68, "Electron ja esta instalado.")
        else:
            runtime_dir = electron_runtime_dir()
            runtime_dir.mkdir(parents=True, exist_ok=True)
            self.set_progress(52, "Instalando runtime Electron local...")
            self.run_npm(
                [
                    "install",
                    "--no-audit",
                    "--no-fund",
                    "--ignore-scripts=false",
                    "--foreground-scripts",
                    "--no-save",
                    f"electron@{ELECTRON_VERSION}",
                ],
                action="npm install electron",
            )

        install_js_candidates = [
            electron_runtime_dir() / "node_modules" / "electron" / "install.js",
            ELECTRON_DIR / "node_modules" / "electron" / "install.js",
        ]
        install_js = next((path for path in install_js_candidates if path.exists()), None)
        if not electron_runtime_ready() and install_js:
            self.set_progress(62, "Reparando runtime do Electron...")
            self.run_node([install_js], cwd=install_js.parent, action="reparo do Electron")

        if not electron_runtime_ready():
            raise RuntimeError("O Electron nao foi instalado corretamente.")

        if electron_build_ready():
            self.set_progress(78, "Build Electron ja esta pronto.")
        else:
            raise RuntimeError(
                "Nao encontrei o build da interface Electron em Bin\\electron\\dist.\n"
                "Atualize a pasta do programa e rode o setup novamente."
            )

    def ensure_media_tools(self):
        ytdlp = RELEASE_DIR / "yt-dlp.exe"
        if not ytdlp.exists() and not resolve_command("yt-dlp.exe", "yt-dlp"):
            self.download_file(
                "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
                ytdlp,
                "Baixando yt-dlp",
                start=12,
                end=18,
            )
        else:
            self.set_progress(18, "yt-dlp ja esta instalado.")

        if (RELEASE_DIR / "ffmpeg.exe").exists() or resolve_command("ffmpeg.exe", "ffmpeg"):
            self.set_progress(30, "ffmpeg ja esta instalado.")
            return

        winget = resolve_command("winget.exe", "winget")
        if not winget:
            self.log("Nao encontrei ffmpeg nem winget. O app ainda abre, mas conversao de audio pode falhar.")
            self.set_progress(30, "ffmpeg nao encontrado; etapa ignorada.")
            return

        self.set_progress(24, "Instalando ffmpeg...")
        self.run(
            [
                winget,
                "install",
                "--id",
                "Gyan.FFmpeg",
                "-e",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            action="instalacao do ffmpeg",
        )
        self.set_progress(30, "ffmpeg instalado.")

    def ensure_python_dependencies(self):
        python_app = RELEASE_DIR / "BaixadorDeVideos3000.exe"
        if python_app.exists():
            self.set_progress(42, "Executavel Python do app ja existe.")
            return

        python = resolve_command("python.exe", "python")
        if not python:
            winget = resolve_command("winget.exe", "winget")
            if not winget:
                raise RuntimeError("Nao encontrei Python nem winget para instalar automaticamente.")
            self.set_progress(34, "Instalando Python...")
            for package_id in ("Python.Python.3.14", "Python.Python.3.13", "Python.Python.3.12"):
                try:
                    self.run(
                        [
                            winget,
                            "install",
                            "--id",
                            package_id,
                            "-e",
                            "--source",
                            "winget",
                            "--accept-package-agreements",
                            "--accept-source-agreements",
                        ],
                        action=f"instalacao do {package_id}",
                    )
                    break
                except RuntimeError:
                    continue
            python = resolve_command("python.exe", "python")
            if not python:
                raise RuntimeError("Nao consegui instalar/localizar o Python.")
        else:
            self.set_progress(34, "Python ja esta instalado.")

        if PYTHON_REQUIREMENTS.exists():
            self.set_progress(38, "Verificando dependencias Python...")
            self.run([python, "-m", "pip", "install", "--upgrade", "pip"], action="atualizacao do pip")
            self.run([python, "-m", "pip", "install", "--upgrade", "-r", PYTHON_REQUIREMENTS], action="dependencias Python")
        self.set_progress(42, "Dependencias Python prontas.")

    def create_shortcut(self, name, target, description):
        desktop = Path(os.path.join(os.environ.get("USERPROFILE", str(Path.home())), "Desktop"))
        shortcut = desktop / f"{name}.lnk"
        icon = ICON_FILE if ICON_FILE.exists() else target
        ps = r"""
$shortcutPath = $args[0]
$targetPath = $args[1]
$workingDirectory = $args[2]
$iconPath = $args[3]
$description = $args[4]
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.IconLocation = $iconPath
$shortcut.Description = $description
$shortcut.Save()
"""
        self.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps,
                str(shortcut),
                str(target),
                str(BIN_DIR),
                str(icon),
                description,
            ],
            action=f"criacao do atalho {name}",
        )

    def create_shortcuts(self):
        self.set_progress(86, "Criando atalhos selecionados...")
        if self.python_shortcut.get():
            target = RELEASE_DIR / "BaixadorDeVideos3000.exe"
            if not target.exists():
                target = LAUNCHER_DIR / "BaixadorDeVideos3000.vbs"
            self.create_shortcut("Baixador de Videos 3000", target, "Baixador de Videos 3000")

        if self.electron_shortcut.get():
            target = LAUNCHER_DIR / "BaixadorDeVideos3000_Electron.exe"
            if not target.exists():
                target = LAUNCHER_DIR / "Abrir_Baixador_Electron.bat"
            self.create_shortcut("Baixador de Videos 3000 Electron", target, "Baixador de Videos 3000 Electron")
        self.set_progress(95, "Atalhos prontos.")

    def install(self):
        try:
            self.ensure_bin()
            self.ensure_media_tools()
            self.ensure_python_dependencies()
            self.ensure_electron()
            self.create_shortcuts()
            self.set_progress(100, "Instalacao concluida.")
            self.log("Instalacao concluida.")
            messagebox.showinfo(APP_TITLE, "Instalacao concluida com sucesso.")
        except Exception as exc:
            self.log(f"ERRO: {exc}")
            messagebox.showerror(APP_TITLE, str(exc))
        finally:
            self.installing = False
            self.install_button.configure(state="normal")

    def mainloop(self):
        self.root.mainloop()


if __name__ == "__main__":
    InstallerApp().mainloop()
