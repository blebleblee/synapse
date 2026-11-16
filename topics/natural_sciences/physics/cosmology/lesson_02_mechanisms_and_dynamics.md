# Lesson 2: Physical Mechanisms & Dynamical Equations

## 1. Governing Differential Equations & Analytical Derivations

The universe does not evolve arbitrarily. Its geometry, matter content, and energy density are locked together by a set of differential equations so tightly constrained that specifying the state of the cosmos at one moment determines its entire past and future trajectory, up to quantum uncertainties that become cosmologically relevant only in the Planck epoch. Understanding those equations — not as abstract symbols but as instruments that practicing cosmologists calibrate against supernova light curves, baryon acoustic oscillation peaks, and CMB power spectra — is the central technical skill this lesson develops.

### The Friedmann Framework as an Equation of Motion

General relativity describes spacetime as a dynamical field governed by Einstein's field equations,

$$G_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu},$$

where $G_{\mu\nu} = R_{\mu\nu} - \frac{1}{2} R g_{\mu\nu}$ is the Einstein tensor encoding spacetime curvature, $\Lambda$ is the cosmological constant, $g_{\mu\nu}$ is the metric tensor, $T_{\mu\nu}$ is the stress-energy tensor of all matter and radiation fields, $G$ is Newton's gravitational constant, and $c$ is the speed of light. For a universe that is homogeneous and isotropic on scales larger than roughly 100 Mpc — an assumption confirmed to one part in $10^5$ by the CMB temperature anisotropy spectrum — the most general metric consistent with these symmetries is the Friedmann–Lemaître–Robertson–Walker (FLRW) line element,

$$ds^2 = -c^2 dt^2 + a(t)^2 \left[ \frac{dr^2}{1 - k r^2} + r^2 d\Omega^2 \right],$$

where $a(t)$ is the dimensionless scale factor normalized so that $a(t_0) = 1$ at the present epoch $t_0$, $r$ is the comoving radial coordinate, $k \in \{-1, 0, +1\}$ encodes spatial curvature (open, flat, closed), and $d\Omega^2 = d\theta^2 + \sin^2\theta\, d\phi^2$ is the metric on the unit two-sphere. Substituting this metric into Einstein's equations and treating the cosmic fluid as a perfect fluid with energy density $\rho(t)$ and isotropic pressure $P(t)$ yields two independent dynamical equations.

The first, the **Friedmann equation**, comes from the time-time component $G_{00}$:

$$H^2 \equiv \left(\frac{\dot{a}}{a}\right)^2 = \frac{8\pi G}{3}\rho - \frac{kc^2}{a^2} + \frac{\Lambda c^2}{3},$$

where $H \equiv \dot{a}/a$ is the Hubble parameter, whose present value $H_0 \approx 67.4\ \text{km s}^{-1}\text{Mpc}^{-1}$ (Planck 2018) anchors the entire distance ladder. The second equation, the **acceleration equation** or Raychaudhuri equation, comes from the space-space component $G_{ii}$:

$$\frac{\ddot{a}}{a} = -\frac{4\pi G}{3}\left(\rho + \frac{3P}{c^2}\right) + \frac{\Lambda c^2}{3}.$$

These two equations are not independent — given an equation of state relating $P$ to $\rho$, one implies the other up to an integration constant fixed by initial conditions. Their combination through $\dot{\rho} + 3H(\rho + P/c^2) = 0$ is the **fluid equation** (or continuity equation), which expresses local energy-momentum conservation $\nabla_\mu T^{\mu\nu} = 0$ in the FLRW background. This is the equation that practicing cosmologists use most directly when modeling the dilution of different energy components across cosmic time, and it is worth internalizing its physical content before proceeding.

### Equation of State and Component Scaling

The equation of state parameter $w$ defined by $P = w \rho c^2$ determines how each energy component scales with the scale factor. Substituting into the fluid equation gives

$$\dot{\rho} = -3H\rho(1 + w),$$

which integrates immediately to

$$\rho \propto a^{-3(1+w)}.$$

