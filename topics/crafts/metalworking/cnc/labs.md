# Operational Verification Labs: CNC Metalworking

## Objective & Operational Lab Setup

This guide functions as a working manual for the shop floor. Its purpose is not to introduce CNC machining abstractly but to put you through a structured sequence of verification exercises that build from fundamental machine qualification through parametric analysis and, finally, through deliberate failure and recovery. By the end of these three labs, you will have personally verified the accuracy, repeatability, and process limits of a CNC milling machine, and you will own a documented reference you can apply to any machine you operate going forward.

The target machine configuration assumed throughout is a 3-axis vertical machining center (VMC) running Fanuc-compatible G-code, equipped with an R8 or BT30/BT40 spindle, a manual or automatic tool changer, and a machine controller capable of storing at least six work coordinate offsets (G54–G59). The same exercises apply to smaller benchtop mills running Mach3, LinuxCNC, or GRBL with minor parameter scaling, and those differences are noted where relevant.

### Analytical Toolchain

The analytical environment for these labs is intentionally low-cost and reproducible. You need a digital caliper (0.01 mm resolution), a 0.0001" (0.0025 mm) resolution dial test indicator (DTI) on a magnetic base, a micrometer set covering 0–75 mm, a metrology-grade 1-2-3 block set, and a 10 mm carbide end mill (two- or four-flute, uncoated or AlTiN) as the primary cutting tool for all exercises. For analytical documentation you need a printed or digital spreadsheet with pre-built cells for recording measured versus nominal dimensions, computing error magnitude and direction, and calculating Cpk process capability. A template for this spreadsheet is defined in full in the Operational Reference Guide at the end of this document.

For workholding, use a 6" precision machine vise trammed to within 0.005 mm across its jaw face. Tramming the vise is the first physical act you will perform before any exercise begins, because every dimensional result downstream depends on it. Mount the vise, sweep the fixed jaw with the DTI along a 100 mm travel, and use a brass drift and dead-blow hammer to tap the vise into alignment. Tighten the hold-down bolts in a cross pattern and re-sweep to confirm the reading is stable under clamp torque. Record the final tram value. If you cannot achieve better than 0.01 mm across 100 mm jaw face, the vise jaw may be worn or the table surface needs cleaning and inspection for burrs.

### Work Material

All cutting exercises use 6061-T6 aluminum billet, cut to 75 mm × 75 mm × 20 mm blanks. This material is soft enough to cut dry or with isopropyl alcohol as a misting coolant, forgiving of minor parameter errors, and dimensionally stable enough to hold tolerance through multi-setup operations. Each blank should be fly-cut or surface-ground flat on both faces before the lab begins, with parallelism verified to within 0.02 mm across the full face using the micrometer. Blanks that are not parallel introduce a tilted datum that contaminates every subsequent measurement.

---

## Exercise 1: Foundational Practical Implementation

### Machine Qualification and Datum Establishment

The first exercise is entirely about verifying that the machine itself is telling the truth before you trust it with a part. A CNC machine that has not been recently qualified may have axis backlash, spindle runout, or coordinate offset errors that will silently corrupt every part it makes. You will measure all three and establish a verified G54 work coordinate system before cutting a single chip.

**Step 1 — Spindle Runout Inspection.**
Load a precision test bar (or a 10 mm ground carbide shank) into the spindle. Mount the DTI so its tip contacts the shank at the spindle nose, as close as possible to the collet face. Zero the indicator. Rotate the spindle by hand through one full revolution while watching the indicator. Record the total indicator runout (TIR). Repeat the measurement 50 mm down the shank. Acceptable TIR at the collet face is under 0.005 mm; at 50 mm, under 0.010 mm. If runout exceeds these values, the collet or holder is contaminated, the collet is worn, or the spindle bearing is damaged. Clean the taper and collet seat with a lint-free cloth and repeat before proceeding. Do not begin cutting until runout is within spec; every surface finish and diameter measurement you make afterward will be meaningless if the spindle is wobbling.

**Step 2 — Axis Backlash Measurement.**
Backlash is the mechanical slack in a ballscrew or rack-and-pinion drive that allows the axis to reverse direction without immediately moving the tool. Even machines with ballscrew compensation enabled in the controller have a residual mechanical component worth measuring directly.

