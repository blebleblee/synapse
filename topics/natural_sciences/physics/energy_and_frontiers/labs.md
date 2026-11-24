# Operational Verification Labs: Energy and Frontiers

## Objective & Laboratory Bench Setup

This guide is a practitioner-first experimental program for physicists working at the intersection of classical thermodynamics, quantum-scale energy phenomena, and spectroscopic measurement. The three exercises that follow are not demonstrations — they are replicable, metrologically rigorous protocols designed to produce publishable-quality data from a standard laboratory bench. You will measure Planck's constant from LED threshold voltages, characterize a calorimetric energy transfer curve across a phase boundary, and stress-test your measurement model against systematic and random error sources using full uncertainty propagation. By the end, you will have three independently verified datasets, three calibrated response curves, and a worked uncertainty budget for each observable.

The theoretical scaffolding is intentional but disciplined. Planck's quantization relation $E = h\nu$ sets the ceiling for how precisely you must measure a forward-bias voltage. The first law of thermodynamics $\Delta U = Q - W$ frames every calorimetric joule you account for. The time-dependent Schrödinger equation motivates why a tunneling current appears below what semiclassical electrostatics would predict. These equations earn their place here because they tell you what to look for in the data, where the deviations live, and what systematic errors they expose. No derivation runs longer than the measurement it motivates.

### Environment Verification

Before mounting any instrument, confirm the Python scientific stack is fully operational. Run each of the following from your terminal, one line at a time, and inspect the version strings against the minimum requirements in the cheat sheet at the end of this guide.

```bash
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "import scipy; print('SciPy', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib', matplotlib.__version__)"
python -c "import astropy; print('Astropy', astropy.__version__)"
```

Minimum acceptable versions: NumPy ≥ 1.24, SciPy ≥ 1.10, Matplotlib ≥ 3.7, Astropy ≥ 5.3. If any import fails, install via `pip install numpy scipy matplotlib astropy` inside your activated virtual environment. The Avogadro molecular editor and PyMOL are referenced in the cheat sheet for molecular energy visualization; they are optional for Exercises 1–3 but required for the extended frontier problem at the end.

### Physical Bench Configuration

The bench serves all three exercises without full teardown between them. At the left station, mount the LED array (minimum four emitters: UV ~400 nm, blue ~470 nm, green ~525 nm, red ~635 nm), a precision variable DC supply (0–5 V, 1 mV resolution), a digital multimeter in voltage mode across each LED, and a series resistor of 1 kΩ ± 1% to limit current below 5 mA throughout all threshold measurements. Keep the ambient light below 10 lux by using a cardboard shroud over the LED station; stray photons read by the photodiode reference detector will introduce a constant offset error of roughly 2–8 mV, which propagates directly into your Planck estimate.

At the center station, install the calorimeter: a Styrofoam-jacketed aluminum cup (mass precisely weighed to ±0.01 g), a calibrated digital thermometer with 0.1 °C resolution, a stirring rod, and a 50 W immersion heater powered through a Variac with a watt-meter in line. The watt-meter must display true RMS power, not apparent power, because the Variac output is not a clean sinusoid at reduced settings and apparent power overestimates energy delivery by up to 12% at 50% dial position.

At the right station, place the oscilloscope (100 MHz bandwidth minimum, 1 GS/s sampling rate) with a 10:1 passive probe, the function generator for driving RC and RL test circuits, and the breadboard carrying the passive components for Exercise 3. Confirm probe compensation on each channel before any acquisition: attach the probe tip to the probe compensation terminal, observe the 1 kHz square wave, and trim the probe's trimmer capacitor until the corners are sharp and the top is flat. A rounded corner indicates under-compensation and will soften every rise-time measurement you make.

---

## Exercise 1: Empirical Observation & Measurement Protocol

### Measuring Planck's Constant from LED Threshold Voltages

The operating principle here is deceptively clean. When a forward-biased LED reaches its turn-on threshold voltage $V_0$, the energy delivered to each charge carrier equals the photon energy of the emitted light:

$$eV_0 = h\nu = \frac{hc}{\lambda}$$

where $e = 1.602 \times 10^{-19}\ \text{C}$, $h$ is Planck's constant, $c = 2.998 \times 10^8\ \text{m/s}$, and $\lambda$ is the peak emission wavelength. Rearranging:

$$h = \frac{eV_0 \lambda}{c}$$

Your task is to determine $V_0$ for each LED with enough precision to yield a $h$ estimate within 5% of the CODATA value ($6.626 \times 10^{-34}\ \text{J·s}$). The measurement is not trivial: the I-V curve of a real LED is an exponential, not a step, and $V_0$ must be operationally defined as the voltage at which a reproducible onset current flows. The standard protocol uses the tangent-line intersection method on the I-V curve, not a fixed-current threshold, because the fixed-current method is sensitive to the absolute forward current and shifts systematically with temperature.

### Step-by-Step Measurement Protocol

Set the series resistor to 1 kΩ and confirm its value with the multimeter in resistance mode before connecting any LED. Connect the first LED (UV, nominal 400 nm) in series with the resistor. Set the supply to 0.00 V. Increase the supply voltage in 50 mV steps from 0 V to 1.0 V, then in 10 mV steps from 1.0 V to 3.5 V, recording both the voltage across the LED ($V_{LED}$) and the current through it ($I = V_{supply} - V_{LED}) / 1000\ \Omega$) at each step. Wait three seconds at each voltage step before recording; the junction temperature equilibrates on a timescale of 1–2 seconds, and reading too quickly will give a falsely high turn-on voltage because a cold junction requires more voltage to forward-bias.

Repeat this sweep three times for each LED without touching the mechanical connections between sweeps. The three sweeps will reveal reproducibility: if the three I-V curves overlay within your multimeter's 1 mV resolution, your contact resistance is stable. If they drift, check the probe clips for oxidation and clean with isopropyl alcohol.

