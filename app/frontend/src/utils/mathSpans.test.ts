import test from 'node:test';
import assert from 'node:assert/strict';
import { transformOutsideCode, replaceMath, findInlineMath } from './mathSpans.ts';

const mark = (md: string) => replaceMath(md, (m) => `[D:${m}]`, (m) => `[I:${m}]`);

test('transformOutsideCode leaves fenced and inline code untouched', () => {
  const md = 'a <5 b\n```rust\nregs: IoMem<0x100>,\n```\nand `i<10` too';
  const out = transformOutsideCode(md, (prose) => prose.replace(/<(?=\d)/g, '&lt;'));
  assert.equal(out, 'a &lt;5 b\n```rust\nregs: IoMem<0x100>,\n```\nand `i<10` too');
});

test('replaceMath renders display and inline math', () => {
  assert.equal(mark('$$E = mc^2$$ and $x^2$.'), '[D:E = mc^2] and [I:x^2].');
});

test('replaceMath does not treat prices as math', () => {
  assert.equal(mark('It costs $5 and $10 per seat.'), 'It costs $5 and $10 per seat.');
  assert.equal(mark('Pay $20, then $x$ more.'), 'Pay $20, then [I:x] more.');
  assert.equal(mark('Budget: $1,200 to $3,400.'), 'Budget: $1,200 to $3,400.');
  assert.equal(mark('From $5 to $x$'), 'From $5 to [I:x]');
});

test('replaceMath ignores escaped dollars and shell prompts', () => {
  assert.equal(mark('Run $ ls then echo \\$HOME and $PATH.'), 'Run $ ls then echo \\$HOME and $PATH.');
});

test('findInlineMath matches what replaceMath renders', () => {
  assert.deepEqual(findInlineMath('Pay $20, then $a<b$ and $5 ok'), ['a<b']);
});

test('replaceMath leaves prose between prices and cell references alone', () => {
  const md = 'Shipping is $31.25 per unit. Cell C10 computes the return cost as =($C$5*2).';
  assert.equal(mark(md), md);
  assert.equal(mark('Revenue ($) and Cost ($) columns, with $\\text{margin} = r - c$.'),
    'Revenue ($) and Cost ($) columns, with [I:\\text{margin} = r - c].');
});

test('replaceMath keeps an escaped dollar inside math', () => {
  assert.equal(mark('Pick $r \\xleftarrow{\\$} \\mathbb{Z}_q$ at random.'), 'Pick [I:r \\xleftarrow{\\$} \\mathbb{Z}_q] at random.');
});
