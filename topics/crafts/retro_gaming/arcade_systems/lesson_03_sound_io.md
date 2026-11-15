# Lesson 3: Sound Synthesis and Input/Output Control

## 1. First-Principles Intuition & Invariants

The marriage of sound and input in arcade systems represents one of the most delicate real-time constraints in embedded computing history. While a dropped frame in video rendering might introduce a barely perceptible stutter, a single missed audio buffer or delayed input poll shatters the player's sense of causality. When a player presses the fire button, the synthesized gunshot must arrive within 16 milliseconds—the threshold of human temporal binding—or the system feels "laggy" even if visually perfect. This psychoacoustic and sensorimotor coupling drives the architectural invariant that underlies all classic arcade design: **sound generation and input handling must operate independently of the main game loop, governed by hardware interrupts and deterministic timing chains that cannot be preempted by computational load**.

Arcade sound synthesis evolved through two dominant paradigms, each reflecting different tradeoffs between hardware complexity and tonal expressiveness. The earlier Programmable Sound Generator (PSG) architecture, exemplified by the General Instrument AY-3-8910 and Texas Instruments SN76489, produces square wave tones through digital frequency dividers. These chips generate sound by counting down programmable period registers at a fixed master clock rate—typically 1.789773 MHz for NTSC systems or 1.7734 MHz for PAL—and toggling an output bit each time the counter reaches zero. The resulting waveform is a symmetric square wave whose fundamental frequency equals the master clock divided by twice the period value. A PSG with three tone channels and one noise channel can layer simultaneous voices, but each channel produces only a single waveform shape with a limited amplitude envelope. The sonic palette skews toward bright, buzzy timbres: the pulsing bass of *Pac-Man*'s siren, the chirping pellet munching, and the descending death wail all emerge from three square wave generators whose period registers are swept across discrete frequency steps in software.

Frequency Modulation (FM) synthesis, introduced to arcades through Yamaha's YM2151 and YM2203 chips in the mid-1980s, abandons fixed waveforms entirely in favor of dynamic spectral construction. The core FM principle descends from John Chowning's 1973 discovery at Stanford: when one sine wave oscillator (the modulator) modulates the instantaneous frequency of another (the carrier), the output contains sidebands at $f_c \pm n \cdot f_m$ where $f_c$ is the carrier frequency, $f_m$ the modulator frequency, and $n$ ranges over integer multiples determined by the modulation index $I$. The modulation index, defined as the ratio of peak frequency deviation to modulator frequency ($I = \Delta f / f_m$), controls timbral brightness: low indices produce subtle vibrato, while indices above 2 generate complex harmonic and inharmonic overtones that can emulate metallic percussion, brass, and electric pianos. Yamaha's chips arrange oscillators into **algorithms**—fixed topologies connecting operators (individual sine wave generators) as carriers and modulators. The YM2151's eight algorithms range from simple two-operator FM (one modulator into one carrier) to parallel stacks of four independently controlled sine waves. A brass stab in *After Burner* might use Algorithm 7: Operator 1 modulates Operator 2, while Operators 3 and 4 modulate a final carrier, creating a rich harmonic stack with independent envelope control on each component. The timbral explosion from PSG to FM was not incremental—it was categorical, enabling arcade soundtracks to leap from beeps to quasi-orchestral gestures within the same generation.

The input subsystem must operate under an equally rigid temporal contract. A digital joystick presents a trivial electrical interface—eight discrete lines for up, down, left, right, and four buttons—but the software challenge lies in **debouncing** (filtering mechanical contact noise) and **polling rate synchronization** (sampling inputs at consistent intervals immune to game logic variability). Early arcade boards sample inputs every vertical blanking interval (VBLANK), the 1.2-millisecond window when the CRT's electron beam returns from the bottom-right corner to the top-left. This synchronization is not arbitrary: reading input during active display avoids mid-frame jitter where a button press might be honored partway through sprite movement calculations, causing inconsistent response distances. The VBLANK interrupt becomes the heartbeat for input, sound, and DMA operations, partitioning the frame into deterministic slices where each subsystem executes in a strict, non-overlapping order.

