# Studio Practice Labs: UI Web Design and Responsive Systems

## Objective & Studio Setup

This guide anchors UI web design practice in direct, observable making. You will work from first principles—visual hierarchy expressed through typographic scale and spatial rhythm, color relationships grounded in contrast and legibility, and responsive layout systems that honor both mobile constraint and desktop abundance. Each exercise isolates a core skill, moves you through progressive difficulty, and concludes with structured critique against real design outcomes.

The discipline demands that you see the relationship between intention and artifact: how a 12-unit grid governs visual order, how a modular type scale prevents arbitrary sizing, how component reuse eliminates inconsistency. You will practice these not as abstract rules, but as lived constraints that liberate decision-making.

### Studio Environment & Tools

**Primary Design Environment:** Figma (or Penpot for open-source parity). Both provide non-destructive artboards, component systems, responsive scaling, and design-to-code hand-off capability. Install one before beginning. Figma's free tier supports unlimited files and viewers; Penpot is fully open-source and self-hostable.

**Secondary Tools:** A pencil sketch pad (A4 or letter size, 50 sheets minimum), 2H and HB graphite pencils, a ruler marked in both millimeters and sixteenths of an inch, and a smartphone or tablet for reference photography and gestural iteration. These enforce spatial reasoning before tool automation.

**Diagnostic Instruments:** Figma's built-in contrast checker (accessibility inspection panel), color picker with hex/RGB output, measurement tool, and responsive preview mode. Keep a grayscale export function active to validate value separation without color dependency. Use a browser's DevTools (Chrome/Firefox) to inspect live websites for breakpoint logic and component structure.

**Reference Library:** Collect 15–20 exemplar designs across three categories: (1) typography-dominant interfaces (news sites, documentation, long-form reading); (2) dense data dashboards (analytics, admin panels, real-time systems); (3) mobile-first e-commerce. For each, screenshot the full responsive range (320px, 768px, 1440px viewports) and annotate the grid structure, type scale, and breakpoint transitions with pencil notes directly on printouts.

**Setup Checklist:**
- Figma/Penpot account created; sample project initialized.
- System fonts installed: Inter or Roboto for sans-serif body copy (Google Fonts or system default); Playfair Display or similar serif for headlines (optional).
- Pencil sketchpad, ruler, and graphite sharpened.
- Reference library downloaded and printed or organized in a tab group.
- DevTools keyboard shortcut memorized (F12 on Windows/Linux, Cmd+Option+I on macOS).
- Browser window resized to 1440px width for desktop view, 390px for mobile view (iPhone 12 Pro equivalent).

---

## Exercise 1: Observation & Fundamentals Drill

### Part 1A: Typographic Scale & Hierarchy Mapping

**Objective:** Develop the hand and eye to recognize and reproduce typographic hierarchy through modular scale ratios. You will analyze an existing interface, extract its type scale, and redraw it on paper to internalize the rhythm.

**Duration:** 60 minutes.

**Procedure:**

Open your browser and navigate to a mature product interface—GitHub, Figma's own documentation site, or Stripe's pricing page. These sites exhibit deliberate, restrained type scales. Take a full-page screenshot at 1440px width and print it at 100% physical size (11 inches wide on letter paper, or A4).

Using your ruler and a 2H pencil, identify every distinct text size on the page. Measure the pixel height of:
- Primary headlines (h1 or `.heading-1`): typically 32–48px.
- Secondary headlines (h2 or `.heading-2`): typically 24–32px.
- Body copy (p or `.body`): typically 16px.
- Small labels or captions (small or `.caption`): typically 12–14px.
- Microcopy or footnotes: typically 11–13px.

Do not guess; measure with your ruler against the printed output. Record each size on a fresh sheet of paper as a vertical line, labeled by function (Headline 1, Subheading, Body, etc.).

Now compute the ratio between consecutive steps. If H1 is 48px and H2 is 32px, the ratio is 48 ÷ 32 = 1.5 (a Perfect Fifth, also called the Major Seventh in typographic parlance). If H2 is 32px and Body is 16px, that's also 1.5. This consistency is not accidental—it is a **modular scale**, a foundational discipline in design systems.

**Modular Scale Construction:**

A modular scale uses a consistent multiplier to generate harmonious intervals. The most common ratios in web design are:

- **1.125 (Minor Second):** Subtle increments; conservative, text-heavy sites. Example: 16px × 1.125 = 18px.
- **1.25 (Major Third):** Balanced, widely adopted. Example: 16px × 1.25 = 20px → 25px → 31.25px → 39px → 49px.
- **1.5 (Perfect Fifth):** Dramatic, high contrast. Example: 16px × 1.5 = 24px → 36px → 54px.
- **1.618 (Golden Ratio / Phi):** Aesthetic, used in luxury and editorial design. Example: 16px × 1.618 = 25.9px → 42px → 68px.

Extract the ratio from your printed example by dividing the larger size by the smaller. Write it down. This is your **foundational scale constant**.

Next, open Figma and create a new file called `type-scale-study-[date]`. On the first artboard (name it `Scale Definition`), create a text frame for each step of the scale. Use the same typeface as your printed reference (or a similar sans-serif system font). Set the sizes exactly as measured. For example, if your scale is 1.25 starting at 16px:

- 16px: "Body text: 16px"
- 20px: "Small heading: 20px"
- 25px: "Heading: 25px"
- 31px: "Subheading: 31px"
- 39px: "Main heading: 39px"
- 49px: "Display: 49px"

Align these vertically with 24px spacing between baselines (a common leading ratio of 1.5× the font size for body). Export this as a PNG and place it next to your printed reference. Compare them line-by-line. They should be visually indistinguishable.

**Hand Drill—Scale Drawing:**

On a fresh page of your sketchpad, without digital tools, sketch a typographic scale in pencil. Draw five horizontal lines, each labeled with a size (16, 20, 25, 31, 39). With an HB pencil, write "Body text" at the 16px line height, "Heading" at 25px, "Display" at 39px. Use light guidelines with your ruler to maintain consistent x-height and ascender heights. The goal is to train your hand to feel the rhythm and your eye to recognize imbalance. Repeat three times over three sheets, each time working faster without measuring.

**Deliverable:** One Figma file with typographic scale definition, one printed and annotated reference, one hand-drawn scale sketch. Photograph the sketch and save alongside your Figma project.

---

### Part 1B: Color Contrast & Legibility Mapping

**Objective:** Master the relationship between color, luminance, and legibility. You will extract a color palette from a reference design, verify its contrast ratios, and identify failure points.

**Duration:** 45 minutes.

**Procedure:**

Return to your reference interface (or choose a new one with a defined color system—Apple, Intercom, or Mailchimp are exemplars). Using Figma's color picker tool (hold Ctrl+C on the design), sample **every distinct color** that appears in the interface. These include:

- Primary brand color (typically a blue, green, or purple).
- Secondary accent color (often a complementary hue or tint).
- Neutral palette (grays for backgrounds, borders, text).
- Status colors (green for success, red for error, yellow for warning, blue for info).
- Shadow/overlay colors (usually black with low opacity).

Create a new artboard in Figma called `Color Palette`. For each color, draw a filled 100×100px square. Label it with its hex code (e.g., `#3B82F6`), RGB values, and semantic name (e.g., `Blue-500`).

Now evaluate contrast. For each color pair that appears as text-on-background in the interface (e.g., dark gray text on white), calculate the WCAG contrast ratio. Figma's contrast checker automates this: select the text layer, open the design panel, scroll to the accessibility section, and inspect the contrast ratio output. The standard is:

- **AA compliance (normal text):** 4.5:1 or higher.
- **AAA compliance (enhanced):** 7:1 or higher.
- **Large text (18px+ or 14px+ bold):** AA requires 3:1, AAA requires 4.5:1.

Document each ratio. If any pair falls below 4.5:1, note it as a **failure point**—this is likely a visual accessibility issue in the original design, or the colors are not paired as text-on-background (they may be used decoratively or in icon form, where contrast rules differ).

**Manual Luminance Check:**

Open your image editor (GIMP, Photoshop, or Krita). Take a screenshot of your reference interface and desaturate it to pure grayscale (Image → Desaturate → Luminosity mode). Export and display it next to the color original. This reveals which color pairs rely purely on hue difference (a failure for colorblind users) versus genuine value separation.

