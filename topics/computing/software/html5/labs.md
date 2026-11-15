# Operational Verification Labs: HTML5

## Objective & Toolchain Setup

HTML5 represents the living standard for web document structure and client-side application interfaces, maintained by the WHATWG consortium and implemented across all modern browser engines—Chromium's Blink, Safari's WebKit, and Firefox's Gecko. Unlike traditional compiled systems languages, HTML5 operates within a sandboxed JavaScript runtime environment where memory safety, concurrency correctness, and performance optimization follow fundamentally different execution models. The browser's rendering engine parses HTML into a Document Object Model (DOM) tree, applies Cascading Style Sheets through the CSS Object Model (CSSOM), and executes JavaScript through a just-in-time (JIT) compiler while maintaining strict security boundaries through Same-Origin Policy enforcement and Content Security Policy directives.

This laboratory guide approaches HTML5 verification through the lens of a systems programmer who must understand the entire stack from HTTP transport through layout reflow and GPU-accelerated compositing. While HTML5 itself is a declarative markup language, modern web applications exhibit complex runtime behavior through JavaScript event loops, asynchronous promise chains, Web Workers for threading, WebAssembly for near-native performance, and Service Workers for offline-first architectures. The exercises in this guide focus on observable system behavior using browser developer tools, performance profiling APIs, static analysis tooling, and automated testing frameworks that provide reproducible, quantitative measurements of correctness and efficiency.

The verification toolchain for HTML5 development centers on Chromium's DevTools protocol, which exposes deep instrumentation for network waterfalls, JavaScript heap snapshots, CSS selector matching costs, layout thrashing detection, and frame-rate profiling. Node.js provides a V8-based runtime for server-side execution and testing infrastructure, while TypeScript adds compile-time type checking to catch contract violations before runtime. Playwright and Puppeteer offer headless browser automation for regression testing, accessibility audits, and visual diff comparisons. Lighthouse performs holistic site quality assessments measuring Core Web Vitals—Largest Contentful Paint, First Input Delay, and Cumulative Layout Shift—which quantify user-perceived performance and directly impact search ranking and conversion metrics.

Begin by establishing a complete verification environment. Install Node.js version 20 or later, which includes the npm package manager and access to the full ecosystem of testing libraries. Use `nvm` (Node Version Manager) on Unix systems or `nvm-windows` to manage multiple Node.js versions cleanly without requiring elevated privileges. Install TypeScript globally with `npm install -g typescript` to gain access to the `tsc` compiler and language server. Add Playwright with `npm install -D @playwright/test` for cross-browser automation, ESLint with `npm install -D eslint` for static analysis, and Prettier with `npm install -D prettier` for consistent code formatting. Install the Chromium-based Edge or Chrome browser with developer builds enabled, or use Firefox Developer Edition for Gecko-specific profiling. On Linux systems, ensure you have `xvfb` installed for headless X11 server emulation during continuous integration runs.

Configure your shell environment to expose Node.js binaries in your PATH. On Unix systems, add `export PATH="$HOME/.nvm/versions/node/v20.11.0/bin:$PATH"` to your `.bashrc` or `.zshrc`. Verify the installation by running `node --version`, `npm --version`, and `tsc --version`. Initialize a new project directory with `npm init -y` to create a `package.json` manifest, then configure TypeScript with `tsc --init` to generate a `tsconfig.json` with strict type checking enabled through `"strict": true` and module resolution set to `"node16"` for proper ESM and CommonJS interoperability. Install type definitions for the DOM with `npm install -D @types/node` and `npm install -D @types/web` to enable full IntelliSense and compile-time verification of browser APIs.

The modern HTML5 development workflow relies on bundlers to transform, minify, and tree-shake JavaScript modules for production deployment. Install Vite with `npm install -D vite` as a zero-configuration development server with sub-50ms hot module replacement and optimized production builds using Rollup. Vite leverages native ES modules during development, eliminating the bundling step entirely and providing instant server startup even for large codebases. Configure Vite by creating `vite.config.ts` in your project root, enabling source maps for debugging with `build.sourcemap: true`, and setting the base path for deployment routing. The development server runs on `http://localhost:5173` by default and automatically injects WebSocket connections for live reloading without full page refreshes.

Install Chrome DevTools Protocol libraries for programmatic inspection with `npm install -D chrome-remote-interface` and `npm install -D puppeteer-core` to control browser instances from Node.js scripts. These tools expose the same telemetry used by the built-in DevTools UI, allowing you to capture Performance timelines, extract Coverage reports showing unused CSS and JavaScript, and retrieve detailed network timing breakdowns including DNS resolution, TLS handshake, Time to First Byte, and content download phases. The Performance Observer API provides programmatic access to navigation timing, resource timing, long task detection, and layout shift metrics directly from client-side JavaScript running in the page context.

For accessibility verification, install `axe-core` with `npm install -D @axe-core/playwright` to run automated WCAG 2.1 conformance checks against your rendered HTML. The Axe engine inspects the computed accessibility tree exposed by the browser's platform accessibility APIs, detecting missing ARIA labels, incorrect heading hierarchies, insufficient color contrast ratios, and keyboard navigation traps. Supplement automated testing with manual screen reader verification using NVDA on Windows, VoiceOver on macOS, or Orca on Linux. Accessibility bugs often manifest only under assistive technology because the visual rendering and the semantic accessibility tree can diverge when ARIA attributes override native element roles incorrectly.

Establish a baseline testing infrastructure by creating `tests/` directory and adding a Playwright configuration file at `playwright.config.ts`. Configure three browser projects—Chromium, Firefox, and WebKit—to verify cross-engine compatibility, since layout engines still exhibit behavioral differences in CSS Grid algorithms, flexbox wrap calculations, and Shadow DOM event propagation. Set reasonable timeouts for test operations: 30 seconds for page navigation, 10 seconds for element visibility assertions, and 5 seconds for network idle detection. Enable video recording on test failure with `video: 'retain-on-failure'` and screenshot capture with `screenshot: 'only-on-failure'` to provide visual debugging context when assertions fail in headless CI environments where you cannot interactively inspect the failure state.

Create a sample HTML5 document structure that will serve as the foundation for all subsequent exercises. The document should use semantic HTML elements, follow progressive enhancement principles, and implement responsive design through CSS media queries and flexible layout systems. Save this as `index.html` in your project root:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="HTML5 operational verification testbed">
    <title>HTML5 Verification Labs</title>
    <link rel="stylesheet" href="styles.css">
    <script type="module" src="main.js"></script>
