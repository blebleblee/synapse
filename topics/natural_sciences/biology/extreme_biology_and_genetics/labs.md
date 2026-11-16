# Operational Verification Labs: Extreme Biology and Genetics

## Objective & Laboratory Bench Setup

This guide is a practitioner's manual for researchers working at the edges of biological possibility: extremophile physiology, stress-induced genomic adaptation, horizontal gene transfer under selective pressure, and the quantitative genetics of populations pushed beyond ordinary viability thresholds. The exercises that follow are not demonstrations of textbook principles but active empirical investigations. You will measure real physical quantities, fit real models to real data, and discover where biological systems break down or transform under extreme conditions.

The organizing question across all three exercises is this: how do living systems maintain heritable function when their physical and chemical environment exceeds the design envelope of ordinary life? Answering it requires you to work simultaneously in the wet lab (spectrophotometry, thermal stress assays, gel electrophoresis) and the computational environment (Python, NumPy, SciPy, Matplotlib), treating both as equally primary instruments. Neither domain is subordinate to the other.

Before any experiment begins, verify that your computational environment is consistent and that your physical instruments are calibrated. Run the following verification sequence in your terminal:

```bash
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
```

You should see version numbers at or above NumPy 1.24, SciPy 1.10, Matplotlib 3.7, and Pandas 2.0. If any import fails, install the missing package with `pip install numpy scipy matplotlib pandas` before proceeding.

Your physical bench requires the following instrumentation and consumables. A UV-Vis spectrophotometer capable of absorbance measurements at 260 nm, 280 nm, and 600 nm is essential: the first two wavelengths are for nucleic acid and protein quantification respectively, and the 600 nm optical density reading (OD₆₀₀) is your primary proxy for bacterial cell density throughout all growth experiments. You will also need a temperature-controlled incubator or water bath with a range of at least 4 °C to 95 °C, accurate to ±0.5 °C, and a vortex mixer, microcentrifuge (minimum 12,000 × g), gel electrophoresis apparatus, and a UV transilluminator for nucleic acid visualization. For the genomic stress experiment, you will need a thermocycler for PCR amplification and either a Nanodrop spectrophotometer or fluorometric quantification system (e.g., Qubit) for precise DNA concentration measurement.

Your biological materials consist of two strains: a mesophilic model organism (Escherichia coli K-12, strain MG1655, grown in Lysogeny Broth at 37 °C) and, if available, a thermophilic comparator (Thermus thermophilus HB8, grown in Thermus broth at 65 °C). The E. coli strain serves as the stress target across all exercises. The T. thermophilus strain provides empirical reference points for GC content, membrane lipid saturation, and enzyme thermostability that illuminate what "extreme" adaptation looks like in evolved systems.

Reagents on hand before starting: LB broth and LB agar, 10× TAE buffer for electrophoresis, ethidium bromide or SYBR Safe DNA stain, agarose (molecular biology grade), a standard DNA ladder (1 kb plus ladder), Phusion or Q5 high-fidelity DNA polymerase with its supplied buffer, dNTP mix at 10 mM each, primer pairs targeting a conserved genomic locus (16S rRNA gene, with universal primers 27F: 5′-AGAGTTTGATCMTGGCTCAG-3′ and 1492R: 5′-TACGGYTACCTTGTTACGACTT-3′), and a commercial genomic DNA extraction kit appropriate for bacterial samples.

The theoretical backbone you need to hold in mind throughout these exercises is compact but non-negotiable. Biological macromolecules operate within narrow thermodynamic windows: proteins denature when thermal energy exceeds the cooperative stabilization energy of their tertiary structure ($\Delta G_{\text{fold}} < 0$ for the native state, approaching zero at the melting temperature $T_m$), membranes undergo phase transitions from fluid to gel when temperature drops below the lipid solidification point, and nucleic acids undergo strand separation when thermal energy overcomes base-stacking and hydrogen-bonding forces. Extremophiles have evolved molecular adaptations—increased GC content in ribosomal RNA stems, saturated versus unsaturated fatty acid ratios tuned for membrane fluidity, and charged surface residues on thermostable enzymes—that shift these transition points into extreme ranges. Your measurements will make these abstract thermodynamic shifts visible as concrete numbers.

---

## Exercise 1: Empirical Observation & Measurement Protocol

### Growth Kinetics Under Thermal Stress: Building the OD₆₀₀ Time Series

The first exercise establishes your baseline empirical picture of how an organism's growth rate responds to temperature as a primary stressor. You will grow E. coli MG1655 at five distinct temperatures spanning its viability range, measure optical density at regular intervals over twelve hours, and extract the exponential growth rate constant $\mu$ (units: h⁻¹) from each time series. The relationship between $\mu$ and temperature follows a modified Arrhenius-type response up to the optimal temperature, followed by a catastrophic collapse at supraoptimal temperatures where protein denaturation outpaces adaptive responses. Measuring this curve empirically, rather than accepting textbook values, is the entire point.

Begin by preparing a 10 mL overnight culture of E. coli MG1655 in LB broth at 37 °C with shaking at 200 rpm. After 14–16 hours, the culture will be in stationary phase, with OD₆₀₀ typically between 1.8 and 2.2. Dilute this overnight culture 1:100 into five separate 50 mL conical flasks, each containing 20 mL of fresh LB broth, giving a starting OD₆₀₀ of approximately 0.018–0.022. Place these flasks immediately into water baths or incubators set at 20 °C, 30 °C, 37 °C, 42 °C, and 48 °C respectively, all with shaking at 200 rpm to ensure oxygenation. Record the actual bath temperature with a calibrated thermometer at every measurement point—do not rely on the thermostat dial.

Withdraw 1 mL samples from each flask at t = 0, 1, 2, 3, 4, 6, 8, 10, and 12 hours. Blank your spectrophotometer with sterile LB broth before each measurement session. If OD₆₀₀ exceeds 0.8 during the exponential phase, dilute the sample 1:2 or 1:4 with sterile LB and multiply the reading by the dilution factor before recording. High-absorbance readings above 0.8 deviate from Beer-Lambert linearity due to multiple scattering and will distort your growth rate estimates if used uncorrected. Record all raw readings, dilution factors, and actual temperatures in a structured lab notebook or directly into the data file format described below.

Enter your time-series data into the following Python script immediately after each measurement session. The script fits a logistic growth model to each temperature series, extracts $\mu$, and plots the full response curve. Working through the analysis in real time allows you to detect pipetting errors or instrument drift before the culture has grown beyond the measurement window.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

# --- DATA ENTRY: replace these values with your actual OD600 readings ---
# Format: each row is [time_hours, OD_20C, OD_30C, OD_37C, OD_42C, OD_48C]
raw_data = np.array([
    [0,   0.020, 0.021, 0.019, 0.020, 0.021],
    [1,   0.021, 0.028, 0.038, 0.031, 0.022],
    [2,   0.023, 0.041, 0.085, 0.058, 0.023],
    [3,   0.026, 0.063, 0.198, 0.112, 0.024],
    [4,   0.030, 0.098, 0.410, 0.223, 0.024],
    [6,   0.044, 0.221, 1.102, 0.651, 0.025],
    [8,   0.067, 0.489, 1.651, 1.388, 0.026],
    [10,  0.098, 0.891, 1.782, 1.712, 0.026],
    [12,  0.133, 1.312, 1.801, 1.724, 0.026],
])

