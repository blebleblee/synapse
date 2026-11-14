# Mixing Masterclass: Balance, EQ, Dynamics, and Space

## Mission Briefing

Mixing is translation: you take a stack of raw tracks — each recorded in a different room, with different mics, different proximity effects, different player dynamics — and translate them into one coherent statement that works on earbuds, car speakers, and a club system. Every move you make changes air pressure in a measurable, audible way, and your ear is the measuring instrument you're training.

This masterclass runs on a working multitrack session: drums (kick, snare, overheads, toms), bass, 2 guitars, lead vocal, 2 backing vocals, keys. Every technique below is something you dial in by ear in minutes, with concrete starting numbers so you're never guessing from zero.

### Session Setup (5 minutes, every single time)

1. **Gain-stage before touching a single plugin.** Solo each channel, play the loudest chorus, and set input trim/clip gain so peaks land around -18 dBFS to -12 dBFS RMS on your DAW meters. Most DAWs run 24-bit float internally with huge headroom, but analog-modeled plugins are tuned to behave correctly in that range. A kick hitting -6 dBFS before any processing makes every compressor downstream react wrong — too much gain reduction, too fast, because the detector sees levels it wasn't designed for.
2. **Label and color-code tracks.** Drums = red, bass = orange, guitars = blue, vocals = yellow, keys = green. You're about to make 40+ decisions; don't burn attention hunting for tracks.
3. **Build group buses before you touch a single fader.** Route all drum tracks to a DRUM BUS, guitars to a GTR BUS, vocals to a VOX BUS, all of those into a MIX BUS. This is non-negotiable: bus glue compression and bus EQ are where mixes get cohesion, and you cannot bolt that on at the end.
4. **Load a reference track.** A commercially released song in a similar genre, on its own fader, gain-matched with a loudness meter — not by ear, because ears lie about level, especially about bass and top end at different volumes.

```
subgraph session_routing ["Signal Flow: Tracks to Master"]
  kick["Kick"] --> drumbus["Drum Bus"]
  snare["Snare"] --> drumbus
  oh["Overheads"] --> drumbus
  bass["Bass DI + Amp"] --> bassbus["Bass Bus"]
  gtr1["Rhythm Gtr"] --> gtrbus["Guitar Bus"]
  gtr2["Lead Gtr"] --> gtrbus
  lv["Lead Vocal"] --> voxbus["Vocal Bus"]
  bv["BGVs"] --> voxbus
  keys["Keys"] --> mixbus["Mix Bus"]
  drumbus --> mixbus
  bassbus --> mixbus
  gtrbus --> mixbus
  voxbus --> mixbus
  mixbus --> master["Master Fader / Limiter"]
end
```

---

## Exercise 1: Balance Before Anything Else

### Why this order matters

Loudness perception is logarithmic and frequency-dependent — at low playback volumes your ear needs more bass and treble energy to perceive them as "equally loud" as midrange (the Fletcher-Munson effect). If you EQ and compress before the fader balance is right, you solve the wrong problem. You'll boost a vocal's presence band to "cut through" when the real issue is the vocal fader sitting 4 dB too low. Fix level first. Always.

### Step-by-Step: The Fader Pass

1. **Play the loudest section. Pull every fader to -∞ except kick and snare.** Bring them up until they sound like a record — not loud, correct relative to each other. Kick usually sits slightly forward of snare.
2. **Add bass.** Balance against kick using the "one instrument or two fighting" test: if you can't tell where kick ends and bass begins in the low end, that's usually a good sign — they're glued, not broken.
3. **Add the rest of the kit** — overheads, room mics, toms — built around the kick/snare foundation.
4. **Bring in the rest of the low end**, then rhythm instruments (guitars, keys), then lead vocal last, pulled up until it sits clearly on top without shouting.
5. **Add backing vocals and ear-candy** (tambourine, extra percussion, pads) last, at a level you feel more than you can name if asked to point it out.

**Target reference levels** (gain-staged correctly, RMS-ish feel on a calibrated monitor, not peak-chasing):

