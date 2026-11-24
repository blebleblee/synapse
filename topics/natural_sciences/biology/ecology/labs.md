# Operational Verification Labs: Ecology

## Objective & Laboratory Bench Setup

Ecology demands rigorous quantitative field and laboratory measurement protocols to transform qualitative natural observations into reproducible empirical datasets. The modern ecologist operates at the intersection of population dynamics theory, environmental chemistry, statistical sampling design, and computational modeling. This laboratory guide grounds ecological hypothesis testing in direct physical measurement: you will deploy quadrat sampling frames to census plant communities, construct mark-recapture population estimators with calculable confidence intervals, measure primary productivity through dissolved oxygen flux in aquatic mesocosms, and model predator-prey oscillations using coupled differential equations fit to real census time series. Each exercise progresses from instrument calibration and data acquisition through statistical uncertainty quantification and ecological interpretation.

Your laboratory bench for these exercises requires both field equipment and computational analysis infrastructure. Field instrumentation includes meter tapes and quadrat frames (0.25 m² to 1 m² aluminum or PVC construction) for vegetation sampling, temperature-compensated dissolved oxygen probes (YSI or Hach models with ±0.1 mg/L precision), portable spectrophotometers for chlorophyll-a quantification (measuring absorbance at 664 nm and 647 nm wavelengths), and GPS units with sub-meter accuracy for spatial sampling design. Laboratory wet-bench equipment includes filtration apparatus with pre-weighed GF/F glass fiber filters (0.7 μm nominal pore size) for particulate matter gravimetric analysis, analytical balances with 0.0001 g readability, and temperature-controlled incubators for respiration rate measurements. The computational environment must provide Python 3.8 or later with NumPy (version 1.21+), SciPy (version 1.7+), Matplotlib (version 3.4+), and pandas (version 1.3+) for time series manipulation. Verify your installation by executing `python -c "import numpy as np; import scipy.stats; import matplotlib.pyplot as plt; print(f'NumPy {np.__version__}, SciPy {scipy.__version__}')"` which should confirm library availability without import errors.

The theoretical foundation underlying these exercises rests on population growth models derived from first-principles demographic accounting. Exponential growth emerges when per-capita birth rate $b$ exceeds per-capita death rate $d$, yielding the differential equation $\frac{dN}{dt} = rN$ where intrinsic growth rate $r = b - d$ and population size $N(t) = N_0 e^{rt}$ represents the solution. Real populations encounter resource limitation, formalized in the logistic model through carrying capacity $K$: the modified equation $\frac{dN}{dt} = rN\left(1 - \frac{N}{K}\right)$ produces sigmoid growth curves with inflection at $N = K/2$. Predator-prey dynamics extend this framework to coupled species interactions, captured in the Lotka-Volterra equations where prey population $V$ and predator population $P$ evolve according to $\frac{dV}{dt} = \alpha V - \beta VP$ and $\frac{dP}{dt} = \delta VP - \gamma P$, with $\alpha$ representing prey birth rate, $\beta$ the predation encounter rate, $\delta$ the predator conversion efficiency, and $\gamma$ the predator death rate. These models translate ecological processes into falsifiable mathematical predictions that field measurements either support or refute.

Primary productivity measurements quantify energy flux through ecosystems by tracking photosynthetic oxygen production and respiratory oxygen consumption. Gross primary productivity (GPP) represents total photosynthetic carbon fixation, while net primary productivity (NPP) subtracts autotrophic respiration: $\text{NPP} = \text{GPP} - R_a$. Light-dark bottle incubations operationalize these definitions by measuring dissolved oxygen change in paired transparent and opaque bottles over fixed time intervals. The transparent bottle accumulates oxygen from photosynthesis minus respiration (net community productivity), while the dark bottle loses oxygen through respiration alone. Subtracting dark bottle oxygen consumption from light bottle oxygen accumulation yields GPP, typically expressed in mg O₂ L⁻¹ hr⁻¹ and convertible to carbon units through stoichiometric ratios (photosynthetic quotient PQ ≈ 1.2 mol O₂ / mol C fixed).

## Exercise 1: Empirical Observation & Measurement Protocol

This foundational exercise establishes quantitative vegetation sampling methodology through quadrat-based community census. You will demarcate study plots, execute stratified random quadrat placement, record species presence and abundance metrics, calculate Shannon diversity indices with bootstrap confidence intervals, and construct rank-abundance curves revealing community evenness. The protocol mirrors standard ecological field survey techniques published in peer-reviewed vegetation science literature.

Begin by selecting a study site exhibiting heterogeneous plant community structure: old-field successional habitat, forest understory, or managed grassland provides suitable complexity. Delineate a 20 m × 20 m (400 m²) master plot using meter tapes and corner stakes, recording GPS coordinates of plot vertices with sub-meter precision. Divide the plot conceptually into a 4 × 4 grid of 16 equal 5 m × 5 m subplots. Generate 12 random subplot coordinates using Python's random number generator seeded for reproducibility: `np.random.seed(42); subplot_indices = np.random.choice(16, size=12, replace=False)`. Map these indices to spatial coordinates by computing row and column positions: subplot index $i$ occupies row $\lfloor i/4 \rfloor$ and column $i \mod 4$, with coordinates at $(5c + 2.5, 5r + 2.5)$ meters from the southwest origin where $r$ and $c$ represent row and column respectively.

Navigate to each selected subplot center and position a 1 m × 1 m quadrat frame aligned to cardinal directions (north-south and east-west edges). Within each quadrat, systematically identify and count all rooted vascular plant individuals, recording species identity and abundance. For herbaceous vegetation, define an individual as a distinct aboveground shoot; for clonal species exhibiting rhizomatous or stoloniferous growth, count discrete ramets rather than attempting genet delineation. For woody vegetation, include only individuals with basal diameter exceeding 1 cm measured at ground level. Record data in a structured field notebook or digital tablet using a standardized form listing plot identifier, quadrat number, species binomial, and count. Photograph each quadrat from nadir view (camera positioned directly above at 1.5 m height) for later verification and voucher documentation.

Transfer field census data into a Python pandas DataFrame for analysis. Construct the DataFrame with columns `['quadrat', 'species', 'count']` where quadrat identifiers range from 0 to 11, species names use consistent taxonomic nomenclature, and counts represent integer abundance values. Calculate site-level species richness (total number of unique species observed across all quadrats) and quadrat-level richness distributions using `df.groupby('quadrat')['species'].nunique()`. Compute total abundance per species through summation: `species_totals = df.groupby('species')['count'].sum().sort_values(ascending=False)`.

