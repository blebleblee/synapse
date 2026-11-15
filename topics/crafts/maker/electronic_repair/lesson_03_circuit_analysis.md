# Lesson 3: Circuit Topology, Signal Flow, Troubleshooting

## 1. First-Principles Intuition & Invariants

Every electronic repair begins with the same invisible enemy: the assumption that you already know where the problem is. A capacitor that looks bulged, a resistor that looks scorched, a trace that looks cracked — these are breadcrumbs, not conclusions. The discipline of systematic circuit troubleshooting is fundamentally about resisting the urge to replace the most suspicious component and instead building a methodical, evidence-driven picture of where energy stops behaving as the designer intended.

To do this well, you must first understand what a schematic actually represents. A schematic is not a map of physical geography — it is a map of *intent*. It captures the relationships between electrical nodes: the points in a circuit that share a common potential. Every wire, trace, and solder joint connecting two component pins without a component between them is, by definition, the same node. The schematic abstracts away the physical routing of copper and instead shows you the logical web of cause and effect. A voltage regulator's output node connects to the VCC rail of a microcontroller's power pin, and that same rail feeds pull-up resistors, decoupling capacitors, and sensor supply lines. When that node fails, the schematic tells you *exactly* what breaks simultaneously — and that cascade of failures is precisely how you triangulate a fault.

The foundational invariant of all circuit analysis is Kirchhoff's two laws, and understanding them physically rather than algebraically will transform your diagnostic instincts. Kirchhoff's Current Law (KCL) states that the sum of currents entering any node equals the sum leaving it — there is no current accumulation in a wire. Kirchhoff's Voltage Law (KVL) states that the sum of voltages around any closed loop is zero. These are not mathematical curiosities; they are the physical bedrock of fault isolation. If you measure a voltage drop across a trace that should have near-zero resistance, KVL tells you a current is flowing through an unexpected resistance — meaning either an unexpected load, a damaged trace, or a solder bridge is forcing energy to dissipate where it should not. If a node is starved of current despite adequate supply voltage, KCL tells you one of the branches feeding it has opened.

The practical upshot is this: a circuit that is not working is not broken randomly. It is broken *specifically*, and the break obeys these laws with perfect fidelity. Your job is to ask, at each node, whether the voltage and current present are consistent with what the schematic predicts given the components attached. When the answer is no, you have found the boundary of the fault. Work inward from that boundary, and the failed component will reveal itself.

There is a second invariant that experienced repair technicians internalize so deeply they stop consciously thinking about it: **every failure is either an open or a short, or a component whose behavior has drifted outside its specified range**. A resistor can fail open (infinite resistance), fail short (near-zero resistance), or drift to a value that is simply wrong. A capacitor can fail open (no capacitance), fail short (catastrophic, usually visible), or exhibit elevated equivalent series resistance (ESR) — a parasitic resistance that makes it look fine on a simple continuity check but causes it to fail under AC ripple conditions. An electrolytic capacitor with high ESR will pass a DMM capacitance check and still cause a voltage regulator to oscillate or a power supply to output excessive ripple. This is the category of failure that separates methodical practitioners from parts-changers: the component that measures *approximately* correct but is functionally dead.

Understanding **power distribution topology** is equally critical before you touch a probe to a board. Modern PCBs almost never distribute power as a single rail. A development board like an Arduino or a Raspberry Pi Zero will typically have a 5V USB input rail, a 3.3V LDO-regulated rail for the MCU core and I²C peripherals, and sometimes a separate analog supply (AVCC or AVDD) isolated from the digital switching noise. These rails are physically separated by ferrite beads, LC filters, or small series resistors precisely because high-frequency switching transients on the digital rail would corrupt ADC readings on the analog rail. When you are tracing a fault involving an ADC or analog sensor, you must check the analog supply rail independently — measuring 3.3V on the main digital rail tells you nothing about whether the AVDD domain has collapsed.

The concept of a **ground plane** deserves particular attention because it is the most underappreciated element in repair work. Ground is not a fixed reference in a physical circuit — it is a network of copper with real, measurable resistance and inductance. On a poorly designed or damaged board, different ground regions can sit at slightly different potentials due to high return currents through thin copper or damaged vias. When you measure a signal voltage, you are always measuring it relative to your probe's ground clip. If that clip is attached to a ground node that has drifted 200mV away from the ground node of the circuit you're measuring, your reading is 200mV wrong. Skilled repair technicians always measure ground-to-ground continuity across the board before committing to any other measurements, and when probing differential or sensitive analog signals, they keep their ground clip as close to the circuit under test as physically possible.

