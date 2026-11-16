# Lesson 01: Foundations and Invariants of Astronomy

## 1. First-Principles Intuition & Invariants

### 1.1 What Astronomy Is Actually Doing

Astronomy is the science of inferring physical reality from received electromagnetic radiation (and, more recently, gravitational waves and neutrinos). Unlike laboratory sciences, the astronomer cannot manipulate the system under study. Every measurement is a projection: a two-dimensional image on a detector encodes a three-dimensional universe, and the temporal signal arriving at a telescope left its source at some time in the past. Working backwards from detector counts to physical truth is the fundamental epistemic problem of the discipline.

This constraint forces a reliance on invariants: conserved quantities, symmetry principles, and universal constants that hold regardless of when or where in the universe a process occurs. Astronomy is therefore deeply dependent on physics being universal, an assumption that has been tested to extraordinary precision and never found wanting at any scale we can probe.

### 1.2 The Fundamental Observational Invariants

**The constancy of the speed of light.** In vacuum, electromagnetic radiation propagates at $c = 2.998 \times 10^8 \, \mathrm{m\,s^{-1}}$ regardless of the motion of source or observer. This is not merely a postulate of special relativity; it is confirmed by pulsar timing, gamma-ray burst arrival times, and the coherence of interferometric baselines. Its consequence for astronomy is that every observation is a measurement of the past: a photon from the Andromeda Galaxy ($d \approx 770 \, \mathrm{kpc}$) left its source $\approx 2.5 \times 10^6$ years ago.

**Conservation of energy and momentum.** Photon energy $E = h\nu$ is Lorentz-invariant up to a Doppler factor, and total four-momentum is conserved in every interaction. This underpins spectroscopy: atomic transitions produce photons of fixed rest-frame energy, and any shift in observed frequency directly encodes relative motion or gravitational potential.

**The inverse-square law.** For an isotropically radiating point source of luminosity $L$ at distance $d$, the flux received is:

$$F = \frac{L}{4\pi d^2}$$

This is a geometric invariant, not a physical one, but it is exact in flat space and correctable in curved spacetime. It is the foundational bridge between intrinsic source properties and observed detector signals.

**Blackbody radiation.** A body in thermal equilibrium at temperature $T$ emits radiation with a spectral energy distribution (SED) described by the Planck function:

$$B_\nu(T) = \frac{2h\nu^3}{c^2} \frac{1}{e^{h\nu/kT} - 1}$$

The total power emitted per unit area is $\sigma T^4$ (Stefan-Boltzmann), and the peak frequency satisfies $\nu_\mathrm{peak} \propto T$ (Wien displacement law). These are thermodynamic invariants: they hold for any object in local thermodynamic equilibrium regardless of composition, and they let us infer stellar temperatures directly from color.

**Gravity as geometry.** In general relativity, the spacetime interval:

$$ds^2 = g_{\mu\nu} dx^\mu dx^\nu$$

is invariant under coordinate transformations. Mass-energy curves spacetime; free particles follow geodesics. For most stellar and planetary astronomy, the Newtonian limit $g_{00} \approx 1 + 2\Phi/c^2$ is sufficient, where $\Phi$ is the gravitational potential. The regime of departure from Newtonian gravity is set by the compactness parameter $\xi = GM/rc^2$; for the Sun, $\xi_\odot \approx 2 \times 10^{-6}$, while for a neutron star $\xi \sim 0.2$.

### 1.3 Units and Scales as Physical Anchors

Astronomy spans a wider dynamic range than any other physical science. Establishing a feel for the relevant scales is prerequisite to reasoning correctly about any problem.

| Scale | Characteristic Value | Physical Anchor |
|---|---|---|
| Solar radius | $R_\odot = 6.96 \times 10^8 \, \mathrm{m}$ | Main-sequence stellar size |
| Astronomical unit | $1 \, \mathrm{AU} = 1.496 \times 10^{11} \, \mathrm{m}$ | Earth-Sun distance |
| Parsec | $1 \, \mathrm{pc} = 3.086 \times 10^{16} \, \mathrm{m}$ | Distance at 1 arcsec parallax |
| Solar luminosity | $L_\odot = 3.83 \times 10^{26} \, \mathrm{W}$ | Main-sequence radiative output |
| Solar mass | $M_\odot = 1.989 \times 10^{30} \, \mathrm{kg}$ | Stellar mass anchor |
| Hubble constant | $H_0 \approx 70 \, \mathrm{km\,s^{-1}\,Mpc^{-1}}$ | Cosmological expansion rate |

