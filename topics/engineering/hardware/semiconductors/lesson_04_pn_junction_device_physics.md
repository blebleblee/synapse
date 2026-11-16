# Lesson 4: PN Junctions, Diodes, Bipolar Transistor Operation

## 1. First-Principles Intuition & Invariants

The PN junction is the atomic-scale boundary between two oppositely doped semiconductor regions, and it forms the foundation of every modern transistor, diode, and integrated circuit. Before we examine the mathematics and measurement protocols that enable practitioners to design, test, and troubleshoot real semiconductor devices, we must establish the physical intuition that governs their behavior.

When a p-type semiconductor (doped with acceptors, creating holes as majority carriers) is brought into contact with an n-type semiconductor (doped with donors, creating electrons as majority carriers), the resulting junction exhibits a remarkable property: it spontaneously develops an internal electric field that opposes further carrier diffusion. This field arises not from any external voltage source, but from the fundamental quantum-mechanical tendency of carriers to diffuse from high concentration to low concentration, coupled with the Coulomb attraction between ionized dopant atoms and mobile carriers.

At the moment of junction formation, electrons from the n-region diffuse across the boundary into the p-region, where they recombine with holes. Similarly, holes diffuse from p to n and recombine with electrons. This recombination process leaves behind exposed positive ions (donor atoms) on the n-side and negative ions (acceptor atoms) on the p-side. These fixed, immobile charge distributions cannot recombine—they are locked into the crystal lattice—and they create an electric field pointing from the n-region (positive) toward the p-region (negative). This field is the **junction potential** or **built-in potential**, denoted $V_{bi}$.

The built-in potential arises from charge balance. In equilibrium, the electric field produced by the ionized dopant layer exactly opposes further diffusion, such that the net current across the junction is zero. Practitioners measure this potential using capacitive techniques or by observing the turn-on voltage of a diode under forward bias. For silicon at room temperature, $V_{bi}$ typically ranges from 0.6 to 0.8 volts; for germanium, 0.25 to 0.35 volts. This value is not arbitrary—it emerges directly from the charge concentrations and thermal voltage $V_T = k_B T / q$, where $k_B$ is Boltzmann's constant, $T$ is absolute temperature in Kelvin, and $q$ is the elementary charge (1.602 × 10⁻¹⁹ coulombs).

Understanding the depletion region is essential for grasping how junctions behave under applied bias. The depletion region is the narrow zone adjacent to the junction where mobile carriers have been swept away or recombined, leaving only the ionized dopant charges. Within this region—typically 0.1 to 1 micrometer wide in modern devices—the electric field is strong enough that it dominates over thermal diffusion. Beyond the depletion region, the semiconductor remains quasi-neutral: positive and negative charges remain well-balanced, and carrier motion is governed primarily by diffusion and thermal forces rather than the junction field.

The width of the depletion region grows as the junction is reverse-biased (i.e., when an external voltage repels carriers away from the junction) and shrinks as it is forward-biased (i.e., when an external voltage attracts carriers toward the junction). This modulation of depletion width is why junctions exhibit a voltage-dependent capacitance: the capacitor formed by the charge separation across the depletion region has a "plate separation" that depends on the applied voltage. This **junction capacitance** is a critical parameter in circuit design, RF applications, and frequency-dependent circuit behavior.

The invariant principle that governs all junction behavior is **Boltzmann equilibrium**: in thermal equilibrium, the product of electron and hole concentrations remains constant and equals the intrinsic carrier concentration squared, $n_i^2$. This relationship, combined with charge neutrality outside the depletion region, uniquely determines the voltage distribution across the junction and the magnitude of the built-in potential. Any applied external voltage perturbs this equilibrium, driving net current to flow across the junction.

## 2. Core Architecture & Mechanics

### 2.1 The Depletion Approximation and Space-Charge Analysis

The depletion approximation is the cornerstone analytical tool for understanding junction behavior. It simplifies the charge distribution within the depletion region by assuming a sharp boundary: inside the depletion region, the electric field varies linearly with position (because the charge density is approximately constant), and outside the depletion region, the field is zero. In reality, carrier concentrations vary smoothly across the junction, but the depletion approximation captures the essential physics with remarkable accuracy for practical devices.

