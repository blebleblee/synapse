# Operational Verification Labs: Audio Engineering

## Objective & Lab Setup

This lab aims to provide hands-on experience with fundamental audio engineering concepts, including digital signal processing (DSP), audio synthesis, and audio analysis. Utilizing the Audacity audio editing software for basic audio manipulation, the SuperCollider programming environment for synthesis and DSP, and the FFTW library for fast Fourier transforms, participants will gain practical skills in these areas. Ensure that the following tools are installed on your system before proceeding:

Audacity is a free, open-source audio editor. SuperCollider is a platform for audio synthesis and algorithmic composition. FFTW is a C subroutine library for computing the discrete Fourier transform (DFT) in one or more dimensions.

## Exercise 1: Foundational Practical Implementation

### Step-by-Step Runnable Exercise Demonstrating the Core Concept

#### Part A: Basic Audio Editing with Audacity

Open Audacity and create a new project. Import an audio file by selecting `File > Import > Audio...` and choosing a WAV or AIFF file. Select a portion of the audio by clicking and dragging over the waveform. Apply an effect to the selected portion by going to `Effect > Echo...`. Set the delay time to 500 ms, feedback to 0.5, and mix to 0.5, then click `OK`. Export the modified audio by selecting `File > Export > Export as WAV...` and saving the file to your desired location.

#### Part B: Basic Synthesis with SuperCollider

Open SuperCollider and ensure the server is booted by evaluating the following code:

```supercollider
s.boot;
```

Create a simple sine wave synthesizer by evaluating the following code:

```supercollider
(
SinOsc.ar(440, 0, 0.5).play;
)
```

Stop the synthesizer by evaluating the following code:

```supercollider
s.allNodesDo({ |node| node.free });
```

Create a more complex synthesizer with an ADSR envelope by evaluating the following code:

```supercollider
(
{
    var env = EnvGen.kr(Env.adsr(0.1, 0.5, 0.3, 1), Gate.kr(1, 1));
    SinOsc.ar(440, 0, env * 0.5)
}.play;
)
```

## Exercise 2: Parameter Variation & Empirical Analysis

### Testing Different Configurations, Measuring Outputs, and Graphing Responses

#### Part A: Audacity Parameter Variation

Import the same audio file used in Exercise 1. Apply the Echo effect with varying parameters: delay time of 200 ms, 500 ms, and 800 ms; feedback of 0.3, 0.5, and 0.7; and mix of 0.3, 0.5, and 0.7. Export each configuration as a separate WAV file. Analyze the differences in the exported files by listening to them and noting any changes in the echo characteristics.

#### Part B: SuperCollider Parameter Variation

Create a synthesizer with adjustable parameters by evaluating the following code:

```supercollider
(
{
    var freq = 440, amp = 0.5, attack = 0.1, decay = 0.5, sustain = 0.3, release = 1;
    var env = EnvGen.kr(Env.adsr(attack, decay, sustain, release), Gate.kr(1, 1));
    SinOsc.ar(freq, 0, env * amp)
}.play;
)
```

Vary the parameters and observe the changes in the synthesized sound: frequency of 220 Hz, 440 Hz, and 880 Hz; amplitude of 0.2, 0.5, and 0.8; attack of 0.05, 0.1, and 0.2; decay of 0.4, 0.5, and 0.6; sustain of 0.2, 0.3, and 0.4; and release of 0.8, 1.0, and 1.2. Record the output of each configuration using Audacity and compare the waveforms.

## Exercise 3: Fault Injection & Stress Testing

### Inducing Boundary Failures, Analyzing Error States, and Verifying Recovery

#### Part A: Audacity Fault Injection

Import the same audio file used in Exercise 1. Induce a fault by attempting to apply an effect with invalid parameters: go to `Effect > Echo...` and set the delay time to -100 ms. Note the error message. Recover from the fault by correcting the parameters and applying the effect again with valid settings.

#### Part B: SuperCollider Fault Injection

Create a synthesizer with invalid parameters by evaluating the following code:

```supercollider
(
{
    var freq = -100, amp = 2.0, attack = -0.1, decay = 1.5, sustain = 1.2, release = -0.5;
    var env = EnvGen.kr(Env.adsr(attack, decay, sustain, release), Gate.kr(1, 1));
    SinOsc.ar(freq, 0, env * amp)
}.play;
)
```

Analyze the error states and correct the parameters: ensure frequency is positive; ensure amplitude is between 0 and 1; and ensure attack, decay, sustain, and release are non-negative. Re-evaluate the corrected code and verify that the synthesizer plays without errors.

## Practical Cheat Sheet & Quick Reference

### Essential Commands, Parameters, Formulas, and Verification Checks

#### Audacity Commands

- **Import Audio**: `File > Import > Audio...`
- **Export Audio**: `File > Export > Export as WAV...`
- **Apply Effect**: `Effect > [Effect Name]...`
- **Select Portion**: Click and drag over the waveform.

#### SuperCollider Commands

- **Boot Server**: `s.boot;`
- **Stop All Nodes**: `s.allNodesDo({ |node| node.free });`
- **Play Synthesizer**: `{ [Synth Code] }.play;`

#### FFTW Parameters

- **Create Plan**: `fftw_plan_dft_1d(n, in, out, FFTW_FORWARD, FFTW_ESTIMATE);`
- **Execute Plan**: `fftw_execute(plan);`
- **Destroy Plan**: `fftw_destroy_plan(plan);`

#### Verification Checks

- **Audacity**: Ensure the audio file imports and exports correctly. Verify that effects are applied without errors.
- **SuperCollider**: Ensure the synthesizer plays without errors. Verify that parameter variations produce expected changes in sound.
- **FFTW**: Ensure the plan is created and executed without errors. Verify that the output matches expected frequency domain representation.
