# Operational Verification Labs: Test Measurement

## Objective & Operational Lab Setup

Test and measurement constitute the empirical foundation upon which all hardware engineering rests. Without rigorous, repeatable measurement protocols, circuit performance degenerates into speculation, transient failures evade diagnosis, and product qualification collapses under the weight of unquantified margin. This laboratory sequence trains the hardware practitioner to extract ground-truth electrical parameters from physical systems using oscilloscopes, spectrum analyzers, network analyzers, multimeters, and signal generators, then cross-correlate those measurements against datasheet specifications, simulation predictions, and system-level performance requirements. The operative mindset is forensic: every voltage ripple, frequency spur, and impedance anomaly reveals a causal chain linking component tolerances, layout parasitics, and environmental stress factors. Mastery of test measurement transforms the engineer from a passive observer of circuit behavior into an active interrogator of physical reality.

The laboratory environment demands a disciplined instrumentation bench. Begin with a four-channel digital storage oscilloscope (DSO) offering at minimum 100 MHz analog bandwidth, 1 GSa/s sample rate, and 10 Mpts memory depth per channel. Tektronix MSO4000 series, Keysight InfiniiVision 4000X, or Rigol DS4000 series instruments satisfy these requirements. Supplement the oscilloscope with a dual-channel arbitrary waveform generator capable of 50 MHz output frequency and 14-bit vertical resolution—Siglent SDG2042X or Keysight 33500B series provide adequate fidelity. For DC and low-frequency AC measurements, deploy a 6½-digit benchtop multimeter such as the Keysight 34461A, which resolves microvolts and nanoamperes while maintaining traceable calibration linearity. High-frequency and RF characterization requires a spectrum analyzer spanning DC to 3 GHz with phase noise floor below -140 dBc/Hz at 10 kHz offset; Siglent SSA3032X or Rigol DSA815-TG units integrate tracking generators for swept-frequency analysis. Network analysis, essential for impedance matching and filter verification, necessitates a vector network analyzer (VNA) covering 300 kHz to 3 GHz with two-port S-parameter measurement capability—NanoVNA-H4 or Rigol VNA1032 serve as cost-effective entry points, while Keysight FieldFox or Copper Mountain Technologies TR1300/1 deliver laboratory-grade accuracy.

Physical connectivity demands precision. Stock the bench with a comprehensive probe inventory: 10:1 passive voltage probes rated for 300 MHz bandwidth and 10 MΩ input impedance, differential voltage probes for floating ground measurements, current probes with sub-nanosecond rise time response, and high-impedance active FET probes for minimal circuit loading. Each probe introduces parasitic capacitance, inductance, and resistive loading that corrupts the measurement if left uncompensated—prior to every session, execute probe compensation against the oscilloscope's square-wave calibration output, adjusting the trimmer capacitor until rise time overshoot and undershoot vanish. For RF measurements, employ SMA and BNC coaxial cables with swept return loss better than 20 dB across the operating band, and terminate unused ports with precision 50 Ω loads to suppress standing waves. Grounding discipline is non-negotiable: bond all instrument chassis to a common star ground point via braided copper strap, and minimize ground loop area by routing return currents through the ground plane of a professionally fabricated PCB test fixture rather than through flying leads.

Signal integrity verification requires known-good reference artifacts. Construct a calibration fixture incorporating precision resistor dividers (0.1% tolerance metal film resistors in Kelvin four-wire configuration), RC low-pass filters with calculated corner frequencies, and crystal oscillator modules (TCXO or OCXO) delivering sub-ppm frequency stability. Cross-check oscilloscope timebase accuracy against a GPS-disciplined 10 MHz reference, and validate vertical gain by measuring a traceable voltage standard. For frequency-domain work, calibrate the VNA using a mechanical calibration kit (open, short, load, through standards) before every measurement session, storing correction coefficients in instrument memory. Document all calibration events in a laboratory notebook with traceability to NIST or equivalent national metrology institute standards.

Software infrastructure augments manual measurement with automated data acquisition and post-processing. Install Python 3.11 with NumPy 1.24, SciPy 1.10, Matplotlib 3.7, and PyVISA 1.13 for instrument control via SCPI (Standard Commands for Programmable Instruments). Most modern oscilloscopes, signal generators, and spectrum analyzers expose Ethernet or USB-TMC connectivity; enumerate available VISA resources using `pyvisa.ResourceManager().list_resources()` and establish persistent TCP/IP sockets for high-throughput waveform transfer. For offline analysis, deploy MATLAB R2023a or GNU Octave 8.2 with Signal Processing and Control System toolboxes, enabling FFT spectral analysis, digital filter synthesis, and time-domain convolution. LTspice XVII provides circuit simulation for pre-measurement prediction and post-measurement correlation—construct SPICE netlists mirroring the physical test fixture, incorporating measured parasitic capacitance and inductance extracted via VNA S-parameter files.

Environmental control stabilizes measurement repeatability. Operate the laboratory at 23 ± 2 °C ambient temperature with relative humidity between 40% and 60%, minimizing thermal drift in precision resistors and oscillator frequency. Shield sensitive measurements from electromagnetic interference (EMI) by enclosing the device under test (DUT) within a Faraday cage constructed from copper mesh or aluminum sheet, with RF-tight feedthrough connectors for power and signal access. When measuring microvolt-level signals or sub-picoampere leakage currents, eliminate triboelectric noise by grounding all conductive surfaces and personnel via wrist straps, and power the DUT from a low-noise linear bench supply rather than a switching regulator.

The following exercises progress from foundational DC and time-domain measurements through frequency-domain characterization to stress testing under temperature and voltage extremes. Each exercise concludes with a quantitative acceptance criterion derived from industry standards or manufacturer datasheets. Document all measurements in a structured format: timestamp, instrument settings (bandwidth, coupling, attenuation, averaging), environmental conditions, and observed values with uncertainty bounds. This discipline transforms raw oscilloscope screenshots into defensible engineering evidence.

---

## Exercise 1: Foundational Practical Implementation

### Exercise 1.1: DC Voltage and Current Measurement with Multimeter Uncertainty Analysis

The 6½-digit benchtop multimeter forms the foundation of DC electrical metrology. Unlike handheld meters that sacrifice accuracy for portability, benchtop instruments achieve sub-ppm linearity through precision voltage references, auto-zero correction, and temperature-compensated ADCs. This exercise establishes a baseline measurement protocol for DC voltage, current, and resistance, quantifying the total uncertainty budget from instrument specifications, thermal drift, and contact resistance.

Connect the Keysight 34461A multimeter to a laboratory-grade voltage reference source—a Linear Technology LTZ1000-based 7 V reference or Analog Devices ADR1000 10 V reference provides long-term stability within 2 ppm/year. Power the reference from a clean 15 V linear supply, allowing a 30-minute warm-up period to reach thermal equilibrium. Configure the multimeter for DC voltage measurement in the 10 V range with 6½-digit resolution (0.1 µV least significant digit), enabling auto-zero to null offset voltage and setting integration time to 10 power line cycles (PLC) to reject 50/60 Hz mains interference. Trigger a single measurement and record the reading: a properly calibrated instrument should display within ±(0.0030% of reading + 0.0005% of range) per the manufacturer's one-year accuracy specification. For a 7 V reference, this yields ±(0.21 mV + 0.5 mV) = ±0.71 mV total uncertainty.

Thermal coefficient dominates long-term drift. While the multimeter maintains thermal stability, the voltage reference exhibits a temperature coefficient (tempco) typically specified as 0.05 ppm/°C. A 2 °C ambient temperature fluctuation induces 7 V × 0.05 ppm/°C × 2 °C = 0.7 µV drift—negligible compared to multimeter uncertainty. However, self-heating within the reference IC can elevate junction temperature by 10 °C above ambient, injecting 3.5 µV error. Mitigate this by mounting the reference on a thermally conductive aluminum block and enclosing it in expanded polystyrene foam insulation.

