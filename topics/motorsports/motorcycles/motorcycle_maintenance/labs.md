# Operational Verification Labs: Motorcycle Maintenance

## Objective & Telemetry Environment Setup

The modern race motorcycle exists as a tightly coupled electromechanical system where suspension kinematics, tire thermal dynamics, engine calibration maps, and rider biomechanical input converge into a single performance envelope. Unlike four-wheel platforms where aerodynamic downforce and lateral load transfer dominate the engineering conversation, the single-track motorcycle operates within a fundamentally different physics regime. The rider's body position directly influences the center of gravity location, the gyroscopic precession torque from the rotating front wheel initiates lean angle through countersteering input, and the tire contact patch operates simultaneously in camber thrust generation and longitudinal traction delivery. This laboratory sequence treats the motorcycle not as a collection of isolated subsystems but as an integrated dynamic platform requiring continuous closed-loop analysis between telemetry data acquisition, mechanical setup iteration, and track validation.

The telemetry environment for motorcycle race engineering centers on high-frequency data acquisition systems capturing suspension travel, wheel speed differential, throttle position sensor voltage, brake line hydraulic pressure, chassis inertial measurement unit acceleration vectors, and GPS-derived velocity and trajectory curvature. The industry standard MoTeC ADL3 or Aim MXG 1.2 dash loggers sample these channels at rates between 10 Hz for slow-moving sensors like coolant temperature and 1000 Hz for critical dynamic channels such as suspension potentiometer displacement and brake pressure transducers. The telemetry file format typically exports as CSV with timestamped columnar data, though MoTeC's proprietary LD file format preserves higher metadata fidelity including GPS track mapping, lap beacon triggers, and calibrated engineering unit conversions. For this laboratory sequence, we assume access to MoTeC i2 Pro analysis software running on Windows 10 or later, with Python 3.10+ and MATLAB R2023a available for custom signal processing and parametric sweep simulation.

The physical workshop environment requires a paddock-grade suspension tuning station equipped with a calibrated damper dyno for force-velocity curve measurement, a digital tire pyrometer with three-zone bead temperature readout capability, a precision low-friction suspension travel measurement fixture, and a corner weight scale set capable of resolving individual wheel loads to within 0.5 kg precision. The data analysis workflow begins with telemetry import from the track session, proceeds through driver trace comparison and anomaly identification, advances into suspension histogram analysis revealing damper velocity distribution and bottoming events, and culminates in tire thermal mapping exposing contact patch load distribution asymmetry. Each exercise in this laboratory guide operates on authentic telemetry data extracted from a 600cc supersport motorcycle competing in club-level sprint racing, with lap times in the 1:32-1:34 range on a 2.4 km road course featuring twelve corners and two high-speed sections exceeding 240 km/h.

Before beginning the exercises, establish the Python environment with the following package installations. The `pandas` library handles CSV telemetry import and time-series manipulation, `numpy` provides vectorized mathematical operations for filtering and differentiation, `matplotlib` generates publication-quality plots with dual-axis capability, and `scipy` supplies signal processing filters including Butterworth low-pass for noise rejection in potentiometer channels. Install these dependencies through the pip package manager with the command `pip install pandas numpy matplotlib scipy`. For MATLAB users, ensure the Signal Processing Toolbox and Curve Fitting Toolbox are licensed and installed, as these provide critical functions for damper force reconstruction from velocity and displacement measurements. The MoTeC i2 Pro software requires a valid license dongle and installation of the latest i2 Pro 1.2 release, available through the MoTeC customer portal. Configure i2 Pro to display time-aligned multi-channel traces with synchronous cursor tracking, enabling direct visual correlation between throttle input, suspension compression events, and tire slip ratio excursions.

The telemetry CSV file structure follows a header row defining channel names, followed by data rows sampled at the logger's acquisition rate. Critical channels for motorcycle analysis include `Time` in seconds, `Speed` in km/h derived from GPS or wheel speed sensors, `ThrottlePos` as a 0-100% normalized value, `BrakePressureFront` and `BrakePressureRear` in bar, `SuspensionTravelFront` and `SuspensionTravelRear` in millimeters with full compression defined as maximum positive displacement, `LongitudinalAccel` and `LateralAccel` in g-force, `SteeringAngle` in degrees, and `EngineRPM` in revolutions per minute. Additional derived channels such as `LapTime`, `LapBeacon`, and `TrackPosition` enable segmented analysis by corner or sector. The data acquisition system timestamps each sample with microsecond precision, allowing reconstruction of transient events such as front fork compression spikes during threshold braking or rear suspension rebound damping oscillation under hard acceleration out of slow corners.

The setup matrix maintained throughout these exercises records the current chassis configuration including fork spring rate in N/mm, fork oil weight in SAE viscosity grade, fork compression and rebound damping clicks from full soft, rear shock spring rate in N/mm, rear shock preload in millimeters of threaded collar adjustment, rear shock compression and rebound damping clicks from full soft, tire compound selection for front and rear, tire cold inflation pressure in kPa, and static ride height measurements at front axle and rear axle. Each telemetry session annotates these parameters in the metadata, enabling correlation between setup changes and on-track performance deltas. The laboratory workflow demands disciplined documentation of every mechanical adjustment, as the multi-dimensional setup space for motorcycle suspension involves nonlinear coupling between preload, ride height, damping force, and dynamic wheel load variation.

The following exercises progress from fundamental telemetry data import and driver input analysis through advanced damper tuning via velocity histogram decomposition and culminate in tire thermal modeling exposing contact patch pressure distribution. Each exercise provides complete executable code, explicit mechanical procedures, and quantitative success criteria. The practitioner should execute these exercises sequentially, as later stages depend on insights and processed data from earlier steps. The laboratory concludes with a diagnostic cheat sheet consolidating common telemetry anomalies, their mechanical root causes, and corrective suspension adjustments.

---

## Exercise 1: Telemetry Data Import & Driver Trace Correlation

The foundation of data-driven motorcycle setup optimization begins with importing raw telemetry logs, synchronizing multiple channels to a common time base, and overlaying driver input traces against vehicle response signals. This exercise establishes the Python workflow for CSV telemetry ingestion, applies time-domain filtering to reject sensor noise, and generates multi-axis plots revealing the causal relationship between throttle application, brake pressure modulation, and suspension displacement transients. The practitioner will identify characteristic rider input signatures including threshold braking events, trail braking release profiles, and mid-corner throttle roll-on behavior, then correlate these inputs with suspension travel excursions and longitudinal acceleration pulses.

Begin by acquiring a telemetry CSV file from a logged track session. For this exercise, assume the file `session_2024_11_15_race1.csv` contains six laps of data sampled at 100 Hz. Place this file in a working directory accessible to the Python script. The CSV structure includes a single header row with column names followed by numeric data rows. Load the file using the `pandas` library, which automatically infers column types and constructs a DataFrame object enabling efficient time-series operations. The following Python script imports the telemetry data, extracts key channels, and applies a low-pass Butterworth filter to smooth suspension displacement signals corrupted by potentiometer electrical noise.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# Import telemetry CSV with automatic header detection
telemetry = pd.read_csv('session_2024_11_15_race1.csv')

# Extract critical channels into numpy arrays for vectorized operations
time = telemetry['Time'].values
speed = telemetry['Speed'].values
throttle = telemetry['ThrottlePos'].values
brake_front = telemetry['BrakePressureFront'].values
brake_rear = telemetry['BrakePressureRear'].values
susp_front = telemetry['SuspensionTravelFront'].values
susp_rear = telemetry['SuspensionTravelRear'].values
accel_long = telemetry['LongitudinalAccel'].values
accel_lat = telemetry['LateralAccel'].values

# Define 4th-order Butterworth low-pass filter at 10 Hz cutoff
# Sampling rate is 100 Hz, Nyquist frequency is 50 Hz
fs = 100.0
cutoff = 10.0
nyquist = 0.5 * fs
normal_cutoff = cutoff / nyquist
b, a = butter(4, normal_cutoff, btype='low', analog=False)

# Apply zero-phase filtering to suspension channels
susp_front_filt = filtfilt(b, a, susp_front)
susp_rear_filt = filtfilt(b, a, susp_rear)

# Compute suspension velocity via numerical differentiation
dt = np.diff(time)
susp_front_vel = np.gradient(susp_front_filt, time)
susp_rear_vel = np.gradient(susp_rear_filt, time)

