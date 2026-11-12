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
  Search
} from 'lucide-react';

export interface AppSettings {
  theme: 'studio' | 'titanium' | 'monokai' | 'nordic';
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
  initialTab?: 'appearance' | 'cluster' | 'models' | 'store';
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
  initialTab,
}) => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'cluster' | 'models' | 'store'>('appearance');

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

  useEffect(() => {
    if (isOpen && activeTab === 'store') {
      fetchPackages();
    }
  }, [isOpen, activeTab]);

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
        </div>

        <form onSubmit={handleSubmit} className="settings-form">
          <div className="settings-tab-content">
            {activeTab === 'appearance' && (
            <div className="settings-section">
              <div className="section-title">
                <Palette size={14} />
                <span>Theme & Appearance</span>
              </div>

              <div className="form-group">
                <label>Color Scheme</label>
                <div className="theme-options-grid">
                  {[
                    { id: 'studio', label: 'Studio Obsidian', desc: 'Deep Carbon & Electric Blue / Gold' },
                    { id: 'titanium', label: 'Titanium Daybreak', desc: 'High-Contrast Clean Light Mode' },
                    { id: 'monokai', label: 'Monokai Pro', desc: 'Toasted Espresso & Neon Pastels' },
                    { id: 'nordic', label: 'Nordic Frost', desc: 'Deep Polar Navy & Arctic Cyan' },
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

              <div className="settings-row-2col">
                <div className="form-group">
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

                <div className="form-group">
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

              <div className="settings-row-2col" style={{ marginTop: '12px' }}>
                <div className="form-group">
                  <label>Reading Language</label>
                  <select
                    value={formData.language || 'en'}
                    onChange={(e) => setFormData({ ...formData, language: e.target.value as any })}
                  >
                    <option value="en">English (Original Source)</option>
                    <option value="cs">Czech (Čeština)</option>
                    <option value="de">German (Deutsch)</option>
                    <option value="es">Spanish (Español)</option>
                    <option value="ru">Russian (Русский)</option>
                  </select>
                  <span className="field-hint">On-the-fly translation preserving math & code</span>
                </div>

                <div className="form-group">
                  <label>Audio Speech Speed</label>
                  <select
                    value={formData.speechRate || '1.0'}
                    onChange={(e) => setFormData({ ...formData, speechRate: e.target.value as any })}
                  >
                    <option value="0.85">0.85x (Slower & Clear)</option>
                    <option value="1.0">1.0x (Standard Natural)</option>
                    <option value="1.15">1.15x (Brisk Cadence)</option>
                    <option value="1.3">1.3x (Fast Review)</option>
                  </select>
                  <span className="field-hint">In-browser Socratic voice synthesis</span>
                </div>
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
                    return (
                      <div key={host} className="cluster-node-item">
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
            <div className="settings-section">
              <div className="section-title">
                <Settings size={14} />
                <span>AI Model Selection & Cloud API Credentials</span>
              </div>

              <div className="settings-row-2col">
                <div className="form-group">
                  <label>Primary Generation Model</label>
                  <input
                    type="text"
                    value={formData.primaryModel}
                    onChange={(e) => setFormData({ ...formData, primaryModel: e.target.value })}
                    placeholder="qwen2.5-coder:32b"
                  />
                </div>

                <div className="form-group">
                  <label>Reviewer / Audit Model</label>
                  <input
                    type="text"
                    value={formData.reviewerModel}
                    onChange={(e) => setFormData({ ...formData, reviewerModel: e.target.value })}
                    placeholder="deepseek-r1:32b"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Socratic Mentor Model (Interactive AI Tutor)</label>
                <input
                  type="text"
                  value={formData.mentorModel || ''}
                  onChange={(e) => setFormData({ ...formData, mentorModel: e.target.value })}
                  placeholder="Auto (routes to fastest online cluster node or cloud fallback)"
                />
                <span className="field-hint">Specify a model e.g. qwen2.5-coder:7b or leave empty for auto-routing across your active cluster</span>
              </div>

              <div className="form-group">
                <label>Anthropic API Key (Claude 3.5 Sonnet / Opus)</label>
                <input
                  type="password"
                  value={formData.anthropicApiKey}
                  onChange={(e) => setFormData({ ...formData, anthropicApiKey: e.target.value })}
                  placeholder="sk-ant-..."
                />
                <span className="field-hint">Stored securely in local SQLite database (never committed to git)</span>
              </div>

              <div className="form-group">
                <label>Anthropic Base URL (Proxy / Custom Gateway)</label>
                <input
                  type="text"
                  value={formData.anthropicBaseUrl}
                  onChange={(e) => setFormData({ ...formData, anthropicBaseUrl: e.target.value })}
                  placeholder="https://api.anthropic.com"
                />
              </div>

              <div className="form-group">
                <label>Google Gemini API Key (Optional Fallback)</label>
                <input
                  type="password"
                  value={formData.geminiApiKey}
                  onChange={(e) => setFormData({ ...formData, geminiApiKey: e.target.value })}
                  placeholder="AIzaSy..."
                />
                <span className="field-hint">Standard Google AI Studio API key (AIzaSy...) is sufficient on its own.</span>
              </div>

              <div className="form-group">
                <label>Google Gemini Base URL (Optional Gateway / Proxy)</label>
                <input
                  type="text"
                  value={formData.geminiBaseUrl || ''}
                  onChange={(e) => setFormData({ ...formData, geminiBaseUrl: e.target.value })}
                  placeholder="https://generativelanguage.googleapis.com (Default)"
                />
                <span className="field-hint">Leave empty for official Google API. Only set if using an enterprise AI proxy or Cloudflare gateway.</span>
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
