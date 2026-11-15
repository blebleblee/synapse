# Lesson 6: Data Converters, Oscillators, and Phase-Locked Loops

## 1. First-Principles Intuition & Invariants

Every mixed-signal system rests on a fundamental tension: the physical world is relentlessly continuous, while the computational world demands discrete, quantized representations. Data converters are the gatekeepers at this border. An analog-to-digital converter (ADC) does not merely "sample" a signal; it commits an irreversible act of approximation, discarding energy and information that can never be recovered. Understanding *why* that information is lost, and *how much*, is the bedrock intuition every analog designer must carry before touching a schematic.

The Nyquist-Shannon sampling theorem establishes the first invariant: a band-limited signal with maximum frequency component $f_{max}$ can be perfectly reconstructed from uniform samples taken at a rate $f_s \geq 2 f_{max}$. This is not a guideline — it is a mathematical guarantee, and violating it produces aliasing, the irreversible folding of out-of-band energy back into the baseband. In practice, anti-aliasing filters with finite roll-off force $f_s$ to be three to ten times $f_{max}$ in real systems, trading converter speed budget against filter order. Oversampling converters like delta-sigma architectures invert this trade deliberately, using extreme oversampling ratios (OSR of 64 to 512) to push quantization noise out of band, then reclaiming it with a digital decimation filter.

Quantization itself introduces a second invariant: for a uniform $N$-bit ADC with full-scale range $V_{FS}$, the least significant bit (LSB) represents a voltage step of $\Delta = V_{FS} / 2^N$, and the theoretical signal-to-noise-plus-distortion ratio (SNDR) of an ideal converter driven with a full-scale sinusoid is:

$$\text{SNDR}_\text{ideal} = 6.02N + 1.76 \;\text{dBFS}$$

This relation is the engineer's ruler. A 12-bit ADC should deliver roughly 74 dB of SNDR; a 16-bit converter around 98 dB. Measured performance always falls short of this ceiling because of aperture jitter, thermal noise, nonlinearity, and reference noise, which is why the effective number of bits (ENOB) metric exists: $\text{ENOB} = (\text{SNDR}_\text{measured} - 1.76) / 6.02$. When a datasheet claims 16-bit resolution but the ENOB is 13.5, those missing 2.5 bits are real and consequential for your signal chain.

The oscillator world is governed by a different first principle: a circuit sustains oscillation when two conditions are simultaneously satisfied at a single frequency — the Barkhausen criteria. The loop gain magnitude must equal unity, and the total phase shift around the feedback loop must equal zero (or an integer multiple of 360°). This sounds simple. In practice, maintaining both conditions across temperature, supply voltage, and process variation while keeping phase noise low enough to be useful is one of the hardest problems in analog design. Phase noise is the oscillator's figure of merit, characterizing the spectral purity of the output as the power spectral density of phase fluctuations $\mathcal{L}(f_m)$ expressed in dBc/Hz at an offset frequency $f_m$ from the carrier. The Leeson model provides physical intuition:

$$\mathcal{L}(f_m) = 10 \log\left[\frac{2FkT}{P_{sig}}\left(1 + \frac{f_0^2}{4Q_L^2 f_m^2}\right)\left(1 + \frac{f_c}{f_m}\right)\right]$$

where $F$ is the device noise figure, $k$ is Boltzmann's constant, $T$ is temperature, $P_{sig}$ is the signal power at the tank, $Q_L$ is the loaded quality factor of the resonator, $f_0$ is the oscillation frequency, and $f_c$ is the flicker noise corner. The profound implication is that phase noise improves with $Q_L^2$ — a resonator's $Q$ factor matters more than any other single parameter. Crystal resonators with $Q$ values of $10^5$ to $10^6$ outperform LC tanks ($Q$ of 5 to 50) by orders of magnitude in phase noise performance, which is why high-purity clocking always bottoms out in a quartz or MEMS reference.

Phase-locked loops (PLLs) synthesize frequencies and clean up clock jitter by locking a controllable oscillator to a reference through a feedback loop governed by control theory. The core invariant of a PLL is that in the locked state, the phase error between reference and feedback is bounded, and the loop dynamics — the bandwidth, peaking, and stability margins — entirely determine how well the PLL rejects oscillator noise inside the loop bandwidth and how well it rejects reference noise outside it. Getting the loop filter design wrong by 20% in bandwidth can push phase margin below 45°, producing peaking in the output spectrum and ringing in the time domain that destroys clock integrity in high-speed digital systems.

