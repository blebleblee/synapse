# Studio Practice Labs: 3D Rendering Global Illumination and Lighting

## Objective & Studio Setup

Global illumination represents a fundamental shift in how light behaves within your 3D scenes. Rather than relying exclusively on direct light rays from your sources to surfaces, global illumination simulates the physically plausible way light bounces between objects, accumulating and diffusing until it fills a space with ambient energy. This lab sequence trains your eye and hands to understand how light propagates in three dimensions, how materials interact with that light, and how to orchestrate both real-time and baked illumination systems to achieve visual intent.

Throughout these exercises, you will work with Blender as your primary tool. Blender's Cycles rendering engine provides a physically based ray-tracing foundation that mirrors industry-standard renderers (V-Ray, RenderMan, Arnold) while remaining freely accessible. The core principles you develop—reading light paths, understanding material energy conservation, managing render samples for quality versus speed—transfer directly to any renderer you encounter.

Before beginning, ensure your workstation has Blender 4.1 or later installed with CUDA, OptiX, or HIP compute capability enabled in Preferences > System > Compute Device. Create a dedicated project folder: `/Studio_GI_Lighting/` with subdirectories for `scenes/`, `renders/`, `references/`, and `critique/`. Download or photograph three reference images of real interior or product lighting scenarios—these will anchor your observation throughout the labs.

Your diagnostic toolkit includes the Blender Compositor for histogram and false-color visualization, viewport shading modes (Material Preview and Rendered), and both Cryptomatte and Lightpath passes for debugging indirect illumination paths. Keep a physical sketchbook nearby for rapid lighting diagrams and material notes; this analog bridge strengthens your spatial reasoning and prevents shallow digital clicking.

---

## Exercise 1: Observation & Fundamentals Drill

The foundation of intelligent lighting and global illumination work is rigorous visual observation. Before manipulating lights or render engines, you must train yourself to see light as a propagating medium that obeys consistent geometric and energy rules.

### Part A: Reading Real Light in Photographs

Open your first reference photograph in an image viewer alongside Blender. This reference should show a real interior or product scene with clear indirect illumination—a window-lit room, a studio-lit product on a colored table, or sunlight filtering through objects. Spend fifteen minutes studying this single image without taking notes. Observe where light appears brightest, where shadows fall, what colors emerge in shadowed regions, and how reflected light from one surface illuminates another.

Now open your sketchbook and draw a simplified lighting diagram of the scene. Use a top-down orthographic view. Mark the primary light source with an arrow; identify secondary surfaces that act as reflectors (a white wall bouncing light into shadow, a colored object tinting reflected illumination). Note the dominant shadow edges and any color shifts in those shadows—this is your first exposure to how secondary light carries color information.

This observational drawing is not about artistic skill; it is about decoding light geometry. When you look at a shadowed face illuminated by light bouncing from a blue wall, you are witnessing a specific chain: sunlight strikes the wall, reflects as blue-tinted radiance, travels to the face, and illuminates it. Your diagram should show this chain as a sequence of arrows and surfaces. The act of drawing forces you to identify what you are seeing rather than passively viewing it.

Repeat this process with your second and third reference images. By the end of Part A, you should have three detailed lighting diagrams showing primary sources, bounces, and secondary reflections. These diagrams are your visual vocabulary for the work ahead.

### Part B: Rendering Fundamentals with a Simple Sphere

Launch Blender and create a new General project. Delete the default cube. Add a UV Sphere (Shift+A > Mesh > UV Sphere) at world origin. Set its radius to 2 meters. This sphere will be your test object throughout this lab sequence; its simple geometry lets you isolate lighting and material effects without topology complexity.

Set your render engine to Cycles (Render Properties > Render Engine > Cycles). Confirm that your GPU compute device is active (Preferences > System). Set the viewport shading to Rendered (press Z, select Rendered) so you see ray-traced results in real time.

By default, Blender includes a world background that emits light. Navigate to Shading > World to see the world shader node graph. You will see a Background shader connected to the World Output. The default is a neutral gray; this provides ambient illumination. For this drill, replace the texture with a pure black (Value 0.0). This removes all ambient light so that only explicit light sources illuminate your sphere.

