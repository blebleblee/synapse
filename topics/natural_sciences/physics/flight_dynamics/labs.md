# Operational Verification Labs: Flight Dynamics

## Objective & Laboratory Bench Setup

Flight dynamics is the physics of bodies moving through fluid media under the competing influences of gravitational attraction, aerodynamic pressure, viscous drag, and lift generation. Unlike the idealized point-mass projectiles of introductory mechanics, real flight involves extended bodies whose orientation, angular momentum, and surface geometry couple back into the translational equations of motion in ways that are both measurable and reproducible at the laboratory bench. These exercises treat the problem empirically first: you will measure forces, fit drag coefficients, extract Reynolds-number dependencies, and stress-test your models against real data before you ever invoke the Navier-Stokes equations as a formal framework.

The goal of this guide is to give a working experimental scientist three complete, reproducible protocols. The first builds intuition for free-fall drag and terminal velocity using direct sensor telemetry. The second characterizes how aerodynamic coefficients vary with geometry and velocity through a systematic parameter sweep and response-curve fit. The third pushes both the physical apparatus and the numerical model to their boundary conditions, quantifies uncertainty propagation formally, and identifies the regimes where the standard drag model breaks down.

### Physical Bench Configuration

Your laboratory bench requires the following instrumented apparatus. A vertical drop tower of minimum 2.5 m effective fall height, constructed from 80/20 aluminum extrusion or equivalent, fitted with a laser-gate timing array at 0.25 m intervals (minimum five gates) to measure instantaneous velocity at each station. A MEMS inertial measurement unit (IMU) — the MPU-6050 or equivalent six-degrees-of-freedom accelerometer/gyroscope — mounted inside a 3D-printed spherical drag body of known cross-sectional area ($A = \pi r^2$, with $r$ measured to $\pm 0.1$ mm using digital calipers). A second drag body of identical mass but different geometry (a cylinder, aspect ratio 2:1) for the parameter variation exercise. A precision analytical balance (0.01 g resolution) for mass determination. A temperature/humidity sensor (DHT22 or equivalent) to record ambient air density conditions, since $\rho_\text{air}$ varies by approximately 1.2% per 10 °C and must be corrected for in any experiment claiming better than 2% drag coefficient accuracy.

The IMU streams data over I2C to a Raspberry Pi 4 (or any Linux SBC), which logs timestamped acceleration vectors at 500 Hz to a CSV file. Laser gate timing provides an independent velocity measurement that cross-validates the IMU integration. This redundancy is not optional — it is the core of the uncertainty analysis in Exercise 3.

### Python Environment Verification

Before any experimental session, verify your scientific Python environment from the terminal. Each of the following commands should return a version string without errors.

```text
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "import astropy; print('Astropy:', astropy.__version__)"
```

The minimum acceptable versions are NumPy 1.24, SciPy 1.10, Matplotlib 3.7, and Astropy 5.3. The Astropy package is included here not for its astronomical functions but for its robust physical constants database and unit-handling framework (`astropy.units`, `astropy.constants`), which enforces dimensional consistency throughout the analysis pipeline — an underused tool in ground-based physics laboratories.

Install or upgrade any missing packages with:

```text
pip install --upgrade numpy scipy matplotlib astropy
```

---

## Exercise 1: Empirical Observation & Measurement Protocol

### Physical Basis: Drag Force and Terminal Velocity

A body falling through air at velocity $v$ experiences a drag force that, in the quadratic (Newton) regime, takes the form:

$$F_D = \frac{1}{2} \rho C_D A v^2$$

where $\rho$ is the air density in $\text{kg/m}^3$, $C_D$ is the dimensionless drag coefficient, $A$ is the reference cross-sectional area in $\text{m}^2$, and $v$ is velocity in $\text{m/s}$. At terminal velocity $v_T$, the drag force exactly balances gravity, giving:

$$v_T = \sqrt{\frac{2mg}{\rho C_D A}}$$

The experimental strategy is to measure $v_T$ directly from the velocity profile as the body asymptotes in the drop tower, then invert this relation to extract $C_D$ given known values of $m$, $g$, $\rho$, and $A$. The differential equation of motion for the falling body is:

$$m\dot{v} = mg - \frac{1}{2}\rho C_D A v^2$$

which integrates analytically to:

$$v(t) = v_T \tanh\left(\frac{g t}{v_T}\right)$$

This hyperbolic tangent velocity profile is what you will fit to the laser gate timing data.

### Measurement Procedure

Begin with the spherical drag body. Measure its diameter at five points using digital calipers and record each measurement in a lab notebook; compute the mean diameter $\bar{d}$ and standard deviation $\sigma_d$. Compute $A = \pi(\bar{d}/2)^2$ and propagate the uncertainty: $\sigma_A = \pi \bar{d}/2 \cdot \sigma_d$. Weigh the body three times on the analytical balance and record the mean mass $m$ and standard deviation $\sigma_m$. Record ambient temperature $T$ (°C) and relative humidity $RH$ (%) from the DHT22.

Compute air density using the empirical formula corrected for humidity. Dry air density at temperature $T$ (in Celsius) and pressure $P$ (in Pascals, measured with a barometer; standard sea-level value is 101325 Pa) is:

$$\rho_\text{dry} = \frac{P M_\text{air}}{R T_K}$$

where $T_K = T + 273.15$ K, $M_\text{air} = 0.028964$ kg/mol, and $R = 8.31446$ J/(mol·K). The humidity correction reduces effective density by a factor $(1 - 0.378 e_w / P)$ where $e_w$ is the saturation vapor pressure in Pa, approximated by the Magnus formula: $e_w = 611.2 \exp(17.67 T / (T + 243.5)) \cdot (RH/100)$.

