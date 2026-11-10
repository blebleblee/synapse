# Beginner Technical Lesson: Modular Synthesis
## 1. Core Mechanics & Basic Principles
Modular synthesis is a method of creating electronic music using modular synthesizers. These synthesizers consist of individual modules that perform specific functions, such as generating sound, processing it, and controlling other modules. The modules are connected together using patch cords to create a custom signal flow, allowing for endless creative possibilities.

At a fundamental level, modular synthesis involves the following core mechanics:
- **Voltage Control:** Most modular synthesizers use voltage control to manipulate parameters. A control voltage (CV) of 1V typically corresponds to one octave in pitch, and 1V per volt (1V/V) is a common standard.
- **Signal Flow:** Signals travel from one module to another through patch cords. Each module processes the incoming signal in some way, such as amplifying it, filtering it, or modulating it.
- **Modulation:** Modulation is the process of varying one parameter with another. For example, you can modulate the pitch of an oscillator with an LFO (Low-Frequency Oscillator) to create vibrato.

## 2. Step-by-Step Component Breakdown
Here are some of the basic components you'll encounter in modular synthesis:

### Oscillator (VCO)
- **Function:** Generates sound waves (sine, square, sawtooth, triangle).
- **Controls:** Frequency (pitch), waveform selection.

### Voltage Controlled Amplifier (VCA)
- **Function:** Amplifies or attenuates the incoming signal.
- **Controls:** Gain (volume), CV input for modulation.

### Low-Frequency Oscillator (LFO)
- **Function:** Generates slow, repeating signals used for modulation.
- **Controls:** Frequency, waveform selection.

### Voltage Controlled Filter (VCF)
- **Function:** Filters the incoming signal to remove certain frequencies.
- **Controls:** Cutoff frequency, resonance, CV input for modulation.

### Envelope Generator (EG)
- **Function:** Produces control voltages that change over time, typically used to control the amplitude of a sound.
- **Controls:** Attack, decay, sustain, release (ADSR).

### Mixer
- **Function:** Combines multiple signals into a single output.
- **Controls:** Channel levels, panning.

### Power Supply
- **Function:** Provides power to all modules.

### Patch Cords
- **Function:** Connects modules together to create a signal flow.

## 3. First Working Implementation
Let's create a simple patch that generates a sine wave, modulates its pitch with an LFO, and controls its amplitude with an envelope generator.

### Patch Configuration:
1. **Oscillator (VCO):**
   - Set waveform to sine.
   - Connect VCO output to VCA input.

2. **Low-Frequency Oscillator (LFO):**
   - Set waveform to triangle.
   - Set frequency to 2 Hz.
   - Connect LFO output to VCO pitch CV input.

3. **Envelope Generator (EG):**
   - Set ADSR values: Attack = 0.1s, Decay = 0.5s, Sustain = 0.5, Release = 1s.
   - Connect EG output to VCA gain CV input.

4. **Mixer:**
   - Connect VCA output to Mixer input.
   - Connect Mixer output to audio interface or headphones.

### Step-by-Step Instructions:
1. **Set up the Oscillator:**
   - Choose a sine wave.
   - Connect the VCO output to the VCA input.

2. **Set up the LFO:**
   - Choose a triangle wave.
   - Set the frequency to 2 Hz.
   - Connect the LFO output to the VCO pitch CV input.

3. **Set up the Envelope Generator:**
   - Set the ADSR values as specified.
   - Connect the EG output to the VCA gain CV input.

4. **Set up the Mixer:**
   - Connect the VCA output to the Mixer input.
   - Connect the Mixer output to your audio interface or headphones.

5. **Trigger the Envelope Generator:**
   - Use a keyboard gate or a trigger module to start the envelope.

### Expected Result:
You should hear a sine wave with a vibrato effect due to the LFO modulating the pitch, and the amplitude should follow the ADSR envelope.

## 4. What Can Go Wrong
Here are some common mistakes and how to spot them:

- **No sound:** Ensure all connections are secure and that the power supply is on.
- **No modulation:** Verify that the CV inputs are correctly connected and that the modulating signal is present.
- **Incorrect waveform:** Double-check the waveform selection on each module.
- **Envelope not triggering:** Make sure the trigger signal is properly connected and active.

## 5. Key Takeaways & Review Checklist
### Key Takeaways:
- Modular synthesis involves connecting individual modules to create a custom signal flow.
- Voltage control is used to manipulate parameters.
- Basic components include oscillators, VCAs, LFOs, VCFs, EGs, and mixers.

### Review Checklist:
- [ ] Set up the Oscillator with a sine wave and connect it to the VCA.
- [ ] Configure the LFO with a triangle wave at 2 Hz and connect it to the VCO pitch CV input.
- [ ] Set up the Envelope Generator with specified ADSR values and connect it to the VCA gain CV input.
- [ ] Connect the VCA output to the Mixer input and the Mixer output to your audio interface or headphones.
- [ ] Test the patch by triggering the Envelope Generator and listening for the expected sound.

By following these steps, you should have a basic understanding of modular synthesis and be able to create simple patches. As you gain more experience, you can explore more complex configurations and modules to expand your sound design capabilities.
