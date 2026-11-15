# Lesson 2: Box Model, Stacking Context, Layout Engines

## 1. First-Principles Intuition & Invariants

Every browser's rendering engine is, at its core, a constraint solver. It takes a tree of DOM nodes annotated with style declarations and produces a concrete geometry — a set of rectangles positioned in two-dimensional space — from which pixels are eventually painted. Understanding CSS layout means understanding the rules that constraint solver obeys: where dimensions come from, how containing relationships are established, and what determines which content paints over what other content.

The box model is the foundational invariant from which everything else follows. It was codified in CSS 2.1 and has remained structurally unchanged, though its interpretation has evolved. Every element in a document generates zero or more CSS boxes. Each box is a rectangle with four concentric regions: the content area at the center, surrounded by padding, then a border, then a margin. This layering is not cosmetic. Each region has distinct semantics in the layout calculation. Padding is owned by the element: it shares the element's background and receives pointer events. The border is the outermost visual edge of the element itself. The margin is interpersonal space — it separates the element from its neighbors, and critically, it belongs to no element. It participates in layout but carries no background and captures no events.

The catastrophic design decision enshrined in the original CSS specification is that `width` and `height` apply only to the content area. The total rendered width of an element is therefore `content-width + padding-left + padding-right + border-left + border-right`, and margins are excluded from that calculation because they affect positioning, not the element's own footprint. Every web developer who has ever been surprised to find that setting `width: 200px` on an element with `padding: 20px` produces a 240px box has collided with this invariant.

The `box-sizing` property exists precisely because this default is counterintuitive for most layout work. Setting `box-sizing: border-box` redefines `width` and `height` as specifying the outer edge of the border, not the inner edge of the content. The browser then back-calculates the content area width as `specified-width - padding-left - padding-right - border-left - border-right`. This is the model that virtually every professional CSS codebase adopts globally via:

```css
*,
*::before,
*::after {
  box-sizing: border-box;
}
```

This rule is not stylistic preference. It is a correction to a specification error. When you reason about layouts as a grid of rectangles, you think in border-box terms instinctively, because a "200px box" means a thing that occupies 200px of space, not a thing whose content region is 200px with additional space piled on top.

Margins introduce a further non-obvious invariant: vertical margin collapsing. When two block-level boxes are adjacent in flow — meaning the bottom margin of one element is geometrically adjacent to the top margin of its sibling — those margins do not add. They collapse, and the resulting gap equals the larger of the two values. This applies between siblings, between a parent and its first child (when the parent has no border or padding separating them), and between empty blocks whose top and bottom margins meet. The rationale was typographic: adjacent paragraphs should produce a consistent spacing rhythm, not doubled gaps. In practice, margin collapse creates one of the most reliable sources of layout confusion in CSS because it is conditional on a half-dozen factors and disappears the moment certain properties are set.

Collapsing does not occur between a parent and child when the parent establishes a block formatting context. It does not occur when the elements are separated by a border or padding. It does not occur in flex or grid containers, or when the elements are absolutely positioned or floated. The modern recommendation is to use gap in flex and grid layouts rather than margins for inter-element spacing, precisely because gap never collapses and its semantics are unambiguous.

The containing block is the second foundational invariant. Layout does not happen in a vacuum — every box is sized and positioned relative to some ancestor rectangle called its containing block. For elements in normal flow, the containing block is established by the nearest block-level ancestor's content area. For absolutely positioned elements, it is the nearest ancestor with `position` set to `relative`, `absolute`, `fixed`, or `sticky`. For fixed elements, it is the initial containing block, which corresponds to the viewport. For elements inside a CSS transform, things diverge from the viewport model: a transformed ancestor creates a new containing block for fixed positioning, which is why `position: fixed` inside a transformed parent does not anchor to the viewport as engineers expect.