Mount the DTI tip against the table edge parallel to the X axis. Command the following sequence via MDI (Manual Data Input):

    G91 G0 X10.0
    G4 P0.5
    G0 X-10.0
    G4 P0.5
    G0 X-1.0
    G4 P0.5
    G0 X1.0

Before executing, zero the indicator after the first `X10.0` move. The reading after the final `X1.0` return should be zero if there is no backlash. Any positive deviation is your X-axis backlash value. Repeat identically for Y and Z. For a machine in good condition, backlash on X and Y should be under 0.010 mm; Z is typically under 0.005 mm due to the ballscrew preload holding the quill against gravity. Record all three values in the spreadsheet. If backlash exceeds 0.025 mm on any axis, enter the value into the controller's backlash compensation register and repeat the test to confirm it is corrected before proceeding.

**Step 3 — Edge Finding and G54 Offset Establishment.**
Place a qualified 75 × 75 × 20 mm aluminum blank in the vise. Use a 10 mm diameter electronic edge finder (or a mechanical wiggler) to locate the X and Y position of the fixed jaw face and the left side of the blank. The procedure for an electronic edge finder is consistent: set spindle speed to 500 RPM, lower the edge finder so the lower ball is approximately 5 mm below the top face of the part, then feed slowly in the minus-X direction until the LED illuminates and the lower ball deflects. At that moment, stop immediately and record the machine coordinate. Subtract half the edge finder diameter (5.000 mm for a standard 10 mm body) to arrive at the true X position of the part edge. Enter this value into G54 X. Repeat for Y using the front face of the blank.

For the Z datum, use a 10 mm ground tool-setting gauge block (or a paper feeler gauge of known thickness — 0.100 mm is standard). With the actual end mill loaded, jog Z down until the gauge block slides with light drag between the cutter face and the part surface. Record the Z machine coordinate, subtract the gauge thickness, and enter this as G54 Z. Confirm by jogging Z to G54 Z=0 in MDI mode and verifying the gauge block still fits with the same drag. Discard the paper method for critical work; a tool-height setter with a repeatability of 0.002 mm costs under $40 and is worth every cent.

**Step 4 — Verification Pocket Cut.**
With G54 established, run the following program. This cuts a single 30 × 30 mm square pocket, 3 mm deep, centered on the blank:

    %
    O0001 (VERIFICATION POCKET LAB 1)
    G90 G94 G17 G21
    G28 G91 Z0
    T1 M6 (10MM 2-FLUTE CARBIDE END MILL)
    G90 G54
    S8000 M3
    G0 X-15.0 Y-15.0
    G43 H1 Z5.0
    G1 Z0.5 F500
    G1 Z-1.0 F200 (FIRST PASS 1MM DEPTH)
    G1 X15.0 F600
    G1 Y15.0
    G1 X-15.0
    G1 Y-15.0
    G0 Z0.5
    G1 Z-2.0 F200 (SECOND PASS 2MM DEPTH)
    G1 X15.0 F600
    G1 Y15.0
    G1 X-15.0
    G1 Y-15.0
    G0 Z0.5
    G1 Z-3.0 F200 (THIRD PASS 3MM DEPTH)
    G1 X15.0 F600
    G1 Y15.0
    G1 X-15.0
    G1 Y-15.0
    G0 Z5.0
    G28 G91 Z0
    M30
    %

After the program completes, do not remove the part. Measure the pocket with the digital caliper: width in X, width in Y, and depth in Z at four corners. Enter all twelve measurements into the spreadsheet. The nominal dimensions are 30.000 × 30.000 × 3.000 mm. For a first-cut verification, an error of less than ±0.05 mm in X and Y, and less than ±0.03 mm in Z, confirms the machine is functioning within acceptable limits for general work. If X reads consistently undersize or oversize relative to nominal, your G54 X datum is offset by that amount and you need to recalculate the edge-find. If the pocket is trapezoidal (X and Y differ between parallel walls), you have a tram error in the spindle or vise.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Feeds, Speeds, and Surface Finish Response