temperatures = [20, 30, 37, 42, 48]
time_h = raw_data[:, 0]
od_matrix = raw_data[:, 1:]

# --- LOGISTIC GROWTH MODEL ---
# N(t) = K / (1 + ((K - N0)/N0) * exp(-mu * t))
# Parameters: K = carrying capacity, N0 = initial OD, mu = growth rate (h^-1)
def logistic_growth(t, K, N0, mu):
    return K / (1.0 + ((K - N0) / N0) * np.exp(-mu * t))

# --- FIT AND EXTRACT GROWTH RATES ---
fitted_mu = []
fitted_K  = []
fit_params_all = []

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for i, temp in enumerate(temperatures):
    od_series = od_matrix[:, i]
    # Initial parameter guesses: K near max OD, N0 near first point, mu ~ 0.5
    p0 = [max(od_series) * 1.05, od_series[0], 0.5]
    bounds = ([0.05, 0.001, 0.001], [3.0, 0.5, 5.0])
    try:
        popt, pcov = curve_fit(
            logistic_growth, time_h, od_series,
            p0=p0, bounds=bounds, maxfev=10000
        )
        K_fit, N0_fit, mu_fit = popt
        K_err = np.sqrt(pcov[0, 0])
        mu_err = np.sqrt(pcov[2, 2])
        fitted_mu.append(mu_fit)
        fitted_K.append(K_fit)
        fit_params_all.append((K_fit, K_err, mu_fit, mu_err))
        label = f"{temp}°C  μ={mu_fit:.3f}±{mu_err:.3f} h⁻¹"
    except RuntimeError:
        fitted_mu.append(np.nan)
        fitted_K.append(np.nan)
        fit_params_all.append((np.nan, np.nan, np.nan, np.nan))
        label = f"{temp}°C  fit failed"

    t_fine = np.linspace(0, 13, 300)
    if not np.isnan(fitted_mu[i]):
        od_fit = logistic_growth(t_fine, *popt)
        axes[0].plot(t_fine, od_fit, color=colors[i], linewidth=1.5)
    axes[0].scatter(time_h, od_series, color=colors[i], s=40,
                    zorder=5, label=label)

axes[0].set_xlabel('Time (h)', fontsize=12)
axes[0].set_ylabel('OD₆₀₀', fontsize=12)
axes[0].set_title('E. coli Growth Curves Under Thermal Stress', fontsize=13)
axes[0].legend(fontsize=9, loc='lower right')
axes[0].set_ylim(bottom=0)
axes[0].grid(True, alpha=0.3)

# --- TEMPERATURE RESPONSE CURVE ---
valid_mask = ~np.isnan(fitted_mu)
valid_temps = np.array(temperatures)[valid_mask]
valid_mu    = np.array(fitted_mu)[valid_mask]

axes[1].scatter(valid_temps, valid_mu, color='crimson', s=80, zorder=5,
                label='Measured μ (h⁻¹)')
axes[1].set_xlabel('Temperature (°C)', fontsize=12)
axes[1].set_ylabel('Specific Growth Rate μ (h⁻¹)', fontsize=12)
axes[1].set_title('Temperature–Growth Rate Response Curve', fontsize=13)
axes[1].grid(True, alpha=0.3)

# Annotate each point with its value
for t_val, mu_val in zip(valid_temps, valid_mu):
    axes[1].annotate(
        f'μ={mu_val:.3f}',
        (t_val, mu_val),
        textcoords='offset points',
        xytext=(6, 6),
        fontsize=9
    )

axes[1].legend(fontsize=10)
plt.tight_layout()
plt.savefig('exercise1_growth_kinetics.png', dpi=150, bbox_inches='tight')
plt.show()

# --- SUMMARY TABLE ---
print("\n--- Growth Rate Summary ---")
print(f"{'Temp (°C)':<12} {'K (OD)':<12} {'K err':<10} {'μ (h⁻¹)':<12} {'μ err':<10}")
print("-" * 56)
for temp, params in zip(temperatures, fit_params_all):
    K_v, K_e, mu_v, mu_e = params
    if np.isnan(mu_v):
        print(f"{temp:<12} {'N/A':<12} {'N/A':<10} {'N/A':<12} {'N/A':<10}")
    else:
        print(f"{temp:<12} {K_v:<12.4f} {K_e:<10.4f} {mu_v:<12.4f} {mu_e:<10.4f}")

# Doubling time from mu: t_d = ln(2) / mu
print("\n--- Doubling Time (t_d = ln2 / μ) ---")
for temp, params in zip(temperatures, fit_params_all):
    mu_v = params[2]
    if not np.isnan(mu_v) and mu_v > 0:
        td = np.log(2) / mu_v
        print(f"  {temp}°C: t_d = {td:.2f} h  ({td*60:.1f} min)")