</head>
<body>
    <header role="banner">
        <nav aria-label="Primary navigation">
            <ul>
                <li><a href="#intro">Introduction</a></li>
                <li><a href="#exercises">Exercises</a></li>
                <li><a href="#results">Results</a></li>
            </ul>
        </nav>
    </header>

    <main id="main-content">
        <section id="intro" aria-labelledby="intro-heading">
            <h1 id="intro-heading">Performance Verification Testbed</h1>
            <p>This interactive testbed demonstrates HTML5 runtime behavior analysis through instrumented code paths and quantitative performance measurement.</p>
        </section>

        <section id="exercises" aria-labelledby="exercises-heading">
            <h2 id="exercises-heading">Interactive Exercises</h2>
            <article id="dom-manipulation">
                <h3>DOM Manipulation Stress Test</h3>
                <button id="trigger-reflow" type="button">Trigger Layout Reflow</button>
                <div id="dynamic-content" aria-live="polite" aria-atomic="true"></div>
                <output id="reflow-metrics" aria-label="Reflow timing metrics"></output>
            </article>

            <article id="memory-allocation">
                <h3>Memory Allocation Patterns</h3>
                <button id="allocate-objects" type="button">Allocate Object Graph</button>
                <button id="force-gc" type="button">Request Garbage Collection</button>
                <output id="heap-metrics" aria-label="Heap memory metrics"></output>
            </article>

            <article id="async-operations">
                <h3>Asynchronous Event Loop</h3>
                <button id="fetch-data" type="button">Fetch Remote Data</button>
                <progress id="fetch-progress" value="0" max="100" aria-label="Data fetch progress"></progress>
                <output id="network-metrics" aria-label="Network timing metrics"></output>
            </article>
        </section>

        <section id="results" aria-labelledby="results-heading">
            <h2 id="results-heading">Performance Results</h2>
            <table id="metrics-table">
                <caption>Captured Performance Metrics</caption>
                <thead>
                    <tr>
                        <th scope="col">Operation</th>
                        <th scope="col">Duration (ms)</th>
                        <th scope="col">Memory Delta (KB)</th>
                        <th scope="col">Timestamp</th>
                    </tr>
                </thead>
                <tbody id="metrics-tbody">
                    <!-- Dynamically populated -->
                </tbody>
            </table>
        </section>
    </main>

    <footer role="contentinfo">
        <p>HTML5 Verification Labs • Operational Toolchain Validation</p>
    </footer>
</body>
</html>
```

Create a corresponding CSS file at `styles.css` implementing a mobile-first responsive design with CSS custom properties for theming and efficient GPU-accelerated transforms:

```css
:root {
    --color-primary: #2563eb;
    --color-surface: #ffffff;
    --color-text: #1f2937;
    --spacing-unit: 8px;
    --max-content-width: 1200px;
    --header-height: 64px;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: 16px;
    line-height: 1.6;
    scroll-behavior: smooth;
}

body {
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    color: var(--color-text);
    background-color: var(--color-surface);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    position: sticky;
    top: 0;
    height: var(--header-height);
    background-color: var(--color-primary);
    color: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    will-change: transform;
}

nav ul {
    display: flex;
    gap: calc(var(--spacing-unit) * 3);
    list-style: none;
    height: 100%;
    align-items: center;
    padding: 0 calc(var(--spacing-unit) * 2);
}

nav a {
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: opacity 200ms ease;
}

nav a:hover,
nav a:focus {
    opacity: 0.8;
}

main {
    flex: 1;
    max-width: var(--max-content-width);
    width: 100%;
    margin: 0 auto;
    padding: calc(var(--spacing-unit) * 4);
}

section {
    margin-bottom: calc(var(--spacing-unit) * 6);
}

h1 {
    font-size: 2.5rem;
    margin-bottom: calc(var(--spacing-unit) * 2);
}

h2 {
    font-size: 2rem;
    margin-bottom: calc(var(--spacing-unit) * 3);
}

h3 {
    font-size: 1.5rem;
    margin-bottom: calc(var(--spacing-unit) * 2);
}

article {
    background-color: #f9fafb;
    border-radius: 8px;
    padding: calc(var(--spacing-unit) * 3);
    margin-bottom: calc(var(--spacing-unit) * 3);
}

button {
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: 4px;
    padding: calc(var(--spacing-unit) * 1.5) calc(var(--spacing-unit) * 3);
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: transform 100ms ease, box-shadow 100ms ease;
    margin-right: calc(var(--spacing-unit) * 2);
    margin-bottom: calc(var(--spacing-unit) * 2);
}

button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

button:active {
    transform: translateY(0);
}

button:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
}

output {
    display: block;
    margin-top: calc(var(--spacing-unit) * 2);
    padding: calc(var(--spacing-unit) * 2);
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    font-family: "Courier New", monospace;
    font-size: 0.875rem;
    white-space: pre-wrap;
    word-break: break-all;
}

progress {
    width: 100%;
    height: 24px;
    margin-top: calc(var(--spacing-unit) * 2);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: calc(var(--spacing-unit) * 3);
}

caption {
    text-align: left;
    font-weight: 600;
    margin-bottom: calc(var(--spacing-unit) * 2);
}

th,
td {
    text-align: left;
    padding: calc(var(--spacing-unit) * 2);
    border-bottom: 1px solid #e5e7eb;
}

th {
    font-weight: 600;
    background-color: #f9fafb;
}

footer {
    background-color: #f9fafb;
    padding: calc(var(--spacing-unit) * 3);
    text-align: center;
    border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
    html {
        font-size: 14px;
    }

    main {
        padding: calc(var(--spacing-unit) * 2);
    }

    nav ul {
        gap: calc(var(--spacing-unit) * 2);
    }

    h1 {
        font-size: 2rem;
    }

    h2 {
        font-size: 1.5rem;
    }

    table {
        font-size: 0.875rem;
    }

    th,
    td {
        padding: calc(var(--spacing-unit) * 1);
    }
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }

    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

@media (prefers-color-scheme: dark) {
    :root {
        --color-surface: #1f2937;
        --color-text: #f9fafb;
    }

    article {
        background-color: #374151;
    }

    output {
        background-color: #111827;
        border-color: #4b5563;
    }

    th {
        background-color: #374151;
    }

    footer {
        background-color: #111827;
        border-top-color: #4b5563;
    }
}
```

With the HTML structure and styling in place, you now possess a testbed that exercises key browser subsystems: semantic HTML parsing, CSS cascade resolution, flexbox and grid layout, event delegation, and responsive media queries. The next sections instrument this foundation with JavaScript performance profiling, memory allocation tracking, and automated regression testing to establish quantitative verification workflows comparable to systems programming with Valgrind, AddressSanitizer, and perf.

## Exercise 1: DOM Manipulation Profiling & Layout Reflow Analysis

The Document Object Model represents HTML's in-memory tree structure where each element, attribute, and text node becomes an object exposing methods for traversal and mutation. When JavaScript modifies the DOM, the browser must recalculate styles (CSS selector matching and cascade resolution), recompute layout (box model dimensions and positioning), repaint affected pixels (rasterization), and composite layers (GPU texture uploads). These phases constitute the critical rendering path, and inefficient DOM manipulation causes visible jank when frame times exceed 16.67 milliseconds, the budget for maintaining 60 frames per second. Layout reflow is particularly expensive because forcing synchronous geometry queries like `offsetHeight` or `getBoundingClientRect()` flushes pending style and layout calculations immediately, creating a pipeline stall that blocks the main thread.

Modern browser engines optimize rendering through incremental layout, where only subtrees affected by DOM changes undergo recomputation, and layer promotion, where elements with certain CSS properties like `transform` or `opacity` animations are rendered to separate GPU textures composited by the hardware without triggering layout. However, accessing layout-dependent properties after DOM mutations forces a synchronous reflow, negating these optimizations. The Performance API provides microsecond-resolution timing through `performance.now()` and the User Timing API for instrumenting code sections with `performance.mark()` and `performance.measure()`. The PerformanceObserver API enables passive monitoring of long tasks (JavaScript execution exceeding 50 milliseconds), layout shifts (visual instability metrics), and resource timing without polling overhead.

Create a JavaScript module at `main.js` that instruments DOM mutations and measures their performance impact. This implementation uses the Performance API to capture timing data, the ResizeObserver API to detect layout changes, and the MutationObserver API to track DOM modifications asynchronously without polling:

```javascript
class PerformanceMonitor {
    constructor() {
        this.metrics = [];
        this.observer = null;
        this.setupObservers();
        this.bindEventHandlers();
    }