These values are not arbitrary. The parsec is defined from the trigonometric parallax method: a star at 1 pc has a parallax angle of 1 arcsecond, meaning $1 \, \mathrm{pc} = 1 \, \mathrm{AU} / \tan(1'') \approx 1 \, \mathrm{AU} / (4.848 \times 10^{-6} \, \mathrm{rad})$. Every distance ladder in astronomy ultimately roots back to this geometric foundation.

### 1.4 Dimensional Thinking: The Virial Theorem

Before deriving any detailed model, the virial theorem provides a powerful invariant constraint on gravitationally bound systems. For a system in dynamical equilibrium, the time-averaged kinetic energy $\langle K \rangle$ and potential energy $\langle U \rangle$ satisfy:

$$2\langle K \rangle + \langle U \rangle = 0$$

This follows from the virial theorem for systems with forces scaling as $r^{-2}$. Consequences:

- The total energy of a bound system is $E = \langle K \rangle + \langle U \rangle = -\langle K \rangle = \langle U \rangle / 2$. A gravitationally bound object has negative total energy.
- When a star contracts, it radiates energy and heats up. This is the negative heat capacity of gravity: losing energy increases temperature. This seems paradoxical from everyday thermodynamics but follows directly from the virial theorem.
- Cluster velocity dispersions encode total mass: $M \sim \sigma_v^2 R / G$, where $\sigma_v$ is the line-of-sight velocity dispersion and $R$ is the system radius.

---

## 2. Core Architecture & Mechanics

### 2.1 The Electromagnetic Spectrum as an Information Channel

The observable universe communicates through photons across roughly 24 decades of frequency, from radio ($\nu \sim 10^6 \, \mathrm{Hz}$) to gamma rays ($\nu \sim 10^{30} \, \mathrm{Hz}$). Each band traces different physical processes and encounters different propagation effects.

**Radio astronomy** traces synchrotron radiation from relativistic electrons spiraling in magnetic fields, free-free emission from ionized hydrogen, and the 21 cm hyperfine transition of neutral hydrogen (HI). The 21 cm line, arising from the spin-flip of the electron in the hydrogen ground state with energy splitting $\Delta E = 5.87 \times 10^{-6} \, \mathrm{eV}$, is the primary tracer of cold gas in galaxies and the intergalactic medium.

**Infrared astronomy** probes thermal emission from cool dust ($T \sim 10$–$1000 \, \mathrm{K}$) and molecular gas, as well as redshifted light from high-redshift galaxies. The dust continuum at $850 \, \mu\mathrm{m}$ (submillimeter) is the primary tool for detecting star-forming regions obscured at optical wavelengths.

**Optical astronomy** captures photospheric emission from stars with $T \sim 3000$–$50000 \, \mathrm{K}$, nebular recombination lines (Balmer series, $\mathrm{H\alpha}$ at 656.3 nm, $\mathrm{H\beta}$ at 486.1 nm), and reflected starlight from planets and comets.

**X-ray and gamma-ray astronomy** traces the most energetic processes: accretion onto compact objects, supernova remnant shocks, nuclear decay, and pair annihilation. These photons cannot penetrate Earth's atmosphere and require space-based detectors.

The key architecture principle is multiwavelength completeness: a physical object emits and absorbs across a range of frequencies, and the full spectral energy distribution encodes its temperature structure, composition, kinematics, and radiation environment.

### 2.2 Spectroscopy: The Rosetta Stone of Astrophysics

The Bohr model of the hydrogen atom, while superseded by quantum mechanics, correctly predicts the transition frequencies via:

$$\frac{1}{\lambda} = R_\infty \left(\frac{1}{n_1^2} - \frac{1}{n_2^2}\right)$$