Consider a one-dimensional PN junction at thermal equilibrium. Let the p-region occupy $x < 0$ with acceptor concentration $N_A$, and the n-region occupy $x > 0$ with donor concentration $N_D$. The depletion region extends from $-x_p$ to $+x_n$, where $x_p$ and $x_n$ are the extents of the depletion region into the p and n regions respectively.

Within the depletion region, the charge density $\rho$ is approximately piecewise constant: $\rho = +q N_D$ for $0 < x < x_n$ (positive donor ions) and $\rho = -q N_A$ for $-x_p < x < 0$ (negative acceptor ions). Poisson's equation in one dimension is:

$$\frac{d^2 V}{dx^2} = -\frac{\rho}{\epsilon_s}$$

where $\epsilon_s$ is the permittivity of the semiconductor material. Inside the n-region of the depletion layer, the electric field $E(x) = -dV/dx$ increases linearly from zero at $x = x_n$ to a maximum at the junction $x = 0$:

$$E(x) = \frac{q N_D}{\epsilon_s}(x_n - x), \quad 0 < x < x_n$$

By symmetry of charge balance (the total positive charge in the depleted donor region must equal the total negative charge in the depleted acceptor region), we have $N_D x_n = N_A x_p$. The maximum electric field at the junction is:

$$E_{max} = \frac{q N_D x_n}{\epsilon_s} = \frac{q N_A x_p}{\epsilon_s}$$

Integrating the electric field to find the potential drop across the depletion region yields the built-in potential. Under reverse bias with applied voltage $V_R$ (positive voltage pushing carriers away from the junction), the total voltage across the junction is $V_R + V_{bi}$, and the depletion width increases. Under forward bias with applied voltage $V_F$, the total voltage across the junction is reduced to $V_{bi} - V_F$, and the depletion width decreases, allowing carriers to overflow the reduced barrier.

### 2.2 The Shockley Diode Equation: From Physics to Practice

The Shockley diode equation is the fundamental relationship between applied voltage and diode current. It emerges from solving the drift-diffusion equations in the quasi-neutral regions (outside the depletion layer) while accounting for the exponential Boltzmann distribution of carriers across the junction potential.

$$I = I_s \left( e^{qV/k_B T} - 1 \right)$$

Here, $I$ is the total diode current, $I_s$ is the **saturation current** (the reverse leakage current when the diode is reverse-biased), $V$ is the applied voltage (positive for forward bias, negative for reverse bias), and $q/k_B T = 1/V_T$ is the inverse thermal voltage. At room temperature (300 K), $V_T \approx 26$ millivolts, so the exponential factor has a characteristic voltage scale of tens of millivolts.

The saturation current $I_s$ depends on the minority carrier concentrations, diffusion coefficients, and the junction area. In silicon, $I_s$ is temperature-dependent: it roughly doubles for every 5-kelvin increase in temperature (for small temperature ranges). Practitioners measure $I_s$ by extrapolating the forward-bias current back to zero voltage, or by carefully measuring reverse leakage current at a known reverse bias and applying the Boltzmann factor relationship.

Forward bias (positive $V$) causes the exponential term to dominate, and current grows rapidly. When $qV \gg k_B T$ (i.e., $V$ significantly exceeds the thermal voltage), the $-1$ term becomes negligible, and $I \approx I_s e^{qV/V_T}$. For every 60 millivolts of forward voltage increase, the current increases by a factor of 10 in silicon. This steep exponential relationship is why diodes turn on sharply at the built-in potential: the current transitions from nearly zero (reverse bias) to substantial (forward bias) over a voltage range of only a few hundred millivolts.

Reverse bias (negative $V$) makes the exponential term vanish, leaving $I \approx -I_s$. The current approaches a constant value independent of the magnitude of reverse voltage—this is the reverse saturation current, and it is limited by the thermal generation of carriers in the depletion region, not by the applied field. In silicon, $I_s$ is extremely small (picoamperes per square micrometer of junction area at room temperature), which is why silicon diodes are excellent rectifiers. In germanium, $I_s$ is larger (nanoamperes per square micrometer), leading to greater reverse leakage and poorer rectification.

The diode's **ideality factor** $n$ modifies this equation in practice:

$$I = I_s \left( e^{qV/(n k_B T)} - 1 \right)$$

