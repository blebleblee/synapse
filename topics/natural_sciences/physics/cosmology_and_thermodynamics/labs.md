# Operational Verification Labs: Cosmology And Thermodynamics

## Objective & Laboratory Bench Setup

The bridge between cosmology and thermodynamics is blackbody radiation. A tungsten filament in a laboratory and the cosmic microwave background both obey Planck's law and the Stefan-Boltzmann equation, despite spanning twelve orders of magnitude in temperature. These exercises measure physical constants from that shared law, fit cosmological parameters from Type Ia supernova observations, and stress-test calorimetric methods through Monte Carlo uncertainty propagation. Each exercise moves from bench measurement through Python analysis to physical interpretation, maintaining an empirical spine throughout.

The laboratory bench requires the following instrumentation and materials. For radiation measurement: a 5 cm × 5 cm aluminum plate painted with matte high-temperature black barbecue paint (emissivity $\varepsilon \approx 0.95$), a hot plate capable of sustained 200 °C output, a Type-K thermocouple with digital readout (0.1 °C resolution), a thin-film thermopile detector (Dexter Research ST150 or equivalent, sensitivity $S \approx 15$ V/W, active area $A_{\text{det}} \approx 5.29 \times 10^{-6}$ m²), a digital multimeter with μV resolution (Keithley 2110 or Keysight 34465A), an optical bench with post mounts, and a precision ruler or caliper for distance measurement. For calorimetry: a Styrofoam coffee-cup calorimeter (two nested cups with lid), an analytical balance (0.001 g readability), a copper cylinder approximately 100 g, a boiling water bath, a mercury thermometer or RTD probe (0.1 °C resolution), and a stopwatch. For computational exercises: a Python 3.9+ environment with NumPy, SciPy, Matplotlib, and Astropy installed.

Verify the environment before beginning:

```bash
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "import scipy; print('SciPy', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib', matplotlib.__version__)"
python -c "import astropy; print('Astropy', astropy.__version__)"
```

All exercises assume ambient laboratory conditions at $T_{\text{amb}} = 293.15$ K (20 °C) unless otherwise noted. Record the actual ambient temperature at the time of measurement and substitute it in the analysis code. The thermopile detector must equilibrate to ambient temperature for at least 15 minutes before measurements begin, as its output depends on the temperature difference between its hot and cold junctions. Shield the optical path from stray infrared sources (laboratory lights, human bodies, warm electronics) using an aluminum foil baffle between the source and detector.

## Exercise 1: Empirical Observation & Measurement Protocol

### 1.1 Laboratory Blackbody Radiation

The Stefan-Boltzmann law gives the total power radiated per unit area by a body at temperature $T$:

$$j = \varepsilon \sigma \left(T^4 - T_{\text{amb}}^4\right) \quad \left[\text{W} \cdot \text{m}^{-2}\right]$$

where $\varepsilon$ is the total hemispherical emissivity (dimensionless, $0 < \varepsilon \leq 1$), $\sigma = 5.6704 \times 10^{-8}$ W·m⁻²·K⁻⁴ is the Stefan-Boltzmann constant, $T$ is the absolute temperature of the radiating surface (K), and $T_{\text{amb}}$ is the ambient temperature (K). The $T_{\text{amb}}^4$ term accounts for the radiation the surface absorbs from its surroundings. For a flat Lambertian source of area $A_s$ at distance $d$ from a detector of area $A_{\text{det}}$, the thermopile voltage is:

$$V_{\text{tp}} = S \cdot \frac{\varepsilon \sigma \left(T^4 - T_{\text{amb}}^4\right) A_s A_{\text{det}}}{\pi d^2} \quad [\text{V}]$$

where $S$ is the thermopile responsivity in V/W, and the factor $\pi d^2$ in the denominator comes from the solid-angle geometry of a Lambertian emitter (radiance $L = j/\pi$, irradiance $E = L A_s / d^2$). The dimensional analysis checks: $[\text{V}] = [\text{V} \cdot \text{W}^{-1}] \cdot [\text{W} \cdot \text{m}^{-2}] \cdot [\text{m}^2] \cdot [\text{m}^2] \cdot [\text{m}^{-2}]$, which reduces to $[\text{V}]$ as required.

The measurement protocol proceeds as follows. Mount the aluminum plate vertically on the hot plate using a stand clamp, with the black-painted face oriented toward the thermopile. Position the thermopile at a measured distance of $d = 10.0 \pm 0.2$ cm from the plate surface, centered on the plate's vertical axis. Attach the Type-K thermocouple to the center of the plate's back surface using high-temperature Kapton tape. Connect the thermopile output to the digital multimeter set to the mVDC range. Allow the entire assembly to reach thermal equilibrium with the room (15 minutes minimum).

Begin measurements at the lowest temperature setting. Set the hot plate to its lowest stable output and wait for the thermocouple reading to stabilize, which typically requires 8 to 12 minutes per temperature step. Record the plate temperature and thermopile voltage simultaneously once the reading drifts by less than 0.1 °C over two minutes. Increase the hot plate setting and repeat for plate temperatures spanning 50 °C to 200 °C in approximately 15 °C increments. At each step, record: plate temperature (°C), thermopile voltage (mV), and ambient temperature (°C). Take three readings at each temperature and average them; the standard deviation of the three readings provides an estimate of the random measurement uncertainty.

The data below represent a representative measurement run. Substitute your own values in the analysis code.

