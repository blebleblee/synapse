# Lesson 4: Data Processing at the Edge

## 1. First-Principles Intuition & Invariants

The fundamental constraint driving edge data processing in IoT systems is the bandwidth and latency tax imposed by cloud transmission. When an embedded sensor array—say, a vibration accelerometer on an industrial pump sampling at 10 kHz—transmits raw waveforms to a distant server, you face several cascading problems: the cellular or WiFi uplink becomes saturated, round-trip latency introduces unacceptable delays for real-time decision-making, and your power budget evaporates as the radio module dominates current draw. Yet the raw sensor stream contains redundancy, noise, and information of varying relevance to your application's actual decision boundary.

Edge processing inverts this paradigm. Instead of shipping terabytes of raw sensor data to the cloud, you perform **filtering, aggregation, statistical extraction, and lightweight inference** directly on the constrained microcontroller or edge gateway—often a device with only kilobytes of RAM and a processor operating at 100 MHz. This approach accomplishes three critical objectives: it reduces transmitted data volume by orders of magnitude (a 10 kHz accelerometer stream compressed to five aggregate statistics per second represents a 50,000× reduction in bandwidth), it enables sub-millisecond response to anomalies without waiting for cloud round-trips, and it preserves privacy by never exposing raw sensor telemetry beyond the device perimeter.

The invariant underlying all edge data processing is the **information extraction principle**: you must extract decision-relevant features from high-volume, low-SNR sensor streams using operations that fit within the memory and computational envelope of a resource-constrained device. This principle creates three orthogonal design tensions. First, **temporal granularity**: you must choose a windowing strategy—fixed-time windows, event-triggered windows, or sliding overlapping windows—that captures transient phenomena without excessive computational overhead. Second, **feature space**: you must select which statistical moments (mean, variance, RMS, peak), spectral characteristics (FFT bins, Goertzel coefficients), or temporal patterns (zero-crossings, rate-of-change) actually encode the information your application needs to distinguish safe from unsafe states. Third, **computational budget**: every operation—convolution, FFT, neural network forward pass—consumes clock cycles and energy; you must allocate this budget optimally across filtering, aggregation, and inference stages.

The physical reality underpinning edge processing is that **sensors are fundamentally analog transducers immersed in electromagnetic and environmental noise**. A 16-bit ADC sampling at 1 MHz produces 2 million measurements per second; 90% of these samples often represent quantization noise and interference, not signal of interest. Classical signal processing—matched filters, polyphase decimation, Butterworth low-pass stages—removes this noise and downsamples the stream to a manageable rate (perhaps 100 samples per second) while preserving the information bandwidth of the underlying phenomenon. Modern edge systems layer on top of this classical foundation: time-frequency analysis via wavelets or constant-Q transforms extracts localized transients, dimensionality reduction through principal component analysis or autoencoders compresses multi-channel data, and lightweight neural networks perform non-linear classification tasks that rule-based heuristics cannot express.

The event-driven paradigm represents a philosophical inversion of the traditional polling model. Rather than sampling at a fixed rate and processing every sample, event-driven edge systems configure the sensor interface (often using threshold comparators, digital pulse counters, or interrupt-driven ADC sampling) to generate events only when interesting phenomena occur. An accelerometer detecting a shock exceeding 2 g might trigger a 100 ms recording window at full sampling rate; the vast majority of time—when the system is quiescent—the sensor remains in a low-power state drawing microamps. This model radically reduces average power consumption and processing load while maintaining responsiveness to anomalies.

Latency optimization in edge systems operates on three distinct timescales. **Microsecond-scale latency** (1–100 μs) governs interrupt response times for safety-critical events: a fault detection triggering a motor shutdown or emergency valve closure must respond within this window or physical damage results. **Millisecond-scale latency** (1–100 ms) applies to inference and feature extraction: a TinyML model classifying acoustic anomalies must produce confidence scores before the sound event has passed out of human perceptual window or before the underlying mechanical failure propagates. **Second-scale latency** (1–10 s) covers bulk data aggregation and transmission scheduling: IoT gateways batch processed features into JSON payloads and transmit during optimal network conditions or on a regular reporting cadence.

