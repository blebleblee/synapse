# Operational Verification Labs: Signal Processing

## Objective & Operational Lab Setup

Signal processing forms the operational backbone of analog and digital circuit design, bridging the continuous-time physical world with discrete-time computational systems. This laboratory sequence establishes hands-on proficiency in analyzing, filtering, modulating, and reconstructing signals through both analog circuit topologies and discrete-time algorithmic implementations. The practitioner will manipulate time-domain waveforms, frequency-domain spectral content, and phase relationships using oscilloscopes, spectrum analyzers, function generators, and computational tools including MATLAB, GNU Octave, Python SciPy, and SPICE-family circuit simulators.

The operational philosophy prioritizes direct measurement, empirical verification, and parameter sweeps over abstract mathematical formalism. Each exercise builds from fundamental signal operations—scaling, shifting, convolution—toward practical filter realization, sampling theory validation, and modulation scheme implementation. The laboratory environment integrates physical bench instrumentation with computational signal processing environments to cultivate intuition about how circuit parasitics, quantization noise, aliasing artifacts, and nonlinear distortion manifest in real systems.

### Required Laboratory Equipment and Software Stack

The physical instrumentation suite must include a dual-channel digital storage oscilloscope with at least 100 MHz bandwidth and 1 GSa/s sampling rate, enabling capture of both time-domain waveforms and FFT spectral displays. A programmable function generator capable of arbitrary waveform synthesis with 50 MHz bandwidth and adjustable DC offset provides signal excitation. A spectrum analyzer or oscilloscope with FFT capability allows frequency-domain verification, with resolution bandwidth settings down to 10 Hz for narrow-band analysis. A dual-output laboratory DC power supply with ±15V rails powers operational amplifier circuits and active filter stages.

Passive components include assorted carbon-film resistors spanning 100 Ω to 1 MΩ with 1% tolerance, multilayer ceramic capacitors from 10 pF to 10 µF, and polypropylene film capacitors for precision analog filters. Active devices comprise general-purpose operational amplifiers such as TL072 dual JFET-input op-amps with 3 MHz gain-bandwidth product and LM358 dual rail-to-rail op-amps, along with voltage comparators like LM311 for threshold detection and square wave generation. Breadboarding infrastructure uses solderless prototyping boards with short ground and power distribution rails to minimize parasitic inductance.

The computational environment requires MATLAB R2020a or later with Signal Processing Toolbox, or alternatively GNU Octave 6.0 or higher for open-source compatibility. Python 3.8 or later with NumPy 1.19, SciPy 1.5, and Matplotlib 3.3 libraries provides equivalent digital signal processing capabilities with Jupyter Notebook integration for interactive exploration. SPICE circuit simulation employs LTspice XVII for transient and AC analysis of analog filter topologies, with component models matching physical devices. A USB-based oscilloscope interface such as Digilent Analog Discovery 2 or Hantek 6022BE enables scripted acquisition and automated parameter sweeps when integrated with Python or MATLAB data acquisition toolboxes.

Calibration procedures must precede all measurements. Verify oscilloscope probe compensation by attaching the 10× passive probe to the instrument's calibration output and adjusting the probe's trimmer capacitor until the square wave exhibits no overshoot or droop. Confirm function generator amplitude accuracy by measuring a 1 kHz, 1 Vpp sine wave into a 50 Ω load with the oscilloscope's AC-coupled input. Set oscilloscope timebase and voltage scales to display three to five cycles of the waveform with peak-to-peak amplitude occupying 70-80% of the vertical display range, ensuring optimal quantization without clipping.

### Signal Representation and Mathematical Foundations

Continuous-time signals evolve as functions of real-valued time $x(t)$ where $t \in \mathbb{R}$, while discrete-time signals exist only at integer sample indices $x[n]$ where $n \in \mathbb{Z}$. The Fourier transform decomposes continuous signals into frequency components via $X(f) = \int_{-\infty}^{\infty} x(t) e^{-j2\pi ft} dt$, revealing spectral content as amplitude and phase functions of frequency. The discrete-time Fourier transform operates on sampled sequences as $X(e^{j\omega}) = \sum_{n=-\infty}^{\infty} x[n] e^{-j\omega n}$ where normalized angular frequency $\omega = 2\pi f / f_s$ relates continuous frequency $f$ to sampling rate $f_s$.

The sampling theorem, formalized by Nyquist and Shannon, dictates that perfect reconstruction of a band-limited continuous signal requires sampling at greater than twice the maximum frequency component. Mathematically, for a signal with bandwidth $B$, the minimum sampling rate $f_s > 2B$ prevents aliasing where high-frequency components fold back into the baseband spectrum. Aliasing manifests as spurious low-frequency artifacts when sampling rates violate this criterion, observable as unexpected spectral peaks and time-domain distortion that cannot be removed by post-processing.

Convolution represents linear time-invariant system behavior in both continuous and discrete domains. The continuous convolution integral $y(t) = \int_{-\infty}^{\infty} x(\tau) h(t-\tau) d\tau$ describes output $y(t)$ as the input signal $x(t)$ convolved with impulse response $h(t)$. Discrete convolution $y[n] = \sum_{k=-\infty}^{\infty} x[k] h[n-k]$ performs equivalent operations on sampled sequences. Convolution in the time domain corresponds to multiplication in the frequency domain via $Y(f) = X(f) H(f)$, providing the foundation for filter design where frequency response $H(f)$ shapes input spectral content to produce desired output characteristics.

### Analog Filter Topologies and Component Selection

Active filters constructed with operational amplifiers overcome the insertion loss limitations of passive LC networks while providing voltage gain and impedance buffering. The Sallen-Key topology implements second-order lowpass filters using two resistors, two capacitors, and a unity-gain voltage follower configuration. Component values determine cutoff frequency $f_c = 1/(2\pi\sqrt{R_1 R_2 C_1 C_2})$ and quality factor $Q$ which controls peaking near the cutoff. For Butterworth response with maximally flat passband, select $Q = 0.707$ by setting $C_1 = C_2 = C$ and $R_2 = 2R_1$.

Multiple feedback (MFB) topology offers inverting gain and higher Q factors suitable for sharper rolloff characteristics. The MFB lowpass configuration uses three resistors and two capacitors around an inverting operational amplifier, achieving cutoff frequency $f_c = 1/(2\pi\sqrt{R_1 R_3 C_1 C_2})$ with DC gain magnitude $|A_v| = R_3/R_1$. Cascading multiple second-order sections realizes higher-order filters, with each stage implementing a complex conjugate pole pair from Butterworth, Chebyshev, or Bessel polynomial factorizations.

Component tolerance directly impacts filter performance. Resistor tolerance of ±1% and capacitor tolerance of ±5% combine to produce cutoff frequency variations of approximately ±7%, requiring empirical trimming for precision applications. Temperature coefficient of capacitance (TCC) for ceramic dielectrics spans -1500 to +150 ppm/°C depending on dielectric class, while polypropylene film capacitors maintain ±100 ppm/°C stability. For frequency-critical filters, use metal-film resistors with ±25 ppm/°C temperature coefficient and polypropylene or polystyrene capacitors.

Operational amplifier gain-bandwidth product limits achievable filter cutoff frequencies. The TL072 with 3 MHz GBW restricts practical lowpass filter cutoff to approximately 300 kHz before phase margin degradation causes peaking and potential oscillation. Higher-speed amplifiers like AD8066 with 65 MHz GBW extend usable frequency range into the low-megahertz region. Slew rate limitations cause nonlinear distortion on large-signal transients; the TL072's 13 V/µs slew rate constrains full-power bandwidth to approximately 65 kHz for ±10V swing, calculated from $f_{max} = SR/(2\pi V_{pp})$.

## Exercise 1: Foundational Practical Implementation

### Time-Domain Signal Generation and Oscilloscope Measurement

