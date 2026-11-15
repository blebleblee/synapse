# Operational Verification Labs: Software Defined Radio

## Objective & Operational Lab Setup

Software-defined radio represents a fundamental paradigm shift in radio frequency engineering, transforming signal processing operations traditionally executed in analog circuitry into digital domain computation. This operational verification laboratory sequence grounds the practitioner in empirical validation of SDR architectures through systematic measurement, parameter sweeping, and failure mode analysis. The exercises progress from foundational I/Q signal generation and observation through multi-stage receiver chain characterization, culminating in boundary condition stress testing that exposes aliasing artifacts, quantization noise floors, and dynamic range limitations inherent to discrete-time sampling systems.

The laboratory environment requires a hardware SDR transceiver capable of operating across HF through UHF spectrum allocations, GNU Radio Companion for flowgraph construction and real-time signal visualization, and Python with NumPy/SciPy for offline batch processing of captured I/Q datasets. The RTL-SDR dongle provides an economical entry point with 24 MHz to 1766 MHz coverage and 8-bit ADC resolution, though professional-grade HackRF One or BladeRF devices enable full-duplex operation and superior dynamic range for advanced exercises. Critical supporting instrumentation includes a calibrated signal generator for injection of known test waveforms, a spectrum analyzer for independent frequency domain validation, and precision 50-ohm terminators to eliminate impedance mismatch reflections that corrupt small-signal measurements.

Begin by installing GNU Radio 3.10 or later through your distribution's package manager, ensuring the gr-osmosdr source block is available for hardware interfacing. On Ubuntu 22.04 LTS, execute `sudo apt install gnuradio gr-osmosdr rtl-sdr` to pull the complete toolchain with RTL-SDR driver stack. Verify the installation by launching GNU Radio Companion with `gnuradio-companion` and confirming the RTL-SDR Source block appears in the Sources category. Connect your SDR hardware via USB 3.0 for adequate bandwidth, then validate device enumeration with `rtl_test -t` which performs a basic tuner connection sweep. The output should enumerate detected RTL2832U devices with associated USB bus addresses and report zero dropped samples during the brief test sequence.

Physical RF chain setup demands attention to grounding and shielding discipline. Connect the SDR antenna input through a 10 dB attenuator to prevent frontend overload from strong local broadcast transmitters. A makeshift attenuator can be constructed using three resistors in a Pi configuration: 150 ohms in series with the input, 68 ohms to ground at input, and 68 ohms to ground at output, all using half-watt carbon film resistors with short lead lengths to minimize parasitic inductance above 100 MHz. For controlled signal injection exercises, route the signal generator output through a coaxial splitter feeding both the SDR input and spectrum analyzer input, establishing parallel observation channels that enable immediate correlation between time-domain I/Q samples and frequency-domain spectral content.

Calibrate the SDR frequency error by tuning to a known precision reference such as WWV at 10.000 MHz or a local FM broadcast station with published carrier frequency. The RTL-SDR oscillator typically exhibits 50 to 100 ppm frequency error from nominal due to crystal tolerance and temperature drift. In GNU Radio, apply this correction through the `freq_corr` parameter in the RTL-SDR Source block, entering the measured offset in parts per million. For example, if you observe a known 162.550 MHz NOAA Weather Radio carrier appearing at 162.565 MHz in the FFT display, the error calculates to `(162565000 - 162550000) / 162550000 * 1e6 = 92.3 ppm`. Enter `-92` in the frequency correction field to shift the local oscillator in the compensating direction, then re-verify alignment of the received carrier with its published frequency.

All captured I/Q data in these laboratories will be stored in the complex64 format, where each sample consists of a 32-bit float in-phase component followed by a 32-bit float quadrature component. This file format enables direct memory-mapping in Python through NumPy's `fromfile` method with `dtype=np.complex64`, providing zero-copy access to multi-megabyte capture buffers. Establish a standardized directory structure with `~/sdr_lab/captures/` for raw I/Q files, `~/sdr_lab/flowgraphs/` for GNU Radio `.grc` files, and `~/sdr_lab/analysis/` for Python post-processing scripts. Each capture file should embed acquisition parameters in its filename following the convention `YYYYMMDD_HHMMSS_fcenter_fsample_description.cf64`, where `fcenter` specifies the tuned center frequency in Hz and `fsample` specifies the sample rate in Hz.

## Exercise 1: Foundational Practical Implementation

This foundational exercise constructs a complete narrowband FM receiver chain in GNU Radio, exercising every fundamental block in the SDR signal processing pipeline from antenna-coupled RF input through demodulated audio output. The workflow establishes empirical understanding of sample rate relationships, filter design parameters, and I/Q complex signal transformations through systematic observation of intermediate waveforms at each processing stage. By instrumenting the flowgraph with time-domain oscilloscope sinks and frequency-domain FFT displays, you will develop intuition for how quadrature sampling captures full spectral information, how decimation reduces computational load while preserving signal bandwidth, and how the FM discriminator extracts angle-modulated intelligence from the complex envelope.

Launch GNU Radio Companion and create a new flowgraph. The first block to place is the Options block, which appears automatically and governs global parameters. Set the ID field to `nbfm_receiver`, the Title to `Narrowband FM Receiver with Instrumentation`, and the Generate Options to `QT GUI` to enable the Qt-based graphical interface with real-time plot widgets. In the Variables section, create a `samp_rate` variable with value `2.4e6`, establishing the 2.4 MHz sample rate that represents the maximum stable rate for RTL-SDR dongles without dropping samples on most USB 2.0 host controllers. Create a second variable `center_freq` with value `162.55e6` to tune the receiver to NOAA Weather Radio, and a third variable `channel_width` with value `12.5e3` representing the 12.5 kHz occupied bandwidth of narrowband FM voice channels.

