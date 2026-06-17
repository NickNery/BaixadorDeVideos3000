import json
import math
import os
import platform
import queue
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from pathlib import Path
from tkinter import (
    BooleanVar,
    Canvas,
    END,
    Frame,
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


if getattr(sys, "frozen", False):
    SOURCE_DIR = Path(sys.executable).resolve().parent
    APP_DIR = SOURCE_DIR
else:
    SOURCE_DIR = Path(__file__).resolve().parent
    APP_DIR = SOURCE_DIR.parent if SOURCE_DIR.name == "src" else SOURCE_DIR
    if APP_DIR.name == "python":
        APP_DIR = APP_DIR.parent
CONFIG_FILE = APP_DIR / "ytdlp_gui_config.json"
APP_VERSION = "1.6.7"
APP_USER_MODEL_ID = "EdgeSolutions.BaixadorDeVideos3000"
DEFAULT_UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/NickNery/BaixadorDeVideos3000/main/update_manifest.json"
UPDATE_CHECK_TIMEOUT_SECONDS = 25
DESIGN_SYSTEM_VERSION = "edge-solution-2026-06"
SSL_CERT_ERROR_HINT = "Erro de certificado SSL no macOS. Rode Instalar_Dependencias_macOS.command para atualizar certifi e depois abra o app de novo."
DOOM_DIR = APP_DIR / "doom"
FREEDOOM_VERSION = "0.13.0"
FREEDOOM_URL = f"https://github.com/freedoom/freedoom/releases/download/v{FREEDOOM_VERSION}/freedoom-{FREEDOOM_VERSION}.zip"
CHOCOLATE_DOOM_VERSION = "3.1.1"
CHOCOLATE_DOOM_WINDOWS_URL = (
    f"https://github.com/chocolate-doom/chocolate-doom/releases/download/"
    f"chocolate-doom-{CHOCOLATE_DOOM_VERSION}/chocolate-doom-{CHOCOLATE_DOOM_VERSION}-win64.zip"
)


def get_app_icon_path():
    for icon_path in (
        APP_DIR / "favicon.ico",
        APP_DIR / "assets" / "favicon.ico",
        SOURCE_DIR / "favicon.ico",
        SOURCE_DIR / "assets" / "favicon.ico",
    ):
        if icon_path.exists():
            return icon_path
    return None


def get_app_png_icon_path():
    for icon_path in (
        APP_DIR / "app_icon.png",
        APP_DIR / "assets" / "app_icon.png",
        SOURCE_DIR / "app_icon.png",
        SOURCE_DIR / "assets" / "app_icon.png",
    ):
        if icon_path.exists():
            return icon_path
    return None


def configure_windows_app_identity():
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


DEFAULT_CONFIG = {
    "design_system": DESIGN_SYSTEM_VERSION,
    "title": "Edge Solutions Downloader",
    "yt_dlp_path": "yt-dlp.exe",
    "default_folder": str(Path.home() / "Downloads"),
    "background_color": "#171717",
    "panel_color": "#1f1f1f",
    "text_color": "#f7f7f7",
    "muted_text_color": "#999999",
    "button_color": "#0000ff",
    "button_text_color": "#ffffff",
    "entry_bg": "#262626",
    "entry_fg": "#f7f7f7",
    "background_image": "",
    "background_mode": "none",
    "background_fit": "cover",
    "background_size": "100",
    "background_height": "170",
    "font_size": "10",
    "extra_args": "",
    "update_manifest_url": DEFAULT_UPDATE_MANIFEST_URL,
}


THEME_CONFIG_KEYS = [
    "design_system",
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
]


FONT_REGULAR = "Poppins"
FONT_MEDIUM = "Poppins SemiBold"
EDGE_BORDER = "#383838"
EDGE_MUTED_SURFACE = "#2e2e2e"
EDGE_BLUE_LIGHT = "#3333ff"


def load_config():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
            config = {**DEFAULT_CONFIG, **loaded}
            if loaded.get("design_system") != DESIGN_SYSTEM_VERSION:
                for key in THEME_CONFIG_KEYS:
                    config[key] = DEFAULT_CONFIG[key]
            return config
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
            str(APP_DIR / "release" / "yt-dlp.exe"),
            str(APP_DIR / "yt-dlp"),
            str(APP_DIR / "release" / "yt-dlp"),
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
                str(APP_DIR / "release" / "yt-dlp"),
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

    release_relative = APP_DIR / "release" / value
    if release_relative.exists():
        return str(release_relative)

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

    release_ytdlp = APP_DIR / "release" / "yt-dlp"
    if release_ytdlp.exists():
        return [str(release_ytdlp)]

    found = shutil.which("yt-dlp")
    if found:
        return [found]

    return [sys.executable, "-m", "yt_dlp"]


def bundled_ffmpeg_location():
    names = ["ffmpeg.exe"] if os.name == "nt" else ["ffmpeg"]
    for name in names:
        for folder in (APP_DIR, APP_DIR / "release"):
            path = folder / name
            if path.exists():
                return str(folder)
    return ""


def running_frozen():
    return bool(getattr(sys, "frozen", False))


def find_certifi_bundle():
    certifi_modules = ("certifi", "pip._vendor.certifi")
    for module_name in certifi_modules:
        try:
            module = __import__(module_name, fromlist=["where"])
            bundle = Path(module.where())
            if bundle.exists():
                return str(bundle)
        except Exception:
            pass

    return ""


def ssl_context_with_certifi():
    certifi_bundle = find_certifi_bundle()
    if certifi_bundle:
        try:
            return ssl.create_default_context(cafile=certifi_bundle)
        except Exception:
            pass
    return ssl.create_default_context()


def urlopen_with_certifi(request, timeout):
    url = getattr(request, "full_url", str(request))
    if str(url).lower().startswith("https://"):
        return urllib.request.urlopen(request, timeout=timeout, context=ssl_context_with_certifi())
    return urllib.request.urlopen(request, timeout=timeout)


def subprocess_environment():
    env = os.environ.copy()
    certifi_bundle = find_certifi_bundle()
    if certifi_bundle:
        env["SSL_CERT_FILE"] = certifi_bundle
        env["REQUESTS_CA_BUNDLE"] = certifi_bundle
        env["CURL_CA_BUNDLE"] = certifi_bundle
    return env


def version_tuple(version):
    return tuple(int(part) for part in re.findall(r"\d+", str(version))[:4])


def cache_busted_url(url):
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("_", str(int(time.time() * 1000))))
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))


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
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Edge.Vertical.TScrollbar")
        self.content = ttk.Frame(self.canvas, style=frame_style)

        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y", padx=(8, 0))

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


