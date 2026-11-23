# Studio Practice Labs: DaVinci Resolve Color Grading and Fusion

## Objective & Studio Setup

This guide takes you through three progressive laboratory sessions that build hands-on mastery of DaVinci Resolve's color grading and Fusion compositing workflows. The labs are designed around real production scenarios: managing media at ingest, grading a typical narrative sequence, and compositing visual effects into graded footage. By the end of these exercises, you will understand how to organize media architecture, execute precise color decisions using node graphs, and composite layered elements with Fusion's parametric control system.

**What you need:** DaVinci Resolve Studio (the free version limits some advanced Fusion features; this guide assumes Studio edition), a sample video project (provided workflows below use freely available test footage), headphones or speakers for audio reference, and a calibrated display or reference monitor. Set your workspace to accommodate three primary windows: the media pool on the left, the node editor in the center-top, and the viewer on the right. Use Resolve's built-in scopes—waveform monitor, histogram, and vectorscope—as diagnostic instruments throughout each exercise. All exercises assume a 1920×1080 (1080p) project timeline at 23.976 fps (or your native frame rate); adjust file names and render paths to match your system.

---

## Exercise 1: Media Management & Non-Destructive Grading Architecture

### Exercise 1: Observation & Fundamentals Drill

Begin by working with a short 30-second clip of mixed color temperature lighting. If you do not have source footage, download a free public-domain short film clip (such as "Big Buck Bunny" or "Sintel" from the Blender Project) and extract a 30-second segment using FFmpeg:

```bash
ffmpeg -i input_video.mp4 -ss 00:00:30 -t 00:00:30 -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k lab1_source.mp4
```

Launch DaVinci Resolve Studio. Create a new project by selecting **File > New Project** and naming it `Lab1_MediaManagement`. Set the timeline resolution to 1920×1080 and the frame rate to 23.976 fps. In the **Media Pool** (left panel), right-click and select **Import Media** to bring in your 30-second clip. Resolve will generate cache files automatically; allow this to complete before proceeding.

Now observe the ungraded footage. Play the clip and study the original color. Open the **Color Page** by clicking the icon at the bottom of the screen, or press **Ctrl+Alt+3** (Cmd+Alt+3 on Mac). The node graph will appear in the center-top panel; initially, you will see a single **Color Corrector** node labeled "Correction 1" connected to the **Viewer** output.

Before grading, establish a diagnostic baseline. At the bottom of the Color page, enable the **Waveform Monitor** by clicking **Workspace > Scopes > Waveform**. The waveform will display luminance (brightness) distribution across your image vertically and time horizontally. A well-exposed image shows waveform activity between 0 (pure black) and 100 (pure white), without clipping at either extreme unless intentional. Study your ungraded clip: does the waveform sit in the mid-tones, or is it bunched at the shadows or highlights? Note the color temperature: does the footage look cool (blue-shifted) in some shots and warm (orange-shifted) in others? This observation will inform your grading decisions.

Enable the **Vectorscope** (Workspace > Scopes > Vectorscope). The vectorscope displays color saturation and hue as a polar plot, with magenta, red, yellow, green, cyan, and blue sectors. A neutrally lit scene will show a small cloud of points near the center; a strongly color-cast scene will show activity biased toward one hue sector. Record your observations: Is the scene predominantly red, green, or blue? Is saturation low (desaturated) or high (vivid)?

Enable the **Histogram** (Workspace > Scopes > Histogram) to see luminance distribution as a column graph. A histogram spread across the full range indicates good contrast; a histogram bunched to the left indicates underexposure, and to the right indicates overexposure. Note where your footage falls.

Play the entire 30-second clip and observe whether these color characteristics remain consistent or shift frame-to-frame. When color shifts abruptly (e.g., from a tungsten-lit interior to a daylight exterior shot), Resolve calls this a "shot break." Make a mental note of where shot breaks occur; you will grade each shot differently.

### Exercise 2: Technique Study — Setting Up Non-Destructive Node Architecture

The power of DaVinci Resolve lies in its non-destructive node graph. Every color operation is a node, and multiple nodes can be chained together without permanently altering pixel data. This architecture allows you to experiment freely, compare versions, and correct mistakes by toggling nodes on and off.

In the Color page, you have one **Color Corrector** node. Right-click on the node (the blue box in the center-top) and select **Add Node > Serial** to append another node after it. Name this new node by right-clicking and selecting **Rename Node**, then typing `Global_Luma_Balance`. This first node will handle overall brightness and contrast.

Click on the first node (`Global_Luma_Balance`) to select it and open its controls in the **Inspector** (the right-side panel). Under the **Color** section, you will see sliders for **Offset**, **Gain**, **Gamma**, **Contrast**, and **Pivot**. These are the fundamental luma adjustments.

