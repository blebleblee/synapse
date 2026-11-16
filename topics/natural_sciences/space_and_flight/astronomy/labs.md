# Operational Verification Labs: Astronomy

## Objective & Laboratory Bench Setup

This guide is a practitioner's manual for empirical astronomy. Every exercise here produces a measurable physical result: a fitted constant, a calibrated curve, or a quantified uncertainty. The domain spans stellar photometry, Hubble flow kinematics, and Keplerian orbital mechanics — three pillars of observational astronomy where theory makes precise, testable predictions and where real data almost never matches those predictions without careful instrument calibration and error accounting.

The theoretical spine running beneath all three exercises is thin but essential. Stellar luminosity, recession velocity, and orbital period each emerge from first principles — the inverse-square law, the Doppler effect, and Newtonian gravity — but the laboratory work is not about deriving those laws. It is about measuring the constants and exponents those laws predict, confronting the gap between the textbook value and the measured value, and closing that gap through systematic calibration. That discipline is the core skill of an observational scientist.

Before writing a single line of code or pointing any instrument at the sky, verify that your Python scientific environment is complete and correctly versioned. Open a terminal and run the following checks in sequence.

```bash
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "import astropy; print('Astropy:', astropy.__version__)"
```

For the exercises in this guide you need NumPy ≥ 1.24, SciPy ≥ 1.10, Matplotlib ≥ 3.7, and Astropy ≥ 5.3. If any package is absent, install the full scientific stack with:

```bash
pip install numpy scipy matplotlib astropy
```

The physical bench for field-adjacent work consists of a calibrated photometer or digital single-lens reflex camera with a known spectral response curve, a refracting or reflecting telescope with an aperture no smaller than 70 mm for meaningful stellar photometry, a GPS receiver for accurate sidereal time, and a stable laptop running the Python environment. For the spectroscopic component of Exercise 1, a low-resolution star spectroscope (e.g., a Star Analyzer 100 or equivalent diffraction grating) mounted at the focuser eyepiece port will give you measurable hydrogen Balmer absorption lines from bright A-type stars without requiring a research-grade spectrograph. If full field deployment is not available, all three exercises include synthetic dataset generation code that faithfully replicates the statistical structure of real observational data, so the numerical and calibration work proceeds identically.

---

## Exercise 1: Empirical Observation & Measurement Protocol

### Stellar Photometry and the Inverse-Square Law Verification

The inverse-square law states that the apparent flux $F$ received from a source of intrinsic luminosity $L$ at distance $d$ obeys:

$$F = \frac{L}{4\pi d^2}$$

This is not an approximation. It is an exact geometric consequence of energy conservation in three-dimensional isotropic space. What makes it a laboratory target is that if you observe a set of stars whose distances are known from parallax measurements — the Hipparcos and Gaia catalogs provide these at sub-milliarcsecond precision — you can plot $\log F$ against $\log d$ and recover a slope of exactly $-2$. Any deviation from $-2$ indicates either systematic photometric error, interstellar extinction, or catalog contamination from unresolved binaries. Measuring that deviation and diagnosing its source is the work of this exercise.

**Instrument Setup and Aperture Photometry Procedure**

If you are working at a physical telescope, begin by collimating the optics and allowing 20 minutes of thermal equilibration before any photometric measurement. Atmospheric seeing degrades aperture photometry, so choose nights with good transparency (limiting naked-eye magnitude ≥ 5.5) and avoid observations within 30° of the horizon where differential refraction introduces chromatic flux errors. Mount your DSLR at prime focus or use a CCD photometer at the Cassegrain port. Set ISO to 400 to minimize read noise while keeping the dynamic range sufficient for stars between magnitude 2 and 8. Exposure time must be chosen so that your brightest target star peaks at no more than 70% of the detector's saturation level — typically 1 to 4 seconds for a 150 mm aperture on a magnitude-3 star under good seeing.

Take a minimum of 10 frames per target field. For each frame, record the background sky value in an annulus between 15 and 25 pixels from the stellar centroid, subtract the median sky background, and sum the signal within a circular aperture of radius 8 pixels (adjusting for your plate scale). This aperture-minus-sky procedure gives you the instrumental flux in ADU. Convert to physical flux using your detector's known gain (electrons per ADU) and a photometric zero-point derived from at least three standard stars with published Johnson-V magnitudes from the Landolt catalog.

**Generating and Analyzing the Dataset**

Whether using real photometric data or the synthetic set below, the analysis pipeline is identical. The following script uses Astropy to query the Hipparcos catalog for a volume-limited sample of nearby main-sequence stars, constructs the inverse-square diagnostic, fits the power-law exponent, and reports the residual.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.io import ascii

# -------------------------------------------------------
# Step 1: Generate a physically realistic synthetic catalog
# representing Hipparcos parallax + Hipparcos Hp-band photometry
# for 120 FGK main-sequence stars within 100 pc.
# -------------------------------------------------------
rng = np.random.default_rng(seed=42)

n_stars = 120

# Distances drawn from a uniform volume distribution (n ∝ d^2 dΩ dd)
# within 15 to 95 pc, as the Hipparcos catalog thins beyond ~100 pc
d_true_pc = np.cbrt(rng.uniform(15**3, 95**3, n_stars))  # volume-uniform draw

# Assign spectral-type absolute magnitudes M_V for FGK dwarfs:
# F5V ~ 3.5, G2V ~ 4.8, K0V ~ 5.9 — draw uniformly across the range
M_V_true = rng.uniform(3.5, 6.5, n_stars)

# Compute true apparent magnitude: m = M + 5*log10(d/10 pc)
m_V_true = M_V_true + 5.0 * np.log10(d_true_pc / 10.0)

# Add realistic photometric measurement noise: sigma ~ 0.015 mag for
# bright stars with a CCD photometer, increasing to 0.04 mag near m=8
sigma_phot = 0.015 + 0.003 * (m_V_true - 4.0)
m_V_obs = m_V_true + rng.normal(0, sigma_phot, n_stars)

# Add Hipparcos-class parallax noise: sigma_pi ~ 1.0 mas
pi_true_mas = 1000.0 / d_true_pc          # parallax in milliarcseconds
sigma_pi = 1.0 * np.ones(n_stars)         # 1 mas Hipparcos formal error
pi_obs_mas = pi_true_mas + rng.normal(0, sigma_pi, n_stars)

# Compute Lutz-Kelker-biased distance from observed parallax
# (use only stars where pi_obs > 3*sigma_pi to avoid negative parallax)
mask = pi_obs_mas > 3.0 * sigma_pi
d_obs_pc = 1000.0 / pi_obs_mas[mask]
m_obs = m_V_obs[mask]
n_good = mask.sum()
print(f"Stars passing 3-sigma parallax cut: {n_good} of {n_stars}")

