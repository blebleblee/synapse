# Operational Verification Labs: Audio DSP

## Objective & Lab Setup

This laboratory aims to provide hands-on experience with fundamental concepts in Audio Digital Signal Processing (DSP) as applied to music production. Through a series of exercises, participants will gain practical skills in implementing, configuring, and analyzing digital filters, understanding the effects of parameter variations, and testing the robustness of DSP algorithms.

### Required Tools, Environments, Packages, or Simulators

The software environment for this laboratory includes MATLAB or Python with the SciPy and NumPy libraries. For filter design and analysis in Python, the `scipy.signal` library is used. Audio file manipulation is handled by `pydub`, and `matplotlib` is used for plotting. Optionally, a Digital Audio Workstation (DAW) such as Ableton Live, FL Studio, or Logic Pro can be used for real-time DSP experimentation.

Ensure that all required libraries are installed in your Python environment. Installation can be performed using pip:

```bash
pip install numpy scipy matplotlib pydub
```

## Exercise 1: Foundational Practical Implementation

In this exercise, we will implement a simple low-pass filter using a Direct Form I biquad filter structure. The low-pass filter will be designed to have a cutoff frequency of 1 kHz and a sampling rate of 44.1 kHz.

### Step-by-Step Runnable Exercise

First, import the necessary libraries:

```python
import numpy as np
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt
from pydub import AudioSegment
from pydub.generators import Sine
```

Define the filter parameters:

```python
cutoff = 1000  # Cutoff frequency in Hz
fs = 44100     # Sampling frequency in Hz
order = 2      # Filter order
```

Design the low-pass filter:

```python
nyq = 0.5 * fs  # Nyquist frequency
normal_cutoff = cutoff / nyq
b, a = butter(order, normal_cutoff, btype='low', analog=False)
```

Generate a test signal consisting of a 5-second audio signal with a 500 Hz sine wave and a 2 kHz sine wave:

```python
duration = 5000  # Duration in milliseconds
freq1 = 500      # Frequency of the first sine wave in Hz
freq2 = 2000     # Frequency of the second sine wave in Hz

sine1 = Sine(freq1, sample_rate=fs).to_audio_segment(duration=duration)
sine2 = Sine(freq2, sample_rate=fs).to_audio_segment(duration=duration)

test_signal = sine1.overlay(sine2)
test_signal = np.array(test_signal.get_array_of_samples(), dtype=np.float32) / 32768.0
```

Apply the filter to the test signal:

```python
filtered_signal = lfilter(b, a, test_signal)
```

Plot the frequency response of the filter:

```python
w, h = freqz(b, a, worN=8000)
plt.figure()
plt.plot(0.5*fs*w/np.pi, np.abs(h), 'b')
plt.title('Digital Filter Frequency Response')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Gain')
plt.grid()
plt.show()
```

Plot the original and filtered signals:

```python
plt.figure()
plt.plot(test_signal[:1000], label='Original Signal')
plt.plot(filtered_signal[:1000], label='Filtered Signal')
plt.title('Original and Filtered Signals')
plt.xlabel('Samples')
plt.ylabel('Amplitude')
plt.legend()
plt.grid()
plt.show()
```

## Exercise 2: Parameter Variation & Empirical Analysis

In this exercise, we will vary the cutoff frequency and order of the low-pass filter and analyze the resulting frequency responses and filtered signals.

### Step-by-Step Runnable Exercise

Define a function to design and apply the filter:

```python
def design_and_apply_filter(cutoff, order, test_signal, fs):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_signal = lfilter(b, a, test_signal)
    return b, a, filtered_signal
```

Vary the cutoff frequency and plot the frequency responses:

```python
cutoffs = [500, 1000, 2000, 4000]
orders = [2, 4, 6]

plt.figure()
for cutoff in cutoffs:
    b, a, filtered_signal = design_and_apply_filter(cutoff, 2, test_signal, fs)
    w, h = freqz(b, a, worN=8000)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), label=f'Cutoff: {cutoff} Hz')
plt.title('Frequency Response for Different Cutoff Frequencies')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Gain')
plt.legend()
plt.grid()
plt.show()
```

Vary the filter order and plot the frequency responses:

```python
plt.figure()
for order in orders:
    b, a, filtered_signal = design_and_apply_filter(1000, order, test_signal, fs)
    w, h = freqz(b, a, worN=8000)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), label=f'Order: {order}')
plt.title('Frequency Response for Different Filter Orders')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Gain')
plt.legend()
plt.grid()
plt.show()
```

Plot the filtered signals for different cutoff frequencies:

```python
plt.figure()
for cutoff in cutoffs:
    b, a, filtered_signal = design_and_apply_filter(cutoff, 2, test_signal, fs)
    plt.plot(filtered_signal[:1000], label=f'Cutoff: {cutoff} Hz')
plt.title('Filtered Signals for Different Cutoff Frequencies')
plt.xlabel('Samples')
plt.ylabel('Amplitude')
plt.legend()
plt.grid()
plt.show()
```

Plot the filtered signals for different filter orders:

```python
plt.figure()
for order in orders:
    b, a, filtered_signal = design_and_apply_filter(1000, order, test_signal, fs)
    plt.plot(filtered_signal[:1000], label=f'Order: {order}')
plt.title('Filtered Signals for Different Filter Orders')
plt.xlabel('Samples')
plt.ylabel('Amplitude')
plt.legend()
plt.grid()
plt.show()
```

## Exercise 3: Fault Injection & Stress Testing

In this exercise, we will introduce faults into the filter design and analyze the resulting behavior. We will test the filter's response to extreme cutoff frequencies and orders, and verify its robustness.

### Step-by-Step Runnable Exercise

Test extreme cutoff frequencies and plot the frequency responses:

```python
extreme_cutoffs = [10, 22050]  # Below and above Nyquist frequency

plt.figure()
for cutoff in extreme_cutoffs:
    b, a, filtered_signal = design_and_apply_filter(cutoff, 2, test_signal, fs)
    w, h = freqz(b, a, worN=8000)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), label=f'Cutoff: {cutoff} Hz')
plt.title('Frequency Response for Extreme Cutoff Frequencies')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Gain')
plt.legend()
plt.grid()
plt.show()
```

Test extreme filter orders and plot the frequency responses:

```python
extreme_orders = [1, 10]  # Very low and very high orders

plt.figure()
for order in extreme_orders:
    b, a, filtered_signal = design_and_apply_filter(1000, order, test_signal, fs)
    w, h = freqz(b, a, worN=8000)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), label=f'Order: {order}')
plt.title('Frequency Response for Extreme Filter Orders')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Gain')
plt.legend()
plt.grid()
plt.show()
```
