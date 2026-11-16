# Operational Verification Labs: Vehicle Dynamics

## Objective & Telemetry Environment Setup

The operational verification laboratory for vehicle dynamics synthesizes three distinct domains of race engineering practice: telemetry data acquisition and interpretation, chassis tuning through iterative damper and anti-roll bar adjustment, and tire thermal management through contact patch load distribution analysis. Unlike classroom simulation exercises that present idealized friction circles and sanitized mathematical abstractions, this laboratory operates on authentic race weekend telemetry streams captured from production data acquisition hardware deployed in competitive motorsport environments. The laboratory objectives are structured to mirror the workflow of a professional race engineer during Friday practice sessions: ingest raw telemetry data from multiple drivers across varied track configurations, isolate performance delta between reference and comparison laps through channel-by-channel trace overlay analysis, diagnose mechanical grip limitations through suspension velocity histograms and tire pyrometer temperature distributions, and formulate actionable setup changes quantified in discrete damper clicks and anti-roll bar blade positions.

The telemetry environment centers on MoTeC i2 Pro as the primary analysis platform, supplemented by Python-based scripting for batch processing of CSV exports and statistical correlation analysis. MoTeC i2 Pro remains the de facto standard in professional motorsport for its native support of high-frequency CAN bus streams, GPS-synchronized lap timing with sub-meter positional accuracy, and integrated mathematical channel processing for derived parameters such as longitudinal and lateral load transfer. The software operates on telemetry log files in the proprietary `.ld` format, which encapsulates time-series data streams from dozens of sensor channels sampled at rates ranging from 10 Hz for slow-moving parameters like engine coolant temperature to 1000 Hz for critical control inputs such as steering angle and brake pressure. For this laboratory, we employ CSV exports from MoTeC i2 Pro to enable cross-platform analysis in Python using the pandas and matplotlib libraries, allowing batch correlation studies across multi-session datasets that would prove cumbersome in the GUI-driven i2 environment.

The physical sensor suite underlying the telemetry data encompasses five primary categories: inertial measurement units providing three-axis accelerometer and gyroscope data at 100 Hz for body slip angle estimation and roll rate calculation, wheel speed sensors mounted at each corner hub for individual tire slip ratio computation, linear potentiometers attached to suspension pushrods or damper bodies for ride height and travel velocity measurement, strain gauge-based load cells for brake line hydraulic pressure and steering rack torque sensing, and infrared tire temperature sensors for contact patch thermal monitoring. The laboratory dataset includes telemetry from a GT3-specification race car equipped with adjustable Öhlins TTX36 dampers featuring independent high-speed and low-speed compression and rebound adjustment across 22 discrete click positions per adjuster, along with modular anti-roll bar blade assemblies allowing stiffness changes in increments of approximately 50 Nm/deg through swappable titanium torsion bars.

Installation of the analysis environment begins with MoTeC i2 Pro version 1.2 or later, available under educational licensing for academic motorsport programs or commercial licensing for professional race teams. The software installation includes the i2 Data Analysis application, the i2 Standard Math Channel Library providing pre-configured derived channels for load transfer and slip angle calculations, and the Worksheet Template Library containing standard trace overlay layouts for corner entry analysis, mid-corner platform stability assessment, and corner exit traction evaluation. Configuration of the workspace requires importing the track database file containing GPS-referenced corner markers and track boundary definitions for the circuit of interest, enabling automated lap segmentation and sector time calculation. The laboratory exercises utilize telemetry data from Watkins Glen International, a 3.4-mile road course featuring eleven turns with a 174-foot elevation change, providing a diverse mixture of high-speed sweepers, heavy braking zones, and technical low-speed chicanes that exercise the full operational envelope of vehicle dynamics phenomena.

Python environment setup requires installation of several specialized libraries beyond the standard scientific computing stack. The core dependencies include pandas version 1.5 or later for DataFrame manipulation and time-series resampling, matplotlib version 3.6 or later for publication-quality plotting with LaTeX-rendered mathematical annotations, numpy version 1.23 or later for vectorized numerical operations on telemetry arrays, and scipy version 1.9 or later for signal processing routines such as Butterworth filtering of noisy sensor channels and cross-correlation analysis of driver input timing. Installation proceeds through the Python package manager with the command `pip install pandas matplotlib numpy scipy seaborn` to include the seaborn statistical visualization library for enhanced correlation heatmap generation. The laboratory also employs the cantools library for decoding binary CAN bus messages from raw `.blf` or `.asc` log files, installed via `pip install cantools`, enabling direct ingestion of data acquisition system output without intermediate conversion through proprietary software.

Creation of a dedicated project directory structure ensures reproducible analysis workflows and efficient organization of multi-session datasets. The recommended hierarchy places raw telemetry exports in a `data/raw/` subdirectory, processed and filtered data in `data/processed/`, analysis scripts in `scripts/`, figure outputs in `figures/`, and setup documentation in `setup_sheets/`. Each telemetry session is stored in a subdirectory named according to the ISO 8601 timestamp and driver identifier, such as `data/raw/20250115_watkins_glen_driver_a/`, containing the CSV export files for individual laps alongside metadata JSON files documenting setup parameters including damper click positions, anti-roll bar blade selections, tire pressure set cold, and ambient track temperature. This organizational scheme supports automated batch processing scripts that iterate across session directories, load setup metadata, correlate performance metrics with mechanical configuration parameters, and generate statistical summaries of setup sensitivity trends.

Before proceeding to the exercises, verify installation integrity by launching MoTeC i2 Pro and loading the provided sample telemetry file `watkins_glen_baseline_lap_114.ld` from the laboratory dataset archive. The file should display in the Workspace browser showing 47 logged channels spanning the categories of GPS position and velocity, inertial sensors, wheel speeds, suspension travel, brake pressure, steering angle, and engine control unit parameters. Open the pre-configured worksheet template `GT3_Corner_Entry_Analysis.i2wsp` which arranges the critical channels in a stacked trace layout: GPS-derived speed in kilometers per hour at the top, brake pressure in bar on the second trace, steering angle in degrees on the third trace, and suspension travel for all four corners in millimeters on the bottom four traces. The worksheet automatically synchronizes all traces to a common time axis with GPS-referenced distance markers indicating the braking zone for Turn 1, the 90-degree right-hander known as The 90. Successful loading of this worksheet with proper trace overlay and distance marker alignment confirms that the telemetry environment is correctly configured and ready for operational analysis.

## Exercise 1: Telemetry Data Import & Driver Trace Correlation

The foundational skill in race engineering telemetry analysis is the precise overlay of driver traces to identify performance deltas at the channel level, decomposing an overall lap time deficit into specific control input timing differences, corner entry speed variations, and mid-corner platform stability characteristics. This exercise develops the systematic workflow for importing multi-session telemetry data, synchronizing reference and comparison laps through GPS distance alignment, and quantifying performance differences through statistical measures of channel deviation. The analytical objective is to replicate the first-practice engineering debrief scenario where two drivers of differing experience levels have completed installation laps on identical vehicle setups, and the race engineer must isolate the specific driving technique differences that account for the faster driver's advantage in order to provide actionable coaching feedback to the developing driver.

Begin by extracting the laboratory dataset archive `watkins_glen_telemetry_dataset.zip` into the project `data/raw/` directory. The archive contains two subdirectories: `driver_a_reference/` includes ten laps of telemetry from the experienced reference driver with consistent lap times in the 1:52.5 to 1:53.2 range, while `driver_b_comparison/` contains ten laps from the comparison driver with lap times spanning 1:54.1 to 1:55.8. Each subdirectory holds individual CSV files named by lap number, such as `lap_003.csv`, alongside a session metadata file `session_info.json` documenting the vehicle setup parameters held constant across both drivers: front damper compression high-speed at 14 clicks from full soft, front damper rebound high-speed at 16 clicks, rear damper compression high-speed at 12 clicks, rear damper rebound high-speed at 14 clicks, front anti-roll bar blade 28mm diameter, rear anti-roll bar blade 32mm diameter, front tire pressure 28.0 psi cold, rear tire pressure 26.5 psi cold, and front wing angle 6 degrees relative to the chassis datum. The identical mechanical setup isolates driver technique as the sole independent variable in the performance comparison.

Launch MoTeC i2 Pro and establish a new workspace by selecting File → New Workspace from the menu bar. The workspace serves as the container for all telemetry files, derived math channels, and worksheet layouts associated with a given analysis session. Navigate to File → Open Log File and select the reference driver's fastest lap file `driver_a_reference/lap_007.csv`, which recorded a lap time of 1:52.623. MoTeC i2 Pro automatically parses the CSV column headers to populate the Channel List panel on the left side of the interface, displaying the 47 available data streams. The critical channels for driver trace correlation include GPS-based vehicle speed (`Speed`), brake pressure in bar (`Brake_Press_Front`), throttle position percentage (`Throttle_Pos`), steering angle in degrees (`Steer_Angle`), lateral acceleration in G-force (`Lateral_Accel`), longitudinal acceleration in G-force (`Longtl_Accel`), and individual suspension travel channels (`Susp_Travel_FL`, `Susp_Travel_FR`, `Susp_Travel_RL`, `Susp_Travel_RR`) measured in millimeters from static ride height.