```

After running this script and saving the figure, examine the temperature response panel carefully. The growth rate $\mu$ should peak near 37 °C for E. coli, then fall sharply between 42 °C and 48 °C. The 48 °C flask will show minimal or zero growth in a healthy experiment, which is precisely the boundary condition you will probe further in Exercise 3. The near-zero growth rate at 20 °C, combined with the absence of death, illustrates the distinction between bacteriostasis (metabolic slowdown below the optimal temperature) and lethality (irreversible membrane and protein damage above it).

### DNA Quantification: Measuring Genomic Integrity Under Stress

Collect 1.5 mL from each flask at the 8-hour mark, pellet the cells by centrifugation at 10,000 × g for 2 minutes, discard the supernatant, and extract genomic DNA using your kit's protocol (typically: enzymatic lysis with lysozyme at 37 °C for 30 minutes, followed by proteinase K digestion, binding to a silica column, washing with ethanol-based buffer, and elution with low-TE buffer or nuclease-free water). Measure the DNA concentration and purity on the Nanodrop or spectrophotometer using the 260/280 nm ratio. A ratio of 1.8–2.0 indicates pure DNA. Values below 1.7 indicate protein contamination; values above 2.1 indicate RNA contamination or buffer artifacts. Record all ratios alongside concentrations.

The 260/280 purity ratio is not merely a quality-control checkbox. For cells grown under thermal stress, protein contamination of the nucleic acid fraction can itself be an experimental signal: at temperatures approaching the heat-shock threshold (42–45 °C for E. coli), cells upregulate chaperone proteins and may exhibit altered membrane permeability, increasing co-extraction of protein with DNA during lysis. If your 42 °C sample shows a consistently lower 260/280 ratio than the 37 °C control after multiple independent extractions, this is worth noting as a secondary observation and reporting with appropriate uncertainty bounds.

---

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### PCR Amplification of the 16S rRNA Gene Across Extracted DNA Templates

The second exercise moves from whole-organism physiology into the molecular layer. You will PCR-amplify the 16S rRNA gene from the genomic DNA extracted in Exercise 1, vary the annealing temperature across a gradient to establish a calibration curve for primer efficiency, quantify amplicon yield by gel densitometry, and use the yield-versus-annealing-temperature relationship to understand how melting thermodynamics govern primer hybridization in real experimental conditions.

The melting temperature $T_m$ of a DNA duplex governs whether a primer will anneal efficiently during PCR. For short oligonucleotides (primers typically 18–25 bp), the nearest-neighbor thermodynamic model gives:

$$T_m = \frac{\Delta H^\circ}{\Delta S^\circ + R \ln(C_T / 4)} - 273.15$$

where $\Delta H^\circ$ is the enthalpy of duplex formation (J mol⁻¹), $\Delta S^\circ$ is the entropy (J mol⁻¹ K⁻¹), $R = 8.314$ J mol⁻¹ K⁻¹, and $C_T$ is the total strand concentration (mol L⁻¹). For the 27F primer (5′-AGAGTTTGATCMTGGCTCAG-3′, 20 nt), the predicted $T_m$ using the nearest-neighbor model in 50 mM Na⁺ is approximately 56 °C, depending on the M/C ambiguity base. You will determine the empirical optimum experimentally, which is the more reliable number for your specific polymerase and buffer system.

Prepare a 96-well PCR plate (or eight individual 0.2 mL tubes) using a thermocycler gradient function set to cover annealing temperatures of 48 °C, 50 °C, 52 °C, 54 °C, 56 °C, 58 °C, 60 °C, and 62 °C. Each reaction tube receives: 10 µL of 2× Q5 reaction buffer (or equivalent high-fidelity master mix), 1 µL of 10 µM 27F primer, 1 µL of 10 µM 1492R primer, 1 µL of template DNA diluted to 10 ng µL⁻¹ in nuclease-free water, and nuclease-free water to a final volume of 20 µL. Use template DNA from your 37 °C growth flask for all eight gradient reactions so that template quality is constant across the annealing temperature variable.

The thermocycler program is: initial denaturation at 98 °C for 30 seconds; then 30 cycles of 98 °C for 10 seconds (denaturation), gradient temperature for 30 seconds (annealing), and 72 °C for 90 seconds (extension at 1 kb per minute for Q5); final extension at 72 °C for 2 minutes. Run all eight reactions simultaneously on the gradient block.

After PCR, cast a 1% agarose gel in 1× TAE buffer with SYBR Safe at 1× final concentration. Load 5 µL of each PCR product alongside 5 µL of your 1 kb plus DNA ladder. Run electrophoresis at 100 V for 45 minutes. The expected amplicon size for 27F/1492R is approximately 1,465 bp. Under UV illumination, photograph the gel immediately.

To quantify band intensity from your gel photograph, use the following Python script. You will need to load the gel image as a grayscale NumPy array and extract intensity profiles. This technique, called gel lane densitometry, converts fluorescent band brightness into a proxy for DNA mass based on intercalating dye stoichiometry.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, gaussian
from scipy.ndimage import uniform_filter1d
from scipy.optimize import curve_fit

# -----------------------------------------------------------------------
# SECTION 1: SIMULATED GEL DENSITOMETRY
# In fieldwork, replace this section by loading your actual gel image:
#   from PIL import Image
#   img = np.array(Image.open('gel_photo.tif').convert('L'))
#   Then define lane_start_x, lane_width, and band_roi_rows from your image.
#
# Here we simulate a realistic gradient PCR gel with known band intensities
# to demonstrate the full analysis pipeline on runnable data.
# -----------------------------------------------------------------------

np.random.seed(42)
gel_height = 400   # pixels (vertical = migration distance)
gel_width  = 600   # pixels (horizontal = lanes)
n_lanes    = 8     # gradient annealing temperatures
lane_width = gel_width // (n_lanes + 2)  # +2 for ladder lanes each side

# Simulate band intensity as a function of annealing temperature.
# True amplification efficiency follows a bell-curve peaking near 56°C.
annealing_temps = np.array([48, 50, 52, 54, 56, 58, 60, 62])

# Gaussian efficiency model: peak at 56°C, sigma ~4°C
def pcr_efficiency_model(T, T_opt, sigma, A):
    return A * np.exp(-0.5 * ((T - T_opt) / sigma) ** 2)

true_efficiency = pcr_efficiency_model(annealing_temps, 56.0, 4.5, 1.0)
# Map efficiency to pixel intensity (0–255 scale, background ~20)
max_intensity = 220
background    = 20
band_intensities = background + true_efficiency * (max_intensity - background)

# Build synthetic gel image
gel = np.full((gel_height, gel_width), background, dtype=np.float64)
band_row   = int(gel_height * 0.55)   # ~55% down the gel = 1465 bp band
band_sigma = 8                         # vertical spread of band in pixels

for lane_idx in range(n_lanes):
    lane_center_x = (lane_idx + 1) * lane_width + lane_width // 2
    # Add Gaussian band vertically
    for row in range(gel_height):
        intensity_contrib = band_intensities[lane_idx] * np.exp(
            -0.5 * ((row - band_row) / band_sigma) ** 2
        )
        col_start = lane_center_x - lane_width // 3
        col_end   = lane_center_x + lane_width // 3
        gel[row, col_start:col_end] += intensity_contrib

# Add Gaussian noise
gel += np.random.normal(0, 3, gel.shape)
gel = np.clip(gel, 0, 255)

# -----------------------------------------------------------------------
# SECTION 2: LANE INTENSITY PROFILE EXTRACTION
# -----------------------------------------------------------------------
extracted_intensities = []
lane_profiles = []

for lane_idx in range(n_lanes):
    lane_center_x = (lane_idx + 1) * lane_width + lane_width // 2
    col_start = lane_center_x - lane_width // 3
    col_end   = lane_center_x + lane_width // 3
    # Average across lane width to reduce noise
    lane_col  = np.mean(gel[:, col_start:col_end], axis=1)
    smoothed  = uniform_filter1d(lane_col, size=5)
    lane_profiles.append(smoothed)
    # Peak intensity in band region (rows 100 to 300)
    roi = smoothed[100:300]
    peak_intensity = np.max(roi) - background
    extracted_intensities.append(peak_intensity)

extracted_intensities = np.array(extracted_intensities)

# -----------------------------------------------------------------------
# SECTION 3: FIT EFFICIENCY CURVE AND DETERMINE OPTIMAL ANNEALING Temp
# -----------------------------------------------------------------------
p0_fit = [56.0, 5.0, max(extracted_intensities)]
bounds_fit = ([44.0, 1.0, 0.0], [66.0, 15.0, 300.0])

popt_pcr, pcov_pcr = curve_fit(
    pcr_efficiency_model,
    annealing_temps.astype(float),
    extracted_intensities,
    p0=p0_fit,
    bounds=bounds_fit,
    maxfev=5000
)
T_opt_fit, sigma_fit, A_fit = popt_pcr
T_opt_err = np.sqrt(pcov_pcr[0, 0])

T_fine = np.linspace(45, 65, 300)
efficiency_fit_curve = pcr_efficiency_model(T_fine, *popt_pcr)

# -----------------------------------------------------------------------
# SECTION 4: PLOTTING
# -----------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(17, 5))

# Panel A: Synthetic gel image
axes[0].imshow(gel, cmap='hot', aspect='auto', vmin=0, vmax=255)
axes[0].set_title('Panel A: Gradient PCR Gel (Simulated)', fontsize=11)
axes[0].set_xlabel('Gel Width (px)')
axes[0].set_ylabel('Migration Distance (px)')
tick_positions = [(i + 1) * lane_width + lane_width // 2 for i in range(n_lanes)]
axes[0].set_xticks(tick_positions)
axes[0].set_xticklabels([f'{t}°C' for t in annealing_temps], fontsize=8, rotation=45)

# Panel B: Lane intensity profiles
for i, profile in enumerate(lane_profiles):
    axes[1].plot(profile, label=f'{annealing_temps[i]}°C',
                 alpha=0.75, linewidth=1.3)
axes[1].axhline(background, color='grey', linestyle='--', linewidth=0.8,
                label='Background')
axes[1].set_xlabel('Migration Distance (px)', fontsize=11)
axes[1].set_ylabel('Mean Pixel Intensity', fontsize=11)
axes[1].set_title('Panel B: Lane Intensity Profiles', fontsize=11)
axes[1].legend(fontsize=7, ncol=2)
axes[1].grid(True, alpha=0.3)

# Panel C: Efficiency vs annealing temperature
axes[2].scatter(annealing_temps, extracted_intensities,
                color='steelblue', s=80, zorder=5,
                label='Measured Band Intensity')
axes[2].plot(T_fine, efficiency_fit_curve,
             color='tomato', linewidth=2,
             label=f'Gaussian fit\nT_opt = {T_opt_fit:.1f}±{T_opt_err:.1f} °C')
axes[2].axvline(T_opt_fit, color='tomato', linestyle=':', linewidth=1.2)
axes[2].set_xlabel('Annealing Temperature (°C)', fontsize=11)
axes[2].set_ylabel('Background-Subtracted Intensity (a.u.)', fontsize=11)
axes[2].set_title('Panel C: PCR Efficiency vs Annealing Temperature', fontsize=11)
axes[2].legend(fontsize=9)
axes[2].grid(True, alpha=0.3)

plt.suptitle('16S rRNA Gene PCR — Gradient Annealing Calibration',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('exercise2_pcr_gradient_calibration.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\n--- PCR Gradient Calibration Results ---")
print(f"Empirical optimal annealing temperature: {T_opt_fit:.1f} ± {T_opt_err:.1f} °C")
print(f"Efficiency curve half-width (σ):         {sigma_fit:.1f} °C")
print(f"Recommendation: Use {T_opt_fit:.0f}°C annealing for all subsequent 27F/1492R reactions.")
print(f"\nBand intensities by lane:")
for temp, intensity in zip(annealing_temps, extracted_intensities):
    bar = '█' * int(intensity / 8)
    print(f"  {temp}°C: {intensity:5.1f} a.u.  {bar}")
```

