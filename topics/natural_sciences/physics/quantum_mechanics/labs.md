# Operational Verification Labs: Quantum Mechanics

## Objective & Laboratory Bench Setup

Quantum mechanics governs the behavior of matter and energy at atomic and subatomic scales, where classical intuition fails and discrete energy states, wave-particle duality, and probabilistic measurement outcomes dominate physical reality. These laboratory exercises ground quantum theory in reproducible empirical measurement, using photoelectric effect apparatus, spectroscopy instruments, and computational wavefunction modeling to verify the quantized nature of light and matter. The experimental physicist's task is to measure Planck's constant through photocurrent threshold voltage analysis, map hydrogen atomic emission spectra to derive the Rydberg constant, simulate quantum tunneling probability distributions through finite potential barriers, and quantify measurement uncertainty inherent in Heisenberg's indeterminacy principle. Each exercise balances direct physical observation with rigorous error propagation analysis, teaching the experimentalist to extract fundamental constants from noisy data and validate theoretical predictions against laboratory reality.

The laboratory bench requires a mercury vapor lamp with calibrated interference filters spanning 365 nm to 578 nm wavelengths, a vacuum phototube apparatus with variable retarding potential supply (0–3 V range, 10 mV resolution), a precision digital multimeter for photocurrent measurement (nanoampere sensitivity), and a USB-connected Ocean Optics spectrometer (200–1100 nm range, 0.5 nm resolution) with fiber optic probe and hydrogen discharge tube. Computational analysis demands a Python 3.10+ environment with NumPy 1.24+, SciPy 1.10+, and Matplotlib 3.7+ installed for numerical wavefunction integration, least-squares parameter fitting, and scientific visualization. The data acquisition pipeline uses PySerial for instrument communication and Pandas for tabular spectroscopic data manipulation. Calibration standards include a NIST-traceable mercury emission lamp (546.074 nm primary reference line) and certified neutral density filters with optical density 0.3, 0.6, and 1.0 at 546 nm. Temperature-stabilized enclosures maintain the photoelectric cell at 23.0 ± 0.5°C to minimize thermionic emission noise, while the spectrometer requires a 30-minute thermal equilibration period before wavelength calibration. Verify instrument readiness by checking spectrometer resolution with the mercury doublet at 576.960 nm and 579.065 nm—if both peaks resolve with baseline separation, the optical system meets specification for hydrogen line analysis.

Establish the Python scientific stack by creating a dedicated virtual environment and installing required packages with exact version pinning to ensure reproducible numerical results. Execute the following terminal commands to configure the computational laboratory environment:

```bash
python3 -m venv quantum_lab_env
source quantum_lab_env/bin/activate
pip install numpy==1.24.3 scipy==1.10.1 matplotlib==3.7.1 pandas==2.0.2 pyserial==3.5
python -c 'import numpy as np; import scipy; import matplotlib; print(f"NumPy {np.__version__}, SciPy {scipy.__version__}, Matplotlib {matplotlib.__version__}")'
```

The verification command should return `NumPy 1.24.3, SciPy 1.10.1, Matplotlib 3.7.1` confirming the environment is operational. Create a working directory structure `quantum_labs/` with subdirectories `data/`, `plots/`, and `analysis/` to organize raw spectroscopic measurements, generated figures, and fitted parameter results respectively.

## Exercise 1: Empirical Observation & Measurement Protocol

The photoelectric effect provides direct experimental evidence for light quantization, demonstrating that electromagnetic radiation delivers energy in discrete packets (photons) rather than continuous waves as classical electromagnetism predicts. When monochromatic light illuminates a metal cathode surface, electrons absorb individual photons and escape if the photon energy $E = h\nu$ exceeds the material work function $\phi$. Einstein's photoelectric equation $eV_{\text{stop}} = h\nu - \phi$ relates the stopping potential $V_{\text{stop}}$ (the reverse voltage that nullifies photocurrent) to incident light frequency $\nu$, yielding a linear relationship whose slope directly measures Planck's constant $h = 6.62607015 \times 10^{-34}$ J·s. This exercise constructs that linear calibration curve through systematic measurement of stopping potential across five discrete wavelengths, extracting both Planck's constant and cathode work function from weighted least-squares regression with propagated instrumental uncertainties.

Begin apparatus preparation by mounting the vacuum phototube in a light-tight enclosure with the mercury lamp positioned 15 cm from the cathode window, ensuring the optical axis passes through the center of the photosensitive surface. Install the 365 nm interference filter (10 nm FWHM bandwidth) in the collimated beam path and verify optical alignment by maximizing photocurrent signal with zero retarding potential applied. Connect the phototube anode to the positive terminal of the retarding potential supply through a precision 100 kΩ current-sensing resistor, and monitor voltage drop across this resistor with the digital multimeter in millivolt mode to measure photocurrent indirectly via Ohm's law $I = V_{\text{sense}}/R$. Set the lamp intensity to produce approximately 50 nA photocurrent at zero bias—this ensures adequate signal-to-noise ratio while avoiding space-charge saturation effects that distort the stopping potential measurement.

The stopping potential measurement protocol requires incrementing the retarding voltage in 50 mV steps from 0 V to 3 V while recording photocurrent at each bias point until current drops below 1 nA noise floor. For the 365 nm ultraviolet filter, sweep the retarding potential and log the data stream using this Python acquisition script that interfaces with a Keithley 2400 SourceMeter via GPIB:

```python
import numpy as np
import pandas as pd
import serial
import time

def measure_stopping_potential(wavelength_nm, output_file):
    """
    Measure photocurrent vs retarding potential for photoelectric effect analysis.
    
    Args:
        wavelength_nm: Illumination wavelength in nanometers
        output_file: CSV file path for saving measurement data
    """
    # Instrument parameters
    voltage_start = 0.0  # V
    voltage_stop = 3.0   # V
    voltage_step = 0.05  # V
    resistance = 1e5     # 100 kΩ current sense resistor
    
    # Generate voltage sweep array
    voltages = np.arange(voltage_start, voltage_stop + voltage_step, voltage_step)
    currents = []
    
    print(f"Measuring photoelectric effect at λ = {wavelength_nm} nm")
    print(f"Voltage range: {voltage_start} V to {voltage_stop} V, step {voltage_step} V")
    
    # Simulated data acquisition loop (replace with actual instrument communication)
    # In production: use pyvisa or pyserial to communicate with SourceMeter
    for v in voltages:
        # Apply retarding potential (instrument command would go here)
        # Example: sourcemeter.write(f":SOUR:VOLT {v}")
        
        time.sleep(0.2)  # Allow settling time
        
        # Read sense voltage across current resistor
        # Example: v_sense = float(sourcemeter.query(":MEAS:VOLT?"))
        # For demonstration, model realistic photoelectric response
        
        # Einstein photoelectric equation parameters (sodium cathode)
        h = 6.62607015e-34  # J·s
        c = 299792458       # m/s
        e = 1.602176634e-19 # C
        phi = 2.28 * e      # Work function sodium: 2.28 eV
        
        photon_energy = h * c / (wavelength_nm * 1e-9)
        v_stop_theoretical = (photon_energy - phi) / e
        
        # Model photocurrent with realistic noise
        if v < v_stop_theoretical:
            i_photo = 5e-8 * (1 - v / v_stop_theoretical) + np.random.normal(0, 1e-9)
        else:
            i_photo = np.random.normal(0, 5e-10)  # Dark current noise
        
        currents.append(max(i_photo, 0))  # Physical current cannot be negative
        
        print(f"V = {v:.3f} V, I = {currents[-1]*1e9:.2f} nA")
    
    # Save measurement data
    df = pd.DataFrame({
        'retarding_potential_V': voltages,
        'photocurrent_A': currents,
        'wavelength_nm': wavelength_nm
    })
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}\n")
    
    return voltages, currents

# Execute measurement for 365 nm UV wavelength
wavelengths = [365, 405, 436, 546, 578]  # nm (mercury emission lines)
datasets = {}

for wl in wavelengths:
    output_path = f"data/photoelectric_{wl}nm.csv"
    v_data, i_data = measure_stopping_potential(wl, output_path)
    datasets[wl] = (v_data, i_data)
```

Execute this script for each of the five mercury wavelengths (365, 405, 436, 546, 578 nm), ensuring complete thermal re-equilibration between filter changes to prevent temperature-dependent work function drift. The stopping potential is operationally defined as the retarding voltage where photocurrent falls to 10% of its zero-bias value—this threshold criterion provides better statistical stability than attempting to extrapolate to zero current through noisy baseline data. Extract stopping potentials from each dataset using a hyperbolic tangent fitting function that models the smooth photocurrent turnoff:

```python
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def fit_stopping_potential(voltage_data, current_data):
    """
    Extract stopping potential from photocurrent vs voltage curve.
    
    Uses tanh transition model: I(V) = I0 * [1 - tanh((V - V_stop)/w)] / 2
    where V_stop is stopping potential and w is transition width.
    """
    def photoelectric_model(v, i0, v_stop, width):
        return i0 * (1 - np.tanh((v - v_stop) / width)) / 2
    
    # Initial parameter guesses
    i_max = np.max(current_data)
    v_half = voltage_data[np.argmin(np.abs(current_data - i_max/2))]
    p0 = [i_max, v_half, 0.2]
    
    # Fit model to data
    popt, pcov = curve_fit(photoelectric_model, voltage_data, current_data, p0=p0)
    perr = np.sqrt(np.diag(pcov))
    
    return popt[1], perr[1], popt, photoelectric_model

# Analyze all wavelength datasets
stopping_potentials = []
stopping_uncertainties = []
frequencies = []

c = 299792458  # m/s

for wl in wavelengths:
    df = pd.read_csv(f"data/photoelectric_{wl}nm.csv")
    v_data = df['retarding_potential_V'].values
    i_data = df['photocurrent_A'].values
    
    v_stop, v_stop_err, fit_params, model_func = fit_stopping_potential(v_data, i_data)
    
    stopping_potentials.append(v_stop)
    stopping_uncertainties.append(v_stop_err)
    frequencies.append(c / (wl * 1e-9))  # Convert wavelength to frequency
    
    print(f"λ = {wl} nm: V_stop = {v_stop:.4f} ± {v_stop_err:.4f} V")
    
    # Plot individual measurement with fit
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(v_data, i_data * 1e9, yerr=0.5, fmt='o', label='Measured data', 
                markersize=4, capsize=3)
    
    v_fit = np.linspace(v_data[0], v_data[-1], 200)
    i_fit = model_func(v_fit, *fit_params) * 1e9
    ax.plot(v_fit, i_fit, 'r-', label=f'Fit: $V_{{stop}}$ = {v_stop:.3f} V', linewidth=2)
    
    ax.axvline(v_stop, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Retarding Potential (V)', fontsize=12)
    ax.set_ylabel('Photocurrent (nA)', fontsize=12)
    ax.set_title(f'Photoelectric Effect: λ = {wl} nm', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"plots/photoelectric_fit_{wl}nm.png", dpi=300)
    plt.close()

# Convert to numpy arrays for regression
frequencies = np.array(frequencies)
stopping_potentials = np.array(stopping_potentials)
stopping_uncertainties = np.array(stopping_uncertainties)
```

The extracted stopping potentials now serve as dependent variables for the Einstein photoelectric equation regression. Plot $eV_{\text{stop}}$ versus photon frequency $\nu = c/\lambda$ and perform weighted linear least-squares fitting to extract Planck's constant from the slope and work function from the y-intercept. The weighting factors $w_i = 1/\sigma_i^2$ account for heteroscedastic measurement uncertainties, ensuring that precise data points influence the fit more strongly than noisy outliers:

```python
from scipy.stats import linregress

# Convert stopping potentials to energy (eV)
e = 1.602176634e-19  # Elementary charge (C)
stopping_energies = stopping_potentials * e  # Convert V to J
stopping_energy_uncertainties = stopping_uncertainties * e

# Weighted linear regression: E = h*nu - phi
weights = 1 / stopping_energy_uncertainties**2
mean_freq = np.average(frequencies, weights=weights)
mean_energy = np.average(stopping_energies, weights=weights)

numerator = np.sum(weights * (frequencies - mean_freq) * (stopping_energies - mean_energy))
denominator = np.sum(weights * (frequencies - mean_freq)**2)

h_measured = numerator / denominator
phi_measured = mean_energy - h_measured * mean_freq

# Calculate uncertainties via weighted covariance
residuals = stopping_energies - (h_measured * frequencies + phi_measured)
chi_squared = np.sum(weights * residuals**2)
dof = len(frequencies) - 2
reduced_chi_squared = chi_squared / dof

h_uncertainty = np.sqrt(reduced_chi_squared / denominator)
phi_uncertainty = h_uncertainty * np.sqrt(np.sum(weights * frequencies**2) / np.sum(weights))

# Report results
h_literature = 6.62607015e-34  # J·s
relative_error = abs(h_measured - h_literature) / h_literature * 100

print("\n=== PLANCK CONSTANT MEASUREMENT RESULTS ===")
print(f"Measured h = ({h_measured:.4e} ± {h_uncertainty:.4e}) J·s")
print(f"Literature h = {h_literature:.4e} J·s")
print(f"Relative error = {relative_error:.2f}%")
print(f"Work function φ = ({phi_measured/e:.3f} ± {phi_uncertainty/e:.3f}) eV")
print(f"Reduced χ² = {reduced_chi_squared:.3f}")

# Generate publication-quality plot
fig, ax = plt.subplots(figsize=(10, 6))

ax.errorbar(frequencies / 1e14, stopping_energies / e, 
            yerr=stopping_energy_uncertainties / e,
            fmt='o', markersize=8, capsize=4, capthick=2,
            label='Experimental data', color='navy')

freq_fit = np.linspace(frequencies.min(), frequencies.max(), 100)
energy_fit = (h_measured * freq_fit + phi_measured) / e

ax.plot(freq_fit / 1e14, energy_fit, 'r-', linewidth=2.5,
        label=f'Linear fit: $h$ = {h_measured:.3e} J·s')

ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
ax.axhline(-phi_measured/e, color='gray', linewidth=1, linestyle='--', 
           label=f'Work function: φ = {phi_measured/e:.2f} eV')

ax.set_xlabel('Frequency (10¹⁴ Hz)', fontsize=14, fontweight='bold')
ax.set_ylabel('Stopping Potential Energy (eV)', fontsize=14, fontweight='bold')
ax.set_title('Einstein Photoelectric Equation: Planck Constant Determination', 
             fontsize=16, fontweight='bold')
ax.legend(fontsize=11, loc='upper left')
ax.grid(True, alpha=0.3, linestyle=':')
ax.tick_params(labelsize=11)

plt.tight_layout()
plt.savefig('plots/planck_constant_measurement.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\nPlots saved to plots/ directory")
```

This analysis pipeline yields Planck's constant with typical experimental precision of 3–5% when executed with careful optical alignment and thermal management. The dominant systematic error sources include cathode surface contamination (which increases work function), stray light leakage into the phototube enclosure (which produces a DC offset in stopping potential), and wavelength calibration drift in the interference filters (which propagates as frequency uncertainty). Validate measurement quality by confirming that reduced chi-squared falls between 0.8 and 1.5—values significantly outside this range indicate either underestimated uncertainties or unmodeled systematic biases requiring further investigation.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

Atomic emission spectroscopy reveals the quantized energy structure of bound electron states through characteristic photon wavelengths emitted during electronic transitions between discrete orbital levels. The hydrogen atom serves as the fundamental testbed because its single-electron configuration admits exact analytical solution of the Schrödinger equation, predicting emission line wavelengths via the Rydberg formula $1/\lambda = R_\infty \left( 1/n_f^2 - 1/n_i^2 \right)$ where $R_\infty = 1.0973731568160 \times 10^7$ m⁻¹ is the Rydberg constant, and $n_i > n_f$ are principal quantum numbers of the initial and final electron states. This exercise maps the visible Balmer series ($n_f = 2$) through high-resolution spectrometry, extracting the Rydberg constant from wavelength measurements and validating quantum mechanical energy level predictions against empirical line positions with sub-nanometer precision.

Configure the Ocean Optics USB2000+ spectrometer by connecting the fiber optic probe to the instrument's SMA905 input connector and launching the OceanView acquisition software to verify baseline system function. Navigate to the spectrometer settings panel and configure integration time to 100 milliseconds, enabling automatic dark spectrum subtraction and boxcar smoothing with width parameter 5 to suppress CCD readout noise without degrading spectral resolution. Position the hydrogen discharge tube vertically in a lamp housing with magnetic ballast, allowing 5 minutes warmup time for plasma stabilization before optical measurements commence. Mount the fiber optic probe 2 cm from the discharge tube viewing window at 90° to the tube axis to minimize self-absorption line broadening, and confirm that the spectrometer registers strong signal peaks in the 400–700 nm region with maximum counts below 90% of saturation threshold to preserve linear detector response.

Wavelength calibration is critical—uncalibrated spectrometers exhibit systematic wavelength errors exceeding ±2 nm that completely invalidate Rydberg constant extraction. Perform absolute wavelength calibration using the mercury vapor lamp reference with known emission lines at 404.656 nm, 435.833 nm, 546.074 nm, and 578.966 nm. Acquire a mercury spectrum with 50 ms integration time and identify the four calibration peaks through automated peak-finding algorithms:

```python
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def calibrate_wavelength(raw_spectrum_file, reference_wavelengths):
    """
    Perform wavelength calibration using known emission lines.
    
    Args:
        raw_spectrum_file: Path to uncalibrated mercury spectrum CSV
        reference_wavelengths: Array of NIST-certified mercury wavelengths (nm)
    
    Returns:
        Calibration polynomial coefficients [a0, a1, a2] for λ = a0 + a1*pixel + a2*pixel²
    """
    # Load raw spectrum (pixel vs intensity)
    df = pd.read_csv(raw_spectrum_file)
    pixels = df['pixel'].values
    intensity = df['intensity'].values
    
    # Find emission peaks
    peaks, properties = find_peaks(intensity, height=0.3*intensity.max(), 
                                    distance=50, prominence=0.2*intensity.max())
    
    # Sort peaks by intensity and select strongest four
    peak_intensities = intensity[peaks]
    strongest_indices = np.argsort(peak_intensities)[-4:]
    calibration_pixels = peaks[strongest_indices]
    calibration_pixels = np.sort(calibration_pixels)  # Order by wavelength
    
    print("Mercury calibration peaks found at pixels:", calibration_pixels)
    
    # Fit quadratic wavelength calibration: λ = a0 + a1*p + a2*p²
    coeffs = np.polyfit(calibration_pixels, reference_wavelengths, deg=2)
    
    # Calculate RMS calibration residual
    fitted_wavelengths = np.polyval(coeffs, calibration_pixels)
    residuals = fitted_wavelengths - reference_wavelengths
    rms_error = np.sqrt(np.mean(residuals**2))
    
    print(f"\nWavelength calibration coefficients:")
    print(f"  a0 = {coeffs[2]:.6f} nm")
    print(f"  a1 = {coeffs[1]:.8f} nm/pixel")
    print(f"  a2 = {coeffs[0]:.10e} nm/pixel²")
    print(f"RMS calibration error = {rms_error:.4f} nm")
    
    # Validate calibration quality
    if rms_error > 0.5:
        print("WARNING: Calibration RMS exceeds 0.5 nm - check peak identification")
    
    return coeffs

# Mercury reference wavelengths (NIST values)
hg_reference = np.array([404.656, 435.833, 546.074, 578.966])  # nm

# Simulate mercury spectrum acquisition (replace with actual spectrometer readout)
pixels_hg = np.arange(0, 2048)
wavelengths_true = 350 + 0.25 * pixels_hg + 1e-5 * pixels_hg**2

# Generate synthetic mercury spectrum with realistic line shapes
intensity_hg = np.zeros_like(pixels_hg, dtype=float)
for wl in hg_reference:
    pixel_center = np.argmin(np.abs(wavelengths_true - wl))
    # Gaussian line profile with instrumental broadening
    intensity_hg += 5000 * np.exp(-((pixels_hg - pixel_center) / 3.0)**2)

intensity_hg += np.random.normal(100, 30, len(pixels_hg))  # Baseline noise

# Save synthetic mercury spectrum
df_hg = pd.DataFrame({'pixel': pixels_hg, 'intensity': intensity_hg})
df_hg.to_csv('data/mercury_calibration.csv', index=False)

# Perform wavelength calibration
calib_coeffs = calibrate_wavelength('data/mercury_calibration.csv', hg_reference)
```

With wavelength calibration established, acquire the hydrogen emission spectrum using identical integration time and averaging parameters to maintain consistent measurement conditions. The hydrogen Balmer series exhibits four visible lines: H-alpha (656.3 nm, red, $n=3\to2$), H-beta (486.1 nm, cyan, $n=4\to2$), H-gamma (434.0 nm, blue, $n=5\to2$), and H-delta (410.2 nm, violet, $n=6\to2$). Export the calibrated spectrum as a CSV file with columns for wavelength and intensity, then apply Gaussian peak fitting to extract precise line centers with sub-pixel resolution:

```python
def fit_emission_lines(spectrum_file, calib_coeffs, expected_wavelengths, 
                       line_labels, search_window=5.0):
    """
    Fit Gaussian profiles to hydrogen emission lines and extract centers.
    
    Args:
        spectrum_file: Path to hydrogen spectrum CSV
        calib_coeffs: Wavelength calibration polynomial coefficients
        expected_wavelengths: Approximate line positions for peak search (nm)
        line_labels: Transition labels (e.g., 'H-alpha')
        search_window: Peak search window half-width (nm)
    
    Returns:
        DataFrame with measured wavelengths, uncertainties, and quantum numbers
    """
    df = pd.read_csv(spectrum_file)
    pixels = df['pixel'].values
    intensity = df['intensity'].values
    wavelengths = np.polyval(calib_coeffs, pixels)
    
    results = []
    
    for wl_expected, label in zip(expected_wavelengths, line_labels):
        # Extract spectral region around expected line
        mask = np.abs(wavelengths - wl_expected) < search_window
        wl_region = wavelengths[mask]
        int_region = intensity[mask]
        
        # Gaussian fit: I(λ) = A * exp(-((λ - λ0) / σ)²) + background
        def gaussian(wl, amplitude, center, sigma, bg):
            return amplitude * np.exp(-((wl - center) / sigma)**2) + bg
        
        # Initial parameter guess
        peak_idx = np.argmax(int_region)
        p0 = [int_region[peak_idx], wl_region[peak_idx], 0.5, np.median(int_region)]
        
        try:
            popt, pcov = curve_fit(gaussian, wl_region, int_region, p0=p0)
            perr = np.sqrt(np.diag(pcov))
            
            wl_measured = popt[1]
            wl_uncertainty = perr[1]
            
            results.append({
                'line': label,
                'wavelength_nm': wl_measured,
                'uncertainty_nm': wl_uncertainty,
                'intensity': popt[0],
                'fwhm_nm': 2.355 * popt[2]  # FWHM = 2.355 * sigma
            })
            
            print(f"{label}: λ = {wl_measured:.4f} ± {wl_uncertainty:.4f} nm")
            
            # Plot individual line fit
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(wl_region, int_region, 'o', markersize=4, label='Measured spectrum')
            wl_fit = np.linspace(wl_region[0], wl_region[-1], 300)
            int_fit = gaussian(wl_fit, *popt)
            ax.plot(wl_fit, int_fit, 'r-', linewidth=2, 
                   label=f'Gaussian fit: λ₀ = {wl_measured:.3f} nm')
            ax.axvline(wl_measured, color='gray', linestyle='--', alpha=0.5)
            ax.set_xlabel('Wavelength (nm)', fontsize=12)
            ax.set_ylabel('Intensity (counts)', fontsize=12)
            ax.set_title(f'Hydrogen {label} Line Profile', fontsize=14)
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"plots/hydrogen_{label.replace(' ', '_')}_fit.png", dpi=300)
            plt.close()
            
        except RuntimeError:
            print(f"WARNING: Fit failed for {label}")
    
    return pd.DataFrame(results)

# Balmer series expected positions and quantum number assignments
balmer_expected = [656.3, 486.1, 434.0, 410.2]  # nm
balmer_labels = ['H-alpha (n=3→2)', 'H-beta (n=4→2)', 
                 'H-gamma (n=5→2)', 'H-delta (n=6→2)']

# Simulate hydrogen spectrum acquisition
wavelengths_h = np.polyval(calib_coeffs, pixels_hg)
intensity_h = np.zeros_like(pixels_hg, dtype=float)

for wl in balmer_expected:
    pixel_center = np.argmin(np.abs(wavelengths_h - wl))
    # Add line with realistic Doppler and instrumental broadening
    intensity_h += 3000 * np.exp(-((pixels_hg - pixel_center) / 2.5)**2)

intensity_h += np.random.normal(80, 20, len(pixels_hg))

df_h = pd.DataFrame({'pixel': pixels_hg, 'intensity': intensity_h})
df_h.to_csv('data/hydrogen_balmer_spectrum.csv', index=False)

# Fit Balmer lines
balmer_results = fit_emission_lines('data/hydrogen_balmer_spectrum.csv', 
                                     calib_coeffs, balmer_expected, balmer_labels)
```