Now add a Sun Lamp to simulate direct sunlight. Press Shift+A > Light > Sun. In the Object Properties, rotate the sun to angle downward at approximately 45 degrees from horizontal (Rotation: X = 45°, Z = 0°). In the Light Properties, set Strength to 1.0 and confirm the light type is "Sun."

Look at your sphere in the Rendered viewport. You should see a bright directly-lit hemisphere facing the light and a completely black shadow on the opposite side. This is direct illumination only—no bounced light fills the shadow. The image looks harsh and unrealistic because real light scatters and bounces everywhere.

Now re-enable global illumination by navigating to the Shader Editor (with the World selected) and replacing the black Background shader with a color. Add a new Background shader and use a light blue (RGB: 0.5, 0.7, 1.0) at Strength 1.0. This blue world acts as a sky. Observe your sphere immediately: the shadow side now shows a soft blue tint. This blue light is not hitting your sphere directly from above—it is traveling through the scene geometry (or lack thereof), bouncing off the world background, and illuminating the shadow. This is the first visible manifestation of global illumination: indirect light carrying color information.

Render a frame at 128 samples (Render Properties > Sampling > Samples > 128) and save the result to `/renders/01_sphere_basic_gi.exr`. Use File > Render > Render Image.

### Part C: Cryptomatte and Light Path Debugging

Now examine how that indirect blue light reached your sphere. In the Shader Editor (with the Camera/World active), navigate to Render Properties > Passes and enable Cryptomatte and Diffuse Indirect. These passes decompose the ray paths that contribute to your final image.

Render again, and in the Compositor, add an input node for Cryptomatte: Shift+A > Input > Cryptomatte. Connect the Cryptomatte output to a Viewer node (Shift+A > Output > Viewer). Enable "Picking" in the Cryptomatte node and hover your cursor over different regions of the sphere render in the Compositor preview. This reveals which objects contributed to each pixel—here, it will show the World, since indirect light bounced from the world background.

Next, enable Render Properties > Passes > Diffuse Indirect. In the Compositor, add a File Output node (Shift+A > Output > File Output). Create two sockets: one connected to the Combined pass, one to the Diffuse Indirect pass. Render and save both. Open them in an image viewer and compare side by side. The Diffuse Indirect pass shows only the light that bounced indirectly onto your sphere; the Combined pass shows direct plus indirect. The difference between these two images is the visual contribution of global illumination to your final render.

Document your observations in your sketchbook: Where does indirect light brighten the sphere? What color does it carry? How does the intensity compare to direct sunlight?

This debugging workflow—using Cryptomatte and light passes to decompose rendering contributions—is essential for professional work. When a render lacks depth or looks flat, these passes tell you whether the problem is insufficient indirect illumination, poorly placed key lights, or material issues.

---

## Exercise 2: Technique Study, Step by Step

Having observed and debugged basic global illumination, you now move to controlled technique building. This exercise guides you through constructing a three-point lighting rig in a simple product scene, then progressively enabling global illumination systems to integrate direct and indirect light.

### Part A: Building a Three-Point Lighting Foundation

Create a new Blender scene. Add a simple product: a UV Sphere (radius 1.5 m), a Torus (major radius 2.0 m, minor radius 0.3 m), and a UV Cube scaled to 5×5×0.2 meters and positioned beneath the objects to act as a table surface. This heterogeneous set of geometry will show how light behaves across curved surfaces, ring topology, and planar reflective surfaces.

Set the world background to pure black (Value 0.0) to ensure you are building light from explicit sources only.

Establish your camera position: press Numpad-0 to enter camera view. Position the camera at approximately (5, 5, 3) looking toward the origin. Use the Gizmo or manually set Transform properties to frame the objects. This is your viewing angle for the entire exercise.

Now build a classic three-point rig:

**Key Light (Primary):** Add a Sun Lamp at position (4, 3, 5). Set Strength to 2.0, Angle to 1.5 degrees (a narrow penumbra simulating a focused studio light). Rotate it to cast light downward and from the left side of your camera view (Rotation: X = 60°, Y = 0°, Z = -30°). This light should create a strong, directional shadow of your objects on the table.

**Fill Light (Secondary):** Add a second Sun Lamp at position (-3, 2, 4). Set Strength to 0.6, Angle to 2.5 degrees. This lamp should be positioned opposite the key light and weaker, designed to soften shadows without eliminating them. Rotate it at (Rotation: X = 50°, Y = 0°, Z = 150°) so it opposes the key light direction.

