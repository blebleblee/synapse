# Lesson 2: Physical Mechanisms & Dynamical Equations

The architecture of our observable universe emerges from a remarkably sparse set of fundamental equations governing matter, energy, and spacetime geometry. Understanding cosmological evolution and thermodynamic behavior requires penetrating beneath phenomenological descriptions to expose the microscopic dynamical mechanisms that propagate information, redistribute energy, and drive systems toward equilibrium states. This lesson dissects the mathematical machinery underlying cosmological expansion, gravitational dynamics, thermodynamic state evolution, and the phase transitions that punctuate cosmic history. We adopt a physicist's operational stance: derive governing equations from first principles, identify their symmetries and conservation laws, then extract physically measurable predictions through explicit calculation.

## 1. Governing Differential Equations & Analytical Derivations

### Einstein's Field Equations and the Friedmann-Lemaître-Robertson-Walker Metric

The gravitational skeleton of cosmology resides in Einstein's field equations, which encode how matter-energy content curves spacetime geometry. In abstract tensorial form, these equations read

$$G_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu}$$

where $G_{\mu\nu} = R_{\mu\nu} - \frac{1}{2}R g_{\mu\nu}$ denotes the Einstein tensor constructed from the Ricci curvature tensor $R_{\mu\nu}$ and Ricci scalar $R$, $\Lambda$ represents the cosmological constant, $g_{\mu\nu}$ is the spacetime metric tensor, and $T_{\mu\nu}$ encodes the stress-energy content of all matter and radiation fields. The factor $8\pi G/c^4$ establishes dimensional consistency, with $G = 6.674 \times 10^{-11} \, \text{m}^3 \text{kg}^{-1} \text{s}^{-2}$ being Newton's gravitational constant and $c = 2.998 \times 10^8 \, \text{m/s}$ the speed of light.

For a homogeneous, isotropic universe—validated observationally through cosmic microwave background measurements showing temperature fluctuations at the $\Delta T/T \sim 10^{-5}$ level—the metric takes the Friedmann-Lemaître-Robertson-Walker (FLRW) form. In comoving spherical coordinates $(t, r, \theta, \phi)$, the line element becomes

$$ds^2 = -c^2 dt^2 + a(t)^2 \left[ \frac{dr^2}{1 - kr^2} + r^2(d\theta^2 + \sin^2\theta \, d\phi^2) \right]$$

where $a(t)$ is the dimensionless scale factor normalized such that $a(t_0) = 1$ at present time $t_0$, and the curvature parameter $k$ takes values $+1$ (closed spherical geometry), $0$ (flat Euclidean geometry), or $-1$ (open hyperbolic geometry). Current observational constraints from Planck satellite data indicate $|k| < 0.005$, consistent with spatial flatness to within measurement precision.

The dynamics of $a(t)$ emerge by substituting the FLRW metric into Einstein's field equations. For a perfect fluid stress-energy tensor $T_{\mu\nu} = (\rho + p/c^2)u_\mu u_\nu + p g_{\mu\nu}$ with energy density $\rho$, pressure $p$, and four-velocity $u^\mu$, the time-time component yields the first Friedmann equation:

$$H^2 = \left(\frac{\dot{a}}{a}\right)^2 = \frac{8\pi G}{3}\rho + \frac{\Lambda c^2}{3} - \frac{kc^2}{a^2}$$

Here $H(t) = \dot{a}/a$ defines the Hubble parameter, with present-day value $H_0 = 67.4 \pm 0.5 \, \text{km/s/Mpc}$ measured through Cepheid variable distance ladders and Type Ia supernovae standard candles. The spatial curvature term $-kc^2/a^2$ becomes negligible as the universe expands for $k = 0, \pm 1$, leaving vacuum energy $\Lambda$ and matter density $\rho$ as the dominant drivers of late-time acceleration or deceleration.

The second Friedmann equation, derived from the spatial trace of Einstein's equations, governs the acceleration of cosmic expansion:

$$\frac{\ddot{a}}{a} = -\frac{4\pi G}{3}\left(\rho + \frac{3p}{c^2}\right) + \frac{\Lambda c^2}{3}$$

This equation reveals that ordinary matter and radiation—both having positive energy density and positive or zero pressure—gravitationally decelerate expansion ($\ddot{a} < 0$), while the cosmological constant with effective equation of state $p = -\rho c^2$ drives accelerated expansion ($\ddot{a} > 0$). Observational evidence for late-time acceleration, awarded the 2011 Nobel Prize in Physics, implies a positive cosmological constant contributing $\Omega_\Lambda \approx 0.69$ of the critical density.

