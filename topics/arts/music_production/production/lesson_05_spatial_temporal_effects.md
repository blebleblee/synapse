# Lesson 5: Spatial & Temporal Processing: Reverb Architectures, Delay Networks, and Stereo Imaging

## 1. Acoustic Foundations & Psychoacoustic Localization Invariants

The human auditory system localizes sound sources in three-dimensional space through a hierarchy of cues, each operating across distinct frequency bands and temporal windows. Understanding these mechanisms is foundational to spatial mixing—not as abstract theory, but as the precise mechanics governing how listeners perceive depth, width, and directional intent in your mix.

### Interaural Time Differences and the Haas Effect

Interaural Time Differences (ITD) represent the primary localization cue below 1.5 kHz. When a sound source originates from one side of the listener's head, the acoustic wavefront reaches the ipsilateral ear before the contralateral ear. For a point source positioned 90 degrees azimuth (directly to the side), this time difference reaches its maximum: approximately 700 microseconds at the adult human head diameter of 19–21 cm.

The precedence effect (also called the Haas effect in the context of artificial sound) governs perception when identical or near-identical signals arrive at each ear with a delay between them. When the leading signal precedes the lagging signal by 0–20 milliseconds, the listener's localization collapses toward the leading signal's position, and the lagging signal is perceptually suppressed—not eliminated, but integrated as reverberant energy rather than a discrete echo. This suppression region holds critical implications for mixing.

Consider a lead vocal recorded in mono, panned center, with a 15 ms pre-delay on a reverb send. That reverb's early reflections, arriving 15 ms after the dry signal, trigger the Haas effect. The listener perceives a single, cohesive vocal image centered in the stereo field, with the reverb tail adding depth without creating a sense of multiple sound sources. Extend that pre-delay to 35 ms, and the mechanism breaks down: the early reflections now arrive outside the precedence window, creating a discrete auditory image offset from the center, a fluttering sense of doubling.

The critical threshold lies between 20–35 ms. Below 20 ms, precedence dominates. Above 40 ms, the ear typically resolves two separate events. This 15 ms middle ground requires careful handling—too much pre-delay causes localization confusion; too little obscures the spatial intent.

### Interaural Level Differences and High-Frequency Localization

Above 1.5 kHz, the wavelengths become shorter than the head diameter, and phase relationships become unreliable for localization. Instead, the auditory system relies on Interaural Level Differences (ILD)—the amplitude difference between ears caused by the head's acoustic shadowing effect.

A sound source 90 degrees to the right produces roughly 15–20 dB level difference at 4 kHz between the right ear (closer) and left ear (shadowed). This high-frequency shadowing is frequency-dependent: the effect increases with frequency and azimuthal angle. At 2 kHz, the shadowing might measure 6–8 dB; at 8 kHz, 18–25 dB.

In mixing, this principle manifests in stereo widening techniques. When you apply aggressive high-pass filtering to a side-channel signal (Left − Right), you preserve the ILD cues at high frequencies while reducing low-frequency decorrelation. A bass guitar panned hard-left with only midrange energy present sounds stable; the same bass with presence peaks at 6 kHz and 12 kHz extends into the stereo field, creating apparent width without phase cancellation risk.

### Spectral Cues and the Pinna Filter

The external ear (pinna) exhibits resonant peaks and nulls that vary with elevation and front-back angle. These spectral cues allow the brain to distinguish front from back and to estimate elevation—localization in the vertical plane. The pinna's transfer function is highly individual; your ears are acoustically unique fingerprints. However, common features emerge: a resonance around 2–4 kHz (related to the ear canal length) and various notches above 4 kHz that deepen with elevation.

When designing spatial effects, particularly binaural and 3D audio systems, these spectral cues become engineered parameters. A reverb algorithm designed to simulate elevation will introduce spectral peaks and notches mimicking the pinna filter. A simple algorithmic reverb, lacking these cues, will sound diffuse but not spatially localized in the vertical plane.

### Mono-Compatibility and Phase Cancellation Mechanics

