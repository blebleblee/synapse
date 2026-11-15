# Operational Verification Labs: Lighting
### Domain: Crafts | Discipline: Lego Technic & System Building

---

## Objective & Operational Lab Setup

Lighting in Lego builds occupies a narrow but demanding technical niche. Done poorly, it looks like an afterthought: wires snake across stud fields, LEDs sit proud of surfaces and ruin silhouettes, and power systems brown out under modest loads. Done with precision, it transforms a static model into something that reads as engineered rather than assembled. These labs treat Lego lighting as a legitimate electrical and mechanical integration problem, drawing on the same reasoning a product engineer would apply to any embedded illumination system: power budgeting, thermal behavior, optical placement, and structural concealment.

The three exercises that follow progress from baseline implementation to analytical stress testing. Each lab builds on the last, so work through them sequentially. You will need a measured, documented approach rather than intuitive assembly; keep a lab notebook or spreadsheet open throughout, because the empirical data you record in Exercise 1 becomes the baseline you attack in Exercises 2 and 3.

### Equipment & Materials Checklist

Before beginning Lab 1, gather the following. These are the authentic tools and components native to Lego lighting work, supplemented by the low-cost electrical instruments every serious Lego builder should own.

**Lego Electrical Components:**
- LEGO Power Functions (PF) AA Battery Box (88000) — 6V nominal output
- LEGO Powered Up Hub (88009) — 7.5V nominal, Bluetooth-controllable
- LEGO Light element (54930c01 / the standard 1×1 round plate with integrated LED, available in white, yellow, red, blue)
- LEGO Power Functions LED Lights set (8870) — provides two white LED units on a single PF cable
- Third-party Lego-compatible LED kits: Briksmax or LightMyBricks strip sets, which provide 1×1 tile-profile LEDs, 1×2 and 1×4 light bars, and USB-to-PF adapter cables

**Measurement & Analysis Instruments:**
- Digital multimeter (DMM) with DC voltage and DC milliamp current measurement, 0.1 mA resolution or better (Fluke 101, Klein MM300, or equivalent)
- USB power meter / inline logger (e.g., WITRN A2L or UM25C) — measures voltage, current, and cumulative mAh for USB-powered setups
- Lux meter or smartphone lux app (Luxmeter by dogbite, iOS/Android) — calibrated against a known light source before use
- 30 cm metal ruler, calipers
- Lab notebook or Google Sheets spreadsheet — mandatory, not optional

**Structural & Integration Supplies:**
- BrickTube or LEGO Technic flexible axle (Technic ref. 32199) for wire routing through stud channels
- LEGO 1×1 round plate with hole (85861) for wire pass-throughs
- Black electrical tape, 19 mm width
- Blu-Tack or low-tack mounting putty for temporary LED positioning
- Transparent 1×1 round tiles (6116903) and translucent slope bricks for diffusion testing

**Analytical Environment:**
Create a dedicated Google Sheets workbook titled **Lego Lighting Lab Log** with five sheets: *Inventory*, *Baseline Measurements*, *Variation Matrix*, *Stress Test Log*, and *Diagnostic Checklist*. The structure of each sheet is defined within the relevant exercise below.

---

## Exercise 1: Foundational Practical Implementation

### 1.1 The Circuit Architecture of a Lego Lighting System

A LEGO Power Functions battery box delivers a nominal 6 V from four AA alkaline cells in series. Fresh alkaline cells measure approximately 1.6 V each at rest, putting the unloaded bus at around 6.4 V. Under a typical multi-LED load of 80–120 mA, internal resistance drops this to roughly 5.8–6.1 V. The Powered Up hub runs from a USB-C source at 7.5 V and is regulated, meaning its output remains stable across a wider load range. Understanding which bus your build uses is not academic pedantry; it determines the current-limiting resistor value required by any raw LED you wire in, and it determines how many parallel LED chains you can run before the battery's discharge curve becomes a problem during a display session.

LEGO's first-party LED elements (the 8870 set and the integrated 1×1 round plate LEDs) have resistors embedded in their cable assemblies, so they are self-limiting on the PF bus. Third-party LED kits from Briksmax and LightMyBricks similarly pre-calculate their current limiting for 5 V USB input. Never mix a USB-spec LED kit directly onto a PF battery box without first measuring the actual forward voltage of your chain.