Exercise 2 builds a personal process knowledge base. Rather than operating from a chart someone else published, you will cut a matrix of test features across four different feeds and speeds combinations, measure the surface roughness empirically using a consistent drag-feel protocol and optical comparison, and correlate the results with tool wear and chip morphology. The underlying physics here is chip load: the thickness of the chip each cutting edge removes per revolution, expressed as $f_z = V_f / (N \cdot Z)$, where $V_f$ is the table feed rate in mm/min, $N$ is spindle RPM, and $Z$ is the number of cutting flutes.

The practical significance of chip load is this: too low a chip load causes the cutting edge to rub rather than shear, generating heat at the tool-workpiece interface, work-hardening the aluminum, and dulling the edge rapidly. Too high a chip load overloads the flutes and causes chatter, tool deflection, or breakage. The target chip load for a 10 mm two-flute carbide end mill in 6061-T6 aluminum is 0.05–0.10 mm per tooth. This exercise explores what happens on both sides of that window.

**Spreadsheet Setup for Parameter Matrix.**
Create a table with the following columns: Run ID, Spindle RPM, Feed Rate (mm/min), Chip Load (mm/tooth), Depth of Cut (mm), Width of Cut (mm), Measured Wall Width (mm), Error from Nominal (mm), Surface Character (1–5 scale), Chip Appearance, Tool Condition After.

The five-point surface character scale is defined as follows: 1 = severe chatter marks visible and tactile, 2 = moderate chatter, light groove pattern, 3 = acceptable milled finish, tool marks visible but not rough to touch, 4 = clean finish, light witness lines from tool passes, 5 = near-mirror finish, no perceptible tool marks. This is a qualitative field, but applied consistently by the same operator across a session it is a valid comparative instrument.

**Test Feature Geometry.**
Mill a series of 10 mm wide × 25 mm long × 3 mm deep open-slot features across the face of a fresh 75 × 75 × 20 mm blank, one slot per parameter set. Leave 10 mm between slots. Use full 10 mm width of cut (1× diameter) and 3 mm depth of cut (0.3× diameter) for all runs. Run the tool in climb milling direction for all passes to maintain consistent force direction, and take each slot in a single pass at full depth to isolate feed/speed effects clearly.

The four parameter sets to run are:

| Run | Spindle (RPM) | Feed (mm/min) | Chip Load (mm/tooth) | Condition |
|-----|--------------|----------------|----------------------|-----------|
| A   | 8000         | 320            | 0.020                | Rubbing (too low) |
| B   | 8000         | 800            | 0.050                | Low end of target |
| C   | 8000         | 1280           | 0.080                | Center of target |
| D   | 8000         | 1920           | 0.120                | High end / aggressive |

Run A deliberately produces a rubbing condition. You will see this in the chip morphology: rather than bright, curled, slightly iridescent aluminum chips, Run A produces fine dusty or powdery chips with a dull color, and the slot walls will show a glazed, work-hardened surface with possible chatter. Run B begins the proper shearing regime. Run C is the optimal operating point for this tool-material combination. Run D pushes toward the upper limit and may produce visible deflection or chatter depending on your machine's rigidity.

After cutting all four slots without touching the tool, measure the actual width of each slot at three positions along its length (entry, middle, exit) using the digital caliper inside-jaw measurement. The nominal width is 10.000 mm — the same as the tool diameter — meaning the tool is cutting full-width. Any deviation from 10.000 mm in slots B, C, and D reflects tool deflection: the cutter bends away from the cutting force, leaving the slot wider than nominal. Expect Run D to show the largest deviation, typically 0.05–0.15 mm wider on the climb side depending on the machine's rigidity. Run A may show erratic width due to rubbing and chatter rather than clean deflection.

**Chip Morphology Inspection.**
Before clearing chips from the table, collect a small sample from each slot using a magnet wand (chips are non-magnetic, so the magnet clears steel swarf only — in this case use a brush to segregate by slot). Lay the chips from each run on a white card and compare them under a 10× loupe or macro lens. Properly loaded chips from Runs C and D will be bright, slightly curled or comma-shaped ribbons of consistent thickness. Run A chips will be powder or tiny fragments. Run B chips will be thin and straight. This visual inspection takes two minutes and in production tells you instantly whether your process is running within the correct regime without touching a measurement tool.