# -------------------------------------------------------
# Step 2: Convert apparent magnitude to flux ratio
# Vega-system: F / F_Vega = 10^(-m/2.5)
# F_Vega in V-band = 3.63e-9 erg/cm^2/s/Angstrom (Bessell 1998)
# We work with the dimensionless flux ratio for the power-law fit.
# -------------------------------------------------------
F_ratio = 10.0 ** (-m_obs / 2.5)

# -------------------------------------------------------
# Step 3: Log-log linear regression to recover the power-law exponent
# log(F) = alpha * log(d) + const
# Theoretical prediction: alpha = -2.0
# -------------------------------------------------------
log_d = np.log10(d_obs_pc)
log_F = np.log10(F_ratio)

slope, intercept, r_value, p_value, std_err = linregress(log_d, log_F)

print(f"\nInverse-Square Law Fit Results")
print(f"  Fitted exponent alpha     : {slope:.4f} ± {std_err:.4f}")
print(f"  Theoretical prediction    : -2.0000")
print(f"  Deviation from theory     : {slope - (-2.0):.4f} ({abs(slope-(-2.0))/std_err:.2f} sigma)")
print(f"  R^2                       : {r_value**2:.5f}")
print(f"  p-value                   : {p_value:.2e}")

# -------------------------------------------------------
# Step 4: Compute absolute magnitude residuals
# M_recovered = m - 5*log10(d_obs/10)
# Compare to the true M_V assigned during generation
# -------------------------------------------------------
M_recovered = m_obs - 5.0 * np.log10(d_obs_pc / 10.0)
M_true_masked = M_V_true[mask]
residuals = M_recovered - M_true_masked
rms_residual = np.sqrt(np.mean(residuals**2))
print(f"\nAbsolute Magnitude Recovery")
print(f"  RMS residual in M_V       : {rms_residual:.4f} mag")
print(f"  Mean bias (M_rec - M_true): {np.mean(residuals):.4f} mag  (Lutz-Kelker bias if negative)")

# -------------------------------------------------------
# Step 5: Diagnostic plots
# -------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Exercise 1 — Inverse-Square Law Verification via Stellar Photometry", fontsize=13)

# Panel A: log F vs log d with fitted line
ax = axes[0]
d_fit = np.linspace(log_d.min(), log_d.max(), 200)
ax.scatter(log_d, log_F, s=14, alpha=0.6, color='steelblue', label='Synthetic catalog')
ax.plot(d_fit, slope * d_fit + intercept, 'r-', lw=1.8, label=f'Fit: α={slope:.3f}±{std_err:.3f}')
ax.plot(d_fit, -2.0 * d_fit + intercept, 'k--', lw=1.2, label='Theory: α=−2.000')
ax.set_xlabel('log₁₀(d / pc)')
ax.set_ylabel('log₁₀(F / F_Vega)')
ax.set_title('Power-Law Flux–Distance Fit')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel B: Residuals in M_V vs distance
ax = axes[1]
ax.scatter(d_obs_pc, residuals, s=14, alpha=0.6, color='darkorange')
ax.axhline(0, color='black', lw=1.0, ls='--')
ax.axhline(np.mean(residuals), color='red', lw=1.2, ls='-', label=f'Mean bias: {np.mean(residuals):.3f} mag')
ax.set_xlabel('Distance (pc)')
ax.set_ylabel('M_V(recovered) − M_V(true)  (mag)')
ax.set_title('Absolute Magnitude Residuals')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel C: Histogram of residuals with Gaussian fit
ax = axes[2]
from scipy.stats import norm
ax.hist(residuals, bins=20, color='mediumpurple', alpha=0.7, density=True, label='Residuals')
x_hist = np.linspace(residuals.min(), residuals.max(), 200)
mu_fit, std_fit = norm.fit(residuals)
ax.plot(x_hist, norm.pdf(x_hist, mu_fit, std_fit), 'r-', lw=2.0,
        label=f'N(μ={mu_fit:.3f}, σ={std_fit:.3f})')
