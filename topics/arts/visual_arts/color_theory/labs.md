# Studio Practice Labs: Color Theory

## Objective & Studio Setup

Color theory is not an abstract intellectual pursuit. It is a mastery of observation, decision-making, and controlled execution that separates intentional color work from accidental harmony. These four studio labs train you to perceive color relationships in real light, translate those observations into digital or physical work, and develop the judgment to critique and refine your own output.

By the end of these labs, you will be able to: mix and match colors with predictable perceptual results; construct harmonies that sit in stable equilibrium across different saturation and value ranges; deploy color systems that solve real design and artistic problems; and critique color work using both metric and subjective frameworks that professional artists and designers use daily.

### Studio Setup Requirements

**For Traditional Media Work:**
- A well-lit studio or north-facing window (avoid direct sun, which shifts color temperature).
- Gouache, acrylic, or watercolor paint in at least the following palette: Titanium White, Ivory Black, Alizarin Crimson (or Quinacridone Magenta), Cadmium Yellow Light, Ultramarine Blue, Viridian Green.
- Mixing palettes (ceramic or glass, not plastic—plastic absorbs stains and distorts color judgment).
- Brushes ranging from #6 to #12 round for mixing and applying paint.
- Pre-cut paper or canvas in a standard size (9" × 12" or 10" × 10" works well for quick studies).
- A value scale swatch (a printed greyscale from white to black in 7–10 steps, 2" × 0.5" each). This is your constant reference.
- A grey viewing card (18% mid-grey, also called neutral grey or "photographer's grey"). Hold this near your work to judge if your colors are too saturated or value-distorted.
- Mirror or flip card to check composition symmetry and value distribution.

**For Digital Work:**
- Raster editor: Krita (free, open-source, superior color engine), GIMP, or Photoshop.
- Display: a monitor calibrated to sRGB or Adobe RGB. Uncalibrated displays are the fastest way to produce muddy, inaccurate color work.
- Reference images saved as high-resolution JPEGs or PNGs. Download from Unsplash, Pexels, or capture your own photographs.
- A digital value scale (provided below) and a screenshot-ready hex color picker or eyedropper tool built into your editor.
- Critique frame: open a second window or tablet showing the critique checklist (provided at the end).

**For All Work:**
- A notebook for recording color values, mixing ratios, and observations during each session.
- A timer (phone stopwatch works).
- Printed or digital versions of the exercises below.

---

## Exercise 1: Observation & Fundamentals Drill — Hue, Saturation, Value Mapping

### Context: What You Are Training

Before you mix or apply color, you must train your eye to decompose any color you see into its three perceptual dimensions: **hue** (the color family: red, blue, green, etc.), **saturation** (intensity or purity: vivid vs. muted), and **value** (brightness: light vs. dark). Professional colorists and painters work in this vocabulary constantly. A muddy painting is not "bad"—it is a *low-saturation* problem. A washed-out digital interface is not "pale"—it is a *high-value* problem. Training this decomposition is the foundation of intentional color work.

This drill spans two parallel tracks: **traditional media observation** and **digital HSV sampling**. Do both; they reinforce each other.

### Part A: Traditional Media — Observational Mixing and Value Ladder

**Duration: 45 minutes**

You will mix a single hue (Ultramarine Blue) through a full range of saturations and values, observing how pigment behaves under real light and how your eye judges relationships.

**Setup:**
1. Lay out your mixing palette in a horizontal line: Titanium White on one end, Ivory Black on the other. Leave the center two-thirds empty.
2. Place your pre-cut paper vertically in front of you.
3. Fill a container with clean water and place a paper towel to your right.

**Procedure:**

*Step 1: Establish the Pure Hue (5 minutes)*
Squeeze a dime-sized amount of Ultramarine Blue directly onto your palette. Using a #8 round brush, mix it thoroughly with a small amount of water until the consistency is creamy (not runny, not thick paste). Load your brush generously and paint a 2" × 1" rectangle in the top-left of your paper. Label it "Pure Hue (100% Saturation)." Rinse your brush thoroughly—pigment residue will contaminate the next mix.

*Step 2: Create a Desaturation Series (20 minutes)*
Now you will gradually desaturate the same blue by adding its **chromatic opposite**, which on the artist's color wheel is orange-yellow (approximated by Cadmium Yellow Light + Alizarin Crimson mixed on a separate area of the palette). This is not adding grey; you are using complementary color to lower saturation while preserving hue identity.

- In a clean area of the palette, mix a small amount of Ultramarine Blue with a tiny pinch of orange. Stir thoroughly for 10 seconds. Paint a 2" × 1" rectangle directly below the pure hue. Label it "75% Saturation (Desaturated with Complement)."
- Repeat with more orange added: 50% Saturation, 25% Saturation, and finally a nearly neutral grey-blue (5% Saturation). Create five rectangles in a vertical column.
- Step back 3 feet and squint. Notice how the colors feel as if they are receding into the background as saturation drops. This perceptual recession is intentional and usable in composition.

*Step 3: Create a Value Ladder (20 minutes)*
In a second column to the right of your desaturated series, you will adjust only value while keeping saturation relatively constant.

