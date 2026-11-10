# Beginner Technical Lesson: Music Theory

## 1. Core Mechanics & Basic Principles (How it works under the hood at a fundamental level)

Music theory is the study of the elements of music and the rules that govern their combination. At its core, music theory encompasses the principles of pitch, rhythm, harmony, and form. These elements are interconnected and form the foundation of musical composition and performance.

### Pitch
Pitch refers to the perceived frequency of a sound. In Western music, the standard pitch system is based on the equal temperament scale, which divides the octave into 12 equal parts called semitones. The frequency of each note can be calculated using the formula \( f_n = f_0 \cdot 2^{n/12} \), where \( f_0 \) is the frequency of a reference note (typically A4 at 440 Hz), and \( n \) is the number of semitones away from the reference note.

### Rhythm
Rhythm is the pattern of sounds and silences in music. It is measured in beats, which are grouped into measures according to a time signature. Common time signatures include 4/4, 3/4, and 2/4, indicating the number of beats per measure and the type of note that receives one beat.

### Harmony
Harmony involves the simultaneous combination of pitches. Chords are the building blocks of harmony, consisting of three or more notes played together. The most common chords are triads, which consist of a root note, a third, and a fifth. Chords can be major, minor, diminished, or augmented, depending on the intervals between the notes.

### Form
Form refers to the structure of a musical composition. Common forms include binary, ternary, and rondo. Binary form consists of two sections (A and B), while ternary form consists of three sections (A, B, and A'). Rondo form features a recurring theme (A) with contrasting sections (B, C, etc.).

## 2. Step-by-Step Component Breakdown

### Pitch
1. **Identify the Reference Note**: Start with A4 at 440 Hz.
2. **Calculate Frequencies**: Use the formula \( f_n = f_0 \cdot 2^{n/12} \) to find the frequency of any note.
3. **Understand Semitones**: Each semitone represents a half-step in the equal temperament scale.

### Rhythm
1. **Understand Time Signatures**: Identify the number of beats per measure and the type of note that receives one beat.
2. **Count Beats**: Practice counting beats within a measure.
3. **Use Metronomes**: Use a metronome to maintain a steady tempo.

### Harmony
1. **Learn Chord Types**: Understand major, minor, diminished, and augmented chords.
2. **Build Chords**: Use the root, third, and fifth to construct triads.
3. **Practice Chord Progressions**: Experiment with common chord progressions like I-IV-V-I.

### Form
1. **Identify Sections**: Recognize the different sections of a piece of music.
2. **Understand Transitions**: Learn how sections transition from one to another.
3. **Create Simple Forms**: Start with binary or ternary forms.

## 3. First Working Implementation (Complete, clean, commented starter code or configuration)

Let's create a simple melody using the C major scale and a basic chord progression in 4/4 time.

### Melody
- **Notes**: C, E, G, C, E, G, C, E, G, C, E, G, C, E, G, C
- **Rhythm**: Quarter notes

### Chord Progression
- **Chords**: C, G, Am, F
- **Rhythm**: Four measures, each chord lasts one measure

### Configuration in MIDI (Example)
```plaintext
# MIDI Configuration for Simple Melody and Chord Progression

# Melody
0, 0, 60, 96  # C4, Start at 0, Duration 96 ticks
0, 96, 64, 96 # E4, Start at 96, Duration 96 ticks
0, 192, 67, 96 # G4, Start at 192, Duration 96 ticks
0, 288, 60, 96 # C4, Start at 288, Duration 96 ticks
0, 384, 64, 96 # E4, Start at 384, Duration 96 ticks
0, 480, 67, 96 # G4, Start at 480, Duration 96 ticks
0, 576, 60, 96 # C4, Start at 576, Duration 96 ticks
0, 672, 64, 96 # E4, Start at 672, Duration 96 ticks
0, 768, 67, 96 # G4, Start at 768, Duration 96 ticks
0, 864, 60, 96 # C4, Start at 864, Duration 96 ticks
0, 960, 64, 96 # E4, Start at 960, Duration 96 ticks
0, 1056, 67, 96 # G4, Start at 1056, Duration 96 ticks
0, 1152, 60, 96 # C4, Start at 1152, Duration 96 ticks
0, 1248, 64, 96 # E4, Start at 1248, Duration 96 ticks
0, 1344, 67, 96 # G4, Start at 1344, Duration 96 ticks
0, 1440, 60, 96 # C4, Start at 1440, Duration 96 ticks

# Chord Progression
0, 0, 60, 96 # C4, Start at 0, Duration 96 ticks
0, 0, 64, 96 # E4, Start at 0, Duration 96 ticks
0, 0, 67, 96 # G4, Start at 0, Duration 96 ticks
0, 96, 67, 96 # G4, Start at 96, Duration 96 ticks
0, 96, 71, 96 # B4, Start at 96, Duration 96 ticks
0, 96, 74, 96 # D5, Start at 96, Duration 96 ticks
0, 192, 69, 96 # A4, Start at 192, Duration 96 ticks
0, 192, 72, 96 # C5, Start at 192, Duration 96 ticks
0, 192, 76, 96 # E5, Start at 192, Duration 96 ticks
0, 288, 72, 96 # F4, Start at 288, Duration 96 ticks
0, 288, 75, 96 # A4, Start at 288, Duration 96 ticks
0, 288, 79, 96 # C5, Start at 288, Duration 96 ticks
```

## 4. What Can Go Wrong (Simple common mistakes and how to spot them)

### Pitch
- **Incorrect Frequency Calculation**: Ensure you use the correct formula to calculate note frequencies.
- **Misunderstanding Semitones**: Remember that each semitone represents a half-step in the equal temperament scale.

### Rhythm
- **Incorrect Time Signature**: Double-check the time signature to ensure the correct number of beats per measure.
- **Inconsistent Rhythm**: Practice counting beats to maintain a steady rhythm.

### Harmony
- **Incorrect Chord Construction**: Verify that chords are constructed using the correct intervals (root, third, fifth).
- **Improper Chord Progressions**: Experiment with common chord progressions to understand how they work.

### Form
- **Misidentified Sections**: Carefully analyze the different sections of a piece of music to understand its structure.
- **Poor Transitions**: Ensure smooth transitions between sections to maintain coherence.

## 5. Key Takeaways & Review Checklist

### Key Takeaways
- **Pitch**: Understand the equal temperament scale and how to calculate note frequencies.
- **Rhythm**: Practice counting beats and using metronomes to maintain a steady tempo.
- **Harmony**: Learn to construct chords and experiment with common chord progressions.
- **Form**: Identify the different sections of a piece of music and understand how they transition.

### Review Checklist
- [ ] Calculate the frequency of a few notes using the formula \( f_n = f_0 \cdot 2^{n/12} \).
- [ ] Practice counting beats in different time signatures.
- [ ] Construct a few chords and play them on an instrument.
- [ ] Identify the sections of a simple piece of music and understand how they transition.