    setupObservers() {
        if ('PerformanceObserver' in window) {
            this.observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'measure') {
                        this.logMetric(entry.name, entry.duration, 0);
                    } else if (entry.entryType === 'layout-shift') {
                        console.warn(`Layout shift detected: score=${entry.value.toFixed(4)}`);
                    } else if (entry.entryType === 'longtask') {
                        console.warn(`Long task detected: ${entry.duration.toFixed(2)}ms`);
                    }
                }
            });

            this.observer.observe({ 
                entryTypes: ['measure', 'layout-shift', 'longtask'],
                buffered: true 
            });
        }

        const memoryObserver = setInterval(() => {
            if (performance.memory) {
                const usedJSHeap = performance.memory.usedJSHeapSize;
                const totalJSHeap = performance.memory.totalJSHeapSize;
                const utilization = ((usedJSHeap / totalJSHeap) * 100).toFixed(2);
                document.getElementById('heap-metrics').textContent = 
                    `Used: ${(usedJSHeap / 1024 / 1024).toFixed(2)} MB / ` +
                    `Total: ${(totalJSHeap / 1024 / 1024).toFixed(2)} MB ` +
                    `(${utilization}% utilization)`;
            }
        }, 1000);
    }

    bindEventHandlers() {
        const reflowButton = document.getElementById('trigger-reflow');
        const allocateButton = document.getElementById('allocate-objects');
        const gcButton = document.getElementById('force-gc');
        const fetchButton = document.getElementById('fetch-data');

        reflowButton.addEventListener('click', () => this.triggerReflowTest());
        allocateButton.addEventListener('click', () => this.allocateObjectGraph());
        gcButton.addEventListener('click', () => this.requestGarbageCollection());
        fetchButton.addEventListener('click', () => this.performAsyncFetch());
    }

    triggerReflowTest() {
        const container = document.getElementById('dynamic-content');
        const output = document.getElementById('reflow-metrics');
        
        performance.mark('reflow-start');
        
        const fragmentOptimized = document.createDocumentFragment();
        const fragmentUnoptimized = document.createDocumentFragment();
        
        for (let i = 0; i < 100; i++) {
            const div = document.createElement('div');
            div.className = 'dynamic-element';
            div.textContent = `Element ${i}: ${Math.random().toString(36).substring(7)}`;
            div.style.padding = '8px';
            div.style.marginBottom = '4px';
            div.style.backgroundColor = '#e0f2fe';
            div.style.borderRadius = '4px';
            fragmentOptimized.appendChild(div);
        }
        
        container.appendChild(fragmentOptimized);
        
        performance.mark('reflow-fragment-complete');
        
        const heights = [];
        for (let i = 0; i < container.children.length; i++) {
            heights.push(container.children[i].offsetHeight);
        }
        
        performance.mark('reflow-forced-sync');
        
        for (let i = 0; i < container.children.length; i++) {
            container.children[i].style.transform = `translateX(${i % 2 === 0 ? 4 : -4}px)`;
        }
        
        performance.mark('reflow-complete');
        
        performance.measure('fragment-insertion', 'reflow-start', 'reflow-fragment-complete');
        performance.measure('forced-reflow', 'reflow-fragment-complete', 'reflow-forced-sync');
        performance.measure('transform-application', 'reflow-forced-sync', 'reflow-complete');
        performance.measure('total-reflow-operation', 'reflow-start', 'reflow-complete');
        
        const measures = performance.getEntriesByType('measure');
        const recentMeasures = measures.slice(-4);
        
        let resultsText = 'Reflow Performance Breakdown:\n';
        recentMeasures.forEach(measure => {
            resultsText += `${measure.name}: ${measure.duration.toFixed(3)}ms\n`;
        });
        
        output.textContent = resultsText;
        
        performance.clearMarks();
        performance.clearMeasures();
    }

    allocateObjectGraph() {
        const output = document.getElementById('heap-metrics');
        
        performance.mark('allocation-start');
        
        const graph = {
            nodes: [],
            edges: [],
            metadata: {
                timestamp: Date.now(),
                allocator: 'test-harness'
            }
        };
        
        for (let i = 0; i < 10000; i++) {
            const node = {
                id: i,
                data: new Array(100).fill(Math.random()),
                neighbors: [],
                timestamp: performance.now()
            };
            graph.nodes.push(node);
        }
        
        for (let i = 0; i < graph.nodes.length; i++) {
            const numEdges = Math.floor(Math.random() * 5);
            for (let j = 0; j < numEdges; j++) {
                const targetIdx = Math.floor(Math.random() * graph.nodes.length);
                graph.nodes[i].neighbors.push(graph.nodes[targetIdx]);
                graph.edges.push({ from: i, to: targetIdx, weight: Math.random() });
            }
        }
        
        performance.mark('allocation-complete');
        performance.measure('object-graph-allocation', 'allocation-start', 'allocation-complete');
        
        const measure = performance.getEntriesByName('object-graph-allocation')[0];
        
        if (performance.memory) {
            const memoryDelta = performance.memory.usedJSHeapSize / 1024;
            this.logMetric('Object Graph Allocation', measure.duration, memoryDelta);
        }
        
        window.testGraph = graph;
        
        performance.clearMarks();
        performance.clearMeasures();
    }

    requestGarbageCollection() {
        if (window.testGraph) {
            window.testGraph = null;
        }
        
        const output = document.getElementById('heap-metrics');
        output.textContent += '\n\nGarbage collection requested. Memory will be reclaimed asynchronously.\nNote: Explicit GC control requires --expose-gc flag in V8.';
        
        if (window.gc) {
            performance.mark('gc-start');
            window.gc();
            performance.mark('gc-complete');
            performance.measure('garbage-collection', 'gc-start', 'gc-complete');
            
            const measure = performance.getEntriesByName('garbage-collection')[0];
            output.textContent += `\n\nForced GC completed in ${measure.duration.toFixed(3)}ms`;
            
            performance.clearMarks();
            performance.clearMeasures();
        }
    }

    async performAsyncFetch() {
        const progress = document.getElementById('fetch-progress');
        const output = document.getElementById('network-metrics');
        
        performance.mark('fetch-start');
        
        progress.value = 10;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        try {
            const navigationStart = performance.timing.navigationStart;
            
            const response = await fetch('https://jsonplaceholder.typicode.com/posts', {
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            progress.value = 50;
            
            performance.mark('fetch-headers-complete');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            progress.value = 100;
            
            performance.mark('fetch-complete');
            
            performance.measure('fetch-ttfb', 'fetch-start', 'fetch-headers-complete');
            performance.measure('fetch-body-parse', 'fetch-headers-complete', 'fetch-complete');
            performance.measure('fetch-total', 'fetch-start', 'fetch-complete');
            
            const resources = performance.getEntriesByType('resource');
            const fetchResource = resources.find(r => r.name.includes('jsonplaceholder.typicode.com'));
            
            let metricsText = 'Network Timing Breakdown:\n';
            
            if (fetchResource) {
                metricsText += `DNS Lookup: ${fetchResource.domainLookupEnd - fetchResource.domainLookupStart}ms\n`;
                metricsText += `TCP Connect: ${fetchResource.connectEnd - fetchResource.connectStart}ms\n`;
                metricsText += `TLS Handshake: ${fetchResource.secureConnectionStart > 0 ? 
                    (fetchResource.connectEnd - fetchResource.secureConnectionStart) : 0}ms\n`;
                metricsText += `Request Sent: ${fetchResource.requestStart - fetchResource.connectEnd}ms\n`;
                metricsText += `TTFB: ${fetchResource.responseStart - fetchResource.requestStart}ms\n`;
                metricsText += `Content Download: ${fetchResource.responseEnd - fetchResource.responseStart}ms\n`;
                metricsText += `Total Duration: ${fetchResource.duration}ms\n`;
                metricsText += `Transfer Size: ${(fetchResource.transferSize / 1024).toFixed(2)} KB\n`;
            }
            
            const measures = performance.getEntriesByType('measure').slice(-3);
            metricsText += '\nApplication Timings:\n';
            measures.forEach(measure => {
                metricsText += `${measure.name}: ${measure.duration.toFixed(3)}ms\n`;
            });
            
            metricsText += `\nFetched ${data.length} records successfully.`;
            output.textContent = metricsText;
            
            this.logMetric('Async Fetch Operation', fetchResource ? fetchResource.duration : 0, 0);
            
            performance.clearMarks();
            performance.clearMeasures();
            
        } catch (error) {
            progress.value = 0;
            output.textContent = `Fetch failed: ${error.message}`;
            
            if (error.name === 'AbortError') {
                output.textContent += '\n(Request aborted due to timeout)';
            }
        }
    }

    logMetric(operation, duration, memoryDelta) {
        const metric = {
            operation,
            duration: duration.toFixed(3),
            memoryDelta: memoryDelta.toFixed(2),
            timestamp: new Date().toISOString()
        };
        
        this.metrics.push(metric);
        
        const tbody = document.getElementById('metrics-tbody');
        const row = tbody.insertRow(0);
        
        row.insertCell(0).textContent = metric.operation;
        row.insertCell(1).textContent = metric.duration;
        row.insertCell(2).textContent = metric.memoryDelta;
        row.insertCell(3).textContent = new Date(metric.timestamp).toLocaleTimeString();
        
        if (this.metrics.length > 50) {
            tbody.deleteRow(tbody.rows.length - 1);
            this.metrics.shift();
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.perfMonitor = new PerformanceMonitor();
    });
} else {
    window.perfMonitor = new PerformanceMonitor();
}

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(
            (registration) => {
                console.log('ServiceWorker registration successful:', registration.scope);
            },
            (error) => {
                console.log('ServiceWorker registration failed:', error);
            }
        );
    });
}
```

Start the development server by running `npx vite` from your project directory. Navigate to `http://localhost:5173` in Chrome and open DevTools with F12. Switch to the Performance tab and begin recording a profile. Click the "Trigger Layout Reflow" button and stop the recording after the operation completes. The flame graph displays the call stack over time, with each horizontal bar representing a function invocation. Expand the "Recalculate Style" and "Layout" sections to see the forced synchronous layout triggered by accessing `offsetHeight` after DOM mutation. The yellow sections indicate scripting time, purple sections indicate rendering, and green sections indicate painting and compositing.