```python
"""
Exercise 1: Stefan-Boltzmann Constant from Blackbody Radiation
and CMB Spectrum Analysis
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy.constants import h, c, k as k_B, pi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# PART A: Laboratory Blackbody Measurement
# ============================================================

# --- Physical Setup Parameters ---
A_source = 2.5e-3           # Source area (m^2), 5cm x 5cm plate
emissivity = 0.95            # Matte black paint
T_ambient = 293.15           # Ambient temperature (K), 20 C

# Thermopile: Dexter Research ST150
S_thermopile = 15.0          # Sensitivity (V/W)
A_detector = 5.29e-6         # Active area (m^2), 2.3mm x 2.3mm
d_det = 0.100                # Source-to-detector distance (m)

# --- Measured Data ---
# Plate temperature (C), thermopile voltage (mV), voltage error (mV)
T_plate_C = np.array([50, 65, 80, 95, 110, 125, 140, 155, 170, 185, 200])
T_plate_K = T_plate_C + 273.15

V_tp_mV = np.array([1.14, 1.94, 2.78, 3.68, 4.85, 5.98,
                     7.45, 8.88, 10.55, 12.60, 14.42])
V_err_mV = np.array([0.02, 0.03, 0.03, 0.04, 0.05, 0.06,
                      0.07, 0.09, 0.11, 0.13, 0.14])

V_tp = V_tp_mV * 1e-3       # Convert to Volts
V_err = V_err_mV * 1e-3     # Convert to Volts

# Compute T^4 - T_amb^4
delta_T4 = T_plate_K**4 - T_ambient**4

# Linear fit: V = slope * (T^4 - T_amb^4) + intercept
def linear_model(x, slope, intercept):
    return slope * x + intercept

popt, pcov = curve_fit(linear_model, delta_T4, V_tp,
                        sigma=V_err, absolute_sigma=True)
slope, intercept = popt
slope_err = np.sqrt(pcov[0][0])
intercept_err = np.sqrt(pcov[1][1])

# Extract Stefan-Boltzmann constant
# slope = S * eps * sigma * A_s * A_det / (pi * d^2)
# => sigma = slope * pi * d^2 / (S * eps * A_s * A_det)
sigma_measured = slope * pi * d_det**2 / (
    S_thermopile * emissivity * A_source * A_detector)
sigma_err = slope_err * pi * d_det**2 / (
    S_thermopile * emissivity * A_source * A_detector)

sigma_true = 5.670374419e-8  # CODATA 2018 value

chi2 = np.sum(((V_tp - linear_model(delta_T4, *popt)) / V_err)**2)
dof = len(V_tp) - 2

print("=" * 65)
print("PART A: Stefan-Boltzmann Constant from Laboratory Blackbody")
print("=" * 65)
print(f"Slope K        = {slope:.4e} +/- {slope_err:.4e} V/K^4")
print(f"Intercept      = {intercept:.4e} +/- {intercept_err:.4e} V")
print(f"Measured sigma = {sigma_measured:.4e} +/- {sigma_err:.4e} W/(m^2 K^4)")
print(f"Known sigma    = {sigma_true:.4e} W/(m^2 K^4)")
print(f"Deviation      = {(sigma_measured - sigma_true)/sigma_true * 100:.2f}%")
print(f"Chi^2/dof      = {chi2/dof:.2f}")

# Plot: Stefan-Boltzmann verification
fig, ax = plt.subplots(1, 1, figsize=(8, 5))
ax.errorbar(delta_T4, V_tp * 1e3, yerr=V_err * 1e3,
            fmt='ro', capsize=3, markersize=6, label='Measured data', zorder=5)
ax.plot(delta_T4, linear_model(delta_T4, *popt) * 1e3, 'b--',
        label=f'Linear fit: $K$ = {slope:.2e} V/K$^4$')
ax.set_xlabel(r'$T^4 - T_{\mathrm{amb}}^4$ (K$^4$)', fontsize=13)
ax.set_ylabel(r'Thermopile voltage (mV)', fontsize=13)
ax.set_title('Stefan-Boltzmann Law Verification', fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('exercise1a_blackbody_fit.png', dpi=150)
plt.close()
print("[Saved] exercise1a_blackbody_fit.png")

# ============================================================
# PART B: CMB Spectrum — Planck Function Fit
# ============================================================

# Planck spectral radiance per unit frequency
def planck_nu(nu, T):
    """B_nu in W sr^-1 m^-2 Hz^-1
    nu: frequency (Hz), T: temperature (K)
    """
    return (2 * h * nu**3 / c**2) / (np.exp(h * nu / (k_B * T)) - 1.0)

T_cmb_true = 2.725  # K, FIRAS measurement

# Generate FIRAS-like spectral data
# FIRAS wavenumber range: 0.5 to 30 cm^-1
wavenumber = np.linspace(0.5, 30.0, 200)   # cm^-1
nu = wavenumber * 100 * c                    # Hz: wavenumber(m^-1) * c

B_cmb_true = planck_nu(nu, T_cmb_true)

# FIRAS achieved ~0.01% relative accuracy
np.random.seed(42)
noise_frac = 0.0001
B_cmb_noisy = B_cmb_true * (1 + noise_frac * np.random.randn(len(nu)))
B_cmb_err = B_cmb_true * noise_frac

# Fit Planck function to extract CMB temperature
popt_cmb, pcov_cmb = curve_fit(planck_nu, nu, B_cmb_noisy,
                                p0=[3.0], sigma=B_cmb_err, absolute_sigma=True)
T_cmb_fit = popt_cmb[0]
T_cmb_fit_err = np.sqrt(pcov_cmb[0][0])

print("\n" + "=" * 65)
print("PART B: CMB Temperature from Planck Spectrum Fit")
print("=" * 65)
print(f"Fitted T_CMB = {T_cmb_fit:.4f} +/- {T_cmb_fit_err:.4f} K")
print(f"Known T_CMB  = {T_cmb_true:.4f} K")
print(f"Deviation    = {(T_cmb_fit - T_cmb_true)/T_cmb_true * 100:.3f}%")

# Plot: CMB spectrum and multi-temperature comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].errorbar(wavenumber, B_cmb_noisy, yerr=B_cmb_err,
                 fmt='ro', markersize=2, capsize=0, label='FIRAS-like data')
axes[0].plot(wavenumber, planck_nu(nu, T_cmb_fit), 'b-',
             linewidth=2, label=f'Planck fit: T = {T_cmb_fit:.3f} K')
axes[0].set_xlabel(r'Wavenumber (cm$^{-1}$)', fontsize=12)
axes[0].set_ylabel(r'$B_\nu$ (W sr$^{-1}$ m$^{-2}$ Hz$^{-1}$)', fontsize=12)
axes[0].set_title('CMB Blackbody Spectrum', fontsize=13)
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# Compare Planck spectra across temperatures
temps = [2.725, 77.0, 195.0, 293.15, 473.15]
colors = ['red', 'orange', 'green', 'blue', 'purple']
labels = ['CMB (2.725 K)', 'LN$_2$ (77 K)', 'Dry ice (195 K)',
          'Room (293 K)', 'Hot plate (473 K)']
wn_plot = np.linspace(0.5, 3000, 2000)
nu_plot = wn_plot * 100 * c

for T_val, color, label in zip(temps, colors, labels):
    B_val = planck_nu(nu_plot, T_val)
    axes[1].plot(wn_plot, B_val, color=color, linewidth=1.5, label=label)

axes[1].set_xlabel(r'Wavenumber (cm$^{-1}$)', fontsize=12)
axes[1].set_ylabel(r'$B_\nu$ (W sr$^{-1}$ m$^{-2}$ Hz$^{-1}$)', fontsize=12)
axes[1].set_title('Planck Spectra: Lab vs Cosmic', fontsize=13)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)
axes[1].set_yscale('log')
axes[1].set_ylim(1e-20, 1e-5)
axes[1].set_xlim(0, 3000)

plt.tight_layout()
plt.savefig('exercise1b_cmb_spectrum.png', dpi=150)
plt.close()
print("[Saved] exercise1b_cmb_spectrum.png")

# ============================================================
# PART C: Dimensional Analysis Summary
# ============================================================
print("\n" + "=" * 65)
print("PART C: Dimensional Analysis")
print("=" * 65)
print("Stefan-Boltzmann law: j = eps * sigma * (T^4 - T_amb^4)")
print("  [W m^-2] = [-] * [W m^-2 K^-4] * [K^4]  =>  consistent")
print()
print("Thermopile signal:")
print("  V = S * eps * sigma * dT4 * A_s * A_det / (pi * d^2)")
print("  [V] = [V W^-1] * [W m^-2] * [m^2] * [m^2] * [m^-2]")
print("  [V] = [V]  =>  consistent")
print()
print("Planck function: B_nu = 2h nu^3 / c^2 / (exp(h nu / kT) - 1)")
print("  h = 6.626e-34 J s,  nu = Hz = s^-1,  c = 3.0e8 m/s")
print("  k_B = 1.381e-23 J/K,  T = K")
print("  B_nu units: J s * s^-3 / m^2 = W m^-2 Hz^-1 sr^-1  =>  consistent")
```