This foundational exercise establishes proficiency in generating, capturing, and quantifying fundamental waveform parameters using bench instrumentation. The practitioner will synthesize sine, square, triangle, and pulse waveforms while measuring amplitude, frequency, rise time, duty cycle, and harmonic distortion through direct oscilloscope observation and cursor-based quantification.

Configure the function generator to produce a 1 kHz sine wave with 2 Vpp amplitude into a 50 Ω load termination. Connect the generator output through a BNC cable to oscilloscope channel 1 with a 10× passive probe. Set the oscilloscope to AC coupling with 500 mV/div vertical scale and 200 µs/div horizontal timebase, displaying five complete cycles. Activate the oscilloscope's measurement functions to compute frequency, peak-to-peak amplitude, RMS voltage, and total harmonic distortion. Record the measured frequency accuracy as the percentage deviation from the nominal 1 kHz setting, typically within ±0.01% for crystal-referenced generators.

Press the oscilloscope's FFT button to display frequency-domain spectral content. Configure the FFT with Hanning window, 1024-point length, and center frequency of 5 kHz to capture the fundamental and first four harmonics. Observe the fundamental peak at 1 kHz and note the absence of significant harmonic content for the undistorted sine wave. Measure the noise floor level, typically -60 to -80 dBV depending on oscilloscope vertical resolution and input coupling.

Change the function generator to square wave mode while maintaining 1 kHz frequency and 2 Vpp amplitude. Observe the time-domain waveform transition from sine to square, noting overshoot and ringing artifacts caused by finite bandwidth limitations. Measure rise time using the oscilloscope's 10%-90% rise time measurement function, recording values typically between 10-50 ns depending on generator specifications. Activate FFT display to observe the square wave's harmonic spectrum, with odd harmonics at 3 kHz, 5 kHz, 7 kHz diminishing in amplitude proportional to $1/n$ where $n$ represents harmonic number.

Switch to triangle wave generation and observe both time-domain slope transitions and frequency-domain harmonic structure. The triangle wave exhibits steeper harmonic rolloff at $1/n^2$, producing a cleaner spectrum than square waves. Measure the peak-to-peak amplitude and verify that the fundamental frequency remains at 1 kHz. Record FFT harmonic amplitudes at 3 kHz, 5 kHz, and 7 kHz, computing the ratio between fundamental and third harmonic in decibels using $20\log_{10}(V_3/V_1)$.

Generate a pulse waveform with 10% duty cycle and measure pulse width, rise time, fall time, and overshoot percentage. The pulse width should equal 100 µs for 1 kHz repetition rate with 10% duty cycle. Use oscilloscope cursors to measure overshoot amplitude relative to the steady-state pulse top, calculating overshoot percentage as $(V_{overshoot} - V_{steady})/V_{steady} \times 100\%$. Values exceeding 5% indicate impedance mismatch or excessive circuit reactance.

### Digital Signal Generation and Sampling in MATLAB/Octave

Launch MATLAB or GNU Octave and create a computational workspace for discrete-time signal synthesis. The following script generates fundamental waveforms with precise parameter control, demonstrating sampling theorem implications and spectral analysis through discrete Fourier transform computation.

```matlab
% Signal Processing Laboratory Exercise 1: Digital Signal Synthesis
% Sampling and Spectral Analysis

clear all; close all; clc;

% Sampling parameters
fs = 10000;              % Sampling frequency (Hz)
Ts = 1/fs;               % Sampling period (seconds)
duration = 1.0;          % Signal duration (seconds)
t = 0:Ts:duration-Ts;    % Time vector
N = length(t);           % Number of samples

% Sine wave generation
f_sine = 1000;           % Sine frequency (Hz)
A_sine = 1.0;            % Amplitude (V)
phase_sine = 0;          % Phase (radians)
x_sine = A_sine * sin(2*pi*f_sine*t + phase_sine);

% Square wave generation via Fourier series (9 harmonics)
x_square = zeros(size(t));
for n = 1:2:17
    x_square = x_square + (4/(n*pi)) * sin(2*pi*n*f_sine*t);
end

% Triangle wave generation via Fourier series (9 harmonics)
x_triangle = zeros(size(t));
for n = 1:2:17
    x_triangle = x_triangle + (8/(n^2*pi^2)) * (-1)^((n-1)/2) * sin(2*pi*n*f_sine*t);
end

% Pulse train generation (10% duty cycle)
duty_cycle = 0.10;
pulse_period = 1/f_sine;
pulse_width = duty_cycle * pulse_period;
x_pulse = A_sine * (mod(t, pulse_period) < pulse_width);

% Frequency domain analysis using FFT
X_sine = fft(x_sine);
X_square = fft(x_square);
X_triangle = fft(x_triangle);
X_pulse = fft(x_pulse);

% Frequency vector (single-sided spectrum)
f_vector = (0:N/2-1)*(fs/N);
X_sine_mag = abs(X_sine(1:N/2))/N;
X_square_mag = abs(X_square(1:N/2))/N;
X_triangle_mag = abs(X_triangle(1:N/2))/N;
X_pulse_mag = abs(X_pulse(1:N/2))/N;

% Time-domain plotting
figure('Position', [100 100 1200 800]);

subplot(4,2,1);
plot(t(1:100), x_sine(1:100), 'b-', 'LineWidth', 1.5);
grid on;
xlabel('Time (s)'); ylabel('Amplitude (V)');
title('Sine Wave - Time Domain');
xlim([0 0.01]);

subplot(4,2,3);
plot(t(1:100), x_square(1:100), 'r-', 'LineWidth', 1.5);
grid on;
xlabel('Time (s)'); ylabel('Amplitude (V)');
title('Square Wave - Time Domain');
xlim([0 0.01]);

subplot(4,2,5);
plot(t(1:100), x_triangle(1:100), 'g-', 'LineWidth', 1.5);
grid on;
xlabel('Time (s)'); ylabel('Amplitude (V)');
title('Triangle Wave - Time Domain');
xlim([0 0.01]);

subplot(4,2,7);
plot(t(1:100), x_pulse(1:100), 'm-', 'LineWidth', 1.5);
grid on;
xlabel('Time (s)'); ylabel('Amplitude (V)');
title('Pulse Train - Time Domain');
xlim([0 0.01]);

% Frequency-domain plotting (log scale)
subplot(4,2,2);
plot(f_vector(1:500), 20*log10(X_sine_mag(1:500)+1e-10), 'b-', 'LineWidth', 1.5);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Sine Wave - Frequency Domain');
xlim([0 5000]); ylim([-80 10]);

subplot(4,2,4);
plot(f_vector(1:500), 20*log10(X_square_mag(1:500)+1e-10), 'r-', 'LineWidth', 1.5);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Square Wave - Frequency Domain');
xlim([0 5000]); ylim([-80 10]);

subplot(4,2,6);
plot(f_vector(1:500), 20*log10(X_triangle_mag(1:500)+1e-10), 'g-', 'LineWidth', 1.5);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Triangle Wave - Frequency Domain');
xlim([0 5000]); ylim([-80 10]);

subplot(4,2,8);
plot(f_vector(1:500), 20*log10(X_pulse_mag(1:500)+1e-10), 'm-', 'LineWidth', 1.5);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Pulse Train - Frequency Domain');
xlim([0 5000]); ylim([-80 10]);

% Quantitative harmonic analysis
fprintf('\n=== Harmonic Analysis Results ===\n\n');

% Find fundamental and harmonic peaks for square wave
[~, idx_fund] = max(X_square_mag(1:N/2));
fund_freq = f_vector(idx_fund);
fund_mag = X_square_mag(idx_fund);

fprintf('Square Wave Analysis:\n');
fprintf('  Fundamental: %.2f Hz, %.4f V (%.2f dB)\n', ...
    fund_freq, fund_mag, 20*log10(fund_mag));

for n = 3:2:9
    [~, idx_harm] = min(abs(f_vector - n*fund_freq));
    harm_mag = X_square_mag(idx_harm);
    harm_ratio_db = 20*log10(harm_mag/fund_mag);
    fprintf('  %dth Harmonic: %.2f Hz, %.4f V (%.2f dBc)\n', ...
        n, f_vector(idx_harm), harm_mag, harm_ratio_db);
end

% Signal-to-noise ratio estimation
noise_floor_idx = round(N/4):round(N/3);  % Mid-frequency region without harmonics
noise_power = mean(X_sine_mag(noise_floor_idx).^2);
signal_power = (A_sine/sqrt(2))^2;
SNR_dB = 10*log10(signal_power/noise_power);
fprintf('\nSine Wave SNR: %.2f dB\n', SNR_dB);

% Total harmonic distortion computation for square wave
fundamental_power = X_square_mag(idx_fund)^2;
harmonic_power = 0;
for n = 3:2:17
    [~, idx_h] = min(abs(f_vector - n*fund_freq));
    harmonic_power = harmonic_power + X_square_mag(idx_h)^2;
end
THD_percent = 100 * sqrt(harmonic_power/fundamental_power);
fprintf('Square Wave THD: %.2f%%\n\n', THD_percent);
```

