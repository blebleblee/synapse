import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

let mermaidInitialized = false;

function sanitizeAndRepairMermaid(diagramText: string): string {
  let cleaned = diagramText.trim();

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

  // Fix subgraphs with spaces in titles: subgraph Storage Class -> subgraph "Storage Class"
  cleaned = cleaned.replace(/subgraph\s+([A-Za-z0-9_-]+\s+[^\n]+)/g, (match, title) => {
    const trimmed = title.trim();
    if (trimmed.startsWith('"') && trimmed.endsWith('"')) return match;
    return `subgraph "${trimmed}"`;
  });

  // Enclose node labels in double quotes if they contain parentheses, slashes, or arithmetic characters
  // e.g. Node[Some text (with parens)] -> Node["Some text (with parens)"]
  cleaned = cleaned.replace(/([A-Za-z0-9_-]+)\[([^"\]\n]*[\(\)\/\+\=\*\&][^"\]\n]*)\]/g, '$1["$2"]');

  // Enclose round parenthesis node labels with special chars: Node(text with spaces) -> Node["text with spaces"]
  cleaned = cleaned.replace(/([A-Za-z0-9_-]+)\(([^"\)\n]*[\s\/\+\=\*\&][^"\)\n]*)\)/g, '$1["$2"]');

  return cleaned;
}

export function renderMarkdownWithMathAndMermaid(rawMarkdown: string, enableMath = false): string {
  if (!rawMarkdown) return '';

  // Strip redundant diagram meta-headers
  let processed = rawMarkdown
    .replace(/^###?\s*(?:Ascii diagram|Mermaid flowchart|ASCII Architecture|System Diagram)[\s:]*$/gim, '')
    .trim();

  // If math is enabled (formal_sciences, natural_sciences), safely parse LaTeX outside code
  if (enableMath) {
    const codeBlocks: string[] = [];
    // Protect fenced code blocks (```...```)
    processed = processed.replace(/(```[\s\S]*?```)/g, (_, block) => {
      codeBlocks.push(block);
      return `%%SYNAPSE_CODEBLOCK_${codeBlocks.length - 1}%%`;
    });

    // Protect inline code (`...`)
    const inlineCodes: string[] = [];
    processed = processed.replace(/(`[^`\n]+?`)/g, (_, code) => {
      inlineCodes.push(code);
      return `%%SYNAPSE_INLINECODE_${inlineCodes.length - 1}%%`;
    });

    // 1. Process display math: $$...$$
    processed = processed.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
      try {
        return `<div class="katex-display">${katex.renderToString(math.trim(), { displayMode: true, throwOnError: false, trust: true })}</div>`;
      } catch (e) {
        console.error('KaTeX render error (display):', e);
        return `<div class="katex-error">Math Error: ${math}</div>`;
      }
    });

    // 2. Process inline math: $...$
    processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, math) => {
      try {
        return katex.renderToString(math.trim(), { displayMode: false, throwOnError: false, trust: true });
      } catch (e) {
        console.error('KaTeX render error (inline):', e);
        return `<span>Math Error: ${math}</span>`;
      }
    });

    // Restore inline code
    processed = processed.replace(/%%SYNAPSE_INLINECODE_(\d+)%%/g, (_, idx) => inlineCodes[Number(idx)]);
    // Restore fenced code blocks
    processed = processed.replace(/%%SYNAPSE_CODEBLOCK_(\d+)%%/g, (_, idx) => codeBlocks[Number(idx)]);
  }

  // 3. Custom marked renderer for mermaid and executable sandbox code blocks
  const renderer = new marked.Renderer();

  renderer.code = function ({ text, lang }) {
    const language = (lang || '').trim().toLowerCase();

    if (language === 'mermaid') {
      const cleanText = sanitizeAndRepairMermaid(text);
      const encodedRaw = encodeURIComponent(cleanText);
      return `<div class="mermaid-container" title="Click to zoom and inspect diagram">
        <div class="diagram-zoom-hint"><span>🔍</span> Click to zoom</div>
        <pre class="mermaid" data-raw="${encodedRaw}">${cleanText}</pre>
      </div>`;
    }

    const isExecutable = ['bash', 'sh', 'zsh', 'shell', 'python', 'c', 'rust', 'sql', 'psql'].includes(language);
    const escapedCode = text
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

    const runBtn = isExecutable
      ? `<button class="btn-run-code" data-code="${escapedCode}" title="Execute in Sandbox Terminal (Docker / k8s / Host)">
          <span class="btn-icon">▶</span> Run in Sandbox
        </button>`
      : '';

    return `<div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-lang">${language || 'code'}</span>
        ${runBtn}
      </div>
      <pre><code class="language-${language}">${text}</code></pre>
    </div>`;
  };

  const html = marked.parse(processed, { renderer }) as string;
  return html;
}

let diagramIdCounter = 0;

export async function renderMermaidDiagramsInElement(container: HTMLElement) {
  try {
    const nodes = container.querySelectorAll('pre.mermaid:not([data-rendered="true"])');
    if (nodes.length === 0) return;

    const mermaid = (await import('mermaid')).default;
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        securityLevel: 'loose',
        suppressErrorRendering: true,
        fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: 14,
        flowchart: {
          useMaxWidth: false,
          htmlLabels: true,
          curve: 'basis',
          nodeSpacing: 45,
          rankSpacing: 45,
        },
        themeVariables: {
          primaryColor: '#1e2430',
          primaryTextColor: '#f0f3f6',
          primaryBorderColor: '#cfa858',
          lineColor: '#cfa858',
          secondaryColor: '#1a1f29',
          tertiaryColor: '#161a22',
        }
      });
      mermaidInitialized = true;
    }

    for (const node of Array.from(nodes)) {
      const el = node as HTMLElement;
      if (el.getAttribute('data-rendered') === 'true') continue;

      el.setAttribute('data-rendered', 'true');
      const rawEncoded = el.getAttribute('data-raw');
      const rawCode = rawEncoded ? decodeURIComponent(rawEncoded) : el.textContent || '';
      const cleanCode = sanitizeAndRepairMermaid(rawCode);
      const diagramId = `mermaid-dia-${Date.now()}-${++diagramIdCounter}`;

      try {
        const { svg } = await mermaid.render(diagramId, cleanCode);
        el.innerHTML = svg;
      } catch (diagramErr) {
        console.warn('Mermaid diagram render failed:', diagramErr);
        const parent = el.closest('.mermaid-container');
        if (parent) {
          parent.classList.add('mermaid-fallback');
        }
        // Remove any orphan error SVG generated by mermaid
        const orphanErr = document.getElementById(diagramId) || document.getElementById(`d${diagramId}`);
        if (orphanErr) orphanErr.remove();
      }
    }
  } catch (err) {
    console.error('Mermaid render error:', err);
  }
}