Create a new worksheet by selecting Worksheet → New Worksheet and configure a stacked trace layout optimized for corner entry analysis. Insert the first trace by right-clicking in the trace area and selecting Insert Trace, then drag the `Speed` channel from the Channel List into the trace. Configure the Y-axis range from 0 to 250 km/h to accommodate the full speed envelope of the circuit. Insert a second trace below the speed trace and add the `Brake_Press_Front` channel with a Y-axis range of 0 to 120 bar to capture peak threshold braking pressures. Insert a third trace for `Throttle_Pos` with range 0 to 100 percent, a fourth trace for `Steer_Angle` with range -180 to +180 degrees, and a fifth trace for `Lateral_Accel` with range -2.0 to +2.0 G. This five-trace layout provides comprehensive visibility into the driver's control input sequence during corner entry: the initial brake application point, the rate of brake pressure buildup, the timing of initial steering input, the coordination between brake release and steering angle increase, and the resulting lateral acceleration response of the chassis.

Synchronize the time axis across all traces by enabling GPS distance mode through the View menu option View → Distance Mode → GPS Distance. This critical step aligns the telemetry data to physical track position rather than elapsed time, compensating for variations in lap start/finish line crossing time and ensuring that corner entry events overlay precisely between different laps. The X-axis now displays distance in meters from the start/finish line, with automatic insertion of corner marker flags at GPS waypoints defined in the track database. Zoom into the Turn 1 braking zone by clicking and dragging a selection box around the distance range from 3200 to 3400 meters, which encompasses the end of the main straight through the apex of The 90. The zoomed view reveals the detailed structure of the corner entry sequence: the reference driver initiates braking at 3285 meters, builds brake pressure to a peak of 102 bar over a distance of 8 meters, begins initial steering input at 3305 meters while maintaining full brake pressure, releases brake pressure linearly from 3315 to 3335 meters while simultaneously increasing steering angle to a peak of 52 degrees at apex, and achieves a minimum corner speed of 94 km/h at 3340 meters.

Overlay the comparison driver's data by loading the second log file through File → Open Log File and selecting `driver_b_comparison/lap_004.csv`, the comparison driver's fastest lap at 1:54.187. MoTeC i2 Pro automatically loads the second log into the same workspace and assigns it a distinct color in the trace display, typically red for the comparison lap against blue for the reference lap. The overlay immediately reveals three qualitative differences in driving technique: the comparison driver initiates braking approximately 15 meters earlier at 3270 meters, builds brake pressure more gradually to a lower peak of 95 bar, and begins steering input earlier at 3295 meters while still at higher brake pressure. These qualitative observations require quantitative validation through channel statistics and delta analysis.

Generate quantitative performance metrics by inserting a Channel Report panel into the workspace. Select Worksheet → Insert Channel Report, configure the report to display statistics for the Turn 1 braking zone distance range 3280 to 3340 meters, and add rows for the channels `Speed`, `Brake_Press_Front`, `Steer_Angle`, `Lateral_Accel`, and `Longtl_Accel`. Configure each row to display the minimum, maximum, and mean values across the selected distance range for both reference and comparison laps. The Channel Report populates with the computed statistics, revealing that the reference driver's minimum speed in Turn 1 is 94.2 km/h compared to 91.8 km/h for the comparison driver, indicating that the comparison driver is over-slowing the car by 2.4 km/h despite initiating braking earlier. The maximum lateral acceleration achieved by the reference driver is 1.82 G compared to 1.68 G for the comparison driver, suggesting that the comparison driver is not fully exploiting the available mechanical grip in the mid-corner phase.

Diagnose the root cause of the minimum speed deficit through timing analysis of the brake release profile. Insert a Math Channel by selecting Channels → New Math Channel and configure a derived channel that computes the rate of change of brake pressure with respect to distance, effectively measuring the brake release gradient. Name the channel `Brake_Release_Rate` and enter the formula `ddist('Brake_Press_Front')`, which invokes the distance-domain derivative function. Add this derived channel to a new trace in the worksheet positioned directly below the brake pressure trace. The brake release rate trace reveals that the reference driver exhibits a steep negative gradient of approximately -8 bar/meter during the primary brake release phase from 3315 to 3335 meters, while the comparison driver shows a shallower gradient of approximately -5 bar/meter over a longer distance from 3310 to 3345 meters. This quantitative difference explains the minimum speed delta: the comparison driver is trailing brake deeper into the corner, which delays the transition to maintenance throttle and results in lower mid-corner speed despite adequate initial brake application.

Export the quantitative analysis results by configuring a Python script to parse the MoTeC CSV exports and compute statistical summaries across all laps in both driver datasets. Create a new Python script file `scripts/telemetry_correlation.py` and import the required libraries:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

def load_telemetry_session(session_dir):
    """Load all lap CSV files from a session directory with metadata."""
    session_path = Path(session_dir)
    metadata_file = session_path / 'session_info.json'
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    lap_files = sorted(session_path.glob('lap_*.csv'))
    laps = []
    
    for lap_file in lap_files:
        df = pd.read_csv(lap_file)
        lap_number = int(lap_file.stem.split('_')[1])
        df['lap_number'] = lap_number
        laps.append(df)
    
    session_df = pd.concat(laps, ignore_index=True)
    
    return session_df, metadata

def compute_corner_statistics(df, corner_name, distance_start, distance_end):
    """Compute statistical summary for a specified corner zone."""
    corner_mask = (df['Distance'] >= distance_start) & (df['Distance'] <= distance_end)
    corner_data = df[corner_mask]
    
    stats = {
        'corner': corner_name,
        'distance_range': (distance_start, distance_end),
        'min_speed': corner_data['Speed'].min(),
        'max_lateral_accel': corner_data['Lateral_Accel'].max(),
        'max_brake_pressure': corner_data['Brake_Press_Front'].max(),
        'mean_throttle': corner_data['Throttle_Pos'].mean(),
        'max_steer_angle': corner_data['Steer_Angle'].abs().max()
    }
    
    return stats

def plot_driver_comparison(ref_df, comp_df, corner_name, distance_start, distance_end):
    """Generate overlay plot comparing reference and comparison drivers."""
    ref_corner = ref_df[(ref_df['Distance'] >= distance_start) & (ref_df['Distance'] <= distance_end)]
    comp_corner = comp_df[(comp_df['Distance'] >= distance_start) & (comp_df['Distance'] <= distance_end)]
    
    fig, axes = plt.subplots(5, 1, figsize=(12, 10), sharex=True)
    
    axes[0].plot(ref_corner['Distance'], ref_corner['Speed'], 'b-', label='Reference', linewidth=1.5)
    axes[0].plot(comp_corner['Distance'], comp_corner['Speed'], 'r-', label='Comparison', linewidth=1.5)
    axes[0].set_ylabel('Speed (km/h)')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title(f'Driver Trace Comparison: {corner_name}')
    
    axes[1].plot(ref_corner['Distance'], ref_corner['Brake_Press_Front'], 'b-', linewidth=1.5)
    axes[1].plot(comp_corner['Distance'], comp_corner['Brake_Press_Front'], 'r-', linewidth=1.5)
    axes[1].set_ylabel('Brake Pressure (bar)')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(ref_corner['Distance'], ref_corner['Throttle_Pos'], 'b-', linewidth=1.5)
    axes[2].plot(comp_corner['Distance'], comp_corner['Throttle_Pos'], 'r-', linewidth=1.5)
    axes[2].set_ylabel('Throttle (%)')
    axes[2].grid(True, alpha=0.3)
    
    axes[3].plot(ref_corner['Distance'], ref_corner['Steer_Angle'], 'b-', linewidth=1.5)
    axes[3].plot(comp_corner['Distance'], comp_corner['Steer_Angle'], 'r-', linewidth=1.5)
    axes[3].set_ylabel('Steering Angle (deg)')
    axes[3].grid(True, alpha=0.3)
    
    axes[4].plot(ref_corner['Distance'], ref_corner['Lateral_Accel'], 'b-', linewidth=1.5)
    axes[4].plot(comp_corner['Distance'], comp_corner['Lateral_Accel'], 'r-', linewidth=1.5)
    axes[4].set_ylabel('Lateral Accel (G)')
    axes[4].set_xlabel('Distance (m)')
    axes[4].grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# Main analysis workflow
ref_session, ref_metadata = load_telemetry_session('data/raw/driver_a_reference')
comp_session, comp_metadata = load_telemetry_session('data/raw/driver_b_comparison')

# Select fastest lap from each driver
ref_fastest = ref_session[ref_session['lap_number'] == 7].copy()
comp_fastest = comp_session[comp_session['lap_number'] == 4].copy()

# Compute Turn 1 statistics
turn1_ref_stats = compute_corner_statistics(ref_fastest, 'Turn 1', 3280, 3340)
turn1_comp_stats = compute_corner_statistics(comp_fastest, 'Turn 1', 3280, 3340)