- Mix Ultramarine Blue at medium saturation (similar to your 50% Saturation swatch above, but freshly mixed so the saturation is consistent). Paint a 2" × 1" rectangle at the top. Label it "Mid-Value (5)."
- Add a tiny amount of Titanium White to the same blue and paint the next rectangle below. Label it "High-Value (6)."
- Continue adding white in small increments: (7), (8), and finally an almost-white tinted blue (9). These should form a clear gradient from your original blue down to nearly white.
- Now, without rinsing, take a clean area of the palette and mix your original blue with a touch of Ivory Black. Paint a rectangle labeled "Low-Value (4)." Continue darkening: (3), (2), and finally an almost-black blue (1).
- You now have a value scale in blue. Notice that as value increases, saturation appears to increase (Helmholtz illusion)—this is a perceptual bias, not a physical change.

**Observation Checkpoint (5 minutes):**
Let your paper dry for 2 minutes. Place your grey viewing card next to both columns. Does the viewing card help you judge which rectangles are truly "mid-value"? Which desaturated rectangle felt most uncomfortable to paint (too muddy to control)? Note your answers in your notebook.

**Deliverable:** A painted paper with a desaturation column and a value ladder in blue. Photograph or scan at high resolution (300 DPI minimum). Save as `Exercise_1A_Blue_Series.jpg`.

---

### Part B: Digital HSV Sampling and Critique

**Duration: 30 minutes**

You will deconstruct a reference photograph into hue, saturation, and value using digital tools, building a "color profile" of a real scene.

**Setup:**
1. Choose a reference image with clear color variety: a photograph of a street market, landscape, interior room, or still life. Save it to your computer at 72 DPI or higher.
2. Open Krita (or GIMP / Photoshop). Create a new document 1920 × 1080 pixels, 8-bit RGB, sRGB color space.
3. Import your reference image as a layer. Scale it to fit the left half of the canvas.

**Procedure:**

*Step 1: Hue Sampling (10 minutes)*

You will identify the dominant hue families in your reference and extract their HSV values.

- Activate the **Color Picker tool** (shortcut: `O` in Krita, `I` in Photoshop).
- In Krita, open the **Advanced Color Selector** (Window → Dockable Dialogs → Advanced Color Selector). Make sure the **HSV selector** mode is active (not RGB, not LAB).
- Click on a clearly saturated, warm-colored area in your reference image (e.g., a red fruit, yellow cloth, orange wall). The HSV values will appear in the dockable panel.
- Record the **H (Hue)** value as a degree (0–360). For example, if you sample a red apple, you might see H=355 (deep red), S=85 (high saturation), V=72 (mid-to-high brightness).
- Repeat for at least five distinct color families in the image: a warm hue (red/orange range), a cool hue (blue/purple range), a yellow, a green, and a neutral (grey or brown).
- Create a table in your notebook:

| Hue Family | H (°) | S (%) | V (%) | Perceived Role (foreground/background/accent) |
|-----------|-------|-------|-------|-----------------------------------------------|
| Red       | 355   | 85    | 72    | Main subject (foreground)                     |
| Blue      | 210   | 65    | 55    | Background, atmospheric                       |
| Yellow    | 42    | 78    | 88    | Highlight/accent                             |
| Green     | 125   | 42    | 50    | Foliage, receding                             |
| Neutral   | —     | 8     | 45    | Shadow, grounding                             |

*Step 2: Saturation and Value Relationships (10 minutes)*

Now you will visually test how saturation and value shift your perception of the scene's spatial depth and harmony.

- In your Krita canvas (right half), create a new layer called "Desaturated Study."
- Using **Colors → Hue/Saturation** (or Desaturate), reduce the saturation of your reference by 50%. Create a swatch showing both the original and 50%-desaturated version side by side.
- Repeat with **Colors → Brightness/Contrast**, increasing brightness by 20 and creating another swatch.
- Observe: Does the desaturated version feel more "background" or "atmospheric"? Does the brightened version feel closer to the viewer or washed out?

*Step 3: Value Compression Measurement (10 minutes)*

You will measure the actual value range in your reference image using histogram analysis.

- Open **Windows → Histogram** in Krita (or **Image → Mode → Levels** in GIMP).
- Look at the histogram: it shows the distribution of brightness values in your image. A histogram compressed into the mid-range (narrow, centered peak) indicates low contrast and muddy colors. A histogram spread across the full range (peaks near black and white) indicates good contrast and color clarity.
- If your histogram is compressed, note this as a "low-contrast" reference. If it spans the full range, note it as "high-contrast."
- Save a screenshot of the histogram and label it. This is diagnostic data you will reference in later exercises.

**Deliverable:** A digital canvas with your reference image, a desaturated study, and a brightness-adjusted study, all labeled. Export as `Exercise_1B_HSV_Analysis.psd` (or `.xcf` for GIMP, `.kra` for Krita) and also as a flattened JPEG `Exercise_1B_HSV_Analysis.jpg`. Include a photograph of your handwritten HSV table.

**Checkpoint:** Compare your two deliverables (traditional and digital). Did the colors you mixed in blue match the hue angles you sampled digitally? If red in your reference was H=355° (a cool red), and you painted Alizarin Crimson (which leans cool), was your perception accurate? Note any discrepancies. This is normal at first; it trains calibration.