For ideal junctions, $n = 1$. In real devices, $n$ ranges from 1 to 2 depending on the dominant recombination mechanism. When $n = 2$, recombination in the depletion region dominates; when $n = 1$, diffusion in the quasi-neutral regions dominates. Practitioners extract $n$ by measuring the slope of the forward current on a semi-logarithmic plot: the slope is $q/(n k_B T)$, so $n$ equals the measured slope times $k_B T / q$.

### 2.3 Measurement and Characterization: Diode IV Curves

Hands-on characterization of a PN junction diode begins with measuring its current-voltage (IV) characteristic. A typical measurement setup uses a current source (or a resistive series element with a variable voltage source) to vary the applied voltage and measure the resulting current. For forward-bias measurements, use a transimpedance amplifier or measure the voltage across a known series resistor. For reverse-bias measurements, use a high-impedance electrometer or a transimpedance amplifier with femtoampere sensitivity.

A semi-logarithmic plot (current on a logarithmic y-axis, voltage on a linear x-axis) reveals the diode's behavior across many orders of magnitude. In forward bias, the curve is a nearly straight line on the semi-log plot, with slope corresponding to the ideality factor. By fitting the straight-line region to the Shockley equation, you can extract both $I_s$ and $n$. In reverse bias, the curve is flat at the saturation current level, until the breakdown voltage is reached, where current rises sharply.

Temperature dependence provides another important characterization protocol. Measure the same diode at multiple temperatures (using a temperature-controlled chamber or a peltier element on a test fixture) and observe how $I_s$ shifts. The temperature coefficient of $I_s$ is approximately $+0.06 \text{ V/K}$ for silicon, meaning $I_s$ roughly doubles every 5 kelvin. Measure the forward voltage at a fixed current (e.g., 1 mA) at each temperature; it should decrease by about $-2 \text{ mV/K}$. This negative temperature coefficient of forward voltage is why LEDs and laser diodes require active temperature compensation in precision analog circuits.

### 2.4 Breakdown Mechanisms: Avalanche and Zener Effects

When a PN junction is reverse-biased with sufficient voltage, it eventually breaks down—the reverse current rises sharply to large values, often destructively. Two distinct mechanisms cause this breakdown, and practitioners must understand both to design circuits that operate safely near the breakdown boundary.

**Zener breakdown** occurs in heavily doped junctions where the depletion region is very narrow (typically less than 100 nanometers). The strong electric field in a narrow depletion region causes **band-to-band tunneling**: electrons in the valence band quantum mechanically tunnel directly into the conduction band, creating electron-hole pairs. These thermally generated carriers contribute to the reverse current, and the tunneling rate rises steeply with applied reverse voltage. Zener breakdown typically occurs at voltages below 5 volts and is relatively independent of temperature. Zener diodes (deliberately designed for narrow-depletion, heavily doped junctions) exploit this effect to create precise voltage references.

**Avalanche breakdown** occurs in lightly doped junctions with wider depletion regions (typically 1 to 10 micrometers). When the reverse electric field becomes strong enough, it accelerates carriers to kinetic energies sufficient to ionize lattice atoms through collision. Each collision creates an additional electron-hole pair, and these new carriers are themselves accelerated, creating an exponential cascade of ionization—an avalanche. Avalanche breakdown typically occurs at voltages above 5 to 10 volts and exhibits a negative temperature coefficient: the breakdown voltage decreases as temperature increases. This is because thermal energy provides carriers with extra kinetic energy, requiring less applied field to trigger ionization.

The **breakdown voltage** $V_{BR}$ can be estimated from the junction parameters. For a one-sided step junction (where one side is much more heavily doped than the other), the breakdown voltage is approximately:

$$V_{BR} \approx \frac{\epsilon_s E_{crit}^2}{2 q N_L}$$

where $E_{crit}$ is the critical electric field for impact ionization (typically 3 × 10⁵ V/cm for silicon) and $N_L$ is the concentration of the lightly doped side. Practitioners use this relationship to predict breakdown voltage from doping profiles measured via capacitance-voltage techniques or from secondary ion mass spectrometry (SIMS).