The invariant that unifies sound and input is **temporal determinism under interrupt discipline**. Arcade systems operate without operating systems, memory protection, or multitasking—every cycle is accounted for. The Z80 or 68000 main CPU runs game logic, but sound synthesis and input polling are delegated to dedicated chips or secondary CPUs that respond to hardware interrupts independent of the main loop's execution state. If the main CPU enters a compute-heavy pathfinding routine for enemy AI, the sound chip continues cycling through its waveform generators at the master clock rate, and the VBLANK interrupt fires regardless, ensuring that player inputs are sampled and sound buffers refilled on schedule. This separation allows arcade cabinets to maintain consistent audio pitch and input responsiveness even as game complexity scales—a luxury unavailable to home computers of the era, where a single CPU time-slices between rendering, game logic, and bit-banging audio through a speaker pin.

## 2. Core Architecture & Mechanics

### Programmable Sound Generator (PSG) Internals

The canonical PSG architecture consists of three square wave tone generators and one pseudo-random noise generator, all sharing a common master clock and digital-to-analog converter (DAC). Each tone channel contains a 10-bit or 12-bit period register $P$ that defines the countdown interval. At each master clock tick, a down-counter decrements; when it reaches zero, the counter reloads from $P$ and the channel's output bit toggles. The resulting waveform frequency is:

$$
f_{\text{output}} = \frac{f_{\text{master}}}{2 \cdot P}
$$

The factor of two arises because a complete square wave cycle requires two toggles (low-to-high and high-to-low). For the AY-3-8910 running at 1.789773 MHz, programming $P = 226$ yields $f = 1789773 / (2 \times 226) \approx 3959$ Hz, close to a concert B7. The discrete period steps impose quantization—achieving exact equal temperament tuning requires precomputed lookup tables mapping MIDI note numbers to closest-fit period values. The amplitude of each channel is controlled by a 4-bit envelope register providing 16 logarithmic volume levels, implemented in hardware as a resistor ladder DAC that approximates human loudness perception (a doubling of amplitude bits corresponds to roughly 2 dB steps, though chip variations and board design affect the exact curve).

The noise generator employs a Linear Feedback Shift Register (LFSR) to produce pseudo-random bit sequences. A typical 15-bit LFSR configuration XORs bit positions 14 and 15, feeding the result back into bit 0, and shifts the register every $N$ master clock cycles where $N$ is programmable. The output bit stream toggled at this rate creates broadband noise whose tonal color shifts with the LFSR clock divider: fast rates (small $N$) yield harsh white noise resembling explosions, while slower rates (large $N$) produce rumbling low-frequency textures. The LFSR polynomial must be carefully chosen—common choices like $x^{15} + x^{14} + 1$ ensure maximal length sequences (period $2^{15} - 1$) that do not repeat short patterns audibly.

### FM Synthesis and Operator Topology

Yamaha's YM2151 OPM (FM Operator Type-M) chip implements four-operator FM synthesis across eight independent voices. Each operator is a sine wave generator with dedicated phase accumulator, frequency multiplier, envelope generator, and amplitude modulator. The phase accumulator increments at a rate determined by the note frequency and a multiplier setting (0.5×, 1×, 2×, ... 15×), wrapping modulo $2\pi$ to index a 256-entry sine lookup table stored in on-chip ROM. The instantaneous output of operator $j$ is:

$$
y_j(t) = A_j(t) \cdot \sin\left(\omega_c t \cdot M_j + \phi_j + \sum_{k} I_{jk} \cdot y_k(t)\right)
$$

where $A_j(t)$ is the time-varying amplitude envelope, $\omega_c$ the carrier angular frequency, $M_j$ the frequency multiplier, $\phi_j$ a fixed phase offset, and the summation represents modulation inputs from upstream operators in the algorithm topology. The modulation index $I_{jk}$ is programmed via a 7-bit Total Level (TL) register for the modulator operator, controlling peak frequency deviation. High TL values on a modulator drive the carrier's phase argument through many radians per cycle, generating dense harmonic sidebands.