---

## 2. Core Architecture & Mechanics

### Successive Approximation Register (SAR) ADC

The SAR ADC is the workhorse of medium-to-high resolution, medium-to-high speed conversion. Its architecture is elegant: a sample-and-hold (S/H) captures the input, and a binary search algorithm implemented in hardware converges on the digital code over $N$ successive approximation cycles, each comparing the held input against a DAC output. The DAC is typically a charge-redistribution capacitor array — a network of binary-weighted capacitors where each capacitor value is exactly $C$, $2C$, $4C$, $8C$, up to $2^{N-1}C$.

The conversion sequence begins when the sample phase ends and the hold begins. The MSB capacitor ($2^{N-1}C$) is switched to the reference voltage $V_{REF}$, all others to ground, and the comparator determines whether the DAC output is above or below the held input. If above, the MSB is set to zero and that capacitor returns to ground; if below, the MSB stays set. This trial-and-decision process repeats down to the LSB. The total conversion time is $N+1$ clock cycles: one for sampling, $N$ for bit trials.

```
SAR ADC Internal Architecture:
┌─────────────────────────────────────────────────────────┐
│  VIN ──► [S/H Switch] ──► [Charge-Redistribution DAC]   │
│                                │                         │
│         ┌──────────────────────▼──────────────┐         │
│         │   C/2  C/4  C/8  C/16 ... C/2^N     │         │
│         │  [MSB]─────────────────────[LSB]     │         │
│         │   │     │    │    │           │      │         │
│         │  VREF/GND switch array (SAR ctrl)    │         │
│         └──────────────────┬──────────────────┘         │
│                            │                             │
│                      [Comparator]                        │
│                            │                             │
│                      [SAR Logic]  ◄──── Clock            │
│                            │                             │
│                      [Output Register]  D[N-1:0]         │
└─────────────────────────────────────────────────────────┘
```

The critical design constraint in the charge redistribution DAC is capacitor matching. A 1-LSB error at any bit position produces a differential nonlinearity (DNL) error that causes missing codes or non-monotonic behavior. For a 12-bit SAR, the capacitor ratio accuracy required is $1/2^{12} \approx 0.024\%$ — well within reach for matched poly capacitors in a modern CMOS process, but requiring careful layout with common-centroid geometry and dummy capacitors at the array periphery to cancel gradient effects. Parasitic capacitance at the comparator input node ($C_{par}$) also degrades accuracy; it appears in parallel with the LSB capacitor, perturbing the binary weighting. Many designs add a small attenuation capacitor to the array's bottom plate to absorb this effect.

A 12-bit, 1 Msps SAR such as the AD7091R draws roughly 358 µA from a 1.8 V supply and achieves 69.5 dB SNDR, translating to an ENOB of 11.26 bits. The gap from 12-bit ideal to 11.26-bit ENOB is dominated by comparator noise and DAC mismatch, not quantization noise.

### Pipeline ADC

Where the SAR trades time (N cycles per conversion) for hardware simplicity, the pipeline ADC trades hardware (N stages) for throughput. Each stage in the pipeline resolves a small number of bits (typically 1.5 bits per stage in modern designs), generates a residue equal to the input minus the stage's DAC output scaled up by the interstage gain, and passes that residue to the next stage. The 1.5-bit-per-stage architecture is particularly robust because it provides one bit of redundancy at each stage, allowing the digital error correction logic to absorb comparator offset errors up to half an LSB of the stage's range, without expensive trimming.

The fundamental building block is the multiplying DAC (MDAC), implemented as a switched-capacitor (SC) circuit. During the sampling phase, two equal capacitors $C_S$ each sample the input $V_{in}$. During the amplification phase, one capacitor switches its bottom plate to $+V_{REF}$, $-V_{REF}$, or ground (the 1.5-bit decision), while the other remains in the feedback loop of an op-amp, creating a closed-loop gain of exactly 2. The residue output is $V_{res} = 2V_{in} - V_{DAC}$.

