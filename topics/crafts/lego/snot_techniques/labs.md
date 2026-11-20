# Operational Verification Labs: SNOT Techniques

## Objective & Operational Lab Setup

SNOT — Studs Not On Top — is the foundational discipline that separates decorative Lego builders from structural architects. Where standard stacking builds vertically along the Y-axis, SNOT rotates the exposed stud face to point laterally (X or Z), enabling flush surface cladding, recessed panel geometry, half-stud offset corrections, and multi-directional structural integration. Mastering SNOT is not merely an aesthetic pursuit. It is the gateway to building compound curved surfaces, accurate minifigure-scale facades, and mechanically rigid sub-assemblies that resist racking forces in directions that standard stacking cannot address.

The governing arithmetic of SNOT derives from one irreducible physical fact: the Lego system is not isotropic. A standard brick is 8 mm wide and 8 mm deep (one stud pitch in both X and Z), but only 9.6 mm tall (one brick height = 3.2 mm per plate × 3 plates). This 8:9.6 ratio, simplified to 5:6, is the number you will return to constantly. Five plates stacked equal exactly 16 mm, which equals two stud pitches. This means that a bracket or headlight brick rotated 90° and stacked five plates high will align its now-horizontal stud precisely one stud pitch from its neighbor, with no fractional gap. That single equivalence — **5 plates = 2 studs in height** — is the master key to all SNOT arithmetic.

Your lab bench must be configured before you begin the exercises. The parts inventory below is non-negotiable: gaps in this inventory will prevent you from completing the verification steps.

**Required Parts Inventory**

| Part Name | Part Number | Quantity |
|---|---|---|
| Plate 1×1 | 3024 | 40 |
| Plate 1×2 | 3023 | 20 |
| Plate 2×4 | 3020 | 10 |
| Brick 1×1 with Stud on Side (Headlight Brick) | 4070 | 20 |
| Bracket 1×2 – 1×2 (Inverted) | 99780 | 10 |
| Bracket 1×2 – 2×2 | 44728 | 10 |
| Tile 1×1 | 3070b | 30 |
| Tile 1×2 | 3069b | 20 |
| Tile 2×4 | 87079 | 10 |
| Brick 1×2 | 3004 | 20 |
| Brick 2×4 | 3001 | 10 |
| Plate 1×1 with Clip (Horizontal) | 77182 | 10 |
| Technic Brick 1×2 with Hole | 3700 | 10 |
| Axle Pin | 43093 | 10 |
| Flat Ruler (mm scale, 300 mm) | — | 1 |
| Digital Vernier Caliper (0–150 mm, 0.01 mm resolution) | — | 1 |
| Printed SNOT Verification Grid (provided at end of this guide) | — | 1 |
| Graph paper (5 mm grid, A4) | — | 2 sheets |
| Pencil and eraser | — | 1 set |

The caliper is not decorative. It will be used at precise verification checkpoints throughout the labs to confirm dimensional compliance. If you do not own a digital caliper, a good-quality analog vernier caliper reading to 0.05 mm is an acceptable substitute. Eyeballing is not a substitute.

Place a printed or hand-drawn reference grid in front of your workspace: a 10×10 stud grid marked in both stud units and millimeters (1 stud = 8 mm, 1 plate = 3.2 mm, 1 brick = 9.6 mm). You will reference this grid constantly as a sanity check on assembly geometry. Keep all parts sorted by type in separate compartments of a tray before beginning.

---

## Exercise 1: Foundational Practical Implementation

### Lab 1-A: The Headlight Brick Offset and Surface Flush Verification

The headlight brick (part 4070) is the simplest SNOT element and the most instructive starting point because its geometry encodes the entire SNOT offset problem in a single piece. The piece is a standard 1×1 brick with one anti-stud recessed into its side face rather than placed on its top. When you press a 1×1 plate into that side stud, the face of that plate sits flush with the outer surface of an adjacent standard brick stack — provided the headlight brick is positioned at the correct height.

Begin by constructing a reference wall. Take a Plate 2×4 as your base. Stack two Brick 1×2 elements on the left two studs to form a two-brick-high column, and leave the right two studs of the base plate empty. This gives you a two-brick wall segment on the left and an open bay on the right. You are now going to demonstrate the offset problem empirically before solving it.

