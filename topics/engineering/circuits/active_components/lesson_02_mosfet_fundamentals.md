# Lesson 2: MOSFET Device Theory

## 1. First-Principles Intuition & Invariants

The Metal-Oxide-Semiconductor Field-Effect Transistor occupies a singular position in the history of technology. No other device has scaled across eleven orders of magnitude in physical dimension while preserving the essential physics that governs its operation. Understanding why requires going deeper than the standard textbook treatment of a voltage-controlled current source. The MOSFET is, at its core, an electrostatically controlled resistor whose channel conductivity is modulated by charge induced at an oxide-semiconductor interface. Everything else—the threshold voltage, the saturation current, channel length modulation, the body effect—derives from this one physical truth.

Begin with the MOS capacitor, because the transistor is impossible to understand without it. Consider a p-type silicon substrate with acceptor concentration $N_A$ atoms per cubic centimeter. When you deposit a thin layer of silicon dioxide on the surface and place a metal (or polysilicon) gate electrode on top, you have constructed the most important capacitor in electronics. This structure is not merely a passive energy storage element. It is a surface charge controller, and its behavior under bias defines every operating regime of the transistor.

Apply a small negative voltage to the gate with respect to the substrate. Holes in the p-type silicon are attracted toward the surface, and the region immediately beneath the oxide accumulates extra positive charge. This is the **accumulation** regime. The oxide capacitance $C_{ox} = \varepsilon_{ox}/t_{ox}$ dominates the electrical behavior, where $\varepsilon_{ox} \approx 3.9\varepsilon_0$ for $\text{SiO}_2$ and $t_{ox}$ is the oxide thickness. For a 5 nm gate oxide, $C_{ox} \approx 6.9 \ \text{fF}/\mu\text{m}^2$—a number worth memorizing because it directly sets the transconductance of every MOSFET you will ever size.

Now increase the gate voltage toward zero and beyond into positive territory. Holes are repelled from the surface, leaving behind negatively charged ionized acceptors. The surface enters **depletion**. The depletion charge per unit area is $Q_{dep} = -qN_A W_{dep}$, where $W_{dep}$ is the depletion width, governed by Poisson's equation:

$$W_{dep} = \sqrt{\frac{2\varepsilon_{si}\phi_s}{qN_A}}$$

Here $\phi_s$ is the surface potential—the electrostatic potential at the Si-SiO₂ interface relative to the bulk. As you continue increasing the gate voltage, $\phi_s$ rises until at a critical value called **strong inversion**, the surface minority carrier concentration (electrons, in p-type silicon) equals the bulk majority carrier concentration. This occurs when $\phi_s = 2\phi_F$, where the Fermi potential is:

$$\phi_F = \frac{kT}{q}\ln\left(\frac{N_A}{n_i}\right)$$

For $N_A = 10^{17} \ \text{cm}^{-3}$ at 300 K, $\phi_F \approx 420 \ \text{mV}$ and $2\phi_F \approx 840 \ \text{mV}$. At this surface potential, a conducting channel of electrons exists at the silicon surface, and the device is on. The gate voltage at which this transition occurs is the **threshold voltage** $V_T$.

The threshold voltage derivation is worth carrying through completely because every practitioner who treats $V_T$ as a datasheet number rather than a physical consequence eventually gets burned by a circuit that fails at corner temperature or under body bias. The gate voltage must simultaneously drop across the oxide and develop the surface potential $2\phi_F$ while supporting the depletion charge:

$$V_T = V_{FB} + 2\phi_F + \frac{|Q_{dep,max}|}{C_{ox}}$$

The flat-band voltage $V_{FB}$ accounts for the work-function difference between the gate material and silicon, plus any fixed oxide charge $Q_{ox}$ trapped at the interface:

$$V_{FB} = \phi_{ms} - \frac{Q_{ox}}{C_{ox}}$$

For an n+ polysilicon gate on p-type silicon, $\phi_{ms} \approx -1.1 \ \text{V}$. Positive oxide charge (common in older processes from sodium contamination or radiation damage) shifts $V_{FB}$ negative, pulling $V_T$ down and threatening to push an NMOS device into depletion-mode operation. This is not academic: radiation-hardened designs for space applications must guard against exactly this charge accumulation in the gate oxide.

Substituting the maximum depletion charge $|Q_{dep,max}| = qN_A W_{dep,max} = \sqrt{4\varepsilon_{si}qN_A\phi_F}$:

$$V_T = \phi_{ms} - \frac{Q_{ox}}{C_{ox}} + 2\phi_F + \frac{\sqrt{4\varepsilon_{si}qN_A\phi_F}}{C_{ox}}$$

This expression reveals four independent handles that process engineers use to target a specific $V_T$: gate work function, oxide charge control, body doping, and oxide thickness. Modern foundries use threshold implants—shallow ion implantation into the channel region—to adjust $V_T$ independently of the other parameters, enabling high-$V_T$, standard-$V_T$, and low-$V_T$ device flavors on the same die.

---

## 2. Core Architecture & Mechanics

### I-V Characteristics: From Channel Charge to Drain Current

With the channel inverted and a drain-to-source voltage $V_{DS}$ applied, charge flows from source to drain. The channel charge density per unit area at a point $x$ along the channel (measured from source) is:

$$Q_i(x) = -C_{ox}\left[V_{GS} - V_T - V(x)\right]$$

where $V(x)$ is the channel potential at position $x$. The drift current density at that point is $J = Q_i(x) \cdot \mu_n \cdot \mathcal{E}(x)$, and integrating from source to drain (a standard derivation using $I_{DS} = $ constant in steady state) yields the foundational result. In the **linear region** ($V_{DS} < V_{GS} - V_T$):

$$I_{DS} = \mu_n C_{ox} \frac{W}{L}\left[\left(V_{GS} - V_T\right)V_{DS} - \frac{V_{DS}^2}{2}\right]$$

The ratio $W/L$ is the aspect ratio—the single most consequential design parameter you control at the schematic level. Doubling $W$ doubles the drive current, the gate capacitance, and the layout area. Every digital standard cell is sized by this ratio, and every analog circuit trade-off in gain, noise, and bandwidth lives here.

As $V_{DS}$ increases, the inversion layer charge at the drain end of the channel shrinks because the gate-to-channel voltage there is $V_{GS} - V_{DS}$. When $V_{DS} = V_{GS} - V_T$, the channel charge at the drain pinches to zero. This is **pinch-off**. For $V_{DS} > V_{GS} - V_T$, the device enters **saturation** and the current saturates at:

$$I_{DS,sat} = \frac{\mu_n C_{ox}}{2} \frac{W}{L}\left(V_{GS} - V_T\right)^2$$

The physical mechanism here is subtle and frequently misunderstood. Pinch-off does not mean current stops. It means the high-field region at the drain sweeps carriers across in velocity saturation, and the channel from source to pinch-off point behaves as if the device sees a fixed $V_{DS} = V_{GS} - V_T$. The remaining voltage $V_{DS} - (V_{GS}-V_T)$ drops across a short depletion region at the drain.

```
NMOS I-V Operating Regions

      I_DS
        ^
        |          Saturation Region
        |        (I_DS ∝ (V_GS - V_T)²)
        |     .....V_GS4..........___________
        |   ..    V_GS3....._____/
        | ..    ..     ____/
        |.    ..  ____/  V_GS2
        |   .. __/
        |  .._/ V_GS1
        | ./
        |/___________________________________________> V_DS
              |
         Linear  |  Saturation
         Region  |  (V_DS = V_GS - V_T boundary)
```

The transition between regions is not a sharp discontinuity in hardware, though SPICE models it piecewise. Near pinch-off, the quadratic model systematically overestimates current in short-channel devices because carrier velocity saturates before channel pinch-off, an effect we address when discussing short-channel physics.

### Channel Length Modulation

A first-year approximation treats the saturation current as independent of $V_{DS}$. Any practicing circuit designer knows this is false: the output conductance $g_{ds} = \partial I_{DS}/\partial V_{DS}$ is nonzero in saturation, and it sets the intrinsic voltage gain of every MOSFET amplifier stage. The mechanism is **channel length modulation**. As $V_{DS}$ increases beyond pinch-off, the depletion region at the drain extends slightly back into the channel, effectively shortening the electrical channel length from $L$ to $L - \Delta L$. Because $I_{DS} \propto 1/L$, more current flows.

The empirical correction introduces the channel length modulation parameter $\lambda$:

$$I_{DS,sat} = \frac{\mu_n C_{ox}}{2}\frac{W}{L}(V_{GS}-V_T)^2 (1 + \lambda V_{DS})$$

