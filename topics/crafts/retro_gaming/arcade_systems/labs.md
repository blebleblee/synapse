# Operational Verification Labs: Arcade Systems

## Objective & Operational Lab Setup

The operational verification of arcade systems demands a hybrid discipline combining circuit-level diagnostics, mechanical restoration, software preservation, and playability validation. This laboratory guide advances the practitioner from passive observation to active troubleshooting and empirical analysis of authentic arcade hardware. Unlike modern gaming systems where firmware updates and virtualization mask underlying failure modes, arcade systems expose their entire operational chain: power supply regulation, cathode ray tube raster geometry, control panel microswitch actuation, PCB trace integrity, ROM data persistence, and Z80/6502 microprocessor instruction execution. Each subsystem presents distinct failure signatures requiring physical intervention, empirical measurement, and systematic isolation protocols.

The operational environment for arcade system verification replicates the conditions of commercial deployment while incorporating diagnostic instrumentation absent from original installations. The primary subject under test comprises either an authentic arcade cabinet (upright, cocktail, or mini-cab configuration) or an extracted PCB assembly mounted to a test harness with standardized JAMMA (Japan Amusement Machine and Marketing Association) edge connector interface. For practitioners lacking access to complete hardware, the laboratory exercises adapt to surrogate validation platforms including MAME (Multiple Arcade Machine Emulator) with cycle-accurate timing verification, FPGA-based hardware simulation cores, and oscilloscope analysis of reference signal waveforms captured from known-good systems.

The baseline toolchain comprises a Fluke 87V digital multimeter with true RMS measurement capability for AC ripple analysis on power rails, a Rigol DS1054Z four-channel oscilloscope (minimum 50 MHz bandwidth) for composite video signal inspection and clock frequency verification, a Hakko FX-888D temperature-controlled soldering station for component-level repair, a ROM programmer (TL866II Plus or equivalent) for EPROM data extraction and validation, and a logic analyzer (Saleae Logic 8 or DSLogic Plus) for address/data bus state capture during boot sequences. Mechanical diagnostics require a Mitutoyo digital caliper for joystick throw measurement, a gram-force gauge for microswitch actuation verification, and a lux meter for monitor brightness calibration. Software tools include MAME with debugger extensions, ROMident hash database for ROM verification, and WinIPAC or equivalent for control interface mapping.

The laboratory space must provide adequate ventilation for soldering flux exhaust and CRT high-voltage discharge protocols. A grounded ESD-safe workbench prevents electrostatic damage to CMOS logic and early MOS technology ICs. Ambient lighting should permit clear visual inspection of solder joints and PCB trace integrity while remaining sufficiently dim for accurate CRT convergence and color purity assessment. All AC mains connections to arcade hardware must route through an isolated variac transformer to prevent inrush current damage during initial power-on verification and to facilitate controlled voltage sag stress testing.

## Exercise 1: Foundational Practical Implementation

### Power Supply Rail Verification and Load-Line Characterization

The first operational verification exercise establishes baseline electrical integrity across all power distribution rails. Arcade systems from the golden era (1978–1995) standardized on switching power supplies providing +5 VDC for TTL logic, +12 VDC and –5 VDC for operational amplifiers in audio circuits, and transformer-isolated secondary windings delivering +25 VDC unregulated for CRT deflection amplifiers and +6.3 VAC for monitor cathode heaters. Failure modes include electrolytic capacitor ESR (equivalent series resistance) degradation causing excessive ripple voltage, rectifier diode avalanche breakdown under surge conditions, and solder joint thermal fatigue on high-current traces feeding logic arrays.

Begin with the arcade cabinet fully de-energized and disconnected from mains power. Remove the back panel to expose the power supply assembly, typically a linear supply in pre-1985 games or a switching supply in later systems. Identify the main DC output connector supplying the PCB—this may be a Molex power connector, barrier terminal strip, or direct hardwired connection. Using the multimeter in DC voltage mode with black probe connected to chassis ground, measure static voltage at each rail with no load applied. Record the no-load voltages: nominal +5 VDC should read 5.00–5.15 VDC; +12 VDC should measure 11.8–12.3 VDC; –5 VDC (if present) should fall within –4.9 to –5.2 VDC. Deviations beyond ±10% indicate regulator failure or incorrect adjustment potentiometer settings.

With baseline DC levels confirmed, connect the arcade PCB to establish operational load. The current draw varies by game complexity: early titles like Space Invaders consume approximately 2.5 A on the +5 V rail; mid-era vector games like Tempest draw 4–5 A; late-era sprite-based games like Street Fighter II exceed 8 A. Power on the system and immediately measure voltage under load using the multimeter's DC mode. The +5 V rail should remain within 4.90–5.10 VDC; excessive droop below 4.85 V suggests insufficient regulator capacity or damaged output filter capacitors. Simultaneously, switch the multimeter to AC voltage mode (still measuring the +5 V rail referenced to ground) to quantify ripple voltage. Acceptable ripple measures below 50 mV peak-to-peak; values exceeding 100 mV indicate capacitor ESR failure requiring immediate replacement to prevent logic circuit malfunction.

For comprehensive load-line analysis, transfer measurement to the oscilloscope. Connect Channel 1 to the +5 V rail using a proper ground spring clip to minimize inductance; set the vertical scale to 50 mV/division and timebase to 10 μs/division. Trigger on edge with appropriate slope to capture switching transients. The waveform should reveal high-frequency switching noise (typically 20–100 kHz for switching supplies) superimposed on the DC level. Measure peak-to-peak ripple amplitude directly from the scope display. Enable AC coupling and increase vertical sensitivity to 10 mV/division to isolate the ripple component from the DC offset. Capture a reference waveform screenshot for comparison during future diagnostics.

Execute dynamic load testing by rapidly toggling the game into attract mode (no player input) and active gameplay with simultaneous scope monitoring. Observe transient voltage sag during load step increases—the power supply should recover to regulation within 500 μs with minimal undershoot. Excessive ringing or prolonged recovery indicates inadequate output capacitance or instability in the feedback compensation network. Document the worst-case transient amplitude and recovery time for each rail.

Complete the power verification with thermal inspection using a non-contact infrared thermometer. Measure heat sink temperatures on pass transistors (linear supplies) or switching MOSFETs (switching supplies) during sustained operation. Temperatures exceeding 70°C suggest inadequate heatsinking, excessive ambient temperature, or component degradation. Bridge rectifiers should operate below 60°C; electrolytic capacitors must remain under 50°C to prevent accelerated electrolyte dry-out. Mark overheating components for replacement or improved thermal management.

