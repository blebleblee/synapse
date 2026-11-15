# Operational Verification Labs: Motorcycle Mechanics

## Objective & Telemetry Environment Setup

The modern race engineer operates at the intersection of mechanical intuition and data-driven precision. This laboratory guide transforms raw telemetry streams into actionable chassis tuning decisions through systematic analysis of suspension kinematics, tire thermal behavior, and rider input coordination. Unlike classroom exercises built around synthetic datasets, these verification labs decode actual logged sessions from track days and competitive sprint races, exposing the engineer to the messy reality of sensor noise, incomplete data capture windows, and the interpretive judgment required when telemetry contradicts rider feedback.

The telemetry environment centers on MoTeC i2 Pro, the de facto standard analysis platform in professional motorcycle racing. MoTeC's strength lies in its channel math engine, which permits construction of derived parameters—roll angle computed from lateral accelerometer and GPS speed, damper velocity extracted by differentiating suspension potentiometer displacement, and friction circle utilization calculated as the vector sum of longitudinal and lateral acceleration divided by estimated tire grip limit. The software ingests CSV exports from RaceCapture Pro MK3 data acquisition units, which sample at 100 Hz across sixteen analog channels and four CAN bus streams. This sampling rate captures transient events during corner entry trail braking and mid-corner throttle application without aliasing, though certain high-frequency phenomena like fork chatter during aggressive front brake application may require supplementary high-speed video correlation.

Installation begins with obtaining MoTeC i2 Pro version 1.2 or later, available through authorized dealer channels or direct from MoTeC Australia for registered competition license holders. The software requires Windows 10 or 11 with a minimum of 16 GB RAM to handle multi-session comparative overlays without pagination lag. After installation, configure the workspace by importing the motorcycle-specific template configuration, which pre-defines standard channel names and engineering units: suspension displacement in millimeters, damper velocity in meters per second, tire temperatures in degrees Celsius, throttle position as percentage, and GPS-derived speed in kilometers per hour. The template also establishes color-coded trace conventions—throttle in green, brake pressure in red, lean angle in blue—that maintain visual consistency across analysis sessions and facilitate rapid pattern recognition when overlaying multiple laps.

RaceCapture Pro MK3 serves as the primary data logger, mounted beneath the seat cowl or within the tail section to minimize aerodynamic disruption and protect against crash damage. The unit interfaces with suspension linear potentiometers installed on fork legs and rear shock linkage, brake line hydraulic pressure transducers threaded into the master cylinder banjo bolts, and a six-axis inertial measurement unit (IMU) rigidly fastened to the chassis centerline near the swingarm pivot. Wiring harness routing follows best practices: shielded twisted-pair cabling for analog sensors to reject electromagnetic interference from ignition coils and alternator rectifiers, and CAN High/Low differential pair terminated with 120-ohm resistors at each bus endpoint to prevent signal reflections. Power supply derives from a dedicated voltage regulator rather than tapping the motorcycle's native electrical system, ensuring clean five-volt reference for analog-to-digital conversion even during engine cranking transients.

Calibration procedures must execute before each track session. Suspension potentiometers require static ride height zeroing with the rider aboard and the motorcycle on-center, establishing the datum from which compression and extension travel measurements reference. Brake pressure transducers calibrate through a two-point process: record the zero-pressure output voltage with the lever released, then apply known hydraulic pressure via a bench bleeding tool fitted with an inline bourdon tube gauge and record the corresponding sensor voltage at 100 bar (approximately 1450 psi, representing threshold braking force). The IMU demands a level-surface initialization sequence where the logger captures three seconds of stationary data to establish gravitational vector alignment and null the gyroscope drift bias. GPS antenna placement atop the tail section maximizes satellite visibility, though pit lane structures and elevated trackside barriers introduce multipath errors that corrupt velocity and position accuracy; engineers mitigate this through post-processing filters that detect and discard anomalous fix solutions with excessive dilution of precision (DOP) values.

Data retrieval occurs via microSD card removal or direct USB connection post-session. RaceCapture stores logs in CSV format with Unix epoch timestamps, channel identifiers, and raw ADC counts or engineering-unit-converted values depending on firmware configuration. The engineer imports these files into MoTeC i2 Pro, where the software parses CSV structure and maps columns to predefined channels based on header string matching. Session metadata—track name, ambient temperature, tire compound, suspension setup sheet—enters manually through the Properties dialog, embedding contextual information that proves invaluable weeks later when reviewing historical tuning progressions. The import wizard also prompts for lap detection configuration: either GPS-based start/finish line crossing or manual marker placement using throttle closure events at corner exit, with the former preferred for its automation and consistency across multiple sessions.

Chassis Sim, a companion kinematic analysis tool, models suspension geometry changes through wheel travel and steering input. Engineers construct virtual linkage assemblies by inputting hard-point coordinates measured from the physical motorcycle: fork axle centerline, fork crown offset, swingarm pivot axis, shock mount locations, and steering head angle. The software then computes instantaneous camber angle, caster trail, anti-squat percentage, and roll center height as functions of suspension displacement, outputting CSV tables that MoTeC imports as math channels to overlay geometric parameters atop telemetry traces. This bidirectional workflow—physical measurements feeding simulation, simulation outputs validating telemetry—closes the loop between theoretical prediction and empirical observation.

