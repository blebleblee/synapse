# Operational Verification Labs: Arcade Restoration

## Objective & Operational Lab Setup

Arcade restoration sits at the intersection of analog electronics, digital logic, CRT physics, woodworking, and software archaeology. The practitioner working through these labs is not simply fixing a broken machine — they are reverse-engineering a 40-year-old engineering decision, made by a team under deadline pressure, using components that were already becoming obsolete at time of manufacture. The discipline demands oscilloscope literacy, board-level soldering confidence, power supply characterization, and the mechanical patience to coax warped cabinet wood back into square. These labs build that complete operational picture through direct, hands-on measurement and repair.

The goal across all three exercises is systematic verification: you will never assume a component is good, never assume a voltage rail is stable, and never trust a previous technician's repair. Every claim about machine state is a hypothesis to be confirmed with an instrument.

### Physical Lab Setup

Your bench must be organized before the first probe touches a board. A dedicated ESD mat (minimum 1 MΩ wrist strap resistance to ground) is non-negotiable when handling RAM, ROMs, and custom gate-array ICs from this era. Connect the mat to earth ground via a clip lead attached to the chassis of a powered-off unit, or to your bench power supply's earth terminal.

Assemble the following instruments and consumables before beginning Exercise 1. Every item on this list is used in a specific, documented step. Nothing is here for show.

**Instruments:**

| Instrument | Specification / Model | Purpose |
|---|---|---|
| Digital Multimeter | Fluke 117 or equivalent true-RMS | DC rail voltage, continuity, ESR pre-check |
| Analog Oscilloscope or DSO | 20 MHz minimum bandwidth (e.g., Rigol DS1054Z) | Clock integrity, sync signal analysis, ripple measurement |
| Logic Probe | Simple TTL/CMOS probe (e.g., Sievert LA-104) | Fast digital signal present/absent verification |
| Variable DC Bench Supply | 0–30V / 3A minimum (e.g., RD6006 module) | Isolated PSU simulation, inrush testing |
| ESR Meter | PEAK ESR70 or Atlas ESR+ | In-circuit electrolytic capacitor health |
| Soldering Station | Hakko FX-888D or Weller WE1010 | Precision rework, component replacement |
| Desoldering Station or Pump | ZD-915 vacuum station preferred | Through-hole IC extraction without pad damage |
| Chassis Current Clamp | Optional but valuable | Idle vs. loaded current draw measurement |

**Consumables:** Solder (Kester 63/37 0.8 mm with no-clean flux core), isopropyl alcohol 99% IPA, flux pen (MG Chemicals 835), cotton swabs, brass sponge for iron tip, Kapton tape, IC extraction tool or PLCC puller, 28-pin and 24-pin ZIF socket replacements, header pins for logic probe access.

**Documentation:** Before touching the machine, download or print the full schematic set and PCB layout for the specific board you are restoring. The canonical sources are KLOV (Killer List of Video Games), arcade-history.com, and the Jamma+ archive at jamma.plus. For this lab series, the reference machine is the **Williams Defender (1980)** main PCB set, which uses a Motorola 6809 CPU, four Motorola 6821 PIA chips, and a custom Williams sound board. This machine was manufactured in sufficient quantity that parts are available, schematics are complete, and the failure modes are well-documented across the community. Every measurement value given below is specific to this board set. When applying these labs to a different board, substitute values from that machine's service manual.

A **repair log** is mandatory. Use a physical notebook or a plain-text file. Record every measurement, every component replaced, and every symptom observed. The log is not bureaucracy — it is the instrument that prevents you from spending six hours chasing a symptom you already characterized two sessions ago.

---

## Exercise 1: Foundational Practical Implementation — Power Supply Characterization and Board Bring-Up

The Williams Defender power supply is a linear regulated unit built around a large toroidal transformer and discrete regulation circuitry. Its job is to deliver stable +5 VDC to the logic board (the CPU, RAM, ROMs, and PIAs all operate from this rail), +12 VDC to the monitor deflection and audio amplifier stages, and −5 VDC for a subset of analog circuitry. After 40+ years, every electrolytic capacitor in the supply is a liability. The filter capacitors — typically 4700 µF to 10,000 µF at 25V — lose capacitance and gain equivalent series resistance (ESR) with age. A capacitor that still reads nominally correct capacitance on a DVM may exhibit 8–12 Ω ESR, where the datasheet spec is 0.03–0.07 Ω. Under load transients from the CPU's instruction fetch cycles, that ESR converts current surges into voltage spikes that corrupt data bus signals and cause the 6809 to fetch phantom opcodes.

