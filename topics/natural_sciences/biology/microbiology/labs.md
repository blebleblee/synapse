# Operational Verification Labs: Microbiology

## Objective & Laboratory Bench Setup

Microbiology sits at the intersection of biological observation and quantitative measurement, demanding rigorous experimental protocols that transform living systems into measurable physical phenomena. This laboratory guide grounds microbiological investigation in empirical reality: colony growth kinetics obey exponential mathematics, spectrophotometric turbidity measurements quantify cell density through Beer-Lambert optical physics, and metabolic rate determinations apply stoichiometric reaction balances. The practitioner must master aseptic technique, calibrate optical instruments to baseline standards, and analyze living cultures as dynamic chemical reactors whose behavior follows thermodynamic and kinetic laws.

The experimental bench requires physical microbiological apparatus integrated with computational data acquisition. Prepare a laminar flow hood or Bunsen burner flame zone for aseptic culture work. Establish a temperature-controlled incubator calibrated to ±0.5°C accuracy for bacterial growth at 37°C or yeast fermentation at 30°C. Mount a spectrophotometer capable of 600 nm optical density measurements with cuvette path length verified at exactly 1.0 cm, ensuring Lambert's law applicability. Equip the bench with calibrated micropipettes (P20, P200, P1000) verified against gravimetric water density standards (1.0 mg = 1.0 µL at 20°C). Install a compound light microscope with 100× oil immersion objective and calibrated ocular micrometer for direct cell enumeration via hemocytometer counting chambers. Stock sterile culture media: nutrient broth with peptone nitrogen source and glucose carbon substrate, tryptic soy agar plates for colony isolation, and defined minimal media enabling metabolic flux analysis through single-variable substrate manipulation.

The computational environment must handle time-series biological data with statistical rigor. Verify Python 3.8+ installation with NumPy for array-based cell density calculations, SciPy for exponential growth curve fitting via nonlinear least squares regression, and Matplotlib for logarithmic-scale growth plots revealing exponential kinetics. Execute verification with `python -c 'import numpy as np; import scipy.optimize; import matplotlib.pyplot as plt; print(f"NumPy {np.__version__}, SciPy {scipy.__version__}, Matplotlib {matplotlib.__version__}")'` confirming operational library versions. Establish Jupyter notebook environment for inline data visualization during multi-hour growth curve experiments, enabling real-time parameter estimation as optical density measurements accumulate.

Prepare reference microorganisms with characterized growth parameters for calibration and validation. *Escherichia coli* K-12 serves as the primary bacterial model with doubling time approximately 20 minutes under optimal aerobic conditions at 37°C in rich media, reaching stationary phase at OD₆₀₀ ≈ 1.0–1.5. *Saccharomyces cerevisiae* laboratory strains provide eukaryotic comparison with doubling time near 90 minutes at 30°C in glucose media. Maintain frozen glycerol stocks at -80°C for reproducible culture revival, streaking onto agar plates 24 hours before each experimental session to obtain fresh overnight seed cultures entering exponential phase.

The laboratory session workflow integrates physical microbiology with quantitative data science: aseptic culture inoculation initiates the biological system, time-resolved spectrophotometric monitoring captures growth dynamics as optical density vectors, Python curve-fitting algorithms extract kinetic parameters (specific growth rate μ, lag time λ, carrying capacity K), and statistical uncertainty analysis quantifies measurement precision through replicate variance and propagation of instrumental error. This practicality-first methodology transforms qualitative microbiology into rigorous physical science grounded in experimental measurement and mathematical modeling.

## Exercise 1: Empirical Observation & Measurement Protocol

The foundational microbiological measurement quantifies bacterial population growth through spectrophotometric turbidity monitoring, establishing the relationship between optical density and cell number while extracting exponential growth kinetics from time-series data. This exercise demands precise aseptic technique to prevent contamination artifacts, calibrated optical measurements to ensure Beer-Lambert law validity, and computational analysis to transform raw absorbance readings into biologically meaningful growth parameters.

Begin with culture preparation under strict aseptic conditions. Retrieve an *E. coli* K-12 glycerol stock from -80°C storage and immediately streak onto a tryptic soy agar plate using a sterile inoculation loop, working within the sterile field of a laminar flow hood or beside a Bunsen burner flame. Incubate the plate inverted at 37°C for 16–18 hours until individual colonies appear with 1–2 mm diameter, representing clonal populations derived from single cells. Select a well-isolated colony and inoculate 5 mL of sterile nutrient broth in a 50 mL Erlenmeyer flask, covering with aluminum foil to permit gas exchange while excluding airborne contaminants. Incubate with rotary shaking at 200 rpm and 37°C for 12–14 hours, generating an overnight culture in mid-exponential phase with OD₆₀₀ approximately 0.8–1.2. This seed culture provides the physiologically active inoculum required for reproducible growth kinetics.

Prepare the experimental growth culture by diluting the overnight seed 1:100 into fresh pre-warmed nutrient broth. Measure 0.5 mL of seed culture with a calibrated P1000 micropipette and transfer into 49.5 mL of sterile broth in a 250 mL baffled flask, creating a starting cell density near 10⁶ cells/mL with negligible lag phase. Record the exact inoculation time as t₀ = 0 minutes. Immediately transfer 1.0 mL into a disposable plastic cuvette and measure baseline optical density at 600 nm wavelength (OD₆₀₀) using a spectrophotometer blanked against sterile media. Record this initial measurement as OD₀, typically 0.01–0.03 for a 1:100 dilution. Place the flask in a 37°C shaking incubator at 200 rpm to ensure aerobic growth conditions with dissolved oxygen above 40% saturation.

Execute time-resolved optical density measurements at precisely controlled intervals. Sample the culture every 30 minutes for the first 4 hours, capturing exponential phase growth dynamics. At each timepoint, aseptically remove 1.0 mL into a clean cuvette, measure OD₆₀₀, and immediately return the sample to the flask to avoid volume loss artifacts. Continue hourly sampling for an additional 6 hours to observe the transition into stationary phase as nutrient depletion slows growth. Record all measurements in a structured data table with columns for time (minutes), optical density (OD₆₀₀), and temperature (°C) to capture any incubator fluctuations affecting growth rate.

Validate the Beer-Lambert law relationship between optical density and cell concentration through serial dilution analysis. At the timepoint where culture OD₆₀₀ reaches approximately 0.6 (mid-exponential phase), prepare a dilution series: undiluted, 1:2, 1:4, 1:8, 1:16 dilutions in sterile broth. Measure OD₆₀₀ for each dilution and verify linear proportionality: a perfect 1:2 dilution should yield exactly half the optical density. Deviation from linearity above OD₆₀₀ ≈ 1.0 indicates detector saturation or light scattering nonlinearity, requiring sample dilution for accurate quantification.

Perform direct microscopic cell enumeration to convert optical density into absolute cell concentration. At OD₆₀₀ = 0.6, dilute the culture 1:1000 in sterile saline (10 µL culture + 990 µL saline in two serial 1:10 steps). Load 10 µL into a Neubauer hemocytometer chamber with 0.1 mm depth and 0.0025 mm² counting grid squares. Under 400× magnification, count individual cells in 25 small squares of the central grid. Calculate cell concentration as:

$$N = \frac{\text{cells counted}}{25} \times 10^4 \times \text{dilution factor} \text{ cells/mL}$$