DC current measurement requires four-wire Kelvin sensing to eliminate lead resistance errors. Construct a test circuit comprising a precision 1 kΩ resistor (0.01% tolerance, 5 ppm/°C tempco, Vishay Z-Foil series) in series with the DUT current path. Drive the circuit from a programmable DC power supply (Keysight E36312A) set to 5 V output. Configure the multimeter for DC current measurement in the 100 mA range, inserting the meter in series with the load. Simultaneously measure voltage across the 1 kΩ sense resistor using a second multimeter in four-wire resistance mode. Calculate current via Ohm's law: if the voltage drop reads 3.5000 V across 1000.0 Ω, current equals 3.5000 mA. Cross-check this against the direct current meter reading—discrepancies exceeding 0.1% indicate burden voltage from the ammeter's internal shunt resistor corrupting the measurement.

Four-wire resistance measurement eliminates contact and lead resistance, essential for sub-ohm measurements. Select a 10 Ω power resistor (Vishay Dale wirewound, 1% tolerance) as the DUT. Connect the multimeter's SENSE HI and SENSE LO terminals directly to the resistor body, bypassing the FORCE terminals which carry excitation current through separate leads. Configure the DMM for four-wire resistance mode with 1 mA test current. The instrument sources current through the FORCE path, measures voltage via the high-impedance SENSE path, and computes resistance as V/I. Record the reading: for a nominal 10 Ω resistor at 23 °C, expect 10.000 Ω ± (0.010% of reading + 0.001 Ω) = ±1.0 mΩ. Repeat the measurement in two-wire mode by shorting FORCE HI to SENSE HI and FORCE LO to SENSE LO—the reading will increase by 0.2 Ω due to lead resistance, demonstrating the necessity of Kelvin connections for precision.

Quantify thermal drift by subjecting the 10 Ω resistor to a controlled temperature ramp. Place the resistor in a temperature-controlled oven or thermal chamber, maintaining four-wire connections via shielded twisted-pair cable with low thermoelectric EMF (copper or gold-plated contacts). Program the chamber to step from 20 °C to 50 °C in 10 °C increments, holding each setpoint for 15 minutes to achieve thermal soak. Measure resistance at each temperature, recording DMM reading and chamber setpoint. Plot resistance versus temperature: the slope yields the experimental tempco in ppm/°C. Compare this against the datasheet specification—Vishay Dale wirewound resistors exhibit 20 ppm/°C, meaning 10 Ω at 20 °C becomes 10.006 Ω at 50 °C (a 6 mΩ increase). If measured tempco deviates by more than 20%, suspect poor thermal coupling between resistor and chamber air, or self-heating from excessive test current.

### Exercise 1.2: Oscilloscope Time-Domain Measurement: Rise Time, Bandwidth, and Probe Loading

Time-domain waveform analysis exposes transient phenomena invisible to DC multimeters: edge speeds, ringing, overshoot, propagation delay, and duty cycle distortion. This exercise calibrates oscilloscope bandwidth against a known-fast signal source, quantifies probe loading effects, and measures edge rates relevant to digital logic families.

Configure the Tektronix MSO4000 oscilloscope for single-ended measurement on Channel 1, AC coupling, 1 MΩ input impedance, 10 mV/div vertical scale, and 10 ns/div timebase. Attach a 10:1 passive probe (Tektronix TPP0500, 500 MHz bandwidth, 10 MΩ || 3.9 pF input impedance) to the oscilloscope's front-panel compensation terminal, which outputs a 1 kHz, 5 V peak-to-peak square wave. Adjust the probe's trimmer capacitor while observing the waveform: correctly compensated, the rising and falling edges appear square with minimal overshoot (<5%) and no leading-edge tilt. Over-compensation manifests as overshoot and ringing (probe capacitance too high), while under-compensation produces rounded edges and reduced amplitude (probe capacitance too low). This compensation procedure nullifies the probe's ~10 pF cable capacitance against the oscilloscope's ~15 pF input capacitance, restoring flat frequency response to 500 MHz.

Probe loading corrupts high-impedance circuits. Demonstrate this by constructing a 10 kHz square wave generator using a 74HC04 hex inverter configured as a ring oscillator. Power the IC from a clean 5 V rail bypassed with 100 nF ceramic and 10 µF tantalum capacitors. Drive a 1 kΩ series resistor from one inverter output, creating a Thevenin source impedance of 1 kΩ. Connect the 10:1 probe to the resistor's far end, observing the waveform amplitude and edge rate. The oscilloscope displays ~4.5 V peak-to-peak with 20 ns rise time. Now replace the 10:1 probe with a 1× passive probe (10 MΩ || 100 pF): amplitude drops to ~3.8 V and rise time degrades to 150 ns due to the RC low-pass filter formed by 1 kΩ source impedance and 100 pF probe capacitance (τ = RC = 150 ns, corner frequency fc = 1/(2πRC) = 1.06 MHz). This demonstrates why high-speed measurements mandate low-capacitance probes or direct 50 Ω coaxial connection.

Rise time measurement quantifies signal bandwidth via the empirical relationship BW ≈ 0.35 / t_r, where t_r is the 10%-to-90% rise time. Generate a fast edge using a precision pulse generator (BNC Model 577, <300 ps rise time) set to 1 MHz repetition rate, 2.5 V amplitude, 50 Ω output impedance. Terminate the generator output into a 50 Ω BNC feedthrough adapter, then connect the oscilloscope via a short (<20 cm) 50 Ω BNC cable, configuring the oscilloscope input for 50 Ω termination to prevent reflections. Enable infinite persistence and zoom the timebase to 500 ps/div. Position cursors at 10% and 90% of the rising edge amplitude: a 300 ps rise time implies ~1.17 GHz bandwidth from the pulse generator. Now measure the same signal through the 500 MHz 10:1 probe—the observed rise time increases to ~700 ps, consistent with the oscilloscope's 100 MHz analog bandwidth (0.35 / 100 MHz = 3.5 ns intrinsic rise time, convolved with the probe's 700 ps contribution).

Bandwidth limitation manifests as high-frequency attenuation. Validate this by sweeping a sine wave from 10 kHz to 500 MHz using the Siglent SDG2042X arbitrary waveform generator, maintaining 1 V RMS amplitude into 50 Ω load. Connect the generator to the oscilloscope via 50 Ω coaxial cable with matched termination. At each frequency decade (10 kHz, 100 kHz, 1 MHz, 10 MHz, 100 MHz, 500 MHz), measure RMS amplitude using the oscilloscope's built-in VRMS measurement function. Plot amplitude versus frequency on semi-log axes: the response remains flat (±3%) from DC to ~80 MHz (the oscilloscope's -3 dB point), then rolls off at -20 dB/decade, reaching -10 dB attenuation at 500 MHz. This first-order low-pass response arises from the oscilloscope's analog front-end anti-aliasing filter and probe compensation network.

### Exercise 1.3: Signal Generator Amplitude and Frequency Accuracy Verification

Signal generators anchor stimulus fidelity in every measurement campaign. This exercise validates generator amplitude flatness, frequency accuracy, harmonic distortion, and output impedance across the DC-to-50 MHz range, cross-referencing oscilloscope and spectrum analyzer readings.

Configure the Siglent SDG2042X for sine wave output at 1 MHz, 1 V RMS amplitude, 50 Ω output impedance. Connect the generator's CH1 output to the oscilloscope's Channel 1 input via a short 50 Ω BNC cable, setting the oscilloscope to 50 Ω termination, AC coupling, 500 mV/div vertical scale, 500 ns/div timebase. Enable the oscilloscope's VRMS measurement: the displayed value should match the generator's amplitude setting within ±(2% of setting + 2 mV). For 1 V RMS, acceptable range is 0.98 V to 1.02 V. If the reading deviates beyond tolerance, suspect incorrect output impedance setting (high-Z versus 50 Ω) or cable mismatch inducing reflections.

Frequency accuracy verification requires a calibrated frequency counter or GPS-disciplined timebase. Modern oscilloscopes integrate frequency counters with gate times up to 1 second, achieving sub-ppm resolution. Enable the oscilloscope's frequency measurement on the 1 MHz sine wave, setting gate time to 1 second for maximum resolution. The reading should display 1.000000 MHz ± 1 ppm (the Siglent SDG2042X specifies ±1 ppm + 1 mHz absolute frequency error). A 1 ppm error at 1 MHz translates to 1 Hz offset—well within the oscilloscope's 1 Hz resolution. Repeat the measurement at 50 MHz: ±1 ppm becomes ±50 Hz, still within the generator's specification. If frequency error exceeds ±5 ppm, the generator's TCXO timebase requires factory recalibration, or the oscilloscope's timebase has drifted from its last calibration cycle.