**Offset** brightens or darkens the entire image uniformly; it is equivalent to turning up the brightness control on a monitor, and it affects all tonal ranges equally. **Gain** multiplies the brightness but preserves black (it brightens highlights and midtones more than shadows). **Gamma** adjusts midtone brightness while holding black and white in place; gamma is the most perceptually natural control for overall exposure correction. **Contrast** spreads the tonal range apart (high contrast) or pulls it together (low contrast). **Pivot** sets the fulcrum around which contrast operates; a pivot of 0.5 (neutral gray) is standard.

For your ungraded clip, adjust **Gamma** first. If the waveform indicated underexposure (bunched to the left), increase gamma to 1.2. Play the clip and observe the waveform and viewer simultaneously. The waveform should spread rightward, indicating increased brightness. If overexposure was present, decrease gamma to 0.8. Find a value where the waveform sits comfortably between 10 and 90, with no crushing of blacks (waveform bunched at 0) or blown highlights (waveform clipping at 100). Record this gamma value.

Next, add a **Curves** adjustment in a new serial node. Right-click on the existing node and select **Add Node > Serial**. Rename this node `Shadows_Midtones_Highlights`. Select the new node and find the **Curves** control in the Inspector. The curve is an interactive graph where the horizontal axis represents input luminance (0 = black, 100 = white) and the vertical axis represents output luminance. A straight diagonal line means no change. Pulling the left end of the curve upward brightens shadows; pulling the middle upward brightens midtones; pulling the right end downward darkens highlights.

For a typical daylit interior scene where shadows are too dark, click on the left-third of the curve and drag it upward slightly (increase Y by 5–10 units). This lifts shadow detail without blowing out the rest of the image. Play the clip and check the waveform; shadow detail should become visible. If the image now looks flat, increase contrast by pulling the right end of the curve upward and the left end downward in a gentle S-shape. The curve remains smooth; avoid sharp kinks, which can introduce posterization (visible banding in gradients).

Now add a **Color Balance** node for color correction. Right-click and select **Add Node > Serial**, then rename it `Color_Temperature_Correction`. In the Inspector, under **Color**, find the **Shadows**, **Midtones**, and **Highlights** sliders. Each is a three-axis control (Red/Cyan, Green/Magenta, Blue/Yellow). If your ungraded clip appeared blue-shifted (cool), move the **Midtones > Blue/Yellow** slider toward yellow (increase the value) to warm the image. If it appeared orange-shifted (warm), move toward blue (decrease). Make small adjustments (5–15 units) and play the clip; color shifts are perceptually loud, and restraint is key to naturalistic grading.

Now you have a three-node non-destructive pipeline: Global Luma Balance → Shadows/Midtones/Highlights → Color Temperature Correction. Play the entire 30-second clip and observe whether these three nodes have brought the footage into a neutral, well-exposed, and color-balanced state. Use the waveform, histogram, and vectorscope to verify: waveform should be distributed across the range, histogram should show no clipping at either end, and vectorscope should show color balanced around the center without strong bias toward any hue.

### Exercise 3: Finished Piece & Self-Critique

Export your graded sequence to verify it. At the top of the Color page, click the **Deliver** tab (or press **Ctrl+Alt+6** on Windows, **Cmd+Alt+6** on Mac). In the **Deliver** page, set the following parameters:

- **Video Format:** H.264
- **Resolution:** 1920×1080
- **Frame Rate:** 23.976 fps
- **Bitrate:** 8 Mbps (sufficient for 1080p streaming reference)
- **Output Path:** `Lab1_graded.mp4` (save to your project folder)

Click **Add to Render Queue**, then click **Start Render**. Resolve will encode the graded sequence and save it to disk. Once complete, open the file in a media player (VLC, QuickTime, or Windows Media Player) on a full screen and observe the result away from the Resolve UI.

Compare the graded version (`Lab1_graded.mp4`) to your original source (`lab1_source.mp4`) side-by-side. Load both files into separate VLC instances, start them in sync, and observe:

- **Luminance balance:** Is the graded version brighter and clearer than the original, with visible shadow detail and controlled highlights?
- **Color neutrality:** Do skin tones appear natural (slight warm bias toward peachy, not blue or sickly green)? Do whites appear white, not tinted?
- **Contrast:** Is the image snappy, or is it flat and dull?
- **Consistency across cuts:** When a shot break occurs, does the color shift abruptly, or have you maintained continuity?

Write down three observations in a text file called `Lab1_observations.txt`. Example:

