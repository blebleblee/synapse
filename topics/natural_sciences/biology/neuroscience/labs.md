# Operational Verification Labs: Neuroscience

## Objective & Laboratory Bench Setup

Neuroscience operates at the intersection of electrical physics, biochemical signal transduction, and complex systems dynamics. The nervous system functions as an electrochemical computer, where voltage-gated ion channels generate action potentials that propagate along axonal membranes, synaptic vesicles release neurotransmitters across nanoscale clefts, and dendritic integration performs spatiotemporal computation. This laboratory guide provides concrete empirical exercises for measuring neuronal electrical properties, analyzing synaptic transmission dynamics, and modeling network behavior using authentic electrophysiology protocols and computational neuroscience tools.

The experimental approach prioritizes direct measurement of physical quantities—membrane potentials, current-voltage relationships, synaptic conductance changes, and spike timing statistics—before building computational models grounded in the Hodgkin-Huxley formalism and cable theory. Each exercise provides complete protocols with explicit experimental parameters, measurement sequences, and error propagation analysis. The theoretical foundations rest on the Nernst-Planck equation for ion flux, the Goldman-Hodgkin-Katz equation for membrane potential, and the cable equation for passive electrical propagation in dendrites.

Your laboratory bench requires a scientific Python environment configured for electrophysiology data analysis and neuronal modeling. Install the core computational neuroscience stack by executing `pip install numpy scipy matplotlib brian2 neuron` to provision NumPy for array operations, SciPy for signal processing and differential equation solvers, Matplotlib for time-series visualization, Brian2 for spiking neural network simulation, and NEURON for biophysically detailed compartmental modeling. Verify the installation integrity by running `python -c 'import brian2; print(brian2.__version__); import neuron; print(neuron.h.nrnversion())'` to confirm both simulation engines respond correctly.

For experimental electrophysiology recordings, you will work with digitized datasets representing patch-clamp recordings acquired at 10-50 kHz sampling rates. These datasets capture membrane voltage trajectories during current injection protocols, spontaneous synaptic events, and evoked network activity. The physical measurement apparatus underlying these recordings includes a patch-clamp amplifier operating in current-clamp or voltage-clamp mode, an analog-to-digital converter with 16-bit resolution, and a Faraday cage to eliminate 60 Hz electromagnetic interference from mains power. While you will analyze pre-recorded datasets rather than perform live electrophysiology, understanding the physical measurement chain—glass micropipette tip resistance (3-7 MΩ), seal resistance (>1 GΩ for gigaseal formation), series resistance compensation, and capacitance neutralization—grounds your interpretation of signal quality and noise characteristics.

The theoretical scaffold begins with the Nernst equation, which predicts the equilibrium potential for a single ion species across a selectively permeable membrane. For an ion X with valence z, the Nernst potential is given by $E_X = \frac{RT}{zF} \ln\frac{[X]_{\text{out}}}{[X]_{\text{in}}}$, where R is the gas constant (8.314 J·mol⁻¹·K⁻¹), T is absolute temperature (typically 293-310 K for mammalian preparations), F is Faraday's constant (96485 C·mol⁻¹), and the concentration ratio reflects the ionic gradient maintained by ATP-driven pumps. At room temperature (298 K), this simplifies to approximately 58 mV per tenfold concentration ratio for monovalent cations. For physiological potassium concentrations of 140 mM intracellular and 5 mM extracellular, the Nernst potential evaluates to approximately -85 mV, establishing the thermodynamic driving force for potassium efflux.

When multiple ion species contribute to membrane conductance simultaneously, the Goldman-Hodgkin-Katz voltage equation provides the steady-state membrane potential by weighting each ion's Nernst potential by its relative permeability: $V_m = \frac{RT}{F} \ln\frac{P_K[K^+]_{\text{out}} + P_{Na}[Na^+]_{\text{out}} + P_{Cl}[Cl^-]_{\text{in}}}{P_K[K^+]_{\text{in}} + P_{Na}[Na^+]_{\text{in}} + P_{Cl}[Cl^-]_{\text{out}}}$. The resting membrane potential of approximately -70 mV in mammalian neurons arises because potassium permeability dominates at rest (P_K ≈ 1, P_Na ≈ 0.04, P_Cl ≈ 0.45), pulling the membrane potential toward the potassium Nernst potential while small sodium and chloride permeabilities shift it slightly positive.

The Hodgkin-Huxley model, developed from voltage-clamp experiments on the squid giant axon, describes action potential generation through the dynamic interplay of voltage-gated sodium and potassium conductances. The membrane potential obeys the differential equation $C_m \frac{dV}{dt} = -\bar{g}_{Na} m^3 h (V - E_{Na}) - \bar{g}_K n^4 (V - E_K) - g_L (V - E_L) + I_{\text{ext}}$, where $C_m$ is the membrane capacitance (approximately 1 μF·cm⁻²), the gating variables m, h, and n evolve according to voltage-dependent rate equations, and $I_{\text{ext}}$ represents externally injected current. The cubic sodium activation (m³) and linear inactivation (h) produce the rapid upstroke and subsequent sodium channel inactivation, while the fourth-power potassium activation (n⁴) generates the delayed repolarization. This mathematical formalism converts biophysical mechanisms—conformational changes in voltage-sensing protein domains—into quantitative predictions of spike timing, threshold dynamics, and refractory periods.

Cable theory extends the Hodgkin-Huxley framework to spatially extended neuronal structures by treating dendrites and axons as cylindrical cables with distributed membrane capacitance and resistance. The cable equation in one spatial dimension becomes $\lambda^2 \frac{\partial^2 V}{\partial x^2} = \tau_m \frac{\partial V}{\partial t} + V - V_{\text{rest}}$, where the space constant $\lambda = \sqrt{r_m / r_i}$ characterizes the distance over which passive voltage signals decay (typically 100-1000 μm in dendrites), $\tau_m = r_m c_m$ defines the membrane time constant (5-30 ms), $r_m$ is the specific membrane resistance, $r_i$ is the intracellular resistivity, and $c_m$ is the specific membrane capacitance. Synaptic inputs arriving at different dendritic locations experience distance-dependent attenuation before reaching the soma, creating a spatial filter that shapes synaptic integration.

Each exercise in this guide builds experimental competency through direct measurement, systematic parameter variation, and rigorous uncertainty quantification. You will analyze real electrophysiology recordings to extract biophysical parameters, simulate neuronal responses under controlled conditions, and stress-test models against boundary conditions that reveal fundamental limitations. The progression moves from single-neuron electrical properties through synaptic transmission to network dynamics, maintaining continuous connection between theoretical predictions and experimental observables.

## Exercise 1: Empirical Observation & Measurement Protocol

### Experimental Context: Measuring Passive Membrane Properties from Current-Clamp Recordings

The passive electrical properties of neuronal membranes—input resistance, membrane time constant, and resting potential—determine how neurons integrate synaptic inputs and respond to current injection. These properties arise from the biophysical composition of the lipid bilayer and the density of leak channels, which together establish the baseline electrical behavior upon which voltage-gated conductances operate. In this exercise, you will analyze a current-clamp recording where a neuron receives a hyperpolarizing current step and measure the passive membrane response to extract quantitative biophysical parameters.

The physical measurement protocol involves establishing a whole-cell patch-clamp configuration in current-clamp mode, where the amplifier injects a controlled current through the recording pipette while measuring the resulting membrane voltage deflection. A typical protocol applies a -50 pA hyperpolarizing current step for 500 ms duration, producing a voltage deflection of 5-20 mV depending on the neuron's input resistance. The voltage trajectory exhibits an exponential approach to steady-state with a time constant determined by the membrane capacitance and resistance, followed by an exponential decay back to resting potential after current termination. By fitting exponential functions to these transients, you extract the membrane time constant and input resistance, which together determine the membrane capacitance via $C_m = \tau_m / R_{\text{in}}$.

Begin by creating a synthetic current-clamp recording that captures the essential physics of passive membrane dynamics. The following Python script generates a voltage trace representing a neuron's response to a hyperpolarizing current step, incorporating realistic noise characteristics from amplifier thermal noise and biological membrane fluctuations:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Physical parameters for passive membrane model
R_in = 150e6  # Input resistance in ohms (150 MΩ typical for cortical pyramidal neuron)
tau_m = 15e-3  # Membrane time constant in seconds (15 ms)
C_m = tau_m / R_in  # Membrane capacitance in farads (calculated from tau and R_in)
V_rest = -70e-3  # Resting potential in volts (-70 mV)
I_step = -50e-12  # Current step amplitude in amperes (-50 pA hyperpolarizing)

# Temporal parameters
dt = 0.1e-3  # Sampling interval in seconds (0.1 ms, equivalent to 10 kHz sampling)
t_total = 1.0  # Total recording duration in seconds
t_step_start = 0.2  # Current step onset time in seconds
t_step_end = 0.7  # Current step offset time in seconds
t = np.arange(0, t_total, dt)  # Time vector

# Analytical solution for voltage trajectory during current step
# During step: V(t) = V_rest + I_step * R_in * (1 - exp(-(t - t_start)/tau_m))
# After step: V(t) = V_rest + Delta_V * exp(-(t - t_end)/tau_m)
V = np.ones_like(t) * V_rest

# Apply current step and compute voltage response
for i, time in enumerate(t):
    if t_step_start <= time < t_step_end:
        # During current injection: exponential approach to new steady-state
        V[i] = V_rest + I_step * R_in * (1 - np.exp(-(time - t_step_start) / tau_m))
    elif time >= t_step_end:
        # After current termination: exponential decay back to resting potential
        V_ss = V_rest + I_step * R_in  # Steady-state voltage during step
        V[i] = V_rest + (V_ss - V_rest) * np.exp(-(time - t_step_end) / tau_m)