### Video Signal Integrity and Raster Geometry Validation

With electrical power verified, advance to composite video signal analysis and CRT display geometry characterization. Arcade monitors operate on 15 kHz horizontal scan frequency (compared to 31 kHz for VGA) with non-standard resolutions ranging from 256×224 (early titles) to 384×256 (later games). The RGB analog signals swing 0–0.7 V peak-to-peak with 75-ohm source impedance; composite sync combines horizontal and vertical synchronization pulses in a single negative-going signal. Common failure modes include weak color channels due to aging amplifier transistors, geometry distortion from deflection yoke magnetic field asymmetry, and intermittent sync loss caused by failing electrolytic coupling capacitors.

Connect the oscilloscope Channel 1 to the composite sync output on the PCB edge connector (typically pin 13 on JAMMA harness). Set vertical scale to 1 V/division and timebase to 10 μs/division. Trigger on the falling edge of the sync pulse. The waveform should exhibit clean negative-going pulses with –3 to –5 V amplitude relative to ground. Horizontal sync pulses repeat at 15.734 kHz (63.5 μs period) with approximately 4.7 μs pulse width. Vertical sync pulses occur every 16.7 ms (60 Hz refresh) with extended duration exceeding 200 μs to distinguish them from horizontal pulses. Irregular pulse timing indicates failing crystal oscillator or divider chain malfunction in the video generation circuit.

Transfer scope measurement to the red, green, and blue video outputs (JAMMA pins 9, 10, 11). Set the oscilloscope to AC coupling with 200 mV/division vertical scale and 10 μs/division timebase. Trigger on the composite sync channel while displaying one color channel. The video signal should modulate between 0 V (black level) and approximately 0.7 V (full brightness white) with sharp transitions indicating proper bandwidth. Measure rise time from 10% to 90% amplitude—values exceeding 100 ns suggest bandwidth limiting from failing capacitors or inadequate amplifier slew rate. Compare amplitude across all three color channels; discrepancies greater than 20% indicate unbalanced RGB amplifier gains requiring potentiometer adjustment or transistor replacement.

With signal integrity confirmed at the source, validate display raster geometry using the game's built-in test pattern (accessible via DIP switch settings or service menu) or inject an external test pattern generator. The ideal test pattern provides high-contrast grid lines at known pixel intervals, circular geometry for aspect ratio verification, and grayscale ramps for linearity assessment. Power on the monitor and allow 15 minutes warm-up for electron gun cathode stabilization and deflection circuit thermal equilibrium.

Measure geometric distortion using a transparent overlay grid or digital photograph with calibrated reference. The raster should fill the CRT bezel uniformly without edge rolloff, pincushion distortion (inward bowing on vertical edges), or barrel distortion (outward bowing). Quantify linearity by measuring the physical spacing between grid lines at screen center versus corners—variation exceeding 5% indicates deflection yoke misalignment or incorrect horizontal/vertical amplitude settings. Adjust the monitor's horizontal and vertical size controls (typically accessible via potentiometers on the neck board or chassis) to achieve uniform geometry, documenting the final potentiometer positions for future reference.

Assess convergence quality by observing white grid lines at high magnification—each line should comprise perfectly overlaid red, green, and blue components without color fringing. Misconvergence appears as colored halos offset from the intended line position, indicating purity ring misalignment or yoke positioning error. Static convergence errors concentrated at screen center require purity adjustment using the magnetic rings on the CRT neck; dynamic convergence errors increasing toward screen edges necessitate adjustment of the yoke's physical position and tilt angle. Perform purity adjustment only after degaussing the CRT shadow mask using the internal degaussing coil activated during power-on or an external degaussing wand.

Complete display verification by measuring brightness and contrast uniformity. Using a lux meter positioned at screen center, measure luminance during full-white test pattern display. Typical arcade monitors produce 50–100 cd/m² in a darkened environment; values below 30 cd/m² suggest cathode emission decline requiring CRT replacement. Repeat measurements at all four screen corners—uniformity within ±15% indicates proper electron beam focus and acceptable shadow mask condition. Observe for localized burn-in patterns (permanent phosphor discoloration) common in games with static HUD elements; minor burn-in does not affect playability but indicates CRT nearing end of life.

### Control Input Response Mapping and Microswitch Timing Analysis

The tactile interface between player and game software operates through discrete mechanical switches (microswitches, leaf switches) and analog potentiometers (spinner, trackball, steering wheel). Each control type presents distinct failure signatures: microswitches develop contact bounce or inadequate actuation force; potentiometers accumulate resistive track wear causing dead zones; and optical encoders (trackballs, rotary spinners) suffer from contamination of the encoder disk or photointerrupter misalignment. Empirical validation requires both static resistance measurement and dynamic timing analysis under simulated gameplay stress.

Begin with the joystick assembly, typically comprising a four-way or eight-way restrictor gate controlling four leaf-style microswitches for directional input. Disconnect the control panel harness from the PCB and use the multimeter in continuity mode to verify switch operation. With the joystick in neutral position, all four direction switches should read open circuit (infinite resistance). Deflect the joystick fully in each direction while monitoring switch closure—each switch should transition cleanly to low resistance (< 1 ohm) and remain closed throughout the deflection range. Sloppy or intermittent contact indicates worn switch contacts requiring replacement or adjustment of the switch actuator arm position.

Quantify switch actuation force using the gram-force gauge. Position the gauge probe perpendicular to the joystick shaft at the grip location and apply force in each direction while noting the force reading at the instant of switch closure. Arcade-quality microswitches typically actuate at 50–100 grams-force; excessive force (> 150 g) causes player fatigue and indicates binding in the pivot mechanism or excessive switch pre-load. Inadequate force (< 30 g) permits accidental actuation from vibration or light contact. Compare actuation force across all four directions; imbalance exceeding 20% suggests uneven spring tension or misaligned switch mounting.

Advance to dynamic timing analysis by reconnecting the control panel and launching MAME with input logging enabled. Configure the emulator to display frame-accurate input timing: `mame <romname> -input_logging -skip_gameinfo -window`. Enter the game's test mode or attract sequence and execute rapid directional inputs (quarter-circle motions, rapid left-right toggles) while observing the log file output. Each input event records with microsecond timestamp precision, enabling calculation of switch bounce duration and minimum discernible input duration. Clean microswitch operation exhibits zero-bounce transitions completing within 5 ms; bouncing switches reveal multiple state changes spanning 20–50 ms.

