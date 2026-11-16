# Lesson 2: Physical Mechanisms & Dynamical Equations

---

## 1. Governing Differential Equations & Analytical Derivations

The first question any experimental physicist must resolve before entering the laboratory is deceptively simple: what equation of motion actually governs the system I am about to probe? In energy science, this question carries immediate practical weight. Whether you are characterizing the discharge curve of a lithium-ion cell, measuring heat flux through a thermoelectric module, or tracking the photocurrent transient in a perovskite solar absorber, the instrument in your hand is sampling the solution to some underlying differential equation. Knowing its form tells you which parameters to control, which to vary, and — critically — which experimental signatures betray a change in physical mechanism.

### The Action Principle as a Diagnostic Compass

The cleanest entry point is the Principle of Least Action. For any conservative energy-transduction system described by generalized coordinates $q_i$ and their time derivatives $\dot{q}_i$, the dynamics follow from demanding that the action integral

$$S = \int_{t_1}^{t_2} \mathcal{L}(q_i, \dot{q}_i, t)\, dt$$

be stationary under arbitrary variations $\delta q_i$ that vanish at the endpoints. The resulting Euler-Lagrange equations,

$$\frac{d}{dt}\frac{\partial \mathcal{L}}{\partial \dot{q}_i} - \frac{\partial \mathcal{L}}{\partial q_i} = 0,$$

are not merely elegant formalism. They are a systematic recipe for constructing the correct equation of motion for any coupled energy store. When you model an electrochemical cell, the generalized coordinate might be the charge $q$ transferred across the interface; the kinetic energy analogue is the magnetic energy $\tfrac{1}{2}L\dot{q}^2$ stored in lead inductance, and the potential energy analogue is the electrochemical free energy of the electrode–electrolyte pair. Applying the Euler-Lagrange equation directly recovers the governing circuit equation without requiring you to invoke Kirchhoff's rules as an axiom. More importantly, the Lagrangian formulation immediately exposes every conserved quantity through Noether's theorem: if $\mathcal{L}$ is independent of an explicit coordinate $q_i$, the conjugate momentum $p_i = \partial \mathcal{L}/\partial \dot{q}_i$ is constant in time. In a lossless LC resonator this is exactly charge conservation; in a rotating flywheel energy store it is angular momentum. Identifying these symmetries in your experimental setup tells you which quantities will drift only under dissipation and which will drift under coupling — a distinction that separates systematic error from physical signal.

### Drift-Diffusion and the Continuity Equation

In solid-state energy devices — photovoltaic cells, thermoelectrics, fuel-cell electrodes — the governing equations couple charge and heat transport through a shared continuity structure. For charge carriers of density $n$ moving under an electric field $\mathcal{E}$ and a concentration gradient, the current density $J$ obeys the drift-diffusion equation:

$$J = q\mu n \mathcal{E} + qD\frac{\partial n}{\partial x},$$

where $q$ is the elementary charge, $\mu$ is carrier mobility, and $D$ is the diffusion coefficient related to $\mu$ through the Einstein relation $D = \mu k_B T / q$. This relation is not merely a convenience; it is the thermodynamic statement that in equilibrium the drift and diffusion currents exactly cancel, enforcing zero net flux. Any experimental deviation from the Einstein ratio — measurable by independently extracting $\mu$ from Hall-effect data and $D$ from time-resolved photoluminescence decay — signals either a non-equilibrium carrier temperature or a polaronic correction to the band picture.

The continuity equation couples this current to the carrier density:

$$\frac{\partial n}{\partial t} = \frac{1}{q}\frac{\partial J}{\partial x} + G - R,$$

where $G$ is the volumetric generation rate and $R$ is the recombination rate. In a solar cell under illumination, $G$ is set by the absorbed photon flux and the absorption coefficient $\alpha(\lambda)$ of the material. In practice, you measure $G$ indirectly by integrating the external quantum efficiency (EQE) spectrum against the AM1.5G solar spectrum using a calibrated integrating-sphere setup; the resulting short-circuit current density $J_{sc}$ is the spatially integrated generation minus all bulk and surface recombination losses.