The first plot confirms the $T^4$ dependence: a linear relationship between thermopile voltage and $T^4 - T_{\text{amb}}^4$ validates the Stefan-Boltzmann law. The fitted slope yields $\sigma$ within a few percent of the CODATA value, with the dominant systematic uncertainty arising from the distance measurement (which enters as $d^2$ in the denominator) and the emissivity specification. The second plot places the 2.725 K CMB spectrum alongside laboratory-temperature blackbody curves. The CMB peaks at a wavenumber of approximately 5.5 cm⁻¹ (wavelength $\lambda_{\text{peak}} \approx 1.9$ mm), far in the microwave regime, while the 473 K hot plate peaks near 1700 cm⁻¹ (mid-infrared). Both spectra share the identical functional form of Planck's law, differing only in the single parameter $T$.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### 2.1 The Hubble Diagram from Type Ia Supernovae

Type Ia supernovae serve as standardized candles because their peak absolute magnitude is tightly distributed around $M_B \approx -19.3$ after correction for light-curve shape and host-galaxy extinction. The observed apparent magnitude $m$ at redshift $z$ encodes the luminosity distance $d_L$ through the distance modulus:

$$\mu(z) = m - M = 5 \log_{10}\left(\frac{d_L(z)}{\text{Mpc}}\right) + 25 \quad [\text{mag}]$$

where $d_L$ is the luminosity distance in megaparsecs. In a flat $\Lambda$CDM cosmology, the luminosity distance is:

$$d_L(z) = \frac{c(1+z)}{H_0} \int_0^z \frac{dz'}{E(z')} \quad [\text{Mpc}]$$

with the Hubble parameter evolution:

$$E(z) = \sqrt{\Omega_m(1+z)^3 + \Omega_\Lambda}$$

Here $H_0$ is the Hubble constant (km·s⁻¹·Mpc⁻¹), $\Omega_m$ is the matter density parameter (dimensionless), $\Omega_\Lambda$ is the dark energy density parameter, and $c = 2.9979 \times 10^5$ km/s is the speed of light. The thermodynamic connection enters through the dark energy equation of state. For a perfect fluid with energy density $\rho$ and pressure $p$, the equation of state parameter $w = p / (\rho c^2)$ governs how the energy density evolves with the scale factor $a$:

$$\rho(a) \propto a^{-3(1+w)}$$

The first law of thermodynamics applied to an adiabatically expanding universe ($dU + p\,dV = 0$) yields this relation directly. For non-relativistic matter, $w = 0$ (zero pressure) and $\rho \propto a^{-3}$, diluting with volume. For radiation, $w = 1/3$ and $\rho \propto a^{-4}$, with the extra factor from redshift. For a cosmological constant, $w = -1$ and $\rho = \text{const}$, meaning vacuum energy does not dilute as the universe expands, a thermodynamic property with no classical analogue.

The exercise generates a realistic supernova sample matching the Pantheon survey characteristics, fits both the standard $\Lambda$CDM model and the generalized $w$CDM model where $w$ is a free parameter, and plots the response curves. The parameter variation is redshift: as $z$ increases, the distance modulus responds differently depending on the cosmological parameters, producing a curve whose shape directly encodes the thermodynamic state of the cosmic fluid.

