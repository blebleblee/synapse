import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

let mermaidInitialized = false;

export function renderMarkdownWithMathAndMermaid(rawMarkdown: string): string {
  if (!rawMarkdown) return '';

  // Strip redundant diagram meta-headers
  let processed = rawMarkdown
    .replace(/^###?\s*(?:Ascii diagram|Mermaid flowchart|ASCII Architecture|System Diagram)[\s:]*$/gim, '')
    .trim();

  // 1. Process display math: $$...$$
  processed = processed.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
    try {
      return `<div class="katex-display">${katex.renderToString(math.trim(), { displayMode: true, throwOnError: false })}</div>`;
    } catch {
      return `<pre><code>${math}</code></pre>`;
    }
  });

  // 2. Process inline math: $...$
  processed = processed.replace(/(?<!\\)\$([^$\n]+?)\$/g, (_, math) => {
    try {
      return katex.renderToString(math.trim(), { displayMode: false, throwOnError: false });
    } catch {
      return `$${math}$`;
    }
  });

  // 3. Custom marked renderer for mermaid and executable sandbox code blocks
  const renderer = new marked.Renderer();

  renderer.code = function ({ text, lang }) {
    const language = (lang || '').trim().toLowerCase();

    if (language === 'mermaid') {
      const cleanText = text.trim();
      return `<div class="mermaid-container" title="Click to zoom and inspect diagram">
        <div class="diagram-zoom-hint"><span>🔍</span> Click to zoom</div>
        <pre class="mermaid">${cleanText}</pre>
      </div>`;
    }

    const isExecutable = ['bash', 'sh', 'zsh', 'shell', 'python', 'c', 'rust'].includes(language);
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

export async function renderMermaidDiagramsInElement(container: HTMLElement) {
  try {
    const nodes = container.querySelectorAll('.mermaid');
    if (nodes.length > 0) {
      const mermaid = (await import('mermaid')).default;
      if (!mermaidInitialized) {
        mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
          fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          fontSize: 15,
          sequence: {
            actorMargin: 50,
            messageMargin: 40,
            boxMargin: 10,
            useMaxWidth: false,
            width: 160,
            height: 65,
          },
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
      await mermaid.run({
        nodes: nodes as NodeListOf<HTMLElement>,
      });
    }
  } catch (err) {
    console.error('Mermaid render error:', err);
  }
}
