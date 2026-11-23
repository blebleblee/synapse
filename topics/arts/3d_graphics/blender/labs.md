# Studio Practice Labs: Blender Modeling Shading and Cycles Rendering

## Objective & Studio Setup

The Studio Practice Labs guide teaches you to model with topological rigor, shade with physically-based material workflows, and render with Cycles using correct light transport and sampling strategy. By the end of these labs, you will have built a coherent, production-ready asset from raw geometry through final render—understanding every decision in the topology, the material node graph, and the rendering parameters that control visual fidelity.

This guide assumes you are working in Blender 4.0 or later, with Cycles rendering engine active. You will work at screen resolution 1920×1080 or higher, and you will keep reference images visible during modeling and shading work. Have a colour picker tool (such as Krita's pipette, GIMP's color picker, or the native system eyedropper) available for capturing real-world colour values from your references.

Your studio setup should include:

- **Blender workspace** with the 3D Viewport, Shader Editor, and Compositor visible simultaneously (save this as a custom workspace).
- **Reference images** organized in a folder: at least three orthographic views (front, side, top) and one perspective photograph of your subject.
- **A printed or second-monitor histogram and colour wheel** for quick reference during shading work.
- **A critique rubric** printed or pinned to your workspace (provided at the end of this guide).
- **Lighting reference** (a photograph of the same object under known lighting conditions, or a 32-bit EXR environment map).

Before you begin, create a new Blender file and set your render engine to **Cycles** (Render Properties > Render Engine > Cycles). Set the render device to **GPU Compute** if available on your hardware; otherwise, **CPU** is acceptable. Configure your Cycles sampling: start with 128 samples for viewport preview and 512 samples for final renders. Enable **Adaptive Sampling** in the Sampling panel (Noise Threshold: 0.01) to accelerate convergence.

---

## Exercise 1: Observation & Fundamentals Drill — Orthographic Modeling from Reference

### Objective

You will block out a simple organic form (a ceramic mug, a stone, or a piece of fruit) using reference images locked in orthographic view. The goal is to develop topological discipline: understanding edge flow, loop density, and polygon count constraints before subdivision. You will not shade or render in this exercise; you will only model and critique the wireframe.

### Part 1A: Reference Setup and Blocking

Open your reference images in Blender using **Image Editor** or **UV Editor**. If your reference is a single photograph, decompose it into orthographic projections by opening the image in a graphics editor (Krita or GIMP) and manually cropping front, side, and top views. Save each as a 2048×2048 PNG with consistent perspective scaling. For example, if your subject is a mug that is 100 mm tall in reality, measure the pixel height on each orthographic view and calculate the scale factor: **mm per pixel** = **100 / pixel_height_at_ref_view**.

Import these images into Blender as reference objects: in the **Properties Panel** (N-key), navigate to **Scene Properties**. Under **Background Images**, click **Add Background Image**. Load your front-view orthographic reference and set its **Offset Y** to 0, **Offset X** to 0, **Scale** to 1.0. Enable **Flip X** if necessary to match your viewport's handedness. Repeat for side and top views, assigning each to its corresponding orthographic camera view using the **Camera** selector in the Background Image properties.

Switch to **Camera > Front Orthographic** view (Numpad 1 for front, Numpad 7 for top, Numpad 3 for side). Your reference image should now fill the viewport. Lock all three orthographic views to your reference images using the **Lock Camera to View** toggle (Numpad /), then disable this toggle so you can orbit freely but your background remains fixed.

Add a new cube to the scene (Shift+A > Mesh > Cube). In Object Mode, scale it uniformly to rough-match your subject's bounding box. For a mug approximately 100 mm tall, 80 mm wide, and 80 mm deep, scale the default cube to X: 0.8, Y: 1.0, Z: 0.8 (using the Scale tool, S-key, then X/Y/Z-axis constraint). Do not worry about precise fit at this stage; you are establishing proportional relationships only.

Enter **Edit Mode** (Tab). Press **A** to select all vertices. Subdivide the cube coarsely using **Edge > Subdivide** (right-click > Subdivide, or Mesh > Edge > Subdivide). In the Subdivide panel, set **Number of Cuts** to 2. This creates 27 vertices (3×3×3) on a subdivided cube—enough to begin shaping. Press **Tab** to exit, then apply a **Subdivision Surface** modifier to preview smooth geometry. In the **Modifiers Panel**, click **Add Modifier > Subdivision Surface**. Set **Viewport Levels** to 2 and **Render Levels** to 3. Do not apply the modifier yet; leave it in the stack for non-destructive editing.

### Part 1B: Orthographic Silhouette Blocking

Return to **Front Orthographic** view. Scale the front face of your subdivided cube to match the silhouette width of your reference mug. Select the front-facing vertices and scale them (S-key) to fit the mug's outline at the reference image. Repeat for the **Side Orthographic** view, scaling the side face to match the mug's side-view profile.

Now enter **Top Orthographic** view. Scale the top face to match the mug's top-down footprint. The mug is now boxed in by orthographic silhouettes on three planes.

Add detail loops for the mug's handle. In **Front View**, rotate your model 90 degrees around the Y-axis (R-key > Y > 90), then add a loop cut on the right edge using **Edge > Loop Cut and Slide** (Ctrl+R). Position this loop about 20% inward from the right edge. Add a second loop cut 10% further inward. These two loops will define the outer and inner edges of the handle's thickness. Do not rotate back; keep the model in its current orientation for now.

