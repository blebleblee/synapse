# Lesson 4: Impedance Matching Networks

## 1. First-Principles Intuition & Invariants

The propagation of electromagnetic energy through a microwave system is fundamentally a problem of impedance continuity. When a traveling wave encounters a discontinuity—a change in characteristic impedance—part of the wave reflects backward, dissipating power and degrading system performance. This reflection arises from the same physical principle that causes light to refract at an air-glass interface: the wave "wants" to continue in the original medium, but the boundary conditions imposed by Maxwell's equations force a portion of the energy back. In microwave circuits, this problem becomes acute because wavelengths are short (centimeters to millimeters), making even small geometric discontinuities significant reflective sources.

The goal of impedance matching is to create a continuous path for electromagnetic energy flow by progressively transforming the impedance at one port to match the impedance at another. This is not merely an optimization—it is a necessity for efficient power transfer, noise performance, and system stability. Consider a 50-ohm coaxial transmission line connected directly to a 75-ohm antenna. The impedance step creates a reflection coefficient of magnitude $\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0} = \frac{75 - 50}{75 + 50} = 0.2$. This means 4% of incident power reflects, and only 96% reaches the load. In high-power amplifier design, filter networks, and antenna systems, this loss translates to reduced efficiency, increased heat dissipation, and potential instability.

The reflection coefficient is the cornerstone quantity in matching theory. For a load impedance $Z_L$ terminating a characteristic impedance $Z_0$, we define:

$$\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0}$$

The magnitude $|\Gamma|$ ranges from 0 (perfect match) to 1 (open or short circuit). The return loss in decibels is $\text{RL} = -20 \log_{10} |\Gamma|$, which quantifies how much power reflects. A return loss of 20 dB corresponds to $|\Gamma| = 0.1$, meaning 1% of power reflects and 99% transmits—a practical target for many systems.

Impedance matching networks exist in two fundamental classes: lumped-element networks built from discrete inductors and capacitors, and distributed networks constructed from transmission-line segments. The choice between these approaches hinges on frequency, available component Q factors, and the required bandwidth. At low microwave frequencies (1–2 GHz), lumped components are practical because their physical size remains manageable and high-Q inductors and capacitors are readily available. As frequency increases beyond 10 GHz, the wavelength shrinks sufficiently that lumped components become parasitic and lossy; distributed networks using microstrip or waveguide segments become dominant.

The fundamental invariant governing all matching networks is energy conservation coupled with causality. Any matching network is, in its simplest form, a two-port network characterized by S-parameters (scattering parameters). For a lossless, reciprocal matching network, the S-parameters obey the unitary condition: $S^\dagger S = I$, ensuring that energy is conserved. In practical implementations, resistive losses in conductors and dielectrics introduce dissipation, violating perfect unitarity. Understanding this trade-off—between matching bandwidth and loss—forms the intellectual foundation for broadband matching design.

A critical theorem limiting all matching networks is the Bode-Fano limit, which imposes an absolute bound on how well a network can match a complex load over a given bandwidth. Specifically, for a resistive load $R$ in parallel with a reactance, the integral of the logarithm of reflection magnitude over frequency is bounded:

$$\int_0^\infty \ln |\Gamma(f)| \, df \leq \frac{\pi}{2} \ln \left| \frac{Z_0}{R_\infty} \right|$$

This inequality states that achieving perfect matching (zero reflection) at one frequency necessarily requires increased reflection at other frequencies. Attempting to squeeze matching bandwidth always exacts a price: resonance sharpens, or matching degrades at the band edges. This is not a limitation of particular network topologies but a fundamental law rooted in the pole-zero structure of transfer functions and causality. Accepting this constraint, practitioners design networks that optimally trade off matching quality, bandwidth, and complexity.

## 2. Core Architecture & Mechanics

### Single-Element and Two-Element L-Networks

The conceptually simplest matching network consists of a single reactive element (inductor or capacitor) placed between source and load. For a 50-ohm source feeding a purely resistive load $R_L$, a single series or shunt element shifts the impedance locus on the Smith chart, tracing a circle of constant resistance (for series elements) or constant conductance (for shunt elements). However, a single element can achieve perfect matching only when the load is purely resistive and lies within a certain range relative to the source impedance.