---

## Exercise 2: Technique Study — Color Harmony Mixing and Composition Lock-In

### Context: What You Are Training

You now understand the three dimensions of color. This exercise moves you from isolated observation into **intentional composition**. You will work with established color harmony systems—analogous (neighboring hues), complementary (opposite hues), triadic (evenly spaced hues)—and deploy them to solve a specific visual problem: creating a coherent, emotionally resonant color environment that *works* without looking accidental.

The discipline here is rigor: you will plan your color before mixing or applying it, execute the plan with precision, and then critique whether the plan was correct or needs refinement. This is how professional colorists work in film, game design, and fine art.

### Part A: Triadic Harmony Study — Traditional Media

**Duration: 90 minutes**

You will create a small still-life painting using a triadic color harmony (three hues evenly spaced on the color wheel: 120° apart). This forces you to work with hues that do not naturally co-exist in many real objects, requiring intentional color mixing and saturation control.

**Setup:**
1. Arrange three simple objects on a neutral (grey or beige) surface under consistent light. Good objects: a lemon, a blue ceramic cup, a red tomato or bell pepper. If you do not have these, use colored paper cylinders or fabric swatches.
2. Lay out a fresh mixing palette with: Titanium White, Ivory Black, Cadmium Yellow Light, Ultramarine Blue, Alizarin Crimson, Cadmium Red, Viridian Green.
3. Pre-cut paper to 8" × 10" (or standard sketchbook page).
4. Place your grey viewing card and your value scale swatch within arm's reach.

**Planning Phase (15 minutes):**

Do not paint yet. You will design the color structure first.

- Choose your triadic triad. The most naturalistic triadic harmony for this exercise is: **Red (0°), Yellow (120°), Blue (240°)**. But you will use muted, slightly-desaturated versions so the harmony feels coherent, not garish.
- Plan your color assignments:
  - **Object 1 (foreground, focal point):** Cadmium Red, slightly desaturated with a touch of Viridian (which is cool and will mute the red). Value: mid (5–6).
  - **Object 2 (secondary interest):** Cadmium Yellow Light, desaturated with a small amount of Ultramarine (complement). Value: high (7–8), so it recedes slightly or reads as highlight.
  - **Object 3 (background anchor):** Ultramarine Blue, desaturated with a touch of Cadmium Yellow. Value: low (3–4), so it grounds the composition.
  - **Background/shadow:** A neutral grey (Ultramarine + Cadmium Yellow + White, heavily white-dominant) or a very desaturated version of one of the three hues.
- Sketch a small 4" × 5" thumbnail in pencil on your paper. Use hatching to indicate value zones (dark, mid, light). Do not worry about detail—this is a value map, not a portrait.

**Execution Phase (60 minutes):**

*Step 1: Establish the value structure (20 minutes)*

- Mix your mid-value red on the palette: Alizarin Crimson (or Cadmium Red) + tiny touch of Viridian + small amount of white. Test the mix on a scrap piece of paper. If it looks too purple, add more yellow. If it looks too brown, add white to lighten. You are aiming for a true mid-value red (value 5–6).
- Paint the red object using loose, gestural strokes. Do not blend or smooth; let the brush marks show. This is a study, not a finished painting.
- Repeat for the yellow: Cadmium Yellow Light + tiny touch of Ultramarine + white. Test on scrap paper. It should feel sunny but not neon.
- Repeat for the blue: Ultramarine + touch of Cadmium Yellow + white. It should feel calm, not aggressive.
- Do not paint the background yet. Step back and observe. Do the three hues sit in visual equilibrium, or does one jump forward or recede too far?

*Step 2: Saturate and refine (20 minutes)*

- If the red feels too muted, add a tiny amount of pure Alizarin Crimson (no white) to boost saturation. If the yellow feels muddy, add a touch of pure Cadmium Yellow.
- Paint a background wash using a heavily white-dominant grey (Ultramarine + Cadmium Yellow + White, ratios approximately 10% + 10% + 80%). Leave some white paper showing; this will read as reflected light or highlight.
- If you chose to desaturate one hue further, do that now: add a bit more of its complement (e.g., more Ultramarine to the yellow to make it feel olive or muted yellow-green).

*Step 3: Final value and edge check (20 minutes)*

- Using a mix of Ivory Black + Ultramarine (not pure black), deepen the shadow areas on the background or under the objects. These should be your lowest value (1–3).
- Soften or sharpen edges selectively: soft edges on areas that recede or feel ambient, sharper edges on the focal point (usually the red object).
- Compare to your value map. Are the light areas still light (value 7–9)? Are the dark areas distinct (value 1–3)? Do you have a mid-value zone that ties them together?

**Observation Checkpoint (10 minutes):**
Let the painting dry for 3 minutes. Hold it at arm's length and squint. Do the three hues feel like a unified harmony, or do they feel like three separate paintings? If the latter, what went wrong? (Common fix: the three hues are all at the same saturation and value, making them equal competitors instead of a coherent whole. Solution: drop the saturation of one or two, or raise/lower their value.)

