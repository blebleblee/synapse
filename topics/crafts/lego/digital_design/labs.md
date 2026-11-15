# Operational Verification Labs: Digital Design

## Objective & Operational Lab Setup

Digital design in Lego Technic represents the intersection of Boolean logic, mechanical computation, and physical state manipulation through pneumatic actuators, gear-driven switches, and lever-based memory cells. This laboratory guide transforms abstract digital logic concepts into tactile, mechanically verifiable systems that obey the same truth tables and timing constraints as electronic circuits, but with the immediacy of physical feedback: pneumatic hiss, axle rotation, and pin displacement. The practitioner will construct working implementations of fundamental logic gates, combinational circuits, and sequential state machines, then subject each design to rigorous empirical verification through input permutation testing, timing analysis, and failure mode injection.

The operational environment requires a dedicated workbench cleared of at least 1.2 meters by 0.8 meters, sufficient to accommodate expanding assemblies and facilitate overhead photography for documentation. Lighting must be directional and shadow-free; a swing-arm LED task lamp positioned at 45 degrees to the work surface eliminates pin-hole ambiguity during assembly verification. The core inventory draws from Lego Technic pneumatic systems (sets 8868, 42043, or equivalent bulk pneumatic components), supplemented by precision mechanical elements: 1×5 and 1×7 liftarms for structural rigidity, friction pins and bushings for pivot articulation, and an assortment of 2-tooth, 8-tooth, 12-tooth, 16-tooth, 20-tooth, and 24-tooth gears for ratio-based logic translation. Pneumatic components include at least two small pumps, four pneumatic cylinders (preferably a mix of small and medium stroke lengths), six pneumatic switches (the three-port valve assemblies that serve as mechanical transistors), and approximately three meters of pneumatic tubing cut into modular 15 cm, 25 cm, and 40 cm segments with clean, perpendicular cuts to ensure airtight tube-to-port insertion.

Truth table verification demands a systematic input enumeration protocol. Prepare a laboratory notebook or spreadsheet template with columns for input states (A, B, C as applicable), predicted output (from theoretical truth table), observed output (physical cylinder extension or retraction), and discrepancy notes. Pneumatic pressure serves as the universal logic high; atmospheric vent represents logic low. A small pump manually actuated provides deterministic pressure pulses, while spring-return switches provide natural pull-down behavior. Timing measurements require a smartphone stopwatch or, for higher precision, a 60 fps video recording analyzed frame-by-frame in post-processing; pneumatic actuation typically exhibits 50–150 millisecond response latency depending on tubing length and cylinder bore diameter.

## Exercise 1: Foundational Practical Implementation

### Exercise 1A: Pneumatic NOT Gate with Normally-Open Switch Inversion

The NOT gate inverts a single input, producing the complement state at its output. In pneumatic Lego systems, the three-port pneumatic switch serves as the foundational inverting element. This switch contains an internal shuttle valve: when input port pressure exceeds a threshold (approximately 1.5 psi in Lego pneumatic systems), the shuttle diverts flow from port A to port B; when input pressure drops, a return spring vents port B and reconnects port A. Configure the switch in normally-open mode, where the absence of input pressure allows flow from the common port to the output port, and input pressure interrupts this flow.

Begin construction by anchoring a 1×7 liftarm vertically to the baseplate using two friction pins spaced five studs apart, ensuring zero play—this vertical beam serves as the structural backbone. Mount the pneumatic switch at the fourth stud height using a perpendicular 1×5 liftarm and a through-axle securing pin. Designate the switch's common port as the pressure supply input, the normally-open port as the output connection, and the control port as the logic input signal. Connect a 15 cm tube segment from the small pump's output to the switch's common port, ensuring the tube seats fully into the port (a 5 mm insertion depth with audible snap indicates proper seating). Connect a second 15 cm tube from the switch's normally-open port to a small pneumatic cylinder mounted horizontally on a parallel 1×7 liftarm five studs away. The cylinder's mounting must allow free extension without axial misalignment; use a friction pin through the cylinder's base mounting hole and verify that the piston rod travels perpendicular to the liftarm face with zero binding across the full stroke length.