Bandwidth conservation in IoT hinges on three complementary techniques. **Compression** reduces the bit-length of transmitted data through quantization (representing floating-point sensor values as 8-bit integers), delta encoding (transmitting differences rather than absolute values when consecutive samples are correlated), and entropy coding (using variable-length bit patterns for frequently occurring statistics). **Selective transmission** applies logic to decide *which* data reaches the cloud: you might transmit only anomaly flags, feature vectors, and event timestamps—never raw waveforms. **Temporal aggregation** summarizes high-frequency sensor streams as lower-frequency statistical summaries: instead of transmitting 10,000 accelerometer samples, you transmit a single JSON object containing mean acceleration, peak acceleration, and FFT power at specific frequency bands.

## 2. Core Architecture & Mechanics

The canonical edge data processing pipeline consists of five logical stages, each with distinct hardware and software requirements. Understanding the signal flow through these stages—and the resource trade-offs at each boundary—forms the foundation for designing practical IoT systems.

**Stage 1: Analog Acquisition & Anti-Aliasing**

The analog-to-digital conversion process begins with the analog front-end (AFE): the sensor transducer, passive filter network, and preamplifier that condition the raw physical signal (temperature, pressure, acceleration, sound) into a voltage suitable for digitization. Consider a vibration monitoring application using a piezoelectric accelerometer. The sensor generates a charge proportional to acceleration; a charge-to-voltage transimpedance amplifier converts this to a rail-referenced signal (typically 0–3.3 V). This signal then passes through an anti-aliasing filter—a second-order or higher Sallen-Key topology with corner frequency set slightly below the Nyquist frequency of your intended sampling rate.

The physics here is non-negotiable: if your ADC samples at 10 kHz, the Nyquist frequency is 5 kHz. Any frequency content above 5 kHz that reaches the ADC will alias back into the baseband (0–5 kHz), creating artifacts that your edge processor cannot distinguish from true signal. A simple first-order RC filter (corner frequency = 1/(2πRC)) provides minimal attenuation; a second-order Butterworth topology (flat passband, 40 dB/decade roll-off) is practical for most industrial applications. The component values are determined by the desired corner frequency and available impedance ranges: for a 5 kHz corner with 10 kΩ resistors, the capacitor value becomes C = 1/(2π × 5000 × 10000) ≈ 3.2 nF.

After filtering, the continuous analog signal enters the ADC's sample-and-hold (S/H) circuit. This is a capacitor that briefly samples the instantaneous input voltage, then holds that value while the ADC's successive-approximation register (SAR) or delta-sigma modulator performs the conversion. The acquisition time—the duration for which the S/H capacitor must charge to the input voltage—imposes a constraint on the maximum input impedance and slew rate. For a 12-bit ADC with 1 LSB accuracy (representing one part in 4096), the settling error must be less than 0.025% of full scale. If your signal source has 1 kΩ output impedance and the ADC datasheet specifies a 10 pF S/H capacitance, the RC time constant is 10 ns; settling to 0.025% accuracy requires approximately 5 RC time constants, or 50 ns. This is achievable at most sampling rates, but must be verified empirically on your specific microcontroller and sensor combination.

**Stage 2: Digital Filtering & Decimation**

Once the ADC produces digital samples, the first processing step is usually a digital filter chain that removes out-of-band noise and downsamples the stream to a lower rate for subsequent feature extraction or inference. The canonical architecture uses a cascade of stages with increasing filter orders and decimation ratios.

A finite impulse response (FIR) filter implements a linear convolution of the input stream with a coefficient vector. The filtered output at time step n is:

$$y[n] = \sum_{k=0}^{M-1} h[k] \cdot x[n-k]$$

where $h[k]$ are the filter coefficients (typically designed via windowing methods like Hamming or Kaiser windows, or Parks-McClellan equiripple design), $x[n-k]$ are past input samples, and $M$ is the filter order. A 64-tap FIR filter requires 64 multiply-accumulate operations per output sample; on a 100 MHz ARM Cortex-M4 with a hardware MAC unit, this consumes roughly 640 clock cycles per sample. At a 10 kHz input rate, this represents 6.4 MHz of computation—less than 7% of available CPU resources, which is practical.

The decimation operation follows filtering: instead of computing output samples at the input rate, you compute every $D$-th sample. This reduces output rate by a factor $D$ (the decimation ratio). A practical cascade might combine a 4-tap FIR followed by 2× decimation (producing a 5 kHz stream), then a 32-tap FIR followed by 5× decimation (producing a 1 kHz stream). Each stage must satisfy the Nyquist criterion: the filter's stopband attenuation must exceed the quantization noise floor at the reduced sampling rate, otherwise aliased energy contaminates the downsampled stream.