**Deliverable:** A finished 8" × 10" painting using a triadic harmony. Photograph or scan at 300 DPI minimum. Save as `Exercise_2A_Triadic_Still_Life.jpg`. Include a photograph of your planning thumbnail and your mixing notes.

---

### Part B: Complementary Harmony Digital Study — Color Grading and Recoloring

**Duration: 60 minutes**

You will take a neutral photograph and recolor it using a **complementary harmony** (two opposite hues on the color wheel: 180° apart, e.g., red and cyan, yellow and blue). This teaches you how color harmony systems structure a scene and how to deploy saturation and value to make a harmony feel intentional, not random.

**Setup:**
1. Open Krita or Photoshop. Load a neutral reference photograph (black and white, or a desaturated color photograph). Good references: a landscape, street scene, or portrait. If you don't have one, download a sample photo from Unsplash in black and white.
2. Create a new layer called "Color Grading."
3. Have your HSV color selector visible (Advanced Color Selector in Krita, or use the Color Picker).

**Procedure:**

*Step 1: Choose your complementary pair (5 minutes)*

You will work with **Yellow (H=60°, warm) and Blue-Violet (H=240°, cool)**. This is a classic warm-cool complementary pairing used in film color grading and illustration.

- Assign Yellow to highlights and mid-lights (the lighter areas of your photograph).
- Assign Blue-Violet to shadows (the darker areas).
- This warm-cool contrast creates visual depth and emotional tension: yellow feels sunny and forward, blue-violet feels recessed and contemplative.

*Step 2: Create color overlays using Hue/Saturation adjustment layers (25 minutes)*

In Krita:
- Create a new layer above your reference. Set the blending mode to **Overlay** or **Soft Light**.
- Using the paint tool, mix a warm yellow (H=60, S=40, V=85—not fully saturated, but clearly yellow). Paint the lighter areas of your photograph: faces, sky, exposed surfaces.
- In a fresh area, mix a cool blue-violet (H=240, S=35, V=50—muted enough to feel like shadow, not neon). Paint the shadow areas: skin shadows, dark backgrounds, underside of objects.
- Lower the layer opacity to 50% if the colors feel too strong. Adjust as needed.

In Photoshop:
- Create a new adjustment layer: **Layer → New Adjustment Layer → Hue/Saturation**.
- In the Hue/Saturation dialog, target the **Yellows** channel and increase saturation by +20, then lower the lightness by –10.
- Create a second adjustment layer, target the **Blues** channel, increase saturation by +20, and lower lightness by –15 to push blues into shadows.
- Alternatively, use **Color Balance** (Colors → Color Balance): push Shadows toward Cyan, push Highlights toward Yellow. This is quicker and often more intuitive.

*Step 3: Refine and test (20 minutes)*

- If the yellow feels too bright or washed out, increase the saturation of the yellow channel slightly.
- If the blue-violet feels muddy, increase the saturation and lower the value (make it darker).
- Take a screenshot of your work. Place it next to your original reference. Does the complementary harmony feel intentional and cohesive, or jarring?
- Save your work as `Exercise_2B_Complementary_Recolor.psd` (or `.xcf`, `.kra`). Also export a flattened JPEG: `Exercise_2B_Complementary_Recolor.jpg`.

**Checkpoint:** Photograph both your traditional triadic painting (Exercise 2A) and your digital complementary recolor (Exercise 2B) in the same light. Do they feel like they belong to the same color-theory curriculum, or do they feel like different exercises? (They should feel related but distinct in approach: one is additive mixing and intuitive harmony, the other is analytical recoloring. Both are essential skills.)

---

## Exercise 3: Finished Piece & Self-Critique — Integrated Color Systems

### Context: What You Are Training

By now, you have mixed colors with intention, deployed harmony systems, and observed how saturation and value reshape perception. This final exercise brings everything together: you will create a **finished piece** (not a study or exercise) that integrates color science, perceptual systems, and harmony into a coherent visual statement. You will then critique your own work using rubrics that professional artists, designers, and art directors use to evaluate color work.

