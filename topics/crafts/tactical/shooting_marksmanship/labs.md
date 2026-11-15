# Operational Verification Labs: Shooting Marksmanship

## Objective & Operational Lab Setup

The discipline of precision marksmanship sits at the intersection of material science, human biomechanics, and atmospheric physics, yet it is ultimately a craft practiced by hand and verified by measurable outcome. Every shot fired is a controlled experiment: the rifle, the ammunition, the shooter's body, and the environment each contribute variables that produce a single observable result, a hole in a target whose position can be measured to a fraction of a millimeter. The purpose of these labs is to train the practitioner to treat each shot as data, to collect that data with the rigor of a machinist inspecting a tolerance, and to use quantitative analysis to drive diagnostic decisions about what to change, what to leave alone, and what to train next.

The operational environment for these labs requires three distinct work areas. The first is the firing range itself, which must accommodate distances from 25 to 500 yards at minimum. A known-distance range with surveyed target frames is ideal, but a field environment with a laser rangefinder and portable target stands will suffice provided distances are measured and recorded. The second work area is the data collection station, positioned behind the firing line, where the practitioner maintains a chronograph, a laptop or tablet running a spreadsheet application (LibreOffice Calc, Microsoft Excel, or Google Sheets), and a printed data book for redundancy. The third is the analytical bench, where post-range session data is entered into structured spreadsheets, diagnostic rubrics are applied, and the next session's training plan is derived from statistical findings.

The equipment list for the shooter is deliberately constrained to isolate fundamentals. The rifle should be a bolt-action or semi-automatic precision platform in .223 Remington, .308 Winchester, or 6.5 Creedmoor, equipped with a telescopic optic with either MOA or MIL reticle adjustments, a riflescope level, and a bipod or support bag. The practitioner needs a shot data book with grid pages for recording shot coordinates, a dial caliper or machinist's rule graduated to 0.01 inch, a chronograph capable of recording velocities to single-digit feet per second, a Kestrel or equivalent weather meter for temperature, barometric pressure, humidity, and wind speed, and a notebook for qualitative observations. Ammunition should be match-grade and of a single lot number for each session to eliminate lot-to-lot velocity variation as a confounding variable. The practitioner should bring a minimum of 200 rounds per session to support all exercises with statistical power.

The analytical toolchain centers on a master spreadsheet workbook titled `Marksmanship_Lab_Workbook.ods` containing four linked sheets: `GroupData`, `Chronograph`, `DopeCard`, and `StressTest`. Each sheet is pre-structured with formulas that auto-calculate key metrics from raw input, so the practitioner's only task at the range is to record coordinates and conditions, then enter them at the analytical bench. The formulas are provided in full in the exercises that follow, and every one is a complete, executable expression with no omitted logic.

Before any round is chambered, the practitioner establishes a zero. The zeroing protocol is itself the first analytical act: fire a three-shot group at 100 yards from a solid prone position with bipod support and a rear sandbag, measure the group's offset from the point of aim in both axes, and adjust the optic in the appropriate direction. The correction formula is straightforward. For a scope with 0.25 MOA per click, the number of clicks needed to move the point of impact to the point of aim is:

$$\text{Clicks} = \frac{\text{Offset (inches)} \times 4}{\text{Distance (yards)} / 100}$$

For example, a group 2.5 inches right and 1.5 inches low at 100 yards requires 10 clicks left (2.5 × 4 / 1) and 6 clicks up (1.5 × 4 / 1). Confirm the zero with a second three-shot group. If the second group does not center on the point of aim within one half-MOA, the problem is likely the shooter, not the optic, and the practitioner should proceed to Exercise 1 to diagnose the fundamental mechanics before adjusting the scope further.

## Exercise 1: Foundational Practical Implementation

### Group Shooting, Coordinate Measurement, and Statistical Group Analysis

The first exercise establishes the practitioner's baseline mechanical consistency by removing as many variables as possible and measuring what remains. The goal is to fire five-shot groups from a single position at a single distance, measure the spatial coordinates of each shot relative to the point of aim, and compute the group's extreme spread, mean radius, and standard deviation. These three metrics, taken together, describe both the worst-case dispersion and the average precision of the shooter-ammunition-rifle system, and they form the baseline against which every subsequent exercise is compared.

