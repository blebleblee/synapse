# Lesson 2: Friedmann Equations in Spacetime Dynamics

## 1. First-Principles Intuition & Invariants

### The Universe as a Dynamical Manifold

Before the twentieth century, the cosmos was largely conceived as static and eternal, a backdrop rather than an actor. Einstein himself, when he first applied his field equations to the universe as a whole in 1917, found to his discomfort that general relativity predicted a universe in motion. He famously introduced the cosmological constant $\Lambda$ as a correction term to enforce a static solution, a move he would later call his "greatest blunder" after Hubble's observations in 1929 confirmed that distant galaxies are receding from us with velocities proportional to their distances. The instrument that makes all of modern cosmology rigorous is the Friedmann-Lemaître-Robertson-Walker (FLRW) metric and the two Friedmann equations that govern its evolution.

The central insight is geometrical: if the universe is homogeneous (the same in every location) and isotropic (the same in every direction), then the spacetime metric must reflect those symmetries exactly. This is the Cosmological Principle, and while it is an approximation that breaks down at scales below roughly 100 megaparsecs, it holds to extraordinary precision when we smooth over the lumpy distribution of galaxies and examine the cosmic microwave background, which is uniform in temperature to one part in $10^5$.

### The FLRW Metric and the Scale Factor

The most general metric consistent with homogeneity and isotropy in comoving coordinates $(t, r, \theta, \phi)$ is the FLRW line element:

$$ds^2 = -c^2\,dt^2 + a(t)^2 \left[ \frac{dr^2}{1 - kr^2} + r^2\,d\Omega^2 \right]$$

where $d\Omega^2 = d\theta^2 + \sin^2\!\theta\,d\phi^2$ is the metric on the unit two-sphere, $k \in \{-1, 0, +1\}$ is the curvature parameter encoding hyperbolic, flat, and spherical spatial sections respectively, and $a(t)$ is the scale factor, a dimensionless function of cosmic time that encodes the entire expansion history of the universe. The coordinates $r$, $\theta$, and $\phi$ are comoving coordinates: they are fixed to the matter of the universe and do not change as the universe expands. All the dynamics, all the history of cosmic expansion and contraction, is encoded in the single function $a(t)$.

The normalization convention sets $a(t_0) = 1$ at the present epoch $t_0$. When cosmologists speak of a galaxy at redshift $z$, they are referring to the epoch when $a = (1+z)^{-1}$, so a galaxy at $z = 2$ was observed when the universe was one-third its present size. The Hubble parameter, defined as

$$H(t) \equiv \frac{\dot{a}}{a}$$

measures the fractional rate of expansion at any cosmic epoch. Its present-day value $H_0$ is approximately $67$–$73$ km s$^{-1}$ Mpc$^{-1}$, with the tension between early-universe (CMB-based) and late-universe (distance ladder-based) measurements representing one of the most urgent open problems in cosmology today. The variable definitions used throughout this lesson are collected in the table below.

| Symbol | Quantity | Units (SI) |
|---|---|---|
| $a(t)$ | Scale factor | dimensionless |
| $H \equiv \dot{a}/a$ | Hubble parameter | s$^{-1}$ |
| $\rho$ | Total energy density | kg m$^{-3}$ |
| $p$ | Pressure | Pa $=$ kg m$^{-1}$ s$^{-2}$ |
| $k$ | Curvature parameter | dimensionless ($-1,0,+1$) |
| $\Lambda$ | Cosmological constant | m$^{-2}$ |
| $G$ | Newton's gravitational constant | m$^3$ kg$^{-1}$ s$^{-2}$ |
| $w \equiv p/\rho c^2$ | Equation-of-state parameter | dimensionless |

### Einstein's Field Equations as the Starting Point

The Friedmann equations are not postulated; they are derived from Einstein's field equations:

$$G_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu}$$