Harmonic distortion quantifies signal purity, critical for filter testing and ADC characterization. Transfer the 1 MHz sine wave output from oscilloscope to spectrum analyzer (Siglent SSA3032X), connecting via 50 Ω coaxial cable with both generator and analyzer configured for 50 Ω impedance. Set the spectrum analyzer's center frequency to 1 MHz, span to 100 MHz, resolution bandwidth (RBW) to 10 kHz, and video bandwidth (VBW) to 1 kHz for noise averaging. The fundamental at 1 MHz should dominate the display at 0 dBm (assuming 1 V RMS into 50 Ω equals 0 dBm = 10 × log₁₀(1 mW)). Identify the second harmonic at 2 MHz and third harmonic at 3 MHz: a quality generator exhibits <-60 dBc (60 dB below carrier) for all harmonics. Total harmonic distortion (THD) computes as THD = √(H₂² + H₃² + H₄² + ...) where Hₙ is the nth harmonic amplitude relative to fundamental. For -60 dBc on all harmonics, THD ≈ 0.1%.

Output impedance mismatch corrupts amplitude when driving non-50 Ω loads. Demonstrate this by measuring generator output into high-impedance load. Remove the 50 Ω termination from the oscilloscope (set input impedance to 1 MΩ), leaving the generator configured for 50 Ω output impedance. The oscilloscope now displays 2 V RMS—double the expected amplitude—because the generator's internal 50 Ω series resistor forms a voltage divider with the oscilloscope's 1 MΩ input. When properly terminated into 50 Ω, the divider ratio is 50 Ω / (50 Ω + 50 Ω) = 0.5, halving the open-circuit voltage. With 1 MΩ load, the ratio approaches unity (1 MΩ / (50 Ω + 1 MΩ) ≈ 0.99995), so the full open-circuit voltage appears at the load. This explains why RF and high-speed digital measurements mandate 50 Ω termination: impedance matching maximizes power transfer and eliminates reflections on transmission lines longer than λ/10.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise 2.1: RC Low-Pass Filter Frequency Response Characterization via Swept Sine and FFT

Frequency-domain analysis decomposes complex waveforms into sinusoidal components, exposing resonances, filter cutoff frequencies, and parasitic inductance. This exercise constructs a first-order RC low-pass filter, measures its frequency response using swept-sine and FFT techniques, and compares empirical results against theoretical transfer function predictions.

Construct the filter on a solderless breadboard using a 1 kΩ resistor (1% metal film, 0805 footprint soldered to a small PCB fragment if using coaxial probing) and a 100 nF capacitor (C0G/NP0 ceramic, ±5% tolerance, 0805 package). Calculate the theoretical corner frequency: fc = 1 / (2πRC) = 1 / (2π × 1 kΩ × 100 nF) = 1.59 kHz. At this frequency, the filter's gain rolls off to -3 dB (70.7% of DC amplitude), and phase shifts by -45°. Above fc, gain decreases at -20 dB/decade (-6 dB/octave) asymptotically, while phase approaches -90°.

Connect the signal generator's CH1 output to the resistor input via a short coaxial cable terminated in 50 Ω at the generator. Ground the resistor's input-side terminal to the breadboard's ground plane (a continuous copper pour or wire grid). Connect the capacitor between the resistor's output terminal and ground, forming the classic voltage-divider topology: input → R → output → C → ground. Probe the filter's output using a 10:1 oscilloscope probe, minimizing ground lead length (<2 cm) by using the probe's barrel ground spring rather than the standard alligator clip—long ground leads introduce inductive reactance (L ~ 1 nH/mm) that adds parasitic resonances above 10 MHz.

Execute a swept-sine frequency response measurement. Program the generator for sine wave output sweeping logarithmically from 100 Hz to 100 kHz over 10 seconds, maintaining 1 V RMS amplitude. Configure the oscilloscope to capture both input (generator output) and output (capacitor voltage) simultaneously on separate channels, using AC coupling and 200 mV/div vertical scale. Trigger on the input channel, setting trigger level to 50% of amplitude and enabling normal trigger mode. Capture a single sweep and transfer the waveform to a computer via Ethernet using PyVISA:

```python
import pyvisa
import numpy as np
import matplotlib.pyplot as plt

rm = pyvisa.ResourceManager()
scope = rm.open_resource('TCPIP0::192.168.1.10::INST0::INSTR')  # Oscilloscope IP
scope.timeout = 10000  # 10-second timeout for waveform transfer

# Configure oscilloscope for dual-channel capture
scope.write('DATa:SOUrce CH1')
scope.write('DATa:ENCdg RIBinary')
scope.write('DATa:WIDth 2')  # 16-bit data
scope.write('DATa:STARt 1')
scope.write('DATa:STOP 10000')  # 10k samples

# Retrieve input waveform (CH1)
scope.write('DATa:SOUrce CH1')
raw_input = scope.query_binary_values('CURVe?', datatype='h', is_big_endian=False)
ymult_in = float(scope.query('WFMOutpre:YMUlt?'))
yoff_in = float(scope.query('WFMOutpre:YOFf?'))
yzero_in = float(scope.query('WFMOutpre:YZEro?'))
v_input = (np.array(raw_input) - yoff_in) * ymult_in + yzero_in

# Retrieve output waveform (CH2)
scope.write('DATa:SOUrce CH2')
raw_output = scope.query_binary_values('CURVe?', datatype='h', is_big_endian=False)
ymult_out = float(scope.query('WFMOutpre:YMUlt?'))
yoff_out = float(scope.query('WFMOutpre:YOFf?'))
yzero_out = float(scope.query('WFMOutpre:YZEro?'))
v_output = (np.array(raw_output) - yoff_out) * ymult_out + yzero_out

# Compute gain (dB) at each frequency
xincr = float(scope.query('WFMOutpre:XINcr?'))
sample_rate = 1 / xincr
time = np.arange(len(v_input)) * xincr

# For swept sine, extract instantaneous frequency and gain
# Simplified: assume fixed frequency points, measure RMS over windows
frequencies = np.logspace(2, 5, 50)  # 100 Hz to 100 kHz, 50 points
gain_db = []

for f in frequencies:
    period = 1 / f
    window_size = int(10 * period * sample_rate)  # 10 cycles
    if window_size > len(v_input):
        continue
    
    rms_in = np.sqrt(np.mean(v_input[:window_size]**2))
    rms_out = np.sqrt(np.mean(v_output[:window_size]**2))
    gain = 20 * np.log10(rms_out / rms_in)
    gain_db.append(gain)

# Plot frequency response
plt.figure(figsize=(10, 6))
plt.semilogx(frequencies[:len(gain_db)], gain_db, 'bo-', label='Measured')

# Theoretical transfer function: H(f) = 1 / sqrt(1 + (f/fc)^2)
fc_theory = 1 / (2 * np.pi * 1e3 * 100e-9)  # 1.59 kHz
gain_theory = -10 * np.log10(1 + (frequencies / fc_theory)**2)
plt.semilogx(frequencies, gain_theory, 'r--', label='Theory (fc=1.59 kHz)')

plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain (dB)')
plt.title('RC Low-Pass Filter Frequency Response')
plt.grid(True, which='both', alpha=0.3)
plt.legend()
plt.axhline(-3, color='k', linestyle=':', label='-3 dB point')
plt.savefig('rc_lowpass_bode.png', dpi=300)
plt.show()
```

The measured response should align with theory within ±1 dB from 100 Hz to 10 kHz. Deviations above 10 kHz indicate parasitic effects: breadboard capacitance (~5 pF per contact point) parallels the 100 nF capacitor, shifting fc upward by ~0.1%. Inductive probe ground leads resonate with the capacitor at f_resonance = 1 / (2π√(LC)) ≈ 20 MHz for L = 10 nH, C = 100 nF, introducing a peaking artifact. Mitigate this by transitioning to a professionally fabricated PCB with coplanar ground pour and SMA connectors for frequencies above 1 MHz.

