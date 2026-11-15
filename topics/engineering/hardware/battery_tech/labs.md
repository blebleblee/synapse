# Operational Verification Labs: Battery Tech

## Objective & Operational Lab Setup

This laboratory manual guides hardware practitioners through the empirical characterization, testing, and failure analysis of electrochemical energy storage systems. Lithium-ion, lithium-polymer, nickel-metal-hydride, and lead-acid chemistries dominate portable electronics, electric vehicles, and grid-scale installations, yet their operational behavior under real-world load profiles, thermal stress, and aging mechanisms remains poorly understood by engineers who lack direct bench experience. The objective of these exercises is to construct a repeatable, quantitative methodology for battery cell selection, State of Charge (SOC) estimation accuracy, thermal runaway risk assessment, and end-of-life prediction using equipment available in a standard electronics laboratory.

The physical setup requires a programmable electronic load capable of constant-current (CC), constant-power (CP), and pulsed discharge profiles with sub-milliamp resolution. The BK Precision 8500 series or Keysight N3300 series provide four-quadrant operation for both discharge and charge cycling when paired with a bench power supply. Voltage and current must be logged at minimum 1 Hz sampling rates, preferably 10 Hz for transient capture during pulse loads. A type-K thermocouple affixed to the cell surface with thermally conductive epoxy (Omegatherm 201) feeds a National Instruments USB-TC01 or equivalent data acquisition module. Ambient temperature must remain stable within ±2°C throughout multi-hour discharge cycles; a laboratory oven or thermal chamber (Tenney T10C) enables elevated-temperature aging protocols. Internal resistance measurements demand a 1 kHz AC milliohm meter such as the Keysight 34465A with Kelvin clip leads to eliminate contact resistance artifacts.

Battery Management System (BMS) prototyping requires a development board hosting a microcontroller with integrated 16-bit ADCs, such as the STM32G474 or Texas Instruments BQ76952 analog front-end. Coulomb counting integrates current over time using the trapezoidal rule at 100 ms intervals, accumulating in a 32-bit signed integer to track net charge transferred. Open-circuit voltage (OCV) versus SOC lookup tables derive from manufacturer datasheets but must be empirically validated via slow-rate (C/20) discharge with 1-hour rest periods every 10% SOC decrement to allow concentration gradients within the electrolyte to equilibrate. The Kalman filter framework for SOC estimation fuses coulomb-counting predictions with periodic OCV measurements, requiring tuning of process noise covariance (Q) and measurement noise covariance (R) matrices based on actual sensor variance observed during bench calibration.

Safety infrastructure is non-negotiable when testing lithium chemistries. A fireproof charging bag (LiPo Guard or equivalent) contains cells during cycling, placed inside a fume hood with minimum 100 CFM exhaust to evacuate hydrogen fluoride and other toxic gases released during thermal decomposition. A Class D fire extinguisher rated for metal fires must be mounted within arm's reach. BMS hardware protection enforces absolute voltage limits: 4.20 V per cell for LiCoO₂, 4.35 V for LiNiMnCoO₂ (NMC), 3.65 V for LiFePO₄, and 2.80 V minimum cutoff for all lithium chemistries. Over-temperature shutdown triggers at 60°C for consumer cells and 80°C for automotive-grade pouch cells. Fusing at 1.5× maximum continuous discharge rating prevents wiring faults from escalating into fire.

The analytical spreadsheet framework employs LibreOffice Calc or Microsoft Excel with embedded Python scripts (xlwings library) for numerical integration and curve fitting. Raw voltage, current, and temperature time-series export as CSV from the electronic load's internal datalogger, then import into a master workbook with pre-configured pivot tables for cycle-to-cycle comparison. Peukert's equation, the Shepherd model for voltage sag under load, and Arrhenius-based capacity fade projections require nonlinear least-squares regression using the Solver add-in or scipy.optimize.curve_fit with initial parameter guesses derived from first-principles electrochemistry.

## Exercise 1: Foundational Practical Implementation

The first exercise establishes baseline electrical and thermal characterization of a fresh 18650 cylindrical lithium-ion cell, typically Samsung INR18650-35E (3500 mAh nominal, 8 A maximum continuous discharge) or Panasonic NCR18650B (3400 mAh, 4.8 A maximum). Begin by measuring open-circuit voltage with a calibrated benchtop multimeter after the cell has equilibrated at room temperature for minimum two hours. Record this voltage as the initial SOC reference point using the manufacturer's OCV-SOC curve, typically available in the datasheet as a polynomial fit or lookup table. For the Samsung 35E, an OCV of 3.70 V corresponds to approximately 40% SOC, while 4.15 V indicates 95% SOC. Mark the cell body with a unique identifier using a permanent marker and photograph all visible markings for traceability.

