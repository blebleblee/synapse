import { marked } from 'marked';
import DOMPurify from 'dompurify';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import 'katex/dist/contrib/mhchem.mjs';
import { synthesizeTerminalCommand } from './commandSynthesizer';
import { sanitizeAndRepairMermaid } from './mermaidRepair';
import { replaceMath, transformOutsideCode } from './mathSpans';

export { sanitizeAndRepairMermaid };

let mermaidInitialized = false;

/** Escapes text for safe interpolation into HTML element content or quoted attributes. */
export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Sanitizes rendered HTML before it is injected into the DOM.
 * Lesson and chat markdown comes from LLM output and third-party topic packs,
 * so it must never be able to run script in the app's origin (which can reach
 * the terminal WebSocket). Keeps KaTeX (MathML + styled spans), data-* attributes
 * used by the code-block buttons, and the Mermaid source containers.
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true, svg: true, mathMl: true },
    FORBID_TAGS: ['style', 'form', 'input', 'textarea', 'select', 'iframe', 'object', 'embed'],
    ADD_ATTR: ['target', 'id'],
  });
}

export function renderMarkdownWithMathAndMermaid(rawMarkdown: string, enableMath = false): string {
  if (!rawMarkdown) return '';

  let processed = rawMarkdown.trim();

  // Strip accidental outer document code fencing (e.g. ```markdown\n# Title... or ```md\n)
  if (processed.startsWith('```markdown\n')) {
    processed = processed.slice(12).trim();
    if (processed.endsWith('```')) {
      processed = processed.slice(0, -3).trim();
    }
  } else if (processed.startsWith('```md\n')) {
    processed = processed.slice(6).trim();
    if (processed.endsWith('```')) {
      processed = processed.slice(0, -3).trim();
    }
  }

  // Strip redundant diagram meta-headers
  processed = processed
    .replace(/^###?\s*(?:Ascii diagram|Mermaid flowchart|ASCII Architecture|System Diagram)[\s:]*$/gim, '')
    .trim();

  // Prose only (code is left as written): render LaTeX math, and escape bare
  // less-than comparisons (<50ms, <10%) so HTML doesn't read them as tags.
  // Escaping inside code showed "IoMem&lt;0x100>" in code blocks.
  processed = transformOutsideCode(processed, (prose) => {
    if (enableMath) {
      prose = replaceMath(
        prose,
        (math) => `<div class="katex-display">${katex.renderToString(math, { displayMode: true, throwOnError: false, trust: true })}</div>`,
        (math) => katex.renderToString(math, { displayMode: false, throwOnError: false, trust: true }),
      );
    }
    return prose.replace(/<(?=\d)/g, '&lt;');
  });

  // 3. Custom marked renderer for mermaid, executable sandbox code blocks, and heading anchor IDs
  const renderer = new marked.Renderer();

  renderer.heading = function ({ depth, text }) {
    const slug = text
      .toLowerCase()
      .replace(/<[^>]*>/g, '')
      .replace(/[^a-z0-9_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
    return `<h${depth} id="${slug}">${text}</h${depth}>\n`;
  };

  renderer.code = function ({ text, lang }) {
    const language = (lang || '').trim().toLowerCase();

    const safeLang = language.replace(/[^a-z0-9_+#.-]/g, '');

    if (language === 'mermaid') {
      const cleanText = sanitizeAndRepairMermaid(text);
      const encodedRaw = encodeURIComponent(cleanText);
      return `<div class="mermaid-container" title="Click to zoom and inspect diagram">
        <div class="diagram-zoom-hint"><span>🔍</span> Click to zoom</div>
        <pre class="mermaid" data-raw="${encodedRaw}">${escapeHtml(cleanText)}</pre>
      </div>`;
    }

    const synth = synthesizeTerminalCommand(text, language);
    const escapedCode = escapeHtml(text);

    const copyBtn = `<button class="btn-copy-code" data-code="${escapedCode}" title="Copy code snippet to clipboard">
      <span class="btn-icon">📋</span> Copy
    </button>`;

    const runBtn = synth.isExecutable
      ? `<button class="btn-run-code" data-code="${escapedCode}" data-lang="${safeLang}" title="${escapeHtml(synth.explanation)}">
          <span class="btn-icon">${escapeHtml(synth.displayLabel)}</span>
        </button>`
      : '';

    return `<div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-lang">${safeLang || 'code'}</span>
        <div class="code-block-actions">
          ${copyBtn}
          ${runBtn}
        </div>
      </div>
      <pre><code class="language-${safeLang}">${escapedCode}</code></pre>
    </div>`;
  };

  const html = marked.parse(processed, { renderer }) as string;
  return sanitizeHtml(html);
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
        theme: 'base',
        securityLevel: 'strict',
        suppressErrorRendering: true,
        fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: 13,
        flowchart: {
          useMaxWidth: false,
          htmlLabels: true,
          curve: 'basis',
          nodeSpacing: 50,
          rankSpacing: 50,
        },
        themeVariables: {
          darkMode: true,
          background: '#0d1117',
          mainBkg: '#161b22',
          primaryColor: '#1c2128',
          primaryTextColor: '#f0f6fc',
          primaryBorderColor: '#cfa858',
          lineColor: '#cfa858',
          secondaryColor: '#21262d',
          tertiaryColor: '#0d1117',
          nodeBorder: '#cfa858',
          clusterBkg: '#161b22',
          clusterBorder: '#30363d',
          defaultLinkColor: '#cfa858',
          fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          fontSize: '13px',
          edgeLabelBackground: '#1c2128',
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