For peak wavelength: do not rely on the LED manufacturer's nominal datasheet value. Use the spectrophotometer in transmission mode. Hold the lit LED (at 2 mA forward current) against the input aperture with the shroud on and collect a 400–700 nm scan at 1 nm resolution. Identify the peak wavelength $\lambda_{peak}$ and record the FWHM of the emission band. The uncertainty in $\lambda_{peak}$ from a decent grating spectrometer is ±1–2 nm; this will be your dominant wavelength error source in the final $h$ estimate.

### Data Reduction: Python Analysis Script

The following script ingests your recorded I-V data, applies the tangent-line intersection method, and computes $h$ with propagated uncertainty for each LED. Enter your measured data directly into the arrays at the top of the script. All four LEDs are processed in a single pass.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress

# ── Physical constants ──────────────────────────────────────────────────────
e_charge = 1.60217663e-19   # C
c_light   = 2.99792458e8    # m/s
h_codata  = 6.62607015e-34  # J·s  (reference)

# ── Measured data: replace with your bench recordings ───────────────────────
# Format: voltage across LED in volts, current in amperes
# Each LED is a dict with keys 'label', 'lambda_m' (peak wavelength, metres),
# 'lambda_unc' (1-sigma uncertainty on wavelength, metres), 'V', 'I'

leds = [
    {
        'label': 'UV 400 nm',
        'lambda_m':   400e-9,
        'lambda_unc':   2e-9,
        'V': np.array([0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40,
                       0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85,
                       0.90, 0.95, 1.00, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06,
                       1.07, 1.08, 1.09, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60,
                       1.70, 1.80, 1.90, 2.00, 2.10, 2.20, 2.30, 2.40, 2.50,
                       2.60, 2.70, 2.80, 2.90, 3.00, 3.10, 3.20, 3.30]),
        'I': np.array([0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6,
                       0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6,
                       0.000e-6, 0.001e-6, 0.001e-6, 0.002e-6, 0.003e-6,
                       0.005e-6, 0.008e-6, 0.013e-6, 0.021e-6, 0.034e-6,
                       0.055e-6, 0.057e-6, 0.059e-6, 0.062e-6, 0.065e-6,
                       0.068e-6, 0.072e-6, 0.078e-6, 0.086e-6, 0.098e-6,
                       0.115e-6, 1.20e-6,  5.80e-6,  18.5e-6,  48.2e-6,
                       102e-6,   195e-6,   340e-6,   560e-6,   870e-6,
                       1.28e-3,  1.80e-3,  2.42e-3,  3.14e-3,  3.95e-3,
                       4.82e-3,  5.75e-3,  6.73e-3,  7.74e-3,  8.78e-3,
                       9.84e-3,  10.9e-3,  11.9e-3]),
    },
    {
        'label': 'Blue 470 nm',
        'lambda_m':   470e-9,
        'lambda_unc':   2e-9,
        'V': np.array([0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80,
                       0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.70,
                       1.80, 1.90, 2.00, 2.10, 2.20, 2.30, 2.40, 2.50, 2.60,
                       2.70, 2.80, 2.90, 3.00, 3.10, 3.20]),
        'I': np.array([0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6,
                       0.000e-6, 0.000e-6, 0.001e-6, 0.004e-6, 0.014e-6,
                       0.048e-6, 0.16e-6,  0.52e-6,  1.65e-6,  5.1e-6,
                       15.3e-6,  43.8e-6,  115e-6,   280e-6,   620e-6,
                       1.25e-3,  2.30e-3,  3.80e-3,  5.60e-3,  7.60e-3,
                       9.80e-3,  12.0e-3,  14.2e-3,  16.4e-3,  18.5e-3,
                       20.5e-3,  22.4e-3,  24.2e-3]),
    },
    {
        'label': 'Green 525 nm',
        'lambda_m':   525e-9,
        'lambda_unc':   2e-9,
        'V': np.array([0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80,
                       0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.70,
                       1.80, 1.90, 2.00, 2.10, 2.20, 2.30, 2.40, 2.50, 2.60,
                       2.70, 2.80, 2.90, 3.00]),
        'I': np.array([0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6,
                       0.000e-6, 0.001e-6, 0.004e-6, 0.016e-6, 0.064e-6,
                       0.25e-6,  0.96e-6,  3.60e-6,  13.0e-6,  44.0e-6,
                       138e-6,   390e-6,   990e-6,   2.25e-3,  4.60e-3,
                       8.50e-3,  13.8e-3,  19.5e-3,  25.5e-3,  31.5e-3,
                       37.4e-3,  43.0e-3,  48.3e-3,  53.4e-3,  58.2e-3,
                       62.8e-3]),
    },
    {
        'label': 'Red 635 nm',
        'lambda_m':   635e-9,
        'lambda_unc':   2e-9,
        'V': np.array([0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80,
                       0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50, 1.60, 1.70,
                       1.80, 1.90, 2.00, 2.10, 2.20, 2.30, 2.40, 2.50]),
        'I': np.array([0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6, 0.000e-6,
                       0.001e-6, 0.005e-6, 0.025e-6, 0.12e-6,  0.56e-6,
                       2.60e-6,  11.5e-6,  48.0e-6,  180e-6,   590e-6,
                       1.70e-3,  4.30e-3,  9.50e-3,  18.5e-3,  31.5e-3,
                       47.5e-3,  65.5e-3,  84.5e-3,  104e-3,   123e-3,
                       142e-3]),
    },
]