Percentage values in CSS are always resolved relative to something, and that something is almost always the containing block's width — even for vertical properties like `margin-top: 10%` and `padding-top: 10%`. This is not intuitive but follows from the original specification's decision that percentage margins and padding always reference the inline dimension of the containing block, regardless of the axis in which the property operates. The practical consequence is that the aspect-ratio trick — the old padding-top percentage hack used to create responsive aspect ratios before the `aspect-ratio` property was standardized — works precisely because vertical padding percentages reference horizontal width.

Stacking context is the third invariant, and arguably the most underestimated one. A stacking context is an independent rendering layer that establishes a local coordinate system for depth ordering. Within a stacking context, elements are painted in a defined sequence: the stacking context's background and borders first, then elements with negative z-index, then block-level descendants in flow, then floated descendants, then inline descendants, then elements with z-index zero or auto, then elements with positive z-index. The z-index values only have meaning within the same stacking context. An element with `z-index: 9999` inside a stacking context with a parent that has `z-index: 1` can never paint above a sibling stacking context with `z-index: 2`, no matter how large its own z-index value is.

A stacking context is created by any of the following conditions: an element with `position` not `static` and a `z-index` other than `auto`; any element with `opacity` less than 1; any element with a CSS `transform`, `filter`, `perspective`, `clip-path`, `mask`, `mix-blend-mode`, or `isolation: isolate`; elements with `will-change` referencing any of these properties; and flex or grid children with `z-index` other than `auto`. The list has grown with each CSS specification revision, and that growth is a source of real production bugs: adding a CSS animation to a component that uses `transform` silently creates a new stacking context, trapping any absolutely positioned descendants that were relying on a higher ancestor for their containing block and depth ordering.

---

## 2. Core Architecture & Mechanics

A browser rendering engine processes a document through a pipeline that transforms markup into pixels. The stages are roughly: parse HTML into a DOM tree, resolve CSS into a computed style tree, combine them into a render tree (excluding invisible nodes like `display: none`), perform layout, composite into paint layers, and rasterize to the screen. Modern engines — Blink (Chrome, Edge), Gecko (Firefox), and WebKit (Safari) — have all evolved toward threaded and GPU-accelerated variants of this pipeline, but the logical stages remain consistent.

```
HTML Source
    │
    ▼
┌──────────────┐
│  HTML Parser │  → DOM Tree (Node, Element, Text)
└──────────────┘
    │
    ▼
┌──────────────────┐
│  CSS Parser      │  → CSSOM (StyleSheet, Rule, Declaration)
└──────────────────┘
    │
    ▼
┌──────────────────────────┐
│  Style Resolution        │  → Computed Style Tree
│  (cascade, specificity,  │     (every property resolved to
│   inheritance, custom    │      a concrete computed value)
│   properties)            │
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  Layout (Reflow)         │  → Layout Tree with geometry
│  (box generation, BFC,   │     (x, y, width, height per box)
│   IFC, flex, grid)       │
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  Compositing / Layering  │  → Layer tree (paint layers,
│                          │     stacking contexts, GPU tiles)
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  Paint & Rasterize       │  → Pixel buffers (per layer)
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  GPU Composite           │  → Final screen output
└──────────────────────────┘
```

Layout is where box model arithmetic happens. The engine walks the layout tree and computes, for each box, its position and dimensions. The two primary formatting contexts in CSS 2.1 are the Block Formatting Context (BFC) and the Inline Formatting Context (IFC). A BFC is established by the root element, floats, absolutely positioned elements, inline-blocks, table cells, `overflow` values other than `visible`, and elements with `display: flow-root`. Inside a BFC, block boxes stack vertically, one per line. Each block's left edge touches the left edge of its containing block by default.

The BFC has one crucial structural property that makes it valuable beyond just describing normal flow: a BFC does not overlap floats, and a BFC contains its own floated children. This is why `overflow: hidden` on a container is a classic float-clearing technique — it establishes a BFC, which causes the container to expand to encompass its floated descendants. The `display: flow-root` value was introduced explicitly to trigger this behavior without the side effects of `overflow: hidden` (which clips content) or the legacy `clearfix` pseudo-element hack.

