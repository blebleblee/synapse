# Operational Verification Labs: Machining

## Objective & Operational Lab Setup

This guide functions as a working laboratory manual for the precision machinist operating in a real or analytically simulated shop environment. Each exercise is structured around verifiable outcomes: you produce measurements, you compare them against tolerances, you diagnose deviations, and you correct your process. The labs progress from foundational setup verification through parametric feeds-and-speeds analysis and into deliberate failure-mode testing, the kind of boundary work that separates a technician who follows instructions from a machinist who understands metal.

The analytical environment for these labs requires the following toolchain, all of which are native to precision metalworking practice. You need a scientific calculator or a spreadsheet application (LibreOffice Calc or Microsoft Excel), a machinist's reference handbook (Machinery's Handbook, 31st edition is the current standard), access to a speeds-and-feeds calculator such as the FSWizard desktop application or G-Wizard, a dial test indicator with 0.001 mm (0.0001 inch) resolution, a 0–25 mm outside micrometer reading to 0.001 mm, a set of gauge blocks (wrung to verify accuracy), a 6-inch digital vernier caliper, and a CNC mill or manual knee mill with a spindle tachometer. Where physical machining is not available, the analytical exercises are designed to work within a full parametric simulation using G-Wizard's material-and-tool model and the spreadsheet models constructed below. No exercise uses a placeholder value: every number comes from a defined formula, a measured reading, or a cited table.

Before beginning Lab 1, establish your reference environment. Confirm that the spindle of your machine (or the simulated machine model) is designated as a vertical knee mill with a 40-taper R8 spindle, a 1.5 kW (2 HP) motor, and a maximum spindle speed of 4,200 RPM. The workpiece material for all three labs is 6061-T6 aluminum alloy. This alloy has a Brinell hardness of approximately 95 HB, a tensile strength of 310 MPa, and it machines cleanly with carbide end mills at surface speeds that the following exercises will calculate and verify. Set your spreadsheet file to a new workbook and label the first sheet "Lab Setup." Enter the following constants in cells A1 through B6:

| Parameter | Value |
|---|---|
| Material | 6061-T6 Aluminum |
| Recommended Surface Speed Vc (m/min) | 300 |
| End Mill Diameter D (mm) | 12 |
| Number of Flutes z | 4 |
| Recommended Feed per Tooth fz (mm/tooth) | 0.05 |
| Axial Depth of Cut ap (mm) | 10 |
| Radial Depth of Cut ae (mm) | 3 |

These are your ground-truth constants. Every derived value in every exercise traces back to this table.

---

## Exercise 1: Foundational Practical Implementation

### 1.1 Spindle Speed and Feed Rate Calculation from First Principles

The relationship between recommended surface speed and actual spindle RPM is governed by a single formula that every machinist must be able to derive without looking it up. Surface speed $V_c$ describes how fast the cutting edge moves through the material in linear terms, expressed in meters per minute. The machine, however, accepts a rotational command in RPM. The conversion is:

$$n = \frac{V_c \times 1000}{\pi \times D}$$

where $n$ is spindle speed in RPM, $V_c$ is 300 m/min, and $D$ is 12 mm. Working this out: $n = (300 \times 1000) / (\pi \times 12) = 300{,}000 / 37.699 = 7{,}958$ RPM. That exceeds the 4,200 RPM limit of the reference machine, which is exactly the point. The machinist who blindly applies a table speed without checking machine capability will overrun the spindle and destroy both tool geometry and bearing preload. The correct approach is to cap $n$ at 4,200 RPM and back-calculate the actual surface speed being achieved: $V_c = (\pi \times 12 \times 4200) / 1000 = 158.3$ m/min. This is a usable, if conservative, speed for 6061-T6 with carbide tooling.

Open your spreadsheet and label a new sheet "Lab 1." In column A, enter the formula labels; in column B, enter the Excel formulas exactly as written below. This model is complete and executable.