where $R_\infty = 1.097 \times 10^7 \, \mathrm{m}^{-1}$ is the Rydberg constant and $n_1 < n_2$ are principal quantum numbers. The Lyman series ($n_1 = 1$) lies in the UV; the Balmer series ($n_1 = 2$) lies in the optical; the Paschen series ($n_1 = 3$) lies in the near-IR.

**Doppler shifts** encode radial velocity. For non-relativistic motion ($v \ll c$):

$$\frac{\Delta\lambda}{\lambda_0} = \frac{v_r}{c}$$

For relativistic sources (AGN jets, gamma-ray bursts), the full relativistic Doppler formula applies:

$$\frac{\nu_\mathrm{obs}}{\nu_\mathrm{em}} = \frac{1}{\gamma(1 + \beta\cos\theta)}$$

where $\beta = v/c$ and $\gamma = (1-\beta^2)^{-1/2}$.

**Cosmological redshift** is distinct from the Doppler effect. It arises from the expansion of spacetime itself:

$$1 + z = \frac{\lambda_\mathrm{obs}}{\lambda_\mathrm{em}} = \frac{a(t_\mathrm{obs})}{a(t_\mathrm{em})}$$

where $a(t)$ is the scale factor of the universe. At low redshift $z \ll 1$, the recession velocity approximates $v \approx cz$, and by Hubble's law $v = H_0 d$, giving $d \approx cz/H_0$. This is the basis of the cosmological distance scale for extragalactic objects.

**Line broadening mechanisms** encode physical conditions:

- Thermal (Doppler) broadening: $\Delta\nu/\nu = \sqrt{8kT\ln 2 / mc^2}$, where $m$ is the particle mass.
- Pressure broadening: collisional interactions shorten the coherence time of emission, broadening lines by $\Delta\nu \sim 1/\tau_\mathrm{collision}$.
- Rotation broadening: a spinning stellar disk produces a characteristic double-horn profile with wing width $v \sin i$ where $i$ is the inclination.
- Zeeman splitting: in a magnetic field $B$, degenerate energy levels split by $\Delta E = g_J \mu_B B m_J$, directly measuring field strength.

### 2.3 Orbital Mechanics and Kepler-Newton Architecture

Planetary and stellar dynamics are governed by Newton's law of gravitation:

$$\mathbf{F} = -\frac{GM_1 M_2}{r^2}\hat{r}$$

This produces conic section orbits. For bound orbits (total energy $E < 0$):

$$r(\theta) = \frac{a(1-e^2)}{1 + e\cos\theta}$$

where $a$ is the semi-major axis and $e$ is the eccentricity ($0 \leq e < 1$ for ellipses). Kepler's third law, derivable from the equation of motion:

$$P^2 = \frac{4\pi^2}{G(M_1 + M_2)} a^3$$

This is an exact result in the two-body problem. It generalizes to any gravitationally bound two-body system: binary stars, exoplanet host systems, moon-planet systems. By measuring period $P$ and semi-major axis $a$, we determine the total mass $M_1 + M_2$. The mass ratio $q = M_1/M_2$ is obtained from the center-of-mass condition $M_1 r_1 = M_2 r_2$.

**Orbital energy and angular momentum** are conserved in the two-body problem:

$$E = \frac{1}{2}\mu v^2 - \frac{GM\mu}{r} = -\frac{GM\mu}{2a}$$

$$\mathbf{L} = \mu \mathbf{r} \times \mathbf{v}$$

where $\mu = M_1 M_2 / (M_1 + M_2)$ is the reduced mass. The vis-viva equation, one of the most useful results in celestial mechanics, follows directly:

$$v^2 = GM\left(\frac{2}{r} - \frac{1}{a}\right)$$

This gives the speed at any point in an orbit given only the current radius and semi-major axis.

### 2.4 Stellar Structure: Hydrostatic Equilibrium

A star is a self-gravitating ball of plasma in mechanical equilibrium. The condition for this equilibrium is that the pressure gradient supports the weight of overlying material:

$$\frac{dP}{dr} = -\frac{G M(r) \rho(r)}{r^2}$$

