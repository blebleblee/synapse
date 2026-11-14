# Lesson 3: Expansion and Noise Gating — Cleaning and Shaping the Mix

## 1. What Problem This Actually Solves

Compression squeezes dynamic range from the top down — it turns loud things down. **Expansion and gating do the opposite: they turn quiet things down, or kill them outright.** Reach for this tool whenever a track has unwanted low-level content sitting beneath the music you actually want to hear.

Real studio and stage situations where this is the fix — not EQ, not compression:

- A snare mic bleeding hi-hat and kick drum between snare hits.
- A vocal mic picking up headphone bleed, room hum, or breath noise between phrases.
- A distorted guitar amp with audible 60/120 Hz hum and fan noise under the riffs — fine while playing, ugly in the rests.
- A bass DI with fret noise and amp hiss between notes, muddying the low end of a mix.
- A synth pad with a slow, noisy filter that needs its tail chopped for rhythmic tightness (gate used as an effect, not noise removal).

The physics in one paragraph: every microphone and every electrical signal chain has a noise floor — hiss, hum, bleed — sitting underneath the wanted signal. Simultaneous masking means that noise floor is inaudible *while* the loud wanted signal is present, but it becomes obvious the instant the wanted signal stops and the noise is left alone in the silence. Expansion and gating don't remove the noise — they make sure you never hear it on its own.

**Expansion** turns the gain down gradually below a threshold — a gentler cousin of compression's ratio, running in reverse. **Gating** is expansion pushed to an extreme ratio (10:1, 20:1, or ∞:1) so it behaves almost like an on/off switch. Same engine, different ratio setting, on most real plugins.

---

## 2. The Controls, and What Moving Each One Actually Does

| Parameter | What it does | Typical range | Live result if you get it wrong |
|---|---|---|---|
| **Threshold** | Level below which gain reduction kicks in | −60 dB to −10 dB | Too high: chops the start/end of notes (gate "eats" the attack). Too low: noise still leaks through between hits. |
| **Ratio** (expander) | dB of gain reduction per dB below threshold | 1.5:1 (gentle) to 10:1 (gate-like) | Too high: sounds choppy/unnatural on sustained sources. Too low: barely audible, noise still present. |
| **Attack** | How fast gain opens back up once signal crosses threshold | 0.1 ms – 20 ms | Too slow: clips off transients (snare sounds dull, pick attack disappears). Too fast: can click/pop on very fast attacks. |
| **Release** | How fast gain closes down after signal drops below threshold | 10 ms – 1000+ ms | Too fast: "chatters" or sounds unnaturally choppy (classic bad-gate snare sound). Too slow: lets noise ring out audibly, or causes pumping. |
| **Hold** | Minimum time the gate stays open once triggered, before release begins | 0 ms – 500 ms | Prevents chatter on sources with a slow natural decay (toms, cymbals) that would otherwise re-trigger the gate rapidly. |
| **Range / Depth** | Maximum gain reduction applied (not infinite) | −80 dB (full gate) to −10 dB (gentle expansion) | Setting range to full −∞ on a live vocal gate risks total dropout on soft words; −20 to −30 dB range usually kills the noise perceptually without the risk. |

**The ratio/range relationship is what people misunderstand most.** An expander at 2:1 with unlimited range eventually behaves like a hard gate anyway, if the signal drops far enough below threshold. A "gate" with a limited range of −15 dB is really just a steep expander — it never fully mutes. Stop thinking of expansion and gating as two different plugins. They're one tool with a ratio/range dial running from "gentle noise reduction" to "hard mute."

---

## 3. Gain Computer Behavior — The Part You Actually Need to Reason About

**Sidechain-driven gain reduction, in plain terms:**

1. The detector (peak or RMS) continuously measures the input level.
2. The detector level is compared to the threshold.
3. If detector level is **above** threshold → gain = unity (0 dB, pass through).
4. If detector level is **below** threshold → gain is reduced, by an amount set by the ratio, down to the limit set by the range.
5. The applied gain doesn't jump instantly — attack smooths the opening, release smooths the closing, so the result is a continuous envelope, not a stair-step.

**Peak vs. RMS detection — this decision matters more than any numeric setting:**

- **Peak detectors** respond to the instantaneous waveform. Fast, good for catching transient noise (clicks, a single loud bleed spike), but twitchy — they'll react to a single stray sample.
- **RMS detectors** average energy over a short window (typically 1–20 ms). Smoother, more musical, tracks perceived loudness better, but reacts slightly slower.

