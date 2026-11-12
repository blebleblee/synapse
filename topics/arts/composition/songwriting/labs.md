# Operational Verification Labs: Songwriting

## Objective & Lab Setup

### Objective
This lab aims to provide hands-on experience in the practical implementation, parameter variation, and fault injection of songwriting techniques. Through a series of exercises, you will learn to construct, analyze, and troubleshoot musical compositions using industry-standard tools and methodologies.

### Lab Setup
For this lab, you will need the following tools and environments:

- **Digital Audio Workstation (DAW):** Ableton Live, Logic Pro X, or FL Studio.
- **MIDI Controller:** Any MIDI keyboard or controller for input.
- **Virtual Instruments:** Native DAW instruments or third-party VST/AU plugins.
- **Audio Interface:** To connect your MIDI controller and headphones/speakers.
- **Graphing Software:** Excel, Google Sheets, or any other spreadsheet application for data analysis and visualization.

## Exercise 1: Foundational Practical Implementation

### Exercise Overview
In this exercise, you will create a basic song structure using a DAW. The song will consist of a verse, chorus, and bridge. You will use MIDI to input a simple melody and chord progression.

#### Step-by-Step Instructions

1. **Open Your DAW:**
   Launch your chosen DAW and create a new project.

2. **Set Up the Tempo and Time Signature:**
   Set the tempo to 120 BPM and the time signature to 4/4.

3. **Create a New MIDI Track:**
   Insert a new MIDI track and select a piano instrument.

4. **Input the Melody:**
   Use your MIDI controller to input a simple melody in the first measure. For example, play the notes C4, D4, E4, F4, G4, F4, E4, D4.

5. **Input the Chord Progression:**
   In the second measure, input a simple chord progression. For example, play the chords Cmaj7, G7, Am7, Fmaj7.

6. **Repeat the Melody and Chord Progression:**
   Repeat the melody and chord progression for the first verse (8 measures).

7. **Create the Chorus:**
   In the next 8 measures, create a chorus. Use a more prominent melody and a different chord progression. For example, play the melody C4, E4, G4, C5, G4, E4, C4, G4 and the chords Cmaj7, G7, Cmaj7, G7.

8. **Create the Bridge:**
   In the next 4 measures, create a bridge. Use a different melody and chord progression to contrast with the verse and chorus. For example, play the melody D4, F4, A4, D5, A4, F4, D4, A4 and the chords Am7, Fmaj7, Cmaj7, G7.

9. **Repeat the Chorus:**
   Repeat the chorus for the final 8 measures.

10. **Listen and Refine:**
    Play back the song and refine the melody and chord progressions as needed.

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise Overview
In this exercise, you will vary parameters such as tempo, key, and instrumentation to analyze their effects on the song's mood and structure.

#### Step-by-Step Instructions

1. **Vary the Tempo:**
   Change the tempo to 140 BPM and listen to the song. Note the difference in mood and energy. Change the tempo back to 120 BPM.

2. **Change the Key:**
   Transpose the song to the key of G major. Note the difference in timbre and emotional resonance. Transpose the song back to the key of C major.

3. **Change the Instrumentation:**
   Replace the piano with a different instrument, such as a guitar or synthesizer. Note the difference in texture and character. Replace the instrument back to the piano.

4. **Graph the Responses:**
   Create a spreadsheet to document your observations. Include columns for tempo, key, instrumentation, and your subjective assessment of mood and energy.

## Exercise 3: Fault Injection & Stress Testing

### Exercise Overview
In this exercise, you will introduce intentional errors to test the robustness of your song structure and composition.

#### Step-by-Step Instructions

1. **Introduce a Timing Error:**
   Introduce a rhythmic error in the melody, such as a syncopation or a skipped note. Listen to the song and note the effect on the structure and flow. Correct the rhythmic error.

2. **Introduce a Chord Progression Error:**
   Introduce a chord progression error, such as a non-diatonic chord or a chord substitution that doesn't resolve properly. Listen to the song and note the effect on the harmonic tension and resolution. Correct the chord progression error.

3. **Introduce an Instrumentation Error:**
   Introduce an instrumentation error, such as a clashing instrument or a poor balance between instruments. Listen to the song and note the effect on the overall texture and clarity. Correct the instrumentation error.

4. **Document the Error States:**
   Create a spreadsheet to document your observations. Include columns for the type of error, the effect on the song, and your steps to correct the error.

## Practical Cheat Sheet & Quick Reference

### Essential Commands and Parameters

- **DAW Commands:**
  - **Insert MIDI Track:** `Cmd+Shift+M` (Mac) or `Ctrl+Shift+M` (Windows)
  - **Transpose:** Use the transpose function in the MIDI editor.
  - **Change Tempo:** Use the tempo control in the transport section.

- **MIDI Controller Commands:**
  - **Input Notes:** Press keys on the MIDI controller.
  - **Change Octave:** Use the octave shift buttons on the MIDI controller.

- **Virtual Instrument Parameters:**
  - **Waveform:** Select the waveform type (saw, square, triangle) in the oscillator section.
  - **Filter Cutoff:** Adjust the cutoff frequency in the filter section.
  - **Envelope ADSR:** Set the attack, decay, sustain, and release times in the envelope section.

- **Formulas and Verification Checks:**
  - **Equal Temperament Ratio:** $f_n = f_0 \cdot 2^{n/12}$
  - **Harmonic Series:** $f_n = n \cdot f_0$
  - **Subjective Assessment:** Listen to the song and document your observations on mood, energy, and structure.
