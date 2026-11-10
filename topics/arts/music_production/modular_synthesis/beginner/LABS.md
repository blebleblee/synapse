# Beginner Hands-On Lab: Modular Synthesis
## Objective & Prerequisites
### Objective
The objective of this lab is to set up a basic modular synthesis environment, execute your first commands, and understand the basic state of your setup. By the end of this lab, you should be able to create a simple modular synthesis patch and observe its output.

### Prerequisites
- Basic understanding of electronic music and synthesis.
- Access to a computer with internet connectivity.
- Installation of a modular synthesis software (e.g., VCV Rack, Reaktor, or any other modular synthesis software of your choice).

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
### Instructions
1. **Download and Install Modular Synthesis Software:**
   - Visit the official website of the modular synthesis software you have chosen (e.g., [VCV Rack](https://vcvrack.com/)).
   - Download the appropriate version for your operating system (Windows, macOS, or Linux).
   - Follow the installation instructions provided on the website.

2. **Launch the Software:**
   - Open the installed software on your computer.
   - Verify that the software launches without any errors.

### Expected Outcome
- The modular synthesis software should open successfully, displaying its main interface.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
### Instructions
1. **Create a New Patch:**
   - Open the software and create a new patch by selecting `File` > `New` or using the shortcut `Ctrl+N` (Windows/Linux) or `Cmd+N` (macOS).

2. **Add a Voltage Controlled Oscillator (VCO):**
   - From the `Modules` panel, find and drag a `VCO` module into the patch area.
   - Position the `VCO` module in the top-left corner of the patch area.

3. **Add an Audio Output:**
   - From the `Modules` panel, find and drag an `Audio Output` module into the patch area.
   - Position the `Audio Output` module in the top-right corner of the patch area.

4. **Connect the VCO to the Audio Output:**
   - Click on the output jack (usually labeled `OUT`) of the `VCO` module.
   - Drag a cable to the input jack (usually labeled `IN`) of the `Audio Output` module.
   - Release the mouse button to complete the connection.

5. **Start Audio Output:**
   - Click on the `Play` button in the toolbar to start audio output.
   - You should hear a sound coming from your speakers or headphones.

### Expected Outcome
- You should hear a continuous tone coming from the speakers or headphones, indicating that the `VCO` is generating audio and sending it to the `Audio Output`.

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
### Instructions
1. **Check Module Parameters:**
   - Click on the `VCO` module to select it.
   - Observe the parameters of the `VCO` module in the `Parameters` panel.
   - Adjust the `Frequency` parameter to change the pitch of the tone.

2. **Observe Audio Output:**
   - Listen to the audio output and notice how changing the `Frequency` parameter affects the pitch of the tone.

### Expected Outcome
- You should be able to see the parameters of the `VCO` module and hear the pitch change as you adjust the `Frequency` parameter.

## Challenge Exercise (Simple self-test for beginners)
### Instructions
1. **Add a Low-Pass Filter (LPF):**
   - From the `Modules` panel, find and drag a `Low-Pass Filter` module into the patch area.
   - Position the `LPF` module between the `VCO` and the `Audio Output`.

2. **Connect the LPF:**
   - Click on the output jack of the `VCO` module.
   - Drag a cable to the input jack of the `LPF` module.
   - Click on the output jack of the `LPF` module.
   - Drag a cable to the input jack of the `Audio Output` module.

3. **Adjust LPF Parameters:**
   - Click on the `LPF` module to select it.
   - Adjust the `Cutoff` parameter to change the cutoff frequency of the filter.
   - Adjust the `Resonance` parameter to change the resonance of the filter.

4. **Observe Audio Output:**
   - Listen to the audio output and notice how changing the `Cutoff` and `Resonance` parameters affects the tone.

### Expected Outcome
- You should be able to hear the effect of the `Low-Pass Filter` on the tone, with changes in the cutoff frequency and resonance altering the sound.