### Step 1.1 — Initial Inspection (Power Off, Cabinet Unplugged)

Begin with the cabinet unplugged and the main PCB disconnected from the edge connector. Open the bottom of the cabinet and locate the power supply board. Using a flashlight, perform a visual survey with specific purpose: look for capacitors with domed tops (the vent disk should be flat or very slightly concave), any sign of electrolyte residue (a brown or black crust at the base of a capacitor can), cracked solder joints around the bridge rectifier diodes (these carry the full secondary current and their solder joints crack from thermal cycling), and any heat discoloration on the voltage regulator heatsinks or surrounding PCB.

Using your multimeter in continuity mode, verify the AC line fuse is intact and that there is no continuity between the primary side ground and the chassis ground at the PSU board (this would indicate a failed line filter capacitor or a short in the MOV surge suppressor, both of which are common in units plugged into poorly conditioned power for decades).

### Step 1.2 — Out-of-Circuit ESR Testing

Remove the PSU board from the cabinet. Using the PEAK ESR70, test every electrolytic capacitor with a lead diameter of 8 mm or larger. The meter injects a 100 kHz test signal and reads back the resistive component in-circuit with reasonable accuracy, though you should unsolder one lead of any capacitor that reads above 1.0 Ω to confirm out-of-circuit. For the Defender PSU, the main filter caps should read below 0.15 Ω. Record every reading in your log against the board location reference designator (e.g., C4, C7).

| Capacitor Location (Defender PSU) | Nominal Value | ESR Pass Threshold | Typical Aged Reading |
|---|---|---|---|
| C4 (main +5V filter) | 10,000 µF / 16V | < 0.15 Ω | 2.5 – 9.0 Ω |
| C7 (main +12V filter) | 4,700 µF / 25V | < 0.20 Ω | 1.8 – 6.0 Ω |
| C9 (−5V filter) | 1,000 µF / 16V | < 0.35 Ω | 0.8 – 4.0 Ω |
| C12 (5V regulation bypass) | 100 µF / 16V | < 0.50 Ω | 0.5 – 3.0 Ω |

Replace every capacitor that fails its threshold. Use Nichicon UHE, Panasonic FM, or Rubycon ZLH series replacements. Match or exceed the original voltage rating and match the capacitance exactly. Do not substitute a 25V rated cap for a 16V position with more capacitance as a "safety upgrade" — the regulation circuit was tuned for specific impedance at the filter node, and over-capacitance can cause the regulator to oscillate.

Solder the replacements using a temperature of 320°C on your Hakko FX-888D with a 2.4 mm chisel tip. Heat the pad and lead together for 2 seconds, flow solder to the joint (not the iron tip), hold, withdraw iron, let cool undisturbed for 3 seconds. Inspect under magnification: a correct joint is smooth, slightly concave, and the lead is fully wetted. A cold joint has a dull, granular surface and the solder has piled up rather than wicked.

### Step 1.3 — Bench PSU Bring-Up Under Current Limiting

Before reconnecting the PSU to the cabinet, use your bench variable supply set to current-limit mode. This is the "smoke stopper" approach applied to a whole supply board rather than a single component. Connect the bench supply output (set to 25 VAC equivalent DC, approximately 35V for the unregulated DC rail — but check your specific Defender schematic, as some variants differ) in series with a 10 Ω 10W resistor between the transformer secondary and the rectifier input. Set the bench supply current limit to 500 mA. Power on. If the current immediately clamps at the limit, something on the board is shorted. If it rises to a stable 80–150 mA and the output voltages appear on the regulators, the board is behaving normally.