| Cell A | Cell B Formula | Computed Result |
|---|---|---|
| Theoretical n (RPM) | `=(300*1000)/(PI()*12)` | 7,958 RPM |
| Machine Max RPM | `=4200` | 4,200 RPM |
| Actual n Used (RPM) | `=MIN(B1,B2)` | 4,200 RPM |
| Actual Vc Achieved (m/min) | `=(PI()*12*B3)/1000` | 158.3 m/min |
| Table Feed Vf (mm/min) | `=B3*4*0.05` | 840 mm/min |
| Material Removal Rate (cm³/min) | `=(B5*10*3)/1000` | 25.2 cm³/min |

The table feed formula $V_f = n \times z \times f_z$ gives you 840 mm/min. This is the programmed feed rate you would enter into an NC block or set on the knee mill's feed dial. The material removal rate (MRR) formula is $MRR = V_f \times a_p \times a_e$, with the result converted from mm³/min to cm³/min by dividing by 1,000.

### 1.2 Machine Traming and Vise Alignment Verification

Before cutting any part, the machinist must verify that the spindle axis is perpendicular to the table plane and that the fixed jaw of the vise is parallel to the table's X-axis. These two conditions are not optional niceties; they are prerequisites for any dimensional accuracy claim. Skipping them and then measuring parts is diagnostic theater.

**Tramming the spindle:** Mount a dial test indicator in the spindle using a bent-arm tramming tool. The indicator tip should sit approximately 100 mm from the spindle centerline. Rotate the spindle by hand through 360 degrees and read the full indicator sweep. Any deviation greater than 0.01 mm across a 200 mm diameter sweep indicates the head is out of tram. For a Bridgeport-style knee mill, loosen the two ram lock bolts at the turret and use a dead-blow mallet to nudge the head. Repeat the sweep. When the total indicated runout (TIR) is below 0.01 mm across a 200 mm diameter, record this result in cell B1 of a new sheet labeled "Verification Log."

**Aligning the vise:** Mount the vise on the table and place the dial indicator against the fixed jaw's machined face. Traverse the X-axis by hand across the full jaw length (typically 100 mm for a 4-inch vise). Any deviation greater than 0.02 mm requires loosening the vise hold-down bolts and tapping the vise body with a soft mallet while re-indicating. Record the final TIR in cell B2 of the Verification Log. A correctly aligned setup will read between 0.005 mm and 0.015 mm TIR on the jaw, which represents real-world surface finish variation on a ground cast-iron jaw face.

**Verification Log targets:**

| Cell | Parameter | Acceptable Limit | Record Value |
|---|---|---|---|
| B1 | Spindle Tram TIR (mm) | ≤ 0.010 mm | _Measure_ |
| B2 | Vise Jaw TIR (mm) | ≤ 0.020 mm | _Measure_ |
| B3 | Edge Finder Repeatability (mm) | ≤ 0.005 mm | _Measure_ |
| B4 | Gauge Block Stack Verification (mm) | ±0.002 mm vs. nominal | _Measure_ |

**Edge finding and work coordinate offset:** Mount an edge finder (a 10 mm shank, 10 mm tip mechanical edge finder) in the collet. With the spindle running at 600 RPM, slowly traverse the X-axis into the workpiece edge until the edge finder tip deflects. Back off until it runs true, then advance in 0.01 mm increments until the tip kicks off-center. At that moment the spindle centerline is exactly 5.000 mm from the workpiece edge. Zero the X-axis DRO and add or subtract 5.000 mm as your G54 X-axis datum. Repeat on the Y-axis. Test the repeatability of this procedure by re-indicating the same edge three times, recording each result in cells B3a, B3b, B3c of the Verification Log. The spread between maximum and minimum values must not exceed 0.005 mm for the work offset to be trusted.

### 1.3 First Toolpath Execution: Facing Pass

Program or manually set up a single facing pass across the top of the 6061-T6 workpiece using the following parameters, which are derived directly from the Lab 1 spreadsheet: spindle at 4,200 RPM, feed rate at 840 mm/min, axial depth of cut 0.5 mm (this is a finish-facing pass, not the full 10 mm depth used in MRR calculations), radial engagement equal to the full tool diameter (12 mm step-over), climb milling direction. Climb milling on aluminum with carbide tooling is correct practice: the chip forms at maximum thickness and thins as it exits, leaving a superior surface finish and reducing built-up edge formation.