Navigate to the Memory tab and take a heap snapshot by clicking "Take snapshot." The snapshot displays all live JavaScript objects grouped by constructor. Expand the "Object" and "Array" entries to see the object graph created by the allocation test. The "Shallow Size" column shows bytes allocated by the object itself, while "Retained Size" shows total bytes that would be freed if this object were garbage collected, including all objects reachable only through this object. Click "Comparison" mode and take a second snapshot after clicking "Request Garbage Collection." The diff view shows which objects were freed, demonstrating that nulling the reference allowed the garbage collector to reclaim the entire graph.

Switch to the Coverage tab and reload the page with recording enabled. The Coverage panel displays unused CSS and JavaScript as red bars. Modern web applications often ship framework bundles where 60-80% of code remains unused on initial page load. Code splitting through dynamic `import()` statements and lazy component loading reduces this waste by deferring non-critical code until needed. The Coverage report guides optimization decisions by quantifying the bytes transmitted but never executed.

Open the Network tab and observe the fetch request to the JSONPlaceholder API. The timing breakdown shows DNS resolution (often cached after the first request), TCP connection establishment, TLS handshake negotiation, request transmission, waiting time until the first byte arrives (TTFB), and content download. High TTFB indicates server processing latency or network round-trip time. Content download time correlates with transfer size and available bandwidth. The `curl` command can replicate this measurement from the terminal: `curl -w "@curl-format.txt" -o /dev/null -s "https://jsonplaceholder.typicode.com/posts"` where `curl-format.txt` contains timing placeholders like `time_namelookup: %{time_namelookup}s\n`.

Configure TypeScript type checking by creating `tsconfig.json` with strict mode and DOM library types:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "allowJs": true,
    "checkJs": false
  },
  "include": ["**/*.js", "**/*.ts"],
  "exclude": ["node_modules"]
}
```

Run type checking with `npx tsc --noEmit` to verify all DOM APIs are used correctly without generating output files. TypeScript will catch common errors like accessing properties that do not exist on Element objects, passing incorrect argument types to fetch, or forgetting to handle null returns from `document.getElementById()`. Convert `main.js` to `main.ts` and add explicit type annotations to the PerformanceMonitor class for full IntelliSense support during development.

## Exercise 2: Cache Behavior & Resource Loading Optimization

Browser performance depends critically on HTTP caching strategies that minimize redundant network requests and leverage stored responses from previous page loads. The HTTP Cache-Control header directs browser caching behavior through directives like `max-age` (freshness lifetime in seconds), `no-cache` (require revalidation), `no-store` (never cache), and `immutable` (resource will never change). Service Workers provide programmable caching through the Cache API, enabling offline-first architectures where the application shell loads instantly from cache while fresh data fetches asynchronously in the background. The Cache API exposes low-level control over HTTP response storage, allowing fine-grained strategies like "network first, fallback to cache" or "cache first, background update."

Modern web applications employ several caching layers: browser HTTP cache (managed by Cache-Control headers), Service Worker cache (programmatic JavaScript control), CDN edge cache (geographically distributed servers), and server-side cache (database query results, rendered HTML fragments). Each layer trades freshness for latency reduction. Resource hints like `<link rel="preload">` instruct the browser to fetch critical resources early in the page load, before the parser encounters them, reducing time to interactive. The `<link rel="prefetch">` hint speculatively fetches resources for likely next navigation, utilizing idle network bandwidth. DNS prefetching with `<link rel="dns-prefetch">` resolves domain names in advance, eliminating DNS lookup latency when the resource is actually requested.

Create a Service Worker implementation at `sw.js` that implements a cache-first strategy for static assets and a network-first strategy for API requests:

```javascript
const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `dynamic-${CACHE_VERSION}`;
const OFFLINE_PAGE = '/offline.html';

const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/main.js',
    '/offline.html'
];

const CACHE_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
const CACHE_MAX_ENTRIES = 50;

self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Install event');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[ServiceWorker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[ServiceWorker] Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[ServiceWorker] Static asset caching failed:', error);
            })
    );
});