For button inputs, execute the same continuity and actuation force tests, then advance to rapid-tap endurance analysis. Configure a metronome or timer to produce 10 Hz pulses and synchronize button presses to the beat, sustaining the sequence for 60 seconds. Monitor MAME input logs to verify 100% registration of all intended presses—missed inputs indicate inadequate switch return force, excessive plunger friction, or capacitive coupling interference on the signal trace. Document the maximum sustained tap rate achieving 100% registration as the button's practical bandwidth limit.

For analog controls (spinner, trackball, steering wheel), measurement shifts from discrete switch timing to quadrature encoder resolution and linearity. Disconnect the trackball from the PCB and connect the X-axis and Y-axis encoder outputs to the logic analyzer, configuring four channels to monitor the A-phase, B-phase, and ground reference for both axes. Manually rotate the trackball at constant velocity and capture the resulting quadrature waveform. Each 90-degree phase shift between A and B channels represents one encoder count; measure the angular distance between consecutive counts using the caliper (if accessible) or by counting visible encoder slots. Typical trackball encoders provide 20–100 counts per revolution; higher resolution improves fine motion control but increases noise sensitivity.

Analyze encoder linearity by plotting instantaneous count rate against constant applied velocity. Non-uniform count intervals indicate mechanical runout in the ball bearing assembly or contamination on the encoder disk. Clean the encoder disk with isopropyl alcohol and compressed air, then repeat the measurement. Persistent non-linearity necessitates bearing replacement or encoder module substitution.

## Exercise 2: Parameter Variation & Empirical Analysis

### DIP Switch Configuration Space Mapping and Behavioral Characterization

Arcade PCBs expose game parameters through dual in-line package (DIP) switches arrayed in banks of 4–8 positions, controlling variables including difficulty level, starting lives, coin-per-credit ratio, bonus award thresholds, and cabinet orientation (upright versus cocktail). Each switch position functions as a binary bit input to the CPU address decoder, with the complete switch bank encoding a multi-bit configuration word. Systematic exploration of this parameter space requires exhaustive enumeration of all valid configurations combined with quantitative measurement of the resulting gameplay metrics: player survival duration, scoring velocity, enemy spawn frequency, and projectile speed.

Locate the DIP switch banks on the PCB, typically positioned near the edge connector for accessibility during cabinet operation. Consult the game's service manual or decode the switch legend silkscreened on the PCB to identify each switch function. For Exercise 2, focus on the difficulty and lives parameters which exert maximal influence on survival probability. Establish a reference configuration representing factory default settings: typically all switches in the OFF position or a documented "medium difficulty" preset.

Configure MAME for automated parameter sweep by creating a configuration script that iterates through all valid DIP switch combinations while capturing gameplay telemetry. The MAME Lua scripting interface enables programmatic control over input generation, state inspection, and metric logging. Create a Lua script that initializes the game, executes a standardized input sequence (recorded from an expert playthrough), and logs performance metrics at 1-second intervals:

```lua
-- Arcade parameter sweep automation script
local function configure_dipswitches(difficulty, lives)
    local ioport = manager:machine():ioport()
    ioport.ports[":DSW0"]:field(0x03):set_value(difficulty)  -- Bits 0-1: difficulty
    ioport.ports[":DSW0"]:field(0x0C):set_value(lives)       -- Bits 2-3: starting lives
end

local function extract_game_state()
    local mem = manager:machine().devices[":maincpu"].spaces["program"]
    local score = mem:read_u24_le(0x9000)           -- Game-specific score address
    local lives = mem:read_u8(0x9010)               -- Lives counter address
    local level = mem:read_u8(0x9015)               -- Current level/wave
    local enemy_count = mem:read_u8(0x9020)         -- Active enemy count
    return score, lives, level, enemy_count
end

local log_file = io.open("parameter_sweep.csv", "w")
log_file:write("difficulty,lives,time,score,lives_remaining,level,enemy_count\n")

for difficulty = 0, 3 do
    for lives = 0, 3 do
        configure_dipswitches(difficulty, lives)
        manager:machine():soft_reset()
        
        local start_time = os.clock()
        while (os.clock() - start_time) < 300 do  -- 5-minute trial
            if emu.framecount() % 60 == 0 then    -- Sample at 1 Hz (60 FPS)
                local score, lives_left, level, enemies = extract_game_state()
                local elapsed = os.clock() - start_time
                log_file:write(string.format("%d,%d,%.1f,%d,%d,%d,%d\n",
                    difficulty, lives, elapsed, score, lives_left, level, enemies))
            end
            emu.wait(1)
            if lives_left == 0 then break end  -- Player defeated
        end
    end
end

log_file:close()
```

Execute the script by launching MAME with Lua plugin enabled: `mame <romname> -plugin luascript -script parameter_sweep.lua -seconds_to_run 300`. The automation completes 16 trials (4 difficulty levels × 4 lives settings) over approximately 80 minutes, generating a CSV file containing time-series data for each configuration. Transfer the CSV to a spreadsheet application or Python environment for statistical analysis.

Construct survival probability curves by plotting the fraction of trials surviving to time *t* as a function of difficulty and starting lives. Fit exponential decay models of the form $P(t) = e^{-\lambda t}$ where $\lambda$ represents the hazard rate—the instantaneous probability of player defeat per unit time. Estimate $\lambda$ for each configuration using least-squares regression on the log-transformed survival data: $\ln(P(t)) = -\lambda t$. Configurations with larger $\lambda$ values impose shorter expected survival durations; quantify the effect size by computing the ratio $\lambda_{\text{hard}} / \lambda_{\text{easy}}$ to measure difficulty scaling.

Analyze scoring dynamics by computing the time derivative of the score trajectory: $\frac{dS}{dt} \approx \frac{S(t+\Delta t) - S(t)}{\Delta t}$. Plot scoring velocity against time for each configuration, observing the transition from rapid early-game accumulation to slower late-game scoring as enemy density increases and player mobility becomes constrained. Compute the area under the scoring velocity curve to obtain cumulative score, then normalize by survival duration to define score efficiency: $\eta = S_{\text{total}} / t_{\text{survive}}$. Efficient play maintains high $\eta$ across all difficulty levels; declining efficiency indicates inadequate adaptation to increased challenge.

Correlate enemy spawn density with player survival by computing the cross-correlation function between enemy count time series and lives-remaining trajectory. Negative correlation (increased enemies preceding life loss) confirms the intended difficulty mechanism; positive or zero correlation suggests spawn logic failure or player strategy exploiting safe zones. Identify critical enemy density thresholds beyond which survival probability drops precipitously—these thresholds inform level design analysis and assist in diagnosing AI behavior anomalies.

### Clock Frequency Perturbation and Timing-Dependent Behavior Quantification