class SelectionPill(Frame):
    def __init__(self, parent, text, variable, value=None, mode="radio", command=None):
        super().__init__(parent, bd=0, highlightthickness=0, padx=1, pady=1, cursor="hand2")
        self.text = text
        self.variable = variable
        self.value = value
        self.mode = mode
        self.command = command
        self.hovered = False
        self.config_ref = DEFAULT_CONFIG.copy()

        self.inner = Frame(self, bd=0, highlightthickness=0, cursor="hand2")
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)
        self.indicator = Canvas(self.inner, width=16, height=16, highlightthickness=0, bd=0, cursor="hand2")
        self.indicator.pack(side="left", padx=(11, 8), pady=9)
        self.label = Label(self.inner, text=text, bd=0, anchor="w", cursor="hand2")
        self.label.pack(side="left", fill="x", expand=True, padx=(0, 11), pady=9)

        for widget in (self, self.inner, self.indicator, self.label):
            widget.bind("<Button-1>", self.activate)
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)

        self.variable.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    def is_selected(self):
        if self.mode == "check":
            return bool(self.variable.get())
        return self.variable.get() == self.value

    def activate(self, event=None):
        if self.mode == "check":
            self.variable.set(not bool(self.variable.get()))
        else:
            self.variable.set(self.value)
        if self.command:
            self.command()

    def on_enter(self, event=None):
        self.hovered = True
        self.refresh()

    def on_leave(self, event=None):
        self.hovered = False
        self.refresh()

    def set_theme(self, config):
        self.config_ref = config
        self.refresh()

    def refresh(self):
        cfg = self.config_ref
        selected = self.is_selected()
        border = cfg["button_color"] if selected else ("#4a4a4a" if self.hovered else EDGE_BORDER)
        surface = "#151535" if selected else ("#363636" if self.hovered else EDGE_MUTED_SURFACE)
        fg = cfg["button_text_color"] if selected else cfg["text_color"]
        indicator_fill = cfg["button_color"] if selected else surface

        self.configure(bg=border)
        self.inner.configure(bg=surface)
        self.indicator.configure(bg=surface)
        self.label.configure(bg=surface, fg=fg, font=(FONT_MEDIUM if selected else FONT_REGULAR, 9, "normal"))

        self.indicator.delete("all")
        if self.mode == "check":
            self.indicator.create_rectangle(2, 2, 14, 14, outline=border, width=2, fill=indicator_fill)
            if selected:
                self.indicator.create_line(4, 8, 7, 11, 13, 4, fill="#ffffff", width=2)
        else:
            self.indicator.create_oval(2, 2, 14, 14, outline=border, width=2, fill=indicator_fill)
            if selected:
                self.indicator.create_oval(6, 6, 10, 10, outline="#ffffff", fill="#ffffff")


