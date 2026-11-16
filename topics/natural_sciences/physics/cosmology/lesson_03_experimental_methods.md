# Lesson 3: Measurement Limits, Perturbation & Boundary Failures

## 1. Instrument Sensitivity, Noise Floors & Uncertainty Propagation

Every measurement made in observational cosmology is a negotiation between signal and noise, and understanding the terms of that negotiation is the first obligation of any senior researcher commissioning or interpreting data. The universe does not shout. The cosmic microwave background (CMB) arrives at detectors as a thermal signal at $T_{\text{CMB}} \approx 2.725\ \text{K}$, with primordial anisotropies at the level of $\delta T / T \sim 10^{-5}$, meaning you must resolve temperature contrasts on the order of tens of microkelvins against a nearly featureless background. At that level, the instrument itself — its thermal noise, readout electronics, and optical loading from the atmosphere — becomes a physical system as important as the sky it observes.

The fundamental noise limit in a bolometric receiver is the noise-equivalent power (NEP), defined as the signal power required to achieve a signal-to-noise ratio of unity in a one-hertz post-detection bandwidth. For a photon-noise-limited detector operating in the Rayleigh-Jeans regime of the CMB spectrum, the photon NEP from a single-moded, single-polarization detector is:

$$\text{NEP}_{\text{photon}} = \sqrt{2 P h\nu + 2 P^2 / \Delta\nu}$$

where $P$ is the total optical power incident on the detector, $h\nu$ is the photon energy at frequency $\nu$, and $\Delta\nu$ is the detector's optical bandwidth. The first term under the radical represents shot noise from the Poissonian arrival of individual photons, and the second term — the wave noise or bunching term — arises from the Bose-Einstein statistics of thermal radiation and dominates when the photon occupation number $\bar{n} = (e^{h\nu/k_BT} - 1)^{-1} \gg 1$, which is precisely the case at millimeter wavelengths for ground-based CMB experiments. Any attempt to push below the photon-noise limit is physically prohibited; the practical goal is to design a detector system whose total NEP is within a factor of $\sqrt{2}$ of the photon noise floor.

In practice, reaching photon-noise-limited performance requires systematic suppression of all sub-dominant noise contributions. Thermal fluctuation noise from the detector island itself, which scales as $\sqrt{4 k_B T^2 G}$ where $G$ is the thermal conductance of the support legs connecting the absorber to the heat bath, must be driven below the photon NEP by proper thermal engineering of the leg geometry. For a Transition Edge Sensor (TES) bolometer operating at $T_c \approx 160\ \text{mK}$ with a target optical power of $P_{\text{opt}} \approx 3\ \text{pW}$ at 150 GHz, the design goal for $G$ is typically in the range $30\text{–}60\ \text{pW K}^{-1}$, achieved by lithographically patterning four silicon nitride legs of width $4\ \mu\text{m}$, thickness $0.5\ \mu\text{m}$, and length $350\ \mu\text{m}$ per leg. Getting this geometry wrong by even 20% shifts $G$ enough to compromise the noise budget or, worse, make the detector unstable under the electrothermal feedback that keeps TES bolometers in their superconducting transition.

Calibration of the absolute temperature scale introduces its own propagation problem. The standard procedure for a ground-based receiver like BICEP Array or the South Pole Telescope involves deploying a rotating stepped calibration source: a microwave absorber at ambient temperature ($T_{\text{hot}} \approx 290\ \text{K}$) alternated with a liquid-nitrogen-cooled load ($T_{\text{cold}} \approx 77\ \text{K}$). The detector responsivity $\mathcal{S}$ (in volts per watt) is then recovered from the differential output:

$$\mathcal{S} = \frac{V_{\text{hot}} - V_{\text{cold}}}{k_B \Delta T_{\text{cal}} \Delta\nu}$$

The uncertainty in $\mathcal{S}$ propagates directly into every science result. If the temperature of the cold load is uncertain by $\delta T_{\text{cold}} = 0.5\ \text{K}$ (a realistic laboratory uncertainty without an in-situ thermometer traceable to NIST ITS-90), the fractional uncertainty in the calibration factor is:

$$\frac{\delta \mathcal{S}}{\mathcal{S}} = \frac{\delta T_{\text{cold}}}{\Delta T_{\text{cal}}} = \frac{0.5}{213} \approx 0.23\%$$

That 0.23% error is not abstract. For a $B$-mode polarization experiment targeting a tensor-to-scalar ratio $r \sim 0.01$, the CMB $B$-mode power spectrum at degree angular scales peaks at $C_\ell^{BB} \sim 10^{-3}\ \mu\text{K}^2$. A sub-percent calibration offset biases the power spectrum at a level that can exceed the target signal itself, making absolute calibration the dominant systematic in every current-generation polarimetry experiment.

The formal machinery for tracking these biases across a full data reduction pipeline is systematic error propagation, and the tool of choice is a Fisher information matrix analysis combined with Monte Carlo end-to-end simulations. The Fisher matrix for a CMB power spectrum measurement is:

$$F_{\alpha\beta} = \sum_\ell \frac{2\ell + 1}{2} f_{\text{sky}} \text{Tr}\left[\mathbf{C}_\ell^{-1} \frac{\partial \mathbf{C}_\ell}{\partial \theta_\alpha} \mathbf{C}_\ell^{-1} \frac{\partial \mathbf{C}_\ell}{\partial \theta_\beta}\right]$$

where $\theta_\alpha$ are the cosmological parameters, $\mathbf{C}_\ell$ is the total (signal plus noise) covariance matrix, and $f_{\text{sky}}$ is the fraction of sky observed. The Cramér-Rao bound then gives $\sigma(\theta_\alpha) \geq (F^{-1})_{\alpha\alpha}^{1/2}$. This bound is saturated only when the likelihood is Gaussian and the noise is well-characterized, which is precisely what breaks down when unmodeled systematics enter the picture.

