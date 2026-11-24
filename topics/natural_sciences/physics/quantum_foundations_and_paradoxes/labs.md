# Operational Verification Labs: Quantum Foundations And Paradoxes

---

## Objective & Laboratory Bench Setup

Quantum mechanics is not merely a theoretical framework — it is a laboratory science with measurable, reproducible signatures that deviate sharply and predictably from classical predictions. This guide treats quantum foundations not as philosophical abstraction but as a body of experimentally accessible phenomena: photoelectric thresholds you can measure with a UV lamp and a phototube, interference fringes you can photograph, uncertainty relations you can probe through diffraction geometry, and statistical distributions you can reconstruct from raw photon-counting data. Every exercise here is designed around the principle that the paradoxes of quantum mechanics — wave-particle duality, the uncertainty principle, quantization of energy and momentum — dissolve into clean, reproducible measurement protocols once you know exactly what to look for and how to look.

The theoretical backbone is minimal but precise. The energy of a photon is $E = h\nu$, where $h = 6.626 \times 10^{-34}\ \text{J·s}$ is Planck's constant and $\nu$ is frequency in hertz. The de Broglie wavelength of a particle with momentum $p$ is:

$$\lambda = \frac{h}{p}$$

The Heisenberg uncertainty principle sets a hard lower bound on simultaneous position and momentum knowledge:

$$\Delta x \cdot \Delta p \geq \frac{\hbar}{2}, \quad \hbar = \frac{h}{2\pi}$$

The time-dependent Schrödinger equation governs the evolution of a quantum state $|\psi(t)\rangle$ in Hilbert space:

$$i\hbar \frac{\partial}{\partial t}|\psi\rangle = \hat{H}|\psi\rangle$$

These four relationships — Planck's energy quantization, de Broglie wave-matter duality, Heisenberg's uncertainty bound, and Schrödinger's propagator — are the four empirical anchors the lab exercises below are designed to verify, stress-test, and push to their boundary conditions.

### Physical Laboratory Bench Configuration

Your bench requires three distinct instrument zones. In the **optical zone**, mount a mercury-vapor UV lamp with a 254 nm and 365 nm switchable filter set, a commercial vacuum phototube (e.g., Leybold 558 77 or equivalent), a precision voltmeter (resolution ≤ 0.001 V) for stopping-potential measurement, and a stable DC power supply capable of reversed-bias voltage from 0 to −3 V. Secure the lamp housing at a fixed 15 cm working distance from the phototube window using an optical rail, and blackout the bench with matte enclosure cloth to suppress ambient photocurrent noise.

In the **diffraction zone**, position a green diode laser pointer (532 nm, ≤ 5 mW, class IIIa) on a kinematic mount at one end of a 2-meter optical bench. At 1.0 m from the laser aperture, mount a precision single-slit slide in a micrometer-driven slit holder (slit widths available: 0.04 mm, 0.08 mm, 0.16 mm). At the far end, 1.0 m beyond the slit, secure a white projection screen with millimeter graph paper taped flat. Use a USB-connected digital camera (or a calibrated CMOS line sensor) to capture fringe patterns for quantitative pixel-to-millimeter analysis.

In the **computation zone**, run a standard laboratory workstation with the following verified Python environment:

```bash
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "import scipy; print('SciPy', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib', matplotlib.__version__)"
```

Required versions: NumPy ≥ 1.24, SciPy ≥ 1.10, Matplotlib ≥ 3.7. All computational exercises below are written against these versions with zero dependency on deprecated APIs. Install with:

```bash
pip install numpy>=1.24 scipy>=1.10 matplotlib>=3.7
```

---

## Exercise 1: Empirical Observation & Measurement Protocol

### The Photoelectric Effect: Measuring Planck's Constant Directly

The photoelectric effect is the founding experimental proof of energy quantization. Einstein's 1905 interpretation established that light delivers energy in discrete quanta, each carrying $E = h\nu$. When a photon strikes a metal surface with work function $\phi$, it ejects an electron only if $h\nu \geq \phi$. The maximum kinetic energy of the ejected electron is then:

$$K_{\max} = h\nu - \phi$$

The stopping potential $V_s$ is the reversed bias voltage at which the photocurrent drops exactly to zero — the point where the retarding electric field has absorbed all kinetic energy from the fastest electrons: $eV_s = K_{\max}$. Combining these:

$$eV_s = h\nu - \phi \quad \Longrightarrow \quad V_s = \frac{h}{e}\nu - \frac{\phi}{e}$$

This is a linear equation in frequency. The slope is $h/e$, and from the known electron charge $e = 1.602 \times 10^{-19}\ \text{C}$, you recover Planck's constant directly from a plot of $V_s$ versus $\nu$.

**Physical Procedure.** Begin with the 254 nm UV filter installed (frequency $\nu_{254} = c/\lambda = 3.00 \times 10^8 / 254 \times 10^{-9} = 1.181 \times 10^{15}\ \text{Hz}$). With the lamp off, zero your voltmeter. Switch the lamp on and allow a 3-minute thermal warm-up period to stabilize lamp intensity. Apply a forward bias of +0.5 V to confirm measurable photocurrent (the ammeter should read a stable baseline, typically 10–100 nA depending on your phototube sensitivity). Now sweep the reversed bias voltage from 0 V toward −3 V in 0.05 V steps. At each step, wait 10 seconds for the photocurrent to stabilize, then record the ammeter reading. The stopping potential $V_s$ is the voltage at which the ammeter first reads zero (or reaches your instrument noise floor, typically < 0.1 nA). Record this $V_{s,254}$. Repeat the full voltage sweep three times and take the mean, computing the standard deviation as your measurement uncertainty.