Energy conservation emerges not as an independent equation but as a mathematical consistency condition. Contracting the Bianchi identity $\nabla_\mu G^{\mu\nu} = 0$ yields the continuity equation

$$\dot{\rho} + 3H\left(\rho + \frac{p}{c^2}\right) = 0$$

which describes how energy density dilutes as the universe expands. For matter with negligible pressure ($p \ll \rho c^2$), integration gives $\rho_m \propto a^{-3}$, reflecting volume dilution. For radiation with equation of state $p = \rho c^2/3$, integration yields $\rho_r \propto a^{-4}$, capturing both volume dilution and redshift energy loss. For vacuum energy with $p = -\rho_\Lambda c^2$, the continuity equation enforces constant density $\rho_\Lambda = \text{const}$, explaining why dark energy dominates at late times.

### Analytical Solution for Matter-Dominated Expansion

Consider a spatially flat ($k=0$) universe dominated by pressureless matter ($p=0$) with negligible cosmological constant, appropriate for describing the era from matter-radiation equality at redshift $z \sim 3400$ until dark energy domination at $z \sim 0.3$. The first Friedmann equation simplifies to

$$\left(\frac{\dot{a}}{a}\right)^2 = \frac{8\pi G}{3}\rho_m$$

Using the matter continuity equation $\rho_m = \rho_{m,0} a^{-3}$ where $\rho_{m,0}$ is the present matter density, we obtain

$$\left(\frac{\dot{a}}{a}\right)^2 = \frac{8\pi G \rho_{m,0}}{3a^3}$$

Separating variables and integrating from initial scale factor $a_i$ at time $t_i$ to $a$ at time $t$:

$$\int_{a_i}^{a} a^{1/2} \, da = \sqrt{\frac{8\pi G \rho_{m,0}}{3}} \int_{t_i}^{t} dt$$

yields the power-law solution

$$a(t) = \left(\frac{3}{2}\sqrt{\frac{8\pi G \rho_{m,0}}{3}}\right)^{2/3}(t - t_i)^{2/3} \propto t^{2/3}$$

Setting $a(t_0) = 1$ at present time $t_0$ fixes the constant of integration. The Hubble parameter for this epoch becomes $H = \dot{a}/a = 2/(3t)$, giving a present age estimate $t_0 = 2/(3H_0) \approx 9.1 \, \text{Gyr}$ if matter alone dictated expansion—undershooting the observed $13.8 \, \text{Gyr}$ precisely because dark energy accelerates late-time expansion, increasing the age integral.

For a radiation-dominated flat universe with $p = \rho_r c^2/3$ and $\rho_r \propto a^{-4}$, identical integration methods yield $a(t) \propto t^{1/2}$, describing the early universe prior to matter-radiation equality. The transition between radiation and matter domination occurs when $\rho_r = \rho_m$, which defines the equality redshift

$$1 + z_{eq} = \frac{\rho_{m,0}}{\rho_{r,0}} = \frac{\Omega_{m,0}}{\Omega_{r,0}} \approx 3400$$

where $\Omega_{m,0} \approx 0.31$ and $\Omega_{r,0} \approx 9 \times 10^{-5}$ represent present-day density parameters for matter and radiation respectively.

### Thermodynamic Evolution and Entropy Generation

The thermodynamic state of the cosmic fluid couples intimately to expansion dynamics through the first law of thermodynamics. For a comoving volume element $V = a^3 V_0$ containing energy $E = \rho V$, the first law in differential form reads

$$dE = -p \, dV + T \, dS$$

where $T$ denotes temperature and $S$ entropy. Expanding the energy differential $dE = d(\rho a^3 V_0) = V_0(3\rho a^2 \, da + a^3 \, d\rho)$ and volume differential $dV = 3a^2 V_0 \, da$, substitution yields

$$a^3 d\rho + 3\rho a^2 da = -3p a^2 da + T \, dS$$

Dividing by $a^3 V_0$ and rearranging recovers the continuity equation $d\rho + 3H(\rho + p/c^2)dt = 0$ when entropy per comoving volume remains constant ($dS = 0$), confirming that adiabatic expansion conserves entropy in comoving coordinates. The entropy density $s = S/V$ for a relativistic gas of particles satisfies $s \propto T^3$ from statistical mechanics, while energy density scales as $\rho \propto T^4$ from Stefan-Boltzmann radiation laws. During adiabatic expansion, $s \propto a^{-3}$ implies $T \propto a^{-1}$, the familiar cosmological redshift relation for photon temperature.

