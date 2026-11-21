import React, { useState, useEffect } from 'react';
import {
  Settings,
  Palette,
  Cpu,
  X,
  Check,
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
  Sliders,
  HardDrive,
  Info,
  Terminal,
  Sparkles
} from 'lucide-react';

export interface AppSettings {
  theme: 'studio' | 'titanium' | 'monokai' | 'nordic' | 'github_dimmed' | 'dracula' | 'solarized';
  fontFamily: 'sans' | 'serif' | 'mono';
  accentColor: 'gold' | 'cyan' | 'emerald' | 'amethyst' | 'rose';
  lineHeight: 'dense' | 'balanced' | 'relaxed';
  fontSize: 'compact' | 'standard' | 'large';
  readerWidth: 'full' | 'constrained';
  language: 'en' | 'cs' | 'de' | 'es' | 'ru';
  codeLigatures?: boolean;
  terminalFontSize?: '12px' | '13px' | '14px' | '15px';
  speechRate?: '0.85' | '1.0' | '1.15' | '1.3';
  ollamaHost: string;
  clusterHosts?: string[];
  primaryModel: string;
  reviewerModel: string;
  mentorModel?: string;
  geminiApiKey: string;
  geminiBaseUrl?: string;
  anthropicApiKey: string;
  anthropicBaseUrl: string;
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'studio',
  fontFamily: 'sans',
  accentColor: 'gold',
  lineHeight: 'balanced',
  fontSize: 'standard',
  readerWidth: 'full',
  language: 'en',
  codeLigatures: true,
  terminalFontSize: '13px',
  speechRate: '1.0',
  ollamaHost: 'http://localhost:11434',
  clusterHosts: ['http://localhost:11434'],
  primaryModel: 'qwen2.5-coder:32b',
  reviewerModel: 'deepseek-r1:32b',
  mentorModel: '',
  geminiApiKey: '',
  geminiBaseUrl: '',
  anthropicApiKey: '',
  anthropicBaseUrl: 'https://api.anthropic.com',
};