# Add realistic noise: thermal noise from amplifier (~0.5 mV RMS) plus membrane fluctuations
noise_thermal = np.random.normal(0, 0.5e-3, len(t))  # Thermal noise from amplifier
noise_membrane = np.random.normal(0, 0.2e-3, len(t))  # Biological membrane fluctuations
V_measured = V + noise_thermal + noise_membrane

# Convert to millivolts for display
V_mV = V_measured * 1e3
t_ms = t * 1e3

print("=== Passive Membrane Property Measurement Protocol ===\n")
print(f"Ground Truth Parameters (Used to Generate Synthetic Data):")
print(f"  Input Resistance (R_in): {R_in*1e-6:.1f} MΩ")
print(f"  Membrane Time Constant (τ_m): {tau_m*1e3:.1f} ms")
print(f"  Membrane Capacitance (C_m): {C_m*1e12:.1f} pF")
print(f"  Resting Potential (V_rest): {V_rest*1e3:.1f} mV")
print(f"  Injected Current Step: {I_step*1e12:.1f} pA")
print(f"\nRecording Parameters:")
print(f"  Sampling Rate: {1/dt*1e-3:.1f} kHz")
print(f"  Total Duration: {t_total*1e3:.0f} ms")
print(f"  Current Step Duration: {(t_step_end - t_step_start)*1e3:.0f} ms\n")

# Measurement Protocol 1: Extract resting potential from baseline period
baseline_mask = t < t_step_start
V_rest_measured = np.mean(V_measured[baseline_mask])
V_rest_std = np.std(V_measured[baseline_mask])

print("--- Measurement 1: Resting Membrane Potential ---")
print(f"Baseline Period: 0 to {t_step_start*1e3:.0f} ms")
print(f"Measured V_rest: {V_rest_measured*1e3:.2f} ± {V_rest_std*1e3:.2f} mV")
print(f"Ground Truth V_rest: {V_rest*1e3:.2f} mV")
print(f"Measurement Error: {abs(V_rest_measured - V_rest)*1e3:.2f} mV\n")

# Measurement Protocol 2: Extract input resistance from steady-state voltage deflection
steady_state_mask = (t > t_step_start + 0.1) & (t < t_step_end - 0.05)  # Exclude transients
V_ss_measured = np.mean(V_measured[steady_state_mask])
Delta_V = V_ss_measured - V_rest_measured
R_in_measured = Delta_V / I_step

print("--- Measurement 2: Input Resistance ---")
print(f"Steady-State Period: {(t_step_start + 0.1)*1e3:.0f} to {(t_step_end - 0.05)*1e3:.0f} ms")
print(f"Steady-State Voltage: {V_ss_measured*1e3:.2f} mV")
print(f"Voltage Deflection (ΔV): {Delta_V*1e3:.2f} mV")
print(f"Measured R_in: {R_in_measured*1e-6:.1f} MΩ")
print(f"Ground Truth R_in: {R_in*1e-6:.1f} MΩ")
print(f"Measurement Error: {abs(R_in_measured - R_in)*1e-6:.1f} MΩ ({abs(R_in_measured - R_in)/R_in*100:.1f}%)\n")

# Measurement Protocol 3: Extract membrane time constant from exponential fit
# Fit exponential to the charging phase (first 50 ms after step onset)
charge_mask = (t >= t_step_start) & (t <= t_step_start + 0.05)
t_fit = t[charge_mask] - t_step_start  # Time relative to step onset
V_fit = V_measured[charge_mask]

# Exponential fit function: V(t) = V_rest + A * (1 - exp(-t/tau))
def exp_charge(t, V_rest_fit, A, tau):
    return V_rest_fit + A * (1 - np.exp(-t / tau))

# Initial parameter guess
p0 = [V_rest_measured, I_step * R_in, tau_m]

try:
    popt, pcov = curve_fit(exp_charge, t_fit, V_fit, p0=p0, maxfev=5000)
    V_rest_fit, A_fit, tau_m_measured = popt
    tau_m_std = np.sqrt(np.diag(pcov))[2]  # Standard error on tau_m
    
    # Calculate membrane capacitance from measured parameters
    C_m_measured = tau_m_measured / R_in_measured
    
    print("--- Measurement 3: Membrane Time Constant ---")
    print(f"Exponential Fit Window: {t_step_start*1e3:.0f} to {(t_step_start + 0.05)*1e3:.0f} ms")
    print(f"Measured τ_m: {tau_m_measured*1e3:.2f} ± {tau_m_std*1e3:.2f} ms")
    print(f"Ground Truth τ_m: {tau_m*1e3:.2f} ms")
    print(f"Measurement Error: {abs(tau_m_measured - tau_m)*1e3:.2f} ms ({abs(tau_m_measured - tau_m)/tau_m*100:.1f}%)")
    print(f"\nCalculated C_m: {C_m_measured*1e12:.1f} pF")
    print(f"Ground Truth C_m: {C_m*1e12:.1f} pF")
    print(f"Measurement Error: {abs(C_m_measured - C_m)*1e12:.1f} pF ({abs(C_m_measured - C_m)/C_m*100:.1f}%)\n")
    
    # Generate fitted curve for visualization
    V_fit_curve = exp_charge(t_fit, *popt)
    
except RuntimeError:
    print("Exponential fit failed to converge. Check data quality and initial parameter guesses.\n")
    V_fit_curve = None

# Visualization: Three-panel figure showing voltage trace, measurement regions, and fit quality
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Panel 1: Full voltage trace with measurement regions highlighted
axes[0].plot(t_ms, V_mV, 'k-', linewidth=0.5, label='Measured Voltage')
axes[0].axhline(V_rest*1e3, color='blue', linestyle='--', linewidth=1, label='Resting Potential')
axes[0].axhline(V_ss_measured*1e3, color='red', linestyle='--', linewidth=1, label='Steady-State Voltage')
axes[0].axvspan(t_step_start*1e3, t_step_end*1e3, alpha=0.2, color='gray', label='Current Step')
axes[0].set_xlabel('Time (ms)', fontsize=11)
axes[0].set_ylabel('Membrane Voltage (mV)', fontsize=11)
axes[0].set_title('Current-Clamp Recording: Passive Membrane Response to Hyperpolarizing Step', fontsize=12, fontweight='bold')
axes[0].legend(loc='upper right', fontsize=9)
axes[0].grid(True, alpha=0.3)

# Panel 2: Zoom on charging phase with exponential fit overlay
if V_fit_curve is not None:
    axes[1].plot((t[charge_mask] - t_step_start)*1e3, V_measured[charge_mask]*1e3, 'ko', markersize=2, label='Measured Data')
    axes[1].plot((t[charge_mask] - t_step_start)*1e3, V_fit_curve*1e3, 'r-', linewidth=2, label=f'Exponential Fit (τ = {tau_m_measured*1e3:.2f} ms)')
    axes[1].set_xlabel('Time After Step Onset (ms)', fontsize=11)
    axes[1].set_ylabel('Membrane Voltage (mV)', fontsize=11)
    axes[1].set_title('Exponential Fit to Charging Phase: Time Constant Extraction', fontsize=12, fontweight='bold')
    axes[1].legend(loc='lower right', fontsize=9)
    axes[1].grid(True, alpha=0.3)

# Panel 3: Residuals to assess fit quality
if V_fit_curve is not None:
    residuals = (V_measured[charge_mask] - V_fit_curve) * 1e3
    axes[2].plot((t[charge_mask] - t_step_start)*1e3, residuals, 'k-', linewidth=0.5)
    axes[2].axhline(0, color='red', linestyle='--', linewidth=1)
    axes[2].fill_between((t[charge_mask] - t_step_start)*1e3, -2*V_rest_std*1e3, 2*V_rest_std*1e3, 
                         alpha=0.3, color='gray', label='±2σ Noise Band')
    axes[2].set_xlabel('Time After Step Onset (ms)', fontsize=11)
    axes[2].set_ylabel('Fit Residuals (mV)', fontsize=11)
    axes[2].set_title('Fit Quality Assessment: Residuals Should Remain Within Noise Floor', fontsize=12, fontweight='bold')
    axes[2].legend(loc='upper right', fontsize=9)
    axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('passive_membrane_properties_measurement.png', dpi=300, bbox_inches='tight')
print("Figure saved: passive_membrane_properties_measurement.png")
plt.show()

# Summary table of all measurements
print("\n=== Summary: Measured vs. Ground Truth Parameters ===")
print(f"{'Parameter':<30} {'Measured':<20} {'Ground Truth':<20} {'Error (%)':<15}")
print("-" * 85)
print(f"{'Resting Potential (mV)':<30} {V_rest_measured*1e3:>6.2f} ± {V_rest_std*1e3:>4.2f}      {V_rest*1e3:>6.2f}              {abs(V_rest_measured - V_rest)/abs(V_rest)*100:>6.2f}")
print(f"{'Input Resistance (MΩ)':<30} {R_in_measured*1e-6:>6.1f}              {R_in*1e-6:>6.1f}              {abs(R_in_measured - R_in)/R_in*100:>6.1f}")
if V_fit_curve is not None:
    print(f"{'Membrane Time Constant (ms)':<30} {tau_m_measured*1e3:>6.2f} ± {tau_m_std*1e3:>4.2f}      {tau_m*1e3:>6.2f}              {abs(tau_m_measured - tau_m)/tau_m*100:>6.2f}")
    print(f"{'Membrane Capacitance (pF)':<30} {C_m_measured*1e12:>6.1f}              {C_m*1e12:>6.1f}              {abs(C_m_measured - C_m)/C_m*100:>6.1f}")
