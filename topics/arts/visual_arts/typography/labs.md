# Operational Verification Labs: Typography

## Objective & Studio Setup

Typography for visual designers and graphic practitioners operates at the intersection of visual communication and brand identity. Where a designer uses grid systems and proportional spacing to verify visual balance, a typographer uses letterform geometry, optical spacing, and hierarchical contrast to verify compositional clarity in page design, visual systems, and design documentation. This lab series treats typography as a **precision instrument for brand identity, legibility, and visual coherence**.

Your studio setup for these exercises requires:

**Core Software Stack:** A vector graphics editor (Adobe Illustrator, Affinity Designer, or open-source Inkscape) paired with your raster image editor of choice (Adobe Photoshop, Affinity Photo, or open-source GIMP). A reference display calibrated to 100–120 cd/m² with accurate color rendering (ideally sRGB or Adobe RGB). A type reference library: download free metric-rich typefaces from Google Fonts or commercial foundries like FontFont or Hoefler & Co. A working layout mockup in your editor with artboard dimensions and color mode locked to your final design.

**Physical Reference Materials:** Print samples of professional graphic design (magazine spreads, book covers, posters). A type specimen sheet template (downloadable from TypeTogether or Monotype). A ruler calibrated in both points (pt, 1/72 inch) and millimeters. A neutral-gray viewing booth or diffused daylight for color-critical work.

**Diagnostic Instruments:** A screen color picker tool (native to most vector editors, or the free Pixel Color Picker browser extension). A type metrics plugin or ruler overlay in your vector editor. A PDF proof-reader with annotation capability (Acrobat Pro or Preview on macOS with markup tools).

The strategic goal is to develop **typographic literacy**—the ability to perceive and control micro-adjustments in letterform rhythm, weight distribution, and spatial relationships that directly impact how a reader processes visual information (exhibition catalogues, data tables, social media assets). Just as a graphic designer trains their eye to detect subtle shifts in proportion and alignment, a typographer trains their eye to detect 5% variations in letter spacing that collapse under magnification or expand under reduction.

---

## Exercise 1: Letterform Anatomy, Metric Foundations & Optical Spacing

### Objective

Master the geometric and proportional language of typography—the **x-height, baseline, cap height, descenders, and ascenders**—and learn to apply optical spacing corrections that compensate for the human eye's perceptual biases. By the end of this exercise, you will construct a custom type specimen sheet with proven optical adjustments, and you will apply those principles to a typographic layout mock-up in a design application or page layout software.

### Part A: Letterform Anatomy & Metric Grid Construction

Begin by opening a new document in your vector editor set to **A4 (210 × 297 mm) or Letter (8.5 × 11 in) at 300 DPI resolution**. This resolution ensures crisp output for print mockups and high-fidelity screen display.

Create a **baseline grid** as your fundamental reference. Set the grid spacing to **4 mm vertical spacing** (or 12 points, a typographic standard). This grid will anchor all letterform measurements. In Illustrator, navigate to **Edit > Preferences > Guides & Grid**, set the grid increment to 4 mm, and enable **Show Grid** (View > Show Grid). In Affinity Designer, use **View > Guides > Create Grid** with equivalent spacing.

Now, import or create a reference typeface. Download the **Noto Serif** family from Google Fonts (a high-quality, freely licensed typeface with extensive character sets and optical sizes). Use the sans-serif variant first: **Noto Sans**. Set a test string of capital letters, lowercase letters, numerals, and descenders. Type the string: **"HAMBURGEFONSTIV hamburgefonstiv 1234567890 gjpyq"** at a large size (72 pt or larger) to examine the anatomy clearly.

On your baseline grid, identify and label these core measurements on a reference letterform (use the capital **H** and lowercase **n**):