The two-element L-network extends this capability by cascading two reactive elements—typically an inductor and capacitor—allowing independent control of both resistance and reactance. Consider a 50-ohm source feeding a 25-ohm load with a series reactance of +j12.5 ohms, giving $Z_L = 25 + j12.5$ ohms. A direct series capacitor cannot simultaneously cancel the +j12.5 reactance and step down the 25-ohm resistance to 50 ohms. Instead, the L-network uses two elements: the first element is chosen to shift the impedance to a real value, and the second element cancels the resulting reactance.

The design procedure for an L-network hinges on the Smith chart. Starting at the load impedance (normalized to the characteristic impedance 50 ohms), we normalize: $z_L = (25 + j12.5)/50 = 0.5 + j0.25$. Moving along a constant-resistance circle (using a shunt element) or constant-reactance arc (using a series element), we seek to reach the center of the chart (perfect match at 1.0 + j0.0). The reactance of the first element and the second element are read directly from the chart arcs.

In practice, the L-network has two configurations: "L-low" (series L, shunt C to ground, preferred when the load resistance is below the source) and "L-high" (series C, shunt L, preferred when load resistance exceeds source). Each configuration achieves matching over a narrow bandwidth—typically a few percent—because the network is frequency-dependent. At DC and extremely low frequencies, capacitors block; at high frequencies, inductors block. The real and imaginary impedances of $L$ and $C$ scale with frequency, so matching achieved at one frequency degrades rapidly away from center frequency.

### Single-Stub Tuning on Transmission Lines

When matching an antenna or load on a transmission line, the single-stub tuner provides a distributed-element solution. A stub is an open- or short-circuited transmission-line segment placed either in series or in shunt with the main transmission line. The stub's input impedance varies periodically with frequency due to standing-wave effects.

Consider a 50-ohm transmission line terminated in a load with reflection coefficient $\Gamma_L$. At the load, the impedance is $Z_L$. Moving away from the load toward the source by an electrical distance $d$, the impedance transforms according to the transmission-line equation:

$$Z(d) = Z_0 \frac{Z_L + jZ_0 \tan(\beta d)}{Z_0 + jZ_L \tan(\beta d)}$$

where $\beta = 2\pi/\lambda$ is the phase constant and $\lambda$ is the wavelength. We seek a distance $d_1$ where the impedance becomes purely real—that is, where the imaginary part is zero. At this point, the susceptance (imaginary admittance) is zero, and placing a shunt stub whose characteristic admittance exactly cancels the susceptance of the main line yields a perfectly matched termination.

The design procedure is straightforward using the Smith chart. Starting at the normalized load impedance, we rotate clockwise along the chart (moving toward the source) until we intersect the real-axis resistance circle. This rotation represents traveling along the transmission line; the arc length in wavelengths tells us the stub position. Then, we read the susceptance value from the chart at that point and choose a stub length that produces an equal and opposite susceptance.

The single stub's electrical length is also derived from the transmission-line equation. An open-circuited stub has input impedance $Z_{\text{stub}} = -jZ_0 \cot(\beta \ell)$, where $\ell$ is the stub length. Setting the imaginary part of the total admittance to zero yields the required stub length $\ell$. Because the cotangent function has period $\pi$ in its argument, every wavelength of stub length introduces periodicity. This periodicity means that multiple stub lengths can achieve the same matching condition, offering flexibility in layout.

Single-stub tuning shines in narrowband applications where matching is required only at a specific frequency or over a tight bandwidth around it. Its simplicity—one open or short circuit placed at a calculated distance—makes it attractive for antenna tuning, filter designs, and amplifier input/output networks. However, its bandwidth limitation is severe. Moving even 10% away from design frequency typically causes the reflected power to increase significantly, because both the main transmission line and the stub are frequency-dependent.

### Double-Stub Tuning for Broadband Matching

The single stub addresses one major limitation of the L-network: it operates on distributed elements, making it practical at high microwave frequencies where lumped components become unwieldy. However, the single stub still suffers from poor bandwidth. The double-stub configuration mitigates this by adding a second stub, providing an additional degree of freedom.

In double-stub tuning, two stubs are placed at fixed intervals (typically $\lambda/8$ or $\lambda/4$ apart) along the transmission line. Each stub is independently tunable. The design procedure differs slightly from single-stub because the stub positions are fixed; only their lengths vary. We choose the spacing between stubs such that the locus of achievable impedances (by varying both stubs) covers a wide region of the Smith chart. With two stubs, it becomes possible to match a broader range of loads and, more importantly, to achieve acceptable matching over a wider frequency range.

