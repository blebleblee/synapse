# Operational Verification Labs: Aerodynamics

## Objective & Laboratory Bench Setup

Aerodynamics is not an abstract discipline — it lives in the pressure differential between a wing's upper and lower surface, in the turbulent wake shedding from a bluff body, and in the precise relationship between fluid velocity and the forces that lift aircraft off the ground. This laboratory guide is designed for the working experimental scientist who wants to move beyond textbook illustrations and develop genuine empirical fluency: the ability to set up an apparatus, collect trustworthy data, propagate measurement uncertainty rigorously, and produce publication-quality analysis using Python's scientific stack.

The theoretical skeleton underlying every exercise here is the Navier-Stokes equation for incompressible flow,

$$\rho \left(\frac{\partial \vec{u}}{\partial t} + (\vec{u} \cdot \nabla)\vec{u}\right) = -\nabla p + \mu \nabla^2 \vec{u} + \rho \vec{g}$$

where $\rho$ is fluid density ($\text{kg/m}^3$), $\vec{u}$ is the velocity field ($\text{m/s}$), $p$ is static pressure ($\text{Pa}$), and $\mu$ is dynamic viscosity ($\text{Pa·s}$). In the limit where viscous forces are negligible relative to inertial forces, this reduces to the Euler equation, and in irrotational steady flow it collapses further into Bernoulli's principle — the workhorse of introductory aerodynamics. But understanding *why* Bernoulli applies (and when it fails) requires direct observation of the flow physics, not just equation manipulation.

The dimensionless Reynolds number governs whether a flow regime is laminar or turbulent:

$$Re = \frac{\rho u L}{\mu}$$

where $L$ is a characteristic length scale (chord length for an airfoil, diameter for a cylinder). Below $Re \approx 10^3$ the flow remains orderly and laminar; above $Re \approx 10^5$ for bluff bodies and $Re \approx 5 \times 10^5$ along flat plates, turbulent transition occurs. Every experiment in this guide is calibrated around measuring or controlling $Re$ explicitly.

**Physical Laboratory Apparatus.** The core instrument is a low-speed subsonic wind tunnel with a working section of at least $300 \times 300$ mm and a velocity range of 2–25 m/s. Mount a pitot-static probe (connected to a differential manometer or a Honeywell HSCDRRN002ND2A3 digital differential pressure sensor, range 0–500 Pa) on a traverse mechanism so it can be positioned to within 0.5 mm in both $y$ and $z$ directions. For force measurement, a two-component strain-gauge balance capable of resolving lift and drag forces in the range 0–10 N with 0.01 N resolution is required. Airfoil models should be NACA 0012 or NACA 4412 symmetric/cambered profiles, chord length $c = 150$ mm, printed or machined to a surface roughness below $Ra = 1.6\ \mu\text{m}$. Surface pressure taps (0.5 mm diameter, 15–20 distributed along chord) connected via Scanivalve to a single pressure transducer allow full $C_p$ distribution mapping.

For flow visualization, a smoke wire rig (nichrome wire, 0.1 mm diameter, coated with mineral oil, energized at 2–4 A) positioned upstream of the test section produces laminar smoke filaments that reveal separation and reattachment. Alternatively, oil-film visualization (mixture of titanium dioxide, oleic acid, and kerosene in 10:3:87 ratio by volume applied to the model surface) captures the skin-friction topology directly on the model surface under running tunnel conditions.

**Software and Sensor Telemetry Environment.** All data acquisition and analysis in this guide runs on Python 3.10+ with the following verified stack. Confirm your environment is correctly configured before beginning any exercise:

```bash
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
```

If any import fails, install via:

```bash
pip install numpy==1.26.4 scipy==1.13.0 matplotlib==3.8.4
```

Sensor telemetry from the differential pressure transducer is read over USB-Serial using a data acquisition board (NI USB-6001 or equivalent, 12-bit ADC, ±10 V range). The strain-gauge balance analog output is amplified through an instrumentation amplifier (INA128, gain = 100) before digitization. Sampling rate for all channels is set at 1000 Hz; each steady-state measurement averages 5000 samples (5 seconds) to suppress turbulent fluctuations and electronic noise.

---

## Exercise 1: Empirical Observation & Measurement Protocol

### Pitot-Static Velocity Survey and Bernoulli Verification

The goal of this first exercise is deceptively simple: measure the freestream dynamic pressure in the wind tunnel's working section, compute the corresponding flow velocity using Bernoulli's equation, and verify that the relationship holds across the full operating range of the tunnel. In doing so you will characterize the tunnel's flow uniformity, establish a calibration baseline for all subsequent experiments, and develop hands-on confidence with differential pressure instrumentation.

**Physical Setup.** Install the pitot-static probe on the traverse, aligned with the tunnel centerline with the probe tip facing directly into the oncoming flow. The probe axis must be within 2° of the flow direction — misalignment beyond 5° introduces cosine errors exceeding 0.4% in dynamic pressure, which compound into 0.2% velocity error. Connect the total pressure port (forward-facing orifice) to the high-pressure port of your differential transducer, and the static pressure port (side-wall orifices, 8 diameters downstream of the tip) to the low-pressure port. Zero the transducer with the tunnel off and all ports open to atmosphere, verifying that the digital readout holds within ±0.1 Pa for 60 seconds before recording the zero offset $p_0$.

Bernoulli's principle along a streamline in steady, incompressible, inviscid flow gives:

$$p_{total} = p_{static} + \frac{1}{2}\rho u^2$$

The differential pressure measured by the probe is therefore the dynamic pressure $q_\infty = p_{total} - p_{static} = \frac{1}{2}\rho u^2$, so the freestream velocity is:

$$u_\infty = \sqrt{\frac{2 q_\infty}{\rho}}$$

Atmospheric density $\rho$ must be computed from the ideal gas law using the ambient temperature $T$ (K) and barometric pressure $P_{atm}$ (Pa):

$$\rho = \frac{P_{atm}}{R_{specific} \cdot T}, \quad R_{specific} = 287.05\ \text{J kg}^{-1}\text{K}^{-1}$$

Record $P_{atm}$ from a calibrated Vaisala PTB330 barometer (or equivalent) and $T$ from a platinum resistance thermometer (PT100) mounted in the settling chamber, shielded from radiation. These two ambient readings must be logged at the beginning and end of every tunnel run; if they drift by more than 1 hPa or 1 K respectively during a run, the data should be discarded and the run repeated.

