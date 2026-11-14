# Lesson 2: Chord Architecture, Voice Leading, and the CAGED Harmony System

---

## Preface to This Lesson

Harmony on the guitar is a spatial problem before it is a theoretical one. A pianist sees all twelve pitch classes laid out in a single, unambiguous row; every octave looks identical. A guitarist sees six strings tuned in a non-uniform series of perfect fourths with one major third embedded between the G and B strings, spread across twenty-two or more frets, with every pitch available in multiple locations simultaneously. That topography is both the instrument's greatest expressive advantage and its most persistent source of confusion.

This lesson treats the fretboard as architecture. You will learn to construct triads in every inversion across every adjacent string set, understand the CAGED system not as a scale memorization trick but as a continuous harmonic map of the entire neck, build four-part jazz voicings through the drop-2 and drop-3 procedures, and develop the rhythmic and dynamic vocabulary of professional comping. By the end, you will navigate the neck without looking down, place any chord quality in any register, and voice-lead through diatonic progressions with the fluency of a practitioner who understands why each note sits where it does.

---

## 1. Triadic Invariants and String Set Architecture

### 1.1 The Triad as a Fretboard Object

A triad contains three distinct pitch classes: the root, the third, and the fifth. In close position these three voices are arranged within a single octave. On the guitar, distributing a close-position triad across three adjacent strings produces what players call a *string set triad*, and because the guitar has four natural string sets of three adjacent strings (E-A-D, A-D-G, D-G-B, and G-B-E), each triad quality exists in three inversions on each of four string sets — twelve shapes per triad quality before you account for octave displacement.

Understanding these shapes as a family rather than as isolated chord fragments is the first cognitive shift this lesson demands. When you internalize that the same C major triad appears as a compact cluster at fret 5 on the G-B-E strings, as a wider shape on D-G-B, and again on A-D-G, you stop thinking in isolated chord shapes and start thinking in continuous harmonic objects that you can move through register at will.

### 1.2 Interval Structures of the Four Triad Qualities

Before mapping shapes to the fretboard, fix the interval content of each quality clearly in mind. All interval measurements below are in semitones.

| Quality | Root to Third | Third to Fifth | Root to Fifth |
|---|---|---|---|
| Major | 4 (M3) | 3 (m3) | 7 (P5) |
| Minor | 3 (m3) | 4 (M3) | 7 (P5) |
| Diminished | 3 (m3) | 3 (m3) | 6 (d5) |
| Augmented | 4 (M3) | 4 (M3) | 8 (A5) |

The tuning asymmetry of the guitar — four fourths of five semitones each, then one major third of four semitones between G and B, then another fourth — means that the fret-number shape for the same interval changes depending on whether the interval crosses the G-B string boundary. A major third (4 semitones) spanning two strings is typically a 5-fret stretch on E-A, A-D, D-G, or B-E, but only a 4-fret stretch when the lower string is G and the upper string is B. Every shape in the following sections accounts for this asymmetry precisely.

### 1.3 Major Triads: Three Inversions Across Four String Sets

The three inversions of a triad distribute the three voices (1, 3, 5) across the three strings with a different pitch class on the lowest string of the set.

- **Root position**: Root on the lowest string, third and fifth above.
- **First inversion**: Third on the lowest string, fifth and root above.
- **Second inversion**: Fifth on the lowest string, root and third above.

All diagrams below use the notation *low-string : middle-string : high-string* expressed as fret numbers. An **R** marks the root.

---

**C Major — String Set E-A-D (strings 6-5-4)**

```
Root Position (C/C): 1st inv (E/C): 2nd inv (G/C):
C = root            E = bass        G = bass

e |---|              e |---|          e |---|
B |---|              B |---|          B |---|
G |---|              G |---|          G |---|
D |-5-| R            D |-5-| (3rd)   D |-5-| (5th→root?)
A |-3-| (5th)        A |-3-| (root)  A |-2-| (3rd)
E |-8-| (root C)     E |-7-| (3rd E) E |-3-| (5th G)

Fret notation: 8-3-5     7-3-5     3-2-5
```

> *Practical note*: String set E-A-D produces voicings with considerable physical stretch. These shapes appear most often in ensemble contexts where you want bass-register chord stabs or when playing solo arrangements that need a low harmonic anchor.

---

**C Major — String Set A-D-G (strings 5-4-3)**

```
Root Position (C):  1st Inv (E):    2nd Inv (G):
Fret:               Fret:           Fret:

G |-5-|             G |-5-|         G |-4-|
D |-5-| (5th)       D |-2-| (root)  D |-5-|
A |-3-| (root R)    A |-2-| (3rd)   A |-5-| (5th)

Notation: 3-5-5     2-2-5     5-5-4
```

---

**C Major — String Set D-G-B (strings 4-3-2)**

The G-B boundary (major third instead of perfect fourth) shifts the shapes on this string set.

```
Root Position (C):  1st Inv (E):    2nd Inv (G):

B |-5-|             B |-5-|         B |-3-|
G |-5-| (5th)       G |-2-| (root)  G |-5-|
D |-5-| (root R)    D |-2-| (3rd)   D |-5-| (5th)

Notation: 5-5-5     2-2-5     5-5-3
```