**Rule of thumb:** peak detection for drum gating (you need to catch the snare's fast attack precisely); RMS for vocal and bass expansion (you want smooth, musical gain changes that track sustained energy, not individual pressure spikes).

---

## 4. Lab 1 — Gating a Snare Mic to Kill Hi-Hat Bleed

**Goal:** the snare mic opens the instant the snare is hit and closes before the next hi-hat hit bleeds through, without chopping the snare's natural ring or chattering on ghost notes.

**Setup (any standard gate plugin — Waves C1 Gate, FabFilter Pro-G, stock DAW gate):**

1. **Detection source:** Peak, fast response.
2. **Threshold:** Start at −30 dB. Play the track. Watch the gain reduction meter — closed during hi-hat-only passages, wide open on snare hits.
3. **Attack:** 0.3–1 ms. Fast enough not to lose the snare's crack, slow enough to avoid a click.
4. **Hold:** 20–50 ms. Keeps the gate open through the snare's natural decay so it doesn't chatter as the drumhead's ring decays below threshold and bounces back above it.
5. **Release:** 80–150 ms. Long enough for a natural decay tail, short enough to close before the next hi-hat hit (typically every 200–250 ms at 120 BPM eighth notes).
6. **Range:** −20 dB, not −60 dB. Full mute between hits sounds unnatural and "sucks" the room ambience in and out. Leaving some bleed audible but 20 dB down reads as clean without sounding gated.

**Debugging checklist:**
- **Chattering (rapid on/off flutter on the decay tail):** increase Hold, or increase Release, or raise Threshold slightly.
- **Gate missed a soft snare hit entirely:** lower Threshold, or switch to RMS detection if the issue is ghost notes with slower attack.
- **Snare sounds clipped/truncated at the front:** Attack is too slow — bring it under 1 ms.
- **Audible "whoosh" or "zip" as gate closes:** Release is too fast for the natural decay — lengthen it, or lower Range so the tail fades into reduced level rather than slamming shut.

---

## 5. Lab 2 — Expanding a Vocal Track to Remove Headphone Bleed and Breath Noise

**Goal:** reduce — not eliminate — the noise floor between vocal phrases without audible pumping or a sense that the vocal is being "squeezed."

**Setup:**

1. **Detection source:** RMS, medium window (~10 ms). Vocals are sustained; you want smooth tracking, not reaction to every breath consonant transient.
2. **Ratio:** 1.5:1 to 2:1. Gentle expansion, not gating — you're lowering the noise floor by maybe 6–10 dB, not killing it to silence.
3. **Threshold:** Set by ear just above the visible noise floor on the meter, listening on headphones at a loud monitoring level during a quiet passage.
4. **Attack:** 5–10 ms. Vocals have soft onsets (breath before the note) — a fast attack here clips the leading edge of words.
5. **Release:** 150–300 ms. Smooth and slow enough to avoid audible gain movement during natural pauses between phrases.
6. **Range:** −8 to −12 dB. You're thinning the noise floor, not removing it. Pushing further starts sounding like an edit, which draws attention — the opposite of transparent processing.

**Why gentler is correct here and a hard gate is wrong:** a hard gate on a vocal creates an audible on/off artifact right at the edges of words — listeners hear the room/noise floor appear and disappear abruptly, which is far more distracting than a slightly-present, steady noise floor. Gentle expansion keeps the noise floor *continuously* present at reduced level, so there's no edit-point artifact for the ear to latch onto.

---

## 6. Lab 3 — Gate as Rhythmic Effect (Not Noise Removal)

A classic technique on synth pads, guitar power chords, and bass: use a gate keyed from a rhythmic trigger to carve a sustained sound into a rhythmic pattern (the "trance gate" chop, minus the sidechain compressor — here it's a straight gate with extreme settings).

1. Insert a gate on a sustained pad.
2. **Threshold:** set low enough that the pad is normally always above it (stays open by default).
3. **Attack:** near-instant, 0.1 ms.
4. **Release:** very fast, 5–15 ms — this creates the rhythmic "chop" rather than a smooth swell.
5. Automate the threshold (or use a sidechain trigger input if the plugin supports it) to pulse in time with the track — eighth notes, sixteenth notes, or a dotted-eighth pattern for the classic trance-gate pump.
6. **Practical trigger options:** many gate plugins accept an external sidechain input — route a MIDI-triggered drum hit or a square-wave LFO converted to audio into the sidechain, and the gate chops the pad in perfect sync without manual automation.

Same engine as Lab 1 and Lab 2 — only the intent changes, from "hide noise" to "create rhythm."

---

## 7. Signal Chain Placement — Where Gates and Expanders Go Relative to Other Processors

```
subgraph chain1 ["Typical Drum Channel Chain"]
    A["Mic Preamp"] --> B["Gate (peak detection, kills bleed)"]
    B --> C["EQ (shape tone after cleanup)"]
    C --> D["Compressor (control dynamics of cleaned signal)"]
    D --> E["Bus / Mix"]
end
```

**Why the gate goes first, before EQ and compression:**

- Compress before gating and the compressor raises the noise floor — that's literally what compression does to quiet signal — making the noise harder for the gate to remove cleanly. You end up gating a louder noise floor against a louder wanted signal, with a worse ratio between them.
- EQ before gating in a way that boosts low end can push hum/rumble right into the gate's detection range and confuse the threshold.
- Gate first = clean signal into every downstream processor = better results all round.

**Exception:** when you specifically want a gate to react to a *compressed* version of the signal — common in parallel drum processing, where an aggressively compressed, loud drum bus keys a gate on another track for extra punch — you deliberately break this rule. That's a sidechain-keying technique, not a signal-path error.

```
subgraph chain2 ["Sidechain-Keyed Gate (Parallel Drum Trick)"]
    F["Snare Mic (main signal)"] --> G["Gate"]
    H["Snare Mic (parallel path)"] --> I["Heavy Compressor"]
    I -->|"sidechain key input"| G
    G --> J["Punchy, Gated-and-Triggered Snare"]
end
```

---

## 8. Quick Reference — Starting Points by Source

| Source | Detection | Ratio/Range | Attack | Hold | Release |
|---|---|---|---|---|---|
| Snare/tom close mic | Peak | Range −15 to −25 dB | 0.3–1 ms | 20–50 ms | 80–150 ms |
| Kick drum close mic | Peak | Range −20 dB | 0.1–0.5 ms | 10–30 ms | 60–100 ms |
| Vocal (de-noise) | RMS | Ratio 1.5:1–2:1, Range −8 to −12 dB | 5–10 ms | — | 150–300 ms |
| Bass DI (fret noise) | RMS | Ratio 2:1–3:1, Range −10 dB | 3–8 ms | — | 100–200 ms |
| Guitar amp (hum/hiss) | RMS | Ratio 2:1–4:1, Range −15 dB | 2–5 ms | 10–20 ms | 100–250 ms |
| Rhythmic gate effect | Peak/sidechain | Range −40 dB+ | 0.1 ms | 0 ms | 5–15 ms |

Use these as starting points, then adjust Threshold by ear while soloing the track. It's the one parameter that's genuinely different on every take, every mic placement, and every room — no table of numbers substitutes for watching the gain-reduction meter against the actual noise floor you're trying to tame.

---

## 9. Ear-Training Drill: Hearing Gate Artifacts

Before trusting your settings on a real mix, train your ear to catch the three classic gate failure modes. Take any sustained source (long guitar chord, vocal note) and process it through a gate with deliberately bad settings, one variable at a time:

1. **Chatter:** Set Release to 5 ms with no Hold on a source with wavering sustain (tremolo guitar, vibrato vocal). Listen for the rapid flutter as the gate re-triggers. This is what you're listening for and fixing in every real mix.
2. **Premature cutoff:** Set Attack to 15+ ms on a percussive source. Listen for the dulled, late-arriving transient — the "thud before the click" effect.
3. **Audible close ("gate zip"):** Set Release to 3 ms on a sustained pad or reverb tail. Listen for the audible "zzzt" as the tail is sliced off rather than fading.

Once you can identify these three artifacts by ear in under a second of listening, you can set gates on a real session fast, by sound, without staring at meters.

---

## 10. Practice Routine — Building Gate-Setting Speed

Treat gate-setting like a physical skill, not a settings lookup. Run this weekly on real tracked material:

1. **5 minutes:** Load a raw, unprocessed snare or vocal take with audible bleed. Solo it. Set a gate from scratch, threshold-first, by ear only — no meters. Time yourself; aim to get a clean, natural-sounding result in under 3 minutes.
2. **5 minutes:** Deliberately break each parameter one at a time (per the ear-training drill above) and name the artifact out loud before fixing it. This builds the diagnostic reflex you need in a live session with a client or band waiting.
3. **5 minutes:** A/B your gated track against the raw track in context, full mix playing, at low monitoring volume (where masking is weakest and problems are most audible). If the gate is doing its job, you shouldn't be able to tell it's there — only that the noise is gone.

The goal isn't memorizing numbers from the quick reference table. It's getting fast enough at reading the gain-reduction meter and trusting your ear that you can set a working gate on an unfamiliar source inside a minute, under session pressure.
