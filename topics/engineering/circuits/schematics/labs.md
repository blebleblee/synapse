# Operational Verification Labs: Schematics

## Objective & Operational Lab Setup

The operational verification of circuit schematics demands a disciplined methodology that bridges abstract circuit topology with physical hardware realization. This laboratory guide trains the practitioner to read, analyze, and validate electrical schematics through three integrated verification domains: symbolic interpretation of schematic representations, quantitative parameter analysis using first-principles circuit theory, and empirical validation through simulation and measurement. The schematic serves as the authoritative contract between design intent and physical implementation, and the engineer must develop the skill to audit this contract for electrical correctness, component feasibility, and manufacturability before committing resources to fabrication or assembly.

The verification workflow proceeds through progressive rigor. Initial exercises establish fluency in schematic symbology, component identification, and netlist extraction—the foundational language of circuit documentation. Subsequent exercises introduce parametric analysis, where the practitioner applies Kirchhoff's voltage and current laws, Thévenin equivalents, and AC impedance calculations to predict circuit behavior under nominal operating conditions. Final stress-testing exercises expose the schematic to boundary conditions: supply voltage extremes, component tolerance stacking, thermal derating, and failure-mode analysis. This three-tier approach mirrors the design validation process in production engineering, where schematics must survive scrutiny at the component level, circuit level, and system integration level before release to manufacturing.

The laboratory environment centers on SPICE-class circuit simulation tools, which provide cycle-accurate analog simulation with component-level fidelity. The practitioner will utilize LTspice XVII, a zero-cost industry-standard simulator developed by Analog Devices, which offers native support for transient analysis, AC frequency sweeps, DC operating point calculation, and Monte Carlo parameter variation. LTspice's schematic capture interface enforces electrical design rules in real time, flagging floating nodes, unconnected pins, and topological errors that would result in simulation failure or ambiguous solutions. The tool's integrated waveform viewer enables direct correlation between schematic topology and time-domain or frequency-domain behavior, establishing the cause-and-effect intuition essential for debugging physical hardware.

Installation of LTspice requires downloading the Windows or macOS native binary from Analog Devices' official distribution server, executing the installer with administrator privileges, and verifying successful installation by launching the application and confirming access to the standard component library located in the `/lib` subdirectory. On Linux systems, LTspice operates under Wine 6.0 or later with full graphical interface support. The practitioner must configure the simulation engine for adequate numerical precision by navigating to `Tools → Control Panel → SPICE` and setting the relative tolerance (`reltol`) to `1e-6`, the absolute current tolerance (`abstol`) to `1e-12 A`, and the absolute voltage tolerance (`vntol`) to `1e-9 V`. These precision settings ensure that the simulator resolves small-signal behavior in high-gain amplifier stages and low-noise analog front ends without premature convergence to incorrect solutions.

Supplementary analytical tools include a scientific calculator capable of complex arithmetic for impedance calculations, a spreadsheet application (LibreOffice Calc or Microsoft Excel) for tabulating parametric sweeps and plotting transfer functions, and a component datasheet library covering resistors, capacitors, inductors, diodes, bipolar junction transistors, and operational amplifiers. The practitioner must maintain a physical notebook for hand calculations, circuit annotations, and failure-mode hypotheses, as the discipline of manual derivation reinforces intuition that pure simulation cannot provide.

The laboratory workspace must accommodate both digital schematic capture and analog measurement instrumentation. A dual-monitor configuration accelerates workflow by displaying the schematic on one screen and simulation waveforms on the other. The workbench must include a digital multimeter for resistance verification of physical components when cross-checking schematic values against inventory, a breadboard for optional prototype validation of simulation results, and adequate lighting for reading fine-pitch component markings. The practitioner will maintain a structured file hierarchy for schematic projects, organizing each exercise into a dedicated subdirectory containing the `.asc` schematic file, associated `.net` SPICE netlist, simulation output logs, and a `README.md` file documenting the circuit's design intent, operating conditions, and verification results.

---

## Exercise 1: Foundational Practical Implementation

### Objective

The first exercise establishes proficiency in schematic capture, component placement, netlist generation, and DC operating point verification. The practitioner will construct a two-stage resistor voltage divider with emitter-follower buffering, extract the SPICE netlist, calculate theoretical node voltages using Kirchhoff's voltage law, and validate predictions through simulation. This circuit topology exemplifies fundamental schematic verification principles: node voltage traceability, current path continuity, and input-output impedance transformation.

### Circuit Topology and Design Intent

The circuit comprises a 12 V DC supply driving a resistive voltage divider formed by R1 (10 kΩ) and R2 (10 kΩ), creating a nominal midpoint voltage of 6 V. This divider output feeds the base terminal of an NPN bipolar junction transistor configured as an emitter follower, which presents high input impedance to avoid loading the divider while driving a 1 kΩ load resistor with low output impedance. The emitter follower's output voltage ideally replicates the base voltage minus one diode drop (approximately 0.7 V for silicon transistors at room temperature), yielding an expected emitter voltage near 5.3 V under no-load conditions. A 1 kΩ collector resistor RC limits maximum collector current to safe operating levels, and a 470 Ω emitter resistor RE stabilizes the bias point against temperature drift.

### Schematic Capture Procedure

Launch LTspice and create a new schematic by selecting `File → New Schematic`. The blank canvas operates in an infinite-zoom coordinate system where components snap to a 0.1-inch grid. Begin by placing the DC voltage source: press `F2` to open the component selector, type `voltage`, select the generic `voltage` symbol, and click to place it in the lower-left quadrant of the canvas. Right-click the placed voltage source symbol and set its DC value to `12` in the value field. Rotate the component if necessary using `Ctrl+R` so that the positive terminal faces upward, consistent with conventional current flow from supply to ground.