Mount the cell in a custom 18650 holder with nickel-plated copper terminals soldered to 16 AWG silicone-insulated wire. Crimp ferrules onto wire ends and secure into the electronic load's binding posts with sufficient torque to achieve contact resistance below 5 mΩ, verified by the load's internal resistance measurement function. Affix the thermocouple to the cell's center point using a 5 mm bead of thermal epoxy, ensuring the junction makes intimate contact with the steel casing. Insulate the thermocouple with Kapton tape to prevent electrical shorts. Place the assembly inside the fireproof bag with the lid partially open for ventilation, positioning the bag on a non-flammable ceramic tile within the fume hood.

Configure the electronic load for a constant-current discharge at 0.2C rate, calculated as 0.2 × 3500 mAh = 700 mA for the Samsung 35E. This slow discharge rate minimizes concentration polarization and ohmic heating, allowing accurate measurement of true cell capacity without significant voltage depression from internal resistance. Set the cutoff voltage to 2.80 V, below which lithium plating on the anode becomes irreversible. Enable data logging at 10-second intervals, capturing timestamp, terminal voltage, load current, and thermocouple temperature. Initiate the discharge and monitor the voltage profile in real time on the load's display.

During the discharge, observe the characteristic voltage curve shape. The initial rapid voltage drop from OCV to the operating plateau reflects activation polarization as the electrochemical double layer forms at the electrode-electrolyte interfaces. For NMC chemistry, the plateau extends from approximately 3.6 V to 3.3 V over 80% of the discharge, representing the gradual delithiation of the cathode's layered oxide structure. The sharp voltage knee below 3.2 V signals depletion of intercalated lithium, with internal resistance rising exponentially as ion transport becomes diffusion-limited. Record the timestamp when the load triggers the 2.80 V cutoff and calculate total discharge time. Multiply the constant current (0.700 A) by the elapsed time in hours to determine delivered capacity in ampere-hours. For a healthy Samsung 35E, expect 3.4 to 3.5 Ah at 0.2C rate and 25°C ambient.

Temperature rise during discharge provides direct insight into internal resistance and heat generation. The thermocouple trace should show gradual warming from ambient to a peak of 30–35°C near the end of discharge, then cooling during the rest period. Heat generation rate follows I²R losses plus entropic heating from the electrochemical reaction, quantified by the equation P = I(V_oc - V_terminal), where V_oc is the instantaneous open-circuit voltage interpolated from the SOC lookup table. Integrate this power over the discharge duration to calculate total energy dissipated as heat, typically 5–8% of the rated energy capacity for low-rate discharges.

After the discharge completes, allow the cell to rest for one hour while monitoring voltage recovery. The terminal voltage will rebound from 2.80 V to approximately 3.10 V as concentration gradients relax and the electrode surface potential stabilizes. This recovery voltage represents the true open-circuit potential at 0% SOC and anchors the low end of the OCV-SOC calibration curve. Record this voltage and the final thermocouple reading once temperature stabilizes within 0.5°C of ambient.

Recharge the cell using a laboratory power supply with constant-current/constant-voltage (CC/CV) algorithm. Apply 0.5C charge current (1.75 A for the 35E) until terminal voltage reaches 4.20 V, then hold voltage constant while monitoring current decay. Terminate charging when current falls below C/20 (175 mA), indicating full charge. Log the total charge-in current-time integral to compare against the discharge capacity. Charge efficiency, defined as the ratio of discharge capacity to charge capacity, typically ranges from 95% to 98% for lithium-ion cells without significant degradation. Values below 90% indicate elevated self-discharge or internal shorts.

Repeat the discharge-charge cycle three times to condition the cell and verify measurement repeatability. Calculate the mean and standard deviation of discharge capacity across the three cycles. Coefficient of variation should remain below 2% for a healthy cell and stable test setup. Plot all three voltage curves on a single graph with time-aligned x-axes to visualize cycle-to-cycle consistency. Any divergence in plateau voltage or capacity fade exceeding 1% per cycle suggests manufacturing defects or nascent degradation mechanisms.

Perform a 1 kHz AC impedance measurement after the third full charge using the milliohm meter. Connect Kelvin clips directly to the cell terminals, bypassing the wire harness to isolate cell impedance from contact resistance. For the Samsung 35E at 100% SOC and 25°C, expect internal resistance between 18 and 25 mΩ. This value will increase with SOC depletion, reaching 30–40 mΩ at 0% SOC due to reduced ionic conductivity in the depleted electrolyte. Record impedance values at 10% SOC intervals during a subsequent slow discharge to construct an empirical resistance-SOC lookup table for voltage sag prediction under transient loads.

