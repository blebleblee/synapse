# Lesson 2: DC-DC Converter Topologies

## 1. First-Principles Intuition & Invariants

Every switching power supply is, at its core, a controlled energy storage and release engine. Unlike a linear regulator, which dissipates the difference between input and output voltages as heat across a pass transistor, a switching converter routes energy through reactive components—inductors and capacitors—that store energy in magnetic and electric fields respectively, releasing it at a different voltage. The efficiency advantage is immediate and profound: an ideal switching converter wastes nothing, because no current flows through a resistive element to generate heat. Real converters fall short of ideal, but modern designs routinely exceed 95% efficiency, something a linear regulator cannot approach whenever the input-to-output voltage ratio deviates significantly from unity.

The unifying invariant across all DC-DC topologies is the volt-second balance on every inductor and the charge balance on every capacitor, evaluated at steady state over a complete switching cycle. These two constraints are not design choices—they are physical laws that the converter must obey or else the operating point will drift until a component fails or a protection circuit intervenes. For the inductor, the volt-second balance states that the integral of voltage across the inductor over one full period must be exactly zero. If it were not, the inductor current would ramp monotonically in one direction each cycle, eventually saturating the core or destroying the switch. For the capacitor, charge balance requires that the net charge delivered to and taken from the output capacitor over one cycle is zero at steady state, which forces the average current into the capacitor to be zero—a constraint that ties the inductor current ripple directly to the output voltage ripple.

The duty cycle $D$ is the dimensionless ratio of switch-on time $t_{on}$ to the full switching period $T_s$, so $D = t_{on}/T_s$. It is the single most consequential design parameter in any switching converter because it sets the voltage conversion ratio and, together with inductance and switching frequency, governs energy storage requirements and ripple amplitude. Increasing switching frequency $f_s$ reduces the energy that must be stored each cycle, allowing smaller magnetic components, but it increases switching losses—the power dissipated during the finite rise and fall times of the switch transitions—and demands tighter layout discipline to control the parasitic inductance and capacitance of PCB traces.

Understanding conduction modes is equally foundational. In **Continuous Conduction Mode (CCM)**, the inductor current never reaches zero; it oscillates between a minimum value $I_{L,min}$ and a maximum $I_{L,max}$ around the DC load current. In **Discontinuous Conduction Mode (DCM)**, the inductor current does reach zero before the next switch-on event, and there is a dead interval each cycle during which both the switch and the diode are off and the inductor delivers no current. CCM provides better transient response and lower peak switch currents at high load, but DCM can simplify control loop design because the converter behaves as a first-order system—the inductor, paradoxically, disappears as a state variable when it decharges to zero. The boundary between these modes is the **critical inductance** $L_{crit}$, below which the converter enters DCM for a given load current, and understanding this boundary is essential for any designer choosing an inductor value.

---

## 2. Core Architecture & Mechanics

### The Buck Converter

The buck converter steps voltage down. Its essential structure places a switch (typically a MOSFET) in series between the input and an LC filter, with a diode (or synchronous MOSFET) providing a freewheeling path when the switch opens.

```
       Q1
Vin ---/---+---L---+--- Vout
           |       |
          D1      C1    Load
           |       |
          GND----GND
```

When Q1 conducts for time $t_{on}$, the voltage across the inductor is $V_{in} - V_{out}$, and current ramps upward according to $\Delta I_L = (V_{in} - V_{out}) \cdot t_{on} / L$. When Q1 turns off, D1 clamps the switching node to ground, and the inductor voltage becomes $-V_{out}$, ramping current downward by $\Delta I_L = V_{out} \cdot t_{off} / L$. Applying volt-second balance—setting the two $\Delta I_L$ expressions equal—yields the CCM voltage conversion ratio immediately:

$$M_{buck} = \frac{V_{out}}{V_{in}} = D$$

The simplicity of this relationship is its own design tool. To produce 3.3 V from a 12 V rail at 500 kHz, the duty cycle is $D = 3.3/12 = 0.275$, so the switch conducts for $0.275 \times 2~\mu s = 550~ns$ each cycle. The inductor current ripple amplitude is set by:

$$\Delta I_L = \frac{(V_{in} - V_{out}) \cdot D}{f_s \cdot L} = \frac{V_{out}(1-D)}{f_s \cdot L}$$

A common design target is $\Delta I_L \approx 20\text{–}40\%$ of the full-load current $I_{out}$. For a 3 A load with 30% ripple, $\Delta I_L = 0.9$ A. Solving for $L$ at 500 kHz:

$$L = \frac{V_{out}(1-D)}{f_s \cdot \Delta I_L} = \frac{3.3 \times 0.725}{500000 \times 0.9} \approx 5.3~\mu H$$

Choose the nearest standard value: 5.6 µH or 6.8 µH, depending on the preferred ripple budget. The output capacitor's equivalent series resistance (ESR) often dominates the output voltage ripple more than the capacitive charge/discharge term. The voltage ripple contribution from ESR is simply $\Delta V_{ESR} = ESR \times \Delta I_L$, so a capacitor with 20 mΩ ESR and 0.9 A ripple contributes 18 mV of ripple—already significant in a 3.3 V rail requiring 1% regulation.

### The Boost Converter

The boost converter steps voltage up. The switch is now connected between the inductor's output node and ground, and the diode points from that node toward the output.

```
       L          D1
Vin ---+---+----->|---+--- Vout
           |          |
          Q1         C1    Load
           |          |
          GND--------GND
```

When Q1 is on, the diode is reverse-biased, and the inductor charges from $V_{in}$ with a current slope of $V_{in}/L$. When Q1 turns off, the inductor's stored energy forces current through D1 into the output capacitor and load. Volt-second balance over the full cycle gives:

$$M_{boost} = \frac{V_{out}}{V_{in}} = \frac{1}{1-D}$$

As $D \to 1$, the theoretical conversion ratio approaches infinity—but this is a dangerous fiction in practice. At very high duty cycles, the converter spends almost all of its time charging the inductor and almost none delivering to the output. Parasitic resistance in the inductor and switch becomes a dominant loss mechanism, and the actual $V_{out}$ saturates well below the theoretical asymptote. Reliable boost designs stay below $D = 0.85$ to $0.9$. Critically, the boost converter's input current is continuous (the inductor is in series with $V_{in}$) but its output current is pulsed—charge is only delivered to the output during the off time—which places a heavier burden on the output capacitor and means the boost topology is significantly more susceptible to output voltage ripple than the buck.

### The Buck-Boost Converter

The inverting buck-boost places the inductor between the switch and the diode such that both energy storage phases share the same reactive element, producing an output voltage of opposite polarity to the input. Its conversion ratio is:

$$M_{buck\text{-}boost} = -\frac{D}{1-D}$$

The magnitude can be greater than or less than the input voltage depending on whether $D$ is above or below 0.5, making this topology truly universal among the non-isolated family. The polarity inversion is a frequent inconvenience—when a system needs a negative rail (op-amp supplies, ADC references) it is an advantage, but generating a positive output requires either a different topology or a Ćuk or SEPIC configuration. The Ćuk converter uses two capacitors and two inductors and achieves non-inverting buck-boost behavior with continuous currents at both input and output, at the cost of doubled component count. The SEPIC (Single-Ended Primary Inductance Converter) achieves the same non-inverting ratio with a coupled inductor variant that is widely favored in battery-powered designs.

### Isolated Topologies: Flyback, Forward, Push-Pull, and Full-Bridge

Non-isolated converters directly connect the input and output ground references, which is acceptable in many systems but unacceptable wherever safety isolation is required (mains-connected supplies, medical devices) or where multiple independent output rails with separate references must be generated. Isolated topologies introduce a transformer, which both provides galvanic isolation and allows the turns ratio $n = N_1/N_2$ to contribute an additional degree of freedom in the voltage conversion ratio.

**The flyback converter** is the workhorse of low-to-medium power isolated designs (typically below 150 W). It is mechanically a buck-boost topology in which the inductor has been replaced by a coupled inductor—the transformer—where energy is stored in the gap of the magnetic core during the switch-on phase and delivered to the secondary during the switch-off phase. Because energy transfer and energy storage happen in separate half-cycles, the transformer does not behave like a conventional transformer; it functions as an isolated inductor pair. The voltage conversion ratio for the flyback in CCM is:

$$\frac{V_{out}}{V_{in}} = \frac{n_2}{n_1} \cdot \frac{D}{1-D}$$

where $n_1$ and $n_2$ are the primary and secondary turns respectively. The flyback's main limitation is that transformer leakage inductance—the portion of primary inductance not coupled to the secondary—generates a voltage spike on the primary switch at turn-off, as the leakage energy has nowhere to go except into the switch's drain-source capacitance. Without a snubber (an RCD clamp, or an active clamp circuit), this spike easily exceeds the MOSFET's voltage rating. A well-designed RCD snubber clamps the spike to a safe level but dissipates the leakage energy as heat, slightly degrading efficiency. Active-clamp flyback topologies recycle this leakage energy into the circuit, recovering 3–5% efficiency in demanding applications.

**The forward converter** is a single-switch topology in which energy is transferred from primary to secondary while the switch conducts—like a conventional transformer. This eliminates the leakage energy problem of the flyback but introduces a new one: the transformer core must be reset each cycle, returning its flux to its starting point to avoid progressive saturation. A tertiary reset winding, an active reset circuit, or a two-switch topology accomplishes this. The forward converter is preferred over the flyback for power levels above ~150 W because its transformer operates as a true transformer (lower peak currents for the same average power), and it naturally lends itself to synchronous rectification on the secondary side.

**Push-pull and full-bridge topologies** are designed for high-power converters (200 W to multiple kilowatts) where a single-switch primary becomes a bottleneck. In a push-pull converter, two switches alternately drive the two ends of a center-tapped primary winding, allowing the transformer core to be driven in both directions through its B-H curve. This doubles the core utilization compared to a single-switch topology. The full-bridge places four switches in an H-bridge configuration across the transformer primary, alternating the polarity of the applied primary voltage. Full-bridge converters dominate in telecom rectifiers, server power supplies, and high-power industrial converters because the switch voltage stress is clamped to $V_{in}$ (each switch only sees the input rail, not twice the input voltage as in a push-pull), and the transformer's full winding is active throughout each power stroke.

The topology comparison below summarizes the key design parameters for a practitioner selecting among these configurations:

| Topology | Power Range | Isolation | Switch Stress | Complexity |
|---|---|---|---|---|
| Buck | 1 W – 1 kW | No | $V_{in}$ | Low |
| Boost | 1 W – 500 W | No | $V_{out}$ | Low |
| Buck-Boost | 1 W – 150 W | No | $V_{in} + V_{out}$ | Low |
| Flyback | 5 W – 150 W | Yes | $V_{in} + nV_{out}$ | Medium |
| Forward | 50 W – 500 W | Yes | $2V_{in}$ (single sw.) | Medium |
| Push-Pull | 100 W – 1 kW | Yes | $2V_{in}$ | Medium-High |
| Full-Bridge | 500 W – 10 kW | Yes | $V_{in}$ | High |

### Inductor and Capacitor Design

Inductor design for switching converters is an exercise in simultaneously satisfying magnetic saturation limits, winding resistance, core loss, and physical size constraints. The inductor must handle the peak current $I_{pk} = I_{out} + \Delta I_L / 2$ without saturating its core, because saturation causes inductance to collapse, the current slope $dI/dt = V/L$ to spike dramatically, and potentially destroys the switch in a few hundred nanoseconds. Core material selection follows the switching frequency: ferrite (Mn-Zn or Ni-Zn) dominates above 100 kHz because its high resistivity suppresses eddy current losses; powdered iron and sendust materials are viable at lower frequencies. The area product method ($A_p = A_c \cdot W_A$, the product of core cross-section area and window area) provides a first-order sizing approach: for a given inductance $L$, peak current $I_{pk}$, and allowable flux density $B_{max}$ (typically 0.2–0.3 T for ferrite at 300 kHz), the required core volume scales directly.

Output capacitor selection demands attention to both capacitance value and ESR. The minimum capacitance to hold voltage ripple below a target $\Delta V_{cap}$ from the charge perspective is:

$$C_{out} \geq \frac{\Delta I_L}{8 f_s \Delta V_{cap}}$$

