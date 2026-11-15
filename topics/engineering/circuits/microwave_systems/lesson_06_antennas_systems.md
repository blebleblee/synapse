# Lesson 6: Antenna Theory, Link Budgets, System Integration

## 1. First-Principles Intuition & Invariants

The antenna sits at the boundary between circuit theory and electromagnetic wave propagation. Unlike the passive lumped-element networks and active amplifiers that dominated earlier lessons, the antenna transforms guided waves traveling along transmission lines into radiating electromagnetic fields that couple to free space, or conversely, capture incident plane waves and convert them back into guided voltages and currents. This transduction is neither lossless nor isotropic; it embodies directivity, gain, and impedance transformation that cascade through every microwave system architecture.

To understand antennas at the practitioner level, we must reject the temptation to treat them as black boxes with "gain" labels. Instead, we recognize that an antenna is fundamentally a resonant structure—typically operating at a characteristic frequency where its physical dimension becomes commensurate with the wavelength of the electromagnetic wave it radiates or receives. At microwave frequencies (1 GHz to 100 GHz), wavelengths shrink from 30 cm at 1 GHz to 3 mm at 100 GHz, making physical antenna dimensions tractable for bench-level fabrication and measurement.

The radiation pattern of an antenna is the three-dimensional map of electromagnetic field strength (or power flux density) radiating from or received by that antenna as a function of angle. This pattern is never uniform; it contains principal lobes (the directions of maximum radiation), minor side lobes, and null directions where radiation is suppressed. The directivity of an antenna quantifies how focused its radiation is compared to an isotropic radiator (a theoretical point source that radiates equally in all directions). Gain extends this concept by incorporating resistive losses and impedance mismatch; the realized gain is always less than or equal to directivity. These quantities are not abstract; they determine the signal-to-noise ratio (SNR) at a receiver thousands of kilometers away, the penetration depth of ground-penetrating radar, and whether a satellite link closes or fails.

The aperture theory of antennas reveals a profound duality: every antenna has an effective aperture area that determines how much power it can intercept from an incident plane wave. A small dipole antenna, despite its physical size, has an effective aperture that can be orders of magnitude larger than its geometric cross-section. Conversely, a large parabolic dish has an effective aperture close to its geometric area, limited by edge diffraction and illumination efficiency.

The Friis transmission equation is the foundation of link budget analysis. It expresses the power received by a receiving antenna as a function of transmitted power, antenna gains, path loss, and frequency:

$$P_r = P_t G_t G_r \left( \frac{\lambda}{4\pi d} \right)^2 = P_t G_t G_r \frac{c^2}{(4\pi f d)^2}$$

where $P_t$ is transmitted power, $G_t$ and $G_r$ are antenna gains in the direction of propagation, $\lambda$ is wavelength, $d$ is distance, $f$ is frequency, and $c$ is the speed of light. This equation is deceptively simple; it assumes free-space propagation without multipath, shadowing, or atmospheric attenuation. Real systems operate in environments where reflection, diffraction, and absorption violate these assumptions. Yet the Friis equation remains the starting point for every link budget because it establishes the power balance that determines whether a communication link, radar detection, or sensing system can achieve its performance goals.

Noise figure and noise factor quantify how much a system degrades the signal-to-noise ratio as a signal passes through amplifiers, mixers, and filters. When multiple stages cascade—a low-noise amplifier (LNA) followed by a mixer, then an intermediate-frequency (IF) amplifier—the noise figure of the entire system is dominated by the early stages. This is Friis's noise formula for cascaded networks:

$$F_{total} = F_1 + \frac{F_2 - 1}{G_1} + \frac{F_3 - 1}{G_1 G_2} + \ldots$$

where $F_i$ is the noise factor of stage $i$ and $G_i$ is the linear gain of stage $i$. The first term, $F_1$, dominates if $G_1$ is large, which is why the LNA must have low noise figure and high gain to set the overall noise performance of the receiver. This principle directly shapes the architecture of every microwave receiver: place a low-noise amplifier immediately after the antenna, before any lossy components, to minimize the noise figure of the entire chain.

