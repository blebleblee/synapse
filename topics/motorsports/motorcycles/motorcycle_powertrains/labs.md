# Operational Verification Labs: Motorcycle Powertrains

## Objective & Telemetry Environment Setup

The powertrain of a racing motorcycle represents the heart of its performance envelope, yet it operates within a tightly coupled mechanical system where engine torque characteristics, clutch engagement behavior, gearbox ratios, and final drive sprocket selection dictate not only straight-line acceleration but also corner-exit traction management and rider confidence under power. Unlike four-wheeled chassis where differential lockup and electronic torque vectoring provide additional tuning dimensions, the motorcycle engineer must orchestrate a delicate balance between peak power delivery, throttle response linearity, and rear tire traction stability through a narrower set of mechanical interventions. This laboratory sequence provides hands-on verification protocols for analyzing real-world telemetry data streams, correlating engine dynamometer curves with logged GPS acceleration traces, and diagnosing powertrain-induced handling anomalies through systematic data acquisition and numerical analysis.

The modern racing motorcycle powertrain telemetry stack consists of three primary sensor domains: engine performance instrumentation, drivetrain mechanical feedback, and chassis dynamic response. Engine-side channels include crankshaft rotational speed measured via Hall effect or inductive pickup sensors at the primary drive sprocket, throttle position via rotary potentiometer or contactless magnetic angle sensor, and inlet manifold absolute pressure for fuel injection load calculation. Drivetrain instrumentation captures clutch pack engagement through hydraulic line pressure transducers, gearbox output shaft speed for ratio verification and wheelie detection, and final drive chain tension fluctuation via strain gauge load cells. Chassis feedback channels provide the critical correlation layer: rear wheel speed from ABS reluctor ring pulse counting, longitudinal and lateral acceleration from triaxial MEMS accelerometer arrays, and suspension travel from linear potentiometers mounted to the rear shock absorber body. When synchronized to GPS absolute position and lap timing beacon triggers, these channels enable lap-by-lap comparison of power delivery efficiency, identification of traction limit excursions, and quantification of setup changes on acceleration performance.

The laboratory environment assumes access to MoTeC i2 Pro telemetry analysis software, the de facto standard in professional motorsport for multi-channel time-series visualization and mathematical channel synthesis. The i2 Pro workspace permits overlay comparison of multiple logged sessions, application of digital filtering and smoothing algorithms, and construction of derived telemetry math channels using C-style expression syntax. Data acquisition hardware varies by racing class and budget: club-level sportbike racing may utilize RaceCapture Pro MK3 with integrated GPS receiver and analog input expansion modules, while factory Grand Prix teams deploy MoTeC M1 series engine control units with integrated data logger functionality and CAN bus bridge to suspension position sensors and wheel speed encoders. Regardless of hardware platform, the fundamental workflow remains consistent: acquire time-stamped sensor data at sufficient sample rate to capture transient events, export to CSV or MoTeC LD file format, import into analysis software, and apply mathematical transformations to extract actionable engineering insight.

For these exercises, the practitioner requires a telemetry dataset from a minimum of five flying laps on a known circuit, captured at 100 Hz sample rate or higher for critical channels such as throttle position, engine RPM, and rear wheel speed. Lower priority channels including coolant temperature and fuel pressure may log at 10 Hz without loss of diagnostic utility. The dataset must include GPS latitude and longitude coordinates for distance-based lap alignment, plus a lap beacon trigger channel to segment continuous logging into discrete lap instances. Supplementary tooling includes a spreadsheet application for suspension kinematics calculations, Python 3.x with NumPy and Matplotlib libraries for custom signal processing routines, and optionally MATLAB for frequency domain analysis of driveline oscillation modes. Physical workshop instrumentation provides ground truth calibration: a calibrated torque wrench for drivetrain fastener verification, dial indicator for chain slack measurement, infrared non-contact tachometer for independent RPM verification, and a portable chassis dynamometer for rear wheel horsepower measurement.

Before commencing the laboratory exercises, verify that the MoTeC i2 Pro installation includes the motorcycle-specific math channel library, which provides pre-built functions for calculating acceleration from GPS velocity differential, gear position inference from transmission ratio mapping, and slip ratio computation from wheel speed versus GPS ground speed. Confirm that the workspace file contains properly defined channel aliases: rename generic analog input labels to physically meaningful sensor descriptions such as "Throttle_Position_Percent" and "Rear_Shock_Travel_mm" to avoid ambiguity during multi-file comparison sessions. Establish a consistent file naming convention that encodes session date, track identifier, rider name, and setup configuration index, enabling rapid retrieval during post-session engineering debriefs. Load the reference lap file, defined as the single fastest complete lap from the dataset, and configure the workspace display to show engine RPM, throttle position, GPS speed, and rear wheel speed on a common time axis with synchronized cursor for simultaneous multi-channel inspection.

## Exercise 1: Telemetry Data Import & Driver Trace Correlation

The first exercise establishes the fundamental telemetry analysis workflow: importing logged data files into the i2 Pro environment, verifying sensor calibration accuracy, aligning multiple laps to a common distance base for direct comparison, and generating derived math channels that expose powertrain performance metrics not directly measurable by hardware sensors. This process transforms raw voltage readings and pulse counts into engineering units with physical meaning, enabling quantitative assessment of engine power delivery, clutch engagement consistency, and traction stability under acceleration.

