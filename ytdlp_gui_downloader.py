import json
import os
import platform
import queue
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from tkinter import (
    BooleanVar,
    Canvas,
    END,
    Label,
    Toplevel,
    StringVar,
    Text,
    Tk,
    PhotoImage,
    filedialog,
    messagebox,
)
from tkinter import ttk, colorchooser

try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False


APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "ytdlp_gui_config.json"
APP_VERSION = "1.2.8"


DEFAULT_CONFIG = {
    "title": "Gerenciador de Downloads Master",
    "yt_dlp_path": "yt-dlp.exe",
    "default_folder": str(Path.home() / "Downloads"),
    "background_color": "#101820",
    "panel_color": "#182430",
    "text_color": "#f4f7fb",
    "muted_text_color": "#a9b4c0",
    "button_color": "#1d9bf0",
    "button_text_color": "#ffffff",
    "entry_bg": "#ffffff",
    "entry_fg": "#101820",
    "background_image": "",
    "background_mode": "banner",
    "background_fit": "cover",
    "background_size": "100",
    "background_height": "170",
    "font_size": "10",
    "extra_args": "",
    "update_manifest_url": "",
}


FONT_REGULAR = "Montserrat"
FONT_MEDIUM = "Montserrat Medium"


def load_config():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
            return {**DEFAULT_CONFIG, **loaded}
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=2, ensure_ascii=False)


def find_yt_dlp(configured_path):
    if os.name == "nt":
        candidates = [
            configured_path,
            str(APP_DIR / "yt-dlp.exe"),
            str(APP_DIR / "yt-dlp"),
            shutil.which("yt-dlp.exe"),
            shutil.which("yt-dlp"),
        ]
    else:
        candidates = []
        if configured_path and not str(configured_path).lower().endswith(".exe"):
            candidates.append(configured_path)
        candidates.extend(
            [
                str(APP_DIR / "yt-dlp"),
                shutil.which("yt-dlp"),
            ]
        )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    if configured_path and configured_path not in {"yt-dlp.exe", "yt-dlp"} and not str(configured_path).lower().endswith(".exe"):
        return configured_path
    return "yt-dlp.exe" if os.name == "nt" else "yt-dlp"


def resolve_executable_path(value):
    value = (value or "").strip()
    if not value:
        return "yt-dlp.exe" if os.name == "nt" else "yt-dlp"

    path = Path(value)
    if path.is_absolute():
        return str(path)

    app_relative = APP_DIR / value
    if app_relative.exists():
        return str(app_relative)

    found = shutil.which(value)
    return found or value


def resolve_ytdlp_command(value):
    if os.name == "nt":
        return [resolve_executable_path(value)]

    value = (value or "").strip()
    if value and not value.lower().endswith(".exe"):
        path = Path(value)
        if path.is_absolute() and path.exists():
            return [str(path)]

        app_relative = APP_DIR / value
        if app_relative.exists():
            return [str(app_relative)]

        found = shutil.which(value)
        if found:
            return [found]

        if value not in {"yt-dlp", "yt-dlp.exe"}:
            return [value]

    app_ytdlp = APP_DIR / "yt-dlp"
    if app_ytdlp.exists():
        return [str(app_ytdlp)]

    found = shutil.which("yt-dlp")
    if found:
        return [found]

    return [sys.executable, "-m", "yt_dlp"]


def version_tuple(version):
    return tuple(int(part) for part in re.findall(r"\d+", str(version))[:4])


def sanitize_filename(name):
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name[:180].strip(" ._") or "video"


def clamp_int(value, default, minimum, maximum):
    try:
        number = int(str(value).strip())
    except ValueError:
        return default
    return min(max(number, minimum), maximum)