Verify the regulated +5V output at the output terminals with your multimeter. It must read between 4.95V and 5.10V. Adjust the trimmer potentiometer (R-TRIM on the Defender PSU, a 500 Ω cermet pot) while observing the meter until you read 5.05V. This 50 mV of headroom is deliberate: the voltage will sag slightly under full logic board load, and you want it to land at 5.00V–5.02V when the game is running.

Connect a 2.5 Ω / 10W load resistor across the +5V output terminal (this simulates a 2A logic board load) and re-measure. If the voltage drops more than 80 mV, the regulation circuit is marginal — check the pass transistor (a TO-3 power device in the Defender supply) for gain degradation with an hFE measurement on your DMM.

### Step 1.4 — Oscilloscope Ripple Measurement

With the bench PSU and load resistor still in circuit, connect your oscilloscope to the +5V output terminal. Set the scope to AC coupling, 50 mV/div vertical, 2 ms/div horizontal, triggering on internal. You are looking for the residual 120 Hz ripple from the full-wave rectification (120 Hz because a full-wave rectifier doubles the input 60 Hz frequency). A healthy supply with fresh filter capacitors will show peak-to-peak ripple below 50 mV. A supply with degraded capacitors will show 200–600 mV of ripple — enough to corrupt TTL logic, whose noise margin is only about 400 mV on a good day.

Record the ripple amplitude from your scope in your log. If ripple exceeds 50 mV after capacitor replacement, check the bridge rectifier diodes with a DMM in diode-test mode (forward voltage should be 0.55–0.65V per diode, reverse resistance should be infinite). A leaking diode dramatically increases ripple by allowing the capacitor to partially discharge back through the rectifier during the off half-cycle.

---

## Exercise 2: Parameter Variation & Empirical Analysis — CPU Clock Integrity and Signal Bus Verification

With a known-good power supply delivering clean DC rails, attention shifts to the digital heart of the board. The Motorola 6809 in the Defender runs at 1 MHz derived from a 4 MHz crystal oscillator divided by four inside the 74LS74 flip-flop clock divider circuit. This clock signal is the heartbeat of everything — the CPU's instruction fetch timing, the memory address decoding, the PIA synchronization, and the timing generators that feed the video hardware. A clock with marginal rise/fall times, excessive jitter, or the wrong frequency causes symptoms that are almost impossible to diagnose without an oscilloscope because they look like random, intermittent failures: graphical garbage, lockups at game start, attract mode corruption, and sound glitches.

### Step 2.1 — Clock Signal Characterization

With the main PCB on your bench (connected to the now-verified PSU), power the board without the ROM chips installed initially. This isolates the clock generator from the bus activity that would otherwise load the signals you are measuring. The 6809 will not fetch instructions without ROMs, but the clock oscillator will still run, the address and data bus will float, and the 74LS series logic ICs will be active.

