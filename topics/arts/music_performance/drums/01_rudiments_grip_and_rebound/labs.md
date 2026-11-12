# Operational Verification Labs: 01 Rudiments Grip And Rebound

## Objective & Lab Setup

### Required Tools & Environments

To conduct the exercises in this lab, you will need a digital audio workstation (DAW) such as Ableton Live, Logic Pro, or FL Studio, a drum simulator plugin like Toontrack's EZdrummer, Addictive Drums, or Superior Drummer, a MIDI keyboard or drum pad for input, and a pair of drumsticks or practice pads for physical practice.

### Lab Setup Instructions

Launch your DAW and create a new project. Install and authorize your drum simulator plugin. Create a new MIDI track and assign it to the drum simulator plugin. Set up your MIDI keyboard or drum pad to send MIDI signals to the DAW. Finally, connect your drumsticks or practice pads to a drum pad or practice surface.

## Exercise 1: Foundational Practical Implementation

### Exercise: Basic Rudimental Groove

Open the drum simulator plugin and select a basic drum kit. Create a new MIDI track and assign it to the drum simulator plugin. Set the time signature to 4/4 and the tempo to 120 BPM. Create a basic rudimental groove by playing a single stroke roll (R-L-R-L) on the snare drum, followed by a double stroke roll (R-L-R-L-R-L) on the snare drum. Repeat the same pattern on the bass drum. Record the groove and play it back to verify the basic rudimental pattern.

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise: Rudimental Groove with Parameter Variation

Open the drum simulator plugin and select a basic drum kit. Create a new MIDI track and assign it to the drum simulator plugin. Set the time signature to 4/4 and the tempo to 120 BPM. Create a rudimental groove by playing a single stroke roll (R-L-R-L) on the snare drum with a note length of 16th notes, followed by a double stroke roll (R-L-R-L-R-L) on the snare drum with a note length of 16th notes. Repeat the same pattern on the bass drum. Vary the snare drum note length to 8th, 16th, and 32nd notes, and the bass drum note length to 8th, 16th, and 32nd notes. Adjust the snare drum velocity from 50% to 100% and the bass drum velocity from 50% to 100%. Record the effects of each variation. Analyze the results and graph the responses using the DAW's built-in analysis tools or a third-party plugin.

## Exercise 3: Fault Injection & Stress Testing

### Exercise: Rudimental Groove with Fault Injection

Open the drum simulator plugin and select a basic drum kit. Create a new MIDI track and assign it to the drum simulator plugin. Set the time signature to 4/4 and the tempo to 120 BPM. Create a rudimental groove by playing a single stroke roll (R-L-R-L) on the snare drum, followed by a double stroke roll (R-L-R-L-R-L) on the snare drum. Repeat the same pattern on the bass drum. Inject the following faults: set the snare drum note length to 0 (silence), set the bass drum note length to 0 (silence), set the snare drum velocity to 0 (silence), set the bass drum velocity to 0 (silence), change the time signature to 3/4, and change the tempo to 180 BPM. Record the effects of each fault. Analyze the results and verify the recovery of the rudimental groove.

## Practical Cheat Sheet & Quick Reference

| Command        | Parameter                      | Formula            | Verification Check                         |
|----------------|--------------------------------|--------------------|--------------------------------------------|
| `set-note-length` | snare drum note length       | 16th notes         | Verify snare drum note length is 16th notes  |
| `set-velocity`  | snare drum velocity          | 50-100%            | Verify snare drum velocity is 50-100%      |
| `inject-fault`  | snare drum note length set to 0 | Silence            | Verify snare drum is silent                |
| `inject-fault`  | bass drum note length set to 0 | Silence            | Verify bass drum is silent                 |
| `inject-fault`  | time signature changed to 3/4  | Verify time signature is 3/4                 |
| `inject-fault`  | tempo changed to 180 BPM       | Verify tempo is 180 BPM                      |

Note: The above cheat sheet serves as a quick reference for the practitioner to verify their understanding of the concepts and exercises.