Entropy generation occurs during non-adiabatic processes such as particle annihilations, phase transitions, and reheating after inflation. Consider electron-positron annihilation at $T \sim 0.5 \, \text{MeV}$ when thermal energy drops below the electron rest mass $m_e c^2 = 0.511 \, \text{MeV}$. Prior to annihilation, relativistic electrons, positrons, and photons maintain thermal equilibrium with $g_* = 11/2$ effective degrees of freedom (2 for photons, 7/2 each for electrons and positrons accounting for fermionic statistics). After annihilation deposits electron-positron rest mass energy into the photon bath, entropy conservation $s_\text{before} = s_\text{after}$ requires

$$g_{*,\text{before}} T_\text{before}^3 = g_{*,\text{after}} T_\text{after}^3$$

With $g_{*,\text{after}} = 2$ (photons only), this gives $T_\text{after}/T_\text{before} = (11/4)^{1/3} \approx 1.401$, explaining why neutrinos that decoupled before annihilation are cooler than photons by exactly this factor today: $T_\nu = (4/11)^{1/3} T_\gamma = 1.945 \, \text{K}$.

### Boltzmann Transport Equation and Non-Equilibrium Kinetics

When departure from thermal equilibrium becomes significant—during Big Bang Nucleosynthesis, recombination, or dark matter freeze-out—the full Boltzmann transport equation governs the evolution of phase-space distribution functions. For a particle species with distribution $f(\mathbf{x}, \mathbf{p}, t)$, the collisional Boltzmann equation in expanding coordinates reads

$$\frac{\partial f}{\partial t} - H |\mathbf{p}|^2 \frac{\partial f}{\partial |\mathbf{p}|} = C[f]$$

where the left side represents free-streaming and redshift effects, while $C[f]$ encodes collision integrals. For dark matter particles $X$ annihilating via $X + \bar{X} \leftrightarrow \text{SM}$ into Standard Model products, the collision term becomes

$$C[f] = -\langle \sigma v \rangle (n_X^2 - n_{X,\text{eq}}^2)$$

where $\langle \sigma v \rangle$ denotes the thermally-averaged annihilation cross section, $n_X$ the actual number density, and $n_{X,\text{eq}}$ the equilibrium density. Converting to the dimensionless variable $Y = n_X/s$ (number-to-entropy ratio), the Boltzmann equation for freeze-out becomes

$$\frac{dY}{dx} = -\frac{\sqrt{\pi}}{45} \frac{M_\text{Pl} m_X (g_{*S}/\sqrt{g_{*\rho}})}{x^2} \langle \sigma v \rangle (Y^2 - Y_\text{eq}^2)$$

with $x = m_X/T$, $M_\text{Pl} = 1.22 \times 10^{19} \, \text{GeV}$ the Planck mass, $m_X$ the dark matter mass, and $g_{*S}, g_{*\rho}$ effective degrees of freedom for entropy and energy density. Freeze-out occurs when the annihilation rate $\Gamma = n_X \langle \sigma v \rangle$ drops below the Hubble rate $H$, typically at $x_f \sim 20$-$25$. Numerical integration through freeze-out determines the relic density

$$\Omega_X h^2 \approx \frac{3 \times 10^{-27} \, \text{cm}^3/\text{s}}{\langle \sigma v \rangle}$$

explaining the observed dark matter density $\Omega_X h^2 = 0.12$ for weakly-interacting massive particles with $\langle \sigma v \rangle \sim 3 \times 10^{-26} \, \text{cm}^3/\text{s}$—the celebrated "WIMP miracle."

### Practical Computation: Cosmological Distance Measures

Observational cosmology relies on converting redshift measurements $z$ into physical distances, requiring numerical integration of the Friedmann equation. The comoving distance to an object at redshift $z$ is given by

$$d_C(z) = \frac{c}{H_0} \int_0^z \frac{dz'}{E(z')}$$

where the dimensionless Hubble parameter $E(z) = H(z)/H_0$ encodes the expansion history through density parameters:

$$E(z) = \sqrt{\Omega_{r,0}(1+z)^4 + \Omega_{m,0}(1+z)^3 + \Omega_{k,0}(1+z)^2 + \Omega_{\Lambda,0}}$$

