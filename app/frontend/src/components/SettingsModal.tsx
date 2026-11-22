import React, { useState, useEffect } from 'react';
import { DEFAULT_SETTINGS, type AppSettings, type SettingsTab } from './settingsDefaults';
import { useEscapeToClose } from '../utils/useEscapeToClose';
import {
  Settings,
  Palette,
  Cpu,
  X,
  Plus,
  Trash2,
  RefreshCw,
  Package,
  Download,
  Upload,
  CheckCircle,
  AlertCircle,
  Loader2,
  Search,
  Server,
  Network,
  HardDrive,
  Terminal,
  Sparkles,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  Power
} from 'lucide-react';


interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => void;
  initialTab?: string;
  onTreeChange?: () => void;
  onLaunchSetupWizard?: () => void;
}

type NodeStatus = {
  online?: boolean;
  latency_ms?: number;
  models?: string[];
  error?: string;
  testing?: boolean;
};

const uniqueHosts = (hosts: string[]) =>
  Array.from(new Set(hosts.map((h) => h.trim().replace(/\/$/, '')).filter(Boolean)));

// Nodes are probed by the backend: Ollama refuses browser requests from
// other origins, and the answer comes back under the host name as typed.
async function probeStatuses(list: string[]): Promise<Record<string, NodeStatus>> {
  const out: Record<string, NodeStatus> = {};
  try {
    const res = await fetch(`/api/settings/cluster-status?hosts=${encodeURIComponent(list.join(','))}`);
    const data = res.ok ? await res.json() : {};
    const detail = res.ok ? undefined : (await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`;
    list.forEach((h) => {
      const s = data[h];
      out[h] = s
        ? { online: s.online, latency_ms: s.latency_ms ?? undefined, models: s.models || [], testing: false, error: s.online ? undefined : 'Offline' }
        : { online: false, testing: false, error: detail || 'Offline' };
    });
  } catch {
    list.forEach((h) => { out[h] = { online: false, testing: false, error: 'Backend unreachable' }; });
  }
  return out;
}

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    return res.ok ? ((await res.json()) as T) : null;
  } catch (err) {
    console.error(`Failed to load ${url}:`, err);
    return null;
  }
}

// Mounted only while open: each opening starts from the saved settings
// (unsaved edits are dropped on close) and loads fresh data.
export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, ...props }) =>
  isOpen ? <SettingsPanel {...props} /> : null;

const SettingsPanel: React.FC<Omit<SettingsModalProps, 'isOpen'>> = ({
  onClose,
  settings,
  onSaveSettings,
  initialTab,
  onTreeChange,
  onLaunchSetupWizard,
}) => {
  useEscapeToClose(onClose);
  const resolveTab = (tab?: string): SettingsTab => {
    if (tab === 'models' || tab === 'cluster' || tab === 'ai') return 'ai';
    if (tab === 'store' || tab === 'storage' || tab === 'maintenance' || tab === 'addons') return 'storage';
    return 'appearance';
  };

  const [activeTab, setActiveTab] = useState<SettingsTab>(resolveTab(initialTab));
  const [providerMode, setProviderMode] = useState<'local' | 'cloud'>(() => {
    return settings.anthropicApiKey || settings.geminiApiKey ? 'cloud' : 'local';
  });

  const [formData, setFormData] = useState<AppSettings>(settings);
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showClusterAdvanced, setShowClusterAdvanced] = useState(true);

  const [clusterNodes, setClusterNodes] = useState<string[]>(
    settings.clusterHosts || DEFAULT_SETTINGS.clusterHosts || []
  );
  const [newNodeUrl, setNewNodeUrl] = useState('');
  // Hosts checked when the dialog opens; they show as "testing" until answered.
  const [initialHosts] = useState(() => uniqueHosts([settings.ollamaHost, ...(settings.clusterHosts || DEFAULT_SETTINGS.clusterHosts || [])]));
  const [nodeStatuses, setNodeStatuses] = useState<Record<string, NodeStatus>>(
    () => Object.fromEntries(initialHosts.map((h) => [h, { testing: true }])),
  );
  const [isScanningCluster, setIsScanningCluster] = useState(true);

  // Curriculum Store & Addons State
  const [packagesData, setPackagesData] = useState<{
    installed: { domain: string; format?: string; title?: string; lesson_count?: number; lab_count?: number }[];
    available_domains: { domain: string; title: string; description: string; lesson_count: number; lab_count: number; is_installed: boolean }[];
  }>({ installed: [], available_domains: [] });
  const [isLoadingPackages, setIsLoadingPackages] = useState(true);
  const [storeSearch, setStoreSearch] = useState('');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [storeMessage, setStoreMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Discovered Models State
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);

  // Options for a model <select>. The saved model always stays listed, so the
  // dropdown never shows a different model than the one the app will use.
  const modelOptions = (current: string | undefined, required = true) => {
    const missing = current && !discoveredModels.includes(current);
    return (
      <>
        {missing && (
          <option value={current}>
            {current}{discoveredModels.length > 0 ? ' (not found on any node)' : ''}
          </option>
        )}
        {!current && required && <option value="">Select a model</option>}
        {discoveredModels.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </>
    );
  };

  // Node Model Pins State
  const [nodePins, setNodePins] = useState<{ [host: string]: string }>({});

  const handleUpdateNodePin = async (host: string, modelName: string) => {
    const cleanHost = host.replace(/^https?:\/\//, '').replace(/\/$/, '');
    const updated = { ...nodePins };
    if (!modelName || modelName === '__auto__') {
      delete updated[cleanHost];
      delete updated[host];
    } else {
      updated[cleanHost] = modelName;
    }
    setNodePins(updated);

    try {
      await fetch('/api/settings/cluster-pins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pins: updated })
      });
    } catch (err) {
      console.error('Failed to save cluster pin:', err);
    }
  };

  const fetchPackages = async () => {
    setIsLoadingPackages(true);
    try {
      const res = await fetch('/api/packages');
      if (res.ok) {
        const data = await res.json();
        setPackagesData(data);
      }
    } catch (err) {
      console.error('Failed to load packages:', err);
    } finally {
      setIsLoadingPackages(false);
    }
  };

  const probeHosts = async (hosts: string[]) => {
    const list = uniqueHosts(hosts);
    if (list.length === 0) return;
    setNodeStatuses((prev) => {
      const next = { ...prev };
      list.forEach((h) => { next[h] = { ...prev[h], testing: true, error: undefined }; });
      return next;
    });
    const result = await probeStatuses(list);
    setNodeStatuses((prev) => ({ ...prev, ...result }));
  };

  const testNodeConnection = (host: string) => probeHosts([host]);

  const scanCluster = async () => {
    setIsScanningCluster(true);
    try {
      await probeHosts([formData.ollamaHost, ...clusterNodes]);
    } finally {
      setIsScanningCluster(false);
    }
  };

  // Opening load. Buttons reuse the handlers above; this runs once per opening.
  useEffect(() => {
    let live = true;
    fetchJson<typeof packagesData>('/api/packages').then((data) => {
      if (!live) return;
      if (data) setPackagesData(data);
      setIsLoadingPackages(false);
    });
    fetchJson<{ models?: unknown }>('/api/settings/discovered-models').then((data) => {
      if (live && data && Array.isArray(data.models)) setDiscoveredModels(data.models as string[]);
    });
    fetchJson<{ pins?: Record<string, string> }>('/api/settings/cluster-pins').then((data) => {
      if (live && data) setNodePins(data.pins || {});
    });
    probeStatuses(initialHosts).then((result) => {
      if (!live) return;
      setNodeStatuses((prev) => ({ ...prev, ...result }));
      setIsScanningCluster(false);
    });
    return () => { live = false; };
  }, [initialHosts]);

  const handleExportPack = async (domain: string) => {
    setActionInProgress(`export-${domain}`);
    setStoreMessage(null);
    try {
      const res = await fetch(`/api/packages/export?domain=${encodeURIComponent(domain)}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Package export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${domain}.synpack`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setStoreMessage({ text: `Exported ${domain}.synpack successfully`, type: 'success' });
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Export failed', type: 'error' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleInstallDomain = async (domain: string) => {
    setActionInProgress(`install-${domain}`);
    setStoreMessage(null);
    try {
      const res = await fetch(`/api/packages/install?domain=${encodeURIComponent(domain)}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Package installation failed');
      setStoreMessage({ text: `Package for ${domain} installed and verified!`, type: 'success' });
      await fetchPackages();
      onTreeChange?.();
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Install failed', type: 'error' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUninstallPack = async (domain: string) => {
    if (!window.confirm(`Are you sure you want to remove '${domain}' from your local workspace?`)) {
      return;
    }
    setActionInProgress(`uninstall-${domain}`);
    setStoreMessage(null);
    try {
      const res = await fetch(`/api/packages/${encodeURIComponent(domain)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Package uninstall failed');
      setStoreMessage({ text: `Removed ${domain} package.`, type: 'success' });
      await fetchPackages();
      onTreeChange?.();
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Uninstall failed', type: 'error' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setActionInProgress('uploading');
    setStoreMessage(null);
    const data = new FormData();
    data.append('file', file);

    try {
      const res = await fetch('/api/packages/install', {
        method: 'POST',
        body: data
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Package import failed');
      }
      setStoreMessage({ text: `Imported ${file.name} successfully!`, type: 'success' });
      await fetchPackages();
      onTreeChange?.();
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Upload failed', type: 'error' });
    } finally {
      setActionInProgress(null);
      e.target.value = '';
    }
  };

  const handleAddNode = () => {
    let url = newNodeUrl.trim();
    if (!url) return;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'http://' + url;
    }
    url = url.replace(/\/$/, '');
    if (!clusterNodes.includes(url)) {
      const updated = [...clusterNodes, url];
      setClusterNodes(updated);
      setFormData((prev) => ({ ...prev, clusterHosts: updated }));
      testNodeConnection(url);
    }
    setNewNodeUrl('');
  };

  const handleRemoveNode = (hostToRemove: string) => {
    const updated = clusterNodes.filter((h) => h !== hostToRemove);
    setClusterNodes(updated);
    setFormData((prev) => ({ ...prev, clusterHosts: updated }));
    setNodeStatuses((prev) => {
      const next = { ...prev };
      delete next[hostToRemove];
      return next;
    });
  };

  const handleSave = () => {
    const updated = {
      ...formData,
      clusterHosts: clusterNodes,
      ollamaHost: clusterNodes[0] || formData.ollamaHost,
    };
    onSaveSettings(updated);
    onClose();
  };


  const currentHostStatus = nodeStatuses[formData.ollamaHost] || {};

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="settings-window" onClick={(e) => e.stopPropagation()}>
        {/* Left Vertical Sidebar (Only 3 clean, purposeful tabs) */}
        <div className="settings-sidebar">
          <div className="settings-sidebar-header">
            <Settings size={18} className="settings-header-icon" />
            <span className="settings-sidebar-title">Settings</span>
          </div>

          <nav className="settings-nav-list">
            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'appearance' ? 'active' : ''}`}
              onClick={() => setActiveTab('appearance')}
            >
              <Palette size={16} />
              <span>Appearance</span>
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'ai' ? 'active' : ''}`}
              onClick={() => setActiveTab('ai')}
            >
              <Cpu size={16} />
              <span>AI Engine</span>
              {currentHostStatus.online && (
                <span className="settings-nav-badge">Online</span>
              )}
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'storage' ? 'active' : ''}`}
              onClick={() => setActiveTab('storage')}
            >
              <Package size={16} />
              <span>Curriculum & Packs</span>
              {packagesData.installed.length > 0 && (
                <span className="settings-nav-badge secondary">{packagesData.installed.length}</span>
              )}
            </button>
          </nav>

          <div className="settings-sidebar-footer">
            <div className="sidebar-app-badge">Synapse v1.2.2</div>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="settings-body">
          <div className="settings-body-header">
            <div>
              <h3>
                {activeTab === 'appearance' && 'Appearance & Reading Design'}
                {activeTab === 'ai' && 'AI Engine & Inference Models'}
                {activeTab === 'storage' && 'Curriculum Store & Maintenance'}
              </h3>
              <p className="settings-tab-desc">
                {activeTab === 'appearance' && 'Customize theme palettes, typography sizing, and reader viewing geometry.'}
                {activeTab === 'ai' && 'Manage local Ollama models, distributed LAN GPU workers, or cloud fallback API keys.'}
                {activeTab === 'storage' && 'Manage installed course packs, export .synpack archives, and vacuum local cache.'}
              </p>
            </div>
            <button className="icon-btn" onClick={onClose} title="Close Settings">
              <X size={16} />
            </button>
          </div>

          <div className="settings-tab-scroll">
            {/* TAB 1: APPEARANCE */}
            {activeTab === 'appearance' && (
              <div className="settings-section">
                {/* Visual Color Palette Dropdowns */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Visual Color Palette</h4>
                  <div className="settings-row-2col">
                    <div className="form-group compact">
                      <label>Color Theme</label>
                      <select
                        value={formData.theme}
                        onChange={(e) => setFormData({ ...formData, theme: e.target.value as any })}
                      >
                        <option value="studio">⬛ Studio Obsidian (Dark Carbon & Gold)</option>
                        <option value="github_dimmed">🌑 GitHub Dimmed (Slate Navy & Blue)</option>
                        <option value="nordic">❄️ Nordic Frost (Polar Night & Cyan)</option>
                        <option value="monokai">☕ Monokai Pro (Espresso & Pastels)</option>
                        <option value="dracula">🧛 Dracula Noir (Deep Violet & Pink)</option>
                        <option value="solarized">🌊 Solarized Dark (Teal Oceanic & Amber)</option>
                        <option value="titanium">⚪ Titanium Daybreak (Light & High Contrast)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Accent Color Highlight</label>
                      <select
                        value={formData.accentColor || 'gold'}
                        onChange={(e) => setFormData({ ...formData, accentColor: e.target.value as any })}
                      >
                        <option value="gold">🟡 Amber Gold (#fbbf24)</option>
                        <option value="cyan">🔵 Electric Cyan (#06b6d4)</option>
                        <option value="emerald">🟢 Matrix Emerald (#10b981)</option>
                        <option value="amethyst">🟣 Royal Amethyst (#a855f7)</option>
                        <option value="rose">🔴 Crimson Rose (#f43f5e)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Typography & Sizing */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Typography & Reading Geometry</h4>
                  <div className="settings-row-3col">
                    <div className="form-group compact">
                      <label>Font Family</label>
                      <select
                        value={formData.fontFamily}
                        onChange={(e) => setFormData({ ...formData, fontFamily: e.target.value as any })}
                      >
                        <option value="sans">Sans (Inter / SF Pro)</option>
                        <option value="serif">Serif (Merriweather)</option>
                        <option value="mono">Monospace (JetBrains Mono)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Reading Font Size</label>
                      <select
                        value={formData.fontSize || 'standard'}
                        onChange={(e) => setFormData({ ...formData, fontSize: e.target.value as any })}
                      >
                        <option value="compact">Compact (13px)</option>
                        <option value="standard">Standard (15px)</option>
                        <option value="large">Large (17px)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Line Spacing</label>
                      <select
                        value={formData.lineHeight || 'balanced'}
                        onChange={(e) => setFormData({ ...formData, lineHeight: e.target.value as any })}
                      >
                        <option value="dense">Dense (1.45)</option>
                        <option value="balanced">Balanced (1.65)</option>
                        <option value="relaxed">Relaxed (1.85)</option>
                      </select>
                    </div>
                  </div>

                  {/* Live Typography Preview Box */}
                  <div className="typography-preview-box">
                    <p
                      className="preview-sample-text"
                      style={{
                        fontFamily: formData.fontFamily === 'serif' ? 'var(--font-serif)' : formData.fontFamily === 'mono' ? 'var(--font-mono)' : 'var(--font-sans)',
                        fontSize: formData.fontSize === 'compact' ? '13px' : formData.fontSize === 'large' ? '17px' : '15px',
                        lineHeight: formData.lineHeight === 'dense' ? 1.45 : formData.lineHeight === 'relaxed' ? 1.85 : 1.65,
                      }}
                    >
                      "The first principle of engineering is that you must not fool yourself, and you are the easiest person to fool."
                    </p>
                  </div>

                  <div className="settings-row-2col" style={{ marginTop: '12px' }}>
                    <div className="form-group compact">
                      <label>Reader View Width</label>
                      <select
                        value={formData.readerWidth || 'full'}
                        onChange={(e) => setFormData({ ...formData, readerWidth: e.target.value as any })}
                      >
                        <option value="full">Full Width (Adapts to Window)</option>
                        <option value="constrained">Focused Editorial Column (780px Max)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Default Reading Language</label>
                      <select
                        value={formData.language || 'en'}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value as any })}
                      >
                        <option value="en">English (Original Curriculum)</option>
                        <option value="cs">Čeština (Czech)</option>
                        <option value="de">Deutsch (German)</option>
                        <option value="es">Español (Spanish)</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: AI ENGINE (Unified Local vs Cloud) */}
            {activeTab === 'ai' && (
              <div className="settings-section">
                {/* Segmented Mode Switcher */}
                <div className="provider-mode-segmented">
                  <button
                    type="button"
                    className={`provider-segment-btn ${providerMode === 'local' ? 'active' : ''}`}
                    onClick={() => setProviderMode('local')}
                  >
                    <Server size={15} />
                    <span>Local (Ollama)</span>
                  </button>
                  <button
                    type="button"
                    className={`provider-segment-btn ${providerMode === 'cloud' ? 'active' : ''}`}
                    onClick={() => setProviderMode('cloud')}
                  >
                    <Cpu size={15} />
                    <span>Cloud (Claude, Gemini)</span>
                  </button>
                </div>

                {/* Local Engine Panel */}
                {providerMode === 'local' && (
                  <>
                    <div className="settings-panel-box">
                      <div className="probe-header-row">
                        <div className="probe-host-label">
                          <Server size={14} />
                          <span>Local Ollama Endpoint:</span>
                          <input
                            type="text"
                            value={formData.ollamaHost}
                            onChange={(e) => setFormData({ ...formData, ollamaHost: e.target.value })}
                            className="wizard-input font-mono"
                            style={{ padding: '3px 8px', fontSize: '12px', width: '240px' }}
                          />
                        </div>
                        <button
                          type="button"
                          className="btn-secondary-sm"
                          onClick={() => testNodeConnection(formData.ollamaHost)}
                          disabled={currentHostStatus.testing}
                        >
                          <RefreshCw size={12} className={currentHostStatus.testing ? 'animate-spin' : ''} />
                          <span>{currentHostStatus.testing ? 'Testing...' : 'Test Connection'}</span>
                        </button>
                      </div>

                      <div className="probe-status-row" style={{ marginTop: '8px' }}>
                        {currentHostStatus.online ? (
                          <div className="probe-badge online">
                            <CheckCircle size={13} />
                            <span>Online ({currentHostStatus.latency_ms || 12} ms) • {discoveredModels.length} models detected</span>
                          </div>
                        ) : (
                          <div className="probe-badge offline">
                            <AlertCircle size={13} />
                            <span>Offline or unreachable on {formData.ollamaHost}. Ensure <code>ollama serve</code> is running.</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Standard Dropdowns for Models (No confusing quick chips!) */}
                    <div className="settings-panel-box">
                      <h4 className="panel-box-heading">Active Model Assignment</h4>
                      <div className="settings-row-3col">
                        <div className="form-group compact">
                          <label>Primary Generation Model</label>
                          <select
                            value={formData.primaryModel}
                            onChange={(e) => setFormData({ ...formData, primaryModel: e.target.value })}
                            className="font-mono"
                          >
                            {modelOptions(formData.primaryModel)}
                          </select>
                        </div>

                        <div className="form-group compact">
                          <label>Socratic Mentor Model</label>
                          <select
                            value={formData.mentorModel || ''}
                            onChange={(e) => setFormData({ ...formData, mentorModel: e.target.value })}
                            className="font-mono"
                          >
                            <option value="">Same as primary</option>
                            {modelOptions(formData.mentorModel, false)}
                          </select>
                        </div>
                        <div className="form-group compact">
                          <label>Reviewer / Evaluator Model</label>
                          <select
                            value={formData.reviewerModel}
                            onChange={(e) => setFormData({ ...formData, reviewerModel: e.target.value })}
                            className="font-mono"
                          >
                            {modelOptions(formData.reviewerModel)}
                          </select>
                        </div>
                      </div>

                    </div>

                    {/* Distributed Cluster Nodes (Clean Horizontal Row Layout) */}
                    <div className="settings-panel-box">
                      <div
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
                        onClick={() => setShowClusterAdvanced((prev) => !prev)}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Network size={14} />
                          <h4 className="panel-box-heading" style={{ margin: 0 }}>Distributed Cluster Nodes ({clusterNodes.length})</h4>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <button
                            type="button"
                            className="btn-secondary-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              scanCluster();
                            }}
                            disabled={isScanningCluster}
                          >
                            <RefreshCw size={11} className={isScanningCluster ? 'animate-spin' : ''} />
                            <span>{isScanningCluster ? 'Testing...' : 'Ping Nodes'}</span>
                          </button>
                          <button type="button" className="icon-btn-sm">
                            {showClusterAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>
                        </div>
                      </div>

                      {showClusterAdvanced && (
                        <div style={{ marginTop: '12px' }}>
                          <div className="cluster-nodes-list">
                            {clusterNodes.map((nodeUrl) => {
                              const status = nodeStatuses[nodeUrl] || {};
                              const cleanKey = nodeUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
                              const currentPin = nodePins[cleanKey] || nodePins[nodeUrl] || '__auto__';

                              return (
                                <div key={nodeUrl} className="cluster-node-row">
                                  <span className={`status-dot ${status.online ? 'online' : 'offline'}`} />
                                  <input
                                    type="text"
                                    value={nodeUrl}
                                    readOnly
                                    className="cluster-node-url-field font-mono"
                                    title={nodeUrl}
                                  />
                                  <div className="node-pin-group">
                                    <span className="node-pin-label">Pin Model:</span>
                                    <select
                                      value={currentPin}
                                      onChange={(e) => handleUpdateNodePin(nodeUrl, e.target.value)}
                                      className="node-pin-select font-mono"
                                    >
                                      <option value="__auto__">Auto (Any Model)</option>
                                      {(status.models || []).map((m) => (
                                        <option key={m} value={m}>{m}</option>
                                      ))}
                                    </select>
                                  </div>
                                  <span className="node-latency">
                                    {status.latency_ms !== undefined ? `${status.latency_ms} ms` : status.online ? 'Ready' : 'Offline'}
                                  </span>
                                  <button
                                    type="button"
                                    className="icon-btn-sm"
                                    onClick={() => testNodeConnection(nodeUrl)}
                                    title="Ping node"
                                  >
                                    <RefreshCw size={11} className={status.testing ? 'animate-spin' : ''} />
                                  </button>
                                  {clusterNodes.length > 1 && (
                                    <button
                                      type="button"
                                      className="icon-btn-sm danger"
                                      onClick={() => handleRemoveNode(nodeUrl)}
                                      title="Remove node"
                                    >
                                      <Trash2 size={11} />
                                    </button>
                                  )}
                                </div>
                              );
                            })}
                          </div>

                          <div className="add-node-bar" style={{ marginTop: '10px' }}>
                            <input
                              type="text"
                              value={newNodeUrl}
                              onChange={(e) => setNewNodeUrl(e.target.value)}
                              placeholder="Add LAN GPU node: e.g. http://192.168.1.50:11434"
                              className="font-mono"
                            />
                            <button type="button" className="btn-secondary" onClick={handleAddNode}>
                              <Plus size={13} />
                              <span>Add Node</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* Cloud Providers Panel */}
                {providerMode === 'cloud' && (
                  <div className="settings-section">
                    <div className="settings-panel-box">
                      <div className="panel-header-with-icon">
                        <Cpu size={15} />
                        <h4 className="panel-box-heading" style={{ margin: 0 }}>Anthropic Claude</h4>
                      </div>

                      <div className="form-group compact" style={{ marginTop: '8px' }}>
                        <label>Anthropic API Key</label>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <input
                            type={showAnthropicKey ? 'text' : 'password'}
                            value={formData.anthropicApiKey || ''}
                            onChange={(e) => setFormData({ ...formData, anthropicApiKey: e.target.value })}
                            placeholder="sk-ant-api03-..."
                            className="font-mono"
                            style={{ flex: 1 }}
                          />
                          <button
                            type="button"
                            className="icon-btn-sm"
                            onClick={() => setShowAnthropicKey((p) => !p)}
                            title={showAnthropicKey ? 'Hide key' : 'Show key'}
                          >
                            {showAnthropicKey ? <EyeOff size={13} /> : <Eye size={13} />}
                          </button>
                        </div>
                      </div>

                      <div className="form-group compact" style={{ marginTop: '8px' }}>
                        <label>Base URL Override (Optional)</label>
                        <input
                          type="text"
                          value={formData.anthropicBaseUrl}
                          onChange={(e) => setFormData({ ...formData, anthropicBaseUrl: e.target.value })}
                          placeholder="https://api.anthropic.com"
                          className="font-mono"
                        />
                      </div>
                    </div>

                    <div className="settings-panel-box">
                      <div className="panel-header-with-icon">
                        <Sparkles size={15} />
                        <h4 className="panel-box-heading" style={{ margin: 0 }}>Google Gemini</h4>
                      </div>

                      <div className="form-group compact" style={{ marginTop: '8px' }}>
                        <label>Gemini API Key</label>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <input
                            type={showGeminiKey ? 'text' : 'password'}
                            value={formData.geminiApiKey || ''}
                            onChange={(e) => setFormData({ ...formData, geminiApiKey: e.target.value })}
                            placeholder="AIzaSy..."
                            className="font-mono"
                            style={{ flex: 1 }}
                          />
                          <button
                            type="button"
                            className="icon-btn-sm"
                            onClick={() => setShowGeminiKey((p) => !p)}
                            title={showGeminiKey ? 'Hide key' : 'Show key'}
                          >
                            {showGeminiKey ? <EyeOff size={13} /> : <Eye size={13} />}
                          </button>
                        </div>
                      </div>

                      <div className="form-group compact" style={{ marginTop: '8px' }}>
                        <label>Base URL Override (Optional)</label>
                        <input
                          type="text"
                          value={formData.geminiBaseUrl || ''}
                          onChange={(e) => setFormData({ ...formData, geminiBaseUrl: e.target.value })}
                          placeholder="https://generativelanguage.googleapis.com"
                          className="font-mono"
                        />
                      </div>
                    </div>

                    <div className="wizard-info-note">
                      Cloud keys are saved securely in your personal local environment configuration (<code>~/.config/synapse/env</code>) and are never sent to external telemetry services.
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: CURRICULUM & STORAGE */}
            {activeTab === 'storage' && (
              <div className="settings-section">
                {/* Masterpack Status Card (No confusing error-prone button when all domains are installed!) */}
                <div className="masterpack-hero-card">
                  <div className="masterpack-info-col">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CheckCircle size={18} style={{ color: '#10b981' }} />
                      <h4>Canonical Master Curriculum (All 12 Core Domains)</h4>
                    </div>
                    <p>
                      {packagesData.installed.length >= 12
                        ? `All 12 core domains are installed locally.`
                        : `${packagesData.installed.length} of 12 domains installed. Download the complete masterpack to unlock all courses offline.`}
                    </p>
                  </div>

                  {packagesData.installed.length < 12 && (
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => handleInstallDomain('complete')}
                      disabled={actionInProgress === 'install-complete'}
                    >
                      {actionInProgress === 'install-complete' ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Download size={13} />
                      )}
                      <span>Download Complete Curriculum (37 MB)</span>
                    </button>
                  )}
                </div>

                {storeMessage && (
                  <div className={`store-message-banner ${storeMessage.type}`}>
                    {storeMessage.type === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                    <span>{storeMessage.text}</span>
                  </div>
                )}

                {/* Filter & Import Bar */}
                <div className="store-top-bar" style={{ marginTop: '14px' }}>
                  <div className="store-search-box">
                    <Search size={13} className="store-search-icon" />
                    <input
                      type="text"
                      placeholder="Filter installed courses..."
                      value={storeSearch}
                      onChange={(e) => setStoreSearch(e.target.value)}
                    />
                  </div>

                  <label className="btn-secondary store-upload-compact-btn" title="Import custom .synpack archive">
                    {actionInProgress === 'uploading' ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Upload size={12} />
                    )}
                    <span>Import .synpack</span>
                    <input type="file" accept=".synpack" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>
                </div>

                {/* Installed Domains Grid (Filtered to prevent 'complete' duplication) */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px' }}>
                  <h4 className="panel-box-heading" style={{ margin: 0 }}>
                    Installed Curriculum Domains ({packagesData.installed.filter((p) => p.domain !== 'complete').length})
                  </h4>
                  <button
                    type="button"
                    className="icon-btn-sm"
                    onClick={fetchPackages}
                    title="Refresh packages"
                    disabled={isLoadingPackages}
                  >
                    <RefreshCw size={12} className={isLoadingPackages ? 'animate-spin' : ''} />
                  </button>
                </div>

                <div className="store-packages-grid">
                  {packagesData.installed
                    .filter((p) => p.domain !== 'complete' && p.domain !== 'synapse_complete_curriculum' && (!storeSearch || p.domain.toLowerCase().includes(storeSearch.toLowerCase())))
                    .map((pkg) => (
                      <div key={pkg.domain} className="store-package-card installed">
                        <div className="package-card-header">
                          <div className="package-badge-row">
                            <span className="package-domain font-mono">{pkg.domain}</span>
                            <span className="package-installed-tag">Installed</span>
                          </div>
                          <h5>{pkg.title || pkg.domain.replace(/_/g, ' ').toUpperCase()}</h5>
                        </div>

                        <div className="package-stats-row">
                          <span>{pkg.lesson_count || 0} Lessons</span>
                          <span>•</span>
                          <span>{pkg.lab_count || 0} Labs</span>
                        </div>

                        <div className="package-card-actions">
                          <button
                            type="button"
                            className="btn-secondary-sm"
                            onClick={() => handleExportPack(pkg.domain)}
                            disabled={actionInProgress === `export-${pkg.domain}`}
                            title="Export to .synpack archive"
                          >
                            {actionInProgress === `export-${pkg.domain}` ? (
                              <Loader2 size={11} className="animate-spin" />
                            ) : (
                              <Download size={11} />
                            )}
                            <span>Export</span>
                          </button>

                          <button
                            type="button"
                            className="btn-secondary-sm danger"
                            onClick={() => handleUninstallPack(pkg.domain)}
                            disabled={actionInProgress === `uninstall-${pkg.domain}`}
                            title="Remove from workspace"
                          >
                            <Trash2 size={11} />
                            <span>Remove</span>
                          </button>
                        </div>
                      </div>
                    ))}
                </div>

                {/* CLI Custom Domain Guide */}
                <div className="settings-panel-box">
                  <div className="panel-header-with-icon">
                    <Terminal size={14} />
                    <h4 className="panel-box-heading" style={{ margin: 0 }}>Custom Domain CLI Workflow</h4>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 8px 0' }}>
                    Author new courses, synthesize curriculum with AI, and package archives via the terminal:
                  </p>
                  <pre className="code-block font-mono" style={{ fontSize: '11px', padding: '10px', background: 'var(--bg-primary)', borderRadius: '6px' }}>
                    {`# 1. Add a new domain/topic:\nbin/synapse add robotics autonomous_systems slam_navigation --title "SLAM"\n\n# 2. Package into a portable .synpack archive:\nbin/synapse pack robotics`}
                  </pre>
                </div>

                {/* Practical Workspace Maintenance */}
                <div className="settings-panel-box">
                  <div className="panel-header-with-icon">
                    <HardDrive size={14} />
                    <h4 className="panel-box-heading" style={{ margin: 0 }}>Workspace Maintenance & Setup</h4>
                  </div>

                  <div style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-secondary-sm"
                      onClick={() => {
                        onClose();
                        onLaunchSetupWizard?.();
                      }}
                    >
                      <Sparkles size={12} />
                      <span>Launch Setup Wizard</span>
                    </button>

                    <button
                      type="button"
                      className="btn-secondary-sm"
                      onClick={async () => {
                        if (confirm('Clear cached narration audio and translations? Chat history is kept.')) {
                          try {
                            const res = await fetch('/api/clean', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ sessions: false, exports: false, caches: true })
                            });
                            if (!res.ok) throw new Error(`Server returned ${res.status}`);
                            const data = await res.json();
                            alert(`Removed ${data.cleaned || 0} cached files.`);
                          } catch (err) {
                            alert(`Clearing the cache failed: ${err instanceof Error ? err.message : err}`);
                          }
                        }
                      }}
                    >
                      <Trash2 size={12} />
                      <span>Clear Transient Cache</span>
                    </button>

                    <button
                      type="button"
                      className="btn-secondary-sm"
                      onClick={async () => {
                        try {
                          const res = await fetch('/api/clean', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ sessions: false, exports: false, db: true })
                          });
                          if (!res.ok) {
                            const data = await res.json().catch(() => ({}));
                            throw new Error(data.detail || `Server returned ${res.status}`);
                          }
                          alert('SQLite database vacuumed and WAL checkpointed.');
                        } catch (err) {
                          alert(`Vacuum failed: ${err instanceof Error ? err.message : err}`);
                        }
                      }}
                    >
                      <HardDrive size={12} />
                      <span>Vacuum SQLite Database</span>
                    </button>

                    <button
                      type="button"
                      className="btn-secondary-sm"
                      style={{ color: '#ef4444', borderColor: '#ef444440' }}
                      onClick={async () => {
                        if (!confirm('Shut down Synapse Workbench server?')) return;
                        try {
                          const res = await fetch('/api/system/shutdown', { method: 'POST' });
                          if (!res.ok) {
                            const data = await res.json().catch(() => ({}));
                            throw new Error(data.detail || `Server returned ${res.status}`);
                          }
                          alert('Synapse Workbench server is shutting down. You may close this browser tab.');
                        } catch (err) {
                          alert(`Shutdown failed: ${err instanceof Error ? err.message : err}`);
                        }
                      }}
                      title="Gracefully stop the local Synapse server process"
                    >
                      <Power size={12} />
                      <span>Shut Down Server</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="settings-body-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="button" className="btn-primary" onClick={handleSave}>
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