Begin by launching MoTeC i2 Pro and creating a new workspace file dedicated to powertrain analysis. Navigate to the File menu and select "Open Log File," then browse to the directory containing the session telemetry data. MoTeC native LD file format imports directly with full channel metadata preservation, while third-party logger CSV exports require manual channel mapping through the import wizard. During CSV import, specify the timestamp column format, typically either Unix epoch seconds or elapsed time in fractional seconds since logger power-on. Map each CSV column header to a predefined i2 Pro channel name, ensuring correct assignment of sensor type, engineering units, and decimal precision. For engine RPM, specify units of revolutions per minute with zero decimal places and a valid range of 0 to 18000 RPM for inline-four sportbike powerplants. Throttle position requires percentage units with one decimal place and a physical range of 0.0 to 100.0 percent, corresponding to the fully closed and wide-open throttle mechanical stops. GPS speed channels demand kilometers per hour or meters per second units with two decimal places, while wheel speed sensors output in RPM or angular velocity radians per second depending on encoder type.

Once the log file imports successfully, inspect the raw data for sensor malfunction indicators: stuck channels that report constant values despite dynamic vehicle motion, out-of-range spikes caused by electrical noise or connector intermittency, and dropout periods where the logger lost sensor signal continuity. The i2 Pro channel properties dialog displays minimum, maximum, and average values for the entire session, providing rapid sanity checking against known physical limits. An engine RPM channel reporting a maximum value of 24000 RPM on a motorcycle with a factory rev limiter set to 14500 RPM indicates sensor miscalibration or incorrect pulses-per-revolution configuration in the logger setup. Throttle position channels exhibiting negative values or exceeding 100 percent reveal zero offset errors or scaling factor mistakes in the analog-to-digital converter calibration table. GPS speed channels showing sustained velocities above the motorcycle's theoretical top speed, calculated from maximum engine RPM and overall gear ratio, point to GPS signal multipath corruption or Doppler velocity processing errors.

After validating raw channel integrity, segment the continuous data log into individual lap instances using the lap beacon trigger channel. The beacon trigger activates when the motorcycle passes a physical transponder loop embedded in the track surface at the start-finish line, generating a digital pulse that timestamps the exact moment of lap completion. Configure i2 Pro to auto-detect lap boundaries by setting a trigger threshold on the beacon channel, typically a rising edge from low to high logic level. The software divides the session into discrete laps, each represented as a separate data object in the workspace file manager. Examine the lap time report to identify the reference lap: the single fastest complete lap with clean sector times and no yellow flag interruptions. Flag this lap as the baseline for all subsequent comparison operations by right-clicking the lap entry and selecting "Set as Reference Lap." The reference lap establishes the distance-based alignment datum, allowing overlay plotting of multiple laps with automatic track position synchronization rather than time-based alignment which suffers from phase shift due to varying lap times.

With lap segmentation complete, construct the first set of derived math channels to extract powertrain-specific performance metrics from the raw sensor data. Create a new math channel named "Acceleration_Longitudinal_G" that computes the rate of change of GPS ground speed with respect to time, scaled to gravitational acceleration units. The i2 Pro expression syntax for this calculation reads: `derivative([GPS_Speed_mps]) / 9.81`, where the derivative function calculates the first-order differential of GPS speed measured in meters per second, divided by Earth's standard gravitational acceleration constant to yield acceleration in G units. Apply a low-pass digital filter with a cutoff frequency of 5 Hz to suppress GPS noise and prevent spurious acceleration spikes from corrupting the trace. This filtered acceleration channel directly quantifies the motorcycle's longitudinal traction efficiency during corner exit, revealing whether the rear tire operates within its adhesion limit or breaks loose into wheelspin.

Next, synthesize a gear position inference channel that reverse-engineers the current transmission gear from the ratio between engine RPM and rear wheel speed. This calculation requires knowledge of the motorcycle's final drive ratio, typically expressed as the ratio of rear sprocket teeth count to front sprocket teeth count, and the individual gearbox ratios for each of the six forward gears. Define a math channel named "Gear_Position_Calculated" with the following expression: `gearCalc([Engine_RPM], [Rear_Wheel_Speed_RPM], [Final_Drive_Ratio], [Gear_Ratio_Array])`, substituting actual numerical values for final drive ratio and a six-element array containing first through sixth gear ratios obtained from the motorcycle manufacturer's technical service manual. The `gearCalc` function compares the instantaneous RPM ratio against each transmission gear ratio, accounting for tire rolling radius and final drive sprocket tooth counts, then returns an integer from 1 to 6 indicating the engaged gear. This synthetic channel enables automatic identification of upshift and downshift events, facilitating gear-specific power delivery analysis without requiring a physical gearbox position sensor.

Construct an additional math channel to quantify rear wheel slip ratio, defined as the percentage difference between rear wheel rotational speed and GPS ground speed. Name this channel "Slip_Ratio_Rear_Percent" and implement the expression: `100 * ([Rear_Wheel_Speed_mps] - [GPS_Speed_mps]) / [GPS_Speed_mps]`, where both wheel speed and GPS speed have been converted to common units of meters per second through appropriate scaling factors accounting for tire rolling circumference. Positive slip ratio values indicate the rear wheel spins faster than the motorcycle's actual ground speed, signifying traction loss and wheelspin. Negative slip ratio occurs during engine braking or rear wheel lock under combined deceleration and downshift, though this condition primarily concerns corner entry braking analysis rather than powertrain performance evaluation. During optimal acceleration, the slip ratio should remain between 0 and 5 percent, corresponding to the peak of the tire longitudinal force curve where adhesive friction generates maximum forward thrust before transitioning into sliding friction and catastrophic wheelspin.

