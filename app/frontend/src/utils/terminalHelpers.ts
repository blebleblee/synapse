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
