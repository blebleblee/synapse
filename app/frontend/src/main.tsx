import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// Global automatic instance authentication interceptor
const originalFetch = window.fetch;
window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const token = localStorage.getItem('synapse_auth_token');
  const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : (input as Request).url;

  if (token && url.startsWith('/api') && !url.includes('/api/auth/login')) {
    init = init || {};
    const headers = new Headers(init.headers || {});
    if (!headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    init.headers = headers;
  }

  const response = await originalFetch(input, init);
  if (response.status === 401 && url.startsWith('/api') && !url.includes('/api/auth')) {
    window.dispatchEvent(new CustomEvent('synapse:unauthorized'));
  }
  return response;
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
