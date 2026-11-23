# Studio Practice Labs: Video Production

## Objective & Studio Setup

This laboratory sequence develops foundational competence in video production through direct practice with image capture, editorial decision-making, and temporal composition. You will work from raw camera footage or captured sequences through color correction and final delivery, developing the visual and technical judgment required to tell stories through video. The exercises progress from observation of light and exposure to the construction of coherent narrative sequences to mastery of output workflows that preserve image quality across distribution platforms.

Video production demands simultaneous mastery of three distinct skill domains: *capture and exposure* (how light becomes data), *temporal composition* (how shots arrange into meaning), and *technical delivery* (how finished work survives compression and playback). This lab synthesizes all three through iterative work with industry-standard software and real source material.

### Studio Setup Requirements

You will need **DaVinci Resolve Studio** (version 19.0 or later; the free version omits certain grading tools but suffices for editing fundamentals). If you lack raw camera footage, download the **publicly available raw footage library** maintained by IMAX and Red Digital Cinema, or capture your own material using any camera capable of recording 1080p minimum (smartphone, mirrorless, cinema camera—the technique transcends the hardware).

Establish a **color-grading reference monitor** setup: position your display in a dim environment (not bright daylight) with ambient light controlled to 5–10 footcandles, and calibrate using either the **X-Rite i1Display Pro** probe or **Datacolor SpyderX Elite** suite for accurate sRGB/Rec.709 reference. If hardware calibration is unavailable, download the **DaVinci Resolve Built-In Reference** LUT and apply it to your working timeline. For every exercise, use a **hardware waveform monitor** (or Resolve's native **Waveform Monitor** and **Vectorscope** overlays) to verify exposure and color data rather than trusting your eye alone; the human visual system adapts to lighting conditions and lies about absolute luminance.

Maintain a **reference folder** containing at least three exemplary sequences from published films or documentaries in your chosen genre (narrative, documentary, commercial, or music-driven). Download them at the highest available quality and ingest them into Resolve as *offline media* to study without playback stuttering. Keep **scratch drive storage** at a minimum of 500 GB free; video editing consumes vast temporary space for cache, proxies, and render outputs.

---

## Exercise 1: Observation & Fundamentals Drill — Reading Light and Exposure

The foundation of video production rests on understanding how light becomes electrical signal, how cameras render that signal into image data, and how to recognize when exposure deviates from intentional aesthetic choice. This exercise trains your eye to read luminance distribution, detect clipping and crushed blacks, and diagnose exposure problems before they propagate through a full project.

### Part A: Waveform Literacy and Exposure Analysis

Open DaVinci Resolve and create a new project named `Lab_01_Exposure_Study`. Set the project frame rate to **23.976 fps** (industry standard for narrative cinema) and resolution to **1920×1080** (broadcast video standard). Create a new timeline in that project and name it `Waveform_Reference`.

Download the **publicly available test footage** from the RED Digital Cinema repository or use this sequence: open the **DaVinci Resolve sample gallery** (Help → Sample Media) and import any scene with varied lighting—indoor/outdoor mix or sunset sequences work best. Place a 2–3 minute clip into the timeline.

Now enable the **Waveform Monitor** in the Color page. Navigate to DaVinci Resolve's **Color** workspace (button in top right), click the **Viewer Options** button (three horizontal lines, top right of main viewer), and select **Waveform Monitor**. Set the display to **Full Range** (0–1023 IRE, standard for cinema DCP work) rather than broadcast safe (0–940 IRE). Play the sequence and observe the waveform in real time.

The waveform display reveals luminance distribution as a vertical histogram: the horizontal axis spans the frame left to right; the vertical axis spans from black (bottom) to white (top). Peaks touching the top (1023 IRE) indicate clipped highlights; peaks touching the bottom (0 IRE) indicate crushed blacks. Healthy mid-tone video occupies the center region (256–768 IRE, roughly 25–75% of the full range).

Identify three distinct moments in your test footage:

1. **Overexposed highlight**: a bright window, sky, or reflective surface where the waveform peaks above 900 IRE. Pause on this frame. Note the timestamp (DaVinci shows timecode in the top left of the viewer). Record the timecode in a text file named `Exposure_Log.txt`.

2. **Crushed shadow**: a dark corner, interior shadow, or backlighting silhouette where the waveform dips below 64 IRE. Pause and record the timecode.

3. **Intentional aesthetic clipping**: a creative choice—perhaps a flare, a blown sky background deliberately desaturated, or a low-key dramatic scene where blacks are crushed intentionally for mood. Record this timecode and annotate it with the word `INTENTIONAL` in your log.

For each timestamp, right-click on the frame in the viewer and select **Capture Still Frame**. DaVinci will export a frozen image to the **Gallery** in the Color page. You now have three reference stills that you can compare side by side by opening them in an image viewer or by dragging them into a contact sheet. The purpose is to train your eye to distinguish technical failure (accidental clipping due to camera misexposure or poor dynamic range management) from artistic intent (purposeful use of crushed values for mood or genre convention).

Write a one-paragraph observation in `Exposure_Log.txt` for each frame:

```text
Timestamp: 00:01:23:15
Type: Overexposed Highlight
Analysis: The waveform peak at this window reaches 950 IRE. The bright area is a south-facing window at midday. 
In broadcast work, this would be unacceptable; in cinema DCP grading, this is recoverable through crushed highlight recovery 
(pulling the white point down in the Curves panel). However, the surrounding skin tones remain at 450–550 IRE (healthy), 
so this is a local exposure problem, not a global overexposure. Recovery: apply a Power Window mask around the window, 
use the Curves panel to drag the highlight knee down to 850 IRE, and increase the saturation to prevent desaturation 
artifacts common in blown-out recovery.

Timestamp: 00:03:47:08
Type: Crushed Shadow
Analysis: A corner of the room falls to 32 IRE. The waveform shows a sharp cliff at the bottom. This is intentional; 
the cinematographer lit this scene with key light hitting the face and rim light on the hair, leaving the background 
very dark for compositional separation. Lifting these blacks would flatten the image. Decision: preserve the crush.

Timestamp: 00:08:12:22
Type: Intentional Aesthetic Clipping
Analysis: A sunset sky over water reaches 980 IRE at the top edge. Mid-tones in the landscape are 400–600 IRE. 
The clipped sky is a classic cinematography choice: expose for the subject (the landscape), and let the sky burn out. 
This prevents an unnatural-looking sky in log color space and maintains golden-hour warmth in the landscape. 
Decision: This is correct exposure, not a problem.
```

This exercise trains pattern recognition. Repeat the process with two more sequences from your reference folder. The goal is to recognize the *signature* of different exposure choices: backlit scenes often have crushed shadows and bright rim light; front-lit interiors often have blown windows; silhouette scenes deliberately crush both shadows and midtones.

### Part B: Dynamic Range Capture and Camera Log Space

Switch to a new timeline named `Log_Space_Comparison`. The camera data you captured in Part A was likely recorded in one of three color spaces: *Rec.709* (broadcast video, compressed dynamic range, 0–1023 IRE), *S-Log* (Sony), *C-Log* (Canon), or *RED Log3G10* (RED cameras). These are **logarithmic** color spaces, designed to preserve maximum tonal information by compressing the highlights and expanding the shadows.

Download a **RAW or Log-recorded sequence** if your test footage from Part A was already corrected to Rec.709. The DaVinci Resolve sample gallery includes several log-recorded clips. Import one and place it into the timeline.

The first time you see log footage, it appears washed out and greenish—this is not degradation, but *maximum tonal information compressed into a visually flat intermediate state*. This flatness is intentional: it preserves information in both the brightest and darkest regions of the frame that would be lost if the camera baked in Rec.709 gamma correction at capture time.

In the **Color** page, observe the waveform and **Vectorscope** (also in Viewer Options). The vectorscope displays color saturation and hue as a polar plot: red at 0°, yellow at 60°, green at 120°, cyan at 180°, blue at 240°, magenta at 300°. In log space, the vectorscope will appear very compact and desaturated—this is correct. The image will look muddy; resist the temptation to crush blacks or oversaturate at this stage.

Now you will apply a **LUT** (Look-Up Table)—a mathematical transformation that remaps pixel values from log space into display-referred (Rec.709) space. In the Color page, open the **LUT Browser** (the button showing "LUT" in the bottom left of the Color panel). Select the LUT corresponding to your camera: if the clip came from a RED camera, choose **RED Log3G10 to Rec.709**; for Sony, choose **S-Log to Rec.709**; for Canon, **C-Log to Rec.709**.

Apply the LUT by dragging it onto the clip in the timeline. The image will transform: the washed-out appearance will give way to normal video, the blacks will deepen, and the colors will saturate. The waveform will now occupy the full 0–1023 IRE range; the vectorscope will fill the color wheel. This transformation does **not** change the underlying data; it only remaps how that data is displayed. The log data is still there, compressed in the file, ready for regrade.

Compare the log waveform to the LUT-corrected waveform by toggling the LUT on and off using the **Bypass** button (the circular arrow in the LUT panel). Notice how the same underlying data redistributes across the full range. This is the core insight: **log space preserves information; display space shows information**.

Write in `Exposure_Log.txt`:

```text
Timestamp: (timestamp of your log clip start)
Log Space vs. Display-Referred Comparison
Raw log appearance: washed, greenish, low saturation
Waveform spread: compressed into middle 25% of range (centered ~400–600 IRE)
Vectorscope: compact, cluster near center
Post-LUT appearance: normal video, saturated, full contrast
Waveform spread: fills 0–1023 IRE, blacks at 0, whites at 1023
Vectorscope: expands to fill color wheel
Insight: The LUT mathematically stretches the compressed log data to match human display perception. 
No information is lost in this transformation; we are simply changing the representation. This is why 
high-end cameras record in log: maximum information is preserved for grading flexibility.
```

### Part C: Practical Exposure for Capture

Open a new timeline named `Capture_Planning`. You will now apply what you've learned by planning an actual shoot or by analyzing a shoot you will perform.

If you have access to a camera (smartphone, mirrorless, cinema camera), plan a short sequence: **three shots, 30 seconds total, varied lighting conditions**. Use the notes below to set exposure *during capture*, not intending to fix it in post.

**Shot 1: Daytime Interior with Bright Window**
- Position your subject (a person, object, or simply a room corner) so a bright window is *behind* or *to the side* of the subject.
- Set camera exposure so the subject's face (or primary object) is metered at 40–50% brightness on your camera's light meter (or at the two-thirds mark if your camera shows a histogram). This will push the window toward 90–100% brightness.
- If your camera has *highlight warning* (most mirrorless cameras show blinking areas for clipped highlights), enable it. Adjust until you have *minimal* clipping in the window.
- Record 10 seconds of static camera; do not move.
- **Principle**: Expose for the subject, not the background. Bright windows are normally rendered slightly blown; this is correct cinema practice.

**Shot 2: Dimly Lit Interior or Evening Exterior**
- Choose a location with low natural light: an interior room with lights off, or an outdoor scene during the blue hour (20–40 minutes after sunset).
- Set exposure so the dominant shadow area (a wall, ground, or person's chin/neck in shadow) meters at 20–30% brightness.
- Do *not* boost the ISO to artifially brighten the frame. Instead, use a wider aperture (smaller f-number: f/2.8 or f/4) or longer shutter speed (if the camera is static, use 1/48 second or slower).
- Record 10 seconds.
- **Principle**: Low-key lighting preserves shadow detail by metering for shadows, not highlights. This creates mood through contrast, not through crushed blacks.

**Shot 3: Mixed Lighting (Tungsten + Daylight)**
- Position your subject so they are lit by both artificial light (indoor tungsten bulbs at ~3000 K) and natural window light (daylight at ~5500 K).
- Set the camera's white balance to **5500 K (Daylight)** or **auto white balance**. This will render the tungsten side of the face warm (orange) and the daylight side cool (blue).
- Expose so the subject's face is at 50–60% brightness.
- Record 10 seconds.
- **Principle**: Mixed color temperature reveals the camera's white balance setting and the cinematographer's color intentionality. This is not an error; it is a storytelling choice (warmth vs. coolness implies emotional association).

Ingest all three shots into DaVinci Resolve. Create a timeline named `Capture_Analysis` and place the three clips end to end (Shot 1 → Shot 2 → Shot 3). Enable the **Waveform Monitor** and **Vectorscope**.

For each shot, pause at the midpoint and document in a file named `Capture_Report.txt`:

```text
SHOT 1: Daytime Interior with Bright Window
Duration: 10 seconds
Subject metering: ~45% brightness (healthy)
Window metering: ~92% brightness (slight clip acceptable)
Waveform: Peaks touch 950–980 IRE at window; subject peaks at 450–500 IRE; shadows at 100–150 IRE
Vectorscope: Warm cast in window area (orange toward 60° on color wheel); neutral face (center cluster)
Decision: Correct exposure. The blown window is intentional separation; subject is properly exposed.

SHOT 2: Dimly Lit Interior
Duration: 10 seconds
Shadow area metering: ~25% brightness
Highlight metering: ~65% brightness (desk lamp or fill light)
Waveform: Compressed into lower half, 50–600 IRE, with sharp cliff at bottom where shadows crush
Vectorscope: Desaturated, neutral cast (warm tungsten light is desaturated by metering; blue shadows create color split)
Decision: Correct exposure for low-key lighting. The crushed blacks are intentional. The color split (warm fill, cool shadow ambient) is a natural artifact of mixed tungsten fill with cooler room ambient.

SHOT 3: Mixed Lighting
Duration: 10 seconds
Warm side (tungsten): 55% brightness, strong orange cast (hue ~40–50° on vectorscope)
Cool side (daylight): 55% brightness, slight blue cast (hue ~200–210° on vectorscope)
Waveform: Face is centered around 450–550 IRE on both sides; color information is split across the vectorscope
Vectorscope: Shows a "line" or "smear" of color data from orange to blue, indicating color temperature split
Decision: Correct exposure with intentional color split. This shot demonstrates how white balance setting plus mixed light sources create color storytelling. In the grade, you might push this split further (increase saturation of the warm side, cool the cool side) or neutralize it.
```

---

## Exercise 2: Technique Study, Step by Step — Building Editorial Sequences

Editorial theory teaches that meaning in video emerges not from individual shots, but from the *relationship between shots*: how cuts occur, what juxtaposition reveals, and how temporal rhythm guides the viewer's emotional response. This exercise trains the construction of coherent sequences through deliberate editing choices, guided by the classic Soviet montage theory and refined by contemporary documentary and narrative practice.

### Part A: Shot Sequence and Continuity Editing

Create a new project named `Lab_02_Editorial_Study`. Set up a timeline named `Continuity_Build` at 23.976 fps, 1920×1080.

You will now ingest or download a **simple, actor-driven sequence** with multiple takes of the same action from different angles. This is crucial: ideally, find a scene with a person entering a room, sitting at a desk, and picking up a phone. The sequence should have:

- **Wide Shot (WS)**: full body, standing in doorway
- **Medium Shot (MS)**: waist-up, entering room, moving toward desk  
- **Close-Up (CU)**: hands on desk, reaching for phone
- **Reaction CU**: face, as phone is picked up
- **Insert CU**: phone screen (or similar detail)

If you don't have this footage, download the **Tearoom Video Test Sequence** from the University of Tokyo or use a scene from a published short film where you can identify multiple angles of one action. Alternatively, **record this sequence yourself** using a smartphone or camera: record the same actor performing the action from each angle (five takes, minimum 30 seconds each), then import all into Resolve.

Place the shots into the timeline in this order: **WS (3 sec) → MS (3 sec) → CU hands (2 sec) → Reaction CU (2 sec) → Insert CU (2 sec)**. Total sequence: 12 seconds.

Play the timeline. This is **continuity editing**—the foundation of all narrative film. Each shot reveals new spatial or temporal information while maintaining the illusion of unbroken action. The viewer does not notice the cuts because each cut reveals what they want to see next (a principle called *motivated cutting*).

Now intentionally break continuity by reordering the shots: **CU hands (2 sec) → WS (3 sec) → Reaction CU (2 sec) → MS (3 sec) → Insert CU (2 sec)**. Play this version. The viewer feels disorientation—they see hands reaching for a phone before they know where the hands are located in space. The wide shot appears as though time has jumped backward. The reaction feels premature. This is **bad continuity**.

In a new version, try **creating rhythm through repetition**: **WS → MS → CU hands → WS (repeat) → CU hands (again) → Reaction CU**. This repeating pattern creates anticipation; the return to the wide shot feels like a breath before the climactic close-up. This is intentional violation of pure continuity to serve emotional pacing.

Document your three edits in a file named `Editorial_Decisions.txt`:

```text
EDIT 1: Continuity Order
Sequence: WS → MS → CU Hands → Reaction CU → Insert CU
Cut timing: 3 sec / 3 sec / 2 sec / 2 sec / 2 sec
Viewer experience: Smooth spatial progression; brain tracks actor's position easily; cuts feel motivated
Continuity principle: Each cut reveals the next expected detail (from wide to close, spatially coherent)
Critique: Technically correct; emotionally neutral; serves information delivery but no stylistic intent

EDIT 2: Broken Continuity (Intentional)
Sequence: CU Hands → WS → Reaction CU → MS → Insert CU
Cut timing: 2 sec / 3 sec / 2 sec / 3 sec / 2 sec
Viewer experience: Jarring; spatial logic feels scrambled; timestamps appear nonlinear
Critique: Disorienting and ineffective; this violates continuity without serving a narrative purpose

EDIT 3: Rhythm Through Repetition
Sequence: WS → MS → CU Hands → WS (repeat) → CU Hands (again) → Reaction CU → Insert CU
Cut timing: 3 sec / 3 sec / 2 sec / 2 sec / 2 sec / 2 sec / 2 sec
Viewer experience: Anticipatory; the return to WS feels like a held breath; repetition builds tension before the final reaction
Continuity principle: Breaking pure continuity to serve pacing and emotional arc; return to WS is motivated by desire to build suspense
Critique: Stylistically intentional; mimics the actor's inner hesitation (repeating the motion before committing to the action)
```

### Part B: Shot Scale and Visual Storytelling

Create a new timeline named `Scale_Study`. Download or record a **monologue or interview sequence** (a person speaking directly to camera for 60–90 seconds). Ideally, capture this in three scales:

- **Wide Shot**: actor full-body, against a background (a room, landscape, or location that reveals context)
- **Medium Shot**: actor waist-up, background still visible but softer or partial
- **Close-Up**: actor face only, background blurred or completely dark

If you don't have this footage, find a **TED Talk, interview clip, or dramatic monologue** (search "close-up acting" on YouTube; many acting reels contain excellent monologue material in multiple scales).

Place the monologue into the timeline as follows, cutting every 10–15 seconds:

```text
Timeline version 1: Static Wide Shot
One continuous 60-second wide shot. No cuts. The actor speaks the entire monologue at the same scale.

Timeline version 2: Progressive Close-Up
Wide Shot (15 sec) → Medium Shot (15 sec) → Close-Up (15 sec) → Repeat MS (10 sec) → CU (5 sec)
This creates a *push into intimacy*—as the monologue intensifies, the camera appears to move closer to the actor,
drawing the viewer into emotional proximity.

Timeline version 3: Reactive Cutting
Wide Shot (5 sec) → Medium Shot (10 sec) → Close-Up (5 sec, reaction moment) → Medium Shot (10 sec, continuation) → Close-Up (8 sec, climax)
Cut based on the emotional *content* of the speech, not merely time. Where the actor emphasizes a word or changes emotional tone,
cut to close-up to magnify that moment. Where the actor is contemplative, cut to wide or medium to create space.
```

For each version, play it at full resolution and assess in `Editorial_Decisions.txt`:

```text
VERSION 1: Static Wide Shot
Duration: 60 seconds, one cut-free take
Effect: Meditative, distant. The viewer observes the actor as though watching from across a room. 
Emotion: Neutral, reportorial. Best suited for documentary observation (a scientist explaining research, 
an interview subject answering questions).
Technical critique: No coverage problems; no need for color correction across cuts. 
Weakness: Difficult for the viewer to maintain emotional connection over 60 seconds without cut variation.

VERSION 2: Progressive Close-Up
Duration: 60 seconds, five cuts
Cut timing: 15 sec (WS) / 15 sec (MS) / 15 sec (CU) / 10 sec (MS) / 5 sec (CU)
Effect: Increasing intimacy; the viewer is drawn closer to the actor's face as the monologue advances.
Emotion: Building investment; climactic focus in the final close-up.
Technical: Progressive close-ups magnify any color inconsistency or white balance shift between takes; 
color correction must be coordinated across scales.
Strength: Naturally guides attention; mimics cinematic convention (beginning with establishing shot, 
ending in close-up for emotional climax).

VERSION 3: Reactive Cutting
Duration: 60 seconds, six cuts (timings varied based on speech rhythm)
Effect: Cuts synchronized to meaning (emphasis in speech = close-up; reflection = wider view).
Emotion: Dynamic, responsive to the actor's internal state.
Technical: Demands precise identification of emotional beats; misplaced cuts feel arbitrary.
Strength: Maximum storytelling efficiency; each cut carries intentionality.
Weakness: Requires sophisticated editorial judgment; can feel manipulative if overused.
Critique: This version demands the most skill and delivers the most sophisticated result.
```

### Part C: Montage and Juxtaposition

Create a new timeline named `Montage_Study`. Montage is the deliberate use of rapid cuts and juxtaposed images to create meaning through collision rather than continuity. Soviet pioneer Sergei Eisenstein developed **Montage of Attractions**: the idea that the *gap between two shots* creates meaning in the viewer's mind that neither shot contains alone.

Collect **five disparate still images or short clips** (5–10 seconds each). Themes can be:

- **Sequence A**: Sunrise (or time progression)
  - Clock at 6:00 AM
  - Doorway with morning light
  - Window with shadows shortening
  - Person pouring coffee
  - Window with high sun (9:00 AM)

- **Sequence B**: Arrival (or emotional arrival)
  - Car pulling into parking lot
  - Footsteps on pavement (audio focus)
  - Doorway threshold
  - Interior hallway
  - Closed office door

- **Sequence C**: Decision (or internal conflict)
  - Hands holding two objects (choosing between them)
  - Face looking left, then right (indecision)
  - Objects being weighed on a scale
  - Objects split-screen (visual juxtaposition)
  - Single object (resolution/choice)

Place Sequence A into the timeline with **1-second cuts** between each image:

```text
Clock 6 AM (1 sec) → Morning doorway (1 sec) → Shortening shadows (1 sec) → Coffee pour (1 sec) → High sun (1 sec)
Total: 5 seconds
Effect: Compressed time; the viewer reconstructs the passage of time from visual cues (sun position, shadows, coffee ritual).
No single image *shows* time passing; the *rhythm of cuts* implies time passing.
```

Now place Sequence B with **varying cut lengths**:

```text
Car arriving (2 sec) → Footsteps (1.5 sec) → Doorway (1 sec) → Hallway (0.5 sec) → Office door (1 sec)
Total: 6 seconds
Effect: Accelerating rhythm (stretching time for the approach, compressing time as destination nears). 
The viewer feels building momentum and tension.
```

Finally, place Sequence C with **alternating shot lengths to emphasize conflict**:

```text
Hands with object A (0.5 sec) → Hands with object B (0.5 sec) → Object A (0.5 sec) → Object B (0.5 sec) → 
Face indecision (1.5 sec) → Split-screen juxtaposition (2 sec) → Single object chosen (1 sec)
Total: 7.5 seconds
Effect: The rapid back-and-forth between objects creates visual tension. The held shots (face, split-screen) 
provide moments of reflection. The final single object feels resolved.
```

Document in `Editorial_Decisions.txt`:

```text
MONTAGE SEQUENCE A: Compressed Time
Principle: Soviet montage of time. Each shot is a visual marker of temporal progression. 
The cuts do not show continuous action; they show *discrete moments* that the viewer's brain combines into the experience of time passing.
Critique: Effective for conveying elapsed time without real-time duration.

MONTAGE SEQUENCE B: Accelerating Approach
Principle: Rhythm as emotion. Shot lengths vary to control pacing; shorter shots feel faster, build anxiety.
The viewer experiences momentum even though the subject (the approaching person) may be moving at constant speed.
Critique: Powerful tool for psychological pacing; frequently used in thrillers and chase sequences.

MONTAGE SEQUENCE C: Juxtaposition and Conflict
Principle: Eisenstein's theory: two shots create a *third* meaning in the viewer's mind that is not in either shot alone.
Object A + Object B does not simply mean "these are both choices"; it means "tension between two options."
Critique: This is the foundation of all meaning in cinema. The gap between shots is creative space.
```

---

## Exercise 3: Finished Piece & Self-Critique — Color Grading, Sound Design, and Delivery

This final exercise synthesizes capture, editorial, and technical knowledge into a complete, finished sequence ready for delivery. You will grade raw or log-recorded footage to broadcast standards, synchronize sound design to visual action, and export in formats suitable for multiple distribution platforms.

### Part A: Primary Color Correction and Look Development

Create a new project named `Lab_03_Color_Grade`. Set the timeline to 23.976 fps, 1920×1080, and name it `Grade_Workflow`.

Import the **three-shot sequence you captured in Exercise 1** (or download a comparable sequence: a daylight interior, a low-key interior, and mixed lighting). Place all three clips into the timeline end to end, with **1-second black leader** before and after (black frames serve as a neutral reference for your eye).

Switch to the **Color page** in DaVinci Resolve. You will see the **Node Graph** (bottom center): a visual flowchart of color operations. By default, there is one **Serial Node** (a single processing stage). You will build a **three-node color pipeline**:

1. **Node 1 (Serial)**: Input LUT or Log Transform (convert from camera log to display-referred)
2. **Node 2 (Serial)**: Primary Balance (Lift, Gamma, Gain adjustment for overall color and exposure)
3. **Node 3 (Serial)**: Secondary Corrections (HSL qualifiers to isolate and adjust specific colors—skin tones, sky, backgrounds)

**Step 1: Apply Input LUT**

Right-click on Node 1 and select **Input LUT**. Choose the LUT corresponding to your camera. If you used a smartphone or standard camera, select **Generic Log to Rec.709** or skip this step if your footage is already in Rec.709. If your clips are mixed (some log, some already corrected), apply the LUT only to the log clips; for the corrected clips, disable the LUT on those nodes using the **Bypass** button.

**Step 2: Primary Balance**

Ensure Node 2 is selected (highlight on the node indicates selection). Open the **Curves panel** in the right sidebar. You will see a diagonal line from bottom-left to top-right: this is the tone curve, mapping input values (horizontal axis) to output values (vertical axis). The left side is blacks, the middle is midtones, the right side is highlights.

For **Shot 1 (Daylight Interior)**:

- Adjust the **Lift** slider (pulls up the blacks without affecting midtones or highlights). Set Lift to **+10** (you'll see the blacks brighten slightly, which opens shadow detail without crushing).
- Adjust **Gamma** (brightens or darkens midtones). Set Gamma to **+5** to lift the face from the previous ~450 IRE to ~550 IRE (brighter, more visible).
- Adjust **Gain** (affects highlights primarily). Leave Gain at **0** for now.

Observe the **Waveform Monitor**. The blacks will rise (the bottom cliff in the waveform moves up), and the midtones will spread upward. The highlights remain relatively unchanged.

Now you will **adjust color balance** using the **Color Wheels** in the right panel. You'll see three color wheels labeled **Shadows**, **Midtones**, **Highlights**. Each wheel represents hue and saturation: moving the dot toward red adds red; moving toward cyan removes red (or adds cyan). Moving toward yellow adds warmth; moving toward blue adds coolness.

For daylight interiors (typically cool windows but warm tungsten fill), adjust the **Shadows** wheel: move the dot slightly toward **warm** (toward yellow/orange, ~+0.1 on the saturation ring, ~+10° on the hue). This warms up the shadow areas under the actor's jaw, creating depth. Adjust the **Midtones** wheel: move slightly toward **warm** (+0.05 saturation, +5° hue) to match the daylight color temperature preference of Rec.709 (which slightly favors warm). Leave **Highlights** neutral (at the center).

Observe the **Vectorscope**. The color points will migrate from center toward the orange/yellow region (40–60° on the color wheel). This is correct for daylight interiors with tungsten fill.

For **Shot 2 (Low-Key Interior)**:

This shot has crushed blacks and compressed midtones. Adjust:

- **Lift**: +15 (more aggressive, to separate blacks from pure black and reveal shadow detail)
- **Gamma**: +8 (lifts the dim midtones higher, compensating for the low capture exposure)
- **Gain**: 0

Adjust color wheels:

- **Shadows**: Move toward blue (+0.08 saturation, -15° hue) to reflect cooler ambient room light
- **Midtones**: Move toward warm (+0.1 saturation, +10° hue) to reflect any tungsten fill on the face
- **Highlights**: Neutral

The **Vectorscope** will show a split: shadows pointing toward blue (~240°), midtones pointing toward warm (~60°). This is intentional; it reflects the mixed light sources captured during recording.

For **Shot 3 (Mixed Lighting)**:

This shot already has strong color split (warm side, cool side). You will *intensify* this intentionally:

- **Lift**: +5 (minimal; this shot has adequate shadow separation)
- **Gamma**: 0 (midtones are already well-exposed)
- **Gain**: 0

Adjust color wheels:

- **Shadows**: Extreme blue (+0.2 saturation, -30° hue; push toward cyan to deepen cool shadows)
- **Midtones**: Extreme warm (+0.15 saturation, +20° hue; push toward yellow-orange to deepen warm side)
- **Highlights**: Neutral

The **Vectorscope** will show a dramatic split from blue to orange. This is a **stylized grade** that emphasizes the mixed color temperature as a visual design choice, not a technical correction.

Play the timeline with all three shots in sequence. The viewer will see **three distinct color worlds**:

1. Daylight interior: warm, balanced, natural
2. Low-key interior: split between cool and warm, moody, with shadow detail revealed
3. Mixed lighting: extreme color split, stylized, theatrical

This demonstrates that **color grading is not uniform application of correction**; each shot is a *distinct aesthetic choice* based on its content and narrative role. Document in a file named `Grade_Notes.txt`:

```text
SHOT 1: Primary Balance Application
Input LUT: Rec.709 (or skipped if already corrected)
Lift: +10 (opens shadow detail without crushing)
Gamma: +5 (brightens midtones, makes face more visible)
Gain: 0 (preserves highlights, prevents blown recovery)
Shadow Color Wheel: +0.1 sat, +10° hue (adds warmth to shadows; mimics tungsten fill)
Midtone Color Wheel: +0.05 sat, +5° hue (slight warmth; Rec.709 preference)
Highlight Color Wheel: 0, 0 (neutral, preserves daylight window color)
Result: Natural, balanced; skin tones at ~550 IRE (healthy); window slightly blown (design intent)
Vectorscope reading: Center cluster (neutral whites) with slight warm migration (40–60° region)

SHOT 2: Primary Balance for Low-Key Lighting
Lift: +15 (aggressive shadow lift; reveals detail in crushed blacks)
Gamma: +8 (strong midtone lift; compensates for dim capture exposure)
Gain: 0
Shadow Color Wheel: +0.08 sat, -15° hue (adds blue; reflects cooler ambient room light)
Midtone Color Wheel: +0.1 sat, +10° hue (adds warm; tungsten fill on face)
Highlight Color Wheel: 0, 0
Result: Mood-driven; shadow detail now visible (blacks raised from 32 IRE to ~100 IRE); color split reflects mixed sources
Vectorscope reading: Bimodal distribution; shadows toward blue (~240°), midtones toward warm (~60°)

SHOT 3: Stylized Color Grade (Intentional Extreme Color Split)
Lift: +5 (minimal; already well-separated blacks)
Gamma: 0 (midtones are correct at capture; no need to adjust)
Gain: 0
Shadow Color Wheel: +0.2 sat, -30° hue (extreme blue; push toward cyan)
Midtone Color Wheel: +0.15 sat, +20° hue (extreme warm; push toward yellow-orange)
Highlight Color Wheel: 0, 0
Result: Theatrical, stylized; not "natural" color correction, but *intentional design*.
The extreme color split emphasizes mixed lighting as a visual language, not an error to correct.
Vectorscope reading: Dramatic arc from blue (~210°) to orange (~70°); maximum color separation
```

### Part B: Secondary Color Correction Using HSL Qualifiers

Create a new Node (Node 4, Serial) for secondary corrections. This node will isolate *specific colors* and adjust them independently.

In Node 4, open the **HSL Qualifier** panel. The HSL (Hue, Saturation, Lightness) qualifier creates a mask based on color: you select a range of hues (e.g., "all reds and magentas"), and only pixels within that hue range are affected by adjustments in that node.

**For Shot 1 (Daylight Interior), isolate and adjust skin tones:**

Click the **HSL Qualifier picker** (eyedropper icon) and click on the actor's face in the viewer. DaVinci will automatically set the hue range to the skin tone color (typically 0–40° on the color wheel, in the red-orange region). The **Range** slider controls how much color variation is included; set it to **±30°** to capture a broad range of skin tones (from olive to deep brown to light pink, depending on actor skin tone).

Now adjust only the skin tones:

- **Saturation**: +15 (increases saturation of skin only; makes skin glow without oversaturating the background)
- **Hue Shift**: +5° (shifts the skin tone slightly toward warmth; creates healthy, flattering appearance)

The actor's skin now appears more vibrant and flattering, while the background (walls, furniture) remains unchanged. This is **selective color correction**: the grade affects only the pixels in the qualifying color range.

**For Shot 1, isolate and adjust the sky or bright background:**

Create a new Node 5 with another HSL Qualifier. Click the picker and click on the bright background (the blown window or bright wall area). DaVinci sets the hue to that region (typically 180–240° for cool daylight windows, or 20–60° for warm walls). Set Range to ±40°.

Adjust:

- **Saturation**: -20 (desaturates the bright area; reduces the overwhelming color of a blown window)
- **Lightness**: -10 (darkens the bright area slightly; compresses the blown-out appearance)

The result: the bright background loses intensity and color punch, drawing attention back to the actor. This is a **background control** technique used in portrait photography and cinema.

**For Shot 3 (Mixed Lighting), isolate warm side vs. cool side:**

Create Node 6 with HSL Qualifier. Use the picker to select the warm (orange/red) side of the face. Set Range to ±30°.

Adjust:

- **Saturation**: +20 (intensifies the warm)
- **Hue Shift**: +10° (shifts toward orange)

Create Node 7. Use the picker to select the cool (blue) side. Set Range to ±30°.

Adjust:

- **Saturation**: +20 (intensifies the cool)
- **Hue Shift**: -10° (shifts toward deeper blue)

The result: the color split is now *designed*, not accidental. Each side of the face has distinct saturation and hue. Play the shot and observe: the viewer perceives the mixed lighting not as a technical error, but as a deliberate visual design.

Document in `Grade_Notes.txt`:

```text
SECONDARY CORRECTIONS: HSL Qualifier Workflow

SHOT 1 - Skin Tone Adjustment (Node 4)
HSL Range: Hue ~20° (orange-red), Range ±30°
Saturation: +15 (skin glows; becomes focal point)
Hue Shift: +5° (warmth; healthy appearance)
Effect: Skin tones are isolated and enhanced without affecting background. 
The face stands out against the daylit background.

SHOT 1 - Background Desaturation (Node 5)
HSL Range: Hue ~200° (cool window/wall), Range ±40°
Saturation: -20 (blown areas lose color intensity)
Lightness: -10 (recovers some dynamic range in bright area)
Effect: The bright background no longer competes with the face for attention. 
Classic portrait grading: isolate subject, suppress background.

SHOT 3 - Warm Side Intensification (Node 6)
HSL Range: Hue ~60° (warm side of face), Range ±30°
Saturation: +20 (intensify warm tones)
Hue Shift: +10° (shift toward deeper orange)
Effect: The warm side of the face becomes more saturated and intense than the cool side.

SHOT 3 - Cool Side Intensification (Node 7)
HSL Range: Hue ~240° (cool side of face), Range ±30°
Saturation: +20 (intensify cool tones)
Hue Shift: -10° (shift toward deeper blue)
Effect: The cool side becomes a distinct visual zone. The two sides now feel deliberately separated by color design.

Final result: Mixed lighting is no longer a technical accident; it is an intentional aesthetic. 
The viewer sees and accepts the color split as part of the visual language.
```

### Part C: Audio Synchronization and Sound Design

Create a new timeline named `Audio_Sync`. You will now add sound design to your sequence. Sound design includes:

- **Dialogue** (if applicable): actor speaking, voice-over narration
- **Ambience**: room tone, background environment sounds (distant traffic, bird song, office hum)
- **Foley**: physically created sound effects (footsteps, hand movements, clothing rustle)
- **Sound effects**: impacts, transitions, signal sounds
- **Music**: underscore or thematic material (if applicable)

**Step 1: Ingest Audio**

If you recorded audio during your capture shoot (or downloaded a sequence with sound), ingest the audio file into DaVinci Resolve. In the Edit page, right-click in the **Media Pool** and select **Import Media**. Select your audio file (WAV, MP3, or MOV with embedded audio).

Drag the audio into the timeline below the video track. DaVinci will automatically create an **audio track**. If the audio is not synchronized with the video (a common problem if audio was recorded separately from video), use the **Slip** tool to manually align audio and video:

- Right-click the audio clip in the timeline
- Select **Show Keyframe Editor**
- Adjust the clip position using the **arrow keys** or by dragging until the audio aligns with the video action

For example, if the video shows the actor's mouth opening to speak at 00:00:05:00, but the audio begins at 00:00:05:15, you need to shift the audio **backward** (earlier) by 15 frames so that the audio leads the video by the appropriate amount.

**Step 2: Edit Audio for Timing**

Switch to the **Fairlight Audio Mixer** (menu option in top right: Fairlight). This is DaVinci's built-in audio editing and mixing interface.

For the three-shot sequence (Daylight Interior, Low-Key Interior, Mixed Lighting), plan the audio as follows:

```text
SHOT 1 (Daylight Interior, 10 seconds):
Audio layer 1 (Ambience): Room tone (ventilation hum, distant street sound) at -18 dB (quiet background)
Audio layer 2 (Dialogue): Actor greeting ("Good morning, I'm here to meet with you") timed to match mouth movement
Audio layer 3 (Foley): Footsteps entering room (1-2 footsteps, 0.5-1.0 second duration)
Audio layer 4 (Foley): Clothing rustle as actor moves (subtle, -24 dB)

SHOT 2 (Low-Key Interior, 10 seconds):
Audio layer 1 (Ambience): Different room tone (quieter, more echo, perhaps lamp warmth—silence with subtle ac hum)
Audio layer 2 (Dialogue): Actor speaking response ("Please, sit down") timed to match lips
Audio layer 3 (Foley): Footsteps walking to chair, chair creak as actor sits
Audio layer 4 (Sound effect): Subtle reverb tail (indicates different acoustic space from Shot 1)

SHOT 3 (Mixed Lighting, 10 seconds):
Audio layer 1 (Ambience): Layered ambience (fluorescent hum, distant activity, more "alive" than Shot 2)
Audio layer 2 (Dialogue): Actor final line timed to lips
Audio layer 3 (Foley): Hand motion sound (subtle paper/desk sounds)
Audio layer 4 (Music sting or transition tone): 1-2 second ascending tone at end, indicating shift or transition
```

In the **Fairlight mixer**, you will see **channel faders** (vertical sliders) for each audio track. Adjust each channel's volume:

- **Ambience**: -18 dB (should be audible but not distracting)
- **Dialogue**: -6 dB to -3 dB (clear, primary focus)
- **Foley**: -12 dB to -18 dB (present, but quiet enough to not overpower)
- **Sound effects or music**: -9 dB (medium importance)

Solo each track (click the **S** button on the fader) to verify that each layer is correctly positioned and timed. Then unmute all and listen to the mix. The dialogue should be intelligible, the ambience should provide context, and the foley should feel natural (not overly processed).

**Step 3: Use Automatic Dialogue Replacement (ADR) if Needed**

If your dialogue is unclear, noisy, or misaligned, you can use **Automatic Dialogue Replacement** to record clean dialogue over the video. This is a professional technique used on sets with poor audio.

In Fairlight, right-click on the dialogue track and select **Lock for Editing**. Create a new audio track above it. Set that track as **Input Track** (Record-armed). 

Set a **click track** (metronome) at 60 BPM. Play the timeline and record new dialogue over the original. When the actor/speaker repeats the lines in sync with the lips on screen, their new recording will record into the new track. Stop recording. Delete or mute the original noisy dialogue track. The new clean dialogue is now your primary layer.

Document the audio mix in a file named `Audio_Mix_Notes.txt`:

```text
AUDIO SYNCHRONIZATION LOG

SHOT 1: Daylight Interior (00:00:00:00 to 00:00:10:00)
Ambience track: Room tone (HVAC hum + distant traffic) at -18 dB; starts at 00:00:00:15 (slight lead for environment establishment)
Dialogue track: "Good morning, I'm here to meet with you" at -6 dB; starts at 00:00:02:00 (after actor crosses threshold)
Foley track: Footsteps (two impacts) at -15 dB; at 00:00:00:20 and 00:00:00:25 (synchronized to visible foot strikes in video)
Clothing rustle at -24 dB; duration 0.3 seconds at 00:00:01:00 (subtle, as actor moves toward desk)
Timing check: Mouth movement and dialogue onset verified in sync using waveform scrubbing (DaVinci Fairlight shows both audio and video waveforms; dialogue peaks align with visible mouth opening)

SHOT 2: Low-Key Interior (00:00:10:00 to 00:00:20:00)
Ambience track: Quieter room tone (minimal hum, more silence/reverb) at -20 dB; starts at 00:00:10:15
Dialogue track: "Please, sit down" at -5 dB; starts at 00:00:12:00 (after actor settles in chair)
Foley track: Footsteps (slower, deliberate; two impacts) at -18 dB; at 00:00:10:20 and 00:00:11:10 (synchronized to visible gait in video)
Chair creak (single impact) at -12 dB; at 00:00:11:30 (synchronized to actor sitting motion)
Reverb tail: 0.5 second decay of ambience at 00:00:19:00, fading to silence (creates acoustic sense of space ending)

SHOT 3: Mixed Lighting (00:00:20:00 to 00:00:30:00)
Ambience track: Layered ambience (fluorescent hum + distant activity) at -16 dB; starts at 00:00:20:10
Dialogue track: Final line (content TBD based on script) at -4 dB; starts at 00:00:22:00
Foley track: Paper/desk sounds (subtle rustling) at -20 dB; at 00:00:23:00 (if actor reaches for objects)
Music sting or transition tone (ascending 1-2 second tone, indicative of narrative shift) at -8 dB; starts at 00:00:28:00 and extends to end (00:00:30:00)

Overall mix philosophy: Dialogue drives attention; ambience and foley provide realism; music/effects signal transitions.
Dynamics: Shot 1 is busier (more foley, more environmental activity); Shot 2 is quieter (intimate, sparse); 
Shot 3 returns to activity and adds musical element (builds energy for potential climax or transition).
```

### Part D: Final Delivery and Export

Create a new timeline named `Final_Export`. Copy the graded video clips and mixed audio from the previous steps into this timeline. You will now prepare the sequence for delivery in two formats:

1. **Broadcast/Streaming Master** (ProRes 422 HQ, Rec.709 color space, all audio channels, metadata)
2. **Web-Optimized Export** (H.264, 1080p, stereo mix, optimized for YouTube/Vimeo)

**Export 1: Broadcast Master (ProRes 422 HQ)**

Right-click on the timeline and select **Export Timeline**. In the **Delivery** window:

- **Codec**: ProRes 422 HQ (high quality, visually lossless, used for archival and professional distribution)
- **Resolution**: 1920×1080
- **Frame rate**: 23.976 fps (maintain cinema frame rate)
- **Color space**: Rec.709 (standard broadcast video color space)
- **Audio format**: Stereo Mix (or 5.1 surround if applicable)
- **Audio codec**: PCM or AAC (lossless preferred for master)
- **Bit depth**: 10-bit (preserves color information through the pipeline)
- **File name**: `Lab_03_Sequence_Master_ProRes422HQ.mov`
- **Location**: Desktop or project folder

Click **Export**. DaVinci will render the timeline to the specified codec. This process may take 5–15 minutes depending on your system and sequence length. While rendering, the application will display a **progress bar** showing percentage complete and estimated time remaining. Do *not* interrupt the render; allow it to complete.

**Export 2: Web-Optimized (H.264, YouTube/Vimeo)**

Right-click on the timeline again and select **Export Timeline**. In the **Delivery** window:

- **Codec**: H.264 (most compatible with browsers and streaming platforms)
- **Resolution**: 1920×1080 (YouTube supports up to 4K, but 1080p is standard for web distribution)
- **Frame rate**: 23.976 fps (maintain cinema frame rate; YouTube will accept and display correctly)
- **Color space**: Rec.709 (web standard)
- **Audio format**: Stereo Mix (downmix all audio to stereo for web compatibility)
- **Audio codec**: AAC (most compatible with web players)
- **Bit rate**: Video 8000 kbps, Audio 128 kbps (balanced quality vs. file size for streaming)
- **File name**: `Lab_03_Sequence_Web_H264_1080p.mp4`
- **Location**: Desktop or project folder

Click **Export**. The H.264 render will complete faster than ProRes (typically 2–5 minutes).

**Export 3: Mobile-Optimized (H.264, 720p, reduced bit rate)**

Repeat the export process with:

- **Resolution**: 1280×720
- **Bit rate**: Video 2500 kbps, Audio 96 kbps (optimized for mobile playback and limited bandwidth)
- **File name**: `Lab_03_Sequence_Mobile_H264_720p.mp4`

After all exports complete, you will have three files:

```text
Lab_03_Sequence_Master_ProRes422HQ.mov        (~2–4 GB, 10-bit, lossless quality)
Lab_03_Sequence_Web_H264_1080p.mp4            (~150–300 MB, 8-bit, web quality)
Lab_03_Sequence_Mobile_H264_720p.mp4          (~40–80 MB, 8-bit, mobile quality)
```

Document the export settings in a file named `Export_Log.txt`:

```text
EXPORT SETTINGS AND DELIVERY FORMATS

MASTER FILE (Archival and Professional Use)
Codec: ProRes 422 HQ
Resolution: 1920×1080
Frame rate: 23.976 fps
Color space: Rec.709 (broadcast video standard)
Audio: Stereo PCM, 48 kHz, 16-bit
Bit depth: 10-bit video
File size: Approximately 2.5 GB per 10 minutes
Use case: Archive storage, professional color-correction handoff, broadcast ingest, offline editing
Quality: Visually lossless; suitable for future re-grading or re-editing
Compression: Lossless intra-frame compression (each frame is independently encoded)

WEB-OPTIMIZED FILE (YouTube, Vimeo, Streaming)
Codec: H.264 (MPEG-4 AVC)
Resolution: 1920×1080
Frame rate: 23.976 fps
Color space: Rec.709
Audio: Stereo AAC, 48 kHz, 128 kbps
Bit depth: 8-bit video
Bit rate: 8000 kbps video, 128 kbps audio
File size: Approximately 200 MB per 10 minutes
Use case: Streaming platforms (YouTube, Vimeo, etc.), social media, online distribution
Quality: Visible compression artifacts possible, but acceptable for web distribution
Compression: Lossy inter-frame compression (relies on frame-to-frame prediction and temporal compression)

MOBILE-OPTIMIZED FILE (Smartphone, Tablet, Limited Bandwidth)
Codec: H.264 (MPEG-4 AVC)
Resolution: 1280×720
Frame rate: 23.976 fps
Color space: Rec.709
Audio: Stereo AAC, 48 kHz, 96 kbps
Bit depth: 8-bit video
Bit rate: 2500 kbps video, 96 kbps audio
File size: Approximately 60 MB per 10 minutes
Use case: Mobile devices, low-bandwidth networks, social media (Instagram, TikTok, Twitter)
Quality: Noticeable compression; suitable for mobile screens where artifact visibility is reduced by screen size
Compression: Lossy inter-frame compression with higher compression ratio than web version

TECHNICAL NOTES:
1. All formats maintain 23.976 fps (cinema frame rate) rather than converting to 29.97 fps (NTSC) or 25 fps (PAL). 
   This preserves the original capture frame rate and prevents judder artifacts.

2. Color space (Rec.709) is correctly applied to all exports. This ensures consistent color appearance across 
   the master file, web streams, and mobile versions.

3. ProRes 422 HQ is chosen for the master because it is:
   - Supported by all professional color-correction software (Resolve, Flame, etc.)
   - Lossless quality, allowing future re-grading without quality loss
   - Industry-standard for archival (Library of Congress recommends ProRes 422 HQ for video preservation)

4. H.264 for web is a lossy codec; compression reduces file size but introduces artifacts (blocking in high-motion scenes, 
   color banding in gradients). This is acceptable for streaming because viewer bitrate is limited by their internet connection.

5. Audio levels were normalized to -23 LUFS (broadcast standard) before export. This ensures consistent loudness 
   across platforms and complies with YouTube Normalized Volume (YNV) and streaming loudness standards.
```

---

## Critique Checklist & Common Fixes

After completing all three exercises, evaluate your work using this checklist. Address any failures before considering the lab complete.

### Visual Critique

**Exposure & Luminance**

- [ ] **Waveform verification**: Play the timeline with the Waveform Monitor visible. No clipped highlights except in intentional areas (windows, sky, blown backgrounds). No crushed blacks except in intentional low-key or silhouette shots.
  - *Fix if failing*: Return to the Color page. Apply a Power Window (radial or rectangular mask) around the problem area. Use Curves to either compress highlights (drag the top-right of the curve down) or lift shadows (drag the bottom-left up). Verify that the color correction is local (affects only the masked region) and does not bleed into other parts of the frame.

- [ ] **Vectorscope sanity check**: The Vectorscope shows color data distributed appropriately for the light source. Daylight interiors should cluster near center (neutral) with slight warm migration. Mixed lighting should show split (orange and blue). No color data should lie far outside the color wheel (which would indicate clipping or oversaturation).
  - *Fix if failing*: Reduce saturation in the HSL Qualifiers. Use the Saturation slider to bring extreme colors toward the center of the vectorscope (Saturation value of -10 to -20 typically corrects oversaturation).

**Color Grading Consistency**

- [ ] **Cut-to-cut color match**: Play the timeline. When you cut from one shot to another, do the colors feel harmonious or jarring? If Shot 1 is very warm and Shot 2 is very cool, is this intentional (stylized storytelling) or accidental (inconsistent color correction)?
  - *Fix if failing*: If the transition is unintentional, adjust the color wheels in the second shot to gradually move toward the first shot's color temperature. Use a **transition node**: create a new serial node between the two clips, and over 24 frames (1 second at 23.976 fps), animate the color wheels from the second shot's color toward the first shot's color. This creates a smooth color transition.

- [ ] **Skin tone consistency**: Play all shots featuring actors or people. Do skin tones look healthy (not overly red, not green, not sickly desaturated)? Healthy skin should sit at Hue 10–30° on the Vectorscope (orange-red region) with moderate saturation (not oversaturated or completely desaturated).
  - *Fix if failing*: Create an HSL Qualifier node for skin tones. Use the eyedropper to select a skin area in the brightest shot. Adjust Hue Shift to move skin toward the warm region (+10° to +20°). Adjust Saturation to increase vibrancy (+10 to +20). Then copy this correction node to the other shots and fine-tune for each shot's specific lighting.

**Contrast and Shadow Detail**

- [ ] **Shadow detail legibility**: Can you see distinct shapes and objects in shadow areas? Or are shadows pure black (data at IRE 0)?
  - *Fix if failing*: If shadows are crushed and this is unintentional, use the Lift slider in the primary balance node to raise the blacks. Set Lift to +10 to +20 and observe the waveform; the bottom cliff should move up, revealing shadow detail. If the shot is intentionally low-key (crushed blacks are part of the aesthetic), do not change this; it is correct.

- [ ] **Highlight recoverability**: Are blown highlights permanently destroyed (data at IRE 1023, unrecoverable), or are they recoverable with crushed-highlight recovery techniques?
  - *Fix if failing*: Create a Power Window around the blown area. In the Curves panel, drag the top-right of the curve down (compress the highlights). This will recover detail if the data is not fully clipped. If the data is fully clipped (no data at all), no recovery is possible; this is a capture failure, not a grading problem.

### Editorial Critique

**Cut Motivation**

- [ ] **Every cut has a reason**: Play the timeline. At each cut, ask: "Why did the editor cut here?" The answer should be one of: (a) new spatial information needed (cutting to show a wider view, closer detail, or new location), (b) emotional beat (cutting on dialogue emphasis or character reaction), (c) temporal progression (cutting to show time passing or action advancing), or (d) rhythm/pacing (cutting to control viewing speed).
  - *Fix if failing*: Identify cuts that serve no clear purpose. These are *unmotivated cuts*. Consider either removing the cut (extend the previous shot to cover the action) or adding visual information to justify the cut (a reaction shot, a detail shot, or a beat of action visible in the new shot).

- [ ] **Cut length vs. shot content**: Long shots (wide, establishing, exposition-heavy) are held longer (3–5 seconds). Medium shots and dialogue are held medium length (2–3 seconds). Close-ups and reaction shots are held briefly (1–2 seconds) to maximize emotional impact. Montage sequences with many rapid cuts are intentionally fast (0.5–1 second per cut) to build energy.
  - *Fix if failing*: If a close-up is held for 5 seconds, the viewer may feel bored or uncomfortable. Reduce to 1–2 seconds. If a wide establishing shot is held for only 0.5 seconds, the viewer may not absorb the spatial information. Extend to at least 2–3 seconds.

**Pacing and Rhythm**

- [ ] **Audio-visual synchronization**: Dialogue begins within 1–2 frames of the visible mouth movement. Foley effects (footsteps, door closure, object impact) occur within 1–2 frames of the visible action. Ambience and music do not distract from dialogue; they sit at least 6 dB lower in volume.
  - *Fix if failing*: In the Fairlight Audio Mixer, use the slip tools to shift audio earlier or later until the onset aligns with the visible action. Use the waveform scrubber (play head over the audio track) to verify frame-by-frame alignment. Adjust track volumes so dialogue is clearly audible and effects provide context without overwhelming.

- [ ] **Pacing matches narrative**: Calm, contemplative scenes have longer cuts and slower pacing. Action, tension, or emotional climaxes have shorter cuts and faster pacing. Transitions between scenes have clear audio/visual cues (sound effects, music swells, or color changes) that signal to the viewer that a shift is occurring.
  - *Fix if failing*: If a low-key dramatic scene feels rushed, extend cut lengths and add silence between effects. If an action sequence feels static, shorten cuts and increase overlap between audio and video elements. Add music or sound design to heighten energy during climactic moments.

### Technical Critique

**Color Space and Delivery**

- [ ] **Rec.709 vs. DCI P3**: For broadcast and streaming (YouTube, Vimeo), export is Rec.709 (standard video color space, slightly less gamut than cinema DCI). For theatrical DCP delivery, export is DCI P3 (cinema standard, wider color gamut). Verify that you are exporting to the correct color space for your distribution platform.
  - *Fix if failing*: If exported to YouTube but color space is set to DCI P3, the colors may appear oversaturated or mismatched on web browsers. Re-export using Rec.709 color space.

- [ ] **Bit depth and compression**: Master file is 10-bit (more color information preserved for future re-grading). Delivery files are 8-bit (sufficient for streaming, reduces file size).
  - *Fix if failing*: If the master file is exported as 8-bit (or worse, compressed H.264), future re-grading may show banding or color fringing. Always export the archival master as 10-bit ProRes 422 HQ. Web deliverables can be 8-bit H.264.

- [ ] **Audio loudness**: All audio (dialogue, effects, music) is normalized to -23 LUFS (broadcast standard, integrated loudness). Peaks do not exceed -1 dBFS (digital headroom, prevents clipping on playback devices).
  - *Fix if failing*: In Fairlight, use the **Loudness Meter** to measure integrated loudness (Lufs). If the mix is too loud (-15 LUFS), reduce all track levels by 8 dB. If too quiet (-30 LUFS), increase by 7 dB. Re-measure and adjust until the integrated reading is -23 ± 1 LUFS.

### Common Fixes Reference

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| Blown highlights with no detail | Clipped data (IRE 1023, unrecoverable) | No fix possible in post; this is a capture failure. For future shoots, reduce exposure or increase shutter speed. |
| Recoverable blown highlights (data above IRE 950) | Crushed-highlight clipping (recoverable) | Use Curves node to drag the top-right down; this remaps the compressed data back into displayable range. Combine with desaturation (HSL Qualifier, Saturation -10 to -20) to prevent posterization. |
| Crushed shadows (pure black, data at IRE 0) in unintentional areas | Underexposure or shadow crush in grade | Use Lift slider to +10 to +20 to raise blacks. Verify no detail emerges (if none, the data is truly crushed and unrecoverable). |
| Color shift from shot to shot (warm to cool mismatch) | Inconsistent camera white balance or inconsistent color grading | Create an HSL Qualifier for a neutral reference (gray wall, shirt) and match hue/saturation across shots. Or create a transition node between shots and animate the color shift over 1 second. |
| Oversaturated or sickly skin tones | Excessive saturation or incorrect hue shift in HSL Qualifier | Use HSL Qualifier on skin tones (Hue ~20°). Set Saturation to -10 to -20 (reduce). Verify skin sits at Hue 15–35° on Vectorscope (orange-red region, not pure red or pink). |
| Dialogue inaudible or misaligned with lips | Low volume, low bitrate codec, or timing misalignment | (1) Volume: raise dialogue track 3–6 dB above effects/music. (2) Bitrate: re-export as ProRes Master, not compressed H.264. (3) Timing: use Fairlight slip tools to shift audio until mouth movement aligns. |
| Thin, flat image (low contrast) | Insufficient gamma adjustment or midtone crushing | Increase Gamma slider by +5 to +15. Verify waveform midtones move up (from 300–400 IRE to 400–500 IRE). Add saturation via HSL Qualifiers (+10 to +15) to restore perceived contrast. |
| Muddy, desaturated colors | Log space display (LUT not applied) or excessive desaturation in grade | Verify LUT is applied (should see bold color in waveform and vectorscope). If colors are intentionally desaturated, increase saturation by +10 to +20 in HSL Qualifiers. |
| Pixelation or color banding in gradients | Excessive compression (8-bit codec or low bitrate) or tone curve aggression | For archival master, use 10-bit ProRes. For streaming, increase H.264 bitrate to 8000 kbps (video). Soften tone curves to avoid drastic remapping that causes banding. |

---

## Final Verification Checklist

Before submitting or sharing your work, verify:

- [ ] All three exercise timelines are complete and play without errors.
- [ ] Waveform and Vectorscope data support your grading choices (no accidental clipping; color data distributed appropriately).
- [ ] Audio is synchronized to video (dialogue and effects within 1–2 frames of visible action).
- [ ] All three export files (ProRes Master, Web H.264 1080p, Mobile H.264 720p) render successfully without dropped frames.
- [ ] At least one peer or mentor has reviewed the work and provided feedback (ideally, someone with professional video editing or grading experience).
- [ ] All documentation files (`Exposure_Log.txt`, `Editorial_Decisions.txt`, `Grade_Notes.txt`, `Audio_Mix_Notes.txt`, `Export_Log.txt`) are completed with detailed observations, not placeholder text.

---

## Studio Maintenance and Archival

After completing the lab, maintain your project for future reference:

1. **Archive the project folder**: Copy the entire DaVinci Resolve project folder (including the database, media cache, and all source files) to external drive or cloud storage. DaVinci projects are highly dependent on relative file paths; moving files after project creation will break links.

2. **Maintain the master exports**: Keep the ProRes 422 HQ master file in archival storage (external drive in a cool, dry environment, or cloud backup with redundancy). This file is your safety net for future re-grading or platform-specific exports.

3. **Document your decisions**: Keep all notes and logs (Exposure_Log.txt, etc.) in a folder within the project. Future work on similar sequences will benefit from reference to these decisions.

4. **Reference still frames**: Export 3–5 key frames from your final grade (at the Color page, capture still frames to the Gallery). These become your color reference for future projects shot in similar lighting conditions.

---

This completes the **Studio Practice Labs: Video Production**. By iterating through observation (Exercise 1), editorial construction (Exercise 2), and technical finishing (Exercise 3), you have developed the foundational skills of video production: understanding how light becomes image, how shots combine into meaning, and how image and sound coordinate to create finished work ready for distribution.
