import React, { useState, useEffect } from 'react';
import { Settings, Palette, Cpu, X, Check } from 'lucide-react';

export interface AppSettings {
  theme: 'studio' | 'titanium' | 'monokai' | 'nordic';
  fontSize: 'compact' | 'standard' | 'large';
  readerWidth: 'full' | 'constrained';
  language: 'en' | 'cs' | 'de' | 'es' | 'ru';
  codeLigatures?: boolean;
  terminalFontSize?: '12px' | '13px' | '14px' | '15px';
  speechRate?: '0.85' | '1.0' | '1.15' | '1.3';
  ollamaHost: string;
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
  const [testResult, setTestResult] = useState<{ ok: boolean; latency_ms?: number; models?: string[]; error?: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    setFormData(settings);
    setTestResult(null);
  }, [settings, isOpen]);

  const handleTestOllama = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await fetch('/api/settings/test-ollama', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host: formData.ollamaHost }),
      });
      const data = await res.json();
      setTestResult(data);
    } catch (err: any) {
      setTestResult({ ok: false, error: err.message || 'Network error' });
    } finally {
      setIsTesting(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSaveSettings(formData);
    setSavedMessage(true);
    setTimeout(() => {
      setSavedMessage(false);
      onClose();
    }, 500);
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

            <div className="form-group">
              <label>Ollama Server Endpoint</label>
              <div className="input-action-row">
                <input
                  type="text"
                  value={formData.ollamaHost}
                  onChange={(e) => setFormData({ ...formData, ollamaHost: e.target.value })}
                  placeholder="http://localhost:11434"
                  className="text-input"
                />
                <button
                  type="button"
                  className="btn btn-secondary-sm btn-test-conn"
                  onClick={handleTestOllama}
                  disabled={isTesting || !formData.ollamaHost.trim()}
                  title="Ping Ollama server and verify available models"
                >
                  {isTesting ? 'Testing...' : 'Test Connection'}
                </button>
              </div>
              {testResult && (
                <div className={`conn-status-pill ${testResult.ok ? 'success' : 'failure'}`}>
                  {testResult.ok ? (
                    <span>✔ Online ({testResult.latency_ms}ms) • Models: {testResult.models?.slice(0, 3).join(', ') || 'ready'}</span>
                  ) : (
                    <span>✖ Connection failed: {testResult.error || 'Server unreachable'}</span>
                  )}
                </div>
              )}
              <span className="field-hint">e.g. http://localhost:11434 or http://homelab.local:11434</span>
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