To validate the accuracy of derived math channels, perform a correlation cross-check against known physical constraints. Display the gear position channel alongside engine RPM and GPS speed on a synchronized time plot, then zoom into a corner exit sequence where the rider executes a third-to-fourth gear upshift. At the precise moment the gear position channel transitions from 3 to 4, the engine RPM should exhibit a sudden drop corresponding to the step change in transmission ratio, while GPS speed continues increasing smoothly as vehicle momentum carries the motorcycle forward despite temporary interruption of drive torque during clutch disengagement. Calculate the expected RPM drop using the formula: `RPM_drop = RPM_before * (1 - Ratio_4th / Ratio_3rd)`, then compare against the measured RPM differential in the telemetry trace. Agreement within 5 percent validates correct gear ratio input parameters and confirms the gearCalc function operates as intended.

Similarly, verify slip ratio channel validity by examining a corner exit where the rider applies full throttle on a high-traction asphalt surface. The slip ratio should rise smoothly from zero to approximately 3 percent as engine torque transfers through the rear tire contact patch, then stabilize at this value as the tire operates at peak longitudinal force coefficient. If the slip ratio trace shows sustained values above 10 percent or exhibits oscillatory behavior with rapid fluctuations between positive and negative values, investigate potential causes: incorrect tire rolling radius in the calculation expression, GPS velocity lag due to insufficient update rate or multipath signal degradation, or physical wheelspin caused by insufficient rear suspension compression damping allowing the tire to break traction momentarily as suspension extends over track surface undulations.

Complete the first exercise by generating a comprehensive overlay plot comparing three distinct laps: the reference lap, a lap with intentionally conservative throttle application for baseline traction margin assessment, and a lap where the rider experimented with aggressive throttle timing to explore the traction limit. Configure the plot to display throttle position, engine RPM, GPS speed, and rear wheel slip ratio on a common distance axis spanning the longest straight section of the circuit. Adjust the vertical axis scaling to maximize trace separation without clipping, and apply distinct color coding to each lap for visual disambiguation: reference lap in blue, conservative lap in green, and aggressive lap in red. Export this plot as a high-resolution PNG image for inclusion in the post-session engineering report, annotating critical features such as the distance coordinate where the aggressive lap slip ratio exceeds 8 percent indicating incipient wheelspin, and the corresponding GPS speed deficit relative to the reference lap demonstrating the performance penalty of traction loss.

## Exercise 2: Damper Velocity Histogram Tuning & Anti-Roll Bar Optimization

The second exercise transitions from pure telemetry observation to actionable suspension tuning informed by powertrain-induced chassis dynamics. Motorcycle rear suspension operates under severe asymmetric loading during acceleration events: chain drive torque generates anti-squat geometry effects that extend the rear shock absorber against spring preload, while simultaneous weight transfer to the rear axle compresses the suspension under increased vertical load. The shock absorber damping characteristics, quantified through velocity-dependent force curves and adjusted via external compression and rebound damping clickers, directly influence rear tire contact patch load variation and thus traction stability under power. Inadequate compression damping permits excessive suspension velocity during rapid throttle application, allowing the tire to momentarily unload and break traction. Excessive rebound damping prevents the suspension from extending smoothly as weight transfers rearward, causing the chassis to pack down into the travel range and reducing available suspension compliance for mid-corner bumps.

The damper velocity histogram provides the empirical foundation for suspension tuning decisions by quantifying the statistical distribution of shock absorber shaft velocities encountered during actual track operation. Unlike static sag measurements or simplified quarter-car kinematic models, the histogram captures the real-world velocity spectrum the damper must control, including high-frequency bump absorption, low-frequency chassis pitch oscillation, and transient spikes from kerb strikes and track surface irregularities. The histogram shape reveals whether the current damping settings appropriately match the velocity distribution: a histogram concentrated at low velocities below 0.5 meters per second indicates the motorcycle operates primarily in the low-speed damping regime controlled by clicker adjustments, while significant histogram content extending beyond 1.0 meter per second demonstrates high-velocity events requiring attention to the internal shim stack configuration inaccessible without damper disassembly.

Commence the exercise by creating a damper velocity math channel from the rear shock absorber position sensor data. The position sensor, typically a linear potentiometer mounted to the shock body with a connecting rod to the suspension linkage, outputs a voltage proportional to shock shaft extension. The logger analog input conditioning scales this voltage to millimeters of travel, with zero corresponding to full compression and maximum value representing full extension with the motorcycle suspended on the service stand. Define a new math channel named "Rear_Damper_Velocity_mps" using the derivative expression: `derivative([Rear_Shock_Position_mm]) / 1000`, dividing by 1000 to convert millimeters per second to meters per second for dimensional consistency with standard damping force curves. Apply a 20 Hz low-pass Butterworth filter to remove sensor noise and spurious velocity spikes from quantization error in the analog-to-digital converter, while preserving the genuine high-frequency content from rapid suspension motion over sharp-edged bumps.

Generate the damper velocity histogram by selecting the newly created velocity channel and invoking the i2 Pro histogram function from the math channel analysis menu. Configure the histogram with velocity bins spanning from negative 2.0 meters per second (compression direction) to positive 2.0 meters per second (rebound direction), using a bin width of 0.1 meters per second for adequate resolution without excessive granularity. Restrict the histogram calculation to the data range corresponding to the reference lap's longest straight section, isolating the powertrain-dominated acceleration phase from corner entry braking events where suspension dynamics follow a different operating regime. The resulting histogram displays a frequency distribution showing the cumulative time or percentage of samples the damper operates within each velocity bin.