Export all logged data as CSV and import into the master spreadsheet template. The template includes pre-built formulas for Peukert capacity correction, energy efficiency calculation, and thermal resistance estimation. The Peukert equation corrects nominal capacity for discharge rate effects: C_actual = C_nominal × (I_nominal / I_actual)^k, where k is the Peukert exponent typically between 1.05 and 1.15 for lithium-ion cells. Fit the exponent by performing discharges at 0.2C, 0.5C, 1C, and 2C rates, then regressing log(capacity) versus log(current) to extract the slope. This empirical model enables capacity prediction for arbitrary load profiles without running exhaustive discharge tests at every current level.

## Exercise 2: Parameter Variation & Empirical Analysis

The second exercise explores battery performance sensitivity to temperature, discharge rate, and state-of-health degradation through controlled parametric sweeps. Temperature dependence of capacity, internal resistance, and voltage plateau shape derives from Arrhenius-activated ion transport kinetics and solid-state diffusion coefficients within the electrode materials. A thermal chamber capable of ±1°C set-point accuracy across the range -20°C to +60°C enables quantitative measurement of these dependencies without confounding variables from ambient fluctuations.

Begin with the cell at 100% SOC verified by full CC/CV charge to 4.20 V as in Exercise 1. Place the cell and its thermocouple assembly inside the thermal chamber, routing the load wires and thermocouple cable through the sealed port. Set the chamber to 0°C and allow two hours for thermal equilibration, confirmed when the thermocouple reading stabilizes. Discharge at 1C rate (3.5 A for the Samsung 35E) to the 2.80 V cutoff while logging voltage and temperature. The 1C rate introduces significant ohmic and polarization losses, causing the voltage plateau to drop from 3.6 V at 0.2C to approximately 3.4 V at 1C and room temperature. At 0°C, expect the plateau to sag further to 3.2 V with total delivered capacity reduced by 20–30% compared to the 25°C baseline. This capacity loss stems from reduced ionic conductivity in the electrolyte, which exhibits Arrhenius temperature dependence with activation energy around 0.3 eV for typical carbonate-based solvents.

Recharge the cell to 100% SOC, then repeat the 1C discharge at chamber temperatures of 10°C, 25°C, 40°C, and 60°C. Each temperature point requires the two-hour equilibration period before initiating discharge. The 60°C test represents accelerated aging conditions typical of automotive underhood environments and reveals thermal runaway risk margins. At elevated temperatures, capacity initially increases due to enhanced ion mobility, but internal resistance remains relatively constant because ohmic losses in the current collectors dominate over ionic resistance at high SOC. Plot delivered capacity and average discharge voltage versus temperature on a single graph with dual y-axes. Fit a quadratic polynomial to the capacity-temperature relationship to capture the non-monotonic behavior: capacity peaks near 40°C, then declines above 50°C as parasitic side reactions and electrolyte decomposition accelerate.

The voltage sag under load provides a direct measure of internal resistance at each temperature. Calculate area-specific impedance (ASI) using the equation ASI = (V_oc - V_load) / I × A, where A is the electrode active area derived from cell geometry. For an 18650 cell, approximate the cylindrical electrode as having 250 cm² active area. At 25°C and 1C discharge, an initial voltage sag of 0.2 V at 3.5 A current yields ASI = (0.2 V / 3.5 A) × 250 cm² = 14 Ω·cm². Plot ASI versus temperature to quantify the activation energy of ionic conduction. The slope of ln(ASI) versus 1/T gives -E_a/k_B, where k_B is Boltzmann's constant (8.617 × 10⁻⁵ eV/K). Expect activation energies between 0.25 and 0.35 eV for liquid carbonate electrolytes.

Pulse discharge profiling reveals transient impedance components invisible during steady-state testing. Configure the electronic load for a repetitive pulse train: 3.5 A for 10 seconds, then 0 A for 30 seconds, cycling until the cell reaches 2.80 V cutoff. The initial voltage drop at pulse onset reflects purely ohmic resistance in the current collectors and separator, while the gradual sag during the 10-second pulse captures charge-transfer and diffusion polarization. The voltage recovery during the 30-second rest period follows an exponential time constant related to the RC network of double-layer capacitance and charge-transfer resistance. Fit the recovery transient to V(t) = V_final + ΔV × exp(-t/τ), extracting the time constant τ typically ranging from 5 to 15 seconds for lithium-ion cells. Shorter time constants indicate lower charge-transfer resistance and better high-rate performance.

