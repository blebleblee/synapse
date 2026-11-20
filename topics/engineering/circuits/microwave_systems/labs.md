# Operational Verification Labs: Microwave Systems

## Objective & Operational Lab Setup

Microwave systems operate in the electromagnetic spectrum between 300 MHz and 300 GHz, where wavelength dimensions become comparable to physical circuit element sizes, forcing a transition from lumped-element circuit theory to distributed transmission line and waveguide analysis. In this operational regime, conventional voltage and current measurements lose meaning; instead, practitioners must characterize systems through scattering parameters (S-parameters), vector field distributions, and complex impedance transformations along propagation paths. This laboratory guide provides three progressively sophisticated verification exercises that ground the practitioner in real-world microwave measurement techniques, electromagnetic simulation workflows, and hardware debugging protocols essential for RF front-end design, antenna systems, radar transceivers, and high-speed digital interconnects.

The foundational challenge in microwave circuit verification lies in the breakdown of Kirchhoff's voltage and current laws when circuit dimensions approach or exceed λ/10, where λ represents the wavelength at the operating frequency. At 10 GHz, for instance, the free-space wavelength computes to λ = c/f = (3×10⁸ m/s)/(10×10⁹ Hz) = 30 mm, meaning any trace longer than 3 mm begins to exhibit transmission line behavior with phase shifts, reflections, and standing wave patterns that cannot be captured by simple lumped-element SPICE models. Practitioners must therefore adopt field-solver electromagnetic simulation tools, vector network analyzer (VNA) measurement protocols, and time-domain reflectometry (TDR) techniques to characterize impedance discontinuities, insertion loss, return loss, and group delay across the operational frequency band.

The operational lab environment requires both computational electromagnetic (CEM) simulation capacity and physical measurement instrumentation. On the simulation front, practitioners should configure a workstation running either Keysight Advanced Design System (ADS), ANSYS HFSS (High Frequency Structure Simulator), or the open-source OpenEMS finite-difference time-domain (FDTD) solver. HFSS employs the finite element method (FEM) to solve Maxwell's equations in frequency domain, discretizing the geometric structure into tetrahedral mesh elements and computing electric and magnetic field distributions that satisfy boundary conditions at material interfaces. The mesh density directly controls solution accuracy; microwave practitioners typically enforce λ/20 maximum edge length in dielectric regions and λ/30 in metallic skin-depth layers to capture evanescent modes near conductor surfaces. For a 10 GHz simulation in FR-4 substrate (εᵣ = 4.4, tanδ = 0.02), the effective wavelength becomes λₑff = λ₀/√εᵣ = 30 mm/√4.4 ≈ 14.3 mm, requiring mesh edges no larger than 0.7 mm in the dielectric and 0.5 mm near copper traces.

On the measurement front, the laboratory must provide a calibrated vector network analyzer spanning the operational frequency range with sufficient dynamic range to resolve small reflections and low insertion losses. The Keysight PNA-X N5247B (67 GHz, 127 dB dynamic range) or Rohde & Schwarz ZVA67 represent industry-standard choices for sub-18 GHz characterization, while millimeter-wave work up to 110 GHz requires extender modules with waveguide interfaces. VNA calibration constitutes the most critical step in microwave measurement; practitioners must perform full two-port short-open-load-thru (SOLT) calibration using a precision calibration kit to establish reference planes at the coaxial connector interfaces, thereby de-embedding systematic errors including directivity (crosstalk between forward and reverse paths), source match (impedance mismatch at the stimulus port), load match (impedance mismatch at the receive port), reflection tracking (frequency response error in reflection measurements), and transmission tracking (frequency response error in transmission measurements). The mathematical error model expresses measured S-parameters as Sₘₑₐₛᵤᵣₑ𝒹 = E𝒹 + Eₛ·Sₐctᵤₐₗ/(1 - Eₗ·Sₐctᵤₐₗ), where E𝒹 represents directivity, Eₛ source match, and Eₗ load match error terms. A twelve-term error correction algorithm inverts this model to recover Sₐctᵤₐₗ from the measured data.

Physical test fixtures require careful attention to transmission line discontinuities and parasitic coupling. Microstrip test boards should be fabricated on low-loss, tightly-controlled dielectric substrates such as Rogers RO4003C (εᵣ = 3.38 ± 0.05, tanδ = 0.0027 at 10 GHz) with 0.5 oz or 1 oz copper cladding (17.5 μm or 35 μm thickness). The characteristic impedance Z₀ of a microstrip line follows from the distributed inductance and capacitance per unit length, approximated by Z₀ ≈ (87/√(εᵣ+1.41)) · ln(5.98h/(0.8w + t)), where h represents substrate height, w trace width, and t copper thickness. For 50 Ω impedance on RO4003C with h = 0.508 mm (20 mil), the trace width computes to approximately 1.1 mm. SMA edge-launch connectors (Southwest Microwave 292-04A-5 or equivalent) provide the lowest-inductance transition from coaxial to microstrip, with the critical requirement that the center pin solder joint reside directly at the microstrip trace edge without any gap or stub that would introduce a series inductance resonance.

Time-domain reflectometry provides complementary diagnostic capability for locating impedance discontinuities along transmission paths. Modern VNAs implement TDR through inverse Fourier transform of frequency-domain S₁₁ data, converting the reflection coefficient Γ(f) into a time-domain impulse response ρ(t) that reveals the physical location of impedance mismatches. The spatial resolution of TDR measurements depends on the frequency span according to Δz = c/(2·Δf·√εᵣ), meaning a 20 GHz frequency span on RO4003C yields approximately 3.6 mm spatial resolution. Practitioners interpret TDR plots by recognizing that inductive discontinuities (narrow traces, via stubs) produce positive-going reflections, while capacitive discontinuities (wide pads, gap capacitors) generate negative-going reflections.

Throughout these exercises, practitioners will develop fluency in three complementary verification workflows: electromagnetic simulation to predict field distributions and S-parameters from first principles, VNA measurement to characterize fabricated hardware against simulation predictions, and TDR analysis to diagnose and root-cause any deviations between measured and simulated performance. This triangulated approach builds the empirical intuition necessary to debug microwave circuits where parasitic coupling, substrate modes, and connector discontinuities often dominate the measured behavior.

## Exercise 1: Foundational Practical Implementation

### 1.1 Quarter-Wave Impedance Transformer Design and Electromagnetic Simulation

The quarter-wave impedance transformer represents the canonical microwave matching network, exploiting the property that a λ/4 transmission line section converts load impedance according to Zᵢₙ = Z₀²/Z_L, where Z₀ denotes the characteristic impedance of the quarter-wave section and Z_L the load impedance. This transformation property arises from the boundary conditions on voltage and current standing waves at the λ/4 electrical length, where the voltage maximum coincides with the current minimum and vice versa. To design a transformer matching a 50 Ω source to a 100 Ω load at 5 GHz, practitioners must compute the required transformer impedance as Z₀ = √(50·100) = 70.7 Ω and the physical length corresponding to λ/4 at the center frequency.

Begin the simulation workflow by launching ANSYS HFSS and creating a new HFDriven project. Set the solution frequency to 5 GHz and configure the frequency sweep from 4 GHz to 6 GHz with 101 points for fine frequency resolution. Under the 3D modeler workspace, draw the substrate geometry by creating a rectangular box with dimensions 30 mm (length) × 10 mm (width) × 0.508 mm (height, corresponding to Rogers RO4003C 20 mil substrate). Assign this box the material properties of RO4003C by defining a new material with relative permittivity εᵣ = 3.38, loss tangent tanδ = 0.0027, and setting the conductivity to zero since the bulk dielectric loss is already captured by tanδ. Position this substrate box such that the bottom face lies in the z = 0 plane.

Create the ground plane by drawing a second rectangular box with identical x and y dimensions but only 0.035 mm height (1 oz copper), positioned immediately below the substrate with its top face coincident with the substrate's bottom face. Assign this box the material "copper" with bulk conductivity σ = 5.8×10⁷ S/m. The finite conductivity allows HFSS to compute resistive losses from skin effect, where the skin depth at 5 GHz computes to δ = √(2/(ωμσ)) = √(2/(2π·5×10⁹·4π×10⁻⁷·5.8×10⁷)) ≈ 0.94 μm, meaning that current concentrates within the top 1 μm of the copper layer.