print("Turn 1 Performance Comparison:")
print(f"Reference minimum speed: {turn1_ref_stats['min_speed']:.1f} km/h")
print(f"Comparison minimum speed: {turn1_comp_stats['min_speed']:.1f} km/h")
print(f"Speed deficit: {turn1_comp_stats['min_speed'] - turn1_ref_stats['min_speed']:.1f} km/h")
print(f"\nReference max lateral accel: {turn1_ref_stats['max_lateral_accel']:.2f} G")
print(f"Comparison max lateral accel: {turn1_comp_stats['max_lateral_accel']:.2f} G")
print(f"Lateral accel deficit: {turn1_comp_stats['max_lateral_accel'] - turn1_ref_stats['max_lateral_accel']:.2f} G")

# Generate comparison plot
fig = plot_driver_comparison(ref_fastest, comp_fastest, 'Turn 1 - The 90', 3200, 3400)
plt.savefig('figures/turn1_driver_comparison.png', dpi=300, bbox_inches='tight')
plt.show()
```

Execute the script from the project root directory with the command `python scripts/telemetry_correlation.py`. The script loads both driver sessions, identifies the fastest lap from each driver based on lap number, computes corner statistics for the Turn 1 braking zone, and generates a five-trace overlay plot saved to `figures/turn1_driver_comparison.png`. The console output displays the quantitative performance deltas:

```
Turn 1 Performance Comparison:
Reference minimum speed: 94.2 km/h
Comparison minimum speed: 91.8 km/h
Speed deficit: -2.4 km/h

Reference max lateral accel: 1.82 G
Comparison max lateral accel: 1.68 G
Lateral accel deficit: -0.14 G
```

Extend the analysis to encompass the full lap by defining corner zones for all eleven turns and computing aggregated statistics across each zone. Modify the script to include a corner database dictionary:

```python
watkins_glen_corners = {
    'Turn 1 - The 90': (3280, 3340),
    'Turn 2 - Esses': (3420, 3520),
    'Turn 3 - Esses': (3520, 3600),
    'Turn 4 - Toe of the Boot': (3850, 3950),
    'Turn 5 - Boot Heel': (4150, 4280),
    'Turn 6 - Chute Entry': (4550, 4650),
    'Turn 7 - Chute Exit': (4750, 4850),
    'Turn 8 - Inner Loop': (5150, 5280),
    'Turn 9 - Outer Loop': (5380, 5480),
    'Turn 10 - NASCAR Turn': (100, 200),
    'Turn 11 - Final Turn': (2850, 2950)
}

corner_summary = []
for corner_name, (start, end) in watkins_glen_corners.items():
    ref_stats = compute_corner_statistics(ref_fastest, corner_name, start, end)
    comp_stats = compute_corner_statistics(comp_fastest, corner_name, start, end)
    
    delta_row = {
        'corner': corner_name,
        'ref_min_speed': ref_stats['min_speed'],
        'comp_min_speed': comp_stats['min_speed'],
        'speed_delta': comp_stats['min_speed'] - ref_stats['min_speed'],
        'ref_max_lat_g': ref_stats['max_lateral_accel'],
        'comp_max_lat_g': comp_stats['max_lateral_accel'],
        'lat_g_delta': comp_stats['max_lateral_accel'] - ref_stats['max_lateral_accel']
    }
    corner_summary.append(delta_row)

summary_df = pd.DataFrame(corner_summary)
summary_df.to_csv('data/processed/full_lap_corner_summary.csv', index=False)
print("\nFull Lap Corner Summary:")
print(summary_df.to_string(index=False))
```

The full lap summary output reveals that the comparison driver's primary performance deficits concentrate in three specific corners: Turn 1 with a 2.4 km/h speed deficit, Turn 5 Boot Heel with a 3.1 km/h deficit, and Turn 10 NASCAR Turn with a 2.8 km/h deficit. These three corners share a common characteristic: all are heavy braking zones transitioning into slow-speed corners requiring precise brake release and early throttle application. The correlation between deficit magnitude and corner type confirms the brake release timing hypothesis derived from the Turn 1 detailed analysis. The comparison driver would benefit from coaching emphasis on aggressive brake release to restore weight to the rear axle earlier in the corner entry phase, enabling earlier throttle application and higher minimum corner speeds.

Validate the coaching recommendation through longitudinal acceleration analysis during the corner exit phase. Insert a new Math Channel in MoTeC i2 Pro to isolate corner exit longitudinal acceleration, filtering out the braking phase contribution. Configure the channel formula as `if('Throttle_Pos' > 10, 'Longtl_Accel', 0)`, which conditionally displays longitudinal acceleration only when throttle position exceeds 10 percent, effectively isolating the exit phase. Add this derived channel to the worksheet and overlay the reference and comparison drivers for Turn 1. The trace reveals that the reference driver achieves initial throttle application 12 meters earlier at a distance of 3332 meters compared to 3344 meters for the comparison driver, and reaches a peak exit longitudinal acceleration of 0.68 G compared to 0.54 G for the comparison driver. The 12-meter earlier throttle application translates directly to higher exit speed and compounds throughout the subsequent acceleration zone on the back straight.

Formalize the driver coaching recommendations in a structured feedback document by exporting the channel statistics and overlay plots. Create a summary report template `setup_sheets/driver_coaching_report_template.md`:

```markdown
# Driver Coaching Report: Telemetry Correlation Analysis

**Session:** {session_date} - {track_name}
**Reference Driver:** {ref_driver_name}  |  **Comparison Driver:** {comp_driver_name}
**Vehicle Setup:** Identical across both drivers (see attached setup sheet)

## Lap Time Summary
- Reference fastest lap: {ref_lap_time}
- Comparison fastest lap: {comp_lap_time}
- Lap time delta: {lap_delta}

## Primary Performance Deficits (Top 3 Corners)

### 1. {corner_1_name}
- Minimum speed delta: {corner_1_speed_delta} km/h
- Max lateral G delta: {corner_1_lat_g_delta} G
- Root cause: {corner_1_diagnosis}
- Coaching recommendation: {corner_1_recommendation}

### 2. {corner_2_name}
- Minimum speed delta: {corner_2_speed_delta} km/h
- Max lateral G delta: {corner_2_lat_g_delta} G
- Root cause: {corner_2_diagnosis}
- Coaching recommendation: {corner_2_recommendation}

### 3. {corner_3_name}
- Minimum speed delta: {corner_3_speed_delta} km/h
- Max lateral G delta: {corner_3_lat_g_delta} G
- Root cause: {corner_3_diagnosis}
- Coaching recommendation: {corner_3_recommendation}

## Driving Technique Analysis

**Brake Release Timing:**
{brake_release_analysis}

**Throttle Application Timing:**
{throttle_application_analysis}

**Steering Input Coordination:**
{steering_coordination_analysis}

## Recommended Focus Areas for Next Session
1. {focus_area_1}
2. {focus_area_2}
3. {focus_area_3}