Begin at the 100-yard line with the rifle zeroed. Set up a single target, preferably a grid target with one-inch squares or a bullseye with clearly marked reference lines. The practitioner assumes a prone position with the bipod deployed on a stable surface, the rifle's stock seated firmly in the shoulder, and the rear support bag positioned under the toe of the stock. The non-firing hand pulls the rear bag into the shoulder to build consistent pressure. The firing hand does not grip the stock; it rests on the trigger with the pad of the index finger's distal joint, applying pressure straight rearward. The cheek weld is established by lowering the head naturally until the eye is behind the scope, not by muscling the head down to the stock. The practitioner closes their eyes, breathes naturally, and on a natural respiratory pause, opens their eyes. If the reticle has drifted off the target, the entire body position is adjusted, not the rifle. This process establishes the Natural Point of Aim, and it is repeated until the reticle rests on the target with the eyes opened after a full relaxation cycle.

Fire a single five-shot group. Do not adjust the rifle between shots. Do not call corrections. Fire at a natural cadence, one shot every five to seven seconds, maintaining the same respiratory pause and trigger press for each. After the group is complete, retrieve the target or photograph it with a scale reference in the frame. At the analytical bench, measure the center of each shot hole relative to the point of aim using the caliper. Record the X coordinate (horizontal, positive right) and Y coordinate (vertical, positive up) for each shot to the nearest 0.01 inch. Enter these into the `GroupData` sheet of the workbook.

The `GroupData` sheet is structured as follows. Row 1 contains headers. Columns A through C contain the shot number, X coordinate, and Y coordinate. For a five-shot group in rows 2 through 6, the formulas are:

```
Cell A2: 1
Cell A3: 2
Cell A4: 3
Cell A5: 4
Cell A6: 5
Cell B2: [X coordinate of shot 1, in inches]
Cell C2: [Y coordinate of shot 1, in inches]
```

Continue entering raw data through B6 and C6. The group centroid is computed in row 8:

```
Cell B8 (Centroid X): =AVERAGE(B2:B6)
Cell C8 (Centroid Y): =AVERAGE(C2:C6)
```

The distance from each shot to the centroid is computed in column D:

```
Cell D2: =SQRT((B2-$B$8)^2+(C2-$C$8)^2)
```

Copy this formula down through D6. The Mean Radius is:

```
Cell D8: =AVERAGE(D2:D6)
```

The Standard Deviation of the radius:

```
Cell D9: =STDEV.S(D2:D6)
```

The Extreme Spread requires computing all ten pairwise distances between the five shots and taking the maximum. Place these in column E, rows 2 through 11:

```
Cell E2:  =SQRT((B2-B3)^2+(C2-C3)^2)  // Pair 1-2
Cell E3:  =SQRT((B2-B4)^2+(C2-C4)^2)  // Pair 1-3
Cell E4:  =SQRT((B2-B5)^2+(C2-C5)^2)  // Pair 1-4
Cell E5:  =SQRT((B2-B6)^2+(C2-C6)^2)  // Pair 1-5
Cell E6:  =SQRT((B3-B4)^2+(C3-C4)^2)  // Pair 2-3
Cell E7:  =SQRT((B3-B5)^2+(C3-C5)^2)  // Pair 2-4
Cell E8:  =SQRT((B3-B6)^2+(C3-C6)^2)  // Pair 2-5
Cell E9:  =SQRT((B4-B5)^2+(C4-C5)^2)  // Pair 3-4
Cell E10: =SQRT((B4-B6)^2+(C4-C6)^2)  // Pair 3-5
Cell E11: =SQRT((B5-B6)^2+(C5-C6)^2)  // Pair 4-5
```

The Extreme Spread:

```
Cell E12: =MAX(E2:E11)
```

Convert all measurements to MOA for distance-independent comparison:

```
Cell F8 (MR in MOA):  =D8/1.047  // at 100 yards, 1 MOA = 1.047 inches
Cell E13 (ES in MOA):  =E12/1.047
```

