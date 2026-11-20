import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import {
  Terminal as TerminalIcon,
  ChevronDown,
  ChevronUp,
  Trash2,
  RefreshCw,
  Maximize2,
  Minimize2,
  Layers,
  HelpCircle,
  X
} from 'lucide-react';

export interface TerminalDrawerHandle {
  runCommand: (command: string) => void;
  getRecentOutput: (lineCount?: number) => string;
}

interface TerminalDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
  onConnectionChange?: (connected: boolean) => void;
}

export const TerminalDrawer = forwardRef<TerminalDrawerHandle, TerminalDrawerProps>(({ isOpen, onToggle, onConnectionChange }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [terminalHeight, setTerminalHeight] = useState(260);
  const [terminalEnv, setTerminalEnv] = useState<'host' | 'docker' | 'k8s'>('host');
  const [showSetupGuide, setShowSetupGuide] = useState(false);
  const isDraggingRef = useRef(false);
  const reconnectTimerRef = useRef<any>(null);
  const isUnmountedRef = useRef(false);
  const lastSizeRef = useRef<{ cols: number; rows: number }>({ cols: 0, rows: 0 });

  const fitTerminal = () => {
    if (!termRef.current || !containerRef.current || !isOpen || !fitAddonRef.current) return;

    try {
      fitAddonRef.current.fit();
      const cols = termRef.current.cols;
      const rows = termRef.current.rows;

      if (
        wsRef.current &&
        wsRef.current.readyState === WebSocket.OPEN &&
        cols > 0 &&
        rows > 0 &&
        (cols !== lastSizeRef.current.cols || rows !== lastSizeRef.current.rows)
      ) {
        lastSizeRef.current = { cols, rows };
        wsRef.current.send(JSON.stringify({
          type: 'resize',
          cols,
          rows,
        }));
      }
    } catch {
      // Ignored if container layout is pending
    }
  };

  const connectWs = (env = terminalEnv) => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('synapse_auth_token');
    const tokenParam = token ? `&token=${encodeURIComponent(token)}` : '';
    const wsUrl = `${protocol}//${host}/ws/terminal?env=${env}${tokenParam}`;

    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      setConnected(true);
      onConnectionChange?.(true);
      fitTerminal();
      termRef.current?.focus();
    };

    ws.onmessage = (event) => {
      if (termRef.current) {
        if (event.data instanceof ArrayBuffer) {
          termRef.current.write(new Uint8Array(event.data));
        } else {
          termRef.current.write(event.data);
        }
      }
    };

    ws.onclose = () => {
      setConnected(false);
      onConnectionChange?.(false);
      if (!isUnmountedRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          connectWs(env);
        }, 2500);
      }
    };
    ws.onerror = () => {
      setConnected(false);
      onConnectionChange?.(false);
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new Terminal({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: '"Hack Nerd Font Mono", "Hack Nerd Font", "Inconsolata for Powerline", "MesloLGS NF", "JetBrainsMono Nerd Font", "JetBrains Mono", "FiraCode Nerd Font", "Fira Code", PowerlineSymbols, SymbolsNerdFontMono, Menlo, Monaco, "Cascadia Code", Consolas, "Courier New", monospace',
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        selectionBackground: '#388bfd33',
        black: '#0d1117',
        red: '#ff7b72',
        green: '#3fb950',
        yellow: '#d29922',
        blue: '#58a6ff',
        magenta: '#bc8cff',
        cyan: '#39c5cf',
        white: '#b1bac4',
      },
      convertEol: true,
      customGlyphs: true,
      rescaleOverlappingGlyphs: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);

    termRef.current = term;
    fitAddonRef.current = fitAddon;

    if (typeof document !== 'undefined' && document.fonts?.ready) {
      document.fonts.ready.then(() => {
        if (!isUnmountedRef.current && isOpen) {
          fitTerminal();
          term.refresh(0, term.rows - 1);
        }
      });
    }

    term.onData((data) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(data);
      }
    });

    connectWs('host');

    const resizeObserver = new ResizeObserver(() => {
      if (isOpen) {
        fitTerminal();
      }
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    // Drag handle resizing listeners
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newHeight = window.innerHeight - e.clientY;
      if (newHeight >= 120 && newHeight <= window.innerHeight * 0.85) {
        setTerminalHeight(newHeight);
      }
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      document.body.style.cursor = '';
      fitTerminal();
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      resizeObserver.disconnect();
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      if (wsRef.current) wsRef.current.close();
      term.dispose();
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        fitTerminal();
        termRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen, isMaximized, terminalHeight]);

  useImperativeHandle(ref, () => ({
    runCommand(command: string) {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(command.trim() + '\n');
        if (!isOpen) {
          onToggle();
        }
      }
    },
    getRecentOutput(lineCount = 40): string {
      if (!termRef.current) return '';
      try {
        const buffer = termRef.current.buffer.active;
        const lines: string[] = [];
        // Scan around active cursor position (baseY + cursorY) to avoid trailing blank viewport rows
        const currentActiveLine = Math.min(buffer.length - 1, buffer.baseY + buffer.cursorY + 1);
        const startLine = Math.max(0, currentActiveLine - lineCount);
        for (let i = startLine; i <= currentActiveLine; i++) {
          const line = buffer.getLine(i);
          if (line) {
            const str = line.translateToString(true);
            if (str.trim().length > 0) {
              lines.push(str);
            }
          }
        }
        return lines.join('\n').trim();
      } catch (err) {
        console.error('Failed to read terminal buffer:', err);
        return '';
      }
    },
  }));

  const handleClear = () => {
    if (termRef.current) {
      termRef.current.clear();
    }
  };

  const handleEnvChange = (newEnv: 'host' | 'docker' | 'k8s') => {
    setTerminalEnv(newEnv);
    if (termRef.current) {
      termRef.current.write(`\r\n\x1b[33m[*] Switching execution environment to: ${newEnv.toUpperCase()}...\x1b[0m\r\n`);
    }
    connectWs(newEnv);
  };

  const currentHeight = !isOpen ? 36 : isMaximized ? 'calc(100vh - 38px)' : `${terminalHeight}px`;

  return (
    <div
      className={`terminal-drawer ${isOpen ? 'open' : 'closed'} ${isMaximized ? 'maximized' : ''}`}
      style={{ height: currentHeight }}
    >
      {/* Resizing Drag Handle */}
      {isOpen && !isMaximized && (
        <div
          className="terminal-resize-handle"
          onMouseDown={(e) => {
            e.preventDefault();
            isDraggingRef.current = true;
            document.body.style.cursor = 'ns-resize';
          }}
          title="Drag to resize terminal height"
        />
      )}

      <div className="terminal-header" onClick={onToggle}>
        <div className="terminal-header-left">
          <div className="terminal-env-selector" onClick={(e) => e.stopPropagation()}>
            <TerminalIcon size={14} className="terminal-icon" />
            <span
              className={`status-dot ${connected ? 'online' : 'offline'}`}
              title={connected ? 'Terminal PTY: Connected' : 'Terminal PTY: Disconnected (Click restart to reconnect)'}
            />
            <Layers size={13} className="env-icon" />
            <select
              value={terminalEnv}
              onChange={(e) => handleEnvChange(e.target.value as any)}
              className="env-select"
              title="Execution Environment Profile"
            >
              <option value="host">Host Shell (Local)</option>
              <option value="docker">Linux Sandbox (Docker / Rancher)</option>
              <option value="k8s">Kubernetes Pod (k3s Cluster)</option>
            </select>
          </div>
        </div>

        <div className="terminal-actions" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            className={`btn-setup-guide ${showSetupGuide ? 'active' : ''}`}
            onClick={() => setShowSetupGuide((prev) => !prev)}
            title="Setup Guide for Rancher Desktop & k3s Sandbox"
          >
            <HelpCircle size={12} />
            <span>Setup Guide</span>
          </button>
          <button className="icon-btn" onClick={() => connectWs(terminalEnv)} title="Restart Terminal Session">
            <RefreshCw size={13} />
          </button>
          <button className="icon-btn" onClick={handleClear} title="Clear Terminal Screen">
            <Trash2 size={13} />
          </button>
          <button
            className="icon-btn"
            onClick={() => {
              if (!isOpen) onToggle();
              setIsMaximized(!isMaximized);
            }}
            title={isMaximized ? 'Restore View' : 'Maximize / Fullscreen Terminal'}
          >
            {isMaximized ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
          <button className="icon-btn" onClick={onToggle} title={isOpen ? 'Collapse' : 'Expand'}>
            {isOpen ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          </button>
        </div>
      </div>

      {showSetupGuide && (
        <div className="terminal-setup-banner">
          <div className="setup-banner-header">
            <strong>Rancher Desktop & k3s Sandbox Setup Guide</strong>
            <button className="icon-btn" onClick={() => setShowSetupGuide(false)}><X size={12} /></button>
          </div>
          <div className="setup-banner-grid">
            <div className="setup-col">
              <h5>🐳 Linux Sandbox (Docker / Rancher)</h5>
              <p>1. Install via Homebrew: <code>brew install --cask rancher</code></p>
              <p>2. In Preferences &rarr; Container Engine, select <strong>dockerd (moby)</strong>.</p>
              <p>3. Verify socket is active: <code>docker info</code></p>
            </div>
            <div className="setup-col">
              <h5>☸️ Kubernetes Pod (k3s Cluster)</h5>
              <p>1. In Rancher Desktop &rarr; Preferences &rarr; Kubernetes, enable k3s.</p>
              <p>2. Wait for cluster status to reach <strong>Running</strong>.</p>
              <p>3. Test cluster node connectivity: <code>kubectl get nodes</code></p>
            </div>
          </div>
        </div>
      )}

      <div
        className="terminal-body"
        ref={containerRef}
        onClick={() => termRef.current?.focus()}
        style={{ display: isOpen ? 'block' : 'none' }}
      />
    </div>
  );
});
