# Beginner Hands-On Lab: Audio DSP
## Objective & Prerequisites
**Objective:**  
In this lab, you will set up your environment for Audio Digital Signal Processing (DSP) and execute your first commands using a popular DSP library, such as `scipy.signal` in Python. By the end of this lab, you should be able to verify your setup and perform basic DSP operations.

**Prerequisites:**  
- Basic knowledge of Python programming.
- Python installed on your system (preferably Python 3.8 or later).
- Familiarity with using a command-line interface (CLI).

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
**Step 1: Install Required Libraries**  
Open your command-line interface (CLI) and install the necessary Python libraries using `pip`. Run the following commands:

```bash
pip install numpy
pip install scipy
pip install matplotlib
```

**Step 2: Verify Installation**  
Create a new Python file named `verify_installation.py` and add the following code to check if the libraries are installed correctly:

```python
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

print("Numpy version:", np.__version__)
print("Scipy version:", signal.__version__)
print("Matplotlib version:", plt.__version__)
```

Run the script using the following command:

```bash
python verify_installation.py
```

**Expected Output:**  
You should see the versions of `numpy`, `scipy`, and `matplotlib` printed in the terminal.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
**Step 1: Create a Simple Signal**  
Create a new Python file named `simple_signal.py` and add the following code to generate a simple sine wave:

```python
import numpy as np
import matplotlib.pyplot as plt

# Parameters
frequency = 5  # Frequency in Hz
sampling_rate = 100  # Sampling rate in Hz
duration = 1  # Duration in seconds

# Time vector
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

# Generate sine wave
sine_wave = np.sin(2 * np.pi * frequency * t)

# Plot the sine wave
plt.plot(t, sine_wave)
plt.title('Sine Wave')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.grid(True)
plt.show()
```

**Step 2: Run the Script**  
Execute the script using the following command:

```bash
python simple_signal.py
```

**Expected Output:**  
A plot window should appear displaying a sine wave with a frequency of 5 Hz.

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
**Step 1: Analyze the Signal**  
Modify the `simple_signal.py` script to include a Fast Fourier Transform (FFT) to analyze the frequency components of the sine wave:

```python
import numpy as np
import matplotlib.pyplot as plt
import scipy.fft as fft

# Parameters
frequency = 5  # Frequency in Hz
sampling_rate = 100  # Sampling rate in Hz
duration = 1  # Duration in seconds

# Time vector
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

# Generate sine wave
sine_wave = np.sin(2 * np.pi * frequency * t)

# Compute FFT
fft_result = fft.fft(sine_wave)
fft_freqs = fft.fftfreq(len(sine_wave), 1/sampling_rate)

# Plot the sine wave
plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(t, sine_wave)
plt.title('Sine Wave')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.grid(True)

# Plot the FFT
plt.subplot(2, 1, 2)
plt.plot(fft_freqs, np.abs(fft_result))
plt.title('FFT of Sine Wave')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Magnitude')
plt.grid(True)

plt.tight_layout()
plt.show()
```

**Step 2: Run the Script**  
Execute the script using the following command:

```bash
python simple_signal.py
```

**Expected Output:**  
Two plots should appear: the first showing the sine wave, and the second showing the FFT of the sine wave, with a peak at 5 Hz.

## Challenge Exercise (Simple self-test for beginners)
**Objective:**  
Generate a square wave with a frequency of 3 Hz and a sampling rate of 100 Hz. Plot the square wave and its FFT.

**Instructions:**  
1. Create a new Python file named `square_wave.py`.
2. Use `scipy.signal.square` to generate a square wave.
3. Plot the square wave and its FFT using `matplotlib`.
4. Run the script and verify the output.

**Expected Output:**  
Two plots should appear: the first showing the square wave, and the second showing the FFT of the square wave, with peaks at odd harmonics of 3 Hz.