Arm the laser gate array. Drop the sphere from rest from the top gate with zero initial rotation (hold it magnetically and release by switching off the magnet). Repeat the drop ten times. For each drop, record the inter-gate transit times $\Delta t_i$ and compute instantaneous average velocities $v_i = 0.25 \text{ m} / \Delta t_i$ at the midpoint positions of each gate interval. Simultaneously, the IMU streams 3-axis acceleration in the body frame; this is logged automatically and analyzed in the Python code below.

### Data Analysis: Fitting the Velocity Profile

Save your laser gate data as a plain CSV file named `drop_data.csv` with columns: `drop_id, gate, position_m, velocity_ms`. The following complete Python script loads this data, computes the mean velocity profile across all ten drops, fits the theoretical $v(t) = v_T \tanh(gt/v_T)$ model using `scipy.optimize.curve_fit`, extracts $v_T$ and its confidence interval, and computes $C_D$ with full uncertainty propagation.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ── Measured experimental parameters ──────────────────────────────────────────
# Sphere geometry (from caliper measurements)
d_m_values = np.array([0.0601, 0.0599, 0.0602, 0.0600, 0.0601])  # meters
d_mean = np.mean(d_m_values)
d_std  = np.std(d_m_values, ddof=1)
A_ref  = np.pi * (d_mean / 2)**2        # m^2
sigma_A = np.pi * (d_mean / 2) * d_std  # m^2, first-order propagation

# Mass (grams -> kg)
m_g_values = np.array([47.23, 47.21, 47.22])
m_kg = np.mean(m_g_values) * 1e-3
sigma_m = np.std(m_g_values, ddof=1) * 1e-3

# Ambient conditions
T_C   = 21.4        # Celsius
RH    = 0.52        # fractional (52%)
P_Pa  = 101180.0    # Pascals (from barometer)
R_gas = 8.31446     # J/(mol K)
M_air = 0.028964    # kg/mol
T_K   = T_C + 273.15

# Saturation vapor pressure (Magnus formula)
e_sat = 611.2 * np.exp(17.67 * T_C / (T_C + 243.5))
e_w   = e_sat * RH
rho_air = (P_Pa * M_air / (R_gas * T_K)) * (1 - 0.378 * e_w / P_Pa)
print(f"Air density: {rho_air:.4f} kg/m^3")

# Local gravitational acceleration (use standard; replace with local measurement)
g_local = 9.8101  # m/s^2 — measure with a pendulum if precision >0.1% is needed

# ── Load laser gate velocity data ─────────────────────────────────────────────
# Format: drop_id (int), gate (int 1-5), position_m (float), velocity_ms (float)
# Example data embedded here; replace with np.genfromtxt('drop_data.csv', ...)
raw = np.array([
    # drop 1
    [1, 1, 0.125, 1.421], [1, 2, 0.375, 2.183], [1, 3, 0.625, 2.741],
    [1, 4, 0.875, 3.102], [1, 5, 1.125, 3.287],
    # drop 2
    [2, 1, 0.125, 1.418], [2, 2, 0.375, 2.179], [2, 3, 0.625, 2.738],
    [2, 4, 0.875, 3.098], [2, 5, 1.125, 3.291],
    # drop 3
    [3, 1, 0.125, 1.425], [3, 2, 0.375, 2.188], [3, 3, 0.625, 2.745],
    [3, 4, 0.875, 3.107], [3, 5, 1.125, 3.284],
    # drop 4
    [4, 1, 0.125, 1.419], [4, 2, 0.375, 2.181], [4, 3, 0.625, 2.740],
    [4, 4, 0.875, 3.100], [4, 5, 1.125, 3.288],
    # drop 5
    [5, 1, 0.125, 1.422], [5, 2, 0.375, 2.185], [5, 3, 0.625, 2.743],
    [5, 4, 0.875, 3.104], [5, 5, 1.125, 3.290],
    # drop 6
    [6, 1, 0.125, 1.420], [6, 2, 0.375, 2.182], [6, 3, 0.625, 2.739],
    [6, 4, 0.875, 3.101], [6, 5, 1.125, 3.286],
    # drop 7
    [7, 1, 0.125, 1.423], [7, 2, 0.375, 2.187], [7, 3, 0.625, 2.744],
    [7, 4, 0.875, 3.106], [7, 5, 1.125, 3.292],
    # drop 8
    [8, 1, 0.125, 1.417], [8, 2, 0.375, 2.178], [8, 3, 0.625, 2.737],
    [8, 4, 0.875, 3.097], [8, 5, 1.125, 3.283],
    # drop 9
    [9, 1, 0.125, 1.424], [9, 2, 0.375, 2.186], [9, 3, 0.625, 2.742],
    [9, 4, 0.875, 3.103], [9, 5, 1.125, 3.289],
    # drop 10
    [10, 1, 0.125, 1.421], [10, 2, 0.375, 2.184], [10, 3, 0.625, 2.741],
    [10, 4, 0.875, 3.102], [10, 5, 1.125, 3.288],
])

positions = raw[raw[:, 0] == 1, 2]  # position array (same for all drops)
n_gates = 5

# Compute mean velocity and standard error across drops at each gate
vel_matrix = raw[:, 3].reshape(10, n_gates)
v_mean = np.mean(vel_matrix, axis=0)
v_sem  = np.std(vel_matrix, axis=0, ddof=1) / np.sqrt(10)

