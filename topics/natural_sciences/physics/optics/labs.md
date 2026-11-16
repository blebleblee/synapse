# Operational Verification Labs: Optics

## Objective & Laboratory Bench Setup

The experimental verification of optical phenomena constitutes one of the most direct routes to understanding electromagnetic wave propagation, photon behavior, and the classical-quantum transition in light-matter interactions. This laboratory sequence builds experimental competence through three progressively sophisticated optical measurement protocols: direct empirical observation of fundamental wave phenomena, systematic parameter variation to extract physical constants, and boundary condition stress testing to quantify measurement uncertainty and instrument resolution limits.

The primary objective of these verification labs is to train your hands and eyes to execute precision optical measurements while simultaneously developing the analytical discipline to propagate measurement uncertainties through computational models. You will measure wavelengths, refractive indices, focal lengths, diffraction patterns, and polarization states using direct physical manipulation of optical components on a bench-top setup. Each exercise yields quantitative data that you will analyze using Python scientific libraries to extract physical constants, plot response curves, and assess the validity regime of classical optical models.

Your laboratory bench must be configured with the following physical apparatus and computational environment. Begin with a stable optical breadboard or bench-top surface isolated from mechanical vibrations. Mount a stabilized laser source capable of emitting coherent monochromatic light in the visible spectrum; a 532 nm green diode laser with output power between 1 and 5 milliwatts provides excellent visibility and safety margins. Secure the laser using a magnetic or threaded mount that permits fine angular adjustment in two orthogonal axes. Position a precision linear translation stage with micrometer or digital encoder readout; this stage will translate optical components through the beam path with position uncertainty below 10 micrometers. Acquire a set of optical mounts, posts, and holders to position lenses, diffraction gratings, polarizers, apertures, and detectors at calibrated distances along the optical axis.

For refractive optics experiments, procure a set of plano-convex and bi-convex lenses with known nominal focal lengths spanning 25 mm to 200 mm. Obtain a parallel-faced glass block or prism with refractive index near 1.5, and ensure all optical surfaces are clean and free of dust or fingerprints. For diffraction experiments, acquire a transmission diffraction grating with ruling density between 300 and 600 lines per millimeter, mounted in a rotational stage for angular scanning. For polarization experiments, obtain a pair of linear polarizers mounted in rotational mounts with angular scales graduated in degrees. Position a photodetector or optical power meter at the beam terminus to measure transmitted light intensity; a calibrated silicon photodiode with amplifier and digital readout provides quantitative irradiance measurements in milliwatts per square centimeter. For spatial pattern recording, mount a translucent screen or white card at appropriate distances and capture images using a calibrated CCD camera or smartphone with known pixel pitch.

Your computational environment requires a Python installation with NumPy for numerical array operations, SciPy for optimization and statistical fitting, and Matplotlib for two-dimensional plotting of experimental data. Verify your Python environment by executing the diagnostic command that imports SciPy and prints its version identifier. The version must be 1.9 or later to ensure access to modern curve fitting and uncertainty propagation routines. Install Jupyter notebooks or configure a text editor with inline plot display capability to streamline the iteration cycle between data acquisition and graphical analysis. Prepare a laboratory notebook, either physical or digital, to record all measured values with timestamps, environmental conditions, and instrument calibration states.

Dimensional analysis and unit discipline are non-negotiable in optical metrology. All length measurements must be recorded in meters with appropriate SI prefixes: millimeters for component spacing, micrometers for slit widths and translation stage displacements, nanometers for wavelengths. Angular measurements must be converted to radians for computational input, although initial recording in degrees with decimal precision is acceptable. Irradiance and optical power must be recorded in watts or milliwatts with explicit notation of aperture areas to permit conversion to intensity units. Every experimental data table you construct must include column headers with explicit units, and every plot axis must carry a label specifying the physical quantity and its units in parentheses.

Safety protocols for laser operation are strict and mandatory. Never look directly into the laser beam or its specular reflections from optical surfaces. Position all optical components such that reflected or transmitted beams terminate on non-reflective beam stops or absorption targets. Post warning signs at the laboratory entrance indicating active laser operation. Wear laser safety glasses rated for the specific wavelength and power level of your source when aligning components or troubleshooting beam paths. Ensure the laser is mounted securely and cannot be accidentally knocked or rotated toward personnel or flammable materials. Operate the laser at the minimum power level necessary to achieve measurable signals, reserving higher power levels only for experiments requiring enhanced signal-to-noise ratios.

Environmental control significantly impacts optical measurement precision. Thermal convection currents in air create refractive index fluctuations that degrade beam collimation and introduce pointing instability. Minimize air currents by closing doors and windows, turning off forced-air ventilation during measurement intervals, and enclosing long beam paths in tubes or shrouds when feasible. Mechanical vibrations from footsteps, nearby machinery, or building infrastructure couple into the optical bench and degrade interferometric or diffraction measurements. Isolate the bench using passive damping pads or active vibration isolation platforms if available. Ambient light contamination saturates photodetectors and reduces measurement dynamic range. Dim room lights and shield detectors from stray illumination using baffles or enclosures with apertures aligned to the beam path.

Calibration of the translation stage constitutes the first critical measurement task. Verify the stage micrometer or encoder readout by translating a precision machined gauge block or calibrated reference target through the beam and comparing the indicated displacement to the known physical dimension. Record the calibration factor as the ratio of true displacement to indicated displacement, and apply this correction factor to all subsequent position measurements. Check for hysteresis by cycling the stage through forward and reverse translation and observing any offset between forward and reverse position readings at the same physical location. Quantify backlash by commanding a small reverse displacement and measuring the stage travel required to reverse the direction of motion. Document these calibration results in your laboratory notebook and update them whenever the stage is dismounted or mechanically adjusted.

The laser wavelength must be verified against a known spectral reference if precise absolute wavelength knowledge is required. Position a calibrated spectrometer or wavelength meter in the beam path and record the center wavelength with its uncertainty. If a reference instrument is unavailable, use the nominal wavelength specified by the laser manufacturer and assign a conservative uncertainty of plus or minus 5 nanometers. This uncertainty propagates through all subsequent calculations involving wavelength-dependent phenomena and must be tracked rigorously using uncertainty propagation formulae.

## Exercise 1: Empirical Observation & Measurement Protocol

The first experimental verification sequence constructs direct empirical evidence for the wave nature of light through single-slit diffraction and establishes measurement protocols for extracting the laser wavelength from spatial intensity distributions. Single-slit diffraction demonstrates the Huygens-Fresnel principle: each point within an illuminated aperture acts as a secondary wavelet source, and the observed intensity pattern on a distant screen results from the superposition of these wavelets with path-length-dependent phase relationships. The central maximum intensity, angular positions of the first minima, and the envelope decay of higher-order maxima encode the slit width and optical wavelength through the diffraction integral.

