# Lesson 4: Battery Management Systems, Pack Design, Applications

## 1. First-Principles Intuition & Invariants

A battery pack is not simply a collection of cells wired together. It is a tightly coupled electrochemical, thermal, and electrical system where the state of each cell propagates through interconnected network paths, and decisions made in one region of the pack cascade through voltage dividers, current distributors, and thermal conductance networks to affect the entire ensemble. The Battery Management System (BMS) is the nervous system that must sense, estimate, and control this multidimensional state space in real time—often with incomplete information, nonlinear dynamics, and severe computational constraints.

The fundamental challenge stems from three irreducible facts about electrochemical cells. First, the internal electrochemical state—the true State of Charge (SOC), State of Health (SOH), and State of Energy (SOE)—cannot be directly measured. We observe only terminal voltage, current, and temperature from external pins. Second, cells age heterogeneously; even cells from the same manufacturing batch diverge in capacity, internal resistance, and power capability over hundreds or thousands of cycles. Third, temperature couples tightly with all other phenomena: it drives diffusion kinetics, alters resistance, shifts the open-circuit voltage (OCV) curve, and accelerates degradation.

Consider a 48V lithium battery pack with twelve cells in series. Each cell nominally delivers 4.2V at full charge, but manufacturing tolerances ensure that identical charging current produces slightly different voltage trajectories across the twelve cells. One cell might reach 4.19V while another hits 4.23V. If you apply a fixed voltage across all twelve in series (58V total), cell imbalance grows: the weaker cell (lower capacity or higher resistance) charges more slowly, so it experiences less heat dissipation per unit current, altering its temperature trajectory relative to neighbors. The weaker cell gradually falls behind, its OCV curve drops relative to the stronger cells, and the voltage difference widens. After tens of cycles, that cell becomes a bottleneck: the entire pack's usable capacity is now limited by the weakest link.

This is why cell balancing exists. Balancing redistributes charge among cells to equalize SOC and voltage, compensating for manufacturing spread and degradation. But balancing itself is a control problem: you must decide which cells to balance, when to balance them, how much energy to dissipate in the balancing resistors or switches, and how aggressively to push without damaging cells or wasting energy.

State estimation—computing SOC, SOH, and SOE from voltage, current, and temperature measurements—is the foundation upon which all BMS decisions rest. SOC (typically expressed as a percentage, 0–100%) represents the fraction of nominal capacity currently stored in the pack. SOH (also 0–100%) reflects the degradation of the pack relative to its original capacity. SOE measures the extractable energy, which depends not only on SOC but also on the current discharge rate and temperature: a cold pack at 50% SOC might deliver only 30% of its rated energy at high current.

The BMS must also manage charge and discharge rates according to electrochemical constraints. Fast charging accelerates lithium plating on the anode if the cell potential falls too low, creating internal short-circuit paths that degrade the cell. Aggressive discharge at low temperatures increases resistive heating and can temporarily raise internal pressure. The BMS enforces rate limits—maximum charge current (CC phase), maximum discharge current—and transitions between operational modes (pre-charge, constant-current, constant-voltage, balancing, resting) to keep cells within safe electrochemical windows.

Thermal management represents perhaps the most physically intricate coupling. Joule heating from internal resistance scales with I²R. Electrochemical polarization (overpotential) during charge and discharge also generates heat. In a high-discharge-current scenario—say, 200A continuous from a 100Ah pack—the cell produces roughly 20–40kW of thermal power per module. Without active cooling (liquid or forced-air), cells reach 50–60°C, at which point diffusion-limited solid-state phenomena become significant, aging accelerates, and power capability begins to decline. The BMS must coordinate with thermal subsystems: reading temperature sensors embedded in the pack, computing thermal resistance paths to ambient, predicting cell temperatures under transient load profiles, and issuing commands to cooling loops or fans.

Pack configuration—how cells are wired (series, parallel, or mixed)—fundamentally shapes the BMS architecture. A series configuration (cells end-to-end, voltages add) provides high voltage but suffers from cell-to-cell imbalance vulnerability: one degraded cell limits the whole pack. A parallel configuration (cells in parallel, currents sum) offers redundancy—a failing cell doesn't halt the pack—but demands precise voltage regulation to prevent current hogging by cells with lower internal resistance. Most practical packs use a hierarchical structure: cells grouped into parallel strings, then multiple strings wired in series, creating a module; modules stacked in series to reach the target voltage. This topology allows each parallel string to have a local balancing controller, reducing wiring complexity.