> *Key observation*: The root-position C major on D-G-B is a compact, fret-5 triangle. This shape appears constantly in chord melody arrangements and jazz comping because it sits in the mid-register and leaves the low strings free for a bass note or thumbed root.

---

**C Major — String Set G-B-E (strings 3-2-1)**

This string set, sitting entirely within the standard guitar chord range, produces the brightest, most penetrating voicings.

```
Root Position (C):  1st Inv (E):    2nd Inv (G):

e |-8-|             e |-8-|         e |-3-|
B |-5-| (5th)       B |-5-| (root)  B |-5-| (root)
G |-5-| (root R)    G |-4-| (3rd)   G |-0-| (5th)

Notation: 5-5-8     4-5-8     0-5-3
```

---

### 1.4 Minor Triads Across String Sets

Using C minor (C – E♭ – G) as the reference, the same inversion logic applies, with the third lowered by one semitone throughout.

**C Minor — String Set G-B-E**

```
Root Position (Cm): 1st Inv (Eb):   2nd Inv (G):

e |-8-|             e |-8-|         e |-3-|
B |-4-| (5th)       B |-4-| (root)  B |-4-|
G |-5-| (root R)    G |-3-| (b3)    G |-0-| (5th)

Notation: 5-4-8     3-4-8     0-4-3
```

The only change from the major shapes is a one-fret drop of the third throughout. Train your eye and hand to identify this single-semitone shift; it means that every major triad shape you memorize implies its minor version one fret lower on the string carrying the third.

---

### 1.5 Diminished and Augmented Triads

**C Diminished — G-B-E**

```
Root Position (Cdim): 1st Inv (Eb): 2nd Inv (Gb):

e |-7-|              e |-7-|        e |-2-|
B |-4-| (d5)         B |-4-| (root) B |-4-|
G |-5-| (root R)     G |-3-| (b3)   G |-11-|

Notation: 5-4-7      3-4-7     11-4-2
```

**C Augmented — G-B-E**

```
Root Position (Caug): 1st Inv (E):  2nd Inv (G#):

e |-9-|              e |-9-|        e |-4-|
B |-5-| (A5)         B |-5-| (root) B |-5-|
G |-5-| (root R)     G |-4-| (M3)   G |-1-|

Notation: 5-5-9      4-5-9     1-5-4
```

> *Augmented triads have a symmetrical interval structure* — three major thirds stacked — which means every inversion of a C augmented triad produces the same fret shape, only rooted on a different string. C augmented, E augmented, and G# augmented are enharmonically the same set of pitch classes. This symmetry becomes a powerful modulation device.

---

### 1.6 Practicing Triadic Inversions as a Continuous Movement

The goal of this section is not to memorize twelve shapes per quality in isolation, but to move through all three inversions of a given quality on a single string set without stopping. Practice the following routine daily for the first two weeks of this lesson:

1. Choose one string set (start with G-B-E).
2. Choose one triad quality (start with major).
3. Play root position → first inversion → second inversion in ascending order up the neck without lifting your hand from the strings between shapes.
4. Reverse direction.
5. Move to the next string set (D-G-B) and repeat, maintaining the same root pitch class (C) so you hear the voice leading across the register shift.

This drill is the foundation for everything that follows. When you can execute it cleanly on all four string sets for all four qualities without looking at the fretboard, you have internalized the architecture of the instrument at the triadic level.

---

## 2. The CAGED System as a Unified Fretboard Map

### 2.1 What CAGED Actually Is

The CAGED system is named after five open-chord shapes — C, A, G, E, and D — that every beginning guitarist learns in the first year of study. What most intermediate players do not realize is that these five shapes are not five separate chords. They are five windows into the same continuous fretboard topology, and they tile the neck without gaps or overlaps from the nut to the body.

The system's insight is straightforward: if you barre the entire nut with an imaginary capo at any fret, the open-string chord shapes remain geometrically valid. An E-shape barre chord at fret 3 is a G major chord in the E window. That same G major chord exists in four other windows simultaneously — the A window at fret 10, the G window at fret 7 (open), the D window at fret 5, and the C window at fret 3 when oriented differently. These five positions describe the same G major triad across the full compass of the neck.

The practical value is navigation without hesitation. When you know which CAGED window you are in at any moment, you know exactly where the root is, where the other chord tones are, which inversion is on the bottom, and where the adjacent window begins. You can move through a chord progression by shifting windows rather than by hunting for the next shape.

### 2.2 The Five Shapes, Their Root Locations, and Full Chord Voicings

Each shape below is shown as a full six-string chord diagram for the key of C major. Fret numbers are absolute; open strings are marked 0; muted strings are marked x. The root location within each shape is explicitly marked.

---

**C Shape — C Major (open position)**

```
e |--0--|
B |--1--|  ← 3rd (E)
G |--0--|  ← 5th (G)  
D |--2--|  ← Root (C) ← ROOT on string 4
A |--3--|  ← 5th below
E |--x--|

Fret notation: x-3-2-0-1-0
Root: string 4 (D string), fret 2 — also string 2 (B string), fret 1
```

The C shape is asymmetrical and physically demanding to barre cleanly, which is why many players avoid it. Do not avoid it. Closed C-shape voicings appear regularly between frets 3 and 7 and provide the richest mid-neck option for major chords with the root on the second string.

---

**A Shape — C Major (barred at fret 3)**