Arcade game software executes on microprocessors clocked at frequencies ranging from 3 MHz (early Z80-based games) to 12 MHz (later 68000-based systems), with gameplay speed directly coupled to CPU clock rate. Unlike modern systems employing delta-time game loops that decouple physics updates from rendering frame rate, classic arcade games execute one simulation step per video frame at fixed 60 Hz update rate. Variations in CPU clock frequency due to crystal aging, temperature drift, or intentional modification produce measurable changes in gameplay tempo: projectile velocities, enemy movement patterns, collision detection windows, and player response requirements all scale linearly with clock frequency.

This exercise quantifies timing-dependent behavior through systematic clock frequency perturbation applied to authentic hardware or cycle-accurate emulation. For hardware testing, access to the CPU clock signal requires identifying the crystal oscillator (typically a metal can package soldered to the PCB with two pins connected to ground and oscillator output). The baseline frequency is stamped on the crystal body (e.g., "6.000 MHz"). Replace the fixed crystal with an adjustable oscillator module providing ±20% frequency range, or inject an external function generator signal through a buffer amplifier to drive the clock input pin.

In MAME, clock frequency adjustment proceeds through command-line parameters modifying the emulated CPU speed: `mame <romname> -cheat -speed <multiplier>` where multiplier scales the base clock (1.0 = nominal, 1.2 = 20% overclock, 0.8 = 20% underclock). For finer control, edit the driver source file to modify the `XTAL()` macro defining the crystal frequency, then recompile MAME with the altered clock value.

Establish the experimental protocol by selecting a representative gameplay segment exhibiting varied mechanics: player movement, projectile firing, enemy AI pathfinding, collision detection, and scoring. Record a reference playthrough at nominal clock frequency using identical input sequences across all frequency variations. For input reproducibility, record player commands to an INP file via MAME's `-record` flag, then replay using `-playback` during each trial: `mame <romname> -playback reference_input.inp -speed <multiplier>`.

Configure the frequency sweep to span 0.7× to 1.3× nominal in 0.05× increments (13 measurement points). At each frequency, capture the following metrics over a standardized 60-second gameplay segment:

1. **Projectile Velocity:** Measure on-screen displacement per frame using pixel counting in recorded video. Extract frames at 60 Hz, overlay a measurement grid, and track a fired projectile across consecutive frames. Compute velocity as $v = \Delta x / \Delta t$ where $\Delta x$ is pixel displacement and $\Delta t = 1/60$ s. Repeat for 10 projectiles per frequency setting and average the results.

2. **Enemy Spawn Interval:** Count the elapsed frame count between consecutive enemy appearances. Extract spawn timestamps from MAME memory watch on the enemy table base address, logging each non-zero entry creation. Convert frame counts to absolute time: $t = N_{\text{frames}} / 60$ s. Construct histograms of inter-spawn intervals for each frequency to characterize spawn process variability.

3. **Collision Window Duration:** Collision detection operates through per-frame overlap testing between sprite bounding boxes. Measure the minimum overlap duration triggering a registered hit by advancing frame-by-frame through a recorded collision event. At reduced clock frequencies, the collision window extends (more frames overlap before objects separate), increasing hit probability. Quantify the relationship by plotting successful collision rate versus clock frequency.

4. **Player Input Latency:** Inject a step input (button press) via the INP file at a known frame index $t_0$. Identify the frame $t_1$ when the game state reflects the input consequence (e.g., projectile spawns). The latency $L = (t_1 - t_0) / 60$ s remains constant in frame count across frequencies but varies in absolute time: $L_{\text{time}} = L_{\text{frames}} / (60 \times f_{\text{multiplier}})$ s.

Construct a comprehensive timing-response matrix by tabulating all metrics against frequency multiplier. Fit linear models to each metric series: $M(f) = M_0 + \alpha(f - 1.0)$ where $M_0$ represents the nominal-frequency value and $\alpha$ quantifies the sensitivity to clock variation. Metrics exhibiting $\alpha \approx 0$ demonstrate timing-independent behavior (frame-locked logic); non-zero $\alpha$ indicates frequency-dependent processes (typically audio synthesis or analog output control).

Validate the linear response model by computing residuals: $r_i = M_i - M(f_i)$. Non-linear behavior appears as systematic curvature in residual plots, suggesting saturation effects (maximum projectile count reached) or discretization artifacts (integer frame count rounding). For critical gameplay parameters like collision detection, non-linear frequency response indicates potential exploits where skilled players manipulate game speed to trivialize challenge.

### Analog Component Tolerance Analysis via Substitution and Drift Simulation

Audio and video signal paths in arcade hardware rely on analog components—resistors, capacitors, operational amplifiers—whose parameter tolerances and temperature coefficients introduce variability in circuit performance. Resistor values carry ±5% tolerance; electrolytic capacitors exhibit ±20% capacitance variation and ESR drift over lifespan; bipolar transistors show $\beta$ (current gain) spread from 100 to 400 within the same part number. This exercise quantifies the sensitivity of observable game characteristics to component parameter variation, enabling identification of critical components whose out-of-tolerance condition degrades playability.

Focus the analysis on the audio amplifier chain, specifically the bass/treble tone control network and final output stage. Locate the schematic diagram in the game's service manual and identify the frequency-shaping network, typically comprising series resistors and capacitors in feedback loops around an operational amplifier (e.g., LM358 or equivalent). The bass control adjusts low-frequency gain via a variable resistor (potentiometer) modifying the cutoff frequency $f_c = 1/(2\pi RC)$; the treble control operates similarly at high frequencies.

Construct an SPICE (Simulation Program with Integrated Circuit Emphasis) model of the audio amplifier using LTspice or ngspice. Transcribe the schematic into a netlist format, defining all component values, operational amplifier model (select a compatible model from the software library), and input/output nodes:

```spice
* Audio Amplifier Stage with Tone Controls
.title Arcade Audio Path Analysis

* Power supply
VCC vcc 0 DC 12
VEE vee 0 DC -12

* Input signal: 1 kHz test tone at 100 mV amplitude
Vin input 0 AC 0.1 SIN(0 0.1 1000)

* Input coupling
C1 input node1 10u
R1 node1 0 47k

* Bass control network (fc ~= 300 Hz)
R2 node1 node2 10k
C2 node2 node3 0.047u
R3 node3 0 {bass_pot}

* Op-amp stage
XU1 node3 node4 vcc vee node5 LM358
R4 node4 0 10k
C3 node4 node5 0.1u
R5 node5 output 1k

* Output load
Rload output 0 8

* Parameter sweep for bass potentiometer
.step param bass_pot 1k 100k 10k

* AC analysis: frequency sweep 20 Hz to 20 kHz
.ac dec 100 20 20k

* Measure output amplitude and phase
.measure AC gain_1k FIND V(output)/V(input) AT=1000
.measure AC fc_3db WHEN V(output)/V(input)=0.707

.end
```

