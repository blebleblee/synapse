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
  Coffee
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
  initialTab?: 'appearance' | 'cluster' | 'models' | 'store' | 'maintenance' | 'inference' | 'storage';
  onTreeChange?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  initialTab,
  onTreeChange,
}) => {
  type SettingsTab = 'appearance' | 'inference' | 'storage';
  const resolveTab = (tab?: string): SettingsTab => {
    if (tab === 'cluster' || tab === 'models' || tab === 'inference') return 'inference';
    if (tab === 'store' || tab === 'maintenance' || tab === 'storage') return 'storage';
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
      onTreeChange?.();
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
      onTreeChange?.();
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
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          anthropic_api_key: formData.anthropicApiKey,
          anthropic_base_url: formData.anthropicBaseUrl,
          gemini_api_key: formData.geminiApiKey,
          gemini_base_url: formData.geminiBaseUrl,
          primary_model: formData.primaryModel,
          reviewer_model: formData.reviewerModel,
          mentor_model: formData.mentorModel,
          ollama_host: clusterNodes[0] || formData.ollamaHost,
        }),
      });
    } catch (err) {
      console.error('Failed to save settings:', err);
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
            <span>Appearance & Reader</span>
          </button>
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'inference' ? 'active' : ''}`}
            onClick={() => setActiveTab('inference')}
          >
            <Cpu size={14} />
            <span>AI Models & Cluster Pins ({clusterNodes.length})</span>
          </button>
          <button
            type="button"
            className={`settings-nav-tab ${activeTab === 'storage' ? 'active' : ''}`}
            onClick={() => setActiveTab('storage')}
          >
            <Package size={14} />
            <span>Storage & Addon Packs</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="settings-form">
          <div className="settings-tab-content">
            {activeTab === 'appearance' && (
              <div className="settings-section compact">
                <div className="section-title">
                  <Palette size={14} />
                  <span>Appearance, Theme & Reader Layout</span>
                </div>

                {/* Box 1: Theme & Accents (Dropdowns to save space) */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Color Scheme & Accent Palette</h4>
                  <div className="settings-row-2col">
                    <div className="form-group compact">
                      <label>Color Scheme Theme</label>
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
                        <option value="titanium">Titanium Daybreak — Clean High-Contrast Light Mode</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Accent Highlight Color</label>
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

                {/* Box 2: Typography & Reader Geometry (Balanced 3-column row) */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Reading Typography & Geometry</h4>
                  <div className="settings-row-3col">
                    <div className="form-group compact">
                      <label>Reading Typography</label>
                      <select
                        value={formData.fontFamily || 'sans'}
                        onChange={(e) => setFormData({ ...formData, fontFamily: e.target.value as any })}
                      >
                        <option value="sans">Modern Sans (Inter / Clean UI)</option>
                        <option value="serif">Academic Serif (Charter / Book)</option>
                        <option value="mono">Technical Mono (JetBrains Code)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Reading Column Width</label>
                      <select
                        value={formData.readerWidth || 'constrained'}
                        onChange={(e) => setFormData({ ...formData, readerWidth: e.target.value as any })}
                      >
                        <option value="constrained">Comfortable Column (860px)</option>
                        <option value="full">Full Width (Fluid 100%)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Line Spacing</label>
                      <select
                        value={formData.lineHeight || 'balanced'}
                        onChange={(e) => setFormData({ ...formData, lineHeight: e.target.value as any })}
                      >
                        <option value="dense">Compact (1.45 - Reference)</option>
                        <option value="balanced">Balanced (1.68 - Standard)</option>
                        <option value="relaxed">Relaxed (1.92 - Longform)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Box 3: Sizing & Localization (Balanced 3-column row) */}
                <div className="settings-panel-box">
                  <h4 className="panel-box-heading">Sizing & Localization</h4>
                  <div className="settings-row-3col">
                    <div className="form-group compact">
                      <label>UI Font Size</label>
                      <select
                        value={formData.fontSize || 'standard'}
                        onChange={(e) => setFormData({ ...formData, fontSize: e.target.value as any })}
                      >
                        <option value="compact">Compact (14px)</option>
                        <option value="standard">Standard (15px)</option>
                        <option value="large">Large (16px)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Curriculum Translation</label>
                      <select
                        value={formData.language || 'en'}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value as any })}
                      >
                        <option value="en">English (Original Masterclass)</option>
                        <option value="cs">Czech (Čeština)</option>
                        <option value="de">German (Deutsch)</option>
                        <option value="es">Spanish (Español)</option>
                        <option value="ru">Russian (Русский)</option>
                      </select>
                    </div>

                    <div className="form-group compact">
                      <label>Terminal Font Size</label>
                      <select
                        value={formData.terminalFontSize || '13px'}
                        onChange={(e) => setFormData({ ...formData, terminalFontSize: e.target.value as any })}
                      >
                        <option value="12px">Compact (12px)</option>
                        <option value="13px">Standard (13px)</option>
                        <option value="14px">Large (14px)</option>
                        <option value="15px">Extra Large (15px)</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

          {activeTab === 'inference' && (
            <div className="settings-section compact">
              <div className="section-title-row">
                <div className="section-title">
                  <Cpu size={14} />
                  <span>AI Models, Inference Routing & Cluster Pins</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn-secondary-sm"
                    onClick={handleScanCluster}
                    disabled={isScanningCluster}
                    title="Ping and test latency across all cluster nodes"
                  >
                    <RefreshCw size={11} className={isScanningCluster ? 'spin' : ''} />
                    <span>{isScanningCluster ? 'Testing...' : 'Test Cluster Nodes'}</span>
                  </button>
                  <button
                    type="button"
                    className="btn-secondary-sm"
                    onClick={fetchDiscoveredModels}
                    disabled={isLoadingModels}
                    title="Rescan endpoints for available models"
                  >
                    <RefreshCw size={11} className={isLoadingModels ? 'animate-spin' : ''} />
                    <span>{isLoadingModels ? 'Pulling...' : 'Pull Models'}</span>
                  </button>
                </div>
              </div>

              {/* Box 1: Active Model Roles */}
              <div className="settings-panel-box">
                <h4 className="panel-box-heading">Active Model Roles</h4>
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

              <div className="settings-panel-box">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h4 className="panel-box-heading" style={{ margin: 0 }}>Cluster Worker Nodes & Model Pinning</h4>
                  {Object.keys(nodePins).length > 0 && (
                    <button
                      type="button"
                      className="btn-secondary-sm"
                      style={{ fontSize: '11px', padding: '2px 8px' }}
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
                            }
                          } catch {
                            alert('Failed to reset pins.');
                          }
                        }
                      }}
                    >
                      <RefreshCw size={10} />
                      <span>Reset Pins</span>
                    </button>
                  )}
                </div>

                <div className="cluster-nodes-list">
                  {clusterNodes.map((host, idx) => {
                    const status = nodeStatuses[host];
                    const cleanHost = host.replace(/^https?:\/\//, '').replace(/\/$/, '');
                    const currentPin = nodePins[cleanHost] || nodePins[host] || '__auto__';

                    return (
                      <div
                        key={host}
                        className="cluster-node-item"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          padding: '6px 12px',
                          background: 'var(--bg-secondary, #121214)',
                          borderRadius: '6px',
                          border: '1px solid var(--border-color, rgba(255,255,255,0.08))'
                        }}
                      >
                        {/* Host URL & Online Status */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '220px' }}>
                          <span className="node-idx" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>#{idx + 1}</span>
                          <span className="node-url" style={{ fontFamily: 'monospace', fontSize: '12px', fontWeight: 600 }}>{cleanHost}</span>
                          {status && (
                            <span
                              className={`node-status-badge ${status.online ? 'online' : status.testing ? 'testing' : 'offline'}`}
                              style={{ padding: '2px 6px', fontSize: '10px' }}
                              title={status.error || (status.models ? `Models: ${status.models.slice(0, 5).join(', ')}` : '')}
                            >
                              {status.testing ? 'Pinging...' : status.online ? `${status.latency_ms}ms` : 'Offline'}
                            </span>
                          )}
                        </div>

                        {/* Model Pinning Selector (Directly Inline!) */}
                        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>📌 Pin:</span>
                          <select
                            className="select-input"
                            style={{
                              flex: 1,
                              padding: '3px 8px',
                              fontSize: '11.5px',
                              height: '28px',
                              background: 'var(--bg-tertiary, #1c2128)',
                              border: '1px solid rgba(255,255,255,0.1)',
                              borderRadius: '4px'
                            }}
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

                        {/* Node Actions */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <button
                            type="button"
                            className="btn-node-action"
                            style={{ padding: '3px 8px', fontSize: '11px', height: '28px' }}
                            onClick={() => handlePingSingleNode(host)}
                            title="Ping node"
                          >
                            Ping
                          </button>
                          <button
                            type="button"
                            className="btn-node-action remove"
                            style={{ padding: '3px 6px', height: '28px' }}
                            onClick={() => handleRemoveNode(idx)}
                            title="Remove node from cluster"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="add-node-row" style={{ marginTop: '8px' }}>
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
              </div>

              {/* Box 3: Cloud API Credentials & Gateways */}
              <div className="settings-panel-box">
                <h4 className="panel-box-heading">Cloud API Gateways & Credentials</h4>

                <div className="settings-row-2col">
                  <div className="form-group compact">
                    <label>Anthropic API Key (Claude Sonnet / Opus)</label>
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
                    <label>Google Gemini Base URL (Optional Gateway)</label>
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

          {activeTab === 'storage' && (
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

              {/* Workspace Storage & Maintenance */}
              <div className="settings-panel-box" style={{ marginTop: '14px' }}>
                <h4 className="panel-box-heading">Workspace Storage & Maintenance</h4>
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

                <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
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
          )}
          </div>

          <div className="modal-actions" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <a
              href="https://buymeacoffee.com/blebleblee"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-coffee-donate"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(251, 191, 36, 0.12)',
                border: '1px solid rgba(251, 191, 36, 0.3)',
                color: '#fbbf24',
                fontSize: '12px',
                fontWeight: 600,
                textDecoration: 'none',
                transition: 'all 0.15s ease'
              }}
              title="Support Synapse open-source development"
            >
              <Coffee size={14} />
              <span>Buy Me a Coffee</span>
            </a>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Version: 1.1.1</span>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button type="button" className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                {savedMessage ? 'Saved!' : 'Save Settings'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