The Shannon diversity index $H' = -\sum_{i=1}^{S} p_i \ln(p_i)$ quantifies community entropy where $S$ represents species richness and $p_i$ denotes the proportional abundance of species $i$. Calculate proportional abundances by dividing species totals by grand total abundance: `p = species_totals / species_totals.sum()`. Compute Shannon index through element-wise logarithmic transformation and weighted summation: `H_prime = -np.sum(p * np.log(p))`. Shannon index values range from 0 (single-species monoculture) to $\ln(S)$ (perfectly even community where all species occur at equal abundance). Interpret your calculated value relative to these theoretical bounds.

Quantify statistical uncertainty in the Shannon index through bootstrap resampling. Each bootstrap iteration resamples the original 12 quadrats with replacement, recalculates species abundances from the resampled data, and recomputes the Shannon index. Execute 10,000 bootstrap iterations to construct the sampling distribution of $H'$. Implement this procedure by first reshaping data into a quadrat-by-species matrix using `pivot_table`, then iterating through bootstrap samples:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Construct example dataset (replace with your field data)
data = {
    'quadrat': [0]*3 + [1]*4 + [2]*2 + [3]*5,
    'species': ['Poa pratensis', 'Trifolium repens', 'Plantago major',
                'Poa pratensis', 'Trifolium repens', 'Taraxacum officinale', 'Plantago major',
                'Poa pratensis', 'Taraxacum officinale',
                'Poa pratensis', 'Trifolium repens', 'Taraxacum officinale', 'Plantago major', 'Achillea millefolium'],
    'count': [12, 8, 3, 15, 6, 4, 2, 18, 7, 10, 9, 5, 4, 3]
}
df = pd.DataFrame(data)

# Aggregate to species totals
species_totals = df.groupby('species')['count'].sum()
total_abundance = species_totals.sum()
p_observed = species_totals / total_abundance
H_observed = -np.sum(p_observed * np.log(p_observed))

print(f"Observed Shannon Index H' = {H_observed:.4f}")
print(f"Species Richness S = {len(species_totals)}")
print(f"Maximum Possible H' = {np.log(len(species_totals)):.4f}")

# Bootstrap confidence interval
n_bootstrap = 10000
H_bootstrap = np.zeros(n_bootstrap)

# Create quadrat-level species abundance matrix
quadrat_species_matrix = df.pivot_table(index='quadrat', columns='species', values='count', fill_value=0)
n_quadrats = len(quadrat_species_matrix)

for i in range(n_bootstrap):
    # Resample quadrats with replacement
    resampled_indices = np.random.choice(n_quadrats, size=n_quadrats, replace=True)
    resampled_matrix = quadrat_species_matrix.iloc[resampled_indices]
    
    # Sum to get species totals in bootstrap sample
    species_totals_boot = resampled_matrix.sum(axis=0)
    total_boot = species_totals_boot.sum()
    
    # Remove species with zero abundance in this bootstrap sample
    species_totals_boot = species_totals_boot[species_totals_boot > 0]
    
    if len(species_totals_boot) > 0:
        p_boot = species_totals_boot / total_boot
        H_bootstrap[i] = -np.sum(p_boot * np.log(p_boot))
    else:
        H_bootstrap[i] = 0.0

# Calculate 95% confidence interval
ci_lower = np.percentile(H_bootstrap, 2.5)
ci_upper = np.percentile(H_bootstrap, 97.5)

print(f"\n95% Bootstrap Confidence Interval: [{ci_lower:.4f}, {ci_upper:.4f}]")
print(f"Bootstrap Standard Error: {np.std(H_bootstrap):.4f}")

# Plot bootstrap distribution
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(H_bootstrap, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='black')
axes[0].axvline(H_observed, color='red', linestyle='--', linewidth=2, label=f"Observed H' = {H_observed:.3f}")
axes[0].axvline(ci_lower, color='orange', linestyle=':', linewidth=1.5, label=f"95% CI")
axes[0].axvline(ci_upper, color='orange', linestyle=':', linewidth=1.5)
axes[0].set_xlabel("Shannon Index H'", fontsize=12)
axes[0].set_ylabel("Probability Density", fontsize=12)
axes[0].set_title("Bootstrap Distribution of Shannon Diversity", fontsize=13)
axes[0].legend()
axes[0].grid(alpha=0.3)