```python
"""
Exercise 2: Hubble Diagram, Cosmological Parameter Fitting,
and Dark Energy Equation of State
"""
import numpy as np
from scipy.integrate import quad
from scipy.optimize import curve_fit
from scipy.constants import c as c_si
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Speed of light in km/s
c_kms = c_si / 1e3  # 299792.458 km/s

# ============================================================
# PART A: Generate Realistic Supernova Sample
# ============================================================
np.random.seed(2024)
H0_true = 70.0        # km/s/Mpc
Om_true = 0.30
OL_true = 0.70

# Redshift distribution mimicking Pantheon: dense at low-z, sparse at high-z
z_low = np.random.uniform(0.01, 0.08, 20)
z_mid = np.random.uniform(0.08, 0.50, 25)
z_high = np.random.uniform(0.50, 1.50, 15)
z = np.sort(np.concatenate([z_low, z_mid, z_high]))

# Luminosity distance for flat LCDM
def E_z(zp, Om, OL):
    return np.sqrt(Om * (1 + zp)**3 + OL)

def d_L_single(zi, H0, Om, OL):
    integral, _ = quad(lambda zp: 1.0 / E_z(zp, Om, OL), 0, zi)
    return c_kms * (1 + zi) / H0 * integral  # Mpc

def mu_lcdm(z_arr, H0, Om, OL):
    """Distance modulus for flat LCDM."""
    return np.array([5 * np.log10(d_L_single(zi, H0, Om, OL)) + 25
                     for zi in z_arr])

# True distance moduli
mu_true = mu_lcdm(z, H0_true, Om_true, OL_true)

# Realistic photometric errors
mu_err = np.where(z < 0.05, 0.15,
         np.where(z < 0.5, 0.12, 0.15))
mu_obs = mu_true + np.random.randn(len(z)) * mu_err

print("=" * 65)
print("PART A: Generated Supernova Sample")
print("=" * 65)
print(f"N_SNe = {len(z)},  z range: {z.min():.4f} to {z.max():.4f}")
print(f"True cosmology: H0={H0_true}, Om={Om_true}, OL={OL_true}")

# ============================================================
# PART B: Fit Lambda CDM Model (H0, Om free; OL = 1 - Om)
# ============================================================

def mu_model_flat(z_arr, H0, Om):
    """Distance modulus for flat universe: OL = 1 - Om."""
    OL = 1.0 - Om
    return mu_lcdm(z_arr, H0, Om, OL)

# Initial guess
p0 = [70.0, 0.3]
popt_lcdm, pcov_lcdm = curve_fit(mu_model_flat, z, mu_obs, p0=p0,
                                  sigma=mu_err, absolute_sigma=True,
                                  bounds=([50, 0.01], [100, 0.99]))
H0_fit, Om_fit = popt_lcdm
H0_err = np.sqrt(pcov_lcdm[0][0])
Om_err = np.sqrt(pcov_lcdm[1][0])
OL_fit = 1.0 - Om_fit

chi2_lcdm = np.sum(((mu_obs - mu_model_flat(z, *popt_lcdm)) / mu_err)**2)
dof_lcdm = len(z) - 2

print("\n" + "=" * 65)
print("PART B: Flat LCDM Fit Results")
print("=" * 65)
print(f"H0     = {H0_fit:.2f} +/- {H0_err:.2f} km/s/Mpc")
print(f"Om     = {Om_fit:.3f} +/- {Om_err:.3f}")
print(f"OL     = {OL_fit:.3f}")
print(f"Chi^2/dof = {chi2_lcdm/dof_lcdm:.2f}")

# ============================================================
# PART C: Fit wCDM Model (H0, Om, w free)
# ============================================================

def E_z_w(zp, Om, OL, w):
    """Hubble parameter for flat wCDM: rho_de proportional to a^{-3(1+w)}."""
    return np.sqrt(Om * (1 + zp)**3 + OL * (1 + zp)**(3 * (1 + w)))

def d_L_w_single(zi, H0, Om, OL, w):
    integral, _ = quad(lambda zp: 1.0 / E_z_w(zp, Om, OL, w), 0, zi)
    return c_kms * (1 + zi) / H0 * integral

def mu_wcdm(z_arr, H0, Om, w):
    """Distance modulus for flat wCDM: OL = 1 - Om."""
    OL = 1.0 - Om
    return np.array([5 * np.log10(d_L_w_single(zi, H0, Om, OL, w)) + 25
                    for zi in z_arr])

p0_w = [70.0, 0.3, -1.0]
popt_w, pcov_w = curve_fit(mu_wcdm, z, mu_obs, p0=p0_w,
                           sigma=mu_err, absolute_sigma=True,
                           bounds=([50, 0.01, -2.0], [100, 0.99, 0.5]))
H0_w, Om_w, w_fit = popt_w
w_err = np.sqrt(pcov_w[2][2])
chi2_w = np.sum(((mu_obs - mu_wcdm(z, *popt_w)) / mu_err)**2)
dof_w = len(z) - 3

print("\n" + "=" * 65)
print("PART C: wCDM Fit Results")
print("=" * 65)
print(f"H0     = {H0_w:.2f} km/s/Mpc")
print(f"Om     = {Om_w:.3f}")
print(f"w      = {w_fit:.3f} +/- {w_err:.3f}")
print(f"Chi^2/dof = {chi2_w/dof_w:.2f}")

# ============================================================
# PART D: Response Curve Plotting
# ============================================================

z_fine = np.linspace(0.005, 1.5, 200)

fig, axes = plt.subplots(2, 1, figsize=(9, 10), gridspec_kw={'height_ratios': [3, 1]})

# Top panel: Hubble diagram
axes[0].errorbar(z, mu_obs, yerr=mu_err, fmt='ko', capsize=2,
                markersize=4, label='Simulated SNe Ia data', zorder=5)
axes[0].plot(z_fine, mu_model_flat(z_fine, *popt_lcdm), 'r-',
            linewidth=2, label=f'$\Lambda$CDM: $H_0$={H0_fit:.1f}, '
            f'$\Omega_m$={Om_fit:.2f}')
axes[0].plot(z_fine, mu_wcdm(z_fine, *popt_w), 'b--',
            linewidth=2, label=f'wCDM: $w$={w_fit:.2f}')
# Reference: matter-only universe for comparison
axes[0].plot(z_fine, mu_model_flat(z_fine, 70, 1.0), 'g:',
            linewidth=1, label='Matter-only ($\Omega_m=1$)', alpha=0.5)

axes[0].set_xlabel('Redshift $z$', fontsize=13)
axes[0].set_ylabel(r'Distance modulus $\mu$ (mag)', fontsize=13)
axes[0].set_title('Hubble Diagram: Type Ia Supernova Response Curve', fontsize=14)
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)
axes[0].set_xlim(0, 1.55)

# Bottom panel: residuals from LCDM fit
mu_fit_vals = mu_model_flat(z, *popt_lcdm)
residuals = mu_obs - mu_fit_vals
axes[1].errorbar(z, residuals, yerr=mu_err, fmt='ko', capsize=2,
                markersize=4, zorder=5)
axes[1].axhline(0, color='r', linewidth=1.5)
axes[1].set_xlabel('Redshift $z$', fontsize=13)
axes[1].set_ylabel(r'$\Delta\mu$ (mag)', fontsize=13)
axes[1].set_title('Residuals from $\Lambda$CDM Fit', fontsize=13)
axes[1].grid(True, alpha=0.3)
axes[1].set_xlim(0, 1.55)
axes[1].set_ylim(-0.6, 0.6)

plt.tight_layout()
plt.savefig('exercise2_hubble_diagram.png', dpi=150)
plt.close()
print("\n[Saved] exercise2_hubble_diagram.png")

# ============================================================
# PART E: Thermodynamic Interpretation
# ============================================================
print("\n" + "=" * 65)
print("PART E: Thermodynamic Interpretation")
print("=" * 65)
print(f"Fitted w = {w_fit:.3f} +/- {w_err:.3f}")
print(f"  w = -1  =>  cosmological constant (vacuum energy)")
print(f"  w = 0   =>  non-relativistic matter (dust)")
print(f"  w = 1/3 =>  radiation")
print()
print("Energy density evolution: rho(a) proportional to a^{-3(1+w)}")
a_vals = np.linspace(0.1, 1.0, 5)
print(f"  {'a':>6s}  {'rho_matter':>12s}  {'rho_radiation':>14s}  {'rho_Lambda':>12s}")
for a in a_vals:
    print(f"  {a:6.2f}  {a**(-3):12.4f}  {a**(-4):14.4f}  {1.0:12.4f}")
print()
print(f"Measured w {'is consistent with' if abs(w_fit - (-1.0)) < 2*w_err else 'differs from'} -1 (cosmological constant)")
print(f"  |w - (-1)| = {abs(w_fit + 1):.3f},  2*sigma_w = {2*w_err:.3f}")

# Uncertainty contour: Om vs w
Om_grid = np.linspace(0.15, 0.50, 50)
w_grid = np.linspace(-1.6, -0.4, 50)
chi2_grid = np.zeros((len(w_grid), len(Om_grid)))

for i, w_val in enumerate(w_grid):
    for j, Om_val in enumerate(Om_grid):
        mu_model = mu_wcdm(z, H0_w, Om_val, w_val)
        chi2_grid[i, j] = np.sum(((mu_obs - mu_model) / mu_err)**2)

fig2, ax2 = plt.subplots(1, 1, figsize=(8, 6))
ax2.contourf(Om_grid, w_grid, chi2_grid,
             levels=[chi2_w, chi2_w + 2.3, chi2_w + 6.17, chi2_w + 11.8],
             colors=['blue', 'cyan', 'yellow', 'red'], alpha=0.4)
ax2.contour(Om_grid, w_grid, chi2_grid,
            levels=[chi2_w + 2.3, chi2_w + 6.17],
            colors=['blue', 'red'], linewidths=1.5)
ax2.plot(Om_w, w_fit, 'kx', markersize=10, markeredgewidth=2, label='Best fit')
ax2.axhline(-1.0, color='white', linestyle='--', linewidth=1, alpha=0.7,
            label=r'$w = -1$ ($\Lambda$CDM)')
ax2.set_xlabel(r'$\Omega_m$', fontsize=13)
ax2.set_ylabel(r'$w$ (dark energy EoS)', fontsize=13)
ax2.set_title(r'Confidence contours: $\Omega_m$ vs $w$ '
              r'(68%, 95%, 99.7%)', fontsize=14)
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('exercise2_contours.png', dpi=150)
plt.close()
print("[Saved] exercise2_contours.png")
```