The YM2151's eight algorithms define fixed operator routings. Algorithm 0 chains operators serially: Op1 → Op2 → Op3 → Op4, maximizing harmonic complexity but offering less independent control. Algorithm 7 splits into two parallel FM pairs (Op1 → Op2, Op3 → Op4), allowing a bright, modulated carrier to be layered with a simpler sine wave for tonal depth. The chip provides independent Attack, Decay, Sustain, and Release (ADSR) envelope generators for each operator, with time constants ranging from 0 milliseconds to several seconds via 5-bit rate and 4-bit level parameters. An FM brass patch might set Op1 (modulator) to a fast attack (5 ms) and short decay to create the initial "blatting" transient, while Op2 (carrier) uses a slower attack (20 ms) and sustained release, smoothing the tail. Real-time register writes update operator parameters mid-note—writing to the frequency register of a sustained note bends pitch, while modulating the TL register during the sustain phase creates dynamic timbral sweeps.

The YM2151 interfaces to the host CPU via an 8-bit data bus and two control lines: address latch (A0) and write enable (/WR). Writing a register requires two sequential bus cycles: first, assert A0=1 and write the register address (0x00–0xFF), then assert A0=0 and write the data byte. The chip internally buffers writes and updates the synthesis engines during the inter-sample interval, avoiding audible clicks. A critical gotcha: writing to a Key-On register (0x08) triggers note start, but the chip requires a 12-cycle delay before the next register write to ensure envelope generators latch correctly. Failing to insert NOPs or dummy reads results in stuck notes where envelopes freeze mid-attack. The YM2151 generates sample output at 55.5 kHz (master clock / 64), producing a 12-bit signed PCM stream that feeds a resistor ladder DAC. Arcade boards typically AC-couple this output through a 10 µF capacitor to block DC offset and feed it into an op-amp buffer driving the cabinet's mono amplifier.

### Input Polling and Debouncing

Arcade input hardware maps to memory-mapped I/O addresses where each bit corresponds to a discrete input line. A typical memory map might assign address $7000 (hex) to joystick and buttons: bit 0 = right, bit 1 = left, bit 2 = down, bit 3 = up, bit 4 = button 1, bit 5 = button 2, and so on. Reading this address via a Z80 `IN A, ($70)` instruction or 68000 `MOVE.B $7000, D0` loads the input state in a single cycle. Mechanically, each button and joystick microswitch connects a logic line to ground when closed, and a pull-up resistor (typically 4.7 kΩ) holds it high when open. The inverted logic means 0 = pressed, 1 = released, so software must bitwise-NOT the read value or adapt comparison logic.

Mechanical switches exhibit contact bounce: when pressed, the contacts open and close multiple times over 1–5 milliseconds before settling into a stable state. Without debouncing, a single button press can register as multiple rapid edges. Hardware debouncing uses an RC low-pass filter (resistor and capacitor in series) to smooth the voltage transition, but arcade boards often rely on software debouncing to save component cost. The standard algorithm maintains a history buffer of the last $N$ consecutive input reads (typically $N=3$ to $N=5$) and declares a button pressed only when all samples agree on the pressed state. In Z80 assembly, this might look like:

```asm
; Debounce routine (Z80)
; Assumes 3-sample history in RAM: input_hist1, input_hist2, input_hist3
LD A, ($7000)       ; Read current input byte
LD HL, input_hist3  ; Shift history
LD B, (HL)          ; input_hist3 → B
LD (HL), A          ; Current → input_hist3
DEC HL
LD C, (HL)          ; input_hist2 → C
LD (HL), B          ; Shift
DEC HL
LD (HL), C          ; Shift

; AND all three samples: stable only if all bits agree
AND B
AND C
LD (debounced_input), A
```

This shifted ring buffer approach filters transient noise while introducing a 3-frame latency (50 ms at 60 Hz). For competitive twitch gameplay, some arcade boards reduce this to 2-sample majority vote at the cost of occasional false positives. Edge detection logic then compares the current debounced state to the previous frame's state via XOR: bits that transition from 1 to 0 represent new button presses (rising edge), while 0 to 1 transitions are releases (falling edge). Game code checks the edge-detected byte to trigger one-shot events like jump or fire, ignoring the held state to prevent repeated triggering during sustained presses.

### Interrupt-Driven Synchronization

The vertical blanking interval (VBLANK) interrupt is the synchronization backbone of arcade systems. The video timing circuit asserts an interrupt request line (IRQ) every 16.67 milliseconds (60 Hz NTSC) or 20 milliseconds (50 Hz PAL) when the CRT beam reaches the bottom scanline. The CPU, configured to respond to hardware interrupts, immediately vectors to an interrupt service routine (ISR) that suspends the main game loop mid-instruction. The VBLANK ISR executes a fixed sequence of tasks: read and debounce inputs, copy sprite and tilemap updates from RAM buffers to video registers (during the blanking window when display memory can be written without causing tearing), refill sound chip registers, and decrement frame-count timers. Because the ISR runs with interrupts disabled to prevent nested preemption, it must complete within the blanking interval—typically 1.2 ms—or the next frame will be delayed, causing jitter.