---

## 2. Core Architecture & Mechanics

### Reading a Schematic as a Directed Signal Graph

The most powerful shift in schematic literacy comes from stopping reading a schematic as a wiring diagram and starting to read it as a **directed graph of signal causality**. Each signal has a source (a GPIO pin, a voltage reference, an oscillator output, a sensor output stage) and one or more sinks (ADC inputs, gate drivers, comparator inputs, communication bus lines). Between source and sink, the signal may pass through conditioning stages — filters, level shifters, amplifiers, or isolation circuits. If you can mentally trace that directed path and identify where it enters and exits each conditioning stage, you can probe it node by node and determine exactly where it stops matching its specification.

Consider a typical I²C bus on a microcontroller board. The SDA and SCL lines are open-drain: the MCU and peripheral devices can pull the lines low but rely on pull-up resistors connected to VCC to restore them high. The topology looks like this:

```
VCC (3.3V)
   |
  4.7kΩ        4.7kΩ
   |               |
  SCL ─────────── SDA
   |               |
[MCU]         [Sensor]
[Peripheral 1]
[Peripheral 2]
```

If SDA is stuck low and you cannot communicate with any device on the bus, you have three candidate failure branches: the pull-up resistor has failed or is missing its supply voltage, the MCU's I²C peripheral is holding SDA low due to a clock-stretch lockup, or one of the peripheral devices has a shorted output stage. The schematic immediately tells you all three branches exist. Your first physical measurement is voltage at the top of the pull-up resistor — if VCC is not present there, the fault is upstream in power distribution. If VCC is present but SDA reads low, you use the **divide-and-isolate** method: physically disconnect the peripheral with the most probability of failure (or temporarily remove it from the board), and check whether SDA recovers. If it does, the fault is in that peripheral. If it does not, work toward the MCU.

This is the schematic-driven mindset in action. You are not guessing — you are reading the topology, enumerating the possible fault locations for the observed symptom, and eliminating branches with measurements.

### Signal Flow Through a Power Supply Stage

The power supply section of any board deserves a full architectural breakdown because power faults cascade into symptoms that look like component failures elsewhere. A linear regulator like the AMS1117-3.3, common on Arduino-class hardware, has an input pin, an output pin, and an adjust/ground pin. Its internal architecture is an error amplifier that compares a fraction of the output voltage against an internal 1.25V reference and drives a pass transistor to maintain regulation. The minimum input-to-output differential (dropout voltage) for the AMS1117 is approximately 1.0–1.3V at full load. If you're feeding it 3.6V from a LiPo cell that has partially discharged, and expecting 3.3V out, you are operating at the edge of its dropout specification and the output will sag.

The signal flow through the regulator stage can be represented as follows:

```
USB 5V / DC Jack
      |
   [Reverse
   Protection
     Diode]
      |
   VIN_RAW ──────────────────────────────► [5V Rail to headers, USB peripherals]
      |
  [AMS1117-3.3]
   IN ─► [Pass Transistor] ─► OUT ─────► [3.3V Rail]
              ▲                               |
         [Error Amp]                    [100nF + 10µF
              |                          Decoupling]
         [1.25V Ref]                          |
              |                             GND
           [ADJ/GND]
              |
             GND
```

The two decoupling capacitors at the output are not optional — they are part of the regulator's feedback stability network. Remove or fail them and the regulator will oscillate, producing a 3.3V rail with hundreds of millivolts of AC ripple riding on it. An oscilloscope with AC coupling and a 20MHz bandwidth limit will show this immediately as a sawtooth or sinusoidal ripple. A DMM will show approximately 3.3V and tell you nothing is wrong. This is the single most common reason a DMM-only diagnostic gives false confidence.

### The Systematic Isolation Protocol

Fault isolation follows a strict physical hierarchy, and working through it in order prevents the most common repair mistake: replacing a component that is itself the victim of a fault further upstream.