When you run this script against your actual gel image (replacing the simulated data block with PIL image loading as described in the comments), the optimal annealing temperature will emerge from the Gaussian fit to the intensity-versus-temperature curve. If your empirical optimum differs from the nearest-neighbor prediction by more than 4 °C, the most common causes are salt concentration differences between the prediction model (50 mM Na⁺) and your actual buffer, GC content of the ambiguity base at position 11 of the 27F primer (the M base can be either A or C, shifting $T_m$ by roughly 1.5 °C), and template secondary structure that competes with primer hybridization. Each of these factors is physically interpretable, not an experimental failure—record and report them as sources of systematic uncertainty.

### GC Content Analysis: Connecting Sequence Composition to Thermostability

Send your best PCR amplicon (highest intensity band from the optimal annealing temperature lane) for Sanger sequencing, or use a publicly available 16S sequence for E. coli MG1655 (GenBank accession NR_102804.1) if sequencing is unavailable in your setting. The following script computes GC content in sliding windows across the amplicon, computes the theoretical $T_m$ of each 20 bp window using the Wallace rule ($T_m = 2(A+T) + 4(G+C)$ °C), and identifies regions of exceptional thermostability that would resist denaturation at standard PCR conditions.

```python
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# 16S rRNA gene partial sequence, E. coli MG1655 (27F/1492R amplicon region, ~500 bp shown)
# Source: NCBI NR_102804.1, positions 28-527
sequence_raw = """
AGAGTTTGATCCTGGCTCAGATTGAACGCTGGCGGCAGGCCTAACACATGCAAGTCGAACGGTAACAGGAA
GCTTGCTTTCTTTGAAGTTAGCGGCGGACGGGTGAGTAATGTCTGGGAAACTGCCCGATGGAGGGGGATAAC
TACTGGAAACGGTAGCTAATACCGCATAACGTCGCAAGACCAAAGAGGGGGACCTTCGGGCCTCTTGCCATC
AGATGTGCCCAGATGGGATTAGCTAGTAGGTGGGGTAACGGCTCACCTAGGCGACGATCCCTAGCTGGTCTG
AGAGGATGACCAGCCACACTGGAACTGAGACACGGTCCAGACTCCTACGGGAGGCAGCAGTGGGGAATATTG
CACAATGGGCGCAAGCCTGATGCAGCCATGCCGCGTGTATGAAGAAGGCCTTCGGGTTGTAAAGTACTTTCA
GCGGGGAGGAAGGGAGTAAAGTTAATACCTTTGCTCATTGACGTTACCCGCAGAAGAAGCACCGGCTAACT
"""
sequence = ''.join(sequence_raw.split()).upper()
# Replace any U with T (in case of RNA-formatted input)
sequence = sequence.replace('U', 'T')

n = len(sequence)
window_size = 20  # bp, matches primer length for direct Tm comparison

# --- GC CONTENT IN SLIDING WINDOWS ---
positions = []
gc_fractions = []
tm_wallace = []

for i in range(n - window_size + 1):
    window = sequence[i:i + window_size]
    counts = Counter(window)
    gc = counts.get('G', 0) + counts.get('C', 0)
    at = counts.get('A', 0) + counts.get('T', 0)
    gc_frac = gc / window_size
    tm = 2 * at + 4 * gc  # Wallace rule, degrees C
    positions.append(i + window_size // 2)
    gc_fractions.append(gc_frac)
    tm_wallace.append(tm)

positions    = np.array(positions)
gc_fractions = np.array(gc_fractions)
tm_wallace   = np.array(tm_wallace)

# --- GLOBAL STATISTICS ---
total_counts = Counter(sequence)
global_gc = (total_counts['G'] + total_counts['C']) / n
global_at = (total_counts['A'] + total_counts['T']) / n
global_tm = 2 * (total_counts['A'] + total_counts['T']) + 4 * (total_counts['G'] + total_counts['C'])
global_tm_per_bp = global_tm / n  # mean Tm contribution per bp

print(f"Sequence length:          {n} bp")
print(f"Global GC content:        {global_gc*100:.1f}%")
print(f"Global AT content:        {global_at*100:.1f}%")
print(f"Global Wallace Tm (full): {global_tm:.0f} °C (not physically meaningful for full sequence)")
print(f"Mean 20-bp window Tm:     {np.mean(tm_wallace):.1f} °C")
print(f"Min 20-bp window Tm:      {np.min(tm_wallace):.1f} °C at position {positions[np.argmin(tm_wallace)]}")
print(f"Max 20-bp window Tm:      {np.max(tm_wallace):.1f} °C at position {positions[np.argmax(tm_wallace)]}")
print(f"Fraction of windows Tm > 60°C: {np.mean(tm_wallace > 60)*100:.1f}%")

# --- PLOTTING ---
fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

axes[0].fill_between(positions, gc_fractions, alpha=0.4, color='steelblue')
axes[0].plot(positions, gc_fractions, color='steelblue', linewidth=1.0)
axes[0].axhline(global_gc, color='navy', linestyle='--', linewidth=1.2,
                label=f'Global GC = {global_gc*100:.1f}%')
axes[0].axhline(0.5, color='grey', linestyle=':', linewidth=0.8, label='50% GC')
axes[0].set_ylabel('GC Fraction (20 bp window)', fontsize=11)
axes[0].set_title('16S rRNA Gene — GC Content and Thermostability Profile', fontsize=12)
axes[0].legend(fontsize=9)
axes[0].set_ylim(0, 1)
axes[0].grid(True, alpha=0.3)

axes[1].fill_between(positions, tm_wallace, alpha=0.4, color='tomato')
axes[1].plot(positions, tm_wallace, color='firebrick', linewidth=1.0)
axes[1].axhline(np.mean(tm_wallace), color='darkred', linestyle='--', linewidth=1.2,
                label=f'Mean Tm = {np.mean(tm_wallace):.1f} °C')
axes[1].axhline(60, color='darkorange', linestyle=':', linewidth=0.8,
                label='Tm = 60°C threshold')
axes[1].set_xlabel('Sequence Position (bp)', fontsize=11)
axes[1].set_ylabel('Wallace Tm, 20-bp window (°C)', fontsize=11)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('exercise2_gc_content_tm_profile.png', dpi=150, bbox_inches='tight')
plt.show()
```