# ── Tangent-line intersection method ────────────────────────────────────────
def find_threshold_tangent(V, I, label):
    """
    Fit a Shockley diode model to the exponential region, extract the
    steepest-slope tangent line, and return its x-intercept (V_threshold).
    Also returns 1-sigma uncertainty from the covariance of the linear fit.
    """
    # Work in log space to identify the clean exponential region
    mask_exp = I > 1e-9   # exclude noise floor
    V_exp = V[mask_exp]
    I_exp = I[mask_exp]

    if len(V_exp) < 5:
        raise ValueError(f"Insufficient exponential-region points for {label}")

    log_I = np.log(I_exp)

    # Linear fit in log(I) vs V to get the ideality-factor slope
    slope_log, intercept_log, r_log, _, stderr_log = linregress(V_exp, log_I)

    # Find the index of steepest dI/dV in the LINEAR I-V region
    # (the linear region is where the ohmic series resistance dominates)
    dI_dV = np.gradient(I, V)
    # Use the top 15% of dI/dV values to define the tangent region
    threshold_slope = np.percentile(dI_dV, 85)
    lin_mask = dI_dV >= threshold_slope
    V_lin = V[lin_mask]
    I_lin = I[lin_mask]

    if len(V_lin) < 3:
        # Fall back: use last 5 points
        V_lin = V[-5:]
        I_lin = I[-5:]

    slope_lin, intercept_lin, r_lin, _, stderr_lin = linregress(V_lin, I_lin)

    # x-intercept of the tangent line: V0 = -intercept / slope
    V0 = -intercept_lin / slope_lin

    # Uncertainty via error propagation: delta_V0 = V0 * sqrt((dB/B)^2 + (dm/m)^2)
    # where B = intercept, m = slope, using linregress stderr
    rel_unc_slope     = stderr_lin / abs(slope_lin)
    rel_unc_intercept = stderr_lin / abs(intercept_lin)  # approximate
    V0_unc = abs(V0) * np.sqrt(rel_unc_slope**2 + rel_unc_intercept**2)

    return V0, V0_unc, slope_lin, intercept_lin, V_lin, I_lin

# ── Main computation loop ────────────────────────────────────────────────────
h_values     = []
h_unc_values = []

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
fig.suptitle("LED I–V Curves: Planck's Constant Determination", fontsize=14, fontweight='bold')
axes_flat = axes.flatten()

for idx, led in enumerate(leds):
    V        = led['V']
    I        = led['I']
    lam      = led['lambda_m']
    lam_unc  = led['lambda_unc']
    label    = led['label']
    ax       = axes_flat[idx]

    V0, V0_unc, slope_lin, intercept_lin, V_lin, I_lin = find_threshold_tangent(V, I, label)

    # Planck's constant from this LED
    h_meas     = e_charge * V0 * lam / c_light
    # Propagate: (delta_h / h)^2 = (delta_V0/V0)^2 + (delta_lam/lam)^2
    h_unc      = h_meas * np.sqrt((V0_unc / V0)**2 + (lam_unc / lam)**2)

    h_values.append(h_meas)
    h_unc_values.append(h_unc)

    percent_error = 100.0 * abs(h_meas - h_codata) / h_codata

    print(f"\n{'─'*55}")
    print(f"LED        : {label}")
    print(f"λ_peak     : {lam*1e9:.1f} nm  (±{lam_unc*1e9:.1f} nm)")
    print(f"V_threshold: {V0*1e3:.1f} mV  (±{V0_unc*1e3:.1f} mV)")
    print(f"h_measured : {h_meas:.4e} J·s  (±{h_unc:.2e} J·s)")
    print(f"h_CODATA   : {h_codata:.4e} J·s")
    print(f"% error    : {percent_error:.2f}%")

    # Plot I-V curve
    ax.semilogy(V, I * 1e3 + 1e-12, 'o', markersize=3, color='steelblue',
                alpha=0.6, label='Measured I-V')

    # Plot tangent line extrapolation
    V_extrap = np.linspace(V0 - 0.3, max(V_lin) + 0.1, 200)
    I_extrap = slope_lin * V_extrap + intercept_lin
    ax.semilogy(V_extrap, I_extrap * 1e3 + 1e-12, 'r--', linewidth=1.5,
                label=f'Tangent line')
    ax.axvline(V0, color='darkorange', linewidth=1.2, linestyle=':',
               label=f'$V_0$ = {V0:.3f} V')

    ax.set_xlabel('$V_{LED}$ (V)', fontsize=10)
    ax.set_ylabel('Current (mA, log scale)', fontsize=10)
    ax.set_title(f'{label}  →  $h$ = {h_meas:.3e} J·s  ({percent_error:.1f}% err)',
                 fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, which='both', alpha=0.3)
    ax.set_ylim(1e-6, 1e3)

plt.tight_layout()
plt.savefig('planck_led_iv_curves.pdf', dpi=300, bbox_inches='tight')
plt.show()

# ── Weighted mean of all four h estimates ────────────────────────────────────
h_arr   = np.array(h_values)
unc_arr = np.array(h_unc_values)
weights = 1.0 / unc_arr**2
h_mean  = np.sum(weights * h_arr) / np.sum(weights)
h_mean_unc = 1.0 / np.sqrt(np.sum(weights))

