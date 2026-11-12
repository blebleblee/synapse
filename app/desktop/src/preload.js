const { contextBridge, ipcRenderer } = require('electron');

// Expose safe desktop bridge to renderer
contextBridge.exposeInMainWorld('synapseDesktop', {
  isDesktop: true,
  platform: process.platform,
  version: '1.0.0',
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  reloadApp: () => ipcRenderer.send('reload-app'),
  toggleDevTools: () => ipcRenderer.send('toggle-devtools'),
});
