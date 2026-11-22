/**
 * Finds LaTeX math in lesson prose. Kept free of imports so
 * scripts/validate_render.mjs can load this exact file (Node strips the
 * types) and check the same spans the reader renders.
 */

/**
 * Inline math `$...$` (Pandoc's rule): the opening `$` is not escaped and is
 * followed by a non-space; the closing `$` follows a non-space and is not
 * followed by a digit. So "$5 and $10" stays text while "$x$" is math. Math
 * never starts with ")" or ends with "(", which keeps "Cost ($)" labels as text.
 * An escaped \$ may appear inside ("\xleftarrow{\$}").
 */
const INLINE_MATH = /(?<![\\$])\$(?=[^\s$)])((?:\\\$|[^$\n])+?)(?<=[^\s\\(])\$(?![\d$])/g;
const DISPLAY_MATH = /\$\$([\s\S]*?)\$\$/g;
const PROSE_WORD = /^[A-Za-z]{3,}[,.;:)]*$/;

/**
 * Text between two prices or spreadsheet references ("$31.25 per unit, and
 * =($") is prose, not math: several plain words and no LaTeX command. Real
 * math writes its words as \text{...}.
 */
function isProse(span: string): boolean {
  return !span.includes('\\') && span.split(/\s+/).filter((w) => PROSE_WORD.test(w)).length >= 3;
}

/** Applies `fn` to the prose only; fenced (```) and inline (`) code is left as is. */
export function transformOutsideCode(markdown: string, fn: (prose: string) => string): string {
  const saved: string[] = [];
  const keep = (code: string) => {
    saved.push(code);
    return `%%SYNAPSE_CODE_${saved.length - 1}%%`;
  };
  const masked = markdown.replace(/```[\s\S]*?```/g, keep).replace(/`[^`\n]+?`/g, keep);
  return fn(masked).replace(/%%SYNAPSE_CODE_(\d+)%%/g, (_, i) => saved[Number(i)]);
}

/** Replaces display and inline math in prose (call it via transformOutsideCode). */
export function replaceMath(
  prose: string,
  renderDisplay: (math: string) => string,
  renderInline: (math: string) => string,
): string {
  return prose
    .replace(DISPLAY_MATH, (_, math: string) => renderDisplay(math.trim()))
    .replace(INLINE_MATH, (whole: string, math: string) =>
      isProse(math.trim()) ? whole : renderInline(math.trim()));
}

/** The inline math spans of a text, as replaceMath would render them. */
export function findInlineMath(prose: string): string[] {
  const found: string[] = [];
  replaceMath(prose.replace(DISPLAY_MATH, ''), (m) => m, (m) => {
    found.push(m);
    return m;
  });
  return found;
}