After the pass, measure the resulting surface with the outside micrometer at three points across the face: left edge, center, and right edge. All three readings should agree within 0.01 mm. If the left-to-right variation exceeds this, the head is out of tram in the Y-axis plane (the in-feed direction), and the tramming procedure must be repeated with attention to the front-to-back axis. Record all three readings in cells B5, B6, and B7 of the Verification Log.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### 2.1 Building a Feeds-and-Speeds Sensitivity Matrix

The goal of this exercise is to understand, through direct calculation and empirical comparison, how changing a single process variable propagates through the entire cutting system. This is the analytical equivalent of making test cuts at different parameters and measuring the outcome. The practitioner who internalizes this matrix can diagnose chatter, tool wear, and poor surface finish by reasoning backward from observed symptoms to root cause.

Create a new spreadsheet sheet labeled "Lab 2 - Matrix." The matrix varies two independent variables: radial depth of cut $a_e$ and feed per tooth $f_z$. All other parameters are held constant at the Lab Setup values: $n = 4{,}200$ RPM, $D = 12$ mm, $z = 4$, $a_p = 10$ mm.

Build the matrix with $a_e$ values across the columns (1 mm, 3 mm, 6 mm, 9 mm, 12 mm) and $f_z$ values down the rows (0.025, 0.040, 0.050, 0.065, 0.080 mm/tooth). Each cell contains the calculated MRR in cm³/min. The formula for a given cell, say intersection of $a_e = 3$ mm and $f_z = 0.05$ mm/tooth, is:

$$MRR = \frac{(n \times z \times f_z) \times a_p \times a_e}{1000}$$

In spreadsheet terms, with $n$ in a named cell or absolute reference at $4200$ and the row/column headers used as inputs, cell C4 (intersection of $a_e = 3$ mm and $f_z = 0.05$) would contain: `=($B$1*4*(C$1))*$A$2*($A4)/1000` where B1 = 4200, C1 = ae column value, A2 = ap = 10, and A4 = fz row value. Complete MRR matrix, all values in cm³/min:

| fz \ ae | 1 mm | 3 mm | 6 mm | 9 mm | 12 mm |
|---|---|---|---|---|---|
| 0.025 mm/tooth | 4.2 | 12.6 | 25.2 | 37.8 | 50.4 |
| 0.040 mm/tooth | 6.72 | 20.2 | 40.3 | 60.5 | 80.6 |
| 0.050 mm/tooth | 8.4 | 25.2 | 50.4 | 75.6 | 100.8 |
| 0.065 mm/tooth | 10.9 | 32.8 | 65.5 | 98.3 | 131.0 |
| 0.080 mm/tooth | 13.4 | 40.3 | 80.6 | 121.0 | 161.3 |

### 2.2 Chip Thinning Correction at Low Radial Engagement

One of the most consequential and least understood relationships in milling is chip thinning. When a machinist reduces the radial depth of cut below 50% of the tool diameter (below 6 mm in this case), the actual chip thickness becomes thinner than the programmed feed per tooth. This is a geometric consequence of the arc of engagement shortening: the chip forms over a smaller portion of the flute's rotational path, and the cutting edge sees less material per pass than the feed rate suggests. If the machinist does not compensate by increasing the feed rate, the tool is effectively rubbing at the beginning of the cut rather than cutting, which generates heat, accelerates flank wear, and defeats the purpose of using a light radial pass.

The chip thinning correction factor is:

$$f_{z,corrected} = \frac{f_z}{\sqrt{1 - \left(1 - \frac{2 \times a_e}{D}\right)^2}}$$

For $a_e = 1$ mm, $D = 12$ mm, and a target $f_z = 0.05$ mm/tooth:

$$f_{z,corrected} = \frac{0.05}{\sqrt{1 - \left(1 - \frac{2}{12}\right)^2}} = \frac{0.05}{\sqrt{1 - (0.8333)^2}} = \frac{0.05}{\sqrt{1 - 0.6944}} = \frac{0.05}{\sqrt{0.3056}} = \frac{0.05}{0.5528} = 0.0905 \text{ mm/tooth}$$

Add a second block to your Lab 2 sheet computing this correction across the same five $a_e$ values:

| ae (mm) | Raw fz (mm/tooth) | Chip Thinning Factor | Corrected fz (mm/tooth) | Corrected Vf (mm/min) |
|---|---|---|---|---|
| 1 | 0.050 | 0.5528 | 0.0905 | 1,520 |
| 3 | 0.050 | 0.7454 | 0.0671 | 1,127 |
| 6 | 0.050 | 1.0000 | 0.0500 | 840 |
| 9 | 0.050 | — (>50%) | 0.0500 | 840 |
| 12 | 0.050 | — (full slot) | 0.0500 | 840 |

The spreadsheet formula for the chip thinning factor at any $a_e$ is: `=IF(A2/12<0.5, 1/SQRT(1-(1-2*A2/12)^2), 1)` where A2 is the $a_e$ value. This IF statement correctly switches off the correction at and above 50% radial engagement, where the formula returns 1.0 and no adjustment is needed.

### 2.3 Empirical Surface Finish Analysis Using Ra Estimation

Surface roughness in milling is not arbitrary. The theoretical arithmetic mean roughness $Ra$ produced by a ball-nose or flat end mill on a facing pass can be estimated from tool geometry and feed parameters. For a flat end mill performing a face or shoulder mill pass, the dominant roughness contribution comes from the feed marks left between successive tool passes, and from the feed-per-revolution scallop in the axial direction. The empirical model for feed-direction Ra on a flat end mill with corner radius $r = 0$ (sharp corner) is:

$$Ra_{theoretical} = \frac{f_r^2}{32 \times r}$$

where $f_r$ is the feed per revolution in mm. Since we are using a 4-flute end mill, $f_r = f_z \times z = 0.05 \times 4 = 0.20$ mm/rev. For a tool with a 0.5 mm corner radius (a standard metric 4-flute, 12 mm end mill with a 0.5 mm chamfer), Ra theoretical becomes $(0.20)^2 / (32 \times 0.5) = 0.04 / 16 = 0.0025$ mm = 2.5 µm. That places the finish in the N7 ISO surface finish range, which is consistent with a standard milling pass. Add this calculation to your Lab 2 sheet and vary $f_z$ from 0.025 to 0.080 to observe the Ra sensitivity:

| fz (mm/tooth) | fr (mm/rev) | Ra theoretical (µm) | ISO Roughness Grade |
|---|---|---|---|
| 0.025 | 0.100 | 0.63 | N6 |
| 0.040 | 0.160 | 1.60 | N7 |
| 0.050 | 0.200 | 2.50 | N7 |
| 0.065 | 0.260 | 4.23 | N8 |
| 0.080 | 0.320 | 6.40 | N8 |

If you have a surface roughness comparator plate (a shop standard set of machined Ra reference samples), measure your actual facing pass against the N7 target. The measured Ra should fall within one ISO grade of the theoretical prediction. A result coarser than N8 on a 6061-T6 facing pass at these parameters indicates either a worn tool, an out-of-tram head producing a slight angular scallop, excessive spindle runout, or vibration from an insufficiently clamped workpiece.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### 3.1 Deliberate Overload Analysis: Finding the Torque Limit

A machinist who has only ever operated within safe parameters will freeze when a tool breaks, a spindle stalls, or a workpiece pulls from the vise. This exercise maps the boundary conditions analytically before the machinist encounters them in metal, and establishes the diagnostic and recovery procedure for each failure mode.

The spindle motor on the reference machine produces 1.5 kW at the spindle. The torque available at a given RPM is $T = P / \omega$ where $\omega = 2\pi n / 60$. At 4,200 RPM: $\omega = 2\pi \times 4200 / 60 = 439.8$ rad/s. Therefore $T = 1500 / 439.8 = 3.41$ N·m. This is the maximum torque the motor can sustain continuously before the drive trips on overcurrent or the belt begins slipping.

The cutting torque required by the end mill is estimated from:

$$T_{cut} = \frac{MRR \times k_c}{60 \times 1000 \times 2\pi \times n / 60}$$

where $k_c$ is the specific cutting force for 6061-T6 aluminum, approximately 700 N/mm². Rearranging via the power consumption route is cleaner: $P_{cut} = MRR \times k_c / 60$, with MRR in mm³/s. At the maximum matrix entry of 161.3 cm³/min = 161,300 mm³/min = 2,688 mm³/s: $P_{cut} = 2688 \times 700 / 1000 = 1,882$ W. That exceeds the 1,500 W machine limit by 25%. The machine will attempt to maintain spindle speed, draw overcurrent, trip the drive, and possibly stall. This is the analytical failure boundary.