**Calculating Cpk from Slot Width Data.**
With twelve width measurements per run (three positions × four runs), you have enough data to compute a rough process capability index for each parameter set. Enter all measurements into the spreadsheet. The upper and lower specification limits for slot width are defined as 10.000 mm nominal ± 0.050 mm (USL = 10.050, LSL = 9.950). Compute the mean $\bar{x}$ and standard deviation $\sigma$ for each set of three measurements, then compute:

$$C_{pk} = \min\left(\frac{USL - \bar{x}}{3\sigma},\ \frac{\bar{x} - LSL}{3\sigma}\right)$$

A Cpk above 1.33 indicates a capable, centered process. Run C should achieve this. Run A will likely fail the floor entirely due to chatter-induced variation. This exercise demonstrates empirically why process parameters are not arbitrary preferences but quantifiable drivers of dimensional consistency.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Deliberate Exceedance and Systematic Recovery

Exercise 3 is the most valuable and the most skipped. The purpose of deliberately inducing failure in a controlled setting is to build a visceral, physical understanding of what failure looks and sounds like before it costs you a production part or a tool. You will push the process outside its verified envelope in three ways — excessive depth of cut, datum corruption, and tool length offset error — and execute a recovery sequence for each.

**Failure Mode 1: Chatter-Inducing Depth of Cut.**
Using a fresh blank and the G54 offset verified in Exercise 1, run the same 10 mm wide slot from Exercise 2 at the optimal Run C parameters (8000 RPM, 1280 mm/min) but increase depth of cut from 3 mm to 10 mm — a 1× diameter depth, well outside the recommended 0.3× for slotting. The purpose is not to break the tool (though you should wear eye protection and stand clear), but to hear and feel the onset of chatter.

What you will hear is a characteristic harmonic screech or bark, cyclic in nature, as the tool deflects and snaps back through the cut at the natural frequency of the tool-spindle-workpiece system. The surface left in the slot will show a characteristic wave pattern at a regular spacing, the wavelength of which is determined by the chatter frequency divided by the feed rate. Measure this wavelength with the caliper after stopping the program. It is typically 0.3–1.5 mm in aluminum under these conditions.

**Recovery Protocol for Chatter.** Stop the program with feed hold, not an emergency stop, because an e-stop leaves the tool buried in the material under unknown forces. With feed hold engaged, retract Z to clear the part using MDI. Inspect the tool for chipping. If the tool is undamaged, the recovery path is to reduce depth of cut to 5 mm or less, increase RPM by 10–15% (to 9000 RPM) to shift the spindle operating frequency away from the chatter resonance, and restart with a fresh plunge into uncut material. If the tool is chipped, replace it, re-measure tool length offset with the setter, update H1 in the tool table, and restart.

Do not simply restart at the same parameters that caused chatter. The machine, tool, and material are a dynamic system, and what failed once will fail again. Changing one of the three variables — depth, speed, or radial engagement — is the minimum corrective action.

**Failure Mode 2: Corrupted Work Coordinate Offset.**
This failure mode simulates what happens when a G54 offset is entered incorrectly — the most common cause of a crash on a CNC machine operated by multiple users or after a machine reset. You will intentionally enter a wrong Z offset and observe the result in a dry-run (spindle off, feed rate overridden to 10%) before cutting.

With the Part in the vise and G54 correctly set, go into the offset table and modify G54 Z by subtracting 5.000 mm (entering a value 5 mm more negative than the correct datum). This tells the machine the part surface is 5 mm lower in space than it actually is. Run the verification pocket program from Exercise 1 with the spindle off and feed rate override at 10%. Watch the Z axis. Rather than stopping at Z0 (part surface) for the first pass and descending to Z-1.0, the machine will descend to what it believes is Z-1.0 but is actually Z+4.0 above the part — it will air-cut the entire pocketing operation. If the error had been in the positive direction (Z datum 5 mm too high), the machine would plunge 5 mm deeper than programmed into the part, potentially crashing the spindle into the vise on a shallow blank.