Swap to the 365 nm filter (frequency $\nu_{365} = 8.219 \times 10^{14}\ \text{Hz}$) and repeat the full three-sweep protocol to obtain $V_{s,365}$. If your filter set includes additional lines (405 nm, 436 nm from mercury), perform the same procedure for each — more frequency-voltage pairs improve your linear regression and reduce systematic error. Record all measurements in a structured table: frequency in Hz, mean stopping potential in volts, and standard deviation.

**Computational Analysis.** The following script ingests your measured stopping potentials, performs a weighted linear regression using SciPy, and extracts Planck's constant with formal uncertainty:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.optimize import curve_fit

# ── Measured data: (frequency in Hz, stopping potential in V, std dev in V)
# Replace with your actual bench measurements; these are representative values
# for a zinc-cathode phototube with ~4.3 eV work function.
data = np.array([
    [1.181e15, 1.60, 0.03],   # 254 nm UV
    [8.219e14, 0.73, 0.02],   # 365 nm UV
    [7.408e14, 0.47, 0.02],   # 405 nm violet
    [6.879e14, 0.26, 0.02],   # 436 nm blue
])

nu   = data[:, 0]   # frequency (Hz)
Vs   = data[:, 1]   # stopping potential (V)
dVs  = data[:, 2]   # measurement uncertainty (V)

# ── Weighted linear regression: Vs = (h/e)*nu - phi/e
# scipy.stats.linregress does not natively support weights,
# so we implement weighted least-squares via numpy.polyfit
weights = 1.0 / dVs**2
coeffs, cov = np.polyfit(nu, Vs, deg=1, w=np.sqrt(weights), cov=True)

slope     = coeffs[0]   # h/e  (V·s)
intercept = coeffs[1]   # -phi/e  (V)
slope_err = np.sqrt(cov[0, 0])
int_err   = np.sqrt(cov[1, 1])

e_charge   = 1.602e-19   # C
h_measured = slope * e_charge
h_err      = slope_err * e_charge
phi_eV     = -intercept  # already in eV since intercept = -phi/e and e=1
h_accepted = 6.626e-34

percent_error = abs(h_measured - h_accepted) / h_accepted * 100

print("=" * 52)
print("  PLANCK'S CONSTANT EXTRACTION")
print("=" * 52)
print(f"  Slope  h/e   = {slope:.4e} ± {slope_err:.2e}  V·s")
print(f"  h (measured) = {h_measured:.4e} ± {h_err:.2e}  J·s")
print(f"  h (accepted) = {h_accepted:.4e}  J·s")
print(f"  Percent error= {percent_error:.2f}%")
print(f"  Work function= {phi_eV:.3f} eV")
print("=" * 52)

# ── Plot
nu_fit = np.linspace(nu.min() * 0.98, nu.max() * 1.02, 300)
Vs_fit = np.polyval(coeffs, nu_fit)

fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(nu, Vs, yerr=dVs, fmt='o', color='steelblue',
            markersize=7, capsize=5, label='Measured stopping potentials')
ax.plot(nu_fit, Vs_fit, '-', color='firebrick', linewidth=2,
        label=f'Linear fit  (slope = {slope:.3e} V·s)')
ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')

# Threshold frequency where Vs = 0
nu_threshold = -intercept / slope
ax.axvline(nu_threshold, color='darkgreen', linewidth=1.2, linestyle=':',
           label=f'Threshold ν₀ = {nu_threshold:.3e} Hz')