---
**Report Generated:** {report_timestamp}
**Engineer:** {engineer_name}
```

Populate the template with the computed statistics and save the completed report as `setup_sheets/driver_coaching_report_20250115_watkins_glen.md`. This structured report provides the comparison driver with actionable, data-driven feedback grounded in quantitative telemetry evidence rather than subjective observation, establishing a foundation for measurable improvement in subsequent practice sessions.

## Exercise 2: Damper Velocity Histogram Tuning & Anti-Roll Bar Optimization

The second operational verification exercise addresses the mechanical tuning workflow for suspension dampers and anti-roll bar systems, translating subjective driver feedback about chassis balance and platform stability into objective adjustments quantified in discrete damper adjuster clicks and anti-roll bar blade selections. Unlike the driver trace correlation analysis which operates in the time and distance domains, damper tuning analysis operates in the velocity domain, constructing histograms of damper shaft velocity to characterize the distribution of suspension events across the low-speed and high-speed damping regimes. The exercise objective is to diagnose a mid-corner understeer condition reported by the driver during high-speed sweeping turns, determine whether the root cause originates from damper velocity-dependent force characteristics or from steady-state roll stiffness distribution, and formulate a tuning change that addresses the handling imbalance without degrading ride quality over curbing or transient response during corner entry weight transfer.

Begin by extracting the damper tuning dataset `watkins_glen_damper_tuning_dataset.zip` into the project directory. The archive contains telemetry data from a systematic damper sweep test conducted during a Friday afternoon test session, where the front damper high-speed compression adjuster was varied across five discrete settings (10, 12, 14, 16, 18 clicks from full soft) while holding all other suspension parameters constant. Each damper setting subdirectory includes ten laps of telemetry data along with a `damper_settings.json` metadata file documenting the complete suspension configuration. The test protocol maintains rear damper settings at the baseline values (12 clicks compression high-speed, 14 clicks rebound high-speed), front and rear anti-roll bar blades at baseline diameters (28mm front, 32mm rear), and tire pressures within 0.3 psi of target cold pressures to isolate damper adjustment as the sole independent variable.

Load the baseline damper setting telemetry into MoTeC i2 Pro by opening the file `damper_sweep_14_clicks/lap_005.csv`, which represents the baseline configuration with front dampers at 14 clicks high-speed compression. Create a new worksheet optimized for damper velocity analysis by inserting four traces corresponding to the four corner suspension travel velocity channels: `Susp_Vel_FL`, `Susp_Vel_FR`, `Susp_Vel_RL`, `Susp_Vel_RR`. These derived channels are computed by MoTeC i2 Pro as the time derivative of the suspension linear potentiometer position signals, yielding velocity in units of meters per second with positive values indicating compression (jounce) and negative values indicating extension (rebound). Configure the Y-axis range for all four traces from -2.0 to +2.0 m/s to encompass the typical velocity range encountered during high-speed cornering and curbing events.

Construct damper velocity histograms by inserting a Histogram panel into the workspace through Worksheet → Insert Histogram. Configure the histogram to analyze the front-left suspension velocity channel `Susp_Vel_FL` across the full lap distance, with bin width set to 0.05 m/s and velocity range from -2.0 to +2.0 m/s. The histogram reveals a bimodal distribution characteristic of suspension velocity behavior: a primary peak centered near zero velocity corresponding to quasi-static roll and pitch attitudes during steady-state cornering, and secondary peaks at higher velocities corresponding to transient events such as initial turn-in, braking-induced pitch, and curb strikes. The critical insight from the velocity histogram is the relative population of events in the low-speed damping regime (velocities below 0.15 m/s, governed by the low-speed compression adjuster) versus the high-speed damping regime (velocities above 0.15 m/s, governed by the high-speed compression adjuster). For the baseline 14-click setting, approximately 68 percent of compression events occur below the 0.15 m/s transition velocity, indicating that the low-speed adjuster dominates the damping force character during typical cornering maneuvers.

Overlay the damper velocity histograms from all five test configurations to identify the velocity regime where adjustments produce measurable differences in damping force distribution. Load the four additional damper setting files (10, 12, 16, 18 clicks) into the workspace as comparison logs, then duplicate the histogram panel four times and assign each copy to analyze a different test configuration. Arrange the five histogram panels in a vertical stack for direct visual comparison. The overlaid histograms reveal that increasing the high-speed compression adjuster from 14 to 18 clicks shifts the distribution of high-velocity events rightward, indicating increased damping force during rapid compression events such as curb strikes, while leaving the low-velocity distribution near zero essentially unchanged. Conversely, the 10-click configuration shows increased population density at high compression velocities, indicating reduced damping force that allows the damper shaft to move more rapidly during transient events.

Quantify the damper adjustment sensitivity by computing the area under the histogram curve in specific velocity bands. Insert a Math Channel configured to integrate the damper velocity histogram over three discrete velocity bands: low-speed compression (0 to 0.15 m/s), high-speed compression (0.15 to 2.0 m/s), and rebound (-2.0 to 0 m/s). The integration yields the total time spent in each velocity regime during the lap, providing a scalar metric for comparing damper configurations. For the baseline 14-click setting, the front-left damper spends 42.3 seconds in low-speed compression, 8.7 seconds in high-speed compression, and 38.2 seconds in rebound during a 112.6-second lap. Increasing the high-speed compression adjuster to 18 clicks reduces the high-speed compression time to 7.1 seconds, indicating that the increased damping force is limiting peak shaft velocities during transient events. Decreasing the adjuster to 10 clicks increases the high-speed compression time to 11.2 seconds, indicating that reduced damping force allows higher peak velocities.

Correlate the damper velocity histogram changes with lap time performance by constructing a scatter plot of high-speed compression time versus lap time across all five test configurations. Create a Python script `scripts/damper_sweep_analysis.py` to automate the data extraction and plotting:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

def load_damper_sweep_data(sweep_dir):
    """Load all damper sweep test configurations and compute velocity histograms."""
    sweep_path = Path(sweep_dir)
    damper_configs = []
    
    for config_dir in sorted(sweep_path.glob('damper_sweep_*_clicks')):
        clicks = int(config_dir.stem.split('_')[2])
        
        with open(config_dir / 'damper_settings.json', 'r') as f:
            settings = json.load(f)
        
        lap_files = sorted(config_dir.glob('lap_*.csv'))
        lap_times = []
        hs_compression_times = []
        
        for lap_file in lap_files:
            df = pd.read_csv(lap_file)
            lap_time = df['Time'].max()
            lap_times.append(lap_time)
            
            # Compute time in high-speed compression regime (>0.15 m/s)
            hs_compression_mask = (df['Susp_Vel_FL'] > 0.15)
            hs_compression_time = hs_compression_mask.sum() * (df['Time'].iloc[1] - df['Time'].iloc[0])
            hs_compression_times.append(hs_compression_time)
        
        damper_configs.append({
            'clicks': clicks,
            'mean_lap_time': np.mean(lap_times),
            'std_lap_time': np.std(lap_times),
            'mean_hs_compression_time': np.mean(hs_compression_times),
            'settings': settings
        })
    
    return pd.DataFrame(damper_configs)

sweep_df = load_damper_sweep_data('data/raw/')

# Plot lap time vs high-speed compression time
fig, ax = plt.subplots(figsize=(10, 6))
ax.errorbar(sweep_df['mean_hs_compression_time'], sweep_df['mean_lap_time'], 
            yerr=sweep_df['std_lap_time'], fmt='o-', capsize=5, markersize=8, linewidth=2)

for idx, row in sweep_df.iterrows():
    ax.annotate(f"{row['clicks']} clicks", 
                xy=(row['mean_hs_compression_time'], row['mean_lap_time']),
                xytext=(5, 5), textcoords='offset points', fontsize=10)

ax.set_xlabel('Mean High-Speed Compression Time (seconds)', fontsize=12)
ax.set_ylabel('Mean Lap Time (seconds)', fontsize=12)
ax.set_title('Damper Sweep Analysis: Lap Time vs High-Speed Compression Activity', fontsize=14)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/damper_sweep_laptime_correlation.png', dpi=300, bbox_inches='tight')
plt.show()

print("Damper Sweep Summary:")
print(sweep_df[['clicks', 'mean_lap_time', 'mean_hs_compression_time']].to_string(index=False))
```

Execute the script to generate the correlation plot and statistical summary. The results reveal a nonlinear relationship between high-speed compression adjuster setting and lap time performance: the baseline 14-click setting yields a mean lap time of 112.82 seconds, increasing to 16 clicks degrades lap time to 113.21 seconds, while decreasing to 12 clicks improves lap time to 112.58 seconds. Further decreasing to 10 clicks degrades lap time to 113.05 seconds, indicating that excessive softening of the high-speed compression damping allows uncontrolled suspension motion that compromises platform stability. The optimal configuration emerges at 12 clicks, representing a two-click reduction from baseline that improves lap time by 0.24 seconds through enhanced transient response during rapid weight transfer events.

Validate the damper adjustment conclusion through driver feedback correlation by reviewing the driver debrief notes recorded during the test session. The debrief documentation for the 12-click configuration reports: "Initial turn-in response improved, car rotates more freely on entry. Mid-corner platform feels slightly softer over curbing but not loose. High-speed sweeper balance neutral to slight understeer, acceptable." The debrief for the 16-click configuration reports: "Initial turn-in feels sluggish, have to wait for the car to respond to steering input. Mid-corner platform very stable but car won't rotate, pushing understeer in high-speed turns." This qualitative feedback aligns precisely with the quantitative telemetry analysis: reducing high-speed compression damping from 14 to 12 clicks improves transient response by allowing more rapid damper shaft velocity during initial weight transfer, enhancing front axle load generation and turn-in authority.

Address the residual mid-corner understeer complaint through anti-roll bar analysis by comparing roll angle distributions between the 12-click damper configuration and a proposed modification to front anti-roll bar stiffness. Load the telemetry data from the 12-click configuration fastest lap and insert a Math Channel to compute chassis roll angle from the suspension travel differential. Configure the channel formula as `atan(('Susp_Travel_FR' - 'Susp_Travel_FL') / track_width) * 180 / pi`, where `track_width` is defined as 1.650 meters for the GT3 vehicle. Add this derived roll angle channel to a new trace in the worksheet and zoom into the high-speed sweeper complex spanning Turns 2 through 5 (distance range 3400 to 4300 meters).

The roll angle trace during the Turn 2-3 Esses reveals a peak roll angle of 2.8 degrees to the right, sustained throughout the mid-corner phase from 3480 to 3550 meters. Overlay the lateral acceleration channel on a second trace to correlate roll angle with lateral load. The peak lateral acceleration of 1.92 G occurs at 3510 meters, coinciding with the peak roll angle. The ratio of roll angle to lateral acceleration, computed as 2.8 degrees / 1.92 G = 1.46 degrees per G, provides a scalar metric for overall chassis roll stiffness. This roll gradient can be decomposed into contributions from spring stiffness, anti-roll bar stiffness, and tire vertical stiffness through the relationship:

$$\phi_{\text{roll gradient}} = \frac{m \cdot h \cdot g}{K_{\phi\text{,front}} + K_{\phi\text{,rear}}}$$

where $m$ is vehicle mass, $h$ is roll moment arm height (center of gravity height above roll axis), $g$ is gravitational acceleration, and $K_{\phi}$ terms represent front and rear roll stiffness contributions in units of Nm/deg. For the GT3 vehicle with mass 1285 kg and CG height 0.485 meters above the roll axis, the measured roll gradient of 1.46 deg/G implies a total roll stiffness of:

$$K_{\phi\text{,total}} = \frac{1285 \cdot 0.485 \cdot 9.81}{1.46 \cdot (\pi/180)} = 244\,800 \text{ Nm/deg}$$

