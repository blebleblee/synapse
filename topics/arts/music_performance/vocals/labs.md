# Operational Verification Labs: Vocals

## Objective & Lab Setup

This laboratory aims to provide hands-on experience in the practical implementation, parameter variation, and fault injection of vocal performance techniques. Utilizing a combination of audio recording software, vocal processing plugins, and digital audio workstations (DAWs) such as Ableton Live, FL Studio, or Pro Tools, participants will explore foundational and advanced vocal processing techniques. Additionally, tools like Audacity will be employed for basic audio editing and analysis, and a microphone with a preamp will be used for recording.

### Required Tools and Environment

The lab requires the following tools and environment setup:
- **Digital Audio Workstation (DAW):** Ableton Live, FL Studio, or Pro Tools.
- **Audio Recording Software:** Audacity.
- **Vocal Processing Plugins:** Reverb, Delay, Compressor, EQ, Pitch Correction (e.g., Autotune).
- **Microphone and Preamp:** Condenser microphone with a preamp.
- **Audio Interface:** USB or Thunderbolt audio interface.
- **Headphones or Speakers:** High-quality headphones or studio monitors.

## Exercise 1: Foundational Practical Implementation

### Recording a Vocal Take

To begin, set up the condenser microphone approximately 6-12 inches from your mouth, aiming for the center of the capsule. Ensure the microphone is placed in a quiet environment to minimize ambient noise. Connect the microphone to the preamp and then to the audio interface. Set the input level on the audio interface to a comfortable level, avoiding clipping. Open your DAW and create a new project. Insert an audio track and arm it for recording, setting the input to the microphone channel on the audio interface. Record a vocal take by singing a simple melody or phrase, such as "Do Re Mi Fa So La Ti Do," while maintaining a consistent volume and pitch. Stop recording after a few repetitions to capture variations in your performance. Playback the recorded vocal take and listen for any issues such as clipping, background noise, or inconsistent volume. Make adjustments to the microphone position or input level as necessary and record additional takes if needed.

### Basic Vocal Processing

Insert an EQ plugin on the vocal track and apply a high-pass filter to cut off frequencies below 100 Hz to reduce unwanted low-end rumble. Apply a low-pass filter to cut off frequencies above 10 kHz to reduce sibilance and hiss. Next, insert a compressor plugin on the vocal track. Set the threshold to -20 dB and the ratio to 4:1 to reduce dynamic range and even out the volume. Set the attack time to 20 ms and the release time to 200 ms to allow for natural-sounding compression. Insert a reverb plugin on the vocal track and set the decay time to 1.5 seconds and the mix to 30% to add a sense of space and depth. Adjust the pre-delay to 20 ms to create a more natural reverb effect. Insert a delay plugin on the vocal track and set the delay time to 600 ms and the feedback to 30% to create a subtle echo effect. Set the mix to 20% to blend the delay with the original vocal.

## Exercise 2: Parameter Variation & Empirical Analysis

### Varying EQ Settings

Vary the high-pass filter cutoff frequency from 80 Hz to 120 Hz in 10 Hz increments, recording the output for each setting and comparing the results. Note how the low-end rumble is reduced as the cutoff frequency increases. Vary the low-pass filter cutoff frequency from 8 kHz to 12 kHz in 1 kHz increments, recording the output for each setting and comparing the results. Note how the sibilance and hiss are reduced as the cutoff frequency decreases.

### Varying Compression Settings

Vary the threshold from -25 dB to -15 dB in 1 dB increments, recording the output for each setting and comparing the results. Note how the dynamic range is reduced as the threshold decreases. Vary the ratio from 2:1 to 8:1 in 1:1 increments, recording the output for each setting and comparing the results. Note how the compression becomes more aggressive as the ratio increases. Vary the attack time from 10 ms to 50 ms in 10 ms increments, recording the output for each setting and comparing the results. Note how the attack time affects the naturalness of the compression. Vary the release time from 100 ms to 500 ms in 100 ms increments, recording the output for each setting and comparing the results. Note how the release time affects the naturalness of the compression.

### Varying Reverb Settings

Vary the decay time from 1 second to 3 seconds in 0.5 second increments, recording the output for each setting and comparing the results. Note how the decay time affects the sense of space and depth. Vary the mix from 20% to 50% in 5% increments, recording the output for each setting and comparing the results. Note how the mix affects the balance between the original vocal and the reverb. Vary the pre-delay from 10 ms to 50 ms in 10 ms increments, recording the output for each setting and comparing the results. Note how the pre-delay affects the naturalness of the reverb.

### Varying Delay Settings

Vary the delay time from 500 ms to 1000 ms in 100 ms increments, recording the output for each setting and comparing the results. Note how the delay time affects the echo effect. Vary the feedback from 20% to 50% in 5% increments, recording the output for each setting and comparing the results. Note how the feedback affects the echo effect. Vary the mix from 10% to 30% in 5% increments, recording the output for each setting and comparing the results. Note how the mix affects the balance between the original vocal and the delay.

## Exercise 3: Fault Injection & Stress Testing

### Inducing Clipping

Record a vocal take with the microphone positioned too close to your mouth, causing clipping. Record the output and listen for the distortion caused by clipping. Use the waveform view in your DAW to identify the clipped sections and note the impact of clipping on the clarity and quality of the vocal. Apply a de-esser plugin to reduce sibilance and hiss, and use a noise gate plugin to remove unwanted noise. Record the output and compare it to the original clipped recording.

### Inducing Background Noise

Record a vocal take in a noisy environment, such as a room with air conditioning or traffic noise. Record the output and listen for the background noise. Use noise reduction tools in your DAW to minimize the noise, and record the output for comparison. Note the effectiveness of the noise reduction techniques on the overall quality of the vocal recording.
