# Lesson 3: Linkages, Pneumatics, Linear Actuators

## 1. First-Principles Intuition & Invariants

Machines do not create motion — they redirect it. This is perhaps the most important principle a Technic engineer internalizes early, because it frames every mechanism not as a source of force but as a transformer of it. A motor spinning at 380 RPM under no load is a kinetic reservoir waiting to be shaped: slowed and amplified through gearing, converted from rotation into translation through a crank, or stored and released through pneumatic pressure. Linkages, pneumatics, and linear actuators are the three primary vocabularies through which Technic achieves this transformation, and mastering each requires understanding not just how the parts connect, but *why* a given geometry produces a specific class of motion.

The conceptual bedrock here is the **degree of freedom** (DOF). Every rigid Technic liftarm or beam is, in isolation, capable of moving through six independent modes: three translational and three rotational. When you pin two beams together at a single pivot, you constrain five of those six DOFs, leaving one — rotation about the pin axis. Each additional pin or link you introduce removes more freedom from the system. A four-bar linkage, for instance, presents four such constrained joints arranged in a closed kinematic loop, and the interplay of those four constraints is what produces the linkage's characteristic coupler curve — the elegant, non-circular path traced by the midpoint of the connecting rod. Grübler's formula makes this precise: for a planar mechanism, the number of degrees of freedom equals three times the number of moving links, minus twice the number of full joints. A four-bar linkage has three moving links and four joints, yielding 3(3) − 2(4) = 1 DOF. That single remaining degree of freedom is exactly what gives the linkage its mechanical determinism: drive the input crank and the output behavior is completely specified by the geometry.

This is the fundamental invariant of linkage design. You are not fighting physics; you are negotiating with geometry. Change the relative lengths of the four bars and you change the character of the output motion entirely. This is why the Technic catalog contains axle holes spaced at every beam unit interval — the builder is being handed a discrete-geometry workshop in which every new hole position represents a different kinematic contract with the mechanism.

Pneumatics introduces a different first principle: **pressure as a reversible force store**. Unlike a spring, which exerts force proportional to displacement, a pneumatic cylinder at steady pressure exerts a force proportional only to its piston area. The relationship is F = P × A, where F is thrust force in Newtons, P is gauge pressure in kilopascals, and A is piston cross-section in square meters. Lego's pneumatic cylinders present a fixed bore diameter, so within a given model the only variable the builder controls is the supply pressure — determined by how many pump strokes have charged the reservoir, or whether the small electric compressor (part 88000) is in the system. At roughly 15–30 psi of operating pressure in typical Lego pneumatic circuits, the small cylinder (part 74981c01) generates on the order of 15–25 Newtons of push force, while the large cylinder (part 2793c01) can reach 40–60 Newtons depending on circuit pressure. These are real forces capable of actuating heavy payload mechanisms, which is precisely what makes pneumatics valuable and what makes pressure management non-trivial.

Linear actuators, specifically the Power Functions and Powered Up electric linear actuators (part 61927c01 and its successors), trade the analog force profile of pneumatics for precise, digitally commandable positioning. They extend and retract by driving an internal lead screw through a small DC motor, converting rotation into translation with a fixed mechanical advantage built into the thread pitch. The actuator travels its full stroke in approximately two to three seconds at 9V, and because it is driven by a reversible motor, it holds its last position under load through the irreversibility of the lead screw — functionally acting as a self-locking linear stage. This self-locking characteristic is worth understanding deeply: the thread helix angle is shallower than the friction angle of the screw interface, which means back-driving the screw requires more torque than the applied load can generate through the thread geometry. The load is mechanically trapped, not electrically held. This is the same principle that makes a worm gear self-locking, and it is enormously useful for maintaining boom angles, platform positions, and suspension geometries without continuous motor power.

---

## 2. Core Architecture & Mechanics

### Four-Bar Linkages: Geometry as the Machine

The four-bar linkage is the simplest closed kinematic chain capable of producing useful output motion, and it is worth spending real time with before reaching for more exotic mechanisms. The four members are conventionally named: the **ground link** (the fixed frame, typically your Technic frame beam), the **input crank** (driven by motor or hand), the **coupler** (the floating link connecting input to output), and the **output rocker** (the link connected back to ground at the far end). The behavior of the whole system is entirely determined by the ratio of these four lengths.