The design process uses the Smith chart with a graphical construction. Starting at the normalized load impedance, we rotate toward the source by the distance to the first stub. At this point, we can adjust the first stub's length to shift the impedance to lie on a specific circle (often chosen to be the real-axis resistance circle or a circle tangent to the center). Then, we advance by the distance to the second stub and adjust its length to bring the impedance to the center of the chart (perfect match). Because two independent stubs provide two tuning parameters, the system becomes over-constrained—we can simultaneously satisfy real and imaginary parts of the impedance.

Practically, double-stub tuning is implemented by fabricating two stub ports spaced $\lambda/8$ to $\lambda/4$ apart and tuning each stub by sliding a shorting plate along its length (for open stubs) or by using a variable capacitor. Commercial tuning systems use this principle extensively in waveguide and microstrip implementations. The bandwidth improvement over single-stub is modest—typically a factor of 2 to 3—because the frequency dependence of the main transmission line and both stubs still limits the frequency range.

### Quarter-Wave Transformers

A quarter-wave transformer is a distributed matching element of immense practical importance in microwave systems. It exploits the property that a transmission-line segment of length exactly $\lambda/4$ (at the design frequency) produces an impedance inversion.

For a transmission line of characteristic impedance $Z_{\text{TL}}$ and length $\ell = \lambda/4$, the input impedance is:

$$Z_{\text{in}} = Z_{\text{TL}}^2 / Z_L$$

If we set $Z_{\text{TL}} = \sqrt{Z_0 Z_L}$, where $Z_0$ is the source impedance and $Z_L$ is the load impedance, then:

$$Z_{\text{in}} = \frac{Z_0 Z_L}{Z_L} = Z_0$$

Perfect matching is achieved. The beauty of this approach is its simplicity: a single quarter-wave section of controlled impedance bridges two arbitrary impedances. At the design frequency (where the physical length equals $\lambda/4$), matching is perfect. However, the matching degrades as frequency moves away from center because the physical length no longer equals $\lambda/4$; instead, it deviates as $(f_0 - f)/f_0$, causing impedance mismatch.

The fractional bandwidth $\Delta f / f_0$ over which a quarter-wave transformer maintains acceptable matching (say, return loss better than 15 dB) is approximately $\Delta f / f_0 \approx 0.5 / Q$, where $Q$ is the quality factor set by the impedance ratio $(Z_{\text{max}} / Z_{\text{min}})^{0.5}$. For a transformer matching 50 ohms to 100 ohms, $Q = (100/50)^{0.5} = 1.41$, and the bandwidth is roughly 35%. For a more extreme impedance ratio, say 10:1, $Q = 3.16$ and bandwidth shrinks to 16%. This frequency dependence underscores a cardinal rule: quarter-wave transformers are best suited to broadband matching when impedance ratios are modest (less than 3:1) or when operating over narrow fractional bandwidths.

In practice, the quarter-wave transformer is implemented in microstrip or waveguide by carefully controlling the transmission-line impedance. In microstrip, the characteristic impedance is set by the width-to-height ratio $W/H$ of the conductor. A narrower line (higher impedance) or wider line (lower impedance) is fabricated with the appropriate dimensions. The transformer section occupies physical length $\ell = \lambda/4$ at the design frequency. If the design frequency is 2 GHz and the microstrip effective dielectric constant is 4 (typical for FR-4 PCB), the wavelength in the substrate is $\lambda = c / (f \sqrt{\epsilon_r}) = 3 \times 10^8 / (2 \times 10^9 \times 2) = 7.5$ cm, so the quarter-wave transformer is 1.875 cm long.

### Multiple Quarter-Wave Sections and Binomial Matching

A single quarter-wave transformer cannot achieve both perfect matching and wide bandwidth simultaneously, by the Bode-Fano limit. However, cascading multiple quarter-wave sections—each with a different characteristic impedance—allows a smoother impedance transition, broadening the bandwidth.

The binomial matching network, also called a Chebyshev or maximally flat network, uses $N$ cascaded quarter-wave sections with characteristic impedances chosen such that the reflection coefficient's magnitude response is Chebyshev-optimal over the design bandwidth. For $N = 2$, the characteristic impedances are $Z_1 = (Z_0 Z_L)^{1/2}$ and $Z_2 = Z_0 Z_1 / Z_L$—the geometric mean and a derived value ensuring smooth transition. For $N = 3$, the impedances involve roots and more complex relationships.

