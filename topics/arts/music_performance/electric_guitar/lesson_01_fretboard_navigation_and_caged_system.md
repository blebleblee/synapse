# Electric Guitar Masterclass: Fretboard Navigation, Technique & Musicianship

## Module 1: Hands-On Fretboard Orientation

### Your First Day on the Neck — What to Actually Practice

Six strings, 22–24 frets, two hands that must work independently before they work together. Left hand frets, right hand picks or strums. Train each hand separately before asking them to cooperate.

**Day-one physical checklist:**

- Thumb behind the neck, roughly opposite your middle finger — not hooked over the top.
- Wrist floats slightly away from the neck. If your palm touches the neck's back surface, the wrist has collapsed and your reach is compromised.
- Fret with the fingertip, not the pad. The finger should arch enough that the nail faces the ceiling.
- Press down just behind the fret wire (on the nut side), never on top of it and never floating halfway between two frets.
- Use only the pressure needed for a clean note. Electric guitar action runs roughly 1.5–2.5 mm at the 12th fret — you are moving a string a couple of millimeters, not crushing it.

**Right hand anchor:** Rest the heel of your picking hand lightly on or near the bridge saddles. This gives you a stable palm-muting reference. Pick angle should sit around 30–45° relative to the string — not flush, not perpendicular.

---

### The Six Strings — Names, Notes, and Memory Hooks

```mermaid
flowchart LR
    String6["String 6<br/>(thickest, lowest)"] --> E2["E2"]
    E2 --> Eddie1["Eddie"]
    
    String5["String 5"] --> A2["A2"]
    A2 --> Ate["Ate"]
    
    String4["String 4"] --> D3["D3"]
    D3 --> Dynamite["Dynamite"]
    
    String3["String 3"] --> G3["G3"]
    G3 --> Good["Good"]
    
    String2["String 2"] --> B3["B3"]
    B3 --> Bye["Bye"]
    
    String1["String 1<br/>(thinnest, highest)"] --> E4["E4"]
    E4 --> Eddie2["Eddie<br/>(octave)"]
```

Memory sentence: **E**ddie **A**te **D**ynamite, **G**ood **B**ye **E**ddie.

The two E strings share a pitch class two octaves apart. Everything learned on the low E string repeats on the high E string at the same fret numbers, an octave higher.

**Open string drill — Day 1:**
Say the string name and note name aloud as you pluck each string, one per click at 60 BPM. Reverse direction. Then skip strings (6→4→2→1→3→5). Repeat until "low E, A, D, G, B, high E" is as automatic as your own name.

---

### The Chromatic Map — Every Note Across the Neck

Moving one fret up raises pitch by a semitone. Moving to the adjacent thicker string at the same fret raises pitch by a perfect fourth (5 semitones) — except crossing from string 3 (G) to string 2 (B), which raises pitch by only a major third (4 semitones). This G→B exception is the single most important asymmetry on the instrument: it shifts every scale shape, chord voicing, and transferred interval by one fret the moment it crosses that boundary.

**Full note map — frets 0 through 12:**

```mermaid
flowchart LR
    subgraph strings ["Guitar Strings"]
        e1["e(1)"]
        B2["B(2)"]
        G3["G(3)"]
        D4["D(4)"]
        A5["A(5)"]
        E6["E(6)"]
    end
    
    subgraph frets ["Fret Positions: 0-12"]
        f0["0"]
        f1["1"]
        f2["2"]
        f3["3"]
        f4["4"]
        f5["5"]
        f6["6"]
        f7["7"]
        f8["8"]
        f9["9"]
        f10["10"]
        f11["11"]
        f12["12"]
    end
    
    e1 -->|"E4, F, F#, G, G#, A, A#, B, C, C#, D, D#, E5"| f0
    B2 -->|"B3, C, C#, D, D#, E, F, F#, G, G#, A, A#, B4"| f0
    G3 -->|"G3, G#, A, A#, B, C, C#, D, D#, E, F, F#, G4"| f0
    D4 -->|"D3, D#, E, F, F#, G, G#, A, A#, B, C, C#, D4"| f0
    A5 -->|"A2, A#, B, C, C#, D, D#, E, F, F#, G, G#, A3"| f0
    E6 -->|"E2, F, F#, G, G#, A, A#, B, C, C#, D, D#, E3"| f0
```

Fret 12 duplicates fret 0, one octave higher — every shape, pattern, and fingering repeats exactly 12 frets up the neck.

**Note geography drill — Weeks 1–2:**
Pick a note (start with A). Find every A on every string, frets 0–12, using the table, then without it. Target: locate any note on any single string within 2 seconds. Cover all 12 pitch classes over two weeks, one or two per day.

---

## Module 2: Left-Hand Technique — Ergonomics and Mechanics

### Fretting Hand Posture in Detail

Fingers are numbered 1 (index) through 4 (pinky). The thumb is unnumbered — an anchor, not a fretting finger (except specific thumb-over techniques in blues and rock).

**Correct arch:** Each finger curves so the tip contacts the string, preventing accidental muting of adjacent strings. Imagine cupping a small ball in your palm — that natural curve is your starting shape.

**Thumb placement rule:** For frets 1–5 (wider spacing), keep the thumb behind finger 2. For frets 7–12 (narrower spacing), the thumb can drift slightly toward the index side. Never let it creep over the top of the neck during single-note playing — that collapses the wrist and kills your reach.

