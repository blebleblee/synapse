import React, { useState, useEffect } from 'react';
import { Settings, Palette, Cpu, X, Check, Plus, Trash2, RefreshCw } from 'lucide-react';

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
  geminiApiKey: string;
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
    'http://localhost:11434',
    'http://studio.2464.cz:11434',
    'http://maxi.2464.cz:11434',
    'http://192.168.200.60:8080'
  ],
  primaryModel: 'qwen2.5-coder:32b',
  reviewerModel: 'deepseek-r1:32b',
  geminiApiKey: '',
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings,
}) => {
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

        <form onSubmit={handleSubmit} className="settings-form">
          <div className="settings-section">
            <div className="section-title">
              <Palette size={14} />
              <span>Theme & Appearance</span>
            </div>

            <div className="form-group">
              <label>Color Scheme</label>
              <div className="theme-options-grid">
                {[
                  { id: 'studio', label: 'Studio Dark', desc: 'Carbon & Royal Blue / Gold' },
                  { id: 'titanium', label: 'Titanium Obsidian', desc: 'Warm Charcoal & Champagne' },
                  { id: 'monokai', label: 'Monokai Pro', desc: 'Espresso & Pastel Accents' },
                  { id: 'nordic', label: 'Nordic Slate', desc: 'Arctic Slate & Teal' },
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

          <div className="settings-section">
            <div className="section-title">
              <Cpu size={14} />
              <span>AI Engine & Cluster Connectivity</span>
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
              <label>Google Gemini API Key (Optional Fallback)</label>
              <input
                type="password"
                value={formData.geminiApiKey}
                onChange={(e) => setFormData({ ...formData, geminiApiKey: e.target.value })}
                placeholder="AIzaSy..."
              />
              <span className="field-hint">Used for cloud fallback and cross-model audits</span>
            </div>
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
