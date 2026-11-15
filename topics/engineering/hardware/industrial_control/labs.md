# Operational Verification Labs: Industrial Control

## Objective & Operational Lab Setup

Industrial control systems represent the critical intersection of electrical engineering, real-time computing, and process automation where hardware failures, firmware race conditions, or misconfigured feedback loops can result in catastrophic physical damage, production line shutdowns, or safety incidents. Unlike consumer electronics or general-purpose computing systems, industrial controllers operate in harsh electromagnetic environments with strict timing determinism requirements, often interfacing directly with high-voltage power electronics, pneumatic actuators, and hazardous chemical processes. The operational verification methodologies presented in this laboratory guide emphasize a practitioner-first approach: you will construct representative control loop models, inject realistic disturbances, measure closed-loop stability margins, and validate fail-safe interlock logic using both hardware-in-the-loop simulation and physical bench testing with actual industrial-grade programmable logic controllers.

The laboratory environment requires a hybrid analytical and physical setup. On the analytical side, you will utilize MATLAB Simulink or GNU Octave with control system toolboxes to model plant dynamics, design compensators, and perform frequency-domain stability analysis using Bode plots and Nyquist diagrams. These models will feed parameter sets into embedded firmware written in IEC 61131-3 Structured Text or ladder logic, compiled for Allen-Bradley CompactLogix, Siemens S7-1200, or Modicon M221 PLCs. On the physical bench, you will require a PLC trainer kit with discrete I/O modules (24VDC sourcing/sinking), analog input cards (0–10V, 4–20mA current loop), and at least one variable frequency drive (VFD) or servo amplifier to close actual motor control loops. Diagnostic instrumentation includes a four-channel digital storage oscilloscope with 100MHz bandwidth minimum for observing PWM waveforms and control signal transients, a Fluke 87V or equivalent true-RMS multimeter for validating current loop calibration, and a USB-to-RS485 adapter with Modbus RTU protocol analyzer software such as QModMaster or Modbus Poll for interrogating fieldbus communication integrity.

The environmental prerequisites extend beyond equipment to operational safety protocols. Industrial control hardware operates at hazardous voltages and currents: 120VAC/240VAC mains power feeds VFDs, 24VDC control power can source multiple amperes through short circuits, and inductive loads like motor windings and solenoid coils generate back-EMF transients exceeding 400V during switching events. Before energizing any circuit, you must verify proper earth grounding continuity using a low-resistance ohmmeter, confirm all emergency-stop (E-stop) circuits are wired in series-redundant normally-closed configurations per ISO 13850 safety standards, and validate that arc-flash hazard boundaries are clearly marked with appropriate personal protective equipment staged nearby. The laboratory space must provide industrial-grade DIN rail mounting systems, wire ducting with strain relief provisions, and a dedicated isolated ground bus separate from building structural ground to mitigate common-mode noise injection from switching power supplies and inverter drives.

Software toolchain configuration demands equal rigor. Install MATLAB R2023b or later with Simulink, Control System Toolbox, and Simscape Electrical for continuous-time plant modeling and discrete controller synthesis. For open-source alternatives, deploy GNU Octave 8.3.0 with the control, signal, and symbolic packages, though be aware that Octave's ODE solver suite lacks the stiff-system Rosenbrock integrators required for certain power electronics models. PLC programming environments vary by vendor: Rockwell Automation Studio 5000 Logix Designer for CompactLogix, Siemens TIA Portal V18 for S7-1200/1500 families, or Schneider Electric EcoStruxure Machine Expert Basic for Modicon M221 controllers. Each environment requires vendor-specific USB drivers and Ethernet/IP or Profinet protocol stack installations. For Modbus RTU communication testing, install pyModbusTCP and minimalmodbus Python libraries alongside libmodbus C bindings if developing custom SCADA gateway firmware. Finally, configure PCAP packet capture tools like Wireshark with industrial Ethernet dissector plugins to decode EtherNet/IP CIP messages, Profinet DCP frames, and Modbus TCP function codes during fieldbus diagnostics.

The analytical verification workflow integrates frequency-domain loop stability analysis with time-domain transient response validation. You will begin by deriving continuous-time transfer functions for representative industrial plants: second-order underdamped motor position servos, first-order-plus-dead-time (FOPDT) temperature control loops with thermal transport lag, and higher-order fluid flow processes with integrating dynamics. These transfer functions feed into PID compensator design routines where you will analytically compute proportional, integral, and derivative gains using Ziegler-Nichols ultimate gain tuning, internal model control (IMC) techniques for dead-time compensation, or lambda-tuning methods that explicitly trade servo bandwidth for disturbance rejection robustness. The designed controllers are discretized using Tustin bilinear transformation or backward Euler methods at realistic scan rates—typically 10ms for fast servo axes, 100ms for process control loops, and 1–5ms for current-mode motor drive inner loops—then exported as IEC 61131-3 function blocks with fixed-point arithmetic scaled to PLC integer register widths.

Physical commissioning procedures validate that the analytical models accurately represent real hardware dynamics. You will perform open-loop step response tests by commanding actuator outputs through manual PLC forcing or analog voltage injection, capturing plant response curves on the oscilloscope, and fitting second-order or FOPDT models to the measured data using least-squares parameter estimation in MATLAB's System Identification Toolbox. Discrepancies between model and measurement often reveal unmodeled nonlinearities: mechanical backlash in gearboxes manifesting as rate-dependent phase lag, magnetic saturation in motor iron causing gain compression at high torque commands, or thermal drift in analog sensor signal conditioning circuits shifting zero-offset over minutes-long time scales. These real-world effects demand gain scheduling, adaptive feedforward compensation, or multi-mode controller switching that analytical models alone cannot reveal.

The laboratory exercises progress from foundational single-loop tuning through multi-variable cascade architectures to fault-injection stress testing that deliberately violates operating envelopes. You will quantify closed-loop performance using industry-standard metrics: integral absolute error (IAE) for disturbance rejection, total variation (TV) for actuator wear minimization, and phase margin/gain margin pairs for robustness against plant parameter uncertainty. Boundary failure scenarios include sensor open-circuit faults triggering fail-safe bumpless transfer to backup redundant channels, actuator saturation windup causing integrator reset logic activation, and communication timeout exceptions forcing controllers into predetermined safe-state outputs. By exercising these edge cases under controlled laboratory conditions, you develop the diagnostic intuition required to troubleshoot industrial control systems failures in production environments where downtime costs thousands of dollars per minute and safety interlocks prevent casual experimentation.

## Exercise 1: Foundational Practical Implementation

The foundational exercise establishes a complete single-input-single-output (SISO) control loop encompassing plant modeling, PID compensator design, discrete-time implementation in PLC firmware, and closed-loop commissioning on physical hardware. The selected plant is a permanent-magnet DC motor position servo driving an inertial load through a low-backlash gearbox—a canonical industrial motion control problem appearing in CNC machine tool axes, robotic joint actuators, and packaging line indexing mechanisms. This system exhibits second-order dynamics dominated by rotor inertia and viscous damping, with armature inductance contributing a parasitic pole at frequencies well above the servo bandwidth, making it an ideal testbed for demonstrating PID tuning trade-offs between tracking speed, overshoot suppression, and disturbance rejection.

