# Lesson 6: Structure Formation via Statistical Cosmology

## 1. First-Principles Intuition & Invariants

The universe you observe tonight through any telescope is not the universe that existed 380,000 years after the Big Bang. At recombination, the cosmos was a nearly featureless plasma, its density fluctuations suppressed to amplitudes of roughly one part in $10^5$. What intervened between that serene uniformity and the baroque architecture of today's cosmic web — galaxy filaments stretching hundreds of megaparsecs, clusters anchoring their nodes, and the vast supervoids between them — is gravitational instability operating across 13.8 billion years of cosmic time. Structure formation is the discipline that quantifies this transformation from first principles, and its tools are the statistical measures of the density field: the power spectrum, correlation functions, transfer functions, and the machinery of N-body simulation.

The intuitive entry point is the Jeans instability, first articulated by Sir James Jeans in 1902 for self-gravitating gas clouds, but whose cosmological descendant governs all large-scale structure. Consider a homogeneous fluid of density $\rho_0$ supporting small perturbations $\delta\rho$ superimposed on a background. The perturbation field is conveniently expressed as the dimensionless overdensity,

$$\delta(\vec{x}, t) = \frac{\rho(\vec{x}, t) - \bar{\rho}(t)}{\bar{\rho}(t)}$$

where $\bar{\rho}(t)$ is the cosmic mean density at time $t$. In a static Newtonian fluid, decomposing $\delta$ into Fourier modes $\delta_k \propto e^{i\vec{k}\cdot\vec{x}}$ and linearizing the coupled continuity, Euler, and Poisson equations yields the perturbation growth equation. Each Fourier mode evolves independently under the dispersion relation

$$\omega^2 = c_s^2 k^2 - 4\pi G \rho_0$$

where $c_s$ is the adiabatic sound speed and $k = |\vec{k}|$ is the comoving wavenumber. The critical scale separating stable oscillations from gravitational runaway is the Jeans wavenumber,

$$k_J = \sqrt{\frac{4\pi G \rho_0}{c_s^2}}$$

For modes with $k > k_J$, pressure wins: the perturbation oscillates as a sound wave. For $k < k_J$, gravity wins: the perturbation grows exponentially, $\delta \propto e^{\gamma t}$ with $\gamma = \sqrt{4\pi G\rho_0 - c_s^2 k^2}$. The corresponding Jeans length $\lambda_J = 2\pi / k_J$ sets the minimum mass scale above which a gas cloud is gravitationally unstable, and in the cosmological context its descendants govern the horizon-scale physics that imprints signatures on the matter power spectrum.

The cosmological generalization is non-trivial. In an expanding universe governed by the Friedmann equations, the background density $\bar{\rho}(t)$ dilutes as the scale factor $a(t)$ grows, and the expansion introduces a Hubble friction term that slows the exponential collapse to a power-law growth. Working in comoving coordinates and treating the matter-dominated era, the linear perturbation equation for pressureless cold dark matter takes the form

$$\ddot{\delta} + 2H\dot{\delta} - \frac{3}{2}H^2\Omega_m \delta = 0$$

where $H = \dot{a}/a$ is the Hubble parameter, $\Omega_m$ is the dimensionless matter density parameter, and overdots denote derivatives with respect to cosmic time $t$. This is a second-order linear ODE with a growing solution $D_+(a)$ and a decaying solution $D_-(a)$. During matter domination, $a \propto t^{2/3}$, $H = 2/(3t)$, and the growing mode solves as $D_+(t) \propto t^{2/3} \propto a$, a strikingly simple result: in matter domination, density perturbations grow linearly with the scale factor. The decaying mode $D_-(t) \propto t^{-1}$ becomes irrelevant quickly. The normalized linear growth factor is conventionally defined as

