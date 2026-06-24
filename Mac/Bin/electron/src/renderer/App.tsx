import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import type { DownloadEvent, DownloadFormat, FileNameMode, ThemeConfig } from "../shared/types";
import "./styles.css";

const APP_VERSION = "1.7.2";

const defaultTheme: ThemeConfig = {
  title: "Edge Solutions Downloader",
  backgroundColor: "#171717",
  panelColor: "#1f1f1f",
  textColor: "#f7f7f7",
  mutedTextColor: "#999999",
  buttonColor: "#0000ff",
  buttonTextColor: "#ffffff",
  entryBg: "#262626",
  entryFg: "#f7f7f7"
};

type Toast = {
  id: number;
  type: "success" | "error" | "info";
  message: string;
};

type DoomPlayer = {
  x: number;
  y: number;
  a: number;
  hp: number;
  ammo: number;
  score: number;
};

type DoomEnemy = {
  x: number;
  y: number;
  hp: number;
  alive: boolean;
};

type DoomState = {
  running: boolean;
  won: boolean;
  gameOver: boolean;
  flash: number;
  bob: number;
  lastTime: number;
};

function loadTheme() {
  try {
    const stored = localStorage.getItem("baixador-theme");
    return stored ? { ...defaultTheme, ...JSON.parse(stored) } : defaultTheme;
  } catch {
    return defaultTheme;
  }
}

function isHexColor(value: string) {
  return /^#[0-9a-fA-F]{6}$/.test(value.trim());
}

function safeCssColor(value: string, fallback: string) {
  return isHexColor(value) ? value : fallback;
}

function Lightfall() {
  const beams = useMemo(
    () =>
      Array.from({ length: 36 }, (_, index) => ({
        id: index,
        left: `${(index * 17) % 100}%`,
        delay: `${(index % 12) * -0.42}s`,
        duration: `${4.4 + (index % 7) * 0.45}s`,
        height: `${70 + (index % 6) * 24}px`
      })),
    []
  );

  return (
    <div className="lightfall" aria-hidden="true">
      <div className="lightfallGlow" />
      {beams.map((beam) => (
        <span
          key={beam.id}
          className="lightfallBeam"
          style={{
            left: beam.left,
            animationDelay: beam.delay,
            animationDuration: beam.duration,
            height: beam.height
          }}
        />
      ))}
    </div>
  );
}

function StarButton({
  children,
  active = false,
  disabled = false,
  onClick,
  type = "button"
}: {
  children: React.ReactNode;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit";
}) {
  return (
    <button className={`starButton ${active ? "active" : ""}`} disabled={disabled} onClick={onClick} type={type}>
      <span className="starBorder" />
      <span className="buttonGlow" />
      <span className="buttonText">{children}</span>
    </button>
  );
}

function BentoCard({
  title,
  children,
  compact = false
}: {
  title: string;
  children: React.ReactNode;
  compact?: boolean;
}) {
  return (
    <section className={`bentoCard ${compact ? "compact" : ""}`}>
      <div className="bentoShine" />
      <h2>{title}</h2>
      {children}
    </section>
  );
}

const DOOM_MAP = [
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
  "111111111111111111111111"
];

const DOOM_ENEMY_STARTS: [number, number][] = [
  [7.4, 3.5],
  [14.5, 5.5],
  [19.5, 7.5],
  [7.5, 13.5],
  [16.5, 15.5],
  [20.5, 18.5]
];

function createDoomPlayer(): DoomPlayer {
  return { x: 2.5, y: 2.5, a: 0, hp: 100, ammo: 50, score: 0 };
}

function createDoomEnemies(): DoomEnemy[] {
  return DOOM_ENEMY_STARTS.map(([x, y]) => ({ x, y, hp: 30, alive: true }));
}

function doomTile(x: number, y: number) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  if (iy < 0 || iy >= DOOM_MAP.length || ix < 0 || ix >= DOOM_MAP[0].length) {
    return "1";
  }
  return DOOM_MAP[iy][ix];
}

function doomSolid(x: number, y: number) {
  return doomTile(x, y) === "1";
}

