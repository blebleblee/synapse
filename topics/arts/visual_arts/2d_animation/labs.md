# Studio Practice Labs: 2D Animation and Motion Graphic Timing

## Objective & Studio Setup

The practice of motion graphics and 2D animation is fundamentally about controlling *time*. While static design manipulates space—composition, balance, hierarchy—animation manipulates the *rate and rhythm* at which change occurs. Timing governs whether a movement feels weighty and deliberate, snappy and energetic, or limp and unconvincing. The student animator must develop an intuition for temporal spacing just as a painter develops an intuition for color relationships. This requires repeated exposure to real timing data, hands-on manipulation of keyframes and easing curves, and the trained eye to recognize when a motion sequence succeeds or fails.

These labs are designed to build that intuition through progressive, cumulative practice. You will begin by observing and measuring real-world motion, move into controlled technique drills where you animate simple shapes under strict timing constraints, and culminate in a finished piece where all principles integrate. Each exercise produces a concrete artifact—a timed sequence, a reference sheet, an animated composition—that you will critique against a rubric. The goal is not to produce portfolio pieces, but to develop the perceptual and technical foundation that professional animation demands.

### Studio Setup & Required Materials

**Hardware & Software Environment:**
You will need access to frame-accurate video editing and playback software, a raster animation tool, and optionally a vector graphics application for motion design work. The core toolkit is:

- **DaVinci Resolve** (free, full version): non-linear video editor with frame-accurate playback, timeline navigation, and reference viewing. Essential for analyzing filmed motion and building timed sequences.
- **Blender** (free, open-source): includes Grease Pencil for 2D drawing-on-animation and Dope Sheet for keyframe timing visualization. The Dope Sheet is your primary timing-analysis instrument.
- **Krita** (free, open-source): frame-by-frame animation workspace with onion-skinning, real-time playback at variable frame rates, and built-in easing curve editor.
- **GIMP or Photoshop** (Photoshop optional but easier for multi-layer work): for frame preparation, compositing, and reference image work.
- **A camera** (phone camera acceptable): to film reference motion of physical objects and body movement.

**Physical Materials:**
- A sketchbook or animation paper pad (12 x 9 inches minimum, 100 sheets or more).
- Pencils: HB for rough work, 2B or 4B for clean drawing, fine-tipped mechanical pencil (0.5 mm) for registration marks.
- Light table or tablet with backlit screen for checking registration and onion-skinning analog work.
- Video reference: download or shoot real motion (a bouncing ball, a human walk cycle, fabric drape, water pour) at 24 fps minimum.