# Rank-abundance curve
species_sorted = species_totals.sort_values(ascending=False)
ranks = np.arange(1, len(species_sorted) + 1)
axes[1].plot(ranks, species_sorted.values, 'o-', linewidth=2, markersize=8, color='darkgreen')
axes[1].set_xlabel("Species Rank", fontsize=12)
axes[1].set_ylabel("Total Abundance", fontsize=12)
axes[1].set_title("Rank-Abundance Curve", fontsize=13)
axes[1].set_yscale('log')
axes[1].grid(alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('vegetation_diversity_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Export species abundance table
species_table = pd.DataFrame({
    'Species': species_totals.index,
    'Total Abundance': species_totals.values,
    'Relative Abundance': (species_totals / total_abundance).values,
    'Frequency (quadrats present)': [df[df['species'] == sp]['quadrat'].nunique() for sp in species_totals.index]
})
species_table = species_table.sort_values('Total Abundance', ascending=False).reset_index(drop=True)
species_table.to_csv('species_abundance_table.csv', index=False)
print("\nSpecies abundance table exported to 'species_abundance_table.csv'")
```

Construct a rank-abundance curve by plotting species abundance (y-axis, logarithmic scale) against species rank (x-axis, linear scale) where rank 1 corresponds to the most abundant species. Steep initial slopes indicate dominance by a few abundant species (low evenness), while gradual slopes reflect more equitable abundance distributions (high evenness). Compare your empirical curve shape to theoretical community models: geometric series (niche preemption), log-series (Fisher's alpha), and log-normal (random niche apportionment).

Execute spatial analysis by calculating intra-quadrat versus inter-quadrat species turnover. Compute Jaccard similarity indices for all pairwise quadrat combinations using the formula $J = \frac{|A \cap B|}{|A \cup B|}$ where $A$ and $B$ represent species sets in quadrats $i$ and $j$. High mean Jaccard similarity (>0.6) indicates spatially homogeneous community composition, while low similarity (< 0.3) reveals strong beta diversity driven by environmental gradients or disturbance patchiness. Implement this calculation through nested loops over quadrat pairs, extracting unique species sets and computing intersection and union cardinalities.

Document all measurement uncertainties in your laboratory notebook. Record quadrat positioning error (typically ±0.5 m from target coordinates due to GPS accuracy and navigation precision), species identification confidence (noting any taxa requiring expert verification or later voucher specimen comparison), and counting error for dense vegetation patches (estimated at ±5-10% for herbaceous quadrats with >50 individuals). These uncertainty sources propagate through diversity calculations, contributing to the bootstrap confidence interval width you quantified above.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

This intermediate exercise quantifies aquatic primary productivity through dissolved oxygen light-dark bottle incubations, measuring photosynthetic oxygen evolution rates across a light intensity gradient. You will calibrate dissolved oxygen probes against Winkler titration standards, prepare replicate bottle arrays, execute controlled light exposure treatments, measure oxygen flux rates, and construct photosynthesis-irradiance (P-I) response curves fitted with hyperbolic tangent models. The protocol follows standard methods published in the American Public Health Association's *Standard Methods for the Examination of Water and Wastewater*.

Collect natural water samples from a productive aquatic system such as a eutrophic pond, shallow lake littoral zone, or slow-moving stream reach. Sample during morning hours (08:00-10:00) when phytoplankton populations are photosynthetically active but have not yet depleted dissolved CO₂. Use a horizontal Van Dorn sampler or clean polycarbonate bottle to collect integrated water column samples from the photic zone (typically 0.5 m depth in turbid systems, 1-2 m in clear water). Immediately transfer water into acid-washed, sample-rinsed amber glass bottles with ground-glass stoppers to minimize gas exchange and photodegradation. Transport samples to the laboratory in a dark, insulated cooler maintaining in situ temperature (±2°C).

Calibrate your dissolved oxygen probe before measurements. Modern optical DO probes (e.g., Hach LDO or YSI ProODO) typically require only single-point calibration in air-saturated water (100% saturation at ambient barometric pressure); a zero check is optional. Prepare the zero standard by dissolving 2 g sodium sulfite (Na₂SO₃) and a trace of cobalt chloride catalyst in 100 mL deionized water; this solution scavenges dissolved oxygen through the reaction $2\text{Na}_2\text{SO}_3 + \text{O}_2 \rightarrow 2\text{Na}_2\text{SO}_4$. Prepare the saturation standard by vigorously aerating deionized water at room temperature for 10 minutes with an aquarium air stone, then allowing the water to equilibrate for 5 minutes. Correct saturation values for local barometric pressure using the equation $C_{\text{sat}} = C_{\text{standard}} \times \frac{P_{\text{local}} - P_{\text{water vapor}}}{P_{\text{standard}}}$ where standard pressure equals 101.325 kPa and water vapor pressure at 20°C equals 2.34 kPa. Immerse the probe in zero standard until readings stabilize (< 0.2 mg/L), execute zero calibration, then repeat for saturation standard (typically 8.8-9.2 mg/L at 20°C and sea level).

Prepare 18 biological oxygen demand (BOD) bottles (300 mL nominal volume, clear borosilicate glass) by rinsing three times with sample water. Fill bottles completely using a siphon tube positioned at the bottom, allowing overflow of at least three bottle volumes to displace headspace and trapped bubbles. Segregate bottles into three treatment groups: six initial bottles for time-zero oxygen determination, six light incubation bottles, and six dark incubation bottles. Wrap dark bottles completely with aluminum foil, ensuring no light penetration. Measure initial dissolved oxygen concentration in the six initial bottles immediately using the calibrated probe, recording temperature simultaneously.

Incubate light and dark bottle pairs under controlled irradiance conditions. Position light bottles in a temperature-controlled water bath or incubator maintained at in situ temperature (±1°C). Illuminate bottles using tungsten-halogen or LED light sources positioned at varying distances to create an irradiance gradient spanning 0 to 800 μmol photons m⁻² s⁻¹. Measure photosynthetically active radiation (PAR) at each bottle position using a calibrated quantum sensor (Li-Cor LI-190 or Apogee MQ-500), recording irradiance in μmol photons m⁻² s⁻¹. Arrange bottles in six paired light-dark combinations at irradiances of approximately 0, 50, 100, 200, 400, and 800 μmol m⁻² s⁻¹. Incubate for 4 hours, a duration sufficient to detect measurable oxygen changes (typically 0.5-3.0 mg/L) without depleting nutrients or causing excessive bacterial respiration.

After incubation, measure final dissolved oxygen concentrations in all bottles, recording temperature. Calculate oxygen change rates by subtracting initial from final concentrations and dividing by incubation time in hours: $\Delta \text{DO}_{\text{light}} = (\text{DO}_{\text{final}} - \text{DO}_{\text{initial}}) / t$ and $\Delta \text{DO}_{\text{dark}} = (\text{DO}_{\text{final}} - \text{DO}_{\text{initial}}) / t$. Net oxygen production in light bottles reflects net photosynthesis (gross photosynthesis minus respiration), while oxygen consumption in dark bottles quantifies respiration rate $R$. Gross primary productivity (GPP) at each irradiance level equals net oxygen change in the light bottle minus oxygen change in the paired dark bottle: $\text{GPP}(I) = \Delta \text{DO}_{\text{light}}(I) - \Delta \text{DO}_{\text{dark}}$.

Plot the photosynthesis-irradiance (P-I) response curve by graphing GPP on the y-axis against irradiance $I$ on the x-axis. Overlay dark bottle respiration as a horizontal line at $y = -R$. The P-I curve typically exhibits hyperbolic saturation: linear increase at low irradiance (light-limited region), curvilinear transition at intermediate irradiance, and plateau at high irradiance (light-saturated region where photosynthetic enzyme kinetics become limiting). Fit the data to the hyperbolic tangent model:

$$\text{GPP}(I) = P_{\text{max}} \times \tanh\left(\frac{\alpha I}{P_{\text{max}}}\right)$$

where $P_{\text{max}}$ represents maximum light-saturated photosynthetic rate (mg O₂ L⁻¹ hr⁻¹), $\alpha$ denotes initial slope or photosynthetic efficiency (mg O₂ L⁻¹ hr⁻¹ per μmol photons m⁻² s⁻¹), and $I$ is irradiance. The light saturation parameter $I_k = P_{\text{max}} / \alpha$ defines the irradiance at which the P-I curve transitions from linear to saturated response.

Implement non-linear least squares fitting using SciPy's `curve_fit` function:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Example dataset: irradiance (umol m-2 s-1) and measured GPP (mg O2 L-1 hr-1)
# Replace with your experimental data
irradiance = np.array([0, 50, 100, 200, 400, 800])
gpp_observed = np.array([0.0, 0.35, 0.68, 1.15, 1.42, 1.48])
gpp_std = np.array([0.05, 0.08, 0.10, 0.12, 0.15, 0.18])  # Standard deviations from replicates
respiration_rate = -0.25  # mg O2 L-1 hr-1 from dark bottles

# Define hyperbolic tangent P-I model
def pi_curve(I, P_max, alpha):
    return P_max * np.tanh((alpha * I) / P_max)

# Initial parameter guesses
p0 = [1.5, 0.01]  # P_max ~ 1.5 mg O2 L-1 hr-1, alpha ~ 0.01

# Fit model to data
popt, pcov = curve_fit(pi_curve, irradiance, gpp_observed, p0=p0, sigma=gpp_std, absolute_sigma=True)
P_max_fit, alpha_fit = popt
P_max_err, alpha_err = np.sqrt(np.diag(pcov))

# Calculate derived parameter I_k
I_k = P_max_fit / alpha_fit
I_k_err = I_k * np.sqrt((P_max_err/P_max_fit)**2 + (alpha_err/alpha_fit)**2)

print("=== Photosynthesis-Irradiance Model Fit ===")
print(f"P_max = {P_max_fit:.3f} ± {P_max_err:.3f} mg O2 L-1 hr-1")
print(f"alpha = {alpha_fit:.4f} ± {alpha_err:.4f} (mg O2 L-1 hr-1) / (umol m-2 s-1)")
print(f"I_k (saturation irradiance) = {I_k:.1f} ± {I_k_err:.1f} umol m-2 s-1")
print(f"Respiration rate R = {respiration_rate:.3f} mg O2 L-1 hr-1")

# Calculate net primary productivity (NPP = GPP - respiration)
npp_observed = gpp_observed + respiration_rate

# Generate smooth model curve for plotting
I_smooth = np.linspace(0, 850, 200)
gpp_smooth = pi_curve(I_smooth, P_max_fit, alpha_fit)
npp_smooth = gpp_smooth + respiration_rate

# Plot P-I curve
fig, ax = plt.subplots(figsize=(10, 7))

# Plot observed data with error bars
ax.errorbar(irradiance, gpp_observed, yerr=gpp_std, fmt='o', markersize=10, 
            capsize=5, capthick=2, color='darkgreen', label='GPP (observed)', zorder=3)
ax.errorbar(irradiance, npp_observed, yerr=gpp_std, fmt='s', markersize=8,
            capsize=5, capthick=2, color='seagreen', label='NPP (observed)', zorder=3)

# Plot fitted curves
ax.plot(I_smooth, gpp_smooth, '-', linewidth=2.5, color='darkgreen', label='GPP (fitted model)', zorder=2)
ax.plot(I_smooth, npp_smooth, '--', linewidth=2.5, color='seagreen', label='NPP (fitted model)', zorder=2)

# Plot respiration rate as horizontal line
ax.axhline(respiration_rate, color='crimson', linestyle=':', linewidth=2, label=f'Respiration R = {respiration_rate:.2f}')
ax.axhline(0, color='black', linestyle='-', linewidth=0.8)

# Mark I_k on plot
ax.axvline(I_k, color='orange', linestyle='-.', linewidth=1.5, alpha=0.7, label=f'$I_k$ = {I_k:.0f} μmol m⁻² s⁻¹')

# Formatting
ax.set_xlabel("Irradiance (μmol photons m⁻² s⁻¹)", fontsize=13)
ax.set_ylabel("O₂ Production Rate (mg L⁻¹ hr⁻¹)", fontsize=13)
ax.set_title("Photosynthesis-Irradiance (P-I) Response Curve", fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=11)
ax.grid(alpha=0.3)
ax.set_xlim(-20, 850)

plt.tight_layout()
plt.savefig('pi_curve_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Export fitted parameters and data
results_table = pd.DataFrame({
    'Irradiance (umol m-2 s-1)': irradiance,
    'GPP Observed (mg O2 L-1 hr-1)': gpp_observed,
    'GPP Std Dev': gpp_std,
    'GPP Fitted': pi_curve(irradiance, P_max_fit, alpha_fit),
    'NPP Observed': npp_observed,
    'NPP Fitted': pi_curve(irradiance, P_max_fit, alpha_fit) + respiration_rate
})

parameters_table = pd.DataFrame({
    'Parameter': ['P_max', 'alpha', 'I_k', 'Respiration R'],
    'Value': [P_max_fit, alpha_fit, I_k, respiration_rate],
    'Uncertainty': [P_max_err, alpha_err, I_k_err, np.nan],
    'Units': ['mg O2 L-1 hr-1', '(mg O2 L-1 hr-1)/(umol m-2 s-1)', 'umol m-2 s-1', 'mg O2 L-1 hr-1']
})

results_table.to_csv('pi_curve_data.csv', index=False)
parameters_table.to_csv('pi_curve_parameters.csv', index=False)
print("\nResults exported to 'pi_curve_data.csv' and 'pi_curve_parameters.csv'")
```

Interpret the fitted parameters ecologically. Low $P_{\text{max}}$ values (< 1 mg O₂ L⁻¹ hr⁻¹) indicate oligotrophic conditions with nutrient-limited phytoplankton biomass, while high $P_{\text{max}}$ (>3 mg O₂ L⁻¹ hr⁻¹) characterizes eutrophic systems with dense algal populations. The photosynthetic efficiency $\alpha$ reflects phytoplankton physiological state and light-harvesting pigment concentration; shade-adapted phytoplankton exhibit higher $\alpha$ (steeper initial slope) than sun-adapted species. The saturation irradiance $I_k$ defines the light environment to which the phytoplankton community is adapted: low $I_k$ (< 100 μmol m⁻² s⁻¹) occurs in turbid or deeply mixed water columns, high $I_k$ (>400 μmol m⁻² s⁻¹) in clear, shallow systems with high surface irradiance.

Validate your P-I curve by comparing measured respiration rates to literature values for similar aquatic systems. Typical phytoplankton respiration rates range from 10-30% of $P_{\text{max}}$ under light-saturated conditions. Calculate the compensation irradiance $I_c$ where gross photosynthesis exactly balances respiration ($\text{GPP}(I_c) = |R|$) by numerically solving the equation $P_{\text{max}} \tanh(\alpha I_c / P_{\text{max}}) = |R|$ using SciPy's `fsolve`. Compensation irradiance defines the minimum light level for positive net growth; values typically range from 10-50 μmol m⁻² s⁻¹ for freshwater phytoplankton.

Assess model goodness-of-fit by calculating coefficient of determination $R^2 = 1 - \frac{\text{SS}_{\text{residual}}}{\text{SS}_{\text{total}}}$ where residual sum of squares equals $\sum_i (y_i - \hat{y}_i)^2$ and total sum of squares equals $\sum_i (y_i - \bar{y})^2$. Values exceeding 0.90 indicate excellent model fit. Plot residuals (observed minus predicted GPP) against irradiance to diagnose systematic deviations: random scatter confirms model adequacy, while patterned residuals (e.g., consistent overestimation at intermediate irradiance) suggest model misspecification.

Propagate measurement uncertainties through the P-I model by conducting Monte Carlo simulation. For each of 5,000 iterations, perturb the observed GPP values by adding random Gaussian noise with standard deviation equal to the measurement uncertainty, refit the model parameters, and store the results. The distributions of $P_{\text{max}}$ and $\alpha$ values across iterations quantify parameter uncertainty arising from measurement error. Calculate 95% confidence intervals as the 2.5th and 97.5th percentiles of these distributions.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

This advanced exercise models predator-prey population dynamics through coupled differential equations fitted to multi-year census time series, testing model robustness under parameter perturbations and initial condition variations. You will implement Lotka-Volterra equations numerically, calibrate parameters using real ecological data or realistic synthetic datasets, execute phase-plane analysis revealing stable limit cycles, conduct sensitivity analysis quantifying parameter influence on population trajectories, and assess model identifiability through likelihood profiling. The exercise synthesizes population ecology theory with computational dynamical systems analysis.

The canonical Lotka-Volterra predator-prey model couples herbivore (prey) and carnivore (predator) population dynamics through consumption interactions. Prey population $V(t)$ grows exponentially in predator absence at rate $\alpha$ but suffers predation mortality at rate $\beta$ proportional to predator-prey encounter frequency. Predator population $P(t)$ declines exponentially at rate $\gamma$ without prey but increases through conversion of consumed prey biomass at efficiency $\delta$. The resulting system of ordinary differential equations reads:

$$\frac{dV}{dt} = \alpha V - \beta VP$$
$$\frac{dP}{dt} = \delta VP - \gamma P$$

This model conserves total energy: prey energy $V$ flows into predator biomass $P$ at rate $\delta \beta VP$ with conversion efficiency $\delta < \beta$ (typically 0.1-0.3 due to metabolic losses). The system exhibits neutrally stable oscillations around equilibrium point $(V^*, P^*) = (\gamma/\delta, \alpha/\beta)$ where growth rates balance. Real ecosystems deviate from neutral stability due to self-limitation terms omitted in the basic model; incorporating logistic prey growth with a saturating functional response (Rosenzweig–MacArthur model) can yield a stable limit cycle; pure logistic prey growth with linear predation yields a stable equilibrium.

Obtain time series census data for a predator-prey system: classic examples include Canadian lynx and snowshoe hare records (Hudson's Bay Company fur trading data, 1845-1935) or Isle Royale wolf and moose populations (National Park Service monitoring, 1959-present). Alternatively, generate synthetic data by numerically integrating the Lotka-Volterra equations with known parameters and adding observational noise, simulating realistic census uncertainty. We adopt the synthetic approach here to ensure pedagogical control while maintaining ecological realism.

Implement numerical integration of the Lotka-Volterra equations using SciPy's `solve_ivp` function with the Runge-Kutta 4(5) method (RK45), an adaptive-step explicit method well-suited to non-stiff oscillatory systems; stiff systems require implicit solvers such as RADAU or BDF. Define the derivative function encoding the right-hand sides of the differential equations, specify initial conditions and time span, then invoke the integrator:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import pandas as pd

# Define Lotka-Volterra model
def lotka_volterra(t, y, alpha, beta, delta, gamma):
    """
    Lotka-Volterra predator-prey model.
    y[0] = V (prey population)
    y[1] = P (predator population)
    """
    V, P = y
    dV_dt = alpha * V - beta * V * P
    dP_dt = delta * V * P - gamma * P
    return [dV_dt, dP_dt]

# True parameters for synthetic data generation
alpha_true = 0.5   # prey growth rate (yr^-1)
beta_true = 0.02   # predation rate (individuals^-1 yr^-1)
delta_true = 0.01  # predator conversion efficiency (individuals^-1 yr^-1)
gamma_true = 0.3   # predator mortality rate (yr^-1)

# Initial conditions
V0 = 40.0  # initial prey population
P0 = 9.0   # initial predator population
y0 = [V0, P0]

# Time span for simulation (50 years)
t_span = (0, 50)
t_eval = np.linspace(0, 50, 200)

# Solve system with true parameters
sol_true = solve_ivp(
    lotka_volterra, 
    t_span, 
    y0, 
    args=(alpha_true, beta_true, delta_true, gamma_true),
    t_eval=t_eval,
    method='RK45',
    rtol=1e-8,
    atol=1e-10
)

V_true = sol_true.y[0]
P_true = sol_true.y[1]

# Generate synthetic census data: subsample time series and add observation noise
census_times = np.arange(0, 51, 2.0)  # biennial census
V_census = np.interp(census_times, sol_true.t, V_true)
P_census = np.interp(census_times, sol_true.t, P_true)

# Add Gaussian observation noise (CV = 15%)
np.random.seed(123)
V_observed = V_census + np.random.normal(0, 0.15 * V_census)
P_observed = P_census + np.random.normal(0, 0.15 * P_census)

# Ensure non-negative populations
V_observed = np.maximum(V_observed, 1.0)
P_observed = np.maximum(P_observed, 1.0)

print("=== Synthetic Census Data Generated ===")
print(f"Number of census points: {len(census_times)}")
print(f"Prey population range: {V_observed.min():.1f} - {V_observed.max():.1f}")
print(f"Predator population range: {P_observed.min():.1f} - {P_observed.max():.1f}")

# Plot synthetic time series
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axes[0].plot(sol_true.t, V_true, '-', linewidth=2, color='forestgreen', label='True prey trajectory', alpha=0.7)
axes[0].plot(census_times, V_observed, 'o', markersize=8, color='darkgreen', label='Observed census data')
axes[0].set_ylabel("Prey Population (V)", fontsize=12)
axes[0].legend(loc='upper right')
axes[0].grid(alpha=0.3)

axes[1].plot(sol_true.t, P_true, '-', linewidth=2, color='crimson', label='True predator trajectory', alpha=0.7)
axes[1].plot(census_times, P_observed, 's', markersize=8, color='darkred', label='Observed census data')
axes[1].set_xlabel("Time (years)", fontsize=12)
axes[1].set_ylabel("Predator Population (P)", fontsize=12)
axes[1].legend(loc='upper right')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('synthetic_census_timeseries.png', dpi=300, bbox_inches='tight')
plt.show()
```

Calibrate model parameters by minimizing the sum of squared residuals between observed census data and model predictions. Define the objective function as the total squared deviation across both species and all census time points:

$$\text{SSR}(\theta) = \sum_{i=1}^{n} \left[ (V_i^{\text{obs}} - V_i^{\text{model}})^2 + (P_i^{\text{obs}} - P_i^{\text{model}})^2 \right]$$

where $\theta = (\alpha, \beta, \delta, \gamma)$ represents the parameter vector and $n$ denotes the number of census occasions. Implement parameter optimization using the Nelder-Mead simplex algorithm through SciPy's `minimize` function, constraining all parameters to positive values through logarithmic transformation:

```python
# Define objective function for parameter fitting
def objective_function(log_params, census_times, V_obs, P_obs, V0, P0):
    """
    Sum of squared residuals between observed and predicted populations.
    Parameters are log-transformed to enforce positivity.
    """
    # Transform back to natural scale
    alpha, beta, delta, gamma = np.exp(log_params)
    
    # Simulate model
    sol = solve_ivp(
        lotka_volterra,
        (census_times[0], census_times[-1]),
        [V0, P0],
        args=(alpha, beta, delta, gamma),
        t_eval=census_times,
        method='RK45',
        rtol=1e-6,
        atol=1e-8
    )
    
    if not sol.success:
        return 1e10  # Large penalty if integration fails
    
    V_model = sol.y[0]
    P_model = sol.y[1]
    
    # Calculate sum of squared residuals
    ssr = np.sum((V_obs - V_model)**2) + np.sum((P_obs - P_model)**2)
    return ssr

# Initial parameter guesses (log-scale)
params_init = np.array([0.4, 0.018, 0.009, 0.28])
log_params_init = np.log(params_init)

# Optimize parameters
result = minimize(
    objective_function,
    log_params_init,
    args=(census_times, V_observed, P_observed, V_observed[0], P_observed[0]),
    method='Nelder-Mead',
    options={'maxiter': 5000, 'xatol': 1e-6, 'fatol': 1e-6}
)

# Extract fitted parameters
log_params_fit = result.x
params_fit = np.exp(log_params_fit)
alpha_fit, beta_fit, delta_fit, gamma_fit = params_fit

print("\n=== Parameter Estimation Results ===")
print(f"Fitted Parameters:")
print(f"  alpha (prey growth) = {alpha_fit:.4f} yr^-1  (true: {alpha_true:.4f})")
print(f"  beta (predation rate) = {beta_fit:.5f} ind^-1 yr^-1  (true: {beta_true:.5f})")
print(f"  delta (conversion efficiency) = {delta_fit:.5f} ind^-1 yr^-1  (true: {delta_true:.5f})")
print(f"  gamma (predator mortality) = {gamma_fit:.4f} yr^-1  (true: {gamma_true:.4f})")
print(f"\nFinal SSR = {result.fun:.2f}")
print(f"Optimization success: {result.success}")

# Simulate with fitted parameters
sol_fit = solve_ivp(
    lotka_volterra,
    t_span,
    [V_observed[0], P_observed[0]],
    args=(alpha_fit, beta_fit, delta_fit, gamma_fit),
    t_eval=t_eval,
    method='RK45',
    rtol=1e-8,
    atol=1e-10
)

V_fit = sol_fit.y[0]
P_fit = sol_fit.y[1]

# Plot fitted trajectories
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axes[0].plot(sol_fit.t, V_fit, '-', linewidth=2.5, color='royalblue', label='Fitted model')
axes[0].plot(census_times, V_observed, 'o', markersize=8, color='darkgreen', label='Observed data')
axes[0].set_ylabel("Prey Population (V)", fontsize=12)
axes[0].legend()
axes[0].grid(alpha=0.3)
axes[0].set_title("Model Fit to Census Data", fontsize=13, fontweight='bold')

axes[1].plot(sol_fit.t, P_fit, '-', linewidth=2.5, color='royalblue', label='Fitted model')
axes[1].plot(census_times, P_observed, 's', markersize=8, color='darkred', label='Observed data')
axes[1].set_xlabel("Time (years)", fontsize=12)
axes[1].set_ylabel("Predator Population (P)", fontsize=12)
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('model_fit_timeseries.png', dpi=300, bbox_inches='tight')
plt.show()
```

Conduct phase-plane analysis by plotting predator population $P$ against prey population $V$ to visualize the system's dynamical structure. The Lotka-Volterra model produces a one-parameter family of neutrally stable closed orbits in phase space, not isolated limit cycles, with trajectory shape determined by initial conditions and parameter values. Calculate equilibrium point $(V^*, P^*) = (\gamma/\delta, \alpha/\beta)$ and overlay it on the phase portrait as a fixed point. Compute nullclines where population growth rates equal zero: the prey nullcline ($dV/dt = 0$) occurs at $P = \alpha/\beta$ (horizontal line) and the predator nullcline ($dP/dt = 0$) at $V = \gamma/\delta$ (vertical line). Nullcline intersections identify equilibria, and nullcline crossings determine regions of phase space where populations increase versus decrease.

Generate phase portraits for multiple initial conditions to map the basin of attraction around the equilibrium:

```python
# Phase-plane analysis
fig, ax = plt.subplots(figsize=(10, 8))

# Calculate equilibrium point
V_eq = gamma_fit / delta_fit
P_eq = alpha_fit / beta_fit

# Plot nullclines
ax.axvline(V_eq, color='blue', linestyle='--', linewidth=2, alpha=0.6, label=f'Predator nullcline (V = {V_eq:.1f})')
ax.axhline(P_eq, color='green', linestyle='--', linewidth=2, alpha=0.6, label=f'Prey nullcline (P = {P_eq:.1f})')

# Plot equilibrium point
ax.plot(V_eq, P_eq, 'ko', markersize=12, label=f'Equilibrium ({V_eq:.1f}, {P_eq:.1f})', zorder=5)

# Simulate trajectories from multiple initial conditions
initial_conditions = [
    [20, 5], [40, 9], [60, 12], [30, 15], [50, 6]
]

for i, ic in enumerate(initial_conditions):
    sol_ic = solve_ivp(
        lotka_volterra,
        (0, 50),
        ic,
        args=(alpha_fit, beta_fit, delta_fit, gamma_fit),
        t_eval=np.linspace(0, 50, 500),
        method='RK45',
        rtol=1e-8
    )
    V_ic = sol_ic.y[0]
    P_ic = sol_ic.y[1]
    
    ax.plot(V_ic, P_ic, linewidth=1.8, alpha=0.7, label=f'IC: V={ic[0]}, P={ic[1]}')
    ax.plot(ic[0], ic[1], 'o', markersize=7, color=ax.lines[-1].get_color())

# Plot observed census trajectory
ax.plot(V_observed, P_observed, 'rs-', markersize=8, linewidth=2, label='Observed census', zorder=4)

ax.set_xlabel("Prey Population (V)", fontsize=13)
ax.set_ylabel("Predator Population (P)", fontsize=13)
ax.set_title("Phase-Plane Portrait: Predator-Prey Dynamics", fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.3)
ax.set_xlim(0, max(V_observed) * 1.3)
ax.set_ylim(0, max(P_observed) * 1.3)

plt.tight_layout()
plt.savefig('phase_plane_portrait.png', dpi=300, bbox_inches='tight')
plt.show()
```

Perform sensitivity analysis by perturbing each parameter individually by ±20% and measuring the resulting change in system behavior. Define sensitivity metrics: (1) period of population oscillations computed via peak-to-peak intervals, (2) oscillation amplitude measured as maximum minus minimum population levels, and (3) equilibrium population values. Calculate the dimensionless sensitivity coefficient $S_{X,\theta} = \frac{\partial \ln X}{\partial \ln \theta} \approx \frac{\Delta X / X}{\Delta \theta / \theta}$ which quantifies the percentage change in output metric $X$ per percentage change in parameter $\theta$. High absolute sensitivity ($|S| > 1$) indicates strong parameter influence requiring precise estimation; low sensitivity ($|S| < 0.1$) suggests parameter insensitivity allowing broad uncertainty.

Implement sensitivity analysis through finite-difference approximation:

```python
# Sensitivity analysis
parameters = {'alpha': alpha_fit, 'beta': beta_fit, 'delta': delta_fit, 'gamma': gamma_fit}
param_names = list(parameters.keys())
perturbation_fraction = 0.20

sensitivity_results = []

for param_name in param_names:
    # Perturb parameter up and down
    params_perturbed_up = parameters.copy()
    params_perturbed_down = parameters.copy()
    
    params_perturbed_up[param_name] *= (1 + perturbation_fraction)
    params_perturbed_down[param_name] *= (1 - perturbation_fraction)
    
    # Simulate with perturbed parameters
    sol_up = solve_ivp(
        lotka_volterra, t_span, [V_observed[0], P_observed[0]],
        args=(params_perturbed_up['alpha'], params_perturbed_up['beta'], 
              params_perturbed_up['delta'], params_perturbed_up['gamma']),
        t_eval=t_eval, method='RK45', rtol=1e-8
    )
    
    sol_down = solve_ivp(
        lotka_volterra, t_span, [V_observed[0], P_observed[0]],
        args=(params_perturbed_down['alpha'], params_perturbed_down['beta'],
              params_perturbed_down['delta'], params_perturbed_down['gamma']),
        t_eval=t_eval, method='RK45', rtol=1e-8
    )
    
    # Calculate metrics: mean prey population over last 20 years (equilibrium proxy)
    time_mask = sol_up.t >= 30
    V_mean_baseline = np.mean(V_fit[sol_fit.t >= 30])
    P_mean_baseline = np.mean(P_fit[sol_fit.t >= 30])
    
    V_mean_up = np.mean(sol_up.y[0][time_mask])
    P_mean_up = np.mean(sol_up.y[1][time_mask])
    V_mean_down = np.mean(sol_down.y[0][time_mask])
    P_mean_down = np.mean(sol_down.y[1][time_mask])
    
    # Calculate sensitivity coefficients
    S_V = ((V_mean_up - V_mean_down) / V_mean_baseline) / (2 * perturbation_fraction)
    S_P = ((P_mean_up - P_mean_down) / P_mean_baseline) / (2 * perturbation_fraction)
    
    sensitivity_results.append({
        'Parameter': param_name,
        'Baseline Value': parameters[param_name],
        'S_V (prey sensitivity)': S_V,
        'S_P (predator sensitivity)': S_P
    })
    
    print(f"\n{param_name} sensitivity:")
    print(f"  S_V = {S_V:.3f}")
    print(f"  S_P = {S_P:.3f}")

sensitivity_df = pd.DataFrame(sensitivity_results)
sensitivity_df.to_csv('sensitivity_analysis.csv', index=False)
print("\nSensitivity analysis exported to 'sensitivity_analysis.csv'")

# Plot sensitivity coefficients
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(param_names))
width = 0.35

bars1 = ax.bar(x - width/2, sensitivity_df['S_V (prey sensitivity)'], width, 
               label='Prey sensitivity', color='forestgreen', alpha=0.8)
bars2 = ax.bar(x + width/2, sensitivity_df['S_P (predator sensitivity)'], width,
               label='Predator sensitivity', color='crimson', alpha=0.8)

ax.set_xlabel("Parameter", fontsize=13)
ax.set_ylabel("Sensitivity Coefficient S", fontsize=13)
ax.set_title("Parameter Sensitivity Analysis", fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(param_names)
ax.legend()
ax.axhline(0, color='black', linewidth=0.8)
ax.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('sensitivity_coefficients.png', dpi=300, bbox_inches='tight')
plt.show()
```

Test model robustness under extreme boundary conditions by simulating scenarios where parameters approach biologically plausible limits. Reduce prey growth rate $\alpha$ by 50% to simulate resource depletion, increase predator mortality $\gamma$ by 100% to model disease outbreak, and halve predation efficiency $\beta$ to represent prey refuge availability. For each scenario, determine whether the system maintains stable oscillations, collapses to predator extinction, or exhibits prey population explosion. Document the parameter threshold where qualitative dynamics shift, identifying tipping points in ecosystem resilience.

Assess parameter identifiability through likelihood profile analysis. For each parameter, fix it at a range of values spanning ±50% of the fitted estimate, re-optimize the remaining three parameters, and calculate the profile likelihood (negative log-likelihood or SSR). Identifiable parameters exhibit sharp, parabolic likelihood profiles with clear global minima, while non-identifiable parameters produce flat profiles indicating that data cannot distinguish among parameter values. Plot the profile log-likelihood against parameter value; confidence intervals correspond to the parameter range where profile likelihood increases by 1.92 units (for 95% confidence in a single parameter based on chi-squared distribution with 1 degree of freedom).

This exercise demonstrates that ecological models require iterative calibration against empirical data, sensitivity analysis to prioritize measurement precision for influential parameters, and boundary stress testing to map domains of model validity. Real predator-prey systems exhibit stochasticity, spatial structure, and age/stage structure absent from the Lotka-Volterra formulation, necessitating model extensions for predictive accuracy in conservation and management applications.

## Laboratory Cheat Sheet & Metric Verification Guide

This reference consolidates essential field protocols, instrument calibration procedures, statistical tests, and computational verification commands for rapid troubleshooting and quality assurance during ecological laboratory operations.

**Vegetation Sampling Protocol Summary:**
- Quadrat size: 1 m² for herbaceous vegetation, 10 m² for woody vegetation, 0.25 m² for cryptogams
- Minimum sample size: 10 quadrats per vegetation type, 30 quadrats for publishable community analysis
- Stratified random sampling: divide study area into homogeneous strata, allocate samples proportionally
- Species identification: voucher specimens required for non-flowering plants and critical taxa
- Recording protocol: species binomial, count/cover class, growth stage, plot coordinates, date, observer initials

**Dissolved Oxygen Measurement Calibration:**
- Zero calibration: Na₂SO₃ solution (2 g/100 mL) with cobalt chloride catalyst, target < 0.2 mg/L
- Saturation calibration: air-saturated water at ambient temperature and pressure
- Barometric correction: $C_{\text{sat}} = C_{\text{standard}} \times (P_{\text{local}} - P_{\text{vapor}})/101.325$ kPa
- Temperature compensation: automatic on modern probes, manual correction using $C(T) = C(20°\text{C}) \times e^{-0.0178(T-20)}$
- Maintenance: replace membrane monthly, rinse electrode after each use, store in moist environment

**Statistical Test Selection Decision Tree:**
- Comparing two means, normal distribution, equal variances → two-sample t-test (`scipy.stats.ttest_ind`)
- Comparing two means, non-normal distribution → Mann-Whitney U test (`scipy.stats.mannwhitneyu`)
- Comparing multiple means, normal distribution → one-way ANOVA (`scipy.stats.f_oneway`)
- Comparing multiple means, non-normal → Kruskal-Wallis test (`scipy.stats.kruskal`)
- Testing association between variables → Pearson correlation (`scipy.stats.pearsonr`) or Spearman rank correlation (`scipy.stats.spearmanr`)

**Diversity Index Formulas and Interpretation:**
- Shannon index: $H' = -\sum p_i \ln(p_i)$, range 0 to $\ln(S)$, typical values 1.5-3.5
- Simpson index: $D = 1 - \sum p_i^2$, range 0 to 1, less sensitive to rare species than Shannon
- Evenness: $J' = H' / \ln(S)$, range 0 to 1, measures equitability independent of richness
- Rarefaction: standardizes richness to equal sample sizes; no direct scipy implementation exists; compute manually with NumPy or use dedicated packages (e.g., scikit-bio)

**Primary Productivity Calculation Reference:**
- Light bottle: $\Delta \text{DO}_L = \text{DO}_{\text{final}} - \text{DO}_{\text{initial}}$ (net community productivity)
- Dark bottle: $\Delta \text{DO}_D = \text{DO}_{\text{final}} - \text{DO}_{\text{initial}}$ (respiration, negative value)
- Gross primary productivity: $\text{GPP} = \Delta \text{DO}_L + |\Delta \text{DO}_D|$ (in mg O₂ L⁻¹ hr⁻¹), where |ΔDO_D| is the magnitude of respiration
- Net primary productivity: $\text{NPP} = \Delta \text{DO}_L$ (photosynthesis minus autotrophic respiration)
- Carbon conversion: with PQ = 1.2 multiply O₂ values by 0.3125 to convert mg O₂ to mg C; use 0.375 only when PQ = 1.0

**Photosynthesis-Irradiance Model Parameters:**
- $P_{\text{max}}$: light-saturated photosynthesis rate, typical range 1-5 mg O₂ L⁻¹ hr⁻¹
- $\alpha$: photosynthetic efficiency (initial slope), typical range 0.005-0.02
- $I_k = P_{\text{max}}/\alpha$: saturation irradiance, typical range 100-500 μmol m⁻² s⁻¹
- $I_c$: compensation irradiance where GPP = R, typical range 10-50 μmol m⁻² s⁻¹

**Lotka-Volterra Model Equilibria and Stability:**
- Equilibrium prey: $V^* = \gamma / \delta$ (predator mortality / conversion efficiency)
- Equilibrium predator: $P^* = \alpha / \beta$ (prey growth / predation rate)
- Period of oscillation: $T \approx 2\pi / \sqrt{\alpha \gamma}$ (approximate for small amplitude cycles)
- Stability: neutrally stable in basic model, stable limit cycle with logistic prey growth

**Error Propagation Formulas:**
- Sum/difference: $\sigma_{X \pm Y} = \sqrt{\sigma_X^2 + \sigma_Y^2}$
- Product/quotient: $\sigma_{XY} / |XY| = \sqrt{(\sigma_X/X)^2 + (\sigma_Y/Y)^2}$
- Power function: $\sigma_{X^n} / |X^n| = |n| \sigma_X / |X|$
- General function: $\sigma_f \approx \sqrt{\sum_i (\partial f/\partial x_i)^2 \sigma_{x_i}^2}$ (first-order Taylor approximation)

**Python Environment Verification Commands:**
```bash
# Verify scientific stack installation
python -c "import numpy; print(f'NumPy {numpy.__version__}')"
python -c "import scipy; print(f'SciPy {scipy.__version__}')"
python -c "import matplotlib; print(f'Matplotlib {matplotlib.__version__}')"
python -c "import pandas; print(f'pandas {pandas.__version__}')"

# Test numerical integration
python -c "from scipy.integrate import solve_ivp; print('solve_ivp available')"

# Test optimization routines
python -c "from scipy.optimize import minimize, curve_fit; print('Optimization tools available')"

# Test statistical functions
python -c "from scipy.stats import ttest_ind, pearsonr; print('Statistical tests available')"
```

**Common Field Equipment Specifications:**
- GPS accuracy: ±3-10 m (consumer units), ±0.3-1 m (differential GPS), ±0.01 m (RTK GPS)
- DO probe precision: ±0.1-0.2 mg/L (optical), ±0.3 mg/L (electrochemical Clark electrode)
- Thermometer accuracy: ±0.1°C (digital electronic), ±0.2°C (alcohol thermometer)
- Spectrophotometer wavelength accuracy: ±1 nm, absorbance precision ±0.002 AU
- Analytical balance readability: 0.1 mg (milligram), 0.01 mg (sub-milligram for ash-free dry mass)

**Data Quality Control Checklist:**
- Record metadata: date, time, location (GPS coordinates), weather conditions, observers
- Include field blanks and replicates: minimum 10% of samples as quality control
- Photograph vouchers and representative samples for documentation
- Calibrate instruments daily: zero and span checks before measurements
- Verify units consistency: convert all measurements to SI units before analysis
- Check for outliers: values exceeding 3 standard deviations from mean warrant re-measurement
- Document deviations from protocol: note equipment malfunctions, weather interruptions, access limitations

**Bootstrap Resampling Implementation Template:**
```python
# Generic bootstrap for any statistic
def bootstrap_statistic(data, statistic_func, n_iterations=10000):
    n = len(data)
    bootstrap_stats = np.zeros(n_iterations)
    for i in range(n_iterations):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic_func(sample)
    ci_lower = np.percentile(bootstrap_stats, 2.5)
    ci_upper = np.percentile(bootstrap_stats, 97.5)
    return bootstrap_stats, ci_lower, ci_upper
```

**Model Fitting Diagnostics:**
- Coefficient of determination: $R^2 = 1 - \text{SS}_{\text{res}}/\text{SS}_{\text{tot}}$, target >0.85 for good fit
- Root mean square error: $\text{RMSE} = \sqrt{\frac{1}{n}\sum(y_i - \hat{y}_i)^2}$, compare to data standard deviation
- Akaike information criterion: $\text{AIC} = 2k - 2\ln(L)$ where $k$ is parameter count, prefer lower values
- Residual patterns: plot residuals vs. predicted values and vs. independent variable, check for heteroscedasticity
- Cook's distance: identify influential points exceeding $4/n$ threshold warranting sensitivity analysis

This cheat sheet provides rapid access to critical operational parameters, verification procedures, and diagnostic criteria required for maintaining measurement quality and analytical rigor throughout ecological field campaigns and laboratory analyses. Consult original method references (APHA, EPA, journal protocols) for detailed procedural specifications and method detection limits relevant to your specific research objectives.
