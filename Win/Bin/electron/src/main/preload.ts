import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("baixador", {
  chooseFolder: () => ipcRenderer.invoke("dialog:choose-folder"),
  openDownloadsFolder: (folder: string) => ipcRenderer.invoke("shell:open-folder", folder),
  startDownload: (options: unknown) => ipcRenderer.invoke("download:start", options),
  cancelDownload: (jobId: string) => ipcRenderer.invoke("download:cancel", jobId),
  getDefaultDownloadsFolder: () => ipcRenderer.invoke("app:get-default-downloads-folder"),
  getPlatform: () => ipcRenderer.invoke("app:get-platform"),
  onDownloadEvent: (callback: (event: unknown) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, payload: unknown) => callback(payload);
    ipcRenderer.on("download:event", listener);
    return () => ipcRenderer.removeListener("download:event", listener);
  }
});