Discharge rate sweeps at constant temperature quantify the Peukert effect and power delivery limits. At 25°C, perform complete discharge cycles at 0.2C, 0.5C, 1C, 2C, and 3C rates (10.5 A for the Samsung 35E, approaching the 8 A maximum continuous rating). Each discharge begins from 100% SOC and terminates at 2.80 V cutoff. Plot delivered capacity versus discharge current on log-log axes. The Peukert equation predicts a linear relationship with slope equal to the Peukert exponent k. Deviations from linearity at high rates signal additional loss mechanisms beyond simple ion transport: lithium plating on the anode below 3.0 V, current density gradients causing localized depletion, and ohmic heating reducing effective capacity. The 3C discharge will likely terminate prematurely below 2.0 Ah due to the 2.80 V cutoff, with significant cell heating to 50°C or higher. This self-heating demonstrates the positive feedback loop in thermal runaway: higher temperature reduces internal resistance slightly but accelerates exothermic side reactions, and if heat generation exceeds passive cooling, temperature rises catastrophically.

Energy density calculations require integrating power over the discharge: E = ∫ V(t) × I(t) dt. For constant-current discharges, this simplifies to E = I × ∫ V(t) dt, where the voltage integral represents the area under the discharge curve. Calculate specific energy in Wh/kg by dividing total energy by cell mass (48 g for an 18650). At 0.2C and 25°C, expect approximately 12.6 Wh (3.5 Ah × 3.6 V average) or 263 Wh/kg. At 3C, the lower average voltage (3.0 V) and reduced capacity (2.0 Ah) yield only 6.0 Wh or 125 Wh/kg, demonstrating the severe energy penalty of high-rate operation. Plot specific energy versus specific power (W/kg) on Ragone plot axes, with power calculated as P = V_avg × I_discharge / mass. The resulting curve traces the fundamental trade-off between energy and power density inherent to electrochemical storage.

Cycling degradation assessment requires accelerated aging under controlled conditions. Perform 100 full charge-discharge cycles at 1C rate and 40°C to simulate six months of daily automotive use. Automate the cycle protocol using the electronic load's internal sequencer: discharge to 2.80 V, rest 5 minutes, charge to 4.20 V at 0.5C then hold until current decays to C/20, rest 5 minutes, repeat. Log capacity and internal resistance every 10 cycles. Healthy cells degrade approximately 0.5% capacity per 100 cycles under these conditions, following a square-root-of-time relationship due to solid-electrolyte interphase (SEI) layer growth on the anode. Plot capacity retention versus cycle number and fit to the model: Q(n) = Q_0 × (1 - a√n), where Q_0 is initial capacity and a is the degradation coefficient. Extrapolate to 80% capacity (conventional end-of-life threshold) to predict cycle life. For the Samsung 35E under these test conditions, expect end-of-life around 800–1000 cycles, scaling to 1500–2000 cycles under gentler 25°C operation.

Resistance growth during cycling provides an orthogonal degradation metric. Measure AC impedance at 100% SOC after every 20 cycles. Plot resistance versus cycle number on semi-log axes; expect exponential growth once the SEI layer transitions from a thin passivation film to a thick resistive barrier. Resistance typically increases by 30–50% at 80% capacity retention, and this impedance rise limits power delivery before capacity fade becomes problematic. For automotive applications, the resistance-limited power fade defines end-of-life more stringently than the capacity threshold.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The third exercise deliberately pushes battery cells beyond normal operating envelopes to map failure modes, quantify safety margins, and validate protection circuitry. These tests consume cells and present fire and toxic gas hazards, demanding rigorous safety protocols including fireproof containment, exhaust ventilation, continuous video monitoring, and emergency shutdown capability via remotely actuated circuit breakers.

Over-discharge testing determines cell behavior below the 2.80 V minimum and the irreversibility threshold for copper dissolution from the anode current collector. Begin with a cell at 0% SOC verified by discharge to 2.80 V followed by one-hour rest. Override the electronic load's voltage limit to 0 V and discharge at 0.2C for an additional 30 minutes, forcing the terminal voltage to approximately 1.5 V. This deep discharge causes the copper foil current collector to oxidize electrochemically, dissolving Cu²⁺ ions into the electrolyte. The dissolved copper migrates to the cathode and plates out during subsequent charging, creating internal shorts and dendrites.