ax.set_xlabel('ΔM_V (mag)')
ax.set_ylabel('Probability Density')
ax.set_title('Residual Distribution')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('ex1_inverse_square_verification.png', dpi=150, bbox_inches='tight')
plt.show()
print("\nFigure saved: ex1_inverse_square_verification.png")
```

**Interpreting the Output**

A correctly functioning pipeline will return a fitted exponent within approximately 0.03 of the theoretical $-2.000$, with the deviation no larger than 2 sigma. The Lutz-Kelker bias — a systematic underestimate of distance caused by the parallax noise floor preferentially scattering nearby stars outward and distant stars inward — will appear as a small negative mean in the absolute magnitude residuals panel: recovered $M_V$ will be slightly too faint relative to true $M_V$ for the most distant stars in the sample. This is a real, historically important systematic in astrometry that the Gaia mission quantified and corrected at the microarcsecond level. Seeing it emerge naturally from a 1 mas noise floor in your synthetic data is exactly the kind of physical intuition that separates a careful astrometrist from someone who merely runs a pipeline.

If your fitted exponent deviates from $-2$ by more than $3\sigma$, the most likely culprits are unresolved binary contamination (binaries are intrinsically more luminous than single stars of the same color, making them appear closer than they are) and uncorrected interstellar extinction (dust reddens and dims starlight in a wavelength-dependent way that the inverse-square law does not account for). Both effects push the fitted slope toward zero — the flux falls off less steeply with distance than $d^{-2}$ because intrinsic over-luminosity and extinction partially cancel each other. Diagnosing which effect dominates requires a color-excess measurement, which is the subject of Exercise 2.

---

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Hubble Flow Kinematics and Recession Velocity Calibration

The Hubble-Lemaître law relates the recession velocity $v$ of a galaxy to its distance $d$ through the Hubble constant $H_0$:

$$v = H_0 \cdot d$$

This is the foundational kinematic relationship of observational cosmology, and measuring $H_0$ from a local galaxy sample is one of the most consequential empirical acts in modern physics — the "Hubble tension" between the local distance-ladder value (~73 km/s/Mpc) and the CMB-derived value (~67 km/s/Mpc) is currently among the most significant unresolved discrepancies in the Standard Model of cosmology. In this exercise you will build a complete Hubble diagram from a synthetic galaxy sample that replicates the statistical properties of the Caltech Faint Galaxy Redshift Survey and the original Hubble (1929) dataset, fit $H_0$ using three different estimators, and perform a systematic calibration study varying the assumed distance indicator to map how $H_0$ responds to its calibration zero-point.

**Physical Setup and the Distance Ladder**

Measuring galaxy recession velocities is straightforward: a spectrograph disperses galaxy light, you identify the redshifted H$\alpha$ emission line at $\lambda_{\rm obs}$ relative to its rest wavelength $\lambda_0 = 6562.8$ Å, and the non-relativistic Doppler formula gives:

$$v = c \cdot z = c \cdot \frac{\lambda_{\rm obs} - \lambda_0}{\lambda_0}$$

for recession velocities $v \ll c$, which holds for all galaxies within ~200 Mpc where peculiar velocity noise does not overwhelm the Hubble flow. Measuring distances is the hard part. For this exercise we use Type Ia supernovae (SNe Ia) as standardizable candles — their peak absolute magnitudes cluster around $M_B \approx -19.3$ mag after the Phillips relation light-curve width correction — and Cepheid variable stars to calibrate the SN Ia zero-point. The calibration zero-point is the lever arm: shifting it by 0.1 mag shifts the inferred $H_0$ by approximately 5%.

**Parameter Variation Protocol**

The key experimental parameter to vary is the assumed SN Ia absolute magnitude $M_B^{\rm cal}$, which we vary from $-19.0$ to $-19.6$ in steps of 0.05 mag, covering the full range of published calibrations from the HST Key Project through the SH0ES collaboration. For each assumed $M_B^{\rm cal}$, we recompute all distance moduli, re-fit the Hubble diagram, and record $H_0$. The resulting $H_0$ versus $M_B^{\rm cal}$ response curve is the calibration sensitivity map of the entire measurement.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------------------
# Physical and cosmological constants
# -------------------------------------------------------
c_kms = 2.99792458e5    # speed of light in km/s
H0_true = 73.0          # injected true H0 in km/s/Mpc (SH0ES 2022 value)
M_B_true = -19.253      # true SN Ia absolute magnitude (Riess+2022)

# -------------------------------------------------------
# Step 1: Generate synthetic galaxy redshift survey
# mimicking the Caltech survey footprint: 180 field galaxies
# in the Local Supercluster and beyond (5–250 Mpc).
# -------------------------------------------------------
rng = np.random.default_rng(seed=137)
n_gal = 180

# True distances: volume-uniform draw in comoving space, 5–250 Mpc
d_true_Mpc = np.cbrt(rng.uniform(5.0**3, 250.0**3, n_gal))

# True recession velocities from Hubble flow + peculiar velocity noise
# Peculiar velocities: sigma_pec ~ 300 km/s (Local Supercluster virial motions)
v_peculiar = rng.normal(0, 300.0, n_gal)
v_hubble = H0_true * d_true_Mpc
v_obs = v_hubble + v_peculiar  # observed recession velocity in km/s

# Compute observed redshift
z_obs = v_obs / c_kms

# -------------------------------------------------------
# Step 2: Assign SN Ia apparent magnitudes with realistic scatter
# Distance modulus: mu = 5*log10(d/10 pc) = 5*log10(d_Mpc * 1e6 / 10)
#                      = 5*log10(d_Mpc) + 25
# Apparent magnitude: m_B = M_B_true + mu
# Scatter: intrinsic SN Ia sigma ~ 0.15 mag after Phillips correction,
#          plus photometric noise sigma ~ 0.05 mag
# -------------------------------------------------------
mu_true = 5.0 * np.log10(d_true_Mpc) + 25.0
sigma_intrinsic = 0.15
sigma_phot = 0.05
sigma_total = np.sqrt(sigma_intrinsic**2 + sigma_phot**2)
m_B_obs = M_B_true + mu_true + rng.normal(0, sigma_total, n_gal)

# -------------------------------------------------------
# Step 3: Calibration sweep — vary M_B_cal from -19.0 to -19.6
# and refit H0 for each assumed calibration.
# -------------------------------------------------------
M_B_cal_grid = np.arange(-19.00, -19.61, -0.05)   # 13 calibration points
H0_fitted = np.zeros(len(M_B_cal_grid))
H0_stderr = np.zeros(len(M_B_cal_grid))

for i, M_cal in enumerate(M_B_cal_grid):
    # Recover distance modulus for each galaxy under this calibration
    mu_recovered = m_B_obs - M_cal
    # Convert distance modulus to distance: d = 10^((mu - 25)/5 + 1) Mpc
    d_recovered_Mpc = 10.0 ** ((mu_recovered - 25.0) / 5.0)

    # Fit Hubble diagram: v = H0 * d  (forced through origin)
    # Weighted least squares: weight by inverse variance of v
    # sigma_v from mu uncertainty: sigma_v ~ v * ln(10)/5 * sigma_mu
    sigma_mu_per_star = sigma_total * np.ones(n_gal)
    sigma_v = v_obs * (np.log(10) / 5.0) * sigma_mu_per_star
    sigma_v = np.clip(sigma_v, 50.0, None)  # floor at 50 km/s

    weights = 1.0 / sigma_v**2

    # Weighted linear regression through origin: H0 = sum(w*v*d) / sum(w*d^2)
    H0_wls = np.sum(weights * v_obs * d_recovered_Mpc) / np.sum(weights * d_recovered_Mpc**2)
    # Standard error of the WLS estimator
    H0_se = np.sqrt(1.0 / np.sum(weights * d_recovered_Mpc**2))

    H0_fitted[i] = H0_wls
    H0_stderr[i] = H0_se

# -------------------------------------------------------
# Step 4: Fit the calibration sensitivity: dH0/dM_cal
# This is the linear response coefficient of H0 to zero-point shift
# -------------------------------------------------------
slope_cal, intercept_cal, r_cal, _, se_cal = linregress(M_B_cal_grid, H0_fitted)
print("Hubble Constant Calibration Sensitivity Analysis")
print(f"  dH0/dM_cal               : {slope_cal:.2f} ± {se_cal:.2f} (km/s/Mpc) / mag")
print(f"  H0 at M_cal = -19.253    : {slope_cal*(-19.253) + intercept_cal:.2f} km/s/Mpc")
print(f"  H0 at M_cal = -19.000    : {slope_cal*(-19.000) + intercept_cal:.2f} km/s/Mpc")
print(f"  H0 at M_cal = -19.600    : {slope_cal*(-19.600) + intercept_cal:.2f} km/s/Mpc")
print(f"  R^2 of linear sensitivity: {r_cal**2:.5f}")

# -------------------------------------------------------
# Step 5: Full Hubble diagram at the reference calibration M_B_true
# with three estimators: OLS, WLS, and inverse-variance weighted mean
# -------------------------------------------------------
mu_ref = m_B_obs - M_B_true
d_ref_Mpc = 10.0 ** ((mu_ref - 25.0) / 5.0)

# OLS (unweighted): slope-through-origin
H0_ols = np.sum(v_obs * d_ref_Mpc) / np.sum(d_ref_Mpc**2)

# WLS: as computed above at the reference calibration
H0_wls_ref = H0_fitted[np.argmin(np.abs(M_B_cal_grid - M_B_true))]

# Inverse-variance weighted mean of v/d ratios
H_ratios = v_obs / d_ref_Mpc
sigma_H = H_ratios * np.sqrt((300.0/v_obs)**2 + (np.log(10)/5.0 * sigma_total)**2)
sigma_H = np.clip(sigma_H, 1.0, None)
w_iv = 1.0 / sigma_H**2
H0_ivw = np.sum(w_iv * H_ratios) / np.sum(w_iv)
H0_ivw_err = np.sqrt(1.0 / np.sum(w_iv))

print(f"\nHubble Constant Estimators at M_B_cal = {M_B_true}")
print(f"  OLS (unweighted)         : H0 = {H0_ols:.2f} km/s/Mpc")
print(f"  WLS (sigma_v weighted)   : H0 = {H0_wls_ref:.2f} km/s/Mpc")
print(f"  IVW (H_i = v_i/d_i)     : H0 = {H0_ivw:.2f} ± {H0_ivw_err:.2f} km/s/Mpc")
print(f"  Injected true H0         : {H0_true:.2f} km/s/Mpc")

# -------------------------------------------------------
# Step 6: Plots
# -------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(17, 5))
fig.suptitle("Exercise 2 — Hubble Flow Kinematics and H₀ Calibration", fontsize=13)

# Panel A: Hubble diagram
ax = axes[0]
ax.scatter(d_ref_Mpc, v_obs, s=12, alpha=0.5, color='steelblue', label='Synthetic galaxies')
d_line = np.linspace(0, 260, 300)
ax.plot(d_line, H0_true * d_line, 'k--', lw=1.5, label=f'True H₀={H0_true}')
ax.plot(d_line, H0_wls_ref * d_line, 'r-', lw=1.8, label=f'WLS fit H₀={H0_wls_ref:.1f}')
ax.set_xlabel('Distance (Mpc)')
ax.set_ylabel('Recession Velocity (km/s)')
ax.set_title('Hubble Diagram')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
ax.set_xlim(0, 260)
ax.set_ylim(-2000, 22000)

# Panel B: H0 vs calibration zero-point (response curve)
ax = axes[1]
M_cal_fine = np.linspace(-19.65, -18.95, 200)
ax.errorbar(M_B_cal_grid, H0_fitted, yerr=2*H0_stderr, fmt='o', color='darkorange',
            ms=5, capsize=3, label='H₀ fit (±2σ)')
ax.plot(M_cal_fine, slope_cal * M_cal_fine + intercept_cal, 'r-', lw=1.5,
        label=f'Sensitivity: {slope_cal:.1f} km/s/Mpc/mag')
ax.axvline(M_B_true, color='black', ls='--', lw=1.0, label=f'True M_B={M_B_true}')
ax.axhline(H0_true, color='gray', ls=':', lw=1.0, label=f'True H₀={H0_true}')
ax.axhline(67.4, color='purple', ls=':', lw=1.0, label='Planck H₀=67.4')
ax.set_xlabel('Assumed SN Ia M_B calibration (mag)')
ax.set_ylabel('Fitted H₀ (km/s/Mpc)')
ax.set_title('H₀ Calibration Response Curve')
ax.legend(fontsize=7)
ax.grid(alpha=0.3)

# Panel C: Residuals from Hubble flow — peculiar velocity map
v_hubble_recovered = H0_wls_ref * d_ref_Mpc
v_pec_recovered = v_obs - v_hubble_recovered
ax = axes[2]
ax.scatter(d_ref_Mpc, v_pec_recovered, s=12, alpha=0.5, color='mediumpurple')
ax.axhline(0, color='black', lw=1.0, ls='--')
ax.axhline(np.std(v_pec_recovered), color='red', ls=':', lw=1.0,
           label=f'σ_pec = {np.std(v_pec_recovered):.0f} km/s')
ax.axhline(-np.std(v_pec_recovered), color='red', ls=':', lw=1.0)
ax.set_xlabel('Distance (Mpc)')
ax.set_ylabel('Peculiar Velocity (km/s)')
ax.set_title('Peculiar Velocity Residuals')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('ex2_hubble_calibration.png', dpi=150, bbox_inches='tight')
plt.show()
print("\nFigure saved: ex2_hubble_calibration.png")
```

