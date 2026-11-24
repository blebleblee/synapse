# Operational Verification Labs: Aerodynamics

## Objective & Telemetry Environment Setup

The aerodynamic performance envelope of a racing vehicle reveals itself not through wind tunnel correlation alone but through the systematic analysis of on-track telemetry data captured across varying ride heights, speeds, and corner loading conditions. This laboratory session transforms theoretical downforce coefficient curves and pressure distribution maps into actionable race engineering decisions by correlating logged vehicle dynamics channels with aerodynamic balance shifts observable through driver behavior, tire loading asymmetries, and suspension displacement histories.

The modern race engineer operates within a telemetry ecosystem centered on high-frequency data acquisition systems capable of sampling critical aerodynamic indicators at rates exceeding 100 Hz. MoTeC i2 Pro serves as the industry-standard analysis platform, providing synchronized multi-channel visualization, mathematical channel construction, and lap-comparative overlay capabilities essential for isolating aerodynamic phenomena from mechanical grip variables. The software ingests native MoTeC LD file formats as well as CSV exports from alternative acquisition systems such as AiM Race Studio, Bosch Motorsport DDU, and open-source RaceCapture/Pro devices.

Before commencing aerodynamic telemetry analysis, verify the integrity of your sensor calibration suite. Ride height sensors mounted at each corner must exhibit linear voltage response across their operational range, typically 0–100 mm of travel with ±0.5 mm resolution. These sensors—commonly linear potentiometers or contactless Hall-effect transducers—require zero-point calibration with the vehicle at static ride height on a level surface, fuel load documented, and driver seated. Suspension displacement channels feed directly into aerodynamic platform angle calculations, as rake angle (front ride height minus rear ride height) governs underbody Venturi tunnel throat areas and diffuser expansion angles with profound sensitivity.

Wheelspeed sensors provide the foundation for accurate ground speed computation, critical because aerodynamic forces scale with the square of velocity. Four-corner wheelspeed data enables slip ratio detection during braking phases, distinguishing mechanical grip losses from aerodynamic instability events. GPS-derived ground speed offers an independent validation channel, though latency and update rate limitations restrict its utility to steady-state speed trap analysis rather than transient corner entry diagnosis.

Steering angle and lateral acceleration channels combine to expose aerodynamic balance shifts through understeer gradient analysis. A neutrally balanced aerodynamic platform maintains consistent steering input requirements across speed ranges, whereas front downforce deficiency manifests as progressively increasing steering angle demands at higher speeds despite constant lateral g-loading. The inverse relationship—decreasing steering input at elevated speeds—signals rear downforce insufficiency and impending snap oversteer behavior.

Establish your telemetry workspace by installing MoTeC i2 Pro version 1.2 or later, ensuring Windows 10/11 compatibility and allocating at least 16 GB of system RAM for large multi-session datasets. Create a dedicated project directory structure organizing raw telemetry files by test session, track configuration, and atmospheric conditions. Atmospheric density variations alter downforce generation by up to 8% between sea-level summer testing and high-altitude autumn race weekends, necessitating barometric pressure and ambient temperature logging for meaningful session-to-session comparisons.

Configure your MoTeC workspace to display the essential aerodynamic diagnostic channel suite: ground speed (km/h), ride height front (mm), ride height rear (mm), lateral acceleration (g), longitudinal acceleration (g), steering angle (deg), throttle position (%), brake pressure (bar), and damper velocities at all four corners (mm/s). Construct calculated channels for rake angle (RH_Rear - RH_Front), pitch acceleration (derivative of pitch angle), and aerodynamic platform velocity (rate of change of average ride height). These derived channels isolate transient aerodynamic loading events from quasi-steady cornering forces.

The laboratory exercises that follow progress through three operational verification domains: telemetry data import and driver trace correlation establishes baseline aerodynamic behavior patterns across corner classifications; damper velocity histogram analysis exposes transient pitch and roll dynamics driven by downforce application and removal; tire temperature profiling reveals load distribution asymmetries caused by aerodynamic balance inconsistencies. Each exercise delivers concrete setup adjustments expressed in damper clicks, spring rate changes, and wing angle increments rather than abstract force coefficients.

## Exercise 1: Telemetry Data Import & Driver Trace Correlation

Begin by acquiring a representative telemetry dataset capturing a minimum of five consecutive flying laps at a circuit exhibiting diverse aerodynamic challenge regimes: high-speed straights exceeding 200 km/h where downforce generation peaks, medium-speed sweepers at 120–160 km/h exposing aerodynamic balance sensitivity, and slow technical sections below 100 km/h where mechanical grip dominates. The Silverstone Grand Prix Circuit exemplifies this diversity, offering the high-speed Copse/Maggotts/Becketts complex, medium-speed Village/Loop sequence, and low-speed Club chicane within a single 5.9 km lap.