**Stage 1: Visual and Tactile Inspection.** Before any instrument touches the board, examine it under a magnifier at oblique lighting — a headlamp held low and to one side creates raking shadows that reveal lifted traces, cracked solder joints, and bulged capacitor tops that straight-on lighting misses. Run a finger (carefully, with power off) over ICs and power components immediately after a failed power cycle; a component that is significantly warmer than its neighbors is dissipating excess power. A MOSFET driver that is shorted drain-to-source will get hot even with no load because it presents a low-resistance path to ground at all times.

**Stage 2: Confirm Ground Continuity.** Set your DMM to continuity mode and confirm that the ground reference pins of every major IC share continuity with the main ground bus. A single lifted via or cracked ground plane segment can float an entire section of circuitry while the rest of the board operates normally.

**Stage 3: Static Supply Rail Verification.** With power applied and no load connected beyond the board itself, measure each supply rail in sequence from the input forward. Document every measurement against the schematic's labeled voltages. A rail that reads low by more than 5% under light load indicates either a failed regulator or an excessive static current draw from that rail — verify by measuring the quiescent current with a DMM in series if the rail can be isolated.

**Stage 4: Signal-Level Probing.** Once all supply rails are confirmed correct, begin probing signal nodes. For digital logic, verify that logic-high and logic-low levels are within the VIH and VIL specifications for the relevant logic family. A 5V MCU GPIO driving a 3.3V peripheral directly (without level shifting) may appear to work but can cause intermittent latch-up under temperature or load variation. For analog signals, compare the measured DC bias point against the schematic's design intent — an op-amp input biased to a wrong voltage indicates a failed bias resistor or a leaky bypass capacitor.

**Stage 5: Dynamic Probing with Oscilloscope.** Static voltages are necessary but not sufficient for diagnosing many faults. An oscilloscope reveals the time-domain behavior: whether clock signals are present and at the correct frequency, whether communication buses show valid frame structures, and whether power rails have AC noise above the tolerance of the downstream ICs. For SPI and I²C buses, a logic analyzer (even a low-cost 24MHz clone based on the Cypress FX2 chip with PulseView/sigrok) will decode the actual transaction data and reveal whether the MCU is sending correct address bytes or whether the peripheral is ACKing or NACKing.

The standard probe topology for oscilloscope measurement on a PCB is worth stating explicitly: the probe tip goes to the signal node under test, the probe's ground clip goes to a ground point within 2–3 cm of the probe tip, and the oscilloscope's input coupling is set to DC unless you are specifically looking for AC ripple on a supply rail. Ground loops from long ground clip leads will inject 50/60 Hz noise into the measurement and cause the waveform to appear noisier than the circuit actually is.

---

## 3. High-Performance Optimization & Failure Modes

### ESR: The Invisible Capacitor Failure

Electrolytic capacitors fail in service primarily through two mechanisms: electrolyte evaporation (which raises ESR) and dielectric degradation under overvoltage. The first mechanism is insidious precisely because it is invisible to a DMM capacitance check. A 1000µF/16V electrolytic that has been operating at the top of its temperature rating for years might read 980µF on a capacitance meter and still have an ESR of 2–3 ohms instead of its nominal 0.1 ohm. At 100mA of ripple current, that ESR generates 200–300mV of AC voltage drop across the capacitor — which appears as ripple on the supply rail, which then corrupts ADC readings, causes reset ICs to trigger spuriously, and produces the kind of intermittent, temperature-dependent failure that makes technicians doubt their sanity.

The correct tool for capacitor health is a **dedicated ESR meter** or a bench LCR meter with ESR measurement capability. A simple, inexpensive option is the Atlas ESR70, which measures ESR in-circuit on capacitors that are not under power — this is a significant practical advantage, since desoldering every suspect capacitor for out-of-circuit measurement is prohibitively time-consuming. The general ESR threshold for concern is anything above 1 ohm for capacitors larger than 100µF, and proportionally higher for smaller values. When in doubt on an aging switching power supply board — particularly boards that have been in service for 10+ years or that show signs of elevated operating temperatures — replace the bulk electrolytics on the output rails as a preventive measure. The cost of four 1000µF Nichicon or Panasonic FM-series capacitors is trivial; the cost of a second diagnostic session because you left marginal caps in place is not.

### Thermal Intermittents and Solder Joint Failure

A substantial class of field failures that resist static diagnosis are **thermal intermittents**: the circuit works when cold, fails when warm, or vice versa. The cold-fail variant is usually caused by tin pest or cold solder joints that have cracked under thermal cycling — the joint expands enough when warm to restore contact. The warm-fail variant is more common and is usually caused by a marginal component (a transistor with elevated leakage current, a ceramic capacitor with strong negative TCC that loses capacitance at temperature) or a solder joint that is mechanically stressed and opens under thermal expansion.

