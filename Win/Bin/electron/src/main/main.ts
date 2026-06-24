import { app, BrowserWindow, dialog, ipcMain, shell } from "electron";
import { spawn, ChildProcessWithoutNullStreams } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

type DownloadOptions = {
  url: string;
  destination: string;
  format: "video" | "audio";
  fileNameMode: "original" | "custom";
  customName: string;
  extraArgs: string;
};

type DownloadJob = {
  process: ChildProcessWithoutNullStreams;
  window: BrowserWindow;
};

const jobs = new Map<string, DownloadJob>();
let mainWindow: BrowserWindow | null = null;

app.disableHardwareAcceleration();
app.commandLine.appendSwitch("disable-gpu");

function isDev() {
  return Boolean(process.env.VITE_DEV_SERVER_URL);
}

function appRoot() {
  if (isDev()) {
    return path.resolve(app.getAppPath(), "..");
  }
  const appPath = app.getAppPath();
  const candidates = [
    path.resolve(appPath, ".."),
    path.resolve(process.cwd()),
    process.resourcesPath,
    path.resolve(process.resourcesPath, "app"),
    appPath
  ];

  return (
    candidates.find((candidate) => {
      return (
        fs.existsSync(path.join(candidate, "release")) ||
        fs.existsSync(path.join(candidate, "electron", "package.json")) ||
        fs.existsSync(path.join(candidate, "assets"))
      );
    }) || path.resolve(appPath, "..")
  );
}

function firstExisting(candidates: string[]) {
  return candidates.find((candidate) => fs.existsSync(candidate));
}

function resolveYtdlpBinary() {
  const root = appRoot();
  const exeName = process.platform === "win32" ? "yt-dlp.exe" : "yt-dlp";
  const local = firstExisting([
    path.join(root, exeName),
    path.join(root, "release", exeName),
    path.join(app.getAppPath(), "..", "release", exeName),
    path.join(app.getAppPath(), "..", "..", "release", exeName)
  ]);
  return local || exeName;
}

function resolveFfmpegDir() {
  const root = appRoot();
  const exeName = process.platform === "win32" ? "ffmpeg.exe" : "ffmpeg";
  const local = firstExisting([
    path.join(root, exeName),
    path.join(root, "release", exeName),
    path.join(app.getAppPath(), "..", "release", exeName),
    path.join(app.getAppPath(), "..", "..", "release", exeName)
  ]);
  return local ? path.dirname(local) : null;
}

function splitArgs(input: string) {
  const args: string[] = [];
  const pattern = /"([^"]*)"|'([^']*)'|(\S+)/g;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(input))) {
    args.push(match[1] ?? match[2] ?? match[3]);
  }
  return args;
}

function sanitizeFileName(value: string) {
  return value.replace(/[<>:"/\\|?*\x00-\x1F]/g, "").trim();
}

function buildYtdlpArgs(options: DownloadOptions) {
  const args = ["--newline", "--no-playlist"];
  const ffmpegDir = resolveFfmpegDir();

  if (ffmpegDir) {
    args.push("--ffmpeg-location", ffmpegDir);
  }

  if (options.format === "audio") {
    args.push("-x", "--audio-format", "mp3", "--audio-quality", "0");
  } else {
    args.push("-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]", "--merge-output-format", "mp4");
  }

  const template =
    options.fileNameMode === "custom" && sanitizeFileName(options.customName)
      ? `${sanitizeFileName(options.customName)}.%(ext)s`
      : "%(title)s [%(id)s].%(ext)s";

  args.push("-o", path.join(options.destination, template));

  if (options.extraArgs.trim()) {
    args.push(...splitArgs(options.extraArgs));
  }

  args.push(options.url.trim());
  return args;
}

function sendDownloadEvent(jobId: string, type: string, message: string, code?: number | null) {
  const target = jobs.get(jobId)?.window || mainWindow;
  if (!target || target.isDestroyed()) {
    return;
  }
  target.webContents.send("download:event", { jobId, type, message, code });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 760,
    minWidth: 920,
    minHeight: 620,
    backgroundColor: "#171717",
    title: "Baixador de Videos 3000",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js")
    }
  });

  if (isDev()) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL as string);
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "renderer", "index.html"));
  }
}

app.setAppUserModelId("EdgeSolutions.BaixadorDeVideos3000");

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  for (const [jobId, job] of jobs) {
    job.process.kill();
    jobs.delete(jobId);
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

ipcMain.handle("app:get-default-downloads-folder", () => path.join(os.homedir(), "Downloads"));
ipcMain.handle("app:get-platform", () => process.platform);

ipcMain.handle("dialog:choose-folder", async () => {
  const options: Electron.OpenDialogOptions = {
    properties: ["openDirectory", "createDirectory"]
  };
  const result = mainWindow ? await dialog.showOpenDialog(mainWindow, options) : await dialog.showOpenDialog(options);
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle("shell:open-folder", async (_event, folder: string) => {
  if (folder && fs.existsSync(folder)) {
    await shell.openPath(folder);
  }
});

ipcMain.handle("download:start", async (event, options: DownloadOptions) => {
  if (!options.url.trim()) {
    throw new Error("Cole uma URL antes de iniciar.");
  }
  if (!options.destination.trim()) {
    throw new Error("Escolha uma pasta de destino.");
  }
  if (!fs.existsSync(options.destination)) {
    fs.mkdirSync(options.destination, { recursive: true });
  }

  const jobId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const bin = resolveYtdlpBinary();
  const args = buildYtdlpArgs(options);
  const child = spawn(bin, args, {
    cwd: appRoot(),
    windowsHide: true
  });
  const window = BrowserWindow.fromWebContents(event.sender) ?? mainWindow;

  if (!window) {
    throw new Error("Janela principal indisponivel.");
  }

  jobs.set(jobId, { process: child, window });
  sendDownloadEvent(jobId, "started", "Download iniciado.");

  child.stdout.on("data", (chunk) => sendDownloadEvent(jobId, "stdout", chunk.toString()));
  child.stderr.on("data", (chunk) => sendDownloadEvent(jobId, "stderr", chunk.toString()));
  child.on("error", (error) => {
    sendDownloadEvent(jobId, "error", error.message);
    jobs.delete(jobId);
  });
  child.on("close", (code) => {
    sendDownloadEvent(jobId, code === 0 ? "done" : "error", code === 0 ? "Download concluido." : `yt-dlp terminou com codigo ${code}.`, code);
    jobs.delete(jobId);
  });

  return { jobId };
});

ipcMain.handle("download:cancel", async (_event, jobId: string) => {
  const job = jobs.get(jobId);
  if (!job) {
    return { cancelled: false };
  }
  job.process.kill();
  jobs.delete(jobId);
  sendDownloadEvent(jobId, "error", "Download cancelado.");
  return { cancelled: true };
});