| Element | Target |
|---|---|
| Kick & snare | Anchor — treat as 0 dB reference point |
| Bass | Within ±1–2 dB of kick energy in the 60–120 Hz range |
| Lead vocal | 2–3 dB "forward" of the instrumental bed — the first thing your ear locks onto |
| BGVs | 4–6 dB below lead vocal |
| Cymbals/overheads | Supportive; should vanish if soloed against a reference track's overheads at matched level |

### Drill: Fader Balance Blind Test

15 minutes a day for two weeks. This trains fast, accurate fader decisions independent of plugins.

1. Load any multitrack session, mute everything.
2. Bring up two tracks (e.g. kick + bass) and balance them by ear in under 30 seconds.
3. Add one track at a time, re-balancing the whole stack on each addition, timing yourself.
4. Progression target: full 10-track rough balance in 10 minutes → 5 minutes → 3 minutes.

---

## Exercise 2: EQ — Carving Space, Not Just "Making It Sound Good"

### The physics in one paragraph

Every instrument radiates a spectrum of harmonics stacked on its fundamental pitch. When two instruments share a fundamental or strong harmonic region — bass guitar and kick both living in 60–120 Hz, or vocals/guitars/keys all fighting in 200–500 Hz "mud" — their waveforms sum, and concentrated energy in a narrow band causes masking: your ear can't resolve which instrument owns that frequency, so the mix reads thick and undefined rather than loud. EQ's real job in a mix (as opposed to mastering or sound design) is carving complementary space — deciding which instrument owns which range and cutting the others out of it, so each sound has room to be heard clearly at a lower overall level. This is subtractive thinking, not "make it sound good by boosting."

### Practical EQ Map (memorize this — it's your starting point every time)

| Frequency range | Who owns it | What to do with everyone else |
|---|---|---|
| 20–60 Hz | Kick fundamental, sub bass | High-pass everything else — guitars, vocals, keys don't need anything below 80–100 Hz |
| 60–120 Hz | Bass guitar fundamental, kick body | Carve a notch in bass OR kick (not both) to let the other through |
| 200–500 Hz | "Mud" / boxiness | Cut 2–4 dB, wide Q, on guitars/keys/vocals to clear buildup |
| 500 Hz–2 kHz | Vocal body, guitar midrange, snare body | Most crowded zone — narrow surgical cuts on whatever's competing |
| 2–5 kHz | Vocal presence/consonants, snare crack, guitar attack | Boost sparingly for clarity and cut-through |
| 5–10 kHz | Cymbal shimmer, vocal sibilance, pick noise | Watch for harshness; de-ess vocals if sibilant |
| 10–20 kHz | "Air" — breath, cymbal sheen | Gentle high-shelf (+1–2 dB) adds polish; rarely need more |

### Step-by-Step: EQ on the Kick Drum

1. **High-pass at 30 Hz**, steep slope (24 dB/octave). This removes sub-rumble below the instrument's useful range — cleanup, not tone shaping.
2. **Find the boxy frequency.** Sweep a narrow-Q (Q=4–6) bell boost of +6 dB slowly through 300–600 Hz. Where it sounds most "cardboard box" is your cut point — pull that down -3 to -5 dB.
3. **Find the thump.** Sweep through 60–100 Hz the same way; boost +2 to +3 dB wide-Q (Q=1) where the kick feels like it's moving air.
4. **Find the beater click.** Boost a narrow band around 2.5–4 kHz if the kick needs to cut through a busy mix. Skip this entirely for genres wanting a softer kick.

### Step-by-Step: EQ on the Lead Vocal