On the top surface of the dielectric substrate, sketch the microstrip transformer geometry. The input and output sections require 50 Ω and 100 Ω impedance, respectively. For the 50 Ω input trace on RO4003C with h = 0.508 mm, the trace width calculates to w₅₀ = 1.1 mm using the microstrip impedance formula. For the 100 Ω output trace, the narrower width computes to w₁₀₀ = 0.23 mm. The intermediate 70.7 Ω transformer section requires w₇₀.₇ = 0.54 mm. Compute the physical length of the transformer section by first determining the effective permittivity εₑff = (εᵣ+1)/2 + (εᵣ-1)/2 · (1/√(1+12h/w)) ≈ 2.54 for the 70.7 Ω line, yielding an effective wavelength λₑff = c/(f√εₑff) = 3×10⁸/(5×10⁹·√2.54) = 37.7 mm, so the quarter-wave length becomes L_λ/4 = 9.42 mm.

Draw the complete microstrip trace as a composite path: start with a 5 mm long 50 Ω section (1.1 mm wide) as the input lead, followed by the 9.42 mm long 70.7 Ω transformer (0.54 mm wide), then a 10 mm long 100 Ω output section (0.23 mm wide), and finally another 5 mm long 50 Ω section as the output lead for VNA port attachment. Extrude this 2D path upward by 0.035 mm to create the copper microstrip trace, and assign the copper material. The total structure length spans approximately 29.4 mm, fitting comfortably within the 30 mm substrate.

Define wave ports at the input and output ends by creating rectangular port faces perpendicular to the microstrip trace. Each port face should extend from the ground plane through the dielectric and at least 5h above the substrate to capture the fringing fields. For the h = 0.508 mm substrate, extend the port faces to z = 3 mm. Position the port faces such that they bisect the 50 Ω trace sections at the input and output ends. Right-click each port face and assign a wave port excitation, setting the integration line to run vertically from the ground plane to the top edge of the trace, thereby defining the voltage reference. HFSS will compute the propagating mode on the microstrip line and extract the characteristic impedance from the field solution.

Enclose the entire structure in a radiation boundary by creating a rectangular airbox extending at least λ/4 beyond the substrate edges in all directions. At 5 GHz with free-space wavelength λ₀ = 60 mm, the airbox should extend 15 mm beyond the substrate in ±x and ±y, and 20 mm above the substrate in +z. Assign the outer faces of this airbox as "radiation" boundary conditions, which implement the Sommerfeld absorbing boundary condition to truncate the computational domain without spurious reflections. HFSS will automatically compute scattered fields propagating outward and remove their contribution to the port impedance calculations.

Configure the adaptive mesh refinement by setting the maximum delta S parameter convergence criterion to 0.01, meaning HFSS will iteratively refine the mesh until consecutive solutions differ by less than 1% in S-parameter magnitude. Set the minimum number of adaptive passes to 3 and maximum to 10. Initiate the simulation and monitor the adaptive convergence. On a modern workstation (Intel i9-12900K, 64 GB RAM), the initial mesh will contain approximately 15,000 tetrahedra, growing to 80,000–120,000 tetrahedra at convergence with solution time around 8–12 minutes.

Upon convergence, examine the S-parameter results in the HFSS report window. Plot S₁₁ (return loss) and S₂₁ (insertion loss) in dB magnitude versus frequency from 4 to 6 GHz. The transformer should exhibit minimum return loss at the center frequency of 5 GHz, with S₁₁ ideally approaching -∞ dB at perfect match but realistically achieving -25 to -35 dB due to small discontinuities at the trace width transitions. The insertion loss S₂₁ should remain above -0.5 dB across the band, with the primary loss mechanism being conductor loss in the copper traces and dielectric loss in the substrate. Verify that the 1-dB fractional bandwidth spans approximately 15–20% (750 MHz to 1 GHz), consistent with the quarter-wave transformer's inherent narrowband response.

Create field overlay plots to visualize the electric field magnitude on the substrate surface at 5 GHz. The field intensity should concentrate at the edges of the microstrip traces, with peak values occurring at the narrow 100 Ω section due to the reduced trace width and correspondingly higher current density. Generate a Smith chart plot of S₁₁ to observe the impedance trajectory as frequency varies; at frequencies below 5 GHz, the transformer appears electrically shorter than λ/4, resulting in inductive input impedance (upper Smith chart), while at frequencies above 5 GHz, the transformer appears electrically longer, producing capacitive input impedance (lower Smith chart).

Export the S-parameter data to a Touchstone (.s2p) file for later use in circuit simulation. This file encodes the complex S-parameters at each frequency point in the standard two-port format:

```text
! HFSS S-parameter export: Quarter-wave transformer
# GHz S MA R 50
4.000 0.287 -165.3 0.982 -21.5 0.982 -21.5 0.287 165.3
4.020 0.283 -166.1 0.983 -21.8 0.983 -21.8 0.283 166.1
...
5.000 0.015 82.4 0.997 -90.2 0.997 -90.2 0.015 -97.6
...
6.000 0.263 164.7 0.984 -158.9 0.984 -158.9 0.263 -164.7
```

The Touchstone format specifies frequency in GHz, S-parameters in magnitude-angle (MA) format with magnitude normalized to unity and angle in degrees, and reference impedance of 50 Ω.

### 1.2 Physical Prototype Fabrication and VNA Characterization

Translate the validated electromagnetic simulation into a physical PCB design using Altium Designer, KiCad, or equivalent PCB CAD software. Export the copper layer geometry as Gerber files, ensuring that the trace widths and lengths match the HFSS model dimensions precisely—any deviation of more than 0.05 mm will produce measurable impedance mismatch. Specify the Rogers RO4003C substrate with 0.508 mm (20 mil) thickness in the fabrication notes, along with 1 oz (35 μm) copper cladding and immersion gold (ENIG) surface finish to ensure low contact resistance for SMA connector soldering.

Submit the Gerber files to a PCB manufacturer specializing in RF/microwave fabrication, such as Sierra Circuits, Advanced Circuits, or JLCPCB for prototype quantities. Request controlled impedance fabrication with ±10% tolerance on the 50 Ω traces, and specify impedance test coupons to verify the manufacturer's process control. Typical turnaround time ranges from 5 days for domestic express service to 2 weeks for standard production. Upon receiving the fabricated boards, inspect the copper traces under magnification (10× loupe or stereo microscope) to verify smooth edges without ragged plating or registration errors between layers.

Solder SMA edge-launch connectors (Southwest Microwave 292-04A-5 or Amphenol 901-10512-2) to the input and output ends of the microstrip line. The critical assembly step involves positioning the SMA center pin directly at the edge of the microstrip trace without any gap or stub. Apply flux to both the connector pin and the microstrip pad, then use a temperature-controlled soldering iron set to 340°C with a chisel tip to reflow leaded solder (Sn63Pb37) for 2–3 seconds until a smooth fillet forms. Avoid prolonged heating that could delaminate the copper from the substrate. Solder the four ground tabs of each SMA connector to the bottom ground plane using vias or edge plating, ensuring low-inductance ground return paths. Inspect each solder joint under magnification to confirm complete wetting and absence of solder bridges or cold joints.

Before connecting the device under test (DUT) to the VNA, perform a full two-port SOLT calibration to establish reference planes at the cable ends. Attach the calibration kit (Keysight 85052D or equivalent) to the VNA ports and step through the calibration wizard: first connect the short standard to Port 1 and measure, then the open, then the 50 Ω load, then repeat for Port 2. Finally, connect a thru adapter between ports and measure the direct connection. The VNA firmware will compute the twelve error terms and display the residual directivity, source match, and load match after calibration—these should achieve better than -40 dB directivity and -35 dB match for a quality calibration kit in good condition.

Connect the fabricated quarter-wave transformer to the VNA ports using phase-stable 2.92 mm coaxial cables (Keysight 85133E or equivalent), tightening the SMA connectors to 8 in-lb torque using a torque wrench to ensure repeatable contact resistance. Configure the VNA to sweep from 4 to 6 GHz with 401 points and IF bandwidth of 1 kHz for low noise floor. Set the display format to log magnitude in dB for S₁₁ and S₂₁ on a dual-trace plot. Activate trace averaging with 16 sweeps to reduce measurement noise, particularly important for resolving the return loss null at 5 GHz.

