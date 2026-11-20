# Operational Verification Labs: Color Theory

## Objective & DAW / Studio Setup

Color theory for the audio practitioner operates at the intersection of visual perception, psychoacoustics, and compositional architecture. While music production traditionally concerns itself with frequency response, dynamics, and spatial imaging, the principles of color theory—hue, saturation, value, and harmony—provide a profound conceptual framework for understanding timbral balance, emotional resonance, and sonic aesthetics in mixed and mastered work.

This laboratory sequence bridges visual color science with audio production methodology. You will learn to perceive timbre as *sonic color*, apply classical color harmony relationships to orchestration and synthesis, and develop diagnostic skills to verify harmonic balance, spectral distribution, and perceived loudness across your mixing environment. The exercises assume you operate within a professional digital audio workstation (Ableton Live, Logic Pro, or Reaper) with a calibrated monitoring chain: flat-response studio monitors (±3 dB from 20 Hz to 20 kHz), acoustic treatment to eliminate room modes below 200 Hz, and a secondary verification system (headphones or portable monitors for A/B validation across listening environments).

Before beginning, establish your studio environment according to the following specifications. Position your monitors at ear level, forming an equilateral triangle with your listening position. Measure the distance from each monitor to your ears: optimal placement occurs between 1.5 and 2.5 meters. Ensure your mixing position sits at least 0.5 meters from rear walls to minimize bass buildup from boundary reinforcement. Install bass traps (porous absorbers, 4–6 inches thick) in room corners to control resonances below 250 Hz. Verify monitor calibration by feeding a 1 kHz sine wave at –20 dBFS through your audio interface and measuring with a sound pressure level (SPL) meter set to C-weighting: target 85 dB SPL at your listening position, representing a neutral reference point. If your room lacks calibration equipment, use a pink noise reference track and adjust monitor levels so that speech-range content (roughly 2–4 kHz) feels neither fatiguing nor buried.