where $G_{\mu\nu} = R_{\mu\nu} - \frac{1}{2}R\,g_{\mu\nu}$ is the Einstein tensor, $R_{\mu\nu}$ is the Ricci curvature tensor, $R = g^{\mu\nu}R_{\mu\nu}$ is the Ricci scalar, $g_{\mu\nu}$ is the metric tensor, and $T_{\mu\nu}$ is the stress-energy tensor. The left side encodes the geometry of spacetime; the right side encodes the content of matter and energy that sources that geometry. For a perfect fluid, the stress-energy tensor takes the maximally symmetric form

$$T^{\mu\nu} = \left(\rho + \frac{p}{c^2}\right)u^\mu u^\nu + p\,g^{\mu\nu}$$

where $u^\mu$ is the four-velocity of the fluid elements. In the comoving frame, $u^\mu = (c, 0, 0, 0)$, and $T^{\mu\nu}$ is diagonal: $T^{00} = \rho c^2$ and $T^{ii} = p\,g^{ii}$, reflecting the pressure isotropy demanded by the Cosmological Principle.

### Deriving the Friedmann Equations from the FLRW Metric

The derivation proceeds by computing the non-zero components of the Ricci tensor for the FLRW metric. This is a disciplined but demanding calculation in tensor algebra. The two independent components that survive after applying the symmetry of the metric are the time-time component and the space-space component. For the FLRW line element, the relevant Christoffel symbols reduce to:

$$\Gamma^0_{ij} = \frac{a\dot{a}}{c}\,\tilde{g}_{ij}, \qquad \Gamma^i_{0j} = \frac{\dot{a}}{a}\,\delta^i_j, \qquad \Gamma^i_{jk} = \tilde{\Gamma}^i_{jk}$$

where $\tilde{g}_{ij}$ and $\tilde{\Gamma}^i_{jk}$ are the spatial metric and its associated Christoffel symbols on the constant-curvature hypersurface. Computing $R_{00}$ and $R_{ij}$ from these symbols and inserting them into the Einstein equations for the perfect fluid yields, after careful manipulation, the two Friedmann equations.

The **first Friedmann equation** emerges from the $(0,0)$ component:

$$\boxed{H^2 = \left(\frac{\dot{a}}{a}\right)^2 = \frac{8\pi G}{3}\rho - \frac{kc^2}{a^2} + \frac{\Lambda c^2}{3}}$$

The **second Friedmann equation** (also called the Raychaudhuri equation) emerges from the trace of the spatial $(i,j)$ components:

$$\boxed{\frac{\ddot{a}}{a} = -\frac{4\pi G}{3}\left(\rho + \frac{3p}{c^2}\right) + \frac{\Lambda c^2}{3}}$$

The **fluid continuity equation** (which is not independent but follows from $\nabla_\mu T^{\mu\nu} = 0$, the Bianchi identity applied to the stress-energy tensor) provides the third relation:

$$\dot{\rho} + 3H\left(\rho + \frac{p}{c^2}\right) = 0$$

This continuity equation has an immediately transparent physical meaning. The term $3H\rho$ represents the dilution of energy density due to the increasing volume of the universe ($V \propto a^3$), while the $3Hp/c^2$ term represents the work done by pressure as the universe expands: a pressureful fluid does work on its surroundings as it expands and therefore loses energy density faster than a pressureless one.

### The Equation of State and Cosmic Components

The system of Friedmann equations is closed only once we specify the equation of state $w = p/(\rho c^2)$ for each component. Each major component of the cosmic energy budget has a characteristic $w$:

For **non-relativistic matter** (baryons, cold dark matter), the random thermal velocities are negligible compared to $c$, so the pressure is effectively zero: $w_m = 0$. Integrating the continuity equation gives $\rho_m \propto a^{-3}$, the expected result for a conserved number of particles in a volume growing as $a^3$.