The baseline anti-roll bar configuration with 28mm front blade and 32mm rear blade contributes approximately 120,000 Nm/deg front and 165,000 Nm/deg rear based on the manufacturer-supplied blade stiffness data. Increasing the front anti-roll bar to a 30mm blade would increase front roll stiffness to approximately 145,000 Nm/deg, shifting the roll stiffness distribution from 42 percent front / 58 percent rear to 47 percent front / 53 percent rear. This five-percentage-point increase in front roll stiffness distribution would transfer more lateral load to the front axle during steady-state cornering, increasing front tire slip angle and potentially addressing the mid-corner understeer condition without altering the transient damper response characteristics.

Simulate the anti-roll bar change using a simplified steady-state load transfer model implemented in Python:

```python
import numpy as np
import matplotlib.pyplot as plt

# Vehicle parameters
mass = 1285  # kg
wheelbase = 2.650  # meters
cg_height = 0.485  # meters above roll axis
static_front_weight_dist = 0.46  # 46% front
track_width_front = 1.650  # meters
track_width_rear = 1.620  # meters

# Baseline anti-roll bar stiffness
arb_front_baseline = 120000  # Nm/deg (28mm blade)
arb_rear_baseline = 165000  # Nm/deg (32mm blade)

# Proposed anti-roll bar stiffness
arb_front_proposed = 145000  # Nm/deg (30mm blade)
arb_rear_proposed = 165000  # Nm/deg (32mm rear, unchanged)

def compute_lateral_load_transfer(lateral_accel_g, arb_front, arb_rear):
    """Compute lateral load transfer distribution for given anti-roll bar stiffness."""
    lateral_accel = lateral_accel_g * 9.81  # m/s^2
    total_lateral_force = mass * lateral_accel
    
    # Total roll moment about roll axis
    roll_moment = total_lateral_force * cg_height
    
    # Roll stiffness distribution
    total_roll_stiffness = arb_front + arb_rear
    front_roll_fraction = arb_front / total_roll_stiffness
    rear_roll_fraction = arb_rear / total_roll_stiffness
    
    # Lateral load transfer at each axle
    front_load_transfer = front_roll_fraction * roll_moment / track_width_front
    rear_load_transfer = rear_roll_fraction * roll_moment / track_width_rear
    
    # Static axle loads
    static_front_load = mass * 9.81 * static_front_weight_dist
    static_rear_load = mass * 9.81 * (1 - static_front_weight_dist)
    
    # Front axle tire loads
    front_outside_load = (static_front_load / 2) + front_load_transfer
    front_inside_load = (static_front_load / 2) - front_load_transfer
    
    # Rear axle tire loads
    rear_outside_load = (static_rear_load / 2) + rear_load_transfer
    rear_inside_load = (static_rear_load / 2) - rear_load_transfer
    
    return {
        'front_outside': front_outside_load,
        'front_inside': front_inside_load,
        'rear_outside': rear_outside_load,
        'rear_inside': rear_inside_load,
        'front_load_transfer': front_load_transfer,
        'rear_load_transfer': rear_load_transfer
    }

# Compute load transfer for 1.92 G cornering
baseline_loads = compute_lateral_load_transfer(1.92, arb_front_baseline, arb_rear_baseline)
proposed_loads = compute_lateral_load_transfer(1.92, arb_front_proposed, arb_rear_proposed)

print("Lateral Load Transfer Analysis at 1.92 G")
print("=" * 50)
print(f"\nBaseline (28mm front / 32mm rear):")
print(f"  Front outside tire: {baseline_loads['front_outside']:.0f} N")
print(f"  Front inside tire:  {baseline_loads['front_inside']:.0f} N")
print(f"  Front load transfer: {baseline_loads['front_load_transfer']:.0f} N")
print(f"  Rear outside tire:  {baseline_loads['rear_outside']:.0f} N")
print(f"  Rear inside tire:   {baseline_loads['rear_inside']:.0f} N")
print(f"  Rear load transfer:  {baseline_loads['rear_load_transfer']:.0f} N")

print(f"\nProposed (30mm front / 32mm rear):")
print(f"  Front outside tire: {proposed_loads['front_outside']:.0f} N")
print(f"  Front inside tire:  {proposed_loads['front_inside']:.0f} N")
print(f"  Front load transfer: {proposed_loads['front_load_transfer']:.0f} N")
print(f"  Rear outside tire:  {proposed_loads['rear_outside']:.0f} N")
print(f"  Rear inside tire:   {proposed_loads['rear_inside']:.0f} N")
print(f"  Rear load transfer:  {proposed_loads['rear_load_transfer']:.0f} N")

print(f"\nDelta (Proposed - Baseline):")
print(f"  Front load transfer change: {proposed_loads['front_load_transfer'] - baseline_loads['front_load_transfer']:.0f} N")
print(f"  Rear load transfer change:  {proposed_loads['rear_load_transfer'] - baseline_loads['rear_load_transfer']:.0f} N")

# Plot tire load comparison
fig, ax = plt.subplots(figsize=(10, 6))
tire_positions = ['FL\nOutside', 'FL\nInside', 'FR\nOutside', 'FR\nInside', 
                  'RL\nOutside', 'RL\nInside', 'RR\nOutside', 'RR\nInside']
baseline_tire_loads = [
    baseline_loads['front_outside'], baseline_loads['front_inside'],
    baseline_loads['front_outside'], baseline_loads['front_inside'],
    baseline_loads['rear_outside'], baseline_loads['rear_inside'],
    baseline_loads['rear_outside'], baseline_loads['rear_inside']
]
proposed_tire_loads = [
    proposed_loads['front_outside'], proposed_loads['front_inside'],
    proposed_loads['front_outside'], proposed_loads['front_inside'],
    proposed_loads['rear_outside'], proposed_loads['rear_inside'],
    proposed_loads['rear_outside'], proposed_loads['rear_inside']
]

x = np.arange(len(tire_positions))
width = 0.35

ax.bar(x - width/2, baseline_tire_loads, width, label='Baseline (28mm front)', alpha=0.8)
ax.bar(x + width/2, proposed_tire_loads, width, label='Proposed (30mm front)', alpha=0.8)

ax.set_ylabel('Tire Vertical Load (N)', fontsize=12)
ax.set_xlabel('Tire Position', fontsize=12)
ax.set_title('Tire Load Distribution Comparison at 1.92 G Lateral Acceleration', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(tire_positions, fontsize=9)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/arb_tire_load_comparison.png', dpi=300, bbox_inches='tight')
plt.show()
```

The load transfer analysis output reveals that the proposed 30mm front anti-roll bar increases front axle lateral load transfer from 1842 N to 2134 N, an increase of 292 N per tire on the loaded outside front tire. This increased load transfer elevates the front tire slip angle operating point on the tire's force-versus-slip-angle curve, increasing front axle cornering force generation and shifting the vehicle balance toward reduced understeer. The rear axle load transfer decreases correspondingly from 2248 N to 1956 N, reducing rear tire slip angle and rear cornering force, which further contributes to the understeer reduction through increased relative front grip.

Formulate the final tuning recommendation by synthesizing the damper velocity histogram analysis and the anti-roll bar load transfer simulation. The optimal configuration addresses the driver's mid-corner understeer complaint through two synergistic adjustments: reduce front damper high-speed compression from 14 clicks to 12 clicks to improve transient turn-in response, and increase front anti-roll bar from 28mm to 30mm blade to increase steady-state front load transfer and mid-corner front grip. Document the recommendation in a formal setup change sheet:

```markdown
# Setup Change Recommendation

**Session:** Friday Practice Session 2
**Track:** Watkins Glen International
**Driver Feedback:** Mid-corner understeer in high-speed sweepers (Turns 2-3 Esses)

## Telemetry Diagnosis
- Damper velocity histogram analysis reveals 68% of suspension events occur in low-speed regime
- Current 14-click front HS compression setting limits transient turn-in response
- Roll angle analysis indicates roll gradient of 1.46 deg/G
- Front roll stiffness distribution at 42%, contributing to understeer balance

## Recommended Changes

### Front Damper High-Speed Compression
- **Current:** 14 clicks from full soft
- **Proposed:** 12 clicks from full soft
- **Rationale:** Improve transient response during initial weight transfer, allow higher peak damper velocity during turn-in
- **Expected lap time improvement:** 0.24 seconds (validated through sweep test)

### Front Anti-Roll Bar
- **Current:** 28mm blade (120,000 Nm/deg)
- **Proposed:** 30mm blade (145,000 Nm/deg)
- **Rationale:** Increase steady-state front load transfer from 1842 N to 2134 N (+292 N), shift roll stiffness distribution from 42% to 47% front
- **Expected effect:** Reduce mid-corner understeer, increase front tire slip angle 0.5-0.8 degrees

## Implementation Notes
- Front damper change: 2 clicks softer, complete adjustment in 30 seconds per corner
- Front ARB blade swap: remove existing 28mm blade, install 30mm blade with spanner torque 65 Nm
- Maintain all other suspension parameters unchanged
- Monitor tire temperatures after 3-lap run to validate load transfer change

## Validation Metrics
- Target minimum speed Turn 2-3 Esses: 142 km/h (currently 139 km/h)
- Target peak lateral acceleration: 1.95-2.00 G (currently 1.92 G)
- Front outside tire contact temp target: 95-100°C (currently 92°C)

---
**Engineer:** [Name]
**Date:** 2025-01-15
**Approved by:** Chief Engineer / Driver
```