# Convert position to time using x = v_T * ln(cosh(g*t/v_T)) — solve numerically
# More direct: compute time from integrating the fitted model. For now, use
# the kinematic estimate t_i ~ integral of 1/v ds from 0 to position_i
# using the trapezoidal rule on the mean velocity profile.
positions_ext = np.insert(positions, 0, 0.0)
v_ext = np.insert(v_mean, 0, 0.0)
dt_intervals = np.diff(positions_ext) / ((v_ext[:-1] + v_ext[1:]) / 2)
t_gates = np.cumsum(dt_intervals)
print(f"Estimated gate times (s): {t_gates}")

# ── Fit velocity model v(t) = v_T * tanh(g * t / v_T) ────────────────────────
def velocity_model(t, v_T):
    return v_T * np.tanh(g_local * t / v_T)

p0 = [5.0]  # initial guess for v_T in m/s
popt, pcov = curve_fit(velocity_model, t_gates, v_mean,
                       p0=p0, sigma=v_sem, absolute_sigma=True)
v_T_fit   = popt[0]
sigma_vT  = np.sqrt(pcov[0, 0])
print(f"\nFitted terminal velocity: {v_T_fit:.4f} ± {sigma_vT:.4f} m/s")

# ── Extract drag coefficient with uncertainty propagation ─────────────────────
# C_D = 2 * m * g / (rho * A * v_T^2)
C_D = 2 * m_kg * g_local / (rho_air * A_ref * v_T_fit**2)

# Partial derivatives for error propagation (first-order linear)
dCD_dm   = 2 * g_local / (rho_air * A_ref * v_T_fit**2)
dCD_dA   = -2 * m_kg * g_local / (rho_air * A_ref**2 * v_T_fit**2)
dCD_dvT  = -4 * m_kg * g_local / (rho_air * A_ref * v_T_fit**3)

sigma_CD = np.sqrt((dCD_dm  * sigma_m)**2 +
                   (dCD_dA  * sigma_A)**2 +
                   (dCD_dvT * sigma_vT)**2)

print(f"Drag coefficient C_D:     {C_D:.4f} ± {sigma_CD:.4f}")
print(f"Literature C_D (sphere):  ~0.47")
print(f"Deviation from literature: {abs(C_D - 0.47)/0.47*100:.2f}%")

# ── Compute Reynolds number at terminal velocity ──────────────────────────────
mu_air   = 1.825e-5  # dynamic viscosity of air at 20 C, Pa·s
Re_T = rho_air * v_T_fit * d_mean / mu_air
print(f"Reynolds number at v_T:   {Re_T:.1f}")
print(f"  (Sphere drag crisis at Re ~ 3e5; we are in Newton drag regime)")

# ── Plot velocity profile: data, fit, and residuals ───────────────────────────
t_smooth = np.linspace(0, t_gates[-1] * 1.4, 500)
v_smooth = velocity_model(t_smooth, v_T_fit)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7),
                                gridspec_kw={'height_ratios': [3, 1]})

ax1.errorbar(t_gates, v_mean, yerr=v_sem, fmt='o', color='steelblue',
             markersize=7, capsize=4, label='Laser gate data (mean ± SEM, n=10)')
ax1.plot(t_smooth, v_smooth, '-', color='firebrick', linewidth=2,
         label=f'Fit: $v_T$ = {v_T_fit:.3f} m/s, $C_D$ = {C_D:.3f}')
ax1.axhline(v_T_fit, linestyle='--', color='gray', linewidth=1,
            label='Terminal velocity $v_T$')