Execute this script and observe the generated plots showing both time-domain waveforms and frequency-domain spectral content. The sine wave exhibits a single spectral peak at 1 kHz with noise floor below -60 dB. The square wave displays odd harmonics at 3 kHz, 5 kHz, 7 kHz with magnitudes decreasing proportional to harmonic number. The triangle wave shows similar odd-harmonic structure but with steeper -40 dB/decade rolloff due to $1/n^2$ amplitude dependence. The pulse train spectrum contains energy distributed across many harmonics determined by the sinc function envelope $\text{sinc}(f \cdot \tau)$ where $\tau$ represents pulse width.

Modify the sampling frequency parameter to `fs = 2500` and re-execute the script. Observe aliasing artifacts in the frequency-domain plots where harmonics above the new Nyquist frequency of 1250 Hz fold back into the baseband spectrum. The 3 kHz harmonic of the square wave aliases to 2500 - 3000 = -500 Hz, appearing at 500 Hz in the positive frequency spectrum. This empirical demonstration validates the sampling theorem requirement for $f_s > 2f_{max}$.

### Analog Lowpass Filter Construction and Verification

Construct a second-order Sallen-Key Butterworth lowpass filter with cutoff frequency of 1 kHz using a TL072 dual operational amplifier. The Butterworth response provides maximally flat passband response with -40 dB/decade stopband rolloff for this second-order implementation.

Calculate component values starting with capacitor selection. Choose $C_1 = C_2 = 100$ nF (0.1 µF) polypropylene film capacitors for temperature stability. For Butterworth Q of 0.707 and cutoff frequency of 1 kHz, compute resistor values as $R_1 = R_2 = R = 1/(2\pi f_c C)$. Substituting numerical values yields $R = 1/(2\pi \times 1000 \times 100 \times 10^{-9}) = 1591$ Ω. Select the nearest standard 1% resistor value of 1.6 kΩ for both $R_1$ and $R_2$.

Wire the circuit on a solderless breadboard with short lead lengths to minimize parasitic inductance. Connect the ±15V power supply to the TL072 with 100 nF ceramic decoupling capacitors mounted directly between each supply pin and ground. Configure one TL072 amplifier section as a unity-gain voltage follower by connecting the output directly to the inverting input. Connect $R_1$ from the filter input node to the non-inverting input. Connect $C_1$ from the non-inverting input to ground. Connect $R_2$ from the non-inverting input to the operational amplifier output. Connect $C_2$ from the operational amplifier output to ground. The filter output is taken from the operational amplifier output node.

Measure the filter frequency response using the function generator and oscilloscope. Set the generator to produce a 1 kHz sine wave with 1 Vpp amplitude. Connect the generator output to the filter input and oscilloscope channel 1. Connect the filter output to oscilloscope channel 2. Enable the oscilloscope's math function to compute the voltage ratio `CH2/CH1` in decibel scale, displaying the filter's magnitude response directly. Sweep the generator frequency from 10 Hz to 100 kHz in logarithmic steps while recording the magnitude response at each frequency point.

Construct a frequency response table with columns for frequency, input amplitude, output amplitude, and magnitude in decibels. At 100 Hz, the output amplitude should equal the input amplitude within measurement uncertainty, indicating passband flat response. At the cutoff frequency of approximately 1 kHz, measure the output amplitude as 0.707 times the input amplitude, corresponding to -3 dB attenuation. At 10 kHz, one decade above cutoff, measure approximately -40 dB attenuation, confirming the second-order -40 dB/decade rolloff characteristic.

Plot the measured frequency response on semi-logarithmic graph paper or using MATLAB's `semilogx` function. The Butterworth response exhibits smooth monotonic rolloff without passband ripple. Measure the actual cutoff frequency where the response crosses -3 dB by interpolating between adjacent measurement points. Component tolerances typically shift the cutoff frequency by ±5% to ±10% from the calculated value of 1 kHz.

### SPICE Simulation of Analog Filter with Component Tolerance Analysis

Launch LTspice and create a new schematic for the Sallen-Key lowpass filter. Place two resistor symbols from the component menu, labeling them `R1` and `R2` with values of 1.6 kΩ. Place two capacitor symbols labeled `C1` and `C2` with values of 100 nF. Place an LT1013 operational amplifier symbol, representing a precision JFET-input device with characteristics similar to the TL072.

Configure the AC analysis by clicking `Simulate > Edit Simulation Cmd > AC Analysis`. Set the simulation type to decade sweep from 1 Hz to 1 MHz with 100 points per decade. Add voltage source V1 with 1V AC magnitude connected to the filter input. Ground the circuit reference node and connect power supplies of ±15V to the operational amplifier supply pins.

Run the AC analysis and plot the output voltage magnitude in decibels and phase in degrees. Right-click the plot window and select `Add Plot Pane` to create separate magnitude and phase graphs. The magnitude plot confirms -3 dB attenuation at the design cutoff frequency with -40 dB/decade asymptotic rolloff. The phase plot shows 0° phase shift at low frequencies, -90° at the cutoff frequency, and approaches -180° at high frequencies, characteristic of a second-order lowpass response.

Perform Monte Carlo tolerance analysis by adding tolerance specifications to component values. Edit resistor R1 and add the parameter `tol=1%` to enable tolerance variation. Similarly, add `tol=5%` to capacitors C1 and C2. Click `Simulate > Edit Simulation Cmd` and change to `MC` (Monte Carlo) analysis with 100 runs. This generates 100 frequency response curves with randomized component values drawn from uniform distributions within specified tolerances.

Execute the Monte Carlo simulation and observe the spread of frequency responses overlaid on a single plot. The cutoff frequency varies by approximately ±7% across the Monte Carlo runs, computed as the RSS (root-sum-square) combination of resistor and capacitor tolerances: $\sqrt{(1\%)^2 + (1\%)^2 + (5\%)^2 + (5\%)^2} \approx 7.1\%$. This statistical distribution quantifies manufacturing variability impact on filter performance without physical prototype iteration.

Export the Monte Carlo simulation results by clicking on the plot and selecting `File > Export Data as Text`. Save the data as a tab-delimited text file and import into MATLAB or Python for statistical analysis. Compute the mean cutoff frequency, standard deviation, and 3-sigma bounds by processing the exported frequency response curves. This empirical tolerance analysis informs component grading decisions and potential trimming requirements for production filters.

## Exercise 2: Parameter Variation & Empirical Analysis

### Sampling Rate Effects and Aliasing Demonstration

This exercise explores the practical consequences of sampling theorem violations through systematic parameter variation. The practitioner will generate signals at frequencies approaching and exceeding the Nyquist limit while observing aliasing artifacts in both time and frequency domains.

Create a MATLAB script that synthesizes a sine wave at variable frequency while maintaining constant sampling rate. The script implements a frequency sweep from 100 Hz to 10 kHz while sampling at 8 kHz, deliberately crossing the Nyquist frequency of 4 kHz to induce aliasing.