where $M(r) = \int_0^r 4\pi r'^2 \rho(r') \, dr'$ is the mass enclosed within radius $r$. This equation of hydrostatic equilibrium (HSE), combined with an equation of state $P = P(\rho, T)$ and energy transport equations, constitutes the foundation of stellar structure theory.

The central pressure of the Sun can be estimated from a simple scaling argument. Integrating HSE over the stellar radius:

$$P_c \sim \frac{GM_\odot^2}{R_\odot^4} \sim \frac{(6.67\times10^{-11})(1.99\times10^{30})^2}{(6.96\times10^8)^4} \sim 10^{14} \, \mathrm{Pa}$$

The actual value from solar models is $P_c \approx 2.5 \times 10^{16} \, \mathrm{Pa}$; our estimate is order-of-magnitude correct. The discrepancy reflects the radial density concentration: the core is much denser than the mean.

**Energy transport** within stars occurs by three mechanisms: radiation (photon diffusion), convection (bulk fluid motion), and conduction (electron transport, relevant only in degenerate matter). The relative efficiency of each determines the stellar interior structure and, ultimately, the timescale and character of stellar evolution.

The photon diffusion timescale through the solar interior is:

$$\tau_\mathrm{diff} \approx \frac{R_\odot^2}{\lambda c / 3} \approx \frac{3R_\odot \kappa \bar{\rho}}{c} \sim 10^4 \, \mathrm{yr}$$

where $\kappa$ is the opacity and $\bar{\rho}$ is the mean density. A photon produced in the solar core takes roughly ten thousand years to random-walk to the surface, though a neutrino produced in the same nuclear reaction leaves the Sun in about two seconds.

### 2.5 The Distance Ladder

Distances in astronomy cannot be measured directly beyond a few kiloparsecs. Instead, they are built up through a hierarchy of overlapping techniques, each calibrated against the previous.

**Geometric methods (< 3 kpc)**

Trigonometric parallax is the foundational rung. For a star at distance $d$, the parallax angle $\varpi$ (in arcseconds) gives:

$$d = \frac{1}{\varpi} \, \mathrm{pc}$$

The Hipparcos satellite measured parallaxes to $\sim 1 \, \mathrm{mas}$ precision for $\sim 10^5$ stars. The Gaia mission has extended this to $\sim 1 \, \mu\mathrm{as}$ for $\sim 10^9$ stars, fundamentally recalibrating all subsequent rungs.

**Standard candles (1 kpc to cosmological distances)**

A standard candle is an object whose intrinsic luminosity $L$ is known, so that distance follows from the measured flux $F$ via $d = \sqrt{L/4\pi F}$.

The *distance modulus* is the logarithmic form:

$$\mu = m - M = 5\log_{10}(d/\mathrm{pc}) - 5$$

where $m$ is the apparent magnitude and $M$ is the absolute magnitude ($M$ is the apparent magnitude the object would have at $d = 10 \, \mathrm{pc}$).

Key standard candles include:

- **Cepheid variables**: Classical Cepheids pulsate with periods $P \sim 1$–$100$ days. Leavitt (1912) discovered that their period correlates tightly with absolute luminosity: $M_V \approx -2.81 \log_{10}(P/\mathrm{d}) - 1.43$. This period-luminosity relation is the primary extragalactic distance indicator to $\sim 30 \, \mathrm{Mpc}$.
- **Type Ia supernovae (SNe Ia)**: The thermonuclear destruction of a white dwarf near the Chandrasekhar mass produces a peak luminosity $M_B \approx -19.3 + 1.0 \Delta m_{15}$, where $\Delta m_{15}$ is the decline in magnitude 15 days after peak. After this Phillips relation correction, SNe Ia have dispersion $\sigma_M \approx 0.15 \, \mathrm{mag}$. They are visible to $z \sim 2$ and were the tool that established the accelerating expansion of the universe.
- **Tully-Fisher relation**: For spiral galaxies, the HI line width $W$ (a proxy for rotation velocity $v_c$) correlates with luminosity: $L \propto v_c^4$. This is a consequence of the virial theorem applied to rotationally supported disks.

