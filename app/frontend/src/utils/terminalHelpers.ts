/**
 * Terminal connection and lifecycle helper functions.
 */

/**
 * Determines whether the terminal WebSocket should automatically reconnect upon closure.
 * Halts reconnect on:
 * - 1000: Normal deliberate closure
 * - 1008: Policy violation (e.g. authentication rejection / missing token)
 * Reconnects on unexpected drops or network timeouts (e.g. 1006, 1001, 1011).
 */
export function shouldReconnectTerminal(closeCode: number): boolean {
  return closeCode !== 1000 && closeCode !== 1008;
}

/**
 * Closes a socket that is being replaced (environment switch, reconnect).
 * Its handlers are detached first: otherwise its onclose would schedule a
 * reconnect to the old environment and close the new socket.
 */
export function retireSocket(ws: Pick<WebSocket, 'close' | 'onopen' | 'onmessage' | 'onerror' | 'onclose'>): void {
  ws.onopen = null;
  ws.onmessage = null;
  ws.onerror = null;
  ws.onclose = null;
  try {
    ws.close(1000);
  } catch {
    /* already closed */
  }
}