```

Execute this script by saving it as `measure_passive_properties.py` and running `python measure_passive_properties.py`. The script generates a synthetic current-clamp recording with known ground-truth parameters, then applies the standard electrophysiology analysis protocol to extract passive membrane properties from the voltage trajectory. The measurement sequence mirrors actual laboratory practice: first establish the baseline resting potential during the pre-stimulus period, then measure the steady-state voltage deflection to calculate input resistance via Ohm's law, and finally fit an exponential function to the charging transient to extract the membrane time constant.

The input resistance measurement relies on the linear relationship $\Delta V = I \cdot R_{\text{in}}$ holding in the subthreshold regime where voltage-gated conductances remain closed. The hyperpolarizing direction prevents sodium channel activation, ensuring the measurement captures purely passive properties. The membrane time constant governs the speed of voltage changes and determines how rapidly synaptic inputs can be integrated—neurons with short time constants (5-10 ms) respond quickly to transient inputs and act as coincidence detectors, while neurons with long time constants (20-40 ms) integrate inputs over extended windows and compute temporal averages.

The exponential fit procedure deserves careful attention because it embodies the core physics of RC circuit dynamics. The membrane behaves as a parallel resistance-capacitance circuit where the capacitance stores charge on the lipid bilayer while the resistance represents ion flux through leak channels. The differential equation governing this circuit is $R_{\text{in}} C_m \frac{dV}{dt} = I - \frac{V - V_{\text{rest}}}{R_{\text{in}}}$, which yields the time constant $\tau_m = R_{\text{in}} C_m$ and predicts exponential voltage trajectories. The fit residuals provide a quantitative check on whether this simple model adequately describes the data—systematic deviations indicate the presence of voltage-dependent conductances, non-uniform cable properties, or series resistance errors.

The uncertainty analysis propagates measurement noise through the parameter extraction pipeline. The resting potential standard deviation quantifies baseline voltage fluctuations from thermal noise and spontaneous channel openings, typically 0.3-0.8 mV in well-isolated recordings. The input resistance error depends on both the voltage measurement uncertainty and the precision of the current injection, with typical errors of 5-15% in automated analysis pipelines. The time constant fit uncertainty reflects both the quality of the exponential model and the signal-to-noise ratio during the transient phase—longer averaging windows reduce noise but require slower current steps that may activate voltage-gated conductances.

After executing the script, inspect the three-panel figure. The top panel shows the complete voltage trajectory with measurement regions marked, allowing you to verify that the current step produced a clean hyperpolarizing deflection without artifacts from amplifier saturation or series resistance errors. The middle panel displays the exponential fit to the charging phase, where good agreement between the data and fit curve validates the passive membrane model. The bottom panel plots the fit residuals, which should fluctuate randomly around zero within the noise band—structured patterns in the residuals indicate model inadequacy or the presence of active conductances.

Modify the ground-truth parameters to explore how different neuronal types exhibit distinct passive properties. Set `R_in = 500e6` and `tau_m = 40e-3` to simulate a small interneuron with high input resistance and long time constant, then observe how the voltage deflection increases dramatically (approaching 25 mV for the same current step) and the charging transient slows. Conversely, set `R_in = 50e6` and `tau_m = 8e-3` to simulate a fast-spiking interneuron with low input resistance and short time constant, producing a small voltage deflection (2-3 mV) and rapid charging kinetics. These parameter variations directly connect biophysical properties to functional roles—neurons with high input resistance are more excitable and require less synaptic input to reach spike threshold, while neurons with short time constants can follow high-frequency input trains with greater temporal precision.

The relationship between input resistance, membrane capacitance, and neuronal morphology reveals how cellular geometry constrains electrical behavior. Input resistance scales inversely with membrane surface area as $R_{\text{in}} \propto 1 / A_{\text{total}}$, so neurons with extensive dendritic arbors exhibit lower input resistance despite having identical specific membrane resistance. Membrane capacitance scales directly with surface area as $C_m = c_m \cdot A_{\text{total}}$, where $c_m \approx 1$ μF·cm⁻² is the specific membrane capacitance of the lipid bilayer. The time constant $\tau_m = R_{\text{in}} C_m = r_m c_m$ depends only on the specific membrane properties and remains invariant with cell size, explaining why the membrane time constant shows less variability across neuronal types than input resistance or capacitance alone.

This exercise establishes the measurement protocols and analysis techniques that underpin all subsequent experiments. The passive membrane properties define the baseline electrical state upon which action potential generation, synaptic integration, and network dynamics operate. Accurate parameter extraction requires attention to experimental artifacts—series resistance compensation ensures the voltage measurement reflects true membrane potential rather than voltage drops across the pipette, capacitance neutralization removes transient charging artifacts, and proper seal quality eliminates leak currents that would artifactually decrease input resistance. In the computational workflow, these physical considerations translate to careful selection of analysis windows that exclude transient artifacts and systematic validation of model assumptions through residual analysis.

## Exercise 2: Parameter Variation, Calibration & Response Curve Plotting

### Experimental Context: Hodgkin-Huxley Action Potential Generation and Threshold Dynamics

The action potential represents one of the most precisely characterized phenomena in cellular neuroscience, where the Hodgkin-Huxley model achieves quantitative agreement with experimental voltage-clamp measurements across a wide range of conditions. The rapid upstroke arises from regenerative sodium channel activation, the peak amplitude is determined by the sodium Nernst potential, the falling phase reflects delayed potassium channel activation combined with sodium channel inactivation, and the afterhyperpolarization results from sustained potassium conductance. This exercise constructs a complete Hodgkin-Huxley neuron model, systematically varies the injected current amplitude, and measures the spike threshold, firing rate, and spike waveform characteristics to generate input-output transfer functions that reveal neuronal excitability.

The Hodgkin-Huxley formalism decomposes membrane dynamics into four coupled differential equations: one for membrane voltage and three for voltage-dependent gating variables. The voltage equation $C_m \frac{dV}{dt} = I_{\text{ext}} - I_{\text{Na}} - I_K - I_L$ includes three ionic currents where the sodium current $I_{\text{Na}} = \bar{g}_{\text{Na}} m^3 h (V - E_{\text{Na}})$ depends on the activation variable m (probability that an activation gate is open) and inactivation variable h (probability that an inactivation gate is open), while the potassium current $I_K = \bar{g}_K n^4 (V - E_K)$ depends on the activation variable n. Each gating variable evolves according to $\frac{dx}{dt} = \alpha_x(V)(1 - x) - \beta_x(V) x$, where the voltage-dependent rate functions $\alpha_x(V)$ and $\beta_x(V)$ were empirically determined from voltage-clamp experiments at different holding potentials.

The spike threshold emerges from the nonlinear interaction between sodium channel activation and potassium channel activation—when depolarization is sufficiently rapid to allow sodium activation to outpace potassium activation, the positive feedback loop drives regenerative sodium entry and produces a spike. The threshold is not a fixed voltage but rather depends on the rate of depolarization, recent spiking history (sodium channel inactivation and potassium channel activation leave residual conductances), and temperature (rate constants accelerate with increasing temperature according to Q₁₀ scaling). This dynamic threshold behavior explains phenomena like rheobase (minimum current for sustained spiking), chronaxie (characteristic timescale of threshold behavior), and accommodation (reduced excitability during slow current ramps).

The following Python script implements the Hodgkin-Huxley model with biophysically accurate parameters and simulates neuronal responses to current steps of varying amplitude. The simulation sweeps injected current from subthreshold values through high-frequency spiking regimes, then analyzes spike timing, interspike intervals, and waveform features to construct comprehensive input-output relationships:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.signal import find_peaks

# Hodgkin-Huxley model parameters (original squid giant axon parameters)
C_m = 1.0  # Membrane capacitance (μF/cm²)
g_Na = 120.0  # Maximum sodium conductance (mS/cm²)
g_K = 36.0  # Maximum potassium conductance (mS/cm²)
g_L = 0.3  # Leak conductance (mS/cm²)
E_Na = 50.0  # Sodium Nernst potential (mV)
E_K = -77.0  # Potassium Nernst potential (mV)
E_L = -54.387  # Leak Nernst potential (mV)

# Voltage-dependent rate functions for gating variables
def alpha_m(V):
    """Sodium activation rate function"""
    return 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))

def beta_m(V):
    """Sodium deactivation rate function"""
    return 4.0 * np.exp(-(V + 65.0) / 18.0)

def alpha_h(V):
    """Sodium inactivation removal rate function"""
    return 0.07 * np.exp(-(V + 65.0) / 20.0)

def beta_h(V):
    """Sodium inactivation rate function"""
    return 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))

def alpha_n(V):
    """Potassium activation rate function"""
    return 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))

def beta_n(V):
    """Potassium deactivation rate function"""
    return 0.125 * np.exp(-(V + 65.0) / 80.0)

# Hodgkin-Huxley differential equations
def hodgkin_huxley(state, t, I_ext):
    """
    Hodgkin-Huxley model ODE system
    state = [V, m, h, n]
    """
    V, m, h, n = state
    
    # Ionic currents
    I_Na = g_Na * m**3 * h * (V - E_Na)
    I_K = g_K * n**4 * (V - E_K)
    I_L = g_L * (V - E_L)
    
    # Membrane voltage derivative
    dVdt = (I_ext - I_Na - I_K - I_L) / C_m
    
    # Gating variable derivatives
    dmdt = alpha_m(V) * (1.0 - m) - beta_m(V) * m
    dhdt = alpha_h(V) * (1.0 - h) - beta_h(V) * h
    dndt = alpha_n(V) * (1.0 - n) - beta_n(V) * n
    
    return [dVdt, dmdt, dhdt, dndt]

# Simulation parameters
dt = 0.01  # Time step (ms)
t_total = 200.0  # Total simulation time (ms)
t_stim_start = 50.0  # Current step onset (ms)
t_stim_end = 150.0  # Current step offset (ms)
t = np.arange(0, t_total, dt)

# Current amplitude sweep parameters
I_min = 0.0  # Minimum injected current (μA/cm²)
I_max = 20.0  # Maximum injected current (μA/cm²)
I_steps = 11  # Number of current steps to test
I_amplitudes = np.linspace(I_min, I_max, I_steps)

print("=== Hodgkin-Huxley Model: Current-Voltage Transfer Function Analysis ===\n")
print(f"Model Parameters:")
print(f"  Membrane Capacitance: {C_m} μF/cm²")
print(f"  Maximum Sodium Conductance: {g_Na} mS/cm²")
print(f"  Maximum Potassium Conductance: {g_K} mS/cm²")
print(f"  Sodium Nernst Potential: {E_Na} mV")
print(f"  Potassium Nernst Potential: {E_K} mV\n")
print(f"Simulation Parameters:")
print(f"  Time Step: {dt} ms")
print(f"  Total Duration: {t_total} ms")
print(f"  Current Step: {t_stim_start} to {t_stim_end} ms")
print(f"  Current Amplitude Range: {I_min} to {I_max} μA/cm² ({I_steps} steps)\n")

# Storage arrays for response metrics
spike_counts = []
firing_rates = []
mean_ISI = []
CV_ISI = []
threshold_voltages = []
spike_amplitudes = []
spike_widths = []

# Main simulation loop: sweep current amplitude
for i, I_amp in enumerate(I_amplitudes):
    # Define time-varying current injection
    I_ext = np.zeros_like(t)
    I_ext[(t >= t_stim_start) & (t < t_stim_end)] = I_amp
    
    # Initial conditions: resting state at V = -65 mV
    V_init = -65.0
    m_init = alpha_m(V_init) / (alpha_m(V_init) + beta_m(V_init))
    h_init = alpha_h(V_init) / (alpha_h(V_init) + beta_h(V_init))
    n_init = alpha_n(V_init) / (alpha_n(V_init) + beta_n(V_init))
    state_init = [V_init, m_init, h_init, n_init]
    
    # Integrate Hodgkin-Huxley ODEs
    solution = np.zeros((len(t), 4))
    for j in range(len(t)):
        if j == 0:
            solution[j] = state_init
        else:
            # Single step integration using scipy.integrate.odeint
            t_span = [t[j-1], t[j]]
            sol = odeint(hodgkin_huxley, solution[j-1], t_span, args=(I_ext[j],))
            solution[j] = sol[-1]
    
    V_trace = solution[:, 0]
    
    # Detect spikes: find peaks in voltage trace above 0 mV threshold
    spike_indices, spike_properties = find_peaks(V_trace, height=0.0, distance=int(2.0/dt))
    n_spikes = len(spike_indices)
    
    # Calculate firing rate during stimulation period
    stim_duration = (t_stim_end - t_stim_start) / 1000.0  # Convert to seconds
    firing_rate = n_spikes / stim_duration if n_spikes > 0 else 0.0
    
    # Calculate interspike interval statistics
    if n_spikes > 1:
        ISI = np.diff(t[spike_indices])  # Interspike intervals in ms
        mean_isi = np.mean(ISI)
        cv_isi = np.std(ISI) / mean_isi if mean_isi > 0 else 0.0
    else:
        mean_isi = np.nan
        cv_isi = np.nan
    
    # Extract spike threshold voltage (voltage at which dV/dt first exceeds 10 mV/ms)
    if n_spikes > 0:
        first_spike_idx = spike_indices[0]
        # Search backwards from spike peak to find threshold crossing
        search_window = slice(max(0, first_spike_idx - int(10.0/dt)), first_spike_idx)
        dVdt = np.gradient(V_trace[search_window], dt)
        threshold_idx = np.where(dVdt > 10.0)[0]
        if len(threshold_idx) > 0:
            threshold_V = V_trace[search_window][threshold_idx[0]]
        else:
            threshold_V = np.nan
        
        # Extract spike amplitude (peak voltage - threshold voltage)
        spike_amp = spike_properties['peak_heights'][0] - threshold_V if not np.isnan(threshold_V) else np.nan
        
        # Extract spike width at half-maximum amplitude
        if not np.isnan(threshold_V) and not np.isnan(spike_amp):
            half_max = threshold_V + spike_amp / 2.0
            spike_trace = V_trace[max(0, first_spike_idx - int(5.0/dt)):min(len(V_trace), first_spike_idx + int(5.0/dt))]
            above_half_max = spike_trace > half_max
            if np.sum(above_half_max) > 0:
                width_samples = np.sum(above_half_max)
                spike_width = width_samples * dt
            else:
                spike_width = np.nan
        else:
            spike_width = np.nan
    else:
        threshold_V = np.nan
        spike_amp = np.nan
        spike_width = np.nan
    
    # Store metrics
    spike_counts.append(n_spikes)
    firing_rates.append(firing_rate)
    mean_ISI.append(mean_isi)
    CV_ISI.append(cv_isi)
    threshold_voltages.append(threshold_V)
    spike_amplitudes.append(spike_amp)
    spike_widths.append(spike_width)
    
    print(f"I_ext = {I_amp:5.1f} μA/cm²: {n_spikes:2d} spikes, Firing Rate = {firing_rate:6.1f} Hz, " +
          f"Threshold = {threshold_V:6.2f} mV, Spike Amplitude = {spike_amp:6.2f} mV")

# Convert lists to numpy arrays for analysis
spike_counts = np.array(spike_counts)
firing_rates = np.array(firing_rates)
mean_ISI = np.array(mean_ISI)
CV_ISI = np.array(CV_ISI)
threshold_voltages = np.array(threshold_voltages)
spike_amplitudes = np.array(spike_amplitudes)
spike_widths = np.array(spike_widths)

# Find rheobase: minimum current that elicits at least one spike
rheobase_idx = np.where(spike_counts > 0)[0]
if len(rheobase_idx) > 0:
    rheobase = I_amplitudes[rheobase_idx[0]]
    print(f"\n=== Excitability Metrics ===")
    print(f"Rheobase (minimum spiking current): {rheobase:.2f} μA/cm²")
else:
    rheobase = np.nan
    print(f"\n=== Excitability Metrics ===")
    print(f"Rheobase: No spikes detected in current range")

# Fit linear region of F-I curve to extract gain
spiking_idx = np.where(spike_counts > 0)[0]
if len(spiking_idx) > 2:
    I_fit = I_amplitudes[spiking_idx]
    F_fit = firing_rates[spiking_idx]
    # Linear fit: F = gain * (I - I_threshold)
    poly_fit = np.polyfit(I_fit, F_fit, 1)
    gain = poly_fit[0]  # Slope in Hz per μA/cm²
    I_threshold_fit = -poly_fit[1] / poly_fit[0]  # X-intercept
    print(f"F-I Curve Gain: {gain:.1f} Hz per μA/cm²")
    print(f"Threshold Current (from linear fit): {I_threshold_fit:.2f} μA/cm²")
else:
    gain = np.nan
    I_threshold_fit = np.nan

# Generate comprehensive visualization
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

# Panel 1: Example voltage traces at different current levels
ax1 = fig.add_subplot(gs[0, :])
example_currents = [0.0, rheobase, 10.0, 20.0] if not np.isnan(rheobase) else [0.0, 5.0, 10.0, 20.0]
for I_example in example_currents:
    idx = np.argmin(np.abs(I_amplitudes - I_example))
    I_amp = I_amplitudes[idx]
    
    # Re-run simulation for this current
    I_ext = np.zeros_like(t)
    I_ext[(t >= t_stim_start) & (t < t_stim_end)] = I_amp
    V_init = -65.0
    m_init = alpha_m(V_init) / (alpha_m(V_init) + beta_m(V_init))
    h_init = alpha_h(V_init) / (alpha_h(V_init) + beta_h(V_init))
    n_init = alpha_n(V_init) / (alpha_n(V_init) + beta_n(V_init))
    state_init = [V_init, m_init, h_init, n_init]
    
    solution = np.zeros((len(t), 4))
    for j in range(len(t)):
        if j == 0:
            solution[j] = state_init
        else:
            t_span = [t[j-1], t[j]]
            sol = odeint(hodgkin_huxley, solution[j-1], t_span, args=(I_ext[j],))
            solution[j] = sol[-1]
    
    V_trace = solution[:, 0]
    ax1.plot(t, V_trace, linewidth=1.5, label=f'I = {I_amp:.1f} μA/cm²')

ax1.axvspan(t_stim_start, t_stim_end, alpha=0.2, color='gray', label='Current Step')
ax1.set_xlabel('Time (ms)', fontsize=11)
ax1.set_ylabel('Membrane Voltage (mV)', fontsize=11)
ax1.set_title('Hodgkin-Huxley Model: Voltage Responses to Current Steps', fontsize=12, fontweight='bold')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# Panel 2: F-I curve (firing rate vs. injected current)
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(I_amplitudes, firing_rates, 'ko-', linewidth=2, markersize=6)
if not np.isnan(gain):
    I_fit_range = np.array([I_threshold_fit, I_amplitudes[-1]])
    F_fit_range = gain * (I_fit_range - I_threshold_fit)
    ax2.plot(I_fit_range, F_fit_range, 'r--', linewidth=2, label=f'Linear Fit (Gain = {gain:.1f} Hz/(μA/cm²))')
    ax2.legend(fontsize=9)
ax2.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax2.set_ylabel('Firing Rate (Hz)', fontsize=11)
ax2.set_title('F-I Curve: Input-Output Transfer Function', fontsize=11, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Panel 3: Spike count vs. current
ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(I_amplitudes, spike_counts, 'bo-', linewidth=2, markersize=6)
ax3.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax3.set_ylabel('Number of Spikes', fontsize=11)
ax3.set_title('Spike Count vs. Current Amplitude', fontsize=11, fontweight='bold')
ax3.grid(True, alpha=0.3)

# Panel 4: Mean interspike interval vs. current
ax4 = fig.add_subplot(gs[1, 2])
valid_ISI = ~np.isnan(mean_ISI)
ax4.plot(I_amplitudes[valid_ISI], mean_ISI[valid_ISI], 'go-', linewidth=2, markersize=6)
ax4.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax4.set_ylabel('Mean ISI (ms)', fontsize=11)
ax4.set_title('Interspike Interval vs. Current', fontsize=11, fontweight='bold')
ax4.grid(True, alpha=0.3)

# Panel 5: Spike threshold voltage vs. current
ax5 = fig.add_subplot(gs[2, 0])
valid_thresh = ~np.isnan(threshold_voltages)
ax5.plot(I_amplitudes[valid_thresh], threshold_voltages[valid_thresh], 'mo-', linewidth=2, markersize=6)
ax5.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax5.set_ylabel('Spike Threshold (mV)', fontsize=11)
ax5.set_title('Threshold Voltage vs. Current', fontsize=11, fontweight='bold')
ax5.grid(True, alpha=0.3)

# Panel 6: Spike amplitude vs. current
ax6 = fig.add_subplot(gs[2, 1])
valid_amp = ~np.isnan(spike_amplitudes)
ax6.plot(I_amplitudes[valid_amp], spike_amplitudes[valid_amp], 'co-', linewidth=2, markersize=6)
ax6.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax6.set_ylabel('Spike Amplitude (mV)', fontsize=11)
ax6.set_title('Spike Amplitude vs. Current', fontsize=11, fontweight='bold')
ax6.grid(True, alpha=0.3)

# Panel 7: Spike width vs. current
ax7 = fig.add_subplot(gs[2, 2])
valid_width = ~np.isnan(spike_widths)
ax7.plot(I_amplitudes[valid_width], spike_widths[valid_width], 'ro-', linewidth=2, markersize=6)
ax7.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax7.set_ylabel('Spike Width (ms)', fontsize=11)
ax7.set_title('Spike Width vs. Current', fontsize=11, fontweight='bold')
ax7.grid(True, alpha=0.3)

# Panel 8: Coefficient of variation of ISI vs. current
ax8 = fig.add_subplot(gs[3, 0])
valid_CV = ~np.isnan(CV_ISI)
ax8.plot(I_amplitudes[valid_CV], CV_ISI[valid_CV], 'yo-', linewidth=2, markersize=6)
ax8.axhline(1.0, color='red', linestyle='--', linewidth=1, label='CV = 1 (Poisson)')
ax8.set_xlabel('Injected Current (μA/cm²)', fontsize=11)
ax8.set_ylabel('CV of ISI', fontsize=11)
ax8.set_title('ISI Regularity vs. Current', fontsize=11, fontweight='bold')
ax8.legend(fontsize=9)
ax8.grid(True, alpha=0.3)

# Panel 9: Gating variables during first spike
ax9 = fig.add_subplot(gs[3, 1:])
if not np.isnan(rheobase):
    idx = np.argmin(np.abs(I_amplitudes - rheobase))
    I_amp = I_amplitudes[idx]
    I_ext = np.zeros_like(t)
    I_ext[(t >= t_stim_start) & (t < t_stim_end)] = I_amp
    
    V_init = -65.0
    m_init = alpha_m(V_init) / (alpha_m(V_init) + beta_m(V_init))
    h_init = alpha_h(V_init) / (alpha_h(V_init) + beta_h(V_init))
    n_init = alpha_n(V_init) / (alpha_n(V_init) + beta_n(V_init))
    state_init = [V_init, m_init, h_init, n_init]
    
    solution = np.zeros((len(t), 4))
    for j in range(len(t)):
        if j == 0:
            solution[j] = state_init
        else:
            t_span = [t[j-1], t[j]]
            sol = odeint(hodgkin_huxley, solution[j-1], t_span, args=(I_ext[j],))
            solution[j] = sol[-1]
    
    V_trace = solution[:, 0]
    m_trace = solution[:, 1]
    h_trace = solution[:, 2]
    n_trace = solution[:, 3]
    
    # Find first spike
    spike_indices = find_peaks(V_trace, height=0.0)[0]
    if len(spike_indices) > 0:
        first_spike = spike_indices[0]
        window = slice(max(0, first_spike - int(20.0/dt)), min(len(t), first_spike + int(30.0/dt)))
        
        ax9_twin = ax9.twinx()
        ax9.plot(t[window], V_trace[window], 'k-', linewidth=2, label='Voltage')
        ax9_twin.plot(t[window], m_trace[window], 'r-', linewidth=1.5, label='m (Na activation)')
        ax9_twin.plot(t[window], h_trace[window], 'b-', linewidth=1.5, label='h (Na inactivation)')
        ax9_twin.plot(t[window], n_trace[window], 'g-', linewidth=1.5, label='n (K activation)')
        
        ax9.set_xlabel('Time (ms)', fontsize=11)
        ax9.set_ylabel('Membrane Voltage (mV)', fontsize=11, color='k')
        ax9_twin.set_ylabel('Gating Variable', fontsize=11)
        ax9.set_title('Gating Variable Dynamics During Action Potential', fontsize=11, fontweight='bold')
        ax9.legend(loc='upper left', fontsize=9)
        ax9_twin.legend(loc='upper right', fontsize=9)
        ax9.grid(True, alpha=0.3)

plt.savefig('hodgkin_huxley_parameter_sweep.png', dpi=300, bbox_inches='tight')
print("\nFigure saved: hodgkin_huxley_parameter_sweep.png")
plt.show()
```