### 1.2 Build Specification: The Verification Model

For this exercise you will construct a standardized test panel: a 16×16 stud baseplate with a raised 2×6 stud building footprint representing a simplified building facade. This model is intentionally simple so it functions as a controlled, repeatable measurement artifact, not an aesthetic showpiece.

Assemble the facade to exactly 8 bricks in height using standard 2×4 and 2×2 bricks in a running bond pattern. Leave three window apertures: one 2×3 stud opening at height courses 2–4, one 2×3 opening at courses 4–6, and one open roof section at course 8. These openings become your LED placement zones.

Install one Briksmax 1×1 tile-profile LED in each of the three window apertures. Connect all three to a single USB distribution board from the Briksmax hub system (5 V USB input, with four output ports). Do not power the system yet.

### 1.3 Pre-Power Electrical Audit

Before applying power, perform the following checks in sequence. This is the electrical equivalent of tramming a vise before cutting: catching problems now costs nothing; catching them after a wiring fault blows an LED costs time, money, and potentially damages the hub.

Using your multimeter in resistance mode (Ω), probe across each LED's + and − terminals from the connector end. A healthy white or blue LED should read open circuit (OL) in both polarities, then drop to a low resistance (typically 10–50 Ω) in the forward-bias direction when probed with the red lead on anode, black on cathode. If you read a dead short (< 2 Ω in both directions), that LED's current-limiting resistor has been bridged by a solder defect during manufacturing — remove it from the circuit before proceeding. Record each LED's forward-bias resistance reading in the *Baseline Measurements* sheet, columns: LED ID, Forward Resistance (Ω), Reverse Resistance (Ω), Pass/Fail.

### 1.4 Powering Up and Taking Baseline Measurements

Connect the USB distribution board to your USB power meter (the WITRN A2L or equivalent), and plug the power meter into a USB wall adapter rated at 5 V / 1 A. This inline meter now captures total system current draw in real time.

Power on the system and allow it to stabilize for 90 seconds — LED current draw drifts slightly as junction temperature rises from ambient. After stabilization, record the following in the *Baseline Measurements* sheet:

| Measurement | Instrument | Expected Range | Record Value |
|---|---|---|---|
| Bus voltage at hub output | DMM DC volts | 4.9–5.1 V | ___ V |
| Total system current draw | USB power meter | 30–90 mA | ___ mA |
| Per-LED current (LED 1) | DMM in series, mA mode | 10–25 mA | ___ mA |
| Per-LED current (LED 2) | DMM in series, mA mode | 10–25 mA | ___ mA |
| Per-LED current (LED 3) | DMM in series, mA mode | 10–25 mA | ___ mA |
| Illuminance at 10 cm (LED 1) | Lux meter, sensor face-on | 50–400 lux | ___ lux |
| Illuminance at 10 cm (LED 2) | Lux meter | 50–400 lux | ___ lux |
| Illuminance at 10 cm (LED 3) | Lux meter | 50–400 lux | ___ lux |

To measure per-LED current, disconnect LED 1's output cable from the hub port, insert your multimeter probes into the break (red to the cable's positive conductor, black to the LED side), and reconnect. This series insertion method gives you the actual forward current of that individual branch without disturbing the others. Note that most Briksmax cables use 28 AWG conductors — handle them with care and do not stress the insulation at the connector joint.

### 1.5 Wire Concealment: Structural Integration Protocol

Visible wiring is the single most common aesthetic failure in amateur Lego lighting builds. The concealment strategy used here treats wire routing as a first-class structural decision made during the build, not retrofitted at the end.

The core principle exploits the 1.6 mm gap between stud rows when bricks are laid in standard running bond. A 28 AWG wire (0.36 mm conductor diameter, typical jacket OD 0.9–1.0 mm) passes through this gap with approximately 0.6 mm of clearance on each side. Route each LED's cable vertically through the interior hollow of the brick column before the column is closed off with plates on the front face. At the base course, bring all three cables through 1×1 round plate holes (part 85861) and channel them underneath the baseplate, secured with Blu-Tack every 4 studs to prevent the cable from pulling the LED out of position when the model is handled.