Beyond the breakdown point, the reverse current is limited only by the series resistance of the device leads and bulk semiconductor regions. In a diode designed to survive breakdown (like a Zener diode), the junction is biased to operate in the avalanche or Zener region, where the voltage remains approximately constant despite large current variations. This voltage regulation property is exploited in shunt voltage regulators, where a Zener diode is connected in parallel with a load to clamp the voltage.

### 2.5 The Bipolar Junction Transistor: Ebers-Moll Model

A bipolar junction transistor (BJT) is fundamentally two back-to-back PN junctions: an emitter-base junction and a base-collector junction. Understanding the BJT requires extending the single-junction analysis to this two-junction geometry and accounting for the interaction between the two junctions.

The **Ebers-Moll model** is the standard large-signal circuit model for BJT operation. It describes the BJT in terms of two parasitic diodes: the B-E junction diode and the B-C junction diode, each governed by a Shockley-like relationship, coupled by transport coefficients that relate to the physical dimensions and doping profiles of the device.

Consider an NPN transistor (emitter N, base P, collector N). When the base-emitter junction is forward-biased and the base-collector junction is reverse-biased, the transistor enters the **active mode**. In this mode, electrons are injected from the emitter into the base, where they diffuse across the narrow base region and are swept into the collector by the reverse-bias field of the collector-base junction. The key insight is that most injected emitter electrons reach the collector before recombining in the base, because the base is intentionally made very thin (typically 100 nanometers to a few micrometers in modern devices).

The Ebers-Moll equations in the active mode are:

$$I_E = I_{ES} \left( e^{qV_{BE}/k_B T} - 1 \right)$$

$$I_C = \beta_F I_B + I_{CO} e^{qV_{BC}/k_B T}$$

where $I_E$ is the emitter current, $I_C$ is the collector current, $I_B$ is the base current, $V_{BE}$ is the base-emitter voltage, $V_{BC}$ is the base-collector voltage, $I_{ES}$ is the emitter saturation current, $I_{CO}$ is the collector-base saturation current, and $\beta_F$ is the **forward current gain** (or $h_{FE}$), which relates the collector and base currents: $I_C = \beta_F I_B$.

The forward current gain $\beta_F$ emerges from the device geometry and doping. It depends on the **base transport factor** $\alpha_T$, which is the fraction of emitter current that reaches the collector without recombining in the base. For a thin, lightly doped base, $\alpha_T$ is close to unity (0.99 to 0.999), meaning 99 to 99.9 percent of injected carriers reach the collector. The current gain relates to the transport factor as:

$$\beta_F = \frac{\alpha_T}{1 - \alpha_T}$$

So if $\alpha_T = 0.99$, then $\beta_F = 99$. This explains why small base currents produce large collector currents: the emitter injects many carriers, most reach the collector, and only the small fraction that recombine in the base must be replenished by base current.

In the active mode with reverse-biased collector-base junction, the second term in the collector current equation ($I_{CO} e^{qV_{BC}/k_B T}$) is negligible, so:

$$I_C \approx \beta_F I_B$$

This is the familiar linear relationship taught in introductory electronics, but it is only valid in the active mode. When the base-collector junction becomes forward-biased (saturation mode), both junctions are forward-biased, and the transistor no longer behaves as a current amplifier.

In **saturation**, both the B-E and B-C junctions are forward-biased. Carriers are injected from both the emitter (across the forward-biased B-E junction) and the collector (across the forward-biased B-C junction). The transistor becomes a pair of resistances—the emitter-base resistance and the collector-base resistance—and the current amplification breaks down. The minimum base current required to drive the transistor into saturation is called the **base overdrive**, and practitioners deliberately overdrive the base (supply 10 to 20 times the minimum base current needed to achieve the desired collector current) to ensure saturated operation in switching applications.

### 2.6 The Early Effect and Output Resistance

Real transistors exhibit a phenomenon called the **Early effect** (named after James M. Early, who first described it): even in the active mode, the collector current increases slightly with increasing reverse voltage on the collector-base junction. This occurs because the width of the depletion region at the collector-base junction increases with reverse voltage, effectively narrowing the quasi-neutral base region. A narrower base means more injected carriers reach the collector, and fewer recombine, so the current gain increases.

The Early effect is quantified by the **Early voltage** $V_A$ (typically 50 to 200 volts for small-signal transistors, much higher for modern integrated circuit transistors). The collector current in the active mode is:

$$I_C = \beta_F I_B \left( 1 + \frac{V_{CE}}{V_A} \right)$$

where $V_{CE}$ is the collector-emitter voltage. For $V_{CE} \gg V_A$, the Early effect dominates and current gain is severely reduced. Practitioners account for the Early effect by including an output resistance $r_o$ in the BJT small-signal model:

$$r_o = \frac{V_A}{I_C}$$

At a collector current of 1 mA and an Early voltage of 100 volts, $r_o = 100 \text{ k}\Omega$. This output resistance is significant in analog circuit design, particularly in high-impedance circuits and precision amplifiers where the Early effect can introduce substantial gain variations with operating point.

### 2.7 Base Transport Factor and Reverse Saturation Current Temperature Dependence

The base transport factor $\alpha_T$ depends on the base thickness and the minority carrier diffusion length in the base. For a transistor with base thickness $W_B$ and electron diffusion length in the base $L_B$:

$$\alpha_T \approx 1 - \frac{W_B}{2 L_B}$$

when $W_B \ll L_B$ (a thin base). A thinner base or longer diffusion length increases $\alpha_T$, improving the current gain. Modern high-performance transistors achieve very thin bases (tens of nanometers) and long diffusion lengths (hundreds of nanometers) by precise doping and crystal growth, resulting in $\alpha_T$ values exceeding 0.999.

The collector-base reverse saturation current $I_{CO}$ is temperature-dependent, following an exponential relationship similar to the diode equation:

$$I_{CO}(T) = I_{CO}(T_0) \left( \frac{T}{T_0} \right)^n e^{q V_{g,eff}(T_0 - T) / k_B T T_0}$$

where $n$ is typically 3 for silicon (reflecting generation-recombination in the depletion region), and $V_{g,eff}$ is the temperature-dependent bandgap. Over a 10-kelvin temperature increase, $I_{CO}$ typically increases by a factor of 2 to 4, depending on the specific device and the temperature range.

### 2.8 Heterojunctions and Band Alignment

Modern high-performance transistors employ **heterojunctions**: junctions between two different semiconductor materials with different bandgaps. The most common example is the silicon-germanium (SiGe) heterojunction bipolar transistor (HBT), which uses a germanium base layer between silicon emitter and collector regions.

The key advantage of heterojunctions is that the emitter-base junction potential is reduced compared to a homojunction with the same doping. This occurs because the bandgap discontinuity at the material boundary allows a lower potential to achieve the same carrier injection. A lower potential means less voltage is wasted in the base-emitter junction, leaving more voltage for the active circuit, and importantly, it reduces the reverse saturation current in the emitter junction, improving the overall current gain.

The band alignment at a heterojunction is characterized by the **conduction band offset** $\Delta E_C$ and **valence band offset** $\Delta E_V$. For SiGe/Si heterojunctions, the bandgap difference of about 0.12 eV is split roughly equally between conduction and valence band offsets. SiGe HBTs achieve current gains exceeding 200 with lower reverse saturation currents than silicon BJTs, and they are widely used in RF and mixed-signal integrated circuits.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Thermal Management and Safe Operating Area

Every transistor and diode has a **maximum junction temperature** specified by the semiconductor manufacturer, typically 150°C for commercial devices and up to 200°C for high-temperature variants. Junction temperature is not simply the ambient temperature—it is elevated by the power dissipated in the device itself. A transistor carrying 100 mA at 5 volts dissipates 0.5 watts, and that power heats the junction.

The relationship between junction temperature and ambient temperature is:

$$T_J = T_A + P \cdot R_{\theta}$$

where $T_J$ is the junction temperature, $T_A$ is the ambient temperature, $P$ is the power dissipated, and $R_{\theta}$ is the **thermal resistance** from junction to ambient. Thermal resistance depends on the device package and whether a heat sink is used. A small-signal transistor in a TO-92 plastic package might have $R_{\theta}$ of 400 to 600°C/W without a heat sink; attached to a modest aluminum heat sink with thermal compound, it might drop to 100°C/W. Power transistors in large packages with integral heat sinks can achieve $R_{\theta}$ values below 1°C/W.