Next, place the voltage divider resistors. Press `F2`, type `res`, and select the standard resistor symbol. Place R1 connected to the positive terminal of the voltage source, then place R2 in series below R1. Right-click R1 and set its resistance value to `10k`. Repeat for R2. Connect a wire from the junction between R1 and R2 by clicking the wire tool (pencil icon or press `F3`), then dragging from the junction node to a new location where the transistor base will connect. This junction node represents the divider output and must remain accessible for voltage probing during simulation.

Place the NPN bipolar junction transistor by pressing `F2` and typing `npn`. LTspice defaults to the 2N2222A model, a general-purpose silicon NPN transistor with β (current gain) approximately 100 and VBE ≈ 0.7 V. Position the transistor so its base terminal aligns with the divider output wire. Connect the transistor collector to the positive supply rail through a 1 kΩ resistor RC. Connect the emitter through a 470 Ω resistor RE to ground. Attach a 1 kΩ load resistor RL from the emitter node to ground, representing the circuit's output stage.

Establish the ground reference by pressing `G` and clicking at the bottom of the schematic near the negative terminal of the voltage source, the bottom of R2, and the bottom of RE. All ground symbols must share the same net name (automatically assigned by LTspice) to ensure a common zero-volt reference. Label critical nodes using the `F4` key: name the divider output node `VDIV`, the transistor base node `VB`, the emitter node `VOUT`, and the collector node `VC`. Node labels enable direct correlation between schematic inspection and simulation results.

### Theoretical Pre-Simulation Analysis

Before executing simulation, the practitioner must derive expected node voltages analytically to establish baseline predictions. The voltage divider output voltage VDIV calculates as:

$$V_{\text{DIV}} = V_{\text{CC}} \cdot \frac{R_2}{R_1 + R_2} = 12\,\text{V} \cdot \frac{10\,\text{k}\Omega}{10\,\text{k}\Omega + 10\,\text{k}\Omega} = 6.0\,\text{V}$$

This calculation assumes infinite input impedance at the divider output, valid when the base current IB drawn by the transistor is negligible compared to the divider current. The divider current ID flows as:

$$I_D = \frac{V_{\text{CC}}}{R_1 + R_2} = \frac{12\,\text{V}}{20\,\text{k}\Omega} = 0.6\,\text{mA}$$

The transistor base-emitter junction forward-biases when VB exceeds the emitter voltage VE by approximately 0.7 V. The emitter voltage VOUT calculates as:

$$V_{\text{OUT}} = V_{\text{B}} - V_{\text{BE}} = 6.0\,\text{V} - 0.7\,\text{V} = 5.3\,\text{V}$$

The emitter current IE divides between the emitter resistor RE and the load resistor RL, which appear in parallel from the emitter node to ground. The parallel resistance calculates as:

$$R_{\text{E,eff}} = \frac{R_E \cdot R_L}{R_E + R_L} = \frac{470\,\Omega \cdot 1000\,\Omega}{470\,\Omega + 1000\,\Omega} \approx 320\,\Omega$$

The emitter current IE derives from Ohm's law applied to the emitter-to-ground path:

$$I_E = \frac{V_{\text{OUT}}}{R_{\text{E,eff}}} = \frac{5.3\,\text{V}}{320\,\Omega} \approx 16.6\,\text{mA}$$

The base current IB relates to emitter current through the transistor's current gain β:

$$I_B = \frac{I_E}{\beta + 1} = \frac{16.6\,\text{mA}}{101} \approx 164\,\mu\text{A}$$

This base current loads the voltage divider, causing VDIV to sag below the unloaded 6.0 V. The actual divider output voltage recalculates as:

$$V_{\text{DIV,loaded}} = V_{\text{CC}} \cdot \frac{R_2}{R_1 + R_2} - I_B \cdot \frac{R_1 \cdot R_2}{R_1 + R_2} = 6.0\,\text{V} - 164\,\mu\text{A} \cdot 5\,\text{k}\Omega \approx 5.18\,\text{V}$$

This loading effect reduces VOUT to approximately 4.48 V, demonstrating the importance of accounting for finite input impedance in practical circuits.

### Simulation Execution and DC Operating Point Verification

Save the schematic by pressing `Ctrl+S` and naming the file `ex1_emitter_follower.asc`. Execute a DC operating point analysis by selecting `Simulate → Edit Simulation Cmd` and choosing the `.op` directive from the DC op pnt tab. Click OK, then click once on the schematic canvas to place the `.op` command text. Press `F5` or click the running-man icon to launch simulation. LTspice computes the DC steady-state solution and displays node voltages overlaid on the schematic.

Verify node voltages by inspecting the on-canvas annotations. The divider output node VDIV should display approximately 5.2 V, the base node VB should match VDIV, and the emitter node VOUT should read approximately 4.5 V, consistent with the hand-calculated predictions accounting for base current loading. The collector node VC should exhibit voltage near 12 V minus the voltage drop across RC due to collector current IC ≈ IE = 16.6 mA, yielding VC ≈ 12 V - (16.6 mA × 1 kΩ) ≈ -4.6 V, which indicates simulation error or topology mistake. The practitioner must recognize this discrepancy immediately.

Re-inspect the schematic for wiring errors. The collector resistor RC must connect between the positive supply rail and the collector terminal, not between the collector and ground. Correct the topology by rewiring RC to the VCC rail, then re-run simulation. The corrected collector voltage should read approximately 10.3 V, indicating 1.7 V drop across RC due to 1.7 mA collector current. The discrepancy between calculated IE (16.6 mA) and simulated IC (1.7 mA) reveals incorrect parallel resistance calculation or component value entry error. Cross-check component values by hovering the cursor over each component symbol and verifying displayed values match specification.

Generate a SPICE netlist for external inspection by selecting `View → SPICE Netlist`. The netlist enumerates all components, nodes, and their interconnections in ASCII text format. Verify that RE and RL connect in parallel between the emitter node and ground node 0. The netlist entry should resemble:

