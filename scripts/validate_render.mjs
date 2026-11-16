#!/usr/bin/env node
/**
 * Headless AST & Render Validator for Synapse Curriculum
 * 
 * Validates real-world rendering fidelity using the frontend's actual render engines:
 *   - Marked (Markdown AST parser & HTML compilation)
 *   - KaTeX (LaTeX mathematical syntax & symbol resolution)
 *   - Mermaid.js (Diagram AST parser & flowchart/sequence grammar validation)
 * 
 * Usage:
 *   node scripts/validate_render.mjs [path/to/file_or_dir] [--json]
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const WORKSPACE_ROOT = path.resolve(__dirname, '..');
const TOPICS_DIR = path.resolve(WORKSPACE_ROOT, 'topics');

// 1. Initialize DOMPurify stub for Mermaid in Node.js environment
try {
  const dompurifyModule = await import(path.resolve(WORKSPACE_ROOT, 'app/frontend/node_modules/dompurify/dist/purify.es.mjs'));
  const dompurify = dompurifyModule.default || dompurifyModule;
  dompurify.sanitize = (s) => s;
  dompurify.addHook = () => {};
  dompurify.removeHook = () => {};
} catch (e) {
  // Graceful fallback if dompurify is already bundled or unavailable
}

// 2. Load Rendering Engines from Frontend node_modules
let marked, katex, mermaid;

try {
  const markedModule = await import(path.resolve(WORKSPACE_ROOT, 'app/frontend/node_modules/marked/lib/marked.esm.js'));
  marked = markedModule.marked;
} catch (e) {
  console.error('[✘] Failed to load marked from frontend node_modules:', e.message);
  process.exit(1);
}

try {
  const katexModule = await import(path.resolve(WORKSPACE_ROOT, 'app/frontend/node_modules/katex/dist/katex.mjs'));
  katex = katexModule.default || katexModule;
  await import(path.resolve(WORKSPACE_ROOT, 'app/frontend/node_modules/katex/dist/contrib/mhchem.mjs'));
} catch (e) {
  console.error('[✘] Failed to load katex from frontend node_modules:', e.message);
  process.exit(1);
}

try {
  const mermaidCore = await import(path.resolve(WORKSPACE_ROOT, 'app/frontend/node_modules/mermaid/dist/mermaid.core.mjs'));
  mermaid = mermaidCore.default;
  mermaid.initialize({
    startOnLoad: false,
    suppressErrorRendering: true,
    securityLevel: 'loose'
  });
} catch (e) {
  console.error('[✘] Failed to load mermaid from frontend node_modules:', e.message);
  process.exit(1);
}

/**
 * Sanitizes and repairs common Mermaid syntax variations (mirrors frontend markdownRenderer.ts)
 */
function sanitizeAndRepairMermaid(diagramText) {
  let cleaned = diagramText.trim();
  cleaned = cleaned.replace(/^(\s*(?:graph|flowchart)\s+[A-Za-z]+)\s*;/gim, '$1');
  cleaned = cleaned.replace(/;\s*$/gm, '');
  cleaned = cleaned.replace(/-->\s*\|\s*([^|\n]+?)\s*\|\s*-->/g, '-->|"$1"|');
  cleaned = cleaned.replace(/-->\s*\|\s*([^|\n]+?)\s*\|\s*>/g, '-->|"$1"|');
  cleaned = cleaned.replace(/--\s*\|\s*([^|\n]+?)\s*\|\s*-->/g, '-->|"$1"|');

  cleaned = cleaned.replace(/-->\s*\|\s*([^|\n]+?)\s*\|\s*/g, (match, label) => {
    const trimmed = label.trim();
    if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
      return `-->|"${trimmed.slice(1, -1).trim()}"| `;
    }
    if (trimmed.includes(' ') || trimmed.includes('(') || trimmed.includes('/') || trimmed.includes(',')) {
      return `-->|"${trimmed.replace(/"/g, "'")}"| `;
    }
    return match;
  });

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
  cleaned = cleaned.replace(/([A-Za-z0-9_-]+)\[([^"\]\n]*[\(\)\/\+\=\*\&][^"\]\n]*)\]/g, (match, id, text) => {
    if (text.startsWith('"') && text.endsWith('"')) return match;
    return `${id}["${text.replace(/"/g, "'")}"]`;
  });

  return cleaned;
}

/**
 * Validates rendering of a single Markdown file across Marked, KaTeX, and Mermaid.js
 */