The parameter $\lambda$ scales inversely with channel length—long-channel devices have small $\lambda$ and high output impedance, which is why cascode mirrors and telescopic op-amp topologies use long-$L$ devices to maximize $r_o = 1/(\lambda I_{DS})$. For a 180 nm NMOS with $L = 2 \ \mu\text{m}$ biased at $I_{DS} = 100 \ \mu\text{A}$, $\lambda \approx 0.05 \ \text{V}^{-1}$ yields $r_o = 200 \ \text{k}\Omega$. Shrink to minimum-length $L = 180 \ \text{nm}$ and $\lambda$ rises by an order of magnitude, collapsing $r_o$ to tens of kilohms—a catastrophic loss of gain in any analog block.

### The Body Effect

The threshold voltage derivation assumed the substrate is at the same potential as the source. When the source-to-body junction is reverse biased by a voltage $V_{SB} > 0$ (for NMOS), the depletion region under the channel widens to accommodate the additional reverse bias. More depletion charge must be imaged on the gate, requiring a higher gate voltage to reach strong inversion. The threshold voltage shifts:

$$V_T(V_{SB}) = V_{T0} + \gamma\left(\sqrt{2\phi_F + V_{SB}} - \sqrt{2\phi_F}\right)$$

The body effect coefficient $\gamma = \sqrt{2\varepsilon_{si}qN_A}/C_{ox}$ has units of $\text{V}^{1/2}$. For a standard 180 nm process, $\gamma \approx 0.5 \ \text{V}^{1/2}$. Consider a source follower where the output node is several hundred millivolts above ground: the source-body reverse bias increases $V_T$, reducing $V_{GS} - V_T$ and decreasing the buffer's drive strength. This is not a simulation artifact. It is a real, bench-measurable effect that explains why source-follower linearity degrades with signal swing and why well-aware designers tie the bulk to the source wherever the process allows isolated N-wells or triple-well structures.

```
Body Effect: V_T vs. V_SB

     V_T (V)
      ^
  0.9 |                              *
      |                         *
  0.7 |                    *
      |               *
  0.5 |          *
      |     *
  0.3 | *
      |___________________________________> V_SB (V)
        0    0.5    1.0    1.5    2.0

   γ = 0.5 V^(1/2), 2φ_F = 0.84 V, V_T0 = 0.35 V
```

### Subthreshold Conduction

Below threshold, the classical square-law model predicts zero drain current. Silicon disagrees. When $V_{GS} < V_T$, the surface is in weak inversion: the channel is not fully formed, but the minority carrier concentration at the surface is elevated above the bulk value by an exponential factor. Carriers diffuse from source to drain rather than drifting, and the current takes the form:

$$I_{DS} = I_0 \frac{W}{L}\exp\left(\frac{V_{GS} - V_T}{n V_T^{therm}}\right)\left(1 - e^{-V_{DS}/V_T^{therm}}\right)$$

Here $V_T^{therm} = kT/q \approx 26 \ \text{mV}$ at 300 K is the thermal voltage, and $n$ is the subthreshold slope factor $n = 1 + C_{dep}/C_{ox} \geq 1$. The subthreshold swing $S$ describes how many millivolts of gate voltage are required to change the drain current by one decade:

$$S = n \cdot \frac{kT}{q} \ln(10) \approx n \times 60 \ \text{mV/decade}$$

The fundamental lower bound—60 mV/decade at room temperature—is a thermodynamic limit set by the Boltzmann distribution of carriers. It is why supply voltages cannot scale to zero even as transistors shrink, and it is why tunnel FETs and negative-capacitance FETs exist as research vehicles: they attempt to break this limit through non-Boltzmann injection mechanisms.

Subthreshold conduction is not merely a leakage curiosity. Ultra-low-power IoT processors deliberately operate in weak inversion where $I_{DS}$ is exponentially sensitive to $V_{GS}$, achieving the highest transconductance-to-current ratio $g_m/I_{DS}$ possible. For a device biased in weak inversion, $g_m/I_{DS} = 1/(nV_T^{therm}) \approx 38 \ \text{S/A}$—roughly five to ten times higher than the same device in strong inversion. The price is speed: the transition frequency $f_T = g_m/(2\pi C_{gs})$ is low because the absolute transconductance is small.

---

## 3. High-Performance Optimization & Failure Modes

### Short-Channel Effects

The classical long-channel MOSFET model assumes that the depletion region beneath the channel is controlled exclusively by the gate. In devices where $L$ is comparable to the source/drain depletion widths—below roughly $250 \ \text{nm}$ in a standard bulk CMOS process—this assumption breaks down catastrophically. The source and drain electric fields penetrate the channel, and the gate loses electrostatic control.