Begin by constructing the single-slit diffraction apparatus. Mount a narrow rectangular slit with adjustable width in a precision holder positioned perpendicular to the laser beam path. Commercial adjustable slits with micrometer-controlled jaw separation are ideal, but a pair of parallel razor blades clamped in a mount with micrometer positioning also suffices. Position the slit approximately 1 meter from the laser source to ensure incident beam plane-wave character; the beam diameter at the slit must be several times larger than the slit width to approximate uniform illumination. Place a translucent white screen or matte photographic paper at a distance L between 1 and 3 meters downstream from the slit. Ensure the screen is perpendicular to the optical axis and that the room is darkened to maximize diffraction pattern visibility.

Activate the laser and adjust the slit width until a clear central bright fringe appears on the screen with at least three or four visible dark minima symmetrically positioned on either side. The slit width should be in the range of 50 to 200 micrometers to produce minima separated by several millimeters at typical screen distances. If the pattern is too compressed or too expanded, adjust either the slit width or the screen distance to achieve well-resolved features. Use the translation stage or a calibrated ruler to measure the distance L from the slit plane to the screen with millimeter accuracy. Record this distance in your laboratory notebook.

The intensity distribution on the screen follows the single-slit diffraction formula, where the amplitude at an observation point making angle theta with the optical axis is proportional to the sinc function. The electric field amplitude is given by the Fraunhofer diffraction integral, yielding intensity proportional to the square of the sinc function. The first intensity minimum occurs at an angle theta_1 satisfying the condition that the path difference between wavelets from the top and bottom edges of the slit equals one wavelength. This geometric condition translates to the equation a sin(theta_1) equals lambda, where a denotes the slit width and lambda denotes the optical wavelength. For small angles measured in radians, the sine function approximates the angle itself, so the angular position of the first minimum simplifies to theta_1 equals lambda divided by a. On the screen at distance L, this angular position corresponds to a transverse displacement y_1 equals L times theta_1, which equals L times lambda divided by a.

Measure the transverse positions of the diffraction minima on the screen using a precision ruler or by capturing a digital image with calibrated pixel scale. Identify the center of the central maximum by locating the midpoint between the first minima on either side. Measure the distance y_1 from this center to the first minimum on one side, then measure the distance to the first minimum on the opposite side and verify that the two measurements agree within experimental uncertainty. Record both values and compute their mean to reduce random error. Repeat the measurement for the second and third minima if they are clearly visible and sufficiently intense above the background. Each measurement should be repeated three times with the ruler repositioned between trials to quantify measurement repeatability.

With the measured positions y_1, the screen distance L, and the geometric relationship derived above, solve for the slit width using the rearranged formula a equals L times lambda divided by y_1. Substitute the known or nominal laser wavelength, for example 532 nanometers for a green diode laser, and compute the inferred slit width in micrometers. Compare this computed value to the slit width indicated by the micrometer on the adjustable slit assembly. If the two values agree within 10 percent, the measurement protocol is validated and the wave model is confirmed. If they disagree significantly, check for systematic errors such as incorrect screen distance, misidentified minima, or non-uniform slit illumination.

Now invert the measurement logic to extract the laser wavelength from a slit of known width. Obtain a precision single slit etched in an opaque metal foil or lithographically fabricated on a glass substrate with certified width traceable to a dimensional standard. Position this calibrated slit in the beam and repeat the diffraction pattern measurement. Measure the screen distance L and the position y_1 of the first minimum with maximum achievable precision. Solve for the wavelength using lambda equals a times y_1 divided by L. Record the computed wavelength and compare it to the nominal specification provided by the laser manufacturer or measured by an independent spectrometer. Compute the percent difference and assign an uncertainty budget accounting for the ruler resolution, screen distance uncertainty, and slit width certification tolerance.

Document your measurements in a structured Python script that imports NumPy for array operations and Matplotlib for plotting. Create arrays holding the measured positions of the minima, indexed by their order m where m equals 1 for the first minimum, m equals 2 for the second, and so forth. The theoretical angular position of the m-th minimum satisfies a sin(theta_m) equals m times lambda, which translates to a linear relationship y_m equals m times L times lambda divided by a in the small-angle limit. Fit a straight line through the origin to the measured positions y_m versus diffraction order m using SciPy's linear regression routine, and extract the slope as the fitted value of L times lambda divided by a. Solve for lambda and compare to the nominal value.

The following Python code block implements the complete single-slit analysis pipeline. It reads measured data, performs linear regression, computes the inferred wavelength with uncertainty, and generates a publication-quality plot overlaying experimental data with theoretical predictions.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress

# Experimental parameters
L = 2.000  # screen distance in meters
a = 100e-6  # slit width in meters (100 micrometers)
lambda_nominal = 532e-9  # nominal laser wavelength in meters

# Measured positions of diffraction minima (in meters from central max)
# Order m: 1, 2, 3, 4
y_measured = np.array([10.64e-3, 21.28e-3, 31.92e-3, 42.56e-3])
m_order = np.array([1, 2, 3, 4])

# Uncertainty in position measurements (ruler resolution)
y_uncertainty = 0.5e-3  # 0.5 mm

# Linear regression to extract wavelength
# Theory: y_m = m * (L * lambda / a)
# Slope = L * lambda / a
slope, intercept, r_value, p_value, std_err = linregress(m_order, y_measured)

# Extract wavelength from slope
lambda_measured = (slope * a) / L
lambda_uncertainty = (std_err * a) / L

print(f"Measured wavelength: {lambda_measured * 1e9:.2f} ± {lambda_uncertainty * 1e9:.2f} nm")
print(f"Nominal wavelength: {lambda_nominal * 1e9:.2f} nm")
print(f"Percent difference: {100 * abs(lambda_measured - lambda_nominal) / lambda_nominal:.2f}%")
print(f"R-squared: {r_value**2:.6f}")

# Generate theoretical prediction curve
m_theory = np.linspace(0, 5, 100)
y_theory = m_theory * (L * lambda_nominal / a)

# Plot experimental data and theoretical curve
plt.figure(figsize=(10, 6))
plt.errorbar(m_order, y_measured * 1e3, yerr=y_uncertainty * 1e3, 
             fmt='o', markersize=8, capsize=5, capthick=2,
             label='Experimental Data', color='darkblue')
