# Operational Verification Labs: DaVinci Resolve

## Objective & Studio Setup

DaVinci Resolve occupies a unique dual role in the modern audio-visual production ecosystem: it functions simultaneously as a professional color grading and editorial platform and as an increasingly capable audio postproduction and mixing environment. For music composers, producers, and audio practitioners, Resolve's audio capabilities extend far beyond simple dialogue cleanup or foley synchronization. The Fairlight audio engine embedded within Resolve provides professional-grade mixing, real-time plugin processing, spectral analysis, and time-stretching workflows that rival dedicated DAWs when properly understood and configured.

This operational verification sequence assumes you are working with a completed video project—either raw footage from live performance, music video content, or orchestral recording sessions—and that your objective is to score, mix, and deliver broadcast-quality audio aligned to picture. Unlike mixing in a traditional DAW where the timeline exists as an abstract grid, Resolve's Fairlight mixing environment anchors every creative decision to visual reference. This constraint becomes an asset: you are forced to make mixing and orchestration choices that serve narrative clarity, emotional arc, and visual rhythm simultaneously.

Before beginning these labs, establish your studio environment with the following specifications. Your monitoring chain should consist of calibrated near-field reference monitors (Genelec 8030 or equivalent, positioned at ear level in an equilateral triangle 1.5 meters from your listening position) with acoustic treatment meeting the ITU-R BS.1116 standard for critical listening. Your interface should support at least 24-bit/96 kHz I/O with stable ASIO (Windows) or CoreAudio (macOS) drivers. For diagnostic instrumentation, you will need a spectrum analyzer plugin (Voxengo SPAN or Native Instruments Komplete Audio 2's built-in analyzer), a loudness meter compliant with ITU-R BS.1770 (Youlean Loudness Meter or Nuendo's integrated loudness display), and MIDI monitoring capability if synchronizing external instruments.

Install DaVinci Resolve Studio (paid version required for Fairlight professional features; the free version lacks critical tools for this workflow). Create a dedicated project folder with the following structure:

```text
Project_Name/
├── Video/
│   └── source_footage.mov (ProRes 422 HQ or DNxHR HQX, minimum)
├── Audio/
│   ├── Stems/
│   │   ├── dialogue.wav
│   │   ├── ambience.wav
│   │   ├── music.wav
│   │   └── effects.wav
│   └── Reference/
│       └── broadcast_reference_mix.mp3
├── Exports/
│   ├── Stereo_Delivery_-5.1dB_LUFS.mov
│   ├── 5.1_Surround_-23_LUFS.mov
│   └── Stems_Individual/
└── Project_Files/
    └── resolve_project.drp
```

