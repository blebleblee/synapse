# Lesson 2: Transmission Line Theory

## 1. First-Principles Intuition & Invariants

Every circuit we have encountered thus far—resistors, capacitors, inductors connected by "wires"—has operated under a fundamental assumption: the voltage at one end of a conductor is instantaneously the same as the voltage at the other end. This assumption collapses catastrophically when signals travel distances comparable to their wavelength, or when rise times become short enough that electromagnetic wave propagation can no longer be ignored. A transmission line is not merely a wire; it is a distributed network of infinitesimal series inductances and shunt capacitances that fundamentally alters how energy propagates from source to load.

Consider a sinusoidal signal at 1 GHz, where the wavelength in free space is approximately 30 centimeters. A PCB trace 10 centimeters long carries this signal—suddenly, the physical length is one-third of a wavelength. At the signal source, current begins to flow; by the time this electromagnetic disturbance reaches the far end, the source voltage has already oscillated through multiple cycles. The front end and far end of the trace are no longer at the same potential. Voltage and current are now functions of both time *t* and position *x* along the line. This is the regime where transmission line theory becomes not an academic curiosity but an essential engineering discipline.

The invariant that anchors all transmission line analysis is conservation of energy and charge. Electromagnetic waves do not simply vanish; they propagate, reflect, and interfere. When a wave encounters a boundary—a discontinuity in characteristic impedance—part of the energy reflects backward while part transmits forward. The ratio of reflected to incident voltage, encoded in the reflection coefficient, determines whether signals constructively reinforce (maximum voltage standing wave) or destructively cancel (minimum voltage standing wave). This standing wave pattern, quantified by the voltage standing wave ratio (VSWR), is the signature of impedance mismatch and the starting point for all matching network design.

The Smith chart, invented by Philip Smith in 1939 and still ubiquitous in RF engineering laboratories today, is not a quaint analog tool but a profound geometric representation of the complex reflection coefficient in the *z*-plane. Every point on the Smith chart corresponds to a unique complex impedance or reflection coefficient; circles of constant resistance and constant reactance tile the entire plane. Navigation on the Smith chart—rotating clockwise as you move down a transmission line, drawing impedance transformations, cascading reflection coefficients—encodes the full physics of transmission line propagation in a single diagram. Engineers who master the Smith chart develop an almost tactile intuition for how circuits behave at microwave frequencies.

## 2. Core Architecture & Mechanics

### The Telegrapher's Equations: Distributed Element Foundation

A transmission line is modeled as a cascade of infinitesimal series and shunt elements. Consider a small segment of line of length $\Delta x$. The series impedance per unit length is $z$ (ohms per meter), which includes both resistance $r$ and inductive reactance $\omega L$:

$$z = r + j\omega L$$

The shunt admittance per unit length is $y$ (siemens per meter), which includes conductance $g$ and capacitive susceptance $\omega C$:

$$y = g + j\omega C$$

The voltage drop across the series impedance over distance $\Delta x$ is:

$$-\frac{\partial V}{\partial x} \Delta x = I(x,t) \cdot z \cdot \Delta x$$

In the limit as $\Delta x \to 0$:

$$-\frac{\partial V}{\partial x} = z \cdot I$$

Similarly, the current diverted through the shunt admittance is:

$$-\frac{\partial I}{\partial x} = y \cdot V$$

These two coupled first-order differential equations are the Telegrapher's equations. They are the foundation of all transmission line behavior. For a sinusoidal steady-state signal of the form $V(x,t) = \text{Re}[V(x) e^{j\omega t}]$, we can write the equations in phasor form:

$$-\frac{dV}{dx} = z \cdot I$$
$$-\frac{dI}{dx} = y \cdot V$$

Differentiating the first equation and substituting the second yields:

$$\frac{d^2V}{dx^2} = z \cdot \frac{dI}{dx} = z \cdot y \cdot V$$

This is a second-order ordinary differential equation with the general solution:

$$V(x) = V_+ e^{-\gamma x} + V_- e^{\gamma x}$$

where the propagation constant is $\gamma = \sqrt{zy}$. The propagation constant has real and imaginary parts: $\gamma = \alpha + j\beta$. The attenuation constant $\alpha$ describes how the wave amplitude decays with distance due to conductor loss and dielectric loss. The phase constant $\beta$ describes how the phase advances with distance; the wavelength on the transmission line is $\lambda = 2\pi / \beta$.

The characteristic impedance $Z_0$ is defined as the ratio of voltage to current for a wave traveling in the positive $x$ direction:

$$Z_0 = \sqrt{\frac{z}{y}} = \sqrt{\frac{r + j\omega L}{g + j\omega C}}$$