Execute the SPICE simulation with component tolerance analysis by defining each component as a Gaussian random variable: resistors with $\mu = R_{\text{nominal}}$, $\sigma = 0.05 R_{\text{nominal}}$ (5% tolerance); capacitors with $\mu = C_{\text{nominal}}$, $\sigma = 0.20 C_{\text{nominal}}$ (20% tolerance). LTspice implements Monte Carlo analysis via the `.step param` directive combined with random number generation:

```spice
.param mc_run = 0
.step param mc_run 1 100 1  ; 100 Monte Carlo iterations

.param R2_val = {10k * (1 + 0.05 * gauss(0))}
.param C2_val = {0.047u * (1 + 0.20 * gauss(0))}
```

Run the Monte Carlo simulation and extract the resulting distribution of cutoff frequencies. Export the `.measure` results to CSV format and import into a statistics package (Python with scipy.stats, R, or Excel). Construct a histogram of $f_c$ values, then fit a probability density function to characterize the distribution shape. Compute summary statistics: mean, standard deviation, and 90% confidence interval. For the example circuit, expect $f_c$ to distribute approximately log-normally with median near 300 Hz and 90% interval spanning 200–450 Hz.

Translate the simulation results to observable audio characteristics by correlating cutoff frequency shift with perceptual bass response. Generate a set of test audio clips with equalization matching the simulated $f_c$ distribution endpoints (200 Hz, 300 Hz, 450 Hz cutoff frequencies). Play each clip through the arcade cabinet audio system and record the output using a calibrated measurement microphone positioned at the player position (typically 1 m from the speaker). Analyze the recorded audio in the frequency domain via FFT to extract the actual frequency response curve, then overlay the SPICE-predicted response to validate model accuracy.

Extend the analysis to aging-related component drift by modeling electrolytic capacitor ESR increase over operational lifetime. Electrolytic capacitors exhibit exponential ESR growth following the Arrhenius equation: $\text{ESR}(t) = \text{ESR}_0 \exp(Bt)$ where $B$ depends on operating temperature and applied voltage ripple. Typical ESR doubling time ranges from 5,000 hours (low-quality capacitors in hot environments) to 50,000 hours (premium capacitors in ventilated installations). Modify the SPICE model to include series resistance representing aged capacitor ESR, then re-run AC analysis to observe degraded frequency response (reduced high-frequency gain, increased distortion).

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Thermal Stress Profiling and Component Failure Prediction

Arcade cabinets enclose power supplies, CRT monitors, and game PCBs within confined volumes with limited ventilation, producing internal ambient temperatures 15–25°C above external conditions. Sustained operation at elevated temperatures accelerates electrolytic capacitor aging, induces thermal expansion mismatch in solder joints (especially at high-power components), and degrades semiconductor junction characteristics. This exercise subjects the arcade system to controlled thermal stress while monitoring component temperatures, power consumption, and failure precursor signatures to establish thermal operating margins and predict maintenance intervals.

Instrument the system with Type-K thermocouples positioned at critical thermal hotspots: power supply heatsinks, CRT neck board, PCB voltage regulator, and enclosed cabinet air. Use a multi-channel data logger (Omega OM-USB-TC or equivalent) sampling at 0.1 Hz resolution to capture temperature evolution. Augment fixed thermocouples with a thermal imaging camera (FLIR E4 or smartphone attachment) for full-field temperature mapping during transient events.

Establish baseline thermal profile by operating the game continuously for 2 hours in a controlled ambient environment (22±2°C) with cabinet ventilation fans operational. Record steady-state temperatures at all instrumented points. Typical thermal rises above ambient: power supply heatsink +30°C, CRT neck board +25°C, voltage regulator +20°C, internal air +15°C. Plot temperature versus time for each sensor, identifying thermal time constants by fitting exponential approach to steady state: $T(t) = T_{\infty} + (T_0 - T_{\infty})e^{-t/\tau}$ where $\tau$ represents the thermal time constant (typically 15–30 minutes).

Impose the first stress condition by obstructing cabinet ventilation: cover or disconnect exhaust fans while maintaining operation. Monitor temperature rise rate $dT/dt$ immediately following fan disablement. Steady-state temperatures increase 8–15°C relative to baseline, with hotspot-to-ambient differential reaching +45°C. Establish the maximum safe operating duration at elevated temperature by monitoring for early failure indicators: visual capacitor bulging (check power supply electrolytics every 10 minutes), sync signal jitter (continuous oscilloscope monitoring), or color purity drift (photographic documentation at 15-minute intervals).

If any failure precursor appears, immediately restore ventilation and allow 30-minute cooldown before proceeding. Document the elapsed time to failure indicator and the maximum temperature reached. For healthy systems, internal temperatures stabilize below component absolute maximum ratings (105°C for electrolytic capacitors, 125°C for voltage regulators) even with obstructed ventilation, though sustained operation under such conditions reduces lifespan predictably.

Quantify lifespan reduction using the Arrhenius acceleration factor: $AF = \exp\left[\frac{E_a}{k}\left(\frac{1}{T_{\text{rated}}} - \frac{1}{T_{\text{stress}}}\right)\right]$ where $E_a$ is activation energy (typically 0.6–0.7 eV for electrolytic failure), $k$ is Boltzmann's constant ($8.617 \times 10^{-5}$ eV/K), and temperatures are in Kelvin. For a capacitor rated at 85°C junction temperature operating at 100°C, the acceleration factor $AF \approx 3.2$, reducing the expected 5,000-hour lifetime to approximately 1,560 hours.

Advance to active thermal cycling stress by alternating between powered operation and forced cooling cycles. Power on the system to steady-state, then remove AC power and direct high-velocity airflow (shop fan or compressed air) at the PCB to achieve rapid cooldown. Monitor temperature decay rates and identify components exhibiting slow thermal response (large thermal mass or poor heat sinking). Repeat the power-on/cool-down cycle 20 times over 4 hours while logging temperature and visually inspecting solder joints for crack initiation at high-stress interfaces (large components, high-current traces).