print(f"\n{'═'*55}")
print(f"Weighted mean h : {h_mean:.4e} J·s  (±{h_mean_unc:.2e} J·s)")
print(f"CODATA h        : {h_codata:.4e} J·s")
print(f"Combined % error: {100*abs(h_mean - h_codata)/h_codata:.2f}%")
print(f"{'═'*55}")
```

The print output from this script gives you the threshold voltage, computed $h$, propagated uncertainty, and percentage deviation from CODATA for each LED individually, then a weighted mean across all four. A well-executed bench run typically returns a combined error of 2–6%. If your result exceeds 8%, the most common culprits are: stray ambient light raising the apparent turn-on current (raising $V_0$ artificially), junction self-heating from too-rapid voltage stepping (lowering $V_0$), or a spectrophotometer wavelength calibration error (shifting all $h$ values by a constant fraction). Check these in that order.

---

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Calorimetric Energy Transfer: Mapping a Phase Transition

A phase transition is one of the most instructive phenomena in experimental thermodynamics because it makes energy storage completely invisible in the temperature record. During a solid-to-liquid transition at constant pressure, every joule you deliver to the system goes into breaking crystal lattice bonds rather than raising the temperature — the heat capacity appears to diverge at the melting point. The operative relation is the enthalpy balance:

$$Q = mc\Delta T + mL_f$$

where $Q$ is total heat delivered (joules), $m$ is sample mass (kg), $c$ is specific heat capacity (J kg⁻¹ K⁻¹), $\Delta T$ is the temperature change in the single-phase region, and $L_f$ is the latent heat of fusion (J/kg). Your experimental goal is to measure the entire $T(t)$ curve from room temperature through melting and several degrees above, infer $L_f$ for the sample, and compare it to the literature value. You will use ice in water as the sample because its thermodynamic properties are precisely known: $c_{ice} = 2090\ \text{J kg}^{-1}\text{K}^{-1}$, $c_{water} = 4186\ \text{J kg}^{-1}\text{K}^{-1}$, $L_f = 334{,}000\ \text{J kg}^{-1}$.

### Setup and Calibration Protocol

Weigh the aluminum calorimeter cup empty to ±0.01 g. Add 150.00 g of crushed ice (weighed on the analytical balance). Insert the thermometer probe centrally, not touching the cup wall, and begin stirring at a constant rate — thermal gradients across a stagnant ice-water bath can reach 2–3 °C and completely distort the plateau identification. Set the immersion heater power to exactly 25.0 W as confirmed by the in-line watt-meter. Begin temperature logging at 10-second intervals. If you have a USB-connected temperature data logger, use it; if you are recording manually, a 10-second interval requires a dedicated timekeeper.

Before the main run, perform a heater calibration: fill the cup with 150.00 g of water at room temperature, run the heater for exactly 300 seconds, and compare the measured $\Delta T$ against the predicted $\Delta T = P \cdot t / (m \cdot c_{water})$. At 25 W for 300 s you deliver 7500 J, which should raise 150 g of water by $\Delta T = 7500 / (0.150 \times 4186) = 11.93\ °\text{C}$. If your measured $\Delta T$ is 10.5 °C, your effective power is $0.150 \times 4186 \times 10.5 / 300 = 22.0\ \text{W}$ and the difference (3 W) is heat loss through the Styrofoam walls. Measure this heat loss rate and use it as a correction factor $\dot{Q}_{loss}$ in all subsequent runs.

### Data Reduction and Response Curve Script

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal  import savgol_filter
from scipy.optimize import curve_fit

# ── Physical constants and known material properties ────────────────────────
c_ice         = 2090.0    # J/(kg·K)
c_water       = 4186.0    # J/(kg·K)
L_f_literature = 334000.0 # J/kg  (literature value for ice)
rho_aluminum  = 2700.0    # kg/m³  (not directly used, included for reference)
c_aluminum    = 897.0     # J/(kg·K)

# ── Experimental parameters ─────────────────────────────────────────────────
P_heater      = 25.0      # W  (from watt-meter, corrected by calibration)
Q_loss_rate   = 2.8       # W  (heat loss rate measured in calibration run)
P_net         = P_heater - Q_loss_rate   # 22.2 W net into sample

m_ice         = 0.15000   # kg  (measured on analytical balance)
m_cup_al      = 0.03512   # kg  (mass of aluminum cup)
dt            = 10.0      # s   (logging interval)

# ── Temperature-time data ────────────────────────────────────────────────────
# Replace this array with your data logger export.
# Format: temperature in degrees Celsius at each 10-second interval,
# starting from t=0 when the heater was switched on.
T_raw = np.array([
    -15.2, -14.9, -14.5, -14.1, -13.7, -13.3, -13.0, -12.6, -12.2, -11.8,
    -11.4, -11.1, -10.7, -10.3,  -9.9,  -9.5,  -9.2,  -8.8,  -8.4,  -8.0,
     -7.6,  -7.3,  -6.9,  -6.5,  -6.1,  -5.8,  -5.4,  -5.0,  -4.6,  -4.3,
     -3.9,  -3.5,  -3.2,  -2.8,  -2.4,  -2.1,  -1.7,  -1.3,  -1.0,  -0.6,
     -0.2,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
      0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
      0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
      0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
      0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
      0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,   0.0,
      0.1,   0.3,   0.6,   1.0,   1.4,   1.8,   2.2,   2.6,   3.0,   3.4,
      3.8,   4.2,   4.6,   5.0,   5.4,   5.8,   6.2,   6.6,   7.0,   7.4,
      7.8,   8.2,   8.6,   9.0,   9.4,   9.8,  10.2,  10.6,  11.0,  11.3,
])

n_points = len(T_raw)
t_array  = np.arange(n_points) * dt   # seconds

# ── Smooth the temperature signal ────────────────────────────────────────────
# Savitzky-Golay: window 7 points (70 s), polynomial order 2
T_smooth = savgol_filter(T_raw, window_length=7, polyorder=2)

# ── Identify the three regions ───────────────────────────────────────────────
# Region 1: single-phase ice warming  (T < -0.5 °C)
# Region 2: phase transition plateau  (-0.5 °C ≤ T ≤ 0.1 °C, dT/dt ≈ 0)
# Region 3: liquid water warming      (T > 0.1 °C)

mask_ice    = T_smooth < -0.5
mask_plat   = (T_smooth >= -0.5) & (T_smooth <= 0.1)
mask_water  = T_smooth > 0.1

t_ice   = t_array[mask_ice]
T_ice   = T_smooth[mask_ice]
t_plat  = t_array[mask_plat]
t_water = t_array[mask_water]
T_water = T_smooth[mask_water]

# ── Linear fit in ice region to get effective specific heat ──────────────────
def linear_model(t, slope, intercept):
    return slope * t + intercept

if len(t_ice) > 3:
    popt_ice, pcov_ice = curve_fit(linear_model, t_ice, T_ice)
    dTdt_ice  = popt_ice[0]   # K/s
    # Heat capacity check: P_net = (m_ice * c_ice + m_cup * c_al) * dT/dt
    C_total_ice = P_net / dTdt_ice      # J/K
    c_ice_meas  = (C_total_ice - m_cup_al * c_aluminum) / m_ice
    print(f"Ice region  dT/dt : {dTdt_ice*1e3:.4f} mK/s")
    print(f"c_ice  measured   : {c_ice_meas:.1f}  J/(kg·K)   [literature: {c_ice:.1f}]")

# ── Linear fit in water region ───────────────────────────────────────────────
if len(t_water) > 3:
    popt_wat, pcov_wat = curve_fit(linear_model, t_water, T_water)
    dTdt_water  = popt_wat[0]
    C_total_wat = P_net / dTdt_water
    c_water_meas = (C_total_wat - m_cup_al * c_aluminum) / m_ice  # mass conserved
    print(f"\nWater region dT/dt: {dTdt_water*1e3:.4f} mK/s")
    print(f"c_water measured  : {c_water_meas:.1f}  J/(kg·K)   [literature: {c_water:.1f}]")

# ── Latent heat from plateau duration ───────────────────────────────────────
if len(t_plat) > 1:
    t_plateau_duration = t_plat[-1] - t_plat[0]   # seconds
    Q_fusion_meas      = P_net * t_plateau_duration  # joules
    L_f_meas           = Q_fusion_meas / m_ice       # J/kg
    pct_err_Lf         = 100 * abs(L_f_meas - L_f_literature) / L_f_literature
    print(f"\nPlateau duration  : {t_plateau_duration:.1f} s")
    print(f"Q_fusion measured : {Q_fusion_meas:.1f} J")
    print(f"L_f measured      : {L_f_meas:.0f} J/kg")
    print(f"L_f literature    : {L_f_literature:.0f} J/kg")
    print(f"% error on L_f    : {pct_err_Lf:.2f}%")

# ── Cumulative energy curve ───────────────────────────────────────────────────
Q_cumulative = P_net * t_array   # joules delivered to system

# ── Figure: T-t curve and cumulative energy ──────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

ax1.plot(t_array / 60, T_raw,    'o', markersize=2, color='lightsteelblue',
         alpha=0.7, label='Raw data')
ax1.plot(t_array / 60, T_smooth, '-', linewidth=2.0, color='steelblue',
         label='Savitzky-Golay smoothed')

# Shade the three regions
ax1.axvspan(t_array[mask_ice][0] / 60 if mask_ice.any() else 0,
            t_array[mask_ice][-1] / 60 if mask_ice.any() else 0,
            alpha=0.10, color='cyan',   label='Ice region')
ax1.axvspan(t_array[mask_plat][0] / 60 if mask_plat.any() else 0,
            t_array[mask_plat][-1] / 60 if mask_plat.any() else 0,
            alpha=0.15, color='orange', label='Phase transition plateau')
ax1.axvspan(t_array[mask_water][0] / 60 if mask_water.any() else 0,
            t_array[-1] / 60,
            alpha=0.10, color='green',  label='Liquid water region')

ax1.axhline(0.0, color='darkred', linewidth=0.8, linestyle='--', alpha=0.6)
ax1.set_ylabel('Temperature (°C)', fontsize=11)
ax1.set_title('Ice–Water Phase Transition: Calorimetric Energy Mapping', fontsize=12)
ax1.legend(fontsize=8, loc='upper left')
ax1.grid(True, alpha=0.3)

ax2.plot(t_array / 60, Q_cumulative, '-', linewidth=2.0, color='darkorange',
         label='Cumulative $Q$ delivered (net)')
ax2.axvspan(t_array[mask_plat][0] / 60 if mask_plat.any() else 0,
            t_array[mask_plat][-1] / 60 if mask_plat.any() else 0,
            alpha=0.15, color='orange', label='Plateau: all $Q$ → $L_f$')
ax2.set_xlabel('Time (minutes)', fontsize=11)
ax2.set_ylabel('Cumulative Energy (J)', fontsize=11)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('calorimeter_phase_transition.pdf', dpi=300, bbox_inches='tight')
plt.show()
```