The practical consequence of the continuity equation is that every transient you record — a step in illumination, a voltage pulse, a temperature ramp — carries a time constant $\tau$ that is set by the balance of generation, recombination, and transport. For bulk recombination dominated by trap-assisted Shockley-Read-Hall processes, the minority carrier lifetime is

$$\tau_{SRH} = \frac{\tau_{p0}(n_0 + n_1 + \Delta n) + \tau_{n0}(p_0 + p_1 + \Delta n)}{n_0 + p_0 + \Delta n},$$

where $n_0$, $p_0$ are equilibrium carrier densities, $n_1$, $p_1$ are the carrier densities when the Fermi level coincides with the trap energy, $\Delta n$ is the excess carrier density, and $\tau_{n0}$, $\tau_{p0}$ are the fundamental capture time constants for electrons and holes respectively. At low injection ($\Delta n \ll n_0 + p_0$), this simplifies to a single exponential decay that you can resolve with time-correlated single-photon counting (TCSPC). At high injection, the apparent lifetime rises toward $\tau_{n0} + \tau_{p0}$, a telltale signature that you can use to distinguish trap recombination from Auger recombination, which instead accelerates at high carrier density with a rate $R_{Auger} = C_n n^2 p + C_p n p^2$.

### Poisson's Equation and Built-In Fields

No carrier transport analysis is self-consistent without coupling the drift-diffusion equation to the electrostatic potential through Poisson's equation:

$$\frac{\partial^2 \phi}{\partial x^2} = -\frac{\rho}{\epsilon_0 \epsilon_r} = -\frac{q(p - n + N_D^+ - N_A^-)}{\epsilon_0 \epsilon_r},$$

where $\phi$ is the electrostatic potential, $\rho$ is the net charge density, $\epsilon_r$ is the relative permittivity of the material, and $N_D^+$, $N_A^-$ are the ionized donor and acceptor concentrations. In a p-n junction at equilibrium, integrating Poisson's equation across the depletion region of width $W = x_n + x_p$ gives the built-in potential

$$V_{bi} = \frac{q N_A x_p^2}{2\epsilon_0 \epsilon_r} + \frac{q N_D x_n^2}{2\epsilon_0 \epsilon_r},$$

and the peak electric field at the metallurgical junction

$$\mathcal{E}_{max} = \frac{q N_A x_p}{\epsilon_0 \epsilon_r} = \frac{q N_D x_n}{\epsilon_0 \epsilon_r}.$$

You measure $V_{bi}$ and the depletion width in the laboratory through capacitance-voltage (C-V) profiling. At reverse bias $V_r$, the depletion width grows as

$$W(V_r) = \sqrt{\frac{2\epsilon_0 \epsilon_r}{q}\left(\frac{1}{N_A} + \frac{1}{N_D}\right)(V_{bi} + V_r)},$$

so the junction capacitance per unit area is $C = \epsilon_0 \epsilon_r / W$. Plotting $1/C^2$ against applied voltage yields a straight line whose slope gives the doping density and whose intercept on the voltage axis gives $V_{bi}$. The practical procedure is as follows.

**C-V Profiling Protocol:**

1. Mount the device in a shielded coaxial fixture (e.g., a Signatone probe station) with the chuck connected to the LCR meter's low terminal and the top contact to the high terminal. Guard the fixture to eliminate stray cable capacitance, which corrupts measurements below 10 pF.
2. Set the AC excitation amplitude to 25–50 mV rms. The excitation must remain small enough that $\delta V_{AC} \ll k_B T / q \approx 26\,\text{mV}$ to avoid driving the junction into nonlinear response.
3. Sweep the DC bias from forward 0.2 V to reverse $-5$ V in steps of 50 mV, waiting 100 ms at each step for the charge to redistribute before triggering the LCR measurement.
4. Measure at 100 kHz for silicon junctions. For high-resistivity perovskite or organic semiconductor junctions, drop to 1–10 kHz to allow carriers to follow the AC perturbation; at higher frequencies these materials exhibit a frequency-independent geometric capacitance that obscures the depletion physics.
5. Compute $1/C^2$ at each bias point, fit a linear regression to the region of complete depletion, and extract slope $m$ and intercept $b$. The doping density follows as $N = 2/(q\epsilon_0\epsilon_r m)$ and the built-in potential as $V_{bi} = -b/m$.
6. Cross-check $V_{bi}$ against the open-circuit voltage $V_{oc}$ under illumination; for a well-passivated junction, $V_{oc}$ should approach $V_{bi}$ minus roughly $3k_BT/q$.