Add an RTL-SDR Source block from the Sources category and configure its parameters. Set the Sample Rate to `samp_rate`, the Ch0 Frequency to `center_freq`, the RF Gain to 30 dB as a starting point for sensitivity versus overload tradeoff, and the IF Gain to 20 dB. The Frequency Correction field should contain the calibrated PPM offset determined during setup. Leave the Gain Mode set to Manual to maintain consistent signal levels across multiple runs. The output of this block produces a complex64 stream representing the I/Q sample pairs at 2.4 megasamples per second, with the tuned center frequency appearing at DC (zero Hz) in the complex baseband representation.

Before applying any processing, insert a QT GUI Frequency Sink block connected directly to the RTL-SDR Source output. This spectrum analyzer display reveals the raw RF environment surrounding your tuned center frequency. Configure the FFT size to 4096 points, providing frequency resolution of `samp_rate / 4096 = 586 Hz` per bin. Set the Center Frequency field to `center_freq` so the horizontal axis displays absolute frequencies rather than baseband offsets. Set the Bandwidth field to `samp_rate`. In the Config tab, enable the Average checkbox with Alpha set to 0.1 to smooth temporal fluctuations in the noise floor. Enable the Max Hold checkbox to capture transient peaks. Run the flowgraph and observe the spectrum. You should see the narrowband FM signal as a distinct peak rising 20 to 40 dB above the surrounding noise floor, with spectral width on the order of 10 to 15 kHz accounting for deviation and modulation bandwidth.

The next stage implements frequency translation to shift the desired signal from its arbitrary position within the 2.4 MHz capture bandwidth to exactly DC, centering it for subsequent filtering. Add a Frequency Xlating FIR Filter block, which combines a multiply-by-complex-exponential frequency shift with a low-pass filter in a computationally efficient polyphase implementation. Set the Decimation factor to 10, reducing the sample rate from 2.4 MHz down to 240 kHz, adequate for capturing the 12.5 kHz channel with margin for filter transition bands. Set the Center Frequency to `channel_freq - center_freq` where `channel_freq` is a new variable containing the precise carrier frequency of your target signal. For NOAA Weather Radio at 162.550 MHz, if you tuned your SDR to 162.55 MHz, the offset is zero. If you instead tuned to 162.5 MHz for wider observation bandwidth, the offset becomes 50 kHz.

The Taps parameter requires a low-pass filter prototype that defines the frequency response and transition band steepness. Use the `firdes.low_pass()` convenience function with arguments `(1, samp_rate, channel_width, channel_width*0.2, window.WIN_HAMMING)`. This generates a unity-gain filter with cutoff at 12.5 kHz and transition band of 2.5 kHz, windowed with the Hamming function to achieve stopband attenuation exceeding 50 dB. The filter automatically scales its number of taps to meet the specified transition width given the input sample rate. At 2.4 MHz input rate with 2.5 kHz transition band, the design calculates approximately 120 taps, resulting in group delay of 60 samples or 25 microseconds.

Insert a second QT GUI Frequency Sink after the Frequency Xlating FIR Filter to observe the isolated channel. Set its Sample Rate parameter to `samp_rate/10` reflecting the decimated rate, and its FFT Size to 2048. The display should now show the narrowband FM signal centered at DC with all other spectrum content suppressed below the noise floor. The characteristic shape of an FM signal appears as a rounded rectangular envelope extending approximately ±6 kHz from center at full modulation. Add a QT GUI Time Sink connected to the same point, configured for Complex input type with 1024 samples displayed. This constellation diagram shows the I and Q components as orthogonal axes. An FM signal produces a cloud of points distributed around a circle, with the radius representing carrier amplitude and the angular velocity representing instantaneous frequency deviation.

Demodulation of the frequency-modulated signal requires extracting the derivative of the complex phase angle. Add a Quadrature Demod block, which computes the angle difference between consecutive complex samples and scales the result by a gain factor. The gain parameter converts radians per sample into units appropriate for audio. Set the Gain parameter to `(samp_rate/10)/(2*math.pi*fdev)` where `fdev` is a new variable set to `5e3`, representing the 5 kHz peak deviation standard for narrowband FM voice. This normalization ensures that maximum deviation produces sample values near ±1.0, matching the expected range for subsequent audio processing. The mathematical derivation stems from the fact that a frequency offset of Δf Hz produces a phase increment of `2π(Δf/fs)` radians per sample, where fs is the sample rate. The quadrature demodulator outputs this phase increment, so dividing by `2π` and multiplying by `fs` recovers the frequency offset Δf.

The demodulated signal resides at 240 kHz sample rate, far exceeding the Nyquist requirement for audio bandwidth limited to 3 kHz. Add a Low Pass Filter block with Decimation set to 5, reducing the rate to 48 kHz which aligns with standard audio hardware. Set the Cutoff Freq to 3 kHz and Transition Width to 500 Hz, using `firdes.low_pass()` with `window.WIN_HAMMING`. Set the Sample Rate parameter to `samp_rate/10` reflecting the input rate to this block. The output sample rate becomes 48 kHz, and the filter simultaneously removes demodulation artifacts above the audio band including quantization noise shaped by the discriminator's differentiation operation.

Finally, add an Audio Sink block configured for 48 kHz sample rate with Device Name left blank to use the system default output. Connect the Low Pass Filter output to the Audio Sink input, completing the signal chain from antenna to speaker. Add a QT GUI Time Sink before the audio sink to visualize the demodulated audio waveform. Set the Sample Rate to 48000, Number of Points to 4096, and Input Type to Float. You should observe voice-modulated waveforms spanning approximately ±0.5 amplitude range with characteristic speech envelope dynamics. Add a QT GUI Frequency Sink at the same point to observe the audio spectrum, where you will see most speech energy concentrated below 2 kHz with sibilants extending to 3 kHz.

