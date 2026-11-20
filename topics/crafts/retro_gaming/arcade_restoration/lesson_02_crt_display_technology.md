# Lesson 2: CRT Display Technology

## 1. First-Principles Intuition & Invariants

There is something almost alchemical about a cathode ray tube. A beam of electrons, bent by magnetic fields measured in fractions of a tesla, strikes a glass face coated in materials derived from rare earth chemistry, and the result is a glowing image that feels, to anyone who grew up in an arcade, more alive than any flat panel that followed it. To restore a CRT-based arcade monitor competently, you have to stop thinking of the display as a commodity component and start understanding it as a precision instrument whose tolerances were established at the factory by engineers who expected it to run eight to twelve hours a day, six days a week, for a decade. That context shapes every decision you will make on the bench.

The foundational invariant of every CRT is the electron gun. Located at the narrow neck of the tube, the gun consists of a heater element that warms a cathode to roughly 700–900 °C, causing it to emit a cloud of electrons through thermionic emission. Those electrons are accelerated toward the face of the tube by a potential difference measured in kilovolts — typically 20–30 kV on a standard arcade monitor, with shadow-mask color tubes sitting closer to 25 kV — and focused into a narrow beam by a series of cylindrical anodes inside the gun assembly. The beam's intensity, and therefore the brightness of the spot it creates on the phosphor screen, is controlled by the voltage on the control grid (G1), which acts as an electronic throttle. This relationship is not linear: the transfer characteristic of a CRT is a power function with an exponent of roughly 2.2, which is why display engineers speak of gamma correction. The game's video hardware pre-distorts the luminance signal to account for this, which means that if your gun bias voltage is drifting, your gamma is wrong, and your image will look either washed out or crushed regardless of how well everything else is adjusted.

The phosphor coating on the inner face of the tube is not a uniform material. In a shadow-mask or aperture-grille color tube, the screen is a mosaic of red, green, and blue phosphor elements arranged in triads or stripes, with each element responding to a specific electron bombardment energy and emitting light in a narrow spectral band. The P22 phosphor family, used in virtually every arcade monitor manufactured from the late 1970s onward, defines those spectral bands: P22R peaks at approximately 625 nm, P22G at 525 nm, and P22B at 460 nm. These are not abstract numbers. They matter to restoration because phosphor persistence — the time the emission tail takes to decay — differs between colors. The blue phosphor in a P22 set has notably shorter persistence than the red, which is why severe burn-in on old arcade monitors tends to show a characteristic blue-depleted ghost: the red and green phosphors have been driven harder at high energy densities, and their emissive efficiency has degraded asymmetrically.

Understanding these invariants before you touch a potentiometer or pick up a degaussing coil is not academic throat-clearing. It is the difference between a technician who adjusts symptoms and a practitioner who corrects causes. Every alignment procedure described in the sections that follow is physically grounded in these properties of electron emission, magnetic deflection, and phosphor chemistry.

---

## 2. Core Architecture & Mechanics

### Raster Scan and the Deflection System

The raster is the architecture of the image. A single electron beam, left to its own devices, would drill a bright hole in the center of the phosphor and destroy it within seconds. The deflection yoke — a saddle-wound assembly of horizontal and vertical coils that slips over the tube neck — imposes ordered motion on that beam by generating time-varying magnetic fields perpendicular to the beam axis. The horizontal coils deflect the beam left and right at the line frequency; the vertical coils sweep it top to bottom at the frame frequency. The result is a systematic scan of the entire screen face, 262 or 263 lines per field in NTSC-timed systems, 312 or 313 in PAL-timed ones, though arcade monitors are often not strictly NTSC or PAL — they are factory-timed to the specific horizontal and vertical frequencies output by a given game's sync circuitry.

The current waveforms that drive deflection are not sinusoidal. The horizontal coils require a precisely shaped sawtooth current, rising linearly during active scan and snapping back during the flyback interval. Generating that sawtooth in an inductive load is nontrivial: the horizontal output transistor (HOT) works with the flyback transformer and a resonant tuning capacitor to produce the required current shape while simultaneously generating the high-voltage supply through flyback action. This dual role of the flyback transformer — simultaneously driving horizontal deflection and generating the final anode voltage — is the reason that horizontal frequency and EHT (Extra High Tension) are coupled in a CRT monitor. If the horizontal frequency drifts, the EHT drifts with it, changing beam focus and image width at the same time. This is why sync stability is not merely a cosmetic issue on an arcade CRT.