- **Baseline:** The horizontal line upon which most letters sit.
- **Cap Height:** The vertical distance from the baseline to the top of a capital letter (e.g., the top of **H**). This is typically 70–75% of the overall em-square in most typefaces.
- **X-Height:** The vertical distance from the baseline to the top of a lowercase letter without ascenders (e.g., the height of the letter **x**). The x-height-to-cap-height ratio is a critical identifier of a typeface's personality; narrow x-heights feel formal and elegant, while tall x-heights feel friendly and open.
- **Ascenders:** The vertical extension of letters like **b**, **d**, **f**, **h**, **k**, **l**, **t** above the x-height. Ascender height typically extends 20–30% above the x-height.
- **Descenders:** The vertical extension of letters like **g**, **j**, **p**, **q**, **y** below the baseline. Descender depth mirrors ascender height for visual balance.

Using the ruler and measurement tools in your vector editor, record these five metrics for your chosen typeface. Create a simple diagram with horizontal lines at each level, labeled with their exact pixel or millimeter distances. This becomes your **metric reference sheet**—bookmark it.

### Part B: Optical Spacing Corrections & Kerning

Letterforms do not sit in perfectly rectangular boxes. The human eye perceives spacing based on the **visual weight and shape profile of adjacent letterforms**, not on mathematical distance alone. This is the core principle of **optical spacing** or **kerning**.

Demonstrate this principle by typing three word pairs in your vector editor:

1. **"AT"** (a capital A followed by a capital T—these two letterforms have conflicting shapes: A has a right-leaning stroke, T has a horizontal top with centered vertical stem)
2. **"VA"** (a capital V followed by a capital A—both are angular, with converging apex points)
3. **"To"** (a capital T followed by lowercase o—the horizontal bar of T overshoots to the left, and lowercase o is round)

Set each pair at 96 pt in Noto Sans. Use your vector editor's glyph panel or font metrics to examine the **default spacing** (known as the sidebearings). Most digital fonts are pre-kerned with common pairs, but manual optical adjustment is still required.

The rule of thumb: **Optically equal spacing between letterforms requires *mathematically unequal* distances.** Examine the "AT" pair. The visual gap between these two letters appears larger than the same mathematical distance between "HH" because A's right stroke and T's right overhang create a visual "pocket" that reads as empty space. Move the T leftward by 10–15% of the original gap until the space between them *optically equals* the space between other letter pairs in your test string.

Perform this adjustment manually in your vector editor by:

1. Selecting the T with the direct selection tool.
2. Nudging it leftward using keyboard arrow keys (typically 1 mm or 5 pixels per keystroke; hold Shift for larger increments of 10 mm or 50 pixels).
3. Stepping back 1 meter from your screen and assessing whether the spacing now feels balanced relative to spacing in adjacent letter pairs like "HN" or "TO".
4. Recording the final distance using the **Measure Tool** (View > Measure in most vector editors).

Repeat this for the VA and To pairs. Create a reference card showing the **original mathematical spacing** versus your **optically corrected spacing**. This card becomes a training aid for future typographic work.

### Part C: Type Specimen Sheet Construction & Hierarchical Contrast

A **type specimen sheet** demonstrates a typeface across multiple sizes, weights, and contexts. It serves dual purposes: as a **visual proof** of the typeface's capabilities and as a **diagnostic tool** to verify optical consistency across scales.

Create a new A4 document. Set up a **12-column grid** (a Swiss design standard). Each column is approximately 17.5 mm wide with 2.5 mm gutters. Structure your specimen sheet with these sections:

**Section 1 – Typeface Identification (Columns 1–12, 1 row, Top 30 mm):** Display the typeface name in the largest optical size. For Noto Sans, use 48–60 pt, set in the regular weight. Below it, add metadata: foundry, designer, release date, character set coverage (e.g., "Latin Extended-A, Greek, Cyrillic"), and any optical sizes available (many professional typefaces offer optical variants optimized for specific sizes: caption, display, text).

**Section 2 – Specimen Text (Columns 1–12, spanning 150 mm):** Use the **pangram** (a sentence containing every letter of the alphabet) repeated at different sizes and weights:

At **18 pt (body text size):** "The quick brown fox jumps over the lazy dog."

At **14 pt (caption size):** Repeat the pangram twice, with 1.2 line spacing.

At **28 pt (subheading size):** "The quick brown fox jumps over the lazy dog."

At **48 pt (display size):** "The quick brown"

Examine each size and note where **optical distortions** appear. At very small sizes (14 pt), serifs (if present) may become too delicate and blur on screen; at display sizes (48 pt), subtle curves in letterforms become exaggerated. This is normal and expected.

**Section 3 – Weight & Italic Variants (Columns 1–6, spanning 100 mm):** Display the pangram in each available weight: Light (if available), Regular, SemiBold, Bold, and Italic variants. At 16 pt, set each variant at a consistent baseline and compare the visual rhythm and density.

**Section 4 – Numerical & Punctuation Reference (Columns 1–12, spanning 40 mm):** Set all numerals (0–9), common punctuation (. , ; : ! ? – — " " ' '), currency symbols ($ € £ ¥), and mathematical symbols (+ − × ÷ = %) at 24 pt. This reference confirms that numerals are proportionally consistent and punctuation marks align properly with letterforms.

Export this specimen sheet as both a **PDF** (for print reference) and a **high-resolution PNG** (for screen reference and design mockups).

### Part D: Applying Optical Spacing to Tabular Figures in Data Tables

Open your design software (InDesign, Affinity Publisher, or Figma). Create a new document with a standard A4 page size and 12 mm margins. Set up a 12-column grid with 8 mm column widths and 4 mm gutters.

Create a **data table** with timetable information. In InDesign, use **Table > Insert Table** and set it to 6 columns × 8 rows. In Affinity Publisher, insert a table via **Insert > Table**. In Figma, use the community plugin for tables or construct the grid manually with rectangles and text frames. Populate the table with sample data: a weekly transit schedule with times (08:00, 09:15, 10:30) and location names.

Set the table's **header row** text size to **14 pt** with **18 pt leading**. Select a **tabular-figure typeface** such as **IBM Plex Mono** or **Courier Prime** (monospace fonts with consistent character widths, essential for numerical alignment). Set the body rows to **11 pt** with **14 pt leading** and apply **−20 tracking** to tighten the overall column density.

Now, examine the table in your design software and inspect the **optical spacing** between numerals and location labels. Look for visual inconsistencies in the alignment of numeric columns: "08:00", "09:15", "10:30", and check letter pairs in location names like "St", "nd", "th", and "or" across rows.

For any numerals or letter pairs that feel optically unbalanced due to tabular-figure constraints, use the **manual kerning** feature in your design software (InDesign: **Window > Type & Tables > Character**; Affinity Publisher: **Character panel**; Figma: **Text settings**) to fine-tune spacing at **±5 to ±15 units** per pair. Adjust tracking to **−15 to −25** for improved visual cohesion. Record your adjustments, apply a **1.5× modular-scale ratio** to secondary headings, and export the refined table as a reference PDF.

### Verification Checkpoint

Print or display your type specimen sheet on a reference monitor. From 1 meter away, assess:

- **Baseline Alignment:** Do all letterforms sit on the same baseline? Are descenders evenly spaced below the baseline?
- **Optical Spacing:** Do letter pairs like "AT", "VA", and "To" feel evenly spaced, or do gaps appear to shift in size?
- **Size Consistency:** Does the typeface maintain legible clarity at 14 pt and 48 pt, or do certain sizes feel uncomfortable to read?
- **Weight Hierarchy:** If displaying multiple weights, is the visual weight progression smooth and predictable (Light → Regular → Bold)?

Document your findings in a brief written note (100–150 words). This becomes your **baseline assessment** for future typographic decisions in score layouts and visual assets.

---

## Exercise 2: Type Selection, Modular Scale & Hierarchical Systems

### Objective