plt.plot(m_theory, y_theory * 1e3, '--', linewidth=2, 
         label=f'Theory (λ = {lambda_nominal * 1e9:.0f} nm)', color='red')
plt.xlabel('Diffraction Order m', fontsize=12)
plt.ylabel('Position y (mm)', fontsize=12)
plt.title('Single-Slit Diffraction: Experimental Verification', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('single_slit_diffraction.png', dpi=300)
plt.show()

# Compute residuals
y_predicted = m_order * (L * lambda_measured / a)
residuals = y_measured - y_predicted
chi_squared = np.sum((residuals / y_uncertainty)**2)
degrees_of_freedom = len(m_order) - 2  # 2 fit parameters (slope, intercept)
reduced_chi_squared = chi_squared / degrees_of_freedom

print(f"\nGoodness of fit:")
print(f"Chi-squared: {chi_squared:.3f}")
print(f"Reduced chi-squared: {reduced_chi_squared:.3f}")
print(f"Residuals (μm): {residuals * 1e6}")
```

Execute this script after substituting your measured values for screen distance, slit width, and minima positions. The linear regression extracts the wavelength from the slope of the position-versus-order line, and the standard error of the slope propagates directly to the wavelength uncertainty. The R-squared value quantifies the linearity of the data; values above 0.999 indicate excellent agreement with the single-slit diffraction model. The reduced chi-squared statistic near unity confirms that the measurement uncertainties are neither underestimated nor overestimated.

Analyze the residuals to identify systematic deviations from the linear model. If residuals exhibit a parabolic trend, the screen may not be perpendicular to the optical axis, or the slit may be tilted. If alternate residuals are positive and negative with increasing magnitude at higher orders, spherical aberration in the laser beam or non-uniform slit illumination may be present. If all residuals are biased positive or negative, the screen distance or slit width may be incorrectly recorded.

Extend the measurement to verify the wavelength dependence by repeating the experiment with a red laser diode at 650 nanometers or a blue laser at 450 nanometers. Compare the measured wavelengths to nominal specifications and confirm that the ratio of measured wavelengths matches the ratio of nominal values. This cross-validation eliminates potential systematic errors in the measurement apparatus that would affect all wavelengths identically.

The single-slit experiment establishes the foundational measurement protocol: identify a physical phenomenon governed by a well-established theoretical model, design an experimental apparatus to produce measurable observables predicted by that model, acquire quantitative data with documented uncertainties, perform statistical analysis to extract physical parameters, and compare extracted values to independent reference measurements. This protocol generalizes to all subsequent optical verification exercises.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

The second experimental sequence quantifies the refractive properties of optical materials through systematic parameter variation and constructs empirical response curves relating measurable observables to material properties. Refraction at dielectric interfaces encodes the material refractive index through Snell's law, which relates incident and transmitted angles to the ratio of wave velocities in the two media. By measuring the angular deflection of a laser beam transmitted through a parallel-faced glass block as a function of incident angle, you will extract the refractive index through least-squares fitting and assess the validity limits of geometric optics.

Construct the refraction measurement apparatus by mounting a rectangular glass block with parallel entrance and exit faces on a precision rotational stage. The block should be several centimeters in lateral dimension with thickness between 1 and 3 centimeters. Clean all optical surfaces thoroughly using lens tissue and isopropanol to remove dust and oils. Position the rotational stage such that the laser beam enters the block at approximately the center of the entrance face. Mount the stage on a rotation axis perpendicular to the plane containing the incident and transmitted beams. Attach a calibrated angular scale or rotary encoder to the stage with resolution of 0.1 degrees or better.

Downstream from the glass block, position a translucent screen or position-sensitive detector at a fixed distance D between 50 and 100 centimeters from the block exit face. Mark the undeflected beam position on the screen with the glass block removed from the beam path; this position defines the zero-deflection reference. Reinsert the glass block at normal incidence such that the entrance and exit faces are perpendicular to the incident beam. Verify that the transmitted beam strikes the screen at the zero-deflection reference position, confirming that the block faces are parallel and the rotation axis is aligned.

The measurement protocol sweeps the incident angle from normal incidence at zero degrees through a range up to 60 or 70 degrees while recording the transverse deflection of the transmitted beam on the screen. Begin with the block at normal incidence and record the baseline beam position. Rotate the stage incrementally by 5-degree steps, pausing at each angle to allow the beam position to stabilize. At each incident angle theta_i, measure the transverse displacement y of the transmitted beam from the zero-deflection reference using a precision ruler or by capturing a digital image and extracting the centroid position in image analysis software. Record both theta_i and y in a data table with explicit units.

The geometric relationship between incident angle theta_i, transmitted angle theta_t, block thickness t, refractive index n, and beam deflection y follows from sequential application of Snell's law and geometric projection. At the entrance face, Snell's law relates the incident and refracted angles: sin(theta_i) equals n times sin(theta_r), where theta_r denotes the refraction angle inside the glass. At the exit face, the beam refracts again as it exits into air, with the exit angle equal to the incident angle by symmetry for a parallel-faced block. The lateral displacement of the beam through the block is t times tan(theta_r), and the additional displacement propagating from the exit face to the screen is the difference between the emergent beam path and the continuation of the incident beam path. The total transverse deflection on the screen depends nonlinearly on theta_i and n.

For moderate angles where the small-angle approximation breaks down but the block remains thin compared to the screen distance, the deflection can be approximated analytically. However, for maximum accuracy and to handle arbitrary angles, compute the exact ray trace numerically. Implement a Python function that accepts incident angle theta_i, refractive index n, block thickness t, and screen distance D as inputs and returns the predicted deflection y. This function applies Snell's law to compute the refraction angle inside the block, traces the ray through the block thickness using trigonometric projection, applies Snell's law again at the exit face to compute the emergent angle, and projects the emergent ray to the screen position.

The following Python code block implements the exact ray-tracing function and performs nonlinear least-squares fitting to extract the refractive index from measured deflection data.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def ray_trace_deflection(theta_i_deg, n, t, D):
    """
    Compute lateral deflection of laser beam transmitted through parallel glass block.
    
    Parameters:
    theta_i_deg: incident angle in degrees
    n: refractive index of glass
    t: block thickness in meters
    D: screen distance from block exit face in meters
    
    Returns:
    y: transverse deflection in meters
    """
    theta_i = np.radians(theta_i_deg)
    
    # Snell's law at entrance: sin(theta_i) = n * sin(theta_r)
    sin_theta_r = np.sin(theta_i) / n
    
    # Check for total internal reflection (should not occur for n > 1)
    if np.any(np.abs(sin_theta_r) > 1):
        return np.nan
    
    theta_r = np.arcsin(sin_theta_r)
    
    # Lateral displacement through block
    y_block = t * np.tan(theta_i - theta_r)
    
    # Exit angle equals incident angle (parallel faces)
    theta_exit = theta_i
    
    # Additional displacement to screen
    y_screen = D * np.tan(theta_exit)
    
    # Total deflection relative to undeflected beam
    y_undeflected = D * np.tan(theta_i)
    y = y_block + y_screen - y_undeflected
    
    return y

# Experimental parameters
t_block = 20e-3  # block thickness 20 mm
D_screen = 0.80  # screen distance 80 cm

# Measured data: incident angles and deflections
theta_i_data = np.array([0, 10, 20, 30, 40, 50, 60])  # degrees
y_data = np.array([0, 1.8, 3.8, 6.2, 9.1, 12.8, 17.5]) * 1e-3  # convert mm to meters

# Measurement uncertainty
y_uncertainty = 0.3e-3  # 0.3 mm ruler resolution

# Fit model: deflection as function of incident angle with n as free parameter
def model(theta_i, n):
    return ray_trace_deflection(theta_i, n, t_block, D_screen)

# Perform nonlinear least-squares fit
initial_guess = [1.5]  # initial guess for refractive index
popt, pcov = curve_fit(model, theta_i_data, y_data, p0=initial_guess, 
                       sigma=y_uncertainty * np.ones_like(y_data), absolute_sigma=True)

n_fitted = popt[0]
n_uncertainty = np.sqrt(pcov[0, 0])

print(f"Fitted refractive index: {n_fitted:.4f} ± {n_uncertainty:.4f}")
print(f"Typical glass n ≈ 1.52 (crown glass), 1.50 (soda-lime glass)")

# Generate theoretical curve with fitted parameter
theta_i_theory = np.linspace(0, 70, 200)
y_theory = ray_trace_deflection(theta_i_theory, n_fitted, t_block, D_screen)

# Compute residuals and chi-squared
y_predicted = model(theta_i_data, n_fitted)
residuals = y_data - y_predicted
chi_squared = np.sum((residuals / y_uncertainty)**2)
degrees_of_freedom = len(theta_i_data) - 1  # 1 fit parameter
reduced_chi_squared = chi_squared / degrees_of_freedom

print(f"\nGoodness of fit:")
print(f"Chi-squared: {chi_squared:.3f}")
print(f"Reduced chi-squared: {reduced_chi_squared:.3f}")

# Plot experimental data and fitted curve
plt.figure(figsize=(10, 6))
plt.errorbar(theta_i_data, y_data * 1e3, yerr=y_uncertainty * 1e3,
             fmt='s', markersize=8, capsize=5, capthick=2,
             label='Experimental Data', color='darkgreen')
plt.plot(theta_i_theory, y_theory * 1e3, '-', linewidth=2,
         label=f'Fitted Model (n = {n_fitted:.3f})', color='purple')
plt.xlabel('Incident Angle θᵢ (degrees)', fontsize=12)
plt.ylabel('Beam Deflection y (mm)', fontsize=12)
plt.title('Refraction Through Glass Block: Index Extraction', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xlim(0, 70)
plt.tight_layout()
plt.savefig('refraction_index_fit.png', dpi=300)
plt.show()

# Plot residuals
plt.figure(figsize=(10, 4))
plt.errorbar(theta_i_data, residuals * 1e6, yerr=y_uncertainty * 1e6,
             fmt='o', markersize=6, capsize=4, color='darkred')
plt.axhline(0, color='black', linestyle='--', linewidth=1)
plt.xlabel('Incident Angle θᵢ (degrees)', fontsize=12)
plt.ylabel('Residual (μm)', fontsize=12)
plt.title('Fit Residuals', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('refraction_residuals.png', dpi=300)
plt.show()
```

Execute this script with your measured deflection data substituted into the arrays. The nonlinear curve fitting routine optimizes the refractive index to minimize the chi-squared statistic, accounting for the measurement uncertainty in each data point. The fitted value should agree with literature values for common optical glasses: crown glass near 1.52, soda-lime glass near 1.50, borosilicate glass near 1.47. The uncertainty in the fitted index reflects both the precision of your deflection measurements and the sensitivity of the model to the index parameter.

Examine the residuals plot to identify systematic deviations. If residuals are randomly distributed about zero with magnitude comparable to the measurement uncertainty, the geometric optics model is validated. If residuals exhibit a systematic trend increasing with angle, nonlinear effects such as dispersion or beam divergence may be significant. If residuals are larger than expected from the stated uncertainty, re-evaluate the uncertainty budget by considering additional sources such as angular alignment error, screen distance uncertainty, or thermal expansion of the glass block.

Extend the measurement to quantify chromatic dispersion by repeating the experiment with laser sources of different wavelengths. Measure the refractive index for red, green, and blue wavelengths and plot the dispersion curve showing refractive index as a function of wavelength. Fit the data to the Cauchy dispersion formula, n equals A plus B divided by lambda squared, where A and B are empirical constants characterizing the material. Extract the Cauchy coefficients and compare them to literature values for the identified glass type.

The parameter variation methodology generalizes to all optical component characterization tasks. For lenses, vary the object distance while measuring image distance to construct a response curve validating the thin-lens equation. For polarizers, vary the analyzer angle relative to the polarizer and measure transmitted intensity to confirm Malus's law. For diffraction gratings, vary the incident angle and measure the angular positions of diffracted orders to extract the grating pitch. In each case, the experimental protocol follows the same structure: identify a theoretical model predicting a measurable observable as a function of a controllable parameter, systematically vary that parameter while recording the observable, perform statistical fitting to extract material or component properties, and assess goodness-of-fit through residual analysis and chi-squared statistics.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

The third experimental sequence probes the validity boundaries of classical optical models through controlled stress testing and constructs rigorous uncertainty budgets for derived physical constants. Every physical model possesses a finite domain of validity bounded by approximations, neglected effects, and idealized assumptions. Identifying these boundaries through deliberate violation of model assumptions reveals the phenomenology that classical models cannot describe and motivates the necessity of more sophisticated theoretical frameworks.

This exercise focuses on polarization optics and the Malus intensity law, which predicts that the transmitted intensity through a pair of linear polarizers depends on the square of the cosine of the relative angle between their transmission axes. The law assumes ideal polarizers with perfect extinction and infinite optical density, monochromatic plane-wave illumination, and negligible reflection or scattering losses. By systematically stressing these assumptions through component misalignment, finite extinction ratios, and depolarized sources, you will quantify the model breakdown and extract corrected empirical parameters accounting for non-ideal effects.

Construct the polarization measurement apparatus by mounting two linear polarizers in precision rotational stages along a common optical axis. Position the first polarizer, designated as the polarizer, in the laser beam path with its transmission axis vertical. Mount a photodetector downstream to measure transmitted optical power in milliwatts. Position the second polarizer, designated as the analyzer, between the first polarizer and the detector, with its transmission axis initially parallel to the polarizer. Attach a calibrated rotary stage to the analyzer with angular resolution of 1 degree or better and zero-angle registration marks clearly visible.

Measure the baseline transmitted intensity with both polarizers aligned parallel. Record this maximum intensity I_max in milliwatts. Rotate the analyzer incrementally through a full 360-degree cycle in steps of 10 degrees, recording the transmitted intensity at each angular position. At each angle, allow the photodetector reading to stabilize for several seconds before recording the value. Repeat the angular sweep three times to quantify measurement repeatability and compute the standard deviation of repeated measurements at each angle.

The ideal Malus law predicts transmitted intensity I equals I_max times cosine-squared of the relative angle theta, where theta denotes the analyzer rotation angle relative to the parallel configuration. Plot the measured intensity versus angle and overlay the theoretical prediction. For ideal polarizers, the intensity should reach zero at 90 degrees when the transmission axes are crossed. In practice, finite extinction ratios permit non-zero transmission at crossed angles, violating the ideal model.

Quantify the extinction ratio by measuring the minimum transmitted intensity I_min at the 90-degree crossed configuration. The extinction ratio is defined as the ratio I_max divided by I_min, typically expressed in decibels as 10 times the logarithm base 10 of the ratio. High-quality Glan-Thompson calcite polarizers achieve extinction ratios exceeding 100,000 to 1, corresponding to 50 dB. Polymer sheet polarizers achieve extinction ratios near 1000 to 1 or 30 dB. Dichroic film polarizers may achieve only 100 to 1 or 20 dB.

Modify the Malus law to account for finite extinction by introducing a baseline offset intensity I_offset representing leakage through the crossed polarizers. The corrected model becomes I equals I_offset plus I_max minus I_offset times cosine-squared theta. Fit this three-parameter model to your measured data using nonlinear least-squares regression and extract the fitted values of I_max, I_offset, and any phase offset in the angular origin. Compare the fitted I_offset to the directly measured I_min and verify consistency.

The following Python code block implements the corrected Malus law fitting and generates diagnostic plots.

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Measured data: analyzer angle (degrees) and transmitted intensity (mW)
theta_data = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 
                       100, 110, 120, 130, 140, 150, 160, 170, 180,
                       190, 200, 210, 220, 230, 240, 250, 260, 270, 280,
                       290, 300, 310, 320, 330, 340, 350])