Begin by constructing the continuous-time plant model from first-principles electrical and mechanical equations. The motor armature circuit obeys Kirchhoff's voltage law: the applied terminal voltage $V_a$ equals the sum of resistive drop $I_a R_a$, inductive voltage $L_a \frac{dI_a}{dt}$, and back-EMF $K_e \omega_m$, where $I_a$ is armature current, $R_a$ and $L_a$ are winding resistance and inductance, $K_e$ is the back-EMF constant, and $\omega_m$ is mechanical shaft speed. Electromagnetic torque $T_e = K_t I_a$ drives the mechanical load equation $J \frac{d\omega_m}{dt} = T_e - B \omega_m - T_L$, where $J$ is total inertia (motor plus load referred to motor shaft), $B$ is viscous damping coefficient, and $T_L$ represents external load torques. Shaft position $\theta_m$ integrates from angular velocity: $\theta_m = \int \omega_m \, dt$. For a representative small servo motor (e.g., Maxon EC45 flat brushless motor with 10:1 planetary gearbox), use the following realistic parameter values: $R_a = 1.2 \, \Omega$, $L_a = 0.8 \, \text{mH}$, $K_e = K_t = 0.042 \, \text{V·s/rad} = 0.042 \, \text{N·m/A}$, $J = 5 \times 10^{-5} \, \text{kg·m}^2$ (motor inertia plus reflected load), and $B = 1 \times 10^{-5} \, \text{N·m·s/rad}$.

Derive the transfer function from applied voltage $V_a(s)$ to shaft position $\Theta_m(s)$ by Laplace-transforming the coupled differential equations. Assuming negligible electrical time constant ($L_a / R_a \approx 0.67 \, \text{ms}$ is much faster than mechanical dynamics), approximate the armature current response as quasi-static: $I_a \approx (V_a - K_e \omega_m) / R_a$. Substituting into the torque equation and combining with the velocity-to-position integrator yields a second-order plant model:

$$G_p(s) = \frac{\Theta_m(s)}{V_a(s)} = \frac{K_t}{R_a J s^2 + (R_a B + K_e K_t) s} = \frac{K_{dc}}{s(\tau_m s + 1)}$$

where the DC gain is $K_{dc} = K_t / (R_a B + K_e K_t) = 0.042 / (1.2 \times 10^{-5} + 0.042^2) \approx 23.4 \, \text{rad/(V·s)}$ and the mechanical time constant is $\tau_m = R_a J / (R_a B + K_e K_t) = (1.2 \times 5 \times 10^{-5}) / (1.2 \times 10^{-5} + 0.00176) \approx 33.5 \, \text{ms}$. This transfer function reveals an integrator pole at the origin (position grows unbounded under constant voltage input) and a real pole at $s = -1/\tau_m \approx -29.9 \, \text{rad/s}$, corresponding to $f = 4.76 \, \text{Hz}$. The plant is type-1 (one integrator), guaranteeing zero steady-state position error to constant reference commands but also requiring derivative action or lead compensation to achieve adequate phase margin.

Implement this plant model in MATLAB Simulink by creating a new model file named `dcmotor_servo.slx`. Drag a Transfer Fcn block from the Continuous library into the canvas and double-click to edit parameters: set Numerator to `[23.4]` and Denominator to `[0.0335 1 0]` to represent the second-order polynomial $0.0335 s^2 + s$. Add a Saturation block (Simulink/Discontinuities) immediately following the transfer function to model the amplifier voltage limit: set Upper limit to `24` and Lower limit to `-24` to reflect a 24VDC power supply rail. Connect a Step block (Sources library) to the plant input, setting Step time to `0`, Initial value to `0`, and Final value to `1.57` radians (90 degrees) to command a representative angular move. Attach Scope blocks (Sinks library) to visualize both the reference step input and the plant position output. Configure the Simulink solver by navigating to Modeling → Model Settings → Solver, selecting Type: Fixed-step, Solver: ode4 (Runge-Kutta), and Fixed-step size: `1e-4` (100 microseconds) to ensure numerical stability for the 30ms mechanical time constant.

Run the open-loop simulation for 0.5 seconds by clicking the Run button. The scope trace reveals the characteristic integrator ramp response: position rises linearly from zero without ever settling to the commanded 1.57 radian setpoint, since the open-loop plant has no inherent position feedback. The initial transient shows first-order exponential approach to a constant velocity determined by the input voltage and the $\tau_m$ time constant, after which position continues integrating indefinitely. This behavior confirms the type-1 integrator structure and underscores the necessity of closing a feedback loop to achieve position regulation.

Design a PID compensator to stabilize the position servo using the internal model control (IMC) tuning methodology, which offers transparent trade-offs between closed-loop bandwidth and robustness. The IMC procedure for a type-1 plant begins by factoring the plant into invertible and non-invertible components: $G_p(s) = G_+(s) G_-(s)$, where $G_-(s) = 1/s$ represents the integrator (non-minimum phase in the velocity-to-position sense) and $G_+(s) = K_{dc} / (\tau_m s + 1)$ is the invertible first-order lag. The IMC controller is $C(s) = G_+^{-1}(s) F(s)$, where $F(s)$ is a low-pass filter that ensures properness and sets the closed-loop time constant $\lambda$. For a type-1 plant, a second-order filter is required: $F(s) = 1 / (\lambda s + 1)^2$. The resulting controller is:

$$C(s) = \frac{1}{K_{dc}} \cdot \frac{\tau_m s + 1}{(\lambda s + 1)^2} \cdot \frac{1}{s} = \frac{\tau_m s + 1}{K_{dc} s (\lambda s + 1)^2}$$

Expanding this into standard PID form $C(s) = K_p (1 + 1/(T_i s) + T_d s)$ requires algebraic manipulation. Multiply numerator and denominator by $s$ and collect terms to obtain:

$$C(s) = \frac{\tau_m}{K_{dc} (\lambda s + 1)^2} + \frac{1}{K_{dc} s (\lambda s + 1)^2}$$

This structure represents a PI controller with a second-order low-pass filter on both proportional and integral paths. For practical PLC implementation, simplify by choosing the closed-loop time constant $\lambda$ equal to the plant time constant $\tau_m = 33.5 \, \text{ms}$, which yields a closed-loop bandwidth approximately $1/(4\lambda) \approx 7.5 \, \text{Hz}$ and provides 60-degree phase margin. Expanding $(\lambda s + 1)^2 = \lambda^2 s^2 + 2\lambda s + 1$ and performing partial fraction decomposition yields the PID parameters:

$$K_p = \frac{\tau_m}{K_{dc} \lambda^2} = \frac{0.0335}{23.4 \times (0.0335)^2} \approx 1.28 \, \text{V/rad}$$

$$K_i = \frac{1}{K_{dc} \lambda^2} = \frac{1}{23.4 \times (0.0335)^2} \approx 38.1 \, \text{V/(rad·s)}$$

$$K_d = 0 \, \text{V·s/rad} \quad \text{(no derivative action in this IMC design)}$$

The integral time constant is $T_i = K_p / K_i = 1.28 / 38.1 \approx 33.6 \, \text{ms}$, confirming the PI structure with integral action scaled to cancel the plant pole.

Implement this discrete-time PID controller in an Allen-Bradley CompactLogix L16ER PLC using Structured Text programming language in Studio 5000 Logix Designer. Create a new Add-On Instruction named `PID_Position` with the following input/output tag structure: `Setpoint` (REAL, position command in radians), `ProcessValue` (REAL, measured position from encoder), `Output` (REAL, control voltage command in volts), `Kp` (REAL, proportional gain), `Ki` (REAL, integral gain), `Kd` (REAL, derivative gain), `ScanTime` (REAL, controller execution period in seconds), `IntegratorState` (REAL, internal integral accumulator), and `PrevError` (REAL, previous error for derivative calculation). The Structured Text logic implements a velocity-form PID algorithm with anti-windup clamping:

```
// Compute position error
Error := Setpoint - ProcessValue;

// Proportional term
P_Term := Kp * Error;

// Integral term with anti-windup
IntegratorState := IntegratorState + (Ki * Error * ScanTime);
IF IntegratorState > 24.0 THEN
    IntegratorState := 24.0;
ELSIF IntegratorState < -24.0 THEN
    IntegratorState := -24.0;
END_IF;
I_Term := IntegratorState;

// Derivative term (on process variable to avoid setpoint kick)
D_Term := -Kd * (ProcessValue - PrevError) / ScanTime;
PrevError := ProcessValue;

// Sum and saturate output
Output := P_Term + I_Term + D_Term;
IF Output > 24.0 THEN
    Output := 24.0;
ELSIF Output < -24.0 THEN
    Output := -24.0;
END_IF;
```

Configure the controller execution task in the Controller Properties → Tasks tab: set the Continuous Task period to `10.0` ms (10 milliseconds = 100 Hz update rate), providing five samples per mechanical time constant and satisfying the Nyquist criterion with 10× margin over the 7.5 Hz closed-loop bandwidth. Assign input tag `AI_EncoderPosition` (configured as a scaled 0–10V analog input representing 0–6.28 radians via linear mapping) to the `ProcessValue` input, and map the `Output` tag to analog output `AO_MotorVoltage` (0–10V controlling a linear voltage-mode servo amplifier with ±24V output swing). Initialize the gain tags: `Kp := 1.28`, `Ki := 38.1`, `Kd := 0.0`, and `ScanTime := 0.01`.

Commission the closed-loop servo on the physical test bench by following these procedures. First, verify open-loop motor operation by forcing the analog output to 2.0V (corresponding to approximately 4.8V at the amplifier output) and confirming smooth motor rotation in the positive direction with no mechanical binding or encoder glitches. Measure the steady-state velocity using a handheld optical tachometer or by observing the encoder count rate: it should stabilize near 20 rad/s given the plant DC gain of 23.4 rad/(V·s) × 0.2V/s command slope. Next, enable the PID controller and command a 90-degree (1.57 radian) step reference while capturing both the position feedback and control output signals on a four-channel oscilloscope. Channel 1 probes the analog encoder output (scaled position), Channel 2 monitors the motor voltage command, Channel 3 captures the error signal $e(t) = r(t) - y(t)$ using math functions, and Channel 4 optionally records motor armature current via a 0.1Ω shunt resistor and differential probe. Set the timebase to 50ms/division to capture the full 200ms settling transient, and trigger on the rising edge of the reference step at 1V threshold.

The oscilloscope trace should reveal a well-damped step response with less than 10% overshoot, 5% settling time under 150ms (approximately $4.5\lambda$), and zero steady-state error confirming the integral action. The control voltage waveform exhibits an initial spike to the 24V saturation limit as the proportional term reacts to the large initial error, followed by exponential decay toward a small DC offset (typically 0.2–0.5V) required to overcome static friction and maintain position against gravitational or spring return torques. If the response shows sustained oscillations, reduce the proportional gain $K_p$ by 20% and re-test; if the response is sluggish with excessive rise time, decrease the closed-loop time constant $\lambda$ to 20ms and recompute the PID gains accordingly. Persistent steady-state error despite integral action indicates actuator saturation or incorrect sensor scaling—verify that the encoder zero position aligns with the commanded reference frame by manually jogging the motor and confirming that the scaled analog voltage matches the mechanical angle.