Learn to construct a **modular typographic scale**—a mathematical ratio applied to font sizes to create proportional relationships that feel harmonious and functional. This principle mirrors the logic of **grid-based layout systems**: just as column widths follow predictable proportional ratios (2:1, 3:2, 4:3), type sizes follow predictable ratios (1.25, 1.33, 1.618). By the end of this exercise, you will build a typographic scale for a full exhibition catalogue booklet, and you will verify that your scale remains legible at multiple print sizes and screen resolutions.

### Part A: Understanding Modular Scale Ratios

The **modular scale** is a mathematical framework where each subsequent size is calculated by multiplying the previous size by a fixed ratio. The most common ratios in typography are:

- **Perfect Fourth (1.33):** Also known as 3:2 ratio. Creates a medium spacing between sizes; feels balanced and widely used.
- **Golden Ratio (1.618):** Also known as Phi (φ). Creates generous spacing; often used in luxury or editorial design.
- **Major Third (1.25):** Creates tight, controlled spacing; useful for dense content with many hierarchical levels.
- **Perfect Fifth (1.5):** Creates generous spacing; useful for display-heavy designs with few sizes.

For this exercise, use the **Major Third (1.25)** ratio as your foundation. This ratio is mathematically elegant and produces a series that feels natural to the ear and eye.

Begin with a **base size of 16 pt**—this is the standard body text size for screen reading and print body copy. Apply the 1.25 multiplier iteratively to generate your full scale:

- **Micro/Caption:** 16 ÷ 1.25 = 12.8 pt (round to 13 pt)
- **Small/Footnote:** 16 pt (base)
- **Body/Paragraph:** 16 pt (base)
- **Lead/Intro:** 16 × 1.25 = 20 pt
- **Subheading 3:** 20 × 1.25 = 25 pt
- **Subheading 2:** 25 × 1.25 = 31.25 pt (round to 32 pt)
- **Subheading 1:** 32 × 1.25 = 40 pt
- **Heading 2 (Section):** 40 × 1.25 = 50 pt
- **Heading 1 (Title):** 50 × 1.25 = 62.5 pt (round to 64 pt)

Create a **type scale reference sheet** in a text editor or spreadsheet with these sizes. This scale now becomes your **typographic constitution**—you will use only these sizes throughout your project. Any time you need a font size decision, consult this scale rather than choosing arbitrary sizes.

### Part B: Type Family Selection & Weight Strategy

Select a **primary typeface family** that offers multiple weights and includes both serif and sans-serif variants (if available), or choose a versatile family with excellent weight variation. For this exercise, download and install the **Inter** typeface family from rsms.me/inter (a modern, humanist sans-serif with 18 weights and exceptional screen rendering) or **IBM Plex** from github.com/IBM/plex (a corporate-grade family with serif, sans, and monospaced variants).

Establish a **weight hierarchy**:

- **Body Text:** Regular (400 weight)
- **Emphasis/Bold:** SemiBold (600 weight) or Bold (700 weight)
- **Headings:** Bold (700 weight) or ExtraBold (800 weight)
- **Display/Titles:** Bold (700 weight) or Black (900 weight)

The principle is **minimal contrast for maximum clarity**. Using too many weights (Light, Regular, Medium, SemiBold, Bold, ExtraBold, Black all in one document) creates visual chaos and dilutes the hierarchy. Restrict yourself to **three weights maximum**: one for body, one for emphasis, and one for headings.

In your vector editor or document software, create a **weight reference card**:

Type the sentence: "The quick brown fox jumps over the lazy dog." at 16 pt in each of your selected weights (typically three: Regular, SemiBold, Bold). Set them on a single page with clear labels. Export as PDF and compare on screen and in print. Assess:

- **Readability:** Does each weight feel comfortable to read at body size?
- **Contrast:** Is the visual contrast between Regular and Bold sufficient to signal hierarchy without feeling jarring?
- **Screen Rendering:** On screen (especially on lower-resolution displays), do heavier weights become muddy or illegible?