The laboratory environment also incorporates tire temperature measurement via infrared pyrometers and analog dial gauges. The Longacre Racing digital pyrometer with memory storage captures surface temperatures at three points across the tire contact patch: inner edge, center tread, and outer edge. Measurement protocol dictates capturing temperatures within thirty seconds of pit lane entry to minimize cooling losses, probing at consistent circumferential locations marked with chalk to enable lap-to-lap comparison. The engineer logs these temperatures into a spreadsheet synchronized with telemetry session timestamps, later graphing thermal distribution against suspension displacement histograms to diagnose camber angle inadequacies or excessive tire slip angle generation during mid-corner phases.

Damper dynamometer testing, though less frequently accessible due to equipment cost, provides ground-truth force-velocity curves that validate suspension tuning decisions. A Roehrig Engineering shock dynamometer cycles the damper through sinusoidal displacement profiles at varying frequencies, measuring resultant force output to construct velocity-dependent damping curves. The engineer exports these curves as CSV files and imports them into MoTeC as reference overlays, comparing logged damper velocities from on-track sessions against force thresholds to identify whether the damper operates within its intended velocity range or exceeds it, inducing harshness or loss of tire contact. For engineers lacking dyno access, alternative verification relies on damper manufacturer published force curves and iterative on-track validation through methodical clicker position adjustments correlated with rider feedback and lap time deltas.

The final preparatory step involves establishing a baseline reference lap. The engineer selects a representative lap from a session where the rider reported neutral handling balance and achieved competitive pace, marking it as the golden reference within MoTeC's lap library. All subsequent analysis compares modified setup iterations against this baseline, quantifying performance deltas in sector times, minimum corner speeds, and peak braking G-forces. This comparative methodology surfaces the incremental gains or losses attributable to specific tuning changes—two clicks softer rebound damping, half-turn additional preload, or five psi tire pressure increase—rather than interpreting each session in isolation without historical context.

With the environment configured, telemetry imported, and baseline established, the engineer proceeds to structured verification exercises that systematically dissect suspension behavior, tire thermal management, and rider input technique through the lens of logged data streams.

---

## Exercise 1: Telemetry Data Import & Driver Trace Correlation

This exercise constructs the foundational workflow for extracting actionable intelligence from raw telemetry logs. The engineer begins with a RaceCapture CSV file captured during a ten-lap track session at a club-level sprint race, progressing through data import, channel validation, lap segmentation, and comparative trace overlay to identify rider input inconsistencies and mechanical setup anomalies.

Begin by launching MoTeC i2 Pro and navigating to File → Open Workspace. Select the motorcycle racing template workspace, which pre-configures channel assignments and graphical layouts optimized for single-track vehicle dynamics. With the workspace loaded, initiate the CSV import wizard via File → Import Data → CSV File. Browse to the RaceCapture log file—typically named with a timestamp convention like `20250115_143022_Session01.csv`—and click Open. The import wizard parses the CSV header row, displaying detected channel names in a mapping dialog. Verify that critical channels align correctly: `GPS_Speed` maps to Speed (km/h), `Accel_Lat` maps to Lateral G, `Accel_Long` maps to Longitudinal G, `SuspFL_Pos` maps to Front Suspension Displacement (mm), `SuspR_Pos` maps to Rear Suspension Displacement (mm), `Brake_Press` maps to Brake Pressure (bar), and `Throttle_Pos` maps to Throttle Position (%). If channel names mismatch due to logger firmware variations, manually drag-and-drop CSV columns onto their corresponding MoTeC channel definitions. Click Import to ingest the dataset.

Post-import, the software populates the Lap Times panel with detected laps based on GPS position crossing the predefined start/finish line coordinates. If lap detection fails—common on unfamiliar tracks lacking GPS boundary data—manually define lap markers by scrubbing the time cursor to throttle-closed corner exit points and pressing the Insert Lap Marker hotkey (default: F3). This manual segmentation proves tedious but essential for isolating individual lap performance and enabling comparative overlays.

Next, validate data integrity by inspecting each channel for dropout events or sensor faults. Open the Channel Inspector panel and sequentially plot each telemetry stream against time. Suspension potentiometers occasionally exhibit zero-voltage dropout when connectors vibrate loose; these manifest as vertical trace discontinuities plummeting to zero displacement before recovering. Brake pressure transducers suffer from air bubble entrapment in hydraulic lines, producing erratic pressure spikes uncorrelated with lever input. GPS velocity traces display characteristic stair-stepping when satellite fix degrades, particularly in pit lane or beneath overhead structures. Flag corrupted laps for exclusion from analysis by right-clicking the lap entry and selecting Exclude Lap, preventing them from polluting statistical aggregates or overlay comparisons.

With data validated, construct a comparative overlay visualizing rider input consistency across three consecutive fast laps. Open the Overlay Manager and select laps 4, 5, and 6—chosen because they occur mid-session after tire warm-up but before degradation onset. Configure the display with four vertically stacked graphs: throttle position and brake pressure in the top pane, lateral and longitudinal G in the second pane, front and rear suspension displacement in the third pane, and GPS speed in the bottom pane. Align all graphs to distance-based X-axis synchronization rather than time-based, ensuring that spatial features—corner entries, apexes, exits—align vertically for direct comparison despite minor lap time variations.