The radar equation extends the Friis transmission equation to the case of a target that reflects energy back to the radar. For a radar transmitting power $P_t$ through an antenna with gain $G_t$, illuminating a target with radar cross-section (RCS) $\sigma$ at distance $d$, and receiving the reflected power with an antenna of gain $G_r$:

$$P_r = \frac{P_t G_t G_r \sigma \lambda^2}{(4\pi)^3 d^4}$$

Note the $d^4$ dependence in the denominator: the signal propagates outward (suffering $d^2$ loss), scatters from the target, and propagates back (suffering another $d^2$ loss), yielding the steeper $d^4$ rolloff. This fundamental difference from communication links means that radar detection range scales as the fourth root of transmitted power, making power and antenna gain critical to system performance.

## 2. Core Architecture & Mechanics

### Radiation Patterns and Antenna Parameters

The radiation pattern of an antenna is most commonly represented in polar coordinates (in the far field), where the radial distance from the origin represents the normalized power radiated or received in that direction. For a half-wave dipole antenna aligned along the z-axis, the time-averaged Poynting vector in the far field is proportional to $\sin^2(\theta)$, where $\theta$ is the angle from the z-axis. This creates a toroidal radiation pattern with maximum radiation perpendicular to the dipole and nulls along the antenna axis.

The beamwidth of an antenna is typically defined as the half-power beamwidth (HPBW), the angular separation between the directions where the radiated power drops to half the peak value (−3 dB). For a half-wave dipole, the HPBW in the plane perpendicular to the dipole is approximately 78 degrees. The directivity $D$ is defined as the ratio of the power radiated in the peak direction to the power that would be radiated by an isotropic antenna receiving the same total power:

$$D = \frac{U_{max}}{U_{avg}} = \frac{U_{max}}{P_{total} / (4\pi)} = \frac{4\pi U_{max}}{P_{total}}$$

where $U(\theta, \phi)$ is the radiation intensity (power per unit solid angle) and $U_{avg} = P_{total} / (4\pi)$ is the average radiation intensity over all solid angles (steradians).

For a half-wave dipole, the directivity is 1.64, or 2.14 dB. This modest directivity reflects the relatively broad radiation pattern. A parabolic reflector antenna, by contrast, can achieve directivity exceeding 50 dB by concentrating radiation into a narrow beam. The relationship between directivity and beamwidth for broadside arrays is approximately:

$$D \approx \frac{4\pi}{\Omega_A}$$

where $\Omega_A$ is the solid angle of the main lobe (in steradians). For a narrow antenna beam with half-power beamwidth $\theta_{HPBW}$ (in radians) and an azimuth width $\phi_{HPBW}$, the solid angle is roughly $\Omega_A \approx \theta_{HPBW} \cdot \phi_{HPBW}$, yielding an approximation often used in system design:

$$G \approx \frac{4\pi A_{phys}}{\lambda^2} \eta_e$$

where $A_{phys}$ is the physical aperture area, $\lambda$ is the wavelength, and $\eta_e$ is the aperture illumination efficiency (typically 0.5 to 0.8 for parabolic dishes).

The gain $G$ of an antenna differs from directivity by including the mismatch loss between the antenna impedance and the source (or load) impedance, and resistive losses within the antenna structure. The relationship is:

$$G = D \cdot \eta_r \cdot |\Gamma|^2$$

where $\eta_r$ is the radiation efficiency (ohmic loss factor) and $|\Gamma|^2$ is the impedance mismatch loss. For a well-designed antenna at its operating frequency, $\eta_r$ is close to unity, but impedance mismatch can reduce gain significantly. A return loss of 10 dB (reflection coefficient magnitude of 0.316) introduces a mismatch loss of 0.1 dB; a return loss of 6 dB introduces 0.5 dB of mismatch loss. In high-performance systems, antennas are designed to have return loss better than 15 dB (reflection coefficient less than 0.178) across their operating bandwidth.

### Antenna Impedance and Matching

