import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import type { DownloadEvent, DownloadFormat, FileNameMode, ThemeConfig } from "../shared/types";
import "./styles.css";

const APP_VERSION = "1.7.1";

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

function loadTheme() {
  try {
    const stored = localStorage.getItem("baixador-theme");
    return stored ? { ...defaultTheme, ...JSON.parse(stored) } : defaultTheme;
  } catch {
    return defaultTheme;
  }
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
    localStorage.setItem("baixador-theme", JSON.stringify(theme));
    const root = document.documentElement;
    root.style.setProperty("--bg", theme.backgroundColor);
    root.style.setProperty("--panel", theme.panelColor);
    root.style.setProperty("--text", theme.textColor);
    root.style.setProperty("--muted", theme.mutedTextColor);
    root.style.setProperty("--button", theme.buttonColor);
    root.style.setProperty("--buttonText", theme.buttonTextColor);
    root.style.setProperty("--entryBg", theme.entryBg);
    root.style.setProperty("--entryFg", theme.entryFg);
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
    showToast("Tema restaurado.", "success");
  }

  return (
    <main className="appShell">
      <Lightfall />

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
                      <input type="color" value={theme[key]} onChange={(event) => updateTheme(key, event.target.value)} />
                      <input value={theme[key]} onChange={(event) => updateTheme(key, event.target.value)} />
                    </div>
                  )}
                </label>
              ))}
            </div>
            <div className="actionRow">
              <StarButton active onClick={() => showToast("Tema salvo.", "success")}>
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