def resize_image_for_area(path, width, height, fit, scale_percent):
    if not PIL_AVAILABLE:
        return PhotoImage(file=path)

    width = max(int(width), 1)
    height = max(int(height), 1)
    scale = max(scale_percent, 10) / 100

    image = Image.open(path).convert("RGBA")
    source_w, source_h = image.size

    if fit == "stretch":
        target_w, target_h = width, height
    elif fit == "contain":
        ratio = min(width / source_w, height / source_h) * scale
        target_w, target_h = max(int(source_w * ratio), 1), max(int(source_h * ratio), 1)
    elif fit == "original":
        target_w, target_h = max(int(source_w * scale), 1), max(int(source_h * scale), 1)
    else:
        ratio = max(width / source_w, height / source_h) * scale
        target_w, target_h = max(int(source_w * ratio), 1), max(int(source_h * ratio), 1)

    resized = image.resize((target_w, target_h), Image.Resampling.LANCZOS)

    if fit == "cover" and (target_w > width or target_h > height):
        left = max((target_w - width) // 2, 0)
        top = max((target_h - height) // 2, 0)
        resized = resized.crop((left, top, left + width, top + height))

    if fit in {"contain", "original"}:
        background = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        left = max((width - resized.width) // 2, 0)
        top = max((height - resized.height) // 2, 0)
        background.alpha_composite(resized, (left, top))
        resized = background

    return ImageTk.PhotoImage(resized)


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, frame_style="Main.TFrame"):
        super().__init__(parent, style=frame_style)
        self.canvas = Canvas(self, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style=frame_style)

        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.resize_content_width)
        self.canvas.bind("<Enter>", self.bind_mousewheel)
        self.canvas.bind("<Leave>", self.unbind_mousewheel)

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def resize_content_width(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def set_colors(self, background_color):
        self.canvas.configure(bg=background_color)


UPDATER_SCRIPT = r'''
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main():
    temp_dir = Path(sys.argv[1])
    app_dir = Path(sys.argv[2])
    app_file = Path(sys.argv[3])
    python_exe = sys.executable

    time.sleep(1.5)

    for source in temp_dir.rglob("*"):
        if source.is_file():
            relative = source.relative_to(temp_dir)
            target = app_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    shutil.rmtree(temp_dir, ignore_errors=True)
    subprocess.Popen([python_exe, str(app_file)], cwd=str(app_dir))


if __name__ == "__main__":
    main()
'''


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.process = None
        self.output_queue = queue.Queue()
        self.background_photo = None
        self.root_background_photo = None
        self.background_resize_job = None
        self.active_toast = None
        self.last_process_lines = []
        self.current_process_kind = None
        self.download_watchdog_job = None
        self.last_output_time = None

        self.destino = StringVar(value=self.config["default_folder"])
        self.formato = StringVar(value="mp4")
        self.nome_modo = StringVar(value="original")
        self.nome_custom = StringVar()
        self.cookies_mode = StringVar(value="none")
        self.cookies_file = StringVar()
        self.yt_dlp_path = StringVar(value=find_yt_dlp(self.config["yt_dlp_path"]))
        self.extra_args = StringVar(value=self.config["extra_args"])
        self.update_manifest_url = StringVar(value=self.config["update_manifest_url"])
        self.keep_window_on_top = BooleanVar(value=False)
        self.status_text = StringVar(value="Pronto para baixar.")
        self.current_screen = "download"

        self.root.title(self.config["title"])
        self.root.geometry("1080x760")
        self.root.minsize(620, 460)
        self.root.configure(bg=self.config["background_color"])

        self.setup_styles()
        self.build_ui()
        self.apply_theme()
        self.load_background_image()
        self.root.after(100, self.drain_output_queue)
        self.root.bind("<Configure>", self.schedule_background_refresh)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def build_ui(self):
        self.root_bg_label = Label(self.root, bd=0)

        self.main = ttk.Frame(self.root, style="Main.TFrame", padding=18)
        self.main.pack(fill="both", expand=True)

        header = ttk.Frame(self.main, style="Main.TFrame")
        header.pack(fill="x", pady=(0, 14))

        title_stack = ttk.Frame(header, style="Main.TFrame")
        title_stack.pack(side="left", fill="x", expand=True)

        self.title_label = ttk.Label(
            title_stack,
            text=self.config["title"],
            style="Title.TLabel",
        )
        self.title_label.pack(anchor="w")
        ttk.Label(
            title_stack,
            text="Baixe videos e audios com yt-dlp, com visual personalizavel.",
            style="AppSubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        ttk.Checkbutton(
            header,
            text="Sempre no topo",
            variable=self.keep_window_on_top,
            command=lambda: self.root.attributes("-topmost", self.keep_window_on_top.get()),
            style="Main.TCheckbutton",
        ).pack(side="right")

        self.nav_frame = ttk.Frame(header, style="Main.TFrame")
        self.nav_frame.pack(side="right", padx=(0, 14))
        self.nav_download_button = ttk.Button(
            self.nav_frame,
            text="Home",
            command=lambda: self.show_screen("download"),
            style="ActiveNav.TButton",
        )
        self.nav_download_button.pack(side="left", padx=(0, 8))
        self.nav_customize_button = ttk.Button(
            self.nav_frame,
            text="Personalizar",
            command=lambda: self.show_screen("customize"),
            style="Nav.TButton",
        )
        self.nav_customize_button.pack(side="left")

        self.screen_area = ttk.Frame(self.main, style="Main.TFrame")
        self.screen_area.pack(fill="both", expand=True)

        self.download_tab = ttk.Frame(self.screen_area, style="Main.TFrame", padding=(0, 14, 0, 0))
        self.customize_tab = ttk.Frame(self.screen_area, style="Main.TFrame", padding=(0, 14, 0, 0))

        self.download_scroll = ScrollableFrame(self.download_tab)
        self.download_scroll.pack(fill="both", expand=True)
        self.download_content = self.download_scroll.content

        self.customize_scroll = ScrollableFrame(self.customize_tab)
        self.customize_scroll.pack(fill="both", expand=True)
        self.customize_content = self.customize_scroll.content

        self.background_banner = ttk.Label(self.download_content, style="Image.TLabel")

        self.body = ttk.Frame(self.download_content, style="Main.TFrame")
        self.body.pack(fill="both", expand=True)
        self.body.columnconfigure(0, weight=3)
        self.body.columnconfigure(1, weight=2)
        self.body.rowconfigure(0, weight=1)

        left = ttk.Frame(self.body, style="Panel.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)

        right = ttk.Frame(self.body, style="Panel.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.columnconfigure(0, weight=1)

        ttk.Label(left, text="Links", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            left,
            text="Cole um ou varios links, um por linha. Funciona com YouTube, Instagram e Twitter/X quando o yt-dlp conseguir extrair.",
            style="Hint.TLabel",
            wraplength=520,
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        self.url_text = Text(left, height=8, wrap="word", relief="flat", bd=0)
        self.url_text.grid(row=2, column=0, sticky="nsew", pady=(0, 14))

        ttk.Label(left, text="Pasta de destino", style="Section.TLabel").grid(row=3, column=0, sticky="w")
        destino_row = ttk.Frame(left, style="Panel.TFrame")
        destino_row.grid(row=4, column=0, sticky="ew", pady=(8, 8))
        destino_row.columnconfigure(0, weight=1)
        ttk.Entry(destino_row, textvariable=self.destino).grid(row=0, column=0, sticky="ew")
        ttk.Button(destino_row, text="Procurar", command=self.choose_folder, style="Accent.TButton").grid(row=0, column=1, padx=(8, 0))

        quick = ttk.Frame(left, style="Panel.TFrame")
        quick.grid(row=5, column=0, sticky="ew", pady=(0, 14))
        for label, folder in [
            ("Desktop", Path.home() / "Desktop"),
            ("Downloads", Path.home() / "Downloads"),
            ("Videos", Path.home() / "Videos"),
        ]:
            ttk.Button(
                quick,
                text=label,
                command=lambda p=folder: self.destino.set(str(p)),
            ).pack(side="left", padx=(0, 8))

        options_grid = ttk.Frame(left, style="Panel.TFrame")
        options_grid.grid(row=6, column=0, sticky="ew")
        options_grid.columnconfigure(0, weight=1)
        options_grid.columnconfigure(1, weight=1)

        format_box = ttk.LabelFrame(options_grid, text="Formato", style="Panel.TLabelframe", padding=12)
        format_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Radiobutton(format_box, text="Video MP4 - alta qualidade", value="mp4", variable=self.formato, style="Main.TRadiobutton").pack(anchor="w")
        ttk.Radiobutton(format_box, text="Audio MP3 - musicas", value="mp3", variable=self.formato, style="Main.TRadiobutton").pack(anchor="w", pady=(8, 0))

        name_box = ttk.LabelFrame(options_grid, text="Nome do arquivo", style="Panel.TLabelframe", padding=12)
        name_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Radiobutton(name_box, text="Manter nome original", value="original", variable=self.nome_modo, style="Main.TRadiobutton").pack(anchor="w")
        ttk.Radiobutton(name_box, text="Usar nome personalizado", value="custom", variable=self.nome_modo, style="Main.TRadiobutton").pack(anchor="w", pady=(8, 0))
        ttk.Entry(name_box, textvariable=self.nome_custom).pack(fill="x", pady=(10, 0))

        actions = ttk.Frame(left, style="Panel.TFrame")
        actions.grid(row=7, column=0, sticky="ew", pady=(14, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        self.download_button = ttk.Button(actions, text="Iniciar download", command=self.start_download, style="Accent.TButton")
        self.download_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.cancel_button = ttk.Button(actions, text="Cancelar", command=self.cancel_download, state="disabled")
        self.cancel_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.status_label = ttk.Label(
            left,
            textvariable=self.status_text,
            style="Status.TLabel",
            wraplength=520,
            justify="left",
        )
        self.status_label.grid(row=8, column=0, sticky="ew", pady=(14, 0))

        ttk.Label(right, text="Acesso e ferramentas", style="Section.TLabel").grid(row=0, column=0, sticky="w")

        cookies_box = ttk.LabelFrame(right, text="Cookies / login", style="Panel.TLabelframe", padding=12)
        cookies_box.grid(row=1, column=0, sticky="ew", pady=(8, 14))
        for text, value in [
            ("Nao usar cookies", "none"),
            ("Usar cookies do Chrome", "chrome"),
            ("Usar cookies do Edge", "edge"),
            ("Usar cookies do Firefox", "firefox"),
            ("Usar arquivo cookies.txt", "file"),
        ]:
            ttk.Radiobutton(cookies_box, text=text, value=value, variable=self.cookies_mode, style="Main.TRadiobutton").pack(anchor="w", pady=2)
        cookies_file_row = ttk.Frame(cookies_box, style="Panel.TFrame")
        cookies_file_row.pack(fill="x", pady=(8, 0))
        ttk.Entry(cookies_file_row, textvariable=self.cookies_file).pack(side="left", fill="x", expand=True)
        ttk.Button(cookies_file_row, text="Arquivo", command=self.choose_cookies_file).pack(side="left", padx=(8, 0))

        tool_box = ttk.LabelFrame(right, text="yt-dlp", style="Panel.TLabelframe", padding=12)
        tool_box.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        tool_box.columnconfigure(0, weight=1)
        ttk.Entry(tool_box, textvariable=self.yt_dlp_path).grid(row=0, column=0, sticky="ew")
        ttk.Button(tool_box, text="Selecionar", command=self.choose_ytdlp).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(tool_box, text="Atualizar yt-dlp", command=self.update_ytdlp, style="Accent.TButton").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(tool_box, text="URL de atualizacao do app", style="Hint.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 4))
        ttk.Entry(tool_box, textvariable=self.update_manifest_url).grid(row=3, column=0, sticky="ew")
        ttk.Button(tool_box, text="Verificar atualizacao", command=self.check_app_update).grid(row=3, column=1, padx=(8, 0))

        extra_box = ttk.LabelFrame(right, text="Argumentos extras", style="Panel.TLabelframe", padding=12)
        extra_box.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        ttk.Entry(extra_box, textvariable=self.extra_args).pack(fill="x")
        ttk.Label(
            extra_box,
            text='Exemplo: --write-thumbnail --embed-metadata',
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(6, 0))

        self.build_customization_tab()
        self.show_screen("download")
        self.status_text.set("Pronto. Cole o link, escolha as opcoes e clique em Iniciar download.")

    def apply_theme(self):
        cfg = self.config
        font_size = self.safe_font_size()
        self.root.configure(bg=cfg["background_color"])
        self.style.configure("Main.TFrame", background=cfg["background_color"])
        self.style.configure("Panel.TFrame", background=cfg["panel_color"], borderwidth=1, relief="solid")
        if hasattr(self, "download_scroll"):
            self.download_scroll.set_colors(cfg["background_color"])
        if hasattr(self, "customize_scroll"):
            self.customize_scroll.set_colors(cfg["background_color"])
        self.style.configure("Title.TLabel", background=cfg["background_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 22, "normal"))
        self.style.configure("AppSubtitle.TLabel", background=cfg["background_color"], foreground=cfg["muted_text_color"], font=(FONT_REGULAR, 10, "normal"))
        self.style.configure("Section.TLabel", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 11, "normal"))
        self.style.configure("Hint.TLabel", background=cfg["panel_color"], foreground=cfg["muted_text_color"], font=(FONT_REGULAR, 9, "normal"))
        self.style.configure("Status.TLabel", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 10, "normal"))
        self.style.configure("PreviewTitle.TLabel", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 14, "normal"))
        self.style.configure("PreviewText.TLabel", background=cfg["panel_color"], foreground=cfg["muted_text_color"], font=(FONT_REGULAR, font_size, "normal"))
        self.style.configure("Main.TCheckbutton", background=cfg["background_color"], foreground=cfg["text_color"])
        self.style.configure("Main.TRadiobutton", background=cfg["panel_color"], foreground=cfg["text_color"])
        self.style.configure("Panel.TLabelframe", background=cfg["panel_color"], foreground=cfg["text_color"])
        self.style.configure("Panel.TLabelframe.Label", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 10, "normal"))
        self.style.configure("Image.TLabel", background=cfg["background_color"])
        self.style.configure("TButton", padding=(11, 8), font=(FONT_REGULAR, 9, "normal"))
        self.style.configure("Accent.TButton", background=cfg["button_color"], foreground=cfg["button_text_color"], padding=(14, 9), font=(FONT_MEDIUM, 9, "normal"))
        self.style.map("Accent.TButton", background=[("active", cfg["button_color"])])
        self.style.configure("Nav.TButton", background=cfg["panel_color"], foreground=cfg["muted_text_color"], padding=(16, 8), font=(FONT_REGULAR, 10, "normal"))
        self.style.configure("ActiveNav.TButton", background=cfg["button_color"], foreground=cfg["button_text_color"], padding=(26, 13), font=(FONT_MEDIUM, 12, "normal"))
        self.style.map("Nav.TButton", background=[("active", cfg["panel_color"])])
        self.style.map("ActiveNav.TButton", background=[("active", cfg["button_color"])])
        self.style.configure("TEntry", fieldbackground=cfg["entry_bg"], foreground=cfg["entry_fg"], padding=6)

        for text_widget in [self.url_text]:
            text_widget.configure(
                bg=cfg["entry_bg"],
                fg=cfg["entry_fg"],
                insertbackground=cfg["entry_fg"],
                font=(FONT_REGULAR, font_size),
            )

        if hasattr(self, "theme_preview_title"):
            self.theme_preview_title.configure(text=self.config["title"])
        if hasattr(self, "image_preview"):
            self.image_preview.configure(bg=cfg["background_color"])
            self.update_image_preview()

    def open_theme_window(self):
        self.show_screen("customize")

    def show_screen(self, screen):
        self.download_tab.pack_forget()
        self.customize_tab.pack_forget()
        self.current_screen = screen

        if screen == "customize":
            self.customize_tab.pack(fill="both", expand=True)
            self.nav_download_button.configure(style="Nav.TButton")
            self.nav_customize_button.configure(style="ActiveNav.TButton")
        else:
            self.download_tab.pack(fill="both", expand=True)
            self.nav_download_button.configure(style="ActiveNav.TButton")
            self.nav_customize_button.configure(style="Nav.TButton")

        self.refresh_background_images()

    def build_customization_tab(self):
        parent = self.customize_content
        parent.columnconfigure(0, weight=3)
        parent.columnconfigure(1, weight=2)
        parent.rowconfigure(0, weight=1)

        settings = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        settings.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        settings.columnconfigure(1, weight=1)

        preview = ttk.Frame(parent, style="Panel.TFrame", padding=16)
        preview.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        preview.columnconfigure(0, weight=1)

        ttk.Label(settings, text="Personalizacao da interface", style="Section.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(
            settings,
            text="As alteracoes ficam salvas no arquivo ytdlp_gui_config.json e carregam automaticamente na proxima abertura.",
            style="Hint.TLabel",
            wraplength=520,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 14))

        self.theme_vars = {}
        self.color_swatches = {}
        fields = [
            ("Titulo do app", "title", "text"),
            ("Cor do fundo", "background_color", "color"),
            ("Cor dos paineis", "panel_color", "color"),
            ("Cor principal do texto", "text_color", "color"),
            ("Cor do texto secundario", "muted_text_color", "color"),
            ("Cor dos botoes", "button_color", "color"),
            ("Cor do texto dos botoes", "button_text_color", "color"),
            ("Fundo dos campos", "entry_bg", "color"),
            ("Texto dos campos", "entry_fg", "color"),
            ("Tamanho da fonte", "font_size", "text"),
            ("Imagem decorativa", "background_image", "image"),
            ("Modo da imagem", "background_mode", "combo:none,banner,full"),
            ("Encaixe da imagem", "background_fit", "combo:cover,contain,stretch,original"),
            ("Tamanho da imagem %", "background_size", "text"),
            ("Altura da faixa", "background_height", "text"),
        ]

        for index, (label, key, field_type) in enumerate(fields, start=2):
            ttk.Label(settings, text=label, style="Hint.TLabel").grid(row=index, column=0, sticky="w", pady=6)
            var = StringVar(value=self.config.get(key, ""))
            self.theme_vars[key] = var
            if field_type == "color":
                color_row = ttk.Frame(settings, style="Panel.TFrame")
                color_row.grid(row=index, column=1, sticky="ew", padx=8, pady=6)
                color_row.columnconfigure(1, weight=1)
                swatch = Canvas(color_row, width=34, height=24, highlightthickness=1, highlightbackground="#808080")
                swatch.grid(row=0, column=0, sticky="w", padx=(0, 8))
                entry = ttk.Entry(color_row, textvariable=var)
                entry.grid(row=0, column=1, sticky="ew")
                self.color_swatches[key] = swatch
                self.paint_swatch(key)
                swatch.bind("<Button-1>", lambda event, v=var, s=swatch: self.pick_color(v, s))
                ttk.Button(settings, text="Escolher", command=lambda v=var, s=swatch: self.pick_color(v, s)).grid(row=index, column=2, sticky="ew", pady=6)
            elif field_type == "image":
                ttk.Entry(settings, textvariable=var).grid(row=index, column=1, sticky="ew", padx=8, pady=6)
                ttk.Button(settings, text="Arquivo", command=lambda v=var: self.pick_image(v)).grid(row=index, column=2, sticky="ew", pady=6)
            elif field_type.startswith("combo:"):
                values = field_type.removeprefix("combo:").split(",")
                combo = ttk.Combobox(settings, textvariable=var, values=values, state="readonly")
                combo.grid(row=index, column=1, sticky="ew", padx=8, pady=6)
                ttk.Label(settings, text=" ", style="Hint.TLabel").grid(row=index, column=2, sticky="ew", pady=6)
            else:
                ttk.Entry(settings, textvariable=var).grid(row=index, column=1, sticky="ew", padx=8, pady=6)
                ttk.Label(settings, text=" ", style="Hint.TLabel").grid(row=index, column=2, sticky="ew", pady=6)

        for key, var in self.theme_vars.items():
            var.trace_add("write", lambda *_args, k=key: self.on_theme_var_changed(k))

        actions_row = ttk.Frame(settings, style="Panel.TFrame")
        actions_row.grid(row=len(fields) + 2, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        actions_row.columnconfigure(0, weight=1)
        actions_row.columnconfigure(1, weight=1)
        actions_row.columnconfigure(2, weight=1)
        ttk.Button(actions_row, text="Aplicar e salvar", command=self.apply_customization_from_tab, style="Accent.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions_row, text="Remover imagem", command=self.clear_background_image).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(actions_row, text="Restaurar padrao", command=self.reset_customization).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        ttk.Label(preview, text="Previa", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.theme_preview_title = ttk.Label(preview, text=self.config["title"], style="PreviewTitle.TLabel")
        self.theme_preview_title.grid(row=1, column=0, sticky="ew", pady=(16, 6))
        ttk.Label(
            preview,
            text="Aqui voce testa cores, titulo e imagem sem precisar editar o codigo.",
            style="PreviewText.TLabel",
            wraplength=320,
        ).grid(row=2, column=0, sticky="ew", pady=(0, 14))
        ttk.Entry(preview).grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(preview, text="Botao de exemplo", style="Accent.TButton").grid(row=4, column=0, sticky="ew")
        ttk.Label(preview, text="Imagem", style="Section.TLabel").grid(row=5, column=0, sticky="w", pady=(22, 8))
        self.image_preview = Canvas(preview, height=150, highlightthickness=0, bg=self.config["background_color"])
        self.image_preview.grid(row=6, column=0, sticky="ew")
        ttk.Label(
            preview,
            text="Modo full coloca a imagem por tras da janela inteira; os paineis continuam por cima para manter leitura.",
            style="PreviewText.TLabel",
            wraplength=320,
        ).grid(row=7, column=0, sticky="ew", pady=(10, 0))
        self.update_image_preview()

    def on_theme_var_changed(self, key):
        if key in self.color_swatches:
            self.paint_swatch(key)
        if key.startswith("background_"):
            self.update_image_preview()

    def safe_font_size(self):
        try:
            value = int(str(self.config.get("font_size", "10")).strip())
            return min(max(value, 8), 18)
        except ValueError:
            return 10

    def paint_swatch(self, key):
        swatch = self.color_swatches.get(key)
        if not swatch:
            return
        color = self.theme_vars.get(key, StringVar(value=self.config.get(key, "#000000"))).get()
        swatch.delete("all")
        try:
            swatch.create_rectangle(2, 2, 32, 22, fill=color or "#000000", outline="")
        except Exception:
            swatch.create_rectangle(2, 2, 32, 22, fill="#000000", outline="")

    def apply_customization_from_tab(self):
        color_keys = {
            "background_color",
            "panel_color",
            "text_color",
            "muted_text_color",
            "button_color",
            "button_text_color",
            "entry_bg",
            "entry_fg",
        }
        for key, var in self.theme_vars.items():
            value = var.get().strip()
            if key in color_keys:
                try:
                    self.root.winfo_rgb(value)
                except Exception:
                    self.show_toast(f"A cor '{value}' nao e valida.", "error")
                    return
            if key == "font_size":
                try:
                    value = str(min(max(int(value), 8), 18))
                except ValueError:
                    self.show_toast("Use um tamanho de fonte entre 8 e 18.", "error")
                    return
            if key == "background_mode" and value not in {"none", "banner", "full"}:
                value = "banner"
            if key == "background_fit" and value not in {"cover", "contain", "stretch", "original"}:
                value = "cover"
            if key == "background_size":
                value = str(clamp_int(value, 100, 10, 300))
            if key == "background_height":
                value = str(clamp_int(value, 170, 80, 420))
            self.config[key] = value

        self.title_label.configure(text=self.config["title"])
        self.root.title(self.config["title"])
        save_config(self.config)
        for key in self.color_swatches:
            self.paint_swatch(key)
        self.apply_theme()
        self.load_background_image()
        self.log("Personalizacao aplicada e salva.")
        self.show_screen("download")

    def clear_background_image(self):
        if hasattr(self, "theme_vars"):
            self.theme_vars["background_image"].set("")
        self.config["background_image"] = ""
        save_config(self.config)
        self.load_background_image()
        self.log("Imagem decorativa removida.")

    def reset_customization(self):
        if not messagebox.askyesno("Restaurar padrao", "Deseja restaurar as cores e o titulo padrao?"):
            return
        for key in [
            "title",
            "background_color",
            "panel_color",
            "text_color",
            "muted_text_color",
            "button_color",
            "button_text_color",
            "entry_bg",
            "entry_fg",
            "background_image",
            "background_mode",
            "background_fit",
            "background_size",
            "background_height",
            "font_size",
        ]:
            self.config[key] = DEFAULT_CONFIG[key]
            self.theme_vars[key].set(DEFAULT_CONFIG[key])
        self.apply_customization_from_tab()

    def pick_color(self, var, swatch=None):
        color = colorchooser.askcolor(initialcolor=var.get())[1]
        if color:
            var.set(color)
            if swatch:
                swatch.delete("all")
                swatch.create_rectangle(2, 2, 32, 22, fill=color, outline="")

    def pick_image(self, var):
        path = filedialog.askopenfilename(
            title="Escolher imagem de fundo",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"), ("Todos os arquivos", "*.*")],
        )
        if path:
            var.set(path)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.destino.get() or str(Path.home()))
        if folder:
            self.destino.set(folder)

    def choose_cookies_file(self):
        path = filedialog.askopenfilename(
            title="Escolher cookies.txt",
            filetypes=[("Cookies TXT", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.cookies_file.set(path)
            self.cookies_mode.set("file")

    def choose_ytdlp(self):
        path = filedialog.askopenfilename(
            title="Selecionar yt-dlp",
            filetypes=[("yt-dlp", ("yt-dlp.exe", "yt-dlp")), ("Executaveis", "*.exe"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.yt_dlp_path.set(path)

    def load_background_image(self):
        image_path = self.config.get("background_image", "").strip()
        mode = self.config.get("background_mode", "banner")

        self.background_banner.pack_forget()
        self.root_bg_label.place_forget()
        self.main.pack_configure(padx=0, pady=0)

        if not image_path or mode == "none":
            self.update_image_preview()
            return

        if not Path(image_path).exists():
            self.log("[AVISO] Imagem decorativa nao encontrada.")
            self.update_image_preview()
            self.background_banner.pack_forget()
            return

        try:
            if mode == "full":
                self.root_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.root_bg_label.lower()
                self.main.lift()
                self.main.pack_configure(padx=18, pady=14)
            else:
                self.background_banner.pack(fill="x", pady=(0, 14), before=self.body)
            self.refresh_background_images()
            self.update_image_preview()
        except Exception as exc:
            self.background_banner.pack_forget()
            self.root_bg_label.place_forget()
            self.log(f"[AVISO] Nao consegui carregar a imagem de fundo: {exc}")

    def schedule_background_refresh(self, event=None):
        if self.background_resize_job:
            self.root.after_cancel(self.background_resize_job)
        self.background_resize_job = self.root.after(160, self.refresh_background_images)

    def refresh_background_images(self):
        self.background_resize_job = None
        image_path = self.config.get("background_image", "").strip()
        mode = self.config.get("background_mode", "banner")
        if not image_path or mode == "none" or not Path(image_path).exists():
            return

        fit = self.config.get("background_fit", "cover")
        size = clamp_int(self.config.get("background_size", "100"), 100, 10, 300)

        try:
            if mode == "full":
                width = max(self.root.winfo_width(), 1)
                height = max(self.root.winfo_height(), 1)
                self.root_background_photo = resize_image_for_area(image_path, width, height, fit, size)
                self.root_bg_label.configure(image=self.root_background_photo)
            else:
                width = max(self.download_scroll.canvas.winfo_width(), 1)
                height = clamp_int(self.config.get("background_height", "170"), 170, 80, 420)
                self.background_photo = resize_image_for_area(image_path, width, height, fit, size)
                self.background_banner.configure(image=self.background_photo)
        except Exception as exc:
            self.log(f"[AVISO] Nao consegui redimensionar a imagem: {exc}")

    def update_image_preview(self):
        if not hasattr(self, "image_preview"):
            return

        self.image_preview.delete("all")
        image_path = self.theme_vars.get("background_image", StringVar(value=self.config.get("background_image", ""))).get().strip()
        mode = self.theme_vars.get("background_mode", StringVar(value=self.config.get("background_mode", "banner"))).get()
        fit = self.theme_vars.get("background_fit", StringVar(value=self.config.get("background_fit", "cover"))).get()
        size = clamp_int(self.theme_vars.get("background_size", StringVar(value=self.config.get("background_size", "100"))).get(), 100, 10, 300)

        self.image_preview.create_rectangle(0, 0, 900, 180, fill=self.config["background_color"], outline="")
        self.image_preview.create_text(
            12,
            14,
            text=f"Modo: {mode} | Encaixe: {fit} | Tamanho: {size}%",
            anchor="nw",
            fill=self.config["muted_text_color"],
            font=(FONT_REGULAR, 9, "normal"),
        )

        if not image_path:
            self.image_preview.create_text(
                12,
                76,
                text="Nenhuma imagem escolhida",
                anchor="w",
                fill=self.config["muted_text_color"],
                font=(FONT_REGULAR, 10, "normal"),
            )
            return

        if not Path(image_path).exists():
            self.image_preview.create_text(
                12,
                76,
                text="Arquivo de imagem nao encontrado",
                anchor="w",
                fill=self.config["muted_text_color"],
                font=(FONT_REGULAR, 10, "normal"),
            )
            return

        if not PIL_AVAILABLE:
            self.image_preview.create_text(
                12,
                76,
                text="Instale Pillow para ver previa e redimensionamento avancado.",
                anchor="w",
                fill=self.config["muted_text_color"],
                font=(FONT_REGULAR, 10, "normal"),
            )
            return

        try:
            preview_photo = resize_image_for_area(image_path, 320, 110, fit, size)
            self.image_preview_photo = preview_photo
            self.image_preview.create_image(160, 88, image=self.image_preview_photo)
        except Exception as exc:
            self.image_preview.create_text(
                12,
                76,
                text=f"Erro ao carregar previa: {exc}",
                anchor="w",
                fill=self.config["muted_text_color"],
                font=(FONT_REGULAR, 10, "normal"),
            )

    def urls(self):
        return [line.strip() for line in self.url_text.get("1.0", END).splitlines() if line.strip()]

    def build_command(self):
        urls = self.urls()
        destino = Path(self.destino.get()).expanduser()
        command = resolve_ytdlp_command(self.yt_dlp_path.get()) + [
            "--newline",
            "--progress",
            "--windows-filenames",
            "--socket-timeout",
            "20",
            "--retries",
            "3",
            "--fragment-retries",
            "3",
            "--no-playlist",
            "-P",
            str(destino),
        ]

        if self.formato.get() == "mp4":
            command += ["-f", "best[ext=mp4]/best", "--merge-output-format", "mp4"]
        else:
            command += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

        if self.nome_modo.get() == "custom":
            name = sanitize_filename(self.nome_custom.get())
            template = f"{name}.%(ext)s" if len(urls) == 1 else f"{name}_%(autonumber)03d.%(ext)s"
            command += ["-o", template]

        cookies_mode = self.cookies_mode.get()
        if cookies_mode in {"chrome", "edge", "firefox"}:
            command += ["--cookies-from-browser", cookies_mode]
        elif cookies_mode == "file" and self.cookies_file.get().strip():
            command += ["--cookies", self.cookies_file.get().strip()]

        if self.extra_args.get().strip():
            command += shlex.split(self.extra_args.get().strip(), posix=False)

        command += urls
        return command

    def validate(self):
        if not self.urls():
            self.status_text.set("Cole pelo menos um link para baixar.")
            self.show_toast("Cole pelo menos um link para baixar.", "error")
            return False
        if self.nome_modo.get() == "custom" and not self.nome_custom.get().strip():
            self.status_text.set("Digite um nome personalizado ou use o nome original.")
            self.show_toast("Digite um nome personalizado ou selecione o nome original.", "error")
            return False
        destino = Path(self.destino.get()).expanduser()
        try:
            destino.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.status_text.set("Nao consegui acessar a pasta de destino.")
            self.show_toast(f"Nao consegui criar/acessar a pasta: {destino}. {exc}", "error")
            return False
        if self.cookies_mode.get() == "file" and not Path(self.cookies_file.get()).exists():
            self.status_text.set("Selecione um arquivo cookies.txt valido.")
            self.show_toast("Selecione um arquivo cookies.txt valido.", "error")
            return False
        return True

    def start_download(self):
        if self.process:
            return
        if not self.validate():
            return

        self.config["yt_dlp_path"] = self.yt_dlp_path.get().strip()
        self.config["default_folder"] = self.destino.get().strip()
        self.config["extra_args"] = self.extra_args.get().strip()
        self.config["update_manifest_url"] = self.update_manifest_url.get().strip()
        save_config(self.config)
        self.last_process_lines = []
        self.current_process_kind = "download"
        self.last_output_time = time.time()

        command = self.build_command()
        self.status_text.set("Iniciando yt-dlp...")
        self.schedule_download_watchdog()
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")

        thread = threading.Thread(target=self.run_process, args=(command,), daemon=True)
        thread.start()

    def startupinfo_for_subprocess(self):
        if os.name != "nt":
            return None
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo

    def run_process(self, command):
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=self.startupinfo_for_subprocess(),
                cwd=str(APP_DIR),
            )
            for line in self.process.stdout:
                self.output_queue.put(line.rstrip())
            code = self.process.wait()
            if code == 0:
                self.output_queue.put({"type": "process_done", "code": code, "message": "[SUCESSO] Download concluido."})
            else:
                self.output_queue.put({"type": "process_done", "code": code, "message": f"[ERRO] O yt-dlp terminou com codigo {code}."})
        except FileNotFoundError:
            self.output_queue.put({"type": "process_done", "code": -1, "message": "[ERRO] yt-dlp nao encontrado. No Windows, selecione o yt-dlp.exe. No macOS, rode Instalar_Dependencias_macOS.command."})
        except Exception as exc:
            self.output_queue.put({"type": "process_done", "code": -1, "message": f"[ERRO] {exc}"})
        finally:
            self.process = None
            self.output_queue.put("__PROCESS_DONE__")

    def cancel_download(self):
        if self.process:
            self.process.terminate()
            self.cancel_download_watchdog()
            self.status_text.set("Cancelando download...")
            self.log("[INFO] Cancelando download...")

    def update_ytdlp(self):
        if self.process:
            return
        command = resolve_ytdlp_command(self.yt_dlp_path.get()) + ["-U"]
        self.log("Atualizando yt-dlp...")
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        threading.Thread(target=self.run_process, args=(command,), daemon=True).start()

    def check_app_update(self):
        manifest_url = self.update_manifest_url.get().strip()
        if not manifest_url:
            self.show_toast("Informe a URL do manifesto de atualizacao.", "error")
            return

        self.config["update_manifest_url"] = manifest_url
        save_config(self.config)
        self.show_toast("Verificando atualizacao do aplicativo...", "info")
        threading.Thread(target=self.fetch_update_manifest, args=(manifest_url,), daemon=True).start()

    def fetch_update_manifest(self, manifest_url):
        try:
            request = urllib.request.Request(manifest_url, headers={"User-Agent": f"YTDLP-GUI/{APP_VERSION}"})
            with urllib.request.urlopen(request, timeout=20) as response:
                data = response.read().decode("utf-8")
            manifest = json.loads(data)
            self.root.after(0, lambda: self.handle_update_manifest(manifest))
        except Exception as exc:
            self.root.after(0, lambda: self.show_toast(f"Nao consegui verificar atualizacao: {exc}", "error"))

    def handle_update_manifest(self, manifest):
        latest_version = str(manifest.get("version", "")).strip()
        files = manifest.get("files", [])
        if not latest_version or not files:
            self.show_toast("Manifesto de atualizacao invalido.", "error")
            return

        if version_tuple(latest_version) <= version_tuple(APP_VERSION):
            self.show_toast(f"Voce ja esta na versao mais recente ({APP_VERSION}).", "success")
            return

        notes = str(manifest.get("notes", "")).strip()
        message = f"Existe uma nova versao: {latest_version}\nVersao atual: {APP_VERSION}"
        if notes:
            message += f"\n\n{notes}"
        message += "\n\nDeseja atualizar agora?"

        if messagebox.askyesno("Atualizacao disponivel", message):
            self.show_toast("Baixando atualizacao...", "info")
            threading.Thread(target=self.download_and_apply_update, args=(manifest,), daemon=True).start()

    def download_and_apply_update(self, manifest):
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="ytdlp_gui_update_"))
            for item in manifest["files"]:
                url = item.get("url", "").strip()
                relative_path = item.get("path", "").strip().replace("\\", "/")
                if not url or not relative_path or relative_path.startswith("/") or ".." in Path(relative_path).parts:
                    raise ValueError("Arquivo invalido no manifesto.")

                target = temp_dir / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                request = urllib.request.Request(url, headers={"User-Agent": f"YTDLP-GUI/{APP_VERSION}"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    target.write_bytes(response.read())

            updater_path = APP_DIR / "_apply_update.py"
            updater_path.write_text(UPDATER_SCRIPT, encoding="utf-8")
            subprocess.Popen([sys.executable, str(updater_path), str(temp_dir), str(APP_DIR), str(Path(__file__).resolve())], cwd=str(APP_DIR))
            self.root.after(0, lambda: self.show_toast("Atualizacao baixada. Reiniciando...", "success", duration=1800))
            self.root.after(1900, self.root.destroy)
        except Exception as exc:
            self.root.after(0, lambda: self.show_toast(f"Falha na atualizacao: {exc}", "error"))

    def drain_output_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line == "__PROCESS_DONE__":
                    self.download_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.current_process_kind = None
                elif isinstance(line, dict) and line.get("type") == "process_done":
                    self.handle_process_done(line.get("code", -1), line.get("message", ""))
                elif isinstance(line, dict) and line.get("type") == "status":
                    self.handle_process_status(line.get("message", ""))
                else:
                    self.log(line)
        except queue.Empty:
            pass
        self.root.after(100, self.drain_output_queue)

    def handle_process_status(self, message):
        cleaned = self.clean_download_status(message)
        self.last_process_lines.append(cleaned)
        self.last_process_lines = self.last_process_lines[-30:]
        self.last_output_time = time.time()
        self.status_text.set(cleaned)

    def handle_process_done(self, code, message):
        self.cancel_download_watchdog()
        if code == 0:
            self.status_text.set("Download concluido com sucesso.")
            self.show_toast("Download concluido com sucesso.", "success", duration=5500)
            return

        clean_message = message.replace("[ERRO] ", "").strip()
        details = "\n".join([part for part in [clean_message, "\n".join(self.last_process_lines[-5:]).strip()] if part]).strip()
        if details:
            self.status_text.set("Download falhou. Veja o aviso vermelho.")
            self.show_toast(f"Download falhou.\n{details}", "error", duration=9000)
        else:
            self.status_text.set("Download falhou.")
            self.show_toast(message.replace("[ERRO] ", "") or "Download falhou.", "error", duration=9000)

    def log(self, message):
        if not message:
            return

        self.last_process_lines.append(message)
        self.last_process_lines = self.last_process_lines[-30:]
        self.last_output_time = time.time()

        lower = message.lower()
        if self.current_process_kind == "download":
            if any(token in lower for token in ["[youtube]", "[instagram]", "[twitter]", "[x]", "[download]", "[info]", "downloading", "extracting", "destination", "merging"]):
                cleaned = self.clean_download_status(message)
                self.status_text.set(cleaned)
                self.schedule_download_watchdog()
            return

        if "[sucesso]" in lower or "salva" in lower or "removida" in lower:
            self.show_toast(message.replace("[SUCESSO] ", ""), "success")
        elif "[erro]" in lower or "erro" in lower or "error" in lower or "nao consegui" in lower:
            self.show_toast(message.replace("[ERRO] ", ""), "error")
        elif "[aviso]" in lower:
            self.show_toast(message.replace("[AVISO] ", ""), "error")
        elif "[info]" in lower or "iniciando" in lower or "atualizando" in lower or "cancelando" in lower or "pronto" in lower:
            self.show_toast(message.replace("[INFO] ", ""), "info")

    def clean_download_status(self, message):
        message = re.sub(r"\s+", " ", message).strip()
        if len(message) > 170:
            return message[:167] + "..."
        return message

    def show_toast(self, message, kind="info", duration=4200):
        if kind == "info":
            self.status_text.set(message)
            return

        if self.active_toast and self.active_toast.winfo_exists():
            self.active_toast.destroy()

        colors = {
            "success": ("#16a34a", "#ffffff"),
            "error": ("#dc2626", "#ffffff"),
            "info": (self.config.get("button_color", "#2563eb"), self.config.get("button_text_color", "#ffffff")),
        }
        bg, fg = colors.get(kind, colors["info"])

        toast = Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=bg)

        label = Label(
            toast,
            text=message,
            bg=bg,
            fg=fg,
            padx=18,
            pady=12,
            justify="left",
            wraplength=360,
            font=(FONT_MEDIUM, 10, "normal"),
        )
        label.pack()

        self.root.update_idletasks()
        x = self.root.winfo_rootx() + 18
        y = self.root.winfo_rooty() + 18
        toast.geometry(f"+{x}+{y}")
        self.active_toast = toast
        toast.after(duration, lambda: toast.destroy() if toast.winfo_exists() else None)

    def schedule_download_watchdog(self):
        self.cancel_download_watchdog()
        self.download_watchdog_job = self.root.after(
            7000,
            self.on_download_watchdog,
        )

    def cancel_download_watchdog(self):
        if self.download_watchdog_job:
            self.root.after_cancel(self.download_watchdog_job)
            self.download_watchdog_job = None

    def on_download_watchdog(self):
        if self.current_process_kind != "download":
            return

        silent_for = time.time() - (self.last_output_time or time.time())
        if self.process and silent_for >= 30:
            try:
                self.process.terminate()
            except Exception:
                pass
            message = "O yt-dlp ficou sem resposta por 30 segundos. Tente outro link, use cookies/login ou verifique a internet."
            self.status_text.set(message)
            return

        message = "Ainda aguardando resposta do yt-dlp. Se demorar muito, o link pode exigir login/cookies ou estar bloqueado."
        self.status_text.set(message)
        self.schedule_download_watchdog()


def main():
    root = Tk()
    app = DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