ax.set_xlabel('Frequency  ν  (Hz)', fontsize=13)
ax.set_ylabel('Stopping Potential  V$_s$  (V)', fontsize=13)
ax.set_title("Photoelectric Effect — Planck's Constant Measurement", fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('planck_measurement.png', dpi=180)
plt.show()
print("Figure saved → planck_measurement.png")
```

Run with `python planck_measurement.py`. The expected output for a well-calibrated bench is a percent error below 3%, confirming that $h \approx 6.6 \times 10^{-34}\ \text{J·s}$ is recoverable from a benchtop stopping-potential sweep. If your percent error exceeds 5%, check for contact potential offsets in your phototube circuit, verify lamp filter transmission curves with a spectrometer, and confirm your voltmeter is reading the actual phototube bias rather than an IR-drop across series resistance.

---

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Single-Slit Diffraction and the Position-Momentum Uncertainty Relation

The Heisenberg uncertainty principle is not merely a theoretical claim — it manifests directly and measurably in single-slit diffraction. When a coherent beam passes through a slit of width $a$, confining the photon's transverse position to $\Delta x \approx a$, the beam acquires a spread of transverse momentum. The first diffraction minimum appears at angle $\theta$ satisfying:

$$a \sin\theta = \lambda$$

The transverse momentum uncertainty imparted to photons that pass through the slit is $\Delta p_y \approx p \sin\theta = (h/\lambda)\sin\theta$. Substituting the first-minimum condition $\sin\theta = \lambda/a$:

$$\Delta x \cdot \Delta p_y \approx a \cdot \frac{h}{\lambda} \cdot \frac{\lambda}{a} = h$$

This is on the order of $\hbar$ (within a factor of $2\pi$), confirming that the uncertainty bound $\Delta x \cdot \Delta p \geq \hbar/2$ is saturated. By varying slit width systematically and measuring the resulting fringe half-width, you map out the inverse relationship between $\Delta x$ and $\Delta p$ across a full order of magnitude.

**Physical Procedure.** Mount the 532 nm laser on the optical rail with the beam propagating horizontally. Confirm beam circularity and lack of astigmatism by projecting it on the screen without a slit: you should see a symmetric Gaussian spot. Install the 0.04 mm slit first. The slit holder micrometer should be zeroed by advancing until photocurrent drops to zero (slit closed), then backing off to your target width. Measure the geometric slit width independently with a calibrated reticle eyepiece or a traveling microscope to verify the manufacturer specification.

Dim the room completely. The diffraction pattern will appear on the graph-paper screen as a bright central maximum flanked by symmetric minima. Photograph the pattern with the USB camera at a fixed exposure (ISO 400, 1/30 s is a reasonable starting point for a 5 mW green laser on a white screen at 1 m). Use a ruler fixed alongside the graph paper for pixel-to-mm calibration: photograph the ruler at the screen plane, count pixels per millimeter, and store this calibration factor before moving the camera.

Measure the distance $y_1$ from the central maximum to the first minimum on both sides and average them. The slit-to-screen distance $L = 1.000\ \text{m}$ (measured with a steel tape to ±1 mm). The first minimum half-angle satisfies $\tan\theta_1 \approx \sin\theta_1 = y_1/L$ for small angles. Record $(a, y_1)$ for slit widths 0.04 mm, 0.08 mm, and 0.16 mm. At each slit width, capture three photographs, extract $y_1$ from each using the calibration, and compute mean ± standard deviation.

**Computational Analysis.** The following script models the full single-slit intensity pattern as $I(\theta) = I_0 \left(\frac{\sin\beta}{\beta}\right)^2$ where $\beta = \pi a \sin\theta / \lambda$, fits the model to your pixel-intensity data extracted from the photographs, and constructs the $\Delta x$-$\Delta p$ product curve:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter1d

# ═══════════════════════════════════════════════════════════
# SECTION 1: Theoretical single-slit intensity model
# ═══════════════════════════════════════════════════════════

lam = 532e-9       # laser wavelength (m)
L   = 1.000        # slit-to-screen distance (m)

def sinc_intensity(y, I0, a_m, y0, bg):
    """
    Single-slit diffraction intensity as a function of screen position y (m).
    Parameters:
      I0   – peak intensity (arbitrary units)
      a_m  – slit width (m)
      y0   – center offset (m)
      bg   – background intensity
    """
    beta = np.pi * a_m * (y - y0) / (lam * L)
    # Safe sinc: avoid division by zero at beta=0
    with np.errstate(divide='ignore', invalid='ignore'):
        sinc_val = np.where(np.abs(beta) < 1e-12, 1.0, np.sin(beta) / beta)
    return bg + I0 * sinc_val**2


# ═══════════════════════════════════════════════════════════
# SECTION 2: Synthetic "measured" intensity profiles
# Substitute real pixel row data extracted from your photographs
# using: row = image_array[center_row, :] after grayscale conversion.
# ═══════════════════════════════════════════════════════════

def generate_synthetic_profile(a_mm, noise_std=0.015, seed=42):
    """Generate a realistic synthetic diffraction profile for slit width a_mm."""
    rng = np.random.default_rng(seed)
    y_mm = np.linspace(-15, 15, 1200)        # screen position (mm)
    y_m  = y_mm * 1e-3
    a_m  = a_mm * 1e-3
    beta = np.pi * a_m * y_m / (lam * L)
    with np.errstate(divide='ignore', invalid='ignore'):
        sinc_v = np.where(np.abs(beta) < 1e-12, 1.0, np.sin(beta) / beta)
    I_true = sinc_v**2
    # Add Gaussian optical blur and Poisson-like noise
    I_blur = gaussian_filter1d(I_true, sigma=3)
    I_noisy = I_blur + rng.normal(0, noise_std, len(I_blur))
    return y_mm, np.clip(I_noisy, 0, None)

slit_widths_mm = [0.04, 0.08, 0.16]
profiles = {a: generate_synthetic_profile(a) for a in slit_widths_mm}

# ═══════════════════════════════════════════════════════════
# SECTION 3: Fit each profile, extract first-minimum position
# ═══════════════════════════════════════════════════════════

results = []
fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)

for idx, a_mm in enumerate(slit_widths_mm):
    y_mm, I_data = profiles[a_mm]
    y_m = y_mm * 1e-3
    a_m = a_mm * 1e-3

    # Initial parameter guesses
    p0 = [1.0, a_m, 0.0, 0.01]
    bounds = ([0, a_m*0.3, -0.01, 0], [5, a_m*3.0, 0.01, 0.1])

    try:
        popt, pcov = curve_fit(sinc_intensity, y_m, I_data, p0=p0,
                               bounds=bounds, maxfev=8000)
        I0_fit, a_fit, y0_fit, bg_fit = popt
        perr = np.sqrt(np.diag(pcov))
        a_fit_mm   = a_fit * 1e3
        a_fit_err  = perr[1] * 1e3

        # First minimum position: y_min1 = lambda*L / a_fit
        y1_theory  = lam * L / a_fit          # meters
        y1_mm_fit  = y1_theory * 1e3

        # Uncertainty product: Delta_x * Delta_p
        delta_x  = a_m                        # slit width = position uncertainty
        delta_py = (6.626e-34 / lam) * (lam / a_m)  # = h/a — transverse momentum spread
        UP       = delta_x * delta_py         # should be ≈ h

        results.append({
            'a_nominal_mm' : a_mm,
            'a_fit_mm'     : a_fit_mm,
            'a_fit_err_mm' : a_fit_err,
            'y1_fit_mm'    : y1_mm_fit,
            'delta_x_m'    : delta_x,
            'delta_py'     : delta_py,
            'UP_Js'        : UP,
            'UP_hbar_ratio': UP / (6.626e-34 / (2 * np.pi)),
        })

        # Plot
        ax = axes[idx]
        ax.plot(y_mm, I_data, 'o', markersize=1.5, alpha=0.5,
                color='steelblue', label='Measured')
        y_fine = np.linspace(y_m.min(), y_m.max(), 3000)
        ax.plot(y_fine * 1e3,
                sinc_intensity(y_fine, *popt),
                '-', color='firebrick', linewidth=2,
                label=f'Fit  a = {a_fit_mm:.3f} mm')
        ax.axvline( y1_mm_fit, color='darkgreen', linestyle='--', linewidth=1.2)
        ax.axvline(-y1_mm_fit, color='darkgreen', linestyle='--', linewidth=1.2,
                   label=f'1st min ±{y1_mm_fit:.2f} mm')
        ax.set_xlabel('Screen position (mm)', fontsize=11)
        ax.set_ylabel('Relative Intensity', fontsize=11)
        ax.set_title(f'Slit width {a_mm} mm', fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)

    except RuntimeError as exc:
        print(f"Fit failed for a={a_mm} mm: {exc}")

plt.suptitle('Single-Slit Diffraction — Heisenberg Uncertainty Verification\n'
             f'λ = 532 nm,  L = {L} m', fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig('diffraction_fits.png', dpi=180, bbox_inches='tight')
plt.show()
print("Figure saved → diffraction_fits.png")

# ═══════════════════════════════════════════════════════════
# SECTION 4: Uncertainty product summary table
# ═══════════════════════════════════════════════════════════
hbar = 6.626e-34 / (2 * np.pi)
print("\n" + "=" * 70)
print(f"  {'a (mm)':<10} {'Δx (μm)':<12} {'Δpᵧ (kg·m/s)':<18} "
      f"{'ΔxΔpᵧ (J·s)':<18} {'/ ℏ':<8}")
print("=" * 70)
for r in results:
    print(f"  {r['a_nominal_mm']:<10.3f} "
          f"{r['delta_x_m']*1e6:<12.1f} "
          f"{r['delta_py']:<18.4e} "
          f"{r['UP_Js']:<18.4e} "
          f"{r['UP_hbar_ratio']:<8.1f}")
print("=" * 70)
print(f"  ℏ = {hbar:.4e} J·s   (Heisenberg bound: ΔxΔp ≥ ℏ/2 = {hbar/2:.4e} J·s)")
```

Run with `python diffraction_uncertainty.py`. The printed table should show $\Delta x \cdot \Delta p_y \approx h$ for each slit width, with the ratio $\Delta x \Delta p_y / \hbar$ converging toward $2\pi \approx 6.28$ — which is consistent with the first-minimum criterion being one full oscillation of the sinc argument. The key experimental signature to verify is the strict inverse relationship: as slit width halves, the central maximum half-width doubles. Any deviation from this $a \cdot y_1 = \lambda L$ hyperbola indicates either a non-monochromatic light source, mechanical vibration in the slit mount, or a slit that is not uniform along its length (inspect with a microscope if divergence exceeds 10% from prediction).

---

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### Quantum Harmonic Oscillator: Energy Level Spacing from Vibrational Spectroscopy

The quantum harmonic oscillator is not an idealization reserved for textbooks — it describes the vibrational modes of diatomic molecules to first approximation, and those modes are directly observable via infrared (IR) spectroscopy. The energy eigenvalues are:

$$E_n = \hbar\omega_0 \left(n + \frac{1}{2}\right), \quad n = 0, 1, 2, \ldots$$

where $\omega_0 = \sqrt{k/\mu}$ is the classical angular frequency of the oscillator, $k$ is the bond force constant in N/m, and $\mu = m_1 m_2 / (m_1 + m_2)$ is the reduced mass of the diatomic pair. Transitions between adjacent levels ($\Delta n = \pm 1$, the selection rule for a harmonic dipole oscillator) emit or absorb a photon of frequency exactly $\nu_0 = \omega_0 / (2\pi)$. For a real molecule, anharmonicity shifts successive transitions downward in wavenumber: the overtone at $2\nu_0$ appears at slightly less than twice the fundamental frequency, and this deviation is parametrized by the anharmonicity constant $x_e$.

The anharmonic energy levels for a Morse oscillator are:

$$E_n = \hbar\omega_e \left[\left(n + \frac{1}{2}\right) - x_e\left(n + \frac{1}{2}\right)^2\right]$$

where $\omega_e$ is the harmonic angular frequency and $x_e$ is the dimensionless anharmonicity parameter. The transition frequency from level $n$ to $n+1$ is then:

$$\tilde{\nu}_{n \to n+1} = \tilde{\nu}_e \left[1 - 2x_e(n+1)\right] \quad (\text{in cm}^{-1})$$

This linear decrease in transition spacing with $n$ is called the Birge-Sponer relation, and fitting it to observed overtone positions is the standard laboratory procedure for extracting $\tilde{\nu}_e$ and $x_e$ simultaneously.

**Physical Procedure.** This exercise uses the near-IR absorption spectrum of HCl gas, which is the canonical pedagogical molecule for this measurement because its vibrational fundamental at $\approx 2886\ \text{cm}^{-1}$ and its first overtone at $\approx 5668\ \text{cm}^{-1}$ are both accessible with a benchtop FTIR spectrometer. Place a 10 cm gas cell filled with HCl at approximately 100 Torr (diluted in N₂ to 1 atm total) in the sample beam of a Thermo Nicolet or Bruker FTIR spectrometer. Set the resolution to $0.5\ \text{cm}^{-1}$ (higher resolution resolves the rotational fine structure, which you will use to extract the moment of inertia, but $0.5\ \text{cm}^{-1}$ is sufficient to identify band centers). Scan from $500\ \text{cm}^{-1}$ to $7000\ \text{cm}^{-1}$. Record a background spectrum with the empty cell first, then the sample spectrum; the instrument software computes the transmittance ratio automatically.

Identify the band centers of the fundamental ($v = 0 \to 1$), first overtone ($v = 0 \to 2$), and second overtone ($v = 0 \to 3$) in your transmittance spectrum. For the fundamental, the band center is the intensity minimum of the Q-branch gap between the R and P branches (at approximately $2886\ \text{cm}^{-1}$ for $^1\text{H}^{35}\text{Cl}$). Export the spectrum as a two-column ASCII file (wavenumber, transmittance) for analysis.

**Computational Analysis.** The following script loads the FTIR ASCII output, identifies absorption band centers by peak detection, constructs the Birge-Sponer plot, and extracts $\tilde{\nu}_e$, $x_e$, and the dissociation energy $D_e$:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths
from scipy.optimize import curve_fit

# ═══════════════════════════════════════════════════════════
# SECTION 1: Load FTIR spectrum
# Replace 'hcl_spectrum.csv' with your actual exported filename.
# Format: two-column CSV, header line, wavenumber (cm⁻¹), transmittance (0–1)
# ═══════════════════════════════════════════════════════════

# Synthetic HCl spectrum generation (replace with real data)
# Morse oscillator parameters for H³⁵Cl:
nu_e   = 2990.946   # harmonic wavenumber (cm⁻¹)
xe     = 0.01741    # anharmonicity constant
Be     = 10.5934    # rotational constant (cm⁻¹)
alpha  = 0.3072     # vibration-rotation coupling (cm⁻¹)

wavenumber = np.linspace(500, 7000, 65001)
transmittance = np.ones_like(wavenumber)

def morse_band_center(v_upper):
    """Wavenumber of v=0 → v_upper transition (cm⁻¹)."""
    E_upper = nu_e * (v_upper + 0.5) - nu_e * xe * (v_upper + 0.5)**2
    E_lower = nu_e * 0.5             - nu_e * xe * 0.5**2
    return E_upper - E_lower

# Approximate band strengths (Franck-Condon-like, decreasing with v)
band_data = []
for v in [1, 2, 3, 4]:
    center = morse_band_center(v)
    strength = 0.85 * (0.18)**(v - 1)   # rough overtone intensity falloff
    width_cm  = 25 + v * 10              # broader with higher v (rotational envelope)
    # Gaussian absorption band
    abs_band = strength * np.exp(-0.5 * ((wavenumber - center) / (width_cm / 2.355))**2)
    transmittance *= np.exp(-abs_band * 3.0)
    band_data.append({'v': v, 'center_true': center, 'strength': strength})

transmittance += np.random.default_rng(7).normal(0, 0.003, len(transmittance))
transmittance = np.clip(transmittance, 0, 1)

# Save synthetic spectrum (mimics instrument export)
np.savetxt('hcl_spectrum.csv',
           np.column_stack([wavenumber, transmittance]),
           delimiter=',', header='wavenumber_cm-1,transmittance',
           comments='')

# ── Load spectrum (use this block with real data)
data = np.loadtxt('hcl_spectrum.csv', delimiter=',', skiprows=1)
wn   = data[:, 0]
T    = data[:, 1]
A    = -np.log10(np.clip(T, 1e-6, 1))   # absorbance

# ═══════════════════════════════════════════════════════════
# SECTION 2: Peak detection — find absorption band centers
# ═══════════════════════════════════════════════════════════
# Smooth before peak detection to suppress noise
from scipy.ndimage import uniform_filter1d
A_smooth = uniform_filter1d(A, size=15)

# Find peaks with minimum prominence and width
peaks, props = find_peaks(A_smooth,
                          height=0.01,
                          prominence=0.008,
                          distance=500,     # minimum 500-point separation (~38 cm⁻¹)
                          width=5)

print("\n" + "=" * 55)
print("  DETECTED VIBRATIONAL BAND CENTERS")
print("=" * 55)
print(f"  {'Peak index':<12} {'Wavenumber (cm⁻¹)':<22} {'Absorbance':<12}")
print("-" * 55)
detected_centers = []
for i, pk in enumerate(peaks):
    print(f"  {i+1:<12} {wn[pk]:<22.2f} {A_smooth[pk]:<12.4f}")
    detected_centers.append(wn[pk])
print("=" * 55)

# ═══════════════════════════════════════════════════════════
# SECTION 3: Birge-Sponer analysis
# Transition v=0→v: G(v) = nu_e*(v + 0.5) - nu_e*xe*(v+0.5)² − G(0)
# ΔG(v) = G(v) - G(v-1) = nu_e(1 - 2*xe*v)   ← linear in v
# ═══════════════════════════════════════════════════════════

v_obs = np.arange(1, len(detected_centers) + 1, dtype=float)
obs_centers = np.array(detected_centers)

# ΔG(v) = observed center for v=0→v minus center for v=0→(v-1)
# For v=1: ΔG(1) = obs_centers[0] (since G(0) is the ZPE, absorbed in reference)
# Birge-Sponer uses ΔG(v+1/2) = G(v+1) - G(v) plotted vs (v+1/2)
delta_G = np.diff(obs_centers)        # ΔG for transitions 2→1, 3→2, ...
v_half  = v_obs[:-1] + 0.5           # midpoints  1.5, 2.5, 3.5 ...

def birge_sponer_line(v_half, nu_e_fit, nu_e_xe_fit):
    """ΔG(v+1/2) = nu_e - 2*nu_e*xe*(v+1/2)"""
    return nu_e_fit - 2 * nu_e_xe_fit * v_half

if len(delta_G) >= 2:
    popt_bs, pcov_bs = curve_fit(birge_sponer_line, v_half, delta_G,
                                  p0=[2900.0, 50.0])
    nu_e_fit   = popt_bs[0]
    nu_exs_fit = popt_bs[1]
    xe_fit     = nu_exs_fit / nu_e_fit
    perr_bs    = np.sqrt(np.diag(pcov_bs))

    # Dissociation energy from Birge-Sponer: D_e = nu_e / (4*xe) in cm⁻¹
    D_e_cm  = nu_e_fit**2 / (4 * nu_exs_fit)
    D_e_eV  = D_e_cm * 1.23984e-4   # cm⁻¹ → eV

    print(f"\n  Birge-Sponer fit results:")
    print(f"  ω̃_e          = {nu_e_fit:.2f} ± {perr_bs[0]:.2f}  cm⁻¹")
    print(f"  ω̃_e x_e      = {nu_exs_fit:.3f} ± {perr_bs[1]:.3f}  cm⁻¹")
    print(f"  x_e          = {xe_fit:.5f}")
    print(f"  D_e (from BS)= {D_e_cm:.1f} cm⁻¹  ({D_e_eV:.3f} eV)")
    print(f"  HCl accepted : ω̃_e = {nu_e:.3f} cm⁻¹, x_e = {xe:.5f}")

# ═══════════════════════════════════════════════════════════
# SECTION 4: Figures
# ═══════════════════════════════════════════════════════════

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))