On the Z80, the VBLANK ISR might be structured as:

```asm
vblank_isr:
    PUSH AF              ; Save all registers
    PUSH BC
    PUSH DE
    PUSH HL

    CALL poll_inputs     ; Read joystick/buttons, update debounce buffer
    CALL update_sound    ; Write new frequencies/volumes to PSG
    CALL dma_sprites     ; Copy sprite buffer to video RAM

    POP HL               ; Restore registers
    POP DE
    POP BC
    POP AF
    EI                   ; Re-enable interrupts
    RETI                 ; Return from interrupt, resume main loop
```

The main game loop runs in the foreground, executing AI, collision detection, and score updates. It reads the debounced input state from a global variable updated by the ISR, ensuring that input handling is decoupled from game logic variability. If the main loop enters a computationally expensive pathfinding routine, the VBLANK ISR still fires every 16.67 ms, maintaining audio continuity and input responsiveness. This separation is the key to arcade systems' perceived "tightness"—the player's actions are sampled at a fixed rate immune to game state complexity.

For sound, dual-CPU architectures like *Galaga* and *Defender* dedicate a secondary Z80 or 6809 to audio synthesis. The main CPU writes sound effect triggers and music commands to a shared mailbox RAM address, and the sound CPU polls this mailbox every frame, updating PSG or FM chip registers accordingly. The sound CPU runs its own VBLANK ISR that increments note counters, applies vibrato or pitch bends, and sequences multi-note melodies stored in lookup tables. This offloading ensures that complex sound routines—like the layered harmonic sweep of a *Galaga* enemy divebomb—execute independently of the main game logic's frame budget. The sound CPU can even implement rudimentary mixing by rapidly switching channel assignments (time-division multiplexing), playing more than three simultaneous tones on a three-channel PSG by rotating note priorities at 240 Hz, exploiting the human ear's temporal averaging.

## 3. High-Performance Optimization & Failure Modes

### Frequency Table Precomputation and Note Accuracy

PSG synthesis requires translating MIDI note numbers or abstract musical pitches into hardware period register values. The equal-tempered scale defines the frequency of note $n$ (where $n=0$ corresponds to C-1 at 8.176 Hz and $n=69$ is A4 at 440 Hz) as:

$$
f_n = 440 \cdot 2^{(n - 69)/12}
$$

Inverting the PSG frequency formula to solve for period $P$ given a target frequency $f$ yields:

$$
P = \frac{f_{\text{master}}}{2 f_n}
$$

For the AY-3-8910 at 1.789773 MHz, computing this at runtime involves floating-point exponentiation and division—prohibitively expensive on an 8-bit CPU without hardware floating-point. The optimization is to precompute a 128-entry lookup table at compile time, storing 12-bit period values for all MIDI notes from C-1 to G9. A C preprocessor script or Python table generator calculates:

```python
import math
F_MASTER = 1789773.0
notes = []
for n in range(128):
    f = 440.0 * (2.0 ** ((n - 69) / 12.0))
    period = int(round(F_MASTER / (2.0 * f)))
    period = max(1, min(4095, period))  # Clamp to 12-bit range
    notes.append(period)

# Output as assembly .db directives
for i, p in enumerate(notes):
    print(f".db {p & 0xFF}, {p >> 8}  ; MIDI note {i}")
```

This table consumes 256 bytes of ROM and enables note lookup via a simple indexed load: `LD HL, note_table` followed by `ADD HL, DE` where `DE` holds twice the MIDI note number (accounting for 2-byte period values). The quantization error—difference between the ideal frequency and the closest integer period—averages about 0.5 cents (1/200 of a semitone), imperceptible in the noisy environment of an arcade cabinet. For applications requiring finer pitch control (vibrato, pitch bends), storing a fractional phase accumulator in software and updating period registers every few frames interpolates between discrete hardware steps.

### FM Patch Design and Envelope Tuning