The precedence effect and ITD/ILD mechanisms assume a stereo listening context. However, mono playback remains a critical compatibility target—mobile playback, broadcast, and single-speaker scenarios still dominate real-world listening. When a stereo mix collapses to mono (Left + Right summed equally), phase cancellation becomes a primary concern.

A 100 ms stereo delay, 400 ms on the left channel, 500 ms on the right, sums to a mono signal with notching. Frequencies whose wavelengths align with the 100 ms delay difference experience partial cancellation. At 10 Hz, the wavelength is 34 meters; a 100 ms delay represents a 3.4 meter path difference—negligible relative cancellation. At 1 kHz, the wavelength is 34 cm; a 100 ms delay represents roughly 3.4 cycles, resulting in partial constructive/destructive interference across the spectrum.

The practical rule: keep relative stereo delays below 20–30 ms for sources that must survive mono conversion. Vocal doubles, snare layers, and lead instruments require mono-safe processing. Ambient textures, pads, and backgrounds tolerate wider stereo delays.

---

## 2. Temporal Delay Architectures & Feedback Topologies

Delay is the fundamental operation underlying both reverb and modulation effects. The mechanics of delay implementation—from analog tape saturation and bucket-brigade clocking artifacts to digital feedback topologies—shape the character and utility of temporal effects in professional mixing.

### Analog Tape Delay: Saturation, Flutter, and Wow

Analog tape delay represents the historical gold standard and remains a tonal reference for modern plugins. The mechanism is mechanical: audio is recorded to a moving magnetic tape via an erase head, playback head, and record head. The time delay equals the physical distance between record and playback heads divided by tape speed.

Tape speed determines two critical sonic characteristics: wow and flutter. Wow refers to slow speed variations (below ~6 Hz) caused by motor irregularities and tape tension variations. Flutter refers to rapid speed variations (6 Hz–1 kHz), caused by capstan and roller imperfections. Modern tape machines exhibit wow/flutter specifications of 0.05–0.1%, measured as frequency deviation. A 1 kHz oscillator passing through a tape deck with 0.1% flutter will exhibit ±1 Hz deviation—subtle but audible as a shimmering, organic texture.

Equally important is tape saturation. As magnetic tape approaches its maximum flux capacity, the recording process becomes nonlinear. Input signals above −3 dBFS exhibit gentle compression and harmonic distortion. This saturation is the primary tonal characteristic of tape—not pristine transparency, but warm, slightly compressed sound with added second and third harmonics at approximately −40 to −50 dBFS relative to the fundamental.

Modern tape delay emulations attempt to capture these behaviors. High-quality plugins model tape hysteresis (the lag between applied magnetic field and tape magnetization), saturation curves, and flutter. The computational cost is significant; a full tape simulation requires convolution or complex nonlinear modeling. Approximations using soft-clipping saturation, subtle pitch modulation (0.05–0.1 Hz LFO at ±0.5% depth), and harmonic distortion achieve 80% of the sonic character at 5% of the CPU cost.

### Bucket-Brigade Device Analog Delays

Bucket-Brigade Devices (BBDs) represent a discrete alternative to tape for analog delay storage. Rather than magnetic flux, BBDs use MOSFET transistor chains to shift analog voltage samples through a series of capacitors. Each clock pulse shifts the voltage down the chain one stage, achieving continuous analog delay.

BBD clocking frequency directly determines maximum delay time. A 100-stage BBD clocked at 500 kHz achieves 200 microseconds per stage, or 20 milliseconds maximum delay. To extend delays to 300–600 ms, designers must reduce clock frequency to 50–100 kHz. Lower clock rates introduce aliasing and noise artifacts; 50 kHz clock on a 100-stage device produces a Nyquist frequency of 25 kHz with aliasing of signals above that threshold, creating characteristic "grit" when signal peaks approach the rails.