The BMS hardware itself is a real-time embedded system. A central controller (often a microcontroller or small SoC like an ARM Cortex-M4 or Cortex-A7) continuously reads analog signals from temperature sensors, current shunts, and cell voltage measurement ICs. It processes these streams through state estimators (Kalman filters, lookup tables, particle filters), enforces control policies (charge rate limits, balancing algorithms, thermal commands), and communicates pack state via CAN, LIN, or proprietary serial links to the external charger or vehicle/grid system. All this must happen reliably in environments with extreme vibration, temperature swings from −20°C to +60°C, and stringent safety regulations.

## 2. Core Architecture & Mechanics

### 2.1 Cell Voltage and State-of-Charge Measurement

The most direct measurement in a BMS is cell voltage. A voltage divider or dedicated multi-cell monitor IC samples the potential across each cell (or groups of cells) relative to a pack ground reference. In a series string of twelve 4.2V cells, the lowest cell sits at 0V (the negative terminal), the next at ~4.2V, the third at ~8.4V, and the twelfth at ~50.4V. Measuring 4.2V across the twelfth cell requires a differential amplifier with high common-mode rejection ratio (CMRR) to reject the 50V of common-mode signal and extract a 4.2V differential signal with millivolt-level precision.

Practical BMS implementations use dedicated ICs—for example, the TI BQ769x0 family or the Analog Devices LTC6811—that integrate a primary controller and a daisy-chained array of secondary monitoring chips, each reading 6–12 cell voltages via ADC inputs. These slaves communicate back to the master via a differential isochronous bus (often a floating, isolated serial line), ensuring that each voltage is timestamped to microsecond accuracy. The architecture is critical: if voltage measurements across twelve cells arrive at different times, you introduce artificial imbalances in the state estimator.

SOC estimation begins with a simple integral: the Coulomb-counting method. As current I flows into or out of the pack over time, the charge ΔQ = ∫I dt accumulates. Dividing by the nominal pack capacity C_nominal gives ΔSOC = ΔQ / C_nominal. Starting from a known SOC (e.g., 0% when the pack is discharged to a minimum voltage), you propagate SOC forward by accumulating current:

SOC(t) = SOC(t₀) + (1/C_nominal) ∫ᵗ₀ᵗ I(τ) dτ

This approach is simple and computationally cheap, requiring only integration. However, it suffers from two fatal flaws in practice. First, the current measurement itself drifts. A 0.1mV offset in the current shunt amplifier translates to a 5A bias if the shunt is 20mΩ and the amplifier gain is 50. Over a full charge-discharge cycle spanning 20 hours, this bias integrates to an SOC error of 2–5%. Second, the relationship between SOC and terminal voltage (the open-circuit voltage curve, OCV) is nonlinear and hysteretic: the OCV for a given SOC differs depending on whether the cell is being charged or discharged, and varies with temperature. Coulomb counting alone cannot correct for these errors.

The remedy is to fuse Coulomb counting with periodic OCV measurements. During a rest period (vehicle parked, grid load stable), the cell current drops to near zero, and the terminal voltage converges to the open-circuit voltage over a time constant of seconds to minutes depending on the cell's RC time constant. The BMS measures this stabilized voltage and looks it up in a temperature-corrected OCV table, extracting a reference SOC. The estimator then resets its Coulomb-counter to this reference and resumes integration. In practice, such reset events occur every few hours of operation, bounding the cumulative Coulomb-counter drift.

For continuous, real-time SOC estimation without waiting for rest periods, the BMS employs a Kalman filter or extended Kalman filter (EKF). The underlying model captures the cell's electrochemical behavior as a circuit: an ideal voltage source (the OCV, which is a function of SOC and temperature) in series with an internal resistance and a parallel RC network representing the electrochemical double layer and bulk electrolyte impedance.

The circuit model is:

V_terminal = V_OCV(SOC, T) − I·R_internal − V_RC

where V_OCV is the open-circuit voltage (nonlinear, temperature-dependent), I is the applied current (positive for discharge), R_internal is the ohmic resistance, and V_RC is the voltage across a parallel RC network:

dV_RC/dt = −V_RC / (R_RC · C_RC) + I · R_RC / C_RC