An Inline Formatting Context arises when a block container holds only inline-level content. In an IFC, boxes are laid out horizontally, one after another, within line boxes. A line box's height is determined by its tallest inline participant, and the alignment of shorter inlines within a line box is governed by `vertical-align`. The complexity of IFC arises from the interaction of text, replaced elements (images, iframes), and inline-block boxes sharing a single line box, each potentially having different baseline positions. The CSS `baseline` alignment model is rooted in typographic baseline metrics — ascenders, descenders, the alphabetic baseline — and an inline-block element's baseline is defined as the baseline of its last line box, unless it has no in-flow content or `overflow` is not `visible`, in which case the baseline is its bottom margin edge. This subtlety is responsible for the classic "phantom space below an image" bug, where an `<img>` inside a `<div>` causes unexpected vertical space because the image is treated as an inline element positioned on the alphabetic baseline, with space reserved below it for descenders.

Modern layout engines implement Flexbox and Grid as first-class formatting contexts that replace BFC/IFC for their subtrees. Flexbox layout involves two phases: first, flex items collect into lines (or a single line for `nowrap`), and each item's hypothetical main-size is determined from its `flex-basis`, which defaults to `auto`, resolving to the item's content size. The flex algorithm then distributes free space according to `flex-grow` and `flex-shrink` factors. The key internal invariant is that flex items participate in a flex formatting context, not a BFC, so normal-flow behaviors like margin collapsing are suppressed.

Grid layout introduces a two-dimensional track system. The engine resolves track sizes through a multi-step algorithm. First, track sizing functions like `fr`, `minmax()`, and `fit-content()` are resolved. Free space — the grid container's available space minus the sum of fixed and content-based track sizes — is distributed to `fr` tracks proportionally. Items then placed into grid cells stretch to fill their area unless `align-self` or `justify-self` overrides the default `stretch` behavior. Grid introduces the concept of implicit tracks, which are created when grid placement positions an item outside the explicitly defined grid. The `grid-auto-rows` and `grid-auto-columns` properties define the sizing rules for these implicit tracks.

The CSS box model's internal representation in Blink, for reference, lives in the `LayoutObject` class hierarchy. `LayoutBox` holds the core geometry: `m_frameRect` (position and size), border and padding edge offsets, and overflow rectangles. `LayoutBlockFlow` implements BFC and IFC behavior. `LayoutFlexibleBox` and `LayoutGrid` extend this for their respective algorithms. The paint layer tree (`PaintLayer`) is built on top of the layout tree and corresponds to stacking contexts and composited layers. Each `PaintLayer` owns a `GraphicsLayer` when promoted to GPU compositing.

The practical debugging interface for this pipeline is the browser's DevTools. Chrome's Elements panel renders the box model diagram visually, showing content, padding, border, and margin dimensions with their computed values. The Layers panel exposes the composited layer tree, naming the reason each layer was promoted. The Performance panel's Rendering track shows layout and paint events with their durations. Firefox's DevTools expose the grid overlay directly on the page, rendering track lines and gap areas in-situ.

---

## 3. High-Performance Optimization & Failure Modes

Layout recalculation — called "reflow" in legacy terminology and now simply "layout" in Blink's performance timeline — is the most expensive step in the rendering pipeline because it is synchronous, recursive, and proportional in cost to the number of affected nodes. When a property affecting box dimensions changes, the engine must invalidate the layout of that element and potentially its entire subtree and siblings. Understanding which property changes trigger which pipeline stages determines how to write performant layout code.