The Grashof condition governs whether the input link can rotate fully (a *crank*) or only oscillate (a *rocker*). If the sum of the shortest and longest link lengths is less than or equal to the sum of the remaining two links, then at least one link can fully rotate — the Grashof condition is satisfied. When the shortest link is the ground link, you get a double-crank mechanism where both input and output can fully rotate. When the shortest link is the input, you get a crank-rocker — the most common configuration in Technic models — where the input crank spins continuously while the output rocker sweeps back and forth through an arc. When the shortest link is the coupler, both the input and output are rockers and the mechanism is a double-rocker: neither end can fully rotate, but the coupler itself can. This is the geometry used in Technic steering mechanisms, where neither the steering input linkage nor the wheel carrier needs to spin fully — they only need to sweep through a moderate angle with well-defined end stops.

In Technic practice, all four bar lengths must be constructed from integer multiples of the stud unit (8mm per stud pitch, noting that axle holes on liftarms are spaced at 8mm center-to-center). This discretization is simultaneously a constraint and a gift: it forces you to work from a finite catalog of geometries, which means the community has thoroughly mapped the design space. A crank-rocker using a 3-stud crank, 5-stud coupler, 4-stud rocker, and 7-stud ground link, for example, produces a rocker sweep of approximately 65°, which is well-matched to a Technic gear rack travel range. Adjust the crank to 2 studs and the coupler to 6 studs, and the dwell behavior at the extreme positions changes substantially — the output rocker slows and nearly pauses near its limits, a behavior called *approximate dwell* that is enormously useful for synchronized pick-and-place mechanisms where you want the working end to linger momentarily while other parts of the machine complete their cycle.

```
Four-Bar Linkage — Crank-Rocker Configuration (Top View, Schematic)

GROUND LINK (Fixed Frame Beam)
 A ════════════════════════════════ D
 |                                  |
 |  INPUT CRANK (length r)          | OUTPUT ROCKER (length l)
 |                                  |
 B ————————————————————————————— C
        COUPLER (length c)

A, D : Fixed pivots bolted to frame (Ø3.2mm Technic pins)
B    : Driven crank pin (rotates about A)
C    : Coupler-rocker joint (floating)
B→C  : Coupler liftarm
D→C  : Output rocker liftarm

Grashof check:  min(r, c, l, ground) + max(r, c, l, ground)
                ≤ sum of remaining two lengths
                → Satisfied → crank can rotate 360°
```

The coupler curve — the path traced by any point attached to the coupler link other than its two endpoints — is a sixth-degree algebraic curve that can approximate straight lines, figure-eights, and near-circular arcs depending on the geometry. The practical significance is profound: by mounting a payload or a tool at a carefully chosen point along the coupler, you can synthesize nearly straight-line motion without rails or sliders, using only pivoting links. Roberts and Chebyshev independently discovered linkage geometries that trace near-perfect straight lines in the mid-19th century; in Technic, you replicate these findings empirically by sliding the mounting hole of a 3L axle along the coupler beam and observing how the path character changes. Near the midpoint of the coupler in a symmetric geometry, the path tends toward a straight line. Near the endpoints, it curves aggressively.

### Crank and Slider Mechanisms

The crank-slider converts continuous rotation into reciprocating linear motion — or the reverse. In Technic, the slider is usually a liftarm or beam constrained to slide along a channel formed by parallel Technic bricks or studless frame rails. The crank is a short arm mounted on an axle, connected to the sliding member by a coupler rod. The kinematics are asymmetric: the forward stroke (crank moving in the direction that keeps the coupler most nearly aligned with the direction of travel) is slower and generates more force than the return stroke. This asymmetry is intentional in mechanisms like a bulldozer blade actuator or a pneumatic pump arm, where the power stroke demands maximum force and the return only needs to reset position quickly.

For a crank of radius r driving a slider through a coupler of length L, the slider displacement x as a function of crank angle θ is:

$$x(\theta) = r\cos\theta + \sqrt{L^2 - r^2\sin^2\theta}$$