An antenna presents an impedance to the transmission line connected to it. This impedance is generally complex: $Z_{ant} = R_{rad} + R_{loss} + j X$, where $R_{rad}$ is the radiation resistance (the equivalent resistance that dissipates power radiated into space), $R_{loss}$ is the ohmic resistance of the antenna structure, and $X$ is the reactance. For a half-wave dipole in free space, the radiation resistance is approximately 73 ohms, with nearly zero reactance at resonance. In practice, the antenna reactance varies with frequency; at frequencies above resonance, the antenna becomes capacitive; below resonance, it becomes inductive.

The reflection coefficient at the antenna port is:

$$\Gamma = \frac{Z_{ant} - Z_0}{Z_{ant} + Z_0}$$

where $Z_0$ is the characteristic impedance of the feed line (typically 50 ohms in microwave systems). The return loss (in dB) is:

$$RL = -20 \log_{10} |\Gamma|$$

and the voltage standing wave ratio (VSWR) is:

$$VSWR = \frac{1 + |\Gamma|}{1 - |\Gamma|}$$

For the half-wave dipole with $Z_{ant} = 73 + j0$ ohms and $Z_0 = 50$ ohms:

$$\Gamma = \frac{73 - 50}{73 + 50} = \frac{23}{123} = 0.187$$

$$RL = -20 \log_{10}(0.187) = 14.56 \text{ dB}$$

$$VSWR = \frac{1 + 0.187}{1 - 0.187} = 1.46$$

This impedance mismatch is acceptable but not ideal. To achieve better matching, antenna designers employ various techniques: narrowing the dipole arms (thick dipoles have lower impedance), adding a balun transformer, or placing a parallel capacitance or inductive stub at the antenna feed point. The balun (balanced-to-unbalanced transformer) is particularly important when feeding a balanced antenna (like a dipole) from an unbalanced transmission line (like a coaxial cable), as it also prevents common-mode currents from flowing on the outer conductor of the coax.

### Array Factor and Phased Array Synthesis

When multiple antenna elements are arranged in a regular pattern and fed with controlled amplitude and phase relationships, they form an antenna array. The radiation pattern of an array is the product of the single-element pattern and the array factor, which depends on the geometric arrangement and the excitation coefficients.

For a linear array of $N$ identical elements separated by distance $d$, all fed with equal amplitude but with a progressive phase shift $\psi$ between adjacent elements, the array factor in the far field is:

$$AF(\theta) = \sum_{n=0}^{N-1} e^{jn(kd\cos\theta + \psi)}$$

where $k = 2\pi / \lambda$ is the wave number and $\theta$ is the angle from the array axis. This is a geometric series with closed form:

$$AF(\theta) = \frac{\sin(N u / 2)}{\sin(u / 2)}}, \quad u = kd\cos\theta + \psi$$

This formula reveals the critical insight of phased array theory: by controlling the phase shift $\psi$, we can steer the main lobe of the array to arbitrary angles without physically rotating the array. Setting $\psi = -kd\cos\theta_0$ points the main lobe toward angle $\theta_0$. The main lobe width (between the first nulls) is:

$$\Delta\theta \approx \frac{2\lambda}{Nd}$$

At broadside ($\theta = 90°$, the plane perpendicular to the array), the beamwidth narrows as the number of elements increases or the element spacing decreases. Practical phased arrays operate with element spacing $d = \lambda/2$ to avoid grating lobes (spurious main lobes appearing at other angles due to spatial aliasing).

The beam steering rate, or the change in main lobe position for a unit change in phase, is:

$$\frac{d\theta_0}{d\psi} = -\frac{1}{kd\sin\theta_0}$$

At broadside, this becomes $d\theta_0 / d\psi = -1 / (2\pi d)$. For a 1-meter array at 10 GHz (wavelength 3 cm, so $d \approx 1.5$ cm), steering by 1 degree requires a phase change of approximately 1.3 radians (75 degrees). This is why phased arrays require precise phase control in each element—phase errors of just a few degrees degrade the beam pattern significantly.