```
RE VOUT 0 470
RL VOUT 0 1k
```

If RL is missing or connected to the wrong node, return to schematic capture and correct the wiring.

### Empirical Validation and Measurement Protocol

Once simulation matches analytical predictions within 10% tolerance, the practitioner must document results in a verification matrix. Create a spreadsheet with columns labeled Node Name, Calculated Voltage (V), Simulated Voltage (V), Absolute Error (V), and Percent Error (%). Populate the table:

| Node Name | Calculated Voltage (V) | Simulated Voltage (V) | Absolute Error (V) | Percent Error (%) |
|-----------|------------------------|------------------------|--------------------|--------------------|
| VDIV      | 5.18                   | 5.21                   | 0.03               | 0.58               |
| VB        | 5.18                   | 5.21                   | 0.03               | 0.58               |
| VOUT      | 4.48                   | 4.51                   | 0.03               | 0.67               |
| VC        | 10.34                  | 10.41                  | 0.07               | 0.68               |

Percent error below 1% indicates excellent correlation between analytical model and simulation. Errors exceeding 5% demand root-cause investigation: verify component values, check for floating nodes, inspect transistor model parameters, and confirm ground reference integrity.

Extend verification to current measurements by right-clicking any wire segment and selecting "Add Current Probe." LTspice overlays current waveforms in the plot window. Measure the collector current IC by probing the wire between RC and the transistor collector. Measure emitter current IE by probing the wire between the emitter and RE. Verify IE ≈ IC, consistent with BJT current relations where IC ≈ α·IE and α ≈ 1 for high-gain transistors.

### Deliverables and Documentation Requirements

The practitioner must produce a one-page technical memorandum documenting Exercise 1 results. The memo includes schematic capture screenshot, netlist excerpt, analytical derivation summary, simulation results table, and deviation analysis. Any discrepancies exceeding 5% must be explained with corrective actions documented. Archive the LTspice `.asc` file, simulation log, and memo PDF in the `ex1/` subdirectory of the laboratory file structure.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Objective

The second exercise advances verification methodology by introducing parametric sweeps, component tolerance analysis, and frequency-domain characterization. The practitioner will modify the emitter-follower circuit to accept AC input signals, perform transient analysis to observe signal amplification and distortion, execute AC frequency sweeps to extract bandwidth and cutoff frequencies, and apply Monte Carlo simulation to quantify performance variability under component tolerance stacking. This exercise mirrors production design validation, where circuits must maintain specifications across manufacturing spread and environmental drift.

### Circuit Modification for AC Signal Analysis

Reopen the `ex1_emitter_follower.asc` schematic and save a copy as `ex2_ac_analysis.asc`. Replace the DC voltage divider with an AC-coupled input stage to enable small-signal frequency response testing. Remove the resistors R1 and R2 by selecting them and pressing `Delete`. Place a sine wave voltage source at the divider output location by pressing `F2`, typing `voltage`, and selecting the voltage symbol. Right-click the new source and configure it as an AC signal: set the DC offset to `2.5` volts (to maintain mid-supply biasing), amplitude to `100m` (100 mV peak), and frequency to `1k` (1 kHz). The SPICE directive should read `SINE(2.5 100m 1k)`.

Insert a DC blocking capacitor C1 between the AC source and the transistor base to prevent the source's DC offset from disturbing the transistor's bias point. Place a `1µ` (1 µF) capacitor in series with the base connection. The capacitor's impedance at 1 kHz calculates as:

$$X_C = \frac{1}{2\pi f C} = \frac{1}{2\pi \cdot 1000\,\text{Hz} \cdot 1\times10^{-6}\,\text{F}} \approx 159\,\Omega$$

This impedance remains low compared to the transistor's input impedance, ensuring minimal signal attenuation at the operating frequency. Add a bias resistor RB from the transistor base to ground to establish a stable DC bias point. Set RB to `100k`, which draws negligible current while preventing the base from floating.

### Transient Analysis Configuration and Time-Domain Observation

Configure a transient analysis to observe the circuit's time-domain response over multiple signal cycles. Select `Simulate → Edit Simulation Cmd`, choose the "Transient" tab, and set the stop time to `10m` (10 milliseconds, capturing 10 cycles of the 1 kHz input). Leave the maximum timestep blank to allow the simulator to auto-select appropriate resolution. Click OK and place the `.tran 10m` directive on the schematic.