The GC profile of the 16S gene is not biologically neutral. The stems of ribosomal RNA secondary structure—the conserved paired helices that give the small subunit ribosome its three-dimensional architecture—are preferentially GC-rich precisely because guanine-cytosine base pairs contribute three hydrogen bonds (versus two for adenine-thymine), and stacking interactions between consecutive GC pairs are thermodynamically more stabilizing. When you compare the GC window profile of E. coli 16S (global GC approximately 54%) against a thermophile such as T. thermophilus (global GC approximately 69%), the thermophile's profile sits uniformly higher, and the low-GC windows that appear in the E. coli sequence largely disappear. This is not coincidence: it is natural selection operating directly on thermodynamic stability.

---

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### Heat-Shock Survival Assay and LD₅₀ Determination

The third exercise is the most demanding and the most biologically revealing. You will determine the lethal dose 50 (LD₅₀) for thermal stress in E. coli, defined here as the temperature at which 50% of the population loses colony-forming ability after a 30-minute exposure. This experiment directly measures the boundary condition of cellular viability: the temperature at which cumulative macromolecular damage—protein unfolding, membrane disruption, RNA degradation—exceeds the cell's capacity for repair and adaptation.

Grow E. coli MG1655 to mid-exponential phase (OD₆₀₀ of 0.4–0.6) in LB broth at 37 °C with shaking. This growth phase is critical: stationary-phase cells have elevated stress resistance due to RpoS (σS)-mediated transcription of stress response genes, and you want the most thermally vulnerable phenotype to maximize the dynamic range of your survival curve. Aliquot 1 mL of culture into twelve 1.5 mL microcentrifuge tubes. Using a dry-block thermostat or water bath set at eleven discrete temperatures—37 °C (control), 44 °C, 46 °C, 48 °C, 50 °C, 52 °C, 54 °C, 56 °C, 58 °C, 60 °C, and 65 °C—incubate each tube for exactly 30 minutes. Use a calibrated probe thermometer to verify that each block position reaches its set temperature within ±0.3 °C before placing the tube. After 30 minutes, transfer each tube immediately to ice for 5 minutes to halt thermal damage.

Serial dilution and plating follows. From each heat-shocked tube, prepare serial dilutions: transfer 100 µL into 900 µL of sterile PBS (1:10 dilution), mix by vortex for 5 seconds, then repeat to achieve dilutions of 10⁻¹, 10⁻², 10⁻³, 10⁻⁴, and 10⁻⁵. Plate 100 µL of each dilution on LB agar in duplicate. Incubate plates at 37 °C for 16–18 hours, then count colonies (targeting plates with 30–300 colonies for valid counting). Calculate colony-forming units per milliliter (CFU mL⁻¹) as: CFU mL⁻¹ = (colony count) ÷ (dilution factor × volume plated in mL). The survival fraction at each temperature is then CFU mL⁻¹(treatment) ÷ CFU mL⁻¹(37 °C control).

The following Python analysis script fits a four-parameter logistic (4PL) sigmoidal model to the survival fraction data, determines LD₅₀ with confidence intervals using bootstrap resampling, and propagates counting uncertainty through the full calculation.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm

np.random.seed(2025)

# -----------------------------------------------------------------------
# DATA ENTRY: Replace with your actual CFU counts
# Format: [temperature_C, CFU_replicate1, CFU_replicate2]
# CFU values are already calculated as CFU/mL
# -----------------------------------------------------------------------
raw_cfu_data = {
    'temperature': [37, 44, 46, 48, 50, 52, 54, 56, 58, 60, 65],
    'cfu_rep1':    [2.8e8, 2.6e8, 2.3e8, 1.9e8, 1.2e8, 5.4e7,
                    8.1e6,  3.2e5,  1.1e4,  3.0e2,  0.0],
    'cfu_rep2':    [3.1e8, 2.5e8, 2.1e8, 1.7e8, 1.1e8, 6.0e7,
                    9.4e6,  2.8e5,  9.0e3,  1.5e2,  0.0],
}
df = pd.DataFrame(raw_cfu_data)

# --- SURVIVAL FRACTION AND UNCERTAINTY ---
control_mean = np.mean([df['cfu_rep1'][0], df['cfu_rep2'][0]])

df['cfu_mean'] = (df['cfu_rep1'] + df['cfu_rep2']) / 2.0
df['cfu_sem']  = np.abs(df['cfu_rep1'] - df['cfu_rep2']) / (2.0 * np.sqrt(2))

df['survival'] = df['cfu_mean'] / control_mean
df['survival_sem'] = df['cfu_sem'] / control_mean

# Replace zero CFU (complete killing) with detection limit for plotting
detection_limit = 1.0 / (1e5 * 0.1)   # 1 colony at max dilution (10^5) in 0.1 mL plate
df['survival_plot'] = df['survival'].replace(0.0, detection_limit / control_mean)