This is not about technical perfection. It is about demonstrating that you can make a color decision, execute it, and explain why it works (or diagnose why it doesn't).

### Part A: Create a Finished Piece — Free Choice, Guided by Constraints

**Duration: 2–3 hours (single session or split across two)**

You will create one finished artwork (painting, digital illustration, design mockup, or photograph) that demonstrates mastery of color harmony and intentionality. The subject is your choice, but the color structure must follow a specific system.

**Constraints (choose one):**

1. **Analogous Harmony with Accent (Recommended for beginners):** Use three consecutive hues on the color wheel (e.g., yellow, yellow-green, green) as your primary harmony, then introduce a single accent hue that is a secondary complementary (e.g., a small area of red-violet). This teaches restraint and intentional focal point deployment.

2. **Limited Palette Tetradic (Intermediate):** Choose four hues evenly spaced (90° apart: red, yellow, green, blue) but keep all four at low-to-mid saturation and limit value range to mid-tones (values 4–7 only). This is extremely difficult and teaches you that harmony is about relationships, not individual hues.

3. **Monochromatic with Accent (Advanced):** Use a single hue (e.g., blue) through a full range of saturations and values, then introduce a single pure-saturation accent in a complementary hue (yellow). This is how minimalist painters and graphic designers work.

**Setup:**

Choose your medium and subject:
- **Traditional media:** 11" × 14" canvas or paper, your preferred paint or drawing medium (acrylic, gouache, oil, watercolor, charcoal + fixative, colored pencil).
- **Digital:** 1920 × 1080 pixels, 8-bit RGB, sRGB. Subject: an illustration, graphic design composition, or digital painting (portrait, landscape, still life, abstract).
- **Hybrid:** Photograph a real scene (8" × 10" print or digital file), then paint or collage over it. This integrates real-world color observation with intentional intervention.

**Execution Roadmap (2–3 hours):**

*Phase 1: Planning (20 minutes)*
- Decide on your harmony system (analogous + accent, tetradic, or monochromatic + accent).
- Create a small thumbnail (2" × 3") in pencil or quick digital sketch. Label the hues, saturation levels, and value ranges you plan to use.
- Write a brief artist's statement (3–4 sentences): What is this piece about? What emotion or concept does the color harmony support? For example: "This landscape uses an analogous blue-green harmony to evoke calm and atmospheric depth, with a single warm-orange accent (sunset) to draw the eye and suggest time passing."
- Gather reference images if you are working from observation (landscape, portrait, still life, etc.).

*Phase 2: Underpainting or value structure (30–40 minutes)*
- Traditional: Use a single neutral or dark tone (burnt umber, ultramarine + burnt sienna) to block in the basic composition and value zones. This is your road map; it stays underneath and unifies the color work above.
- Digital: Create a greyscale value study layer, then add a new color layer above it and set the blending mode to Multiply or Overlay. This lets you see value and color simultaneously.

*Phase 3: Color application and harmony lock-in (60–80 minutes)*
- Mix your primary harmony colors (3–4 hues). Keep saturation consistent at first—do not let one hue dominate by being much more saturated than the others.
- Apply color to major shapes or zones. Work loosely; this is not a photorealistic render.
- Introduce saturation variation: drop the saturation of secondary or background areas, keep primary focal areas more saturated.
- If you are using an accent hue, apply it sparingly (no more than 5–10% of the visual area). Make sure it has good value contrast with its surroundings so it reads clearly.

*Phase 4: Final refinement and integration (30–40 minutes)*
- Zoom out (if digital) or step back 6 feet (if traditional). Squint to check value distribution and overall harmony.
- Use a mirror (traditional) or horizontal flip (digital) to check for compositional balance and symmetry bias.
- Sharpen edges on focal areas; soften edges on receding areas.
- If the harmony feels incomplete or jarring, do not abandon it. Instead, ask: Is one hue too saturated? Is the value range too compressed? Is the accent hue in the right location? Make a small, targeted adjustment rather than repainting.

**Checkpoint (10 minutes):**
Photograph or export your finished piece at high resolution (minimum 300 DPI for print, minimum 1920 × 1080 for digital). Save as `Exercise_3A_Finished_Piece_[Title].jpg` and also save your working file (`[Title].psd`, `.xcf`, `.kra`, or similar).

**Deliverable:** One finished artwork demonstrating a chosen color harmony system, plus the planning thumbnail and artist's statement.

---

### Part B: Self-Critique Using Rubric Framework

**Duration: 45 minutes**

You will evaluate your own finished piece using a structured rubric. This is not about judging yourself harshly; it is about developing the vocabulary and diagnostic eye that professional artists use to refine their work.

**Rubric: Color Harmony and Intentionality (100 points)**

Print this rubric or open it on a second screen. For each criterion, score your work from 1–5. Write a brief explanation (1–2 sentences) for each score, referencing specific areas of your piece.

| Criterion | 1–2 (Needs Work) | 3 (Developing) | 4 (Proficient) | 5 (Mastery) | Your Score | Explanation |
|-----------|-----------------|---|---|---|---|---|
| **Harmony System Clarity** Does the chosen harmony system (analogous, complementary, triadic, etc.) read clearly when you look at the work? Or do the hues feel random? | Hues feel unrelated or clashing. No clear harmony is evident. | One or two hues feel harmonious, but others feel discordant. The harmony is partially obscured. | The chosen harmony system is evident. All hues feel intentionally related. | The harmony feels inevitable. The hues belong together so naturally that it's hard to imagine them any other way. | ___ | ___ |
| **Saturation Control** Are saturations varied intentionally (e.g., focal areas more saturated, backgrounds desaturated), or are all hues equally saturated? | All hues are uniformly saturated or uniformly desaturated. No variation to guide the eye. | Saturation varies, but inconsistently. Some focal areas are under-saturated; some backgrounds are over-saturated. | Saturation is used strategically. Focal areas are more saturated; receding areas are muted. | Saturation creates a clear visual hierarchy and depth structure. The eye flows naturally from saturated to desaturated areas. | ___ | ___ |
| **Value Range and Contrast** Does the work use the full range of values (lights to darks), or is it compressed in the mid-tones? | Almost all values are mid-tone. Very little contrast between light and dark areas. | Some light and dark values exist, but the range is narrow. Mid-tones dominate. | A clear range from light (7–9) to dark (1–3) is present. Good contrast. | The full value range (1–10) is deployed deliberately. Each value zone serves a spatial or emotional purpose. | ___ | ___ |
| **Focal Point Clarity** Is there a clear focal point, or do multiple areas compete for attention equally? | No clear focal point. The eye wanders without direction. | A potential focal point exists, but it doesn't feel dominant. Other areas compete. | A clear focal point is established, usually through saturation, value, or color temperature contrast. | The focal point is unavoidable. Color, value, and composition all guide the eye there immediately. | ___ | ___ |
| **Color Temperature Strategy (Warm/Cool)** Do warm and cool hues feel balanced, or does one dominate arbitrarily? | Warm and cool colors feel unbalanced or unmotivated. Composition feels chaotic or emotionally incoherent. | Warm and cool hues are present but not clearly distinguished or balanced. | Warm (red, yellow, orange) and cool (blue, green, violet) hues feel intentionally balanced. The temperature shift supports composition or emotion. | Warm and cool are deployed as a primary compositional tool. Temperature shifts create spatial depth, emotional resonance, or narrative clarity. | ___ | ___ |
| **Technical Execution** Is the application of color smooth, controlled, and intentional, or does it feel labored or sloppy? | Clumsy application. Uneven coverage, muddy mixing, or lack of control. | Adequate application with some inconsistencies. Some areas show control; others feel uncertain. | Skilled application. Colors are mixed cleanly, applied deliberately, and blended or layered with control. | Masterful execution. Each brushstroke (or pixel) is purposeful and reveals skill. The technique is invisible; only the color and emotion remain. | ___ | ___ |

**Scoring Interpretation:**

- **Total 24–30:** Your work needs significant refinement. Revisit Exercise 1 and 2 to strengthen observation and harmony planning. Consider redoing the piece with clearer harmony constraints.
- **Total 31–40:** Your work shows developing skill. Identify the two criteria with the lowest scores and focus on those in your next piece.
- **Total 41–50:** Your work is proficient. You are ready to integrate color work into larger projects or explore more complex harmony systems.
- **Total 50+:** Your work demonstrates mastery. You have intentional control over color and can deploy harmony systems to achieve specific emotional and compositional goals.

**Specific Diagnostic Questions (Use if you score below 4 on any criterion):**

1. **Harmony feels random or discordant:** 
   - Action: Extract the HSV values of your three primary hues (using the color picker). Are they evenly spaced on the hue wheel (120° apart for triadic, 60° apart for analogous, 180° apart for complementary)? If not, your harmony is not mathematically pure; this is not wrong, but it explains why the harmony feels unstable. Decide: is this intentional (a deliberate off-harmony for emotional impact) or accidental (needs refinement)?

2. **Saturation feels uniform and muddy:**
   - Action: Desaturate your work (Colors → Desaturate). Look at the resulting greyscale. Can you still see distinct areas and focal points? If not, your saturation strategy is not working. Solution: identify your focal area, increase its saturation by 20–30%, and decrease background saturation by the same amount. The difference should be dramatic.

3. **Value range feels compressed:**
   - Action: Check your histogram. If it clusters in the mid-range, increase the darkest dark (add black to shadows) and the lightest light (preserve white highlights or increase brightness of light areas). Do not change mid-tones; adjust the extremes.

4. **Focal point competes with distracting areas:**
   - Action: Squint at your work. When you squint, do you still see the focal point immediately? If not, the focal point is not different enough in value or saturation from surrounding areas. Increase the contrast between focal point and surroundings.

---

## Critique Checklist & Common Fixes

### Quick Critique Before Submission (10 minutes)

Use this checklist to do a final pass on any color work before you consider it finished or submit it for feedback.

**Checklist:**

- [ ] **Hue check:** Hold your work at arm's length and name the three primary hues you see. Are they related (e.g., all warm, or analogous on the wheel)? Or do they feel random? If random, revisit your harmony system.

- [ ] **Saturation check:** Use a greyscale viewing card or take a black-and-white screenshot. Can you still see the main compositional structure in greyscale? If not, you are relying too heavily on color for structure; strengthen your value composition.

- [ ] **Value check:** Use a greyscale filter (traditional: view through a blue filter or B&W photo frame; digital: Desaturate or Black & White adjustment layer). Do you see a clear range from light to dark, or is everything mid-tone? If mid-tone dominated, deepen shadows and brighten highlights.

- [ ] **Focal point check:** Squint at your work from across the room. Where does your eye go first? Is it the intended focal point? If not, increase saturation or value contrast at the focal point.

- [ ] **Temperature check:** Identify the warmest area (highest saturation of red, yellow, or orange). Identify the coolest area (highest saturation of blue or green). Do these feel balanced, or does one dominate? If unbalanced, increase the saturation or area of the under-represented temperature.

- [ ] **Mirror/flip check (composition only, not color-specific):** Flip your work horizontally (mirror it). Does it still feel balanced and intentional? Or does the balance collapse? This reveals if you are accidentally relying on a compositional crutch (e.g., always putting the focal point in the right third).

---

### Common Color Problems and Fixes

#### Problem 1: "My colors look muddy or desaturated, even though I tried to use vibrant pigments."

**Diagnosis:** You are mixing too many hues together, or you are adding too much white.

**Fix:**
- Limit your palette to three primary hues + white + black. Do not mix more than two colors together on the palette.
- When lightening a color, add white in very small amounts (less than you think). Each addition of white reduces saturation significantly.
- If you are working digitally, check your color mode: are you in RGB or CMYK? CMYK has a narrower gamut; switch to RGB for vibrant color.
- In traditional media, choose pigments known for high saturation: Cadmium Yellow Light, Alizarin Crimson, Ultramarine Blue, Viridian Green. Avoid mixing Earth pigments (Burnt Sienna, Ochre) unless you intentionally want muted, warm tones.

#### Problem 2: "One hue dominates the composition and makes everything else feel dull."

**Diagnosis:** One hue is significantly more saturated than others, or your value distribution is uneven (too much of one value zone).

**Fix:**
- Lower the saturation of the dominant hue by mixing it with its complement.
- Alternatively, increase the saturation of the other hues to match it.
- Check value distribution: if one hue occupies too much of the mid-tone zone, it will visually dominate. Try shifting one of the other hues to a higher or lower value (brighter or darker).
- Use the accent color rule: limit any single hue to no more than 50% of the total visual area.

#### Problem 3: "My color harmony feels random, like I just threw colors together."

**Diagnosis:** Your hues are not related on the color wheel, or your saturation and value are so similar that there is no visual hierarchy to organize the hues.

**Fix:**
- Choose a harmony system and stick with it. Use a physical color wheel (online or printed). Analogous = three consecutive hues. Complementary = two opposite hues. Triadic = three hues 120° apart. Tetradic = four hues 90° apart.
- Once you have chosen your hues, vary their saturation and value deliberately. Make one or two hues more saturated than the others. Make one hue darker or lighter to establish hierarchy.
- If the harmony still feels chaotic, you may have chosen hues that are too far apart. Try shifting one hue by 20–30° on the wheel to bring it closer to its neighbors.

#### Problem 4: "My focal point is not drawing the eye."

**Diagnosis:** Your focal area is not different enough from surrounding areas in value or saturation, or it is too small to read clearly.

**Fix:**
- Increase the value contrast: make the focal area lighter or darker than surroundings by at least 2–3 value points (e.g., focal area = value 7, surrounding = value 4).
- Increase saturation contrast: make the focal area much more saturated than surroundings. If the focal area is green, make it a vivid lime green (high saturation), and make the background a muted sage green (low saturation).
- Sharpen edges: hard, crisp edges on the focal area; softer, blurred edges on receding areas.
- Increase size (if possible): a focal point that is too small will never read, no matter how saturated or contrasty it is.

#### Problem 5: "The color feels emotionally wrong for my subject."

**Diagnosis:** Your color temperature (warm/cool balance) or saturation level is not aligned with your intent.

**Fix:**
- Warm, saturated colors (red, yellow, orange) feel energetic, happy, or aggressive.
- Cool, saturated colors (blue, green, violet) feel calm, sad, or mysterious.
- Desaturated colors feel nostalgic, quiet, or aging.
- Bright, high-value colors feel optimistic or exposed.
- Dark, low-value colors feel ominous or intimate.
- Identify your emotional intent and choose temperature/saturation accordingly. If you want a joyful piece, shift your palette toward warm and saturated. If you want a contemplative piece, shift toward cool and desaturated.

#### Problem 6: "I mixed my colors on the palette and they look great, but once I apply them to the canvas/screen, they look different."

**Diagnosis:** You are observing **simultaneous contrast** (color perception shifts based on surrounding context) or you are applying too thin a layer, allowing the under-layer to shift the perceived hue.

**Fix:**
- Apply a thicker, more opaque layer. If the first coat is thin and translucent, it will mix optically with what is underneath.
- Test your mixed color on a scrap piece of the same paper/canvas type before applying to the final work.
- Remember: a color does not exist in isolation. It always sits next to other colors. A red you mixed looks different next to green than it does next to blue. This is not a mistake; it is a feature. Use it intentionally. If a color looks too dull in context, increase saturation or value contrast, or change its surroundings.

#### Problem 7: "My digital colors are vibrant on screen but look muddy when I print them."

**Diagnosis:** Color space mismatch. You are working in a color space (RGB, wide gamut) that cannot be accurately reproduced in print (CMYK, limited gamut).

**Fix:**
- If you are designing for print, work in CMYK color mode from the start (Image → Mode → CMYK in Photoshop). The colors will look more muted on screen, but they will print accurately.
- Alternatively, work in RGB but simulate the print output using soft proofing (View → Soft Proofing in Photoshop; select the CMYK profile you are printing to). This shows you what your colors will look like in print without changing your working file.
- For web/screen work, stay in RGB and use sRGB color space for consistency across devices.
- When unsure, increase saturation and contrast slightly in your digital file; printers always desaturate colors somewhat.

---

### Peer and Professional Critique Framework (For Group Sessions)

If you are sharing your work with other artists or instructors, use this framework to give and receive critique.

**Before critique, the artist states:**
- Intent: "This piece explores the calm of a winter morning using an analogous blue-green harmony with a single warm accent (amber light on snow)."
- Challenge: "I struggled with the saturation of the green trees—they felt simultaneously flat and aggressive."
- Question: "Does the focal point (the amber light) feel intentional, or does it feel like an error?"

**Critique responder focuses on:**

1. **Harmony observation:** "I see blue, blue-green, and green as your primary hues. The amber accent reads clearly. The harmony feels stable and intentional."

2. **Technical observation:** "Your saturation strategy is working—the trees are more desaturated than I expected, which makes them recede nicely. The flatness you felt might be a value issue, not saturation. The trees are all mid-value; if you darkened them or added a lighter version, they'd feel more three-dimensional."

3. **Emotional response:** "The piece feels contemplative and serene. The amber accent created a sense of hope or warmth emerging from the cool environment. It worked emotionally."

4. **Actionable suggestion:** "If you revisit this, try shifting the green trees slightly toward blue-green (add more blue to your mix) to tighten the harmony even more. The current green is slightly yellow-tinted, which is beautiful but technically off from your stated analogous system."

5. **Question back:** "What if you increased the value range? Make the darkest shadows nearly black, and the lightest highlights nearly white. Do you think that would solve the flatness without changing saturation?"

---

## Closing: Integration and Next Steps

You have now completed a full cycle of color observation, mixing, harmony planning, and critique. You understand how hue, saturation, and value work in concert; how to mix intentional colors in physical media; how to analyze color relationships in digital tools; and how to critique your own work using rubrics that professionals use.

**Moving forward:**

- **Repeat these exercises with different harmony systems.** Do another triadic study with different hues (e.g., green, violet, orange). Do another complementary recolor with a different temperature pairing (e.g., red and cyan instead of yellow and blue).

- **Integrate color into your ongoing artistic practice.** Before you start any painting or design, spend 10 minutes planning the color harmony on paper. Write the HSV values or mixing ratios. This one habit—planning before executing—will raise the intentionality of everything you make.

- **Study color in the world.** Photograph well-lit scenes (sunsets, markets, interior rooms). Extract their color values using a color picker. Build a personal library of natural color harmonies. Notice which harmonies feel most emotionally resonant to you.

- **Push saturation and value intentionally.** Beginners often play it safe with muted, mid-tone color. Push yourself: create a piece using only saturated, high-chroma hues. Create another using only desaturated, grey-influenced colors. Create another using extreme value contrast (mostly black and white with one saturated accent). These experiments will deepen your intuition.

- **Learn color in context.** Take a formal course in color theory or color in design. Read *Interaction of Color* by Josef Albers (the exercises in this book are excellent). Study paintings and designs you admire and extract their color systems using your tools.

Color mastery is not a destination; it is a continuous practice of observation, decision-making, and refinement. These exercises are your foundation. Build on them.

---

## Appendix: Digital Color Reference Values

### Standard Color Wheel Hues (HSV)

| Hue Name | H (°) | Standard Saturation (%) | Standard Value (%) |
|----------|-------|------------------------|-------------------|
| Red | 0 | 100 | 100 |
| Orange | 30 | 100 | 100 |
| Yellow | 60 | 100 | 100 |
| Yellow-Green | 90 | 100 | 100 |
| Green | 120 | 100 | 100 |
| Cyan | 180 | 100 | 100 |
| Blue | 240 | 100 | 100 |
| Violet | 270 | 100 | 100 |
| Magenta/Red-Violet | 300 | 100 | 100 |

### Common Harmony Hue Pairs (H angles)

| Harmony Type | Hue 1 | Hue 2 | Hue 3 | Hue 4 |
|--------------|-------|-------|-------|-------|
| **Analogous** (3 hues, 60° apart) | 0° (Red) | 60° (Yellow) | 120° (Green) | — |
| **Complementary** (2 hues, 180° apart) | 0° (Red) | 180° (Cyan) | — | — |
| **Triadic** (3 hues, 120° apart) | 0° (Red) | 120° (Green) | 240° (Blue) | — |
| **Tetradic/Square** (4 hues, 90° apart) | 0° (Red) | 90° (Yellow-Green) | 180° (Cyan) | 270° (Violet) |
| **Split-Complementary** (3 hues: main + two adjacent to complement) | 0° (Red) | 150° (Blue-Green) | 210° (Blue-Violet) | — |

### Desaturation Formula (Traditional Media)

To lower the saturation of any hue, mix it with its **chromatic opposite**:

| Hue | Opposite (Complement) |
|-----|---------------------------|
| Red (0°) | Cyan (180°) or Viridian Green + Ultramarine Blue |
| Yellow (60°) | Blue-Violet (240°) or Ultramarine Blue + Alizarin Crimson |
| Green (120°) | Magenta/Red-Violet (300°) or Alizarin Crimson + Cadmium Red |
| Blue (240°) | Orange (30°) or Cadmium Yellow Light + Cadmium Red |

**Desaturation ratio:** Start with 90% primary hue + 10% complement. Mix thoroughly. Test on scrap paper. If still too saturated, increase complement to 15–20%. If the mixture turns grey or muddy, you have added too much complement; switch back to adding white.

---

**End of Studio Practice Labs: Color Theory**