The two key observables extracted from this script are the specific heat capacities of ice and water (verified against literature values) and the latent heat $L_f$ from the plateau duration. The slope ratios $dT/dt_{ice} / dT/dt_{water}$ should equal $c_{water} / c_{ice} \approx 2.00$ within your experimental uncertainty; if the ratio deviates by more than 10%, revisit the heat-loss calibration because an underestimated $P_{net}$ stretches the apparent plateau and inflates $L_f$.

---

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### RC Circuit Step Response: Time-Constant Extraction and Full Uncertainty Budget

An RC circuit is analytically exact. Given a step input $V_{in}$, the voltage across the capacitor follows:

$$V_C(t) = V_{in}\left(1 - e^{-t/\tau}\right), \quad \tau = RC$$

The time constant $\tau$ has no free parameters: it is entirely determined by the values of $R$ and $C$ on your breadboard. This makes the RC step response an ideal stress-testing vehicle. You can measure $\tau$ three independent ways — directly from the oscilloscope screen (63.2% rule), from a least-squares exponential fit to the acquired waveform, and from the individually measured $R$ and $C$ values using an LCR meter — then compare all three. Any discrepancy larger than the propagated uncertainty is a systematic error that must be explained and tracked back to its source. This is the full discipline of experimental uncertainty analysis applied to a simple system before you trust it on a complicated one.

### Bench Assembly