### Heat Conduction and the Fourier–Biot Equation

Thermal energy storage and transport obey a governing equation structurally identical to the carrier diffusion equation. The heat equation in a medium with thermal conductivity $\kappa$, mass density $\rho_m$, and specific heat $c_p$ is

$$\rho_m c_p \frac{\partial T}{\partial t} = \nabla \cdot (\kappa \nabla T) + \dot{Q}_{gen},$$

where $\dot{Q}_{gen}$ is the volumetric heat generation rate from Joule heating, chemical reaction, or radiation absorption. The thermal diffusivity $\alpha_{th} = \kappa / (\rho_m c_p)$ controls how fast a temperature disturbance propagates through the medium. A high thermal diffusivity means the material equilibrates quickly; a low diffusivity means temperature gradients persist. Thermoelectric generators exploit the interplay between this equation and the Seebeck effect: a temperature gradient $\nabla T$ drives a thermoelectric voltage $V = S \Delta T$, where $S$ is the Seebeck coefficient in units of $\text{V K}^{-1}$. The figure of merit $ZT = S^2 \sigma T / \kappa$ embeds the competition between electrical power output ($S^2\sigma$) and thermal leakage ($\kappa$); maximizing $ZT$ requires simultaneously large $S$, high electrical conductivity $\sigma$, and low thermal conductivity, three properties that are coupled through carrier density and therefore deeply antagonistic in conventional semiconductors.

Measuring $ZT$ directly requires combining three independent experiments on the same specimen. You measure $\sigma$ using a standard four-probe van der Pauw geometry on a thin square lamella. You measure $S$ by imposing a known temperature difference $\Delta T$ across the sample using a resistive heater on one face and a heat sink on the other, reading both $\Delta T$ with calibrated type-K thermocouples and the resulting open-circuit Seebeck voltage with a nanovoltmeter, then computing $S = \Delta V / \Delta T$. You measure $\kappa$ using the laser flash method: a short laser pulse deposits energy on the front face of a disc-shaped specimen while an infrared detector records the temperature rise on the rear face; fitting the resulting transient to the Cowan model gives $\alpha_{th}$, and $\kappa$ follows from $\kappa = \alpha_{th} \rho_m c_p$ where $c_p$ is measured in a simultaneous differential scanning calorimetry (DSC) run. The uncertainty in $ZT$ accumulates from all three measurements, so a careful error propagation using

$$\left(\frac{\delta(ZT)}{ZT}\right)^2 = \left(\frac{2\delta S}{S}\right)^2 + \left(\frac{\delta \sigma}{\sigma}\right)^2 + \left(\frac{\delta \kappa}{\kappa}\right)^2$$

is not optional; in a typical lab setup where each quantity carries $\pm 5\%$ uncertainty, the combined uncertainty in $ZT$ reaches $\pm 11\%$, large enough to mask meaningful differences between materials unless measurement protocols are rigorously standardized.

---

## 2. Microscopic vs. Macroscopic Phase Transitions

A phase transition is the most dramatic signature a thermodynamic system can display: an abrupt or continuous change in the structure of its equilibrium state as an external parameter — temperature, pressure, field strength — crosses a critical threshold. For the experimental scientist working on energy materials, phase transitions are both a hazard and a resource. The lithium-ion cell that undergoes an order-disorder transition in its cathode lattice during cycling will degrade; the shape-memory alloy actuator exploits a martensitic transformation to convert heat directly into mechanical work; the ferroelectric capacitor stores energy by switching between two polarization states. Understanding the physical mechanism at the microscopic level is what separates a researcher who can engineer the transition from one who merely observes it.

