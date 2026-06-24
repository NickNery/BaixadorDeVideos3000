"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
electron_1.contextBridge.exposeInMainWorld("baixador", {
    chooseFolder: () => electron_1.ipcRenderer.invoke("dialog:choose-folder"),
    openDownloadsFolder: (folder) => electron_1.ipcRenderer.invoke("shell:open-folder", folder),
    startDownload: (options) => electron_1.ipcRenderer.invoke("download:start", options),
    cancelDownload: (jobId) => electron_1.ipcRenderer.invoke("download:cancel", jobId),
    getDefaultDownloadsFolder: () => electron_1.ipcRenderer.invoke("app:get-default-downloads-folder"),
    getPlatform: () => electron_1.ipcRenderer.invoke("app:get-platform"),
    onDownloadEvent: (callback) => {
        const listener = (_event, payload) => callback(payload);
        electron_1.ipcRenderer.on("download:event", listener);
        return () => electron_1.ipcRenderer.removeListener("download:event", listener);
    }
});