Zoom into the first significant braking zone, typically a high-speed corner entry where the rider decelerates from 200 km/h to 80 km/h over approximately 100 meters. Observe the brake pressure trace: an ideal application exhibits a rapid initial rise to threshold pressure (70-80 bar for a 320mm dual-disc sportbike front brake), holds constant through the primary deceleration phase, then trails off smoothly as the rider releases pressure while simultaneously rolling in throttle. Inconsistent applications—abrupt pressure spikes, multiple discrete peaks, or premature release—indicate rider input uncertainty or front-end instability inducing survival reactions. Note the lap-to-lap repeatability: if brake pressure curves overlay tightly, the rider demonstrates excellent muscle memory calibration and confidence in front tire grip. Divergence beyond 10% peak pressure variance suggests either deteriorating tire performance or suspension setup inadequacy forcing the rider to adapt stroke-by-stroke.

Correlate brake pressure against longitudinal G to assess deceleration efficiency. In the second graph pane, longitudinal G should mirror brake pressure application, reaching peak negative values (typically -1.2 to -1.4 G for modern sportbike tires) coincident with maximum pressure. If longitudinal G plateaus below expected values despite aggressive brake pressure, suspect either front tire saturation—the contact patch exceeds its friction coefficient limit—or rear wheel liftoff, where excessive front load transfer unloads the rear tire completely, eliminating its braking contribution. The solution diverges: tire saturation demands compound change or temperature reduction via pressure adjustment, while rear liftoff requires fork spring preload reduction or rear ride height increase to mitigate pitch angle.

Shift focus to the corner apex, identified by minimum GPS speed and peak lateral G. Examine throttle position: the rider should initiate throttle application slightly before the apex, smoothly ramping from zero to 30-40% as the motorcycle rotates toward corner exit. Abrupt throttle snaps generate longitudinal load transfer that unloads the front tire, destabilizing lean angle and forcing the rider to momentarily close throttle again, visible as a double-hump throttle trace. This phenomenon, colloquially termed "throttle stab," reveals either excessive rear suspension extension damping—preventing timely squat response to chain torque—or insufficient throttle-to-lean coordination from the rider. Differentiate between mechanical and rider causation by comparing throttle traces across laps: consistent double-humps implicate mechanical setup, while random occurrence suggests rider technique variability.

Suspension displacement traces in the third pane expose dynamic platform control. During corner entry braking, front fork compression should reach 60-70% of available travel (approximately 75-85mm on a modern sportbike with 120mm total travel), then stabilize through the apex before rebounding during corner exit acceleration. Excessive compression beyond 80% risks bottoming, evident as trace clipping at maximum displacement followed by instantaneous rebound. Conversely, insufficient compression below 50% indicates excessive fork spring preload or inadequate brake pressure, underutilizing available grip. Rear suspension responds inversely: compressing during acceleration (chain torque squat) and extending during braking (anti-squat geometry and forward load transfer). The ideal rear trace remains relatively centered through mid-corner, neither fully compressed nor extended, maintaining optimal tire contact patch loading.

Construct a velocity-distance graph to assess corner exit performance. Plot GPS speed on the Y-axis against distance on the X-axis, overlaying the three selected laps. The exit velocity gradient—the slope of the speed curve as the motorcycle accelerates away from the apex—quantifies drive traction efficiency. Steeper gradients indicate superior traction utilization, either from better tire temperature management, optimized rear suspension squat characteristics, or more confident throttle application. If one lap exhibits noticeably superior exit gradient, investigate the telemetry preceding it: did the rider carry slightly more mid-corner speed (higher apex velocity), apply throttle earlier (lower distance coordinate at initial throttle application), or simply execute smoother throttle modulation (higher average throttle position through the exit phase)? Isolate the causative factor by examining each input independently, then replicate that technique or setup condition in subsequent sessions.

Quantify lap time deltas using MoTeC's sector analysis tool. Define sectors by major track features—typically four sectors per lap, each encompassing 2-3 corners. The software computes elapsed time per sector for each lap, displaying deltas relative to the baseline reference lap. If Sector 2 consistently shows +0.3 seconds relative to the baseline, drill into that sector's telemetry to diagnose whether time loss occurs during braking (lower peak longitudinal G), corner entry (slower minimum speed), mid-corner (excessive roll angle or suspension deflection indicating instability), or corner exit (shallower velocity gradient). This granular decomposition transforms abstract lap time deficits into specific mechanical or rider technique corrections.

Export the annotated overlay as a PDF report via File → Export → PDF Report. Configure the export to include all four graph panes, lap time summary table, and embedded notes documenting observed anomalies. This report serves as the session debrief artifact, shared with the rider and crew chief to align tuning decisions with empirical evidence rather than subjective impressions. Archive the PDF alongside the raw CSV log file in a version-controlled directory structure organized by date and track, enabling longitudinal analysis of setup evolution across the racing season.