The vertical deflection circuit, by contrast, drives its coils with a true sawtooth or parabola-corrected current at the much lower frame rate, typically 60 Hz for North American arcade hardware. The vertical output stage is a linear amplifier, usually built around a dedicated IC such as the LA7837, TDA1170, or equivalent, which compares a ramp generated from the sync pulse against a reference to produce the correct coil current. When this circuit ages, the most common failure is insufficient vertical height — the raster fills only 60–70% of the tube face — caused by an electrolytic capacitor in the pump or bootstrap circuit losing capacitance. The repair is almost always a targeted recapping of the vertical output stage rather than component replacement, and the capacitors involved are invariably in the 47–470 µF range at 25–50 V.

The deflection yoke itself can fail in ways that are easy to misdiagnose. A partial short between turns in the horizontal winding will not necessarily prevent the monitor from scanning; it will appear as an S-curve distortion or a compressed image region that no potentiometer adjustment can correct. Measuring yoke winding resistance and comparing it against the service manual specification — typically 1–4 Ω for the horizontal winding, 10–50 Ω for vertical — will reveal the fault immediately. Yoke replacement on most arcade monitors requires removing the tube from the chassis, loosening the yoke clamp ring, noting the original position and tilt angle precisely with a marker line before removal, and re-seating the replacement to the same angular position before performing convergence.

```text
SIGNAL AND POWER FLOW — ARCADE CRT MONITOR

Video Input (JAMMA/RGB)
         │
         ▼
 ┌────────────────────┐
 │   Sync Separator   │  ← LM1881 / CA3160 or discrete
 │  (H-sync / V-sync) │
 └───────┬────────────┘
         │ Composite sync stripped
         ├─────────────────────────────────────────┐
         ▼                                         ▼
 ┌───────────────┐                       ┌─────────────────┐
 │ Horizontal    │                       │ Vertical        │
 │ Oscillator &  │                       │ Oscillator &    │
 │ Drive Stage   │                       │ Output Stage    │
 └───────┬───────┘                       └────────┬────────┘
         │                                        │
         ▼                                        ▼
 ┌───────────────┐                       ┌─────────────────┐
 │ Horizontal    │  Flyback pulse →      │ Vertical Yoke   │
 │ Output Trans. │ ┌──────────────┐      │ Coils           │
 │ (HOT)         │ │   Flyback    │      └─────────────────┘
 └───────────────┘ │ Transformer  │
                   │  (LOPT)      │──── EHT (~25 kV) → Final Anode
                   └──────┬───────┘
                          │
                   Focus / Screen voltage taps
                          │
                   ┌──────▼───────┐
                   │  Focus Block  │
                   │  (Tripler or  │
                   │   voltage     │
                   │   divider)    │
                   └──────────────┘

RGB Video Signal Path:
         │
         ▼
 ┌────────────────────┐
 │  Video Preamplifier│  ← Brightness / Sub-brightness pots
 │  R, G, B channels  │
 └────────┬───────────┘
          ▼
 ┌────────────────────┐
 │  Cathode Drive     │  ← Individual G1 bias per gun
 │  (3× output stage) │
 └────────┬───────────┘
          ▼
     Electron Guns (R/G/B)
          │
          ▼
     Shadow Mask → Phosphor Triads
```

### High Voltage Regulation and the EHT Circuit

The final anode voltage — referred to in British service literature as EHT — is not generated by a conventional linear or switching supply. It is harvested from the ringing energy stored in the flyback transformer during the horizontal retrace interval. When the HOT switches off at the end of active scan, the energy in the horizontal yoke inductance causes the transformer primary to ring upward; a rectifier diode (usually a stacked string of high-voltage silicon diodes, or an internal high-voltage tripler module) captures that ring and charges the final anode capacitance — which is partly the distributed capacitance of the aquadag coating on the inside and outside of the tube face. The EHT is therefore self-regulating in a loose sense: increased beam current (brighter image) tends to load the flyback, pulling EHT down and reducing beam velocity, which acts as a natural compression limit. This is why very bright arcade images can appear slightly defocused — the EHT has sagged enough to broaden the focal point.

Dedicated EHT regulation circuits appeared on higher-quality arcade monitors, particularly in Nanao chassis (MS-8, MS-9) and the Wells-Gardner 25K7xxx series. These regulators sense the anode voltage through a resistive divider tapped from the focus block and feed back a correction to the horizontal drive pulse width, holding EHT within roughly ±5% across the beam current range. When this regulation loop fails — typically because a resistor in the sensing divider has drifted high due to carbon migration, or because the feedback optocoupler has aged — the EHT climbs under low-beam-current conditions (dark scenes) and falls under high-current conditions (bright full-white screens), producing a visible size breathing effect. Restoring the regulation requires measuring the anode voltage with a properly rated HV probe (minimum 40 kV rating, 1000 MΩ input impedance) and adjusting the EHT trimmer potentiometer — always with the monitor running and after a ten-minute warm-up — to achieve the service manual specification, commonly 24.5–26.5 kV depending on tube size and chassis generation.