Extract the Rydberg constant by inverting measured wavelengths to wavenumbers $\tilde{\nu} = 1/\lambda$ and performing linear regression against the Balmer series quantum number term $(1/4 - 1/n^2)$. The Rydberg formula predicts $\tilde{\nu} = R_\infty (1/4 - 1/n^2)$, so plotting wavenumber versus quantum number term yields slope equal to the Rydberg constant:

```python
def extract_rydberg_constant(balmer_df):
    """
    Calculate Rydberg constant from Balmer series wavelength measurements.
    """
    # Extract principal quantum numbers from line labels
    quantum_numbers = np.array([3, 4, 5, 6])  # n_initial for Balmer series
    n_final = 2
    
    # Convert wavelengths to wavenumbers (m⁻¹)
    wavelengths_m = balmer_df['wavelength_nm'].values * 1e-9
    wavenumbers = 1 / wavelengths_m
    wavenumber_uncertainties = (balmer_df['uncertainty_nm'].values * 1e-9 / 
                                 wavelengths_m**2)
    
    # Rydberg formula terms: 1/n_f² - 1/n_i²
    rydberg_terms = 1/n_final**2 - 1/quantum_numbers**2
    
    # Weighted linear fit through origin: wavenumber = R_inf * rydberg_term
    weights = 1 / wavenumber_uncertainties**2
    R_measured = np.sum(weights * wavenumbers * rydberg_terms) / \
                 np.sum(weights * rydberg_terms**2)
    
    # Uncertainty propagation
    residuals = wavenumbers - R_measured * rydberg_terms
    chi_squared = np.sum(weights * residuals**2)
    dof = len(quantum_numbers) - 1
    reduced_chi_squared = chi_squared / dof
    
    R_uncertainty = np.sqrt(reduced_chi_squared / np.sum(weights * rydberg_terms**2))
    
    # Compare to literature value
    R_literature = 1.0973731568160e7  # m⁻¹
    relative_error = abs(R_measured - R_literature) / R_literature * 100
    
    print("\n=== RYDBERG CONSTANT MEASUREMENT ===")
    print(f"Measured R∞ = ({R_measured:.6e} ± {R_uncertainty:.6e}) m⁻¹")
    print(f"Literature R∞ = {R_literature:.10e} m⁻¹")
    print(f"Relative error = {relative_error:.3f}%")
    print(f"Reduced χ² = {reduced_chi_squared:.3f}")
    
    # Generate Rydberg plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.errorbar(rydberg_terms, wavenumbers / 1e7, 
                yerr=wavenumber_uncertainties / 1e7,
                fmt='o', markersize=10, capsize=5, capthick=2,
                label='Measured Balmer lines', color='darkred')
    
    term_fit = np.linspace(0, rydberg_terms.max(), 100)
    wavenumber_fit = R_measured * term_fit / 1e7
    
    ax.plot(term_fit, wavenumber_fit, 'b-', linewidth=2.5,
            label=f'Linear fit: R∞ = {R_measured:.4e} m⁻¹')
    
    ax.set_xlabel('Rydberg Term: 1/n²ₓ - 1/n²ᵢ', fontsize=14, fontweight='bold')
    ax.set_ylabel('Wavenumber (10⁷ m⁻¹)', fontsize=14, fontweight='bold')
    ax.set_title('Hydrogen Balmer Series: Rydberg Constant Determination', 
                 fontsize=16, fontweight='bold')
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.tick_params(labelsize=12)
    
    # Annotate individual lines
    for i, (term, wn, label) in enumerate(zip(rydberg_terms, wavenumbers/1e7, 
                                                balmer_df['line'])):
        ax.annotate(label.split()[0], xy=(term, wn), 
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=9, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('plots/rydberg_constant_measurement.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return R_measured, R_uncertainty

R_exp, R_exp_err = extract_rydberg_constant(balmer_results)
```

This spectroscopic method typically achieves 0.1–0.5% precision in Rydberg constant determination when executed with proper wavelength calibration and temperature-stabilized discharge tubes. The primary systematic error sources include Doppler broadening from thermal atomic motion (which shifts line centers), pressure broadening from collisional de-excitation (which asymmetrically distorts line shapes), and wavelength-dependent spectrometer resolution (which biases measured line positions). Validate the measurement by comparing individual line positions to NIST reference wavelengths—residuals should be randomly distributed with no trend across the visible spectrum. If residuals show quadratic curvature, the wavelength calibration polynomial is inadequate and requires higher-order terms or recalibration with additional reference lines.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

Quantum tunneling manifests wave-particle duality through the non-zero probability that particles penetrate classically forbidden potential barriers, enabling phenomena from alpha decay to scanning tunneling microscopy. The transmission coefficient $T(E)$ quantifies tunneling probability as a function of particle energy $E$ and barrier parameters (height $V_0$, width $a$), governed by the time-independent Schrödinger equation solutions in three spatial regions: incident/reflected waves in region I ($x < 0$), exponentially decaying wavefunction in the barrier region II ($0 < x < a$), and transmitted wave in region III ($x > a$). This exercise numerically integrates the Schrödinger equation across finite rectangular barriers with varying height-to-energy ratios, constructing transmission coefficient response curves that reveal quantum mechanical tunneling behavior inaccessible to classical mechanics. The analysis quantifies how transmission probability varies with barrier opacity parameter $\kappa a = a\sqrt{2m(V_0-E)}/\hbar$ and validates theoretical predictions against numerical wavefunction propagation with controlled discretization error.

Begin by formulating the time-independent Schrödinger equation in dimensionless form to expose the fundamental parameter dependencies. For a particle of mass $m$ with energy $E$ encountering a rectangular potential barrier of height $V_0$ and width $a$, the wavefunction $\psi(x)$ satisfies:

$$-\frac{\hbar^2}{2m}\frac{d^2\psi}{dx^2} + V(x)\psi = E\psi$$

where the potential is $V(x) = V_0$ for $0 \leq x \leq a$ and $V(x) = 0$ elsewhere. Introduce dimensionless position $\xi = x/a$ and energy ratio $\epsilon = E/V_0$, transforming the equation to dimensionless form with barrier opacity parameter $\alpha^2 = 2mV_0a^2/\hbar^2$ controlling the system physics:

$$-\frac{d^2\psi}{d\xi^2} + \alpha^2(1-\epsilon)\psi = \alpha^2\epsilon\psi$$

Numerical solution proceeds through finite difference discretization, approximating second derivatives via centered difference formula $\psi''(\xi) \approx [\psi(\xi+\Delta\xi) - 2\psi(\xi) + \psi(\xi-\Delta\xi)]/\Delta\xi^2$. Implement the shooting method: specify incident wave boundary conditions $\psi(0) = 1 + r$ and $\psi'(0) = ik(1-r)$ where $r$ is reflection coefficient and $k = \sqrt{2mE}/\hbar$ is the incident wavenumber, then integrate forward through the barrier region to extract transmission coefficient from asymptotic behavior in region III:

```python
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import matplotlib.pyplot as plt

def schrodinger_barrier_system(xi, psi_dpsi, alpha_squared, epsilon):
    """
    Define Schrödinger equation as first-order ODE system for barrier tunneling.
    
    State vector: [ψ, dψ/dξ]
    Equation: d²ψ/dξ² = α²[(1-ε)Θ(ξ)Θ(1-ξ) + ε]ψ
    where Θ is Heaviside step function defining barrier region 0 ≤ ξ ≤ 1
    
    Args:
        xi: Dimensionless position
        psi_dpsi: State vector [ψ, dψ/dξ]
        alpha_squared: Barrier opacity parameter α² = 2mV₀a²/ℏ²
        epsilon: Energy ratio ε = E/V₀
    
    Returns:
        Derivative vector [dψ/dξ, d²ψ/dξ²]
    """
    psi, dpsi = psi_dpsi
    
    # Potential: V = V₀ for 0 ≤ ξ ≤ 1, else V = 0
    if 0 <= xi <= 1:
        V_dimensionless = 1 - epsilon  # Inside barrier
    else:
        V_dimensionless = -epsilon  # Outside barrier (E relative to barrier top)
    
    d2psi = alpha_squared * V_dimensionless * psi
    
    return [dpsi, d2psi]

def calculate_transmission_coefficient(alpha_squared, epsilon, xi_span=(-2, 3), 
                                        n_points=5000):
    """
    Compute quantum tunneling transmission coefficient via wavefunction propagation.
    
    Args:
        alpha_squared: Barrier opacity α² (dimensionless)
        epsilon: Energy ratio E/V₀
        xi_span: Integration domain (barrier centered at ξ ∈ [0,1])
        n_points: Number of integration points
    
    Returns:
        Transmission coefficient T = |ψ(ξ→∞)|² / |ψ(ξ→-∞)|²
    """
    # Incident wave parameters (from left)
    k_incident = np.sqrt(alpha_squared * epsilon)  # Wavenumber outside barrier
    
    # Initial conditions: incident plane wave + reflected wave
    # ψ(ξ << 0) = exp(ik·ξ) + r·exp(-ik·ξ)
    # Normalize incident amplitude to 1, reflection r determined self-consistently
    psi_initial = 1.0  # Incident + reflection at left boundary
    dpsi_initial = 1j * k_incident * 1.0  # Derivative of incident wave
    
    initial_state = [psi_initial, dpsi_initial]
    
    # Integrate Schrödinger equation across barrier
    xi_eval = np.linspace(xi_span[0], xi_span[1], n_points)
    
    solution = solve_ivp(
        schrodinger_barrier_system,
        xi_span,
        initial_state,
        args=(alpha_squared, epsilon),
        t_eval=xi_eval,
        method='DOP853',  # High-order Runge-Kutta
        rtol=1e-10,
        atol=1e-12
    )
    
    psi = solution.y[0]
    dpsi = solution.y[1]
    
    # Extract transmitted wave amplitude (asymptotic region ξ >> 1)
    # ψ(ξ >> 1) ≈ t·exp(ik·ξ) where t is transmission amplitude
    # Use last 10% of domain for asymptotic fitting
    asymptotic_region = xi_eval > (xi_span[1] - 0.3)
    xi_asymptotic = xi_eval[asymptotic_region]
    psi_asymptotic = psi[asymptotic_region]
    
    # Fit transmitted wave: ψ = t·exp(ik·ξ)
    # Extract transmission amplitude via least-squares
    phase_factor = np.exp(-1j * k_incident * xi_asymptotic)
    t_amplitude = np.mean(psi_asymptotic * phase_factor)
    
    # Transmission coefficient T = |t|²
    T = np.abs(t_amplitude)**2
    
    return T, solution, xi_eval, psi

def analytical_transmission(alpha_squared, epsilon):
    """
    Calculate analytical transmission coefficient (thin barrier approximation).
    
    For ε < 1 (E < V₀): T ≈ 1 / [1 + (α²(1-ε)/4ε) sinh²(√(α²(1-ε)))]
    """
    if epsilon >= 1:
        # Classical transmission (over barrier)
        return 1.0
    
    kappa_squared = alpha_squared * (1 - epsilon)
    kappa = np.sqrt(kappa_squared)
    
    # WKB approximation for thick barrier
    T_analytical = 1 / (1 + (kappa_squared / (4 * epsilon)) * np.sinh(kappa)**2)
    
    return T_analytical

# Scan transmission coefficient vs energy ratio
epsilon_values = np.linspace(0.05, 1.5, 50)
alpha_squared = 50.0  # Moderate barrier opacity

T_numerical = []
T_analytical_values = []

print("Computing quantum tunneling transmission curves...")
print(f"Barrier opacity parameter α² = {alpha_squared:.1f}\n")

for eps in epsilon_values:
    T_num, _, _, _ = calculate_transmission_coefficient(alpha_squared, eps)
    T_an = analytical_transmission(alpha_squared, eps)
    
    T_numerical.append(T_num)
    T_analytical_values.append(T_an)
    
    print(f"ε = {eps:.3f}: T_numerical = {T_num:.6f}, T_analytical = {T_an:.6f}")

T_numerical = np.array(T_numerical)
T_analytical_values = np.array(T_analytical_values)

# Plot transmission coefficient response curve
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Linear scale plot
ax1.plot(epsilon_values, T_numerical, 'o-', linewidth=2, markersize=6,
         label='Numerical (Schrödinger integration)', color='darkblue')
ax1.plot(epsilon_values, T_analytical_values, '--', linewidth=2,
         label='Analytical (WKB approximation)', color='red')

ax1.axvline(1.0, color='gray', linestyle=':', linewidth=1.5, 
            label='Classical threshold (E = V₀)')
ax1.axhline(1.0, color='gray', linestyle=':', linewidth=1, alpha=0.5)

ax1.set_xlabel('Energy Ratio ε = E/V₀', fontsize=13, fontweight='bold')
ax1.set_ylabel('Transmission Coefficient T', fontsize=13, fontweight='bold')
ax1.set_title(f'Quantum Tunneling Through Rectangular Barrier (α² = {alpha_squared:.0f})',
              fontsize=15, fontweight='bold')
ax1.legend(fontsize=11, loc='lower right')
ax1.grid(True, alpha=0.3, linestyle=':')
ax1.set_ylim([-0.05, 1.1])

# Logarithmic scale plot (highlights tunneling regime)
tunneling_regime = epsilon_values < 1.0
ax2.semilogy(epsilon_values[tunneling_regime], T_numerical[tunneling_regime], 
             'o-', linewidth=2, markersize=6, label='Numerical', color='darkblue')
ax2.semilogy(epsilon_values[tunneling_regime], T_analytical_values[tunneling_regime],
             '--', linewidth=2, label='Analytical', color='red')

ax2.set_xlabel('Energy Ratio ε = E/V₀', fontsize=13, fontweight='bold')
ax2.set_ylabel('Transmission Coefficient T (log scale)', fontsize=13, fontweight='bold')
ax2.set_title('Tunneling Regime Detail (E < V₀)', fontsize=14, fontweight='bold')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3, linestyle=':', which='both')

plt.tight_layout()
plt.savefig('plots/quantum_tunneling_transmission.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nTransmission curve plot saved to plots/quantum_tunneling_transmission.png")
```

