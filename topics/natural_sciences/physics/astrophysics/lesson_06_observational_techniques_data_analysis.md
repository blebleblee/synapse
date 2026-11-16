# Lesson 6: Observational Techniques, Data Analysis

## 1. First-Principles Intuition & Invariants

The observable universe reveals itself through electromagnetic radiation, gravitational perturbations, and particle fluxes that have traversed cosmological distances before reaching our detectors. Every photon captured by a telescope, every spectral line recorded by a spectrograph, and every interference fringe measured by a baseline array encodes physical information about its source—temperature, composition, velocity, distance, and the geometry of spacetime itself. Astrophysical observation is fundamentally an inverse problem: we receive integrated signals from distant sources and must disentangle the astrophysical parameters that produced them, accounting for instrumental response functions, atmospheric absorption, interstellar extinction, and cosmological effects that modify the signal during propagation.

The theoretical foundation of astrophysical measurement rests on the principle that photons propagate through spacetime carrying conserved quantities. In the absence of scattering or absorption, photon number is conserved along geodesics, and the specific intensity $I_\nu$ (energy per unit time, per unit area, per unit solid angle, per unit frequency) satisfies the radiative transfer equation. For a ray propagating through a medium with absorption coefficient $\kappa_\nu$ and emission coefficient $j_\nu$, the change in specific intensity along path element $ds$ follows:

$$\frac{dI_\nu}{ds} = -\kappa_\nu I_\nu + j_\nu$$

When thermal equilibrium prevails, the source function $S_\nu = j_\nu / \kappa_\nu$ equals the Planck function $B_\nu(T)$, which encodes blackbody radiation at temperature $T$. This establishes the fundamental connection between measured flux and source physics. In the optically thin limit where $\tau_\nu = \int \kappa_\nu ds \ll 1$, we observe emission directly proportional to the emission coefficient integrated along the line of sight. In the optically thick regime where $\tau_\nu \gg 1$, we observe the surface brightness corresponding to the blackbody temperature at the photosphere where $\tau_\nu \approx 1$.

The wavelength-dependent response of astronomical detectors must be calibrated against standard sources to convert instrumental counts into absolute flux units. The fundamental flux unit in optical and infrared astronomy is the jansky, defined as $1 \text{ Jy} = 10^{-26} \text{ W m}^{-2} \text{ Hz}^{-1}$, though stellar magnitudes remain the dominant photometric system. The apparent magnitude $m$ of a source relates to its observed flux $F$ through the logarithmic relation:

$$m = -2.5 \log_{10}\left(\frac{F}{F_0}\right)$$

where $F_0$ is the zero-point flux defining magnitude zero in a given photometric bandpass. The absolute magnitude $M$ represents the apparent magnitude the source would have at a standard distance of $10$ parsecs. The distance modulus $(m - M)$ directly encodes luminosity distance $d_L$ in parsecs through:

$$m - M = 5 \log_{10}\left(\frac{d_L}{10 \text{ pc}}\right)$$

This relation forms the foundation of the cosmic distance ladder, whereby distances to progressively more remote objects are calibrated through a hierarchical chain of standard candles and distance indicators.

Spectroscopy decomposes the integrated flux into its wavelength-dependent components, revealing absorption and emission features that encode atomic and molecular physics. When an atom transitions between energy levels $E_i$ and $E_f$, it absorbs or emits a photon with frequency $\nu = (E_f - E_i)/h$, where $h$ is Planck's constant. The quantum mechanical selection rules governing allowed transitions produce characteristic spectral signatures for each element. Hydrogen, with its simple single-electron structure, exhibits the Lyman series (transitions to $n=1$), Balmer series (transitions to $n=2$), and higher series following the Rydberg formula:

$$\frac{1}{\lambda} = R_H \left(\frac{1}{n_f^2} - \frac{1}{n_i^2}\right)$$