Load your video source into a new DaVinci Resolve project at 24 fps (or your project's native frame rate) and set your session to 48 kHz sample rate. The 48 kHz standard exists because it provides sufficient headroom above the Nyquist limit (24 kHz) while maintaining practical file sizes and computational overhead. Set your project's bit depth to 24-bit; while 32-bit floating-point mixing provides theoretical advantages in accumulation of rounding errors, the practical audible difference between 24-bit and 32-bit mixing on modern interfaces is negligible, and 24-bit reduces CPU load significantly.

---

## Exercise 1: Practical Composition & Voice-Leading Realization with Picture Lock

This exercise requires you to compose original underscore (background music) synchronized to a locked picture cut. The discipline of composing to picture forces you to make orchestration and arrangement decisions within explicit temporal and dramatic constraints, a skill that transfers directly to live performance preparation and instrumental balance in ensemble writing.

### Stage 1A: Spotting Session & Narrative Mapping

Open your video project and perform a spotting session—a deliberate, uninterrupted viewing of the entire cut while making real-time notes about where music should enter, where it should support silence, and where emotional intensity should peak. This is not an abstract exercise; you will make concrete decisions about orchestration based on visual rhythm.

Import your locked picture to the Media pool (File > Import Media). Drag the video clip to the Fairlight timeline, establishing it as your reference layer. Set the in-point and out-point to your total project duration using the keyboard shortcut I (in-point) and O (out-point). Resolve will display timecode overlays; use these to log every beat, cut, and emotional transition.

Create a detailed written spotting chart. For a three-minute commercial spot or music video, your chart should identify at minimum six distinct sections: (1) the opening hook (0–8 seconds), (2) establishing underscore during introduction of character or product (8–35 seconds), (3) an emotional peak or climactic moment (35–90 seconds), (4) resolution or callback to opening theme (90–120 seconds), (5) final emotional beat (120–150 seconds), and (6) credits or fade (150–180 seconds). For each section, specify the orchestration intention: Is this sparse and intimate (solo cello or solo piano) or lush and triumphant (full ensemble)? Is the harmonic language modal, tonal, or atonal? Will rhythm be metrically strict (locked to a grid at 120 BPM) or rubato and flexible?

Document the visual rhythm by transcribing the edit points. If the cut contains rapid montage sequences (cuts every 1–2 seconds), your orchestration must reflect this acceleration: shorter musical phrases, higher register activity, faster harmonic movement, and tighter rhythmic precision. Conversely, static, held shots require sustained orchestral textures and slower harmonic rhythm to avoid feeling static or dreary.

### Stage 1B: Template Setup & Instrument Configuration

In Fairlight, construct a mixing template optimized for orchestral composition and scoring. DaVinci Resolve's mixer operates with a track-based architecture; each audio track occupies a vertical fader strip on the console display. Create the following track configuration:

**Master Bus & Subgroup Structure:**
Establish a stereo master bus (automatically created). Create four subgroups: Strings (for violin, viola, cello, and double bass stems), Woodwinds (flute, oboe, clarinet, bassoon), Brass (trumpet, trombone, French horn, tuba), and Percussion (timpani, snare, kick, cymbals, mallets). This hierarchical structure allows you to sculpt balance within orchestral families while maintaining independent control of the overall timbre.

Right-click in the Fairlight mixer and select "Create New Track." Repeat four times. Label each track by right-clicking its track header and selecting "Edit Name." Use the naming convention: "STRINGS_L/R," "WOODWINDS_L/R," "BRASS_L/R," "PERCUSSION_L/R." Create one additional stereo track labeled "MUSIC_SCRATCH" for reference compositions or rough guide tracks.

Set each subgroup output to the master bus by clicking the output dropdown on each track header and selecting "Master." This routing guarantees that all orchestral content will reach the master output at the correct sum level.

### Stage 1C: Harmonic Framework & Functional Progression Mapping

Before recording or importing any audio, establish the harmonic architecture of your score. This is the foundational constraint that will govern every orchestration, voice-leading, and arrangement decision. Choose a key center appropriate to your visual content. If the piece contains emotional warmth and stability, use a major key (C major, G major, or F major provide open, resonant sonorities). If the content demands tension or ambiguity, use a natural minor key (A minor, E minor) or a modal framework (D Dorian for melancholic introspection, G Mixolydian for blues-tinged excitement).

Map a functional progression using Roman numeral analysis. For a 120-second underscore with four distinct sections, establish eight harmonic blocks, each occupying roughly 15 seconds. A canonical progression for emotional underscore follows the functional framework: I (tonic/home) → vi (relative minor, introduces melancholy) → IV (subdominant, opens harmonic space) → V (dominant, creates tension) → I (resolution). This progression, originating from classical sonata form, remains effective because it mirrors natural psychological pacing: stability, introspection, expansion, anticipation, and cathartic return.

Transcribe this progression into Resolve's marker system. Create a marker for each harmonic block by clicking in the timeline at the exact beat where a chord change occurs and pressing M. Type the Roman numeral and chord voicing into the marker (e.g., "I maj7 / Strings Pizzicato") and press Enter. These markers will display above the timeline and serve as real-time reminders during composition and mixing.

### Stage 1D: Real-Time Orchestration & Stem Recording

Import reference audio stems into Resolve's Fairlight timeline. If you do not have pre-recorded orchestral stems, use a MIDI-driven approach with virtual instruments. Open a session in your primary DAW (Ableton Live, Logic Pro, Reaper, or Dorico) and configure the MIDI export and audio bounce workflow. Compose a short orchestral phrase (16–32 bars at your chosen tempo) that responds to the harmonic framework and visual cuts you identified in Stage 1A.

Create four separate bounces (one for each orchestral family: Strings, Woodwinds, Brass, Percussion) with the following specifications:
- **File Format:** WAV, 24-bit, 48 kHz
- **Metadata:** Embed the original BPM in the file name (e.g., "STRINGS_120BPM_v1.wav")
- **Level:** Bounce at -6 dB to leave mixing headroom

In Resolve's Media pool, drag each stem into the corresponding Fairlight track (STRINGS_L/R, WOODWINDS_L/R, and so forth). Synchronize the in-points by snapping each stem to the timeline's measure line using the snap-to-grid function (keyboard shortcut: N toggles snapping). Position each stem so that the downbeat aligns precisely with the first visual cut or emotional transition you identified in your spotting chart.

Play through the synchronized video and audio. Does the harmonic progression create emotional alignment with the visual rhythm? Do the orchestral attacks synchronize with visual cuts or emotional peaks? If timing misalignment occurs, use Fairlight's time-shift tool (right-click the clip and select "Time Shift") to nudge the stem forward or backward by precise frame increments. In a 24 fps session, one frame equals 41.67 milliseconds; ensure that string attacks land no later than 50 ms after a visual cut to maintain perceived synchronicity.

### Stage 1E: Voice-Leading Refinement & Harmonic Tension Mapping

With the orchestral stems synchronized to picture, evaluate the voice-leading quality of your score. Smooth voice-leading—where individual melodic lines (parts) move by step (a second) rather than leap—creates psychological continuity and reduces the listener's cognitive load. When transitioning between harmonic blocks (e.g., from IV to V), verify that each orchestral voice moves by the shortest available interval. For instance, if the Strings are voicing a C major triad (C–E–G) and you need to move to G dominant 7 (G–B–D–F), the Strings should retain G or E (common tones) and move the remaining notes by step: C → B or C → D, rather than jumping to distant registers.

Create a second mixing pass specifically designed to expose voice-leading weaknesses. Insert a spectrum analyzer plugin (Voxengo SPAN) on the Master bus (Fairlight > Plugins > Audio FX > Voxengo SPAN). Set the analyzer to "Peak" mode and observe the frequency response during each harmonic transition. Smooth voice-leading produces minimal spectral discontinuity—a stable, flowing curve across the frequency spectrum. Harsh voice-leading creates jagged peaks and valleys, indicating uncontrolled intervals or register jumps.

If the spectrum reveals discontinuity at a harmonic transition, adjust the orchestral voicing. Open your reference DAW and re-record the affected section, paying explicit attention to voice-leading rules: (1) keep common tones in the same voice, (2) move all other voices by the shortest available interval (preferably stepwise), and (3) if leaps are necessary (e.g., to avoid parallel fifths or to maintain tessitura), ensure the leap is followed by stepwise motion in the opposite direction (a principle called "recovery").

Re-export the corrected stem at 48 kHz, 24-bit, with the same level (−6 dB headroom). In Resolve, right-click the original stem and select "Replace with New Media." Choose the corrected WAV file. The timeline will update automatically, preserving all synchronization and mixing decisions applied to the previous version.

### Stage 1F: Dynamic Range & Orchestral Balance Documentation

As your orchestral underscore develops, create a detailed dynamic range and orchestral balance chart. This document will serve as reference during final mixing and during quality assurance testing. For each harmonic block (marked at 15-second intervals), specify:

**Loudness Target (LUFS):** Each section should occupy a distinct loudness envelope. Opening sections (establishing atmosphere) typically target −18 to −15 LUFS (quieter, more intimate). Climactic sections target −12 to −9 LUFS (brighter, more energetic). Use Youlean Loudness Meter or Nuendo's integrated loudness display to measure and document the integrated loudness over each 15-second block.

**Orchestral Balance Ratios:** For each section, specify the relative level (in dB) of each orchestral family. A typical "full orchestral" balance might be: Strings +0 dB (reference), Woodwinds −3 dB (slightly recessed), Brass −2 dB (prominent but not overwhelming), Percussion −6 dB (subtle rhythmic texture). Document deviations: a "Woodwind-featured" section might use Woodwinds +2 dB, Strings −3 dB, Brass −6 dB, Percussion −8 dB.

**Register Profile:** Categorize each section as "Low-Register" (fundamental energy between 50–150 Hz, supporting harmonic weight), "Mid-Register" (200–2000 Hz, clarity and definition), or "High-Register" (2000–8000 Hz, brilliance and air). A register profile prevents orchestral mudiness: if all four families occupy the low-register simultaneously, the spectrum becomes congested and harmonic clarity collapses. Instead, allocate registers: Strings occupy low-register fundamentals, Woodwinds occupy mid-register melodic content, Brass occupies high-mid register harmonic reinforcement, and Percussion occupies a broad spectrum with emphasis on attack transients (0–500 ms decay, then rapid fade).

Document these specifications in a plain-text file within your project folder:

```text
ORCHESTRAL_BALANCE_CHART.txt

Section 1 (0:00–0:15) — Opening Theme / Establishing
  Loudness Target: -18 LUFS (intimate, sparse)
  Balance: Strings +0dB | Woodwinds -6dB (solo flute only) | Brass -∞ (muted) | Percussion -8dB (soft mallets)
  Register Profile: Low-Register (cello + bass fundamentals) + High-Register (solo violin melody)
  Voice-Leading Quality: Stepwise motion throughout; common-tone retention in chord changes

Section 2 (0:15–0:30) — Development & Harmonic Expansion
  Loudness Target: -15 LUFS (warm, engaging)
  Balance: Strings +0dB | Woodwinds -2dB (oboe countermelody) | Brass -3dB (French horn pad) | Percussion -4dB (timpani rolls)
  Register Profile: Full spectrum coverage; no register collisions
  Voice-Leading Quality: One leap per voice per 8-bar phrase; all leaps followed by stepwise recovery

Section 3 (0:30–1:00) — Climactic Peak
  Loudness Target: -12 LUFS (bright, energetic)
  Balance: Strings +2dB (tutti, max brilliance) | Woodwinds +1dB (full section) | Brass +3dB (full, including tuba) | Percussion +2dB (full articulation)
  Register Profile: High-Register dominant; low-register support from basses only
  Voice-Leading Quality: Parallel harmony acceptable at climax (builds massiveness); register spread maximized

Section 4 (1:00–1:30) — Resolution & Emotional Descent
  Loudness Target: -14 LUFS (cathartic)
  Balance: Strings +1dB (reduced from climax, but still present) | Woodwinds -2dB | Brass -6dB (wind-down) | Percussion -10dB (subtle only)
  Register Profile: Mid-Register focus (emotional center); high-register activity fades
  Voice-Leading Quality: Return to smooth stepwise motion; V–I resolution emphasized with leading-tone resolution in melody
```

---

## Exercise 2: Timbre Synthesis, Waveform Shaping & Modulation Routing

This exercise translates orchestral composition into practical mixing decisions within Resolve's Fairlight environment. You will manipulate spectral character, dynamic envelope, and spatial placement to sculpt individual instrument timbre and orchestral balance without replacing or re-recording any source material. This discipline—timbre shaping through EQ, compression, and spatial processing—represents the core skill of mixing for visual media.

### Stage 2A: Spectral Analysis & Diagnostic Listening

Begin with spectral analysis of your orchestral stems. In Fairlight, insert Voxengo SPAN on the Master bus output by clicking the Master track header, then clicking the "+" button in the Effects panel (located to the right of the mixer). Select "Audio FX" > "Metering" > "Voxengo SPAN." Set the analyzer to "Peak Spectrum" mode (checkbox in the lower left of the SPAN window) and engage "Average" mode to display a smoothed frequency response curve over time.

Play your orchestral underscore from beginning to end while observing the SPAN display. The frequency response should exhibit the following characteristics for well-balanced orchestral music:

**60–150 Hz (Low Fundamental):** Presence indicates weight and bass support. For orchestral music, target −3 to 0 dB relative to 1 kHz. If the response is below −6 dB, the orchestration lacks gravitas; if it exceeds +3 dB, mud accumulates and harmonic clarity collapses. This frequency range is dominated by double basses, cellos playing in the bass register, and kettle drums (timpani).

**150–500 Hz (Low-Mid Presence):** This region carries emotional warmth and vocal/string sustain. Ideally target −1 to +1 dB. Excessive energy above +3 dB creates a "honky," nasal quality; insufficient energy below −2 dB causes emotional detachment. Cello fundamentals, violas, and the lower harmonics of violins dominate this band.

**500 Hz–2 kHz (Core Clarity):** This is the human auditory system's most sensitive region (the "presence peak"). Target −2 to +2 dB. Excessive presence (+5 dB or higher) creates listener fatigue and harshness; insufficient presence below −3 dB reduces intelligibility of orchestral textures. Violin fundamentals, woodwind core tones, and mid-range brass occupy this band.

**2–6 kHz (Upper-Mid Brilliance):** Presence here conveys energy and modernity. Target 0 to +3 dB. Insufficient energy causes orchestrations to sound "dull" or "distant"; excessive energy creates "aggressive" or "fatiguing" character. High-register violin and flute partials, woodwind air, and high-register brass harmonic content live here.

**6–12 kHz (Presence & Air):** This region defines perceived clarity and three-dimensional space. Target 0 to +2 dB. Insufficient energy makes orchestral music sound "thick" and "enclosed"; excessive energy creates "sibilant" harshness and a "thin" character. High-frequency flute partials, violin shimmer, and percussion transient attack spectra dominate.

**Above 12 kHz (Super-High Presence):** This band defines perceived brightness and air. For orchestral music targeting broadcast delivery, target 0 to +1 dB. Excessive presence creates "fatiguing," "shrill" character; insufficient presence sounds "muffled." Most orchestral instruments (other than cymbals, gongs, and overtone-rich strings) contribute minimal energy above 12 kHz.

If your spectral analysis reveals significant deviations from these targets (e.g., a −6 dB dip at 2 kHz indicating lack of clarity, or a +5 dB peak at 6 kHz indicating harshness), proceed to Stage 2B to apply corrective EQ.

### Stage 2B: Corrective & Creative EQ Implementation

Each orchestral subgroup (Strings, Woodwinds, Brass, Percussion) requires customized EQ treatment. This is not about "making things sound better"—it is about achieving specific spectral targets that ensure clarity within the mix and reduce listener fatigue during extended listening.

**Strings EQ Profile:**
Insert a parametric EQ plugin on the STRINGS_L/R track by clicking the "+" button in the track's Effects panel and selecting "Audio FX" > "EQ" > "Parametric EQ." Configure the following nodes:

Node 1 (Low-Cut Filter): Set to High-Pass mode, frequency 40 Hz, slope 24 dB/octave. This removes subsonic rumble and reduces accumulation of low-frequency mud from bowed instruments.

Node 2 (Low-Mid Clarity): Frequency 200 Hz, Q (width) 0.7 (broad), Gain +2 dB. Strings in the bass-register (cellos, double basses) occupy 150–400 Hz; a gentle boost here adds emotional warmth without muddiness.

Node 3 (Midrange Fundamental): Frequency 700 Hz, Q 1.0, Gain −1 dB (slight cut). Many string recordings exhibit a "woody" peak around 700 Hz from the instrument body resonance; a subtle cut removes this character without destroying naturalness.

Node 4 (Presence Peak): Frequency 2.5 kHz, Q 0.8, Gain +2 dB. High-register violins and violas exhibit resonance here; boosting creates clarity and presence within the ensemble.

Node 5 (Upper Harmonic Shimmer): Frequency 6 kHz, Q 0.6, Gain +1.5 dB. Violins' upper harmonic partials live here; gentle boosting adds "air" and extends perceived spatial depth.

Node 6 (High-End Presence): Frequency 10 kHz, Q 0.5, Gain +0.5 dB (subtle). Further shimmer extension without creating harshness.

Node 7 (Ultra-High Presence Limit): Frequency 14 kHz, Q 0.4, Gain −2 dB (slight dip). Prevents excessive high-end brilliance that could cause listener fatigue.

**Woodwinds EQ Profile:**
Insert a parametric EQ on WOODWINDS_L/R:

Node 1 (Low-Cut): Frequency 50 Hz, slope 18 dB/octave (slightly gentler than Strings, as some woodwind recordings carry low-frequency resonance from the instrument body). 

Node 2 (Bass Resonance): Frequency 150 Hz, Q 0.8, Gain −1.5 dB. Woodwinds exhibit a resonant peak in this region; cutting slightly improves clarity when mixed with strings.

Node 3 (Low-Mid Fundamental): Frequency 400 Hz, Q 1.0, Gain +1 dB. Oboe, clarinet, and bassoon fundamentals occupy this band.

Node 4 (Core Clarity): Frequency 1.2 kHz, Q 0.9, Gain +3 dB. Woodwind brightness and "squeak" character live here; a boost emphasizes intelligibility and presence.

Node 5 (Mid-Presence Peak): Frequency 3 kHz, Q 0.8, Gain +2 dB. Woodwind articulation and "air" occupy this region.

Node 6 (Upper-Mid Harmonic): Frequency 5 kHz, Q 0.6, Gain +1 dB. Extension of articulation character.

Node 7 (High-Presence Limit): Frequency 10 kHz, Q 0.5, Gain −1 dB. Prevents flute overtones from becoming shrill.

**Brass EQ Profile:**
Insert a parametric EQ on BRASS_L/R:

Node 1 (Low-Cut): Frequency 60 Hz, slope 24 dB/octave. Brass instruments produce minimal subsonic energy; a steeper cut avoids rumble.

Node 2 (Bass Presence): Frequency 120 Hz, Q 1.0, Gain +1 dB. Tuba and low-register trombone fundamentals.

Node 3 (Midrange Body): Frequency 500 Hz, Q 0.9, Gain −1.5 dB. Brass exhibits a characteristic "woofy" peak here; cutting adds definition.

Node 4 (Mid-Presence Characteristic): Frequency 1.5 kHz, Q 0.8, Gain +4 dB. Brass "bite" and articulation live here; strong boost emphasizes brass section presence in the mix.

Node 5 (Upper-Mid Brilliance): Frequency 3.5 kHz, Q 0.7, Gain +2.5 dB. Brass high-register harmonic content.

Node 6 (Presence Peak): Frequency 6 kHz, Q 0.6, Gain +2 dB. Trumpet and high-register trombone shimmer.

Node 7 (Sibilance Control): Frequency 8 kHz, Q 0.5, Gain −1 dB. Prevents excessive "hiss" from high-register brass.

**Percussion EQ Profile:**
Insert a parametric EQ on PERCUSSION_L/R:

Node 1 (Subsonic Removal): Frequency 20 Hz, slope 24 dB/octave. Percussion transients contain minimal subsonic energy; aggressive filtering prevents rumble.

Node 2 (Attack Definition): Frequency 2 kHz, Q 0.8, Gain +2 dB. Percussion articulation and attack transients are concentrated here.

Node 3 (Brightness & Shimmer): Frequency 4 kHz, Q 0.7, Gain +1.5 dB.

Cymbal and hi-hat overtones; extension of transient brilliance.

Node 4 (High-Frequency Air): Frequency 10 kHz, Q 0.5, Gain +1 dB. Final extension of percussion shimmer and articulation clarity.

The parametric EQ profiles presented here embody decades of orchestral recording practice distilled into repeatable, verifiable frequency-domain interventions. Each node represents a hypothesis about spectral energy distribution that can be validated through A/B comparison, RMS measurement, and spectrographic analysis. The Q-values balance surgical precision against musical naturalness; the gain adjustments reflect empirical observations of orchestral timbral balance in professional productions. When applying these profiles, engage bypass switching to confirm each adjustment produces the intended perceptual result—increased clarity, improved separation, or corrected tonal balance—without introducing artifacts. Document all deviations from these baseline profiles in your session notes; such deviations constitute site-specific calibrations that may inform future sessions. The ultimate validation criterion remains the match between the monitoring environment's acoustic output and the reference standard you have established through critical listening to professionally mixed orchestral recordings in your calibrated space.

## Summary & Verification Matrix

| **Invariant/Mechanism** | **Governing Principle** | **Diagnostic Criterion** | **Failure Mode** |
|-------------------------|-------------------------|--------------------------|------------------|
| **Gain Staging Hierarchy** | All channel faders at unity (0 dB) before bus processing; master fader at unity; gain adjustments via clip gain or pre-fader inserts only. | No channel peak exceeds −6 dBFS; master bus headroom maintained at −3 dBFS minimum; no clipping indicators illuminate during playback. | Distortion on master bus; loss of dynamic range; inability to accommodate processing headroom; masking of individual section timbres. |
| **Frequency-Domain Separation** | High-pass filtering applied progressively from low-frequency sections upward (strings: 80 Hz, woodwinds: 120 Hz, brass: 60 Hz, percussion: 20 Hz); Q-values ≤1.0 for tonal shaping, Q ≥0.5 for transient preservation. | Spectrographic analysis reveals distinct energy bands per section with minimal overlap below 200 Hz; bypass comparison confirms increased clarity without timbral thinning. | Muddy low-mid accumulation (200–500 Hz); loss of instrument body and warmth; excessive "hollowness" from aggressive high-pass filtering. |
| **Parametric EQ Node Allocation** | Minimum 4 nodes per section (low-cut, fundamental shaping, mid-presence, high-extension); Q-values inversely proportional to frequency (tighter Q at low frequencies, broader Q at high frequencies). | A/B bypass switching confirms each node produces audible, musically justified change; RMS level shift per node < 2 dB to avoid gain-masking perception. | Over-EQ'd "processed" timbre; phase distortion from excessive node count; loss of natural orchestral balance; listener fatigue from hyped presence regions. |
| **Reference Calibration Protocol** | Monitoring system calibrated to 85 dB SPL (C-weighted, slow) pink noise at mix position; comparison against minimum three professional orchestral recordings in same genre and aesthetic. | SPL meter confirms ±1 dB accuracy at mix position; tonal balance of session output matches reference recordings in bass extension, midrange clarity, and high-frequency air. | Mixes translate poorly to consumer playback systems; bass-light or bass-heavy output; excessive brightness or dullness relative to commercial standards. |
| **Bus Processing Order** | EQ inserted before compression/limiting on all buses; sidechain filtering (if used) mirrors main EQ high-pass frequency; parallel processing returns summed post-fader to preserve gain structure. | Dynamic range compression applied only after frequency-domain corrections; compressor gain reduction meters show < 3 dB reduction on transient peaks during orchestral tutti passages. | Pumping/breathing artifacts; loss of orchestral dynamics; frequency-dependent compression creating unnatural timbral shifts during loud passages. |
| **Session Documentation & Repeatability** | All plugin settings, routing, and gain adjustments logged in session notes or template; deviations from baseline profiles annotated with rationale and perceptual outcome. | Template recall produces bit-identical routing and processing chain; printed channel strip settings match logged values within ±0.5 dB and ±10 Hz. | Inability to reproduce mix decisions across sessions; inconsistent sound across projects; loss of institutional knowledge when collaborators change. |
