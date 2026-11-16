# Lesson 4: Signal Integrity Principles in Power Distribution Networks

## 1. First-Principles Intuition & Invariants

The silent killer of high-speed digital systems lives not in logic gates, but in the copper beneath them. Signal integrity failures originate from two fundamental physical realities that every PCB designer must internalize: every conductor carrying current possesses inductance, and every potential difference across conductors creates capacitance. These parasitic elements transform what appears on a schematic as an ideal voltage supply into a complex electromagnetic landscape where transient currents, reflections, and ground bounce can corrupt signals faster than any logic error in firmware.

When a microprocessor's output driver switches from low to high, it does not instantaneously charge a load to the rail voltage. Instead, the driver must source current through the finite inductance of bonding wires, package leads, PCB traces, and via arrays. This series inductance creates a voltage drop according to Faraday's law: $V_L = L \frac{di}{dt}$. In modern processors drawing tens of amperes with slew rates measured in nanoseconds, this inductance can easily drop 500 millivolts or more across a single signal line—enough to violate noise margins and trigger false logic transitions. Worse, this same inductance stores energy in its magnetic field, and when the switching transient ends, this energy must dissipate somewhere, creating reflections and ringing that persist for multiple clock periods.

The power distribution network (PDN) exists to solve this problem, but only if designed with signal integrity as its primary objective rather than an afterthought. A PDN is not merely a collection of capacitors and power planes; it is a carefully engineered impedance network that must present a low, frequency-dependent impedance across the entire spectrum of switching transients your circuits will generate. The target impedance methodology—the discipline of calculating and achieving a maximum impedance floor across all frequencies—transforms PDN design from art into a reproducible engineering discipline.

The challenge lies in the frequency dependence of real circuit elements. At DC and very low frequencies, the dominant impedance of a PDN comes from the equivalent series resistance (ESR) of capacitors and the resistance of power planes. At intermediate frequencies (tens of megahertz to hundreds of megahertz), the equivalent series inductance (ESL) of capacitors and trace inductances dominates. At very high frequencies (gigahertz range), the plane-to-plane capacitance and via inductances control the impedance. No single capacitor or design technique spans all these frequency regimes effectively, which is why the most robust PDNs employ a hierarchical strategy: bulk capacitors for low-frequency supply regulation, intermediate-value ceramics for mid-frequency transient response, and tiny high-frequency bypass capacitors positioned as close as possible to the load.

Signal integrity in modern digital systems is fundamentally a problem of controlling electromagnetic transients. Every time a driver switches, it injects charge into the power and ground distribution networks, creating voltage fluctuations that all other circuits share. This is simultaneous switching noise (SSN): when thousands of output buffers switch synchronously—which happens regularly in synchronous digital logic—the aggregate current through the inductance of shared power distribution creates a voltage spike that momentarily starves other circuits of supply voltage. If this voltage drop exceeds the noise margin of downstream receivers, logical errors propagate. Furthermore, the return current path for these switching transients creates ground bounce—a rise in the local ground potential relative to the system reference—which directly degrades receiver noise margins by reducing the low-level voltage threshold.

Transmission line theory governs how signals propagate along PCB traces at high speeds. When a signal edge rises fast enough that the wavelength becomes comparable to trace length, the trace must be treated not as a lumped circuit element but as a distributed transmission line with characteristic impedance $Z_0 = \sqrt{L'/C'}$, where $L'$ and $C'$ are the per-unit-length inductance and capacitance of the trace. If a driver with source impedance $Z_s$ drives a load with input impedance $Z_L$ across a transmission line of characteristic impedance $Z_0$, the signal does not smoothly transition to its final value. Instead, a wave front propagates along the line at velocity $v = 1/\sqrt{L'C'}$, and when this wave reaches the discontinuity at the load, a reflection occurs. The reflection coefficient is $\Gamma = (Z_L - Z_0)/(Z_L + Z_0)$. If the load impedance matches the line impedance perfectly ($Z_L = Z_0$), no reflection occurs and the signal settles cleanly. If there is a mismatch, a reflected wave propagates backward toward the source, arrives at the source impedance, reflects again, and creates ringing that persists until dissipated by resistance in the circuit. This is why controlled impedance is not a luxury for high-speed designs—it is an absolute necessity.