Validate disturbance rejection performance by applying a calibrated external torque during steady-state tracking. With the servo holding position at 1.57 radians, manually apply a tangential force to the motor shaft using a spring scale calibrated to 2 Newtons at a 5cm moment arm, producing a 0.1 N·m disturbance torque (approximately 2× the motor's continuous rated torque). Observe the position feedback signal on the oscilloscope: the position should dip by less than 0.05 radians (3 degrees) before the integral action recovers to zero error within 100ms. The control voltage will step up by $\Delta V = T_{dist} / K_t \approx 0.1 / 0.042 \approx 2.4 \, \text{V}$ to counteract the disturbance, demonstrating the feedforward compensation inherent in the integral term. If the disturbance causes position errors exceeding 5 degrees or recovery times longer than 200ms, increase the integral gain $K_i$ by 30% while monitoring for signs of integrator windup (output saturating at 24V during disturbances) and reduce if saturation persists longer than 50ms.

Document the final tuned PID gains, measured step response characteristics (rise time, overshoot, settling time), and disturbance rejection metrics in a commissioning report formatted as a CSV table suitable for import into maintenance management systems. The table columns should include: `ControllerTag`, `Kp_V/rad`, `Ki_V/rad/s`, `Kd_V*s/rad`, `Lambda_ms`, `Bandwidth_Hz`, `PhaseMargin_deg`, `RiseTime_ms`, `Overshoot_pct`, `SettlingTime_ms`, `DisturbanceRejection_deg/Nm`. For the example servo, the final row reads: `PID_Position`, `1.28`, `38.1`, `0.0`, `33.5`, `7.5`, `60`, `85`, `8`, `145`, `30`. This structured data enables automated performance regression testing when motors or amplifiers are replaced during preventive maintenance, ensuring that tuning remains consistent across hardware revisions.

## Exercise 2: Parameter Variation & Empirical Analysis

Industrial control systems encounter parametric uncertainty from multiple sources: mechanical wear changes inertia and friction coefficients, temperature variations alter electrical resistance and magnetic properties, and process load fluctuations modify open-loop time constants by factors of two to five. Robust controller designs must maintain stability and performance across this operating envelope without requiring retuning, a property quantified by gain and phase margins in frequency-domain analysis. This exercise systematically perturbs plant parameters around their nominal values, measures closed-loop responses, and constructs empirical stability maps relating controller aggressiveness to robustness margins—knowledge essential for deploying controllers in uncontrolled industrial environments where plants age, loads vary, and operating conditions drift.

Begin by extending the MATLAB Simulink model from Exercise 1 to accept parameterized plant coefficients as workspace variables rather than hardcoded block parameters. Open `dcmotor_servo.slx` and double-click the Transfer Fcn block representing the motor plant. Replace the numerator coefficient `[23.4]` with the variable `Kdc` and the denominator polynomial `[0.0335 1 0]` with `[tau_m 1 0]`. In the MATLAB command window, define these base-case parameters as global workspace variables:

```matlab
Kdc = 23.4;          % DC gain [rad/(V·s)]
tau_m = 0.0335;      % Mechanical time constant [s]
J_nominal = 5e-5;    % Nominal inertia [kg·m^2]
B_nominal = 1e-5;    % Nominal damping [N·m·s/rad]
Kt = 0.042;          % Torque constant [N·m/A]
Ra = 1.2;            % Armature resistance [Ohm]
```

Create a parameter sweep script `sweep_inertia.m` that varies load inertia from 50% to 200% of nominal in ten logarithmically-spaced steps, recomputes the plant transfer function coefficients, simulates the closed-loop step response, and extracts performance metrics. The script structure follows:

```matlab
% Parameter sweep: inertia variation
J_range = logspace(log10(0.5*J_nominal), log10(2.0*J_nominal), 10);
results = struct('J', [], 'tau_m', [], 'Kdc', [], ...
                 'RiseTime', [], 'Overshoot', [], 'SettlingTime', [], ...
                 'GainMargin_dB', [], 'PhaseMargin_deg', []);

for idx = 1:length(J_range)
    J = J_range(idx);
    % Recompute plant coefficients
    tau_m = (Ra * J) / (Ra * B_nominal + Kt^2);
    Kdc = Kt / (Ra * B_nominal + Kt^2);
    
    % Simulate closed-loop response
    sim('dcmotor_servo', 0.5);
    position = logsout.get('position').Values.Data;
    time = logsout.get('position').Values.Time;
    
    % Extract step response metrics
    stepinfo_data = stepinfo(position, time, 1.57);
    results(idx).J = J;
    results(idx).tau_m = tau_m;
    results(idx).Kdc = Kdc;
    results(idx).RiseTime = stepinfo_data.RiseTime;
    results(idx).Overshoot = stepinfo_data.Overshoot;
    results(idx).SettlingTime = stepinfo_data.SettlingTime;
    
    % Compute stability margins via loop transfer function
    % L(s) = C(s) * G(s) where C(s) is PID from Exercise 1
    Kp = 1.28; Ki = 38.1; Kd = 0.0;
    C = tf([Kp*tau_m Kp Ki], [tau_m 1 0]);  % PID with derivative filter
    G = tf(Kdc, [tau_m 1 0]);
    L = C * G;
    [Gm, Pm, ~, ~] = margin(L);
    results(idx).GainMargin_dB = 20*log10(Gm);
    results(idx).PhaseMargin_deg = Pm;
end

% Plot results
figure;
subplot(2,2,1);
semilogx([results.J]/J_nominal, [results.RiseTime]*1000, 'b-o', 'LineWidth', 1.5);
xlabel('Inertia Ratio J/J_{nominal}'); ylabel('Rise Time [ms]');
grid on; title('Rise Time vs Inertia Variation');

subplot(2,2,2);
semilogx([results.J]/J_nominal, [results.Overshoot], 'r-o', 'LineWidth', 1.5);
xlabel('Inertia Ratio J/J_{nominal}'); ylabel('Overshoot [%]');
grid on; title('Overshoot vs Inertia Variation');

subplot(2,2,3);
semilogx([results.J]/J_nominal, [results.GainMargin_dB], 'g-o', 'LineWidth', 1.5);
hold on; plot(xlim, [6 6], 'k--'); hold off;  % 6dB minimum margin line
xlabel('Inertia Ratio J/J_{nominal}'); ylabel('Gain Margin [dB]');
grid on; title('Gain Margin vs Inertia Variation');

subplot(2,2,4);
semilogx([results.J]/J_nominal, [results.PhaseMargin_deg], 'm-o', 'LineWidth', 1.5);
hold on; plot(xlim, [45 45], 'k--'); hold off;  % 45deg minimum margin line
xlabel('Inertia Ratio J/J_{nominal}'); ylabel('Phase Margin [deg]');
grid on; title('Phase Margin vs Inertia Variation');

% Export data to CSV for PLC documentation
writetable(struct2table(results), 'inertia_sweep_results.csv');
```

Execute this script and analyze the resulting plots. The rise time curve exhibits a monotonically increasing trend: doubling inertia from $J_{nom}$ to $2J_{nom}$ increases the mechanical time constant by a factor of two (since $\tau_m \propto J$), slowing the closed-loop response proportionally. Specifically, rise time grows from approximately 85ms at $J = 0.5 J_{nom}$ to 170ms at $J = 2 J_{nom}$, reflecting the $\tau_m$ dependence embedded in the IMC tuning law. The overshoot curve shows more complex behavior: initially low (5–8%) at nominal inertia, it climbs to 15–20% as inertia doubles because the fixed PID gains become relatively more aggressive (higher proportional and integral action) relative to the slowed plant dynamics. This overshoot increase signals degraded damping ratio, approaching the marginally stable boundary where phase margin drops below 30 degrees.

The gain margin plot reveals a reassuring trend: gain margin remains above 10dB across the entire inertia range, indicating that the controller can tolerate a 3× increase in loop gain before instability. Gain margin improves slightly at higher inertias (12dB at $J = 2 J_{nom}$) because the additional plant lag reduces high-frequency gain, moving the critical -180° phase crossover to lower frequencies where the controller's integral action dominates. Conversely, phase margin deteriorates more severely: starting near 60 degrees at nominal inertia, it degrades to 38 degrees at $J = 2 J_{nom}$, approaching the 30-degree minimum threshold used in industrial practice. This asymmetry between gain and phase margins reflects the integrator pole in the plant transfer function—type-1 systems are inherently more sensitive to phase lag than gain variations.

Repeat the parameter sweep for viscous damping coefficient $B$, which physically represents bearing friction, windage losses, and eddy current braking. Modify the sweep script by replacing the `J_range` loop variable with:

```matlab
B_range = logspace(log10(0.2*B_nominal), log10(5.0*B_nominal), 10);
for idx = 1:length(B_range)
    B = B_range(idx);
    tau_m = (Ra * J_nominal) / (Ra * B + Kt^2);
    Kdc = Kt / (Ra * B + Kt^2);
    % [remainder identical to inertia sweep]
end
```

The damping sweep produces counterintuitive results: increasing damping from $0.2 B_{nom}$ to $5 B_{nom}$ actually worsens closed-loop performance, raising both rise time and overshoot. This occurs because higher damping reduces the plant DC gain $K_{dc}$ (denominator grows as $R_a B + K_t^2$ increases), requiring larger control voltages to achieve the same position change. The PID controller, tuned for nominal $K_{dc}$, becomes relatively less aggressive at high damping, leading to sluggish responses with 200–300ms rise times. Simultaneously, the mechanical time constant $\tau_m$ decreases as damping increases (smaller numerator $R_a J$ divided by larger denominator $R_a B + K_t^2$), introducing a pole-zero mismatch with the fixed integral time constant $T_i = K_p / K_i$. This mismatch manifests as 20–25% overshoot at $B = 5 B_{nom}$, far exceeding the 10% specification.

The stability margin analysis for damping variations reveals a critical operational boundary. Phase margin remains acceptable (above 40 degrees) only within the range $0.5 B_{nom} < B < 2 B_{nom}$, corresponding to a 4:1 damping uncertainty. Outside this envelope, either retuning is required or adaptive gain scheduling must activate. Construct a gain scheduling lookup table by fitting a polynomial to the $(B, K_p)$ relationship that maintains constant 60-degree phase margin:

```matlab
B_sched = [0.5 1.0 2.0 5.0] * B_nominal;
Kp_sched = zeros(size(B_sched));
for idx = 1:length(B_sched)
    B = B_sched(idx);
    tau_m = (Ra * J_nominal) / (Ra * B + Kt^2);
    Kdc = Kt / (Ra * B + Kt^2);
    lambda = tau_m;  % IMC tuning with lambda = tau_m
    Kp_sched(idx) = tau_m / (Kdc * lambda^2);
end
poly_coeffs = polyfit(B_sched, Kp_sched, 2);  % Quadratic fit
fprintf('Gain scheduling polynomial: Kp = %.4f*B^2 + %.4f*B + %.4f\n', ...
        poly_coeffs(1), poly_coeffs(2), poly_coeffs(3));
```

The resulting polynomial $K_p(B) = 0.0012 B^2 + 0.85 B + 0.65$ provides a real-time gain adaptation law implementable in PLC Structured Text. Add the following logic to the `PID_Position` Add-On Instruction:

```
// Estimate damping coefficient from steady-state velocity error
// During constant velocity commands, B ≈ Kt * I_ss / omega_ss
IF CommandVelocity > 0.1 THEN  // Avoid division by zero at standstill
    B_estimate := (0.042 * MotorCurrent) / CommandVelocity;
    // Clamp estimate to reasonable bounds
    IF B_estimate < 5.0e-6 THEN B_estimate := 5.0e-6; END_IF;
    IF B_estimate > 5.0e-5 THEN B_estimate := 5.0e-5; END_IF;
    // Update proportional gain via scheduling polynomial
    Kp := 0.0012*B_estimate*B_estimate + 0.85*B_estimate + 0.65;
END_IF;
```

This adaptive controller continuously estimates damping from measured motor current and velocity, adjusting proportional gain to compensate for bearing wear, temperature-induced viscosity changes, or load variations—all without human intervention.

Perform experimental validation of the gain-scheduled controller on the physical servo bench under artificially varied damping conditions. Simulate increased damping by mounting a viscous damper (a rotary dashpot or eddy-current brake) to the motor shaft, adjustable via a thumbscrew to produce 2× to 5× nominal damping torque. Command a series of 1-radian step moves with the dashpot progressively tightened after each step, recording position response curves on the oscilloscope. With fixed-gain control, observe the rise time increasing from 85ms to 250ms and overshoot growing from 8% to 28% as damping increases. Then enable the adaptive gain scheduling logic and repeat the test: rise time remains between 90–110ms across the full damping range, and overshoot stays below 12%, confirming that the polynomial gain law successfully compensates for parametric uncertainty.

Quantify the controller's robustness using a structured sensitivity analysis table. For each parameter (inertia $J$, damping $B$, and DC gain $K_{dc}$), compute the percentage change in phase margin per 10% parameter deviation from nominal. Create a MATLAB script that numerically differentiates phase margin with respect to each parameter:

```matlab
params = {'J', 'B', 'Kdc'};
nominal_values = [J_nominal, B_nominal, Kdc];
sensitivity = zeros(size(params));

for idx = 1:length(params)
    % Perturb parameter by +5%
    param_high = nominal_values(idx) * 1.05;
    % Recompute plant and margins
    [tau_m_high, Kdc_high] = compute_plant(param_high, nominal_values);
    [~, Pm_high] = compute_margins(tau_m_high, Kdc_high);
    
    % Perturb parameter by -5%
    param_low = nominal_values(idx) * 0.95;
    [tau_m_low, Kdc_low] = compute_plant(param_low, nominal_values);
    [~, Pm_low] = compute_margins(tau_m_low, Kdc_low);
    
    % Compute sensitivity: d(Pm) / d(param) normalized by param
    sensitivity(idx) = ((Pm_high - Pm_low) / (0.1 * nominal_values(idx))) * ...
                       (nominal_values(idx) / 60);  % Normalize to 60deg baseline
end

fprintf('Parameter Sensitivity (Phase Margin Change per 10%% variation):\n');
fprintf('  Inertia J:     %.2f deg / 10%%\n', sensitivity(1));
fprintf('  Damping B:     %.2f deg / 10%%\n', sensitivity(2));
fprintf('  DC Gain Kdc:   %.2f deg / 10%%\n', sensitivity(3));
```

The output reveals that phase margin is most sensitive to inertia variations (approximately -3.5 deg per 10% increase), moderately sensitive to damping (-1.8 deg per 10%), and relatively insensitive to DC gain (-0.6 deg per 10%). This ranking guides maintenance priorities: motor-load inertia ratio must be carefully documented and verified during installation, damping changes should trigger controller retuning during annual maintenance, while DC gain drifts (from magnet demagnetization or temperature effects) can be tolerated with minimal impact on stability.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

Production industrial control systems operate under failure modes that laboratory tuning exercises never encounter: sensors develop intermittent open-circuit faults producing wild measurement spikes, actuators saturate during aggressive maneuvers and trigger integrator windup, fieldbus communication frames drop due to electromagnetic interference, and power supply brownouts force controllers into safe-state shutdown sequences. This exercise systematically injects these fault conditions into the closed-loop servo system, quantifies their impact on stability and safety, and implements industry-standard fault detection, isolation, and recovery (FDIR) logic that transitions controllers through degraded operating modes without human intervention. The procedures follow IEC 61508 functional safety standards for Safety Integrity Level 2 (SIL-2) applications, requiring fail-safe behavior within 100ms of fault detection and diagnostic coverage exceeding 90%.

Begin with sensor fault injection testing using a hardware-in-the-loop configuration that physically interrupts the encoder signal path. Wire a double-pole-double-throw (DPDT) relay in series with the encoder's differential A/B quadrature outputs, controlled by a spare PLC digital output. When the relay de-energizes, the encoder signals float to mid-rail voltage levels (typically 2.5V on a 5V supply) which the PLC's differential line receiver interprets as invalid states oscillating between logic high and low at MHz rates. Implement the fault injection sequence in a new PLC subroutine:

```
// Sensor fault injection test routine
// Inject open-circuit fault for 500ms during steady-state tracking

IF TestMode_Enable AND (SystemTimer - TestStartTime > 2.0) THEN
    // System has settled to steady state for 2 seconds
    IF NOT FaultInjected THEN
        EncoderFault_Relay := FALSE;  // De-energize relay, open encoder path
        FaultInjectionTime := SystemTimer;
        FaultInjected := TRUE;
    END_IF;
    
    // Hold fault for 500ms
    IF (SystemTimer - FaultInjectionTime) > 0.5 THEN
        EncoderFault_Relay := TRUE;  // Re-energize relay, restore encoder
        TestMode_Enable := FALSE;    // End test
        FaultInjected := FALSE;
    END_IF;
END_IF;
```

Observe the controller behavior during the 500ms fault window on the oscilloscope. Without fault detection logic, the PLC's analog input module latches the last valid encoder value before the fault, or worse, interprets the floating voltage as a large position error (e.g., reading 8.5V when the encoder was at 5.0V position, perceived as a +3.5 radian error). The PID controller responds to this phantom error by commanding full positive voltage (+24V), driving the motor against mechanical end-stops and potentially causing hardware damage. The control output saturates within 10ms, and the integrator accumulates error at maximum rate, building up a 12 volt-second "windup debt" over the 500ms fault duration. When the encoder signal restores, the controller attempts to dissipate this windup, producing a 2-radian overshoot that slams the load into the opposite end-stop.

Implement sensor validation logic using a rate-limit plausibility check that flags encoder readings changing faster than the motor's maximum physical acceleration capability. Add this diagnostic block at the start of the PID controller execution:

```
// Sensor validation via rate-limit plausibility check
EncoderVelocity := (ProcessValue - PrevProcessValue) / ScanTime;
MaxPhysicalVelocity := 100.0;  // Maximum motor speed [rad/s]

IF ABS(EncoderVelocity) > MaxPhysicalVelocity THEN
    SensorFault := TRUE;
    SensorFaultCounter := SensorFaultCounter + 1;
    
    // Freeze process value at last good reading
    ProcessValue := PrevProcessValue;
    
    // Transition to safe state if fault persists for 100ms (10 scans)
    IF SensorFaultCounter >= 10 THEN
        ControllerState := SAFE_STATE;
        Output := 0.0;  // Zero voltage command
        IntegratorState := 0.0;  // Reset integrator to prevent windup
        FaultLatchActive := TRUE;
    END_IF;
ELSE
    // Reset fault counter if reading is plausible
    IF SensorFaultCounter > 0 THEN
        SensorFaultCounter := SensorFaultCounter - 1;  // Decrement with hysteresis
    END_IF;
    SensorFault := FALSE;
END_IF;

PrevProcessValue := ProcessValue;
```

This logic implements a leaky integrator fault counter that increments on implausible readings and slowly decrements on good readings, providing immunity to single-scan glitches while detecting sustained faults within 100ms. The state transition to `SAFE_STATE` freezes all control outputs and requires manual operator acknowledgment via HMI button press before resuming automatic control, ensuring that latent hardware faults are inspected before restart.

Rerun the sensor fault injection test with validation logic enabled. The oscilloscope trace now shows a clean transition: when the encoder fault occurs, the position feedback freezes at its last good value, the control output ramps down smoothly to zero over 100ms as the integrator unwinds, and the motor coasts to a stop under viscous damping within 500ms. No mechanical impacts occur, and the diagnostic HMI panel illuminates a "Sensor Fault - Encoder 1" alarm with timestamp and fault code 0x0042 (rate limit violation). After the relay restores the encoder signal, the operator clears the fault via HMI, the controller transitions back to `AUTOMATIC` mode, and normal tracking resumes within two seconds.

Proceed to actuator saturation stress testing by commanding a series of aggressive position moves that deliberately exceed the motor's torque capability. Configure a trapezoidal motion profile with 200 rad/s² acceleration, 50 rad/s maximum velocity, and 5-radian move distance—parameters requiring peak torque approximately 3× the motor's continuous rating. Implement the profile generator in Structured Text:

```
// Trapezoidal motion profile generator
IF ProfileActive THEN
    TimeInProfile := SystemTimer - ProfileStartTime;
    
    // Phase 1: Acceleration (0 to T_accel)
    T_accel := MaxVelocity / MaxAcceleration;  // Time to reach max velocity
    IF TimeInProfile < T_accel THEN
        CurrentVelocity := MaxAcceleration * TimeInProfile;
        CurrentPosition := 0.5 * MaxAcceleration * TimeInProfile * TimeInProfile;
    
    // Phase 2: Constant velocity (T_accel to T_accel + T_cruise)
    ELSIF TimeInProfile < (T_accel + T_cruise) THEN
        CurrentVelocity := MaxVelocity;
        CurrentPosition := 0.5 * MaxAcceleration * T_accel * T_accel + ...
                           MaxVelocity * (TimeInProfile - T_accel);
    
    // Phase 3: Deceleration (T_accel + T_cruise to T_total)
    ELSE
        T_decel := TimeInProfile - T_accel - T_cruise;
        CurrentVelocity := MaxVelocity - MaxAcceleration * T_decel;
        CurrentPosition := 0.5 * MaxAcceleration * T_accel * T_accel + ...
                           MaxVelocity * T_cruise + ...
                           MaxVelocity * T_decel - 0.5 * MaxAcceleration * T_decel * T_decel;
        
        IF T_decel >= T_accel THEN
            ProfileActive := FALSE;  // Move complete
        END_IF;
    END_IF;
    
    Setpoint := ProfileStartPosition + CurrentPosition;
END_IF;
```

Execute the profile and monitor the control output on the oscilloscope. The voltage command immediately saturates at +24V during the acceleration phase, remaining pegged for the full T_accel = 0.25 seconds required to reach 50 rad/s velocity. During this saturation period, the integrator continues accumulating position tracking error at a rate of approximately 0.5 rad/s (the difference between commanded and achievable acceleration), building up 0.125 radians of error by the end of acceleration. When the profile transitions to constant velocity cruise, the control output drops to approximately 5V (the steady-state voltage required for 50 rad/s against damping), but the integrator maintains its 4.8 volt-second accumulated charge. During deceleration, the controller commands -24V to brake, again saturating for 250ms. The final position error settles near zero after a 300ms damped oscillation, but peak transient error reaches 0.15 radians (8.6 degrees)—unacceptable for precision applications.

Implement anti-windup logic using the "back-calculation" method, which prevents integrator accumulation whenever the actuator saturates. Modify the PID controller as follows:

```
// Anti-windup via back-calculation method
Output_Ideal := P_Term + I_Term + D_Term;

// Apply saturation limits
IF Output_Ideal > 24.0 THEN
    Output := 24.0;
    Saturation_Error := Output_Ideal - Output;  // Positive excess
ELSIF Output_Ideal < -24.0 THEN
    Output := -24.0;
    Saturation_Error := Output_Ideal - Output;  // Negative excess
ELSE
    Output := Output_Ideal;
    Saturation_Error := 0.0;
END_IF;

// Back-calculate integrator adjustment
Kb := 1.0 / Ki;  // Back-calculation gain (inverse of integral gain)
IntegratorState := IntegratorState - (Kb * Saturation_Error * ScanTime);
```

The back-calculation gain $K_b = 1/K_i$ ensures that the integrator unwinds at exactly the rate needed to drive the saturation error to zero, preventing windup accumulation while maintaining integral action authority when the output is not saturated. Rerun the aggressive motion profile with anti-windup enabled: peak tracking error reduces to 0.08 radians (4.6 degrees), final settling time decreases from 300ms to 180ms, and no post-move oscillations occur. The integrator state trajectory remains bounded between ±5.0, compared to ±15.0 without anti-windup.

Test fieldbus communication robustness by injecting Modbus RTU frame errors using a bus traffic generator connected to the RS-485 network. Configure the generator to transmit corrupted frames (invalid CRC checksums) at a rate of 5% during normal operation, simulating electrical noise from variable frequency drives or arc welders. Monitor the PLC's Modbus diagnostic counters via the controller status tags:

```
// Modbus communication health monitoring
CommTimeout := ModbusNode[1].Timeout_Count;
CommCRC_Error := ModbusNode[1].CRC_Error_Count;
CommSuccess := ModbusNode[1].Success_Count;

// Compute error rate over last 100 transactions
CommErrorRate := (CommCRC_Error + CommTimeout) / (CommSuccess + CommCRC_Error + CommTimeout);

IF CommErrorRate > 0.10 THEN
    // Error rate exceeds 10%, degrade to safe mode
    ControllerState := COMM_FAULT;
    Output := 0.0;
    HMI_Alarm := "Fieldbus Error Rate High";
ELSIF CommErrorRate > 0.05 THEN
    // Warning level: reduce controller bandwidth
    Lambda_Degrade := Lambda_Normal * 2.0;  // Double closed-loop time constant
    Kp := Kp * 0.5;  // Halve proportional gain
    Ki := Ki * 0.5;  // Halve integral gain
    HMI_Warning := "Fieldbus Degraded - Performance Reduced";
END_IF;
```

This adaptive logic gracefully degrades controller aggressiveness when communication reliability drops, trading bandwidth for robustness. With 5% frame error rate, the controller reduces its gains by 50%, increasing rise time from 85ms to 170ms but preventing oscillations caused by stale feedback data. If error rate exceeds 10%, the system transitions to safe-state with zero output, equivalent to a communication timeout condition.

Perform power supply brownout testing by injecting a 200ms voltage sag to 18VDC (from nominal 24VDC) using a programmable DC power supply in series with the PLC power input. Monitor the PLC's internal supply voltage via the diagnostic status word and implement brownout detection:

```
// Power supply monitoring and brownout recovery
SupplyVoltage := ControllerDiagnostic.SupplyVoltage_mV / 1000.0;  // Convert to volts

IF SupplyVoltage < 20.0 THEN
    // Brownout detected, initiate emergency shutdown sequence
    BrownoutActive := TRUE;
    
    // Ramp down control output over 50ms to prevent mechanical shock
    IF Output > 0.0 THEN
        Output := Output - (0.48 * ScanTime);  // 24V/50ms = 0.48 V/ms
        IF Output < 0.0 THEN Output := 0.0; END_IF;
    ELSIF Output < 0.0 THEN
        Output := Output + (0.48 * ScanTime);
        IF Output > 0.0 THEN Output := 0.0; END_IF;
    END_IF;
    
    // After output reaches zero, set safe-state flag
    IF ABS(Output) < 0.1 THEN
        ControllerState := BROWNOUT_SAFE;
        IntegratorState := 0.0;
    END_IF;
    
ELSIF BrownoutActive AND (SupplyVoltage > 22.0) THEN
    // Supply restored with hysteresis, ready for restart
    BrownoutActive := FALSE;
    HMI_Message := "Power Restored - Restart Required";
END_IF;
```

The controlled ramp-down over 50ms prevents the motor from suddenly decelerating under back-EMF braking, which could cause mechanical resonances or load disturbances. After the brownout ends, the controller requires manual restart to ensure that the system state is verified before resuming automatic operation.

Document all fault injection test results in a failure modes and effects analysis (FMEA) table formatted per IEC 61508 Annex D. The table columns include: `Failure_Mode`, `Detection_Method`, `Detection_Time_ms`, `Safe_State_Transition_ms`, `Diagnostic_Coverage_pct`, `Residual_Risk`. Example rows:

| Failure_Mode | Detection_Method | Detection_Time_ms | Safe_State_Transition_ms | Diagnostic_Coverage_pct | Residual_Risk |
|---|---|---|---|---|---|
| Encoder Open Circuit | Rate Limit Check | 20 | 100 | 95 | Position drift < 0.1 rad during detection window |
| Actuator Saturation | Output Clamp Detection | 10 | N/A (anti-windup) | 99 | Tracking error < 0.1 rad during saturation |
| Modbus Frame Error | CRC Check + Timeout | 50 | 200 | 98 | Stale data for max 2 scan cycles |
| Power Brownout | Voltage Monitor | 15 | 65 | 100 | None (hardware-level detection) |

This FMEA table serves as verification evidence for functional safety certification audits and guides preventive maintenance schedules by identifying which faults require periodic testing.

## Operational Reference Guide & Diagnostic Checklist

The operational reference guide consolidates the laboratory findings into a practitioner-ready document for commissioning new industrial control installations, troubleshooting performance degradations, and conducting annual validation audits. This section provides structured procedures, diagnostic flowcharts, and quantitative acceptance criteria formatted for field technicians operating under time pressure in noisy industrial environments.

### Pre-Commissioning Verification Checklist

Before energizing any control loop, execute this mandatory safety and functionality checklist in sequence, verifying each step with physical measurements and photographic documentation:

**Electrical Safety (perform with power disconnected):**
1. Verify earth ground continuity from PLC chassis to main distribution panel ground bar: measure resistance using Fluke 1587 insulation tester in low-resistance mode, confirm < 0.1 Ω per NEC Article 250.
2. Inspect all control power wiring (24VDC bus) for proper wire gauge: 18 AWG minimum for runs < 10 meters, 16 AWG for 10–20 meters per voltage drop calculations limiting to < 2% (0.48V at 24VDC).
3. Confirm emergency-stop circuit wiring in series-redundant normally-closed configuration: manually trip each E-stop button and verify that all downstream contactors de-energize simultaneously within 50ms (measure using oscilloscope on contactor coil voltage).
4. Validate analog input/output scaling: inject calibrated test signals (Fluke 789 ProcessMeter generating 4.000 mA, 12.000 mA, 20.000 mA for 4–20mA loops) and verify PLC raw count registers match engineering unit scaling factors within ±0.5% full scale.

**Mechanical Safety:**
5. Confirm mechanical end-of-travel limit switches are positioned to prevent actuator over-travel by at least 10mm margin beyond normal operating range.
6. Measure motor shaft runout using dial indicator: maximum 0.05mm TIR (total indicated runout) to prevent encoder alignment errors.
7. Verify gearbox backlash: manually rotate motor shaft in both directions while measuring output shaft motion with dial indicator; backlash < 0.5° for servo applications, < 2.0° for non-precision drives.
8. Inspect flexible couplings for wear: no visible cracks in elastomer elements, axial float within 0.2–0.5mm per manufacturer specifications.

**Control System Configuration:**
9. Document PLC firmware revision, I/O module catalog numbers, and network topology in the site maintenance database, including MAC addresses of all Ethernet/IP or Profinet devices.
10. Verify controller scan time under maximum I/O load: force all inputs to toggle every scan and measure actual scan period using PLC diagnostic counters; confirm < 1.5× the configured periodic task rate (e.g., < 15ms for 10ms task).
11. Validate sensor polarity and direction: apply positive motion/signal and verify that feedback increases in the PLC tag (not decreases due to inverted wiring).
12. Test actuator direction: command +1V output and verify motor rotates in the mechanically-defined positive direction (typically CCW viewed from motor shaft end).

### PID Tuning Field Procedure

When plant parameters are unknown or documented tuning data is unavailable, execute this empirical tuning protocol to derive initial PID gains within 30 minutes:

**Step 1: Open-Loop Step Test (10 minutes)**
- Disable all feedback loops by forcing the PID controller to manual mode with output frozen at 0V.
- Command a 10% step change in actuator output (2.4V for ±24V range) and record process variable response using PLC trend logging at 10× the expected loop bandwidth (e.g., 100ms sampling for 1Hz bandwidth loops).
- Measure the following characteristics from the response curve:
  - Dead time $t_d$: elapsed time from step input until process variable begins changing (typically 0–50ms for electrical systems, 1–10s for thermal/hydraulic systems).
  - Time constant $\tau$: time for response to reach 63.2% of final value after dead time expires.
  - DC gain $K$: steady-state change in process variable divided by step magnitude (e.g., if 2.4V input produces 5.0 rad position change, $K = 5.0/2.4 = 2.08$ rad/V).
- Classify plant type: if the response continues rising indefinitely (integrator/ramp), it is type-1; if it settles to a constant value, it is type-0.

**Step 2: Initial Gain Calculation (5 minutes)**
- For type-0 (self-regulating) plants, apply the Cohen-Coon tuning rules:
  - $K_p = (1.35 / K) \cdot (\tau / t_d) \cdot (1 + t_d / (4\tau))$
  - $T_i = t_d \cdot (2.5 + t_d / \tau) / (1 + 0.6 \cdot t_d / \tau)$
  - $T_d = 0.37 \cdot t_d / (1 + 0.2 \cdot t_d / \tau)$
  - Convert to PLC gains: $K_i = K_p / T_i$, $K_d = K_p \cdot T_d$.
- For type-1 (integrating) plants, use the IMC method from Exercise 1:
  - $K_p = \tau / (K \cdot \lambda^2)$ where $\lambda = \max(2 t_d, \tau/3)$.
  - $K_i = 1 / (K \cdot \lambda^2)$
  - $K_d = 0$ (derivative action typically omitted for integrating plants).

**Step 3: Closed-Loop Testing (15 minutes)**
- Enable automatic mode with calculated gains and command a 25% setpoint step change.
- Observe response on HMI trend display and measure:
  - Rise time $t_r$ (10% to 90% of final value)
  - Overshoot $M_p$ (percentage of setpoint exceeded)
  - Settling time $t_s$ (time to remain within ±2% of setpoint)
- Apply gain adjustments per this table:

| Symptom | Adjustment |
|---|---|
| Overshoot > 25% or oscillations | Reduce $K_p$ by 30%, reduce $K_i$ by 20% |
| Rise time > 10× dead time | Increase $K_p$ by 20%, increase $K_i$ by 20% |
| Steady-state error > 2% after 20× $\tau$ | Increase $K_i$ by 50% |
| High-frequency noise in output | Add derivative filter: $T_f = T_d / 5$, reduce $K_d$ by 30% |

Iterate adjustments in maximum three tuning cycles; if performance remains unacceptable, re-examine the open-loop model for unmodeled dynamics (nonlinear friction, resonances).

### Diagnostic Fault Tree

When a commissioned control loop exhibits unstable or degraded performance, navigate this diagnostic tree to isolate root causes within 20 minutes:

**[START] Is the process variable oscillating?**
- YES → Measure oscillation frequency $f_{osc}$ using FFT on PLC trend data.
  - If $f_{osc} < 1/(4\tau)$ (slow oscillation near loop bandwidth): Excessive proportional or integral gain. Reduce $K_p$ by 20%, test again.
  - If $f_{osc} \approx 1/(2 T_d)$ (fast oscillation near derivative time): Derivative kick or noise amplification. Reduce $K_d$ by 50% or add derivative filter $T_f = T_d / 10$.
  - If $f_{osc}$ matches mechanical resonance (measure via tap test or swept-sine): Add notch filter at resonance frequency or reduce loop bandwidth by increasing $\lambda$ to $2\tau$.
- NO → Proceed to steady-state checks.

**Is there steady-state error > 2% of span?**
- YES → Check for integrator saturation or disabled integral action.
  - Verify that PLC tag `IntegratorState` is within ±80% of saturation limits; if saturated for > 1 second, increase actuator range or reduce setpoint rate-of-change.
  - Confirm $K_i > 0$ (common error when copying P-only controllers).
- NO → Check response speed.

**Is rise time > 20× expected value or actuator not moving?**
- Check for these hardware faults in order:
  1. Actuator stuck or unpowered: Measure voltage at motor terminals using DMM; should be non-zero and proportional to PLC output tag.
  2. Sensor failed or mis-scaled: Manually move process to known position (e.g., home switch) and verify PLC process value matches mechanical position within 2%.
  3. Wrong control direction: If increasing output decreases process variable, invert controller output by negating PID gains or swapping actuator polarity.
  4. PLC scan overload: Check controller scan time; if > 1.5× configured rate, reduce I/O count or offload non-critical tasks to lower-priority threads.

**Are there intermittent faults or alarm spikes?**
- Enable PLC diagnostic buffer logging at maximum rate (1ms) and capture 10 seconds surrounding fault event.
- Analyze for these patterns:
  - Single-scan spikes in process variable: Sensor noise from EMI; add RC low-pass filter (1kΩ + 0.1µF) at analog input terminals.
  - Periodic dropouts every 50/60Hz cycle: Ground loop causing common-mode noise; break shield ground at one end of sensor cable and verify isolated ground bus.
  - Random communication timeouts: Check RS-485 bus termination resistors (120Ω at both ends), verify baud rate mismatch (all nodes identical), replace cables exceeding 1000m length limit.

### Annual Performance Validation Protocol

Industrial control systems require periodic re-verification to detect degraded performance from component aging, process changes, or maintenance modifications. Execute this protocol annually or after any major system modification:

**Closed-Loop Performance Test (30 minutes per loop):**
1. Command five consecutive 50% setpoint step changes (up-down-up-down-up sequence) and record process variable, setpoint, and control output at 10× loop bandwidth sampling rate.
2. Compute average performance metrics across the five steps: $\overline{t_r}$, $\overline{M_p}$, $\overline{t_s}$, and integral absolute error $\text{IAE} = \int_0^{T} |e(t)| \, dt$.
3. Compare to baseline commissioning data stored in site database; flag deviations exceeding these thresholds:
   - Rise time increase > 30%: Indicates increased inertia, reduced actuator torque, or sensor lag; inspect for mechanical wear.
   - Overshoot increase > 10 percentage points: Reduced damping or excessive gain; re-tune using field procedure above.
   - IAE increase > 50%: Dead time increased (transport lag) or actuator nonlinearity developed; check for valve packing friction, gearbox backlash growth.

**Stability Margin Measurement (15 minutes per loop):**
1. Inject a pseudo-random binary signal (PRBS) excitation on the setpoint input using the PLC's random number generator seeded with a known value for repeatability:
   ```
   IF SystemTimer MOD 0.1 < 0.05 THEN
       Setpoint := Setpoint_Nominal + 0.05 * (RAND(42) - 0.5);
   END_IF;
   ```
2. Record 300 seconds of input-output data and export to CSV format.
3. Perform frequency-domain identification in MATLAB using the `tfestimate` function:
   ```matlab
   data = csvread('prbs_test_data.csv');
   time = data(:,1); input = data(:,2); output = data(:,3);
   [Txy, F] = tfestimate(input, output, hanning(512), 256, 2048, 1/mean(diff(time)));
   [Gm_measured, Pm_measured] = margin(Txy, F*2*pi);
   fprintf('Measured Gain Margin: %.1f dB\n', 20*log10(Gm_measured));
   fprintf('Measured Phase Margin: %.1f deg\n', Pm_measured);
   ```
4. Compare measured margins to design targets (typically $\text{GM} \geq 6 \, \text{dB}$, $\text{PM} \geq 45°$); if either falls below threshold, re-tune controller with increased $\lambda$ (reduced bandwidth) to restore robustness.

**Fieldbus Health Check (10 minutes):**
1. Query Modbus node diagnostics and record cumulative counters: `Success_Count`, `CRC_Error_Count`, `Timeout_Count`, `Exception_Count`.
2. Compute error rates: $\text{CRC Rate} = \text{CRC Errors} / \text{Total Transactions}$, $\text{Timeout Rate} = \text{Timeouts} / \text{Total Transactions}$.
3. Acceptance criteria: CRC rate < 0.1%, timeout rate < 0.5%, no exception responses in last 10,000 transactions.
4. If thresholds exceeded, perform physical layer diagnostics:
   - Measure bus voltage differential using oscilloscope: should be 2.0–3.0V peak-to-peak during idle, 1.5–6.0V during transmission.
   - Verify termination resistors: 120Ω ±5% at furthest nodes.
   - Check for voltage drop on long cable runs: < 0.5V difference between nearest and furthest node ground references.

All test results, raw data files, and pass/fail determinations are archived in the site document management system with test date, technician name, and equipment serial numbers for traceability and compliance auditing.