Build a "Lab 3 - Stress Test" sheet and enter this power model for all 25 matrix combinations from Lab 2. Flag any cell where $P_{cut} > 1500$ W in red using Excel conditional formatting: `=IF(computed_power > 1500, "OVERLOAD", "OK")`. The overload threshold formula for a given MRR is: `=A2*700/1000` where A2 contains MRR in mm³/s (convert from your cm³/min values by multiplying by 1000/60). Applying this across the matrix:

| fz \ ae | 1 mm | 3 mm | 6 mm | 9 mm | 12 mm |
|---|---|---|---|---|---|
| 0.025 | OK | OK | OK | OK | OK |
| 0.040 | OK | OK | OK | OK | OK |
| 0.050 | OK | OK | OK | OK | OK |
| 0.065 | OK | OK | OK | OK | **OVERLOAD** |
| 0.080 | OK | OK | OK | **OVERLOAD** | **OVERLOAD** |

This confirms that the reference machine's power envelope is the limiting constraint at high $a_e$ and $f_z$ combinations, not the spindle speed or tool geometry. Any programmed toolpath using $f_z = 0.065$ mm/tooth at full slot (12 mm ae) or $f_z = 0.080$ mm/tooth at $a_e \geq 9$ mm will stall the drive.

### 3.2 Tool Deflection and Thin-Wall Failure Mode

A second class of failure, more insidious than motor overload because it produces dimensional error rather than a sudden stop, is end mill deflection. A 12 mm carbide end mill behaves as a cantilevered beam under radial cutting forces. The deflection at the tool tip is:

$$\delta = \frac{F_r \times L^3}{3 \times E \times I}$$

where $F_r$ is the radial cutting force in Newtons, $L$ is the stick-out length from the collet face to the flute tip, $E$ is Young's modulus for cemented carbide (580 GPa = 580,000 N/mm²), and $I$ is the second moment of area for a solid circular cross-section: $I = \pi D^4 / 64 = \pi \times 12^4 / 64 = 1017.9$ mm⁴.

Estimate $F_r$ from the tangential force at the Lab Setup condition: $F_t = k_c \times a_p \times a_e \times f_z / D_{effective}$. Using the simpler power-based approach: at $P_{cut} = 1250$ W (the loaded condition at $f_z = 0.065$, $a_e = 9$ mm, within the OK zone at the boundary), $F_t = P_{cut} \times 60 / (V_c) = 1250 \times 60 / (158.3 \times 1000 / 1000)= 1250 / (2.638) \approx 474$ N. The radial force $F_r \approx 0.3 \times F_t$ for aluminum with carbide tooling, giving $F_r \approx 142$ N.

For a tool with 35 mm stick-out from the collet (a common value when clearing a 25 mm workpiece height with a standard holder):

$$\delta = \frac{142 \times 35^3}{3 \times 580{,}000 \times 1017.9} = \frac{142 \times 42{,}875}{1{,}775{,}130{,}000} = \frac{6{,}088{,}250}{1{,}775{,}130{,}000} = 0.00343 \text{ mm}$$

That deflection of 3.4 µm is well within the 0.025 mm tolerance of a standard machined fit. However, if stick-out increases to 60 mm to reach the bottom of a deep pocket, the deflection scales with the cube of length: $\delta_{60} = 0.00343 \times (60/35)^3 = 0.00343 \times 5.03 = 0.0172$ mm. At 80 mm stick-out: $\delta_{80} = 0.00343 \times (80/35)^3 = 0.00343 \times 11.9 = 0.041$ mm, which exceeds the tolerance and will produce a noticeably out-of-tolerance wall. Build this deflection model into your Lab 3 sheet:

| Stick-out L (mm) | Fr (N) | δ (mm) | Within 0.025 mm tolerance? |
|---|---|---|---|
| 25 | 142 | 0.00124 | YES |
| 35 | 142 | 0.00343 | YES |
| 50 | 142 | 0.0100 | YES |
| 60 | 142 | 0.0172 | YES |
| 70 | 142 | 0.0273 | **NO** |
| 80 | 142 | 0.0411 | **NO** |