### Color Signal Decoding and RGB Drive

Arcade monitors of the vector and raster era almost universally accept analog RGB rather than composite video. The JAMMA harness carries separate R, G, and B analog signals along with composite sync on a single line, eliminating the need for the chroma subcarrier encoding and decoding that burdens consumer television circuits. This is a critical restoration advantage: there is no PAL/NTSC chroma decoder to age, no burst gate to drift, and no color saturation determined by subcarrier amplitude. The color you see is a direct function of the drive voltage on each cathode, subject only to the phosphor and the gun bias adjustment.

Each color channel has two critical adjustments that must be understood as a system, not as independent controls. The drive (or gain) potentiometer sets the amplitude of the video signal applied to the cathode — it determines white balance at peak white. The cutoff (or bias, or sub-brightness) potentiometer sets the DC operating point of the video output stage — it determines the black level for each gun independently. These two controls interact. Setting cutoff first is mandatory: with no video signal present (raster blanked or black screen), adjust each channel's cutoff until the glow from that gun just disappears — this sets the black point. Then introduce a full white signal and use the drive pots to achieve the target color temperature, which on an arcade monitor is conventionally 6500 K (D65), observable as a pure, neutral white with a slight warm cast rather than the blue-biased white of a consumer television.

The practical tool for this procedure is a color analyzer or even a calibrated colorimeter placed at the screen face, but experienced practitioners can achieve a serviceable D65 alignment using a gray step chart and observing the shadow area of the ramp — the first 10–20 IRE region — for color contamination. A gray that shows a magenta tint in its dark regions means the blue cutoff is set too high relative to red and green. A gray that shifts cyan in the shadows means the red cutoff is set too high. These visual heuristics, while less precise than a spectroradiometer, are sufficient for arcade-grade calibration and have been used by field technicians since the 1980s.

### Sync Separation

The sync separator is the monitor's first point of contact with the game board's video signal, and its proper operation is prerequisite to everything else. In most arcade monitors, sync separation is handled by a dedicated IC — the LM1881 is the canonical example, used in Happ, Nanao, and Wells-Gardner chassis across thirty years of production — which strips the horizontal and vertical sync pulses from the composite sync waveform by clipping below the blanking pedestal level and differentiating the resulting pulse train. The LM1881's internal timing is set by an external capacitor on its sync tip clamp pin, and the value of this capacitor determines the IC's ability to separate interlaced versus non-interlaced sync and its noise immunity to narrow glitch pulses. Using the wrong capacitor value — a common mistake when this chip is replaced without consulting the service manual — produces intermittent vertical roll on certain game titles whose sync pulses have unusually short serration periods.

A second failure mode is ground-loop contamination entering the composite sync line from the JAMMA harness. Because JAMMA uses a shared ground rail for logic and video, ground currents from the game board's power supply can induce noise spikes on the sync line that the separator reads as false sync pulses. The symptom is horizontal tearing that varies with the intensity of on-screen action — more enemies, more tearing — because more logic switching generates more ground noise. The correct remedy is a 75 Ω series termination resistor at the monitor's sync input, combined with a small ceramic capacitor (100 pF) to ground, forming a lowpass filter that suppresses spikes without attenuating the sync pulse amplitude below the separator's threshold.

### Convergence: Static and Dynamic

Convergence is the geometric alignment of the three electron beams so that they all strike the same phosphor triad at every point on the screen. Poor convergence manifests as color fringing — a red ghost to the right of a white vertical line, or a green shadow above a horizontal edge — and is visually intolerable on games with text-heavy overlays such as Pac-Man or Galaga. There are two distinct categories of convergence error, each requiring different tools and procedures.

Static convergence is the alignment error at the center of the screen, corrected by magnets mounted on the tube neck. On most color arcade tubes, a set of four- and six-pole plastic magnet assemblies are factory-fitted to the neck between the electron gun and the deflection yoke. Rotating these ring magnets shifts the relative beam positions at the screen center. The procedure requires a crosshatch test signal — either from a dedicated test pattern generator or from a crosshatch PROM socketed into the game board in place of the original graphics ROM — and an observation of color contamination on the central intersection point of the grid. Rotation of the four-pole ring shifts the blue beam relative to the red-green pair in a circular arc; the six-pole ring adjusts the red-green beam convergence. Adjustments interact, so the correct protocol is to iterate between them in small increments rather than attempting to fully correct one before touching the other.