The inter-stage gain of exactly 2 demands an op-amp with enough open-loop gain that the closed-loop gain error is below 0.5 LSB for the final resolution. For a 14-bit pipeline, the stage gain error must be below $1/(2 \cdot 2^{14}) \approx 30 \text{ ppm}$, requiring an op-amp DC gain above approximately $2 / 30\text{e-6} \approx 65{,}000$ V/V (96 dB). This is why high-speed pipeline ADCs push op-amp design to the edge: gain-bandwidth product, slew rate, and output swing all fight each other as supply voltages scale down with process node.

Calibration has become essential in modern pipeline ADCs. Digital background calibration techniques inject a small pseudo-random dither sequence, observe its effect in the output, and iteratively converge on correction coefficients for each stage's gain and offset errors. This allows the ADC to meet 16-bit linearity using capacitors that only match to 12-bit natural accuracy, effectively buying 4 bits of performance from the calibration algorithm. The TI ADS9224R uses this approach to achieve 16-bit, 3 Msps performance with 93 dB SNR.

### Delta-Sigma (ΔΣ) ADC

The delta-sigma architecture embraces coarse quantization — often just a single comparator (1-bit quantizer) — and compensates with extreme oversampling combined with noise shaping. The noise shaping mechanism is the key: a first-order ΔΣ modulator places a differentiator $H(z) = 1 - z^{-1}$ in the feedback path of the quantization noise, which spectrally shapes the noise away from DC toward higher frequencies. A second-order modulator applies $(1-z^{-1})^2$, pushing even more noise out of band, and so on for higher orders.

The quantization noise density at the input to the digital decimation filter is not flat (white) as it would be in a Nyquist converter — it rises with frequency following the noise shaping function. The digital decimation filter then low-pass filters and downsamples this shaped noise, retaining only the signal-band portion. The achievable SQNR for an $L$-th order modulator with an oversampling ratio $\text{OSR} = f_s / (2 f_{BW})$ is approximately:

$$\text{SQNR} \approx 10\log_{10}\left(\frac{3(2L+1)}{2\pi^{2L}} \cdot \frac{3}{2} \cdot 2^{2B} \cdot \text{OSR}^{2L+1}\right)$$

where $B$ is the number of bits in the internal quantizer. For a first-order, 1-bit modulator with OSR = 256, SQNR is approximately 60 dB — only 10 bits. For a second-order modulator with OSR = 256, SQNR jumps to roughly 100 dB — over 16 bits. This OSR doubling with $2L+1$ exponent is why audio ΔΣ converters operating at 128× or 256× oversampling achieve 24-bit ENOB with comparators that individually resolve only 1 bit.