Fire three five-shot groups in this configuration, entering each into a separate block of the `GroupData` sheet (rows 2-6 for group 1, rows 10-14 for group 2, rows 18-22 for group 3, with formulas adjusted accordingly). The practitioner is looking for three things. First, consistency: the mean radius of all three groups should agree within 15 percent. If one group is dramatically tighter or larger than the others, the shooter's mechanics are inconsistent, and the variable is the human, not the equipment. Second, location: the group centroids should cluster near the point of aim. If they do not, the zero needs refinement. Third, shape: the group should be roughly circular. A group that is elongated vertically suggests breathing inconsistency or a rear bag that is shifting. A group elongated horizontally suggests a flinch, trigger yank, or unstable bipod that is bouncing on recoil.

The diagnostic rubric for group shape is applied as follows. Compute the standard deviation of the X coordinates and the standard deviation of the Y coordinates separately:

```
Cell B9 (SD_X): =STDEV.S(B2:B6)
Cell C9 (SD_Y): =STDEV.S(C2:C6)
```

The aspect ratio:

```
Cell B10: =B9/C9
```

An aspect ratio between 0.7 and 1.4 indicates a generally circular group with no dominant directional error. An aspect ratio below 0.7 means the group is vertically elongated, pointing to a vertical-axis error such as breathing or inconsistent eye relief causing parallax shift. An aspect ratio above 1.4 means the group is horizontally elongated, pointing to a horizontal-axis error such as trigger yank or biped loading. Record the aspect ratio for each group and note the dominant error pattern in the data book. This is the diagnostic foundation for everything that follows: the practitioner cannot fix what they have not first measured and classified.

## Exercise 2: Parameter Variation & Empirical Analysis

### Distance Dope Collection, Velocity Statistics, and Positional Degradation Mapping

The second exercise shifts from static baseline measurement to controlled parameter variation. The practitioner will systematically vary three independent variables: target distance, shooting position, and ammunition velocity (as measured by chronograph), while measuring the same dependent variables as Exercise 1: group size, mean radius, and point-of-impact shift. The goal is to build an empirically verified dope card, quantify the statistical performance of the ammunition, and map the degradation in precision as the stability of the shooting position decreases. This is the lab where the spreadsheet transitions from a recording tool to a predictive instrument.

The session begins with chronograph data collection. Set up the chronograph ten feet from the muzzle, following the manufacturer's recommended distance to avoid powder-fragment false readings. Fire ten rounds over the chronograph, recording each velocity in the `Chronograph` sheet. The sheet structure is:

```
Cell A2 through A11: Shot 1 through 10
Cell B2 through B11: Velocity (fps) for each shot
Cell B13 (Mean):   =AVERAGE(B2:B11)
Cell B14 (SD):     =STDEV.S(B2:B11)
Cell B15 (ES):     =MAX(B2:B11)-MIN(B2:B11)
```

For match-grade .308 Winchester with 175-grain Sierra MatchKing bullets from a 20-inch barrel, typical values are a mean velocity of 2580 to 2670 fps with a standard deviation under 15 fps and an extreme spread under 50 fps. If the standard deviation exceeds 20 fps, the ammunition's consistency is a limiting factor and the practitioner should document this as a systemic constraint on achievable precision. The velocity standard deviation directly affects vertical dispersion at distance. A round leaving the muzzle at 2650 fps versus 2590 fps (a 60 fps spread) produces a different time of flight and therefore a different drop at 500 yards. The approximate vertical dispersion at range R due to velocity variation is:

$$\Delta Y \approx \frac{V_{SD} \times R^2}{V_{mean}^2 \times 2g \times t_{flight}}$$

In practice, for .308 at 500 yards, a 15 fps SD produces approximately 0.3 MOA of vertical dispersion from velocity variation alone. This sets the floor: if the shooter's mechanical mean radius is 0.4 MOA and the velocity SD contributes 0.3 MOA, the expected group size at 500 yards is the quadrature sum:

$$\text{Expected Group MR} = \sqrt{0.4^2 + 0.3^2} = 0.5 \text{ MOA}$$