FFT-based frequency analysis offers an alternative to swept-sine measurements. Apply a wideband stimulus—a square wave or noise burst—and compute the DFT (Discrete Fourier Transform) of input and output waveforms. The transfer function H(f) equals DFT(output) / DFT(input), capturing all frequency components simultaneously. Generate a 10 kHz square wave at 1 V amplitude from the signal generator, applying it to the RC filter input. Capture 10,000 samples at 1 MSa/s on both channels, export the waveforms, and process with NumPy:

```python
import numpy as np
import matplotlib.pyplot as plt

# Assume v_input and v_output arrays already loaded from oscilloscope
sample_rate = 1e6  # 1 MSa/s
N = len(v_input)
freq = np.fft.rfftfreq(N, d=1/sample_rate)

# Compute FFT
fft_input = np.fft.rfft(v_input)
fft_output = np.fft.rfft(v_output)

# Transfer function H(f) = FFT(output) / FFT(input)
H = fft_output / (fft_input + 1e-12)  # Avoid division by zero
gain_fft = 20 * np.log10(np.abs(H))
phase_fft = np.angle(H, deg=True)

# Plot Bode magnitude and phase
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

ax1.semilogx(freq[1:1000], gain_fft[1:1000], 'b-', label='FFT Magnitude')
ax1.set_ylabel('Gain (dB)')
ax1.set_title('RC Filter Bode Plot (FFT Method)')
ax1.grid(True, which='both', alpha=0.3)
ax1.axhline(-3, color='r', linestyle='--', label='-3 dB')
ax1.legend()

ax2.semilogx(freq[1:1000], phase_fft[1:1000], 'g-', label='FFT Phase')
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Phase (degrees)')
ax2.axhline(-45, color='r', linestyle='--', label='-45° at fc')
ax2.grid(True, which='both', alpha=0.3)
ax2.legend()

plt.tight_layout()
plt.savefig('rc_filter_fft_bode.png', dpi=300)
plt.show()
```

FFT analysis reveals harmonic content and aliasing artifacts. The 10 kHz square wave contains odd harmonics at 30 kHz, 50 kHz, 70 kHz, etc., with amplitudes decreasing as 1/n (fundamental has 4/π amplitude, third harmonic 4/(3π), fifth harmonic 4/(5π)). The RC filter attenuates these harmonics: at 30 kHz (18.9× fc), gain drops to -20 × log₁₀(18.9) ≈ -25 dB, and the output waveform appears sinusoidal rather than square. Quantify harmonic distortion by measuring the ratio of third harmonic amplitude to fundamental: THD = √(H₃² + H₅² + H₇²...) / H₁. For an ideal first-order low-pass, THD decreases as corner frequency decreases relative to input frequency.

### Exercise 2.2: Smith Chart Impedance Matching and S-Parameter Measurement with VNA

Radio frequency and high-speed digital circuits demand impedance matching to maximize power transfer and minimize reflections on transmission lines. This exercise employs a vector network analyzer (VNA) to measure S-parameters (scattering parameters) of passive components, plots results on a Smith chart, and designs a lumped-element matching network to transform a mismatched load into 50 Ω.

Begin by calibrating the NanoVNA-H4 vector network analyzer. Connect the VNA's Port 1 to a mechanical calibration kit (SMA male open, short, and 50 Ω load standards). Power the VNA and navigate to the calibration menu. Execute a one-port SOL (Short-Open-Load) calibration sequence:

1. **Short standard**: Connect the short circuit standard to Port 1. On the VNA display, select "Short" calibration step. The VNA measures S₁₁ (reflection coefficient), which should approach -1 ∠180° (magnitude 1, phase 180°) since a short reflects all incident power with 180° phase inversion.

2. **Open standard**: Replace the short with the open circuit standard. Select "Open" calibration. S₁₁ should approach +1 ∠0° (magnitude 1, phase 0°), reflecting all power without inversion.

3. **Load standard**: Connect the precision 50 Ω load. Select "Load" calibration. S₁₁ should approach 0 ∠arbitrary (magnitude near 0 dB), indicating perfect absorption with no reflection.

After calibration, the VNA stores correction coefficients compensating for systematic errors (directivity, source match, frequency response). These coefficients remain valid for hours if connectors remain undisturbed and temperature stable.

Measure the S₁₁ of an unknown inductor—a 100 nH chip inductor (0805 package, ±10% tolerance, Q > 20 at 100 MHz). Solder the inductor between the center conductor and ground shell of an SMA edge-launch connector, bonding ground leads with <5 mm trace length to minimize parasitic inductance. Connect the SMA fixture to VNA Port 1. Configure the VNA frequency span from 10 MHz to 1 GHz with 201 measurement points. Display S₁₁ in Smith chart format: the trace spirals clockwise from the right side of the chart (low frequency, inductive reactance Z ≈ jωL) toward the top (high frequency, increasing reactance). At 100 MHz, the inductor's impedance is Z_L = j2πfL = j(2π × 100 MHz × 100 nH) = j62.8 Ω. On the Smith chart, this corresponds to a point on the constant-resistance circle (r = 0) with normalized reactance x = 62.8 / 50 = 1.26. Mark this point and extract the S₁₁ magnitude and phase: |S₁₁| ≈ 0.78 (-2.2 dB), ∠S₁₁ ≈ +55°.

Reflection coefficient S₁₁ relates to impedance via the transformation S₁₁ = (Z - Z₀) / (Z + Z₀), where Z₀ = 50 Ω is the reference impedance. Invert this to recover impedance: Z = Z₀(1 + S₁₁) / (1 - S₁₁). For the measured S₁₁ = 0.78 ∠55°, compute:

```python
import numpy as np

S11_mag = 0.78
S11_phase = 55  # degrees
S11 = S11_mag * np.exp(1j * np.deg2rad(S11_phase))

Z0 = 50
Z = Z0 * (1 + S11) / (1 - S11)
print(f"Impedance: {Z.real:.2f} + j{Z.imag:.2f} Ω")
```

Output: `Impedance: 6.24 + j62.31 Ω`, confirming the inductive reactance with small series resistance from conductor loss.

Design a matching network to transform the inductive load into 50 Ω at 100 MHz. The simplest topology is an L-match comprising a series capacitor and shunt inductor. Calculate component values analytically: given source impedance Z_S = 50 Ω and load impedance Z_L = 6.24 + j62.31 Ω, synthesize a two-element network such that input impedance looking into the network equals 50 Ω.

Using Smith chart graphical method: plot Z_L = 6.24 + j62.31 Ω on the chart (normalize to 50 Ω: z_L = 0.125 + j1.246). Rotate clockwise along a constant-resistance circle (add series reactance) until intersecting the r = 1 circle (50 Ω real part). This requires adding series capacitive reactance X_C = -51.3 Ω. Next, rotate toward the chart center along a constant-conductance circle (add shunt susceptance) until reaching the chart center (z = 1 + j0). This requires shunt inductive susceptance B_L. Calculate component values:

```python
import numpy as np

f = 100e6  # 100 MHz
XC = -51.3  # Series capacitive reactance
C_series = -1 / (2 * np.pi * f * XC)
print(f"Series capacitor: {C_series * 1e12:.2f} pF")

# After adding series C, impedance becomes Z' = 6.24 + j(62.31 - 51.3) = 6.24 + j11.01
# Shunt inductor to resonate with j11.01 and achieve 50 Ω input
# Detailed calculation involves parallel combination; simplified:
L_shunt = 50 / (2 * np.pi * f * 1.5)  # Approximate
print(f"Shunt inductor: {L_shunt * 1e9:.2f} nH")
```

Output: `Series capacitor: 31.05 pF`, `Shunt inductor: 53.05 nH`. Construct the network on a PCB using 0805 chip components (33 pF capacitor, 56 nH inductor), measure S₁₁ again—the matched network should exhibit S₁₁ < -20 dB (VSWR < 1.2:1) at 100 MHz, confirming impedance transformation.