## Exercise 3: Tire Temperature Analysis & Wear Modeling

The third operational verification exercise addresses tire thermal management and wear prediction, critical competencies for race engineers managing stint strategy and compound selection across multi-hour endurance events. Tire performance degrades through two distinct mechanisms: thermal degradation when the tire operates outside its optimal temperature window, and mechanical wear as tread rubber abrades through contact patch shear stress cycles. The exercise objective is to analyze tire temperature data collected via infrared pyrometer measurements across the contact patch width (inside, middle, outside positions), correlate temperature distributions with suspension geometry and load transfer characteristics, diagnose camber angle misalignment or excessive tire pressure, and construct a predictive wear model that estimates remaining tire life based on current degradation rate.

Begin by extracting the tire temperature dataset `watkins_glen_tire_thermal_dataset.zip` into the project directory. The archive contains tire pyrometer measurements collected at five-lap intervals throughout a 40-lap stint on Pirelli DHE compound slick tires, recording inside, middle, and outside contact patch temperatures for all four corners immediately upon pit entry. Each measurement point includes ambient air temperature, track surface temperature measured via infrared sensor, tire pressure recorded hot after the measurement stint, and cumulative lap count on the tire set. The dataset also includes telemetry data for representative laps within each measurement interval, enabling correlation between tire temperature distribution and suspension kinematics.

Load the tire temperature measurement log `tire_temperature_log.csv` into a Python analysis environment and compute the contact patch temperature spread as a diagnostic metric for camber angle and load transfer optimization:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Load tire temperature measurements
tire_temps = pd.read_csv('data/raw/tire_temperature_log.csv')

# Compute contact patch temperature spread
tire_temps['FL_spread'] = tire_temps['FL_outside'] - tire_temps['FL_inside']
tire_temps['FR_spread'] = tire_temps['FR_outside'] - tire_temps['FR_inside']
tire_temps['RL_spread'] = tire_temps['RL_outside'] - tire_temps['RL_inside']
tire_temps['RR_spread'] = tire_temps['RR_outside'] - tire_temps['RR_inside']

# Compute average contact patch temperature
tire_temps['FL_avg'] = (tire_temps['FL_inside'] + tire_temps['FL_middle'] + tire_temps['FL_outside']) / 3
tire_temps['FR_avg'] = (tire_temps['FR_inside'] + tire_temps['FR_middle'] + tire_temps['FR_outside']) / 3
tire_temps['RL_avg'] = (tire_temps['RL_inside'] + tire_temps['RL_middle'] + tire_temps['RL_outside']) / 3
tire_temps['RR_avg'] = (tire_temps['RR_inside'] + tire_temps['RR_middle'] + tire_temps['RR_inside']) / 3

print("Tire Temperature Analysis Summary")
print("=" * 70)
print(f"\nFront-Left Contact Patch Temperature Distribution:")
print(f"  Inside:  {tire_temps['FL_inside'].mean():.1f}°C (±{tire_temps['FL_inside'].std():.1f}°C)")
print(f"  Middle:  {tire_temps['FL_middle'].mean():.1f}°C (±{tire_temps['FL_middle'].std():.1f}°C)")
print(f"  Outside: {tire_temps['FL_outside'].mean():.1f}°C (±{tire_temps['FL_outside'].std():.1f}°C)")
print(f"  Average spread: {tire_temps['FL_spread'].mean():.1f}°C")

print(f"\nFront-Right Contact Patch Temperature Distribution:")
print(f"  Inside:  {tire_temps['FR_inside'].mean():.1f}°C (±{tire_temps['FR_inside'].std():.1f}°C)")
print(f"  Middle:  {tire_temps['FR_middle'].mean():.1f}°C (±{tire_temps['FR_middle'].std():.1f}°C)")
print(f"  Outside: {tire_temps['FR_outside'].mean():.1f}°C (±{tire_temps['FR_outside'].std():.1f}°C)")
print(f"  Average spread: {tire_temps['FR_spread'].mean():.1f}°C")

print(f"\nRear-Left Contact Patch Temperature Distribution:")
print(f"  Inside:  {tire_temps['RL_inside'].mean():.1f}°C (±{tire_temps['RL_inside'].std():.1f}°C)")
print(f"  Middle:  {tire_temps['RL_middle'].mean():.1f}°C (±{tire_temps['RL_middle'].std():.1f}°C)")
print(f"  Outside: {tire_temps['RL_outside'].mean():.1f}°C (±{tire_temps['RL_outside'].std():.1f}°C)")
print(f"  Average spread: {tire_temps['RL_spread'].mean():.1f}°C")

print(f"\nRear-Right Contact Patch Temperature Distribution:")
print(f"  Inside:  {tire_temps['RR_inside'].mean():.1f}°C (±{tire_temps['RR_inside'].std():.1f}°C)")
print(f"  Middle:  {tire_temps['RR_middle'].mean():.1f}°C (±{tire_temps['RR_middle'].std():.1f}°C)")
print(f"  Outside: {tire_temps['RR_outside'].mean():.1f}°C (±{tire_temps['RR_outside'].std():.1f}°C)")
print(f"  Average spread: {tire_temps['RR_spread'].mean():.1f}°C")

# Generate contact patch temperature visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for idx, (corner, ax) in enumerate(zip(['FL', 'FR', 'RL', 'RR'], axes.flatten())):
    inside_col = f'{corner}_inside'
    middle_col = f'{corner}_middle'
    outside_col = f'{corner}_outside'
    
    ax.plot(tire_temps['lap_number'], tire_temps[inside_col], 'b-o', label='Inside', markersize=6)
    ax.plot(tire_temps['lap_number'], tire_temps[middle_col], 'g-s', label='Middle', markersize=6)
    ax.plot(tire_temps['lap_number'], tire_temps[outside_col], 'r-^', label='Outside', markersize=6)
    
    # Optimal temperature window (compound-specific)
    ax.axhspan(85, 105, alpha=0.2, color='green', label='Optimal Window')
    
    ax.set_xlabel('Lap Number', fontsize=11)
    ax.set_ylabel('Temperature (°C)', fontsize=11)
    ax.set_title(f'{corner} Tire Contact Patch Temperature', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)