**One finger per fret (OFPF) — when to use it:**
OFPF becomes comfortable around fret 5 and up, where spacing tightens. In first position (frets 1–4 on a 25.5" scale), stretching four fingers across four frets is demanding for beginners — build toward it gradually rather than forcing it on day one.

### Four-Finger Independence Exercises

Fingers 3 and 4 share a tendon branch from the extensor digitorum communis, which is why pinky independence from the ring finger is the hardest coordination task on the instrument. These drills target it directly.

**Exercise 1 — Spider Crawl (60 BPM → 100 BPM):**

```mermaid
flowchart LR
    subgraph e_string ["e string"]
        e5["5"]
        e6["6"]
        e7["7"]
        e8["8"]
        e5 --> e6 --> e7 --> e8
    end
    
    subgraph B_string ["B string"]
        B5["5"]
        B6["6"]
        B7["7"]
        B8["8"]
        B5 --> B6 --> B7 --> B8
    end
    
    subgraph G_string ["G string"]
        G5["5"]
        G6["6"]
        G7["7"]
        G8["8"]
        G5 --> G6 --> G7 --> G8
    end
    
    subgraph D_string ["D string"]
        D5["5"]
        D6["6"]
        D7["7"]
        D8["8"]
        D5 --> D6 --> D7 --> D8
    end
    
    subgraph A_string ["A string"]
        A5["5"]
        A6["6"]
        A7["7"]
        A8["8"]
        A5 --> A6 --> A7 --> A8
    end
    
    subgraph E_string ["E string"]
        E5["5"]
        E6["6"]
        E7["7"]
        E8["8"]
        E5 --> E6 --> E7 --> E8
    end
```

Fingers 1–2–3–4, one per fret, on every string pair, then move the whole pattern up and down the neck. No finger lifts until its next note demands it. Every note equal in volume and clarity.

**Exercise 2 — Ring/Pinky isolation (60 BPM):**

```mermaid
flowchart LR
    Start["Frets 5 & 6\nFingers 1 & 2\n(held down)"]

    subgraph fret7 ["Fret 7 — Finger 3"]
        E7["e | 7"]
        B7["B | 7"]
        G7["G | 7"]
    end

    subgraph fret9 ["Fret 9 — Finger 4"]
        E9["e | 9"]
        B9["B | 9"]
        G9["G | 9"]
    end

    Start --> fret7
    E7 --> E9
    B7 --> B9
    G7 --> G9
```

Fingers 1 and 2 remain planted on frets 5 and 6 throughout. Only 3 and 4 move. This isolates the exact tendon slip that frees the pinky from the ring finger. Five minutes daily for two weeks produces measurable improvement.

**Exercise 3 — Hammer-on/Pull-off strength (70 BPM):**

```mermaid
flowchart LR
    subgraph e_string ["e string"]
        e1["5"] --> e2["h7"]
        e2 --> e3["7"]
        e3 --> e4["p5"]
        e4 --> e5["5"]
        e5 --> e6["h7"]
        e6 --> e7["7"]
        e7 --> e8["p5"]
        e8 --> e9["5"]
        e9 --> e10["h7"]
        e10 --> e11["7"]
        e11 --> e12["p5"]
        e12 --> e13["5"]
        e13 --> e14["h7"]
        e14 --> e15["7"]
        e15 --> e16["p5"]
        e16 --> e17["5"]
        e17 --> e18["h7"]
        e18 --> e19["7"]
        e19 --> e20["p5"]
        e20 --> e21["5"]
        e21 --> e22["h7"]
        e22 --> e23["7"]
        e23 --> e24["p5"]
        e24 --> e25["5"]
        e25 --> e26["h7"]
        e26 --> e27["7"]
        e27 --> e28["p5"]
        e28 --> e29["5"]
        e29 --> e30["h7"]
        e30 --> e31["7"]
        e31 --> e32["p5"]
    end
    
    subgraph B_string ["B string"]
        B1["5"] --> B2["h7"]
        B2 --> B3["7"]
        B3 --> B4["p5"]
        B4 --> B5["5"]
        B5 --> B6["h7"]
        B6 --> B7["7"]
        B7 --> B8["p5"]
        B8 --> B9["5"]
        B9 --> B10["h7"]
        B10 --> B11["7"]
        B11 --> B12["p5"]
        B12 --> B13["5"]
        B13 --> B14["h7"]
        B14 --> B15["7"]
        B15 --> B16["p5"]
        B16 --> B17["5"]
        B17 --> B18["h7"]
        B18 --> B19["7"]
        B19 --> B20["p5"]
        B20 --> B21["5"]
        B21 --> B22["h7"]
        B22 --> B23["7"]
        B23 --> B24["p5"]
        B24 --> B25["5"]
        B25 --> B26["h7"]
        B26 --> B27["7"]
        B27 --> B28["p5"]
        B28 --> B29["5"]
        B29 --> B30["h7"]
        B30 --> B31["7"]
        B31 --> B32["p5"]
    end
    
    subgraph G_string ["G string"]
        G1["5"] --> G2["h7"]
        G2 --> G3["7"]
        G3 --> G4["p5"]
        G4 --> G5["5"]
        G5 --> G6["h7"]
        G6 --> G7["7"]
        G7 --> G8["p5"]
        G8 --> G9["5"]
        G9 --> G10["h7"]
        G10 --> G11["7"]
        G11 --> G12["p5"]
        G12 --> G13["5"]
        G13 --> G14["h7"]
        G14 --> G15["7"]
        G15 --> G16["p5"]
        G16 --> G17["5"]
        G17 --> G18["h7"]
        G18 --> G19["7"]
        G19 --> G20["p5"]
        G20 --> G21["5"]
        G21 --> G22["h7"]
        G22 --> G23["7"]
        G23 --> G24["p5"]
        G24 --> G25["5"]
        G25 --> G26["h7"]
        G26 --> G27["7"]
        G27 --> G28["p5"]
        G28 --> G29["5"]
        G29 --> G30["h7"]
        G30 --> G31["7"]
        G31 --> G32["p5"]
    end
```

Hammer-ons must sound loud enough without a pick stroke. Pull-offs need a slight sideways flick rather than a straight lift — the sideways motion is what plucks the lower note.

---

## Module 3: Right-Hand Mechanics — Picking, Strumming, and Fingerstyle

### Pick Mechanics

**Grip:** Hold the pick between the side of the index finger and the pad of the thumb, tip extending 3–5 mm past your fingers. Too much exposed tip gives uncontrolled flex; too little drags on the string.

**Alternate picking:** Down on the beat, up on the offbeat — the foundational motion. Start at 60 BPM with a metronome. Raise tempo only when every note is equally clean and equally loud.

**Downstroke authority:** Most rhythm playing favors downstrokes because they deliver a stronger, more forceful attack that sits better in a mix. Reserve upstrokes for deliberate articulation, not default habit.

**Pick slant angles:**
- Downward pick slant (DPS): tip angled down, favors downstrokes — common in rock/metal rhythm playing.
- Upward pick slant (UPS): tip angled up, favors upstrokes — common in country and certain lead lines.
- Neutral/flat: used for tremolo picking and strict alternate picking.

**Economy picking:** Sweep in the direction of string travel when crossing strings instead of always alternating. Moving from string 6 toward string 1, stack consecutive downstrokes; moving back, consecutive upstrokes. This shortens pick travel at high speed.

**Alternate picking drill (60 BPM → 120 BPM):**

```mermaid
flowchart TD
    e["String e: 5-6-7-8-8-7-6-5"]
    B["String B: 5-6-7-8-8-7-6-5"]
    
    e -->|"pattern repeats"| B
    B -->|"across all strings"| e
    
    style e fill:#f9f9f9,stroke:#333,stroke-width:2px
    style B fill:#f9f9f9,stroke:#333,stroke-width:2px
```

One note per click. Add 5 BPM only when the current tempo feels effortless.

### Palm Muting

Rest the heel of your picking hand on the strings 10–15 mm in front of the bridge saddles. Too far forward produces a dead thud; too far back (or lifted) leaves the strings ringing unmuted. The sweet spot produces a controlled "chugging" texture.

Palm muting is dynamic, not fixed — roll the wrist forward mid-phrase to deepen the mute progressively, creating a swell. This is a signature rock and metal rhythm technique.

### Fingerstyle Foundation

Without a pick, assign the right-hand fingers:

```
Thumb (p) → strings 6, 5, 4 (bass strings)
Index (i) → string 3
Middle (m) → string 2
Ring (a)   → string 1
```

**Travis picking pattern — foundational (60 BPM), over an open G chord (320033):**

```
  T = thumb, i = index, m = middle, a = ring

  Beat: 1  +  2  +  3  +  4  +
  Str:  6     3     5     3     (thumb alternates 6th and 5th; fingers arpeggiate treble strings)
  R.H.: T     i     T     m
```

The thumb alternates bass strings on beats 1 and 3 while the fingers independently pick treble strings, producing the illusion of two instruments at once — the backbone of folk, country, and acoustic fingerstyle.

---

## Module 4: Open Chords — Your First Vocabulary

### The Five Essential Open Chord Shapes

**E major (022100):**
```
   E A D G B e
   0 2 2 1 0 0

   Finger 1: B string, fret 1
   Finger 2: A string, fret 2
   Finger 3: D string, fret 2
   Strings 1, 3, 6: open
```

**A major (x02220):**
```
   E A D G B e
   x 0 2 2 2 0

   Option 1: fingers 1–2–3 on D–G–B, fret 2 each
   Option 2: barre D–G–B at fret 2 with finger 1 (prepares you for barre chords)
```

**D major (xx0232):**
```
   E A D G B e
   x x 0 2 3 2

   Finger 1: G string, fret 2
   Finger 2: high e string, fret 2
   Finger 3: B string, fret 3
   Mute strings 6 and 5
```

**G major (320003) — two fingerings:**
```
   Version 1 (beginner):
   Finger 1: A string, fret 2
   Finger 2: low E string, fret 3
   Finger 3: B string, fret 3

   Version 2 (preferred):
   Finger 2: A string, fret 2
   Finger 3: low E string, fret 3
   Finger 4: high e string, fret 3
```

Version 2 frees fingers 1 and 2 to drop straight into Cadd9, D, or Em — the key to smooth open-position transitions.

**C major (x32010):**
```
   E A D G B e
   x 3 2 0 1 0

   Finger 1: B string, fret 1
   Finger 2: D string, fret 2
   Finger 3: A string, fret 3
   G and high e strings: open
```

### Minor Chord Shapes

**Em (022000):** finger 2 on A string fret 2, finger 3 on D string fret 2. Everything else open — the most resonant open chord on the instrument.

**Am (x02210):** finger 1 on B string fret 1, finger 2 on D string fret 2, finger 3 on G string fret 2.

**Dm (xx0231):** finger 1 on high e fret 1, finger 2 on G string fret 2, finger 3 on B string fret 3.

### Chord Transition Drill

Pick two chords. Metronome at 60 BPM. Change chord on beat 1 of every other measure (every 8 beats). Increase tempo only when both chords ring clean through the change.

**Priority transitions:**
1. G → D → Em → C (the "axis" progression — appears in hundreds of songs)
2. Am → F → C → G
3. E → A → D (rock/blues power progression)

**Pivot finger technique:** When two chords share a note at the same string/fret, keep that finger planted. Going from C to Am, finger 1 (B string, fret 1) never moves — one less finger to reposition, and a noticeably faster, cleaner change.

---

## Module 5: Barre Chords — Unlocking the Full Neck

### The E-Shape Barre Chord

The open E major shape, barred at any fret with the index finger, becomes a movable major chord with its root on string 6.

**F major barre (133211) — the first barre chord:**
```
   Fret 1, full barre, finger 1 across all 6 strings
   Finger 2: G string, fret 2
   Finger 3: A string, fret 3
   Finger 4: D string, fret 3
```

The barre fails in predictable ways:

| Failure | Cause | Fix |
|---|---|---|
| B string buzzes or mutes | Finger 1 bent at the middle joint, creating a gap | Straighten finger 1; roll it slightly toward the headstock |
| High e string mutes | Index finger not reaching string 1 | Extend farther; confirm thumb sits behind finger 1, not finger 2 |
| All strings buzz | Insufficient pressure | Fret just behind (nut-side of) the fret wire |
| Wrist pain | Excess grip force | You're using far more force than needed; relax consciously |

**E-shape barre root map (string 6):**
```
Fret:  1    2    3    4    5    6    7    8    9   10   11   12
Root:  F    F#   G    G#   A    A#   B    C    C#   D    D#   E
```

Memorize this row. Once you know the note on the low E string at any fret, you know the chord name.

**E minor barre shape:** remove finger 2 from the E major barre. Root locations stay the same; the quality flips to minor.

### The A-Shape Barre Chord

The open A major shape, barred at any fret, becomes a movable major chord with root on string 5.

**B major barre (x24442):**
```
   Barre fret 2 with finger 1 (strings 1–5)
   Finger 2: D string, fret 4
   Finger 3: G string, fret 4
   Finger 4: B string, fret 4

   Alternative "mini-barre": fret 2 with finger 1, then finger 3 barres frets 3–4 across D–G–B
```

**A-shape barre root map (string 5):**
```
Fret:  1    2    3    4    5    6    7    8    9   10   11   12
Root:  A#   B    C    C#   D    D#   E    F    F#   G    G#   A
```

### Combining E-Shape and A-Shape for Any Key

For any major chord you have two barre options: root on string 6 or root on string 5. Use whichever keeps your hand closer to its current position.

**Example — I–IV–V in G:**
```
G major: E-shape barre, fret 3  (root on string 6)
C major: A-shape barre, fret 3  (root on string 5) — hand stays in place
D major: A-shape barre, fret 5  (root on string 5) — shift up two frets
```

One shift for the whole progression, versus three large jumps if you stayed in E-shape throughout (fret 3 → fret 8 → fret 10). Knowing both shapes builds economy of motion into your fretting hand by default.

---

## Module 6: The CAGED System — Fretboard Architecture

### What CAGED Actually Is

CAGED isn't a memorization gimmick — it's a direct consequence of the tuning's interval structure. Because standard tuning is mostly perfect fourths with one major-third exception (G→B), only five distinct open-chord shapes exist. These shapes — C, A, G, E, D — tile the entire fretboard in a repeating cycle with no gaps.

Each shape contains the same three pitch classes (root, major third, perfect fifth) arranged differently across the strings, and the shapes interlock: the top notes of one overlap the bottom notes of the next.

```mermaid
flowchart TB
    subgraph sub_caged_key_c ["CAGED Cycle — Key of C Major"]
        direction TB
        C1["C shape\nFrets 0-3\nRoot: A string, fret 3"]
        A1["A shape\nFrets 3-5\nRoot: A string, fret 5"]
        G1["G shape\nFrets 5-8\nRoot: low E string, fret 8"]
        E1["E shape\nFrets 7-10\nRoot: low E string, fret 8"]
        D1["D shape\nFrets 9-12\nRoot: D string, fret 10"]
        C2["C shape octave\nFrets 12-15\nRoot: A string, fret 15"]

        C1 -->|"+2 frets"| A1
        A1 -->|"+3 frets"| G1
        G1 -->|"+2 frets"| E1
        E1 -->|"+2 frets"| D1
        D1 -->|"+3 frets"| C2
    end
```

The offsets (+2, +3, +2, +2, +3) sum to 12 — one octave. The two larger jumps occur at the G and D shapes because those are the points where the root crosses the G→B string boundary, requiring an extra fret to preserve pitch equivalence.

### The Five Shapes with Scale Degrees Marked

**C shape (key of C, frets 0–3):** R=C, 3=E, 5=G
```mermaid
flowchart LR
    e["e"]
    B["B"]
    G["G"]
    D["D"]
    A["A"]
    E["E"]
    
    node0["0"]
    node1["1"]
    node2["2"]
    node3["3"]
    R["R"]
    
    e --> node0
    e --> node1
    e --> node3
    
    B --> node1
    B --> node3
    
    G --> node2
    
    D --> node2
    D --> node3
    
    A --> node3
    A --> R
```

**A shape (key of C, frets 3–5):** R=C on A string, fret 3
```mermaid
flowchart LR
    subgraph fret3 ["Fret 3"]
        B3["B – 1"]
        G3["G – 1"]
        D3["D – 1"]
    end

    subgraph fret4 ["Fret 4"]
        G4["G – 2"]
        D4["D – 2"]
    end

    subgraph fret5 ["Fret 5"]
        e5["e – 5"]
        B5["B – 5"]
        A5["A – 5 (Root)"]
    end

    B3 --> B5
    G3 --> G4
    D3 --> D4
```

**G shape (key of C, frets 5–8):** R=C on low E, fret 8
```mermaid
flowchart LR
    subgraph strings ["Guitar Strings"]
        eS["e (high)"]
        BS["B"]
        GS["G"]
        DS["D"]
        AS["A"]
        ES["E (low)"]
    end

    subgraph fret5 ["Fret 5"]
        e5["e • 5"]
        B5["B • 5"]
        G5["G • 5"]
        D5["D • 5"]
        A5["A • 5"]
    end

    subgraph fret7 ["Fret 7"]
        e7["e • 7"]
        B7["B • 7"]
        G7["G • 7"]
        D7["D • 7"]
        A7["A • 7"]
        E7["E • 7"]
    end

    subgraph fret8 ["Fret 8"]
        e8["e • 8"]
        B8["B • 8"]
        G8["G • 8"]
        ER["E • 8 (Root)"]
    end

    eS --> e5 --> e7 --> e8
    BS --> B5 --> B7 --> B8
    GS --> G5 --> G7 --> G8
    DS --> D5 --> D7
    AS --> A5 --> A7
    ES --> E7 --> ER
```

**E shape (key of C, frets 7–10):** R=C on low E, fret 8
```mermaid
flowchart TD
    subgraph fret7["Fret 7"]
        e7["e"]
        B7["B"]
        G7["G"]
        D7["D"]
        A7["A"]
    end
    
    subgraph fret8["Fret 8"]
        e8["e"]
        B8["B"]
        E8["E (Root)"]
        A8["A"]
    end
    
    subgraph fret9["Fret 9"]
        G9["G"]
        D9["D"]
    end
    
    subgraph fret10["Fret 10"]
        e10["e"]
        B10["B"]
        D10["D"]
        A10["A"]
        E10["E"]
    end
    
    e7 --> e8 --> e10
    B7 --> B8 --> B10
    G7 --> G9
    D7 --> D9 --> D10
    A7 --> A8 --> A10
    E8 --> E10
```

**D shape (key of C, frets 9–12):** R=C on D string, fret 10 (octave R on B string fret 12)
```mermaid
flowchart TD
    subgraph strings["Guitar Strings"]
        e["e"]
        B["B"]
        G["G"]
        D["D"]
        A["A"]
        E["E"]
    end
    
    subgraph frets["Fret Positions"]
        fret9["Fret 9"]
        fret10["Fret 10"]
        fret12["Fret 12"]
    end
    
    e -->|9| fret9
    e -->|12| fret12
    
    B -->|10| fret10
    B -->|12| fret12
    
    G -->|9| fret9
    G -->|12| fret12
    
    D -->|10| fret10
    D -->|12| fret12
    
    fret12 --> octave["R octave"]
```

### CAGED Practice Protocol

Don't try to absorb all five shapes at once. One shape per week.

**Week 1 — E shape:** Play the E-shape barre at every root from fret 1 to fret 12. For each position also play the arpeggio (root → 3rd → 5th → octave → 5th → 3rd → root) using only notes inside that shape's fret span. Metronome at 60 BPM, one note per two beats; work up to 80 BPM.

**Week 2 — A shape:** Same drill. Connect A shape back to E shape by locating the shared chord tones at the boundary frets.

**Weeks 3–5 — G, C, D shapes:** Add one per week. By week 5, run the full CAGED cycle in one key (e.g. G major) up the neck without stopping.

**Shape-linking drill (after week 5):** Choose a key, play the chord in each CAGED shape consecutively up the neck, transitioning through the shared note at each boundary. This is what turns the neck into one connected surface instead of five isolated boxes.

---

## Module 7: Pentatonic and Blues Scales — Lead Guitar Foundation

### The Minor Pentatonic Scale

Five notes, two notes per string — the most versatile lead guitar tool on the instrument.

Formula: Root – b3 – 4 – 5 – b7

**A minor pentatonic, position 1 (frets 5–8):**
```mermaid
flowchart LR
    fret5["Fret 5"]
    fret8["Fret 8"]
    
    subgraph strings ["Guitar Strings"]
        e["e"]
        B["B"]
        G["G"]
        D["D"]
        A["A"]
        E["E"]
    end
    
    e -->|5| fret5
    e -->|8| fret8
    B -->|5| fret5
    B -->|8| fret8
    G -->|5| fret5
    G -->|7| fret8
    D -->|5| fret5
    D -->|7| fret8
    A -->|5| fret5
    A -->|7| fret8
    E -->|5| fret5
    E -->|8| fret8
```

Finger 1 on all lower-fret notes, finger 4 (or 3) on all higher-fret notes — two fingers per string locks the position in cleanly.

### All Five Pentatonic Positions

The five positions map directly onto the five CAGED shapes — not a coincidence, since the pentatonic scale is the skeleton of the major/minor chord. Know CAGED and you already know where the five pentatonic boxes live.

```mermaid
flowchart TD
    subgraph pos1 ["Position 1 (A shape) — frets 5-8"]
        direction LR
        e1["e: 5────8"]
        B1["B: 5────8"]
        G1["G: 5────7"]
        D1["D: 5────7"]
        A1["A: 5────7"]
        E1["E: 5────8"]
    end
    
    subgraph pos2 ["Position 2 (G shape) — frets 7-10"]
        direction LR
        e2["e: 8────10"]
        B2["B: 8────10"]
        G2["G: 7────9"]
        D2["D: 7────10"]
        A2["A: 7────10"]
        E2["E: 8────10"]
    end
    
    subgraph pos3 ["Position 3 (E shape) — frets 10-12"]
        direction LR
        e3["e: 10────12"]
        B3["B: 10────12"]
        G3["G: 9────12"]
        D3["D: 10────12"]
        A3["A: 10────12"]
        E3["E: 10────12"]
    end
    
    subgraph pos4 ["Position 4 (D shape) — frets 12-15"]
        direction LR
        e4["e: 12────15"]
        B4["B: 13────15"]
        G4["G: 12────14"]
        D4["D: 12────14"]
        A4["A: 12────14"]
        E4["E: 12────15"]
    end
    
    subgraph pos5 ["Position 5 (C shape) — frets 2-5 (or 14-17)"]
        direction LR
        e5["e: 2────5"]
        B5["B: 1────3"]
        G5["G: 2────4"]
        D5["D: 2────5"]
        A5["A: 2────5"]
        E5["E: 2────5"]
    end
    
    pos1 --> pos2
    pos2 --> pos3
    pos3 --> pos4
    pos4 --> pos5
```

### The Blues Scale — Adding the b5

Add the flattened fifth (b5), the "blue note," to the minor pentatonic.

A blues scale: A – C – D – D# – E – G

**Position 1 of A blues scale (frets 5–8):**
```mermaid
flowchart TD
    subgraph fretboard["Guitar Fretboard - Blues Scale with Blue Note"]
        e1["e |──5──────8──|"]
        B1["B |──5──────8──|"]
        G1["G |──5──────7──|"]
        D1["D |──5──6───7──|"]
        A1["A |──5──────7──|"]
        E1["E |──5──────8──|"]
        
        note["fret 6 on D string = D# (blue note)"]
        
        e1 --> B1 --> G1 --> D1 --> A1 --> E1
        D1 -.-> note
    end
```

The blue note is a passing tone, not a destination — bend through it, slide through it, or hit it and resolve immediately up or down.

### String Bending — The Core Lead Guitar Technique

A bend raises pitch by pushing the string toward the ceiling (strings 1–3) or pulling toward the floor (strings 4–6). One whole-step bend equals 2 frets of pitch increase; a half-step bend equals 1 fret. The pitch must land cleanly on target — that's what separates a musical bend from an out-of-tune squawk.

**Executing a whole-step bend:**
1. Finger 3 on the note to bend, fingers 1 and 2 behind it on the same string for leverage.
2. Push perpendicular to the string's length, toward the ceiling (strings 1–3).
3. Drive the push from wrist rotation, not finger strength — the forearm rotates slightly as you push.
4. Target: the note two frets higher than your starting fret.

**Verification drill:** Fret the target note (two frets up) first to hear it, then return and bend up to match. If the bend lands on that pitch, it's in tune; if not, adjust the wrist rotation and try again.

**Classic bend positions (A minor pentatonic, position 1):**
```mermaid
flowchart TD
    subgraph fretboard["Guitar Fretboard - Bend Notation"]
        e1["e |──5──────8──|"]
        B1["B |──5──8b──8──| ← fret 8 bend = whole step, matches fret 10 pitch"]
        G1["G |──5──7b──7──| ← fret 7 bend = whole step, matches fret 9 pitch"]
        D1["D |──5──7───7──|"]
        A1["A |──5──7───7──|"]
        E1["E |──5──────8──|"]
        
        e1 --> B1 --> G1 --> D1 --> A1 --> E1
    end
    
    legend["b = whole-step bend"]
    
    fretboard --> legend
```

### Lead Guitar Practice Structure (Daily 20 Minutes)

```
0:00-5:00    Pentatonic position 1, up and down, alternate picking (60-90 BPM)
5:00-10:00   Bending drill: 5 bends on G string, 5 on B string, each held 2 beats then released. Tune each one.
10:00-15:00  Play along with an A minor backing track, staying inside position 1 only. Focus on phrasing, not speed.
15:00-20:00  Connect positions 1 and 2: phrase in position 1, slide or shift to position 2, resolve there.
```

---

## Module 8: Rhythm Guitar and Chord Voicings

### Power Chords — The Foundation of Rock Rhythm

A power chord contains only two pitch classes: root and perfect fifth. Neither major nor minor, which makes it universally compatible with both.

**E5 power chord:**
```mermaid
flowchart TD
    E["E string: fret 0 (open)"]
    A["A string: fret 2<br/>← finger 1"]
    D["D string: fret 2<br/>← finger 3 (or barre with finger 1's tip)"]
    G["G string: muted ✕<br/>(muted with finger 1's tip)"]
    B["B string: muted ✕"]
    e["e string: muted ✕"]
    
    E
    A
    D
    G
    B
    e
```

**A5 power chord:**
```mermaid
flowchart TD
    E["E string"]
    A["A string"]
    D["D string"]
    G["G string"]
    B["B string"]
    e["e string"]
    
    E ---|"x (muted)"|E
    A ---|"0 (open)"|A
    D ---|"2 (finger 1)"|D
    G ---|"2 (finger 3)"|G
    B ---|"x (muted)"|B
    e ---|"x (muted)"|e
```

The same two-finger root+fifth shape moves freely on strings 6–5 or 5–4. Root name = note on the lower string of the pair.

**Power chord palm-muted rhythm pattern — 120 BPM:**
```mermaid
flowchart LR
    A["E5 String 6<br/>Fret 0"]
    
    subgraph beat ["Beat Pattern: 1 + 2 + 3 + 4 +"]
        B1["Beat 1<br/>↓<br/>PM"]
        B2["+ <br/>↓<br/>PM"]
        B3["2<br/>↓<br/>PM"]
        B4["+ <br/>↑<br/>PM"]
        B5["3<br/>↓<br/>──"]
        B6["+ <br/>↓<br/>PM"]
        B7["4<br/>↓<br/>PM"]
        B8["+ <br/>↑<br/>──"]
    end
    
    A --> B1 --> B2 --> B3 --> B4 --> B5 --> B6 --> B7 --> B8
    
    style B1 fill:#e1f5ff
    style B2 fill:#e1f5ff
    style B3 fill:#e1f5ff
    style B4 fill:#e1f5ff
    style B5 fill:#fff3e0
    style B6 fill:#e1f5ff
    style B7 fill:#e1f5ff
    style B8 fill:#fff3e0
```

### Extended and Suspended Chord Voicings

**Dsus2 (xx0230) and Dsus4 (xx0233):**
```
Dsus2: remove finger 1 from D major → B string rings open (major 2nd)
Dsus4: move finger 2 from e-string fret 2 to e-string fret 3 (adds 4th)
```

Alternating these with D major is a core sound of acoustic and clean electric rhythm playing.

**Gadd9 (320030 or 320033):**
```mermaid
flowchart TD
    e["e string |──3──| (optional, finger 4)"]
    B["B string |──3──| (optional, finger 3)"]
    G["G string |──0──|"]
    D["D string |──0──|"]
    A["A string |──2──| (finger 1)"]
    E["E string |──3──| (finger 2)"]
```

Add9 avoids the suspended 4th — it colors the chord without removing the third, keeping major quality while sounding open and contemporary.

**A7 (x02020):**
```mermaid
flowchart TD
    e["e string: open"]
    B["B string: fret 2 (finger 2)"]
    G["G string: open"]
    D["D string: fret 2 (finger 1)"]
    A["A string: open"]
    E["E string: muted"]
```

The A7 → D7 alternation covers a large share of blues and funk rhythm vocabulary.

### The Rhythm Guitar Approach

Rhythm guitar is about locking with the drums and placing notes with intention, not about the strum pattern itself.

**Strum pattern fundamentals:** The right hand moves in a constant down-up pendulum, one stroke per eighth note at all times — what changes is whether the pick actually contacts the strings. Ghost strums (motion without contact) preserve the groove pocket while accented hits create rhythmic interest.

**Standard rock strum pattern (100 BPM):**
```
Beat: 1  +  2  +  3  +  4  +
Str:  ↓  ↑  ↓     ↓  ↑  ↓  ↑
      ✓  ✓  ✓  ✗  ✓  ✓  ✓  ✓

✓ = contact, ✗ = ghost strum
```

**Funk 16th-note pattern (90 BPM):**
```
Beat: 1  e  +  a  2  e  +  a  3  e  +  a  4  e  +  a
Str:  ↓  ✗  ↑  ✗  ↓  ✗  ↑  ↓  ✗  ✗  ↑  ✗  ↓  ✗  ✗  ↑
PM:   PM          PM    PM                PM
```

Accented hits mark the "one"; syncopated upstrokes create the funk feel. Keep unaccented strokes as damped 16th-note chops by releasing left-hand pressure without lifting off the string.

---

## Module 9: Signal Chain Architecture

```mermaid
flowchart LR
    subgraph sub_guitar_body ["Guitar Body"]
        STR["String Vibration\nFundamental + Harmonics"]
        NUT["Nut and Saddle\nMechanical Coupling"]
        STR --> NUT
    end

    subgraph sub_electronics ["Guitar Electronics"]
        PU["Pickup\nMagnetic to Electrical"]
        VOL["Volume Pot\nOutput Level"]
        TONE["Tone Pot\nRC Low-Pass Filter"]
        PU --> VOL --> TONE
    end

    subgraph sub_effects ["Effects Chain"]
        COMP["Compressor\nDynamic Leveling"]
        OD["Overdrive / Distortion\nHarmonic Saturation"]
        MOD["Modulation\nChorus / Phaser / Flanger"]
        DLY["Delay / Reverb\nTime-Based Effects"]
        COMP --> OD --> MOD --> DLY
    end

    subgraph sub_amplifier ["Amplifier"]
        PRE["Preamp\nGain / EQ"]
        PWR["Power Amp\nOutput Stage"]
        SPK["Speaker Cabinet\nMechanical Resonance"]
        PRE --> PWR --> SPK
    end

    NUT --> PU
    TONE --> COMP
    SPK --> AIR["Acoustic Output\nAir Pressure Waves"]
```

### Pickup Physics in One Paragraph

A pickup is a coil of wire wrapped around magnets. A vibrating steel string disturbs the magnetic field and induces a voltage proportional to the *rate of change* of flux, not the flux itself — the pickup behaves as a velocity sensor, so fast-changing waveforms (high harmonics) produce proportionally more output than slow-changing ones (the fundamental). Single-coil pickups (Strat, Tele) give bright, articulate tone with audible 60 Hz hum from AC power lines. Humbuckers (Les Paul, SG) wire two opposing coils in series, canceling the hum while summing the string signal, which yields higher output, more midrange, and a warmer character because the added coil inductance rolls off extreme highs.

### Tone Control Mechanics

The tone control is a first-order RC low-pass filter: a capacitor in series with a potentiometer to ground. Turning the knob down raises the resistance in circuit, lowering the cutoff frequency and progressively removing high partials. Stratocasters typically use 0.047 µF capacitors; Les Pauls use 0.022 µF — the smaller cap leaves more treble in the circuit at any knob position, part of why a Les Paul keeps a mid-focused character even with the tone rolled back.

**Practical use:** Rolling a Stratocaster's neck-pickup tone from 10 to 7 is a faster route to a warm jazz tone than EQ tweaking at the amp. Rolling to 3–4 produces a cocked-wah timbre that cuts through a dense mix differently than a full-treble signal.

### Effects Chain Ordering and Why It Matters

```
Guitar → Tuner → Compressor → Overdrive/Distortion →
EQ → Modulation (Chorus/Phaser) → Delay → Reverb → Amp
```

- **Tuner first** sees the cleanest signal for accurate pitch detection.
- **Compressor before dirt** evens out pick dynamics before they hit the overdrive, giving more consistent saturation.
- **Overdrive before modulation** means the overdrive shapes the dry signal first; modulation then moves that already-distorted signal in pitch/time, widening the effect.
- **Delay before reverb** mimics how sound naturally propagates in a room — delay repeats feed into the reverb tail. Reversed, the reverb tail itself gets delayed, producing a washed-out sludge.

**Dirt before amp vs. in the effects loop:** An amp's effects loop sits between preamp and power amp. Effects placed there hear an already-driven preamp signal. Putting time-based effects (delay, reverb) in the loop instead of in front of the amp keeps their repeats and tails clean, uncolored by preamp distortion — correct practice for high-gain setups. For clean or low-gain amps it makes little audible difference.

---

## Module 10: Voice Leading and Harmonic Movement

### Roman Numeral Analysis — The Key-Agnostic Framework

Chords in a progression are named by scale degree within the key, not by letter name — this lets you transpose any progression to any key instantly.

In G major:
```
I   = G major
ii  = A minor
iii = B minor
IV  = C major
V   = D major
vi  = E minor
vii°= F# diminished
```

Uppercase = major, lowercase = minor, ° = diminished.

**Progressions worth internalizing:**
- **I–IV–V (major key):** G–C–D. The 12-bar blues is built on this.
- **I–V–vi–IV:** G–D–Em–C. Appears across an enormous range of popular songs.
- **ii–V–I (jazz):** Am–D–G. The fundamental jazz cadence.
- **i–VII–VI–VII (rock/modal):** Em–D–C–D. A Dorian/Aeolian rocking vamp.

### Secondary Dominants

The V chord pulls toward I because of the tritone tension between its third and seventh. You can borrow that pull for any chord in the key by temporarily treating it as a local I and playing the V7 of that chord.

**V/V in G major:** V is D; V of D is A7. Playing A7 → D inside a G major context tonicizes D momentarily without leaving the key.

**Common secondary dominants in G major:**
```
V/ii  → E7  → Am
V/iii → F#7 → Bm
V/IV  → G7  → C
V/V   → A7  → D
V/vi  → B7  → Em
```

Each one creates a brief intensification before resolving to its target — the tool that makes simple progressions sound sophisticated.

### Connecting Chords on the Fretboard with Minimal Movement

Smooth voice leading moves each chord tone to the nearest available chord tone in the next chord. Jumping position for every change is a beginner habit; advanced players keep the hand as stationary as possible.

**Example: I–V–vi–IV in C major using open/CAGED voicings:**
```
Cmaj7  (x32000):  static — no barre needed
G/B    (x20033):  bass note moves C → B (A string, fret 3 → fret 2)
Am7    (x02010):  finger 2 stays on D string fret 2; finger 1 moves to B string fret 1
Fmaj7  (x33210):  barre fret 1 — the largest move in the progression
```

Three of four changes involve minimal finger movement, producing a connected, pianistic quality rather than four unrelated barre grabs.

**Rootless voicings for clean electric and jazz:**
In a band, the bass covers the root. This frees the guitarist to voice from the third upward for less muddy, more harmonically interesting textures.

```
Cmaj7 rootless: strings 4-1 at frets 3-5-4-3 (no root C)
Dm7 rootless:   strings 4-1 at frets 5-6-5-5
G7 rootless:    strings 4-1 at frets 4-3-3-3 (or 4-5-3-4 for the tritone-sub voicing)
```

---

## Module 11: Advanced Techniques

### Vibrato — The Human Element

Vibrato is pitch oscillation that sustains and colors a note expressively — identical notes with different vibrato styles sound like different players.

- **Wrist vibrato (classical, jazz):** the wrist rocks while the finger stays in contact; pitch oscillates subtly above and below target.
- **Arm vibrato (blues, rock):** the forearm rotates, using the finger as a lever; wider and more expressive.
- **Below-pitch vibrato (blues style):** start on the note, dip below, return — the ear hears it as resolving upward, creating emotional pull.

**Vibrato drill (60 BPM):** Hold a note (finger 3, B string fret 10). Begin a vibrato cycle on each beat. Week 1: one cycle per two beats, slow and wide. Week 2: two cycles per beat, faster and controlled. Keep oscillation width consistent across cycles.

### Hammer-ons, Pull-offs, and Legato Lines

Legato phrasing plays fast lines with minimal picking effort, at the cost of each slurred note being slightly quieter unless you apply deliberate extra force.

**Legato scale run (A minor pentatonic, position 1):**
```mermaid
flowchart TD
    subgraph strings["Guitar Strings (Top to Bottom)"]
        e["e |──5h8────────────────|"]
        B["B |──5h8────────────────|"]
        G["G |──5h7────────────────|"]
        D["D |──5h7────────────────|"]
        A["A |──5h7────────────────|"]
        E["E |──5h8────────────────|"]
    end
    
    subgraph technique["Technique"]
        asc["Ascending: pick first note per string,<br/>hammer the second"]
        desc["Descending: pick top note,<br/>pull off to the lower"]
    end
    
    subgraph tempo["Speed Target"]
        bpm1["80 BPM (16th notes)"]
        bpm2["110 BPM"]
        bpm3["140 BPM"]
        bpm1 --> bpm2 --> bpm3
    end
    
    strings --> technique
    technique --> tempo
```

**Trill exercise (independence and strength):**
```mermaid
flowchart LR
    B["B"]
    trill["5h7p5h7p5<br/>(continuous trill, 1 minute per finger pair, fingers 1 and 3)"]
    B --- trill --- B
```

### Sliding — Smooth Position Shifts

A slide keeps the finger in contact with the string while shifting position, retaining the attack of the first note and arriving at the second through a smooth glide.

- **Legato slide:** pick the first note only; the second sounds from momentum.
- **Shift slide:** re-pick after the slide completes, to re-attack the second note.
- **Approach slide (grace slide):** no defined starting pitch — start below the target and slide up quickly for a scooping, vocal quality.

**Connecting pentatonic positions 1 and 2 via slide (G string):**
```mermaid
flowchart LR
    F5["Fret 5"]
    F7["Fret 7\n(Finger 3 — start)"]
    F9["Fret 9\n(Slide destination\nPosition 2)"]

    F5 --> F7
    F7 -->|"slide →"| F9
```

### Natural and Artificial Harmonics

**Natural harmonics:** touch the string directly above a fret wire (don't press down) and pluck, producing a bell-like tone at that harmonic.

```
Fret 12 → octave above open string (2nd harmonic)
Fret 7  → octave + perfect 5th above open string (3rd harmonic)
Fret 5  → two octaves above open string (4th harmonic)
Fret 9  → two octaves + major 3rd (5th harmonic, slightly sharp of equal temperament)
```

**Practical use:** The fret-12 harmonic lets you check intonation by ear without a tuner — compare it to the fretted 12th-fret note. Sharp fretted note means the saddle needs to move away from the nut to lengthen the string.

**Pinch harmonics:** let the thumb edge of the picking hand brush the string immediately after the pick strikes. This produces a harmonic squeal whose pitch depends on where that contact lands relative to the bridge — closer to the bridge, higher harmonic. Requires overdrive or amp gain to sustain; on a clean signal, the level is too low to hear.

---

## Module 12: Fretboard Navigation Failure Modes and Diagnosis

| Problem | Root Cause | Diagnosis | Fix |
|---|---|---|---|
| Notes sound as thuds | Finger pad touching adjacent string; insufficient arch | Clean alone, muted in a chord | Arch the finger higher; fret with the very tip |
| Fret buzz | Finger too far from fret wire; action too low | Buzz disappears under more pressure | Move finger to just behind (nut-side of) the fret wire |
| Positional locking | Shape memorized without interval awareness | Can't find a note outside the learned box | Drill scale degrees by number; name notes as you play |
| G→B shift errors | Asymmetry not internalized as reflex | Patterns working on strings 6–4 fail on strings 3–1 | Explicitly drill every interval across the G–B boundary |
| Barre chord string gaps | Index finger bent at the middle joint | Specific strings buzz while others ring clean | Roll index finger toward the headstock; use its bony outer edge |
| Bends land out of tune | Weak target-pitch awareness; wrist not rotating | Bend arrives at a vague pitch | Pre-hear the target by fretting it first, then match by bending |
| Fatigue and forearm pain | Excess grip force; collapsed wrist | Pain after 10–15 minutes of practice | Minimum-force fretting; take breaks; keep wrist forward of the neck |
| Intonation drift up the neck | Saddle position wrong; relief incorrect | Harmonic at fret 12 ≠ fretted note at fret 12 | Intonate each saddle; check truss rod relief |

### The Minimum Force Test

Fret any note with far less force than you normally would — barely enough to touch the string — then increase pressure gradually until the note sounds clean with no buzz. That threshold is the actual required force. Most beginners apply 5–10× more than needed. Repeating this test consciously over several weeks rewires muscle memory toward efficiency and prevents the tendon overuse that causes playing-related injuries.

### Intonation Setup Procedure

1. Tune to pitch with an accurate chromatic tuner.
2. Play the 12th-fret harmonic on string 6; note the pitch.
3. Fret the 12th fret firmly on string 6; note the pitch.
4. If the fretted note is **sharp** of the harmonic, the string is too short — move the saddle away from the nut.
5. If **flat**, the string is too long — move the saddle toward the nut.
6. Re-tune the open string after each saddle adjustment (moving the saddle shifts tension).
7. Repeat for all six strings.

This guarantees the fretted octave matches the harmonic octave within tuner accuracy. It won't guarantee perfect intonation at every single fret — that depends on string mass uniformity and setup quality — but it gets the instrument as in-tune as its design allows.

---

## Module 13: Structured Practice Architecture

### Daily Practice Template (45 Minutes)

```
0:00-5:00    Physical warm-up
             Spider crawl, frets 5-8, all strings, 60 BPM
             Chromatic runs, alternate picking, 60-70 BPM

5:00-10:00   Note geography
             Name every note on one string (rotate daily)
             No shape patterns — compute from the nearest open-string landmark

10:00-20:00  Technique focus (rotate weekly)
             Week 1: Barre chord transitions (E-shape, all 12 roots)
             Week 2: Pentatonic position 1 lead (bends, vibrato)
             Week 3: CAGED shape arpeggio (E shape to A shape connection)
             Week 4: Legato runs (hammer-on/pull-off lines)

20:00-30:00  Chord progression and rhythm
             This week's target progression with metronome or drum loop
             Strum pattern + clean changes + palm muting variations

30:00-40:00  Applied musicianship
             Improvise over a backing track using only the target scale/position
             Restriction: fewer notes, more rhythm and phrasing

40:00-45:00  Free playing / ear training
             No rules, no metronome
             Try to reproduce a melody heard today, by ear
```

### Four-Phase Mastery Progression

```mermaid
flowchart LR
    subgraph sub_p1 ["Phase 1 - Foundation (Months 1-3)"]
        P1A["Open chords\nE A D G C Em Am"]
        P1B["Basic strumming\ndown-up, palm muting"]
        P1C["Note names\nall 6 strings, frets 0-12"]
        P1A --> P1B --> P1C
    end

    subgraph sub_p2 ["Phase 2 - Navigation (Months 3-8)"]
        P2A["Barre chords\nE and A shapes, 12 keys"]
        P2B["Pentatonic scale\n5 positions"]
        P2C["CAGED system\nchord shapes + arpeggios"]
        P2A --> P2B --> P2C
    end

    subgraph sub_p3 ["Phase 3 - Expression (Months 6-18)"]
        P3A["Lead techniques\nbends, vibrato, slides"]
        P3B["Diatonic scales\nmajor, natural minor"]
        P3C["Voice leading\nconnecting CAGED shapes"]
        P3A --> P3B --> P3C
    end

    subgraph sub_p4 ["Phase 4 - Musicianship (Ongoing)"]
        P4A["Harmonic analysis\nRoman numerals, secondary dominants"]
        P4B["Ear training\nmelodies, chord ID"]
        P4C["Repertoire\nfull songs + improvisation"]
        P4A --> P4B --> P4C
    end

    sub_p1 --> sub_p2 --> sub_p3 --> sub_p4
    sub_p4 -->|"Return with new ears"| sub_p3
```

### The Backing Track Protocol

A metronome tells you if you're on the beat; a drummer tells you if you're grooving. Different skills. Once a technique is clean at metronome tempo, move it onto a backing track.

**Sources:** YouTube ("A minor blues backing track"), JamTracks, iReal Pro, or a self-built loop in GarageBand/REAPER.

**Constraint-based improvisation rule:** When improvising over a new progression for the first time, limit yourself to three notes from the fitting pentatonic scale. Removing note-choice cognitive load forces attention onto rhythm, timing, vibrato, and phrasing — the elements that actually make music sound musical.

---

## Module 14: Physics of the Fretboard — What You Need to Know (And Nothing More)

Equal temperament divides the octave into 12 equal semitones, each a frequency ratio of 2^(1/12) ≈ 1.05946. Every fret raises pitch by this ratio, and twelve of them multiply to exactly 2 — the octave — which is why fret 12 is the geometric midpoint of the string and every pattern repeats there. Frets get physically closer together up the neck because equal frequency ratios correspond to logarithmically shrinking physical distances. Practical takeaway: pressing harder doesn't change pitch (beyond a negligible sharpening from excess force), and every fingering pattern repeats identically 12 frets higher.

Standard tuning (E–A–D–G–B–E) is mostly perfect fourths (5 semitones) with one major third (4 semitones) between G and B. That asymmetry keeps open major chord shapes practical without large stretches, while keeping the treble strings close enough for single-note melodic playing. The consequence is the one-fret G→B adjustment you'll apply constantly — every interval, pattern, and chord shape shifts by one fret crossing that boundary.

A plucked string vibrates at its fundamental and simultaneously at all integer multiples of it. Where you pick determines which harmonics stand out: near the bridge emphasizes brightness (upper partials); near the 12th fret produces a hollow, woody tone (even partials cancel). Open chords ring with extra sympathetic vibration because open strings share harmonic relationships with the fretted notes — barre the same chord shape up the neck and that sympathetic ring disappears even though the pitch relationships are identical. Not a flaw, a resource for deliberate tone choices.

---

## Quick-Reference Cards

### Fret-to-Note Reference (Low E string, the navigation spine)

```
Fret:   0    1    2    3    4    5    6    7    8    9   10   11   12
Note:   E    F    F#   G    G#   A    A#   B    C    C#   D    D#   E
```

Know this row cold and you always have the root of any E-shape barre chord and any E-string scale pattern.

### Cross-String Interval Summary

| Crossing | Interval at same fret | Semitones | Unison offset |
|---|---|---|---|
| String 6 → 5 | Perfect 4th | +5 | +5 frets |
| String 5 → 4 | Perfect 4th | +5 | +5 frets |
| String 4 → 3 | Perfect 4th | +5 | +5 frets |
| **String 3 → 2** | **Major 3rd** | **+4** | **+4 frets** |
| String 2 → 1 | Perfect 4th | +5 | +5 frets |

The bolded row is the G→B exception — every scale shape, chord voicing, and position shift must account for it.

### Five Invariants — The Axioms of the Instrument

1. **Semitone per fret.** Each fret raises pitch by 2^(1/12). Fret 12 = one octave up; all patterns repeat there.
2. **Standard tuning.** Mostly perfect fourths with one major third exception (G→B). Know it reflexively.
3. **Cross-string unison.** Same pitch on the adjacent thicker string sits +5 frets away (+4 across G→B). These two numbers are the entire architecture of the neck.
4. **CAGED tiling.** Five shapes cover the neck with no gaps. Root offsets: +2, +3, +2, +2, +3 (sum = 12), asymmetric because of the G→B exception.
5. **Pickup as velocity sensor.** It captures rate of change of magnetic flux, not displacement. Pluck position, pickup selection, and tone control shape timbre; none of them change fretted pitch.
