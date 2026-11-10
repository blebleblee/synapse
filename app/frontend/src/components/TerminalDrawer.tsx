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
  Layers
} from 'lucide-react';

export interface TerminalDrawerHandle {
  runCommand: (command: string) => void;
}

interface TerminalDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const TerminalDrawer = forwardRef<TerminalDrawerHandle, TerminalDrawerProps>(({ isOpen, onToggle }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [terminalHeight, setTerminalHeight] = useState(260);
  const [terminalEnv, setTerminalEnv] = useState<'host' | 'docker' | 'k8s'>('host');
  const isDraggingRef = useRef(false);

  const connectWs = (env = terminalEnv) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/terminal?env=${env}`;

    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      setConnected(true);
      if (termRef.current && fitAddonRef.current) {
        fitAddonRef.current.fit();
        const cols = termRef.current.cols;
        const rows = termRef.current.rows;
        ws.send(JSON.stringify({ type: 'resize', cols, rows }));
      }
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

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    wsRef.current = ws;
  };

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new Terminal({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
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
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);

    termRef.current = term;
    fitAddonRef.current = fitAddon;

    term.onData((data) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(data);
      }
    });

    connectWs('host');

    const resizeObserver = new ResizeObserver(() => {
      if (isOpen && fitAddonRef.current && termRef.current) {
        fitAddonRef.current.fit();
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'resize',
            cols: termRef.current.cols,
            rows: termRef.current.rows,
          }));
        }
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
      if (fitAddonRef.current && termRef.current) {
        fitAddonRef.current.fit();
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      if (wsRef.current) wsRef.current.close();
      term.dispose();
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        if (fitAddonRef.current && termRef.current) {
          fitAddonRef.current.fit();
        }
      }, 100);
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
          <div className="terminal-title">
            <TerminalIcon size={15} className="terminal-icon" />
            <span>Terminal</span>
            <span className={`status-dot ${connected ? 'online' : 'offline'}`} title={connected ? 'Connected' : 'Disconnected'} />
          </div>

          {/* Labeled Environment Profile Selector on the Left */}
          <div className="terminal-env-selector" onClick={(e) => e.stopPropagation()}>
            <span className="env-label">Environment:</span>
            <Layers size={13} className="env-icon" />
            <select
              value={terminalEnv}
              onChange={(e) => handleEnvChange(e.target.value as any)}
              className="env-select"
              title="Switch execution environment"
            >
              <option value="host">Host Shell (Local)</option>
              <option value="docker">Linux Sandbox (Docker / Rancher)</option>
              <option value="k8s">Kubernetes Pod (k3s Cluster)</option>
            </select>
          </div>
        </div>

        <div className="terminal-actions" onClick={(e) => e.stopPropagation()}>
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

      <div className="terminal-body" ref={containerRef} style={{ display: isOpen ? 'block' : 'none' }} />
    </div>
  );
});