This is a first-order linear differential equation governing the RC transient. During a step change in current—say, from 0A to 100A discharge—the terminal voltage drops instantaneously by I·R_internal, then decays exponentially toward V_OCV − I·(R_internal + R_RC) over a time constant τ = R_RC · C_RC, typically 10–100 seconds for lithium cells.

The Kalman filter fuses multiple measurement streams to estimate the true SOC despite noise and model uncertainty. The state vector includes SOC and the RC voltage V_RC. At each timestep, the filter performs a prediction step (integrating the differential equations with current as input) and an update step (comparing predicted terminal voltage to measured voltage and correcting the SOC estimate if they diverge). The strength of the EKF is that it weights measurements and model predictions according to their respective uncertainties, optimally combining them.

In pseudocode:

```
function EKF_SOC_Update(state, current, measured_voltage, dt):
  // Prediction: propagate state forward
  state.SOC += (current / C_nominal) * dt  // Coulomb counting
  state.V_RC *= exp(-dt / (R_RC * C_RC))   // RC decay
  state.V_RC += current * R_RC * (1 - exp(-dt / (R_RC * C_RC)))
  
  // Predicted measurement
  V_OCV = OCV_lookup(state.SOC, temperature) 
  V_predicted = V_OCV - current * R_internal - state.V_RC
  
  // Measurement residual
  residual = measured_voltage - V_predicted
  
  // Kalman gain (simplified)
  K = P / (P + measurement_noise_variance)
  
  // Update state
  state.SOC += K * residual / (dV_OCV/dSOC * C_nominal)
  state.V_RC += K * residual
  
  // Covariance update (omitted for brevity)
  return state
```

The OCV lookup table is central to this estimator. Manufacturers provide discharge curves at multiple temperatures (−10°C, 0°C, 25°C, 40°C, 60°C) where voltage is measured at 10% SOC intervals (0%, 10%, 20%, ..., 100%) under near-zero current. The BMS interpolates between temperature points and uses polynomial fitting or cubic spline interpolation to refine intermediate SOC values. Accuracy of the OCV table directly determines SOC estimation accuracy; errors as small as 5mV in the OCV can produce 1–2% SOC errors.

### 2.2 State of Health and Capacity Estimation

State of Health (SOH) measures how much the pack has degraded. Lithium cells lose capacity through multiple failure modes: solid-electrolyte interphase (SEI) growth consumes cyclable lithium and increases impedance; transition-metal dissolution from the cathode reduces active sites; copper dendrite growth can eventually pierce the separator, causing thermal runaway. Over thousands of cycles, capacity gradually declines. A pack that stored 100Ah when new might drop to 95Ah after 500 cycles, 80Ah after 2000 cycles, and reach end-of-life at ~70Ah (manufacturers typically define end-of-life as 80% of initial capacity, though some applications tolerate lower thresholds).

SOH is defined as the ratio of current nominal capacity to initial capacity:

SOH = C_current / C_initial × 100%

The challenge is that C_current cannot be directly measured in real time; it must be estimated. The Coulomb counter provides a proxy: at the end of a full discharge (pack voltage reaches minimum threshold), the total charge delivered is approximately the current capacity. However, this requires regular full discharge-recharge cycles, which is impractical in automotive and grid applications. Instead, the BMS uses incremental capacity analysis or differential voltage analysis.

Incremental capacity analysis plots dQ/dV (the change in charge per unit voltage) versus voltage, which is related to the differential capacity curve of the cell. Over cycle life, the shape of the incremental capacity curve changes due to loss of cyclable lithium and cathode material; peaks shift and broaden. By comparing the current incremental capacity curve to a reference curve measured at 0 cycles (new battery), the BMS can estimate capacity fade. This method requires high-resolution voltage measurements (sub-millivolt precision) and careful filtering to suppress noise, but it avoids needing a full discharge.

A simpler, more robust approach used in many automotive BMS implementations is to track the accumulated charge delivered over a fixed voltage window. For example, during discharge from 4.0V to 3.0V (a window where the OCV-SOC relationship is relatively linear), the BMS records total Coulombs delivered. This "partial capacity" is a proxy for true capacity; if partial capacity declines by 15%, the full capacity has likely declined similarly. The BMS updates an SOH variable periodically (e.g., after every 10 full charge-discharge cycles):

SOH_new = (Q_delivered_in_window / Q_reference_in_window) × SOH_old