Launch MoTeC i2 Pro and navigate to File → Open Workspace, selecting your project directory. Import the raw telemetry file through File → Add Files to Workspace, choosing the LD or CSV format corresponding to your acquisition hardware. MoTeC automatically parses channel definitions embedded within LD files; CSV imports require manual channel mapping through the Data Import Wizard, specifying column headers, units, and scaling factors. Verify channel import integrity by inspecting minimum/maximum values and identifying any flatlined channels indicating sensor failures or wiring faults.

Create a new worksheet dedicated to aerodynamic analysis by right-clicking the worksheet tab bar and selecting New Worksheet. Rename this worksheet "Aero Platform Dynamics" to distinguish it from mechanical grip and powertrain analysis views. Populate the worksheet with a vertical stack of time-series graph panels, each synchronized to a common time axis spanning a complete flying lap. The first panel displays ground speed overlaid with throttle position, providing immediate context for aerodynamic loading phases. Full throttle at high speed represents maximum downforce generation; corner entry braking phases expose front axle aerodynamic load transfer dynamics.

Add a second panel visualizing ride height channels at front and rear axles simultaneously, scaled identically (0–50 mm) to emphasize rake angle evolution throughout the lap. Observe ride height compression during high-speed straight-line running: aerodynamic downforce drives suspension displacement proportional to velocity squared, reducing ride heights by 10–20 mm between corner exit and braking point on fast circuits. This compression alters underbody Venturi tunnel geometry, potentially triggering flow separation if ride heights approach minimum clearance thresholds. Note any asymmetric front-to-rear compression ratios indicating aerodynamic balance shifts requiring wing angle adjustments.

The third panel presents lateral acceleration alongside steering angle, revealing the classic understeer/oversteer signatures embedded within driver inputs. At corner entry, compare steering angle application rate against lateral acceleration rise: a driver compensating for front downforce deficiency applies steering angle early and aggressively, yet lateral acceleration builds gradually as the front axle struggles to generate cornering force. Conversely, rear downforce deficiency manifests as sudden lateral acceleration spikes accompanied by corrective steering angle reversals—the driver catches snap oversteer events through rapid counter-steering.

Construct a calculated math channel quantifying the understeer gradient across varying speeds. In MoTeC's Math Channel editor, define a new channel named "Aero_Understeer_Index" using the expression:

```text
(SteeringAngle / LateralAccel) - ReferenceGradient
```

The reference gradient represents the baseline steering sensitivity measured during low-speed mechanical grip corners, typically 15–25 degrees of steering per lateral g. High-speed corner analysis revealing increased steering angle per g indicates aerodynamic understeer; decreased values signal rear-biased downforce and potential instability. Plot this channel over a complete lap, identifying speed thresholds where the understeer index transitions from neutral (±2 deg/g) to problematic (>5 deg/g variation).

Overlay multiple lap traces to assess aerodynamic consistency and driver adaptation strategies. Select your fastest representative lap as the baseline reference, then overlay the subsequent three laps using MoTeC's lap overlay function (Ctrl+Shift+O). Focus analysis on high-speed corner entry phases where aerodynamic effects dominate. Consistent ride height compression magnitudes across laps indicate stable aerodynamic platform behavior; lap-to-lap variations exceeding 3 mm suggest ride height sensitivity requiring damper or spring adjustments to control transient pitch dynamics.

Export a critical corner segment for detailed micro-analysis by defining a cursor window spanning two seconds before turn-in through corner apex. Right-click the time axis and select "Set Zoom to Cursor Window," isolating the transient aerodynamic loading phase. Within this zoomed view, add damper velocity channels for front-left and front-right corners, revealing how rapidly the aerodynamic platform responds to initial steering input. High damper compression velocities (>150 mm/s) during turn-in indicate insufficient front bump damping, allowing the front axle to dive excessively and potentially stall the front wing or underfloor flow structures.

Quantify the aerodynamic load transfer timeline by measuring the time delay between steering input initiation and maximum ride height compression. Place cursors at the steering angle inflection point (driver begins turn-in) and the minimum front ride height sample within the corner entry phase. Typical aerodynamic load transfer occurs within 0.2–0.4 seconds, constrained by suspension bump velocity and damper flow restrictions. Delays exceeding 0.5 seconds indicate overly soft front springs or inadequate bump damping, allowing prolonged pitch transients that destabilize the aerodynamic platform.

Create a data report documenting baseline aerodynamic performance metrics for subsequent comparison following setup changes. MoTeC's Report Generator (Tools → Report Generator) enables automated extraction of minimum/maximum channel values, statistical distributions, and lap-to-lap consistency metrics. Configure a report template capturing the following aerodynamic key performance indicators per lap: minimum front ride height at maximum speed, maximum rake angle achieved, peak lateral acceleration in high-speed corners, and understeer index average across corners exceeding 150 km/h.

