import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  X,
  Server,
  Key,
  Check,
  Loader2,
  RefreshCw,
  HardDrive
} from 'lucide-react';
import type { AppSettings } from './settingsDefaults';

interface SetupWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentSettings: AppSettings;
  onSaveSettings: (settings: AppSettings) => void;
}

type ProbeResult = { online: boolean; models: string[] };

// Asks the backend to probe exactly this host (browsers can't reach Ollama
// directly), so the answer comes back under the host name as typed.
async function probeHost(host: string): Promise<ProbeResult> {
  const clean = host.trim().replace(/\/$/, '');
  try {
    const res = await fetch(`/api/settings/cluster-status?hosts=${encodeURIComponent(clean)}`);
    if (!res.ok) return { online: false, models: [] };
    const node = (await res.json())[clean];
    return node?.online ? { online: true, models: node.models || [] } : { online: false, models: [] };
  } catch {
    return { online: false, models: [] };
  }
}

// Mounted only while open: each opening probes once and starts at step 1.
export const SetupWizardModal: React.FC<SetupWizardModalProps> = ({ isOpen, ...props }) =>
  isOpen ? <SetupWizardPanel {...props} /> : null;

const SetupWizardPanel: React.FC<Omit<SetupWizardModalProps, 'isOpen'>> = ({
  onClose,
  currentSettings,
  onSaveSettings,
}) => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [localOllamaOnline, setLocalOllamaOnline] = useState<boolean | null>(null);
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);
  const [isProbing, setIsProbing] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string>(
    currentSettings.primaryModel || 'qwen2.5-coder:32b'
  );
  const [ollamaHost, setOllamaHost] = useState<string>(
    currentSettings.ollamaHost || 'http://localhost:11434'
  );
  const [anthropicKey, setAnthropicKey] = useState<string>(currentSettings.anthropicApiKey || '');
  const [geminiKey, setGeminiKey] = useState<string>(currentSettings.geminiApiKey || '');

  const applyProbe = useCallback((result: ProbeResult) => {
    setLocalOllamaOnline(result.online);
    setDiscoveredModels(result.models);
    if (result.models.length > 0) {
      setSelectedModel((cur) => (result.models.includes(cur) ? cur : result.models[0]));
    }
    setIsProbing(false);
  }, []);

  const probeOllama = async (host = ollamaHost) => {
    setIsProbing(true);
    applyProbe(await probeHost(host));
  };

  const initialHost = currentSettings.ollamaHost || 'http://localhost:11434';
  useEffect(() => {
    let live = true;
    probeHost(initialHost).then((result) => { if (live) applyProbe(result); });
    return () => { live = false; };
  }, [initialHost, applyProbe]);


  const handleFinish = () => {
    const updated: AppSettings = {
      ...currentSettings,
      ollamaHost,
      primaryModel: selectedModel,
      mentorModel: selectedModel,
      anthropicApiKey: anthropicKey,
      geminiApiKey: geminiKey,
    };
    localStorage.setItem('synapse_onboarding_completed', 'true');
    onSaveSettings(updated);
    onClose();
  };

  const handleSkip = () => {
    localStorage.setItem('synapse_onboarding_completed', 'true');
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={handleSkip}>
      <div className="setup-wizard-card" onClick={(e) => e.stopPropagation()}>
        {/* Wizard Header */}
        <div className="wizard-header">
          <div className="wizard-brand">
            <Sparkles size={20} className="wizard-brand-icon" />
            <span>Synapse Setup Wizard</span>
          </div>
          <button className="icon-btn-sm" onClick={handleSkip} title="Skip setup">
            <X size={15} />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="wizard-stepper">
          {[
            { num: 1, label: 'Welcome' },
            { num: 2, label: 'AI Engine' },
            { num: 3, label: 'Cloud Keys' },
            { num: 4, label: 'Ready' },
          ].map((s) => (
            <div
              key={s.num}
              className={`wizard-step-node ${step === s.num ? 'active' : step > s.num ? 'completed' : ''}`}
            >
              <div className="step-num-circle">
                {step > s.num ? <Check size={12} /> : s.num}
              </div>
              <span className="step-name">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="wizard-body">
          {step === 1 && (
            <div className="wizard-pane">
              <div className="wizard-hero-icon">
                <HardDrive size={42} />
              </div>
              <h3>Welcome to Synapse Workbench</h3>
              <p>
                Synapse is a local-first, privacy-respecting AI learning environment.
                All your course materials, active recall decks, and mentor chats stay strictly on your local machine.
              </p>
              <div className="wizard-feature-list">
                <div className="feature-item">
                  <CheckCircle size={15} className="feature-icon" />
                  <span>Masterclasses across 12 core domains, from computing and engineering to the arts, installable for offline use</span>
                </div>
                <div className="feature-item">
                  <CheckCircle size={15} className="feature-icon" />
                  <span>Interactive Socratic Mentor connected to live terminal sessions</span>
                </div>
                <div className="feature-item">
                  <CheckCircle size={15} className="feature-icon" />
                  <span>Private by design: zero telemetry, 100% offline capable</span>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="wizard-pane">
              <h3>Local AI Engine Detection</h3>
              <p>Synapse can run entirely on your local GPU via Ollama or LM Studio.</p>

              <div className="wizard-probe-box">
                <div className="probe-header-row">
                  <div className="probe-host-label">
                    <Server size={14} />
                    <input
                      type="text"
                      value={ollamaHost}
                      onChange={(e) => setOllamaHost(e.target.value)}
                      className="wizard-input font-mono"
                      style={{ padding: '2px 8px', fontSize: '12px', width: '220px' }}
                      title="Ollama host URL"
                    />
                  </div>
                  <button
                    type="button"
                    className="btn-secondary-sm"
                    onClick={() => probeOllama(ollamaHost)}
                    disabled={isProbing}
                  >
                    <RefreshCw size={12} className={isProbing ? 'animate-spin' : ''} />
                    <span>{isProbing ? 'Probing...' : 'Re-test'}</span>
                  </button>
                </div>

                <div className="probe-status-row">
                  {isProbing ? (
                    <div className="probe-badge checking">
                      <Loader2 size={13} className="animate-spin" />
                      <span>Detecting local Ollama service...</span>
                    </div>
                  ) : localOllamaOnline ? (
                    <div className="probe-badge online">
                      <CheckCircle size={13} />
                      <span>Local Ollama is Online ({discoveredModels.length} models found)</span>
                    </div>
                  ) : (
                    <div className="probe-badge offline">
                      <AlertCircle size={13} />
                      <span>Ollama not detected on localhost. You can start it anytime via <code>ollama serve</code> or use cloud models.</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="wizard-field-group">
                <label>Primary Masterclass & Mentor Model</label>
                {discoveredModels.length > 0 ? (
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="wizard-select"
                  >
                    {discoveredModels.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    placeholder="e.g. qwen2.5-coder:32b or llama3.3:70b"
                    className="wizard-input"
                  />
                )}
                <span className="wizard-field-hint">
                  Recommended local models: <code>qwen2.5-coder:32b</code>, <code>llama3.3:70b</code>, or <code>deepseek-r1:14b</code>.
                </span>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="wizard-pane">
              <div className="wizard-pane-header">
                <Key size={24} className="wizard-header-icon" />
                <div>
                  <h3>Cloud API Keys (Optional)</h3>
                  <p>If you prefer cloud models or don't have a local GPU, you can provide API keys below.</p>
                </div>
              </div>

              <div className="wizard-field-group">
                <label>Anthropic API Key (Claude Sonnet / Opus)</label>
                <input
                  type="password"
                  value={anthropicKey}
                  onChange={(e) => setAnthropicKey(e.target.value)}
                  placeholder="sk-ant-..."
                  className="wizard-input font-mono"
                />
              </div>

              <div className="wizard-field-group">
                <label>Google Gemini API Key (Gemini 2.5 Flash / Pro)</label>
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="AIzaSy..."
                  className="wizard-input font-mono"
                />
              </div>

              <div className="wizard-info-note">
                Keys are stored securely in your personal local environment configuration (<code>~/.config/synapse/env</code>) and are never sent to third-party tracking services.
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="wizard-pane">
              <div className="wizard-hero-icon success">
                <CheckCircle size={44} />
              </div>
              <h3>Configuration Complete</h3>
              <p>Your learning environment is configured and ready.</p>

              <div className="wizard-summary-box">
                <div className="summary-row">
                  <span className="summary-lbl">Primary AI Model:</span>
                  <span className="summary-val font-mono">{selectedModel}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-lbl">AI Host:</span>
                  <span className="summary-val font-mono">{ollamaHost}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-lbl">Cloud Fallbacks:</span>
                  <span className="summary-val">
                    {anthropicKey ? 'Anthropic Configured' : geminiKey ? 'Gemini Configured' : 'Local Only (Private)'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Wizard Footer Navigation */}
        <div className="wizard-footer">
          <button type="button" className="btn-secondary" onClick={handleSkip}>
            Skip & Use Defaults
          </button>

          <div className="wizard-nav-btns">
            {step > 1 && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setStep((prev) => (prev - 1) as any)}
              >
                <ArrowLeft size={14} />
                <span>Back</span>
              </button>
            )}

            {step < 4 ? (
              <button
                type="button"
                className="btn-primary"
                onClick={() => setStep((prev) => (prev + 1) as any)}
              >
                <span>Continue</span>
                <ArrowRight size={14} />
              </button>
            ) : (
              <button type="button" className="btn-primary" onClick={handleFinish}>
                <Sparkles size={14} />
                <span>Enter Workbench</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