Finally, establish a math channel library for derived parameters used in subsequent exercises. Navigate to the Math Channels panel and define the following expressions:

**Damper Velocity Front (m/s):**  
`diff('Front Suspension Displacement (mm)') / 1000`  
This differentiates front fork displacement with respect to time, converting millimeters per second to meters per second to match damper force curve units.

**Damper Velocity Rear (m/s):**  
`diff('Rear Suspension Displacement (mm)') / 1000`  
Parallel computation for rear shock.

**Friction Circle Utilization (%):**  
`sqrt(pow('Lateral G', 2) + pow('Longitudinal G', 2)) / 1.4 * 100`  
Computes the magnitude of the combined acceleration vector and normalizes it against an assumed maximum tire grip limit of 1.4 G, expressing the result as a percentage of available friction circle capacity.

**Roll Angle (degrees):**  
`atan('Lateral G' / 9.81) * 180 / pi()`  
Estimates motorcycle roll angle from lateral acceleration, assuming the accelerometer mounts at the chassis centerline and that roll occurs about an axis through the contact patches.

**Throttle Rate of Change (%/s):**  
`diff('Throttle Position (%)')`  
Quantifies throttle application aggressiveness, revealing abrupt inputs that destabilize chassis dynamics.

Save the workspace with these math channels enabled, ensuring they auto-populate in future imported sessions without re-definition.

---

## Exercise 2: Damper Velocity Histogram Tuning & Anti-Roll Bar Optimization

Suspension damping optimization hinges on understanding the velocity distribution experienced by fork and shock dampers during dynamic track operation. This exercise constructs damper velocity histograms from logged telemetry, interprets the distributions relative to damper force curves, and iteratively adjusts compression and rebound clicker settings to center the operational velocity range within the damper's most controllable force region.

Begin with a ten-lap telemetry session imported into MoTeC i2 Pro, ensuring the Front Damper Velocity and Rear Damper Velocity math channels populate correctly per Exercise 1 definitions. Open the Histogram tool via Analysis → Histogram and configure it to analyze Front Damper Velocity over the entire session duration. Set the histogram bin width to 0.05 m/s, providing sufficient resolution to detect fine-grained velocity clustering without over-smoothing the distribution. Execute the analysis, generating a bar graph displaying frequency counts across velocity bins ranging from approximately -2.0 m/s (compression) to +2.0 m/s (extension/rebound).

Interpret the histogram shape: an ideal distribution approximates a Gaussian bell curve centered slightly offset from zero velocity toward the compression side, reflecting the fact that modern sportbike suspension spends marginally more time absorbing bumps (compression) than recovering from them (rebound) due to aggressive track surface irregularities. However, real-world histograms frequently exhibit bimodal peaks—one during braking-induced compression, another during corner exit rebound—or pronounced asymmetry with excessive tail density extending into high compression velocities beyond 1.5 m/s. These pathological distributions signal damping inadequacy: the damper fails to control motion within its designed velocity envelope, forcing it into blow-off regions where damping force plateaus and platform control degrades.

Overlay the histogram against the damper's published force-velocity curve, obtained from the suspension manufacturer's technical datasheet. For example, an Öhlins TTX36 fork damper exhibits compression force rising logarithmically from 200 N at 0.1 m/s to 1200 N at 1.5 m/s, then flattening due to shim stack blow-off beyond 1.8 m/s. If the histogram concentration lies between 0.2 m/s and 1.2 m/s, the damper operates within its controllable range and tuning proceeds via clicker adjustments. Conversely, if significant histogram density extends beyond 1.5 m/s, the damper exceeds its velocity capacity and requires either spring rate reduction (to decrease suspension displacement amplitude and hence velocity) or complete damper revalve (re-shimming the piston to increase high-speed damping force before blow-off onset).

Assume the front damper histogram reveals excessive density between 1.3 m/s and 1.8 m/s during corner entry braking, indicating insufficient compression damping. The engineer increases front fork compression clickers from the current 12 clicks out (from full closed) to 10 clicks out, closing the adjuster by two clicks. Each click typically alters low-speed compression force by approximately 5%, though the precise sensitivity varies by damper design. Return to the track for a five-lap validation session with the adjusted setting.

Import the new telemetry and regenerate the front damper velocity histogram. If successful, the distribution shifts leftward, reducing density above 1.5 m/s and concentrating more frequency around 0.8-1.2 m/s. Simultaneously, inspect the front suspension displacement trace during corner entry: the fork should compress more gradually, reaching similar maximum displacement but over a longer time duration, indicating higher damping resistance. If the fork now exhibits abrupt compression followed by immediate extension bounce, the clicker adjustment overcorrected, introducing excessive damping that prevents the fork from tracking surface irregularities. Revert one click outward (11 clicks out) to split the difference.

Parallel analysis applies to rear shock tuning. Generate a rear damper velocity histogram and correlate it against the shock's force curve. Rear suspension differs from front in that it experiences more extreme velocity spikes during chain torque squat (corner exit acceleration) and anti-squat geometry effects. If the rear histogram exhibits a pronounced tail extending beyond 2.0 m/s during exit acceleration, suspect insufficient rebound damping. The shock compresses under chain torque but rebounds too rapidly when the rider momentarily closes throttle mid-exit to correct line, inducing a pogo-stick oscillation visible as multiple compression-rebound cycles on the displacement trace. Increase rear rebound damping by closing the rebound adjuster two clicks (e.g., from 14 clicks out to 12 clicks out), then re-test.