To operate the NOT gate, leave the switch's control port disconnected (vented to atmosphere, representing logic low input). Actuate the pump twice with firm, complete strokes. The cylinder should extend fully within 100 milliseconds as air flows through the normally-open path. Record the output state as logic high (extended). Now connect a third 15 cm tube from a second pump (or a manual valve if available) to the switch's control port and apply pressure. The cylinder should retract immediately as the switch shuttle blocks the normally-open path and vents the output port. Record the output state as logic low (retracted). This completes one truth table verification cycle:

| Input A | Output Q |
|---------|----------|
| 0 (vent)| 1 (extended) |
| 1 (pressure) | 0 (retracted) |

The discrepancy analysis must account for pneumatic hysteresis. If the cylinder remains partially extended when input pressure is applied, inspect for tube leaks at port junctions by applying soapy water and observing for bubble formation. If the cylinder extends sluggishly when input is vented, verify that the switch return spring has not been compressed or damaged; a fatigued spring exhibits 50+ millisecond delay in shuttle return. Re-seat all tubes, apply pressure, and re-verify. Photograph the assembly from three orthogonal views (top, front, right side) and annotate the input/output ports in your lab notebook.

### Exercise 1B: Two-Input Pneumatic AND Gate via Series Valve Cascade

The AND gate produces logic high output only when all inputs are simultaneously high, embodying the multiplicative conjunction of Boolean algebra. Pneumatic implementation exploits the series flow restriction property: air must traverse both valves sequentially to reach the output cylinder. Construct the AND gate by chaining two pneumatic switches in series configuration, where the output port of the first switch feeds the common port of the second switch.

Establish a rigid L-shaped base structure using two 1×9 liftarms joined at a right angle with a perpendicular connector and cross-braced with a 1×5 liftarm diagonal to eliminate torsional flex. Mount the first pneumatic switch (designated Switch A) on the horizontal arm at stud position three, and mount the second switch (Switch B) on the vertical arm at stud position five. Connect a 20 cm tube from the pump's output to Switch A's common port. Connect a 15 cm tube from Switch A's normally-closed port to Switch B's common port—note the use of normally-closed configuration here, which allows flow only when the control port receives pressure. Connect a 20 cm tube from Switch B's normally-closed port to the pneumatic cylinder. The cylinder mounts horizontally on a parallel liftarm with friction pin retention and free piston travel verified.

Operational verification proceeds through exhaustive input permutation. Configure both switch control ports vented (both inputs at logic low). Actuate the pump; the cylinder remains retracted because Switch A's normally-closed port blocks flow. Apply pressure to Switch A's control port alone (Input A high, Input B low). The cylinder remains retracted because Switch B's normally-closed port still blocks flow. Release Switch A and apply pressure to Switch B's control port alone (Input A low, Input B high). The cylinder remains retracted because Switch A now blocks flow upstream. Finally, apply pressure to both control ports simultaneously. Both switches transition to flow-through state, and the cylinder extends within 150 milliseconds. The cumulative tube length of 55 cm introduces perceptible lag; this is expected and demonstrates the RC time constant analog in fluidic systems.

Truth table verification:

| Input A | Input B | Output Q |
|---------|---------|----------|
| 0       | 0       | 0        |
| 0       | 1       | 0        |
| 1       | 0       | 0        |
| 1       | 1       | 1        |

Failure modes include partial cylinder extension when only one input is high, indicating a stuck or leaking valve shuttle. Disassemble the suspect switch, inspect the internal shuttle for debris or plastic flash, and reassemble with attention to O-ring alignment. If the cylinder extends sluggishly even when both inputs are high, calculate the cumulative pressure drop across the series restrictions: each switch imposes approximately 0.3 psi drop at nominal flow rates, and the 55 cm tube length contributes additional viscous drag. Reduce tube length by repositioning switches closer together, or substitute a medium-bore cylinder with lower breakaway friction.