Interpret the histogram shape to diagnose suspension tuning deficiencies. An ideal histogram for acceleration events exhibits a primary peak centered near zero velocity with smooth exponential decay toward higher absolute velocities in both compression and rebound directions. This distribution indicates the suspension operates close to equilibrium ride height with controlled excursions into the damping range. A histogram with a pronounced secondary peak in the compression direction at velocities around negative 1.0 meter per second suggests the suspension encounters a repetitive high-velocity compression event, likely the initial squat transient when the rider first applies throttle exiting a slow corner. If this secondary peak contains more than 10 percent of the total sample population, the compression damping setting is insufficient to control the squat rate, allowing the suspension to blow through its travel too rapidly and potentially bottom against the mechanical stop.

Conversely, a histogram skewed toward positive rebound velocities with a long tail extending beyond 1.5 meters per second indicates excessive rebound damping resistance prevents the shock from extending smoothly during the weight transfer phase. This condition causes the rear suspension to pack down progressively over consecutive corner exits, reducing available travel for subsequent bumps and degrading tire contact patch load stability. The histogram tail also reveals the maximum velocities the damper must handle: if the distribution extends beyond 2.0 meters per second in either direction, the shock absorber operates beyond the velocity range adequately controlled by external clicker adjustments, requiring revalving the internal shim stack to increase high-speed damping force capacity.

Translate histogram insights into concrete damping adjustment recommendations using the suspension tuner's empirical guideline: each click of compression damping adjustment alters the low-speed damping force by approximately 3 to 5 percent, while each rebound click modifies rebound force by a similar increment. If the histogram shows excessive compression velocity content indicating squat control deficiency, calculate the required damping force increase from the force-velocity curve published in the shock absorber manufacturer's technical data sheet. Locate the compression velocity bin containing the secondary peak, read the corresponding velocity value, then reference the damper dyno curve to determine the current damping force at that velocity. Increase the compression damping force by 15 to 20 percent to adequately control the squat event, then back-calculate the number of clicker adjustments required: `clicks_needed = (target_force_increase_percent / 4.0)`, rounding to the nearest integer click count.

Implement the damping change by rotating the compression damping adjuster clockwise by the calculated number of clicks, meticulously counting each detent position and verifying free rotation without binding. Record the original baseline setting in the setup sheet before making adjustments to permit rapid reversion if the change degrades performance. Return to the track and log a minimum of three flying laps with the updated compression damping setting, ensuring the rider maintains consistent throttle application timing and racing line to isolate the suspension variable from driving style variations. Import the new telemetry session into i2 Pro and regenerate the damper velocity histogram using the identical analysis parameters as the baseline session. Overlay the new histogram on the original histogram plot using transparency rendering to visualize the distribution shift.

Assess the effectiveness of the damping adjustment by comparing the before-and-after histogram shapes. A successful compression damping increase manifests as a reduction in the secondary peak amplitude at high compression velocities, with histogram mass redistributing toward lower velocities closer to the equilibrium position. Quantify the improvement by integrating the histogram area beyond a threshold velocity, for example calculating the percentage of samples exceeding 1.0 meter per second compression velocity before and after the damping change. A reduction of 30 to 50 percent in high-velocity sample count confirms the damping adjustment successfully controlled the squat transient without introducing excessive damping that slows suspension response to track surface inputs.

Complement the histogram analysis with direct inspection of the rear shock absorber position trace during a specific corner exit sequence. Display the shock position channel on a distance-based plot aligned to the reference lap's track map, zooming into a tight second-gear hairpin exit where squat control proves most critical. Mark the distance coordinate where the rider first applies measurable throttle exceeding 20 percent, then observe the suspension position trajectory over the following 50 meters as the motorcycle accelerates through third gear. The baseline trace with insufficient compression damping exhibits a rapid initial compression spike of 15 to 20 millimeters within the first 10 meters, followed by a slower rebound extension as weight transfers rearward. The optimized damping trace shows a smoother, more gradual compression progression limited to 10 millimeters maximum displacement, indicating the damper force successfully resists the squat impulse and maintains suspension geometry closer to optimal ride height throughout the acceleration phase.

Extend the damping optimization procedure to the rebound circuit by examining histogram content in the positive velocity range. If the histogram shows a pronounced tail extending beyond 1.0 meter per second rebound velocity, reduce the rebound damping by two to three clicks counterclockwise to permit faster shock extension during weight transfer. Exercise caution with rebound adjustments: insufficient rebound damping causes oscillatory suspension behavior where the shock extends too rapidly, overshoots equilibrium position, then compresses again in a lightly damped oscillation visible as a 2-3 Hz sinusoidal component in the position trace. Monitor the shock position channel on subsequent test laps for any evidence of oscillation, and if observed, immediately restore one click of rebound damping to increase energy dissipation and critically damp the suspension resonance.