print(f"Telemetry session duration: {time[-1]:.1f} seconds")
print(f"Total samples acquired: {len(time)}")
print(f"Maximum front suspension travel: {np.max(susp_front_filt):.1f} mm")
print(f"Maximum rear suspension travel: {np.max(susp_rear_filt):.1f} mm")
```

The Butterworth filter configuration employs a 10 Hz cutoff frequency selected to preserve suspension displacement transients during braking and cornering events while attenuating high-frequency electrical noise from the linear potentiometer wiper contact. The fourth-order filter provides a steep roll-off characteristic, delivering 80 dB/decade attenuation beyond the cutoff frequency. The `filtfilt` function applies the filter in both forward and reverse directions, canceling phase distortion that would otherwise shift suspension displacement events relative to the throttle and brake input timestamps. This zero-phase filtering ensures that peak front fork compression aligns precisely with peak brake pressure in the time domain, a critical requirement for diagnosing brake dive characteristics and fork compression damping adequacy.

The numerical differentiation of suspension displacement to compute suspension velocity employs the `numpy.gradient` function, which implements second-order accurate central differences in the interior of the data array and first-order forward or backward differences at the boundaries. Suspension velocity in mm/s directly correlates with damper force through the damper's force-velocity characteristic curve, typically exhibiting an asymmetric profile with higher rebound damping force than compression damping force at equivalent velocities. High-magnitude suspension velocities indicate transient loading events such as curb strike impacts or aggressive brake application, while sustained moderate velocities reveal steady-state cornering compression or acceleration squat.

Generate a comprehensive driver trace correlation plot overlaying throttle position, brake pressure, suspension travel, and longitudinal acceleration across a single representative lap. This visualization exposes the temporal coupling between rider input and chassis response, revealing the dynamic interplay between throttle modulation, weight transfer, and suspension kinematics. The following script isolates lap three from the telemetry session, normalizes the time axis to lap time in seconds, and constructs a four-panel stacked plot with shared time axis synchronization.

```python
# Extract lap beacon events to isolate individual laps
lap_beacon = telemetry['LapBeacon'].values
lap_starts = np.where(np.diff(lap_beacon) > 0.5)[0] + 1
lap_starts = np.insert(lap_starts, 0, 0)

# Isolate lap 3 data (index 2 in zero-based indexing)
lap_idx_start = lap_starts[2]
lap_idx_end = lap_starts[3] if len(lap_starts) > 3 else len(time)

time_lap = time[lap_idx_start:lap_idx_end] - time[lap_idx_start]
speed_lap = speed[lap_idx_start:lap_idx_end]
throttle_lap = throttle[lap_idx_start:lap_idx_end]
brake_front_lap = brake_front[lap_idx_start:lap_idx_end]
susp_front_lap = susp_front_filt[lap_idx_start:lap_idx_end]
susp_rear_lap = susp_rear_filt[lap_idx_start:lap_idx_end]
accel_long_lap = accel_long[lap_idx_start:lap_idx_end]

# Construct four-panel stacked plot with shared time axis
fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

# Panel 1: Throttle position and vehicle speed
ax1 = axes[0]
ax1_twin = ax1.twinx()
ax1.plot(time_lap, throttle_lap, 'g-', linewidth=1.5, label='Throttle Position (%)')
ax1_twin.plot(time_lap, speed_lap, 'b-', linewidth=1.5, label='Speed (km/h)')
ax1.set_ylabel('Throttle Position (%)', color='g', fontsize=11)
ax1_twin.set_ylabel('Speed (km/h)', color='b', fontsize=11)
ax1.tick_params(axis='y', labelcolor='g')
ax1_twin.tick_params(axis='y', labelcolor='b')
ax1.set_ylim([0, 105])
ax1_twin.set_ylim([0, 260])
ax1.grid(True, alpha=0.3)
ax1.set_title('Driver Trace Correlation: Lap 3', fontsize=13, fontweight='bold')

# Panel 2: Brake pressure front
ax2 = axes[1]
ax2.plot(time_lap, brake_front_lap, 'r-', linewidth=1.5, label='Front Brake Pressure (bar)')
ax2.set_ylabel('Front Brake Pressure (bar)', color='r', fontsize=11)
ax2.tick_params(axis='y', labelcolor='r')
ax2.set_ylim([0, np.max(brake_front_lap) * 1.1])
ax2.grid(True, alpha=0.3)

# Panel 3: Suspension travel front and rear
ax3 = axes[2]
ax3.plot(time_lap, susp_front_lap, 'orange', linewidth=1.5, label='Front Suspension Travel (mm)')
ax3.plot(time_lap, susp_rear_lap, 'purple', linewidth=1.5, label='Rear Suspension Travel (mm)')
ax3.set_ylabel('Suspension Travel (mm)', fontsize=11)
ax3.legend(loc='upper right', fontsize=9)
ax3.set_ylim([0, np.max([np.max(susp_front_lap), np.max(susp_rear_lap)]) * 1.1])
ax3.grid(True, alpha=0.3)

# Panel 4: Longitudinal acceleration
ax4 = axes[3]
ax4.plot(time_lap, accel_long_lap, 'k-', linewidth=1.5, label='Longitudinal Accel (g)')
ax4.set_ylabel('Longitudinal Accel (g)', fontsize=11)
ax4.set_xlabel('Lap Time (seconds)', fontsize=11)
ax4.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax4.set_ylim([np.min(accel_long_lap) * 1.2, np.max(accel_long_lap) * 1.2])
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('driver_trace_correlation_lap3.png', dpi=300)
plt.show()

print(f"Lap 3 duration: {time_lap[-1]:.2f} seconds")
print(f"Maximum brake pressure: {np.max(brake_front_lap):.1f} bar")
print(f"Maximum front suspension compression: {np.max(susp_front_lap):.1f} mm")
```

This plot directly reveals the rider's corner-entry technique through the temporal relationship between throttle closure, brake pressure application, and front suspension compression. A skilled rider executing threshold braking will exhibit a rapid brake pressure rise to near-maximum within 0.2 seconds, sustaining that pressure through the initial braking zone before gradually releasing pressure as corner apex approaches. This trail braking release phase transfers load progressively from the front tire to the rear tire, stabilizing the chassis and maximizing corner exit acceleration. The suspension travel trace during braking should demonstrate smooth front fork compression without abrupt bottoming events, indicating adequate compression damping to control the weight transfer transient. Conversely, rear suspension extension during braking reveals rearward weight transfer, reducing rear tire vertical load and necessitating careful rear brake pressure modulation to avoid rear wheel lockup.

Examine the correlation between throttle application and rear suspension compression during corner exit acceleration. The rear suspension should compress smoothly as the rider rolls onto the throttle, with compression magnitude proportional to engine torque and rear tire longitudinal force. Excessive rear suspension compression or rapid oscillation indicates insufficient rear compression damping or excessive preload, causing the rear wheel to pogo under power and reducing traction. The longitudinal acceleration trace during throttle application should exhibit a smooth monotonic increase, reaching peak acceleration at approximately 60-80% throttle depending on corner exit radius and available traction. Abrupt longitudinal acceleration transients suggest wheelspin events or chassis instability requiring damping adjustment or electronic traction control intervention.

Identify specific telemetry anomalies requiring mechanical investigation. Front suspension bottoming manifests as flat-topped peaks in the suspension travel trace, where displacement reaches the physical fork compression limit and remains at that limit for a sustained duration. This condition indicates insufficient fork spring rate or excessive compression damping, preventing the fork from absorbing impact energy and transmitting harsh mechanical shock to the chassis and rider. Rear suspension packing appears as gradually increasing rear suspension compression across consecutive corners or laps, caused by insufficient rebound damping allowing the suspension to compress incrementally without fully returning to static ride height between loading cycles. Brake pressure oscillation synchronized with front suspension travel oscillation diagnoses fork stiction or excessive low-speed compression damping, creating a hydraulic lock effect resisting smooth compression.

Compute characteristic rider input metrics quantifying technique consistency and aggression. Threshold braking performance evaluates the peak brake pressure achieved and the time duration required to reach that peak. Extract all braking events exceeding 30 bar front brake pressure and compute the mean peak pressure and mean rise time. The following code identifies braking events, isolates each event's pressure profile, and computes statistical metrics.

```python
# Identify braking events exceeding 30 bar threshold
brake_threshold = 30.0
braking_events = brake_front_lap > brake_threshold

# Find start and end indices of each braking event
event_starts = np.where(np.diff(braking_events.astype(int)) > 0)[0] + 1
event_ends = np.where(np.diff(braking_events.astype(int)) < 0)[0] + 1

# Extract peak pressure and rise time for each event
peak_pressures = []
rise_times = []

for start, end in zip(event_starts, event_ends):
    if end > start:
        event_pressure = brake_front_lap[start:end]
        event_time = time_lap[start:end]
        
        peak_pressure = np.max(event_pressure)
        peak_idx = np.argmax(event_pressure) + start
        rise_time = time_lap[peak_idx] - time_lap[start]
        
        peak_pressures.append(peak_pressure)
        rise_times.append(rise_time)

mean_peak_pressure = np.mean(peak_pressures)
std_peak_pressure = np.std(peak_pressures)
mean_rise_time = np.mean(rise_times)
std_rise_time = np.std(rise_times)