I_data = np.array([4.82, 4.65, 4.18, 3.45, 2.58, 1.68, 0.95, 0.42, 0.12, 0.048,
                   0.11, 0.39, 0.89, 1.62, 2.52, 3.41, 4.15, 4.63, 4.80,
                   4.67, 4.21, 3.48, 2.61, 1.71, 0.98, 0.44, 0.13, 0.051,
                   0.12, 0.41, 0.92, 1.65, 2.55, 3.44, 4.18, 4.66])

# Measurement uncertainty (photodetector resolution)
I_uncertainty = 0.02  # mW

# Ideal Malus law (no offset)
def malus_ideal(theta, I_max):
    return I_max * np.cos(np.radians(theta))**2

# Corrected Malus law with extinction offset
def malus_corrected(theta, I_max, I_offset, phase):
    return I_offset + (I_max - I_offset) * np.cos(np.radians(theta - phase))**2

# Fit ideal model
popt_ideal, pcov_ideal = curve_fit(malus_ideal, theta_data, I_data, p0=[5.0])
I_max_ideal = popt_ideal[0]

# Fit corrected model
popt_corrected, pcov_corrected = curve_fit(malus_corrected, theta_data, I_data, 
                                            p0=[5.0, 0.05, 0.0])
I_max_fitted, I_offset_fitted, phase_fitted = popt_corrected
uncertainties = np.sqrt(np.diag(pcov_corrected))