For **radiation** (photons, relativistic neutrinos), the pressure is exactly one-third the energy density: $w_r = 1/3$. This follows from the trace of the electromagnetic stress-energy tensor in $3+1$ dimensions and from kinetic theory for massless particles. The continuity equation then gives $\rho_r \propto a^{-4}$. The extra factor of $a^{-1}$ beyond the dilution factor arises because each photon's energy is redshifted as the universe expands: $E_\gamma = hc/\lambda \propto a^{-1}$.

For the **cosmological constant** $\Lambda$, often reinterpreted as vacuum energy with $\rho_\Lambda = \Lambda c^2/(8\pi G)$, the equation of state is $w_\Lambda = -1$, meaning the pressure is exactly negative: $p_\Lambda = -\rho_\Lambda c^2$. The continuity equation gives $\rho_\Lambda = \mathrm{const}$, independent of $a$: vacuum energy is not diluted by expansion. This negative pressure is the source of the accelerating expansion discovered in 1998 by the Supernova Cosmology Project and the High-Z Supernova Search Team.

### Critical Density and the Density Parameters

One of the most practically important quantities in observational cosmology is the **critical density**, defined as the total energy density for which the spatial geometry is exactly flat ($k = 0$) at a given epoch:

$$\rho_c(t) = \frac{3H(t)^2}{8\pi G}$$

At the present epoch, with $H_0 \approx 67.4$ km s$^{-1}$ Mpc$^{-1}$ from Planck 2018:

$$\rho_{c,0} \approx 8.62 \times 10^{-27}\,\text{kg m}^{-3}$$

This is an almost incomprehensibly small density, roughly five hydrogen atoms per cubic meter. The fact that the actual density of the universe is so close to this critical value is one of the central puzzles that inflationary cosmology was constructed to explain. The **density parameter** for each component is defined as the ratio:

$$\Omega_i \equiv \frac{\rho_i}{\rho_c}$$

so that the first Friedmann equation can be rewritten in a form that is both compact and directly confronted with observational data:

$$H^2 = H_0^2 \left[ \Omega_{m,0}\,a^{-3} + \Omega_{r,0}\,a^{-4} + \Omega_{\Lambda,0} + \Omega_{k,0}\,a^{-2} \right]$$

where the curvature density parameter is defined as $\Omega_{k,0} = -kc^2/(H_0^2)$, and the flat-universe normalization constraint is $\Omega_{m,0} + \Omega_{r,0} + \Omega_{\Lambda,0} + \Omega_{k,0} = 1$. The Planck 2018 results give $\Omega_{m,0} \approx 0.315$, $\Omega_{\Lambda,0} \approx 0.685$, $\Omega_{r,0} \approx 9.1 \times 10^{-5}$, and $\Omega_{k,0}$ consistent with zero at the level of $0.4\%$.

---

## 2. Core Architecture & Mechanics

### The Dynamical System: Phase Space of the Scale Factor

The two Friedmann equations, combined with the fluid equation and an equation of state, constitute a dynamical system for $a(t)$ and $\rho(t)$. Understanding the qualitative behavior of this system before computing numerical solutions is the hallmark of a mature cosmologist. The second Friedmann equation is the key to understanding whether the expansion is accelerating or decelerating. The condition for acceleration is $\ddot{a} > 0$, which requires:

$$\rho + \frac{3p}{c^2} < \frac{\Lambda c^2}{4\pi G}$$

For a universe with no cosmological constant, acceleration requires $w < -1/3$. The ordinary matter and radiation that dominate the early universe both have $w \geq 0$, so they always decelerate the expansion. Only a component with sufficiently negative pressure, whether a cosmological constant ($w = -1$), dark energy ($-1 < w < -1/3$), or a scalar inflaton field, can reverse this and drive acceleration.

The evolution of the scale factor for a single-component, spatially flat universe admits exact analytical solutions. For a matter-dominated universe ($w = 0$), integrating the first Friedmann equation with $\rho = \rho_0 a^{-3}$ gives the **Einstein-de Sitter solution**:

$$a(t) \propto t^{2/3}$$

For a radiation-dominated universe ($w = 1/3$):