Record your observations and finalize your weight choices.

### Part C: Constructing a Full Exhibition Catalogue Booklet

Now apply your modular scale and type selections to a real project: **exhibition catalogue booklet**. Exhibition catalogues typically include: exhibition title, artist name, artwork list with medium and dimensions, curatorial statement, artist statement, exhibition credits, copyright information, and artwork captions.

Open a document editor (Microsoft Word, Google Docs, or preferably a layout program like Adobe InDesign or Affinity Publisher). Create a new document set to **A4 size (210 × 297 mm)** with the following margins: **top 20 mm, bottom 20 mm, left 15 mm, right 15 mm**. This leaves a content area of approximately **180 × 257 mm**, which accommodates a 2- or 3-column grid comfortably.

Structure your catalogue as follows:

**Page 1 – Cover (Title Page):**

- **Exhibition Title (Top):** Heading 1 (64 pt, Bold, Inter or IBM Plex). Set in all caps: "FORMAL GEOMETRIES". Align center. Apply 0 pt letter spacing (default).
- **Artist Name (Center):** Subheading 1 (40 pt, Bold). Set in Title Case: "Emma Richardson". Align center. Add 1 mm vertical spacing below.
- **Curatorial Note (Below):** Lead text (20 pt, Regular, italic). "Paintings and sculptures exploring the intersection of space and form." Align center.

**Page 2 – Artwork List:**

- **"Artworks" Section Header:** Heading 2 (32 pt, Bold, all caps). Align left. Add 1 cm vertical space below.
- **Artwork Entries:** Body text (16 pt, Regular). Format each work as: **"Title, [Year] | Medium | Dimensions (H × W × D)"**. Use a monospaced font (Courier or IBM Plex Mono) for dimensions to ensure consistency. Set line spacing to 1.5 (relaxed spacing for readability). Add 0.5 cm space between each entry.

Example:

```text
1. Untitled (Blue Series 1), 2023 | Oil on canvas | 120 × 90 cm
2. Geometric Study IV, 2024 | Mixed media on paper | 42 × 29.7 cm
3. Monolith, 2023 | Stainless steel | 180 × 60 × 45 cm
```

**Page 3 – Credits & Information:**

- **"Exhibition Credits" Section Header:** Heading 2 (32 pt, Bold, all caps). Align left.
- **Credits List:** Body text (14 pt, Regular). Format as: **"Role: Name/Organization"**. Set line spacing to 1.25 (slightly tighter for credits).
- **"Exhibition Notes" Section Header:** Heading 2 (32 pt, Bold, all caps). Align left. Add 1 cm space above.
- **Exhibition Notes:** Body text (13 pt, Regular). Justify text left. Add 0.5 cm space after this section.
- **Copyright Information:** Micro text (13 pt, Regular, 50% gray). Justify left.

**Page 4 – Artist Statement:**

- **"Artist Statement" Section Header:** Heading 2 (32 pt, Bold, all caps). Align left.
- **Statement Text:** Body text (16 pt, Regular). 2–3 paragraphs (approximately 250–400 words). Justify text. Set line spacing to 1.5 for comfortable reading. Apply 0.5 cm paragraph indent (first line indent) to each paragraph.

### Part D: Verifying the Document at Multiple Scales

Export your catalogue as a high-resolution **PDF (300 DPI)** and a **web-optimized PDF (72 DPI)**. Print the 300 DPI version at full size (A4). On screen, open the 72 DPI version and zoom to 100%.

Assess the following:

**Print Assessment (A4 Full Size):**

- **Baseline Alignment:** Are all text blocks aligned to a baseline grid? (Most professional layout software supports baseline grids; enable it in your preferences and align all text to it.)
- **Heading Hierarchy:** Can you instantly identify which text is a heading, which is body, and which is caption, based on size and weight alone?
- **Line Length:** Measure the line length of body text. Optimal line length for comfortable reading is **50–75 characters per line**. Count the characters in a typical body text line. If you have fewer than 40 or more than 90 characters per line, adjust your margins or column width.
- **Spacing Between Sections:** Is there consistent vertical spacing between sections? Each space should correspond to one of your modular scale sizes (e.g., if you use 32 pt for Heading 2, leave 32 pt of space after it before the next section begins).