**Back Light (Rim):** Add a third Sun Lamp at position (0, -4, 3). Set Strength to 1.2, Angle to 1.0 degree. This light sits behind and above your objects, designed to rim-light them and separate them from the background. Rotate it at (Rotation: X = 70°, Y = 0°, Z = 0°).

Render a frame at 128 samples. This is your baseline direct-lighting-only render. Save to `/renders/02_product_three_point_direct.exr`. Observe the harsh shadow edges and the unnaturally dark areas where fill light does not reach—these are typical artifacts of direct-only rendering in professional work.

### Part B: Materials and Energy Conservation

Before adding global illumination, establish proper materials. Select your sphere object and enter the Shader Editor. By default, it has a Principled BSDF shader. In the Material Properties, name this material "Ceramic_White."

In the Principled BSDF node, set:
- **Base Color:** RGB (0.95, 0.95, 0.95) — a bright, nearly-white matte surface
- **Metallic:** 0.0
- **Roughness:** 0.3 — slightly rough, not polished
- **Subsurface Weight:** 0.0 (keep at 0 for now; subsurface scattering is a separate technique)
- **IOR:** 1.5 (standard dielectric material)

This material represents a ceramic or plaster finish. The combination of high Base Color value and moderate roughness means the material diffusely reflects most light without specular highlights.

Select the torus and assign a different material called "Wood_Dark." Set:
- **Base Color:** RGB (0.3, 0.2, 0.15) — a dark wood tone
- **Metallic:** 0.0
- **Roughness:** 0.5 — wood is moderately rough
- **IOR:** 1.5

Select the cube (table surface) and create "Table_Reflective":
- **Base Color:** RGB (0.8, 0.75, 0.7) — warm beige
- **Metallic:** 0.0
- **Roughness:** 0.15 — a sanded, polished surface with subtle specular reflections

The principle underpinning these material assignments is energy conservation: the sum of reflected, transmitted, and absorbed light energy must not exceed 1.0 (100%). The Principled BSDF in Blender enforces this automatically, but understanding it shapes your material decisions. A Base Color of (1.0, 1.0, 1.0) on a metal with Metallic 1.0 will reflect nearly all light; the same color on a rough dielectric will absorb some. Dark colors (low RGB values) absorb more energy and reflect less, making them appear duller and contributing less indirect light to their surroundings.

Render again at 128 samples with your three-point rig and materialized objects. Save to `/renders/02_product_materials_direct.exr`. The materials should now look more naturalistic; the white sphere should stand out as bright, the wood torus should appear darker and warmer, and the table should have a subtle sheen.

### Part C: Enabling Global Illumination with Render Settings

Now introduce controlled global illumination. In Render Properties > Light Paths, observe the defaults:
- **Max Bounces:** 32
- **Diffuse Bounces:** 12
- **Glossy Bounces:** 8
- **Transmission Bounces:** 8

These values control how many times a light ray can scatter before the renderer stops tracing it. Higher values simulate more realistic light bouncing but require more computation. For this exercise, leave them at defaults initially; we will optimize later.

Enable Render Properties > Sampling > Adaptive Sampling. Set Adaptive Threshold to 0.01 (a stringent 1% threshold) and Adaptive Min Samples to 64. This tells Blender to automatically direct more samples toward pixels that need refinement, improving efficiency.

Navigate to World Shader Editor and enable a minimal indirect fill. Replace the black Background with:
- A Background shader set to light gray (RGB: 0.3, 0.3, 0.3) at Strength 1.0.

This gray world acts as a neutral fill light that reflects off your objects. It is not physically realistic (real skies have specific color and brightness properties), but it simulates a studio cyclorama—a neutral curved backdrop that provides ambient fill.

Render at 256 samples (now that adaptive sampling helps efficiency). Save to `/renders/02_product_gi_minimal.exr`. Compare side by side with your direct-only render. The shadows should now have a subtle gray tone, and the dark wood torus should show softened shadow edges. This is global illumination at work: light from the gray world background bounces onto your objects, gradually filling in darkness.

The visual difference may seem subtle, but it is profound. Your render now includes at least one bounced light path: Sun Lamp → Table Surface → Objects (indirect fill). This is the core of global illumination: by allowing light to bounce between surfaces, you gain perceptually correct soft shadows and color bleeding that no direct-lighting rig alone can achieve.