Quantify the tuning impact using MoTeC's statistical summary tool. Compute the standard deviation of front suspension displacement across the baseline and adjusted sessions. A well-tuned suspension reduces displacement standard deviation by 10-15%, indicating more consistent platform height and improved tire contact patch load stability. Additionally, calculate the 95th percentile damper velocity: if it decreases from 1.7 m/s to 1.3 m/s post-adjustment, the damper no longer spends significant time in blow-off, confirming the tuning direction.

Extend the analysis to anti-roll bar tuning, though motorcycles lack literal anti-roll bars due to single-track geometry. Instead, engineers modulate roll stiffness through spring preload and damping asymmetry. However, for sidecars or three-wheeled platforms, anti-roll bars exist and require tuning via telemetry. Plot roll angle (computed via the math channel from Exercise 1) against lateral G. An ideal relationship exhibits linear proportionality: roll angle increases at a constant rate per G of lateral load. Non-linearity—roll angle accelerating disproportionately at high lateral G—indicates insufficient roll stiffness, whether from inadequate spring rates or soft damping. If increasing damping fails to restore linearity, stiffer springs are necessary.

Construct a damper force estimation channel by multiplying damper velocity by the interpolated force from the manufacturer's curve. In MoTeC's math channel editor, define:

**Front Damper Force Estimate (N):**  
`interpolate('Front Damper Velocity (m/s)', [0, 0.5, 1.0, 1.5, 2.0], [0, 400, 800, 1200, 1300])`  
Replace the bracketed force values with actual curve data from the damper datasheet. This derived channel estimates real-time damping force during logged sessions, enabling direct comparison against chassis load transfer forces to assess whether damping adequately resists suspension displacement.

Plot estimated front damper force against front suspension displacement. During corner entry braking, damper force should rise sharply as the fork compresses, peaking at approximately 1000-1200 N for a 600cc sportbike. If force plateaus prematurely at 800 N despite continued displacement, the damper has entered blow-off and no longer provides proportional resistance. This confirms the necessity for spring rate increase or damper revalve.

Document each clicker adjustment and corresponding histogram shift in a suspension tuning log spreadsheet. Columns include: Session Date, Front Compression Clickers, Front Rebound Clickers, Rear Compression Clickers, Rear Rebound Clickers, Front 95th Percentile Velocity, Rear 95th Percentile Velocity, Best Lap Time, and Rider Feedback. Over multiple sessions, patterns emerge: perhaps front compression at 10 clicks out consistently yields fastest lap times on smooth tracks but induces harshness on bumpy circuits, necessitating 12 clicks out for those venues. This empirical database becomes the team's institutional knowledge, accelerating setup convergence at new tracks.

Finally, validate damper adjustments through rider feedback correlation. After each setup change, conduct a structured debrief using a standardized questionnaire: rate front-end stability during corner entry on a 1-10 scale, assess mid-corner confidence, and evaluate rear grip during exit acceleration. Plot these subjective ratings against quantitative telemetry metrics—suspension displacement standard deviation, damper velocity histogram centroid, and minimum corner speeds. If rider-reported front-end instability coincides with histogram tail density above 1.5 m/s, the correlation confirms that telemetry-derived damping inadequacy manifests as perceptible handling deficits. Conversely, if the rider reports improved stability post-adjustment but telemetry shows negligible histogram change, suspect placebo effect or conflated variables like tire temperature variation.

---

## Exercise 3: Tire Temperature Analysis & Wear Modeling

Tire thermal management dictates performance consistency across session duration and longevity across race distance. This exercise integrates pyrometer-measured surface temperatures with telemetry-derived slip angle estimates and suspension camber geometry to optimize tire pressure, camber angle, and load distribution, culminating in a predictive wear model that forecasts remaining grip reserves based on thermal history.

Immediately upon pit lane entry after a flying lap, execute the tire temperature measurement protocol. Using a Longacre digital pyrometer, probe the front tire at three circumferential locations spaced 120 degrees apart, each measurement capturing inner edge, center tread, and outer edge temperatures. Record measurements in a spreadsheet with columns: Lap Number, Front Inner (°C), Front Center (°C), Front Outer (°C), Rear Inner (°C), Rear Center (°C), Rear Outer (°C), and Ambient Temperature (°C). Repeat for the rear tire. Complete the protocol within sixty seconds to minimize cooling bias, as tire surface temperature drops approximately 5-10°C per minute post-session due to convective and radiative heat loss.

Interpret the temperature distribution across the tire width. An ideal front tire exhibits the hottest temperature at the center tread, with inner and outer edges 5-10°C cooler, indicating optimal contact patch loading and camber angle alignment. If the outer edge reads significantly hotter than the center—by 15°C or more—the motorcycle operates with insufficient camber angle during cornering, overloading the outer tread blocks and underutilizing the inner contact patch. The remedy involves increasing static camber via suspension geometry adjustment (if available through eccentric pivot bushings) or altering ride height to influence dynamic camber gain through suspension travel. Conversely, if the inner edge runs hottest, excessive camber exists, though this pathology rarely occurs on motorcycles due to their reliance on lean angle rather than static camber.