### Landau Theory and the Order Parameter

The unifying language for phase transitions is Landau's theory of continuous (second-order) transitions. The central object is the order parameter $\phi$, a quantity that is zero in the disordered phase and acquires a nonzero value in the ordered phase. For a ferromagnet, $\phi$ is the spontaneous magnetization; for a ferroelectric, it is the electric polarization; for a superconductor, it is the amplitude of the macroscopic quantum condensate wave function. Landau's insight was that near the critical point, the free energy density can be expanded as a power series in $\phi$ constrained by the symmetry of the system:

$$f(\phi, T) = f_0 + a(T)\phi^2 + b\phi^4 + c\phi^6 + \cdots$$

For a system with inversion symmetry, odd powers vanish. The coefficient $a(T)$ changes sign at the transition temperature $T_c$, with $a(T) \approx a_0(T - T_c)$ for $a_0 > 0$. When $b > 0$, minimizing $f$ with respect to $\phi$ gives $\phi = 0$ for $T > T_c$ and

$$\phi^2 = -\frac{a(T)}{2b} = \frac{a_0(T_c - T)}{2b}$$

for $T < T_c$, so the order parameter grows as $\phi \propto (T_c - T)^{1/2}$ — the mean-field critical exponent of $\beta = 1/2$. This prediction becomes testable the moment you identify your order parameter and choose the right experimental probe: neutron diffraction for structural order, magnetometry for magnetic order, second-harmonic generation (SHG) for ferroelectric polarization, or specific heat anomaly (the $\lambda$ anomaly in $c_p$) for virtually any symmetry-breaking transition.

When $b < 0$, the free energy develops a double-well structure at a temperature above $T_c$, and the transition jumps discontinuously — this is the first-order scenario. The hallmark in the laboratory is hysteresis: the transition occurs at different temperatures on heating and cooling, and the sample absorbs or releases latent heat $L = T_c \Delta s$ at the transition, detectable as a sharp peak in a DSC trace. The width of the hysteresis loop quantifies the kinetic barrier between the two phases and is controlled by nucleation kinetics rather than thermodynamics alone.

### Nucleation Kinetics and the Classical Framework

A first-order transition does not proceed instantaneously when the thermodynamic condition is met. The new phase must nucleate from the old one, and nucleation requires the formation of a fluctuation large enough that the volume free-energy gain outweighs the surface-energy penalty of creating a new interface. For a spherical nucleus of radius $r$ forming in a matrix with a volumetric driving force $\Delta G_v < 0$ and a surface energy $\gamma$, the total free energy of formation is

$$\Delta G(r) = \frac{4}{3}\pi r^3 \Delta G_v + 4\pi r^2 \gamma.$$

This function has a maximum at the critical nucleus radius

$$r^* = -\frac{2\gamma}{\Delta G_v},$$

and the activation barrier at that radius is

$$\Delta G^* = \frac{16\pi \gamma^3}{3(\Delta G_v)^2}.$$

The nucleation rate follows an Arrhenius form $J = J_0 \exp(-\Delta G^* / k_B T)$, which explains why a material can be undercooled substantially below $T_c$ before the new phase appears at a measurable rate — the barrier $\Delta G^*$ shrinks only as the square of the driving force, so a modest undercooling leaves the barrier prohibitively large. This is why lithium iron phosphate (LFP) cathode particles, which undergo a first-order two-phase reaction during lithiation, can be driven into a metastable solid-solution state at high charge-discharge rates: the nucleation barrier is not overcome on the timescale of rapid cycling, and the phase transformation is kinetically bypassed.

You can measure nucleation rates directly using isothermal calorimetry. Place the sample in a thermally equilibrated calorimeter at a fixed undercooling $\Delta T = T_c - T_{hold}$, and monitor the heat flow as a function of time. The onset of exothermic (or endothermic) signal marks nucleation; the subsequent rise and fall traces the Avrami-Johnson-Mehl transformation kinetics:

$$f(t) = 1 - \exp\left(-\frac{\pi}{3} J \dot{r}^3 t^4\right),$$

where $f(t)$ is the transformed volume fraction, $J$ is the nucleation rate, and $\dot{r} = dr/dt$ is the growth velocity of the transformed domain. By fitting this model to calorimetric data at several undercoolings, you extract $J(T)$ and $\dot{r}(T)$ independently, and from their temperature dependencies recover both the nucleation barrier $\Delta G^*$ and the growth activation energy.

### Microscopic Origin: Phonon Soft Modes and Electronic Instabilities

At the atomic scale, many structural phase transitions are driven by the softening of a particular phonon mode: a collective lattice vibration whose restoring force vanishes as the temperature approaches $T_c$ from above. This is the concept of a soft mode, and it is one of the most experimentally accessible microscopic signatures of an impending transition. The frequency of the soft mode follows

$$\omega_s^2(T) \propto (T - T_c),$$

so the mode frequency drops to zero at $T_c$, signaling that the lattice has lost stability against that particular atomic displacement pattern. In perovskite oxides like barium titanate (BaTiO₃) — the archetypal ferroelectric used in capacitive energy storage and piezoelectric harvesting — the soft mode is an optical phonon at the Brillouin zone center involving the displacement of the Ti$^{4+}$ cation relative to the oxygen octahedron cage.

You measure soft-mode behavior with Raman spectroscopy or inelastic neutron scattering. In a temperature-dependent Raman experiment on BaTiO₃, you will observe a low-frequency mode that progressively red-shifts as the sample is heated toward the cubic-to-tetragonal transition near 393 K. The practical procedure for a temperature-dependent Raman run is as follows.

**Temperature-Dependent Raman Protocol (Perovskite Ferroelectrics):**

1. Mount the specimen in a Linkam THMS600 or equivalent temperature-controlled stage under dry nitrogen purge to prevent surface oxidation and moisture condensation on the optical window.
2. Align a 532 nm diode-pumped solid-state laser in backscattering geometry ($\bar{z}(xx)z$ configuration to access $A_1$ symmetry modes). Keep incident power below 2 mW on a $1\,\mu\text{m}^2$ spot to avoid local laser heating, which would artificially shift the apparent transition temperature. Verify this by confirming that the peak position does not drift when power is halved.
3. Set the spectrometer to cover 50–1000 cm$^{-1}$ using a 1800 gr/mm grating with a notch filter to suppress the Rayleigh line. Collect spectra with 30 s integration, averaging three accumulations.
4. Ramp temperature from 25 °C to 450 °C in 10 K steps, equilibrating for 2 minutes at each set point before acquisition. The 10 K step is small enough to resolve the transition onset but fast enough to complete the run before sample drift or degradation.
5. Fit each spectrum using Lorentzian line profiles. Track the peak position $\omega_s(T)$ and the linewidth $\Gamma(T)$ of the low-frequency soft mode; $\Gamma$ broadens critically near $T_c$ because the soft mode lifetime diverges as the restoring force vanishes.
6. Plot $\omega_s^2$ versus $T$. A linear fit to the high-temperature data extrapolates to $\omega_s^2 = 0$ at $T_c$, providing a spectroscopic determination of the transition temperature that is independent of the macroscopic polarization measurement.

For electronic phase transitions — the metal-to-insulator transition in vanadium dioxide (VO₂), or the charge-density-wave formation in transition metal dichalcogenides used in intercalation batteries — the driving instability is not phononic but electronic: a Peierls-type nesting of the Fermi surface at wavevector $\vec{q} = 2k_F$ that opens a gap at the Fermi level and lowers the total electronic energy. The experimental fingerprint is an abrupt change in resistivity by several orders of magnitude across the transition, often within a temperature window of only a few kelvin. In VO₂, the resistivity drops by $10^4$ across the 68 °C transition because the monoclinic insulating phase, stabilized by V–V dimerization, gives way to a rutile metallic phase where the $d_{x^2-y^2}$ band crosses the Fermi level. Measuring this with a four-probe resistance setup through the transition gives you a sharply reproducible switching curve that you can use to characterize the transition width, the hysteresis, and the cycling stability simultaneously.