### Exercise 1C: Two-Input Pneumatic OR Gate via Parallel Valve Topology

The OR gate asserts logic high output when any input is high, embodying the additive disjunction of Boolean algebra. Pneumatic implementation exploits parallel flow paths: air reaches the output cylinder through either of two independent routes. This topology requires a Y-junction or dual-input manifold, which Lego pneumatics do not provide as a discrete component. Construct the functional equivalent using a modified switch configuration or a structural junction fabricated from stacked tube ports.

The practical OR gate implementation leverages two switches configured in normally-open mode, with their outputs converging on a single cylinder via a custom Y-junction. Fabricate the Y-junction by drilling a 4 mm diameter hole through the center of a 1×3 Technic brick (use a pin vise or drill press with the brick clamped in a soft-jaw vise to prevent cracking). Insert two tube segments halfway into adjacent stud holes, and insert a third tube into the drilled center hole such that all three tubes meet in a common air cavity within the brick. Seal the junction with cyanoacrylate adhesive applied sparingly to the tube-brick interface; allow 10 minutes curing time and verify airtightness by blowing gently through one input tube while blocking the other—air should exit smoothly through the output tube.

Mount two pneumatic switches on parallel 1×7 liftarms separated by seven studs, positioned at identical heights for visual clarity. Connect a 15 cm tube from each switch's normally-open port to the two input branches of the Y-junction. Connect a 20 cm tube from the Y-junction's output to the pneumatic cylinder. Connect separate 15 cm tubes from the pump (or two independent pumps for true simultaneous control) to the common port of each switch. The control ports remain vented initially.

Operational verification: With both control ports vented, actuate the pump feeding Switch A. The cylinder extends because air flows through Switch A's normally-open path, through the Y-junction, and into the cylinder. Release pressure and verify cylinder retraction via spring return. Now actuate the pump feeding Switch B alone; the cylinder extends via the alternate path. Finally, actuate both pumps simultaneously; the cylinder extends, and the Y-junction equalizes pressure from both sources. The truth table confirms OR logic:

| Input A | Input B | Output Q |
|---------|---------|----------|
| 0       | 0       | 0        |
| 0       | 1       | 1        |
| 1       | 0       | 1        |
| 1       | 1       | 1        |

Critically inspect the Y-junction for asymmetric flow resistance. If one input path consistently produces slower cylinder extension than the other, the junction geometry may favor one branch. Re-drill the center hole 0.5 mm larger, or fabricate a new junction with symmetric tube insertion depths. Photograph the Y-junction in cross-section if possible, or produce a detailed sketch annotating tube angles and insertion depths for reproducibility documentation.

## Exercise 2: Parameter Variation & Empirical Analysis

### Exercise 2A: Timing Characterization Across Tube Length and Cylinder Bore

Pneumatic logic gates exhibit propagation delay analogous to electronic gate delay, governed by fluid dynamics: volumetric flow rate through restrictive orifices (tube bore, valve ports) and the compliance of the actuator (cylinder swept volume). This exercise quantifies the relationship between tube length, cylinder size, and actuation response time through systematic empirical measurement, constructing a design lookup table for future circuit optimization.

Establish a test fixture comprising a single pneumatic switch in normally-open configuration, a pump, and interchangeable tube lengths: 10 cm, 20 cm, 40 cm, and 80 cm. Prepare three pneumatic cylinders: small (approximately 1.5 cm³ swept volume), medium (approximately 3.0 cm³), and large (approximately 6.0 cm³, typically from sets like 8868). The experimental protocol measures the interval between pump actuation initiation and cylinder full extension, operationally defined as the instant the piston rod reaches maximum displacement with no further visible motion.

