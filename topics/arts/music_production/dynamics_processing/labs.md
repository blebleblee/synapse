# Operational Verification Labs: Dynamics Processing

## Objective & Lab Setup

The objective of this laboratory is to provide hands-on experience with dynamics processing in music production. Dynamics processing includes techniques such as compression, limiting, expansion, and gating, which are essential for controlling the dynamic range of audio signals. Through a series of exercises, you will learn to implement, configure, and analyze these processes using industry-standard digital audio workstation (DAW) software and plugins.

For this lab, you will need the following tools and software:
A DAW such as Ableton Live, Logic Pro X, or FL Studio.
A dynamics processing plugin (e.g., Waves CLA-76 Compressor, FabFilter Pro-C, or the built-in compressor in your DAW).
A sample audio file to process (e.g., a drum loop, vocal recording, or instrumental track).
A digital audio interface to monitor audio output (optional but recommended for better sound quality).
A computer with sufficient processing power to run the DAW and plugins smoothly.

## Exercise 1: Foundational Practical Implementation

In this exercise, you will implement basic dynamics processing on a sample audio file using a compressor plugin. You will learn to set up the compressor, adjust its parameters, and observe the effects on the audio signal.

Launch your DAW and create a new project. Import the sample audio file into a new track. Select the track with the sample audio and insert a compressor plugin by right-clicking on the track and choosing "Insert Plugin" or using the corresponding shortcut. Choose a compressor plugin from the list (e.g., Waves CLA-76 Compressor, FabFilter Pro-C).

Set the **Threshold** to -20 dB, which is the level above which the compressor will start reducing the gain. Set the **Ratio** to 4:1, meaning that for every 4 dB increase in input level above the threshold, the output level will only increase by 1 dB. Set the **Attack** time to 20 ms, the time it takes for the compressor to start reducing gain after the signal exceeds the threshold. Set the **Release** time to 100 ms, the time it takes for the compressor to stop reducing gain after the signal falls below the threshold. Set the **Make-up Gain** to 3 dB to compensate for the gain reduction applied by the compressor.

Play the sample audio file and listen to the compressed output. Observe the waveform and metering in the DAW to see the effect of the compressor on the dynamic range of the audio signal.

## Exercise 2: Parameter Variation & Empirical Analysis

In this exercise, you will vary the parameters of the compressor and analyze the resulting changes in the audio signal. You will measure the output level and observe the effects on the waveform and metering.

Increase the **Threshold** to -10 dB and play the sample audio file. Observe the waveform and metering, noting the increase in gain reduction and the overall level of the audio signal. Decrease the **Threshold** to -30 dB and play the sample audio file again. Observe the waveform and metering, noting the decrease in gain reduction and the overall level of the audio signal.

Set the **Threshold** back to -20 dB. Increase the **Ratio** to 8:1 and play the sample audio file. Observe the waveform and metering, noting the more aggressive gain reduction and the overall level of the audio signal. Decrease the **Ratio** to 2:1 and play the sample audio file. Observe the waveform and metering, noting the less aggressive gain reduction and the overall level of the audio signal.

Set the **Ratio** back to 4:1. Increase the **Attack** time to 50 ms and play the sample audio file. Observe the waveform and metering, noting the slower onset of gain reduction and the overall level of the audio signal. Decrease the **Attack** time to 10 ms and play the sample audio file. Observe the waveform and metering, noting the faster onset of gain reduction and the overall level of the audio signal. Increase the **Release** time to 200 ms and play the sample audio file. Observe the waveform and metering, noting the slower release of gain reduction and the overall level of the audio signal. Decrease the **Release** time to 50 ms and play the sample audio file. Observe the waveform and metering, noting the faster release of gain reduction and the overall level of the audio signal.

Use the metering and waveform displays in the DAW to graph the input and output levels of the audio signal. Create a table or chart to document the changes in gain reduction, attack, and release times, and their corresponding effects on the audio signal.

## Exercise 3: Fault Injection & Stress Testing

In this exercise, you will induce boundary failures and analyze the error states of the compressor. You will verify the recovery of the compressor under extreme conditions.

Set the **Threshold** to -40 dB and the **Ratio** to 10:1. Play the sample audio file and observe the waveform and metering, noting the extreme gain reduction and the potential distortion or pumping artifacts in the audio signal.

Set the **Attack** time to 1 ms and the **Release** time to 1 ms. Play the sample audio file and observe the waveform and metering, noting the rapid onset and release of gain reduction and the potential pumping artifacts in the audio signal.

Set the **Threshold** to -10 dB and the **Ratio** to 1:1. Play the sample audio file and observe the waveform and metering, noting the minimal gain reduction and the overall level of the audio signal.

Reset the compressor parameters to their default values. Play the sample audio file and observe the waveform and metering, verifying that the compressor has recovered to its normal state and that the audio signal is free of distortion or artifacts.

## Practical Cheat Sheet & Quick Reference

### Essential Commands and Parameters
- **Threshold**: The level above which the compressor starts reducing gain.
- **Ratio**: The ratio of input dB to output dB above the threshold.
- **Attack**: The time it takes for the compressor to start reducing gain after the signal exceeds the threshold.
- **Release**: The time it takes for the compressor to stop reducing gain after the signal falls below the threshold.
