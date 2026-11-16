# Operational Verification Labs: Flying And Aviation

## Objective & Laboratory Bench Setup

The empirical study of flight demands direct engagement with the physical forces that enable controlled motion through a compressible fluid medium. This laboratory sequence positions you at the intersection of classical fluid dynamics, atmospheric thermodynamics, and rigid-body kinematics to measure, calibrate, and validate the fundamental parameters governing aviation. You will construct aerodynamic test apparatus, instrument airflow velocity fields, measure lift and drag force components under variable Reynolds number regimes, and analyze the stability derivatives that determine aircraft control authority. Each exercise progresses from baseline observation through parametric sweep to boundary stress testing, culminating in a complete characterization of flight performance envelopes with rigorous uncertainty quantification.

Your laboratory bench requires a subsonic wind tunnel or equivalent airflow generation system capable of delivering controlled, laminar flow at velocities ranging from 5 to 40 meters per second. Mount a precision force balance with three-axis load cell arrays to resolve lift, drag, and pitching moment forces with millinewton resolution. Install a pitot-static probe array upstream and downstream of your test section to capture stagnation and static pressure distributions, coupled to differential pressure transducers with 0.1 Pascal sensitivity. Acquire a digital angle-of-attack protractor or servo-driven goniometer to sweep airfoil inclination through ±30 degrees with 0.1-degree precision. Equip your data acquisition system with National Instruments USB-6343 or equivalent multichannel ADC hardware, synchronized to capture force, pressure, and angle measurements at 1 kHz sampling rates. For flow visualization, prepare smoke generators or neutrally buoyant helium-filled soap bubbles illuminated by laser sheet optics, captured by high-speed cameras operating at 120 frames per second minimum. Temperature and humidity sensors must record ambient conditions to enable air density corrections via the ideal gas law. Your Python environment must include NumPy 1.24+, SciPy 1.10+, Matplotlib 3.7+, and Pandas 2.0+ for signal processing, curve fitting, and uncertainty propagation through Monte Carlo simulation.

Verify your scientific Python stack integrity by executing the following diagnostic sequence in your terminal environment. Open a command shell and confirm each module loads without import errors, reporting version numbers that meet or exceed the minimum specifications enumerated above.

```python
python -c "import numpy as np; print(f'NumPy: {np.__version__}')"
python -c "import scipy as sp; print(f'SciPy: {sp.__version__}')"
python -c "import matplotlib as mpl; print(f'Matplotlib: {mpl.__version__}')"
python -c "import pandas as pd; print(f'Pandas: {pd.__version__}')"
```

Establish a dedicated laboratory notebook directory structure to archive raw telemetry streams, calibration coefficients, and post-processed datasets. Create subdirectories labeled `raw_data/`, `calibration/`, `processed/`, and `figures/` to maintain provenance chains from sensor voltages through final publication-quality plots. Initialize a Git repository in your project root to version-control analysis scripts and experimental protocols, ensuring reproducibility across repeated measurement campaigns.

Calibrate your force balance by applying known deadweight masses in the vertical axis and recording voltage outputs across the full anticipated load range. Construct a linear regression model mapping sensor voltage to force magnitude, extracting slope and intercept coefficients with uncertainty bounds derived from the least-squares covariance matrix. Similarly, calibrate pressure transducers against a mercury manometer or NIST-traceable pressure standard, spanning the expected dynamic pressure range corresponding to your target velocity envelope. Record ambient temperature and barometric pressure at the start of each experimental session, computing air density via $\rho = p / (R_{\text{specific}} T)$ where $R_{\text{specific}} = 287.05 \, \text{J/(kg·K)}$ for dry air. This density correction proves essential when comparing data acquired across different days or atmospheric conditions, as both lift and drag forces scale linearly with freestream density.

Mount a NACA 0012 symmetric airfoil section as your primary test article, selecting a chord length $c$ between 10 and 20 centimeters and a span sufficient to minimize three-dimensional wingtip vortex effects within your tunnel width. Machine the airfoil from rigid foam or composite laminate to maintain dimensional tolerance within ±0.5 millimeters of the analytical profile, verified by optical profilometry or caliper traverse. Attach the model to your force balance via a streamlined sting support, positioned at the quarter-chord point to minimize pitching moment contamination from mounting interference. Ensure the sting diameter remains below 5% of the chord to avoid excessive wake blockage.

## Exercise 1: Empirical Observation & Measurement Protocol

Begin your flight mechanics investigation by establishing the baseline aerodynamic force coefficients for a symmetric airfoil across the linear lift regime. This exercise constructs the empirical foundation upon which all subsequent parametric studies rest, measuring lift $L$, drag $D$, and pitching moment $M$ as functions of angle of attack $\alpha$ under fixed freestream conditions. You will discover that the relationship between lift and angle of attack remains rigorously linear for small angles, described by the lift slope $C_{L\alpha} = \partial C_L / \partial \alpha$, while drag exhibits a quadratic dependence arising from the induced drag component generated by finite wing circulation. The pitching moment about the quarter-chord point remains nearly constant for symmetric sections, validating the aerodynamic center location predicted by thin airfoil theory.

Set your wind tunnel to deliver a nominal freestream velocity $U_\infty = 20.0 \, \text{m/s}$, verified by pitot-static probe measurements. Compute the dynamic pressure $q_\infty = \frac{1}{2} \rho U_\infty^2$, where $\rho$ represents the air density computed from your ambient pressure and temperature readings. For standard sea-level conditions at $T = 288.15 \, \text{K}$ and $p = 101325 \, \text{Pa}$, you obtain $\rho = 1.225 \, \text{kg/m}^3$, yielding $q_\infty = 245 \, \text{Pa}$. This dynamic pressure constitutes the reference scaling parameter for all subsequent force coefficient definitions.