$$a(t) \propto t^{1/2}$$

For a $\Lambda$-dominated universe ($w = -1$), the exponential de Sitter solution emerges:

$$a(t) \propto e^{H_\Lambda t}, \qquad H_\Lambda = \sqrt{\frac{\Lambda c^2}{3}}$$

These are not merely formal solutions. Each dominated epoch marks a distinct phase of cosmic history, and the transitions between them have direct, measurable consequences for the formation of large-scale structure, the abundances of light elements from Big Bang Nucleosynthesis, and the anisotropy spectrum of the CMB.

### Signal Flow: From Metric to Observables

The following diagram maps the logical flow from the fundamental spacetime geometry through the Friedmann equations to the observational quantities that cosmologists actually measure.

```
┌─────────────────────────────────┐
│       FLRW Metric g_μν          │
│  ds² = -c²dt² + a(t)²γ_ij dx^i dx^j  │
└────────────────┬────────────────┘
                 │  Christoffel symbols Γ
                 ▼
┌─────────────────────────────────┐
│     Riemann & Ricci Tensors     │
│    R_μνρσ → R_μν → R (scalar)   │
└────────────────┬────────────────┘
                 │  G_μν = R_μν - ½Rg_μν
                 ▼
┌─────────────────────────────────┐
│    Einstein Field Equations     │
│  G_μν + Λg_μν = (8πG/c⁴) T_μν  │
└──────────┬──────────────────────┘
           │  Perfect fluid T_μν (ρ, p)
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐   ┌────────────────────┐
│First   │   │Second Friedmann    │
│Friedm. │   │(Raychaudhuri) Eq.  │
│H² = …  │   │ ä/a = -4πG/3(ρ+3p/c²)+Λc²/3│
└───┬────┘   └─────────┬──────────┘
    │                  │
    └────────┬──────────┘
             │  + Equation of state  w = p/(ρc²)
             │  + Fluid continuity   ρ̇ + 3H(ρ+p/c²) = 0
             ▼
┌─────────────────────────────────┐
│   Scale factor history  a(t)    │
│   (matter / radiation / Λ eras) │
└────────────────┬────────────────┘
                 │
     ┌───────────┼─────────────┐
     ▼           ▼             ▼
┌─────────┐ ┌─────────┐  ┌──────────────┐
│Hubble   │ │Redshift │  │Comoving &    │
│H(z)     │ │z=a⁻¹-1 │  │Luminosity    │
│parameter│ │         │  │distances     │
└─────────┘ └─────────┘  └──────────────┘
     │           │             │
     └───────────┴──────┬──────┘
                        ▼
         ┌──────────────────────────┐
         │  Observational Tests     │
         │  · Type Ia supernovae    │
         │  · BAO power spectrum    │
         │  · CMB angular diameter  │
         │  · H(z) from OHD data    │
         └──────────────────────────┘
```

### Comoving Distances and the Cosmic Distance Ladder

The scale factor $a(t)$ connects directly to the distances astronomers measure. The **comoving distance** to an object at redshift $z$ is:

$$\chi(z) = \frac{c}{H_0} \int_0^z \frac{dz'}{E(z')}$$

where the dimensionless Hubble function is:

$$E(z) = \frac{H(z)}{H_0} = \sqrt{\Omega_{m,0}(1+z)^3 + \Omega_{r,0}(1+z)^4 + \Omega_{\Lambda,0} + \Omega_{k,0}(1+z)^2}$$

The **luminosity distance**, which relates the intrinsic luminosity $L$ of a source to its observed flux $F$ via $F = L/(4\pi d_L^2)$, is:

$$d_L(z) = (1+z)\,\chi(z)$$

The **angular diameter distance**, which relates the physical size $\ell$ of an object to its observed angular size $\theta$ via $\theta = \ell/d_A$, is:

$$d_A(z) = \frac{\chi(z)}{1+z}$$