export async function validateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const relPath = path.relative(WORKSPACE_ROOT, filePath);
  const errors = [];
  let mathCount = 0;
  let mermaidCount = 0;

  // 1. Markdown AST & Compilation Check
  try {
    marked.parse(content);
  } catch (err) {
    errors.push({
      type: 'MARKDOWN_PARSE_ERROR',
      message: `Markdown compiler crashed: ${err.message}`
    });
  }

  // 2. KaTeX Math Equations Validation
  // Mask code blocks and inline code so code syntax isn't mistaken for math
  let contentNoCode = content.replace(/(```[\s\S]*?```)/g, '');
  contentNoCode = contentNoCode.replace(/(`[^`\n]+?`)/g, '');

  // Extract display math: $$...$$
  const displayMathRegex = /\$\$([\s\S]*?)\$\$/g;
  let match;
  while ((match = displayMathRegex.exec(contentNoCode)) !== null) {
    mathCount++;
    const math = match[1].trim();
    if (!math) continue;
    try {
      katex.renderToString(math, { displayMode: true, throwOnError: true, strict: 'ignore' });
    } catch (err) {
      errors.push({
        type: 'KATEX_MATH_ERROR',
        message: `KaTeX display math error in [${math.slice(0, 40).replace(/\n/g, ' ')}...]: ${err.message}`
      });
    }
  }

  // Extract inline math: $...$ (avoiding escaped \$ or currency like $120,000 or $20M)
  const inlineMathRegex = /(?<!\\)\$(?!\s|\d[\d,]*(?:\.\d+)?(?:[KMBkmb]|(?:\s*(?:million|billion|trillion|USD|EUR)))?\b)([^$\n]+?)(?<!\s)\$/gi;
  while ((match = inlineMathRegex.exec(contentNoCode)) !== null) {
    const math = match[1].trim();
    // Heuristic: ignore simple standalone currency amounts like $50 or $100
    if (/^\d+(?:,\d+)*(?:\.\d+)?$/.test(math)) continue;
    // Ignore empty or whitespace
    if (!math) continue;
    mathCount++;
    try {
      katex.renderToString(math, { displayMode: false, throwOnError: true, strict: 'ignore' });
    } catch (err) {
      errors.push({
        type: 'KATEX_MATH_ERROR',
        message: `KaTeX inline math error in [$${math.slice(0, 30)}$]: ${err.message}`
      });
    }
  }

  // 3. Mermaid Diagram Syntax Validation
  const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
  while ((match = mermaidRegex.exec(content)) !== null) {
    mermaidCount++;
    const rawDiagram = match[1].trim();
    const cleanDiagram = sanitizeAndRepairMermaid(rawDiagram);
    try {
      await mermaid.parse(cleanDiagram);
    } catch (err) {
      errors.push({
        type: 'MERMAID_SYNTAX_ERROR',
        message: `Mermaid.js parser rejected diagram: ${err.message}`
      });
    }
  }

  return {
    file: relPath,
    mathCount,
    mermaidCount,
    passed: errors.length === 0,
    errors
  };
}

/**
 * Scans directories recursively for markdown files
 */
function findMarkdownFiles(dir) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findMarkdownFiles(full));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      if (['GEMINI.md', 'SYLLABUS.md', 'README.md', 'TOPIC_OUTLINE.md', 'CURRICULUM_BLUEPRINT.md'].includes(entry.name)) {
        continue;
      }
      results.push(full);
    }
  }
  return results;
}

async function main() {
  const args = process.argv.slice(2);
  const jsonMode = args.includes('--json');
  const targetArg = args.find(a => !a.startsWith('--'));

  let targetPath = TOPICS_DIR;
  if (targetArg) {
    targetPath = path.resolve(WORKSPACE_ROOT, targetArg);
  }

  let filesToScan = [];
  if (fs.statSync(targetPath).isDirectory()) {
    filesToScan = findMarkdownFiles(targetPath);
  } else {
    filesToScan = [targetPath];
  }

  if (!jsonMode) {
    console.log('='.repeat(60));
    console.log(' 🔬 SYNAPSE HEADLESS AST & RENDER VALIDATOR');
    console.log('='.repeat(60));
    console.log(` Target Path:   ${path.relative(WORKSPACE_ROOT, targetPath) || '.'}`);
    console.log(` Files to Test: ${filesToScan.length}`);
    console.log('-'.repeat(60));
  }

  let totalMath = 0;
  let totalMermaid = 0;
  let totalErrors = 0;
  const allResults = [];

  for (const file of filesToScan) {
    const res = await validateFile(file);
    totalMath += res.mathCount;
    totalMermaid += res.mermaidCount;
    if (!res.passed) {
      totalErrors += res.errors.length;
      if (!jsonMode) {
        console.log(`\n[✘] ${res.file}:`);
        for (const e of res.errors) {
          console.log(`    • [${e.type}] ${e.message}`);
        }
      }
    }
    allResults.push(res);
  }

  if (jsonMode) {
    console.log(JSON.stringify({
      scanned_files: filesToScan.length,
      total_math_equations: totalMath,
      total_mermaid_diagrams: totalMermaid,
      total_render_errors: totalErrors,
      passed: totalErrors === 0,
      results: allResults.filter(r => !r.passed)
    }, null, 2));
    process.exit(totalErrors === 0 ? 0 : 1);
  }

  console.log('-'.repeat(60));
  console.log(' RENDER VALIDATION SUMMARY:');
  console.log(`   Files Scanned:       ${filesToScan.length}`);
  console.log(`   KaTeX Equations:     ${totalMath} verified`);
  console.log(`   Mermaid Diagrams:    ${totalMermaid} verified`);
  console.log(`   Render Errors:       ${totalErrors}`);
  console.log(`   Verdict:             ${totalErrors === 0 ? '🟢 PASSED (100% Renderable)' : '🔴 FAILED'}`);
  console.log('='.repeat(60));

  process.exit(totalErrors === 0 ? 0 : 1);
}

main().catch(err => {
  console.error('[✘] Fatal Render Validator Error:', err);
  process.exit(1);
});