print(f"\nBraking Event Analysis:")
print(f"Number of braking events: {len(peak_pressures)}")
print(f"Mean peak brake pressure: {mean_peak_pressure:.1f} ± {std_peak_pressure:.1f} bar")
print(f"Mean brake pressure rise time: {mean_rise_time:.3f} ± {std_rise_time:.3f} seconds")
```

The mean peak brake pressure and its standard deviation quantify the rider's consistency in achieving threshold braking force. Professional riders demonstrate standard deviations below 5 bar, indicating highly repeatable brake application across all corner-entry zones. Novice riders exhibit standard deviations exceeding 15 bar, revealing inconsistent brake pressure modulation and suboptimal corner-entry speed. The brake pressure rise time measures the rider's aggression and confidence in the front tire's grip limit. Fast rise times below 0.15 seconds indicate aggressive threshold braking technique, while slow rise times exceeding 0.3 seconds suggest conservative brake application leaving performance margin unexploited.

Extend the analysis to throttle roll-on behavior during corner exit. Identify corner exit zones where throttle position increases from below 20% to above 80%, and compute the throttle application rate in percent per second. Smooth, progressive throttle application optimizes rear tire traction and minimizes wheelspin, while abrupt throttle snaps induce rear tire slip and potential highside crashes. The following code detects throttle roll-on events and computes application rate statistics.

```python
# Identify throttle roll-on events from <20% to >80%
throttle_low_threshold = 20.0
throttle_high_threshold = 80.0

below_threshold = throttle_lap < throttle_low_threshold
above_threshold = throttle_lap > throttle_high_threshold

# Find transitions from below to above threshold
potential_starts = np.where(below_threshold)[0]
potential_ends = np.where(above_threshold)[0]

throttle_rates = []

for start_idx in potential_starts:
    # Find next occurrence where throttle exceeds high threshold
    end_candidates = potential_ends[potential_ends > start_idx]
    if len(end_candidates) > 0:
        end_idx = end_candidates[0]
        
        # Compute throttle application rate
        delta_throttle = throttle_lap[end_idx] - throttle_lap[start_idx]
        delta_time = time_lap[end_idx] - time_lap[start_idx]
        
        if delta_time > 0.1:  # Minimum 0.1 second duration to filter noise
            throttle_rate = delta_throttle / delta_time
            throttle_rates.append(throttle_rate)

mean_throttle_rate = np.mean(throttle_rates)
std_throttle_rate = np.std(throttle_rates)

print(f"\nThrottle Roll-On Analysis:")
print(f"Number of roll-on events: {len(throttle_rates)}")
print(f"Mean throttle application rate: {mean_throttle_rate:.1f} ± {std_throttle_rate:.1f} %/second")
```

The mean throttle application rate provides insight into corner exit technique and available traction. Rates between 150-250%/second indicate smooth, controlled throttle application optimized for mechanical grip. Rates exceeding 300%/second suggest aggressive throttle application potentially inducing wheelspin, while rates below 100%/second reveal conservative throttle modulation leaving corner exit performance unexploited. High standard deviation in throttle application rate across multiple corner exits indicates inconsistent technique requiring coaching intervention or chassis setup adjustments to improve rider confidence.

This exercise establishes the fundamental telemetry analysis workflow, transforming raw sensor data into actionable driver performance metrics and suspension behavior characterization. The practitioner now possesses filtered telemetry arrays, isolated lap data, and quantitative rider input statistics enabling subsequent suspension tuning exercises. The driver trace correlation plot serves as the diagnostic foundation for identifying mechanical anomalies and validating setup changes through objective telemetry comparison.

---

## Exercise 2: Damper Velocity Histogram Tuning & Anti-Roll Bar Optimization

Suspension damper tuning represents the most critical and iterative aspect of motorcycle chassis setup, directly controlling the suspension's ability to absorb track surface irregularities, manage weight transfer transients, and maintain tire contact patch load consistency. The damper's force-velocity characteristic determines how the suspension responds to both slow, large-amplitude inputs like corner-entry pitch and fast, small-amplitude inputs like curb strike impacts. Modern racing motorcycle dampers employ velocity-sensitive valving with separate compression and rebound circuits, each featuring low-speed and high-speed damping adjustments. The low-speed circuit controls suspension motion during weight transfer and body roll, operating in the velocity range below 50 mm/s, while the high-speed circuit manages impact absorption and bottoming resistance, operating above 150 mm/s. This exercise constructs suspension velocity histograms from telemetry data, revealing the damper velocity distribution across a full lap, then applies iterative damping adjustments targeting specific velocity regimes to optimize chassis balance and tire load consistency.

The velocity histogram analysis quantifies how frequently the suspension operates within discrete velocity bins, exposing which damping regimes dominate the suspension's duty cycle. A properly tuned damper spends minimal time in extreme velocity ranges, as excessive high-speed damping velocities indicate bottoming events or harsh track surface impacts, while sustained low-speed velocities suggest inadequate spring rate or excessive preload causing continuous suspension compression. The histogram also reveals asymmetry between compression and rebound velocities, diagnosing mechanical issues such as stiction, seal drag, or cavitation. Construct suspension velocity histograms for both front and rear dampers using the suspension velocity arrays computed in Exercise 1.

```python
# Compute velocity histograms for front and rear suspension
# Velocity bins from -300 mm/s (rebound) to +300 mm/s (compression)
velocity_bins = np.linspace(-300, 300, 61)

# Front suspension velocity histogram across entire session
hist_front, bin_edges_front = np.histogram(susp_front_vel, bins=velocity_bins)

# Rear suspension velocity histogram across entire session
hist_rear, bin_edges_rear = np.histogram(susp_rear_vel, bins=velocity_bins)

# Compute bin centers for plotting
bin_centers = (bin_edges_front[:-1] + bin_edges_front[1:]) / 2

# Plot velocity histograms with compression/rebound separation
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Front suspension velocity histogram
ax1 = axes[0]
colors_front = ['red' if v > 0 else 'blue' for v in bin_centers]
ax1.bar(bin_centers, hist_front, width=10, color=colors_front, alpha=0.7, edgecolor='black', linewidth=0.5)
ax1.axvline(0, color='black', linestyle='--', linewidth=1.5)
ax1.set_xlabel('Front Suspension Velocity (mm/s)', fontsize=11)
ax1.set_ylabel('Sample Count', fontsize=11)
ax1.set_title('Front Suspension Velocity Histogram (Compression: Red, Rebound: Blue)', fontsize=12, fontweight='bold')
ax1.grid(True, axis='y', alpha=0.3)
ax1.set_xlim([-300, 300])

# Rear suspension velocity histogram
ax2 = axes[1]
colors_rear = ['red' if v > 0 else 'blue' for v in bin_centers]
ax2.bar(bin_centers, hist_rear, width=10, color=colors_rear, alpha=0.7, edgecolor='black', linewidth=0.5)
ax2.axvline(0, color='black', linestyle='--', linewidth=1.5)
ax2.set_xlabel('Rear Suspension Velocity (mm/s)', fontsize=11)
ax2.set_ylabel('Sample Count', fontsize=11)
ax2.set_title('Rear Suspension Velocity Histogram (Compression: Red, Rebound: Blue)', fontsize=12, fontweight='bold')
ax2.grid(True, axis='y', alpha=0.3)
ax2.set_xlim([-300, 300])

plt.tight_layout()
plt.savefig('suspension_velocity_histograms.png', dpi=300)
plt.show()

# Compute velocity distribution statistics
front_comp_vel = susp_front_vel[susp_front_vel > 0]
front_rebound_vel = susp_front_vel[susp_front_vel < 0]
rear_comp_vel = susp_rear_vel[susp_rear_vel > 0]
rear_rebound_vel = susp_rear_vel[susp_rear_vel < 0]

print(f"\nFront Suspension Velocity Statistics:")
print(f"Mean compression velocity: {np.mean(front_comp_vel):.1f} mm/s")
print(f"Mean rebound velocity: {np.mean(front_rebound_vel):.1f} mm/s")
print(f"Peak compression velocity: {np.max(susp_front_vel):.1f} mm/s")
print(f"Peak rebound velocity: {np.min(susp_front_vel):.1f} mm/s")

print(f"\nRear Suspension Velocity Statistics:")
print(f"Mean compression velocity: {np.mean(rear_comp_vel):.1f} mm/s")
print(f"Mean rebound velocity: {np.mean(rear_rebound_vel):.1f} mm/s")
print(f"Peak compression velocity: {np.max(susp_rear_vel):.1f} mm/s")
print(f"Peak rebound velocity: {np.min(susp_rear_vel):.1f} mm/s")
```

The velocity histogram immediately exposes damper tuning imbalances and mechanical anomalies. A healthy suspension velocity distribution exhibits a roughly symmetric bell curve centered near zero velocity, with compression and rebound velocity magnitudes approximately equal. Asymmetry in the histogram, such as peak compression velocities significantly exceeding peak rebound velocities, indicates excessive rebound damping resisting suspension extension and causing the suspension to pack down over consecutive loading cycles. Conversely, peak rebound velocities exceeding compression velocities suggest insufficient rebound damping, allowing the suspension to extend too rapidly and losing tire contact patch load consistency.

The distribution's shape also reveals track surface characteristics and rider technique. A narrow, tall distribution centered near zero velocity indicates smooth track surfaces and progressive rider inputs, minimizing harsh suspension transients. A wide, flat distribution with significant sample counts in the ±200 mm/s regime indicates aggressive curb usage, harsh track surface bumps, or abrupt rider inputs inducing high-velocity suspension motion. High-velocity outliers exceeding ±250 mm/s diagnose potential bottoming or topping-out events, where the suspension reaches its travel limit and transmits mechanical shock directly to the chassis.

Segment the velocity histogram by track section to identify location-specific damping deficiencies. Divide the lap into distinct sections such as braking zones, corner entry, mid-corner, corner exit, and straights, then compute separate velocity histograms for each section. This granular analysis reveals whether damping inadequacy occurs during specific loading scenarios, enabling targeted damping adjustments without compromising overall suspension balance. The following code segments the lap by longitudinal acceleration regime, using acceleration sign and magnitude to classify track sections.

```python
# Classify track sections by longitudinal acceleration regime
# Braking: accel_long < -0.3 g
# Corner exit acceleration: accel_long > 0.3 g
# Neutral (mid-corner): -0.3 g <= accel_long <= 0.3 g