After the over-discharge, rest the cell for one hour and measure open-circuit voltage. Expect 2.0 to 2.5 V rather than the normal 3.1 V at 0% SOC, indicating permanent cell damage. Attempt to recharge using the standard CC/CV protocol to 4.20 V while monitoring voltage, current, and temperature closely. The voltage will rise abnormally fast during the initial CC phase, reaching 4.20 V after transferring only 20–30% of the rated capacity. This premature voltage rise stems from the plated copper shorts bypassing active material, making the cell appear full when it remains deeply depleted. The cell may also heat excessively (>45°C) during charging due to current shunts through the internal shorts. Terminate charging if temperature exceeds 60°C or if the cell case begins to swell.

Discharge the damaged cell at 0.2C and compare capacity to the pre-damage baseline. Expect 50–70% capacity retention after a single over-discharge to 1.5 V, with most of the loss attributed to stranded lithium tied up in the SEI layer and plated copper consuming cyclable lithium inventory. Repeat the discharge-charge cycle five times to quantify degradation rate. Heavily over-discharged cells continue to lose capacity with each cycle as the internal shorts propagate. This exercise demonstrates why BMS protection must guarantee hard cutoffs at 2.80 V with sufficient margin to account for voltage sag under load and cell-to-cell imbalance in multi-cell packs.

Over-charge testing maps thermal runaway thresholds and venting behavior. Fully charge a fresh cell to 4.20 V, then continue charging at 0.5C with the voltage limit disabled. Monitor terminal voltage, cell surface temperature, and the load current continuously at 10 Hz sampling. The voltage will rise approximately linearly at 50 mV per minute above 4.20 V as lithium metal begins plating on the anode and the cathode over-delithiates into unstable phases. At 4.35 V, exothermic decomposition of the electrolyte initiates, visible as a sharp inflection in the temperature trace. By 4.50 V, the cell enters thermal runaway: temperature rises at >10°C per minute, current consumption increases despite voltage saturation, and the cell case swells from internal gas pressure.

Immediately terminate charging when the temperature rise rate exceeds 5°C per minute or when voltage reaches 4.60 V, whichever occurs first. Remove the cell from the electronic load using insulated tongs and place it in a sand-filled steel bucket to contain any fire or venting. Allow cooling under observation for 30 minutes. Post-mortem examination will reveal a swollen cell case, ruptured safety vent at the positive terminal, and white electrolyte residue from vented gases. This destructive test calibrates the BMS over-voltage threshold: for LiCoO₂ chemistry, 4.25 V absolute maximum; for NMC, 4.30 V; and for LiFePO₄, 3.70 V. Protection circuitry must trigger at least 100 mV below thermal runaway onset to provide margin for voltage measurement error and cell-to-cell variation.

Short-circuit testing measures worst-case discharge current and validates fuse sizing. Construct a test rig using a 1-meter length of 12 AWG copper wire with calibrated resistance 5 mΩ. This wire serves as both the short-circuit load and a current shunt for measurement. Charge the cell to 100% SOC and measure open-circuit voltage. Connect the cell terminals to the wire ends using insulated alligator clips, then simultaneously attach a high-current hall-effect sensor (Allegro ACS770) around the wire to log discharge current. The initial short-circuit current will spike to 80–100 A for the Samsung 35E, limited only by the cell's internal resistance (20 mΩ) plus the wire resistance (5 mΩ). This current decays exponentially with a time constant of approximately 2 seconds as the cell voltage collapses and internal temperature rises.

Record the current waveform for 10 seconds, then immediately disconnect the short circuit. Measure cell voltage and temperature. The voltage will have dropped to below 3.0 V, and surface temperature may reach 80°C from the I²R heating pulse. Allow the cell to cool and rest for one hour, then measure capacity degradation by performing a full discharge at 0.2C. Expect 10–20% capacity loss from a single 10-second short circuit due to SEI layer damage and lithium plating. This exercise quantifies the energy let-through that fuses must survive during overcurrent faults. Size fuses at 1.5× the maximum continuous discharge rating (12 A for the Samsung 35E) to protect against sustained overloads while tolerating transient inrush currents.

Nail penetration testing simulates catastrophic mechanical damage and internal short circuits. This test requires extensive safety precautions: perform inside a fireproof containment vessel (steel ammunition box) with remote-actuated nail penetration mechanism, surrounded by sand, under video surveillance, in a fume hood with maximum exhaust. Charge the cell to 100% SOC and position it horizontally in the containment vessel. The penetration mechanism drives a 3 mm diameter steel nail through the cell's center at controlled speed (1 mm/s) using a pneumatic actuator triggered from outside the hood. Monitor cell voltage and temperature via long wire leads exiting the containment vessel.