Extend the analysis by visualizing spatial wavefunction structure across the barrier, revealing exponential decay inside the classically forbidden region and phase continuity at boundary interfaces. Plot the real and imaginary components of $\psi(\xi)$ for representative tunneling ($\epsilon = 0.3$), resonant ($\epsilon = 1.0$), and over-barrier ($\epsilon = 1.4$) cases:

```python
# Generate wavefunction spatial profiles for three representative energies
test_energies = [0.3, 1.0, 1.4]
energy_labels = ['Sub-barrier tunneling (ε=0.3)', 
                 'Barrier threshold (ε=1.0)',
                 'Over-barrier transmission (ε=1.4)']

fig, axes = plt.subplots(3, 1, figsize=(12, 12))

for idx, (eps, label) in enumerate(zip(test_energies, energy_labels)):
    T, sol, xi, psi = calculate_transmission_coefficient(alpha_squared, eps)
    
    ax = axes[idx]
    
    # Plot real and imaginary parts
    ax.plot(xi, np.real(psi), '-', linewidth=2, label='Re(ψ)', color='blue')
    ax.plot(xi, np.imag(psi), '-', linewidth=2, label='Im(ψ)', color='red')
    ax.plot(xi, np.abs(psi)**2, '-', linewidth=2.5, label='|ψ|² (probability density)',
            color='black', alpha=0.6)
    
    # Mark barrier region
    ax.axvspan(0, 1, alpha=0.15, color='gray', label='Potential barrier')
    ax.axhline(0, color='black', linewidth=0.8, linestyle='-', alpha=0.3)
    
    # Add transmission coefficient to title
    ax.set_title(f'{label} — Transmission T = {T:.6f}', 
                fontsize=13, fontweight='bold')
    ax.set_xlabel('Dimensionless Position ξ = x/a', fontsize=12)
    ax.set_ylabel('Wavefunction ψ(ξ)', fontsize=12)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.set_xlim([xi[0], xi[-1]])

plt.tight_layout()
plt.savefig('plots/quantum_wavefunction_profiles.png', dpi=300, bbox_inches='tight')
plt.close()

print("Wavefunction spatial profiles saved to plots/quantum_wavefunction_profiles.png")
```

Quantify numerical accuracy by computing relative deviation between numerical transmission coefficients and analytical WKB approximations. The WKB method assumes slowly varying potentials and becomes exact in the semiclassical limit $\alpha \to \infty$, but exhibits deviations of order 10% for moderate opacity parameters. Calculate pointwise relative error $\delta T = |T_{\text{num}} - T_{\text{WKB}}|/T_{\text{WKB}}$ across the energy sweep:

```python
# Quantify numerical vs analytical accuracy
relative_errors = np.abs(T_numerical - T_analytical_values) / (T_analytical_values + 1e-10)

fig, ax = plt.subplots(figsize=(10, 6))

ax.semilogy(epsilon_values, relative_errors * 100, 'o-', linewidth=2, 
            markersize=7, color='darkgreen')

ax.axvline(1.0, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)
ax.axhline(1.0, color='red', linestyle='--', linewidth=1, 
           label='1% accuracy threshold')

ax.set_xlabel('Energy Ratio ε = E/V₀', fontsize=13, fontweight='bold')
ax.set_ylabel('Relative Error |T_num - T_WKB| / T_WKB (%)', fontsize=13, fontweight='bold')
ax.set_title('Numerical Integration Accuracy vs WKB Approximation', 
             fontsize=15, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, linestyle=':', which='both')

plt.tight_layout()
plt.savefig('plots/tunneling_numerical_accuracy.png', dpi=300, bbox_inches='tight')
plt.close()

mean_error = np.mean(relative_errors[epsilon_values < 1.0]) * 100
max_error = np.max(relative_errors[epsilon_values < 1.0]) * 100

print(f"\n=== NUMERICAL ACCURACY ANALYSIS ===")
print(f"Mean relative error (tunneling regime): {mean_error:.3f}%")
print(f"Maximum relative error: {max_error:.3f}%")
print(f"Integration method: 8th-order Runge-Kutta (DOP853)")
print(f"Relative tolerance: 1e-10, Absolute tolerance: 1e-12")
```

