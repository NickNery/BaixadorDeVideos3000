"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const node_child_process_1 = require("node:child_process");
const node_fs_1 = __importDefault(require("node:fs"));
const node_os_1 = __importDefault(require("node:os"));
const node_path_1 = __importDefault(require("node:path"));
const jobs = new Map();
let mainWindow = null;
electron_1.app.disableHardwareAcceleration();
electron_1.app.commandLine.appendSwitch("disable-gpu");
function isDev() {
    return Boolean(process.env.VITE_DEV_SERVER_URL);
}
function appRoot() {
    if (isDev()) {
        return node_path_1.default.resolve(electron_1.app.getAppPath(), "..");
    }
    return process.resourcesPath;
}
function firstExisting(candidates) {
    return candidates.find((candidate) => node_fs_1.default.existsSync(candidate));
}
function resolveYtdlpBinary() {
    const root = appRoot();
    const exeName = process.platform === "win32" ? "yt-dlp.exe" : "yt-dlp";
    const local = firstExisting([
        node_path_1.default.join(root, exeName),
        node_path_1.default.join(root, "release", exeName),
        node_path_1.default.join(electron_1.app.getAppPath(), "..", "release", exeName),
        node_path_1.default.join(electron_1.app.getAppPath(), "..", "..", "release", exeName)
    ]);
    return local || exeName;
}
function resolveFfmpegDir() {
    const root = appRoot();
    const exeName = process.platform === "win32" ? "ffmpeg.exe" : "ffmpeg";
    const local = firstExisting([
        node_path_1.default.join(root, exeName),
        node_path_1.default.join(root, "release", exeName),
        node_path_1.default.join(electron_1.app.getAppPath(), "..", "release", exeName),
        node_path_1.default.join(electron_1.app.getAppPath(), "..", "..", "release", exeName)
    ]);
    return local ? node_path_1.default.dirname(local) : null;
}
function splitArgs(input) {
    const args = [];
    const pattern = /"([^"]*)"|'([^']*)'|(\S+)/g;
    let match;
    while ((match = pattern.exec(input))) {
        args.push(match[1] ?? match[2] ?? match[3]);
    }
    return args;
}
function sanitizeFileName(value) {
    return value.replace(/[<>:"/\\|?*\x00-\x1F]/g, "").trim();
}
function buildYtdlpArgs(options) {
    const args = ["--newline", "--no-playlist"];
    const ffmpegDir = resolveFfmpegDir();
    if (ffmpegDir) {
        args.push("--ffmpeg-location", ffmpegDir);
    }
    if (options.format === "audio") {
        args.push("-x", "--audio-format", "mp3", "--audio-quality", "0");
    }
    else {
        args.push("-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]", "--merge-output-format", "mp4");
    }
    const template = options.fileNameMode === "custom" && sanitizeFileName(options.customName)
        ? `${sanitizeFileName(options.customName)}.%(ext)s`
        : "%(title)s [%(id)s].%(ext)s";
    args.push("-o", node_path_1.default.join(options.destination, template));
    if (options.extraArgs.trim()) {
        args.push(...splitArgs(options.extraArgs));
    }
    args.push(options.url.trim());
    return args;
}
function sendDownloadEvent(jobId, type, message, code) {
    const target = jobs.get(jobId)?.window || mainWindow;
    if (!target || target.isDestroyed()) {
        return;
    }
    target.webContents.send("download:event", { jobId, type, message, code });
}
function createWindow() {
    mainWindow = new electron_1.BrowserWindow({
        width: 1180,
        height: 760,
        minWidth: 920,
        minHeight: 620,
        backgroundColor: "#171717",
        title: "Baixador de Videos 3000",
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
            preload: node_path_1.default.join(__dirname, "preload.js")
        }
    });
    if (isDev()) {
        mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    }
    else {
        mainWindow.loadFile(node_path_1.default.join(__dirname, "..", "renderer", "index.html"));
    }
}
electron_1.app.setAppUserModelId("EdgeSolutions.BaixadorDeVideos3000");
electron_1.app.whenReady().then(() => {
    createWindow();
    electron_1.app.on("activate", () => {
        if (electron_1.BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});
electron_1.app.on("window-all-closed", () => {
    for (const [jobId, job] of jobs) {
        job.process.kill();
        jobs.delete(jobId);
    }
    if (process.platform !== "darwin") {
        electron_1.app.quit();
    }
});
electron_1.ipcMain.handle("app:get-default-downloads-folder", () => node_path_1.default.join(node_os_1.default.homedir(), "Downloads"));
electron_1.ipcMain.handle("app:get-platform", () => process.platform);
electron_1.ipcMain.handle("dialog:choose-folder", async () => {
    const options = {
        properties: ["openDirectory", "createDirectory"]
    };
    const result = mainWindow ? await electron_1.dialog.showOpenDialog(mainWindow, options) : await electron_1.dialog.showOpenDialog(options);
    return result.canceled ? null : result.filePaths[0];
});
electron_1.ipcMain.handle("shell:open-folder", async (_event, folder) => {
    if (folder && node_fs_1.default.existsSync(folder)) {
        await electron_1.shell.openPath(folder);
    }
});
electron_1.ipcMain.handle("download:start", async (event, options) => {
    if (!options.url.trim()) {
        throw new Error("Cole uma URL antes de iniciar.");
    }
    if (!options.destination.trim()) {
        throw new Error("Escolha uma pasta de destino.");
    }
    if (!node_fs_1.default.existsSync(options.destination)) {
        node_fs_1.default.mkdirSync(options.destination, { recursive: true });
    }
    const jobId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const bin = resolveYtdlpBinary();
    const args = buildYtdlpArgs(options);
    const child = (0, node_child_process_1.spawn)(bin, args, {
        cwd: appRoot(),
        windowsHide: true
    });
    const window = electron_1.BrowserWindow.fromWebContents(event.sender) ?? mainWindow;
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
electron_1.ipcMain.handle("download:cancel", async (_event, jobId) => {
    const job = jobs.get(jobId);
    if (!job) {
        return { cancelled: false };
    }
    job.process.kill();
    jobs.delete(jobId);
    sendDownloadEvent(jobId, "error", "Download cancelado.");
    return { cancelled: true };
});
