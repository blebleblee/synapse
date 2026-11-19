import React, { useState } from 'react';
import { Lock, Shield, KeyRound, AlertCircle } from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onLoginSuccess: (token: string) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onLoginSuccess }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: password.trim() }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Authentication failed. Please verify your password.');
      }

      const data = await res.json();
      if (data.token) {
        localStorage.setItem('synapse_auth_token', data.token);
        onLoginSuccess(data.token);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop login-backdrop" style={{ zIndex: 9999 }}>
      <div className="modal-card login-card" style={{ maxWidth: '380px', width: '90%' }}>
        <div className="login-header" style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div
            className="login-icon-badge"
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'var(--accent-glow, rgba(234, 179, 8, 0.15))',
              border: '1px solid var(--accent-color, #eab308)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px auto',
              color: 'var(--accent-color, #eab308)',
            }}
          >
            <Shield size={24} />
          </div>
          <h3 style={{ margin: '0 0 6px 0', fontSize: '18px', fontWeight: 600 }}>
            Synapse Workbench
          </h3>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-muted)' }}>
            This hosted instance is protected. Enter password to unlock.
          </p>
        </div>

        {error && (
          <div
            className="login-error-banner"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 12px',
              borderRadius: '6px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: '#ef4444',
              fontSize: '12px',
              marginBottom: '16px',
            }}
          >
            <AlertCircle size={14} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '11px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '6px',
                color: 'var(--text-secondary)',
              }}
            >
              Instance Password
            </label>
            <div style={{ position: 'relative' }}>
              <KeyRound
                size={14}
                style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                  pointerEvents: 'none',
                }}
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password..."
                autoFocus
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '9px 12px 9px 32px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-input, var(--bg-surface))',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || !password.trim()}
            style={{
              width: '100%',
              padding: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '13px',
              fontWeight: 600,
              borderRadius: '6px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading || !password.trim() ? 0.6 : 1,
            }}
          >
            <Lock size={14} />
            <span>{isLoading ? 'Verifying...' : 'Unlock Workbench'}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
