# Operational Verification Labs: Audio Effects

## Objective & Lab Setup

This laboratory aims to provide hands-on experience with implementing, configuring, and analyzing audio effects in a music production environment. Utilizing the Audacity audio editor for basic effects and the JUCE framework for advanced digital signal processing (DSP) programming, participants will explore various audio effects and their parameters. Ensure the following tools are installed on your system:

- **Audacity**: A free, open-source audio editor and recorder.
- **JUCE**: A C++ framework for building cross-platform audio applications.
- **Python**: For data analysis and plotting.
- **Matplotlib**: A plotting library for Python.
- **Numpy**: A library for numerical computations in Python.

## Exercise 1: Foundational Practical Implementation

### Delay Effect in Audacity

Open Audacity and import a sample audio file. Select a portion of the audio track where you wish to apply the delay effect. Navigate to the **Effect** menu and select **Delay**. In the Delay settings, configure the parameters as follows:

- **Delay Time**: 500 milliseconds.
- **Feedback**: 30%.
- **Dry/Wet Mix**: 50%.

Click **OK** to apply the effect. Listen to the modified audio and observe the delay effect.

### Reverb Effect in Audacity

Select a portion of the audio track where you want to apply the reverb effect. Navigate to the **Effect** menu and select **Reverb**. In the Reverb settings, configure the parameters as follows:

- **Room Size**: 0.5.
- **Damping**: 0.5.
- **Wet Gain**: 0.5.
- **Dry Gain**: 0.5.
- **Width**: 1.0.
- **Pre-delay**: 0.0.

Click **OK** to apply the effect. Listen to the modified audio and observe the reverb effect.

### Chorus Effect in Audacity

Select a portion of the audio track where you want to apply the chorus effect. Navigate to the **Effect** menu and select **Chorus**. In the Chorus settings, configure the parameters as follows:

- **Depth**: 0.5.
- **Rate**: 0.5.
- **Wet Gain**: 0.5.
- **Dry Gain**: 0.5.
- **Feedback**: 0.25.
- **Delay**: 0.01.

Click **OK** to apply the effect. Listen to the modified audio and observe the chorus effect.

## Exercise 2: Parameter Variation & Empirical Analysis

### Delay Effect Parameter Variation

Repeat the delay effect implementation with different delay times: 200ms, 500ms, and 1000ms. Record the perceived changes in audio quality and the perceived depth of the delay effect. Plot the results using Python and Matplotlib with the following code snippet:

```python
import matplotlib.pyplot as plt

delay_times = [200, 500, 1000]
perceived_depth = [3, 5, 7]  # Example data

plt.plot(delay_times, perceived_depth, marker='o')
plt.title('Perceived Depth of Delay Effect')
plt.xlabel('Delay Time (ms)')
plt.ylabel('Perceived Depth')
plt.grid(True)
plt.show()
```

### Reverb Effect Parameter Variation

Repeat the reverb effect implementation with different room sizes: 0.3, 0.5, and 0.7. Record the perceived changes in audio quality and the perceived spaciousness of the reverb effect. Plot the results using Python and Matplotlib with the following code snippet:

```python
room_sizes = [0.3, 0.5, 0.7]
perceived_spaciousness = [2, 5, 8]  # Example data

plt.plot(room_sizes, perceived_spaciousness, marker='o')
plt.title('Perceived Spaciousness of Reverb Effect')
plt.xlabel('Room Size')
plt.ylabel('Perceived Spaciousness')
plt.grid(True)
plt.show()
```

### Chorus Effect Parameter Variation

Repeat the chorus effect implementation with different depths: 0.3, 0.5, and 0.7. Record the perceived changes in audio quality and the perceived richness of the chorus effect. Plot the results using Python and Matplotlib with the following code snippet:

```python
depths = [0.3, 0.5, 0.7]
perceived_richness = [2, 5, 8]  # Example data

plt.plot(depths, perceived_richness, marker='o')
plt.title('Perceived Richness of Chorus Effect')
plt.xlabel('Depth')
plt.ylabel('Perceived Richness')
plt.grid(True)
plt.show()
```

## Exercise 3: Fault Injection & Stress Testing

### Delay Effect Fault Injection

Repeat the delay effect implementation with an extremely high delay time of 5000ms and observe the audio output for any artifacts or issues. If supported by the software, repeat the implementation with a negative delay time (e.g., -500ms) and observe the audio output for any artifacts or issues.

### Reverb Effect Fault Injection

Repeat the reverb effect implementation with an extremely high room size of 1.5 and observe the audio output for any artifacts or issues. If supported by the software, repeat the implementation with a negative room size (e.g., -0.5) and observe the audio output for any artifacts or issues.

### Chorus Effect Fault Injection

Repeat the chorus effect implementation with an extremely high depth of 1.5 and observe the audio output for any artifacts or issues. If supported by the software, repeat the implementation with a negative depth (e.g., -0.5) and observe the audio output for any artifacts or issues.

## Practical Cheat Sheet & Quick Reference

### Audacity Commands

- **Import Audio**: File > Import > Audio
- **Apply Delay**: Effect > Delay
- **Apply Reverb**: Effect > Reverb
- **Apply Chorus**: Effect > Chorus

### JUCE Framework

- **Create a New Project**: Use Projucer to create a new audio plugin project.
- **Compile and Run**: Use the Projucer or your preferred IDE to compile and run the project.

### Python Libraries

- **Matplotlib**: `pip install matplotlib`
- **Numpy**: `pip install numpy`

### Parameter Reference Tables

#### Delay Effect Parameters

| Parameter     | Description                                                   |
|---------------|---------------------------------------------------------------|
| Delay Time    | Time delay between the original and the echoed signal.        |
| Feedback      | Amount of the output signal that is fed back into the delay line. |
| Dry/Wet Mix   | Ratio of the original signal to the processed signal.         |

#### Reverb Effect Parameters

| Parameter     | Description                                                   |
|---------------|---------------------------------------------------------------|
| Room Size     | Size of the simulated room.                                   |
| Damping       | Amount of high-frequency damping.                             |
| Wet Gain      | Gain of the processed signal.                                 |
| Dry Gain      | Gain of the original signal.                                  |
| Width         | Width of the stereo image.                                    |
| Pre-delay     | Time delay before the reverb starts.                          |

#### Chorus Effect Parameters

| Parameter     | Description                                                   |
|---------------|---------------------------------------------------------------|
| Depth         | Depth of the modulation.                                      |
| Rate          | Rate of the modulation.                                       |
| Wet Gain      | Gain of the processed signal.                                 |
| Dry Gain      | Gain of the original signal.                                  |
| Feedback      | Amount of the output signal that is fed back into the chorus. |
| Delay         | Delay time of the chorus effect.                              |