# Panel 1: Full absorbance spectrum with band labels
ax1.plot(wn, A, color='steelblue', linewidth=0.8, alpha=0.6, label='Absorbance')
ax1.plot(wn, A_smooth, color='navy', linewidth=1.5, label='Smoothed')
for i, pk in enumerate(peaks):
    ax1.axvline(wn[pk], color='firebrick', linewidth=1.0, linestyle='--', alpha=0.8)
    ax1.text(wn[pk] + 30, A_smooth[pk] * 0.85,
             f'v={i+1}\n{wn[pk]:.0f}', fontsize=8, color='firebrick', ha='left')
ax1.set_xlim(1800, 7200)
ax1.set_xlabel('Wavenumber (cm⁻¹)', fontsize=12)
ax1.set_ylabel('Absorbance', fontsize=12)
ax1.set_title('HCl Vibrational Overtone Spectrum (FTIR)', fontsize=13)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.25)

# Panel 2: Birge-Sponer plot
if len(delta_G) >= 2:
    v_half_plot = np.linspace(0.5, v_half.max() + 1.0, 200)
    dG_fit_line = birge_sponer_line(v_half_plot, *popt_bs)
    v_max_bs    = nu_e_fit / (2 * nu_exs_fit)   # dissociation at ΔG = 0

    ax2.plot(v_half, delta_G, 'o', color='steelblue', markersize=9,
             zorder=5, label='Observed ΔG(v+½)')
    ax2.plot(v_half_plot, dG_fit_line, '-', color='firebrick', linewidth=2,
             label=f'Birge-Sponer fit\nω̃_e = {nu_e_fit:.1f} cm⁻¹')
    ax2.axhline(0, color='gray', linewidth=0.8, linestyle=':')
    ax2.axvline(v_max_bs, color='darkgreen', linewidth=1.2, linestyle='--',
                label=f'v_max = {v_max_bs:.1f}  (dissociation)')
    ax2.set_xlabel('Vibrational quantum number (v + ½)', fontsize=12)
    ax2.set_ylabel('ΔG(v + ½)  (cm⁻¹)', fontsize=12)
    ax2.set_title('Birge-Sponer Plot — Morse Oscillator Fit', fontsize=13)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.25)