temps     = df['temperature'].values.astype(float)
survival  = df['survival_plot'].values
surv_sem  = df['survival_sem'].values
surv_sem  = np.where(surv_sem == 0, 0.01 * survival, surv_sem)  # floor SEM

# --- FOUR-PARAMETER LOGISTIC (4PL) MODEL ---
# S(T) = bottom + (top - bottom) / (1 + (T / LD50)^hill_slope)
# For survival data: top ~1 (at control temp), bottom ~0 (complete killing)
def four_pl(T, bottom, top, ld50, hill):
    return bottom + (top - bottom) / (1.0 + (T / ld50) ** hill)

p0_4pl    = [0.001, 1.0, 54.0, -10.0]
bounds_4pl = ([-0.01, 0.5, 44.0, -50.0],
              [0.1,   1.5, 65.0,  -1.0])

popt_4pl, pcov_4pl = curve_fit(
    four_pl, temps, survival,
    p0=p0_4pl, bounds=bounds_4pl, maxfev=20000,
    sigma=surv_sem, absolute_sigma=True
)
bottom_fit, top_fit, ld50_fit, hill_fit = popt_4pl
ld50_err = np.sqrt(pcov_4pl[2, 2])

# --- BOOTSTRAP CONFIDENCE INTERVAL ON LD50 ---
n_boot = 5000
ld50_boot = []
for _ in range(n_boot):
    boot_indices = np.random.choice(len(temps), size=len(temps), replace=True)
    t_boot = temps[boot_indices]
    s_boot = survival[boot_indices]
    se_boot = surv_sem[boot_indices]
    try:
        popt_b, _ = curve_fit(
            four_pl, t_boot, s_boot,
            p0=popt_4pl, bounds=bounds_4pl, maxfev=5000,
            sigma=se_boot, absolute_sigma=True
        )
        ld50_boot.append(popt_b[2])
    except RuntimeError:
        continue

ld50_boot = np.array(ld50_boot)
ld50_ci_low  = np.percentile(ld50_boot, 2.5)
ld50_ci_high = np.percentile(ld50_boot, 97.5)

# --- UNCERTAINTY PROPAGATION: CFU COUNTING ERROR ---
# Poisson uncertainty on colony counts: sigma_colony = sqrt(N_colonies)
# For a plate with N colonies, relative uncertainty = 1/sqrt(N)
# We report at which temperature this exceeds 20% (unreliable counting threshold)
print("\n--- Counting Uncertainty Analysis ---")
print(f"{'Temp (°C)':<12} {'CFU/mL (mean)':<18} {'SEM':<15} {'Rel. Uncert.':<15}")
print("-" * 60)
for _, row in df.iterrows():
    if row['cfu_mean'] > 0:
        rel_unc = row['cfu_sem'] / row['cfu_mean'] * 100 if row['cfu_mean'] > 0 else np.nan
        flag = "  <-- HIGH UNCERTAINTY" if rel_unc > 20 else ""
        print(f"{row['temperature']:<12.0f} {row['cfu_mean']:<18.2e} "
              f"{row['cfu_sem']:<15.2e} {rel_unc:<12.1f}%{flag}")
    else:
        print(f"{row['temperature']:<12.0f} {'0 (detection limit)':<18} {'N/A':<15} {'N/A':<15}")

# --- PLOTTING ---
T_fine = np.linspace(35, 68, 400)
survival_curve = four_pl(T_fine, *popt_4pl)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: Survival curve, linear scale
axes[0].errorbar(temps, survival, yerr=surv_sem,
                 fmt='o', color='steelblue', markersize=7,
                 capsize=4, label='Measured survival fraction', zorder=5)
axes[0].plot(T_fine, survival_curve,
             color='tomato', linewidth=2.0,
             label=f'4PL fit: LD₅₀ = {ld50_fit:.1f}°C')
axes[0].axvline(ld50_fit, color='tomato', linestyle='--', linewidth=1.2)
axes[0].axhline(0.5, color='grey', linestyle=':', linewidth=0.8, label='50% survival')
axes[0].fill_betweenx(
    [0, 1.1], ld50_ci_low, ld50_ci_high,
    alpha=0.15, color='tomato',
    label=f'95% CI: [{ld50_ci_low:.1f}, {ld50_ci_high:.1f}]°C'
)
axes[0].set_xlabel('Temperature (°C)', fontsize=11)
axes[0].set_ylabel('Survival Fraction (relative to 37°C control)', fontsize=11)
axes[0].set_title('E. coli Thermal LD₅₀ — Survival Curve (Linear)', fontsize=12)
axes[0].legend(fontsize=9)
axes[0].set_ylim(-0.05, 1.15)
axes[0].grid(True, alpha=0.3)

# Panel B: Log-scale survival
log_survival = np.log10(np.maximum(survival, 1e-9))
log_curve    = np.log10(np.maximum(survival_curve, 1e-9))
axes[1].scatter(temps, log_survival, color='steelblue', s=60, zorder=5,
                label='Measured (log scale)')
axes[1].plot(T_fine, log_curve, color='tomato', linewidth=2.0,
             label=f'4PL fit')
axes[1].axvline(ld50_fit, color='tomato', linestyle='--', linewidth=1.2,
                label=f'LD₅₀ = {ld50_fit:.1f}°C')
axes[1].axhline(np.log10(0.5), color='grey', linestyle=':', linewidth=0.8)
axes[1].set_xlabel('Temperature (°C)', fontsize=11)
axes[1].set_ylabel('log₁₀(Survival Fraction)', fontsize=11)
axes[1].set_title('E. coli Thermal LD₅₀ — Survival Curve (Log Scale)', fontsize=12)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)
# Custom y-axis labels for log scale
yticks_log = [-8, -6, -4, -2, 0]
axes[1].set_yticks(yticks_log)
axes[1].set_yticklabels([f'10^{y}' for y in yticks_log])