1. **High-pass at 80–100 Hz.** Removes mic rumble and proximity-effect boom without touching the voice's fundamental (adult voice fundamentals rarely go below 100 Hz).
2. **Cut mud at 200–300 Hz**, -2 to -3 dB, wide Q — especially on close-mic'd vocals with heavy proximity effect.
3. **Boost presence at 3–5 kHz**, +2 to +3 dB. The single most reliable "make the vocal pop" move — it's the same range your ear uses to parse consonants in speech.
4. **Check sibilance at 6–9 kHz.** If "s" and "t" sounds spike, that's a job for a de-esser (Exercise 3), not a static cut — the problem is transient, not constant.
5. **Air shelf above 10 kHz**, +1 to +2 dB, if the vocal needs breathiness/sheen without harshness.

### Drill: The Sweep-and-Cut Ear Trainer

The single best drill for developing EQ ears.

1. Solo any track. Insert a parametric EQ.
2. Set a bell boost to +12 dB (exaggerated on purpose), Q = 4.
3. Slowly sweep the frequency knob from 100 Hz to 10 kHz over about 20 seconds while listening.
4. Stop at every frequency that sounds notably bad (harsh, boxy, thin, boomy) and name it out loud: "that's boxy," "that's harsh."
5. Repeat daily on different instruments. Within 2–3 weeks you'll identify problem frequencies within a few hundred Hz by ear alone — the difference between engineers who sweep-and-guess and ones who know "that's 400 Hz mud" on contact.

---

## Exercise 3: Compression — Shaping Dynamics, Not Just "Making It Louder"

### The physics in one paragraph

A compressor is an automatic volume fader that turns the signal down once it crosses a threshold, at a rate set by the ratio, with timing governed by attack (how fast it reacts) and release (how fast it lets go). Musically, this lets you control the shape of a sound's envelope — transient "snap" versus sustained "body" — independent of the player's natural dynamics. A slow attack lets the initial transient (pick attack, stick hit) through uncompressed before clamping down on the sustain, making the sound punchier. A fast attack catches the transient immediately, taming aggressive peaks but reducing perceived punch.

### Step-by-Step: Compressing the Bass Guitar (where beginners most often get it wrong)

1. **Threshold:** set so the compressor engages only on the loudest notes at first — watch gain reduction, aim for 3–4 dB on peaks.
2. **Ratio:** start at 4:1 for control without squashing. Bass needs consistency more than character, so don't undersell this.
3. **Attack:** 10–30 ms — slow enough to let the pluck/pick transient through for definition, fast enough to control the sustain before it runs away.
4. **Release:** follow the tempo. A reliable starting method: set release so the gain reduction meter returns to 0 right as the next note hits. Use "Auto" release if your plugin has smart program-dependent release — most modern ones do this well.
5. **Makeup gain:** bring the output back up to match the bypassed level. A/B against bypass to confirm you're hearing "more even," not just "louder."

### Step-by-Step: Compressing the Lead Vocal (2-stage approach used on most pro vocal chains)

**Stage 1 — Leveling compressor** (controls overall dynamic range, stays transparent):
- Ratio: 2:1 to 3:1
- Attack: 15–25 ms (lets consonants through)
- Release: 80–150 ms, or auto
- Threshold: aim for 4–6 dB average gain reduction across a verse
- Goal: make the performance consistent, not squashed. You should not consciously hear it working.

**Stage 2 — Character/peak-catching compressor** (controls occasional loud words, adds tone):
- Ratio: 4:1 to 6:1
- Attack: 1–5 ms (fast, catches the word that jumps out)
- Release: 50–100 ms
- Threshold: set so it only grabs the loudest 10% of phrases, 2–3 dB max reduction
- This stage is insurance, not the main leveling tool.

### Drill: Gain Reduction Meter Calibration

1. Solo a track with a compressor inserted, ratio locked at 4:1.
2. Lower the threshold in 1 dB steps while watching the gain reduction meter and listening.
3. At each step, say out loud what changed: "more control," "starting to pump," "breathing audibly," "squashed, no dynamics left."
4. Identify the exact dB of gain reduction where the effect becomes audible as "compression" rather than "natural dynamics." This threshold is different for every instrument — train your ear to recognize it per-source.

### De-essing (a specialized fast compressor for sibilance)