For the 500 kHz buck example with 0.9 A ripple and 10 mV capacitive ripple target: $C_{out} \geq 0.9 / (8 \times 500000 \times 0.01) = 22.5~\mu F$. A pair of 22 µF X5R ceramic capacitors in parallel (ESR $\approx 2$ mΩ each) comfortably meets both the capacitance and ESR requirements. Electrolytic capacitors carry substantially higher ESR (10–100 mΩ range) and become the dominant ripple source, but they offer much higher capacitance per unit volume when large bulk storage is needed during load transients.

### Signal Flow and Switching Waveforms

The following diagram captures the essential waveform sequence in a CCM buck converter across one switching period, correlating switch state with inductor voltage and current:

```
Gate Drive  ___________           ___________
(Q1)       |           |         |           |
           |  t_on     |  t_off  |           |
___________             _________             ___

V_L         (Vin - Vout)         (-Vout)
           +___________+        +___________+
           |           |        |           |
-----------+           +--------+           +---

I_L                  /\                  /\
                    /  \                /  \
I_avg   ----------/----\--------------/----\----
                 /      \            /      \
________________/        \__________/        \__

           |<---  T_s  --->|
```

The inductor current's triangular ripple sits atop the DC load current. Probe the switching node (the junction of Q1 drain, D1 anode, and L1 input) with a 10× passive probe to observe the rectangular waveform whose duty cycle the control IC is regulating. Use a current probe around the inductor to verify the ripple magnitude matches the design equation and to catch the onset of DCM—visible as the current waveform's lower envelope touching zero before the next gate pulse.

---

## 3. High-Performance Optimization & Failure Modes

### Gate Drive Optimization and Switching Loss

Switching loss is proportional to both switching frequency and the product of switch rise and fall times, which are set by the gate charge $Q_g$ of the MOSFET and the gate drive current capability. The energy dissipated per transition is approximately $E_{sw} \approx \frac{1}{2} V_{DS} \cdot I_D \cdot (t_r + t_f)$, and total switching loss per second scales as $P_{sw} = E_{sw} \cdot f_s$. A gate driver with 2 A source/sink capability charging a MOSFET with 10 nC gate charge produces a gate voltage slew that completes the transition in roughly 5 ns, resulting in manageable switching losses at 500 kHz. Halving the gate resistance cuts transition time and switching loss but increases the $dV/dt$ of the switching node, coupling more noise through parasitic capacitances into the control circuitry. Gate resistor selection is therefore a deliberate trade-off between EMI and efficiency.

Dead time—the brief interval between turning one switch off and its complementary switch on in a synchronous buck—is critical to prevent shoot-through, where both high-side and low-side MOSFETs conduct simultaneously and form a direct short across the input rail. The energy dumped in a shoot-through event is $\frac{1}{2} C_{decoupling} V_{in}^2$ plus whatever the input capacitor and inductance of the supply rail will deliver before the overcurrent protection responds, which can be enough to destroy both MOSFETs in microseconds. Modern synchronous buck controllers implement adaptive dead-time control, monitoring the body diode voltage of the low-side FET and triggering the high-side gate only after the diode voltage reverses, minimizing the dead-time interval while guaranteeing no overlap.

### Transformer Saturation in Isolated Topologies

Volt-second imbalance is the leading cause of transformer saturation in push-pull and full-bridge converters. If the two drive phases are not perfectly symmetric—even a 10 ns asymmetry in switch timing, or a slight difference in on-state resistance between switches—a net DC flux builds in the transformer core each cycle. Because the incremental permeability of a ferrite core drops sharply near saturation, the primary current spikes as the core saturates, stressing the switches and generating radiated EMI. Current-mode control is the preferred solution: by sensing primary peak current and using it to terminate each switch cycle, the controller naturally balances the flux each half-cycle. Flux-walking in voltage-mode-controlled push-pull converters is typically managed with a small air gap in the core (at the cost of increased magnetizing current) or a DC blocking capacitor in series with the primary.

### Compensation and Loop Stability