Build the following on the breadboard: a 10 kΩ ± 1% resistor ($R$) in series with a 100 nF ± 5% ceramic capacitor ($C$). The predicted time constant is $\tau = 10{,}000 \times 100 \times 10^{-9} = 1.00\ \text{ms}$. Connect the function generator output to the RC series combination. Set the function generator to a 50 Hz square wave with 5.0 V peak-to-peak amplitude, 2.5 V DC offset (so the output swings from 0 to 5 V), and confirm on the oscilloscope channel 1 that the waveform looks correct before connecting channel 2. The 50 Hz period is 20 ms, giving the capacitor 10 ms per half-cycle, which is 10 time constants — enough for complete charge and discharge before each new step.

Connect oscilloscope channel 2 across the capacitor only (not the whole circuit). Set channel 2 to DC coupling, 1 V/div, timebase 500 µs/div. Trigger on channel 1's rising edge at the 2.5 V threshold. You should see a clean exponential rise curve on channel 2.

**Oscilloscope measurement:** Use the oscilloscope's built-in cursor tool to place one cursor at $t = 0$ (the moment $V_C$ begins rising) and the second cursor at the moment $V_C = 0.632 \times V_{final}$. If $V_{final} = 5.0\ \text{V}$, the cursor belongs at 3.16 V. The time between the two cursors is your direct-read $\tau_{scope}$. Repeat this measurement five times on five different waveform acquisitions (press RUN/STOP, capture, measure, repeat) and record all five values. Compute mean and standard deviation.

**LCR meter measurement:** Remove $R$ from the breadboard. Set the LCR meter to resistance mode at 1 kHz. Measure the resistor four times, rotating it 90° between measurements to cancel probe contact asymmetry. Repeat with $C$ in capacitance mode at 1 kHz. Record all eight individual readings. The LCR-derived $\tau_{LCR} = \bar{R} \cdot \bar{C}$.

### Full Uncertainty Propagation and Oscilloscope Data Acquisition Script

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats    import t as t_dist   # Student's t distribution

# ── Oscilloscope step-response data ─────────────────────────────────────────
# The oscilloscope exports a CSV with time (seconds) and voltage (volts).
# Paste your acquired waveform here. These values represent a typical
# 10 kΩ / 100 nF bench acquisition at 1 MS/s (1 µs per sample).

# Time array: 0 to 5 ms in 2-µs steps (2500 points)
dt_scope   = 2e-6          # 2 µs per sample (500 kHz effective rate)
n_samples  = 2500
t_scope    = np.arange(n_samples) * dt_scope

# Synthetic waveform with realistic noise: replace with oscilloscope CSV data
np.random.seed(42)
tau_true   = 1.012e-3      # simulating a slight R and C tolerance shift
V_final    = 4.98          # V (actual supply after cable loading)
V_noise    = 0.025         # V RMS noise (typical for 8-bit scope at 1V/div)

V_scope_clean  = V_final * (1 - np.exp(-t_scope / tau_true))
V_scope        = V_scope_clean + np.random.normal(0, V_noise, n_samples)

# ── Exponential fit ──────────────────────────────────────────────────────────
def exp_rise(t, V_inf, tau):
    return V_inf * (1.0 - np.exp(-t / tau))

p0 = [5.0, 1.0e-3]   # initial guesses: V_inf = 5 V, tau = 1 ms

popt, pcov = curve_fit(exp_rise, t_scope, V_scope,
                       p0=p0, maxfev=10000)

V_fit,  tau_fit  = popt
V_fit_unc, tau_fit_unc = np.sqrt(np.diag(pcov))

print(f"Exponential fit results:")
print(f"  V_inf  = {V_fit:.4f} V    (±{V_fit_unc:.4f} V  1-sigma)")
print(f"  tau    = {tau_fit*1e6:.2f} µs  (±{tau_fit_unc*1e6:.2f} µs  1-sigma)")

# ── Oscilloscope cursor method (five repeated readings) ──────────────────────
# Replace with your five recorded values in microseconds
tau_cursor_us = np.array([1018, 1024, 1009, 1031, 1016])  # µs
tau_cursor_s  = tau_cursor_us * 1e-6
tau_cursor_mean = np.mean(tau_cursor_s)
tau_cursor_std  = np.std(tau_cursor_s, ddof=1)
n_cursor        = len(tau_cursor_s)

# 95% confidence interval using Student's t (n-1 degrees of freedom)
t_critical_cursor = t_dist.ppf(0.975, df=n_cursor - 1)
tau_cursor_ci95   = t_critical_cursor * tau_cursor_std / np.sqrt(n_cursor)

print(f"\nCursor method (n={n_cursor}):")
print(f"  tau_mean = {tau_cursor_mean*1e6:.2f} µs")
print(f"  std_dev  = {tau_cursor_std*1e6:.2f} µs")
print(f"  95% CI   = ±{tau_cursor_ci95*1e6:.2f} µs")

# ── LCR meter measurements ────────────────────────────────────────────────────
# Four resistance readings (ohms) and four capacitance readings (farads)
R_lcr_readings = np.array([9987.0, 9991.0, 9983.0, 9988.0])  # Ω
C_lcr_readings = np.array([101.4e-9, 101.1e-9, 101.6e-9, 101.3e-9])  # F

R_mean  = np.mean(R_lcr_readings)
R_std   = np.std(R_lcr_readings, ddof=1)
C_mean  = np.mean(C_lcr_readings)
C_std   = np.std(C_lcr_readings, ddof=1)

tau_lcr     = R_mean * C_mean
# Propagate: (delta_tau/tau)^2 = (delta_R/R)^2 + (delta_C/C)^2
# Using standard deviation of the mean as the uncertainty on each
n_lcr        = len(R_lcr_readings)
R_sem        = R_std / np.sqrt(n_lcr)
C_sem        = C_std / np.sqrt(n_lcr)
tau_lcr_unc  = tau_lcr * np.sqrt((R_sem / R_mean)**2 + (C_sem / C_mean)**2)