In practice, when L is at least four times r (a ratio easily achieved in Technic by using a 2-stud crank with a 9-stud coupler), the motion approximates a simple sinusoid closely enough that you can treat it as such for timing purposes. When L/r is small — a 3-stud crank with a 4-stud coupler, for instance — the asymmetry becomes significant and pronounced dwell behavior appears at the crank's dead-center positions.

### Pneumatic Circuit Architecture

A Lego pneumatic circuit has three functional zones: the **pressure source**, the **distribution network**, and the **actuators**. Understanding each zone independently before integrating them prevents the most common failure mode in Technic pneumatics, which is not mechanical breakage but circuit leakage.

The pressure source is either manual (the hand pump, part 74981c01) or electric (the compressor motor assembly). The manual pump is a single-acting piston: each downstroke compresses air into the outlet tube. Because the pump valve only opens when the outlet pressure is below the pump compression pressure, it has a natural cutoff — once circuit pressure equals what the pump can generate (~30 psi at full stroke), no further air enters regardless of how vigorously you pump. The electric compressor operates on the same principle but runs continuously, which means you must include a pressure relief valve or a pressure accumulator (a sealed Lego reservoir, part 76765) if the compressor is running against closed valves. Without a reservoir, the circuit pressure climbs to the point where the compressor motor stalls against back-pressure, drawing locked-rotor current and generating heat.

The distribution network is simply the interconnecting tubing — Lego's 3mm OD pneumatic hose, available in multiple lengths. Its internal volume is not trivial: a 20-stud run of tubing contains roughly 0.5 cm³ of air volume, which matters when you are trying to understand why cylinder response lags the valve actuation. Each centimeter of additional tubing adds dead volume that must be pressurized before the cylinder begins to move. In high-speed mechanisms where timing is critical, minimize tube run lengths and avoid coils or sharp bends that restrict airflow.

```
Pneumatic Circuit — Dual-Cylinder Actuation (Schematic)

                          ┌─────────────┐
                          │  RESERVOIR  │ ←── Electric Compressor
                          │  (76765)    │     or Manual Pump
                          └──────┬──────┘
                                 │
                        ┌────────┴────────┐
                        │   3-PORT VALVE  │ (Part 71206)
                        │  (A) | OFF | (B)│
                        └───┬─────────┬───┘
                            │         │
                     ┌──────┴──┐   ┌──┴──────┐
                     │  CYL A  │   │  CYL B  │
                     │ EXTEND  │   │ EXTEND  │
                     └─────────┘   └─────────┘

Valve center position vents both cylinder ports to atmosphere.
Valve (A) position pressurizes Cyl A, vents Cyl B.
Valve (B) position pressurizes Cyl B, vents Cyl A.
Reservoir decouples pump duty cycle from cylinder response speed.
```

Lego's switching valve (part 71206) is a three-position, three-port spool valve. In its center (off) position, both outlet ports are open to atmosphere, which means connected cylinders go slack — their pistons can be pushed freely by external loads. This is a critical circuit behavior to design around: if your pneumatic arm is supporting a load and the valve returns to center, the arm will fall. The design solution is to either keep the valve in an energized position when holding load, or to use a mechanical latch — a Technic ratchet or over-center linkage — to provide mechanical retention independent of circuit pressure.

Dual-cylinder actuation multiplies available force when both cylinders are arranged in parallel (both connected to the same valve port, both pushing in the same direction). Two small cylinders in parallel provide approximately twice the thrust of one, since the pressure acts on the sum of both piston areas. Connecting them in series — where the rod of Cylinder A pushes the body of Cylinder B — doubles stroke length at the same force, because only the pressure on the first cylinder's piston generates thrust; the second cylinder just transmits it. This is an important distinction that builders frequently get backwards, connecting cylinders in series expecting more force when they actually need more stroke.

### Linear Actuator Mechanics and Integration

The Technic electric linear actuator is built around a 7.1mm-pitch trapezoidal lead screw driven through a 5:1 worm gear reduction internal to the housing. The worm gear serves two purposes: it steps down the motor speed to a useful linear travel rate, and it provides the self-locking behavior already discussed. The actuator's full stroke is approximately 28mm, with mechanical end stops that stall the motor when reached. Because the internal motor is unprotected against continuous stall current, any control system driving an actuator must either include current sensing with a timeout or rely on timed pulses that stop well before the mechanical limits.

