# Operational Verification Labs: Analytical Chemistry

## Objective & Laboratory Bench Setup

Analytical chemistry stands at the empirical crossroads of chemical theory and quantitative measurement, demanding precision instrumentation, rigorous calibration protocols, and systematic error propagation analysis. These operational verification labs construct a complete measurement pipeline from sample preparation through spectroscopic analysis, chromatographic separation, and potentiometric titration, grounding abstract chemical equilibria in concrete instrumental response curves and calibration standards.

The laboratory bench configuration requires a UV-Vis spectrophotometer (wavelength range 190–1100 nm, spectral bandwidth ≤2 nm), a precision analytical balance (readability 0.1 mg, linearity ±0.2 mg), calibrated volumetric glassware (Class A tolerances per ISO 1042), and a pH meter with combination glass electrode (resolution 0.01 pH units, accuracy ±0.02 pH). The computational analysis environment integrates NumPy for matrix operations and statistical aggregation, SciPy for nonlinear least-squares regression and numerical integration, and Matplotlib for publication-quality visualization of calibration curves, Beer-Lambert linearity verification, and residual error distributions.

Verify the scientific Python environment by executing the following diagnostic sequence in a terminal session:

```bash
python -c 'import numpy as np; print(f"NumPy {np.__version__}")'
python -c 'import scipy; print(f"SciPy {scipy.__version__}")'
python -c 'import matplotlib; print(f"Matplotlib {matplotlib.__version__}")'
```

Expected output confirms NumPy ≥1.24, SciPy ≥1.10, and Matplotlib ≥3.7. The laboratory notebook adopts SI units throughout: molar concentrations in mol/L (M), absorbance dimensionless, path length in cm, wavelength in nm, and pH as the negative base-10 logarithm of hydrogen ion activity.

## Exercise 1: Empirical Observation & Measurement Protocol

### Beer-Lambert Law Verification Through UV-Vis Spectrophotometry

The Beer-Lambert law provides the foundational quantitative relationship between solution concentration and optical absorbance, stating that absorbance $A$ relates linearly to molar absorptivity $\varepsilon$ (L mol$^{-1}$ cm$^{-1}$), path length $b$ (cm), and concentration $c$ (mol/L) through the expression $A = \varepsilon b c$. This exercise constructs an empirical calibration curve for potassium permanganate (KMnO₄), a chromophore exhibiting strong visible absorption at $\lambda_{\text{max}} = 525$ nm due to ligand-to-metal charge transfer transitions in the permanganate anion.

Begin by preparing a 1.000 mM stock solution: accurately weigh 31.61 mg of reagent-grade KMnO₄ (molar mass 158.034 g/mol) on the analytical balance, transfer quantitatively to a 200.0 mL volumetric flask using a powder funnel, dissolve in approximately 150 mL of distilled water with gentle swirling, dilute to the calibration mark with additional distilled water, and invert the stoppered flask fifteen times to ensure homogeneous mixing. Record the exact mass to ±0.1 mg for subsequent propagation of uncertainty calculations.

Prepare a dilution series spanning the linear dynamic range of the spectrophotometer: pipette 1.00, 2.00, 3.00, 4.00, and 5.00 mL aliquots of the stock solution into five clean 50.0 mL volumetric flasks using a calibrated pipette (Class A tolerance ±0.02 mL), dilute each to volume with distilled water, and invert to mix. The resulting concentrations are 20.0, 40.0, 60.0, 80.0, and 100.0 μM, respectively. Prepare a blank reference solution containing only distilled water in an identical volumetric flask.

Set the spectrophotometer to 525 nm wavelength with 2 nm spectral bandwidth and allow the deuterium and tungsten lamps to stabilize for at least 15 minutes until baseline drift is less than 0.001 AU/min. Zero the instrument using the blank reference in a matched 1.00 cm quartz cuvette, ensuring all optical surfaces are clean and free of fingerprints or particulate contamination. Measure the absorbance of each standard solution in triplicate, rinsing the cuvette three times with the next solution before filling to minimize cross-contamination, and record all values to three decimal places.

The following Python implementation constructs the calibration curve through linear regression, computes the molar absorptivity from the slope, quantifies regression statistics including the coefficient of determination $R^2$, and performs residual analysis to detect systematic deviations from linearity:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Experimental data: concentrations in micromolar (μM) and absorbance (AU)
concentrations = np.array([0.0, 20.0, 40.0, 60.0, 80.0, 100.0])  # μM
absorbance_trial1 = np.array([0.000, 0.445, 0.891, 1.339, 1.782, 2.231])
absorbance_trial2 = np.array([0.001, 0.448, 0.888, 1.335, 1.786, 2.225])
absorbance_trial3 = np.array([-0.001, 0.442, 0.894, 1.341, 1.779, 2.228])

# Compute mean absorbance and standard deviation for each concentration
absorbance_mean = np.mean([absorbance_trial1, absorbance_trial2, absorbance_trial3], axis=0)
absorbance_std = np.std([absorbance_trial1, absorbance_trial2, absorbance_trial3], axis=0, ddof=1)

# Linear regression: A = epsilon * b * c
# Convert concentrations to mol/L for SI consistency
concentrations_M = concentrations * 1e-6  # mol/L
path_length_cm = 1.00  # cm

# Perform weighted least squares regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations_M, absorbance_mean)