Rear tire temperature interpretation differs due to the tire's dual role: supporting lean angle cornering forces and transmitting longitudinal drive torque. A rear tire operating optimally exhibits a relatively uniform temperature distribution across the tread width when measured immediately post-apex, with a modest 5-10°C increase at the center reflecting drive torque slip. Pronounced center overheating—exceeding 20°C above edge temperatures—indicates wheel spin during corner exit acceleration, either from excessive throttle application or insufficient rear suspension squat allowing the tire to break loose. The solution involves either rider coaching (smoother throttle modulation) or mechanical tuning (softer rear compression damping to allow more rapid squat response, increasing rear contact patch load during initial throttle application).

Correlate measured temperatures against telemetry-logged tire surface temperature sensors, if equipped. High-end race teams embed thermocouples 1-2mm beneath the tire tread surface, logging continuous temperature traces synchronized with telemetry. Import these traces into MoTeC and overlay them against lap distance. Tire temperature should stabilize within 2-3 laps post-session start, reaching operational range (typically 80-100°C for slick race tires, 60-80°C for DOT street-legal track tires). If temperature fails to stabilize—exhibiting continuous rise throughout the session—suspect inadequate tire pressure allowing excessive carcass flexing and hysteretic heat generation. Increase cold pressure by 1-2 psi and re-test.

Construct a slip angle estimation math channel to diagnose tire overwork. Slip angle, the angular difference between the tire's direction of travel and its heading, correlates directly with lateral force generation and thermal energy dissipation. In MoTeC, approximate slip angle as:

**Front Slip Angle Estimate (degrees):**  
`atan(('Lateral G' * 9.81 * 1.2) / (pow('GPS Speed (km/h)' / 3.6, 2) / 0.6)) * 180 / pi()`  
This simplified formula assumes front axle weight distribution (1.2 representing front mass proportion), wheelbase (0.6 meters, a typical sportbike dimension), and converts lateral acceleration into slip angle via single-track vehicle dynamics. The estimate omits steering angle input due to sensor unavailability on most club-level data loggers, introducing modest error but sufficient for diagnostic trends.

Plot estimated front slip angle against tire temperature. If slip angles consistently exceed 8-10 degrees during mid-corner phases coincident with high tire temperatures, the front tire operates beyond its optimal slip angle range, generating excessive heat through tread scrub rather than efficient grip. The solution diverges based on root cause: if the rider carries excessive corner entry speed forcing high slip angles, coaching emphasizes earlier braking and lower minimum speeds. If slip angles arise despite conservative entry speeds, suspect insufficient front tire pressure causing carcass collapse and contact patch distortion, artificially inflating apparent slip angle.

Develop a predictive tire wear model correlating thermal exposure with grip degradation. Begin by defining a thermal dose metric:

**Thermal Dose (°C·laps):**  
Sum of (Tire Center Temperature - Baseline Temperature) × Number of Laps  
For example, if a tire operates at 90°C center temperature for 10 laps with a baseline of 70°C, thermal dose equals (90 - 70) × 10 = 200°C·laps. This metric accumulates heat exposure over session duration, serving as a proxy for tread compound degradation via thermal cycling and oxidative hardening.

Correlate thermal dose against lap time degradation. Import multi-session telemetry spanning a full race distance (e.g., 20 laps). Plot best lap time per five-lap segment against cumulative thermal dose. A linear regression typically reveals lap time increasing by 0.1-0.3 seconds per 100°C·laps of thermal exposure, quantifying performance drop-off. If degradation exceeds 0.5 seconds per 100°C·laps, suspect aggressive tire compound choice for the track's thermal demand, necessitating a switch to a harder compound with superior thermal stability despite potentially lower peak grip.

Validate the wear model through post-session tire inspection. Measure tread depth at multiple points using a digital depth gauge, recording remaining tread in millimeters. Compare measured wear depth against thermal dose: tires with higher cumulative thermal exposure exhibit greater depth loss. Construct a calibration curve (wear depth vs. thermal dose) specific to each tire compound, enabling predictive modeling. For example, if Compound A loses 0.5mm per 500°C·laps, the engineer forecasts that a 30-lap race accumulating 1200°C·laps total dose will consume 1.2mm of tread, confirming the tire's suitability for race distance without excessive degradation.

Optimize tire pressure through iterative telemetry correlation. Conduct three back-to-back five-lap sessions with front tire cold pressures set at 30 psi, 32 psi, and 34 psi (rear pressure held constant at 28 psi). Import all three sessions into MoTeC and overlay minimum corner speeds across a consistent set of corners. If 32 psi yields the highest minimum speeds and lowest lap time variance, that pressure setting optimally balances contact patch loading and carcass stiffness. Simultaneously, inspect suspension displacement traces: excessive pressure (34 psi) manifests as reduced fork compression during corner entry braking, indicating the inflated tire's increased stiffness absorbs less load transfer, forcing the suspension to work harder. Conversely, insufficient pressure (30 psi) exhibits excessive fork compression and erratic steering response due to carcass instability.