Execute this script by saving it as `hodgkin_huxley_sweep.py` and running `python hodgkin_huxley_sweep.py`. The simulation generates a comprehensive characterization of Hodgkin-Huxley neuron excitability by systematically varying injected current and measuring multiple spike-related metrics. The F-I curve (firing rate versus injected current) quantifies the neuron's input-output transfer function and reveals the linear regime where firing rate scales proportionally with current, the rheobase marking the transition from quiescence to spiking, and potential saturation at high currents where sodium channel inactivation or potassium channel activation limits firing rate.

The spike threshold analysis reveals that threshold voltage varies systematically with current amplitude due to the dynamic nature of sodium and potassium channel activation kinetics. For near-threshold currents, slow depolarization allows more time for potassium channel activation to oppose sodium channel activation, effectively raising the threshold voltage. For larger currents, rapid depolarization brings the neuron to threshold before substantial potassium activation occurs, lowering the effective threshold. This rate-dependent threshold behavior underlies the neuron's ability to act as a temporal filter that responds preferentially to rapid input transients while filtering out slow baseline drifts.

The interspike interval statistics provide insight into spike timing regularity. The coefficient of variation (CV) of the ISI distribution quantifies regularity—CV near zero indicates highly regular spiking (like a clock), while CV near 1.0 indicates irregular Poisson-like spiking. The Hodgkin-Huxley model exhibits low CV values because the deterministic dynamics produce nearly periodic spiking when driven by constant current. Real neurons show higher CV values due to synaptic noise, channel stochasticity, and network fluctuations, but the baseline regular firing pattern established by the intrinsic conductances provides the foundation upon which noise adds variability.