Mount the test fixture on a baseplate with the cylinder oriented horizontally and the piston rod tip aligned with a vertical scale improvised from a 1×16 Technic beam positioned edgewise, with stud holes serving as millimeter graduations. Position a smartphone camera on a tripod 30 cm from the assembly, framing the pump handle, cylinder rod, and scale in a single shot. Record at 60 fps or higher. Execute each test by actuating the pump with a rapid, full-stroke motion while recording. Transfer the video to a computer and analyze frame-by-frame using VLC media player or equivalent, counting frames from the first visible pump handle motion to the frame where the cylinder rod stabilizes at full extension. Convert frame count to milliseconds by dividing by the frame rate (e.g., 30 frames at 60 fps = 500 ms).

Conduct five replicate measurements for each tube length and cylinder size combination (3 cylinders × 4 tube lengths = 12 configurations × 5 replicates = 60 measurements). Calculate the mean response time and standard deviation for each configuration. Empirical results from prior workshops yield the following representative data:

**Small Cylinder (1.5 cm³ swept volume):**
- 10 cm tube: 45 ms ± 8 ms
- 20 cm tube: 75 ms ± 12 ms
- 40 cm tube: 140 ms ± 18 ms
- 80 cm tube: 310 ms ± 35 ms

**Medium Cylinder (3.0 cm³ swept volume):**
- 10 cm tube: 70 ms ± 10 ms
- 20 cm tube: 110 ms ± 15 ms
- 40 cm tube: 210 ms ± 22 ms
- 80 cm tube: 480 ms ± 45 ms

**Large Cylinder (6.0 cm³ swept volume):**
- 10 cm tube: 120 ms ± 15 ms
- 20 cm tube: 180 ms ± 20 ms
- 40 cm tube: 360 ms ± 30 ms
- 80 cm tube: 780 ms ± 60 ms

The data reveal two governing trends. First, response time scales approximately linearly with tube length for a fixed cylinder size, consistent with the volumetric fill time required to pressurize the cumulative tube and cylinder volume. The slope of this relationship (milliseconds per centimeter of tube) increases with cylinder size, reflecting the greater total volume requiring pressurization. Second, response time increases nonlinearly with cylinder swept volume for fixed tube length, indicating that larger cylinders impose higher breakaway friction and require more air mass to overcome static friction and accelerate the piston to steady-state velocity.

Construct a design nomograph by plotting response time (y-axis, milliseconds) versus tube length (x-axis, centimeters) with separate curves for each cylinder size. Overlay horizontal reference lines at 100 ms, 200 ms, and 500 ms to demarcate acceptable latency thresholds for interactive mechanisms (100 ms perceivable by human operators, 500 ms acceptable for sequential automation). This nomograph becomes the primary tool for gate layout optimization: designers constrained by timing specifications select cylinder size and tube routing to satisfy the response time budget.

### Exercise 2B: Pressure Drop Quantification in Series Gate Cascades

Complex combinational logic circuits require cascading multiple gates, where the output of one gate feeds the input of the next. Each gate introduces pressure drop due to valve flow restrictions, and cumulative pressure loss eventually falls below the minimum actuation threshold of downstream cylinders. This exercise measures pressure drop across series gate configurations and establishes the maximum practical cascade depth.

Fabricate a modular pressure measurement apparatus using a water-filled U-tube manometer, constructible from transparent Lego pneumatic tubing and a rigid backing board. Fill a 60 cm tube segment halfway with colored water (add food dye for visibility), seal one end with a stopper or tape, and connect the open end to the pneumatic circuit via a T-junction spliced into the tube between gates. Mount the U-tube vertically on a baseplate with the water column visible alongside a millimeter ruler. When pressure is applied, the water column displaces; the height differential (in millimeters) converts directly to pressure differential via $\Delta P = \rho g \Delta h$, where $\rho$ is water density (1 g/cm³), $g$ is gravitational acceleration (980 cm/s²), and $\Delta h$ is column displacement in centimeters. For small pressures typical in Lego pneumatics, 10 mm water column displacement corresponds to approximately 0.01 psi.