Observe the measured S-parameter traces and compare against the HFSS simulation predictions. The insertion loss S₂₁ should closely track the simulated response, typically within ±0.2 dB across the band, with measured loss slightly higher due to connector transitions and any fabrication tolerances. The return loss S₁₁ will likely exhibit a less deep null than predicted, achieving -20 to -28 dB at 5 GHz rather than the -35 dB simulated value. This degradation arises from several second-order effects: trace width variations from etching tolerance (typically ±0.025 mm), substrate thickness variation (±5% or ±0.025 mm), and connector pin positioning tolerance (±0.1 mm). Each of these perturbations introduces a small impedance mismatch that coherently adds to limit the achievable return loss.

Activate the VNA's time-domain analysis mode to convert the frequency-domain S₁₁ data into a TDR plot showing impedance versus distance. Set the time span to encompass the full length of the transformer, approximately 30 mm or 150 ps delay at the substrate's velocity factor v = c/√εₑff. Apply a low-pass gating function with cutoff at 10 GHz to suppress high-frequency noise. The TDR trace should reveal three distinct impedance regions: the 50 Ω input section appearing as a flat impedance near the reference level, an upward step to 70.7 Ω at the transformer entrance, and a further upward step to 100 Ω at the transformer exit. Any deviations from these ideal impedance levels indicate fabrication errors or connector discontinuities.

To quantify the connector discontinuity, measure a back-to-back SMA connector pair (two connectors soldered directly together without any microstrip trace) and observe the TDR signature. The connector pair will exhibit a small inductive series impedance spike of 2–5 Ω·ps duration, corresponding to the inductance of the solder joint and center pin discontinuity. This connector artifact appears in all subsequent measurements and should be de-embedded by subtracting its S-parameter contribution using the VNA's fixture de-embedding function or offline post-processing in Python using the scikit-rf library.

Document all measured data by exporting the S-parameter traces to Touchstone files and capturing screenshots of the Smith chart and TDR plots. Create a measurement report table comparing simulated versus measured performance metrics:

| Metric | Simulated | Measured | Deviation |
|--------|-----------|----------|-----------|
| S₁₁ @ 5 GHz | -34.2 dB | -26.8 dB | +7.4 dB |
| S₂₁ @ 5 GHz | -0.28 dB | -0.41 dB | -0.13 dB |
| 10 dB return loss BW | 1.24 GHz | 1.18 GHz | -60 MHz |
| Center frequency | 5.000 GHz | 5.032 GHz | +32 MHz |

The center frequency shift of +32 MHz indicates that the fabricated structure is electrically slightly shorter than designed, consistent with the substrate thickness running toward the thin side of the tolerance band or the effective permittivity being marginally lower than the nominal εᵣ = 3.38 value.

### 1.3 Parametric Sensitivity Analysis and Design Centering

To understand which dimensional tolerances most significantly impact performance, return to the HFSS model and conduct a parametric sweep on the critical geometric variables. Define the transformer trace width w_xfmr as a variable ranging from 0.49 mm to 0.59 mm (±0.05 mm around the nominal 0.54 mm), and the transformer length L_xfmr from 9.0 mm to 9.8 mm (±0.4 mm around the nominal 9.42 mm). Set up a nested parametric analysis with 5 steps per variable, yielding 25 simulation runs.

Execute the parametric sweep and generate a contour plot of minimum return loss versus (w_xfmr, L_xfmr). The contour plot will reveal an elliptical region of acceptable performance (return loss < -20 dB) centered on the nominal design point. The major axis of this ellipse typically aligns with the transformer length dimension, indicating that length tolerance exerts greater influence than width tolerance on the matching performance. This sensitivity arises because the transformer's electrical length directly determines the phase relationship between incident and reflected waves, while the width primarily affects the characteristic impedance with a weaker logarithmic dependence.

Quantify the sensitivities by computing partial derivatives of S₁₁ with respect to each parameter at the nominal point. Extract the S₁₁ data at 5 GHz for each parametric point and fit a local quadratic surface S₁₁(w, L) = a₀ + a₁·w + a₂·L + a₃·w² + a₄·L² + a₅·w·L. The linear coefficients a₁ and a₂ represent the first-order sensitivities: ∂S₁₁/∂w ≈ 15 dB/mm and ∂S₁₁/∂L ≈ 28 dB/mm, confirming that length variations have approximately twice the impact of width variations on return loss.

Implement design centering by solving for the (w, L) combination that maximizes the worst-case return loss within the tolerance box. Formulate this as a minimax optimization problem: maximize min(S₁₁(w, L)) over all (w, L) within [w_nom ± 0.05 mm, L_nom ± 0.4 mm]. Solve numerically using the OptQuest optimizer built into HFSS or export the parametric data to MATLAB and employ the fmincon function with appropriate box constraints. The optimized design will typically shift the nominal length slightly longer (9.55 mm instead of 9.42 mm) to center the return loss null within the tolerance distribution, thereby ensuring that worst-case fabricated units still achieve -22 dB or better return loss.

This exercise establishes the complete simulation-to-measurement workflow: electromagnetic field solution predicting S-parameters from Maxwell's equations, physical fabrication translating the design into hardware, VNA characterization validating performance against simulation, and parametric analysis identifying critical tolerances that govern yield. Practitioners now possess the foundational workflow applicable to arbitrary microwave circuit designs, from filters and couplers to antenna feed networks and power dividers.

## Exercise 2: Parameter Variation & Empirical Analysis

### 2.1 Microstrip Low-Pass Filter Design with Stopband Optimization

Microwave filters exploit the frequency-dependent impedance of reactive elements to shape the transmission response, passing desired signal bands while attenuating spurious or harmonic content. In microstrip technology, lumped inductors and capacitors give way to distributed resonators in the form of high-impedance (narrow) and low-impedance (wide) trace sections that approximate series inductance and shunt capacitance, respectively. This exercise develops a fifth-order Chebyshev low-pass filter with 3 dB cutoff frequency at 4 GHz, passband ripple of 0.5 dB, and stopband rejection exceeding 40 dB at 6 GHz, demonstrating the design trade-offs between passband flatness, transition band sharpness, and stopband attenuation depth.

Begin the filter synthesis by computing the normalized lowpass prototype element values for a fifth-order Chebyshev response with 0.5 dB ripple using standard filter tables or the Python scipy.signal.cheby1 function. The prototype ladder network consists of alternating series inductors and shunt capacitors with normalized element values g₀ = 1 (source resistance), g₁ = 1.7058 (series L), g₂ = 1.2296 (shunt C), g₃ = 2.5408 (series L), g₄ = 1.2296 (shunt C), g₅ = 1.7058 (series L), and g₆ = 1 (load resistance). These dimensionless values scale to physical component values through impedance and frequency scaling factors.

Denormalize the prototype to 50 Ω system impedance and 4 GHz cutoff frequency using the transformations L = (R₀·gᵢ)/(2πf_c) for series inductors and C = gᵢ/(R₀·2πf_c) for shunt capacitors, where R₀ = 50 Ω and f_c = 4×10⁹ Hz. This yields physical element values L₁ = 3.40 nH, C₂ = 0.98 pF, L₃ = 5.07 nH, C₄ = 0.98 pF, L₅ = 3.40 nH. In microstrip realization, series inductors become high-impedance narrow trace sections with characteristic impedance Z_high and electrical length θ such that the inductive reactance X_L = Z_high·tan(θ) approximates 2πf_c·L at the cutoff frequency. Choosing Z_high = 100 Ω and solving θ = arctan(2πf_c·L/Z_high) gives electrical lengths θ₁ = 25.8°, θ₃ = 37.7°, θ₅ = 25.8°. Shunt capacitors similarly map to low-impedance wide trace sections with Z_low and electrical length φ such that susceptance B_C = (1/Z_low)·tan(φ) approximates 2πf_c·C, yielding Z_low = 20 Ω and electrical lengths φ₂ = 20.5°, φ₄ = 20.5°.