```
Observation 1: The shadows lifted nicely with the gamma adjustment, 
but the highlights now look slightly blown in the bright window area. 
Consider pulling down the top-right of the curves to control highlights.

Observation 2: The color balance feels natural, but the midtone blue/yellow 
slider might have overcorrected. The sky now looks too warm.

Observation 3: Shot break at frame 450 is jarring—the second shot is significantly 
cooler than the first. Needs individual grading per shot, not global correction.
```

---

## Exercise 2: Shot-by-Shot Grading with Clip-Based Corrections

### Exercise 1: Observation & Identifying Shot Breaks

Create a new project: **File > New Project**, name it `Lab2_ShotGrading`. Import a longer clip (at least 2–3 minutes) with visible shot breaks. If you do not have source footage, construct a simple test sequence using FFmpeg by concatenating two segments with different color temperatures:

```bash
# Download two different scenes (or create them)
ffmpeg -i input1.mp4 -ss 00:00:00 -t 00:00:45 -c copy segment1.mp4
ffmpeg -i input2.mp4 -ss 00:00:30 -t 00:00:45 -c copy segment2.mp4

# Concatenate them
echo "file 'segment1.mp4'" > filelist.txt
echo "file 'segment2.mp4'" >> filelist.txt

ffmpeg -f concat -safe 0 -i filelist.txt -c copy lab2_source.mp4
```

Import `lab2_source.mp4` into the Media Pool. Go to the **Edit** page (press **Ctrl+Alt+1** or **Cmd+Alt+1**) to view the timeline. You will see a single clip spanning the duration. Enable the **Timeline Scopes** to monitor color across the timeline. In the Edit page, go to **Workspace > Scopes > Waveform** to display the waveform in real-time as you play the timeline.

Play the timeline from start to finish. Watch the waveform closely. You will notice shifts in luminance and color when shot breaks occur; the waveform will suddenly drop or spike, and the vectorscope (if displayed) will show hue shifts. Mark the timecodes where these transitions occur. In DaVinci, you can add **markers** to flag important frames. Press **M** at a shot break to add a marker, and Resolve will note the frame number. Create markers at every shot break in your sequence.

After marking, examine each shot individually. Click on a marker, and Resolve will jump to that frame. Hover over the clip in the timeline and look at the **clip selector** (the frame counter at the bottom center of the Edit page) to see the exact timecode. Take screenshots or notes of the color characteristics of each shot. Example notes:

```
Shot 1 (00:00:00 - 00:00:45): Indoor tungsten lighting, warm cast, dim
Shot 2 (00:00:45 - 00:01:30): Outdoor daylight, cool cast, bright
```

Understanding the original color palette of each shot is essential before grading; it informs your creative intent and helps you identify which corrections are technical (exposure/white balance fixes) and which are stylistic (mood, contrast, saturation adjustments).

### Exercise 2: Clip-Based Correction Using Nodes and Keyframes

Switch to the **Color** page. In the timeline at the bottom of the Color page, you will see a colored bar representing your single clip. The goal now is to apply shot-specific corrections. DaVinci allows two approaches: (1) grade the entire clip with global corrections, then add overrides for problem areas using **Power Windows** (spatially selective corrections), or (2) segment the timeline into separate clips and grade each independently.

For this lab, use approach 2: break the single clip into segments at shot breaks. Go back to the **Edit** page. Right-click on your clip in the timeline and select **Split Clip** (or press **Ctrl+B**). Resolve will ask for a timecode; enter the timecode of your first shot break. The clip will split into two segments. Repeat for each shot break until you have one clip segment per shot. Now go back to the Color page; you will see multiple clips in the timeline, each with its own color correction context.

Select the first clip segment in the Color page timeline. Notice that the node graph has reset to a single **Color Corrector** node; each clip starts with a blank slate. This is intentional—it allows per-shot grading. However, you can also use **Paste Corrections** to apply a correction from one shot to another and then modify it. For now, grade the first shot from scratch.

For Shot 1 (the warm, dim interior), create a node pipeline: Right-click on the Color Corrector node and select **Add Node > Serial**. Rename it `Shot1_Exposure`. Increase gamma to brighten the dim interior (try 1.3–1.5). Check the waveform; aim to lift the bottom of the waveform to around 20–30 to reveal shadow detail. Next, add a **Curves** node (right-click > Add Node > Serial, rename `Shot1_Contrast`). Create a subtle S-curve to add contrast: click the left-third of the curve at approximately (20, 15) and drag down slightly, then click the right-third at approximately (80, 85) and drag up slightly. This deepens shadows and brightens highlights, adding punch.