The Hubble diagram shows the distance modulus increasing with redshift, but the slope is not constant. At low redshift ($z < 0.1$), the relation is approximately linear in $\log z$, governed by the Hubble law $d_L \approx cz/H_0$. At higher redshift, the curve bends: a matter-only universe ($\Omega_m = 1$) predicts a steeper rise than the data show, because matter decelerates expansion and increases distances at fixed $z$. The dark energy component ($\Omega_\Lambda \approx 0.7$, $w \approx -1$) flattens the curve at $z > 0.5$ by accelerating the expansion, reducing the luminosity distance. The residuals from the $\Lambda$CDM fit scatter symmetrically around zero with no systematic trend, confirming that $w = -1$ is consistent with the data. The confidence contour plot shows the degeneracy between $\Omega_m$ and $w$: increasing $w$ (stiffening the dark energy fluid) can be partially compensated by decreasing $\Omega_m$, but the data constrain $w$ to the neighborhood of $-1$ at the 95% confidence level.

The thermodynamic reading is direct. The fitted $w = -1$ means the dark energy pressure is negative and equal in magnitude to its energy density: $p = -\rho c^2$. In the first law $dU + p\,dV = 0$, this gives $d(\rho c^2 V) - \rho c^2 dV = 0$, which requires $d\rho = 0$. Vacuum energy density is constant, a thermodynamic property that drives the accelerating expansion. No ordinary substance exhibits $w = -1$; the closest classical analogue is the tension in a stretched membrane, but with the sign reversed.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### 3.1 Coffee-Cup Calorimetry and the Dulong-Petit Limit

The specific heat capacity of a solid connects macroscopic thermodynamic measurement to the microscopic equipartition theorem. For a crystalline solid at temperatures well above the Debye temperature, the Dulong-Petit law predicts a molar heat capacity:

$$c_v = \frac{3R}{M} \quad \left[\text{J} \cdot \text{g}^{-1} \cdot \text{K}^{-1}\right]$$

where $R = 8.314$ J·mol⁻¹·K⁻¹ is the gas constant and $M$ is the molar mass (g·mol⁻¹). For copper, $M = 63.55$ g·mol⁻¹, giving $c_v = 0.392$ J·g⁻¹·K⁻¹. Each atom in the lattice has six degrees of freedom (three kinetic, three potential), each contributing $\frac{1}{2}k_B T$ to the average energy, for a total of $3k_B T$ per atom or $3R$ per mole. The laboratory measurement uses a coffee-cup calorimeter and exploits the principle of energy conservation.

The experimental procedure requires precise execution. Weigh the copper cylinder on the analytical balance to 0.001 g. Measure the mass of the inner Styrofoam cup. Add approximately 100 mL of distilled water using a graduated cylinder, then weigh the cup plus water to determine the water mass precisely. Record the initial water temperature $T_i$ using the RTD probe, stirring gently for 30 seconds before reading to ensure uniformity. Place the copper cylinder in the boiling water bath and hold it there for five minutes to ensure thermal equilibrium at $T_h \approx 95$ °C (slightly below 100 °C due to bath heat loss to the room). Transfer the copper quickly to the calorimeter, minimizing the time in air to reduce radiative and convective cooling. Stir continuously and monitor the temperature. Record the maximum stable temperature $T_{\text{eq}}$ reached, which is the thermal equilibrium point. Take three repeat measurements and average.