```matlab
% Exercise 2: Sampling Rate Effects and Aliasing Analysis

clear all; close all; clc;

% Fixed sampling parameters
fs = 8000;               % Sampling frequency (Hz)
Ts = 1/fs;               % Sampling period
f_nyquist = fs/2;        % Nyquist frequency (Hz)
duration = 0.5;          % Signal duration (seconds)
t = 0:Ts:duration-Ts;    % Time vector
N = length(t);

% Frequency sweep parameters
f_sweep = [100 500 1000 2000 3000 3500 3900 4100 4500 5000 6000 7000 8000 9000];
n_freqs = length(f_sweep);

% Pre-allocate storage for FFT results
fft_results = zeros(n_freqs, N/2);
f_vector = (0:N/2-1)*(fs/N);

% Generate and analyze signals at each frequency
figure('Position', [50 50 1400 900]);

for idx = 1:n_freqs
    f_signal = f_sweep(idx);
    
    % Generate continuous-time signal (oversampled for visualization)
    fs_continuous = 500000;  % 500 kHz for smooth plotting
    t_continuous = 0:1/fs_continuous:duration-1/fs_continuous;
    x_continuous = sin(2*pi*f_signal*t_continuous);
    
    % Generate sampled signal at fs = 8 kHz
    x_sampled = sin(2*pi*f_signal*t);
    
    % Compute FFT of sampled signal
    X_sampled = fft(x_sampled);
    X_mag = abs(X_sampled(1:N/2))/N;
    fft_results(idx,:) = X_mag;
    
    % Find peak frequency in spectrum
    [peak_mag, peak_idx] = max(X_mag);
    f_measured = f_vector(peak_idx);
    
    % Determine expected alias frequency
    if f_signal <= f_nyquist
        f_expected = f_signal;
        alias_status = 'No Aliasing';
    else
        % Alias frequency for first fold-back
        if f_signal < fs
            f_expected = fs - f_signal;
            alias_status = 'Aliased (1st fold)';
        else
            f_rem = mod(f_signal, fs);
            if f_rem < f_nyquist
                f_expected = f_rem;
            else
                f_expected = fs - f_rem;
            end
            alias_status = 'Aliased (multiple folds)';
        end
    end
    
    % Plot time-domain comparison
    subplot(n_freqs, 2, 2*idx-1);
    plot(t_continuous(1:800), x_continuous(1:800), 'b-', 'LineWidth', 0.5);
    hold on;
    stem(t(1:50), x_sampled(1:50), 'r', 'LineWidth', 1.5, 'MarkerSize', 4);
    hold off;
    grid on;
    xlabel('Time (s)'); ylabel('Amplitude');
    title(sprintf('f = %d Hz - Time Domain', f_signal));
    xlim([0 0.05]);
    
    % Plot frequency-domain spectrum
    subplot(n_freqs, 2, 2*idx);
    stem(f_vector(1:400), X_mag(1:400), 'r', 'LineWidth', 1.5, 'MarkerSize', 4);
    grid on;
    xlabel('Frequency (Hz)'); ylabel('Magnitude');
    title(sprintf('Spectrum: f_{signal} = %d Hz, f_{measured} = %.0f Hz - %s', ...
        f_signal, f_measured, alias_status));
    xlim([0 4000]);
    
    % Print analysis to console
    fprintf('Signal Freq: %5d Hz | Measured: %6.1f Hz | Expected: %6.1f Hz | %s\n', ...
        f_signal, f_measured, f_expected, alias_status);
end

% Spectral waterfall plot showing aliasing across frequency sweep
figure('Position', [100 100 1000 600]);
imagesc(f_vector(1:400), f_sweep, 20*log10(fft_results(:,1:400)+1e-10));
colorbar;
xlabel('Frequency (Hz)'); ylabel('Signal Frequency (Hz)');
title('Aliasing Waterfall: Signal Frequency vs Measured Spectrum');
set(gca, 'YDir', 'normal');
caxis([-60 0]);
hold on;
plot([f_nyquist f_nyquist], [min(f_sweep) max(f_sweep)], 'w--', 'LineWidth', 2);
text(f_nyquist+200, 8000, 'Nyquist Limit', 'Color', 'white', 'FontSize', 12, 'FontWeight', 'bold');
hold off;
```

Execute this script and examine the resulting time-domain and frequency-domain plots. For signal frequencies below the Nyquist limit of 4 kHz, the sampled waveform faithfully represents the continuous signal, with spectral peaks appearing at the correct frequencies. At 3.9 kHz, the signal remains unaliased with a clear spectral peak at 3.9 kHz. When the signal frequency increases to 4.1 kHz, exceeding the Nyquist limit, the measured spectrum shows a peak at 3.9 kHz instead of 4.1 kHz. The alias frequency computed as $f_{alias} = f_s - f_{signal} = 8000 - 4100 = 3900$ Hz matches the observed spectral peak.

As signal frequency continues increasing to 5 kHz, the alias appears at 3 kHz, computed as $8000 - 5000 = 3000$ Hz. At 6 kHz, the alias appears at 2 kHz. This systematic folding demonstrates that frequency components above the Nyquist limit become indistinguishable from lower frequencies, manifesting as spurious low-frequency content that cannot be separated from genuine low-frequency signals through post-acquisition filtering.

The waterfall plot visualization displays the spectral evolution as signal frequency sweeps from 100 Hz to 9 kHz. Below the Nyquist frequency indicated by the white dashed line, the spectral peak tracks linearly with signal frequency. Above the Nyquist limit, the spectral peak folds back, creating a V-shaped boundary where high-frequency signals alias to lower apparent frequencies.

### Anti-Aliasing Filter Design and Empirical Validation

Construct a third-order Butterworth lowpass filter serving as an anti-aliasing filter for an 8 kHz sampling system. The filter cutoff frequency must be set below the Nyquist frequency with sufficient attenuation at frequencies approaching $f_s/2$ to suppress aliasing artifacts while preserving desired signal content.

Select a cutoff frequency of 3 kHz, providing 25% margin below the 4 kHz Nyquist limit. The third-order Butterworth filter provides -60 dB/decade rolloff, achieving approximately -18 dB attenuation at the Nyquist frequency of 4 kHz. This attenuation reduces alias amplitude to 12.6% of the original signal, significantly suppressing aliasing-induced distortion.

Implement the third-order filter by cascading a second-order Sallen-Key section with a first-order RC section. For the second-order stage with cutoff at 3 kHz, choose capacitors $C_1 = C_2 = 47$ nF. Compute resistor values as $R_1 = 1/(2\pi f_c C \times 1.414) = 1/(2\pi \times 3000 \times 47 \times 10^{-9} \times 1.414) = 800$ Ω for Butterworth $Q = 1$ second-order section. Select standard 820 Ω resistors. For the first-order RC section, choose $C_3 = 47$ nF and $R_3 = 1/(2\pi f_c C_3) = 1129$ Ω, selecting a standard 1.1 kΩ resistor.

Construct the two-stage filter on the breadboard with a TL072 dual operational amplifier. Use one amplifier section for the second-order Sallen-Key stage and configure the second amplifier section as a unity-gain buffer driving the first-order RC network. Mount decoupling capacitors at the power supply pins and minimize lead lengths to reduce parasitic effects.

Characterize the anti-aliasing filter frequency response by sweeping the function generator from 100 Hz to 20 kHz while measuring input and output amplitudes. At 3 kHz cutoff, confirm -3 dB attenuation. At 4 kHz Nyquist frequency, measure attenuation between -16 dB and -20 dB depending on component tolerances. At 8 kHz sampling frequency, measure greater than -40 dB attenuation, ensuring that any signal energy at the sampling frequency is sufficiently suppressed.