### Part D: Color Bleeding and Reflective Surfaces

To make color bleeding visually apparent, modify your scene. Keep the three-point rig and your materials, but change the world background to a saturated color: RGB (1.0, 0.0, 0.0) at Strength 0.5 (a deep red). This exaggerated color will propagate via global illumination into your scene.

Render at 256 samples. Save to `/renders/02_product_color_bleeding.exr`. Examine the shadows and undersides of your objects, especially the sphere and torus. You should see a reddish tint in areas not directly lit by your key light, particularly in contact shadows where geometry is very close together. This red color is coming from the world background bouncing around your scene—a phenomenon called color bleeding. In real scenes, this is subtle and naturalistic; here, the exaggerated red makes the mechanism clear.

Now, reduce the roughness of your table surface to increase its specularity. Select the table, go to Shader Editor, and change the Table_Reflective material Roughness from 0.15 to 0.05. Render again at 256 samples and save to `/renders/02_product_specular_bounce.exr`. The table now acts as a polished mirror, and you should see stronger red-tinted reflections on the undersides of objects sitting on it. The specular bounce—light reflecting off a glossy surface at a sharp angle—now contributes more prominently to indirect illumination.

Document your observations: In which regions does color bleeding appear strongest? How does surface roughness affect the intensity of indirect light? Why does the dark wood torus show color bleeding more prominently than the bright white sphere?

The answers relate to material absorption and reflectance. Dark materials absorb more light (less energy is available to bounce), so they appear to contribute less indirect illumination. However, any light they do reflect carries strong color information from their surroundings. The white sphere, conversely, reflects more light overall, so indirect illumination is proportionally weaker relative to its own self-emission and direct reflection.

### Part E: Render Optimization—Samples, Denoising, and Noise

Rendering global illumination correctly requires sufficient samples to avoid visible noise. At 256 samples, your image likely has acceptable quality. Reduce samples to 64 and render again; save to `/renders/02_product_low_samples.exr`. The image should show speckling and grain, particularly in shadow regions and on rough surfaces. This is Monte Carlo noise—the statistical consequence of sampling light paths randomly.

Professional workflows solve this via denoising. In Render Properties > Compositing, enable Denoising. Leave the Denoising Engine as "OpenImageDenoise" (the default). Render at 64 samples again. Enable Render Properties > Passes > Denoising Normal and Denoising Albedo to give the denoiser auxiliary information for edge preservation. Render and save to `/renders/02_product_denoised.exr`. The denoised result should be nearly as clean as the 256-sample render but computed in a fraction of the time.

This is a critical professional technique: render at lower samples to save time, then use AI-based denoising to recover quality. Modern production pipelines almost always employ this strategy.

### Part F: Baked Global Illumination (Lightmap Workflow)

For real-time engines or scenarios where repeated rendering is infeasible, pre-computed lighting is essential. Blender supports baking indirect illumination into lightmaps—pre-rendered textures that encode light information across surfaces.

Create a new material called "Baked_Target" on your table cube. In the Shader Editor, add a new Image Texture node (Shift+A > Texture > Image Texture) but do not connect it yet. Click "New" in the Image Texture node and create an image called "table_bake" at 2048×2048 pixels. Leave the image unconnected; it is a bake target, not a live shader node.

Select the table object. In Object Properties > Bake, ensure Cycles is active. Set Bake Type to "Combined," which bakes all lighting contributions (direct and indirect) into a single texture. Set Render Passes to include Diffuse and Glossy.

Before baking, ensure your UV map is correct. Select the table and press Tab to enter Edit Mode. Press U > Unwrap > Smart UV Project to auto-unwrap the cube faces. This maps 3D surface area to 2D texture space, necessary for lightmap baking.

Return to Object Mode and click Bake (Object Properties > Bake > Bake). The bake process runs the full Cycles renderer with your three-point rig and global illumination, rendering lighting information directly into the lightmap texture. For a small scene like this, baking should complete in 10–30 seconds.

Once complete, switch to the Shading workspace. Select the table, and in its Principled BSDF, reduce the Base Color saturation temporarily to see the baked texture more clearly. Connect the previously unconnected Image Texture (table_bake) directly to the Base Color input of the Principled BSDF. Set the material's Roughness to 0.0 (temporarily making it perfectly smooth) so baked texture details are visible without self-shadowing.