Construct a series cascade of one, two, three, and four AND gates (each gate comprising two switches in series as per Exercise 1B). Connect the manometer T-junction immediately upstream of the final gate's output cylinder. Apply pump pressure and measure the water column displacement for each cascade depth. Record the cylinder extension force qualitatively by attempting to manually resist piston motion with fingertip pressure—this provides a coarse but intuitive force metric.

Empirical cascade pressure drop data from prior experiments:

- Single AND gate (two switches in series): 12 mm H₂O displacement, cylinder extends with strong force
- Two AND gates (four switches): 28 mm H₂O displacement, cylinder extends with moderate force
- Three AND gates (six switches): 51 mm H₂O displacement, cylinder extends slowly with weak force
- Four AND gates (eight switches): 78 mm H₂O displacement, cylinder fails to extend fully or stalls mid-stroke

The data indicate that cumulative pressure drop grows approximately linearly with the number of series switches, and the practical cascade limit for reliable operation is three gates deep (six switches total) before output actuation becomes unreliable. Designers confronting deeper logic must introduce pneumatic buffers: intermediate cylinders that mechanically actuate secondary pumps or valves, effectively regenerating pressure at each stage. This mirrors the buffer amplifier stages in electronic logic families.

### Exercise 2C: Duty Cycle and Fatigue Testing of Pneumatic Switches

Pneumatic switches contain elastomeric seals and return springs subject to fatigue failure under repeated actuation. This exercise characterizes switch reliability through accelerated life testing, establishing maintenance intervals for operational circuits.

Select a single pneumatic switch and mount it in a test fixture where the control port connects to a pump actuated by a motor-driven cam mechanism (construct the cam from a 12-tooth gear mounted eccentrically on an axle driven by an electric motor from a Lego Power Functions set). The cam profile must produce a full pressure pulse followed by complete vent on each rotation. Set the motor to low speed (approximately 30 RPM) to simulate realistic operational duty cycles.

Connect the switch output to a cylinder and monitor for successful extension on each cycle. Implement a cycle counter using a manual tally counter or by recording video and counting frames. Continue actuation until the cylinder exhibits failure modes: incomplete extension, slow retraction, or air leakage audible as hissing at ports. Typical failure onset occurs at 5,000–15,000 cycles, with variance depending on switch manufacturing batch and prior usage history.

Disassemble the failed switch and inspect the internal shuttle mechanism. Common failure modes include O-ring compression set (permanent deformation preventing airtight sealing), return spring plastic yielding (loss of spring force leading to incomplete shuttle return), and shuttle bore wear (enlarged clearances allowing bypass leakage). Photograph the failed components under magnification and compare to a new switch's internals. This empirical understanding informs operational maintenance protocols: critical switches in long-running automated systems require prophylactic replacement at 3,000–5,000 cycle intervals, before statistical failure onset.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Exercise 3A: Overload Testing of Pneumatic Cylinders Under Mechanical Constraint

Pneumatic cylinders develop maximum force at full bore pressure, but this force is finite and can be exceeded by external mechanical loading, leading to stall or damage. This exercise determines the failure threshold and establishes safe operating envelopes for load-bearing applications.

Construct a force measurement test rig using a lever arm and calibrated weights. Mount a medium pneumatic cylinder horizontally with the piston rod tip pressing against one end of a 1×15 liftarm acting as a rigid beam. The liftarm pivots on a fulcrum positioned five studs from the cylinder rod end (5:1 mechanical advantage). Hang a small basket from the opposite end of the liftarm, ten studs from the fulcrum. This configuration amplifies cylinder force by a factor of two, allowing convenient measurement with small weights.