Two-port S-parameter measurement characterizes transmission loss and isolation. Configure the VNA for two-port calibration (SOLT: Short-Open-Load-Through) by connecting calibration standards sequentially to Port 1 and Port 2, then connecting a through adapter between ports. After calibration, measure a 10 dB attenuator pad (π-network resistive attenuator, 50 Ω input/output impedance). Connect Port 1 to the attenuator input, Port 2 to the output. Display S₂₁ (forward transmission): magnitude should read -10 dB ±0.5 dB across the full frequency span (DC to 1 GHz for a broadband attenuator). S₁₁ and S₂₂ (input and output reflection coefficients) should remain below -20 dB, confirming 50 Ω impedance match. S₁₂ (reverse transmission) equals S₂₁ for a reciprocal passive network, distinguishing it from non-reciprocal devices like isolators and circulators.

### Exercise 2.3: Spectrum Analyzer Spurious Emission and Phase Noise Measurement

Spectrum analyzers resolve frequency-domain signals invisible to oscilloscopes: discrete spurs from clock harmonics, phase noise sidebands surrounding carriers, and intermodulation products from nonlinear mixing. This exercise quantifies spurious-free dynamic range (SFDR), measures phase noise spectral density, and identifies EMI sources radiating from a switching power supply.

Configure the Siglent SSA3032X spectrum analyzer for a baseline spurious measurement. Set center frequency to 100 MHz, span to 200 MHz (capturing 0 to 200 MHz), resolution bandwidth (RBW) to 10 kHz, video bandwidth (VBW) to 1 kHz, and input attenuation to 10 dB to protect the mixer from overload. Connect the signal generator output (Siglent SDG2042X) set to 100 MHz, -10 dBm amplitude, 50 Ω output. The spectrum analyzer displays a sharp peak at 100 MHz with amplitude near -10 dBm (correcting for cable loss and attenuation). Zoom the span to ±10 MHz around the carrier (center 100 MHz, span 20 MHz) and reduce RBW to 1 kHz for higher frequency resolution. The displayed noise floor should drop to approximately -100 dBm/Hz, limited by the analyzer's inherent phase noise and thermal noise.

Measure phase noise by analyzing the power spectral density of frequency fluctuations surrounding the carrier. Phase noise, denoted ℒ(f), quantifies single-sideband noise power density at offset frequency f from the carrier, normalized to carrier power: ℒ(f) = 10 log₁₀(P_noise(f) / P_carrier) in dBc/Hz. At the spectrum analyzer, enable the phase noise measurement mode (if available) or manually extract sideband power. Position a marker 10 kHz offset from the 100 MHz carrier, note the amplitude (e.g., -85 dBm), then compute noise power density by dividing by RBW: P_noise_density = -85 dBm - 10 log₁₀(1 kHz) = -85 dBm - 30 dB = -115 dBm/Hz. With carrier at -10 dBm, phase noise is ℒ(10 kHz) = -115 dBm/Hz - (-10 dBm) = -105 dBc/Hz. High-quality signal generators exhibit ℒ(10 kHz) < -120 dBc/Hz; the measured value includes the spectrum analyzer's own phase noise floor.

Separate device-under-test (DUT) phase noise from analyzer phase noise using the cross-correlation method: measure the same signal with two independent spectrum analyzers and correlate their results, or use a low-noise external reference oscillator. For this lab, accept the combined phase noise as an upper bound.

Spurious emission identification exposes unintended frequency components. Construct a simple switching regulator circuit using a TI LM2596 buck converter IC, converting 12 V input to 5 V output at 500 mA load current. The LM2596 operates at 150 kHz switching frequency. Connect the regulator output to a 10 Ω load resistor, bypassing with 100 µF electrolytic and 10 µF ceramic capacitors. Place a near-field H-field probe (a small loop of coaxial cable with shield broken, forming a 5 mm diameter loop) close to the inductor, connecting the probe's coaxial output to the spectrum analyzer input. Set span to 0 to 30 MHz, RBW 10 kHz. The spectrum displays the 150 kHz fundamental switching frequency and harmonics at 300 kHz, 450 kHz, 600 kHz, etc., extending to the tenth harmonic at 1.5 MHz. Amplitude decreases with harmonic number due to the inductor's low-pass filtering, but insufficient input capacitor bypassing allows high-frequency ripple to couple onto the input rail, radiating from PCB traces acting as unintentional antennas.

Quantify spurious-free dynamic range (SFDR): the ratio of carrier power to the largest spurious signal. If the fundamental at 150 kHz reads -20 dBm and the strongest harmonic (third harmonic, 450 kHz) measures -60 dBm, SFDR = -20 dBm - (-60 dBm) = 40 dB. EMI regulations (e.g., FCC Part 15, CISPR 22) specify maximum radiated emission levels as a function of frequency; for example, <40 dBµV/m at 3 meters for frequencies above 30 MHz. Convert the conducted emission (measured at the probe) to radiated field strength using antenna factor tables and near-field-to-far-field transformations—beyond the scope of this lab, but the spectrum analyzer's amplitude directly informs filter design decisions.

Mitigate spurious emissions by adding LC filters. Insert a ferrite bead (Murata BLM18AG series, 100 Ω at 100 MHz) in series with the regulator input, and parallel the existing capacitors with additional 1 µF and 100 nF ceramics placed within 5 mm of the IC's power pins. Repeat the spectrum analyzer scan: harmonic amplitudes should decrease by 10–20 dB, shifting the noise floor downward. This empirical approach—measure, modify, re-measure—forms the core of EMC (electromagnetic compatibility) debugging.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Exercise 3.1: Temperature-Dependent Oscillator Frequency Drift and Allan Deviation

Oscillator stability underpins all time- and frequency-dependent measurements. Temperature fluctuations shift crystal resonance frequency via thermoelastic coupling, aging degrades resonator Q-factor, and power supply ripple modulates output frequency. This exercise characterizes a crystal oscillator's temperature coefficient, measures short-term frequency stability via Allan deviation, and validates oven-controlled oscillator (OCXO) performance.

Select a 10 MHz crystal oscillator module—start with a simple TCXO (temperature-compensated crystal oscillator) such as the Abracon ASTX-H11. Power the oscillator from a low-noise 3.3 V linear regulator (LDO) with <10 µVrms output noise. Connect the oscillator's sine wave or CMOS logic output to the frequency counter input of the oscilloscope or a dedicated frequency counter (HP 53131A, Keysight 53230A). Configure the counter for 10 MHz input, 1-second gate time, and continuous measurement mode, logging frequency readings to a CSV file via SCPI automation:

```python
import pyvisa
import time
import csv

rm = pyvisa.ResourceManager()
counter = rm.open_resource('TCPIP0::192.168.1.20::INST0::INSTR')  # Frequency counter IP

counter.write('CONF:FREQ (@1)')  # Configure channel 1 for frequency measurement
counter.write('FREQ:ARM:STAR:SOUR IMM')  # Immediate trigger
counter.write('FREQ:ARM:STOP:SOUR TIM')
counter.write('FREQ:ARM:STOP:TIM 1')  # 1-second gate time

# Collect 1000 samples over ~1000 seconds
frequencies = []
with open('oscillator_stability.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp', 'Frequency_Hz'])
    
    for i in range(1000):
        freq = float(counter.query('READ?'))
        timestamp = time.time()
        frequencies.append(freq)
        writer.writerow([timestamp, freq])
        print(f"Sample {i+1}: {freq:.6f} Hz")
        time.sleep(1)
```

Place the oscillator module inside a temperature chamber programmed for a 20 °C to 60 °C ramp at 2 °C/minute. Maintain continuous frequency logging throughout the ramp. Plot frequency versus chamber setpoint temperature: the TCXO exhibits a cubic temperature characteristic f(T) = f₀ + α(T - T₀) + β(T - T₀)² + γ(T - T₀)³, where f₀ is the nominal frequency at turnover temperature T₀ (typically 25 °C), and α, β, γ are temperature coefficients. For a ±0.5 ppm TCXO, maximum frequency excursion over -40 °C to +85 °C remains within ±5 Hz at 10 MHz (10 MHz × 0.5 ppm = 5 Hz). Fit the measured data to a polynomial and extract coefficients:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Load data from CSV
data = np.loadtxt('oscillator_stability.csv', delimiter=',', skiprows=1)
temperature = np.linspace(20, 60, len(data))  # Assume linear ramp
frequency = data[:, 1]