The physical mechanics of current distribution create another critical constraint: current must flow in closed loops. For every path a signal takes from driver output to receiver input, return current must flow somewhere, and the inductance of that return path determines the voltage transient induced at the receiving end. If return current has only a long, winding path through substrate to some distant ground plane, the inductance of that return loop is enormous. If the signal trace is immediately adjacent to a ground plane with numerous vias connecting it to the trace's return path, the inductance is minimized. This principle—minimizing the area of current loops—is perhaps the most powerful tool in the signal integrity engineer's arsenal. A well-routed PCB with many vias connecting signal traces to their return planes exhibits far better signal integrity than a poorly routed board with fewer vias, even if both use the same capacitors.

Ground bounce and power supply noise are coupled phenomena. When output drivers source current, this current must flow through the power distribution network to reach the driver's output pin, and the inductance of this path creates a voltage drop. Simultaneously, the return current from the driver must flow through ground connections, and the inductance of the ground path creates a rise in the local ground potential—ground bounce. From the perspective of a receiver powered by the same supply, both effects conspire to reduce the effective voltage swing at the receiver input: the high level appears lower (because the supply sags), and the low level appears higher (because ground bounces up). This is why a 3.3 V logic system can experience receiver inputs that appear to be only 2.8 V or lower during heavy switching, well below the guaranteed 2.0 V high-level input threshold.

EMI and EMC considerations flow directly from signal integrity principles. A PCB that exhibits poor signal integrity—ringing, reflections, and ground bounce—radiates electromagnetic energy at the frequencies corresponding to these transients. The fastest edges in your design determine the highest frequency content in the radiated spectrum. A 1 nanosecond rising edge contains significant frequency content extending to at least 500 MHz and beyond. If this edge exhibits ringing and overshoot due to transmission line reflections, the spectral content becomes even richer, potentially violating FCC, ISED, or CE EMC limits. Conversely, a well-designed PDN with minimal noise inherently reduces radiated emissions because there is simply less electrical activity to radiate.

## 2. Core Architecture & Mechanics

### Transmission Line Theory and Controlled Impedance Routing

A microstrip transmission line consists of a signal trace routed above a ground plane, with dielectric material (typically FR-4 with permittivity $\varepsilon_r \approx 4.2$) between them. The characteristic impedance of this geometry is given by the microstrip equation:

$$Z_0 = \frac{120}{\sqrt{\varepsilon_r}} \ln\left(\frac{5.98h}{0.8w}\right) \text{ ohms}$$

where $h$ is the distance from trace to ground plane and $w$ is the trace width, both in the same units. For a typical four-layer PCB with 0.5 mm between signal layer and ground plane, a 50 ohm characteristic impedance requires a trace width of approximately 0.20 mm (8 mils). For 75 ohm impedance—common in video and differential signaling—the trace width increases to roughly 0.30 mm (12 mils).

The propagation velocity on a microstrip line is:

$$v = \frac{c}{\sqrt{\varepsilon_r}}$$

where $c$ is the speed of light in vacuum. For FR-4 with $\varepsilon_r = 4.2$, this yields $v \approx 146 \text{ mm/ns}$ or about 0.65 times the speed of light. On a standard 60-mil-thick PCB, a signal traveling 300 mm takes roughly 2 nanoseconds. This is significant: if your digital system operates at 1 GHz with 1 nanosecond clock periods, a 300 mm trace delay is two full clock periods—meaningful for timing closure.

A signal propagating along a uniform transmission line experiences no reflections if the load impedance matches the line impedance exactly. However, the instant the source begins driving, a voltage wave propagates forward at velocity $v$, and when it reaches the load, a reflection occurs. The reflection coefficient at the load is:

$$\Gamma_L = \frac{Z_L - Z_0}{Z_L + Z_0}$$

For an open circuit ($Z_L \to \infty$), $\Gamma_L = 1$ and the entire incident wave reflects back in phase with itself, causing the voltage to double at the load. For a short circuit ($Z_L = 0$), $\Gamma_L = -1$ and the reflected wave cancels the incident wave, creating a voltage null at the load. For matched impedance ($Z_L = Z_0$), $\Gamma_L = 0$ and no reflection occurs—the signal settles cleanly to its final value after the propagation delay.