**Screen Assessment (72 DPI, 100% Zoom):**

- **Readability at Small Sizes:** Does body text (16 pt) feel comfortable at arm's length (approximately 60 cm from your eyes)?
- **Font Rendering:** Are there any jagged edges or blurriness in your chosen typeface? If so, your vector editor or PDF renderer may be using sub-optimal anti-aliasing. Try exporting at 150% zoom and re-scaling in an image viewer.
- **Color Contrast:** If you used gray text (as in copyright information), verify that the contrast ratio between text and background meets accessibility standards (minimum 4.5:1 for body text, 3:1 for large text). Use the WebAIM contrast checker (webaim.org/resources/contrastchecker) to verify.

### Verification Checkpoint

From 2 meters away, view your printed catalogue. Can you scan the document and instantly locate: (1) the exhibition title, (2) the list of works, and (3) the credits? If yes, your hierarchy is working. If not, increase the size or weight of key headings.

Document your findings: Did the modular scale produce a harmonious visual result? Did any sizes feel awkward or redundant? This assessment informs refinements to your scale for future projects.

---

## Exercise 3: Grid Systems, Columnar Layouts & Multi-Page Documents

### Objective

Master the **Swiss grid system**—a modular, proportional framework for laying out text and images across multiple pages. This exercise teaches you to construct a **12-column grid** (or 8-column for simpler layouts), apply it consistently across pages, and verify that your layout remains readable and visually cohesive when scaled or reformatted for different media (print, screen, tablet).

### Part A: Constructing a 12-Column Grid

Begin with your A4 document from Exercise 2. In a professional layout program (Adobe InDesign or Affinity Publisher), establish a **12-column grid** with consistent gutter widths.

**Grid Dimensions:**

- **Page Size:** A4 (210 × 297 mm)
- **Margins:** 15 mm (top, bottom, left, right)
- **Content Area:** 180 mm wide × 267 mm tall
- **Column Width:** (180 mm − 11 mm gutter space) ÷ 12 columns = **14.08 mm per column** (round to 14 mm)
- **Gutter Width:** (11 mm gutter space) ÷ 11 gutters = **1 mm per gutter** (standard).

In InDesign, navigate to **Layout > Margins and Columns**. Set:
- Columns: 12
- Gutter: 1 mm

In Affinity Publisher, go to **View > Guides > Create Grids**, and set:
- Columns: 12
- Gutter: 1 mm
- Margin: 15 mm (all sides)

Enable **View > Guides > Show Guides** (or press Ctrl+' or Cmd+' depending on your OS) to visualize the grid on your page.

### Part B: Mapping Content to Grid Units

The power of a grid system lies in its **modularity**. Instead of placing text and images arbitrarily, you place them in **multiples of grid units**. This creates visual order and alignment.

For your publication document, map each content block to grid columns:

- **Page Title (Artist Name):** Spans columns 2–11 (10 columns wide, centered), with 1-column margins on left and right.
- **Track List:** Spans columns 1–6 (left half of page, 6 columns wide) for track numbers and titles; spans columns 7–12 (right half of page, 6 columns wide) for durations.
- **Credits Section:** Spans columns 1–7 (left half, 7 columns) for contributor names; spans columns 8–12 (right half, 5 columns) for role descriptions, using a smaller font size.
- **Artist Statement:** Spans columns 2–11 (10 columns wide, centered), with 1-column margins.

Create a **visual grid overlay** by printing or exporting your page with the grid visible (most layout software allows **View > Show Frame Edges** or similar). Label each grid unit with its column number for reference.