Position your NACA 0012 airfoil at zero geometric angle of attack, defined as the chord line aligned parallel to the tunnel freestream direction. Allow the flow to stabilize for 30 seconds, ensuring turbulent fluctuations decay to a steady-state mean. Acquire force balance data continuously for 10 seconds at 1 kHz sampling rate, accumulating 10,000 samples per measurement. Simultaneously record pitot probe pressures and ambient conditions. Extract time-averaged force components $\overline{L}$ and $\overline{D}$ along with standard deviations $\sigma_L$ and $\sigma_D$ to quantify measurement precision. Compute the lift coefficient $C_L = \overline{L} / (q_\infty S)$ and drag coefficient $C_D = \overline{D} / (q_\infty S)$, where $S = c \cdot b$ denotes the planform area with chord $c$ and span $b$. For a symmetric airfoil at zero angle of attack, you expect $C_L \approx 0$ within measurement uncertainty, while $C_D$ reflects the profile drag arising from skin friction and pressure recovery in the boundary layer.

Increment the angle of attack in 2-degree steps from $\alpha = 0°$ to $\alpha = 16°$, repeating the 10-second averaging procedure at each station. Beyond approximately $\alpha = 12°$ for typical NACA sections at moderate Reynolds numbers, you will observe lift curve departure from linearity as the boundary layer separates from the suction surface, precipitating stall. Continue measurements through $\alpha = 20°$ to fully characterize the post-stall regime, where lift degrades and drag increases dramatically due to massive flow separation and vortex shedding.

Process your accumulated dataset using the following Python script, which reads raw force balance voltages, applies calibration transformations, computes dimensionless coefficients, and generates a publication-quality lift and drag polar plot. Save this script as `process_airfoil_sweep.py` in your project root directory.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Physical constants and calibration coefficients
RHO_AIR = 1.225  # kg/m^3, standard sea level
U_INF = 20.0     # m/s, freestream velocity
CHORD = 0.15     # m, airfoil chord length
SPAN = 0.40      # m, model span
S_REF = CHORD * SPAN  # m^2, reference area

# Force balance calibration (from deadweight calibration)
# Lift channel: F_lift [N] = slope_L * V_lift [V] + intercept_L
SLOPE_L = 2.453  # N/V
INTERCEPT_L = -0.012  # N
# Drag channel: F_drag [N] = slope_D * V_drag [V] + intercept_D
SLOPE_D = 0.982  # N/V
INTERCEPT_D = -0.005  # N

# Compute dynamic pressure
q_inf = 0.5 * RHO_AIR * U_INF**2
print(f"Dynamic pressure: {q_inf:.3f} Pa")
print(f"Reference area: {S_REF:.6f} m^2")
print(f"Reynolds number: {(RHO_AIR * U_INF * CHORD / 1.81e-5):.0f}")

# Load raw voltage data: columns [alpha_deg, V_lift, V_drag]
# Each row represents one angle-of-attack measurement station
data = np.array([
    [0.0, -0.005, 0.035],
    [2.0, 0.124, 0.038],
    [4.0, 0.254, 0.045],
    [6.0, 0.383, 0.056],
    [8.0, 0.510, 0.071],
    [10.0, 0.633, 0.092],
    [12.0, 0.748, 0.119],
    [14.0, 0.812, 0.158],
    [16.0, 0.785, 0.215],
    [18.0, 0.695, 0.287],
    [20.0, 0.598, 0.351]
])

alpha_deg = data[:, 0]
alpha_rad = np.deg2rad(alpha_deg)
V_lift = data[:, 1]
V_drag = data[:, 2]

# Apply calibration to convert voltages to forces
F_lift = SLOPE_L * V_lift + INTERCEPT_L
F_drag = SLOPE_D * V_drag + INTERCEPT_D

# Compute dimensionless coefficients
C_L = F_lift / (q_inf * S_REF)
C_D = F_drag / (q_inf * S_REF)

# Perform linear regression on the linear lift region (0° to 10°)
linear_mask = alpha_deg <= 10.0
fit = stats.linregress(alpha_rad[linear_mask], C_L[linear_mask])
C_L_alpha = fit.slope  # per radian
C_L_alpha_deg = C_L_alpha * np.pi / 180.0  # per degree
alpha_L0 = -fit.intercept / fit.slope  # zero-lift angle

print(f"\nLift curve slope: {C_L_alpha:.4f} per radian ({C_L_alpha_deg:.4f} per degree)")
print(f"Zero-lift angle: {np.rad2deg(alpha_L0):.3f} degrees")
print(f"R^2: {fit.rvalue**2:.6f}")

# Create DataFrame for tabular output
df = pd.DataFrame({
    'alpha_deg': alpha_deg,
    'C_L': C_L,
    'C_D': C_D,
    'L/D': C_L / C_D
})
print("\n" + df.to_string(index=False))

# Generate lift curve and drag polar plots
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Lift curve
axes[0].plot(alpha_deg, C_L, 'o-', color='#2E86AB', linewidth=2, markersize=6, label='Measured')
alpha_fit = np.linspace(0, 10, 100)
C_L_fit = fit.intercept + fit.slope * np.deg2rad(alpha_fit)
axes[0].plot(alpha_fit, C_L_fit, '--', color='#A23B72', linewidth=1.5, label=f'Linear fit: $C_L = {C_L_alpha:.3f}\\alpha$')
axes[0].axhline(0, color='black', linewidth=0.5, linestyle=':')
axes[0].axvline(0, color='black', linewidth=0.5, linestyle=':')
axes[0].set_xlabel('Angle of Attack $\\alpha$ [deg]', fontsize=11)
axes[0].set_ylabel('Lift Coefficient $C_L$', fontsize=11)
axes[0].set_title('Lift Curve: NACA 0012', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3)
axes[0].legend(fontsize=9)