The reflection propagates backward toward the source, where it encounters the source impedance. If the source has non-zero series resistance (as real CMOS drivers do), some energy dissipates in this resistance and the reflection weakens. However, without proper termination strategy, multiple reflections occur, creating ringing that settles only after the electromagnetic energy dissipates as heat.

Series termination—placing a resistor in series with the driver output—changes the source impedance seen by the incident wave traveling forward from the driver toward the load. If the driver has negligible source resistance and we place a resistor $R_s$ in series with the output, the source impedance becomes $Z_s = R_s$. The reflected wave traveling backward sees this $R_s$ combined with the driver's output impedance. In ideal CMOS drivers, the output impedance is approximately the on-resistance of the output transistor, typically 20–50 ohms for modern logic. Choosing $R_s$ such that $Z_s + Z_{driver} \approx Z_0$ means that when the reflected wave returns to the source, it sees a matched termination and dissipates rather than reflecting again. This eliminates most ringing within one or two round-trip delays. Series termination is simple, low-cost, and requires only a small resistor, making it the most common termination strategy in practical PCB design.

Parallel termination places a resistor connected between the signal line and either ground or power, creating a resistive divider. If the termination resistor $R_t$ is connected to ground, the voltage divider formed by the line impedance $Z_0$ and $R_t$ must satisfy:

$$\frac{R_t}{R_t + Z_0} \cdot V_{supply} = V_{threshold}$$

For a 50 ohm transmission line terminating to ground through a resistor, a 100 ohm parallel terminator creates a voltage divider of 1:3, reducing the signal swing to one-third the supply voltage. This increases power consumption (steady-state current flows through $R_t$ whenever the line is high) but eliminates reflections more aggressively than series termination. Parallel termination is preferred in high-speed buses like LVDS or when absolute minimum ringing is required, despite the higher power cost.

AC termination combines series and parallel resistors to capture the benefits of both: the series resistor ($R_s$) in the driver's output path controls reflections from the incident wave, while a parallel resistor ($R_p$) connected via a series capacitor ($C_s$) to the receiver provides DC-level flexibility without steady-state current draw. The capacitor blocks DC, so the steady-state voltage divider is determined by the receiver input impedance (typically several kilohms), not by $R_p$. At high frequencies, the capacitive reactance becomes negligible, and the parallel resistor dominates, providing reflectance control. AC termination is common in DDR memory interfaces, where power consumption is critical.

### Power Distribution Network Architecture and Target Impedance

A modern PDN must span at least four orders of magnitude in frequency to be effective. At 1 Hz (DC), the impedance is primarily resistive from power plane sheet resistance. At 10 kHz, bulk capacitors dominate. At 100 MHz, intermediate ceramics control impedance. At 1 GHz and beyond, high-frequency decoupling capacitors and plane-to-plane capacitance take over. Each frequency band requires different circuit elements and physical placement strategies.

The impedance of a capacitor as a function of frequency is:

$$Z_C(f) = \sqrt{R_{ESR}^2 + \left(\frac{1}{2\pi f C} - 2\pi f L_{ESL}\right)^2}$$

At very low frequencies (well below the self-resonant frequency $f_0 = 1/(2\pi\sqrt{LC})$), the impedance is dominated by $1/(2\pi f C)$ and drops with increasing frequency. At the self-resonant frequency, the inductive and capacitive reactances cancel, leaving only the ESR, which is the minimum impedance. Above resonance, the ESL dominates and impedance rises linearly with frequency.

A typical bulk capacitor (10 µF ceramic, 1206 case size) has ESL around 500 pH and ESR around 20 mΩ. Its self-resonant frequency is roughly:

$$f_0 = \frac{1}{2\pi\sqrt{500 \times 10^{-12} \times 10 \times 10^{-6}}} \approx 225 \text{ kHz}$$

This capacitor provides excellent impedance control from DC up to several hundred kilohertz, but above its resonance frequency, its impedance rises and it becomes ineffective.