**Reading the Calibration Response Curve**

The slope $dH_0/dM_{\rm cal}$ that emerges from Panel B — typically around $-23$ to $-26$ (km/s/Mpc) per magnitude — is the single most important diagnostic number in this exercise. It tells you that a 0.25 mag shift in the SN Ia zero-point (the full spread of published Cepheid-based calibrations in the literature as of 2024) is sufficient to shift $H_0$ by approximately 6 km/s/Mpc, which is precisely the size of the Hubble tension. This is not a numerical coincidence. It is the core reason the Hubble tension has proven so resistant to resolution: the two independently measured values of $H_0$ sit exactly within the systematic uncertainty envelope of the distance ladder calibration. Any experimentalist who proposes to measure $H_0$ to 1% precision must therefore demonstrate control of the SN Ia zero-point to better than 0.04 mag — a calibration requirement that places extraordinary demands on photometric stability, filter characterization, and cross-survey color transformations.

The peculiar velocity residual panel provides an independent check on the sample completeness. If the recovered peculiar velocity dispersion $\sigma_{\rm pec}$ is significantly larger than 400 km/s, the sample is likely contaminated by cluster members whose virial motions are not part of the smooth Hubble flow. If it is significantly smaller than 150 km/s, the pipeline has over-smoothed the data or the peculiar velocity noise was not correctly propagated.

---

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### Keplerian Orbital Mechanics: Period–Semimajor Axis Verification and Monte Carlo Error Propagation

Kepler's third law, derived from Newtonian gravity, states that the square of an orbital period $T$ is proportional to the cube of the semimajor axis $a$:

$$T^2 = \frac{4\pi^2}{G(M_1 + M_2)} a^3$$

