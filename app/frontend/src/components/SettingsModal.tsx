import React, { useState, useEffect } from 'react';
import { Settings, Palette, Cpu, X, Check } from 'lucide-react';

export interface AppSettings {
  theme: 'studio' | 'titanium' | 'monokai' | 'nordic';
  fontSize: 'compact' | 'standard' | 'large';
  readerWidth: 'full' | 'constrained';
  ollamaHost: string;
  primaryModel: string;
  reviewerModel: string;
  geminiApiKey: string;
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'studio',
  fontSize: 'standard',
  readerWidth: 'full',
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

  useEffect(() => {
    setFormData(settings);
  }, [settings, isOpen]);

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
                  <option value="constrained">Comfortable Column (960px)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <div className="section-title">
              <Cpu size={14} />
              <span>AI Engine & Model Routing</span>
            </div>

            <div className="form-group">
              <label>Ollama Server URL</label>
              <input
                type="text"
                value={formData.ollamaHost}
                onChange={(e) => setFormData({ ...formData, ollamaHost: e.target.value })}
                placeholder="http://localhost:11434"
              />
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