Integrate the anti-aliasing filter with a sampling system to empirically validate alias suppression. Connect the filter output to an analog-to-digital converter input on the Digilent Analog Discovery 2 or equivalent USB oscilloscope configured for 8 kHz sampling. Generate a 5 kHz test signal at the filter input, exceeding the Nyquist limit. Without the anti-aliasing filter, the sampled spectrum displays a spurious 3 kHz alias peak. With the anti-aliasing filter inserted, the 5 kHz signal is attenuated by approximately 25 dB, reducing the alias amplitude from 1.0V to 0.056V, effectively eliminating the alias artifact from the sampled spectrum.

Repeat the experiment with signal frequencies of 6 kHz, 7 kHz, and 10 kHz, documenting the alias suppression effectiveness. Create a table comparing the unfiltered alias amplitude to the filtered alias amplitude at each test frequency. The anti-aliasing filter provides greater suppression as signal frequency increases due to the cumulative -60 dB/decade rolloff characteristic.

### Convolution and Impulse Response Measurement

Convolution represents the fundamental operation of linear time-invariant systems, where output signals result from input signals convolved with system impulse response. This section develops hands-on proficiency in measuring impulse responses of analog filters and performing discrete convolution operations computationally.

Generate an approximation of an impulse function using the function generator's pulse mode with minimum pulse width setting. Configure a 100 ns pulse width with 1V amplitude and 1 kHz repetition rate. Connect this pulse generator output to the input of the Sallen-Key lowpass filter constructed in Exercise 1. Connect oscilloscope channel 1 to monitor the input pulse and channel 2 to capture the filter output impulse response.

Trigger the oscilloscope on the rising edge of the input pulse with trigger level set to 0.5V. Set the timebase to 200 µs/div to capture the complete impulse response decay. The filter output exhibits a characteristic damped oscillatory response determined by the filter's complex pole locations. Measure the peak response time, overshoot amplitude, and decay time constant using oscilloscope cursors.

For a second-order Butterworth filter with Q = 0.707 and cutoff frequency 1 kHz, the impulse response exhibits minimal overshoot with rapid decay to steady state. Measure the time required for the response to decay to 1% of peak amplitude, typically 3-5 milliseconds for a 1 kHz cutoff filter. This impulse response duration represents the filter's memory length, determining the convolution kernel size required for discrete-time implementation.

Capture the impulse response waveform digitally by saving oscilloscope data to CSV format or by acquiring samples through USB oscilloscope interface. Export the time and voltage vectors to MATLAB or Python for convolution analysis. The following script demonstrates discrete convolution of an arbitrary input signal with the measured filter impulse response.

```matlab
% Exercise 2: Discrete Convolution with Measured Impulse Response

clear all; close all; clc;

% Load measured impulse response from oscilloscope
% If unavailable, synthesize theoretical impulse response
fs_impulse = 100000;  % 100 kHz sampling for impulse response capture
t_impulse = (0:1/fs_impulse:0.01-1/fs_impulse)';  % 10 ms capture window
fc = 1000;  % Filter cutoff frequency (Hz)
zeta = 0.707;  % Butterworth damping ratio (Q = 0.707)
wn = 2*pi*fc;  % Natural frequency (rad/s)
wd = wn*sqrt(1-zeta^2);  % Damped natural frequency

% Theoretical second-order Butterworth impulse response
h_impulse = (wn^2/wd) * exp(-zeta*wn*t_impulse) .* sin(wd*t_impulse);
h_impulse = h_impulse / max(abs(h_impulse));  % Normalize to unity gain

% Generate test input signal: sum of sinusoids
fs_signal = 10000;  % 10 kHz sampling for test signal
t_signal = (0:1/fs_signal:1-1/fs_signal)';
x_signal = 0.5*sin(2*pi*200*t_signal) + ...
           0.3*sin(2*pi*800*t_signal) + ...
           0.2*sin(2*pi*2000*t_signal) + ...
           0.15*sin(2*pi*5000*t_signal);

% Resample impulse response to match signal sampling rate
h_resampled = resample(h_impulse, fs_signal, fs_impulse);
h_resampled = h_resampled / sum(h_resampled);  % Preserve DC gain

% Perform discrete convolution
y_conv = conv(x_signal, h_resampled, 'same');

% Compute FFT for frequency-domain analysis
N_signal = length(t_signal);
X_signal = fft(x_signal);
Y_conv = fft(y_conv);
f_vector = (0:N_signal/2-1)*(fs_signal/N_signal);

X_mag = abs(X_signal(1:N_signal/2))/N_signal;
Y_mag = abs(Y_conv(1:N_signal/2))/N_signal;

% Plotting
figure('Position', [100 100 1200 800]);

subplot(3,2,1);
plot(t_impulse*1000, h_impulse, 'b-', 'LineWidth', 1.5);
grid on;
xlabel('Time (ms)'); ylabel('Amplitude');
title('Measured Filter Impulse Response');

subplot(3,2,2);
plot(f_vector, 20*log10(abs(fft(h_resampled, N_signal))(1:N_signal/2)+1e-10), 'b-', 'LineWidth', 1.5);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('Filter Frequency Response (from impulse response)');
xlim([0 5000]); ylim([-60 10]);

subplot(3,2,3);
plot(t_signal, x_signal, 'r-', 'LineWidth', 1.0);
grid on;
xlabel('Time (s)'); ylabel('Amplitude');
title('Input Signal (Multi-Tone)');
xlim([0 0.05]);

subplot(3,2,4);
stem(f_vector(1:500), X_mag(1:500), 'r', 'LineWidth', 1.5, 'MarkerSize', 4);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude');
title('Input Spectrum');
xlim([0 5000]);

subplot(3,2,5);
plot(t_signal, y_conv, 'g-', 'LineWidth', 1.0);
grid on;
xlabel('Time (s)'); ylabel('Amplitude');
title('Convolved Output Signal');
xlim([0 0.05]);

subplot(3,2,6);
stem(f_vector(1:500), Y_mag(1:500), 'g', 'LineWidth', 1.5, 'MarkerSize', 4);
grid on;
xlabel('Frequency (Hz)'); ylabel('Magnitude');
title('Output Spectrum (After Convolution)');
xlim([0 5000]);

% Quantitative analysis
fprintf('\n=== Convolution Analysis Results ===\n\n');
fprintf('Input Signal Components:\n');
freqs_input = [200 800 2000 5000];
for f_test = freqs_input
    [~, idx] = min(abs(f_vector - f_test));
    mag_in = X_mag(idx);
    mag_out = Y_mag(idx);
    attenuation_db = 20*log10(mag_out/mag_in);
    fprintf('  %5d Hz: Input = %.4f V, Output = %.4f V, Attenuation = %.2f dB\n', ...
        f_test, mag_in, mag_out, attenuation_db);
end

% Verify convolution theorem: conv in time = multiplication in frequency
H_fft = fft(h_resampled, N_signal);
Y_freq_domain = X_signal .* H_fft;
y_freq_method = real(ifft(Y_freq_domain));
error_rms = sqrt(mean((y_conv - y_freq_method).^2));
fprintf('\nConvolution Theorem Verification:\n');
fprintf('  RMS error between time-domain conv and freq-domain mult: %.6f\n', error_rms);
```

Execute this convolution script and analyze the results. The input spectrum displays peaks at 200 Hz, 800 Hz, 2000 Hz, and 5000 Hz with decreasing amplitudes. After convolution with the 1 kHz lowpass filter impulse response, the output spectrum shows that 200 Hz and 800 Hz components pass with minimal attenuation (less than 1 dB), the 2000 Hz component is attenuated by approximately 12 dB, and the 5000 Hz component is suppressed by more than 30 dB.

The convolution theorem verification confirms that convolving in the time domain produces identical results to multiplying in the frequency domain, with RMS error on the order of $10^{-10}$ arising only from floating-point numerical precision. This equivalence provides the mathematical foundation for efficient filter implementation using FFT-based frequency-domain processing for long convolution kernels.