where $R_H = 1.097 \times 10^7 \text{ m}^{-1}$ is the Rydberg constant. The Doppler shift of these spectral lines encodes radial velocity through the relativistic relation $\lambda_{\text{obs}}/\lambda_{\text{rest}} = \sqrt{(1+\beta)/(1-\beta)}$ where $\beta = v/c$. For cosmological sources, the redshift $z = (\lambda_{\text{obs}} - \lambda_{\text{rest}})/\lambda_{\text{rest}}$ additionally encodes the expansion of spacetime between emission and observation.

Interferometry exploits the wave nature of light to achieve angular resolution far exceeding what a single telescope aperture can provide. When two telescopes separated by baseline vector $\vec{B}$ observe the same source, the electric field amplitude at each telescope produces an interference pattern encoding the spatial structure of the source. The visibility function $V(\vec{u})$ measured at spatial frequency $\vec{u} = \vec{B}/\lambda$ is the Fourier transform of the sky brightness distribution $I(\vec{\theta})$:

$$V(\vec{u}) = \int I(\vec{\theta}) e^{-2\pi i \vec{u} \cdot \vec{\theta}} d^2\theta$$

This van Cittert-Zernike theorem establishes that an interferometer samples the Fourier components of the sky brightness, with longer baselines probing finer angular scales. Synthesis imaging reconstructs the sky brightness distribution by inverting the Fourier relation, combining measurements from multiple baselines and observing times to fill the $uv$-plane coverage.

Gravitational lensing provides a geometrical probe of mass distribution through the deflection of light by spacetime curvature. The deflection angle $\vec{\alpha}$ for a light ray passing impact parameter $\vec{\xi}$ from a mass distribution with projected surface density $\Sigma(\vec{\xi})$ follows from the thin-lens approximation:

$$\vec{\alpha}(\vec{\xi}) = \frac{4G}{c^2} \int \frac{(\vec{\xi} - \vec{\xi}')}{|\vec{\xi} - \vec{\xi}'|^2} \Sigma(\vec{\xi}') d^2\xi'$$

For a point mass $M$, this reduces to the Einstein deflection angle $\alpha = 4GM/(c^2 b)$ where $b$ is the impact parameter. Strong lensing produces multiple images, Einstein rings, and arcs when the source, lens, and observer are nearly aligned. Weak lensing induces coherent tangential shear patterns around mass concentrations, detectable statistically by correlating the shapes of background galaxies.

## 2. Core Architecture & Mechanics

### Photometric Systems and Magnitude Calibration

The execution of precise stellar photometry requires constructing a calibrated magnitude system that spans the instrumental bandpass and corrects for atmospheric extinction, detector quantum efficiency variations, and intrapixel sensitivity variations. The Johnson-Cousins $UBVRI$ system defines five standard passbands centered at approximately $365$ nm (U, ultraviolet), $445$ nm (B, blue), $551$ nm (V, visual), $658$ nm (R, red), and $806$ nm (I, infrared). Each bandpass is defined by the transmission function $S(\lambda)$ combining telescope optics, filter transmission, and detector quantum efficiency. The instrumental magnitude $m_{\text{inst}}$ measured from aperture photometry around a stellar point spread function (PSF) relates to the calibrated magnitude through:

$$m_{\text{calib}} = m_{\text{inst}} - k_X \cdot X + ZP$$

where $k_X$ is the extinction coefficient in magnitudes per airmass, $X = \sec(z)$ is the airmass at zenith angle $z$, and $ZP$ is the photometric zero-point in magnitudes. The extinction coefficient accounts for Rayleigh scattering, aerosol absorption, and molecular absorption bands (particularly ozone at UV wavelengths, water vapor in near-infrared bands). Determining $k_X$ requires observing standard stars at multiple airmasses throughout the night and fitting the linear relation between observed magnitude and airmass.

The zero-point $ZP$ calibrates the instrumental system to the standard magnitude scale by observing stars with known magnitudes from photometric catalogs. For differential photometry, where only relative magnitudes within a field matter, the zero-point cancels and extinction remains the primary correction. For absolute photometry required in distance determinations, the zero-point must be determined nightly to account for variations in atmospheric transparency and detector sensitivity.

Color indices constructed from magnitude differences in different bands encode intrinsic stellar properties while canceling distance-dependent terms. The $(B-V)$ color index correlates with effective temperature through the blackbody spectrum shape. For a blackbody, the Wien displacement law $\lambda_{\text{max}} T = 2.898 \times 10^{-3} \text{ m K}$ shifts the peak emission blueward as temperature increases, producing bluer $(B-V)$ colors for hotter stars. Interstellar extinction reddens starlight preferentially at shorter wavelengths, adding an extinction correction to the observed color:

$$(B-V)_0 = (B-V)_{\text{obs}} - E(B-V)$$

where $E(B-V)$ is the color excess and $(B-V)_0$ is the intrinsic color. The extinction in magnitudes scales approximately as $A_V \approx 3.1 \, E(B-V)$ for typical interstellar dust in the Milky Way.

### Spectroscopic Reduction Pipeline

Astronomical spectroscopy transforms a two-dimensional CCD image into a calibrated flux-versus-wavelength spectrum through a multi-stage reduction pipeline. The raw image contains the spectrum dispersed along the spatial axis (typically horizontal), with the slit direction along the perpendicular axis (vertical). The reduction workflow proceeds through bias subtraction, flat-fielding, cosmic ray rejection, wavelength calibration, sky subtraction, spectral extraction, and flux calibration.

Bias frames captured with zero exposure time characterize the detector readout offset and are subtracted from all science frames to remove this additive contribution. Flat-field frames taken of a uniformly illuminated source (twilight sky or internal lamp) map the pixel-to-pixel sensitivity variations and are divided into the science frames after bias subtraction. The normalized flat-field $F_{\text{norm}}(\lambda, y) = F(\lambda, y) / \langle F(\lambda, y) \rangle_y$ corrects for both variations along the dispersion direction (wavelength-dependent sensitivity) and spatial direction (slit illumination non-uniformity).

Wavelength calibration establishes the mapping between detector pixel coordinate $x$ and wavelength $\lambda$ by observing emission-line calibration lamps (typically ThAr, ThNe, or Xe arc lamps) that produce sharp lines at precisely known laboratory wavelengths. The dispersion relation is fit to a polynomial:

$$\lambda(x) = \sum_{n=0}^{N} a_n x^n$$

with coefficients $a_n$ determined by identifying emission lines in the calibration spectrum and minimizing residuals. For echelle spectrographs that produce multiple spectral orders, each order requires independent wavelength calibration. The wavelength solution accuracy directly limits radial velocity precision; modern stabilized spectrographs achieve wavelength calibration stability at the meter-per-second level through simultaneous ThAr or laser frequency comb calibration.

Sky subtraction removes the additive contribution from atmospheric emission lines and scattered continuum light. For long-slit spectroscopy, sky regions offset from the target along the slit provide direct measurement of the sky spectrum at the same wavelength. The sky spectrum $S(\lambda, y_{\text{sky}})$ is interpolated to the target position and subtracted from the target spectrum. For fiber-fed spectrographs, dedicated sky fibers positioned away from the target measure the sky contribution. Night sky emission is dominated by OH airglow lines in the near-infrared (producing a forest of narrow emission features between $0.7$ and $2.5$ μm) and sodium D-line emission at $589$ nm.

Spectral extraction integrates the flux within an aperture centered on the target trace after sky subtraction. Optimal extraction weights each spatial pixel by the PSF profile to maximize signal-to-noise ratio while minimizing contamination from neighboring sources:

$$f(\lambda) = \frac{\sum_y P(\lambda, y) \, [S(\lambda, y) - B(\lambda, y)] / \sigma^2(\lambda, y)}{\sum_y P^2(\lambda, y) / \sigma^2(\lambda, y)}$$

where $P(\lambda, y)$ is the normalized spatial PSF profile, $S(\lambda, y)$ is the sky-subtracted image, $B(\lambda, y)$ is any residual background, and $\sigma^2(\lambda, y)$ is the variance at each pixel. This optimal extraction approach was developed by Keith Horne and provides superior signal-to-noise compared to simple aperture summation, particularly for faint sources where read noise dominates.

Flux calibration transforms the extracted spectrum from instrumental counts to physical flux units by observing spectrophotometric standard stars with known absolute flux distributions. The instrumental response function $R(\lambda)$ relates observed counts $C(\lambda)$ to true flux $F(\lambda)$ through:

$$C(\lambda) = R(\lambda) \, F(\lambda) \, t_{\text{exp}}$$

where $t_{\text{exp}}$ is the exposure time. Observing a standard star with known flux $F_{\text{std}}(\lambda)$ and measured counts $C_{\text{std}}(\lambda)$ determines the response function $R(\lambda) = C_{\text{std}}(\lambda) / [F_{\text{std}}(\lambda) \, t_{\text{exp}}]$, which is then applied to calibrate science targets. Telluric absorption features from atmospheric water vapor and molecular oxygen appear as broad absorption bands superimposed on the stellar spectrum and must be corrected by dividing by the spectrum of a rapidly rotating early-type star (which has few intrinsic features) observed at similar airmass.

### Interferometric Visibility Measurement

Radio interferometry and optical/infrared interferometry measure the complex visibility function by cross-correlating signals from spatially separated telescopes. At radio frequencies, the voltage signals $V_1(t)$ and $V_2(t)$ from two antennas separated by baseline $\vec{B}$ are digitized and cross-multiplied in a correlator to produce the visibility:

$$\mathcal{V}_{12}(\tau) = \langle V_1(t) \, V_2^*(t - \tau) \rangle_t$$

where $\tau = \vec{B} \cdot \hat{s} / c$ is the geometric delay for a source in direction $\hat{s}$. The correlator output is integrated over time to achieve adequate signal-to-noise, with integration times ranging from seconds (for bright sources) to hours (for faint sources). The visibility amplitude $|\mathcal{V}_{12}|$ encodes the degree of spatial coherence, ranging from unity for an unresolved point source to near-zero for a fully resolved extended source. The visibility phase $\arg(\mathcal{V}_{12})$ encodes the source position offset from the phase tracking center.

For optical and infrared interferometry, atmospheric turbulence introduces rapidly varying phase errors that must be corrected on timescales shorter than the atmospheric coherence time (typically $10-50$ ms for visible wavelengths). The complex visibility is measured by combining beams from multiple telescopes in an optical beam combiner and detecting interference fringes. The VLTI (Very Large Telescope Interferometer) and CHARA (Center for High Angular Resolution Astronomy) arrays use delay lines to compensate for geometric path differences and achieve coherent beam combination across baselines up to hundreds of meters.

The closure phase technique circumvents atmospheric phase corruption by forming phase combinations that cancel atmospheric contributions. For three telescopes forming baselines $\mathcal{V}_{12}$, $\mathcal{V}_{23}$, and $\mathcal{V}_{31}$, the closure phase:

$$\Phi_{\text{closure}} = \arg(\mathcal{V}_{12}) + \arg(\mathcal{V}_{23}) + \arg(\mathcal{V}_{31})$$

is independent of antenna-based phase errors and depends only on source structure. Closure phases are particularly powerful for detecting asymmetries in stellar photospheres, jets in active galactic nuclei, and companions in binary systems.

### Gravitational Lensing Analysis

Weak gravitational lensing analysis measures the coherent distortion of background galaxy shapes by foreground mass distributions. Each background galaxy image is characterized by an ellipticity $\vec{\epsilon}$ that receives contributions from both intrinsic ellipticity $\vec{\epsilon}_{\text{int}}$ (the galaxy's true shape) and lensing-induced shear $\vec{\gamma}$. The observed ellipticity relates to the convergence $\kappa$ and shear through:

$$\vec{\epsilon}_{\text{obs}} = \frac{\vec{\epsilon}_{\text{int}} + \vec{g}}{1 + g^* \epsilon_{\text{int}}}$$

where $\vec{g} = (\gamma_1 + i\gamma_2)/(1-\kappa)$ is the reduced shear. For weak lensing where $|\vec{g}| \ll 1$, this simplifies to $\vec{\epsilon}_{\text{obs}} \approx \vec{\epsilon}_{\text{int}} + \vec{g}$. Since intrinsic galaxy orientations are randomly distributed, averaging the observed ellipticities over many background galaxies within an angular bin isolates the shear signal:

$$\langle \vec{\epsilon}_{\text{obs}} \rangle \approx \vec{g}$$

The tangential shear component $\gamma_t$ around a mass concentration produces a coherent tangential alignment of background galaxies. For a circularly symmetric lens, the tangential shear profile relates to the projected surface mass density through:

$$\gamma_t(\theta) = \bar{\kappa}(<\theta) - \kappa(\theta)$$

where $\bar{\kappa}(<\theta)$ is the mean convergence within radius $\theta$. This relation allows reconstruction of the mass profile from the measured shear profile.

Practical weak lensing analysis requires careful correction for PSF anisotropy, which introduces spurious shape correlations that can dominate the lensing signal. The PSF ellipticity at each galaxy position is modeled from the observed shapes of unsaturated stars across the field, and this PSF contribution is deconvolved from the galaxy shapes through PSF correction algorithms. The GREAT3 challenge demonstrated that current methods achieve PSF correction accuracy of $|\Delta e| \sim 10^{-3}$ per galaxy, though this remains the limiting systematic for next-generation surveys.

Strong gravitational lensing produces multiple images of background sources when the alignment is sufficiently close. The lens equation:

$$\vec{\beta} = \vec{\theta} - \vec{\alpha}(\vec{\theta})$$

relates the true source position $\vec{\beta}$ to the observed image position $\vec{\theta}$ through the deflection angle $\vec{\alpha}(\vec{\theta})$. For a point mass $M$ at the lens position, the Einstein radius $\theta_E$ defines the characteristic angular scale:

$$\theta_E = \sqrt{\frac{4GM}{c^2} \frac{D_{LS}}{D_L D_S}}$$

where $D_L$, $D_S$, and $D_{LS}$ are the angular diameter distances to the lens, source, and from lens to source respectively. Galaxies typically have Einstein radii of order $1$ arcsecond for background sources at cosmological distances. Time delays between multiple images encode the Hubble constant through:

$$\Delta t = \frac{1 + z_L}{c} \frac{D_L D_S}{D_{LS}} \Delta \phi$$

where $\Delta \phi$ is the Fermat potential difference between image positions. This time-delay cosmography provides an independent $H_0$ measurement reaching few-percent precision for well-modeled lens systems.

### Cosmic Distance Ladder Construction

The cosmic distance ladder establishes a hierarchical chain of distance measurements extending from nearby parallax distances to cosmological distances beyond one gigaparsec. The foundation rests on trigonometric parallax, where the annual apparent motion of nearby stars against the distant background encodes their distance through $d = 1/p$ where parallax $p$ is measured in arcseconds and distance in parsecs. The Gaia mission has measured parallaxes with microarcsecond precision for over one billion stars, establishing the zero-point of the distance scale.

Cepheid variable stars provide the first rung above direct parallax measurements. These pulsating supergiants exhibit a tight period-luminosity relation discovered by Henrietta Leavitt: longer-period Cepheids are intrinsically more luminous. The relation in the $V$-band takes the form:

$$M_V = -2.43 (\log_{10} P - 1.0) - 4.05$$

where $P$ is the pulsation period in days and $M_V$ is the absolute magnitude. Measuring the apparent magnitude and period of a Cepheid immediately yields its distance through the distance modulus. This technique extends distance measurements to tens of megaparsecs, reaching nearby galaxy groups. The Hubble Space Telescope Key Project measured Cepheid distances to nineteen galaxies to calibrate the Hubble constant.

Type Ia supernovae serve as standardizable candles extending to cosmological distances beyond one gigaparsec. These thermonuclear explosions of carbon-oxygen white dwarfs that accrete mass to the Chandrasekhar limit produce remarkably uniform peak luminosities. The intrinsic scatter in peak absolute magnitude is $\sigma_M \approx 0.15$ mag, corresponding to distance uncertainties of seven percent. The Phillips relation further reduces scatter by correlating peak luminosity with light curve decline rate: faster-declining supernovae are intrinsically fainter. After this correction, the standardized distance modulus scatter decreases to $\sigma_M \approx 0.12$ mag.

The Hubble diagram plots distance modulus against redshift for Type Ia supernovae:

$$\mu = m - M = 5 \log_{10} d_L + 25$$

where the luminosity distance $d_L$ depends on the cosmological parameters $H_0$, $\Omega_m$, and $\Omega_\Lambda$. For a flat universe with matter density $\Omega_m$ and dark energy density $\Omega_\Lambda = 1 - \Omega_m$, the luminosity distance follows:

$$d_L(z) = \frac{c(1+z)}{H_0} \int_0^z \frac{dz'}{\sqrt{\Omega_m (1+z')^3 + \Omega_\Lambda}}$$

Fitting this relation to observed supernova distances determines the cosmological parameters. The accelerating expansion of the universe was discovered through this method when supernova observations at $z \sim 0.5-1.0$ appeared systematically fainter than expected for a decelerating universe, implying $\Omega_\Lambda \approx 0.7$.

## 3. High-Performance Optimization & Failure Modes

### Systematic Error Mitigation in Photometry

Achieving millimagnitude photometric precision requires controlling systematic errors that dominate the error budget beyond Poisson statistics. Atmospheric extinction variations on sub-hour timescales due to passing clouds and aerosol layers produce systematic magnitude variations that correlate across multiple stars. Differential photometry largely cancels these effects by referencing target measurements against stable comparison stars in the same field, since atmospheric variations affect all stars similarly. However, color-dependent extinction introduces residual systematics when the target and comparison stars have significantly different spectral types.

The optimal aperture radius for photometry balances two competing effects: larger apertures capture more source flux but also collect more sky background noise and suffer greater systematics from PSF variations. For a Gaussian PSF with standard deviation $\sigma_{\rm PSF}$, the optimal aperture radius is approximately $r_{\rm opt} \approx 1.4 \sigma_{\rm PSF}$ for sky-noise-limited observations. Aperture corrections account for flux falling outside the measurement aperture by measuring bright isolated stars with large apertures and comparing to the smaller apertures used for fainter sources.

Intrapixel sensitivity variations produce photometric errors when a stellar image drifts across pixels between exposures. Modern CCDs exhibit few-percent sensitivity variations between pixel centers and edges. For precision photometry, undersampled PSFs (where the PSF FWHM is comparable to the pixel size) exhibit larger sensitivity to pointing drifts. Defocusing the telescope slightly to spread the PSF over more pixels averages over intrapixel variations and improves photometric stability, though at the cost of reduced spatial resolution.

### Spectroscopic Resolution and Signal-to-Noise Optimization

The spectral resolving power $R = \lambda / \Delta\lambda$ determines the ability to resolve adjacent spectral features. For radial velocity measurements, higher resolution directly improves velocity precision by narrowing the spectral line profiles against which Doppler shifts are measured. The cross-correlation method achieves radial velocity precision approximately:

$$\sigma_v \approx \frac{c}{R \sqrt{N_{\rm photons}}}$$

where $N_{\rm photons}$ is the total number of detected photons across all spectral lines. Reaching meter-per-second precision requires $R \sim 100,000$ and signal-to-noise ratios exceeding $100$ per resolution element. The HARPS spectrograph achieves $R = 115,000$ and long-term radial velocity stability of $1$ m/s through extreme environmental control and simultaneous wavelength calibration.

Spectral resolution trades against light-gathering power: narrow slits required for high resolution reject light from the seeing disk, while wide slits accept more light but degrade resolution through geometric broadening. The throughput-resolution product is approximately conserved, so maximizing signal-to-noise for a fixed integration time requires balancing resolution against throughput. For faint sources where exposure time is limited, intermediate resolution ($R \sim 1000-5000$) often provides optimal signal-to-noise for identifying spectral features while maintaining acceptable velocity precision.

Cosmic rays produce spurious counts in CCD exposures, appearing as sharp peaks in individual pixels. For spectroscopy where the signal is dispersed across many pixels, cosmic ray rejection is critical to avoid corrupting the extracted spectrum. The standard approach splits long exposures into multiple shorter exposures and performs sigma-clipping: pixels that deviate by more than $5\sigma$ from the median of multiple exposures are rejected. However, this approach fails for single exposures of transient phenomena. L.A. Cosmic and similar algorithms identify cosmic rays by their morphological signatures—sharply peaked with steep edges—and interpolate over contaminated pixels.

### Interferometric Image Reconstruction

Reconstructing sky brightness distributions from interferometric visibilities is an ill-posed inverse problem: the number of Fourier components that must be reconstructed (one per resolution element) vastly exceeds the number of measured visibilities (one per baseline). The CLEAN algorithm iteratively deconvolves the dirty beam (the Fourier transform of the $uv$-coverage sampling function) from the observed dirty image by fitting point sources and subtracting their sidelobes. The residual after CLEAN iterations approximates the true sky brightness distribution convolved with a restoring beam (typically a Gaussian matched to the synthesized beam resolution).

Maximum entropy methods (MEM) incorporate a regularization term favoring smooth images with maximum entropy subject to consistency with the measured visibilities:

$$S = -\sum_i p_i \ln(p_i/m_i)$$

where $p_i$ is the pixel brightness, $m_i$ is a default model, and the sum is over all image pixels. The reconstructed image maximizes entropy while satisfying $\chi^2 \leq N_{\rm vis}$ where $N_{\rm vis}$ is the number of visibilities. This approach naturally interpolates between measured spatial frequencies while avoiding spurious structure in unsampled regions of the $uv$-plane.

Closure phase imaging reconstructs images from closure phases and visibility amplitudes without requiring amplitude calibration. The BSMEM algorithm uses both bispectrum phases (closure phases) and visibility amplitudes to constrain the image reconstruction. For extremely sparse arrays like VLBI networks, self-calibration iteratively refines the image and antenna gain solutions: an initial image model predicts visibilities, antenna gains are adjusted to match observed visibility amplitudes, and the improved gain solutions enable better imaging. This bootstrap procedure converges to a self-consistent image and gain solution after several iterations.

### Weak Lensing Systematic Control

Achieving the shape measurement accuracy required for weak lensing cosmology ($|\Delta e| < 10^{-3}$ per galaxy) demands unprecedented control of systematic errors. PSF anisotropy leaks into galaxy shape measurements when the PSF ellipticity varies across the field of view. Atmospheric turbulence, optical aberrations, and detector artifacts all contribute to PSF anisotropy. Modeling the PSF from stellar shapes across the field requires interpolating between stars separated by arcminutes to predict the PSF at galaxy positions. Principal component analysis decomposes the PSF variation into basis functions (typically Zernike polynomials or similar) that are fit to stellar measurements and interpolated across the field.

Galaxy shape measurement algorithms must decouple the intrinsic galaxy morphology from the PSF convolution. Moment-based methods measure ellipticity from weighted second moments of the galaxy image, then apply PSF corrections derived from the moments of PSF model. The KSB algorithm corrects for PSF convolution through a linear response approximation valid for small PSF ellipticity. Model-fitting approaches (like lensfit and im3shape) fit parametric galaxy models (Sérsic profiles) convolved with the PSF to the observed images, simultaneously constraining galaxy shape and size. These methods achieve better performance for low signal-to-noise galaxies but require careful prior choice to avoid biasing the shape distribution.

Shear calibration bias arises when the shape measurement algorithm responds non-linearly to shear. The multiplicative bias $m$ and additive bias $c$ parameterize the systematic error:

$$e_{\rm meas} = (1 + m) e_{\rm true} + c$$

Calibrating these biases requires realistic image simulations spanning the full range of galaxy morphologies, sizes, signal-to-noise ratios, and PSF properties present in the data. The GREAT3 challenge established that calibration simulations must match the data to sub-percent accuracy in the magnitude, size, and color distributions to avoid biasing cosmological parameters.

### Statistical Inference for Cosmological Parameters

Extracting cosmological parameters from observational data requires proper statistical inference accounting for measurement uncertainties, sample selection effects, and model degeneracies. Bayesian inference provides a principled framework through Bayes' theorem:

$$p(\theta | D) = \frac{p(D | \theta) p(\theta)}{p(D)}$$

where $p(\theta | D)$ is the posterior probability of parameters $\theta$ given data $D$, $p(D | \theta)$ is the likelihood, $p(\theta)$ is the prior, and $p(D)$ is the evidence. For cosmological parameter estimation from supernova distances, the likelihood assumes Gaussian errors on distance moduli:

$$p(D | \theta) = \prod_i \frac{1}{\sqrt{2\pi \sigma_i^2}} \exp\left[-\frac{(\mu_i^{\rm obs} - \mu_i^{\rm theory}(\theta))^2}{2\sigma_i^2}\right]$$

where $\mu_i^{\rm obs}$ are the observed distance moduli, $\mu_i^{\rm theory}(\theta)$ are the predictions for cosmological parameters $\theta$, and $\sigma_i$ are the measurement uncertainties. Markov Chain Monte Carlo (MCMC) sampling explores the posterior distribution by constructing a chain of parameter samples that asymptotically samples from $p(\theta | D)$. The Metropolis-Hastings algorithm proposes parameter updates and accepts or rejects them based on the likelihood ratio, ensuring detailed balance. Convergence diagnostics like the Gelman-Rubin statistic verify that multiple chains have converged to the same posterior distribution.

For complex hierarchical models with many parameters, Hamiltonian Monte Carlo (HMC) provides efficient sampling by using gradient information to propose distant moves that maintain high acceptance rates. The No U-Turn Sampler (NUTS) automatically tunes the trajectory length in HMC, eliminating manual tuning of algorithm parameters. These advanced sampling methods enable Bayesian analysis of weak lensing surveys with hundreds of millions of galaxies and thousands of nuisance parameters describing systematic uncertainties.

Model comparison quantifies whether additional model complexity is justified by improved fit to the data through the Bayesian evidence ratio or Bayes factor:

$$B_{12} = \frac{p(D | M_1)}{p(D | M_2)} = \frac{\int p(D | \theta_1, M_1) p(\theta_1 | M_1) d\theta_1}{\int p(D | \theta_2, M_2) p(\theta_2 | M_2) d\theta_2}$$

Values $B_{12} > 10$ indicate strong evidence favoring model $M_1$ over $M_2$. Computing the evidence integral requires sampling the full prior volume, which nested sampling algorithms achieve efficiently. Model selection guards against overfitting by penalizing model complexity through the Occam factor implicit in the evidence integral.