Validate your telemetry analysis against driver qualitative feedback by conducting a post-session debrief structured around specific corner classifications. Present ride height and damper velocity traces from high-speed corners where the driver reported aerodynamic balance concerns, confirming whether telemetry data supports subjective assessments. Drivers often perceive front-end instability as "sudden understeer at turn-in," which telemetry reveals as rapid front ride height collapse exceeding 8 mm within 0.3 seconds, stalling front wing elements and shedding downforce precisely when the driver demands maximum front axle grip.

Document all findings within a session engineering log, noting atmospheric conditions (ambient temperature 22°C, barometric pressure 1013 mbar, track temperature 34°C), baseline setup parameters (front wing angle +3.5°, rear wing mainplane +8°, gurney flap 20 mm), and observed aerodynamic behavior anomalies. This log establishes the foundation for Exercise 2's damper optimization work, where suspension velocity control addresses transient aerodynamic platform instabilities exposed through telemetry correlation analysis.

## Exercise 2: Damper Velocity Histogram Tuning & Anti-Roll Bar Optimization

Aerodynamic downforce does not manifest as a steady-state vertical load but rather as a dynamic forcing function modulated by ride height variations, pitch angle oscillations, and transient corner entry events. The suspension damper system functions as the primary control mechanism regulating how rapidly the chassis responds to aerodynamic load changes, directly influencing underbody flow stability and wing angle-of-attack consistency. This exercise applies damper velocity histogram analysis to quantify suspension dynamic behavior, then optimizes bump and rebound damping forces to maintain aerodynamic platform stability across the operational ride height envelope.

Return to your MoTeC i2 Pro workspace and load the telemetry dataset analyzed in Exercise 1. Create a new worksheet titled "Damper Dynamics – Aero Correlation" and configure a four-panel vertical layout displaying damper velocity channels for each corner: front-left, front-right, rear-left, rear-right. Scale all velocity axes identically from -200 to +200 mm/s, enabling direct cross-corner comparison of compression (positive velocity) and extension (negative velocity) event magnitudes. Overlay ground speed and throttle position in the top panel to contextualize damper activity within the lap's aerodynamic loading phases.

Examine front damper velocity traces during high-speed straight-line running where aerodynamic downforce peaks. As the vehicle accelerates from 150 km/h through 250 km/h, downforce increases quadratically, compressing the suspension progressively. Observe the damper velocity signature: sustained low-magnitude compression velocities (20–40 mm/s) represent the gradual ride height reduction driven by increasing aerodynamic load. Modern aerodynamic platforms generate 2000–3000 N of downforce at 250 km/h on GT3-specification vehicles, displacing suspension ride height by 15–25 mm depending on spring stiffness and damper blow-off thresholds.

Isolate a high-speed corner entry event where maximum aerodynamic downforce suddenly transitions to reduced loading as the driver lifts throttle and applies brakes. The telemetry trace reveals a violent front damper extension event (large negative velocity spike, often exceeding -150 mm/s) as the front axle rebounds from its compressed, high-downforce state. This extension velocity magnitude directly determines how rapidly the front ride height increases, which in turn modulates front wing angle-of-attack and underbody throat area. Insufficient rebound damping permits excessively rapid ride height rise, effectively reducing front downforce during corner entry when the driver demands maximum front axle grip.

Generate damper velocity histograms to quantify the statistical distribution of suspension velocities across an entire lap. MoTeC provides histogram generation through the Math Channels menu: create a new histogram channel named "FL_Damper_Histogram" configured with 10 mm/s bin width spanning -200 to +200 mm/s. Apply this histogram to the front-left damper velocity channel over a representative lap window. The resulting distribution exposes the frequency and magnitude of compression versus extension events, revealing whether the damper spends excessive time operating in low-velocity regimes (insufficient damping control) or high-velocity regimes (excessive harshness).

An optimally damped aerodynamic platform exhibits a histogram distribution centered near zero velocity with symmetric tails extending to ±100 mm/s. The histogram should display a narrow central peak representing quasi-steady-state ride height adjustments during straight-line running, flanked by moderate-frequency bins at ±50–80 mm/s corresponding to corner entry/exit transients. Histograms exhibiting heavy concentration in high-velocity bins (>120 mm/s) indicate underdamped behavior allowing rapid pitch oscillations that destabilize airflow attachment; conversely, histograms confined entirely to low-velocity bins suggest overdamped suspension sacrificing mechanical grip compliance.

