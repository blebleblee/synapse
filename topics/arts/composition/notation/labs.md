# Operational Verification Labs: Notation

## Objective & Lab Setup

### Objective
This laboratory aims to provide hands-on experience with the practical implementation, parameter variation, and fault injection of musical notation systems. Through these exercises, you will gain a deep understanding of how notation tools function, how to configure them for different musical needs, and how to troubleshoot common issues.

### Lab Setup
For this laboratory, you will need the following tools and environments:

Music Notation Software: MuseScore or Finale. MuseScore is a free and open-source option, while Finale is a commercial product with a free trial. A Digital Audio Workstation (DAW): Ableton Live, Logic Pro, or FL Studio. These DAWs can be used to import and play back the notation files you create. A Text Editor: Any text editor of your choice (e.g., Sublime Text, VSCode, or Notepad++) for editing configuration files or code if necessary. A Graphing Tool: Excel, Google Sheets, or any other spreadsheet software for graphing responses from parameter variations.

## Exercise 1: Foundational Practical Implementation

### Exercise 1a: Creating a Simple Score
Open MuseScore or Finale and create a new score. Set the key signature to C major and the time signature to 4/4. Ensure you have a piano staff. Using the note entry mode, enter the following melody in the right hand: Measure 1 consists of C4, E4, G4, C5; Measure 2 consists of B3, B3, A3, G3; Measure 3 consists of F3, F3, E3, D3; Measure 4 consists of C4, C4, B3, A3. Add a fermata on the last note and a crescendo from the first to the last note. Save your work as `SimpleMelody.mscz` or `SimpleMelody.musx` depending on the software.

### Exercise 1b: Exporting the Score
Export the score to MIDI. In MuseScore, go to `File > Export > Export as MIDI`. In Finale, go to `File > Export > MIDI File`. Import the MIDI file into your DAW and use a piano instrument to play back the MIDI file. Verify that the notes, dynamics, and articulations are correct.

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise 2a: Varying Time Signatures
Load `SimpleMelody.mscz` or `SimpleMelody.musx` in your notation software. Change the time signature from 4/4 to 3/4. Modify the rhythm of the melody to fit the new time signature, for example, change the quarter notes to dotted quarter notes followed by eighth notes. Export the new score as MIDI and play it back in your DAW to verify the changes. Create a graph comparing the duration of the original and modified melodies. Use a spreadsheet tool to plot the total duration of each measure in both time signatures.

### Exercise 2b: Varying Key Signatures
Load `SimpleMelody.mscz` or `SimpleMelody.musx` in your notation software. Change the key signature from C major to G major. Transpose the melody up by a perfect fifth. Export the new score as MIDI and play it back in your DAW to verify the changes. Create a graph comparing the pitch of the original and transposed melodies. Use a spreadsheet tool to plot the frequency of each note in both key signatures.

## Exercise 3: Fault Injection & Stress Testing

### Exercise 3a: Inducing Boundary Failures
Load `SimpleMelody.mscz` or `SimpleMelody.musx` in your notation software. Enter a note that is out of the range of a standard piano staff, such as C7. Export the score as MIDI and play it back in your DAW. Observe how the out-of-range note is handled. Note any errors or warnings in the notation software and the DAW. Determine how the software handles the out-of-range note. Remove the out-of-range note and verify that the score plays back correctly.

### Exercise 3b: Stress Testing with Complex Scores
Add multiple staves, instruments, and complex rhythms to your score. Export the complex score as MIDI and play it back in your DAW. Observe the performance of the notation software and the DAW. Note any lag, crashes, or other issues. Simplify the score by reducing the number of staves, instruments, or rhythms. Re-export and play back the score to verify improvements. Create a graph comparing the performance of the original and optimized scores. Use a spreadsheet tool to plot the response time or memory usage of each score.

## Practical Cheat Sheet & Quick Reference

### Commands and Parameters
- **MuseScore:**
  - `File > Export > Export as MIDI`
  - `File > Save As`
- **Finale:**
  - `File > Export > MIDI File`
  - `File > Save As`
- **DAW:**
  - Import MIDI file: `File > Import > MIDI`
  - Play back MIDI file: `Play` button
- **Graphing Tool:**
  - Create a new spreadsheet: `File > New`
  - Plot data: `Insert > Chart`

### Formulas and Verification Checks
- **Time Signature Change:**
  - Original duration: \( \text{Measure} \times \text{Quarter Note Duration} \)
  - New duration: \( \text{Measure} \times \text{New Quarter Note Duration} \)
- **Key Signature Change:**
  - Original frequency: \( f_n = f_0 \cdot 2^{n/12} \)
  - New frequency: \( f_n = f_0 \cdot 2^{(n+7)/12} \) (for transposing up a perfect fifth)

By completing these exercises, you will have a solid understanding of how to implement, configure, and troubleshoot musical notation systems. This knowledge will be invaluable in your compositional and performance practices.
