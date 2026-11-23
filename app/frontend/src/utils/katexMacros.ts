/**
 * LaTeX commands that lessons use legitimately but KaTeX does not define.
 * Shared by the reader (markdownRenderer.ts) and scripts/validate_render.mjs,
 * so what the validator passes is what learners see.
 */
export const KATEX_MACROS: Record<string, string> = {
  // Principal argument of a complex number (amsmath users define it)
  '\\Arg': '\\operatorname{Arg}',
  // Linear logic connectives (cmll package): additive and, multiplicative or
  '\\with': '\\mathbin{\\&}',
  '\\parr': '\\mathbin{\\text{⅋}}',
  // Sharkovskii ordering
  '\\surhd': '\\rhd',
};