Record this calculation in the workbook and use it as a predictive baseline against actual measured groups at distance.

The dope collection phase fires five-shot groups at 200, 300, 400, and 500 yards. At each distance, record the atmospheric conditions using the Kestrel: temperature, barometric pressure, and humidity. Record the wind speed and direction at the firing line and at the target if possible. Enter these into the `DopeCard` sheet alongside the measured drop and windage corrections. The `DopeCard` sheet structure is:

```
Row 1: Headers: Range | Drop_raw | Drop_MIL | Drop_MOA | Wind_1mph_MIL | Wind_1mph_MOA | Temp | BP | Humidity | TOF | V_remaining
Row 2: 100 | [measured drop in inches] | =B2/3.6 | =B2/1.047 | [measured] | [measured] | [temp] | [bp] | [hum] | [TOF] | [vel]
Row 3: 200 | ... | ...
Row 4: 300 | ... | ...
Row 5: 400 | ... | ...
Row 6: 500 | ... | ...
```

To collect the raw drop, fire the five-shot group and measure the vertical offset of the group centroid from the point of aim. If the group is 18 inches low at 300 yards, the raw drop is 18 inches, the MIL correction is 18 / 3.6 = 5.0 MIL, and the MOA correction is 18 / (1.047 × 3) = 5.74 MOA. The wind correction is collected by noting the wind speed and direction during the group, measuring the horizontal offset of the centroid, and normalizing to a 1 mph full-value wind. For example, a 10 mph wind from 3 o'clock (full value, 90 degrees) producing 7.5 inches of rightward drift at 300 yards yields a wind correction of 7.5 / 10 = 0.75 inches per mph, which is 0.75 / (3.6 × 3) = 0.069 MIL per mph or 0.75 / (1.047 × 3) = 0.239 MOA per mph.

The theoretical wind drift can be computed using the simplified formula:

$$D_{wind} = \frac{W \times R^2 \times \sin(\theta)}{C_w \times V_{mean}}$$

Where W is wind speed in mph, R is range in yards, θ is the wind angle relative to the bullet's path, C_w is a constant approximately 15 for .308 at these velocities, and V_mean is the mean velocity. Compare the theoretical value to the measured value. Agreement within 10 percent validates the model and confirms the shooter's wind reading. Disagreement exceeding 15 percent indicates either a wind-reading error, a crosswind that varied during the string, or a ballistic model that does not account for transonic transition at longer ranges.

The positional degradation phase returns to 100 yards and fires three five-shot groups from each of four positions: prone with bipod (the baseline from Exercise 1), prone with a sling and no bipod, kneeling with a sling, and standing with a sling. For each group, measure the mean radius and extreme spread as before. Enter the results into a summary table in the `GroupData` sheet:

```
Position          | Group MR (MOA) | Group ES (MOA) | Aspect Ratio | Notes
Prone Bipod       | [from Ex 1]    | [from Ex 1]   | [from Ex 1]  | Baseline
Prone Sling       | [measured]     | [measured]    | [measured]    | 
Kneeling Sling    | [measured]     | [measured]    | [measured]    |
Standing Sling    | [measured]     | [measured]    | [measured]    |
```

The expected progression for a competent practitioner is a mean radius of approximately 0.5 MOA from prone bipod, 0.75 MOA from prone sling, 1.5 MOA from kneeling, and 2.5 MOA from standing. The degradation factor, computed as the ratio of each position's mean radius to the prone bipod mean radius, quantifies how much the position degrades the shooter's precision:

$$\text{Degradation Factor} = \frac{MR_{position}}{MR_{baseline}}$$

A degradation factor under 2.0 for kneeling or under 4.0 for standing indicates solid positional fundamentals. A factor exceeding these thresholds points to an unstable position that must be addressed with coaching or equipment changes before the practitioner can reliably engage targets from that position under operational conditions.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Timed Engagement, Malfunction Clearance, and Performance Degradation Under Load