The diagnostic tool for thermal intermittents is a **freeze spray** (1,1,1-trichloroethane-free electronics cooling spray) and a heat gun or hot air rework station. Apply freeze spray to a suspicious region while the circuit is powered and running in its failing state. If the fault clears when you cool a specific IC, that component or its solder joints are the thermal failure point. Apply hot air at 80–100°C to a region while the circuit is in its working state — if the fault appears when you heat a specific area, same conclusion. This divide-and-heat/cool approach can localize a thermal fault to within a 2 cm² area in under ten minutes.

Reflow of suspect solder joints with a temperature-controlled iron and fresh flux (no-clean flux pen or liquid flux in a syringe for SMD work) is the corrective action. The reflow temperature for eutectic SnPb solder is approximately 183°C liquidus, so iron tip temperature should be set to 320–350°C for SMD reflowing through a flux application. Lead-free SAC305 alloy has a liquidus of approximately 217°C and requires 350–380°C. The most common technician error is using too low a temperature out of excessive caution, resulting in a cold solder joint that looks reflowed but was never actually liquid — the sign is a grainy, dull surface instead of the smooth, slightly concave meniscus of a proper joint.

### Logic Family Conflicts and Signal Integrity Degradation

A category of fault that does not appear in component-level testing but causes systematic communication failures is **logic level incompatibility and signal integrity degradation**. When a 5V MCU drives a 3.3V device directly, the receiving device typically survives (most 3.3V ICs are 5V-tolerant on inputs) but the signal may exhibit overshoot that incrementally stresses the input protection diodes. Over thousands of hours of operation, this manifests as an input that starts to draw leakage current, pulling the signal line low and degrading signal integrity for all other devices on that bus.

The oscilloscope is the definitive tool here. A clean digital signal on a properly terminated bus has rise times proportional to the bus capacitance and driver strength, a clean flat top with less than 100mV of overshoot, and fall times that mirror the rise times. Ringing above 10–15% of the signal amplitude indicates an impedance mismatch — either the bus capacitance is too high (too many devices, excessive trace length, or a leaky device), or a termination resistor has been omitted. For I²C buses, reducing pull-up resistor values (from 4.7kΩ to 2.2kΩ or 1kΩ) increases drive current and sharpens rise times on heavily loaded buses, at the cost of higher static current draw. For SPI buses at speeds above a few MHz on traces longer than 5 cm, a 33–50 ohm series resistor at the driver output acts as a source terminator that damps ringing without requiring a parallel termination at the load end.

### Component Substitution Under Tolerance Stack

The final failure mode worth addressing explicitly is the one that technicians create themselves during repair: **component substitution errors**. When a resistor is replaced with the nearest available value, or a capacitor is substituted with one of similar capacitance but different voltage rating or temperature coefficient, the repaired circuit may work in bench testing and fail in deployment. The classic example is substituting an NP0/C0G ceramic capacitor (zero temperature coefficient, used in timing or filter circuits) with an X7R or Y5V part of identical capacitance. The Y5V dielectric loses up to 82% of its rated capacitance at 125°C and can lose 60% at DC bias. In a crystal oscillator load capacitance position, this means the oscillator runs at the wrong frequency above 50°C. The board passes room-temperature testing. It fails in a hot enclosure in the field.

The discipline of substitution is to treat the schematic annotation and the original component datasheet as requirements, not suggestions. If a resistor is marked with a 1% tolerance designation in a precision voltage divider, a 5% substitution will shift the output voltage by an unpredictable amount. If a capacitor position is annotated NP0, the replacement must be NP0. The schematic is the specification. Reading it as a directed signal graph — understanding *why* each component value was chosen relative to the signals flowing through it — is what separates a repair that holds for a decade from one that returns in three months.

The deepest skill in electronic repair is therefore not soldering technique or instrument operation, though both matter enormously. It is the ability to read a circuit topology, predict what every node should look like under normal operation, and then compare that prediction systematically against reality. Every deviation is a data point. The component that fails to match its prediction, while all its neighbors match theirs, is the failed component. The schematic is not paperwork — it is the fault's address, waiting for you to read it.