with $\Omega_{k,0} = 1 - \Omega_{r,0} - \Omega_{m,0} - \Omega_{\Lambda,0}$ enforcing the constraint from spatial flatness. For a flat $\Lambda$CDM universe with $\Omega_{m,0} = 0.31$ and $\Omega_{\Lambda,0} = 0.69$ (neglecting radiation at low $z$), numerical integration using Simpson's rule with 1000 steps provides sufficient accuracy for most applications.

To implement this calculation, discretize the integral into $N$ steps with $\Delta z = z/N$. Apply Simpson's rule:

$$d_C(z) \approx \frac{c}{H_0} \frac{\Delta z}{3} \left[ \frac{1}{E(0)} + 4\sum_{i=1,3,5,...}^{N-1} \frac{1}{E(i\Delta z)} + 2\sum_{i=2,4,6,...}^{N-2} \frac{1}{E(i\Delta z)} + \frac{1}{E(z)} \right]$$

For $H_0 = 67.4 \, \text{km/s/Mpc}$, converting to SI units requires $H_0 = 2.184 \times 10^{-18} \, \text{s}^{-1}$, giving $c/H_0 = 4460 \, \text{Mpc}$ as the Hubble radius. The luminosity distance $d_L = (1+z)d_C$ accounts for both flux dilution and photon energy redshift, while angular diameter distance $d_A = d_C/(1+z)$ corrects for the angular size—redshift relation. Validate implementations by checking that $d_L(z=1) \approx 6600 \, \text{Mpc}$ for standard $\Lambda$CDM cosmology.

## 2. Microscopic vs. Macroscopic Phase Transitions

### Order Parameters and Symmetry Breaking in Cosmological Phase Transitions

The thermal history of the universe punctuated by a sequence of phase transitions as cooling reduced thermal energy below characteristic mass scales, breaking symmetries and altering the fundamental interactions. Understanding these transitions requires connecting microscopic quantum field dynamics to macroscopic thermodynamic observables through statistical mechanics and order parameter formalism. A phase transition manifests when a system's free energy landscape develops multiple minima, each corresponding to distinct phases with different symmetry properties.

The Ginzburg-Landau effective potential provides a phenomenological framework for describing phase transitions near critical temperatures. For a scalar order parameter field $\phi$ with expectation value $\langle \phi \rangle = 0$ in the symmetric phase and $\langle \phi \rangle \neq 0$ in the broken phase, the temperature-dependent effective potential takes the form

$$V_\text{eff}(\phi, T) = -\frac{1}{2}\mu^2(T)\phi^2 + \frac{1}{4}\lambda \phi^4 + V_0$$

where $\mu^2(T) = \mu_0^2 + \alpha T^2$ parameterizes the temperature dependence, $\lambda > 0$ ensures stability, and $V_0$ sets the vacuum energy. At high temperatures $T > T_c$ where $T_c = \sqrt{-\mu_0^2/\alpha}$, the quadratic coefficient $\mu^2(T) > 0$ makes the symmetric minimum $\phi = 0$ energetically favorable. Below $T_c$, $\mu^2(T) < 0$ destabilizes the symmetric minimum, and the field settles into one of two degenerate vacua at $\phi = \pm v(T)$ where $v(T) = \sqrt{\mu^2(T)/\lambda}$.

The order of the transition depends on potential topology. A second-order (continuous) transition occurs when the symmetric and broken minima coincide at $T_c$, with the order parameter evolving smoothly through zero. Including cubic terms $V_\text{eff} = -\frac{1}{2}\mu^2\phi^2 - \frac{1}{3}\beta\phi^3 + \frac{1}{4}\lambda\phi^4$ can generate a first-order transition where symmetric and broken phases coexist at distinct minima separated by an energy barrier. The transition proceeds through bubble nucleation: quantum tunneling or thermal fluctuations nucleate bubbles of the true vacuum that expand and collide, releasing latent heat $L = V(\phi_\text{false}) - V(\phi_\text{true})$ into the plasma.

### Electroweak Phase Transition and Baryogenesis

The electroweak phase transition at $T_\text{EW} \sim 160 \, \text{GeV}$ represents the universe's final major symmetry breaking, where the Higgs field acquired its vacuum expectation value $v = 246 \, \text{GeV}$, giving mass to $W^\pm, Z$ bosons and fermions through spontaneous symmetry breaking. The Standard Model Higgs potential

$$V(\phi, T) = -\mu^2(T)|\phi|^2 + \lambda(T)|\phi|^4$$

