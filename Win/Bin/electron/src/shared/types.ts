export type DownloadFormat = "video" | "audio";
export type FileNameMode = "original" | "custom";

export type ThemeConfig = {
  title: string;
  backgroundColor: string;
  panelColor: string;
  textColor: string;
  mutedTextColor: string;
  buttonColor: string;
  buttonTextColor: string;
  entryBg: string;
  entryFg: string;
};

export type DownloadOptions = {
  url: string;
  destination: string;
  format: DownloadFormat;
  fileNameMode: FileNameMode;
  customName: string;
  extraArgs: string;
};

export type DownloadEvent =
  | { jobId: string; type: "started"; message: string }
  | { jobId: string; type: "stdout"; message: string }
  | { jobId: string; type: "stderr"; message: string }
  | { jobId: string; type: "done"; message: string; code: number | null }
  | { jobId: string; type: "error"; message: string };

export type AppBridge = {
  chooseFolder: () => Promise<string | null>;
  openDownloadsFolder: (folder: string) => Promise<void>;
  startDownload: (options: DownloadOptions) => Promise<{ jobId: string }>;
  cancelDownload: (jobId: string) => Promise<{ cancelled: boolean }>;
  onDownloadEvent: (callback: (event: DownloadEvent) => void) => () => void;
  getDefaultDownloadsFolder: () => Promise<string>;
  getPlatform: () => Promise<string>;
};