Document the final optimized damping settings in the motorcycle setup matrix, a tabular record of all suspension parameters indexed by track identifier and environmental conditions. The setup matrix entry for rear shock damping includes compression clicker position counted from the full-soft (fully counterclockwise) reference position, rebound clicker position similarly referenced, spring preload measured in millimeters of free length compression, and static sag measured with the rider aboard in full racing leathers and fuel tank at half capacity. Annotate the setup matrix entry with qualitative rider feedback keywords such as "stable," "planted," "responsive," or warning flags like "harsh" or "packing" to provide experiential context that pure telemetry data cannot capture. Cross-reference the setup matrix with the damper velocity histogram plots stored in the session analysis folder, enabling rapid recall of the histogram shape associated with each damping configuration during future test sessions at the same circuit.

## Exercise 3: Tire Temperature Analysis & Wear Modeling

The third exercise investigates the thermal operating envelope of the rear tire, the critical interface through which engine torque transmits to the track surface and the primary traction-limiting factor in motorcycle powertrain performance. Tire compound friction coefficient exhibits strong temperature dependence: cold tire rubber below 60 degrees Celsius generates insufficient adhesive friction for safe cornering and aggressive acceleration, while overheated rubber exceeding 110 degrees Celsius experiences molecular breakdown and catastrophic traction loss. The tire's three-zone temperature profile—inner edge, center tread, and outer edge—provides diagnostic information about suspension camber settings, tire pressure optimization, and corner exit line selection. Systematic temperature measurement using an infrared pyrometer immediately after the completion of a flying lap, combined with telemetry-based thermal energy deposition modeling, enables the race engineer to tune tire pressure and adjust camber angle for optimal operating temperature at the traction limit.

Tire temperature measurement demands strict adherence to a standardized protocol to ensure repeatability and comparability across sessions. The rider completes a flying lap at full race pace, then immediately enters the pit lane at reduced speed, maintaining steady throttle to avoid thermal shock from rapid deceleration. The pit crew member stations at the designated hot tire measurement position with an infrared pyrometer and stopwatch. As the motorcycle comes to a controlled stop, the timer starts and the crew member has exactly 15 seconds to acquire temperature readings at six prescribed locations on the rear tire: inner edge at 30 degrees from the tire centerline, inner mid-tread at 15 degrees, center tread at 0 degrees, outer mid-tread at 15 degrees, outer edge at 30 degrees, and the tire sidewall for ambient reference. The pyrometer emissivity setting must match the tire compound: typically 0.95 for carbon-black reinforced racing slicks. Each measurement point receives a two-second integration period to average out thermal gradients from tread pattern grooves, and the temperature value is recorded vocally for transcription by a second crew member operating the data entry tablet.

Construct a tire temperature spreadsheet to organize and visualize the measurement data. Create column headers for lap number, lap time, ambient air temperature, track surface temperature measured via infrared thermometer aimed at the asphalt, and the six tire zone temperatures: TI_Inner, TI_InnerMid, TI_Center, TI_OuterMid, TI_Outer, and TI_Sidewall. Enter the measured values for the baseline reference lap, then calculate derived metrics to quantify temperature distribution characteristics. Define a "Temperature_Spread" column computing the difference between the hottest and coldest tread zone: `max(TI_Inner, TI_InnerMid, TI_Center, TI_OuterMid, TI_Outer) - min(TI_Inner, TI_InnerMid, TI_Center, TI_OuterMid, TI_Outer)`. An ideal temperature spread remains below 15 degrees Celsius, indicating uniform tread contact and efficient load distribution across the tire width. Excessive spread beyond 25 degrees reveals either incorrect tire pressure causing center-heavy or edge-heavy contact patch loading, or suspension camber misalignment concentrating cornering loads on one tire edge.

Calculate a "Camber_Balance_Index" to diagnose asymmetric camber-induced temperature gradients. This metric compares the inner and outer edge temperature differential: `Camber_Balance = (TI_Inner - TI_Outer) / TI_Center * 100`, yielding a percentage value indicating the degree of thermal asymmetry. Positive camber balance values signify the inner edge runs hotter than the outer edge, characteristic of insufficient negative camber allowing the tire to roll onto the outer shoulder during aggressive cornering. Negative camber balance indicates excessive negative camber forcing the tire to ride on the inner edge, reducing the effective contact patch width and compromising straight-line acceleration traction. Target a camber balance index within plus or minus 10 percent for balanced temperature distribution, adjusting rear suspension camber via eccentric axle spacers or swingarm pivot geometry modification to center the temperature profile.

Correlate tire temperature measurements with telemetry-derived traction metrics to establish causality between thermal state and performance. Display the rear wheel slip ratio channel on a distance-based plot synchronized to the temperature measurement lap, then annotate the plot with horizontal reference lines indicating the measured tire center tread temperature. Zoom into corner exit zones where the slip ratio exceeds 5 percent, signaling the tire operates at or beyond the peak of the friction curve. If these high slip ratio events occur when the tire temperature reads below 75 degrees Celsius, the root cause is insufficient thermal energy deposition to achieve optimal rubber compound activation temperature. Recommend extending the warm-up procedure by adding two additional formation laps with periodic hard acceleration bursts to build tire temperature before commencing the flying lap.

Conversely, if high slip ratio excursions coincide with tire temperatures exceeding 105 degrees Celsius, the tire operates in the thermal degradation regime where elevated temperature softens the rubber compound beyond the optimal window, reducing peak friction coefficient and increasing wear rate. Address overheating through tire pressure reduction: lowering cold inflation pressure by 1 psi reduces the tire's internal hysteresis-driven heat generation by approximately 3 degrees Celsius under sustained high-load operation. Implement pressure changes in 1 psi increments, measure temperatures after each adjustment, and iterate until the center tread temperature stabilizes within the target range of 85 to 95 degrees Celsius for DOT racing slick compounds or 75 to 85 degrees Celsius for DOT street-legal track day tires.