function angleDistance(a: number, b: number) {
  return Math.atan2(Math.sin(a - b), Math.cos(a - b));
}

function shadeColor(color: string, shade: number) {
  const safeShade = Math.max(0, Math.min(1, shade));
  const red = Number.parseInt(color.slice(1, 3), 16);
  const green = Number.parseInt(color.slice(3, 5), 16);
  const blue = Number.parseInt(color.slice(5, 7), 16);
  return `rgb(${Math.floor(red * safeShade)}, ${Math.floor(green * safeShade)}, ${Math.floor(blue * safeShade)})`;
}

function DoomEasterEgg({ onClose }: { onClose: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const keysRef = useRef<Set<string>>(new Set());
  const playerRef = useRef<DoomPlayer>(createDoomPlayer());
  const enemiesRef = useRef<DoomEnemy[]>(createDoomEnemies());
  const stateRef = useRef<DoomState>({
    running: true,
    won: false,
    gameOver: false,
    flash: 0,
    bob: 0,
    lastTime: performance.now()
  });

  function resetGame() {
    playerRef.current = createDoomPlayer();
    enemiesRef.current = createDoomEnemies();
    stateRef.current.won = false;
    stateRef.current.gameOver = false;
    stateRef.current.flash = 0;
    stateRef.current.bob = 0;
    stateRef.current.lastTime = performance.now();
  }

  function movePlayer(dx: number, dy: number) {
    const player = playerRef.current;
    const nx = player.x + dx;
    const ny = player.y + dy;
    if (!doomSolid(nx, player.y)) {
      player.x = nx;
    }
    if (!doomSolid(player.x, ny)) {
      player.y = ny;
    }
  }

  function lineClear(targetX: number, targetY: number) {
    const player = playerRef.current;
    const dx = targetX - player.x;
    const dy = targetY - player.y;
    const distance = Math.max(Math.hypot(dx, dy), 0.01);
    const steps = Math.max(4, Math.floor(distance / 0.08));
    for (let step = 1; step < steps; step += 1) {
      const x = player.x + dx * (step / steps);
      const y = player.y + dy * (step / steps);
      if (doomSolid(x, y)) {
        return false;
      }
    }
    return true;
  }

  function shoot() {
    const player = playerRef.current;
    const state = stateRef.current;
    if (state.won || state.gameOver || player.ammo <= 0) {
      return;
    }

    player.ammo -= 1;
    state.flash = 0.14;

    let bestEnemy: DoomEnemy | null = null;
    let bestDiff = 0.16;
    for (const enemy of enemiesRef.current) {
      if (!enemy.alive) {
        continue;
      }
      const dx = enemy.x - player.x;
      const dy = enemy.y - player.y;
      const distance = Math.hypot(dx, dy);
      const angle = Math.atan2(dy, dx);
      const diff = Math.abs(angleDistance(angle, player.a));
      if (diff < bestDiff && distance < 9 && lineClear(enemy.x, enemy.y)) {
        bestEnemy = enemy;
        bestDiff = diff;
      }
    }

    if (bestEnemy) {
      bestEnemy.hp -= 34;
      if (bestEnemy.hp <= 0) {
        bestEnemy.alive = false;
        player.score += 100;
      }
    }
  }

  function castRay(angle: number) {
    let distance = 0.02;
    const step = 0.035;
    const rayX = Math.cos(angle);
    const rayY = Math.sin(angle);
    let hit = "1";
    let shade = 1;

    while (distance < 24) {
      const x = playerRef.current.x + rayX * distance;
      const y = playerRef.current.y + rayY * distance;
      hit = doomTile(x, y);
      if (hit !== "0") {
        const rx = Math.abs(x - Math.floor(x) - 0.5);
        const ry = Math.abs(y - Math.floor(y) - 0.5);
        shade = rx > ry ? 0.78 : 1;
        break;
      }
      distance += step;
    }

    return { distance, hit, shade };
  }

  function updateGame(dt: number) {
    const state = stateRef.current;
    const player = playerRef.current;
    if (state.won || state.gameOver) {
      return;
    }

    const keys = keysRef.current;
    const speed = keys.has("shift") ? 4.3 : 2.8;
    const turnSpeed = 2.5;
    let forward = 0;
    let strafe = 0;

    if (keys.has("w")) forward += 1;
    if (keys.has("s")) forward -= 1;
    if (keys.has("d")) strafe += 1;
    if (keys.has("a")) strafe -= 1;
    if (keys.has("q") || keys.has("arrowleft")) player.a -= turnSpeed * dt;
    if (keys.has("e") || keys.has("arrowright")) player.a += turnSpeed * dt;

    if (forward || strafe) {
      const length = Math.hypot(forward, strafe) || 1;
      const stepForward = (forward / length) * speed * dt;
      const stepStrafe = (strafe / length) * speed * dt;
      movePlayer(
        Math.cos(player.a) * stepForward + Math.cos(player.a + Math.PI / 2) * stepStrafe,
        Math.sin(player.a) * stepForward + Math.sin(player.a + Math.PI / 2) * stepStrafe
      );
      state.bob += dt * 9;
    }

    state.flash = Math.max(0, state.flash - dt);

    for (const enemy of enemiesRef.current) {
      if (!enemy.alive) {
        continue;
      }
      const dx = player.x - enemy.x;
      const dy = player.y - enemy.y;
      const distance = Math.hypot(dx, dy);
      if (distance < 7 && lineClear(enemy.x, enemy.y)) {
        const enemyDx = (dx / Math.max(distance, 0.01)) * dt * 0.68;
        const enemyDy = (dy / Math.max(distance, 0.01)) * dt * 0.68;
        if (!doomSolid(enemy.x + enemyDx, enemy.y)) {
          enemy.x += enemyDx;
        }
        if (!doomSolid(enemy.x, enemy.y + enemyDy)) {
          enemy.y += enemyDy;
        }
      }
      if (distance < 0.7) {
        player.hp -= 18 * dt;
        if (player.hp <= 0) {
          player.hp = 0;
          state.gameOver = true;
        }
      }
    }

    if (doomTile(player.x, player.y) === "X") {
      state.won = true;
    }
  }

  function drawEnemies(
    ctx: CanvasRenderingContext2D,
    depthBuffer: number[],
    rays: number,
    viewHeight: number,
    fov: number,
    width: number
  ) {
    const player = playerRef.current;
    const visible = enemiesRef.current
      .filter((enemy) => enemy.alive)
      .map((enemy) => ({
        enemy,
        distance: Math.hypot(enemy.x - player.x, enemy.y - player.y),
        angle: Math.atan2(enemy.y - player.y, enemy.x - player.x)
      }))
      .sort((a, b) => b.distance - a.distance);

    for (const item of visible) {
      const diff = angleDistance(item.angle, player.a);
      if (Math.abs(diff) > fov / 1.5) {
        continue;
      }
      const screenX = (0.5 + diff / fov) * width;
      const ray = Math.floor((screenX / width) * rays);
      if (ray >= 0 && ray < depthBuffer.length && item.distance > depthBuffer[ray] + 0.2) {
        continue;
      }

      const size = Math.min(220, viewHeight / Math.max(item.distance, 0.1));
      const y = viewHeight / 2 - size / 2 + Math.sin(stateRef.current.bob) * 3;
      ctx.fillStyle = "#311818";
      ctx.fillRect(screenX - size * 0.28, y + size * 0.28, size * 0.56, size * 0.58);
      ctx.fillStyle = "#8b2d1f";
      ctx.fillRect(screenX - size * 0.2, y + size * 0.06, size * 0.4, size * 0.25);
      ctx.fillStyle = "#ffd25d";
      ctx.fillRect(screenX - size * 0.1, y + size * 0.14, size * 0.06, size * 0.06);
      ctx.fillRect(screenX + size * 0.04, y + size * 0.14, size * 0.06, size * 0.06);
    }
  }

  function drawWeapon(ctx: CanvasRenderingContext2D, width: number, height: number, hudHeight: number) {
    const center = width / 2;
    const base = height - hudHeight + 8 + (stateRef.current.flash ? 14 : 0);
    ctx.fillStyle = "#222222";
    ctx.fillRect(center - 48, base + 26, 96, 90);
    ctx.fillStyle = "#5c5c5c";
    ctx.fillRect(center - 26, base, 52, 94);
    ctx.fillStyle = stateRef.current.flash ? "#fff2a0" : "#151515";
    ctx.fillRect(center - 10, base - 9, 20, 22);
  }

  function drawHud(ctx: CanvasRenderingContext2D, width: number, height: number, hudHeight: number) {
    const player = playerRef.current;
    const y = height - hudHeight;
    ctx.fillStyle = "#2b2b2b";
    ctx.fillRect(0, y, width, hudHeight);
    ctx.fillStyle = "#111111";
    ctx.fillRect(0, y, width, 4);
    ctx.fillStyle = "#d8d8d8";
    ctx.font = "700 17px Montserrat, system-ui, sans-serif";
    ctx.fillText(`AMMO ${player.ammo}`, 36, y + 32);
    ctx.fillText(`HEALTH ${Math.floor(player.hp)}%`, 220, y + 32);
    ctx.fillText(`SCORE ${player.score}`, 470, y + 32);
    ctx.fillStyle = "#ff3030";
    ctx.font = "700 12px Montserrat, system-ui, sans-serif";
    ctx.fillText("E1M1 | W/A/S/D move | mouse mira | clique atira | Q/E gira | Shift corre | Esc sai", 36, y + 62);
  }

  function drawEnd(ctx: CanvasRenderingContext2D, width: number, height: number) {
    const state = stateRef.current;
    if (!state.won && !state.gameOver) {
      return;
    }
    ctx.fillStyle = "rgba(0, 0, 0, 0.72)";
    ctx.fillRect(0, 0, width, height);
    ctx.textAlign = "center";
    ctx.fillStyle = state.won ? "#ff3030" : "#d8d8d8";
    ctx.font = "800 42px Montserrat, system-ui, sans-serif";
    ctx.fillText(state.won ? "E1M1 COMPLETE" : "YOU DIED", width / 2, height / 2 - 20);
    ctx.fillStyle = "#ffffff";
    ctx.font = "500 15px Montserrat, system-ui, sans-serif";
    ctx.fillText("Pressione R para reiniciar ou Esc para sair", width / 2, height / 2 + 34);
    ctx.textAlign = "start";
  }

  function drawGame() {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) {
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(rect.width, 1);
    const height = Math.max(rect.height, 1);
    if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const hudHeight = 86;
    const viewHeight = Math.max(height - hudHeight, 1);
    const rays = Math.max(120, Math.min(220, Math.floor(width / 4)));
    const fov = Math.PI / 3;
    const player = playerRef.current;

    ctx.fillStyle = "#18202a";
    ctx.fillRect(0, 0, width, viewHeight / 2);
    ctx.fillStyle = "#2b241d";
    ctx.fillRect(0, viewHeight / 2, width, viewHeight / 2);

    const depthBuffer: number[] = [];
    for (let index = 0; index < rays; index += 1) {
      const rayAngle = player.a - fov / 2 + (index / rays) * fov;
      const { distance, hit, shade } = castRay(rayAngle);
      const corrected = Math.max(distance * Math.cos(rayAngle - player.a), 0.05);
      depthBuffer.push(corrected);
      const sliceHeight = Math.min(viewHeight * 1.5, viewHeight / corrected);
      const x0 = Math.floor((index * width) / rays);
      const x1 = Math.floor(((index + 1) * width) / rays) + 1;
      const y0 = Math.floor(viewHeight / 2 - sliceHeight / 2 + Math.sin(stateRef.current.bob) * 3);
      const color = hit !== "X" ? "#8a8a8a" : "#b42626";
      ctx.fillStyle = shadeColor(color, shade * Math.max(0.22, 1 - corrected / 14));
      ctx.fillRect(x0, y0, x1 - x0, sliceHeight);
      ctx.fillStyle = "#2f2f2f";
      ctx.fillRect(x0, y0 + sliceHeight / 2, x1 - x0, 2);
    }

    drawEnemies(ctx, depthBuffer, rays, viewHeight, fov, width);

    ctx.strokeStyle = "rgba(255, 255, 255, 0.72)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(width / 2 - 9, viewHeight / 2);
    ctx.lineTo(width / 2 + 9, viewHeight / 2);
    ctx.moveTo(width / 2, viewHeight / 2 - 9);
    ctx.lineTo(width / 2, viewHeight / 2 + 9);
    ctx.stroke();

    drawWeapon(ctx, width, height, hudHeight);
    drawHud(ctx, width, height, hudHeight);
    drawEnd(ctx, width, height);
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    canvas?.focus();

    function onKeyDown(event: KeyboardEvent) {
      const key = event.key.toLowerCase();
      if (["w", "a", "s", "d", "q", "e", "arrowleft", "arrowright", "shift", " ", "r", "escape"].includes(key)) {
        event.preventDefault();
      }
      if (key === "escape") {
        onClose();
        return;
      }
      if (key === "r" && (stateRef.current.won || stateRef.current.gameOver)) {
        resetGame();
      }
      if (key === " " && !event.repeat) {
        shoot();
      }
      keysRef.current.add(key);
    }

    function onKeyUp(event: KeyboardEvent) {
      keysRef.current.delete(event.key.toLowerCase());
    }

    function frame(time: number) {
      const state = stateRef.current;
      if (!state.running) {
        return;
      }
      const dt = Math.min((time - state.lastTime) / 1000, 0.05);
      state.lastTime = time;
      updateGame(dt);
      drawGame();
      window.requestAnimationFrame(frame);
    }

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    const frameId = window.requestAnimationFrame(frame);

    return () => {
      stateRef.current.running = false;
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      if (document.pointerLockElement) {
        document.exitPointerLock();
      }
    };
  }, [onClose]);

  function handleMouseDown(event: React.MouseEvent<HTMLCanvasElement>) {
    if (event.button !== 0) {
      return;
    }
    canvasRef.current?.focus();
    canvasRef.current?.requestPointerLock?.();
    shoot();
  }

  function handleMouseMove(event: React.MouseEvent<HTMLCanvasElement>) {
    if (document.pointerLockElement === canvasRef.current && !stateRef.current.won && !stateRef.current.gameOver) {
      playerRef.current.a += event.movementX * 0.003;
    }
  }

  return (
    <div className="doomOverlay">
      <div className="doomTopbar">
        <div>
          <p className="eyebrow">Arquivo secreto</p>
          <h2>E1M1</h2>
        </div>
        <button className="doomClose" type="button" onClick={onClose}>
          Fechar
        </button>
      </div>
      <canvas
        ref={canvasRef}
        className="doomCanvas"
        tabIndex={0}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
      />
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState<"home" | "customize">("home");
  const [theme, setTheme] = useState<ThemeConfig>(() => loadTheme());
  const [destination, setDestination] = useState("");
  const [url, setUrl] = useState("");
  const [format, setFormat] = useState<DownloadFormat>("video");
  const [fileNameMode, setFileNameMode] = useState<FileNameMode>("original");
  const [customName, setCustomName] = useState("");
  const [extraArgs, setExtraArgs] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [status, setStatus] = useState("Pronto para baixar.");
  const [logs, setLogs] = useState<string[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [doomOpen, setDoomOpen] = useState(false);
  const closeDoom = useCallback(() => setDoomOpen(false), []);

  useEffect(() => {
    window.baixador.getDefaultDownloadsFolder().then(setDestination).catch(() => undefined);
  }, []);

  useEffect(() => {
    const remove = window.baixador.onDownloadEvent((event: DownloadEvent) => {
      setLogs((current) => [...current.slice(-80), event.message.trim()].filter(Boolean));

      if (event.type === "started") {
        setStatus("Baixando...");
        showToast("Download iniciado.", "info");
      }
      if (event.type === "done") {
        setStatus("Download concluido.");
        setActiveJobId(null);
        showToast("Download concluido.", "success");
      }
      if (event.type === "error") {
        setStatus(event.message || "Download falhou.");
        setActiveJobId(null);
        showToast(event.message || "Download falhou.", "error");
      }
    });
    return remove;
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--bg", safeCssColor(theme.backgroundColor, defaultTheme.backgroundColor));
    root.style.setProperty("--panel", safeCssColor(theme.panelColor, defaultTheme.panelColor));
    root.style.setProperty("--text", safeCssColor(theme.textColor, defaultTheme.textColor));
    root.style.setProperty("--muted", safeCssColor(theme.mutedTextColor, defaultTheme.mutedTextColor));
    root.style.setProperty("--button", safeCssColor(theme.buttonColor, defaultTheme.buttonColor));
    root.style.setProperty("--buttonText", safeCssColor(theme.buttonTextColor, defaultTheme.buttonTextColor));
    root.style.setProperty("--entryBg", safeCssColor(theme.entryBg, defaultTheme.entryBg));
    root.style.setProperty("--entryFg", safeCssColor(theme.entryFg, defaultTheme.entryFg));
  }, [theme]);

  function showToast(message: string, type: Toast["type"]) {
    const id = Date.now();
    setToasts((current) => [...current, { id, message, type }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 4200);
  }

  async function chooseFolder() {
    const folder = await window.baixador.chooseFolder();
    if (folder) {
      setDestination(folder);
    }
  }

  async function startDownload() {
    try {
      setStatus("Preparando download...");
      const result = await window.baixador.startDownload({
        url,
        destination,
        format,
        fileNameMode,
        customName,
        extraArgs
      });
      setActiveJobId(result.jobId);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Nao consegui iniciar o download.";
      setStatus(message);
      showToast(message, "error");
    }
  }

  async function cancelDownload() {
    if (!activeJobId) {
      return;
    }
    await window.baixador.cancelDownload(activeJobId);
    setActiveJobId(null);
    setStatus("Download cancelado.");
  }

  function updateTheme<K extends keyof ThemeConfig>(key: K, value: ThemeConfig[K]) {
    setTheme((current) => ({ ...current, [key]: value }));
  }

  function resetTheme() {
    setTheme(defaultTheme);
    localStorage.setItem("baixador-theme", JSON.stringify(defaultTheme));
    showToast("Tema restaurado.", "success");
  }

  function applyCustomization() {
    if (theme.backgroundColor.trim().toUpperCase() === "#DOOM") {
      const nextTheme = { ...theme, backgroundColor: defaultTheme.backgroundColor };
      setTheme(nextTheme);
      localStorage.setItem("baixador-theme", JSON.stringify(nextTheme));
      setDoomOpen(true);
      showToast("#DOOM ativado.", "info");
      return;
    }

    const colorKeys: (keyof ThemeConfig)[] = [
      "backgroundColor",
      "panelColor",
      "textColor",
      "mutedTextColor",
      "buttonColor",
      "buttonTextColor",
      "entryBg",
      "entryFg"
    ];
    if (colorKeys.some((key) => !isHexColor(theme[key]))) {
      showToast("Revise as cores antes de salvar.", "error");
      return;
    }

    localStorage.setItem("baixador-theme", JSON.stringify(theme));
    showToast("Tema salvo.", "success");
  }

  return (
    <main className="appShell">
      <Lightfall />

      {doomOpen && <DoomEasterEgg onClose={closeDoom} />}

      <div className="toastStack">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>

      <header className="topbar">
        <div>
          <p className="eyebrow">BaixadorDeVideos3000</p>
          <h1>{theme.title}</h1>
          <span className="version">Electron + React + TypeScript v{APP_VERSION}</span>
        </div>
        <nav className="navButtons">
          <StarButton active={screen === "home"} onClick={() => setScreen("home")}>
            Home
          </StarButton>
          <StarButton active={screen === "customize"} onClick={() => setScreen("customize")}>
            Personalizar
          </StarButton>
        </nav>
      </header>

      {screen === "home" ? (
        <section className="contentGrid">
          <BentoCard title="Download">
            <label>
              Link do video
              <textarea value={url} onChange={(event) => setUrl(event.target.value)} placeholder="Cole aqui links do YouTube, Instagram, Twitter/X e outros sites aceitos pelo yt-dlp." />
            </label>

            <div className="twoColumns">
              <label>
                Formato
                <select value={format} onChange={(event) => setFormat(event.target.value as DownloadFormat)}>
                  <option value="video">Video MP4</option>
                  <option value="audio">Audio MP3</option>
                </select>
              </label>
              <label>
                Nome do arquivo
                <select value={fileNameMode} onChange={(event) => setFileNameMode(event.target.value as FileNameMode)}>
                  <option value="original">Nome original</option>
                  <option value="custom">Nome personalizado</option>
                </select>
              </label>
            </div>

            {fileNameMode === "custom" && (
              <label>
                Nome personalizado
                <input value={customName} onChange={(event) => setCustomName(event.target.value)} placeholder="Sem .mp4 ou .mp3" />
              </label>
            )}

            <label>
              Pasta de destino
              <div className="folderRow">
                <input value={destination} onChange={(event) => setDestination(event.target.value)} />
                <StarButton onClick={chooseFolder}>Procurar</StarButton>
              </div>
            </label>

            <label>
              Argumentos extras
              <input value={extraArgs} onChange={(event) => setExtraArgs(event.target.value)} placeholder='Exemplo: --cookies-from-browser chrome' />
            </label>

            <div className="actionRow">
              <StarButton active disabled={Boolean(activeJobId)} onClick={startDownload}>
                Iniciar download
              </StarButton>
              <StarButton disabled={!activeJobId} onClick={cancelDownload}>
                Cancelar
              </StarButton>
            </div>
          </BentoCard>

          <div className="sideStack">
            <BentoCard title="Status" compact>
              <p className="statusText">{status}</p>
              <div className="miniActions">
                <StarButton onClick={() => window.baixador.openDownloadsFolder(destination)}>Abrir pasta</StarButton>
              </div>
            </BentoCard>

            <BentoCard title="Eventos" compact>
              <div className="logBox">
                {logs.length === 0 ? <p>Nenhum evento ainda.</p> : logs.map((line, index) => <p key={`${line}-${index}`}>{line}</p>)}
              </div>
            </BentoCard>
          </div>
        </section>
      ) : (
        <section className="contentGrid customizeGrid">
          <BentoCard title="Personalizacao">
            <div className="themeGrid">
              {(
                [
                  ["title", "Titulo"],
                  ["backgroundColor", "Fundo"],
                  ["panelColor", "Paineis"],
                  ["textColor", "Texto"],
                  ["mutedTextColor", "Texto secundario"],
                  ["buttonColor", "Botoes"],
                  ["buttonTextColor", "Texto dos botoes"],
                  ["entryBg", "Campos"],
                  ["entryFg", "Texto dos campos"]
                ] as [keyof ThemeConfig, string][]
              ).map(([key, label]) => (
                <label key={key}>
                  {label}
                  {key === "title" ? (
                    <input value={theme[key]} onChange={(event) => updateTheme(key, event.target.value)} />
                  ) : (
                    <div className="colorRow">
                      <input
                        type="color"
                        value={isHexColor(theme[key]) ? theme[key] : defaultTheme[key]}
                        onChange={(event) => updateTheme(key, event.target.value)}
                      />
                      <input value={theme[key]} onChange={(event) => updateTheme(key, event.target.value)} />
                    </div>
                  )}
                </label>
              ))}
            </div>
            <div className="actionRow">
              <StarButton active onClick={applyCustomization}>
                Aplicar e salvar
              </StarButton>
              <StarButton onClick={resetTheme}>Restaurar padrao</StarButton>
            </div>
          </BentoCard>

          <BentoCard title="Previa" compact>
            <div className="previewPanel">
              <p className="eyebrow">Preview</p>
              <h3>{theme.title}</h3>
              <p>Os efeitos visuais desta versao nascem em React/CSS, entao ficam mais faceis de mudar depois.</p>
              <StarButton active>Botao Edge</StarButton>
            </div>
          </BentoCard>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(<App />);