Measure convolution execution time for varying input signal lengths and impulse response lengths. Create a parameter sweep where input length varies from 100 to 10000 samples while impulse response length varies from 10 to 1000 samples. For each combination, execute both time-domain convolution using MATLAB's `conv` function and frequency-domain multiplication using `fft`, `ifft`, and element-wise multiplication. Record execution times using `tic` and `toc` commands.

Plot execution time versus input length on log-log axes for both methods. Time-domain convolution exhibits $O(N \cdot M)$ complexity where $N$ represents input length and $M$ represents impulse response length, producing a linear relationship on log-log plots. Frequency-domain multiplication exhibits $O(N \log N)$ complexity due to FFT operations, resulting in a logarithmic slope. For impulse response lengths exceeding approximately 100 samples, frequency-domain processing provides computational advantages despite FFT overhead.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Nonlinear Distortion Analysis and Harmonic Generation

Linear time-invariant system models assume signal amplitudes remain within the device's linear operating region. Real operational amplifiers and analog circuits exhibit nonlinear behavior when output voltages approach supply rail limits, input common-mode range is exceeded, or slew rate limitations cause distortion on large, fast transients. This exercise characterizes nonlinear distortion through total harmonic distortion measurement and intermodulation product analysis.

Configure the Sallen-Key lowpass filter with input signal amplitude systematically increased from 100 mVpp to 10 Vpp while monitoring output waveform fidelity. Set the function generator to produce a 1 kHz sine wave at each amplitude level. Connect oscilloscope channel 1 to monitor filter input and channel 2 to capture filter output. Activate the oscilloscope's FFT function to display output harmonic content.

At low input amplitudes below 1 Vpp, the output waveform replicates the input with minimal distortion. The FFT display shows a single spectral peak at the fundamental frequency with harmonic content below -60 dBc (dB relative to carrier). As input amplitude increases to 5 Vpp, observe the appearance of third-harmonic distortion at 3 kHz in the FFT display. The third harmonic arises from cubic nonlinearity terms in the operational amplifier transfer function, with amplitude proportional to the cube of input amplitude.

Further increasing input amplitude to 8 Vpp with ±15V supply rails causes output clipping when the operational amplifier output stage saturates near ±13V. Observe severe waveform distortion in the time domain as the sine wave peaks flatten symmetrically. The FFT display reveals substantial odd-harmonic content at 3 kHz, 5 kHz, 7 kHz characteristic of hard clipping, with third-harmonic amplitude reaching -20 dBc or higher.

Quantify total harmonic distortion by measuring the RMS amplitude of all harmonics relative to the fundamental. Use the oscilloscope's built-in THD measurement function if available, or manually compute THD from FFT peak amplitudes. Record THD percentage as a function of input amplitude, observing exponential increase as output approaches clipping. For output amplitudes remaining within ±10V for ±15V supplies, THD typically remains below 0.1%. At output amplitudes exceeding ±12V, THD rapidly increases beyond 1%, then exceeds 10% as hard clipping occurs.

Implement a two-tone intermodulation distortion test by generating two closely spaced sine waves at 900 Hz and 1100 Hz with equal amplitudes. Sum these signals using a resistive combiner network with three 10 kΩ resistors configured as a summing node. Connect the combined signal to the filter input and capture the output spectrum. Third-order intermodulation products appear at $2f_1 - f_2 = 1700$ Hz and $2f_2 - f_1 = 1300$ Hz due to cubic nonlinearity terms mixing the two fundamental frequencies.

Measure the amplitude of intermodulation products relative to the fundamental tones, computing the third-order intercept point (IP3). The IP3 characterizes the input power level at which intermodulation product power would theoretically equal fundamental power, extrapolated from measurements at lower input levels. For TL072 operational amplifiers at 1 kHz with ±15V supplies, output-referred IP3 typically exceeds +20 dBm (10 Vpp into 50 Ω), sufficient for most analog signal processing applications.

Characterize slew rate limitations by applying a large-amplitude square wave at the filter input. Set the function generator to 10 kHz square wave with 10 Vpp amplitude. Observe the filter output waveform, which should ideally exhibit smooth exponential transitions determined by the filter time constant. When operational amplifier slew rate limits are exceeded, output transitions become linear ramps with slope equal to the slew rate specification.

Measure the output voltage transition time from 10% to 90% of full amplitude using oscilloscope cursors. Compare the measured rise time against the theoretical filter response calculated from $t_r \approx 0.35/f_c$, which yields 0.35 ms for a 1 kHz cutoff filter. If measured rise time significantly exceeds theoretical values, slew rate limiting is occurring. For TL072 with 13 V/µs slew rate, full ±10V output swing requires minimum transition time of 1.54 µs, limiting full-power bandwidth to approximately 65 kHz for 10 Vpp signals.

### Dynamic Range and Noise Floor Characterization

Dynamic range quantifies the ratio between maximum undistorted signal level and minimum detectable signal level above the noise floor. This fundamental performance metric governs the smallest resolvable signal amplitudes and determines requirements for input signal conditioning and gain distribution.

Measure the filter noise floor by terminating the input with a 50 Ω resistor to ground, eliminating external signal sources. Connect the filter output to the oscilloscope with maximum vertical sensitivity setting of 1-2 mV/div. Set the oscilloscope bandwidth limit to 20 MHz to reduce high-frequency noise. Capture the noise waveform over a 100 ms time span and compute RMS noise voltage using the oscilloscope's measurement function.

The observed noise combines operational amplifier voltage noise, current noise interacting with source impedance, resistor thermal noise, and oscilloscope measurement noise. For TL072 operational amplifiers, input-referred voltage noise spectral density is approximately 18 nV/√Hz. Integrating over the filter bandwidth of 1 kHz yields RMS input noise of $e_{n,rms} = 18 \text{ nV/√Hz} \times \sqrt{1000 \text{ Hz}} = 570 \text{ nV}$.

Resistor thermal noise contributes additional noise proportional to resistance value and temperature. The thermal noise voltage of a resistor is given by $e_{n,R} = \sqrt{4kTRB}$ where $k = 1.38 \times 10^{-23}$ J/K represents Boltzmann's constant, $T = 300$ K represents absolute temperature, $R$ represents resistance, and $B$ represents bandwidth. For the 1.6 kΩ resistors in the filter with 1 kHz bandwidth, thermal noise is $e_{n,R} = \sqrt{4 \times 1.38 \times 10^{-23} \times 300 \times 1600 \times 1000} = 5.1 \text{ µV}$.

Sum noise contributions as RSS to compute total output-referred noise: $e_{n,total} = \sqrt{e_{n,amp}^2 + e_{n,R1}^2 + e_{n,R2}^2}$. This calculation typically yields total RMS noise between 5-10 µV for the Sallen-Key filter topology. Measure the actual noise voltage with the oscilloscope and compare to calculated values, accounting for oscilloscope input noise specification of 1-2 µV RMS.

Compute dynamic range as the ratio of maximum undistorted output voltage to RMS noise voltage. With ±15V supplies, maximum undistorted output reaches approximately ±10V (20 Vpp or 7.07 Vrms) before THD exceeds 1%. Dynamic range is $DR = 20\log_{10}(7.07 \text{ Vrms} / 7 \text{ µVrms}) = 120 \text{ dB}$. This substantial dynamic range enables processing of signals spanning six orders of magnitude in amplitude.

Validate dynamic range measurement by injecting progressively smaller sine wave signals at the filter input. Start with 1 Vpp amplitude and reduce by factors of 10 to 100 mVpp, 10 mVpp, 1 mVpp, and 100 µVpp. At each level, measure the output signal amplitude and observe SNR degradation as signal approaches noise floor. When signal amplitude equals RMS noise, SNR equals 0 dB and signal becomes barely distinguishable from noise fluctuations.

Capture oscilloscope screenshots showing time-domain waveforms at each signal level, documenting the transition from clean sinusoids at high amplitude to noise-dominated traces at low amplitude. Use oscilloscope averaging to improve SNR at low signal levels, accumulating 128 or 256 acquisitions to reduce random noise by $\sqrt{N}$ where $N$ represents the number of averages.