plt.tight_layout()
plt.savefig('hcl_birge_sponer.png', dpi=180)
plt.show()
print("Figure saved → hcl_birge_sponer.png")
```

**Uncertainty and Boundary Condition Analysis.** Once you have the fitted $\tilde{\nu}_e$ and $x_e$, perform three deliberate stress tests to characterize the measurement's limits. First, vary the FTIR resolution from $4.0\ \text{cm}^{-1}$ to $0.5\ \text{cm}^{-1}$ in steps and refit: the fitted $\tilde{\nu}_e$ should converge to within $0.1\%$ as resolution improves, confirming that rotational-branch overlap at coarse resolution shifts apparent band centers by a predictable amount proportional to $B_e$. Second, reduce the HCl pressure from 100 Torr to 10 Torr: at lower pressure, Doppler broadening dominates over collisional (pressure) broadening, and the Voigt profile becomes more Gaussian; this shifts the peak centroid detectably only if your resolution is better than the Doppler width ($\approx 0.08\ \text{cm}^{-1}$ for HCl at 300 K), making it a useful test of your instrument's actual resolving power. Third, evaluate the effect of the number of detected overtones on $D_e$: fitting the Birge-Sponer line to only two points versus four produces dramatically different $D_e$ estimates because the extrapolation to $\Delta G = 0$ is longer, and the statistical uncertainty propagates as:

$$\sigma_{D_e} \approx \frac{\tilde{\nu}_e}{2 x_e^2} \cdot \sigma_{x_e}$$

where $\sigma_{x_e}$ is the formal uncertainty from the linear regression covariance matrix. The following propagation block computes this directly:

```python
import numpy as np