class DoomE1M1Window:
    MAP = [
        "111111111111111111111111",
        "100000000100000000000001",
        "100111000100011111110001",
        "100101000000010000010001",
        "100101111110010111010001",
        "100100000010010101010001",
        "100111101010000101000001",
        "100000101011110101111101",
        "111110101000010100000101",
        "100000101111010111110101",
        "100111100000010000010101",
        "100100001111011110010101",
        "100101111001000010010001",
        "100100000001111010111101",
        "100111111100000010000001",
        "100000000111011111110001",
        "101111110100010000000001",
        "100000010100010111111101",
        "1001100100000001000000X1",
        "100100011111110101111111",
        "100000000000000100000001",
        "111111111111111111111111",
    ]

    def __init__(self, master):
        self.window = Toplevel(master)
        self.window.title("DOOM 1993 - E1M1")
        self.window.geometry("960x620")
        self.window.minsize(720, 460)
        self.window.configure(bg="#050505")
        self.canvas = Canvas(self.window, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.keys = set()
        self.player = {"x": 2.5, "y": 2.5, "a": 0.0, "hp": 100.0, "ammo": 50, "score": 0}
        self.enemy_starts = [(7.4, 3.5), (14.5, 5.5), (19.5, 7.5), (7.5, 13.5), (16.5, 15.5), (20.5, 18.5)]
        self.enemies = [{"x": x, "y": y, "hp": 30, "alive": True} for x, y in self.enemy_starts]
        self.running = True
        self.flash = 0.0
        self.bob = 0.0
        self.won = False
        self.game_over = False
        self.last_time = time.perf_counter()

        self.window.bind("<KeyPress>", self.on_key_press)
        self.window.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_shoot)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.after(100, self.focus)
        self.tick()

    def focus(self):
        try:
            self.window.focus_force()
            self.canvas.focus_set()
        except Exception:
            pass

    def close(self):
        self.running = False
        self.window.destroy()

    def on_key_press(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key == "r" and (self.won or self.game_over):
            self.reset()

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def on_shoot(self, event=None):
        if self.won or self.game_over or self.player["ammo"] <= 0:
            return
        self.player["ammo"] -= 1
        self.flash = 0.14
        best_enemy = None
        best_diff = 0.16
        for enemy in self.enemies:
            if not enemy["alive"]:
                continue
            dx = enemy["x"] - self.player["x"]
            dy = enemy["y"] - self.player["y"]
            distance = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            diff = abs(math.atan2(math.sin(angle - self.player["a"]), math.cos(angle - self.player["a"])))
            if diff < best_diff and distance < 9 and self.line_clear(enemy["x"], enemy["y"]):
                best_enemy = enemy
                best_diff = diff
        if best_enemy:
            best_enemy["hp"] -= 34
            if best_enemy["hp"] <= 0:
                best_enemy["alive"] = False
                self.player["score"] += 100

    def reset(self):
        self.player.update({"x": 2.5, "y": 2.5, "a": 0.0, "hp": 100.0, "ammo": 50, "score": 0})
        for enemy, (x, y) in zip(self.enemies, self.enemy_starts):
            enemy["x"] = x
            enemy["y"] = y
            enemy["alive"] = True
            enemy["hp"] = 30
        self.won = False
        self.game_over = False

    def tile(self, x, y):
        ix = int(x)
        iy = int(y)
        if iy < 0 or iy >= len(self.MAP) or ix < 0 or ix >= len(self.MAP[0]):
            return "1"
        return self.MAP[iy][ix]

    def is_solid(self, x, y):
        return self.tile(x, y) == "1"

    def move(self, dx, dy):
        nx = self.player["x"] + dx
        ny = self.player["y"] + dy
        if not self.is_solid(nx, self.player["y"]):
            self.player["x"] = nx
        if not self.is_solid(self.player["x"], ny):
            self.player["y"] = ny

    def line_clear(self, target_x, target_y):
        dx = target_x - self.player["x"]
        dy = target_y - self.player["y"]
        distance = max(math.hypot(dx, dy), 0.01)
        steps = max(4, int(distance / 0.08))
        for step in range(1, steps):
            x = self.player["x"] + dx * (step / steps)
            y = self.player["y"] + dy * (step / steps)
            if self.is_solid(x, y):
                return False
        return True

    def cast_ray(self, angle):
        distance = 0.02
        step = 0.035
        ray_x = math.cos(angle)
        ray_y = math.sin(angle)
        hit = "1"
        shade = 1.0
        while distance < 24:
            x = self.player["x"] + ray_x * distance
            y = self.player["y"] + ray_y * distance
            hit = self.tile(x, y)
            if hit != "0":
                rx = abs(x - math.floor(x) - 0.5)
                ry = abs(y - math.floor(y) - 0.5)
                shade = 0.78 if rx > ry else 1.0
                break
            distance += step
        return distance, hit, shade

    def update(self, dt):
        if self.won or self.game_over:
            return
        speed = 2.8
        turn_speed = 2.4
        forward = 0
        if "w" in self.keys:
            forward += 1
        if "s" in self.keys:
            forward -= 1
        if "a" in self.keys:
            self.player["a"] -= turn_speed * dt
        if "d" in self.keys:
            self.player["a"] += turn_speed * dt
        if forward:
            self.move(math.cos(self.player["a"]) * forward * speed * dt, math.sin(self.player["a"]) * forward * speed * dt)
            self.bob += dt * 9
        self.flash = max(0, self.flash - dt)

        for enemy in self.enemies:
            if not enemy["alive"]:
                continue
            dx = self.player["x"] - enemy["x"]
            dy = self.player["y"] - enemy["y"]
            distance = math.hypot(dx, dy)
            if distance < 7 and self.line_clear(enemy["x"], enemy["y"]):
                enemy_dx = (dx / max(distance, 0.01)) * dt * 0.65
                enemy_dy = (dy / max(distance, 0.01)) * dt * 0.65
                if not self.is_solid(enemy["x"] + enemy_dx, enemy["y"]):
                    enemy["x"] += enemy_dx
                if not self.is_solid(enemy["x"], enemy["y"] + enemy_dy):
                    enemy["y"] += enemy_dy
            if distance < 0.7:
                self.player["hp"] -= 18 * dt
                if self.player["hp"] <= 0:
                    self.player["hp"] = 0
                    self.game_over = True

        if self.tile(self.player["x"], self.player["y"]) == "X":
            self.won = True

    def draw(self):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        hud_height = 86
        view_height = max(height - hud_height, 1)
        rays = 170
        fov = math.pi / 3
        self.canvas.delete("all")

        self.canvas.create_rectangle(0, 0, width, view_height / 2, fill="#18202a", outline="")
        self.canvas.create_rectangle(0, view_height / 2, width, view_height, fill="#2b241d", outline="")

        depth_buffer = []
        for index in range(rays):
            ray_angle = self.player["a"] - fov / 2 + (index / rays) * fov
            distance, hit, shade = self.cast_ray(ray_angle)
            corrected = max(distance * math.cos(ray_angle - self.player["a"]), 0.05)
            depth_buffer.append(corrected)
            slice_height = min(view_height * 1.5, view_height / corrected)
            x0 = int(index * width / rays)
            x1 = int((index + 1) * width / rays) + 1
            y0 = int(view_height / 2 - slice_height / 2 + math.sin(self.bob) * 3)
            y1 = int(y0 + slice_height)
            color = "#8a8a8a" if hit != "X" else "#b42626"
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=self.shade_color(color, shade * max(0.22, 1 - corrected / 14)), outline="")
            self.canvas.create_rectangle(x0, int((y0 + y1) / 2), x1, int((y0 + y1) / 2) + 2, fill="#2f2f2f", outline="")

        self.draw_enemies(depth_buffer, rays, view_height, fov, width)
        self.draw_weapon(width, height, hud_height)
        self.draw_hud(width, height, hud_height)
        if self.won or self.game_over:
            self.draw_end(width, height)

    def draw_enemies(self, depth_buffer, rays, view_height, fov, width):
        visible = []
        for enemy in self.enemies:
            if not enemy["alive"]:
                continue
            dx = enemy["x"] - self.player["x"]
            dy = enemy["y"] - self.player["y"]
            visible.append((math.hypot(dx, dy), math.atan2(dy, dx), enemy))
        for distance, angle, enemy in sorted(visible, key=lambda item: item[0], reverse=True):
            diff = math.atan2(math.sin(angle - self.player["a"]), math.cos(angle - self.player["a"]))
            if abs(diff) > fov / 1.5:
                continue
            screen_x = (0.5 + diff / fov) * width
            ray = int((screen_x / width) * rays)
            if 0 <= ray < len(depth_buffer) and distance > depth_buffer[ray] + 0.2:
                continue
            size = min(220, view_height / max(distance, 0.1))
            y = view_height / 2 - size / 2 + math.sin(self.bob) * 3
            self.canvas.create_rectangle(screen_x - size * 0.28, y + size * 0.28, screen_x + size * 0.28, y + size * 0.86, fill="#311818", outline="")
            self.canvas.create_rectangle(screen_x - size * 0.2, y + size * 0.06, screen_x + size * 0.2, y + size * 0.31, fill="#8b2d1f", outline="")
            self.canvas.create_rectangle(screen_x - size * 0.1, y + size * 0.14, screen_x - size * 0.04, y + size * 0.2, fill="#ffd25d", outline="")
            self.canvas.create_rectangle(screen_x + size * 0.04, y + size * 0.14, screen_x + size * 0.1, y + size * 0.2, fill="#ffd25d", outline="")

    def draw_weapon(self, width, height, hud_height):
        center = width / 2
        base = height - hud_height + 8 + (14 if self.flash else 0)
        muzzle = "#fff2a0" if self.flash else "#151515"
        self.canvas.create_rectangle(center - 48, base + 26, center + 48, base + 90, fill="#222222", outline="")
        self.canvas.create_rectangle(center - 26, base, center + 26, base + 86, fill="#5c5c5c", outline="")
        self.canvas.create_rectangle(center - 10, base - 9, center + 10, base + 13, fill=muzzle, outline="")

    def draw_hud(self, width, height, hud_height):
        y = height - hud_height
        self.canvas.create_rectangle(0, y, width, height, fill="#2b2b2b", outline="")
        self.canvas.create_rectangle(0, y, width, y + 4, fill="#111111", outline="")
        self.canvas.create_text(36, y + 28, text=f"AMMO {self.player['ammo']}", anchor="w", fill="#d8d8d8", font=(FONT_MEDIUM, 17))
        self.canvas.create_text(220, y + 28, text=f"HEALTH {int(self.player['hp'])}%", anchor="w", fill="#d8d8d8", font=(FONT_MEDIUM, 17))
        self.canvas.create_text(470, y + 28, text=f"SCORE {self.player['score']}", anchor="w", fill="#d8d8d8", font=(FONT_MEDIUM, 17))
        self.canvas.create_text(36, y + 60, text="E1M1: HANGAR | W/S anda, A/D gira, clique esquerdo atira", anchor="w", fill="#ff3030", font=(FONT_MEDIUM, 12))

    def draw_end(self, width, height):
        self.canvas.create_rectangle(0, 0, width, height, fill="#000000", stipple="gray50", outline="")
        text = "E1M1 COMPLETE" if self.won else "YOU DIED"
        color = "#ff3030" if self.won else "#d8d8d8"
        self.canvas.create_text(width / 2, height / 2 - 20, text=text, fill=color, font=(FONT_MEDIUM, 34))
        self.canvas.create_text(width / 2, height / 2 + 32, text="Pressione R para reiniciar", fill="#ffffff", font=(FONT_REGULAR, 14))

    def shade_color(self, color, shade):
        shade = min(max(shade, 0), 1)
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        return f"#{int(red * shade):02x}{int(green * shade):02x}{int(blue * shade):02x}"

    def tick(self):
        if not self.running:
            return
        now = time.perf_counter()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now
        self.update(dt)
        self.draw()
        self.window.after(33, self.tick)