Place a single Brick 1×2 on the right two studs of the base plate. Take a headlight brick and place it on top of that brick, with its side stud facing the left wall. Now press a Tile 1×1 into the headlight's side stud. Hold the assembly at eye level, horizontal to your line of sight. Observe that the face of the tile does not align flush with the outer face of the left wall. It sits recessed by exactly 1.6 mm — half a plate thickness — relative to that wall. Measure this with your caliper: the offset should read between 1.5 mm and 1.7 mm. Record your measurement in your lab notebook as **Measurement 1-A-i**.

This recess exists because the headlight brick places its side stud center at a height of 4.8 mm above the bottom of the brick (half of 9.6 mm), while the tile face, which is 3.2 mm thick, centers at 1.6 mm above the stud. The geometric center does not fall on a whole-plate boundary. The fix is not to add a plate on top of the headlight — that shifts the stud upward — but to insert a Plate 1×1 beneath the headlight brick before seating it.

Disassemble the right column. Place a Plate 1×1 on the right two studs of the base plate, then place the Brick 1×2 on top of that, then the headlight brick on top of that. Now press the Tile 1×1 into the side stud again. Remeasure the flush differential with your caliper. The reading should be 0.0 mm ±0.1 mm (the tolerance of Lego's molded dimensions). Record as **Measurement 1-A-ii**.

The 1-plate correction works because the plate elevates the headlight's side stud by 3.2 mm, shifting the tile face from its recessed position into perfect alignment. This is not a trick or workaround — it is the designed behavior of the system. Document this rule in your notebook as the **Headlight Base Rule**: *any headlight brick used to clad a vertical surface must sit atop a plate when its base is a plate-level datum, or atop nothing when its base is a brick-level datum one full brick above a plate base.* The choice depends entirely on whether the surrounding wall uses a brick-at-bottom or plate-at-bottom layout.

### Lab 1-B: The Bracket Method and the 2:5 Ratio in Practice

Where the headlight brick handles 1×1 or 1×2 side-stud situations, the bracket system scales to larger panels. The Bracket 1×2–2×2 (part 44728) is a right-angle element: two studs face upward and two studs face sideways, with the sideways face offset exactly one plate thickness (3.2 mm) inward from the upward face's outer edge. This offset is again the designed flush compensation, and it means that a plate pressed into the bracket's sideways studs will sit flush with a standard brick face — but only when the bracket is positioned at the arithmetically correct height.

Build a new reference base for this exercise. Take two Plate 2×4 elements and stud-connect them side by side along their 4-stud length to make a 4×4 plate base. On the left 2×4 of the base, stack five Plate 1×1 elements in a single column on the leftmost stud. Count carefully: five plates, one per click. With your caliper, measure the total height of this five-plate column from the base plate's top surface to the top of the fifth plate's top surface. The reading must be **16.0 mm ±0.2 mm**. Record as **Measurement 1-B-i**. This confirms the foundational ratio: five plates equal two stud pitches, which equals 16 mm.

Now disassemble the five-plate column. On the left 2×4 of the base, place a Bracket 1×2–2×2 with its 1×2 upward-facing studs engaging the base plate and its 2×2 sideways-facing studs pointing toward the right 2×4. Build a 2×2 panel of Tile 2×4 elements (use two Tile 2×4 elements stacked in a 2×4 configuration) and press them into the bracket's sideways studs. The panel now sits vertically, studded face outward.

On the right 2×4 of the base, stack a column of Brick 1×2 elements, two bricks high, directly adjacent to the tile panel. Hold the assembly at eye level. The face of the tile panel should be flush with the outer face of the brick column. Measure the differential: target **0.0 mm ±0.2 mm**. Record as **Measurement 1-B-ii**.

If you observe a step — either proud or recessed — the bracket is at the wrong height relative to the adjacent column. The most common error at this stage is placing the bracket directly on the base plate when the adjacent wall is built from bricks starting at plate level, or vice versa. Work through the correction systematically: add or remove one plate beneath the bracket and re-measure. Each plate change shifts the panel face by 3.2 mm. Document every iteration in your notebook: the bracket's starting configuration, the measured offset, the correction applied, and the final verified measurement. This iterative measurement discipline is the core skill of SNOT work.

### Lab 1-C: Half-Stud Offset with the SNOT Plate Stack

The half-stud offset is the most precise and least intuitive SNOT technique. It allows you to position a surface element at exactly 4 mm from its neighbor, rather than the standard 8 mm stud pitch. It is used extensively in facade work where windows, doors, or decorative tiles must center between standard stud positions.

The mechanism uses two brackets facing opposite directions on a common base, with a single Plate 1×2 bridging between them, so the plate's center sits at the half-stud point. Construct the following: take a Plate 2×4 base. On the first two studs, place a Bracket 1×2–2×2 with sideways studs facing right. On the third and fourth studs, place a second Bracket 1×2–2×2 with sideways studs facing left. The two sideways faces now point toward each other across the gap.

Press a Plate 1×2 into the sideways studs of both brackets simultaneously, one stud in each bracket. This plate is now horizontal, suspended between the two brackets, with its surface at exactly 4 mm — one half-stud — offset from the base plate surface. Measure the height of the suspended plate's top face above the base plate's top face with your caliper. Target **4.0 mm ±0.2 mm**. Record as **Measurement 1-C-i**.

This is the half-stud offset platform. Now stack a column of three plates directly on the base plate beside this assembly. The top of the third plate above the base plate sits at 9.6 mm — which is not 4 mm. The half-stud platform at 4 mm represents a position in the vertical dimension that is unreachable by standard vertical stacking, which can only produce multiples of 3.2 mm. The half-stud offset breaks that constraint precisely because the bracket geometry places the sideways stud at a non-integer-plate height. Document this observation in your notebook and annotate it with the precise measured value.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Lab 2-A: Systematic Mapping of SNOT Offsets Across Bracket Types

Having verified the two canonical SNOT offsets (zero-offset flush and half-stud offset), this exercise constructs a complete offset map for all bracket variants in your inventory. The purpose is empirical: you will measure, not calculate, the offset each bracket type introduces, then verify that the measurements match the theoretical prediction.

Prepare your graph paper. Draw a vertical axis labeled "Offset from Base (mm)" with range 0–20 mm. Draw a horizontal axis with six positions, one for each bracket test configuration you will build. Title this chart "SNOT Bracket Offset Map."

**Configuration A — Bracket 1×2–2×2 on bare base plate, sideways studs facing up:**
Place the bracket directly on a 2×4 base plate. Measure the height of the top face of the bracket's sideways stud plate (not the stud tip, but the plate face). Record the measurement and plot it on the chart.

**Configuration B — Bracket 1×2–2×2 on one Plate 1×1 spacer, sideways studs facing up:**
Insert a single Plate 1×1 beneath the bracket. Remeasure and plot.

**Configuration C — Bracket 1×2–2×2 on one Brick 1×2 spacer, sideways studs facing up:**
Replace the plate spacer with a full Brick 1×2. Remeasure and plot.

**Configuration D — Inverted Bracket 1×2–1×2 (part 99780) on bare base plate:**
Place the inverted bracket directly on the base plate, anti-stud connection downward, sideways studs facing laterally. Measure the height of the sideways stud plate face. Record and plot.

**Configuration E — Inverted Bracket on one Plate 1×1 spacer:**
Add a single plate beneath the inverted bracket. Remeasure and plot.

**Configuration F — Stacked headlight brick (4070) on bare base plate, side stud height measurement:**
Place the headlight brick on the base plate. Measure the height of the side stud's center from the base plate top surface. Because the stud tip is accessible, measure from the base to the tip of the side stud and subtract 1.8 mm (Lego stud protrusion height). Record and plot.

For each configuration, the theoretical value is derivable from the formula:

$$H_{\text{offset}} = H_{\text{spacers}} + H_{\text{bracket-stud}}$$

where $H_{\text{spacers}}$ is the total height of all plates and bricks beneath the bracket (each plate = 3.2 mm, each brick = 9.6 mm) and $H_{\text{bracket-stud}}$ is the fixed height of the bracket's sideways stud face above the bracket's base anti-stud, which for the 1×2–2×2 bracket is **3.2 mm** and for the inverted bracket 99780 is **4.8 mm**.

Fill in the theoretical column of the following table, then fill in your measured column, then compute the error:

| Configuration | Theoretical H (mm) | Measured H (mm) | Error (mm) |
|---|---|---|---|
| A: Bracket 1×2–2×2, bare base | 3.2 | ___ | ___ |
| B: Bracket 1×2–2×2, +1 plate | 6.4 | ___ | ___ |
| C: Bracket 1×2–2×2, +1 brick | 12.8 | ___ | ___ |
| D: Inverted Bracket 99780, bare | 4.8 | ___ | ___ |
| E: Inverted Bracket 99780, +1 plate | 8.0 | ___ | ___ |
| F: Headlight 4070, bare base | 4.8 | ___ | ___ |

An error within ±0.3 mm indicates a correctly assembled configuration and a well-calibrated caliper. Errors larger than 0.5 mm indicate either a stacking mistake (a hidden gap, a half-pressed connection, or a misidentified part) or caliper jaw positioning error. If you detect a large discrepancy, disassemble, re-stack with deliberate firm pressure on every connection, and remeasure before concluding there is an anomaly.

Plot all six measured values on your bar chart. The pattern that emerges is your personal, empirically verified SNOT offset reference. This chart belongs in your permanent builder's notebook and will be used in every subsequent SNOT-intensive build you undertake.

### Lab 2-B: Flush Cladding Panel — Multi-Row Verification

A single-stud SNOT connection verified in isolation is necessary but not sufficient. In practice, SNOT cladding covers multi-row panels, and geometric errors accumulate across rows. This exercise constructs a 4×5 tile panel mounted on SNOT brackets and verifies planarity across the entire surface.

Build a base frame: two Brick 2×4 elements side by side on a large base plate, forming a 4×4 stud wall one brick high. Mount four Bracket 1×2–2×2 elements across the top stud row of this wall, sideways studs pointing outward. Each bracket occupies 1×2 studs, so four brackets fill the entire 4-stud-wide top row. Now mount a 4-wide × 2-tall panel of tiles in the bracket sideways studs. Use four Tile 2×4 elements arranged 2×2 (each tile covers 2 studs × 4 studs, placed vertically, so two tiles side by side make 4 studs wide and 4 studs tall, but here tile orientation must cover the sideways studs: orient each Tile 2×4 with its 4-stud length running vertically in the SNOT panel). This gives you a smooth, stud-free face panel four studs wide and two tile-heights tall.

Place the assembly on your flat reference surface (the base plate as the datum). Using your ruler laid flat against the tile panel face, check that the ruler contacts all four corners of the panel simultaneously. If one corner lifts off the ruler, the bracket on that corner is either higher or lower than the others. Identify which corner by sliding the ruler edge along the full panel width in both horizontal and vertical sweeps.

If you detect a planarity error, the diagnostic procedure is: (1) press firmly on each bracket connection to ensure full seating, (2) check that the base wall bricks are fully seated on the base plate with no rocking, (3) verify that all four brackets are the same part number (a single mixed bracket from a different bracket variant will introduce the offset difference identified in Lab 2-A). Record the planarity status (planar or non-planar), the location of any deviation, its direction (proud or recessed), and the correction applied.

The final verified panel must pass the ruler sweep test with no visible light gap at any point. Document "PASS" or "FAIL" for each ruler sweep and record the final status as **Verification 2-B: Planarity Check**.

### Lab 2-C: Cross-Axis SNOT — Integrating X and Z Rotations

The most demanding parametric variation in SNOT work is building elements that orient studs in multiple lateral directions simultaneously. A corner column, for example, may require SNOT elements on two perpendicular faces. This exercise constructs a 2×2 corner assembly with SNOT-cladded faces on both the X-facing and Z-facing sides.

Build a 2×2×3 (width × depth × height) brick column on a base plate, using standard 2×4 bricks cut to 2×2 footprint by using pairs of 1×2 bricks. This column has four faces. You will clad the front face (Z-facing) and the right face (X-facing) with SNOT tile panels.

For the Z-face: mount two Bracket 1×2–2×2 elements with sideways studs pointing in the Z-direction, one on the first-stud row and one on the second-stud row of the front face of the column top. Because the brackets are mounted on top of bricks (not beside them), you must account for the bracket's own height. The column is currently 3 bricks tall (3 × 9.6 mm = 28.8 mm). Mount your brackets on the top of the third brick, sideways studs pointing outward, and clad with tiles as before.

For the X-face: repeat the bracket and tile mounting on the right face, same height level.

Now examine the corner where the two tile panels meet. If both panels are flush with their respective brick faces, they will meet at a 90° miter at the column corner. Measure the gap at the corner miter with your caliper. Record as **Measurement 2-C-i (corner gap, mm)**. A perfect miter has a gap of 0.0 mm, but in practice a gap of 0.1–0.3 mm is acceptable and falls within Lego molding tolerance. A gap larger than 0.5 mm indicates a mounting height discrepancy between the two bracket rows.

Adjust by adding or removing a plate beneath one bracket row and re-measure. Record all iterations. The goal is to arrive at the minimum measurable corner gap, with both tile faces flush against their respective brick columns. Document the final corner gap as the conclusion of Lab 2-C.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Lab 3-A: Connection Strength Under Lateral Shear

Standard Lego stud connections resist vertical separation well, but SNOT connections load the stud-to-anti-stud joint in a lateral shear direction, which is the connection's weakest axis. This exercise quantifies the shear resistance of SNOT-mounted panels under progressively increasing loads.

Build the reference panel from Lab 2-B: four brackets mounted on a one-brick-high wall, with a 4-wide tile panel in the sideways studs. Hold the base plate securely flat on your bench with one hand, and with the other hand press against the tile panel face with a single fingertip, increasing pressure gradually. Note the pressure level at which you detect: (a) the first detectable flex in the panel, (b) the first audible creak indicating partial stud disengagement, and (c) full separation. Record these three threshold states in your notebook as **Stress Level: Flex**, **Stress Level: Creak**, **Stress Level: Separation**.

This is a qualitative test, not a torque-meter test, but it provides calibrated physical intuition. The panel will almost certainly flex before it separates, because the brackets themselves act as short cantilever beams loaded at the stud-to-tile connection point. The flex is not a failure — it is the elastic deformation of the bracket arm under shear. Failure occurs when the stud disengages from the tile's anti-stud tube.

Repeat the test with a panel that has been reinforced by adding a Technic Brick 1×2 with Hole (part 3700) inserted into the wall directly behind one bracket, with an Axle Pin passing through the Technic brick's hole and into the bracket's arm hole (if the bracket has a compatible pinhole). Record whether this reinforcement changes the flex threshold, the creak threshold, or the separation threshold.

For most bracket configurations, the axle pin reinforcement significantly increases the flex-to-separation range: the panel will still flex (elastic deformation), but the pinned connection prevents full stud disengagement until a much higher force is applied. Document the qualitative improvement and assign each condition a descriptor: **Unreinforced** or **Pin-Reinforced**.

### Lab 3-B: Geometric Failure Modes — Over-Offset and Under-Offset Cataloguing

SNOT fails geometrically in two modes: over-offset (the cladding panel protrudes proud of the target surface) and under-offset (the panel sits recessed). Both are caused by incorrect spacer height beneath the bracket or headlight brick. This exercise deliberately induces both failure modes and verifies the recovery procedure.

**Inducing Over-Offset:** Return to the Lab 1-A setup (headlight brick flush cladding). Instead of the correct 1-plate spacer beneath the headlight, insert a Brick 1×2 beneath it (9.6 mm instead of 3.2 mm). Measure the proud offset of the tile face relative to the adjacent wall face. Record as **Failure Mode 3-B-i (over-offset, mm)**. The expected value is approximately 6.4 mm proud, calculated as: brick height (9.6) minus plate height (3.2) = 6.4 mm additional offset.

**Inducing Under-Offset:** Remove all spacers beneath the headlight brick, placing it directly on the base plate on the brick level (this was the initial uncorrected state from Lab 1-A). Remeasure the recess. Record as **Failure Mode 3-B-ii (under-offset, mm)**. Expected value: 1.6 mm recessed.

**Recovery Protocol — Step by Step:**

The recovery procedure for any SNOT offset failure follows this exact diagnostic tree, executed in order:

First, measure the actual offset error with your caliper and record its direction (proud or recessed) and magnitude.

Second, convert the error magnitude to plate equivalents by dividing by 3.2 mm. Round to the nearest whole number. For example, a 6.4 mm proud offset requires removing two plates (6.4 ÷ 3.2 = 2.0).

Third, if the calculated plate count is a non-integer (e.g., the error is 4.0 mm, which is 1.25 plates), the error is not resolvable by plate addition or removal alone. In this case, the bracket type must be changed to one with a different intrinsic stud offset (refer to your Lab 2-A offset map), and the spacer height must be recalculated from first principles using the formula: $H_{\text{spacers}} = H_{\text{target}} - H_{\text{bracket-stud}}$.

Fourth, apply the correction: add or remove the calculated number of plates beneath the bracket or headlight, rebuild the cladding panel, and re-measure. The target is 0.0 mm ±0.2 mm.

Fifth, if the corrected measurement is within tolerance, record **RECOVERY: PASS** with the final measurement. If it remains outside tolerance after two correction iterations, disassemble the entire assembly and rebuild from the base plate up, re-verifying every connection level before proceeding.

Document the complete recovery sequence for both failure modes in your notebook, including every intermediate measurement.

### Lab 3-C: Mixed-Height Wall Cladding — Integrating Bricks and Plates

The most common real-world SNOT stress case is a wall that uses both full bricks and plates at different heights within the same section, requiring SNOT elements to span across a mixed-pitch height grid. This is where offset errors accumulate and compound, and where incomplete mastery is most visible.

Build the following mixed wall on a 2×8 base plate: on the left four studs, stack from bottom to top — one Brick 1×2, one Plate 1×2, one Brick 1×2. On the right four studs, stack from bottom to top — three Plate 1×2 elements, one Brick 1×2, one Plate 1×2. Both columns must end at exactly the same height. Verify this with your ruler laid flat across the top of both columns. If there is a height discrepancy, the left column reaches 9.6 + 3.2 + 9.6 = 22.4 mm and the right column reaches 3.2 + 3.2 + 3.2 + 9.6 + 3.2 = 22.4 mm — they are equal. Measure and confirm as **Measurement 3-C-i (column height differential, mm)**, target 0.0 mm.

Now mount SNOT brackets on the top of each column, sideways studs pointing outward in the same direction, and attempt to build a single continuous tile panel across both bracket positions. The challenge: even though the columns are the same height, the brick-and-plate composition of each column creates different available correction points at different heights within each column. If you need to add a plate correction beneath the left bracket, the correction interacts with the last brick differently than it does in the right column.

Document every attempted configuration, measuring the tile panel planarity after each change. The exercise is complete when the tile panel passes the ruler sweep test from Lab 2-B. Record the final bracket height on each column (in terms of spacers used) and derive the general rule: when two columns of equal total height are built from different brick-and-plate combinations, the bracket spacer configuration must be calculated from the total height datum, not from the last piece placed. This rule — **bracket height is absolute, not relative** — is the single most important conceptual correction that separates practitioners who can SNOT consistently from those who cannot.

---

## Operational Reference Guide & Diagnostic Checklist

### The Master SNOT Arithmetic Table

The following table encodes every standard SNOT height equivalence you will encounter in practical builds. All values are exact as specified by Lego's 1:1 design standard (8 mm stud pitch, 3.2 mm plate height, 9.6 mm brick height, 1.8 mm stud protrusion).

| Height in Plates | Height in Bricks | Height in mm | Equivalent Stud Pitches | Notes |
|---|---|---|---|---|
| 1 | 0.33 | 3.2 | 0.4 | Single plate; not a stud-aligned height |
| 2 | 0.67 | 6.4 | 0.8 | Not stud-aligned |
| 3 | 1.0 | 9.6 | 1.2 | 1 brick height; not stud-aligned |
| 5 | 1.67 | 16.0 | 2.0 | **Canonical SNOT: 5 plates = 2 studs** |
| 10 | 3.33 | 32.0 | 4.0 | Double the canonical unit |
| 15 | 5.0 | 48.0 | 6.0 | Triple the canonical unit |
| 6 | 2.0 | 19.2 | 2.4 | 2 bricks; common wall height |
| 9 | 3.0 | 28.8 | 3.6 | 3 bricks; standard doorframe |

### Part Selection Decision Tree

When beginning a SNOT cladding application, work through the following decision sequence before placing a single piece.

Determine whether the target cladding surface must be flush with an adjacent standard brick face, recessed from it, or proud of it. For flush cladding, the bracket's intrinsic stud offset must equal the standard brick face offset, which is 3.2 mm (one plate) for all standard 1×2–2×2 brackets, and the spacers beneath the bracket must bring the sideways stud face into exact alignment with the adjacent wall face level. For recessed or proud surfaces (decorative panel insets or raised frames), calculate the required deviation from flush and add or subtract plates accordingly.

Determine whether the cladding spans a single connection point or a multi-row panel. Single points use headlight bricks. Multi-row panels use brackets, and the bracket count must equal the panel stud count in the mounting direction, with one bracket per two panel studs at minimum. Under-bracketing causes panel flex at the stress levels verified in Lab 3-A.

Determine whether any corner miter joints are required. Corner miters require both joining SNOT panels to be at exactly the same height datum. Build both panels before finalizing bracket heights on either one, and verify corner gap as in Lab 2-C before committing to the design.

### Diagnostic Checklist — Pre-Build Verification

Before beginning any SNOT-intensive construction, verify each item in this checklist:

— All brackets in the assembly are the same part number (or, if different types are intentionally used, the offset map from Lab 2-A has been consulted and all heights recalculated).

— The base datum (the surface from which all heights are measured) has been physically verified as level using the ruler sweep test.

— All spacer heights beneath each bracket have been calculated using the formula $H_{\text{spacers}} = H_{\text{target}} - H_{\text{bracket-stud}}$, where $H_{\text{target}}$ is the desired sideways stud face height above the base datum and $H_{\text{bracket-stud}}$ is the bracket's intrinsic stud offset (3.2 mm for 44728, 4.8 mm for 99780, 4.8 mm for headlight 4070).

— At least one test panel piece has been pressed into the sideways studs and measured for flush alignment before the full cladding panel is assembled.

### Diagnostic Checklist — Post-Build Fault Identification

If the finished SNOT panel exhibits a defect, classify it using the following fault taxonomy and apply the indicated resolution.

**Fault: Panel is uniformly proud across its entire width by X mm.**
Cause: Spacer stack is too tall by X mm. Resolution: Remove $X ÷ 3.2$ plates from beneath each bracket.

**Fault: Panel is uniformly recessed across its entire width by X mm.**
Cause: Spacer stack is too short by X mm. Resolution: Add $X ÷ 3.2$ plates beneath each bracket.

**Fault: Panel is planar but at an angle (one side proud, opposite side recessed).**
Cause: Spacer heights are inconsistent across bracket positions. Resolution: Identify the highest bracket (at the proud corner), reduce its spacer by one plate, re-measure. Iterate until the panel passes the ruler sweep test.

**Fault: Panel has a central bulge but both edges are flush.**
Cause: Base wall is not flat — the central bricks are sitting higher than the edge bricks due to an underlying stacking error. Resolution: Disassemble the base wall, lay all base bricks on a flat surface and confirm full seating with zero rocking, then rebuild the wall before remounting brackets.

**Fault: Individual tiles within the panel have visible seams or misalignment, but the panel backing is planar.**
Cause: Mixed tile thicknesses (using tiles from different production eras or counterfeit elements). Resolution: Verify all tiles are genuine Lego elements. Genuine Lego tiles from any era manufactured since 1990 are within ±0.05 mm of the 3.2 mm standard. Tiles from third-party manufacturers may differ by 0.1–0.3 mm, causing visible step faults at tile boundaries.

**Fault: Corner miter gap is larger than 0.5 mm.**
Cause: The two SNOT panels meeting at the corner are at slightly different height datums. Resolution: Return to Lab 2-C procedure, remeasure each panel's height datum independently, and adjust the lower panel's bracket spacers upward by one plate and re-verify.

### The SNOT Verification Grid

Draw the following grid on your graph paper at 1:1 scale (each square = 8 mm × 8 mm). Use it as a physical layout reference when planning SNOT assemblies. Mark each bracket position with a "B", each headlight position with an "H", and each spacer count with a numeral inside the symbol. The grid allows you to plan an entire SNOT facade before physical assembly, verify that all bracket heights are consistent, and identify any position that requires a non-standard spacer count before you discover it mid-build.

```text
 ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐  ← 10 studs wide
 │   │   │   │   │   │   │   │   │   │   │  Row 10 (80 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 9  (72 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 8  (64 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 7  (56 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 6  (48 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 5  (40 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 4  (32 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 3  (24 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 2  (16 mm)
 ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
 │   │   │   │   │   │   │   │   │   │   │  Row 1  (8 mm)
 └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
   1   2   3   4   5   6   7   8   9  10
   Col →
```

Annotate directly on this grid in pencil during planning. Erase and revise freely. The grid is your pre-flight checklist, your build blueprint, and your post-build forensic reference all in one.

The practitioner who measures before cutting, counts spacers before placing, and verifies flush before tiling will never need the recovery protocols in Lab 3-B. The practitioner who skips the measurement steps will use those protocols every time. The difference between the two builders is not talent — it is the discipline to verify what the mathematics already guarantees.