For the roof section LED, route the cable through a Technic 1×1 brick with axle hole (87073) oriented horizontally in the wall, threading the cable through the 5.1 mm axle channel. This is a clean, reversible feedthrough that leaves no visible cable on the exterior face.

After concealment, re-verify all three illuminance readings against the baseline — a cable pinched during routing will reduce forward current and therefore lux output. A drop of more than 15% from baseline on any single LED indicates a compromised cable.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### 2.1 The Variable Matrix: What You Are Measuring and Why

This exercise moves from single-point verification to structured empirical analysis. You will systematically vary three parameters — supply voltage, LED quantity per branch, and diffusion material — while measuring their effect on illuminance output and system current draw. The goal is to build an intuitive, data-backed map of how each parameter behaves in practice, so that when you design a future display build, you can predict its power requirements and optical output before committing brick to brick.

Set up the *Variation Matrix* sheet in your spreadsheet with the following column headers: Condition ID, Supply Voltage (V), LEDs in Branch, Diffusion Material, Bus Current (mA), LED Branch Current (mA), Lux at 10 cm, Lux at 30 cm, Notes.

### 2.2 Voltage Variation: PF Battery Box vs. Powered Up Hub vs. USB

Replace the USB source with the LEGO Power Functions AA Battery Box. The PF bus is 6 V nominal, which exceeds the 5 V design spec of the Briksmax LEDs. Briksmax specifies a maximum input of 5.5 V; running their LEDs at 6 V is outside specification and will shorten LED lifespan, though the internal resistor will prevent immediate failure. For this controlled test, limit the high-voltage condition to 60 seconds and record your data promptly.

Wire the Briksmax hub's USB input through a USB step-down module (Pololu D36V6F5 or equivalent 5V buck converter rated 500 mA) to give you a clean voltage source you can adjust. Set it first to 4.5 V, then 5.0 V, then 5.5 V in succession, allowing 60 seconds stabilization at each. Record bus current and lux output at each voltage. What you will observe is that lux output is not linearly proportional to voltage; because the LED's series resistor drops a fixed voltage, a 10% increase in supply voltage produces a disproportionately larger increase in forward current. Specifically, if your LED's forward voltage ($V_f$) is 3.2 V and its series resistor is 100 Ω:

At 5.0 V: $I = (5.0 - 3.2) / 100 = 18$ mA  
At 5.5 V: $I = (5.5 - 3.2) / 100 = 23$ mA  
At 4.5 V: $I = (4.5 - 3.2) / 100 = 13$ mA

This is a 25% voltage increase from 4.5 V to 5.5 V producing a 77% current increase — the kind of non-linear amplification that explains why slightly discharged batteries cause dramatic brightness drops. Record the actual values your hardware produces; they will differ from these calculated values due to component tolerances, but the trend will be consistent.

### 2.3 Branch Loading: Series vs. Parallel LED Configuration