As the nail penetrates the separator layer, the voltage collapses instantly to near zero as the cathode and anode short internally. Temperature spikes at >50°C per second, and the cell may eject flames and smoke within 2–5 seconds. The thermal runaway progresses through exothermic decomposition of the cathode and electrolyte, reaching peak temperatures exceeding 600°C. Maintain video recording throughout the event and for 10 minutes afterward. Do not open the containment vessel for 30 minutes to allow cooling and dissipation of toxic gases. This destructive test validates that BMS protection cannot prevent thermal runaway from mechanical damage; physical protection (steel enclosures, crush-resistant casings) is mandatory for safety.

Thermal chamber oven testing maps abuse tolerance at temperature extremes. Place a fully charged cell in a programmable oven and ramp temperature at 5°C per minute from room temperature to 150°C while monitoring cell voltage and case temperature via thermocouple. At approximately 110°C, the internal pressure relief vent will burst, audible as a sharp pop and visible as white smoke from vented electrolyte vapor. Cell voltage collapses to zero as the electrolyte evaporates. Continue heating to 150°C and hold for 30 minutes to ensure the cell does not enter thermal runaway. Cells that pass this test without fire or explosion meet UN 38.3 transportation safety standards. Cells that ignite or explode indicate insufficient venting capability or unstable cathode chemistry; reject such cell models from designs.

Recovery protocols after abuse testing assess whether cells retain partial function or pose ongoing hazards. After each stress test that does not result in venting or fire, attempt to recharge the cell to 50% SOC using a reduced current limit (0.1C) while monitoring for abnormal voltage response or temperature rise. Cells that charge smoothly to 4.00 V and discharge with >50% capacity retention may be cycled at reduced rates for non-critical applications. Cells that exhibit voltage instability, excessive self-discharge (>5% per day), or swelling during charging must be safely discharged to 0 V and disposed of through battery recycling channels. Never re-use cells that have vented gases or shown evidence of internal shorts.

## Operational Reference Guide & Diagnostic Checklist

This reference section consolidates critical parameters, failure signatures, and diagnostic procedures for rapid troubleshooting in development and production environments.

**Lithium-Ion Cell Specifications by Chemistry:**
- **LiCoO₂ (Cobalt):** 3.70 V nominal, 4.20 V max charge, 2.80 V min discharge, 150–200 Wh/kg, 1C standard rate, high energy density, thermal runaway at 150°C
- **LiNiMnCoO₂ (NMC):** 3.70 V nominal, 4.20–4.35 V max (grade dependent), 2.50–2.80 V min, 180–220 Wh/kg, 2–3C standard rate, balanced performance, thermal runaway at 210°C
- **LiFePO₄ (Iron Phosphate):** 3.20 V nominal, 3.65 V max charge, 2.50 V min discharge, 90–120 Wh/kg, 5–10C capable, excellent safety, thermal runaway at 270°C, flat discharge curve complicates SOC estimation
- **LiNiCoAlO₂ (NCA):** 3.65 V nominal, 4.20 V max charge, 2.50 V min discharge, 200–250 Wh/kg, 2–3C standard rate, highest energy density, thermal runaway at 140°C, requires precision BMS

**BMS Protection Thresholds (Conservative Design):**
- Over-voltage: 4.15 V per cell for NMC/NCA, 3.60 V for LFP, with 50 mV hysteresis
- Under-voltage: 3.00 V per cell, with load disconnect at 2.90 V
- Over-current discharge: 1.5× maximum continuous rating, 100 ms delay
- Over-current charge: 1.0× maximum continuous rating, 1 second delay
- Over-temperature discharge: 60°C, with 5°C hysteresis
- Over-temperature charge: 45°C, with 5°C hysteresis
- Cell imbalance: 50 mV maximum delta between cells in series string

**Internal Resistance Diagnostic Ranges (18650 Form Factor, 100% SOC, 25°C):**
- New cell, <10 cycles: 15–25 mΩ
- Mid-life, 200–500 cycles: 25–40 mΩ
- End-of-life, >800 cycles: 40–60 mΩ
- Failing cell, internal short: <10 mΩ or >100 mΩ
- Measurement technique: 1 kHz AC milliohm meter, Kelvin connections, ±0.1 mΩ accuracy

**Capacity Fade Diagnostic Procedure:**
1. Fully charge cell to manufacturer's maximum voltage using CC/CV protocol
2. Rest cell for 2 hours at room temperature to allow concentration gradients to equilibrate
3. Discharge at 0.2C to minimum voltage cutoff (2.80 V for Li-ion)
4. Calculate delivered capacity: Q = I × t, where I is constant current and t is discharge time in hours
5. Compare to nameplate capacity: fade percentage = 100 × (Q_nameplate - Q_measured) / Q_nameplate
6. Acceptable fade rates: <2% per 100 cycles for consumer electronics, <0.5% per 100 cycles for automotive
7. Investigate if fade exceeds 5% in first 50 cycles (manufacturing defect) or accelerates beyond square-root trend (thermal abuse)