# Cubic fit
def cubic_model(T, f0, alpha, beta, gamma, T0):
    return f0 + alpha*(T - T0) + beta*(T - T0)**2 + gamma*(T - T0)**3

popt, _ = curve_fit(cubic_model, temperature, frequency, p0=[10e6, 0, 0, 0, 25])
f0, alpha, beta, gamma, T0 = popt

print(f"Turnover temperature T0: {T0:.2f} °C")
print(f"Frequency at T0: {f0:.6f} Hz")
print(f"Linear coefficient α: {alpha:.6e} Hz/°C")
print(f"Quadratic coefficient β: {beta:.6e} Hz/°C²")

# Plot measured vs. fitted
plt.figure(figsize=(10, 6))
plt.plot(temperature, frequency, 'b.', label='Measured')
plt.plot(temperature, cubic_model(temperature, *popt), 'r-', label='Cubic Fit')
plt.xlabel('Temperature (°C)')
plt.ylabel('Frequency (Hz)')
plt.title('TCXO Frequency vs. Temperature')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('tcxo_temp_stability.png', dpi=300)
plt.show()
```

Short-term stability assessment via Allan deviation quantifies frequency fluctuations over various averaging intervals, distinguishing white phase noise, flicker phase noise, and random walk frequency noise. Allan deviation σ_y(τ) computes as the square root of half the average squared difference between adjacent frequency measurements averaged over interval τ:

σ_y(τ) = √( (1 / (2(M-1))) Σ[i=1 to M-1] (y_i+1 - y_i)² )

where y_i = (f_i - f_nominal) / f_nominal is the fractional frequency deviation. Implement Allan deviation calculation:

```python
import numpy as np
import matplotlib.pyplot as plt

# Frequency data already loaded
f_nominal = 10e6
y = (frequency - f_nominal) / f_nominal  # Fractional frequency

# Compute Allan deviation for tau = 1, 2, 4, 8, ... seconds
tau_values = [1, 2, 4, 8, 16, 32, 64, 128]
allan_dev = []

for tau in tau_values:
    # Resample data at interval tau
    n_samples = len(y) // tau
    y_resampled = [np.mean(y[i*tau:(i+1)*tau]) for i in range(n_samples)]
    
    # Compute Allan deviation
    if len(y_resampled) < 2:
        continue
    diffs = np.diff(y_resampled)
    sigma = np.sqrt(0.5 * np.mean(diffs**2))
    allan_dev.append(sigma)

# Plot log-log
plt.figure(figsize=(10, 6))
plt.loglog(tau_values[:len(allan_dev)], allan_dev, 'bo-')
plt.xlabel('Averaging Time τ (seconds)')
plt.ylabel('Allan Deviation σ_y(τ)')
plt.title('TCXO Allan Deviation')
plt.grid(True, which='both', alpha=0.3)
plt.savefig('tcxo_allan_deviation.png', dpi=300)
plt.show()
```

For a TCXO, Allan deviation typically reaches a minimum (flicker floor) at τ ~ 1–10 seconds, then increases at longer averaging times due to temperature drift and aging. A GPS-disciplined oscillator (GPSDO) or rubidium frequency standard achieves σ_y(1s) < 1×10⁻¹¹, two orders of magnitude better than a TCXO.

Compare the TCXO against an OCXO (oven-controlled crystal oscillator, e.g., Bliley NV47C). OCXOs maintain the crystal resonator at a thermally stable setpoint (typically 80 °C) using a proportional-integral-derivative (PID) heater controller, reducing temperature-induced drift to <±0.01 ppm over 0 °C to 70 °C ambient range. Repeat the frequency logging procedure while subjecting the OCXO to the same thermal ramp. The OCXO's frequency remains flat within ±0.1 Hz (±0.01 ppm at 10 MHz), demonstrating superior stability. However, OCXOs consume 1–3 watts continuous power for oven heating, versus milliwatts for TCXOs, trading power for performance.

### Exercise 3.2: Power Supply Rejection Ratio (PSRR) and Load Transient Response

Analog circuits demand clean, stable DC power rails. Voltage regulators attenuate input ripple and reject rapid load current changes, characterized by power supply rejection ratio (PSRR) and transient response time. This exercise measures PSRR across frequency, probes load transient overshoot, and evaluates output capacitor ESR effects.

Construct a linear low-dropout (LDO) regulator test circuit using a Texas Instruments TPS7A4700 adjustable LDO, configured for 3.3 V output from a 5 V input. Bypass the input with 10 µF ceramic and 100 µF electrolytic capacitors, and the output with 22 µF ceramic (X7R dielectric, 0.01 Ω ESR) placed within 10 mm of the LDO's output pin. Connect a 10 Ω power resistor as a 330 mA load (3.3 V / 10 Ω).

Measure DC output voltage using the 6½-digit multimeter in four-wire mode, connecting sense leads directly to the load resistor terminals. Record output voltage: should read 3.300 V ±(0.5% + 5 mV) = 3.283 V to 3.317 V per datasheet line regulation specification. Apply input voltage variation: adjust the bench supply from 4.5 V to 5.5 V in 100 mV steps, measuring output voltage at each step. Calculate line regulation as ΔV_out / ΔV_in: for a 1 V input change, output should vary <10 mV, yielding line regulation <10 mV/V = 0.01 = 1%. The LDO's internal feedback loop maintains constant output by modulating pass transistor gate voltage in response to input changes.

PSRR quantifies AC ripple rejection. Inject a small-amplitude sine wave ripple onto the DC input voltage using the signal generator's modulation feature or a bias tee. Configure the generator for 5 V DC offset, 100 mV RMS sine wave at variable frequency (100 Hz to 100 kHz). Connect the generator output to the LDO input via a bias tee (Mini-Circuits ZFBT-4R2GW+), allowing DC and AC signals to combine. Measure input ripple amplitude using an oscilloscope AC-coupled probe on the LDO input pin, and output ripple on the LDO output pin. At 1 kHz, input ripple = 100 mV RMS, output ripple = 500 µV RMS. PSRR = 20 log₁₀(V_ripple_in / V_ripple_out) = 20 log₁₀(100 mV / 0.5 mV) = 46 dB. Sweep frequency from 100 Hz to 100 kHz, plotting PSRR versus frequency:

```python
import numpy as np
import matplotlib.pyplot as plt

# Example measured data (frequency in Hz, PSRR in dB)
frequency = np.array([100, 200, 500, 1e3, 2e3, 5e3, 10e3, 20e3, 50e3, 100e3])
psrr_db = np.array([70, 68, 65, 60, 55, 48, 40, 32, 24, 18])