This exercise is physically safe because you are running spindle-off and slow. Its value is in building the habit of a dry-run air-cut before the first part of any new setup. After observing the incorrect motion, correct the G54 Z to its proper value, run the air-cut again at 10% feed to confirm correct motion, then run at full parameters.

**Recovery Protocol for Offset Corruption.** The formal recovery sequence is as follows. First, engage feed hold and check actual Z machine position on the controller display against where you expected the tool to be. Second, retract to home position (G28 G91 Z0 in MDI). Third, re-establish all three axes of G54 from scratch using the edge finder and tool setter — never attempt to calculate a correction delta from a corrupted offset, because the corrupted value may have been modified by another incorrect input you have not identified. Fourth, run a full air-cut at 10% feed rate. Fifth, run the first part at 25% feed rate override and inspect before releasing to full feed.

**Failure Mode 3: Tool Length Offset Error and Recovery.**
Load the same 10 mm end mill but deliberately enter a tool length offset in the H1 register that is 2.000 mm shorter than the actual measured length (simulate this by subtracting 2.0 from the value returned by your tool setter). This replicates the error of forgetting to re-measure after a tool change, one of the most common and consequential mistakes in CNC operation.

Run the verification pocket program in air-cut mode (spindle off, 10% feed). The Z motion will show the cutter approaching to what appears to be the correct height from the display, but physically it will stop 2 mm above the intended depth. In an actual cut, this means the machine would reach its Z-3.0 programmed depth command but only actually reach Z-1.0 of material depth. The finished pocket would measure 1.0 mm deep instead of 3.0 mm — a defect that might not be caught until final inspection in a production setting.

The recovery is mechanical rather than numerical: always re-measure every tool that enters the spindle. Use the tool-height setter, record the value, compare it to the previous entry for that tool, and investigate any discrepancy greater than 0.5 mm before running. A tool that was re-seated and re-measured should return within 0.010 mm of its previous value; a discrepancy larger than 0.050 mm indicates contamination in the taper, a pulled-back collet, or a wrong tool loaded in the holder.

**Boundary Condition: G54 Z Clearance Plane Violation.**
The final stress test explores what happens when insufficient clearance height causes the tool to drag across a part feature or clamp during a rapid traverse. Set up two 20 mm tall parallels in the vise with the blank resting on them. The blank surface is now 20 mm higher than the vise rail. In G54, set Z datum correctly to the blank surface. Now modify the program's rapid retract height from Z5.0 to Z2.0 — still above the part surface but only 2 mm above, which puts the cutter below the top of the vise jaw during any X or Y rapid move.

Run in spindle-off, 10% feed air-cut. You will see the cutter traverse across the vise jaw height during the repositioning moves. This is the geometry that causes crashes when setup height is not carefully thought through, especially after workholding changes. The recovery is to establish a clearance plane rule: the minimum safe Z retract height is the highest obstacle in the work envelope above G54 Z=0, plus 10 mm margin. For a standard 6" vise with the blank held at jaw height, this is typically Z=15 to Z=20 as the rapid clearance height in the program.

---

## Operational Reference Guide & Diagnostic Checklist

### Pre-Run Verification Checklist

This checklist is meant to be run physically on the machine before every setup, not read from memory. Print it and keep it at the control panel.

Before mounting any workholding, verify the spindle taper and collet are clean and dry. Mount the vise and tram to under 0.010 mm per 100 mm jaw. Verify table surface is free of chips and swarf that would rock the vise. Torque hold-down bolts to the vise manufacturer's specification (typically 25–35 Nm for a 6" vise on M12 studs).

After loading the workpiece, confirm it seats fully on parallels with no rock — press down at all four corners while tapping with a dead-blow; the parallels should be fully pinched. Tighten the vise and re-verify by tapping the part with the dead-blow; a solid thud rather than a ringing tone confirms full seating.

For every tool loaded, run the tool setter and record the actual H value before entering it into the offset table. Never type a tool length offset from memory or from a previous session's notes without measuring.

For every new program, run a full air-cut at 10% feed rate override with the spindle off before executing at full parameters. Watch the Z axis during the approach moves and confirm the cutter is at the correct height relative to the part surface.