$$D_+(a) = \frac{5\Omega_m}{2} H(a) \int_0^a \frac{da'}{[a' H(a')]^3}$$

which must be computed numerically for realistic cosmologies incorporating dark energy. In the presence of a cosmological constant $\Lambda$, the Hubble friction from accelerated expansion suppresses growth at late times — a physically critical point because the onset of dark energy domination at $z \approx 0.3$ effectively froze the linear growth of structure, and perturbations in the dark energy era grow considerably more slowly than linearly.

The power spectrum of primordial density fluctuations is seeded by quantum vacuum oscillations during cosmic inflation. For a canonically normalized scalar inflaton field $\phi$ slowly rolling down its potential $V(\phi)$, quantum fluctuations of the inflaton propagate outside the Hubble horizon during inflation and freeze as classical perturbations. The Harrison-Zel'dovich-Peebles spectrum, the prediction of scale-invariant inflation, takes the form

$$\mathcal{P}_\mathcal{R}(k) = A_s \left(\frac{k}{k_*}\right)^{n_s - 1}$$

where $A_s$ is the scalar amplitude measured at the pivot scale $k_* = 0.05 \,\mathrm{Mpc}^{-1}$, and $n_s$ is the spectral index. Planck 2018 data constrain these to $A_s \approx 2.1 \times 10^{-9}$ and $n_s \approx 0.965$, the slight red tilt ($n_s < 1$) indicating a small departure from perfect scale invariance consistent with slow-roll inflation models. This primordial spectrum is the initial condition from which all structure formation proceeds. It describes a Gaussian random field — a field entirely characterized by its two-point statistics — and because linear evolution preserves Gaussianity, the linear matter power spectrum retains a Gaussian character until modes go nonlinear.

The matter power spectrum $P(k)$ at any epoch relates to the primordial spectrum through the transfer function $T(k)$,

$$P(k, a) = A_s k^{n_s} T^2(k) D_+^2(a)$$

The transfer function encodes the entire causal history of how different modes evolved from horizon entry through the radiation-matter transition and into matter domination. It is the central object of linear perturbation theory, and understanding its shape requires following modes through three distinct regimes. Modes that entered the Hubble horizon during radiation domination ($k > k_\mathrm{eq}$, where $k_\mathrm{eq} \approx 0.01 \, h \, \mathrm{Mpc}^{-1}$ corresponds to the horizon scale at matter-radiation equality) experienced stagnation during the radiation-dominated era — the Mézáros effect — because radiation pressure prevented the matter perturbation from growing. These modes are therefore suppressed relative to large-scale modes. Modes that entered the horizon after matter-radiation equality ($k \ll k_\mathrm{eq}$) grew unimpeded and retain $T(k) \rightarrow 1$ on large scales. The net result is a characteristic turnover in the power spectrum at $k_\mathrm{eq}$. The Bardeen-Bond-Kaiser-Szalay (BBKS) fitting formula provides an analytic approximation,

$$T(k) = \frac{\ln(1 + 2.34q)}{2.34q}\left[1 + 3.89q + (16.1q)^2 + (5.46q)^3 + (6.71q)^4\right]^{-1/4}$$

where $q = k / (\Omega_m h^2 \, \mathrm{Mpc}^{-1})$ is the shape parameter, with $h = H_0 / (100 \, \mathrm{km\,s^{-1}\,Mpc^{-1}})$. Modern precision cosmology replaces BBKS with Boltzmann codes — CAMB (Code for Anisotropies in the Microwave Background) and CLASS (Cosmic Linear Anisotropy Solving System) — which solve the full hierarchy of Boltzmann equations for coupled photon, neutrino, baryon, and dark matter perturbations, including the acoustic oscillations in the photon-baryon plasma that imprint Baryon Acoustic Oscillations (BAO) onto the power spectrum.

The two-point correlation function $\xi(r)$ is the configuration-space counterpart of the power spectrum, related through a Fourier transform. For a statistically homogeneous and isotropic field, the correlation function depends only on the separation magnitude $r = |\vec{r}_1 - \vec{r}_2|$:

$$\xi(r) = \langle \delta(\vec{x})\, \delta(\vec{x} + \vec{r}) \rangle = \frac{1}{2\pi^2} \int_0^\infty P(k) j_0(kr) k^2 \, dk$$

where $j_0(kr) = \sin(kr)/(kr)$ is the zeroth spherical Bessel function. Physically, $\xi(r)$ measures the excess probability above Poisson of finding a galaxy pair at separation $r$, normalized to random. The sharp acoustic peak in $\xi(r)$ at $r \approx 150 \, \mathrm{Mpc}$ — the BAO peak — is the configuration-space imprint of the sound horizon at recombination and serves as a standard ruler for measuring the expansion history of the universe.

Baryon Acoustic Oscillations deserve deep physical exposition because they are among the most elegant signatures in observational cosmology. Prior to recombination, the photon-baryon fluid was a tightly coupled plasma: photons provided enormous pressure while baryons provided gravitational mass. Overdense dark matter perturbations attracted baryons, compressing the photon-baryon fluid and driving outward-propagating acoustic waves. Each wave traveled at the sound speed of the photon-baryon plasma,

$$c_s = \frac{c}{\sqrt{3(1 + R)}}$$

where $R = 3\rho_b / (4\rho_\gamma)$ is the baryon-to-photon momentum ratio. At recombination, when photons decoupled and the pressure vanished abruptly, these acoustic waves froze in place. The characteristic scale they imprinted on the matter distribution is the comoving sound horizon at the drag epoch,

$$r_s = \int_0^{a_\mathrm{drag}} \frac{c_s \, da}{a^2 H(a)} \approx 147 \, \mathrm{Mpc}$$

This scale appears as an oscillatory modulation of $P(k)$ — with peaks and troughs spaced by $\Delta k \approx \pi / r_s$ — and as the acoustic peak in $\xi(r)$ at $r \approx 150 \, \mathrm{Mpc}$. The 2005 detection of this peak in the SDSS galaxy correlation function by Eisenstein et al. was a landmark measurement, confirming both the ΛCDM framework and providing a geometric constraint on $H(z)$ and $D_A(z)$ that is now one of the most powerful tools in dark energy characterization.

---

## 2. Core Architecture & Mechanics

### Linear Theory to Nonlinear Collapse: The Zel'dovich Approximation

Linear perturbation theory breaks down when $\delta \sim 1$, which occurs first on small scales (high-$k$ modes go nonlinear first) and progressively at larger scales as cosmic time advances. The first step beyond linear theory, and an extraordinarily accurate approximation that bridges the linear regime into the onset of nonlinear collapse, is the Zel'dovich approximation. Rather than tracking density fields, it tracks particle trajectories. A particle initially at comoving Lagrangian position $\vec{q}$ moves to Eulerian position $\vec{x}$ according to

$$\vec{x}(\vec{q}, t) = \vec{q} - D_+(t) \nabla_q \Psi(\vec{q})$$

where $\Psi(\vec{q})$ is the displacement potential related to the initial gravitational potential by $\nabla^2 \Psi = \delta_0(\vec{q})$. The displacement field $\vec{s} = -\nabla_q \Psi$ is irrotational at first order in perturbation theory. The resulting density field is obtained from mass conservation: $\rho \, d^3x = \rho_0 \, d^3q$, and computing the Jacobian of the mapping yields

$$1 + \delta = \frac{1}{(1-D_+ \lambda_1)(1-D_+ \lambda_2)(1-D_+ \lambda_3)}$$

where $\lambda_1, \lambda_2, \lambda_3$ are the eigenvalues of the deformation tensor $\partial^2\Psi / \partial q_i \partial q_j$. When $D_+(t)\lambda_1 \rightarrow 1$, the density diverges along one axis — this is pancake collapse, the formation of sheets. The Zel'dovich approximation predicts that the first structures to form are two-dimensional sheets (Zel'dovich pancakes), not spherically symmetric halos, an insight confirmed by every large N-body simulation and visible in the observed large-scale structure as the planar walls of the cosmic web.

### The Matter Power Spectrum: Computational Pipeline

A modern precision computation of $P(k)$ proceeds through a well-defined pipeline. The Boltzmann solver CLASS or CAMB integrates the full set of linearized Einstein-Boltzmann equations from deep in the radiation era to the present. Internally, CLASS represents the perturbation equations as a system of coupled first-order ODEs for the gauge-invariant variables in synchronous gauge (or conformal Newtonian gauge), including the metric perturbations $\Phi$ and $\Psi$, the photon temperature multipoles $\Theta_\ell$, neutrino hierarchy $\mathcal{N}_\ell$, and matter velocity divergence $\theta_m$. The photon hierarchy is truncated at $\ell_\mathrm{max} \approx 2000$ using a Boltzmann truncation scheme, and the tight-coupling approximation is applied before recombination to avoid the numerically stiff photon-baryon system. At each output redshift, CLASS integrates the total matter power spectrum as

$$P(k, z) = \frac{2\pi^2}{k^3} \Delta^2_m(k, z) = \frac{2\pi^2}{k^3} A_s \left(\frac{k}{k_*}\right)^{n_s} T_m^2(k, z)$$

where $T_m(k,z)$ is the total matter transfer function output by the Boltzmann hierarchy. The dimensionless power spectrum $\Delta^2(k) = k^3 P(k) / (2\pi^2)$ is the quantity most informative for intuition: it represents the variance of density fluctuations per logarithmic interval in $k$, and the characteristic scale where $\Delta^2(k) \sim 1$ defines the nonlinear scale $k_\mathrm{nl}(z)$ separating linear and nonlinear regimes.

The halofit prescription, originally due to Smith et al. (2003) and updated by Takahashi et al. (2012), extends the power spectrum into the nonlinear regime through calibrated fitting functions derived from N-body simulations. Halofit maps the linear power spectrum to a nonlinear one using the ansatz that $P_\mathrm{nl}(k)$ depends on the linear spectrum through a set of spectral shape parameters evaluated at $k_\sigma$ (the nonlinear scale where $\sigma(k_\sigma) = 1$). The emulator-based approach, exemplified by EuclidEmulator2 and CosmicEmu, supersedes halofit for precision work by interpolating $P_\mathrm{nl}(k)$ from a dense grid of N-body simulations across cosmological parameter space.

### N-body Simulation Architecture

The workhorse of nonlinear structure formation is the cosmological N-body simulation. The fundamental problem is to evolve $N$ particles under their mutual gravitational interactions in an expanding spacetime, with $N$ ranging from $10^8$ for fast exploratory runs to $5 \times 10^{12}$ for state-of-the-art simulations like AbacusSummit. The equations of motion in comoving coordinates are

$$\ddot{\vec{x}} + 2H\dot{\vec{x}} = -\frac{1}{a^2}\nabla\phi$$

where the comoving gravitational potential satisfies the comoving Poisson equation

$$\nabla^2\phi = 4\pi G \bar{\rho} a^2 \delta$$

Solving the Poisson equation naively costs $\mathcal{O}(N^2)$ operations and is entirely intractable for $N > 10^6$. The particle-mesh (PM) method reduces this to $\mathcal{O}(N_g^3 \log N_g)$ by assigning particles to a mesh via a mass assignment scheme (nearest grid point, cloud-in-cell, or triangular-shaped cloud) and solving the Poisson equation with a Fast Fourier Transform. The P³M (particle-particle/particle-mesh) method adds direct particle-particle force corrections at short range to recover sub-cell force accuracy. The industry-standard algorithm for modern large-scale simulations is the TreePM method, implemented in codes such as Gadget-4, PKDGRAV3, and Arepo: a Barnes-Hut oct-tree resolves short-range forces in $\mathcal{O}(N \log N)$ time, while a PM grid handles the long-range smooth component, the two regimes separated at a force-split scale $r_s \sim 1\, h^{-1}\mathrm{Mpc}$.

```
Initial Conditions (ICs)
     │
     ▼
 Inflation Power Spectrum  ──▶  P_prim(k) = A_s (k/k*)^(n_s-1)
     │
     ▼
 Boltzmann Solver (CAMB/CLASS)
     │
     ├── Einstein equations  (Φ, Ψ metric perturbations)
     ├── Photon hierarchy    (Θ_ℓ multipoles)
     ├── Neutrino hierarchy  (N_ℓ multipoles)
     └── CDM + baryon fluids (δ, θ)
     │
     ▼
  P(k, z=0) [linear]  ──▶  T(k) transfer function
     │
     ├── BAO feature at k ~ nπ/r_s
     └── Turnover at k_eq ~ 0.01 h/Mpc
     │
     ▼
 IC Generator (N-GenIC / 2LPT / monofonIC)
  Displacement field via Zel'dovich (1LPT)
  or Second-order LPT correction (2LPT)
     │
     ▼
 N-body Solver (Gadget-4 / PKDGRAV3 / Arepo)
  ┌──────────────────────────────────┐
  │  Drift (kick-drift-kick leapfrog) │
  │  Gravity: TreePM or PM+P³M       │
  │  Time integration: adaptive Δt   │
  │  Outputs: snapshots at z_i        │
  └──────────────────────────────────┘
     │
     ▼
 Halo Finder (Friends-of-Friends / ROCKSTAR)
     │
     ▼
 Power Spectrum / Correlation Function
 BAO measurement / Halo Mass Function
```

Initial conditions for N-body simulations are generated by displacing particles from a uniform grid or glass particle load according to the Zel'dovich approximation at first order, or the second-order Lagrangian perturbation theory (2LPT) correction for higher accuracy. The 2LPT correction accounts for the fact that the displacement potential at second order receives a contribution from the coupling of two first-order modes:

$$\vec{s}^{(2)}(\vec{q}) = \frac{1}{2}\sum_{i \neq j} \left(\Psi_{,ii}^{(1)} \Psi_{,jj}^{(1)} - (\Psi_{,ij}^{(1)})^2\right)$$

This correction is essential for starting simulations at $z_\mathrm{start} \lesssim 50$; without it, transient artifacts from incorrect initial velocities contaminate low-redshift clustering statistics. Modern IC generators like monofonIC implement third-order LPT and can generate conditions with matched amplitude for paired fixed simulations that suppress cosmic variance.

### Halo Finding and the Cosmic Web

Once a simulation produces particle distributions, the extraction of physically meaningful structures requires halo-finding algorithms. The Friends-of-Friends (FoF) algorithm links together all particle pairs separated by less than a linking length $b \cdot \bar{d}$, where $\bar{d}$ is the mean inter-particle spacing and the canonical choice $b = 0.2$ encloses roughly the virial radius. FoF halos are parameter-free but can erroneously bridge neighboring halos through particle bridges. The spherical overdensity (SO) algorithm instead finds the radius $r_{200}$ within which the mean enclosed density equals 200 times the critical density $\rho_c(z)$:

$$M_{200} = \frac{4}{3}\pi r_{200}^3 \cdot 200 \rho_c(z) = \frac{800\pi}{3} \frac{H^2(z)}{G} r_{200}^3$$

Phase-space halo finders such as ROCKSTAR (Robust Overdensity Calculation using K-Space Topologically Adaptive Refinement) operate in six-dimensional phase space, making them far more robust at identifying substructure within larger halos — the subhalos that host satellite galaxies.

The cosmic web itself is quantified through the T-web and V-web formalisms, which classify each point in the density field by the eigenvalues of the tidal or velocity shear tensor. At each point, computing the eigenvalues $\lambda_1 \geq \lambda_2 \geq \lambda_3$ of the tidal tensor $T_{ij} = \partial^2\phi/\partial x_i\partial x_j$ and comparing them to a threshold $\lambda_\mathrm{th}$ yields a fourfold classification: voids (all $\lambda < \lambda_\mathrm{th}$), sheets/walls (one $\lambda > \lambda_\mathrm{th}$), filaments (two $\lambda > \lambda_\mathrm{th}$), and nodes/clusters (all three $\lambda > \lambda_\mathrm{th}$). The fraction of cosmic volume in voids exceeds 80%, while nodes contain only a few percent of the volume but concentrate a significant fraction of the mass — a vivid illustration that most of the universe is empty.

### Measuring BAO in Galaxy Surveys

The observational measurement of BAO requires computing the angle-averaged two-point correlation function or power spectrum from a galaxy catalog. For a survey with $N_g$ galaxies in volume $V$, the estimator of Landy and Szalay (1993) for $\xi(r)$ is

$$\hat{\xi}(r) = \frac{DD(r) - 2DR(r) + RR(r)}{RR(r)}$$

where $DD$, $DR$, and $RR$ are normalized pair counts in the data-data, data-random, and random-random catalogs respectively. The random catalog samples the same survey geometry as the data but with no clustering — typically 50 to 100 times the data density to suppress shot noise in $RR$. The power spectrum estimator of Feldman, Kaiser, and Peacock (FKP) assigns to each galaxy a weight

$$w_\mathrm{FKP}(\vec{x}) = \frac{1}{1 + \bar{n}(\vec{x}) P_0}$$

where $\bar{n}(\vec{x})$ is the local mean galaxy number density and $P_0 \approx 10^4 \, h^{-3}\mathrm{Mpc}^3$ is a fiducial power spectrum amplitude. This weight minimizes the variance of the power spectrum estimator across all scales. The galaxy overdensity field is then computed on a mesh via FFT, and $P(k)$ is estimated from the spherical average of $|\tilde\delta(\vec{k})|^2$.

Redshift-space distortions (RSD) introduce anisotropy into the observed power spectrum because galaxy peculiar velocities $v_r$ along the line of sight shift the inferred redshift. The apparent comoving position of a galaxy is $\vec{s} = \vec{x} + (v_r/aH)\hat{r}$, and to linear order the redshift-space power spectrum becomes anisotropic via the Kaiser effect:

$$P^s(k, \mu) = (1 + f\mu^2)^2 P(k)$$

where $\mu = k_\parallel / k$ is the cosine of the angle between the wavevector and the line of sight, and $f = d\ln D_+/d\ln a \approx \Omega_m(z)^{0.55}$ is the growth rate. Fitting the anisotropic power spectrum $P^s(k,\mu)$ simultaneously constrains $f\sigma_8$ and the geometric ratio $D_A H$, compressing the full clustering information into two of the most powerful cosmological observables available from spectroscopic galaxy surveys.

---

## 3. High-Performance Optimization & Failure Modes

### Numerical Resolution and Convergence

The reliability of a cosmological N-body simulation is governed by three resolution parameters that must be tuned together: the box size $L_\mathrm{box}$, the number of particles $N_p$, and the gravitational softening length $\epsilon_\mathrm{soft}$. The box size determines which large-scale modes are sampled: the fundamental mode has $k_\mathrm{min} = 2\pi/L_\mathrm{box}$, and modes longer than the box are entirely absent, suppressing power on scales $k < k_\mathrm{min}$. Missing large-scale power introduces a systematic bias in halo abundances and clustering through the missing large-scale tidal field — the super-sample covariance problem. For BAO science, $L_\mathrm{box} \geq 1 \, h^{-1}\mathrm{Gpc}$ is mandatory, since the acoustic scale $r_s \approx 150 \, \mathrm{Mpc}$ must be sampled with many modes.

The particle mass $m_p = \bar{\rho} L_\mathrm{box}^3 / N_p$ sets the minimum halo mass that can be resolved. A halo must contain at least $\sim 100$ particles to have a reliably converged mass and concentration, so a simulation targeting galaxy groups at $M_h \gtrsim 10^{13} M_\odot$ requires $m_p \lesssim 10^{11} M_\odot$. Pushing to galaxy-scale halos at $M_h \sim 10^{12} M_\odot$ demands $m_p \sim 10^{10} M_\odot$. The gravitational softening length $\epsilon_\mathrm{soft}$ prevents unphysical two-body scattering when particle separation approaches zero; the optimal choice $\epsilon_\mathrm{soft} \approx 1/30$ of the mean inter-particle spacing $\bar{d} = L_\mathrm{box}/N_p^{1/3}$ balances suppression of two-body relaxation against loss of small-scale force accuracy.

A common and costly failure mode is insufficient dynamic range. Simulating both BAO scales and halo substructure simultaneously forces a compromise: a $1 \, h^{-1}\mathrm{Gpc}$ box with $m_p = 10^{10} M_\odot$ demands $N_p \approx 10^{11}$ particles, which is at the frontier of current computing. Zoom-in simulations address this by embedding a high-resolution Lagrangian region centered on a target halo within a lower-resolution background volume that provides the correct large-scale tidal field. The contamination of the zoom region by low-resolution particles must be monitored rigorously — any high-mass boundary particle within $r_{200}$ of the target halo invalidates the halo's properties.

### Cosmic Variance and Ensemble Strategies

For any finite simulation volume, the measured $P(k)$ on scales approaching $L_\mathrm{box}$ is dominated by sampling variance — the fact that only a small number of Fourier modes contribute at low $k$. The variance on the power spectrum estimator at wavenumber $k$ within a bin $\Delta k$ is

$$\frac{\sigma^2_{P(k)}}{P^2(k)} = \frac{2}{N_\mathrm{modes}} \left(1 + \frac{1}{\bar{n}P(k)}\right)^2$$

where $N_\mathrm{modes} = 4\pi k^2 \Delta k V_\mathrm{box} / (2\pi)^3$ is the number of independent modes in the bin. At $k \sim 0.01 \, h\,\mathrm{Mpc}^{-1}$ in a $1 \, \mathrm{Gpc}/h$ box, $N_\mathrm{modes} \sim$ few, and cosmic variance errors can exceed 20%. The paired-and-fixed technique, introduced by Angulo and Pontzen (2016), addresses this by running simulations in pairs where the amplitudes of all Fourier modes are fixed to exactly $|A(k)|^2 = P(k)$ and the two realizations use opposite phases. This eliminates sample variance in the mean power spectrum at the cost of losing information about higher-order statistics and cannot be used for covariance matrix estimation.

Covariance matrix estimation for BAO fitting requires running large ensembles of simulations. The covariance matrix of the power spectrum vector $\vec{P} = \{P(k_1), P(k_2), \ldots\}$ estimated from $N_s$ simulations converges as $\sigma_C \propto N_s^{-1/2}$, and an inverted covariance matrix estimated from $N_s$ simulations with $N_b$ bandpowers introduces a Hartlap correction factor $(N_s - N_b - 2)/(N_s - 1)$ to the inverse that is unbiased only when $N_s \gg N_b$. For a typical BAO analysis with $N_b = 50$ bandpowers, one needs $N_s \gtrsim 300$ simulations to keep the Hartlap correction below 20%, which motivates the use of fast approximate simulation methods: COLA (COmoving Lagrangian Acceleration), Pinocchio, and EZmocks, which reproduce the two-point statistics of full N-body runs at a fraction of the computational cost.

### Modeling Nonlinearities and Baryonic Effects

The nonlinear matter power spectrum receives corrections from several sources that become important at different scales. Pure gravitational nonlinearities, captured well by halofit and emulators, dominate at $k > 0.1 \, h\,\mathrm{Mpc}^{-1}$. Baryonic effects — gas cooling, star formation, AGN feedback — become significant at $k > 0.3 \, h\,\mathrm{Mpc}^{-1}$ and can suppress $P(k)$ by 10–30% relative to dark-matter-only predictions at $k \sim 1 \, h\,\mathrm{Mpc}^{-1}$, primarily through AGN feedback ejecting gas from halo cores. Neutrino free-streaming suppresses the matter power spectrum at scales below the neutrino free-streaming length $\lambda_\mathrm{fs} = 8 \pi^2 m_\nu / (3M_\mathrm{Pl} H)$, with the total suppression scaling approximately as

$$\frac{\Delta P}{P} \approx -8 f_\nu, \quad f_\nu = \frac{\Omega_\nu}{\Omega_m}$$

For the minimum-mass neutrino hierarchy with $\sum m_\nu \approx 0.06 \, \mathrm{eV}$, $f_\nu \approx 0.004$ and the suppression is about 3% — entirely detectable by Stage-IV surveys like DESI, Euclid, and the Rubin Observatory LSST.

The principal modeling failure mode in BAO analysis is incorrect treatment of mode coupling. Nonlinear gravitational evolution generates higher-order correlations that shift and broaden the BAO peak in $\xi(r)$ relative to the linear prediction. The peak shift is at the level of $\sim 0.5\%$ in $r_s$, which is small but non-negligible for percent-level dark energy constraints. The standard mitigation is BAO reconstruction, a procedure that uses the observed galaxy density field to reverse-engineer the linear displacement field under the Zel'dovich approximation and thereby sharpen the BAO peak. The iterative reconstruction algorithm of Eisenstein et al. (2007) proceeds by computing the smoothed galaxy overdensity $\delta_s(\vec{x})$ at a scale $\sim 15 \, h^{-1}\mathrm{Mpc}$, solving for the displacement via $\nabla\cdot\vec{\Psi} = -\delta_s/b$ (with $b$ the linear galaxy bias), and shifting galaxies back along $-\vec{\Psi}$. Applied to BOSS DR12, reconstruction improved the BAO measurement precision from 1.5% to 1.0% — a factor of 1.5 increase in constraining power for free, using no additional data.

### Practical Workflow for a BAO Analysis Pipeline

A complete, end-to-end BAO measurement from a spectroscopic galaxy survey involves a sequence of carefully validated steps that each carry their own systematic budget. The survey footprint and redshift selection function define the geometric mask $W(\vec{x})$, which must be incorporated into both the data pair counts and the random catalog. Fiber collisions — the inability of a spectroscopic instrument to place two fibers within some minimum angular separation — suppress clustering on small angular scales and must be corrected through weighting schemes or angular upweighting. Photometric systematics (stellar density, airmass, Galactic dust) modulate the galaxy density and produce spurious large-scale power if uncorrected; these are mitigated by regressing the galaxy density against imaging systematics maps and deriving per-galaxy weights.

The BAO fitting itself is performed in the compressed parameter space of dilation parameters $\alpha_\perp = D_A(z)r_s^\mathrm{fid}/D_A^\mathrm{fid}(z)r_s$ and $\alpha_\parallel = H^\mathrm{fid}(z)r_s^\mathrm{fid}/H(z)r_s$, where the superscript "fid" denotes the fiducial cosmology used to convert redshifts to distances. The model power spectrum or correlation function in the dilation-parameter parameterization is

$$P^\mathrm{model}(k_\perp, k_\parallel) = P_\mathrm{nl}\left(\frac{k_\perp}{\alpha_\perp}, \frac{k_\parallel}{\alpha_\parallel}\right) \cdot F_\mathrm{BAO}$$

where the BAO feature is additionally broadened by a damping term $\exp(-(k_\parallel^2 \Sigma_\parallel^2 + k_\perp^2 \Sigma_\perp^2)/2)$ representing nonlinear smearing, with $\Sigma_{\perp,\parallel} \sim 4$–$10 \, h^{-1}\mathrm{Mpc}$ depending on redshift and reconstruction status. A broad-band polynomial absorbs the smooth broadband shape from galaxy bias and redshift-space distortions, isolating the BAO information exclusively in the oscillatory feature. The likelihood is then maximized over $\{\alpha_\perp, \alpha_\parallel, \mathrm{nuisance}\}$ using either a frequentist $\chi^2$ minimization or a Markov Chain Monte Carlo sampler. The final DESI Year 1 BAO results (2024) achieve $\alpha_\parallel$ precision at the sub-percent level across five redshift bins spanning $0.1 < z < 4.2$, placing constraints on the dark energy equation of state $w(z)$ that hint at a possible evolution away from $w = -1$.

Understanding the physical origin, mathematical structure, and computational demands of structure formation is not peripheral to cosmology — it is cosmology. Every observable in modern surveys, from weak gravitational lensing shear maps to redshift-space galaxy multipoles to the thermal Sunyaev-Zel'dovich effect, encodes information that can only be interpreted against the backdrop of the density field's statistical architecture developed in this lesson. The power spectrum, the transfer function, and the BAO feature are not merely technical objects: they are the compressed memory of the universe's thermal history, gravitational evolution, and the initial quantum fluctuations of the inflaton field, written in the language of large-scale structure for those who know how to read it.