Insert a de-esser after your main EQ and compression on vocals. Target 5–8 kHz, listen specifically to "s" and "sh" sounds, and set threshold so the de-esser engages only on sibilant consonants — confirm the gain reduction meter lights up only on "s" sounds, not every word. Over-de-essing causes a lisping artifact; if you hear that, raise the threshold back up.

---

## Exercise 4: Bus Processing and Glue

Individual track processing only gets you partway. Mixes that sound like "one thing" use bus compression to tie elements together.

### Drum Bus Glue Compression

1. Route all drum tracks to a bus. Insert a VCA-style compressor (dbx 160 or SSL bus comp emulations are the standard here).
2. Ratio: 4:1. Attack: 10 ms (slow enough to let transients through). Release: Auto or 100 ms.
3. Threshold: dial in for 2–4 dB of gain reduction on the loudest hits — just enough that the meter moves on every kick/snare hit.
4. This is glue — it makes the kit breathe together as one instrument instead of independent hits.

### Mix Bus Processing (the final 2%)

1. **Light bus compression:** 1.5–2:1 ratio, slow attack (30 ms), auto release, 1–2 dB max reduction. This should be nearly inaudible — cohesion insurance, not a creative effect.
2. **Gentle mix-bus EQ:** often just a high-shelf +0.5 dB at 10 kHz for air and a low-shelf +0.5 dB at 60 Hz for weight. Nothing dramatic — big tonal moves belong on individual tracks, not the master.
3. **Leave headroom.** Peak the mix bus around -6 dBFS before any mastering limiter touches it. If you're already slamming a limiter during mixing, you've lost the ability to make final decisions at mastering.

```
subgraph bus_processing ["Bus Processing Chain"]
  tracks["Individual Tracks (EQ + Comp per track)"] --> busA["Sub-Bus (Glue Compression)"]
  busA --> mixbus2["Mix Bus (Light Comp + Gentle EQ)"]
  mixbus2 --> headroom["-6 dBFS Headroom Target"]
  headroom --> mastering["Mastering Stage (separate session)"]
end
```

---

## Exercise 5: Space — Panning, Reverb, Delay, and Phase

### Panning for a 3D Soundstage

Think of the stereo field as a stage. Kick, snare, bass, and lead vocal sit dead center — the structural spine of the mix, mono-compatible and anchoring. Everything else gets placed left-right to avoid collision:

- **Overheads/cymbals:** hard-panned per the overhead mic positions. If recorded in stereo, leave them — they're already correct.
- **Rhythm guitar:** pan to 25–35% left; second rhythm guitar or keys to 25–35% right (balance, not identical sounds on both sides).
- **Lead guitar solos:** typically center or slightly off-center, since they become the focal point when they appear.
- **Backing vocals:** spread wide, 50–80% left/right, often doubled takes panned hard opposite each other.

### Reverb: Depth, Not Mud

Use reverb on sends, not inserts, so every track shares the same "room" and sits in a consistent depth of field.