Render and save to `/renders/02_product_lightmap_baked.exr`. Compare with your ray-traced global illumination render. They should be nearly identical, though the baked version may show some artifacts at texture boundaries if the unwrap was imperfect. This baked texture can now be exported and used in a real-time game engine without further computation.

Your sketchbook should now contain detailed notes on render settings, material configurations, and baking workflows. These are your reference cards for future projects.

---

## Exercise 3: Finished Piece & Self-Critique

The final exercise demands you create a complete, publishable render that demonstrates mastery of global illumination and lighting under real production constraints.

### Part A: Scene Construction and Brief

Design a brief for yourself: "Interior product render—a coffee mug and book on a wooden desk, photographed from a 45-degree overhead angle in soft natural window light supplemented by a desk lamp." This brief constrains your creative decisions but leaves room for interpretation.

Create a new Blender scene and build the geometry:

1. **Desk Surface:** Model a rectangular mesh (5 × 3 × 0.05 m) using Edit Mode. Subdivide it into a 32×32 grid (Subdiv Surface modifier set to Levels Viewport 2, Render 4) to allow for surface detail. Add a material called "Wood_Desk": Base Color RGB (0.4, 0.3, 0.2), Roughness 0.4, Metallic 0.0.

2. **Coffee Mug:** Import or model a simple cylindrical mug (0.08 m diameter, 0.1 m height). Add a simple handle using a torus (major radius 0.055 m, minor radius 0.01 m). Create two materials: "Ceramic_Mug" (Base Color RGB 0.9, 0.9, 0.9, Roughness 0.2) for the body and "Ceramic_Mug_Handle" (identical) for the handle. Position the mug at (1.5, 0.5, 0.05 m) on the desk surface.

3. **Book:** Model a rectangular box (0.15 × 0.2 × 0.02 m) with one plane subdivided and displaced slightly to simulate texture. Add a material called "Book_Red": Base Color RGB (0.7, 0.1, 0.1), Roughness 0.6. Position it at (-1.0, 0.8, 0.05 m).

4. **Wall Behind Desk:** Model a large plane (8 × 6 m) positioned 2 meters behind the desk. Add material "Wall_Plaster": Base Color RGB (0.9, 0.85, 0.8), Roughness 0.5. This wall will catch light and reflect indirect illumination back into the scene.

5. **Window Light Source:** Add a Rectangular Emitter lamp (Shift+A > Light > Area) positioned at (−3, 0, 2.5 m), scaled to 2×1.5 m. This emitter simulates window light. Set Strength to 2.0 and Angle to 0.0 (soft, diffuse). Assign it a light color of RGB (1.0, 0.95, 0.85) to simulate warm window light. This is a crucial element: rather than using a Sun lamp, an Area light with soft shadows simulates real sunlight filtered through windows.

6. **Desk Lamp:** Add a Spot Lamp (Shift+A > Light > Spot) positioned at (1.0, −1.5, 0.3 m), pointing downward (Rotation: X = 90°, Y = 0°, Z = 0°). Set Strength to 1.0, Size (Spot Size) to 45 degrees, and Blend to 0.15. This lamp provides local accent lighting. Assign it a warm color RGB (1.0, 0.9, 0.7).

Set your world background to a light blue (RGB: 0.7, 0.8, 1.0) at Strength 0.3. This provides a subtle sky-colored fill.

Position your camera at (3, −2, 1.2) looking toward the desk center (0, 0, 0.1). This 45-degree overhead angle is classic product and interior photography.

### Part B: Render Settings and Global Illumination Configuration

Configure your render for final production quality:

**Sampling:**
- Samples: 512 (high quality)
- Adaptive Sampling: Enabled, Threshold 0.005, Min Samples 128
- Adaptive Min Samples defines the minimum sample count before adaptation kicks in

**Light Paths (Global Illumination Control):**
- Max Bounces: 32
- Diffuse Bounces: 8
- Glossy Bounces: 8
- Transmission Bounces: 4
- Volume Bounces: 4