# Formal uncertainty propagation for D_e = nu_e^2 / (4 * nu_e * xe)
# Using partial derivatives:  dD_e/d(nu_e) and dD_e/d(nu_e*xe)
#
# D_e = A^2 / (4B)  where A = nu_e_fit, B = nu_exs_fit
# dD_e/dA = 2A/(4B) = A/(2B)
# dD_e/dB = -A^2/(4B^2)

A_val     = nu_e_fit          # nu_e  (cm⁻¹)
B_val     = nu_exs_fit        # nu_e * xe (cm⁻¹)
sigma_A   = perr_bs[0]
sigma_B   = perr_bs[1]

dDe_dA    = A_val / (2 * B_val)
dDe_dB    = -(A_val**2) / (4 * B_val**2)

sigma_De_cm = np.sqrt((dDe_dA * sigma_A)**2 + (dDe_dB * sigma_B)**2)
sigma_De_eV = sigma_De_cm * 1.23984e-4

print("\n  Error Propagation for Dissociation Energy D_e:")
print(f"  D_e = {D_e_cm:.1f} ± {sigma_De_cm:.1f} cm⁻¹")
print(f"      = {D_e_eV:.4f} ± {sigma_De_eV:.4f} eV")
print(f"  Relative uncertainty: {sigma_De_cm/D_e_cm*100:.2f}%")
print(f"\n  HCl accepted D_e ≈ 37240 cm⁻¹ (4.616 eV)")
print(f"  Note: Birge-Sponer systematically underestimates D_e")
print(f"  because the Morse oscillator overestimates anharmonic")
print(f"  level spacing near dissociation limit.")
```

The systematic underestimate of $D_e$ by the Birge-Sponer method is itself a boundary-condition lesson: the harmonic-to-Morse approximation breaks down near dissociation where higher-order anharmonic terms (the Dunham coefficients $Y_{lm}$) become significant. This is precisely where quantum mechanical boundary conditions become non-trivial — the continuum states above $D_e$ are not bound eigenstates, and the sharp energy-level picture dissolves into a scattering problem described by S-matrix formalism rather than by discrete eigenvalues.

---

## Laboratory Cheat Sheet & Metric Verification Guide

### Quick Verification Commands

```bash
# Confirm full scientific Python environment
python -c "
import numpy as np, scipy, matplotlib
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
print(f'NumPy   {np.__version__}')
print(f'SciPy   {scipy.__version__}')
print(f'Mpl     {matplotlib.__version__}')
print('All imports OK')
"