In Powered Up systems, the linear actuator is treated as a plain motor output — the hub sends PWM signals to the actuator's internal motor, and speed is controlled by duty cycle. The actuator itself provides no position feedback; if positional control is required, the builder must mount an external sensor. A Powered Up color sensor aimed at a printed indicator strip mounted to the actuator rod, or a touch sensor tripped by a flag at a specific extension, are both common and effective solutions. For applications requiring only two positions (fully extended and fully retracted), timed moves are the simplest approach: empirically measure the full-stroke travel time at your operating voltage, then command moves of that duration from each end-stop, allowing the end-stop stall to establish absolute reference at each limit.

---

## 3. High-Performance Optimization & Failure Modes

### Linkage Optimization: Stiffness, Clearance, and Timing

The most pervasive failure mode in Technic linkages is not geometric miscalculation but structural compliance — the linkage deflects under load because the liftarms are bending, the pins are rocking in their holes, or the frame is twisting at its attachment points. Each of these compliance paths absorbs the geometric precision you built into the kinematic design. A crank-rocker that traces a beautiful near-linear coupler curve in CAD or slow hand-motion will exhibit hysteresis under load: the output position when approaching from one direction will differ from the output position when approaching from the other, because the elastic deflection of the structure changes sign when the load direction reverses. This is not a kinematic problem — it is a structural one, and it is solved structurally.

For high-load linkages, build redundancy into every pin joint. A single half-pin connecting two liftarms at a floating joint can rock by as much as 1–2° under lateral load. Replace it with a full-length friction pin and a lock bush on the far side, or better, build the joint as a double-shear connection where the loaded liftarm rides between two frame liftarms and is captured by a full axle running through all three layers. Double-shear joints divide the bending moment on the pin between two shear planes, reduce deflection by roughly four times compared to a cantilever (single-shear) joint of the same pin length, and prevent the rocking that disrupts coupler curve accuracy.

Bearing alignment is equally important. Whenever a powered axle drives a crank, the axle must be supported on both sides of the crank by bushings or beam holes. An unsupported cantilevered crank places a bending moment on the axle at the crank attachment point, and under load, the axle bends enough to introduce angular error into every downstream link. Mount the crank between two supported beam layers with the crank face flush against one beam and the crank secured with a lock bush against the other. The axle then runs in double bearing, the crank sees pure torsion rather than combined bending and torsion, and deflection drops dramatically.

Timing across multiple linkages — necessary whenever a machine coordinates two or more coupled mechanisms, as in a walking robot or a pick-and-place crane — depends on the angular phase relationship between the input cranks. In Technic, phase is set by the angular position of each crank on its driving axle. Because Technic axles are square cross-section and crank hubs engage on that square profile, phase adjustment is discrete in 90° increments unless you use a differential or worm gear stage to introduce continuous phase offset. For most four-limbed walking mechanisms, a 90° phase offset between paired legs provides stable gait geometry; for a two-cylinder reciprocating mechanism, 180° phase keeps the net load on the driving axle more constant, reducing torque ripple and axle wind-up.

### Pneumatic Failure Modes and Pressure Management

Leakage is the dominant failure mode in Lego pneumatic circuits, and it manifests in two forms: connector leakage at tube-to-fitting interfaces, and valve leakage through the spool seal. Connector leakage increases with age because the soft polyurethane tubing develops a permanent set around the connector barb, reducing the interference fit that creates the seal. The fix is mechanical: trim 3–5mm of aged tubing from each end before reconnecting, exposing a fresh cross-section of unhardened material. If the tube is too short to trim, replace the run entirely. Never attempt to seal a leaking Lego pneumatic fitting with sealant compounds — the polymer chemistry of the tubing and fittings is incompatible with most sealants, and the residue contaminates the spool valve.

Valve leakage across the spool causes continuous slow pressure loss from the reservoir even with no cylinders moving. The spool seals are small O-rings molded into the valve body, and over decades they dry out and lose elasticity. Light re-lubrication with a silicone-based grease (not petroleum-based, which attacks the rubber) applied to the spool by partial disassembly of the valve usually restores a full seal. If the valve cannot be restored, it must be replaced — a leaking valve makes pressure management impossible and means the compressor motor runs continuously at light load, reducing its service life.