Run the completed flowgraph and verify audio output. If the NOAA Weather Radio transmission is active, you should hear clear voice synthesis delivering regional forecast information. Adjust the RF Gain slider in the RTL-SDR Source block while observing the input spectrum display. Increasing gain raises the received signal peak relative to the noise floor, improving SNR until the ADC saturates or strong interferers capture the receiver dynamic range. Decreasing gain below approximately 20 dB causes the desired signal to approach the noise floor, degrading demodulation quality and introducing crackling artifacts from threshold events where noise temporarily dominates signal.

Capture the raw I/Q data for offline analysis by adding a File Sink block connected to the RTL-SDR Source output. Set the File parameter to `~/sdr_lab/captures/nbfm_raw_2400ksps.cf64` and run the flowgraph for 10 seconds, accumulating `2.4e6 * 10 * 8 bytes = 192 MB`. Stop the flowgraph and verify the file size matches expectations. Write a Python script `analyze_capture.py` in the analysis directory containing:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Load the captured I/Q data
samples = np.fromfile('~/sdr_lab/captures/nbfm_raw_2400ksps.cf64', dtype=np.complex64)
fs = 2.4e6  # Sample rate in Hz

# Compute power spectral density using Welch's method
freqs, psd = signal.welch(samples, fs=fs, nperseg=4096, scaling='density')

# Plot the spectrum
plt.figure(figsize=(12, 6))
plt.semilogy(freqs / 1e6, psd)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Power Spectral Density (V²/Hz)')
plt.title('Captured SDR Spectrum - Welch PSD Estimate')
plt.grid(True, alpha=0.3)
plt.savefig('spectrum_analysis.png', dpi=300)

# Compute spectrogram for time-frequency analysis
f, t, Sxx = signal.spectrogram(samples, fs=fs, nperseg=1024, noverlap=512)
plt.figure(figsize=(12, 8))
plt.pcolormesh(t, f / 1e6, 10 * np.log10(Sxx), shading='gouraud', cmap='viridis')
plt.ylabel('Frequency (MHz)')
plt.xlabel('Time (seconds)')
plt.title('Spectrogram of Captured SDR Signal')
plt.colorbar(label='Power (dB)')
plt.savefig('spectrogram.png', dpi=300)

# Calculate occupied bandwidth using 99% power criterion
cumulative_power = np.cumsum(psd) / np.sum(psd)
lower_idx = np.searchsorted(cumulative_power, 0.005)
upper_idx = np.searchsorted(cumulative_power, 0.995)
occupied_bw = freqs[upper_idx] - freqs[lower_idx]
print(f"99% Occupied Bandwidth: {occupied_bw / 1e3:.2f} kHz")

# Measure peak-to-average power ratio (PAPR)
instantaneous_power = np.abs(samples) ** 2
peak_power = np.max(instantaneous_power)
avg_power = np.mean(instantaneous_power)
papr_db = 10 * np.log10(peak_power / avg_power)
print(f"Peak-to-Average Power Ratio: {papr_db:.2f} dB")
```

Execute the script with `python3 analyze_capture.py` to generate quantitative metrics and publication-quality plots. The occupied bandwidth measurement provides empirical validation of the transmitted signal's spectral footprint, which should align with the 12.5 kHz channel allocation. Discrepancies indicate excessive deviation, poor pre-emphasis filtering, or transmitter malfunction. The PAPR metric characterizes the signal's dynamic range demands on receiver and transmitter amplifiers, with typical FM voice producing PAPR between 6 and 10 dB.

## Exercise 2: Parameter Variation & Empirical Analysis

This exercise systematically explores the impact of SDR receiver parameters on demodulation fidelity through controlled sweeps of sample rate, filter bandwidth, decimation strategy, and gain settings. By capturing identical signal conditions across parameter variations and applying objective quality metrics including signal-to-noise ratio, total harmonic distortion, and bit error rate for digital modes, you develop empirical intuition for the tradeoffs governing SDR architecture decisions. The investigation reveals how sample rate determines alias-free bandwidth, how filter transition width trades stopband rejection against group delay, and how quantization noise propagates through the processing chain as a function of ADC resolution and signal level.

Begin by modifying the narrowband FM receiver flowgraph to parameterize the decimation structure. Replace the fixed decimation factors with variables enabling runtime adjustment without flowgraph regeneration. Add variables `decim1` set to 10, `decim2` set to 5, and `audio_rate` calculated as `samp_rate/decim1/decim2`, which should evaluate to 48000 Hz. Update the Frequency Xlating FIR Filter decimation parameter to reference `decim1` and the audio low-pass filter decimation parameter to reference `decim2`. This factorization enables exploration of different rate reduction strategies while maintaining constant output sample rate.

Insert instrumentation to capture demodulated audio for offline SNR measurement. Add a second File Sink connected to the audio low-pass filter output, configured for float32 format with filename `~/sdr_lab/captures/audio_decim{}_{}_{}.f32` where the braces will be replaced by parameter values in the analysis script. To enable programmatic control of capture parameters, convert the flowgraph to Python code by selecting Generate in the GNU Radio Companion menu, then edit the resulting Python script to accept command-line arguments. Locate the `__init__` method of the generated class and add argument parsing:

```python
import argparse

