# Operational Verification Labs: Digital Painting

## Objective & Studio Setup

Digital painting is the art of creating visual imagery through software-based brushwork, layering, color theory application, and compositional refinement. For the traditional artist or designer moving into digital painting—particularly one engaged in editorial illustration, concept art, or multimedia design—digital painting demands a disciplined workflow: precise tool mastery, systematic layer organization, critical *seeing*, and iterative refinement against reference materials and established principles of form, value, and color.

This operational verification lab sequence positions digital painting as a complementary creative discipline for visual artists and designers. Just as value studies reveal compositional structure through careful observation and critical analysis, digital painting develops understanding of form, light, and spatial relationships through layered mark-making and color temperature shifts. The hand-eye coordination developed through gesture drawing directly informs confident brushwork and expressive line quality; the understanding of atmospheric perspective mirrors the use of depth cues and color saturation in spatial composition.

### Required Software & Hardware Setup

**Primary Digital Painting Application:** Krita (open-source, professional-grade) or Clip Studio Paint (industry standard for illustration and animation).

**Supporting Diagnostic Tools:**
- **Color Picker & Palette Managers:** Built into Krita/Clip Studio; augment with Coolors.co for systematic palette generation.
- **Reference Display:** High-fidelity sRGB-calibrated monitor (27" minimum, 95% DCI-P3 or Adobe RGB for professional work). Calibrate using a hardware colorimeter (X-Rite i1Display Pro or Datacolor SpyderX Elite).
- **Input Devices:** Pressure-sensitive graphics tablet (Wacom Pro, XP-Pen, or Huion) with at least 8192 pressure levels. Alternatively, a display tablet (iPad with Apple Pencil, Wacom Cintiq) for direct on-screen brushwork.
- **Reference Library:** High-resolution image collection organized by composition type (portraiture, landscape, still life, abstraction), lighting setup (three-point studio, natural side-light, rim-light), and historical period or artistic movement.

**Workspace Organization:**
1. Launch your primary painting application and establish a standardized document template: 3000 × 4000 pixels at 300 DPI, sRGB color space, 16-bit depth (if available) for maximum tonal gradation.
2. Create a dedicated folder structure: `Projects/DigitalPainting/[ProjectName]/Source_Assets/`, `Ref_Images/`, `WIP_Exports/`, and `Finals/`.
3. Open a secondary reference window (Krita's Reference Docker or external tablet displaying references) at 25–50% screen real estate.
4. Set up a color palette JSON or palette file matching your intended mood: cool/warm dominance, saturation level (saturated vs. desaturated), and value range (high-key vs. low-key).

---

## Exercise 1: Foundational Value Studies & Gesture Blocking

### Conceptual Foundation

Before color enters the visual field, a painter must master *value*—the grayscale relationship between light and dark. Value is the most powerful compositional and atmospheric tool in visual arts; it reads at a distance before color registers. Thoughtful value distribution creates visual clarity and hierarchy, guiding the viewer's eye through the composition and establishing the structure that holds a painting together.

A gesture block is the rapid, intuitive placement of compositional masses without refinement of detail. This is analogous to blocking in basic values or laying down rough compositional scaffolding before resolving specific forms and details. The goal of this exercise is to develop perceptual accuracy, hand-eye coordination, and decision-making speed under time pressure—all essential for responsive visual practice.

### Lab Protocol: 30-Minute Value Study Sprint

**Setup:**
- Open Krita or Clip Studio Paint and create a new 2000 × 2000 pixel document at 300 DPI, sRGB, grayscale mode.
- Set your brush to a hard round or chalk brush at 100% hardness, 80–90% opacity. Disable pressure sensitivity for now.
- Load a reference image from your library—preferably a portrait with strong directional lighting (Rembrandt-style three-quarter lighting, or dramatic side-light).
- Use Krita's Reference Docker (Windows > Docking Dialogs > Reference) to pin the reference at 40% opacity on the right half of your screen.

**Execution Protocol:**

**Minutes 0–5: Proportional Blocking.** Squint at the reference image to eliminate mid-tone detail and perceive only the five major value zones: highlight (brightest whites), light (light grays), midtone (neutral gray), shadow (dark grays), and reflected shadow (darkest without pure black). Using a large brush (size 40–60 pixels), block in these five zones without concern for anatomical accuracy. Think of it as placing geometric masses of light and dark. Your goal is rapid spatial decision-making, not precision. Use only three tones: white (255), midtone (128), and black (0).

**Minutes 5–15: Secondary Form Definition.** Subdivide each major zone with secondary value distinctions. For a portrait, this means differentiating the forehead highlight from the cheekbone highlight, or the shadow on the jaw from the shadow in the eye socket. Introduce intermediate tones: 64 (dark shadow), 192 (light), etc. Work with a medium brush (20–30 pixels). The goal is to create a clear read of form without rendering. Your image should now resemble a five-value or seven-value grayscale study.

**Minutes 15–25: Edge Definition & Atmospheric Perspective.** Soften edges in the background and distance; sharpen edges in the focal point (typically the eyes in portraiture). Use a smaller brush (10–15 pixels) with a soft transition (70% hardness). If your reference is a landscape, create atmospheric depth by keeping background hills lighter and less detailed. If portraiture, darken the background behind the head to separate it from the light source direction. Adjust shadow-side values to recede slightly by moving them 5–10% toward the midtone.

**Minutes 25–30: Critical Review & Refinement.** Zoom to 100% view and examine your study against the reference. Toggle reference visibility on and off. Ask: Does the major light source direction read clearly? Are the highlight and shadow sides distinguishable at 3 feet distance? Is there atmospheric depth? Make three to five targeted refinements—typically darkening one shadow, lightening one highlight, or softening one edge.

**Verification Checklist:**
- [ ] All five value zones are visually distinct (measurable 15–20% difference between zones in histogram).
- [ ] Focal point (eyes for portraiture; main subject for landscape) has the sharpest edges and highest contrast.
- [ ] Background reads as receding (lighter, softer, less detailed than foreground).
- [ ] No muddy mid-grays dominating the image; clear separation between light and shadow sides.
- [ ] Gesture reads recognizably (portrait recognizable as human head; landscape as landscape) at 50% zoom.

**Repetition Protocol:** Complete four 30-minute sprints over four consecutive days, using four different reference images from contrasting genres: one portrait, one landscape, one still life, one architectural interior. By repetition four, your blocking speed should increase 40–50%, and your value choices should shift intuitively without conscious deliberation.

---

## Exercise 2: Color Theory Application & Palette Construction

### Conceptual Foundation

Color in digital painting operates through three simultaneous dimensions: *hue* (the color wheel position—red, yellow, green, blue, etc.), *saturation* (intensity of color versus gray), and *value* (lightness to darkness, independent of hue). The perceptual power of color rests not in saturation but in *temperature shift* and *saturation contrast*. A painter who understands that a shadow under a warm light source becomes cool (blue-shifted) will create far more luminous, believable work than one who simply darkens a color using the slider.

For the visual practitioner, color harmony operates through consistent principles: a highly saturated orange-red appears energetic and demands resolution in a cool shadow. Analogous color schemes (adjacent on the color wheel) feel unified and harmonious; complementary schemes feel tense and dynamic. Triadic schemes (three colors equidistant on the wheel) feel balanced and vibrant, creating visual rhythm through their spatial relationship on the wheel.

### Lab Protocol: Systematic Palette Construction & Application

**Part A: Palette Generation & Temperature Mapping (40 minutes)**

**Setup:**
- Create a new Krita document: 4000 × 3000 pixels, RGB color space, 16-bit depth.
- Open the Colors docking panel (Windows > Docking Dialogs > Colors).
- Open a web browser to Coolors.co or use Krita's built-in palette generation.

**Execution Protocol:**

**Step 1: Establish a Color Temperature Intention.** Decide whether your painting will be *warm-dominant* (reds, oranges, yellows dominating with cool accents) or *cool-dominant* (blues, cyans, purples with warm accents). For this exercise, choose warm-dominant. The psychological effect is intimacy, energy, and nostalgia.

**Step 2: Generate a Core Triad.** On Coolors.co, generate a triadic palette. Lock one color as your dominant hue—let's say a warm coral-orange (Hex: #E07856). The Coolors algorithm will suggest two complementary points. Accept this palette. You now have three primary color anchors.

**Step 3: Expand with Saturation & Value Variants.** For each of the three primary hues, create four variants:
- **Full saturation, light value:** 80% lightness, 100% saturation (accent, highlight).
- **Full saturation, midtone value:** 50% lightness, 100% saturation (primary local color).
- **Full saturation, dark value:** 20% lightness, 100% saturation (shadow side).
- **Desaturated, midtone value:** 50% lightness, 30% saturation (atmospheric transition, distant elements).

For coral-orange (#E07856 = HSV 10°, 54%, 88%), generate:
- Coral-light: HSV 10°, 100%, 95% = #FFEBDA (warm highlight)
- Coral-mid: HSV 10°, 100%, 75% = #E07856 (primary local color, matches original)
- Coral-dark: HSV 10°, 100%, 25% = #6B2410 (warm shadow)
- Coral-desaturated: HSV 10°, 25%, 55% = #8B6D63 (atmospheric mid-gray)

**Step 4: Temperature Shifting in Shadows.** This is the decisive move separating amateur from professional work. For each primary hue, shift the shadow version *toward blue* (opposite on the color wheel). If your coral shadow is HSV 10°, shift it to HSV 240° (blue) at 50% saturation and 25% value. This creates the effect of cool blue shadow under warm light—physically accurate (cool light reflecting into shadows) and psychologically luminous.

Warm coral with cool blue shadow:
- Coral-shadow-cool: HSV 240°, 50%, 25% = #0A0F1F (deep cool blue-black, not brown).

**Step 5: Save as Palette.** In Krita, export this nine-color palette (three hues × three saturation/value variants + one neutral) as a .gpl (GIMP Palette) file. Name it `Warm_Coral_Triad_Palette.gpl`. Store in your project folder.

**Verification Checklist:**
- [ ] All 9 colors are visually distinct in hue, saturation, or value.
- [ ] Each primary hue has a light, midtone, dark, and desaturated variant.
- [ ] Shadow colors are temperature-shifted (warm hues get cool shadows; cool hues get warm shadows).
- [ ] Palette loads correctly in Krita's color docker.
- [ ] Palette file is saved and accessible in project folder.

**Part B: Palette Application to Value Study (60 minutes)**

**Setup:**
- Open your best grayscale value study from Exercise 1.
- Flatten the image to a single layer (Image > Flatten).
- Convert to RGB color space (Image > Color Mode > RGB).
- Load your newly constructed palette into Krita's Docking Dialogs > Color Selector.

**Execution Protocol:**

**Step 1: Underpainting Layer.** Create a new layer below your value study called "Underpainting_Color." Set its blend mode to "Multiply" and opacity to 60%. Using a large soft brush (60–80 pixels, 40% opacity), block in the three primary hues from your palette across major zones: coral-mid for lit skin, cool blue shadow for shadow side, and a desaturated tan for background. Do not follow the value study precisely; instead, layer color intuitively over the grayscale forms. This creates a warm/cool dialogue that will enhance perceived depth.

**Step 2: Local Color Refinement.** Create a new layer called "Local_Color_Layer" above the underpainting. Using your palette, begin repainting over the value study with full local colors: coral-mid for lit cheekbones (if portrait), coral-light for highlights, coral-dark-cool for shadows. Use a medium hard brush (30–40 pixels, 80% opacity) with pressure sensitivity enabled. The pressure sensitivity controls opacity, allowing soft blending without lowering the brush opacity slider. Work methodically across the image, respecting the value structure but now expressing hue and saturation.

**Step 3: Saturation Modulation by Distance.** Elements in the background or mid-ground should use the desaturated variant of each hue (e.g., desaturated coral for background fabric instead of saturated coral). This creates atmospheric perspective—a psychological principle: distant objects appear less saturated due to atmospheric haze. Use the desaturated variants selectively: 30% of background elements, 10% of mid-ground, 0% of foreground focal point.

**Step 4: Temperature Contrast Accent.** In the most brightly lit area (typically the highlight on a portrait's cheekbone or forehead), introduce a tiny accent of the *complementary temperature*. If your primary scheme is warm coral, add a small stroke of cool blue or cyan at 20% opacity in the brightest highlight. This is called a "temperature accent" and creates vibrance by contrast—the visual equivalent of adding a bright harmonic overtone to a dull fundamental.

**Step 5: Edge Softening & Atmospheric Glaze.** Create a final layer called "Atmospheric_Glaze" above all previous layers. Set it to "Overlay" or "Soft Light" blend mode at 30% opacity. Using a very large soft brush (100+ pixels) and the desaturated variants of your palette, paint very light strokes of cool color over the background to enhance depth. If the overall image feels too saturated, add a layer of neutral gray (HSV 0°, 0%, 60%) at very low opacity to calm it.

**Verification Checklist:**
- [ ] All three primary hues from your palette are visibly present and distinguishable.
- [ ] Warm/cool temperature shift is evident between lit and shadow sides.
- [ ] Background is visibly more desaturated and receding than foreground.
- [ ] At least one temperature accent (complementary color) is visible in a highlight area.
- [ ] Value structure from Exercise 1 remains intact; color enhances rather than obscures form.
- [ ] Image reads as cohesive, with clear light source direction and atmospheric depth.

**Final Check:** Export as PNG at 300 DPI. Open in a second window and compare to your grayscale study. The value hierarchy should be identical; only hue and saturation should have changed. If values have shifted, you've made an error in layer blending or opacity—undo and recalibrate.

---

## Exercise 3: Rendering, Brushwork Mastery & Compositional Refinement

### Conceptual Foundation

Rendering is the final phase of image creation, where broad strokes crystallize into tactile surfaces, atmospheric effects, and focal point emphasis. In drawing, rendering locks line, composition, and value decisions, and refines them through line weight, hatching, and selective detail emphasis. In painting, rendering locks composition, color, and value decisions, and refines them through brushwork, texture application, and selective detail emphasis.

The principle of *differential rendering* states that focal points receive maximum detail and edge clarity; peripheral areas receive progressively less detail and softer edges. This mimics human visual attention and creates psychological hierarchy. In visual composition, this manifests through contrast and emphasis: the focal point receives the brightest color, sharpest focus, or largest form; supporting elements recede through desaturation, blur, or reduced scale.

### Lab Protocol: Detailed Rendering with Strategic Edge Control (120 minutes)

**Setup:**
- Open your color-applied study from Exercise 2.
- Set up a new three-layer stack: Background_Detail (bottom), Midground_Rendering (middle), Foreground_Focal_Point (top).
- Load brushes: Hard Round (100% hardness) for sharp details, Soft Round (20% hardness) for blending, and a specialty texture brush (chalk, oil impasto, or stipple) for surface variation.
- Pressure sensitivity must be ON, with pressure controlling opacity.

**Execution Protocol:**

**Phase 1: Background Rendering (25 minutes).** Select the Background_Detail layer. Using only the Soft Round brush at 30–40% base opacity (modified by pressure), apply diffuse, soft strokes with minimal detail. If this is a portrait with a background, suggest form with broad color washes and occasional soft edges. Avoid hard lines and sharp contrast. The goal is atmospheric recession—the viewer's eye should slide past the background without catching on detail. Paint with slow, deliberate strokes, allowing brush strokes to blend into one another. Do not use the eraser; instead, lower opacity or switch to a desaturated color to create subtle transitions.

**Phase 2: Midground Transition (25 minutes).** Move to the Midground_Rendering layer. This is where supporting forms live—secondary facial features if portrait, trees or architectural elements if landscape. Use a medium hard brush (60% hardness) at 60–70% opacity. Introduce slightly more edge definition than background but less than foreground. Paint approximately 40% of this layer with sharp strokes, 60% with soft transitions. If rendering a portrait, this phase handles ear structure, neck, and shoulder definition. Use a mix of local colors and slight temperature shifts (not as extreme as shadows, but slightly cooler than the lit side). Pressure sensitivity should modulate opacity significantly—light pressure yields 30% opacity strokes, full pressure yields 70% opacity.

**Phase 3: Focal Point Rendering (70 minutes).** Select the Foreground_Focal_Point layer. This is where mastery emerges. For a portrait, render the eyes, nose, and mouth with maximum precision and edge control. For a landscape, render the primary focal tree or architectural feature. 

Within this phase, apply the principle of *edge control hierarchy*:
- **Hard edges (100% opacity, full brush hardness):** Used only at the focal point's most critical boundary—the upper eyelid line in portraiture, the silhouette of a tree's leading branch in landscape. Approximately 10% of focal point edges.
- **Medium edges (70% opacity, 70% hardness):** Mid-priority forms and internal structures. The iris boundary, nostril definition, mouth corner shadow. Approximately 40% of edges.
- **Soft edges (40% opacity, 20% hardness):** Transitional areas, reflected light, and areas reading as atmospheric. Approximately 50% of edges.

Use the Hard Round brush for structure, the Soft Round for blending, and the texture brush for surface variation. For eyes in portraiture, apply this sequence:
1. Hard Round, 100% hardness, 90% opacity: Paint the iris circle with saturated color (typically cool blue, warm brown, or green depending on reference).
2. Soft Round, 30% hardness, 80% opacity: Blend the iris transition into the sclera (white of the eye).
3. Hard Round, 100% hardness, 60% opacity: Define the pupil as a small dark circle, leaving a tiny white catchlight (highlight reflection of light source).
4. Soft Round, 20% hardness, 40% opacity: Soften the upper eyelid shadow over the iris, creating depth.
5. Specialty texture brush (if available), 40% opacity: Add fine lashes along the upper eyelid using short, curved strokes pointing outward and downward.

This eye rendering typically requires 15–20 minutes per eye for professional-grade work.

**Phase 4: Atmospheric Effects & Depth Enhancement (varied timing).** Create a new layer called "Atmospheric_Effects" above all previous layers. Set blend mode to "Overlay" at 25% opacity. Using the Soft Round brush at 20% opacity:
- Paint cool blue slightly desaturated color into shadowed recesses to enhance cool-shadow perception.
- Paint warm light yellow or orange around primary light sources to suggest atmospheric glow.
- Add very subtle vertical strokes to suggest directional light rays if appropriate to the scene.

**Phase 5: Final Focal Point Emphasis.** To make the focal point magnetically draw the viewer's eye, apply one final refinement: increase contrast at the focal point by adding one or two small touches of near-white (95% value) highlight and near-black (5% value) shadow directly adjacent. This micro-contrast is psychologically powerful. In the eye, this means a bright catchlight and a dark pupil outline. In landscape, this means bright sky behind a dark tree silhouette.

**Verification Checklist:**
- [ ] Background is noticeably softer and less detailed than foreground; edges blur progressively with distance.
- [ ] Focal point (eyes for portrait, primary subject for landscape) has maximum edge sharpness and highest local contrast.
- [ ] Brushwork is evident and varied; not uniformly blended or airbrush-like.
- [ ] All three layers (background, midground, foreground) are visibly distinct in detail level and edge softness.
- [ ] Atmospheric effects (cool shadows, warm light) are subtle but perceptible.
- [ ] Pressure sensitivity responsiveness is evident; opacity varies naturally across brush strokes.
- [ ] Image reads as psychologically complete; focal point immediately draws attention.

**Export & Presentation:**
Export as 16-bit PNG at 300 DPI (maintains maximum color depth). Open in a secondary viewer (Adobe Lightroom, macOS Preview, Windows Photos) at 100% zoom to verify rendering clarity. If brush strokes appear muddy or over-blended, return to Clip Studio or Krita and add edge definition using the Hard Round brush at 70% hardness, 60% opacity, with quick deliberate strokes. Do not over-render; the goal is perceived skill and clarity, not photographic smoothness.

---

## Exercise 4: Compositional Structure Analysis & Iterative Refinement

### Conceptual Foundation

Composition is the arrangement of visual elements (forms, values, colors, lines) to guide viewer attention and create psychological meaning. The foundations of composition are universal across visual arts: hierarchy (some elements matter more than others), balance (asymmetrical or symmetrical equilibrium), rhythm (repetition with variation), and contrast (opposition creating visual tension and release).

For the visual artist, compositional analysis involves: Does the composition have a clear focal point (primary subject, dominant element) with supporting elements in secondary roles? Is the visual space balanced across the frame, or does one area dominate uncomfortably? Does the composition have variety in shapes, values, or movement, or is it repetitive? These are the fundamental questions of visual design.

### Lab Protocol: Compositional Structure Mapping (90 minutes)

**Part A: Rule of Thirds & Focal Point Placement (30 minutes)**

**Setup:**
- Open your rendered painting from Exercise 3.
- Create a new layer called "Compositional_Analysis_Overlay" above all content.
- In Krita, enable View > Guides > Image Guides and set to "Rule of Thirds" grid.
- This overlays nine rectangles across the image; the four intersection points are optimal focal point locations.

**Execution Protocol:**

**Step 1: Identify the Primary Focal Point.** Ask yourself: Where is my eye naturally drawn? In a portrait, typically the eyes. In a landscape, the most brightly lit or most saturated element. In a still life, the object with the highest contrast. Mark this point mentally or with a small crosshair using the Ellipse Select Tool.

**Step 2: Evaluate Placement Against Rule of Thirds.** Is the focal point positioned at one of the four intersection points of the Rule of Thirds grid, or on one of the dividing lines? If yes, your composition likely has natural appeal. If the focal point is centered or randomly placed, consider whether deliberate centering serves your intention (symmetrical, formal, meditative) or whether you should reposition.

**Step 3: Trace the Viewer's Eye Path.** Create mental connections between the focal point and supporting compositional elements.

Use directional lines (implied lines created by edges, gazes, or gesture) to trace how the viewer's eye moves from the focal point through the composition. In a portrait, the subject's gaze direction creates a vector; in a landscape, a river, road, or tree line creates a leading line. Mark these directional flows on your analysis overlay layer using the Brush Tool with a contrasting color (bright red or cyan at 50% opacity). Ask: Does the eye move in a predictable, controlled circuit through the composition, or does it exit the frame abruptly? Strong compositions create circular or triangular eye paths that keep the viewer engaged. If your eye path analysis reveals dead zones (regions the eye never visits) or exit vectors (lines that lead the viewer out of the frame without return), note these as compositional weaknesses requiring adjustment in future iterations.

**Step 4: Balance and Visual Weight Distribution.** Examine whether visual weight (determined by size, contrast, saturation, and detail density) is evenly distributed across the composition or heavily biased toward one region. A composition with all visual weight in the upper left quadrant will feel unbalanced unless countered by a subordinate element in the lower right. Use your analysis overlay to sketch circles representing visual weight centers. A well-balanced composition has 2-4 weight centers distributed across the frame, with the primary focal point commanding the strongest weight. If you find all weight concentrated in one region, plan compositional adjustments: introduce a secondary element, redistribute contrast, or adjust the crop to rebalance the frame.

**Part B: Contrast Mapping & Hierarchy Verification (30 minutes)**

Export your painting as a grayscale image (Layer > Convert to Grayscale) to isolate tonal contrast from chromatic complexity. Examine the grayscale version: Does the focal point exhibit the highest contrast (darkest dark against lightest light), or is contrast distributed evenly across the image? In classical composition, the area of highest contrast *must* coincide with the primary focal point. If you discover high contrast in peripheral regions, those regions will compete for attention, fragmenting the viewer's focus. Mark contrast hotspots on your analysis overlay and evaluate whether they support or undermine the intended hierarchy. Think of it as competing focal points in a composition: if two elements carry equal visual weight and sit at similar contrast levels, neither reads as dominant and the hierarchy collapses. Similarly, if two regions of a painting both exhibit maximum contrast, they cancel each other's impact.

**Part C: Compositional Armature Construction (30 minutes)**

Advanced compositions often rely on geometric armatures—underlying structural scaffolds such as the Golden Ratio spiral, Fibonacci grid, or dynamic symmetry diagonals. Overlay these grids (available as downloadable templates or constructible via the Path Tool) on your painting to assess whether major compositional elements align with the armature's organizing lines. Armature alignment is not mandatory, but when present, it produces compositions with subliminal coherence that viewers perceive as "rightness" without conscious awareness. Document which armature, if any, your composition approximates, and note whether future paintings might benefit from deliberate armature-based construction.

---

## Summary & Verification Matrix

| **Governing Invariant** | **Core Mechanism** | **Diagnostic Criterion** | **Failure Mode** |
|------------------------|-------------------|-------------------------|-----------------|
| **Focal Point Dominance** | Rule of Thirds placement + maximum local contrast establishes primary visual anchor | Focal point positioned at grid intersection *and* exhibits highest tonal contrast in grayscale | Focal point centered or low-contrast; viewer's eye wanders without anchor; composition feels diffuse |
| **Directional Flow Control** | Leading lines, gaze vectors, and edge trajectories create controlled eye movement circuits | Analysis overlay reveals closed-loop eye path; no exit vectors; all quadrants visited | Eye path exits frame or bypasses regions; dead zones present; composition feels incomplete or fragmented |
| **Visual Weight Distribution** | Size, contrast, saturation, and detail density determine perceived weight; balance requires distributed weight centers | 2-4 weight centers distributed across frame; primary weight coincides with focal point | All weight concentrated in single region; composition feels unbalanced or "tipped" |
| **Hierarchical Contrast** | Tonal contrast (grayscale delta) establishes visual priority; highest contrast = primary focus | Grayscale conversion confirms focal point has darkest-dark against lightest-light; subordinate elements exhibit reduced contrast | High contrast in peripheral regions competes with focal point; multiple contrast hotspots fragment attention |
| **Armature Coherence** | Geometric scaffolds (Golden Ratio, Fibonacci, dynamic symmetry) provide subliminal organizational structure | Major compositional elements align with armature lines; grid overlay reveals structural correspondence | Random element placement; no alignment with organizing grid; composition lacks subliminal coherence |
| **Chunked Writing Compliance** | Content exceeding 50 lines must be delivered via atomic chunked operations without commentary | All chunks executed as single uninterrupted sequence; no status updates between chunks | Truncated files, corruption, or user interruption between chunks; transport layer limits violated |