Dynamic convergence is the alignment error that varies across the screen face, introduced by the fact that a flat phosphor screen is not equidistant from the electron gun at all points — the corners are geometrically farther away than the center — and by manufacturing tolerances in the yoke winding. On self-converging tubes (the dominant design from the mid-1970s onward), dynamic convergence is largely handled by the shaped magnetic field of the yoke itself, whose non-uniform winding density is designed to compensate for the beam-landing geometry. If dynamic convergence is unacceptable on a self-converging tube, the primary corrective tool is yoke tilt and shift: loosening the yoke clamp ring and physically translating or rotating the yoke on the tube neck will change the dynamic convergence pattern. The rule of thumb is that tilting the yoke clockwise, as viewed from the rear, shifts the corner convergence error in a predictable rotational pattern that can be mapped against the crosshatch grid.

---

## 3. High-Performance Optimization & Failure Modes

### Burn-In Assessment and Phosphor Recovery Protocols

Burn-in is the archetypal long-term failure mode of arcade CRTs, and it deserves careful assessment before any alignment work begins, because a severely burned tube will never produce a satisfactory image regardless of how well it is adjusted. Burn-in is not uniform phosphor exhaustion — it is localized depletion of emissive efficiency in areas that have sustained prolonged high-intensity bombardment. The classic Pac-Man burn presents as a fixed ghost of the maze layout, faintly visible even when the monitor displays a different game or a solid white field. Pac-Man's static maze elements occupied precisely defined screen positions for years of continuous operation, driving those phosphor regions to depletion while the surrounding area retained close to full efficiency.

Quantifying burn-in severity before attempting recovery establishes a realistic expectation. Connect the monitor to a known-good video source and display a full-raster white field at normal operating brightness. Observe the screen in a darkened room and photograph it. Mild burn (20–30% efficiency loss in the affected region) will show as a barely perceptible shadow. Severe burn (50%+ loss) will show a clearly visible dark ghost that is impossible to attribute to any optical effect. Tubes with severe burn are candidates for replacement, not recovery. Mild to moderate burn responds to the following accelerated phosphor recovery procedure, which works by deliberately running the unused regions at reduced efficiency to partially equalize the screen.

The recovery process runs a white raster at 20–30% of normal brightness — achieved by reducing the screen (G2) voltage on the focus block, not by changing the drive pots, so that the adjustment remains proportional across all three guns — for extended periods between active game play. Some practitioners add a slow-moving random noise or Lissajous pattern source to distribute beam energy across the full screen face rather than holding a fixed white field. Recovery is slow: measurable improvement in a mildly burned tube typically requires 40–80 hours of recovery operation. Set realistic expectations with the cabinet owner before beginning.

### Capacitor Aging and Targeted Recapping Strategy

Electrolytic capacitors are the dominant consumable failure mode in arcade CRT chassis, and the temptation to wholesale-recap every electrolytic on the board — a practice sometimes called a "shotgun recap" — deserves critical examination. Wholesale recapping is appropriate only when a chassis has been in service for more than twenty years without prior service, is showing multiple simultaneous symptoms, or will be installed in a revenue-generating cabinet where downtime is costly. For a chassis with a single identifiable symptom, targeted replacement of the specific capacitors implicated by the failure mode is faster, cheaper, and reduces the risk of introducing new faults through soldering errors or component misidentification.