---

## 3. High-Performance Implementation & Failure Modes

### 3.1 Signal Detection and Noise

An astronomical detector (CCD, bolometer, photodiode array) converts photon flux into a countable signal. The fundamental noise floor is Poisson noise: if $N$ photons are collected, the statistical uncertainty is $\sqrt{N}$. The signal-to-noise ratio (SNR) for a source against a background is:

$$\mathrm{SNR} = \frac{N_s}{\sqrt{N_s + N_b + N_d + \sigma_r^2}}$$

where $N_s$ is source counts, $N_b$ is sky background counts (per pixel, summed over the aperture), $N_d$ is dark current, and $\sigma_r$ is the readout noise. In the source-limited regime $N_s \gg N_b, N_d, \sigma_r$, the SNR $\approx \sqrt{N_s} \propto \sqrt{F A t}$, where $A$ is the collecting area and $t$ is integration time. Doubling sensitivity requires quadrupling integration time or quadrupling collecting area.

**Systematic noise sources** are more insidious than Poisson noise because they do not average down with longer observations:

- Flat-field errors: non-uniform detector response, correctable by dividing by a uniformly illuminated calibration frame.
- Atmospheric seeing: turbulent cells in the troposphere introduce wavefront distortions, smearing stellar images to a typical angular size of $\theta_\mathrm{seeing} \sim 0.5''$–$2''$ at good sites. Adaptive optics corrects this in real time by measuring the wavefront distortion via a guide star and applying conjugate corrections via a deformable mirror.
- Cosmic rays: high-energy particles produce sharp, non-astronomical signals in CCDs, distinguishable by their sub-pixel extent and removed by median-combining multiple exposures.

### 3.2 Coordinate Systems and Their Transformations

Astronomical positions are expressed in several coordinate systems, and transforming between them is a frequent source of error.

**Equatorial coordinates** (right ascension $\alpha$, declination $\delta$) are the standard celestial frame, referenced to the celestial equator and vernal equinox. Because Earth's rotation axis precesses with period $\sim 26\,000 \, \mathrm{yr}$, the equinox drifts; coordinates must always be reported with an epoch (J2000.0 is standard). The proper motion of nearby stars further displaces them over time.

**Galactic coordinates** ($\ell, b$) are centered on the Sun with $\ell = 0$ pointing toward the Galactic center and $b = 0$ in the Galactic plane. These are most natural for studies of Galactic structure, dust extinction (which scales approximately as $\csc |b|$ away from the plane), and stellar populations.

**Ecliptic coordinates** ($\lambda, \beta$) are referenced to the plane of Earth's orbit. They are used primarily for solar system objects.

The transformation between equatorial and galactic coordinates is a fixed rotation matrix:

$$\begin{pmatrix} x \\ y \\ z \end{pmatrix}_\mathrm{gal} = \mathbf{R} \begin{pmatrix} \cos\delta\cos\alpha \\ \cos\delta\sin\alpha \\ \sin\delta \end{pmatrix}$$

where $\mathbf{R}$ is the $3 \times 3$ rotation matrix encoding the Galactic pole position ($\alpha_{GP} = 192.86°$, $\delta_{GP} = +27.13°$) and the ascending node of the Galactic plane on the equator.

### 3.3 Common Failure Modes and Systematic Errors

**The Malmquist bias** is a selection effect that systematically overestimates distances and luminosities in flux-limited surveys. Because flux-limited samples preferentially include the brightest objects at large distances, the apparent mean luminosity of a volume element increases with distance even if the true luminosity function is uniform. Any distance-dependent analysis of a flux-limited catalog must correct for this bias or will infer spuriously high luminosities at large distances.

**Extinction and reddening.** Dust grains along the line of sight preferentially absorb and scatter blue photons, making sources appear redder and fainter. The wavelength dependence is approximately $A_\lambda \propto \lambda^{-1.7}$ in the optical. The relation between color excess and total extinction in the $V$ band is parametrized by:

$$R_V = \frac{A_V}{E(B-V)} \approx 3.1$$

