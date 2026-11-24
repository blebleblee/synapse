# Orchestral Scoring: Mockup Craft from Score Paper to Mixed Session

## Who this is for and what you need running

This is a performance and production lab, not a signal-analysis course. The craft of orchestral scoring sits at the intersection of composition (what notes, for which instruments, in what register) and mockup engineering (how you make a sample library sing those notes convincingly). Every section below assumes you have a DAW open and a library loaded, and that you'll execute the drills with your hands, not just read them.

**Minimum rig:**
- DAW: Logic Pro, Cubase Pro, Reaper, or Ableton Live Suite — any will do; the piano roll and CC automation lane are universal.
- One tier-1 orchestral library with true legato and multiple articulations (VSL, Spitfire Symphony, EastWest Hollywood Orchestra, or Garritan Personal Orchestra 5 as a floor).
- A 61+ key weighted MIDI controller with a mod wheel and, ideally, an expression pedal jack.
- Audio interface running at 24-bit/48kHz, buffer set to 256 samples for programming work.

**Five-minute rig check before you start any lesson here:**
1. Load a string ensemble patch on a new instrument track.
2. Play a C-E-G chord. Confirm all three notes sound and sustain correctly.
3. Move your mod wheel — you should hear vibrato depth change on a sustained note.
4. Send CC11 from 40 to 100 — volume should swell without the tone changing character.
5. Hold the sustain pedal (CC64) — notes should ring past key release.

If any of these fail, fix your MIDI routing before continuing. Nothing below works on a broken signal chain.

---

## Part 1: The Grammar of a Convincing Mockup

### 1.1 Velocity selects the sample, CC11 shapes the phrase

This is the single most important mental model in orchestral MIDI work, and it's where most beginner mockups fail.

A string or brass sample library doesn't have one recording of a note — it has many, recorded at different bow pressures, air speeds, or mallet strikes (pp, mp, mf, f, ff). **MIDI velocity (0–127) picks which of those recordings plays.** Velocity 40 might trigger a soft-bow, gentle-attack sample; velocity 100 triggers a hard-bow, aggressive-attack sample. These aren't just louder versions of each other — they're acoustically different performances with different harmonic content and transient shape.

**CC11 (Expression) is a volume fader that acts *after* the sample is chosen.** It shapes the envelope of a phrase — the crescendo across four bars, the swell into a downbeat — without changing which recording is playing.

The practical rule: **use velocity to set the character of an attack, use CC11 to shape the phrase around it.** A sustained mf passage that crescendos to ff should mostly ride on CC11 (60→110) with velocities clustered in the mf-to-f zone (75–95) for the individual note attacks. If you only move velocity and leave CC11 flat, you'll hear discrete jumps in tone color instead of a smooth dynamic arc — the classic "stepping" sound of amateur mockups.

**Drill — hear the difference yourself:**
1. On a sustained violin patch, play a single held C4 at velocity 40, CC11 locked at 100. Note the tone.
2. Play the same note at velocity 100, CC11 locked at 100. Note how the *timbre* changed, not just the volume.
3. Now play velocity 70 (fixed) and automate CC11 from 40 to 110 over 4 seconds. You'll hear a clean swell with consistent tone — this is what a real crescendo sounds like.

### 1.2 Keyswitches: how you tell the engine which "instrument" to use

Articulations (legato, staccato, spiccato, tremolo, sul ponticello, pizzicato) are different recorded instruments as far as the sample engine is concerned. You select between them with **keyswitches** — MIDI notes placed below the playable range (typically C-1 to G-1) that don't sound themselves but flip the active articulation for everything that follows.

A typical VSL/Spitfire mapping:

| Keyswitch Note | Articulation |
|---|---|
| C-1 | Sustain / Long |
| C#-1 | Staccato |
| D-1 | Legato |
| D#-1 | Portato (soft tongued) |
| E-1 | Spiccato |
| F-1 | Tremolo |
| F#-1 | Pizzicato |

