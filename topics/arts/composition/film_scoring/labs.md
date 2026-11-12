# Operational Verification Labs: Film Scoring

## Objective & Lab Setup

This laboratory aims to provide hands-on experience in the practical implementation, parameter variation, and fault injection of film scoring techniques. The lab will utilize the following tools and environments:

- **Digital Audio Workstation (DAW):** Ableton Live Suite
- **MIDI Controller:** Akai MPK Mini MKII
- **Virtual Instruments:** Native Instruments Komplete Ultimate
- **Audio Interface:** Focusrite Scarlett 2i2
- **Software for Graphing and Analysis:** Microsoft Excel or Google Sheets

Ensure that all software is installed and properly configured before beginning the exercises. Familiarize yourself with the basic operation of the DAW and MIDI controller.

## Exercise 1: Foundational Practical Implementation

### Setting Up the DAW

Launch Ableton Live Suite and create a new project. Create a new MIDI track by clicking on the "+" icon in the Session view and selecting "MIDI Track." Select a virtual instrument by clicking on the instrument icon in the MIDI track and choosing a string section from Native Instruments Komplete Ultimate. Connect the MIDI controller to your computer via USB and ensure that Ableton Live recognizes the controller by checking the "MIDI From" and "MIDI To" settings in the Preferences under the Link/MIDI tab. Map the MIDI controller to the virtual instrument by selecting the MIDI track and choosing your MIDI controller as the input source from the "MIDI From" dropdown menu.

### Composing a Basic Film Score

Enter Session view and select the MIDI clip slot in the first measure of the MIDI track. Record a simple melody using the MIDI controller. Play a four-bar theme in C major, using quarter notes and half notes. For example, play the following notes: Measure 1: C4, E4, G4, C5; Measure 2: E4, G4, B4, E5; Measure 3: G4, B4, D5, G5; Measure 4: B4, D5, F5, B5. Enter Arrangement view and extend the MIDI clip to four bars. Add a second MIDI track for the harmony by selecting a different string section or a piano from the Komplete Ultimate library. Record a chord progression to accompany the melody using the following chords: Measure 1: Cmaj7; Measure 2: G7; Measure 3: Am7; Measure 4: Fmaj7. Adjust the volume and panning of each track to create a balanced sound using the mixer to set the levels and pan positions.

### Adding Orchestration and Dynamics

Add a third MIDI track for the rhythm section by choosing a drum kit from the Komplete Ultimate library. Record a simple drum pattern to provide a rhythmic foundation using a basic 4/4 beat with kick, snare, and hi-hat. Add a fourth MIDI track for additional orchestration by selecting a brass section or woodwinds from the Komplete Ultimate library. Record a countermelody or additional harmony to enrich the texture by playing a simple four-bar theme in the brass or woodwinds section. Adjust the dynamics of each track to create a sense of tension and release using automation to vary the volume and panning over time.

## Exercise 2: Parameter Variation & Empirical Analysis

### Testing Different Configurations, Measuring Outputs, and Graphing Responses

#### Varying Instrumentation and Timbre

Experiment with different virtual instruments for each track by replacing the string section with a different orchestral instrument or a synth pad. Measure the impact on the overall sound and emotional tone of the film score by listening to the changes and noting any differences in timbre, resonance, and texture. Graph the responses in a spreadsheet by creating a table with columns for instrument type, timbre description, and emotional impact. Use a scale from 1 to 5 to rate the emotional impact.

#### Adjusting Dynamics and Panning

Vary the dynamics of each track by adjusting the volume automation to create a gradual crescendo and decrescendo in the melody and harmony tracks. Measure the impact on the emotional tension and release by listening to the changes and noting any differences in intensity and mood. Graph the responses in a spreadsheet by creating a table with columns for dynamic level, emotional tension, and mood description. Use a scale from 1 to 5 to rate the emotional tension and mood.

#### Modulating Key and Chord Progression

Experiment with different key signatures and chord progressions by modulating to a related key (e.g., G major) and changing the chord progression accordingly. Measure the impact on the overall sound and emotional tone of the film score by listening to the changes and noting any differences in harmonic tension and resolution. Graph the responses in a spreadsheet by creating a table with columns for key signature, chord progression, and emotional impact. Use a scale from 1 to 5 to rate the emotional impact.

## Exercise 3: Fault Injection & Stress Testing

### Inducing Boundary Failures, Analyzing Error States, and Verifying Recovery

#### Introducing Faults in Instrumentation

Introduce a fault in the instrumentation by selecting an incompatible or glitchy virtual instrument, such as a broken or malfunctioning preset. Analyze the error state and listen to the resulting sound, noting any artifacts, distortion, or unexpected behavior. Verify recovery by replacing the faulty instrument with a working preset and listening to the corrected sound to ensure that the emotional tone and texture are restored.

#### Introducing Faults in Dynamics and Panning

Introduce a fault in the dynamics and panning by setting extreme values, such as the volume to 0 dB or the panning to 100% left or right. Analyze the error state and listen to the resulting sound, noting any loss of balance, silence, or phase cancellation. Verify recovery by setting appropriate values for volume and panning and listening to the corrected sound to ensure that the overall balance and texture are restored.

#### Introducing Faults in Key and Chord Progression

Introduce a fault in the key and chord progression by using unrelated or dissonant chords, such as a random chord progression that does not follow tonal rules. Analyze the error state and listen to the resulting sound, noting any harmonic dissonance, tension, or lack of resolution. Verify recovery by using a related or consonant chord progression and listening to the corrected sound to ensure that the harmonic tension and resolution are restored.

## Practical Cheat Sheet & Quick Reference

### Essential Commands, Parameters, Formulas, and Verification Checks

| Command/Parameter | Description | Example |
|-------------------|-------------|---------|
| **MIDI Track** | Creates a new MIDI track for recording and playing MIDI data. | Click "+" icon in Session view, select "MIDI Track". |