BBD delays exhibit distinctive frequency-dependent phase shift and mild nonlinearities due to transistor mismatch and capacitor tolerance variations. These artifacts are the sonic signature of classic analog delays like the Electro-Harmonix Memory Man and Boss RE-20. Modern emulations capture this via mathematical models, but pure BBD character remains difficult to replicate perfectly—the interaction between clock frequency, voltage rails, and transistor characteristics introduces subtle randomness that hardware carries inherently.

### Digital Delay Topologies: Ping-Pong, Multi-Tap, and Feedback Networks

Digital delay is implemented via a circular buffer—a block of memory addressed sequentially. The write pointer advances sample-by-sample; the read pointer lags behind by the delay time in samples. When the write pointer reaches the end of the buffer, it wraps to the beginning, creating a circular structure.

**Ping-pong delay** alternates delayed repeats between left and right channels. The first repeat appears on the left, the second on the right, the third on the left, and so forth. This topology is commonplace in modern production, particularly for electronic music and synth-pop. The mechanism is simple: a single feedback delay line with the feedback routed to opposite channels on each repeat.

Implementation: maintain a single delay buffer. The feedback calculation routes the delayed sample to both channels but sets a pan coefficient that alternates with each repeat cycle. In pseudocode:

```
for each sample:
  output_L = input_L + delayed_sample * pan_L * feedback
  output_R = input_R + delayed_sample * pan_R * feedback
  
  pan alternates: [1, 0] → [0, 1] → [1, 0]
  
  write(input + feedback * delayed_sample)
```

Ping-pong delays at fast tempos (quarter-note or eighth-note repeats) create rhythmic interest without taking up excessive mono space. The alternation causes phase separation between channels; in mono, the repeats partially cancel, reducing overall level and creating a sense of "shimmer."

**Multi-tap delays** create parallel delay lines with independent delay times and feedback amounts. A four-tap delay running at quarter-note, eighth-note, triplet eighth, and sixteenth-note repeats generates polyrhythmic textures. Each tap maintains its own read pointer into the delay buffer, and each tap's output is summed.

Example: at 120 BPM, quarter-note delay time = (60 / 120) * 1000 = 500 ms. Eighth-note = 250 ms, triplet eighth = 166.67 ms, sixteenth = 125 ms. Separate feedback for each tap controls repeat density. A synth with quarter-note feedback at 0.6, eighth-note at 0.3, and sixteenth at 0.1 produces a cascading repeat structure that locks to the rhythm while adding textural complexity.

**Feedback delay networks (FDNs)** extend the concept by creating cross-coupled delay lines. Rather than simple feedback, each delay's output is routed through a mixing matrix before feeding back into the network. This topology forms the basis of professional algorithmic reverbs (discussed in Section 3) but applies equally to creative delay effects.

A simple 4-line FDN delay network:

```
Input → [Mixing Matrix] → 4 parallel delay lines → [Mixing Matrix] → Output
                         ↓
                   [Feedback loop]
```

Each delay line operates at a different rate. For 120 BPM, the four lines might be clocked at quarter, eighth, triplet eighth, and sixteenth tempos. The mixing matrix applies gain and pan coefficients:

```
Matrix:
[0.5   0.3  −0.2   0.1] [L1]
[0.2   0.6   0.1  −0.15] [L2]
[−0.1  0.15  0.7   0.2]  [L3]
[0.3  −0.1   0.15  0.5]  [L4]
```

The negative coefficients introduce phase cancellation, preventing buildup and creating textural richness. The feedback loop adds complexity: each tap's output re-enters the matrix, creating autocorrelation and complexity growth over time.

### BPM-to-Millisecond Synchronization Equations

Precise delay synchronization requires converting musical note durations to millisecond values. The formula is fundamental:

**Delay in milliseconds = (60 / BPM) × Beat_Fraction × 1000**

Common values at 120 BPM:
- Whole note: (60 / 120) × 4 × 1000 = 2000 ms
- Half note: (60 / 120) × 2 × 1000 = 1000 ms
- Quarter note: (60 / 120) × 1 × 1000 = 500 ms
- Eighth note: (60 / 120) × 0.5 × 1000 = 250 ms
- Sixteenth note: (60 / 120) × 0.25 × 1000 = 125 ms
- Triplet eighth: (60 / 120) × (1/3) × 1000 = 166.67 ms
- Dotted quarter: (60 / 120) × 1.5 × 1000 = 750 ms