The two extra factors of $(1+z)$ separating $d_L$ from $d_A$ reflect two distinct physical effects: one factor accounts for the redshifting of each photon's energy, and the second accounts for the reduction in photon arrival rate due to cosmic time dilation. This distinction is not merely formal. The Tolman surface brightness test, which measures how rapidly surface brightness falls with redshift, provides a consistency check of the FLRW framework itself, and surveys with the Hubble Space Telescope and James Webb Space Telescope routinely exploit these relations to measure cosmological parameters.

### Numerical Integration: Computing $a(t)$ in Practice

For realistic cosmologies with multiple components, the first Friedmann equation is integrated numerically. Rewriting it as:

$$\frac{da}{dt} = H_0 \sqrt{\Omega_{m,0}\,a^{-1} + \Omega_{r,0}\,a^{-2} + \Omega_{\Lambda,0}\,a^{2} - kc^2/H_0^2}$$

transforms the problem into a first-order ODE in $a(t)$. With initial condition $a(t_0) = 1$ and integrating backward toward the Big Bang ($a \to 0$) or forward into the future, a standard fourth-order Runge-Kutta scheme with adaptive step size provides accurate results. The practical implementation in Python using `scipy.integrate.solve_ivp` follows a workflow of defining the right-hand side function, specifying the $\Omega$ parameters, choosing an integration interval in $a$ or $t$, and then post-processing the output to extract $H(z)$, $\chi(z)$, and $d_L(z)$ via a secondary quadrature integral using `scipy.integrate.quad`.

The **conformal time** $\eta$, defined by $d\eta = dt/a(t)$, is frequently a superior independent variable for numerical work because it converts the FLRW metric into a conformally flat form:

$$ds^2 = a(\eta)^2\left(-c^2\,d\eta^2 + \frac{dr^2}{1 - kr^2} + r^2\,d\Omega^2\right)$$

Perturbation theory for structure formation, Boltzmann solvers like CAMB and CLASS, and gravitational wave propagation calculations are all more naturally expressed in conformal time, so familiarity with both the cosmic time and conformal time representations is essential for research-level work.

### The Deceleration Parameter and the Phase Transition to Acceleration

A coordinate-invariant characterization of the expansion history is provided by the **deceleration parameter**:

$$q \equiv -\frac{\ddot{a}\,a}{\dot{a}^2} = -1 - \frac{\dot{H}}{H^2}$$

A matter+$\Lambda$ universe transitions from decelerated ($q > 0$) to accelerated ($q < 0$) expansion at the redshift where:

$$\Omega_{m,0}(1+z_{\rm acc})^3 = 2\Omega_{\Lambda,0}$$

Solving with the Planck values gives $z_{\rm acc} \approx 0.33$, meaning the universe switched from decelerating to accelerating expansion roughly 3.8 billion years ago. This transition is directly observed in the Hubble diagram of Type Ia supernovae: at high redshift ($z \sim 0.5$–$1$), supernovae appear dimmer (more distant) than a decelerating universe would predict, and that excess dimness is the observational signature of acceleration.

---

## 3. High-Performance Optimization & Failure Modes

### Precision Cosmology: Fitting Parameters to Observational Data

The mature practice of cosmology is not merely solving the Friedmann equations for a given set of parameters but inverting the problem: given observational data, infer the posterior probability distributions over the cosmological parameters $\{\Omega_m, \Omega_\Lambda, H_0, w_0, w_a, \ldots\}$. This is a Bayesian inference problem, and its standard workflow uses Markov Chain Monte Carlo (MCMC) sampling. The community-standard tool is `emcee` (Foreman-Mackey et al. 2013) for affine-invariant ensemble MCMC, though nested sampling codes like `MultiNest` and `PolyChord` offer better performance in multi-modal or high-dimensional posteriors.