where Q_reference_in_window is the Coulombs delivered in that window when the pack was new (either measured in the factory or provided by the OEM.

Thermal effects couple with SOH estimation. Capacity fade accelerates with temperature; a cell at 40°C degrades roughly twice as fast as one at 25°C. The BMS must track not just cycle count, but also the thermal history—the sum of time spent at elevated temperature weighted by degradation rate. Calendar aging (capacity loss simply sitting on a shelf) also occurs; after two years at 25°C, a pack loses 2–3% capacity even if never cycled. Some advanced BMS implementations integrate this into a degradation model:

dSOH/dt = −k_cycle · |I| / C_nominal − k_calendar · exp(−E_a / (k_B · T))

where k_cycle is a cycle-life coefficient, E_a is an activation energy (~20 kJ/mol for lithium), k_B is Boltzmann's constant, and T is absolute temperature. This model predicts SOH as a function of both cycling and calendar aging, allowing the BMS to issue warnings when EOL is approaching.

### 2.3 Cell Balancing Architectures

Cell balancing corrects for imbalances that arise from manufacturing tolerances, localized temperature differences, and heterogeneous aging. Without balancing, the weakest cell (lowest capacity or highest resistance) reaches its minimum voltage threshold first during discharge, forcing the pack to stop even though stronger cells retain significant energy. Similarly, the cell with lowest capacity reaches its maximum voltage first during charge, forcing cutoff before the pack reaches nominal capacity.

Two primary balancing topologies exist: passive and active. Passive balancing dissipates excess charge from overcharged or over-voltage cells through series resistors (typically 5–100Ω, dissipating 10–100mW per cell). Active balancing uses power converters (switched capacitor networks or small DC-DC converters) to transfer charge between cells.

Passive balancing is simpler and highly reliable. Each cell (or cell group) connects to a balancing resistor through a MOSFET switch. When a cell voltage exceeds a threshold (e.g., 4.15V for a 4.2V nominal cell), the BMS controller closes the MOSFET, shunting current through the resistor. The resistor dissipates power as heat:

P = V² / R

For a 4.15V cell with a 10Ω resistor, P = 17.2 / 10 = 1.72W. With a balancing resistor integration on the cell monitor IC or PCB, this heat is managed via the PCB's copper area or thermal vias. The energy dissipated is wasted, but the simplicity is often worth the cost.

Active balancing preserves the dissipated energy by transferring it to under-charged cells. A typical architecture uses a flyback converter or a switched-capacitor network. Consider a switched-capacitor balancer: a capacitor is alternately connected to an overcharged cell (to charge the capacitor) and an under-charged cell (to discharge the capacitor). By controlling the switching frequency and duty cycle, you regulate the charge transfer rate. Over several minutes, this redistributes charge from high cells to low cells. The energy is lossless (except for MOSFET on-resistance and capacitor ESR losses, typically 1–3%), so active balancing is preferred for high-power packs where energy efficiency matters.

The balancing algorithm—the logic that decides when and which cells to balance—is a control policy. A simple greedy approach balances all cells above a threshold simultaneously. A more sophisticated algorithm minimizes total balancing energy dissipation while keeping all cells within a target voltage band. The optimization problem can be posed as:

minimize: ∑ᵢ Pᵢ(t)   (total power dissipated in balancing)
subject to: |V_i − V_j| ≤ ε   for all pairs (i, j)   (voltage tolerance)
            V_i_min ≤ V_i ≤ V_i_max   (voltage limits)

This is solved at runtime using a simple algorithm. At each BMS update (typically 10–100ms), the controller checks which cells are out of tolerance and adjusts balancing duty cycles. For a 12-cell pack, this is negligible computation.

Balancing timing is crucial. Aggressive balancing dissipates energy (for passive) or couples cells through the balancer (for active), affecting thermal distribution and potentially introducing transient voltages. Most BMS implementations balance only during idle periods or low-current charging when dissipation is acceptable. Some perform micro-balancing during normal operation to prevent imbalances from growing.

### 2.4 Thermal Management and Temperature Estimation

Temperature profoundly shapes all BMS decisions. Cell capacity, resistance, power capability, and aging rate are all strong functions of T. A lithium cell at −20°C has roughly 50% of its 25°C power capability and four times the resistance. At 60°C, aging rates double. The BMS must estimate and predict cell temperatures and manage cooling systems to keep cells in an optimal window (typically 15–40°C for best performance and longevity).

Direct temperature measurement is performed using thermistors (NTC resistors) or precision ICs (like the TI TMP1075) embedded in the pack. A typical automotive pack has 4–8 temperature sensors spread across its volume to detect hot spots. The sensors connect to the BMS controller via single-wire or I²C interfaces. However, distributed measurements capture only a few points; the true temperature field is continuous.

Temperature estimation fills the gaps. The BMS models the pack's thermal resistance and capacitance, using lumped heat-balance equations. For a simplified model treating the entire pack as a single node:

C_thermal · dT/dt = Q_generated − (T − T_ambient) / R_thermal

where C_thermal is the pack's thermal capacitance (typically 100–1000 J/K for a 50–100kWh pack), Q_generated is the heat produced by I²R losses and electrochemical polarization, R_thermal is the thermal resistance to ambient (10−4 to 10−3 K/W, depending on cooling), and T_ambient is the ambient temperature.

The heat generated has two components. Joule heating from internal resistance is I²·R_internal, directly measured from current. Electrochemical heating is harder to estimate without a detailed model, but a practical approximation is:

Q_chem = I · (V_OCV − V_terminal) = I · (I·R_internal + V_RC)

So the total heat is Q_total ≈ I·(V_OCV − V_terminal).

For a more detailed spatially-distributed model, the pack is divided into thermal regions (e.g., four quadrants in a large automotive battery), each with its own temperature, and thermal resistances represent conduction between regions and to ambient. This requires solving a system of differential equations:

dT_i/dt = (1/C_i) · [Q_i + ∑_j (T_j − T_i)/R_ij − (T_i − T_ambient)/R_i,ambient]

This system is integrated at each BMS update step. The state includes cell temperatures; measurements from thermistors are fused via an extended Kalman filter similar to the SOC estimator, correcting predicted temperatures when they diverge from measured values.

The BMS uses temperature predictions to enforce charge and discharge rate limits. As T rises, the maximum allowed charge current (CC current) decreases:

I_cc_max(T) = I_cc_max,25°C × derating_curve(T)

where derating_curve(T) is a piecewise linear or polynomial function provided by the cell manufacturer. Similarly, the maximum discharge current is derated at extreme temperatures (too cold: high resistance causes excessive voltage drop; too hot: aging accelerates).

Thermal management also involves coordinating with external cooling systems. For automotive packs, this might be a liquid-cooled cold plate with a pump and radiator; for stationary grid storage, it could be forced-air cooling or passive convection. The BMS computes the required cooling power and sends control signals (PWM duty cycle for a pump, fan on/off) to the thermal system. A simple proportional controller suffices:

P_cooling_setpoint = k_p · (T_max − T_setpoint) + k_i · ∫(T_max − T_setpoint)dt

where T_max is the highest measured cell temperature and T_setpoint is a target temperature (e.g., 30°C).

### 2.5 Charge and Discharge Control

The BMS acts as a gatekeeper, allowing charge or discharge only when it is safe. It enforces limits derived from electrochemical constraints and state estimates. The primary limits are:

**Charge current limit:** To prevent lithium plating on the anode during fast charging, the cell voltage must remain above a minimum threshold. As the cell charges, its OCV rises. The BMS enforces:

V_terminal ≥ V_OCV_min + margin

During constant-current (CC) charging, the charger supplies a fixed current I_cc. The terminal voltage rises as V_terminal = V_OCV(SOC) + I_cc·R_internal. As SOC approaches full, V_OCV rises, and V_terminal approaches the cell's maximum voltage (typically 4.2V or 4.35V depending on chemistry). When V_terminal reaches this limit, the charger transitions to constant-voltage (CV) mode, where it holds V_terminal fixed and allows current to decay as the OCV rises. The BMS monitors this transition and cuts off charging when current drops below a threshold (e.g., 0.05C, where C is the nominal capacity).

**Discharge current limit:** At low temperatures, high discharge current causes excessive resistive heating and can temporarily raise cell pressure if gas generation occurs. The BMS limits discharge current based on temperature:

I_discharge_max(T) = I_discharge_max,25°C × derating_curve(T)

Additionally, if a cell's voltage drops below a minimum threshold (typically 2.7–3.0V) during discharge, the BMS cuts off discharge to prevent over-discharge, which causes irreversible copper dissolution and separator damage.

**SOC window limit:** The BMS prevents charging above 100% SOC (where lithium plating risk is high) and discharging below a minimum SOC (