Convert electrical lengths to physical lengths using the effective permittivity and wavelength relations. For the high-impedance 100 Ω sections on RO4003C with trace width w₁₀₀ = 0.23 mm and substrate height h = 0.508 mm, compute εₑff,high = 2.54 and λₑff,high = c/(f_c·√εₑff,high) = 47.2 mm at 4 GHz. The physical lengths become L₁ = 25.8°/360° × 47.2 mm = 3.38 mm, L₃ = 4.95 mm, L₅ = 3.38 mm. For the low-impedance 20 Ω sections with trace width w₂₀ = 4.2 mm, compute εₑff,low = 2.91 and λₑff,low = 44.0 mm, yielding physical lengths C₂ = 20.5°/360° × 44.0 mm = 2.51 mm, C₄ = 2.51 mm.

Construct the complete filter layout in HFSS by placing the five microstrip sections in cascade: 50 Ω input lead (5 mm), high-Z L₁ section (3.38 mm × 0.23 mm), low-Z C₂ section (2.51 mm × 4.2 mm), high-Z L₃ section (4.95 mm × 0.23 mm), low-Z C₄ section (2.51 mm × 4.2 mm), high-Z L₅ section (3.38 mm × 0.23 mm), and 50 Ω output lead (5 mm). The width transitions between high-Z and low-Z sections create abrupt impedance steps that introduce parasitic shunt capacitance and series inductance, degrading the ideal filter response. To mitigate these discontinuities, implement step compensation by chamfering the trace width transitions with 45° tapers over a length of approximately 0.5 mm, smoothing the field distribution and reducing reflection at each junction.

Simulate the filter structure from DC to 10 GHz with adaptive meshing converging to ΔS < 0.01. The initial simulation will reveal several performance deviations from the ideal lumped-element response: the passband ripple may exceed 0.5 dB due to impedance mismatch at the transitions, the cutoff frequency will shift lower by 100–200 MHz due to parasitic capacitance at the wide sections, and the stopband attenuation will degrade from the ideal response due to higher-order mode coupling and substrate wave propagation. These effects become particularly pronounced at frequencies above 5 GHz where the substrate thickness approaches λ/10 and parallel-plate modes begin to propagate between the microstrip ground plane and any top-side reference planes.

Optimize the filter performance by tuning the section lengths and widths using HFSS's built-in optimizer. Define the design variables as the five section lengths L₁, L₃, L₅, C₂, C₄ with initial values set to the computed physical lengths and allowed to vary ±20%. Specify the optimization goals: S₁₁ < -20 dB from DC to 3.8 GHz (passband match), S₂₁ > -1 dB from DC to 3.8 GHz (passband insertion loss), and S₂₁ < -40 dB at 6 GHz (stopband rejection). Configure the Quasi-Newton optimizer with 50 maximum iterations and convergence tolerance of 0.001. The optimizer will iteratively adjust the section lengths to satisfy the goals, typically requiring 20–30 full-wave simulations over 2–3 hours of computation time.

The optimized design will exhibit several trends: the high-impedance sections lengthen by 5–10% to compensate for the parasitic capacitance at the transitions, the low-impedance sections shorten by 10–15% to account for the additional capacitance from fringing fields at the wide trace edges, and the overall cutoff frequency shifts toward the target 4 GHz. The optimized S-parameter response should achieve passband return loss better than -22 dB, insertion loss of -0.6 to -0.8 dB (dominated by conductor and dielectric loss), and stopband rejection exceeding 45 dB at 6 GHz with the transmission zero occurring near 5.2 GHz.

### 2.2 Fabrication and Statistical Measurement Across Process Variation

Order five copies of the optimized filter design from the PCB manufacturer, requesting that the boards be fabricated across different production panels or batches to capture process variation in substrate thickness, copper plating, and etching profile. This statistical sampling allows empirical characterization of the fabrication tolerances and their impact on filter yield.

Upon receiving the five boards, label them Unit 1 through Unit 5 and measure each unit's physical dimensions using a calibrated digital caliper and optical comparator. Record the substrate thickness at multiple points using a micrometer, the trace widths for each section using the optical comparator with 50× magnification, and the section lengths. Typical measured variations include substrate thickness ranging ±0.020 mm (±4%), high-impedance trace width ranging ±0.015 mm (±6%), and low-impedance trace width ranging ±0.10 mm (±2.4%).

Solder SMA connectors to each unit following the same assembly protocol documented in Exercise 1. Maintain consistent solder joint quality by using the same iron temperature, solder alloy, and heating duration for all units to isolate fabrication variation from assembly variation.

Measure all five units on the VNA using the same calibrated setup, sweeping from DC to 10 GHz with 401 points. For each unit, save the S-parameter data to a uniquely named Touchstone file (filter_unit1.s2p through filter_unit5.s2p) and extract the key performance metrics: 3 dB cutoff frequency f_c, passband return loss worst case RL_pass, insertion loss at 3 GHz IL_3GHz, and stopband rejection at 6 GHz Att_6GHz.

Tabulate the measured results in a statistical summary:

| Unit | f_c (GHz) | RL_pass (dB) | IL_3GHz (dB) | Att_6GHz (dB) |
|------|-----------|--------------|--------------|---------------|
| 1 | 3.94 | -24.3 | -0.72 | -46.2 |
| 2 | 3.98 | -22.1 | -0.68 | -44.8 |
| 3 | 3.91 | -25.7 | -0.75 | -47.1 |
| 4 | 3.96 | -23.5 | -0.70 | -45.5 |
| 5 | 3.93 | -24.8 | -0.73 | -46.8 |
| Mean | 3.94 | -24.1 | -0.72 | -46.1 |
| Std | 0.027 | 1.32 | 0.026 | 0.89 |

Compute the coefficient of variation (CV = σ/μ) for each metric to quantify the relative process stability. The cutoff frequency exhibits CV = 0.69%, indicating tight frequency control despite the dimensional tolerances. The passband return loss shows higher relative variation (CV = 5.5%) because return loss depends exponentially on small impedance mismatches through the relationship RL ≈ -20·log₁₀|Γ|, where Γ = (Z - Z₀)/(Z + Z₀), so a 5% impedance error translates to approximately 1.5 dB variation in return loss.

Overlay all five measured S₂₁ traces on a single plot with different colors to visualize the variation envelope. The passband responses will cluster tightly within ±0.05 dB, while the stopband null locations will spread over a 150–200 MHz range due to the cumulative phase error from dimensional tolerances. This empirical envelope defines the manufacturing yield: if the specification requires f_c = 4.0 ± 0.1 GHz and Att_6GHz > 43 dB, all five units pass, indicating high expected yield (>95%) for this design and fabrication process.

### 2.3 Monte Carlo Tolerance Analysis and Yield Prediction

To predict yield across the full tolerance distributions without fabricating hundreds of units, implement a Monte Carlo simulation in HFSS or MATLAB that randomly samples the geometric parameters according to their statistical distributions and evaluates the resulting S-parameter performance.

Define the dimensional random variables based on the manufacturer's process capability data: substrate thickness h ~ Normal(0.508 mm, 0.013 mm) with ±3σ tolerance of ±0.04 mm, high-impedance trace width w_high ~ Normal(0.23 mm, 0.008 mm), low-impedance trace width w_low ~ Normal(4.2 mm, 0.05 mm), and section lengths with ±2% tolerance. In Python, use numpy.random.normal to generate 500 random samples of the parameter vector [h, w_high, w_low, L₁, L₃, L₅, C₂, C₄].

For each random sample, construct a parameterized HFSS model by passing the sampled dimensions as variables, run the simulation, extract the key metrics, and store the results. This brute-force Monte Carlo approach requires 500 full-wave simulations, consuming approximately 60–80 hours of computation time on a single workstation. To accelerate the analysis, implement a surrogate modeling approach: run 100 strategically chosen HFSS simulations using Latin Hypercube Sampling (LHS) to explore the parameter space, then fit a Gaussian Process Regression (GPR) model that predicts S-parameters as a function of the dimensional parameters. The GPR surrogate trains in minutes and evaluates in milliseconds, enabling rapid Monte Carlo sampling of the remaining 400 points.