Practitioners must ensure that the junction temperature never exceeds the specified maximum. This is enforced by the **Safe Operating Area (SOA)** graph, which plots the maximum allowable collector current as a function of collector-emitter voltage.

The Safe Operating Area is bounded by four constraints: maximum current (limited by bond-wire fusing and metallization), maximum voltage (limited by avalanche breakdown), maximum power dissipation (limited by junction temperature), and secondary breakdown (a localized thermal runaway phenomenon in bipolar transistors where current constricts to a small region, creating a hot spot that further concentrates current until the device fails). Secondary breakdown typically occurs at high $V_{CE}$ and moderate current, well below the DC power limit, and is exacerbated by inductive loads that force the transistor through high-voltage, high-current trajectories during switching. To operate safely, designers must verify that all load lines remain within the SOA boundary for both DC and transient conditions, provide adequate heat sinking to maintain $T_J < T_{J,\text{max}}$, and implement snubber circuits or active clamping to suppress inductive voltage spikes. Failure modes include thermal runaway (where increased temperature reduces $V_{BE}$ threshold, increasing $I_C$, which further heats the junction), avalanche breakdown (where impact ionization in the collector-base depletion region generates a runaway multiplication of carriers), and oxide rupture in integrated devices (where electrostatic discharge or overvoltage punctures thin gate oxides in adjacent MOSFETs). Understanding these physical limits and thermal dynamics is essential for reliable circuit design—ignoring SOA constraints or thermal resistance leads to catastrophic and often permanent device failure.

## Summary & Verification Matrix

| Concept | Governing Invariant / Equation | Physical Mechanism | Diagnostic Criterion |
|---------|-------------------------------|-------------------|---------------------|
| **PN Junction Equilibrium** | $V_\text{bi} = \frac{kT}{q} \ln\!\left(\frac{N_A N_D}{n_i^2}\right)$ | Diffusion of majority carriers creates depletion region; built-in field opposes further diffusion until equilibrium | Measure $V_\text{bi}$ via C-V profiling: $\frac{1}{C^2} \propto V_R + V_\text{bi}$ |
| **Diode I-V Characteristic** | $I = I_S \left(e^{V/nV_T} - 1\right)$; $I_S \propto n_i^2$ | Forward bias lowers barrier, exponentially increasing minority carrier injection; reverse bias saturates at $-I_S$ | Verify $n \approx 1$ (ideal), $n \approx 2$ (recombination-dominated); $I_S$ doubles every ~10°C |
| **BJT Current Gain** | $\beta = \frac{I_C}{I_B} = \frac{D_n W_B^{-1}}{D_p W_E^{-1}} \cdot \frac{N_D^\text{(base)}}{N_A^\text{(emitter)}}$ | Emitter efficiency and base transport factor determine fraction of emitter current reaching collector | Measure $\beta$ at multiple $I_C$: peaks at mid-current, drops at low $I_C$ (recombination) and high $I_C$ (high-level injection, Kirk effect) |
| **Base Width Modulation (Early Effect)** | $I_C = I_S e^{V_{BE}/V_T} \left(1 + \frac{V_{CE}}{V_A}\right)$; $V_A \propto W_B^2$ | Increasing $V_{CE}$ widens collector depletion region, shrinking effective $W_B$, raising $\beta$ and $I_C$ | Measure output resistance $r_o = \frac{V_A}{I_C}$ from $I_C$ vs. $V_{CE}$ slope; typical $V_A = 50$–200 V |
| **Thermal Runaway & SOA** | $T_J = T_A + P \cdot R_\theta$; $T_J < T_{J,\text{max}}$ | Power dissipation heats junction; thermal feedback can cause current concentration (secondary breakdown) | Verify all DC and transient load lines remain within SOA; measure $T_J$ via $V_{BE}$ at known $I_C$ (temperature coefficient $\approx -2$ mV/°C) |
| **Heterojunction Advantage** | $\beta_\text{HBT} \propto \exp\!\left(\frac{\Delta E_g}{kT}\right)$; $I_S \propto n_i^2(\text{emitter})$ | Wider-gap emitter suppresses hole injection from base, dramatically improving emitter efficiency and reducing $I_S$ | SiGe HBTs: $\beta > 200$, $f_T > 200$ GHz; verify graded Ge profile via SIMS or C-V profiling of bandgap variation |