These values are balanced: sufficiently high to simulate multiple indirect bounces (window light reflecting off the wall, then the desk, filling the mug's interior shadow), but not so high that render time explodes.

**Denoising:**
- Enable Denoising: ON
- Denoising Engine: OpenImageDenoise
- Include Denoising Data: Enabled (Normal and Albedo passes)

**Cryptomatte & Light Path Passes (for debugging):**
Enable the following in Render Properties > Passes:
- Combined
- Diffuse Direct
- Diffuse Indirect
- Glossy Direct
- Glossy Indirect
- Emission

These passes let you decompose exactly which light paths contribute to your final image.

### Part C: Progressive Rendering and Observation

Before committing to the full 512-sample render, do a progressive test:

1. **64 samples render:** Render at low samples to verify geometry, material placement, and lighting direction are correct. Save to `/renders/03_scene_proof_64.exr`. Check that the mug is well-lit, the book has depth, and the desk surface shows directional light from your window emitter. This render should complete in 5–15 seconds depending on your GPU.

2. **256 samples render:** Increase to medium quality and examine shadow softness, indirect light color in shadowed regions, and overall ambient fill. Save to `/renders/03_scene_proof_256.exr`. At this quality, the image should look nearly final, though noise may be visible in very dark areas.

3. **Full 512-sample render:** Execute the final render. This may take 2–5 minutes depending on your hardware. Save to `/renders/03_scene_final_512.exr`.

As each render completes, stand back and observe from arm's length. Where is light brightest? Do shadows fall in plausible directions? Does the mug appear three-dimensional, or flat? Are there any harsh artifacts (aliasing, speckling, banding)? These observations inform your critique.

### Part D: Pass Analysis and Debugging

Export and examine your light path passes. In the Compositor (Shift+F3), create a node setup to view each pass:

```
File Input (renders/03_scene_final_512.exr)
├─ Combined → Viewer (displays final image)
├─ Diffuse Direct → Viewer (direct illumination on diffuse surfaces)
├─ Diffuse Indirect → Viewer (bounced light on diffuse surfaces)
├─ Glossy Direct → Viewer (specular reflection of direct lights)
└─ Glossy Indirect → Viewer (specular reflection of bounced light)
```

For each pass, write observations in your sketchbook:

- **Diffuse Direct:** This shows only light rays that traveled directly from your lamps to diffuse surfaces. It should show strong illumination from the window emitter and desk lamp, with sharp shadows. Dark regions indicate areas not directly lit.

- **Diffuse Indirect:** This reveals indirect diffuse bouncing. You should see warm light bouncing from the desk surface onto the mug's lower side, blue-tinted light from the wall filling shadows, and color bleeding from the red book toward adjacent surfaces.

- **Glossy Direct:** Specular reflections of direct lights. The mug's shiny surface should show a mirror-like reflection of the window emitter; the desk lamp may create a bright spot.

- **Glossy Indirect:** Subtle reflections of environment light. If your wall is light and your camera angle allows it, you may see the wall reflected in the mug's surface as a soft highlight.

Compare the sum of Diffuse Direct + Diffuse Indirect + Glossy Direct + Glossy Indirect to your Combined pass. They should closely match (differences are due to emission, background, and color space precision).

This pass decomposition is a professional diagnostic tool. If your render looks flat, check Diffuse Indirect: is enough bounced light reaching shadows? If highlights look harsh, compare Glossy Direct and Glossy Indirect: are you over-lighting specular surfaces?

### Part E: Comparison Renders—Isolating Global Illumination's Impact

To clearly demonstrate the effect of global illumination, create two additional renders:

**Render 1: Global Illumination Disabled**
In Render Properties > Light Paths, temporarily set:
- Max Bounces: 1 (only direct light and first reflection)
- Diffuse Bounces: 0 (no diffuse bouncing)
- Glossy Bounces: 1 (only direct specular, no indirect specular)

Render at 256 samples and save to `/renders/03_scene_NO_GI.exr`. This render shows only direct light from your window and desk lamp, with no bounced indirect illumination. Shadows should be pure black or very dark, and the overall image should appear harsh and low-contrast.

**Render 2: Global Illumination Enabled (Your Final Render)**
Restore your production settings and render again. Save to `/renders/03_scene_WITH_GI.exr` (or reference your earlier 512-sample render).

Create a side-by-side comparison in an image viewer. The difference is stark: GI-enabled render should show soft, filled shadows, color bleeding from the red book, warm light bouncing from the desk onto the mug, and an overall sense of spatial coherence that the no-GI render lacks.

Document your findings: Approximately what percentage of shadow illumination comes from indirect light versus direct light? In which materials (white mug, red book, wooden desk) is indirect light most visible?

### Part F: Critique and Iteration

Print your final render (or display it full-screen on a large monitor). Evaluate it against these professional criteria:

**Lighting Direction & Motivation:** Does the direction of light make sense for your scene brief? Window light should come from a consistent direction; the desk lamp should provide local accent. If the lighting feels unmotivated or confused, your camera angle or light positions need adjustment.

**Shadow Quality:** Are shadows soft and plausible? Do they fall in physically coherent directions? Harsh shadows indicate insufficient global illumination or a camera angle that makes direct shadows too visible; either adjust Max Bounces upward (adds more computation but more realistic fill) or reposition your key light source.

**Material Realism:** Do your materials respond to light as expected? The white mug should appear bright and reflect significant light; the red book should appear saturated and darker; the wooden desk should show warm wood tones. If materials look flat or desaturated, check Base Color values in your materials and confirm they align with your reference.

**Color Bleeding:** Is there subtle color bleeding from the red book onto adjacent surfaces? This is global illumination working correctly. If it is absent or too weak, your Diffuse Bounces value may be too low, or your book color may not be saturated enough.

**Noise & Denoising Artifacts:** Is the image noise-free and sharp? Denoising should not introduce halos or blur edges. If edges look over-smoothed, reduce Denoising Strength or increase samples.

If your critique identifies issues, make targeted adjustments:

1. **Flat shadows?** Increase Render Properties > Light Paths > Diffuse Bounces to 12–16, then re-render.
2. **Excessive noise in shadows?** Increase Samples from 512 to 1024, or reduce Denoising Threshold.
3. **Material looks wrong?** Check Shader Editor for that material; confirm Base Color, Roughness, and Metallic are correct.
4. **Harsh or blown-out highlights?** Reduce Area light Strength or increase Spot light Size to soften its falloff.

Iterate once. Render a corrected version at full settings and save to `/renders/03_scene_final_corrected.exr`.

---

## Critique Checklist & Common Fixes

The following checklist applies whether you are critiquing your own work or a peer's render. Use it to identify problems and diagnose their root causes.

### Visual Checks (Do These First)

**Lighting coherence:** Stand at arm's length and squint. Lighting direction should feel natural and motivated by your scene (window, lamps, etc.). If light seems to come from multiple conflicting directions, one light source is probably too bright relative to others, or a light is positioned incorrectly. Fix: Review light positions and Strength values; ensure key lights outnumber and outweigh fill/accent lights in energy.

**Shadow behavior:** Shadows should be softest farthest from the light source (penumbra) and sharpest closest to the light. If all shadows are uniformly soft, your light sources are too diffuse or too far away; if all are uniformly hard, your global illumination is insufficient or your lights are too small (narrow beam angles). Fix: For soft shadows, use large Area lights or increase Sun light Angle. For better shadow definition with soft fill, combine a small focused key light with diffuse fill lights.

**Realism of dark regions:** Very dark areas (near-black shadows) should contain subtle detail and color, not pure black. If shadows are pure black, your scene lacks ambient fill or indirect bouncing. Fix: Enable or increase world background color, or increase Diffuse Bounces.

**Material appearance:** Each material should respond to light distinctly. Matte surfaces reflect light diffusely; glossy surfaces show sharp specular highlights; metals show mirror-like reflections. If all surfaces look similarly lit (matte and shiny alike), check that your materials have correct Roughness and Metallic values.

### Render Settings Checks

**Sample count adequate?** Zoom into shadow regions at 100% (1:1 pixel zoom). Visible grain or speckling indicates insufficient samples. This is especially evident in areas lit primarily by indirect bouncing, which is noisier than direct light. Fix: Increase Samples (e.g., 512 → 1024) or enable Adaptive Sampling with lower Threshold (e.g., 0.01).

**Light Paths sufficient?** If shadows are uniformly black or barely visible, increase Max Bounces and/or Diffuse Bounces. Scenes with many small reflective objects or narrow corridors require higher bounce counts (12–16 diffuse bounces) to achieve plausible indirect fill. Test by rendering a small region at 512 samples with Max Bounces 32 and Diffuse Bounces 16; if the image changes significantly compared to Diffuse Bounces 4, your original settings were too conservative. Fix: Increase bounce counts; re-render.

**Denoiser artifacts?** Look for halos (bright rings) around sharp edges or over-smoothed bump map detail. This indicates the denoiser is over-aggressive. Fix: Reduce Denoising Strength (if available in your renderer) or disable denoising and increase samples instead.

### Common Problems & Fixes

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| Harsh, unrealistic shadows | Direct lighting only; insufficient global illumination | Increase Diffuse Bounces to 8–12; ensure world background is not pure black |
| Flat, low-contrast render | Over-aggressive denoising or insufficient direct-to-indirect light ratio | Increase key light Strength; verify lights are positioned to create directional shadows; reduce denoiser strength |
| Noise in dark regions | Monte Carlo sampling variance; too few samples in areas lit primarily by indirect bouncing | Increase Samples to 1024+; enable Adaptive Sampling; consider render-time denoising |
| Specular highlights blown out (pure white) | Light source too strong or too close to reflective surface | Reduce light Strength or move light away; increase Roughness on reflective surfaces |
| Color bleeding absent or too subtle | Diffuse Bounces too low; colored surfaces not saturated enough | Increase Diffuse Bounces to 12+; ensure colored objects have vivid Base Colors (avoid gray tints) |
| Material looks flat or desaturated | Incorrect Base Color, Roughness, or Metallic values in Shader | In Shader Editor, verify Base Color RGB values are in correct range; set Roughness to 0.3–0.5 for natural materials (not 1.0); confirm Metallic is 0.0 for non-metals |
| Long render times (hours) | Excessive light bounces, high sample count, or complex scene geometry | Reduce Max Bounces to 16, Diffuse Bounces to 8; enable Adaptive Sampling; use Cryptomatte to identify over-complex objects and simplify |
| Texture seams or discontinuities in baked lightmaps | Poor UV unwrapping; overlapping UV islands | Re-unwrap using Smart UV Project; ensure no UV islands overlap in UV space; increase lightmap resolution (e.g., 2048 → 4096) |

### Professional Diagnostic Workflow

When a render looks wrong but the problem is not immediately obvious, follow this systematic process:

1. **Enable Render Properties > Passes > Cryptomatte** and examine which objects contribute to problem pixels. This isolates whether the issue is in a specific material or light path.

2. **Decompose into passes** (Diffuse Direct, Diffuse Indirect, Glossy Direct, Glossy Indirect) in the Compositor and compare each. If Diffuse Indirect is black or very dim, indirect bouncing is the problem. If Glossy Direct shows blown-out highlights, your specular light is too strong.

3. **Temporarily increase Samples to 2048** and render a small viewport region to establish a "ground truth" image. Compare this high-quality reference to your current production render. If they differ significantly, your settings are too conservative; if they match, your current settings are adequate.

4. **Check material absorption** by temporarily setting a problematic object to pure white (Base Color 1.0, 1.0, 1.0) and re-rendering. If the scene suddenly looks brighter and more filled with indirect light, the object was absorbing too much light due to its color. Adjust its Base Color accordingly.

5. **Document your findings in your sketchbook** with the render, settings, and diagnosis. This builds your personal reference library for future troubleshooting.

---

## Conclusion & Ongoing Practice

You have now trained your eye to see light as a propagating phenomenon, understood the fundamental mechanisms of global illumination (direct light, one-bounce indirect, multi-bounce diffuse and specular), and developed practical workflows for render optimization, baking, and troubleshooting.

Continuing this practice demands regular rendering of real-world briefs: interiors, products, characters, vehicles. Each new scene teaches something—a material property, a lighting direction, an edge case in global illumination. Keep your sketchbook alongside your rendering workspace; rapid lighting diagrams and pass studies form the intuition that transforms you from a tool-operator into a visually literate 3D artist.

The principles you have learned—energy conservation in materials, importance of sampling and denoising, indirect light's role in visual realism, baked lighting for real-time systems—transfer directly to any renderer. Whether you eventually work in V-Ray, RenderMan, Unreal Engine's Lumen, or a custom in-house system, your understanding of how light propagates and how to orchestrate it remains constant. The tools change; the visual language of light does not.
