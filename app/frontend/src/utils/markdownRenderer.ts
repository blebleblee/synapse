import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
});

export function renderMarkdownWithMathAndMermaid(rawMarkdown: string): string {
  if (!rawMarkdown) return '';

  // 1. Process display math: $$...$$
  let processed = rawMarkdown.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
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
      return `<div class="mermaid-container">
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
      await mermaid.run({
        nodes: nodes as NodeListOf<HTMLElement>,
      });
    }
  } catch (err) {
    console.error('Mermaid render error:', err);
  }
}
