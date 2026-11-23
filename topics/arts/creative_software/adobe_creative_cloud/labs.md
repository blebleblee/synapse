# Studio Practice Labs: Adobe Creative Cloud

## Objective & Studio Setup

These labs treat Creative Cloud as one production pipeline rather than a set of separate programs. You will build a small brand kit for a fictional independent bakery: a vector logo in Illustrator, a textured poster in Photoshop, a one-page flyer in InDesign and a 10-second logo animation in After Effects. All four must stay connected to a single source logo, so that one change in Illustrator reaches every deliverable without redrawing anything.

The skill being trained is not any single tool. It is knowing **where each piece of work belongs** (vector, raster, layout, motion), and **how to link rather than copy** between applications.

**Software:** Illustrator, Photoshop, InDesign and After Effects, plus Adobe Media Encoder for the final render. Any current Creative Cloud release works; menu paths below are from recent versions.

**Hardware:** a monitor set to a known profile (sRGB is fine for screen work), 16 GB of RAM for running two or three of the applications at once, and optionally a pen tablet for the masking work.

**Before you start:**

1. Create a project folder with subfolders `01_logo`, `02_poster`, `03_flyer`, `04_motion`, `assets` and `exports`. Every file you place in another application must live inside this folder; links to files on the desktop break as soon as the project moves.
2. Put two or three of your own photographs in `assets` (bread, flour, a wooden table, at least 3000 px on the long side).
3. Unify colour settings: in Photoshop, choose *Edit → Color Settings* and pick *North America General Purpose 2* or *Europe General Purpose 3*, then apply the same preset in Illustrator and InDesign (or synchronise all three from Adobe Bridge with *Edit → Color Settings*). Mismatched settings are the most common reason colours shift between applications.
4. Create a Creative Cloud Library called `Bakery Brand` (*Window → Libraries*). Libraries are shared by all four applications and hold colours, character styles and graphics.

---

## Exercise 1: Observation & Fundamentals Drill

Before building the brand, practise the two operations every later step depends on: drawing clean vector paths and hiding pixels without destroying them.

**Part A: Efficient Bézier paths (Illustrator, 30 minutes)**

1. Create a 1000 × 1000 px document (*File → New → Web*), RGB.
2. Place a photo of a croissant or a wheat ear (*File → Place*), lower its opacity to 40% in the *Transparency* panel and lock its layer.
3. On a new layer, trace the outline with the **Pen tool (P)**. Place anchor points only where the curve changes direction (the extreme top, bottom, left and right of each bulge) and drag out handles instead of adding points. A good trace of a croissant needs about 12–20 anchors.
4. Check your work with *View → Outline* (Cmd/Ctrl+Y). Lumps and kinks show up as clusters of anchors; delete extras with the **Anchor Point delete tool (−)** and smooth with the **Direct Selection tool (A)**.
5. Draw the same shape a second time using the **Curvature tool (Shift+~)** and compare the anchor counts.

Self-check: zoom to 800%. A clean path has smooth curves at any zoom and no anchors in the middle of a straight run.

**Part B: Non-destructive masking (Photoshop, 30 minutes)**

1. Open one of your photos. Duplicate nothing and erase nothing.
2. Run *Select → Subject*, then refine the edge in *Select → Select and Mask* (use the *Refine Edge Brush* on the crust, where the selection is softest).
3. Output to *Layer Mask*. Paint on the mask with black (hide) and white (reveal) at 100% hardness for crisp edges and lower hardness for the crumbs.
4. Add a solid colour fill layer in bright red *below* the photo. Every gap in the mask now shows as red. Fix them, then delete the red layer.
5. Save as `assets/croissant_cutout.psd`.

Self-check: disable the mask (Shift-click its thumbnail). The original photo must be complete. If it is not, pixels were destroyed somewhere.

---

## Exercise 2: Technique Study, Step by Step

**Step 1: The source logo (Illustrator)**

