import test from 'node:test';
import assert from 'node:assert/strict';
import { terminalSafeText } from './terminalText.ts';

test('terminalSafeText - a snippet cannot end the bracketed paste early', () => {
  const evil = 'echo hi\x1b[201~\nrm -rf ~/x\n';
  const safe = terminalSafeText(evil);
  assert.ok(!safe.includes('\x1b'));
  assert.equal(safe, 'echo hi[201~\nrm -rf ~/x');
});

test('terminalSafeText - keeps tabs and newlines, normalizes CRLF', () => {
  assert.equal(terminalSafeText('  a\tb\r\nc\rd  '), 'a\tb\nc\nd');
});

test('terminalSafeText - drops C1 controls and DEL', () => {
  assert.equal(terminalSafeText('a\x9bb\x7fc\x07'), 'abc');
});