---

## 3. Energy Transfer, Entropy & Rate Limitations

Every real energy conversion process operates at an efficiency below the thermodynamic limit, and the gap between the theoretical ceiling and the measured performance is paid for in entropy production. Understanding exactly where entropy is generated — and at what rate — is the foundation of practical energy engineering. It tells you whether a system is limited by thermodynamics, by kinetics, by transport, or by materials defects, and therefore where intervention will yield the greatest return.

### The Second Law as a Rate Equation

The second law of thermodynamics, in its most useful form for a process operating between a heat source at $T_H$ and a heat sink at $T_C$, states that the entropy of the universe cannot decrease:

$$\frac{dS_{universe}}{dt} = \frac{dS_{system}}{dt} + \frac{dS_{surroundings}}{dt} \geq 0,$$

with equality holding only for a reversible process. For a steady-state device operating at power output $P$ and rejecting waste heat $\dot{Q}_C$ to the cold reservoir, the entropy production rate is

$$\dot{\sigma} = \frac{\dot{Q}_C}{T_C} - \frac{\dot{Q}_H}{T_H} = \dot{Q}_H\left(\frac{1}{T_C} - \frac{1}{T_H}\right) - \frac{P}{T_C}.$$

The Carnot efficiency $\eta_C = 1 - T_C/T_H$ corresponds to $\dot{\sigma} = 0$, but it is achieved only at zero power output — an infinitely slow, quasi-static process. The practically relevant question is: what is the efficiency at maximum power? Curzon and Ahlborn showed in 1975 that for an endoreversible engine — one in which all entropy production is localized to the finite thermal conductance between the working fluid and the reservoirs, while the working cycle itself remains reversible — the efficiency at maximum power is

$$\eta_{CA} = 1 - \sqrt{\frac{T_C}{T_H}}.$$

For a steam turbine operating between 565 °C (838 K) and 35 °C (308 K), the Carnot limit is 63.3% while the Curzon-Ahlborn efficiency is 39.4%, very close to the actual measured efficiencies of 36–40% for well-designed modern turbines. This agreement is not coincidental; it reflects that the dominant irreversibility in a large turbine is indeed heat transfer across a finite temperature difference, not fluid friction or shock losses.

### Chemical Potential and Electrochemical Rate Laws

In electrochemical energy storage and conversion — batteries, fuel cells, electrolyzers — the relevant energy currency is the electrochemical potential of species $i$:

$$\tilde{\mu}_i = \mu_i^0 + RT\ln a_i + z_i F\phi,$$

where $\mu_i^0$ is the standard chemical potential, $a_i$ is the activity of species $i$, $z_i$ is its charge number, $F = 96{,}485\,\text{C mol}^{-1}$ is the Faraday constant, and $\phi$ is the local electric potential. The driving force for any electrode reaction is the overpotential $\eta = E - E_{eq}$, the deviation of the electrode potential $E$ from its equilibrium value $E_{eq}$ given by the Nernst equation. The rate at which charge crosses the electrode–electrolyte interface is described by the Butler-Volmer equation:

$$i = i_0\left[\exp\left(\frac{\alpha_a F \eta}{RT}\right) - \exp\left(-\frac{\alpha_c F \eta}{RT}\right)\right],$$

where $i_0$ is the exchange current density, the equal and opposite anodic and cathodic partial currents flowing at equilibrium, $\alpha_a$ and $\alpha_c$ are the anodic and cathodic transfer coefficients with $\alpha_a + \alpha_c = 1$ for a single-step elementary reaction, $R$ is the gas constant, and $T$ is absolute temperature. The exchange current density is not a material constant but a function of temperature, electrolyte composition, and surface structure:

$$i_0 = F k^0 a_{O}^{1-\alpha_c} a_{R}^{\alpha_a},$$

where $k^0$ is the standard rate constant for the redox couple and $a_O$, $a_R$ are the activities of the oxidized and reduced species at the surface. Measuring $i_0$ requires driving the electrode to small overpotentials ($|\eta| < 10$ mV) where the Butler-Volmer equation linearizes to

$$i \approx i_0 \frac{F\eta}{RT},$$

so the slope of an $i$-vs-$\eta$ plot in the linear regime directly gives $i_0 F / RT$, from which $i_0$ follows immediately. This linear regime measurement is called the polarization resistance, $R_p = RT/(F i_0)$, and it is the standard entry point for characterizing electrode kinetics.

The practical measurement of $i_0$ by electrochemical impedance spectroscopy (EIS) is more reliable than DC polarization curves because it separates the kinetic resistance $R_{ct} = R_p$ from the ohmic resistance $R_\Omega$ of the electrolyte and from mass-transport (diffusion) impedance, all of which appear as distinct features in the Nyquist plot.

**EIS Measurement Protocol for Electrode Kinetics:**

1. Prepare the working electrode in a standard three-electrode cell: the electrode under study as the working electrode (WE), a large-area platinum mesh as the counter electrode (CE), and a Ag/AgCl or standard hydrogen electrode (SHE) as the reference electrode (RE). Degas the electrolyte with argon for 30 minutes before and during the measurement to eliminate dissolved oxygen, which would add a parasitic reduction current.
2. Hold the WE at its open-circuit potential (OCP) for 15–30 minutes until the drift rate falls below 0.5 mV/min. Apply EIS only at or very near OCP; measuring away from equilibrium introduces nonlinearity that invalidates the small-signal analysis.
3. Set the AC perturbation amplitude to 10 mV rms. This is small enough to remain within the linear regime of the Butler-Volmer equation ($10\,\text{mV} \approx 0.4 \times k_BT/e$) while large enough to give a signal-to-noise ratio above 20 dB across the full frequency range.
4. Sweep frequency from 100 kHz down to 10 mHz using a logarithmic spacing of 10 points per decade. The high-frequency intercept of the Nyquist plot with the real axis gives $R_\Omega$. The semicircle at intermediate frequencies represents the charge-transfer resistance $R_{ct}$ in parallel with the double-layer capacitance $C_{dl}$; the diameter of this semicircle is $R_{ct}$. At the lowest frequencies, a 45° Warburg tail (or a vertical spike for a blocked diffusion geometry) represents diffusive mass transport.
5. Fit the spectrum to an equivalent circuit model using complex nonlinear least-squares (CNLS) regression. For a simple outer-sphere redox couple, a Randles circuit ($R_\Omega + (C_{dl} \| (R_{ct} + Z_W))$) is appropriate, where $Z_W = \sigma \omega^{-1/2}(1-j)$ is the Warburg impedance. Report the fit quality using the chi-squared residual; values above $10^{-3}$ indicate a poor model choice or surface contamination requiring cleaning.
6. Compute $i_0 = RT/(F R_{ct} A)$ where $A$ is the geometric electrode area, or the electrochemically active surface area (ECSA) determined from the double-layer capacitance $C_{dl}$ normalized to a reference value (typically $20–40\,\mu\text{F cm}^{-2}$ for smooth polycrystalline metal).

### Entropy Production in Charge Transport: Ohmic and Beyond

For purely resistive transport, the volumetric entropy production rate is simply

$$\dot{\sigma}_{Ohmic} = \frac{\vec{J} \cdot \vec{J}}{\sigma T} = \frac{|\vec{J}|^2}{\sigma T},$$

which is always positive and grows as the square of the current density. This is why power electronics operate at the lowest practical current densities and highest feasible voltages: the $I^2 R$ loss in interconnects, busbars, and cell internal resistance is the dominant parasitic dissipation in any grid-scale storage installation. For a battery pack with internal resistance $R_{int}$ cycling at current $I$, the round-trip coulombic efficiency is modified by the energy efficiency:

$$\eta_{energy} = \frac{\int (V_{OCV} - I R_{int})\, dq}{\int (V_{OCV} + I R_{int})\, dq} = \frac{V_{OCV} - I R_{int}}{V_{OCV} + I R_{int}},$$

where the integrals are taken over a full charge-discharge cycle at constant current. At the C-rate where $I R_{int} = 0.1 V_{OCV}$, the energy efficiency drops to $90/110 \approx 82\%$, with the full 18% dissipated as resistive heat. Measuring $R_{int}$ precisely requires a hybrid pulse power characterization (HPPC) test: apply a 10 s discharge pulse at a known current, record the instantaneous voltage drop $\Delta V$ at the onset of the pulse (which gives the pure ohmic $R_\Omega = \Delta V / I$), and then record the continuing slower voltage drop (which gives the charge-transfer and diffusion contributions). The separation of timescales — microseconds to milliseconds for $R_\Omega$, seconds to minutes for $R_{ct}$ and $R_{diff}$ — makes the pulse technique a powerful complement to EIS.

Beyond the ohmic regime, entropy is produced by concentration gradients in the electrolyte. When current flows through a binary electrolyte of concentration $c$, the electrochemical potential gradient drives ion migration, and in the steady state, a concentration gradient builds up according to the Nernst-Planck equation. The associated concentration overpotential is

$$\eta_{conc} = -\frac{RT}{z_i F}\ln\left(\frac{c_s}{c_b}\right),$$

where $c_s$ is the surface concentration of the electroactive species and $c_b$ is the bulk concentration. When $c_s$ approaches zero — the mass-transport-limited condition — $\eta_{conc}$ diverges logarithmically and the current density saturates at the limiting current density

$$i_L = \frac{z_i F D c_b}{\delta},$$

where $\delta$ is the diffusion layer thickness set by the hydrodynamics of the cell. In a rotating disk electrode (RDE) experiment, $\delta = 1.61 D^{1/3} \nu^{1/6} \omega^{-1/2}$ by the Levich equation, where $\nu$ is the kinematic viscosity of the electrolyte and $\omega$ is the rotation rate. Plotting $i_L$ versus $\omega^{1/2}$ gives a straight line (the Levich plot) whose slope yields $D$, the diffusion coefficient of the electroactive species, with no free parameters beyond the known electrolyte viscosity and concentration. This measurement is indispensable for characterizing mass-transport limitations in flow battery electrolytes and for determining the effective diffusivity of oxygen in polymer electrolyte membrane fuel cells, where $D$ depends strongly on the membrane water content and therefore on humidity management.

### Connecting Entropy Production to Observable Efficiency Losses

The practical synthesis of this analysis is the concept of overpotential decomposition in an operating electrochemical cell. The terminal voltage of a battery or fuel cell under load can be written as

$$V = E_{eq} - \eta_\Omega - \eta_{ct} - \eta_{conc},$$

where $\eta_\Omega = I R_\Omega$ is the ohmic loss, $\eta_{ct}$ is the charge-transfer overpotential from Butler-Volmer kinetics, and $\eta_{conc}$ is the concentration overpotential from mass transport. Each term corresponds to a distinct physical mechanism and a distinct entropy production rate:

$$T\dot{\sigma}_{total} = I(\eta_\Omega + \eta_{ct} + \eta_{conc}).$$

The total irreversibility is therefore exactly the total electrical power dissipated as heat. By measuring the three overpotential components separately — $\eta_\Omega$ from HPPC, $\eta_{ct}$ from EIS, and $\eta_{conc}$ from the Levich analysis — and summing them, you reconstruct the full loss budget of the device. Any discrepancy between this reconstructed sum and the directly measured voltage loss points to a loss mechanism you have not yet identified: a parasitic side reaction, an electronic short through the separator, or a contact resistance at the current collector interface. The decomposition is not an academic exercise; it is the diagnostic framework that tells you exactly where to focus materials engineering effort to push the device closer to its thermodynamic limit.