1. Create 2 reverb return tracks: a short room/plate (0.8–1.2 sec decay) for drums, and a longer hall (1.8–2.5 sec decay) for vocals and pads.
2. Send amounts: drums get 5–10%, lead vocal 10–20%, backing vocals 20–30% (they're meant to feel "behind" the lead).
3. **High-pass the reverb return itself at 300–500 Hz.** This is the single biggest fix for "muddy reverb" — the low end of a reverb tail is almost always useless mud. Cut it ruthlessly.
4. **Pre-delay** (10–30 ms on vocal reverb) keeps the dry vocal intelligible by delaying the onset of the reverb just enough that consonants cut through before the wash arrives.

### Delay for Width and Depth

A short stereo delay (1/8 note or 1/8 dotted, synced to tempo) on a doubled vocal or guitar part creates width without the smear of reverb. Feedback at 10–20%, high-passed at 500 Hz and low-passed at 8 kHz, so the repeats sit behind the dry signal instead of on top of it.

### Phase Coherence Check (do this before you trust any multi-mic'd source)

Overheads, snare top/bottom, and DI+amp bass pairs are all vulnerable to phase cancellation — two mics capturing the same event at slightly different times, which cancels frequencies and thins the sound out when summed to mono.

1. **The practical test:** solo the pair of mics in question, flip the mix to mono (every DAW has a mono-sum button in the master or monitor section), and listen for the sound getting noticeably thinner or losing low end compared to stereo.
2. **The fix:** nudge one track a few milliseconds earlier/later until the mono sum sounds fullest — not just "less thin," fullest — or use a phase-alignment plugin to auto-correct based on waveform correlation. On snare top/bottom, flipping the bottom mic's polarity (the "phase" button, really a 180° polarity flip) is standard practice and usually fixes it instantly.
3. **Always check your final mix in mono before calling it done.** Club PAs, phone speakers, and many PA systems sum to mono, and a mix that falls apart in mono will fail live.

---

## Exercise 6: Fault Diagnosis — Real Problems, Fast Fixes

The actual failure modes you'll hit in every real session.

```
subgraph diagnosis_tree ["Mix Problem Diagnosis Flowchart"]
  start["Mix sounds off"] --> q1{"Muddy / undefined low-mids?"}
  q1 -->|Yes| fix1["Check 200-500 Hz buildup across guitars/keys/vox; high-pass non-bass elements"]
  q1 -->|No| q2{"Vocal buried / not cutting through?"}
  q2 -->|Yes| fix2["Check 3-5 kHz presence; check fader level first; check masking from guitars in same range"]
  q2 -->|No| q3{"Thin / weak on mono playback?"}
  q3 -->|Yes| fix3["Phase check multi-mic sources; flip polarity on snare bottom / DI"]
  q3 -->|No| q4{"Pumping / breathing artifact?"}
  q4 -->|Yes| fix4["Slow compressor release; reduce ratio or raise threshold; check sidechain filter on bus comp"]
  q4 -->|No| q5{"Harsh / fatiguing on long listen?"}
  q5 -->|Yes| fix5["Check 2-4 kHz overall buildup; check de-esser threshold; check cymbal overheads EQ"]
end
```

### Fault 1: The Mix Falls Apart in Mono
**Symptom:** Full and wide in stereo, thin and hollow in mono.
**Diagnosis:** Phase cancellation between multi-mic'd sources, or over-reliance on stereo widener plugins that use phase tricks rather than real stereo content.
**Fix:** Run the phase coherence check from Exercise 5 on every multi-mic'd source. Remove or reduce stereo widener plugins one at a time and re-check mono after each removal to isolate the culprit.

### Fault 2: Compressor Pumping on the Mix Bus
**Symptom:** You can hear the compressor "breathing" — level visibly rising and falling in time with the kick, audible as an artifact rather than control.
**Diagnosis:** Release time too fast for the tempo, or ratio/threshold too aggressive for bus-level "glue" duty.
**Fix:** Slow the release (try Auto mode first), raise the threshold so gain reduction tops out at 2–3 dB instead of 6+, or lower the ratio to 2:1. If the kick is triggering it unnecessarily, add a sidechain high-pass filter at 100–150 Hz on the compressor's detector so sub-bass doesn't trigger excessive reduction.

### Fault 3: Vocal Disappears When the Full Band Comes In
**Symptom:** Vocal sounds great solo'd, vanishes the moment guitars and cymbals enter.
**Diagnosis:** Masking — guitars and vocal sharing 500 Hz–3 kHz energy, vocal fader actually too low once full-mix context reveals it, or inconsistent vocal dynamics against a wall of sustained guitar.
**Fix:** Cut competing midrange in the guitars, not the vocal — carve the room around the vocal rather than over-boosting it to compensate. Re-check vocal fader level in full-mix context, not solo. Add the Stage 2 peak-catching compressor from Exercise 3 if word-to-word inconsistency is the real issue.

### Fault 4: Snare Sounds Thin and Weak Despite Boosting EQ
**Symptom:** Boosting 200 Hz and 5 kHz on the snare isn't helping — it still sounds flat.
**Diagnosis:** Almost always a top/bottom mic phase issue, or the snare being masked by overheads/room mics carrying snare energy out of phase with the close mic.
**Fix:** Flip polarity on the snare bottom mic first — the single most common fix in live recording. If overheads are involved, nudge the close mic's track earlier by 1–3 ms to align wavefronts, or use a dedicated phase-alignment plugin referencing the overheads as the time source.

### Fault 5: Session CPU Overload / Plugin Crashes Mid-Mix
**Symptom:** DAW stutters, drops out, or crashes with a plugin-related error during playback.
**Diagnosis:** Too many real-time instances of CPU-heavy plugins (convolution reverb, heavy saturation, lookahead limiters) without bus consolidation.
**Fix:** Freeze or render tracks with finalized processing to audio (every major DAW has a "Freeze Track" command). Consolidate reverb/delay sends onto shared buses instead of per-track instances. If a specific plugin crashes, check for a buffer size mismatch — raise your audio buffer size in preferences during mixing; you don't need low-latency monitoring once tracking is done.

---

## Quick Reference: Signal Chain Order and Starting Points

### Standard insert order per channel
EQ (corrective, cuts) → Compressor → EQ (tonal, boosts) → De-esser (vocals only) → Saturation/character (optional) → Send to reverb/delay buses

### Starting-point cheat sheet

| Element | High-pass | Key cut | Key boost | Comp ratio | Comp attack |
|---|---|---|---|---|---|
| Kick | 30 Hz | 300–500 Hz (-3 dB) | 60–80 Hz, 3 kHz | 4:1 | 10–20 ms |
| Snare | 80 Hz | 400 Hz (-3 dB) | 200 Hz, 5 kHz | 5:1 | 5–10 ms |
| Bass | 30 Hz | 800 Hz (-2 dB) | 80 Hz, 1 kHz | 4:1 | 10–30 ms |
| Lead Vocal | 80–100 Hz | 250 Hz (-3 dB) | 3–5 kHz, air shelf | 3:1 (+ 5:1 stage 2) | 15–25 ms |
| Rhythm Guitar | 100 Hz | 300–500 Hz (-3 dB) | 2–3 kHz | 3:1 | 15 ms |
| Overheads | 200 Hz | — | 8–10 kHz shelf | light/none | — |

### Essential DAW/plugin workflow commands
- **Insert plugin:** right-click the channel's processing lane → Insert → select from category
- **A/B bypass check:** map a bypass toggle shortcut if your DAW doesn't default one — use it constantly, trust your ears only in direct comparison
- **Solo isolate:** use "Solo in Place" so bus sends don't vanish when soloing a track that feeds a reverb bus
- **Gain stage check:** input trim/clip gain, separate from the fader — fix level problems here before touching the fader
- **Freeze/render track:** right-click track header → Freeze, to save CPU on finalized processing chains
- **Mono check:** utility plugin or monitor-section mono button — check every mix before export

### Core math worth knowing (stop here — don't over-engineer it)

**Gain reduction** is the difference, in dB, between the input level above threshold and the output level after the ratio is applied:

$$GR_{dB} = (Input_{dB} - Threshold_{dB}) \times \left(1 - \frac{1}{Ratio}\right)$$

Example: input peaks 10 dB above threshold, ratio 4:1 → gain reduction = 10 × (1 − 0.25) = 7.5 dB. This is why 4:1 on a loud transient still lets real punch through — it's controlled reduction, not a brick wall.

**Headroom target for the mix bus before mastering:** peaks around -6 dBFS, RMS around -18 to -14 dBFS, so a mastering limiter has genuine room to work instead of just undoing an already-squashed mix.

Phase coherence, dynamic range, and signal-to-noise are things you verify by ear and by meter — correlation meter, mono-sum check, gain reduction meter — during the exercises above. You don't calculate them by hand in a mixing session; your metering plugins already do that in real time.