The design procedure uses tables or software tools (such as Mathjax or MATLAB) to compute the section impedances given the impedance ratio $Z_L / Z_0$ and the number of sections $N$. With $N = 2$ and an impedance ratio of 2:1 (matching 50 ohms to 100 ohms), the bandwidth for a -20 dB return loss improves from ~35% (single quarter-wave) to ~50%. As $N$ increases, bandwidth expands further, asymptotically approaching the Bode-Fano limit.

The physical realization requires fabricating multiple microstrip sections (or waveguide sections) with decreasing or increasing widths to achieve the impedance sequence. Each section must be precisely $\lambda/4$ long at the center design frequency. Off-center frequencies introduce phase errors; a section that is nominally $\lambda/4$ becomes $\lambda/4 + \Delta\phi$ at higher frequencies and $\lambda/4 - \Delta\phi$ at lower frequencies. These phase errors accumulate across multiple sections, ultimately setting the bandwidth limit.

## 3. High-Performance Optimization & Failure Modes

### Lumped-Element Matching: Design and Practical Constraints

Lumped-element matching networks—built from discrete inductors and capacitors—are essential at frequencies below 5 GHz where component quality factors are high and sizes are manageable. The design flow begins with the load impedance (measured or specified), normalization to the characteristic impedance, and identification of the nearest matching configuration.

For a complex load $Z_L = R_L + jX_L$, the first step is to normalize: $z_L = Z_L / Z_0$. On the Smith chart, this point defines the starting position. The matching network must transform this point to the center (1.0 + j0.0, perfect match). Two approaches dominate: the analytical method using impedance transformation equations, and the graphical Smith-chart method.

The analytical approach for an L-network proceeds as follows. We decide on the network topology: series-inductor followed by shunt capacitor (L-high) or series-capacitor followed by shunt inductor (L-low). For L-high, the series inductor is chosen to cancel the imaginary part of the load, transitioning the impedance to real. Then the shunt capacitor is calculated to step the real impedance to 50 ohms.

Specifically, if we place a series inductor $X_L = \omega L$, the impedance becomes $Z' = R_L + j(X_L + X_L) = R_L + j(X_L + \omega L)$. Choosing $\omega L = -X_L$ cancels the reactance, leaving $Z' = R_L$. Now, placing a shunt capacitor $B_C = \omega C$ in parallel shifts the admittance. The parallel admittance is $Y = 1/R_L + j\omega C$. For this to equal $1/Z_0$, we need $1/R_L = 1/Z_0$ and $\omega C = 0$, which is impossible unless $R_L = Z_0$. Instead, the shunt capacitor is tuned to cancel a small reactance introduced during the first step, or the network topology is adjusted.

In reality, the practical procedure recognizes that a pure series inductance cannot directly achieve matching for arbitrary loads. Instead, the two-element L-network exploits the fact that series and shunt elements can independently control the real and imaginary parts in combination. The design involves solving two equations:

For the impedance $Z_L = R_L + jX_L$ to be transformed to $Z_0$ using a series element $X_S$ and shunt element $X_P$:

$$\frac{1}{Z_0} = \frac{1}{R_L + j(X_L + X_S)} + \frac{1}{jX_P}$$

This is a complex equation with two unknowns ($X_S$ and $X_P$), yielding two real equations (real and imaginary parts). Solving these yields the required reactances.

Practically, circuit simulation software (such as ADS, HFSS, or free tools like Qucs or ngspice) automates this calculation. The designer specifies the load impedance and desired characteristic impedance, and the tool recommends component values. However, understanding the underlying mathematics is crucial for troubleshooting mismatches and optimizing for component availability.

Component quality factor $Q = \omega L / R$ (for inductors) or $Q = 1/(\omega R C)$ (for capacitors) dramatically affects matching network performance. A high-Q inductor (large $L$ relative to DC resistance $R$) allows precise impedance control with minimal loss. Conversely, a low-Q component dissipates significant power in its resistance, degrading matching and adding noise. At microwave frequencies (5–20 GHz), discrete inductors are typically thin-film chip components with $Q$ values ranging from 30 to 80, while capacitors are ceramic with $Q$ values exceeding 100. As frequency increases, $Q$ degrades because resistance becomes frequency-dependent (skin effect) and dielectric loss in capacitors increases.