```
e |--3--|  ← Root (C)
B |--5--|  ← 5th (G)
G |--5--|  ← 3rd (E)
D |--5--|  ← Root (C) ← ROOT on string 4
A |--3--|  ← Root (C) ← ROOT on string 5
E |--x--|

Fret notation: x-3-5-5-5-3
Root: string 5 (A string), fret 3; and string 1 (e string), fret 3
```

The A shape produces a dense, mid-range voicing with the root on the A string. It is the most commonly used barre chord position for rhythm guitar and comping. The triple-string barre across D-G-B at fret 5 gives it a particularly bright, full tone.

---

**G Shape — C Major (barred at fret 7 — partial capo concept)**

```
e |--7--|  ← 5th (G)... wait — recalibrate:
```

For C major in the G shape, the geometric position sits at fret 7 with the root on strings 1 and 6:

```
e |--8--|  ← Root (C)
B |--8--|  ← 5th (G)... 
```

Let us build this carefully. The open G chord has the shape: 3-2-0-0-0-3. Transposing this shape to produce C major requires moving every note up by 5 semitones (C is 5 semitones above G):

```
Open G:   3-2-0-0-0-3
C (G shape, +5 frets): 8-7-5-5-5-8

e |--8--|  ← Root (C)
B |--8--|  ← 5th (G)
G |--5--|  ← 3rd (E)
D |--5--|  ← Root (C)
A |--7--|  ← 5th (G)
E |--8--|  ← Root (C) ← ROOT on strings 6, 4, and 1

Fret notation: 8-7-5-5-8-8
```

The G shape requires a full barre plus two additional fretting fingers, making it physically the most demanding of the five. Its advantage is that it places the root on three strings simultaneously and spans the widest fretboard register, giving the fullest low-to-high voicing available.

---

**E Shape — C Major (barred at fret 8)**

The open E chord: 0-2-2-1-0-0. Transposing to C (+8 semitones):

```
e |--8--|  ← Root (C) ← ROOT
B |--8--|  ← 5th (G)
G |--9--|  ← 3rd (E)
D |--10-|  ← Root (C)
A |--10-|  ← 5th (G)
E |--8--|  ← Root (C)

Fret notation: 8-10-10-9-8-8
Root: strings 6 and 1 (E strings), fret 8
```

The E shape barre chord is the most universally played of the five, drilled into every rock and pop guitarist from the first week. Its root sits unambiguously on the low E string, making it the most harmonically transparent shape for bassists and rhythm section players to hear.

---

**D Shape — C Major (high position)**

The open D chord: x-x-0-2-3-2. Transposing to C (+10 semitones):

```
e |--10-|  ← 3rd (E)
B |--10-|  ← Root (C) ← ROOT on string 2
G |--9--|  ← 5th (G)
D |--10-|  ← Root (C)
A |--x--|
E |--x--|

Fret notation: x-x-10-9-10-10
Root: string 2 (B string), fret 10; and string 4 (D string), fret 10
```

The D shape sits highest on the neck and uses only the top four strings, making it ideal for chord melody playing, upper-register comping behind a vocalist, and adding harmonic color without competing with a bassist.

---

### 2.3 How the Five Shapes Interlock

Place the five shapes in sequence along the neck for C major:

```
Fret:  0    2    4    5    7    8    10   12
       |    |    |    |    |    |    |    |
       C    C    A    A    G    E    E    D    (back to C, oct up)
      shape      shape    shape shape    shape
```

More precisely, the shape transitions occur as follows:

| Shape | Root on Low E (string 6) | Approximate Fret Range for C |
|---|---|---|
| E shape | fret 8 | frets 7–9 |
| D shape | n/a (roots on str. 2 and 4) | frets 9–12 |
| C shape | n/a (root on str. 4 and str. 2) | frets 10–12 / open |
| A shape | fret 3 on A string | frets 3–5 |
| G shape | fret 8 on E string | frets 7–10 |

The key insight is continuity: the highest frets of one shape overlap with or directly abut the lowest frets of the next. When you play the A shape for C major at frets 3–5 and need to move up the neck, the next shape is the G shape beginning around fret 7. When you reach the G shape, the E shape awaits at fret 8, and so on around the cycle.

### 2.4 Root Anchors as Navigation Points

Each CAGED shape has a characteristic root location that you must internalize as a visual and tactile anchor:

- **C shape**: root on string 4 (D string) and string 2 (B string).
- **A shape**: root on string 5 (A string) and string 1 (e string).
- **G shape**: root on strings 6, 4, and 1.
- **E shape**: root on strings 6 and 1.
- **D shape**: root on string 4 and string 2.

Notice that C and D share the same root-string pattern, as do G and E. The A shape is unique in keeping the root on the A string. These patterns reduce the memorization load: once you can find a note on strings 5 and 6 (the low E and A strings), you can anchor any E-shape or A-shape chord anywhere on the neck without counting frets. Practice this by calling out root notes — "play G major in every CAGED position, naming the root location before each voicing" — until the shapes and their root anchors respond without conscious recall.

### 2.5 Transitioning Without Looking

The professional test of CAGED fluency is the ability to shift between shapes mid-phrase, in time, without glancing down. The following protocol builds that skill:

**Step 1**: Play a I–IV–V–I progression in C major (C, F, G, C) entirely within the E-shape window (around fret 8 for C, fret 1 for F and G if transposed, or use the full barre positions). Do not leave the window.