1. Create `01_logo/bakery_logo.ai`: one artboard, 1000 × 1000 px, **RGB** (the logo will be used on screen and in a poster; the print flyer converts colours later in InDesign).
2. Build the mark from simple shapes: a circle and your croissant path from Exercise 1. Merge overlaps with the **Shape Builder tool (Shift+M)** or *Pathfinder → Unite*.
3. Set the wordmark (the bakery's name) in a typeface with a clear personality, then *Type → Create Outlines* on a **copy** kept on a hidden layer. Outlines guarantee the logo looks the same on a machine without the font; the hidden live-text copy lets you edit the name later.
4. Choose a palette of three colours. Add each to the `Bakery Brand` library as a colour swatch, and the finished mark as a library graphic.
5. Name the layers `mark`, `wordmark` and `wordmark_live (hidden)`. Layer names will become After Effects layer names in Step 4.

**Step 2: The poster (Photoshop)**

1. Create `02_poster/poster.psd` at A3 size (297 × 420 mm), 300 ppi, RGB.
2. Place your best photo as a background. Add a **Gradient Map** adjustment layer clipped to it (Alt/Option-click between the layers) using two colours from the library, so the photo takes on the brand palette. Lower the adjustment's opacity until the photo still reads as food.
3. Place the logo with *File → Place Linked* and choose `bakery_logo.ai`. The logo arrives as a **linked Smart Object**: it stays vector, scales without loss and updates when the `.ai` changes.
4. Give the logo a subtle *Drop Shadow* (layer style: opacity 25–35%, distance 6 px, size 12 px) so it separates from the photo without looking stuck on.
5. Test the link: in Illustrator, change one brand colour and save. In Photoshop, the *Layers* panel marks the Smart Object as modified; choose *Layer → Smart Objects → Update Modified Content*. The poster updates without re-placing anything.

**Step 3: The flyer (InDesign)**

1. Create `03_flyer/flyer.indd`: A5 portrait, 3 mm bleed on all sides, margins 12 mm.
2. Set up two **paragraph styles** (`Heading`, `Body`) and one **character style** (`Price`). Base them on a type scale: with body text at 10 pt and a ratio of 1.25 (a major third), the heading is 10 × 1.25³ ≈ 19.5 pt.
3. Place the logo (*File → Place*, `bakery_logo.ai`) and a photo from `assets`. InDesign links both by default; check the *Links* panel.
4. Write a short menu of five items with prices, using only your styles. No local formatting: if you need a different look, make a style.
5. Open *Window → Output → Separations Preview* and *Window → Output → Preflight*. Fix every error, then export with the *PDF/X-4* preset (*File → Export → Adobe PDF (Print)*), including the bleed (*Marks and Bleeds → Use Document Bleed Settings*).
6. Run *File → Package*. It collects the document, every linked file and the fonts into one folder: the habit that keeps print jobs from failing at the printer.

**Step 4: The logo animation (After Effects)**

1. Create `04_motion/logo_reveal.aep`.
2. *File → Import → File*, choose `bakery_logo.ai`, and set *Import As* to **Composition – Retain Layer Sizes**. Each Illustrator layer becomes an After Effects layer whose bounds fit its artwork, so its anchor point sits on the artwork instead of the centre of the artboard.
3. Open the composition settings: 1920 × 1080, 25 fps, 10 seconds. Scale the logo layers to fit.
4. Select the `mark` layer and choose *Layer → Create → Create Shapes from Vector Layer*. The resulting shape layer can be animated path by path. (Alternatively, keep the vector layer and turn on its **Continuously Rasterize** switch so it stays sharp when scaled above 100%.)
5. Animate:
   - **Entrance (0–1.5 s):** scale the mark from 0% to 100%. Select both keyframes and press **F9** (*Easy Ease*). Open the **Graph Editor**, switch to the speed graph and drag the incoming influence of the last keyframe to about 80%, so the mark decelerates hard and settles.
   - **Wordmark (1–2.5 s):** reveal it with a *Linear Wipe* effect animated from 100% to 0% completion, or with a rectangle mask whose path is keyframed.
   - **Hold (2.5–10 s):** add slight life with an expression on the mark's *Position*: Alt/Option-click the stopwatch and type `wiggle(0.5, 6)` (half a cycle per second, at most 6 px).
6. Enable **Motion Blur** for the animated layers and for the composition (the two switches must both be on).
7. Render: *Composition → Add to Adobe Media Encoder Queue*, choose the H.264 *Match Source – High bitrate* preset and export to `exports/logo_reveal.mp4`.

---

## Exercise 3: Finished Piece & Self-Critique

**Brief.** The bakery changes its main colour two days before the launch. Deliver an updated poster, flyer and animation, and prove that you changed the colour only once.

1. In Illustrator, change the main brand colour in `bakery_logo.ai` and update the library swatch. Save.
2. Update every deliverable *without re-placing or redrawing anything*:
   - Photoshop: *Update Modified Content* on the linked Smart Object; adjust the gradient map if it used the old colour.
   - InDesign: the *Links* panel shows the logo as modified; update it. Re-export the PDF/X-4 and re-package.
   - After Effects: the imported `.ai` composition updates when the project reopens (or choose *File → Reload Footage* on the source). The shape layer made in Step 4 does **not** update, because it was converted. Note how long the fix takes, and record which approach you would choose next time.
3. Export a contact sheet of all four results side by side (a new Photoshop or InDesign document with screenshots or exports) and write three sentences on what broke, if anything.

**Self-critique process.** Review each piece with these checks:

- **The squint test:** half-close your eyes or apply *Filter → Blur → Gaussian Blur* to a flattened copy. The logo and the headline should still be the first things you see.
- **The value check:** add a *Black & White* adjustment layer on top of the poster. If the logo disappears into the photo in greyscale, the contrast comes only from hue and will fail for many viewers.
- **The small-size test:** export the logo at 64 × 64 px. If the croissant becomes a blob, simplify the mark.
- **The motion audit:** step through the animation frame by frame (Page Up/Page Down). Any motion that moves at constant speed and stops abruptly needs easing.
- **The link audit:** open the *Links* panel in InDesign and *File → Dependencies → Find Missing Fonts / Missing Footage* in After Effects. Nothing may be missing or point outside the project folder.

---

## Critique Checklist & Common Fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Logo looks blurry in After Effects when scaled up | Vector layer rasterized at its import size | Turn on **Continuously Rasterize** for the layer, or convert to shape layers |
| Colours differ between Photoshop and InDesign | Different colour settings, or RGB artwork converted twice | Synchronise colour settings in Bridge; keep sources RGB and convert once, at PDF export |
| Logo in the poster does not update | Placed embedded (*File → Place Embedded*) instead of linked | Replace it with *File → Place Linked* |
| Printer reports missing fonts or images | Files outside the project folder, or no package | Keep links inside the project; send the output of *File → Package* |
| Animation feels mechanical | Linear keyframes | **F9** (Easy Ease), then shape the speed graph in the Graph Editor |
| Fast motion looks choppy | Motion blur enabled on the layer but not the composition (or the reverse) | Enable both switches |
| Flyer text styles are inconsistent | Local overrides on top of styles (a "+" after the style name) | Clear overrides; change the style, not the text |
| Cut-out has a halo of old background | Mask edge not refined | *Select and Mask* with *Decontaminate Colors*, or paint the mask edge by hand |