def __init__(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('--decim1', type=int, default=10)
    parser.add_argument('--decim2', type=int, default=5)
    parser.add_argument('--rf-gain', type=float, default=30.0)
    parser.add_argument('--duration', type=float, default=5.0)
    parser.add_argument('--output-prefix', type=str, default='param_sweep')
    args = parser.parse_args()
    
    self.decim1 = args.decim1
    self.decim2 = args.decim2
    self.audio_rate = self.samp_rate / self.decim1 / self.decim2
```

Update the relevant block configurations to reference `self.decim1` and `self.decim2` instead of hardcoded values. Add a timer mechanism to automatically stop the flowgraph after the specified duration:

```python
from PyQt5 import QtCore

def __init__(self):
    # ... existing initialization ...
    
    # Setup automatic shutdown timer
    self.timer = QtCore.QTimer()
    self.timer.timeout.connect(self.stop)
    self.timer.start(int(args.duration * 1000))
```

Create a shell script `parameter_sweep.sh` that invokes the modified flowgraph across a range of decimation configurations:

```bash
#!/bin/bash

# Sweep decimation factors while maintaining 48 kHz audio output
# Total decimation must equal 50 to achieve 2.4MHz -> 48kHz

for decim1 in 2 5 10 25 50; do
    decim2=$((48000 * decim1 / 2400000))
    if [ $((2400000 / decim1 / decim2)) -eq 48000 ]; then
        echo "Testing decimation strategy: decim1=$decim1, decim2=$decim2"
        python3 nbfm_receiver.py \
            --decim1 $decim1 \
            --decim2 $decim2 \
            --duration 10 \
            --output-prefix "decim_${decim1}_${decim2}"
        sleep 2  # Brief pause between runs
    fi
done
```

Execute the sweep with `bash parameter_sweep.sh`, accumulating a set of audio capture files representing different multistage decimation architectures. The sweep explores configurations ranging from aggressive first-stage decimation (decim1=50, decim2=1) which minimizes processing at high sample rate but demands wider filter transition bands, through balanced strategies (decim1=10, decim2=5) that distribute filtering across stages, to conservative approaches (decim1=2, decim2=25) that perform most decimation near the audio rate where filter design is simplified.

Analyze the captured audio files with a Python script that computes SNR through signal and noise power estimation. The methodology separates voiced speech segments from silence intervals, treating the former as signal+noise and the latter as noise-only references:

```python
import numpy as np
import glob
from scipy.io import wavfile
from scipy import signal as sp_signal

def estimate_snr_from_audio(audio_file, fs=48000):
    """
    Estimate SNR by comparing power in voiced vs. silence segments.
    """
    # Load audio samples
    samples = np.fromfile(audio_file, dtype=np.float32)
    
    # Compute short-term RMS energy with 20ms frames
    frame_length = int(0.02 * fs)
    hop_length = frame_length // 2
    num_frames = (len(samples) - frame_length) // hop_length
    
    energy = np.zeros(num_frames)
    for i in range(num_frames):
        start = i * hop_length
        frame = samples[start:start + frame_length]
        energy[i] = np.sqrt(np.mean(frame ** 2))
    
    # Threshold-based voice activity detection
    # Assume bottom 30% of energy distribution represents silence/noise
    energy_threshold = np.percentile(energy, 30)
    
    noise_frames = energy < energy_threshold
    signal_frames = energy >= energy_threshold
    
    if np.sum(noise_frames) == 0 or np.sum(signal_frames) == 0:
        return np.nan
    
    # Extract corresponding samples
    noise_samples = []
    signal_samples = []
    for i in range(num_frames):
        start = i * hop_length
        frame = samples[start:start + frame_length]
        if noise_frames[i]:
            noise_samples.extend(frame)
        else:
            signal_samples.extend(frame)
    
    noise_power = np.mean(np.array(noise_samples) ** 2)
    signal_power = np.mean(np.array(signal_samples) ** 2)
    
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db

# Process all captured audio files
results = []
for audio_file in sorted(glob.glob('~/sdr_lab/captures/decim_*.f32')):
    snr = estimate_snr_from_audio(audio_file)
    # Extract decimation parameters from filename
    parts = audio_file.split('_')
    decim1 = int(parts[-3])
    decim2 = int(parts[-2])
    results.append((decim1, decim2, snr))
    print(f"Decimation {decim1}×{decim2}: SNR = {snr:.2f} dB")

# Identify optimal configuration
results.sort(key=lambda x: x[2], reverse=True)
print(f"\nOptimal decimation strategy: {results[0][0]}×{results[0][1]} "
      f"with SNR = {results[0][2]:.2f} dB")
```

The results typically reveal that balanced multi-stage decimation architectures outperform extreme single-stage approaches. Aggressive early decimation produces suboptimal results because the wide transition band required for anti-aliasing filters at high decimation ratios allows more out-of-band noise to fold into the passband. Conversely, minimal early decimation forces high-rate processing through many filter stages, accumulating numerical precision loss and computational artifacts. The optimal configuration generally places the first decimation stage at 5 to 10 times reduction with well-designed Hamming-windowed FIR filters, followed by moderate second-stage decimation with sharper cutoff characteristics enabled by the lower sample rate.

Extend the analysis to characterize filter performance through swept bandwidth measurements. Modify the flowgraph to parameterize the audio low-pass filter cutoff frequency, adding a variable `audio_bw` and replacing the hardcoded 3 kHz cutoff with this variable. Generate a sweep script that varies cutoff from 1 kHz through 8 kHz in 500 Hz steps while capturing fixed-content NOAA Weather Radio audio. Process each capture with FFT-based spectral analysis to measure signal power integrated from DC to `audio_bw` and noise power integrated from `audio_bw` to the Nyquist frequency:

```python
def measure_filter_effectiveness(audio_file, cutoff_freq, fs=48000):
    """
    Quantify filter stopband rejection by measuring passband vs. stopband power.
    """
    samples = np.fromfile(audio_file, dtype=np.float32)
    
    # Compute power spectral density
    freqs, psd = sp_signal.welch(samples, fs=fs, nperseg=2048)
    
    # Integrate power in passband (DC to cutoff)
    passband_mask = freqs <= cutoff_freq
    passband_power = np.trapz(psd[passband_mask], freqs[passband_mask])
    
    # Integrate power in stopband (cutoff to Nyquist)
    stopband_mask = freqs > cutoff_freq
    stopband_power = np.trapz(psd[stopband_mask], freqs[stopband_mask])
    
    # Calculate stopband rejection
    rejection_db = 10 * np.log10(passband_power / stopband_power)
    
    return rejection_db, passband_power, stopband_power
```

Plot the filter rejection versus cutoff frequency to reveal the transition band characteristics. Narrower cutoff frequencies require steeper filter roll-off to maintain adequate stopband attenuation, increasing filter order and group delay. Excessively wide cutoff frequencies admit quantization noise and high-frequency artifacts from the FM discriminator, degrading SNR. The optimal cutoff balances speech intelligibility, which benefits from preserving energy through 3 kHz, against noise rejection, which favors aggressive low-pass filtering. Standard practice in narrowband FM voice systems settles on 3 kHz cutoff as an empirically validated compromise.

Investigate the impact of RF gain settings on receiver dynamic range by sweeping the RTL-SDR Source gain parameter from 0 dB to 49.6 dB in 5 dB steps. At each gain setting, capture 5 seconds of audio and compute SNR along with a clipping detection metric that identifies ADC saturation events. The RTL-SDR uses an 8-bit ADC producing signed samples in the range -128 to +127. Saturation occurs when samples cluster at these extrema, indicating insufficient headroom:

```python
def detect_clipping(iq_file):
    """
    Measure ADC saturation by counting samples at digital full-scale.
    """
    samples = np.fromfile(iq_file, dtype=np.complex64)
    
    # Convert to 8-bit integer representation for analysis
    # RTL-SDR raw samples are scaled floats representing the actual ADC values
    i_samples = np.real(samples)
    q_samples = np.imag(samples)
    
    # Detect samples within 1% of full scale
    threshold = 0.99
    i_clipped = np.sum(np.abs(i_samples) > threshold)
    q_clipped = np.sum(np.abs(q_samples) > threshold)
    
    total_samples = len(samples) * 2  # Both I and Q
    clipping_rate = (i_clipped + q_clipped) / total_samples
    
    return clipping_rate * 100  # Return as percentage
```

Execute the gain sweep and plot SNR versus gain alongside clipping percentage. The characteristic curve shows SNR improving with gain as the signal rises above the quantization noise floor, reaching a plateau where thermal noise dominates, then degrading as gain increases further and clipping artifacts appear. The optimal operating point resides just below the onset of clipping, typically at 30 to 35 dB gain for RTL-SDR receivers observing moderate-strength signals. Weak signal reception may require maximum gain despite elevated noise floor, while strong local signals demand attenuation to prevent overload.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

This exercise subjects the SDR receiver to adversarial signal conditions that expose fundamental limitations of discrete-time sampling systems and digital signal processing. By deliberately inducing aliasing through Nyquist violations, saturating the ADC with high-level interferers, and introducing multipath fading through controlled RF channel emulation, you develop diagnostic skills for identifying failure modes in operational deployments. The investigation culminates in implementing detection and mitigation strategies including automatic gain control, alias rejection filtering, and adaptive equalization that restore receiver functionality under non-ideal conditions.

Begin by constructing a test signal generator flowgraph that produces controlled interference for injection into the SDR receiver. Create a new GNU Radio flowgraph with a Signal Source block configured for Complex output, Frequency set to `interference_freq` variable, Sample Rate set to `samp_rate`, and Waveform set to Cosine. This generates a pure tone at arbitrary frequency offset from DC. Add a Multiply Const block to scale the interference amplitude, with Constant set to variable `interference_amp`. Sum this interference with a legitimate FM signal by adding an Add block that combines the Signal Source output with an RTL-SDR Source output. Route the summed signal through your existing FM receiver chain.

Configure the interference frequency to violate Nyquist by setting `interference_freq` to 1.8 MHz, exceeding the 1.2 MHz Nyquist bandwidth of the 2.4 MHz sample rate. Run the flowgraph and observe the spectrum display. The interferer appears at its generated frequency of 1.8 MHz, but simultaneously a mirror image alias appears at `samp_rate - interference_freq = 600 kHz` due to spectral folding. This aliased component cannot be distinguished from a legitimate signal at 600 kHz, demonstrating the fundamental ambiguity introduced by undersampling. Tune the receiver center frequency to place your desired signal at 500 kHz offset, positioning it near the alias. Increase `interference_amp` until the alias causes audible distortion or complete capture of the demodulator.

Quantify the alias rejection of the SDR's anti-aliasing filter by sweeping the interference frequency from 0.5×`samp_rate` through 2.0×`samp_rate` and measuring the aliased power appearing within the receiver passband. For an ideal anti-aliasing filter, all energy beyond Nyquist should be attenuated to the noise floor before sampling. Real-world SDR hardware exhibits finite rejection, typically 40 to 60 dB for the RTL-SDR's front-end LC filter. Write a measurement script that injects a calibrated interference tone, captures the resulting I/Q samples, and computes the ratio of in-band alias power to the interference power that would appear if no filtering existed:

```python
def measure_alias_rejection(center_freq, interference_freq, duration=1.0):
    """
    Inject out-of-band tone and measure aliased power in passband.
    """
    # Generate interference tone
    fs = 2.4e6
    t = np.arange(int(fs * duration)) / fs
    interference = np.exp(2j * np.pi * interference_freq * t)
    
    # Mix with captured SDR samples (assumes simultaneous capture)
    iq_samples = np.fromfile('~/sdr_lab/captures/alias_test.cf64', 
                             dtype=np.complex64, 
                             count=int(fs * duration))
    
    # Calculate expected alias frequency
    if interference_freq > fs / 2:
        alias_freq = fs - interference_freq
    else:
        alias_freq = interference_freq
    
    # Measure power in narrow band around alias frequency
    freqs, psd = sp_signal.welch(iq_samples, fs=fs, nperseg=4096)
    alias_idx = np.argmin(np.abs(freqs - alias_freq))
    alias_band = slice(alias_idx - 5, alias_idx + 5)  # ±5 bins around alias
    alias_power = np.mean(psd[alias_band])
    
    # Measure noise floor in clean region
    noise_band = (freqs > 100e3) & (freqs < 200e3)
    noise_floor = np.mean(psd[noise_band])
    
    rejection_db = 10 * np.log10(alias_power / noise_floor)
    return rejection_db
```

Sweep interference frequency from 1.5 MHz to 3.5 MHz in 100 kHz steps, capturing the alias rejection at each point. Plot rejection versus frequency offset beyond Nyquist to characterize the analog anti-aliasing filter response. The curve reveals the LC filter's roll-off characteristics, typically showing 6 to 12 dB per octave attenuation. Poor alias rejection at specific frequencies may indicate resonances or impedance discontinuities in the RF chain.

Stress the ADC dynamic range by injecting a strong continuous-wave interferer at varying power levels while attempting to receive a weak FM signal. Configure the signal generator to produce a carrier at 162.450 MHz with +10 dBm output power, and tune your SDR to 162.550 MHz to receive NOAA Weather Radio 100 kHz away. The strong interferer does not occupy the desired channel but exercises the receiver's dynamic range by elevating the composite signal presented to the ADC. Connect the signal generator through a 30 dB attenuator to the SDR input, initially presenting -20 dBm at the receiver. Verify clean audio reception of the desired signal.

Incrementally reduce the attenuation in 5 dB steps, increasing the interferer level while monitoring the demodulated audio quality and the raw I/Q samples for clipping. At some threshold, typically when the interferer reaches approximately 30 dB above the desired signal, the ADC quantization noise floor rises sufficiently to degrade SNR, or the interferer captures a significant portion of the ADC's dynamic range through intermodulation. Document the blocking dynamic range, defined as the interferer level at which the desired signal SNR degrades by 3 dB relative to the no-interferer baseline:

```python
def measure_blocking_dynamic_range(desired_signal_freq, interferer_freq,
                                   interferer_levels_dbm):
    """
    Measure receiver sensitivity degradation vs. out-of-channel interferer level.
    """
    results = []
    
    for interferer_dbm in interferer_levels_dbm:
        # Configure signal generator to specified level
        # (Requires SCPI control of actual hardware signal generator)
        
        # Capture receiver output
        # ... capture code ...
        
        # Compute SNR of desired signal
        snr = estimate_snr_from_audio('capture.f32')
        results.append((interferer_dbm, snr))
    
    # Find 3 dB degradation point
    baseline_snr = results[0][1]  # Lowest interferer level
    for interferer_dbm, snr in results:
        if snr < baseline_snr - 3:
            return interferer_dbm
    
    return None  # No blocking observed
```

Implement automatic gain control to extend receiver dynamic range by adaptively adjusting RF gain based on measured signal power. Modify the FM receiver flowgraph to include a Complex to Mag^2 block that computes instantaneous power, followed by a Single Pole IIR Filter block with alpha set to 0.01 to average power over approximately 100 samples. Add a Python Embedded Block that reads this averaged power and adjusts the RTL-SDR Source RF gain through the `set_gain()` method:

```python
import numpy as np

class agc_controller(gr.sync_block):
    def __init__(self, target_power=-20, gain_limits=(0, 45)):
        gr.sync_block.__init__(
            self,
            name="AGC Controller",
            in_sig=[np.float32],   # Averaged power input
            out_sig=None
        )
        self.target_power_db = target_power
        self.min_gain, self.max_gain = gain_limits
        self.current_gain = 30.0
        self.rtlsdr_source = None  # Set via setter method
        
    def work(self, input_items, output_items):
        power_linear = input_items[0]
        power_db = 10 * np.log10(np.mean(power_linear) + 1e-12)
        
        # Simple proportional control
        error_db = self.target_power_db - power_db
        gain_adjustment = 0.1 * error_db  # 10% correction per iteration
        
        new_gain = np.clip(self.current_gain + gain_adjustment,
                          self.min_gain, self.max_gain)
        
        if self.rtlsdr_source and abs(new_gain - self.current_gain) > 0.5:
            self.rtlsdr_source.set_gain(new_gain)
            self.current_gain = new_gain
        
        return len(input_items[0])
```

Connect the averaged power output to this AGC controller block and provide a reference to the RTL-SDR Source block through a setter method called during flowgraph initialization. Test the AGC by applying stepped interferer levels and observing the gain automatically reduce to prevent saturation, then recover when the interferer is removed. Measure the AGC response time by capturing the gain control signal during a transient event, revealing the attack and decay time constants governed by the IIR filter alpha parameter.

Simulate multipath fading by creating an RF channel emulator that applies time-varying delays and Doppler shifts to the received signal. Add a Delay block in the FM receiver flowgraph configured with a variable delay parameter that modulates sinusoidally: `delay_samples = int(base_delay + modulation_depth * math.sin(2 * math.pi * fade_rate * time))`. The base delay represents the static path delay difference, modulation depth controls the severity of destructive interference nulls, and fade rate determines how quickly the channel fluctuates. Set `base_delay` to 50 samples (21 microseconds at 2.4 MHz), `modulation_depth` to 25 samples, and `fade_rate` to 2 Hz to emulate slow vehicle motion.

Split the received signal with a Complex to Mag block to extract the envelope, then plot this envelope in a QT GUI Time Sink to observe the characteristic deep fades occurring approximately twice per second as the direct and delayed paths cycle through constructive and destructive interference. The audio output exhibits periodic dropouts during fade nulls when the signal briefly falls below the demodulator threshold. Implement fade mitigation through diversity combining by creating a second receiver chain with different delay parameters, summing the demodulated audio from both chains:

```python
# In GNU Radio flowgraph, create two parallel FM receiver chains
# with uncorrelated multipath channels, then add their outputs:

audio_combined = gr.add_ff()
self.connect((fm_receiver_1, 0), (audio_combined, 0))
self.connect((fm_receiver_2, 0), (audio_combined, 1))
self.connect(audio_combined, audio_sink)
```

Measure the diversity gain by comparing SNR with single-channel versus dual-channel reception under fading conditions. Capture 60 seconds of audio for each configuration and compute the cumulative distribution function of instantaneous SNR. Diversity combining significantly reduces the probability of deep fades, with the 10th percentile SNR typically improving by 6 to 10 dB.

## Operational Reference Guide & Diagnostic Checklist

This reference consolidates the essential troubleshooting procedures, performance validation metrics, and diagnostic decision trees developed through the preceding exercises into a field-deployable checklist for operational SDR systems. The guide prioritizes systematic elimination of root causes through quantitative measurement rather than subjective assessment, progressing from RF frontend verification through digital processing chain validation to final audio quality metrics.

**Initial System Verification Procedure**: Before investigating complex failure modes, establish baseline functionality through this abbreviated power-on sequence. Connect the SDR hardware and execute `rtl_test -t` to verify USB enumeration and basic tuner communication. Expected output shows device detection with zero dropped samples during the brief test sweep. If device enumeration fails, check USB cable integrity by testing with a known-good cable and verify adequate bus power by connecting to a directly motherboard-mounted USB port rather than hub-connected or front-panel ports. Execute `rtl_eeprom` to read device identification and verify expected manufacturer and product fields match your hardware model. For RTL-SDR V3 dongles, the manufacturer string should contain "RTLSDRBlog" and the product string should indicate "RTL2838UHIDIR". Discrepancies suggest counterfeit hardware or corrupted EEPROM requiring reflash with genuine descriptor data.

Launch GNU Radio Companion and load the baseline FM receiver flowgraph. Tune to a known-active strong local signal such as a commercial FM broadcast station. If no audio output is heard, systematically verify each stage: check the QT GUI Frequency Sink display after the RTL-SDR Source block for spectral content with peaks rising at least 30 dB above the noise floor. Absence of spectral peaks despite correct tuning indicates frontend failure, inadequate antenna coupling, or improper RF gain settings. Verify antenna connection integrity with a DC continuity check between the SMA center pin and antenna element. Inspect the RF chain for damaged coaxial cables showing shield-to-center shorts detectable with a multimeter resistance measurement, which should read open circuit (>1 MΩ).

**Sample Rate and Bandwidth Calculations**: All SDR processing chain parameters derive from the fundamental sample rate and desired signal bandwidth. Given a sample rate `fs` in samples per second, the Nyquist bandwidth extends from DC to `fs/2` Hz. To receive a signal occupying bandwidth `BW`, the minimum sample rate calculates as `fs = 2.0 * BW * (1 + α)` where `α` represents the transition band factor accounting for practical filter roll-off, typically 0.2 to 0.5. For a 12.5 kHz FM voice channel, the required sample rate exceeds `2.0 * 12.5e3 * 1.2 = 30 kHz`. When cascading decimation stages, the filter cutoff at each stage must satisfy `fc < fs_out/2` where `fs_out = fs_in/decimation`. Design intermediate filters with cutoff `fc = fs_out/(2 * 1.2)` to provide 20% guardband against aliasing. Verify these relationships in operational systems by measuring the occupied signal bandwidth from spectral plots and confirming it remains below half the sample rate at each processing stage.

**Decimation Filter Design Guidelines**: Multi-stage decimation requires careful allocation of transition bandwidth to each filter stage. The first-stage filter operates at the highest sample rate, making computational efficiency critical. Use Hamming-windowed FIR designs with transition bandwidth approximately 20% of the decimated rate, producing filter orders on the order of 100 to 200 taps. The `firdes.low_pass()` function in GNU Radio automatically computes the required number of taps given sample rate, cutoff frequency, and transition width. For a 2.4 MHz to 240 kHz decimation-by-10 stage with 12.5 kHz cutoff, specify transition width of 48 kHz (`240 kHz * 0.2`) resulting in approximately 60 taps. Second-stage filters benefit from lower sample rate enabling sharper cutoff characteristics; a 240 kHz to 48 kHz decimation-by-5 stage can use 3 kHz transition width producing 100 taps with stopband attenuation exceeding 60 dB. Measure actual filter performance by injecting white noise and computing the ratio of passband to stopband power from the PSD estimate.

**Frequency Translation and Mixing**: The frequency xlating FIR filter implements a complex multiply by $e^{j2\pi f_c n / f_s}$ to shift the spectrum by offset `fc` before low-pass filtering and decimation. The offset parameter requires careful sign convention: positive offset shifts signals at positive frequencies down toward DC, equivalent to tuning the receiver higher in frequency. When receiving a signal at 162.550 MHz with the SDR tuned to 162.500 MHz, the signal appears at +50 kHz in baseband, requiring offset `+50e3` to center it at DC. Verify correct offset by observing the QT GUI Frequency Sink after the xlating filter; the desired signal should appear centered at 0 Hz with symmetric spectral shape. Incorrect offset manifests as asymmetric spectrum or signal positioned away from DC, producing suboptimal filtering and potential aliasing in subsequent decimation.

**FM Demodulation Gain Scaling**: The Quadrature Demod block outputs the instantaneous frequency deviation in units of radians per sample. Converting to audio requires gain scaling `K = fs / (2 * π * fdev)` where `fs` is the sample rate input to the demodulator and `fdev` is the expected peak frequency deviation. For narrowband FM voice with ±5 kHz deviation received at 240 kHz sample rate, the gain calculates to `240e3 / (2 * π * 5e3) = 7.639`. Incorrect gain produces audio that is too loud or too quiet relative to the nominal ±1.0 range expected by subsequent processing. Measure the demodulated audio peak values; properly scaled signals should reach approximately ±0.7 during full modulation. Peaks consistently exceeding ±1.0 indicate excessive gain causing clipping, while peaks below ±0.3 indicate insufficient gain requiring re-calibration of the deviation estimate.

**SNR Measurement Methodology**: Quantitative SNR assessment requires separating signal from noise in the measurement. For voice audio, implement voice activity detection by computing short-term RMS energy in 20 millisecond frames and thresholding at the 30th percentile of the energy distribution. Frames below threshold represent noise-only samples; frames above represent signal-plus-noise. Calculate noise power `Pn` by averaging the squared samples in noise-only frames and signal-plus-noise power `Ps+n` by averaging squared samples in signal frames. The SNR computes as `SNR = 10 * log10((Ps+n - Pn) / Pn)` in decibels. Typical narrowband FM voice achieves 20 to 30 dB SNR under good conditions; SNR below 15 dB produces noticeable degradation; SNR below 10 dB renders speech unintelligible. For continuous signals without silence intervals, estimate noise power from the spectral floor in frequency regions outside the signal bandwidth.

**ADC Saturation Detection**: Monitor the raw I/Q samples for clipping events where samples reach the maximum digital value. For RTL-SDR 8-bit ADC producing float samples normalized to ±1.0 range, saturation occurs when the absolute value exceeds 0.95. Count saturation events and calculate the clipping rate as the percentage of total samples affected. Any non-zero clipping rate indicates insufficient headroom and requires RF gain reduction. Clipping rates below 0.1% may be tolerable for noise-like signals but produce unacceptable distortion for narrowband signals. Plot the amplitude histogram of I and Q samples separately; a properly adjusted receiver shows Gaussian distribution centered at zero with tails reaching approximately ±0.5. Histograms with mass concentrated at ±1.0 indicate severe clipping. Histograms narrowly concentrated near zero indicate insufficient gain, wasting ADC dynamic range and elevating relative quantization noise.

**Troubleshooting No Audio Output**: When the SDR receiver produces no audio despite correct tuning and visible signal in the spectrum display, systematically check: verify the audio sink sample rate matches the final processing stage output rate, typically 48000 Hz. Mismatched rates produce silent output or distorted audio. Check audio system configuration with `aplay -l` to list available playback devices and ensure the default ALSA device corresponds to active speakers or headphones. Test audio hardware independently with `speaker-test -c 2 -t wav` which plays test tones through the default device. If audio hardware functions but SDR output remains silent, insert a QT GUI Time Sink before the audio sink to verify demodulated waveform presence. Absence of waveform despite spectrum signal indicates demodulator failure, typically caused by incorrect quadrature demod gain or filter misconfiguration. Presence of waveform with no audio output indicates audio sink configuration error or volume muted at the OS level.

**Spectral Inversion and Sideband Ambiguity**: Complex sampling with I/Q pairs preserves positive and negative frequency information, but certain hardware configurations or software settings may swap the I and Q channels producing spectral inversion. Symptoms include FM signals that demodulate to reversed audio (high frequencies sound low and vice versa) or SSB signals appearing on the wrong sideband. Verify spectral orientation by tuning to a known FM broadcast station and observing the QT GUI Frequency Sink; if the signal appears mirrored (pilot tone and stereo subcarriers reversed), enable the "Swap IQ" option in the RTL-SDR Source block. For direct conversion receivers, spectral inversion also arises from incorrect local oscillator mixing; consult hardware documentation for the expected sideband configuration.

**Filter Group Delay Impact**: FIR filters introduce group delay equal to half the filter length in samples, representing the time offset between input and output. For a 100-tap filter operating at 240 kHz sample rate, the group delay equals `50 / 240e3 = 208 microseconds`. In multi-stage decimation cascades, delays accumulate. Excessive delay impacts real-time applications requiring low latency, such as voice repeater systems or adaptive feedback control. Measure total system latency by injecting an impulse and observing the time offset to the output response. Reduce latency by decreasing filter lengths at the cost of wider transition bands and reduced stopband rejection, or by replacing FIR filters with lower-order IIR alternatives accepting their nonlinear phase response.

**Dynamic Range Measurement**: Receiver dynamic range characterizes the ratio between the strongest and weakest signals that can be simultaneously processed without degradation. The blocking dynamic range measures the maximum interferer level that can be tolerated outside the desired channel while maintaining desired signal SNR. Measure by tuning to a weak signal, noting baseline SNR, then injecting an out-of-channel tone at increasing levels until SNR degrades 3 dB. The interferer level at this threshold in dBm minus the desired signal level in dBm yields the blocking DR in dB. Typical RTL-SDR dongles achieve 50 to 60 dB blocking DR. The spurious-free dynamic range (SFDR) measures the weakest detectable signal relative to the strongest signal before spurious mixing products appear at the third-order intercept point. Measure SFDR by injecting two strong tones and observing the intermodulation products that arise at frequencies `2f1 - f2` and `2f2 - f1`.

**Multipath and Fading Characterization**: Mobile or portable operation introduces time-varying multipath propagation causing signal amplitude and phase to fluctuate. Characterize fading by capturing the complex envelope magnitude over 60 seconds and computing the fade rate and fade depth statistics. The fade rate in Hz corresponds to the peak in the power spectral density of the envelope. The fade depth in dB measures the 10th percentile envelope level relative to the median level. Rayleigh fading models predict 10 dB fade depth for non-line-of-sight channels; measured depths significantly exceeding this indicate severe multipath requiring diversity reception or equalization. Plot the envelope CDF on Rayleigh probability paper; linear fit confirms the Rayleigh fading model applies, while deviations indicate Rician fading with a dominant line-of-sight component.

**Calibration and Reference Signal Tracking**: SDR local oscillator frequency error accumulates with integration time, causing narrow filters to drift off-tune and degrade reception. Calibrate frequency error at system startup by tuning to a precision reference such as WWV or GPS-disciplined oscillator signals. The measured error in parts per million applies as a linear correction across the entire tuning range. Temperature changes induce drift requiring periodic re-calibration; monitor a known reference signal continuously and adjust the frequency correction parameter when drift exceeds 10% of the channel bandwidth. For narrowband signals, implement automatic frequency control by measuring the spectral peak offset from DC after initial coarse tuning and applying fine correction through the frequency xlating filter offset parameter.

This operational reference guide provides the diagnostic foundation for maintaining SDR systems in production deployment. Systematic application of these measurements and troubleshooting procedures isolates root causes rapidly, enabling restoration of service and continuous performance optimization through empirical feedback.