For example, a red error message on a white background has adequate luminance separation. A light blue button on a white background may appear distinct in full color but vanish in grayscale.

**Palette Construction in Figma:**

Create a systematic color palette using Figma's color styles. On a new artboard called `Color System`, organize your palette into named groups:

```text
Primary
├── Primary-50 (#EFF6FF)
├── Primary-100 (#DBEAFE)
├── Primary-500 (#3B82F6)
├── Primary-700 (#1D4ED8)
└── Primary-900 (#1E3A8A)

Semantic
├── Success (#10B981)
├── Warning (#F59E0B)
├── Error (#EF4444)
└── Info (#3B82F6)

Neutral
├── Gray-50 (#F9FAFB)
├── Gray-500 (#6B7280)
├── Gray-900 (#111827)
└── Black (#000000)
```

For each color, create two 200×200px swatches stacked vertically:
- Top: the color itself, labeled with hex and semantic name.
- Bottom: white text (12px, Inter medium) on that color, reading "[Color Name] on White" followed by the contrast ratio.

Measure contrast for every combination likely to appear in your interface. Create a contrast matrix (a table with colors as rows and backgrounds as columns, each cell showing the ratio). Paste this table as an image into Figma or save as a reference document. You should see that only dark colors on light backgrounds (or vice versa) achieve 4.5:1+.

**Deliverable:** One Figma file with extracted palette and contrast matrix. One grayscale rendering of your reference interface. Written notes identifying color pairs that fail accessibility thresholds.

---

### Part 1C: Grid Structure & Spatial Reasoning Recognition

**Objective:** Train your eye to perceive underlying grid systems and their role in organizing layout rhythm. You will deconstruct a live interface, identify its grid unit, and validate layout coherence.

**Duration:** 50 minutes.

**Procedure:**

Open your reference interface at 1440px width. Most modern interfaces use a base grid unit of 4px, 8px, or 16px. Sizes, spacing, and positions are multiples of this unit. Take a screenshot and import it into Figma as a background image on a new artboard called `Grid Deconstruction`.

Using Figma's measurement tool, identify key measurements:
- Left/right padding from viewport edge: measure from the browser chrome to the first content element.
- Horizontal gap between columns or cards.
- Vertical spacing between sections (paragraph gap, card gap, section padding).
- Button and input heights.

For example, if the left padding is 24px and the gap between cards is 16px, your base unit is likely 8px (24 = 8×3, 16 = 8×2). If measurements are 32px and 16px, your base unit is 16px (32 = 16×2, 16 = 16×1). Write down this unit.

Now overlay a grid in Figma. Click the main artboard, open the design panel, scroll to "Layout Grid," and enable a grid with:
- **Grid Type:** Uniform Grid
- **Count:** 12 (the standard for responsive layout in web design)
- **Gutter:** Your identified base unit (e.g., 8px)
- **Margin:** The left/right padding you measured (e.g., 24px)

The 12-column grid divides the 1440px viewport into 12 equal columns. With 24px margins and 8px gutters, each column is (1440 - 48px - 88px [11 gutters]) / 12 = 94px wide. This is your **12-column grid constant** for desktop.

Draw rectangles on key content blocks (header, main card, footer) and snap them to the grid. They should align perfectly. This confirms that the layout is **grid-based**, not arbitrary. If elements do not align, they are either exceptions (intentional breakouts) or the grid is different.

**Responsive Grid Mapping:**

Resize your artboard to 768px (tablet viewport). Enable a grid with 8 columns (fewer columns due to narrower space), same 24px margins, same 8px gutters. Now measure the same content blocks. Do they still align? Often they do not—this is the **breakpoint transition**. Resize again to 390px (mobile) and use a 4-column grid or single-column layout.

Document these breakpoints in a table:

| Viewport | Grid Columns | Margin | Gutter | Column Width |
|----------|--------------|--------|--------|--------------|
| 1440px   | 12           | 24px   | 8px    | 94px         |
| 768px    | 8            | 16px   | 8px    | 80px         |
| 390px    | 4            | 16px   | 8px    | 50px         |

This table is your **responsive grid strategy** for the reference design.

**Hand Drill—Grid Sketching:**

On a new sketchpad page, draw a 12-column grid in light pencil. Use your ruler to divide a 7-inch-wide area into 12 equal columns with gutters. Now sketch a simple layout (header spanning 12 columns, two side-by-side cards spanning 6 columns each, footer spanning 12). Redraw the same layout as an 8-column grid, then as a 4-column grid. This trains your spatial reasoning to anticipate how layouts scale.

**Deliverable:** One Figma file with grid overlay and responsive grid table. One annotated screenshot showing grid structure. One hand-drawn responsive grid sketch.

---

## Exercise 2: Technique Study, Step by Step

### Part 2A: Building a Type Scale System in Figma

**Objective:** Construct a reusable, non-destructive typographic system in Figma using text styles, component tokens, and responsive scaling. You will move from arbitrary sizing to systematic, maintainable type.

**Duration:** 90 minutes.

**Procedure:**

Create a new Figma file called `typographic-system-build-[date]`. Invite no collaborators yet; this is your solo authoring space.

**Step 1: Define Your Scale Constant and Size Range**

On the first page (name it `Scale Reference`), establish your modular scale. For this exercise, use the **Major Third ratio (1.25)** starting from a 16px body baseline. Generate the full scale:

```text
Display Large:  16 × 1.25^5 = 49px (rounded)
Display:        16 × 1.25^4 = 39px (rounded)
Heading Large:  16 × 1.25^3 = 31px (rounded)
Heading:        16 × 1.25^2 = 25px (rounded)
Subheading:     16 × 1.25^1 = 20px (rounded)
Body:           16 × 1.25^0 = 16px
Small:          16 × 0.8   = 13px (rounded down for legibility)
```

Create a text frame for each size and label it. Use Inter or your chosen system sans-serif. Set line height to 1.5× for body (24px), 1.4× for headings (35px for 25px heading), and 1.2× for display (59px for 49px heading). These ratios ensure readable line spacing proportional to the type size.

**Step 2: Create Text Styles**

In Figma's Assets panel, create a new text style library. Name your first style `Display Large`. Set its properties:

- Font: Inter (or system default)
- Font weight: 600 (Semi-bold)
- Font size: 49px
- Line height: 1.2 (59px)
- Letter spacing: -0.02em (slight tightening for large display type)
- Text transform: None

Right-click and select "Edit style." In the modal, check the "Main component" checkbox to enable editing from this central source. Click "Create style." Repeat for each scale size:

| Style Name        | Size | Weight | Line Height | Letter Spacing |
|-------------------|------|--------|-------------|----------------|
| Display Large     | 49px | 600    | 1.2 (59px)  | -0.02em        |
| Display           | 39px | 600    | 1.4 (55px)  | -0.01em        |
| Heading Large     | 31px | 600    | 1.4 (43px)  | 0em            |
| Heading           | 25px | 600    | 1.4 (35px)  | 0em            |
| Subheading        | 20px | 500    | 1.5 (30px)  | 0em            |
| Body              | 16px | 400    | 1.5 (24px)  | 0em            |
| Body Small        | 14px | 400    | 1.5 (21px)  | 0em            |
| Caption           | 13px | 400    | 1.5 (20px)  | 0.01em         |

Create all eight styles. In Figma, you will see them organized hierarchically in the Assets panel under "Text Styles." Each is now a reusable token. When you apply "Display Large" to any text frame, it inherits all properties. If you later edit the central "Display Large" style (say, changing weight to 700), every instance updates automatically.

**Step 3: Create Typographic Components**

On a new page called `Typography Components`, build composite components that combine text styles with predefined layouts and spacing. For example, a "Card Heading" might be a component containing:

1. A "Heading" text style (25px, 600 weight).
2. A fixed margin-bottom of 16px (2 grid units).
3. A dark gray text color (`#1F2937`).

To create this component in Figma:
- Draw a frame 400px wide, auto-height.
- Inside, place a text frame with placeholder text "Card Heading" and apply the "Heading" text style.
- Set the text color to `#1F2937`.
- Select the text frame, then right-click and select "Create component." Name it `Card Heading`.
- In the component panel, set the frame padding to: Top 0, Right 0, Bottom 16, Left 0.