**Rule you must internalize: place the keyswitch at least 150–200ms before the note it governs.** The engine needs lead time to swap the active sample set. Put it right on the beat with the note and you'll get a glitch, a wrong articulation on the first note, or silence.

**Drill — articulation switching without glitches:**
1. On Violin I, insert a legato keyswitch (D-1) a full eighth-note *before* beat 1 of bar 3.
2. Enter a four-note ascending legato phrase (D4-E4-F4-G4, quarters).
3. Two bars later, insert a staccato keyswitch (C#-1) before the next phrase starts.
4. Play back. You should hear a clean legato slide in bar 3, and a crisp detached bounce in bar 5, with no stray attacks or silence at the transition points.

If your library supports **CC-based articulation switching** (VSL uses CC32), prefer it over keyswitches for anything you plan to automate heavily — CC32 values are just data on a continuous lane, with zero risk of colliding with actual note pitches during edits or transposition.

### 1.3 Legato engines: what "true legato" actually buys you

Tier-1 libraries record **interval-specific transitions** — a separate sample of a string player physically sliding a bow finger from C to D, a different sample for C to F, another for a descending minor third. The engine detects two notes played within roughly 150–200ms of each other and plays the recorded transition instead of two separate attacks.

This is why legato spacing matters mechanically, not just musically:

- **Notes spaced too far apart (>200ms gap)**: the engine can't link them, so you get two independent attacks — sounds like someone re-bowing, not sliding.
- **No keyswitch active**: engine defaults to sustain/attack mode, no transition at all.
- **Note-off before note-on** (non-overlapping): some engines (especially older Kontakt-based ones) need legato notes to overlap slightly, or at minimum have no gap, to trigger the transition sample.

**Drill — diagnosing a broken legato line:**
1. Solo your Violin I track playing a D4→E4→F4 phrase under the legato keyswitch.
2. Listen specifically at the D4→E4 junction. You're listening for a audible *portamento slide*, not a clean reattack.
3. If you hear two separate attacks: zoom into the piano roll, check the gap between note-off of D4 and note-on of E4. If it's more than ~150 ticks at 120 BPM (roughly 150ms), tighten it until the notes touch or very slightly overlap.
4. Re-bounce and re-check. This single fix resolves 80% of "my strings sound fake" complaints.

---

## Part 2: Building the Template and Scoring a Real Passage

### 2.1 Template structure that scales

Organize your project by orchestral family, left to right in the mixer matching stage position, so your panning decisions are intuitive rather than arbitrary:

```text
Strings (L→R stage position)
├── Violin I   — hard left, 16 desks
├── Violin II  — center-left, 14 desks
├── Violas     — center, 12 desks
├── Cellos     — center-right, 10 desks
└── Basses     — right, 8 desks

Woodwinds (center, elevated)
├── Flutes, Oboes, Clarinets (Bb), Bassoons — 2-3 players each

Brass (center-rear, elevated)
├── Horns (4-6), Trumpets (Bb, 3-4), Trombones (3: 2 tenor + bass), Tuba (1)

Percussion (rear)
├── Timpani (D2, G2, C3, F3), Snare/Bass Drum, Cymbals, Auxiliary
```

Group tracks by family under a bus (VCA group or folder, depending on DAW) so you can push an entire string section's level with one fader during a mix pass, without touching individual balances you've already carved out.

**MIDI channel and latency setup — do this once per template:**
- One software instrument track per articulation-switchable instrument, channel 1 (multi-timbral patches can share channels 1–16 if your library is built that way, but separate tracks per instrument is far easier to score with).
- Turn **off** low-latency mode during mixing/mockup playback (Logic: Preferences → Audio); it disables heavy convolution reverb tails that you need to hear. Turn it **on** only while tracking live MIDI input.
- Enable automatic Plugin Delay Compensation (Cubase: Studio Setup → ASIO-Guard; Reaper: enable "Anticipative FX processing"). Convolution reverbs can introduce 20–50ms of latency — without PDC, your tracks drift out of sync with each other after bouncing.

### 2.2 Scoring a four-part string chorale with proper voice leading

This is the bread-and-butter skill: turning a harmonic progression into physically idiomatic string writing, then performing it convincingly in MIDI.

**Progression: I – IV – V – I in C major.**

Four-part voice leading rules that keep this sounding like real orchestration rather than block chords:
- Keep common tones stationary between chords where possible (C is common to I and IV; G is common to I and V).
- Move the other voices by the smallest possible step.
- Never move two voices in parallel fifths or octaves — check every pair of voices at every chord change.
- The soprano (Violin I) carries the contour the ear follows; keep it the most active line.

**Voicing (optimal ranges, not absolute limits):**
- Violin I (soprano): C4–C6
- Viola (alto): C3–E5
- Cello (bass): C2–C4

```text
Bar 1 (C major):    Vln I = C5   Vla = E4   Cello = C3
Bar 2 (F major):    Vln I = F5   Vla = C5   Cello = F3   (soprano leaps 4th, alto leaps 6th)
Bar 3 (G major):    Vln I = G5   Vla = B4   Cello = G3
Bar 4 (C major):    Vln I = C5   Vla = E4   Cello = C3   (resolution, mirrors bar 1)
```

Check it on paper before you touch the DAW: Violin I and Cello at bar 1→2 move from (C5, C3) to (F5, F3) — that's a parallel octave on the outer voices, a classic voice-leading error. Fix by inverting the cello motion: keep cello on C3 held as a pedal tone through bar 2, or move it to A2 instead of F3 if the harmony allows a first-inversion F chord. Catching this kind of clash on paper before MIDI entry saves you from re-recording automation later.

**MIDI entry (Violin I, as reference — apply the corrected voicing to Viola and Cello similarly):**

```text
Bar 1, Beat 1: C5, whole note, velocity 80, CC11 ramp 70→90
Bar 2, Beat 1: F5, whole note, velocity 85, CC11 ramp 90→95
Bar 3, Beat 1: G5, whole note, velocity 90, CC11 ramp 95→100
Bar 4, Beat 1: C5, whole note, velocity 75, CC11 ramp 100→70 (release into cadence)
```

Note the velocity range: 75–90. This stays inside a single sample velocity layer (mf) for the whole phrase, so the *tone color stays consistent*, and all the dynamic motion comes from CC11. This is exactly the discipline from Part 1.1 applied to real material.

**Drill — record and verify:**
1. Enter all three parts.
2. Solo Violin I and Cello together. Listen at every bar transition for parallel motion — if the two lines seem to move "in lockstep" an octave or fifth apart, you've got the error above. Fix the voicing before moving on.
3. Draw the CC11 ramps by hand in the automation lane — don't leave it flat. A flat CC11 line across a 4-bar phrase is the #1 giveaway of a non-musician programming the mockup.

### 2.3 Adding woodwind counterpoint on top

Flute entrance at bar 3, under legato, moving in eighth notes against the sustained string chorale — this is where you practice interval-specific legato spacing in a real musical context, not an isolated drill.

```text
Bar 2, Beat 4 (triplet subdivision, slightly before bar 3): keyswitch D-1 (legato), zero-length
Bar 3, Beat 1:    D5, eighth, velocity 70, CC11 80
Bar 3, Beat 1.5:  E5, eighth, velocity 72, CC11 82
Bar 3, Beat 2:    F5, eighth, velocity 75, CC11 85
Bar 3, Beat 2.5:  E5, eighth, velocity 73, CC11 83
Bar 4, Beat 1:    D5, half note, velocity 68, CC11 75 (release, let the line breathe)
```

Keep eighth notes touching or overlapping by a few ticks — this is what triggers the legato engine's interval transitions rather than discrete attacks. Verify by soloing the flute and listening for the characteristic connected slur between D5 and E5: a real sliding timbral connection, not two separate tongued notes.

### 2.4 Humanizing by hand — the fastest path to a believable performance

Perfectly quantized MIDI is the second biggest tell of an amateur mockup (after flat CC11 lines). Real players don't land exactly on the grid, and sections don't attack in perfect unison — basses in particular lag slightly behind the bow due to string thickness and slower attack transient.

**Hand method (no scripting needed, do this on every important phrase):**
1. Turn off snap-to-grid in the piano roll (Logic: `G`).
2. Select all notes in the Violin I phrase. Nudge each note individually by eye and ear, ±5–15ms off grid — slightly early feels urgent, slightly late feels relaxed. Vary it note to note; uniform offset just creates a new, different grid.
3. Select the Cello/Bass notes. Push them 10–20ms **later** than the written beat — this mimics the natural attack lag of low strings and immediately makes the bottom of your mix feel like a real section instead of a sequenced loop.
4. Leave the melodic lead line (flute, Violin I solo) essentially on the beat or very slightly ahead (5–10ms early) — this keeps the melody feeling forward and present against a slightly lazier accompaniment.

This 60-second manual pass, applied consistently, does more for believability than any plugin. If your DAW includes a humanize function (most do), use it as a starting randomization and then manually override the bass lag and lead-line push by hand — automatic humanization alone tends to randomize uniformly and misses this directional nuance.

---

## Part 3: Dynamics, Articulation Choice, and Section Balance by Ear

### 3.1 Matching velocity and CC11 to real dynamic markings

Use this as your working reference when translating a score dynamic into MIDI data — not a rigid formula, a starting point you adjust by listening.

| Dynamic | Velocity | CC11 | Context |
|---|---|---|---|
| ppp | 15–25 | 30–40 | Extremely rare; whisper-quiet solo moments |
| pp | 25–40 | 40–55 | Quiet accompaniment, backgrounds |
| p | 40–55 | 55–70 | Common lyrical/soft passages |
| mp | 55–70 | 70–85 | Comfortable neutral playing |
| mf | 70–85 | 85–95 | Default orchestral texture |
| f | 85–100 | 95–110 | Climactic, full ensemble |
| ff | 100–115 | 110–120 | Dramatic peaks, powerful brass |
| fff | 115–127 | 120–127 | Rare maximum — risk of clipping, use sparingly |

The critical move for a real crescendo: change **both** numbers together. A p→f crescendo over 4 bars should ramp velocity roughly 50→90 across the note entries *and* CC11 roughly 60→105 across the phrase. Move only CC11 and the crescendo sounds like a volume knob being turned (flat, unconvincing). Move only velocity and you get discrete jumps between sample layers (stepped, mechanical). Move both and the crescendo breathes like a real section playing harder.

### 3.2 Choosing articulation for clarity, not just style

Shorter articulations (staccato, spiccato) have faster attack transients, which pushes more energy into upper harmonics — they sound brighter and more separated in a dense mix. Longer articulations (sustain, legato) carry more fundamental energy and blend, which is exactly what you want for pads and harmonic beds but exactly what causes mud in busy contrapuntal passages.

**Practical rule for orchestration density:** in a thick tutti passage where multiple sections are moving simultaneously, favor staccato/spiccato in the inner voices (violas, horns) to keep lines distinct, and reserve long sustain for the outer voices (melody on top, bass foundation below) where you want glue rather than separation. If a passage sounds muddy on playback, the first fix to try is swapping an inner-voice sustain line to portato or staccato before reaching for EQ.

**Drill:**
1. Write the same four-bar passage with all parts on sustain. Bounce and listen — note the warm but potentially cluttered texture.
2. Switch the Viola and Horn lines to staccato/portato, keep melody and bass on sustain. Bounce and compare.
3. You should hear the middle of the texture open up — individual lines become distinguishable rather than fused into a wash.

### 3.3 Round-robin and the machine-gun fix

Repeated notes at identical velocity on a library without good round-robin (sample rotation across repeats) sound like a stuck recording — the "machine-gun effect." You'll hear it immediately on repeated trumpet or snare hits.

**Quick fix that works on any library:** manually vary velocity on repeated notes by ±5–8 points note to note (90, 84, 91, 87, 93...) instead of a flat 90 across all sixteen hits. This forces the sample engine to cross different velocity layers even if round-robin is weak, breaking up the exact-repeat perception. Also nudge timing by a few ticks per repeat (see humanization, 2.4) — identical timing plus identical velocity is what makes the ear lock onto the repetition in the first place.

---

## Part 4: Troubleshooting at the Session Level

These are the failures you will actually hit while scoring, and the fastest fix for each.

| Symptom | Cause | Fix |
|---|---|---|
| Audio dropouts/clicks during playback | Buffer too small for polyphony load, CPU overload | Raise buffer to 512–1024 samples for mixing; freeze CPU-heavy tracks (right-click → Freeze Track) |
| Legato sounds like separate reattacks, no slide | Notes spaced >200ms apart, or no legato keyswitch active | Tighten note spacing so adjacent notes touch/slightly overlap; confirm keyswitch sent ≥150ms before phrase |
| Machine-gun repeated notes | No round-robin, or RR patch not loaded | Load the RR-enabled version of the patch; manually vary velocity ±5–8 per repeat as a fallback |
| Phrase has no felt dynamic motion | CC11 flat or left at default | Draw an actual ramp in the automation lane; never leave CC11 as a flat line across a phrase of more than 2 bars |
| Wrong articulation plays on first note of phrase | Keyswitch placed too close to or after the note | Move keyswitch earlier, minimum 150–200ms before note-on; verify in the MIDI list/event editor |
| Low end sounds muddy/boomy | Overlapping fundamentals in 80–200Hz between cello, bass, bassoon, low horn | High-pass non-bass instruments at 100–120Hz; separate cello/bass by octave in the arrangement itself |
| Brass sounds harsh and fatiguing | Velocities pushed above 110 across the whole section simultaneously, excess 2–4kHz buildup | Cap section velocities at 100–105 in tutti writing; cut 3kHz by 2–3dB on brass bus |
| Notes cut off unexpectedly in dense passages | Polyphony ceiling hit in the sample engine | Check voice count display (Kontakt shows "Voices: n/max" top right); raise the limit in engine settings or freeze tracks to free voices |
| Tracks drift out of sync after bouncing | Plugin Delay Compensation disabled, convolution reverb latency uncompensated | Enable automatic PDC in DAW audio preferences; re-bounce |

---

## Part 5: Mixing Pass — Balance, EQ, and Space

### 5.1 Order of operations

Mix in this order, every time. Skipping ahead (reaching for EQ before balance is right) wastes time correcting problems that a fader move would have solved.

1. **Balance with faders only.** No EQ, no reverb. Get Violin I audible against Cello, get brass sitting under strings in tutti, get woodwind counterpoint audible but not dominant. If you can't get a good balance with faders alone, the orchestration itself (voicing, register choices) is the actual problem — fix that before touching the mixer again.
2. **Subtractive EQ.** Cut what's clashing — usually 200–400Hz mud between cello/bass/bassoon/horn, or 2–4kHz harshness on overdriven brass velocities.
3. **Additive EQ.** Gentle presence boosts (+1 to +3dB) in the 2–5kHz range for clarity, air boosts (+1 to +3dB) above 10kHz on strings for shimmer. Small moves — if you're reaching for +6dB, you likely have a balance problem, not an EQ problem.
4. **Reverb and depth.** 15–25% wet mix for a symphonic hall feel on the full ensemble bus; closer to 5–10% for intimate chamber writing. Send brass and percussion to a slightly different (usually larger, more diffuse) reverb than strings to simulate real stage depth.
5. **Final dynamics.** Light bus compression (2:1 ratio, slow attack, auto release) to glue the mix; a limiter on the master only as a safety ceiling (-1dBFS), not as a loudness tool.

### 5.2 EQ reference by frequency zone

| Range | Typical content | What to do |
|---|---|---|
| 20–60Hz | Sub-bass rumble, stage noise | High-pass everything except kick/contrabass at 30–40Hz |
| 60–120Hz | Tuba, double bass, timpani fundamentals | Narrow cut if boomy; this is where masking between bass instruments happens |
| 120–250Hz | Cello/bass body, low horn/trombone | Primary mud zone — cut 1–3dB here on everything except the actual bass instrument if the mix feels thick |
| 250–500Hz | Horn/trombone warmth, viola/cello body | Light boost here (+1–2dB) gives fullness without mud |
| 1–2kHz | String presence, woodwind clarity | Boost for intelligibility in dense tutti |
| 2–5kHz | Bow noise, articulation detail, brass bite | Boost carefully for definition; this is also where harshness lives — cut here first if brass is fatiguing |
| 5–10kHz | String air, flute breath, cymbal shimmer | Gentle boost for sparkle |

### 5.3 Final quality check before calling a mockup done

Run through this list on headphones and monitors both. A passing mockup should hit most of these:

- Quietest passage and loudest passage differ by at least 15–20dB in perceived loudness — if everything sits at similar volume, you've been riding velocity without CC11.
- No section is perfectly quantized — spot-check the bass line in the piano roll; it should show deliberate lag behind the beat.
- At least two or three different articulations appear per instrument across any 8-bar span — an all-legato string part through an entire piece reads as flat and unperformed.
- CC11 automation lanes show actual curves, not flat lines longer than two bars.
- No red clipping on any channel meter; master peaks stay under -1dBFS.
- Soloing the low strings/brass reveals no audible mud buildup in the 150–300Hz range.
- Legato string lines have audible connecting slides between notes, not discrete reattacks.

---

## Quick Reference: MIDI CC Assignments for Orchestral Work

| CC# | Name | Use |
|---|---|---|
| CC1 | Modulation | Vibrato depth — ramp in gradually (0→60 over ~1 second) rather than applying it from note onset, which sounds unnatural |
| CC11 | Expression | Primary phrase dynamics — your main crescendo/diminuendo tool |
| CC7 | Volume | Set once per track for section balance; don't automate this for phrasing |
| CC64 | Sustain | Pedal on/off — mainly relevant for piano/harp patches |
| CC2 | Breath Controller | Alternative to CC11 for winds/brass if your controller supports it — more expressive than static values |
| CC32 | Articulation (VSL) | CC-based articulation switching, safer than keyswitches for heavy automation |
| CC74 | Timbre/Brightness | Filter or harmonic brightness control, library-dependent |

## Quick Reference: Instrument Ranges (Concert Pitch Unless Noted)

| Instrument | Full Range | Comfortable Writing Range | Transposition |
|---|---|---|---|
| Violin | G3–E7 | G3–E6 | None |
| Viola | C3–A6 | C3–E5 | None |
| Cello | C2–C6 | C2–G4 | None |
| Double Bass | E1–G4 | E1–E3 | Sounds octave below written |
| Flute | C4–D7 | C4–C6 | None |
| Oboe | Bb3–A6 | Bb3–F5 | None |
| Clarinet (Bb) | D3–G6 | E3–C6 | Sounds major 2nd below written |
| Bassoon | Bb1–Eb5 | Bb1–Bb4 | None |
| Horn (F) | Bb2–F5 | F3–C5 | Sounds perfect 5th below written |
| Trumpet (Bb) | E3–D6 | F#3–C5 | Sounds major 2nd below written |
| Trombone | E2–Bb5 | E2–Bb4 | None |
| Tuba | D1–F4 | D1–Bb3 | None |
| Timpani (4 drums) | D2–A3 | Tuned per key: D2, G2, C3, F3 | None |

Mastery here comes from repetition: score a phrase, bounce it, listen critically against a real recording of the same instrumentation, identify exactly what's missing (usually dynamics, humanization, or legato spacing), fix it, and repeat. The checklist and reference tables above are there to speed up that diagnostic loop, not to replace the listening.