ax1.set_xlabel('Time (s)', fontsize=12)
ax1.set_ylabel('Velocity (m/s)', fontsize=12)
ax1.set_title('Sphere Free-Fall: Velocity Profile and Drag Model Fit', fontsize=13)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Residuals
v_fit_at_gates = velocity_model(t_gates, v_T_fit)
residuals = v_mean - v_fit_at_gates
ax2.bar(t_gates, residuals, width=0.015, color='steelblue', alpha=0.7)
ax2.axhline(0, color='black', linewidth=0.8)
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('Residual (m/s)', fontsize=12)
ax2.set_title('Fit Residuals', fontsize=11)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('exercise1_velocity_profile.png', dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved: exercise1_velocity_profile.png")
```

This script produces two outputs that together constitute a complete verification record. The upper panel shows whether the tanh velocity curve passes through all gate measurements within their standard-error bars — if any gate falls outside, check that drop for initial rotation (the IMU gyroscope channel will show a non-zero angular rate at release). The lower panel shows residuals; systematic curvature in the residuals indicates that the quadratic drag assumption is breaking down, usually because the body is oscillating in orientation during fall. The printed $C_D$ value and its percent deviation from the literature sphere value of 0.47 give an immediate pass/fail criterion: a well-constructed smooth sphere in this Reynolds number range should reproduce $C_D$ to within $\pm 5\%$.

---

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Physical Basis: Geometry Dependence and the Drag Polar

Having measured $C_D$ for a single body at a single velocity, the deeper question is how $C_D$ varies with body geometry and how it depends on flow regime as characterized by the Reynolds number. The Reynolds number is the dimensionless ratio of inertial to viscous forces:

$$Re = \frac{\rho v L}{\mu}$$

where $L$ is the characteristic length (diameter for a sphere, chord length for a wing) and $\mu$ is dynamic viscosity in Pa·s. For a smooth sphere, $C_D \approx 0.47$ across $10^3 < Re < 2\times10^5$; above $Re \approx 3\times10^5$ the boundary layer transitions to turbulence and $C_D$ drops sharply to about 0.2 — the famous drag crisis. For a cylinder with its axis perpendicular to flow, $C_D \approx 1.0$ to 1.2 in the same sub-critical range. These numbers are not simply memorized — they are measured.

### Experimental Protocol: Multi-Body Drop Series

Prepare five drag bodies spanning a range of geometries and cross-sectional areas, with masses matched to within 2% using internal ballast so that mass variation does not confound the drag comparison. A practical set for this laboratory is: Sphere ($d = 60$ mm), Smooth Cylinder ($d = 40$ mm, $h = 80$ mm, axis vertical), Rough Sphere (sandpaper-wrapped, same diameter as smooth sphere), Hemisphere (dome facing downward), and Hemisphere (dome facing upward). Each body has the same IMU installed; only the outer shell changes.

For each body, run ten drops as in Exercise 1. Record the fitted $v_T$ for each body and compute $C_D$ with the same uncertainty propagation. Because mass is matched, the ratio $C_D^{(i)} / C_D^{(j)}$ isolates purely geometric effects. Compile results into a structured NumPy array and generate a comparison plot with the following script.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ── Air density and g_local from Exercise 1 (must be measured same session) ───
rho_air = 1.1972   # kg/m^3 — from Exercise 1 measurement
g_local = 9.8101   # m/s^2
mu_air  = 1.825e-5  # Pa·s at 21.4 C

# ── Body parameter table ───────────────────────────────────────────────────────
# Columns: label, m_kg, A_ref_m2, d_char_m (characteristic length for Re)
bodies = [
    {"label": "Sphere (smooth)",     "m": 0.04722, "A": np.pi*(0.030)**2, "d": 0.060},
    {"label": "Cylinder (vertical)", "m": 0.04701, "A": np.pi*(0.020)**2, "d": 0.040},
    {"label": "Sphere (rough)",      "m": 0.04735, "A": np.pi*(0.030)**2, "d": 0.060},
    {"label": "Hemisphere (dome↓)",  "m": 0.04698, "A": np.pi*(0.030)**2, "d": 0.060},
    {"label": "Hemisphere (dome↑)",  "m": 0.04703, "A": np.pi*(0.030)**2, "d": 0.060},
]

# ── Measured terminal velocities from drop series (mean ± SEM across 10 drops) ─
# Replace with measured values; these are representative lab values
vT_data = np.array([3.288, 2.914, 3.011, 2.421, 3.701])   # m/s mean
vT_sem  = np.array([0.008, 0.011, 0.009, 0.013, 0.010])   # m/s SEM

# ── Compute C_D and Re for each body ──────────────────────────────────────────
C_D_vals    = np.zeros(len(bodies))
sigma_CD    = np.zeros(len(bodies))
Re_vals     = np.zeros(len(bodies))

for i, body in enumerate(bodies):
    m   = body["m"]
    A   = body["A"]
    d   = body["d"]
    vT  = vT_data[i]
    dvT = vT_sem[i]

    C_D_vals[i] = 2 * m * g_local / (rho_air * A * vT**2)
    # Dominant uncertainty term is from vT (squared in denominator)
    dCD_dvT     = -4 * m * g_local / (rho_air * A * vT**3)
    sigma_CD[i] = abs(dCD_dvT) * dvT
    Re_vals[i]  = rho_air * vT * d / mu_air

    print(f"{body['label']:25s}  vT={vT:.3f} m/s  "
          f"C_D={C_D_vals[i]:.3f}±{sigma_CD[i]:.3f}  Re={Re_vals[i]:.0f}")

# ── Literature reference values ────────────────────────────────────────────────
C_D_lit = np.array([0.47, 1.05, 0.52, 1.42, 0.38])
# Sources: White (2011) Fluid Mechanics 7e, Table 11.3

# ── Bar chart: measured vs. literature ────────────────────────────────────────
labels   = [b["label"] for b in bodies]
x        = np.arange(len(labels))
width    = 0.35

fig, ax = plt.subplots(figsize=(11, 5))
bars1 = ax.bar(x - width/2, C_D_vals, width, yerr=sigma_CD,
               capsize=5, label='Measured', color='steelblue', alpha=0.85)
bars2 = ax.bar(x + width/2, C_D_lit, width,
               label='Literature', color='coral', alpha=0.85)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=18, ha='right', fontsize=10)
ax.set_ylabel('Drag coefficient $C_D$', fontsize=12)
ax.set_title('Drag Coefficient: Measured vs. Literature by Body Geometry', fontsize=13)
ax.legend(fontsize=11)
ax.set_ylim(0, 2.0)
ax.grid(axis='y', alpha=0.3)

# Annotate percent deviation
for i in range(len(labels)):
    dev = (C_D_vals[i] - C_D_lit[i]) / C_D_lit[i] * 100
    ax.text(x[i], max(C_D_vals[i], C_D_lit[i]) + 0.08,
            f'{dev:+.1f}%', ha='center', fontsize=8.5, color='dimgray')

plt.tight_layout()
plt.savefig('exercise2_CD_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved: exercise2_CD_comparison.png")
```

### Velocity Sweep: Building the $C_D$–$Re$ Response Curve

The bar chart answers how geometry changes $C_D$ at a single Reynolds number. To characterize how $C_D$ changes with $Re$ for a single body — the response curve that determines whether you are in the Stokes, intermediate, or Newton drag regime — you vary the effective velocity by changing the ballast mass in the sphere body across a wide range. For each mass configuration $m_j$ (use ten equally spaced masses from 10 g to 100 g), drop ten times and extract $v_T^{(j)}$, then compute $C_D^{(j)}$ and $Re^{(j)}$. This gives you ten $(Re, C_D)$ data points spanning roughly one decade in Reynolds number.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

# ── Measured (Re, C_D) response curve for smooth sphere ──────────────────────
# Columns: mass_kg, vT_ms, uncertainty_vT
mass_sweep = np.array([0.0100, 0.0200, 0.0300, 0.0400, 0.0500,
                       0.0600, 0.0700, 0.0800, 0.0900, 0.1000])
vT_sweep   = np.array([1.432, 2.021, 2.473, 2.856, 3.194,
                       3.498, 3.776, 4.034, 4.274, 4.498])  # m/s
vT_unc     = np.array([0.015, 0.012, 0.010, 0.009, 0.009,
                       0.008, 0.008, 0.008, 0.009, 0.009])  # m/s SEM

# Fixed geometry
A_sphere  = np.pi * (0.030)**2  # m^2
d_sphere  = 0.060               # m
rho_air   = 1.1972              # kg/m^3
mu_air    = 1.825e-5            # Pa·s
g_local   = 9.8101              # m/s^2

# Compute C_D and Re
CD_sweep  = 2 * mass_sweep * g_local / (rho_air * A_sphere * vT_sweep**2)
Re_sweep  = rho_air * vT_sweep * d_sphere / mu_air

# Uncertainty in C_D (dominant term: vT)
dCD_dvT  = -4 * mass_sweep * g_local / (rho_air * A_sphere * vT_sweep**3)
sigma_CD_sweep = abs(dCD_dvT) * vT_unc

print("Re       C_D     ±sigma_CD")
for i in range(len(Re_sweep)):
    print(f"{Re_sweep[i]:8.0f}  {CD_sweep[i]:.4f}  {sigma_CD_sweep[i]:.4f}")

# ── Empirical drag correlation: Henderson (1976) for 0.1 < Re < 1e6 ───────────
# C_D = 24/Re + 6/(1+sqrt(Re)) + 0.4  for Re < 2e5 (sub-critical)
def henderson_CD(Re):
    return 24.0/Re + 6.0/(1.0 + np.sqrt(Re)) + 0.4

Re_theory = np.logspace(2.5, 5.5, 400)
CD_theory = henderson_CD(Re_theory)

# ── Fit a power-law to the flat Newton regime (Re > 3000) ─────────────────────
mask_newton = Re_sweep > 3000
if np.sum(mask_newton) >= 3:
    log_Re = np.log10(Re_sweep[mask_newton])
    log_CD = np.log10(CD_sweep[mask_newton])
    coeffs = np.polyfit(log_Re, log_CD, 1)
    slope, intercept = coeffs
    print(f"\nNewton regime power law: C_D = 10^{intercept:.3f} * Re^{slope:.3f}")
    print(f"  (Expected: slope ~ 0 for Newton drag; C_D ~ constant)")

# ── Plot response curve ────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax.errorbar(Re_sweep, CD_sweep, yerr=sigma_CD_sweep,
            fmt='o', color='steelblue', markersize=7, capsize=4,
            label='Measured (sphere, mass sweep)', zorder=5)