The **Chebyshev expansion** is a practitioner's shortcut for the quadrature integral in $\chi(z)$. Because $E(z)$ is smooth across most of its domain, approximating $1/E(z)$ with a Chebyshev polynomial of degree 10–15 and integrating analytically yields relative errors below $10^{-8}$ while being orders of magnitude faster than adaptive quadrature. Codes like `astropy.cosmology` implement pre-compiled integrators for exactly this reason: when you are evaluating $d_L(z)$ millions of times inside an MCMC chain, the difference between a 10-microsecond and a 1-microsecond call per evaluation becomes a wall-clock difference of hours.

The **dark energy equation-of-state parameterization** most widely used in observational cosmology is the Chevallier-Polarski-Linder (CPL) form:

$$w(a) = w_0 + w_a(1 - a)$$

This introduces a first-order Taylor expansion of $w$ in the scale factor around $a = 1$. The $\Lambda$CDM model corresponds to $w_0 = -1$, $w_a = 0$. When fitting this model to data, the energy density of the dark energy component generalizes to:

$$\rho_{\rm DE}(a) = \rho_{\rm DE,0}\,a^{-3(1 + w_0 + w_a)}\exp\left[-3w_a(1-a)\right]$$

which must be evaluated numerically at each step of the MCMC chain. The CMB, baryon acoustic oscillations (BAO), and supernovae together constrain $w_0$ and $w_a$ jointly, and their combined posteriors currently remain consistent with $\Lambda$CDM at the 95% confidence level.

### Critical Failure Modes and Their Physical Interpretations

**The Big Bang singularity** is the most fundamental boundary condition failure of the FLRW framework. As $a \to 0$, the energy density $\rho \to \infty$ for any $w > -1$ component, and all curvature invariants diverge. The Penrose-Hawking singularity theorems guarantee that general relativity cannot be extended through this point within its own framework. In practice, numerical integrators must be stopped at some $a_{\min} > 0$ (typically $a_{\min} = 10^{-5}$ or the energy scale of Big Bang Nucleosynthesis at $T \sim 10^9$ K), and observables should never be extrapolated into the pre-BBN epoch without incorporating physics beyond the standard model.

**The phantom divide** is the singularity that arises when the dark energy equation-of-state parameter crosses $w = -1$. For $w < -1$ (phantom dark energy), the energy density of dark energy grows with expansion, $\rho_{\rm DE} \propto a^{-3(1+w)}$, and the universe is driven toward a **Big Rip** singularity in finite cosmic time, at which point all gravitationally bound structures, then all atoms, are torn apart by the diverging expansion rate. CPL parameterizations that allow $w_a \neq 0$ can transiently cross the phantom divide, but single-field scalar field models cannot without introducing ghost instabilities. This is a failure mode in the theoretical modeling, not the numerical integration, and it must be flagged whenever a Markov chain sample ventures into $w_0 + w_a < -1$ territory.

**Numerical stiffness** in the full Boltzmann system (which couples the Friedmann equations to photon, neutrino, baryon, and dark matter perturbation equations) arises because the photon-baryon plasma before recombination oscillates on timescales $\sim (c_s k)^{-1}$ that are many orders of magnitude shorter than the Hubble time $H^{-1}$. The ratio of these timescales is roughly $k/aH$, which can exceed $10^3$ for small-scale modes ($k \sim 0.1$ Mpc$^{-1}$) during radiation domination. CAMB handles this by switching between a tight-coupling approximation (which analytically integrates the stiff oscillations) and a full numerical integration, controlled by a threshold parameter `tight_coupling_trigger` that the user should not loosen without validating outputs against cross-checks.

**Gauge artifacts** in perturbation theory are a failure mode that is subtle but endemic to cosmological computations. The Friedmann equations describe the unperturbed background, but computing the CMB power spectrum or the matter power spectrum requires perturbing the FLRW metric. The perturbations of the metric are not gauge-invariant: a pure coordinate transformation can generate or remove apparent density perturbations. The two standard gauge choices are the **synchronous gauge** (used by CAMB) and the **conformal Newtonian gauge** (used by CLASS by default). Physical observables like the CMB temperature anisotropy power spectrum $C_\ell$ are gauge-invariant and must agree between the two codes; discrepancies at the $0.1\%$ level in the unlensed power spectrum are routinely used as a validation cross-check in precision cosmology pipelines.

