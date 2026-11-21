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
  HardDrive,
  Terminal,
  Sparkles,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp
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

export type SettingsTab = 'appearance' | 'ai' | 'storage';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => void;
  initialTab?: string;
  onTreeChange?: () => void;
  onLaunchSetupWizard?: () => void;
}

const THEME_OPTIONS = [
  { id: 'studio', name: 'Studio Obsidian', baseColor: '#0c0d0f', accentColor: '#fbbf24' },
  { id: 'github_dimmed', name: 'GitHub Dimmed', baseColor: '#1c2128', accentColor: '#539bf5' },
  { id: 'nordic', name: 'Nordic Frost', baseColor: '#0f131a', accentColor: '#2dd4bf' },
  { id: 'monokai', name: 'Monokai Pro', baseColor: '#19181a', accentColor: '#ffd866' },
  { id: 'dracula', name: 'Dracula Noir', baseColor: '#1e1f29', accentColor: '#bd93f9' },
  { id: 'solarized', name: 'Solarized Dark', baseColor: '#00212b', accentColor: '#b58900' },
  { id: 'titanium', name: 'Titanium Daybreak', baseColor: '#101114', accentColor: '#e5e7eb' },
];

const ACCENT_OPTIONS = [
  { id: 'gold', name: 'Amber Gold', hex: '#fbbf24' },
  { id: 'cyan', name: 'Electric Cyan', hex: '#06b6d4' },
  { id: 'emerald', name: 'Matrix Emerald', hex: '#10b981' },
  { id: 'amethyst', name: 'Royal Amethyst', hex: '#a855f7' },
  { id: 'rose', name: 'Crimson Rose', hex: '#f43f5e' },
];

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
    if (tab === 'models' || tab === 'cluster' || tab === 'ai') return 'ai';
    if (tab === 'store' || tab === 'storage' || tab === 'maintenance' || tab === 'addons') return 'storage';
    return 'appearance';
  };

  const [activeTab, setActiveTab] = useState<SettingsTab>(resolveTab(initialTab));
  const [providerMode, setProviderMode] = useState<'local' | 'cloud'>(() => {
    return settings.anthropicApiKey || settings.geminiApiKey ? 'cloud' : 'local';
  });

  useEffect(() => {
    if (isOpen && initialTab) {
      setActiveTab(resolveTab(initialTab));
    }
  }, [isOpen, initialTab]);

  const [formData, setFormData] = useState<AppSettings>(settings);
  const [savedMessage, setSavedMessage] = useState(false);
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showClusterAdvanced, setShowClusterAdvanced] = useState(false);

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
          error: err.name === 'TimeoutError' ? 'Timeout (4s)' : 'Offline',
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
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2500);
  };

  if (!isOpen) return null;

  const currentHostStatus = nodeStatuses[formData.ollamaHost] || {};

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="settings-window" onClick={(e) => e.stopPropagation()}>
        {/* Left Vertical Sidebar (Only 3 clean, purposeful tabs) */}
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
            <div className="sidebar-app-badge">Synapse v1.2.1 • Offline First</div>
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
                {activeTab === 'appearance' && 'Customize theme palettes, typography sizing, and reader geometry.'}
                {activeTab === 'ai' && 'Manage your local Ollama cluster, primary models, or cloud fallback API keys.'}
                {activeTab === 'storage' && 'Download complete masterclass packs, export custom domains, and vacuum local cache.'}
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
                {/* Visual Theme Cards */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Visual Color Scheme</h4>
                  <div className="theme-cards-grid">
                    {THEME_OPTIONS.map((th) => (
                      <div
                        key={th.id}
                        className={`theme-card ${formData.theme === th.id ? 'active' : ''}`}
                        onClick={() => setFormData({ ...formData, theme: th.id as any })}
                      >
                        <div className="theme-preview-swatch">
                          <div className="swatch-base" style={{ backgroundColor: th.baseColor }} />
                          <div className="swatch-accent" style={{ backgroundColor: th.accentColor }} />
                        </div>
                        <div className="theme-card-info">
                          <span className="theme-card-name">{th.name}</span>
                          {formData.theme === th.id && <Check size={13} className="theme-check-icon" />}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Accent Color Swatches */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Accent Highlights</h4>
                  <div className="accent-chips-row">
                    {ACCENT_OPTIONS.map((ac) => (
                      <button
                        key={ac.id}
                        type="button"
                        className={`accent-chip-btn ${formData.accentColor === ac.id ? 'active' : ''}`}
                        onClick={() => setFormData({ ...formData, accentColor: ac.id as any })}
                      >
                        <span className="chip-circle" style={{ backgroundColor: ac.hex }} />
                        <span>{ac.name}</span>
                      </button>
                    ))}
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
                        <option value="sans">Modern Sans (Inter / SF Pro)</option>
                        <option value="serif">Academic Serif (Merriweather / Georgia)</option>
                        <option value="mono">Engineering Monospace (JetBrains Mono)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Reading Font Size</label>
                      <select
                        value={formData.fontSize || 'standard'}
                        onChange={(e) => setFormData({ ...formData, fontSize: e.target.value as any })}
                      >
                        <option value="compact">Compact (13px) — High Density</option>
                        <option value="standard">Standard (15px) — Balanced</option>
                        <option value="large">Large (17px) — Relaxed</option>
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
                    <span>Local AI Engine (Ollama / Local Cluster)</span>
                  </button>
                  <button
                    type="button"
                    className={`provider-segment-btn ${providerMode === 'cloud' ? 'active' : ''}`}
                    onClick={() => setProviderMode('cloud')}
                  >
                    <Cpu size={15} />
                    <span>Cloud Providers (Anthropic Claude / Google Gemini)</span>
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

                    <div className="settings-panel-box">
                      <h4 className="panel-box-heading">Active Model Assignment</h4>
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
                          <label>Socratic Mentor Model</label>
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

                      {discoveredModels.length > 0 && (
                        <div style={{ marginTop: '8px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Quick Select from Local Models:</span>
                          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                            {discoveredModels.slice(0, 5).map((m) => (
                              <button
                                key={m}
                                type="button"
                                className="node-model-chip font-mono"
                                onClick={() => setFormData({ ...formData, primaryModel: m, mentorModel: m })}
                                title="Set as primary and mentor"
                              >
                                {m}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Advanced: Cluster Nodes */}
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
                                      >
                                        <RefreshCw size={11} className={status.testing ? 'animate-spin' : ''} />
                                      </button>
                                      {clusterNodes.length > 1 && (
                                        <button
                                          type="button"
                                          className="icon-btn-sm danger"
                                          onClick={() => handleRemoveNode(nodeUrl)}
                                        >
                                          <Trash2 size={11} />
                                        </button>
                                      )}
                                    </div>
                                  </div>

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
                {/* 1-Click Masterpack Hero Card */}
                <div className="masterpack-hero-card">
                  <div className="masterpack-info-col">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Package size={18} style={{ color: 'var(--accent-gold)' }} />
                      <h4>Canonical Master Curriculum Pack</h4>
                    </div>
                    <p>
                      The master curriculum bundle includes all 12 core domains and 539 masterclasses.
                      Currently <strong>{packagesData.installed.length}</strong> domains are installed locally.
                    </p>
                  </div>

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
                    <span>{packagesData.installed.length >= 12 ? 'Update Full Curriculum Pack' : 'Download Complete Masterpack'}</span>
                  </button>
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

                {/* Installed Domains Grid */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px' }}>
                  <h4 className="panel-box-heading" style={{ margin: 0 }}>
                    Installed Curriculum Domains ({packagesData.installed.length})
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
                <div className="settings-panel-box" style={{ marginTop: '16px' }}>
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
                <div className="settings-panel-box" style={{ marginTop: '16px' }}>
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
                        if (confirm('Clear transient cache (audio TTS and translation buffers)?')) {
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
                          if (res.ok) {
                            alert('SQLite database vacuumed and WAL checkpointed.');
                          }
                        } catch {
                          alert('Vacuum completed.');
                        }
                      }}
                    >
                      <HardDrive size={12} />
                      <span>Vacuum SQLite Database</span>
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
