import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import BooleanVar, Text, Tk, messagebox
from tkinter import ttk


APP_TITLE = "Setup - Baixador de Videos 3000"
NODE_URL = "https://nodejs.org/"


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
    machine = os.environ.get("Path", "")
    add_path_if_exists(Path(os.environ.get("ProgramFiles", "")) / "nodejs")
    add_path_if_exists(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs")
    if machine:
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + machine


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


class InstallerApp:
    def __init__(self):
        self.root = Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("720x520")
        self.root.minsize(680, 480)
        self.root.configure(bg="#171717")

        self.python_shortcut = BooleanVar(value=True)
        self.electron_shortcut = BooleanVar(value=True)
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
            height=14,
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

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(16, 0))
        self.install_button = ttk.Button(actions, text="Instalar agora", style="Accent.TButton", command=self.start_install)
        self.install_button.pack(side="left")
        ttk.Button(actions, text="Fechar", command=self.root.destroy).pack(side="right")

    def log(self, text):
        self.log_box.insert("end", str(text).rstrip() + "\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def start_install(self):
        if self.installing:
            return
        self.installing = True
        self.install_button.configure(state="disabled")
        threading.Thread(target=self.install, daemon=True).start()

    def run(self, command, cwd=None, action="comando"):
        self.log(f"> {action}")
        completed = subprocess.run(
            [str(part) for part in command],
            cwd=str(cwd) if cwd else None,
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

    def ensure_bin(self):
        if not BIN_DIR.exists():
            raise RuntimeError(f"Nao encontrei a pasta Bin em:\n{BIN_DIR}")
        if not ELECTRON_DIR.exists():
            raise RuntimeError(f"Nao encontrei a pasta Electron em:\n{ELECTRON_DIR}")

    def ensure_node(self):
        if resolve_node() and resolve_npm_cli():
            self.log("Node.js e npm encontrados.")
            return

        winget = resolve_command("winget.exe", "winget")
        if not winget:
            webbrowser.open(NODE_URL)
            raise RuntimeError("Nao encontrei winget. Abri o site do Node.js para instalacao manual.")

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

    def ensure_electron(self):
        self.ensure_node()
        electron_exe = ELECTRON_DIR / "node_modules" / "electron" / "dist" / "electron.exe"
        node = resolve_node()
        npm_cli = resolve_npm_cli()
        if not node or not npm_cli:
            raise RuntimeError("Nao consegui localizar Node.js/npm depois da instalacao.")

        if not electron_exe.exists():
            self.run([node, npm_cli, "install"], cwd=ELECTRON_DIR, action="npm install")

        install_js = ELECTRON_DIR / "node_modules" / "electron" / "install.js"
        if not electron_exe.exists() and install_js.exists():
            self.run([node, install_js], cwd=ELECTRON_DIR, action="reparo do Electron")

        if not electron_exe.exists():
            raise RuntimeError("O Electron nao foi instalado corretamente.")

        self.run([node, npm_cli, "run", "build"], cwd=ELECTRON_DIR, action="npm run build")

    def ensure_media_tools(self):
        ytdlp = RELEASE_DIR / "yt-dlp.exe"
        if not ytdlp.exists() and not resolve_command("yt-dlp.exe", "yt-dlp"):
            self.log("Baixando yt-dlp...")
            RELEASE_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe", ytdlp)

        if (RELEASE_DIR / "ffmpeg.exe").exists() or resolve_command("ffmpeg.exe", "ffmpeg"):
            self.log("ffmpeg encontrado.")
            return

        winget = resolve_command("winget.exe", "winget")
        if not winget:
            self.log("Nao encontrei ffmpeg nem winget. O app ainda abre, mas conversao de audio pode falhar.")
            return

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

    def ensure_python_dependencies(self):
        python_app = RELEASE_DIR / "BaixadorDeVideos3000.exe"
        if python_app.exists():
            self.log("Executavel Python de release encontrado.")
            return

        python = resolve_command("python.exe", "python")
        if not python:
            winget = resolve_command("winget.exe", "winget")
            if not winget:
                raise RuntimeError("Nao encontrei Python nem winget para instalar automaticamente.")
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

        if PYTHON_REQUIREMENTS.exists():
            self.run([python, "-m", "pip", "install", "--upgrade", "pip"], action="atualizacao do pip")
            self.run([python, "-m", "pip", "install", "--upgrade", "-r", PYTHON_REQUIREMENTS], action="dependencias Python")

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

    def install(self):
        try:
            self.ensure_bin()
            self.ensure_media_tools()
            self.ensure_python_dependencies()
            self.ensure_electron()
            self.create_shortcuts()
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