Extend the cylinder fully by applying pump pressure. Incrementally add 10-gram masses to the basket while maintaining pump pressure. The cylinder will initially resist the load, maintaining full extension. Continue adding mass until the cylinder retracts visibly under load. Record the total mass at failure. For a typical Lego medium cylinder operating at approximately 2.5 psi (the maximum achievable with the small pump via repeated strokes), failure occurs at approximately 180–220 grams in the basket, corresponding to a cylinder force of approximately 360–440 grams-force (3.5–4.3 Newtons) accounting for the 2:1 mechanical advantage.

Analyze the failure mode. The cylinder retracts because the external load exceeds the pressure-area force product $F = P \times A$, where $P$ is internal pressure and $A$ is piston bore area (approximately 1.5 cm² for Lego medium cylinders). The measured failure load validates the force budget: $F = 2.5 \text{ psi} \times 1.5 \text{ cm}^2 \times 0.0703 \text{ kg/cm}^2/\text{psi} \approx 0.26 \text{ kg-force}$, or 260 grams-force, consistent with the observed 200-gram basket load amplified by the 2:1 lever ratio.

Repeat the test with a large cylinder, which exhibits higher failure loads (approximately 400–500 grams in the basket due to larger bore area). Use this empirical data to construct a load rating table for each cylinder size, specifying maximum safe continuous force and maximum intermittent force (allowing 50% safety margin below measured failure threshold). Operational circuits must never exceed the continuous force rating; intermittent overloads risk accelerated seal wear.

### Exercise 3B: Deadlock Detection and Recovery in Sequential Logic Circuits

Sequential digital circuits contain feedback loops and state memory, introducing the possibility of deadlock: stable states where the circuit becomes unresponsive to input changes. This exercise constructs a simple SR (Set-Reset) latch, induces a deadlock condition, and implements a mechanical reset protocol.

The SR latch stores a single bit of state using cross-coupled NOR gates. Construct the latch from two OR gates (Exercise 1C topology) with each gate's output feeding the opposite gate's input, creating positive feedback. Label the gates Gate A and Gate B. Gate A's additional input is the Set signal; Gate B's additional input is the Reset signal. The latch output Q is taken from Gate B's output cylinder, and the complement output $\overline{Q}$ from Gate A's output cylinder.

Operational verification begins with both Set and Reset inputs at logic low (vented). The latch should stabilize in one of two valid states: Q extended (logic high) or Q retracted (logic low), depending on initial conditions. Apply a brief pressure pulse to the Set input; Q should transition to extended and remain extended even after Set returns to low. Apply a brief pulse to Reset; Q should transition to retracted and remain retracted. This demonstrates bistable memory: the latch retains state without continuous input.

Induce the forbidden state by simultaneously applying pressure to both Set and Reset inputs. Both output cylinders attempt to extend, fighting each other through the feedback cross-coupling. The circuit enters an indeterminate oscillation or stall, with both cylinders partially extended and consuming continuous pump capacity. This is the digital logic equivalent of a race condition.

Recovery requires breaking the feedback loop temporarily. Implement a mechanical master reset by installing a manual valve in series with the pump supply line feeding both gates. Closing this valve vents all circuit pressure simultaneously, forcing both cylinders to retract via spring return and clearing the deadlock state. Open the valve and apply either Set or Reset to restore normal operation. This manual reset valve becomes a mandatory component in all sequential circuits subject to unexpected state conditions.

### Exercise 3C: Environmental Stress Testing: Temperature, Humidity, and Altitude Effects

Pneumatic systems exhibit performance sensitivity to environmental parameters that alter air density, viscosity, and elastomer properties. This exercise quantifies these effects through controlled environmental exposure, establishing operational limits for field deployment.

Temperature testing requires a thermal chamber or improvised equivalent. Construct a cold environment test by placing the assembled circuit (a simple AND gate and cylinder from Exercise 1B) inside a household refrigerator (approximately 4°C) for 30 minutes to achieve thermal equilibrium. Remove the assembly and immediately actuate the pump, measuring cylinder response time using the video analysis method from Exercise 2A. Record the ambient temperature using a digital thermometer placed adjacent to the circuit. Repeat the test after allowing the assembly to return to room temperature (approximately 22°C), and again after heating the assembly to approximately 35°C by placing it near (not on) a heat lamp for 15 minutes.