The first consequence is **threshold voltage roll-off**. As $L$ decreases, the source and drain depletion regions each contribute charge to the channel depletion region, reducing the net charge the gate must supply. The threshold voltage drops—sometimes by hundreds of millivolts—as $L$ approaches its minimum. Process engineers counteract this with halo (or pocket) implants: heavily doped pockets placed at the source and drain edges to suppress the lateral depletion spread, restoring gate control. Without halo implants, minimum-length transistors in a digital library would have $V_T$ values too low to suppress leakage in the off state.

The second consequence is **Drain-Induced Barrier Lowering (DIBL)**. In a long-channel device, the source-to-channel potential barrier is set entirely by the gate. In a short device, raising $V_{DS}$ allows the drain electric field to lower the source barrier, increasing current even when the gate voltage is below threshold. DIBL is characterized in millivolts of threshold shift per volt of drain-source voltage:

$$\text{DIBL} = \frac{\Delta V_T}{\Delta V_{DS}} \quad [\text{mV/V}]$$

A well-designed 65 nm node device exhibits DIBL below 100 mV/V. Values above 150 mV/V indicate inadequate gate length or insufficient halo dosing and manifest in silicon as anomalously high off-state current and poor subthreshold slope. You can directly measure DIBL on a parameter analyzer by extracting $V_T$ (using the constant-current method at $I_D = 100 \ \text{nA} \cdot W/L$) at $V_{DS} = 50 \ \text{mV}$ and again at $V_{DS} = 1.0 \ \text{V}$, then computing the difference.

The third short-channel effect is **velocity saturation**. Bulk silicon electron mobility is $\mu_n \approx 450 \ \text{cm}^2/\text{V}\cdot\text{s}$ at low fields. As the lateral electric field $\mathcal{E} = V_{DS}/L$ rises above roughly $10^4 \ \text{V/cm}$, carrier scattering with optical phonons limits drift velocity to a saturation value $v_{sat} \approx 10^7 \ \text{cm/s}$. For a 100 nm channel with $V_{DS} = 1 \ \text{V}$, $\mathcal{E} = 10^5 \ \text{V/cm}$—well into velocity saturation. The drain current in this regime becomes:

$$I_{DS,sat} \approx \mu_n C_{ox} \frac{W}{L}\left(V_{GS} - V_T\right)\frac{\mathcal{E}_{sat}L}{2}$$

which simplifies to $I_{DS} \propto (V_{GS} - V_T)$ rather than $(V_{GS} - V_T)^2$—a linear, not quadratic, dependence on overdrive. This is why short-channel device models in SPICE (BSIM4, PSP) look nothing like the Level 1 square-law model, and why gain stages designed with BSIM models perform differently from long-channel hand calculations.

### Gate Oxide Integrity and Hot Carrier Injection

The gate oxide is simultaneously the most important and the most fragile element of the MOSFET. Its job is to sustain an enormous electric field—a 3 nm oxide under 1 V of gate bias sees $\mathcal{E}_{ox} \approx 3.3 \ \text{MV/cm}$, approaching the dielectric breakdown field of SiO₂. Two degradation mechanisms limit device lifetime.

**Time-Dependent Dielectric Breakdown (TDDB)** occurs when defect precursors in the oxide bulk accumulate under sustained electric stress until a conductive filament of silicon forms between gate and channel. TDDB lifetime follows a Weibull distribution and is modeled using the E-model ($\ln(\text{lifetime}) \propto 1/\mathcal{E}_{ox}$) or the 1/E model depending on field regime. Foundry reliability rules enforce maximum gate voltage limits—violating them by even 10% can reduce oxide lifetime from ten years to months. When debugging anomalous gate leakage on a bench sample, a sudden increase in $I_G$ from picoamps to nanoamps is the signature of a partially formed breakdown path, and the device should be considered compromised.