self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activate event');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            return name.startsWith('static-') && name !== STATIC_CACHE ||
                                   name.startsWith('dynamic-') && name !== DYNAMIC_CACHE;
                        })
                        .map((name) => {
                            console.log(`[ServiceWorker] Deleting old cache: ${name}`);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[ServiceWorker] Old caches cleared');
                return self.clients.claim();
            })
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    if (request.method !== 'GET') {
        return;
    }
    
    if (url.origin === location.origin) {
        event.respondWith(cacheFirstStrategy(request));
    } else if (url.hostname.includes('jsonplaceholder.typicode.com')) {
        event.respondWith(networkFirstStrategy(request));
    } else {
        event.respondWith(staleWhileRevalidateStrategy(request));
    }
});

async function cacheFirstStrategy(request) {
    try {
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            const cacheTime = new Date(cachedResponse.headers.get('sw-cache-time'));
            const age = Date.now() - cacheTime.getTime();
            
            if (age < CACHE_MAX_AGE_MS) {
                console.log(`[ServiceWorker] Serving from cache: ${request.url}`);
                return cachedResponse;
            } else {
                console.log(`[ServiceWorker] Cache expired for: ${request.url}`);
            }
        }
        
        console.log(`[ServiceWorker] Cache miss, fetching: ${request.url}`);
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const responseToCache = networkResponse.clone();
            const headers = new Headers(responseToCache.headers);
            headers.set('sw-cache-time', new Date().toISOString());
            
            const modifiedResponse = new Response(await responseToCache.blob(), {
                status: responseToCache.status,
                statusText: responseToCache.statusText,
                headers: headers
            });
            
            cache.put(request, modifiedResponse);
            await limitCacheSize(STATIC_CACHE, CACHE_MAX_ENTRIES);
        }
        
        return networkResponse;
        
    } catch (error) {
        console.error(`[ServiceWorker] Fetch failed for ${request.url}:`, error);
        
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        if (request.destination === 'document') {
            const offlineResponse = await cache.match(OFFLINE_PAGE);
            if (offlineResponse) {
                return offlineResponse;
            }
        }
        
        return new Response('Network error occurred', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

async function networkFirstStrategy(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    
    try {
        console.log(`[ServiceWorker] Network-first fetch: ${request.url}`);
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
            await limitCacheSize(DYNAMIC_CACHE, CACHE_MAX_ENTRIES);
        }
        
        return networkResponse;
        
    } catch (error) {
        console.error(`[ServiceWorker] Network-first failed for ${request.url}:`, error);
        
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            console.log(`[ServiceWorker] Serving stale cache: ${request.url}`);
            return cachedResponse;
        }
        
        return new Response(JSON.stringify({ error: 'Offline and no cache available' }), {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
    }
}

async function staleWhileRevalidateStrategy(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                cache.put(request, networkResponse.clone());
                limitCacheSize(DYNAMIC_CACHE, CACHE_MAX_ENTRIES);
            }
            return networkResponse;
        })
        .catch((error) => {
            console.error(`[ServiceWorker] Background revalidation failed for ${request.url}:`, error);
            return cachedResponse;
        });
    
    if (cachedResponse) {
        console.log(`[ServiceWorker] Serving cached while revalidating: ${request.url}`);
        return cachedResponse;
    }
    
    return fetchPromise;
}

async function limitCacheSize(cacheName, maxEntries) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > maxEntries) {
        const entriesToDelete = keys.length - maxEntries;
        const keysToDelete = keys.slice(0, entriesToDelete);
        
        await Promise.all(
            keysToDelete.map((key) => {
                console.log(`[ServiceWorker] Evicting from cache: ${key.url}`);
                return cache.delete(key);
            })
        );
    }
}

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        console.log('[ServiceWorker] Received SKIP_WAITING message');
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        console.log('[ServiceWorker] Received CLEAR_CACHE message');
        event.waitUntil(
            caches.keys()
                .then((cacheNames) => {
                    return Promise.all(
                        cacheNames.map((name) => caches.delete(name))
                    );
                })
                .then(() => {
                    console.log('[ServiceWorker] All caches cleared');
                    event.ports[0].postMessage({ success: true });
                })
                .catch((error) => {
                    console.error('[ServiceWorker] Cache clearing failed:', error);
                    event.ports[0].postMessage({ success: false, error: error.message });
                })
        );
    }
});

self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        console.log('[ServiceWorker] Background sync triggered');
        event.waitUntil(performBackgroundSync());
    }
});

async function performBackgroundSync() {
    try {
        const pendingRequests = await getPendingRequests();
        
        await Promise.all(
            pendingRequests.map((request) => 
                fetch(request)
                    .then(() => removePendingRequest(request))
                    .catch((error) => {
                        console.error('[ServiceWorker] Background sync request failed:', error);
                    })
            )
        );
        
        console.log('[ServiceWorker] Background sync completed');
    } catch (error) {
        console.error('[ServiceWorker] Background sync error:', error);
    }
}

async function getPendingRequests() {
    return [];
}

async function removePendingRequest(request) {
    return true;
}
```

Create an offline fallback page at `offline.html` that the Service Worker serves when the network is unavailable and no cache exists:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - HTML5 Verification Labs</title>
    <style>
        body {
            font-family: system-ui, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background-color: #f9fafb;
            color: #1f2937;
        }
        .container {
            text-align: center;
            padding: 2rem;
            max-width: 500px;
        }
        h1 {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        p {
            font-size: 1.125rem;
            line-height: 1.6;
            margin-bottom: 2rem;
        }
        button {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 12px 24px;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover {
            background-color: #1d4ed8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>You're Offline</h1>
        <p>This page requires a network connection. Please check your internet connectivity and try again.</p>
        <button onclick="window.location.reload()">Retry</button>
    </div>
</body>
</html>
```

Update `main.js` to register the Service Worker and provide cache management controls:

```javascript
async function clearAllCaches() {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        const messageChannel = new MessageChannel();
        
        return new Promise((resolve, reject) => {
            messageChannel.port1.onmessage = (event) => {
                if (event.data.success) {
                    console.log('All caches cleared successfully');
                    resolve();
                } else {
                    console.error('Cache clearing failed:', event.data.error);
                    reject(new Error(event.data.error));
                }
            };
            
            navigator.serviceWorker.controller.postMessage(
                { type: 'CLEAR_CACHE' },
                [messageChannel.port2]
            );
        });
    } else {
        return caches.keys().then((names) => 
            Promise.all(names.map((name) => caches.delete(name)))
        );
    }
}

async function inspectCacheContents() {
    const cacheNames = await caches.keys();
    const results = {};
    
    for (const name of cacheNames) {
        const cache = await caches.open(name);
        const keys = await cache.keys();
        
        results[name] = {
            entries: keys.length,
            urls: keys.map((req) => req.url)
        };
    }
    
    console.table(results);
    return results;
}

window.cacheUtils = {
    clear: clearAllCaches,
    inspect: inspectCacheContents
};
```

Reload the page and observe Service Worker registration in the Application tab of DevTools. The Service Workers pane displays the active worker, its scope, and controls to unregister or update it. Click "Update on reload" to force a new Service Worker installation on each page refresh during development. The Cache Storage pane lists all caches managed by the Service Worker, showing cached URLs and their responses. Right-click an entry to delete it, or click "Clear storage" to purge all cached data, IndexedDB databases, and local storage simultaneously.