The vertical output section almost always contains the highest-stress capacitors: the pump capacitor (which bootstraps the vertical output IC's supply rail above the main B+ voltage to allow full vertical swing) is typically a 100–470 µF device at 50 V rated to operate near its voltage ceiling with a high ripple current. Its failure manifests as reduced vertical height and a slight S-distortion near the bottom of the raster. Replacing it with a modern equivalent rated 105°C rather than the original 85°C part is the single highest-value capacitor replacement on most chassis. The horizontal stage contains high-voltage film capacitors for the S-correction and ringing networks; these rarely fail catastrophically but can drift in value enough to shift horizontal linearity. Measuring them in-circuit with an ESR meter (for electrolytics) or a capacitance bridge (for films) before replacement avoids unnecessary board disturbance.

### HOT Failure and Flyback Transformer Diagnosis

The horizontal output transistor is the highest-stress active device in the chassis. It switches the full deflection current through an inductive load at the horizontal frequency, sustaining collector voltage spikes that can reach three to four times the supply voltage during commutation. The damper diode, historically a separate component but integrated into the HOT's die in modern equivalent parts, clamps the reverse swing of the deflection coil and must be verified functional when diagnosing HOT failure. A shorted HOT will blow the chassis fuse immediately on power application; an open HOT will produce no raster and no EHT, but the vertical stage and heater supply will be active. Measuring the HOT collector-emitter saturation voltage during operation with a low-capacitance probe — the measurement must be done on a live chassis, so proper high-voltage safety procedures are absolutely mandatory — provides a direct assessment of transistor health. A saturated collector voltage above 3 V on a device specified at 1.5 V or less indicates impending failure.

Flyback transformer failure is less common than HOT failure but more difficult to diagnose with standard bench equipment. Internal arc-over between the EHT winding and the core manifests as intermittent high-voltage arcing audible as a sharp crack, visible as a blue flash at the tube neck or anode cap, and accompanied by a momentary loss of raster. The arc will eventually carbon-track the internal insulation and produce a permanent partial short. Measuring EHT with an HV probe while deliberately driving the monitor to full-white output stresses the transformer: a sagging EHT that recovers when beam current is reduced suggests marginal regulation, while an EHT that collapses entirely suggests a winding short. Replacement flyback transformers for common chassis (Nanao MS-8, Electrohome G07, Wells-Gardner 7000 series) remain available through arcade parts suppliers such as Bob Roberts' archive-based distributors and Ultimarc's service network; the key specification to verify before ordering is the resonant frequency of the EHT winding, which determines the tuning capacitor required for correct horizontal frequency operation.

### Purity, Degaussing, and Magnetic Contamination

External magnetic fields — from loudspeakers mounted too close to the tube face, from adjacent cabinets, or from ferrous tools left near the tube during storage — magnetize the shadow mask and inner frame of the tube, pulling individual electron beams off their intended phosphor triads and producing large irregular patches of color contamination. This is purity error, distinct from convergence error in that it affects the landing position of all three beams together rather than their relative alignment. The demagnetization procedure uses a degaussing coil — a large toroidal coil carrying 50 or 60 Hz AC current, available in professional versions rated 3–5 A and consumer versions adequate for most arcade tube sizes — applied in a specific sequence: energize the coil at arm's length from the screen, bring it to within 15 cm of the screen face in a slow circular sweeping motion, then withdraw it to arm's length before de-energizing it. The critical rule is that the coil must be withdrawn while energized and must be positioned at least one meter from the tube face before power is removed; stopping or de-energizing the coil close to the tube re-magnetizes the shadow mask in the coil's residual field orientation.

Most arcade monitors include an internal automatic degaussing (ADG) circuit — a thermistor-based posistor network that passes AC line current through a built-in degaussing coil for the first few seconds after power-up, then self-limits as the thermistor heats and its resistance rises. If the ADG posistor has failed open, the internal degaussing is absent and purity errors accumulate with each power cycle. Testing the ADG circuit requires measuring current draw on the AC primary in the first ten seconds of operation: a healthy ADG draws 1–3 A for 5–10 seconds before dropping to the chassis idle current; a failed posistor shows no such transient.

### Geometry Correction and Service Mode Alignment

Geometry errors — pincushion distortion, trapezoid (keystone), tilt, and linearity errors — are corrected by a combination of physical yoke adjustment and potentiometer settings on the chassis board, with the specific controls available depending on the chassis generation. Most arcade chassis provide at minimum: width (adjusting the resonant tuning capacitor or a varicap in the horizontal drive chain), height (vertical gain), vertical and horizontal centering (DC shift to the respective output stages), and pincushion correction (a parabolic current added to the horizontal yoke in proportion to the vertical position). Higher-end chassis such as the Nanao MS-9 add independent north and south pincushion, top and bottom pillow, and EW (east-west) balance controls.

The correct sequence for geometry alignment is invariable. First, establish the proper EHT with an HV probe, because geometry is EHT-dependent. Second, center the raster horizontally and vertically using the appropriate pots. Third, set the correct width and height to fill the visible phosphor area of the tube with an appropriate overscan margin of 3–5%. Fourth, correct pincushion with the pincushion pot. Fifth, correct linearity by observing the crosshatch test pattern and ensuring that grid squares at the screen edges are the same size as those at the center. Attempting to correct linearity before pincushion, or adjusting width before EHT, violates the dependency chain and produces circular adjustments that never converge. Discipline about this sequence is what separates a monitor that is aligned once from one that is adjusted indefinitely.

The completed monitor should be run continuously for a minimum of four hours before final alignment lock-down, because component temperatures stabilize over that period and the EHT, focus voltage, and geometry will all shift slightly from their cold-start values. Performing all final pot adjustments from cold produces a monitor that drifts off-specification within the first hour of game play. This thermal stabilization step is not optional — it is the professional finishing mark that distinguishes a restoration-grade result from a service-call patch.