A DC-DC converter's control loop must regulate the output voltage against load and line disturbances while maintaining stability with adequate phase margin. The power stage of a CCM buck converter presents a second-order LC filter transfer function with a double pole at the resonant frequency $f_0 = 1/(2\pi\sqrt{LC})$ and a right-half-plane (RHP) zero is absent (unlike the boost and buck-boost, whose duty-cycle-to-output transfer functions carry an RHP zero that fundamentally limits achievable closed-loop bandwidth). For a 5.6 µH / 47 µF output filter, $f_0 = 1/(2\pi\sqrt{5.6\mu \times 47\mu}) \approx 9.8$ kHz. The phase contributed by this double pole passes through −180° near resonance, requiring a Type-III compensator or a PID with two zeros and two additional poles to restore adequate phase margin (typically 45°–60°) at the desired crossover frequency of $f_c \approx f_s/10$.

For boost and buck-boost converters, the RHP zero is unavoidable and limits the control loop bandwidth to roughly one-third to one-fifth of the RHP zero frequency: $f_{RHP} = (1-D)^2 R_{load} / (2\pi L)$. Attempting to close the loop faster than this limit causes the phase margin to collapse and the converter to exhibit a low-frequency oscillation that looks, on a scope, like a slow modulation of the output voltage at frequencies well below the switching frequency. The correct response is to reduce the crossover frequency of the compensator, not to add more gain.

### Failure Mode Analysis

**Inductor saturation** presents as an instantaneous, destructive spike in switch current during normal operation under load. It is diagnosable by reducing load until the current spike disappears, confirming the inductor's saturation current rating is insufficient for the peak current at full load. The fix is a higher-current-rated inductor, a larger core with more turns, or reducing $\Delta I_L$ by increasing L or $f_s$.

**Capacitor ESR degradation** is an aging failure that slowly worsens output voltage ripple over months or years, particularly in electrolytic capacitors operating above 60°C. It is detectable by measuring ripple voltage with an oscilloscope AC-coupled to the output rail. As ESR rises, the ripple waveform shifts from the rounded capacitive shape toward a spiked waveform that tracks the inductor current transitions. Replacing electrolytics with low-ESR polymer or X7R/X5R ceramic capacitors in new designs eliminates this failure mode entirely.

**Drain voltage overshoot** in flyback converters, beyond the RCD clamp level, results from lead inductance between the MOSFET drain and the snubber clamp circuit. Even 10 nH of PCB trace inductance, combined with the rapid $dI/dt$ of MOSFET turn-off, adds tens of volts to the peak drain voltage. The layout fix is to place the snubber components within 5 mm of the MOSFET drain pad, with wide, low-inductance copper pours rather than routed traces.

**Thermal runaway in synchronous rectifiers** can occur when the low-side synchronous MOSFET's body diode conducts during the dead time interval at light load, dropping 0.6–0.8 V across the diode and dissipating power proportional to the dead-time fraction. At very light loads where body-diode conduction becomes the dominant loss, the converter may paradoxically become less efficient as load decreases. Burst-mode or pulse-skipping control schemes address this by switching off the converter entirely for multiple cycles during light-load operation, maintaining efficiency above 80% even at load currents below 1% of rated full load.

### Practical Bench Validation Workflow

After assembling a new converter design, the following sequence catches the most critical failure modes before connecting the converter to a live load. First, power the converter through a bench supply set to current-limit at 20% of the expected full-load input current, and verify that startup behavior is monotonic—no burst oscillation on the output, no thermal hot spots on the switch within the first 30 seconds of operation at no-load. Second, attach a resistive load at 25%, 50%, 75%, and 100% of rated output power, measuring efficiency at each point with a precision power analyzer (Yokogawa WT310 or equivalent). Efficiency should be monotonically maximized in the 50–75% load range for a CCM design. Third, connect a current-mode electronic load configured for a 50% step between 25% and 75% of rated current with a 1 µs transition edge, and capture the output voltage transient response on a 500 MHz bandwidth oscilloscope with a low-inductance probing point directly across the output capacitors. The peak deviation and recovery time reveal the loop bandwidth and phase margin more directly than any Bode plot from simulation. Finally, run the converter at full load in a thermal chamber at the maximum rated ambient temperature, measuring all switch and magnetics temperatures with a thermocouple or IR camera, and verifying that junction temperatures remain at least 25°C below their rated maximums with the worst-case airflow conditions applied.