plt.figure(figsize=(10, 6))
plt.semilogx(frequency, psrr_db, 'bo-')
plt.xlabel('Frequency (Hz)')
plt.ylabel('PSRR (dB)')
plt.title('LDO Power Supply Rejection Ratio')
plt.grid(True, which='both', alpha=0.3)
plt.axhline(40, color='r', linestyle='--', label='40 dB typical @ 10 kHz')
plt.legend()
plt.savefig('ldo_psrr.png', dpi=300)
plt.show()
```

PSRR degrades at high frequency due to finite control loop bandwidth and output capacitor impedance. The LDO's feedback loop bandwidth (~100 kHz for the TPS7A4700) limits PSRR beyond this frequency; above the loop crossover, PSRR drops at -20 dB/decade. Output capacitor ESR creates a zero in the control-to-output transfer function, improving high-frequency PSRR, but excessive ESR increases output impedance.

Load transient response tests the regulator's ability to maintain output voltage during rapid load current changes. Replace the static 10 Ω load with an electronic load (BK Precision 8600 series) configured for dynamic mode: 100 mA baseline current, 500 mA pulse current, 10 µs rise/fall time, 1 kHz repetition rate. Connect a 1:1 oscilloscope probe (or coaxial probe) to the LDO output capacitor, minimizing ground lead inductance by using the probe's ground spring. Trigger the oscilloscope on the load current step (monitor the electronic load's trigger output). Capture the output voltage transient: when load current steps from 100 mA to 500 mA, output voltage dips (undershoot) then recovers. Measure undershoot amplitude and recovery time (time from 10% to 90% of final value).

Typical undershoot = output capacitor ESR × ΔI_load + (ΔI_load / C_out) × t_recovery. For C_out = 22 µF, ESR = 0.01 Ω, ΔI_load = 400 mA, t_recovery = 10 µs, predicted undershoot = (0.01 Ω × 0.4 A) + (0.4 A / 22 µF × 10 µs) = 4 mV + 182 mV = 186 mV. Measure the actual undershoot: if it exceeds 200 mV, insufficient output capacitance or excessive ESR is the cause. Parallel an additional 22 µF ceramic capacitor and repeat—undershoot should halve, confirming the capacitor's role in supplying transient current while the LDO's feedback loop responds.

Evaluate output impedance versus frequency by injecting a small AC current and measuring the resulting voltage ripple. Replace the load resistor with a current source (or use the electronic load in AC mode if available). Inject 10 mA RMS sine wave at frequencies from 100 Hz to 1 MHz, measuring output voltage ripple. Output impedance Z_out(f) = V_ripple / I_ripple. At low frequency (<1 kHz), Z_out ≈ LDO's output impedance specification (~10 mΩ). At high frequency (>100 kHz), Z_out increases due to capacitor ESR and parasitic inductance: Z_out(f) = ESR + jωL_parasitic. For a 22 µF ceramic with 10 nH lead inductance, Z_out(1 MHz) = √(ESR² + (2π × 1 MHz × 10 nH)²) ≈ 63 mΩ (dominated by inductance).

### Exercise 3.3: Thermal Shutdown and Overcurrent Protection Verification

Power management ICs integrate protection features—thermal shutdown, current limiting, short-circuit protection—to prevent catastrophic failure. This exercise deliberately triggers these protection mechanisms, verifies safe operation, and measures recovery time.

Configure the same TPS7A4700 LDO circuit from Exercise 3.2, monitoring output voltage, input current, and junction temperature. Attach a thermocouple (K-type, 0.5 mm bead diameter) to the LDO's exposed thermal pad using thermally conductive epoxy (Arctic Silver 5) or Kapton tape, connecting the thermocouple to a digital thermometer (Fluke 54-II). Record ambient temperature T_ambient = 23 °C. Apply 5 V input, 10 Ω load (330 mA output current). Measure steady-state junction temperature T_junction ≈ T_ambient + (I_out × V_dropout × θ_JA), where V_dropout = V_in - V_out = 1.7 V, θ_JA = junction-to-ambient thermal resistance (~40 °C/W for the LDO in a standard PCB layout). P_dissipated = 0.33 A × 1.7 V = 0.56 W, ΔT = 0.56 W × 40 °C/W = 22.4 °C, T_junction ≈ 45 °C. The thermocouple reads ~43 °C (slightly lower due to thermal resistance between junction and package surface).

Trigger thermal shutdown by increasing input voltage to 12 V while maintaining the 10 Ω load. Power dissipation jumps to P = 0.33 A × (12 V - 3.3 V) = 2.87 W, ΔT = 2.87 W × 40 °C/W = 115 °C, T_junction ≈ 138 °C. The TPS7A4700 datasheet specifies thermal shutdown threshold T_SD = 160 °C typical. As junction temperature approaches this limit, the LDO disables its pass transistor, output voltage collapses to 0 V, and input current drops to quiescent current (~5 mA). Monitor the oscilloscope trace capturing output voltage during shutdown: voltage ramps down over ~10 ms (set by output capacitor discharge through the load). Once the junction cools to T_SD - hysteresis (~140 °C), the LDO re-enables, output voltage recovers, and the cycle repeats—a thermal oscillation signature indicating inadequate heatsinking.

Mitigate thermal shutdown by adding a heatsink. Attach an aluminum finned heatsink (thermal resistance θ_SA ~ 10 °C/W) to the LDO package using thermal interface material (TIM, thermal conductivity >2 W/m·K). Recalculate junction temperature: θ_JA_new = θ_JC + θ_CA, where θ_JC (junction-to-case) = 5 °C/W, θ_CA (case-to-ambient via heatsink) = 10 °C/W, total θ_JA = 15 °C/W. At 2.87 W dissipation, ΔT = 43 °C, T_junction = 66 °C—well below shutdown threshold. Confirm stable operation by running the circuit for 10 minutes, monitoring temperature every 30 seconds. Temperature should stabilize at 65–70 °C.

Overcurrent protection limits output current to prevent pass transistor destruction. Short the LDO output to ground using a low-inductance path (twisted pair wire, <10 cm length). Observe output voltage on oscilloscope (DC-coupled, 1 V/div, 10 ms/div): voltage remains near zero while current-limit circuit clamps output current to I_limit = 1.5 A typical. Measure input current during short circuit: I_in = I_limit + I_quiescent ≈ 1.5 A. The LDO operates in constant-current mode, with junction temperature rising rapidly. After ~100 ms, thermal shutdown activates (faster due to high power dissipation), output disables, then re-enables after cooling—creating a hiccup-mode current limit cycle.

Remove the short circuit. Output voltage should recover within 100 µs (determined by output capacitor recharge time: t = C × ΔV / I, where C = 22 µF, ΔV = 3.3 V, I = 1.5 A, t = 48 µs). Measure actual recovery time: if exceeding 1 ms, suspect soft-start circuitry limiting inrush current during startup.

Verify fold-back current limiting (if implemented). Some LDOs reduce current limit threshold as output voltage drops, preventing thermal runaway during sustained overload. Plot I_limit versus V_out by incrementally decreasing load resistance from 10 Ω to 1 Ω, measuring output voltage and current at each step:

```python
import numpy as np
import matplotlib.pyplot as plt

# Measured load resistance, output voltage, output current
R_load = np.array([10, 5, 3, 2, 1.5, 1])
V_out = np.array([3.3, 3.3, 3.2, 2.8, 2.0, 0.5])
I_out = V_out / R_load