### Observational Workflow: Measuring $H(z)$ from Cosmic Chronometers

One of the cleanest direct probes of the Friedmann equations is the **cosmic chronometer method**, which measures $H(z)$ without assuming any cosmological model. The method exploits the fact that:

$$H(z) = -\frac{1}{1+z}\frac{dz}{dt}$$

so if one can measure the differential age $dt$ of the universe across a small redshift interval $dz$ using passively evolving elliptical galaxies as standard clocks, $H(z)$ follows directly. The practical workflow is as follows.

First, assemble a spectroscopic sample of massive, passively evolving galaxies (stellar mass $M_* > 10^{11}\,M_\odot$, specific star formation rate $< 10^{-11}$ yr$^{-1}$) spanning a redshift range, typically drawn from SDSS, zCOSMOS, or BOSS. Second, determine the stellar ages of these galaxies by fitting their spectral energy distributions or the 4000 Å break strength $D_n(4000)$ to stellar population synthesis models such as BC03 or MILES. Third, pair galaxies in narrow redshift bins $\Delta z \sim 0.02$–$0.1$, compute $\Delta t$ from the age difference, and divide by $-\Delta z / (1+z)$ to obtain $H(z)$. The dominant systematic is the stellar population model uncertainty, which introduces a $\sim 5$% systematic floor on $H(z)$ regardless of sample size. This systematic can be partially mitigated by using model-independent spectral indicators, but it cannot be eliminated entirely at present.

The resulting $H(z)$ measurements at $0 < z < 2$ can then be compared directly to the Friedmann prediction $H(z) = H_0 E(z)$ by running an MCMC fit over $\{H_0, \Omega_m, \Omega_\Lambda, w_0\}$ with uniform or physically motivated priors. The residuals from the best-fit model, plotted as $\Delta H / \sigma_H$ versus $z$, should be white noise with no systematic trend. A trend would indicate either an unmodeled systematic in the chronometer method or a genuine departure from the FLRW framework.

### The $H_0$ Tension: When the Friedmann Equations Strain Against Observation

No discussion of the Friedmann equations in the present era is complete without addressing the Hubble tension. The early-universe measurement of $H_0$ from the Planck CMB power spectrum, within $\Lambda$CDM, gives $H_0 = 67.4 \pm 0.5$ km s$^{-1}$ Mpc$^{-1}$. The late-universe measurement from the SH0ES team, anchoring the Cepheid-calibrated Type Ia supernova distance ladder, gives $H_0 = 73.0 \pm 1.0$ km s$^{-1}$ Mpc$^{-1}$. The discrepancy is now approximately $5\sigma$ and has survived every systematic scrutiny applied to both measurements.

The resolution almost certainly lies in one of three places: an unidentified systematic in either measurement, a modification to the standard FLRW+$\Lambda$CDM model that changes the sound horizon scale $r_s$ before recombination (the anchor of the CMB-based $H_0$), or new physics at late times that modifies the expansion rate below $z \sim 1$. Models in the first category include early dark energy, extra relativistic species ($\Delta N_{\rm eff} > 0$), and modified recombination history. Models in the second category include interacting dark energy and modified gravity theories. For a practitioner implementing Friedmann equation solvers and MCMC pipelines, the Hubble tension serves as a constant reminder that the first Friedmann equation is only as reliable as the physics we insert into the right-hand side: the geometry is correct, but our census of the energy content of the universe may yet be incomplete.

The Friedmann equations are not a relic of twentieth-century physics. They are the working equations of a living, contested observational science, and every new dataset from surveys like DESI, the Vera C. Rubin Observatory LSST, and the Euclid satellite will be confronted against their predictions. Mastery of their derivation, their numerical implementation, and their observational tests is not background knowledge for a cosmologist; it is the job itself.