Compare front and rear damper velocity histograms to diagnose aerodynamic balance issues rooted in suspension dynamics. A front-biased velocity distribution (front dampers exhibiting higher average velocities than rear) indicates excessive front axle pitch sensitivity, often caused by soft front springs combined with inadequate front bump damping. This configuration permits the front axle to rapidly compress under high-speed downforce application, then rebound violently during corner entry braking, creating a dynamic pitch oscillation that modulates front downforce by 10–15% at frequencies uncomfortable for the driver to anticipate and correct.

Adjust front bump damping to control aerodynamic platform compression rates during downforce application. Modern racing dampers provide independent bump and rebound adjustment through external rotary knobs or shims in valve stacks, typically offering 12–16 clicks of adjustment range. From your baseline setup (assume front bump damping set to 6 clicks from full soft), increase front bump damping by 3 clicks and repeat the telemetry capture session over an identical five-lap run. Import the new telemetry file into MoTeC and overlay the revised damper velocity traces against the baseline configuration.

Quantify the damping adjustment effect by comparing maximum front damper compression velocities during high-speed aerodynamic loading phases. The baseline configuration exhibited peak compression velocities of 95 mm/s during acceleration from 180–230 km/h; the revised setup with increased bump damping should reduce peak velocities to 65–75 mm/s. This velocity reduction translates directly to reduced ride height collapse rates, maintaining more consistent underbody Venturi tunnel geometry and preventing flow separation events triggered by excessive ride height compression.

Inspect the updated damper velocity histogram and verify the distribution has shifted toward lower compression velocities without significantly increasing extension velocities. If extension velocity magnitudes increased (indicating the damper now resists rebound more than intended), the damper adjustment introduced undesirable cross-coupling between bump and rebound circuits—a common issue with single-adjustment dampers lacking independent bump/rebound control. High-end motorsport dampers (Öhlins TTX, Penske 8300 series) provide four-way adjustment separating low-speed and high-speed bump/rebound circuits, enabling precise aerodynamic platform control without mechanical grip compromises.

Address lateral aerodynamic balance through anti-roll bar stiffness optimization. Anti-roll bars couple left-right suspension displacements, influencing how aerodynamic downforce distributes across the front and rear axles during cornering. Excessive front anti-roll bar stiffness increases front roll resistance, effectively increasing front ride height on the outside wheel during cornering, which can stall front wing endplates or reduce front underbody effective area. Conversely, insufficient rear anti-roll bar stiffness permits excessive rear roll angles that alter rear wing angle-of-attack relative to the vehicle's pitch plane.

Create a calculated channel quantifying roll angle from left-right ride height differentials. Define a new math channel "Front_Roll_Angle" using the expression:

```text
atan((RideHeight_FR - RideHeight_FL) / FrontTrackWidth) * (180 / PI)
```

Assume a front track width of 1.6 meters for GT3 vehicles. Plot this roll angle channel alongside lateral acceleration through a medium-speed corner (120–140 km/h, generating 1.8–2.2 lateral g). Measure the roll angle magnitude at peak lateral acceleration: optimal aerodynamic platform control maintains front roll angles below 2.5 degrees to preserve front wing endplate ground clearance and prevent excessive ride height asymmetry that disrupts underbody flow uniformity.

If front roll angles exceed 3 degrees at peak cornering loads, increase front anti-roll bar stiffness by rotating the blade adjuster one position stiffer (typically 2–3 mm blade length reduction). Anti-roll bar stiffness scales with blade thickness cubed and length inversely, so small geometric changes produce substantial roll resistance increases. Document the baseline anti-roll bar configuration (e.g., "Front ARB blade position 3 of 5, blade thickness 25 mm") before making adjustments to enable reversal if handling balance degrades.

Capture post-adjustment telemetry and overlay front roll angle traces against the baseline configuration. The increased anti-roll bar stiffness should reduce peak roll angles by 0.5–0.8 degrees while maintaining similar lateral acceleration magnitudes, confirming the adjustment successfully limited aerodynamic platform attitude changes without sacrificing mechanical grip. Simultaneously inspect tire temperature data (Exercise 3) to verify the anti-roll bar change did not introduce excessive load transfer that overheats the outside front tire.

Validate damper and anti-roll bar optimizations through driver feedback correlation. Present the driver with telemetry overlays comparing baseline and revised configurations, focusing on high-speed corner entry phases where aerodynamic balance sensitivity peaks. Drivers typically perceive improved damper control as "more consistent front-end response" and "reduced pitch sensitivity under braking," while optimized anti-roll bar balance manifests as "better mid-corner stability" and "reduced sudden understeer at apex." Quantitative telemetry confirmation of these subjective improvements—reduced damper velocity peaks, decreased roll angles, more consistent ride heights—validates the setup changes and establishes confidence for further refinement.

Document all damper and anti-roll bar adjustments in the session engineering log, recording exact click positions, blade settings, and observed telemetry effects. This log becomes the foundation for developing vehicle-specific setup matrices that encode aerodynamic platform optimization strategies across varying track characteristics and atmospheric conditions.

