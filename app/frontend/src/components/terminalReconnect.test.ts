import test from 'node:test';
import assert from 'node:assert/strict';
import { shouldReconnectTerminal, retireSocket } from '../utils/terminalHelpers.ts';

test('shouldReconnectTerminal - halts reconnect on code 1008 (policy violation / unauthorized)', () => {
  assert.equal(shouldReconnectTerminal(1008), false);
});

test('shouldReconnectTerminal - halts reconnect on code 1000 (normal deliberate closure)', () => {
  assert.equal(shouldReconnectTerminal(1000), false);
});

test('shouldReconnectTerminal - allows reconnect on abnormal closure or network drop (1006, 1001, etc.)', () => {
  assert.equal(shouldReconnectTerminal(1006), true); // 1006 abnormal closure
  assert.equal(shouldReconnectTerminal(1001), true); // 1001 going away
  assert.equal(shouldReconnectTerminal(1011), true); // 1011 internal server error
});

test('retireSocket - detaches handlers so a replaced socket cannot reconnect', () => {
  let closedWith: number | undefined;
  const ws: any = {
    onopen: () => {}, onmessage: () => {}, onerror: () => {}, onclose: () => { throw new Error('old onclose ran'); },
    close(code?: number) { closedWith = code; this.onclose?.({ code: 1005 }); },
  };
  retireSocket(ws);
  assert.equal(ws.onclose, null);
  assert.equal(ws.onmessage, null);
  assert.equal(closedWith, 1000);
});