**Self-Discharge Rate Measurement:**
1. Charge cell to 100% SOC and measure open-circuit voltage immediately after charging
2. Disconnect all loads and monitoring equipment except high-impedance voltage logger (>10 MΩ input impedance)
3. Store cell at constant temperature (25°C ± 1°C) for 30 days in sealed, non-conductive container
4. Measure final open-circuit voltage after 30-day storage period
5. Convert voltage drop to SOC loss using OCV-SOC lookup table
6. Calculate self-discharge rate as percentage per month: R = 100 × ΔQ / Q_nameplate / 30 days
7. Acceptable rates: <3% per month for consumer cells, <1% per month for precision applications
8. Rates exceeding 5% per month indicate internal shorts or electrolyte decomposition

**Thermal Runaway Warning Signs:**
- Voltage rise >50 mV above maximum charge voltage despite constant-current limit active
- Temperature rise >5°C per minute during charging or >10°C per minute during discharge
- Cell case swelling visible as rounded edges or convex surfaces (measure with calipers)
- Hissing or gas venting sounds from pressure relief valve
- Sweet or solvent odor indicating electrolyte vapor leakage
- Resistance drop below 10 mΩ suggesting internal short formation
- Immediate actions: disconnect charge/discharge current, move to fireproof containment, evacuate area, activate ventilation, monitor remotely

**Coulomb Counting SOC Estimation Algorithm (Embedded C for STM32):**

```c
// Battery SOC estimation using trapezoidal coulomb counting with periodic OCV reset
// Requires 16-bit ADC for current and voltage sensing at 100 ms interval

#include "stm32g4xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

#define NOMINAL_CAPACITY_MAH 3500.0f  // Samsung INR18650-35E
#define COULOMB_EFFICIENCY 0.98f      // Charge/discharge efficiency
#define ADC_RESOLUTION 65536.0f       // 16-bit ADC
#define VREF 3.3f                     // ADC reference voltage
#define CURRENT_SENSE_GAIN 0.1f       // Ohms, shunt resistor
#define SAMPLE_INTERVAL_SEC 0.1f      // 100 ms sampling
#define OCV_RESET_CURRENT_MA 10.0f    // Rest detection threshold
#define OCV_RESET_DURATION_SEC 3600.0f // 1 hour rest before OCV reset

// OCV-SOC lookup table for NMC chemistry (11 points, 0-100% SOC)
static const float ocv_table[11] = {
    3.100f, 3.400f, 3.550f, 3.650f, 3.700f, 3.750f, 
    3.820f, 3.950f, 4.050f, 4.150f, 4.200f
};

typedef struct {
    float soc_percent;           // State of charge, 0-100%
    float coulombs_accumulated;  // Net charge transferred, coulombs
    float voltage_terminal;      // Current terminal voltage
    float current_amps;          // Current through cell, positive = discharge
    uint32_t rest_timer_sec;     // Time at rest for OCV reset
    bool is_at_rest;             // Flag indicating rest condition
} battery_state_t;

static battery_state_t batt_state = {
    .soc_percent = 50.0f,
    .coulombs_accumulated = 0.0f,
    .voltage_terminal = 3.70f,
    .current_amps = 0.0f,
    .rest_timer_sec = 0,
    .is_at_rest = false
};

// Interpolate SOC from OCV using lookup table
float soc_from_ocv(float voltage) {
    if (voltage <= ocv_table[0]) return 0.0f;
    if (voltage >= ocv_table[10]) return 100.0f;
    
    for (int i = 0; i < 10; i++) {
        if (voltage >= ocv_table[i] && voltage <= ocv_table[i+1]) {
            float soc_low = i * 10.0f;
            float soc_high = (i + 1) * 10.0f;
            float voltage_range = ocv_table[i+1] - ocv_table[i];
            float voltage_offset = voltage - ocv_table[i];
            return soc_low + (voltage_offset / voltage_range) * 10.0f;
        }
    }
    return 50.0f; // Fallback if table lookup fails
}

// Update SOC estimation, call at 100 ms interval
void battery_soc_update(float voltage_raw_adc, float current_raw_adc) {
    // Convert ADC readings to physical units
    float voltage = (voltage_raw_adc / ADC_RESOLUTION) * VREF * 2.0f; // Voltage divider R1=R2
    float current = ((current_raw_adc / ADC_RESOLUTION) * VREF) / CURRENT_SENSE_GAIN;
    
    batt_state.voltage_terminal = voltage;
    batt_state.current_amps = current;
    
    // Coulomb counting with trapezoidal integration
    float coulombs_delta = current * SAMPLE_INTERVAL_SEC;
    batt_state.coulombs_accumulated += coulombs_delta * COULOMB_EFFICIENCY;
    
    // Convert coulombs to SOC percentage
    float capacity_coulombs = NOMINAL_CAPACITY_MAH * 3.6f; // mAh to coulombs
    float soc_delta = (coulombs_delta / capacity_coulombs) * 100.0f;
    batt_state.soc_percent -= soc_delta; // Negative because discharge reduces SOC
    
    // Clamp SOC to valid range
    if (batt_state.soc_percent > 100.0f) batt_state.soc_percent = 100.0f;
    if (batt_state.soc_percent < 0.0f) batt_state.soc_percent = 0.0f;
    
    // Detect rest condition for OCV reset
    if (fabsf(current) < (OCV_RESET_CURRENT_MA / 1000.0f)) {
        batt_state.rest_timer_sec += (uint32_t)SAMPLE_INTERVAL_SEC;
        batt_state.is_at_rest = true;
    } else {
        batt_state.rest_timer_sec = 0;
        batt_state.is_at_rest = false;
    }
    
    // Reset SOC from OCV after prolonged rest
    if (batt_state.rest_timer_sec >= OCV_RESET_DURATION_SEC) {
        float soc_from_voltage = soc_from_ocv(voltage);
        batt_state.soc_percent = soc_from_voltage;
        batt_state.coulombs_accumulated = 0.0f; // Reset accumulator
        batt_state.rest_timer_sec = 0;
    }
}

// Read current SOC estimate
float battery_get_soc(void) {
    return batt_state.soc_percent;
}

// Read current terminal voltage
float battery_get_voltage(void) {
    return batt_state.voltage_terminal;
}

// Read instantaneous current
float battery_get_current(void) {
    return batt_state.current_amps;
}

// Check if battery is at rest for OCV measurement
bool battery_is_at_rest(void) {
    return batt_state.is_at_rest;
}
```