## Exercise 3: Tire Temperature Analysis & Wear Modeling

Aerodynamic downforce directly modulates tire contact patch loading, influencing tire temperature distributions, wear rates, and the fundamental grip generation mechanisms that determine corner entry speeds and lap time consistency. This exercise correlates tire surface temperature profiles with aerodynamic balance characteristics, revealing whether downforce distribution aligns with mechanical setup or introduces load transfer asymmetries that compromise tire operating windows. The integration of telemetry-derived temperature data with visual tire wear observations provides comprehensive diagnostic capability for optimizing aerodynamic balance through wing angle adjustments and ride height targeting.

Tire temperature measurement in professional motorsport employs infrared pyrometers capturing surface temperatures at three lateral positions across the tread: inside edge, center, and outside edge. Handheld pyrometers (Longacre, Intercomp) provide post-session measurements captured immediately upon pit entry before heat dissipates; advanced systems integrate wireless infrared sensors transmitting continuous temperature telemetry to the data acquisition system during on-track sessions. For this exercise, assume post-session pyrometer data captured at three front tire positions and three rear positions, recorded within 30 seconds of pit entry following a five-lap high-intensity run.

Begin by constructing a tire temperature data table organizing measurements by axle, lateral position, and session timing. Create a spreadsheet or MoTeC report template with columns: Tire_Position (FL_Inside, FL_Center, FL_Outside, FR_Inside, etc.), Temperature_Celsius, Lap_Count, and Session_Timestamp. Populate this table with baseline configuration data captured during Exercise 1 sessions before damper or anti-roll bar adjustments. Typical high-performance tire operating temperatures range from 85–105°C for slick racing tires; temperatures below 75°C indicate insufficient energy input (underloaded tire or inadequate driving aggression), while temperatures exceeding 110°C signal overloading and imminent thermal degradation.

Analyze front tire temperature distributions to diagnose aerodynamic front axle loading characteristics. Compare inside edge versus outside edge temperatures for the front-left tire following a clockwise-direction circuit (predominantly right-hand corners loading the left-side tires). Optimal tire temperature distribution exhibits outside edge temperatures 5–10°C higher than inside edges, reflecting the combined effects of camber angle (negative camber unloads inside edge) and lateral load transfer during cornering. Temperature differentials exceeding 15°C indicate excessive load transfer potentially caused by insufficient front downforce allowing mechanical roll to dominate, or excessive front anti-roll bar stiffness.

Examine the center tread temperature relative to edge temperatures to assess tire contact patch pressure distribution. Center temperatures exceeding edge temperatures by more than 8°C indicate over-inflation or excessive vertical loading concentrated in the tire's central contact patch region. In the context of aerodynamic analysis, center-biased temperature profiles at the front axle suggest high front downforce levels compressing the tire vertically and concentrating contact pressure centrally. While this confirms effective downforce generation, it may indicate opportunity to reduce front wing angle if the resulting understeer balance proves undesirable.

Correlate tire temperature asymmetries with telemetry-derived ride height and roll angle data from Exercise 2. Load your MoTeC workspace and display front roll angle alongside front-left and front-right damper velocities during a representative medium-speed corner. If the front-left outside edge temperature exceeded the front-right outside edge by more than 10°C (unexpected on a right-hand dominant circuit), inspect telemetry for asymmetric suspension behavior: unequal damper velocities or asymmetric roll angles indicate mechanical setup issues rather than aerodynamic balance concerns. Symmetric tire temperatures across left-right pairs confirm aerodynamic balance adjustments as the appropriate optimization path.

Quantify rear tire temperature distributions to validate rear downforce levels and aerodynamic balance relative to the front axle. Rear tire temperatures should exhibit similar inside-outside differentials as the front (5–10°C outside bias) but with absolute temperature levels 3–7°C lower than fronts, reflecting the typical front-biased cornering load distribution on most circuit racing vehicles. Rear tire temperatures approaching or exceeding front tire temperatures indicate rear-biased aerodynamic downforce potentially causing oversteer tendencies, or insufficient front downforce leaving the front axle underloaded.

Construct an aerodynamic balance inference from tire temperature ratios. Calculate the average front tire temperature (averaging all six front tire measurement points) and average rear tire temperature. Define an empirical "Tire Temp Balance Index" as:

```text
Tire_Temp_Balance = (AvgFrontTemp - AvgRearTemp) / AvgFrontTemp
```

Values between 0.05–0.10 (front tires 5–10% hotter than rears) indicate balanced aerodynamic downforce distribution. Values exceeding 0.15 suggest front-biased loading requiring rear wing angle increases or front wing angle reductions; values below 0.03 indicate rear-biased loading demanding inverse adjustments. This empirical index provides rapid setup direction during test sessions when instrumented aerodynamic force measurement is unavailable.