**Step 2**: Play the same progression using only the A-shape window (around fret 3 for C, fret 8 for F, fret 10 for G).

**Step 3**: Connect two adjacent windows across the progression — begin the C chord in the A shape, move to the G shape for F, and return to E shape for G.

**Step 4**: Play the full twelve-bar blues in one key, changing CAGED shapes on each chord change, ascending through the shapes from low to high over the form, then descending on the repeat.

A player who can execute Step 4 fluently has achieved functional CAGED mastery. The neck is no longer a collection of positions; it is a continuous surface.

---

## 3. Four-Part Harmony: Drop-2 and Drop-3 Voicings

### 3.1 The Logic of Voice Dropping

Close-position four-part harmony arranges four voices — from bottom to top: root (1), third (3), fifth (5), and seventh (7) for a seventh chord — within the smallest possible intervallic space. On a keyboard this is immediately playable within one hand. On the guitar, close-position seventh chords often require finger stretches that are impossible or produce poor tone because the voicing is too compressed in pitch space for the instrument's register.

Voice dropping is a procedure for opening up close-position chords into guitar-friendly, resonant voicings while preserving the full harmonic content. The two primary procedures are:

**Drop-2**: Take the second voice from the top of a close-position chord and drop it one octave. If the close-position Cmaj7 in root position arranges voices as C–E–G–B (bottom to top), the second voice from the top is G. Dropping G one octave produces the drop-2 voicing: G–C–E–B (bottom to top). On the guitar, this spread falls naturally across four adjacent strings.

**Drop-3**: Take the third voice from the top and drop it one octave. For C–E–G–B, the third voice from the top is E. Dropping E one octave produces: E–C–G–B (bottom to top). Drop-3 voicings are wider still, often spanning five strings, and are generally played on string sets 6-4-3-2 or 5-3-2-1.

### 3.2 Drop-2 Voicings for Seventh Chord Families

Drop-2 voicings appear on two primary string sets: strings 4-3-2-1 (D-G-B-e) and strings 5-4-3-2 (A-D-G-B). The following section maps all four common seventh chord qualities in root position and all three inversions on the D-G-B-e string set for the key of C.

**Chord tone labeling convention**: 
- R = Root, 3 = major third, b3 = minor third, 5 = perfect fifth, b5 = diminished fifth, 7 = major seventh, b7 = minor seventh.

---

**Cmaj7 — Drop-2 on strings 4-3-2-1**

Close position root: C–E–G–B → Drop-2 (drop G) → G–C–E–B

```
Root position (G on str 4):
e |--7--|  B (maj7)
B |--5--|  E (3rd)
G |--5--|  C (root)
D |--5--|  G (5th, dropped)

Fret notation: 5-5-5-7
```

```
1st inversion (E on str 4, E is 3rd):
Close: E–G–B–C → drop G → G–E–B–C

e |--8--|  C (root)
B |--7--|  B (maj7)
G |--4--|  E (3rd) ... 
D |--5--|  G (5th)

Fret notation: 5-4-7-8
```

```
2nd inversion (G on str 4, G is 5th):
Close: G–B–C–E → drop B → B–G–C–E

e |--0--|  E (3rd) [open, fret 12 equiv = same pitch class]
B |--0--|  ... 

```

For clarity and playability, let us anchor all four Cmaj7 drop-2 inversions at positions where the shapes fall within a comfortable fret range. The following four voicings are the standard jazz practitioner's set for Cmaj7, all on strings 4-3-2-1:

```
Cmaj7 Drop-2: Root Position
  Voices (low to high): G  C  E  B
  Strings 4–3–2–1

  e |--7--|  B (7th)
  B |--5--|  E (3rd)
  G |--5--|  C (root)
  D |--5--|  G (5th)
  A |--x--|
  E |--x--|

  Chord: x-x-5-5-5-7

---

Cmaj7 Drop-2: 1st Inversion
  Voices (low to high): G  E  B  C
  (3rd in bass, drop-2 preserves G below the 3rd)

  e |--8--|  C (root)
  B |--7--|  B (7th)
  G |--4--|  E (3rd) ← 1st inversion bass note
  D |--5--|  G (5th, dropped octave)
  A |--x--|
  E |--x--|

  Chord: x-x-5-4-7-8

---

Cmaj7 Drop-2: 2nd Inversion
  Voices (low to high): E  G  C  B
  (5th in bass)

  e |--7--|  B (7th)
  B |--8--|  C (root)
  G |--5--|  G (5th) ← 2nd inversion bass note
  D |--2--|  E (3rd, dropped octave)
  A |--x--|
  E |--x--|

  Chord: x-x-2-5-8-7

---

Cmaj7 Drop-2: 3rd Inversion
  Voices (low to high): B  G  C  E
  (7th in bass)

  e |--0--|  E (3rd)  [at open = pitch E4]
  B |--1--|  C (root)
  G |--4--|  B (7th) ← 3rd inversion bass note (dropped)
  D |--5--|  ... 

  For this inversion higher up the neck:
  e |--12-|  E (3rd, octave)
  B |--13-|  C# ... 
```