Connect your oscilloscope probe to the 6809 pin 34 (the EXTAL input, which receives the divided clock) using a probe ground clip attached to a GND via immediately adjacent to the IC — keep the ground lead under 2 cm to avoid adding inductance that would corrupt the measurement. Set the scope to 1 µs/div and 2V/div. You should see a clean square wave at 1.0 MHz (measured with the scope's frequency counter mode if available, or by reading the period from the grid).

Capture and record:
- Frequency: target 1.000 MHz ± 0.5%
- Rise time (10% to 90%): should be under 25 ns for healthy 74LS74 output
- Duty cycle: should be 50% ± 5%
- Peak-to-peak amplitude: should be 4.8V – 5.0V

If the frequency drifts from nominal by more than 1%, check the crystal (X1) and its load capacitors (C1 and C2, typically 20–33 pF on the Defender clock circuit). A crystal can be tested by temporarily substituting a known-good crystal of identical frequency (4 MHz) from a donor board or parts supply. If the oscillator fails to start entirely, check the power supply to the 74LS04 inverter that forms the oscillator feedback loop — a marginal Vcc at the oscillator IC is a common cause of intermittent startup failure.

### Step 2.2 — Address Bus and Data Bus Probing During ROM Access

With the clock confirmed clean, install the ROM chips (the Defender game ROMs are a set of 2732 EPROMs at positions A1 through A6 on the main board — verify your specific board revision against the schematic, as there are several Defender board variants). Power on the board. The 6809 will immediately begin fetching from the reset vector, which points into the ROM space.

Attach your logic probe to the data bus lines D0 through D7 (probe tip to IC pin, probe ground clip to GND). On a healthy board executing the attract mode loop, every data line should toggle: the probe LED should flicker rapidly, indicating both high and low states are present. A data line that is permanently high or permanently low indicates either a failed ROM (check the specific ROM by substituting from your parts bin), a failed address decoder gate, or a solder bridge on the ROM socket. Data bus lines D0–D7 on the Defender board are accessible at the ROM sockets; use the edge connector PCB pads if the sockets are recessed.

Now move to the oscilloscope for a more detailed view. Probe D3 (arbitrarily chosen as a central data line). Set the scope to 1 µs/div. You will see a chaotic but regular waveform — not a clean square wave, because the data bus carries different values depending on which instruction the CPU is executing. What you are looking for is that the signal transitions are clean (not rounded or showing excessive ringing), that the high level is above 2.4V, and that the low level is below 0.4V. These are the TTL guaranteed logic level thresholds. A signal lingering in the 0.8V–2.0V "forbidden zone" indicates a bus contention condition — two ICs trying to drive the same line simultaneously — which is catastrophic for both devices and usually caused by a failed tri-state buffer or a incorrectly decoded chip-select signal.

### Step 2.3 — Memory Read/Write Cycle Timing Verification

The 6809's memory bus timing is documented in the Motorola MC6809 datasheet (available from Motorola's archived documentation and reproduced in the Defender service manual supplement). The critical timing parameter for a 1 MHz bus is the address setup time before the E clock goes high: the 6809 requires addresses to be valid at least 30 ns before the rising edge of E. The 2732 EPROM has an access time of 450 ns in the original Defender specification (though many boards were upgraded to 250 ns or 200 ns EPROMs during service). With the oscilloscope, you can verify this directly.