**Diagnostic Tools:**
- Frame-by-frame video player (VLC, QuickTime Pro, or Resolve's timeline scrubber).
- Animation timing chart (provided in Exercise 1).
- Easing curve reference (sine, ease-in-out, custom bezier curves; provided in Exercise 3).
- Critique rubric (provided at the end of this guide).

### Understanding Frame Rate, Timing Increments, and Playback Speed

Before beginning the exercises, clarify the relationship between frame rate, duration, and perceptual timing. Standard professional frame rates are:

- **24 fps**: Film standard, creates a slight temporal blur that feels cinematic and slightly loose.
- **25 fps**: PAL video standard (Europe, parts of Asia).
- **29.97 fps**: NTSC video standard (North America, Japan).
- **30 fps**: Often used in real-time graphics and some broadcast workflows.
- **60 fps**: Smooth, responsive; commonly used in motion graphics and high-frame-rate video.

For 2D animation practice, work at **24 fps** unless otherwise specified. This creates a standard 1/24th-second increment per frame (≈ 41.7 milliseconds). A 12-frame sequence lasts 0.5 seconds; a 24-frame sequence lasts 1 second. Memorizing these conversions is essential:

| Frames | Duration at 24 fps | Frames | Duration at 24 fps |
|--------|-------------------|--------|-------------------|
| 1      | 41.7 ms           | 24     | 1.0 s              |
| 2      | 83.3 ms           | 36     | 1.5 s              |
| 3      | 125 ms            | 48     | 2.0 s              |
| 6      | 250 ms            | 60     | 2.5 s              |
| 12     | 500 ms            | 120    | 5.0 s              |

This framework grounds all timing decisions: when you hold a keypose for 8 frames, you are committing to a 333 millisecond *pause*—long enough for the eye to register and read the pose, but short enough to maintain visual flow. When you ease a motion over 12 frames instead of 6, you are doubling the duration and thereby halving the perceived speed. These quantitative relationships are non-negotiable in professional work.

---

## Exercise 1: Observation & Fundamentals Drill — Analyzing Real Motion and Extracting Timing Data

### Objective
Develop the perceptual skill to observe real motion, extract its timing structure, and represent that structure as numerical timing data and simple diagrams. This exercise trains the eye to recognize spacing, acceleration, weight, and rhythm in everyday motion before attempting to animate artificially.

### Part A: Filming and Frame-Analysis of a Bouncing Ball

A bouncing ball is the canonical first animation study because its motion is governed by a single physical principle—gravity—and yet exhibits all the core timing phenomena: anticipation (the dip before the bounce), acceleration (speeding up as it falls), deceleration (slowing as it rises after the bounce), and arcs (the parabolic path of flight). By studying real ball physics, you establish a baseline against which all other timing decisions are measured.

**Step 1: Shoot Reference Footage**

Using a phone camera or camcorder, record a ball bouncing in a controlled environment. Use a small to medium ball (tennis ball, ping-pong ball, or small rubber ball—approximately 2–4 cm diameter). Place the ball on a hard, level surface (floor, table, or concrete). Frame the shot so the ball's entire arc is visible from release to the final bounce, filling roughly 50–60% of the frame width. Shoot at a minimum of 60 fps if your camera supports it; this provides temporal resolution that you can downsample to 24 fps for analysis without losing detail. Light the scene evenly so the ball is clearly silhouetted or well-defined. Record 10–15 seconds of continuous bouncing, allowing the ball to settle after the final bounce.

Export the footage as a QuickTime or MP4 file (H.264 codec, 1920 × 1080 resolution minimum) to your computer.

**Step 2: Import and Analyze in DaVinci Resolve**

Open DaVinci Resolve (free version). Create a new project. Under *Project Settings*, set the timeline frame rate to **24 fps** even though your footage was shot at 60 fps; Resolve will interpret the footage at the frame rate you specify, allowing you to slow down the high-frame-rate footage to analyze every frame of the bounce cycle.

Create a new timeline. Drag your ball footage into the timeline. Click on the footage clip in the timeline, then right-click and select *Clip Properties* → *Retime Controls*. Set the retime speed to **40%** (which converts 60 fps footage to 24 fps equivalent timing). This slowing-down is temporary and for analysis only; you are not changing the original file.

Now scrub through the timeline frame by frame using the arrow keys on your keyboard. Identify and mark the following **key positions** in the bounce sequence using the *Color Markers* tool (click on a frame, then press M and choose a color):

1. **Release / Start Frame (Green marker)**: The frame at which the ball leaves the hand or initial position, beginning the first fall.
2. **Contact / Lowest Point (Red marker)**: The frame at which the ball contacts the ground and reverses direction. This is the apex of compression—the ball is at its lowest vertical position and momentarily stationary before spring-back.
3. **Post-Bounce Peak (Blue marker)**: The highest point the ball reaches after bouncing. The ball is momentarily stationary before gravity pulls it down again.
4. **Second Contact (Red marker)**: The ball contacts the ground a second time (bounce #2).
5. **Second Peak (Blue marker)**: The ball reaches its second post-bounce height.

Do not mark every single frame. Mark only the **key poses**—the poses that define the structure of motion. After marking a full sequence of three to five bounces, export a **still-frame image** at each marked frame. In Resolve, right-click on each marked frame and select *Export Frame*. Save each frame as a **PNG** file named `bounce_frame_01_release.png`, `bounce_frame_02_contact.png`, etc.

**Step 3: Measure Spacing and Duration**

Create a new document in a text editor or spreadsheet. List each key frame and record:

- The **absolute frame number** in the timeline (shown in the top-left corner of Resolve as HH:MM:SS:FF).
- The **duration in frames** since the last key frame.
- A **description** of the pose and its function (e.g., "Release: ball held at shoulder height, fully extended arm").

For example:

```text
Frame 0: Release (ball at shoulder height)
Frame 24: Contact (ball lowest, fully compressed)
Duration: 24 frames = 1.0 second (fall from shoulder height)

Frame 24: Contact (ball at lowest point, stationary)
Frame 36: Post-Bounce Peak (ball at 60% of original height)
Duration: 12 frames = 0.5 seconds (rise after first bounce)

Frame 36: Post-Bounce Peak (ball momentarily stationary)
Frame 48: Contact (second bounce)
Duration: 12 frames = 0.5 seconds (fall from first peak)

Frame 48: Contact (second bounce)
Frame 54: Second Peak (ball at ~40% of original height)
Duration: 6 frames = 0.25 seconds (rise after second bounce)
```

This data reveals the **temporal hierarchy** of the bounce: the initial fall takes twice as long as each subsequent rise, and each bounce loses height and duration relative to the previous one. This is the **decay curve** of bouncing motion—gravity pulls the ball down with consistent acceleration, but energy loss on each impact reduces the rebound height and speed.

**Step 4: Extract and Plot Vertical Position Over Time**

Using your marked frames, estimate the vertical pixel position of the ball center in each key frame. Use GIMP or Photoshop to open each exported PNG and read the pixel coordinates. Create a simple chart with **time (frames)** on the x-axis and **vertical position (pixels, with 0 at the top of the frame)** on the y-axis. Plot each key frame as a point. Connect the points with lines to visualize the trajectory.

You will observe a characteristic shape: the ball falls smoothly (a parabolic arc), hits the ground sharply, then rises again in a more gradual parabolic curve. Each subsequent bounce produces a smaller arc. This graph is your **motion profile**—a visual representation of how spacing changes over time.

### Part B: Drawing a Timing Chart for a Walk Cycle

A walk cycle is the second foundational animation study. Unlike a bounce (which is symmetric in space and follows simple gravity), a walk is **asymmetric, complex, and driven by muscular action**. By drawing a timing chart for a real walk, you learn to recognize the rhythm and spacing of human locomotion.

**Step 1: Shoot or Source Video Reference of a Walk**

Film yourself or a volunteer walking directly toward the camera at a normal pace. The camera should be fixed and level, shooting from approximately waist height. Use a 60 fps camera if possible, and record 10–15 seconds of continuous walking. Alternatively, source a high-quality walk cycle from an animation reference library (such as *animationresources.org* or similar).

**Step 2: Identify Gait Cycle Phases**

The human walk cycle repeats every 2 steps (left foot → right foot → left foot again). In 24 fps animation, a natural, unhurried walk cycle typically takes 48 frames (2 seconds). Within that cycle, identify these **key poses**:

1. **Frame 0 / Contact (Left)**: Left heel strikes the ground. Right leg is extended behind, beginning to swing forward. Torso is neutral.
2. **Frame 12 / Passing Position (Left)**: Left leg is vertical, bearing weight. Right leg is mid-swing, passing beneath the body.
3. **Frame 24 / Contact (Right)**: Right heel strikes the ground. Left leg is extended behind. This is the halfway point of the cycle.
4. **Frame 36 / Passing Position (Right)**: Right leg is vertical. Left leg is mid-swing.
5. **Frame 48 / Contact (Left, repeat)**: Left heel strikes again; the cycle repeats.

**Step 3: Analyze Spacing Between Key Poses**

The key poses in a walk are not evenly spaced. The **contact-to-passing** phase (8 frames) is shorter than the **passing-to-contact** phase (12 frames). This asymmetry is crucial: the passing position is a moment of transition, happening quickly, while the phase from passing to contact includes a deceleration and weight shift that feels slower. If you evenly spaced the key poses (12 frames apart), the walk would feel robotic and lifeless.

Draw a simple stick-figure timeline on paper:

```text
Frame 0 (Contact L):  |  ||
                       |/  \
                       

Frame 12 (Passing):   |  ||
                     /|   \
                    /

Frame 24 (Contact R): ||  |
                      \  /|
                       \/

Frame 36 (Passing):    || |
                        \ \|
                         \ \

Frame 48 (Contact L):   |  ||
                        |/  \
```

Below each pose, write the frame number and duration since the previous pose. The asymmetric spacing (8-12 frames instead of uniform 10-frame intervals) creates a rhythm that feels human and natural.

### Part C: Timing Chart Documentation

Create a final **Timing Chart** document (use a printed or digital template, or design your own). The chart should include:

1. **Title and Source**: "Ball Bounce Analysis – Tennis Ball" or "Walk Cycle – Natural Pace."
2. **Frame Rate and Total Duration**: "24 fps, total 48 frames (2.0 seconds)."
3. **Key Poses and Frame Numbers**: A row for each key pose, with its frame number and a simple line drawing or thumbnail image.
4. **Duration Between Poses**: A column showing the frame count and time duration (in milliseconds) between each consecutive key pose.
5. **Motion Type / Description**: A column describing the character of motion (e.g., "Acceleration (fall)", "Deceleration (bounce rebound)", "Weight shift").

Print or save this chart. You will refer to it in Exercise 2 when you animate the same motion synthetically.

### Critique Checklist for Exercise 1

Before moving forward, verify that your timing data is accurate:

- **Accuracy of Key Pose Identification**: Are your marked frames at the precise moment of contact, peak, or transition? Scrub through the footage at half speed and re-check; it is easy to be off by 1–2 frames.
- **Completeness of Measurement**: Have you recorded frame numbers and durations for a complete cycle or sequence (at least 3–5 key events)?
- **Chart Clarity**: Is your timing chart legible, with clear labels and proportionally accurate diagrams?
- **Physical Plausibility**: Do the frame counts and durations make physical sense? (e.g., Does the first fall take longer than the first rise? Does each bounce get progressively shorter?)

---

## Exercise 2: Technique Study, Step by Step — Animating Simple Shapes with Precise Timing

### Objective
Apply the timing data you extracted in Exercise 1 to create a fully animated sequence of a bouncing ball and a simplified walk cycle. By animating known, measurable motion, you train your hands and eyes to execute timing decisions with frame-accurate precision. The focus is not on artistic polish, but on matching the reference timing exactly.

### Part A: The Bouncing Ball Animation

#### Setup and Scene Preparation

Open **Krita** (free, open-source raster animation tool). Create a new document: **1920 × 1080 pixels, 300 DPI, RGB 8-bit color space**. Set the frame rate to 24 fps. Under *File* → *Settings* → *Animation*, verify that the workspace is set to "Animation" mode; Krita will display the **Timeline** panel at the bottom, showing frame thumbnails.

Create a new layer called "Ball." All animated content will live on this single layer. Create a second layer called "Background" and fill it with a solid gray (RGB 128, 128, 128) to provide visual contrast and a surface reference for the ball to interact with.

Add a third layer called "Ground Line" and draw a horizontal line at the bottom third of the canvas (y-position ≈ 720 pixels) using a black pencil brush. This line represents the ground surface and provides a spatial anchor. Lock the "Ground Line" and "Background" layers so you don't accidentally paint on them.

**Establish a spatial reference frame**: The ball should be drawn at a consistent size (approximately 60 × 60 pixels in diameter). Use the circle select tool to define a perfect circle, then stroke the selection with a 3-pixel black outline. The ball's center will be tracked as it moves through space. Mark the starting position (release point) at approximately 300 pixels from the top of the canvas. Mark the contact point (ground) at the y-position of your ground line.

#### Frame 0: Release Position

In the **Timeline**, double-click **Frame 1** to enter drawing mode. The timeline will highlight Frame 1, and the canvas will be active for painting. Using the circle select tool, create a perfect circle at your marked release position (x ≈ 960, y ≈ 150). Stroke it with a 3-pixel black outline. Hold Shift and press the right-arrow key to advance to **Frame 2**. Krita will create a new blank frame, and the previous frame will appear as an onion-skin (a faint, semi-transparent overlay).

Repeat this process for each frame according to your timing chart. Use the onion-skin overlay to verify that the ball's position is consistent from frame to frame. If the ball needs to stay stationary for multiple frames (as it does at release and at peak positions), draw it once, then hold Ctrl+D to duplicate the current frame multiple times.

#### Frames 1–24: Falling (Acceleration)

According to your reference timing chart, the ball falls from release to contact in 24 frames. During this phase, the ball accelerates due to gravity: the spacing between frames should increase (frames closer together at the start of the fall, farther apart at the end). This is the fundamental principle of **spacing for acceleration**: the visual distance between successive frames increases as speed increases.

Using your position reference data from Exercise 1, calculate the vertical drop per frame:
- Release position: y = 150 pixels.
- Contact position: y = 720 pixels.
- Total drop: 570 pixels.
- Frames: 24.

For a **linear fall** (constant acceleration under gravity), the positions should follow a quadratic spacing curve. Rather than calculating exact pixel positions mathematically, use your reference footage as a visual guide: for each frame, compare your drawn ball against the reference at the same frame offset, and adjust the y-position to match.

Draw frames 1–24 as follows:

- **Frames 1–4** (first sixth of the fall): Ball drops gradually; spacing is tight (10–15 pixels per frame).
- **Frames 5–12** (middle of the fall): Ball drops faster; spacing increases (20–30 pixels per frame).
- **Frames 13–24** (final third of the fall): Ball accelerates further; spacing is wide (30–40 pixels per frame).

As you draw, use Krita's onion-skin to verify smooth motion. If the ball jumps or stutters, adjust the intermediate frames. After completing Frame 24, play back the animation (press Space or click the Play button in the Timeline). The motion should feel like a continuous acceleration, not a series of discrete jumps.

#### Frames 24–36: Rising After First Bounce (Deceleration)

At Frame 24 (contact), the ball is at its lowest point (y ≈ 720). After the bounce, it rises to a height that is approximately 50–60% of the original release height. This corresponds to a y-position of approximately 300–350 pixels. The rise takes 12 frames.

During this phase, motion is **decelerated**: the ball starts fast (immediately after the spring-back) and slows as it reaches the peak. Spacing is wide at first, then progressively tighter:

- **Frames 25–28** (first third of the rise): Ball jumps quickly; spacing is wide (40–50 pixels per frame).
- **Frames 29–32** (middle of the rise): Motion slows; spacing narrows (25–35 pixels per frame).
- **Frames 33–36** (final approach to peak): Motion is slow; spacing is tight (10–15 pixels per frame).

#### Frames 36–48: Falling After First Bounce (Acceleration Again)

The ball now falls from the first peak (y ≈ 300) to the ground again (y ≈ 720). This fall takes 12 frames. As before, spacing increases (acceleration under gravity). The spacing profile should mirror the first fall, but compressed into fewer frames:

- **Frames 37–40**: Tight spacing (8–12 pixels per frame).
- **Frames 41–44**: Medium spacing (15–20 pixels per frame).
- **Frames 45–48**: Wide spacing (20–30 pixels per frame).

#### Frames 48–60: Second Rise and Beyond

Repeat the deceleration pattern, but with a reduced peak height (approximately 40–50% of the original release height, or y ≈ 400). Then continue the bounce cycle for 2–3 more bounces, each one progressively smaller, until the ball settles.

#### Playback and Timing Verification

Once all 60+ frames are drawn, export the animation as a **video file**. In Krita, go to *File* → *Export As*, select **MP4** or **WebM** format, and set the frame rate to **24 fps**. Name the file `bounce_animation_v01.mp4`. Play the file in a video player (VLC, Quicktime, or Resolve).

Compare your animation frame-by-frame against your reference footage. Use Resolve to load both videos side by side: create a new timeline, drag your animation into one track and the reference into another track, and sync them. Use Resolve's frame-advance tools (arrow keys) to compare each frame. Check for:

- **Accuracy of Contact Points**: Does the ball touch the ground at exactly the same frame in both animations?
- **Accuracy of Peak Heights**: Does the ball reach the same height in your animation as in the reference?
- **Smooth Spacing**: Does the motion feel as smooth and natural as the reference, without sudden jumps or slow-downs?

If you identify discrepancies, return to Krita, navigate to the offending frame, and adjust the ball's position. Re-export and re-compare. This iterative refinement is the core skill of timing: learning to see the difference between "close enough" and "correct."

### Part B: Simplified Walk Cycle Animation

#### Setup

Create a new Krita document: 1920 × 1080 pixels, 24 fps, RGB 8-bit. Create three layers: "Character," "Ground Line," and "Background." Draw the ground line and background as before.

#### Character Model: Stick Figure

For this exercise, use a **stick figure** (5 elements: head, torso, left arm, right arm, left leg, right leg). This eliminates the complexity of articulating a full body and lets you focus purely on timing and weight distribution.

Draw the stick figure at a size approximately 300–400 pixels tall. Use a consistent stroke width (2–3 pixels) for all limbs. At Frame 1 (contact left), position the figure as follows:

- **Head**: Circle at the top center (x ≈ 960, y ≈ 200).
- **Torso**: Vertical line from head to hip (y ≈ 450).
- **Left Leg**: From hip to ground (y ≈ 720), vertical and weight-bearing.
- **Right Leg**: From hip, extended backward at a 45-degree angle, toe still touching the ground (y ≈ 730).
- **Left Arm**: From torso, extended backward (opposite to the left leg's forward position in a walking gait, to show counter-rotation).
- **Right Arm**: From torso, extended forward.

This is your **Contact Left** pose. Take a screenshot or photo of it and save it as `walk_01_contact_left.png` for reference.

#### Frames 1–12: Left Leg Bearing, Right Leg Swinging Forward (Passing Position)

According to your Exercise 1 timing chart, this phase takes 8 frames at 24 fps. During this transition, the right leg swings from behind to vertical (the passing position), where the right thigh is perpendicular to the ground. The torso remains relatively stationary; the head follows the torso's slight forward motion.

- **Frame 1**: Contact Left (left leg bearing, right leg extended back).
- **Frames 2–4** (first 1/3 of swing): Right leg begins swinging forward; hip rotates slightly; left arm and right arm exchange positions gradually (counter-rotation).
- **Frames 5–8** (final 2/3 of swing): Right leg swings past vertical (passing position); weight is distributed between both legs momentarily; torso leans slightly forward.

Draw each frame, using onion-skin to verify smooth motion. The passing position should feel like a moment of balance and transition, not a static pause.

#### Frames 12–24: Right Leg Bearing, Left Leg Swinging (Second Half of Cycle)

This phase mirrors the first half but with left and right reversed. It takes 12 frames (8 for the swing + 4 for the weight shift and deceleration into contact).

- **Frames 12–16**: Right leg descends to vertical (contact right); left leg begins swinging forward; counter-rotation continues.
- **Frames 17–24** (second half of cycle): Right leg bears weight; left leg extends backward; torso vertical; weight is now on the right leg.

#### Frames 24–48: Completion of Cycle

Repeat frames 1–24 to complete one full walk cycle (48 frames total, 2 seconds at 24 fps). Duplicate your first 24 frames into frames 25–48. When played in sequence, the animation should loop smoothly: Frame 48 (Contact Left) transitions seamlessly into Frame 1 (Contact Left, repeated).

#### Timing Critique

The critical timing principle in a walk cycle is **asymmetry**: the contact-to-passing phase (8 frames) is shorter than the passing-to-contact phase (12 frames). This creates a rhythm that feels human and unhurried. If you use 10-frame intervals throughout, the walk will feel mechanical and robotic.

Export your walk cycle as `walk_cycle_v01.mp4` at 24 fps. Load it into Resolve alongside your reference footage. Use frame-by-frame comparison to verify:

- **Leg Extension Accuracy**: Do the legs reach the same angles in your animation as in the reference?
- **Weight Distribution**: Does the torso shift weight naturally from one leg to the other, or does it remain static?
- **Counter-Rotation**: Do the arms swing opposite to the legs (left arm forward when right leg forward, etc.)?
- **Cycle Length**: Does the animation loop without jumping or stuttering at Frame 48 → Frame 1 transition?

---

## Exercise 3: Finished Piece & Self-Critique — Compositing and Easing

### Objective
Integrate the bounce and walk animations into a composite scene with easing curves and secondary motion. Add a second animated element (such as a ball bouncing in the character's hand or a secondary ball bouncing at a different rhythm) and use easing curves to refine the timing, introducing subtle acceleration and deceleration that make the motion feel less mechanical.

### Part A: Creating a Composite Scene in Blender

Blender's **Dope Sheet** is the most precise instrument for visualizing and editing keyframe timing across multiple layers. Use it to composite your bounce and walk animations and to apply easing curves.

#### Setup

Open **Blender**. Delete the default cube (X → Delete). Switch to the **Animation** workspace (top menu bar). You will see the main 3D viewport, the Properties panel on the right, and the Dope Sheet timeline at the bottom.

Create two new objects:

1. **Ball 1 (Bouncing Ball)**: Add a UV Sphere (Add → Mesh → UV Sphere, default settings). Scale it down (S → 0.1) and position it at y ≈ 2 on the z-axis (the ground plane in Blender). Rename it to "Ball_Bounce."

2. **Character (Stick Figure)**: Add a simple armature (skeleton) for the stick figure. Use Blender's built-in Grease Pencil feature to draw directly onto the 3D scene, or model a simple stick figure using cylinders and spheres. For simplicity, use Grease Pencil: Add → Grease Pencil → Monkey (this is a placeholder; you can draw over it or delete it). Name it "Character_Walk."

Both objects will have an **Armature modifier** (for the stick figure) and animation data (keyframes). These keyframes will appear in the Dope Sheet.

#### Importing Animation Data

Blender's Dope Sheet expects keyframe data to be present in the scene. Since you created your animations in Krita (raster frames), you must translate them into keyframe positions. This is tedious but instructive: it forces you to record exact numerical frame data.

For the **Ball_Bounce** object, insert keyframes at each of your key positions (release, contact, first peak, second contact, etc.). To insert a keyframe:

1. Set the timeline scrubber to Frame 1 (release position).
2. Move the ball to the release y-position (z ≈ 3.0 in Blender coordinates).
3. With the ball selected, press *i* (Insert Keyframe) → *Location*.
4. Advance to Frame 24 (contact).
5. Move the ball to the contact position (z ≈ 0.0).
6. Insert a keyframe.
7. Continue for all key frames through the full bounce sequence.

Once keyframes are inserted, the Dope Sheet will display them as small white squares on a timeline. The x-axis represents frame number; the y-axis represents each object or property.

#### Applying Easing Curves

This is where timing becomes sophisticated. So far, your Krita animations used **linear spacing**: equal pixel increments between frames. Real motion, however, rarely accelerates or decelerates uniformly. Instead, it follows **easing curves**—smooth mathematical functions that describe how acceleration changes over time.

In the Dope Sheet, select a keyframe and right-click. Choose *Handle Type* → *Automatic Bezier*. This applies a smooth easing curve between the selected keyframe and the next one. The curve is now no longer linear but smoothly interpolated.

For the bounce animation, apply different easing curves to different phases:

- **Fall (Frames 1–24)**: Use *Automatic Bezier* or *Free* to create a gradual acceleration curve. The ball should start slow and end fast.
- **Rise (Frames 24–36)**: Use *Automatic Bezier* but drag the handle inward to create a sharp deceleration. The ball should start fast and end slow.

To adjust the curve manually, switch the Dope Sheet to **Graph Editor** view (click the graph icon in the top-left of the Dope Sheet panel). The timeline becomes a 2D graph: x-axis is frame number, y-axis is object position. Keyframes appear as points; curves are drawn between them. Drag the curve handles to shape the easing:

- A **flat curve** at the start means slow motion; a **steep curve** means fast motion.
- An **S-shaped curve** (slow → fast → slow) describes deceleration followed by acceleration, typical of an object bouncing.

Adjust until the visual curvature matches your reference footage.

#### Synchronizing Multiple Animations

Add a second ball (Ball_2) with a different bounce rhythm. This ball will bounce out of phase with Ball_1—perhaps starting at Frame 12 (halfway through Ball_1's cycle). This creates **polyrhythmic motion**—multiple elements moving on different timing cycles that nonetheless create a cohesive whole.

Insert keyframes for Ball_2 starting at Frame 12 and following the same bounce pattern as Ball_1, but offset by 12 frames. When both balls play together, Ball_1 and Ball_2 create an alternating rhythm: Bounce, Bounce, Bounce, Bounce—but each ball bounces at a different height and time.

This is a core principle of motion design: **layering rhythms**. No motion happens in isolation; professional animations layer multiple animated elements on interlocking timing cycles that create visual interest and temporal complexity.

#### Rendering

Once easing curves are applied and multiple animations are synchronized, render the scene. Set the output format to MP4 (Render → Output Properties → File Format → MPEG-4). Set the frame range to 1–120 (5 seconds at 24 fps). Click *Render* → *Render Animation*. Blender will produce a file `composite_animation_v01.mp4`.

### Part B: Advanced Timing Concepts—Secondary Motion and Overlapping Action

#### Principle: Secondary Motion and Overlapping Action

In professional animation, motion is never perfectly synchronized. When a character moves, different parts of the body move at different times and speeds. This is **overlapping action**: the head arrives at a position before the torso; the limbs finish moving slightly after the torso stops; and so on. Secondary motion (like hair, cloth, or a tail following the main motion) lags behind and creates a trailing, natural effect.

For this exercise, add secondary motion to your walk cycle. Modify your stick figure to include a **simple flag or tail** (a vertical line or polygon that hangs from the character's back). As the character walks, the tail lags behind the torso's motion, creating a trailing effect.

In Blender, create a simple tail by adding a Bezier curve that follows the character's hip. Add keyframes to the tail's position, but offset them by 4–6 frames relative to the torso's movement. When the torso moves forward at Frame 10, the tail doesn't start moving until Frame 14. This delay creates a natural, whip-like follow-through.

#### Principle: Anticipation

Before a character performs an action (like jumping or throwing), there is a preparatory motion in the opposite direction. This is **anticipation**: the character dips before jumping, pulls back before throwing. Anticipation creates clarity and communicates intent.

Modify your walk cycle by adding a slight downward movement (duck) just before each leg swings forward. At Frame 11 (just before the right leg passes), lower the torso by 1–2 inches. At Frame 12 (the passing position), raise the torso back to neutral. This tiny motion—occurring over just 2 frames—adds a subtle rhythm that makes the walk feel more dynamic and human.

### Part C: Exporting and Critique

Export your final composite as a **ProRes or DNxHR file** for maximum quality. In Blender, set Render → Output Properties → File Format → PNG Sequence (this exports each frame as a separate image). Then use **FFmpeg** (command-line video encoding tool) to assemble the PNG sequence into a video file:

```bash
ffmpeg -framerate 24 -i frame_%04d.png -c:v prores_ks -profile:v 3 output.mov
```

This produces a high-quality video file. Open it in DaVinci Resolve and inspect it frame by frame. Use the following critique rubric.

---

## Critique Checklist & Common Fixes

### Checklist: Accurate Timing

**Question 1: Does the motion respect the reference timing?**
- Load your animation and reference footage in Resolve side by side.
- Advance frame by frame and compare key poses.
- Measurement: Are your key frames within ±1 frame of the reference? (Tolerance is 1 frame, since small timing variations are imperceptible at playback speed.)
- **Fix**: If off by >1 frame, return to your animation file and adjust the frame position. Re-export and re-compare.

**Question 2: Does the spacing create natural acceleration and deceleration?**
- Play back your animation at normal speed (press Space in Krita or click Play in Resolve).
- Observe: Does the motion feel smooth, or does it stutter or jump?
- Measurement: Use Blender's Graph Editor to visually inspect the easing curves. The curve should be smooth and continuous, without sharp kinks or reversals.
- **Fix**: If stuttering, the spacing is too irregular. Adjust intermediate frames by drawing or by smoothing the easing curve.

**Question 3: Does overlapping action exist?**
- Focus on multi-part objects (like the stick figure's torso and limbs).
- Observe: Does each part move at a slightly different time, or do they all move in perfect synchronization?
- Measurement: In the Dope Sheet, compare keyframe timings for the torso vs. limbs. There should be a 2–4 frame offset.
- **Fix**: If everything is synchronized, add a 4-frame offset to secondary elements (limbs, tail, etc.). Re-render and re-evaluate.

### Common Issues and Fixes

**Issue 1: Motion Feels Floaty or Weightless**
- **Cause**: The spacing is even throughout the motion. The object accelerates and decelerates at equal rates (linear easing).
- **Fix**: Identify the direction of the motion. If the object is falling, increase spacing in the final frames (more space between later frames means faster motion at the end). If rising, reverse it: more space at the start, tight space at the end. Examine your reference and replicate the exact spacing.

**Issue 2: Motion Feels Mechanical or Robotic**
- **Cause**: Perfect synchronization across all moving parts; no overlapping action or secondary motion.
- **Fix**: Add a 4–6 frame offset to secondary elements (arms, hair, tail). Ensure that limbs finish moving slightly after the torso stops. The head should lag behind the torso by 1–2 frames.

**Issue 3: Character's Walk Feels Stiff or Unnatural**
- **Cause**: The legs are too vertical, or the torso is not shifting weight.
- **Fix**: Review the reference footage. In a natural walk, the torso rotates slightly (shoulders and hips twist in opposite directions). The legs should not be perfectly vertical; the stance leg should have a slight knee bend. Redraw these poses with more lifelike joint angles and weight distribution.

**Issue 4: Bounce Sequence Loses Energy Too Quickly**
- **Cause**: The rebound heights are reducing too sharply, or the timing between bounces is inconsistent.
- **Fix**: Review your reference timing data from Exercise 1. Each bounce should lose approximately 20–30% of the previous height. The timing between bounces should follow a consistent decay pattern. Adjust peak heights and frame durations to match the reference.

**Issue 5: Secondary Motion (Tail, Hair) Feels Stuck or Unnatural**
- **Cause**: The lag time (offset) is too small, or the easing is not smooth.
- **Fix**: Increase the frame offset to 6–8 frames (instead of 2–4). Apply smooth easing curves (Bezier or Catmull-Rom) to the secondary element's motion, ensuring no sharp changes in direction or speed.

### Measurement Tools and Reference

For precise timing analysis, use these tools:

1. **DaVinci Resolve Frame Counter**: Shows HH:MM:SS:FF in the top-left corner. Use this to track exact frame positions when comparing animations.
2. **Blender Graph Editor**: Displays easing curves as mathematical functions. Smooth, gradual curves indicate natural motion; sharp kinks or reversals indicate mechanical motion.
3. **Krita Onion Skin**: Enable *Show Previous Frames* (5–10 previous frames) and *Show Next Frame* (1–2 next frames). This creates a visual trace of motion over time, letting you see the entire trajectory at once.
4. **Resolve Waveform Monitor**: While not strictly for animation, this tool is useful for detecting inconsistent timing when animations are exported as video. Use it to verify that frame durations are consistent.

---

## Appendix: Easing Curve Reference and Mathematical Foundations

### Why Easing Matters: The Physics of Motion

Easing curves are not arbitrary aesthetic choices—they describe how physical forces act on objects over time. A falling object accelerates due to gravity; its acceleration is constant (9.8 m/s² on Earth), but its *velocity* increases linearly. When mapped to animation frames, this results in increasing spacing: the object travels farther each frame, so frames must be more widely spaced to show that motion smoothly.

An easing curve is a function *f(t)* where *t* is time (or frame number, normalized from 0 to 1) and *f(t)* is the object's position (or other animated property), also normalized from 0 to 1. For a linear easing, *f(t) = t* (a straight diagonal line). For acceleration, *f(t)* curves upward (a parabola, often *f(t) = t²* for simple quadratic acceleration). For deceleration, *f(t)* curves downward but flattens at the end (*f(t) = 1 - (1-t)²*).

Professional animation tools offer preset easing curves:

- **Linear**: *f(t) = t*. No acceleration or deceleration; constant speed.
- **Ease-In** (or "Ease Out" in some tools): *f(t) = t²* or *f(t) = t³*. Slow start, fast end (acceleration).
- **Ease-Out** (or "Ease In" in some tools): *f(t) = 1 - (1-t)²*. Fast start, slow end (deceleration).
- **Ease-In-Out** (or "Ease"): A combination: fast middle, slow at both ends. Formula: *f(t) = t < 0.5 ? 2t² : 1 - 2(1-t)²*.
- **Sine Easing**: *f(t) = sin(t * π/2)* (ease-in) or *cos(t * π/2)* (ease-out). Smoother than quadratic; often preferred for natural motion.
- **Cubic Easing**: *f(t) = t³* (ease-in) or *1 - (1-t)³* (ease-out). Stronger acceleration/deceleration than quadratic.

### Applying Easing Curves in Krita and Blender

**In Krita**, the easing curve tool is accessible through *Windows* → *Dockable Dialogs* → *Animation Curves*. This panel shows the easing curve for the currently selected animation curve (if one exists). For frame-by-frame animation (which is what you are doing), easing is implicitly controlled by the spacing between frames; Krita does not auto-generate easing curves from keyframes.

**In Blender**, easing is applied to keyframe interpolation. Select a keyframe in the Dope Sheet (or Graph Editor), right-click, and choose *Interpolation* → *Bezier* (smooth easing) or *Linear* (no easing). To customize the easing curve, switch to the Graph Editor, select the keyframe, and drag the curve handles. The shape of the handle determines the easing profile.

### Standard Easing Values for Common Motions

Use these as starting points:

| Motion Type | Easing Profile | Frame Duration | Relative Speed |
|-------------|----------------|----------------|-----------------|
| Free fall (gravity) | Ease-In (quadratic) | 24 frames | Slow → Fast |
| Bounce rebound (upward) | Ease-Out (quadratic) | 12 frames | Fast → Slow |
| Character walk step | Ease-In-Out (sine) | 24 frames | Slow → Fast → Slow |
| Character jump (preparation) | Ease-Out | 6 frames | Fast → Slow |
| Character jump (ascent) | Ease-Out | 12 frames | Fast → Slow |
| Character jump (descent) | Ease-In | 12 frames | Slow → Fast |
| Sliding or gliding motion | Linear | Variable | Constant |
| Hair or cloth follow-through | Ease-Out + delay | 8 frames | Fast → Slow |

---

## Final Summary and Progression Path

You have now completed three progressive exercises that build timing intuition and technical skill:

1. **Exercise 1** taught you to *observe* and *measure* real motion, extracting numerical timing data.
2. **Exercise 2** taught you to *replicate* that timing exactly, frame by frame, using hand animation and digital tools.
3. **Exercise 3** taught you to *refine* timing using easing curves, overlapping action, and secondary motion, integrating multiple animated elements into a composite scene.

By repeating these exercises with different subjects—a bouncing ball, a walk cycle, a jump, a pour of water, a swinging pendulum—you will develop an internalized sense of timing. Eventually, you will not need to measure real motion or consult reference footage; you will *know* that a jump takes 20–24 frames, that a natural walk cycle is 48 frames, that falling motion accelerates predictably. This knowledge is the foundation of professional animation.

The next step is to apply these principles to character animation with more complex rigs, to motion graphics with layered text and shapes, and to specialized domains like particle effects, fluid dynamics, and camera animation. But the core principle remains: timing is everything. All of animation is about controlling the rate and rhythm of change over time.