Create additional components:
- `Page Title` (Display Large, `#000000`, margin-bottom 24px)
- `Section Heading` (Heading Large, `#000000`, margin-bottom 16px)
- `Body Text` (Body, `#374151` [mid-gray], line-clamp disabled)
- `Label` (Caption, `#6B7280` [light gray], text-transform uppercase, letter-spacing +0.05em)
- `Link` (Body, `#3B82F6` [blue], text-decoration underline, hover state `#1D4ED8`)

For each component, fill the entire page with an example. Take a screenshot once complete; this is your typographic reference.

**Step 4: Test Responsive Scaling**

Resize the artboard to 768px width (tablet). Do your components still look proportional? They should, because sizes are fixed. But in a real responsive implementation, you might scale certain sizes down. For educational purposes, create a second set of components on a new page called `Typography Components—Mobile` that uses reduced sizes:

| Style Name        | Mobile Size |
|-------------------|-------------|
| Display Large     | 32px        |
| Heading           | 20px        |
| Body              | 15px        |
| Caption           | 12px        |

These are proportionally similar to the desktop sizes (maintaining ~20% reduction) but tuned for smaller screens. Document the scaling strategy: "Display and heading text scales down 15–25% on mobile; body scales down 6%; captions remain at 12px minimum."

**Deliverable:** One Figma file with text styles, typographic components, and mobile variants. Document (in Figma or a separate text file) the scale constant, all size/weight/line-height properties, and the responsive scaling strategy.

---

### Part 2B: Constructing a Color System with Semantic Tokens

**Objective:** Build a systematic, accessible color palette in Figma using semantic naming, contrast validation, and component-level color overrides. You will move from arbitrary color picking to a maintainable, accessible system.

**Duration:** 90 minutes.

**Procedure:**