**Procedure.** Set the tunnel fan controller to eight discrete voltage setpoints corresponding to nominal tunnel speeds of 3, 5, 8, 10, 12, 15, 18, and 22 m/s (determined from prior calibration curves or the tunnel manufacturer's performance map). At each setpoint, allow 90 seconds for the flow to stabilize, then acquire 5000 samples at 1000 Hz from the differential pressure transducer. Record $T$ and $P_{atm}$ at each condition. Additionally, perform a spatial survey at 12 m/s: traverse the probe in a $5 \times 5$ grid covering the full $300 \times 300$ mm working section cross-plane at 60 mm intervals, acquiring 2000 samples per point. This grid survey reveals tunnel non-uniformity and quantifies the boundary layer growth on the tunnel walls.

**Data Acquisition and Bernoulli Verification Code.** The following script reads pressure data files exported from your DAQ system (each file is a single-column CSV of raw voltage values in volts), applies the sensor calibration, computes velocity, and produces both a velocity-vs-setpoint verification curve and the spatial flow uniformity contour map.

```python
#!/usr/bin/env python3
"""
Exercise 1: Pitot-static velocity survey and Bernoulli verification.

Data files assumed format:
  - centerline_<speed_index>.csv : 5000-row single-column voltage arrays
  - grid_<row>_<col>.csv         : 2000-row single-column voltage arrays
  
Sensor calibration: Honeywell HSCDRRN002ND2A3
  Full-scale output: 90% of supply = 0.9 * Vcc, full-scale range = 500 Pa
  Transfer function: p_diff (Pa) = (V_out/Vcc - 0.1) / 0.8 * 500
  Vcc = 3.3 V
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats
from pathlib import Path

# ── Physical constants and sensor parameters ──────────────────────────────────
R_SPECIFIC   = 287.05          # J/(kg·K), specific gas constant for dry air
VCC          = 3.3             # V, sensor supply voltage
P_SCALE      = 500.0           # Pa, full-scale differential pressure
SENSOR_GAIN  = 100.0           # INA128 amplifier gain (dimensionless)
ADC_VREF     = 10.0            # V, DAQ ADC reference voltage (±10 V range)
ADC_BITS     = 12              # bit depth
ADC_COUNTS   = 2**ADC_BITS     # 4096

# ── Ambient conditions (replace with actual logged values) ────────────────────
# Logged at start of session using Vaisala PTB330 and PT100 thermometer
P_ATM_PA     = 101325.0        # Pa (example: standard atmosphere)
T_AMBIENT_K  = 293.15          # K  (example: 20.0 °C)

# ── Nominal tunnel setpoints (m/s) for labeling ───────────────────────────────
NOMINAL_SPEEDS = np.array([3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 22.0])

# ── Spatial grid parameters ───────────────────────────────────────────────────
GRID_ROWS    = 5               # number of traverse positions in y
GRID_COLS    = 5               # number of traverse positions in z
GRID_SPACING = 60.0            # mm between grid points

def adc_counts_to_volts(counts_array: np.ndarray) -> np.ndarray:
    """Convert 12-bit ADC integer counts to amplifier output voltage."""
    return (counts_array / (ADC_COUNTS - 1)) * 2 * ADC_VREF - ADC_VREF

def amplifier_to_sensor_voltage(v_amp: np.ndarray) -> np.ndarray:
    """Remove INA128 gain to recover sensor output voltage."""
    return v_amp / SENSOR_GAIN

def sensor_voltage_to_pressure(v_sensor: np.ndarray) -> np.ndarray:
    """
    Apply Honeywell HSCDRRN002ND2A3 transfer function.
    p_diff = ((V_out / Vcc) - 0.1) / 0.8 * P_SCALE
    """
    return ((v_sensor / VCC) - 0.1) / 0.8 * P_SCALE

def pressure_to_velocity(q_Pa: float, rho: float) -> float:
    """Bernoulli: u = sqrt(2q/rho). Returns velocity in m/s."""
    q_clipped = max(q_Pa, 0.0)   # dynamic pressure must be non-negative
    return np.sqrt(2.0 * q_clipped / rho)

def compute_air_density(P_atm: float, T_K: float) -> float:
    """Ideal gas law: rho = P/(R_specific * T)."""
    return P_atm / (R_SPECIFIC * T_K)

def load_and_process_csv(filepath: Path, zero_offset_Pa: float,
                          rho: float) -> dict:
    """
    Load a DAQ voltage CSV, convert to dynamic pressure and velocity.
    Returns dict with keys: q_mean, q_std, u_mean, u_std, n_samples.
    """
    raw_counts = np.loadtxt(filepath, delimiter=',')
    v_amp      = adc_counts_to_volts(raw_counts)
    v_sensor   = amplifier_to_sensor_voltage(v_amp)
    q_raw      = sensor_voltage_to_pressure(v_sensor)
    q_corrected = q_raw - zero_offset_Pa

    # Sample statistics
    q_mean = float(np.mean(q_corrected))
    q_std  = float(np.std(q_corrected, ddof=1))
    u_mean = pressure_to_velocity(q_mean, rho)

    # Velocity uncertainty via error propagation: u = sqrt(2q/rho)
    # du/dq = 1/(2u) * 2/rho = 1/(rho*u)  =>  sigma_u = sigma_q / (rho * u)
    u_std  = q_std / (rho * u_mean) if u_mean > 0.01 else 0.0

    return {
        'q_mean': q_mean, 'q_std': q_std,
        'u_mean': u_mean, 'u_std': u_std,
        'n_samples': len(raw_counts)
    }

def bernoulli_verification_plot(nominal: np.ndarray, measured: np.ndarray,
                                  u_err: np.ndarray, rho: float,
                                  save_path: Path):
    """
    Plot measured velocity vs nominal tunnel speed with Bernoulli prediction,
    linear regression, and 95% confidence band.
    """
    # Linear regression: measured = slope * nominal + intercept
    slope, intercept, r_value, p_value, se = stats.linregress(nominal, measured)

    x_fit  = np.linspace(nominal.min() * 0.9, nominal.max() * 1.05, 200)
    y_fit  = slope * x_fit + intercept

    # 95% CI on the regression line
    n      = len(nominal)
    x_mean = nominal.mean()
    s_xx   = np.sum((nominal - x_mean)**2)
    t_crit = stats.t.ppf(0.975, df=n-2)
    ci     = t_crit * se * np.sqrt(1/n + (x_fit - x_mean)**2 / s_xx)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(x_fit, x_fit, 'k--', lw=1.0, label='Ideal: $u_{meas} = u_{nom}$')
    ax.fill_between(x_fit, y_fit - ci, y_fit + ci,
                    alpha=0.15, color='steelblue', label='95% CI regression')
    ax.plot(x_fit, y_fit, '-', color='steelblue', lw=1.5,
            label=f'Lin. fit: slope={slope:.4f}, $R^2$={r_value**2:.5f}')
    ax.errorbar(nominal, measured, yerr=2*u_err, fmt='o',
                color='firebrick', capsize=4, ms=5, zorder=5,
                label='Measured ± 2σ (95%)')

    ax.set_xlabel('Nominal Tunnel Speed (m/s)', fontsize=12)
    ax.set_ylabel('Pitot-Measured Velocity (m/s)', fontsize=12)
    ax.set_title(f'Bernoulli Velocity Verification\n'
                 f'Air density: $\\rho$ = {rho:.4f} kg/m³', fontsize=13)
    ax.legend(fontsize=10)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(True, which='major', alpha=0.4)
    ax.grid(True, which='minor', alpha=0.15)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    print(f"  → Bernoulli plot saved: {save_path}")
    print(f"    Regression slope = {slope:.5f}  (ideal = 1.0000)")
    print(f"    R² = {r_value**2:.6f}")

def flow_uniformity_contour(grid_velocities: np.ndarray, spacing_mm: float,
                             save_path: Path):
    """
    Plot 2D contour map of pitot velocity across the tunnel cross-section.
    grid_velocities shape: (GRID_ROWS, GRID_COLS).
    """
    rows, cols = grid_velocities.shape
    y_coords   = np.arange(rows) * spacing_mm - (rows - 1) * spacing_mm / 2
    z_coords   = np.arange(cols) * spacing_mm - (cols - 1) * spacing_mm / 2
    Z, Y       = np.meshgrid(z_coords, y_coords)

    u_mean_field = grid_velocities.mean()
    non_uniformity = (grid_velocities.max() - grid_velocities.min()) / u_mean_field * 100

    fig, ax = plt.subplots(figsize=(7, 6))
    cf = ax.contourf(Z, Y, grid_velocities, levels=20, cmap='RdYlBu_r')
    cs = ax.contour(Z, Y, grid_velocities, levels=10,
                    colors='k', linewidths=0.5, alpha=0.6)
    ax.clabel(cs, fmt='%.2f', fontsize=7)
    cbar = fig.colorbar(cf, ax=ax, shrink=0.9)
    cbar.set_label('Local velocity (m/s)', fontsize=11)

    # Mark working section boundary
    rect = plt.Rectangle((-150, -150), 300, 300,
                          fill=False, edgecolor='white', lw=2, ls='--')
    ax.add_patch(rect)

    ax.set_xlabel('Z — lateral (mm)', fontsize=11)
    ax.set_ylabel('Y — vertical (mm)', fontsize=11)
    ax.set_title(f'Tunnel Flow Uniformity at $u_\\infty$ ≈ 12 m/s\n'
                 f'Non-uniformity: {non_uniformity:.2f}%  '
                 f'($\\bar{{u}}$ = {u_mean_field:.3f} m/s)', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    print(f"  → Uniformity contour saved: {save_path}")
    print(f"    Flow non-uniformity: {non_uniformity:.2f}%  "
          f"(acceptance criterion: < 1.5%)")

def run_exercise_1():
    """Main driver for Exercise 1."""
    print("\n" + "="*65)
    print("  EXERCISE 1: Pitot-Static Velocity Survey — Bernoulli Verification")
    print("="*65)

    data_dir  = Path("data/exercise_1")
    out_dir   = Path("output/exercise_1")
    out_dir.mkdir(parents=True, exist_ok=True)

    rho = compute_air_density(P_ATM_PA, T_AMBIENT_K)
    print(f"\n  Ambient: P = {P_ATM_PA:.1f} Pa, T = {T_AMBIENT_K:.2f} K")
    print(f"  Computed air density: ρ = {rho:.5f} kg/m³")

    # ── Load zero-offset calibration file (tunnel off) ────────────────────────
    zero_path  = data_dir / "zero_calibration.csv"
    zero_counts = np.loadtxt(zero_path, delimiter=',')
    zero_v_amp  = adc_counts_to_volts(zero_counts)
    zero_v_sen  = amplifier_to_sensor_voltage(zero_v_amp)
    zero_offset = float(np.mean(sensor_voltage_to_pressure(zero_v_sen)))
    zero_noise  = float(np.std(sensor_voltage_to_pressure(zero_v_sen), ddof=1))
    print(f"\n  Sensor zero offset: {zero_offset:.4f} Pa  "
          f"(noise floor σ = {zero_noise:.4f} Pa)")

    # ── Centerline sweep ──────────────────────────────────────────────────────
    measured_u = np.zeros(len(NOMINAL_SPEEDS))
    sigma_u    = np.zeros(len(NOMINAL_SPEEDS))

    print(f"\n  {'Nominal (m/s)':>14}  {'q_mean (Pa)':>12}  "
          f"{'u_meas (m/s)':>13}  {'σ_u (m/s)':>10}  {'Re_chord':>10}")
    print("  " + "-"*68)

    chord_m = 0.150  # m
    for i, u_nom in enumerate(NOMINAL_SPEEDS):
        fp  = data_dir / f"centerline_{i+1}.csv"
        res = load_and_process_csv(fp, zero_offset, rho)
        measured_u[i] = res['u_mean']
        sigma_u[i]    = res['u_std']
        Re = rho * res['u_mean'] * chord_m / (1.81e-5)  # dynamic viscosity air @ 20°C
        print(f"  {u_nom:>14.1f}  {res['q_mean']:>12.3f}  "
              f"{res['u_mean']:>13.4f}  {res['u_std']:>10.6f}  {Re:>10.0f}")

    bernoulli_verification_plot(NOMINAL_SPEEDS, measured_u, sigma_u, rho,
                                out_dir / "bernoulli_verification.png")

    # ── Spatial grid survey at 12 m/s ─────────────────────────────────────────
    print(f"\n  Loading 5×5 spatial grid survey data...")
    grid_u = np.zeros((GRID_ROWS, GRID_COLS))
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            fp  = data_dir / f"grid_{r+1}_{c+1}.csv"
            res = load_and_process_csv(fp, zero_offset, rho)
            grid_u[r, c] = res['u_mean']

    flow_uniformity_contour(grid_u, GRID_SPACING,
                            out_dir / "flow_uniformity.png")

    print(f"\n  Exercise 1 complete. Outputs written to: {out_dir}/\n")

if __name__ == "__main__":
    run_exercise_1()
```

**Interpreting Results.** The Bernoulli verification plot should yield a regression slope between 0.995 and 1.005 with $R^2 > 0.9999$. A slope systematically below 1.0 indicates either a blocked pitot tube orifice (check with a 0.3 mm wire probe), a leaking pressure line connection, or ADC gain error — recalibrate the amplifier against a known pressure source (Druck DPI 610 or equivalent dead-weight tester). The spatial survey should show non-uniformity below 1.5% in the core 60% of the working section; values exceeding 2.5% in the central region indicate the tunnel's flow conditioning screens need cleaning or replacement.

The Reynolds numbers printed in the console output are critical context for all subsequent exercises. At 12 m/s over a 150 mm chord, $Re \approx 1.2 \times 10^5$ — well within the laminar-to-turbulent transitional regime on an NACA 4412 profile, which makes this tunnel speed particularly interesting for boundary-layer investigation.

---

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Angle-of-Attack Sweep: Lift and Drag Polar Measurement

Having established a reliable velocity reference, you are now ready to characterize the aerodynamic performance of an airfoil across its full operating envelope. The central quantity is the aerodynamic force coefficient, which renders the dimensional lift and drag forces non-dimensional and comparable across different tunnel speeds, chord lengths, and air densities. For a wing of planform area $S$ (or per unit span, $S = c \cdot 1$) in flow at dynamic pressure $q_\infty$:

$$C_L = \frac{L}{\frac{1}{2} \rho u_\infty^2 \cdot c \cdot b}, \qquad C_D = \frac{D}{\frac{1}{2} \rho u_\infty^2 \cdot c \cdot b}$$

where $L$ is lift force (N), $D$ is drag force (N), $c$ is chord length (m), and $b$ is model span (m). The lift curve has a linear region governed by thin-airfoil theory:

$$\frac{dC_L}{d\alpha} = 2\pi \quad \text{(per radian, inviscid thin airfoil)}$$

Real airfoils deviate from this slope near $\alpha = 0°$ due to camber offset and near stall due to boundary layer separation. Experimentally verifying the linear slope, locating the zero-lift angle $\alpha_{L=0}$, and precisely identifying the stall angle $\alpha_{stall}$ are the core tasks here.

**Physical Setup.** Mount the NACA 4412 model on the two-component strain-gauge balance with the rotation axis aligned with the aerodynamic center (approximately $0.25c$ from the leading edge). The model span should be as large as the tunnel width permits, with end-plates or wall mounting to minimize three-dimensional tip effects; a span-to-chord aspect ratio of at least 4:1 is recommended. Connect the balance analog outputs to the DAQ board through the INA128 instrumentation amplifiers. The angle of attack $\alpha$ is set via a precision worm-gear rotating mount with degree-resolution locking. Verify the geometric zero ($\alpha = 0°$) by confirming the chord line is parallel to the tunnel axis using a machinist's digital level on the model surface, accurate to 0.05°.

Before the sweep, perform a static calibration of the balance: with the tunnel off and the model at $\alpha = 0°$, hang known calibration weights of 0 N, 0.5 N, 1 N, 2 N, 3 N, and 5 N from the lift and drag load cells separately. Record the DAQ voltage output at each load. This produces two calibration curves (lift channel and drag channel) whose slopes (N/V) are stored and applied to all subsequent tunnel data. The calibration should be linear with $R^2 > 0.9998$; nonlinearity indicates bridge wiring errors or amplifier saturation.

**Procedure.** Set the tunnel to $u_\infty = 15$ m/s ($q_\infty \approx 135$ Pa, $Re \approx 1.5 \times 10^5$). Sweep $\alpha$ from $-8°$ to $+22°$ in 1° increments, allowing 60 seconds of settling time at each angle before acquiring 5000 samples at 1000 Hz. Record tare forces (tunnel on, no model — replace model with a streamlined sting fairing) at the same angle increments before the main sweep; subtract these tare values from all subsequent readings to remove sting aerodynamic interference. Additionally, repeat the entire sweep at $u_\infty = 10$ m/s and $20$ m/s to verify Reynolds number independence of the non-dimensionalized coefficients in the linear regime.

**Parameter Variation and Polar Plotting Code.**

```python
#!/usr/bin/env python3
"""
Exercise 2: Angle-of-attack sweep — lift/drag polar and C_L curve.

Balance calibration files:
  balance_calib_lift.csv  : columns [load_N, voltage_V], 6 rows
  balance_calib_drag.csv  : columns [load_N, voltage_V], 6 rows

AoA sweep data files:
  aoa_sweep_<tunnel_speed>ms/aoa_<signed_angle_deg>.csv
    e.g. aoa_sweep_15ms/aoa_-08.csv ... aoa_sweep_15ms/aoa_+22.csv
  tare files:
  tare_<tunnel_speed>ms/tare_<signed_angle_deg>.csv
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats, signal
from pathlib import Path

# ── Geometry and flow parameters ──────────────────────────────────────────────
CHORD_M      = 0.150           # m, airfoil chord length
SPAN_M       = 0.290           # m, model span in tunnel (tunnel width – 2×gap)
S_REF        = CHORD_M * SPAN_M  # m², reference planform area
R_SPECIFIC   = 287.05
MU_AIR       = 1.81e-5         # Pa·s, dynamic viscosity at 20°C
P_ATM_PA     = 101325.0
T_AMBIENT_K  = 293.15
RHO          = P_ATM_PA / (R_SPECIFIC * T_AMBIENT_K)

TUNNEL_SPEEDS = [10.0, 15.0, 20.0]  # m/s — three Re sweeps
AOA_RANGE     = np.arange(-8, 23, 1)  # degrees, -8 to +22 inclusive

# ADC / amplifier parameters (same as Exercise 1)
ADC_VREF      = 10.0
ADC_BITS      = 12
ADC_COUNTS    = 2**ADC_BITS
BALANCE_GAIN  = 100.0

def adc_to_volts(counts: np.ndarray) -> np.ndarray:
    return (counts / (ADC_COUNTS - 1)) * 2 * ADC_VREF - ADC_VREF

def load_balance_calibration(calib_path: Path) -> tuple[float, float]:
    """
    Fit linear calibration: Voltage = slope * Force + intercept.
    Returns (sensitivity N/V, intercept N).
    The inverse (force from voltage) is: Force = (V - intercept) / slope.
    """
    data       = np.loadtxt(calib_path, delimiter=',')
    load_N     = data[:, 0]
    voltage_V  = data[:, 1]
    slope, intercept, r_val, _, se = stats.linregress(voltage_V, load_N)
    print(f"    Calibration {calib_path.name}: "
          f"slope = {slope:.6f} N/V, R² = {r_val**2:.7f}")
    if r_val**2 < 0.9998:
        raise ValueError(
            f"Balance calibration nonlinearity: R² = {r_val**2:.5f} < 0.9998. "
            "Check bridge wiring and amplifier gain.")
    return slope, intercept

def load_force_csv(filepath: Path,
                   cal_slope: float, cal_intercept: float,
                   tare_force_N: float) -> dict:
    """
    Load DAQ file, convert ADC counts → voltage → force (N),
    subtract tare, return mean and std.
    """
    counts  = np.loadtxt(filepath, delimiter=',')
    volts   = adc_to_volts(counts) / BALANCE_GAIN  # remove INA128 gain
    force_N = cal_slope * volts + cal_intercept

    # Apply 4th-order Butterworth low-pass at 50 Hz to suppress vibration
    fs      = 1000.0  # Hz sample rate
    fc      = 50.0    # Hz cutoff
    b, a    = signal.butter(4, fc / (fs / 2), btype='low')
    force_f = signal.filtfilt(b, a, force_N)

    force_net  = force_f - tare_force_N
    return {'mean': float(np.mean(force_net)),
            'std':  float(np.std(force_net, ddof=1)),
            'n':    len(force_N)}

def compute_coefficients(L_N: float, D_N: float, q_inf: float) -> tuple:
    """Compute C_L and C_D from forces and dynamic pressure."""
    C_L = L_N / (q_inf * S_REF)
    C_D = D_N / (q_inf * S_REF)
    return C_L, C_D

def run_aoa_sweep(tunnel_speed: float,
                  lift_cal: tuple, drag_cal: tuple,
                  data_dir: Path) -> dict:
    """
    Process full AoA sweep for one tunnel speed.
    Returns arrays of alpha, C_L, C_D, and their standard deviations.
    """
    q_inf  = 0.5 * RHO * tunnel_speed**2
    Re     = RHO * tunnel_speed * CHORD_M / MU_AIR
    speed_tag = f"{int(tunnel_speed):02d}ms"

    alpha_arr  = []
    CL_arr, CL_std_arr = [], []
    CD_arr, CD_std_arr = [], []

    tare_dir   = data_dir / f"tare_{speed_tag}"
    sweep_dir  = data_dir / f"aoa_sweep_{speed_tag}"

    for alpha_deg in AOA_RANGE:
        sign = "+" if alpha_deg >= 0 else ""
        tag  = f"aoa_{sign}{alpha_deg:03d}" if alpha_deg >= 0 \
               else f"aoa_{alpha_deg:04d}"
        # Signed filename convention: aoa_+005.csv, aoa_-008.csv
        fname = f"aoa_{alpha_deg:+04d}.csv"

        tare_fp  = tare_dir  / fname
        sweep_fp = sweep_dir / fname

        # Tare forces
        tare_L = load_force_csv(tare_fp, *lift_cal, 0.0)['mean']
        tare_D = load_force_csv(tare_fp, *drag_cal, 0.0)['mean']

        # Net aerodynamic forces
        L_res  = load_force_csv(sweep_fp, *lift_cal, tare_L)
        D_res  = load_force_csv(sweep_fp, *drag_cal, tare_D)

        C_L, C_D = compute_coefficients(L_res['mean'], D_res['mean'], q_inf)

        # Propagate uncertainty: σ_CL = σ_L / (q_inf * S_REF)
        sigma_CL = L_res['std'] / (q_inf * S_REF * np.sqrt(L_res['n']))
        sigma_CD = D_res['std'] / (q_inf * S_REF * np.sqrt(D_res['n']))

        alpha_arr.append(alpha_deg)
        CL_arr.append(C_L);    CL_std_arr.append(sigma_CL)
        CD_arr.append(C_D);    CD_std_arr.append(sigma_CD)

    return {
        'alpha':  np.array(alpha_arr),
        'CL':     np.array(CL_arr),    'CL_std': np.array(CL_std_arr),
        'CD':     np.array(CD_arr),    'CD_std': np.array(CD_std_arr),
        'q_inf':  q_inf, 'Re': Re,
        'speed':  tunnel_speed
    }

def fit_linear_clalpha(alpha_deg: np.ndarray, CL: np.ndarray,
                        alpha_min: float = -4.0,
                        alpha_max: float = 10.0) -> dict:
    """
    Fit C_L = (dCL/dalpha) * alpha + CL0 in the linear regime.
    Returns slope (per degree), zero-lift angle, and R².
    """
    mask  = (alpha_deg >= alpha_min) & (alpha_deg <= alpha_max)
    slope, intercept, r_val, _, se = stats.linregress(alpha_deg[mask],
                                                       CL[mask])
    alpha_L0 = -intercept / slope  # zero-lift angle
    # Convert slope to per-radian
    slope_per_rad = slope * (180.0 / np.pi)
    return {
        'slope_per_deg': slope, 'slope_per_rad': slope_per_rad,
        'intercept': intercept, 'alpha_L0_deg': alpha_L0,
        'R2': r_val**2, 'se': se
    }

def find_stall_angle(alpha_deg: np.ndarray, CL: np.ndarray) -> float:
    """
    Identify stall as the angle of maximum C_L followed by a drop > 0.05.
    Uses a robust peak-finding approach.
    """
    peaks, props = signal.find_peaks(CL, prominence=0.05)
    if len(peaks) == 0:
        return float(alpha_deg[np.argmax(CL)])
    # Return the highest-CL peak
    dominant = peaks[np.argmax(CL[peaks])]
    return float(alpha_deg[dominant])

def plot_cl_curve(sweeps: list[dict], linear_fits: list[dict],
                   save_path: Path):
    """Plot C_L vs alpha for all three Reynolds number sweeps."""
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ['steelblue', 'firebrick', 'forestgreen']

    for sw, fit, col in zip(sweeps, linear_fits, colors):
        Re_k = sw['Re'] / 1e3
        ax.errorbar(sw['alpha'], sw['CL'], yerr=2*sw['CL_std'],
                    fmt='o', ms=4, capsize=3, color=col, alpha=0.8,
                    label=f"$Re$ = {Re_k:.0f}k (±2σ)")

        # Plot linear fit extension
        alpha_fit = np.linspace(-8, 23, 300)
        CL_fit    = fit['slope_per_deg'] * alpha_fit + fit['intercept']
        # Only draw fit line within linear regime
        mask_fit  = (alpha_fit >= -4) & (alpha_fit <= 10)
        ax.plot(alpha_fit[mask_fit], CL_fit[mask_fit],
                '--', color=col, lw=1.4, alpha=0.7)

        # Annotate stall
        alpha_stall = find_stall_angle(sw['alpha'], sw['CL'])
        CL_stall    = sw['CL'][sw['alpha'] == int(alpha_stall)][0]
        ax.annotate(f"stall {alpha_stall:.0f}°",
                    xy=(alpha_stall, CL_stall),
                    xytext=(alpha_stall + 1.5, CL_stall - 0.07),
                    fontsize=8, color=col,
                    arrowprops=dict(arrowstyle='->', color=col, lw=0.8))

    # Thin-airfoil theory line: slope = 2π/rad = 0.1097/deg
    alpha_th = np.linspace(-8, 14, 200)
    CL_th    = 2 * np.pi * np.deg2rad(alpha_th)   # inviscid prediction
    ax.plot(alpha_th, CL_th, 'k:', lw=1.0, label='Thin-airfoil theory (2π/rad)')

    ax.axhline(0, color='k', lw=0.5, alpha=0.5)
    ax.axvline(0, color='k', lw=0.5, alpha=0.5)
    ax.set_xlabel('Angle of Attack α (degrees)', fontsize=12)
    ax.set_ylabel('Lift Coefficient $C_L$', fontsize=12)
    ax.set_title('NACA 4412 Lift Curve — Reynolds Number Comparison', fontsize=13)
    ax.legend(fontsize=9)
    ax.set_xlim(-9, 24)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(True, which='major', alpha=0.4)
    ax.grid(True, which='minor', alpha=0.15)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    print(f"  → C_L curve saved: {save_path}")

def plot_polar(sweeps: list[dict], save_path: Path):
    """Plot aerodynamic polar: C_L vs C_D (drag polar)."""
    fig, ax = plt.subplots(figsize=(7, 8))
    colors = ['steelblue', 'firebrick', 'forestgreen']

    for sw, col in zip(sweeps, colors):
        Re_k = sw['Re'] / 1e3
        ax.plot(sw['CD'], sw['CL'], 'o-', ms=4, lw=1.2,
                color=col, label=f"$Re$ = {Re_k:.0f}k")
        ax.errorbar(sw['CD'], sw['CL'],
                    xerr=2*sw['CD_std'], yerr=2*sw['CL_std'],
                    fmt='none', ecolor=col, alpha=0.3, capsize=2)

        # Maximum L/D point
        ld_ratio = sw['CL'] / sw['CD']
        idx_ld   = np.nanargmax(ld_ratio)
        ax.plot(sw['CD'][idx_ld], sw['CL'][idx_ld], '*',
                ms=12, color=col, zorder=10,
                label=f"$(L/D)_{{max}}$ = {ld_ratio[idx_ld]:.1f} "
                      f"at α = {sw['alpha'][idx_ld]}°")

    ax.set_xlabel('Drag Coefficient $C_D$', fontsize=12)
    ax.set_ylabel('Lift Coefficient $C_L$', fontsize=12)
    ax.set_title('NACA 4412 Aerodynamic Polar', fontsize=13)
    ax.legend(fontsize=9)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(True, which='major', alpha=0.4)
    ax.grid(True, which='minor', alpha=0.15)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    print(f"  → Polar plot saved: {save_path}")

def run_exercise_2():
    print("\n" + "="*65)
    print("  EXERCISE 2: AoA Sweep — Lift/Drag Polar Measurement")
    print("="*65)

    data_dir = Path("data/exercise_2")
    out_dir  = Path("output/exercise_2")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Balance calibration ───────────────────────────────────────────────────
    print("\n  Loading balance calibrations...")
    lift_cal = load_balance_calibration(data_dir / "balance_calib_lift.csv")
    drag_cal = load_balance_calibration(data_dir / "balance_calib_drag.csv")

    # ── Run sweeps for all three tunnel speeds ─────────────────────────────────
    sweeps      = []
    linear_fits = []

    for u_inf in TUNNEL_SPEEDS:
        print(f"\n  Processing sweep at {u_inf:.0f} m/s "
              f"(Re = {RHO*u_inf*CHORD_M/MU_AIR:.2e})...")
        sw   = run_aoa_sweep(u_inf, lift_cal, drag_cal, data_dir)
        fit  = fit_linear_clalpha(sw['alpha'], sw['CL'])
        sweeps.append(sw)
        linear_fits.append(fit)

        alpha_stall = find_stall_angle(sw['alpha'], sw['CL'])
        print(f"    dCL/dα = {fit['slope_per_deg']:.5f} /deg  "
              f"({fit['slope_per_rad']:.4f} /rad, theory: {2*np.pi:.4f})")
        print(f"    Zero-lift angle α_L0 = {fit['alpha_L0_deg']:.2f}°  "
              f"(NACA 4412 expected: ≈ −4.0°)")
        print(f"    Stall angle: {alpha_stall:.1f}°")
        print(f"    Linear fit R²: {fit['R2']:.7f}")

    # ── Plots ──────────────────────────────────────────────────────────────────
    plot_cl_curve(sweeps, linear_fits, out_dir / "CL_vs_alpha.png")
    plot_polar(sweeps, out_dir / "aerodynamic_polar.png")

    print(f"\n  Exercise 2 complete. Outputs written to: {out_dir}/\n")

if __name__ == "__main__":
    run_exercise_2()
```

**What the Results Should Show.** For the NACA 4412 at $Re = 1.5 \times 10^5$, you should measure a lift-curve slope of approximately $0.095$–$0.105$ per degree (theoretical inviscid value: $0.1097$/deg), a zero-lift angle near $-4°$ (consistent with the 4% camber), and a stall angle around $14°$–$16°$ depending on the turbulence intensity of your tunnel. The polar will reveal the characteristic bucket shape: a low-drag laminar bucket at low angles of attack, transitioning to higher drag after stall. If your measured $dC_L/d\alpha$ exceeds the theoretical $2\pi/\text{rad}$ slope by more than 5%, check for model blockage effects — the tunnel working-section blockage ratio (model frontal area / working section area) should be below 7.5%.

---

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### Stall, Separation, and Full Measurement Uncertainty Budget

The most revealing aerodynamic behavior occurs at the edges of the operational envelope — specifically in the stall and post-stall regime where boundary layer separation transforms the smooth potential-flow physics into a coupled viscous-inviscid interaction problem. This exercise is simultaneously a physical exploration of flow separation and a rigorous lesson in experimental uncertainty analysis, the discipline that separates publishable measurements from laboratory folklore.

The boundary layer's vulnerability to separation is governed by the adverse pressure gradient it encounters on the suction (upper) surface of the airfoil as $\alpha$ increases. In the favorable gradient region near the leading edge, the laminar boundary layer remains attached. As the pressure recovery region extends further forward with increasing $\alpha$, the boundary layer must do work against an increasing pressure gradient; eventually the momentum of near-wall fluid is exhausted and separation occurs. The separation point moves progressively forward with angle of attack until full trailing-edge stall (gradual, characteristic of moderate camber) or leading-edge stall (abrupt, characteristic of thin profiles) results in catastrophic lift loss.

**Physical Setup: Surface Pressure Distribution.** For this exercise, replace the force balance model with the surface-tapped pressure model. Connect the 18 chordwise pressure taps (distributed as: 0, 1.25, 2.5, 5, 7.5, 10, 15, 20, 30, 40, 50, 60, 70, 75, 80, 85, 90, and 95% chord on the upper surface; a symmetric 10-tap subset on the lower surface) via 0.8 mm polyurethane tubing to a Scanivalve mechanical multiplexer, which routes each tap sequentially to a single precision pressure transducer (Validyne DP15 with 0–350 Pa diaphragm, or equivalent). The Scanivalve steps through all taps under DAQ triggering, 2000 samples per tap position, 60 ms settling time per step.

The pressure coefficient at each tap location $x/c$ is:

$$C_p = \frac{p_{tap} - p_\infty}{q_\infty} = 1 - \left(\frac{u_{local}}{u_\infty}\right)^2$$

where the last equality holds for inviscid flow via Bernoulli. Integrating $C_p$ around the airfoil profile gives the normal force coefficient $C_N$; projecting onto the wind axis yields $C_L$ (from the pressure distribution alone, independent of the balance), providing an important cross-check.

**Stress Testing Protocol.** Perform the following sequence to systematically probe boundary conditions:

First, map the full $C_p$ distribution at $\alpha = 0°$, $4°$, $8°$, $12°$, $14°$, $16°$, $18°$, and $20°$ at $u_\infty = 15$ m/s. The evolution of the suction peak (minimum $C_p$ near the leading edge), the pressure plateau that marks separation, and the wake deficit collectively constitute a complete aerodynamic portrait of the stall progression. Second, at $\alpha = 15°$ (nominally near stall onset), perform a time-resolved sequence: rather than averaging, record the raw 5-second pressure trace on tap number 7 (located at 10% chord on the upper surface) at 1000 Hz. The autocorrelation function of this signal reveals the characteristic frequency of vortex shedding if unsteady separation has established itself. Third, repeat the $\alpha = 15°$ measurement after applying a 3 mm trip strip (sandpaper roughness strip, grit P80) at 10% chord on the upper surface to trigger turbulent boundary layer transition; compare the resulting $C_p$ and stall behavior with the untripped case.

**Complete Uncertainty Analysis Code.** The following script processes all $C_p$ distributions, computes integrated forces, performs autocorrelation analysis, and constructs a formal uncertainty budget for the entire measurement chain.

```python
#!/usr/bin/env python3
"""
Exercise 3: Surface pressure distribution, stall analysis,
            and full measurement uncertainty budget.

Data structure:
  data/exercise_3/
    cp_alpha_<aaa>_tap_<tt>.csv   : 2000-sample pressure files per tap per alpha
    unsteady_alpha15_tap07.csv    : 5000-sample time series at 1000 Hz
    tripped_alpha15_tap_<tt>.csv  : tripped case at alpha=15

Scanivalve tap positions (x/c):
  Upper surface taps 1-18:
    [0.00, 0.0125, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.40,
     0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
  Lower surface taps 19-28:
    [0.025, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.75, 0.90]
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import signal, stats
from pathlib import Path

# ── Geometry ──────────────────────────────────────────────────────────────────
CHORD_M   = 0.150
SPAN_M    = 0.290
S_REF     = CHORD_M * SPAN_M
R_SPEC    = 287.05
MU_AIR    = 1.81e-5
P_ATM     = 101325.0
T_K       = 293.15
RHO       = P_ATM / (R_SPEC * T_K)
U_INF     = 15.0
Q_INF     = 0.5 * RHO * U_INF**2
FS_HZ     = 1000.0            # DAQ sample rate

# ── Tap chord positions ───────────────────────────────────────────────────────
XC_UPPER = np.array([0.00, 0.0125, 0.025, 0.05, 0.075, 0.10,
                     0.15, 0.20, 0.30, 0.40, 0.50, 0.60,
                     0.70, 0.75, 0.80, 0.85, 0.90, 0.95])
XC_LOWER = np.array([0.025, 0.05, 0.10, 0.20, 0.30,
                     0.40, 0.50, 0.60, 0.75, 0.90])

# ── Scanivalve calibration ─────────────────────────────────────────────────────
# Validyne DP15, 0-350 Pa range, 0-10V output via signal conditioner
SCAN_VREF   = 10.0  # V
SCAN_PRANGE = 350.0  # Pa

def voltage_to_pressure_scanivalve(v: np.ndarray,
                                    zero_v: float) -> np.ndarray:
    """
    Validyne DP15 linear transfer: p = (V - V_zero) / V_ref * P_range
    Zero voltage measured with both ports open to atmosphere.
    """
    return (v - zero_v) / SCAN_VREF * SCAN_PRANGE

def load_tap_csv(filepath: Path, zero_v: float) -> dict:
    """Load a single tap data file and return pressure statistics."""
    counts_raw = np.loadtxt(filepath, delimiter=',')
    # ADC: 16-bit, ±10V
    adc_bits   = 16
    v_out      = (counts_raw / (2**adc_bits - 1)) * 2 * SCAN_VREF - SCAN_VREF
    p_arr      = voltage_to_pressure_scanivalve(v_out, zero_v)
    return {'mean': float(np.mean(p_arr)),
            'std':  float(np.std(p_arr, ddof=1)),
            'raw':  p_arr}

def compute_cp_distribution(alpha_deg: float,
                             upper_pressures_Pa: np.ndarray,
                             lower_pressures_Pa: np.ndarray,
                             p_inf_Pa: float) -> dict:
    """
    Compute Cp = (p_tap - p_inf) / q_inf for upper and lower surfaces.
    p_inf_Pa: freestream static pressure (from pitot-static wall tap).
    """
    Cp_upper = (upper_pressures_Pa - p_inf_Pa) / Q_INF
    Cp_lower = (lower_pressures_Pa - p_inf_Pa) / Q_INF
    return {'Cp_upper': Cp_upper, 'Cp_lower': Cp_lower,
            'alpha': alpha_deg}

def integrate_cn_from_cp(xc_upper: np.ndarray, Cp_upper: np.ndarray,
                          xc_lower: np.ndarray, Cp_lower: np.ndarray) -> float:
    """
    Integrate normal force coefficient using trapezoidal rule.
    C_N = integral_0^1 (Cp_lower - Cp_upper) d(x/c)

    Both arrays are interpolated onto a common x/c grid for robust integration.
    """
    xc_common   = np.linspace(0.0, 1.0, 1000)
    Cp_up_interp = np.interp(xc_common, xc_upper, Cp_upper,
                              left=Cp_upper[0], right=0.0)
    Cp_lo_interp = np.interp(xc_common, xc_lower, Cp_lower,
                              left=Cp_lower[0], right=0.0)
    C_N = np.trapz(Cp_lo_interp - Cp_up_interp, xc_common)
    return float(C_N)

def cn_to_cl(C_N: float, alpha_deg: float) -> float:
    """
    For small angles: C_L ≈ C_N * cos(alpha) - C_A * sin(alpha).
    Neglecting chord-force contribution (axial force C_A is small):
    C_L ≈ C_N * cos(alpha).
    """
    return C_N * np.cos(np.deg2rad(alpha_deg))

# ── Uncertainty budget ─────────────────────────────────────────────────────────
def uncertainty_budget_cp(p_tap_mean: float, p_tap_std: float,
                           p_inf_std: float,
                           n_samples: int = 2000) -> dict:
    """
    Full first-order error propagation for Cp = (p_tap - p_inf) / q_inf.

    Sources considered:
      u1: Random pressure fluctuation (σ_p_tap / sqrt(n))
      u2: Reference static pressure uncertainty (σ_p_inf / sqrt(n_inf))
      u3: Dynamic pressure uncertainty  σ_q = σ_rho * q_inf / rho + ...
          Simplified: σ_q / q_inf ≈ sqrt((σ_T/T)^2 + (σ_P/P_atm)^2 +
                                          (σ_u/u)^2 * 4)   (velocity contribution)
      u4: Scanivalve settling time error (systematic offset ≈ 0.5 Pa, rectangular dist)
      u5: ADC quantization: LSB/sqrt(12)
    """
    # Type A uncertainties (statistical)
    u1    = p_tap_std / np.sqrt(n_samples)   # Pa
    u2    = p_inf_std / np.sqrt(n_samples)   # Pa (from static wall tap)

    # Type B uncertainties (systematic)
    # ADC: 16-bit, ±10 V, converted to pressure units (DP15, 350 Pa range)
    lsb_v = 2 * SCAN_VREF / (2**16 - 1)      # V per count
    lsb_p = lsb_v / SCAN_VREF * SCAN_PRANGE   # Pa per count
    u3    = lsb_p / np.sqrt(12)               # Pa, quantization (uniform dist)

    u4    = 0.5 / np.sqrt(3)                  # Pa, Scanivalve settling (rect)

    # Relative dynamic pressure uncertainty: temperature ±0.5 K, baro ±50 Pa,
    # velocity ±0.05 m/s (from pitot calibration in Exercise 1)
    sigma_T_rel = 0.5 / T_K
    sigma_P_rel = 50.0 / P_ATM
    sigma_u_rel = 0.05 / U_INF
    sigma_q_rel = np.sqrt(sigma_T_rel**2 + sigma_P_rel**2
                          + (2 * sigma_u_rel)**2)

    # Partial derivatives of Cp w.r.t. each quantity:
    # dCp/dp_tap = 1/q_inf
    # dCp/dp_inf = -1/q_inf
    # dCp/dq_inf = -(p_tap-p_inf)/q_inf^2 = -Cp/q_inf
    Cp_val    = (p_tap_mean - 101325.0) / Q_INF   # rough nominal Cp
    dCp_dp    = 1.0 / Q_INF
    dCp_dq    = -Cp_val / Q_INF

    # Combined standard uncertainty
    u_comb = np.sqrt(
        (dCp_dp * u1)**2   +   # random tap fluctuation
        (dCp_dp * u2)**2   +   # ref static uncertainty
        (dCp_dp * u3)**2   +   # ADC quantization
        (dCp_dp * u4)**2   +   # Scanivalve settling
        (dCp_dq * sigma_q_rel * Q_INF)**2  # q_inf uncertainty
    )

    # Expanded uncertainty (k=2, ~95% confidence)
    U95 = 2.0 * u_comb

    return {
        'u_tap_random':     dCp_dp * u1,
        'u_ref_static':     dCp_dp * u2,
        'u_quantization':   dCp_dp * u3,
        'u_scanivalve':     dCp_dp * u4,
        'u_qinf':           abs(dCp_dq * sigma_q_rel * Q_INF),
        'u_combined':       u_comb,
        'U95':              U95
    }

def autocorrelation_analysis(time_series: np.ndarray,
                              fs: float, save_path: Path):
    """
    Compute normalized autocorrelation and power spectral density
    of unsteady pressure to identify vortex shedding frequency.
    """
    n      = len(time_series)
    ts_z   = time_series - np.mean(time_series)  # zero-mean

    # Normalized autocorrelation
    acf    = np.correlate(ts_z, ts_z, mode='full') / (n * np.var(ts_z))
    lags   = np.arange(-(n-1), n) / fs  # seconds

    # Power spectral density: Welch method, 50% overlap, Hann window
    f_psd, Pxx = signal.welch(ts_z, fs=fs, window='hann',
                               nperseg=512, noverlap=256,
                               scaling='density')

    # Find dominant shedding frequency (above 5 Hz to exclude DC drift)
    mask_f    = f_psd > 5.0
    f_dom     = f_psd[mask_f][np.argmax(Pxx[mask_f])]
    # Strouhal number: St = f*c/U_inf
    St        = f_dom * CHORD_M / U_INF

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Autocorrelation
    ax = axes[0]
    lag_range = np.abs(lags) < 0.5  # show ±0.5 s
    ax.plot(lags[lag_range], acf[n-1:][lag_range[:n]], color='steelblue', lw=1.0)
    ax.axhline(0, color='k', lw=0.5)
    ax.axhline(1.96/np.sqrt(n), color='r', lw=0.8, ls='--', label='95% CI bounds')
    ax.axhline(-1.96/np.sqrt(n), color='r', lw=0.8, ls='--')
    ax.set_xlabel('Lag (s)', fontsize=11)
    ax.set_ylabel('Normalized Autocorrelation', fontsize=11)
    ax.set_title(f'Pressure Autocorrelation — Tap 7 at α=15°', fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.4)

    # PSD
    ax = axes[1]
    ax.semilogy(f_psd, Pxx, color='firebrick', lw=1.0)
    ax.axvline(f_dom, color='k', ls='--', lw=1.0,
               label=f'$f_{{shed}}$ = {f_dom:.1f} Hz (St = {St:.3f})')
    ax.set_xlabel('Frequency (Hz)', fontsize=11)
    ax.set_ylabel('PSD (Pa²/Hz)', fontsize=11)
    ax.set_title('Power Spectral Density — Unsteady Pressure', fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, which='both', alpha=0.3)

    fig.suptitle(f'Vortex Shedding Analysis: dominant $f$ = {f_dom:.1f} Hz, '
                 f'St = {St:.3f}', fontsize=11, y=1.01)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"  → Autocorrelation/PSD plot saved: {save_path}")
    print(f"    Dominant shedding frequency: {f_dom:.2f} Hz")
    print(f"    Strouhal number: St = {St:.4f}")
    print(f"    (Canonical bluff-body reference: St ≈ 0.2 for cylinder)")

def plot_cp_distributions(alpha_cases: list[float],
                           Cp_data: dict, save_path: Path):
    """
    Plot Cp vs x/c for multiple angles of attack on a single figure.
    Convention: Cp positive downward (inverted y-axis), upper surface on top.
    """
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharex=True, sharey=True)
    axes = axes.flatten()
    cmap = plt.get_cmap('plasma')
    colors = [cmap(i / (len(alpha_cases) - 1)) for i in range(len(alpha_cases))]

    for idx, alpha_deg in enumerate(alpha_cases):
        ax  = axes[idx]
        dat = Cp_data[alpha_deg]

        ax.plot(XC_UPPER, dat['Cp_upper'], 'o-', ms=4, lw=1.2,
                color=colors[idx], label='Upper')
        ax.plot(XC_LOWER, dat['Cp_lower'], 's--', ms=4, lw=1.2,
                color=colors[idx], alpha=0.6, label='Lower')
        ax.axhline(0, color='k', lw=0.5)
        ax.invert_yaxis()  # aerodynamic convention: suction (negative Cp) on top
        ax.set_title(f'α = {alpha_deg:.0f}°\n'
                     f'$C_L$ (integrated) = {dat["CL_integrated"]:.3f}',
                     fontsize=10)
        ax.set_xlim(0, 1)
        ax.grid(True, alpha=0.3)
        if idx >= 4:
            ax.set_xlabel('x/c', fontsize=10)
        if idx % 4 == 0:
            ax.set_ylabel('$C_p$', fontsize=10)
        if idx == 0:
            ax.legend(fontsize=8)

    fig.suptitle('NACA 4412 — $C_p$ Distribution at $Re$ = 1.5×10⁵', fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=200)
    plt.close(fig)
    print(f"  → Cp distribution panel saved: {save_path}")

def print_uncertainty_table(budget: dict, alpha: float, tap_xc: float):
    """Print a formatted uncertainty budget table."""
    print(f"\n  ── Uncertainty Budget: Cp at x/c={tap_xc:.3f}, α={alpha:.0f}° ──")
    print(f"  {'Source':<35}  {'Contribution (ΔCp)':>20}  {'% of U95':>10}")
    print("  " + "-"*68)
    items = [
        ('Random tap pressure fluctuation',  budget['u_tap_random']),
        ('Reference static pressure',        budget['u_ref_static']),
        ('ADC quantization',                 budget['u_quantization']),
        ('Scanivalve settling time',         budget['u_scanivalve']),
        ('Dynamic pressure (q_inf)',         budget['u_qinf']),
    ]
    for name, val in items:
        pct = val / budget['U95'] * 100 if budget['U95'] > 0 else 0
        print(f"  {name:<35}  {val:>20.6f}  {pct:>10.1f}%")
    print("  " + "-"*68)
    print(f"  {'Combined standard uncertainty u_c':<35}  "
          f"{budget['u_combined']:>20.6f}")
    print(f"  {'Expanded uncertainty U (k=2, 95%)':<35}  "
          f"{budget['U95']:>20.6f}\n")

def run_exercise_3():
    print("\n" + "="*65)
    print("  EXERCISE 3: Stall Mapping, Separation & Uncertainty Analysis")
    print("="*65)

    data_dir = Path("data/exercise_3")
    out_dir  = Path("output/exercise_3")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Sensor zero offset ─────────────────────────────────────────────────────
    zero_path = data_dir / "scanivalve_zero.csv"
    zero_raw  = np.loadtxt(zero_path, delimiter=',')
    adc_bits  = 16
    zero_v    = float(np.mean(
        (zero_raw / (2**adc_bits - 1)) * 2 * SCAN_VREF - SCAN_VREF))
    print(f"\n  Scanivalve zero voltage: {zero_v:.5f} V")

    # ── Freestream static pressure from wall tap ───────────────────────────────
    p_inf_path = data_dir / "static_wall_tap.csv"
    p_inf_data = load_tap_csv(p_inf_path, zero_v)
    P_INF      = p_inf_data['mean']   # Pa, used as reference in Cp
    print(f"  Freestream static pressure (wall tap): {P_INF:.2f} Pa")

    # ── Load Cp distributions for all alpha cases ─────────────────────────────
    ALPHA_CASES = [0.0, 4.0, 8.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    N_UPPER     = len(XC_UPPER)
    N_LOWER     = len(XC_LOWER)
    Cp_data     = {}

    print("\n  {'α (deg)':>8}  {'Cp_min (upper)':>16}  {'C_N':>8}  {'C_L (press.)':>14}")
    print("  " + "-"*52)

    for alpha_deg in ALPHA_CASES:
        p_upper = np.zeros(N_UPPER)
        p_lower = np.zeros(N_LOWER)
        p_upper_std = np.zeros(N_UPPER)

        # Load upper surface taps
        for t, xc in enumerate(XC_UPPER):
            fp  = data_dir / f"cp_alpha_{int(alpha_deg):+03d}_tap_{t+1:02d}.csv"
            res = load_tap_csv(fp, zero_v)
            p_upper[t]     = res['mean']
            p_upper_std[t] = res['std']

        # Load lower surface taps
        for t, xc in enumerate(XC_LOWER):
            fp  = data_dir / f"cp_alpha_{int(alpha_deg):+03d}_tap_{t+19:02d}.csv"
            res = load_tap_csv(fp, zero_v)
            p_lower[t] = res['mean']

        cp_dict  = compute_cp_distribution(alpha_deg, p_upper, p_lower, P_INF)
        C_N      = integrate_cn_from_cp(XC_UPPER, cp_dict['Cp_upper'],
                                         XC_LOWER, cp_dict['Cp_lower'])
        C_L_int  = cn_to_cl(C_N, alpha_deg)

        cp_dict['CL_integrated'] = C_L_int
        cp_dict['C_N']           = C_N
        Cp_data[alpha_deg]       = cp_dict

        Cp_min = cp_dict['Cp_upper'].min()
        print(f"  {alpha_deg:>8.1f}  {Cp_min:>16.4f}  {C_N:>8.4f}  "
              f"{C_L_int:>14.4f}")

    plot_cp_distributions(ALPHA_CASES, Cp_data,
                           out_dir / "Cp_distributions.png")

    # ── Formal uncertainty budget at representative condition ─────────────────
    # Select tap 7 (10% chord upper), alpha = 8 deg as representative
    fp_rep    = data_dir / "cp_alpha_+08_tap_07.csv"
    res_rep   = load_tap_csv(fp_rep, zero_v)
    budget    = uncertainty_budget_cp(res_rep['mean'], res_rep['std'],
                                       p_inf_data['std'], n_samples=2000)
    print_uncertainty_table(budget, alpha=8.0, tap_xc=XC_UPPER[6])

    # ── Unsteady pressure analysis at alpha = 15° ─────────────────────────────
    print("\n  Running autocorrelation and PSD analysis on unsteady tap data...")
    unsteady_path = data_dir / "unsteady_alpha15_tap07.csv"
    raw_counts    = np.loadtxt(unsteady_path, delimiter=',')
    adc_b16       = 16
    v_ts = (raw_counts / (2**adc_b16 - 1)) * 2 * SCAN_VREF - SCAN_VREF
    p_ts = voltage_to_pressure_scanivalve(v_ts, zero_v)

    autocorrelation_analysis(p_ts, FS_HZ,
                              out_dir / "unsteady_vortex_shedding.png")

    # ── Tripped vs untripped comparison at alpha = 15° ────────────────────────
    print("\n  Comparing tripped vs untripped boundary layer at α=15°...")
    fig_trip, ax_t = plt.subplots(figsize=(9, 6))

    for case_label, case_prefix, style in [
            ('Untripped (natural transition)', 'cp_alpha_+15', 'o-'),
            ('Tripped at 10%c (P80 roughness)', 'tripped_alpha15', 's--')]:
        p_up = np.zeros(N_UPPER)
        p_lo = np.zeros(N_LOWER)
        for t in range(N_UPPER):
            fp = data_dir / f"{case_prefix}_tap_{t+1:02d}.csv"
            p_up[t] = load_tap_csv(fp, zero_v)['mean']
        for t in range(N_LOWER):
            fp = data_dir / f"{case_prefix}_tap_{t+19:02d}.csv"
            p_lo[t] = load_tap_csv(fp, zero_v)['mean']
        Cp_up = (p_up - P_INF) / Q_INF
        Cp_lo = (p_lo - P_INF) / Q_INF
        C_N   = integrate_cn_from_cp(XC_UPPER, Cp_up, XC_LOWER, Cp_lo)
        C_L   = cn_to_cl(C_N, 15.0)
        ax_t.plot(XC_UPPER, Cp_up, style, ms=5, lw=1.3,
                  label=f'{case_label} (upper, $C_L$={C_L:.3f})')
        ax_t.plot(XC_LOWER, Cp_lo, style, ms=5, lw=1.3, alpha=0.5,
                  label=f'{case_label} (lower)')

    ax_t.invert_yaxis()
    ax_t.axhline(0, color='k', lw=0.5)
    ax_t.axvline(0.10, color='gray', lw=0.8, ls=':', label='Trip strip at x/c=0.10')
    ax_t.set_xlabel('x/c', fontsize=12)
    ax_t.set_ylabel('$C_p$', fontsize=12)
    ax_t.set_title('Tripped vs Untripped Boundary Layer\nNACA 4412 at α=15°, '
                   '$Re$=1.5×10⁵', fontsize=12)
    ax_t.legend(fontsize=8)
    ax_t.grid(True, alpha=0.4)
    fig_trip.tight_layout()
    trip_path = out_dir / "tripped_vs_untripped.png"
    fig_trip.savefig(trip_path, dpi=200)
    plt.close(fig_trip)
    print(f"  → Tripped comparison plot saved: {trip_path}")

    print(f"\n  Exercise 3 complete. Outputs written to: {out_dir}/\n")

if __name__ == "__main__":
    run_exercise_3()
```

**Interpreting the Uncertainty Budget.** A well-executed analysis typically reveals that the dominant uncertainty contributor is the random pressure fluctuation in the tunnel's turbulent flow, not the sensor's electronic noise or quantization. At low angles of attack the expanded uncertainty on $C_p$ is typically $U_{95} \approx \pm 0.015$–$0.025$, which is fully adequate for lift coefficient integration to within $\pm 0.03$ in $C_L$. Near stall, unsteadiness of the separation point inflates the random fluctuation term significantly — the autocorrelation analysis will typically reveal a correlation time of 50–200 ms for the oscillating separation bubble, meaning that 5-second averages are sufficient for convergence of the mean but the standard deviation remains elevated.

The tripped versus untripped comparison is physically instructive. Forcing turbulent transition at 10% chord prevents the formation of a laminar separation bubble, which at $Re = 1.5 \times 10^5$ would otherwise form near the leading edge and dramatically alter the pressure distribution. The tripped case will show a fuller suction peak, delayed stall (by 2°–4°), and a higher $C_{L,max}$ — a direct consequence of the turbulent boundary layer's greater resistance to adverse pressure gradient separation due to its enhanced momentum exchange from the freestream.

---

## Laboratory Cheat Sheet & Metric Verification Guide

This section is a compact operational reference for the working scientist. It consolidates the key governing equations, dimensional analysis, instrument specifications, acceptance thresholds, and Python environment verification into a single lookup resource.

---

### Core Governing Equations

The dynamic pressure and velocity relationship from Bernoulli's principle:

$$q_\infty = \frac{1}{2}\rho u_\infty^2, \qquad u_\infty = \sqrt{\frac{2 q_\infty}{\rho}}$$

Air density from the ideal gas law:

$$\rho = \frac{P_{atm}}{R_{specific} \cdot T}, \qquad R_{specific} = 287.05\ \text{J kg}^{-1}\text{K}^{-1}$$

Reynolds number (governs laminar/turbulent regime transition):

$$Re = \frac{\rho u L}{\mu}, \qquad \mu_{air,20°C} = 1.81 \times 10^{-5}\ \text{Pa·s}$$

Force coefficients (non-dimensionalization):

$$C_L = \frac{L}{q_\infty \cdot S}, \qquad C_D = \frac{D}{q_\infty \cdot S}, \qquad C_p = \frac{p - p_\infty}{q_\infty}$$

Thin-airfoil lift slope (inviscid theoretical limit):

$$\left.\frac{dC_L}{d\alpha}\right|_{theory} = 2\pi\ \text{rad}^{-1} \approx 0.1097\ \text{deg}^{-1}$$

Strouhal number for vortex shedding characterization:

$$St = \frac{f \cdot L}{u_\infty}, \qquad St_{cylinder} \approx 0.21\ \text{at } Re \approx 10^5$$

Combined standard uncertainty via first-order error propagation (GUM compliant):

$$u_c(y) = \sqrt{\sum_i \left(\frac{\partial y}{\partial x_i}\right)^2 u^2(x_i)}, \qquad U_{95} = 2 \cdot u_c(y)$$

---

### Instrument Specifications and Acceptance Thresholds

| Parameter | Instrument | Range | Resolution | Acceptance Criterion |
|---|---|---|---|---|
| Differential pressure | Honeywell HSCDRRN002ND2A3 | 0–500 Pa | 0.01 Pa | Zero drift < ±0.1 Pa/hr |
| Surface pressure | Validyne DP15 + Scanivalve | 0–350 Pa | 0.005 Pa | Linearity R² > 0.9999 |
| Aerodynamic force | Strain-gauge balance | 0–10 N | 0.01 N | Calibration R² > 0.9998 |
| Temperature | PT100 (settling chamber) | 0–80°C | 0.1°C | Stability < ±1 K per run |
| Barometric pressure | Vaisala PTB330 | 500–1100 hPa | 0.1 hPa | Drift < ±1 hPa per run |
| Angle of attack | Worm-gear mount + digital level | -20° to +30° | 0.05° | Geometric zero to ±0.1° |
| Flow uniformity | 5×5 pitot traverse | Full section | 0.5 mm | Non-uniformity < 1.5% |

---

### Reynolds Number Reference Table (NACA 4412, $c = 150$ mm, $T = 20°C$)

| $u_\infty$ (m/s) | $q_\infty$ (Pa) | $Re$ | Flow Regime |
|---|---|---|---|
| 3 | 5.4 | 29,800 | Fully laminar; large separation bubble likely |
| 5 | 15.0 | 49,700 | Laminar; separation bubble dominant |
| 8 | 38.4 | 79,500 | Transitional; bubble intermittent |
| 10 | 60.0 | 99,400 | Low transitional; standard test point |
| 15 | 135.0 | 149,100 | Mid transitional; primary test point |
| 18 | 194.4 | 178,900 | Upper transitional; turbulent near stall |
| 22 | 290.4 | 218,600 | Near turbulent; thin laminar run near LE |

---

### Python Environment Verification

Run the following block at the start of every laboratory session to confirm the scientific Python stack is fully operational and that all required libraries are importable at their expected versions:

```python
#!/usr/bin/env python3
"""
Lab environment verification script.
Run before every aerodynamics laboratory session.
Expected output: all PASS with version numbers printed.
"""

import sys

checks = [
    ("Python",      lambda: sys.version,              "3.10"),
    ("NumPy",       lambda: __import__('numpy').__version__,       "1."),
    ("SciPy",       lambda: __import__('scipy').__version__,       "1."),
    ("Matplotlib",  lambda: __import__('matplotlib').__version__,  "3."),
]

print("\n  ── Aerodynamics Lab — Environment Verification ──")
print(f"  {'Package':<14}  {'Installed Version':<22}  {'Status':>8}")
print("  " + "-"*48)

all_pass = True
for name, version_fn, min_prefix in checks:
    try:
        ver = version_fn()
        status = "PASS" if ver.startswith(min_prefix) else "CHECK"
        if status != "PASS":
            all_pass = False
        print(f"  {name:<14}  {str(ver):<22}  {status:>8}")
    except Exception as e:
        print(f"  {name:<14}  {'IMPORT ERROR':<22}  {'FAIL':>8}")
        print(f"               → {e}")
        all_pass = False

# Verify numerical stack integrity
try:
    import numpy as np
    import scipy.signal
    import matplotlib
    matplotlib.use('Agg')  # non-interactive backend for headless environments
    import matplotlib.pyplot as plt

    # Quick functional test: FFT round-trip
    x = np.random.default_rng(42).normal(0, 1, 1024)
    X = np.fft.rfft(x)
    x_back = np.fft.irfft(X)
    assert np.allclose(x, x_back, atol=1e-10), "FFT round-trip failed"

    # Quick signal processing test: Butterworth filter design
    b, a = scipy.signal.butter(4, 0.1)
    assert len(b) == 5 and len(a) == 5, "Filter design failed"

    print(f"\n  {'Numerical stack integrity':<36}  {'PASS':>8}")
except AssertionError as e:
    print(f"\n  {'Numerical stack integrity':<36}  {'FAIL':>8}")
    print(f"    AssertionError: {e}")
    all_pass = False

print("  " + "-"*48)
if all_pass:
    print("  All checks passed. Laboratory environment is ready.\n")
else:
    print("  One or more checks failed. Resolve before proceeding.\n")
    sys.exit(1)
```

---

### Common Failure Modes and Diagnostic Actions

When the Bernoulli regression slope falls below 0.990, the most probable causes are a partially blocked pitot tube orifice (insert a 0.3 mm wire to clear debris), a pinhole leak in the pressure tubing (check by pressurizing with a hand pump and observing drift), or ADC zero offset drift exceeding the recorded calibration value. When the lift curve slope exceeds $2\pi/\text{rad}$ by more than 8%, check for tunnel blockage — the model's frontal area at high $\alpha$ can exceed 10% of the working section and generate solid blockage correction requirements using the Maskell blockage formula.

Oscillatory readings in the balance output at the tunnel's natural vibration frequency (typically 15–50 Hz for small research tunnels) indicate structural resonance of the model mount. Address this by adding vibration-damping rubber gaskets at the balance attachment points or by applying the 50 Hz low-pass Butterworth filter defined in Exercise 2 more aggressively. If the stall is abrupt and reproducible within 0.5°, boundary layer transition is natural and the measurement is clean; if stall angle varies by more than 2° between repeat runs at identical conditions, the tunnel turbulence intensity is too high or the model surface has accumulated contamination requiring a wipe with IPA. The oil-film visualization procedure described in the bench setup section is the fastest diagnostic tool for confirming transition location and identifying unexpected separation topology on the model surface.