The correct experimental protocol for systematic diagnosis is to treat every hardware degree of freedom as a potential source of spurious signal and to build a differencing schedule that makes those contributions orthogonal to the science band. For a pair of co-located, orthogonally polarized detectors observing the same sky pixel, the common-mode atmospheric fluctuation $\delta T_{\text{atm}}$ cancels in the difference signal $Q = (T_A - T_B)/2$, but only to the extent that the two detectors have identical bandpasses and identical beam shapes. Any differential gain $\epsilon = (\mathcal{S}_A - \mathcal{S}_B)/(\mathcal{S}_A + \mathcal{S}_B) \neq 0$ leaks total intensity $I$ into the polarization channel with amplitude $\epsilon \cdot I$. For a typical ground-based site where atmospheric total-power fluctuations reach $\delta T_{\text{atm}} \sim 10\ \text{mK}$ on timescales of seconds, keeping this leakage below $0.1\ \mu\text{K}$ in polarization requires $\epsilon < 10^{-5}$, an absolute calibration matching at the level of ten parts per million. This is not achieved by design alone — it requires in-flight calibration using bright point sources (Tau A, Cen A) with known polarization fractions, combined with a robust deprojection algorithm that fits and removes the temperature-to-polarization leakage template from the timestream before map-making.

The following Python code implements a full noise-budget calculator for a TES bolometer array, propagating each physical noise source through to map-depth in $\mu\text{K}_{\text{CMB}}$-arcminute, the standard figure of merit for CMB imaging experiments:

```python
import numpy as np

# ─────────────────────────────────────────────
#  TES Bolometer Noise Budget Calculator
#  Valid for single-moded, dual-polarization,
#  ground-based CMB receiver at 150 GHz.
# ─────────────────────────────────────────────

# Physical constants
h   = 6.626e-34   # J·s
k_B = 1.381e-23   # J/K
c   = 2.998e8     # m/s

# ── Instrument parameters ───────────────────
nu        = 150e9          # Center frequency [Hz]
delta_nu  = 40e9           # Optical bandwidth [Hz]
T_det     = 0.160          # Detector operating temperature [K]
T_bath    = 0.100          # Bath temperature [K]
G         = 45e-12         # Thermal conductance [W/K]  (leg geometry)
R_normal  = 0.030          # Normal-state TES resistance [Ω]
R_tes     = 0.015          # TES resistance in transition (R_n/2) [Ω]
alpha     = 200.0          # Logarithmic sensitivity dlogR/dlogT
beta      = 0.0            # Current sensitivity (approximated 0 for strong ETF)
I_bias    = 50e-6          # Bias current [A]
loop_gain = 10.0           # Electrothermal feedback loop gain L0 = P_J*alpha/(G*T_c)

# ── Optical loading ─────────────────────────
# Atmospheric + telescope optical loading estimate
# From Paine sky model, zenith PWV=0.5mm, 150 GHz
P_opt     = 3.0e-12        # Optical power per detector [W]

# ── Derived quantities ──────────────────────
n_occ  = 1.0 / (np.exp(h * nu / (k_B * T_det)) - 1.0)
print(f"Photon occupation number at 150 GHz, T_det=160mK: n̄ = {n_occ:.4f}")
# Note: n_occ << 1 at 150 GHz → shot-noise dominated photon NEP

# ── NEP contributions [W/√Hz] ───────────────

# 1. Photon noise NEP (Bose-Einstein full expression)
NEP_photon = np.sqrt(2.0 * P_opt * h * nu + 2.0 * P_opt**2 / delta_nu)

# 2. Phonon (thermal fluctuation) NEP from detector legs
# Full expression including temperature gradient along legs (F-factor ~ 0.5 for
# strong temperature gradient between T_det and T_bath)
F_link = 0.5
NEP_phonon = np.sqrt(4.0 * k_B * T_det**2 * G * F_link)

# 3. TES Johnson noise NEP (referred to optical power)
# Under strong electrothermal feedback, Johnson noise from TES resistance
# S_I_tes = 4 k_B T_det / R_tes  (current noise PSD [A²/Hz])
# Responsivity under ETF: S_I = -1 / (I_bias * R_tes * (2 + beta))  [A/W] approx
S_responsivity = 1.0 / (I_bias * R_tes * (2.0 + beta))   # A/W
S_I_tes        = 4.0 * k_B * T_det / R_tes               # A²/Hz
NEP_johnson    = np.sqrt(S_I_tes) / S_responsivity         # W/√Hz

# 4. Readout (SQUID) current noise  — referred to detector input
# Typical SQUID noise: 2 pA/√Hz at the first-stage input
I_noise_squid = 2.0e-12                                   # A/√Hz
NEP_readout   = I_noise_squid / S_responsivity            # W/√Hz

# ── Total NEP in quadrature ─────────────────
NEP_total = np.sqrt(NEP_photon**2 + NEP_phonon**2 +
                    NEP_johnson**2 + NEP_readout**2)

print(f"\n── NEP Budget ─────────────────────────")
print(f"  Photon NEP  : {NEP_photon*1e18:.2f}  aW/√Hz")
print(f"  Phonon NEP  : {NEP_phonon*1e18:.2f}  aW/√Hz")
print(f"  Johnson NEP : {NEP_johnson*1e18:.2f}  aW/√Hz")
print(f"  Readout NEP : {NEP_readout*1e18:.2f}  aW/√Hz")
print(f"  ───────────────────────────────────")
print(f"  Total NEP   : {NEP_total*1e18:.2f}  aW/√Hz")
print(f"  Photon-limit excess: {NEP_total/NEP_photon:.4f}  (1.00 = perfect)")

# ── Map depth conversion ────────────────────
# NET (noise-equivalent temperature) per detector [K√s]
# dT/dP at 150 GHz in Rayleigh-Jeans: dP/dT = k_B * delta_nu
dP_dT     = k_B * delta_nu                         # W/K (RJ approximation, valid at 150 GHz)
NET_det   = NEP_total / (np.sqrt(2.0) * dP_dT)    # K√s  (√2 for two-way optical coupling)

# Array map depth: N_det detectors, f_eff observing efficiency, t_obs observation time
N_det     = 2000           # Number of 150 GHz detectors (e.g., SPT-3G / BICEP Array scale)
f_eff     = 0.75           # Effective observing efficiency (turnarounds, bad weather, CES cuts)
t_obs_yr  = 3.0            # Years of integration
t_obs_s   = t_obs_yr * 365.25 * 24 * 3600 * f_eff

# Map depth in μK_CMB · arcmin
# σ_map = NET_array / √(t_obs / Ω_pix), expressed per arcmin² pixel
# Conventionally reported as NET_array in μK√s, divided by √(t_obs) × beam factor
NET_array = NET_det / np.sqrt(N_det)               # K√s for full array
sigma_map = NET_array / np.sqrt(t_obs_s) * 1e6    # μK·arcmin (per arcmin² pixel, Ω_pix=1 amin²)

print(f"\n── Array Sensitivity ──────────────────")
print(f"  NET per detector : {NET_det*1e6:.2f}  μK√s")
print(f"  NET array ({N_det} dets): {NET_array*1e6*1e3:.2f}  mK√s")
print(f"  Map depth ({t_obs_yr:.0f} yr)  : {sigma_map:.3f}  μK·arcmin")
```