Construct the GPR surrogate using the scikit-learn library in Python:

```python
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel

# Load the 100 HFSS simulation results
# X_train: (100, 8) array of [h, w_high, w_low, L1, L3, L5, C2, C4]
# y_train: (100, 4) array of [f_c, RL_pass, IL_3GHz, Att_6GHz]

# Define the GPR kernel with length scales adapted to parameter ranges
kernel = ConstantKernel(1.0) * RBF(length_scale=[0.013, 0.008, 0.05, 0.07, 0.10, 0.07, 0.05, 0.05])

# Train separate GPR models for each output metric
gpr_fc = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-6)
gpr_fc.fit(X_train, y_train[:, 0])

gpr_RL = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-6)
gpr_RL.fit(X_train, y_train[:, 1])

gpr_IL = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-6)
gpr_IL.fit(X_train, y_train[:, 2])

gpr_Att = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-6)
gpr_Att.fit(X_train, y_train[:, 3])

# Generate 500 Monte Carlo samples
X_mc = np.column_stack([
    np.random.normal(0.508, 0.013, 500),  # h
    np.random.normal(0.23, 0.008, 500),   # w_high
    np.random.normal(4.2, 0.05, 500),     # w_low
    np.random.normal(3.38, 0.07, 500),    # L1
    np.random.normal(4.95, 0.10, 500),    # L3
    np.random.normal(3.38, 0.07, 500),    # L5
    np.random.normal(2.51, 0.05, 500),    # C2
    np.random.normal(2.51, 0.05, 500)     # C4
])

# Predict metrics for all Monte Carlo samples
y_mc_fc = gpr_fc.predict(X_mc)
y_mc_RL = gpr_RL.predict(X_mc)
y_mc_IL = gpr_IL.predict(X_mc)
y_mc_Att = gpr_Att.predict(X_mc)

# Compute yield: fraction of samples meeting specs
spec_fc_low, spec_fc_high = 3.90, 4.10  # GHz
spec_RL_min = -20  # dB
spec_Att_min = -43  # dB

yield_mask = (y_mc_fc >= spec_fc_low) & (y_mc_fc <= spec_fc_high) & \
             (y_mc_RL <= spec_RL_min) & (y_mc_Att <= spec_Att_min)

estimated_yield = np.sum(yield_mask) / len(yield_mask)
print(f"Estimated yield: {estimated_yield*100:.1f}%")
```

The Monte Carlo analysis typically predicts 92–97% yield for this filter design with standard PCB fabrication tolerances. To visualize the parameter sensitivities, generate scatter plots of each output metric versus each input parameter, coloring passing samples green and failing samples red. The scatter plots will reveal that substrate thickness h and high-impedance width w_high dominate the cutoff frequency variation, while the low-impedance width w_low primarily affects the stopband rejection depth.

To improve yield, implement centering and tolerance tightening strategies. Centering shifts the nominal design point to the center of the tolerance distribution, maximizing the margin to specification limits in all directions. Tolerance tightening reduces the allowed variation in the most sensitive parameters by specifying tighter fabrication controls, such as requesting ±0.010 mm trace width tolerance instead of the standard ±0.025 mm, at increased fabrication cost. Re-run the Monte Carlo analysis with centered nominal values and tightened tolerances to predict the yield improvement: typically, centering alone increases yield from 95% to 98%, while adding ±0.010 mm width tolerance further increases yield to 99.5%.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### 3.1 High-Power Nonlinear Characterization and Thermal Effects

Microwave circuits operating at high power levels exhibit nonlinear behavior that degrades signal integrity through harmonic generation, intermodulation distortion, and gain compression. These nonlinearities arise from voltage-dependent capacitances in semiconductor junctions, current-dependent inductances in magnetic materials, and conductor resistivity changes with temperature. This exercise characterizes the power handling limits of a microstrip transmission line and quantifies the thermal coefficient of electrical length, demonstrating the measurement techniques necessary for power amplifier design, transmitter output networks, and antenna feed systems.

Begin by fabricating a simple 50 Ω microstrip test line on RO4003C substrate, 50 mm long and 1.1 mm wide, with SMA connectors at both ends. This line serves as the device under test (DUT) for power sweep measurements. Calculate the expected power handling limit from the breakdown field strength of air and the conductor current density limits. The breakdown field in air at atmospheric pressure is approximately E_bd = 3 MV/m, but the actual breakdown mechanism in microstrip occurs in the dielectric substrate, where RO4003C exhibits dielectric strength of approximately 30 kV/mm. For a 0.508 mm substrate thickness, breakdown voltage computes to V_bd = 30 kV/mm × 0.508 mm = 15.2 kV. The peak voltage on a 50 Ω line carrying power P relates through V_pk = √(2·P·Z₀), so the breakdown power is P_bd = V_bd²/(2·Z₀) = (15.2×10³)²/(2·50) = 2.3 MW, vastly exceeding typical microwave signal levels.

The practical power limit arises instead from conductor heating and thermal runaway. The conductor loss per unit length for a microstrip line follows α_c = R_s/(2·Z₀·w), where R_s = √(πfμ₀/σ) represents the surface resistance due to skin effect. At 5 GHz with copper conductivity σ = 5.8×10⁷ S/m, the surface resistance computes to R_s = √(π·5×10⁹·4π×10⁻⁷/5.8×10⁷) = 0.058 Ω, yielding conductor loss α_c = 0.058/(2·50·1.1×10⁻³) = 0.53 Np/m = 4.6 dB/m. For the 50 mm test line, the total conductor loss is approximately 0.23 dB.

The dissipated power in the conductor converts to heat according to P_diss = P_in · (1 - 10^(-α_L/10)), where α is the loss in dB and L the line length. For 1 W input power, the dissipated power computes to P_diss = 1 W · (1 - 10^(-0.23/10)) = 0.052 W = 52 mW. This heat must conduct through the substrate to the ground plane and then to the ambient environment or heatsink. The thermal resistance of the RO4003C substrate follows from Fourier's law: R_th = h/(k·A), where h = 0.508 mm is the substrate thickness, k = 0.71 W/(m·K) is the thermal conductivity, and A = L·w = 50 mm × 1.1 mm = 55 mm² is the area. This yields R_th = 0.508×10⁻³/(0.71·55×10⁻⁶) = 13 K/W. At 52 mW dissipation, the temperature rise computes to ΔT = P_diss · R_th = 0.052 W · 13 K/W = 0.68 K, a negligible value that will not affect circuit performance.

At higher power levels approaching 10–50 W continuous wave (CW), the temperature rise becomes significant. For 10 W input power with 0.23 dB loss, the dissipated power increases to 520 mW, producing a temperature rise of 6.8 K. This temperature rise affects the substrate permittivity through the temperature coefficient of dielectric constant, τ_εr = (1/εᵣ)·(dεᵣ/dT) ≈ -400 ppm/K for RO4003C. The fractional change in permittivity computes to Δεᵣ/εᵣ = τ_εr · ΔT = -400×10⁻⁶/K · 6.8 K = -0.27%, corresponding to a 0.14% change in electrical length and a 7 MHz shift in a 5 GHz center frequency.

To measure this thermal coefficient experimentally, configure a VNA power sweep from -10 dBm to +30 dBm (0.1 mW to 1 W) at a fixed frequency of 5 GHz. Enable port 1 source leveling to maintain constant incident power despite load impedance variations, and set a slow sweep rate (1 point per second) to allow thermal equilibrium at each power level. Monitor the phase of S₂₁ as the input power increases; the phase shift Δφ relates to the electrical length change through Δφ = (2π/λ) · ΔL_eff, where ΔL_eff represents the effective length change due to permittivity shift.

Plot the measured S₂₁ phase versus input power. The phase will exhibit an initial linear region at low power (< 0 dBm) where thermal effects are negligible, followed by a nonlinear roll-off at higher power as the conductor temperature rises. Fit the high-power region to a thermal model: φ(P) = φ₀ + (dφ/dT) · R_th · α · L · P, where φ₀ is the zero-power phase, dφ/dT = -(2π/λ) · L · (1/2εᵣ) · (dεᵣ/dT) represents the phase temperature coefficient, and the product α·L·P gives the dissipated power. Extract the thermal coefficient dεᵣ/dT from the fitted slope and compare against the datasheet value.