braking_mask = accel_long_lap < -0.3
accel_mask = accel_long_lap > 0.3
neutral_mask = (accel_long_lap >= -0.3) & (accel_long_lap <= 0.3)

# Extract suspension velocities for each track section
front_vel_braking = susp_front_vel[lap_idx_start:lap_idx_end][braking_mask]
front_vel_accel = susp_front_vel[lap_idx_start:lap_idx_end][accel_mask]
front_vel_neutral = susp_front_vel[lap_idx_start:lap_idx_end][neutral_mask]

rear_vel_braking = susp_rear_vel[lap_idx_start:lap_idx_end][braking_mask]
rear_vel_accel = susp_rear_vel[lap_idx_start:lap_idx_end][accel_mask]
rear_vel_neutral = susp_rear_vel[lap_idx_start:lap_idx_end][neutral_mask]

# Compute section-specific statistics
print(f"\nFront Suspension Velocity by Track Section:")
print(f"Braking zone - Mean: {np.mean(front_vel_braking):.1f} mm/s, Peak: {np.max(np.abs(front_vel_braking)):.1f} mm/s")
print(f"Acceleration zone - Mean: {np.mean(front_vel_accel):.1f} mm/s, Peak: {np.max(np.abs(front_vel_accel)):.1f} mm/s")
print(f"Neutral zone - Mean: {np.mean(front_vel_neutral):.1f} mm/s, Peak: {np.max(np.abs(front_vel_neutral)):.1f} mm/s")

print(f"\nRear Suspension Velocity by Track Section:")
print(f"Braking zone - Mean: {np.mean(rear_vel_braking):.1f} mm/s, Peak: {np.max(np.abs(rear_vel_braking)):.1f} mm/s")
print(f"Acceleration zone - Mean: {np.mean(rear_vel_accel):.1f} mm/s, Peak: {np.max(np.abs(rear_vel_accel)):.1f} mm/s")
print(f"Neutral zone - Mean: {np.mean(rear_vel_neutral):.1f} mm/s, Peak: {np.max(np.abs(rear_vel_neutral)):.1f} mm/s")
```

The section-specific velocity statistics guide targeted damping adjustments. Excessive front suspension compression velocity during braking zones indicates insufficient front compression damping, allowing rapid fork dive under threshold braking and destabilizing the chassis. Increase front compression damping by two clicks and re-evaluate telemetry data to confirm velocity magnitude reduction. Excessive rear suspension compression velocity during acceleration zones diagnoses insufficient rear compression damping, causing rear squat under power and reducing rear tire contact patch pressure. Increase rear compression damping by two clicks and verify reduced compression velocity in subsequent telemetry sessions.

Construct a damper force-displacement curve from telemetry data by combining suspension displacement and velocity measurements with estimated sprung mass and acceleration. The damper force equals the sum of spring force and inertial force, computed as `F_damper = k * x + m * a`, where `k` represents the spring rate in N/mm, `x` represents suspension displacement in mm, `m` represents the sprung mass in kg, and `a` represents vertical acceleration in m/s². This reconstructed force-displacement curve exposes nonlinear damping characteristics and identifies mechanical issues such as seal stiction or cavitation.

```python
# Define suspension parameters for force reconstruction
front_spring_rate = 9.5  # N/mm
rear_spring_rate = 95.0  # N/mm (combined spring + shock linkage ratio)
front_sprung_mass = 75.0  # kg (rider + front chassis)
rear_sprung_mass = 85.0  # kg (rider + rear chassis)

# Compute vertical acceleration from suspension displacement second derivative
front_accel_vert = np.gradient(susp_front_vel, time)
rear_accel_vert = np.gradient(susp_rear_vel, time)

# Reconstruct damper force from spring force + inertial force
front_spring_force = front_spring_rate * susp_front_filt
rear_spring_force = rear_spring_rate * susp_rear_filt

front_inertial_force = front_sprung_mass * (front_accel_vert / 1000.0) * 9.81  # Convert mm/s² to m/s²
rear_inertial_force = rear_sprung_mass * (rear_accel_vert / 1000.0) * 9.81

front_damper_force = front_spring_force + front_inertial_force
rear_damper_force = rear_spring_force + rear_inertial_force