**Peukert Equation Capacity Correction Spreadsheet Formula:**
In cell B2, enter the nominal capacity (e.g., 3.5 for 3500 mAh). In cell B3, enter the Peukert exponent (typically 1.05 to 1.15, measure empirically). In cell A6 onward, list discharge currents (0.7, 1.75, 3.5, 7.0, 10.5 A). In cell B6, enter the formula: `=$B$2 * (1 / A6)^($B$3 - 1)` and copy down. This calculates effective capacity at each discharge rate. Plot column A versus column B on log-log axes to verify linearity.

**Ragone Plot Energy-Power Density Calculation:**
For each discharge rate test, calculate average voltage as the time-weighted mean: `V_avg = SUMPRODUCT(voltage_column, time_delta_column) / SUM(time_delta_column)`. Calculate total energy: `E_Wh = V_avg * I_discharge * t_hours`. Calculate specific energy: `E_specific = E_Wh / cell_mass_kg`. Calculate average power: `P_avg = E_Wh / t_hours`. Calculate specific power: `P_specific = P_avg / cell_mass_kg`. Plot E_specific (y-axis, log scale) versus P_specific (x-axis, log scale) with data points labeled by discharge rate.

**Failure Mode Diagnosis Decision Tree:**
- **Voltage >4.3 V during charge:** Over-charge event, check BMS voltage sensing calibration, verify charge current cutoff algorithm, inspect for control loop failures
- **Voltage <2.5 V at rest:** Over-discharge damage, measure internal resistance (expect >50 mΩ), attempt recovery charge at 0.1C, monitor for gas venting, likely permanent capacity loss >30%
- **Capacity fade >10% in <50 cycles:** Manufacturing defect or severe thermal abuse, check cycle temperature logs, inspect for electrolyte leakage at vents, reject cell batch
- **Resistance increase >50% at mid-life:** SEI layer overgrowth or current collector corrosion, correlate with average cycle temperature and depth-of-discharge, reduce charge rate to 0.3C to extend remaining life
- **Self-discharge >5% per month:** Internal micro-short from dendrite formation or separator degradation, do not return to service, schedule immediate replacement
- **Cell swelling or bulging:** Gas generation from electrolyte decomposition, immediate safety hazard, discharge to 0 V in fireproof container, do not puncture, recycle through hazmat channels

This operational verification framework equips hardware practitioners with quantitative methodologies for battery selection, performance prediction, and failure analysis grounded in physical electrochemistry and validated through direct bench measurement.
