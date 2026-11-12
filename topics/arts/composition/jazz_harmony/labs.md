# Operational Verification Labs: Jazz Harmony

## Objective & Lab Setup

### Objective
This laboratory aims to provide hands-on experience in the practical implementation, parameter variation, and fault injection of jazz harmony concepts. Through a series of exercises, participants will gain a deep understanding of how jazz harmony functions within compositions and how to effectively use software tools to analyze and manipulate harmonic structures.

### Lab Setup
For this lab, you will need the following tools and environments:
- **Music Theory Software:** MuseScore, Finale, or Sibelius for notation and analysis.
- **Digital Audio Workstation (DAW):** Ableton Live, Logic Pro, or FL Studio for audio production and playback.
- **Harmony Analysis Tools:** ChordPro or a similar tool for chord chart creation and analysis.
- **Python Environment:** For scripting and data analysis, ensure Python 3.8 or later is installed along with libraries such as `numpy`, `matplotlib`, and `music21`.

## Exercise 1: Foundational Practical Implementation

### Exercise Overview
In this exercise, we will create a simple jazz chord progression and analyze its harmonic structure using both notation software and a DAW. This will serve as the foundation for more complex harmonic manipulations in subsequent exercises.

### Step-by-Step Procedure

Launch MuseScore and create a new score for a jazz ensemble, such as piano, bass, drums, and saxophone. Set the time signature to 4/4 and the key signature to C major. In the piano staff, enter the following chords: Cmaj7, D7, G7, Cmaj7. Use the chord symbol plugin to add chord symbols above the staff, ensuring each chord lasts for one measure. In the bass staff, add a simple walking bass line that outlines the roots and third of each chord. In the drum staff, add a basic swing rhythm with hi-hat, snare, and bass drum. Export the score as a MIDI file to use in the DAW for further analysis and manipulation. Open your DAW and import the MIDI file, creating separate tracks for each instrument (piano, bass, drums). Use the chord symbol feature in your DAW to add chord symbols to the piano track, ensuring they match the progression entered in MuseScore. Play back the arrangement to ensure all parts are in sync and the harmony is correct, making any necessary adjustments to the rhythm or chord symbols.

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise Overview
In this exercise, we will vary the parameters of the chord progression and analyze the resulting harmonic changes. We will use Python to automate the process of generating different chord progressions and analyzing their harmonic content.

### Step-by-Step Procedure

Open a Python script and define a function that generates a random jazz chord progression based on a given key and length, using the `music21` library to create and manipulate chords.

```python
from music21 import *

def generate_chord_progression(key, length):
    scale = scale.MajorScale(key)
    chords = []
    for _ in range(length):
        root = scale[random.randint(0, 6)]
        chord_type = random.choice(['major7', 'minor7', 'dominant7'])
        chord = chord.Chord(root.pitches + [root.transpose(4).pitch, root.transpose(7).pitch])
        chord.add(root.transpose(11).pitch)
        chord.figure = chord_type
        chords.append(chord)
    return chords
```

Use the function to generate multiple chord progressions of varying lengths and keys, storing the progressions in a list for further analysis.

```python
progressions = [generate_chord_progression('C', 4) for _ in range(10)]
```

Define a function to analyze the harmonic content of a chord progression, using the `music21` library to extract harmonic intervals and analyze chord functions.

```python
def analyze_progression(progression):
    analysis = []
    for chord in progression:
        intervals = [interval.Interval(chord.pitches[0], pitch) for pitch in chord.pitches[1:]]
        analysis.append((chord.figure, [str(interval) for interval in intervals]))
    return analysis
```

Use `matplotlib` to create visualizations of the harmonic analysis, plotting the chord functions and their intervals over the progression.

```python
import matplotlib.pyplot as plt

def plot_analysis(analysis):
    chord_functions = [chord[0] for chord in analysis]
    intervals = [chord[1] for chord in analysis]
    plt.figure(figsize=(10, 5))
    plt.plot(chord_functions, marker='o')
    plt.title('Chord Functions in Progression')
    plt.xlabel('Chord Index')
    plt.ylabel('Chord Function')
    plt.xticks(range(len(chord_functions)), chord_functions)
    plt.show()
```

Run the analysis and visualization functions on the generated progressions, observing the harmonic changes and variations in the chord functions.

```python
for progression in progressions:
    analysis = analyze_progression(progression)
    plot_analysis(analysis)
```

## Exercise 3: Fault Injection & Stress Testing

### Exercise Overview
In this exercise, we will introduce intentional errors into the chord progression and analyze the resulting harmonic dissonance. This will help us understand how harmonic errors affect the overall structure and perception of a jazz composition.

### Step-by-Step Procedure

Modify the chord progression by replacing one or more chords with incorrect or dissonant chords. For example, replace a Cmaj7 with a Cdim7 or a G7 with a Gmaj7. Use the analysis function from Exercise 2 to analyze the faulty progression, comparing the harmonic intervals and chord functions of the faulty progression with the original. Enter the faulty progression into MuseScore and export it as a MIDI file. Import the MIDI file into the DAW and play back the arrangement, listening to the faulty progression and noting the dissonance and harmonic tension. Identify the faulty chords and replace them with the correct chords, reanalyzing the corrected progression using the analysis function. Play back the corrected progression and compare it with the original.