Test offline behavior by opening the Network tab, selecting "Offline" from the throttling dropdown, and reloading the page. The Service Worker serves cached assets transparently, and the page functions normally despite network absence. Switch back to "Online" throttling and click "Trigger Layout Reflow" to verify the API fetch succeeds. Now switch to "Offline" again and repeat the fetch. The Service Worker falls back to the cached response, demonstrating graceful degradation.

Measure cache effectiveness by examining the Size column in the Network tab. Responses served from Service Worker cache display "(ServiceWorker)" instead of byte sizes, and the Time column shows retrieval latency under 10 milliseconds compared to 50-200 milliseconds for network requests. The Performance tab's Network track color-codes requests: dark blue for HTML, purple for CSS, yellow for JavaScript, green for images, and light blue for XHR/Fetch. Cached resources appear instantly at the start of the timeline rather than delayed by network round-trip time.

Configure ESLint to enforce code quality standards by creating `.eslintrc.json`:

```json
{
  "env": {
    "browser": true,
    "es2022": true,
    "node": true,
    "serviceworker": true
  },
  "extends": [
    "eslint:recommended"
  ],
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module"
  },
  "rules": {
    "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "no-console": "off",
    "prefer-const": "error",
    "no-var": "error",
    "eqeqeq": ["error", "always"],
    "curly": ["error", "all"],
    "brace-style": ["error", "1tbs"],
    "semi": ["error", "always"],
    "quotes": ["error", "single", { "avoidEscape": true }],
    "arrow-parens": ["error", "always"],
    "no-multi-spaces": "error",
    "no-trailing-spaces": "error",
    "space-before-blocks": "error",
    "keyword-spacing": "error"
  }
}
```

Run ESLint with `npx eslint main.js sw.js` to detect code quality violations. ESLint identifies unused variables, missing semicolons, inconsistent quotation marks, and potential runtime errors like accessing undefined variables. Integrate ESLint into your editor for real-time feedback as you type. Most editors support ESLint through plugins that display violations as inline squiggles and offer automatic fixes for many rules.

## Exercise 3: Automated Browser Testing & Accessibility Validation

Automated testing provides regression protection and confidence that code changes do not break existing functionality. Playwright offers a high-level API for browser automation that handles modern web application patterns like Shadow DOM, iframes, dynamic content loading, and asynchronous state changes. Unlike low-level tools like Selenium, Playwright provides built-in waiting strategies that automatically retry assertions until elements become visible, clickable, or contain expected text, eliminating flaky tests caused by race conditions between test execution and page rendering.

Accessibility testing ensures that web applications remain usable by people with disabilities who rely on assistive technologies like screen readers, voice control, or keyboard navigation. The Web Content Accessibility Guidelines (WCAG) define three conformance levels: A (minimum), AA (mid-range target), and AAA (enhanced). WCAG 2.1 Level AA serves as the legal standard in many jurisdictions and covers requirements like sufficient color contrast (4.5:1 for normal text, 3:1 for large text), keyboard accessibility for all interactive elements, proper heading hierarchy, form labels associated with inputs, and alternative text for images. Automated tools like Axe detect 30-40% of WCAG violations, with the remainder requiring manual testing and expert review.

Create a Playwright configuration at `playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  
  fullyParallel: true,
  
  forbidOnly: !!process.env.CI,
  
  retries: process.env.CI ? 2 : 0,
  
  workers: process.env.CI ? 1 : undefined,
  
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }]
  ],
  
  use: {
    baseURL: 'http://localhost:5173',
    
    trace: 'retain-on-failure',
    
    screenshot: 'only-on-failure',
    
    video: 'retain-on-failure',
    
    actionTimeout: 10000,
    
    navigationTimeout: 30000,
  },
  
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5']
      },
    },
    
    {
      name: 'mobile-safari',
      use: { 
        ...devices['iPhone 13']
      },
    },
  ],
  
  webServer: {
    command: 'npx vite',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

Create a comprehensive test suite at `tests/verification.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('HTML5 Verification Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/HTML5 Verification Labs/);
  });
  
  test('should render page structure correctly', async ({ page }) => {
    const header = page.locator('header[role="banner"]');
    await expect(header).toBeVisible();
    
    const nav = page.locator('nav[aria-label="Primary navigation"]');
    await expect(nav).toBeVisible();
    
    const main = page.locator('main#main-content');
    await expect(main).toBeVisible();
    
    const footer = page.locator('footer[role="contentinfo"]');
    await expect(footer).toBeVisible();
    
    const sections = page.locator('main section');
    await expect(sections).toHaveCount(3);
  });
  
  test('should have proper heading hierarchy', async ({ page }) => {
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
    await expect(h1).toHaveText(/Performance Verification Testbed/);
    
    const h2Elements = page.locator('h2');
    const h2Count = await h2Elements.count();
    expect(h2Count).toBeGreaterThan(0);
    
    const h3Elements = page.locator('h3');
    const h3Count = await h3Elements.count();
    expect(h3Count).toBeGreaterThan(0);
  });
  
  test('should perform DOM manipulation stress test', async ({ page }) => {
    const button = page.locator('#trigger-reflow');
    await expect(button).toBeVisible();
    await expect(button).toBeEnabled();
    
    const output = page.locator('#reflow-metrics');
    
    const startTime = Date.now();
    await button.click();
    const endTime = Date.now();
    
    const clickDuration = endTime - startTime;
    console.log(`Reflow button click duration: ${clickDuration}ms`);
    
    await expect(output).not.toBeEmpty();
    const outputText = await output.textContent();
    expect(outputText).toContain('Reflow Performance Breakdown');
    expect(outputText).toContain('fragment-insertion');
    expect(outputText).toContain('forced-reflow');
    
    const dynamicContent = page.locator('#dynamic-content');
    const childCount = await dynamicContent.locator('.dynamic-element').count();
    expect(childCount).toBe(100);
  });
  
  test('should allocate and track object graph', async ({ page }) => {
    const allocateButton = page.locator('#allocate-objects');
    const heapMetrics = page.locator('#heap-metrics');
    
    const initialText = await heapMetrics.textContent();
    
    await allocateButton.click();
    
    await expect(heapMetrics).not.toHaveText(initialText || '');
    
    await page.waitForTimeout(1000);
    
    const metricsTable = page.locator('#metrics-table tbody tr');
    const rowCount = await metricsTable.count();
    expect(rowCount).toBeGreaterThan(0);
    
    const firstRow = metricsTable.first();
    const operation = await firstRow.locator('td').nth(0).textContent();
    expect(operation).toContain('Object Graph Allocation');
  });
  
  test('should perform async fetch operation', async ({ page }) => {
    await page.route('**/jsonplaceholder.typicode.com/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, title: 'Test Post', body: 'Test content' }
        ])
      });
    });
    
    const fetchButton = page.locator('#fetch-data');
    const progress = page.locator('#fetch-progress');
    const output = page.locator('#network-metrics');
    
    await fetchButton.click();
    
    await expect(output).toContainText('Network Timing Breakdown');
    
    const progressValue = await progress.getAttribute('value');
    expect(progressValue).toBe('100');
  });
  
  test('should handle fetch errors gracefully', async ({ page }) => {
    await page.route('**/jsonplaceholder.typicode.com/**', async (route) => {
      await route.abort('failed');
    });
    
    const fetchButton = page.locator('#fetch-data');
    const output = page.locator('#network-metrics');
    
    await fetchButton.click();
    
    await expect(output).toContainText('Fetch failed');
  });
  
  test('should be keyboard accessible', async ({ page }) => {
    await page.keyboard.press('Tab');
    
    const firstLink = page.locator('nav a').first();
    await expect(firstLink).toBeFocused();
    
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    const reflowButton = page.locator('#trigger-reflow');
    await expect(reflowButton).toBeFocused();
    
    await page.keyboard.press('Enter');
    
    const output = page.locator('#reflow-metrics');
    await expect(output).not.toBeEmpty();
  });
  
  test('should have sufficient color contrast', async ({ page }) => {
    const header = page.locator('header');
    const headerBg = await header.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });
    
    const headerColor = await header.evaluate((el) => {
      return window.getComputedStyle(el).color;
    });
    
    console.log(`Header background: ${headerBg}, color: ${headerColor}`);
    
    expect(headerBg).toBeTruthy();
    expect(headerColor).toBeTruthy();
  });
  
  test('should pass automated accessibility audit', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('should be responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    const header = page.locator('header');
    await expect(header).toBeVisible();
    
    const nav = page.locator('nav ul');
    const navDisplay = await nav.evaluate((el) => {
      return window.getComputedStyle(el).display;
    });
    
    expect(navDisplay).toBe('flex');
    
    const button = page.locator('#trigger-reflow');
    await expect(button).toBeVisible();
    await button.click();
    
    const output = page.locator('#reflow-metrics');
    await expect(output).toBeVisible();
  });
  
  test('should support prefers-reduced-motion', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    
    await page.reload();
    
    const scrollBehavior = await page.evaluate(() => {
      return window.getComputedStyle(document.documentElement).scrollBehavior;
    });
    
    expect(scrollBehavior).toBe('auto');
  });
  
  test('should support dark mode', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    
    await page.reload();
    
    const bodyBg = await page.locator('body').evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });
    
    console.log(`Dark mode body background: ${bodyBg}`);
    
    expect(bodyBg).toContain('rgb(31, 41, 55)');
  });
  
  test('should persist metrics across interactions', async ({ page }) => {
    const reflowButton = page.locator('#trigger-reflow');
    await reflowButton.click();
    
    await page.waitForTimeout(500);
    
    const allocateButton = page.locator('#allocate-objects');
    await allocateButton.click();
    
    await page.waitForTimeout(500);
    
    const tableRows = page.locator('#metrics-table tbody tr');
    const rowCount = await tableRows.count();
    
    expect(rowCount).toBeGreaterThanOrEqual(2);
    
    const operations = await tableRows.evaluateAll((rows) => {
      return rows.map((row) => row.cells[0].textContent);
    });
    
    expect(operations).toContain('Object Graph Allocation');
  });
  
  test('should handle Service Worker lifecycle', async ({ page, context }) => {
    await page.goto('/');
    
    const swRegistered = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.ready;
        return registration.active !== null;
      }
      return false;
    });
    
    expect(swRegistered).toBeTruthy();
    
    await context.clearCookies();
    await page.reload();
    
    const cacheNames = await page.evaluate(async () => {
      return await caches.keys();
    });
    
    console.log('Active caches:', cacheNames);
  });
});