The gating variable dynamics panel reveals the mechanistic basis of action potential generation. The sodium activation variable m rises rapidly during the upstroke (with m³ dependence amplifying the effect), while the sodium inactivation variable h falls simultaneously to terminate sodium influx. The potassium activation variable n rises more slowly (hence "delayed rectifier"), reaching its peak during the falling phase when potassium efflux repolarizes the membrane. The temporal choreography of these three variables—fast sodium activation, slightly slower sodium inactivation, and delayed potassium activation—produces the stereotyped action potential waveform that propagates reliably along axons.

Modify the model parameters to explore how conductance densities shape excitability. Increase the maximum sodium conductance to `g_Na = 180.0` mS/cm² (50% increase) and observe how the rheobase decreases, the F-I curve gain increases, and spike amplitude grows. This heightened sodium conductance makes the neuron more excitable, requiring less current to reach threshold and producing larger amplitude spikes. Conversely, increase the maximum potassium conductance to `g_K = 54.0` mS/cm² (50% increase) and observe the opposite effects—higher rheobase, reduced gain, and more pronounced afterhyperpolarization. These parameter manipulations mirror pharmacological interventions (sodium channel blockers reduce excitability while potassium channel blockers increase excitability) and developmental changes (immature neurons express lower potassium conductance densities, making them more excitable).

The temperature dependence of the Hodgkin-Huxley model provides another crucial calibration parameter. The original squid giant axon experiments were performed at 6.3°C, but mammalian neurons operate at 37°C where reaction rates accelerate according to Q₁₀ relationships (typically Q₁₀ ≈ 3 for ion channel kinetics). To simulate mammalian temperatures, multiply all rate constants by $3^{(T - 6.3)/10}$ where T is the target temperature in Celsius. At 37°C, this yields approximately a 10-fold acceleration of all kinetics, dramatically shortening spike duration and refractory periods while increasing maximum firing rates from ~50 Hz in the squid axon to 200-500 Hz in fast-spiking mammalian interneurons.

The F-I curve gain measurement provides a single number that captures how sensitively a neuron converts synaptic current into spike output. Neurons with high gain (steep F-I curves) amplify small input differences into large rate differences, implementing a high-gain amplifier suitable for detecting weak signals. Neurons with low gain (shallow F-I curves) compress input differences into similar output rates, implementing a dynamic range compressor suitable for encoding information across wide input ranges without saturation. The gain is not a fixed property but can be modulated by neuromodulators that alter conductance densities—norepinephrine increases gain by reducing potassium conductances, while acetylcholine can reduce gain by activating hyperpolarization-activated cation currents.

This exercise establishes the quantitative framework for understanding neuronal excitability as an engineered system with tunable parameters, transfer functions, and operating ranges. The Hodgkin-Huxley model serves as the foundation for virtually all modern computational neuroscience, from single-compartment integrate-and-fire simplifications to multi-compartment models with dozens of distinct ion channel types. The parameter sweep methodology generalizes to any neuronal model—systematically vary input parameters, measure output metrics, and construct response curves that reveal fundamental operating principles.

## Exercise 3: Boundary Condition Stress Testing & Uncertainty Analysis

### Experimental Context: Synaptic Integration, Stochastic Fluctuations, and Network Synchronization