For example, counting 180 cells across 25 squares at 1:10,000 dilution yields N = (180/25) × 10⁴ × 10⁴ = 7.2 × 10⁸ cells/mL at OD₆₀₀ = 0.6, establishing the empirical conversion factor: 1.0 OD₆₀₀ unit ≈ 1.2 × 10⁹ cells/mL for *E. coli* in this optical path length.

Analyze growth kinetics computationally by fitting the exponential growth model to optical density time series data. The bacterial population in exponential phase follows:

$$N(t) = N_0 e^{\mu t}$$

where N(t) represents cell density at time t, N₀ denotes initial density at inoculation, and μ denotes the specific growth rate (h⁻¹). Since optical density serves as a proxy for cell density within the linear range, the equivalent OD growth equation becomes:

$$\text{OD}(t) = \text{OD}_0 e^{\mu t}$$

Taking natural logarithms linearizes the relationship:

$$\ln(\text{OD}(t)) = \ln(\text{OD}_0) + \mu t$$

Create a Python analysis script to extract μ from experimental data. Store time (minutes converted to hours) and OD₆₀₀ measurements in NumPy arrays, compute natural logarithm of OD values, and apply linear regression to the exponential phase region (typically OD₆₀₀ from 0.05 to 0.8):

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress

# Experimental data: time in minutes, OD600 measurements
time_min = np.array([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 
                     330, 360, 420, 480, 540, 600])
od600 = np.array([0.025, 0.035, 0.052, 0.078, 0.118, 0.178, 0.268, 0.401, 
                  0.598, 0.845, 1.102, 1.285, 1.401, 1.489, 1.512, 1.518, 1.520])

# Convert time to hours
time_h = time_min / 60.0

# Identify exponential phase (OD600 between 0.05 and 0.8)
exp_phase_mask = (od600 >= 0.05) & (od600 <= 0.8)
time_exp = time_h[exp_phase_mask]
od_exp = od600[exp_phase_mask]

# Linear regression on log-transformed data
ln_od_exp = np.log(od_exp)
slope, intercept, r_value, p_value, std_err = linregress(time_exp, ln_od_exp)

# Specific growth rate (h^-1) is the slope
mu = slope
doubling_time = np.log(2) / mu  # hours

print(f"Specific growth rate μ = {mu:.3f} h⁻¹")
print(f"Doubling time t_d = {doubling_time:.1f} minutes")
print(f"R² = {r_value**2:.4f}")
print(f"Standard error = {std_err:.4f}")

# Fit full logistic growth model to capture stationary phase
def logistic_growth(t, od0, mu, od_max):
    """Logistic growth: OD(t) = od_max / (1 + (od_max/od0 - 1)*exp(-mu*t))"""
    return od_max / (1 + (od_max / od0 - 1) * np.exp(-mu * t))

# Initial parameter guesses: od0=0.025, mu=1.5, od_max=1.5
popt, pcov = curve_fit(logistic_growth, time_h, od600, 
                       p0=[0.025, 1.5, 1.5], maxfev=10000)
od0_fit, mu_fit, od_max_fit = popt
perr = np.sqrt(np.diag(pcov))

print(f"\nLogistic model parameters:")
print(f"OD₀ = {od0_fit:.4f} ± {perr[0]:.4f}")
print(f"μ = {mu_fit:.3f} ± {perr[1]:.3f} h⁻¹")
print(f"OD_max = {od_max_fit:.3f} ± {perr[2]:.3f}")

# Generate fitted curves
time_fit = np.linspace(0, 10, 200)
od_fit = logistic_growth(time_fit, *popt)

# Plot experimental data and model fits
plt.figure(figsize=(12, 5))

# Panel 1: Semi-log plot showing exponential phase
plt.subplot(1, 2, 1)
plt.semilogy(time_h, od600, 'o', markersize=8, label='Experimental data')
plt.semilogy(time_exp, od_exp, 'ro', markersize=10, label='Exponential phase')
exp_fit = np.exp(intercept) * np.exp(slope * time_fit)
plt.semilogy(time_fit, exp_fit, 'r--', linewidth=2, 
             label=f'Exponential fit: μ={mu:.3f} h⁻¹')