Now add a **Color Balance** node for white balance correction. Rename it `Shot1_WB`. The warm tungsten interior will have a strong red/orange cast. Under **Midtones**, move the **Red/Cyan** slider toward cyan (try –30 to –50) and the **Yellow/Blue** slider toward blue (try –20 to –40). Play the clip and use the waveform and vectorscope to guide you. The vectorscope should show color balanced around the center. Adjust until skin tones look natural (a subtle peachy warmth, not orange or pale). Your Shot 1 should now be well-exposed, contrasty, and color-balanced.

Click on the second clip segment in the Color page timeline. The node graph resets. Grade Shot 2 (the bright, cool outdoor daylight) independently. Add a **Curves** node and pull down the highlights significantly (the right end of the curve should be pulled down to around (95, 80) to prevent blown highlights from the bright sky). Add a **Color Balance** node; this shot is likely blue-shifted, so move **Midtones > Blue/Yellow** toward yellow (+30 to +50) and **Midtones > Red/Cyan** toward red (+10 to +20) to warm it and neutralize the cyan cast.

Play both clips in sequence (press spacebar in the Color page timeline). Do the two shots now feel visually matched—similar brightness, similar color temperature, similar contrast? Or do they still jump abruptly? Note the transition; this is your diagnostic checkpoint.

### Exercise 3: Finished Piece & Cross-Shot Continuity Check

Render the graded multi-shot timeline. Go to the **Deliver** page, set parameters as before (H.264, 1920×1080, 23.976 fps, 8 Mbps), and name the output `Lab2_multishot_graded.mp4`. Click **Add to Render Queue** and **Start Render**.

Once complete, play the rendered file in a media player fullscreen. Focus on the shot transitions. Watch closely at each cut:

- **Brightness transition:** Does the image jump brighter or darker, or is the transition smooth?
- **Color temperature transition:** Does the shot suddenly become cooler or warmer, or is there continuity?
- **Saturation transition:** Does one shot appear more vivid than another?
- **Contrast transition:** Does the punch of contrast change abruptly?

Create a document `Lab2_continuity_check.txt` and log the transition quality:

```
Transition 1 (Shot 1 to Shot 2 at 00:00:45):
- Brightness: Smooth, well-matched
- Color temperature: Slight warm-to-cool shift, expected for interior-to-exterior
- Saturation: Matched
- Contrast: Matched
Grade: PASS—natural continuity given the lighting change

Transition 2 (Shot 2 to Shot 3 at 00:01:30):
- Brightness: Shot 3 is noticeably dimmer than Shot 2—jump is jarring
- Color temperature: Shot 3 is too blue; needs +20 on the yellow slider
- Saturation: Shot 3 is desaturated compared to Shot 2
Grade: FAIL—needs re-grading of Shot 3
```

If transitions fail the continuity check, go back to the Color page, select the offending clip, and adjust the corrections. Render again and re-check. Iterate until all transitions feel natural.

---

## Exercise 3: Fusion Compositing — Layering and Masking

### Exercise 1: Observation & Compositing Fundamentals

Create a new project: **File > New Project**, name it `Lab3_Fusion`. For this lab, you need multiple video layers: a base graded footage, a text overlay, and a graphics element. Create these using freely available tools:

**Step 1: Prepare base footage.** Use your Lab 2 graded output (`Lab2_multishot_graded.mp4`) as the base layer.

**Step 2: Create a text overlay using FFmpeg.** The drawtext filter renders text onto video. Create a simple 2-second title card with white text on black:

```bash
ffmpeg -f lavfi -i color=black:s=1920x1080:d=2 -vf \
  "drawtext=fontfile=/path/to/Arial.ttf:text='PROJECT TITLE':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2" \
  -pix_fmt yuv420p lab3_title.mp4
```

(On Windows, use `C:/Windows/Fonts/arial.ttf` for the font path; on Mac, use `/Library/Fonts/Arial.ttf`; on Linux, use `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`.)

**Step 3: Create a graphics element.** Use ImageMagick to create a 5-second colored bar or gradient:

```bash
convert -size 1920x1080 gradient:blue-cyan -annotate +960+540 "GRAPHICS ELEMENT" \
  -pointsize 48 -fill white lab3_graphic.png

ffmpeg -loop 1 -i lab3_graphic.png -c:v libx264 -t 5 -pix_fmt yuv420p lab3_graphic.mp4
```

Concatenate your three elements (title, base footage, graphics) into a single timeline:

```bash
echo "file 'lab3_title.mp4'" > concat_list.txt
echo "file 'Lab2_multishot_graded.mp4'" >> concat_list.txt
echo "file 'lab3_graphic.mp4'" >> concat_list.txt

ffmpeg -f concat -safe 0 -i concat_list.txt -c copy lab3_composite_source.mp4
```