The computational benefit of cascade decimation is substantial. If you attempted to implement a single-stage 64-tap FIR at 10 kHz, then manually decimated by 10×, you waste 90% of the MAC operations computing samples you discard. By decimating early—after filtering to the reduced bandwidth—you reduce computation by the decimation ratio at each stage. For a 100× total decimation (10 kHz input to 100 Hz output), a three-stage cascade (2×, 5×, 10×) might consume 10% of CPU resources, compared to 70% for a naive single-stage approach.

**Stage 3: Feature Extraction & Aggregation**

Raw filtered samples, even at reduced rates, still contain redundancy and lack semantic meaning for your application. Feature extraction transforms this stream into a compact vector of statistics that encode the phenomena of interest. For industrial condition monitoring, common features include the RMS (root mean square) value—the L2 norm of the signal, which correlates with vibration energy; the crest factor (peak-to-RMS ratio), which identifies impulsive transients; and spectral statistics (power at specific frequency bands, entropy across the FFT).

The RMS calculation over a window of $N$ samples is:

$$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=0}^{N-1} x[i]^2}$$

This requires $N$ multiply operations (to compute $x[i]^2$), $N$ additions (to accumulate), and one square root. For a 1 kHz decimated stream, computing RMS over a 1-second window (1000 samples) costs roughly 2000 arithmetic operations—negligible on modern microcontrollers. More sophisticated features like spectral moments (centroid, spread, skewness) require FFT computation, which is costlier but still practical.

The Fast Fourier Transform (FFT) decomposes a time-domain signal into its frequency components:

$$X[k] = \sum_{n=0}^{N-1} x[n] \cdot e^{-j2\pi kn/N}$$