For a planetary system where $M_2 \ll M_1$ (a good approximation for the Sun–planet system where the Sun contains 99.86% of the total mass), this reduces to $T^2 \propto a^3$ with a constant that depends only on the solar mass and $G$. Measuring that constant from the observed periods and semimajor axes of the Solar System planets, then inverting it to recover $G \cdot M_\odot$, is an exercise in precision measurements that the boundary condition stress test here turns into a full uncertainty decomposition.

The boundary conditions being tested are: What happens when you include Mercury — whose orbit is dominated by relativistic precession, not Newtonian dynamics — in the sample? What happens when you include Pluto and other Trans-Neptunian Objects whose poorly constrained orbital elements introduce large formal uncertainties? And what happens when you inject correlated systematic errors mimicking the kind of timing biases that afflict ground-based transit timing photometry? Each boundary represents a failure mode that a real astrometrist must recognize and exclude.

**Monte Carlo Error Propagation**

Uncertainty in $G M_\odot$ propagates from two independently measured quantities: the orbital period $T$ and the semimajor axis $a$. For uncorrelated Gaussian errors, the standard propagation formula gives:

$$\frac{\sigma_{GM_\odot}}{GM_\odot} = \sqrt{\left(\frac{2\sigma_T}{T}\right)^2 + \left(\frac{3\sigma_a}{a}\right)^2}$$

But real measurement errors are not always uncorrelated or Gaussian — transit timing variations, gravitational perturbations from Jupiter, and observational cadence gaps all introduce non-Gaussian tails. The Monte Carlo approach propagates the full error distribution by drawing 100,000 samples from the actual error distributions of $T$ and $a$, computing $GM_\odot$ for each sample, and characterizing the resulting posterior. The difference between the propagated Gaussian uncertainty and the Monte Carlo result is a direct measure of non-linearity and distributional non-Gaussianity in the measurement chain.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress, chi2, norm
from scipy.optimize import curve_fit

# -------------------------------------------------------
# Physical constants
# -------------------------------------------------------
G_SI   = 6.674e-11      # m^3 kg^-1 s^-2
M_sun  = 1.989e30       # kg
AU_m   = 1.496e11       # meters per AU
yr_s   = 3.156e7        # seconds per year
GM_sun_true = G_SI * M_sun  # 1.327e20 m^3/s^2

# -------------------------------------------------------
# Step 1: Solar System planetary orbital data
# Source: JPL Horizons ephemeris (2024), all values in AU and years
# Format: (name, a_AU, T_yr, sigma_a_AU, sigma_T_yr, include_stress)
# sigma values represent realistic observational uncertainties, NOT
# the ultra-precise ephemeris errors — scaled to what a ground-based
# observer could achieve over a decade of observation.
# include_stress: True = include in boundary-condition stress set
# -------------------------------------------------------
planets = [
    # name         a_AU       T_yr       sig_a     sig_T     stress
    ("Mercury",    0.38710,   0.24085,   0.0005,   0.0003,   True),
    ("Venus",      0.72333,   0.61520,   0.0003,   0.0002,   False),
    ("Earth",      1.00000,   1.00000,   0.0001,   0.0001,   False),
    ("Mars",       1.52366,   1.88085,   0.0005,   0.0004,   False),
    ("Jupiter",    5.20336,   11.8626,   0.0020,   0.0050,   False),
    ("Saturn",     9.53707,   29.4475,   0.0040,   0.0100,   False),
    ("Uranus",     19.1913,   84.0168,   0.0100,   0.0200,   False),
    ("Neptune",    30.0690,   164.793,   0.0200,   0.0500,   False),
    # Stress boundary conditions:
    ("Pluto",      39.4821,   248.590,   0.5000,   2.0000,   True),   # large uncertainty
    ("Eris",       67.8700,   557.000,   3.0000,   15.000,   True),   # very poorly constrained
]

names   = [p[0] for p in planets]
a_AU    = np.array([p[1] for p in planets])
T_yr    = np.array([p[2] for p in planets])
sig_a   = np.array([p[3] for p in planets])
sig_T   = np.array([p[4] for p in planets])
is_stress = np.array([p[5] for p in planets], dtype=bool)

# -------------------------------------------------------
# Step 2: Convert to SI units for GM_sun recovery
# a in meters, T in seconds
# -------------------------------------------------------
a_m   = a_AU * AU_m
T_s   = T_yr * yr_s
sig_a_m = sig_a * AU_m
sig_T_s = sig_T * yr_s

# Kepler III: GM_sun = 4*pi^2 * a^3 / T^2 for each planet
GM_per_planet = 4.0 * np.pi**2 * a_m**3 / T_s**2

# Gaussian uncertainty propagation
sigma_GM_gauss = GM_per_planet * np.sqrt((3.0*sig_a_m/a_m)**2 + (2.0*sig_T_s/T_s)**2)

# -------------------------------------------------------
# Step 3: Identify clean sample (no stress objects)
# -------------------------------------------------------
clean = ~is_stress
print("Kepler III GM_sun Recovery — Planet-by-Planet")
print(f"{'Planet':<10} {'a (AU)':<10} {'T (yr)':<10} {'GM_sun (1e20)':<16} {'sig (1e18)':<14} {'Stress?'}")
print("-"*72)
for i, name in enumerate(names):
    stress_flag = "YES" if is_stress[i] else ""
    print(f"{name:<10} {a_AU[i]:<10.5f} {T_yr[i]:<10.5f} "
          f"{GM_per_planet[i]/1e20:<16.6f} {sigma_GM_gauss[i]/1e18:<14.4f} {stress_flag}")

# Weighted mean GM_sun from clean sample
w_clean = 1.0 / sigma_GM_gauss[clean]**2
GM_wmean_clean = np.sum(w_clean * GM_per_planet[clean]) / np.sum(w_clean)
GM_wmean_err   = np.sqrt(1.0 / np.sum(w_clean))

# Weighted mean including all stress objects
w_all = 1.0 / sigma_GM_gauss**2
GM_wmean_all = np.sum(w_all * GM_per_planet) / np.sum(w_all)
GM_wmean_all_err = np.sqrt(1.0 / np.sum(w_all))

print(f"\nGM_sun Recovery Summary")
print(f"  True GM_sun              : {GM_sun_true:.6e} m³/s²")
print(f"  Clean sample (n={clean.sum()})     : {GM_wmean_clean:.6e} ± {GM_wmean_err:.2e} m³/s²")
print(f"  Deviation (clean)        : {(GM_wmean_clean - GM_sun_true)/GM_wmean_err:.3f} sigma")
print(f"  Full sample (n={len(names)})    : {GM_wmean_all:.6e} ± {GM_wmean_all_err:.2e} m³/s²")
print(f"  Deviation (full)         : {(GM_wmean_all - GM_sun_true)/GM_wmean_all_err:.3f} sigma")

