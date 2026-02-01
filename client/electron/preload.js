const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("nexusTodo", {
  platform: process.platform,
  version: process.versions.electron
});

contextBridge.exposeInMainWorld("nexusTodoBridge", {
  request: (options) => ipcRenderer.invoke("api-request", options)
});
