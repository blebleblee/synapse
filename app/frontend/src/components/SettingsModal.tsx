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
  Wrench
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
  clusterHosts: [
    'http://localhost:11434'
  ],
  primaryModel: 'qwen2.5-coder:32b',
  reviewerModel: 'deepseek-r1:32b',
  mentorModel: '',
  geminiApiKey: '',
  geminiBaseUrl: '',
  anthropicApiKey: '',
  anthropicBaseUrl: 'https://api.anthropic.com',
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => void;
  initialTab?: 'appearance' | 'cluster' | 'models' | 'store' | 'maintenance';
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  initialTab,
}) => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'cluster' | 'models' | 'store' | 'maintenance'>('appearance');

  useEffect(() => {
    if (isOpen && initialTab) {
      setActiveTab(initialTab);
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

  // Endpoint Discovered Models State
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

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
    setIsLoadingModels(true);
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
    } finally {
      setIsLoadingModels(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchPackages();
      fetchDiscoveredModels();
      fetchNodePins();
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
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Install failed', type: 'error' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUninstallPack = async (domain: string) => {
    setActionInProgress(`uninstall-${domain}`);
    setStoreMessage(null);
    try {
      const res = await fetch(`/api/packages/${encodeURIComponent(domain)}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Package uninstall failed');
      setStoreMessage({ text: `Package ${domain} uninstalled`, type: 'success' });
      await fetchPackages();
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
    try {
      const uploadForm = new FormData();
      uploadForm.append('file', file);
      const res = await fetch('/api/packages/install', {
        method: 'POST',
        body: uploadForm
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to install uploaded package');
      }
      const result = await res.json();
      setStoreMessage({ text: `Successfully installed ${result.domain || 'custom'} package!`, type: 'success' });
      await fetchPackages();
    } catch (err: any) {
      setStoreMessage({ text: err.message || 'Upload installation failed', type: 'error' });
    } finally {
      setActionInProgress(null);
      if (e.target) e.target.value = '';
    }
  };

  useEffect(() => {
    setFormData(settings);
    if (isOpen) {
      fetch('/api/settings/cluster')
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data.hosts) && data.hosts.length > 0) {
            setClusterNodes(data.hosts);
          }
        })
        .catch(() => {});
    }
  }, [settings, isOpen]);

  const handleAddNode = () => {
    const clean = newNodeUrl.trim().replace(/\/+$/, '');
    if (!clean) return;
    if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
      alert('Node URL must start with http:// or https://');
      return;
    }
    if (clusterNodes.includes(clean)) {
      alert('Node already exists in cluster list');
      return;
    }
    setClusterNodes([...clusterNodes, clean]);
    setNewNodeUrl('');
  };

  const handleRemoveNode = (index: number) => {
    const next = [...clusterNodes];
    next.splice(index, 1);
    setClusterNodes(next);
  };

  const handlePingSingleNode = async (host: string) => {
    setNodeStatuses((prev) => ({
      ...prev,
      [host]: { ...prev[host], testing: true }
    }));
    try {
      const res = await fetch('/api/settings/test-ollama', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host }),
      });
      const data = await res.json();
      setNodeStatuses((prev) => ({
        ...prev,
        [host]: {
          online: data.ok,
          latency_ms: data.latency_ms,
          models: data.models,
          error: data.error,
          testing: false
        }
      }));
    } catch (err: any) {
      setNodeStatuses((prev) => ({
        ...prev,
        [host]: {
          online: false,
          error: err.message || 'Network error',
          testing: false
        }
      }));
    }
  };

  const handleScanCluster = async () => {
    setIsScanningCluster(true);
    try {
      const res = await fetch('/api/settings/cluster-status');
      const data = await res.json();
      setNodeStatuses(data);
    } catch (err) {
      console.error('Failed to scan cluster:', err);
    } finally {
      setIsScanningCluster(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch('/api/settings/cluster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hosts: clusterNodes }),
      });
    } catch (err) {
      console.error('Failed to save cluster hosts:', err);
    }
    onSaveSettings({
      ...formData,
      clusterHosts: clusterNodes,
      ollamaHost: clusterNodes[0] || formData.ollamaHost
    });
    setSavedMessage(true);
    setTimeout(() => {
      setSavedMessage(false);
      onClose();
    }, 800);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card settings-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <Settings size={18} className="settings-header-icon" />
            <h3>Workbench Settings</h3>
          </div>
          <button className="icon-btn" onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        <div className="settings-tabs-nav">
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'appearance' ? 'active' : ''}`}
            onClick={() => setActiveTab('appearance')}
          >
            <Palette size={14} />
            <span>Theme & Reader</span>
          </button>
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'cluster' ? 'active' : ''}`}
            onClick={() => setActiveTab('cluster')}
          >
            <Cpu size={14} />
            <span>Ollama Cluster ({clusterNodes.length})</span>
          </button>
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'models' ? 'active' : ''}`}
            onClick={() => setActiveTab('models')}
          >
            <Settings size={14} />
            <span>AI Models & Cloud API</span>
          </button>
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'store' ? 'active' : ''}`}
            onClick={() => setActiveTab('store')}
          >
            <Package size={14} />
            <span>Curriculum Store & Addons</span>
          </button>
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'maintenance' ? 'active' : ''}`}
            onClick={() => setActiveTab('maintenance')}
          >
            <Wrench size={14} />
            <span>System & Maintenance</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="settings-form">
          <div className="settings-tab-content">
            {activeTab === 'appearance' && (
            <div className="settings-section">
              <div className="section-title">
                <Palette size={14} />
                <span>Theme & Custom Appearance</span>
              </div>

              <div className="form-group">
                <label>Color Scheme Theme</label>
                <div className="theme-options-grid">
                  {[
                    { id: 'studio', label: 'Studio Obsidian', desc: 'Deep OLED Carbon & Gold' },
                    { id: 'github_dimmed', label: 'GitHub Dimmed', desc: 'Slate Navy & High Contrast' },
                    { id: 'nordic', label: 'Nordic Frost', desc: 'Polar Night & Arctic Cyan' },
                    { id: 'monokai', label: 'Monokai Pro', desc: 'Toasted Espresso & Neon Pastels' },
                    { id: 'dracula', label: 'Dracula Noir', desc: 'Deep Violet Indigo & Pink' },
                    { id: 'solarized', label: 'Solarized Dark', desc: 'Teal Oceanic & Warm Amber' },
                    { id: 'titanium', label: 'Titanium Daybreak', desc: 'Clean High-Contrast Light Mode' },
                  ].map((t) => (
                    <button
                      type="button"
                      key={t.id}
                      className={`theme-card ${formData.theme === t.id ? 'active' : ''}`}
                      onClick={() => setFormData({ ...formData, theme: t.id as any })}
                    >
                      <div className="theme-card-header">
                        <span className="theme-name">{t.label}</span>
                        {formData.theme === t.id && <Check size={14} className="check-icon" />}
                      </div>
                      <span className="theme-desc">{t.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group" style={{ marginTop: '14px' }}>
                <label>Accent Highlight Color</label>
                <div className="accent-options-row">
                  {[
                    { id: 'gold', label: 'Amber Gold', color: '#fbbf24' },
                    { id: 'cyan', label: 'Electric Cyan', color: '#06b6d4' },
                    { id: 'emerald', label: 'Matrix Emerald', color: '#10b981' },
                    { id: 'amethyst', label: 'Royal Amethyst', color: '#a855f7' },
                    { id: 'rose', label: 'Crimson Rose', color: '#f43f5e' },
                  ].map((a) => (
                    <button
                      type="button"
                      key={a.id}
                      className={`accent-chip ${formData.accentColor === a.id ? 'active' : ''}`}
                      onClick={() => setFormData({ ...formData, accentColor: a.id as any })}
                    >
                      <span className="accent-dot" style={{ backgroundColor: a.color }} />
                      <span>{a.label}</span>
                      {formData.accentColor === a.id && <Check size={12} />}
                    </button>
                  ))}
                </div>
              </div>

              <div className="settings-row-4col" style={{ marginTop: '14px' }}>
                <div className="form-group compact">
                  <label>Reading Typography</label>
                  <select
                    value={formData.fontFamily || 'sans'}
                    onChange={(e) => setFormData({ ...formData, fontFamily: e.target.value as any })}
                  >
                    <option value="sans">Modern Sans (Inter / UI)</option>
                    <option value="serif">Academic Serif (Charter / Book)</option>
                    <option value="mono">Technical Mono (JetBrains Code)</option>
                  </select>
                </div>

                <div className="form-group compact">
                  <label>Reader Line Spacing</label>
                  <select
                    value={formData.lineHeight || 'balanced'}
                    onChange={(e) => setFormData({ ...formData, lineHeight: e.target.value as any })}
                  >
                    <option value="dense">Compact (1.45 - Reference)</option>
                    <option value="balanced">Balanced (1.68 - Standard)</option>
                    <option value="relaxed">Relaxed (1.92 - Longform)</option>
                  </select>
                </div>

                <div className="form-group compact">
                  <label>UI Font Size</label>
                  <select
                    value={formData.fontSize}
                    onChange={(e) => setFormData({ ...formData, fontSize: e.target.value as any })}
                  >
                    <option value="compact">Compact (14px)</option>
                    <option value="standard">Standard (15px)</option>
                    <option value="large">Large (16px)</option>
                  </select>
                </div>

                <div className="form-group compact">
                  <label>Reading Width</label>
                  <select
                    value={formData.readerWidth}
                    onChange={(e) => setFormData({ ...formData, readerWidth: e.target.value as any })}
                  >
                    <option value="full">Full Width (Fluid 100%)</option>
                    <option value="constrained">Comfortable Column (860px)</option>
                  </select>
                </div>
              </div>

              <div className="form-group compact" style={{ marginTop: '12px' }}>
                <label>Curriculum Translation Language</label>
                <select
                  value={formData.language || 'en'}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value as any })}
                >
                  <option value="en">English (Original Masterclass Source)</option>
                  <option value="cs">Czech (Čeština)</option>
                  <option value="de">German (Deutsch)</option>
                  <option value="es">Spanish (Español)</option>
                  <option value="ru">Russian (Русский)</option>
                </select>
              </div>
            </div>
          )}

          {activeTab === 'cluster' && (
            <div className="settings-section">
              <div className="section-title">
                <Cpu size={14} />
                <span>Distributed Ollama Inference Cluster</span>
              </div>

              <div className="cluster-nodes-manager">
                <div className="cluster-manager-header">
                  <label>Active Cluster Worker Nodes</label>
                  <button
                    type="button"
                    className="btn-secondary-sm btn-scan-cluster"
                    onClick={handleScanCluster}
                    disabled={isScanningCluster}
                    title="Ping and test latency across all cluster nodes"
                  >
                    <RefreshCw size={11} className={isScanningCluster ? 'spin' : ''} />
                    <span>{isScanningCluster ? 'Scanning...' : 'Test All Nodes'}</span>
                  </button>
                </div>

                <div className="cluster-nodes-list">
                  {clusterNodes.map((host, idx) => {
                    const status = nodeStatuses[host];
                    const cleanHost = host.replace(/^https?:\/\//, '').replace(/\/$/, '');
                    const currentPin = nodePins[cleanHost] || nodePins[host] || '__auto__';

                    return (
                      <div key={host} className="cluster-node-item" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                          <div className="node-info">
                            <span className="node-idx">#{idx + 1}</span>
                            <span className="node-url">{host}</span>
                            {status && (
                              <span
                                className={`node-status-badge ${status.online ? 'online' : status.testing ? 'testing' : 'offline'}`}
                                title={status.error || (status.models ? `Models: ${status.models.slice(0, 5).join(', ')}` : '')}
                              >
                                {status.testing
                                  ? 'Pinging...'
                                  : status.online
                                  ? `Online (${status.latency_ms}ms)`
                                  : 'Offline'}
                              </span>
                            )}
                          </div>
                          <div className="node-actions">
                            <button
                              type="button"
                              className="btn-node-action"
                              onClick={() => handlePingSingleNode(host)}
                              title="Ping node"
                            >
                              Ping
                            </button>
                            <button
                              type="button"
                              className="btn-node-action remove"
                              onClick={() => handleRemoveNode(idx)}
                              title="Remove node from cluster"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </div>

                        <div className="node-pin-control" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '4px' }}>
                          <span style={{ color: 'var(--text-muted, #888)', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            📌 <strong>Pinned Model:</strong>
                          </span>
                          <select
                            className="select-input"
                            style={{ flex: 1, padding: '4px 8px', fontSize: '12px', background: 'var(--bg-secondary, #121214)', border: '1px solid rgba(255,255,255,0.1)' }}
                            value={currentPin}
                            onChange={(e) => handleUpdateNodePin(host, e.target.value)}
                          >
                            <option value="__auto__">⚡ Auto-Select (Dynamic / Best Match)</option>
                            {status?.models && status.models.length > 0 ? (
                              <optgroup label="Models on this Node">
                                {status.models.map((m) => (
                                  <option key={m} value={m}>{m}</option>
                                ))}
                              </optgroup>
                            ) : null}
                            {discoveredModels && discoveredModels.length > 0 ? (
                              <optgroup label="All Discovered Cluster Models">
                                {discoveredModels.map((m) => (
                                  <option key={`disc-${m}`} value={m}>{m}</option>
                                ))}
                              </optgroup>
                            ) : null}
                          </select>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="add-node-row">
                  <input
                    type="text"
                    value={newNodeUrl}
                    onChange={(e) => setNewNodeUrl(e.target.value)}
                    placeholder="http://192.168.1.50:11434 or :8080"
                    className="text-input"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddNode();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn-primary-sm"
                    onClick={handleAddNode}
                    disabled={!newNodeUrl.trim()}
                    title="Add endpoint to cluster"
                  >
                    <Plus size={13} />
                    <span>Add Node</span>
                  </button>
                </div>
                <span className="field-hint">Supports Ollama (port 11434) and LocalAI / OpenAI-compatible (port 8080) endpoints.</span>
              </div>
            </div>
          )}

          {activeTab === 'models' && (
            <div className="settings-section compact">
              <div className="section-title-row">
                <div className="section-title">
                  <Settings size={14} />
                  <span>AI Models & Cloud API Keys</span>
                </div>
                <button
                  type="button"
                  className="btn-secondary-sm"
                  onClick={fetchDiscoveredModels}
                  disabled={isLoadingModels}
                  title="Rescan endpoints for available models"
                >
                  <RefreshCw size={12} className={isLoadingModels ? 'animate-spin' : ''} />
                  <span>{isLoadingModels ? 'Scanning...' : 'Pull Models from Endpoints'}</span>
                </button>
              </div>

              {/* Box 1: Active Model Routing (Full Width 3-Column Row) */}
              <div className="settings-panel-box">
                <h4 className="panel-box-heading">Active Model Routing</h4>
                <div className="settings-row-3col">
                  <div className="form-group compact">
                    <label>Primary Generation Model</label>
                    <select
                      value={formData.primaryModel}
                      onChange={(e) => setFormData({ ...formData, primaryModel: e.target.value })}
                    >
                      {!formData.primaryModel && <option value="">Select Primary Model...</option>}
                      {formData.primaryModel && !discoveredModels.includes(formData.primaryModel) && (
                        <option value={formData.primaryModel} title={formData.primaryModel}>
                          {formData.primaryModel.length > 34 ? `${formData.primaryModel.slice(0, 32)}...` : formData.primaryModel}
                        </option>
                      )}
                      {discoveredModels.map((m) => (
                        <option key={`p-${m}`} value={m} title={m}>
                          {m.length > 34 ? `${m.slice(0, 32)}...` : m}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group compact">
                    <label>Reviewer / Audit Model</label>
                    <select
                      value={formData.reviewerModel}
                      onChange={(e) => setFormData({ ...formData, reviewerModel: e.target.value })}
                    >
                      {!formData.reviewerModel && <option value="">Select Reviewer Model...</option>}
                      {formData.reviewerModel && !discoveredModels.includes(formData.reviewerModel) && (
                        <option value={formData.reviewerModel} title={formData.reviewerModel}>
                          {formData.reviewerModel.length > 34 ? `${formData.reviewerModel.slice(0, 32)}...` : formData.reviewerModel}
                        </option>
                      )}
                      {discoveredModels.map((m) => (
                        <option key={`r-${m}`} value={m} title={m}>
                          {m.length > 34 ? `${m.slice(0, 32)}...` : m}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group compact">
                    <label>Socratic Mentor Model (AI Tutor)</label>
                    <select
                      value={formData.mentorModel || ''}
                      onChange={(e) => setFormData({ ...formData, mentorModel: e.target.value })}
                    >
                      {!formData.mentorModel && <option value="">Select Mentor Model...</option>}
                      {formData.mentorModel && !discoveredModels.includes(formData.mentorModel) && (
                        <option value={formData.mentorModel} title={formData.mentorModel}>
                          {formData.mentorModel.length > 34 ? `${formData.mentorModel.slice(0, 32)}...` : formData.mentorModel}
                        </option>
                      )}
                      {discoveredModels.map((m) => (
                        <option key={`m-${m}`} value={m} title={m}>
                          {m.length > 34 ? `${m.slice(0, 32)}...` : m}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Box 2: Cloud API Credentials & Gateways (Spacious Full Width) */}
              <div className="settings-panel-box">
                <h4 className="panel-box-heading">Cloud API Credentials & Gateways</h4>

                <div className="settings-row-2col">
                  <div className="form-group compact">
                    <label>Anthropic API Key (Claude 3.5 Sonnet / Opus)</label>
                    <input
                      type="password"
                      value={formData.anthropicApiKey}
                      onChange={(e) => setFormData({ ...formData, anthropicApiKey: e.target.value })}
                      placeholder="sk-ant-api03-..."
                    />
                  </div>

                  <div className="form-group compact">
                    <label>Anthropic Base URL (Proxy / Custom Gateway)</label>
                    <input
                      type="text"
                      value={formData.anthropicBaseUrl}
                      onChange={(e) => setFormData({ ...formData, anthropicBaseUrl: e.target.value })}
                      placeholder="https://api.anthropic.com"
                    />
                  </div>
                </div>

                <div className="settings-row-2col" style={{ marginTop: '8px' }}>
                  <div className="form-group compact">
                    <label>Google Gemini API Key (Gemini 2.5 Flash / Pro)</label>
                    <input
                      type="password"
                      value={formData.geminiApiKey}
                      onChange={(e) => setFormData({ ...formData, geminiApiKey: e.target.value })}
                      placeholder="AIzaSy..."
                    />
                  </div>

                  <div className="form-group compact">
                    <label>Google Gemini Base URL (Optional Gateway / Proxy)</label>
                    <input
                      type="text"
                      value={formData.geminiBaseUrl || ''}
                      onChange={(e) => setFormData({ ...formData, geminiBaseUrl: e.target.value })}
                      placeholder="https://generativelanguage.googleapis.com"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'store' && (
            <div className="settings-section">
              <div className="section-title-row">
                <div className="section-title">
                  <Package size={14} />
                  <span>Curriculum Store & Portable Addons</span>
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

              {storeMessage && (
                <div className={`store-message-banner ${storeMessage.type}`}>
                  {storeMessage.type === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                  <span>{storeMessage.text}</span>
                </div>
              )}

              {/* Compact Search & Sideload Toolbar */}
              <div className="store-top-bar">
                <div className="store-search-box">
                  <Search size={13} className="store-search-icon" />
                  <input
                    type="text"
                    placeholder="Filter domains (e.g. computing, arts)..."
                    value={storeSearch}
                    onChange={(e) => setStoreSearch(e.target.value)}
                  />
                  {storeSearch && (
                    <button type="button" className="store-search-clear" onClick={() => setStoreSearch('')} title="Clear filter">
                      <X size={11} />
                    </button>
                  )}
                </div>

                <label className="btn-secondary store-upload-compact-btn" title="Sideload custom .synpack archive">
                  {actionInProgress === 'uploading' ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Installing...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={12} />
                      <span>Sideload .synpack</span>
                    </>
                  )}
                  <input
                    type="file"
                    accept=".synpack,.tar.gz"
                    onChange={handleFileUpload}
                    disabled={actionInProgress !== null}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>

              {/* Unified Domain Packages Grid */}
              <div className="store-subsection-header">
                <span>
                  Curriculum Domains ({packagesData.available_domains.filter((d) => !storeSearch || d.title.toLowerCase().includes(storeSearch.toLowerCase()) || d.domain.toLowerCase().includes(storeSearch.toLowerCase()) || d.description.toLowerCase().includes(storeSearch.toLowerCase())).length})
                </span>
              </div>

              {isLoadingPackages && packagesData.available_domains.length === 0 && (
                <div className="store-loading-state">
                  <Loader2 className="animate-spin" size={18} />
                  <span>Loading curriculum packages...</span>
                </div>
              )}

              {!isLoadingPackages && packagesData.available_domains.length === 0 && (
                <div className="store-empty-state">
                  <Package size={24} className="store-empty-icon" />
                  <span>No curriculum packages found.</span>
                  <button type="button" className="btn-secondary" onClick={fetchPackages}>
                    <RefreshCw size={12} />
                    <span>Retry Loading</span>
                  </button>
                </div>
              )}

              <div className="store-domains-grid">
                {packagesData.available_domains
                  .filter((d) => !storeSearch || d.title.toLowerCase().includes(storeSearch.toLowerCase()) || d.domain.toLowerCase().includes(storeSearch.toLowerCase()) || d.description.toLowerCase().includes(storeSearch.toLowerCase()))
                  .map((d) => (
                    <div key={d.domain} className={`store-domain-card ${d.is_installed ? 'installed' : ''}`}>
                      <div className="store-card-header">
                        <div className="store-card-title-col">
                          <span className="store-domain-pill">{d.domain}</span>
                          <h4 className="store-domain-title">{d.title}</h4>
                        </div>
                        {d.is_installed && (
                          <span className="store-status-badge installed" title="Active in local topics">
                            <Check size={11} /> Installed
                          </span>
                        )}
                      </div>

                      <p className="store-domain-desc">{d.description}</p>

                      <div className="store-card-footer">
                        <div className="store-stat-pill">
                          <span>{d.lesson_count} lessons</span>
                          <span className="dot-sep">•</span>
                          <span>{d.lab_count} labs</span>
                        </div>

                        <div className="store-card-actions">
                          <button
                            type="button"
                            className="store-action-btn export"
                            onClick={() => handleExportPack(d.domain)}
                            disabled={actionInProgress === `export-${d.domain}`}
                            title={`Export ${d.domain}.synpack archive`}
                          >
                            {actionInProgress === `export-${d.domain}` ? (
                              <Loader2 size={11} className="animate-spin" />
                            ) : (
                              <Download size={11} />
                            )}
                            <span>Export</span>
                          </button>

                          {d.is_installed ? (
                            <button
                              type="button"
                              className="store-action-btn uninstall"
                              onClick={() => handleUninstallPack(d.domain)}
                              disabled={actionInProgress === `uninstall-${d.domain}`}
                              title={`Uninstall / unregister ${d.domain} package`}
                            >
                              {actionInProgress === `uninstall-${d.domain}` ? (
                                <Loader2 size={11} className="animate-spin" />
                              ) : (
                                <Trash2 size={11} />
                              )}
                              <span>Uninstall</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="store-action-btn install"
                              onClick={() => handleInstallDomain(d.domain)}
                              disabled={actionInProgress === `install-${d.domain}`}
                              title={`Register ${d.domain} package`}
                            >
                              {actionInProgress === `install-${d.domain}` ? (
                                <Loader2 size={11} className="animate-spin" />
                              ) : (
                                <Package size={11} />
                              )}
                              <span>Install</span>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {activeTab === 'maintenance' && (
            <div className="settings-section">
              <div className="section-title">
                <Wrench size={14} />
                <span>System Health & Runtime Maintenance</span>
              </div>

              <div className="settings-panel-box" style={{ marginBottom: '16px' }}>
                <h4 className="panel-box-heading">Workspace Transient Data & Progress</h4>
                <div className="form-group compact">
                  <label>Session Artifacts & Study Progress</label>
                  <span className="field-hint">
                    Clears temporary markdown chat sessions (.workspace_sessions), cached export bundles, or resets lesson completion checkmarks.
                  </span>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-secondary-sm"
                      onClick={async () => {
                        if (confirm('Clear all transient chat sessions and temporary exports?')) {
                          try {
                            const res = await fetch('/api/clean', { method: 'POST' });
                            if (res.ok) {
                              const data = await res.json();
                              alert(`Successfully cleaned ${data.cleaned} transient artifacts.`);
                            }
                          } catch {
                            alert('Cleanup failed.');
                          }
                        }
                      }}
                    >
                      <Trash2 size={12} />
                      <span>Clear Transient Artifacts</span>
                    </button>
                    <button
                      type="button"
                      className="btn-secondary-sm"
                      onClick={async () => {
                        if (confirm('Reset all lesson completion checkmarks across all courses?')) {
                          try {
                            const res = await fetch('/api/clean', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ sessions: false, exports: false, mastery: true })
                            });
                            if (res.ok) {
                              alert('Lesson completion progress reset.');
                              window.location.reload();
                            }
                          } catch {
                            alert('Reset failed.');
                          }
                        }
                      }}
                    >
                      <RefreshCw size={12} />
                      <span>Reset Lesson Progress</span>
                    </button>
                  </div>
                </div>
              </div>

              <div className="settings-panel-box" style={{ marginBottom: '16px' }}>
                <h4 className="panel-box-heading">Inference Cluster & Model Pinning</h4>
                <div className="form-group compact">
                  <label>Node Model Pins (.synapse_node_pins.json)</label>
                  <span className="field-hint">
                    Current host model pin overrides. You can configure individual pins directly in the <strong>Cluster & Nodes</strong> tab.
                  </span>

                  {Object.keys(nodePins).length > 0 ? (
                    <div style={{ margin: '8px 0', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {Object.entries(nodePins).map(([host, model]) => (
                        <div key={host} style={{ fontSize: '11px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '5px 8px', borderRadius: '4px' }}>
                          <span style={{ fontFamily: 'monospace', color: 'var(--accent, #e5a93c)' }}>{host}</span>
                          <span style={{ color: 'var(--text-muted, #aaa)' }}>📌 {model}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="field-hint" style={{ display: 'block', margin: '6px 0', fontStyle: 'italic' }}>
                      No nodes currently pinned (dynamic selection active across all nodes).
                    </span>
                  )}

                  <button
                    type="button"
                    className="btn-secondary-sm"
                    style={{ marginTop: '8px', width: 'fit-content' }}
                    onClick={async () => {
                      if (confirm('Reset all cluster node pins back to automatic model selection?')) {
                        try {
                          const res = await fetch('/api/settings/cluster-pins', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pins: {} })
                          });
                          if (res.ok) {
                            setNodePins({});
                            alert('Node model pins reset successfully.');
                          }
                        } catch {
                          alert('Failed to reset pins.');
                        }
                      }
                    }}
                  >
                    <RefreshCw size={12} />
                    <span>Reset Model Pins</span>
                  </button>
                </div>
              </div>

              <div className="settings-panel-box">
                <h4 className="panel-box-heading">Database & Workspace Storage</h4>
                <div className="maintenance-info-grid">
                  <div className="maintenance-info-item">
                    <span className="info-label">Runtime DB</span>
                    <span className="info-val">data/synapse.db (SQLite)</span>
                  </div>
                  <div className="maintenance-info-item">
                    <span className="info-label">Curriculum Dir</span>
                    <span className="info-val">topics/ (504 Courses)</span>
                  </div>
                  <div className="maintenance-info-item">
                    <span className="info-label">Engine Log</span>
                    <span className="info-val">generator.log</span>
                  </div>
                  <div className="maintenance-info-item">
                    <span className="info-label">User Credentials</span>
                    <span className="info-val">~/.config/synapse/env</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              {savedMessage ? 'Saved!' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