The third exercise removes the comfort of the static range and introduces controlled stressors: time limits, target transitions, induced malfunctions, and physical fatigue. The goal is to measure how the practitioner's precision degrades under each stressor, identify the failure threshold where group size exceeds the mission-effective standard (defined here as 2 MOA for the purposes of this lab), and practice the recovery protocols that return the shooter to baseline performance. This exercise uses the `StressTest` sheet of the workbook to record each run and compute degradation metrics.

The first drill is the Box Drill, a timed multi-target engagement that tests target acquisition, scope manipulation, and trigger control under a clock. Set up four targets at 100 yards, arranged in a square pattern two yards apart. The practitioner begins at the low ready, and on the start signal (a shot timer beep), engages each target with one round in a clockwise pattern, then one round each in a counterclockwise pattern, for a total of eight rounds. The par time is 30 seconds. Run the drill three times. Record the total time and the extreme spread of the two-shot group on each target in the `StressTest` sheet:

```
Run | Time (s) | T1 ES | T2 ES | T3 ES | T4 ES | Avg ES | Pass/Fail
1   | [time]   | [ES]  | [ES]  | [ES]  | [ES]  | =AVERAGE(C2:F2) | =IF(G2<2.094,"PASS","FAIL")
2   | [time]   | [ES]  | [ES]  | [ES]  | [ES]  | =AVERAGE(C3:F3) | =IF(G3<2.094,"PASS","FAIL")
3   | [time]   | [ES]  | [ES]  | [ES]  | [ES]  | =AVERAGE(C4:F4) | =IF(G4<2.094,"PASS","FAIL")
```

The pass threshold of 2.094 inches represents 2 MOA at 100 yards (2 × 1.047). A run passes if the average extreme spread across all four targets is under this threshold. The practitioner is looking for a time under 25 seconds with a passing group size. If the time is fast but the group size fails, the shooter is rushing the trigger press. If the group size passes but the time exceeds 30 seconds, the shooter needs work on target transitions and scope manipulation speed. Record both metrics and note which failure mode dominates.

The second drill is the Cold Bore Protocol, which tests the shooter's ability to deliver a first-round hit from a cold, uncompensated condition. The practitioner sets up a single target at 300 yards and, from a cold rifle that has not been fired that day, fires a single shot. The shot is followed immediately by a four-shot group. Measure the distance of the cold bore shot from the point of aim, then measure the mean radius and extreme spread of the subsequent four-shot group. Record in `StressTest`:

```
Run | Cold Shot Offset (in) | Cold Shot Offset (MOA) | 4-shot MR (in) | 4-shot ES (in) | 4-shot MR (MOA) | 4-shot ES (MOA) | Notes
1   | [measured] | =B2/3.141 | [measured] | [measured] | =D2/3.141 | =E2/3.141 | 
```

The 3.141 divisor converts inches to MOA at 300 yards (1 MOA = 1.047 × 3 = 3.141 inches). A cold bore offset under 1 MOA and a four-shot group mean radius under 1 MOA indicates a cold-bore-capable shooter and a consistent rifle. A cold bore offset exceeding 2 MOA, with a tight subsequent group, suggests the first-round focal shift: the shooter's eye is not settled, the scope's parallax is not adjusted, or the barrel's first shot from cold produces a different point of impact than subsequent shots. The remedy is to fire a fouling shot before beginning a precision engagement sequence, and to practice the scope setup protocol (parallax adjustment, diopter focus, eye relief verification) deliberately before every cold shot.

The third drill is the Malfunction Clearance Protocol. The practitioner's assistant randomly loads a magazine with a mix of live rounds and dummy rounds (inert cartridges with no primer or powder) that will not fire. The practitioner does not know the order. When the trigger is pressed and the rifle does not fire, the practitioner executes the immediate action drill. For a bolt-action rifle, this is: lift the bolt handle, pull the bolt fully rearward, push the bolt forward, push the bolt handle down, and fire. For a semi-automatic rifle, the drill is: slap the magazine to ensure it is seated, pull the charging handle fully rearward, release it, and fire. The timer records the time from the click of the dummy round to the next shot. Run this drill ten times with the dummy rounds randomly distributed. Record each clearance time:

```
Run | Clearance Time (s) | Hit (Y/N) | Notes
1   | [time]            | [Y/N]     | 
2   | [time]            | [Y/N]     | 
... through 10
Cell B12 (Mean): =AVERAGE(B2:B11)
Cell B13 (SD):   =STDEV.S(B2:B11)
Cell B14 (Max):  =MAX(B2:B11)
```

A competent clearance time is under 3 seconds for a bolt action and under 2.5 seconds for a semi-automatic. The standard deviation of clearance times should be under 0.5 seconds. A large standard deviation or a maximum exceeding 5 seconds indicates inconsistent motor programming, and the practitioner should dry-fire the clearance drill 50 times per session until the motion is automatic.

The fourth drill is the Fatigue Protocol, which measures the effect of elevated heart rate and muscle tremor on precision. The practitioner fires a five-shot group from prone at 100 yards as a baseline. Then performs 30 push-ups and 30 bodyweight squats in rapid succession, immediately drops into the prone position, and fires a second five-shot group. The elapsed time from completing the squats to firing the first shot is recorded. After a three-minute rest, a third five-shot group is fired to measure recovery. Record all three groups:

```
Condition      | MR (MOA) | ES (MOA) | Time to 1st shot (s) | Notes
Baseline       | [calc]   | [calc]   | N/A                  | 
Post-Fatigue   | [calc]   | [calc]   | [measured]           |
Recovery       | [calc]   | [calc]   | [measured]           |
```

The fatigue degradation factor is the ratio of the post-fatigue mean radius to the baseline mean radius. A factor under 2.0 indicates that the practitioner can maintain positional stability and trigger control under physical stress. A factor of 2.0 to 4.0 indicates moderate degradation, and the practitioner should focus on breathing protocols: after the squats, take three controlled breaths, each inhaling for four seconds and exhaling for six, to down-regulate the sympathetic nervous system before assuming the shooting position. A factor exceeding 4.0 indicates severe degradation, and the practitioner must build aerobic conditioning and practice the shooting position under elevated heart rate regularly.

The recovery group should return to within 20 percent of the baseline mean radius. If it does not, the fatigue state is persisting and the practitioner needs a longer recovery interval or has a conditioning deficit. The three-minute rest is a diagnostic, not a prescription: if recovery is incomplete in three minutes, the practitioner should extend the rest and re-measure to find their actual recovery time, then build the operational protocol around that measured value.

## Operational Reference Guide & Diagnostic Checklist

### Pre-Range Verification Checklist

Complete this checklist before every range session. Each item is a binary verification: confirmed or not confirmed. No item may be skipped.

| Verification Item | Confirmed |
|---|---|
| Rifle bore inspected clear and dry | Y / N |
| Optic mounts torqued to specification (typically 25 in-lbs for rings, 65 in-lbs for bases) | Y / N |
| Riflescope level confirmed with bubble level while rifle is in shooting position | Y / N |
| Zero confirmed at 100 yards within 0.5 MOA | Y / N |
| Ammunition of single lot number, match grade, inspected for case damage | Y / N |
| Chronograph battery checked, sky screens clean and aligned | Y / N |
| Kestrel or weather meter calibrated and current | Y / N |
| Data book and pen in hand, not in bag | Y / N |
| Ear and eye protection in place before crossing firing line | Y / N |
| Bolt or charging handle function-checked on safe and empty chamber | Y / N |

### Group Diagnostic Rubric

When a group does not meet the expected performance standard, apply this rubric in sequence. The diagnostics are ordered from most common to least common, addressing the highest-probability cause first.

**Vertical stringing** (aspect ratio below 0.7, group taller than wide): The dominant error is vertical, almost always caused by inconsistent breathing or a shifting rear support. Confirm the practitioner is firing on a natural respiratory pause, not holding breath after exhalation or firing on an inhale. Check that the rear bag is not shifting between shots; the non-firing hand should maintain consistent pressure on the bag. If the stringing exceeds 2 MOA, check for parallax error: adjust the scope's parallax until the reticle does not shift against the target when the practitioner moves their eye slightly.