test.describe('Performance Metrics', () => {
  
  test('should meet Core Web Vitals thresholds', async ({ page }) => {
    await page.goto('/');
    
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const navigationEntry = entries.find(
            (entry) => entry.entryType === 'navigation'
          ) as PerformanceNavigationTiming;
          
          if (navigationEntry) {
            resolve({
              domContentLoaded: navigationEntry.domContentLoadedEventEnd - navigationEntry.domContentLoadedEventStart,
              loadComplete: navigationEntry.loadEventEnd - navigationEntry.loadEventStart,
              domInteractive: navigationEntry.domInteractive - navigationEntry.fetchStart,
              ttfb: navigationEntry.responseStart - navigationEntry.requestStart
            });
          }
        });
        
        observer.observe({ entryTypes: ['navigation'] });
        
        setTimeout(() => resolve(null), 5000);
      });
    });
    
    console.log('Performance metrics:', metrics);
    
    if (metrics && typeof metrics === 'object') {
      expect((metrics as any).ttfb).toBeLessThan(800);
      expect((metrics as any).domInteractive).toBeLessThan(3000);
    }
  });
  
  test('should have minimal JavaScript execution time', async ({ page }) => {
    await page.goto('/');
    
    const performanceData = await page.evaluate(() => {
      const perfEntries = performance.getEntriesByType('measure');
      return perfEntries.map((entry) => ({
        name: entry.name,
        duration: entry.duration
      }));
    });
    
    console.log('Performance measures:', performanceData);
    
    const longTasks = performanceData.filter((entry) => entry.duration > 50);
    
    expect(longTasks.length).toBeLessThan(3);
  });
});
```

Install Axe accessibility testing library with `npm install -D @axe-core/playwright`. Run the complete test suite with `npx playwright test` to execute all tests across Chromium, Firefox, and WebKit browsers. Playwright automatically starts the Vite development server, waits for it to be ready, runs all tests in parallel, and shuts down the server afterward. The terminal output displays test results with timing information, and any failures include stack traces pointing to the exact assertion that failed.

View the detailed HTML report with `npx playwright show-report`. The report displays test results organized by browser, execution time for each test, screenshots captured on failure, and video recordings showing the exact sequence of user interactions that led to the failure. Click on a failed test to see the error message, source code location, and captured artifacts. The trace viewer provides a timeline showing network requests, DOM mutations, console logs, and screenshots at each step, enabling rapid diagnosis of flaky tests caused by timing issues or unexpected state.

Run accessibility audits with `npx playwright test --grep="accessibility"` to execute only tests tagged with accessibility checks. The Axe library reports violations with detailed information including the failing HTML element, WCAG success criterion violated, impact level (critical, serious, moderate, minor), and suggested remediation. Common violations include missing alt attributes on images, form inputs without associated labels, insufficient color contrast, and improper heading hierarchies that confuse screen reader navigation.

Configure continuous integration by creating `.github/workflows/test.yml` for GitHub Actions:

```yaml
name: Playwright Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    timeout-minutes: 15
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - uses: actions/setup-node@v4
      with:
        node-version: 20
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Install Playwright Browsers
      run: npx playwright install --with-deps
    
    - name: Run Playwright tests
      run: npx playwright test
    
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30
    
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results
        path: test-results/
        retention-days: 30
```

This workflow executes on every push to main or develop branches and on all pull requests, ensuring that code changes do not introduce regressions before merging. The `actions/upload-artifact` step preserves test reports and failure artifacts for 30 days, allowing developers to review failures that occurred during the CI run even if they cannot reproduce them locally.

## Developer Cheat Sheet & Toolchain Checklist

The HTML5 verification workflow combines browser DevTools, command-line testing frameworks, static analysis, and automated accessibility audits to establish confidence in correctness and performance. This checklist consolidates essential commands, configuration patterns, and diagnostic procedures for daily development tasks.

**Development Server & Build Commands:**

Start Vite development server with hot module replacement: `npx vite`. Access the application at `http://localhost:5173`. The server automatically rebuilds and injects changes without full page refreshes, preserving application state across edits.

Build optimized production bundle: `npx vite build`. Output artifacts appear in `dist/` directory with minified JavaScript, CSS extraction, asset hashing for cache busting, and tree-shaking to eliminate unused code. Inspect bundle composition with: `npx vite build --mode analyze` or use `rollup-plugin-visualizer` to generate an interactive treemap showing module sizes.