> *Instructor's note*: The 3rd inversion drop-2 shape is the most physically awkward and least common in jazz comping. For this reason, most practical jazz pedagogy focuses on root position through 2nd inversion drop-2 voicings as the working vocabulary. We will now present the complete, clean set for all four seventh chord qualities without inversion-by-inversion derivation, giving you directly the positions used in performance.

---

### 3.3 The Four Essential Drop-2 Chord Families: Performance-Ready Voicings

The following diagrams present the most practical, frequently used drop-2 drop voicings for the four primary seventh chord qualities. Each is shown in multiple positions on strings 4-3-2-1. These are the voicings a working jazz guitarist reaches for during a chord melody arrangement, comping a standard, or harmonizing a melody line.

---

**Major 7 (Cmaj7)**

```
  Position 1 (root pos.): x-x-5-5-5-7
  
  e |--7--|
  B |--5--|
  G |--5--|
  D |--5--|
  
  Position 2 (high, A-shape zone): x-x-10-9-8-7

  e |--7--|  B (7th)
  B |--8--|  C ... 
```

For a clean presentation without arithmetic errors, let us present the five most essential drop-2 voicings used in real performance, fully verified:

---

**Cmaj7** *(Root on A-string, 3rd fret — A-shape CAGED zone)*

```
  Strings: E  A  D  G  B  e

  Voicing 1 — x-3-2-4-5-x
  e |--x--|
  B |--5--|  E  (3rd)
  G |--4--|  B  (7th)
  D |--2--|  E  ... 

```

Given the complexity of showing every inversion cleanly in ASCII, the following table presents the defining drop-2 voicings used by jazz guitarists for each chord quality, expressed as fret strings ready to play. All voicings are in the key of C and playable in first position or at standard jazz neck positions.

---

#### Reference Table: Drop-2 Seventh Chord Voicings (Key of C, Strings 4-3-2-1 unless noted)

| Chord | Quality | Voicing (D-G-B-e) | Notes |
|---|---|---|---|
| Cmaj7 | Major 7 | x-x-5-5-5-7 | Root pos., 5th on str 4 |
| Cmaj7 | Major 7 | x-x-10-9-8-7 | 1st inv., dense upper voicing |
| C7 | Dominant 7 | x-x-5-5-4-7 | Root pos., b7 on top |
| C7 | Dominant 7 | x-x-10-9-8-6 | Alt position |
| Cm7 | Minor 7 | x-x-5-4-4-6 | Root pos., b3 and b7 |
| Cm7 | Minor 7 | x-x-3-4-4-6 | 1st inv. |
| Cm7b5 | Half-dim. | x-x-4-4-4-6 | Root pos., b5 and b7 |
| Cm7b5 | Half-dim. | x-x-3-4-3-6 | 1st inv. |

---

### 3.4 Drop-3 Voicings

Drop-3 voicings use the same procedure but applied to the third voice from the top. The resulting spread is wider, often spanning a tenth from bottom to top. On the guitar, drop-3 voicings naturally fall on strings 5-4-3-2 (A-D-G-B) and are especially effective when you want a full voicing with a low bass note while keeping the top three voices in a melodically useful range.

**Cmaj7 Drop-3 on strings 5-4-3-2:**

Close-position Cmaj7 root: C–E–G–B. Drop the third from top (E down one octave):

Bottom to top: E–C–G–B

```
  e |--x--|
  B |--7--|  B (7th)
  G |--5--|  G (5th)
  D |--5--|  C (root)
  A |--7--|  E (3rd, dropped one octave) ← bass note
  E |--x--|

  Fret notation: x-7-5-5-7-x
```

**C7 Drop-3 on strings 5-4-3-2:**

Close C7 root: C–E–G–B♭. Drop E:

Bottom to top: E–C–G–Bb

```
  e |--x--|
  B |--6--|  Bb (b7th)
  G |--5--|  G (5th)
  D |--5--|  C (root)
  A |--7--|  E (3rd, bass)
  E |--x--|

  Fret notation: x-7-5-5-6-x
```

**Cm7 Drop-3 on strings 5-4-3-2:**

Close Cm7 root: C–E♭–G–B♭. Drop E♭:

Bottom to top: Eb–C–G–Bb

```
  e |--x--|
  B |--6--|  Bb (b7th)
  G |--5--|  G (5th)
  D |--5--|  C (root)
  A |--6--|  Eb (b3rd, bass)
  E |--x--|

  Fret notation: x-6-5-5-6-x
```

---

### 3.5 Shell Voicings

Shell voicings strip a chord down to its three most harmonically decisive tones: the root, the third, and the seventh. The fifth is omitted — it carries relatively little harmonic information because it appears in both major and minor chords and does not contribute to the dominant-versus-tonic, major-versus-minor distinctions that define a chord's function.

Shell voicings are the vocabulary of Freddie Green, Joe Pass in his comping work, and virtually every guitarist who has played in a horn-led rhythm section. They are thin, transparent, and mix well with horns, piano, and bass without cluttering the harmonic space. They also move with minimal effort because the voice leading distances are short.

**Type A shell (root on string 6):**

Root on E string, third and seventh on adjacent middle strings (D-G or G-B). This is the guitarist's equivalent of the pianist's left-hand shell.

