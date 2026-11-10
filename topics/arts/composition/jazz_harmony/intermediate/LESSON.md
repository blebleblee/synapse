# Intermediate Technical Lesson: Jazz Harmony

## 1. Production Architecture & Invariant Mechanisms

In the realm of jazz harmony, the architecture of a production system must be robust, flexible, and capable of handling the complex harmonic progressions and improvisational elements that define the genre. The system should be designed to support a wide range of harmonic functions, from simple diatonic progressions to complex substitutions and extensions. The invariant mechanisms in this architecture include:

- **Harmonic Function Mapping:** A consistent mapping of harmonic functions (e.g., tonic, dominant, subdominant) to their respective chord types and extensions.
- **Chord Substitution Rules:** A set of rules for substituting chords within a progression, such as tritone substitutions, secondary dominants, and modal interchange.
- **Improvisational Guidelines:** A framework for generating and evaluating improvisational lines, including the use of scales, modes, and arpeggios.

These mechanisms ensure that the system can generate harmonically rich and contextually appropriate music, regardless of the specific style or genre.

## 2. Data Structures, Protocols & Wire Formats

### Data Structures

- **Chord Progression:** A list of chords, each represented by a root note, chord type, and optional extensions. For example, `Cmaj7` or `D7alt9`.
- **Scale:** A list of notes representing a scale, such as a major scale, minor scale, or mode. For example, `Cmaj` or `Ddorian`.
- **Harmonic Function:** A mapping of a chord to its harmonic function within a progression. For example, `Cmaj7` as the tonic in the key of C.

### Protocols

- **Chord Progression Protocol:** A protocol for generating and manipulating chord progressions, including functions for transposing, substituting, and extending chords.
- **Scale Protocol:** A protocol for generating and manipulating scales, including functions for transposing, mode mixing, and generating arpeggios.
- **Improvisation Protocol:** A protocol for generating and evaluating improvisational lines, including functions for generating scales, modes, and arpeggios.

### Wire Formats

- **Chord Progression Format:** A format for representing chord progressions in a machine-readable form, such as JSON or XML. For example:
  ```json
  {
    "chords": [
      {"root": "C", "type": "maj7"},
      {"root": "D7", "type": "alt9"},
      {"root": "G7", "type": "dom7"},
      {"root": "Cmaj7", "type": "maj7"}
    ]
  }
  ```
- **Scale Format:** A format for representing scales in a machine-readable form, such as JSON or XML. For example:
  ```json
  {
    "root": "C",
    "type": "major",
    "notes": ["C", "D", "E", "F", "G", "A", "B"]
  }
  ```

## 3. Full Production Implementation (Enterprise-grade, zero-placeholder code or manifests)

Below is a simplified example of an enterprise-grade implementation of jazz harmony in Python. This implementation includes a chord progression generator, a scale generator, and an improvisation generator.

```python
import random

# Chord Progression Generator
class ChordProgression:
    def __init__(self, key, chords):
        self.key = key
        self.chords = chords

    def transpose(self, interval):
        transposed_chords = []
        for chord in self.chords:
            new_root = self.transpose_note(chord['root'], interval)
            transposed_chords.append({'root': new_root, 'type': chord['type']})
        return ChordProgression(self.transpose_note(self.key, interval), transposed_chords)

    def transpose_note(self, note, interval):
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        index = notes.index(note) + interval
        return notes[index % 12]

    def substitute_chords(self):
        substitutions = {
            'maj7': ['7alt9'],
            'dom7': ['maj7', '7sus4'],
            'min7': ['7alt9', 'maj7']
        }
        substituted_chords = []
        for chord in self.chords:
            if chord['type'] in substitutions:
                new_type = random.choice(substitutions[chord['type']])
                substituted_chords.append({'root': chord['root'], 'type': new_type})
            else:
                substituted_chords.append(chord)
        return ChordProgression(self.key, substituted_chords)

# Scale Generator
class Scale:
    def __init__(self, root, type):
        self.root = root
        self.type = type
        self.notes = self.generate_scale()

    def generate_scale(self):
        scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'dorian': [0, 2, 3, 5, 7, 9, 10],
            'phrygian': [0, 1, 3, 5, 7, 8, 10],
            'lydian': [0, 2, 4, 6, 7, 9, 11],
            'mixolydian': [0, 2, 4, 5, 7, 9, 10],
            'aeolian': [0, 2, 3, 5, 7, 8, 10],
            'locrian': [0, 1, 3, 5, 6, 8, 10]
        }
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        index = notes.index(self.root)
        scale_notes = [notes[(index + interval) % 12] for interval in scales[self.type]]
        return scale_notes

# Improvisation Generator
class Improvisation:
    def __init__(self, scale, length):
        self.scale = scale
        self.length = length

    def generate_line(self):
        return [random.choice(self.scale) for _ in range(self.length)]

# Example Usage
key = 'C'
chords = [
    {'root': 'C', 'type': 'maj7'},
    {'root': 'D7', 'type': 'dom7'},
    {'root': 'G7', 'type': 'dom7'},
    {'root': 'Cmaj7', 'type': 'maj7'}
]
progression = ChordProgression(key, chords)
transposed_progression = progression.transpose(2)
substituted_progression = transposed_progression.substitute_chords()

scale = Scale('C', 'major')
improvisation = Improvisation(scale.notes, 8)
line = improvisation.generate_line()

print("Original Progression:", progression.chords)
print("Transposed Progression:", transposed_progression.chords)
print("Substituted Progression:", substituted_progression.chords)
print("Scale Notes:", scale.notes)
print("Improvisation Line:", line)
```

## 4. Performance Tuning, Scaling & Edge Cases

### Performance Tuning

- **Efficient Data Structures:** Use efficient data structures for storing and manipulating chord progressions and scales, such as lists and dictionaries.
- **Caching:** Cache frequently used chord progressions and scales to reduce computation time.
- **Parallel Processing:** Use parallel processing to generate multiple chord progressions and improvisation lines simultaneously.

### Scaling

- **Modular Design:** Design the system in a modular manner, allowing for easy addition and removal of features.
- **Scalable Data Structures:** Use scalable data structures that can handle large chord progressions and scales.

### Edge Cases

- **Invalid Chords:** Handle invalid chords by generating a default chord or raising an error.
- **Invalid Scales:** Handle invalid scales by generating a default scale or raising an error.
- **Invalid Improvisation Lines:** Handle invalid improvisation lines by generating a default line or raising an error.

## 5. Architectural Summary & Production Checklist

### Architectural Summary

- **Chord Progression Generator:** A component for generating and manipulating chord progressions.
- **Scale Generator:** A component for generating and manipulating scales.
- **Improvisation Generator:** A component for generating and evaluating improvisational lines.

### Production Checklist

- [ ] Implement chord progression generator with transposition and substitution functions.
- [ ] Implement scale generator with mode mixing and arpeggio generation functions.
- [ ] Implement improvisation generator with scale and mode selection functions.
- [ ] Test chord progression generator with various keys and chord types.
- [ ] Test scale generator with various roots and types.
- [ ] Test improvisation generator with various scales and lengths.
- [ ] Optimize performance with efficient data structures and caching.
- [ ] Ensure scalability with modular design and scalable data structures.
- [ ] Handle edge cases with error handling and default values.