Open your DAW and create a new session at 44.1 kHz, 24-bit resolution (matching standard streaming delivery specifications). Create four stereo tracks: **Composition Base** (for MIDI orchestration), **Synthesis Lab** (for timbre exploration), **Mixing Reference** (for spectral analysis and diagnostic metering), and **Master Bus** (for loudness verification and final mastering simulation). Insert a spectrum analyzer plugin (Voxengo SPAN or your DAW's native frequency analyzer) on the Master Bus output. This will serve as your primary diagnostic instrument throughout all exercises.

---

## Exercise 1: Practical Composition & Voice-Leading Realization

### Part A: Mapping Color Harmony to Orchestration

The perceptual relationship between visual hue and sonic timbre rests on a fundamental principle: both represent harmonic complexity and spectral distribution. A warm color—deep orange or amber—exhibits energy concentrated in the low to mid frequencies of visible light's spectrum; analogously, a warm timbre (oboe, French horn, warm pad synthesis) concentrates acoustic energy in the fundamental and lower harmonics. A cool color—cyan or violet—scatters energy across higher wavelengths; a cool timbre (bright trumpet, high string harmonics, filtered white noise) emphasizes upper partials and sibilance. This correspondence is not metaphorical but perceptually grounded: the retina's cone cells respond to wavelength distributions that parallel the basilar membrane's frequency decomposition in the inner ear.

Classical color harmony systems—complementary, analogous, triadic, and tetradic relationships—map directly onto orchestral voice-leading principles and spectral mixing strategy. Begin by composing an eight-bar harmonic progression in F major, deliberately structured to explore these relationships.

Open your **Composition Base** track and insert a software instrument capable of realistic MIDI expression: Spitfire Audio's BBCSO Core (which offers immediate timbral variety), Native Instruments Komplete, or your DAW's native orchestral library. Create the following harmonic progression over eight bars, each bar spanning a whole note:

```text
Bar 1: F major (F–A–C)
Bar 2: D minor (D–F–A) [vi chord]
Bar 3: B♭ major (B♭–D–F) [IV chord]
Bar 4: F major (F–A–C) [I chord]
Bar 5: G minor (G–B♭–D) [ii chord]
Bar 6: E♭ major (E♭–G–B♭) [VI chord – modal interchange]
Bar 7: D minor (D–F–A) [vi chord]
Bar 8: F major (F–A–C) [I chord]
```

Program each chord as a half-note figure across three voices: root in the bass (C2 octave), third in the tenor (approximately middle C to G4), and fifth in the soprano (one octave above the root's octave). Use a legato articulation with zero attack time and a gentle release tail (approximately 200–300 milliseconds). This voice-leading structure creates smooth, stepwise motion without jarring leaps—precisely analogous to an analogous color harmony in visual design, where neighboring hues blend without harsh contrast.

Now, assign *warm-spectrum timbres* (oboe, French horn, warm pad) to the bass and tenor voices, and a *cool-spectrum timbre* (bright violin, flute, crystalline pad) to the soprano. The result mirrors a triadic color harmony: the warm foundation anchors perceptual weight and emotional grounding, while the cool soprano provides visual (sonic) brightness and focal attention. Listen to this progression across multiple iterations, adjusting MIDI velocities so that the bass sits at 70 LUFS, the tenor at 65 LUFS, and the soprano at 60 LUFS—creating a dynamic hierarchy that mirrors visual depth (darker tones receding, brighter tones advancing).

### Part B: Complementary Harmony & Spectral Tension

Complementary color pairs (red–cyan, yellow–blue, magenta–green) create maximum visual contrast and perceptual tension. In orchestration, this translates to frequency-domain opposition: pairing instruments whose spectral centroids (the frequency at which half the energy lies above and below) are maximally separated.

Extend your composition by inserting a new four-bar section immediately following bar 8. Create a *complementary harmonic tension* by introducing a secondary chord progression that sits outside the F major diatonic collection:

```text
Bar 9: F major (F–A–C) [original I chord]
Bar 10: D♭ major (D♭–F–A♭) [tritone substitution of the V chord]
Bar 11: B major (B–D♯–F♯) [chromatic mediant, maximum distance from F]
Bar 12: F major (F–A–C) [resolution]
```

Orchestrate this progression with maximum spectral opposition: assign the F major and D♭ major chords (bars 9–10) to deep, low-register instruments (contrabass, tuba, 32-foot organ pedal synthesized with a square wave filtered to 60 Hz center frequency). Assign the B major chord (bar 11) to the highest-register instruments available: piccolo, glockenspiel, or a bright digital pad with a 6 kHz spectral peak. The tritone substitution in bar 10 creates harmonic instability that resolves through the maximum contrast in bar 11, generating perceptual tension precisely analogous to placing a bright cyan shape adjacent to a deep red ground in visual composition.

Import a spectrum analyzer plugin onto your Master Bus. As you play back this progression, observe the energy distribution. During bars 9–10, the analyzer should display dominant energy below 250 Hz (bass-dominated). During bar 11, energy should concentrate in the 4–8 kHz range (presence peak). This spectral oscillation is *audible color shift*—the tonal palette literally changes across the bar-level harmonic progression.

### Part C: Analogous Harmony & Spectral Cohesion

Analogous color harmonies (neighboring hues: yellow, yellow-green, green) create visual unity and perceptual coherence. In sonic terms, analogous harmony emerges when multiple voices occupy overlapping frequency ranges with non-conflicting partials—they blend seamlessly rather than contrasting.

Compose a new eight-bar passage using exclusively the following instruments: viola (warm, mid-range), English horn (darker oboe, overlapping upper-mid frequencies), and a warm pad synthesized with a complex sawtooth wave filtered to a 1 kHz center with moderate resonance (Q ≈ 4). All three instruments occupy the frequency range between approximately 200 Hz and 3 kHz. Construct the harmonic progression as a diatonic sequence in G major:

```text
Bar 1: G major (G–B–D)
Bar 2: E minor (E–G–B)
Bar 3: A minor (A–C–E)
Bar 4: D major (D–F♯–A)
Bar 5: G major (G–B–D)
Bar 6: C major (C–E–G) [modal mixture]
Bar 7: E minor (E–G–B)
Bar 8: G major (G–B–D)
```

Arrange each chord as a three-voice stack: viola on the root (G3 octave), English horn on the third (one octave higher), warm pad on the fifth (one octave above the English horn). Ensure minimal motion between bars—each voice should step by no more than a major second between successive chords. This creates an analogous harmonic color: perceptually warm, cohesive, and emotionally unified. The spectrum analyzer will show consistent energy distribution across the progression; there are no sudden frequency-domain shifts.

---

## Exercise 2: Timbre Synthesis, Waveform Shaping & Modulation Routing

### Part A: Additive Synthesis & Harmonic Color Construction

Timbre—the perceived "color" of a sound—is fundamentally defined by the amplitude envelope of each harmonic partial. A clarinet, which produces sound by vibrating a reed coupled to a cylindrical resonator, naturally emphasizes odd-numbered harmonics (1st, 3rd, 5th, 7th...); its spectrum appears as alternating peaks and nulls. A piano string, struck with a hammer, excites all harmonics nearly equally, resulting in a bright, spectrally rich timbre. Additive synthesis—the mathematical superposition of sinusoidal components at specific frequencies and amplitudes—allows direct control over timbre by sculpting the harmonic profile.

Open your **Synthesis Lab** track and insert a wavetable synthesizer capable of additive harmonic editing (Native Instruments Massive X, Serum, or your DAW's native synth). Create a custom wavetable representing a warm, clarinet-like timbre by programming the following harmonic series:

```text
Harmonic 1 (fundamental): Amplitude 1.0 (0 dB)
Harmonic 3 (3rd partial): Amplitude 0.7 (–3 dB)
Harmonic 5 (5th partial): Amplitude 0.4 (–8 dB)
Harmonic 7 (7th partial): Amplitude 0.25 (–12 dB)
Harmonic 9 (9th partial): Amplitude 0.15 (–17 dB)
All even harmonics: Amplitude 0 (muted)
```

This harmonic profile—odd-only, descending amplitude—produces a mellow, warm timbre similar to a clarinet. Set the synth's attack time to 50 milliseconds (simulating the reed's initial transient), sustain to full amplitude, and release to 300 milliseconds. Transpose the synth one octave below your Composition Base track and play the same F major progression from Exercise 1, Part A, using only this synthesized timbre. The result should sound noticeably warmer, less spectrally aggressive than the orchestra library instruments.

Now, create a second wavetable representing a *bright, cool timbre* by programming this harmonic profile:

```text
Harmonic 1 (fundamental): Amplitude 1.0 (0 dB)
Harmonic 2 (1st overtone): Amplitude 0.6 (–4 dB)
Harmonic 3 (3rd partial): Amplitude 0.8 (–2 dB)
Harmonic 4 (2nd overtone): Amplitude 0.5 (–6 dB)
Harmonic 5 (5th partial): Amplitude 0.7 (–3 dB)
Harmonic 6 (3rd overtone): Amplitude 0.4 (–8 dB)
Harmonic 7 (7th partial): Amplitude 0.6 (–4 dB)
Harmonic 8 (4th overtone): Amplitude 0.3 (–10 dB)
Harmonics 9–16: Amplitude 0.2–0.1 (–14 to –20 dB, descending)
```

This profile—all harmonics present, extended high-frequency content—produces a bright, crystalline timbre resembling a bell or bright synthesizer pad. Set the attack to 200 milliseconds (slower onset), sustain to full amplitude, and release to 500 milliseconds (longer decay tail, simulating bell resonance).

Play the same progression using this bright timbre. Notice the perceptual shift: the timbre occupies more frequency space, feels "shinier," and commands more attention. Alternate between the two timbres on successive bars of your progression, observing how timbre change alone can convey harmonic color shift independent of actual pitch content.

### Part B: Subtractive Synthesis & Filter Envelope Modulation

Subtractive synthesis—the inverse of additive synthesis—begins with a spectrally rich waveform (sawtooth, square, or white noise) and sculpts timbre by removing energy through filtering. The filter's center frequency, resonance (Q), and envelope automation control timbre evolution across the note's duration, enabling dynamic color change.

Insert a second instance of your wavetable synth on the **Synthesis Lab** track. Select a raw sawtooth waveform, which naturally contains all harmonics (1–∞) at equal amplitude. Insert a 24 dB per octave low-pass filter (Moog ladder topology, if available) immediately post-oscillator.

Set the filter's cutoff frequency to 2 kHz (a bright but not aggressive setting) and resonance to Q = 4 (moderate peak at the cutoff, enhancing the filter's "character"). Play a single sustained F3 note at full velocity. Observe the spectrum analyzer: the sawtooth's harmonics extend well beyond the Nyquist limit (22.05 kHz at 44.1 kHz sample rate), but the filter attenuates everything above approximately 2 kHz, creating a warm, rounded timbre similar to a horn.

Now, create a filter envelope that modulates the cutoff frequency across the note's duration:

- **Attack (0–200 ms):** Cutoff sweeps from 500 Hz to 4 kHz, creating a "whoosh" effect as brightness increases during the note onset.
- **Decay (200–800 ms):** Cutoff slides from 4 kHz to 2 kHz, introducing warmth as the note stabilizes.
- **Sustain (800 ms onward):** Cutoff holds at 1.5 kHz, creating a smooth, settled timbre.
- **Release (note off to 500 ms after):** Cutoff slides from 1.5 kHz to 300 Hz, darkening the note as it fades.

Program this envelope into your synth's filter modulation. Play the same F major progression from Exercise 1, using a legato trigger so each note flows without retriggering the synth. As you play, the timbre should transition from bright to warm to dark, mimicking a visual color gradient from cool (bright attack) through neutral (decay/sustain) to warm (release). Listen carefully: this dynamic timbre evolution is the sonic equivalent of watching a color shift from cyan through neutral gray to deep orange.

### Part C: Wavetable Morphing & Frequency Modulation

Extend timbral control by morphing between multiple wavetable morphs—a technique that interpolates between two or more discrete waveforms in real time. This creates a flowing, organic timbre evolution impossible with static waveforms.

In your synth, create three distinct wavetable snapshots:

1. **Harmonic Profile A (warm, thin):** Harmonics 1, 3, 5 only (odd harmonics, descending amplitude).
2. **Harmonic Profile B (neutral, full):** Harmonics 1–8 with equal amplitude.
3. **Harmonic Profile C (bright, extended):** Harmonics 1–16 with descending amplitude envelope (each harmonic reduced by –2 dB relative to the previous).

Assign a low-frequency oscillator (LFO) at 0.5 Hz (one complete cycle every two seconds) to modulate the wavetable morphing parameter. Set the morphing to cycle continuously through A → B → C → B → A across each two-second cycle. As the cycle progresses, you will hear the timbre shift from warm-and-thin through full-and-neutral to bright-and-extended, then back through neutral to warm. This is dynamic color in real time—the sonic equivalent of watching colors cycle through a visual spectrum.

Overlay this morphing synth beneath your orchestral composition from Exercise 1. The result is a rich timbral landscape where primary voices (orchestra) provide harmonic structure and secondary voices (morphing synth) provide continuous, evolving color texture.

---

## Exercise 3: Dynamic Mixing, Spectrum Analysis & Audio Stress Testing

### Part A: Building Spectral Balance & Frequency-Domain Orchestration

Professional mixing rests on controlling the frequency-domain distribution of energy across the entire mix. An unbalanced mix concentrates energy in narrow frequency bands, resulting in "muddy" low-mids, "honky" mid-range, or "fatiguing" high-frequency emphasis. Spectral balance—the even, musically appropriate distribution of energy—ensures clarity, perceived loudness, and tonal coherence.

Open your **Mixing Reference** track and create a composite audio arrangement combining all material from Exercises 1 and 2:

- Orchestral composition (Exercise 1): Bass and tenor voices on dedicated tracks, soprano on a separate track.
- Warm synthesized timbre (Exercise 2, Part A): One track.
- Bright synthesized timbre (Exercise 2, Part A): One track.
- Subtractive synth with filter envelope (Exercise 2, Part B): One track.
- Morphing wavetable synth (Exercise 2, Part C): One track.

Pan the orchestral bass track hard left (–90°), tenor center, soprano hard right (+90°). This creates a spatial image that mirrors visual composition: low frequencies (bass) occupy lateral space, mid-frequencies (tenor) provide central anchor, high frequencies (soprano) spread across the stereo field. Pan the synthesis tracks as follows: warm synth center, bright synth slightly right (+30°), subtractive synth slightly left (–30°), morphing synth full width using mid-side processing (centered fundamentals with spread overtones).

Insert a spectrum analyzer on your Master Bus. Begin playback of your composite arrangement. The analyzer should display a relatively even energy distribution across the frequency spectrum, roughly following an inverse power law (lower frequencies contain more energy, but not excessively so—approximately –3 dB per octave descent below 500 Hz). If the mix shows energy "peaks" (narrow frequency bands with 6+ dB more energy than adjacent frequencies), those frequencies are likely problematic.

To diagnose frequency imbalance, use a parametric equalizer on your Master Bus. Insert a 3-band parametric EQ with the following settings:

- **Low Band (100 Hz, Q = 0.7, Gain = 0 dB initially):** Set this to a high-pass filter with 12 dB per octave slope, leaving the 100 Hz center frequency untouched but removing everything below approximately 40 Hz (subsonic rumble that consumes mix energy without audible benefit).
- **Mid Band (1 kHz, Q = 1, Gain = 0 dB initially):** Leave as reference; this band typically anchors the mix tonality.
- **High Band (8 kHz, Q = 0.7, Gain = 0 dB initially):** Monitor this band for excessive presence-peak energy that can cause listening fatigue.

As you listen to the mix, observe the spectrum analyzer. If energy concentrates around a specific frequency, use the parametric EQ to surgically reduce that frequency by introducing a notch (Q = 4–6, Gain = –3 to –6 dB) centered on the problematic frequency. For example, if the analyzer shows a 5 dB peak at 2 kHz, insert a parametric notch: Center = 2 kHz, Q = 5, Gain = –4 dB. Solo the orchestral bass track and verify that the notch predominantly affects that track; if not, adjust the notch parameters.

Iterate this process across all tracks until the Master Bus spectrum analyzer displays a smooth, descending frequency response with no prominent peaks or nulls. This process—frequency-domain orchestration—is the mixing equivalent of balancing a visual composition's color palette. Just as a painting with too much red in one corner feels visually unbalanced, a mix with excessive 2 kHz energy feels tonally unbalanced.

### Part B: Loudness Metering & LUFS-Based Mix Verification

Perceived loudness is not linear with physical amplitude; the human ear is less sensitive to very low and very high frequencies, and perceived loudness follows a logarithmic relationship with sound pressure level (the "equal loudness contours" or Fletcher-Munson curves). Modern loudness metering uses the LUFS (Loudness Units relative to Full Scale) standard, which weight frequency perception according to human hearing sensitivity and integrate loudness across time (typically using a 3-second sliding window for short-term LUFS or 60-second for integrated LUFS).

Insert a loudness meter plugin on your Master Bus (Waves WLM Plus, MeterPlugs NUGEN loudness meter, or your DAW's native loudness meter). Set the meter to display integrated LUFS (long-term average), short-term LUFS (3-second rolling window), and true-peak value (the maximum unclipped digital value across all samples). Configure the metering for streaming delivery targets: Integrated LUFS = –14 LUFS (Spotify, YouTube, Apple Music standard), Short-term LUFS no higher than –11 LUFS (preventing abrupt loudness jumps), True-peak no higher than –1 dBTP (leaving 1 dB headroom to prevent clipping during sample-rate conversion or transcoders).

Play back your composite arrangement and monitor the loudness meter throughout. The integrated LUFS should stabilize around –16 to –18 LUFS during sustained passages (providing ≈2–4 LUFS headroom below the –14 LUFS target, accommodating peaks without clipping). If your mix runs hotter than –12 LUFS integrated, reduce Master Bus fader by 3 dB and verify that no individual track clips (check your DAW's clipping indicators). If your mix runs cooler than –20 LUFS integrated, increase individual track levels to bring closer to target, ensuring that no single track exceeds 0 dBFS peak.

Once loudness targets are met, verify spectral balance a second time using the spectrum analyzer. Loudness normalization can mask frequency imbalances; a mix that sounds balanced at –16 LUFS might reveal problematic peaks when normalized to –14 LUFS. Iterate EQ adjustments until both loudness and spectral balance meet target specifications.

### Part C: Stereo Width, Spatial Imaging & Cross-Frequency Coherence

Stereo imaging—the perception of sound sources positioned across the left-right stereo field—enhances perceived loudness, creates spatial interest, and prevents listening fatigue by distributing energy across multiple spatial channels rather than concentrating all energy in mono (center channel only).

Insert a mid-side (M/S) analyzer plugin on your Master Bus (Voxengo SPAN offers M/S analysis mode). This tool decomposes your stereo signal into mid (mono-compatible, left+right summed) and side (stereo difference, left–right) components. A healthy stereo mix should maintain consistent M/S ratio across the frequency spectrum: the mid component should dominate (ensuring mono compatibility—no phase cancellation when played back on mono systems), while the side component provides spatial width without destabilizing the image.

Configure your M/S analyzer to display both mid and side energy in dB across the spectrum. Ideal specifications are:

- **Low frequencies (20–200 Hz):** Predominantly mid (side energy ≤ –20 dB relative to mid) to maintain stable low-end imaging and prevent phase cancellation issues that destabilize bass on mono playback.
- **Mid frequencies (200 Hz–5 kHz):** Mixed mid and side (side energy ≈ –6 to –12 dB relative to mid) to provide stable vocal and harmonic imaging.
- **High frequencies (5–20 kHz):** Balanced mid and side (side energy ≈ –3 to –9 dB relative to mid) to maintain perceived stereo width while preserving presence-peak clarity.

If your mix shows excessive side energy in the low frequencies (bass sounds "wide" and unstable), insert an M/S matrix tool (many DAWs include this as a utility plugin) and apply a high-pass filter to only the side channel: cutoff frequency 200 Hz, 12 dB per octave slope. This removes stereo information from low frequencies while preserving mid-band and high-frequency stereo width.

As you verify M/S balance, simultaneously check your spectrum analyzer and loudness meter. The goal is simultaneous optimization across three dimensions: spectral balance (no frequency peaks), loudness compliance (–14 LUFS target), and stereo coherence (appropriate M/S ratio across frequency bands).

### Final Integration and Verification Protocol

Once M/S balance is established, perform a final integrated verification pass that unifies all three measurement domains. Play back your reference audio through your calibrated monitoring chain while simultaneously observing spectrum analyzer, loudness meter, and M/S analyzer. The hallmark of a professionally balanced mix is convergence: spectral balance shows no frequency-band deviations exceeding ±3 dB from your reference curve, integrated loudness stabilizes within ±0.5 LUFS of your –14 LUFS target, and M/S ratios remain within specified ranges across all frequency bands. If any single metric fails, diagnose the root cause systematically: spectral peaks indicate EQ correction needs, loudness overshoot indicates gain-staging errors, and M/S imbalance indicates stereo-field processing issues. Iterate corrections one dimension at a time, re-verify after each adjustment, and document your correction chain (plugin order, settings, bypass states) to establish a repeatable workflow. The verification process is complete only when all three measurement systems simultaneously confirm compliance for a minimum of 30 seconds of representative program material—this duration ensures transient events, dynamic passages, and sustained harmonic content all meet specifications.

This integrated approach mirrors professional mastering engineering practice: measurements are not isolated checkpoints but interdependent verification layers that collectively validate perceptual balance, technical compliance, and commercial viability. By maintaining calibrated measurement tools, reference audio benchmarks, and systematic verification protocols, you establish an objective foundation beneath subjective mixing decisions—ensuring that creative choices translate reliably across playback systems while meeting industry loudness and format specifications. The measurement-driven workflow does not replace critical listening but augments it, providing quantitative confirmation that your perceptual judgments produce technically sound, commercially competitive results.

## Summary & Verification Matrix

| Domain | Governing Invariant | Core Mechanism | Diagnostic Criterion | Failure Mode & Correction |
|--------|---------------------|----------------|---------------------|---------------------------|
| **Spectral Balance** | Frequency energy must match reference curve within ±3 dB across 20 Hz–20 kHz | FFT-based spectrum analyzer with 1/3-octave smoothing and reference overlay | Visual deviation from reference curve; peak energy >3 dB indicates resonance or EQ error | Excess bass: high-pass filter at 80–120 Hz; muddy mids: cut at 200–500 Hz; harsh highs: shelving cut above 8 kHz |
| **Loudness Compliance** | Integrated loudness must achieve –14 LUFS ±1 LU with true peak ≤ –1 dBTP | ITU-R BS.1770-4 compliant loudness meter measuring integrated, short-term, and true peak simultaneously | Integrated LUFS reading after 30+ seconds of program material; short-term meter shows dynamic range utilization | Under-target: apply makeup gain post-processing; over-target: reduce master fader or compressor makeup gain; true peak violations: apply true-peak limiter |
| **M/S Stereo Coherence** | Low frequencies (20–200 Hz) must be predominantly mono (side ≤ –20 dB); high frequencies maintain width (side ≈ –3 to –9 dB) | M/S matrix decomposition separating mid (L+R) and side (L–R) components with frequency-dependent analysis | M/S analyzer shows side energy relative to mid across frequency bands; phase correlation meter confirms mono compatibility | Excessive low-frequency side: high-pass filter side channel at 200 Hz; insufficient width: add side-channel presence boost above 5 kHz; phase cancellation: check for polarity inversion |
| **Dynamic Range Preservation** | Loudness range (LRA) must remain ≥6 LU to prevent over-compression; PLR (peak-to-loudness ratio) ≥9 dB maintains transient clarity | Loudness range measurement tracks difference between 10th and 95th percentile loudness over program duration | LRA readout on loudness meter; PLR calculated as (true peak dBTP – integrated LUFS) | LRA < 6 LU: reduce compression ratio or increase threshold; PLR < 9 dB: reduce limiter gain reduction or increase attack time to preserve transients |