class FreedoomLauncherWindow:
    def __init__(self, master):
        self.master = master
        self.running = True
        self.process = None

        self.window = Toplevel(master)
        self.window.title("Freedoom - #DOOM")
        self.window.geometry("560x330")
        self.window.minsize(500, 300)
        self.window.configure(bg="#171717")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.status = StringVar(value="Preparando Freedoom...")
        self.detail = StringVar(value="Na primeira vez eu baixo os arquivos livres do jogo e preparo o motor.")

        shell = Frame(self.window, bg="#171717", padx=24, pady=24)
        shell.pack(fill="both", expand=True)

        Label(
            shell,
            text="#DOOM",
            bg="#171717",
            fg="#f7f7f7",
            font=(FONT_MEDIUM, 28, "normal"),
            anchor="w",
        ).pack(fill="x")
        Label(
            shell,
            text="Freedoom + Chocolate Doom",
            bg="#171717",
            fg="#999999",
            font=(FONT_REGULAR, 11, "normal"),
            anchor="w",
        ).pack(fill="x", pady=(0, 20))
        Label(
            shell,
            textvariable=self.status,
            bg="#171717",
            fg="#ffffff",
            font=(FONT_MEDIUM, 12, "normal"),
            anchor="w",
            justify="left",
            wraplength=500,
        ).pack(fill="x")
        Label(
            shell,
            textvariable=self.detail,
            bg="#171717",
            fg="#c7c7c7",
            font=(FONT_REGULAR, 10, "normal"),
            anchor="w",
            justify="left",
            wraplength=500,
        ).pack(fill="x", pady=(8, 20))

        self.progress = ttk.Progressbar(shell, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill="x")
        self.progress.start(12)

        self.controls = Label(
            shell,
            text="Controles: W/S andar, A/D mover, E usar, Shift correr, Q/R trocar arma, Tab mapa, clique esquerdo atirar.",
            bg="#171717",
            fg="#999999",
            font=(FONT_REGULAR, 9, "normal"),
            anchor="w",
            justify="left",
            wraplength=500,
        )
        self.controls.pack(fill="x", pady=(18, 0))

        self.close_button = ttk.Button(shell, text="Fechar", command=self.close, style="Secondary.TButton")
        self.close_button.pack(anchor="e", pady=(18, 0))

        self.window.after(120, self.focus)
        threading.Thread(target=self.prepare_and_launch, daemon=True).start()

    def focus(self):
        try:
            self.window.focus_force()
            self.window.lift()
        except Exception:
            pass

    def close(self):
        self.running = False
        try:
            self.window.destroy()
        except Exception:
            pass

    def ui(self, callback):
        try:
            self.window.after(0, callback)
        except Exception:
            pass

    def set_status(self, status, detail=None):
        def update():
            self.status.set(status)
            if detail is not None:
                self.detail.set(detail)

        self.ui(update)

    def finish(self, status, detail, close_delay=None):
        def update():
            try:
                self.progress.stop()
                self.progress.pack_forget()
            except Exception:
                pass
            self.status.set(status)
            self.detail.set(detail)
            if close_delay:
                self.window.after(close_delay, self.close)

        self.ui(update)

    def prepare_and_launch(self):
        try:
            DOOM_DIR.mkdir(parents=True, exist_ok=True)
            wad_path = self.ensure_freedoom()
            engine_path = self.ensure_engine()
            config_path = self.ensure_control_config()

            self.set_status("Abrindo Freedoom...", "Se o mouse ficar preso na janela do jogo, use Esc para abrir o menu.")
            command = self.build_command(engine_path, wad_path, config_path)
            self.process = subprocess.Popen(command, cwd=str(DOOM_DIR), env=subprocess_environment())
            self.finish(
                "Freedoom aberto.",
                "O jogo iniciou em uma janela do motor Doom. Volte ao app quando terminar.",
                close_delay=3200,
            )
        except Exception as exc:
            self.finish("Nao consegui abrir o Freedoom.", str(exc))

    def ensure_freedoom(self):
        existing = self.find_file(DOOM_DIR, "freedoom1.wad")
        if existing:
            return existing

        archive_path = DOOM_DIR / f"freedoom-{FREEDOOM_VERSION}.zip"
        self.download_file(
            FREEDOOM_URL,
            archive_path,
            "Baixando Freedoom...",
            "Isso baixa somente dados livres do jogo, sem usar arquivos originais pagos do DOOM.",
        )
        extract_dir = DOOM_DIR / "freedoom"
        extract_dir.mkdir(parents=True, exist_ok=True)
        self.set_status("Extraindo Freedoom...", "Preparando o arquivo freedoom1.wad.")
        self.safe_extract_zip(archive_path, extract_dir)

        wad_path = self.find_file(extract_dir, "freedoom1.wad") or self.find_file(DOOM_DIR, "freedoom1.wad")
        if not wad_path:
            raise RuntimeError("O arquivo freedoom1.wad nao foi encontrado depois da extracao.")
        return wad_path

    def ensure_engine(self):
        if os.name == "nt":
            return self.ensure_windows_engine()
        return self.ensure_macos_engine()

    def ensure_windows_engine(self):
        existing = self.find_file(DOOM_DIR, "chocolate-doom.exe")
        if existing:
            return existing

        archive_path = DOOM_DIR / f"chocolate-doom-{CHOCOLATE_DOOM_VERSION}-win64.zip"
        self.download_file(
            CHOCOLATE_DOOM_WINDOWS_URL,
            archive_path,
            "Baixando Chocolate Doom...",
            "O motor e usado para rodar o Freedoom no Windows.",
        )
        extract_dir = DOOM_DIR / "chocolate-doom"
        extract_dir.mkdir(parents=True, exist_ok=True)
        self.set_status("Extraindo Chocolate Doom...", "Preparando o motor do jogo.")
        self.safe_extract_zip(archive_path, extract_dir)

        engine_path = self.find_file(extract_dir, "chocolate-doom.exe") or self.find_file(DOOM_DIR, "chocolate-doom.exe")
        if not engine_path:
            raise RuntimeError("O motor chocolate-doom.exe nao foi encontrado depois da extracao.")
        return engine_path

    def ensure_macos_engine(self):
        existing = self.find_macos_chocolate_doom()
        if existing:
            return existing

        brew_path = self.find_homebrew()
        if brew_path:
            self.set_status(
                "Instalando Chocolate Doom pelo Homebrew...",
                "Isso pode demorar alguns minutos na primeira vez.",
            )
            subprocess.run([brew_path, "install", "chocolate-doom"], check=True, timeout=900, env=subprocess_environment())
            existing = self.find_macos_chocolate_doom()
            if existing:
                return existing

        raise RuntimeError(
            "Chocolate Doom nao foi encontrado no Mac. Rode o Instalador_Automatico_macOS.command atualizado "
            "ou instale com: brew install chocolate-doom"
        )

    def ensure_control_config(self):
        config_dir = DOOM_DIR / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "default.cfg"
        config_path.write_text(
            "\n".join(
                [
                    "use_mouse 1",
                    "mouseb_fire 0",
                    "mouseb_strafe -1",
                    "mouseb_forward -1",
                    "mouseb_speed -1",
                    "mouseb_use -1",
                    "mouse_sensitivity 7",
                    "dclick_use 0",
                    "key_up 119",
                    "key_down 115",
                    "key_strafeleft 97",
                    "key_straferight 100",
                    "key_fire 157",
                    "key_use 101",
                    "key_speed 182",
                    "key_prevweapon 113",
                    "key_nextweapon 114",
                    "key_map_toggle 9",
                    "key_map_follow 102",
                    "key_map_grid 103",
                    "key_map_mark 109",
                    "key_map_clearmark 99",
                    "screenblocks 10",
                    "show_messages 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return config_path

    def build_command(self, engine_path, wad_path, config_path):
        command = [
            str(engine_path),
            "-iwad",
            str(wad_path),
            "-config",
            str(config_path),
            "-warp",
            "1",
            "1",
            "-skill",
            "3",
            "-window",
        ]
        return command

    def download_file(self, url, destination, status, detail):
        self.set_status(status, detail)
        request = urllib.request.Request(url, headers={"User-Agent": f"YTDLP-GUI/{APP_VERSION}"})
        temp_path = destination.with_suffix(destination.suffix + ".tmp")

        with urlopen_with_certifi(request, timeout=180) as response, temp_path.open("wb") as file:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                file.write(chunk)

        temp_path.replace(destination)

    def safe_extract_zip(self, archive_path, destination):
        root = destination.resolve()
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (destination / member.filename).resolve()
                if target != root and root not in target.parents:
                    raise RuntimeError("Arquivo ZIP invalido: caminho fora da pasta de destino.")
                archive.extract(member, destination)

    def find_file(self, root, filename):
        try:
            for candidate in root.rglob(filename):
                if candidate.is_file():
                    return candidate
        except Exception:
            return None
        return None

    def find_homebrew(self):
        for candidate in (shutil.which("brew"), "/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
            if candidate and Path(candidate).exists():
                return candidate
        return None

    def find_macos_chocolate_doom(self):
        for candidate in (
            shutil.which("chocolate-doom"),
            "/opt/homebrew/bin/chocolate-doom",
            "/usr/local/bin/chocolate-doom",
        ):
            if candidate and Path(candidate).exists():
                return Path(candidate)
        return None


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

    requirements = app_dir / "python" / "requirements.txt"
    if requirements.exists():
        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--upgrade", "-r", str(requirements)],
                cwd=str(app_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=180,
            )
        except Exception:
            pass

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
        self.window_icon_photo = None
        self.last_process_lines = []
        self.current_process_kind = None
        self.download_watchdog_job = None
        self.last_output_time = None
        self.update_check_running = False
        self.update_check_id = 0
        self.update_check_timeout_job = None
        self.selection_pills = []
        self.doom_window = None

        self.destino = StringVar(value=self.config["default_folder"])
        self.formato = StringVar(value="mp4")
        self.nome_modo = StringVar(value="original")
        self.nome_custom = StringVar()
        self.cookies_mode = StringVar(value="none")
        self.cookies_file = StringVar()
        self.yt_dlp_path = StringVar(value=find_yt_dlp(self.config["yt_dlp_path"]))
        self.extra_args = StringVar(value=self.config["extra_args"])
        self.update_manifest_url = StringVar(value=self.config.get("update_manifest_url") or DEFAULT_UPDATE_MANIFEST_URL)
        self.keep_window_on_top = BooleanVar(value=False)
        self.status_text = StringVar(value="Pronto para baixar.")
        self.current_screen = "download"

        self.root.title(f"{self.config['title']} - v{APP_VERSION}")
        self.root.geometry("1080x760")
        self.root.minsize(620, 460)
        self.root.configure(bg=self.config["background_color"])
        self.apply_window_icon()

        self.setup_styles()
        self.build_ui()
        self.apply_theme()
        self.load_background_image()
        self.root.after(100, self.drain_output_queue)
        self.root.bind("<Configure>", self.schedule_background_refresh)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def apply_window_icon(self):
        png_icon_path = get_app_png_icon_path()
        if png_icon_path:
            try:
                self.window_icon_photo = PhotoImage(file=str(png_icon_path))
                self.root.iconphoto(True, self.window_icon_photo)
            except Exception:
                self.window_icon_photo = None

        icon_path = get_app_icon_path()
        if not icon_path:
            return
        try:
            self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

    def make_selection_pill(self, parent, text, variable, value=None, mode="radio", command=None):
        pill = SelectionPill(parent, text=text, variable=variable, value=value, mode=mode, command=command)
        self.selection_pills.append(pill)
        return pill

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
            text=f"Downloads de video e audio com visual premium Edge Solutions. v{APP_VERSION}",
            style="AppSubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.always_on_top_pill = self.make_selection_pill(
            header,
            text="Sempre no topo",
            variable=self.keep_window_on_top,
            command=lambda: self.root.attributes("-topmost", self.keep_window_on_top.get()),
            mode="check",
        )
        self.always_on_top_pill.pack(side="right")

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
        self.make_selection_pill(format_box, "Video MP4 - alta qualidade", self.formato, "mp4").pack(fill="x")
        self.make_selection_pill(format_box, "Audio MP3 - musicas", self.formato, "mp3").pack(fill="x", pady=(8, 0))

        name_box = ttk.LabelFrame(options_grid, text="Nome do arquivo", style="Panel.TLabelframe", padding=12)
        name_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.make_selection_pill(name_box, "Manter nome original", self.nome_modo, "original").pack(fill="x")
        self.make_selection_pill(name_box, "Usar nome personalizado", self.nome_modo, "custom").pack(fill="x", pady=(8, 0))
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
            self.make_selection_pill(cookies_box, text, self.cookies_mode, value).pack(fill="x", pady=3)
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
        self.update_app_button = ttk.Button(tool_box, text="Verificar atualizacao", command=self.check_app_update)
        self.update_app_button.grid(row=3, column=1, padx=(8, 0))

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
        self.style.configure("Panel.TFrame", background=cfg["panel_color"], borderwidth=1, relief="solid", bordercolor=EDGE_BORDER)
        if hasattr(self, "download_scroll"):
            self.download_scroll.set_colors(cfg["background_color"])
        if hasattr(self, "customize_scroll"):
            self.customize_scroll.set_colors(cfg["background_color"])
        self.style.configure("Title.TLabel", background=cfg["background_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 23, "normal"))
        self.style.configure("AppSubtitle.TLabel", background=cfg["background_color"], foreground=cfg["muted_text_color"], font=(FONT_REGULAR, 10, "normal"))
        self.style.configure("Section.TLabel", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 12, "normal"))
        self.style.configure("Hint.TLabel", background=cfg["panel_color"], foreground=cfg["muted_text_color"], font=(FONT_REGULAR, 9, "normal"))
        self.style.configure("Status.TLabel", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 10, "normal"))
        self.style.configure("PreviewTitle.TLabel", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 14, "normal"))
        self.style.configure("PreviewText.TLabel", background=cfg["panel_color"], foreground=cfg["muted_text_color"], font=(FONT_REGULAR, font_size, "normal"))
        self.style.configure("Main.TCheckbutton", background=cfg["background_color"], foreground=cfg["text_color"])
        self.style.configure("Main.TRadiobutton", background=cfg["panel_color"], foreground=cfg["text_color"])
        self.style.map("Main.TCheckbutton", background=[("active", cfg["background_color"])], foreground=[("active", cfg["text_color"])])
        self.style.map("Main.TRadiobutton", background=[("active", cfg["panel_color"])], foreground=[("active", cfg["text_color"])])
        self.style.configure("Panel.TLabelframe", background=cfg["panel_color"], foreground=cfg["text_color"], bordercolor=EDGE_BORDER, relief="solid")
        self.style.configure("Panel.TLabelframe.Label", background=cfg["panel_color"], foreground=cfg["text_color"], font=(FONT_MEDIUM, 10, "normal"))
        self.style.configure("Image.TLabel", background=cfg["background_color"])
        self.style.configure("TButton", background=EDGE_MUTED_SURFACE, foreground=cfg["text_color"], padding=(12, 8), font=(FONT_REGULAR, 9, "normal"), bordercolor=EDGE_BORDER)
        self.style.map("TButton", background=[("active", "#363636"), ("disabled", "#242424")], foreground=[("disabled", cfg["muted_text_color"])])
        self.style.configure("Accent.TButton", background=cfg["button_color"], foreground=cfg["button_text_color"], padding=(15, 10), font=(FONT_MEDIUM, 9, "normal"), bordercolor=cfg["button_color"])
        self.style.map("Accent.TButton", background=[("active", EDGE_BLUE_LIGHT), ("disabled", "#242424")], foreground=[("disabled", cfg["muted_text_color"])])
        self.style.configure("Nav.TButton", background=EDGE_MUTED_SURFACE, foreground=cfg["muted_text_color"], padding=(16, 8), font=(FONT_REGULAR, 10, "normal"), bordercolor=EDGE_BORDER)
        self.style.configure("ActiveNav.TButton", background=cfg["button_color"], foreground=cfg["button_text_color"], padding=(28, 13), font=(FONT_MEDIUM, 12, "normal"), bordercolor=cfg["button_color"])
        self.style.map("Nav.TButton", background=[("active", "#363636")], foreground=[("active", cfg["text_color"])])
        self.style.map("ActiveNav.TButton", background=[("active", EDGE_BLUE_LIGHT)])
        self.style.configure("TEntry", fieldbackground=cfg["entry_bg"], foreground=cfg["entry_fg"], padding=7, bordercolor=EDGE_BORDER, lightcolor=EDGE_BORDER, darkcolor=EDGE_BORDER, insertcolor=cfg["entry_fg"])
        self.style.configure("TCombobox", fieldbackground=cfg["entry_bg"], background=cfg["entry_bg"], foreground=cfg["entry_fg"], arrowcolor=cfg["text_color"], bordercolor=EDGE_BORDER)
        self.style.map("TCombobox", fieldbackground=[("readonly", cfg["entry_bg"])], foreground=[("readonly", cfg["entry_fg"])])
        self.style.configure(
            "Edge.Vertical.TScrollbar",
            gripcount=0,
            background=EDGE_MUTED_SURFACE,
            darkcolor=cfg["background_color"],
            lightcolor=cfg["background_color"],
            troughcolor=cfg["background_color"],
            bordercolor=cfg["background_color"],
            arrowcolor=cfg["muted_text_color"],
            width=10,
            relief="flat",
        )
        self.style.map(
            "Edge.Vertical.TScrollbar",
            background=[("active", cfg["button_color"]), ("pressed", cfg["button_color"])],
            arrowcolor=[("active", cfg["button_text_color"]), ("pressed", cfg["button_text_color"])],
        )

        for pill in self.selection_pills:
            pill.set_theme(cfg)

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
        background_secret = self.theme_vars.get("background_color")
        if background_secret and background_secret.get().strip().upper() == "#DOOM":
            background_secret.set(self.config.get("background_color", DEFAULT_CONFIG["background_color"]))
            self.launch_doom_easter_egg()
            self.show_toast("#DOOM ativado. Preparando Freedoom...", "info")
            return

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
        self.root.title(f"{self.config['title']} - v{APP_VERSION}")
        save_config(self.config)
        for key in self.color_swatches:
            self.paint_swatch(key)
        self.apply_theme()
        self.load_background_image()
        self.log("Personalizacao aplicada e salva.")
        self.show_screen("download")

    def launch_doom_easter_egg(self):
        try:
            if self.doom_window and self.doom_window.running:
                self.doom_window.focus()
                return
        except Exception:
            pass
        self.doom_window = FreedoomLauncherWindow(self.root)

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

        ffmpeg_location = bundled_ffmpeg_location()
        if ffmpeg_location:
            command += ["--ffmpeg-location", ffmpeg_location]

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
                env=subprocess_environment(),
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
        if not manifest_url.lower().startswith(("http://", "https://")):
            self.show_toast("A URL de atualizacao precisa comecar com http:// ou https://.", "error")
            return
        if self.update_check_running:
            self.show_toast("Ja estou verificando atualizacao. Aguarde terminar.", "error")
            return

        self.config["update_manifest_url"] = manifest_url
        save_config(self.config)
        self.update_check_id += 1
        check_id = self.update_check_id
        self.start_update_check(check_id)
        threading.Thread(target=self.fetch_update_manifest, args=(manifest_url, check_id), daemon=True).start()

    def start_update_check(self, check_id):
        self.update_check_running = True
        if hasattr(self, "update_app_button"):
            self.update_app_button.configure(text="Verificando...", state="disabled")
        self.status_text.set("Verificando atualizacao do aplicativo...")
        if self.update_check_timeout_job:
            self.root.after_cancel(self.update_check_timeout_job)
        self.update_check_timeout_job = self.root.after(
            UPDATE_CHECK_TIMEOUT_SECONDS * 1000,
            lambda: self.on_update_check_timeout(check_id),
        )

    def finish_update_check(self, check_id):
        if check_id != self.update_check_id or not self.update_check_running:
            return False
        self.update_check_running = False
        if self.update_check_timeout_job:
            self.root.after_cancel(self.update_check_timeout_job)
            self.update_check_timeout_job = None
        if hasattr(self, "update_app_button"):
            self.update_app_button.configure(text="Verificar atualizacao", state="normal")
        return True

    def on_update_check_timeout(self, check_id):
        if check_id != self.update_check_id or not self.update_check_running:
            return
        self.update_check_running = False
        self.update_check_timeout_job = None
        if hasattr(self, "update_app_button"):
            self.update_app_button.configure(text="Verificar atualizacao", state="normal")
        message = "A verificacao demorou demais. Confira se a URL esta publica e se a internet consegue acessar o GitHub."
        self.status_text.set(message)
        self.show_toast(message, "error", duration=8000)

    def handle_update_check_error(self, message, check_id):
        if not self.finish_update_check(check_id):
            return
        self.status_text.set(message)
        self.show_toast(message, "error", duration=8000)

    def fetch_update_manifest(self, manifest_url, check_id):
        try:
            request_url = cache_busted_url(manifest_url)
            request = urllib.request.Request(request_url, headers={"User-Agent": f"YTDLP-GUI/{APP_VERSION}"})
            with urlopen_with_certifi(request, timeout=12) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    raise urllib.error.HTTPError(request_url, status, "Erro HTTP ao abrir manifesto", response.headers, None)
                data = response.read(2_000_000).decode("utf-8-sig")
            manifest = json.loads(data)
            self.root.after(0, lambda manifest=manifest, check_id=check_id: self.handle_update_manifest(manifest, check_id))
        except urllib.error.HTTPError as exc:
            message = f"Nao consegui verificar atualizacao: erro HTTP {exc.code}."
            self.root.after(0, lambda message=message, check_id=check_id: self.handle_update_check_error(message, check_id))
        except urllib.error.URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            message = SSL_CERT_ERROR_HINT if self.has_ssl_certificate_error(reason) else f"Nao consegui verificar atualizacao: {reason}."
            self.root.after(0, lambda message=message, check_id=check_id: self.handle_update_check_error(message, check_id))
        except ssl.SSLError as exc:
            message = SSL_CERT_ERROR_HINT if self.has_ssl_certificate_error(str(exc)) else f"Nao consegui verificar atualizacao: {exc}."
            self.root.after(0, lambda message=message, check_id=check_id: self.handle_update_check_error(message, check_id))
        except json.JSONDecodeError:
            message = "Nao consegui verificar atualizacao: a URL nao retornou um JSON valido."
            self.root.after(0, lambda message=message, check_id=check_id: self.handle_update_check_error(message, check_id))
        except Exception as exc:
            message = f"Nao consegui verificar atualizacao: {exc}."
            self.root.after(0, lambda message=message, check_id=check_id: self.handle_update_check_error(message, check_id))

    def handle_update_manifest(self, manifest, check_id):
        if not self.finish_update_check(check_id):
            return
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
            if running_frozen():
                installer_key = "installer_windows_url" if os.name == "nt" else "installer_macos_url"
                installer_url = str(manifest.get(installer_key, "")).strip()
                if installer_url:
                    webbrowser.open(installer_url)
                    self.show_toast("Baixe e execute o instalador novo para concluir a atualizacao.", "info", duration=7000)
                else:
                    self.show_toast("Baixe a versao nova pelo GitHub ou pela pasta do servidor.", "info", duration=7000)
                return
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
                if APP_DIR.name.lower() == "bin" and relative_path.lower().startswith("bin/"):
                    relative_path = relative_path[4:]

                target = temp_dir / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                request = urllib.request.Request(url, headers={"User-Agent": f"YTDLP-GUI/{APP_VERSION}"})
                with urlopen_with_certifi(request, timeout=60) as response:
                    target.write_bytes(response.read())

            updater_path = APP_DIR / "_apply_update.py"
            updater_path.write_text(UPDATER_SCRIPT, encoding="utf-8")
            subprocess.Popen([sys.executable, str(updater_path), str(temp_dir), str(APP_DIR), str(Path(__file__).resolve())], cwd=str(APP_DIR))
            self.root.after(0, lambda: self.show_toast("Atualizacao baixada. Reiniciando...", "success", duration=1800))
            self.root.after(1900, self.root.destroy)
        except Exception as exc:
            message = SSL_CERT_ERROR_HINT if self.has_ssl_certificate_error(str(exc)) else f"Falha na atualizacao: {exc}"
            self.root.after(0, lambda message=message: self.show_toast(message, "error"))

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

    def has_ssl_certificate_error(self, text):
        lower = text.lower()
        return "certificate_verify_failed" in lower or "unable to get local issuer certificate" in lower

    def handle_process_done(self, code, message):
        self.cancel_download_watchdog()
        if code == 0:
            self.status_text.set("Download concluido com sucesso.")
            self.show_toast("Download concluido com sucesso.", "success", duration=5500)
            return

        clean_message = message.replace("[ERRO] ", "").strip()
        details = "\n".join([part for part in [clean_message, "\n".join(self.last_process_lines[-5:]).strip()] if part]).strip()
        if self.has_ssl_certificate_error(details):
            ssl_message = SSL_CERT_ERROR_HINT
            self.status_text.set(ssl_message)
            self.show_toast(ssl_message, "error", duration=10000)
            return
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
    configure_windows_app_identity()
    root = Tk()
    app = DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
