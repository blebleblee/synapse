import test from 'node:test';
import assert from 'node:assert/strict';
import { summarizeGeneration } from './generation.ts';

test('summarizeGeneration - every file failed is an error, not a silent reload', () => {
  const s = summarizeGeneration({ 'lesson_01.md': false, 'labs.md': false }, [], true);
  assert.equal(s.kind, 'error');
  assert.match(s.text, /2 file\(s\) could not be generated: lesson_01.md, labs.md/);
  assert.match(s.text, /existing lessons were kept/);
});

test('summarizeGeneration - files already on disk are not failures', () => {
  const s = summarizeGeneration({ 'lesson_01.md': false, 'labs.md': true }, ['lesson_01.md'], false);
  assert.deepEqual(s, { kind: 'success', text: 'Generated 1 file(s).' });
});

test('summarizeGeneration - partial failure of a new course says to run again', () => {
  const s = summarizeGeneration({ 'lesson_01.md': true, 'labs.md': false }, [], false);
  assert.equal(s.kind, 'error');
  assert.match(s.text, /Run it again/);
});

test('summarizeGeneration - nothing to do', () => {
  assert.equal(summarizeGeneration({ 'a.md': false }, ['a.md'], false).kind, 'info');
  assert.equal(summarizeGeneration(undefined, undefined, false).kind, 'info');
});