Over-pressurization is a less common but more dramatic failure mode. At pressures above approximately 40 psi, Lego pneumatic hose begins to balloon visibly at connectors and can separate entirely. The electric compressor is not capable of generating damaging pressures on its own (its motor stalls before that point), but manual pumping with a large-volume external pump connected to the Lego system can exceed safe limits. Keep all pneumatic circuits within the Lego native system — use only Lego pumps, Lego compressors, and Lego tubing — and over-pressurization is not a practical risk.

Speed control in pneumatic circuits is achieved by restricting airflow, not by reducing pressure. A flow restrictor — a simple in-line fitting with a reduced bore — slows the cylinder movement by limiting the volumetric flow rate into the cylinder even though circuit pressure remains constant. In Lego terms, this is approximated by using narrower-bore connectors or looping a portion of the tube through a 90° T-fitting that partially bleeds flow, though the native Lego catalog does not include purpose-built adjustable restrictors. Empirical tuning with tube length (longer tube = more restriction) is the practical approach. For cylinders that must move slowly and predictably, a tube run of 300–500mm (using a looped extension) provides useful flow restriction and softens the cylinder's end-of-stroke impact, reducing mechanical shock to the linkage.

### Linear Actuator Failure Modes and Integration Pitfalls

The most common actuator failure is side-loading — applying a force perpendicular to the actuator's axis of travel. The actuator rod is an unsupported round bar guided only by the internal lead screw thread and a small bronze bushing at the rod exit. Any lateral force at the rod tip creates a bending moment on that bushing, which wears rapidly and eventually allows the rod to wobble, introducing backlash. In linkage systems, side-loading occurs whenever the coupler attached to the actuator rod is not aligned with the actuator's axis at mid-stroke. The design solution is to introduce a spherical joint or a pivot pin at the rod tip that allows the coupler to adopt small angular offsets without transmitting bending moments into the rod. In Technic, a simple Ø3.2mm ball joint connector (part 32174, the ball-with-pin), captured in a matching socket liftarm at the actuator rod end, accomplishes exactly this.

Thermal performance degrades when actuators are run continuously near their mechanical end-stops. The internal motor draws 2–3× its running current when stalled, and if a control loop commands repeated full-stroke sweeps without adequate dwell time, the motor winding temperature rises to the point where the brush commutator develops intermittent contact resistance. This manifests as erratic speed — the actuator moves normally for several strokes, then slows or jerks mid-travel. The fix is dwell time: add at least 0.5 seconds of pause at each end-stop position, allowing the motor to cool and the PTC thermal protection in the Powered Up hub to reset if it has tripped.

Finally, the interaction between pneumatic cylinders and four-bar linkages deserves explicit attention because it is simultaneously the most powerful combination in Technic and the most demanding to get right. A pneumatic cylinder driving the input crank of a four-bar linkage creates a system where force, velocity, and mechanical advantage all vary continuously around the crank cycle — the linkage transforms the constant-force, constant-pressure output of the cylinder into a force profile that peaks near the crank's dead-center positions (where the cylinder has maximum mechanical advantage on the crank) and dips near mid-stroke. This is not a bug; it is a feature. Design the linkage so that the high-force portion of the output motion coincides with the phase angles where the cylinder's mechanical advantage on the crank is highest, and you effectively amplify the pneumatic force precisely where the application demands it most.

A well-tuned Technic crane boom, for instance, positions the pneumatic cylinder so that its attachment to the boom arm places it near perpendicular to the boom at the highest-load configuration — typically when the boom is nearly horizontal and carrying maximum payload. At that angle, the cylinder force has its greatest moment arm around the boom pivot, the four-bar geometry is in its highest-mechanical-advantage phase, and the structural loads on the frame are distributed most evenly. This is not accident; it is synthesis. It is the product of understanding linkage kinematics, pneumatic force characteristics, and structural loading simultaneously, and designing the geometry to make all three peak in the same phase of the cycle. That convergence — the moment when geometry, force, and structure all align — is the hallmark of a master-level Technic mechanism.