Empirical results from prior testing cycles:
- At 4°C: response time increases by 25–40% relative to room temperature baseline due to increased air viscosity and reduced elastomer compliance.
- At 35°C: response time decreases by 10–15% due to decreased air viscosity, but tube flexibility increases, introducing potential kinking and flow restriction if tubes are bent sharply.

Humidity effects manifest as condensation within tubes and cylinders at high humidity (above 80% RH) combined with temperature cycling. Simulate this condition by storing the circuit in a sealed container with a wet sponge overnight, then bringing it to room temperature. Actuate the pump and observe for water droplets expelled from the cylinder exhaust port. Accumulated condensate reduces effective swept volume and can cause sluggish actuation or stalling. Prevention requires periodic venting: store circuits in low-humidity environments or install inline desiccant dryers fabricated from perforated Technic bricks filled with silica gel beads.

Altitude effects alter absolute air pressure, reducing the pressure differential achievable by fixed-displacement pumps. Simulate altitude by operating the circuit inside a vacuum chamber (if available) or by noting performance degradation when operating at actual high altitudes (above 2,000 meters elevation). At 3,000 meters, atmospheric pressure drops to approximately 70% of sea level, proportionally reducing maximum cylinder force. Compensate by increasing pump stroke count or substituting larger-bore cylinders.

Document all environmental test results in a tabular format specifying operational limits:

| Parameter | Minimum | Maximum | Nominal | Failure Mode Outside Range |
|-----------|---------|---------|---------|----------------------------|
| Temperature | 0°C | 40°C | 20–25°C | Sluggish actuation (cold), tube kinking (hot) |
| Humidity | 20% RH | 70% RH | 40–50% RH | Condensate accumulation (high humidity) |
| Altitude | 0 m | 2,000 m | Sea level | Reduced force (high altitude) |

## Operational Reference Guide & Diagnostic Checklist

### Systematic Troubleshooting Protocol for Pneumatic Logic Circuits

When a pneumatic logic circuit exhibits unexpected behavior, execute this diagnostic tree in order:

**1. Verify Power Supply (Pump Function):** Disconnect all tubes from the pump output and actuate the pump. A properly functioning pump expels a strong air jet audible and palpable at the output port. If the pump produces weak output or no output, disassemble the pump housing, inspect the piston O-ring for wear or displacement, and verify the check valve ball moves freely. Replace damaged O-rings with spares from sacrificed pneumatic components.

**2. Isolate Circuit Sections:** Disconnect tubes systematically, starting from the output cylinder and working backward toward the pump. Connect the pump directly to the cylinder, bypassing all logic gates. If the cylinder now extends properly, the fault lies in the gate circuit. If the cylinder still fails, the cylinder itself is defective.

**3. Inspect Tube Integrity:** Examine every tube segment for splits, kinks, or incomplete port insertion. A tube pulled halfway out of a port creates a massive leak, rendering the circuit inoperative. Re-seat all tubes with firm pressure until the insertion depth reaches approximately 5 mm and the tube resists pull-out force.

**4. Test Individual Gates:** Connect the pump directly to each gate's common port and manually actuate the control port by applying pressure via a handheld tube. The output port should exhibit strong airflow when the gate is in the passing state. If airflow is weak or absent, disassemble the switch, clean debris from the shuttle bore, and verify O-ring integrity.

**5. Check for Feedback Loop Deadlocks:** In sequential circuits, verify that no two gates are simultaneously commanding contradictory states to the same actuator. Trace signal paths through the circuit using colored tape markers on tubes, confirming that feedback paths do not create logic conflicts.

**6. Measure Timing Margins:** Record actuator response times using video analysis. If measured times exceed design specifications from Exercise 2A by more than 50%, the circuit has developed leaks or internal friction. Replace suspect components and re-verify.