**Hot Carrier Injection (HCI)** is a lateral-field effect. Near the drain pinch-off point, carriers accelerate to energies exceeding 1.5 eV—sufficient to surmount the Si-SiO₂ barrier and inject into the oxide, where they become trapped as fixed charge or interface states. HCI shifts $V_T$, degrades $g_m$, and increases the subthreshold slope over time. The worst-case bias condition for HCI in NMOS is $V_{GS} \approx V_{DS}/2$, which maximizes the product of impact ionization current and lateral electric field. Reliability engineers simulate HCI lifetime using device simulators (Sentaurus, Cogenda) with the Lucky Electron Model or more accurate non-local transport models. At the schematic level, the defense is: never allow a device to sustain a drain-source voltage exceeding the process nominal supply in steady state, and scrutinize any cascode bias that might momentarily collapse and expose a bottom device to full rail voltage.

### Bench Characterization: Extracting MOSFET Parameters

Understanding device physics reaches its full value when you can extract the model parameters yourself from a physical device. Using a semiconductor parameter analyzer (Keysight B1500A, Tektronix 4200-SCS, or a precision SMU pair), the standard extraction sequence proceeds as follows.

For threshold voltage extraction: sweep $V_{GS}$ from 0 to $V_{DD}$ with $V_{DS} = 50 \ \text{mV}$ (linear region, low-field). Plot $I_{DS}$ versus $V_{GS}$ and find the linear extrapolation intercept—the x-axis crossing gives $V_T$. Alternatively, the transconductance peak method identifies $V_T$ as the gate voltage at which $dg_m/dV_{GS}$ is maximum, which is more robust to mobility degradation at high overdrive.

For $\mu_n C_{ox}$: in the linear region at small $V_{DS}$, $I_{DS} \approx \mu_n C_{ox}(W/L)(V_{GS}-V_T)V_{DS}$. The slope of $I_{DS}$ versus $V_{GS}$ in the linear region, divided by $V_{DS} \cdot (W/L)$, directly yields $\mu_n C_{ox}$.

For $\lambda$: bias the device in saturation ($V_{DS} > V_{GS} - V_T$) at a fixed $V_{GS}$ and sweep $V_{DS}$. Plot $I_{DS}$ versus $V_{DS}$ and extrapolate the linear portion of the saturation region back to the x-axis. The intercept at $I_{DS} = 0$ occurs at $V_{DS} = -1/\lambda$—the Early voltage in MOS terminology.

For the body effect coefficient $\gamma$: repeat the $V_T$ extraction at multiple values of $V_{SB}$ from 0 to 2 V. Plot $V_T$ versus $\sqrt{2\phi_F + V_{SB}} - \sqrt{2\phi_F}$; the slope is $\gamma$. Any deviation from linearity at high $V_{SB}$ indicates nonuniform channel doping, which is expected near the halo implant edges in modern devices.

### Operating Point Design: Translating Physics to Bias Strategy

For analog circuit design, the MOSFET is biased using three knobs: the overdrive voltage $V_{ov} = V_{GS} - V_T$, the drain current $I_{DS}$, and the aspect ratio $W/L$. These three are not independent—$I_{DS} = \frac{1}{2}\mu_n C_{ox}(W/L)V_{ov}^2$ links them. The design space resolves into two camps.

High-overdrive biasing ($V_{ov} > 200 \ \text{mV}$) places the device firmly in strong inversion, where the square-law model is reasonably accurate, $g_m = \mu_n C_{ox}(W/L)V_{ov}$ is high in absolute terms, and $f_T = g_m/(2\pi C_{gs})$ is maximized. This is the regime of RF amplifiers, comparators, and high-speed switched-capacitor circuits where speed dominates power efficiency.

Low-overdrive biasing ($V_{ov} < 100 \ \text{mV}$, approaching weak inversion) gives the highest $g_m/I_{DS}$, lowest noise corner in some topologies, and best power efficiency. The penalty is nonlinearity: the transition between weak and moderate inversion is modeled poorly by both the ideal exponential and the ideal square law, and $g_m/I_{DS}$ versus inversion coefficient must be characterized from measured data or extracted via ACM or EKV compact models. Precision analog designers who operate in this regime use the inversion coefficient $IC = I_{DS}/(2n\mu C_{ox}(W/L)V_T^{therm^2})$ as a process-portable design variable, allowing topology design to be separated from technology targeting.

The unifying principle across all these regimes is electrostatics. Every parameter—threshold voltage, body effect, subthreshold slope, DIBL, oxide breakdown—traces back to the charge distribution at the Si-SiO₂ interface and the ability of the gate to control it. When a circuit fails to match simulation, when a device ages faster than the reliability model predicted, when a minimum-length mirror has the wrong output impedance, the right diagnostic reflex is always to return to that interface, ask what charge is there, and ask what field is controlling it.