plt.figure(figsize=(10, 6))
plt.plot(V_out, I_out * 1000, 'bo-')
plt.xlabel('Output Voltage (V)')
plt.ylabel('Output Current (mA)')
plt.title('LDO Current Limit Characteristic')
plt.grid(True, alpha=0.3)
plt.axhline(1500, color='r', linestyle='--', label='1.5 A constant limit')
plt.legend()
plt.savefig('ldo_current_limit.png', dpi=300)
plt.show()
```

If the curve folds back (current decreases as voltage drops below a threshold), fold-back limiting is active. This protects the LDO but may prevent startup into capacitive loads; external current-boost circuits or soft-start resistors resolve this.

---

## Operational Reference Guide & Diagnostic Checklist

### Measurement Best Practices and Common Pitfalls

**Probe Compensation and Bandwidth Verification**: Uncalibrated probes introduce 10–20% amplitude error and bandwidth-dependent phase distortion. Compensate all passive probes before every measurement session against the oscilloscope's 1 kHz square wave calibration output. Verify probe bandwidth by measuring a known-fast edge (pulse generator with <500 ps rise time) and calculating BW = 0.35 / t_r. Deviations exceeding ±10% indicate probe damage or cable capacitance mismatch.

**Ground Loop Minimization**: Inductive ground leads inject noise and resonances above 10 MHz. Replace standard alligator ground clips with probe ground springs (effective length <10 mm) or coaxial barrel grounds. For RF measurements above 100 MHz, transition to coaxial connectivity with SMA launchers and eliminate all flying leads. Quantify ground loop inductance by measuring a fast edge with progressively longer ground leads: each additional 25 mm adds ~25 nH, introducing ringing at f = 1 / (2π√(LC)) where C is probe capacitance.

**Impedance Matching and Termination**: Transmission line theory governs all signals with rise times faster than 2× propagation delay. For PCB traces longer than t_r × v_propagation / 2 (approximately 3 cm for 1 ns rise time on FR4), source and load impedance must match the transmission line's characteristic impedance Z0 (typically 50 Ω for coaxial cables, 50–100 Ω for PCB microstrip). Verify 50 Ω termination by measuring input impedance with a VNA: |S₁₁| should remain below -20 dB (VSWR < 1.2:1) across the operating band. Unterminated lines double signal amplitude via constructive reflection, corrupting timing and voltage measurements.

**Sampling Theorem and Aliasing**: Digital oscilloscopes must sample at >2× the highest frequency component (Nyquist criterion) to reconstruct waveforms without aliasing. For a 100 MHz sine wave, 200 MSa/s minimum sample rate suffices, but practical reconstruction demands 10× oversampling (1 GSa/s). Verify by measuring a 100 MHz sine at 100 MSa/s: aliasing produces a false 0 Hz (DC) or low-frequency artifact. Enable the oscilloscope's bandwidth limit filter (20 MHz typical) when measuring low-frequency signals to suppress out-of-band noise aliasing into the measurement band.

**Noise Floor and Dynamic Range**: Oscilloscope noise floor limits minimum detectable signal amplitude. For a DSO with 8-bit ADC and 1 V full-scale range, LSB resolution = 1 V / 2⁸ = 3.9 mV, yielding ~6 effective bits (ENOB) after accounting for quantization noise and jitter. Improve SNR by signal averaging: N averages improves SNR by √N. For 100 averages, SNR improves 20 dB. Spectrum analyzers achieve -120 dBm noise floor (0.7 µVRMS in 50 Ω) via narrow RBW and post-detection filtering.

**Calibration and Traceability**: Measurement accuracy depends on instrument calibration linearity and stability. Calibrate multimeters annually against NIST-traceable voltage and resistance standards (Fluke 5730A multifunction calibrator or equivalent). Verify oscilloscope timebase against a GPS-disciplined 10 MHz reference annually, and vertical gain against a precision voltage standard quarterly. VNA calibration (SOLT or TRL) nullifies systematic errors but remains valid only if connectors remain undisturbed and temperature stable within ±2 °C. Document all calibration events with date, certificate number, and environmental conditions.

### Troubleshooting Decision Tree for Measurement Anomalies

**Symptom**: Oscilloscope waveform exhibits excessive noise or hash, obscuring signal features.
- **Check**: Probe ground lead length and connection integrity. Replace with spring ground or coaxial adapter.
- **Check**: Input coupling (AC versus DC). AC coupling blocks DC offsets but introduces low-frequency roll-off at ~10 Hz.
- **Check**: Bandwidth limit filter setting. Enable 20 MHz filter to suppress high-frequency noise when measuring <1 MHz signals.
- **Check**: Grounding: verify all instruments bonded to common ground point. Floating grounds create circulating currents and EMI pickup.
- **Action**: Increase signal averaging (16–256 averages) to reduce random noise by √N. If noise persists, suspect inadequate shielding or nearby EMI sources (switching supplies, digital clocks).

**Symptom**: Frequency counter reading drifts or displays unstable values.
- **Check**: Gate time setting. Increase to 1–10 seconds for sub-Hz resolution. Short gate times (0.1 s) yield ±10 Hz uncertainty at 10 MHz.
- **Check**: Input signal amplitude and SNR. Frequency counters require >100 mVpp signal with SNR >20 dB for reliable triggering.
- **Check**: Trigger level and hysteresis. Auto-trigger may false-trigger on noise; set manual trigger at 50% of signal amplitude.
- **Action**: If drift correlates with temperature, suspect oscillator tempco. Log frequency versus temperature, compute tempco, and compensate mathematically or upgrade to TCXO/OCXO.

**Symptom**: VNA S-parameter measurement shows ripple or spurious resonances in passband.
- **Check**: Calibration status. Re-execute SOLT calibration if >1 hour elapsed or connectors disturbed.
- **Check**: Cable flexure and connector torque. Hand-tighten SMA connectors to 8 in-lb (avoid over-torque which deforms center pin).
- **Check**: Port power level. Excessive power saturates DUT or VNA mixer, generating harmonics and intermodulation. Reduce to -10 dBm.
- **Action**: Increase averaging (16–64 traces) to suppress noise floor. Apply time-domain gating to remove reflections from cable discontinuities beyond the DUT.

**Symptom**: Spectrum analyzer displays unexpected spurs or broadband noise floor elevation.
- **Check**: Input attenuation. Insufficient attenuation (<10 dB) allows strong signals to overdrive the mixer, generating spurious products.
- **Check**: RBW and VBW settings. Narrow RBW increases frequency resolution but requires longer sweep time. Ensure VBW ≤ RBW to prevent excessive noise averaging distortion.
- **Check**: Preamplifier setting. Internal preamp reduces noise floor by 10–15 dB but saturates at -30 dBm input. Disable for strong signals.
- **Action**: Identify spur sources by correlating spur frequency with known oscillators (clock harmonics, power supply switching frequency). Use marker math to compute spur offset from carrier: if offset = 60 Hz or 120 Hz, suspect mains pickup; if offset = Fswitching, suspect power supply EMI coupling.

**Symptom**: Load transient undershoot exceeds specification despite adequate output capacitance.
- **Check**: Capacitor ESR. Measure in-circuit ESR with an impedance analyzer or LCR meter at 100 kHz. Target ESR <0.02 Ω for low-dropout regulators.
- **Check**: PCB layout. Kelvin sense routing: connect sense traces directly to load, not through the capacitor.
- **Check**: Capacitor dielectric type. X7R ceramics lose 60% capacitance at rated voltage; prefer X5R or C0G for stable capacitance.
- **Action**: Parallel multiple capacitors (e.g., 3× 22 µF) to reduce effective ESR by 3× and distribute current. Place capacitors symmetrically around load to minimize loop inductance.

**Symptom**: PSRR measurement shows lower rejection than datasheet specification.
- **Check**: Measurement setup: inject ripple via bias tee, not through input capacitor which forms a voltage divider.
- **Check**: Frequency: PSRR degrades above loop bandwidth (~100 kHz). Verify measurement frequency within specification conditions.
- **Check**: Load current: PSRR improves at higher load current (feedback loop operates in higher-gain region). Match test load to datasheet conditions.
- **Action**: If PSRR remains below spec, suspect PCB layout: inadequate ground plane or excessive input capacitor ESR. Measure ripple directly at LDO input pin to exclude external coupling.

### Equipment Maintenance and Calibration Schedule

**Daily Procedures**:
- Verify oscilloscope probe compensation before measurements. Adjust trimmer capacitor for flat square wave response.
- Clean instrument front panels and connectors with isopropyl alcohol and lint-free cloth. Remove oxidation from SMA connectors with brass brush.
- Inspect probe cables for kinks or damage. Replace damaged probes immediately—internal broken shields act as antennas, injecting noise.

**Monthly Procedures**:
- Cross-check multimeter accuracy against a secondary voltage reference (battery-backed 10 V reference or Zener diode standard). Deviation >0.01% triggers recalibration.
- Verify signal generator frequency accuracy against GPS-disciplined reference or oscilloscope frequency counter. Deviation >2 ppm triggers service.
- Clean VNA calibration kit connectors with contact cleaner (DeoxIT Gold) and inspect for thread damage.

**Annual Procedures**:
- Factory calibration for all primary instruments: oscilloscopes, multimeters, spectrum analyzers, signal generators. Obtain NIST-traceable calibration certificates documenting traceability chain.
- Replace oscilloscope probe cables showing increased capacitance (measure with impedance analyzer: C > 15 pF indicates degraded dielectric).
- Update instrument firmware to latest stable release. Archive previous firmware version in case rollback required.

**Instrument-Specific Service Notes**:
- Oscilloscopes: Clean cooling fan filters quarterly. Dust accumulation restricts airflow, causing thermal drift and calibration errors.
- Spectrum analyzers: Replace aging YIG-tuned oscillator (YTO) if phase noise floor degrades >5 dB or sweep linearity errors exceed 0.1%.
- VNAs: Store mechanical calibration kits in sealed containers with desiccant. Humidity corrodes precision connectors, degrading return loss >3 dB.
- Signal generators: For OCXOs and rubidium standards, perform warm-up cycle (24 hours continuous power) monthly to prevent oscillator aging.

This operational guide and diagnostic checklist codifies the empirical discipline required to transform measurement instrumentation from passive recording devices into active agents of hardware interrogation, bridging the chasm between theoretical circuit models and physical reality embodied in silicon, solder, and copper.
