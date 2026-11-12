# Operational Verification Labs: Acoustics

## Objective & Lab Setup

### Objective
This laboratory aims to provide hands-on experience with fundamental acoustics principles in music production. Through a series of exercises, you will explore the physical properties of sound waves, their interaction with different materials, and the effects of various acoustic phenomena on audio recordings. The lab utilizes tools such as Audacity for audio editing, Python with libraries like NumPy and SciPy for signal processing, and a simple acoustic simulation software like FDTD (Finite-Difference Time-Domain) to model sound wave propagation.

### Lab Setup
Ensure you have the following tools and software installed on your computer:

- **Audacity**: A free, open-source audio editor and recorder.
- **Python**: A programming language with libraries such as NumPy, SciPy, and Matplotlib.
- **FDTD Acoustic Simulation Software**: A tool to simulate sound wave propagation and interaction with materials.

## Exercise 1: Foundational Practical Implementation

### Exercise 1.1: Generating a Pure Tone
In this exercise, you will generate a pure tone using Python and NumPy, and then analyze its frequency spectrum using a Fast Fourier Transform (FFT).

#### Step-by-Step Procedure
Open your Python environment and import the necessary libraries:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import write, read
```

Define the parameters for the pure tone:

```python
sample_rate = 44100  # in Hz
duration = 1.0  # in seconds
frequency = 440.0  # in Hz (A4 note)
```

Generate the time array and the pure tone:

```python
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
tone = 0.5 * np.sin(2 * np.pi * frequency * t)
```

Save the tone as a WAV file:

```python
write("pure_tone.wav", sample_rate, tone.astype(np.float32))
```

Load the generated tone using SciPy:

```python
sample_rate, tone = read("pure_tone.wav")
```

Compute the FFT of the tone:

```python
fft = np.fft.fft(tone)
frequencies = np.fft.fftfreq(len(tone), 1/sample_rate)
```

Plot the magnitude of the FFT:

```python
plt.figure(figsize=(10, 5))
plt.plot(frequencies, np.abs(fft))
plt.title("Frequency Spectrum of Pure Tone")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(0, 2000)  # Limit x-axis to 2000 Hz for clarity
plt.grid()
plt.show()
```

### Exercise 1.2: Recording and Analyzing a Vocal Sample
In this exercise, you will record a vocal sample using Audacity, and then analyze its frequency spectrum using Python.

#### Step-by-Step Procedure
Open Audacity and set the project rate to 44100 Hz. Record a short vocal sample (e.g., a vowel sound) and save the recording as a WAV file.

Load the recorded vocal sample using SciPy:

```python
sample_rate, vocal_sample = read("vocal_sample.wav")
```

Compute the FFT of the vocal sample:

```python
fft = np.fft.fft(vocal_sample)
frequencies = np.fft.fftfreq(len(vocal_sample), 1/sample_rate)
```

Plot the magnitude of the FFT:

```python
plt.figure(figsize=(10, 5))
plt.plot(frequencies, np.abs(fft))
plt.title("Frequency Spectrum of Vocal Sample")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(0, 2000)  # Limit x-axis to 2000 Hz for clarity
plt.grid()
plt.show()
```

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise 2.1: Varying Frequency and Analyzing the Spectrum
In this exercise, you will vary the frequency of a pure tone and analyze how it affects the frequency spectrum.

#### Step-by-Step Procedure
Define a range of frequencies:

```python
frequencies = [220, 440, 880]  # C4, A4, C5 notes
```

For each frequency, generate a tone and compute its FFT:

```python
for freq in frequencies:
    tone = 0.5 * np.sin(2 * np.pi * freq * t)
    fft = np.fft.fft(tone)
    plt.figure(figsize=(10, 5))
    plt.plot(frequencies, np.abs(fft))
    plt.title(f"Frequency Spectrum of {freq} Hz Tone")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.xlim(0, 2000)  # Limit x-axis to 2000 Hz for clarity
    plt.grid()
    plt.show()
```

### Exercise 2.2: Simulating Sound Wave Propagation in a Room
In this exercise, you will use FDTD software to simulate sound wave propagation in a room and analyze the resulting acoustic response.

#### Step-by-Step Procedure
Open the FDTD acoustic simulation software and define the dimensions of the room (e.g., 5m x 4m x 3m). Place a sound source (e.g., a point source) at one end of the room and a receiver (e.g., a microphone) at the other end. Set the frequency of the sound source to 440 Hz.

Run the simulation and observe the sound wave propagation and the resulting acoustic response at the receiver. Adjust the room dimensions and material properties (e.g., wall absorption) and rerun the simulation to observe the changes in the acoustic response.

## Exercise 3: Fault Injection & Stress Testing

### Exercise 3.1: Introducing Noise and Analyzing the Effect on the Spectrum
In this exercise, you will introduce noise to a pure tone and analyze how it affects the frequency spectrum.

#### Step-by-Step Procedure
Generate a pure tone as in Exercise 1.1 and add Gaussian noise to the tone:

```python
noise = 0.1 * np.random.normal(size=tone.shape)
noisy_tone = tone + noise
```

Save the noisy tone as a WAV file:

```python
write("noisy_tone.wav", sample_rate, noisy_tone.astype(np.float32))
```

Load the noisy tone using SciPy:

```python
sample_rate, noisy_tone = read("noisy_tone.wav")
```

Compute the FFT of the noisy tone:

```python
fft = np.fft.fft(noisy_tone)
frequencies = np.fft.fftfreq(len(noisy_tone), 1/sample_rate)
```

Plot the magnitude of the FFT:

```python
plt.figure(figsize=(10, 5))
plt.plot(frequencies, np.abs(fft))
plt.title("Frequency Spectrum of Noisy Tone")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(0, 2000)  # Limit x-axis to 2000 Hz for clarity
plt.grid()
plt.show()
```

### Exercise 3.2: Simulating Room Acoustic Failures
In this exercise, you will simulate room acoustic failures by varying room dimensions and material properties to observe their impact on sound wave propagation and acoustic response. Adjust parameters such as wall absorption and room size to introduce failures and analyze the resulting changes in the simulation output.