The side lobe level of a uniformly excited linear array is approximately −13 dB relative to the main lobe. To reduce side lobes, the excitation amplitude across the array can be tapered using window functions (Hamming, Blackman, Chebyshev). For example, a Hamming window reduces side lobe levels to −43 dB at the cost of slightly widening the main lobe. This trade-off between beamwidth and side lobe suppression is fundamental; narrowing the main lobe inevitably increases the side lobe level unless the array is carefully weighted.

### The Friis Transmission Equation and Link Budgets

The Friis transmission equation in logarithmic form (in dB) is:

$$P_r [dBm] = P_t [dBm] + G_t [dBi] + G_r [dBi] - L_p [dB]$$

where the path loss in free space is:

$$L_p = 20 \log_{10}(4\pi d / \lambda) = 20 \log_{10}(4\pi f d / c)$$

At 10 GHz over a distance of 1 km:

$$L_p = 20 \log_{10}(4\pi \times 10^{10} \times 10^3 / 3 \times 10^8) = 20 \log_{10}(4.19 \times 10^4) = 92.4 \text{ dB}$$

If the transmitter delivers 1 W (0 dBm) through an antenna with 15 dBi gain, and the receiver has an antenna with 15 dBi gain, the received power is:

$$P_r = 0 + 15 + 15 - 92.4 = -62.4 \text{ dBm}$$

In linear units, this is approximately 0.6 microwatts. Whether this power level is sufficient depends on the receiver's sensitivity, which is determined by its noise figure and required SNR.