Constructing expressive FM patches demands systematic exploration of operator topologies and envelope shapes. A practical workflow begins with algorithm selection: for percussive sounds (drums, explosions), prefer parallel algorithms (7, 6) with short attack/decay envelopes on all operators to create sharp transients with rapid spectral collapse. For sustained harmonic tones (bass, leads), select serial algorithms (0, 1) where modulators with slower envelopes sculpt evolving timbres. The modulation index $I$ controls brightness: start with $I \approx 2$ (Total Level around 40) for a warm tone, then increase TL by 16 (doubling the index) to add edge. If the sound becomes too harsh, reduce the modulator's Attack Rate to soften the transient spike.

Envelope generators on the YM2151 use logarithmic rate scaling: each Attack Rate (AR) value halves the attack time as AR increases by 4 units. An AR of 31 produces a near-instantaneous attack (< 1 ms), while AR of 10 yields a slow, pad-like fade-in over 200 ms. The Decay Rate (DR) and Release Rate (RR) similarly control exponential decay slopes. A common pitfall is setting all operators to identical ADSR shapes, producing static timbres; instead, stagger envelopes to create timbral motion. For a bell patch, set Operator 1 (modulator) to AR=31, DR=10, Sustain Level (SL)=0 (decay to silence), and Operator 2 (carrier) to AR=25, DR=6, SL=8 (sustain at mid-level). The modulator's rapid decay destabilizes the carrier's frequency modulation over time, mimicking the inharmonic damping of struck metal.

Real-time parameter modulation—writing to operator registers while notes sustain—unlocks dynamic effects. A siren effect involves cycling the carrier frequency register through a sawtooth wave pattern, implemented as a lookup table indexed by a frame counter. Writing to the Key-On register (0x08) with the same slot already active restarts envelopes without changing pitch, useful for re-triggering percussive accents in rhythm loops. However, register writes incur a 12-cycle latency (as mentioned), and writing too rapidly can cause envelope state machines to glitch. A safe practice is to buffer all register writes in an array and flush them sequentially within the VBLANK ISR, ensuring minimum inter-write delays are respected.

### Input Lag Mitigation and Polling Rate

The total input lag chain spans four stages: mechanical switch closure, debounce filtering, VBLANK sampling, and game logic response. Mechanical switches introduce 1–3 ms of bounce, software debouncing adds 16–50 ms (1–3 frames), VBLANK sampling contributes up to 16 ms (worst case if the button press occurs just after a VBLANK), and game logic response adds one frame (16 ms) for physics integration. Summing these, total latency ranges from 34 to 85 milliseconds. Competitive players perceive lag above 50 ms as sluggish, so aggressive optimization targets the debounce filter and logic response.

Reducing debounce history from 3 frames to 2 frames cuts 16 ms but increases false positive risk. An adaptive debounce algorithm tracks the stability of each input line independently: if a button has been stable for several seconds, reduce its debounce requirement to 1 frame; if noise is detected (rapid state flipping), revert to 3-frame filtering. This heuristic minimizes latency for stable inputs while maintaining robustness during electrical transients (coin door slams, electromagnetic interference from CRT degaussing).

An advanced optimization is **input polling oversampling**: instead of reading inputs once per VBLANK, sample them at the start of the VBLANK ISR, mid-frame (via a horizontal blanking interrupt), and immediately before game logic execution. Store all three samples and prioritize the earliest-detected edge. This reduces worst-case sampling lag from 16 ms to approximately 5 ms (assuming 3× oversampling). Implementing this on Z80 requires hijacking the horizontal blanking interrupt (HBLANK), which fires every 63.5 µs during active display. The HBLANK ISR must be extremely lightweight—read inputs into a scratch register and return in under 10 cycles—to avoid interfering with DMA or audio updates.

### Sound Channel Allocation and Priority

PSG systems with only three tone channels face resource contention when music, sound effects, and interface bleeps all demand simultaneous playback. The standard solution is a priority-based channel allocator: assign Channel 0 to sound effects (highest priority), Channel 1 to melody (medium priority), and Channel 2 to bass/harmony (lowest priority). When a high-priority event (explosion) arrives, the allocator preempts the currently playing note on Channel 0, caches the interrupted note's state (frequency, volume, envelope phase), plays the sound effect, and then restores the cached state upon completion. This "voice stealing" algorithm maintains auditory hierarchy—critical gameplay audio (player hit, enemy destroyed) always overrides ambient music.