To extend impedance control to megahertz and gigahertz frequencies, intermediate ceramics (0.1 µF, 0603 or 0402) with smaller ESL (typically 100–200 pH) and smaller ESR (5–10 mΩ) have higher resonant frequencies, around 10–20 MHz. These capacitors bridge the gap between bulk capacitors and the higher-frequency regime. Finally, very small high-frequency capacitors (10 pF to 100 pF, often 0201 case size) have ESL below 50 pH and resonate in the gigahertz range, providing impedance control where the intermediate ceramics fail.

The target impedance of a PDN is typically set by the maximum current transient $\Delta I$ and the tolerable voltage drop $\Delta V$:

$$Z_{target} = \frac{\Delta V}{\Delta I}$$

For a processor dissipating 50 W at 3.3 V, with a maximum transient of 15 A occurring over 100 ps (a di/dt of 150 A/ns), and a tolerable voltage drop of 150 mV (roughly 5% of the 3.3 V supply), the target impedance is:

$$Z_{target} = \frac{150 \text{ mV}}{15 \text{ A}} = 10 \text{ m}\Omega$$

This is an extraordinarily low impedance, achievable only through careful hierarchical design of bulk, intermediate, and high-frequency capacitors, combined with optimized power plane geometry.

The PDN impedance curve is plotted on a logarithmic scale as impedance (y-axis in milliohms) versus frequency (x-axis in Hz or MHz). Each capacitor contributes a resonance peak; the design goal is to ensure that the impedance never exceeds the target across the entire frequency spectrum from DC to the highest switching frequency in the system. Typically, switching transients in modern logic occur at the clock frequency and its harmonics, potentially reaching 10 GHz or higher in advanced processors.

### Decoupling Capacitor Placement and Via Array Optimization

Physical placement of capacitors is as critical as their electrical characteristics. A 10 µF capacitor placed 50 mm away from the die is useless because the inductance of the PCB trace and vias connecting the capacitor to the power pin dominates the capacitor's own ESL, rendering the capacitor ineffective. The trace inductance scales roughly as 1 nH per millimeter of trace length, so a 50 mm trace adds 50 nH of inductance—five orders of magnitude larger than the capacitor's ESL.

Modern high-speed processors employ BGA (Ball Grid Array) packages with hundreds or thousands of power and ground balls distributed across the package substrate. Each power ball must be connected to capacitors and power planes with minimal inductance. This requires multiple vias—typically 4 to 16 vias per capacitor pad, depending on current levels—placed in a pattern that minimizes loop area. The pattern that minimizes loop area for a parallel connection is a cross or plus shape: power vias form a tight cluster above the capacitor pad, while ground return vias form another tight cluster adjacent to the power vias. This arrangement minimizes the area enclosed by the current path and dramatically reduces the loop inductance.

The rule of thumb for via inductance is approximately 1 nH per via, through-hole diameter and PCB thickness accounted for. A 0.3 mm diameter via in a 1.6 mm thick PCB exhibits roughly 0.7–1.0 nH of inductance. An array of 8 vias in parallel exhibits 1/8 of the inductance of a single via, yielding 0.1–0.125 nH total. Placed directly beneath a capacitor pad on a 0.5 mm grid, the loop area is minimized, and the connection inductance is determined entirely by the via array.

The placement hierarchy for bypass capacitors should follow this pattern: First, position the largest value (bulk) capacitors at the module level—perhaps 10–20 of them distributed around the BGA package, placed with 4–8 vias each into both power and ground planes. These capacitors are responsible for stabilizing the supply against low-frequency load variations and providing bulk charge storage for transient currents. Second, place intermediate-value ceramics (0.1 µF, 0.01 µF) directly adjacent to or beneath the package, using 2–4 vias each. These capacitors respond to mid-frequency transients and bridge the frequency gap between bulk capacitors and plane capacitance. Third, place high-frequency capacitors (10–100 pF) underneath the BGA package if possible, with minimal trace routing between capacitor pad and package ball. In many designs, high-frequency capacitors are placed on the back side of the PCB, directly opposite the processor's power and ground balls, allowing vias to connect them with minimal trace length.

