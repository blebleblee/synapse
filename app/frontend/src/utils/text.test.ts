import test from 'node:test';
import assert from 'node:assert/strict';
import { toTitleCase, cleanLessonTitle, splitHighlight, toSlug } from './text.ts';

test('toTitleCase - replaces underscores and capitalizes words', () => {
  assert.equal(toTitleCase('postgresql_internals'), 'Postgresql Internals');
  assert.equal(toTitleCase('large_language_models'), 'Large Language Models');
  assert.equal(toTitleCase(''), '');
});

test('toTitleCase - keeps acronyms and unit prefixes upper case', () => {
  assert.equal(toTitleCase('ai'), 'AI');
  assert.equal(toTitleCase('3d_graphics'), '3D Graphics');
  assert.equal(toTitleCase('3d_printing'), '3D Printing');
  assert.equal(toTitleCase('aid_workers'), 'Aid Workers');
});

test('cleanLessonTitle - strips leading numbers and prefixes', () => {
  assert.equal(cleanLessonTitle('Lesson 01: Foundations'), 'Foundations');
  assert.equal(cleanLessonTitle('02 - Indexing Strategies'), 'Indexing Strategies');
  assert.equal(cleanLessonTitle('Architecture & Invariants'), 'Architecture & Invariants');
  assert.equal(cleanLessonTitle(''), '');
});

test('splitHighlight - identifies matching tokens case-insensitively', () => {
  const parts = splitHighlight('B-Tree index structure and leaf page traversal.', 'b-tree');
  assert.deepEqual(parts, [
    { text: 'B-Tree', isMatch: true },
    { text: ' index structure and leaf page traversal.', isMatch: false },
  ]);
});

test('splitHighlight - handles multiple search terms and boundaries', () => {
  const parts = splitHighlight('PostgreSQL page layout and write-ahead logging', 'page logging');
  assert.deepEqual(parts, [
    { text: 'PostgreSQL ', isMatch: false },
    { text: 'page', isMatch: true },
    { text: ' layout and write-ahead ', isMatch: false },
    { text: 'logging', isMatch: true },
  ]);
});

test('splitHighlight - handles empty query or no matches cleanly', () => {
  assert.deepEqual(splitHighlight('No matches here', ''), [
    { text: 'No matches here', isMatch: false },
  ]);
  assert.deepEqual(splitHighlight('No matches here', 'xyz'), [
    { text: 'No matches here', isMatch: false },
  ]);
  assert.deepEqual(splitHighlight('', 'test'), []);
});

test('toSlug - makes a folder-safe course or category name', () => {
  assert.equal(toSlug('Rust Internals'), 'rust_internals');
  assert.equal(toSlug('  Prompt Engineering & Spec-Driven  '), 'prompt_engineering_spec-driven');
  assert.equal(toSlug('Účetnictví 101'), 'ucetnictvi_101');
  assert.equal(toSlug('infra/structure'), 'infra_structure');
  assert.equal(toSlug('!!!'), '');
});