Import `lab3_composite_source.mp4` into the Media Pool. Go to the **Edit** page and confirm the timeline shows all three segments. Now switch to the **Fusion** page (press **Ctrl+Alt+5** or **Cmd+Alt+5**). The Fusion page opens a node-based compositing environment. At first, you will see a **Loader** node (the input video) connected to a **Saver** node (the output). This is a minimal pipeline.

Fusion operates on the principle of non-destructive node graphs, similar to the Color page, but with more explicit control over compositing operations. Each node represents a layer, an effect, a blend mode, or a final output. The workflow is: load source layers → composite them together → apply effects → output the result.

### Exercise 2: Building a Multi-Layer Composite with Blending and Masking

Your goal is to composite three layers: a base video, a watermark overlay, and a credits roll. First, add a second video input (the watermark). Right-click in the Fusion node graph and select **Add Tool > Input > Loader**. A second Loader node will appear. Connect it to your watermark file by double-clicking the new Loader and navigating to `lab3_graphic.mp4` in the **Clip** field.

Now add a **Merge** node to combine the two Loaders. Right-click and select **Add Tool > Composite > Merge**. The Merge node combines two or more inputs using blend modes. Connect the first Loader's **Image** output to the Merge node's **Background** input, and the second Loader's **Image** output to the Merge node's **Foreground** input. The Merge node will now composite the graphic over the base footage.

By default, the Merge uses an **Operation** of "Over," which treats the foreground as opaque and places it on top. This is correct for a watermark. However, you likely want the watermark to be semi-transparent (a typical watermark opacity is 30–50%). In the Merge node's Inspector (right panel), find the **Foreground Opacity** slider and reduce it to 0.4 (40% opacity). The watermark will now appear translucent over the base footage.

Play the Fusion timeline by pressing spacebar in the node editor. You will see the base footage with the semi-transparent graphic overlay. If the graphic is positioned at the top-left and you want it centered, you need to add a **Transform** node to reposition it. Right-click and select **Add Tool > Transform > Transform**. Connect the second Loader's output to the Transform node, then connect the Transform node to the Merge's Foreground input (delete the direct connection first by clicking it and pressing Delete). In the Transform Inspector, set **Center X** to 960 (half of 1920) and **Center Y** to 540 (half of 1080) to center the graphic.

Now add a third input for credits text. Create a text file called `credits.txt`:

```
Directed by [Your Name]
Produced by [Your Name]
Cinematography by [Your Name]
Sound Design by [Your Name]
Music by [Your Name]
```

Create a video of scrolling credits using FFmpeg:

```bash
ffmpeg -f lavfi -i color=black:s=1920x1080:d=10 -vf \
  "drawtext=textfile=credits.txt:fontfile=/path/to/Arial.ttf:fontcolor=white:fontsize=36:x=(w-text_w)/2:y=100+(t*50):line_spacing=50" \
  -pix_fmt yuv420p lab3_credits.mp4
```

This creates a 10-second video with text that scrolls downward at 50 pixels per second. Import `lab3_credits.mp4` into the Media Pool. Add a third Loader in Fusion to reference this file. Add another Merge node to composite the credits over the existing composite. Connect the first Merge's output (Background) to this new Merge's Background input, and the third Loader (credits) to the new Merge's Foreground input. Set the new Merge's Foreground Opacity to 0.6 (60% opaque for readability).

Your node graph now reads: Loader 1 (base) → Merge 1 (with Loader 2 watermark and Transform) → Merge 2 (with Loader 3 credits) → Saver (output). Play the timeline; you should see base footage with a centered semi-transparent watermark and scrolling credits.

Now add an effect to the final composite. Right-click and select **Add Tool > Color > ColorCorrector**. This is a simplified color correction node for quick tweaks in Fusion. Connect the second Merge node's output (the final composite) to the ColorCorrector, and connect the ColorCorrector to the Saver. In the ColorCorrector Inspector, increase **Saturation** to 1.1 to make the composite slightly more vivid. This subtle boost makes overlays pop and gives the final output a polished look.

Your Fusion graph is now complete: three inputs, two compositing layers, one transform, one color correction, and one output. This is a professional multi-layer compositing pipeline.

### Exercise 3: Finished Piece & Composite Verification

Verify your Fusion timeline by playing it in the node editor. Check:

- **Layering order:** Base → watermark → credits (correct z-order?)
- **Opacity blending:** Watermark and credits are readable but not opaque (do they look natural?)
- **Positioning:** Watermark is centered, credits scroll from top to bottom (correct placement?)
- **Color boost:** The final composite appears slightly more saturated than the base (is the effect visible but not overdone?)