Document tire management strategy in a session-by-session matrix. Columns include: Ambient Temperature, Track Surface Temperature (measured via infrared gun), Front Cold Pressure, Rear Cold Pressure, Average Front Temperature Post-Session, Average Rear Temperature Post-Session, Thermal Dose Accumulated, and Fastest Lap Time. Over a season, this database reveals temperature-pressure correlations: perhaps front pressure requires +2 psi on hot days (ambient above 30°C) to prevent overheating, or -1 psi on cold days (ambient below 15°C) to achieve operating temperature. These empirical adjustments transcend generic manufacturer recommendations, tailoring tire setup to the team's specific riding style and track conditions.

Finally, integrate tire thermal data with suspension tuning from Exercise 2. If increasing front compression damping (Exercise 2) reduces front tire edge temperatures by 5°C while simultaneously decreasing damper velocity histogram tail density, the causative mechanism becomes clear: stiffer damping limits fork compression during braking, reducing dynamic load transfer magnitude, moderating contact patch pressure, and ultimately lowering thermal generation. This systems-level insight—linking suspension tuning to tire thermal management—exemplifies the holistic engineering approach required for competitive performance optimization.

---

## Race Engineering Diagnostic Cheat Sheet & Setup Matrix

This reference section consolidates diagnostic decision trees and setup parameter matrices derived from the preceding exercises, enabling rapid troubleshooting during practice sessions and pre-race setup convergence.

### Damper Velocity Histogram Diagnostic Tree

**Symptom:** Front damper velocity histogram tail density exceeds 1.5 m/s (>10% of total counts)  
**Primary Diagnosis:** Insufficient front compression damping or excessive fork spring rate inadequacy  
**Corrective Actions:**  
1. Increase front compression damping: close compression adjuster 2 clicks (e.g., 12 clicks out → 10 clicks out)  
2. If histogram tail persists post-adjustment, reduce fork spring preload 5mm to decrease compression force resistance threshold  
3. If both adjustments fail, consider fork spring rate reduction (e.g., 1.0 N/mm → 0.95 N/mm) or damper revalve  

**Symptom:** Rear damper velocity histogram exhibits bimodal peaks at +1.0 m/s (rebound) and -1.2 m/s (compression)  
**Primary Diagnosis:** Underdamped rear shock inducing pogo oscillation during corner exit  
**Corrective Actions:**  
1. Increase rear rebound damping: close rebound adjuster 2 clicks  
2. Validate via suspension displacement trace—oscillation frequency should decrease  
3. If oscillation persists, increase rear compression damping 1 click to resist initial squat  

### Tire Temperature Distribution Matrix

| Temperature Pattern | Inner (°C) | Center (°C) | Outer (°C) | Diagnosis | Corrective Action |
|---------------------|-----------|------------|-----------|-----------|-------------------|
| Optimal | 85 | 95 | 85 | Proper camber, balanced load | Maintain current setup |
| Outer Overheat | 80 | 90 | 110 | Insufficient camber angle | Increase static camber or reduce ride height |
| Center Overheat | 85 | 115 | 85 | Wheel spin (rear) or excessive pressure | Soften throttle application or reduce tire pressure 1 psi |
| Inner Overheat | 105 | 95 | 80 | Excessive camber angle (rare) | Decrease static camber |
| Uniform Underheat | 65 | 70 | 65 | Insufficient tire pressure or ambient cold | Increase cold pressure 2 psi or abort session |

### Suspension Setup Parameter Reference

**Front Fork Settings (Typical 600cc Sportbike):**  
- Spring Rate: 0.95-1.05 N/mm  
- Preload: 10-15mm static sag (rider aboard, measured from fully extended)  
- Compression Damping: 10-14 clicks out from full closed (softer for bumpy tracks, stiffer for smooth tracks)  
- Rebound Damping: 8-12 clicks out from full closed  
- Fork Oil Level: 110-120mm from top of fully compressed fork (higher level = progressive spring rate)  

**Rear Shock Settings:**  
- Spring Rate: 9.5-11.0 N/mm  
- Preload: 8-12mm static sag  
- Compression Damping: 12-16 clicks out  
- Rebound Damping: 10-14 clicks out  
- Ride Height: 0-10mm above baseline (raising rear increases front-end feel, decreases stability)  

### Telemetry Channel Threshold Alerts

Configure MoTeC i2 Pro to flag the following threshold violations in real-time during live telemetry streaming or post-session analysis:

- **Front Suspension Bottoming:** Front Suspension Displacement > 110mm (indicates harsh compression damping or insufficient spring rate)  
- **Rear Wheel Spin:** Rear Slip Ratio (derived from wheel speed vs. GPS speed) > 8% mid-corner (indicates excessive throttle or inadequate traction)  
- **Excessive Lean Angle:** Roll Angle > 58 degrees (approaching safety limit for most sportbikes)  
- **Brake Pressure Spike:** Brake Pressure Rate of Change > 50 bar/s (indicates abrupt, potentially destabilizing brake input)  
- **Throttle Chop:** Throttle Rate of Change < -80%/s (indicates mid-corner survival reaction due to instability)  