The naive energy conservation equation (ignoring the calorimeter's own heat capacity) is:

$$m_{\text{Cu}} \, c_{\text{Cu}} \, (T_h - T_{\text{eq}}) = m_w \, c_w \, (T_{\text{eq}} - T_i)$$

Solving for the specific heat of copper:

$$c_{\text{Cu}} = \frac{m_w \, c_w \, (T_{\text{eq}} - T_i)}{m_{\text{Cu}} \, (T_h - T_{\text{eq}})} \quad \left[\text{J} \cdot \text{g}^{-1} \cdot \text{K}^{-1}\right]$$

This equation neglects the heat absorbed by the Styrofoam cup, the lid, the thermometer probe, and any heat exchanged with the room. Including the calorimeter heat capacity $C_{\text{cal}}$ (in J·K⁻¹), the corrected equation becomes:

$$m_{\text{Cu}} \, c_{\text{Cu}} \, (T_h - T_{\text{eq}}) = \left(m_w \, c_w + C_{\text{cal}}\right)(T_{\text{eq}} - T_i)$$

The calorimeter heat capacity for a standard Styrofoam coffee-cup calorimeter is approximately $C_{\text{cal}} = 30 \pm 10$ J·K⁻¹, determined from the cup mass, specific heat of polystyrene ($\sim 1.3$ J·g⁻¹·K⁻¹), and the thermometer thermal mass. This boundary condition is the dominant systematic error: ignoring it biases $c_{\text{Cu}}$ low by approximately 6 to 8%.

```python
"""
Exercise 3: Calorimetry, Boundary Condition Testing,
and Monte Carlo Uncertainty Propagation
"""
import numpy as np
from scipy.constants import R as R_gas
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# PART A: Naive Calculation (ignoring calorimeter heat capacity)
# ============================================================

# Measured values with uncertainties (1-sigma)
m_Cu = 100.000          # g, copper cylinder mass
m_Cu_err = 0.001         # g, analytical balance resolution

m_water = 100.000        # g, water mass
m_water_err = 0.001      # g

T_initial = 20.0         # C, initial water temperature
T_initial_err = 0.1      # C, RTD probe resolution

T_hot = 95.0             # C, copper temperature (boiling water bath)
T_hot_err = 0.5          # C, bath thermal non-uniformity

T_eq = 25.93             # C, measured equilibrium temperature
T_eq_err = 0.1           # C, RTD resolution + thermal lag

c_water = 4.186          # J/(g K), specific heat of water at 20 C

# C_cal: calorimeter heat capacity (J/K)
# Two nested Styrofoam cups (~4g each), lid, thermometer probe
C_cal = 30.0             # J/K
C_cal_err = 10.0         # J/K (large uncertainty)

# Naive formula (no calorimeter correction)
delta_T_water = T_eq - T_initial       # C
delta_T_copper = T_hot - T_eq          # C
c_Cu_naive = (m_water * c_water * delta_T_water) / \
             (m_Cu * delta_T_copper)

# True value (literature)
c_Cu_true = 0.385        # J/(g K)
# Dulong-Petit prediction: 3R / M_Cu
M_Cu_molar = 63.55        # g/mol
c_Cu_dulong_petit = 3 * R_gas / M_Cu_molar  # J/(g K)

print("=" * 65)
print("PART A: Naive Calculation (no calorimeter correction)")
print("=" * 65)
print(f"m_Cu    = {m_Cu:.3f} +/- {m_Cu_err:.3f} g")
print(f"m_water = {m_water:.3f} +/- {m_water_err:.3f} g")
print(f"T_i     = {T_initial:.1f} +/- {T_initial_err:.1f} C")
print(f"T_h     = {T_hot:.1f} +/- {T_hot_err:.1f} C")
print(f"T_eq    = {T_eq:.2f} +/- {T_eq_err:.2f} C")
print(f"Delta T_water  = {delta_T_water:.2f} C")
print(f"Delta T_copper = {delta_T_copper:.2f} C")
print(f"\nc_Cu (naive)  = {c_Cu_naive:.4f} J/(g K)")
print(f"c_Cu (true)   = {c_Cu_true:.4f} J/(g K)")
print(f"c_Cu (Dulong-Petit) = {c_Cu_dulong_petit:.4f} J/(g K)")
print(f"Naive error   = {(c_Cu_naive - c_Cu_true)/c_Cu_true * 100:.1f}%")

# ============================================================
# PART B: Corrected Calculation (with calorimeter heat capacity)
# ============================================================

c_Cu_corrected = ((m_water * c_water + C_cal) * delta_T_water) / \
                  (m_Cu * delta_T_copper)

print("\n" + "=" * 65)
print("PART B: Corrected Calculation (with C_cal)")
print("=" * 65)
print(f"C_cal = {C_cal} +/- {C_cal_err} J/K")
print(f"c_Cu (corrected) = {c_Cu_corrected:.4f} J/(g K)")
print(f"Corrected error  = {(c_Cu_corrected - c_Cu_true)/c_Cu_true * 100:.1f}%")

# ============================================================
# PART C: Monte Carlo Uncertainty Propagation
# ============================================================
N_samples = 100000
np.random.seed(42)

# Sample each measured quantity from its distribution
m_Cu_samp = np.random.normal(m_Cu, m_Cu_err, N_samples)
m_w_samp = np.random.normal(m_water, m_water_err, N_samples)
Ti_samp = np.random.normal(T_initial, T_initial_err, N_samples)
Th_samp = np.random.normal(T_hot, T_hot_err, N_samples)
Teq_samp = np.random.normal(T_eq, T_eq_err, N_samples)
Ccal_samp = np.random.normal(C_cal, C_cal_err, N_samples)

# Naive formula samples (no C_cal)
dTw_naive = Teq_samp - Ti_samp
dTC_naive = Th_samp - Teq_samp
c_Cu_naive_samp = (m_w_samp * c_water * dTw_naive) / (m_Cu_samp * dTC_naive)

# Corrected formula samples (with C_cal)
c_Cu_corr_samp = ((m_w_samp * c_water + Ccal_samp) * dTw_naive) / \
                  (m_Cu_samp * dTC_naive)

# Statistics
c_Cu_naive_mean = np.mean(c_Cu_naive_samp)
c_Cu_naive_std = np.std(c_Cu_naive_samp)
c_Cu_corr_mean = np.mean(c_Cu_corr_samp)
c_Cu_corr_std = np.std(c_Cu_corr_samp)

# Confidence intervals
ci_naive = np.percentile(c_Cu_naive_samp, [2.5, 16, 84, 97.5])
ci_corr = np.percentile(c_Cu_corr_samp, [2.5, 16, 84, 97.5])

print("\n" + "=" * 65)
print("PART C: Monte Carlo Uncertainty Propagation (N=100000)")
print("=" * 65)
print(f"\nNaive (no C_cal):")
print(f"  c_Cu = {c_Cu_naive_mean:.4f} +/- {c_Cu_naive_std:.4f} J/(g K)")
print(f"  95% CI: [{ci_naive[0]:.4f}, {ci_naive[3]:.4f}]")
print(f"  68% CI: [{ci_naive[1]:.4f}, {ci_naive[2]:.4f}]")
print(f"\nCorrected (with C_cal):")
print(f"  c_Cu = {c_Cu_corr_mean:.4f} +/- {c_Cu_corr_std:.4f} J/(g K)")
print(f"  95% CI: [{ci_corr[0]:.4f}, {ci_corr[3]:.4f}]")
print(f"  68% CI: [{ci_corr[1]:.4f}, {ci_corr[2]:.4f}]")

# ============================================================
# PART D: Error Budget Analysis
# ============================================================
# Vary each parameter by +1 sigma, hold others fixed, measure impact
print("\n" + "=" * 65)
print("PART D: Error Budget (corrected formula)")
print("=" * 65)

def c_Cu_calc(mC, mw, Ti, Th, Te, Ccal):
    return ((mw * c_water + Ccal) * (Te - Ti)) / (mC * (Th - Te))

params = {
    'm_Cu':     (m_Cu, m_Cu_err),
    'm_water':   (m_water, m_water_err),
    'T_initial': (T_initial, T_initial_err),
    'T_hot':     (T_hot, T_hot_err),
    'T_eq':      (T_eq, T_eq_err),
    'C_cal':     (C_cal, C_cal_err),
}

c_base = c_Cu_calc(m_Cu, m_water, T_initial, T_hot, T_eq, C_cal)
print(f"{'Parameter':>12s}  {'+1 sigma':>10s}  {'dc_Cu':>10s}  {'% of total':>10s}")

# Total variance from Monte Carlo
total_var = c_Cu_corr_std**2

for name, (val, err) in params.items():
    kwargs_plus = {n: v[0] for n, v in params.items()}
    kwargs_plus[name] = val + err
    c_plus = c_Cu_calc(**kwargs_plus)
    dc = c_plus - c_base
    pct = (dc**2 / total_var) * 100
    print(f"  {name:>10s}  {val + err:10.3f}  {dc:10.5f}  {pct:8.1f}%")

# ============================================================
# PART E: Stress Test — Boundary Condition Variation
# ============================================================
print("\n" + "=" * 65)
print("PART E: Boundary Condition Stress Test")
print("=" * 65)

# Vary C_cal from 0 to 60 J/K
C_cal_range = np.linspace(0, 60, 100)
c_Cu_vs_Ccal = []
for Cc in C_cal_range:
    c_val = ((m_water * c_water + Cc) * delta_T_water) / \
            (m_Cu * delta_T_copper)
    c_Cu_vs_Ccal.append(c_val)

c_Cu_vs_Ccal = np.array(c_Cu_vs_Ccal)

# Find C_cal that gives the true c_Cu
C_cal_recovery = (c_Cu_true * m_Cu * delta_T_copper) / delta_T_water - \
                  m_water * c_water
print(f"C_cal needed to recover true c_Cu = {C_cal_recovery:.1f} J/K")
print(f"Estimated C_cal = {C_cal} +/- {C_cal_err} J/K")
print(f"Recovery within {abs(C_cal_recovery - C_cal)/C_cal_err:.1f} sigma")

# ============================================================
# PART F: Plotting
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(13, 10))

# Panel 1: Monte Carlo distributions
axes[0, 0].hist(c_Cu_naive_samp, bins=100, alpha=0.5, color='red',
                label=f'Naive: {c_Cu_naive_mean:.4f} +/- {c_Cu_naive_std:.4f}')
axes[0, 0].hist(c_Cu_corr_samp, bins=100, alpha=0.5, color='blue',
                label=f'Corrected: {c_Cu_corr_mean:.4f} +/- {c_Cu_corr_std:.4f}')
axes[0, 0].axvline(c_Cu_true, color='black', linewidth=2, linestyle='-',
                   label=f'True: {c_Cu_true:.4f}')
axes[0, 0].axvline(c_Cu_dulong_petit, color='green', linewidth=2,
                   linestyle='--', label=f'Dulong-Petit: {c_Cu_dulong_petit:.4f}')
axes[0, 0].set_xlabel(r'$c_{\mathrm{Cu}}$ (J g$^{-1}$ K$^{-1}$)', fontsize=12)
axes[0, 0].set_ylabel('Sample count', fontsize=12)
axes[0, 0].set_title('Monte Carlo Distributions', fontsize=13)
axes[0, 0].legend(fontsize=9)
axes[0, 0].grid(True, alpha=0.3)

# Panel 2: C_cal sensitivity
axes[0, 1].plot(C_cal_range, c_Cu_vs_Ccal, 'b-', linewidth=2)
axes[0, 1].axhline(c_Cu_true, color='black', linestyle='--', linewidth=1.5,
                   label=f'True $c_{{\\mathrm{{Cu}}}}$ = {c_Cu_true}')
axes[0, 1].axvline(C_cal, color='red', linestyle=':', linewidth=1.5,
                   label=f'Estimated $C_{{\\mathrm{{cal}}}}$ = {C_cal}')
axes[0, 1].axvline(C_cal + C_cal_err, color='red', linestyle=':', alpha=0.5)
axes[0, 1].axvline(C_cal - C_cal_err, color='red', linestyle=':', alpha=0.5)
axes[0, 1].axvline(0, color='green', linestyle='--', alpha=0.5,
                   label='Naive ($C_{cal}=0$)')
axes[0, 1].set_xlabel(r'$C_{\mathrm{cal}}$ (J K$^{-1}$)', fontsize=12)
axes[0, 1].set_ylabel(r'$c_{\mathrm{Cu}}$ (J g$^{-1}$ K$^{-1}$)', fontsize=12)
axes[0, 1].set_title('Boundary Condition: $C_{cal}$ Sensitivity', fontsize=13)
axes[0, 1].legend(fontsize=9)
axes[0, 1].grid(True, alpha=0.3)

# Panel 3: Error budget bar chart
err_names = list(params.keys())
err_pcts = []
for name, (val, err) in params.items():
    kwargs_plus = {n: v[0] for n, v in params.items()}
    kwargs_plus[name] = val + err
    c_plus = c_Cu_calc(**kwargs_plus)
    dc = (c_plus - c_base)
    err_pcts.append((dc**2 / total_var) * 100)

axes[1, 0].barh(err_names, err_pcts, color='steelblue', alpha=0.8)
axes[1, 0].set_xlabel(r'Variance contribution (%)', fontsize=12)
axes[1, 0].set_title('Error Budget', fontsize=13)
axes[1, 0].grid(True, alpha=0.3, axis='x')

# Panel 4: Dulong-Petit comparison
materials = ['Cu', 'Al', 'Fe', 'Pb']
M_molar = np.array([63.55, 26.98, 55.85, 207.2])  # g/mol
c_dp = 3 * R_gas / M_molar  # J/(g K)
c_exp = np.array([0.385, 0.897, 0.449, 0.129])  # experimental values

x_pos = np.arange(len(materials))
width = 0.35
axes[1, 1].bar(x_pos - width/2, c_dp, width, label='Dulong-Petit (3R/M)',
               color='steelblue', alpha=0.8)
axes[1, 1].bar(x_pos + width/2, c_exp, width, label='Experimental',
               color='coral', alpha=0.8)
axes[1, 1].set_xticks(x_pos)
axes[1, 1].set_xticklabels(materials)
axes[1, 1].set_ylabel(r'$c_v$ (J g$^{-1}$ K$^{-1}$)', fontsize=12)
axes[1, 1].set_title('Dulong-Petit Law: $c_v = 3R/M$', fontsize=13)
axes[1, 1].legend(fontsize=10)
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('exercise3_calorimetry.png', dpi=150)
plt.close()
print("\n[Saved] exercise3_calorimetry.png")
```

The naive calculation yields $c_{\text{Cu}} \approx 0.360$ J·g⁻¹·K⁻¹, which is 6.5% below the accepted value of 0.385. This systematic underestimate is the calorimeter boundary condition: the Styrofoam cup, lid, and thermometer absorb heat that the naive formula attributes solely to the water. Including $C_{\text{cal}} = 30$ J·K⁻¹ shifts the result to 0.385 J·g⁻¹·K⁻¹, recovering the true value within the Monte Carlo uncertainty. The Monte Carlo distribution broadens significantly when $C_{\text{cal}}$ is included as an uncertain parameter, because its relative uncertainty (33%) is the largest in the error budget. The error budget panel shows that $T_{\text{eq}}$ and $C_{\text{cal}}$ dominate the variance, together accounting for over 80% of the total uncertainty.

The Dulong-Petit comparison shows that copper, aluminum, iron, and lead all obey the $3R/M$ prediction to within a few percent at room temperature. This agreement is the macroscopic signature of the quantum mechanical equipartition theorem: each atom in the crystal lattice contributes $3k_B T$ of thermal energy, and dividing by the molar mass converts from per-mole to per-gram units. The connection to cosmology runs through the same statistical mechanics: the CMB photon gas obeys an analogous relation where each photon mode contributes $k_B T$ to the energy density, yielding the $T^4$ Stefan-Boltzmann law measured in Exercise 1. The calorimeter measures atomic lattice vibrations; the thermopile measures electromagnetic field modes; both are manifestations of the same thermodynamic principle operating at different energy scales.

## Laboratory Cheat Sheet & Metric Verification Guide

The following reference table consolidates the key equations, constants, and verification metrics for all three exercises. Use it to cross-check results during and after each lab session.

**Fundamental Constants**

| Symbol | Value | Units | Exercise |
|--------|-------|-------|----------|
| $\sigma$ | $5.6704 \times 10^{-8}$ | W·m⁻²·K⁻⁴ | 1 |
| $h$ | $6.6261 \times 10^{-34}$ | J·s | 1 |
| $k_B$ | $1.3807 \times 10^{-23}$ | J·K⁻¹ | 1 |
| $c$ | $2.9979 \times 10^{5}$ | km·s⁻¹ | 2 |
| $R$ | 8.314 | J·mol⁻¹·K⁻¹ | 3 |
| $T_{\text{CMB}}$ | 2.725 | K | 1 |

**Key Equations**

Stefan-Boltzmann law: $j = \varepsilon \sigma (T^4 - T_{\text{amb}}^4)$ where $j$ is radiated power per area, $\varepsilon$ is emissivity, $\sigma$ is the Stefan-Boltzmann constant, and $T$ is absolute temperature.

Thermopile signal: $V = S \varepsilon \sigma (T^4 - T_{\text{amb}}^4) A_s A_{\text{det}} / (\pi d^2)$ where $S$ is thermopile sensitivity (V/W), $A_s$ is source area, $A_{\text{det}}$ is detector area, and $d$ is source-detector distance.

Planck spectrum: $B_\nu = 2h\nu^3 / [c^2 (\exp(h\nu/k_B T) - 1)]$ where $\nu$ is frequency (Hz) and $B_\nu$ is spectral radiance (W·sr⁻¹·m⁻²·Hz⁻¹).

Luminosity distance: $d_L = c(1+z)/H_0 \int_0^z dz'/E(z')$ where $E(z) = \sqrt{\Omega_m(1+z)^3 + \Omega_\Lambda}$ for $\Lambda$CDM.

