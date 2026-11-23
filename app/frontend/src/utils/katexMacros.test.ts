import test from 'node:test';
import assert from 'node:assert/strict';
import katex from 'katex';
import { KATEX_MACROS } from './katexMacros.ts';

// Commands real lessons use; without the macros KaTeX reports
// "Undefined control sequence" and learners see red source text.
for (const expr of ['\\Arg z', 'A \\with B', 'A \\parr B', '3 \\surhd 5']) {
  test(`renders ${expr}`, () => {
    assert.doesNotThrow(() => katex.renderToString(expr, { throwOnError: true, macros: { ...KATEX_MACROS } }));
    assert.throws(() => katex.renderToString(expr, { throwOnError: true }));
  });
}
