# Lesson 3: Ball Dynamics: Paths, Drops, and Separation Mechanics

## 1. First-Principles Intuition & Invariants

Every Great Ball Contraption module is, at its mechanical heart, a negotiation between gravity and structure. The ball—a 32mm Lego soccer ball or the slightly smaller 25mm basketball variant—carries kinetic energy it did not earn through the contraption's own effort. It earned it from the motor that lifted it, the ramp that guided it, the chute that released it. By the time it arrives at a junction, a drop, or a separation gate, every joule of that energy has a history, and the job of the GBC engineer is to honor that history without waste.

The first invariant every advanced practitioner must internalize is that ball velocity is not a parameter you set—it is a parameter you inherit. The exit speed at the top of one module's lift becomes the entry condition for the next module's intake. This coupling is what makes GBC chains fragile under naive design and elegant under disciplined design. When you trace the energy path of a single ball from intake bowl to output chute, you are tracing a closed contract: the ball arrives within a velocity window, traverses your mechanism within a timing window, and departs within a geometry window that your downstream neighbor has already specified. Violate any of these three windows and the chain stalls.

Gravity is not an adversary in this system—it is the primary actuator. A drop of one stud height (8mm) imparts approximately 0.078 m/s² of acceleration to any ball of standard Lego mass (roughly 10–12 grams), but the practical consequence of this is felt through *contact geometry* far more than through raw speed. A ball dropping onto a flat horizontal tile bounces chaotically; the same ball dropping onto a curved receiver channel loses most of its vertical component through controlled deflection and exits with predictable horizontal momentum. The shape of the receiving surface is therefore the most powerful velocity-management tool available to you, and it costs nothing but intentional design.

The second invariant is *lane geometry determinism*. In a parallel-path architecture—where balls must be distributed across two or more lanes, hoppers, or sub-modules—the moment of separation must be mechanically unambiguous. A ball that hesitates at a bifurcation point, touching both lanes simultaneously, is a jammed ball. The separation geometry must commit the ball to one path before it has time to settle into an ambiguous straddling posture. This requires the lane divider to be narrower than the ball diameter (32mm) at the point of contact, so the ball's center of mass falls decisively to one side. The practical minimum for a reliable passive divider is a 1-stud-wide ridge (8mm) terminated in a chamfered or studless tile face, positioned such that the ball contacts it while still carrying at least 60–70% of its entry momentum. A stationary ball at a divider is a problem waiting to happen.

Trajectory prediction in Lego GBC is not a calculus exercise—it is a tactile calibration discipline. The standard Technic beam grid gives you an 8mm spatial resolution, which means that horizontal trajectory errors accumulate in 8mm steps and vertical drop heights are multiples of 3.2mm (one plate) or 9.6mm (one brick). An experienced GBC builder develops what might be called *stud-space intuition*: the ability to look at a chute exit angle and immediately calculate where on the receiver surface the ball will land, in units of studs and plates rather than meters and centimeters. This intuition is built not through mathematics but through deliberate physical prototyping—launching balls from known heights at known angles over graph-paper mockups, then transcribing the landing coordinates back into beam-and-plate offsets.

The third invariant governs *separation timing* in motorized switching mechanisms. When a Powered Up or Power Functions motor drives a physical gate or diverter paddle, the ball's arrival at the gate and the gate's position must be synchronized within a margin no wider than the ball's diameter divided by its approach velocity. For a typical GBC ball entering a switch at 0.3 m/s, this margin is roughly 100 milliseconds. Any microcontroller or Powered Up hub command latency, motor spin-up time, or mechanical backlash in the gate linkage that consumes more than half of that margin will produce intermittent misrouting. This is not a software problem—it is a mechanical problem expressed through software symptoms, and it must be solved at the structural level before any timing adjustment in firmware will help.

---

## 2. Core Architecture & Mechanics

### The Anatomy of a GBC Ball Path