For non-relativistic matter (pressureless dust), $w = 0$ and $\rho_m \propto a^{-3}$: the energy density falls as the inverse of the comoving volume, exactly as expected when particle number is conserved and particles are diluted by expansion. For radiation, $w = 1/3$ and $\rho_r \propto a^{-4}$: the extra factor of $a^{-1}$ beyond mere dilution comes from the cosmological redshift of each photon's energy, $E = hc/\lambda \propto a^{-1}$. For a cosmological constant, $w = -1$ and $\rho_\Lambda = \text{const}$: energy density is unchanged as the universe expands, which is the defining characteristic that drives accelerated expansion. Dark energy with $w \neq -1$ can be modeled as a slowly rolling scalar field (quintessence), but current observational constraints from the Dark Energy Survey and Planck place $w = -1.03 \pm 0.03$, consistent with $\Lambda$.

Practitioners define the density parameters $\Omega_i \equiv \rho_i / \rho_c$ where the critical density $\rho_c \equiv 3H^2 / 8\pi G$ is the density required for spatial flatness at a given epoch. The Friedmann equation then becomes a constraint among present-day values:

$$\Omega_m + \Omega_r + \Omega_\Lambda + \Omega_k = 1,$$

where $\Omega_k \equiv -kc^2 / (a^2 H^2)$ parameterizes spatial curvature. Planck 2018 results give $\Omega_m \approx 0.315$, $\Omega_\Lambda \approx 0.685$, $\Omega_r \approx 9 \times 10^{-5}$, and $|\Omega_k| < 0.005$, confirming a spatially flat, dark energy dominated cosmos to high precision.

### Solving the Friedmann Equation Numerically

Understanding the analytical scaling laws is necessary but not sufficient for research practice. Real data analysis requires integrating the Friedmann equation numerically to compute comoving distances, angular diameter distances, and luminosity distances as a function of redshift $z$, where $1 + z = a_0 / a = 1/a$ for $a_0 = 1$. The comoving distance to a source at redshift $z$ is

$$\chi(z) = \frac{c}{H_0} \int_0^z \frac{dz'}{E(z')},$$

where the dimensionless Hubble function $E(z)$ packages the matter, radiation, and dark energy densities:

$$E(z) \equiv \frac{H(z)}{H_0} = \sqrt{\Omega_m(1+z)^3 + \Omega_r(1+z)^4 + \Omega_\Lambda + \Omega_k(1+z)^2}.$$

The luminosity distance $d_L = (1+z)\chi(z)$ and angular diameter distance $d_A = \chi(z)/(1+z)$ follow immediately. These are the quantities that enter supernova standard candle analysis (Type Ia SNe measure $d_L(z)$) and BAO standard ruler analysis (galaxy surveys measure $d_A(z)/r_s$ and $H(z) r_s$, where $r_s$ is the sound horizon at drag epoch). The following Python code integrates $E(z)$ using `scipy.integrate.quad` and reproduces the $\Lambda$CDM distance-redshift relation to percent-level accuracy over $0 \leq z \leq 10$:

```python
import numpy as np
from scipy.integrate import quad
import matplotlib.pyplot as plt

# Planck 2018 flat ΛCDM parameters
H0 = 67.4           # km/s/Mpc
c  = 2.998e5        # km/s
Om = 0.315          # matter density parameter
Or = 9.0e-5         # radiation density parameter
OL = 1.0 - Om - Or  # cosmological constant (flat universe: Omega_k = 0)

def E(z):
    """Dimensionless Hubble function E(z) = H(z)/H0."""
    return np.sqrt(Om * (1+z)**3 + Or * (1+z)**4 + OL)

def comoving_distance(z):
    """Comoving distance chi(z) in Mpc."""
    integrand = lambda zp: 1.0 / E(zp)
    result, _ = quad(integrand, 0, z)
    return (c / H0) * result

def luminosity_distance(z):
    """Luminosity distance d_L(z) in Mpc."""
    return (1 + z) * comoving_distance(z)

def angular_diameter_distance(z):
    """Angular diameter distance d_A(z) in Mpc."""
    return comoving_distance(z) / (1 + z)

# Compute over a redshift grid
z_arr = np.linspace(0.01, 5.0, 500)
chi   = np.array([comoving_distance(z) for z in z_arr])
dL    = np.array([luminosity_distance(z) for z in z_arr])
dA    = np.array([angular_diameter_distance(z) for z in z_arr])

# Distance modulus mu = 5 log10(dL/10 pc) = 5 log10(dL * 1e6 / 10)
mu = 5.0 * np.log10(dL * 1e6 / 10.0)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].plot(z_arr, dL, label=r'$d_L$ (luminosity)', color='steelblue')
axes[0].plot(z_arr, chi, label=r'$\chi$ (comoving)',  color='darkorange')
axes[0].plot(z_arr, dA, label=r'$d_A$ (angular diam)', color='forestgreen')
axes[0].set_xlabel('Redshift $z$', fontsize=12)
axes[0].set_ylabel('Distance (Mpc)', fontsize=12)
axes[0].set_title(r'$\Lambda$CDM Distance Measures', fontsize=13)
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(z_arr, mu, color='crimson')
axes[1].set_xlabel('Redshift $z$', fontsize=12)
axes[1].set_ylabel(r'Distance modulus $\mu$', fontsize=12)
axes[1].set_title('Hubble Diagram ($\Lambda$CDM)', fontsize=13)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('lcdm_distances.pdf', dpi=150)
plt.show()

# Print benchmark values for validation against Ned Wright's calculator
for z_test in [0.1, 0.5, 1.0, 2.0]:
    print(f"z={z_test:.1f}: chi={comoving_distance(z_test):.1f} Mpc, "
          f"dL={luminosity_distance(z_test):.1f} Mpc, "
          f"mu={5*np.log10(luminosity_distance(z_test)*1e6/10):.3f}")
```

Running this code and cross-checking the printed $\chi$, $d_L$, and $\mu$ values against Ned Wright's publicly available Cosmology Calculator (or the `astropy.cosmology` module with `Planck18` preset) is a standard validation step before using any custom cosmological pipeline. The agreement should be better than 0.1% for $z \leq 5$; discrepancies larger than that indicate a numerical integration step size issue or an error in the $\Omega$ parameters.

### Inflation: The Scalar Field Equation of Motion

Before the radiation-dominated epoch, the universe underwent a period of exponential expansion driven by a nearly uniform scalar field $\phi$ — the inflaton — rolling slowly down a nearly flat potential $V(\phi)$. The action for a minimally coupled scalar field in a curved spacetime is

$$S = \int d^4x \sqrt{-g} \left[ \frac{M_{\rm Pl}^2}{2} R - \frac{1}{2}(\partial_\mu \phi)^2 - V(\phi) \right],$$

where $M_{\rm Pl} = (8\pi G)^{-1/2} \approx 2.435 \times 10^{18}\ \text{GeV}$ is the reduced Planck mass and $R$ is the Ricci scalar. Varying with respect to $\phi$ in the FLRW background gives the **Klein-Gordon equation** for the homogeneous inflaton:

$$\ddot{\phi} + 3H\dot{\phi} + V'(\phi) = 0,$$

where $V'(\phi) \equiv dV/d\phi$ and the $3H\dot{\phi}$ term acts as a Hubble friction that slows the field's roll. The energy density and pressure of the scalar field are

$$\rho_\phi = \frac{1}{2}\dot{\phi}^2 + V(\phi), \qquad P_\phi = \frac{1}{2}\dot{\phi}^2 - V(\phi).$$

The **slow-roll approximation** holds when the kinetic energy is negligible compared to the potential energy, $\frac{1}{2}\dot{\phi}^2 \ll V(\phi)$, and the acceleration $\ddot{\phi}$ is negligible compared to the friction term. This double condition is quantified by the slow-roll parameters

$$\epsilon \equiv -\frac{\dot{H}}{H^2} = \frac{\dot{\phi}^2}{2 M_{\rm Pl}^2 H^2}, \qquad \eta \equiv \frac{\dot{\epsilon}}{H\epsilon},$$

or equivalently in potential form:

$$\epsilon_V \equiv \frac{M_{\rm Pl}^2}{2}\left(\frac{V'}{V}\right)^2, \qquad \eta_V \equiv M_{\rm Pl}^2 \frac{V''}{V}.$$

Inflation requires $\epsilon \ll 1$ (so that $\rho_\phi \approx V(\phi)$ drives near-de Sitter expansion) and ends when $\epsilon \approx 1$. The number of e-folds of inflation is $N = \int H\, dt = \int_{\phi_{\rm end}}^{\phi_*} \frac{V}{M_{\rm Pl}^2 V'} d\phi$, and the observational requirement that large-scale structure forms correctly from inflationary perturbations demands $N \approx 50$–$60$ e-folds between the pivot scale leaving the horizon and reheating.

---

## 2. Microscopic vs. Macroscopic Phase Transitions

Cosmic history is punctuated by phase transitions — moments when the smooth thermal evolution of a near-equilibrium plasma gives way to sudden qualitative changes in the state of matter. These transitions are not metaphors; they are concrete thermodynamic events that left imprints still measurable today, from the baryon-to-photon ratio to the acoustic peaks in the CMB to the large-scale topology of the cosmic web.

### The Big Bang Nucleosynthesis Transition: A Nuclear Rate Equation

The synthesis of light elements (BBN) occurred between roughly $t \approx 1\text{ s}$ and $t \approx 300\text{ s}$ after the Big Bang, when the temperature of the universe fell from $\sim 10\ \text{MeV}$ through $\sim 0.07\ \text{MeV}$. This is not a phase transition in the thermodynamic sense of spontaneous symmetry breaking, but it is a kinetic transition: the rates of weak interaction processes that interconvert neutrons and protons fall below the Hubble expansion rate, freezing the neutron-to-proton ratio at a value that determines the ultimate helium abundance.

At temperatures $T \gtrsim 1\ \text{MeV}$, neutrons and protons are held in equilibrium by the charged-current weak reactions $n + \nu_e \leftrightarrow p + e^-$ and $n + e^+ \leftrightarrow p + \bar{\nu}_e$. In equilibrium, the neutron-to-proton ratio follows the Boltzmann factor,

$$\frac{n_n}{n_p} = \exp\left(-\frac{\Delta m c^2}{k_B T}\right),$$

where $\Delta m c^2 = (m_n - m_p)c^2 \approx 1.293\ \text{MeV}$ is the neutron-proton mass difference. The weak interaction rate scales as $\Gamma_{\rm weak} \sim G_F^2 T^5$, where $G_F \approx 1.166 \times 10^{-5}\ \text{GeV}^{-2}$ is the Fermi constant. The Hubble rate during the radiation epoch scales as $H \sim T^2 / M_{\rm Pl}$. Freeze-out occurs when $\Gamma_{\rm weak} \sim H$, which gives a freeze-out temperature

$$T_{\rm fo} \sim \left(\frac{M_{\rm Pl} G_F^{-2}}{1}\right)^{1/3} \approx 0.8\ \text{MeV},$$

at which the neutron fraction is $X_n \equiv n_n/(n_n + n_p) \approx 1/7$. After freeze-out, neutrons decay with a half-life $\tau_{1/2} \approx 611\ \text{s}$, reducing $X_n$ slightly before helium forms. The final helium mass fraction is

$$Y_P \approx 2 X_n \approx 0.247,$$

in excellent agreement with the primordial helium abundance inferred from observations of extremely metal-poor HII regions: $Y_P^{\rm obs} = 0.2449 \pm 0.0040$ (Aver et al. 2015). The sensitivity of $Y_P$ to the neutron lifetime, the number of light neutrino species $N_\nu$, and the baryon-to-photon ratio $\eta_b = n_b / n_\gamma$ makes BBN the earliest quantitatively predictive laboratory in cosmology, and practitioners use public codes like `AlterBBN` and `PArthENoPE` to compute light element abundances as functions of $\eta_b$ and $N_\nu$ when confronting observational data.

### The QCD Phase Transition

At temperatures around $T_{\rm QCD} \approx 150$–$170\ \text{MeV}$, occurring at $t \approx 10\ \mu\text{s}$ after the Big Bang, QCD matter underwent the transition from a quark-gluon plasma (QGP) — a deconfined soup of quarks and gluons moving quasi-freely over distances much larger than the nucleon size — to a confined phase of hadrons. Lattice QCD calculations at finite temperature and zero baryon chemical potential show that this transition is a smooth **crossover** rather than a first-order phase transition at the baryon densities relevant to the early universe. The Polyakov loop $\langle L \rangle$, which acts as an order parameter for deconfinement in the pure-gauge theory, rises smoothly from near zero to near unity over a temperature range of roughly $\pm 10\%$ around $T_{\rm QCD}$.

The cosmological significance of the QCD transition lies in its effect on the number of effective relativistic degrees of freedom $g_*(T)$, which determines the energy density of the radiation bath:

$$\rho_r = \frac{\pi^2}{30} g_*(T) T^4.$$

Above $T_{\rm QCD}$, the QGP contributes $g_* \approx 106.75$ (counting all Standard Model particles). Below $T_{\rm QCD}$, the quarks and gluons are confined into pions and other hadrons, and $g_*$ drops sharply to $\approx 10.75$ (photons, three neutrino species, electrons). This sudden reduction in degrees of freedom causes the temperature to rise slightly (the radiation bath reheats itself as entropy is deposited into photons) and alters the Hubble rate, with observable consequences for the axion dark matter window and gravitational wave backgrounds from first-order extensions of the Standard Model.

Experimentally, the ALICE experiment at CERN's LHC recreates QGP conditions in heavy-ion collisions at $\sqrt{s_{NN}} \approx 5.02\ \text{TeV}$, measuring the crossover through charmonium suppression ($J/\psi$ yields), elliptic flow coefficients $v_2$, and the equation of state extracted from hadron spectra. Mapping these terrestrial measurements onto cosmological initial conditions requires care — LHC collisions are small, transient, and baryon-rich compared to the early universe — but the QCD coupling constant extracted from both sources must agree, and it does.

### Recombination and Photon Decoupling: A Multi-Level Atom Problem

At $z_{\rm rec} \approx 1100$ ($T \approx 0.3\ \text{eV}$, $t \approx 380{,}000\ \text{yr}$), hydrogen recombination converted the cosmos from an opaque plasma to a transparent neutral gas and released the photons now observed as the CMB. The equilibrium Saha equation for the neutral hydrogen fraction $X_e = n_e / (n_e + n_H)$ is

$$\frac{X_e^2}{1 - X_e} = \frac{1}{n_b} \left(\frac{m_e k_B T}{2\pi \hbar^2}\right)^{3/2} \exp\left(-\frac{E_I}{k_B T}\right),$$

where $E_I = 13.6\ \text{eV}$ is the hydrogen ionization energy and $n_b$ is the baryon number density. The Saha equation predicts that $X_e$ drops from $\sim 1$ to $\sim 10^{-4}$ over a temperature interval of a few thousand Kelvin. However, the Saha equation is an equilibrium result, and the actual recombination process is **out of equilibrium** because direct recombination to the ground state produces an ionizing photon that immediately re-ionizes a neighboring atom. Efficient recombination must proceed through excited states: either via the two-photon decay $2s \to 1s + 2\gamma$ (rate $\Lambda_{2\gamma} = 8.22\ \text{s}^{-1}$) or via Lyman-$\alpha$ escape. This is captured by the Peebles rate equation,

$$\frac{dX_e}{dt} = \mathcal{C} \left[\beta(T)(1 - X_e) - n_H \alpha^{(2)}(T) X_e^2 \right],$$

where $\alpha^{(2)}(T)$ is the case-B recombination coefficient (recombinations to all states except the ground state), $\beta(T) = \alpha^{(2)}(T)(m_e k_B T / 2\pi\hbar^2)^{3/2} e^{-E_{2s}/k_BT}$ is the photoionization rate from the $2s$ level, and $\mathcal{C}$ is the Peebles $\mathcal{C}$-factor accounting for the probability that an excited hydrogen atom decays to the ground state before being re-ionized by a thermal photon. The modern treatment implemented in `RECFAST` and `HyRec` extends this to multi-level atoms with hundreds of hydrogen and helium shell states, achieving sub-percent accuracy in $X_e(z)$ necessary for precision CMB power spectrum computation.

The photon mean free path grows as recombination proceeds and $X_e$ drops, reaching the Hubble radius at $z_* \approx 1090$, defining the **last scattering surface** (LSS). The thickness of the LSS is not infinitesimal — recombination spans $\Delta z \approx 80$ in redshift — and this finite thickness damps CMB anisotropies on angular scales smaller than $\ell \sim 1000$ through Silk damping, the diffusion of photons across density perturbations during the recombination epoch.

---

## 3. Energy Transfer, Entropy & Rate Limitations

Cosmological evolution is fundamentally a story about how energy moves between components, how entropy is generated and conserved, and when the rates of physical processes become too slow to maintain equilibrium. Each of these themes has a precise mathematical expression and a direct observational consequence.

### Entropy Conservation and the Thermodynamics of the Radiation Bath

In the absence of entropy-generating processes, the comoving entropy density $s a^3$ is conserved. The entropy density of the thermal plasma is

$$s = \frac{2\pi^2}{45} g_{*S}(T) T^3,$$

where $g_{*S}$ is the effective number of degrees of freedom contributing to entropy (which tracks $g_*$ but weights species by temperature when different sectors decouple). Conservation of comoving entropy, $d(s a^3)/dt = 0$, gives

$$s a^3 = \frac{2\pi^2}{45} g_{*S} (aT)^3 = \text{const},$$

which means that the product $g_{*S}^{1/3} aT$ is conserved. This is the precise statement of "adiabatic expansion": when $g_{*S}$ is constant, $aT = \text{const}$ and the photon temperature simply redshifts as $T \propto a^{-1}$. But when $g_{*S}$ decreases — for example, when $e^+e^-$ pairs annihilate at $T \sim 0.5\ \text{MeV}$ and deposit their entropy into photons — the photon temperature receives a boost relative to the neutrino temperature. The neutrinos have already decoupled at $T_{\nu,\rm dec} \approx 2\ \text{MeV}$ and do not share in this entropy injection, so the photon-to-neutrino temperature ratio becomes

$$\frac{T_\gamma}{T_\nu} = \left(\frac{11}{4}\right)^{1/3} \approx 1.401,$$

a result that enters the precise calculation of the effective number of relativistic species $N_{\rm eff} = 3.044$ (including QED corrections to photon-electron interactions) and is probed by CMB polarization and spectral distortion measurements.

### The Boltzmann Equation and Freeze-Out

The evolution of the number density $n_\chi$ of a species $\chi$ in an expanding universe is governed by the Boltzmann equation. For a particle species undergoing pair annihilation $\chi\bar{\chi} \to \text{SM SM}$ with thermally averaged annihilation cross section $\langle\sigma v\rangle$, the Boltzmann equation in the FLRW background takes the form

$$\frac{dn_\chi}{dt} + 3H n_\chi = -\langle\sigma v\rangle \left(n_\chi^2 - n_{\chi,{\rm eq}}^2\right),$$

where $n_{\chi,{\rm eq}}$ is the equilibrium number density. The left side describes the dilution of number density by Hubble expansion; the right side accounts for annihilation (which decreases $n_\chi$ when $n_\chi > n_{\chi,{\rm eq}}$) and pair creation from the thermal bath (which increases $n_\chi$ when $n_\chi < n_{\chi,{\rm eq}}$). It is convenient to work with the yield $Y \equiv n_\chi / s$ (number per comoving entropy) and the inverse temperature $x \equiv m_\chi c^2 / k_B T$, transforming the Boltzmann equation to

$$\frac{dY}{dx} = -\frac{\langle\sigma v\rangle s}{H x} (Y^2 - Y_{\rm eq}^2).$$

**Chemical freeze-out** occurs when the annihilation rate $\Gamma_{\rm ann} = n_\chi \langle\sigma v\rangle$ falls below $H$, at which point $n_\chi$ can no longer track the exponentially falling $n_{\chi,{\rm eq}}$ and the comoving abundance freezes to a constant relic value $Y_\infty$. The relic density today is

$$\Omega_\chi h^2 = \frac{m_\chi s_0 Y_\infty}{\rho_{c,0}/h^2} \approx \frac{1.07 \times 10^9\ \text{GeV}^{-1}}{M_{\rm Pl} \sqrt{g_*(x_f)} x_f \langle\sigma v\rangle},$$

where $x_f \approx 20$–$25$ for a typical WIMP, $s_0 = 2891.2\ \text{cm}^{-3}$ is the present-day entropy density, and the freeze-out temperature $T_f = m_\chi / (k_B x_f)$. For $\Omega_\chi h^2 = 0.12$ (the measured dark matter density), one requires $\langle\sigma v\rangle \approx 3 \times 10^{-26}\ \text{cm}^3\text{s}^{-1}$, the famous **WIMP miracle**: a particle with electroweak-scale mass and electroweak-strength interactions naturally produces the observed dark matter abundance. This result drives the design of direct detection experiments (LZ, XENONnT) and indirect detection searches (Fermi-LAT dwarf galaxy constraints), which target exactly this cross section.

### Silk Damping and Photon Diffusion

Before and during recombination, photons and baryons form a tightly coupled fluid that supports acoustic oscillations — standing sound waves in the primordial plasma driven by the competition between radiation pressure and gravitational compression. The sound speed in this fluid is

$$c_s = \frac{c}{\sqrt{3(1 + R)}}, \qquad R \equiv \frac{3\rho_b}{4\rho_\gamma},$$

and the sound horizon at decoupling, $r_s = \int_0^{t_*} c_s\, dt / a$, is the comoving length scale of the first acoustic peak in the CMB power spectrum, measured to be $r_s = 147.09 \pm 0.26\ \text{Mpc}$ (Planck 2018). This is the standard ruler used in BAO analyses.

The coupling is not perfect: photons have a mean free path $\lambda_\gamma = 1/(n_e \sigma_T)$, where $\sigma_T = 6.652 \times 10^{-25}\ \text{cm}^2$ is the Thomson cross section. Random-walk diffusion of photons over this mean free path damps perturbations on scales smaller than the **Silk damping scale**

$$\lambda_D = \sqrt{\int_0^{\eta_*} \frac{d\eta}{6(1+R)} \frac{1}{a n_e \sigma_T}},$$

where $\eta = \int dt/a$ is conformal time. Modes with comoving wavenumber $k > k_D \equiv 2\pi/\lambda_D$ are exponentially suppressed in the CMB power spectrum, with the suppression going as $e^{-(k/k_D)^2}$. The observed damping tail at $\ell > 1000$ in the Planck TT power spectrum is a direct measurement of this diffusion process, and the precise shape of the tail constrains $n_e(z)$ during recombination, the helium fraction (which affects the electron density through the number of free electrons contributed by He II and He III), and the spectral index of primordial perturbations.

### Gravitational Wave Energy Budget

Stochastic gravitational wave backgrounds (SGWBs) generated by first-order phase transitions in the early universe carry an energy spectrum $\Omega_{\rm GW}(f) = (1/\rho_c) d\rho_{\rm GW}/d\ln f$ that encodes the thermodynamic parameters of the transition: the transition temperature $T_*$, the latent heat fraction $\alpha \equiv \rho_{\rm vac}/\rho_{\rm rad}|_{T_*}$, and the inverse duration $\beta/H_*$. For a strongly first-order transition driven by bubble nucleation, the peak frequency of the GW spectrum today is

$$f_{\rm peak} \approx 2.6 \times 10^{-5}\ \text{Hz} \left(\frac{\beta/H_*}{100}\right) \left(\frac{T_*}{100\ \text{GeV}}\right) \left(\frac{g_*(T_*)}{100}\right)^{1/6},$$

which falls squarely in the millihertz band targeted by LISA (launch $\sim$2035). The energy density at the peak scales as $\Omega_{\rm GW} h^2 \propto \alpha^2 (\beta/H_*)^{-2} \kappa_\phi^2$, where $\kappa_\phi$ is the efficiency of converting vacuum energy to bulk fluid motion. Practitioners parametrize the phase transition thermodynamics in `PTPlot` or `GW-Bubble-Calc` to predict LISA signal-to-noise ratios as a function of BSM parameter space, connecting particle physics inputs directly to gravitational wave observatory science.

The deepest lesson of this section is that cosmology is a subject where the universe itself functions as the laboratory. The equations governing structure formation, nucleosynthesis, recombination, and freeze-out are not theoretical decorations — they are measurement instruments. Every parameter in the Friedmann equation, every rate coefficient in the Peebles equation, every annihilation cross section in the Boltzmann equation has a corresponding observable that pins it down. Mastery of this discipline means learning to read the cosmos as an experiment, translating its observational outputs back through the governing equations into the fundamental physics that produced them.