plt.tight_layout()
plt.savefig('exercise3_ld50_survival_curve.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\n--- LD50 Determination Results ---")
print(f"4PL model LD50:        {ld50_fit:.2f} °C")
print(f"Standard error (fit):  ±{ld50_err:.2f} °C")
print(f"Bootstrap 95% CI:      [{ld50_ci_low:.2f}, {ld50_ci_high:.2f}] °C")
print(f"Hill coefficient:      {hill_fit:.2f}  (steepness of transition)")
print(f"Fitted bottom:         {bottom_fit:.4f} (residual survival floor)")
print(f"Fitted top:            {top_fit:.4f}  (maximum survival = control)")
```

The Hill coefficient returned by this fit deserves careful interpretation. A steep Hill coefficient (absolute value greater than 10) indicates cooperative collapse: the survival fraction drops from 90% to 10% over a temperature range of only a few degrees. This cooperativity reflects the thermodynamic reality of protein denaturation. Proteins do not unfold residue by residue; they undergo collective unfolding transitions in which the loss of a few key stabilizing contacts triggers a cascade of secondary structure collapse, similar in mathematical form to a phase transition. When this cooperativity is observed empirically in your survival data, you are measuring the macroscopic consequence of microscopic thermodynamic cooperativity operating simultaneously across tens of thousands of protein molecules in each cell.

### Uncertainty Propagation: Error Budgets for Biological Measurements

Every quantitative result in a biological experiment carries uncertainty from multiple independent sources, and understanding how these uncertainties combine is as important as the measurement itself. The following script builds an explicit error budget for the LD₅₀ determination, decomposing total uncertainty into contributions from temperature control accuracy, colony counting Poisson noise, dilution pipetting error, and biological replicate variability.

```python
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------
# ERROR BUDGET ANALYSIS FOR LD50 DETERMINATION
# This script propagates four independent uncertainty sources through
# the full measurement chain and shows their fractional contribution.
# -----------------------------------------------------------------------

# --- SOURCE 1: TEMPERATURE CONTROL UNCERTAINTY ---
# Your thermostat has ±0.5°C accuracy; at the LD50 slope, this translates
# to a CFU uncertainty via the slope of the survival curve at LD50.
# From the 4PL fit: dS/dT at LD50 ≈ hill * (top-bottom) / (4 * LD50)
# (derivative of 4PL at the inflection point, simplified)

ld50_nominal   = 54.0   # degrees C (from fit)
hill           = -10.0  # from fit
top            = 1.0
bottom         = 0.001

dS_dT_at_ld50 = abs(hill) * (top - bottom) / (4.0 * ld50_nominal)  # per degree C
temp_uncertainty_C = 0.5    # thermostat accuracy
sigma_survival_from_temp = dS_dT_at_ld50 * temp_uncertainty_C

# --- SOURCE 2: COLONY COUNTING POISSON NOISE ---
# A plate with N colonies has counting uncertainty sigma_N = sqrt(N).
# For a "good" plate with N=200 colonies, relative uncertainty = 1/sqrt(200).
N_colonies_typical = 200
sigma_colonies_poisson = np.sqrt(N_colonies_typical)
rel_uncertainty_counting = sigma_colonies_poisson / N_colonies_typical

# Propagate to survival fraction: S = CFU(treatment) / CFU(control)
# Both numerator and denominator carry Poisson errors.
# If N_t = treated count, N_c = control count:
# sigma_S/S = sqrt(1/N_t + 1/N_c)
N_treated  = 50    # typical colony count on treated plates near LD50
N_control  = 300   # typical colony count on control plates
rel_sigma_survival_counting = np.sqrt(1.0/N_treated + 1.0/N_control)

# Convert to absolute survival uncertainty at S=0.5
S_at_ld50 = 0.5
sigma_survival_from_counting = rel_sigma_survival_counting * S_at_ld50

# --- SOURCE 3: PIPETTING VOLUME ERROR ---
# A calibrated P1000 pipette has ±1% systematic error at 1 mL,
# and ±2% at 100 µL (P200 range). Serial dilutions compound this.
# For a 10^-4 dilution (four 1:10 steps), error compounds as:
# sigma_dilution/dilution = n_steps * sigma_single/step
n_dilution_steps   = 4
sigma_per_step_rel = 0.02   # 2% per pipetting step
sigma_dilution_rel = n_dilution_steps * sigma_per_step_rel  # 8% total
sigma_survival_from_pipetting = sigma_dilution_rel * S_at_ld50

# --- SOURCE 4: BIOLOGICAL REPLICATE VARIABILITY ---
# Two biological replicates; estimate from inter-replicate CVs across the dataset.
# Typical inter-replicate CV for colony counts: 10–15%.
cv_biological = 0.12  # 12% coefficient of variation between replicates
sigma_survival_from_biology = cv_biological * S_at_ld50

# --- COMBINE IN QUADRATURE (all sources assumed independent) ---
sigma_sources = np.array([
    sigma_survival_from_temp,
    sigma_survival_from_counting,
    sigma_survival_from_pipetting,
    sigma_survival_from_biology
])

sigma_total_survival = np.sqrt(np.sum(sigma_sources**2))

# Propagate survival uncertainty to LD50 uncertainty via inverse 4PL:
# sigma_LD50 = sigma_S / |dS/dT|_at_LD50
sigma_ld50_total = sigma_total_survival / dS_dT_at_ld50

# --- FRACTIONAL CONTRIBUTIONS TO TOTAL VARIANCE ---
variances = sigma_sources**2
var_total = np.sum(variances)
fractional_contributions = variances / var_total * 100

source_names = [
    'Temperature control\n(±0.5°C thermostat)',
    'Colony counting\n(Poisson, N≈50)',
    'Pipetting volume\n(4-step dilution, ±2%/step)',
    'Biological replicates\n(inter-replicate CV 12%)'
]

print("=" * 65)
print("   COMPLETE UNCERTAINTY BUDGET — LD50 THERMAL ASSAY")
print("=" * 65)
print(f"\n{'Source':<42} {'σ(S)':<12} {'% of Var':<10}")
print("-" * 65)
for name, sig, frac in zip(source_names, sigma_sources, fractional_contributions):
    name_oneline = name.replace('\n', ' ')
    print(f"{name_oneline:<42} {sig:<12.4f} {frac:<10.1f}%")
print("-" * 65)
print(f"{'TOTAL (quadrature sum)':<42} {sigma_total_survival:<12.4f} {'100.0':<10}%")
print(f"\nLD50 total uncertainty:  ±{sigma_ld50_total:.2f} °C")
print(f"Relative uncertainty:    {sigma_ld50_total/ld50_nominal*100:.1f}%")
print(f"\nReported result:  LD50 = {ld50_nominal:.1f} ± {sigma_ld50_total:.1f} °C  (1σ combined)")

# --- PIE CHART OF VARIANCE CONTRIBUTIONS ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

colors_pie = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
wedge_props = {'linewidth': 1.5, 'edgecolor': 'white'}
axes[0].pie(
    fractional_contributions,
    labels=source_names,
    colors=colors_pie,
    autopct='%1.1f%%',
    startangle=140,
    wedgeprops=wedge_props,
    textprops={'fontsize': 9}
)
axes[0].set_title('Variance Budget: LD₅₀ Measurement\n(Fractional Contribution to Total σ²)',
                  fontsize=11)

# --- BAR CHART: ABSOLUTE SIGMA CONTRIBUTIONS ---
bar_colors = colors_pie
short_names = ['Temp\ncontrol', 'Colony\ncounting', 'Pipetting\nerror', 'Biological\nreplicates']
bars = axes[1].bar(short_names, sigma_sources, color=bar_colors,
                   edgecolor='white', linewidth=1.5)
axes[1].axhline(sigma_total_survival, color='black', linestyle='--', linewidth=1.5,
                label=f'σ_total = {sigma_total_survival:.4f}')
axes[1].set_ylabel('Absolute Uncertainty in Survival Fraction σ(S)', fontsize=10)
axes[1].set_title('Absolute Uncertainty Contributions\n(Survival Fraction at LD₅₀)',
                  fontsize=11)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3, axis='y')