plt.xlabel('Time (hours)', fontsize=12)
plt.ylabel('OD₆₀₀ (log scale)', fontsize=12)
plt.title('Exponential Growth Phase Analysis', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

# Panel 2: Full growth curve with logistic model
plt.subplot(1, 2, 2)
plt.plot(time_h, od600, 'o', markersize=8, label='Experimental data')
plt.plot(time_fit, od_fit, 'b-', linewidth=2, label='Logistic model')
plt.axhline(y=od_max_fit, color='gray', linestyle=':', 
            label=f'Carrying capacity: {od_max_fit:.2f}')
plt.xlabel('Time (hours)', fontsize=12)
plt.ylabel('OD₆₀₀', fontsize=12)
plt.title('Complete Growth Curve with Stationary Phase', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('ecoli_growth_kinetics.png', dpi=300, bbox_inches='tight')
plt.show()

# Calculate generation time distribution from replicate measurements
# Simulate experimental uncertainty with 3 replicate cultures
np.random.seed(42)
n_replicates = 3
mu_replicates = np.random.normal(mu, std_err, n_replicates)
td_replicates = np.log(2) / mu_replicates * 60  # minutes

print(f"\nReplicate doubling times:")
for i, td in enumerate(td_replicates, 1):
    print(f"  Replicate {i}: {td:.1f} minutes")
print(f"Mean ± SD: {td_replicates.mean():.1f} ± {td_replicates.std():.1f} minutes")
```

This computational analysis extracts quantitative growth parameters from raw optical measurements. The linear regression on log-transformed exponential phase data yields μ ≈ 1.8 h⁻¹ for healthy *E. coli* in nutrient broth at 37°C, corresponding to a doubling time of approximately 23 minutes. The R² value near 0.99 validates exponential kinetics during this growth phase. The logistic model extension captures nutrient depletion effects as the culture transitions into stationary phase, with the carrying capacity parameter OD_max representing the maximum sustainable cell density (typically 1.5–2.0 OD₆₀₀ units for batch culture in standard media).

Quantify measurement uncertainty through error propagation analysis. Spectrophotometer precision typically exhibits standard deviation σ_OD ≈ 0.005 OD units for replicate readings. When computing specific growth rate from the slope of ln(OD) versus time, the uncertainty propagates as:

$$\sigma_\mu = \sigma_{\text{slope}} = \sqrt{\frac{\sum (y_i - \hat{y}_i)^2}{(n-2) \sum (x_i - \bar{x})^2}}$$

where n denotes the number of measurements in the exponential phase. For a typical 7-point exponential phase dataset spanning 4 hours, this yields σ_μ ≈ 0.05 h⁻¹, resulting in doubling time uncertainty of approximately ±1 minute. Biological variation between replicate cultures typically dominates over instrumental error, with culture-to-culture coefficient of variation near 5–8% for growth rate measurements.

Validate culture purity through Gram staining and microscopic morphology assessment. At experiment completion, prepare a heat-fixed smear on a glass slide, stain with crystal violet and safranin following standard Gram protocol, and examine under 1000× oil immersion. *E. coli* appears as small (1–2 µm length) Gram-negative (pink) rods, often in short chains during exponential growth. Any alternative morphologies (cocci, long filaments, mixed Gram reactions) indicate contamination requiring culture discard and experimental restart with fresh aseptic technique.

This exercise establishes the complete measurement chain from living bacterial culture to quantitative kinetic parameters: aseptic handling preserves biological integrity, spectrophotometry converts cell density into measurable optical physics, curve-fitting algorithms extract growth rate constants, and error analysis quantifies experimental precision. The practitioner gains empirical mastery of microbial growth quantification while recognizing optical density as a proxy observable governed by Beer-Lambert optical principles and exponential population dynamics.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

Microbiological systems respond quantitatively to environmental perturbations, with metabolic rate and growth kinetics following predictable functional relationships to temperature, substrate concentration, and inhibitor presence. This exercise systematically varies experimental parameters to construct calibration curves and response surfaces, revealing the physical chemistry underlying microbial physiology while demonstrating the power of factorial experimental design in biological research.

**Temperature Dependence of Growth Rate: Arrhenius Activation Energy**

Bacterial metabolism obeys chemical kinetic principles, with enzymatic reaction rates exhibiting exponential temperature dependence described by the Arrhenius equation. Measure *E. coli* specific growth rate across a temperature range from 25°C to 42°C to extract the activation energy for the rate-limiting metabolic processes governing cell division.

Prepare six identical cultures by diluting a single overnight *E. coli* seed culture 1:100 into 50 mL nutrient broth in six separate 250 mL flasks. Immediately transfer flasks to six temperature-controlled shaking incubators set to 25°C, 30°C, 33°C, 37°C, 40°C, and 42°C, all maintaining 200 rpm agitation. Monitor OD₆₀₀ every 30 minutes for each culture over 8 hours, extending measurement intervals as growth rate decreases at temperature extremes. Record incubator temperatures with a calibrated thermometer at each sampling timepoint to verify ±0.5°C stability.

Analyze each temperature dataset independently using the exponential phase linear regression method from Exercise 1, extracting specific growth rate μ(T) at each temperature. The Arrhenius relationship predicts:

$$\mu(T) = A e^{-E_a / RT}$$

where A represents the pre-exponential frequency factor, E_a denotes the activation energy (J/mol), R is the universal gas constant (8.314 J mol⁻¹ K⁻¹), and T is absolute temperature (K). Taking natural logarithms linearizes the equation:

$$\ln(\mu) = \ln(A) - \frac{E_a}{R} \cdot \frac{1}{T}$$

Plot ln(μ) versus 1/T to obtain a linear relationship with slope -E_a/R. Implement the analysis in Python:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Experimental data: temperature (°C) and measured specific growth rate (h^-1)
temp_celsius = np.array([25.0, 30.0, 33.0, 37.0, 40.0, 42.0])
mu_measured = np.array([0.52, 0.89, 1.21, 1.82, 2.15, 1.95])
mu_std = np.array([0.04, 0.06, 0.08, 0.09, 0.12, 0.15])  # Standard deviations

# Convert to Kelvin and compute inverse temperature
temp_kelvin = temp_celsius + 273.15
inv_temp = 1000.0 / temp_kelvin  # 1/T in units of 1000/K for convenient plotting

# Natural log of growth rate
ln_mu = np.log(mu_measured)
ln_mu_err = mu_std / mu_measured  # Propagated uncertainty in ln(mu)

# Linear regression for Arrhenius plot
# Exclude 42°C data if it shows thermal deactivation
arrhenius_mask = temp_celsius <= 40.0
slope, intercept, r_value, p_value, std_err = linregress(
    inv_temp[arrhenius_mask], ln_mu[arrhenius_mask])

# Extract activation energy
R = 8.314  # J/(mol·K)
Ea = -slope * R * 1000  # Convert from 1000/K units, result in J/mol
Ea_kJ = Ea / 1000  # Convert to kJ/mol
Ea_err = std_err * R * 1000 / 1000

# Pre-exponential factor
A = np.exp(intercept)

print(f"Arrhenius Analysis:")
print(f"Activation Energy E_a = {Ea_kJ:.1f} ± {Ea_err:.1f} kJ/mol")
print(f"Pre-exponential factor A = {A:.2e} h⁻¹")
print(f"R² = {r_value**2:.4f}")

# Typical activation energy for bacterial growth: 50-80 kJ/mol
print(f"\nInterpretation:")
if 50 <= Ea_kJ <= 80:
    print("E_a within expected range for metabolic enzyme-limited growth")
elif Ea_kJ < 50:
    print("Low E_a suggests diffusion or transport limitation")
else:
    print("High E_a may indicate protein denaturation effects")

# Temperature coefficient Q10 (rate increase per 10°C)
# Compare rates at 30°C and 40°C
mu_30 = A * np.exp(-Ea / (R * (30 + 273.15)))
mu_40 = A * np.exp(-Ea / (R * (40 + 273.15)))
Q10 = (mu_40 / mu_30) ** (10 / (40 - 30))
print(f"\nQ₁₀ coefficient = {Q10:.2f}")

# Generate Arrhenius plot
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.errorbar(inv_temp, ln_mu, yerr=ln_mu_err, fmt='o', markersize=8, 
             capsize=5, capthick=2, label='Experimental data')
# Fitted line
inv_temp_fit = np.linspace(inv_temp.min() - 0.1, inv_temp.max() + 0.1, 100)
ln_mu_fit = intercept + slope * inv_temp_fit
plt.plot(inv_temp_fit, ln_mu_fit, 'r--', linewidth=2, 
         label=f'Arrhenius fit: E_a={Ea_kJ:.1f} kJ/mol')
plt.xlabel('1000/T (K⁻¹)', fontsize=12)
plt.ylabel('ln(μ) (ln(h⁻¹))', fontsize=12)
plt.title('Arrhenius Plot: Growth Rate vs Temperature', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.errorbar(temp_celsius, mu_measured, yerr=mu_std, fmt='o', markersize=8,
             capsize=5, capthick=2, label='Experimental data')
# Fitted Arrhenius curve
temp_fit_celsius = np.linspace(20, 45, 100)
temp_fit_kelvin = temp_fit_celsius + 273.15
mu_fit = A * np.exp(-Ea / (R * temp_fit_kelvin))
plt.plot(temp_fit_celsius, mu_fit, 'b-', linewidth=2, label='Arrhenius model')
plt.axvline(x=37, color='green', linestyle=':', label='Optimal (37°C)')
plt.xlabel('Temperature (°C)', fontsize=12)
plt.ylabel('Specific growth rate μ (h⁻¹)', fontsize=12)
plt.title('Growth Rate Response to Temperature', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('temperature_growth_response.png', dpi=300, bbox_inches='tight')
plt.show()
```

Typical *E. coli* activation energy ranges from 60–75 kJ/mol, reflecting the temperature sensitivity of rate-limiting ribosomal protein synthesis and DNA replication machinery. The Q₁₀ coefficient typically falls near 2.0–2.5, meaning growth rate approximately doubles for each 10°C temperature increase within the physiological range. The decline in growth rate above 40°C indicates the onset of thermal protein denaturation and membrane dysfunction, defining the organism's upper temperature tolerance limit.

**Substrate Concentration Dependence: Michaelis-Menten Kinetics**

Microbial growth rate exhibits saturable dependence on limiting nutrient concentration, following Monod kinetics analogous to enzyme-substrate Michaelis-Menten relationships. Construct a glucose-limitation calibration curve to extract the half-saturation constant K_s, representing the substrate concentration at half-maximal growth rate.

Prepare a chemically defined minimal medium containing essential salts (KH₂PO₄, Na₂HPO₄, MgSO₄, NH₄Cl) and trace elements, but omitting glucose carbon source. Filter-sterilize and aliquot into six 50 mL volumes. Prepare a sterile 20% (w/v) glucose stock solution and add to each medium aliquot to achieve final concentrations: 0.01%, 0.02%, 0.05%, 0.10%, 0.20%, and 0.50% glucose (equivalent to 0.56 mM, 1.11 mM, 2.78 mM, 5.55 mM, 11.1 mM, 27.8 mM). Inoculate each medium 1:100 with an *E. coli* culture pre-adapted to minimal medium by 24-hour prior growth under identical conditions (starting density ∼10⁷ cells/mL), ensuring cells possess the enzymatic machinery for glucose utilization without lag-phase enzyme induction delays.

Monitor growth in each glucose concentration through OD₆₀₀ measurement every 30 minutes over 12 hours at 37°C with shaking. Extract specific growth rate μ from the exponential phase of each curve. The Monod equation predicts:

$$\mu(S) = \mu_{\max} \frac{S}{K_s + S}$$

where S denotes substrate concentration (mM glucose), μ_max represents maximum growth rate at saturating substrate, and K_s is the half-saturation constant. Fit this hyperbolic relationship using nonlinear regression:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Experimental data: glucose concentration (mM) and growth rate (h^-1)
glucose_mM = np.array([0.56, 1.11, 2.78, 5.55, 11.1, 27.8])
mu_obs = np.array([0.28, 0.48, 0.81, 1.15, 1.42, 1.48])
mu_obs_std = np.array([0.03, 0.04, 0.05, 0.06, 0.07, 0.08])

# Monod kinetic model
def monod_kinetics(S, mu_max, Ks):
    """Monod equation: mu = mu_max * S / (Ks + S)"""
    return mu_max * S / (Ks + S)

# Nonlinear curve fitting
popt, pcov = curve_fit(monod_kinetics, glucose_mM, mu_obs, 
                       p0=[1.5, 2.0], sigma=mu_obs_std, absolute_sigma=True)
mu_max_fit, Ks_fit = popt
perr = np.sqrt(np.diag(pcov))

print(f"Monod Kinetic Parameters:")
print(f"μ_max = {mu_max_fit:.3f} ± {perr[0]:.3f} h⁻¹")
print(f"K_s = {Ks_fit:.3f} ± {perr[1]:.3f} mM glucose")
print(f"\nAt half-saturation (S = K_s = {Ks_fit:.2f} mM):")
print(f"μ = {mu_max_fit/2:.3f} h⁻¹ (50% of μ_max)")

# Generate fitted curve
glucose_fit = np.logspace(-1, 2, 200)  # 0.1 to 100 mM
mu_fit = monod_kinetics(glucose_fit, mu_max_fit, Ks_fit)

# Plot substrate response curve
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.errorbar(glucose_mM, mu_obs, yerr=mu_obs_std, fmt='o', markersize=10,
             capsize=5, capthick=2, label='Experimental data')
plt.plot(glucose_fit, mu_fit, 'b-', linewidth=2, label='Monod model')
plt.axhline(y=mu_max_fit, color='red', linestyle=':', 
            label=f'μ_max = {mu_max_fit:.2f} h⁻¹')
plt.axvline(x=Ks_fit, color='green', linestyle=':', 
            label=f'K_s = {Ks_fit:.2f} mM')
plt.axhline(y=mu_max_fit/2, color='gray', linestyle=':', alpha=0.5)
plt.xlabel('Glucose concentration (mM)', fontsize=12)
plt.ylabel('Specific growth rate μ (h⁻¹)', fontsize=12)
plt.title('Monod Kinetics: Glucose-Limited Growth', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.xscale('log')

# Lineweaver-Burk double reciprocal plot for validation
plt.subplot(1, 2, 2)
inv_glucose = 1.0 / glucose_mM
inv_mu = 1.0 / mu_obs
# Linear fit: 1/mu = (Ks/mu_max)*(1/S) + 1/mu_max
slope_lb, intercept_lb = np.polyfit(inv_glucose, inv_mu, 1)
Ks_lb = slope_lb / intercept_lb
mu_max_lb = 1.0 / intercept_lb

plt.plot(inv_glucose, inv_mu, 'o', markersize=10, label='Experimental data')
inv_glucose_fit = np.linspace(0, inv_glucose.max()*1.1, 100)
inv_mu_fit = slope_lb * inv_glucose_fit + intercept_lb
plt.plot(inv_glucose_fit, inv_mu_fit, 'r--', linewidth=2,
         label=f'Linear fit: K_s={Ks_lb:.2f} mM')
plt.xlabel('1/[Glucose] (mM⁻¹)', fontsize=12)
plt.ylabel('1/μ (h)', fontsize=12)
plt.title('Lineweaver-Burk Plot (Double Reciprocal)', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('glucose_limitation_kinetics.png', dpi=300, bbox_inches='tight')
plt.show()

# Calculate yield coefficient: biomass produced per glucose consumed
# Assuming glucose depletion at stationary phase
od_max_per_glucose = np.array([0.15, 0.28, 0.62, 1.18, 1.85, 2.02])
Y_XS = od_max_per_glucose / glucose_mM  # OD units per mM glucose
print(f"\nBiomass Yield Coefficient:")
print(f"Y_X/S = {Y_XS.mean():.3f} ± {Y_XS.std():.3f} OD/mM glucose")
```

Typical *E. coli* K_s values for glucose range from 0.5–3 mM, indicating high-affinity glucose transport systems enable efficient growth at low substrate concentrations. The maximum specific growth rate μ_max near 1.5 h⁻¹ in minimal medium falls below the 1.8 h⁻¹ observed in rich nutrient broth, reflecting metabolic overhead of biosynthetic pathway enzyme expression when amino acids must be synthesized de novo.

**Antibiotic Inhibition: Minimum Inhibitory Concentration Determination**

Quantify the bacteriostatic effect of ampicillin on *E. coli* growth by measuring the minimum inhibitory concentration (MIC) through a dose-response curve. Prepare a two-fold dilution series of ampicillin sodium salt in sterile water: 128, 64, 32, 16, 8, 4, 2, 1, 0.5 µg/mL. Inoculate 96-well microtiter plates with 200 µL per well containing nutrient broth, ampicillin at the designated concentration, and 1:100 diluted *E. coli* overnight culture (approximately 10⁷ cells/mL inoculum). Include positive control wells (no antibiotic) and negative control wells (sterile media only). Incubate plates at 37°C in a microplate reader with continuous orbital shaking, measuring OD₆₀₀ every 15 minutes for 18 hours.

Analyze inhibition curves by calculating fractional growth relative to untreated control. Define fractional growth as the ratio of maximum OD₆₀₀ reached in antibiotic-treated wells to the maximum OD₆₀₀ in control wells. Fit a four-parameter logistic (4PL) dose-response model:

$$\text{Fractional Growth} = \text{Bottom} + \frac{\text{Top} - \text{Bottom}}{1 + 10^{(\log_{10} IC_{50} - \log_{10}[\text{Amp}]) \cdot \text{Hill slope}}}$$

where IC₅₀ represents the concentration producing 50% growth inhibition (approximating MIC), Hill slope describes the steepness of the dose-response transition, Top denotes fractional growth at zero antibiotic (normalized to 1.0), and Bottom represents complete inhibition baseline (near 0.0).

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Experimental data: ampicillin concentration (µg/mL) and fractional growth
amp_conc = np.array([0, 0.5, 1, 2, 4, 8, 16, 32, 64, 128])
frac_growth = np.array([1.00, 0.98, 0.95, 0.91, 0.78, 0.42, 0.08, 0.02, 0.01, 0.01])
frac_growth_std = np.array([0.05, 0.06, 0.05, 0.07, 0.08, 0.09, 0.03, 0.01, 0.005, 0.005])

# Four-parameter logistic model
def dose_response_4pl(x, bottom, top, ic50, hill_slope):
    """4PL dose-response: y = bottom + (top - bottom)/(1 + 10^((log10(ic50) - log10(x)) * hill_slope))"""
    return bottom + (top - bottom) / (1 + 10**((np.log10(ic50) - np.log10(x + 1e-9)) * hill_slope))

# Fit excluding zero concentration (log scale issues)
mask = amp_conc > 0
popt, pcov = curve_fit(dose_response_4pl, amp_conc[mask], frac_growth[mask],
                       p0=[0.0, 1.0, 8.0, 2.0], maxfev=10000)
bottom, top, ic50, hill_slope = popt
perr = np.sqrt(np.diag(pcov))

print(f"Dose-Response Analysis:")
print(f"IC₅₀ (MIC) = {ic50:.2f} ± {perr[2]:.2f} µg/mL ampicillin")
print(f"Hill slope = {hill_slope:.2f} ± {perr[3]:.2f}")
print(f"Top (max growth) = {top:.3f} ± {perr[1]:.3f}")
print(f"Bottom (full inhibition) = {bottom:.3f} ± {perr[0]:.3f}")

# Generate fitted curve
amp_fit = np.logspace(-1, 2.5, 200)  # 0.1 to 300 µg/mL
frac_fit = dose_response_4pl(amp_fit, *popt)

# Plot dose-response curve
plt.figure(figsize=(10, 6))
plt.errorbar(amp_conc[amp_conc > 0], frac_growth[amp_conc > 0], 
             yerr=frac_growth_std[amp_conc > 0],
             fmt='o', markersize=10, capsize=5, capthick=2, label='Experimental data')
plt.plot(amp_fit, frac_fit, 'b-', linewidth=2, label='4PL model fit')
plt.axhline(y=0.5, color='red', linestyle=':', label='50% inhibition')
plt.axvline(x=ic50, color='green', linestyle=':', label=f'IC₅₀ = {ic50:.1f} µg/mL')
plt.xlabel('Ampicillin concentration (µg/mL)', fontsize=12)
plt.ylabel('Fractional growth (OD_max / OD_control)', fontsize=12)
plt.title('Antibiotic Dose-Response: Ampicillin Inhibition of E. coli', fontsize=14)
plt.xscale('log')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('ampicillin_dose_response.png', dpi=300, bbox_inches='tight')
plt.show()

# Calculate MIC as lowest concentration with <10% growth
mic_threshold = 0.10
mic_observed = amp_conc[frac_growth <= mic_threshold].min()
print(f"\nMIC (observed, <10% growth threshold) = {mic_observed:.1f} µg/mL")
```

The IC₅₀ value typically falls near 6–10 µg/mL for ampicillin-sensitive *E. coli* strains, while the clinical MIC breakpoint (CLSI standard) is defined at ≤8 µg/mL for susceptibility. The Hill slope near 2.0 indicates cooperative inhibition kinetics, potentially reflecting multiple penicillin-binding protein targets with varying affinities. Resistant strains harboring β-lactamase genes exhibit IC₅₀ values exceeding 128 µg/mL, providing quantitative discrimination between susceptible and resistant phenotypes.

This parameter variation exercise demonstrates systematic experimental design principles: temperature sweeps reveal activation energies governing metabolic rate-limiting steps, substrate titrations extract Michaelis-Menten constants defining nutrient affinity, and dose-response curves quantify drug potency through IC₅₀ determination. Each calibration curve transforms qualitative microbiological observation into quantitative physical chemistry, enabling predictive modeling of microbial behavior under environmental perturbation.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

Microbiological systems exhibit nonlinear responses at environmental extremes, with growth transitions, metabolic regime shifts, and cellular viability limits defining the operational boundaries of life. This exercise probes boundary conditions through systematic stress testing while implementing rigorous statistical analysis to quantify measurement uncertainty and biological variability, distinguishing instrumental error from genuine population heterogeneity.

**pH Stress Response: Proton Motive Force Disruption**

Bacterial cytoplasmic pH homeostasis depends on active proton pumping to maintain intracellular near-neutrality despite external pH fluctuations. Measure *E. coli* viability and growth kinetics across extreme pH values to identify the limits of proton motive force compensation and the onset of irreversible acid or alkaline damage.

Prepare citrate-phosphate buffer systems to achieve stable pH values: 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0 (neutral control), 7.5, 8.0, 8.5, 9.0, 9.5. Sterilize buffers by autoclaving or filtration and add nutrients (peptone, yeast extract, glucose) to create buffered growth media. Verify pH with a calibrated electrode before and after autoclaving, adjusting with sterile HCl or NaOH to maintain ±0.1 pH unit accuracy. Inoculate each medium with 1:100 diluted overnight *E. coli* culture and monitor growth via OD₆₀₀ measurements every hour for 12 hours at 37°C.

Quantify cell viability through colony-forming unit (CFU) enumeration at each pH condition. At 4 hours post-inoculation (mid-exponential phase for control cultures), perform serial 10-fold dilutions in sterile phosphate-buffered saline (PBS pH 7.2) to dilution factors of 10⁻⁴ to 10⁻⁷. Plate 100 µL of each dilution onto tryptic soy agar plates in triplicate, spread with sterile glass rods, and incubate at 37°C for 18–24 hours. Count colonies on plates yielding 30–300 colonies per plate (statistically valid range) and calculate viable cell concentration:

$$\text{CFU/mL} = \frac{\text{colony count}}{\text{volume plated (mL)} \times \text{dilution factor}}$$

Compare viability at each pH to the neutral pH control to determine the pH-dependent survival fraction:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

# Experimental data: pH values, growth rates, and viable cell counts
ph_values = np.array([4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5])
mu_measured = np.array([0.0, 0.12, 0.45, 0.89, 1.35, 1.68, 1.82, 1.71, 1.42, 0.78, 0.21, 0.0])
cfu_per_ml = np.array([1.2e5, 4.5e6, 2.8e7, 1.5e8, 5.2e8, 8.1e8, 9.2e8, 7.8e8, 4.9e8, 1.1e8, 8.3e6, 3.2e5])

# Normalize viability to neutral pH control
cfu_control = cfu_per_ml[ph_values == 7.0][0]
survival_fraction = cfu_per_ml / cfu_control

# Standard deviations from triplicate measurements
mu_std = np.array([0.0, 0.02, 0.05, 0.08, 0.10, 0.12, 0.10, 0.11, 0.09, 0.07, 0.03, 0.0])
cfu_std = cfu_per_ml * 0.15  # 15% CV typical for plate counting

print("pH Stress Response Analysis:")
print(f"Optimal pH range (μ > 1.5 h⁻¹): {ph_values[(mu_measured > 1.5)].min():.1f} - {ph_values[(mu_measured > 1.5)].max():.1f}")
print(f"pH tolerance limits (μ > 0.1 h⁻¹): {ph_values[(mu_measured > 0.1)].min():.1f} - {ph_values[(mu_measured > 0.1)].max():.1f}")
print(f"Lethal pH extremes (survival < 1%): pH < {ph_values[survival_fraction < 0.01].min():.1f} or pH > {ph_values[survival_fraction < 0.01].max():.1f}")

# Plot dual-axis pH response
fig, ax1 = plt.subplots(figsize=(10, 6))

color_growth = 'tab:blue'
ax1.set_xlabel('pH', fontsize=12)
ax1.set_ylabel('Specific growth rate μ (h⁻¹)', color=color_growth, fontsize=12)
ax1.errorbar(ph_values, mu_measured, yerr=mu_std, fmt='o-', markersize=8,
             color=color_growth, capsize=5, capthick=2, linewidth=2, label='Growth rate')
ax1.tick_params(axis='y', labelcolor=color_growth)
ax1.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
ax1.axvspan(6.5, 7.5, alpha=0.1, color='green', label='Optimal pH zone')
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
color_viability = 'tab:red'
ax2.set_ylabel('Survival fraction (CFU/CFU_control)', color=color_viability, fontsize=12)
ax2.errorbar(ph_values, survival_fraction, yerr=cfu_std/cfu_control, fmt='s-',
             markersize=8, color=color_viability, capsize=5, capthick=2, linewidth=2, label='Viability')
ax2.tick_params(axis='y', labelcolor=color_viability)
ax2.set_yscale('log')
ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)

plt.title('E. coli pH Stress Response: Growth Rate and Viability', fontsize=14)
fig.tight_layout()
plt.savefig('ph_stress_response.png', dpi=300, bbox_inches='tight')
plt.show()

# Statistical analysis: identify pH midpoint for 50% maximal growth
mu_max = mu_measured.max()
ph_optimal = ph_values[mu_measured == mu_max][0]
spline = UnivariateSpline(ph_values, mu_measured - mu_max/2, s=0)
ph_half_points = spline.roots()
print(f"\nOptimal pH = {ph_optimal:.1f} (μ_max = {mu_max:.2f} h⁻¹)")
if len(ph_half_points) == 2:
    print(f"pH range for 50% maximal growth: {ph_half_points[0]:.2f} - {ph_half_points[1]:.2f}")
```

Typical *E. coli* exhibits optimal growth at pH 6.5–7.5, with significant growth reduction below pH 5.5 (acid stress) or above pH 8.5 (alkaline stress). The asymmetric response reflects differential proton pump capacity: F₁F₀-ATPase efficiently expels excess protons under acidic conditions, while alkaline stress overwhelms limited proton import mechanisms. Viability loss precedes growth cessation, with irreversible membrane damage occurring below pH 4.0 or above pH 9.5 as lipid bilayer integrity fails under extreme proton concentration gradients.

**Osmotic Stress: Water Activity Manipulation**

Cellular turgor pressure and macromolecular hydration depend critically on water activity, with hypertonic stress inducing plasmolysis and hypotonic stress risking cell lysis. Measure growth response to sodium chloride osmotic stress, ranging from hypotonic (pure water) to near-saturation hypertonic conditions.

Prepare nutrient broth media supplemented with NaCl to achieve final concentrations: 0% (hypotonic control), 0.5%, 1.0%, 2.0%, 3.0%, 4.0%, 5.0%, 6.0% (w/v). Calculate water activity a_w for each condition using the empirical relationship for NaCl solutions:

$$a_w \approx 1 - 0.035 \times \text{molality}$$

where molality = (g NaCl / 58.44 g/mol) / (kg water). Inoculate each medium 1:100 with an *E. coli* overnight culture (∼10⁹ cells/mL) grown in standard 0.5% NaCl broth to achieve starting density ∼10⁷ cells/mL, and monitor OD₆₀₀ every 30 minutes for 16 hours. The extended lag phase at high osmolarity reflects the time required for compatible solute (trehalose, proline) accumulation to restore cytoplasmic osmotic balance.

Measure cell morphology changes under osmotic stress via microscopy. At 4 hours post-inoculation, prepare wet mount slides from each NaCl concentration and image cells under 1000× phase contrast microscopy. Measure cell length and width using calibrated image analysis software, calculating cell volume assuming cylindrical geometry with hemispherical caps:

$$V = \pi r^2 (L - \frac{4r}{3}) + \frac{4\pi r^3}{3}$$

where r denotes cell radius and L represents total cell length.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Experimental data: NaCl concentration, water activity, growth parameters
nacl_percent = np.array([0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
nacl_molality = (nacl_percent / 100) / (58.44e-3 * (1 - nacl_percent/100))  # mol/kg water
water_activity = 1 - 0.035 * nacl_molality

mu_obs = np.array([1.52, 1.78, 1.71, 1.45, 1.08, 0.62, 0.18, 0.0])
lag_time_h = np.array([0.5, 0.4, 0.5, 0.8, 1.5, 3.2, 6.8, np.nan])
cell_volume_um3 = np.array([1.2, 1.0, 0.95, 0.82, 0.71, 0.64, 0.58, 0.55])

# Fit water activity dependence model
def osmotic_growth_model(aw, mu_opt, aw_opt, sigma):
    """Gaussian-like response centered at optimal water activity"""
    return mu_opt * np.exp(-((aw - aw_opt)**2) / (2 * sigma**2))

mask = mu_obs > 0
popt, _ = curve_fit(osmotic_growth_model, water_activity[mask], mu_obs[mask],
                    p0=[1.8, 0.99, 0.02])
mu_opt, aw_opt, sigma = popt

print("Osmotic Stress Analysis:")
print(f"Optimal water activity a_w = {aw_opt:.4f} ({nacl_percent[np.argmax(mu_obs)]:.1f}% NaCl)")
print(f"Growth rate at optimum μ_opt = {mu_opt:.2f} h⁻¹")
print(f"Osmotic tolerance width σ = {sigma:.4f}")
print(f"\nUpper osmotic limit (no growth): {nacl_percent[mu_obs == 0].min():.1f}% NaCl (a_w = {water_activity[mu_obs == 0].min():.3f})")

# Cell volume analysis
volume_ratio = cell_volume_um3 / cell_volume_um3[nacl_percent == 0.5][0]
print(f"\nCell volume reduction at 5% NaCl: {(1 - volume_ratio[nacl_percent == 5.0][0]) * 100:.0f}% (plasmolysis)")

# Plotting
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Growth rate vs NaCl
axes[0, 0].plot(nacl_percent, mu_obs, 'o-', markersize=10, linewidth=2)
axes[0, 0].set_xlabel('NaCl concentration (%)', fontsize=11)
axes[0, 0].set_ylabel('Specific growth rate μ (h⁻¹)', fontsize=11)
axes[0, 0].set_title('Growth Rate vs Osmotic Stress', fontsize=12)
axes[0, 0].axvline(x=0.5, color='green', linestyle=':', label='Optimal (0.5%)')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# Growth rate vs water activity
axes[0, 1].plot(water_activity[mask], mu_obs[mask], 'o', markersize=10, label='Data')
aw_fit = np.linspace(water_activity.min(), water_activity.max(), 100)
mu_fit = osmotic_growth_model(aw_fit, *popt)
axes[0, 1].plot(aw_fit, mu_fit, 'r-', linewidth=2, label='Gaussian fit')
axes[0, 1].set_xlabel('Water activity a_w', fontsize=11)
axes[0, 1].set_ylabel('Specific growth rate μ (h⁻¹)', fontsize=11)
axes[0, 1].set_title('Growth Rate vs Water Activity', fontsize=12)
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# Lag time vs NaCl
axes[1, 0].plot(nacl_percent[~np.isnan(lag_time_h)], lag_time_h[~np.isnan(lag_time_h)],
                's-', markersize=10, linewidth=2, color='orange')
axes[1, 0].set_xlabel('NaCl concentration (%)', fontsize=11)
axes[1, 0].set_ylabel('Lag time (hours)', fontsize=11)
axes[1, 0].set_title('Osmotic Adaptation Time', fontsize=12)
axes[1, 0].grid(True, alpha=0.3)

# Cell volume vs NaCl
axes[1, 1].plot(nacl_percent, cell_volume_um3, 'd-', markersize=10,
                linewidth=2, color='purple')
axes[1, 1].set_xlabel('NaCl concentration (%)', fontsize=11)
axes[1, 1].set_ylabel('Cell volume (µm³)', fontsize=11)
axes[1, 1].set_title('Cell Shrinkage Under Hyperosmotic Stress', fontsize=12)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('osmotic_stress_analysis.png', dpi=300, bbox_inches='tight')
plt.show()
```

Osmotic stress tolerance limits occur near 5–6% NaCl (approximately 0.85–1.0 M) for standard *E. coli* strains, corresponding to water activity a_w ≈ 0.96. Halotolerant strains and marine bacteria extend this limit through constitutive expression of osmoprotectant synthesis pathways. The exponential increase in lag time with increasing osmolarity reflects the kinetics of compatible solute accumulation required to restore cytoplasmic osmotic potential before cell division can resume.

**Replicate Variability and Statistical Power Analysis**

Quantify biological versus technical variability through parallel replicate culture analysis, distinguishing stochastic population dynamics from systematic experimental error. Prepare twelve identical cultures by inoculating twelve separate flasks with 1:100 diluted aliquots from a single overnight *E. coli* seed culture. Monitor all cultures simultaneously under identical environmental conditions (37°C, 200 rpm shaking, same incubator) with OD₆₀₀ measurements every 30 minutes over 8 hours.

Calculate inter-replicate coefficient of variation (CV) at each timepoint:

$$\text{CV}(\%) = \frac{\sigma}{\bar{x}} \times 100\%$$

where σ denotes standard deviation and x̄ represents mean OD₆₀₀ across the twelve replicates. Extract specific growth rate from each replicate independently and perform statistical analysis:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress, f_oneway, ttest_ind

# Simulated replicate data: 12 cultures, OD600 measured at 17 timepoints
np.random.seed(42)
n_replicates = 12
n_timepoints = 17
time_h = np.linspace(0, 8, n_timepoints)

# Generate realistic replicate data with biological + technical variance
mu_true = 1.80  # h^-1
od0_true = 0.025
sigma_bio = 0.08  # biological variation in growth rate
sigma_tech = 0.003  # technical measurement error in OD

mu_replicates = np.random.normal(mu_true, sigma_bio, n_replicates)
od_data = np.zeros((n_replicates, n_timepoints))

for i in range(n_replicates):
    od_true = od0_true * np.exp(mu_replicates[i] * time_h)
    od_true[time_h > 5] = 1.5  # Stationary phase plateau
    od_data[i, :] = od_true + np.random.normal(0, sigma_tech, n_timepoints)
    od_data[i, :] = np.maximum(od_data[i, :], 0.01)  # Physical constraint

# Calculate statistics
od_mean = od_data.mean(axis=0)
od_std = od_data.std(axis=0, ddof=1)
od_cv = (od_std / od_mean) * 100

# Extract growth rate from each replicate
mu_fitted = np.zeros(n_replicates)
for i in range(n_replicates):
    exp_mask = (time_h >= 1) & (time_h <= 4)  # Exponential phase
    slope, _, _, _, _ = linregress(time_h[exp_mask], np.log(od_data[i, exp_mask]))
    mu_fitted[i] = slope

print("Replicate Variability Analysis:")
print(f"Mean growth rate: {mu_fitted.mean():.3f} ± {mu_fitted.std():.3f} h⁻¹")
print(f"Coefficient of variation in μ: {(mu_fitted.std() / mu_fitted.mean()) * 100:.1f}%")
print(f"Range: {mu_fitted.min():.3f} to {mu_fitted.max():.3f} h⁻¹")
print(f"\nMean OD_600 CV at exponential phase (2-4h): {od_cv[(time_h >= 2) & (time_h <= 4)].mean():.1f}%")
print(f"Maximum OD_600 CV: {od_cv.max():.1f}% at t={time_h[np.argmax(od_cv)]:.1f}h")

# Statistical power calculation for detecting 10% growth rate difference
effect_size = 0.10 * mu_true  # 10% difference
pooled_std = mu_fitted.std()
cohens_d = effect_size / pooled_std
print(f"\nEffect size (Cohen's d) for 10% μ difference: {cohens_d:.2f}")
# Power approximation for t-test (two-tailed, α=0.05)
from scipy.stats import norm
z_crit = norm.ppf(0.975)  # Two-tailed α=0.05
z_power = cohens_d * np.sqrt(n_replicates / 2) - z_crit
power = norm.cdf(z_power)
print(f"Statistical power with n={n_replicates}: {power:.2%}")
print(f"Minimum n for 80% power: {int(np.ceil(2 * ((z_crit + norm.ppf(0.80)) / cohens_d)**2))}")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Individual replicate growth curves
axes[0, 0].plot(time_h, od_data.T, alpha=0.3, linewidth=1)
axes[0, 0].plot(time_h, od_mean, 'k-', linewidth=3, label='Mean')
axes[0, 0].fill_between(time_h, od_mean - od_std, od_mean + od_std,
                        alpha=0.3, color='gray', label='±1 SD')
axes[0, 0].set_xlabel('Time (hours)', fontsize=11)
axes[0, 0].set_ylabel('OD₆₀₀', fontsize=11)
axes[0, 0].set_title('Replicate Growth Curves (n=12)', fontsize=12)
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Coefficient of variation over time
axes[0, 1].plot(time_h, od_cv, 'o-', markersize=8, linewidth=2, color='red')
axes[0, 1].axhline(y=5, color='green', linestyle=':', label='5% threshold')
axes[0, 1].axhline(y=10, color='orange', linestyle=':', label='10% threshold')
axes[0, 1].set_xlabel('Time (hours)', fontsize=11)
axes[0, 1].set_ylabel('Coefficient of variation (%)', fontsize=11)
axes[0, 1].set_title('Inter-Replicate Variability', fontsize=12)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Distribution of fitted growth rates
axes[1, 0].hist(mu_fitted, bins=8, edgecolor='black', alpha=0.7)
axes[1, 0].axvline(x=mu_fitted.mean(), color='red', linewidth=2, label='Mean')
axes[1, 0].axvline(x=mu_fitted.mean() - mu_fitted.std(), color='orange',
                   linestyle='--', label='±1 SD')
axes[1, 0].axvline(x=mu_fitted.mean() + mu_fitted.std(), color='orange', linestyle='--')
axes[1, 0].set_xlabel('Specific growth rate μ (h⁻¹)', fontsize=11)
axes[1, 0].set_ylabel('Frequency', fontsize=11)
axes[1, 0].set_title('Distribution of Growth Rates Across Replicates', fontsize=12)
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Q-Q plot for normality assessment
from scipy.stats import probplot
probplot(mu_fitted, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot: Growth Rate Normality Test', fontsize=12)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('replicate_variability_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Uncertainty budget analysis
print(f"\nUncertainty Sources:")
print(f"Technical (measurement) noise: σ_OD = {sigma_tech:.6f} OD units")
print(f"Biological growth rate variability: {(mu_fitted.std() / mu_fitted.mean()) * 100:.1f}% CV")
print(f"Biological variance (growth rate): {mu_fitted.var():.6f} h⁻²")
print(f"Growth rate standard error: {mu_fitted.std() / np.sqrt(n_replicates):.4f} h⁻¹")
```

Biological variability in growth rate typically exhibits 4–6% coefficient of variation for *E. coli* cultures derived from a single clone, reflecting stochastic gene expression and cell-cycle asynchrony within the population. Technical measurement error contributes < 1% CV for calibrated spectrophotometers, making biological variation the dominant uncertainty source. Statistical power analysis reveals that detecting a 10% difference in growth rate between two conditions requires n ≥ 8 replicates per group to achieve 80% power at α = 0.05 significance, assuming CV ≈ 5%.

This boundary condition analysis establishes the operational limits of microbial growth while quantifying experimental uncertainty through rigorous statistical methodology. The practitioner learns to distinguish biological phenomena from measurement artifacts, design adequately powered experiments, and interpret quantitative results within their uncertainty bounds—essential skills for reproducible microbiological research.

## Laboratory Cheat Sheet & Metric Verification Guide

**Critical Culture Handling Protocols**

Aseptic technique verification: Flame loop/needle until red-hot; cool 5 seconds before touching culture. Work within 15 cm radius of Bunsen burner flame or inside laminar flow hood with HEPA-filtered air velocity 0.3–0.5 m/s. Autoclave media at 121°C, 15 psi for 20 minutes; verify spore strip indicators post-cycle. Store plates inverted to prevent condensation drip contamination.

*E. coli* K-12 growth parameters (37°C, nutrient broth, aerobic): Doubling time t_d = 20–25 min; specific growth rate μ = 1.6–2.0 h⁻¹; lag phase after 1:100 dilution ≈ 20–30 min; stationary phase OD₆₀₀ = 1.5–2.0; exponential range for kinetics OD₆₀₀ = 0.05–0.8.

**Spectrophotometry Calibration & Validation**

Blank reference: Use sterile media in matched cuvettes; re-blank if drift >0.005 OD units per hour. Verify linearity: Prepare serial dilutions of standardized latex microsphere suspension (1.0 OD standard); linear range typically OD₆₀₀ = 0.05–1.0 for 1 cm path length. Cell density conversion: 1.0 OD₆₀₀ ≈ 8 × 10⁸ cells/mL (*E. coli* K-12, strain-dependent ±30%). Path length verification: Measure water absorbance at 975 nm (near-IR water peak); A₉₇₅ = 0.180 for exactly 1.0 cm path.

Troubleshooting: Bubbles in cuvette → false high OD (remove via gentle tapping). Condensation on cuvette exterior → wipe with Kimwipe before measurement. OD >1.0 → dilute 1:5 or 1:10 in sterile media; multiply result by dilution factor. Wavelength accuracy: Verify 600 nm setting with holmium oxide glass filter (narrow peak at 536.3 nm).

**Growth Kinetics Computation Recipes**

Exponential growth rate from OD time series:
```python
# Select exponential phase (OD 0.05 to 0.8)
import time

exp_mask = (od >= 0.05) & (od <= 0.8)
ln_od = np.log(od[exp_mask])
time_exp = time[exp_mask]
mu, intercept = np.polyfit(time_exp, ln_od, 1)  # slope = growth rate
doubling_time_min = np.log(2) / mu * 60  # Convert h^-1 to minutes
```

Logistic model with carrying capacity:
```python
from scipy.optimize import curve_fit
def logistic(t, od0, mu, od_max):
    return od_max / (1 + (od_max/od0 - 1) * np.exp(-mu * t))
params, _ = curve_fit(logistic, time, od, p0=[0.02, 1.5, 1.5])
```

Generation time from discrete measurements: g = t × log(2) / log(N_t / N_0), where N_t and N_0 are cell counts at times t and 0.

**Statistical Validation Checkpoints**

Minimum replicate requirements: n ≥ 3 for preliminary data; n ≥ 6 for publication-quality experiments; n ≥ 10 for detecting < 15% effect sizes. Report mean ± standard deviation (SD) for parametric data; median ± interquartile range (IQR) for non-normal distributions. Significance testing: two-sample t-test for comparing two groups (assumes normality and equal variance); ANOVA for multiple groups; Mann-Whitney U for non-parametric comparisons.

Outlier detection: Grubbs' test for single outlier; Dixon's Q-test for small samples (n = 3–7). Remove outliers only with documented justification; rerun experiment if >10% of data points flagged. R² threshold for curve fits: exponential growth R² >0.98; dose-response curves R² >0.95.

**Hemocytometer Cell Counting Procedure**

Load 10 µL diluted culture into chamber; count cells in 25 small squares (0.2 mm × 0.2 mm, 0.1 mm depth). Cell concentration = (cells counted / 25) × 25 × 10⁴ × dilution factor = (cells counted) × 10⁴ × dilution factor per mL. Count >100 total cells for < 10% statistical error. Exclude cells touching top/left borders; include cells touching bottom/right borders (standard convention). Clumps: Count as single unit if indistinguishable or divide by estimated cell number.

**Antibiotic Stock Preparation Standards**

Ampicillin: 100 mg/mL in sterile water; filter-sterilize; store -20°C; stable 6 months. Working concentration 50–100 µg/mL. Kanamycin: 50 mg/mL in water; autoclavable; stable at 4°C for 1 year. Working concentration 25–50 µg/mL. Chloramphenicol: 34 mg/mL in 100% ethanol; store -20°C; light-sensitive (wrap foil). Working concentration 10–30 µg/mL. Tetracycline: 5 mg/mL in 50% ethanol; highly light-sensitive; store -20°C in dark; prepare fresh monthly. Working concentration 10–20 µg/mL.

**Buffer System Recipes for pH Control**

Citrate-phosphate buffer (pH 3.0–6.0): Mix 0.1 M citric acid + 0.2 M Na₂HPO₄ at varying ratios; adjust with 1 M HCl/NaOH. Phosphate buffer (pH 6.0–8.0): Mix 0.1 M NaH₂PO₄ + 0.1 M Na₂HPO₄; standard PBS is 137 mM NaCl, 2.7 mM KCl, 10 mM Na₂HPO₄, 1.8 mM KH₂PO₄, pH 7.4. Tris-HCl buffer (pH 7.0–9.0): 0.1 M Tris base adjusted with HCl; temperature-dependent (pK_a shifts -0.03 per °C). Verify all buffers with calibrated pH meter using two-point calibration (pH 4.0 and 7.0 standards).

**Quick Reference: Python Scientific Stack Verification**

```bash
# Verify installations
python -c "import numpy; print(f'NumPy {numpy.__version__}')"
python -c "import scipy; print(f'SciPy {scipy.__version__}')"
python -c "import matplotlib; print(f'Matplotlib {matplotlib.__version__}')"

# Test basic functionality
python -c "import numpy as np; print(np.exp(np.log(2)))"  # Should print 2.0
python -c "from scipy.optimize import curve_fit; print('curve_fit available')"
python -c "import matplotlib.pyplot as plt; plt.figure(); print('plotting OK')"
```

**Safety & Biosafety Reminders**

BSL-1 organisms (*E. coli* K-12, *S. cerevisiae*): Standard microbiological practices; lab coat, gloves, eye protection mandatory. Autoclave all culture waste before disposal (121°C, 30 min for liquid cultures). Chemical disinfection: 70% ethanol for surfaces (10 min contact), 10% bleach for spills (30 min contact). Never mouth-pipette; use mechanical pipetting aids only. Broken glass disposal: sharps container, not regular trash.

This cheat sheet condenses the critical protocols, equations, and verification procedures required for reproducible microbiological experimentation, enabling rapid reference during active laboratory sessions while maintaining quantitative rigor and statistical validity.