The power and ground planes themselves act as a distributed capacitor, with the dielectric between planes serving as the dielectric material. A 0.5 mm gap between power and ground planes in a 600 mm² area of a typical FR-4 PCB (with $\varepsilon_r = 4.2$) creates a plane capacitance of roughly:

$$C = \varepsilon_r \cdot \frac{A}{d} = 4.2 \times \frac{600 \times 10^{-6}}{0.5 \times 10^{-3}} \approx 5 \text{ nF}$$

While 5 nF is small compared to a single 10 µF bulk capacitor, the plane capacitance is distributed uniformly across the entire board and exhibits extremely low impedance at high frequencies because it has minimal ESL. The plane-to-plane capacitance resonates at frequencies determined by the dimensions of the plane structure; for a 600 mm² area, resonant modes occur in the gigahertz range. This makes plane capacitance invaluable for controlling impedance at the highest frequencies, which is why modern high-speed boards employ planes as close together as possible—sometimes 0.3 mm or less.

### Ground Bounce and Simultaneous Switching Noise Mechanisms

When output buffers switch simultaneously, they draw current from the power distribution network in a sharp, transient pulse. The aggregate current from many buffers creates a voltage drop across the inductance of the power delivery path:

$$V_{drop} = L_{PDN} \frac{dI}{dt}$$

For example, if 100 output buffers, each capable of sourcing 50 mA, switch within a 100 ps window, the di/dt is approximately $(100 \times 50 \text{ mA}) / 100 \text{ ps} = 50 \text{ A/ns}$. If the PDN inductance is 500 pH, the voltage drop is:

$$V_{drop} = 500 \times 10^{-12} \times 50 \times 10^9 = 25 \text{ mV}$$

This happens to all circuits sharing the power distribution network, so every gate in the design experiences a temporary 25 mV sag in supply voltage. While this seems small, it directly reduces the noise margin at receiver inputs. A 3.3 V logic system with 25 mV supply sag experiences an effective supply of 3.275 V instead of 3.3 V, reducing the voltage swing available for signaling and potentially violating noise margins on long, weakly driven signals.

Ground bounce is the mirror image of this phenomenon. Current flowing through output drivers must return to ground through the ground distribution network. The inductance of this return path causes the local ground potential to rise temporarily:

$$V_{ground\_bounce} = L_{ground} \frac{dI_{return}}{dt}$$

From the perspective of a receiver powered by the saging supply and receiving signals referenced to the bouncing ground, both effects conspire. A logic high at the receiver sees reduced supply voltage (from the sag) and elevated ground reference (from bounce), compressing the effective swing. A logic low at the receiver sees the same trends. The combined effect can reduce available noise margin by 50 mV or more in poorly designed systems.

Simultaneously switching noise (SSN) is particularly acute in synchronous digital systems where output transitions are aligned to clock edges. Microprocessors, memory interfaces (DDR, GDDR), and high-speed serial buses all exhibit periodic, synchronized output transitions. Each clock cycle triggers a burst of switching activity, injecting a sharp current pulse into the power distribution network. If the PDN inductance is not well-controlled, this pulse creates a voltage transient that couples into signal lines through the shared power and ground planes. This coupling is capacitive (through the dielectric) and inductive (through loops). Signals switching during the period of maximum supply sag or ground bounce experience distorted rising and falling edges, slower transitions, and potential false triggering at logic threshold levels.

### EMI and Shielding Strategies

The radiated emissions from a poorly designed PCB originate from three primary sources: the switching transients in digital circuits, the return current loops that close on ground planes, and differential loop currents in high-speed differential pairs. Each of these sources radiates electromagnetic energy proportional to its frequency content, current magnitude, and loop area.

A single, well-controlled signal transition radiates minimal energy because the rising and falling edges are smooth and the current path is controlled. However, if that same signal exhibits overshoot, ringing, or reflections due to transmission line effects, the spectral content becomes very rich, extending to higher frequencies and exhibiting greater amplitude. An overshoot spike that rises to 20% beyond the nominal high level and rings for several nanoseconds contains energy in frequency components well beyond the fundamental switching frequency.