If any element is misaligned or the opacity is wrong, adjust the Transform or Merge nodes and re-play to verify. Once satisfied, render the Fusion timeline. At the bottom of the Fusion page, click the **Deliver** button (or switch to the Deliver page). Set parameters:

- **Video Format:** ProRes 422 HQ (professional-grade codec for editing and archival)
- **Resolution:** 1920×1080
- **Frame Rate:** 23.976 fps
- **Output Path:** `Lab3_composite_final.mov`

Click **Add to Render Queue** and **Start Render**. Resolve will encode the Fusion timeline with all layers, effects, and color corrections baked in. Once complete, open `Lab3_composite_final.mov` in a media player fullscreen.

Verify the composite:

```
Checkpoint 1: Base footage visibility and color
- Is the base graded footage visible beneath overlays?
- Does the color grading from Lab 2 carry through?

Checkpoint 2: Watermark placement and opacity
- Is the watermark centered on screen?
- Is it readable but not too prominent?
- Does it maintain consistent opacity throughout?

Checkpoint 3: Credits readability
- Do credits scroll smoothly from top to bottom?
- Are they white text on a dark background, readable?
- Is the scroll speed appropriate (not too fast, not too slow)?

Checkpoint 4: Overall polish
- Do the layers feel intentionally composed, not stacked haphazardly?
- Is the final saturation boost noticeable but tasteful?
- Are there any visual glitches, dropped frames, or artifacts?
```

Create a file `Lab3_composite_verification.txt` and log your findings. Example:

```
Checkpoint 1: PASS—base footage is visible and color-graded throughout
Checkpoint 2: PASS—watermark is centered and 40% opaque, readable
Checkpoint 3: PASS—credits scroll smoothly, white text is readable against black
Checkpoint 4: PASS—saturation boost is subtle, final composite looks professional

Overall: PASS—Fusion timeline is production-ready
```

---

## Critique Checklist & Common Fixes

### Color Grading Diagnostic Rubric

After completing any color grading work, use this checklist to verify technical and aesthetic quality:

**Technical Correctness:**

1. **Luminance Range (Waveform Monitor):** The waveform should span from approximately 5 to 95, with no clipping at 0 (pure black) or 100 (pure white) unless intentional. If the waveform is bunched to the left (shadows), increase gamma or lift shadows with curves. If clipped to the right (highlights), decrease gain or pull down the highlights with curves. If the range is narrow (flat, low contrast), increase contrast via curves or the contrast slider. If the range is exaggerated (extreme blacks and whites), lower contrast.

2. **Color Balance (Vectorscope):** The vectorscope should show a small cloud of points centered around the middle (neutral). If the cloud is biased toward red or cyan, adjust **Red/Cyan** in Color Balance. If biased toward green or magenta, adjust **Green/Magenta**. If biased toward yellow or blue, adjust **Yellow/Blue**. For neutral grading, the cloud should be small and central; for stylized grading (e.g., intentional warm cast for a nostalgic look), the cloud can be offset, but the offset should be deliberate and consistent across the shot.

3. **Histogram Clipping:** The histogram should show no towers at either extreme (0 or 100) unless intentional (e.g., silhouette shots may clip blacks). If you see towers at the extremes in a normal exposure, adjust curves or exposure to prevent clipping.

**Aesthetic Quality:**

4. **Skin Tone Naturalism:** Zoom in on any faces in the footage using the **Zoom** tool or by adjusting the viewer scale. Skin tones should appear warm (peachy, with a bias toward red and yellow) but not orange or sickly. Use the color picker tool (press **I** in the viewer) to sample a skin tone and check its color coordinates. A neutral skin tone sits at approximately 30–40% red, 20–30% green, and 10–20% blue in normalized RGB space. If skin appears too cyan or green, add red to the midtones.

5. **Sky and Water Colors:** Skies should appear blue or cyan depending on time of day (morning/evening skies can be more orange, midday skies more saturated blue). Water should reflect the sky but be slightly desaturated. If a sky appears washed out or greenish, increase saturation selectively using a **Power Window** (see below) or add blue to the highlights.

6. **Shadow Detail:** Shadows should reveal detail (texture, form) without appearing muddy or overly lifted. If shadows are crushed (pure black with no detail), lift them. If they are overlifted (looking bleached and flat), reduce the lift. The sweet spot is when shadow areas are dark but reveal object geometry and surface texture.

7. **Highlight Compression:** Highlights should appear bright but not blown (pure white with no detail). Specular highlights (reflections on glass, metal, water) can be blown intentionally for sparkle, but large highlight areas (sky, walls) should retain detail. If highlights are blown, reduce gain or pull down the highlight curve.