### Filter Instability, Oscillation Detection, and Stability Restoration

Improper operational amplifier selection, inadequate phase margin, or parasitic capacitance can cause active filter circuits to oscillate spontaneously, generating sustained sinusoidal or square wave outputs without input excitation. This section develops diagnostic skills for identifying instability mechanisms and implementing corrective measures.

Deliberately induce filter oscillation by adding excessive stray capacitance. Connect a 100 pF capacitor in parallel with the operational amplifier's feedback resistor R2 in the Sallen-Key filter. This additional capacitance creates a parasitic pole at high frequency, reducing phase margin and potentially triggering oscillation.

Power the modified filter with ±15V supplies and observe the output on the oscilloscope with no input signal applied. If oscillation occurs, the output displays a continuous sine wave with frequency typically in the megahertz range determined by the operational amplifier's gain-bandwidth product and parasitic elements. Measure the oscillation frequency and amplitude, noting whether oscillation is sinusoidal or contains harmonic distortion indicating nonlinear limiting.

Analyze oscillation conditions using the Barkhausen stability criterion, which states that oscillation occurs when loop gain magnitude equals unity and loop phase shift equals 180° (or equivalently 0° for negative feedback systems). Identify the frequency where these conditions are met by considering the operational amplifier's open-loop gain rolloff and phase shift combined with feedback network characteristics.

Eliminate oscillation through compensation techniques. First, remove the deliberately added 100 pF capacitor to restore nominal circuit topology. If oscillation persists due to layout parasitics or operational amplifier marginal stability, add a small compensation capacitor (5-10 pF) in parallel with the feedback resistor to intentionally reduce high-frequency gain and restore phase margin. Incrementally increase compensation capacitance while monitoring output for oscillation suppression.

Alternatively, add a series isolation resistor of 50-100 Ω between the operational amplifier output and the feedback network to decouple capacitive loading. This resistor interacts with parasitic capacitance to create a local dominant pole, stabilizing the feedback loop. Verify oscillation elimination by monitoring the output with no input signal and confirming DC voltage near ground potential with only low-level noise.

Test filter stability margins by applying a small square wave input and observing output for ringing or overshoot. A stable, well-damped filter exhibits smooth monotonic transitions with less than 5% overshoot. Excessive ringing with multiple oscillatory cycles indicates marginal stability. Adjust compensation capacitance to achieve critically damped or slightly overdamped response.

Perform stability analysis in LTspice by running AC analysis with the modified filter schematic. Plot the loop gain magnitude and phase by breaking the feedback loop at the operational amplifier output. Insert an AC voltage source in the feedback path and plot the ratio of voltages across the break point. Phase margin is computed as the phase difference from 180° at the frequency where loop gain magnitude crosses 0 dB. Phase margin exceeding 45° ensures adequate stability with tolerance for component variations.

Explore the relationship between operational amplifier gain-bandwidth product and maximum achievable filter cutoff frequency. Replace the TL072 with a higher-speed amplifier such as LT1818 with 400 MHz GBW. Increase the filter cutoff frequency by proportionally decreasing resistor values while maintaining fixed capacitance. Observe that higher-speed amplifiers enable higher cutoff frequencies before instability occurs, following the rule-of-thumb that operational amplifier GBW should exceed filter cutoff frequency by a factor of 50-100 for stable operation.

### Temperature Coefficient Effects and Environmental Stress Testing

Component parameter variations with temperature alter filter characteristics, shifting cutoff frequency and modifying gain accuracy. This section quantifies temperature sensitivity and develops compensation strategies for precision applications.

Characterize the Sallen-Key filter's temperature coefficient by measuring frequency response at room temperature (25°C), elevated temperature (55°C), and reduced temperature (0°C). Use a temperature-controlled oven or cold spray to achieve desired operating temperatures. Allow the circuit to thermally stabilize for 15 minutes at each temperature before measurement.

Mount a thermocouple or digital temperature sensor directly on the operational amplifier package to verify device temperature. Measure the filter cutoff frequency at each temperature point using the swept sine wave technique described in Exercise 1. Record cutoff frequency shift in Hertz and compute temperature coefficient in parts-per-million per degree Celsius (ppm/°C) using $TC = (1/f_0) (df/dT) \times 10^6$ where $f_0$ represents nominal cutoff frequency at 25°C and $df/dT$ represents frequency change per degree.

For filters constructed with standard carbon-film resistors (±100 ppm/°C) and ceramic capacitors (X7R dielectric with ±1500 ppm/°C), total frequency temperature coefficient typically reaches ±1600 ppm/°C, producing cutoff frequency shift of ±5% over 0-55°C industrial temperature range. Upgrade to metal-film resistors with ±25 ppm/°C and C0G/NP0 ceramic capacitors with ±30 ppm/°C to achieve ±40 ppm/°C frequency stability, reducing frequency shift to ±0.14% over temperature.

Document temperature effects by plotting cutoff frequency versus temperature and computing linear regression slope. The resulting temperature coefficient guides component selection for applications with stringent thermal stability requirements such as precision data acquisition, audio processing, and instrumentation systems.

Implement passive temperature compensation by selecting resistors and capacitors with opposing temperature coefficients. Polypropylene capacitors exhibit negative temperature coefficient of approximately -200 ppm/°C, partially offsetting positive resistor temperature coefficient to reduce net frequency drift. Precision filter designs exploit this compensation by balancing temperature coefficients during component selection.

Test power supply rejection by varying supply voltage while monitoring filter characteristics. Nominal ±15V supplies are varied to ±12V and ±18V while measuring cutoff frequency and passband gain. Operational amplifier common-mode rejection ratio (CMRR) and power supply rejection ratio (PSRR) determine sensitivity to supply variations. TL072 specification shows PSRR of 80 dB, meaning 1V supply change produces approximately 100 µV output variation at DC.

## Operational Reference Guide & Diagnostic Checklist

### Systematic Troubleshooting Decision Tree

Signal processing circuit failures manifest through distinct observable symptoms that guide diagnostic procedures. Absence of output signal despite input excitation suggests power supply failure, incorrect component values, or operational amplifier damage. Distorted output waveforms indicate clipping, slew rate limiting, or nonlinear operation. Unexpected frequency response indicates incorrect component values or parasitic effects. Oscillation or instability points to inadequate phase margin or positive feedback mechanisms.

Begin troubleshooting by verifying power supply voltages at the operational amplifier pins. Measure DC voltage between V+ pin and ground, expecting +15V ±0.5V. Measure DC voltage between V- pin and ground, expecting -15V ±0.5V. Measure voltage between V+ and V- pins, expecting 30V total. Absence of correct supply voltages indicates power supply failure, wiring errors, or open circuit conditions.

Verify operational amplifier functionality by temporarily disconnecting the filter circuit and configuring the operational amplifier as a unity-gain buffer. Connect the non-inverting input to a 1V DC source and ground the inverting input through a 10 kΩ resistor. Measure output voltage, expecting 1V indicating proper operation. If output remains at ground or supply rail, the operational amplifier is damaged and requires replacement.

Check passive component values using a digital multimeter with the circuit unpowered. Measure resistor values in-circuit, accounting for parallel resistance from other components. Verify capacitor values using a capacitance meter or LCR meter, noting that in-circuit measurement may show incorrect values due to parallel elements. Compare measured values against design values, identifying component placement errors or incorrect values.

Probe signal paths with the oscilloscope to identify where signal processing failures occur. Starting at the input, verify that the input signal reaches the first filter stage with expected amplitude and frequency. Progress through each filter stage, confirming signal presence and expected attenuation or amplification. Loss of signal at a specific node indicates failure of the preceding stage.

### Oscilloscope Configuration for Signal Processing Measurements

Proper oscilloscope setup ensures accurate waveform capture without measurement artifacts. Select AC coupling for signals without DC components, removing DC offsets that reduce usable display range. Select DC coupling when DC offset information is required or for very low frequency signals below 1 Hz where AC coupling attenuation becomes significant.