The recovery protocol for stick-out-induced dimensional error follows a strict sequence. First, reduce stick-out to the minimum required to clear the part feature by no more than 5 mm. Second, take a spring pass: re-run the finish toolpath at zero programmed depth of cut, allowing the elastic springback of the toolholder-spindle system to remove the remaining material from the deflection bow. Third, measure the wall with a caliper or micrometer and compare against nominal. If the error persists after the spring pass, the tool is worn or the collet is running with excessive TIR (greater than 0.015 mm), which amplifies the effective radial force. Check collet TIR with the dial indicator before removing the tool.

### 3.3 Workholding Failure and Vise Pull-Out Force Verification

The third boundary condition in this exercise set is workpiece movement during cutting. A part that shifts in the vise invalidates every measurement made afterward and can send a tool through the machined wall. The holding force of a standard 4-inch milling vise with a 7/8-inch lead screw tightened to 30 N·m of torque is approximately 8,000–12,000 N (determined by the lead screw efficiency: $F_{clamp} = 2\pi \eta T / l$ where $\eta \approx 0.3$ for a dry steel lead screw and $l = 3.175$ mm pitch). Using a moment wrench set to 30 N·m: $F_{clamp} = (2\pi \times 0.3 \times 30) / 0.003175 = 56.55 / 0.003175 = 17,811$ N. With a friction coefficient of 0.15 between a parallel (steel) and aluminum workpiece, the maximum resisting friction force is $F_{friction} = \mu \times F_{clamp} = 0.15 \times 17{,}811 = 2{,}672$ N. The maximum cutting force across any Lab 2 matrix condition was approximately 474 N. The safety factor is $2672 / 474 = 5.6$, well above the minimum acceptable factor of 3.0 for rigid workholding.

The failure condition occurs when the contact area is reduced: a thin (3 mm) workpiece sitting on a single parallel with only 3 mm of contact on the fixed jaw has dramatically reduced friction area and can rock under pulsating cutting forces. For any workpiece with a height-to-width aspect ratio greater than 2:1, add a second parallel to distribute the clamping load, and place a round bar or sacrificial shim against the jaw to prevent tipping. Record these conditions in your Verification Log.

---

## Operational Reference Guide & Diagnostic Checklist

This reference section consolidates every critical parameter, formula, and decision threshold from the three exercises into a single-page audit framework. The machinist should run through this checklist before any first cut on a new setup.

### Master Parameter Reference Table

| Parameter | Symbol | Formula | Lab Setup Value |
|---|---|---|---|
| Spindle Speed | n (RPM) | $(V_c \times 1000) / (\pi \times D)$ | 4,200 RPM (machine-limited) |
| Actual Surface Speed | Vc (m/min) | $(\pi \times D \times n) / 1000$ | 158.3 m/min |
| Table Feed Rate | Vf (mm/min) | $n \times z \times f_z$ | 840 mm/min |
| Material Removal Rate | MRR (cm³/min) | $(V_f \times a_p \times a_e) / 1000$ | 25.2 cm³/min |
| Chip Thinning Factor | CTF | $1 / \sqrt{1-(1-2a_e/D)^2}$ when $a_e < D/2$ | 0.75 at ae=3 mm |
| Corrected Feed per Tooth | fz,corr | $f_z \times CTF$ | 0.067 mm/tooth at ae=3 mm |
| Spindle Power Required | Pcut (W) | $MRR_{mm³/s} \times k_c / 1000$ | ≤1,500 W limit |
| Tool Tip Deflection | δ (mm) | $F_r \times L^3 / (3EI)$ | ≤0.025 mm for H7 tolerance |
| Theoretical Ra | Ra (µm) | $f_r^2 / (32 \times r)$ | 2.5 µm at fz=0.05 |
| Clamp Safety Factor | SF | $F_{friction} / F_{cutting}$ | Minimum 3.0 |

### Diagnostic Decision Tree

The following decision tree is the working troubleshooting protocol. Run through it in sequence; do not skip stages.

**Symptom: Chatter (audible vibration, washboard surface pattern)**