with temperature-dependent coefficients arising from thermal loop corrections determines whether the transition proceeded smoothly or through a first-order phase transition with bubble nucleation. For the observed Higgs mass $m_h = 125 \, \text{GeV}$, lattice simulations and perturbative calculations indicate a smooth crossover rather than a sharp first-order transition, disappointing hopes for electroweak baryogenesis within the minimal Standard Model.

Electroweak baryogenesis requires three Sakharov conditions: baryon number violation (provided by electroweak sphalerons), C and CP violation (present but insufficient in the Standard Model), and departure from thermal equilibrium (requiring a strong first-order transition). The strength of the phase transition is quantified by the ratio $\xi = v(T_c)/T_c$, where a strong transition requires $\xi > 1$ to suppress sphaleron processes in the broken phase that would wash out any generated baryon asymmetry. Extensions beyond the Standard Model—such as adding singlet scalars or modifying the Higgs sector—can strengthen the transition by adjusting the temperature-dependent effective potential.

During a first-order transition, the bubble wall velocity $v_w$ and thickness $L_w$ determine reaction rates and particle reflection probabilities. The wall velocity emerges from force balance between pressure difference $\Delta p = L/T$ and friction from particle scattering in the plasma. Typical velocities range from subsonic $v_w \sim 0.1c$ with thick walls dominated by diffusion, to detonations with $v_w \sim c$ and thin walls where particles penetrate and equilibrate. The CP-violating asymmetry generated at the wall depends on reflection coefficients for chiral fermions, computed by solving transport equations in the wall background.

### QCD Phase Transition and Quark-Hadron Confinement

The quantum chromodynamics (QCD) phase transition at $T_\text{QCD} \sim 150 \, \text{MeV}$ marked the confinement of quarks and gluons into hadrons, fundamentally altering the particle content and equation of state. Above the transition, the universe contained a quark-gluon plasma with free quarks $u, d, s$ and gluons interacting through the strong force. Below the transition, asymptotic freedom at high energy densities gave way to confinement, binding quarks into protons, neutrons, pions, and other hadrons.

Lattice QCD calculations with dynamically evolving quark fields and fine temporal/spatial lattices probe the QCD transition by computing the order parameter—the chiral condensate $\langle \bar{q}q \rangle$ for light quarks. These calculations reveal a smooth crossover rather than a sharp first-order transition for physical quark masses, with the pseudocritical temperature $T_{pc} = 156.5 \pm 1.5 \, \text{MeV}$ defined through the peak in chiral susceptibility. The equation of state $p(\epsilon)$ relating pressure to energy density shows rapid change near $T_{pc}$, with the sound speed squared $c_s^2 = dp/d\epsilon$ dipping to $\sim 0.15$ before rising to the conformal value $1/3$ at high temperatures.

The crossover nature means that quark and hadron degrees of freedom coexist across a temperature range $\Delta T \sim 30 \, \text{MeV}$, with the effective number of degrees of freedom interpolating smoothly. For baryon number conservation calculations during Big Bang Nucleosynthesis, the uncertainty in $g_{*S}$ arising from QCD equation of state details contributes subdominant but measurable corrections to predicted light element abundances. Observational constraints from deuterium-to-hydrogen ratio $D/H = (2.527 \pm 0.030) \times 10^{-5}$ and helium-4 mass fraction $Y_p = 0.2449 \pm 0.0040$ validate post-QCD thermodynamics within $3\%$ precision.

### Critical Phenomena and Correlation Lengths

Near continuous phase transitions, thermodynamic quantities exhibit power-law divergences characterized by critical exponents. The correlation length $\xi$—the distance over which fluctuations remain correlated—diverges as $\xi \sim |T - T_c|^{-\nu}$ where $\nu$ is the correlation length exponent. Other critical exponents govern heat capacity $C_V \sim |T-T_c|^{-\alpha}$, order parameter $\langle \phi \rangle \sim |T-T_c|^\beta$, and susceptibility $\chi \sim |T-T_c|^{-\gamma}$. These exponents satisfy scaling relations such as $\alpha + 2\beta + \gamma = 2$ (Rushbrooke inequality) and depend only on spatial dimensionality $d$ and order parameter dimensionality $n$, demonstrating universality across diverse physical systems.

For cosmological phase transitions, finite correlation lengths at critical points seed density perturbations that affect subsequent structure formation. During the QCD crossover, correlation lengths reach $\xi \sim (1-2) \, \text{fm}$ before falling rapidly as the system moves away from $T_{pc}$. These fluctuations could imprint signatures in primordial black hole formation or gravitational wave spectra, though detection remains beyond current sensitivity. For first-order transitions, bubble nucleation generates stochastic gravitational wave backgrounds with characteristic frequency $f_* \sim \beta/a_*$ determined by the nucleation rate parameter $\beta$ and scale factor at transition $a_*$.