Probe the chip-select line of ROM A1 (pin 20 of the 2732 at board position A1, which should be active-low CS). Set the scope to 500 ns/div. Trigger on the falling edge of CS (indicating a read cycle targeting that ROM). Using the scope's cursor measurement, measure the time from the CS falling edge to the data bus becoming valid. This should be less than the EPROM's rated access time minus the address propagation delay through the decoder logic. For a 450 ns EPROM in a 1 MHz system (memory cycle time = 1000 ns), you have substantial margin. If you have substituted faster 150 ns EPROMs, also verify that the data setup time before the E clock falls is at least 30 ns (the 6809's data hold requirement) — faster EPROMs can produce faster-than-expected transitions that the original bus termination was not designed for, causing signal integrity problems in the form of ringing on the data lines that gets sampled as a valid logic level.

### Step 2.4 — Empirical Voltage Rail Mapping Under Game Load

With the game running in attract mode, construct a systematic voltage map of the board. Using your DMM in DC voltage mode, probe Vcc at the power pin of each logic IC on the board. The key measurement is Vcc sag along the power distribution trace from the edge connector to the far ICs. Record all readings in a table:

| IC Position | Device | Vcc Measured (V) | GND Measured (V) | Rail Sag |
|---|---|---|---|---|
| CPU (U1) | MC6809E | 5.02 | 0.00 | Ref |
| RAM bank 1 (U12) | 4116 DRAM | 4.91 | 0.03 | 0.14V |
| PIA 1 (U20) | MC6821 | 4.88 | 0.04 | 0.18V |
| ROM A6 (far edge) | 2732 EPROM | 4.79 | 0.05 | 0.28V |

A rail sag exceeding 0.3V at any IC indicates either a high-resistance solder joint on the power trace, a cracked trace (common in boards that were bent during removal), or a marginal power supply. The acceptable minimum Vcc for 74LS TTL is 4.75V. Any IC operating below that threshold is in an indeterminate state. Use the oscilloscope on those low-voltage ICs to look for glitches on their outputs that would not be visible on the DMM's averaging display.

Sag between the input connector and a distant IC is fundamentally a resistance problem. A 0.3V drop at 2A load implies 0.15 Ω of series resistance — the product of the trace width, length, and copper thickness. The repair is to bridge the failed section of trace with a 24 AWG or 22 AWG wire jumper soldered directly across the damaged segment, which reduces the resistance to negligible levels and restores proper rail voltage.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol — Thermal Stress, Intermittent Fault Isolation, and CRT Monitor Restoration

Intermittent faults are the most time-consuming and psychologically demanding category in arcade restoration. A machine that fails after 20 minutes of operation, works fine for 10 minutes when you open the cabinet for inspection, and then fails again the moment you close it and walk away is exhibiting a thermal intermittent — a component or solder joint whose electrical characteristics change with temperature in a way that crosses a logic threshold boundary. The systematic approach to thermal fault isolation is not intuition or experience-based guessing. It is a physical protocol that uses temperature as a controlled variable.

### Step 3.1 — Thermal Profiling During Extended Operation

Power the board and allow it to run in attract mode for 30 minutes. During this time, your oscilloscope is permanently connected to the CPU's E clock line and triggering on a stop condition: specifically, set the scope to trigger on "pattern hold" or "abnormal waveform" mode if your DSO supports it (the Rigol DS1054Z supports this via the trigger menu under "Pattern" mode). This will capture and freeze the display the moment the clock deviates from normal — either stopping, changing frequency, or showing noise. Set the trigger threshold to 2.5V and the hold-off time to 1 µs to avoid false triggers from normal bus traffic.

While the scope monitors the clock, use a non-contact IR thermometer (or a type-K thermocouple probe on your multimeter) to record the surface temperature of key ICs every five minutes. Create a thermal map in your log:

| Time (min) | CPU (°C) | RAM 4116 bank (°C) | Clock buffer 74LS04 (°C) | PIA1 (°C) | Ambient (°C) |
|---|---|---|---|---|---|
| 5 | 38 | 42 | 36 | 37 | 24 |
| 10 | 44 | 51 | 39 | 42 | 24 |
| 15 | 49 | 58 | 41 | 46 | 25 |
| 20 | 51 | 67 | 43 | 48 | 25 |
| 25 | 52 | 68 | 44 | 49 | 25 |
| 30 | 53 | 69 | 44 | 50 | 25 |

If the system locks up during this period, check the scope: did the clock stop, or did it continue? If the clock stopped, the fault is in the oscillator circuit or the CPU itself lost Vcc. If the clock continued but the game locked, the CPU is executing but reaching a corrupted program state — suspect RAM failure (the 4116 DRAMs in Defender run hot and are historically the most common failure point) or a marginal ROM with a bit that only misreads when the chip is thermally stressed.

### Step 3.2 — Targeted Thermal Stress (Freeze Spray and Heat Gun Protocol)

With the machine running and exhibiting intermittent behavior, thermal probing becomes a targeted intervention. This step uses two tools: compressed freeze spray (MG Chemicals 403A Super Cold, −40°C) and a hot air rework station (or a heat gun at low setting, keeping airflow below 150°C at the IC surface to avoid solder reflow).

The methodology is elimination by contrast. If you cool an IC and the fault goes away, that IC's characteristics were temperature-dependent in the direction of thermal expansion — a cold solder joint that opens up when the PCB expands, or a device whose leakage current increases enough when hot to pull a logic line low. If you heat a cold IC and the fault immediately appears, the same conclusion applies but confirms the direction.

Apply freeze spray in 2-second bursts to individual IC packages, starting with the 4116 DRAM bank (positions U12–U19 on the Defender board). Allow 20 seconds between each application to let the board return to operating temperature before testing the next IC. If freezing U14 (for example) causes the game to begin operating normally for 10–15 seconds before returning to its failed state as the chip warms again, you have isolated the fault to that specific device.

Replace the identified 4116 DRAM by heating each of its 16 pins with the desoldering station (350°C, 7–8 seconds of vacuum) and extracting cleanly. Install a 16-pin DIP socket in its place (never solder a replacement 4116 direct — the entire bank may need progressive replacement). Insert the new 4116 (a compatible modern replacement is the NTE2321 or an equivalent DRAM from a parts supplier like console5.com or jammaholic.com). Verify that pin 1 of the new IC aligns with pin 1 of the socket by confirming the notch orientation matches the board silkscreen.

### Step 3.3 — CRT Monitor Restoration and Safety Protocol

The CRT monitor in a Defender cabinet (a Wells-Gardner 19K4600 or the alternative K4900 chassis, depending on cabinet variant) operates at voltages that are lethal. The flyback transformer generates 20–25 kV on the anode of the CRT, and the main filter capacitors on the B+ rail (typically 165–185 VDC) hold lethal charge for hours after power is removed. This section is not about bypassing that reality — it is about working safely within it, because the monitor is inseparable from a complete restoration.

Before touching any component on the monitor chassis, discharge the CRT anode. Build a discharge tool: take a 10 MΩ resistor (1W rating minimum) and solder it in series between a clip lead and a flat-blade screwdriver. Clip the resistor's other end to a known chassis ground. Slide the screwdriver blade under the rubber anode cup on the side of the CRT and make contact with the anode clip. Hold for 10 seconds. The resistor limits the discharge current to a safe level while still draining the capacitance. After discharge, verify with a DMM (1000V range) that the anode reads below 50V before proceeding. Discharge the main filter capacitors on the B+ rail with a 1 kΩ 5W resistor clipped across each capacitor's terminals for 30 seconds.

With the chassis fully discharged, perform a systematic cap kit replacement on the monitor chassis. The Wells-Gardner K4600 cap kit is commercially available from Bob Roberts' parts archive and from Arcade Restoration Workshop. The kit replaces all electrolytics on the chassis, which addresses the most common failure modes: a collapsed B+ rail (failing main filter cap), horizontal collapse (failing horizontal output capacitors), and loss of focus/screen voltage (failing the HV section filter caps).

The specific capacitor values for the Wells-Gardner K4600 that most frequently fail in service are:

| Reference | Original Value | Failure Mode When Bad | Replacement |
|---|---|---|---|
| C401 | 220 µF / 250V | B+ sag, dim image, shutdown | Nichicon 220 µF / 350V |
| C407 | 47 µF / 160V | Horizontal fold-over | Nichicon 47 µF / 200V |
| C412 | 1 µF / 250V | Vertical collapse | Panasonic 1 µF / 400V |
| C308 | 470 µF / 35V | Loss of picture | Nichicon 470 µF / 50V |
| C201 | 100 µF / 25V | Sound hum injection into video | Rubycon 100 µF / 35V |

Resolder every visible cold joint on the chassis before installing the new capacitors, paying particular attention to the flyback transformer mounting pins, the horizontal output transistor solder pads, and the neck board socket. Use 60/40 solder for the chassis work (the original solder is typically 60/40, and the higher lead content provides better flow on the large through-hole pads), not 63/37 — the difference is minor but 60/40 gives you a slightly longer plastic phase that is easier to manage on large-pad connectors.

### Step 3.4 — Recovery Validation — Full System Integration Test

Reconnect the monitor chassis to the main PCB and power supply. Connect the game board to the cabinet edge connector. Power on with your oscilloscope still connected to the +5V rail (AC coupling, looking for the ripple signature you measured in Exercise 1 as your baseline). The ripple after all repairs should be below 30 mV peak-to-peak.

Allow the machine to run for 60 minutes continuously. During this period, perform a structured observation cycle every 10 minutes. Confirm the following conditions are stable throughout the run:

The video output must maintain stable sync with no rolling, tearing, or color shift (for a color CRT chassis variant). The attract mode must cycle through all five screens (radar, gameplay, high score, the demo sequence, and the initials table) without graphical artifacts or lockups. The audio must produce the characteristic Defender synthesizer sounds without buzzing, clicking, or DC offset hum in the speaker. Control inputs — tested by pressing each button and joystick direction during attract mode's input read cycle — must register without ghosting or missing inputs.

If any fault reappears during the 60-minute thermal soak, your log gives you the timestamp and the ambient/IC temperature at that moment. Cross-reference with your thermal map from Step 3.1 to narrow the suspect component. The resolution is always the same: measure, isolate, substitute, verify.

---

## Operational Reference Guide & Diagnostic Checklist

### The Diagnostic Decision Tree

Arcade fault diagnosis follows a strict hierarchy that prevents wasted effort. The most common mistake a practitioner makes is reaching for the oscilloscope before confirming that the power supply is correct. Everything else is downstream of a stable supply. The second most common mistake is replacing components without first characterizing their measured state — the log entry "replaced because it looked bad" is a failure of methodology.

The diagnostic hierarchy for any arcade PCB follows this sequence without deviation. First, characterize and repair the power supply to its full specification — ripple, regulation, and load response. Second, verify the clock signal at the CPU's clock input pin. Third, verify the CPU's reset line is deasserted correctly after power-on (probe the RST pin; it must go from low to high approximately 20–50 ms after Vcc rises, driven by the RC circuit on the reset supervisor — in Defender, this is a simple RC network with a 100 µF capacitor and 10 kΩ resistor). Fourth, verify bus activity with the logic probe. Only after these four conditions are confirmed does individual component substitution become a rational next step.

### Solder Quality Reference

Every joint you make during a restoration must meet the IPC-A-610 Class 2 standard for consumer electronics: full 360° wetting of both the pad and the lead, no cold joints (dull, granular surface), no bridges, no lifted pads, and solder fill through the barrel of through-hole joints of at least 75%. Inspect every joint with a 5× jeweler's loupe or a USB microscope under raking light (light from the side, not from above) to reveal texture that overhead lighting hides. Cold joints reflect light differently from reflowed joints — they scatter light from their granular surface rather than specularly reflecting it.

### Oscilloscope Quick-Reference for Arcade Diagnostics

| Measurement | Scope Setting | Expected Result | Fault Indicator |
|---|---|---|---|
| CPU clock (1 MHz system) | 1 µs/div, 2V/div, DC couple | 1.000 MHz ± 0.5%, < 25 ns rise | Clock absent, slow rise, wrong freq |
| +5V ripple (under load) | 2 ms/div, 50 mV/div, AC couple | < 50 mV pk-pk 120 Hz | >100 mV: failed filter cap |
| Data bus activity | 1 µs/div, 2V/div, DC couple | Chaotic but fast-switching | Static high/low: stuck bus or ROM |
| ROM chip-select | 500 ns/div, 2V/div, DC couple | Periodic pulses, 0 to 5V clean | No pulses: decoder failure |
| CRT H-sync | 10 µs/div, 2V/div | Periodic pulse at ~15.75 kHz | Missing: horizontal stage failure |

### Common Defender Fault Patterns and Resolutions

The most frequently encountered fault on a Defender board presented for restoration is a totally dead board with no video — the most common cause, in order of probability: (1) failed 4116 DRAM, identifiable by substituting the entire bank; (2) failed ROM, identifiable by probing each ROM's CS and OE lines during CPU execution; (3) failed PIA at U20 or U30, identifiable by probing the RS0, RS1, CS, and R/W lines; (4) failed address decoder logic, identifiable by tracing the address lines from the CPU through the 74LS138 or 74LS139 decoder ICs and verifying that chip-selects appear in the correct address ranges.

The 4116 DRAM is a particularly important subject. It was designed for a +12V, +5V, and −5V supply environment, which is exactly the Defender supply architecture. However, the −5V rail is routed through the 4116's pin 1 (the substrate bias), and if the −5V rail is weak or absent, the DRAM will fail silently — appearing to operate but producing random bit errors that manifest as corrupted graphics or crash loops. Always verify −5V at the 4116 bank pins directly with a multimeter as part of any Defender diagnostic session.

The CRT convergence and geometry adjustments — the pincushion, linearity, and focus controls accessed through the monitor chassis pots — should be set only after all electronic faults are resolved and the chassis has been running for 30 minutes at temperature. Setting convergence on a cold, freshly repaired chassis will require readjustment once it reaches thermal equilibrium. Mark the final pot positions with a dab of nail polish on the pot body and PCB so that future technicians can see the calibrated reference position.

A restored Defender running clean is a singular artifact: a machine designed in 1979, debugged by Eugene Jarvis's team in Atari's shadow, and built to operate in a 24-hour commercial environment. The voltage rails you just characterized, the clock signal you verified, the solder joints you reflowed — all of it is in direct service of keeping that specific piece of engineering history operable for another 40 years. That is the work.