### Part C: Multi-Page Document & Grid Consistency

Extend your catalogue to **4 pages** and verify that the grid aligns consistently across pages. Add a **header and footer** to reinforce visual continuity:

- **Header:** Publication title in 13 pt, Regular, centered. Positioned 5 mm below the top margin (inside the margin area, not in the content area).
- **Footer:** Page number in 13 pt, Regular, centered.

Positioned 5 mm below the top margin (inside the margin area, not in the content area).
- **Footer:** Page number in 13 pt, Regular, centered. Positioned 5 mm above the bottom margin.

Check that all text blocks and graphical elements align to the same grid boundaries across all four pages. Export each page as a PDF with grid overlays enabled, then compare them side-by-side. If any element drifts by more than 0.5 mm from its intended grid position, correct the frame anchor or margin settings. This process reveals **grid drift**, a common failure mode in multi-page layouts caused by inconsistent baseline grids or floating frame anchors. To prevent drift, lock all text frames to the master page grid and use **baseline grid alignment** (InDesign: Paragraph panel > Align to Baseline Grid; Affinity Publisher: Paragraph > Baseline Grid > Align to Grid). Verify that body text baselines snap to a consistent vertical rhythm—typically matching your leading value—so that facing pages align horizontally when viewed in spreads.

Grid systems succeed when they become **generative constraints** rather than restrictive templates. Once you internalize the relationship between column count, gutter width, and content hierarchy, you can make rapid, confident layout decisions without trial-and-error repositioning. The grid does not eliminate creative judgment; it accelerates it by encoding spatial logic into reusable infrastructure. Your final deliverable should demonstrate that every design choice—typeface pairing, hierarchy, spacing, alignment—traces back to measurable parameters defined in your grid specification. This makes your layout **auditable**: another designer could reconstruct your decisions from the grid alone.

## Summary & Verification Matrix

| **Invariant/Mechanism** | **Governing Principle** | **Diagnostic Criterion** | **Failure Mode** |
|---|---|---|---|
| **Grid Modularity** | All content blocks span whole-number multiples of column units; no arbitrary widths or offsets. | Measure any text frame width: it must equal `(n × column_width) + ((n-1) × gutter_width)` for integer `n`. | Content drifts between grid lines; alignment breaks across pages. |
| **Baseline Grid Alignment** | Body text baselines snap to a vertical grid with interval equal to leading value (e.g., 14 pt leading = 14 pt baseline grid). | Select body text and enable baseline grid view: every line's baseline should align to grid increments. Measure distance between baselines with a ruler tool. | Text baselines misalign in facing-page spreads; vertical rhythm is irregular. |
| **Hierarchical Span Differentiation** | Higher-hierarchy elements (titles, headings) span more columns than lower-hierarchy elements (captions, footnotes). | Compare column spans: title > subheading > body > caption. Span ratios should reflect typographic scale ratios. | Visual hierarchy is flat; reader cannot distinguish content importance by position. |
| **Cross-Page Grid Consistency** | Grid column boundaries and baseline grid remain fixed across all pages; margins and gutters do not shift. | Export pages with grid overlay; superimpose page 1 grid over pages 2–4 in image editor. Boundaries must coincide within ±0.5 mm. | Grid drift: elements on page 3 no longer align with page 1 structure; document appears inconsistent. |
| **Locked Frame Anchoring** | Text and image frames lock to master page grid; manual repositioning disabled or requires override confirmation. | Attempt to drag a text frame: software should snap to grid or require explicit unlock. Check frame properties for "Align to Grid" or "Lock to Master" status. | Frames float freely; accidental nudges break grid alignment; layout degrades over edit cycles. |
| **Gutter Preservation** | White space (gutters) between columns remains unoccupied; no content bleeds into gutter zones. | Highlight gutter areas and verify no text or graphic elements intersect them. Use software's "Check Overset Text" or collision detection. | Content crowds; readability suffers; grid structure becomes invisible to reader. |