Integrate tire wear observations with temperature analysis to distinguish aerodynamic loading effects from mechanical grip phenomena. Conduct post-session tire inspections measuring tread depth at inside, center, and outside positions using a tire tread depth gauge (resolution 0.1 mm). Excessive outside edge wear correlating with high outside edge temperatures confirms mechanical load transfer dominance; conversely, uniform tread wear across the tire width despite significant temperature gradients suggests aerodynamic downforce is compressing the tire vertically without inducing lateral load transfer—an ideal scenario maximizing grip generation.

Model tire wear rates as a function of aerodynamic downforce levels to predict tire life over race distances. Assume a baseline tire degradation rate measured during Exercise 1 sessions: front tire tread depth decreased 0.8 mm over 15 laps (approximately 75 km) under baseline downforce configuration. If subsequent sessions with increased front wing angle (+1.5° mainplane adjustment) exhibit front tire degradation of 1.1 mm over the same distance, the increased downforce induced a 37% acceleration in wear rate. Multiply this wear rate by expected race distance to forecast tire life: a 120-lap race would consume approximately 8.8 mm of tread depth, approaching the 10 mm safety limit and potentially requiring an additional pit stop.

Adjust aerodynamic balance to optimize tire temperature distributions and extend tire life without sacrificing lap time. Based on Exercise 1–3 integrated analysis, assume telemetry revealed front-biased aerodynamic balance (high front roll resistance, rapid front damper compression, front tire temperatures 12% higher than rears). Reduce front wing mainplane angle by 1.0 degree while simultaneously increasing rear wing angle by 0.5 degrees, targeting a more neutral tire temperature distribution. This adjustment reduces front downforce by approximately 8% while increasing rear downforce by 5%, shifting aerodynamic balance rearward.

Capture validation telemetry over a five-lap run with the revised aerodynamic configuration and repeat tire temperature measurements post-session. Compare the new tire temperature data against baseline values: target a reduction in average front tire temperatures of 4–6°C and an increase in average rear tire temperatures of 2–3°C, narrowing the front-rear differential from 12% to 6%. Overlay telemetry traces showing steering angle and lateral acceleration through high-speed corners, confirming the aerodynamic balance shift did not introduce unacceptable understeer (increasing steering angle per lateral g) or nervous rear-end behavior (sudden lateral acceleration spikes requiring corrective steering).

Construct a comprehensive aerodynamic balance optimization matrix documenting the relationships between wing angles, ride heights, tire temperatures, and subjective handling balance. This matrix takes the form of a multi-dimensional lookup table:

| Front Wing (deg) | Rear Wing (deg) | Avg Front Temp (°C) | Avg Rear Temp (°C) | Temp Balance Index | Understeer Index (deg/g) | Driver Feedback |
|------------------|-----------------|---------------------|--------------------|--------------------|--------------------------|-----------------|
| +3.5 | +8.0 | 98.2 | 87.5 | 0.109 | +4.2 | Front limited, stable rear |
| +2.5 | +8.5 | 93.8 | 89.7 | 0.044 | +1.8 | Neutral, consistent |
| +2.5 | +9.0 | 93.5 | 91.2 | 0.025 | -0.5 | Slight oversteer, responsive |

Each row represents a tested configuration with quantified outcomes across telemetry metrics (understeer index from Exercise 1), tire thermal data (temperature balance index), and qualitative driver assessments. This matrix enables data-driven aerodynamic setup decisions during race weekends when track evolution, temperature variations, or tire compound changes demand rapid balance adjustments.

Extend tire temperature analysis to transient thermal modeling by correlating tire temperature rise rates with aerodynamic loading phases throughout a lap. Advanced analysis exports tire temperature telemetry (if wireless sensors are available) synchronized with ride height and damper velocity channels, revealing that tire temperatures increase most rapidly during high-speed straight-line phases where maximum downforce compresses the tire and generates contact patch hysteresis heating. This insight informs tire warm-up strategies: drivers should prioritize high-speed aerodynamic loading zones during out-laps to rapidly elevate tire temperatures into the optimal operating window, rather than aggressive low-speed mechanical grip exploitation that generates less efficient frictional heating.

## Race Engineering Diagnostic Cheat Sheet & Setup Matrix

The operational verification exercises completed above establish a systematic telemetry-driven methodology for aerodynamic balance optimization. This final section consolidates key diagnostic indicators, setup adjustment protocols, and decision trees into a rapid-reference format suitable for trackside engineering use during compressed practice sessions and qualifying runs where analytical depth must yield to decisiveness.

### Aerodynamic Balance Diagnostic Flowchart