### Defect Formation and Kibble-Zurek Mechanism

Spontaneous symmetry breaking during phase transitions generically produces topological defects—domain walls, cosmic strings, or monopoles—depending on the broken symmetry's homotopy group structure. When a scalar field with $U(1)$ symmetry transitions to a broken phase with degenerate vacua $\phi = v e^{i\theta}$, causally disconnected regions choose independent phases $\theta$. Along closed loops encircling phase singularities, the winding number $n = (2\pi)^{-1}\oint d\theta$ must be integer, trapping flux and forming cosmic strings with linear mass density $\mu \sim \eta^2$ set by the symmetry breaking scale $\eta$.

The Kibble-Zurek mechanism quantifies defect density produced during rapid quenches. As the system cools through $T_c$ at rate $\dot{T}$, equilibration time $\tau_\text{eq} \sim \xi/c_s$ grows while available time shrinks. The system freezes out when $\tau_\text{eq} \sim t$, determining the correlation length $\hat{\xi}$ at freeze-out. Near $T_c$, $\tau_\text{eq} \sim \xi_0 |T-T_c|^{-\nu z}$ where $\xi_0$ is microscopic length and $z$ the dynamical exponent. For quench rate $\dot{T}$, the freeze-out time scales as $\hat{t} \sim (\xi_0/\dot{T})^{1/(1+\nu z)}$, giving defect density

$$n_\text{defect} \sim \hat{\xi}^{-d} \sim \left(\frac{\xi_0}{\dot{T}}\right)^{-d/(1+\nu z)}$$

This scaling has been verified experimentally in superfluid helium, superconductors, and liquid crystals, and predicts cosmic string densities for GUT-scale symmetry breaking. For $\eta \sim 10^{16} \, \text{GeV}$, observational limits on cosmic string contributions to CMB temperature anisotropies constrain $G\mu/c^2 < 10^{-7}$, ruling out simple GUT scenarios unless additional dilution mechanisms operated.

## 3. Energy Transfer, Entropy & Rate Limitations

### Thermalization Timescales and Kinetic Equilibration

The concept of thermal equilibrium in cosmology requires careful scrutiny: a system reaches equilibrium when interaction rates exceed the expansion rate, allowing sufficient collisions to establish Maxwell-Boltzmann or Fermi-Dirac distributions before the expanding volume dilutes particles beyond interaction range. For a species with number density $n$ and interaction cross section $\sigma$, the interaction rate per particle is $\Gamma = n \langle \sigma v \rangle$ where $\langle \sigma v \rangle$ denotes the thermal average over velocity distributions. Comparing to the Hubble rate $H$, equilibrium persists when $\Gamma/H > 1$.

Consider neutrino decoupling during the MeV era. Neutrinos interact through weak interactions with characteristic cross section $\sigma_\nu \sim G_F^2 T^2$ where $G_F = 1.166 \times 10^{-5} \, \text{GeV}^{-2}$ is the Fermi constant. The interaction rate scales as $\Gamma_\nu \sim n_\nu \sigma_\nu c \sim G_F^2 T^5$ for relativistic neutrinos with $n_\nu \sim T^3$. Meanwhile, radiation domination gives $H \sim \sqrt{g_* G T^4/3}$ where $g_*$ counts effective relativistic degrees of freedom. Equating rates determines the decoupling temperature:

$$G_F^2 T_\nu^5 \sim \sqrt{G T_\nu^4} \implies T_\nu \sim \left(\frac{\sqrt{G}}{G_F^2}\right)^{2} \sim 1 \, \text{MeV}$$

At this temperature, neutrino interactions freeze out and the neutrino distribution function free-streams thereafter, preserving the Fermi-Dirac form but with temperature diluted by subsequent expansion. Precision calculations including QED corrections and finite-temperature effects give $T_\nu = 1.4 \, \text{MeV}$ for electron neutrinos, slightly shifted by electron-positron annihilation.

### Transport Coefficients and Diffusion Processes

When interaction rates remain finite but insufficient to maintain strict equilibrium, transport theory describes approach toward equilibrium through diffusion, thermal conduction, and viscosity. The diffusion coefficient $D$ quantifies spatial spreading of number density perturbations through random walk:

$$D = \frac{1}{3}\lambda_\text{mfp} \langle v \rangle$$

where $\lambda_\text{mfp} = 1/(n\sigma)$ is the mean free path and $\langle v \rangle$ the mean particle speed. For photons in the pre-recombination plasma, Thomson scattering on free electrons gives $\sigma_T = 6.65 \times 10^{-29} \, \text{m}^2$ and $\lambda_\gamma \sim 100 \, \text{pc} (1+z)^{-3}$ at $z = 1100$. The photon diffusion length $r_\text{diff} = \sqrt{D t}$ over cosmic time $t$ determines the maximum scale for causal communication, imprinting the acoustic scale in CMB anisotropies.

Shear viscosity $\eta$ and bulk viscosity $\zeta$ encode momentum transport and resistance to compression. For a relativistic gas, kinetic theory gives $\eta \sim nT\tau$ where $\tau = \lambda_\text{mfp}/c$ is the collision time. During the quark-hadron crossover, lattice QCD calculations constrain the shear viscosity to entropy ratio $\eta/s \sim 0.1$, approaching but not reaching the conjectured quantum bound $\eta/s \geq \hbar/(4\pi k_B)$ from AdS/CFT duality. Viscous corrections to the perfect fluid stress tensor modify cosmological perturbation evolution, suppressing power on small scales that enter the horizon during high-viscosity epochs.

### Photon-Baryon Fluid Dynamics and Acoustic Oscillations

Prior to recombination, photons and baryons formed a tightly-coupled fluid through Compton scattering and Coulomb interactions. The momentum transfer rate $\Gamma_\gamma = n_e \sigma_T c$ vastly exceeded $H$ until $z \sim 1100$, locking photons and baryons into a single-temperature fluid with effective pressure $p = \rho_\gamma c^2/3$ dominated by relativistic photons. Perturbations in this fluid obey coupled wave equations derived from energy-momentum conservation.

For a density perturbation $\delta_\gamma$ and velocity divergence $\theta = \nabla \cdot \mathbf{v}$, the linearized fluid equations in Fourier space become

$$\dot{\delta}_\gamma = -\frac{4}{3}\theta + \frac{4}{3}\dot{h}$$

$$\dot{\theta} = k^2\left(\frac{c_s^2}{c^2}\delta_\gamma + \frac{\delta_b}{4}\right) - \frac{\dot{a}}{a}\theta$$

where $h$ denotes metric perturbations, $\delta_b$ the baryon density contrast, $k$ the comoving wavenumber, and $c_s = c/\sqrt{3(1+3\rho_b/(4\rho_\gamma))}$ the sound speed accounting for baryon loading. These equations describe acoustic oscillations with characteristic frequency $\omega = k c_s$. Modes that enter the horizon (when $k = a H$) at different times oscillate through different phases before decoupling, imprinting peaks and troughs in the CMB power spectrum.

The angular scale of the first acoustic peak corresponds to the sound horizon at recombination:

$$r_s(z_*) = \int_{z_*}^\infty \frac{c_s(z)}{H(z)} dz \approx 144 \, \text{Mpc}$$

where $z_* = 1090$ marks the photon decoupling surface. This projects to an angular scale $\theta_* = r_s/d_A(z_*)$ where $d_A$ is the angular diameter distance. Planck satellite measurements give $\theta_* = 0.596^\circ$, corresponding to multipole $\ell_* = \pi/\theta_* \approx 300$. The peak positions encode geometric information about spatial curvature through the angular diameter distance relation, while peak heights reflect baryon density through the baryon-to-photon ratio.

### Radiative Transfer and Photon Decoupling

The visibility function $g(\tau)$ quantifies the probability distribution for when a CMB photon last scattered, where $\tau = \int n_e \sigma_T c \, dt$ denotes the optical depth. Defining $\kappa = -d\tau/d\eta$ as the differential optical depth per conformal time $\eta = \int c dt/a$, the visibility function becomes $g = \kappa e^{-\tau}$, peaked at $\tau \sim 1$ when scattering transitions from frequent to rare. The visibility function width $\Delta \eta \sim (\kappa_*)^{-1}$ sets the thickness of the last scattering surface, approximately 50 comoving Mpc for instantaneous recombination but broadened by residual ionization tails.

Solving the radiative transfer equation determines temperature anisotropies $\Theta(\mathbf{n}, \eta) = \Delta T(\mathbf{n}, \eta)/T_0$ along direction $\mathbf{n}$ and time $\eta$:

$$\frac{\partial \Theta}{\partial \eta} + \mathbf{n} \cdot \nabla \Theta = -\kappa[\Theta - \Theta_0 - \mathbf{n} \cdot \mathbf{v}_b] + \frac{1}{4}\dot{h} + \Phi$$

where $\Theta_0$ is the monopole, $\mathbf{v}_b$ the baryon velocity, and $\Phi, h$ metric potentials. The first term represents scattering that isotropizes the distribution, while source terms encode gravitational redshift and Doppler shifts. Expanding $\Theta$ in spherical harmonics and evolving the coupled hierarchy of multipole moments from initial conditions through recombination yields predictions for the CMB temperature and polarization power spectra.

### Entropy Production and Irreversibility

While comoving entropy remains constant during adiabatic expansion, true entropy increases during dissipative processes. Quantifying entropy production requires examining the second law in expanding spacetime. For a fluid with entropy current $s^\mu$, the entropy production rate per volume is

$$\frac{dS}{dV dt} = \nabla_\mu s^\mu \geq 0$$

Viscous stresses generate entropy at rate $\Pi^{\mu\nu}\partial_\mu u_\nu / T$ where $\Pi^{\mu\nu}$ denotes the viscous stress tensor. For shear viscosity with $\Pi^{\mu\nu} = -2\eta\sigma^{\mu\nu}$ and shear rate tensor $\sigma^{\mu\nu} = \nabla^{(\mu}u^{\nu)} - \frac{1}{3}\Theta h^{\mu\nu}$, the entropy production becomes

$$\frac{dS}{dVdt} = \frac{\eta}{T}\sigma_{\mu\nu}\sigma^{\mu\nu} \geq 0$$

confirming that viscosity irreversibly increases entropy. During violent events like phase transitions or structure formation shocks, these dissipative terms become significant, converting bulk kinetic energy into heat and increasing total entropy.

The total entropy of the observable universe can be estimated from the entropy density in the CMB, $s_\gamma = (2\pi^2/45)g_* T^3 \approx 2900 \, \text{cm}^{-3}$ for current temperature $T_0 = 2.725 \, \text{K}$. Integrating over the observable volume $(4\pi/3)(c/H_0)^3$ gives $S_\text{universe} \sim 10^{88} k_B$. Yet black holes contain vastly more entropy proportional to horizon area: a solar-mass black hole harbors $S_{BH} \sim 10^{54} k_B$ while supermassive black holes reach $10^{90} k_B$. The ultimate entropy budget at heat death, when all matter accretes into black holes which subsequently evaporate via Hawking radiation, will be dominated by the final photons and gravitons carrying away the black hole entropy.

### Observational Validation Through Precision Measurements

The theoretical framework presented here makes quantitative predictions testable through precision cosmological observables. The CMB temperature power spectrum measured by Planck agrees with $\Lambda$CDM predictions at the sub-percent level across multipoles $2 \leq \ell \leq 2500$, constraining parameters like $\Omega_b h^2 = 0.02237 \pm 0.00015$ and $\Omega_c h^2 = 0.1200 \pm 0.0012$. Baryon acoustic oscillation measurements from galaxy surveys trace the sound horizon scale into the low-redshift universe, validating distance-redshift relations. Type Ia supernovae distance moduli confirm accelerated expansion with systematic uncertainties now approaching statistical errors.

Remaining tensions include the $4\sigma$ discrepancy between CMB-inferred $H_0 = 67.4 \pm 0.5 \, \text{km/s/Mpc}$ and local distance ladder measurements $H_0 = 73.0 \pm 1.0 \, \text{km/s/Mpc}$. Proposed explanations range from systematic errors in Cepheid calibrations to new physics such as early dark energy or varying fundamental constants. Resolving this tension requires both improved observational techniques—James Webb Space Telescope Cepheid observations, gravitational wave standard sirens—and theoretical innovations exploring extensions to $\Lambda$CDM. Similarly, the $\sigma_8$ tension between CMB measurements of matter clustering amplitude and weak lensing surveys motivates reexamination of structure formation physics including neutrino masses, modified gravity, or baryonic feedback in galaxy formation.

The thermodynamic and dynamical mechanisms dissected in this lesson provide the quantitative foundation for understanding cosmic evolution from the Planck epoch through structure formation. Mastery requires not merely memorizing equations but developing physical intuition for when approximations break down, which effects dominate at each epoch, and how microscopic physics scales up to cosmic observables. The exercises that follow guide you through explicit calculations that build this intuition through hands-on problem solving.