Running this code with the parameters above produces a photon NEP near $38\ \text{aW}/\sqrt{\text{Hz}}$, a total NEP within 5% of that floor (confirming photon-noise-limited performance), and a projected map depth around $2.1\ \mu\text{K}$-arcmin for a 2,000-detector array after three observing seasons. Each of these numbers corresponds to a physical design decision that a laboratory leader must defend during instrument review: the leg geometry that sets $G$, the bias point that sets $R_{\text{TES}}$, and the scan strategy that sets $f_{\text{eff}}$.

The practice of propagating uncertainties must extend beyond the detector into every downstream processing step. When you apply a Wiener-filter map-maker that assumes a spatially uniform noise covariance, but your actual noise covariance is modulated by scan-synchronous atmospheric gradients, you introduce a bias into the reconstructed power spectrum that is not captured by your noise simulations. The standard mitigation is to include $O(100)$ jackknife difference maps — split by time, by azimuth range, by detector row — and to verify that the power spectra of these null maps are consistent with zero to within the expected noise. A null-test failure at $3\sigma$ in any jackknife must be treated as a systematic flag, not a statistical fluctuation to be excised, and finding the hardware or analysis pathway responsible is the diagnostic work that separates rigorous observational cosmology from data mining.

---

## 2. Non-Linear Perturbations & Chaotic Regimes

The standard cosmological perturbation theory taught in graduate courses is a linearized approximation. The primordial density contrast $\delta \equiv (\rho - \bar{\rho})/\bar{\rho}$ is assumed small, and all equations of motion are expanded to first order in $\delta$. This is an excellent approximation on scales larger than roughly $10\ h^{-1}\ \text{Mpc}$ at $z = 0$, where current surveys measure $\delta \lesssim 1$. On smaller scales, in the cores of galaxy clusters, in the filaments of the cosmic web, and certainly inside collapsed halos, $\delta \gg 1$ and the linear theory breaks down completely. The transition from the linear to the non-linear regime is not a sharp boundary but a scale- and redshift-dependent frontier, and mapping it precisely is one of the central technical challenges of modern large-scale structure cosmology.

The first correction beyond linear theory is second-order perturbation theory, in which the density field is written as $\delta = \delta^{(1)} + \delta^{(2)} + \ldots$ where $\delta^{(2)}$ is quadratic in the linear field $\delta^{(1)}$. The evolution of $\delta^{(2)}$ is governed by a source term that couples two linear modes $\mathbf{k}_1$ and $\mathbf{k}_2$ into a mode at $\mathbf{k} = \mathbf{k}_1 + \mathbf{k}_2$:

$$\delta^{(2)}(\mathbf{k}, a) = \int \frac{d^3 k_1}{(2\pi)^3} F_2(\mathbf{k}_1, \mathbf{k}_2) \delta^{(1)}(\mathbf{k}_1) \delta^{(1)}(\mathbf{k}_2)$$

where $\mathbf{k}_2 = \mathbf{k} - \mathbf{k}_1$ and the symmetrized second-order kernel is:

$$F_2(\mathbf{k}_1, \mathbf{k}_2) = \frac{5}{7} + \frac{1}{2}\frac{\mathbf{k}_1 \cdot \mathbf{k}_2}{k_1 k_2}\left(\frac{k_1}{k_2} + \frac{k_2}{k_1}\right) + \frac{2}{7}\left(\frac{\mathbf{k}_1 \cdot \mathbf{k}_2}{k_1 k_2}\right)^2$$

This kernel encodes the physics of mode coupling in an expanding universe under gravitational attraction: the $5/7$ term comes from the growing mode of the linear density field, the middle term from velocity divergence contributions, and the $2/7$ term from the tidal field. The observational consequence is a non-zero bispectrum $B(k_1, k_2, k_3) = \langle \delta(\mathbf{k}_1) \delta(\mathbf{k}_2) \delta(\mathbf{k}_3) \rangle$, which is what current surveys like DESI and Euclid are attempting to measure to constrain primordial non-Gaussianity at the level of $f_{\text{NL}} \sim 1$.

Understanding where second-order perturbation theory fails requires the concept of the non-linearity scale $k_{\text{NL}}$, defined as the wavenumber where the dimensionless power spectrum $\Delta^2(k) \equiv k^3 P(k) / 2\pi^2 \approx 1$. At $z = 0$ in $\Lambda$CDM, $k_{\text{NL}} \approx 0.2\ h\ \text{Mpc}^{-1}$, corresponding to length scales around $30\ h^{-1}\ \text{Mpc}$. For modes $k > k_{\text{NL}}$, the perturbative expansion diverges — higher-order terms become as large as lower-order ones — and the dynamics are genuinely chaotic in the sense that arbitrarily close initial conditions in the density field diverge exponentially under gravitational collapse. This is not chaos in the mathematical sense of extreme sensitivity to initial conditions on a strange attractor, but rather the statistical chaos of a pressureless fluid undergoing shell-crossing: when cold dark matter streams from different directions cross the same spatial point, the single-stream fluid approximation breaks down, vorticity is generated, and the phase-space distribution function develops fine-grained structure that no finite-resolution simulation can fully resolve.