**Continuity (Multi-Shot Sequences):**

8. **Shot-to-Shot Brightness Matching:** At each cut, the brightness should not jump abruptly unless the narrative intent is to show a lighting change (e.g., interior to exterior). Play the sequence and watch the waveform at each cut; it should not suddenly spike or drop. If it does, re-grade the offending shot to match.

9. **Shot-to-Shot Color Matching:** Color temperature should be consistent across connected shots unless a narrative lighting change is intentional. The vectorscope should show similar color biases across shots. If one shot is visibly cooler or warmer than the next, adjust Color Balance to match.

10. **Shot-to-Shot Contrast Matching:** Contrast should be consistent to avoid visible jumps in image texture and snappiness. If one shot has a flat S-curve and the next has an aggressive S-curve, the contrast will feel different. Use identical curve shapes across connected shots as a baseline, then adjust for shot-specific needs.

### Common Fixes for Typical Grading Problems

**Problem: Underexposed Footage (too dark, waveform bunched to the left)**

Fix: In a **Curves** node, lift the entire curve upward (click and drag the middle of the curve up), or increase **Gamma** in the global luma controls to 1.2–1.5. If only shadows are dark and midtones are correct, click the left-third of the curve and drag up. Use the waveform to verify that the entire range is now distributed properly. Avoid lifting gamma too high, which will blow highlights.

**Problem: Overexposed Footage (too bright, waveform clipped to the right)**

Fix: In a **Curves** node, pull down the right end of the curve (highlights) to prevent clipping. Reduce **Gain** to darken the image uniformly while preserving blacks. If midtones are blown but shadows are correct, create a gentle downward curve in the midtone range (click the middle and drag down). Check the waveform; the right end should no longer be clipped.

**Problem: Flat Contrast (image looks dull and lifeless)**

Fix: In a **Curves** node, create an S-curve: click the left-third of the curve at approximately (20, 15) and drag down slightly to deepen shadows; click the right-third at approximately (80, 85) and drag up to brighten highlights. The curve becomes a gentle S-shape. This spread increases perceived contrast and makes the image "pop." Alternatively, increase the **Contrast** slider in the global luma controls to 1.1–1.2. Verify with the histogram and waveform that the range has expanded.

**Problem: Crushed Blacks (shadows appear as pure black with no texture or detail)**

Fix: In a **Curves** node, lift the left end of the curve upward (shadows) to reveal detail. Alternatively, in **Color Balance**, increase the **Shadows > Offset** to brighten the darkest areas. Use the waveform to ensure that the left end (blacks) is lifted to around 5–10 instead of clipping at 0. Balance this with contrast; if shadows are lifted, you may need to increase overall contrast to compensate.

**Problem: Blown Highlights (bright areas appear as pure white with no detail)**

Fix: In a **Curves** node, pull down the right end of the curve to compress highlights. Alternatively, reduce **Gain** to darken highlights while preserving midtones. Use the waveform to ensure that the right end (highlights) is compressed to around 90–95 instead of clipping at 100. If only specular highlights (reflections) are blown and you want to preserve them, use a **Power Window** to selectively pull down only the blown area.

**Problem: Blue or Cyan Color Cast (image appears too cool)**

Fix: In a **Color Balance** node, move **Midtones > Blue/Yellow** toward yellow (increase the value, e.g., +30 to +50). If the entire image is affected, adjust Shadows and Highlights separately. Use the vectorscope to verify that the blue bias is reduced and the cloud moves toward the center or toward yellow. If only highlights are blue, adjust **Highlights > Blue/Yellow** without touching Midtones.

**Problem: Orange or Warm Color Cast (image appears too warm)**

Fix: In a **Color Balance** node, move **Midtones > Blue/Yellow** toward blue (decrease the value, e.g., –30 to –50). Additionally, move **Midtones > Red/Cyan** toward cyan (decrease the value) to reduce orange. Use the vectorscope to verify that the warm bias is reduced. If the cast is due to tungsten lighting, this is a standard white balance correction.

**Problem: Green or Magenta Tint (image appears sickly or unnatural)**

Fix: In a **Color Balance** node, move **Midtones > Green/Magenta** toward the opposite hue. If the image is too green, move toward magenta (increase the value). If too magenta, move toward green (decrease the value). Green casts are common in fluorescent-lit interiors; magenta casts are common in some LED or sodium-vapor lighting. Use the vectorscope to guide your adjustment; the color should return to neutral or the intended palette.

**Problem: Desaturated or Dull Colors (image lacks vibrancy)**