print("Ideal Malus Law Fit:")
print(f"  I_max = {I_max_ideal:.3f} mW")

print("\nCorrected Malus Law Fit:")
print(f"  I_max = {I_max_fitted:.3f} ± {uncertainties[0]:.3f} mW")
print(f"  I_offset = {I_offset_fitted:.4f} ± {uncertainties[1]:.4f} mW")
print(f"  Phase offset = {phase_fitted:.2f} ± {uncertainties[2]:.2f} degrees")

# Compute extinction ratio
extinction_ratio = I_max_fitted / I_offset_fitted
extinction_dB = 10 * np.log10(extinction_ratio)
print(f"  Extinction ratio = {extinction_ratio:.0f}:1 ({extinction_dB:.1f} dB)")

# Generate theoretical curves
theta_theory = np.linspace(0, 360, 500)
I_ideal = malus_ideal(theta_theory, I_max_ideal)
I_corrected = malus_corrected(theta_theory, I_max_fitted, I_offset_fitted, phase_fitted)

# Compute residuals
I_predicted_corrected = malus_corrected(theta_data, I_max_fitted, I_offset_fitted, phase_fitted)
residuals_corrected = I_data - I_predicted_corrected
chi_squared = np.sum((residuals_corrected / I_uncertainty)**2)
dof = len(theta_data) - 3  # 3 fit parameters
reduced_chi_squared = chi_squared / dof

print(f"\nGoodness of fit:")
print(f"  Chi-squared = {chi_squared:.2f}")
print(f"  Reduced chi-squared = {reduced_chi_squared:.3f}")

# Plot data and fits
plt.figure(figsize=(12, 6))
plt.errorbar(theta_data, I_data, yerr=I_uncertainty, fmt='o', markersize=6,
             capsize=3, label='Experimental Data', color='navy', alpha=0.7)
plt.plot(theta_theory, I_ideal, '--', linewidth=2, 
         label='Ideal Malus Law', color='orange')
plt.plot(theta_theory, I_corrected, '-', linewidth=2.5,
         label='Corrected Model (with extinction offset)', color='crimson')