Return current paths that loop over large areas radiate according to the magnetic dipole radiation formula. For a loop of area $A$ carrying current $I(t)$, the radiated power is proportional to $(dI/dt)^2 \cdot A^2 \cdot f^4$, where $f$ is the frequency. This $f^4$ dependence means that current loops with areas measured in square centimeters can radiate significant energy in the gigahertz range. Conversely, minimizing loop area to square millimeters reduces radiated emissions by many orders of magnitude.

Shielding against radiated emissions or reducing emissions from a design typically involves one or more of these strategies:

First, control impedance and minimize ringing through proper termination and impedance matching.

Second, reduce loop areas by ensuring return currents flow directly beneath their signal traces through continuous reference planes. Any gap or slot in the reference plane forces current to detour, enlarging the loop. A 10 mm gap requiring a 15 mm detour can increase radiated emissions by 20–30 dB at frequencies above 500 MHz. Stitching vias placed adjacent to high-speed signal vias ensure return currents transition cleanly between layers without forming large loops.

Third, implement strategic shielding and filtering at board interfaces where emissions escape. Guard traces grounded at both ends can contain radiated energy from critical signal traces. Metal enclosures act as waveguide-below-cutoff barriers at frequencies where the longest enclosure dimension is less than λ/2. Ferrite beads and common-mode chokes suppress differential-mode and common-mode currents on cables before they radiate. Finally, spread-spectrum clocking techniques distribute switching energy across a wider frequency band, reducing peak emissions by 10–15 dB without altering the fundamental circuit behavior. The cumulative effect of these strategies—controlled impedance, minimized loop area, continuous return paths, and selective filtering—transforms a radiating PCB into a magnetically and electrically quiet system that meets stringent EMC standards while maintaining signal integrity across all operating conditions.

## Summary & Verification Matrix

| **Governing Invariant** | **Core Mechanism** | **Critical Threshold** | **Diagnostic Signature** | **Mitigation Strategy** |
|-------------------------|-------------------|------------------------|--------------------------|-------------------------|
| PDN impedance < target Z across frequency | Capacitor network with distributed ESL/ESR forms parallel resonant tank | |Z| must remain below target (e.g., 1 mΩ–10 mΩ) from DC to GHz | Impedance peaks at anti-resonances; valleys at self-resonance | Add capacitors to fill impedance nulls; use multiple decade values with low ESL |
| Return current follows path of least impedance | At high frequency, inductive reactance dominates; current flows beneath signal trace | Above ~10 MHz, inductance >> resistance | Enlarged loop area from reference gaps; EMI spikes in radiated emissions | Maintain continuous reference planes; place stitching vias adjacent to signal transitions |
| Decoupling effective within radius r ≈ c/(2πf) | Capacitor supplies charge only to loads within its effective radius due to propagation delay | Bulk caps cover low-f; ceramics cover high-f with spatial distribution | Voltage droop exceeds ripple budget; ringing on power rails | Distribute ceramic capacitors near each IC; ensure coverage overlap at target frequencies |
| Simultaneous switching noise ∝ LdI/dt | Package and plane inductance converts transient current into voltage noise | ΔV = L(dI/dt); typical threshold 5–10% of V_DD | Ground bounce on scope; timing errors; voltage sag during switching events | Reduce inductance with thick copper, wide planes, low-inductance vias; stagger switching edges |
| Radiated emissions ∝ (dI/dt)² · A² · f⁴ | Current loops act as magnetic dipoles; emission scales with loop area and frequency | Regulatory limits at 30 MHz–6 GHz (FCC/CISPR) | Narrow-band or broadband EMI peaks in radiated scan; fails compliance | Minimize loop area via return path control; use shielding, filtering, and spread-spectrum clocking |
| Power rail target impedance Z = ripple_budget / max_transient_current | Decoupling network must present impedance low enough to limit voltage excursion | If I_max = 5 A, ΔV_budget = 50 mV, then Z_target = 10 mΩ | Measured PDN impedance exceeds target; supply voltage ripple exceeds specification | Iteratively add capacitors and reduce parasitic inductance until Z(f) envelope stays below target across full bandwidth |