Develop a simplified thermal energy balance model to predict tire temperature evolution as a function of power dissipation from slip energy and convective cooling from airflow. The governing equation for tire temperature rate of change reads: `dT/dt = (P_slip - P_cool) / (m_tire * c_rubber)`, where `P_slip` represents the power dissipated through tire-to-road sliding friction, `P_cool` denotes the convective heat transfer rate to ambient air, `m_tire` is the tire mass, and `c_rubber` is the specific heat capacity of the rubber compound. Calculate slip power using telemetry channels: `P_slip = F_long * V_slip`, where longitudinal force `F_long` derives from the product of motorcycle mass, longitudinal acceleration, and slip velocity `V_slip` is the difference between rear wheel rotational speed and GPS ground speed. Estimate convective cooling power using the empirical correlation: `P_cool = h_conv * A_tire * (T_tire - T_ambient)`, with convective heat transfer coefficient `h_conv` approximately 60 W/m²K at typical motorcycle racing speeds and tire surface area `A_tire` of 0.08 square meters for a 190/55-17 rear tire.

Implement the thermal model in Python to simulate tire temperature trajectory over the course of a flying lap. Define constants for tire mass (5.5 kg including wheel rim contribution to thermal mass), rubber specific heat capacity (1800 J/kgK), and initial temperature equal to the measured pre-lap sidewall temperature. Import the telemetry CSV file containing GPS speed, rear wheel speed, and longitudinal acceleration channels sampled at 100 Hz. Iterate through each time step, calculate the instantaneous slip power and cooling power, numerically integrate the temperature rate equation using the Euler forward method with time step matching the telemetry sample interval, and accumulate the temperature change to generate a predicted tire temperature trace. Plot the simulated temperature alongside the measured post-lap pyrometer reading to validate model accuracy.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Tire thermal model constants
TIRE_MASS_KG = 5.5
RUBBER_SPECIFIC_HEAT_J_KG_K = 1800.0
CONVECTION_COEFF_W_M2_K = 60.0
TIRE_SURFACE_AREA_M2 = 0.08
AMBIENT_TEMP_C = 25.0
BIKE_MASS_KG = 180.0
TIRE_RADIUS_M = 0.305

# Load telemetry data
df_telem = pd.read_csv('session_telemetry_lap_reference.csv')
time_s = df_telem['Time_s'].values
gps_speed_mps = df_telem['GPS_Speed_mps'].values
rear_wheel_speed_rpm = df_telem['Rear_Wheel_Speed_RPM'].values
accel_long_g = df_telem['Accel_Long_G'].values

# Convert rear wheel speed to linear velocity
rear_wheel_speed_mps = rear_wheel_speed_rpm * (2.0 * np.pi * TIRE_RADIUS_M) / 60.0

# Calculate slip velocity
slip_velocity_mps = rear_wheel_speed_mps - gps_speed_mps

# Calculate longitudinal force from acceleration
force_long_n = BIKE_MASS_KG * accel_long_g * 9.81

# Initialize temperature array
tire_temp_c = np.zeros(len(time_s))
tire_temp_c[0] = 65.0  # Initial tire temperature from sidewall pyrometer

# Thermal simulation loop
for i in range(1, len(time_s)):
    dt = time_s[i] - time_s[i-1]
    
    # Slip power dissipation
    p_slip_w = force_long_n[i] * abs(slip_velocity_mps[i])
    
    # Convective cooling power
    p_cool_w = CONVECTION_COEFF_W_M2_K * TIRE_SURFACE_AREA_M2 * (tire_temp_c[i-1] - AMBIENT_TEMP_C)
    
    # Net heat rate
    q_net_w = p_slip_w - p_cool_w
    
    # Temperature rate of change
    dt_dt_k_s = q_net_w / (TIRE_MASS_KG * RUBBER_SPECIFIC_HEAT_J_KG_K)
    
    # Euler integration
    tire_temp_c[i] = tire_temp_c[i-1] + dt_dt_k_s * dt

# Plot results
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

ax1.plot(time_s, gps_speed_mps * 3.6, 'b-', label='GPS Speed')
ax1.plot(time_s, rear_wheel_speed_mps * 3.6, 'r--', label='Rear Wheel Speed')
ax1.set_ylabel('Speed (km/h)')
ax1.legend()
ax1.grid(True)

ax2.plot(time_s, slip_velocity_mps, 'g-', linewidth=1.5)
ax2.set_ylabel('Slip Velocity (m/s)')
ax2.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
ax2.grid(True)

ax3.plot(time_s, tire_temp_c, 'r-', linewidth=2, label='Simulated Tire Temp')
ax3.axhline(y=85, color='g', linestyle='--', label='Target Min Temp')
ax3.axhline(y=95, color='orange', linestyle='--', label='Target Max Temp')
ax3.set_xlabel('Time (seconds)')
ax3.set_ylabel('Tire Temperature (°C)')
ax3.legend()
ax3.grid(True)

plt.tight_layout()
plt.savefig('tire_thermal_analysis_lap_reference.png', dpi=300)
plt.show()