At 100 BPM:
- Quarter note: (60 / 100) × 1 × 1000 = 600 ms
- Eighth note: (60 / 100) × 0.5 × 1000 = 300 ms

At 140 BPM:
- Quarter note: (60 / 140) × 1 × 1000 = 428.57 ms
- Sixteenth note: (60 / 140) × 0.25 × 1000 = 107.14 ms

When designing tempo-synced delay effects, these calculations become parameter values. A delay plugin with BPM input automatically computes these values internally; manual delay plugins require manual calculation. The precision matters: a 16th-note delay set to 110 ms instead of 107 ms will gradually drift out of phase with the track's grid, creating subtle but cumulative timing sloppiness.

---

## 3. Reverb Engine Mechanics: Algorithmic Feedback Delay Networks vs Convolution Impulse Responses

Reverb is not a single effect but a category of spatial processors that simulate acoustic reflections in enclosed spaces. Two primary reverb architectures dominate professional mixing: algorithmic reverbs (using mathematical delay networks and filtering) and convolution reverbs (using measured impulse responses). Understanding the underlying mechanics is essential for selecting the appropriate tool and achieving professional results.

### The Acoustics of Enclosed Spaces

When sound propagates in an enclosed room, it undergoes a predictable sequence of reflections. The first sound reaches the listener via the direct path. Shortly after (5–100 ms, depending on room size), discrete early reflections arrive—sound that bounced once or twice off room surfaces before reaching the listener. These early reflections convey spatial information: their timing patterns and frequency content encode the room's dimensions and acoustic properties.

Following the early reflections, a dense cloud of higher-order reflections arrives, each individual reflection becoming progressively harder to distinguish. This dense reflection field is the reverberation tail, characterized by exponential decay. The decay rate is quantified by the reverberation time, specifically RT60—the time required for the sound level to decay by 60 dB from the initial peak.

A small untreated room (3m × 4m × 2.5m) exhibits RT60 around 0.3–0.5 seconds; a concert hall (100m × 50m × 20m) exhibits RT60 of 2–3 seconds. The frequency dependence is critical: the same room exhibits different RT60 values at different frequencies. High frequencies decay faster due to air absorption and high-frequency absorption by materials; low frequencies decay slower due to room modes and low-frequency reflectance.

Typical professional reverb times for mixing:

| Reverb Type | RT60 (ms) | Application | Frequency Dependency |
|---|---|---|---|
| Plate reverb | 1.5–3 s (1500–3000 ms) | Drums, vocals, rock | Relatively flat; slight high-frequency decay |
| Room reverb | 0.2–0.6 s (200–600 ms) | Vocals, snare, acoustic instruments | Moderate; 3–6 dB/octave high-frequency rolloff |
| Hall reverb | 2–4 s (2000–4000 ms) | Orchestral, ambient, pads | Shallow; 1–3 dB/octave rolloff |
| Cathedral reverb | 4–8 s (4000–8000 ms) | Dramatic, cinematic, sparse | Deep; 4–8 dB/octave high-frequency decay |
| Spring reverb | 2–4 s (2000–4000 ms) | Surf, vintage rock, vocal color | Peak at ~200 Hz; noticeable coloration |

### Moorer and Dattorro Feedback Delay Network Topologies

Algorithmic reverbs generate reverb-like acoustic characteristics via mathematical constructs. The Moorer architecture (1979) and Dattorro topology (1997) represent the two dominant design paradigms, each with distinct sonic and computational characteristics.

**Moorer Reverb Architecture:**

The Moorer design employs parallel comb filters followed by series all-pass filters. The topology:

```
Input → [4 Comb Filters in Parallel] → [2 All-Pass Filters in Series] → Output
```

Each comb filter implements:

```
y(n) = x(n) + feedback * y(n − delay_samples)
```