The browser compositing model divides the rendering work into three tiers. Changes that only affect composited layer properties — `transform` and `opacity` — can be executed entirely on the GPU compositor thread without touching the main thread. No layout, no paint, just a matrix multiplication applied to an already-rasterized layer. Changes that affect paint — `color`, `background-color`, `border-color`, `box-shadow` — trigger repaint of the affected layer but not layout recalculation. Changes that affect geometry — `width`, `height`, `margin`, `padding`, `font-size`, `display` — trigger a full layout pass, followed by paint and composite. The engineering implication is unambiguous: animations and transitions should operate exclusively on `transform` and `opacity`. Every CSS animation that animates `width`, `margin`, `top`, or `left` is forcing a synchronous main-thread layout on every frame.

```css
/* Forces layout on every frame — avoid */
.panel-bad {
  transition: width 300ms ease, height 300ms ease;
}

/* Compositor-only — preferred */
.panel-good {
  transition: transform 300ms ease, opacity 300ms ease;
  transform: scaleX(0);
  transform-origin: left center;
}
.panel-good.open {
  transform: scaleX(1);
}
```

The `will-change` property tells the browser to promote an element to its own composited layer proactively, before the animation starts. This eliminates the layer-promotion cost at animation start, which can itself cause a visual stutter. However, `will-change` is not free: each composited layer consumes GPU memory proportional to its pixel area, and GPU memory is finite. A common failure mode in mobile web development is to apply `will-change: transform` globally or on many elements simultaneously, exhausting GPU memory and causing the browser to fall back to software rendering for the entire page — the exact opposite of the intended optimization. Use `will-change` surgically: apply it in response to a hover event that precedes an interaction, and remove it when the animation is complete.

Forced synchronous layout (FSL) — sometimes called "layout thrashing" — is the pathology that arises when JavaScript reads a geometry property (which forces the browser to flush pending layout changes to return an accurate value) immediately after writing a style property (which invalidates the layout). The read flushes the invalidated layout, then the write invalidates it again, and the next read flushes it again. In a loop over many elements, this produces one full layout pass per iteration.

```javascript
// Layout thrashing — O(n) synchronous layouts
const elements = document.querySelectorAll('.item');
elements.forEach(el => {
  const width = el.offsetWidth; // forces layout flush
  el.style.width = (width * 1.1) + 'px'; // invalidates layout
});

// Correct approach: batch reads before writes
const widths = Array.from(elements).map(el => el.offsetWidth); // one layout flush
elements.forEach((el, i) => {
  el.style.width = (widths[i] * 1.1) + 'px'; // all writes after reads
});
```

Properties that force layout when read include `offsetWidth`, `offsetHeight`, `offsetTop`, `offsetLeft`, `scrollWidth`, `scrollHeight`, `scrollTop`, `scrollLeft`, `clientWidth`, `clientHeight`, `clientTop`, `clientLeft`, `getBoundingClientRect()`, `getComputedStyle()` when querying dimension or position values, and `innerText` (because it requires a layout to compute text metrics). The `requestAnimationFrame` callback is the correct place to perform writes, as the browser has just completed a frame and no pending layout changes exist at that point.

Stacking context bugs manifest in specific, predictable ways. The most common is a dropdown menu or tooltip rendering beneath content it should cover. The usual cause is that the dropdown's parent has `transform` applied for an animation, or `opacity` is set, or `filter` is used for a visual effect, all of which create stacking contexts that trap the dropdown at the same z-order level as the sibling content that covers it. The diagnostic procedure is to walk up the DOM tree from the failing element in DevTools, checking the Layers panel for each ancestor to identify which one created the new stacking context.

```css
/* Bug: modal is trapped inside a stacking context */
.animated-container {
  transform: translateZ(0); /* creates stacking context */
  z-index: 1;
}

.animated-container .modal {
  position: fixed;
  z-index: 9999; /* meaningless — only competes within .animated-container's context */
}

/* Fix: render the modal outside the transformed ancestor,
   e.g., via a React portal attached to document.body */
```