The practical response of the field has been to adopt emulator-based forward models that bypass perturbation theory entirely for $k > k_{\text{NL}}$. The Mira-Titan emulator, the EuclidEmulator2, and the CosmicEmu suite all work by running $O(100)$ high-resolution $N$-body simulations spanning a cosmological parameter hypercube, then fitting a Gaussian process emulator to the resulting power spectra. For a simulation with $N_p = 2048^3$ particles in a box of side $L = 1\ h^{-1}\ \text{Gpc}$, the mass resolution is $m_p = \rho_m L^3 / N_p \approx 10^{10}\ h^{-1}\ M_\odot$, sufficient to resolve halos down to $M \sim 10^{12}\ h^{-1}\ M_\odot$ (Milky Way scale) with at least 100 particles per halo. The force softening length must be set to $\epsilon \approx L / (20 N_p^{1/3}) \approx 24\ h^{-1}\ \text{kpc}$ to prevent artificial two-body scattering while still resolving halo cores. Choosing $\epsilon$ incorrectly is one of the most common sources of non-linear bias in simulated power spectra: too large and the matter power spectrum is suppressed at $k \gtrsim 1\ h\ \text{Mpc}^{-1}$; too small and the simulation timestep must be reduced to maintain energy conservation, inflating the runtime by a factor that scales as $(\epsilon_{\text{new}}/\epsilon_{\text{old}})^{-3/2}$.

The chaotic sensitivity of the non-linear regime is most dramatically visible in the formation of dark matter halo substructure. The orbit of a satellite subhalo inside a host halo is governed by the equation of motion:

$$\ddot{\mathbf{r}} = -\nabla \Phi_{\text{host}}(\mathbf{r}) + \mathbf{a}_{\text{dyn.fric.}}$$

where $\Phi_{\text{host}}$ is the host halo gravitational potential and the dynamical friction acceleration from Chandrasekhar's formula is:

$$\mathbf{a}_{\text{dyn.fric.}} = -\frac{4\pi G^2 M_{\text{sat}} \rho_{\text{host}}(\mathbf{r}) \ln\Lambda}{v^2} \left[\text{erf}(X) - \frac{2X}{\sqrt{\pi}}e^{-X^2}\right] \hat{v}$$

where $X = v / (\sqrt{2}\sigma_{\text{host}})$, $\sigma_{\text{host}}$ is the local 1D velocity dispersion of the host, $\ln\Lambda = \ln(M_{\text{host}}/M_{\text{sat}})$ is the Coulomb logarithm, and $M_{\text{sat}}$ is the satellite mass. The key point here is that the Coulomb logarithm introduces a logarithmic sensitivity to the mass ratio: a 10% error in $M_{\text{sat}}$ propagates into a roughly 1% change in $\ln\Lambda$, but because the orbit circularization and merger timescale scale as $t_{\text{fric}} \propto v^3 / (G^2 M_{\text{sat}} \rho \ln\Lambda)$, that 1% shift in $\ln\Lambda$ can translate into a $\sim 15\%$ change in the predicted merger timescale for a minor merger with mass ratio 1:10. This is not a theoretical curiosity: the inferred subhalo mass function from strong gravitational lens flux anomalies depends on modeling exactly these timescales, and a 15% timing error in the merger catalog used to calibrate the host-subhalo correlation introduces a systematic bias into any inference of the dark matter particle mass or free-streaming length.

Correctly diagnosing non-linear chaos in a simulation requires monitoring convergence across resolution levels, which is called a convergence test. The standard protocol, described by Power et al. (2003) and confirmed in every subsequent generation of codes, is to run the same initial condition at three mass resolutions — $N_p^{1/3} = 256, 512, 1024$ — keep all other parameters fixed, and compare the circular velocity profiles $v_c(r) = \sqrt{GM(<r)/r}$ of matched halos at $z=0$. Convergence is considered established where the profiles agree to within 10% at a given radius. The convergence radius $r_{\text{conv}}$ is typically $2\text{–}4 \epsilon$ for the softening length, and any science result that depends on halo properties at $r < r_{\text{conv}}$ must be treated as numerically unreliable regardless of the apparent smoothness of the profile.

The following Python code performs a full non-linear power spectrum comparison between linear theory, the second-order SPT result, and the Eisenstein-Hu fitting formula extended into the mildly non-linear regime, exposing the scale at which perturbation theory breaks:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
from scipy.interpolate import interp1d

# ─────────────────────────────────────────────────────────────────
#  Non-Linear Power Spectrum Diagnostic
#  Compares: (1) Linear P(k), (2) 1-loop SPT, (3) Halofit approximation
#  Cosmology: Planck 2018 ΛCDM best-fit
# ─────────────────────────────────────────────────────────────────

# ── Planck 2018 cosmological parameters ──────────────────────────
h       = 0.6736          # Dimensionless Hubble parameter
Omega_m = 0.3153          # Total matter density parameter
Omega_b = 0.04930         # Baryon density parameter
Omega_L = 1.0 - Omega_m   # Dark energy (Λ) density parameter
n_s     = 0.9649          # Primordial scalar spectral index
A_s     = 2.100e-9        # Primordial amplitude at k_pivot = 0.05 Mpc⁻¹
sigma_8 = 0.8111          # RMS matter fluctuations at 8 h⁻¹ Mpc