For a lossless transmission line (ideal case with $r = 0$ and $g = 0$):

$$Z_0 = \sqrt{\frac{L}{C}}$$

This is a purely real quantity. For a microstrip line on a PCB with substrate dielectric constant $\varepsilon_r \approx 4.5$, trace width $w$, and height above ground plane $h$, the characteristic impedance can be approximated as:

$$Z_0 \approx \frac{120}{\sqrt{\varepsilon_r}} \ln\left(\frac{8h}{w} + \frac{w}{4h}\right)$$

A typical 50-ohm microstrip on standard FR-4 (one-ounce copper, 0.063-inch substrate height) requires a trace width around 4 to 5 mils. This is not a coincidence; the 50-ohm standard emerged from coaxial cable impedances used in early RF systems and has remained dominant because it provides a reasonable compromise between bandwidth, loss, and manufacturing tolerance.

The current associated with the forward and backward voltage waves is:

$$I(x) = \frac{V_+}{Z_0} e^{-\gamma x} - \frac{V_-}{Z_0} e^{\gamma x}$$

The negative sign on the backward current term reflects the fact that reflected waves carry power in the negative $x$ direction.

### Boundary Conditions and the Reflection Coefficient

At the load end of the transmission line (position $x = \ell$), the voltage and current must satisfy Ohm's law with the load impedance $Z_L$:

$$V(\ell) = I(\ell) \cdot Z_L$$

Substituting the general solutions:

$$V_+ e^{-\gamma \ell} + V_- e^{\gamma \ell} = \left( \frac{V_+}{Z_0} e^{-\gamma \ell} - \frac{V_-}{Z_0} e^{\gamma \ell} \right) Z_L$$

The reflection coefficient at the load is defined as the ratio of reflected to incident voltage at that point:

$$\Gamma_L = \frac{V_-}{V_+} e^{2\gamma \ell}$$

But we typically work with the reflection coefficient at the load reference plane, where position is set to zero at the load. In that case:

$$\Gamma_L = \frac{Z_L - Z_0}{Z_L + Z_0}$$

This is the fundamental relationship in transmission line theory. If the load is perfectly matched ($Z_L = Z_0$), then $\Gamma_L = 0$—no reflection. If the load is an open circuit ($Z_L \to \infty$), then $\Gamma_L \to +1$—complete reflection with the same phase. If the load is a short circuit ($Z_L = 0$), then $\Gamma_L = -1$—complete reflection with 180-degree phase inversion. If the load is a pure short of arbitrary magnitude, the reflection coefficient lies on the unit circle in the complex plane.

### Voltage Standing Wave Ratio (VSWR)

The total voltage at any point on the transmission line is the superposition of incident and reflected waves:

$$V(x) = V_+ e^{-j\beta x} + V_- e^{j\beta x}$$

(For a lossless line, $\gamma = j\beta$, so $\alpha = 0$.) The magnitude of this total voltage oscillates between a maximum and minimum as we move along the line. The maximum occurs when the incident and reflected waves are in phase; the minimum occurs when they are 180 degrees out of phase.

The voltage standing wave ratio (VSWR) is defined as:

$$\text{VSWR} = \frac{V_{\max}}{V_{\min}} = \frac{1 + |\Gamma_L|}{1 - |\Gamma_L|}$$

A VSWR of 1.0 indicates a perfectly matched load with no reflections and no standing waves—every point on the line sees the same voltage magnitude. A VSWR greater than 1 indicates the presence of reflections. A VSWR of 3.0, for example, means the maximum voltage is three times the minimum voltage. High VSWR causes several problems in practice: it increases the voltage stress on components, it causes excessive loss in lossy transmission lines (the standing wave pattern ensures that some parts of the line carry much more current than others), and it degrades the bandwidth and group delay characteristics of the circuit.

### The Smith Chart: Geometric Navigation

The Smith chart is a conformal mapping of the complex reflection coefficient plane onto a circle of unit radius. The mapping is constructed such that circles of constant resistance and constant reactance in the $z$-plane (impedance) become circles and arcs on the Smith chart. This geometric property is extraordinarily powerful for circuit design.

The normalized impedance at any point on the transmission line is related to the reflection coefficient by:

$$z = \frac{1 + \Gamma}{1 - \Gamma}$$

Conversely:

$$\Gamma = \frac{z - 1}{z + 1}$$

The entire passive impedance space—all possible combinations of resistance and reactance—maps to the interior and boundary of the unit circle on the Smith chart. Purely resistive impedances lie on the real axis. The point $z = 1 + j0$ (matched impedance, 50 ohms in absolute units) sits at the center of the chart and corresponds to $\Gamma = 0$.