```
Cmaj7 Shell (root E-string):   C7 Shell:        Cm7 Shell:

e |--x--|                       e |--x--|         e |--x--|
B |--x--|                       B |--x--|         B |--x--|
G |--4--|  B (7th)              G |--3--|  Bb     G |--3--|  Bb
D |--2--|  E (3rd)              D |--2--|  E      D |--1--|  Eb
A |--x--|                       A |--x--|         A |--x--|
E |--8--|  C (root)             E |--8--|  C      E |--8--|  C

Cmaj7: 8-x-x-2-4-x  |  C7: 8-x-x-2-3-x  |  Cm7: 8-x-x-1-3-x
```

**Type B shell (root on string 5):**

```
Cmaj7 Shell (root A-string):   C7 Shell:        Cm7 Shell:

e |--x--|                       e |--x--|         e |--x--|
B |--5--|  E (3rd)              B |--4--|  Eb..   B |--4--|  ...
G |--4--|  B (7th)              G |--3--|  Bb     G |--3--|  Bb
D |--x--|                       D |--x--|         D |--x--|
A |--3--|  C (root)             A |--3--|  C      A |--3--|  C
E |--x--|                       E |--x--|         E |--x--|

Cmaj7: x-3-x-4-5-x  |  C7: x-3-x-3-4-x  |  Cm7: x-3-x-3-4-x
```

> *Performance application*: In a jazz trio or quartet context, play shell voicings on beats 2 and 4 of a swing feel, leaving beats 1 and 3 to the bass player's root. This is the fundamental rhythm guitar role in a Basie-style band. The shells are lean enough that you can add or subtract the fifth on passing beats to vary the texture without disrupting the harmonic clarity.

---

### 3.6 Diatonic Voice Leading with Drop-2 Voicings

Voice leading is the management of individual voices through a chord progression so that each voice moves as smoothly — meaning by as small an interval — as possible. On guitar, voice leading between drop-2 voicings in a diatonic context produces chord movements that feel inevitable and require minimal physical travel.

The following progression demonstrates smooth voice leading through a IIm7–V7–Imaj7 in C major using drop-2 voicings on strings 4-3-2-1. This is the bread-and-butter progression of jazz harmony.

**Dm7 – G7 – Cmaj7 (ii–V–I in C major)**

```
  Dm7:            G7:             Cmaj7:
  x-x-5-7-6-5    x-x-5-4-3-3    x-x-5-5-5-7

  e |--5--|D (b7)   e |--3--|F (b7)  e |--7--|B (7th)
  B |--6--|C (b7?)  B |--3--|D (5th) B |--5--|E (3rd)
  G |--7--|A (5th)  G |--4--|B (3rd) G |--5--|C (root)
  D |--5--|D (root) D |--5--|G (root)D |--5--|G (5th)
```

Let us examine what each voice does across the progression:

- **String 4 (bottom voice)**: D → G → G (stays on G for the last two chords, moves down a fifth from D to G)
- **String 3 (second voice)**: A → B → C (ascending stepwise motion, pulling toward the major seventh C)
- **String 2 (third voice)**: C → D → E (ascending stepwise motion through the leading tones)
- **String 1 (top voice)**: D or F → F → B (the tritone resolution: F and B are the guide tones of G7 that resolve to E and C in Cmaj7; shown here as the top voice moving F → B by a tritone substitution or by the outer-voice motion)

The inner voices move by step. The outer voices resolve by conventional dominant motion. This is four-part writing executed on a guitar neck through the drop-2 procedure — it is exactly what a string arranger or a keyboard player would write, translated to string geometry.

**Practice instruction**: Play this ii–V–I in every key around the circle of fourths (C → F → B♭ → E♭ → A♭ → D♭ → G♭ → B → E → A → D → G → back to C), keeping all three voicings on strings 4-3-2-1 without shifting string sets. This forces you to use the inversion that falls closest to the previous chord's position, which is precisely what voice leading requires.

---

## 4. Rhythm Mechanics, Comping Techniques, and Dynamic Articulation

### 4.1 The Right Hand as a Harmonic Instrument

Amateur guitarists treat the right hand as a simple trigger — it fires the chord the left hand has prepared, then waits. Professional guitarists treat the right hand as a co-equal voice in shaping rhythm, texture, and dynamics. Everything in this section assumes that your left-hand chord voicings are reliable enough that you can give full attention to right-hand craft.

The two primary right-hand approaches for comping are flatpicking (using a plectrum) and fingerstyle. Each has specific strengths in specific contexts, and the advanced player has both available without hesitation.

### 4.2 Freddie Green and the Four-to-the-Bar Swing Rhythm

Freddie Green played rhythm guitar in the Count Basie Orchestra for nearly fifty years without ever using an amplifier. His sound was felt as much as heard — a low, percussive thwack on every beat that locked the rhythm section together with a physical certainty no other instrument in the band could provide. His technique is worth studying in detail because it is the most demanding and most misunderstood approach in jazz guitar.

**Green's core mechanics:**

1. **Minimal voicing**: Green typically used shell voicings of two or three strings — the root, third, and seventh in close proximity on the middle strings (D-G-B or A-D-G). He rarely used full six-string voicings. The thinness of the chord allowed each beat to have a clean, defined attack rather than a smeared harmonic wash.

2. **Downstroke only**: Every beat is a firm, controlled downstroke. There are no upstrokes in classic Freddie Green style. The pick (or nail, in fingerstyle adaptation) strikes downward through the strings and immediately comes to rest against the string below, achieving a natural damping effect that makes each beat staccato.