FM systems with 8 voices rarely exhaust channels but must still manage polyphony. A least-recently-used (LRU) allocator tracks when each voice was last key-on'd; when all voices are active and a new note arrives, the allocator steals the oldest voice. This works well for transient sounds (drums, blips) but fails for sustained notes (organ pads), where stealing a note mid-sustain causes jarring cutoffs. A hybrid approach reserves two voices exclusively for sustained music (melody, bass) and pools the remaining six for effects and percussion. Game code marks music voices as "protected" in a bitmask, and the allocator skips them when searching for stealable candidates.

### Failure Mode: Register Write Timing and Audio Glitches

Writing to sound chip registers while the chip is mid-sample can cause audible glitches. The YM2151 internally double-buffers frequency and volume registers, swapping buffers during the inter-sample interval, but the Key-On register (0x08) is immediate—writing to it while an envelope is ramping causes the envelope generator to snap to the attack phase, creating a pop. The mitigation is to queue all Key-On writes and flush them during VBLANK, when the chip's internal sample buffer is being read out and no active envelope transitions are occurring. For games that require sub-frame audio timing (rhythm games where note accuracy matters within a few milliseconds), use a shadow register array in RAM: write all updates to the shadow, then copy the shadow to the chip in a tight loop during VBLANK. This ensures atomicity—either all registers update or none do—preventing partial state writes that cause detuning or stuck oscillators.

A related failure mode arises from incorrect master clock frequencies. If the PCB design uses a non-standard crystal oscillator (say, 1.8 MHz instead of 1.789773 MHz for cost reasons), all frequency calculations are off by ~0.5%, causing music to sound sharp. Worse, if the main CPU clock and sound chip clock are derived from different crystals with independent drift, tuning can vary with temperature as the cabinet warms up during operation. Professional arcade boards use a single master clock generator (often a 6 MHz or 8 MHz crystal with frequency dividers) to derive all subsystem clocks, ensuring phase-locked operation. For homebrew projects using discrete PSG chips, always measure the actual clock frequency with an oscilloscope or frequency counter before generating note tables, and recompute tables if the clock drifts by more than 0.1%.

### Failure Mode: Interrupt Overrun and Frame Slippage

If the VBLANK ISR exceeds the 1.2 ms blanking window, the CPU will still be executing ISR code when the next frame's active display begins. On systems with interrupt priority logic (like the 68000 with multiple IRQ levels), the next VBLANK interrupt will be queued and delayed, causing the current frame to "slip"—extending to 33 ms instead of 16.67 ms. This manifests as audio pitch drops (if the sound update routine is skipped) and visual judder. Profiling the ISR with cycle-accurate timing (using a logic analyzer on the CPU's address bus) reveals where bottlenecks occur. Common culprits include unrolled sprite DMA loops that copy hundreds of bytes without early exit, and sound update routines that perform linear searches through active note lists instead of using indexed lookups.

The fix is to partition ISR tasks by priority and defer non-critical work to the main loop. The VBLANK ISR should only handle time-critical operations: poll inputs, latch video register writes, and trigger audio buffer swaps. Complex operations like pathfinding for AI or multi-step sound sequencing move to the main loop, which runs with interrupts enabled and can be preempted by VBLANK without causing frame slip. For games with heavy sprite counts (bullet-hell shooters), implement a sprite priority queue where only the highest-priority sprites (player, enemies within a radius) are DMA'd during VBLANK, while background decorative sprites are deferred to the next frame's blanking window if time runs out. This "drop frames, not deadlines" philosophy ensures that audio and input remain responsive even when visual complexity spikes.

The interplay between sound synthesis and input handling defines the tactile feel of an arcade game—the sensation that the machine responds instantly and predictably to player intent. Mastering the hardware's timing constraints, register interfaces, and interrupt discipline transforms a collection of chips and switches into a cohesive, responsive whole. The PSG's quantized tones and the FM synthesizer's spectral richness are not merely technical specifications; they are the acoustic signatures of an era, and understanding their operation at the register level empowers modern designers to authentically recreate or deliberately subvert that sound. Input polling, debouncing, and interrupt-driven synchronization are not incidental details—they are the deterministic foundation upon which player trust is built, one frame at a time.