# -------------------------------------------------------
# Step 4: Monte Carlo uncertainty propagation for each planet
# Draw 100,000 samples from Gaussian(a, sig_a) x Gaussian(T, sig_T)
# and propagate to GM_sun posterior
# -------------------------------------------------------
N_mc = 100_000
rng = np.random.default_rng(seed=314159)
MC_results = {}

print("\nMonte Carlo vs Gaussian Uncertainty Propagation")
print(f"{'Planet':<10} {'Gauss sigma':<16} {'MC sigma (16-84%)':<20} {'MC/Gauss':<10} {'MC skew'}")
print("-"*70)

for i, name in enumerate(names):
    a_samp = rng.normal(a_m[i], sig_a_m[i], N_mc)
    T_samp = rng.normal(T_s[i], sig_T_s[i], N_mc)
    # Reject unphysical samples (negative a or T)
    valid = (a_samp > 0) & (T_samp > 0)
    a_samp = a_samp[valid]
    T_samp = T_samp[valid]

    GM_samp = 4.0 * np.pi**2 * a_samp**3 / T_samp**2

    p16, p50, p84 = np.percentile(GM_samp, [16, 50, 84])
    mc_sigma = (p84 - p16) / 2.0

    # Skewness of posterior
    mc_mean = GM_samp.mean()
    mc_std  = GM_samp.std()
    skewness = np.mean(((GM_samp - mc_mean)/mc_std)**3)

    MC_results[name] = GM_samp
    ratio = mc_sigma / sigma_GM_gauss[i] if sigma_GM_gauss[i] > 0 else np.nan
    print(f"{name:<10} {sigma_GM_gauss[i]/1e18:<16.4f} {mc_sigma/1e18:<20.4f} {ratio:<10.4f} {skewness:.4f}")

# -------------------------------------------------------
# Step 5: Inject correlated systematic error (transit timing bias)
# Simulate a +0.5% systematic offset in all measured periods
# mimicking an instrumental clock drift or barycentric correction error
# -------------------------------------------------------
T_biased = T_s * 1.005  # 0.5% systematic overcounting
GM_biased = 4.0 * np.pi**2 * a_m**3 / T_biased**2
w_b = 1.0 / sigma_GM_gauss[clean]**2
GM_biased_mean = np.sum(w_b * GM_biased[clean]) / np.sum(w_b)
systematic_shift = GM_biased_mean - GM_sun_true
print(f"\nSystematic Error Injection (0.5% period overcounting)")
print(f"  GM_sun (biased)          : {GM_biased_mean:.6e} m³/s²")
print(f"  Systematic shift         : {systematic_shift:.4e} m³/s²  ({100*systematic_shift/GM_sun_true:.3f}%)")
print(f"  Shift in sigma units     : {systematic_shift/GM_wmean_err:.2f} sigma")

# -------------------------------------------------------
# Step 6: Diagnostic plots
# -------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(17, 10))
fig.suptitle("Exercise 3 — Keplerian Orbital Mechanics & Monte Carlo Uncertainty", fontsize=13)

# Panel A: Kepler III log-log plot
ax = axes[0, 0]
log_a = np.log10(a_AU[clean])
log_T = np.log10(T_yr[clean])
slope_k3, int_k3, r_k3, _, se_k3 = linregress(log_a, log_T)
a_fit = np.linspace(-0.5, 1.6, 200)
ax.errorbar(np.log10(a_AU[clean]), np.log10(T_yr[clean]),
            xerr=sig_a[clean]/a_AU[clean]/np.log(10),
            yerr=sig_T[clean]/T_yr[clean]/np.log(10),
            fmt='o', color='steelblue', capsize=4, ms=6, label='Clean sample')
ax.errorbar(np.log10(a_AU[is_stress]), np.log10(T_yr[is_stress]),
            xerr=sig_a[is_stress]/a_AU[is_stress]/np.log(10),
            yerr=sig_T[is_stress]/T_yr[is_stress]/np.log(10),
            fmt='s', color='crimson', capsize=4, ms=6, label='Stress objects')
ax.plot(a_fit, 1.5 * a_fit, 'k--', lw=1.5, label='Kepler III: slope=1.5')
ax.plot(a_fit, slope_k3 * a_fit + int_k3, 'r-', lw=1.8,
        label=f'Fit: slope={slope_k3:.4f}±{se_k3:.4f}')
ax.set_xlabel('log₁₀(a / AU)')
ax.set_ylabel('log₁₀(T / yr)')
ax.set_title("Kepler's Third Law (log-log)")
ax.legend(fontsize=7)
ax.grid(alpha=0.3)

# Panel B: GM_sun per planet with error bars
ax = axes[0, 1]
planet_idx = np.arange(len(names))
colors = ['crimson' if s else 'steelblue' for s in is_stress]
ax.errorbar(planet_idx, GM_per_planet/1e20, yerr=2*sigma_GM_gauss/1e20,
            fmt='none', color='gray', capsize=4, lw=1.2)
ax.scatter(planet_idx, GM_per_planet/1e20, c=colors, s=50, zorder=5)
ax.axhline(GM_sun_true/1e20, color='black', ls='--', lw=1.5, label=f'True GM☉={GM_sun_true/1e20:.4f}')
ax.axhline(GM_wmean_clean/1e20, color='blue', ls='-', lw=1.5,
           label=f'Clean WLS: {GM_wmean_clean/1e20:.4f}±{GM_wmean_err/1e20:.4f}')
ax.set_xticks(planet_idx)
ax.set_xticklabels([n[:4] for n in names], fontsize=7, rotation=30)
ax.set_ylabel('GM☉ (×10²⁰ m³/s²)')
ax.set_title('GM☉ Recovery per Planet (±2σ)')
ax.legend(fontsize=7)
ax.grid(alpha=0.3)

# Panel C: MC posterior for Earth (baseline) and Pluto (stress)
ax = axes[0, 2]
for body, color, ls in [("Earth", "steelblue", "-"), ("Pluto", "crimson", "--"),
                         ("Mercury", "darkorange", ":")]:
    samp = MC_results[body] / 1e20
    ax.hist(samp, bins=80, density=True, histtype='step', color=color, lw=1.5,
            label=f'{body} MC posterior')