Select all vertices (A-key) and apply a **Smooth** operation (Mesh > Smooth > Smooth Vertex, or right-click > Smooth). Set **Repeat** to 2 and click **OK**. This smooths the orthographic blocking into a rounded form without losing silhouette fidelity.

### Part 1C: Wireframe Critique and Loop Validation

Switch to **Wireframe** viewport shading mode (Z-key > Wireframe, or the wireframe shading icon in the top-right of the 3D Viewport). Inspect the topology of your model from multiple angles (Numpad 7 for top, Numpad 1 for front, Numpad 3 for side, and free rotation with middle-mouse drag).

Check the following **topological rules**:

1. **Quad Flow**: All faces should be quads (four-sided), never triangles or n-gons. Count the number of triangles (tris) using the **Statistics** overlay. Enable this in the top-right corner: **Viewport Overlays > Statistics**. Your tri count should be zero.

2. **Edge Loops**: All major features (the mug's rim, the transition from body to base, the handle attachment points) should be surrounded by clean edge loops that flow perpendicular to the feature direction. For the mug's body, horizontal loops should run around the circumference; vertical loops should run top-to-bottom.

3. **Vertex Density**: Count the vertices on a feature like the mug's rim. You should have 8–16 vertices around a circular form to capture smooth curvature with the Subdivision Surface modifier. Fewer vertices (4–6) will produce a faceted appearance; more than 24 will waste computational resources.

4. **Pole Avoidance**: A pole is a vertex where more or fewer than four edges meet (e.g., a vertex with 5 or 3 edges). Poles create pinching artefacts in subdivision. In your mug model, the top rim should have poles only at the handle attachment points (which is acceptable). Everywhere else, every vertex should have exactly four edges. If you see poles in the body or base, delete vertices or merge edges to restore quad flow.

Rotate the model in the viewport and visually inspect for poles. If you spot one, select that vertex (Alt+click on a face, or select the vertex directly), then delete it using **X > Merge** or by collapsing nearby edges.

### Part 1D: Finishing and File Save

Apply a **Bevel** modifier after the Subdivision Surface modifier to add realistic edge hardness. Click **Add Modifier > Bevel** in the Modifiers panel. Set **Width** to 0.2 mm (a very small value; Blender's default unit is millimeters). Set **Segments** to 2 (fewer segments for hard edges, more for soft transitions). Enable **Clamp Overlap** to prevent intersecting geometry.

In **Solid** shading mode (Z-key > Solid), your mug should now appear as a smooth, beveled form. The silhouette in front and side views should match your reference images within 5% error.

Save your file as `mug_model_exercise1.blend` in your project folder. Use **File > Save As**.

### Part 1E: Self-Critique Checklist

Before moving to Exercise 2, answer these questions:

- **Silhouette fidelity**: Does the front-view outline match your reference within 5%? Does the side-view outline match? Mark any areas where the model deviates more than 5% and note whether the error is in scale, proportions, or feature placement.
- **Topology correctness**: Is the wireframe all quads? Are there zero triangles (confirmed by Statistics overlay)?
- **Loop density**: Are feature edges (rim, base transition, handle) surrounded by appropriate loop counts (8–16 for circular features, 4–8 for linear features)?
- **Pole locations**: Are poles restricted to intentional attachment points (e.g., handle base)?
- **Modifier stack**: Does the Bevel modifier make the edges look realistic, or do they appear too soft or too hard? Note the Width value you used.

If any answer is "no" or uncertain, return to Edit Mode and correct the issue before proceeding.

---

## Exercise 2: Technique Study, Step by Step — PBR Shading and Material Workflow

### Objective

You will now shade the mug with a physically-based rendering (PBR) workflow using Cycles. You will capture real-world material properties (albedo, roughness, metallic, normal map), build a node graph in the Shader Editor, and render a preview under controlled lighting. The goal is to understand the relationship between material parameters, light transport, and perceived surface quality.

### Part 2A: Reference Material Capture and Analysis

Photograph or find a high-resolution image of your mug's material under neutral lighting (a 6500K LED panel works well). Open this image in a colour picker tool (Krita's Color Picker, GIMP's Eyedropper, or macOS Digitalcolor Meter). Sample three representative areas:

1. **Mid-tone lit area**: The brightest flat surface facing the light source.
2. **Shadow area**: A region in soft shadow, away from direct illumination.
3. **Specular highlight**: The brightest point where the light source reflects off the surface.

For each area, record the **RGB values** (0–255 scale) and convert to Blender's **sRGB linear scale** (0.0–1.0) by dividing by 255 and applying sRGB-to-linear conversion: **linear = sRGB ^ 2.2**. For example, if your mid-tone lit area reads RGB(180, 175, 170) in sRGB, convert as: **R = (180/255)^2.2 = 0.42**, **G = (175/255)^2.2 = 0.40**, **B = (170/255)^2.2 = 0.39**.

Estimate the material's **roughness** by observing the specular highlight:
- **Sharp, tight highlight** (smaller than 10% of the lit surface): Roughness ≈ 0.1–0.2 (polished ceramic or gloss paint).
- **Moderate, diffuse highlight** (15–40% of the lit surface): Roughness ≈ 0.3–0.5 (matte ceramic, unpolished metal).
- **Very broad, almost imperceptible highlight**: Roughness ≈ 0.6–1.0 (clay, unfinished wood, heavily weathered surfaces).

For a typical ceramic mug, roughness is usually 0.4–0.6 (semi-matte).

Estimate **metallic** value:
- **Non-metallic** (ceramic, plastic, rubber, wood, stone): Metallic = 0.0.
- **Metallic** (steel, aluminium, copper, gold): Metallic = 1.0.

For your ceramic mug, Metallic = 0.0 unless it has a metal handle or trim.

### Part 2B: Normal Map Generation and Displacement

If your reference image is a single photograph, you can generate a **normal map** using an AI-driven tool (Nomad Sculpt's baking, Marmoset Toolbag's texture generation, or free alternatives like Normal Map Online). Alternatively, if your model's topology is clean and your geometry captures surface detail (scratches, dimples, texture), you can skip a separate normal map and rely on **geometry-based normals** from your topology.

For a ceramic mug with a simple glaze, skip the normal map initially (Metallic = 0.0, Normal Map = None). The Subdivision Surface modifier and Bevel modifier provide sufficient geometric detail. If your mug has a textured surface (e.g., speckled ceramic, embossed logo), you can add a **Bump Map** or **Displacement Map** in the Shader Editor after shading the base material.

### Part 2C: Shader Editor Setup and Material Node Graph

Open the **Shader Editor** window (top menu: **Window > Toggle Sidebar**, then in the new window, **Editor Type > Shader Editor**). Ensure your mug object is selected in the 3D Viewport. In the Shader Editor, you should see the default **Principled BSDF** shader (if not, click **New** to create a material slot, then add a Principled BSDF node).

The **Principled BSDF** is Blender's unified physically-based shader. It accepts the following inputs (from top to bottom):

- **Base Color**: The diffuse colour of the material (the sRGB linear values you calculated above).
- **Subsurface**: For translucent materials (wax, skin, marble); for ceramic, leave this at 0.0.
- **Subsurface Radius**: Only relevant if Subsurface > 0.
- **Subsurface IOR**: Only relevant if Subsurface > 0.
- **Metallic**: 0.0 for ceramic, 1.0 for metal.
- **Specular**: Controls the intensity of the specular reflection on non-metallic surfaces. For most ceramics, 0.5 is a good starting point.
- **Specular Tint**: Colour cast on specular highlights. For neutral ceramic, leave at 0.0.
- **Roughness**: The roughness value you estimated (0.4–0.6 for ceramic).
- **Anisotropic**: Directional surface scratches (like brushed metal or satin fabric). For smooth ceramic, 0.0.
- **Normal**: Plugs in a normal map or bump texture (optional).

Set the following values on your Principled BSDF for a ceramic mug:

1. **Base Color**: Input the sRGB-linear RGB values you sampled. Click the Base Color swatch, enter the RGB values in decimal (0.0–1.0 scale). Use the colour picker icon to paste hex values if you converted them first. Example: mid-tone grey ceramic = RGB(0.42, 0.40, 0.39).

2. **Metallic**: 0.0 (ceramic is non-metallic).

3. **Specular**: 0.5 (ceramic has moderate specularity).

4. **Roughness**: 0.45 (semi-matte ceramic glaze).

5. **Normal**: Leave unplugged for now. We will add a bump map only if the model's geometry doesn't capture sufficient detail.

Connect the **Principled BSDF** output (the green "BSDF" port on the right) to the **Material Output** node's **Surface** input. If no Material Output node exists, click **Add > Output > Material Output** in the Shader Editor (Shift+A).

Your node graph should now look like this (in ASCII representation):

```text
Principled BSDF node:
  Base Color: RGB(0.42, 0.40, 0.39)
  Metallic: 0.0
  Specular: 0.5
  Roughness: 0.45
  [green BSDF output] ──→ Material Output [Surface input]
```

### Part 2D: Lighting Setup and Viewport Rendering

Switch to the 3D Viewport. Press **Z > Rendered** to enable real-time Cycles rendering in the viewport. You should see your mug rendered in a neutral grey environment with one default light.

Replace the default lighting with a 3-point studio setup. Delete the default light (select it in the Outliner or the viewport, press X > Delete). Add three light sources:

1. **Key Light (Main)**: Add a light using **Shift+A > Light > Sun**. Position it 45 degrees above and to the front-left of your mug (use the Gizmo or G > X/Y/Z to position). Set **Energy** to 2.0 (Watts in Blender's physical units). This is your main illumination.

2. **Fill Light**: Add a second Sun light. Position it 30 degrees above and to the right of your mug, at a 90-degree angle to the key light. Set **Energy** to 1.0. This fills in shadows created by the key light.

3. **Back Light**: Add a third Sun light. Position it behind and slightly above your mug at 45 degrees. Set **Energy** to 0.8. This separates the mug from the background and adds rim lighting.

Render a preview frame by pressing **F12** (or **Render > Render Image** in the top menu). The render window opens showing a full 1920×1080 render at 512 samples (or your configured sample count). Wait for convergence (usually 10–30 seconds on a GPU). Examine the result:

- **Is the mug visible?** (Color bleeding or pitch-black indicates lighting or shader issues.)
- **Are the highlights in the right places?** (Specular highlights should appear on the top rim and the front facing surface.)
- **Is the colour correct?** (Does it match your reference material sample?)
- **Are there obvious noise or fireflies?** (Bright, isolated pixels indicate insufficient sampling or extreme parameter values.)

If the render is completely black or clipped, check that your Cycles **Render Settings > Light Paths > Max Bounces** is set to at least 8 (default is usually correct). Check that your Sun lights have **Energy > 0** and are not rotated 180 degrees (pointing away from the scene).

### Part 2E: Roughness and Specular Refinement

Examine the specular highlight on the rendered mug. If it appears too sharp and small (like polished glass), increase **Roughness** to 0.55–0.65. If it appears too broad and washed out (like chalk), decrease **Roughness** to 0.25–0.35. Adjust in increments of 0.05, then render again.

Similarly, adjust **Specular** to control the intensity of reflections:
- **Specular = 0.3**: Very matte, almost no visible highlight.
- **Specular = 0.5**: Moderate, typical ceramic or plastic.
- **Specular = 0.8**: Highly reflective, polished enamel or gloss paint.

For ceramic, Specular between 0.4 and 0.6 is typical. Test by rendering and comparing to your reference photograph.

### Part 2F: Base Colour Fine-Tuning

If your rendered mug's colour appears too saturated or desaturated compared to your reference, adjust the **Base Color**'s saturation in the node graph. In the Shader Editor, insert a **Hue/Saturation** node between the Base Color colour input and the Principled BSDF's Base Color input:

1. In the Shader Editor, click **Add > Input > ColorRamp** (not Hue/Saturation; Blender's naming varies). No, use **Add > Color > Hue/Saturation** if available, or use **Add > Vector > Curves** for finer control.

Actually, the simplest approach is to modify the colour directly in the **Base Color** swatch. Click the swatch and use the **Saturation** slider in the colour picker to desaturate or saturate the base colour.

Alternatively, insert a **Hue Saturation** node:

1. In the Shader Editor, Shift+A > Input > Hue Saturation. Nope, there is no Hue Saturation input node. Use **Shift+A > Color > Hue Saturation** to add it to the graph.

2. Connect your Base Color source to the **Color** input of the Hue Saturation node.

3. Connect the **Color** output of the Hue Saturation node to the Principled BSDF's **Base Color** input.

4. Adjust the **Saturation** slider on the Hue Saturation node (range: -1.0 to 1.0; 0.0 is neutral, negative desaturates, positive oversaturates).

For most ceramics, Saturation should remain at 0.0 (neutral) or adjusted slightly (±0.1) for warmth.

### Part 2G: Final Shading Critique and Save

Render a final frame at 512 samples. Compare it to your reference photograph side-by-side. Use the **Colour Picker** tool (K-key in Blender's viewport) to sample the rendered colour and compare RGB values. Render errors greater than 15% in any channel (R, G, or B) indicate a need for further adjustment.

Document your final shader parameters in a text file:

```text
Ceramic Mug - Material Parameters:
Base Color: RGB(0.42, 0.40, 0.39) [sRGB-linear]
Metallic: 0.0
Specular: 0.5
Roughness: 0.45
Normal Map: None
Subsurface: 0.0
Lighting:
  - Key Light (Sun): Energy 2.0, Position (45°, 0°) [azimuth, elevation]
  - Fill Light (Sun): Energy 1.0, Position (315°, 30°)
  - Back Light (Sun): Energy 0.8, Position (225°, 45°)
Render Settings:
  - Samples: 512
  - Max Bounces: 8
  - Adaptive Sampling: Enabled (Noise Threshold 0.01)
```

Save your file as `mug_model_exercise2.blend`.

---

## Exercise 3: Finished Piece & Self-Critique — Multi-Pass Render Composition

### Objective

You will now produce a final, high-quality render of your shaded mug using Blender's **Cryptomatte** and **Render Passes** system. You will decompose the render into separate layers (diffuse, specular, shadow, emission, etc.), then composite them in the Compositor to produce a final image with enhanced contrast, colour grading, and visual appeal. This workflow mirrors professional studio rendering.

### Part 3A: Render Pass Configuration and Cryptomatte

In the **Render Properties** panel (camera icon on the right), scroll to **Passes** and enable the following:

1. **Diffuse** (Diffuse Color): Captures indirect and direct diffuse illumination.
2. **Specular** (Specular Color): Captures mirror-like reflections and highlights.
3. **Shadow**: Captures shadows cast by objects.
4. **Ambient Occlusion** (if using; optional for ceramic on a plain background): Adds contact shadows.
5. **Normal**: Captures world-space normals for compositing tricks.
6. **Cryptomatte Object**: Enables object ID passes for selective editing.

Also enable **Denoising Data** if you are using NVIDIA's OptiX denoiser (most GPU-accelerated systems):

1. In Render Properties, scroll to **Denoising** and enable **Use OptiX Denoiser** (if your GPU supports NVIDIA Optix; otherwise, skip).

### Part 3B: Compositor Setup and Pass Routing

Open the **Compositor** workspace (**Blender > Top Menu > Compositor**). Enable **Use Nodes** (top-right, checkbox next to "Use Nodes"). You should see default **Render Layers** and **Composite** nodes.

The **Render Layers** node outputs all render passes. The **Composite** node is the final output. You will now construct a node tree to mix the passes and add color grading.

Add the following nodes (Shift+A in the Compositor):

1. **Color Ramp** node: Maps raw pass values to displayable brightness. Shift+A > Converter > ColorRamp.
2. **Mix RGB** node: Blends multiple passes. Shift+A > Color > Mix RGB (or **Mix** if using Blender 3.2+).
3. **Curves** node: Advanced colour grading. Shift+A > Color > Curves.
4. **Bright/Contrast** node: Quick contrast boost. Shift+A > Color > Bright/Contrast.

Connect the nodes in this order:

```text
Render Layers
  [Diffuse] ──→ Mix RGB (Factor: 0.7)
  [Specular] ──┘
                    ↓
                  Curves (adjust RGB curves)
                    ↓
              Bright/Contrast (Contrast: +20)
                    ↓
                 Composite [Image input]
```

Specifically:

1. Connect **Render Layers > Diffuse** to **Mix RGB > Color1**.
2. Connect **Render Layers > Specular** to **Mix RGB > Color2**.
3. Set **Mix RGB > Factor** (blending between the two) to 0.7 (70% diffuse, 30% specular).
4. Connect **Mix RGB > Result** to **Curves > Image input**.
5. In **Curves**, click the diagonal line to add control points. Add one point at the lower-left (shadows) and raise it slightly to brighten shadows (adds fill from the fill light). Add another point in the midtones (center) and ensure it stays on the diagonal. Add a third point at the upper-right (highlights) and pull it down very slightly to prevent blown highlights. The curve should resemble a gentle S-shape.
6. Connect **Curves > Image** to **Bright/Contrast > Image**.
7. Set **Bright/Contrast > Contrast** to 20 (increases midtone separation).
8. Connect **Bright/Contrast > Image** to **Composite > Image**.

### Part 3C: Render and Composite

In the 3D Viewport, press **F12** to render a full image. Wait for convergence (512 samples at GPU speed typically completes in 15–60 seconds). Once rendering completes, the Compositor automatically composites the passes and displays the result in the Compositor's preview window.

If the Compositor window is not visible, open **Image Editor** and select the **Composite** result from the image dropdown (top-left of the Image Editor). You should now see your composited mug with enhanced contrast and colour-graded shadows.

### Part 3D: Cryptomatte Object Matte and Selective Rendering

To isolate the mug from the background, use **Cryptomatte Object** to create a matte. In the Compositor:

1. Add **Cryptomatte Object** node: Shift+A > Input > Cryptomatte.
2. Add **Mix** node (Mix RGB or Compositor Mix): Shift+A > Color > Mix.
3. Add a **Viewer** node to preview: Shift+A > Output > Viewer.

Connect:

```text
Render Layers [Image] ──→ Viewer (temporary preview)
Render Layers [Cryptomatte Object] ──→ Cryptomatte Object node
Cryptomatte Object [Matte] ──→ Mix [Factor]
Cryptomatte Object [Matte] ──→ Mix [Color1 / Color2 as background]
```

In the **Cryptomatte Object** node, enable **Pick** (the eyedropper icon). Click on the mug in the preview to select it. The Cryptomatte node now outputs a binary matte (white where the mug is, black elsewhere).

This matte can be used for:

- **Background removal**: Route the matte to a **Mix** node to composite the mug over a solid background or external image.
- **Shadow pass isolation**: Route the matte to a **Mix** to invert shadows under the mug only.

For now, leave this as a preview; you will use it in Exercise 4 if needed.

### Part 3E: Final Render Output and File Export

Once you are satisfied with the composite, render the final image at **1920 × 1080** and **768 samples** (double your preview sampling for final quality). Configure this in **Render Properties**:

- **Resolution X**: 1920
- **Resolution Y**: 1080
- **Samples** (Cycles > Sampling): 768
- **Adaptive Sampling**: Enabled (Noise Threshold: 0.005, tighter than preview)

Press **F12** to render. This will take 1–3 minutes on a modern GPU, or 10–20 minutes on CPU.

Once rendering completes, save the result as an **EXR** file (preserves 16-bit or 32-bit precision and all passes). Click **Image > Save As** in the top menu. Choose the **OpenEXR** format and save as `mug_render_final.exr`.

Also export a **PNG** for quick viewing and critique: **Image > Save As**, choose **PNG**, save as `mug_render_final.png`. This PNG is your submission-ready image.

### Part 3F: Rendered Mug Documentation

Create a final critique document with the following sections:

**Render Specifications:**
```text
File: mug_render_final.png
Resolution: 1920 × 1080 pixels
Render Engine: Cycles
Samples: 768
Denoising: OptiX Denoiser enabled
Render Time: [insert actual time in minutes/hours]
```

**Material Parameters (Final):**
```text
Base Color: RGB(0.42, 0.40, 0.39)
Metallic: 0.0
Specular: 0.5
Roughness: 0.45
Subsurface: 0.0
Normal Map: None
```

**Lighting Setup:**
```text
Key Light: Sun, Energy 2.0, Rotation (X: 45°, Z: 0°)
Fill Light: Sun, Energy 1.0, Rotation (X: 30°, Z: 90°)
Back Light: Sun, Energy 0.8, Rotation (X: 45°, Z: 225°)
World Background: Default Grey (1.0, 1.0, 1.0) or custom HDRI
```

**Compositing Passes Used:**
- Diffuse (70% weight)
- Specular (30% weight)
- Curves adjustment: Custom S-curve for shadow lift and highlight compression
- Contrast boost: +20 in Bright/Contrast node

Save this document as `mug_render_critique.txt` alongside your PNG and EXR files.

---

## Critique Checklist & Common Fixes

Use this checklist to evaluate your finished rendered mug and diagnose rendering or shading problems.

### Visual Quality Checklist

**1. Colour Accuracy (Target: RGB error < 10% per channel)**

- **Problem**: Rendered mug is too dark, too bright, too saturated, or too desaturated.
- **Diagnosis**: Compare your rendered RGB to your reference photograph using a colour picker. Sample the same location (e.g., mid-tone front face) on both images.
- **Fixes**:
  - If too dark overall: Increase Sun light **Energy** values by 20% (e.g., 2.0 → 2.4). Check that **World Strength** (World Properties) is not set to 0.
  - If too bright overall: Decrease Sun light **Energy** by 20%. Check that **Adaptive Sampling > Noise Threshold** is not too high (should be ≤ 0.01).
  - If too saturated (colours look hot or vivid): Decrease **Base Color Saturation** by 0.1 in the Hue/Saturation node, or manually desaturate the **Base Color** in the colour picker.
  - If too desaturated (colours look grey or muddy): Increase **Base Color Saturation** by 0.1, or boost the **Specular** value to 0.6–0.7 to increase highlight brightness.

**2. Specular Highlight Quality (Target: Sharp, single highlight per light source)**

- **Problem**: Specular highlights are missing, too soft, too hard, or doubled.
- **Diagnosis**: Render at 512+ samples and inspect the highlight on the rendered image. A proper ceramic mug should show one primary highlight on the top rim and a secondary, dimmer highlight on the front face.
- **Fixes**:
  - If highlight is missing or very dim: Increase **Specular** to 0.6 or 0.7. Check that your key light **Energy** is > 1.5.
  - If highlight is too soft or broad: Decrease **Roughness** to 0.3–0.4. This tightens the highlight.
  - If highlight is too hard and glassy: Increase **Roughness** to 0.5–0.65. This softens the highlight.
  - If there are multiple sharp highlights or a halo: Your render **Sample** count is too low, causing fireflies (bright noise). Increase to 768 or 1024 samples. Enable **OptiX Denoiser** to suppress noise.

**3. Shadow Quality (Target: Soft shadows with realistic gradation)**

- **Problem**: Shadows are harsh, unrealistic, or too dark; or shadows are non-existent.
- **Diagnosis**: Render and examine the base of the mug where it meets the background. Shadows should be soft and gradual, fading from dark to light over a 10–20 pixel gradient.
- **Fixes**:
  - If shadows are non-existent: Add a **Fill Light** (a second Sun with lower energy, positioned opposite the key light). Set fill light **Energy** to 0.8–1.0.
  - If shadows are too harsh and sharp: Sun lights in Blender produce infinitely sharp shadows by default. Enable **Shadow > Angle** on the Sun light (a small non-zero angle softens shadows). Set **Angle** to 0.5°–2.0° to simulate the sun's angular size.
  - If shadows are too dark: Increase the **Fill Light Energy** or add a **World Background HDRI** to provide ambient illumination.
  - If shadows wash out (too light and lack contrast): Increase **Key Light Energy** and reduce **Fill Light Energy** ratio.

**4. Geometry and Silhouette (Target: Smooth curves, no faceting or pinching)**

- **Problem**: Mug edges are faceted, pinched, or lumpy; silhouette does not match reference.
- **Diagnosis**: Render at any sample count and visually inspect the outline. Enable **Wireframe** overlay in the viewport (Z > Wireframe) to check topology.
- **Fixes**:
  - If edges are faceted (visible polygons): Increase **Subdivision Surface > Viewport Levels** from 2 to 3 (or **Render Levels** from 3 to 4). This adds more subdivision iterations.
  - If edges are pinched or creased unexpectedly: Check for **poles** in the topology (vertices with 3 or 5+ edges). Return to Edit Mode, select the problem vertex, and delete or merge it to restore quad flow.
  - If silhouette deviates from reference: Return to Exercise 1; your block-out was inaccurate. Re-scale vertices to match orthographic views.

**5. Noise and Convergence (Target: Clean image with zero visible noise at 768 samples)**

- **Problem**: Render shows obvious speckled noise, bright fireflies, or colour artefacts.
- **Diagnosis**: This is a sampling issue. Render at 128 samples and visually compare to 768 samples. If 768 samples still looks noisy, the issue is likely light path problems or extreme parameter values.
- **Fixes**:
  - Standard noise (speckled grain across the image): This is normal at low sample counts. Increase **Samples** to 768 or higher. Enable **Adaptive Sampling** (**Noise Threshold: 0.005**) to focus samples on difficult areas.
  - Fireflies (bright, isolated pixels): Usually caused by extreme specular values or very weak bounce paths. Reduce **Specular** to 0.4–0.5. Check that all light **Energy** values are ≤ 2.0 and ≥ 0.5. If using an HDRI, ensure its **Strength** is not > 2.0.
  - Denoising artefacts (blurry or banding after denoising): Disable **OptiX Denoiser** and render with more samples instead. OptiX can cause false smoothing.

### Material & Shading Checklist

**6. Base Colour Accuracy (Target: RGB delta < 5% per channel vs. reference)**

- **Problem**: Mug colour does not match reference photograph.
- **Diagnosis**: Use colour picker to sample both rendered and reference images at the same location (e.g., mid-tone front face). Calculate RGB delta: **|(rendered_R - reference_R) / reference_R|**.
- **Fixes**:
  - If delta > 5% in any channel: Directly edit the **Base Color** swatch in the Principled BSDF. Click the colour and manually input the reference RGB value (converted to 0.0–1.0 range).
  - If the entire image is too red/green/blue: This indicates a **colour space mismatch**. Ensure your Blender **Colour Management** is set to **sRGB** or **Linear** consistently (Render Properties > Colour Management).

**7. Metallic / Non-Metallic Rendering (Target: Metallic = 0.0 for ceramic, 1.0 for metal, appropriate reflections)**

- **Problem**: Ceramic mug looks like plastic or metal; metal parts look flat.
- **Diagnosis**: Render and inspect reflectivity. A non-metallic ceramic should reflect the environment only dimly (mostly on edges and specular highlights). A metallic surface should reflect the environment brightly.
- **Fixes**:
  - If ceramic looks too shiny (metal-like): Reduce **Metallic** to 0.0 (ensure it is exactly 0.0, not a low value like 0.1). Increase **Roughness** to 0.5–0.6.
  - If ceramic looks too matte (no specular): Increase **Specular** to 0.5–0.7. Render at 512+ samples to ensure convergence.
  - If metal parts look dull: Set **Metallic** to 1.0 and **Roughness** to 0.1–0.3 (polished metal) or 0.4–0.6 (brushed metal).

**8. Normal Map / Displacement (Target: Surface detail without obvious seams or stretching)**

- **Problem**: Normal map causes banding, faceting, or unrealistic surface normals; displacement causes geometry intersections.
- **Diagnosis**: If you used a normal map or displacement, render and inspect for obvious texture tiling, seams, or unnatural normal directions.
- **Fixes**:
  - If using normal map: Ensure it is in **OpenGL** or **DirectX** format (not Vulkan). Blender expects OpenGL by default. If normals point inward, multiply the normal map's green channel by –1 in a **Curves** node.
  - If using displacement: Increase **Subdivision Surface > Render Levels** to 4 or 5 to provide geometry for displacement to deform. Displacement requires fine geometry; a coarse mesh will show blocky artifacts.
  - If texture seams are visible: Use **UV > Seam** in Edit Mode to mark UV seam boundaries, then **UV > Unwrap** to minimize stretching. Align seams to hidden areas (e.g., the mug's back or bottom).

### Lighting & Compositing Checklist

**9. Light Positioning and Ratio (Target: Key:Fill:Back = 2.0:1.0:0.8 or similar, appropriate shadows and highlights)**

- **Problem**: Lighting looks flat, one-sided, or overly dramatic.
- **Diagnosis**: Render and examine the lit side, shadow side, and rim lighting. The key light should illuminate about 60–70% of the mug's visible surface; the fill light should softly light the shadow side; the back light should separate the mug from the background.
- **Fixes**:
  - If the mug looks flat (no depth): Increase the key light **Energy** and reduce the fill light **Energy** to widen the light/shadow ratio. Try Key: 2.5, Fill: 0.8, Back: 0.6.
  - If the shadow side is too bright (no contrast): Reduce fill light **Energy** to 0.5 or even 0.3.
  - If rim lighting is absent: Increase back light **Energy** to 1.0–1.2 and ensure it is positioned behind and to the side of the mug.
  - If highlight placement is wrong (appearing on the wrong face): Rotate the key light. Use the **Gizmo** (R-key > X/Y/Z axis) to adjust its angle precisely.

**10. Composite Node Graph (Target: Smooth colour transitions, no banding, appropriate contrast)**

- **Problem**: Composited image is too dark, blown out, banded, or oversaturated after compositing.
- **Diagnosis**: Disable compositing temporarily (uncheck **Use Nodes** in the Compositor) and render to see the raw result. Compare the composite output to this raw result.
- **Fixes**:
  - If composite is too dark: Check the **Bright/Contrast > Bright** value (should be 0 or slightly positive, e.g., +5 to +10). Reduce the **Mix RGB > Factor** weighting if specular is dominating (set Factor closer to 0.9 to favour diffuse).
  - If composite is blown out: Reduce the **Bright/Contrast > Bright** value or the **Curves** highlights (pull the top-right control point down).
  - If banding is visible (posterized transitions): Render at higher sample counts (1024+) and ensure your **Colour Depth** output is **8-bit RGB** at minimum (or 16-bit if exporting as EXR). Banding often indicates insufficient bit depth in the output format.

---

## Extended Studio Practice: Multi-Object Scene

Once you have completed Exercises 1–3 with the mug, extend your practice by modeling and shading a second object (a plate, a wooden spoon, or a glass). Follow the same workflow:

1. **Orthographic modeling** using reference images and topology discipline.
2. **PBR material setup** with captured RGB, roughness, and metallic values.
3. **Lighting and rendering** with a consistent 3-point setup.
4. **Compositing** to produce a final render.

Arrange the two objects together in a single scene, adjust lighting to illuminate both objects cohesively, and produce a final composite render. This reinforces material interaction, lighting balance, and scene composition—skills essential for professional 3D work.

---

## Appendix: Diagnostic Rubric for Self-Critique

Print and use this rubric to score your finished render on a scale of 1 (poor) to 5 (excellent):

| Criterion | 1 (Poor) | 2 (Weak) | 3 (Acceptable) | 4 (Good) | 5 (Excellent) |
|-----------|----------|----------|---|---|---|
| **Silhouette Accuracy** | Silhouette mismatched by > 15% from reference. | Silhouette off by 10–15%. | Silhouette matches within 5–10%. | Silhouette matches within 5%. | Silhouette matches within 2%, edge quality flawless. |
| **Topology Quality** | Contains n-gons or triangles; poles present throughout. | Mostly quads with occasional tris; poles in non-critical areas. | All quads, poles only at handles/attachment points. | All quads, clean poles, optimized density. | Production-quality topology, all quads, minimal pole count. |
| **Colour Accuracy** | RGB error > 20% in any channel. | RGB error 15–20%. | RGB error 10–15%. | RGB error 5–10%. | RGB error < 5%, perceptually indistinguishable from reference. |
| **Specular Quality** | No visible highlights or highlights are doubled/ghosting. | Highlights present but hard/fuzzy/multiple. | Single highlight per light, appropriate softness. | Tight, single highlight with realistic falloff. | Specular reflections match reference photograph exactly. |
| **Shadow Quality** | Shadows are harsh, unrealistic, or absent. | Shadows present but too dark or too soft. | Shadows realistic, soft, with appropriate density. | Shadows rich, with subtle gradation, good contact shadows. | Professional shadow quality: soft, realistic, perceptually accurate. |
| **Noise & Convergence** | Heavy speckled noise, fireflies visible at any zoom level. | Visible noise, noticeable at 1:1 view. | Minor noise at 1:1 view, clean at display resolution. | Clean at all zoom levels, no visible noise. | Flawless convergence, zero noise artifacts. |
| **Material Believability** | Material looks flat, plastic, or completely wrong. | Material vaguely resembles reference but lacks subtlety. | Material reads correctly as ceramic, appropriate roughness. | Material is photorealistic, convincing glaze and finish. | Material is indistinguishable from real ceramic; expert shading. |
| **Lighting & Composition** | Lighting is flat or non-existent; mug invisible or blown out. | Lighting is present but unbalanced or uninspired. | Lighting is good, 3-point setup visible, well-balanced. | Lighting is excellent, dramatic yet natural, professional quality. | Lighting is museum-quality: perfect ratio, directionality, mood. |
| **Overall Render Quality** | Render is unusable; major defects in geometry, shading, or lighting. | Render is acceptable for practice but obvious flaws remain. | Render is solid, suitable for portfolio review. | Render is polished, near-professional quality. | Render is production-ready, indistinguishable from photography. |

**Scoring Guide:**
- **Score 1–2**: Return to the relevant exercise and re-examine your model topology, material parameters, or lighting setup. Identify the specific failure and correct it.
- **Score 3**: Acceptable for learning; identify weak areas and refine in a second pass.
- **Score 4**: Good work; refinement would focus on micro-adjustments to material values or lighting ratios.
- **Score 5**: Excellent; your model is ready for portfolio presentation or client delivery.

---

## File Organization Summary

By the end of all three exercises, your project folder should contain:

```text
project_folder/
├── mug_model_exercise1.blend          (Orthographic blocking, topology check)
├── mug_model_exercise2.blend          (Shaded model, viewport render)
├── mug_model_exercise3.blend          (Final composited render, all passes)
├── mug_render_final.exr               (32-bit render with all passes)
├── mug_render_final.png               (8-bit PNG for quick viewing)
├── mug_render_critique.txt            (Documentation of parameters and final result)
├── reference_images/
│   ├── mug_front_ortho.png
│   ├── mug_side_ortho.png
│   ├── mug_top_ortho.png
│   └── mug_photograph.jpg
└── notes/
    └── material_analysis.txt           (RGB, roughness, metallic notes)
```

Before archiving your project, verify that all `.blend` files open without errors (File > Open > your file, then Render > Render Image to confirm). Save a final `.blend` file as `mug_project_archive.blend` with all objects, materials, and lights intact.

---

## Conclusion

You have now completed a full production-pipeline 3D asset workflow: orthographic modeling with topological rigor, PBR material authoring grounded in real-world reference capture, physically-based rendering with Cycles, and professional compositing. The techniques you have practiced—edge flow discipline, specular refinement, light placement, and sampling optimization—are the foundation for all 3D work, from product visualization to game-asset production to visual effects.

Repeat this workflow with different subjects (glass objects with refraction, metallic products, natural forms) to build versatility. As you advance, you will add complexity: rigging for animation, more sophisticated simulations, and larger asset libraries. The core discipline—topology first, materials second, lighting third—remains constant across all Blender production.