plt.suptitle('Tire Temperature Evolution Over 40-Lap Stint', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('figures/tire_temperature_evolution.png', dpi=300, bbox_inches='tight')
plt.show()
```

The temperature distribution analysis output reveals asymmetric contact patch loading patterns across the four corners. The front-left tire exhibits a mean temperature spread of 18.2°C with the outside edge consistently 18 degrees hotter than the inside edge, indicating excessive negative camber angle that concentrates load on the outside shoulder. The Pirelli DHE compound optimal operating window spans 85 to 105°C, and the front-left outside edge averages 108°C across the stint, exceeding the upper temperature limit and risking thermal degradation of the tread compound. The front-right tire shows a more balanced spread of 8.4°C, suggesting appropriate camber angle for the right-hand dominant layout of Watkins Glen which features seven right-hand corners versus four left-hand corners. The rear tires exhibit spreads of 6.2°C left and 7.8°C right, indicating well-balanced contact patch loading consistent with the lower lateral load transfer typical of rear axles in front-engine GT3 vehicles.

Diagnose the front-left camber angle misalignment by correlating the measured temperature spread with suspension kinematic camber gain. Load the telemetry data for lap 15, the midpoint of the stint where tire temperatures have stabilized, and extract the suspension travel data for the front-left corner during the high-speed right-hand sweeper complex of Turns 8-9. The telemetry indicates a peak suspension compression of 32mm during the 1.88 G cornering event, corresponding to a chassis roll angle of 2.6 degrees. Consulting the suspension kinematic analysis worksheet for the vehicle, the front-left suspension exhibits a kinematic camber gain coefficient of 0.85 degrees of negative camber per degree of chassis roll, yielding 2.2 degrees of additional negative camber during the cornering event. Adding this dynamic camber gain to the static camber setting of -3.2 degrees produces a total camber angle of -5.4 degrees during peak cornering load.

The excessive negative camber angle concentrates the tire contact patch load on the outside shoulder, elevating local shear stress and heat generation. The relationship between contact patch temperature distribution and camber angle follows an empirical correlation derived from tire thermal finite element models: for each degree of camber angle beyond the optimal value (approximately -2.8 degrees for the Pirelli DHE compound at 1.88 G lateral load), the outside edge temperature increases by approximately 7°C relative to the inside edge. The measured 18.2°C spread implies a 2.6-degree excess camber angle, aligning closely with the computed total camber of -5.4 degrees versus the optimal -2.8 degrees. Formulate a corrective action by reducing the static camber setting from -3.2 degrees to -2.6 degrees, yielding a total dynamic camber of -4.8 degrees under the same cornering load, a 0.6-degree reduction that should decrease the temperature spread to approximately 14°C and bring the outside edge temperature below the 105°C thermal degradation threshold.

Extend the tire temperature analysis to construct a predictive wear model based on contact patch thermal energy dissipation and mechanical abrasion cycles. Tire wear rate correlates strongly with average contact patch temperature through the Arrhenius equation for polymer degradation kinetics, which describes the exponential increase in chemical reaction rate with temperature. For racing slick compounds operating above the glass transition temperature (approximately 60°C), the wear rate $W$ in micrometers of tread depth loss per lap is approximated by:

$$W = W_0 \cdot \exp\left(\frac{E_a}{R} \left(\frac{1}{T_{\text{ref}}} - \frac{1}{T_{\text{avg}}}\right)\right)$$

where $W_0$ is the baseline wear rate at reference temperature $T_{\text{ref}} = 368$ K (95°C), $E_a$ is the activation energy for polymer degradation (approximately 45 kJ/mol for styrene-butadiene rubber compounds), $R$ is the universal gas constant 8.314 J/(mol·K), and $T_{\text{avg}}$ is the measured average contact patch temperature in Kelvin. Implement the wear prediction model in Python:

```python
def compute_tire_wear_rate(avg_temp_celsius, baseline_wear_rate=1.8, activation_energy=45000, ref_temp_celsius=95):
    """Compute tire wear rate using Arrhenius thermal degradation model."""
    R = 8.314  # J/(mol·K)
    T_avg = avg_temp_celsius + 273.15  # Convert to Kelvin
    T_ref = ref_temp_celsius + 273.15
    
    wear_rate = baseline_wear_rate * np.exp((activation_energy / R) * ((1 / T_ref) - (1 / T_avg)))
    return wear_rate

# Compute wear rates for each tire across the stint
tire_temps['FL_wear_rate'] = tire_temps['FL_avg'].apply(compute_tire_wear_rate)
tire_temps['FR_wear_rate'] = tire_temps['FR_avg'].apply(compute_tire_wear_rate)
tire_temps['RL_wear_rate'] = tire_temps['RL_avg'].apply(compute_tire_wear_rate)
tire_temps['RR_wear_rate'] = tire_temps['RR_avg'].apply(compute_tire_wear_rate)

# Compute cumulative wear
tire_temps['FL_cumulative_wear'] = (tire_temps['FL_wear_rate'] * 5).cumsum()  # 5 laps per measurement interval
tire_temps['FR_cumulative_wear'] = (tire_temps['FR_wear_rate'] * 5).cumsum()
tire_temps['RL_cumulative_wear'] = (tire_temps['RL_wear_rate'] * 5).cumsum()
tire_temps['RR_cumulative_wear'] = (tire_temps['RR_wear_rate'] * 5).cumsum()

# Tire specification: 6mm nominal tread depth, minimum legal depth 1mm
nominal_tread_depth = 6000  # micrometers
minimum_tread_depth = 1000  # micrometers
usable_tread_depth = nominal_tread_depth - minimum_tread_depth

# Predict remaining tire life
final_lap = tire_temps['lap_number'].max()
final_wear_FL = tire_temps.loc[tire_temps['lap_number'] == final_lap, 'FL_cumulative_wear'].values[0]
final_wear_FR = tire_temps.loc[tire_temps['lap_number'] == final_lap, 'FR_cumulative_wear'].values[0]
final_wear_RL = tire_temps.loc[tire_temps['lap_number'] == final_lap, 'RL_cumulative_wear'].values[0]
final_wear_RR = tire_temps.loc[tire_temps['lap_number'] == final_lap, 'RR_cumulative_wear'].values[0]

avg_wear_rate_FL = tire_temps['FL_wear_rate'].mean()
avg_wear_rate_FR = tire_temps['FR_wear_rate'].mean()
avg_wear_rate_RL = tire_temps['RL_wear_rate'].mean()
avg_wear_rate_RR = tire_temps['RR_wear_rate'].mean()

remaining_laps_FL = (usable_tread_depth - final_wear_FL) / avg_wear_rate_FL
remaining_laps_FR = (usable_tread_depth - final_wear_FR) / avg_wear_rate_FR
remaining_laps_RL = (usable_tread_depth - final_wear_RL) / avg_wear_rate_RL
remaining_laps_RR = (usable_tread_depth - final_wear_RR) / avg_wear_rate_RR

print(f"\n{'='*70}")
print("Tire Wear Prediction Model")
print(f"{'='*70}")
print(f"\nCumulative wear after {final_lap} laps:")
print(f"  FL: {final_wear_FL:.0f} μm  ({(final_wear_FL/usable_tread_depth)*100:.1f}% of usable depth)")
print(f"  FR: {final_wear_FR:.0f} μm  ({(final_wear_FR/usable_tread_depth)*100:.1f}% of usable depth)")
print(f"  RL: {final_wear_RL:.0f} μm  ({(final_wear_RL/usable_tread_depth)*100:.1f}% of usable depth)")
print(f"  RR: {final_wear_RR:.0f} μm  ({(final_wear_RR/usable_tread_depth)*100:.1f}% of usable depth)")

print(f"\nPredicted remaining tire life:")
print(f"  FL: {remaining_laps_FL:.0f} laps")
print(f"  FR: {remaining_laps_FR:.0f} laps")
print(f"  RL: {remaining_laps_RL:.0f} laps")
print(f"  RR: {remaining_laps_RR:.0f} laps")
print(f"\nLimiting tire: {'FL' if remaining_laps_FL == min(remaining_laps_FL, remaining_laps_FR, remaining_laps_RL, remaining_laps_RR) else 'FR' if remaining_laps_FR == min(remaining_laps_FL, remaining_laps_FR, remaining_laps_RL, remaining_laps_RR) else 'RL' if remaining_laps_RL == min(remaining_laps_FL, remaining_laps_FR, remaining_laps_RL, remaining_laps_RR) else 'RR'} at {min(remaining_laps_FL, remaining_laps_FR, remaining_laps_RL, remaining_laps_RR):.0f} laps")

# Visualize cumulative wear progression
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(tire_temps['lap_number'], tire_temps['FL_cumulative_wear'], 'b-o', label='FL', linewidth=2, markersize=6)
ax.plot(tire_temps['lap_number'], tire_temps['FR_cumulative_wear'], 'r-s', label='FR', linewidth=2, markersize=6)
ax.plot(tire_temps['lap_number'], tire_temps['RL_cumulative_wear'], 'g-^', label='RL', linewidth=2, markersize=6)
ax.plot(tire_temps['lap_number'], tire_temps['RR_cumulative_wear'], 'm-d', label='RR', linewidth=2, markersize=6)

ax.axhline(usable_tread_depth, color='red', linestyle='--', linewidth=2, label='Usable Tread Depth Limit')

ax.set_xlabel('Lap Number', fontsize=12)
ax.set_ylabel('Cumulative Wear (μm)', fontsize=12)
ax.set_title('Tire Wear Progression with Predictive Model', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/tire_wear_prediction.png', dpi=300, bbox_inches='tight')
plt.show()
```

The wear prediction model output indicates that after 40 laps, the front-left tire has accumulated 1842 micrometers of wear (36.8% of usable tread depth), projecting a remaining life of 63 additional laps before reaching the minimum legal tread depth. The front-right tire shows 1523 micrometers of wear with 78 laps remaining, the rear-left 1156 micrometers with 105 laps remaining, and rear-right 1298 micrometers with 92 laps remaining. The front-left tire emerges as the limiting factor for stint duration, consistent with the elevated contact patch temperatures resulting from excessive camber angle. Implementing the proposed static camber reduction from -3.2 to -2.6 degrees would reduce the average contact patch temperature from 101°C to approximately 96°C, decreasing the predicted wear rate from 2.46 μm/lap to 1.96 μm/lap through the exponential temperature sensitivity of the Arrhenius model, extending the front-left tire life from 63 to 79 additional laps and bringing it into balance with the front-right tire.

Validate the wear model predictions through physical tread depth measurements using a digital depth gauge. The tire specification documents nominal new tread depth of 6.0mm with measurement uncertainty ±0.1mm. After the 40-lap stint, measure tread depth at three circumferential positions (0°, 120°, 240° around the tire) and three lateral positions (inside edge 25mm from sidewall, center, outside edge 25mm from sidewall) for a total of nine measurements per tire. Average the nine measurements to compute mean remaining tread depth and compare against the model prediction:

```
Front-Left Measured Mean Tread Depth: 4.12 mm (±0.08 mm)
  Predicted wear: 1.84 mm
  Measured wear: 1.88 mm
  Model error: +2.1%

Front-Right Measured Mean Tread Depth: 4.42 mm (±0.06 mm)
  Predicted wear: 1.52 mm
  Measured wear: 1.58 mm
  Model error: +3.8%

Rear-Left Measured Mean Tread Depth: 4.79 mm (±0.05 mm)
  Predicted wear: 1.16 mm
  Measured wear: 1.21 mm
  Model error: +4.1%

Rear-Right Measured Mean Tread Depth: 4.65 mm (±0.07 mm)
  Predicted wear: 1.30 mm
  Measured wear: 1.35 mm
  Model error: +3.7%
```

The measured tread depth values validate the wear prediction model with errors below 5% across all four corners, confirming the applicability of the Arrhenius thermal degradation framework for in-race tire life estimation. The slightly conservative model predictions (overpredicting wear by 2-4%) provide an appropriate safety margin for race strategy decisions, ensuring that tire change intervals do not extend beyond actual tire capability.

## Race Engineering Diagnostic Cheat Sheet & Setup Matrix

The operational verification laboratory concludes with the synthesis of diagnostic procedures and setup optimization heuristics into a consolidated reference guide suitable for trackside deployment during race weekends. The diagnostic cheat sheet encapsulates the systematic troubleshooting workflow developed through the three exercises: telemetry trace correlation for driver coaching, damper velocity histogram analysis for transient response optimization, and tire temperature interpretation for thermal management and wear prediction. The setup matrix provides decision trees mapping driver feedback symptoms to specific mechanical adjustments quantified in damper clicks, anti-roll bar blade selections, and static camber angle changes.

### Telemetry Diagnostic Workflow

**Driver Trace Correlation Protocol (Exercise 1 Application):**

1. Identify performance delta magnitude and corner-specific concentration through full-lap comparison of reference and target driver fastest laps
2. Zoom into deficit-dominant corner and overlay five critical channels: Speed, Brake Pressure, Throttle Position, Steering Angle, Lateral Acceleration
3. Compute Channel Report statistics for corner entry zone (brake application point to apex): minimum speed, maximum brake pressure, maximum steering angle, mean lateral acceleration
4. Analyze brake release gradient using distance-domain derivative of brake pressure channel: steep gradient (>8 bar/m) indicates aggressive release technique, shallow gradient (< 5 bar/m) indicates conservative trailing brake deep into corner
5. Correlate minimum corner speed with brake release timing: earlier brake release enables earlier throttle application and higher mid-corner speed
6. Quantify throttle application timing differential using conditional longitudinal acceleration channel filtering throttle position >10%
7. Generate driver coaching report documenting: lap time delta, corner-specific speed deltas (minimum speed), control input timing deltas (brake release distance, throttle application distance), recommended technique adjustments

**Damper Tuning Diagnostic Protocol (Exercise 2 Application):**

1. Construct damper velocity histogram for each corner covering full lap distance with 0.05 m/s bin width and -2.0 to +2.0 m/s range
2. Compute percentage of suspension events in low-speed regime (< 0.15 m/s) vs high-speed regime (>0.15 m/s) to identify dominant damping force regime
3. For driver feedback reporting sluggish turn-in or delayed transient response: reduce high-speed compression damping 2-4 clicks to increase peak shaft velocity during initial weight transfer
4. For driver feedback reporting excessive mid-corner platform motion or instability over curbing: increase high-speed compression damping 2-4 clicks to limit peak shaft velocity during rapid transient events
5. For driver feedback reporting harsh ride quality or suspension topping out: reduce high-speed compression damping and verify adequate suspension travel margin (minimum 15mm to bump stop under peak compression)
6. Validate damper adjustment through lap time correlation: compare mean lap time before and after adjustment across minimum 5-lap sample to establish statistical significance (p< 0.05 via Student's t-test)

**Tire Temperature Diagnostic Protocol (Exercise 3 Application):**

1. Measure contact patch temperatures (inside, middle, outside) within 60 seconds of pit entry using calibrated infrared pyrometer held 25mm from tire surface
2. Record tire pressure hot using digital gauge with 0.1 psi resolution immediately following temperature measurement
3. Compute contact patch temperature spread: $\Delta T = T_{\text{outside}} - T_{\text{inside}}$
4. Interpret spread magnitude:
   - $|\Delta T| < 5°C$: Optimal contact patch loading, no camber adjustment required
   - $5°C < |\Delta T| < 12°C$: Acceptable contact patch loading, monitor for thermal degradation
   - $12°C < |\Delta T| < 20°C$: Suboptimal contact patch loading, camber adjustment recommended
   - $|\Delta T| > 20°C$: Severe contact patch loading imbalance, immediate camber adjustment mandatory
5. Determine camber adjustment direction: positive spread (outside hotter) indicates excessive negative camber, reduce static camber by $(\Delta T / 7°C)$ degrees; negative spread (inside hotter) indicates insufficient negative camber, increase static camber
6. Monitor average contact patch temperature relative to compound-specific optimal window: Pirelli DHE 85-105°C, Michelin Sport Cup 90-110°C, Goodyear Eagle F1 80-100°C
7. For average temperature above optimal window: reduce tire pressure 0.5-1.0 psi to increase contact patch area and distribute heat generation, reduce camber angle to balance contact patch loading
8. For average temperature below optimal window: increase tire pressure 0.5-1.0 psi to concentrate contact patch loading and elevate shear stress, increase driving aggression to generate additional slip energy
9. Apply tire wear prediction model using measured temperatures to estimate remaining tire life and inform stint strategy

### Setup Optimization Matrix

**Understeer Correction Hierarchy:**

*Driver feedback: "Car pushing / won't turn / front end sliding"*

**Step 1 - Static Setup Changes (implement before on-track verification):**
- Increase front anti-roll bar one blade size (e.g., 28mm → 30mm) to increase front roll stiffness distribution by 5 percentage points
- Reduce front tire pressure 0.5-1.0 psi to increase front contact patch area and mechanical grip
- Reduce front damper low-speed compression 2 clicks to allow more weight transfer to front axle during initial turn-in
- Increase rear anti-roll bar one blade size to reduce rear roll stiffness distribution (use only if front ARB already at maximum available stiffness)

**Step 2 - Aerodynamic Balance Adjustment (if available and Step 1 insufficient):**
- Increase front wing angle 0.5-1.0 degrees to increase front downforce and mechanical front tire loading
- Reduce rear wing angle 0.5-1.0 degrees to reduce rear downforce (use only if front wing already at maximum allowed angle)

**Step 3 - Advanced Geometry Changes (consult chief engineer, requires alignment rack):**
- Reduce front static camber 0.3-0.5 degrees to increase front contact patch mechanical grip at expense of ultimate cornering limit
- Increase front toe-out 0.05-0.10 degrees total to improve turn-in response

**Oversteer Correction Hierarchy:**

*Driver feedback: "Car loose / rear end unstable / spinning out"*

**Step 1 - Static Setup Changes:**
- Increase rear anti-roll bar one blade size to increase rear roll stiffness distribution by 5 percentage points
- Reduce rear tire pressure 0.5-1.0 psi to increase rear contact patch area
- Reduce rear damper low-speed compression 2 clicks to allow more weight transfer to rear axle
- Reduce front anti-roll bar one blade size to increase front roll stiffness distribution (use only if rear ARB already at maximum stiffness)

**Step 2 - Aerodynamic Balance Adjustment:**
- Increase rear wing angle 0.5-1.0 degrees to increase rear downforce
- Reduce front wing angle 0.5 degrees if rear wing at maximum allowed angle

**Step 3 - Advanced Geometry Changes:**
- Reduce rear static camber 0.3-0.5 degrees
- Increase rear toe-in 0.05-0.10 degrees total to improve straight-line stability

**Transient Response Tuning:**

*Driver feedback: "Car slow to respond / sluggish turn-in / delayed reaction"*

**Primary adjustment:** Reduce front high-speed compression damping 2-4 clicks to allow higher peak damper shaft velocity during initial weight transfer, improving front axle load generation rate

*Driver feedback: "Car darty / nervous / too responsive / difficult to place"*

**Primary adjustment:** Increase front high-speed compression damping 2-4 clicks to limit peak damper shaft velocity, slowing front axle load generation rate and providing more progressive response

**Ride Quality Optimization:**

*Driver feedback: "Harsh ride / suspension topping out / losing contact over curbs"*

**Step 1:** Reduce high-speed compression damping 2 clicks front and rear
**Step 2:** Reduce spring rate one step if available (e.g., 65 N/mm → 60 N/mm)
**Step 3:** Verify suspension travel margin, target minimum 15mm to bump stop under peak compression event

*Driver feedback: "Car floating / soft platform / excessive body motion"*

**Step 1:** Increase low-speed compression damping 2 clicks front and rear
**Step 2:** Increase spring rate one step if available
**Step 3:** Verify roll stiffness distribution appropriate for track layout (40-45% front for balanced tracks)

**Tire Thermal Management Strategy:**

*Measured front tire average temperature >105°C (Pirelli DHE compound):*
- Reduce front tire pressure 1.0 psi
- Reduce front static camber 0.5 degrees to distribute contact patch loading
- Reduce front damper compression settings 2 clicks to soften transient load spikes
- Coach driver to reduce slip angle in high-speed corners, prioritize maintenance throttle over peak lateral acceleration

*Measured rear tire average temperature < 85°C:*
- Increase rear tire pressure 1.0 psi to concentrate contact patch loading
- Reduce rear anti-roll bar one blade size to increase rear roll angle and mechanical load transfer
- Coach driver to increase entry speed and maintain higher throttle through mid-corner to generate additional rear tire slip energy

This consolidated diagnostic cheat sheet and setup optimization matrix provides the race engineer with a systematic framework for translating telemetry data, driver feedback, and tire temperature measurements into specific, quantified mechanical adjustments. The hierarchical structure prioritizes high-impact, reversible changes before progressing to more invasive geometry modifications that require specialized alignment equipment and extended setup time. Application of this methodology during race weekend practice sessions enables rapid convergence toward optimal vehicle setup while maintaining traceability of all configuration changes through detailed documentation in the setup change log.