**Horizontal stringing** (aspect ratio above 1.4, group wider than tall): The dominant error is horizontal, typically caused by trigger yank, a flinch, or bipod instability. Dry-fire the rifle with a coin balanced on the barrel. If the coin falls on the trigger break, the practitioner is yanking the trigger. Practice dry-fire with the coin until it stays in place through the break. If the coin stays but the group still strings, check the bipod: it should be loaded slightly forward, not perpendicular, so that recoil pushes the rifle back into a consistent position. The bipod legs should be on a surface that does not compress or slip.

**Diagonal stringing**: A group elongated at a 45-degree angle often indicates a combination of a horizontal trigger error and a vertical breathing error, or a scope that is canted. Verify the scope level with the rifle in position. If the scope is level, the diagonal indicates a compounding of two errors, and the practitioner should address the larger error first, as measured by the individual SD_X and SD_Y values.

**Flier pattern** (four shots tight, one shot distant): A single shot that departs from the group is either a shooter error or an ammunition defect. The practitioner should call every shot: note the sight picture and trigger feel at the moment of break. A called flier, where the practitioner knows the shot was off before the bullet lands, is a shooter error. An uncalled flier, where the sight picture and trigger felt correct, points to ammunition inconsistency. Sort the ammunition by bearing surface length (measured with a comparator) and segregate outliers.

**Random scatter** (no dominant direction, large mean radius with no pattern): This indicates a fundamental position problem. Return to the NPOA drill: close eyes, relax, open eyes, check reticle position. If the reticle is more than 2 MOA off the target after relaxation, the position is not natural and the practitioner is muscling the rifle onto target, introducing tension that produces random dispersion. Rebuild the position from scratch.

### Ammunition Performance Acceptance Criteria

| Metric | Acceptable | Marginal | Unacceptable |
|---|---|---|---|
| Velocity SD (10 shots) | < 12 fps | 12–20 fps | > 20 fps |
| Velocity ES (10 shots) | < 35 fps | 35–50 fps | > 50 fps |
| Bearing surface SD (30 rounds) | < 0.002 in | 0.002–0.004 in | > 0.004 in |
| Case length SD (30 rounds) | < 0.001 in | 0.001–0.002 in | > 0.002 in |

### Dope Card Validation Checklist

After completing the distance dope collection in Exercise 2, validate the dope card against theoretical predictions before trusting it in the field. For each distance, compute the theoretical drop using the ballistics solver or the simplified kinematic model and compare to the measured drop:

```
Distance | Measured Drop (MOA) | Theoretical Drop (MOA) | Delta (MOA) | Validated
100      | [from data]         | [from solver]          | =B-C        | =IF(ABS(D)<0.5,"YES","NO")
200      | [from data]         | [from solver]          | =B-C        | =IF(ABS(D)<0.5,"YES","NO")
300      | [from data]         | [from solver]          | =B-C        | =IF(ABS(D)<0.5,"YES","NO")
400      | [from data]         | [from solver]          | =B-C        | =IF(ABS(D)<0.75,"YES","NO")
500      | [from data]         | [from solver]          | =B-C        | =IF(ABS(D)<0.75,"YES","NO")
```

A delta under 0.5 MOA at 100-300 yards and under 0.75 MOA at 400-500 yards indicates a validated dope card. A larger delta indicates either an atmospheric measurement error, a zero error, or a ballistic model that is not accurately representing the bullet's drag at that velocity. If the dope card fails validation, re-shoot the failing distance with fresh atmospheric data and confirm the zero before adjusting the card.

### Post-Range Data Entry Protocol

Within 24 hours of the range session, all data must be entered into the workbook and the diagnostic rubric applied. The sequence is: enter group coordinates and compute metrics, enter chronograph data and compute statistics, enter atmospheric conditions and validate the dope card, enter stress test results and compute degradation factors, and write a qualitative summary in the data book identifying the dominant error pattern and the specific drill to address it in the next session. The next session's training plan is derived directly from this analysis, not from a preconceived schedule. If the dominant error is trigger control, the next session begins with 50 dry-fire repetitions with the coin balance drill before live fire. If the dominant error is wind reading, the next session includes a wind-reading exercise using a wind flag or mirage observation at each distance before firing. The data drives the training, not the reverse.
