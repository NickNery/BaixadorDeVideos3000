"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const node_child_process_1 = require("node:child_process");
const node_fs_1 = __importDefault(require("node:fs"));
const node_http_1 = __importDefault(require("node:http"));
const node_https_1 = __importDefault(require("node:https"));
const node_os_1 = __importDefault(require("node:os"));
const node_path_1 = __importDefault(require("node:path"));
const jobs = new Map();
let mainWindow = null;
const FREEDOOM_VERSION = "0.13.0";
const FREEDOOM_URL = `https://github.com/freedoom/freedoom/releases/download/v${FREEDOOM_VERSION}/freedoom-${FREEDOOM_VERSION}.zip`;
const CHOCOLATE_DOOM_VERSION = "3.1.1";
const CHOCOLATE_DOOM_WINDOWS_URL = `https://github.com/chocolate-doom/chocolate-doom/releases/download/chocolate-doom-${CHOCOLATE_DOOM_VERSION}/chocolate-doom-${CHOCOLATE_DOOM_VERSION}-win64.zip`;
electron_1.app.disableHardwareAcceleration();
electron_1.app.commandLine.appendSwitch("disable-gpu");
function isDev() {
    return Boolean(process.env.VITE_DEV_SERVER_URL);
}
function appRoot() {
    if (isDev()) {
        return node_path_1.default.resolve(electron_1.app.getAppPath(), "..");
    }
    const appPath = electron_1.app.getAppPath();
    const candidates = [
        node_path_1.default.resolve(appPath, ".."),
        node_path_1.default.resolve(process.cwd()),
        process.resourcesPath,
        node_path_1.default.resolve(process.resourcesPath, "app"),
        appPath
    ];
    return (candidates.find((candidate) => {
        return (node_fs_1.default.existsSync(node_path_1.default.join(candidate, "release")) ||
            node_fs_1.default.existsSync(node_path_1.default.join(candidate, "electron", "package.json")) ||
            node_fs_1.default.existsSync(node_path_1.default.join(candidate, "assets")));
    }) || node_path_1.default.resolve(appPath, ".."));
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
function doomDir() {
    return node_path_1.default.join(appRoot(), "doom");
}
function findOnPath(name) {
    const pathValue = process.env.PATH || "";
    for (const folder of pathValue.split(node_path_1.default.delimiter)) {
        if (!folder) {
            continue;
        }
        const candidate = node_path_1.default.join(folder, name);
        if (node_fs_1.default.existsSync(candidate)) {
            return candidate;
        }
    }
    return null;
}
function findFileRecursive(root, fileName) {
    if (!node_fs_1.default.existsSync(root)) {
        return null;
    }
    for (const entry of node_fs_1.default.readdirSync(root, { withFileTypes: true })) {
        const fullPath = node_path_1.default.join(root, entry.name);
        if (entry.isFile() && entry.name === fileName) {
            return fullPath;
        }
        if (entry.isDirectory()) {
            const found = findFileRecursive(fullPath, fileName);
            if (found) {
                return found;
            }
        }
    }
    return null;
}
function sendDoomEvent(window, type, message) {
    const target = window && !window.isDestroyed() ? window : mainWindow;
    if (!target || target.isDestroyed()) {
        return;
    }
    target.webContents.send("doom:event", { type, message });
}
function runProcess(command, args, options = {}) {
    return new Promise((resolve, reject) => {
        const child = (0, node_child_process_1.spawn)(command, args, {
            cwd: options.cwd,
            windowsHide: true
        });
        let output = "";
        const timeout = options.timeoutMs
            ? setTimeout(() => {
                child.kill();
                reject(new Error(`Tempo esgotado ao executar ${command}.`));
            }, options.timeoutMs)
            : null;
        child.stdout.on("data", (chunk) => {
            output += chunk.toString();
        });
        child.stderr.on("data", (chunk) => {
            output += chunk.toString();
        });
        child.on("error", (error) => {
            if (timeout) {
                clearTimeout(timeout);
            }
            reject(error);
        });
        child.on("close", (code) => {
            if (timeout) {
                clearTimeout(timeout);
            }
            if (code === 0) {
                resolve();
            }
            else {
                reject(new Error(output.trim() || `${command} terminou com codigo ${code}.`));
            }
        });
    });
}
function downloadFile(url, destination, window, status, redirectCount = 0) {
    sendDoomEvent(window, "info", status);
    node_fs_1.default.mkdirSync(node_path_1.default.dirname(destination), { recursive: true });
    const tempPath = `${destination}.tmp`;
    return new Promise((resolve, reject) => {
        if (redirectCount > 5) {
            reject(new Error("Redirecionamentos demais ao baixar o arquivo."));
            return;
        }
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === "http:" ? node_http_1.default : node_https_1.default;
        const request = client.get(parsedUrl, {
            headers: {
                "User-Agent": "BaixadorDeVideos3000-Electron"
            }
        }, (response) => {
            const statusCode = response.statusCode || 0;
            const locationHeader = response.headers.location;
            const redirect = Array.isArray(locationHeader) ? locationHeader[0] : locationHeader;
            if (statusCode >= 300 && statusCode < 400 && redirect) {
                response.resume();
                const nextUrl = new URL(redirect, parsedUrl).toString();
                downloadFile(nextUrl, destination, window, status, redirectCount + 1).then(resolve).catch(reject);
                return;
            }
            if (statusCode !== 200) {
                response.resume();
                reject(new Error(`Falha ao baixar arquivo. Codigo HTTP ${statusCode}.`));
                return;
            }
            const file = node_fs_1.default.createWriteStream(tempPath);
            response.pipe(file);
            file.on("finish", () => {
                file.close(() => {
                    node_fs_1.default.renameSync(tempPath, destination);
                    resolve();
                });
            });
            file.on("error", (error) => {
                node_fs_1.default.rmSync(tempPath, { force: true });
                reject(error);
            });
        });
        request.on("error", (error) => {
            node_fs_1.default.rmSync(tempPath, { force: true });
            reject(error);
        });
        request.setTimeout(180000, () => {
            request.destroy(new Error("Tempo esgotado ao baixar arquivo."));
        });
    });
}
async function extractZip(archivePath, destination, window, status) {
    sendDoomEvent(window, "info", status);
    node_fs_1.default.mkdirSync(destination, { recursive: true });
    if (process.platform === "win32") {
        await runProcess("powershell.exe", [
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "& { param([string]$ArchivePath, [string]$DestinationPath) Expand-Archive -LiteralPath $ArchivePath -DestinationPath $DestinationPath -Force }",
            archivePath,
            destination
        ], { timeoutMs: 180000 });
        return;
    }
    await runProcess("/usr/bin/unzip", ["-oq", archivePath, "-d", destination], { timeoutMs: 180000 });
}
async function ensureFreedoom(window) {
    const root = doomDir();
    const existing = findFileRecursive(root, "freedoom1.wad");
    if (existing) {
        return existing;
    }
    const archivePath = node_path_1.default.join(root, `freedoom-${FREEDOOM_VERSION}.zip`);
    if (!node_fs_1.default.existsSync(archivePath)) {
        await downloadFile(FREEDOOM_URL, archivePath, window, "Baixando Freedoom...");
    }
    const extractDir = node_path_1.default.join(root, "freedoom");
    await extractZip(archivePath, extractDir, window, "Extraindo Freedoom...");
    const wadPath = findFileRecursive(extractDir, "freedoom1.wad") || findFileRecursive(root, "freedoom1.wad");
    if (!wadPath) {
        throw new Error("O arquivo freedoom1.wad nao foi encontrado depois da extracao.");
    }
    return wadPath;
}
async function ensureWindowsChocolateDoom(window) {
    const root = doomDir();
    const existing = findFileRecursive(root, "chocolate-doom.exe");
    if (existing) {
        return existing;
    }
    const archivePath = node_path_1.default.join(root, `chocolate-doom-${CHOCOLATE_DOOM_VERSION}-win64.zip`);
    if (!node_fs_1.default.existsSync(archivePath)) {
        await downloadFile(CHOCOLATE_DOOM_WINDOWS_URL, archivePath, window, "Baixando Chocolate Doom...");
    }
    const extractDir = node_path_1.default.join(root, "chocolate-doom");
    await extractZip(archivePath, extractDir, window, "Extraindo Chocolate Doom...");
    const enginePath = findFileRecursive(extractDir, "chocolate-doom.exe") || findFileRecursive(root, "chocolate-doom.exe");
    if (!enginePath) {
        throw new Error("O motor chocolate-doom.exe nao foi encontrado depois da extracao.");
    }
    return enginePath;
}
function findMacChocolateDoom() {
    return firstExisting([
        findOnPath("chocolate-doom") || "",
        "/opt/homebrew/bin/chocolate-doom",
        "/usr/local/bin/chocolate-doom"
    ]);
}
function findHomebrew() {
    return firstExisting([findOnPath("brew") || "", "/opt/homebrew/bin/brew", "/usr/local/bin/brew"]);
}
async function ensureMacChocolateDoom(window) {
    const existing = findMacChocolateDoom();
    if (existing) {
        return existing;
    }
    const brewPath = findHomebrew();
    if (brewPath) {
        sendDoomEvent(window, "info", "Instalando Chocolate Doom pelo Homebrew...");
        await runProcess(brewPath, ["install", "chocolate-doom"], { cwd: doomDir(), timeoutMs: 900000 });
        const installed = findMacChocolateDoom();
        if (installed) {
            return installed;
        }
    }
    throw new Error("Chocolate Doom nao foi encontrado no Mac. Rode o setup do Mac atualizado ou instale com: brew install chocolate-doom");
}
function ensureChocolateDoomConfig() {
    const configDir = node_path_1.default.join(doomDir(), "config");
    node_fs_1.default.mkdirSync(configDir, { recursive: true });
    const configPath = node_path_1.default.join(configDir, "default.cfg");
    node_fs_1.default.writeFileSync(configPath, [
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
        ""
    ].join("\n"), "utf-8");
    return configPath;
}
async function launchChocolateDoom(window) {
    node_fs_1.default.mkdirSync(doomDir(), { recursive: true });
    const wadPath = await ensureFreedoom(window);
    const enginePath = process.platform === "win32" ? await ensureWindowsChocolateDoom(window) : await ensureMacChocolateDoom(window);
    const configPath = ensureChocolateDoomConfig();
    const args = ["-iwad", wadPath, "-config", configPath, "-warp", "1", "1", "-skill", "3", "-window"];
    sendDoomEvent(window, "info", "Abrindo Freedoom no Chocolate Doom...");
    await new Promise((resolve, reject) => {
        const child = (0, node_child_process_1.spawn)(enginePath, args, {
            cwd: doomDir(),
            detached: true,
            stdio: "ignore",
            windowsHide: false
        });
        child.once("error", reject);
        child.once("spawn", () => {
            child.unref();
            resolve();
        });
    });
    sendDoomEvent(window, "done", "Freedoom aberto.");
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
electron_1.ipcMain.handle("doom:launch", async (event) => {
    const window = electron_1.BrowserWindow.fromWebContents(event.sender) ?? mainWindow;
    try {
        await launchChocolateDoom(window);
        return { ok: true };
    }
    catch (error) {
        const message = error instanceof Error ? error.message : "Nao consegui abrir o Freedoom.";
        sendDoomEvent(window, "error", message);
        throw new Error(message);
    }
});