A receiver's noise figure expresses the degradation of SNR due to the receiver's internal noise. If the antenna presents a thermal noise power of $N_0 = k T B$ (where $k$ is Boltzmann's constant, $T$ is temperature in Kelvin, and $B$ is bandwidth), and the receiver has noise figure $F$, the total output noise power is $F \cdot N_0$. The minimum SNR at the receiver output is approximately:

$$SNR_{min} \approx \frac{P_r}{F k T B}$$

For a 1 MHz bandwidth receiver at room temperature (290 K) with noise figure 3 dB and received power of −62.4 dBm:

$$P_r = 10^{-62.4/10} \text{ W} = 0.58 \times 10^{-6} \text{ W}$$

$$N_0 = 1.38 \times 10^{-23} \times 290 \times 10^6 = 4.0 \times 10^{-12} \text{ W}$$

$$SNR = \frac{0.58 \times 10^{-6}}{2 \times 4.0 \times 10^{-12}} = 72.5 \approx 18.6 \text{ dB}$$

This SNR may be sufficient for analog communication but is marginal for digital modulation schemes that require 8–12 dB SNR for reliable demodulation at bit error rates of 10^-5 or lower.

The concept of link margin quantifies how much additional path loss (due to shadowing, rain attenuation, or increased distance) a link can tolerate while still meeting its performance requirement. If the minimum SNR required is 10 dB, and the calculated SNR is 18.6 dB, the link margin is approximately 8.6 dB, corresponding to an additional path loss of 8.6 dB or roughly a 2.7× increase in distance (since path loss scales as 20 dB per decade of distance).

### Noise Figure Cascades and Receiver Architecture

In a cascade of RF amplifiers and mixers, the total noise figure is determined primarily by the first stage. Using Friis's formula for noise factor:

$$F_{total} = F_1 + \frac{F_2 - 1}{G_1} + \frac{F_3 - 1}{G_1 G_2} + \frac{F_4 - 1}{G_1 G_2 G_3}$$

If the first stage is a low-noise amplifier with $F_1 = 0.8$ (0.9 dB) and $G_1 = 20$ dB (100 linear), and the second stage is a mixer with $F_2 = 8$ (9 dB) and $G_2 = −7$ dB (0.2 linear):

$$F_{total} = 0.8 + \frac{8 - 1}{100} + \frac{F_3 - 1}{100 \times 0.2} = 0.8 + 0.07 + \frac{F_3 - 1}{20}$$

Even if the third stage has $F_3 = 50$ (17 dB), the contribution to total noise factor is $(50 - 1) / 20 = 2.45$, which corresponds to 3.9 dB. The total noise figure is dominated by the LNA and mixer, with the LNA contributing 0.9 dB and the mixer contributing approximately 0.25 dB (after accounting for the LNA's gain).

This cascading effect drives the architecture of every RF receiver: the LNA must come first, with the lowest noise figure achievable; lossy components like filters and switches must come after the LNA to avoid degrading the noise figure; and the mixer should have good conversion gain (small loss) to prevent subsequent stages from contributing significantly to total noise.

### The Radar Equation

For radar applications, the received power from a target is:

$$P_r = \frac{P_t G_t G_r \sigma \lambda^2}{(4\pi)^3 d^4}$$

In logarithmic form:

$$P_r [dBm] = P_t [dBm] + G_t [dBi] + G_r [dBi] + \sigma [dBsm] + 20 \log_{10}(\lambda) - 30 \log_{10}(4\pi d)$$

The radar cross-section (RCS) $\sigma$ is a property of the target; it has units of square meters and represents the effective area that the target presents to the radar. A sphere of radius $a$ has RCS $\sigma = \pi a^2$; a perfectly conducting flat plate of area $A$ normal to the radar has $\sigma = 4\pi A^2 / \lambda^2$ (due to constructive interference at the specular reflection point). Aircraft RCS typically ranges from 0.1 to 10 square meters depending on aspect angle and frequency.

The minimum detectable signal (MDS) of a radar is related to its noise figure and required SNR:

$$MDS = F k T B + SNR_{required}$$

where $F$ is the noise factor, $k$ is Boltzmann's constant, $T$ is system temperature, $B$ is bandwidth, and $SNR_{required}$ is typically 10–13 dB for detection at probability of detection near unity with false alarm rate near unity per scan.

The maximum detection range occurs when $P_r = MDS$:

$$d_{max} = \left( \frac{P_t G_t G_r \sigma \lambda^2}{(4\pi)^3 \cdot MDS} \right)^{1/4}$$

This fourth-root dependence means that radar range scales as the fourth root of transmitted power, the fourth root of antenna gain, and inversely as the fourth root of noise figure. Doubling transmitted power increases range by a factor of $2^{1/4} \approx 1.19$, or 19%. To double radar range requires a 16-fold increase in power or a 16-fold improvement in noise figure—a profound advantage to placing the radar transmitter and receiver in close proximity and using a single antenna for both transmission and reception (a monostatic radar).

### Effective Aperture and Antenna Efficiency

The effective aperture area $A_e$ of an antenna is the area that captures power from an incident plane wave with power flux density $S$ (in watts per square meter):

$$P_r = S \cdot A_e$$

For a parabolic reflector antenna with physical aperture area $A_{phys}$, the effective aperture is:

$$A_e = \eta_i \cdot A_{phys}$$

where $\eta_i$ is the illumination efficiency. The illumination efficiency accounts for the fact that the feed horn does not uniformly illuminate the entire reflector surface; it tapers toward the edges, reducing the effective area. For a Gaussian illumination pattern (typical of well-designed feeds), $\eta_i \approx 0.65$; for a more uniform illumination, $\eta_i$ can reach 0.80 or higher at the cost of increased side lobes.

The gain of an antenna can be expressed in terms of its effective aperture:

$$G = \frac{4\pi A_e}{\lambda^2}$$

This relationship bridges the concepts of directivity and effective aperture. A high-gain antenna (e.g., a dish antenna) achieves its gain through a large effective aperture, while a small antenna (e.g., a dipole) achieves its directivity through resonant concentration of radiation despite its small physical size.

## 3. High-Performance Optimization & Failure Modes

### System Integration and Link Budget Spreadsheets

Practical microwave system design begins with a link budget spreadsheet that accounts for all gains and losses from transmitter to receiver. Here is a typical structure for a 10 GHz communication link:

| Parameter | Value | Unit |
|-----------|-------|------|
| Transmit Power | 30 | dBm |
| Transmit Cable Loss | −2 | dB |
| Transmit Antenna Gain | 15 | dBi |
| Path Loss (10 km) | −92.4 | dB |
| Receive Antenna Gain | 15 | dBi |
| Receive Cable Loss | −2 | dB |
| Received Power | −64.4 | dBm |
| Receiver Noise Figure | 3 | dB |
| System Temperature (290 K, 1 MHz BW) | −107 | dBm |
| Required SNR (QPSK) | 7 | dB |
| Receiver Sensitivity | −100 | dBm |
| Link Margin | 35.6 | dB |

The link margin of 35.6 dB in this example indicates a robust link with substantial tolerance for rain attenuation, shadowing, or antenna pointing errors. If the required sensitivity is −100 dBm (corresponding to 7 dB SNR in 1 MHz bandwidth), and the calculated received power is −64.4 dBm, the excess margin is 35.6 dB—far more than necessary. A more typical design goal is 3–6 dB link margin, accounting for atmospheric losses and equipment aging.

### Impedance Matching and Return Loss Measurement

In practice, antenna impedance varies with frequency, typically showing a smooth variation around the design frequency. For a half-wave dipole, the impedance versus frequency near resonance can be approximated by:

$$Z(\Delta f) = R_0 + j \frac{2\pi \Delta f}{\Delta f_{BW}} X_{max}$$

where $R_0$ is the resistance at resonance (approximately 73 ohms for a thin dipole), $\Delta f$ is the frequency offset from resonance, $\Delta f_{BW}$ is the −3 dB bandwidth, and $X_{max}$ is the reactance at the bandwidth edge.

Return loss is measured using a network analyzer (scalar or vector). A scalar network analyzer measures the magnitude of the reflection coefficient using a directional coupler or bridge. A vector network analyzer (VNA) measures both magnitude and phase, providing the complex reflection coefficient and impedance. For accurate antenna measurements, the antenna is typically placed in an anechoic chamber (a room lined with RF-absorbing foam to suppress reflections from walls and ceiling) or measured in free space at sufficient distance from ground and other obstacles.

Mismatch loss of 0.1 dB (return loss of 20 dB) is negligible in most designs. Mismatch loss of 0.5 dB (return loss of 13 dB) is noticeable but acceptable. Mismatch loss exceeding 1 dB (return loss of 10 dB) requires design attention. For mission-critical systems, return loss better than 15 dB is standard, corresponding to reflection coefficient magnitude less than 0.178 and mismatch loss less than 0.07 dB.

### Gain Measurement and Antenna Testing

The gain of an antenna is measured using several methods. The most direct is the substitution method: an antenna of known gain is placed in an anechoic chamber with a test transmitter at a fixed distance. The received power is recorded. The test antenna is then substituted in the same location, and the received power is measured again. The gain difference between the test antenna and the reference antenna is:

$$G_{test} = G_{ref} + 20 \log_{10} \frac{P_r^{test}}{P_r^{ref}}$$

This method is accurate but requires a reference antenna and an anechoic chamber. For field measurements or development testing, the far-field pattern can be measured by rotating the antenna and recording the received power as a function of angle. The antenna is placed on a turntable in front of a transmitting horn antenna at a distance of at least $2D^2 / \lambda$ (the Rayleigh distance), where $D$ is the largest dimension of the antenna. At 10 GHz with a 30 cm antenna and wavelength of 3 cm, the Rayleigh distance is 600 meters—impractically large for field testing. Near-field to far-field (NFFF) transformation using a vector network analyzer and antenna model can extend the usable test distance, but this requires sophisticated measurement and data processing.

In the microwave lab, a practical compromise is the compact range, a setup where a curved reflector (often a parabolic mirror) creates a plane wave over a limited volume. This extends the usable test range to 2–10 meters while maintaining a quasi-plane wave condition. Compact ranges are expensive (tens of thousands of dollars) but essential for development of directional antennas above 5 GHz.

### Cascaded System Noise and Sensitivity Calculation

For a receiver with multiple stages (LNA, mixer, IF amplifier), the total noise figure is calculated using Friis's formula. A typical receiver chain at 10 GHz might be:

| Stage | Gain (dB) | Gain (linear) | Noise Figure (dB) | Noise Factor |
|-------|-----------|---------------|-------------------|--------------|
