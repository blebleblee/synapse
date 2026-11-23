import React, { useState, useEffect, useRef } from 'react';
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
  HardDrive,
  Terminal,
  Sparkles,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  Power
} from 'lucide-react';


/** One titled group of settings, separated from the next by a line. */
const SettingsGroup: React.FC<{
  title: string;
  description?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  children?: React.ReactNode;
}> = ({ title, description, icon, actions, children }) => (
  <section className="settings-group">
    <header className="settings-group-header">
      <div>
        <h4 className="settings-group-title">{icon}{title}</h4>
        {description && <p className="settings-group-desc">{description}</p>}
      </div>
      {actions && <div className="settings-group-actions">{actions}</div>}
    </header>
    {children}
  </section>
);

/** A labelled control with an optional one-line hint under it. */
const Field: React.FC<{ label: string; hint?: string; children: React.ReactNode }> = ({ label, hint, children }) => (
  <label className="settings-field">
    <span className="settings-field-label">{label}</span>
    {children}
    {hint && <span className="settings-field-hint">{hint}</span>}
  </label>
);

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
  // The "complete" masterpack is a download bundle, not a subject area.
  // Alphabetical, so a course does not jump to the top after it is imported.
  const installedDomains = packagesData.installed
    .filter((p) => p.domain !== 'complete' && p.domain !== 'synapse_complete_curriculum')
    .sort((a, b) => a.domain.localeCompare(b.domain));

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

  const packFileInputRef = useRef<HTMLInputElement>(null);

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
              <span>AI models</span>
            </button>

            <button
              type="button"
              className={`settings-nav-item ${activeTab === 'storage' ? 'active' : ''}`}
              onClick={() => setActiveTab('storage')}
            >
              <Package size={16} />
              <span>Courses</span>
            </button>
          </nav>

          <div className="settings-sidebar-footer">
            <div className="sidebar-app-badge">Synapse v1.3.1</div>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="settings-body">
          <div className="settings-body-header">
            <div>
              <h3>
                {activeTab === 'appearance' && 'Appearance'}
                {activeTab === 'ai' && 'AI models'}
                {activeTab === 'storage' && 'Courses and maintenance'}
              </h3>
              <p className="settings-tab-desc">
                {activeTab === 'appearance' && 'Colors, lesson text and layout. Saved in this browser.'}
                {activeTab === 'ai' && 'Where the AI runs and which model does what.'}
                {activeTab === 'storage' && 'Install, share and remove courses; keep the app tidy.'}
              </p>
            </div>
            <button className="icon-btn" onClick={onClose} title="Close Settings">
              <X size={16} />
            </button>
          </div>

          <div className="settings-tab-scroll">
            {/* TAB 1: APPEARANCE */}
            {activeTab === 'appearance' && (
              <>
                <SettingsGroup title="Colors" description="The color theme for the whole app and the highlight color for links, buttons and the active lesson.">
                  <div className="settings-row-2col">
                    <Field label="Theme">
                      <select
                        value={formData.theme}
                        onChange={(e) => setFormData({ ...formData, theme: e.target.value as any })}
                      >
                        <option value="studio">Studio Obsidian (dark, gold)</option>
                        <option value="github_dimmed">GitHub Dimmed (dark, blue)</option>
                        <option value="nordic">Nordic Frost (dark, cyan)</option>
                        <option value="monokai">Monokai Pro (dark, pastel)</option>
                        <option value="dracula">Dracula Noir (dark, violet)</option>
                        <option value="solarized">Solarized Dark (dark, teal)</option>
                        <option value="titanium">Titanium Daybreak (light)</option>
                      </select>
                    </Field>
                    <Field label="Accent color">
                      <select
                        value={formData.accentColor || 'gold'}
                        onChange={(e) => setFormData({ ...formData, accentColor: e.target.value as any })}
                      >
                        <option value="gold">Amber gold</option>
                        <option value="cyan">Electric cyan</option>
                        <option value="emerald">Emerald green</option>
                        <option value="amethyst">Amethyst purple</option>
                        <option value="rose">Crimson rose</option>
                      </select>
                    </Field>
                  </div>
                </SettingsGroup>

                <SettingsGroup title="Lesson text" description="How lessons read in the middle panel. The sample below updates as you change these.">
                  <div className="settings-row-3col">
                    <Field label="Font">
                      <select
                        value={formData.fontFamily}
                        onChange={(e) => setFormData({ ...formData, fontFamily: e.target.value as any })}
                      >
                        <option value="sans">Sans serif</option>
                        <option value="serif">Serif</option>
                        <option value="mono">Monospace</option>
                      </select>
                    </Field>
                    <Field label="Text size">
                      <select
                        value={formData.fontSize || 'standard'}
                        onChange={(e) => setFormData({ ...formData, fontSize: e.target.value as any })}
                      >
                        <option value="compact">Small (13 px)</option>
                        <option value="standard">Medium (15 px)</option>
                        <option value="large">Large (17 px)</option>
                      </select>
                    </Field>
                    <Field label="Line spacing">
                      <select
                        value={formData.lineHeight || 'balanced'}
                        onChange={(e) => setFormData({ ...formData, lineHeight: e.target.value as any })}
                      >
                        <option value="dense">Tight</option>
                        <option value="balanced">Normal</option>
                        <option value="relaxed">Relaxed</option>
                      </select>
                    </Field>
                  </div>

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
                </SettingsGroup>

                <SettingsGroup title="Layout and language">
                  <div className="settings-row-2col">
                    <Field label="Lesson width" hint="A narrow column is easier to read on wide screens.">
                      <select
                        value={formData.readerWidth || 'full'}
                        onChange={(e) => setFormData({ ...formData, readerWidth: e.target.value as any })}
                      >
                        <option value="full">Fill the panel</option>
                        <option value="constrained">Narrow column (780 px)</option>
                      </select>
                    </Field>
                    <Field label="Lesson language" hint="Other languages are machine-translated by the AI model.">
                      <select
                        value={formData.language || 'en'}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value as any })}
                      >
                        <option value="en">English (original)</option>
                        <option value="cs">Čeština (Czech)</option>
                        <option value="de">Deutsch (German)</option>
                        <option value="es">Español (Spanish)</option>
                      </select>
                    </Field>
                  </div>
                </SettingsGroup>
              </>
            )}

            {/* TAB 2: AI MODELS (local Ollama or cloud keys) */}
            {activeTab === 'ai' && (
              <>
                <div className="provider-mode-segmented" role="tablist" aria-label="Where the AI models run">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={providerMode === 'local'}
                    className={`provider-segment-btn ${providerMode === 'local' ? 'active' : ''}`}
                    onClick={() => setProviderMode('local')}
                  >
                    <Server size={15} />
                    <span>On this network (Ollama)</span>
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={providerMode === 'cloud'}
                    className={`provider-segment-btn ${providerMode === 'cloud' ? 'active' : ''}`}
                    onClick={() => setProviderMode('cloud')}
                  >
                    <Cpu size={15} />
                    <span>Cloud API keys</span>
                  </button>
                </div>

                {providerMode === 'local' && (
                  <>
                    <SettingsGroup title="Ollama server" description="The Ollama server Synapse talks to first.">
                      <Field label="Server address">
                        <div className="settings-input-row">
                          <input
                            type="text"
                            value={formData.ollamaHost}
                            onChange={(e) => setFormData({ ...formData, ollamaHost: e.target.value })}
                            className="font-mono"
                            placeholder="http://localhost:11434"
                          />
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => testNodeConnection(formData.ollamaHost)}
                            disabled={currentHostStatus.testing}
                          >
                            <RefreshCw size={13} className={currentHostStatus.testing ? 'animate-spin' : ''} />
                            <span>{currentHostStatus.testing ? 'Testing…' : 'Test connection'}</span>
                          </button>
                        </div>
                      </Field>
                      {currentHostStatus.online ? (
                        <div className="probe-badge online">
                          <CheckCircle size={13} />
                          <span>Connected ({currentHostStatus.latency_ms ?? '?'} ms), {discoveredModels.length} models available</span>
                        </div>
                      ) : (
                        <div className="probe-badge offline">
                          <AlertCircle size={13} />
                          <span>No answer from {formData.ollamaHost}. Check that <code>ollama serve</code> is running there.</span>
                        </div>
                      )}
                    </SettingsGroup>

                    <SettingsGroup title="Models" description="Which installed model does which job.">
                      <div className="settings-row-2col">
                        <Field label="Main model" hint="Lesson summaries, and the mentor when it uses the main model.">
                          <select
                            value={formData.primaryModel}
                            onChange={(e) => setFormData({ ...formData, primaryModel: e.target.value })}
                            className="font-mono"
                          >
                            {modelOptions(formData.primaryModel)}
                          </select>
                        </Field>
                        <Field label="Mentor model" hint="Mentor chat and quizzes. A smaller model answers faster but makes more mistakes.">
                          <select
                            value={formData.mentorModel || ''}
                            onChange={(e) => setFormData({ ...formData, mentorModel: e.target.value })}
                            className="font-mono"
                          >
                            <option value="">Same as main model</option>
                            {modelOptions(formData.mentorModel, false)}
                          </select>
                        </Field>
                      </div>
                    </SettingsGroup>

                    <SettingsGroup
                      title={`Other Ollama computers (${clusterNodes.length})`}
                      description="Optional: more machines on your network with Ollama. Requests go to whichever is free."
                      actions={
                        <>
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={scanCluster}
                            disabled={isScanningCluster}
                          >
                            <RefreshCw size={13} className={isScanningCluster ? 'animate-spin' : ''} />
                            <span>{isScanningCluster ? 'Checking…' : 'Check all'}</span>
                          </button>
                          <button
                            type="button"
                            className="btn-secondary icon-only"
                            onClick={() => setShowClusterAdvanced((prev) => !prev)}
                            aria-expanded={showClusterAdvanced}
                            title={showClusterAdvanced ? 'Hide computers' : 'Show computers'}
                          >
                            {showClusterAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>
                        </>
                      }
                    >
                      {showClusterAdvanced && (
                        <>
                          <div className="cluster-nodes-list">
                            {clusterNodes.map((nodeUrl) => {
                              const status = nodeStatuses[nodeUrl] || {};
                              const cleanKey = nodeUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
                              const currentPin = nodePins[cleanKey] || nodePins[nodeUrl] || '__auto__';

                              return (
                                <div key={nodeUrl} className="cluster-node-row">
                                  <span className={`status-dot ${status.online ? 'online' : 'offline'}`} title={status.online ? 'Online' : 'Offline'} />
                                  <span className="cluster-node-url-field font-mono" title={nodeUrl}>{nodeUrl}</span>
                                  <span className="node-latency">
                                    {status.latency_ms !== undefined ? `${status.latency_ms} ms` : status.online ? 'Ready' : 'Offline'}
                                  </span>
                                  <select
                                    value={currentPin}
                                    onChange={(e) => handleUpdateNodePin(nodeUrl, e.target.value)}
                                    className="node-pin-select font-mono"
                                    title="Only send this model to this computer"
                                    aria-label={`Model for ${nodeUrl}`}
                                  >
                                    <option value="__auto__">Any model</option>
                                    {(status.models || []).map((m) => (
                                      <option key={m} value={m}>Only {m}</option>
                                    ))}
                                  </select>
                                  <button
                                    type="button"
                                    className="btn-secondary icon-only"
                                    onClick={() => testNodeConnection(nodeUrl)}
                                    title="Check this computer"
                                  >
                                    <RefreshCw size={13} className={status.testing ? 'animate-spin' : ''} />
                                  </button>
                                  {clusterNodes.length > 1 && (
                                    <button
                                      type="button"
                                      className="btn-secondary icon-only danger"
                                      onClick={() => handleRemoveNode(nodeUrl)}
                                      title="Remove this computer"
                                    >
                                      <Trash2 size={13} />
                                    </button>
                                  )}
                                </div>
                              );
                            })}
                          </div>

                          <div className="settings-input-row">
                            <input
                              type="text"
                              value={newNodeUrl}
                              onChange={(e) => setNewNodeUrl(e.target.value)}
                              placeholder="http://192.168.1.50:11434"
                              className="font-mono"
                              aria-label="Address of another Ollama computer"
                            />
                            <button type="button" className="btn-secondary" onClick={handleAddNode}>
                              <Plus size={13} />
                              <span>Add computer</span>
                            </button>
                          </div>
                        </>
                      )}
                    </SettingsGroup>
                  </>
                )}

                {providerMode === 'cloud' && (
                  <>
                    <SettingsGroup title="Anthropic Claude" icon={<Cpu size={14} />}>
                      <div className="settings-row-2col">
                        <Field label="API key">
                          <div className="settings-input-row">
                            <input
                              type={showAnthropicKey ? 'text' : 'password'}
                              value={formData.anthropicApiKey || ''}
                              onChange={(e) => setFormData({ ...formData, anthropicApiKey: e.target.value })}
                              placeholder="sk-ant-api03-..."
                              className="font-mono"
                            />
                            <button
                              type="button"
                              className="btn-secondary icon-only"
                              onClick={() => setShowAnthropicKey((p) => !p)}
                              title={showAnthropicKey ? 'Hide key' : 'Show key'}
                            >
                              {showAnthropicKey ? <EyeOff size={13} /> : <Eye size={13} />}
                            </button>
                          </div>
                        </Field>
                        <Field label="Base URL (optional)">
                          <input
                            type="text"
                            value={formData.anthropicBaseUrl}
                            onChange={(e) => setFormData({ ...formData, anthropicBaseUrl: e.target.value })}
                            placeholder="https://api.anthropic.com"
                            className="font-mono"
                          />
                        </Field>
                      </div>
                    </SettingsGroup>

                    <SettingsGroup title="Google Gemini" icon={<Sparkles size={14} />}>
                      <div className="settings-row-2col">
                        <Field label="API key">
                          <div className="settings-input-row">
                            <input
                              type={showGeminiKey ? 'text' : 'password'}
                              value={formData.geminiApiKey || ''}
                              onChange={(e) => setFormData({ ...formData, geminiApiKey: e.target.value })}
                              placeholder="AIzaSy..."
                              className="font-mono"
                            />
                            <button
                              type="button"
                              className="btn-secondary icon-only"
                              onClick={() => setShowGeminiKey((p) => !p)}
                              title={showGeminiKey ? 'Hide key' : 'Show key'}
                            >
                              {showGeminiKey ? <EyeOff size={13} /> : <Eye size={13} />}
                            </button>
                          </div>
                        </Field>
                        <Field label="Base URL (optional)">
                          <input
                            type="text"
                            value={formData.geminiBaseUrl || ''}
                            onChange={(e) => setFormData({ ...formData, geminiBaseUrl: e.target.value })}
                            placeholder="https://generativelanguage.googleapis.com"
                            className="font-mono"
                          />
                        </Field>
                      </div>
                    </SettingsGroup>

                    <p className="settings-note">
                      Keys are stored on this computer in <code>~/.config/synapse/env</code>. They are sent only to the provider you use.
                    </p>
                  </>
                )}
              </>
            )}

            {/* TAB 3: COURSES */}
            {activeTab === 'storage' && (
              <>
                {storeMessage && (
                  <div className={`store-message-banner ${storeMessage.type}`}>
                    {storeMessage.type === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                    <span>{storeMessage.text}</span>
                  </div>
                )}

                <SettingsGroup
                  title={`Installed courses (${installedDomains.length} of 12 subject areas)`}
                  actions={
                    <button
                      type="button"
                      className="btn-secondary icon-only"
                      onClick={fetchPackages}
                      title="Refresh the list"
                      disabled={isLoadingPackages}
                    >
                      <RefreshCw size={13} className={isLoadingPackages ? 'animate-spin' : ''} />
                    </button>
                  }
                >
                  {installedDomains.length > 3 && (
                    <div className="store-search-box">
                      <Search size={13} className="store-search-icon" />
                      <input
                        type="text"
                        placeholder="Filter subject areas…"
                        value={storeSearch}
                        onChange={(e) => setStoreSearch(e.target.value)}
                      />
                    </div>
                  )}
                  <div className="store-packages-grid">
                    {installedDomains
                      .filter((p) => !storeSearch || `${p.domain} ${p.title || ''}`.toLowerCase().includes(storeSearch.toLowerCase()))
                      .map((pkg) => (
                        <div key={pkg.domain} className="store-package-card installed">
                          <h5>{pkg.title || pkg.domain.replace(/_/g, ' ')}</h5>
                          <div className="package-stats-row">
                            <span>{pkg.lesson_count || 0} lessons</span>
                            <span>·</span>
                            <span>{pkg.lab_count || 0} labs</span>
                          </div>
                          <div className="package-card-actions">
                            <button
                              type="button"
                              className="btn-secondary"
                              onClick={() => handleExportPack(pkg.domain)}
                              disabled={actionInProgress === `export-${pkg.domain}`}
                              title="Save this subject area as a .synpack file"
                            >
                              {actionInProgress === `export-${pkg.domain}` ? (
                                <Loader2 size={13} className="animate-spin" />
                              ) : (
                                <Download size={13} />
                              )}
                              <span>Export</span>
                            </button>
                            <button
                              type="button"
                              className="btn-secondary danger"
                              onClick={() => handleUninstallPack(pkg.domain)}
                              disabled={actionInProgress === `uninstall-${pkg.domain}`}
                              title="Remove from this computer"
                            >
                              <Trash2 size={13} />
                              <span>Remove</span>
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                </SettingsGroup>

                <SettingsGroup title="Add courses" description="Download all 12 subject areas, or import a .synpack file someone shared with you.">
                  <div className="settings-button-row">
                    {installedDomains.length < 12 ? (
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
                        <span>Download all courses (37 MB)</span>
                      </button>
                    ) : (
                      <span className="probe-badge online">
                        <CheckCircle size={13} />
                        <span>All 12 subject areas are installed.</span>
                      </span>
                    )}
                    {/* A real button (a <label> around a hidden input cannot be reached with Tab). */}
                    <button
                      type="button"
                      className="btn-secondary"
                      title="Import a .synpack file"
                      onClick={() => packFileInputRef.current?.click()}
                      disabled={actionInProgress === 'uploading'}
                    >
                      {actionInProgress === 'uploading' ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Upload size={13} />
                      )}
                      <span>Import .synpack file</span>
                    </button>
                    <input ref={packFileInputRef} type="file" accept=".synpack" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </div>
                </SettingsGroup>

                <SettingsGroup title="Write your own course" icon={<Terminal size={14} />} description="Courses are created in a terminal with the synapse command:">
                  <pre className="settings-code font-mono">
                    {`# Create a course and let the AI write its lessons\nbin/synapse add robotics autonomous_systems slam_navigation --title "SLAM"\n\n# Package it as a .synpack file to share\nbin/synapse pack robotics`}
                  </pre>
                </SettingsGroup>

                <SettingsGroup title="Maintenance" icon={<HardDrive size={14} />}>
                  <div className="settings-action-list">
                    <div className="settings-action-item">
                      <div>
                        <strong>Setup wizard</strong>
                        <span>Walk through the first-run setup again.</span>
                      </div>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          onClose();
                          onLaunchSetupWizard?.();
                        }}
                      >
                        <Sparkles size={13} />
                        <span>Open wizard</span>
                      </button>
                    </div>

                    <div className="settings-action-item">
                      <div>
                        <strong>Clear cache</strong>
                        <span>Deletes saved narration audio and translations. They are made again when needed. Chat history is kept.</span>
                      </div>
                      <button
                        type="button"
                        className="btn-secondary"
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
                        <Trash2 size={13} />
                        <span>Clear cache</span>
                      </button>
                    </div>

                    <div className="settings-action-item">
                      <div>
                        <strong>Compact database</strong>
                        <span>Shrinks the progress database file. Nothing is deleted.</span>
                      </div>
                      <button
                        type="button"
                        className="btn-secondary"
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
                            alert('Database compacted.');
                          } catch (err) {
                            alert(`Compacting the database failed: ${err instanceof Error ? err.message : err}`);
                          }
                        }}
                      >
                        <HardDrive size={13} />
                        <span>Compact</span>
                      </button>
                    </div>

                    <div className="settings-action-item">
                      <div>
                        <strong>Stop Synapse</strong>
                        <span>Stops the Synapse server on this computer. Start it again with bin/synapse.</span>
                      </div>
                      <button
                        type="button"
                        className="btn-secondary danger"
                        onClick={async () => {
                          if (!confirm('Stop the Synapse server?')) return;
                          try {
                            const res = await fetch('/api/system/shutdown', { method: 'POST' });
                            if (!res.ok) {
                              const data = await res.json().catch(() => ({}));
                              throw new Error(data.detail || `Server returned ${res.status}`);
                            }
                            alert('Synapse is stopping. You can close this tab.');
                          } catch (err) {
                            alert(`Stopping the server failed: ${err instanceof Error ? err.message : err}`);
                          }
                        }}
                      >
                        <Power size={13} />
                        <span>Stop server</span>
                      </button>
                    </div>
                  </div>
                </SettingsGroup>
              </>
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