# Drag polar
axes[1].plot(C_D, C_L, 'o-', color='#2E86AB', linewidth=2, markersize=6)
for i, alpha in enumerate(alpha_deg):
    if i % 2 == 0:
        axes[1].annotate(f'{alpha:.0f}°', xy=(C_D[i], C_L[i]), xytext=(5, 5),
                        textcoords='offset points', fontsize=8, alpha=0.7)
axes[1].axhline(0, color='black', linewidth=0.5, linestyle=':')
axes[1].axvline(0, color='black', linewidth=0.5, linestyle=':')
axes[1].set_xlabel('Drag Coefficient $C_D$', fontsize=11)
axes[1].set_ylabel('Lift Coefficient $C_L$', fontsize=11)
axes[1].set_title('Drag Polar: NACA 0012', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/airfoil_characteristics.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nFigure saved: figures/airfoil_characteristics.png")
```

Execute this analysis script from your project root directory, ensuring the `figures/` subdirectory exists to receive output graphics. The console output reports your extracted lift curve slope, typically $C_{L\alpha} \approx 0.10$ to $0.11$ per degree for two-dimensional airfoils in the subcritical Reynolds number regime, aligning with thin airfoil theory predictions of $2\pi$ per radian for inviscid flow modified by viscous boundary layer effects. The drag polar reveals the classic parabolic relationship $C_D = C_{D0} + k C_L^2$, where $C_{D0}$ represents the zero-lift profile drag and $k$ quantifies the induced drag efficiency factor. For your finite-span model, $k$ relates to the effective aspect ratio and Oswald efficiency factor.

Examine your lift curve plot carefully, noting the departure from linearity beyond $\alpha \approx 12°$ as leading-edge separation initiates stall. The maximum lift coefficient $C_{L,\text{max}}$ typically reaches 1.2 to 1.5 for smooth airfoils before degrading sharply. The drag polar demonstrates that minimum drag occurs near zero lift for symmetric sections, while the maximum lift-to-drag ratio $L/D$ appears at a moderate lift coefficient around $C_L = 0.4$ to $0.6$, corresponding to the optimal cruise condition for unpowered gliders.

Quantify measurement uncertainty by propagating your force balance voltage standard deviations through the calibration transformations and coefficient definitions. For each angle of attack, compute $\sigma_{C_L} = (1 / q_\infty S) \sqrt{(\sigma_L)^2 + (C_L \sigma_q / q_\infty)^2}$, where $\sigma_q$ arises from velocity measurement uncertainty. Typical uncertainties remain below 2% of the measured coefficient values in the linear regime, expanding to 5% near stall due to increased unsteady fluctuations.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

The lift and drag characteristics you measured in Exercise 1 depend critically on the Reynolds number $\text{Re} = \rho U_\infty c / \mu$, which quantifies the ratio of inertial to viscous forces in the boundary layer. This exercise sweeps freestream velocity across a factor-of-four range, generating a family of lift curves that reveal Reynolds number effects on separation onset, stall angle, and maximum lift coefficient. You will discover that higher Reynolds numbers delay stall by energizing the boundary layer, enabling it to remain attached against stronger adverse pressure gradients. Simultaneously, you will measure the drag coefficient's Reynolds number dependence, observing that skin friction drag decreases with increasing Reynolds number as the boundary layer transition point moves forward and the turbulent boundary layer profile becomes fuller.

Configure your wind tunnel to deliver five discrete freestream velocities: $U_\infty = 10, 15, 20, 25, 30 \, \text{m/s}$, corresponding to Reynolds numbers spanning approximately $1.0 \times 10^5$ to $3.0 \times 10^5$ based on your airfoil chord length. At each velocity setting, conduct a complete angle-of-attack sweep from $0°$ to $20°$ in 2-degree increments, replicating the measurement protocol from Exercise 1. Before each velocity change, allow the tunnel 60 seconds to stabilize at the new setpoint, verified by pitot probe convergence to within ±0.5% of the target dynamic pressure.

Record your ambient temperature and barometric pressure at the start of each velocity series, computing the instantaneous air density and kinematic viscosity $\nu = \mu / \rho$ where the dynamic viscosity $\mu$ follows Sutherland's law: $\mu = \mu_0 (T / T_0)^{3/2} (T_0 + S) / (T + S)$ with reference values $\mu_0 = 1.716 \times 10^{-5} \, \text{Pa·s}$, $T_0 = 273.15 \, \text{K}$, and Sutherland constant $S = 110.4 \, \text{K}$. This temperature correction proves essential when comparing data acquired across seasonal variations or climate-controlled laboratory drift.

Organize your expanded dataset as a multi-indexed Pandas DataFrame, facilitating Reynolds-number-grouped operations and vectorized coefficient calculations. The following script processes the velocity sweep data, generates a family of Reynolds-number-parameterized lift curves, and extracts the Reynolds number dependence of the stall angle and maximum lift coefficient through polynomial interpolation.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import brentq

# Physical constants
RHO_AIR = 1.225  # kg/m^3
MU_AIR = 1.81e-5  # Pa·s, dynamic viscosity at 15°C
NU_AIR = MU_AIR / RHO_AIR  # m^2/s, kinematic viscosity
CHORD = 0.15  # m
SPAN = 0.40  # m
S_REF = CHORD * SPAN

# Calibration coefficients (same as Exercise 1)
SLOPE_L = 2.453
INTERCEPT_L = -0.012
SLOPE_D = 0.982
INTERCEPT_D = -0.005

# Velocity sweep data: [U_inf, alpha_deg, V_lift, V_drag]
raw_data = np.array([
    # U_inf = 10 m/s, Re = 82,873
    [10.0, 0.0, -0.003, 0.072],
    [10.0, 2.0, 0.032, 0.076],
    [10.0, 4.0, 0.066, 0.085],
    [10.0, 6.0, 0.099, 0.098],
    [10.0, 8.0, 0.130, 0.115],
    [10.0, 10.0, 0.159, 0.138],
    [10.0, 12.0, 0.182, 0.168],
    [10.0, 14.0, 0.195, 0.208],
    [10.0, 16.0, 0.188, 0.265],
    [10.0, 18.0, 0.172, 0.328],
    [10.0, 20.0, 0.151, 0.385],
    # U_inf = 15 m/s, Re = 124,309
    [15.0, 0.0, -0.004, 0.050],
    [15.0, 2.0, 0.070, 0.054],
    [15.0, 4.0, 0.144, 0.062],
    [15.0, 6.0, 0.217, 0.075],
    [15.0, 8.0, 0.289, 0.093],
    [15.0, 10.0, 0.357, 0.117],
    [15.0, 12.0, 0.419, 0.149],
    [15.0, 14.0, 0.462, 0.195],
    [15.0, 16.0, 0.450, 0.262],
    [15.0, 18.0, 0.401, 0.345],
    [15.0, 20.0, 0.348, 0.425],
    # U_inf = 20 m/s, Re = 165,746
    [20.0, 0.0, -0.005, 0.035],
    [20.0, 2.0, 0.124, 0.038],
    [20.0, 4.0, 0.254, 0.045],
    [20.0, 6.0, 0.383, 0.056],
    [20.0, 8.0, 0.510, 0.071],
    [20.0, 10.0, 0.633, 0.092],
    [20.0, 12.0, 0.748, 0.119],
    [20.0, 14.0, 0.812, 0.158],
    [20.0, 16.0, 0.785, 0.215],
    [20.0, 18.0, 0.695, 0.287],
    [20.0, 20.0, 0.598, 0.351],
    # U_inf = 25 m/s, Re = 207,183
    [25.0, 0.0, -0.006, 0.026],
    [25.0, 2.0, 0.193, 0.028],
    [25.0, 4.0, 0.393, 0.034],
    [25.0, 6.0, 0.592, 0.044],
    [25.0, 8.0, 0.788, 0.058],
    [25.0, 10.0, 0.978, 0.077],
    [25.0, 12.0, 1.158, 0.102],
    [25.0, 14.0, 1.292, 0.138],
    [25.0, 16.0, 1.315, 0.191],
    [25.0, 18.0, 1.195, 0.265],
    [25.0, 20.0, 1.048, 0.342],
    # U_inf = 30 m/s, Re = 248,619
    [30.0, 0.0, -0.007, 0.020],
    [30.0, 2.0, 0.278, 0.022],
    [30.0, 4.0, 0.565, 0.027],
    [30.0, 6.0, 0.850, 0.035],
    [30.0, 8.0, 1.132, 0.047],
    [30.0, 10.0, 1.407, 0.063],
    [30.0, 12.0, 1.668, 0.084],
    [30.0, 14.0, 1.875, 0.115],
    [30.0, 16.0, 1.920, 0.161],
    [30.0, 18.0, 1.765, 0.228],
    [30.0, 20.0, 1.562, 0.305]
])

# Build DataFrame with computed quantities
df = pd.DataFrame(raw_data, columns=['U_inf', 'alpha_deg', 'V_lift', 'V_drag'])

# Compute Reynolds number and dynamic pressure for each row
df['Re'] = RHO_AIR * df['U_inf'] * CHORD / MU_AIR
df['q_inf'] = 0.5 * RHO_AIR * df['U_inf']**2

# Apply force calibrations
df['F_lift'] = SLOPE_L * df['V_lift'] + INTERCEPT_L
df['F_drag'] = SLOPE_D * df['V_drag'] + INTERCEPT_D

# Compute coefficients
df['C_L'] = df['F_lift'] / (df['q_inf'] * S_REF)
df['C_D'] = df['F_drag'] / (df['q_inf'] * S_REF)

# Extract unique Reynolds numbers
Re_values = df['Re'].unique()
print("Reynolds numbers tested:")
for re in Re_values:
    print(f"  {re:.0f}")

# Plot family of lift curves
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(Re_values)))

# Store maximum C_L and corresponding alpha for each Re
Re_summary = []

for i, (re_val, color) in enumerate(zip(Re_values, colors)):
    subset = df[df['Re'] == re_val].sort_values('alpha_deg')
    alpha = subset['alpha_deg'].values
    C_L = subset['C_L'].values
    C_D = subset['C_D'].values
    
    # Find maximum C_L and stall angle
    idx_max = np.argmax(C_L)
    C_L_max = C_L[idx_max]
    alpha_stall = alpha[idx_max]
    
    Re_summary.append({'Re': re_val, 'C_L_max': C_L_max, 'alpha_stall': alpha_stall})
    
    label = f'Re = {re_val/1e3:.0f}k'
    axes[0].plot(alpha, C_L, 'o-', color=color, linewidth=2, markersize=5, label=label)

axes[0].set_xlabel('Angle of Attack $\\alpha$ [deg]', fontsize=11)
axes[0].set_ylabel('Lift Coefficient $C_L$', fontsize=11)
axes[0].set_title('Reynolds Number Effect on Lift Curve', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3)
axes[0].legend(fontsize=9, loc='upper left')
axes[0].set_xlim(0, 20)
axes[0].set_ylim(-0.2, 1.8)

# Plot C_L_max and stall angle vs Reynolds number
Re_df = pd.DataFrame(Re_summary)
ax2 = axes[1]
ax2.plot(Re_df['Re']/1e3, Re_df['C_L_max'], 'o-', color='#2E86AB', linewidth=2, markersize=7, label='$C_{L,max}$')
ax2.set_xlabel('Reynolds Number [×10³]', fontsize=11)
ax2.set_ylabel('Maximum Lift Coefficient $C_{L,max}$', fontsize=11, color='#2E86AB')
ax2.tick_params(axis='y', labelcolor='#2E86AB')
ax2.grid(True, alpha=0.3)

ax2_twin = ax2.twinx()
ax2_twin.plot(Re_df['Re']/1e3, Re_df['alpha_stall'], 's-', color='#A23B72', linewidth=2, markersize=7, label='$\\alpha_{stall}$')
ax2_twin.set_ylabel('Stall Angle $\\alpha_{stall}$ [deg]', fontsize=11, color='#A23B72')
ax2_twin.tick_params(axis='y', labelcolor='#A23B72')

axes[1].set_title('Reynolds Number Scaling Laws', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('figures/reynolds_sweep.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nReynolds Number Summary:")
print(Re_df.to_string(index=False))
print(f"\nFigure saved: figures/reynolds_sweep.png")
```

Run this analysis to generate a family of lift curves color-coded by Reynolds number. The systematic upward shift in maximum lift coefficient with increasing Reynolds number reflects delayed boundary layer separation, as the higher momentum flux near the wall enables the flow to negotiate stronger adverse pressure gradients before detaching. Quantitatively, $C_{L,\text{max}}$ typically increases from approximately 1.3 at $\text{Re} = 8 \times 10^4$ to 1.6 at $\text{Re} = 2.5 \times 10^5$, approaching the asymptotic high-Reynolds-number limit where further increases yield diminishing returns.

The stall angle similarly advances from approximately $14°$ at low Reynolds number to $16°$ at high Reynolds number, granting the pilot an additional margin before departure from controlled flight. This Reynolds number sensitivity explains why model aircraft and unmanned aerial vehicles operating at chord-based Reynolds numbers below $5 \times 10^5$ exhibit dramatically different stall characteristics compared to full-scale general aviation aircraft cruising at $\text{Re} \sim 5 \times 10^6$.

Examine the drag coefficient evolution by plotting $C_D$ versus Reynolds number at fixed angle of attack. Select $\alpha = 0°$ to isolate profile drag without induced drag contamination. You will observe a monotonic decrease in $C_D$ with increasing Reynolds number, reflecting the reduction in skin friction coefficient as the boundary layer transitions from laminar to turbulent and the turbulent boundary layer thickness decreases. This drag reduction constitutes a primary driver for designing high-aspect-ratio wings that maximize Reynolds number by increasing chord length, balanced against structural weight penalties.

Extend your analysis by computing the lift-to-drag ratio $L/D$ across the full measurement matrix, identifying the optimal angle of attack that maximizes aerodynamic efficiency at each Reynolds number. For gliders and sailplanes, this maximum $L/D$ point defines the minimum sink rate speed, while for powered aircraft it determines the velocity for maximum range via the Breguet range equation. Plot $L/D$ versus $C_L$ for each Reynolds number on a single figure, revealing that the maximum efficiency point shifts to higher lift coefficients as Reynolds number increases, due to the proportionally larger decrease in drag compared to the modest increase in achievable lift.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

The controlled parametric sweeps conducted in Exercises 1 and 2 characterized nominal flight performance within the conventional operating envelope. Real-world aviation, however, demands quantification of extreme off-design conditions: high-angle maneuvers approaching stall, asymmetric wing contamination by ice accretion or surface roughness, and compressibility effects emerging as flight Mach number exceeds $M = 0.3$. This exercise probes these boundary regimes, measuring the degradation in lift curve slope and maximum lift coefficient induced by simulated leading-edge roughness, while quantifying the uncertainty propagation through your complete measurement and analysis chain via Monte Carlo simulation.

Begin by establishing a baseline reference dataset at your nominal Reynolds number $\text{Re} = 1.66 \times 10^5$ ($U_\infty = 20 \, \text{m/s}$), replicating the angle-of-attack sweep from Exercise 1 with ten repeated measurement cycles to accumulate statistics on run-to-run variability. For each angle-of-attack station, compute the mean and standard deviation of lift and drag forces across the ten trials, revealing the irreducible measurement noise floor set by tunnel turbulence intensity, force balance thermal drift, and unsteady vortex shedding. Typical coefficient of variation (standard deviation divided by mean) remains below 1% in the linear lift regime, expanding to 3-5% near stall where flow unsteadiness intensifies.

Simulate leading-edge contamination by adhering carborundum grit (60-grit sandpaper, nominal grain size 250 micrometers) to the first 5% of chord on the upper surface, mimicking insect debris accumulation or light rime ice. This deliberate roughness element trips the boundary layer from laminar to turbulent flow immediately downstream, eliminating the low-drag laminar run that otherwise extends to 30-40% chord for smooth airfoils at subcritical Reynolds numbers. Repeat your angle-of-attack sweep with the contaminated configuration, observing a dramatic reduction in maximum lift coefficient by 15-25% and a forward shift in stall angle by 2-4 degrees. The drag coefficient at all lift conditions increases substantially, reflecting the thicker turbulent boundary layer and earlier separation onset.

Quantify the roughness penalty by computing the differential coefficients $\Delta C_{L,\text{max}} = C_{L,\text{max}}^{\text{rough}} - C_{L,\text{max}}^{\text{smooth}}$ and the percentage degradation $\Delta C_{L,\text{max}} / C_{L,\text{max}}^{\text{smooth}} \times 100\%$. This contamination sensitivity underscores the critical importance of wing leading-edge de-icing systems and airframe cleanliness inspections in certified aircraft. The Federal Aviation Administration mandates that aircraft demonstrate acceptable handling qualities with wing contamination representative of realistic in-service conditions, validated through flight test with artificial ice shapes affixed to wing leading edges.

Conduct a comprehensive uncertainty analysis by propagating measurement errors through your entire data reduction pipeline using Monte Carlo simulation. The primary uncertainty sources include force balance voltage noise ($\sigma_V \approx 0.001 \, \text{V}$), calibration coefficient uncertainty from the least-squares fit ($\sigma_{\text{slope}} \approx 0.5\%$ of nominal), freestream velocity measurement error ($\sigma_U \approx 0.2 \, \text{m/s}$ from pitot probe resolution), air density uncertainty arising from temperature and pressure sensor tolerances ($\sigma_\rho / \rho \approx 0.3\%$), and geometric measurement uncertainty in chord length and span ($\sigma_c / c \approx 0.1\%$). The following script implements a Monte Carlo propagation by perturbing each input parameter according to its uncertainty distribution across 10,000 synthetic trials, computing the resulting coefficient distributions, and extracting 95% confidence intervals.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Nominal values and measurement uncertainties
U_INF_NOM = 20.0  # m/s
SIGMA_U = 0.2  # m/s
RHO_NOM = 1.225  # kg/m^3
SIGMA_RHO_FRAC = 0.003  # fractional uncertainty
CHORD_NOM = 0.15  # m
SIGMA_CHORD_FRAC = 0.001
SPAN_NOM = 0.40  # m
SIGMA_SPAN_FRAC = 0.001

SLOPE_L_NOM = 2.453  # N/V
SIGMA_SLOPE_L_FRAC = 0.005
INTERCEPT_L_NOM = -0.012  # N
SIGMA_INTERCEPT_L = 0.003  # N

# Example measurement at alpha = 10 degrees
V_LIFT_NOM = 0.633  # V
SIGMA_V_LIFT = 0.001  # V

N_SAMPLES = 10000

# Generate perturbed parameter samples
np.random.seed(42)
U_inf_samples = np.random.normal(U_INF_NOM, SIGMA_U, N_SAMPLES)
rho_samples = np.random.normal(RHO_NOM, SIGMA_RHO_FRAC * RHO_NOM, N_SAMPLES)
chord_samples = np.random.normal(CHORD_NOM, SIGMA_CHORD_FRAC * CHORD_NOM, N_SAMPLES)
span_samples = np.random.normal(SPAN_NOM, SIGMA_SPAN_FRAC * SPAN_NOM, N_SAMPLES)
slope_L_samples = np.random.normal(SLOPE_L_NOM, SIGMA_SLOPE_L_FRAC * SLOPE_L_NOM, N_SAMPLES)
intercept_L_samples = np.random.normal(INTERCEPT_L_NOM, SIGMA_INTERCEPT_L, N_SAMPLES)
V_lift_samples = np.random.normal(V_LIFT_NOM, SIGMA_V_LIFT, N_SAMPLES)

# Compute derived quantities for each sample
S_samples = chord_samples * span_samples
q_inf_samples = 0.5 * rho_samples * U_inf_samples**2
F_lift_samples = slope_L_samples * V_lift_samples + intercept_L_samples
C_L_samples = F_lift_samples / (q_inf_samples * S_samples)

# Statistical summary
C_L_mean = np.mean(C_L_samples)
C_L_std = np.std(C_L_samples)
C_L_median = np.median(C_L_samples)
C_L_ci = np.percentile(C_L_samples, [2.5, 97.5])

print("Monte Carlo Uncertainty Propagation Results")
print("=" * 50)
print(f"Number of samples: {N_SAMPLES}")
print(f"\nNominal C_L: {C_L_mean:.4f}")
print(f"Standard deviation: {C_L_std:.4f}")
print(f"Coefficient of variation: {100 * C_L_std / C_L_mean:.2f}%")
print(f"95% confidence interval: [{C_L_ci[0]:.4f}, {C_L_ci[1]:.4f}]")
print(f"Median: {C_L_median:.4f}")

# Sensitivity analysis: correlation coefficients
input_matrix = np.column_stack([
    U_inf_samples, rho_samples, chord_samples, span_samples,
    slope_L_samples, intercept_L_samples, V_lift_samples
])
input_labels = ['U_inf', 'rho', 'chord', 'span', 'slope_L', 'intercept_L', 'V_lift']

print("\nSensitivity Analysis (Pearson correlation with C_L):")
for label, input_samples in zip(input_labels, input_matrix.T):
    corr, _ = stats.pearsonr(input_samples, C_L_samples)
    print(f"  {label:15s}: {corr:+.4f}")

# Visualization: histogram and normal Q-Q plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Histogram with fitted normal distribution
axes[0].hist(C_L_samples, bins=50, density=True, alpha=0.7, color='#2E86AB', edgecolor='black', linewidth=0.5)
x_fit = np.linspace(C_L_samples.min(), C_L_samples.max(), 200)
pdf_fit = stats.norm.pdf(x_fit, C_L_mean, C_L_std)
axes[0].plot(x_fit, pdf_fit, 'r-', linewidth=2, label=f'Normal fit\n$\\mu={C_L_mean:.4f}$\n$\\sigma={C_L_std:.4f}$')
axes[0].axvline(C_L_mean, color='black', linestyle='--', linewidth=1.5, label='Mean')
axes[0].axvline(C_L_ci[0], color='red', linestyle=':', linewidth=1.5, label='95% CI')
axes[0].axvline(C_L_ci[1], color='red', linestyle=':', linewidth=1.5)
axes[0].set_xlabel('Lift Coefficient $C_L$', fontsize=11)
axes[0].set_ylabel('Probability Density', fontsize=11)
axes[0].set_title('Monte Carlo Distribution of $C_L$', fontsize=12, fontweight='bold')
axes[0].legend(fontsize=9)
axes[0].grid(True, alpha=0.3)

# Q-Q plot to assess normality
stats.probplot(C_L_samples, dist="norm", plot=axes[1])
axes[1].set_title('Normal Q-Q Plot', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/uncertainty_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nFigure saved: figures/uncertainty_analysis.png")

# Expanded uncertainty budget breakdown
print("\nExpanded Uncertainty Budget (95% coverage, k=2):")
print(f"  Total expanded uncertainty: ±{2 * C_L_std:.4f} ({100 * 2 * C_L_std / C_L_mean:.2f}%)")
```

Execute this Monte Carlo analysis to reveal that your lift coefficient measurement uncertainty typically amounts to ±2-3% at 95% confidence, dominated by the combined contributions from force balance voltage noise and dynamic pressure uncertainty. The sensitivity analysis reports Pearson correlation coefficients between each input parameter and the output $C_L$, revealing that freestream velocity exerts the strongest influence (correlation magnitude near 0.9) due to its squared appearance in the dynamic pressure term. Force balance voltage and calibration slope contribute secondary effects, while geometric measurement uncertainties remain negligible due to their tight manufacturing tolerances.

The Q-Q plot assesses whether the output $C_L$ distribution follows a Gaussian form, which proves valid when propagating normally distributed inputs through mildly nonlinear transformations like your coefficient definitions. Deviation from the diagonal reference line at the distribution tails would indicate non-Gaussian behavior requiring alternative uncertainty quantification methods such as bootstrap resampling or Bayesian inference.

Extend your boundary stress testing by investigating compressibility effects as Mach number increases beyond $M = 0.3$. If your wind tunnel capabilities permit freestream velocities approaching 100 m/s (Mach 0.3 at standard conditions), you will observe a systematic increase in lift curve slope and a forward movement of the center of pressure as the flow accelerates to local supersonic velocities over the airfoil upper surface. The Prandtl-Glauert compressibility correction predicts $C_{L,\alpha}^{\text{compressible}} = C_{L,\alpha}^{\text{incompressible}} / \sqrt{1 - M^2}$, which you can validate by plotting the ratio of measured lift slopes at different Mach numbers against the theoretical correction factor.

Conclude this exercise by constructing a comprehensive error budget table summarizing all uncertainty sources, their individual contributions to the total uncertainty, and recommended measurement improvements. Prioritize upgrades to the highest-impact components: a higher-resolution force balance to reduce voltage noise, a digital micromanometer for improved dynamic pressure measurement, and temperature-controlled wind tunnel operation to eliminate density drift. Document your complete uncertainty analysis in a technical memorandum formatted per AIAA standards, suitable for submission to a peer-reviewed conference or journal specializing in experimental fluid mechanics.

## Laboratory Cheat Sheet & Metric Verification Guide

This reference section consolidates the essential formulas, dimensional analysis relationships, and quick diagnostic checks required for efficient laboratory operation and troubleshooting. Consult this guide during active experimentation to verify unit consistency, estimate expected magnitudes, and identify anomalous measurements indicative of sensor malfunction or flow disturbances.

**Fundamental Aerodynamic Coefficients:** The lift coefficient $C_L = L / (q_\infty S)$, drag coefficient $C_D = D / (q_\infty S)$, and pitching moment coefficient $C_M = M / (q_\infty S c)$ normalize forces and moments by the product of dynamic pressure $q_\infty = \frac{1}{2} \rho U_\infty^2$ and reference area $S$. The moment coefficient additionally scales by chord $c$ to render it dimensionless. Expected ranges for conventional airfoils include $0 < C_L < 1.5$, $0.01 < C_D < 0.5$, and $|C_M| < 0.3$ about the quarter-chord point.

**Reynolds Number and Mach Number:** The Reynolds number quantifies viscous flow regime via $\text{Re} = \rho U_\infty c / \mu = U_\infty c / \nu$ where $\mu$ represents dynamic viscosity and $\nu = \mu / \rho$ denotes kinematic viscosity. At standard sea-level conditions ($T = 15°\text{C}$, $p = 101325 \, \text{Pa}$), use $\rho = 1.225 \, \text{kg/m}^3$ and $\nu = 1.48 \times 10^{-5} \, \text{m}^2/\text{s}$. The Mach number $M = U_\infty / a$ compares flow velocity to the speed of sound $a = \sqrt{\gamma R T}$, where $\gamma = 1.4$ for air and $R = 287.05 \, \text{J/(kg·K)}$ yields $a = 340.3 \, \text{m/s}$ at standard conditions. Compressibility effects become significant for $M > 0.3$.

**Lift Curve Slope and Stall Prediction:** Thin airfoil theory predicts a two-dimensional lift slope $C_{L,\alpha} = 2\pi \approx 0.11$ per degree for inviscid flow. Viscous boundary layers reduce this to approximately $0.10$ per degree at moderate Reynolds numbers. The zero-lift angle $\alpha_{L=0}$ vanishes for symmetric sections but reaches $-2°$ to $-4°$ for cambered airfoils. Stall onset occurs when the adverse pressure gradient over the upper surface exceeds the boundary layer's ability to remain attached, typically at $\alpha_{\text{stall}} = 12°$ to $16°$ for smooth airfoils at $\text{Re} > 10^5$.

**Drag Decomposition and Polar Fitting:** Total drag partitions into profile drag (skin friction plus pressure drag) and induced drag (circulation-generated downwash): $C_D = C_{D,0} + k C_L^2$ where $C_{D,0}$ represents the zero-lift drag and $k = 1 / (\pi e AR)$ depends on aspect ratio $AR$ and Oswald efficiency factor $e$. For a finite wing, $AR = b^2 / S$ where $b$ denotes wingspan. Fit this parabolic relationship to your drag polar data via least-squares regression to extract $C_{D,0}$ and $k$.

**Maximum Lift-to-Drag Ratio:** Aerodynamic efficiency peaks at the angle of attack where $\text{d}(C_L / C_D) / \text{d}\alpha = 0$, which occurs when $C_L = \sqrt{C_{D,0} / k}$. At this condition, the induced drag equals the profile drag, and the minimum required power for steady flight reaches its nadir. For typical low-speed airfoils, maximum $L/D$ ranges from 30 for sailplanes to 15 for general aviation aircraft and 8 for fighter jets with swept wings.

**Uncertainty Propagation Formulas:** For uncorrelated input uncertainties, the output variance follows $\sigma_y^2 = \sum_i (\partial y / \partial x_i)^2 \sigma_{x_i}^2$. For the lift coefficient $C_L = F_L / (q_\infty S)$, compute $\sigma_{C_L} / C_L = \sqrt{(\sigma_{F_L} / F_L)^2 + (\sigma_q / q_\infty)^2 + (\sigma_S / S)^2}$ assuming relative uncertainties combine in quadrature. Report expanded uncertainties at 95% confidence by multiplying standard uncertainties by coverage factor $k = 2$.

**Pitot-Static Pressure Measurement:** A pitot tube aligned with the freestream measures stagnation pressure $p_0 = p_\infty + q_\infty$, while static ports sample the undisturbed static pressure $p_\infty$. The differential pressure $\Delta p = p_0 - p_\infty = q_\infty$ directly yields dynamic pressure, from which velocity follows via $U_\infty = \sqrt{2 q_\infty / \rho}$. Calibrate pressure transducers against a water manometer using $\Delta p = \rho_{\text{H}_2\text{O}} g h$ where $h$ represents the height difference in meters.

**Temperature Correction for Air Properties:** Dynamic viscosity varies with temperature according to Sutherland's law: $\mu(T) = \mu_0 (T / T_0)^{3/2} (T_0 + S) / (T + S)$ with $\mu_0 = 1.716 \times 10^{-5} \, \text{Pa·s}$ at $T_0 = 273.15 \, \text{K}$ and $S = 110.4 \, \text{K}$. Air density follows the ideal gas law $\rho = p / (R T)$ where $p$ represents absolute pressure in Pascals and $T$ is absolute temperature in Kelvin. A 10°C temperature increase reduces density by approximately 3.4%.

**Force Balance Calibration Protocol:** Suspend known masses from the balance sensing axis, recording voltage outputs across the anticipated force range. Perform at least five calibration points spanning 0% to 100% of full scale. Fit a linear model $F = m V + b$ via least-squares regression, extracting slope $m$ (sensitivity in N/V) and intercept $b$ (zero-load offset). Compute the coefficient of determination $R^2 > 0.999$ to verify linearity. Repeat calibration monthly or after any mechanical disturbance to the balance.

**Wind Tunnel Blockage Corrections:** A finite-span model occupies a fraction of the tunnel cross-sectional area, artificially accelerating the flow and inflating measured forces. Apply the blockage correction $C_L^{\text{corrected}} = C_L^{\text{measured}} / (1 + \tau)$ where the blockage factor $\tau = (S_{\text{model}} / S_{\text{tunnel}}) \times k_{\text{blockage}}$ depends on tunnel geometry. For solid blockage in a closed test section, $k_{\text{blockage}} \approx 1.0$; for wake blockage, $k_{\text{blockage}} \approx 0.25$. Keep model frontal area below 7.5% of tunnel area to limit corrections below 5%.

**Quick Diagnostic Checks:** Before each test session, verify zero-load force balance outputs remain within ±0.01 N with the tunnel off. Confirm pitot probe dynamic pressure increases quadratically with tunnel speed setpoint. Inspect flow visualization smoke patterns for symmetry about the model centerline; asymmetry indicates tunnel flow angularity requiring realignment. Monitor ambient temperature drift below 0.5°C/hour to maintain Reynolds number stability within 1%. Check that maximum lift coefficient falls within 1.2 to 1.6 for smooth NACA sections; values outside this range suggest flow tripping or premature turbulent transition.

**Data Acquisition Sample Rate Selection:** Capture unsteady aerodynamic phenomena by sampling at frequencies exceeding twice the highest relevant flow frequency (Nyquist criterion). For boundary layer instabilities and vortex shedding, use $f_{\text{sample}} \geq 1 \, \text{kHz}$. Anti-alias analog signals with hardware low-pass filters set to $0.4 f_{\text{sample}}$ before digitization. Time-average steady-state measurements over at least 1000 samples to reduce random noise by a factor of $\sqrt{N} \approx 32$.

**Standard Atmospheric Model Reference Values:** At sea level ($h = 0 \, \text{m}$): temperature $T = 288.15 \, \text{K}$ ($15°\text{C}$), pressure $p = 101325 \, \text{Pa}$ ($1013.25 \, \text{hPa}$), density $\rho = 1.225 \, \text{kg/m}^3$, speed of sound $a = 340.3 \, \text{m/s}$, kinematic viscosity $\nu = 1.461 \times 10^{-5} \, \text{m}^2/\text{s}$. At altitude, apply lapse rate $\text{d}T/\text{d}h = -6.5 \, \text{K/km}$ and hydrostatic relation $\text{d}p/\text{d}h = -\rho g$ to compute local atmospheric properties.

**Flight Performance Calculations:** The power required for level flight equals $P = D V = \frac{1}{2} \rho V^3 S C_D$, exhibiting a cubic velocity dependence. Minimum power occurs at maximum $C_L^{3/2} / C_D$, while maximum range corresponds to maximum $L/D$. The rate of climb follows $R/C = (P_{\text{available}} - P_{\text{required}}) / W$ where $W$ represents aircraft weight. Glide ratio equals $L/D$, yielding glide distance $d = h \times (L/D)$ from altitude $h$.

**Common Error Modes and Troubleshooting:** If measured $C_L$ at zero angle of attack exceeds ±0.05, check for model rigging misalignment or tunnel flow angularity. If drag increases unexpectedly, inspect for surface contamination, force balance mounting interference, or tunnel boundary layer ingestion. If lift curve slope falls below 0.08 per degree, verify Reynolds number exceeds $10^5$ and check for premature boundary layer tripping. If pressure transducers drift, verify temperature stability and re-zero with tunnel off. If force balance noise exceeds 1% of full scale, investigate mechanical vibration sources or electrical interference from tunnel motor controllers.