The nervous system operates far from the idealized conditions assumed in deterministic models—synaptic inputs arrive stochastically with Poisson-like timing statistics, ion channels open and close randomly according to voltage-dependent transition rates, and neurons exist within recurrent networks where collective dynamics generate emergent synchronization patterns. This exercise stress-tests the Hodgkin-Huxley model under realistic boundary conditions by adding synaptic noise, quantifying threshold variability from trial-to-trial fluctuations, and analyzing phase synchronization in coupled neuron networks. The goal is to identify the operating regime boundaries where deterministic predictions break down and stochastic effects dominate.

Synaptic noise arises from the random arrival times of presynaptic action potentials and the stochastic release of neurotransmitter vesicles at individual synapses. A typical cortical neuron receives 5,000-10,000 synaptic inputs, with spontaneous firing rates of 1-10 Hz in the presynaptic population producing approximately 10,000-50,000 synaptic events per second. Each synaptic event produces a conductance transient with amplitude 10-100 pS (picosiemens) and duration 1-5 ms, generating a continuous background fluctuation in membrane potential with standard deviation 2-5 mV. This noise profoundly affects neuronal dynamics by jittering spike timing, lowering effective threshold, and enabling spontaneous spiking even below the deterministic rheobase.

The following Python script implements a conductance-based synaptic noise model where excitatory and inhibitory synaptic events arrive as independent Poisson processes, each producing transient conductance changes that drive current according to $I_{\text{syn}} = g_{\text{syn}}(t)(V - E_{\text{syn}})$. The simulation runs multiple trials with identical mean input current but different noise realizations, then analyzes trial-to-trial variability in spike timing, threshold voltage, and firing rate to quantify how stochasticity affects neuronal reliability:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde

# Hodgkin-Huxley model (same as Exercise 2)
C_m = 1.0
g_Na = 120.0
g_K = 36.0
g_L = 0.3
E_Na = 50.0
E_K = -77.0
E_L = -54.387

def alpha_m(V):
    return 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0))

def beta_m(V):
    return 4.0 * np.exp(-(V + 65.0) / 18.0)

def alpha_h(V):
    return 0.07 * np.exp(-(V + 65.0) / 20.0)

def beta_h(V):
    return 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))

def alpha_n(V):
    return 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0))

def beta_n(V):
    return 0.125 * np.exp(-(V + 65.0) / 80.0)

# Synaptic noise parameters
rate_exc = 2000.0  # Excitatory synaptic event rate (Hz)
rate_inh = 1000.0  # Inhibitory synaptic event rate (Hz)
g_exc_max = 0.05  # Peak excitatory conductance per event (mS/cm²)
g_inh_max = 0.10  # Peak inhibitory conductance per event (mS/cm²)
E_exc = 0.0  # Excitatory reversal potential (mV)
E_inh = -80.0  # Inhibitory reversal potential (mV)
tau_syn = 5.0  # Synaptic conductance decay time constant (ms)

# Simulation parameters
dt = 0.01  # Time step (ms)
t_total = 500.0  # Total simulation time (ms)
t = np.arange(0, t_total, dt)
n_trials = 50  # Number of trials with different noise realizations

I_mean = 8.0  # Mean injected current (μA/cm²) - near threshold

print("=== Synaptic Noise and Stochastic Threshold Analysis ===\n")
print(f"Synaptic Noise Parameters:")
print(f"  Excitatory event rate: {rate_exc} Hz")
print(f"  Inhibitory event rate: {rate_inh} Hz")
print(f"  Excitatory reversal potential: {E_exc} mV")
print(f"  Inhibitory reversal potential: {E_inh} mV")
print(f"  Synaptic time constant: {tau_syn} ms\n")
print(f"Simulation: {n_trials} trials with I_mean = {I_mean} μA/cm²\n")

# Storage for trial-by-trial analysis
all_spike_times = []
all_spike_counts = []
all_first_spike_times = []
all_threshold_voltages = []
all_voltage_traces = []

for trial in range(n_trials):
    # Generate Poisson synaptic event times
    n_exc_events = np.random.poisson(rate_exc * t_total / 1000.0)
    n_inh_events = np.random.poisson(rate_inh * t_total / 1000.0)
    
    exc_times = np.sort(np.random.uniform(0, t_total, n_exc_events))
    inh_times = np.sort(np.random.uniform(0, t_total, n_inh_events))
    
    # Compute synaptic conductances at each time point
    g_exc = np.zeros_like(t)
    g_inh = np.zeros_like(t)
    
    for t_exc in exc_times:
        onset_idx = int(t_exc / dt)
        if onset_idx < len(t):
            decay = np.exp(-(t[onset_idx:] - t_exc) / tau_syn)
            g_exc[onset_idx:] += g_exc_max * decay
    
    for t_inh in inh_times:
        onset_idx = int(t_inh / dt)
        if onset_idx < len(t):
            decay = np.exp(-(t[onset_idx:] - t_inh) / tau_syn)
            g_inh[onset_idx:] += g_inh_max * decay
    
    # Modified Hodgkin-Huxley with synaptic currents
    def hh_with_synapses(state, t_idx):
        V, m, h, n = state
        
        # Ionic currents
        I_Na = g_Na * m**3 * h * (V - E_Na)
        I_K = g_K * n**4 * (V - E_K)
        I_L = g_L * (V - E_L)
        
        # Synaptic currents
        I_syn_exc = g_exc[t_idx] * (V - E_exc)
        I_syn_inh = g_inh[t_idx] * (V - E_inh)
        
        # Total current
        I_total = I_mean - I_Na - I_K - I_L - I_syn_exc - I_syn_inh
        
        # Voltage derivative
        dVdt = I_total / C_m
        
        # Gating variables
        dmdt = alpha_m(V) * (1.0 - m) - beta_m(V) * m
        dhdt = alpha_h(V) * (1.0 - h) - beta_h(V) * h
        dndt = alpha_n(V) * (1.0 - n) - beta_n(V) * n
        
        return [dVdt, dmdt, dhdt, dndt]
    
    # Initial conditions
    V_init = -65.0
    m_init = alpha_m(V_init) / (alpha_m(V_init) + beta_m(V_init))
    h_init = alpha_h(V_init) / (alpha_h(V_init) + beta_h(V_init))
    n_init = alpha_n(V_init) / (alpha_n(V_init) + beta_n(V_init))
    state_init = [V_init, m_init, h_init, n_init]
    
    # Integrate with synaptic noise
    solution = np.zeros((len(t), 4))
    solution[0] = state_init
    
    for i in range(1, len(t)):
        state = solution[i-1]
        derivs = hh_with_synapses(state, i)
        solution[i] = state + dt * np.array(derivs)
    
    V_trace = solution[:, 0]
    all_voltage_traces.append(V_trace)
    
    # Detect spikes
    spike_indices, _ = find_peaks(V_trace, height=0.0, distance=int(2.0/dt))
    spike_times = t[spike_indices]
    n_spikes = len(spike_times)
    
    all_spike_times.append(spike_times)
    all_spike_counts.append(n_spikes)
    
    # First spike time and threshold
    if n_spikes > 0:
        first_spike_time = spike_times[0]
        all_first_spike_times.append(first_spike_time)
        
        # Estimate threshold
        first_spike_idx = spike_indices[0]
        search_window = slice(max(0, first_spike_idx - int(10.0/dt)), first_spike_idx)
        dVdt = np.gradient(V_trace[search_window], dt)
        threshold_idx = np.where(dVdt > 10.0)[0]
        if len(threshold_idx) > 0:
            threshold_V = V_trace[search_window][threshold_idx[0]]
            all_threshold_voltages.append(threshold_V)
        else:
            all_threshold_voltages.append(np.nan)
    
    if (trial + 1) % 10 == 0:
        print(f"Completed {trial + 1}/{n_trials} trials")

# Convert to numpy arrays
all_spike_counts = np.array(all_spike_counts)
all_first_spike_times = np.array(all_first_spike_times)
all_threshold_voltages = np.array([v for v in all_threshold_voltages if not np.isnan(v)])

# Statistical analysis
mean_spike_count = np.mean(all_spike_counts)
std_spike_count = np.std(all_spike_counts)
mean_first_spike_time = np.mean(all_first_spike_times)
std_first_spike_time = np.std(all_first_spike_times)
mean_threshold = np.mean(all_threshold_voltages)
std_threshold = np.std(all_threshold_voltages)
cv_first_spike = std_first_spike_time / mean_first_spike_time if mean_first_spike_time > 0 else np.nan

print(f"\n=== Statistical Analysis Over {n_trials} Trials ===")
print(f"Spike Count: {mean_spike_count:.1f} ± {std_spike_count:.1f} spikes")
print(f"First Spike Latency: {mean_first_spike_time:.1f} ± {std_first_spike_time:.1f} ms (CV = {cv_first_spike:.3f})")
print(f"Threshold Voltage: {mean_threshold:.2f} ± {std_threshold:.2f} mV")
print(f"Trials with no spikes: {np.sum(all_spike_counts == 0)}/{n_trials}")

# Visualization
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

# Panel 1: Overlay of 10 example voltage traces
ax1 = fig.add_subplot(gs[0, :])
for i in range(min(10, n_trials)):
    ax1.plot(t, all_voltage_traces[i], linewidth=0.8, alpha=0.7)