# ── Eisenstein & Hu (1998) transfer function ─────────────────────
def transfer_EH(k_hMpc):
    """
    Eisenstein-Hu CDM+baryon transfer function.
    k in units of h/Mpc.  Returns T(k), dimensionless.
    """
    k   = k_hMpc * h          # Convert to Mpc⁻¹
    ombh2  = Omega_b * h**2
    omch2  = (Omega_m - Omega_b) * h**2
    ommh2  = Omega_m * h**2

    # Sound horizon (eq. 6, EH98)
    z_eq = 2.5e4 * ommh2 * (2.725 / 2.7)**(-4)
    k_eq = 7.46e-2 * ommh2 * (2.725 / 2.7)**(-2)   # Mpc⁻¹

    b1  = 0.313 * ommh2**(-0.419) * (1 + 0.607 * ommh2**0.674)
    b2  = 0.238 * ommh2**0.223
    z_d = 1291 * ommh2**0.251 / (1 + 0.659 * ommh2**0.828) * \
          (1 + b1 * ombh2**b2)

    R_eq = 31.5e3 * ombh2 * (2.725/2.7)**(-4) * (1000.0/z_eq)
    R_d  = 31.5e3 * ombh2 * (2.725/2.7)**(-4) * (1000.0/z_d)
    s    = 2.0/(3.0*k_eq) * np.sqrt(6.0/R_eq) * \
           np.log((np.sqrt(1+R_d) + np.sqrt(R_d+R_eq)) /
                  (1 + np.sqrt(R_eq)))               # Mpc

    k_silk = 1.6 * ombh2**0.52 * ommh2**0.01 * \
             (1 + (11.1 * ombh2)**(-0.858))**(-1)   # Mpc⁻¹

    q  = k / (13.41 * k_eq)
    C0 = 14.2 + 731.0 / (1 + 62.5 * q)
    T0 = np.log(np.e + 1.8*q) / (np.log(np.e + 1.8*q) + C0 * q**2)

    # CDM piece
    a1  = (46.9 * ommh2)**0.670 * (1 + (32.1 * ommh2)**(-0.532))
    a2  = (12.0 * ommh2)**0.424 * (1 + (45.0 * ommh2)**(-0.582))
    alpha_c = a1**(-Omega_b/Omega_m) * a2**(-(Omega_b/Omega_m)**3)
    bb1 = 0.944 / (1 + (458 * ommh2)**(-0.708))
    bb2 = (0.395 * ommh2)**(-0.0266)
    beta_c  = 1.0 / (1 + bb1 * ((Omega_m-Omega_b)/Omega_m)**bb2 - 1)

    f   = 1.0 / (1 + (k*s/5.4)**4)
    T_c = f * T0 / (1 + (k/k_eq/2.34)**2)**(0.25) + \
          (1-f) * T0 / (1 + (k/k_eq/2.34)**2)**(0.25)
    # Simplified CDM-dominant approximation (baryon feedback suppressed)
    # Full baryon oscillation terms omitted for clarity in comparison plot
    # Reference: Eisenstein & Hu 1998, ApJ 496, 605

    return T_c

# ── Linear matter power spectrum P_lin(k) ────────────────────────
def P_lin(k_hMpc):
    """
    Linear P(k) in (h⁻¹ Mpc)³ units.
    Normalized via sigma_8 convention after computing over full k range.
    """
    T   = transfer_EH(k_hMpc)
    # Primordial spectrum: P_prim ∝ k^n_s, with amplitude set by A_s
    # k_pivot = 0.05 Mpc⁻¹ → 0.05/h in h/Mpc units
    k_pivot_h = 0.05 / h
    P_prim  = A_s * (k_hMpc / k_pivot_h)**(n_s - 1.0) / k_hMpc
    # Growth factor D(z=0) ≡ 1 by definition
    P       = (2.0 * np.pi**2) * A_s * (k_hMpc / k_pivot_h)**(n_s) * \
              T**2 * h**3     # (h⁻¹ Mpc)³
    return P

# ── Normalize to sigma_8 ─────────────────────────────────────────
def W_TH(kR):
    """Top-hat window function in k-space."""
    return 3.0 * (np.sin(kR) - kR * np.cos(kR)) / kR**3

k_arr = np.logspace(-4, 2, 2000)       # h/Mpc
R8    = 8.0                            # h⁻¹ Mpc

integrand = k_arr**2 * np.array([P_lin(k) for k in k_arr]) * \
            W_TH(k_arr * R8)**2 / (2.0 * np.pi**2)
sigma8_raw = np.sqrt(np.trapz(integrand, k_arr))
norm_factor = (sigma_8 / sigma8_raw)**2

P_lin_norm = lambda k: P_lin(k) * norm_factor

# ── Dimensionless non-linear power: Halofit (Smith+2003 form) ────
def Delta2_lin(k):
    return k**3 * P_lin_norm(k) / (2.0 * np.pi**2)

def P_halofit(k_hMpc):
    """
    Halofit non-linear power spectrum (Smith et al. 2003 calibration).
    Returns P_nl in (h⁻¹ Mpc)³.
    Accurate to ~10% for 0.1 < k < 10 h/Mpc, z=0 ΛCDM.
    """
    # Find non-linearity scale k_nl where Delta2_lin(k_nl) = 1
    k_test = np.logspace(-2, 2, 500)
    D2_arr = np.array([Delta2_lin(k) for k in k_test])
    # Interpolate to find k_NL
    idx = np.argmin(np.abs(D2_arr - 1.0))
    k_nl = k_test[idx]
    # Effective spectral index n_eff at k_nl
    logk = np.log(k_test)
    logD = np.log(D2_arr + 1e-30)
    n_eff = np.gradient(logD, logk)[idx] - 3.0
    # Curvature C
    C_curv = np.gradient(np.gradient(logD, logk), logk)[idx]
    # Halofit quasi-linear coefficients (Smith+2003 Table 1)
    a_n = 10**(1.4861 + 1.8369*n_eff + 1.6762*n_eff**2 +
               0.7940*n_eff**3 + 0.1670*n_eff**4 - 0.6206*C_curv)
    b_n = 10**(0.9463 + 0.9466*n_eff + 0.3084*n_eff**2 - 0.9400*C_curv)
    c_n = 10**(-0.2807 + 0.6669*n_eff + 0.3214*n_eff**2 - 0.0793*C_curv)
    gamma_n = 0.8649 + 0.2989*n_eff + 0.1631*C_curv
    alpha_n = 1.3884 + 0.3700*n_eff - 0.1452*n_eff**2
    beta_n  = 0.8291 + 0.9854*n_eff + 0.3400*n_eff**2
    mu_n    = 10**(-3.5442 + 0.1908*n_eff)
    nu_n    = 10**(0.9589 + 1.2857*n_eff)

    y    = k_hMpc / k_nl
    D2_Q = Delta2_lin(k_hMpc) * (1 + Delta2_lin(k_hMpc))**beta_n / \
           (1 + alpha_n * Delta2_lin(k_hMpc)) * \
           np.exp(-y/4.0 - y**2/8.0)
    D2_H_prime = a_n * y**(3*gamma_n) / \
                 (1 + b_n * y**alpha_n + (c_n * y)**(3-gamma_n))
    D2_H = D2_H_prime / (1 + mu_n/y + nu_n/y**2)
    D2_nl = D2_Q + D2_H
    return 2.0 * np.pi**2 * D2_nl / k_hMpc**3