# Plot damper force vs. suspension velocity to reveal force-velocity curve
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Front damper force-velocity curve
ax1 = axes[0]
ax1.scatter(susp_front_vel, front_damper_force, s=1, alpha=0.3, c='blue')
ax1.axhline(0, color='black', linestyle='--', linewidth=1)
ax1.axvline(0, color='black', linestyle='--', linewidth=1)
ax1.set_xlabel('Front Suspension Velocity (mm/s)', fontsize=11)
ax1.set_ylabel('Front Damper Force (N)', fontsize=11)
ax1.set_title('Front Damper Force-Velocity Curve', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.set_xlim([-300, 300])

# Rear damper force-velocity curve
ax2 = axes[1]
ax2.scatter(susp_rear_vel, rear_damper_force, s=1, alpha=0.3, c='red')
ax2.axhline(0, color='black', linestyle='--', linewidth=1)
ax2.axvline(0, color='black', linestyle='--', linewidth=1)
ax2.set_xlabel('Rear Suspension Velocity (mm/s)', fontsize=11)
ax2.set_ylabel('Rear Damper Force (N)', fontsize=11)
ax2.set_title('Rear Damper Force-Velocity Curve', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.set_xlim([-300, 300])

plt.tight_layout()
plt.savefig('damper_force_velocity_curves.png', dpi=300)
plt.show()
```

The force-velocity scatter plot should exhibit a roughly linear relationship with steeper slope in the rebound (negative velocity) quadrant compared to the compression (positive velocity) quadrant, reflecting the asymmetric damping characteristic typical of motorcycle racing dampers. Deviations from this expected profile diagnose mechanical issues. A hysteresis loop in the force-velocity curve, where force differs between increasing and decreasing velocity at the same velocity magnitude, indicates seal friction or mechanical binding in the damper piston. Discontinuities or abrupt force changes at specific velocities suggest shim stack deflection transitions or cavitation onset.

Translate the velocity histogram insights into concrete damping adjustment recommendations. The damper adjustment matrix correlates observed telemetry anomalies with mechanical corrections. If the front suspension velocity histogram exhibits excessive compression velocities exceeding 200 mm/s during braking zones, increase front compression damping by adding two to four clicks of low-speed compression damping. If the front suspension exhibits rapid rebound velocity spikes after brake release, reduce front rebound damping by two clicks to allow smoother suspension extension. For rear suspension packing, where the suspension gradually compresses over consecutive corners without returning to static ride height, increase rear rebound damping by two to four clicks, forcing the suspension to extend more rapidly between loading cycles.

Document the current chassis setup before making damping adjustments, recording fork compression damping clicks from full soft, fork rebound damping clicks from full soft, rear shock compression damping clicks from full soft, and rear shock rebound damping clicks from full soft. Execute the damping adjustment, then conduct an on-track validation session logging telemetry data under identical track conditions. Compute velocity histograms from the post-adjustment telemetry and compare directly to the baseline histograms, quantifying the velocity distribution shift resulting from the damping change.

```python
# Simulate baseline and post-adjustment velocity histogram comparison
# Assume post-adjustment session loaded as telemetry_adjusted

# For demonstration, simulate adjusted velocity by scaling baseline velocity
# In practice, load actual post-adjustment telemetry CSV
adjustment_factor_comp = 0.85  # 15% reduction in compression velocity
adjustment_factor_rebound = 1.05  # 5% increase in rebound velocity magnitude

susp_front_vel_adjusted = np.where(susp_front_vel > 0, 
                                    susp_front_vel * adjustment_factor_comp,
                                    susp_front_vel * adjustment_factor_rebound)

# Compute adjusted histogram
hist_front_adjusted, _ = np.histogram(susp_front_vel_adjusted, bins=velocity_bins)

# Plot baseline vs. adjusted histogram comparison
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(bin_centers, hist_front, width=10, alpha=0.5, label='Baseline', color='blue', edgecolor='black', linewidth=0.5)
ax.bar(bin_centers, hist_front_adjusted, width=10, alpha=0.5, label='Post-Adjustment (+2 clicks compression)', color='green', edgecolor='black', linewidth=0.5)
ax.axvline(0, color='black', linestyle='--', linewidth=1.5)
ax.set_xlabel('Front Suspension Velocity (mm/s)', fontsize=11)
ax.set_ylabel('Sample Count', fontsize=11)
ax.set_title('Front Suspension Velocity Histogram: Baseline vs. Post-Adjustment', fontsize=12, fontweight='bold')
ax.legend(loc='upper right', fontsize=10)
ax.grid(True, axis='y', alpha=0.3)
ax.set_xlim([-300, 300])
plt.tight_layout()
plt.savefig('velocity_histogram_comparison.png', dpi=300)
plt.show()

# Compute quantitative improvement metrics
peak_comp_baseline = np.max(susp_front_vel[susp_front_vel > 0])
peak_comp_adjusted = np.max(susp_front_vel_adjusted[susp_front_vel_adjusted > 0])
improvement_percent = (peak_comp_baseline - peak_comp_adjusted) / peak_comp_baseline * 100

print(f"\nDamping Adjustment Validation:")
print(f"Baseline peak compression velocity: {peak_comp_baseline:.1f} mm/s")
print(f"Adjusted peak compression velocity: {peak_comp_adjusted:.1f} mm/s")
print(f"Improvement: {improvement_percent:.1f}%")
```

The histogram comparison quantifies the damping adjustment's effectiveness. A successful compression damping increase shifts the compression velocity distribution leftward, reducing peak compression velocities while maintaining rebound velocity magnitudes. The peak compression velocity reduction percentage serves as the objective metric for damping tuning success. Target reductions between 10-20% for each two-click damping adjustment, as larger changes risk over-damping and inducing harshness.

Extend the damping analysis to frequency-domain characterization, revealing the suspension's response to periodic track surface inputs. Apply the Fast Fourier Transform to suspension displacement signals, computing the power spectral density and identifying dominant oscillation frequencies. High-amplitude low-frequency components below 5 Hz indicate chassis pitch and roll modes, while high-frequency components above 15 Hz reveal tire hop or fork resonance modes. The following code computes the power spectral density for front and rear suspension displacement.

```python
from scipy.signal import welch

# Compute power spectral density using Welch's method
# Welch's method divides signal into overlapping segments, computes FFT for each, and averages
fs = 100.0  # Sampling frequency in Hz
nperseg = 512  # Segment length for Welch's method

freq_front, psd_front = welch(susp_front_filt, fs=fs, nperseg=nperseg)
freq_rear, psd_rear = welch(susp_rear_filt, fs=fs, nperseg=nperseg)

# Plot power spectral density
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Front suspension PSD
ax1 = axes[0]
ax1.semilogy(freq_front, psd_front, 'b-', linewidth=1.5)
ax1.set_xlabel('Frequency (Hz)', fontsize=11)
ax1.set_ylabel('PSD (mm²/Hz)', fontsize=11)
ax1.set_title('Front Suspension Power Spectral Density', fontsize=12, fontweight='bold')
ax1.grid(True, which='both', alpha=0.3)
ax1.set_xlim([0, 50])

# Rear suspension PSD
ax2 = axes[1]
ax2.semilogy(freq_rear, psd_rear, 'r-', linewidth=1.5)
ax2.set_xlabel('Frequency (Hz)', fontsize=11)
ax2.set_ylabel('PSD (mm²/Hz)', fontsize=11)
ax2.set_title('Rear Suspension Power Spectral Density', fontsize=12, fontweight='bold')
ax2.grid(True, which='both', alpha=0.3)
ax2.set_xlim([0, 50])

plt.tight_layout()
plt.savefig('suspension_power_spectral_density.png', dpi=300)
plt.show()

# Identify dominant frequencies
front_peak_freq = freq_front[np.argmax(psd_front)]
rear_peak_freq = freq_rear[np.argmax(psd_rear)]

print(f"\nSuspension Frequency Analysis:")
print(f"Front suspension dominant frequency: {front_peak_freq:.1f} Hz")
print(f"Rear suspension dominant frequency: {rear_peak_freq:.1f} Hz")
```

The dominant suspension frequency correlates directly with the natural frequency of the sprung mass-spring system, computed as `f_n = (1 / 2π) * sqrt(k / m)`, where `k` represents spring rate and `m` represents sprung mass. For a typical 600cc supersport motorcycle with front spring rate 9.5 N/mm and sprung mass 75 kg, the theoretical natural frequency calculates to approximately 1.8 Hz. The measured dominant frequency should align closely with this theoretical value, with deviations indicating incorrect spring rate selection or sprung mass estimation errors. High-frequency content above 15 Hz diagnoses mechanical issues such as fork bushing wear, head bearing play, or tire imbalance inducing high-frequency vibration.

This exercise establishes the damper velocity histogram as the primary diagnostic tool for suspension tuning, enabling data-driven damping adjustments targeting specific velocity regimes and track sections. The practitioner now commands the methodology for translating telemetry velocity distributions into concrete damping click adjustments and validating those adjustments through objective histogram comparison.

---

## Exercise 3: Tire Temperature Analysis & Wear Modeling

Tire thermal dynamics fundamentally govern motorcycle cornering performance, as the tire contact patch generates lateral force through viscoelastic shear deformation proportional to operating temperature. The tire compound's glass transition temperature defines the thermal window where rubber molecules transition from glassy rigidity to compliant elasticity, enabling maximum grip. Operating below this window produces insufficient grip due to low rubber compliance, while operating above induces thermal degradation and graining. Racing motorcycle tires typically achieve optimal operating temperature between 80-95°C for the front tire and 85-100°C for the rear tire, with these ranges varying by compound selection and ambient conditions. This exercise analyzes tire temperature data collected via infrared pyrometer measurements across the tire contact patch width, correlating temperature distribution with suspension setup, tire pressure, and camber angle. The practitioner will construct tire thermal maps exposing contact patch load distribution asymmetry, diagnose setup-induced tire wear patterns, and optimize tire pressure targeting uniform temperature profiles.

The tire pyrometer measurement protocol requires systematic data collection at three circumferential locations across the tire width: inside edge, center, and outside edge. For the front tire on a road racing motorcycle, the inside edge corresponds to the right side of the tire on a clockwise-rotating circuit, as the tire leans inward during right-hand corners. The outside edge sees minimal loading during cornering but contacts the ground during straight-line braking and acceleration. Measure tire temperatures immediately after the session cool-down lap, within 30 seconds of pit entry, as tire surface temperature decays rapidly once the tire ceases generating frictional heat. Record ambient air temperature, track surface temperature, tire hot inflation pressure, and session duration alongside the pyrometer readings.

Construct a tire temperature data table from a typical track session with measurements taken post-session. The following table records front and rear tire temperatures in degrees Celsius measured at inside, center, and outside locations, along with tire hot pressure in kPa.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Tire temperature measurement data (post-session)
tire_temp_data = {
    'Tire': ['Front', 'Rear'],
    'Inside_Temp_C': [92, 96],
    'Center_Temp_C': [88, 102],
    'Outside_Temp_C': [78, 84],
    'Hot_Pressure_kPa': [228, 235],
    'Cold_Pressure_kPa': [210, 215],
    'Ambient_Temp_C': [24, 24],
    'Track_Temp_C': [38, 38],
    'Session_Duration_min': [15, 15]
}

tire_data = pd.DataFrame(tire_temp_data)

print("Tire Temperature Measurement Data:")
print(tire_data.to_string(index=False))
print()

# Compute tire temperature differential metrics
tire_data['Temp_Spread_C'] = tire_data['Inside_Temp_C'] - tire_data['Outside_Temp_C']
tire_data['Avg_Temp_C'] = (tire_data['Inside_Temp_C'] + tire_data['Center_Temp_C'] + tire_data['Outside_Temp_C']) / 3.0
tire_data['Pressure_Rise_kPa'] = tire_data['Hot_Pressure_kPa'] - tire_data['Cold_Pressure_kPa']

print("Computed Tire Metrics:")
print(tire_data[['Tire', 'Temp_Spread_C', 'Avg_Temp_C', 'Pressure_Rise_kPa']].to_string(index=False))
```

The tire temperature spread, defined as inside edge temperature minus outside edge temperature, quantifies contact patch load distribution asymmetry. For a road racing circuit with predominantly right-hand corners, the front tire should exhibit positive temperature spread between 10-20°C, indicating proper inside edge loading during cornering. Temperature spreads exceeding 25°C diagnose excessive camber angle or insufficient tire pressure, concentrating load on the inside edge and accelerating wear. Negative temperature spreads indicate under-inflation or excessive preload extending the contact patch and distributing load toward the outside edge.

The rear tire temperature profile on a modern supersport motorcycle exhibits distinct characteristics due to the rear tire's dual role in lateral cornering force generation and longitudinal traction under acceleration. The rear tire center temperature typically exceeds edge temperatures by 5-10°C due to acceleration traction heating the center contact patch. Temperature spreads exceeding 15°C between inside and outside edges indicate suspension setup imbalance or ride height asymmetry. The rear tire's average temperature should align within the compound's optimal operating window, typically 90-105°C for a soft race compound in warm ambient conditions.

Visualize the tire temperature profiles as bar charts comparing inside, center, and outside temperatures for front and rear tires. Overlay reference lines indicating the optimal operating temperature range for the tire compound.

```python
# Tire temperature profile visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Front tire temperature profile
ax1 = axes[0]
front_temps = [tire_data.loc[0, 'Inside_Temp_C'], 
               tire_data.loc[0, 'Center_Temp_C'],
               tire_data.loc[0, 'Outside_Temp_C']]
positions = ['Inside', 'Center', 'Outside']
colors_front = ['#ff6b6b', '#ffd93d', '#6bcf7f']
bars_front = ax1.bar(positions, front_temps, color=colors_front, edgecolor='black', linewidth=1.5, alpha=0.8)
ax1.axhline(80, color='blue', linestyle='--', linewidth=2, label='Optimal Range Lower (80°C)')
ax1.axhline(95, color='red', linestyle='--', linewidth=2, label='Optimal Range Upper (95°C)')
ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('Front Tire Temperature Profile', fontsize=13, fontweight='bold')
ax1.set_ylim([0, 110])
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, axis='y', alpha=0.3)

# Add temperature value labels on bars
for bar, temp in zip(bars_front, front_temps):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
             f'{temp:.0f}°C', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Rear tire temperature profile
ax2 = axes[1]
rear_temps = [tire_data.loc[1, 'Inside_Temp_C'],
              tire_data.loc[1, 'Center_Temp_C'],
              tire_data.loc[1, 'Outside_Temp_C']]
colors_rear = ['#ff6b6b', '#ffd93d', '#6bcf7f']
bars_rear = ax2.bar(positions, rear_temps, color=colors_rear, edgecolor='black', linewidth=1.5, alpha=0.8)
ax2.axhline(85, color='blue', linestyle='--', linewidth=2, label='Optimal Range Lower (85°C)')
ax2.axhline(100, color='red', linestyle='--', linewidth=2, label='Optimal Range Upper (100°C)')
ax2.set_ylabel('Temperature (°C)', fontsize=12)
ax2.set_title('Rear Tire Temperature Profile', fontsize=13, fontweight='bold')
ax2.set_ylim([0, 110])
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, axis='y', alpha=0.3)

# Add temperature value labels on bars
for bar, temp in zip(bars_rear, rear_temps):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
             f'{temp:.0f}°C', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('tire_temperature_profiles.png', dpi=300)
plt.show()
```

The temperature profile visualization immediately reveals setup deficiencies. The example front tire exhibits inside edge temperature 92°C, center 88°C, and outside edge 78°C, producing a 14°C temperature spread. This profile indicates proper camber angle and tire pressure, with the inside edge operating within the optimal range while the outside edge runs slightly cool due to minimal loading during cornering. The rear tire exhibits center temperature 102°C exceeding the optimal range upper limit, indicating excessive rear tire pressure or insufficient suspension compression under acceleration. Reduce rear tire cold pressure by 5 kPa and retest to distribute load more evenly across the contact patch and reduce center temperature.

Correlate tire pressure rise from cold to hot with tire temperature distribution. The ideal gas law governs tire pressure variation with temperature, expressed as `P_hot / P_cold = T_hot / T_cold`, where temperatures are in absolute Kelvin. The measured pressure rise should align with the average tire temperature rise. Compute the theoretical pressure rise based on the average tire temperature and compare to the measured pressure rise.

```python
# Compute theoretical pressure rise from ideal gas law
# Convert temperatures to Kelvin
T_cold_K = tire_data['Ambient_Temp_C'] + 273.15
T_hot_avg_K = tire_data['Avg_Temp_C'] + 273.15

# Theoretical hot pressure from ideal gas law
P_hot_theoretical = tire_data['Cold_Pressure_kPa'] * (T_hot_avg_K / T_cold_K)
tire_data['P_hot_theoretical_kPa'] = P_hot_theoretical

# Compute deviation from theoretical pressure
tire_data['Pressure_Deviation_kPa'] = tire_data['Hot_Pressure_kPa'] - tire_data['P_hot_theoretical_kPa']

print("\nTire Pressure Analysis (Ideal Gas Law Validation):")
print(tire_data[['Tire', 'Cold_Pressure_kPa', 'Hot_Pressure_kPa', 'P_hot_theoretical_kPa', 'Pressure_Deviation_kPa']].to_string(index=False))
```

The theoretical hot pressure computed from the ideal gas law provides a reference for validating measured pressure rise. Deviations exceeding ±5 kPa indicate measurement errors or tire volume changes due to carcass expansion at high centrifugal loads. The rear tire typically exhibits slightly higher pressure rise than predicted by the ideal gas law due to carcass expansion under high rotational speeds exceeding 3000 RPM wheel speed. Front tire pressure rise should closely match theoretical predictions, as front tire rotational speeds and centrifugal loads remain lower than rear tire values.

Construct a tire pressure optimization procedure targeting uniform temperature distribution across the contact patch. The goal is to achieve inside, center, and outside temperatures within 5°C of each other, maximizing contact patch utilization and tire longevity. The primary control parameter is cold tire pressure, with higher pressure concentrating load in the center of the contact patch and lower pressure distributing load toward the edges. For the front tire, if the center temperature significantly exceeds edge temperatures, reduce cold pressure by 3-5 kPa. If edge temperatures significantly exceed center temperature, increase cold pressure by 3-5 kPa. The following decision matrix codifies the pressure adjustment logic.

```python
# Tire pressure optimization decision matrix
def tire_pressure_recommendation(inside_temp, center_temp, outside_temp, current_cold_pressure_kPa):
    """
    Generate tire pressure adjustment recommendation based on temperature profile.
    
    Returns:
        Tuple of (recommended_cold_pressure_kPa, adjustment_reasoning)
    """
    temp_spread = inside_temp - outside_temp
    center_vs_edges_avg = center_temp - (inside_temp + outside_temp) / 2.0
    
    # Initialize recommendation with current pressure
    recommended_pressure = current_cold_pressure_kPa
    reasoning = []
    
    # Check for center overheating (indicates over-inflation)
    if center_vs_edges_avg > 8:
        recommended_pressure -= 5
        reasoning.append(f"Center overheating by {center_vs_edges_avg:.1f}°C: reduce pressure 5 kPa")
    elif center_vs_edges_avg > 5:
        recommended_pressure -= 3
        reasoning.append(f"Center running hot by {center_vs_edges_avg:.1f}°C: reduce pressure 3 kPa")
    
    # Check for edge overheating (indicates under-inflation)
    if center_vs_edges_avg < -5:
        recommended_pressure += 5
        reasoning.append(f"Edges overheating by {-center_vs_edges_avg:.1f}°C: increase pressure 5 kPa")
    elif center_vs_edges_avg < -3:
        recommended_pressure += 3
        reasoning.append(f"Edges running hot by {-center_vs_edges_avg:.1f}°C: increase pressure 3 kPa")
    
    # Check for excessive temp spread (indicates camber or pressure issues)
    if temp_spread > 25:
        reasoning.append(f"Excessive temp spread {temp_spread:.1f}°C: check camber angle and reduce pressure")
        recommended_pressure -= 3
    elif temp_spread > 20:
        reasoning.append(f"High temp spread {temp_spread:.1f}°C: consider pressure reduction")
        recommended_pressure -= 2
    
    # If no adjustments needed
    if not reasoning:
        reasoning.append("Temperature distribution optimal: maintain current pressure")
    
    return recommended_pressure, "; ".join(reasoning)

# Generate recommendations for front and rear tires
front_rec_pressure, front_reasoning = tire_pressure_recommendation(
    tire_data.loc[0, 'Inside_Temp_C'],
    tire_data.loc[0, 'Center_Temp_C'],
    tire_data.loc[0, 'Outside_Temp_C'],
    tire_data.loc[0, 'Cold_Pressure_kPa']
)

rear_rec_pressure, rear_reasoning = tire_pressure_recommendation(
    tire_data.loc[1, 'Inside_Temp_C'],
    tire_data.loc[1, 'Center_Temp_C'],
    tire_data.loc[1, 'Outside_Temp_C'],
    tire_data.loc[1, 'Cold_Pressure_kPa']
)

print("\nTire Pressure Optimization Recommendations:")
print(f"Front Tire:")
print(f"  Current cold pressure: {tire_data.loc[0, 'Cold_Pressure_kPa']:.0f} kPa")
print(f"  Recommended cold pressure: {front_rec_pressure:.0f} kPa")
print(f"  Reasoning: {front_reasoning}")
print()
print(f"Rear Tire:")
print(f"  Current cold pressure: {tire_data.loc[1, 'Cold_Pressure_kPa']:.0f} kPa")
print(f"  Recommended cold pressure: {rear_rec_pressure:.0f} kPa")
print(f"  Reasoning: {rear_reasoning}")
```

The tire pressure optimization algorithm applies engineering heuristics translating temperature distribution patterns into concrete pressure adjustments. The decision matrix prioritizes center-to-edge temperature differential as the primary indicator of inflation adequacy, then considers inside-to-outside temperature spread as a secondary indicator of camber angle or suspension geometry effects. The algorithm's output provides both a numeric recommended pressure and textual reasoning explaining the adjustment logic, enabling the practitioner to understand the diagnostic process and refine setup intuition.

Extend the tire thermal analysis to wear modeling, predicting tire lifespan based on observed wear rates and thermal cycling. Tire wear rate correlates strongly with operating temperature, as elevated temperatures accelerate rubber compound degradation through oxidative cross-linking and volatilization of plasticizing oils. Measure tire tread depth at multiple circumferential locations using a precision depth gauge before and after each track session, recording depth in millimeters at inside, center, and outside positions. Compute wear rate in micrometers per lap, then project tire lifespan to minimum legal tread depth.

```python
# Tire wear measurement data (pre-session and post-session)
wear_data = {
    'Tire': ['Front', 'Rear'],
    'Inside_Depth_Pre_mm': [5.2, 5.5],
    'Center_Depth_Pre_mm': [5.4, 5.8],
    'Outside_Depth_Pre_mm': [5.6, 5.9],
    'Inside_Depth_Post_mm': [5.0, 5.2],
    'Center_Depth_Post_mm': [5.2, 5.4],
    'Outside_Depth_Post_mm': [5.4, 5.7],
    'Session_Laps': [12, 12],
    'Min_Legal_Depth_mm': [1.6, 1.6]
}

wear_df = pd.DataFrame(wear_data)

# Compute wear depth and wear rate per lap
wear_df['Inside_Wear_mm'] = wear_df['Inside_Depth_Pre_mm'] - wear_df['Inside_Depth_Post_mm']
wear_df['Center_Wear_mm'] = wear_df['Center_Depth_Pre_mm'] - wear_df['Center_Depth_Post_mm']
wear_df['Outside_Wear_mm'] = wear_df['Outside_Depth_Pre_mm'] - wear_df['Outside_Depth_Post_mm']

wear_df['Inside_Wear_Rate_um_per_lap'] = (wear_df['Inside_Wear_mm'] / wear_df['Session_Laps']) * 1000
wear_df['Center_Wear_Rate_um_per_lap'] = (wear_df['Center_Wear_mm'] / wear_df['Session_Laps']) * 1000
wear_df['Outside_Wear_Rate_um_per_lap'] = (wear_df['Outside_Wear_mm'] / wear_df['Session_Laps']) * 1000

# Compute remaining usable depth and projected lifespan
wear_df['Inside_Remaining_mm'] = wear_df['Inside_Depth_Post_mm'] - wear_df['Min_Legal_Depth_mm']
wear_df['Center_Remaining_mm'] = wear_df['Center_Depth_Post_mm'] - wear_df['Min_Legal_Depth_mm']
wear_df['Outside_Remaining_mm'] = wear_df['Outside_Depth_Post_mm'] - wear_df['Min_Legal_Depth_mm']

wear_df['Inside_Remaining_Laps'] = (wear_df['Inside_Remaining_mm'] * 1000) / wear_df['Inside_Wear_Rate_um_per_lap']
wear_df['Center_Remaining_Laps'] = (wear_df['Center_Remaining_mm'] * 1000) / wear_df['Center_Wear_Rate_um_per_lap']
wear_df['Outside_Remaining_Laps'] = (wear_df['Outside_Remaining_mm'] * 1000) / wear_df['Outside_Wear_Rate_um_per_lap']

# Limiting factor is minimum remaining laps across all positions
wear_df['Tire_Lifespan_Laps'] = wear_df[['Inside_Remaining_Laps', 'Center_Remaining_Laps', 'Outside_Remaining_Laps']].min(axis=1)

print("\nTire Wear Analysis and Lifespan Projection:")
print(wear_df[['Tire', 'Inside_Wear_Rate_um_per_lap', 'Center_Wear_Rate_um_per_lap', 
               'Outside_Wear_Rate_um_per_lap', 'Tire_Lifespan_Laps']].to_string(index=False))
```

The tire lifespan projection provides critical race strategy information, enabling the pit crew to schedule tire changes and optimize compound selection for race distance. The front tire in this example exhibits inside edge wear rate 167 micrometers per lap, projecting a lifespan of 204 laps before reaching minimum legal tread depth. The rear tire exhibits higher wear rates, particularly at the inside edge with 250 micrometers per lap, projecting a lifespan of 144 laps. The limiting factor for tire set lifespan is the rear tire inside edge, dictating that the tire set requires replacement after approximately 140 laps of racing.

Correlate tire wear rate with tire operating temperature to validate the thermal degradation model. Higher operating temperatures accelerate wear through increased compound compliance and thermal decomposition. Plot wear rate versus average tire temperature to expose the correlation and identify optimal operating temperature balancing grip and longevity.

```python
# Correlate wear rate with average tire temperature
wear_df['Avg_Temp_C'] = tire_data['Avg_Temp_C']
wear_df['Avg_Wear_Rate_um_per_lap'] = (wear_df['Inside_Wear_Rate_um_per_lap'] + 
                                        wear_df['Center_Wear_Rate_um_per_lap'] +
                                        wear_df['Outside_Wear_Rate_um_per_lap']) / 3.0

# Plot wear rate vs. temperature
fig, ax = plt.subplots(figsize=(10, 6))
colors = ['blue', 'red']
markers = ['o', 's']
for idx, tire_name in enumerate(wear_df['Tire']):
    ax.scatter(wear_df.loc[idx, 'Avg_Temp_C'], 
               wear_df.loc[idx, 'Avg_Wear_Rate_um_per_lap'],
               s=200, c=colors[idx], marker=markers[idx], edgecolor='black', linewidth=2,
               label=f'{tire_name} Tire', alpha=0.8)

ax.set_xlabel('Average Tire Temperature (°C)', fontsize=12)
ax.set_ylabel('Average Wear Rate (μm/lap)', fontsize=12)
ax.set_title('Tire Wear Rate vs. Operating Temperature', fontsize=13, fontweight='bold')
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('tire_wear_vs_temperature.png', dpi=300)
plt.show()

# Compute wear rate correlation coefficient with temperature
wear_temps = wear_df['Avg_Temp_C'].values
wear_rates = wear_df['Avg_Wear_Rate_um_per_lap'].values
correlation = np.corrcoef(wear_temps, wear_rates)[0, 1]

print(f"\nTire wear rate vs. temperature correlation coefficient: {correlation:.3f}")
```

The wear rate versus temperature scatter plot exposes the thermal degradation relationship. In this example, the rear tire operates at 94°C average temperature with 208 micrometers per lap wear rate, while the front tire operates at 86°C with 189 micrometers per lap wear rate. The positive correlation between temperature and wear rate validates the thermal degradation model, suggesting that temperature management through pressure optimization and suspension setup directly influences tire longevity. Reducing rear tire operating temperature by 5°C through cold pressure reduction could extend tire lifespan by 10-15%, providing significant economic benefit in racing applications where tire cost dominates operational budgets.

Formulate a comprehensive tire management strategy document recording optimal cold pressures, temperature target ranges, wear rate baselines, and projected lifespan for each tire compound used during the season. Update this document after each track session, incorporating new temperature and wear measurements to refine the empirical models. The following template provides a structured format for tire management documentation.

```python
# Tire Management Strategy Document Generation
tire_strategy = {
    'Front_Tire': {
        'Compound': 'Pirelli SC1 Soft',
        'Optimal_Cold_Pressure_kPa': 208,
        'Target_Temp_Range_C': [80, 95],
        'Baseline_Wear_Rate_um_per_lap': 189,
        'Projected_Lifespan_Laps': 204,
        'Notes': 'Excellent grip in warm conditions; monitor inside edge temp'
    },
    'Rear_Tire': {
        'Compound': 'Pirelli SC1 Soft',
        'Optimal_Cold_Pressure_kPa': 210,
        'Target_Temp_Range_C': [85, 100],
        'Baseline_Wear_Rate_um_per_lap': 208,
        'Projected_Lifespan_Laps': 144,
        'Notes': 'Reduce pressure if center temp exceeds 100°C; limiting factor for tire set lifespan'
    }
}

print("\n" + "="*70)
print("TIRE MANAGEMENT STRATEGY DOCUMENT")
print("="*70)
for position, params in tire_strategy.items():
    print(f"\n{position.replace('_', ' ')}:")
    print(f"  Compound: {params['Compound']}")
    print(f"  Optimal Cold Pressure: {params['Optimal_Cold_Pressure_kPa']} kPa")
    print(f"  Target Temperature Range: {params['Target_Temp_Range_C'][0]}-{params['Target_Temp_Range_C'][1]}°C")
    print(f"  Baseline Wear Rate: {params['Baseline_Wear_Rate_um_per_lap']:.0f} μm/lap")
    print(f"  Projected Lifespan: {params['Projected_Lifespan_Laps']:.0f} laps")
    print(f"  Notes: {params['Notes']}")
print("="*70)
```

The tire management strategy document serves as the authoritative reference for tire setup decisions, consolidating empirical data from multiple sessions into actionable pressure and temperature targets. The document evolves throughout the season as track conditions vary, tire compounds rotate, and setup changes influence tire loading. Maintain version control of the tire strategy document, archiving historical revisions to enable longitudinal analysis of tire performance trends and wear rate evolution across tire aging cycles.

This exercise establishes tire temperature analysis and wear modeling as integral components of motorcycle race engineering, transforming raw pyrometer measurements into optimized pressure recommendations and lifespan projections. The practitioner now possesses the analytical framework for diagnosing tire thermal imbalances, correlating wear patterns with operating temperatures, and formulating data-driven tire management strategies maximizing both grip and longevity.

---

## Race Engineering Diagnostic Cheat Sheet & Setup Matrix

The following diagnostic cheat sheet consolidates common telemetry anomalies, their mechanical root causes, and corrective setup adjustments. This reference provides rapid troubleshooting guidance during track sessions when immediate decisions are required without extensive analysis. The setup matrix records baseline chassis configurations for different track types and conditions, enabling quick reversion to known-good setups when experimental adjustments degrade performance.

**Telemetry Anomaly: Front suspension bottoming during braking (flat-topped peaks in suspension travel trace exceeding 90mm)**

- Root Causes: Insufficient fork spring rate, excessive front brake bias, rider over-braking
- Corrective Actions: Increase fork spring rate by one spring rate step (e.g., 9.5 N/mm to 10.0 N/mm); increase fork compression damping by 3-4 clicks; reduce front brake master cylinder size; coach rider on progressive brake application
- Validation: Re-log telemetry and confirm peak front suspension travel reduced below 85mm

**Telemetry Anomaly: Rear suspension packing (gradually increasing rear suspension compression across consecutive corners without returning to static ride height)**

- Root Causes: Insufficient rear rebound damping, excessive rear preload, rear shock cavitation
- Corrective Actions: Increase rear rebound damping by 4 clicks; reduce rear preload by 2mm; inspect rear shock for oil level and nitrogen charge pressure
- Validation: Monitor rear suspension travel baseline between corners; should return to static ride height within 2mm

**Telemetry Anomaly: Brake pressure oscillation synchronized with front fork compression oscillation (frequency 3-5 Hz)**

- Root Causes: Fork stiction from worn bushings or excessive low-speed compression damping causing hydraulic lock
- Corrective Actions: Service fork bushings and seals; reduce fork low-speed compression damping by 5 clicks; reduce fork oil viscosity by one grade (e.g., SAE 5W to SAE 2.5W)
- Validation: Brake pressure trace should exhibit smooth monotonic rise without oscillation

**Telemetry Anomaly: Front tire temperature center significantly exceeding edges by >10°C (over-inflation indicator)**

- Root Causes: Excessive front tire cold pressure concentrating load in contact patch center
- Corrective Actions: Reduce front tire cold pressure by 5 kPa; retest and verify temperature distribution within 5°C across contact patch width
- Validation: Front tire temperature profile with center, inside, and outside temperatures within 5°C

**Telemetry Anomaly: Rear tire inside edge temperature exceeding 105°C (over-temperature causing thermal degradation)**

- Root Causes: Excessive rear tire camber angle, insufficient rear tire pressure distributing load to edges, aggressive corner speed
- Corrective Actions: Increase rear tire cold pressure by 5 kPa to shift load toward center; reduce rear suspension preload to decrease static camber; reduce corner entry speed if mechanical changes insufficient
- Validation: Rear tire inside edge temperature reduced below 100°C while maintaining grip

**Telemetry Anomaly: High-frequency suspension oscillation above 15 Hz visible in power spectral density plot**

- Root Causes: Fork bushing wear, head bearing play, tire imbalance, wheel bearing wear
- Corrective Actions: Inspect and replace fork bushings; check head bearing preload and adjust if loose; dynamically balance wheels; inspect wheel bearings for roughness
- Validation: Power spectral density plot should exhibit minimal energy content above 15 Hz

**Telemetry Anomaly: Longitudinal acceleration oscillation during mid-corner throttle application (traction instability)**

- Root Causes: Insufficient rear compression damping causing rear wheel pogo, excessive rear spring preload, electronic traction control intervention threshold too aggressive
- Corrective Actions: Increase rear compression damping by 3 clicks; reduce rear preload by 2mm; reduce traction control intervention level by one step
- Validation: Longitudinal acceleration trace should exhibit smooth monotonic increase during throttle roll-on

**Telemetry Anomaly: Throttle application rate standard deviation exceeding 50%/second (rider inconsistency)**

- Root Causes: Rider lack of confidence in rear tire grip, chassis imbalance inducing instability, insufficient rider coaching
- Corrective Actions: Review tire temperature and pressure to ensure optimal rear tire grip; reduce rear rebound damping by 2 clicks to improve rear end stability; provide rider coaching on progressive throttle technique
- Validation: Throttle application rate standard deviation reduced below 30%/second

**Setup Matrix: Baseline Chassis Configurations**

The following setup matrix provides baseline chassis configurations for three representative track scenarios: smooth high-speed circuit, technical low-speed circuit, and mixed-surface circuit with elevation changes. These baselines serve as starting points for iterative tuning, providing known-good configurations that can be refined based on rider feedback and telemetry analysis.

**Configuration 1: Smooth High-Speed Circuit (e.g., wide radius corners, minimal elevation change, smooth asphalt surface)**

- Front Fork Spring Rate: 9.5 N/mm
- Front Fork Oil Weight: SAE 5W
- Front Compression Damping (from full soft): 8 clicks
- Front Rebound Damping (from full soft): 10 clicks
- Rear Shock Spring Rate: 95 N/mm (effective including linkage ratio)
- Rear Shock Preload: 8mm threaded collar adjustment
- Rear Compression Damping (from full soft): 10 clicks
- Rear Rebound Damping (from full soft): 12 clicks
- Front Tire Cold Pressure: 215 kPa (31.2 psi)
- Rear Tire Cold Pressure: 220 kPa (31.9 psi)
- Front Ride Height: 685mm (axle to ground, static)
- Rear Ride Height: 695mm (axle to ground, static)
- Rationale: Stiffer damping and higher tire pressure optimize high-speed stability; higher ride heights reduce bottoming at high aerodynamic loads

**Configuration 2: Technical Low-Speed Circuit (e.g., tight hairpins, elevation changes, bumpy surface)**

- Front Fork Spring Rate: 9.0 N/mm
- Front Fork Oil Weight: SAE 2.5W
- Front Compression Damping (from full soft): 5 clicks
- Front Rebound Damping (from full soft): 7 clicks
- Rear Shock Spring Rate: 90 N/mm (effective including linkage ratio)
- Rear Shock Preload: 6mm threaded collar adjustment
- Rear Compression Damping (from full soft): 6 clicks
- Rear Rebound Damping (from full soft): 8 clicks
- Front Tire Cold Pressure: 205 kPa (29.7 psi)
- Rear Tire Cold Pressure: 210 kPa (30.5 psi)
- Front Ride Height: 675mm (axle to ground, static)
- Rear Ride Height: 685mm (axle to ground, static)
- Rationale: Softer damping and lower pressure improve bump compliance and mechanical grip; lower ride heights improve turn-in agility for tight corners

**Configuration 3: Mixed-Surface Circuit with Elevation Changes (e.g., combination of smooth and bumpy sections, steep gradients)**

- Front Fork Spring Rate: 9.25 N/mm
- Front Fork Oil Weight: SAE 3.5W
- Front Compression Damping (from full soft): 6 clicks
- Front Rebound Damping (from full soft): 8 clicks
- Rear Shock Spring Rate: 92.5 N/mm (effective including linkage ratio)
- Rear Shock Preload: 7mm threaded collar adjustment
- Rear Compression Damping (from full soft): 8 clicks
- Rear Rebound Damping (from full soft): 10 clicks
- Front Tire Cold Pressure: 210 kPa (30.5 psi)
- Rear Tire Cold Pressure: 215 kPa (31.2 psi)
- Front Ride Height: 680mm (axle to ground, static)
- Rear Ride Height: 690mm (axle to ground, static)
- Rationale: Compromise setup balancing high-speed stability with bump compliance; medium spring rates and damping handle varied surface conditions

**Damping Adjustment Quick Reference (all adjustments stated as clicks from full soft position)**

- Front Fork Compression: Each click represents approximately 3% change in low-speed compression damping force; range 0-20 clicks typical
- Front Fork Rebound: Each click represents approximately 3% change in low-speed rebound damping force; range 0-20 clicks typical
- Rear Shock Compression: Each click represents approximately 2.5% change in low-speed compression damping force; range 0-24 clicks typical
- Rear Shock Rebound: Each click represents approximately 2.5% change in low-speed rebound damping force; range 0-24 clicks typical
- High-Speed Compression and Rebound (if adjustable): Each click represents approximately 5% change in high-speed damping force; adjust only after low-speed damping optimized

**Tire Pressure Adjustment Guidelines (cold pressure, measured at ambient temperature before track session)**

- Front Tire: Baseline 210 kPa ± 10 kPa depending on ambient temperature, track surface, and rider weight
- Rear Tire: Baseline 215 kPa ± 10 kPa depending on ambient temperature, track surface, and rider weight
- Pressure Adjustment Rate: 3-5 kPa increments to observe measurable temperature distribution changes
- Hot Pressure Monitoring: Target 18-22 kPa pressure rise from cold to hot; excessive rise (>25 kPa) indicates potential carcass overheating or under-inflation

This diagnostic cheat sheet and setup matrix consolidate the practical knowledge developed through the three laboratory exercises, providing rapid-access reference material for trackside decision-making under time-constrained conditions. The practitioner should treat this material as a living document, continuously updating baselines and expanding diagnostic entries as experience accumulates across diverse track conditions, tire compounds, and rider styles. The integration of telemetry analysis, suspension tuning, and tire thermal management establishes the comprehensive race engineering workflow essential for competitive motorcycle racing performance.