A complete ball path from module intake to module output can be decomposed into five distinct mechanical zones, each with its own geometry constraints and failure modes. Understanding these zones as a system rather than as independent components is what separates a practitioner who builds reliable chains from one who spends event hours clearing jams.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     GBC BALL PATH ARCHITECTURE                          │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  INTAKE  │───▶│  LIFT /  │───▶│  TRANSIT │───▶│SEPARATION│          │
│  │  ZONE    │    │  DRIVE   │    │  CHUTE   │    │  GATE    │          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│       │                                                │                │
│       │            Ball arrives with                  │                │
│       │            inherited velocity                 ▼                │
│       │                                      ┌────────────────┐        │
│       │                                      │   PATH A       │        │
│       └──────────────────────────────────────│   PATH B       │        │
│                                              └────────────────┘        │
│                                                        │                │
│                                                        ▼                │
│                                               ┌──────────────┐         │
│                                               │   OUTPUT /   │         │
│                                               │   HANDOFF    │         │
│                                               └──────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

The **intake zone** sets the entry condition for every downstream event. Its critical dimension is the mouth width: for 32mm balls, a minimum clear width of 36mm (four and a half studs, achievable with a half-stud-offset bracket on one wall) prevents jamming on entry while still constraining lateral drift. The floor of the intake should slope inward at 15–20 degrees toward the lift mechanism—shallow enough that multiple balls do not avalanche simultaneously, steep enough that a resting ball will roll under gravity alone without motor assistance. This angle, in Lego geometry, corresponds to a rise of 1 plate (3.2mm) over a run of approximately 2 studs (16mm), giving a natural 11-degree slope. Achieving the target 15–20 degrees requires either a 2-plate rise over 2 studs (21 degrees—acceptable) or a 1-plate rise over 1.5 studs (12 degrees—marginal but functional for smooth-floored channels).

The **transit chute** is where trajectory physics becomes the dominant design variable. A straight chute angled between 25 and 40 degrees to horizontal produces the most predictable exit conditions. Below 25 degrees, ball speed is insufficient to clear the chute reliably under its own gravity—any surface friction or ball-to-ball contact causes stalls. Above 45 degrees, exit velocity becomes difficult to dissipate at the receiver, leading to bouncing and overshoot. The 30-degree sweet spot is achievable in Technic geometry using a 3-4-5 Pythagorean liftarm triangle: a vertical rise of 3 liftarm units (24mm) and a horizontal run of 4 liftarm units (32mm) gives a hypotenuse of 5 units and an angle of exactly 36.87 degrees—close enough to 37 degrees that it performs identically to a 35-degree chute for all practical purposes.

The sidewall treatment of the chute matters more than most builders initially recognize. Studded inner walls create periodic 0.8mm bumps that induce micro-deflections in the rolling ball's trajectory, accumulating over a long chute into exit-angle uncertainty of ±3–5mm. This is negligible for single-path delivery but becomes a critical error source when balls must land in a narrow receiver funnel at the end of the chute. The fix is straightforward: apply smooth tiles to all ball-contact surfaces inside the chute. The transition from studded to tiled floor must itself be flush—a tile edge that protrudes even one plate height above the adjacent surface will catch fast-moving balls and impart an upward deflection at the exit.

### Passive Separation: The Wedge Divider

The simplest and most reliable separation mechanism requires no motor, no sensor, and no timing logic. It exploits the fact that a ball approaching a ridge along its centerline is in an unstable equilibrium: any lateral asymmetry in the approach vector commits it to one side. In practice, a staggered alternating-deflection wedge can achieve 50/50 distribution across two lanes without any active control, using nothing more than a carefully placed 1×2 Technic brick with a hole, oriented perpendicular to the ball path, with a half-stud offset toward one lane. The first ball deflects left; its passage slightly disturbs the wedge surface, biasing the second ball right. Over hundreds of balls, this passive stochastic system converges to near-equal distribution, provided the ball approach velocity is consistent.

```
           BALL APPROACH DIRECTION
                     │
                     ▼
         ════════════╪════════════  ← chute floor (tiled)
                     │
                  ┌──┴──┐
                  │ridge│  ← 1-stud-wide divider
                  └──┬──┘
                     │
           ┌─────────┴─────────┐
           ▼                   ▼
         LANE A              LANE B
      (left path)         (right path)
```