The tolerance of component values also affects matching. A 5% tolerance on a capacitor nominally sized at 10 pF represents ±0.5 pF, which at 10 GHz (where $C = 10$ pF implies impedance $X_C = 1/(2\pi \times 10^{10} \times 10 \times 10^{-12}) = 1.59$ ohms) creates a ±0.08 ohm impedance variation. For a 50-ohm system, this is small; but in high-impedance matching networks or those operating near resonance, such tolerances can degrade matching significantly. Production yield often requires additional tuning—laser trimming of inductors or tuning capacitors—to achieve the specified performance across a batch of units.

Parasitic effects lurk in all lumped components. The inductor has series resistance from the copper windings and fringing capacitance from the coil turns. The capacitor has parasitic series inductance from its leads and connections. At high frequencies, these parasitic elements dominate the component behavior, rendering the ideal model invalid. A 10 pF chip capacitor might have a series lead inductance of 0.5 nH, equivalent to 31.4 milliohms at 10 GHz—no longer negligible. Accurate component modeling requires S-parameter measurements or SPICE models that capture these parasitics, available from manufacturers for precision RF components.

### Broadband Matching and the Bode-Fano Trade-off

The Bode-Fano limit is not merely a theoretical curiosity; it governs the achievable bandwidth of any matching network. This limit emerges from the causality constraint on passive networks: the network must be realizable with passive elements (resistors, inductors, capacitors, transmission lines), implying that the transfer function must have a pole in the right half-plane for certain configurations.

For a resistive load $R$ terminating a 50-ohm line, the minimum reflection coefficient over all possible lossless, passive, reciprocal matching networks satisfies:

$$\int_0^\infty \ln |\Gamma_{\min}(f)| \, d\omega \geq -\pi \ln \left( \frac{2R}{Z_0} \right)$$

where $\omega = 2\pi f$. This integral sums the logarithm of reflection magnitude across all frequencies. A more intuitive form states that the product of $(1 - |\Gamma|)$ over all frequencies is bounded. Trying to achieve near-zero reflection (small $|\Gamma|$) at one frequency necessarily requires increased reflection at other frequencies to satisfy the integral constraint. The integral is a "hard constraint"—no passive network can violate it.

The practical consequence is that broadband matching networks require trade-offs. For a given load impedance and desired bandwidth, the designer must choose: (1) accept higher return loss at the band edges to achieve excellent matching at center frequency (Chebyshev response), (2) accept slightly worse matching throughout the band to maintain more uniform response (Butterworth response), or (3) use active matching (amplifiers or phase shifters) to dynamically adjust impedance—but at the cost of added complexity, power consumption, and noise.

Chebyshev networks (also called equiripple networks) distribute the reflection coefficient uniformly across the bandwidth, ensuring that no single frequency experiences excessive mismatch. The reflection coefficient ripples between a maximum value $|\Gamma_{\max}|$ at band edges and minima deeper in the band. A typical specification might demand that $|\Gamma| < 0.1$ across a 2:1 frequency octave (e.g., 1–2 GHz). Meeting this with Chebyshev matching requires approximately $N = 3$ to 4 sections, depending on the impedance ratio.

Butterworth networks trade uniform passband matching for smooth roll-off outside the band. The magnitude response exhibits no ripple; instead, the reflection coefficient monotonically increases as frequency moves away from center. This topology is preferred when simplicity and predictability matter more than filling the full bandwidth with excellent matching.

Practical optimization involves numerical synthesis. Given an impedance ratio, desired bandwidth, and target return loss, software tools (such as Renormalization-Group Flow tables, circuit simulators with optimization routines, or dedicated RF synthesis packages) compute the required network topology and component values. The synthesis typically produces several candidate topologies; the designer selects based on complexity, tunability, and cost.

### Tuning, Measurement, and Characterization

In real systems, matching networks are rarely perfectly tuned on first try. Manufacturing tolerances, unknown or variable load impedances, and frequency shifts due to temperature or component aging necessitate tuning.

Impedance measurement is the foundation of tuning. The reflection coefficient $\Gamma$ is measured directly using a network analyzer (such as an HP 8753ES or modern portable units like the Rohde & Schwarz ZVL series).