ax.axvline(GM_sun_true/1e20, color='black', ls='-', lw=1.5, label='True GM☉')
ax.set_xlabel('GM☉ (×10²⁰ m³/s²)')
ax.set_ylabel('Probability Density')
ax.set_title('MC Posteriors: Earth vs Pluto vs Mercury')
ax.legend(fontsize=7)
ax.grid(alpha=0.3)
ax.set_xlim(0.9e20/1e20 * GM_sun_true/1e20, 1.1e20/1e20 * GM_sun_true/1e20)

# Panel D: MC vs Gaussian sigma comparison
ax = axes[1, 0]
gauss_sigmas = sigma_GM_gauss / 1e18
mc_sigmas = np.array([(np.percentile(MC_results[n], 84) - np.percentile(MC_results[n], 16))
                       / 2.0 / 1e18 for n in names])
ax.scatter(gauss_sigmas, mc_sigmas, c=colors, s=60, zorder=5)
for i, name in enumerate(names):
    ax.annotate(name[:4], (gauss_sigmas[i], mc_sigmas[i]), fontsize=6, xytext=(3, 2),
                textcoords='offset points')
max_sig = max(gauss_sigmas.max(), mc_sigmas.max()) * 1.1
ax.plot([0, max_sig], [0, max_sig], 'k--', lw=1.0, label='MC = Gauss')
ax.set_xlabel('Gaussian σ(GM☉) (×10¹⁸ m³/s²)')
ax.set_ylabel('MC σ(GM☉) 16–84% (×10¹⁸ m³/s²)')
ax.set_title('Gaussian vs MC Uncertainty')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel E: Systematic bias map — period offset sweep
ax = axes[1, 1]
bias_grid = np.linspace(-0.02, 0.02, 100)   # -2% to +2% period bias
GM_bias_arr = np.zeros(100)
for j, bias in enumerate(bias_grid):
    T_b = T_s[clean] * (1.0 + bias)
    GM_b = 4.0 * np.pi**2 * a_m[clean]**3 / T_b**2
    w_bb = 1.0 / sigma_GM_gauss[clean]**2
    GM_bias_arr[j] = np.sum(w_bb * GM_b) / np.sum(w_bb)