Extend the power sweep to higher levels using an external power amplifier (e.g., Mini-Circuits ZHL-16W-43+) capable of +40 dBm (10 W) output. Connect the amplifier output to the DUT through a directional coupler (e.g., Narda 4226-20) to monitor incident and reflected power separately, protecting the VNA receiver from high power. Increase the input power in 1 dB steps up to +37 dBm (5 W) while monitoring both the S₂₁ phase shift and the return loss S₁₁. At sufficiently high power (typically +33 to +37 dBm for a 50 mm microstrip line), the S₁₁ magnitude will begin to degrade from its low-power value as the conductor temperature rises and the impedance drifts due to both permittivity and conductor resistivity changes.

If available, use an infrared thermal camera (FLIR E60 or equivalent) to image the microstrip line surface temperature distribution during the high-power sweep. Position the camera perpendicular to the board surface at a distance of 30 cm and set the emissivity to 0.85 (typical for copper with light oxidation). Capture thermal images at 1 W, 3 W, and 5 W input power after allowing 60 seconds for thermal equilibrium at each level. The thermal images will reveal hotspots at the SMA connector solder joints where the current density concentrates, and a uniform temperature rise along the microstrip trace length. Measure the peak temperature rise using the camera's spot measurement tool and compare against the calculated thermal resistance prediction.

### 3.2 Passive Intermodulation (PIM) Testing and Third-Order Intercept Point

Passive intermodulation (PIM) arises from weak nonlinearities in nominally linear passive components such as connectors, transmission lines, filters, and antennas. These nonlinearities originate from metal oxide semiconductor junctions at connector interfaces (contact nonlinearity), ferromagnetic contamination in plating or hardware (magnetic nonlinearity), and microcracks or loosely bonded interfaces that act as point-contact diodes. PIM products appear as spurious emissions at frequencies f_PIM = m·f₁ ± n·f₂ where f₁ and f₂ are the input carrier frequencies and m, n are integers. Third-order products (m+n=3) are particularly problematic because they fall close to the carriers and cannot be easily filtered.

To characterize PIM in the microstrip test line, employ a two-tone stimulus with carriers at f₁ = 1842.5 MHz and f₂ = 1847.5 MHz, separated by Δf = 5 MHz. The lower third-order product appears at 2f₁ - f₂ = 1837.5 MHz and the upper at 2f₂ - f₁ = 1852.5 MHz, both within the same frequency band as the carriers. Configure a PIM test system consisting of two low-PIM signal generators (Keysight E8257D or equivalent) combined through a low-PIM hybrid combiner (Spinner BN 431841), a high-power amplifier, the DUT, and a low-noise spectrum analyzer with notch filters to suppress the carrier feedthrough.

Set each signal generator to deliver +43 dBm (20 W) at the DUT input, yielding a combined carrier power of +46 dBm (40 W). This high power level is necessary to generate measurable PIM products, typically 100–120 dB below the carrier level for high-quality passive components. Insert 30 dB notch filters (K&L Microwave or TTE Filters) at f₁ and f₂ between the DUT output and the spectrum analyzer to suppress carrier leakage, which would otherwise overload the analyzer input and obscure the PIM products.

Measure the spectrum from 1830 to 1860 MHz with 10 kHz resolution bandwidth (RBW) and 1 Hz video bandwidth (VBW) to maximize sensitivity. The spectrum will display the two carriers at +43 dBm (reduced by the line loss), and two third-order PIM products at 1837.5 and 1852.5 MHz. Measure the PIM product power level P_PIM3 and compute the PIM ratio as PIM3 = P_PIM3 - P_carrier. A well-assembled microstrip line with clean SMA connectors should exhibit PIM3 < -110 dBc at 2×20 W input power.

The PIM level scales with carrier power according to a power law: P_PIM3 = K + 3·P_carrier, where K is a constant depending on the nonlinearity strength. Vary the carrier power from +37 dBm to +43 dBm in 2 dB steps and measure the corresponding PIM3 product level at each power. Plot P_PIM3 versus P_carrier on a log-log scale; the slope should equal 3, confirming the third-order nonlinearity. Extrapolate this line to find the third-order intercept point (IP3), defined as the hypothetical carrier power at which the PIM product would equal the carrier power (P_PIM3 = P_carrier). For a typical microstrip line with good-quality connectors, the output-referenced IP3 (OIP3) computes to approximately +70 to +75 dBm.

To investigate the sources of PIM, systematically replace components in the test setup. First, replace the SMA connectors with new units from a different manufacturer and re-measure PIM3; a change in PIM level indicates that the connectors contribute to the nonlinearity. Then, clean the connector interfaces with isopropyl alcohol and a lint-free swab, removing any oxide layers or contamination, and re-torque to 8 in-lb. Clean connectors typically reduce PIM by 5–10 dB. Next, replace the microstrip test board itself while keeping the same connectors; if PIM remains constant, the board trace is not the dominant PIM source.

For deep PIM troubleshooting, implement a time-gating measurement to spatially locate the PIM source along the transmission path. This technique requires a PIM analyzer with time-domain capability (Anritsu PIM Master MW82119B or Kaelus iPA). The analyzer transmits the two-tone stimulus and receives the third-order product through the same port (reflection mode), measuring the time delay between transmitted pulse and received PIM echo. By gating the time-domain response, the analyzer can resolve PIM sources separated by as little as 1 meter (corresponding to a 10 ns round-trip delay in typical transmission media). This spatial resolution allows identification of specific connectors, solder joints, or discontinuities generating PIM.

### 3.3 Electrostatic Discharge (ESD) Susceptibility and Recovery Verification

Microwave circuits exposed to human handling or electrostatic environments must survive ESD events without permanent damage or performance degradation. The IEC 61000-4-2 standard defines ESD test levels ranging from ±2 kV (Level 1) to ±8 kV (Level 4) for contact discharge, and up to ±15 kV for air discharge. An ESD event delivers a high-voltage, fast-rise-time pulse (< 1 ns rise time) that can punch through thin oxide layers, create microwelds at contact interfaces, or induce latchup in active devices. This exercise establishes an ESD testing protocol for passive microwave structures and verifies functionality recovery after stress.

Configure an ESD simulator (Noseworthy 2000 or Thermo KeyTek MiniZap) to generate contact discharge pulses per IEC 61000-4-2. The simulator charges a 150 pF capacitor through a 50–100 MΩ resistor to the test voltage (e.g., +4 kV for Level 2), then discharges through a 330 Ω series resistor when a discharge tip makes contact with the DUT. This RC network shapes the ESD current waveform to match human body model (HBM) statistics: 7.5 A initial peak current for a 4 kV event, decaying with a 150 ns time constant. The ESD standard requires 10 discharges at each polarity (+4 kV and -4 kV) with 1 second spacing between events to allow the DUT to thermally recover.

Before ESD testing, establish the baseline S-parameter performance by measuring the microstrip test line from DC to 10 GHz with 401 points and saving the reference trace. Note the return loss, insertion loss, and TDR impedance profile as the "known good" state. Apply ESD stress by positioning the simulator discharge tip at the SMA connector center pin of Port 1 while grounding Port 2 through a 50 Ω terminator connected to the test bench ground. Set the ESD simulator to +4 kV contact discharge mode and trigger 10 consecutive discharges with 1 second interval. Visually inspect the connector center pin after the stress; high-voltage discharges may leave visible pitting or discoloration at the contact point.

Re-measure the S-parameters and compare against the baseline. For a passive microstrip line without active protection components, the S-parameters should remain unchanged within measurement uncertainty (< 0.05 dB insertion loss change, < 1 dB return loss change) since the dielectric and conductors can absorb the ESD energy without permanent damage. However, if the ESD tip contacted a solder joint or trace discontinuity where a microgap exists, the high current density (> 10⁵ A/cm²) may create a permanent conductive bridge or weld, slightly degrading return loss. The TDR plot will reveal such damage as a small impedance step or discontinuity at the stressed location.