The divider must be positioned so that the ball contacts the ridge *before* it decelerates to below 0.15 m/s. Below this velocity threshold, surface friction dominates over momentum, and the ball will seek the nearest concavity rather than be deflected by the ridge—meaning it will jam against the divider instead of splitting from it. If your chute exit velocity is marginal, raising the chute's upstream angle by 3–4 degrees (one plate of rise added to the support structure) is preferable to any attempt to reduce divider friction, since the ball's momentum budget must be solved at the energy input stage.

### Active Separation: Motor-Driven Gate with Powered Up Hub

For GBC configurations where unequal distribution or sequenced routing is required—feeding a faster sub-module preferentially, or alternating between three output hoppers in a defined pattern—a Powered Up Large Angular Motor driving a rotating gate paddle gives the builder precise positional control with ±3-degree accuracy at typical operating speeds.

The gate paddle itself should be fabricated from a 1×6 Technic liftarm (or two overlapping 1×4 liftarms for stiffness) mounted to the motor output via a cross-axle coupler, rotating through a 60–90 degree arc. At the 0-degree position it blocks Path A and opens Path B; at the 60-degree position it blocks Path B and opens Path A. The critical mechanical detail is the *gate seal geometry*: the paddle must not simply block a path, it must positively guide the ball into the open path. A purely blocking gate that closes one lane leaves the ball with nowhere to go for the 100ms window during which it bridges the transition. A guiding gate uses the paddle face itself as a curved deflection surface, so the moment the ball contacts the paddle it is already being redirected toward the open lane.

The timing of the gate cycle is driven by the module's known ball throughput rate. A well-tuned GBC module delivers balls at 1 ball per second (1 BPS) at the standard rate, with peaks up to 2 BPS for high-performance designs. A gate switching at 0.5 Hz will route balls in an approximately alternating pattern at 1 BPS. When using the Powered Up app's Scratch-based block programming environment, or the SPIKE Prime hub's MicroPython runtime for more precise control, the switching command is best issued on a fixed timer interrupt rather than on a ball-sensing event, because sensor latency and ball approach variability together introduce more timing uncertainty than a well-calibrated open-loop schedule.

The following MicroPython routine for a SPIKE Prime hub implements a fixed-cadence gate cycle with configurable dwell time per lane. This runs entirely within the LEGO SPIKE app's MicroPython interpreter—no external tooling required.

    from hub import port
    import motor, time

    GATE_MOTOR = port.A
    PATH_A_ANGLE = 0        # degrees: gate directs to Lane A
    PATH_B_ANGLE = 65       # degrees: gate directs to Lane B
    DWELL_MS     = 1200     # milliseconds per lane (adjust for ball rate)
    SPEED        = 500      # motor speed in degrees/second

    motor.run_to_absolute_position(GATE_MOTOR, PATH_A_ANGLE, SPEED)
    time.sleep_ms(500)

    while True:
        motor.run_to_absolute_position(GATE_MOTOR, PATH_B_ANGLE, SPEED)
        time.sleep_ms(DWELL_MS)
        motor.run_to_absolute_position(GATE_MOTOR, PATH_A_ANGLE, SPEED)
        time.sleep_ms(DWELL_MS)

The `DWELL_MS` value is the primary tuning knob. Set it to match your module's inter-ball interval in milliseconds: at 1 BPS, 1000ms dwell routes one ball per lane per cycle; at 2 BPS, reduce dwell to 500ms. The `SPEED` value of 500 degrees/second completes the 65-degree gate sweep in approximately 130ms, well within the 100ms safety margin for 0.3 m/s approach velocities—and fast enough to avoid contact with the trailing ball even at 2 BPS.

### Sensor-Triggered Switching: Color Sensor as Ball Detector