Thermal cycling induces fatigue in solder joints through coefficient of thermal expansion (CTE) mismatch between PCB substrate (FR-4 glass-epoxy, CTE ~17 ppm/°C), copper traces (CTE ~17 ppm/°C), and component leads (Alloy 42 iron-nickel, CTE ~5 ppm/°C for through-hole, or solder ball interfaces for surface-mount). Each thermal cycle accumulates incremental strain, with failure occurring after $N_f$ cycles following the Coffin-Manson relationship: $N_f = C(\Delta \epsilon)^{-n}$ where $\Delta \epsilon$ is strain range and $C$, $n$ are material constants. Practical field data suggests 10,000–50,000 thermal cycles to failure for leaded components with $\Delta T$ = 50°C.

Conclude thermal stress testing with power supply load dump analysis. Configure an electronic load (BK Precision 8500 series or equivalent) to simulate maximum PCB current draw on the +5 V rail, then execute rapid load steps from 25% to 100% to 0% while monitoring output voltage transient response. Inadequate output capacitance or failing regulators produce voltage spikes exceeding ±10% during load dump, potentially latching up CMOS logic. Capture transients on the oscilloscope and measure maximum overshoot/undershoot amplitude and recovery time.

### ESD Susceptibility Mapping and Circuit Protection Validation

Electrostatic discharge events occur when players contact metal cabinet components (coin door, control panel) after accumulating body charge from synthetic carpet or low-humidity environments. Human body model (HBM) ESD events deliver 1–4 kV pulses through 1.5 kΩ series resistance with sub-100 ns rise times, coupling into PCB traces and potentially inducing latchup in CMOS logic, gate oxide rupture in MOSFETs, or data corruption in RAM. This exercise quantifies ESD susceptibility at exposed cabinet interfaces and validates protection circuits against IEC 61000-4-2 Level 3 (6 kV contact discharge, 8 kV air discharge) standards.

Procure an ESD simulator (Noseworthy ESD-2010 or Keytek MiniZap) providing calibrated discharge voltages from 1 kV to 10 kV with selectable output impedances matching HBM, machine model (MM), or charged device model (CDM). For budget-constrained scenarios, construct a DIY ESD generator from a piezoelectric igniter (extracted from a grill lighter) delivering ~15 kV air discharge through a 330 pF capacitor and 2 kΩ resistor to approximate HBM characteristics.

Identify ESD entry points on the cabinet: metal coin door, joystick shaft, button tops, marquee mounting screws, and power switch. For each entry point, trace the electrical path to PCB ground: coin door typically connects to chassis ground via mounting screws; joystick shaft connects to control panel ground plane; button terminals connect directly to PCB inputs through ribbon cable. Map the ground return path using multimeter continuity mode, verifying that chassis ground ties to PCB ground at a single star-point connection to prevent ground loops.

Configure the game PCB in operational state with the monitor powered on and game in attract mode. Set the ESD simulator to 4 kV HBM mode (typical human body charge in 30% relative humidity). Apply contact discharge directly to the coin door metal surface while observing game behavior. Document any observable effects: screen corruption, game reset, audio glitch, or complete lockup. Increment ESD voltage in 1 kV steps from 2 kV to 8 kV, identifying the threshold voltage producing reproducible upset.

For each failure mode, employ the oscilloscope to capture the coupled transient on PCB traces. Connect the scope probe tip to test points near suspected vulnerable components (RAM data lines, interrupt inputs, clock lines) using the shortest possible ground connection to minimize inductance. Set the trigger to edge mode with threshold at ±2 V from nominal logic levels. Apply ESD injection while capturing the transient waveform. Analyze the pulse amplitude, rise time, and duration. Typical unprotected traces exhibit 10–50 V spikes lasting 50–200 ns, exceeding the ±0.5 V noise immunity margin of TTL logic.

Retrofit ESD protection by installing transient voltage suppression (TVS) diodes at entry points lacking protection. Select bidirectional TVS diodes with clamping voltage below the protected device's absolute maximum rating: 5.5 V clamping for 5 V logic, 13 V for 12 V power rails. Popular devices include ON Semiconductor 1.5KE series (1500 W peak pulse power) or Littelfuse SP720 series (array format for multi-line protection). Install the TVS diode between the exposed metal surface and circuit ground, with leads as short as possible (< 10 mm) to minimize parasitic inductance.

Re-test ESD susceptibility post-retrofit, confirming that 8 kV contact discharge produces no observable malfunction. Capture oscilloscope traces at protected nodes, verifying clamped voltage remains within safe operating area. The TVS diode limits voltage to ~6 V with sub-1 ns response time, preventing damage while shunting ESD current harmlessly to ground.

Extend the analysis to air discharge testing by configuring the ESD simulator in air discharge mode and approaching the target surface with the discharge tip at 10 mm standoff distance. Air discharge couples energy capacitively and magnetically without direct galvanic contact, exciting resonant modes in PCB traces and cable harnesses. Apply 8 kV air discharge to all exposed surfaces while monitoring for upset. Air discharge typically exhibits lower coupling efficiency than contact discharge but can excite high-Q resonances in unshielded cables (video sync lines, control panel ribbon cables) producing ringing transients exceeding 20 V.

Mitigate air discharge coupling by installing ferrite beads on susceptible cables. Select beads with high impedance at the ESD pulse spectrum (30–300 MHz): Fair-Rite 2643625002 provides ~1000 Ω impedance at 100 MHz. Install one bead per cable near the PCB connector, ensuring the bead encloses all conductors. Re-test air discharge susceptibility; ferrite beads attenuate coupled transients by 10–20 dB, typically sufficient to prevent upset.

### Power Anomaly Injection and Brownout Recovery Characterization

Public arcade installations experience mains power quality disturbances including voltage sags during motor starting (HVAC compressors, building elevators), transient surges from inductive load switching, and complete outages during utility faults. Arcade power supplies must tolerate these anomalies without data corruption or component damage, implementing brownout detection and graceful shutdown protocols. This exercise injects controlled power disturbances while monitoring system response, identifying minimum acceptable voltage thresholds, hold-up time capacities, and recovery behavior.

Insert a manual variac transformer (Superior Electric Powerstat or equivalent, minimum 1 kVA rating) between the AC mains outlet and arcade cabinet power cord. The variac permits continuous adjustment of output voltage from 0–130% of nominal (0–156 VAC for 120 VAC mains). Install an AC voltmeter on the variac output to display instantaneous voltage; alternatively, use the oscilloscope in AC-coupled mode to monitor voltage waveform distortion during transients.

Establish the nominal operating point by configuring the variac to deliver 120 VAC and powering on the arcade system. Allow 5 minutes for thermal stabilization, then confirm all functions operate normally: display brightness adequate, audio output clear, controls responsive, gameplay smooth. Begin gradual voltage reduction by adjusting the variac downward in 5 VAC increments at 30-second intervals while observing system behavior. Document the voltage at which each anomaly appears:

- **Audio Distortion (115–110 VAC):** Amplifier clipping or modulation distortion as power supply regulation degrades.
- **Display Brightness Reduction (110–100 VAC):** CRT high-voltage multiplier output drops, reducing beam current and screen luminance.
- **Sync Instability (100–95 VAC):** Horizontal or vertical sync pulse amplitude inadequate, producing rolling or tearing artifacts.
- **Logic Malfunction (95–85 VAC):** Voltage regulator dropout causes +5 V rail to sag below 4.75 V minimum, inducing RAM data errors, erratic CPU execution, or complete lockup.

Record the brownout threshold voltage producing first logic malfunction. Quality arcade power supplies tolerate down to 90 VAC (25% under-voltage) without upset; marginal supplies fail at 100–105 VAC. If the system exhibits brownout below 100 VAC, suspect aging filter capacitors or inadequate regulator design requiring component-level repair or power supply replacement.

Advance to transient dropout testing by configuring the variac to nominal voltage, then rapidly rotating the adjustment knob to zero and immediately returning to nominal. This simulates a momentary interruption lasting 50–200 ms (depending on operator reaction time). Observe whether the system maintains operation (indicating adequate hold-up time) or resets. The hold-up time $t_{\text{hold}}$ depends on energy storage in the power supply's bulk capacitors: $t_{\text{hold}} = \frac{C(V_{\text{max}}^2 - V_{\text{min}}^2)}{2P_{\text{load}}}$ where $C$ is total capacitance, $V_{\text{max}}$ is peak rectified voltage (~170 V for 120 VAC mains), $V_{\text{min}}$ is minimum voltage sustaining regulation (~100 V), and $P_{\text{load}}$ is system power consumption (~100 W for typical arcade game).

For a power supply with 470 μF bulk capacitance, $t_{\text{hold}} \approx \frac{470 \times 10^{-6}(170^2 - 100^2)}{2 \times 100} \approx 33$ ms. This hold-up time covers typical utility fault clearing times (16–20 ms for one AC cycle interruption) but not extended outages. If observed hold-up time significantly undershoots the calculated value, suspect dried-out or failing capacitors requiring replacement.

Measure hold-up time precisely using the oscilloscope to monitor the +5 V DC rail while disconnecting AC mains. Capture the voltage decay waveform and identify the time from mains disconnection to the instant the +5 V rail drops below 4.75 V (regulator dropout threshold). Compare measured hold-up time against specification; deviation exceeding 30% indicates capacitor degradation.

Execute overvoltage stress testing by increasing variac output to 130 VAC (110% nominal), then 140 VAC (117% nominal), while monitoring for failure modes: overheating components, insulation breakdown arcing (snapping sounds), or smoke indicating catastrophic failure. Modern arcade power supplies incorporate overvoltage protection (OVP) crowbar circuits that trigger at 130–150% nominal, shorting the input to blow the fuse and prevent downstream damage. If OVP activates, observe the fuse clearing and replace it with an identical type and rating (typically 3 AG slow-blow, 5 A rating). If the system operates at 140 VAC without protection activation, add external overvoltage protection via a metal-oxide varistor (MOV) across the AC input terminals: Littelfuse V130LA10AP clamps at 184 V with 70 J energy absorption capacity.

Conclude power anomaly testing with surge immunity validation using a surge generator (KeyTek Surge Generator) injecting IEC 61000-4-5 standard surges: ±1 kV differential mode (line-to-neutral) and ±2 kV common mode (line/neutral-to-ground). Apply 10 surges of each polarity while monitoring for system upset, component damage, or fuse clearing. Arcade systems with MOV input protection and proper chassis grounding should withstand Level 3 surge testing (2 kV common mode) without malfunction.

## Operational Reference Guide & Diagnostic Checklist

### Systematic Fault Isolation Decision Tree

When confronting an inoperative or malfunctioning arcade system, effective diagnosis proceeds through hierarchical isolation of subsystem failures rather than component-level shotgun replacement. Begin at the power supply (the foundation of all operation), advance to video synchronization and display, verify CPU and ROM integrity, then isolate peripheral control inputs. Each decision node presents a binary test with clearly defined pass/fail criteria, progressively narrowing the fault domain.

**Power Supply Verification (Decision Node 1):**
- **Test:** Measure DC voltages at JAMMA edge connector: +5 V (pins 3, 4, C, D), +12 V (pin 9), -5 V (pin E).
- **Pass Criteria:** +5 V = 4.90–5.10 V, +12 V = 11.8–12.3 V, -5 V = -4.9 to -5.2 V.
- **Fail Action:** If all rails absent, verify AC mains at power supply input, check fuse continuity, inspect for catastrophic component failure (burnt resistors, bulging capacitors). If specific rail absent, isolate failed regulator or rectifier stage via schematic tracing and component substitution.

**CPU Clock and Reset (Decision Node 2):**
- **Test:** Probe CPU clock input pin with oscilloscope; verify continuous square wave at specified frequency (typically 3–12 MHz) with 40–60% duty cycle.
- **Pass Criteria:** Clock amplitude >3.5 V peak-to-peak, frequency within ±5% of specification, reset line held at logic high (>4 V) after power-on.
- **Fail Action:** If clock absent, check crystal oscillator output, verify load capacitors intact. If reset stuck low, trace reset circuit to power-on reset capacitor or watchdog timer, check for shorted decoupling capacitor or failed supervisor IC.

**Program ROM Verification (Decision Node 3):**
- **Test:** Extract ROM chips and read contents via ROM programmer, compute checksum or MD5 hash, compare against known-good database (MAME ROM set, operator manual specification).
- **Pass Criteria:** Hash matches reference exactly, no read errors during extraction.
- **Fail Action:** If read errors occur, clean ROM socket contacts with DeoxIT D5 spray and retry. If hash mismatch, reprogram EPROM with verified binary image or replace mask ROM with 27C EPROM equivalent.

**Video Sync and Timing (Decision Node 4):**
- **Test:** Monitor composite sync output at JAMMA pin 13; verify 15.734 kHz horizontal sync and 60 Hz vertical sync present with correct pulse widths.
- **Pass Criteria:** Horizontal pulses 4.7 μs width repeating at 63.5 μs interval; vertical pulses >200 μs width repeating at 16.7 ms interval.
- **Fail Action:** If sync absent, probe video timing generator IC inputs (clock, enable lines), verify address decoder enabling the video section. If sync malformed, check load capacitors on sync driver output, verify termination resistor at monitor input (typically 75 Ω).