The `isolation: isolate` property is a precision tool for stacking context problems. It creates a stacking context on demand without changing any visual properties, allowing a component to establish its own internal z-index universe without contaminating the global stacking order. The correct use case is a component library widget that uses internal z-index values for its dropdown and overlay sub-elements, where you want those values to be contained and not conflict with the host application's z-index scale.

```css
/* Component library: establish isolated stacking context */
.dropdown-component {
  isolation: isolate;
  position: relative;
}

.dropdown-component .trigger {
  position: relative;
  z-index: 1;
}

.dropdown-component .menu {
  position: absolute;
  z-index: 10; /* relative to .dropdown-component's context, not the page */
  top: 100%;
  left: 0;
}
```

Percentage height resolution is a persistent source of layout failure. `height: 100%` on an element resolves to a percentage of its containing block's height, but the containing block's height is `auto` by default, meaning it's determined by its content. A percentage of `auto` is undefined and falls back to `auto`, so the percentage has no effect. This is why `height: 100%` on an element requires the entire ancestor chain up to the root to have explicitly set heights. The modern solution is to use viewport units (`vh`, `dvh`) or flex/grid layouts where the container's height is set once and children are sized via `flex: 1` or `align-self: stretch`. The `dvh` unit (dynamic viewport height) corrects the long-standing mobile browser problem where `100vh` includes the browser's retractable UI chrome, causing content to be taller than the visible viewport.

Intrinsic sizing keywords deserve attention because they expose the internal sizing algorithm to CSS authors. `width: min-content` sizes an element to its smallest possible width without overflowing — for text, this is the width of the longest unbreakable word. `width: max-content` sizes to the ideal content width with no line wrapping. `width: fit-content` behaves like `max-content` up to the available space, then shrinks to fit. These keywords are the same algorithms the browser uses internally when sizing flex items with `flex-basis: auto`, grid tracks with `auto` sizing, and table cells. Making them directly addressable allows authors to replicate behaviors that previously required hacks like `display: inline-block` on a block-level element to trigger shrink-wrapping.

The `contain` property is the most underused performance tool in CSS. It allows an author to signal containment boundaries to the layout engine, restricting the scope of layout, paint, and style recalculation to the element's subtree. `contain: layout` guarantees that nothing outside the element affects its internal layout and nothing inside it affects external layout. `contain: paint` guarantees that the element's content does not paint outside its border box. `contain: style` limits the scope of counter and quote style changes. `contain: strict` is the combination of all three. For component-based architectures where each widget is structurally independent, `contain: layout paint` on each root component element dramatically reduces the blast radius of DOM mutations, because the browser knows a change inside one component cannot require re-layout of unrelated components.

```css
/* Container component: explicitly scoped layout and paint */
.widget-card {
  contain: layout paint;
  position: relative; /* establishes containing block for absolute children */
  border-radius: 8px;
  overflow: hidden; /* clips paint to border-box; redundant with contain:paint but explicit */
}
```

The Container Queries specification (`@container`) builds on this containment model: a `@container` query fires when the nearest ancestor with `container-type: inline-size` (or `size`) changes its dimension, allowing components to respond to their allocated space rather than the viewport. This inverts the classic responsive design model and is the correct tool for reusable components that must adapt to arbitrary layout contexts in a design system.

Understanding layout performance at this level requires using the browser's profiling tools rigorously. Chrome DevTools Performance panel records a full timeline. In the flame chart, layout events appear in purple. Each layout event shows its duration and the number of nodes laid out. A forced synchronous layout is flagged explicitly with a red triangle and a trace showing which JavaScript call caused the flush. The Rendering settings panel exposes overlays including "Layout Shift Regions" (flashing blue on elements that caused Cumulative Layout Shift) and "Paint Flashing" (green rectangles over repainted regions). These overlays turn invisible optimization problems into immediate visual signals, closing the feedback loop between code change and rendering behavior.