The arc labeled "R = 0.5" on the Smith chart represents all impedances of the form $0.5 + jx$, where $x$ ranges from $-\infty$ to $+\infty$. Similarly, the arc labeled "X = 1.0" represents all impedances of the form $r + j1.0$. These arcs tile the entire interior of the unit circle. By reading the intersection of two arcs, we immediately determine both the resistance and reactance at that point.

As we move along a transmission line from load toward source, the reflection coefficient rotates clockwise around the origin of the Smith chart. The distance traveled (in wavelengths) determines the rotation angle: each quarter wavelength (0.25λ) rotates the point by 90 degrees. This is one of the most profound insights in RF engineering. If you have a load at impedance $Z_L$ corresponding to a certain point on the Smith chart, and you move a quarter wavelength down the line toward the source, the impedance you observe looking toward the load has transformed to a new point exactly 90 degrees clockwise from the original. This quarter-wave impedance transformer is so useful that it is enshrined as a fundamental building block in RF circuits.

### Transmission Line Impedance Transformation

As we move a distance $d$ from the load toward the source, the input impedance (the impedance seen looking toward the load) transforms according to:

$$Z_{\text{in}}(d) = Z_0 \frac{Z_L + jZ_0 \tan(\beta d)}{Z_0 + jZ_L \tan(\beta d)}$$

In terms of the reflection coefficient, the reflection coefficient at distance $d$ from the load is:

$$\Gamma(d) = \Gamma_L e^{2j\beta d}$$

This exponential term represents the rotation on the Smith chart. The magnitude of the reflection coefficient remains constant (in a lossless line) as we move down the line; only the phase changes.

### Stub Matching: Practical Impedance Correction

One of the most powerful applications of transmission line theory is stub matching. A stub is simply a short length of transmission line connected either in series or in parallel with the main transmission line. By choosing the stub length and its termination (open or short circuit), we can introduce either inductive or capacitive reactance to cancel the reactance of the load, bringing the overall impedance into resonance with the source impedance.

For a shunt (parallel) open-circuit stub placed directly at the load, the stub presents an admittance that combines with the load admittance. If the load has admittance $y_L = g_L + jb_L$, we want to find a stub length such that the admittance it presents is $-jb_L$, thereby canceling the imaginary part. Once the susceptance is canceled, we have only conductance in parallel, and we can use a series quarter-wave transformer to match the remaining real part.

The characteristic admittance of a transmission line stub of length $\ell_s$ terminated in an open circuit is:

$$y_{\text{stub}} = -j \cot(\beta \ell_s) / Z_0$$

Setting this equal to $-jb_L$:

$$\cot(\beta \ell_s) = b_L Z_0$$

Solving for $\ell_s$ requires taking the inverse cotangent. In practice, the Smith chart makes this calculation graphical and intuitive. We plot the load admittance (remembering to use the admittance chart, which is the Smith chart rotated 180 degrees), move along a constant-conductance circle until we intersect the real axis (the point where susceptance is zero), and the arc length traced tells us the required stub length in wavelengths.

## 3. High-Performance Optimization & Failure Modes

### Time Domain Reflectometry (TDR) Analysis: Practical Debugging

In practical microwave systems, we often cannot directly measure the impedance of a line. Instead, we use Time Domain Reflectometry (TDR), which injects a step or impulse into the transmission line and observes the reflected signal. The reflection coefficient at any discontinuity can be inferred from the amplitude and timing of the reflected pulse.

A TDR instrument sends a fast rising edge (typically with rise time in the tens of picoseconds) down the transmission line toward the load. At any impedance discontinuity, a portion of the pulse energy reflects back toward the source. The TDR receiver captures the reflected waveform and displays it as a function of time. The distance to the discontinuity can be calculated from the round-trip propagation time and the known propagation velocity on the line:

$$\text{distance} = \frac{v_p \cdot t_{\text{round-trip}}}{2}$$

where $v_p = c / \sqrt{\varepsilon_r}$ is the propagation velocity. For a typical PCB with $\varepsilon_r \approx 4.5$, the velocity is roughly 2 × 10^8 m/s, or about 0.2 m/ns. A reflection arriving 5 nanoseconds after injection indicates a discontinuity 0.5 meters (50 centimeters) from the source.

The amplitude of the reflected pulse encodes the reflection coefficient. If the pulse height (relative to the incident step amplitude) is half the incident amplitude, then $\Gamma = 0.5$, indicating a partial mismatch. A full-height reflection (same amplitude as incident) indicates $\Gamma = 1$ (open circuit). An inverted reflection (opposite polarity) indicates $\Gamma = -1$ (short circuit).