**RGB Video Amplitude (Decision Node 5):**
- **Test:** Inject test pattern (color bars or grid), measure RGB output voltages at JAMMA pins 9, 10, 11 during white display.
- **Pass Criteria:** Each channel 0.5–0.7 V peak amplitude, balanced within ±10% across channels.
- **Fail Action:** If one channel weak, isolate RGB amplifier transistor or video DAC resistor ladder, check for open coupling capacitor. If all channels weak, verify video enable signal, check common emitter resistor in amplifier stage.

**Control Input Registration (Decision Node 6):**
- **Test:** Launch game service mode, execute input test displaying real-time switch status. Actuate each control while observing on-screen response.
- **Pass Criteria:** Each input registers immediately upon actuation, releases cleanly upon release.
- **Fail Action:** If specific input dead, verify switch continuity, check pull-up resistor to +5 V at input buffer. If multiple inputs erratic, inspect edge connector pin contact, verify ground continuity between control panel and PCB.

### Critical Component Lifetime Expectancy Reference

Arcade systems comprise components with vastly differing failure rates and aging mechanisms. Scheduled replacement of wear-prone components prevents catastrophic failures during operation and extends overall system reliability. The following table codifies typical lifespan expectations under normal operating conditions (8 hours per day, 70°F ambient, adequate ventilation):

| Component | Typical Lifespan | Failure Mechanism | Replacement Indication |
|-----------|------------------|-------------------|------------------------|
| Electrolytic capacitors (power supply) | 5,000–10,000 hours | Electrolyte evaporation, ESR increase | Voltage ripple >100 mV, bulging case, leakage |
| Electrolytic capacitors (PCB signal path) | 10,000–20,000 hours | Capacitance loss | Sync instability, audio distortion |
| CRT phosphor | 20,000–50,000 hours | Phosphor aging, cathode emission decline | Brightness <50% of specification, color shift |
| Switching power supply MOSFET | 50,000+ hours | Gate oxide degradation, thermal cycling | Overheating, regulation failure, audible switching noise |
| Microswitches (control panel) | 1,000,000–5,000,000 actuations | Contact wear, spring fatigue | Inconsistent actuation force, contact bounce >20 ms |
| Joystick assembly (mechanical) | 500,000 cycles | Pivot bearing wear, spring set | Excess play (>1 mm), binding, non-centering |
| Battery (SRAM backup, RTC) | 5–10 years | Self-discharge, electrolyte dry-out | High score loss, clock reset on power cycle |
| Fan bearing (brushless) | 20,000–40,000 hours | Lubricant evaporation | Audible noise, reduced airflow, vibration |

Implement scheduled maintenance based on cumulative operating hours tracked via electromechanical hour meter installed on the cabinet power input. At 5,000-hour intervals, perform:
1. Visual inspection of all electrolytic capacitors for bulging or leakage.
2. ESR measurement of power supply bulk capacitors using ESR meter (Peak Atlas ESR70 or equivalent); replace any capacitor exceeding 3× datasheet ESR.
3. Monitor brightness measurement and comparison to baseline; plan CRT replacement when luminance drops below 60% of initial value.
4. Microswitch actuation force audit; replace any switch deviating >30% from specification.

At 10,000-hour intervals, execute comprehensive power supply refurbishment: replace all electrolytic capacitors regardless of measured condition (preventive replacement), clean PCB and heatsinks of accumulated dust, verify fan operation and replace if bearing noise audible.

### Emergency Recovery and Data Preservation Protocols

Catastrophic failures during operation—complete power loss, CPU crash, ROM corruption—threaten loss of game state, high score data, and operator revenue accounting. Robust arcade systems implement non-volatile storage for critical data (battery-backed SRAM, EEPROM) and watchdog timer circuits detecting CPU lockup. Understanding these protection mechanisms enables emergency recovery and data salvage when primary systems fail.

**Battery-Backed SRAM Preservation:** High score tables and game settings reside in volatile SRAM powered by a lithium coin cell (CR2032, 3 V, 220 mAh capacity) via diode-isolated backup circuit. The battery maintains SRAM contents for 5–10 years of continuous operation. Battery failure appears as high score reset to factory defaults upon power cycling. To preserve data during battery replacement:
1. Power on the game and allow full boot to attract mode.
2. While maintaining AC power, carefully desolder the positive battery terminal (do NOT remove battery completely).
3. Solder a fresh CR2032 battery in parallel with the old battery, observing polarity (positive terminal to diode cathode).
4. Once new battery installed, remove old battery and clean solder pads.
5. Verify high scores persist after power cycle.

Alternatively, extract SRAM data via ROM programmer before battery removal. Identify the SRAM chip (typically 6264, 2 KB × 8-bit static RAM), note the IC socket pinout, and read the chip contents via programmer. Store the binary image file; reprogram after battery replacement if data loss occurs.

**Watchdog Timer Reset Recovery:** CPU lockup due to software bugs or DRAM soft errors triggers the hardware watchdog timer, asserting the CPU reset line to force restart. The watchdog expects periodic "keep-alive" signals from software; absence of keep-alive for >100 ms indicates lockup. Chronic watchdog resets indicate unstable RAM, failing CPU, or corrupted program ROM. Diagnose by:
1. Monitoring the watchdog reset line (typically connected to CPU reset pin) with oscilloscope; observe reset pulse frequency.
2. If resets occur <5 seconds after boot, suspect ROM corruption: extract and verify all program ROMs.
3. If resets occur during gameplay (irregular intervals), suspect DRAM failure: execute RAM test mode via service menu, replace failing RAM chip.
4. If resets correlate with thermal conditions (occurring after 15+ minutes operation), suspect inadequate cooling or thermally-sensitive component failure: apply freeze spray to suspected ICs while monitoring for reset cessation.

**Catastrophic PCB Failure Data Salvage:** If the game PCB suffers irreparable damage (lightning surge, liquid contamination, mechanical impact), recover high score data and settings from the battery-backed SRAM:
1. Carefully extract the SRAM IC from its socket without applying excessive force (use IC extraction tool or gently pry with flathead screwdriver from opposite ends).
2. Insert the SRAM into a ROM programmer or Arduino-based SRAM reader.
3. Read the entire SRAM contents (2 KB typical) and save to binary file.
4. Acquire a replacement PCB (same game and revision).
5. Program a new SRAM chip with the extracted data and install in the replacement PCB.
6. Power on and verify high scores and settings restored.

For games using EEPROM (later 1990s titles), data recovery requires specialized EEPROM programmers supporting in-circuit programming protocols (I²C, SPI). Consult the game's service manual to identify EEPROM type and pinout, then extract data via programmer's software interface before replacing the failed PCB.