Repeat the ESD stress at incrementally higher voltages: +6 kV (Level 3), +8 kV (Level 4), and if the device survives, continue to +10 kV and +12 kV to determine the failure threshold. Monitor both the S-parameters and the DC resistance between ports after each stress level. A sudden increase in insertion loss or decrease in DC isolation indicates catastrophic failure, typically from dielectric breakdown creating a conductive path through the substrate or a surface flashover along the substrate edge. Document the failure voltage and inspect the failed device under microscope to identify the failure mechanism: look for carbon tracking along the substrate surface (surface flashover), pinholes in the copper trace (breakdown through the copper), or discoloration in the dielectric (volumetric breakdown).

For designs incorporating ESD protection, implement transient voltage suppressor (TVS) diodes at the RF input/output ports. Select TVS diodes with low capacitance (< 0.5 pF) and appropriate breakdown voltage (VBR > 2×V_signal_max) to clamp ESD transients while presenting minimal parasitic loading to the RF signal. Typical microwave TVS diodes include the Bourns CDSOT23-T05C (5 V breakdown, 0.3 pF) or Littelfuse SP4303 (3.3 V breakdown, 0.35 pF). Connect the TVS diode cathode to the signal trace and anode to ground via a short, low-inductance path (< 2 mm trace length, 0.3 mm via diameter).

Re-test the ESD-protected design using the same contact discharge protocol. The TVS diode will clamp the voltage transient to VBR + I_ESD·R_dynamic, where R_dynamic ≈ 1 Ω represents the diode's dynamic resistance during conduction. For a 4 kV ESD event producing 7.5 A peak current, the clamped voltage computes to approximately 5 V + 7.5 A × 1 Ω = 12.5 V, well below the dielectric breakdown threshold. Measure the S-parameters before and after ESD stress to verify that the TVS diode introduces acceptable parasitic effects: typically -0.3 to -0.5 dB additional insertion loss at 5 GHz due to the diode capacitance shunting some signal to ground, and -18 to -22 dB return loss degradation at the port due to the impedance mismatch introduced by the 0.3 pF capacitance in parallel with the 50 Ω line.

Perform accelerated life testing by applying 1000 ESD pulses at +4 kV with 1 second interval while continuously monitoring the insertion loss. The TVS diode may degrade after repeated high-current transients, with the capacitance increasing by 10–20% due to lattice damage in the semiconductor junction. This capacitance drift will manifest as gradually increasing insertion loss, detectable by comparing the initial and post-stress S₂₁ traces. If the insertion loss increases by more than 0.1 dB after 1000 pulses, the TVS diode has suffered permanent degradation and should be replaced. This accelerated test simulates years of operational handling in a controlled manufacturing or field service environment.

## Operational Reference Guide & Diagnostic Checklist

### VNA Calibration Verification and De-embedding Procedures

Calibration quality directly determines measurement accuracy in microwave characterization. After performing SOLT calibration, verify the calibration health by measuring the through standard and confirming that S₂₁ = 0 dB ± 0.05 dB and S₁₁, S₂₂ < -40 dB across the full frequency band. If the through measurement shows ripple or deviation from ideal, repeat the calibration with fresh cleaning of the calibration standards using isopropyl alcohol and compressed air to remove any residual contamination from the contact surfaces.

For precision measurements requiring better than -50 dB dynamic range, implement enhanced calibration techniques such as electronic calibration (ECal) using an Keysight N4691B or similar automatic calibration module. ECal eliminates operator variability in connector torque and reduces calibration time from 5 minutes to 30 seconds while improving repeatability to ±0.02 dB insertion loss and ±0.5° phase. However, ECal modules have limited power handling (typically +27 dBm maximum), so they cannot be used for high-power measurements requiring SOLT calibration with power-rated standards.

When test fixtures introduce additional transmission line length or discontinuities between the calibration reference plane and the DUT, implement port extension or de-embedding to mathematically shift the reference plane to the DUT terminals. Port extension applies a phase shift to the measured S-parameters corresponding to the electrical length of the fixture, effectively removing the fixture's transmission delay but not its loss or mismatch. The port extension delay τ is set by measuring a known through or short standard at the end of the fixture and adjusting τ until the measured phase aligns with the expected value.

For more accurate de-embedding that removes both phase and amplitude effects of the fixture, measure two-port S-parameters of the fixture alone (with ports connected together through a short adapter) and use the fixture's S-parameter matrix [S_fixture] to mathematically extract the DUT's intrinsic response. The de-embedded DUT S-parameters compute from [S_measured] = [S_fixture,input] × [S_DUT] × [S_fixture,output], solved by matrix inversion: [S_DUT] = [S_fixture,input]⁻¹ × [S_measured] × [S_fixture,output]⁻¹. Implement this de-embedding in the VNA's internal math functions or offline in Python using the scikit-rf library's de-embedding methods.

### Electromagnetic Simulation Troubleshooting and Convergence Diagnostics

When HFSS adaptive meshing fails to converge after 10 passes (ΔS still > 0.02), the root cause typically involves one of three issues: insufficient mesh resolution at critical geometric features, port excitation problems, or radiation boundary placement too close to radiating structures. Diagnose the specific failure mode by examining the mesh density plot and field distribution at the final iteration.

For mesh resolution issues, inspect the mesh around narrow traces, sharp corners, and via transitions. HFSS's automatic meshing may fail to adequately resolve features with high aspect ratio or small critical dimensions. Manually seed these regions by selecting the problematic face or edge and assigning a maximum element length of λ/30 or smaller. Alternatively, use the "On Selection" mesh operation to enforce 3–5 mesh layers through narrow trace widths, capturing the current distribution across the conductor.

Port excitation problems manifest as non-physical field patterns with strong reactive components near the port. The most common error involves placing the wave port integration line incorrectly, not aligned with the expected E-field direction. For microstrip ports, the integration line must run vertically from the ground plane to the top of the trace, not horizontally across the trace width. Visualize the port field pattern by plotting the E-field at the port face; a correct excitation shows a vertical E-field concentrated between the trace and ground, while incorrect excitation produces horizontal or circumferential fields indicating cross-polarization.

Radiation boundary placement becomes critical for antennas and other radiating structures. If the boundary lies closer than λ/4 to the radiating element, near-field reactive energy may interact with the boundary, producing non-physical resonances in the S-parameter response. Incrementally move the radiation boundary outward by λ/8 steps and re-simulate until the S-parameters stabilize, confirming that the boundary lies in the far-field region. The computational cost increases as the boundary volume grows, so balance accuracy requirements against simulation time constraints.

### TDR Interpretation and Fault Localization Techniques

Time-domain reflectometry reveals impedance discontinuities as positive or negative steps in the TDR impedance trace, corresponding to inductive or capacitive perturbations respectively. The spatial location of each discontinuity computes from the time delay τ and the effective velocity of propagation: z = v_eff × τ = (c/√εₑff) × τ. For a microstrip on RO4003C with εₑff = 2.54, the velocity is v_eff = 1.88×10⁸ m/s, so a discontinuity appearing at τ = 150 ps locates at z = 28.2 mm from the reference plane.

The magnitude of the impedance step ΔZ relates to the reflection coefficient Γ through the TDR trace amplitude. For small perturbations where Γ << 1, the impedance change approximates ΔZ/Z₀ ≈ 2Γ. A TDR step of +5 Ω on a 50 Ω line corresponds to Γ = 0.05 and indicates an inductive discontinuity with reactance X_L ≈ ωL ≈ 5 Ω at the measurement frequency. Conversely, a -5 Ω step indicates a capacitive discontinuity with susceptance B_C ≈ ωC such that 1/(ωC) ≈ 5 Ω.

When multiple discontinuities exist, their reflections superpose in the TDR trace, sometimes obscuring individual features. Apply time-domain gating by defining a narrow time window around the discontinuity of interest and zeroing the TDR response outside this window. Transform the gated time-domain data back to frequency domain to observe the S-parameter contribution of just that specific discontinuity, isolating its effect from other parts of the structure. This gated frequency-domain analysis reveals whether a particular discontinuity causes a resonance or degradation at specific frequencies.

