import test from 'node:test';
import assert from 'node:assert/strict';
import { mentorSuggestions } from './mentorSuggestions.ts';

test('technical courses keep terminal and debugging prompts', () => {
  const labels = mentorSuggestions('computing', 'Bash').map((s) => s.label).join(' | ');
  assert.match(labels, /terminal/);
  assert.match(labels, /debugging/);
});

test('non-technical courses get no terminal or engineering prompts', () => {
  for (const domain of ['arts', 'humanities', 'languages', 'business', undefined]) {
    const all = mentorSuggestions(domain, 'Color Theory').map((s) => `${s.label} ${s.prompt}`).join(' ');
    assert.doesNotMatch(all, /terminal|debugging|engineers/i, String(domain));
  }
});

test('the course name goes into the prompt', () => {
  assert.ok(mentorSuggestions('arts', 'Color Theory').some((s) => s.prompt.includes('Color Theory')));
});