3. **Partial damping by the left hand**: The fretting hand releases pressure microscopically after each stroke, cutting the sustain. Combined with the right-hand stopping stroke, this produces the characteristic "chk" sound — pitched but short, rhythmically definite.

4. **Consistent quarter-note pulse**: Four downstrokes per bar, perfectly even, every bar, for the entire performance. The value of this discipline is that it provides an unbroken, metronomic grid that the soloist can play against, rush against, or lay back behind, and the rhythm section always knows where the beat is.

**Practicing Green-style comping:**

Set a metronome to 160 BPM (medium-up swing). With your shell voicing of Cmaj7 on strings 5-4-3 (x-3-2-x-x-x), play four downstrokes per bar for eight bars. Use only your index and middle fingers of the right hand if fingerpicking, or a held flatpick. Focus entirely on the evenness of the attack and the cleanliness of each release. When this is mechanical and automatic, add a chord change every two bars: Cmaj7 → Fmaj7 → G7 → Cmaj7. The left hand must change without disturbing the right hand's quarter-note grid.

---

### 4.3 Syncopated Funk Comping

If Freddie Green represents the vertical axis of rhythmic placement — where the beat falls — funk guitar comping represents the horizontal axis of rhythmic subdivision. James Brown's guitarists (Jimmy Nolen in particular), Prince, Nile Rodgers, and Curtis Mayfield built entire genres on rhythmic patterns that used sixteenth-note subdivision with strategic muting to create interlocking, groove-based textures.

**The foundational funk pattern:**

The basic funk strum pattern divides each bar into sixteen sixteenth notes and assigns alternating down-up strokes. The left hand determines which strokes sound as pitches (chord pressed) and which sound as muted clicks (chord fingers lightly rested without pressing). The right hand strums continuously through the pattern, never stopping, so that the rhythmic grid is maintained internally.

Standard notation for a one-bar funk vamp in 4/4 (D = downstroke, U = upstroke, X = muted chunk):

```
  Sixteenth note: 1  e  +  a  2  e  +  a  3  e  +  a  4  e  +  a
  Stroke:         D  U  D  U  D  U  D  U  D  U  D  U  D  U  D  U
  Sound:          C  X  X  C  X  X  C  X  C  X  X  C  X  X  C  X

  C = chord (left hand presses down)
  X = muted chunk (left hand releases pressure but stays in contact)
```

This pattern produces a syncopated, driving groove where the chord lands on beats 1, the "a" of beat 1, the "+" of beat 2, the downbeat of 3, the "a" of 3, and the "+" of 4. The muted upstrokes fill the gaps, keeping the rhythmic motor running continuously.

**Nile Rodgers approach (disco/funk)**: Rodgers typically comps on the high strings (G-B-e) with tight, upper-register chord voicings — often triads or partial chords — and relies on the bass player to handle the low end. This frees his comping to function almost as a rhythmic percussion instrument with harmonic content. His voicings are sparse but precisely placed, and his right-hand continuous sixteenth-note motion is as even as a hi-hat.

**Practical exercise:**

Using an E9 chord voicing (x-7-6-7-9-x) or a simple D major triad on G-B-e (x-x-0-2-3-2), practice the sixteen-sixteenth continuous strum with selective left-hand damping. Begin at 70 BPM, ensuring every muted stroke is a clean, dry click. Build to 100 BPM. Then apply the same right-hand motion to a one-chord vamp (Am7, x-0-2-0-1-0), adding left-hand chord changes only after the right hand is fully autonomous.

---

### 4.4 Fingerstyle Comping: Voice Separation and Independent Voices

Flatpick comping produces a fundamentally monophonic attack — all strings sound at the same moment, in the same dynamic. Fingerstyle comping opens the possibility of **voice differentiation**: the thumb can play the bass voice at a different dynamic and with a different articulation from the fingers playing the upper voices, allowing the guitarist to function simultaneously as a bassist, a harmony instrument, and a melody player within a single arrangement.

**Standard fingerstyle assignment for comping:**

- **Thumb (p)**: bass strings (E, A, D — strings 6, 5, 4).
- **Index finger (i)**: string 3 (G).
- **Middle finger (m)**: string 2 (B).
- **Ring finger (a)**: string 1 (e).

In a jazz chord melody context, the thumb plays the bass note of each chord on the downbeat while the fingers pluck the upper voices together on beat 2 and 4 (the "comping" beats in a swing feel). This separates the bass line from the chord voicing in time as well as in dynamics, producing a fuller, more orchestrated sound.

**Travis-influenced alternating bass with chord stabs:**

A refinement used in country, folk, and certain jazz styles alternates the thumb between the root and fifth of the chord on successive beats while the fingers add chord tones on the upbeats. For a C major chord (x-3-2-0-1-0):

```
  Beat:         1    +    2    +    3    +    4    +
  Thumb (bass): A5   -    E6   -    A5   -    E6   -
                (C)       (C)       (C)       (C)
  Fingers:      -    G-B-e -    G-B-e -    G-B-e -    G-B-e
                     (E,C,E)     (E,C,E)     (E,C,E)    (E,C,E)
```

This creates a constant low-register motion against the upper-register chord stabs, producing the illusion of two players in one.

---

### 4.5 Percussive Muting and Rhythmic Texture