ax.plot(bias_grid * 100, (GM_bias_arr - GM_sun_true)/GM_sun_true * 100, 'r-', lw=2.0)
ax.axhline(0, color='black', ls='--', lw=1.0)
ax.axvline(0, color='black', ls='--', lw=1.0)
ax.axvline(0.5, color='gray', ls=':', lw=1.0, label='+0.5% injected bias')
ax.set_xlabel('Period systematic bias (%)')
ax.set_ylabel('GM☉ systematic error (%)')
ax.set_title('Systematic Error Propagation:\nPeriod Timing Bias → GM☉')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Panel F: Chi-squared consistency test for clean sample
ax = axes[1, 2]
chi2_vals = ((GM_per_planet[clean] - GM_wmean_clean) / sigma_GM_gauss[clean])**2
ndof = clean.sum() - 1
chi2_total = chi2_vals.sum()
p_chi2 = 1.0 - chi2.cdf(chi2_total, ndof)
ax.bar(np.array(names)[clean], chi2_vals, color='steelblue', alpha=0.7)
ax.axhline(1.0, color='black', ls='--', lw=1.0, label='χ²/dof = 1 (expected)')
ax.set_ylabel('χ²ᵢ contribution')
ax.set_title(f'χ² Consistency Test\nχ²={chi2_total:.2f}, ndof={ndof}, p={p_chi2:.3f}')
ax.set_xticklabels([n[:4] for n in np.array(names)[clean]], rotation=30, fontsize=7)
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('ex3_kepler_mc_uncertainty.png', dpi=150, bbox_inches='tight')
plt.show()
print("\nFigure saved: ex3_kepler_mc_uncertainty.png")
```

**Interpreting the Boundary Condition Failures**

The stress testing protocol is designed to fail in instructive ways. When you include Pluto and Eris in the weighted mean, the large formal uncertainties on their orbital elements cause the weighted estimator to downweight them so severely that they contribute almost nothing to the final result — but they inflate the chi-squared statistic and reduce the apparent goodness-of-fit, which is a signal to audit the sample. When you include Mercury without correcting for its relativistic orbital precession (43 arcseconds per century, the first experimental confirmation of general relativity), you recover a $GM_\odot$ that is slightly too large because Mercury's observed period already incorporates the GR correction while your Newtonian $T^2 \propto a^3$ formula does not. The magnitude of this discrepancy — typically 0.1 to 0.3 sigma for a ground-based measurement — is small but non-zero and grows systematically as you add more Mercury transits.

The systematic bias map in Panel E communicates the most practically important result: a 1% systematic overcounting of orbital periods — which could arise from an uncorrected barycentric velocity correction, an incorrect leap-second accounting, or a timing system clock drift — translates to a 2% error in $GM_\odot$. This is a purely linear propagation, following the exponent of $T^{-2}$ in Kepler's third law. Any measurement system that claims sub-percent precision on $GM_\odot$ must demonstrate timing accuracy to 0.1% or better across the full observation baseline, which for Saturn or Uranus spans decades.

---

## Laboratory Cheat Sheet & Metric Verification Guide

This section is a practitioner's reference for the numerical criteria that define a successful laboratory run across all three exercises. Use it as a go/no-go checklist before filing results or drawing scientific conclusions.

### Environment Verification

Before running any exercise script, confirm all dependencies are present and functional with a single verification sweep:

```bash
python -c "
import numpy as np, scipy, matplotlib, astropy
print(f'NumPy   {np.__version__}')
print(f'SciPy   {scipy.__version__}')
print(f'MPL     {matplotlib.__version__}')
print(f'Astropy {astropy.__version__}')
from scipy.stats import linregress, norm, chi2
from scipy.optimize import curve_fit
from astropy.coordinates import SkyCoord
import astropy.units as u
print('All imports: PASS')
"
```

The output must show four version lines followed by `All imports: PASS`. Any `ImportError` or `ModuleNotFoundError` must be resolved before proceeding.

### Exercise 1 — Inverse-Square Law: Acceptance Criteria

The slope $\alpha$ of the $\log F$ vs $\log d$ fit must lie in the interval $[-2.10,\, -1.90]$ for the synthetic dataset with the seed set to 42. Any result outside this window indicates a bug in the flux conversion, a failure in the magnitude-to-flux transformation, or incorrect masking of the parallax quality cut. The RMS residual in absolute magnitude must be below 0.25 mag. The mean Lutz-Kelker bias must be negative (between $-0.10$ and $0.00$ mag) — a positive mean bias would indicate that the parallax noise is being added with the wrong sign. The $R^2$ of the power-law fit must exceed 0.95; a lower value indicates insufficient dynamic range in distance coverage and the synthetic distance range should be widened.

| Metric | Acceptable Range | Failure Diagnostic |
|---|---|---|
| Slope $\alpha$ | $[-2.10,\, -1.90]$ | Flux conversion error or wrong parallax sign |
| RMS $\Delta M_V$ | $< 0.25$ mag | Excessive photometric scatter or wrong zero-point |
| Mean bias | $[-0.10,\, 0.00]$ mag | Lutz-Kelker sign error |
| $R^2$ | $> 0.95$ | Distance range too narrow |
| $p$-value | $< 10^{-20}$ | Insufficient sample size or noise floor too high |

### Exercise 2 — Hubble Flow: Acceptance Criteria

The WLS estimate of $H_0$ must recover the injected value of 73.0 km/s/Mpc to within 3 km/s/Mpc (better than 4% relative error) for the reference calibration. The calibration sensitivity $dH_0/dM_{\rm cal}$ must be negative and in the range $[-30,\,-20]$ (km/s/Mpc)/mag — a sensitivity outside this range indicates a numerical error in the distance modulus conversion. The peculiar velocity dispersion recovered from the residual panel must lie between 250 and 380 km/s; the injected value is 300 km/s and the scatter around it comes from the finite sample size. The $R^2$ of the linear calibration response must exceed 0.999, confirming that $H_0$ responds linearly to zero-point shifts across the full calibration grid.

| Metric | Acceptable Range | Failure Diagnostic |
|---|---|---|
| $H_0$ (WLS, ref cal) | $70$–$76$ km/s/Mpc | Period/distance unit conversion error |
| $dH_0/dM_{\rm cal}$ | $[-30,\,-20]$ | Distance modulus formula sign error |
| $\sigma_{\rm pec}$ residual | $250$–$380$ km/s | Peculiar velocity noise not injected correctly |
| Calibration $R^2$ | $> 0.999$ | Non-linear response — check for data clip or saturation |

### Exercise 3 — Keplerian Mechanics: Acceptance Criteria

The clean-sample weighted mean $GM_\odot$ must recover the true value $1.327 \times 10^{20}$ m³/s² to within 1 sigma (the formal uncertainty of the weighted mean). The chi-squared $p$-value for the clean sample must exceed 0.05, confirming that the inter-planet scatter is consistent with the quoted formal uncertainties. If the chi-squared $p$-value falls below 0.01, the dominant excess scatter source is almost always Mercury's relativistic precession or unmodeled Jupiter perturbations on the outer planets — removing Mercury alone should restore consistency. The Monte Carlo sigma for Earth must agree with the Gaussian propagation to within 5% (the ratio column should be $1.00 \pm 0.05$), confirming that the linear approximation is valid for well-measured planets with small relative errors. For Pluto and Eris the MC/Gauss ratio will exceed 1.1 and may reach 1.3, reflecting the genuine non-linearity of $GM \propto a^3/T^2$ when relative errors on $a$ or $T$ exceed a few percent.

| Metric | Acceptable Range | Failure Diagnostic |
|---|---|---|
| $GM_\odot$ (clean sample) | Within 1$\sigma$ of true | Unit conversion error (AU, yr to SI) |
| Chi-squared $p$-value | $> 0.05$ | Mercury GR precession not excluded |
| MC/Gauss ratio (Earth) | $1.00 \pm 0.05$ | Sampling noise — increase $N_{\rm MC}$ to $10^6$ |
| MC/Gauss ratio (Pluto) | $1.10$–$1.40$ | Expected non-linearity; outside range = coding error |
| Systematic slope (bias map) | Approximately $-2\%$ per 1% period error | Exponent of $T^{-2}$ not correctly applied |

### Quick-Reference Physical Constants Used in This Guide

| Constant | Symbol | Value | Source |
|---|---|---|---|
| Gravitational constant | $G$ | $6.674 \times 10^{-11}$ m³ kg⁻¹ s⁻² | CODATA 2018 |
| Solar mass | $M_\odot$ | $1.989 \times 10^{30}$ kg | IAU 2015 |
| Speed of light | $c$ | $2.998 \times 10^5$ km/s | CODATA 2018 |
| Astronomical Unit | AU | $1.496 \times 10^{11}$ m | IAU 2012 |
| H$\alpha$ rest wavelength | $\lambda_0$ | $6562.8$ Å | NIST ASD |
| Vega V-band flux | $F_{\rm Vega}$ | $3.63 \times 10^{-9}$ erg/cm²/s/Å | Bessell 1998 |
| SN Ia absolute magnitude | $M_B$ | $-19.253$ mag | Riess et al. 2022 |
| Hubble constant (SH0ES) | $H_0$ | $73.04 \pm 1.04$ km/s/Mpc | Riess et al. 2022 |
| Hubble constant (Planck) | $H_0$ | $67.36 \pm 0.54$ km/s/Mpc | Planck 2018 |

### Diagnostic Command Reference

The following one-liners test specific pipeline components without running the full exercises. Each should complete silently if the environment and logic are correct.

```bash
# Verify inverse-square exponent from a 50-point toy dataset
python -c "
import numpy as np; from scipy.stats import linregress
rng=np.random.default_rng(0); d=rng.uniform(10,100,50)
F=1.0/d**2 * rng.lognormal(0,0.02,50)
s,*_=linregress(np.log10(d),np.log10(F))
assert abs(s+2.0)<0.1, f'Slope fail: {s:.3f}'; print(f'ISL slope: {s:.4f} PASS')
"

# Verify Hubble flow recovery from noise-free data
python -c "
import numpy as np
d=np.linspace(5,200,50); H0_true=73.0; v=H0_true*d
H0_fit=np.sum(v*d)/np.sum(d**2)
assert abs(H0_fit-H0_true)<0.01, f'H0 fail: {H0_fit}'; print(f'H0 fit: {H0_fit:.4f} PASS')
"

# Verify Kepler III SI unit consistency for Earth
python -c "
import numpy as np
G=6.674e-11; M=1.989e30; a=1.496e11; T=3.156e7
GM_K=4*np.pi**2*a**3/T**2; GM_true=G*M
err=abs(GM_K-GM_true)/GM_true
assert err<0.001, f'Error {err:.2%}'; print(f'Kepler GM_sun: {GM_K:.4e}, err={err:.4%} PASS')
"
```

Each PASS result confirms that the corresponding numerical pipeline is internally consistent. A failure at this level, before any noise is introduced, is always a unit conversion error or a formula sign error — both of which are silent in floating-point arithmetic and invisible without this kind of sanity-check harness.