The network analyzer sweeps frequency, injects a calibrated signal into the device under test (DUT), and measures both forward and reflected waves, yielding $S_{11}$ (reflection coefficient looking into the matching network and load). Modern analyzers resolve magnitude to ±0.01 dB and phase to ±0.1°, sufficient for most matching applications. Calibration is critical: short-open-load-thru (SOLT) or thru-reflect-line (TRL) standards remove systematic errors introduced by cables, connectors, and test fixtures. After calibration, the reference plane is mathematically shifted to the DUT input, and the measured $\Gamma$ reveals the true impedance mismatch. Tuning proceeds iteratively: adjustable matching elements (variable capacitors, tuning stubs, or sliding short circuits) are varied while monitoring $|\Gamma|$ or VSWR in real time. For narrowband systems, the goal is to null $|\Gamma|$ at the operating frequency; for broadband networks, the entire passband is swept, and compromises are made to flatten the response across the band. After tuning, the network's temperature stability and power handling are verified under operational conditions, ensuring that the match remains robust across environmental and drive-level variations.

Characterization completes the design cycle. Beyond $S_{11}$, insertion loss $S_{21}$ is measured to quantify dissipation in the matching network itself—lossy components (resistive traces, magnetic cores) degrade efficiency, and high-Q reactive elements minimize this penalty. Power sweeps confirm linearity: passive matching networks should exhibit no compression or harmonic generation, but solder joints, ferrites, or varactors may introduce nonlinearities at high power. Thermal cycling and vibration tests validate mechanical stability, particularly for MMIC or waveguide implementations where thermal expansion or mechanical stress can detune the match. Finally, the measured data are compared against specifications, and deviations are root-caused through sensitivity analysis—component tolerances, parasitic reactances, or unforeseen coupling paths are identified and corrected. This closed-loop process—design, measure, tune, characterize—ensures that the matching network delivers its promised performance across all operating conditions, completing the transformation from theoretical synthesis to deployable hardware.

## Summary & Verification Matrix

| **Invariant/Criterion** | **Governing Equation/Relation** | **Physical Mechanism** | **Diagnostic Test** |
|-------------------------|----------------------------------|------------------------|---------------------|
| **Reflection Coefficient Magnitude** | $\|\Gamma\| = \left\|\frac{Z_L - Z_0}{Z_L + Z_0}\right\| \leq \Gamma_{\text{max}}$ (e.g., 0.1 for RL > 20 dB) | Impedance mismatch creates standing waves; $\|\Gamma\|$ quantifies reflected power fraction | Measure $S_{11}$ with calibrated VNA; verify $\|\Gamma\| < 0.1$ across band |
| **VSWR and Return Loss** | $\text{VSWR} = \frac{1 + \|\Gamma\|}{1 - \|\Gamma\|}$, $\text{RL} = -20\log_{10}\|\Gamma\|$ dB | VSWR describes voltage standing wave amplitude ratio; RL expresses mismatch loss logarithmically | VSWR meter or compute from $S_{11}$; confirm RL > 20 dB in passband |
| **Quality Factor and Bandwidth** | $Q = \frac{f_0}{\Delta f}$; fractional BW $\approx \frac{4}{\pi N Q}$ for $N$-section networks | High $Q$ implies narrow bandwidth; multi-section networks extend BW by cascading transformations | Sweep $S_{11}$ vs. frequency; measure 3 dB or $\|\Gamma\| = 0.1$ bandwidth |
| **Insertion Loss** | $\text{IL} = -20\log_{10}\|S_{21}\|$ dB; ideally IL $\approx 0$ dB for lossless matching | Resistive losses in components, substrate, or magnetic materials dissipate power | Measure $S_{21}$ through network; verify IL < 0.5 dB for low-loss designs |
| **Power Handling and Linearity** | $P_{\text{max}}$ set by voltage breakdown, current density, thermal dissipation | High RF voltage stresses dielectrics; high current heats conductors; nonlinearities generate harmonics | Power sweep $S_{11}$, $S_{21}$; confirm no compression or harmonic distortion to $P_{\text{rated}}$ |
| **Temperature and Mechanical Stability** | $\Delta Z = Z_0 \left(\alpha_{\text{therm}} \Delta T + \alpha_{\text{mech}} \Delta x\right)$ | Thermal expansion shifts electrical length; vibration detunes lumped elements | Cycle temperature −40°C to +85°C; vibration test per MIL-STD-810; verify $\|\Gamma\|$ drift < 0.05 |
