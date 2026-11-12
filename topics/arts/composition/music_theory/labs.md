# Operational Verification Labs: Music Theory

## Objective & Lab Setup

This laboratory aims to provide hands-on experience with foundational music theory concepts through practical implementation, parameter variation, and fault injection. Utilizing the open-source music theory library `music21` in Python, participants will analyze, create, and manipulate musical data. Ensure Python and the `music21` library are installed on your system. Installation can be achieved via pip:

```bash
pip install music21
```

A basic understanding of Python programming and music theory concepts, including scales, chords, and intervals, is assumed.

## Exercise 1: Foundational Practical Implementation

In this exercise, we will create a simple C major scale and a C major chord using `music21`. These will be displayed on the console and saved as MIDI files.

### Step-by-Step Runnable Exercise Demonstrating the Core Concept

#### Step 1: Import the necessary modules

```python
from music21 import scale, chord, stream
```

#### Step 2: Create a C major scale

```python
c_major_scale = scale.MajorScale('C')
```

#### Step 3: Generate the notes of the C major scale

```python
c_major_notes = c_major_scale.getPitches('C', 'C8')
```

#### Step 4: Create a stream to hold the scale

```python
scale_stream = stream.Stream()
scale_stream.append(c_major_notes)
```

#### Step 5: Display the scale

```python
scale_stream.show('text')
```

#### Step 6: Save the scale as a MIDI file

```python
scale_stream.write('midi', 'c_major_scale.mid')
```

#### Step 7: Create a C major chord

```python
c_major_chord = chord.Chord(['C4', 'E4', 'G4'])
```

#### Step 8: Create a stream to hold the chord

```python
chord_stream = stream.Stream()
chord_stream.append(c_major_chord)
```

#### Step 9: Display the chord

```python
chord_stream.show('text')
```

#### Step 10: Save the chord as a MIDI file

```python
chord_stream.write('midi', 'c_major_chord.mid')
```

## Exercise 2: Parameter Variation & Empirical Analysis

In this exercise, we will explore different scales and chords by varying parameters and analyzing the outputs. We will generate a C minor scale and a C7 chord, then compare them with the C major scale and C major chord created in Exercise 1.

#### Step 1: Create a C minor scale

```python
c_minor_scale = scale.MinorScale('C')
c_minor_notes = c_minor_scale.getPitches('C', 'C8')
minor_scale_stream = stream.Stream()
minor_scale_stream.append(c_minor_notes)
minor_scale_stream.show('text')
minor_scale_stream.write('midi', 'c_minor_scale.mid')
```

#### Step 2: Create a C7 chord

```python
c7_chord = chord.Chord(['C4', 'E4', 'G4', 'Bb4'])
c7_chord_stream = stream.Stream()
c7_chord_stream.append(c7_chord)
c7_chord_stream.show('text')
c7_chord_stream.write('midi', 'c7_chord.mid')
```

#### Step 3: Compare the scales and chords

Listen to the MIDI files generated for the C major scale, C minor scale, C major chord, and C7 chord. Analyze the differences in sound and harmonic tension.

## Exercise 3: Fault Injection & Stress Testing

In this exercise, we will intentionally create errors by using invalid parameters and observe the behavior of the `music21` library. We will then correct these errors to verify recovery.

#### Step 1: Create a scale with an invalid tonic

```python
try:
    invalid_scale = scale.MajorScale('Z')
except Exception as e:
    print(f"Error: {e}")
```

#### Step 2: Create a chord with an invalid note

```python
try:
    invalid_chord = chord.Chord(['C4', 'E4', 'G4', 'Z4'])
except Exception as e:
    print(f"Error: {e}")
```

#### Step 3: Correct the errors and verify recovery

```python
# Correcting the invalid scale
correct_scale = scale.MajorScale('C')
correct_scale_notes = correct_scale.getPitches('C', 'C8')
correct_scale_stream = stream.Stream()
correct_scale_stream.append(correct_scale_notes)
correct_scale_stream.show('text')
correct_scale_stream.write('midi', 'correct_scale.mid')

# Correcting the invalid chord
correct_chord = chord.Chord(['C4', 'E4', 'G4', 'Bb4'])
correct_chord_stream = stream.Stream()
correct_chord_stream.append(correct_chord)
correct_chord_stream.show('text')
correct_chord_stream.write('midi', 'correct_chord.mid')
```

## Practical Cheat Sheet & Quick Reference

### Essential Commands, Parameters, Formulas, and Verification Checks

| Command/Parameter | Description |
|-------------------|-------------|
| `scale.MajorScale('C')` | Creates a major scale with C as the tonic. |
| `scale.MinorScale('C')` | Creates a minor scale with C as the tonic. |
| `chord.Chord(['C4', 'E4', 'G4'])` | Creates a C major chord. |
| `chord.Chord(['C4', 'E4', 'G4', 'Bb4'])` | Creates a C7 chord. |
| `stream.Stream()` | Creates a stream to hold musical elements. |
| `stream.show('text')` | Displays the musical elements in text format. |
| `stream.write('midi', 'filename.mid')` | Writes the stream to a MIDI file. |

By following these exercises, you will gain a practical understanding of music theory concepts and their implementation using the `music21` library. This will enable you to analyze, create, and manipulate musical data effectively.