plt.xlabel('Analyzer Angle θ (degrees)', fontsize=12)
plt.ylabel('Transmitted Intensity (mW)', fontsize=12)
plt.title('Malus Law: Ideal vs. Corrected Model', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xlim(0, 360)
plt.ylim(0, 5.5)
plt.tight_layout()
plt.savefig('malus_law_fit.png', dpi=300)
plt.show()

# Plot residuals on log scale to visualize extinction region
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(theta_data, residuals_corrected * 1e3, 'o', markersize=6, color='darkred')
plt.axhline(0, color='black', linestyle='--', linewidth=1)
plt.xlabel('Analyzer Angle θ (degrees)', fontsize=11)
plt.ylabel('Residual (μW)', fontsize=11)
plt.title('Fit Residuals (Linear Scale)', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.semilogy(theta_data, I_data, 'o', markersize=6, label='Data', color='navy')
plt.semilogy(theta_theory, I_corrected, '-', linewidth=2, label='Fit', color='crimson')
plt.xlabel('Analyzer Angle θ (degrees)', fontsize=11)
plt.ylabel('Transmitted Intensity (mW, log scale)', fontsize=11)
plt.title('Intensity on Log Scale (Extinction Detail)', fontsize=12, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3, which='both')
plt.xlim(0, 360)
plt.tight_layout()
plt.savefig('malus_residuals_and_log.png', dpi=300)
plt.show()
```

Execute this analysis with your measured intensity data. The corrected model fit yields physically meaningful parameters: I_max represents the true maximum transmission, I_offset quantifies polarizer imperfection, and the phase offset accounts for any angular misalignment in the zero-angle reference. The extinction ratio extracted from the fit characterizes the polarizer quality and enables comparison across different polarizer types.

Stress-test the model by introducing controlled perturbations. Replace the laser source with a partially depolarized source such as an LED or incandescent lamp viewed through a diffuser. Repeat the angular intensity measurement and observe that the modulation depth decreases: the ratio of maximum to minimum intensity is reduced compared to the fully polarized laser case. Quantify the degree of polarization using the formula DOP equals I_max minus I_min divided by I_max plus I_min. For fully polarized light, DOP equals unity; for unpolarized light, DOP equals zero. Fit the measured data to a model combining polarized and unpolarized components: I equals I_unpolarized plus I_polarized times cosine-squared theta. Extract the fraction of polarized intensity and compare it to independent measurements using a quarter-wave plate and Stokes parameter analysis.

Introduce angular misalignment by tilting one polarizer out of perpendicularity with the beam axis. Measure the transmitted intensity as a function of tilt angle and observe that the extinction degrades rapidly as the polarizer normal deviates from the beam propagation direction. This effect arises from the angular dependence of the polarizer transmission axis projection and the oblique incidence phase shifts. Quantify the angular tolerance by determining the tilt angle at which the extinction ratio degrades by a factor of two. This tolerance specification is critical for aligning polarization-sensitive optical systems in practical applications.

Conduct wavelength stress testing by repeating the measurement with broadband white light filtered through narrow-band interference filters centered at different wavelengths. Plot the extinction ratio as a function of wavelength and observe chromatic variation in polarizer performance. Dichroic polarizers exhibit strong wavelength dependence due to the absorption spectrum of the dichroic dye molecules. Wire-grid polarizers exhibit weaker wavelength dependence but may show resonances at wavelengths comparable to the grid pitch. Document these wavelength-dependent effects and specify the polarizer operating wavelength range over which extinction exceeds a minimum acceptable threshold.

Construct a comprehensive uncertainty budget for the refractive index measurement conducted in Exercise 2. Identify all sources of uncertainty: angular measurement uncertainty in the incident and transmitted angles, distance measurement uncertainty for the block thickness and screen position, beam position measurement uncertainty on the screen, and systematic uncertainties from environmental effects such as thermal expansion or air refractive index variations. Propagate each uncertainty component through the refractive index extraction formula using standard uncertainty propagation techniques. Sum the contributions in quadrature to obtain the total combined uncertainty. Compare the combined uncertainty to the standard deviation of the fitted refractive index parameter extracted from the nonlinear regression. If they agree, the uncertainty budget is validated. If the fitted uncertainty is larger, unaccounted random variations dominate. If the fitted uncertainty is smaller, the stated measurement uncertainties may be overestimated or correlated.

The following Python code block implements a Monte Carlo uncertainty propagation analysis for the refractive index measurement.

```python
import numpy as np
import matplotlib.pyplot as plt

def monte_carlo_refractive_index(theta_i, y_measured, t, D, 
                                  theta_i_unc, y_unc, t_unc, D_unc, N_samples=10000):
    """
    Monte Carlo uncertainty propagation for refractive index extraction.
    
    Parameters:
    theta_i: incident angle (degrees)
    y_measured: measured deflection (meters)
    t: block thickness (meters)
    D: screen distance (meters)
    theta_i_unc: angular uncertainty (degrees)
    y_unc: deflection measurement uncertainty (meters)
    t_unc: thickness uncertainty (meters)
    D_unc: distance uncertainty (meters)
    N_samples: number of Monte Carlo samples
    
    Returns:
    n_samples: array of refractive index samples
    n_mean: mean refractive index
    n_std: standard deviation (uncertainty)
    """
    # Generate random samples from normal distributions
    theta_i_samples = np.random.normal(theta_i, theta_i_unc, N_samples)
    y_samples = np.random.normal(y_measured, y_unc, N_samples)
    t_samples = np.random.normal(t, t_unc, N_samples)
    D_samples = np.random.normal(D, D_unc, N_samples)
    
    # Compute refractive index for each sample
    n_samples = np.zeros(N_samples)
    
    for i in range(N_samples):
        # Numerical inversion: find n such that ray_trace_deflection matches y
        # Use simple search over plausible n range
        n_test = np.linspace(1.3, 1.8, 500)
        y_test = np.array([ray_trace_deflection(theta_i_samples[i], n, 
                                                  t_samples[i], D_samples[i]) 
                          for n in n_test])
        
        # Find n that minimizes |y_test - y_sample|
        idx = np.argmin(np.abs(y_test - y_samples[i]))
        n_samples[i] = n_test[idx]
    
    n_mean = np.mean(n_samples)
    n_std = np.std(n_samples)
    
    return n_samples, n_mean, n_std

# Example: uncertainty analysis for one measurement point
theta_i = 40.0  # degrees
y_measured = 9.1e-3  # meters
t = 20e-3  # meters
D = 0.80  # meters

# Uncertainty estimates
theta_i_unc = 0.5  # degrees (protractor resolution)
y_unc = 0.3e-3  # meters (ruler resolution)
t_unc = 0.1e-3  # meters (caliper resolution)
D_unc = 2e-3  # meters (ruler resolution)

print("Running Monte Carlo uncertainty propagation...")
print(f"Number of samples: 10000")
print(f"Input uncertainties:")
print(f"  θᵢ: {theta_i} ± {theta_i_unc} degrees")
print(f"  y: {y_measured * 1e3:.2f} ± {y_unc * 1e3:.2f} mm")
print(f"  t: {t * 1e3:.2f} ± {t_unc * 1e3:.2f} mm")
print(f"  D: {D * 1e2:.1f} ± {D_unc * 1e2:.2f} cm")

n_samples, n_mean, n_std = monte_carlo_refractive_index(
    theta_i, y_measured, t, D, theta_i_unc, y_unc, t_unc, D_unc
)

print(f"\nResult:")
print(f"  Refractive index: {n_mean:.4f} ± {n_std:.4f}")

# Plot histogram of refractive index distribution
plt.figure(figsize=(10, 6))
plt.hist(n_samples, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='black')
plt.axvline(n_mean, color='red', linestyle='--', linewidth=2, label=f'Mean = {n_mean:.4f}')
plt.axvline(n_mean - n_std, color='orange', linestyle=':', linewidth=2)
plt.axvline(n_mean + n_std, color='orange', linestyle=':', linewidth=2, 
            label=f'±1σ = {n_std:.4f}')
plt.xlabel('Refractive Index n', fontsize=12)
plt.ylabel('Probability Density', fontsize=12)
plt.title('Monte Carlo Uncertainty Distribution', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('monte_carlo_uncertainty.png', dpi=300)
plt.show()

# Compute sensitivity coefficients (partial derivatives)
delta = 1e-6
dn_dtheta = (ray_trace_deflection(theta_i + delta, n_mean, t, D) - 
             ray_trace_deflection(theta_i - delta, n_mean, t, D)) / (2 * delta)
dn_dy = 1.0 / dn_dtheta  # approximate inverse sensitivity

print(f"\nSensitivity analysis:")
print(f"  ∂y/∂θᵢ ≈ {dn_dtheta * 1e3:.4f} mm/degree")
print(f"  Angular precision needed for 0.01 n accuracy: {0.01 * abs(dn_dy * dn_dtheta):.3f} degrees")
```

Execute this Monte Carlo simulation to visualize how measurement uncertainties propagate through the nonlinear ray-tracing calculation. The histogram displays the probability distribution of the inferred refractive index, accounting for all input uncertainties simultaneously. The standard deviation of this distribution represents the combined uncertainty, which should match the uncertainty derived from analytical error propagation formulae for validation.

The sensitivity analysis quantifies how much each input uncertainty contributes to the final uncertainty in the refractive index. If angular uncertainty dominates, improve angular measurement precision by upgrading the rotational stage encoder. If deflection uncertainty dominates, increase the screen distance to amplify the transverse displacement signal. This targeted approach to uncertainty reduction maximizes measurement precision with minimal equipment investment.

## Laboratory Cheat Sheet & Metric Verification Guide

This reference section consolidates critical measurement protocols, data analysis algorithms, and diagnostic commands for rapid execution during laboratory sessions. Refer to this cheat sheet when verifying optical component specifications, troubleshooting measurement anomalies, or validating computational analysis pipelines.

**Single-Slit Diffraction Wavelength Extraction:**
Measure the distance L from slit to screen with millimeter precision. Measure the slit width a using a calibrated micrometer or accept the manufacturer's certified value. Identify the position y_m of the m-th intensity minimum by locating the dark fringes symmetrically positioned on both sides of the central maximum. For small angles, the wavelength equals a times y_m divided by m times L. For angles exceeding 10 degrees, compute the exact sine function: lambda equals a times sine of arctangent of y_m divided by L, divided by m. Plot y_m versus diffraction order m on a linear scale and verify that the data fall on a straight line through the origin with slope L lambda divided by a. Extract lambda from the slope using linear regression with uncertainty propagated from the position measurement standard deviation.

**Refractive Index Extraction via Beam Deflection:**
Mount the glass block on a precision rotary stage with angular encoder resolution below 0.5 degrees. Measure the block thickness t using a digital caliper with resolution 0.01 millimeters. Position the screen at distance D between 50 and 100 centimeters from the block exit face. Sweep the incident angle from 0 to 60 degrees in 5-degree increments. At each angle, record the transverse beam deflection y relative to the undeflected baseline. Implement the exact ray-tracing function that applies Snell's law at both block faces and accounts for the geometric path through the block. Fit the measured deflection data to this model using nonlinear least-squares regression with the refractive index as the single free parameter. Verify that the fitted index lies between 1.4 and 1.9 for typical optical glasses. Compute the reduced chi-squared statistic and confirm that it lies between 0.5 and 2.0, indicating good model agreement without over-fitting.

**Polarizer Extinction Ratio Measurement:**
Align the polarizer and analyzer transmission axes parallel to achieve maximum transmitted intensity I_max. Rotate the analyzer to the crossed configuration at 90 degrees relative to the polarizer. Measure the minimum transmitted intensity I_min with the photodetector shielded from ambient light. The extinction ratio equals I_max divided by I_min. Convert to decibels using 10 times logarithm base 10 of the ratio. High-quality calcite polarizers achieve 50 dB or greater. Film polarizers typically achieve 20 to 30 dB. If the measured extinction is worse than expected, check for angular misalignment, surface contamination, or stray reflections entering the detector. Verify detector linearity by measuring intensity at several power levels and confirming proportionality. If the detector saturates at high intensity, attenuate the beam using neutral density filters and re-scale the measured values.

**Malus Law Verification and Correction:**
Record transmitted intensity versus analyzer angle in 10-degree steps over a full 360-degree rotation. Plot intensity versus angle and overlay the ideal Malus law curve I equals I_max times cosine-squared theta. If the data exhibit non-zero intensity at the 90-degree and 270-degree crossed positions, fit the corrected model I equals I_offset plus I_max minus I_offset times cosine-squared of theta minus phase. Extract the extinction offset I_offset and compute the extinction ratio. Inspect residuals for systematic deviations indicating depolarization, beam ellipticity, or analyzer angle calibration error. Repeat the measurement with a quarter-wave plate inserted between the polarizers to convert linear polarization to circular and verify that the transmitted intensity becomes independent of analyzer angle, confirming circular polarization.

**Python Environment Verification:**
Before executing any data analysis script, verify that NumPy, SciPy, and Matplotlib are installed and functional. Open a terminal and run the command python -c 'import numpy; print(numpy.__version__)' to confirm NumPy availability and print its version. Repeat for SciPy using python -c 'import scipy; print(scipy.__version__)' and Matplotlib using python -c 'import matplotlib; print(matplotlib.__version__)'. The minimum required versions are NumPy 1.20, SciPy 1.9, and Matplotlib 3.5. If any package is missing, install it using pip install numpy scipy matplotlib. On systems with both Python 2 and Python 3 installed, use python3 and pip3 explicitly to target the Python 3 environment.

**Data File Structure and Import:**
Organize all experimental data in plain-text comma-separated-value (CSV) files with column headers specifying physical quantities and units. Use descriptive filenames encoding the measurement type, date, and session identifier, for example single_slit_diffraction_2025-01-15.csv. In Python, import data using NumPy's loadtxt or genfromtxt functions with the delimiter argument set to comma and the skip_header argument set to 1 to ignore the header row. Example: data equals numpy.loadtxt('measurement.csv', delimiter equals comma, skip underscore header equals 1). Extract individual columns using array slicing: theta equals data colon comma 0 extracts the first column, intensity equals data colon comma 1 extracts the second column. Verify that the imported arrays have the expected length and that values lie within physically reasonable ranges before proceeding to analysis.

**Curve Fitting Best Practices:**
When performing nonlinear least-squares fitting using scipy.optimize.curve_fit, provide initial parameter guesses close to the expected values to ensure convergence to the global minimum rather than a local minimum. Include the sigma argument specifying the measurement uncertainty for each data point to enable weighted fitting and compute meaningful parameter uncertainties. Set the absolute_sigma argument to True to interpret the sigma values as absolute uncertainties rather than relative weights. After fitting, extract the covariance matrix pcov and compute parameter uncertainties as the square root of the diagonal elements. Verify that the uncertainties are physically reasonable and not absurdly small, which would indicate numerical instability. Compute the chi-squared statistic and reduced chi-squared to assess goodness-of-fit. A reduced chi-squared near unity indicates that the model and uncertainties are consistent. Values much less than unity suggest overestimated uncertainties; values much greater than unity suggest model inadequacy or underestimated uncertainties.

**Residual Analysis Procedure:**
After fitting a model to experimental data, compute residuals as the difference between measured values and model predictions. Plot residuals versus the independent variable to visualize systematic deviations. Randomly distributed residuals with zero mean indicate good model agreement. Systematic trends, such as parabolic curvature or sinusoidal oscillations, indicate missing physics or incorrect functional form. Residuals that increase in magnitude with the independent variable suggest heteroscedastic uncertainties or nonlinear effects not captured by the model. Quantify residual magnitude by computing the root-mean-square residual and comparing it to the stated measurement uncertainty. If the RMS residual exceeds the uncertainty by a factor of two or more, re-examine the measurement procedure and uncertainty estimates.

**Uncertainty Propagation Formulae:**
For a derived quantity Q that depends on measured quantities x, y, z through a function Q equals f of x comma y comma z, the uncertainty in Q is given by the quadrature sum of partial derivative contributions. The formula is sigma Q squared equals the sum over all variables of the partial derivative of f with respect to that variable squared times the uncertainty in that variable squared. For uncorrelated uncertainties, compute each partial derivative numerically or analytically, multiply by the corresponding uncertainty, square the result, sum the contributions, and take the square root. For example, the refractive index extracted from Snell's law n equals sine theta i divided by sine theta r has uncertainty sigma n equals square root of cosine theta i divided by sine theta r squared times sigma theta i squared plus sine theta i times cosine theta r divided by sine theta r squared squared times sigma theta r squared.

**Monte Carlo Uncertainty Propagation:**
When analytical uncertainty propagation becomes intractable due to complex functional relationships or numerical inversion procedures, use Monte Carlo simulation to propagate uncertainties. Generate a large sample of input parameter sets, with each parameter drawn from a normal distribution centered on its measured value with standard deviation equal to its uncertainty. For each input sample, compute the derived quantity using the full computational model. Collect the ensemble of derived quantity values and compute the sample mean and standard deviation. The standard deviation represents the propagated uncertainty. Visualize the distribution using a histogram to detect non-Gaussian shapes indicating nonlinear sensitivity or asymmetric uncertainty. A sample size of 10,000 provides uncertainty estimates accurate to a few percent; increase to 100,000 for high-precision applications.

**Instrument Calibration Intervals:**
Recalibrate all measurement instruments at the beginning of each laboratory session or whenever an instrument is moved, adjusted, or subjected to mechanical shock. Translation stages require calibration of the position encoder against a traceable length standard such as a gauge block or optical interferometer. Rotary stages require angular calibration against a precision angle gauge or autocollimator. Photodetectors require responsivity calibration against a traceable optical power standard. If calibration standards are unavailable, perform cross-checks by measuring known reference samples or repeating measurements with independent instruments. Document all calibration results in the laboratory notebook with timestamps and traceability information.

**Common Failure Modes and Diagnostics:**
If measured diffraction or interference patterns exhibit low contrast or washed-out fringes, the laser beam may be diverging or contaminated with multiple transverse modes. Check beam collimation using a shear plate interferometer or beam profiler. If the beam diameter increases significantly over a distance of one meter, insert a spatial filter consisting of a microscope objective and pinhole to select only the fundamental Gaussian mode. If measured intensities fluctuate randomly during data acquisition, the laser power may be unstable or the photodetector may have excessive noise. Monitor the laser output with a separate power meter to verify stability better than 1 percent over the measurement interval. Shield the photodetector from electrical noise by using coaxial cables and grounding the instrument chassis. If fitted model parameters differ significantly from literature values despite careful measurement technique, the optical components may not meet specifications. Verify lens focal lengths by measuring image positions at multiple object distances. Verify polarizer extinction by measuring minimum transmission with high-quality calibrated detectors. Verify glass refractive index using an Abbe refractometer or independent prism minimum-deviation measurement.

**Measurement Reporting Standards:**
All experimental results must be reported with explicit uncertainties expressed to the same number of decimal places as the result itself. Use the plus-minus notation to indicate uncertainty, for example n equals 1.523 plus-minus 0.004. When reporting uncertainties, use one or two significant figures: 0.004 or 0.0037, not 0.003729. State whether the reported uncertainty represents one standard deviation, the standard error of the mean, or a confidence interval at a specified confidence level. Include all relevant experimental details: instrument models, measurement conditions, environmental parameters such as temperature and humidity, and any calibration corrections applied. Provide plots with clearly labeled axes including units, error bars on data points, and legends distinguishing experimental data from theoretical predictions. Archive raw data files and analysis scripts to enable reproduction and verification by independent investigators.