### Session Debrief Question Protocol

Standardize rider feedback collection through this structured questionnaire, administered immediately post-session:

1. Front-end stability during corner entry braking (1-10 scale): ____  
2. Mid-corner confidence and line precision (1-10 scale): ____  
3. Rear grip during corner exit acceleration (1-10 scale): ____  
4. Suspension harshness over curbs/bumps (1-10 scale, 10 = excessive harshness): ____  
5. Steering effort and responsiveness (1-10 scale, 10 = too heavy/slow): ____  
6. Specific corner or track section requiring improvement: ________________  
7. Comparative assessment vs. previous session (better/same/worse): ____  

Cross-reference rider ratings against telemetry metrics: if front-end stability rates 4/10 but telemetry shows no front suspension anomalies, suspect tire temperature or pressure issue rather than suspension tuning.

### Quick-Reference Clicker Adjustment Increments

**Conservative Adjustment (Low Confidence in Direction):**  
1 click compression or rebound adjustment  
Lap time delta threshold for validation: ±0.2 seconds  

**Standard Adjustment (Moderate Confidence):**  
2 clicks compression or rebound adjustment  
Lap time delta threshold: ±0.4 seconds  

**Aggressive Adjustment (High Confidence or Emergency Correction):**  
3-4 clicks compression or rebound adjustment  
Lap time delta threshold: ±0.6 seconds  
Caution: Excessive adjustment risks overshooting optimal window, necessitating multiple iterations to converge  

### Tire Pressure Starting Point Calculation

**Formula:**  
Cold Pressure (psi) = Base Pressure + Ambient Factor + Load Factor  

**Base Pressure:**  
Front = 30 psi | Rear = 28 psi (manufacturer baseline for 600cc sportbike, street-legal DOT tire)  

**Ambient Factor:**  
+1 psi per 5°C above 20°C ambient  
-1 psi per 5°C below 20°C ambient  

**Load Factor:**  
+0.5 psi if rider mass > 80 kg  
-0.5 psi if rider mass < 65 kg  

**Example Calculation:**  
Ambient = 28°C, Rider = 75 kg  
Front Cold Pressure = 30 + [(28-20)/5 × 1] + 0 = 30 + 1.6 = 31.6 psi → round to 32 psi  
Rear Cold Pressure = 28 + 1.6 = 29.6 psi → round to 30 psi  

### Damper Force Curve Interpolation Table

For engineers lacking access to manufacturer-published force curves, use these generic approximations for modern sportbike cartridge dampers (values in Newtons):

**Front Fork Compression Force:**  
| Velocity (m/s) | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 |
|----------------|-----|-----|-----|-----|-----|
| Force (N)      | 0   | 350 | 750 | 1150| 1250|

**Front Fork Rebound Force:**  
| Velocity (m/s) | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 |
|----------------|-----|-----|-----|-----|-----|
| Force (N)      | 0   | 450 | 950 | 1350| 1450|

**Rear Shock Compression Force:**  
| Velocity (m/s) | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 |
|----------------|-----|-----|-----|-----|-----|
| Force (N)      | 0   | 400 | 900 | 1400| 1550|

**Rear Shock Rebound Force:**  
| Velocity (m/s) | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 |
|----------------|-----|-----|-----|-----|-----|
| Force (N)      | 0   | 500 | 1100| 1650| 1800|

Import these tables into MoTeC as interpolation lookup arrays for the damper force estimation math channels defined in Exercise 2.

### Data Logger Configuration Checklist

**Pre-Session Validation:**  
☐ Suspension potentiometers zeroed with rider aboard, bike on-center  
☐ Brake pressure transducers calibrated (zero pressure and 100 bar reference points recorded)  
☐ IMU initialized on level surface (3-second stationary capture completed)  
☐ GPS antenna clear line-of-sight (no bodywork obstruction)  
☐ MicroSD card formatted and inserted, sufficient storage for session duration (minimum 2 GB free)  
☐ Sampling rate confirmed at 100 Hz across all analog channels  
☐ CAN bus termination resistors verified (120Ω at each bus endpoint)  
☐ Battery voltage >12.5V (logger power supply)  

**Post-Session Data Retrieval:**  
☐ Logger removed from motorcycle before tire temperature measurement (to avoid delay)  
☐ CSV file exported to laptop within 5 minutes (prevents data loss from card corruption)  
☐ File renamed with convention: YYYYMMDD_HHMM_TrackName_SessionType.csv  
☐ Backup copy saved to cloud storage (Google Drive, Dropbox) immediately  

This cheat sheet, combined with the structured exercises and telemetry workflows established in Exercises 1-3, equips the race engineer with a systematic, data-driven methodology for motorcycle chassis optimization. Mastery demands not only technical proficiency in telemetry analysis tools but also the interpretive acumen to synthesize mechanical measurements, rider feedback, and lap time outcomes into coherent tuning directives. The engineer functions as the translator between empirical sensor data and actionable mechanical adjustments, continuously refining the motorcycle's dynamic behavior toward the asymptotic limit of tire grip and rider confidence.