in the diffuse interstellar medium, though $R_V$ ranges from 2.5 to 5 in denser regions. Failure to correct for extinction systematically shifts inferred temperatures (bluer intrinsic than observed) and distances (sources appear farther away than they are).

**Confusion and blending.** At high source densities (e.g., the Galactic bulge, crowded cluster cores, deep cosmological fields), multiple unresolved sources fall within a single resolution element. Photometric and astrometric measurements of blended sources are biased; this must be accounted for with point-spread function (PSF) fitting photometry rather than aperture photometry.

**Non-standard candles.** Every distance indicator has a dispersion and an evolutionary correction. Cepheids in metal-poor environments follow a shifted period-luminosity relation because stellar opacity depends on metallicity. SNe Ia in star-forming versus passive host galaxies show a systematic offset in peak luminosity at the $\sim 0.1 \, \mathrm{mag}$ level, possibly related to progenitor age or metallicity. Failure to apply host-galaxy corrections is a major source of systematic uncertainty in $H_0$ measurements.

**The $H_0$ tension** is the most prominent current example of systematic error in astronomy. The local distance ladder (Cepheids + SNe Ia) gives $H_0 = 73.0 \pm 1.0 \, \mathrm{km\,s^{-1}\,Mpc^{-1}}$ (Riess et al.), while the CMB power spectrum fit to $\Lambda$CDM gives $H_0 = 67.4 \pm 0.5 \, \mathrm{km\,s^{-1}\,Mpc^{-1}}$ (Planck Collaboration). The discrepancy is $\sim 5\sigma$. It may reflect uncharacterized systematic errors in one or both methods, or it may indicate new physics beyond $\Lambda$CDM. This tension exemplifies the central challenge of astronomy: disentangling astrophysical systematics from genuine physical signals.

### 3.4 High-Performance Observational Strategies

**Signal co-addition and dithering.** Multiple short exposures are preferred over a single long exposure because they permit cosmic-ray rejection, fill in detector gaps when the telescope is dithered between exposures, and avoid saturation of bright sources. The combined image is typically produced by sigma-clipping or median-combining the individual frames.

**Spectral calibration.** Wavelength solutions for spectrographs are established by comparison arc lamp spectra (ThAr, NeAr) with known transition wavelengths. The wavelength solution drifts with temperature and flexure; stability of the wavelength solution to $< 1 \, \mathrm{m\,s^{-1}}$ (required for exoplanet radial velocities) demands either simultaneous calibration or laser frequency comb calibration.

**Photometric calibration.** Flux calibration requires observation of standard stars with known spectral energy distributions. The atmosphere introduces wavelength-dependent extinction with airmass $X$; the standard Bouguer-Langley method measures the instrumental magnitude of a standard at multiple airmass values to fit simultaneously for the star's flux and the extinction coefficient.

---

## 4. Summary & Verification Matrix

### 4.1 Conceptual Summary

Astronomy is an observational science that transforms received radiation into physical knowledge. Its reliability rests on a small set of invariants: the universality of physical law, the constancy of $c$, the conservation of energy and momentum, the geometric inverse-square law, and the blackbody SED for thermal sources. These invariants, combined with the quantum mechanics of atomic transitions, make spectroscopy the dominant analytical tool. Orbital mechanics provides exact solutions to the two-body problem through the vis-viva equation and Kepler's third law, connecting observable periods and angles to masses and distances. Stellar structure is governed by hydrostatic equilibrium. And distances, the hardest quantities to measure, are chained through a hierarchy of geometric and standard-candle methods, each vulnerable to its own systematic errors.

### 4.2 Key Equations Reference

| Equation | Physical content |
|---|---|
| $F = L / 4\pi d^2$ | Flux-luminosity-distance relation |
| $B_\nu(T) = \frac{2h\nu^3}{c^2}(e^{h\nu/kT}-1)^{-1}$ | Planck spectral radiance |
| $1/\lambda = R_\infty(1/n_1^2 - 1/n_2^2)$ | Hydrogen spectral series |
| $\Delta\lambda/\lambda_0 = v_r/c$ | Non-relativistic Doppler shift |
| $1 + z = a(t_\mathrm{obs})/a(t_\mathrm{em})$ | Cosmological redshift |
| $P^2 = 4\pi^2 a^3 / G(M_1+M_2)$ | Kepler's third law |
| $v^2 = GM(2/r - 1/a)$ | Vis-viva equation |
| $dP/dr = -GM(r)\rho/r^2$ | Hydrostatic equilibrium |
| $\mu = m - M = 5\log_{10}(d/\mathrm{pc}) - 5$ | Distance modulus |
| $2\langle K\rangle + \langle U\rangle = 0$ | Virial theorem |

