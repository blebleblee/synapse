# Operational Verification Labs: Organ

## Objective & Lab Setup

This laboratory aims to provide hands-on experience with the operational verification of an organ, encompassing foundational practical implementation, parameter variation and empirical analysis, and fault injection and stress testing. Utilizing a digital organ simulator such as Hauptwerk, which is widely recognized in the field of organ performance and simulation, participants will gain practical insights into the verification process.

### Required Domain-Specific Tools, Environments, Packages, or Simulators

The lab requires the following tools:
- **Hauptwerk**: A digital organ simulator offering a comprehensive environment for simulating and verifying organ performance.
- **Digital Audio Workstation (DAW)**: Such as Ableton Live or Logic Pro, for recording and analyzing the output of the organ.
- **Graphing Software**: Such as Microsoft Excel or MATLAB, for plotting and analyzing empirical data.

## Exercise 1: Foundational Practical Implementation

### Step-by-Step Runnable Exercise Demonstrating the Core Concept

To begin, install Hauptwerk on your computer by following the official installation guide provided by the manufacturer. Next, download and install a sample organ library from the Hauptwerk website or another reputable source. Launch Hauptwerk and load the sample organ library. Configure the MIDI input settings to connect your MIDI keyboard or organ console to Hauptwerk. Play a simple piece of music using your MIDI keyboard or organ console, and record the output using your DAW to analyze the sound characteristics. Play a C major scale to verify that each note is produced correctly, and check the MIDI output to ensure that the correct MIDI messages are being sent.

## Exercise 2: Parameter Variation & Empirical Analysis

### Testing Different Configurations, Measuring Outputs, and Graphing Responses

Change the stop settings in Hauptwerk to vary the tonal color of the organ, recording the output for each configuration. Use the DAW to measure the fundamental frequency and harmonic content of each note, analyzing the sound characteristics for each stop configuration. Plot the fundamental frequency and harmonic content for each stop configuration using graphing software, and compare the sound characteristics of different stop configurations.

## Exercise 3: Fault Injection & Stress Testing

### Inducing Boundary Failures, Analyzing Error States, and Verifying Recovery

Disconnect the MIDI input to simulate a hardware failure, and load a corrupted organ library to simulate a software failure. Observe the behavior of Hauptwerk when the MIDI input is disconnected and when a corrupted organ library is loaded. Reconnect the MIDI input and verify that Hauptwerk functions correctly, and reload a valid organ library to ensure that Hauptwerk functions correctly after inducing and recovering from faults.

## Practical Cheat Sheet & Quick Reference

### Essential Commands, Parameters, Formulas, and Verification Checks

- **Hauptwerk Commands**:
  - Load a new organ library.
  - Set up MIDI input settings.
  - Play a note using the MIDI keyboard or organ console.
  - Record the output using the DAW.

- **DAW Commands**:
  - Start recording the output.
  - Stop recording the output.
  - Analyze the fundamental frequency of a note.
  - Analyze the harmonic content of a note.

- **Graphing Software Commands**:
  - Plot the fundamental frequency and harmonic content.
  - Compare the sound characteristics of different stop configurations.

- **Verification Checks**:
  - Ensure each note is produced correctly.
  - Confirm that the correct MIDI messages are being sent.
  - Verify that Hauptwerk functions correctly after inducing and recovering from faults.