Using individual LED modules with exposed lead wires (available from LightMyBricks' bare LED accessory packs), wire two LEDs in series on a single hub port and repeat the illuminance measurements. Then rewire the same two LEDs in parallel. Series wiring halves the current through each LED (both LEDs share the voltage drop across the resistor), producing lower per-LED brightness but extending battery life. Parallel wiring doubles the branch current draw while each LED operates at full rated forward current.

For the series condition, recalculate expected forward current manually before applying power: if the branch resistor is 100 Ω and each LED has $V_f = 3.2$ V on a 5 V bus, the two LEDs in series would need $6.4$ V just to reach threshold — which exceeds the supply voltage. This calculation tells you that two white LEDs in series cannot operate on a 5 V USB bus. Record this as a failed condition in your matrix, noting the reason. This is a valuable negative result: it teaches the fundamental constraint governing series LED chains and prevents wiring mistakes in future builds.

For the parallel condition, record bus current carefully. Two LEDs at 18 mA each draws 36 mA from that hub port. Briksmax hubs typically provide 100 mA maximum per port. Understand your margin.

### 2.4 Diffusion Material Analysis: Optical Benchmarking

Diffusion materials soften the point-source harshness of bare LEDs. In Lego builds, the practical options are: no diffusion (bare LED), a transparent 1×1 round tile placed directly over the LED, a translucent 1×2 brick (available in trans-clear, trans-yellow, trans-red), and a folded single layer of white tissue paper inserted as a 0.1 mm shim between the LED and a tile face.

For each diffusion condition, position the lux meter sensor at exactly 10 cm and 30 cm from the LED face, perpendicular to the emission axis, using your ruler to maintain positional consistency. Record four lux readings at each distance, discard the highest and lowest, and average the remaining two (this is a simplified 2-of-4 trimmed mean, sufficient for this measurement precision).

| Diffusion Condition | Lux at 10 cm (avg) | Lux at 30 cm (avg) | Perceived Hotspot |
|---|---|---|---|
| Bare LED, no cover | ___ | ___ | Harsh, visible die |
| Trans-clear 1×1 tile | ___ | ___ | Slight softening |
| Trans-yellow 1×2 brick | ___ | ___ | Warm diffusion, −15 to −25% lux |
| Tissue paper shim | ___ | ___ | Maximum diffusion, −30 to −40% lux |
| Translucent slope 1×2 (45°) | ___ | ___ | Directional spread |

You will find that the tissue paper shim provides the most even distribution but reduces peak lux by roughly 35%, which is acceptable in interior-lit building facades where you want ambient glow rather than beam projection. The trans-yellow brick warms the color temperature significantly — measuring with your phone's camera white balance on automatic will reveal this shift clearly even if your lux meter only measures intensity.

### 2.5 Analytical Synthesis: Building the Power Budget Model

With your Variation Matrix now populated with real measurements, open a new tab in your spreadsheet titled *Power Budget Calculator* and build the following model, which you will reuse for every future Lego lighting build.

| Input Cell | Label | Your Value |
|---|---|---|
| B2 | Supply voltage (V) | 5.0 |
| B3 | LED forward voltage, Vf (V) | 3.2 |
| B4 | Series resistor (Ω) | 100 |
| B5 | Number of parallel LED branches | 3 |
| B6 | Battery capacity (mAh) | 2500 |

| Calculated Cell | Formula | Description |
|---|---|---|
| B8 | `=(B2-B3)/B4` | Per-branch current (A) |
| B9 | `=B8*1000` | Per-branch current (mA) |
| B10 | `=B9*B5` | Total system current (mA) |
| B11 | `=B6/B10` | Runtime (hours) |
| B12 | `=B10*B2/1000` | Total power draw (W) |

Enter your measured values from Exercise 1 into B3 and B8 (using your measured per-LED current rather than the calculated value), and observe how well the model predicts the total current you measured with the USB power meter. A discrepancy greater than 15% suggests your LED's internal resistor value differs from 100 Ω, and you should calculate the actual resistor value using the measured current and your known Vf.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### 3.1 Purpose and Philosophy of Failure-Mode Testing

A lighting system that only gets tested under ideal conditions is a system that will fail unexpectedly at a display event or during a photo session. This exercise deliberately drives the system to its failure boundaries, documents what goes wrong, and establishes recovery procedures. The practitioner who has seen their system fail under controlled conditions is far better prepared than one who has only seen nominal operation.

Open the *Stress Test Log* sheet and prepare columns: Test ID, Condition Imposed, Expected Failure Mode, Observed Symptom, Measured Delta (from baseline), Recovery Action, Post-Recovery Lux, Pass/Fail.

### 3.2 Thermal Stress: Extended Operation at Maximum Current

Configure all three LEDs on your verification panel simultaneously at maximum rated forward current (use the 5.5 V setting on your adjustable supply, confirmed to push each LED to 23 mA per your Exercise 2 measurements). Allow the system to run continuously for 45 minutes. At 5-minute intervals, measure and record total bus current and lux output for LED 1 (the accessible reference LED).

What you will observe: luminous flux from LED 1 will drop approximately 2–5% over 45 minutes as the LED junction temperature rises and the phosphor conversion efficiency decreases. This is called thermal droop and is a normal characteristic of white LEDs driven above their rated current. The recovery test is to power down for 10 minutes, allow the LED to return to ambient temperature, and re-measure lux. It should return to within 1–2% of the original cold baseline. If it does not recover fully, the LED has experienced some permanent phosphor degradation. Document the percentage of permanent lux loss in your Stress Test Log.

For enclosed builds — a MOC interior where the LED sits within a brick cavity with limited airflow — thermal droop is more severe because heat cannot dissipate. The practical engineering response is to derate the forward current by 20–30% in enclosed installations, which you can achieve by increasing the series resistance. For the Briksmax system, insert a 47 Ω resistor in series with the LED cable (crimp-connected, not soldered, to preserve reversibility) and measure the resulting current reduction and lux penalty. A 47 Ω addition to a 100 Ω existing series resistor reduces current by approximately 32% and lux by roughly 25–30%, which is a worthwhile trade for a build that will run continuously for hours.

### 3.3 Mechanical Stress: Cable Pull-Out and Reconnection Cycling

Lego builds are disassembled, transported, and rebuilt repeatedly. The micro-JST and proprietary connector systems used by Briksmax and LightMyBricks are rated for approximately 30–50 insertion cycles before contact resistance begins to increase. This test measures connector degradation empirically.

Perform 25 full disconnect-reconnect cycles on LED 1's hub port connector, reconnecting with the correct orientation each time. After every 5th cycle, record the per-LED forward current with your DMM. An increase in per-LED current indicates connector contact resistance has decreased (the spring contacts have burnished to lower resistance — this is normal and beneficial for a few cycles). A decrease in current after cycle 15–20 indicates the contact spring is fatiguing and resistance is rising. If you observe a current drop exceeding 2 mA from the baseline, the connector is degrading and should be replaced before the contact resistance causes intermittent flickering during display.

Document the cycle-by-cycle current in a small sub-table in the Stress Test Log:

| Cycle | LED 1 Current (mA) | Delta from Baseline |
|---|---|---|
| 0 (baseline) | ___ | 0.0 |
| 5 | ___ | ___ |
| 10 | ___ | ___ |
| 15 | ___ | ___ |
| 20 | ___ | ___ |
| 25 | ___ | ___ |

### 3.4 Voltage Collapse: Battery Discharge Simulation

This test simulates the behavior of an aging battery pack mid-display. Use a variable power supply set to 5.0 V baseline, then step it down in 0.25 V increments: 5.0, 4.75, 4.5, 4.25, 4.0, 3.75, 3.5 V. At each step, record bus current and lux for LED 1. Allow 60 seconds stabilization at each step.

Your data will reveal a lux cliff — a voltage threshold below which brightness drops precipitously. For most white LEDs with 3.2 V forward voltage, the cliff occurs around 3.8–4.0 V when the supply can no longer maintain sufficient overdrive above Vf. Below the cliff, the LED does not simply get dimmer proportionally; it enters subthreshold operation where efficiency collapses and color shifts toward deep blue-white as the phosphor is underdriven.

The recovery protocol for voltage collapse is not to increase the number of LEDs (which increases load and worsens the problem) but to reduce the number of parallel branches to the minimum necessary for the display. Document in the Stress Test Log: at what supply voltage does your build drop below 50% of its baseline lux output? That voltage is your minimum acceptable battery voltage, and it determines when batteries must be replaced.

### 3.5 Structural Integration Failure: Stud Crush on Concealed Wiring

This test verifies that your wire concealment strategy from Exercise 1 survives the mechanical forces of building and rebuilding the model. Remove and reinstall the front facade plates three times, each time applying normal building force (approximately 15–20 N thumbpress on each plate). After each removal-reinstall cycle, measure lux for all three LEDs against baseline.

A lux drop of more than 10% in any LED after reinstallation indicates that the cable routing channel is being pinched during plate installation, partially crushing the wire and increasing its resistance. The recovery is to reroute that cable 1–2 studs laterally to clear the pinch point, or to use a cable relief loop — 10–15 mm of extra cable coiled loosely inside the brick cavity — so the cable is not placed under tension during assembly.

---

## Operational Reference Guide & Diagnostic Checklist

### Quick-Reference Specification Table

The following table consolidates the nominal operating parameters for the most common Lego-compatible lighting components. Use this as the starting point for any new build's power budget calculation.

| Component | Supply Voltage | Forward Current | Forward Voltage (Vf) | Series Resistor (internal) | Max Parallel Branches (5V / 1A source) |
|---|---|---|---|---|---|
| LEGO 8870 PF LED (white) | 6–9 V PF bus | 20 mA | 3.2 V | ~140 Ω | N/A (PF only) |
| Briksmax 1×1 tile LED (white) | 5 V USB | 18–22 mA | 3.2 V | ~100 Ω | 40 |
| LightMyBricks 1×1 LED (warm white) | 5 V USB | 15–20 mA | 3.0 V | ~105 Ω | 45 |
| LightMyBricks LED strip (per 3-LED segment) | 5 V USB | 45–60 mA | — | Built-in | 15 |
| Powered Up Hub LED port | 7.5 V regulated | 20 mA max per port | — | External required | 4 ports |

### Wire Gauge and Current Capacity Reference

| Wire Gauge | Max Current (continuous) | Use Case in Lego |
|---|---|---|
| 28 AWG | 500 mA | Standard LED extension cables |
| 26 AWG | 1000 mA | Hub-to-battery trunk lines |
| 24 AWG | 2000 mA | Main bus runs in large display builds |

### Diagnostic Decision Tree

A practitioner encountering a lighting fault in a completed Lego build should work through this diagnostic sequence without disassembling more than necessary. The sequence is ordered from least disruptive to most disruptive.

**Symptom: One LED not illuminating, others normal.**
Disconnect the failed LED from the hub and test it in a known-good port. If it illuminates there, the hub port is damaged — remap to a spare port. If it does not illuminate in a known-good port, the LED or its cable has failed. Probe the LED's connector with the DMM in forward-bias resistance mode; a dead short across both terminals in both probe orientations confirms internal failure — replace the LED.

**Symptom: All LEDs dimmer than baseline, uniform reduction across branches.**
Measure bus voltage at the hub output. If more than 0.3 V below specification, the power source is degraded — replace batteries or verify the USB supply under load. If bus voltage is nominal, the hub's internal current-distribution circuitry may be overloaded; disconnect one branch and check if remaining LEDs recover. If they do, you have exceeded the hub's total current rating and must add a secondary hub on a separate USB port.

**Symptom: Intermittent flickering on specific LED, random intervals.**
This is almost always a connector contact issue. Clean the affected connector's contacts with a dry cotton swab to remove oxidation, then cycle the connection 3 times to burnish the contacts. If flickering persists, check for cable pinching by running the cable externally (temporarily bypassing the concealed route) — if flickering stops, the cable is being stressed in the concealed route and must be rerouted with a relief loop.

**Symptom: Visible color shift (bluer than other LEDs) on one unit.**
The LED is being underdriven. Measure its forward current; it will be below 10 mA. The series resistor on that branch's cable has likely been damaged and its resistance has increased (this can happen if the cable was kinked sharply). Replace the cable assembly.

**Symptom: LED luminously much brighter than others, slight warm tint.**
Overdriving condition: measure forward current; it will be above rated specification. The cable's series resistor may have partially failed short. Remove the LED immediately to prevent premature phosphor degradation, and replace the cable.

### Pre-Display Operational Checklist

Before a display event, Lego showcase, or photo session where the lighting system must perform reliably, complete the following checklist. Each item maps to a specific failure mode characterized in this lab.

1. Measure bus voltage at the hub output under full load. Must be within ±0.3 V of specification. Fresh batteries only for display sessions lasting more than 2 hours.
2. Verify total system current draw against the Power Budget Calculator baseline. A reading more than 15% above predicted total indicates a wiring short or unanticipated load. A reading more than 15% below predicted indicates an open circuit (failed LED or broken cable) that may not be visually obvious at first glance.
3. Run the system at full load for 10 minutes prior to opening to the public, and confirm no LED undergoes visible thermal droop beyond 5% lux reduction. If thermal droop is detected, insert 47 Ω derating resistors on the worst-performing branches.
4. Inspect all cable exit points at the base of the model for pinching. Any cable that is under visible tension should be relieved with a free loop before display.
5. Confirm diffusion tiles and translucent brick elements are seated flush. A displaced diffuser produces a visible hotspot that reads as a defect under close inspection.
6. Photograph the illuminated model in a dimmed room before display. This is both a marketing asset and a documented baseline — if a fault develops during the display session, the photograph gives you a before-state to compare against when diagnosing which element failed.