### Component Specification Reference Table

| Component | Key Dimensions | Pressure Rating | Typical Response Time | Failure Modes | Replacement Interval |
|-----------|----------------|-----------------|----------------------|---------------|----------------------|
| Small Pump | 2×4 stud footprint | 3.0 psi max output | N/A (manual actuation) | Piston O-ring wear, check valve jamming | 10,000 strokes |
| Small Cylinder | 1.5 cm³ swept volume | 4.0 psi max | 45 ms (10 cm tube) | Piston seal leakage, rod binding | 15,000 cycles |
| Medium Cylinder | 3.0 cm³ swept volume | 4.0 psi max | 70 ms (10 cm tube) | Piston seal leakage, spring fatigue | 12,000 cycles |
| Pneumatic Switch | 2×4 stud footprint | 4.0 psi max | 25 ms shuttle travel | Shuttle O-ring wear, spring failure | 5,000 cycles |
| Pneumatic Tubing | 4 mm outer diameter | 5.0 psi max | N/A | Splitting at port junction, kinking | 500 insertion/removal cycles |

### Advanced Circuit Design Guidelines

**Minimize Tube Length:** Route tubes along the shortest geometric path between components, avoiding unnecessary slack. Use rigid structural elements (beams, axles) as tube guides to prevent sagging and kinking. Every 10 cm of tube length adds approximately 15–25 ms propagation delay.

**Match Cylinder Size to Load:** Oversizing cylinders increases response time and air consumption without benefit. Undersizing causes stalling under load. Use the force calculation $F = P \times A$ with measured pump pressure (approximately 2.5 psi for small pumps) and catalog cylinder bore areas to select the minimum cylinder size meeting force requirements with 50% safety margin.

**Implement Pressure Regulation:** For circuits requiring precise timing, install a pressure accumulator fabricated from a sealed rigid container (e.g., a Lego storage box) connected via tubes to the pump output. The accumulator volume buffers pressure fluctuations, stabilizing actuator response times. Size the accumulator volume to at least ten times the total swept volume of all cylinders in the circuit.

**Parallel Redundancy for Reliability:** Critical actuators in safety-related applications should be driven by redundant parallel gates, each capable of independently commanding the actuator. This topology tolerates single-gate failure without loss of function, analogous to fail-safe redundancy in electronic control systems.

**Document Circuit State Transitions:** For sequential circuits, maintain a state transition diagram annotating each stable state, the input conditions triggering transitions, and the expected output states. During troubleshooting, manually walk through the state diagram with the physical circuit, verifying that observed transitions match predictions. Discrepancies indicate misunderstood feedback paths or undocumented gate interactions.

### Photographic Documentation Standards

Maintain a laboratory archive of high-resolution photographs for every completed circuit, captured from standardized perspectives:

- **Top View:** Camera positioned directly overhead, capturing the complete circuit footprint with all tube routing visible. Use a contrasting background (white paper or baseplate) to isolate the assembly.
- **Front Elevation:** Camera at the same height as the circuit midpoint, perpendicular to the primary actuation axis. Frame to include all input ports, gates, and output actuators.
- **Tube Routing Detail:** Close-up shots of each tube junction showing insertion depth, bend radius, and port alignment.
- **Failure Modes:** Photograph damaged components (split tubes, worn O-rings, failed springs) alongside new components for visual comparison.

Annotate all photographs with scale references (include a ruler in frame) and label input/output ports using image editing software or physical labels affixed adjacent to ports before capture. Archive photographs in a structured directory hierarchy: `/Labs/DigitalDesign/Exercise[N]/[CircuitName]/` with consistent filename conventions: `[CircuitName]_TopView_[Date].jpg`.

This documentation protocol enables future practitioners to replicate circuits without ambiguity and provides forensic evidence for failure analysis. The rigor applied to mechanical construction must extend equally to knowledge capture; an undocumented working circuit holds no more instructional value than a failed experiment.