### Measurement Verification Spreadsheet Structure

The following table structure is the complete recording instrument for all three exercises. Reproduce this in any spreadsheet application with formulas populated as defined.

| Field | Column | Formula |
|-------|--------|---------|
| Nominal Dimension (mm) | A | Manual entry |
| Measured Dimension 1 (mm) | B | Manual entry |
| Measured Dimension 2 (mm) | C | Manual entry |
| Measured Dimension 3 (mm) | D | Manual entry |
| Mean (mm) | E | `=AVERAGE(B:D)` |
| Std Dev (mm) | F | `=STDEV(B:D)` |
| USL (mm) | G | Manual entry |
| LSL (mm) | H | Manual entry |
| Cpu | I | `=(G-E)/(3*F)` |
| Cpl | J | `=(E-H)/(3*F)` |
| Cpk | K | `=MIN(I,J)` |
| Error from Nominal (mm) | L | `=E-A` |
| Pass / Fail (±0.05 mm) | M | `=IF(ABS(L)<0.05,"PASS","FAIL")` |

Populate one row per feature per exercise. At the end of Exercise 2, you will have four rows (one per parameter set) with Cpk values that tell the statistical story of each operating condition clearly and without subjectivity.

### Feeds and Speeds Reference for 6061-T6 Aluminum

This table covers the working range for two-flute and four-flute solid carbide end mills in 6061-T6 at 60% radial engagement (the most common slotting condition) and is calibrated for a rigid VMC with a 7.5 kW spindle. Reduce all feeds by 30% for benchtop machines or machines with more than 0.025 mm measured backlash.

| Tool Dia (mm) | Flutes | RPM   | Feed (mm/min) | Chip Load (mm/tooth) | DOC Max (mm) | WOC Max (mm) |
|--------------|--------|-------|----------------|----------------------|--------------|--------------|
| 6            | 2      | 12000 | 720            | 0.030                | 2.0          | 3.0          |
| 8            | 2      | 10000 | 960            | 0.048                | 2.5          | 4.0          |
| 10           | 2      | 8000  | 1280           | 0.080                | 3.0          | 5.0          |
| 10           | 4      | 8000  | 2400           | 0.075                | 3.0          | 5.0          |
| 12           | 2      | 7000  | 1120           | 0.080                | 4.0          | 6.0          |
| 16           | 4      | 5500  | 1760           | 0.080                | 5.0          | 8.0          |

### Diagnostic Fault Tree

When a cut produces an unexpected result, work through this sequence before changing anything. The fault tree is ordered by frequency of occurrence in a correctly maintained machine.

If the finished dimension is consistently wrong in one axis only, the first suspect is the G54 datum for that axis. Re-run the edge-find from scratch and compare the new offset value to the stored one. A discrepancy larger than 0.02 mm confirms the datum was the error source.

If the dimension varies unpredictably between passes or between parts, the suspect is backlash combined with inconsistent direction of approach. Measure backlash per the Exercise 1 protocol, check that compensation is enabled in the controller, and standardize all final finish passes to climb milling direction.

If surface finish is poor but dimensions are correct, the tool is dull or the chip load is in the rubbing regime. Replace the tool and verify chip load is above 0.05 mm/tooth. If chatter marks are present in a regular wave pattern, increase spindle speed by 10% increments until the chatter frequency shifts outside the system resonance.

If Z depth is consistently shallow across all features, the tool length offset is reading less than actual tool length. Re-measure with the tool setter and update H1. If depth varies from feature to feature within the same program, check that the cutter is not pulling out of the collet under axial cutting force — a symptom of an undertightened collet or a collet worn beyond its gripping capacity.

If the program runs but the tool never touches the material, the rapid clearance height in G54 Z is set above zero when it should be negative, or the G54 Z datum was set with the tool already below the part surface. Return to Step 3 of Exercise 1 and re-establish Z datum from the top face of the blank.

Every fault trace ends at a physical measurement or a parameter check. CNC machining produces deterministic errors with physical causes, and no fault is mysterious once you have the measurement data to anchor the investigation.