# Output final predicted temperature
print(f"Simulated end-of-lap tire temperature: {tire_temp_c[-1]:.1f} °C")
print(f"Measured post-lap pyrometer reading: [ENTER_MEASURED_VALUE] °C")
print(f"Prediction error: {abs(tire_temp_c[-1] - [ENTER_MEASURED_VALUE]):.1f} °C")
```

Refine the thermal model by incorporating additional physical effects for improved prediction accuracy. Add a radiation heat transfer term to account for infrared emission from the hot tire surface: `P_rad = epsilon * sigma * A_tire * (T_tire**4 - T_ambient**4)`, where epsilon is the tire emissivity (0.95), sigma is the Stefan-Boltzmann constant (5.67e-8 W/m²K⁴), and temperatures are expressed in Kelvin. Include a conduction heat transfer path from the tire through the wheel rim to the brake rotor acting as a heat sink: `P_cond = k_eff * (T_tire - T_rim) / L_thickness`, with effective thermal conductivity `k_eff` approximately 0.3 W/mK and tire sidewall thickness `L_thickness` of 8 millimeters. These refinements typically improve model accuracy from ±10 degrees Celsius to ±5 degrees Celsius, sufficient for predictive optimization of tire pressure and camber settings without iterative on-track testing.

Apply the validated thermal model to predict the effect of tire pressure changes on operating temperature. Reducing cold inflation pressure from 32 psi to 31 psi decreases tire structural stiffness, increasing the internal hysteresis energy dissipation and contact patch deformation. Model this effect by scaling the slip power term by a pressure-dependent factor: `P_slip_adjusted = P_slip * (1 + 0.03 * (P_ref - P_actual))`, where `P_ref` is the baseline pressure and `P_actual` is the proposed new pressure. Re-run the thermal simulation with the adjusted slip power, observe the predicted temperature change, and verify against actual pyrometer measurements after implementing the pressure change on track. This predictive capability enables pre-session setup optimization, reducing the number of on-track test laps required to converge on optimal tire parameters and preserving tire life for race distance simulation runs.

Conclude the tire analysis exercise by constructing a comprehensive tire wear model that predicts tread depth degradation as a function of cumulative sliding distance and average operating temperature. Tire wear rate follows an Arrhenius temperature dependence: `wear_rate = A * exp(-E_a / (R * T))`, where `A` is a compound-specific pre-exponential factor, `E_a` is the activation energy for rubber abrasion, `R` is the universal gas constant, and `T` is the absolute temperature in Kelvin. Integrate the wear rate over the lap distance weighted by the local slip ratio to accumulate total tread loss. Compare the predicted wear against physical tread depth measurements using a digital tire depth gauge at four circumferential locations around the tire, averaging the readings to obtain mean tread depth. A well-calibrated wear model predicts tread depth loss within 0.2 millimeters over a five-lap stint, enabling accurate race strategy planning for multi-stint endurance events where tire degradation dictates pit stop timing.

## Race Engineering Diagnostic Cheat Sheet & Setup Matrix

The final section consolidates the empirical knowledge developed through the three laboratory exercises into a rapid diagnostic reference guide and a structured setup parameter matrix. The diagnostic cheat sheet provides symptom-to-root-cause mapping for common powertrain-related performance deficits observed in telemetry data, enabling the trackside engineer to quickly identify corrective actions during time-limited practice sessions. The setup matrix documents the complete baseline configuration of the motorcycle's powertrain and chassis parameters, serving as both a known-good reference state for troubleshooting and a version-controlled record of setup evolution across multiple test sessions and racing circuits.

### Powertrain Diagnostic Cheat Sheet

**Symptom:** Rear wheel slip ratio exceeds 8 percent sustained for more than 0.5 seconds during corner exit, accompanied by GPS speed loss relative to reference lap.

**Root Cause Candidates:**
1. Insufficient rear tire operating temperature below 75°C: Extend warm-up procedure, reduce tire pressure by 1 psi to increase internal heat generation.
2. Excessive engine torque delivery rate: Retard throttle map progression in ECU calibration, reducing rate of change from 20% to 50% throttle.
3. Inadequate rear suspension compression damping: Increase compression clicker setting by 2-3 clicks to control squat-induced weight transfer spike.
4. Worn rear tire beyond 50% tread life: Replace with fresh tire, verify tread depth minimum 3.0 mm at center.

**Verification Test:** Log three flying laps with corrective action applied, overlay slip ratio channel against baseline reference lap, confirm peak slip ratio reduced below 6 percent threshold.

---

**Symptom:** Engine RPM exhibits 300-500 RPM oscillation at constant throttle position on long straightaway, visible as sinusoidal modulation in RPM trace.

**Root Cause Candidates:**
1. Excessive driveline lash: Inspect chain slack, adjust to 25-30 mm vertical deflection at mid-span. Check sprocket teeth for hooking wear.
2. Insufficient drivetrain damping: Install rubber-mounted countershaft sprocket cushion or increase rear shock compression damping to dissipate oscillation energy.
3. ECU fuel injection instability: Review lambda sensor feedback loop gains, verify closed-loop fuel trim authority limited to ±5 percent.

**Verification Test:** Measure chain tension with calibrated spring scale, apply 10 kg force at mid-span, verify deflection within specification. Re-log data, confirm RPM oscillation amplitude reduced below 200 RPM.

---

**Symptom:** Gear position calculated channel shows spurious transitions (e.g., momentary shift from 4th to 6th gear, then immediate return to 4th) not corresponding to rider shift action.

**Root Cause Candidates:**
1. Incorrect gear ratio input parameters in telemetry math channel expression: Verify transmission ratios against service manual specifications.
2. Rear wheel speed sensor dropout or noise: Inspect sensor air gap, clean magnetic pickup face, verify secure connector mating.
3. GPS velocity lag during high longitudinal acceleration: Replace GPS velocity with integrated accelerometer-based speed calculation for improved transient response.

**Verification Test:** Manually annotate actual shift points via video synchronization, compare against calculated gear position channel, adjust gear ratio parameters until agreement within one gear across all shift events.

---

**Symptom:** Rear shock absorber velocity histogram shows secondary peak at high compression velocity (exceeding 1.2 m/s) occupying more than 15 percent of sample population.

**Root Cause Candidates:**
1. Insufficient compression damping force: Increase compression clicker by 3-4 clicks to resist squat transient.
2. Excessive chain torque anti-squat geometry: Reduce anti-squat percentage by lowering swingarm pivot or raising countershaft sprocket height.
3. Rider throttle application technique too aggressive: Review onboard video, coach rider to modulate throttle more progressively over initial 10 meters of corner exit.

**Verification Test:** Implement compression damping increase, regenerate histogram, verify secondary peak amplitude reduced by minimum 30 percent or peak velocity shifts below 1.0 m/s threshold.

---

**Symptom:** Tire temperature measurement shows center tread 20°C hotter than inner and outer edges, with temperature spread exceeding 25°C.

**Root Cause Candidates:**
1. Excessive tire pressure causing center-biased contact patch: Reduce cold pressure by 2 psi, re-measure temperature distribution.
2. Insufficient cornering load transfer due to conservative riding: Verify with lateral acceleration telemetry, confirm peak lateral G exceeds 1.4 G on high-speed corners.
3. Incorrect tire compound selection for track surface characteristics: Consult tire manufacturer hot pressure recommendation chart, verify pressure within specified range.

**Verification Test:** Adjust pressure, complete flying lap, measure temperatures within 15 seconds of pit entry, confirm temperature spread reduced below 20°C and center-to-edge differential less than 10°C.

---

### Motorcycle Setup Matrix Template

| Parameter Category | Parameter Name | Unit | Baseline Value | Test Session 1 | Test Session 2 | Notes |
|-------------------|----------------|------|----------------|----------------|----------------|-------|
| **Powertrain** | Engine ECU Map | - | Map 3 (Wet) | Map 1 (Dry) | Map 1 (Dry) | Dry map provides 8% more peak torque |
| | Throttle Response Mode | - | Mode B (Linear) | Mode B | Mode A (Aggressive) | Mode A tested for qualifying |
| | Final Drive Ratio | - | 42T/15T (2.80) | 42T/15T | 43T/15T (2.87) | Ratio increase for acceleration priority |
| | Chain Slack | mm | 28 | 28 | 30 | Decreased slack to reduce driveline oscillation |
| **Rear Suspension** | Spring Preload | mm | 8.0 | 8.0 | 9.0 | Added preload for heavier rider |
| | Compression Damping | clicks from soft | 12 | 14 | 14 | Two clicks added after histogram analysis |
| | Rebound Damping | clicks from soft | 10 | 10 | 11 | One click added to control extension rate |
| | Static Sag (rider aboard) | mm | 32 | 32 | 30 | Reduced via preload increase |
| | Ride Height (swingarm angle) | degrees | 4.2 | 4.2 | 4.5 | Raised rear via shock length adjustment |
| **Rear Tire** | Cold Pressure | psi | 32.0 | 31.0 | 30.5 | Pressure reduction for temperature control |
| | Hot Pressure (post-lap) | psi | 34.5 | 33.8 | 33.2 | Target hot pressure 33-34 psi range |
| | Tire Compound | - | Dunlop N-Tec Slick | Dunlop N-Tec | Pirelli Diablo Supercorsa | Compound change for cooler conditions |
| | Measured Temp (Center) | °C | 92 | 88 | 86 | Temperature optimization via pressure |
| | Measured Temp (Inner) | °C | 85 | 82 | 84 | Improved balance after camber adjustment |
| | Measured Temp (Outer) | °C | 88 | 86 | 85 | Outer edge cooling indicates better camber |
| | Camber Angle | degrees | -1.8 | -1.8 | -2.1 | Increased negative camber via eccentric |
| **Data Acquisition** | Logger Sample Rate | Hz | 100 | 100 | 100 | Maintain 100 Hz for damper velocity capture |
| | GPS Update Rate | Hz | 10 | 10 | 20 | Upgraded GPS for improved velocity accuracy |

**Setup Matrix Usage Protocol:** Before each test session, photograph the current setup matrix entry and distribute to the pit crew and rider. After implementing any parameter change, immediately update the corresponding matrix cell with the new value and timestamp. At the conclusion of the session, append a qualitative performance assessment in the Notes column, incorporating both telemetry-derived metrics (e.g., "lap time improved 0.3 seconds") and rider subjective feedback (e.g., "rear felt more planted through Turn 7"). Archive the completed setup matrix with associated telemetry files and tire temperature spreadsheets in a version-controlled repository indexed by date, track name, and session type (practice, qualifying, race).

The setup matrix enables systematic A-B comparison testing by isolating single-variable changes between successive test sessions. When investigating a performance deficit, revert all parameters to the last known-good configuration documented in the matrix, then incrementally reintroduce changes one at a time while monitoring telemetry for causality. This disciplined approach prevents compounding errors where multiple simultaneous changes obscure the root cause of performance variation, accelerating the convergence toward an optimized setup tailored to the specific combination of circuit layout, ambient conditions, tire compound, and rider skill characteristics.