A radix-2 FFT of 256 samples requires approximately $N \log_2(N) = 256 \times 8 = 2048$ complex multiplications. On an ARM Cortex-M4 with hardware floating-point, optimized FFT libraries (CMSIS-DSP from Arm's embedded DSP library, or open-source projects like KissFFT) execute in roughly 5–10 milliseconds for a 256-point transform. This cost is incurred periodically (perhaps every 250 ms for a 1 Hz feature update rate), not continuously, so the average CPU load remains acceptable.

Feature aggregation windowing strategies determine how frequently features are computed and transmitted. **Fixed-time windowing** divides the input stream into non-overlapping intervals (e.g., 1-second windows) and computes features independently for each window. This is simple to implement and has predictable memory footprint but can miss transients that straddle window boundaries. **Sliding-window aggregation** maintains a rolling buffer and computes features continuously; each new sample triggers a window shift and feature update. This captures transient phenomena but requires more memory (to buffer overlapping windows) and sustained computation. **Event-triggered windowing** computes features only when a trigger condition occurs—for instance, when peak acceleration exceeds a threshold or when spectral power in a specific band rises above baseline. This minimizes average computation but requires careful threshold tuning to avoid false positives (triggering on noise) or false negatives (missing real anomalies).

**Stage 4: TinyML Inference**

Modern edge devices can execute lightweight neural networks for classification and regression tasks. These networks—constrained to 10–100 KB of model weights due to flash memory limitations—cannot replicate the accuracy of cloud-scale deep learning but often outperform rule-based heuristics on complex decision boundaries.

A typical TinyML architecture for IoT anomaly detection uses a simple multilayer perceptron (MLP) with one or two hidden layers. Consider a bearing fault classifier: inputs are 10 statistical features extracted from vibration (RMS, crest factor, spectral centroid, etc.); outputs are class probabilities for {normal, early fault, bearing failure}. A practical network might have a 10→32→16→3 structure (10 input features, 32 neurons in first hidden layer, 16 in second layer, 3 output classes):

Forward pass through first hidden layer:
$$h_i^{(1)} = \text{ReLU}\left( \sum_{j=0}^{9} W_{ij}^{(1)} \cdot x_j + b_i^{(1)} \right)$$

where $W^{(1)}$ is a 32×10 weight matrix, $b^{(1)}$ is a 32-element bias vector, and ReLU is the rectified linear unit activation ($\text{ReLU}(z) = \max(0, z)$). This layer requires 10×32 = 320 multiply-accumulates plus 32 comparisons for ReLU.

Forward pass through second hidden layer:
$$h_i^{(2)} = \text{ReLU}\left( \sum_{j=0}^{31} W_{ij}^{(2)} \cdot h_j^{(1)} + b_i^{(2)} \right)$$

This requires 32×16 = 512 MACs plus 16 comparisons.

Output layer with softmax:
$$y_k = \frac{e^{z_k}}{\sum_{\ell=0}^{2} e^{z_\ell}}, \quad z_k = \sum_{i=0}^{15} W_{ik}^{(3)} \cdot h_i^{(2)} + b_k^{(3)}$$

This requires 16×3 = 48 MACs, plus three exponentials and a normalization. Total: approximately 880 MACs and 50–60 transcendental operations. On a 100 MHz ARM Cortex-M4, this executes in under 10 milliseconds, enabling inference rates of 100+ Hz if needed.

The quantization trade-off is critical: floating-point arithmetic is expensive on microcontrollers lacking an FPU (floating-point unit). Modern TinyML frameworks quantize weights and activations to 8-bit or even 4-bit integers, reducing memory footprint and computation time by 4–8×. An 8-bit quantized model uses int8 arithmetic: weights are represented as signed 8-bit integers scaled by a quantization factor (e.g., $W_{\text{int8}} = \text{round}(W_{\text{float32}} / \text{scale})$). During inference, multiply-accumulates use integer multiplication (native on all microprocessors), and the output is rescaled back to float for activation functions. The accuracy loss from quantization is typically 1–3% for well-trained models.

Tools like TensorFlow Lite for Microcontrollers (TFLite Micro) provide end-to-end workflows: train a model in Python using standard TensorFlow, quantize and convert to a C header file containing binary model weights and a minimal interpreter runtime (typically 50–100 KB), and include this in your embedded firmware. The interpreter is a compact virtual machine that executes the model graph; most IoT frameworks now use this approach rather than requiring hand-optimized assembly.

**Stage 5: Event-Driven Output & Transmission**

The final stage determines what data leaves the edge device and at what cadence. Most IoT systems employ a hybrid strategy: continuous collection and processing of local features, periodic transmission of aggregated statistics (every 60 seconds, every 1 hour, or on a WiFi connection event), and immediate transmission of alerts when anomalies are detected.

An event queue manages this asynchronous flow. When an anomaly classifier produces a high-confidence fault prediction, an event is enqueued with timestamp, feature vector, and confidence score. The transmission scheduler checks this queue periodically and combines pending events with the latest feature aggregates into a JSON payload:

```json
{
  "device_id": "pump_bay_3",
  "timestamp": 1704067200,
  "features": {
    "vibration_rms": 2.34,
    "temperature": 65.2,
    "vibration_crest_factor": 4.1,
    "spectral_centroid_hz": 1420
  },
  "alerts": [
    {
      "type": "bearing_fault",
      "confidence": 0.92,
      "feature_vector": [2.34, 65.2, 4.1, 1420, ...]
    }
  ]
}
```

This consolidated message transmits over WiFi, cellular LTE-M, or LoRaWAN depending on device capabilities. A gateway device (Raspberry Pi, AWS Greengrass core, or proprietary embedded Linux system) may further aggregate multiple device messages before forwarding to the cloud, a pattern that dramatically reduces bandwidth for large sensor networks.

The following diagram illustrates the complete data flow:

```
Sensor → AFE Filter → ADC → FIR Decimator → Feature Extract → TinyML
          (analog)    (10kHz)  (1kHz)         (100 Hz)         (10 Hz)
                                                    ↓
                                             Event Queue
                                                    ↓
                                         Transmission Scheduler
                                                    ↓
                                         WiFi/LTE/LoRa Module
                                                    ↓
                                              Cloud
```

Each stage reduces data volume and computational load: the AFE removes out-of-band noise; decimation reduces sample rate by 10×; feature extraction compresses 1000 raw samples into 5–10 scalar statistics; the inference engine produces a single classification or anomaly score; the transmission scheduler batches events and periodic reports into discrete packets. The cumulative effect is a 10,000× reduction in data volume compared to transmitting raw ADC samples, while preserving decision-relevant information.

## 3. High-Performance Optimization & Failure Modes

Deploying edge processing in production IoT systems surfaces subtle failure modes that do not appear in laboratory prototyping. Understanding these failure modes and implementing mitigations is the difference between a functional proof-of-concept and a reliable industrial system.

**Latency Bottlenecks & Real-Time Constraints**

The most insidious latency failure occurs when processing deadlines slip silently. Consider a vibration monitoring application where you aggregate features over 1-second windows and transmit every 60 seconds. If the feature extraction stage occasionally exceeds 1 second of computation (due to cache misses, garbage collection pauses, or interrupt contention), samples are dropped or delayed, corrupting feature fidelity. Real-time embedded systems must bound worst-case latency, not average latency.

The solution is **profiling with worst-case execution time (WCET) analysis**. Using tools like ARM's Performance Monitor Unit (PMU), you count clock cycles for each processing stage under realistic conditions: with varying input data patterns, under interrupt load, and with memory cache in different states. A simple profiling approach on ARM Cortex-M devices uses the DWT (Data Watchpoint and Trace) cycle counter. The following C routine measures the execution time of a function:

```c
#include <stdint.h>

// Enable DWT cycle counter (ARM Cortex-M)
void dwt_enable(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNT_Msk;
}

// Measure cycles for a function
uint32_t measure_cycles(void (*func)(void)) {
    uint32_t start = DWT->CYCCNT;
    func();
    uint32_t end = DWT->CYCCNT;
    return end - start;
}

// Example: measure FFT performance
void measure_fft_performance(void) {
    float input[256];
    float output[256];
    
    // Populate input with test data
    for (int i = 0; i < 256; i++) {
        input[i] = sinf(2.0f * M_PI * i / 256.0f); // 1 Hz sine in 256 samples
    }
    
    uint32_t cycles = DWT->CYCCNT;
    arm_rfft_fast_f32(&S, input, output, 0);
    cycles = DWT->CYCCNT - cycles;
    
    float execution_time_ms = (cycles / (float)SystemCoreClock) * 1000.0f;
    printf("FFT execution: %u cycles, %.2f ms\n", cycles, execution_time_ms);
}
```

Once you establish WCET for each stage, you can build a predictability budget: if FFT takes 5 ms worst-case, feature aggregation takes 2 ms, and inference takes 1 ms, then the entire processing pipeline has a 8 ms latency budget. This leaves 42 ms of slack for a 50 ms window (before the next ADC batch arrives). If profiling reveals that FFT occasionally spikes to 8 ms (due to memory stalls), you redesign the system: perhaps using a smaller FFT (128 points instead of 256), or implementing FFT computation across multiple windows (interleaving FFT calculations to amortize cost over time).

Another critical latency issue is **interrupt priority inversion**. If a low-priority background task is executing FFT computation when a high-priority ADC interrupt fires, the FFT blocks the ADC service routine, potentially causing samples to drop. The fix is priority-aware task scheduling: ensure that ADC interrupt handlers have higher priority than application-level processing, and use OS-level real-time scheduling (if your system runs an RTOS like FreeRTOS) to guarantee that high-priority tasks preempt lower-priority work.

**Memory Fragmentation & Buffer Overflow**

Edge devices typically operate with fixed, pre-allocated memory: no dynamic heap allocation, or severely restricted allocation patterns. Many IoT systems run malloc-free, using only statically allocated buffers. This eliminates dynamic memory fragmentation but requires careful buffer sizing.

A common failure occurs when feature aggregation requires a larger window than available RAM. Consider a 10 kHz accelerometer sampled at 12 bits (2 bytes per sample). A 1-second window requires 20 KB of buffered samples. If your device has only 96 KB of SRAM (typical for mid-range microcontrollers), and 50 KB is already consumed by the FFT working area, the remaining 46 KB is insufficient. The workaround is implementing a **streaming or online aggregation algorithm**: instead of buffering all samples, you compute running statistics incrementally as samples arrive.

For example, computing RMS online requires maintaining only two accumulators:

```c
typedef struct {
    uint32_t sample_count;
    float sum_of_squares;
} OnlineRMS;

void online_rms_init(OnlineRMS *rms) {
    rms->sample_count = 0;
    rms->sum_of_squares = 0.0f;
}

void online_rms_update(OnlineRMS *rms, float sample) {
    rms->sum_of_squares += sample * sample;
    rms->sample_count++;
}

float online_rms_get(const OnlineRMS *rms) {
    if (rms->sample_count == 0) return 0.0f;
    return sqrtf(rms->sum_of_squares / rms->sample_count);
}
```

This algorithm uses 12 bytes of state regardless of window length, enabling arbitrarily long aggregation windows without buffer overflow. Similar online algorithms exist for variance (