Set vertical scale to display waveform amplitude occupying 60-80% of the display height, maximizing quantization resolution without clipping. For 2 Vpp signals, select 500 mV/div providing 4V full-scale display on eight vertical divisions. Set timebase to display three to five complete cycles for periodic signals, enabling observation of waveform shape and period measurement.

Configure trigger level at the signal's mean value with rising or falling edge triggering. For sine waves, set trigger level to zero crossing for stable triggering. For pulse signals, set trigger level to 50% of amplitude. Adjust trigger holdoff to prevent false triggering on complex waveforms with multiple edges per cycle.

Enable bandwidth limiting to 20 MHz when measuring low-frequency signals below 100 kHz to reduce high-frequency noise pickup and prevent aliasing in the oscilloscope's ADC. Disable bandwidth limiting for wideband signals to preserve fast rise times and high-frequency content.

Utilize oscilloscope cursors for precise measurements of voltage amplitude, time intervals, rise times, and frequency. Horizontal cursors measure voltage levels; vertical cursors measure time intervals. Cursor readouts typically provide resolution of 0.1% of full scale, superior to automated measurements for specific parameter extraction.

Activate FFT display for frequency-domain analysis with appropriate window selection. Rectangular window provides best frequency resolution for continuous wave signals. Hanning window reduces spectral leakage for signals not synchronized with FFT length. Blackman-Harris window provides maximum stopband attenuation for detecting weak spectral components near strong signals.

### MATLAB Signal Processing Toolbox Essential Functions

The following functions provide core signal processing operations for laboratory analysis and filter design. Execute `help functionname` in the MATLAB command window for detailed syntax and options.

The `fft` function computes discrete Fourier transform using fast Fourier transform algorithms with $O(N \log N)$ complexity. Syntax: `X = fft(x)` where `x` represents time-domain vector and `X` represents complex frequency-domain vector. For real-valued input signals, use `X = fft(x); X_onesided = X(1:N/2)` to extract the single-sided spectrum eliminating redundant negative frequencies.

The `filter` function implements discrete-time filtering via difference equation. Syntax: `y = filter(b, a, x)` where `b` represents numerator coefficients, `a` represents denominator coefficients, and `x` represents input signal. For FIR filters, set `a = 1`. For IIR filters, provide both numerator and denominator coefficient vectors.

The `butter` function designs Butterworth filter coefficients. Syntax: `[b, a] = butter(N, Wn, 'filtertype')` where `N` represents filter order, `Wn` represents normalized cutoff frequency (0 to 1, where 1 corresponds to Nyquist frequency), and `filtertype` specifies `'low'`, `'high'`, `'bandpass'`, or `'stop'`. For lowpass filter with 1 kHz cutoff at 10 kHz sampling rate: `[b, a] = butter(4, 0.2, 'low')` creates fourth-order Butterworth lowpass.

The `freqz` function computes frequency response from filter coefficients. Syntax: `[H, f] = freqz(b, a, N, fs)` where `H` represents complex frequency response, `f` represents frequency vector, `N` represents number of frequency points, and `fs` represents sampling frequency. Plot magnitude response in decibels using `plot(f, 20*log10(abs(H)))`.

The `conv` function performs discrete convolution. Syntax: `y = conv(x, h, 'option')` where `x` represents input signal, `h` represents impulse response, and `'option'` specifies output length: `'full'` returns length $N + M - 1$, `'same'` returns length $N$ matching input, `'valid'` returns length $N - M + 1$ with no edge artifacts.

The `resample` function performs sampling rate conversion. Syntax: `y = resample(x, P, Q)` resamples signal `x` at $P/Q$ times the original rate, where `P` and `Q` are integers. This function applies anti-aliasing lowpass filtering during decimation and interpolation filtering during upsampling to prevent aliasing artifacts.

### Component Selection Guidelines for Precision Analog Filters

Resistor selection prioritizes stability, noise, and tolerance. Metal-film resistors with ±1% tolerance and ±50 ppm/°C temperature coefficient provide adequate performance for most applications. Thin-film resistors with ±0.1% tolerance and ±25 ppm/°C temperature coefficient suit precision filters. Avoid carbon composition resistors which exhibit poor temperature stability and excess noise. Select resistor power rating at least double the expected dissipation to ensure reliability.

Capacitor selection depends on dielectric properties. C0G/NP0 ceramic capacitors offer ±30 ppm/°C stability and negligible voltage coefficient for precision applications but are limited to values below 1 µF. X7R ceramic capacitors provide higher capacitance density but suffer ±15% capacitance variation over temperature. Polypropylene film capacitors deliver excellent stability with ±100 ppm/°C temperature coefficient and negligible voltage coefficient, ideal for audio and precision analog filters.

Operational amplifier selection balances gain-bandwidth product, slew rate, input noise, and supply voltage requirements. For filters with cutoff frequencies below 10 kHz, general-purpose amplifiers like TL072 (3 MHz GBW, 13 V/µs slew rate) or LM358 (1 MHz GBW, 0.6 V/µs slew rate) suffice. For cutoff frequencies from 10 kHz to 1 MHz, select high-speed amplifiers such as LT1818 (400 MHz GBW, 2500 V/µs slew rate) or AD8066 (65 MHz GBW, 180 V/µs slew rate).

Input noise specification determines minimum signal levels. Voltage noise spectral density ranges from 4 nV/√Hz for precision low-noise amplifiers to 20 nV/√Hz for general-purpose devices. For low source impedance applications below 1 kΩ, voltage noise dominates; select amplifiers with minimum voltage noise density. For high source impedance above 10 kΩ, current noise interacting with source resistance becomes significant; select JFET-input amplifiers with current noise below 1 pA/√Hz.

### Common Failure Modes and Recovery Procedures

Oscillation at high frequency (1-100 MHz) indicates insufficient phase margin or capacitive loading. Add 10-20 pF compensation capacitor across feedback resistor. Increase series output resistance to 50-100 Ω to isolate capacitive loads. Verify power supply decoupling with 100 nF ceramic capacitors mounted directly at operational amplifier pins. Check for ground loops causing positive feedback through supply rails.

Distortion and clipping result from insufficient supply voltage headroom or slew rate limitations. Increase supply voltage to ±15V or higher if operational amplifier ratings permit. Reduce signal amplitude to maintain output swing within ±2V of supply rails. Select operational amplifier with higher slew rate specification if large, fast transients cause distortion. Verify bias current compensation for high source impedance to prevent DC offset clipping.

Excessive noise manifests as high-frequency fuzz on output waveforms or elevated noise floor in FFT displays. Verify proper grounding with single-point ground topology. Add ferrite beads on supply rails to suppress high-frequency noise injection. Shield sensitive analog nodes with grounded enclosures. Increase filter cutoff frequency or add post-filter lowpass stage to limit noise bandwidth.

Incorrect frequency response indicates component value errors, parasitic effects, or loading. Verify resistor and capacitor values with precision meter. Check for parallel PCB trace capacitance or solder pad capacitance adding to design values. Measure filter performance with high-impedance oscilloscope probe (10 MΩ input impedance) to prevent loading. Add buffer amplifier if subsequent stages load filter output.

Component thermal damage from overcurrent or overvoltage appears as charred resistors, cracked capacitors, or destroyed operational amplifiers. Verify supply voltage polarity and magnitude before applying power. Add current-limiting resistors in series with inputs to prevent excessive current from signal sources. Include transient suppression with clamping diodes or transorbs on input and output nodes for circuits exposed to electrostatic discharge or inductive transients.

This comprehensive laboratory sequence has developed operational proficiency in signal processing from fundamental time-domain and frequency-domain concepts through analog filter implementation, digital signal processing algorithms, and systematic troubleshooting methodologies. The practitioner now commands the measurement techniques, computational tools, and circuit design skills required for professional signal processing applications across telecommunications, instrumentation, audio, and data acquisition domains.
