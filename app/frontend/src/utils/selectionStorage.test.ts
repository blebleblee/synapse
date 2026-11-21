import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parseStoredSelection,
  saveStoredSelection,
  clearStoredSelection,
  getStoredSelection
} from './selectionStorage.ts';

test('parseStoredSelection - parses valid payload with specific lesson', () => {
  const raw = JSON.stringify({ path: 'computing/data/postgresql', lessonId: 'lesson_01' });
  const result = parseStoredSelection(raw);
  assert.deepEqual(result, { path: 'computing/data/postgresql', lessonId: 'lesson_01' });
});

test('parseStoredSelection - parses valid payload with "all" lessons', () => {
  const raw = JSON.stringify({ path: 'computing/data/postgresql', lessonId: 'all' });
  const result = parseStoredSelection(raw);
  assert.deepEqual(result, { path: 'computing/data/postgresql', lessonId: 'all' });
});

test('parseStoredSelection - defaults missing or empty lessonId to "all"', () => {
  const raw = JSON.stringify({ path: 'computing/data/postgresql' });
  const result = parseStoredSelection(raw);
  assert.deepEqual(result, { path: 'computing/data/postgresql', lessonId: 'all' });

  const rawEmptyLesson = JSON.stringify({ path: 'computing/data/postgresql', lessonId: '   ' });
  const resultEmpty = parseStoredSelection(rawEmptyLesson);
  assert.deepEqual(resultEmpty, { path: 'computing/data/postgresql', lessonId: 'all' });
});

test('parseStoredSelection - rejects malformed JSON and non-object values safely', () => {
  assert.equal(parseStoredSelection(null), null);
  assert.equal(parseStoredSelection(''), null);
  assert.equal(parseStoredSelection('undefined'), null);
  assert.equal(parseStoredSelection('{ broken: json'), null);
  assert.equal(parseStoredSelection('12345'), null);
  assert.equal(parseStoredSelection('true'), null);
  assert.equal(parseStoredSelection('["computing/data/postgresql"]'), null);
});

test('parseStoredSelection - rejects invalid path types or empty path strings', () => {
  assert.equal(parseStoredSelection(JSON.stringify({ path: 123, lessonId: 'l1' })), null);
  assert.equal(parseStoredSelection(JSON.stringify({ path: '', lessonId: 'l1' })), null);
  assert.equal(parseStoredSelection(JSON.stringify({ path: '   ', lessonId: 'l1' })), null);
  assert.equal(parseStoredSelection(JSON.stringify({ path: null, lessonId: 'l1' })), null);
  assert.equal(parseStoredSelection(JSON.stringify({ noPath: true })), null);
});

test('getStoredSelection & saveStoredSelection - storage round-trip with mock localStorage', () => {
  const mockStorage = new Map<string, string>();
  globalThis.localStorage = {
    getItem: (key: string) => mockStorage.get(key) || null,
    setItem: (key: string, val: string) => mockStorage.set(key, val),
    removeItem: (key: string) => mockStorage.delete(key),
    clear: () => mockStorage.clear(),
    key: (idx: number) => Array.from(mockStorage.keys())[idx] || null,
    length: mockStorage.size
  };

  clearStoredSelection();
  assert.equal(getStoredSelection(), null);

  saveStoredSelection('computing/data/postgresql', 'lesson_02');
  assert.deepEqual(getStoredSelection(), {
    path: 'computing/data/postgresql',
    lessonId: 'lesson_02'
  });

  saveStoredSelection('computing/infrastructure/kubernetes', 'all');
  assert.deepEqual(getStoredSelection(), {
    path: 'computing/infrastructure/kubernetes',
    lessonId: 'all'
  });

  clearStoredSelection();
  assert.equal(getStoredSelection(), null);
});