In practice, TDR is invaluable for debugging impedance problems on high-speed PCBs. A well-designed 50-ohm trace should show a flat TDR waveform with minimal reflections. Any bump or dip in the TDR trace indicates a localized impedance discontinuity. Common culprits include via stubs (unused via pads extending into the transmission line), abrupt width changes at connectors, and impedance mismatches at layer transitions.

### Stub Discontinuities and Via Effects

A subtle but pervasive source of impedance mismatch in modern PCBs is the via stub. When routing a signal from one layer to another on a PCB, the designer must pass through a via. However, the via often extends beyond the target layer, creating a short stub that branches off the main transmission line. This stub presents a parallel impedance that varies with frequency. At certain frequencies, the stub length is such that its admittance presents a short circuit to the main line, creating a severe reflection.

A via of diameter 8 mils, height 0.063 inches (standard board thickness), and via pad diameter 14 mils has an inductance of roughly 0.5 nanohenries. At 1 GHz, this inductance presents a reactance of $X_L = \omega L = 2\pi \times 10^9 \times 0.5 \times 10^{-9} \approx 3$ ohms—a relatively small perturbation. However, the stub length determines the resonant frequency. For a via stub of 0.5 inches (12.7 mm) extending beyond the connection point, the electrical length is approximately 0.2λ at 1 GHz. This creates a parallel resonance where the stub presents high impedance at certain frequencies and low impedance at others, causing frequency-dependent reflections.

The solution is to remove the stub entirely by back-drilling (plating through the via hole and then drilling out the unused portion) or by using blind and buried vias that do not extend the full board thickness. Back-drilling adds cost but is essential for high-speed designs above a few gigahertz where stub-induced reflections become unacceptable.

### Dispersion and Group Delay

In real transmission lines, different frequency components travel at different velocities. This phenomenon is called dispersion. For a microstrip, the dispersion arises from the frequency dependence of the dielectric constant and the distribution of fields between the dielectric and the surrounding air. At DC, the effective dielectric constant of a microstrip is lower than at high frequencies, meaning low-frequency components travel faster than high-frequency components.

The group delay $\tau_g$ is defined as the derivative of phase with respect to angular frequency:

$$\tau_g = -\frac{d\phi}{d\omega} = \frac{d\beta}{d\omega}$$

where $\beta$ is the phase constant. In a lossless, non-dispersive line, the group delay is constant. But in real lines, group delay varies with frequency. For a Gaussian pulse propagating down a dispersive line, the different frequency components arrive at slightly different times, causing the pulse to broaden and distort. This is particularly problematic in high-speed digital systems where pulse integrity is critical.

The Kramers-Kronig relations establish that any dispersion (frequency-dependent phase velocity) must be accompanied by loss (attenuation). A perfectly non-dispersive line cannot exist; the presence of any frequency dependence in the propagation velocity necessarily implies that the line is lossy.

### Loss Mechanisms: Conductor and Dielectric

Conductor loss arises from the finite conductivity of the trace metal (copper) and the ground plane. As the signal current flows, it dissipates energy according to $P = I^2 R$. For a microstrip line, the resistance is dominated by the series resistance of the trace itself. At DC, this is straightforward: $R = \rho \ell / A$, where $\rho$ is the resistivity of copper (approximately 1.7 × 10^-8 ohm-meters), $\ell$ is the length, and $A$ is the cross-sectional area. But at high frequencies, the current does not distribute uniformly across the cross-section; instead, it concentrates near the surface in a layer of depth called the skin depth:

$$\delta = \sqrt{\frac{2}{\omega \mu \sigma}}$$

where $\mu$ is the permeability (approximately $\mu_0$ for copper), and $\sigma$ is the conductivity. At 1 GHz, the skin depth in copper is approximately 2 micrometers. The current flows almost entirely within this 2-micrometer layer near the surface, leaving most of the bulk conductor unused. As frequency increases and skin depth decreases, the effective resistance increases as $\sqrt{f}$.

Dielectric loss arises from the lossy nature of the substrate material. The dielectric constant of real materials has both real and imaginary parts: $\varepsilon = \varepsilon' - j\varepsilon''$. The imaginary part represents the loss. At room temperature, FR-4 has a loss tangent (the ratio of imaginary to real permittivity) around 0.02 at 1 GHz. This causes the electromagnetic energy stored in the dielectric to be partially dissipated as heat. The attenuation constant due to dielectric loss is approximately:

$$\alpha_{\text{diel}} \approx \frac{\omega \sqrt{\varepsilon_r}}{2Z_0 c} \tan \delta$$

where $\tan \delta$ is the loss tangent. For a 50-ohm microstrip on standard FR-4 at 1 GHz, dielectric loss typically contributes about 0.1 dB per inch. For a 10-inch trace, this accumulates to roughly 1 dB of insertion loss, a noticeable degradation.

For modern high-frequency designs, engineers often specify materials with lower loss tangent. PTFE-based laminates (Teflon) have loss tangents around 0.002 at 1 GHz, an order of magnitude better than FR-4. Rogers RO3000 series materials offer a middle ground with loss tangents around 0.003 and dimensional stability suitable for complex multilayer designs.

### Return Loss and Mismatch Loss

Return loss is defined as the negative decibel ratio of reflected to incident power:

$$\text{Return Loss} = -10 \log_{10}(|\Gamma|^2) = 20 \log_{10}(1/|\Gamma|)$$

A perfectly matched load (VSWR = 1.0, $\Gamma = 0$) has infinite return loss. A return loss of 20 dB corresponds to $|\Gamma| = 0.1$, meaning 1% of the incident power is reflected. A return loss of 10 dB corresponds to $|\Gamma| \approx 0.316$, or about 10% reflection.

The mismatch loss is the reduction in available power to the load due to reflections:

$$\text{Mismatch Loss} = -10 \log_{10}(1 - |\Gamma|^2)$$

For $|\Gamma| = 0.1$, the mismatch loss is only 0.04 dB—negligible. But for $|\Gamma| = 0.5$, the mismatch loss reaches 0.51 dB, and for $|\Gamma| = 0.8$, it reaches 2.92 dB. In power-limited applications (such as wireless power transfer or long-distance satellite links), even a few dB of mismatch loss can be catastrophic to link budget.

### Matching Network Design Workflow

The systematic design of a matching network on the Smith chart follows a proven workflow. First, normalize the load impedance by dividing by the desired characteristic impedance (usually 50 ohms). Plot this normalized impedance on the Smith chart. If the impedance has significant reactance, the load will not be efficiently matched; we must move along the Smith chart to find a point with lower reactance.

If the load is a capacitive impedance (upper half of the Smith chart), we can add a series inductance or move down the transmission line (clockwise on the Smith chart) to reach a point with lower reactance. If we have a quarter-wave section of transmission line at a different characteristic impedance, we can use it as a quarter-wave transformer. A quarter-wave transformer with characteristic impedance $Z_0'$ transforms a load impedance $Z_L$ to an input impedance $Z_{\text{in}} = Z_0'^2 / Z_L$.

Conversely, we can use a shunt stub to cancel reactance. Plot the load admittance (rotate the Smith chart 180 degrees or use the admittance chart directly). Move along a constant-conductance circle until we hit the real axis. The distance traveled in wavelengths is the required stub length. Then add a series inductance or capacitance (or a length of transmission line) to cancel any remaining reactance.

In practice, matching network design is an iterative process. We might start with a series inductor, realize it causes unacceptable bandwidth reduction, and switch to a shunt-stub approach. We might use a double-stub matching network, which uses two stubs (usually at fixed separation) to match a wide range of loads without the bandwidth degradation of single-element networks. Each design choice presents tradeoffs between bandwidth, component count, ease of tuning, and thermal performance.

### Quality Factor and Bandwidth

The quality factor Q of a matching network determines its bandwidth. A narrow-band (high-Q) network achieves a perfect match over a limited frequency range, typically a few percent of the center frequency. A broad-band (low-Q) network achieves an acceptable match over a wider frequency range, but the match is never perfect.

For a series LC matching network, the quality factor is:

$$Q = \frac{\omega_0 L}{R} = \frac{1}{\omega_0 R C}$$

where $\omega_0$ is the resonant frequency. The fractional bandwidth (the bandwidth as a fraction of the center frequency) is approximately:

$$\text{BW} \approx \frac{f_0}{Q}$$

If we require a 5% fractional bandwidth and have a load resistance of 25 ohms (a mismatch relative to 50 ohms), then the required Q is:

$$Q \approx \frac{1}{0.05} = 20$$

For a center frequency of 1 GHz:

$$L = \frac{QR}{\omega_0} = \frac{20 \times 25}{2\pi \times 10^9} \approx 79.6 \text{ nanohenries}$$

This inductance is large enough that parasitic inductances from component leads become significant, and precise tuning may be required. If we need 10% bandwidth (lower Q = 10), the inductance drops to 40 nanohenries, but the match is less precise.

### Measurement and Validation: Network Analyzer Workflow

Mo