ax.plot(Re_theory, CD_theory, '-', color='firebrick', linewidth=2,
        label='Henderson (1976) correlation')
ax.axhline(0.47, linestyle='--', color='gray', linewidth=1.2,
           label='$C_D = 0.47$ (Newton regime reference)')

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Reynolds Number $Re$', fontsize=12)
ax.set_ylabel('Drag Coefficient $C_D$', fontsize=12)
ax.set_title('$C_D$–$Re$ Response Curve: Smooth Sphere (Mass Sweep)', fontsize=13)
ax.legend(fontsize=10)
ax.set_xlim(1e2, 1e6)
ax.set_ylim(0.1, 10)
ax.grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig('exercise2_CD_Re_curve.png', dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved: exercise2_CD_Re_curve.png")
```

The log-log $C_D$–$Re$ plot is the definitive calibration record for your drag bodies. If your measured points track the Henderson correlation within their error bars across the full mass sweep, your measurement system is calibrated and your geometry is accurately characterized. Deviations above the correlation at high Re indicate surface roughness above the implicit smooth-body assumption; deviations below indicate that the body is rotating during fall (the Magnus effect reduces effective drag for a backspin configuration) and the IMU gyroscope channel should show this clearly.

---

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### Physical Basis: Where the Model Breaks Down

The quadratic drag model $F_D = \frac{1}{2}\rho C_D A v^2$ with a constant $C_D$ is an approximation valid within a specific Reynolds number range. It assumes steady, axisymmetric flow, a rigid non-rotating body, incompressible fluid, and negligible wall effects. Each of these assumptions can be violated at the boundary conditions of the experiment. This exercise systematically tests four failure modes: low-Reynolds Stokes regime crossover, body rotation (Magnus effect), wall proximity effect, and density perturbation from air column turbulence. For each, you will measure the deviation from the nominal model, fit a correction function, and propagate uncertainty through a full Monte Carlo simulation.

The transition from Newton to Stokes drag occurs around $Re \sim 1$, where the Stokes law $F_D = 3\pi \mu d v$ applies and gives $C_D = 24/Re$. Your tower cannot reach this regime with macroscopic bodies, but the intermediate regime ($1 < Re < 1000$) is accessible with small, light bodies (expanded polystyrene spheres) and requires the full Schiller-Naumann correlation:

$$C_D = \frac{24}{Re}\left(1 + 0.15 Re^{0.687}\right)$$

which you will verify against direct measurement in Stress Test A.

### Stress Test A: Stokes-to-Newton Crossover

Use lightweight expanded polystyrene (EPS) spheres of densities $\rho_s \approx 20$ kg/m³ in diameters from 10 mm to 60 mm to explore lower Reynolds numbers. Compute the terminal velocity analytically for each sphere under Stokes drag and verify against measurement.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# ── EPS sphere parameters ──────────────────────────────────────────────────────
rho_sphere = 20.0    # kg/m^3 (expanded polystyrene)
rho_air    = 1.1972  # kg/m^3
mu_air     = 1.825e-5
g_local    = 9.8101

diameters_mm = np.array([10, 15, 20, 25, 30, 40, 50, 60])
diameters_m  = diameters_mm * 1e-3

# For each diameter, solve for v_T numerically using Schiller-Naumann C_D
# Force balance: (1/2)*rho_air*C_D(Re)*A*v^2 = m*g
# where Re = rho_air*v*d/mu_air depends on v — must solve self-consistently

def schiller_naumann(Re):
    if Re < 1e-6:
        return 24.0 / 1e-6
    return (24.0 / Re) * (1 + 0.15 * Re**0.687)

def residual_vT(v, d):
    if v <= 0:
        return -1.0
    Re = rho_air * v * d / mu_air
    CD = schiller_naumann(Re)
    r  = d / 2
    A  = np.pi * r**2
    m  = rho_sphere * (4/3) * np.pi * r**3
    F_drag    = 0.5 * rho_air * CD * A * v**2
    F_net = (rho_sphere - rho_air) * (4/3) * np.pi * r**3 * g_local
    return F_net - F_drag

vT_SN   = np.zeros(len(diameters_m))
Re_SN   = np.zeros(len(diameters_m))
CD_SN   = np.zeros(len(diameters_m))

for i, d in enumerate(diameters_m):
    # Bracket: Stokes terminal velocity as lower bound, Newton as upper
    r = d / 2
    A = np.pi * r**2
    m = rho_sphere * (4/3) * np.pi * r**3
    vT_stokes_est = (d**2 * (rho_sphere - rho_air) * g_local) / (18 * mu_air)
    vT_newton_est = np.sqrt(2 * m * g_local / (rho_air * 0.47 * A))
    v_low  = min(vT_stokes_est, vT_newton_est) * 0.01
    v_high = max(vT_stokes_est, vT_newton_est) * 10

    try:
        vT_SN[i] = brentq(residual_vT, v_low, v_high, args=(d,), xtol=1e-6)
    except ValueError:
        vT_SN[i] = np.nan
        print(f"  Bracket failed at d={d*1e3:.0f}mm; check bounds")

    if not np.isnan(vT_SN[i]):
        Re_SN[i] = rho_air * vT_SN[i] * d / mu_air
        CD_SN[i] = schiller_naumann(Re_SN[i])

print(f"\n{'d (mm)':>8} {'vT (m/s)':>10} {'Re':>10} {'C_D':>8}")
for i in range(len(diameters_m)):
    print(f"{diameters_mm[i]:>8.0f} {vT_SN[i]:>10.4f} "
          f"{Re_SN[i]:>10.1f} {CD_SN[i]:>8.4f}")

# ── Measured vT from drop tower (replace with actual measurements) ─────────────
vT_measured = np.array([0.0981, 0.2201, 0.3912, 0.6109, 0.8803,
                         1.5612, 2.4388, 3.5119])  # m/s
vT_meas_unc = np.array([0.003,  0.005,  0.007,  0.009,  0.010,
                         0.012,  0.015,  0.018])   # m/s SEM

# ── Plot: predicted vs. measured, residuals ────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(diameters_mm, vT_SN, 'o-', color='firebrick', linewidth=2,
         markersize=6, label='Schiller-Naumann prediction')
ax1.errorbar(diameters_mm, vT_measured, yerr=vT_meas_unc,
             fmt='s', color='steelblue', markersize=7, capsize=4,
             label='Measured (drop tower, n=10 each)')
ax1.set_xlabel('Sphere diameter (mm)', fontsize=12)
ax1.set_ylabel('Terminal velocity (m/s)', fontsize=12)
ax1.set_title('EPS Sphere Terminal Velocity\nStokes-to-Newton Crossover', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

ax2.scatter(Re_SN, (vT_measured - vT_SN) / vT_SN * 100,
            s=60, color='steelblue', zorder=5)
ax2.axhline(0, color='black', linewidth=1)
ax2.fill_between([Re_SN.min()*0.5, Re_SN.max()*2], -5, 5,
                 color='green', alpha=0.1, label='±5% acceptance band')
ax2.set_xscale('log')
ax2.set_xlabel('Reynolds Number', fontsize=12)
ax2.set_ylabel('Deviation (%)', fontsize=12)
ax2.set_title('Measured vs. Predicted Deviation', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(Re_SN.min()*0.5, Re_SN.max()*2)

plt.tight_layout()
plt.savefig('exercise3_stresstest_A.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Stress Test B: Monte Carlo Uncertainty Propagation

The first-order linear uncertainty propagation used in Exercises 1 and 2 is valid only when the uncertainties are small relative to the parameter values and the model is locally linear. For $C_D$ extraction, the dominant source of uncertainty is $v_T$ (entering as $v_T^{-2}$), which is a nonlinear relationship. A Monte Carlo simulation samples the full joint probability distribution over all input parameters and propagates it through the nonlinear model, yielding the true uncertainty distribution for $C_D$ without the linearity assumption.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, skew, kurtosis

np.random.seed(42)
N_samples = 100_000

# ── Parameter distributions (from Exercise 1 measurements) ────────────────────
# Each is sampled as Gaussian with measured mean and standard deviation.
m_mean,   m_std    = 0.04722,  0.000015   # kg
A_mean,   A_std    = np.pi*(0.030)**2, np.pi*(0.030)*0.0001/2  # m^2
vT_mean,  vT_std   = 3.288,   0.008       # m/s
rho_mean, rho_std  = 1.1972,  0.0012      # kg/m^3 (from T, P, RH uncertainty)
g_mean,   g_std    = 9.8101,  0.0005      # m/s^2 (pendulum calibration unc.)

m_s   = np.random.normal(m_mean,   m_std,   N_samples)
A_s   = np.random.normal(A_mean,   A_std,   N_samples)
vT_s  = np.random.normal(vT_mean,  vT_std,  N_samples)
rho_s = np.random.normal(rho_mean, rho_std, N_samples)
g_s   = np.random.normal(g_mean,   g_std,   N_samples)

# Guard against unphysical samples
m_s   = np.abs(m_s)
A_s   = np.abs(A_s)
vT_s  = np.abs(vT_s)
rho_s = np.abs(rho_s)

# ── Compute C_D for each sample ───────────────────────────────────────────────
CD_mc = 2 * m_s * g_s / (rho_s * A_s * vT_s**2)

# ── Statistics of the C_D distribution ───────────────────────────────────────
CD_p16, CD_p50, CD_p84 = np.percentile(CD_mc, [16, 50, 84])
CD_p025, CD_p975       = np.percentile(CD_mc, [2.5, 97.5])
CD_skew = skew(CD_mc)
CD_kurt = kurtosis(CD_mc)

print(f"Monte Carlo C_D statistics (N={N_samples:,})")
print(f"  Median:          {CD_p50:.5f}")
print(f"  68% CI:          [{CD_p16:.5f}, {CD_p84:.5f}]")
print(f"  95% CI:          [{CD_p025:.5f}, {CD_p975:.5f}]")
print(f"  Asymmetry:       +{CD_p84-CD_p50:.5f} / -{CD_p50-CD_p16:.5f}")
print(f"  Skewness:        {CD_skew:.4f}  (>0: right tail from vT^-2)")
print(f"  Excess kurtosis: {CD_kurt:.4f}")

# ── Variance attribution: sensitivity indices (Saltelli/Sobol method, 1st order) ──
# Approximate by one-at-a-time variance (OAT) relative contribution
def CD_model(m, A, vT, rho, g):
    return 2 * m * g / (rho * A * vT**2)

CD_ref = CD_model(m_mean, A_mean, vT_mean, rho_mean, g_mean)

# Fix all params at mean, vary one at a time
var_m   = np.var(CD_model(m_s,     A_mean, vT_mean, rho_mean, g_mean))
var_A   = np.var(CD_model(m_mean,  A_s,    vT_mean, rho_mean, g_mean))
var_vT  = np.var(CD_model(m_mean,  A_mean, vT_s,    rho_mean, g_mean))
var_rho = np.var(CD_model(m_mean,  A_mean, vT_mean, rho_s,    g_mean))
var_g   = np.var(CD_model(m_mean,  A_mean, vT_mean, rho_mean, g_s))

var_total_OAT = var_m + var_A + var_vT + var_rho + var_g
print(f"\nVariance attribution (OAT first-order fractions):")
for name, var in [("m",   var_m), ("A",   var_A), ("vT",  var_vT),
                  ("rho", var_rho), ("g",  var_g)]:
    print(f"  {name:4s}: {var/var_total_OAT*100:5.1f}%")

# ── Histogram of C_D distribution ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
counts, edges, _ = ax.hist(CD_mc, bins=120, density=True,
                           color='steelblue', alpha=0.7, label='MC samples')
ax.axvline(CD_p50,  color='black',  linewidth=2.0, label=f'Median = {CD_p50:.4f}')
ax.axvline(CD_p16,  color='orange', linewidth=1.5, linestyle='--',
           label=f'68% CI: [{CD_p16:.4f}, {CD_p84:.4f}]')
ax.axvline(CD_p84,  color='orange', linewidth=1.5, linestyle='--')
ax.axvline(CD_p025, color='red',    linewidth=1.2, linestyle=':',
           label=f'95% CI: [{CD_p025:.4f}, {CD_p975:.4f}]')
ax.axvline(CD_p975, color='red',    linewidth=1.2, linestyle=':')
ax.axvline(0.47,    color='green',  linewidth=1.5, linestyle='-.',
           label='Literature $C_D = 0.47$')

x_fit = np.linspace(CD_mc.min(), CD_mc.max(), 400)
ax.plot(x_fit, norm.pdf(x_fit, CD_mc.mean(), CD_mc.std()),
        '-', color='firebrick', linewidth=2, label='Gaussian fit')

ax.set_xlabel('Drag coefficient $C_D$', fontsize=12)
ax.set_ylabel('Probability density', fontsize=12)
ax.set_title('Monte Carlo Uncertainty Propagation: $C_D$ Distribution\n'
             f'(Skewness = {CD_skew:.3f}; dominant source: $v_T$)', fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('exercise3_MC_uncertainty.png', dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved: exercise3_MC_uncertainty.png")
```

The variance attribution printout invariably shows that $v_T$ accounts for over 85% of the total variance in $C_D$ — a direct consequence of the $v_T^{-2}$ dependence. This is the most important practical result of Exercise 3: improving the precision of your drag coefficient measurement means improving your terminal velocity measurement, not your mass or geometry measurements. The right engineering response is to add laser gate stations (reducing SEM by $1/\sqrt{n_\text{gates}}$) or extend the drop height to give the velocity more time to asymptote before the final measurement gate.

The positive skewness ($\approx +0.06$ for typical experimental conditions) confirms that the $v_T^{-2}$ nonlinearity introduces a slight rightward tail in the $C_D$ distribution: the first-order linear propagation underestimates the upper uncertainty bound by a small but measurable amount. For high-precision work (target uncertainty below 1%), the Monte Carlo interval rather than the linear propagation result should be reported as the definitive uncertainty budget.

---

## Laboratory Cheat Sheet & Metric Verification Guide

This section provides the complete quick-reference summary for field use: verification commands, pass/fail criteria, expected numerical outputs, and troubleshooting decision logic. It is intended to be printed and kept at the bench during experimental sessions.

### Environment Verification

Before every experimental session, run the following verification block from a terminal. All six checks must pass before data collection begins.

```python
# Run as: python verify_env.py
import sys

checks = []

try:
    import numpy as np
    checks.append(("NumPy",      np.__version__,      True))
except ImportError as e:
    checks.append(("NumPy",      str(e),              False))

try:
    import scipy
    checks.append(("SciPy",      scipy.__version__,   True))
except ImportError as e:
    checks.append(("SciPy",      str(e),              False))

try:
    import matplotlib
    checks.append(("Matplotlib", matplotlib.__version__, True))
except ImportError as e:
    checks.append(("Matplotlib", str(e),              False))

try:
    import astropy
    checks.append(("Astropy",    astropy.__version__, True))
except ImportError as e:
    checks.append(("Astropy",    str(e),              False))

try:
    from scipy.optimize import curve_fit, brentq
    checks.append(("scipy.optimize.curve_fit + brentq", "OK", True))
except ImportError as e:
    checks.append(("scipy.optimize", str(e),          False))

try:
    from scipy.constants import g
    assert abs(g - 9.80665) < 1e-4
    checks.append(("scipy.constants.g",
                   f"{g:.5f} m/s^2 (standard gravity)", True))
except Exception as e:
    checks.append(("scipy.constants.g", str(e),       False))

print("\n── Environment Verification ─────────────────────────")
all_pass = True
for name, value, status in checks:
    icon = "✓" if status else "✗"
    print(f"  {icon}  {name:40s} {value}")
    if not status:
        all_pass = False

print("─────────────────────────────────────────────────────")
if all_pass:
    print("  ALL CHECKS PASSED — bench is ready for data collection.\n")
else:
    print("  ONE OR MORE CHECKS FAILED — resolve before proceeding.\n")
    sys.exit(1)
```

### Physical Constants Reference Table

| Quantity | Symbol | Value | Units | Source |
|---|---|---|---|---|
| Standard gravity | $g_0$ | 9.80665 | m/s² | BIPM |
| Air density (20°C, 101.325 kPa, dry) | $\rho_\text{air}$ | 1.2041 | kg/m³ | NIST |
| Dynamic viscosity of air (20°C) | $\mu$ | $1.825 \times 10^{-5}$ | Pa·s | White (2011) |
| Kinematic viscosity of air (20°C) | $\nu$ | $1.516 \times 10^{-5}$ | m²/s | White (2011) |
| Sphere $C_D$ (Newton regime) | $C_D$ | 0.47 | — | White (2011) |
| Cylinder $C_D$ (axis $\perp$ flow) | $C_D$ | 1.0–1.2 | — | White (2011) |
| Stokes drag crossover | $Re$ | $\sim 1$ | — | — |
| Newton drag onset | $Re$ | $\sim 10^3$ | — | — |
| Sphere drag crisis | $Re$ | $\sim 3 \times 10^5$ | — | — |

### Pass/Fail Acceptance Criteria

| Metric | Acceptance Threshold | Action if Failed |
|---|---|---|
| $C_D$ deviation from literature (sphere) | $< 5\%$ | Check for body rotation (IMU gyro), wall proximity |
| $C_D$ repeatability (10 drops, same body) | $\sigma_{C_D} / C_D < 2\%$ | Check laser gate alignment, drafts in room |
| Velocity residuals (tanh fit) | All gates within $\pm 2\sigma$ | Inspect individual drop traces for anomalies |
| Monte Carlo 68% CI width | $< 0.03$ in $C_D$ units | Extend drop tower or add gates |
| $v_T$ variance fraction from vT source | $> 70\%$ expected | If $< 70\%$, re-measure $m$ and $A$ precision |
| Re computed at $v_T$ | $10^3 < Re < 2\times10^5$ | If outside, body is in wrong drag regime for constant-$C_D$ model |

### Diagnostic Decision Logic

If the fitted $C_D$ is systematically **above** the literature value for the sphere geometry, the most probable causes in descending order of likelihood are: (1) the body is rotating during fall (Magnus effect generating additional side force, which the planar drag model misinterprets as excess drag — confirm on IMU gyroscope channel), (2) the drop tower has significant wall-proximity effects (the blockage ratio $A_\text{body}/A_\text{tower}$ should be $< 0.03$ to keep wall corrections below 1%), or (3) the ambient air density was computed without humidity correction and $\rho_\text{air}$ is overestimated.

If the fitted $C_D$ is systematically **below** the literature value, the dominant cause is usually an underestimated terminal velocity — which occurs when the drop tower is too short and the body has not yet reached $v_T$ at the final gate. The diagnostic is to compare $v_\text{final gate}$ to the fitted $v_T$: if the ratio is below 0.95, the tower is too short for that body configuration and you must either use a taller tower, reduce body mass, or increase body cross-sectional area.

If the velocity residuals show **systematic curvature** rather than random scatter around zero, the tanh model itself is misspecified. This occurs either because initial velocity was non-zero (hold the magnet closer to the top gate so drop is from rest) or because $C_D$ is itself velocity-dependent in the measured range (use the Schiller-Naumann model from Exercise 3 Stress Test A rather than the constant-$C_D$ Newton model).

The variance attribution from the Monte Carlo analysis tells you precisely where to invest calibration effort. In a well-characterized experiment, the terminal velocity measurement should account for 85–90% of the total $C_D$ variance. If the mass term is instead dominant (more than 20%), your body has a large mass uncertainty relative to its size, suggesting internal structure that shifts center of mass between drops — open and re-ballast. If the air density term exceeds 10%, your temperature or pressure sensor is underperforming and should be cross-calibrated against a certified reference.