### 4.3 Verification Matrix

Each row states a claim from this lesson, the test that would falsify it, and the status of that test.

| Claim | Falsification test | Empirical status |
|---|---|---|
| Physical laws are universal | Measure fundamental constants ($\alpha$, $G$, $c$) at high redshift and find variation | No variation detected to $|\Delta\alpha/\alpha| < 10^{-6}$ across $z \sim 0$–$3$ |
| Inverse-square law holds | Gravitational wave luminosity distance vs. electromagnetic distance in binary neutron star merger | Consistent in GW170817 to $< 15\%$ |
| Blackbody emission from stellar photospheres | Fit Planck function to resolved stellar SEDs; residuals reveal atmospheric absorption | Confirmed with departures explained by stellar atmosphere models |
| Kepler's third law in the two-body limit | Timing of binary pulsars; planet transit + radial velocity masses | Confirmed at $10^{-10}$ precision for PSR J0737-3039 |
| Hydrostatic equilibrium in the Sun | Helioseismology: p-mode frequencies constrain interior density and pressure profiles | Solar models accurate to $< 0.3\%$ in sound speed profile |
| Distance modulus from parallax-calibrated Cepheids | Independent distance from detached eclipsing binaries in LMC | Consistent to $\sim 1\%$ |
| Cosmological redshift is not Doppler | Supernova light curves stretch by $(1+z)$; photon arrival rate decreases by $(1+z)$ | Both effects observed and consistent with expansion interpretation |
| Malmquist bias inflates apparent luminosities | Compare $\langle M \rangle$ in volume-limited vs. flux-limited sub-samples of same survey | Systematically confirmed in every flux-limited spectroscopic survey |

### 4.4 Diagnostic Questions

A student who has mastered this lesson should answer the following without reference material.

1. A star has apparent magnitude $m_V = 8.0$ and absolute magnitude $M_V = 3.0$. What is its distance?

   *Answer:* $\mu = 5.0$, so $d = 10^{(5.0+5)/5} \, \mathrm{pc} = 10^{2} \, \mathrm{pc} = 100 \, \mathrm{pc}$.

2. A spectral line observed at 660 nm is known to have a rest wavelength of 656.3 nm. Is the source approaching or receding? What is its radial velocity?

   *Answer:* The line is redshifted ($\Delta\lambda = +3.7 \, \mathrm{nm}$), so the source is receding. $v_r = c \Delta\lambda / \lambda_0 = (3\times10^5 \, \mathrm{km\,s^{-1}})(3.7/656.3) \approx 1690 \, \mathrm{km\,s^{-1}}$.

3. A binary star system has an orbital period of 2 years and a semi-major axis of 2 AU. What is the total system mass in solar masses?

   *Answer:* Kepler's third law in solar units: $M_\mathrm{tot} = a^3/P^2 = 8/4 = 2 \, M_\odot$.

4. Why does a contracting protostellar cloud heat up rather than cool down?

   *Answer:* By the virial theorem, $2\langle K\rangle = -\langle U\rangle$. As the cloud contracts, $|U|$ increases. Half of the released gravitational energy goes into kinetic energy (heat), raising the temperature; the other half is radiated away. The system loses total energy while increasing temperature because gravity produces a negative effective heat capacity.

5. What two systematic errors would cause you to overestimate the distance to a star-forming galaxy?

   *Answer:* Dust extinction (makes the galaxy appear fainter than it is, inflating the inferred distance from the inverse-square law) and Malmquist bias (preferential inclusion of intrinsically luminous objects in flux-limited samples causes the mean standard-candle luminosity to be overestimated).