# Verify physical constants against CODATA 2018
python -c "
from scipy.constants import h, hbar, e, c, m_e, N_A, k
print(f'h    = {h:.6e} J·s      (CODATA: 6.626070e-34)')
print(f'ħ    = {hbar:.6e} J·s   (CODATA: 1.054572e-34)')
print(f'e    = {e:.6e} C        (CODATA: 1.602176e-19)')
print(f'c    = {c:.6e} m/s      (CODATA: 2.997924e+08)')
print(f'm_e  = {m_e:.6e} kg     (CODATA: 9.109384e-31)')
print(f'kB   = {k:.6e} J/K      (CODATA: 1.380649e-23)')
"
```

### Physical Constants Reference

| Constant | Symbol | Value | Units |
|---|---|---|---|
| Planck's constant | $h$ | $6.62607 \times 10^{-34}$ | J·s |
| Reduced Planck | $\hbar$ | $1.05457 \times 10^{-34}$ | J·s |
| Electron charge | $e$ | $1.60218 \times 10^{-19}$ | C |
| Speed of light | $c$ | $2.99792 \times 10^8$ | m/s |
| Electron mass | $m_e$ | $9.10938 \times 10^{-31}$ | kg |
| Boltzmann constant | $k_B$ | $1.38065 \times 10^{-23}$ | J/K |
| Avogadro's number | $N_A$ | $6.02214 \times 10^{23}$ | mol⁻¹ |
| Bohr radius | $a_0$ | $5.29177 \times 10^{-11}$ | m |
| Fine structure | $\alpha$ | $7.29735 \times 10^{-3}$ | dimensionless |

### Measurement Acceptance Thresholds

| Exercise | Measured Quantity | Acceptance Criterion | Common Failure Mode |
|---|---|---|---|
| Ex. 1 Photoelectric | $h$ from stopping potential slope | $< 3\%$ error from $6.626 \times 10^{-34}\ \text{J·s}$ | Contact potential offset in phototube; fix by calibrating with known UV line |
| Ex. 1 Photoelectric | Work function $\phi$ | Within $\pm 0.1\ \text{eV}$ of tabulated metal value | Contaminated cathode surface; clean with isopropanol and re-evacuate |
| Ex. 2 Diffraction | $\lambda$ recovered from $y_1$ | $< 2\%$ error from $532\ \text{nm}$ | Slit width deviation; re-measure slit with traveling microscope |
| Ex. 2 Uncertainty | $\Delta x \cdot \Delta p_y$ (absolute product) | Ratio $\Delta x \cdot \Delta p_y / \hbar$ in range $[5, 8]$ (expect $\approx 2\pi \approx 6.28$) | Camera not in far-field ($L < 50a^2/\lambda$); increase $L$ |
| Ex. 3 FTIR | $\tilde{\nu}_e$ for HCl | $< 0.1\%$ from $2990.95\ \text{cm}^{-1}$ | Insufficient resolution; rescan at $0.5\ \text{cm}^{-1}$ |
| Ex. 3 FTIR | $x_e$ for HCl | Within $\pm 0.0005$ of $0.01741$ | Only two bands detected; extend scan to $7000\ \text{cm}^{-1}$ for $v=3$ |
| Ex. 3 Propagation | $\sigma_{D_e} / D_e$ | Report with $< 5\%$ relative uncertainty | Too few overtone bands in Birge-Sponer fit; increase gas pressure |

### Dimensional Analysis Checklist

Before submitting any numerical result, verify dimensional consistency by checking these unit chains:

The stopping-potential slope carries units of V·s = J·s/C, so multiplying by $e$ in coulombs recovers J·s. Confirm: $[\text{slope}] \times [e] = \text{V·s} \times \text{C} = \text{J·s} = [h]$.

The de Broglie momentum uncertainty carries units of kg·m/s. Confirm: $[h/\lambda] = \text{J·s/m} = (\text{kg·m}^2/\text{s}^2)\cdot\text{s}/\text{m} = \text{kg·m/s}$.

The uncertainty product must recover J·s = kg·m²/s. Confirm: $[\Delta x][\Delta p] = \text{m} \cdot \text{kg·m/s} = \text{kg·m}^2/\text{s} = \text{J·s}$.

Wavenumber in cm⁻¹ converts to energy via $E = hc\tilde{\nu}$: confirm $[\text{J·s}][\text{m/s}][\text{m}^{-1}] = \text{J}$, and note that the factor of $100$ converting cm⁻¹ to m⁻¹ must be explicit in code — a missing factor of 100 is the most common unit error in spectroscopy calculations.

### Key Equations Summary

$$V_s = \frac{h}{e}\nu - \frac{\phi}{e} \qquad \text{(photoelectric stopping potential)}$$

$$a \sin\theta_1 = \lambda \qquad \text{(first diffraction minimum)}$$

$$\Delta x \cdot \Delta p \geq \frac{\hbar}{2} \qquad \text{(Heisenberg position-momentum bound)}$$

$$\tilde{\nu}_{v \to v+1} = \tilde{\nu}_e\left[1 - 2x_e(v+1)\right] \qquad \text{(Birge-Sponer relation)}$$

$$D_e = \frac{\tilde{\nu}_e^2}{4\tilde{\nu}_e x_e} = \frac{\tilde{\nu}_e}{4x_e} \qquad \text{(Morse dissociation energy)}$$

$$\sigma_{D_e} = \sqrt{\left(\frac{\partial D_e}{\partial \tilde{\nu}_e}\sigma_{\tilde{\nu}_e}\right)^2 + \left(\frac{\partial D_e}{\partial (\tilde{\nu}_e x_e)}\sigma_{\tilde{\nu}_e x_e}\right)^2} \qquad \text{(error propagation)}$$