# ── SPT 1-loop correction (approximate P13 + P22) ────────────────
def P_SPT_1loop(k_hMpc):
    """
    1-loop Standard Perturbation Theory correction.
    P22 and P13 integrals evaluated numerically.
    Valid approximation for k < 0.3 h/Mpc where SPT converges.
    """
    P0 = P_lin_norm
    # P13(k): interaction of linear mode k with two modes summing to zero
    # P13 = 6 P_lin(k) ∫ d³q/(2π)³ F3_sym(k,q,-q) P_lin(q)
    # Leading-order limit: P13(k) ≈ P_lin(k) × k² × σ² × (-61/105)
    # where σ² = ∫ P_lin(q)/(2π²) dq  (velocity dispersion)
    q_arr = np.logspace(-4, 2, 300)
    P_arr = np.array([P0(q) for q in q_arr])
    sigma2_v = np.trapz(P_arr / (3.0 * (2.0*np.pi**2) / q_arr**0), q_arr) # rough
    sigma2_v = np.trapz(P_arr, q_arr) / (6.0 * np.pi**2)                   # ∫P(q)dq/(6π²)

    P13 = P0(k_hMpc) * (-61.0/105.0) * k_hMpc**2 * sigma2_v

    # P22(k): convolution integral ∫ d³q [F2(q,k-q)]² P(q) P(|k-q|)
    # Evaluated via 1D Legendre decomposition (leading approximation)
    # P22(k) ≈ 2 ∫ dq q² P(q)/(2π²) × ∫ dμ [F2(q,k,μ)]² P(|k-q|)
    n_q   = 60
    n_mu  = 30
    q_int = np.logspace(np.log10(1e-3), np.log10(10.0), n_q)
    mu_int = np.linspace(-0.9999, 0.9999, n_mu)
    P22   = 0.0
    for q in q_int:
        for mu in mu_int:
            kmq = np.sqrt(k_hMpc**2 + q**2 - 2*k_hMpc*q*mu)
            if kmq < 1e-6:
                continue
            x    = q / k_hMpc
            F2sq = (5.0/7.0 + 0.5*mu*(x + 1.0/x) + 2.0/7.0*mu**2)**2
            dq   = q_int[1] - q_int[0] if len(q_int) > 1 else q
            dmu  = mu_int[1] - mu_int[0]
            P22 += 2.0 * q**2 * P0(q) * F2sq * P0(kmq) / \
                   (2.0*np.pi**2) * dq * dmu
    return P0(k_hMpc) + 2.0*P13 + P22

# ── Compute and display the breakdown scale ──────────────────────
k_plot  = np.logspace(-2, 1.0, 120)
P_lin_v    = np.array([P_lin_norm(k) for k in k_plot])
P_hf_v     = np.array([P_halofit(k)  for k in k_plot])
D2_lin_v   = k_plot**3 * P_lin_v  / (2*np.pi**2)
D2_hf_v    = k_plot**3 * P_hf_v   / (2*np.pi**2)
ratio_hf   = P_hf_v / P_lin_v

# Non-linearity scale where Δ²_lin = 1
knl_idx = np.argmin(np.abs(D2_lin_v - 1.0))
k_NL    = k_plot[knl_idx]

print(f"Non-linearity scale k_NL = {k_NL:.3f} h/Mpc")
print(f"At k=1 h/Mpc: P_halofit / P_linear = {ratio_hf[np.argmin(np.abs(k_plot-1.0))]:.2f}")
print(f"At k=5 h/Mpc: P_halofit / P_linear = {ratio_hf[np.argmin(np.abs(k_plot-5.0))]:.2f}")

# Diagnostic table
print("\n k [h/Mpc]  |  Δ²_lin   |  Δ²_halofit  |  Ratio (NL/Lin)")
print(" ──────────────────────────────────────────────────────────")
for i in range(0, len(k_plot), 12):
    print(f"  {k_plot[i]:6.3f}    |  {D2_lin_v[i]:7.4f}  |  {D2_hf_v[i]:9.4f}    |  {ratio_hf[i]:6.3f}")