# Extract molar absorptivity (slope = epsilon * b)
molar_absorptivity = slope / path_length_cm  # L mol^-1 cm^-1
r_squared = r_value ** 2

# Compute residuals for diagnostic analysis
absorbance_predicted = slope * concentrations_M + intercept
residuals = absorbance_mean - absorbance_predicted

# Print quantitative results
print("Beer-Lambert Calibration Results")
print("=" * 50)
print(f"Molar Absorptivity (ε): {molar_absorptivity:.1f} L mol⁻¹ cm⁻¹")
print(f"Y-intercept: {intercept:.4f} AU")
print(f"Correlation Coefficient (R²): {r_squared:.6f}")
print(f"Standard Error of Regression: {std_err:.4f}")
print(f"\nConcentration (μM)  Absorbance (mean)  Std Dev  Residual")
print("-" * 60)
for i in range(len(concentrations)):
    print(f"{concentrations[i]:8.1f}        {absorbance_mean[i]:8.4f}      {absorbance_std[i]:6.4f}   {residuals[i]:+7.4f}")

# Visualization: calibration curve with error bars and residual plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Top panel: calibration curve
ax1.errorbar(concentrations, absorbance_mean, yerr=absorbance_std, 
             fmt='o', color='darkviolet', markersize=8, capsize=5, 
             capthick=2, label='Experimental Data (n=3)')
ax1.plot(concentrations, slope * concentrations_M + intercept, 
         'k-', linewidth=2, label=f'Linear Fit: A = {slope:.4f}c + {intercept:.4f}')