ax1.set_xlabel('Time (ms)', fontsize=11)
ax1.set_ylabel('Membrane Voltage (mV)', fontsize=11)
ax1.set_title(f'Voltage Traces from 10 Trials (I_mean = {I_mean} μA/cm² + Synaptic Noise)', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Panel 2: Raster plot of spike times across all trials
ax2 = fig.add_subplot(gs[1, :])
for trial_idx, spike_times in enumerate(all_spike_times):
    ax2.plot(spike_times, np.ones_like(spike_times) * trial_idx, 'k|', markersize=8)
ax2.set_xlabel('Time (ms)', fontsize=11)
ax2.set_ylabel('Trial Number', fontsize=11)
ax2.set_title('Raster Plot: Spike Timing Across Trials', fontsize=12, fontweight='bold')
ax2.set_ylim([-1, n_trials])
ax2.grid(True, alpha=0.3, axis='x')

# Panel 3: Histogram of spike counts
ax3 = fig.add_subplot(gs[2, 0])
ax3.hist(all_spike_counts, bins=range(int(np.min(all_spike_counts)), int(np.max(all_spike_counts))+2), 
         edgecolor='black', alpha=0.7)
ax3.axvline(mean_spike_count, color='red', linestyle='--', linewidth=2, label=f'Mean = {mean_spike_count:.1f}')
ax3.set_xlabel('Number of Spikes', fontsize=11)
ax3.set_ylabel('Number of Trials', fontsize=11)
ax3.set_title('Spike Count Distribution', fontsize=11, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3, axis='y')

# Panel 4: Histogram of first spike latencies
ax4 = fig.add_subplot(gs[2, 1])
ax4.hist(all_first_spike_times, bins=20, edgecolor='black', alpha=0.7)
ax4.axvline(mean_first_spike_time, color='red', linestyle='--', linewidth=2, 
            label=f'Mean = {mean_first_spike_time:.1f} ms')
ax4.set_xlabel('First Spike Latency (ms)', fontsize=11)
ax4.set_ylabel('Number of Trials', fontsize=11)
ax4.set_title('First Spike Timing Variability', fontsize=11, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3, axis='y')

# Panel 5: Histogram of threshold voltages
ax5 = fig.add_subplot(gs[2, 2])
ax5.hist(all_threshold_voltages, bins=20, edgecolor='black', alpha=0.7)
ax5.axvline(mean_threshold, color='red', linestyle='--', linewidth=2, 
            label=f'Mean = {mean_threshold:.2f} mV')
ax5.set_xlabel('Threshold Voltage (mV)', fontsize=11)
ax5.set_ylabel('Number of Trials', fontsize=11)
ax5.set_title('Threshold Variability from Noise', fontsize=11, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(True, alpha=0.3, axis='y')

# Panel 6: Mean voltage trajectory with confidence bands
ax6 = fig.add_subplot(gs[3, :2])
voltage_array = np.array(all_voltage_traces)
mean_voltage = np.mean(voltage_array, axis=0)
std_voltage = np.std(voltage_array, axis=0)
ax6.plot(t, mean_voltage, 'b-', linewidth=2, label='Mean Voltage')
ax6.fill_between(t, mean_voltage - std_voltage, mean_voltage + std_voltage, 
                  alpha=0.3, color='blue', label='±1 SD')
ax6.set_xlabel('Time (ms)', fontsize=11)
ax6.set_ylabel('Membrane Voltage (mV)', fontsize=11)
ax6.set_title('Mean Voltage Trajectory with Confidence Bands', fontsize=11, fontweight='bold')
ax6.legend(fontsize=9)
ax6.grid(True, alpha=0.3)

# Panel 7: Interspike interval distribution (pooled across all trials)
ax7 = fig.add_subplot(gs[3, 2])
all_isis = []
for spike_times in all_spike_times:
    if len(spike_times) > 1:
        isis = np.diff(spike_times)
        all_isis.extend(isis)

if len(all_isis) > 0:
    all_isis = np.array(all_isis)
    ax7.hist(all_isis, bins=30, edgecolor='black', alpha=0.7, density=True)
    mean_isi = np.mean(all_isis)
    ax7.axvline(mean_isi, color='red', linestyle='--', linewidth=2, 
                label=f'Mean ISI = {mean_isi:.1f} ms')
    ax7.set_xlabel('Interspike Interval (ms)', fontsize=11)
    ax7.set_ylabel('Probability Density', fontsize=11)
    ax7.set_title('ISI Distribution (Pooled)', fontsize=11, fontweight='bold')
    ax7.legend(fontsize=9)
    ax7.grid(True, alpha=0.3, axis='y')

plt.savefig('synaptic_noise_stochastic_analysis.png', dpi=300, bbox_inches='tight')
print("\nFigure saved: synaptic_noise_stochastic_analysis.png")
plt.show()

# Quantify reliability: correlation between trials
print("\n=== Reliability and Trial-to-Trial Variability ===")
if len(all_first_spike_times) > 1:
    reliability = 1.0 - (std_first_spike_time / mean_first_spike_time)
    print(f"Temporal Reliability (1 - CV): {reliability:.3f}")
    print(f"Interpretation: 1.0 = perfectly reliable, 0.0 = completely variable")

# Fano factor for spike counts
fano_factor = std_spike_count**2 / mean_spike_count if mean_spike_count > 0 else np.nan
print(f"\nFano Factor (variance/mean): {fano_factor:.3f}")
print(f"Interpretation: 1.0 = Poisson process, <1.0 = more regular, >1.0 = more bursty")
```

Execute this script as `python synaptic_noise_analysis.py`. The simulation generates fifty trials with identical mean current but different realizations of stochastic synaptic input, then analyzes how noise affects spike timing precision, threshold variability, and firing rate reliability. The raster plot reveals trial-to-trial jitter in spike timing—even though all trials receive the same mean input, the random fluctuations from synaptic noise cause spikes to occur at different times across trials, with jitter typically ranging from 5-20 ms for near-threshold inputs.

The first spike latency distribution quantifies the temporal precision of the neural response. The coefficient of variation (CV) of first spike times provides a dimensionless measure of reliability—CV values near 0.1-0.2 indicate highly reliable spike timing where the stimulus precisely controls spike occurrence, while CV values approaching 1.0 indicate unreliable timing dominated by noise fluctuations. This reliability depends critically on the signal-to-noise ratio: stronger mean currents (larger signal) produce more reliable responses, while higher synaptic event rates (larger noise) reduce reliability.

The threshold voltage histogram reveals that the effective spike threshold is not a fixed voltage but rather a stochastic quantity distributed over several millivolts. This threshold variability arises because the instantaneous membrane conductance state at the moment of threshold crossing differs across trials—if an excitatory synaptic event occurs just before threshold, it provides additional depolarizing drive that effectively lowers threshold, while an inhibitory event raises it. The mean threshold shifts to more hyperpolarized values compared to the deterministic case because fluctuations allow the neuron to occasionally reach threshold via rare large positive fluctuations even when the mean input is below the deterministic rheobase.

The Fano factor analysis examines whether spike counts exhibit Poisson statistics (Fano factor = 1.0), sub-Poisson regularity (Fano factor < 1.0), or super-Poisson burstiness (Fano factor > 1.0). The Hodgkin-Huxley model with moderate noise typically produces Fano factors of 0.3-0.7, indicating more regular spiking than a Poisson process because the refractory period enforces a minimum interspike interval. Real cortical neurons show Fano factors ranging from 0.5 to 1.5 depending on behavioral state, with higher values during spontaneous activity (larger network fluctuations) and lower values during stimulus-driven responses (stimulus constrains variability).

Modify the noise parameters to explore different operating regimes. Increase the excitatory synaptic rate to `rate_exc = 4000.0` Hz while decreasing individual event amplitude to `g_exc_max = 0.025` mS/cm² (double the rate, halve the amplitude) to maintain the same mean input while increasing fluctuation frequency. This produces higher-frequency, smaller-amplitude membrane potential fluctuations that more closely resemble the continuous diffusion approximation underlying stochastic integrate-and-fire models. Observe how the threshold distribution narrows and the CV of first spike times decreases because the higher event rate produces more Gaussian-like fluctuations with reduced rare-event probability.

Alternatively, create a balanced excitation-inhibition regime by setting `rate_exc = 3000.0` Hz, `rate_inh = 2400.0` Hz, and adjusting conductances so that the mean excitatory and inhibitory currents nearly cancel. In this regime, the neuron operates near resting potential on average but exhibits large fluctuations as the stochastic imbalance between excitation and inhibition drives membrane potential excursions. This balanced state captures key features of cortical network dynamics where neurons fire irregularly despite high synaptic input rates because excitation and inhibition track each other closely on average while fluctuating independently on short timescales.

The uncertainty analysis framework established here generalizes to all experimental neuroscience measurements. The trial-to-trial variability observed in recordings reflects the combined effects of measurement noise (electrode noise, amplifier artifacts), biological stochasticity (channel noise, synaptic variability), and network fluctuations (ongoing dynamics in presynaptic populations). Quantifying this variability through repeated trials allows separation of systematic effects (reproducible responses to stimuli) from noise (trial-to-trial jitter), enabling detection of subtle signals embedded in noisy recordings and rigorous statistical testing of hypotheses about neural coding and computation.

The transition from deterministic to stochastic descriptions represents a fundamental boundary condition in neuroscience modeling. When synaptic noise is weak compared to mean input, deterministic models like Hodgkin-Huxley accurately predict average responses and the noise can be treated perturbatively. When noise becomes comparable to or exceeds mean input, stochastic formulations become necessary, typically implemented through stochastic differential equations or Langevin formulations where Gaussian white noise drives voltage fluctuations. The analysis tools developed here—CV of spike timing, Fano factors, response reliability metrics—apply across this continuum and enable quantitative assessment of when noise fundamentally alters neural computation versus merely adding variance around deterministic predictions.

## Laboratory Cheat Sheet & Metric Verification Guide

### Quick Reference: Essential Neuroscience Formulas and Parameters

**Nernst Potential (Single Ion Species)**

The equilibrium potential for ion X: $E_X = \frac{RT}{zF} \ln\frac{[X]_{\text{out}}}{[X]_{\text{in}}} = \frac{58 \text{ mV}}{z} \log_{10}\frac{[X]_{\text{out}}}{[X]_{\text{in}}}$ at 25°C

Typical values: $E_K \approx -85$ mV, $E_{Na} \approx +60$ mV, $E_{Cl} \approx -70$ mV, $E_{Ca} \approx +120$ mV

**Goldman-Hodgkin-Katz Equation (Multiple Ions)**

Resting membrane potential: $V_m = \frac{RT}{F} \ln\frac{P_K[K^+]_{\text{out}} + P_{Na}[Na^+]_{\text{out}} + P_{Cl}[Cl^-]_{\text{in}}}{P_K[K^+]_{\text{in}} + P_{Na}[Na^+]_{\text{in}} + P_{Cl}[Cl^-]_{\text{out}}}$

At rest: $P_K : P_{Na} : P_{Cl} \approx 1.0 : 0.04 : 0.45$, yielding $V_m \approx -70$ mV

**Passive Membrane Properties**

Input resistance: $R_{\text{in}} = \frac{\Delta V}{I}$ (typical range 50-500 MΩ)

Membrane time constant: $\tau_m = R_{\text{in}} C_m$ (typical range 5-40 ms)

Membrane capacitance: $C_m = c_m \cdot A_{\text{total}}$ where $c_m \approx 1$ μF/cm²

Space constant: $\lambda = \sqrt{\frac{r_m}{r_i}}$ (typical range 100-1000 μm in dendrites)

**Cable Equation**

One-dimensional passive cable: $\lambda^2 \frac{\partial^2 V}{\partial x^2} = \tau_m \frac{\partial V}{\partial t} + (V - V_{\text{rest}})$

Steady-state solution: $V(x) = V_0 \exp(-x/\lambda)$ (exponential decay with distance)

**Hodgkin-Huxley Action Potential**

Voltage equation: $C_m \frac{dV}{dt} = I_{\text{ext}} - \bar{g}_{Na} m^3 h (V - E_{Na}) - \bar{g}_K n^4 (V - E_K) - g_L (V - E_L)$

Sodium conductance: $g_{Na} = \bar{g}_{Na} m^3 h$ (cubic activation, linear inactivation)

Potassium conductance: $g_K = \bar{g}_K n^4$ (fourth-power delayed activation)

Gating variable kinetics: $\frac{dx}{dt} = \alpha_x(V)(1-x) - \beta_x(V) x$

**Synaptic Transmission**

Synaptic current: $I_{\text{syn}} = g_{\text{syn}}(t)(V - E_{\text{syn}})$

Conductance waveform: $g_{\text{syn}}(t) = \bar{g}_{\text{syn}} \exp(-t/\tau_{\text{syn}})$ for $t \geq 0$

AMPA receptors: $E_{\text{syn}} = 0$ mV, $\tau_{\text{syn}} = 1-5$ ms

GABA_A receptors: $E_{\text{syn}} = -70$ mV, $\tau_{\text{syn}} = 5-10$ ms

**Spike Timing Metrics**

Interspike interval: $\text{ISI} = t_{n+1} - t_n$

Coefficient of variation: $\text{CV}_{\text{ISI}} = \frac{\sigma_{\text{ISI}}}{\mu_{\text{ISI}}}$ (regularity measure)

Firing rate: $f = \frac{N_{\text{spikes}}}{T}$ (spike count / observation window)

Fano factor: $F = \frac{\sigma^2_N}{\mu_N}$ (spike count variability measure)

### Verification Commands and Unit Tests

**Environment Verification**

Check Python scientific stack installation:
```bash
python -c 'import numpy; print("NumPy:", numpy.__version__)'
python -c 'import scipy; print("SciPy:", scipy.__version__)'
python -c 'import matplotlib; print("Matplotlib:", matplotlib.__version__)'
```

Expected output: NumPy ≥ 1.20, SciPy ≥ 1.7, Matplotlib ≥ 3.3

**Numerical Integration Accuracy**

Test Hodgkin-Huxley integration against analytical steady-state:
```python
import numpy as np
from scipy.integrate import odeint

# At resting potential, all derivatives should be near zero
V_rest = -65.0
m_inf = 0.05
h_inf = 0.60
n_inf = 0.32

# Run 100 ms at rest with no external current
def hh_test(state, t):
    V, m, h, n = state
    # [implementation as in Exercise 2]
    return [dVdt, dmdt, dhdt, dndt]

t_test = np.linspace(0, 100, 10000)
state_init = [V_rest, m_inf, h_inf, n_inf]
solution = odeint(hh_test, state_init, t_test, args=(0.0,))

# Verify steady-state stability
assert np.abs(solution[-1, 0] - V_rest) < 0.1, "Voltage drift at rest"
assert np.abs(solution[-1, 1] - m_inf) < 0.01, "Gating variable drift"
print("✓ Numerical integration stable at rest")
```

**Spike Detection Validation**

Verify spike detection captures all action potentials:
```python
from scipy.signal import find_peaks

# Generate known spike train
t = np.linspace(0, 100, 10000)
V_true = -65 + 20*np.sin(2*np.pi*10*t/1000)  # 10 Hz oscillation
spike_times_true = np.arange(5, 100, 10)  # Spikes every 10 ms

# Add spikes at known times
for t_spike in spike_times_true:
    idx = int(t_spike * 100)
    if idx < len(V_true):
        V_true[idx:idx+20] += 80 * np.exp(-np.arange(20)/2)  # Spike waveform

# Detect spikes
peaks, _ = find_peaks(V_true, height=0.0, distance=100)
spike_times_detected = t[peaks]

# Verify detection
assert len(spike_times_detected) == len(spike_times_true), f"Missed spikes: {len(spike_times_true) - len(spike_times_detected)}"
print(f"✓ Detected {len(spike_times_detected)}/{len(spike_times_true)} spikes correctly")
```

**Parameter Extraction Uncertainty**

Quantify measurement error propagation:
```python
# Simulate parameter extraction with known ground truth
R_in_true = 150e6  # Ohms
tau_m_true = 15e-3  # seconds
sigma_noise = 0.5e-3  # 0.5 mV RMS noise

n_measurements = 100
R_in_measured = []
tau_m_measured = []

for _ in range(n_measurements):
    # [Generate synthetic data with noise]
    # [Extract parameters as in Exercise 1]
    R_in_measured.append(R_in_extracted)
    tau_m_measured.append(tau_extracted)

R_in_mean = np.mean(R_in_measured)
R_in_std = np.std(R_in_measured)
print(f"R_in: {R_in_mean*1e-6:.1f} ± {R_in_std*1e-6:.1f} MΩ (true: {R_in_true*1e-6:.1f} MΩ)")
print(f"Relative error: {np.abs(R_in_mean - R_in_true)/R_in_true * 100:.2f}%")
```

### Common Pitfalls and Debugging Strategies

**Problem: Hodgkin-Huxley model produces unstable numerical integration**

Diagnostic: Voltage diverges to extreme values (>200 mV or <-200 mV)

Solution: Reduce time step to dt ≤ 0.01 ms, use implicit integration (odeint default), check initial conditions are at steady-state

**Problem: No spikes detected despite current injection**

Diagnostic: Voltage depolarizes but never crosses 0 mV threshold

Solution: Current amplitude too low (increase I_ext), maximal conductances incorrect (check g_Na >> g_K), integration time too short (extend simulation)

**Problem: Exponential fit to membrane charging fails to converge**

Diagnostic: curve_fit raises RuntimeError or returns nonsensical parameters

Solution: Exclude initial transient (first 5-10 ms after step onset), verify data window contains clear exponential, improve initial parameter guess, increase maxfev iteration limit

**Problem: Synaptic noise produces no observable membrane potential fluctuations**

Diagnostic: Voltage trace appears identical across trials

Solution: Increase synaptic event rates or conductance amplitudes, verify synaptic conductance time series is non-zero, check reversal potentials differ from resting potential

**Problem: Spike timing jitter exceeds expected variability**

Diagnostic: CV of first spike times > 0.5 with moderate noise

Solution: Reduce time step for better temporal resolution, verify spike detection threshold appropriate, check mean current is sufficiently above rheobase to produce reliable responses

### Physical Constants and Conversion Factors

Universal gas constant: R = 8.314 J·mol⁻¹·K⁻¹

Faraday constant: F = 96485 C·mol⁻¹

Room temperature: T ≈ 298 K (25°C)

Physiological temperature: T ≈ 310 K (37°C)

Elementary charge: e = 1.602 × 10⁻¹⁹ C

Boltzmann constant: k_B = 1.381 × 10⁻²³ J·K⁻¹

Thermal voltage at 25°C: V_T = k_B T / e ≈ 25.7 mV

Unit conversions: 1 μm = 10⁻⁶ m, 1 mV = 10⁻³ V, 1 pA = 10⁻¹² A, 1 μF = 10⁻⁶ F, 1 mS = 10⁻³ S

### Biological Parameter Ranges

Neuronal membrane capacitance: 5-500 pF (typical 50-150 pF for soma)

Input resistance: 10-1000 MΩ (small interneurons high, large pyramidal neurons low)

Membrane time constant: 3-50 ms (fast-spiking interneurons short, pyramidal neurons long)

Resting potential: -60 to -80 mV (most cortical neurons -70 ± 5 mV)

Action potential amplitude: 80-110 mV (measured from resting to peak)

Action potential threshold: -45 to -60 mV (dynamic, current-dependent)

Action potential duration: 0.3-2.0 ms (duration at half-maximum amplitude)

Maximum firing rate: 10-600 Hz (regular-spiking ~100 Hz, fast-spiking ~600 Hz)

Synaptic conductance: 10-1000 pS (single synapse), 1-10 nS (total synaptic input)

Synaptic time constant: 1-20 ms (AMPA fast ~2 ms, NMDA slow ~50 ms, GABA ~5-10 ms)

This laboratory guide provides the complete experimental foundation for investigating neuronal electrical properties, action potential generation, and synaptic integration using quantitative biophysical measurements and computational modeling. The exercises progress from passive membrane characterization through active spike dynamics to stochastic network behavior, establishing the measurement protocols, analysis techniques, and uncertainty quantification methods essential for rigorous neuroscience research. Each exercise emphasizes the direct connection between biophysical mechanisms and experimental observables, enabling you to interpret electrophysiology recordings, validate computational models, and design experiments that test specific hypotheses about neural function.