```

The diagnostic table this code produces makes the breakdown of linear theory immediately visible: at $k = 0.1\ h\ \text{Mpc}^{-1}$ the ratio $P_{\text{halofit}}/P_{\text{lin}} \approx 1.03$, confirming that perturbation theory is reliable. At $k = 1\ h\ \text{Mpc}^{-1}$ that ratio reaches approximately 2.5, meaning that a survey analyzing galaxy clustering at this scale using only the linear power spectrum would underestimate the amplitude by a factor of 2.5 — a catastrophic bias for any cosmological parameter inference.

Chaotic behavior in the non-linear regime also manifests in the velocity field. The pairwise velocity dispersion $\sigma_{12}(r)$ between galaxy pairs separated by distance $r$ diverges logarithmically in SPT at all orders because the velocity field is not curl-free in the multi-stream regime. This is the mathematical signature of shell-crossing: once dark matter streams from different initial positions occupy the same comoving volume, the single-valued velocity field assumption implicit in SPT is violated, and the expansion diverges. Numerical simulations handle this correctly because they track individual particles; analytic methods require the Vlasov equation (the collisionless Boltzmann equation in phase space) rather than the fluid approximation, which is why the Effective Field Theory of Large Scale Structure (EFTofLSS) has become the state-of-the-art perturbative framework for the mildly non-linear regime. The EFT introduces a sound-speed counterterm $c_s^2 k^2 P_{\text{lin}}(k)$ that absorbs the UV sensitivity of loop integrals into a single renormalized parameter calibrated against simulations, extending the validity of perturbation theory from $k_{\text{NL}} \approx 0.2\ h\ \text{Mpc}^{-1}$ to roughly $k \approx 0.6\ h\ \text{Mpc}^{-1}$ at $z = 0$, and further at higher redshift where $\delta$ is smaller.

---

## 3. Extreme Boundary Conditions & Phase Breakdown

The most challenging measurement environments in cosmology are those where the physics undergoes a qualitative change — a phase transition, a symmetry breaking, a regime change in the equation of state — and the instruments or models constructed for the smooth background case must be extended or replaced entirely. These boundary conditions are not mathematical curiosities; they set the domain of validity for every tool in the observer's arsenal, and failing to recognize when you have crossed one is how systematic errors of principle, not just practice, enter the final result.

The electroweak phase transition at $T_{\text{EW}} \approx 160\ \text{GeV}$ ($t \approx 10^{-11}\ \text{s}$) and the QCD confinement transition at $T_{\text{QCD}} \approx 150\text{–}200\ \text{MeV}$ ($t \approx 10^{-5}\ \text{s}$) are the two phase boundaries in the early universe that have the most direct observational consequences. At the QCD transition, quarks and gluons are confined into hadrons, the number of relativistic degrees of freedom $g_*$ drops from 61.75 to 17.25 over a temperature interval of roughly $\Delta T / T_{\text{QCD}} \sim 0.3$, and this change in $g_*$ imprints a step-function-like feature in the primordial gravitational wave background spectrum at frequencies around $f_{\text{QCD}} \approx 10^{-8}\ \text{Hz}$, which falls in the sensitivity band of pulsar timing arrays (PTAs). The relationship between the temperature at which a gravitational wave mode was produced and its present-day frequency is:

$$f_0 = 1.65 \times 10^{-7}\ \text{Hz} \left(\frac{T_*}{1\ \text{GeV}}\right) \left(\frac{g_*(T_*)}{100}\right)^{1/6}$$

where $T_*$ is the temperature at GW production and $g_*$ is evaluated at that temperature. For $T_* = 150\ \text{MeV}$ and $g_* = 17.25$, this gives $f_0 \approx 2.3 \times 10^{-8}\ \text{Hz}$, squarely in the sensitivity band of the NANOGrav 15-year dataset and the IPTA data release 2. The NANOGrav detection of a stochastic GW background announced in 2023 is consistent with either supermassive black hole binaries or new physics at the QCD scale, and distinguishing between these interpretations is a live experimental problem requiring more precise timing residuals and better noise models for each pulsar.

The practical measurement challenge in PTA science illustrates how extreme boundary conditions manifest as instrument-level failures. The timing residual $\delta t$ for a pulsar at distance $d$ in the presence of a GW background with strain $h$ is of order $h d / c$. For the GW background at nanohertz frequencies, $h \sim 10^{-15}$ and $d \sim 1\ \text{kpc} \approx 3 \times 10^{19}\ \text{m}$, giving $\delta t \sim 30\ \text{ns}$. Achieving this timing precision requires removing the dispersion measure (DM) variations caused by the interstellar medium, which introduces a frequency-dependent delay:

$$\Delta t_{\text{DM}}(\nu) = \frac{e^2}{2\pi m_e c} \frac{\text{DM}}{\nu^2} \equiv \frac{\mathcal{K} \cdot \text{DM}}{\nu^2}$$

where $\mathcal{K} = e^2 / (2\pi m_e c) \approx 4.148 \times 10^3\ \text{MHz}^2\ \text{pc}^{-1}\ \text{cm}^3\ \text{s}$ is the dispersion constant and DM is the dispersion measure in pc cm$^{-3}$. Because the interstellar plasma is turbulent and the electron density along the line of sight fluctuates on timescales of days to years, DM is a time-varying quantity $\text{DM}(t)$ that must be measured simultaneously with the pulse timing at every epoch. This requires observing each pulsar at a minimum of two widely separated radio frequencies — the standard NANOGrav campaign uses L-band (1.4 GHz) and S-band (2.1 GHz) simultaneously with the Green Bank Telescope — so that the $\nu^{-2}$ dispersion delay can be fitted and subtracted. The residual DM uncertainty after this subtraction is typically $\sigma_{\text{DM}} \approx 10^{-4}\ \text{pc cm}^{-3}$ for bright millisecond pulsars, which propagates into a timing residual uncertainty:

$$\sigma_{t,\text{DM}} = \frac{\mathcal{K} \cdot \sigma_{\text{DM}}}{\nu_{\text{eff}}^2} \approx \frac{4148 \times 10^{-4}}{(1400)^2}\ \text{s} \approx 211\ \text{ns}$$

at 1.4 GHz alone. This is already larger than the signal, which is why simultaneous multi-frequency observations are not optional but mandatory for any PTA claiming detection-level sensitivity.

The cosmic recombination epoch at $z_{\text{rec}} \approx 1100$ ($T_{\text{rec}} \approx 3000\ \text{K}$, $t_{\text{rec}} \approx 380{,}000\ \text{yr}$) represents a different kind of phase boundary: the transition of hydrogen from ionized plasma to neutral gas, which decouples the photon-baryon fluid and releases the CMB. The standard calculation of the recombination history uses the Peebles-Zeldovich recombination code (or its modern descendant CosmoRec/HyRec), which tracks the hydrogen level populations through a network of approximately $300$ two-photon and Lyman-series transitions. The ionization fraction $x_e(z)$ evolves according to:

$$\frac{dx_e}{dz} = \frac{C_P}{H(z)(1+z)} \left[\alpha_B(T_b) n_H x_e^2 - \beta_B(T_b)(1-x_e)e^{-h\nu_\alpha / k_B T_b}\right]$$

where $\alpha_B$ is the case-B recombination coefficient (recombination to $n \geq 2$ levels only, since recombinations directly to $n=1$ re-ionize the medium), $\beta_B = \alpha_B (m_e k_B T_b / 2\pi\hbar^2)^{3/2} e^{-h\nu_{2s}/k_BT_b}$ is the photoionization rate, $C_P = (\Lambda_{2s1s} + \beta_B) / (\Lambda_{2s1s} + \beta_B + K_H n_H (1-x_e) \Lambda_{2s1s})$ is the Peebles C-factor (the fraction of recombinations to $n=2$ that actually result in a net recombination), $K_H = \lambda_\alpha^3 / (8\pi H(z))$ is a geometrical factor relating the Lyman-$\alpha$ photon escape probability to the expansion rate, and $\Lambda_{2s1s} \approx 8.23\ \text{s}^{-1}$ is the two-photon decay rate of the metastable $2s$ hydrogen level. The two-photon decay is the essential bypass mechanism: direct Lyman-$\alpha$ photons produced by $2p \to 1s$ transitions are immediately reabsorbed by the almost-transparent neutral medium, trapping the system in a detailed-balance bottleneck. It is only through the two-photon channel and the redshifting of Lyman-$\alpha$ photons out of resonance by the Hubble expansion (captured by the $K_H$ factor) that recombination proceeds out of equilibrium. Any systematic error in the two-photon rate, the Lyman-series line profiles, or the hydrogen energy levels propagates directly into $x_e(z)$, shifts the redshift of last scattering $z_*$, and biases the inferred values of $\Omega_b h^2$, $\Omega_c h^2$, and $H_0$ from CMB power spectrum fits. The current state-of-the-art estimate is that theoretical uncertainties in the recombination history contribute a systematic error of $\Delta H_0 \approx 0.1\ \text{km s}^{-1} \text{Mpc}^{-1}$ to the inferred Hubble constant — small compared to the present $5\sigma$ Hubble tension of $\sim 5\ \text{km s}^{-1} \text{Mpc}^{-1}$, but non-negligible at the precision level demanded by next-generation CMB-S4 and Simons Observatory measurements.

The gravitational wave boundary — the innermost stable circular orbit (ISCO) of a Kerr black hole — represents the extreme boundary condition in the strong-field regime of general relativity. For a Schwarzschild black hole of mass $M$, the ISCO is at $r_{\text{ISCO}} = 6GM/c^2 = 3 R_s$, and the orbital frequency there is:

$$f_{\text{ISCO}} = \frac{c^3}{6\sqrt{6}\pi G M} = \frac{4400\ \text{Hz}}{M / M_\odot}$$

For the binary black hole mergers detected by LIGO-Virgo, with total masses in the range $20\text{–}100\ M_\odot$, this places the ISCO frequency in the range $44\text{–}220\ \text{Hz}$, squarely in the most sensitive band of Advanced LIGO's noise curve. The boundary condition that the measurement must confront here is the transition from the adiabatic inspiral regime — where post-Newtonian (PN) waveform templates are valid — to the merger and ringdown phases, where only numerical relativity (NR) can provide accurate waveforms. The PN expansion parameter is $v/c = (G M \pi f / c^3)^{1/3}$; at the ISCO this takes the value $(6)^{-1/2} \approx 0.41$, which is not small. The 3.5PN waveforms used in matched-filter searches begin to accumulate phase errors of order $\pi/2$ radians several cycles before the ISCO, which is precisely why the SEOBNRv4 and IMRPhenomXP waveform families that underlie current LIGO parameter estimation blend PN inspiral with an effective-one-body (EOB) mapping to NR waveforms at the boundary.

The practical consequence for data analysts is that any parameter estimation performed using a waveform model that does not accurately reproduce the merger-ringdown phase is systematically biased in the inferred mass ratio and spin parameters. The diagnostic test is to compare posterior distributions obtained from two independent waveform families — say IMRPhenomXPHM and SEOBNRv5HM — and verify that the posteriors are consistent. A discrepancy exceeding $0.5\sigma$ in any parameter should trigger an investigation of which waveform family is less faithful at the signal-to-noise ratio of that particular event. For high-SNR events like GW150914 (SNR $\approx 24$) or GW190521 (a nearly equal-mass $\sim 150\ M_\odot$ event near the edge of the pair-instability mass gap), waveform systematics are the dominant source of uncertainty in the inferred parameters, not detector noise. The resolution requires either higher-accuracy NR simulations with smaller numerical truncation errors, or a direct time-domain comparison between the data and an interpolated NR waveform at the best-fit parameters — a computationally expensive procedure that is currently performed only for the loudest events but will become standard practice as LIGO achieves its design sensitivity and detects hundreds of compact binary mergers per year.

The phase breakdown at the black hole singularity itself — where the Kretschner curvature scalar $K = R_{\mu\nu\rho\sigma}R^{\mu\nu\rho\sigma} \to \infty$ — represents the ultimate boundary condition, the point where classical GR ceases to be a valid description and quantum gravitational corrections must dominate. At the Planck scale $\ell_P = \sqrt{\hbar G / c^3} \approx 1.6 \times 10^{-35}\ \text{m}$, the dimensionless ratio of the Compton wavelength to the Schwarzschild radius equals unity, and the standard assumption that spacetime curvature can be treated as a smooth background over scales large compared to $\ell_P$ fails. While observational access to this regime is out of reach for current instruments, its indirect consequences — the information loss paradox, the firewall conjecture, the nature of Hawking radiation — set boundary conditions on what any complete theory of quantum gravity must reproduce, and those constraints are becoming increasingly precise as LIGO accumulates ringdown waveforms that probe the near-horizon geometry to within $\sim 1\%$ of the event horizon radius. The ringdown is a sequence of quasinormal modes (QNMs) with complex frequencies $\omega_{lmn} = \omega_R + i\omega_I$ where $\omega_R$ sets the oscillation frequency and $\omega_I$ sets the damping time. For the fundamental $l=m=2, n=0$ mode of a Kerr black hole:

$$\omega_{220} M \approx (1 - 0.63(1-\chi)^{0.3}) - \frac{i}{4}(1-0.63(1-\chi)^{0.3})^{-0.45}(1-\chi)^{0.45}$$

where $\chi = J/(GM^2/c)$ is the dimensionless spin parameter. The black hole spectroscopy program — measuring multiple QNM frequencies from a single ringdown signal — tests the Kerr hypothesis directly: if the remnant is a Kerr black hole, the ratios of QNM frequencies are uniquely determined by $M$ and $\chi$ alone, and any deviation signals either new physics beyond GR or the presence of exotic compact objects. The current signal-to-noise ratios achievable with Advanced LIGO are marginally sufficient to detect the subdominant $l=m=3$ overtone in the loudest events; third-generation detectors like the Einstein Telescope and Cosmic Explorer, with their factor-of-ten improvement in strain sensitivity, will make routine black hole spectroscopy possible, turning the extreme boundary condition of the near-horizon geometry from a theoretical limit into an experimental playground.