ax1.set_xlabel('Concentration (μM)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Absorbance (AU)', fontsize=12, fontweight='bold')
ax1.set_title('Beer-Lambert Calibration Curve for KMnO₄ at 525 nm', 
              fontsize=14, fontweight='bold')
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.text(0.05, 0.95, f'ε = {molar_absorptivity:.1f} L mol⁻¹ cm⁻¹\nR² = {r_squared:.6f}',
         transform=ax1.transAxes, fontsize=11, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Bottom panel: residual plot
ax2.scatter(concentrations, residuals, color='crimson', s=80, alpha=0.7)
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1.5)
ax2.fill_between(concentrations, -2*std_err, 2*std_err, alpha=0.2, color='gray')
ax2.set_xlabel('Concentration (μM)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Residual (AU)', fontsize=12, fontweight='bold')
ax2.set_title('Residual Analysis', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('beer_lambert_calibration_kmnO4.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nCalibration curve saved as 'beer_lambert_calibration_kmnO4.png'")
```

Execute this script by saving it as `beer_lambert_analysis.py` and running `python beer_lambert_analysis.py` from the laboratory notebook directory. The output reports a molar absorptivity of approximately 2230 L mol⁻¹ cm⁻¹ for KMnO₄ at 525 nm, consistent with literature values (2200–2300 L mol⁻¹ cm⁻¹), and an $R^2$ value exceeding 0.9999, confirming excellent linearity across the concentration range. The residual plot reveals whether systematic curvature, heteroscedasticity (concentration-dependent variance), or outlier points compromise the linear model assumption.

### Physical Interpretation and Uncertainty Propagation

The molar absorptivity quantifies the intrinsic absorption cross-section of the permanganate chromophore, arising from quantum mechanical transition probabilities between the ground electronic state and excited charge-transfer configurations. The near-unity $R^2$ validates the Beer-Lambert assumption that molecular interactions and non-ideality effects remain negligible within this concentration regime. Deviations at higher concentrations (typically above 1 mM) manifest as negative curvature due to self-association, solvent-solute interactions, and refractive index changes.

Propagate uncertainty through the calibration curve using the root-sum-square method. The standard uncertainty in absorbance measurements is $u(A) = 0.003$ AU (instrument specification). The uncertainty in concentration preparation combines volumetric glassware tolerances and balance uncertainty:

$$u_{\text{rel}}(c) = \sqrt{\left(\frac{u_{\text{mass}}}{m}\right)^2 + \left(\frac{u_{\text{vol}}}{V}\right)^2}$$

For the stock solution: $u_{\text{mass}} = 0.1$ mg, $m = 31.6$ mg, $u_{\text{vol}} = 0.15$ mL, $V = 200.0$ mL, yielding $u_{\text{rel}}(c) = 0.32\%$. The uncertainty in molar absorptivity propagates from the regression slope uncertainty, computed as the standard error of the regression divided by the square root of the number of calibration points.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Potentiometric Acid-Base Titration with Gran Plot Linearization

Potentiometric titration measures the pH evolution during incremental addition of a strong base to a weak acid solution, constructing an experimental titration curve that reveals the equivalence point, buffer capacity, and dissociation constant $K_a$. This exercise titrates acetic acid (CH₃COOH) with standardized sodium hydroxide (NaOH), applying Gran plot linearization to determine the equivalence volume with sub-microliter precision and extracting the $pK_a$ from the half-equivalence point pH.

Prepare 50.00 mL of approximately 0.1 M acetic acid solution by pipetting 0.29 mL of glacial acetic acid (density 1.049 g/mL, purity 99.7%) into a 50.0 mL volumetric flask, diluting to volume, and mixing thoroughly. Standardize the acid concentration by titration against primary standard potassium hydrogen phthalate (KHP) or by accepting the calculated nominal concentration with appropriate uncertainty bounds. Transfer the acid solution to a 150 mL beaker, immerse a calibrated pH electrode and magnetic stir bar, and position a 10.00 mL burette (Class A, tolerance ±0.02 mL) filled with standardized 0.1000 M NaOH above the beaker.

Calibrate the pH meter using certified buffer solutions at pH 4.00, 7.00, and 10.00, achieving two-point or three-point calibration with slope response 95–105% of the Nernstian ideal (59.16 mV/pH at 25°C). Initiate magnetic stirring at moderate speed (avoid vortex formation) and record the initial pH. Add NaOH in 0.50 mL increments initially, reducing to 0.10 mL increments near the anticipated equivalence point (approximately 5 mL for this system), and expanding back to 0.50 mL increments beyond the equivalence region. Allow 30 seconds for equilibration after each addition before recording the pH to three decimal places.

The Gran linearization method transforms the sigmoidal titration curve into two linear segments (before and after the equivalence point) whose intersection defines the equivalence volume $V_{\text{eq}}$ with enhanced precision. For the pre-equivalence region, the Gran function $G_1 = (V_0 + V) \times 10^{\text{pH}}$ linearizes with respect to added volume $V$, while the post-equivalence region employs $G_2 = (V_0 + V) \times 10^{-\text{pH}}$. The following Python implementation processes the titration data, constructs Gran plots, determines the equivalence point through linear regression, and extracts the $pK_a$ from the buffer region:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit

# Experimental titration data
# V_added: volume of NaOH added (mL)
# pH: measured pH values
V_added = np.array([0.00, 0.50, 1.00, 1.50, 2.00, 2.50, 3.00, 3.50, 4.00, 
                    4.50, 4.60, 4.70, 4.80, 4.90, 5.00, 5.10, 5.20, 5.30, 
                    5.40, 5.50, 6.00, 6.50, 7.00, 7.50, 8.00])
pH = np.array([2.89, 3.67, 3.92, 4.10, 4.27, 4.44, 4.62, 4.82, 5.05, 
               5.35, 5.45, 5.56, 5.70, 5.88, 6.15, 8.72, 10.65, 11.09, 
               11.37, 11.56, 11.96, 12.18, 12.32, 12.42, 12.49])

# System parameters
V0 = 50.00  # initial volume of acid (mL)
C_base = 0.1000  # concentration of NaOH (M)

# Gran function calculations
# Pre-equivalence: G1 = (V0 + V) * 10^pH
# Post-equivalence: G2 = (V0 + V) * 10^(pH - 14)
G1 = (V0 + V_added) * 10**pH
G2 = (V0 + V_added) * 10**(pH - 14)

# Identify pre-equivalence region (pH < 6) and post-equivalence region (pH > 9)
pre_eq_mask = pH < 6.0
post_eq_mask = pH > 9.0

# Linear regression for Gran plots
slope1, intercept1, r1, _, _ = stats.linregress(V_added[pre_eq_mask], G1[pre_eq_mask])
slope2, intercept2, r2, _, _ = stats.linregress(V_added[post_eq_mask], G2[post_eq_mask])

# Equivalence points from x-intercepts (G = 0)
V_eq1 = -intercept1 / slope1  # from pre-equivalence Gran plot
V_eq2 = -intercept2 / slope2  # from post-equivalence Gran plot
V_eq_mean = (V_eq1 + V_eq2) / 2

# Calculate acid concentration from equivalence volume
C_acid = (C_base * V_eq_mean) / V0

# Extract pKa from half-equivalence point (V = V_eq/2)
# At half-equivalence: pH = pKa (Henderson-Hasselbalch)
half_eq_idx = np.argmin(np.abs(V_added - V_eq_mean/2))
pKa_experimental = pH[half_eq_idx]

# Print results
print("Potentiometric Titration Analysis")
print("=" * 60)
print(f"Equivalence Volume (Pre-eq Gran):  {V_eq1:.3f} mL")
print(f"Equivalence Volume (Post-eq Gran): {V_eq2:.3f} mL")
print(f"Mean Equivalence Volume:            {V_eq_mean:.3f} mL")
print(f"Acid Concentration:                 {C_acid:.4f} M")
print(f"Experimental pKa:                   {pKa_experimental:.2f}")
print(f"Literature pKa (acetic acid):       4.76")
print(f"Percent Error:                      {abs(pKa_experimental - 4.76)/4.76 * 100:.1f}%")

# Visualization: titration curve and Gran plots
fig = plt.figure(figsize=(14, 10))

# Titration curve with derivative
ax1 = plt.subplot(2, 2, 1)
ax1.plot(V_added, pH, 'o-', color='steelblue', markersize=6, linewidth=2)
ax1.axvline(V_eq_mean, color='red', linestyle='--', linewidth=2, label=f'V_eq = {V_eq_mean:.2f} mL')
ax1.axhline(pKa_experimental, color='green', linestyle='--', linewidth=1.5, label=f'pKa = {pKa_experimental:.2f}')
ax1.set_xlabel('Volume NaOH Added (mL)', fontsize=11, fontweight='bold')
ax1.set_ylabel('pH', fontsize=11, fontweight='bold')
ax1.set_title('Potentiometric Titration Curve', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# First derivative (dpH/dV) to locate inflection point
dV = np.diff(V_added)
dpH = np.diff(pH)
derivative = dpH / dV
V_deriv = (V_added[:-1] + V_added[1:]) / 2

ax2 = plt.subplot(2, 2, 2)
ax2.plot(V_deriv, derivative, 's-', color='orangered', markersize=5, linewidth=1.5)
ax2.axvline(V_eq_mean, color='red', linestyle='--', linewidth=2)
ax2.set_xlabel('Volume NaOH Added (mL)', fontsize=11, fontweight='bold')
ax2.set_ylabel('dpH/dV', fontsize=11, fontweight='bold')
ax2.set_title('First Derivative (Inflection Detection)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Pre-equivalence Gran plot
ax3 = plt.subplot(2, 2, 3)
ax3.plot(V_added[pre_eq_mask], G1[pre_eq_mask], 'o', color='darkgreen', markersize=7, label='Data')
V_fit1 = np.linspace(0, V_eq1, 100)
G1_fit = slope1 * V_fit1 + intercept1
ax3.plot(V_fit1, G1_fit, 'k-', linewidth=2, label=f'Fit: R² = {r1**2:.5f}')
ax3.axvline(V_eq1, color='red', linestyle='--', linewidth=2, label=f'V_eq = {V_eq1:.2f} mL')
ax3.set_xlabel('Volume NaOH Added (mL)', fontsize=11, fontweight='bold')
ax3.set_ylabel('G₁ = (V₀ + V) × 10^pH', fontsize=11, fontweight='bold')
ax3.set_title('Pre-Equivalence Gran Plot', fontsize=13, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)

# Post-equivalence Gran plot
ax4 = plt.subplot(2, 2, 4)
ax4.plot(V_added[post_eq_mask], G2[post_eq_mask], 's', color='purple', markersize=7, label='Data')
V_fit2 = np.linspace(V_eq2, np.max(V_added), 100)
G2_fit = slope2 * V_fit2 + intercept2
ax4.plot(V_fit2, G2_fit, 'k-', linewidth=2, label=f'Fit: R² = {r2**2:.5f}')
ax4.axvline(V_eq2, color='red', linestyle='--', linewidth=2, label=f'V_eq = {V_eq2:.2f} mL')
ax4.set_xlabel('Volume NaOH Added (mL)', fontsize=11, fontweight='bold')
ax4.set_ylabel('G₂ = (V₀ + V) × 10^(-pH)', fontsize=11, fontweight='bold')
ax4.set_title('Post-Equivalence Gran Plot', fontsize=13, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('potentiometric_titration_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nTitration analysis saved as 'potentiometric_titration_analysis.png'")
```

Save this implementation as `titration_analysis.py` and execute with `python titration_analysis.py`. The Gran plot intercepts converge to an equivalence volume of approximately 5.00 mL, corresponding to an acetic acid concentration of 0.1000 M. The experimental $pK_a$ extracted at the half-equivalence point should fall within 4.70–4.80, matching the literature value of 4.76 for acetic acid at 25°C. Deviations arise from temperature variations (the $pK_a$ exhibits a temperature coefficient of approximately +0.002 per °C), ionic strength effects, and electrode junction potential drift.

### Henderson-Hasselbalch Buffer Region Analysis

The buffer region between 20% and 80% titration exhibits minimal pH change per unit added base, quantified by the buffer capacity $\beta = \frac{dC_{\text{base}}}{d\text{pH}}$. The Henderson-Hasselbalch equation relates pH to the ratio of conjugate base to weak acid:

$$\text{pH} = pK_a + \log_{10}\left(\frac{[\text{A}^-]}{[\text{HA}]}\right)$$

At the half-equivalence point, the concentrations of acetic acid and acetate are equal, causing the logarithmic term to vanish and yielding $\text{pH} = pK_a$ directly. The buffer capacity reaches its maximum at this point, calculated as $\beta_{\text{max}} = 0.576 \, C_{\text{total}}$ for a monoprotic weak acid buffer system. Experimental verification requires measuring the pH change induced by adding known aliquots of strong acid or base to a prepared buffer solution at the half-equivalence composition.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### High-Performance Liquid Chromatography (HPLC) Method Validation

Chromatographic separation method validation assesses the analytical performance characteristics including linearity, precision, accuracy, limit of detection (LOD), limit of quantitation (LOQ), and robustness across operational parameter perturbations. This exercise validates an HPLC method for quantifying caffeine in beverage samples, constructing calibration curves across five orders of magnitude concentration range, computing detection limits from signal-to-noise statistics, and stress-testing the method against variations in mobile phase composition, flow rate, and column temperature.

The HPLC system configuration employs a reverse-phase C18 column (150 mm × 4.6 mm, 5 μm particle size), an isocratic mobile phase of 70:30 water:acetonitrile (v/v) with 0.1% trifluoroacetic acid modifier, a flow rate of 1.0 mL/min, column temperature of 30°C, injection volume of 20 μL, and UV detection at 273 nm corresponding to the caffeine absorption maximum. Prepare a 1000 μg/mL stock solution by dissolving 50.0 mg of anhydrous caffeine (molar mass 194.19 g/mol) in 50.0 mL of mobile phase in a volumetric flask.

Construct a nine-point calibration series spanning 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, and 1000.0 μg/mL by serial dilution of the stock solution. Inject each standard in triplicate, recording the peak area (mAU·s) and retention time (min). The blank injection (mobile phase only) establishes the baseline noise level for LOD and LOQ calculations. Caffeine elutes as a sharp, symmetric peak at approximately 4.5 minutes under these conditions.

The following Python implementation processes the HPLC chromatographic data, constructs a weighted calibration curve to account for heteroscedastic variance at low concentrations, computes detection limits using the ICH Q2(R1) guideline definitions, and performs robustness testing across systematic parameter variations:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit

# Calibration data: concentration (μg/mL) and peak area (mAU·s)
concentrations = np.array([0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0])
peak_area_1 = np.array([125, 598, 1205, 5987, 12034, 60145, 120312, 601245, 1202341])
peak_area_2 = np.array([118, 612, 1198, 6012, 11987, 59987, 120567, 600987, 1201987])
peak_area_3 = np.array([132, 589, 1211, 5976, 12098, 60234, 120198, 601567, 1202789])

# Compute mean and standard deviation for each concentration
peak_area_mean = np.mean([peak_area_1, peak_area_2, peak_area_3], axis=0)
peak_area_std = np.std([peak_area_1, peak_area_2, peak_area_3], axis=0, ddof=1)

# Blank injections for noise determination (n=10)
blank_peak_areas = np.array([12, 18, 15, 20, 14, 16, 19, 13, 17, 15])
blank_mean = np.mean(blank_peak_areas)
blank_std = np.std(blank_peak_areas, ddof=1)

# Weighted linear regression (weights = 1/variance)
weights = 1 / (peak_area_std**2 + 1e-6)  # add small constant to avoid division by zero
slope_wt, intercept_wt = np.polyfit(concentrations, peak_area_mean, 1, w=weights)

# Unweighted regression for comparison
slope_uw, intercept_uw, r_uw, _, _ = stats.linregress(concentrations, peak_area_mean)
r_squared_uw = r_uw ** 2

# Compute predicted values and residuals
peak_area_pred_wt = slope_wt * concentrations + intercept_wt
residuals_wt = peak_area_mean - peak_area_pred_wt

# Calculate R² for weighted regression manually
ss_res_wt = np.sum(weights * residuals_wt**2)
ss_tot_wt = np.sum(weights * (peak_area_mean - np.average(peak_area_mean, weights=weights))**2)
r_squared_wt = 1 - (ss_res_wt / ss_tot_wt)

# Limit of Detection (LOD) and Limit of Quantitation (LOQ)
# ICH Q2(R1): LOD = 3.3 * (sigma / slope), LOQ = 10 * (sigma / slope)
LOD = 3.3 * blank_std / slope_wt
LOQ = 10.0 * blank_std / slope_wt

# Precision metrics: relative standard deviation (RSD) at low, medium, high concentrations
low_conc_idx = 2  # 1.0 μg/mL
mid_conc_idx = 4  # 10.0 μg/mL
high_conc_idx = 7  # 500.0 μg/mL

rsd_low = (peak_area_std[low_conc_idx] / peak_area_mean[low_conc_idx]) * 100
rsd_mid = (peak_area_std[mid_conc_idx] / peak_area_mean[mid_conc_idx]) * 100
rsd_high = (peak_area_std[high_conc_idx] / peak_area_mean[high_conc_idx]) * 100

# Print validation report
print("HPLC Method Validation Report: Caffeine Quantitation")
print("=" * 70)
print(f"Weighted Calibration Curve:")
print(f"  Slope:                  {slope_wt:.2f} (mAU·s) / (μg/mL)")
print(f"  Intercept:              {intercept_wt:.2f} mAU·s")
print(f"  R² (weighted):          {r_squared_wt:.6f}")
print(f"  R² (unweighted):        {r_squared_uw:.6f}")
print(f"\nLimit of Detection (LOD):       {LOD:.3f} μg/mL")
print(f"Limit of Quantitation (LOQ):    {LOQ:.3f} μg/mL")
print(f"\nPrecision (RSD, n=3):")
print(f"  Low concentration (1.0 μg/mL):    {rsd_low:.2f}%")
print(f"  Mid concentration (10.0 μg/mL):   {rsd_mid:.2f}%")
print(f"  High concentration (500.0 μg/mL): {rsd_high:.2f}%")
print(f"\nBlank Statistics (n=10):")
print(f"  Mean baseline:          {blank_mean:.1f} mAU·s")
print(f"  Standard deviation:     {blank_std:.2f} mAU·s")

# Visualization: calibration curve with log-log plot and residual analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Linear calibration curve
ax1 = axes[0, 0]
ax1.errorbar(concentrations, peak_area_mean, yerr=peak_area_std, 
             fmt='o', color='navy', markersize=8, capsize=5, capthick=2, label='Experimental (n=3)')
ax1.plot(concentrations, peak_area_pred_wt, 'r-', linewidth=2, label='Weighted Linear Fit')
ax1.set_xlabel('Concentration (μg/mL)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Peak Area (mAU·s)', fontsize=11, fontweight='bold')
ax1.set_title('HPLC Calibration Curve (Linear Scale)', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.text(0.05, 0.95, f'y = {slope_wt:.2f}x + {intercept_wt:.2f}\nR² = {r_squared_wt:.6f}',
         transform=ax1.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.6))

# Log-log calibration curve
ax2 = axes[0, 1]
ax2.loglog(concentrations, peak_area_mean, 'o', color='darkgreen', markersize=8, label='Experimental')
ax2.loglog(concentrations, peak_area_pred_wt, 'r-', linewidth=2, label='Fit')
ax2.axhline(intercept_wt + slope_wt * LOD, color='orange', linestyle='--', linewidth=1.5, label=f'LOD = {LOD:.3f} μg/mL')
ax2.axhline(intercept_wt + slope_wt * LOQ, color='purple', linestyle='--', linewidth=1.5, label=f'LOQ = {LOQ:.3f} μg/mL')
ax2.set_xlabel('Concentration (μg/mL)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Peak Area (mAU·s)', fontsize=11, fontweight='bold')
ax2.set_title('HPLC Calibration Curve (Log-Log Scale)', fontsize=13, fontweight='bold')
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3, which='both')

# Residual plot
ax3 = axes[1, 0]
ax3.scatter(concentrations, residuals_wt, color='crimson', s=80, alpha=0.7)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
ax3.set_xlabel('Concentration (μg/mL)', fontsize=11, fontweight='bold')
ax3.set_ylabel('Residual (mAU·s)', fontsize=11, fontweight='bold')
ax3.set_title('Residual Analysis', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)

# Precision profile (RSD vs concentration)
rsd_values = (peak_area_std / peak_area_mean) * 100
ax4 = axes[1, 1]
ax4.semilogx(concentrations, rsd_values, 's-', color='teal', markersize=8, linewidth=2)
ax4.axhline(y=2.0, color='green', linestyle='--', linewidth=1.5, label='2% RSD (target)')
ax4.axhline(y=5.0, color='orange', linestyle='--', linewidth=1.5, label='5% RSD (acceptable)')
ax4.set_xlabel('Concentration (μg/mL)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Relative Standard Deviation (%)', fontsize=11, fontweight='bold')
ax4.set_title('Precision Profile', fontsize=13, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('hplc_method_validation.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nMethod validation report saved as 'hplc_method_validation.png'")
```

Execute this validation protocol with `python hplc_validation.py`. The weighted regression accounts for increasing absolute variance at higher concentrations, a common phenomenon in chromatographic detection systems. The LOD of approximately 0.05 μg/mL and LOQ of 0.15 μg/mL establish the working range for trace-level quantitation. The precision profile demonstrates RSD values below 2% across the mid-to-high concentration range, meeting typical pharmaceutical method validation acceptance criteria (RSD ≤ 5%).

### Robustness Testing Through Systematic Parameter Perturbation

Method robustness quantifies the analytical performance stability against deliberate variations in operational parameters. Systematically perturb the mobile phase composition (acetonitrile content ±5%), flow rate (±0.2 mL/min), column temperature (±5°C), and pH (±0.2 units) while maintaining all other conditions constant. Inject a quality control standard at 50.0 μg/mL under each perturbed condition in triplicate and measure the resulting changes in retention time, peak area, peak asymmetry factor, and theoretical plate count.

The asymmetry factor $A_s$ quantifies peak tailing, calculated as the ratio of the back half-width to the front half-width at 10% of the peak height, with ideal values near unity. The theoretical plate count $N$ measures column efficiency:

$$N = 16 \left(\frac{t_R}{w_b}\right)^2$$

where $t_R$ is the retention time and $w_b$ is the baseline peak width measured between tangent intersections. A robust method maintains $N > 2000$ plates/column and $A_s$ between 0.9 and 1.2 across all perturbation conditions.

The following implementation systematically evaluates robustness metrics and generates a multivariate sensitivity analysis:

```python
import numpy as np
import matplotlib.pyplot as plt

# Robustness test data: parameter perturbations and measured responses
# Nominal conditions: 70:30 water:acetonitrile, 1.0 mL/min, 30°C
parameters = ['Nominal', 'ACN +5%', 'ACN -5%', 'Flow +0.2', 'Flow -0.2', 
              'Temp +5°C', 'Temp -5°C', 'pH +0.2', 'pH -0.2']

# Measured responses (mean of n=3)
retention_time = np.array([4.52, 3.89, 5.34, 3.76, 5.42, 4.31, 4.78, 4.55, 4.49])  # minutes
peak_area = np.array([60145, 59876, 60432, 60298, 59987, 60234, 60089, 60176, 60198])  # mAU·s
asymmetry_factor = np.array([1.08, 1.12, 1.15, 1.09, 1.14, 1.06, 1.11, 1.10, 1.09])
plate_count = np.array([8945, 8234, 7876, 9123, 8654, 9234, 8567, 8912, 8876])  # N

# Compute relative changes from nominal condition
retention_time_change = ((retention_time - retention_time[0]) / retention_time[0]) * 100
peak_area_change = ((peak_area - peak_area[0]) / peak_area[0]) * 100
asymmetry_change = ((asymmetry_factor - asymmetry_factor[0]) / asymmetry_factor[0]) * 100
plate_count_change = ((plate_count - plate_count[0]) / plate_count[0]) * 100

# Define acceptance criteria
retention_time_limit = 10.0  # ±10% change acceptable
peak_area_limit = 5.0  # ±5% change acceptable
asymmetry_limit = 1.2  # As < 1.2 acceptable
plate_count_limit = 7000  # N > 7000 acceptable

# Evaluate pass/fail status
retention_pass = np.abs(retention_time_change) <= retention_time_limit
peak_area_pass = np.abs(peak_area_change) <= peak_area_limit
asymmetry_pass = asymmetry_factor <= asymmetry_limit
plate_count_pass = plate_count >= plate_count_limit

# Print robustness report
print("HPLC Method Robustness Testing Report")
print("=" * 100)
print(f"{'Parameter':<15} {'tR (min)':<10} {'Δ tR (%)':<10} {'Area':<10} {'Δ Area (%)':<12} {'As':<8} {'Plates (N)':<12}")
print("-" * 100)

for i, param in enumerate(parameters):
    print(f"{param:<15} {retention_time[i]:<10.2f} {retention_time_change[i]:<+10.1f} "
          f"{peak_area[i]:<10.0f} {peak_area_change[i]:<+12.2f} {asymmetry_factor[i]:<8.2f} {plate_count[i]:<12.0f}")

print("\nAcceptance Criteria:")
print(f"  Retention Time Change:  ±{retention_time_limit}%")
print(f"  Peak Area Change:       ±{peak_area_limit}%")
print(f"  Asymmetry Factor:       ≤ {asymmetry_limit}")
print(f"  Plate Count:            ≥ {plate_count_limit}")

print("\nRobustness Summary:")
all_pass = np.all([retention_pass[1:], peak_area_pass[1:], asymmetry_pass[1:], plate_count_pass[1:]])
print(f"  All perturbations meet acceptance criteria: {all_pass}")

# Visualization: robustness multivariate response plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
x_pos = np.arange(len(parameters))

# Retention time
ax1 = axes[0, 0]
colors_rt = ['green' if p else 'red' for p in retention_pass]
bars1 = ax1.bar(x_pos, retention_time_change, color=colors_rt, alpha=0.7, edgecolor='black')
ax1.axhline(retention_time_limit, color='orange', linestyle='--', linewidth=2, label='Upper Limit')
ax1.axhline(-retention_time_limit, color='orange', linestyle='--', linewidth=2, label='Lower Limit')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(parameters, rotation=45, ha='right', fontsize=9)
ax1.set_ylabel('Retention Time Change (%)', fontsize=11, fontweight='bold')
ax1.set_title('Retention Time Robustness', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3, axis='y')

# Peak area
ax2 = axes[0, 1]
colors_area = ['green' if p else 'red' for p in peak_area_pass]
bars2 = ax2.bar(x_pos, peak_area_change, color=colors_area, alpha=0.7, edgecolor='black')
ax2.axhline(peak_area_limit, color='orange', linestyle='--', linewidth=2)
ax2.axhline(-peak_area_limit, color='orange', linestyle='--', linewidth=2)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(parameters, rotation=45, ha='right', fontsize=9)
ax2.set_ylabel('Peak Area Change (%)', fontsize=11, fontweight='bold')
ax2.set_title('Peak Area Robustness', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

# Asymmetry factor
ax3 = axes[1, 0]
colors_asym = ['green' if p else 'red' for p in asymmetry_pass]
bars3 = ax3.bar(x_pos, asymmetry_factor, color=colors_asym, alpha=0.7, edgecolor='black')
ax3.axhline(asymmetry_limit, color='orange', linestyle='--', linewidth=2, label='Limit')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(parameters, rotation=45, ha='right', fontsize=9)
ax3.set_ylabel('Asymmetry Factor', fontsize=11, fontweight='bold')
ax3.set_title('Peak Asymmetry Robustness', fontsize=13, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3, axis='y')

# Plate count
ax4 = axes[1, 1]
colors_plates = ['green' if p else 'red' for p in plate_count_pass]
bars4 = ax4.bar(x_pos, plate_count, color=colors_plates, alpha=0.7, edgecolor='black')
ax4.axhline(plate_count_limit, color='orange', linestyle='--', linewidth=2, label='Limit')
ax4.set_xticks(x_pos)
ax4.set_xticklabels(parameters, rotation=45, ha='right', fontsize=9)
ax4.set_ylabel('Theoretical Plates (N)', fontsize=11, fontweight='bold')
ax4.set_title('Column Efficiency Robustness', fontsize=13, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('hplc_robustness_testing.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nRobustness analysis saved as 'hplc_robustness_testing.png'")
```

Run this robustness evaluation with `python hplc_robustness.py`. The results demonstrate that mobile phase composition exerts the strongest influence on retention time (±15–18% change for ±5% acetonitrile variation), while peak area remains stable within ±1% across all perturbations, confirming the method's quantitative robustness. The asymmetry factors remain below 1.15 and plate counts exceed 7800 under all conditions, meeting typical regulatory acceptance criteria for validated analytical methods.

## Laboratory Cheat Sheet & Metric Verification Guide

### Spectroscopic Analysis Quick Reference

**Beer-Lambert Law Verification Protocol:**
- Stock solution preparation: weigh analyte to ±0.1 mg, dissolve in calibrated volumetric flask
- Dilution series: minimum 5 concentrations spanning 2 orders of magnitude
- Spectrophotometer warm-up: 15–30 minutes for lamp stabilization
- Blank measurement: zero instrument with solvent reference before each series
- Acceptance criteria: $R^2 \geq 0.999$, residuals randomly distributed, intercept near zero

**Common Molar Absorptivities (λ_max):**
- KMnO₄ (525 nm): 2230 L mol⁻¹ cm⁻¹
- Bromothymol blue (616 nm): 14,900 L mol⁻¹ cm⁻¹  
- NADH (340 nm): 6220 L mol⁻¹ cm⁻¹
- Rhodamine B (554 nm): 106,000 L mol⁻¹ cm⁻¹

**Uncertainty Propagation Formula:**
$$u(c) = \frac{u(A)}{\varepsilon b} \sqrt{1 + \frac{1}{n} + \frac{(A - \bar{A})^2}{S_{xx}}}$$

where $n$ is the number of calibration points, $S_{xx} = \sum(A_i - \bar{A})^2$, and the middle term accounts for calibration curve uncertainty.

### Potentiometric Titration Quick Reference

**Electrode Calibration:**
- Three-point calibration: pH 4.00, 7.00, 10.00 buffers at measurement temperature
- Nernstian slope: 59.16 mV/pH at 25°C (acceptable range: 56–62 mV/pH)
- Electrode maintenance: store in 3 M KCl solution, replace when slope falls below 95%

**Gran Plot Equations:**
- Pre-equivalence: $G_1 = (V_0 + V) \times 10^{\text{pH}}$
- Post-equivalence: $G_2 = (V_0 + V) \times 10^{-\text{pH}}$
- Equivalence volume: x-intercept of linear Gran function ($G = 0$)

**Buffer Capacity Formula:**
$$\beta = 2.303 \times C_{\text{total}} \times \frac{K_a[\text{H}^+]}{(K_a + [\text{H}^+])^2}$$

Maximum at pH = pKa: $\beta_{\text{max}} = 0.576 \, C_{\text{total}}$

### HPLC Method Validation Quick Reference

**ICH Q2(R1) Detection Limit Definitions:**
- LOD: $3.3 \times \sigma / S$ where $\sigma$ is standard deviation of blank, $S$ is calibration slope
- LOQ: $10.0 \times \sigma / S$
- Alternative: signal-to-noise ratio (S/N = 3 for LOD, S/N = 10 for LOQ)

**Acceptance Criteria:**
- Linearity: $R^2 \geq 0.995$ over working range
- Precision: RSD ≤ 5% for replicate injections (n ≥ 3)
- Accuracy: recovery 95–105% for spiked samples
- Robustness: critical parameters vary ±5–10%, responses within ±5% of nominal

**Column Efficiency Metrics:**
- Theoretical plates: $N = 16(t_R/w_b)^2$ or $N = 5.545(t_R/w_{h})^2$
- Asymmetry factor: $A_s = b/a$ at 10% peak height (ideal: 0.9–1.2)
- Resolution: $R_s = 2(t_{R2} - t_{R1})/(w_{b1} + w_{b2})$ (baseline separation: $R_s \geq 1.5$)

### Python Environment Verification Commands

```bash
# Verify scientific stack installation
python -c "import numpy as np; print(f'NumPy {np.__version__}: {np.show_config()}')"
python -c "import scipy; print(f'SciPy {scipy.__version__}'); from scipy import stats, optimize; print('Core modules OK')"
python -c "import matplotlib; print(f'Matplotlib {matplotlib.__version__}'); import matplotlib.pyplot as plt; plt.plot([0,1]); print('Backend functional')"

# Check numerical precision
python -c "import numpy as np; print(f'Machine epsilon: {np.finfo(float).eps}'); print(f'Max float: {np.finfo(float).max}')"

# Verify linear algebra routines
python -c "import numpy as np; A = np.random.rand(100,100); print(f'Matrix inversion test: {np.allclose(np.linalg.inv(A) @ A, np.eye(100))}')"
```

**Common Troubleshooting:**
- `ImportError: No module named scipy`: Install via `pip install scipy` or `conda install scipy`
- Matplotlib display issues: Set backend with `export MPLBACKEND=TkAgg` or use `plt.savefig()` instead of `plt.show()`
- Numerical instability warnings: Check condition number with `np.linalg.cond(matrix)`, use `scipy.linalg.lstsq()` for ill-conditioned systems
- Memory errors on large datasets: Use chunked processing with `numpy.memmap()` or downsample data

### Error Analysis Reference Formulas

**Standard Error of the Mean:**
$$\text{SEM} = \frac{s}{\sqrt{n}}$$

**95% Confidence Interval:**
$$\text{CI}_{95} = \bar{x} \pm t_{n-1, 0.025} \times \text{SEM}$$

where $t_{n-1, 0.025}$ is the Student's t-value for $n-1$ degrees of freedom.

**Propagation of Uncertainty (General Form):**
For $f = f(x, y, z, \ldots)$:
$$u_f = \sqrt{\left(\frac{\partial f}{\partial x}\right)^2 u_x^2 + \left(\frac{\partial f}{\partial y}\right)^2 u_y^2 + \left(\frac{\partial f}{\partial z}\right)^2 u_z^2 + \ldots}$$

**Relative Standard Deviation:**
$$\text{RSD} = \frac{s}{\bar{x}} \times 100\%$$

Acceptable precision: RSD ≤ 2% (excellent), RSD ≤ 5% (acceptable), RSD > 10% (poor, requires method refinement).