print(f"\nLCR meter method:")
print(f"  R_mean  = {R_mean:.2f} Ω   (±{R_sem:.2f} Ω SEM)")
print(f"  C_mean  = {C_mean*1e9:.3f} nF  (±{C_sem*1e9:.3f} nF SEM)")
print(f"  tau_LCR = {tau_lcr*1e6:.2f} µs  (±{tau_lcr_unc*1e6:.2f} µs)")

# ── Comparison table and chi-squared consistency check ───────────────────────
methods = ['Exponential fit', 'Cursor (mean)', 'LCR product']
tau_vals = [tau_fit,          tau_cursor_mean, tau_lcr]
tau_uncs = [tau_fit_unc,      tau_cursor_ci95, tau_lcr_unc]

print(f"\n{'─'*58}")
print(f"{'Method':<20}  {'τ (µs)':>10}  {'±Unc (µs)':>12}  {'Dev from fit':>12}")
print(f"{'─'*58}")
for meth, tv, tu in zip(methods, tau_vals, tau_uncs):
    dev = (tv - tau_fit) / tau_fit_unc
    print(f"{meth:<20}  {tv*1e6:>10.2f}  {tu*1e6:>12.2f}  {dev:>+11.2f}σ")
print(f"{'─'*58}")

# ── Boundary condition stress test: vary R from 5 kΩ to 50 kΩ ────────────────
# Predict tau, then compare to what a noisy real acquisition would yield
R_sweep    = np.linspace(5000, 50000, 20)   # Ω
tau_pred   = R_sweep * C_mean               # predicted tau at LCR C

# Simulate what the curve-fit would return for each R value
# (in a real lab, these are your breadboard-swap measurements)
tau_meas_sweep = tau_pred * (1 + np.random.normal(0, 0.012, len(R_sweep)))
tau_meas_unc   = tau_pred * 0.012   # 1.2% random error per swap

# ── Figures ──────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Panel 1: Raw waveform + fit
axes[0].plot(t_scope * 1e3, V_scope,       'o', markersize=1.2, color='lightsteelblue',
             alpha=0.5, label='Acquired data')
axes[0].plot(t_scope * 1e3, exp_rise(t_scope, *popt), '-', linewidth=2.0,
             color='steelblue', label=f'Fit: τ={tau_fit*1e6:.1f} µs')
axes[0].axhline(0.632 * V_fit, color='darkorange', linewidth=1.0, linestyle='--',
                alpha=0.7, label='63.2% level')
axes[0].set_xlabel('Time (ms)')
axes[0].set_ylabel('Voltage (V)')
axes[0].set_title('RC Step Response: Acquired Waveform')
axes[0].legend(fontsize=8)
axes[0].grid(True, alpha=0.3)

# Panel 2: Comparison bar chart
method_labels = ['Exp. Fit', 'Cursor', 'LCR R×C']
x_pos = np.arange(len(method_labels))
axes[1].bar(x_pos, [tv * 1e6 for tv in tau_vals],
            yerr=[tu * 1e6 for tu in tau_uncs],
            color=['steelblue', 'darkorange', 'seagreen'],
            capsize=6, width=0.5, alpha=0.8)
axes[1].axhline(tau_lcr * 1e6, color='black', linewidth=0.8, linestyle=':')
axes[1].set_xticks(x_pos)
axes[1].set_xticklabels(method_labels, fontsize=9)
axes[1].set_ylabel('Time Constant τ (µs)')
axes[1].set_title('Three-Method τ Comparison')
axes[1].grid(True, axis='y', alpha=0.3)

# Panel 3: Stress test sweep
axes[2].plot(R_sweep / 1000, tau_pred * 1e6, '--', linewidth=1.5,
             color='gray', label='Predicted τ = R × C̄')
axes[2].errorbar(R_sweep / 1000, tau_meas_sweep * 1e6,
                 yerr=tau_meas_unc * 1e6,
                 fmt='o', markersize=4, color='steelblue', capsize=4,
                 label='Measured τ (simulated bench)')
axes[2].set_xlabel('Resistance R (kΩ)')
axes[2].set_ylabel('Time Constant τ (µs)')
axes[2].set_title('Stress Test: τ vs R (C fixed)')
axes[2].legend(fontsize=8)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('rc_stress_test_uncertainty.pdf', dpi=300, bbox_inches='tight')
plt.show()

# ── Formal uncertainty budget table ─────────────────────────────────────────
print(f"\n{'═'*62}")
print(f"{'UNCERTAINTY BUDGET — RC Time Constant Measurement':^62}")
print(f"{'═'*62}")
print(f"{'Source':<28}  {'Type':>6}  {'Value':>10}  {'Contribution':>12}")
print(f"{'─'*62}")

# Type A: statistical from fit
u_A_fit    = tau_fit_unc
# Type A: cursor repeatability
u_A_cursor = tau_cursor_std / np.sqrt(n_cursor)
# Type B: LCR R reading (rectangular distribution: tolerance ±1% → std = 1%/√3)
u_B_R      = R_mean * 0.01 / np.sqrt(3)
# Type B: LCR C reading (tolerance ±5% → std = 5%/√3)
u_B_C      = C_mean * 0.05 / np.sqrt(3)
u_B_tau    = tau_lcr * np.sqrt((u_B_R/R_mean)**2 + (u_B_C/C_mean)**2)
# Type B: oscilloscope timebase accuracy (quoted ±50 ppm → ~0.005%)
u_B_tb     = tau_fit * 50e-6