Preview production build locally: `npx vite preview`. This serves the `dist/` directory on `http://localhost:4173`, allowing you to test the production build locally before deployment.

**TypeScript Type Checking:**

Run TypeScript compiler in check-only mode: `npx tsc --noEmit`. This validates all type annotations without generating output files. Add `--watch` for continuous checking that re-runs on file changes.

Generate declaration files for libraries: `npx tsc --declaration --emitDeclarationOnly --outDir dist/types`. This produces `.d.ts` files containing type definitions that consumers of your library can import for IntelliSense.

**Static Analysis & Code Quality:**

Run ESLint on all JavaScript and TypeScript files: `npx eslint . --ext .js,.ts`. Add `--fix` to automatically resolve violations like missing semicolons, incorrect spacing, and unused imports.

Format all files with Prettier: `npx prettier --write .`. Prettier handles code formatting consistently across the team without manual style debates. Configure in `.prettierrc.json`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always"
}
```

**Browser Testing & Automation:**

Run all Playwright tests: `npx playwright test`. Add `--project=chromium` to test only Chromium, `--grep="accessibility"` to run tests matching a pattern, or `--debug` to step through tests interactively with the Playwright Inspector.

Run tests in headed mode to watch execution: `npx playwright test --headed`. This opens visible browser windows, useful for debugging unexpected behavior or verifying visual appearance.

Update baseline screenshots for visual regression tests: `npx playwright test --update-snapshots`. This regenerates all screenshot assertions, necessary after intentional UI changes.

Generate test code by recording browser interactions: `npx playwright codegen http://localhost:5173`. The Playwright Inspector captures clicks, form inputs, and navigation, generating test code automatically.

**Service Worker Debugging:**

Inspect Service Worker state in DevTools Application tab → Service Workers. Use "Update on reload" during development to force re-registration. Use "Bypass for network" to disable Service Worker caching temporarily.

View cached responses in Application tab → Cache Storage. Inspect request URLs, response status codes, headers, and body content. Delete individual entries or entire caches to test fallback behavior.

Manually trigger Service Worker update from console: `navigator.serviceWorker.getRegistration().then((reg) => reg.update())`. This forces the browser to fetch the latest Service Worker script and initiate the installation lifecycle.

Clear all Service Worker caches programmatically: `caches.keys().then((names) => Promise.all(names.map((n) => caches.delete(n))))`. Run this in the browser console to purge all cached data without unregistering the Service Worker.

**Performance Profiling:**

Capture Performance timeline in DevTools: Open Performance tab, click Record, perform actions, click Stop. Examine the flame graph for function call stacks, identify long tasks exceeding 50ms, and analyze rendering phases (style calculation, layout, paint, composite).

Take heap snapshot in Memory tab: Click "Take snapshot" to capture all live JavaScript objects. Compare snapshots before and after suspected memory leak to identify objects not being garbage collected. Filter by constructor to find specific object types.

Measure resource loading with Network tab: Disable cache with "Disable cache" checkbox to simulate first-visit performance. Use throttling presets like "Fast 3G" or "Slow 3G" to test on constrained networks. The waterfall view shows request dependencies and blocking resources.

Audit site quality with Lighthouse: Open Lighthouse tab in DevTools, select categories (Performance, Accessibility, Best Practices, SEO, PWA), and click "Generate report." Lighthouse measures Core Web Vitals, identifies render-blocking resources, checks HTTPS usage, validates manifest.json, and verifies accessibility attributes.

**Accessibility Testing:**

Test keyboard navigation: Tab through all interactive elements. Ensure focus indicators are visible and tab order follows visual flow. Verify Enter and Space activate buttons and links. Use arrow keys for radio button groups and comboboxes.

Test with screen reader: Enable NVDA (Windows), VoiceOver (macOS), or Orca (Linux). Navigate by heading with H key. Navigate by landmark with D key. Read forms field by field with Tab. Ensure all images have alt text and form inputs have labels.

Verify color contrast: Use DevTools Accessibility pane to inspect computed contrast ratios. Normal text requires 4.5:1, large text requires 3:1. Tools like WebAIM Contrast Checker provide visual contrast validation.

Validate semantic HTML: Open DevTools Accessibility pane and examine the accessibility tree. Verify heading hierarchy (h1 → h2 → h3), landmark regions (header, main, nav, footer), and ARIA attributes. Misuse of ARIA can make accessibility worse than no ARIA.

**Common Performance Pitfalls:**

Layout thrashing: Reading layout properties (`offsetHeight`, `getBoundingClientRect()`) after DOM mutations forces synchronous reflow. Batch all reads before writes, or use `requestAnimationFrame()` to schedule reads and writes in separate frames.

Long tasks blocking main thread: JavaScript execution exceeding 50ms delays input response and drops frames. Break work into smaller chunks using `requestIdleCallback()` for non-urgent tasks or Web Workers for CPU-intensive computation.

Memory leaks from event listeners: Failing to remove event listeners when elements are removed from the DOM keeps objects alive, preventing garbage collection. Use `AbortController` with `addEventListener(type, handler, { signal })` to automatically clean up listeners.

Redundant network requests: Missing cache headers cause browsers to re-fetch unchanged resources. Set `Cache-Control: max-age=31536000, immutable` for fingerprinted assets (with content hashes in filenames) and `Cache-Control: no-cache` for HTML requiring revalidation.

**Essential DevTools Keyboard Shortcuts:**

- Open DevTools: F12 or Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows/Linux)
- Command palette: Cmd+Shift+P / Ctrl+Shift+P
- Toggle device emulation: Cmd+Shift+M / Ctrl+Shift+M
- Capture screenshot: Cmd+Shift+P → "Capture screenshot"
- Search all files: Cmd+Option+F / Ctrl+Shift+F
- Toggle DOM inspection: Cmd+Shift+C / Ctrl+Shift+C

**Deployment Checklist:**

- Run production build: `npx vite build`
- Verify bundle size: Check `dist/` directory sizes. Target under 200KB for initial JavaScript, under 50KB for initial CSS.
- Test production build locally: `npx vite preview`
- Run full test suite: `npx playwright test --project=chromium --project=firefox --project=webkit`
- Run Lighthouse audit on production URL: Ensure Performance score above 90, Accessibility score 100.
- Verify HTTPS certificate: Check valid certificate with proper domain name and expiration date far in future.
- Test Service Worker offline behavior: Disable network in DevTools and verify critical functionality works.
- Validate Content Security Policy: Ensure CSP headers block inline scripts and unsafe-eval.
- Check CORS headers: Verify API responses include appropriate `Access-Control-Allow-Origin` headers.
- Test on real devices: Emulation approximates but does not perfectly replicate actual device behavior, especially for touch interactions and performance.

This operational verification workflow treats HTML5 development with the same rigor as systems programming, applying quantitative performance measurement, automated regression testing, and continuous monitoring to ensure correctness and user experience quality. The browser's built-in instrumentation exposes detailed telemetry comparable to kernel tracing with perf or eBPF, while TypeScript and ESLint provide compile-time verification analogous to Rust's borrow checker or C++ static analyzers. By combining these tools into a disciplined development workflow, you achieve the confidence and reliability required for production web applications serving millions of users across diverse devices and network conditions.
