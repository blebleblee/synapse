# Beginner Hands-On Lab: Music Theory

## Objective & Prerequisites
The objective of this lab is to familiarize you with the basic tools and environment necessary for exploring music theory. This lab assumes you have access to a computer with internet connectivity and are comfortable using a command-line interface (CLI) or a graphical user interface (GUI). We will use a simple music theory library called `music21` in Python, which is widely used for music analysis and composition.

### Prerequisites:
- Basic knowledge of Python programming.
- Python installed on your system (version 3.6 or higher).
- Ability to use a text editor or an Integrated Development Environment (IDE) like VSCode, PyCharm, or Jupyter Notebook.

## Exercise 1: Environment Setup & Sanity Check
Before we begin, we need to ensure that `music21` is installed and properly configured on your system. Follow these steps to set up your environment:

1. **Open your terminal or command prompt.**

2. **Install `music21` using pip:**
   ```bash
   pip install music21
   ```

3. **Verify the installation by running a simple Python script:**
   Create a new file named `test_music21.py` and add the following code:
   ```python
   from music21 import *

   # Create a simple note
   n = note.Note("C4")
   print(n)
   ```

4. **Run the script:**
   ```bash
   python test_music21.py
   ```

   **Expected Output:**
   ```
   <music21.note.Note C>
   ```

If you see the expected output, your environment is set up correctly, and you are ready to proceed.

## Exercise 2: Your First Working Experiment
In this exercise, we will create a simple melody using `music21` and play it back. Follow these steps:

1. **Create a new Python file named `simple_melody.py` and add the following code:**
   ```python
   from music21 import *

   # Create a stream to hold our melody
   melody = stream.Stream()

   # Add notes to the melody
   notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
   for pitch in notes:
       n = note.Note(pitch, quarterLength=0.5)
       melody.append(n)

   # Show the melody in a music notation format
   melody.show()
   ```

2. **Run the script:**
   ```bash
   python simple_melody.py
   ```

   **Expected Output:**
   A window will open displaying the melody in music notation. If you have a MIDI synthesizer installed, you may also hear the melody played back.

## Exercise 3: Inspecting Basic State
In this exercise, we will inspect the basic state of the notes in our melody. Follow these steps:

1. **Modify the `simple_melody.py` file to include the following code:**
   ```python
   from music21 import *

   # Create a stream to hold our melody
   melody = stream.Stream()

   # Add notes to the melody
   notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
   for pitch in notes:
       n = note.Note(pitch, quarterLength=0.5)
       melody.append(n)

   # Print the details of each note in the melody
   for n in melody.notes:
       print(f"Pitch: {n.pitch}, Duration: {n.duration.type}, Quarter Length: {n.quarterLength}")

   # Show the melody in a music notation format
   melody.show()
   ```

2. **Run the script:**
   ```bash
   python simple_melody.py
   ```

   **Expected Output:**
   The terminal will display the details of each note in the melody, followed by the music notation window:
   ```
   Pitch: C4, Duration: quarter, Quarter Length: 0.5
   Pitch: D4, Duration: quarter, Quarter Length: 0.5
   Pitch: E4, Duration: quarter, Quarter Length: 0.5
   Pitch: F4, Duration: quarter, Quarter Length: 0.5
   Pitch: G4, Duration: quarter, Quarter Length: 0.5
   Pitch: A4, Duration: quarter, Quarter Length: 0.5
   Pitch: B4, Duration: quarter, Quarter Length: 0.5
   Pitch: C5, Duration: quarter, Quarter Length: 0.5
   ```

## Challenge Exercise
Create a simple chord progression using `music21` and display it in music notation. Use the following chords: C major, G major, Am minor, F major.

1. **Create a new Python file named `chord_progression.py` and add the following code:**
   ```python
   from music21 import *

   # Create a stream to hold our chord progression
   progression = stream.Stream()

   # Define the chords
   chords = [
       chord.Chord(["C4", "E4", "G4"]),
       chord.Chord(["G4", "B4", "D5"]),
       chord.Chord(["A4", "C5", "E5"]),
       chord.Chord(["F4", "A4", "C5"])
   ]

   # Add chords to the progression
   for c in chords:
       c.duration.type = 'half'
       progression.append(c)

   # Show the chord progression in a music notation format
   progression.show()
   ```

2. **Run the script:**
   ```bash
   python chord_progression.py
   ```

   **Expected Output:**
   A window will open displaying the chord progression in music notation. If you have a MIDI synthesizer installed, you may also hear the chords played back.

Congratulations! You have completed the Beginner Hands-On Lab for Music Theory. You now have a basic understanding of how to set up your environment, create simple melodies and chord progressions, and inspect the state of musical objects using `music21`.