Fix: In a **Color Balance** or **Saturation** control, increase saturation to 1.1–1.2. Alternatively, in a **Curves** node, increase the **Saturation** parameter if available. Some color casters (like fluorescent or old camera sensors) produce inherently desaturated images; a 10–20% saturation boost often restores vibrancy. Use the vectorscope to verify that color activity increases; the cloud should spread away from the center, indicating more saturated colors.

**Problem: Over-Saturated Colors (image looks garish or posterized)**

Fix: Reduce saturation to 0.8–0.9 in the **Color Balance** or **Saturation** control. Over-saturation can make skin tones look artificial and can cause banding in gradient areas (e.g., skies). Check the vectorscope; if the cloud is very large and far from center, reduce saturation. For stylized looks (e.g., 1970s color grading with high saturation), over-saturation can be intentional, but it should be a deliberate creative choice, not an accident.

**Problem: Shot-to-Shot Brightness Jump (one shot is suddenly brighter than the previous)**

Fix: Select the offending clip in the Color page. In the **Curves** node, adjust the overall brightness to match the previous shot. Use the waveform scopes on both shots simultaneously (enable dual-clip view if available) to match waveform distributions. If the brightness jump is due to aperture or exposure differences in original footage, this correction is essential. If the jump is due to lighting changes (e.g., interior to exterior), it may be intentional, but verify by watching the sequence.

**Problem: Shot-to-Shot Color Temperature Mismatch (one shot is cooler or warmer)**

Fix: In a **Color Balance** node, adjust **Blue/Yellow** to warm or cool the shot to match the previous shot. Use the vectorscope to verify that the hue bias matches between shots. If one shot is shot indoors (tungsten) and another outdoors (daylight), some color shift is natural, but the shift should not be jarring. Grade each shot so that the color shift feels intentional and contextual (e.g., moving from warm interior to cool exterior).

**Problem: Fusion Composite Layers Not Blending Correctly (layers look stacked, not composited)**

Fix: Verify that all Loader inputs are connected to Merge nodes in the correct order. The first Loader should feed the **Background** input of the first Merge; subsequent layers should feed the **Foreground** input. Use **Merge > Operation: Over** for opaque blending or **Multiply** for darkening blends. If the blend mode is incorrect, the layers will appear separate. Additionally, check the **Foreground Opacity**; if it is set to 1.0, the foreground is fully opaque and obscures the background entirely.

**Problem: Fusion Composite Text or Graphics Misaligned (not centered or positioned incorrectly)**

Fix: Add a **Transform** node between the Loader and the Merge. In the Transform Inspector, adjust **Center X** and **Center Y** to reposition. For centering: **Center X = 960** (half of 1920), **Center Y = 540** (half of 1080). For offset positioning, adjust these values accordingly. If the element is too small or too large, increase or decrease the **Scale** slider (default is 1.0; 1.5 enlarges by 50%, 0.5 shrinks by 50%). Use the viewer to verify placement in real-time.

**Problem: Rendered Output Does Not Match Viewer Preview**

Fix: This often occurs due to cache inconsistencies. In the Color page or Fusion page, go to **Workspace > Cache > Flush All Caches**. Resolve will clear cached frames and re-render the timeline. This can take time, but it ensures that the render reflects the current node graph. Additionally, verify that the **Delivery** codec and resolution match your project settings; mismatches can cause subtle color shifts or resolution downsampling.

---

## Summary and Next Steps

You have completed three progressive laboratory exercises in DaVinci Resolve's color grading and Fusion compositing workflows. Lab 1 established non-destructive node architecture and introduced diagnostic scopes (waveform, histogram, vectorscope). Lab 2 extended this to multi-shot grading, using clip-based corrections to maintain visual continuity across cuts. Lab 3 integrated Fusion compositing, layering multiple sources, and applying effects to create a polished final output.

The skills you have practiced—observing color characteristics, building correction nodes, managing exposure and color balance, and verifying quality using scopes—form the foundation of professional color grading and compositing. The diagnostic rubric and common fixes guide you through the most frequent challenges. As you continue working in Resolve, refer to this rubric, experiment with more complex node graphs (e.g., Power Windows for selective corrections, Fusion's keyframe animation for dynamic compositing), and develop your eye for color and contrast through repeated practice and critique.

The next level of mastery involves advanced techniques: **Power Windows and Tracking** (spatially selective corrections that follow moving subjects), **Keyframe Animation** (time-varying color and effect changes), **LUT Application** (look-up tables for creative color grading), and **3D Compositing** (depth compositing with Z-depth passes in Fusion). These are covered in advanced Resolve courses; for now, solidify your foundation with the exercises above, and return to this guide whenever you encounter a grading or compositing challenge.