rows = [
    ("Fit covariance (Type A)",     "A", u_A_fit,    u_A_fit),
    ("Cursor repeatability (A)",    "A", u_A_cursor, u_A_cursor),
    ("R component tolerance (B)",   "B", u_B_R,      u_B_R * C_mean),
    ("C component tolerance (B)",   "B", u_B_C,      tau_lcr * (u_B_C/C_mean)),
    ("Scope timebase (B)",          "B", u_B_tb,     u_B_tb),
]

u_combined = np.sqrt(sum(r[3]**2 for r in rows))

for name, kind, val, contrib in rows:
    print(f"{name:<28}  {kind:>6}  {val*1e9:>8.2f} ns  {contrib*1e9:>10.2f} ns")
print(f"{'─'*62}")
print(f"{'Combined u_c (k=1)':<28}  {'─':>6}  {'─':>10}  {u_combined*1e9:>10.2f} ns")
print(f"{'Expanded U (k=2, 95%)':<28}  {'─':>6}  {'─':>10}  {2*u_combined*1e9:>10.2f} ns")
print(f"{'═'*62}")
```

The uncertainty budget printed at the end follows GUM (Guide to the Expression of Uncertainty in Measurement) conventions. Type A uncertainties come from repeated observations; Type B from calibration certificates, component tolerances, and equipment specifications. Component tolerance is the dominant contributor by a factor of three to five. If you replace the 5% ceramic capacitor with a 1% polypropylene film capacitor, the combined uncertainty drops below 150 ns on a 1 ms time constant, bringing the relative uncertainty below 0.015%.

---

## Laboratory Cheat Sheet & Metric Verification Guide

### Environment and Tool Verification

| Check | Command | Minimum Acceptable |
|---|---|---|
| Python version | `python --version` | 3.10+ |
| NumPy | `python -c "import numpy; print(numpy.__version__)"` | 1.24+ |
| SciPy | `python -c "import scipy; print(scipy.__version__)"` | 1.10+ |
| Matplotlib | `python -c "import matplotlib; print(matplotlib.__version__)"` | 3.7+ |
| Astropy | `python -c "import astropy; print(astropy.__version__)"` | 5.3+ |
| Avogadro | `avogadro --version` (GUI app) | 1.97+ |
| PyMOL | `python -c "import pymol; print(pymol.__version__)"` | 2.5+ |

### Physical Constants Reference

| Constant | Symbol | Value | Units |
|---|---|---|---|
| Planck's constant | $h$ | $6.62607015 \times 10^{-34}$ | J·s |
| Elementary charge | $e$ | $1.60217663 \times 10^{-19}$ | C |
| Speed of light | $c$ | $2.99792458 \times 10^{8}$ | m/s |
| Boltzmann constant | $k_B$ | $1.380649 \times 10^{-23}$ | J/K |
| Avogadro's number | $N_A$ | $6.02214076 \times 10^{23}$ | mol⁻¹ |
| Latent heat of ice fusion | $L_f$ | $334{,}000$ | J/kg |
| Specific heat — water | $c_p$ | $4186$ | J/(kg·K) |
| Specific heat — ice | $c_p$ | $2090$ | J/(kg·K) |

### Instrument Calibration Checklist

Perform the following before any measurement session starts. Run through the list in order; a failure at any step invalidates downstream data.

| Step | Action | Pass Criterion |
|---|---|---|
| Oscilloscope probe comp | 1 kHz square wave at comp terminal; trim until flat top | Corners sharp; top flat to ±2% of amplitude |
| DMM null | Short DMM leads in resistance mode | Reads ≤ 0.1 Ω before zeroing |
| Thermometer ice point | Probe in well-stirred ice-water slurry | Reads 0.0 ± 0.2 °C after 90 s |
| Watt-meter calibration | Known load (1 kΩ ± 0.1% at measured 5.000 V) | Reads 25.0 ± 0.3 mW |
| Spectrophotometer wavelength | 546.1 nm mercury vapor lamp line | Peak ≤ ±1.0 nm from 546.1 nm |
| LCR meter reference | Measure 10.00 kΩ ± 0.01% standard resistor | Reads within ±0.1% of 10.00 kΩ |

### Expected Metric Outcomes

| Exercise | Observable | Expected Result | Acceptable Deviation |
|---|---|---|---|
| 1 | $h$ weighted mean | $6.63 \times 10^{-34}\ \text{J·s}$ | ≤ 5% from CODATA |
| 1 | Per-LED $h$ spread | ≤ 8% across four LEDs | Larger spread → check λ calibration |
| 2 | $c_{water}$ measured | 4186 J/(kg·K) | ≤ 4% relative |
| 2 | $L_f$ measured | 334,000 J/kg | ≤ 6% relative |
| 2 | $c_{ice}/c_{water}$ ratio | 0.499 | ≤ 5% relative |
| 3 | $\tau_{fit}$ vs $\tau_{LCR}$ | Agreement within 1.5% | Larger gap → check C tolerance |
| 3 | Expanded uncertainty $U$ (k=2) | ≤ 300 ns on 1 ms $\tau$ | Larger → component grade issue |

### Common Error States and Diagnostic Actions

A threshold voltage that shifts by more than 15 mV between consecutive sweeps on the same LED almost always indicates junction self-heating from too-rapid stepping or insufficient current limiting. Verify the series resistance is physically in circuit by measuring $V_{resistor}$ directly; a solder bridge or reversed probe will read zero volts across it. A calorimetric $L_f$ that exceeds the literature value by more than 10% points to an overestimated $P_{net}$: recalibrate the heat-loss rate at the specific ambient temperature of the lab, because the Styrofoam loss rate increases by roughly 0.4 W per 5 °C of room temperature rise. An RC time constant that is consistently shorter than predicted at all $R$ values in the stress sweep indicates parasitic capacitance on the breadboard rails — spring-clip breadboards add 5–20 pF of stray capacitance per row, which is negligible at 100 nF but becomes a 1–5% correction at 10 nF. Replace the breadboard with direct soldered connections for high-precision RC work below 10 nF.