**High-Speed Understeer Symptoms:**
- Telemetry: Increasing steering angle per lateral g as speed rises above 180 km/h
- Tire Temp: Front outside edges 8–12°C hotter than inside, rear temps uniform
- Ride Height: Front ride height collapse >20 mm at peak speed
- **Action:** Increase front wing mainplane angle +1.0°, or reduce rear wing -0.5° if front already at maximum

**High-Speed Oversteer Symptoms:**
- Telemetry: Sudden lateral acceleration spikes requiring corrective steering above 160 km/h
- Tire Temp: Rear outside edges 10–15°C hotter than fronts, rear center temps elevated
- Ride Height: Rear ride height collapse >18 mm at peak speed with minimal front compression
- **Action:** Increase rear wing mainplane angle +0.5–1.0°, add rear gurney flap if wing at limit

**Pitch Instability (Front-End Diving):**
- Telemetry: Front damper compression velocities >120 mm/s during corner entry braking
- Ride Height: Front ride height drops >8 mm within 0.3 seconds of brake application
- Driver: "Front end dives into braking zones, inconsistent turn-in feel"
- **Action:** Increase front bump damping +2–4 clicks, consider stiffer front springs if issue persists

**Pitch Instability (Porpoising):**
- Telemetry: Oscillating ride height at front and rear (0.5–1.5 Hz frequency) during high-speed running
- Damper: Alternating compression/extension velocity spikes at 0.5–2 second intervals
- Driver: "Car bouncing or breathing at high speed, unsettled platform"
- **Action:** Increase front and rear rebound damping +3 clicks, raise minimum ride height +3 mm to increase underbody flow margin

**Roll Excess (Lateral Platform Control):**
- Telemetry: Front or rear roll angles exceeding 3.0° at peak lateral acceleration
- Tire Temp: Extreme inside-outside temperature differentials (>18°C)
- Driver: "Car rolls excessively in fast corners, delayed response"
- **Action:** Increase anti-roll bar stiffness one position stiffer, verify with post-adjustment roll angle telemetry

### Setup Adjustment Magnitude Guidelines

**Wing Angle Adjustments:**
- Minor balance trim: ±0.25–0.5° mainplane angle changes
- Moderate balance shift: ±0.5–1.0° mainplane, consider gurney flap add/remove (10–20 mm height)
- Major balance overhaul: ±1.0–2.0° mainplane combined with flap changes and potential ride height revision

**Damper Click Adjustments:**
- Initial exploration: ±2–3 clicks from baseline, assess telemetry response
- Refinement tuning: ±1 click increments once behavior understood
- Damper adjustment limits: Avoid exceeding 50% of available range in single direction to preserve mechanical grip compliance

**Anti-Roll Bar Adjustments:**
- Blade position changes: One position (typically 2–3 mm blade length change) per iteration
- Always adjust front and rear independently; avoid simultaneous changes that obscure cause-effect
- Document absolute settings: "Front ARB blade position 4/5, rear ARB position 3/5"

**Ride Height Adjustments:**
- Minimum safe clearance: 15–20 mm front, 25–30 mm rear (circuit-dependent)
- Rake angle optimization: 8–15 mm rake (rear higher than front) typical for underbody-dependent aero
- Ride height changes affect spring preload: Recalibrate ride height sensors after spring changes

### Atmospheric Correction Factors

Aerodynamic downforce generation scales with air density, demanding correction factors when atmospheric conditions deviate from baseline test sessions. Use the following empirical corrections to normalize setup recommendations across varying conditions:

**Air Density Correction Formula:**
```text
Density_Ratio = (Pressure_mbar / 1013) * (288 / (Temp_Kelvin))
Corrected_Downforce = Measured_Downforce * Density_Ratio
```

**Practical Application Example:**
- Baseline test: 1013 mbar, 20°C (293 K), measured front downforce 2000 N at 250 km/h
- Race day: 995 mbar, 28°C (301 K)
- Density ratio: (995/1013) * (288/301) = 0.939
- Expected race downforce: 2000 N * 0.939 = 1878 N

The 6% downforce reduction requires compensating wing angle increase of approximately +0.5° to restore baseline aerodynamic balance and tire loading characteristics.

### Tire Temperature Target Ranges by Compound

| Tire Compound | Optimal Center Temp (°C) | Inside-Outside Differential (°C) | Front-Rear Balance (% hotter front) |
|---------------|--------------------------|----------------------------------|-------------------------------------|
| Slick Soft | 95–105 | 5–10 | 6–10% |
| Slick Medium | 88–98 | 5–10 | 5–8% |
| Slick Hard | 82–92 | 4–8 | 4–7% |
| Wet Intermediate | 65–75 | 3–6 | 3–5% |

### Telemetry Channel Alarm Thresholds

Configure MoTeC i2 Pro alarm outputs to alert when critical aerodynamic safety thresholds breach during live sessions:

**Minimum Ride Height Alarm:**
- Front ride height < 12 mm: Risk of front underbody contact and catastrophic flow separation
- Rear ride height < 20 mm: Risk of diffuser stall and sudden rear downforce loss

**Excessive Damper Velocity Alarm:**
- Any corner damper velocity > 180 mm/s: Indicates suspension bottoming or excessive transient loading
- Trigger review of bump stops, spring rates, and damper digressive tuning

**Roll Angle Alarm:**
- Front or rear roll angle > 4.0°: Excessive platform attitude change risking flow detachment
- Immediate anti-roll bar stiffness increase required

**Pitch Rate Alarm:**
- Pitch angle change rate > 5.0 deg/s: Unstable aerodynamic platform oscillation
- Address through damper rebound tuning and ride height increase

### Rapid Setup Iteration Protocol

When track time is limited and multiple aerodynamic balance hypotheses require testing, employ this prioritized iteration sequence to maximize learning efficiency:

**Run 1 – Baseline Data Capture (5 laps):**
- Document all setup parameters photographically (wing angles, damper settings, ride heights)
- Capture comprehensive telemetry across all corner types
- Record tire temperatures immediately post-session
- Establish driver subjective baseline: "Rate front-end confidence 1-10, rear stability 1-10"

**Run 2 – Primary Hypothesis Test (3 laps):**
- Implement single variable change addressing highest-priority issue (typically aerodynamic balance)
- Example: Front wing +1.0° if high-speed understeer identified
- Capture telemetry emphasizing high-speed corner entry phases
- Quick tire temperature spot check (front-left, rear-left only if time-constrained)

**Run 3 – Secondary Hypothesis or Refinement (3 laps):**
- If Run 2 improved behavior but overshot ideal balance, refine adjustment magnitude
- If Run 2 degraded behavior, revert to baseline and test alternative hypothesis
- If Run 2 achieved desired balance, explore complementary optimization (damper fine-tuning)

**Run 4 – Validation and Edge Case Testing (5 laps):**
- Validate optimized setup across full fuel load range (simulate race conditions)
- Instruct driver to explore handling limit boundaries intentionally
- Capture tire temperature data over longer run to assess thermal stability and wear rates

### Session Engineering Log Template

Maintain a structured engineering log capturing all setup iterations, telemetry observations, and decision rationale. This log serves as institutional memory across race weekends and enables pattern recognition as circuit-specific aerodynamic knowledge accumulates.

**Session Header:**
- Date/Time: 2025-01-15 14:30
- Circuit: Silverstone Grand Prix
- Session Type: Free Practice 2
- Atmospheric: 18°C ambient, 1015 mbar, 28°C track temp, wind 8 km/h SW
- Fuel Load: 60 L (half tank), driver weight 75 kg

**Baseline Configuration:**
- Front wing: +3.5° mainplane, no gurney
- Rear wing: +8.0° mainplane, 20 mm gurney
- Ride heights: 22 mm front, 35 mm rear (static, driver aboard)
- Front dampers: Bump 6, Rebound 8 (Öhlins TTX scale)
- Rear dampers: Bump 7, Rebound 9
- Front ARB: Position 3/5, rear ARB: Position 4/5

**Telemetry Observations – Baseline:**
- Copse (high-speed right): Front ride height min 8 mm, front damper compression peak 98 mm/s, steering angle 42° at 1.95 lateral g → understeer index +3.8 deg/g
- Maggotts-Becketts complex: Roll angle peak 2.8° front, 2.4° rear
- Club chicane (low-speed): Tire temps FL 96°C (outside), RR 89°C (outside), temp balance index 0.087

**Hypothesis:** High-speed understeer driven by insufficient front downforce relative to rear; front ride height collapse approaching stall threshold

**Action Taken – Run 2:**
- Front wing increased to +4.5° mainplane (+1.0° adjustment)
- All other parameters unchanged

**Telemetry Observations – Run 2:**
- Copse: Front ride height min 10 mm, front damper compression peak 85 mm/s, steering angle 38° at 1.98 lateral g → understeer index +1.2 deg/g (improvement)
- Tire temps: FL 99°C (outside), RR 91°C (outside), temp balance index 0.081

**Driver Feedback:** "Front end more predictable through Copse and Becketts, can carry more speed. Still slight push mid-corner in Copse. Rear feels stable."

**Conclusion:** Front wing increase moved balance toward neutral, tire temperature distribution improved. Consider additional +0.5° front wing for final optimization.

**Next Action:** Run 3 – Front wing to +5.0°, validate with tire temp and telemetry correlation.

This structured log format ensures all setup decisions trace back to quantitative telemetry evidence and qualitative driver input, enabling robust post-session analysis and continuous aerodynamic optimization refinement across an entire racing season.