For advanced fault diagnosis in high-speed digital interconnects, use differential TDR by simultaneously driving two signal lines with opposite polarity and measuring the differential impedance Z_diff = 2×(Z_even - Z_odd). Differential TDR is sensitive to coupling between traces and reveals common-mode to differential-mode conversion caused by asymmetries in the layout. A perfect differential pair exhibits constant Z_diff along its length, while bends, vias, or asymmetric trace routing produce differential impedance steps indicating signal integrity degradation.

### Microwave Safety Protocols and RF Exposure Limits

Microwave systems operating at power levels above +30 dBm (1 W) require careful attention to personnel safety and compliance with maximum permissible exposure (MPE) limits. The FCC OET Bulletin 65 and IEEE C95.1 standard specify frequency-dependent power density limits to prevent thermal tissue heating. In the most restrictive frequency range (30–300 MHz), the MPE for occupational exposure limits to 1 mW/cm² for controlled environments and 0.2 mW/cm² for general public exposure.

Calculate the far-field power density at distance r from an isotropic radiator using S = P_t·G/(4πr²), where P_t is the transmitted power and G the antenna gain. For a +40 dBm (10 W) transmitter with 0 dBi gain at 5 GHz, the power density at 1 meter distance computes to S = 10 W/(4π·1²) = 0.8 mW/cm², approaching the occupational limit. Increase the distance to r_safe = √(P_t·G/(4π·MPE)) = √(10 W·1/(4π·0.001 W/cm²)) = 28 cm to ensure compliance with the 1 mW/cm² limit.

In laboratory settings, implement administrative controls by posting warning signs at the entrance indicating "RF RADIATION HAZARD" with the frequency, power level, and required safe distance. Install indicator lights that illuminate when transmitters are active, and use key-switch or password interlock on high-power amplifiers to prevent accidental energization. Physically enclose radiating antennas in RF absorber-lined chambers (anechoic chambers) to contain the electromagnetic fields and allow safe work at high power levels.

For bench-level measurements using VNAs and signal generators, the risk is minimal since most equipment operates at milliwatt power levels. However, be aware that VNA harmonic generators for millimeter-wave applications (WR-10, WR-15 waveguide bands) may use frequency multipliers that concentrate several watts of power into submillimeter waveguide apertures, producing extremely high power density (> 100 mW/cm²) in the near field. Never look directly into an energized waveguide aperture, and always terminate unused ports with matched loads to prevent unintended radiation.

Implement proper grounding and bonding to prevent equipment damage from RF current circulating through unintended paths. Connect all equipment chassis to a common ground bus using braided ground straps (< 6 inch length, < 1 Ω DC resistance), and bond the ground bus to building ground through a dedicated earth ground rod. High-power RF amplifiers require particularly robust grounding to sink the large common-mode currents that flow on the chassis during high-power operation; inadequate grounding allows these currents to couple into measurement cables, causing erratic S-parameter readings or damage to VNA inputs.

### S-Parameter Data Processing and Post-Measurement Analysis

Export measured S-parameter data from the VNA to Touchstone (.s2p, .s4p) format for post-processing in circuit simulation tools or numerical analysis software. The Touchstone format supports multiple representations: magnitude-angle (MA), real-imaginary (RI), and dB-angle (DB), with the most common being MA format for general-purpose use and RI format for mathematical processing that requires addition or multiplication of S-parameters.

In Python, load and manipulate S-parameter files using the scikit-rf library:

```python
import skrf as rf

# Load a two-port S-parameter file
ntwk = rf.Network('filter_measured.s2p')

# Extract individual S-parameters as complex arrays
s11 = ntwk.s[:, 0, 0]  # reflection at port 1
s21 = ntwk.s[:, 1, 0]  # transmission from port 1 to port 2
freq = ntwk.f / 1e9    # frequency in GHz

# Compute derived quantities
return_loss = -20 * np.log10(np.abs(s11))
insertion_loss = -20 * np.log10(np.abs(s21))
vswr = (1 + np.abs(s11)) / (1 - np.abs(s11))
group_delay = -np.diff(np.unwrap(np.angle(s21))) / (2*np.pi*np.diff(ntwk.f))

# Plot return loss and insertion loss
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
ax1.plot(freq, return_loss, label='Return Loss')
ax1.set_ylabel('Return Loss (dB)')
ax1.set_xlabel('Frequency (GHz)')
ax1.grid()
ax1.legend()

ax2.plot(freq, insertion_loss, label='Insertion Loss', color='orange')
ax2.set_ylabel('Insertion Loss (dB)')
ax2.set_xlabel('Frequency (GHz)')
ax2.grid()
ax2.legend()
plt.tight_layout()
plt.savefig('filter_response.png', dpi=300)
```

When comparing simulated and measured S-parameters, overlay the traces on the same plot to visually identify discrepancies. Quantify the agreement using metrics such as mean absolute error (MAE) or root-mean-square error (RMSE) across the frequency band. For narrowband structures like filters, focus the comparison on key metrics: center frequency shift, bandwidth change, and peak return loss, rather than comparing every frequency point where measurement noise dominates.

Cascade multiple two-port networks by multiplying their S-parameter matrices using the chain parameter (ABCD) representation. Convert S-parameters to ABCD parameters using the transformations A = ((1+s11)·(1-s22) + s12·s21)/(2·s21), B = Z0·((1+s11)·(1+s22) - s12·s21)/(2·s21), C = (1/Z0)·((1-s11)·(1-s22) - s12·s21)/(2·s21), D = ((1-s11)·(1+s22) + s12·s21)/(2·s21), where Z0 = 50 Ω. Multiply the ABCD matrices of each network in sequence, then convert the resulting product back to S-parameters to obtain the overall cascade response. This technique enables prediction of system-level performance from individually characterized components.

### Final Diagnostic Checklist for Microwave Circuit Verification

Execute this systematic verification sequence when commissioning any microwave circuit:

**Physical Inspection:**
- Verify substrate material and thickness match design specifications (±5% tolerance).
- Inspect trace widths at 50× magnification: look for ragged edges, undercut, or over-etch.
- Confirm trace-to-ground spacing meets minimum clearance (typically 3× substrate height for microstrip).
- Check solder joints for complete wetting, absence of bridges, and minimal fillet size to reduce parasitic capacitance.
- Verify connector torque: 8 in-lb for SMA, 12 in-lb for 3.5 mm, 5 in-lb for 2.4 mm and 1.85 mm connectors.

**Electrical Characterization:**
- Perform full two-port SOLT calibration with verification of through standard (|S21| = 0 ± 0.05 dB).
- Measure S-parameters from DC to 1.5× highest operating frequency to capture harmonic behavior.
- Check return loss at all ports: S11, S22 < -10 dB minimum, < -20 dB target for well-matched designs.
- Verify insertion loss: compare measured loss against calculated conductor + dielectric loss (± 0.2 dB agreement expected).
- Generate Smith chart plot: impedance locus should remain within the 2:1 VSWR circle across passband.

**Time-Domain Analysis:**
- Convert S11 to TDR: impedance should be flat within ±5 Ω for uniform transmission lines.
- Locate all discontinuities: correlate TDR features with physical geometry (connectors, vias, trace width changes).
- Measure rise time from TDR step response: bandwidth (GHz) ≈ 0.35 / rise_time(ns) for 10-90% definition.

**Parametric Stress:**
- Vary temperature from -20°C to +70°C: measure S-parameter drift (specify thermal chamber or heat gun for localized heating).
- Sweep input power from -10 dBm to maximum rated power: monitor phase shift indicating thermal effects.
- Apply mechanical stress: torque connectors to maximum specification, flex PCB (if flexible substrate), verify no S-parameter change.

**Functional Validation:**
- Inject modulated signals representative of actual use case: measure EVM, adjacent channel power, spectral mask compliance.
- Characterize harmonics and spurious: measure output spectrum with signal generator + spectrum analyzer, verify harmonic suppression > 40 dBc.
- Perform swept-frequency CW interference test: inject CW tone at various offsets, verify no desensitization of receiver chain or spectral regrowth in transmitter.

This hierarchical checklist progresses from simple visual inspection through static S-parameter measurement to dynamic parametric and functional tests, ensuring complete verification coverage across all potential failure modes. Practitioners should document each measurement with timestamped data files and photographs, building a verification dossier that establishes traceability from simulation predictions through fabrication to final measured performance.