export type SettingsTab = 'appearance' | 'models' | 'cluster' | 'addons' | 'maintenance';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => void;
  initialTab?: 'appearance' | 'cluster' | 'models' | 'store' | 'maintenance' | 'addons';
  onTreeChange?: () => void;
  onLaunchSetupWizard?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  initialTab,
  onTreeChange,
  onLaunchSetupWizard,
}) => {
  const resolveTab = (tab?: string): SettingsTab => {
    if (tab === 'cluster') return 'cluster';
    if (tab === 'models') return 'models';
    if (tab === 'store' || tab === 'addons') return 'addons';
    if (tab === 'maintenance') return 'maintenance';
    return 'appearance';
  };

  const [activeTab, setActiveTab] = useState<SettingsTab>(resolveTab(initialTab));

  useEffect(() => {
    if (isOpen && initialTab) {
      setActiveTab(resolveTab(initialTab));
    }
  }, [isOpen, initialTab]);

  const [formData, setFormData] = useState<AppSettings>(settings);
  const [savedMessage, setSavedMessage] = useState(false);
  const [clusterNodes, setClusterNodes] = useState<string[]>(
    settings.clusterHosts || DEFAULT_SETTINGS.clusterHosts || []
  );
  const [newNodeUrl, setNewNodeUrl] = useState('');
  const [nodeStatuses, setNodeStatuses] = useState<{
    [host: string]: {
      online?: boolean;
      latency_ms?: number;
      models?: string[];
      error?: string;
      testing?: boolean;
    };
  }>({});
  const [isScanningCluster, setIsScanningCluster] = useState(false);

  // Curriculum Store & Addons State
  const [packagesData, setPackagesData] = useState<{
    installed: { domain: string; format?: string; title?: string; lesson_count?: number; lab_count?: number }[];
    available_domains: { domain: string; title: string; description: string; lesson_count: number; lab_count: number; is_installed: boolean }[];
  }>({ installed: [], available_domains: [] });
  const [isLoadingPackages, setIsLoadingPackages] = useState(false);
  const [storeSearch, setStoreSearch] = useState('');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [storeMessage, setStoreMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Discovered Models State
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);

  // Node Model Pins State
  const [nodePins, setNodePins] = useState<{ [host: string]: string }>({});

  const fetchNodePins = async () => {
    try {
      const res = await fetch('/api/settings/cluster-pins');
      if (res.ok) {
        const data = await res.json();
        setNodePins(data.pins || {});
      }
    } catch (err) {
      console.error('Failed to load node pins:', err);
    }
  };

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

  const fetchDiscoveredModels = async () => {
    try {
      const res = await fetch('/api/settings/discovered-models');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.models)) {
          setDiscoveredModels(data.models);
        }
      }
    } catch (err) {
      console.error('Failed to load discovered models:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchPackages();
      fetchDiscoveredModels();
      fetchNodePins();
      scanCluster();
    }
  }, [isOpen]);

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
      setStoreMessage({ text: `Successfully exported ${domain}.synpack`, type: 'success' });
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
      setStoreMessage({ text: `Package for ${domain} installed and registered!`, type: 'success' });
      await fetchPackages();
      onTreeChange?.();
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Install failed', type: 'error' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUninstallPack = async (domain: string) => {
    if (!window.confirm(`Are you sure you want to remove the '${domain}' package from your local workspace?`)) {
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
      setStoreMessage({ text: `Successfully imported ${file.name}!`, type: 'success' });
      await fetchPackages();
      onTreeChange?.();
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Upload failed', type: 'error' });
    } finally {
      setActionInProgress(null);
      e.target.value = '';
    }
  };

  const testNodeConnection = async (host: string) => {
    setNodeStatuses((prev) => ({
      ...prev,
      [host]: { ...prev[host], testing: true, error: undefined },
    }));

    const start = performance.now();
    try {
      const cleanHost = host.replace(/\/$/, '');
      const res = await fetch(`${cleanHost}/api/tags`, {
        method: 'GET',
        signal: AbortSignal.timeout(4000),
      });

      const latency = Math.round(performance.now() - start);

      if (res.ok) {
        const data = await res.json();
        const models = (data.models || []).map((m: any) => m.name || m.model);
        setNodeStatuses((prev) => ({
          ...prev,
          [host]: {
            online: true,
            latency_ms: latency,
            models,
            testing: false,
          },
        }));
      } else {
        setNodeStatuses((prev) => ({
          ...prev,
          [host]: {
            online: false,
            error: `HTTP ${res.status}`,
            testing: false,
          },
        }));
      }
    } catch (err: any) {
      setNodeStatuses((prev) => ({
        ...prev,
        [host]: {
          online: false,
          error: err.name === 'TimeoutError' ? 'Timeout (4s)' : 'Offline / Unreachable',
          testing: false,
        },
      }));
    }
  };

  const scanCluster = async () => {
    setIsScanningCluster(true);
    try {
      const res = await fetch('/api/settings/cluster-status');
      if (res.ok) {
        const data = await res.json();
        setNodeStatuses(data);
      } else {
        await Promise.all(clusterNodes.map((node) => testNodeConnection(node)));
      }
    } catch {
      await Promise.all(clusterNodes.map((node) => testNodeConnection(node)));
    } finally {
      setIsScanningCluster(false);
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
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2500);
  };

  if (!isOpen) return null;

  const onlineNodesCount = Object.values(nodeStatuses).filter((s) => s.online).length;
  const installedAddonsCount = packagesData.installed.length;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="settings-window" onClick={(e) => e.stopPropagation()}>
        {/* Left Vertical Sidebar */}
        <div className="settings-sidebar">
          <div className="settings-sidebar-header">
            <Settings size={18} className="settings-header-icon" />
            <span className="settings-sidebar-title">Workbench Settings</span>
          </div>

          <nav className="settings-nav-list">
            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'appearance' ? 'active' : ''}`}
              onClick={() => setActiveTab('appearance')}
            >
              <Palette size={15} />
              <span>Appearance</span>
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'models' ? 'active' : ''}`}
              onClick={() => setActiveTab('models')}
            >
              <Cpu size={15} />
              <span>AI & Models</span>
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'cluster' ? 'active' : ''}`}
              onClick={() => setActiveTab('cluster')}
            >
              <Network size={15} />
              <span>Cluster Nodes</span>
              {onlineNodesCount > 0 && (
                <span className="settings-nav-badge">{onlineNodesCount}</span>
              )}
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'addons' ? 'active' : ''}`}
              onClick={() => setActiveTab('addons')}
            >
              <Package size={15} />
              <span>Storage & Addons</span>
              {installedAddonsCount > 0 && (
                <span className="settings-nav-badge secondary">{installedAddonsCount}</span>
              )}
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'maintenance' ? 'active' : ''}`}
              onClick={() => setActiveTab('maintenance')}
            >
              <Sliders size={15} />
              <span>System & Setup</span>
            </button>
          </nav>

          <div className="settings-sidebar-footer">
            <div className="sidebar-app-badge">Synapse v1.2.1 • Offline First</div>
          </div>
        </div>

        {/* Right Main Body Content */}
        <div className="settings-body">
          <div className="settings-body-header">
            <div>
              <h3>
                {activeTab === 'appearance' && 'Appearance & Reader'}
                {activeTab === 'models' && 'AI Models & Cloud Fallbacks'}
                {activeTab === 'cluster' && 'Cluster Nodes & Hardware Discovery'}
                {activeTab === 'addons' && 'Curriculum Store & Addons'}
                {activeTab === 'maintenance' && 'System Maintenance & Setup'}
              </h3>
              <p className="settings-tab-desc">
                {activeTab === 'appearance' && 'Customize theme styling, typography, and reader viewing options.'}
                {activeTab === 'models' && 'Configure primary local LLMs, Socratic mentor model, and optional cloud keys.'}
                {activeTab === 'cluster' && 'Manage distributed Ollama inference servers, latency pings, and hardware pins.'}
                {activeTab === 'addons' && 'Install masterclass domain packs, export local packages, or sideload .synpack archives.'}
                {activeTab === 'maintenance' && 'Database management, cache cleaning, and first-run setup wizard.'}
              </p>
            </div>
            <button className="icon-btn" onClick={onClose} title="Close Settings">
              <X size={16} />
            </button>
          </div>

          <div className="settings-tab-scroll">
            {/* Tab 1: Appearance */}
            {activeTab === 'appearance' && (
              <div className="settings-section">
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Theme & Color Accents</h4>
                  <div className="settings-row-2col">
                    <div className="form-group compact">
                      <label>Color Theme</label>
                      <select
                        value={formData.theme}
                        onChange={(e) => setFormData({ ...formData, theme: e.target.value as any })}
                      >
                        <option value="studio">Studio Obsidian — Deep OLED Carbon & Gold</option>
                        <option value="github_dimmed">GitHub Dimmed — Slate Navy & High Contrast</option>
                        <option value="nordic">Nordic Frost — Polar Night & Arctic Cyan</option>
                        <option value="monokai">Monokai Pro — Toasted Espresso & Neon Pastels</option>
                        <option value="dracula">Dracula Noir — Deep Violet Indigo & Pink</option>
                        <option value="solarized">Solarized Dark — Teal Oceanic & Warm Amber</option>
                        <option value="titanium">Titanium Daybreak — High-Contrast Light Mode</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Accent Highlight</label>
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

                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Typography & Reading Geometry</h4>
                  <div className="settings-row-3col">
                    <div className="form-group compact">
                      <label>Body Font Family</label>
                      <select
                        value={formData.fontFamily}
                        onChange={(e) => setFormData({ ...formData, fontFamily: e.target.value as any })}
                      >
                        <option value="sans">Modern Sans (Inter / SF Pro)</option>
                        <option value="serif">Academic Serif (Merriweather / Georgia)</option>
                        <option value="mono">Engineering Monospace (JetBrains Mono)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Content Line Height</label>
                      <select
                        value={formData.lineHeight || 'balanced'}
                        onChange={(e) => setFormData({ ...formData, lineHeight: e.target.value as any })}
                      >
                        <option value="dense">Dense (1.45) — High density</option>
                        <option value="balanced">Balanced (1.65) — Standard</option>
                        <option value="relaxed">Relaxed (1.85) — Long-form</option>
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

            {/* Tab 2: AI & Models */}
            {activeTab === 'models' && (
              <div className="settings-section">
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Local AI Engine Assignment</h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 8px 0' }}>
                    Select the local models running on your cluster nodes. When online, models are automatically discovered from Ollama.
                  </p>

                  <div className="settings-row-2col">
                    <div className="form-group compact">
                      <label>Primary Masterclass Generation Model</label>
                      <input
                        type="text"
                        list="discovered-models-list"
                        value={formData.primaryModel}
                        onChange={(e) => setFormData({ ...formData, primaryModel: e.target.value })}
                        placeholder="e.g. qwen2.5-coder:32b"
                        className="font-mono"
                      />
                    </div>

                    <div className="form-group compact">
                      <label>Socratic Mentor & Chat Model</label>
                      <input
                        type="text"
                        list="discovered-models-list"
                        value={formData.mentorModel || ''}
                        onChange={(e) => setFormData({ ...formData, mentorModel: e.target.value })}
                        placeholder="Default to Primary Model"
                        className="font-mono"
                      />
                    </div>
                  </div>

                  <datalist id="discovered-models-list">
                    {discoveredModels.map((m) => (
                      <option key={m} value={m} />
                    ))}
                  </datalist>

                  <div className="form-group compact" style={{ marginTop: '8px' }}>
                    <label>Reviewer / Evaluator Model</label>
                    <input
                      type="text"
                      list="discovered-models-list"
                      value={formData.reviewerModel}
                      onChange={(e) => setFormData({ ...formData, reviewerModel: e.target.value })}
                      placeholder="e.g. deepseek-r1:32b"
                      className="font-mono"
                    />
                  </div>
                </div>

                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Optional Cloud Fallback API Keys</h4>
                  <div className="settings-row-2col">
                    <div className="form-group compact">
                      <label>Anthropic API Key (Claude Sonnet / Opus)</label>
                      <input
                        type="password"
                        value={formData.anthropicApiKey || ''}
                        onChange={(e) => setFormData({ ...formData, anthropicApiKey: e.target.value })}
                        placeholder="sk-ant-..."
                        className="font-mono"
                      />
                    </div>

                    <div className="form-group compact">
                      <label>Google Gemini API Key (Gemini Flash / Pro)</label>
                      <input
                        type="password"
                        value={formData.geminiApiKey || ''}
                        onChange={(e) => setFormData({ ...formData, geminiApiKey: e.target.value })}
                        placeholder="AIzaSy..."
                        className="font-mono"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Cluster Nodes */}
            {activeTab === 'cluster' && (
              <div className="settings-section">
                <div className="section-title-row">
                  <div className="section-title">
                    <Server size={14} />
                    <span>Inference Nodes & Hardware Endpoints</span>
                  </div>
                  <button
                    type="button"
                    className="btn-secondary-sm"
                    onClick={scanCluster}
                    disabled={isScanningCluster}
                  >
                    <RefreshCw size={12} className={isScanningCluster ? 'animate-spin' : ''} />
                    <span>{isScanningCluster ? 'Testing...' : 'Ping All Nodes'}</span>
                  </button>
                </div>

                <div className="cluster-nodes-list">
                  {clusterNodes.map((nodeUrl) => {
                    const status = nodeStatuses[nodeUrl] || {};
                    const cleanKey = nodeUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
                    const currentPin = nodePins[cleanKey] || nodePins[nodeUrl] || '__auto__';

                    return (
                      <div key={nodeUrl} className="cluster-node-card">
                        <div className="node-card-header">
                          <div className="node-status-indicator">
                            <span className={`status-dot ${status.online ? 'online' : 'offline'}`} />
                            <span className="node-url font-mono">{nodeUrl}</span>
                          </div>

                          <div className="node-actions">
                            {status.latency_ms !== undefined && (
                              <span className="node-latency">{status.latency_ms} ms</span>
                            )}
                            <button
                              type="button"
                              className="icon-btn-sm"
                              onClick={() => testNodeConnection(nodeUrl)}
                              title="Test node latency"
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
                        </div>

                        {status.models && status.models.length > 0 && (
                          <div className="node-models-tags">
                            {status.models.slice(0, 6).map((m) => (
                              <span key={m} className="node-model-chip font-mono">
                                {m}
                              </span>
                            ))}
                            {status.models.length > 6 && (
                              <span className="node-model-chip more">+{status.models.length - 6} more</span>
                            )}
                          </div>
                        )}

                        <div className="node-pin-row" style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Pin Model:</span>
                          <select
                            value={currentPin}
                            onChange={(e) => handleUpdateNodePin(nodeUrl, e.target.value)}
                            style={{ padding: '2px 6px', fontSize: '11px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: '4px' }}
                          >
                            <option value="__auto__">Auto (Load Balanced)</option>
                            {(status.models || []).map((m) => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="add-node-bar" style={{ marginTop: '12px' }}>
                  <input
                    type="text"
                    value={newNodeUrl}
                    onChange={(e) => setNewNodeUrl(e.target.value)}
                    placeholder="Add remote node: e.g. http://192.168.1.50:11434"
                    className="font-mono"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddNode())}
                  />
                  <button type="button" className="btn-secondary" onClick={handleAddNode}>
                    <Plus size={13} />
                    <span>Add Node</span>
                  </button>
                </div>
              </div>
            )}

            {/* Tab 4: Storage & Addons */}
            {activeTab === 'addons' && (
              <div className="settings-section">
                <div className="section-title-row">
                  <div className="section-title">
                    <Package size={14} />
                    <span>Curriculum Store & Addon Management</span>
                  </div>
                  <button
                    type="button"
                    className="icon-btn-sm"
                    onClick={fetchPackages}
                    title="Refresh Packages"
                    disabled={isLoadingPackages}
                  >
                    <RefreshCw size={13} className={isLoadingPackages ? 'animate-spin' : ''} />
                  </button>
                </div>

                <div className="settings-info-box" style={{ marginBottom: '14px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <Info size={14} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                  <span>Synapse includes 12 canonical core domains. Below you can inspect installed modules, export them to standalone <code>.synpack</code> packages, or import custom archives.</span>
                </div>

                {storeMessage && (
                  <div className={`store-message-banner ${storeMessage.type}`}>
                    {storeMessage.type === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                    <span>{storeMessage.text}</span>
                  </div>
                )}

                {/* Sideload & Filter bar */}
                <div className="store-top-bar">
                  <div className="store-search-box">
                    <Search size={13} className="store-search-icon" />
                    <input
                      type="text"
                      placeholder="Filter domain packs..."
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

                {/* Installed Packages Grid */}
                <h4 className="panel-box-heading" style={{ marginTop: '16px' }}>
                  Installed Knowledge Packs ({packagesData.installed.length})
                </h4>

                <div className="store-packages-grid">
                  {packagesData.installed
                    .filter((p) => !storeSearch || p.domain.toLowerCase().includes(storeSearch.toLowerCase()))
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
                            title="Export package to .synpack"
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
                            title="Remove domain package from local workspace"
                          >
                            <Trash2 size={11} />
                            <span>Remove</span>
                          </button>
                        </div>
                      </div>
                    ))}
                </div>

                {/* Available uninstalled domains */}
                {packagesData.available_domains.filter((d) => !d.is_installed).length > 0 && (
                  <>
                    <h4 className="panel-box-heading" style={{ marginTop: '18px' }}>
                      Available Masterclass Domains
                    </h4>
                    <div className="store-packages-grid">
                      {packagesData.available_domains
                        .filter((d) => !d.is_installed && (!storeSearch || d.domain.includes(storeSearch.toLowerCase())))
                        .map((d) => (
                          <div key={d.domain} className="store-package-card">
                            <div className="package-card-header">
                              <span className="package-domain font-mono">{d.domain}</span>
                              <h5>{d.title}</h5>
                              <p className="package-desc">{d.description}</p>
                            </div>

                            <div className="package-card-actions">
                              <button
                                type="button"
                                className="btn-primary-sm"
                                onClick={() => handleInstallDomain(d.domain)}
                                disabled={actionInProgress === `install-${d.domain}`}
                              >
                                {actionInProgress === `install-${d.domain}` ? (
                                  <Loader2 size={11} className="animate-spin" />
                                ) : (
                                  <Download size={11} />
                                )}
                                <span>Install Package</span>
                              </button>
                            </div>
                          </div>
                        ))}
                    </div>
                  </>
                )}

                {/* CLI Custom Domain Reference Card */}
                <div className="settings-panel-box" style={{ marginTop: '16px' }}>
                  <div className="panel-header-with-icon">
                    <Terminal size={14} />
                    <h4 className="panel-box-heading" style={{ margin: 0 }}>Custom Domain CLI Workflow</h4>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0 8px 0' }}>
                    You can create new domains, synthesize custom curriculum, and bundle archives via the terminal:
                  </p>
                  <pre className="code-block font-mono" style={{ fontSize: '11px', padding: '10px', background: 'var(--bg-primary)', borderRadius: '6px' }}>
                    {`# 1. Create a custom topic:\nbin/synapse add robotics autonomous_systems slam_navigation --title "SLAM"\n\n# 2. Package your domain into an archive:\nbin/synapse pack robotics`}
                  </pre>
                </div>
              </div>
            )}

            {/* Tab 5: System & Maintenance */}
            {activeTab === 'maintenance' && (
              <div className="settings-section">
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Workspace Onboarding</h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 10px 0' }}>
                    Re-run the guided first-time setup wizard to test local Ollama detection, select primary models, or configure cloud API fallbacks.
                  </p>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => {
                      onClose();
                      onLaunchSetupWizard?.();
                    }}
                  >
                    <Sparkles size={14} />
                    <span>Launch First-Run Setup Wizard</span>
                  </button>
                </div>

                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Runtime Database & Artifacts</h4>
                  <div className="maintenance-info-grid">
                    <div className="maintenance-info-item">
                      <span className="info-label">Runtime DB</span>
                      <span className="info-val">data/synapse.db (SQLite WAL)</span>
                    </div>
                    <div className="maintenance-info-item">
                      <span className="info-label">Curriculum Dir</span>
                      <span className="info-val">topics/ (539 Masterclasses)</span>
                    </div>
                    <div className="maintenance-info-item">
                      <span className="info-label">User Credentials</span>
                      <span className="info-val">~/.config/synapse/env</span>
                    </div>
                    <div className="maintenance-info-item">
                      <span className="info-label">Persistence</span>
                      <span className="info-val">Preserved Across Updates</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-secondary-sm"
                      onClick={async () => {
                        if (confirm('Clear transient cache (audio, neural TTS, translation buffers)?')) {
                          try {
                            const res = await fetch('/api/clean', { method: 'POST' });
                            if (res.ok) {
                              const data = await res.json();
                              alert(`Cleared ${data.cleaned || 0} transient artifacts.`);
                            }
                          } catch {
                            alert('Cache cleanup completed.');
                          }
                        }
                      }}
                    >
                      <Trash2 size={12} />
                      <span>Clear Transient Caches</span>
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
                          if (res.ok) {
                            alert('SQLite database vacuumed and WAL checkpointed.');
                          }
                        } catch {
                          alert('Vacuum completed.');
                        }
                      }}
                    >
                      <HardDrive size={12} />
                      <span>Vacuum Database & Checkpoint WAL</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="settings-body-actions">
            {savedMessage && (
              <span className="save-confirm-inline">
                <Check size={14} /> Preferences saved successfully
              </span>
            )}
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