The numerical integration achieves sub-percent accuracy throughout the tunneling regime when executed with adaptive step-size control and tight error tolerances. Dominant error sources include numerical stiffness at sharp potential discontinuities (which requires fine spatial discretization), exponential growth of evanescent waves in thick barriers (which strains floating-point precision), and phase accumulation in oscillatory asymptotic regions (which demands long integration domains). Validate numerical robustness by varying the integration domain span and monitoring transmission coefficient convergence—properly converged results exhibit less than 0.1% variation when extending the asymptotic region from $\xi_{\text{max}} = 3$ to $\xi_{\text{max}} = 5$.

## Laboratory Cheat Sheet & Metric Verification Guide

**Fundamental Physical Constants (CODATA 2018 Exact Values)**

Planck constant: $h = 6.62607015 \times 10^{-34}$ J·s

Reduced Planck constant: $\hbar = h/(2\pi) = 1.054571817 \times 10^{-34}$ J·s

Elementary charge: $e = 1.602176634 \times 10^{-19}$ C

Speed of light: $c = 299792458$ m/s (exact definition)

Electron mass: $m_e = 9.1093837015 \times 10^{-31}$ kg

Rydberg constant: $R_\infty = 1.0973731568160 \times 10^7$ m⁻¹

**Quick Verification Commands**

Verify Python scientific environment integrity and package versions before beginning experimental data analysis workflows:

```bash
python -c 'import numpy as np; import scipy; import matplotlib; print(f"NumPy {np.__version__}\nSciPy {scipy.__version__}\nMatplotlib {matplotlib.__version__}")'
python -c 'import scipy.constants as const; print(f"h = {const.h:.6e} J·s\nRydberg = {const.Rydberg:.10e} m^-1")'
```

Expected output confirms installation correctness and constant value access:

```
NumPy 1.24.3
SciPy 1.10.1
Matplotlib 3.7.1
h = 6.626070e-34 J·s
Rydberg = 1.0973731569e+07 m^-1
```

**Photoelectric Effect Measurement Checklist**

Before commencing data acquisition, verify the following instrument configurations and environmental conditions to ensure measurement validity:

1. Mercury lamp warm-up time ≥ 10 minutes for spectral line intensity stabilization
2. Phototube dark current < 1 nA with lamp off and zero bias applied
3. Retarding potential supply output ripple < 10 mV RMS to prevent AC modulation artifacts
4. Optical enclosure light leakage < 0.1% verified by blocking external illumination
5. Temperature stability ±0.5°C maintained throughout multi-hour measurement session

**Hydrogen Spectroscopy Calibration Protocol**

Execute the following wavelength calibration sequence before acquiring hydrogen Balmer spectra:

1. Record mercury reference spectrum with 50 ms integration time and 10-spectrum averaging
2. Identify calibration peaks via automated peak-finding with minimum prominence 30% of maximum intensity
3. Fit quadratic wavelength polynomial $\lambda(\text{pixel}) = a_0 + a_1 p + a_2 p^2$ to mercury lines
4. Validate calibration RMS residual < 0.3 nm across 400–650 nm visible range
5. Store calibration coefficients in metadata header for all subsequent spectroscopic measurements

**Quantum Tunneling Simulation Convergence Criteria**

Numerical wavefunction integration achieves physical accuracy when satisfying these computational tolerances:

1. Relative integration tolerance rtol ≤ 1e-10 (fractional error per step)
2. Absolute integration tolerance atol ≤ 1e-12 (absolute wavefunction amplitude error)
3. Spatial domain extends ≥2 barrier widths beyond barrier edges to capture asymptotic behavior
4. Transmission coefficient converges to three significant figures when doubling integration point density
5. Wavefunction probability current conserved to within 0.01% across all spatial boundaries

**Error Propagation Formulas**

When combining multiple measured quantities with Gaussian uncertainties, propagate standard deviations through functional relationships via the multivariate error propagation formula. For function $f(x_1, x_2, \ldots, x_n)$ with independent variables having uncertainties $\sigma_{x_i}$:

$$\sigma_f = \sqrt{\sum_{i=1}^{n} \left(\frac{\partial f}{\partial x_i}\right)^2 \sigma_{x_i}^2}$$

Common cases encountered in quantum mechanics laboratory analysis:

Ratio uncertainty: $\sigma_{y/x} = (y/x)\sqrt{(\sigma_y/y)^2 + (\sigma_x/x)^2}$

Product uncertainty: $\sigma_{xy} = xy\sqrt{(\sigma_x/x)^2 + (\sigma_y/y)^2}$

Power law uncertainty: $\sigma_{x^n} = |nx^{n-1}|\sigma_x$

Weighted mean uncertainty: $\sigma_{\bar{x}} = 1/\sqrt{\sum_i w_i}$ where weights $w_i = 1/\sigma_i^2$

**Typical Experimental Uncertainties**

The following uncertainty ranges represent achievable precision in undergraduate laboratory implementations with standard equipment:

Photoelectric stopping potential: ±20 mV (systematic alignment effects dominate)

Wavelength calibration: ±0.3 nm (spectrometer pixel resolution limit)

Emission line center: ±0.05 nm (Gaussian fit statistical precision)

Photocurrent measurement: ±2% (multimeter accuracy + contact resistance)

Integration time: ±1 ms (spectrometer clock jitter)

**Common Experimental Failure Modes**

Photoelectric effect negative result: stopping potential independent of wavelength indicates excessive stray light contamination or cathode surface oxidation requiring vacuum tube replacement.

Hydrogen spectrum missing lines: discharge tube pressure out of specification (optimal range 0.1–1 Torr) or insufficient excitation voltage (requires >100 V DC minimum).

Tunneling transmission exceeds unity: numerical instability from insufficient integration tolerance or asymptotic region truncation cutting off transmitted wave before proper normalization.

Calibration RMS > 0.5 nm: wrong mercury lines identified (doublet resolution failure) or spectrometer wavelength drift during measurement requiring recalibration.

Chi-squared >> 1: underestimated measurement uncertainties or presence of unmodeled systematic error requiring instrumental diagnosis.
