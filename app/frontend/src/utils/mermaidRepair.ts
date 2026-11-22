/**
 * Repairs common Mermaid syntax slips in generated lessons before rendering.
 * Kept free of imports so scripts/validate_render.mjs can load this exact file
 * (Node strips the types) and validate what the reader really renders.
 */
function isLightHexColor(hexStr: string): boolean {
  const clean = hexStr.replace('#', '').trim();
  let r = 0, g = 0, b = 0;
  if (clean.length === 3) {
    r = parseInt(clean[0] + clean[0], 16);
    g = parseInt(clean[1] + clean[1], 16);
    b = parseInt(clean[2] + clean[2], 16);
  } else if (clean.length === 6) {
    r = parseInt(clean.slice(0, 2), 16);
    g = parseInt(clean.slice(2, 4), 16);
    b = parseInt(clean.slice(4, 6), 16);
  } else {
    return false;
  }
  return (0.299 * r + 0.587 * g + 0.114 * b) > 140;
}

export function sanitizeAndRepairMermaid(diagramText: string): string {
  let cleaned = diagramText.trim();

  // Enforce high-contrast dark text on light node fills in dark mode
  cleaned = cleaned.replace(/style\s+([A-Za-z0-9_-]+)\s+([^;\n]+)/g, (match, id, styleProps) => {
    if (styleProps.includes('color:')) return match;
    const fillMatch = styleProps.match(/fill:(#[0-9a-fA-F]{3,6})/i);
    if (fillMatch && isLightHexColor(fillMatch[1])) {
      return `style ${id} ${styleProps},color:#0f172a`;
    }
    return match;
  });

  // Strip trailing semicolons after graph header or statements: graph TD; -> graph TD
  cleaned = cleaned.replace(/^(\s*(?:graph|flowchart)\s+[A-Za-z]+)\s*;/gim, '$1');
  cleaned = cleaned.replace(/;\s*$/gm, '');

  // Fix malformed arrows like -->|label|--> or -->|label|> into -->|"label"|
  cleaned = cleaned.replace(/-->\s*\|\s*([^|\n]+?)\s*\|\s*-->/g, '-->|"$1"|');
  cleaned = cleaned.replace(/-->\s*\|\s*([^|\n]+?)\s*\|\s*>/g, '-->|"$1"|');
  cleaned = cleaned.replace(/--\s*\|\s*([^|\n]+?)\s*\|\s*-->/g, '-->|"$1"|');

  // Enclose unquoted multi-word edge labels with double quotes: -->|Some Label Text| -> -->|"Some Label Text"|
  cleaned = cleaned.replace(/-->\s*\|\s*([^"|\n]+?)\s*\|\s*/g, (match, label) => {
    const trimmed = label.trim();
    if ((trimmed.includes(' ') || trimmed.includes('(')) && !trimmed.startsWith('"')) {
      return `-->|"${trimmed}"| `;
    }
    return match;
  });

  // Fix subgraphs with quoted or multi-word titles: subgraph "Title" or subgraph Title Here -> subgraph sub_id ["Title"]
  cleaned = cleaned.replace(/subgraph\s+"([^"\n]+)"/g, (_, title) => {
    const id = 'sub_' + title.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 30);
    return `subgraph ${id} ["${title}"]`;
  });
  cleaned = cleaned.replace(/subgraph\s+([A-Za-z0-9_-]+[ \t]+[^\n[]+)(?=\n|$)/g, (match, title) => {
    const trimmed = title.trim();
    if (trimmed.startsWith('"')) return match;
    const id = 'sub_' + trimmed.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 30);
    return `subgraph ${id} ["${trimmed}"]`;
  });

  // Enclose unquoted node labels with special characters in double quotes safely
  cleaned = cleaned.replace(/([A-Za-z0-9_-]+)\[([^"\]\n]*[()/+=*&][^"\]\n]*)\]/g, (match, id, text) => {
    if (text.startsWith('"') && text.endsWith('"')) return match;
    return `${id}["${text.replace(/"/g, "'")}"]`;
  });

  return cleaned;
}
