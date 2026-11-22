// Settings shape and defaults, shared by the app and the settings dialog.

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