for bar, sig in zip(bars, sigma_sources):
    axes[1].text(bar.get_x() + bar.get_width() / 2.0,
                 bar.get_height() + 0.001,
                 f'{sig:.4f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('exercise3_uncertainty_budget.png', dpi=150, bbox_inches='tight')
plt.show()
```

The error budget analysis will almost always reveal that biological replicate variability and colony counting noise near the LD₅₀ dominate the total uncertainty budget, while temperature control contributes less than expected. This is a consistent finding in thermal stress biology: the cells themselves exhibit stochastic variation in thermotolerance—arising from cell-cycle position, local metabolite concentrations, and random fluctuations in chaperone gene expression—that exceeds the precision limits of the instrument measuring the perturbation. This irreducible biological stochasticity is not an experimental flaw; it is a real property of the system under study. Reporting the full error budget rather than only the fit uncertainty gives readers the information they need to judge whether a claimed LD₅₀ shift of 1–2 °C between two strains is a genuine biological signal or noise within the measurement floor.

---

## Laboratory Cheat Sheet & Metric Verification Guide

### Quick Reference: Critical Parameters, Expected Values, and Diagnostic Checks

This section is a condensed operational reference. Use it at the bench for rapid sanity-checking and before any analytical step where a miscalibrated instrument or misprepared reagent could compromise an entire experimental series.

**Growth Rate Reference Values for E. coli MG1655 in LB at 200 rpm**

| Temperature (°C) | Expected μ (h⁻¹) | Expected Doubling Time | Classification |
|:---:|:---:|:---:|:---|
| 20 | 0.08–0.14 | 300–520 min | Cold stress, reduced |
| 30 | 0.45–0.60 | 69–92 min | Sub-optimal |
| 37 | 0.85–1.10 | 38–49 min | Optimal |
| 42 | 0.55–0.75 | 55–75 min | Heat stress response active |
| 45 | 0.10–0.25 | 165–415 min | Severe stress |
| 48 | 0.00–0.05 | >825 min | Near-lethal, variable |

**DNA Quality Thresholds (Nanodrop / UV Spectrophotometer)**

| Metric | Acceptable Range | Action if Outside Range |
|:---|:---:|:---|
| A260/A280 ratio | 1.78–2.00 | < 1.7: re-extract with proteinase K; > 2.1: treat with RNase A |
| A260/A230 ratio | 1.80–2.20 | < 1.6: phenol/ethanol carryover; re-precipitate with 70% ethanol wash |
| Concentration | ≥ 10 ng µL⁻¹ for PCR | Concentrate by SpeedVac or ethanol precipitation |

**PCR Troubleshooting Matrix**

| Observation | Most Probable Cause | Corrective Action |
|:---|:---|:---|
| No band at any annealing temperature | Template quality failure | Verify A260/A280; re-extract DNA |
| Smear instead of discrete band | Non-specific priming; annealing too low | Increase annealing temp by 2°C increments |
| Band at wrong size | Primer-dimer artifact | Add 1M betaine at 1× final; redesign primers |
| Band present in no-template control | Contamination | Replace all reagents; decontaminate bench with 10% bleach |
| Faint band only at optimal temp | Insufficient template | Increase template to 25–50 ng per reaction |

**Spectrophotometer Calibration Checks (Before Each Use)**

Blank the instrument with the identical buffer used to dilute your samples—never with water when measuring LB-grown cells diluted in LB, as the LB broth itself absorbs at 280 nm and will cause systematic underestimation. Run a standard absorbance check using a certified neutral density filter (OD = 1.000 ± 0.005 at 600 nm) before each experimental session. Verify linearity by measuring a twofold dilution series of a mid-exponential culture; the OD₆₀₀ values should track the dilution factor to within 3% across the range 0.05–0.80. Any deviation beyond 5% from perfect linearity in this range indicates a fouled cuvette, lamp degradation, or detector nonlinearity, and all data collected on that instrument session must be flagged.

**Survival Assay Checklist (Pre-Experiment)**

Before initiating the heat-shock exposure tubes, verify each of the following in order. First, confirm that all water bath positions have reached their set temperatures and have been stable for at least 15 minutes (measured with an independent probe thermometer, not the thermostat readout). Second, confirm that your LB agar plates were poured within the previous 48 hours and stored at 4 °C; plates older than 72 hours develop surface condensation and satellite colony artifacts that distort counts. Third, confirm that your mid-exponential culture is at OD₆₀₀ between 0.40 and 0.60 by taking a spectrophotometer reading immediately before distributing aliquots into stress tubes. Fourth, confirm that your 10-fold serial dilutions are prepared in sterile PBS (not LB), because LB's nutrient content allows residual growth during the plating workflow and inflates viable counts. Fifth, pre-label all plates with temperature, dilution factor, replicate number, and time before beginning the dilution series—no post-hoc labeling, as plates become indistinguishable once incubated.

**Python Environment Verification Commands**

Run these in sequence at the start of any computational analysis session:

```bash
python -c "import numpy as np; a = np.array([1.0,2.0,3.0]); print('NumPy OK:', a.mean())"
python -c "from scipy.optimize import curve_fit; print('SciPy curve_fit: OK')"
python -c "from scipy.stats import norm; print('SciPy stats: OK')"
python -c "import matplotlib.pyplot as plt; plt.figure(); plt.close(); print('Matplotlib: OK')"
python -c "import pandas as pd; df=pd.DataFrame({'a':[1,2,3]}); print('Pandas OK:', df['a'].sum())"
```

Each line should print without error or traceback. If `scipy.optimize.curve_fit` fails to import, your SciPy installation is incomplete or below version 1.7; reinstall with `pip install --upgrade scipy`. If Matplotlib raises a backend error in a headless server environment, prepend `import matplotlib; matplotlib.use('Agg')` before any `import matplotlib.pyplot` call and save figures to file rather than displaying interactively.

**Key Equations Summary**

The specific growth rate from logistic curve fitting: $\mu = \ln(2) / t_d$, where $t_d$ is the doubling time extracted from the logistic fit parameter.

The Beer-Lambert law corrected for dilution: $[\text{cells}] \propto A_{600} \times D$, where $D$ is the dilution factor applied before reading, valid only for $A_{600} \leq 0.80$ in a 1 cm path-length cuvette.

The Wallace rule for oligonucleotide melting temperature: $T_m = 2(n_A + n_T) + 4(n_G + n_C)$, where $n$ denotes the count of each base in the duplex, valid for sequences of 14–20 bp in 50 mM monovalent salt.

Uncertainty propagation for a ratio $f = A/B$: $\sigma_f / f = \sqrt{(\sigma_A/A)^2 + (\sigma_B/B)^2}$, used for survival fraction calculations where both numerator (treated CFU) and denominator (control CFU) carry independent counting uncertainties.

Combined uncertainty from $k$ independent sources: $\sigma_{\text{total}} = \sqrt{\sum_{i=1}^{k} \sigma_i^2}$, the standard quadrature combination valid when all sources are uncorrelated, which holds for the four sources identified in Exercise 3 (temperature, counting, pipetting, and biological variation)....