Equation of state: $\rho(a) \propto a^{-3(1+w)}$ where $a$ is the scale factor and $w = p/(\rho c^2)$ is the EoS parameter.

Calorimetry (corrected): $c_{\text{Cu}} = (m_w c_w + C_{\text{cal}})(T_{\text{eq}} - T_i) / [m_{\text{Cu}}(T_h - T_{\text{eq}})]$ where all temperatures are in °C (differences are equivalent in K).

Dulong-Petit law: $c_v = 3R/M$ where $M$ is the molar mass (g·mol⁻¹) and $c_v$ is the specific heat (J·g⁻¹·K⁻¹).

**Verification Metrics**

Exercise 1: The fitted $\sigma$ should agree with $5.6704 \times 10^{-8}$ W·m⁻²·K⁻⁴ to within 5%. The $T^4$ plot should be linear with $\chi^2/\text{dof} < 2$ and an intercept consistent with zero within $2\sigma$. The fitted $T_{\text{CMB}}$ should be $2.725 \pm 0.002$ K.

Exercise 2: The fitted $H_0$ should fall in the range 65–75 km·s⁻¹·Mpc⁻¹, $\Omega_m$ in 0.25–0.35, and $w$ within $-1.3$ to $-0.7$. The residual scatter should be consistent with the photometric errors ($\chi^2/\text{dof} \approx 1$).