Work in the same Figma file or a new file called `color-system-build-[date]`. On a page called `Color Palette Definition`, establish your palette. Begin with a primary brand color. For this exercise, use a mid-blue (#3B82F6), which is Web-safe and highly legible.

**Step 1: Generate Tint and Shade Variants**

From your primary color (#3B82F6), generate a ramp of lighter (tints) and darker (shades) versions. The goal is to have multiple intensities for use in different contexts (hover states, disabled states, backgrounds, text). Use a tool like **Chroma.js** or manually adjust in Figma's color picker:

```text
Primary-50:   #EFF6FF (lightest tint, background use)
Primary-100:  #DBEAFE
Primary-200:  #BFDBFE
Primary-300:  #93C5FD
Primary-400:  #60A5FA
Primary-500:  #3B82F6 (base, default button color)
Primary-600:  #2563EB (hover state)
Primary-700:  #1D4ED8 (active/pressed state)
Primary-800:  #1E40AF
Primary-900:  #1E3A8A (darkest shade, text on light background)
```

Create 100×100px swatches for each, stacked vertically on the canvas. Label each with its hex code and semantic name (e.g., "Primary-500").

Repeat for a secondary accent color (optional) and your neutral grayscale:

```text
Gray-50:      #F9FAFB
Gray-100:     #F3F4F6
Gray-200:     #E5E7EB
Gray-300:     #D1D5DB
Gray-400:     #9CA3AF
Gray-500:     #6B7280 (default text on light background)
Gray-600:     #4B5563
Gray-700:     #374151
Gray-800:     #1F2937
Gray-900:     #111827 (darkest, body text on white)
```

Create semantic status colors:

```text
Success:      #10B981 (green, pass, confirmed)
Warning:      #F59E0B (amber, caution, pending)
Error:        #EF4444 (red, failure, alert)
Info:         #0EA5E9 (cyan, informational)
```

**Step 2: Validate Contrast Ratios**

For each potential text-color-on-background pairing, measure the contrast ratio in Figma's accessibility panel. Create a matrix table on a new page called `Contrast Matrix`. Rows are text colors, columns are backgrounds:

|           | White (#FFF) | Gray-50 | Gray-100 | Light Blue (#EFF6FF) |
|-----------|--------------|---------|----------|----------------------|
| Gray-900  | 16.1:1 ✓✓✓   | 12.5:1 ✓✓✓ | 11.4:1 ✓✓ | 10.2:1 ✓✓             |
| Gray-700  | 8.3:1 ✓✓✓    | 6.1:1 ✓✓  | 5.6:1 ✓  | 5:1 ✓                |
| Primary-700 | 5.2:1 ✓✓    | 3.8:1    | 3.5:1    | 1.2:1 ✗               |

Mark each cell with ✓ (AA compliance, 4.5:1+), ✓✓ (AAA compliance, 7:1+), or ✗ (failure, below 4.5:1). Explicitly note which combinations are forbidden for text. For example, Gray-700 on Gray-100 fails at 5.6:1; use Gray-900 instead.

**Step 3: Create Color Styles in Figma**

In the Assets panel, create color styles for each palette entry. For Primary-500:
- Right-click in the color panel and select "Create new color group."
- Name it "Primary."
- Inside, right-click and select "Create color style."
- Name it "Primary / 500."
- Set the hex to #3B82F6.
- Click "Create style."

Repeat for every color in your palette. You will end up with a hierarchical structure:

```text
Colors
├── Primary
│   ├── Primary / 50
│   ├── Primary / 500
│   └── Primary / 900
├── Semantic
│   ├── Success
│   ├── Error
│   └── Info
└── Neutral
    ├── Gray / 50
    └── Gray / 900
```

**Step 4: Apply Colors to Your Typographic Components**

Return to your typographic components (from Exercise 2A). For each one, assign a color style instead of a fixed hex. For example:
- `Page Title` text color: set to "Neutral / Gray-900" style.
- `Link` text color: set to "Primary / 500" style.
- `Link (hover)` text color: set to "Primary / 700" style.
- `Button (error state)` text color: set to "Semantic / Error" style.

Now, if you change the central "Neutral / Gray-900" style to a different hex, all `Page Title` instances update automatically. This is **semantic token binding**—you have decoupled the name from the value, allowing global recoloring.

**Step 5: Document Your System**

On a page called `Color System Guide`, create a written reference:

```text
COLOR SYSTEM GUIDE

Base Color: Blue (#3B82F6)
Neutral: Grayscale (see ramp)
Semantic: Success (green), Warning (amber), Error (red), Info (cyan)

USAGE RULES:
- Text on white or light backgrounds: use Gray-900 or Gray-700
- Text on colored backgrounds: validate contrast in the matrix
- Interactive states: Primary-500 (default), Primary-600 (hover), Primary-700 (active)
- Disabled elements: Gray-300 text on Gray-100 background (3.5:1, acceptable for disabled)
- Error states: use Semantic / Error (#EF4444) for text and 10% opacity for background tint

FORBIDDEN PAIRINGS:
- Primary-500 on Gray-100 (1.8:1 — too low)
- Success on white (3.2:1 — too low for body text, OK for large 18px+ text)
- Any text color on Primary-50 (insufficient contrast)
```

**Deliverable:** One Figma file with color palette ramps, contrast matrix, color styles, and usage guide. All typographic components now have semantic color assignments.

---

### Part 2C: Grid and Responsive Layout Specification

**Objective:** Define a 12/8/4-column responsive grid system with breakpoints, establish spacing constants, and create layout component templates. You will build the structural skeleton that holds all other elements.

**Duration:** 120 minutes.

**Procedure:**

Work in a new Figma file called `grid-system-build-[date]`. On the first page, name it `Responsive Breakpoints`.

**Step 1: Define Breakpoints and Grid Parameters**

Web design typically uses breakpoints at standard viewport widths where the layout changes significantly. Define yours:

```text
BREAKPOINT CONFIGURATION

Mobile:         375–569px  (single column, 4-column grid option)
Tablet:         570–1023px (8-column grid)
Desktop:        1024px+    (12-column grid)
Large Desktop:  1920px+    (12-column grid with wider content area, optional)
```

For each breakpoint, specify:
- Viewport width
- Number of grid columns
- Column width
- Gutter width
- Left/right margin (padding from browser edge to content)

Calculate these values. Begin with the **base unit** of 8px. All spacing must be a multiple of 8px.

```text
MOBILE (375px viewport):
  Columns:      4
  Margin:       16px (2 units)
  Gutter:       8px (1 unit)
  Column Width: (375 - 32 margin - 24 gutters) / 4 = 79.75px ≈ 80px

TABLET (768px viewport):
  Columns:      8
  Margin:       24px (3 units)
  Gutter:       16px (2 units)
  Column Width: (768 - 48 margin - 112 gutters) / 8 = 70px

DESKTOP (1440px viewport):
  Columns:      12
  Margin:       32px (4 units)
  Gutter:       24px (3 units)
  Column Width: (1440 - 64 margin - 264 gutters) / 12 = 97.33px ≈ 97px

LARGE DESKTOP (1920px viewport):
  Columns:      12
  Margin:       64px (8 units, wider margin for breathing room)
  Gutter:       24px
  Column Width: (1920 - 128 margin - 264 gutters) / 12 = 133px
```

Create a table in Figma documenting these values. Take a screenshot and save as a reference.

**Step 2: Create Artboards for Each Breakpoint**

In Figma, create four artboards, each named and sized exactly:

- `Mobile – 375` (375px × 812px, iPhone-proportioned)
- `Tablet – 768` (768px × 1024px)
- `Desktop – 1440` (1440px × 900px)
- `Desktop Large – 1920` (1920px × 1080px)

For each artboard, enable the layout grid. Use Figma's grid settings:
- **Grid Type:** Uniform Grid
- **Count:** (number of columns for that breakpoint)
- **Gutter:** (gutter value from your table)
- **Margin:** (margin value)

Verify the calculated column width matches what Figma shows. If not, adjust manually until correct.

**Step 3: Create Spacing Tokens**

On a new page called `Spacing System`, establish a spacing scale. Use multiples of 8px:

```text
space-1:  4px   (half unit, rare use)
space-2:  8px   (1 unit, default component margin)
space-3:  12px  (1.5 units)
space-4:  16px  (2 units, common margin between sections)
space-6:  24px  (3 units, header/footer margin)
space-8:  32px  (4 units, page section margin)
space-12: 48px  (6 units, hero/large section margin)
space-16: 64px  (8 units, page-level margin)
```

On the artboard, draw rectangles of these exact heights, stacked vertically. Label each. These are your spacing constants; use no other values for margins, padding, or gaps.

**Step 4: Create Layout Components**

On a new page called `Layout Components`, build reusable layout containers. Create components for:

**1. Container (responsive width box)**
- Desktop: 12 columns, full width with margins
- Tablet: 8 columns
- Mobile: 4 columns

In Figma, create a component called `Container`:
- Draw a frame on the Desktop 1440 artboard.
- Width: 1376px (12 columns × 97px + 11 gutters × 24px = 1376px, accounting for margins internally)
- Height: auto
- Stroke: 1px border #D1D5DB (for visibility during design)
- Padding: 0 (margin is handled by parent page)

Right-click and select "Create component." Duplicate this component onto the Tablet and Mobile artboards and resize:
- Tablet: 720px wide (8 columns × 70px + 7 gutters × 16px)
- Mobile: 343px wide (4 columns × 80px + 3 gutters × 8px)

For each variant, right-click on the container and select "Create component set" to link them. You now have one `Container` component with responsive width variants.

**2. Grid Cell (single column unit)**
- Used for stacking cards or other grid-aligned elements

Create a component called `Grid Cell`:
- Width: 1 column (varies by breakpoint)
- Height: auto
- Padding: 16px (space-4)
- Background: #FFFFFF
- Stroke: 1px #E5E7EB

Duplicate onto all three breakpoints. The width will auto-adjust as you create variants.

**3. Section (vertical spacing container)**
- Used to group and space major content sections

Create a component called `Section`:
- Width: full width (auto)
- Height: auto
- Padding: 48px 0 (space-12 vertical, space-0 horizontal)
- Background: transparent or alternating colors (see below)

You now have building blocks. Compose them: a page contains Sections; each Section contains a Container; the Container holds Grid Cells or Card components.

**Step 5: Create Layout Templates**

On a new page called `Layout Templates`, build full-page mockups using your grid and components. Create:

**Template 1: Hero + Grid Card Layout**
- Hero section (full-width Container, centered text, 200px height on desktop, 150px on mobile)
- Spacing (space-8)
- Section with title
- 3-column card grid (each card is 4 columns wide on desktop, 8 columns on tablet, full 4 columns on mobile)
- Footer

Build this on the Desktop 1440 artboard first. Then duplicate the entire frame and place it on the Tablet 768 artboard, manually adjusting column spanning. Repeat for Mobile.

**Template 2: Sidebar + Main Content**
- Left sidebar: 3 columns (desktop), hidden (mobile)
- Main content: 9 columns (desktop), 8 columns (tablet), 4 columns (mobile)
- Spacing: space-6 between sidebar and main

Build this layout showing the responsive transformation.

**Step 6: Document Responsive Behavior**

On a final page called `Responsive Rules`, write plain-language rules for how layouts adapt:

```text
RESPONSIVE LAYOUT RULES

1. At tablet (570px), multi-column grids collapse:
   - 4-column grids (desktop) become 2 columns on tablet, 1 on mobile
   - 3-column grids become 2 on tablet, 1 on mobile
   - Sidebars hide or shift below main content

2. Text sizes scale (see typography system)

3. Spacing adjusts with viewport:
   - Desktop margins: 32px
   - Tablet margins: 24px
   - Mobile margins: 16px
   - Gaps between items remain consistent multiples of 8px

4. Touch targets (buttons, links) must be minimum 44×44px on mobile

5. Images scale with container:
   - Use `background-size: cover` for full-width heroes
   - Use `max-width: 100%; height: auto` for responsive images
```

**Deliverable:** One Figma file with four responsive breakpoint artboards, grid specification table, spacing tokens, layout components (Container, Grid Cell, Section), two layout templates, and responsive behavior documentation.

---

### Part 2D: Building a Card Component System

**Objective:** Design a reusable card component that adapts across breakpoints, integrates your type and color systems, and demonstrates component-level design thinking. You will move from isolated elements to cohesive, compound systems.

**Duration:** 120 minutes.

**Procedure:**

Continuing in your Figma file, create a new page called `Card Component System`.

**Step 1: Define Card Variants**

A card is a contained content unit. Define its variants based on use case:

1. **Article Card** (title, excerpt, thumbnail image, metadata)
2. **Data Card** (metric label, large number, context, change indicator)
3. **Interaction Card** (title, description, call-to-action button)

**Step 2: Build the Article Card**

On your 1440px desktop artboard, create a frame 400px wide, auto-height called `Card – Article – Base`:

```text
Frame: Card – Article – Base
  Width: 400px
  Height: auto (measure after content is placed)
  Padding: 0
  Background: #FFFFFF
  Stroke: 1px #E5E7EB
  Border Radius: 8px (1 unit of roundness)
  Shadow: 0 1px 3px rgba(0, 0, 0, 0.1)

Children (top to bottom):
  1. Image Frame
     - Dimension: 400×200px (2:1 aspect ratio)
     - Fill: placeholder color #D1D5DB
     - Radius: 8px 8px 0 0 (top corners only)

  2. Content Container
     - Padding: 16px (space-4)
     - Background: transparent
     
     Children:
       a. Category Tag
          - Text: "Design" (using Caption style #6B7280)
          - Background: #F3F4F6
          - Padding: 4px 8px
          - Border Radius: 4px
          - Margin-bottom: 8px (space-2)
       
       b. Card Title
          - Text: "Article Title Here" (Heading style)
          - Text color: Neutral / Gray-900
          - Margin-bottom: 8px
       
       c. Card Description
          - Text: "Brief excerpt of the article content..." (Body Small style)
          - Text color: Neutral / Gray-700
          - Clamp: 2 lines (overflow hidden, ellipsis)
          - Margin-bottom: 16px (space-4)
       
       d. Metadata (flex container)
          - Display: flex, justify-content: space-between
          - Left item: Author name + date (Caption style, Gray-600)
          - Right item: Read time (Caption style, Gray-600)
```

Build this structure in Figma. Use text styles for every text element (not manual font sizing). Use color styles for every color. Use spacing tokens (multiples of 8px) for all margins and padding.

Take a screenshot of the completed desktop card. Measure its final height; note it (e.g., 376px).

**Step 3: Create Hover and Active States**

Duplicate your card frame. Name the copy `Card – Article – Hover`. Modify:
- Background: #F9FAFB (subtle shade on hover)
- Stroke: 1px #3B82F6 (primary blue)
- Shadow: 0 10px 25px rgba(0, 0, 0, 0.1) (deeper shadow)

This is the interactive feedback state.

Duplicate again: `Card – Article – Loading`. Show a skeleton state:
- Image: #E5E7EB solid fill
- Title: #E5E7EB animated shimmer (or static for now)
- Description: 2 lines of #E5E7EB (representing text placeholders)

**Step 4: Create Responsive Variants**

On the Tablet 768px artboard, duplicate your card frame and resize to 320px (fits 2×2 grid on tablet). Adjust internal spacing and image aspect ratio if necessary (e.g., 320×160px image). Name it `Card – Article – Tablet`.

On the Mobile 375px artboard, create a card at 343px width (full content area minus margins). Name it `Card – Article – Mobile`. Adjust:
- Image: 343×172px (maintain 2:1 ratio)
- Padding: 12px (reduce from 16px to save space)
- Font sizes: use mobile typography variants if applicable (see Exercise 2A)

Take screenshots of all three variants side-by-side. They should maintain visual hierarchy and legibility at all sizes.

**Step 5: Convert to Components and Create Instances**

In Figma, select the desktop card (`Card – Article – Base`) and right-click "Create component." This becomes your main component.

Right-click again and select "Create component set." You will be prompted to name the base; keep it `Card – Article`. Figma will recognize this as a main component.

Now, right-click on the tablet card and select "Create component" as well. In the design panel, change the "Main component" dropdown to link it as a variant of `Card – Article` with property "Breakpoint: tablet."

Do the same for mobile: "Breakpoint: mobile."

You now have one `Card – Article` component with three breakpoint variants. When you drag an instance of `Card – Article` onto your page, you can toggle between variants in the design panel.

**Step 6: Build the Data Card**

On your artboards, create a second card type for displaying metrics. This card is typically smaller and more graphical:

```text
Frame: Card – Data – Base
  Width: 200px
  Height: 180px (fixed height for dashboard grid)
  Padding: 16px
  Background: #FFFFFF
  Stroke: 1px #E5E7EB
  Border Radius: 8px

Children:
  1. Card Header (flex, justify-content: space-between)
     - Metric Title: "Revenue" (Label style, Gray-500)
     - Icon: (placeholder 20×20px square, Gray-300)
     - Margin-bottom: 12px

  2. Main Value
     - Text: "$42,500" (Display Large style, Primary-900)
     - Margin-bottom: 4px

  3. Change Indicator (flex)
     - Arrow icon or symbol
     - Change text: "+12.5% from last month" (Caption style, Success color)
```

Create this card, then variants for tablet and mobile (adjusted width). Create components and variants as before.

**Step 7: Create a Card Showcase Page**

On a new page called `Card Showcase`, arrange instances of your cards in a grid to show the system in context:

- Desktop grid: 3 Article Cards across the top (using 4-column spans), 4 Data Cards in a 2×2 grid below
- Tablet grid: 2 Article Cards, 2 Data Cards
- Mobile: single-column stack

Use your grid and layout components (Container, Section) to structure this. The page should visually demonstrate how cards scale and stack.

**Deliverable:** One Figma file with fully specified card components (Article and Data), all three breakpoint variants, hover/active/loading states, and a showcase page demonstrating cards in context. All text uses text styles, all colors use color styles, all spacing uses token multiples.

---

## Exercise 3: Finished Piece & Self-Critique

### Part 3: Designing a Complete Responsive Landing Page

**Objective:** Synthesize all prior skills into a cohesive, production-ready landing page design. You will build a multi-section, responsive page from wireframe to high-fidelity mockup, then conduct structured critique against industry standards.

**Duration:** 180 minutes (spread across 2–3 sessions).

**Procedure:**

**Phase 1: Briefing and Wireframing (40 minutes)**

You are designing a landing page for a fictional SaaS product: *ViewMetrics*, a data visualization tool for small businesses. The page needs to:
- Establish brand identity and product value clearly.
- Guide visitors toward a sign-up call-to-action.
- Adapt gracefully from mobile (375px) to desktop (1440px).

Create a new Figma file called `viewmetrics-landing-design-[date]`.

On the first page, titled `Wireframe – Mobile First`, sketch a low-fidelity layout in grayscale using basic rectangles. Include these sections:

1. **Header / Navigation** (120px height)
   - Logo (80px wide)
   - Hamburger menu (mobile only; hidden on desktop)
   - CTA button "Sign Up" (60px height, right-aligned on desktop)

2. **Hero Section** (300px mobile, 500px desktop)
   - Headline: "Visualize Your Business in Seconds"
   - Subheading: 2–3 lines of supporting text
   - CTA button: "Get Started Free"
   - Background: solid color (placeholder)

3. **Features Section** (variable height)
   - 3 feature cards (1 column mobile, 3 columns desktop)
   - Each card: icon, title (Subheading), description (Body Small), CTA link

4. **Social Proof Section** (variable height)
   - Headline: "Trusted by 500+ companies"
   - 5–6 customer logos (placeholder rectangles)
   - Optional: 3–5 testimonial cards (small)

5. **Pricing Table Section** (variable height, desktop only; collapsed on mobile)
   - 3 pricing tiers
   - Each tier: plan name, price, features list, CTA button

6. **Final CTA Section** (200px)
   - Headline: "Ready to get started?"
   - Button: "Start Free Trial"
   - Background: primary color (brand blue)

7. **Footer** (150px)
   - Logo, company links, social links, copyright

Wireframe this on Mobile 375px first. Use the grid you defined (4 columns). For each section, draw placeholder rectangles and label them. Do not add any color or typography yet; this is structure only.

Take a screenshot and name it `wireframe-mobile.png`.

Now wireframe the same page on Desktop 1440px. Sections now have more horizontal breathing room: hero might be 50/50 split image + text, features grid is 3 columns, pricing table displays full detail. Take a screenshot: `wireframe-desktop.png`.

**Phase 2: Visual Design – High-Fidelity Mockup (90 minutes)**

Create a new page in Figma titled `Design – Mobile – 375`.

Using your established systems (typography, colors, spacing, grid), build the full page design:

**Header (Mobile):**
- Frame: 375px wide, 64px height
- Padding: 16px horizontal, 12px vertical
- Background: #FFFFFF
- Stroke: 1px bottom #E5E7EB
- Left: Logo (placeholder 40×40px gray square)
- Right: Hamburger icon (3 horizontal lines, 24×24px, #111827)
- Center (vacant; navigation hidden on mobile)

**Hero Section:**
- Frame: 375px wide (full viewport), auto-height
- Padding: 32px 16px (top/bottom, left/right)
- Background: linear gradient from #EFF6FF (light blue) to #FFFFFF
- Children:
  - Headline: "Visualize Your Business in Seconds" (Display style, 32px mobile variant, Gray-900)
  - Subheading: "Track revenue, monitor growth, and spot trends—all in one dashboard." (Body style, Gray-700)
  - Spacing between: 16px
  - CTA Button: "Get Started Free" (details below)
  - Spacing: 24px above button

**Button Component (CTA):**
Create a new component called `Button – Primary`:
- Frame: auto width with padding 16px 24px (height 48px)
- Background: Primary-500 (#3B82F6)
- Text: "Get Started Free" (Body style, weight 600, color white)
- Border radius: 6px
- Shadow: 0 2px 8px rgba(59, 130, 246, 0.3) (subtle shadow)
- Hover state: Background Primary-600, shadow slightly deeper
- Pressed state: Background Primary-700
- Disabled state: Background Gray-300, text Gray-500

Create this component now. You'll reuse it throughout.

**Features Section:**
- Frame: 375px wide, auto-height
- Background: #F9FAFB (light gray)
- Padding: 48px 16px
- Children (vertically stacked, 1 column):
  - Section Title: "Core Features" (Heading style, Gray-900)
  - Spacing: 32px
  - Feature Card 1 (using Card – Data variant or custom small card)
    - Icon: placeholder 48×48px square, Gray-300
    - Title: "Real-Time Dashboards" (Subheading, Gray-900)
    - Description: "Updated every second..." (Body Small, Gray-700)
    - Spacing below: 24px
  - Feature Card 2: (repeat structure)
  - Feature Card 3: (repeat structure)

**Social Proof Section:**
- Frame: 375px wide, auto-height
- Background: #FFFFFF
- Padding: 48px 16px
- Children:
  - Headline: "Trusted by 500+ companies" (Heading, Gray-900, centered)
  - Spacing: 24px
  - 5 logo placeholders: 50×50px squares, Gray-200, arranged in a horizontal scroll pattern (or 2 rows of 2.5 each for mobile)

**CTA Section:**
- Frame: 375px wide, auto-height
- Background: Primary-500 (blue)
- Padding: 48px 16px
- Children (centered):
  - Headline: "Ready to get started?" (Heading, color white)
  - Spacing: 16px
  - Button: "Start Free Trial" (Button – Primary component, variant: white/outline)

Create a "Button – Primary – Outline" variant:
- Background: transparent
- Stroke: 2px white
- Text: white
- Hover: Background white, text Primary-500

**Footer:**
- Frame: 375px wide, auto-height
- Background: Gray-900 (#111827)
- Padding: 32px 16px
- Children:
  - Logo: 40×40px white square (placeholder)
  - Spacing: 24px
  - Footer links (5 links in a vertical list, 12px Caption style, Gray-400)
  - Spacing: 16px
  - Copyright text: "© 2024 ViewMetrics. All rights reserved." (Caption, Gray-500)

Measure the total height of this mobile page (you can read it in Figma's design panel). Note it; it should be approximately 2200–2400px for a full landing page.

Take a high-resolution export of the entire page (File > Export > PNG, highest setting). Name it `viewmetrics-mobile-hifi.png`.

Now duplicate this entire page. Rename to `Design – Tablet – 768` and resize all frames to 768px width. Adjust:
- Hero section: now 2-column (text on left, placeholder image on right), adjust padding
- Features grid: 2 columns instead of 1
- Logo grid: 3 columns
- Footer: 2 columns (links left, copyright right)

Take a screenshot: `viewmetrics-tablet-hifi.png`.

Duplicate again: `Design – Desktop – 1440`. Adjust:
- Header: full horizontal layout, logo left, navigation center (now visible), CTA right
- Hero: 50/50 image+text split, larger font sizes
- Features: 3-column grid
- Social Proof: 5 logos in one row
- Pricing Table (new section on desktop): add a 3-column pricing grid with 4 rows (plan names, prices, feature lists, buttons)
- Footer: 4-column layout (logo+social, product links, company links, newsletter signup)

Export: `viewmetrics-desktop-hifi.png`.

**Phase 3: Responsive Review and Annotation (30 minutes)**

Place all three mockups side-by-side on a new page called `Responsive Review`. Annotate each with arrows and notes:

- Highlight how the hero section transforms from stacked (mobile) to side-by-side (desktop)
- Mark the breakpoint transitions (375→768px, 768→1440px)
- Note how text sizes adapt (Display Large at 32px mobile, 49px desktop)
- Call out button sizing (48px mobile, 56px desktop)
- Annotate spacing: "16px margins on mobile, 32px on desktop"

Add a legend:

```text
RESPONSIVE ANNOTATIONS:

Mobile (375px):
- Single-column layout
- 16px side margins
- 48px buttons, full width
- Typography: Display 32px, Heading 25px, Body 16px

Tablet (768px):
- 2-column layout where applicable
- 24px side margins
- 50px buttons, 2-column where space permits
- Typography: Display 39px, Heading 25px, Body 16px

Desktop (1440px):
- Multi-column layouts (3+ columns)
- 32px side margins
- 56px buttons, inline with content
- Typography: Display 49px, Heading 31px, Body 16px

BREAKPOINT TRIGGERS:
- At 568px: switch from Mobile to Tablet grid (4→8 columns)
- At 1024px: switch from Tablet to Desktop grid (8→12 columns)
```

**Phase 4: Self-Critique Against Rubric (30 minutes)**

See the Critique Checklist & Common Fixes section below. Use that rubric to evaluate your design.

**Deliverable:** One comprehensive Figma file with wireframes (mobile and desktop), three high-fidelity responsive mockups (mobile, tablet, desktop), annotations, and self-critique notes. Export all three mockups as PNG files and save alongside the Figma file.

---

## Critique Checklist & Common Fixes

Use this rubric to evaluate your work after Exercise 3. Grade yourself on a scale of 1–5 for each criterion (1 = failing, 5 = exemplary). Aim for 4+ across all categories.

### Visual Hierarchy & Typography (20 points)

**Criterion 1: Type Scale Consistency (5 points)**
- **5 (Exemplary):** All text uses the established modular scale (1.25× ratio). No arbitrary sizes. Desktop uses full range (Display 49px → Caption 13px); mobile uses scaled-down variants (Display 32px → Caption 12px). Hierarchy is immediately visible: display text dominates, body text is legible, captions are subordinate.
- **4 (Strong):** Most text uses the scale; 1–2 arbitrary sizes. Hierarchy is clear but not perfectly consistent.
- **3 (Adequate):** 50% compliance with scale. Hierarchy is present but requires squinting.
- **2 (Weak):** Ad-hoc sizing throughout. Hierarchy is confusing or non-existent.
- **1 (Failing):** No discernible scale or hierarchy.

**Common Fix:** Audit every text layer. If a size is not in your scale (13, 16, 20, 25, 31, 39, 49px), change it to the nearest scale value. Use Figma's search to find all text layers and batch-apply text styles.

**Criterion 2: Contrast & Legibility (5 points)**
- **5 (Exemplary):** All body text achieves 7:1+ contrast (AAA). Headlines achieve 4.5:1+ (AA minimum). No text relies solely on color differentiation (passes grayscale test). Links are underlined or distinct.
- **4 (Strong):** Body text 4.5:1+, most headings 4.5:1+. 1–2 elements fall short. Grayscale test mostly passes.
- **3 (Adequate):** Body text 4.5:1+, some headlines below threshold. Mostly readable in grayscale but subtle color-dependent distinctions are lost.
- **2 (Weak):** Multiple elements below 4.5:1. Grayscale rendering reveals legibility failures.
- **1 (Failing):** Widespread contrast failures; text is hard to read on background.

**Common Fix:** Use Figma's accessibility checker on every text layer. If contrast < 4.5:1, darken the text or lighten the background. For color-dependent UI (e.g., status indicators), add an icon or label in addition to color.

**Criterion 3: Line Length & Readability (5 points)**
- **5 (Exemplary):** Body text line length is 50–75 characters (at max width). Leading (line height) is 1.5× font size or greater. Paragraph spacing is consistent (24px gaps).
- **4 (Strong):** Line length 60–80 chars. Leading 1.4–1.6×. Spacing mostly consistent.
- **3 (Adequate):** Line length 50–90 chars; acceptable but could be tighter. Leading 1.3–1.7×.
- **2 (Weak):** Line length >100 chars (too wide). Leading <1.3× or inconsistent.
- **1 (Failing):** Extremely long lines (>120 chars) or cramped leading (<1.2×).

**Common Fix:** On desktop, constrain body text to a max-width of 650px (roughly 75 characters in 16px Inter). Increase line height to 1.5× (24px for 16px body). Use consistent paragraph spacing (always 24px between paragraphs).

**Criterion 4: Hierarchy Through Weight & Size (5 points)**
- **5 (Exemplary):** Headline hierarchy uses distinct weights (Heading: 600, Subheading: 500, Body: 400) *and* distinct sizes (Heading 25px, Subheading 20px, Body 16px). Visual distinction is immediate.
- **4 (Strong):** Weight and size both differentiate; one is less pronounced.
- **3 (Adequate):** Only size or only weight is used to differentiate; hierarchy is present but subtle.
- **2 (Weak):** Hierarchy is not obvious without reading content.
- **1 (Failing):** All text appears the same weight/size.

**Common Fix:** Ensure every text type (H1, H2, H3, Body, etc.) has a unique weight and size combination. Document these in your typography system (Exercise 2A).

---

### Color & Contrast (15 points)

**Criterion 5: Semantic Color Use (5 points)**
- **5 (Exemplary):** Primary color used for key CTAs (Sign Up, Start, Primary Actions). Secondary/accent colors are absent or used minimally. Semantic colors (success green, error red, warning amber) are used correctly and sparingly.
- **4 (Strong):** Primary color dominates CTAs; secondary color used in <3 places. Semantic colors correct.
- **3 (Adequate):** Primary color used but mixed with other colors. Semantic colors occasionally misused.
- **2 (Weak):** Multiple colors compete for attention. Semantic colors used incorrectly (green for warning, etc.).
- **1 (Failing):** Color chaos; no clear primary action color.

**Common Fix:** Limit your page to 2–3 primary colors total. Use primary color (#3B82F6) for all main CTAs. Use secondary color (if present) for 1–2 supporting actions. Reserve semantic colors (green, red, amber) for status feedback only.

**Criterion 6: Color Palette Consistency (5 points)**
- **5 (Exemplary):** All colors are from the defined palette (Primary, Secondary, Semantic, Neutral). No ad-hoc hex values. Colors are applied via color styles in Figma.
- **4 (Strong):** 90%+ of colors are from palette. 1–2 ad-hoc colors.
- **3 (Adequate):** 75%+ from palette. Several off-palette colors but visually coherent.
- **2 (Weak):** <75% from palette; design looks disjointed.
- **1 (Failing):** Arbitrary colors throughout.

**Common Fix:** Audit all colored elements (backgrounds, text, strokes, fills). If a color is not in your palette, replace it with the nearest palette color. In Figma, right-click on each color and assign a color style (from your defined styles). Remove all detached colors.

**Criterion 7: Accessibility & Colorblindness (5 points)**
- **5 (Exemplary):** Grayscale rendering of the page shows no loss of information or hierarchy. No critical distinctions rely on red/green (protanopia/deuteranopia safe). Links are distinguishable from body text.
- **4 (Strong):** Grayscale is mostly readable; 1–2 minor elements lose distinction. Colorblind-safe.
- **3 (Adequate):** Grayscale readable but subtle distinctions are lost (e.g., disabled buttons become hard to spot). Mostly colorblind-safe.
- **2 (Weak):** Grayscale loses meaningful information. Some red/green confusion possible.
- **1 (Failing):** Critical information is color-only; grayscale renders the page unusable.

**Common Fix:** Export a grayscale version of your page (Image → Desaturate in GIMP/Photoshop, or use Figma's export with color profile adjustment). Check that all UI elements (buttons, form states, alerts) are still distinguishable. Add icons or text labels to color-dependent UI (e.g., status indicators).

---

### Grid & Responsive Layout (20 points)

**Criterion 8: Grid Alignment & Structure (5 points)**
- **5 (Exemplary):** All major content blocks align to the 12-column grid (desktop) or 8-column (tablet) or 4-column (mobile). Gutters are consistent (24px desktop, 16px tablet, 8px mobile). No visual misalignment.
- **4 (Strong):** 90%+ alignment; 1–2 elements are off-grid (intentional breakouts).
- **3 (Adequate):** 75%+ alignment. Some elements are off-grid unintentionally.
- **2 (Weak):** <75% aligned. Grid structure is not apparent.
- **1 (Failing):** No grid discipline; layout is chaotic.

**Common Fix:** Overlay a 12-column grid in Figma on the desktop artboard (see Exercise 1C). Adjust element widths to snap to column boundaries. Verify that each element's left and right edges align to grid lines. Repeat for tablet (8 columns) and mobile (4 columns).

**Criterion 9: Responsive Scaling & Breakpoints (5 points)**
- **5 (Exemplary):** Layout smoothly transforms at 375px→768px and 768px→1440px breakpoints. Single-column (mobile) becomes 2–3 columns (tablet) becomes 3–4 (desktop). Font sizes scale proportionally. Spacing adjusts (16px mobile → 24px tablet → 32px desktop).
- **4 (Strong):** Transitions are mostly smooth; 1–2 breakpoints feel awkward.
- **3 (Adequate):** Transitions are functional but could be refined. Font scaling is inconsistent.
- **2 (Weak):** Breakpoints are abrupt or misaligned with content. Scaling is irregular.
- **1 (Failing):** Layout breaks at certain sizes or does not scale.

**Common Fix:** Test your mockups at all three breakpoints (375, 768, 1440px). At each breakpoint, check that columns span correctly, text remains legible, and buttons are clickable (44px min height on mobile). Adjust spacing: use 16px margins on mobile, 24px on tablet, 32px on desktop.

**Criterion 10: Spacing & Padding Consistency (5 points)**
- **5 (Exemplary):** All spacing uses the 8px base unit (8, 16, 24, 32, 48, 64px). No ad-hoc values like 15px or 18px. Padding inside components is consistent; gaps between sections follow the spacing scale.
- **4 (Strong):** 90%+ compliance with 8px unit. 1–2 non-standard values.
- **3 (Adequate):** 75% compliance. Some off-unit spacing.
- **2 (Weak):** <75% compliance; spacing feels irregular.
- **1 (Failing):** Arbitrary spacing throughout; no discernible rhythm.

**Common Fix:** Audit all padding and margin values. If a value is not 8, 16, 24, 32, 48, 64, or 96px, change it to the nearest token. In Figma, use the measurement tool to verify padding inside frames and gaps between elements.

**Criterion 11: Touch Target Sizing (mobile) (5 points)**
- **5 (Exemplary):** All interactive elements (buttons, links, form inputs) are minimum 44×44px on mobile. Spacing between adjacent targets is 8px+ to prevent mis-taps. Hover/focus states are visually clear.
- **4 (Strong):** Most targets are 44px+; 1–2 small elements (captions with inline links) are acceptable at 36px.
- **3 (Adequate):** Targets are 40px+ but could be larger. Spacing is adequate.
- **2 (Weak):** Some targets <40px. Spacing is cramped.
- **1 (Failing):** Targets are too small; difficult to tap on mobile.

**Common Fix:** Measure every button and interactive element on your mobile mockup. If <44px, increase to 44×48px. If multiple buttons are adjacent, add 8–12px spacing between them.

---

### Interaction & User Experience (15 points)

**Criterion 12: Call-to-Action Clarity (5 points)**
- **5 (Exemplary):** Primary CTA is visually dominant (large, bright primary color, prominent position—hero, center, upper-right). Secondary CTAs are present but subordinate (outline style, gray color). User flow is clear: sign up → main CTA.
- **4 (Strong):** Primary CTA is dominant; secondary CTAs are adequately subordinate.
- **3 (Adequate):** Primary CTA is identifiable but not dominating. Flow is somewhat clear.
- **2 (Weak):** Multiple CTAs compete for attention; unclear which is primary.
- **1 (Failing):** No clear CTA or CTA is hidden/difficult to find.

**Common Fix:** Ensure the main CTA (e.g., "Sign Up" or "Get Started") appears in the hero section in primary blue (Button – Primary component). Place it center-left or center-right, not buried below the fold. Use outline or gray buttons for secondary actions (e.g., "Learn More").

**Criterion 13: Affordance & Interactive Feedback (5 points)**
- **5 (Exemplary):** Buttons have clear hover states (color change, shadow increase, underline). Links are underlined or in a distinct color. Form inputs have focus states (blue outline, shadow). Disabled states are visually muted (gray, reduced opacity).
- **4 (Strong):** Most interactive elements have hover/focus states; 1–2 missing.
- **3 (Adequate):** Some hover states present but subtle; focus states not shown.
- **2 (Weak):** Few interactive states; it's unclear what's clickable.
- **1 (Failing):** No interactive states; static design feels unresponsive.

**Common Fix:** Create component variants for each button state: Default (Primary-500 background), Hover (Primary-600, deeper shadow), Active (Primary-700), Disabled (Gray-300 background, Gray-500 text). Show these variants in a component showcase page in Figma. For links, use an underline or a distinct color (Primary-600) to differentiate from body text.

**Criterion 14: Information Hierarchy & Scanability (5 points)**
- **5 (Exemplary):** Page is scannable in <10 seconds. Headlines are descriptive and benefit-focused. Subheadings clarify each section. Bullet points and short sentences reduce cognitive load. White space separates sections. User can identify value proposition immediately (hero headline is clear).
- **4 (Strong):** Page is scannable in ~15 seconds. Hierarchy is clear; minor clarity issues.
- **3 (Adequate):** Scannable in ~20–30 seconds. Some sections lack clear headers or benefits.
- **2 (Weak):** Scannable in >30 seconds. Dense paragraphs; hierarchy is muddled.
- **1 (Failing):** Page is a wall of text; not scannable.

**Common Fix:** Restructure content. For each section, ask: "What is the user trying to do here?" and place that answer in a headline. Use short subheadings (5–8 words). Break long paragraphs into 2–3 sentences max. Add whitespace (space-6 or 24px) between major sections. Test by squinting at the design; the main sections and CTAs should still be recognizable.

---

### Design System Maturity (15 points)

**Criterion 15: Component Consistency & Reuse (5 points)**
- **5 (Exemplary):** All UI elements (buttons, cards, inputs, etc.) are reusable components in Figma. Instances are used throughout the page (not duplicated). Component variants exist for all states (default, hover, disabled, loading). Changes to a main component automatically update all instances.
- **4 (Strong):** Most UI uses components; 1–2 elements are duplicated instead of instanced.
- **3 (Adequate):** Basic components exist but some elements are not componentized.
- **2 (Weak):** Few components; mostly manual duplication.
- **1 (Failing):** No components; every element is unique.

**Common Fix:** Audit your Figma file. Identify repeating elements (buttons, cards, form fields) and convert them to components (right-click → Create component). Then replace all instances with component instances (Edit original → Replace with component). Create variants for all states. Document your components in a "Component Library" page in Figma.

**Criterion 16: Type & Color System Integration (5 points)**
- **5 (Exemplary):** All text uses text styles (not manual font setting). All colors use color styles (not manual hex entry). Typography system matches the modular scale (1.25×). Color palette is comprehensive (primary, secondary, semantic, neutral) and uses semantic naming (e.g., "Primary-500," "Error," "Success").
- **4 (Strong):** 90%+ uses styles. System is mostly comprehensive.
- **3 (Adequate):** 75%+ uses styles. System has gaps (missing dark mode, inconsistent naming).
- **2 (Weak):** <75% uses styles. System is incomplete.
- **1 (Failing):** No styles; all manual sizing and color.

**Common Fix:** In Figma, review your Assets panel. For every distinct text type, create a text style (e.g., "Display Large," "Body," "Caption"). For every distinct color, create a color style (e.g., "Primary-500," "Semantic/Error"). Audit all text and color layers and apply styles instead of manual values.

**Criterion 17: Documentation & Handoff Readiness (5 points)**
- **5 (Exemplary):** Figma file includes documented pages: Typography System, Color System, Grid Definition, Component Library, Wireframes, Responsive Mockups, and Annotations. All components are named consistently (e.g., "Button / Primary," "Card / Article"). Layer names are semantic (not "Frame 42"). Colors, text styles, and components use a consistent naming hierarchy. Ready for developer handoff.
- **4 (Strong):** Most documentation present; minor naming inconsistencies.
- **3 (Adequate):** Basic documentation; some gaps; layers need cleanup.
- **2 (Weak):** Sparse documentation; layer names are generic; unclear structure.
- **1 (Failing):** No documentation; Figma file is disorganized.

**Common Fix:** Create a "System Documentation" page in Figma. Add sections for each subsystem: typography (scale table, styles list), colors (palette with contrast matrix), spacing (token definitions), and components (library list). Rename all layers and frames semantically (e.g., "Button – Primary" instead of "Group 1"). Sort components alphabetically in the Assets panel. Add a "Handoff Notes" section with breakpoint specifications and responsive behavior rules.

---

### Common Design Mistakes & Fixes

**Mistake 1: Arbitrary Type Sizes**
- Symptoms: Sizes are 17px, 23px, 42px—not part of a scale.
- Fix: Define a modular scale (1.25× ratio starting at 16px) and use only those sizes. If a size falls between two scale values, use the larger one (erring on the side of readability).

**Mistake 2: Poor Contrast (Failing WCAG AA)**
- Symptoms: Light gray text (#999999) on white background; unreadable in brightness-challenged environments.
- Fix: Use Figma's contrast checker. All body text must be 4.5:1+. Use Gray-900 or Gray-700 for body on light backgrounds.

**Mistake 3: Unresponsive Images**
- Symptoms: Hero image is 1200px wide; on mobile, it's cropped or causes horizontal scroll.
- Fix: Set image width to 100% with max-width: 100%; set height: auto. For square images, use aspect-ratio CSS or Figma's aspect ratio lock.

**Mistake 4: Buttons That Don't Look Clickable**
- Symptoms: Buttons are small (30px), no hover state, same color as body text.
- Fix: Make buttons minimum 44px tall, 48px+ on desktop. Use primary color. Add a hover state (darker shade, shadow). Add a focus state (outline or background change) for keyboard navigation.

**Mistake 5: Inconsistent Spacing**
- Symptoms: Some sections have 20px gaps, others 24px, others 32px.
- Fix: Define spacing tokens (8, 16, 24, 32, 48px) and use only those values. All margins, padding, and gaps must be multiples of 8px.

**Mistake 6: Grid Misalignment**
- Symptoms: Some elements snap to grid, others are off-grid unintentionally.
- Fix: Enable a visible grid in Figma. Align all major content blocks to column boundaries. Document breakpoint grids (12 columns desktop, 8 tablet, 4 mobile).

**Mistake 7: Text That Breaks Awkwardly on Mobile**
- Symptoms: Headline wraps to 3 lines; paragraphs are wider than the viewport.
- Fix: Test font sizes at all breakpoints. For mobile, reduce headline sizes by 20% (Display Large: 49px desktop → 39px mobile). Set body text max-width: 650px on desktop, full-width on mobile.

**Mistake 8: Color-Only Status Indicators**
- Symptoms: A button is red to indicate error, but someone with protanopia (red-blind) sees just a button.
- Fix: Add text ("Error") or an icon (✗) in addition to the color. Use semantic colors (success green, error red) but reinforce them with iconography or text.

**Mistake 9: Hover States Only on Desktop**
- Symptoms: Button hover effect is defined but not tested on mobile (where hover does not exist).
- Fix: Ensure all interactive elements have focus states (triggered by keyboard tab or touch). Test on mobile using DevTools device emulation.

**Mistake 10: Over-Styled, Unreadable Hero Section**
- Symptoms: Hero text is 72px white on a dark image; unreadable. Hero has gradients, overlays, animations—visual noise.
- Fix: Simplify. Use high-contrast text (white on dark, or dark on light with sufficient opacity). Add a semi-transparent overlay (black at 30–50% opacity) behind text if necessary. Avoid animations in the design file (mention them in handoff notes if needed).

---

## Final Deliverables Checklist

By the end of these three exercises, your studio output should include:

### Exercise 1 Deliverables:
- [ ] Typographic scale study (Figma file + printed reference + hand-drawn sketch)
- [ ] Color palette with contrast matrix (Figma file + grayscale rendering)
- [ ] Grid deconstruction with responsive mapping (Figma file + annotated screenshots)

### Exercise 2 Deliverables:
- [ ] Typographic system file with text styles, components, and mobile variants
- [ ] Color system file with palette ramps, contrast validation, semantic tokens, and color styles
- [ ] Grid system file with responsive breakpoints, spacing tokens, layout components, and templates
- [ ] Card component system (Article, Data variants with all breakpoints)

### Exercise 3 Deliverables:
- [ ] ViewMetrics landing page design file with:
  - [ ] Wireframes (mobile and desktop)
  - [ ] High-fidelity mockups (375px, 768px, 1440px)
  - [ ] Responsive annotations and breakpoint documentation
  - [ ] Self-critique against the rubric above
- [ ] Exported mockups as PNG files (mobile, tablet, desktop)
- [ ] Design system documentation page

### Studio Practice Log:
- [ ] Photographs of hand-drawn sketches (typographic scales, grid sketches)
- [ ] Grayscale and contrast validation exports
- [ ] Notes from critique (what worked, what needs refinement)

All Figma files should be named with timestamps (`[exercise]-[date]`) and organized into a folder structure for easy navigation.

---

## Closing Reflection

UI web design is the intersection of constraint and expression. The grid disciplines your thinking; the type scale prevents chaos; the color system ensures accessibility. Within these systems, you have the freedom to compose layouts that guide users, orient attention, and communicate value.

The exercises above are not one-time drills—they are muscle memory. Return to them. Redesign the landing page with a different color palette. Redraw the grid system for a narrower mobile-first viewport (320px). Rebuild the card components with new typography.

The best designers internalize these systems so thoroughly that they disappear. You do not think about the 8px grid; you *feel* it. You do not calculate 1.25× ratios; you *sense* the rhythm. This comes from repetition and critique. Use the rubric. Compare your work to exemplar designs. Iterate.

Design systems are not constraints; they are foundations. Build on them deliberately.