When open-loop timing is insufficient—typically in modules that receive balls from an upstream neighbor whose throughput rate is variable or unpredictable—a SPIKE Prime color sensor mounted flush with the chute floor, facing upward through a 1×2 tile gap, can detect ball presence by reflected light intensity. A Lego ball passing 8–10mm above the sensor face produces a reflected light reading of 55–70% intensity (on the SPIKE Prime's 0–100 scale) against a 10–15% baseline reading from the tile. This 40-point differential is reliable across all standard Lego ball colors, though transparent or very dark balls produce a compressed differential of 20–25 points—still workable with a carefully placed white tile reflector immediately adjacent to the sensor.

The sensor trigger should fire the gate motor command with the minimum possible software latency. In SPIKE Prime MicroPython, `motor.run_to_absolute_position()` is a non-blocking call when given a callback or run in an async context, meaning the gate command can be issued within one interpreter tick (approximately 2–5ms) of the sensor threshold crossing. The remaining latency is mechanical: the motor must spin up and traverse the gate arc before the ball arrives. For this reason, the sensor must be positioned *upstream* of the gate by a distance equal to the product of ball velocity and total gate actuation time. At 0.3 m/s approach velocity and 130ms gate actuation, the sensor placement must be at minimum 39mm (approximately 5 studs) upstream of the gate paddle's leading edge. In practice, 6–7 studs of upstream sensor offset provides adequate margin while remaining within the same module frame.

---

## 3. High-Performance Optimization & Failure Modes

### Throughput Ceiling and the Separation Bottleneck

The theoretical maximum throughput of a parallel-path GBC module is determined not by the lift mechanism's speed but by the separation stage's cycle time. If the gate requires 130ms to actuate plus 100ms of minimum dwell to fully commit a ball to a lane, the minimum inter-ball interval is 230ms, capping throughput at approximately 4.3 balls per second across both lanes combined. This ceiling is generous compared to the 2 BPS practical maximum of most lift designs, meaning the separation stage is not typically the bottleneck. However, in high-performance builds using high-speed conveyor lifts or large-volume cup-wheel designs targeting 3+ BPS, the gate actuation speed becomes critical. Upgrading from a standard Large Angular Motor to the SPIKE Prime Medium Angular Motor reduces actuating mass and improves angular acceleration, cutting actuation time to approximately 80ms for the same 65-degree arc—raising the ceiling to approximately 6.25 BPS, well above any current GBC lift design's output.

### Trajectory Variance and Landing Zone Drift

Over extended operation (30 minutes to several hours at a GBC event), thermal expansion of the supporting structure causes dimensional drift. A Technic liftarm at 20°C is 15.9mm between pin centers for a 2-stud beam; at 35°C (a warm room with multiple motors running) this dimension grows by approximately 0.009mm—trivial for a single beam but non-trivial across a 500mm chute structure assembled from 30+ interconnected beams. The cumulative drift can shift the landing zone by 1–2mm, which is beneath the resolution of the stud grid but above the tolerance of a narrowly designed receiver funnel. The mitigation is to design receiver funnels with 4–5mm of lateral clearance beyond the nominal landing zone diameter, using curved or chamfered guide rails rather than hard vertical walls. A ball that lands 2mm off-center in a funnel with 5mm clearance rails recovers to center; the same ball hitting a hard wall at 2mm deflection rebounds unpredictably.

### Axle Twist and Gate Position Creep

A gate paddle driven through a long axle run (more than 4 studs of unsupported axle) will exhibit torsional wind-up under load, causing the paddle's physical angle to lag behind the motor's commanded angle by 3–8 degrees depending on axle diameter and load resistance. For 3L cross-axles (the smallest practical size) this torsional error reaches 8 degrees under a 25g ball contact force—enough to misalign the gate relative to the lane boundary and produce intermittent routing errors. The fix is to mount the gate paddle on the motor output shaft directly, using a 90-degree bevel gear pair if the motor orientation does not align with the paddle axis, rather than transmitting rotation across a long axle run. If a long axle run is unavoidable, use a 5L or 7L cross-axle with intermediate bushing support at every 3 studs of span, and increase the motor position targets by an empirically measured offset to compensate for steady-state wind-up.

### Ball Accumulation and Back-Pressure Failure

One of the most insidious failure modes in parallel-path systems is *back-pressure accumulation* on the lower-throughput lane. If Lane A is feeding a faster sub-module than Lane B, balls queue in Lane B's output chute. As the queue grows, the rearmost ball in Lane B's queue applies backward pressure against the separation gate's guiding surface at the moment the gate is committing a new ball to Lane B. This contact force is small—typically under 50g—but it occurs precisely when the gate is at its mechanically weakest point (mid-arc, with maximum moment arm), and it can stall a motor with insufficient torque margin. The Large Angular Motor's stall torque is approximately 25 N·cm; the torque required to push a queued ball backward through a 15-degree chute is approximately 2–4 N·cm, leaving an 80% torque margin that is normally more than adequate. The dangerous condition arises when three or more balls are queued in Lane B, multiplying the back-pressure to 6–12 N·cm and consuming nearly half the motor's torque reserve. The structural solution is to design Lane B's output chute with a ball accumulation buffer of no more than two ball diameters (64mm) between the gate exit and the downstream module's intake, forcing any back-pressure to be resolved by the downstream module slowing its intake rather than propagating pressure back to the gate.

### Jam Recovery and Self-Clearing Chute Design

No passive chute design is jam-proof under all ball approach conditions, so a practitioner building for public GBC events must engineer self-clearing behavior into every transit chute. The most effective technique is a *relief notch*: a 1×2 stud gap in the chute's floor at the natural jam point (typically the first 15–20% of chute length from the intake, where ball velocity is lowest), covered by a hinged 1×2 tile on a friction pin. Under normal operation, ball weight keeps the tile flush with the chute floor. When a ball stalls and a second ball accumulates behind it, the combined weight (20–24g) exceeds the friction pin's retention torque and the tile deflects downward by 5–10 degrees, dropping the stalled ball a half-plate height and re-establishing its momentum through gravity. This mechanism resets itself within 200ms of clearing, is entirely passive, and adds fewer than five parts to the assembly.

Sensor-triggered jam detection, available to builders using a SPIKE Prime hub, provides a complementary active recovery layer. A color sensor positioned at the mid-chute relief notch that reads ball presence for more than 500ms without a downstream sensor confirming ball exit triggers a brief motor speed reduction followed by a sharp speed pulse—the mechanical equivalent of a tap to dislodge a stacked pair. This two-sensor jam detection pattern is implemented in SPIKE MicroPython by logging timestamps on each sensor trigger event and computing the dwell duration in the main loop, then issuing the motor pulse command if dwell exceeds the threshold. The speed pulse magnitude should be tuned to no more than 20% above normal operating speed for 150ms; a larger pulse risks launching the dislodged ball faster than the downstream gate can accommodate, trading a chute jam for a separation miss.

### Calibrating the Full Chain: A Field Validation Protocol

Having built a parallel-path module with all the above mechanics in place, the final discipline is systematic chain validation under realistic conditions. Run the module in isolation first, feeding balls manually from a small hopper at 1 BPS, and photograph the landing zone on each receiving surface from directly above using consistent lighting. A distribution of landing marks (use chalk-tipped balls for the test, or place a thin paper template on the receiver surface) that clusters within a 10mm diameter circle confirms that chute trajectory variance is within tolerance. Any elongated distribution along the chute axis indicates variable exit speed, requiring chute angle or surface friction adjustment; any lateral scatter indicates exit-angle instability from studded walls or misaligned chute-to-receiver transitions.

Then integrate the module into the chain and observe the first 100-ball cycle. Count routing errors (balls going to the wrong lane) and stalls separately—these have different root causes and different fixes. Routing errors above 2% indicate gate timing or geometry issues; stalls above 1% indicate intake or chute design issues. Both thresholds are achievable in a well-engineered module, and reaching them before bringing a GBC chain to a public event is the difference between a module that runs all day and one that requires constant intervention. The ball path, in the end, is a continuous physical argument—and every component in the chain must be making the same point.