Exercise 3: The naive $c_{\text{Cu}}$ should be biased low by 5–8%. The corrected value should be $0.385 \pm 0.015$ J·g⁻¹·K⁻¹. The Dulong-Petit prediction $3R/M = 0.392$ J·g⁻¹·K⁻¹ should agree with the corrected measurement within $2\sigma$.

**Common Error Sources**

Distance error in Exercise 1 enters as $d^2$, so a 2 mm error at 10 cm distance produces a 4% systematic in $\sigma$. The thermopile must reach thermal equilibrium with the room; a 1 °C offset in the cold junction produces a baseline shift comparable to the 50 °C signal. In Exercise 2, the supernova sample size and redshift distribution strongly affect the $\Omega_m$–$w$ degeneracy; a sample lacking $z > 0.5$ objects cannot constrain $w$ meaningfully. In Exercise 3, heat loss during the copper transfer from bath to calorimeter is the most difficult systematic to quantify; the 0.5 °C uncertainty in $T_h$ partially accounts for this, but a slow transfer can bias $T_h$ below the bath temperature. The calorimeter heat capacity $C_{\text{cal}}$ is the dominant boundary condition; ignoring it produces a systematic error five times larger than the statistical uncertainty from temperature measurements alone.

**Environment Verification Commands**

```bash
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "import scipy; print('SciPy', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib', matplotlib.__version__)"
python -c "import astropy; print('Astropy', astropy.__version__)"
python -c "from scipy.constants import sigma as s; print('Stefan-Boltzmann:', s)"
python -c "from scipy.constants import h; print('Planck:', h)"
python -c "from scipy.constants import R; print('Gas constant:', R)"
python -c "from astropy.cosmology import FlatLambdaCDM; cosmo=FlatLambdaCDM(70,0.3); print('dL(z=0.5):', cosmo.luminosity_distance(0.5))"
```