Begin by checking spindle speed. If the RPM is at or near a natural resonance of the tool-workpiece-fixture system, a 10–15% RPM increase or decrease will often move the system out of the resonant zone. If chatter persists, check stick-out: any stick-out exceeding 4× the tool diameter (48 mm for a 12 mm end mill) is structurally suspect and should be reduced. If the stick-out is acceptable, verify that the vise is tight against its hold-down bolts (not just the workpiece clamping force) and that the table locks are engaged on axes not in use. If chatter remains after all physical checks, reduce radial depth of cut by 50% and re-run. Chatter that disappears with reduced ae but returns at the original ae is a system rigidity problem, not a feeds-and-speeds problem.

**Symptom: Poor surface finish (rough, torn surface on 6061-T6 aluminum)**

This almost always indicates one of three causes. First, built-up edge: aluminum is welding to the tool's cutting edge due to insufficient cutting speed or the wrong coating (bare carbide or TiN is preferred for aluminum; TiAlN is designed for steel and runs too hot for aluminum, promoting adhesion). Increase spindle speed toward the recommended 300 m/min limit; if the machine allows it. Second, dull tool: a 12 mm carbide end mill on 6061-T6 should produce good finish for 50–80 linear meters of cutting under these parameters. If you are beyond that, replace the tool. Third, excessive feed per revolution: if $f_r > 0.25$ mm/rev, Ra will exceed N7 and the surface will appear visually rough. Verify your feed calculation against the Lab 1 spreadsheet.

**Symptom: Dimensional error (measured part is oversize or undersize relative to program)**

Oversize walls (measured larger than programmed) indicate tool deflection away from the wall during the finish pass. Apply the spring pass protocol from Exercise 3.2. Undersize walls (measured smaller) indicate either a tool that cut more than programmed because of an incorrect work offset, a vise that allowed workpiece movement (check the Verification Log safety factor), or a worn tool that pulled into the cut. Verify the G54 origin using the edge finder procedure from Exercise 1.2.

**Symptom: Machine stall or drive trip during cut**

This is a power overload event. Cross-reference your MRR against the power matrix from Exercise 3.1. Reduce either $a_e$ or $f_z$ until the computed $P_{cut}$ falls below 1,200 W (leaving a 20% safety margin against the 1,500 W limit). Do not simply restart and retry at the same parameters: the drive will trip again and thermal cycling degrades drive electronics. Identify the safe parameter set first, then restart.

### Pre-Cut Verification Checklist

Work through each item in order. Any "FAIL" result requires correction before the spindle starts.

| Step | Verification Action | Pass Criterion | Status |
|---|---|---|---|
| 1 | Spindle tram check with DTI | TIR ≤ 0.010 mm / 200 mm diameter | PASS / FAIL |
| 2 | Vise jaw alignment | TIR ≤ 0.020 mm across jaw | PASS / FAIL |
| 3 | Work coordinate offset (edge find) | 3-repeat spread ≤ 0.005 mm | PASS / FAIL |
| 4 | Gauge block Z-reference verification | ±0.002 mm vs. nominal stack | PASS / FAIL |
| 5 | Collet TIR check | TIR ≤ 0.015 mm at tool tip | PASS / FAIL |
| 6 | Tool stick-out within deflection limit | L ≤ 60 mm for 0.025 mm tolerance | PASS / FAIL |
| 7 | Feeds-and-speeds power check | Pcut ≤ 1,200 W | PASS / FAIL |
| 8 | Workholding safety factor | SF ≥ 3.0 | PASS / FAIL |
| 9 | Table locks engaged (non-cutting axes) | Physical check | PASS / FAIL |
| 10 | Chip thinning correction applied if ae < D/2 | Vf adjusted per CTF formula | PASS / FAIL |

This checklist is not bureaucratic overhead. Each item corresponds to a failure mode characterized in one of the three exercises: items 1–3 address measurement validity, items 4–5 address tool setup accuracy, items 6–8 address structural and power limits, and items 9–10 address dynamic stability. A machinist who runs this checklist before every new setup will, over time, internalize the physics behind each step until the checklist becomes an automatic mental model rather than a written procedure. That internalization is the difference between a machinist who makes good parts and one who understands why the parts are good.