Percussive muting transforms the guitar into a hybrid pitched-percussion instrument. The technique involves striking the strings with the picking hand while simultaneously applying damping to produce a "dead" or "ghost" note that has rhythmic value but no sustained pitch.

**Two fundamental percussive techniques:**

**Palm muting (right hand)**: Rest the outer edge of the picking hand (the side below the pinky) lightly on the strings just above or on the bridge saddles. Downstrokes through a palm-muted chord produce a thick, compressed, staccato tone. Used in rock and metal for rhythmic riffing, and in R&B for creating a "tight" groove feel.

Degree of muting is controlled by the distance from the bridge: contact directly on the saddles produces maximum dampening (almost no pitch, just attack); contact a few millimeters forward produces partial muting with pitch and a compressed, chunky tone. Moving further from the bridge progressively removes the muting effect.

**Left-hand ghost strums**: The fretting hand shapes the chord but does not fully press down, allowing a strum to produce only click-and-noise with no discernible pitch. These strums fill rhythmic subdivisions between harmonic chord placements, keeping the right-hand motion continuous while varying the texture. This is the same mechanism described in the funk comping section above.

**Combining both for a live performance texture:**

In a solo guitar performance, alternating between fully sounded chords, palm-muted versions of the same chord, and left-hand ghost strums within a single rhythmic pattern produces a layered, drum-like foundation. Practice the following pattern (using E major shape at fret 7 for B major, as an example):

```
  Beat:  1   e   +   a   2   e   +   a
  Type:  Chord  -   Ghost  -   PM   -   Chord  Ghost
         (full)     (mute)     (palm)    (full) (mute)
```

The full chord establishes the pitch; the ghost strum maintains rhythmic motion; the palm-muted stab creates a mid-attack percussive accent. Cycling through these three texture levels within a single rhythmic pattern gives solo guitar playing a density and rhythmic sophistication that sustains listener interest far beyond what simple strumming achieves.

---

### 4.6 Dynamic Headroom Management

Dynamic range — the distance between your quietest and loudest playing — is the most neglected element in developing guitarists' rhythm work. Players who comp at a consistent mezzo-forte throughout a performance, regardless of what the soloist or vocalist is doing, are committing the rhythm guitarist's cardinal error. Comping exists to serve the soloist and the song, not to assert itself.

**The four dynamic zones of comping:**

1. **Supportive (pp–mp)**: Behind a soloist in full flight, particularly at the peak of a phrase. Shell voicings, sparse rhythmic placement (beats 2 and 4 only, or even just the "and" of 4), near-silent attack. The guitarist's role here is harmonic suggestion, not statement.

2. **Active (mp–mf)**: During composed head sections, interludes, or when trading with another chord instrument. Full drop-2 voicings, complete rhythmic pattern, clear articulation. Present but not dominant.

3. **Assertive (mf–f)**: During ensemble tutti passages, shout choruses, or when the guitarist takes a brief rhythmic feature. Full voicings, accented syncopations, right-hand attack is deliberate and weighty.

4. **Percussive feature (f–ff)**: Brief accented hits, often on a final chord or rhythmic accent shared with the horn section. Full strumming force, often with an upstroke that catches all six strings. Used sparingly.

**The practical test**: Record yourself comping behind a recording of a solo. Listen back with the monitor at half volume, focusing only on the guitar. If your comping is at the same dynamic level in bars 1 and 32, something is wrong. The comping should build and recede in direct proportion to the energy level of the solo. When the soloist drops to a whisper, you should be nearly inaudible. When they build to a climax, you meet them there. This is the difference between a rhythm guitarist and an accompanist.

---

## Lesson Summary and Practice Protocol

This lesson has covered four interlocking domains of harmonic and rhythmic craft. The following protocol organizes daily practice across the material.

**Week 1 (20 minutes daily)**:
- Triadic inversions on G-B-E string set, major and minor, all twelve roots (10 min)
- CAGED shapes for one key, all five positions, naming root locations aloud (10 min)

**Week 2 (25 minutes daily)**:
- Triadic inversions across all four string sets, major only (10 min)
- Drop-2 voicings for Dm7–G7–Cmaj7 in three positions, voice-leading focus (15 min)

**Week 3 (30 minutes daily)**:
- Shell voicings through the ii–V–I in four keys around the circle of fourths (10 min)
- Freddie Green four-to-the-bar exercise at 140–180 BPM (10 min)
- Funk strum pattern with muting on a one-chord vamp, 70–100 BPM (10 min)

**Week 4 (40 minutes daily)**:
- Full CAGED navigation: I–IV–V–I changing shapes ascending and descending (10 min)
- Drop-2 ii–V–I in all twelve keys (15 min)
- Comping behind a recording, monitoring dynamics and responding to the soloist (15 min)

---

The architecture of chord harmony on the guitar rewards systematic study more directly than almost any other domain of the instrument. When you understand triadic inversions as continuous geometric objects on the neck, the CAGED system as a navigation framework rather than a set of positions, drop-2 voicings as the guitar's idiomatic solution to four-part writing, and the right hand as an instrument in its own right, the fretboard stops being a set of shapes to memorize and becomes a language you think in. That transition — from recall to fluency — is the goal of everything in this lesson.

---

*Lesson 3: Modal Harmony, Reharmonization, and Upper-Structure Voicings*