Run the simulation by pressing `F5`. The waveform viewer opens automatically, initially blank. Click on the node label `VOUT` on the schematic to plot the emitter output voltage as a function of time. The waveform should display a sinusoidal signal oscillating around 4.5 V with peak-to-peak amplitude slightly less than 200 mV (accounting for the emitter follower's voltage gain of approximately unity). Overlay the input signal by clicking on the AC source's positive terminal. The plot now displays both input and output, enabling direct visual comparison of phase relationship and amplitude transfer.

Measure signal gain by calculating the ratio of output amplitude to input amplitude. Use the waveform viewer's cursor tool (click the crosshair icon or press `Ctrl+Left-Click` on the waveform) to place measurement cursors at the peak and trough of the output waveform. The viewer displays peak-to-peak voltage in the cursor readout. Divide output peak-to-peak voltage by input peak-to-peak voltage (200 mV) to compute gain. Expected gain for an emitter follower is approximately 0.95 to 0.98, reflecting slight voltage division across the emitter resistance.

Inspect for signal distortion by zooming into individual waveform peaks. Non-sinusoidal distortion manifests as flattened peaks or asymmetric positive/negative half-cycles, indicating transistor cutoff, saturation, or slew-rate limiting. Clean sinusoidal output confirms linear operation within the small-signal regime. If distortion appears, reduce input amplitude to `50m` and re-run transient analysis to verify operation below clipping thresholds.

### AC Frequency Sweep and Bandwidth Extraction

Convert the simulation to AC analysis mode to extract frequency-dependent impedance and gain characteristics. Delete the `.tran` directive and select `Simulate → Edit Simulation Cmd → AC Analysis`. Set the analysis type to "Decade," number of points per decade to `100`, start frequency to `10` Hz, and stop frequency to `1Meg` (1 MHz). Place the `.ac dec 100 10 1Meg` directive on the schematic and run simulation.

Plot the output voltage magnitude by clicking the `VOUT` node label. LTspice displays the frequency response as a Bode magnitude plot, with frequency on a logarithmic horizontal axis and voltage magnitude in decibels on the vertical axis. The emitter follower exhibits flat gain near 0 dB (unity gain) across the mid-band frequencies, with rolloff at low frequencies due to C1's increasing impedance and rolloff at high frequencies due to transistor parasitic capacitances.

Measure the -3 dB bandwidth by placing cursors on the frequency response curve and identifying frequencies where gain drops 3 dB below the mid-band value. The low-frequency cutoff fL corresponds to the RC high-pass filter formed by C1 and the input impedance looking into the base. Calculate the theoretical cutoff:

$$f_L = \frac{1}{2\pi C_1 R_{\text{in}}}$$

where $R_{\text{in}} \approx \beta \cdot (R_E \parallel R_L) = 100 \cdot 320\,\Omega = 32\,\text{k}\Omega$. Substituting values:

$$f_L = \frac{1}{2\pi \cdot 1\times10^{-6}\,\text{F} \cdot 32\times10^{3}\,\Omega} \approx 5.0\,\text{Hz}$$

The simulation should confirm fL near 5 Hz. The high-frequency cutoff fH depends on transistor parasitic capacitances, primarily the base-emitter junction capacitance Cbe and the collector-base Miller capacitance. These parameters are embedded in the transistor's SPICE model and are not easily hand-calculated without datasheet inspection. Measure fH from the Bode plot using cursors, expected in the range of 10 kHz to 100 kHz for the 2N2222A model.

### Monte Carlo Tolerance Analysis and Statistical Variation

Real-world circuits exhibit performance variability due to component tolerance stacking. Resistors typically carry ±5% tolerance, capacitors ±10%, and transistor parameters vary by ±20% or more across production lots. LTspice supports Monte Carlo analysis through the `.step` and `.param` directives combined with random distribution functions. Modify the schematic to incorporate tolerance modeling.

Right-click resistor RE and change its value from `470` to `{RE_nom*gauss(1,0.05)}`, where `RE_nom` is a parameter defining the nominal resistance and `gauss(1,0.05)` generates a Gaussian random variable with mean 1 and standard deviation 0.05 (5% tolerance). Add a `.param RE_nom=470` directive to the schematic. Repeat for other resistors and the coupling capacitor, defining `.param RC_nom=1k`, `.param RL_nom=1k`, `.param C1_nom=1u`, and modifying component values to `{RC_nom*gauss(1,0.05)}`, `{RL_nom*gauss(1,0.05)}`, and `{C1_nom*gauss(1,0.1)}`.

Add a `.step param run 1 100 1` directive to instruct LTspice to run 100 simulation iterations, each with different random component values. Run the simulation and observe the waveform viewer displaying 100 overlaid output traces, visualizing the spread of circuit performance across tolerance variations. Right-click the plot pane and select "View → Set Plot Settings → Step Legend" to display individual trace identifiers.

Quantify performance spread by exporting waveform data to a spreadsheet. In the waveform viewer, press `Ctrl+W` to open the waveform data export dialog. Export the VOUT trace at a specific time point (e.g., 5 ms) for all 100 runs. Import the data into a spreadsheet and calculate statistical descriptors: mean output voltage, standard deviation, minimum, maximum, and ±3σ range. The ±3σ range captures 99.7% of expected production outcomes under Gaussian distribution assumptions.

Construct a histogram of output voltages to visualize the distribution. Create 10 equally spaced bins spanning the range from minimum to maximum observed output voltage, count the number of simulation runs falling into each bin, and plot a bar chart. A centered, bell-shaped distribution confirms that component tolerances do not introduce systematic bias or excessive skew in circuit performance. If the distribution exhibits multi-modality or heavy tails, investigate whether certain component combinations push the transistor into cutoff or saturation, requiring bias point re-centering or tolerance tightening.

### Parametric Sweep of Load Resistance and Output Impedance Characterization

The emitter follower's output impedance Zout determines its ability to drive varying load resistances without performance degradation. Perform a parametric sweep of RL to quantify Zout empirically. Replace the fixed `1k` load resistor value with `{RL_sweep}` and add a `.step param RL_sweep list 100 470 1k 4.7k 10k` directive, instructing the simulator to run five analyses with RL equal to 100 Ω, 470 Ω, 1 kΩ, 4.7 kΩ, and 10 kΩ.

Execute a transient simulation with the parametric sweep active. The waveform viewer displays five overlaid VOUT traces, each corresponding to a different load resistance. Observe that lighter loads (higher RL) produce higher output voltage, while heavier loads (lower RL) reduce output voltage due to increased voltage division across the emitter follower's output impedance. Measure the output voltage at 5 ms for each RL value and tabulate results:

| RL (Ω) | VOUT (V) | ΔVOUT (V) vs. RL=10kΩ |
|--------|----------|-----------------------|
| 100    | 4.05     | -0.45                 |
| 470    | 4.30     | -0.20                 |
| 1000   | 4.41     | -0.09                 |
| 4700   | 4.48     | -0.02                 |
| 10000  | 4.50     | 0.00                  |

The output impedance Zout calculates from the change in output voltage with respect to change in load current:

$$Z_{\text{out}} = \frac{\Delta V_{\text{OUT}}}{\Delta I_{\text{L}}}$$

where $\Delta I_L$ is the change in load current between two RL values. For RL transitioning from 10 kΩ to 1 kΩ, the load current changes from 0.45 mA to 4.41 mA, yielding:

$$Z_{\text{out}} = \frac{4.50\,\text{V} - 4.41\,\text{V}}{4.41\,\text{mA} - 0.45\,\text{mA}} \approx \frac{0.09\,\text{V}}{3.96\,\text{mA}} \approx 22.7\,\Omega$$

This empirical output impedance aligns with the theoretical prediction for an emitter follower:

$$Z_{\text{out}} \approx \frac{R_E}{\beta + 1} + \frac{R_{\text{source}}}{\beta + 1}$$

where $R_{\text{source}}$ represents the Thévenin resistance driving the base. For this circuit, $R_{\text{source}} \approx 0$ (ideal voltage source through low-impedance capacitor), yielding:

$$Z_{\text{out}} \approx \frac{470\,\Omega}{101} \approx 4.7\,\Omega$$

The discrepancy between calculated 4.7 Ω and measured 22.7 Ω arises from the parallel combination of RE and the transistor's intrinsic emitter resistance re, approximately 26 Ω at 1 mA emitter current. Refine the calculation:

$$Z_{\text{out}} \approx r_e + \frac{R_E \parallel R_B}{\beta + 1}$$

where $r_e = \frac{V_T}{I_E} = \frac{26\,\text{mV}}{16\,\text{mA}} \approx 1.6\,\Omega$. The refined estimate approaches the empirical measurement, validating the analysis methodology.

### Deliverables and Documentation Requirements

The practitioner must produce a comprehensive technical report documenting Exercise 2 results. The report includes annotated schematics for AC analysis configuration, transient waveform screenshots with cursor measurements, Bode magnitude plots with annotated -3 dB bandwidth, Monte Carlo histogram and statistical summary, parametric sweep data table, and output impedance derivation. Archive all LTspice files, exported waveform data, spreadsheet analysis, and the final report PDF in the `ex2/` subdirectory.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Objective

The third exercise subjects the schematic to extreme operating conditions to identify failure modes, validate design margins, and establish recovery procedures. The practitioner will systematically stress the emitter-follower circuit through supply voltage extremes, over-temperature operation, component open/short faults, and signal overload, documenting failure thresholds and implementing protective design modifications. This exercise trains the diagnostic mindset required for field troubleshooting and reliability engineering, where circuits must survive transient abuse and degrade gracefully rather than catastrophically.

### Supply Voltage Stress Testing and Voltage Regulator Insertion

Copy the `ex2_ac_analysis.asc` schematic and save as `ex3_stress_test.asc`. The original 12 V supply represents nominal operating conditions, but production circuits must tolerate supply voltage variation from brownout (undervoltage) to surge (overvoltage) conditions. Define a parametric sweep of supply voltage VCC from 8 V to 16 V to characterize circuit behavior across this range.

Modify the voltage source V1 by right-clicking and changing its DC value from `12` to `{VCC_sweep}`. Add a `.step param VCC_sweep list 8 9 10 11 12 13 14 15 16` directive to the schematic. Run a DC operating point analysis (`.op`) with the sweep active. LTspice computes nine DC solutions, one for each supply voltage.

Plot the emitter output voltage VOUT as a function of VCC_sweep by clicking the VOUT node label after simulation completes. The plot displays VOUT increasing approximately linearly with VCC, confirming that the emitter follower tracks the supply voltage. Measure the output voltage at VCC = 8 V and VCC = 16 V to quantify voltage tracking:

| VCC (V) | VOUT (V) | VOUT / VCC |
|---------|----------|-----------|
| 8       | 2.85     | 0.356     |
| 12      | 4.50     | 0.375     |
| 16      | 6.15     | 0.384     |

The increasing VOUT/VCC ratio indicates that bias current through RE increases with supply voltage, shifting the transistor's operating point. Calculate the collector current IC at VCC = 16 V by probing the collector node current:

$$I_C = \frac{V_{\text{CC}} - V_{\text{C}}}{R_C} = \frac{16\,\text{V} - 13.2\,\text{V}}{1\,\text{k}\Omega} = 2.8\,\text{mA}$$

At VCC = 8 V:

$$I_C = \frac{8\,\text{V} - 6.8\,\text{V}}{1\,\text{k}\Omega} = 1.2\,\text{mA}$$

The collector current varies by a factor of 2.3× across the supply voltage range, risking thermal stress at high supply voltages and inadequate bias margin at low voltages. Insert a Zener diode voltage regulator to stabilize the bias point against supply variation. Add a 1N4733A Zener diode (5.1 V nominal breakdown voltage) in series with a 1 kΩ current-limiting resistor R_zener from VCC to ground. Connect the transistor base to the Zener cathode through a 10 kΩ bias resistor.

Modify the schematic to include the Zener regulator: place a Zener diode by pressing `F2`, typing `zener`, and selecting the `ZENER` symbol. Right-click the Zener and edit its model to reference the 1N4733A model (available in LTspice's standard library under `lib/cmp/standard.dio`). Connect R_zener between VCC and the Zener anode, and the Zener cathode to the base bias resistor. Re-run the supply voltage sweep and verify that VOUT remains stable within ±5% across the 8 V to 16 V range.

### Thermal Stress and Temperature Coefficient Analysis

Semiconductor device parameters exhibit strong temperature dependence, particularly the base-emitter voltage VBE, which decreases approximately 2 mV/°C. Model thermal stress by sweeping the ambient temperature from -40°C to +85°C, the industrial temperature range for commercial electronics. Add a `.temp -40 -20 0 25 50 70 85` directive to sweep temperature across seven values.

Run a DC operating point analysis with the temperature sweep active. Plot VOUT versus temperature and observe the output voltage decreasing with increasing temperature due to VBE reduction. Quantify the temperature coefficient TCVOUT by measuring the slope of the VOUT-versus-temperature curve:

$$\text{TC}_{V_{\text{OUT}}} = \frac{\Delta V_{\text{OUT}}}{\Delta T} = \frac{V_{\text{OUT}}(85\,°\text{C}) - V_{\text{OUT}}(-40\,°\text{C})}{85\,°\text{C} - (-40\,°\text{C})}$$

Expected values fall near -2 mV/°C, consistent with VBE temperature dependence. Compensate for temperature drift by adding a negative-temperature-coefficient thermistor in parallel with RE, or by replacing the fixed bias resistor with a complementary temperature-tracking bias network. For this exercise, document the uncompensated temperature coefficient and flag it as a design weakness requiring mitigation in production hardware.

### Component Fault Injection and Failure Mode Analysis

Simulate catastrophic component failures by systematically open-circuiting and short-circuiting each component while monitoring output voltage and current paths. Begin with the emitter resistor RE: modify its value to `1G` (1 GΩ, approximating an open circuit) and run DC operating point analysis. The output voltage VOUT should collapse to approximately 0 V, as the open-circuited emitter prevents current flow, forcing the transistor into cutoff.

Verify current flow by probing the emitter node current. The probe should display near-zero current, confirming cutoff operation. Short-circuit RE by changing its value to `1m` (1 mΩ, approximating a short) and re-run analysis. The output voltage should jump to approximately VB - VBE, but the collector current will surge to unsafe levels, potentially exceeding the transistor's maximum collector current rating. Measure IC and compare against the 2N2222A's absolute maximum rating of 800 mA (consult the datasheet). If IC exceeds 800 mA, the transistor would fail by thermal runaway in physical hardware.

Document failure modes in a Failure Mode and Effects Analysis (FMEA) table:

| Component | Fault Type  | Failure Symptom                    | System Impact      | Detection Method        | Mitigation Strategy        |
|-----------|-------------|------------------------------------|--------------------|-------------------------|----------------------------|
| RE        | Open        | VOUT → 0 V, transistor cutoff      | Loss of output     | DC voltage measurement  | Redundant parallel resistor |
| RE        | Short       | IC → >800 mA, thermal runaway      | Component destruction | Overcurrent protection | Series fuse or PTC thermistor |
| C1        | Open        | Loss of AC coupling, VOUT flat     | No signal transmission | AC signal probing      | Dual-path coupling with fail-safe DC restoration |
| C1        | Short       | Base DC bias collapses, cutoff     | Loss of output     | DC voltage measurement  | Series blocking diode |
| RC        | Open        | Collector floats to VCC, no IC     | Loss of output     | Collector voltage measurement | Pulldown resistor to detect open condition |
| Q1        | Collector-Emitter short | VOUT → VCC, runaway current | Power supply overload | Smoke, current sense | Fuse or current-limiting supply |

For each fault mode, propose a design modification that enables detection or fail-safe operation. For example, add a 100 Ω series resistor in the collector path to limit short-circuit current to 120 mA under worst-case VCC = 16 V, preventing catastrophic transistor failure while allowing sufficient headroom for normal operation.

### Signal Overload and Clipping Threshold Determination

Increase the AC input amplitude progressively to identify the signal level at which the transistor enters nonlinear operation, causing output waveform clipping. Modify the AC source amplitude from `100m` to `{Vin_sweep}` and add a `.step param Vin_sweep list 0.1 0.5 1 2 3 4` directive, sweeping input amplitude from 100 mV to 4 V peak.

Run a transient analysis with the amplitude sweep active and plot the output waveform VOUT. At low amplitudes (100 mV, 500 mV), the output remains sinusoidal. At 1 V input, observe slight flattening of negative peaks, indicating the transistor approaches cutoff as the base voltage swings below VBE. At 2 V input, negative clipping becomes pronounced, with the output waveform exhibiting flat-bottom half-cycles. At 4 V input, both positive and negative clipping occurs, as the output voltage cannot exceed VCC - VCE(sat) or fall below VBE(sat).

Measure the clipping threshold by calculating the peak-to-peak output voltage for each input amplitude and identifying where the output no longer scales linearly with input. Plot output amplitude versus input amplitude in a spreadsheet and fit a linear regression to the low-amplitude data points. The deviation point where measured output falls below the regression line by more than 1% marks the onset of nonlinear distortion. Document the clipping threshold amplitude and correlate it to the DC bias point: circuits biased closer to mid-supply (VCC/2) tolerate larger signal swings before clipping.

### Recovery Protocol and Design Hardening Recommendations

Based on the stress test results, document a formal recovery protocol for field technicians encountering failed circuits. The protocol must include voltage measurement checkpoints, component substitution procedures, and verification tests to confirm restoration of nominal operation. Structure the protocol as a decision tree flowchart:

1. Measure VCC at the power supply input. If VCC < 10 V or > 14 V, verify power supply regulation before proceeding.
2. Measure VOUT with no input signal applied. If VOUT = 0 V, suspect RE open or transistor cutoff; measure base voltage VB. If VB < 2 V, check bias network; if VB > 4 V and VOUT = 0 V, suspect emitter open circuit.
3. Measure VOUT with 100 mV AC input at 1 kHz applied. If VOUT remains DC with no AC component, suspect C1 open; measure AC voltage across C1 to confirm.
4. Inject 1 V AC input. If output clips, reduce input amplitude and re-test. If clipping persists at low amplitude, transistor may be damaged; measure IC under DC bias. If IC > 50 mA with no input signal, replace transistor.
5. After any component replacement, re-measure all node voltages under DC bias and verify against nominal values documented in Exercise 1. Perform frequency sweep to confirm -3 dB bandwidth matches specification.

Implement design hardening modifications to improve circuit robustness:

- Add a 100 mA polyfuse in series with VCC to protect against short-circuit faults.
- Replace C1 with a dual-series capacitor configuration (two 2.2 µF capacitors in series) to provide redundancy against open-circuit failure.
- Add a 10 kΩ pulldown resistor from base to ground to establish a defined bias state if the bias network fails open.
- Implement a Zener clamp (back-to-back 5.6 V Zener diodes) across the output to protect downstream circuitry from overvoltage transients.

Re-run the complete stress test suite with hardened circuit modifications active and verify that all failure modes either resolve gracefully or trigger protective mechanisms before catastrophic damage occurs.

### Deliverables and Documentation Requirements

The practitioner must produce a comprehensive reliability report documenting Exercise 3 results. The report includes FMEA table, stress test plots (supply voltage sweep, temperature sweep, amplitude sweep), clipping threshold analysis, failure mode investigation screenshots, recovery protocol flowchart, and hardened schematic with protective components annotated. Archive all simulation files, extracted data, and the final report PDF in the `ex3/` subdirectory.

---

## Operational Reference Guide & Diagnostic Checklist

### Schematic Verification Workflow Summary

The complete schematic verification workflow integrates three operational phases: static topology audit, parametric DC/AC analysis, and dynamic stress testing. This reference guide condenses the methodology into a portable checklist that practitioners can execute on any circuit schematic, regardless of complexity or application domain.

**Phase 1: Static Topology Audit (Pre-Simulation)**

Execute these checks by manual schematic inspection before running any simulation:

1. **Node Connectivity Verification**: Trace every net from source to sink. Confirm no nodes float (unconnected to any active driver or bias network). Floating nodes cause simulation convergence failure and represent real-world faults.

2. **Ground Reference Audit**: Verify exactly one ground symbol exists per isolated circuit domain. Multi-domain schematics (e.g., analog + digital, or primary + secondary isolated sections) require separate ground nets with explicit isolation barriers (transformers, optocouplers, or capacitors).

3. **Power Supply Continuity**: Trace VCC and ground rails across all subcircuits. Verify decoupling capacitors (typically 0.1 µF ceramic) placed adjacent to every active IC power pin. Missing decoupling permits supply-rail ringing and noise injection.

4. **Component Value Sanity Check**: Scan for implausible values (e.g., 1 fF capacitors, 1 TΩ resistors, 1 PH inductors) that likely indicate data entry errors. Compare against E12/E24 standard component series to confirm commercial availability.

5. **Polarity Verification**: Inspect every polarized component (electrolytic capacitors, diodes, transistors, ICs) for correct orientation. Reversed polarity causes immediate failure upon power-up in physical hardware.

6. **Short-Circuit Inspection**: Verify no direct wire connections between VCC and ground nets. Check for accidental net merges by hovering the cursor over nodes and confirming unique net names for distinct circuit junctions.

**Phase 2: Parametric DC/AC Analysis (Simulation Verification)**

Execute these simulations sequentially to characterize nominal operation:

1. **DC Operating Point Analysis**: Run `.op` simulation and verify all node voltages fall within expected ranges. Transistor collectors should sit between cutoff (near VCC) and saturation (near 0.3 V for BJTs, 0.1 V for MOSFETs). Verify quiescent current draw matches hand-calculated predictions within 20%.

2. **Transient Analysis**: Apply nominal AC input signal (100 mV to 1 V amplitude) and verify output waveform replicates input shape without clipping, ringing, or DC drift. Measure rise time, fall time, and propagation delay if relevant to circuit function.

3. **AC Frequency Sweep**: Execute `.ac dec 100 1 100Meg` analysis and extract -3 dB bandwidth, gain-bandwidth product, and phase margin (for feedback circuits). Verify no peaking or resonance artifacts in the frequency response, which indicate instability or parasitic resonances.

4. **Input/Output Impedance Extraction**: Inject 1 A AC current source at input or output nodes and measure resulting AC voltage to calculate impedance magnitude and phase. Verify impedance values match design specifications for signal integrity and matching requirements.

**Phase 3: Dynamic Stress Testing (Boundary Validation)**

Execute these fault injection tests to validate robustness:

1. **Supply Voltage Sweep**: Vary VCC from 0.8× to 1.2× nominal value and verify circuit maintains functional output. Measure current consumption at extremes to ensure compliance with power budget.

2. **Temperature Sweep**: Sweep ambient temperature across -40°C to +85°C (industrial range) or 0°C to +70°C (commercial range). Verify output voltage drift remains below ±5% and no oscillations or instability occur.

3. **Component Tolerance Monte Carlo**: Apply ±5% resistor, ±10% capacitor, and ±20% transistor β variation across 100 simulation runs. Verify performance metrics (gain, bandwidth, output voltage) remain within specification limits for 99% of runs (±3σ).

4. **Single-Fault Injection**: Sequentially open-circuit and short-circuit each passive component, and measure resulting node voltages. Document failure modes that cause catastrophic behavior (overcurrent, overvoltage, smoke) and propose protective design modifications.

5. **Signal Overload Testing**: Increase input signal amplitude until output clipping or distortion exceeds 1% THD (total harmonic distortion). Verify headroom margin sufficient to accommodate expected signal peaks plus 6 dB safety margin.

### Common Schematic Errors and Diagnostic Procedures

**Error: Simulation Fails to Converge**

Symptoms: LTspice displays "timestep too small" or "convergence error" message and terminates simulation prematurely.

Diagnosis: Check for floating nodes, missing ground reference, or topological loops without resistance (e.g., inductor-capacitor loops, ideal voltage sources in parallel). Verify every node connects to ground through at least one DC path (resistor, transistor base-emitter junction, or diode forward path).

Resolution: Add small-value resistors (1 MΩ to 10 MΩ) from floating nodes to ground. Insert series resistance (1 Ω to 10 Ω) in capacitor-inductor loops. Reduce simulation precision by increasing `reltol` from `1e-6` to `1e-4` as a temporary workaround to isolate the problematic subcircuit.

**Error: Output Voltage Incorrect by >50%**

Symptoms: DC operating point node voltages differ drastically from hand calculations, but simulation converges successfully.

Diagnosis: Suspect incorrect component values (e.g., 10k entered as 10m, 1µF entered as 1pF) or wrong transistor model (PNP instead of NPN, N-channel MOSFET instead of P-channel). Verify component values by hovering cursor over each symbol and confirming displayed value matches schematic annotation.

Resolution: Regenerate netlist by selecting `View → SPICE Netlist` and inspect component definitions. Cross-check resistor, capacitor, and transistor model names against intended values. Re-run simulation after corrections and confirm node voltages approach analytical predictions.

**Error: AC Analysis Shows Unexpected High-Frequency Resonance**

Symptoms: Bode plot exhibits sharp gain peaking at frequencies not predicted by hand calculations, often accompanied by phase discontinuities.

Diagnosis: Suspect parasitic inductance in wiring (LTspice does not model PCB trace inductance by default) or missing load capacitance. Resonance frequency calculates as $f_0 = \frac{1}{2\pi\sqrt{LC}}$; measure peak frequency and solve for parasitic L or C.

Resolution: Add explicit parasitic capacitance (1 pF to 10 pF) across high-impedance nodes to model PCB stray capacitance. Add series resistance (10 Ω to 100 Ω) in output paths to dampen resonance. If resonance persists, verify transistor high-frequency model parameters (ft, Cob, Cib) match datasheet specifications.

**Error: Temperature Sweep Causes Oscillation**

Symptoms: Circuit operates stably at 25°C but exhibits spontaneous oscillation at -40°C or +85°C extreme temperatures.

Diagnosis: Transistor gain β increases at cold temperatures and decreases at hot temperatures, potentially altering feedback loop gain margins. Measure loop gain and phase margin at temperature extremes by breaking feedback path and injecting AC test signal.

Resolution: Add frequency compensation capacitor across high-gain stage to reduce bandwidth and stabilize phase margin. Reduce open-loop gain by increasing emitter degeneration resistance. Consult amplifier stability criteria: phase margin must exceed 45° and gain margin must exceed 10 dB at all temperatures.

### Simulation Tool Configuration Best Practices

**LTspice Precision Settings**

Access via `Tools → Control Panel → SPICE`:

- **Relative Tolerance (`reltol`)**: Set to `1e-6` for analog circuits requiring < 0.1% accuracy. Reduce to `1e-4` for troubleshooting convergence issues in complex nonlinear circuits.
- **Absolute Current Tolerance (`abstol`)**: Set to `1e-12 A` for low-noise amplifiers and precision current sources. Increase to `1e-9 A` for power circuits where sub-nanoamp precision is irrelevant.
- **Absolute Voltage Tolerance (`vntol`)**: Set to `1e-9 V` for high-impedance nodes in CMOS and JFET circuits. Increase to `1e-6 V` for general-purpose analog circuits.

**Waveform Plotting Optimization**

- **Time Axis Scaling**: Use `Plot Settings → Horizontal Axis → Log` for visualizing startup transients spanning milliseconds to seconds. Use `Linear` for steady-state AC waveforms.
- **Cursor Measurements**: Press `Ctrl` and left-click waveform to place first cursor, right-click to place second cursor. The readout displays differential voltage (`V1-V2`), time difference (`Δt`), and reciprocal frequency (`1/Δt`).
- **FFT Spectrum Analysis**: Right-click waveform pane, select `View → FFT`, and configure window function to `Hanning` for general-purpose spectral analysis. Use `Blackman-Harris` for precise harmonic distortion measurement.

**Component Library Management**

LTspice's standard library resides in `<install_dir>/lib/cmp/`. To add custom component models:

1. Obtain SPICE model file (`.lib` or `.mod`) from manufacturer website or datasheet.
2. Copy model file to `<install_dir>/lib/sub/` directory for subcircuits or `<install_dir>/lib/cmp/standard.bjt` for transistor models.
3. In schematic, right-click component and edit `Value` field to reference new model name exactly as defined in `.model` statement.
4. Add `.lib <filename.lib>` directive to schematic if model resides in external file.

### Documentation and Archival Standards

Every completed verification exercise must produce three deliverable artifacts:

1. **Annotated Schematic PDF**: Export schematic as vector PDF via `File → Export → PDF`. Annotate PDF with node voltage callouts, critical current paths highlighted in color, and component value tolerance annotations. Include revision number and verification date in schematic title block.

2. **Verification Test Report**: Structure report with sections for Circuit Description, Analytical Predictions, Simulation Results, Deviation Analysis, and Recommendations. Include data tables for all measured parameters, screenshots of critical waveforms, and mathematical derivations for hand calculations. Report length should span 3-5 pages for simple circuits, 10-20 pages for complex multi-stage designs.

3. **Simulation Archive Package**: Create ZIP archive containing `.asc` schematic file, all referenced `.lib` model files, exported waveform data in CSV format, and a `README.txt` file documenting simulation setup instructions, tool versions, and any non-standard configuration parameters. Archive enables reproducibility if circuit requires re-verification months or years later.

Store all deliverables in a version-controlled repository (Git) with commit messages documenting verification pass/fail status, identified issues, and resolution actions. Tag commits with verification milestone identifiers (e.g., `v1.0-verified`, `v1.1-stress-tested`) to enable traceability between schematic revisions and verification evidence.

---

This completes the Operational Verification Labs guide for circuit schematics. The practitioner has now acquired the methodological discipline to read, analyze, simulate, stress-test, and document electrical schematics with professional rigor. These skills form the foundation for advanced circuit design, hardware debugging, and reliability engineering across all domains of analog and digital electronics.