The practical constraint is modulator stability. Order-3 and higher continuous-time ΔΣ modulators are conditionally stable — the integrator chain can overload if the input signal exceeds a certain amplitude relative to the reference. Loop coefficient scaling (Lee's criterion and the more rigorous root-locus stability analysis) is used to set the integrator output swings, and clipping indicators in the digital filter output are used to detect overload in deployment.

### DAC Architectures and Linearity

A digital-to-analog converter reconstructs an analog signal from a digital word. The two dominant implementations are the R-2R resistor ladder and the current-steering DAC. The R-2R ladder is elegant: a recursive network of resistors with values $R$ and $2R$ creates binary-weighted current contributions from each bit without requiring a separate resistor for each bit weight. Its INL (integral nonlinearity) and DNL performance are dominated by resistor matching, which is achievable to 10 to 12 bits in thin-film laser-trimmed networks.

For higher speeds (100 Msps and above), the current-steering DAC topology dominates. Each bit (or thermometer-coded group of bits) controls a matched current source that steers current either to the output node or to a dummy load, keeping the current source always active to avoid switching transients from current source settling. The MSB current sources are typically implemented with binary-weighting, while the upper bits use thermometer (fully decoded) coding to guarantee monotonicity and to reduce glitch energy. The differential nonlinearity of a current-steering DAC is dominated by current source mismatch, which follows a statistical model: for unit-cell current sources with relative mismatch $\sigma_I / I$, the DNL standard deviation for the most significant bit is approximately $2^{N/2} \cdot (\sigma_I / I)$ LSBs. This scaling means that going from 12 to 14 bits requires four times better current source matching — a primary driver of DAC area growth.

Glitch impulse area is the other critical DAC metric. When a major-carry transition occurs (e.g., 0111...1 to 1000...0), all $N$ bits toggle simultaneously, and due to unequal switching delays between turning off lower-bit sources and turning on the MSB, a large current spike appears on the output. This glitch energy, measured in nV·s, folds back into the signal band after reconstruction filtering and manifests as spurious tones at harmonic multiples of the update frequency. Proper layout minimizing interconnect length asymmetry, matched current source loading, and deglitch circuits that briefly force the output to a midscale level during transitions all suppress glitch energy.

### LC and Ring Oscillators

LC oscillators sustain sinusoidal oscillation by exchanging energy periodically between an inductor $L$ and a capacitor $C$. The resonant frequency is:

$$f_0 = \frac{1}{2\pi\sqrt{LC}}$$

The tank circuit is lossy — the inductor has series resistance $r_s$, and the capacitor has dielectric loss — giving the tank a quality factor $Q_L = \omega_0 L / r_s$. An active device (typically a cross-coupled CMOS differential pair in integrated designs, or a BJT Colpitts/Clapp topology in discrete designs) supplies the negative resistance needed to cancel tank loss. The cross-coupled pair presents an input impedance of $-2/g_m$ differentially, and for oscillation to start, the magnitude of this negative resistance must exceed the tank loss resistance $R_P$ (the parallel equivalent of the tank). The startup condition is therefore $g_m > 2/R_P$, with a safety margin of 2× to 3× typically used in design to guarantee oscillation over process corners.

For a practical 2.4 GHz LC VCO in 65 nm CMOS: a symmetric inductor of 2 nH with $Q$ of 8 at 2.4 GHz presents $R_P = Q \cdot \omega_0 L \approx 8 \cdot (2\pi \cdot 2.4\text{e9}) \cdot 2\text{e-9} \approx 241 \;\Omega$. The required $g_m$ for startup is $2/241 \approx 8.3$ mS, and a cross-coupled pair biased at 2 mA with $g_m \approx 20$ mS provides the 2.4× margin. The varactor diode (a reverse-biased CMOS accumulation-mode MOS capacitor) allows the oscillation frequency to be tuned by varying $C$ with the control voltage, giving the VCO its gain $K_{VCO}$ in Hz/V.

Ring oscillators replace the high-Q resonator with a cascade of inverting delay stages, with the total loop phase shift equal to 180° from the digital inversions plus 180° from the propagation delay, satisfying Barkhausen at the frequency where stage delay $\tau_d = 1/(2N f_0)$ for $N$ stages. Ring oscillators offer very wide tuning range (easily an octave or more) and integrate readily in digital CMOS without inductors. Their fatal weakness is phase noise: without a high-Q resonator to anchor the energy, the phase diffuses freely according to random thermal noise perturbations in the inverter switching thresholds. Phase noise in a ring oscillator is roughly $20 \log(N)$ worse than an LC oscillator with equivalent power consumption — often 20 to 30 dB inferior, which is why ring oscillators are confined to on-chip clock generation where jitter requirements are modest (picosecond-class tolerance) and LC oscillators or crystal references are reserved for RF carrier synthesis.

### PLL Loop Dynamics and Charge Pump Architecture

A phase-locked loop is a feedback control system that minimizes the phase difference between a reference signal and the output of a voltage-controlled oscillator divided by an integer ratio $N$. The standard integer-N PLL topology contains four subsystems: the phase-frequency detector (PFD), the charge pump (CP), the loop filter (LF), and the VCO.

```
Integer-N PLL Signal Flow:
                    ┌──────────────────────────────────────┐
                    │                                      │
  FREF ──► [PFD] ──► [Charge Pump] ──► [Loop Filter] ──► [VCO] ──► FOUT
            ▲                                                │
            │               ÷N                              │
            └──────────── [Divider] ◄───────────────────────┘
```

The phase-frequency detector compares the rising edges of the reference $F_{REF}$ and the divided feedback $F_{FB}$, asserting a UP pulse if $F_{FB}$ lags, or a DOWN pulse if it leads. These pulse widths are proportional to phase error. The charge pump converts these digital pulses into analog current impulses: the UP path sources current $I_{CP}$ into the loop filter, and the DOWN path sinks $I_{CP}$ from it. The loop filter integrates these impulses into a smooth control voltage $V_{CTRL}$, which tunes the VCO.

The loop filter is almost universally a passive RC network — a series R-C combination (C1 and R1) with an additional shunt capacitor C2 to filter charge pump current spikes. This creates a second-order low-pass filter that, combined with the VCO's integrating behavior (phase is the integral of frequency), makes the open-loop transfer function a type-2, second-order system. The open-loop gain is:

$$G(s) = \frac{I_{CP}}{2\pi} \cdot \frac{K_{VCO}}{N} \cdot \frac{1 + sR_1C_1}{s^2 C_1 (1 + sR_1C_2/(C_1+C_2))}$$

where the $1/s^2$ factor (two poles at the origin) confirms the type-2 nature. The loop bandwidth $\omega_n$ and damping factor $\zeta$ are set by $I_{CP}$, $K_{VCO}$, $N$, $R_1$, and $C_1$. For a phase margin of 60°, the standard design procedure targets $\zeta \approx 0.7$ to 1.0, which requires the zero frequency $\omega_z = 1/(R_1 C_1)$ to be placed approximately at $\omega_n / 2.2$ below the loop bandwidth.

Concretely: for a PLL with $f_{REF} = 10$ MHz, $N = 240$ (synthesizing 2.4 GHz), $K_{VCO} = 100$ MHz/V, and $I_{CP} = 1$ mA, targeting a loop bandwidth of 100 kHz with 60° phase margin:

The natural frequency is $\omega_n = 2\pi \cdot 100\text{e3} = 628$ krad/s. Using the second-order approximation $\omega_n = \sqrt{I_{CP} \cdot K_{VCO} / (2\pi \cdot N \cdot C_1)}$, solving for $C_1 = I_{CP} \cdot K_{VCO} / (2\pi \cdot N \cdot \omega_n^2) = (1\text{e-3} \cdot 2\pi \cdot 100\text{e6}) / (2\pi \cdot 240 \cdot (628\text{e3})^2) \approx 1.67$ nF. The phase margin condition gives $R_1 = 2\zeta / (\omega_n C_1) = 2 \cdot 0.707 / (628\text{e3} \cdot 1.67\text{e-9}) \approx 1.35$ kΩ. The shunt capacitor $C_2 = C_1 / 10 \approx 167$ pF to push the third pole to $10\omega_n$, well outside the phase margin crossover.

VCO gain $K_{VCO}$ deserves special attention because it appears directly in both the loop gain and the VCO's phase noise performance from supply-induced FM modulation. A high $K_{VCO}$ makes the loop respond aggressively but also makes the VCO's output frequency sensitive to supply noise — every millivolt of ripple on the control line multiplied by $K_{VCO}$ appears as frequency modulation. LC VCOs in PLL applications typically use switched-capacitor banks to coarsely select the frequency band and limit the varactor's tuning range (and thus $K_{VCO}$) to 50 to 200 MHz/V, keeping supply sensitivity manageable.

---

## 3. High-Performance Optimization & Failure Modes

### Aperture Jitter and ADC Clock Quality

The single most underappreciated performance limiter in high-speed ADC systems is aperture jitter — the uncertainty in the moment the sample is actually captured. For a sinusoidal input at frequency $f_{in}$ with amplitude $A$, the voltage error due to timing jitter $\sigma_t$ is $\sigma_V = 2\pi f_{in} A \sigma_t$. This noise adds directly to the total noise floor, capping the achievable SNDR at:

$$\text{SNDR}_{max} = -20\log_{10}(2\pi f_{in} \sigma_t)$$

For a 14-bit ADC sampling a 100 MHz input signal, achieving 86 dB SNDR requires $\sigma_t < 1 / (2\pi \cdot 100\text{e6} \cdot 10^{86/20}) \approx 80$ fs RMS. This is an extraordinarily demanding clock quality requirement. Achieving 80 fs RMS jitter at the ADC sample clock input requires a crystal oscillator, a low-noise PLL or clock buffer with better than −160 dBc/Hz in-band phase noise, and a PCB layout where the clock trace is treated as an RF signal — 50 Ω controlled impedance, no stubs, terminated at the source or load, and physically isolated from digital signal transitions that could couple noise through the board's power planes.

A common bench failure mode is the engineer who measures excellent ADC SNDR at low input frequencies (proving the ADC itself is healthy) but sees SNDR cliff-diving above 20 MHz. The diagnosis is almost always the clock source: a function generator with 1 ps RMS jitter (perfectly adequate for 1 MHz input work) is catastrophically noisy for a 100 MHz IF sampling ADC. The fix is a low-jitter clock oscillator (SiTime SIT9516 or similar TCXO) followed by a dedicated clock fanout buffer (TI CDCLVP1102 or ADI ADCLK948) with its own decoupled power supply, routed last before the ADC sample clock pin.

### SAR DAC Mismatch and Bit Error Injection

SAR ADC DNL errors manifest as distinctive waveform artifacts that an oscilloscope cannot reveal but a spectrum analyzer can unmask. When the capacitor ratio at a mid-scale major-carry transition (code 2047 to 2048 in a 12-bit converter) is off by even 0.5 LSB, the ADC exhibits a "bubble" — a range of input voltages that map to no output code (missing code) or to two consecutive codes. In the frequency domain, this nonlinearity produces harmonic distortion, particularly third-order intermodulation products (IM3) when two tones are applied simultaneously.

Diagnosis procedure: apply a 1 kHz full-scale sine wave to the ADC, capture 32768 samples, compute the FFT with a Hann window, and examine the spurious-free dynamic range (SFDR). If the SFDR is 20 dB below the datasheet specification, examine the histogram of the output codes. Missing codes appear as bins with zero count; excess codes (caused by gain error at the same transition) appear as bins with double the expected count. For a uniform sine wave input, the ideal code histogram follows a $1/\sqrt{1-(2k/2^N - 1)^2}$ distribution — deviations from this shape map precisely to the INL curve.

For precision measurement applications (vibration analysis, medical imaging, instrumentation), the standard remediation is on-chip or external calibration. Texas Instruments' ADS127L11 uses a foreground calibration sequence that measures the capacitor mismatch directly by injecting a known charge and reading the residue, then stores correction coefficients in internal SRAM. The calibration cycle takes approximately 10 ms and should be re-run every 10°C of temperature change to track TC-induced capacitor drift.

### Pipeline ADC Gain Error and Sparkle Codes

The most insidious failure mode in high-speed pipeline ADCs is the "sparkle code" — a rare, random output code that is wildly incorrect by hundreds or thousands of LSBs. These events occur when the comparator in an early pipeline stage makes a wrong decision (a metastability event) and the downstream stages propagate the error. Metastability occurs when the comparator's input differential voltage is so close to zero that the regenerative pair does not resolve before the clock edge latches the decision; the output dwells in an indeterminate voltage between logic 0 and 1, which the later stages interpret unpredictably.

The probability of a sparkle code is proportional to $\exp(-t_{resolve}/\tau)$, where $t_{resolve}$ is the time given for regeneration and $\tau = 1/(g_m/C)$ is the regeneration time constant of the comparator. At higher sampling rates, $t_{resolve}$ shrinks, and sparkle rates rise exponentially. Modern pipeline ADCs guard against this with the 1.5-bit-per-stage digital error correction: even if a comparator in stage 1 produces the wrong result, the residue output of that stage still passes the input signal information forward, and the error appears only as a stage 1 offset which the digital correction logic absorbs within the ±$V_{REF}/4$ correction range, as long as the comparator offset is bounded.

However, if the input to the first stage overdrive is applied — a signal that exceeds $V_{REF}$ — the MDAC output clips, and digital error correction can no longer recover the sample. The overrange detector assert-time is therefore critical. If the application involves transient overdrive (RF switching pulses, ESD events, electrical fast transients in industrial environments), place a precision analog clamp — such as back-to-back Schottky diodes to the reference rails, or a dedicated clamping amplifier — before the ADC input, ensuring recovery time shorter than one conversion period.

### PLL Phase Noise, Reference Spurs, and Lock Failures

PLL output phase noise has a characteristic noise transfer function that creates the "bathtub curve" shape seen on a spectrum analyzer or clock analyzer. Inside the loop bandwidth, the PLL tracks the reference, so the output phase noise follows the reference noise multiplied by $20\log(N)$ — this is the fundamental cost of frequency multiplication. Outside the loop bandwidth, the PLL tracks the VCO, so the output phase noise reverts to the free-running VCO phase noise rolling off at −20 dBc/Hz per decade (Leeson flat region) transitioning to −30 or −40 dBc/Hz beyond the flicker corner. The optimal loop bandwidth for minimum integrated phase noise lies at the crossover between these two noise regimes, which you can read directly from overlaid reference and VCO noise plots.

Reference spurs are discrete spectral lines appearing at $f_{REF}$ offsets from the carrier. They arise from charge pump current mismatch between the UP and DOWN paths. Even in the locked state, the PFD generates small, equal-width UP and DOWN pulses (the "dead zone avoidance" pulses) on every reference cycle; if $I_{UP} \neq I_{DOWN}$ by even 0.1%, a net charge injection of $\Delta I \cdot t_{pulse}$ periodically perturbs $V_{CTRL}$ at $f_{REF}$, which the VCO converts to FM sidebands. Mitigation requires careful charge pump design with matched PMOS/NMOS current mirrors, common-centroid layout of the mirror transistors, and cascode biasing to maintain drain-source voltage equality between UP and DOWN transistors. At the system level, a narrow-band notch in the loop filter at $f_{REF}$ can suppress residual spurs, though at the cost of loop filter complexity and reduced phase margin.

PLL lock detection is a frequent source of system-level failures in frequency synthesizers. A lock detector circuit typically measures whether the PFD's UP/DOWN pulse widths remain below a threshold window for $M$ consecutive reference cycles, then asserts a lock-indicate flag. If the flag logic gates the downstream RF chain or enables a DAC output, a marginal lock condition (loop is "near" lock but oscillating with 10–100 kHz residual phase error) can cause intermittent unlock events that the digital controller's timeout logic does not catch because the average phase error appears small. The cure is to monitor both the digital lock detect signal and the analog $V_{CTRL}$ voltage through a comparator window circuit, verifying that $V_{CTRL}$ sits within the VCO's linear tuning range before declaring system ready.

### Oscillator Startup Failures and Frequency Pulling

A crystal oscillator that fails to start is a common embedded systems problem that traces directly to the Barkhausen margin analysis being done at room temperature in simulation but not at the cold-temperature corner under degraded supply. CMOS inverter oscillators for crystals (the standard microcontroller clock circuit) depend on the inverter small-signal transconductance $g_m$, which is proportional to both $\sqrt{I_D}$ and to $\mu_n C_{ox} W/L$. At $-40°$C, carrier mobility increases modestly, but at low supply voltage the threshold voltage $V_T$ rises, reducing overdrive and $g_m$. Simultaneously, the crystal's motional resistance $R_m$ increases at low temperatures (a 20–50% rise from +25°C to −40°C is typical for AT-cut crystals). The startup gain margin, defined as $g_m / (4\pi^2 f_0^2 C_{L1} C_{L2} R_m)$ where $C_{L1}$ and $C_{L2}$ are the CMOS inverter load capacitors, can fall below 5× at the cold-fast process corner, risking no-start.

The quantitative design rule is to target a gain margin of at least 5× under worst-case conditions. Increasing $C_{L1}$ and $C_{L2}$ simultaneously increases the loop gain but also increases the oscillation startup time ($\sim C_L R_m \cdot \ln(\text{margin})$ cycles). For a 32.768 kHz RTC crystal with $R_m = 70\; k\Omega$ and $C_L = 7$ pF, the startup time at 5× margin is approximately $7\text{e-12} \cdot 70\text{e3} \cdot \ln(5) / (2 \cdot 32768) \approx 11$ ms — well within microcontroller reset supervisor tolerances. If startup margin analysis reveals a risk, reducing $C_L$ (to increase margin) while switching to a crystal with lower $R_m$ is preferable to simply increasing inverter $g_m$, which raises drive level and can overdrive the crystal into nonlinear operation, actually pulling the oscillation frequency away from the nominal by several ppm.

Frequency pulling is the shift in oscillation frequency caused by changes in the load capacitance presented to the crystal, and it is the dominant accuracy mechanism in crystals connected to CMOS pins with variable capacitance from neighboring switching logic. The pulling sensitivity of a crystal is $S = f_0 / (2 C_0 / C_m + C_L)^2$ where $C_0$ is the shunt capacitance and $C_m$ is the motional capacitance. For a 25 MHz crystal with $C_0 = 5$ pF, $C_m = 15$ fF, and $C_L = 10$ pF, pulling sensitivity is approximately 10 ppm/pF — meaning 1 pF of digital switching capacitance from an adjacent GPIO toggling couples through PCB parasitics and shifts the clock by 10 ppm, which at 25 MHz is a 250 Hz frequency excursion. Layout isolation (ground moat around the crystal and load capacitors, keepout zone under the crystal body, no signal vias within 2 mm) is not optional for oscillators above 1 MHz serving as timing references.