where delay_samples corresponds to a musical note duration (typically 40–120 ms for a compact reverb). The feedback coefficient determines the RT60:

```
feedback = 10^(−3 * delay_ms / RT60_ms)
```

For a 60 ms comb delay with 2 second (2000 ms) RT60:

```
feedback = 10^(−3 * 60 / 2000) = 10^(−0.09) = 0.813
```

Four parallel combs at delays of 50, 60, 70, and 80 ms create early reflections with different characteristic frequencies (determined by the comb's resonance peaks). The sum of these four comb outputs is then processed by two series all-pass filters, typically at 5 ms and 1.7 ms delays.

All-pass filters introduce phase shift without changing magnitude:

```
y(n) = −x(n) + feedback * x(n − delay_samples) + feedback * y(n − delay_samples)
```

All-pass filters do not attenuate; they diffuse—spreading early reflections temporally, creating a denser reflection field. The series configuration creates cascading diffusion, improving the sense of acoustic space and reducing the "comb filter" coloration.

**Dattorro Reverb Architecture:**

The Dattorro topology employs a more complex FDN structure with cross-coupled delay lines and a unique early reflection section. The topology:

```
Input → [Input All-Pass] → [Early Reflection Matrix] → [Parallel FDN with 8 Delays] → Output
```

The input all-pass (typically 4 ms) initially diffuses the input signal. The early reflection matrix employs a specific mixing topology to generate the initial reflections, typically spanning 0–100 ms. The parallel FDN employs eight delay lines at carefully chosen lengths (23, 29, 37, 43, 47, 53, 59, 67 ms for a natural-sounding reverb) with cross-feedback via a unitary mixing matrix.

The unitary matrix ensures energy conservation—no net gain or loss across the network. A simple unitary matrix for 4 delay lines:

```
1/2 * [1   1   1   1]
      [1  −1   1  −1]
      [1   1  −1  −1]
      [1  −1  −1   1]
```

The Dattorro architecture produces exceptionally smooth, dense reverb tails with minimal audible periodicity or "flutter." The price is computational complexity: the architecture requires more operations per sample than Moorer design.

### All-Pass Filters, Diffusion, and Temporal Smearing

All-pass filters are the workhorses of professional reverb design. Unlike high-pass or low-pass filters that attenuate certain frequencies, all-pass filters preserve magnitude across the spectrum while introducing frequency-dependent phase shift. This property makes them ideal for temporal diffusion without tonal coloration.

An all-pass filter implementation in the frequency domain exhibits unity magnitude (|H(f)| = 1 across all frequencies) but phase that varies smoothly from 0° to −360° (or −180° depending on implementation). In the time domain, an all-pass impulse response produces a series of decaying reflections rather than a single spike.

For reverb design, the all-pass's diffusion characteristic is exploited to "smear" early reflections, preventing them from being audibly discrete. A single 5 ms all-pass applied to an impulse produces a series of reflections at approximately 5 ms, 10 ms, 15 ms, etc., each at decreasing amplitude. This temporal spreading is inaudible when applied to natural audio material, but the effect accumulates—each subsequent reflection becomes denser.

Series all-pass chains exhibit exponential diffusion growth. A single all-pass at 5 ms creates 5 ms spacing; two series all-passes at 5 ms and 1.7 ms create spacing that reduces to approximately 1.7 ms (the shortest delay dominates). Three series all-passes with delays of 5 ms, 1.7 ms, and 0.7 ms create spacing approaching 0.7 ms—sufficient to make the reflection field sound continuous rather than discrete.

The practical limit is computational cost. Each additional all-pass adds one multiply-accumulate operation per sample; at 48 kHz, a single all-pass demands 48,000 operations per second. Multiple all-passes and multiple delay lines scale rapidly.

### Damping Filters and Frequency-Dependent Decay

Real acoustic spaces do not exhibit flat frequency response in their reverb tails. High frequencies decay faster than low frequencies due to air absorption and material properties. Professional reverb algorithms implement this via frequency-dependent damping—typically a shelving filter applied within each delay line's feedback loop.

The damping filter is implemented as a first-order shelving low-pass:

```
y(n) = damping * y(n−1) + (1 − damping) * x(n)
```

where damping ranges from 0 (no filtering, flat response) to 0.9 (aggressive high-frequency attenuation). A damping value of 0.5 produces roughly 6 dB/octave high-frequency rolloff. A value of 0.8 produces roughly 15 dB/octave rolloff.

For a concert hall reverb with RT60 = 3 seconds at 1 kHz and desired 6 dB/octave high-frequency decay:

- 1 kHz RT60: 3000 ms (specified)
- 2 kHz RT60: 3000 − 6 dB attenuation rate per octave = approximately 2100 ms
- 4 kHz RT60: 4 dB down further = approximately 1200 ms
- 8 kHz RT60: approximately 600 ms

Implementation: increase the damping coefficient in the feedback loop from 0.3 (flat response) to 0.6 (aggressive rolloff). Each delay line's output is filtered before feedback, progressively reducing high-frequency energy.

### Convolution Impulse Responses and Partition Convolution

Convolution reverbs operate from a fundamentally different principle: they capture the exact impulse response of a real acoustic space (or carefully designed synthetic response) and mathematically convolve the input signal with that response. The impulse response is a time-domain representation of exactly how a space responds to a brief impulse—it captures all reflections, diffusion, and decay characteristics.

The convolution operation is defined as:

```
y(n) = Σ h(k) * x(n − k) for k = 0 to N−1
```

where h(k) is the impulse response (typically 1–20 seconds of audio), x(n) is the input signal, and y(n) is the output. This is a direct time-domain convolution, requiring N multiply-accumulate operations per output sample, where N is the impulse response length.

For a 2-second impulse response at 48 kHz, N = 96,000 samples. Direct convolution requires 96,000 MACs per output sample—approximately 4.6 billion operations per second for real-time processing at 48 kHz. This is computationally prohibitive for multiple instances or additional processing.

**Partition Convolution** solves this via FFT-based processing. The impulse response is divided into partitions (typically 512–4096 samples each), and each partition is transformed to the frequency domain via FFT. The incoming audio is processed in blocks, transformed to the frequency domain, multiplied by each partition's FFT (frequency-domain multiplication replaces time-domain convolution), and the results are inverse-transformed and overlap-added.

Partition convolution reduces computational cost from O(N) to O(log N) per sample, making real-time multi-channel convolution reverb practical on modern hardware.

**Impulse Response Characteristics:**

A high-quality convolution reverb impulse response exhibits:

1. **Direct sound**: The first 2–5 ms contains the direct path response, typically a sharp transient.
2. **Early reflections**: 5–100 ms region shows discrete reflections from nearby surfaces, highly space-specific.
3. **Dense reflection field**: 100–500 ms region exhibits progressively denser, shorter reflections.
4.

**Reverb tail**: The exponential decay region beyond 500 ms where modal density becomes so high that individual reflections are indistinguishable, governed by the Sabine or Eyring equations. The tail's decay profile (RT60) is determined by room volume and surface absorption, with large spaces exhibiting longer, smoother decays. High-quality impulse responses maintain spectral coherence throughout the decay—realistic spaces show frequency-dependent absorption where high frequencies decay faster than lows due to air absorption and surface material properties. A 5-second tail at 48 kHz represents 240,000 samples; partition convolution with 2048-sample blocks reduces this to approximately 117 FFT operations per block (forward, per-partition multiply, inverse), yielding ~2.7 million operations per second versus 11.5 billion for direct convolution—a 4,200× efficiency gain that enables real-time stereo or multichannel operation.

The distinction between algorithmic and convolution reverb is fundamental: algorithmic designs offer parametric control, low CPU cost, and creative flexibility but produce synthetic spatial signatures with periodic artifacts and limited naturalism. Convolution reverb provides absolute acoustic fidelity to the captured space but consumes significantly more resources and offers limited real-time manipulation beyond level, pre-delay, and basic EQ. Modern production typically employs hybrid approaches—algorithmic reverbs for creative effects, exaggerated spaces, and automation-intensive contexts; convolution for photorealistic room emulation, matching production to acoustic environments, and post-production audio-for-picture work. High-end implementations combine both: convolution for early reflections (spatial signature) with algorithmic tails (modulation, parameter control), balancing authenticity with creative malleability while maintaining computational efficiency across dozens of simultaneous instances in contemporary DAW sessions.

## Summary & Verification Matrix

| Domain | Governing Invariant | Core Mechanism | Diagnostic Criteria |
|--------|-------------------|----------------|---------------------|
| **Algorithmic Reverb** | Recirculation creates exponential decay; feedback < 1.0 ensures stability; comb filters require all-pass diffusers to break periodicity | Feedback delay networks (FDN) with unitary matrices, nested all-pass chains, or hybrid architectures route signal through delay lines with frequency-dependent absorption | Periodic comb artifacts = insufficient diffusion; metallic resonance = modal buildup from integer-ratio delays; rapid density collapse = inadequate network complexity (< 8 delay lines or < 4 nested all-passes) |
| **Convolution Reverb** | Impulse response h(k) fully defines space response; y(n) = Σ h(k)·x(n−k); partition FFT reduces O(N) → O(log N) complexity | Direct capture or synthetic IR divided into 512–4096 sample partitions, frequency-domain multiplication per partition, overlap-add reconstruction | Static spatial signature (no modulation) confirms true convolution; CPU load scales with IR length (~96k samples = 2s at 48kHz); pre-ringing in output = acausal IR artifacts or improper windowing |
| **Delay Networks (FDN)** | Hadamard/Householder matrices ensure energy conservation; eigenvalues on unit circle prevent gain/loss; delay coprimality breaks periodicity | N×N unitary feedback matrix routes N delay outputs to N inputs with orthogonal mixing, preserving total energy while maximizing decorrelation | Spectral uniformity across 20Hz–20kHz confirms orthogonal mixing; time-domain correlation < 0.1 between channels verifies decorrelation; gain stability ±0.1 dB over 10s confirms unitarity |
| **Stereo Imaging** | Inter-channel correlation ρ ∈ [−1, +1]: ρ=1 (mono), ρ=0 (uncorrelated), ρ=−1 (out-of-phase); Haas precedence (< 35ms) preserves fusion; ITD/ILD encode direction | Haas-zone early reflections (5–35ms) with decorrelated tails; complementary comb filters or Gerzon vector processing for width; M/S encoding for independent center/side control | Goniometer phase scope shows ±45° spread for natural width, > ±60° risks mono collapse; stereo correlation meter 0.3–0.7 = spacious but compatible; mono sum null-test reveals destructive interference from excessive decorrelation |
| **Temporal Architecture** | Pre-delay 0–100ms separates direct sound from reverb onset; early/late crossover 50–150ms defines spatial intimacy vs. size; RT60 defines perceived volume | Pre-delay → early reflections (< 100ms, spatial signature) → dense field (100–500ms) → exponential tail (> 500ms, decay time); frequency-dependent absorption via shelving filters in feedback paths | Pre-delay < 20ms = tight integration; 40–80ms = natural room; > 100ms = obvious separation; RT60 ratio (HF/LF) < 0.5 = dark/distant, > 0.8 = bright/close; early reflection density > 1000 reflections/sec at 100ms confirms adequate diffusion |
| **Computational Efficiency** | Direct convolution O(N) MACs/sample; FFT convolution O(log N); algorithmic FDN constant cost regardless of decay time | Partition convolution: block size B, IR length L → (L/B) FFTs per block; algorithmic: fixed delay RAM + matrix multiply per sample | Real-time factor (RTF) < 0.3 sustainable for 64+ instances; convolution: 2s IR @ 48kHz with 2048-sample blocks ≈ 2.7M ops/sec; FDN: 8 delays + 8×8 Hadamard ≈ 0.15M ops/sec; latency = block size (512 samples = 10.7ms @ 48kHz) |
