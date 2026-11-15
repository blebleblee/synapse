# Lesson 4: Motors, Sensors, Control Logic

## 1. First-Principles Intuition & Invariants

There is a moment every serious Technic builder encounters, usually mid-project, when static mechanics are no longer enough. The gear train is elegant, the frame is triangulated, the linkages move with satisfying precision — but the model sits inert, waiting for a hand to push it. The step from passive mechanism to autonomous machine requires more than adding a motor and calling the job done. It demands a fundamental shift in how you think about the system: from a chain of static forces to a closed loop of information, power, and response.

Lego's Powered Up platform is the native language of that shift. It replaced the older Power Functions ecosystem gradually from 2018 onward, moving from a purely electrical distribution model (a battery box driving a motor, full stop) toward a networked architecture where hubs, motors, and sensors are nodes in a communicating graph. Understanding why this architecture exists, not merely how to wire it, is what separates a practitioner who bolts on a motor from one who designs a genuinely responsive machine.

The fundamental invariant of any motorized Technic system is the relationship between torque, speed, and load. A brushless DC motor — the technology inside every LEGO Powered Up motor — produces maximum torque at zero RPM and maximum speed at zero load. Between these extremes lies the torque-speed curve: a nearly linear descent from stall torque to no-load speed. Every decision you make about gear reduction, motor selection, and power delivery is an attempt to position your operating point on that curve in the most favorable region for the task. A mechanism that must lift a heavy load needs to operate near the high-torque, low-speed end; a mechanism that must sweep quickly through air needs to work near the high-speed, low-torque end. The gearing you place between motor and output shaft shifts the entire operating point up or down the load axis. This is not an abstract principle — it manifests physically as a motor that runs warm and bogs under load (geared too fast), or one that spins freely while a clutch gear clicks endlessly (geared too slowly, stalling the motor against the slip clutch).

The second invariant is that sensors without feedback logic are merely expensive indicators. A color sensor that tells you a brick is red is useless unless the program responds differently to red than to blue. A rotation sensor that counts degrees is useless unless the program uses that count to stop, reverse, or adjust motor speed. The entire value of the Powered Up sensor suite lives in the conditional logic that acts on sensor data. This is why control theory — even at the simplified level appropriate to Lego systems — matters. The difference between a robot arm that slams into its hard stop at full speed and one that decelerates smoothly into a known position is entirely a function of how the program interprets encoder feedback and adjusts motor power in real time.

The third invariant, specific to the Powered Up platform, is that communication latency exists and must be designed around. When you run a program on a Smart Hub and issue a motor command, that command travels through an internal message queue, is processed by the hub firmware, and is applied to the motor driver. When a sensor value changes, it propagates back through the same chain before your program sees it. At the timescales of human interaction this latency is invisible. At the timescales of a fast-moving mechanism trying to stop within two degrees of arc, it is not. Advanced practitioners account for latency by placing feedback-critical logic as close to the hardware as possible — running control programs on the hub itself rather than through a Bluetooth-connected tablet — and by designing mechanisms with enough mechanical compliance (a Technic spring, a rubber band tensioner, or even deliberate gear backlash) to absorb the small positional errors that communication lag inevitably introduces.

---

## 2. Core Architecture & Mechanics

### The Powered Up Hardware Ecosystem

Lego's Powered Up hardware organizes itself into three functional tiers: hubs, active devices, and passive wiring. Understanding what happens at each tier is essential before writing a single line of control code.

The hub is the brain. The two hubs relevant to serious Technic work are the **Technic Hub** (88012) and the **Smart Hub** (also called the Move Hub, found in BOOST sets). The Technic Hub carries four powered ports, an internal accelerometer and gyroscope, Bluetooth Low Energy connectivity, and enough processing headroom to run programs downloaded from the LEGO MINDSTORMS or Pybricks environments. It has no internal motors and no display — it is purely infrastructure, designed to disappear inside a model. The Smart Hub packs a small internal motor and a tilt sensor into a compact form factor better suited to smaller builds. For serious Technic work, the Technic Hub is the correct choice almost universally, because four independently controlled ports give you the flexibility to drive two motors and read two sensors simultaneously, all from a single hub that can be buried inside a chassis.

Active devices — motors and sensors — connect via the LPF2 (Low Power Functions 2) connector, a six-pin Dupont-style plug that carries power, ground, and a bidirectional serial data line. This is architecturally important: every motor in the Powered Up lineup that includes an encoder is not just an actuator but also a sensor. The motor reports its own rotational position back to the hub continuously. This built-in feedback channel is what makes closed-loop position control possible without any additional hardware.

The motor lineup spans a carefully differentiated performance envelope:

The **Small Angular Motor** (45603) is the precision instrument. Its integrated encoder resolves to approximately one degree of accuracy, and its physical form factor (designed for MINDSTORMS Robot Inventor) makes it easy to integrate into compact gearboxes. Stall torque is modest — roughly 0.08 N·m — which means it needs gearing to do serious mechanical work but rewards you with quiet, controllable motion at low loads.

The **Medium Angular Motor** (45603 / 88008) steps up both torque (approximately 0.17 N·m at stall) and physical bulk. It is the workhorse of mid-scale Technic builds: steering racks, turntable drives, robotic joint actuators. Its encoder has the same degree-level resolution as the Small Angular Motor, so position control quality is equivalent; the difference is purely in force output and package size.

The **Large Angular Motor** (88013) is the heavy mover. At roughly 0.6 N·m stall torque, it can drive large wheel assemblies, heavy lifting booms, and other mechanisms that would stall the smaller motors even with favorable gearing. The tradeoff is current draw: at full load a Large Angular Motor pulls close to 800 mA, which matters when you're running multiple devices from a single hub whose total port current budget is limited by the AAA or rechargeable battery pack supplying it.

The **XL Motor** (88014) sacrifices encoder precision for maximum torque (approximately 1.2 N·m stall torque), making it appropriate for high-force, low-precision tasks: driving a heavy wheeled vehicle, spinning a belt conveyor, powering a winch. Without degree-level encoder feedback, closed-loop position control is not possible with the XL Motor alone; for position tasks, pair it with a separate rotation sensor or rely on hard mechanical stops.

Sensor options are more limited than in the MINDSTORMS ecosystem but sufficient for sophisticated Technic work. The **Color Sensor** (45605) detects eight discrete colors plus ambient light intensity and reflected light intensity, making it useful for line following, object detection, and state-machine triggers (a conveyor that stops when it detects a red tile has arrived at a station). The **Distance Sensor** (45604) uses infrared time-of-flight measurement to report range from roughly 5 cm to 200 cm, enabling proximity braking, obstacle avoidance, and position homing. The **Force Sensor** (45606), introduced with MINDSTORMS Robot Inventor, measures applied force and binary contact state — an elegant solution for gripper control that needs to know when fingers have closed on an object without crushing it.

```
Technic Hub (88012)
│
├── Port A ──► Large Angular Motor  [torque output + encoder feedback]
├── Port B ──► Medium Angular Motor [torque output + encoder feedback]
├── Port C ──► Color Sensor         [color / light intensity input]
├── Port D ──► Distance Sensor      [range input]
│
├── Internal IMU ──► Accelerometer (X/Y/Z) + Gyroscope (X/Y/Z)
│
└── BLE ──► Pybricks / LEGO App / Remote Control handset
```

The hub's internal IMU deserves more attention than it typically receives. The gyroscope measures angular velocity in degrees per second on three axes; the accelerometer measures linear acceleration including gravity. For a wheeled vehicle, the gyroscope yaw axis gives you a continuous heading estimate — not GPS-accurate, but sufficient to execute straight-line drives that self-correct for differential motor speed variation, or turns that stop at a specified angle. For a crane or boom, the accelerometer pitch axis gives you direct measurement of arm elevation without needing a separate angle sensor. These internal sensors require no port wiring and consume no port budget, making them effectively free instrumentation.

### The Control Software Stack

Lego provides two official programming environments for Powered Up hardware: the **LEGO App** (a block-based visual environment) and the **MINDSTORMS Robot Inventor App** (which adds a Python-ish text layer called MINDSTORMS Python). Both are functional entry points, but serious practitioners migrate to **Pybricks**, an open-source MicroPython firmware that replaces the stock hub firmware and gives you direct, low-latency Python control over all hardware with a clean, well-documented API.

Pybricks is the professional toolchain for Powered Up Technic work, and this lesson treats it as the native environment. Flashing a Technic Hub with Pybricks takes under two minutes via the Pybricks online IDE (code.pybricks.com), requires no special hardware, and is fully reversible by reflashing the original LEGO firmware. After flashing, you write programs in standard MicroPython, download them via Bluetooth, and run them standalone — the hub needs no ongoing Bluetooth connection to a host device during execution, eliminating the latency that plagues phone-dependent control.

The Pybricks API surfaces motor control at three abstraction levels. At the lowest level, `motor.dc(duty_cycle)` applies a raw PWM duty cycle from -100% to +100%, giving no encoder feedback involvement whatsoever — open-loop control. At the middle level, `motor.run(speed)` uses encoder feedback to maintain a target speed in degrees per second, absorbing load variation by automatically adjusting duty cycle. At the highest level, `motor.run_angle(speed, angle)` or `motor.run_target(speed, target_angle)` executes a complete profiled move — accelerating to speed, running, then decelerating to stop precisely at the target angle, using a PID controller running inside the hub firmware.

These three levels correspond to three control philosophies, each appropriate for different mechanical situations. Open-loop dc control is correct when you need maximum responsiveness, don't care about precise position, and trust the mechanism to constrain motion (a wheeled drive base hitting a bump, a conveyor running indefinitely). Speed control is correct for continuous motion mechanisms where consistent velocity matters more than position: a belt conveyor that must feed parts at a steady rate, a turntable that must rotate smoothly for video capture. Position control is correct for any mechanism with a defined endpoint: a robot arm joint, a steering rack, a linear actuator.

### Feedback Loops and PID Intuition

The PID controller embedded in Pybricks's motor control is worth understanding structurally, because its three parameters — proportional gain (Kp), integral gain (Ki), and derivative gain (Kd) — directly affect physical behavior you will observe on the bench.

The proportional term is the simplest: the motor correction effort is proportional to the current position error. A large Kp creates a motor that responds aggressively to any deviation from target — fast and stiff, but prone to oscillation if the gain is high enough that the correction overshoots and triggers an equal correction in the opposite direction. A small Kp creates a sluggish motor that approaches its target slowly and may never quite reach it because the correction force becomes smaller than friction before the error reaches zero.

The integral term accumulates error over time. If a small constant friction load is pushing the motor away from its target, proportional correction alone will find an equilibrium where motor force exactly balances friction — but that equilibrium is not the target position, it is a steady-state error. The integral term detects that error has persisted over time and adds a growing correction force until the steady-state error is eliminated. In Technic mechanisms with significant friction (heavy gear trains, tight-fitting linear guides, rubber-tired wheels on carpet), integral gain is what prevents the motor from resting short of target.

The derivative term acts on the rate of change of error. When the motor is approaching its target rapidly, the error is decreasing fast, and the derivative term applies a braking force proportional to that rate of decrease. This is what prevents the aggressive overshoot that high proportional gain alone would cause. In practice, derivative gain is the most sensitive to mechanical noise: if your mechanism has vibration, backlash, or encoder resolution limits that create noisy error signals, excessive Kd causes the controller to react to noise rather than real position change, producing jittery motion.

Pybricks exposes PID gains via the `motor.control.limits()` and `motor.control.pid()` methods, allowing you to tune them directly in Python rather than accepting the firmware defaults. The defaults are conservative and work well for most mechanisms; you will typically need to adjust them when driving mechanisms with unusual friction profiles or when precision requirements are tighter than the defaults achieve.

```
Desired Position ──►[+]──► PID Controller ──► Motor PWM ──► Motor
                     ↑                                          │
                     │                                          ▼
                     └──────────────────────── Encoder Feedback
```

The feedback path is what transforms an open-loop actuator into a closed-loop servo. Without the encoder return path, the motor is simply a power consumer. With it, the motor is a positioning system whose accuracy is bounded by encoder resolution, control loop frequency, and mechanical compliance — all of which you can characterize and design around.

---

## 3. High-Performance Optimization & Failure Modes

### Gear Ratio Selection for Motor Operating Point

The single most consequential mechanical decision in a motorized Technic build is gear ratio, and it is worth quantifying rather than estimating. The Large Angular Motor's no-load speed is approximately 175 RPM at the output shaft. If your mechanism requires 20 RPM at the final output (a slow-turning turntable, for example), a nominal 8.75:1 total reduction places the motor operating speed near 175 RPM, which is at the unloaded extreme. Add load, and the motor will bog to perhaps 140 RPM — still well within the useful range. If instead you needed 10 RPM and used a 17.5:1 reduction, the motor would run at a faster proportion of its no-load speed for any given output load, consuming less current and running cooler. The principle is that more reduction generally means a healthier motor operating point, up to the limit where the gearing becomes impractically large or introduces unacceptable backlash.

Standard Lego spur gears (the most common bevel gear combination being 20T and 12T bevel pairs giving 1.67:1) allow you to build gear trains with precise ratios. The workhorse compound reduction pairs are 8T-to-24T (3:1 per stage), 12T-to-36T (3:1 per stage), and 16T-to-48T (3:1 per stage). Stacking two 3:1 stages gives 9:1; three stages give 27:1 — more than enough reduction for any Technic application. The practical constraint on deep gear trains is accumulated backlash: each mesh adds a small amount of play, and four compound stages can produce enough total backlash to make degree-level position control unreliable. The mitigation is to use Pybricks's `motor.run_target()` with the `then=Stop.HOLD` parameter, which keeps the PID controller active after the move completes and continuously corrects for any backlash-induced drift.

Worm gears deserve special mention for two reasons: their reduction ratio per stage is enormous (the standard Lego worm meshed with a 24T gear gives 24:1), and they are inherently self-locking — the worm can drive the gear but the gear cannot back-drive the worm. This self-locking property is mechanically valuable for any mechanism that must hold position under gravity load without requiring the motor to maintain active torque. A crane boom held by a worm gear stays put when the motor is unpowered. The tradeoff is efficiency: worm gears have significantly higher friction than spur gears, running at roughly 50-70% efficiency versus 95%+ for spur gears. This means the motor must do substantially more work to drive a given load through a worm stage, so current draw increases even if the mechanical output is the same.

### Sensor Integration Patterns

The most reliable sensor integration pattern for precision Technic work is the **homing sequence**: on startup, the program drives the mechanism toward a known hard stop at low speed (20-30% duty cycle to avoid violent impact), waits for the motor encoder velocity to drop to zero (indicating contact with the stop), resets the motor encoder to zero at that position, and then all subsequent moves are executed as absolute target angles from that known reference. This pattern eliminates cumulative positioning error from power cycles, slip, or manual manipulation of the mechanism between runs.

In Pybricks, the homing sequence looks like this in structure:

    from pybricks.hubs import TechnicHub
    from pybricks.pupdevices import Motor
    from pybricks.parameters import Port, Direction, Stop
    from pybricks.tools import wait

    hub = TechnicHub()
    arm = Motor(Port.A, Direction.CLOCKWISE)

    # Homing: drive toward hard stop at low speed
    arm.run(-200)                      # 200 deg/s toward zero stop
    wait(2000)                         # allow time to reach stop
    arm.stop()
    arm.reset_angle(0)                 # declare this position as zero

    # Now execute absolute moves from home
    arm.run_target(300, 90, then=Stop.HOLD)   # move to 90 degrees
    arm.run_target(300, 0, then=Stop.HOLD)    # return to home

The homing sequence is not optional for mechanisms where position matters. Without it, any position you command is relative to wherever the motor happened to be when the program started — a fundamentally unreliable reference.

The Distance Sensor enables a more sophisticated pattern: **proximity-based deceleration**. Rather than commanding a fixed move and hoping the mechanism arrives at target without obstruction, you combine a distance sensor facing the direction of travel with a software ramp that reduces motor speed as the measured distance decreases. This is mechanically equivalent to what a human driver does when approaching a wall — the closer the wall, the lighter the throttle. In Pybricks, this is implemented with a simple control loop:

    target_distance = 60   # mm from obstacle to stop
    while True:
        dist = eyes.distance()          # Distance Sensor reading in mm
        error = dist - target_distance
        if error <= 0:
            drive.stop()
            break
        speed = max(50, min(500, error * 3))   # proportional speed ramp
        drive.run(speed)

The `error * 3` term is a manual proportional gain, and the `max(50, ...)` floor prevents the motor from stalling at extremely small errors. This is a hand-coded P-controller for a specific task, written outside the Pybricks motor control API — entirely appropriate when you need custom behavior that the built-in position controller does not cover.

Color sensor state machines are the third major integration pattern. A mechanism with multiple discrete operating states — a sorting conveyor, a pick-and-place arm — can use color tiles on the mechanism itself as physical state flags. Placing a red tile at the "eject" position and a green tile at the "load" position means the control program does not need to track abstract encoder counts; it reads physical reality directly. The state machine logic separates cleanly from the motion logic: one task reads the sensor and maintains a `current_state` variable, another task executes motor commands appropriate to `current_state`. In Pybricks's multitasking model (using `run_task()` with async/await coroutines), these two tasks run concurrently without blocking each other.

### Failure Modes and Mitigations

The most common failure mode in Powered Up Technic systems is **motor stall under unexpected load**. The motor firmware detects stall by monitoring the ratio between applied PWM and resulting encoder velocity — if the motor is commanded at high power but the encoder shows no movement, the firmware interprets this as a stall and cuts power to protect the motor windings from thermal damage. This protection is good, but it manifests in your program as an exception (`MotorStalled`) that terminates the current move. The correct response in a production program is to catch the exception, back off the mechanism, attempt a re-home sequence, and retry rather than crashing the program. Mechanical causes of unexpected stall include debris caught in a gear train, a mechanism that has flexed under load until two parts contact, a gear mesh that has shifted to an interference condition, and a battery pack that has sagged in voltage sufficiently to reduce available torque below the load requirement.

**Bluetooth latency and disconnection** are failure modes specific to programs that run on a host device (phone or tablet) and communicate with the hub in real time rather than running standalone on the hub. The latency for a round-trip command-and-response over Bluetooth LE is typically 20-80 ms under good conditions, but can spike to several hundred milliseconds in environments with RF congestion. This renders real-time closed-loop control from a host device unreliable for fast mechanisms. The mitigation, as noted in the first section, is to run the control program on the hub itself via Pybricks's standalone execution model. The host device is used only for download and start/stop commands; all sensor reading and motor commanding happens inside the hub with no Bluetooth round-trip in the control path.

**Encoder drift in long-running mechanisms** occurs when a mechanism is driven for extended periods at high load with significant vibration. At very high vibration amplitudes, the optical encoder inside the motor can produce spurious pulses that accumulate into a small but growing position error. The mitigation for applications where this matters is periodic re-homing: program the system to execute a brief homing sequence after every N completed work cycles, restoring the absolute position reference before error can accumulate to a problematic magnitude.

**Battery voltage sag** is the most insidious failure mode because it degrades performance gradually rather than producing an immediate error. As the AAA batteries in a standard Powered Up battery box discharge, the available voltage drops from approximately 6V to below 4.5V. Since motor speed at a given PWM duty cycle is proportional to supply voltage, a motor running at 70% duty cycle with fresh batteries runs meaningfully faster than the same motor at 70% duty cycle with half-discharged batteries. Speed-controlled modes (`motor.run()`) compensate for this automatically through their feedback loops — the same 300 deg/s target will be maintained regardless of battery state, at the cost of increasing duty cycle to compensate. Open-loop `motor.dc()` control does not compensate; the motor simply slows down as voltage sags. For timing-sensitive applications, speed-controlled mode is therefore always preferable to open-loop control. The rechargeable battery pack (88013, intended for the Technic Hub) maintains a flatter discharge curve than AAA alkalines and is strongly recommended for any build that must perform consistently across a full session.

### Hub IMU for Orientation Control

The Technic Hub's internal gyroscope unlocks a class of control logic that requires no additional sensors: **heading-locked straight-line driving**. A wheeled vehicle driven by two independent motors will almost always drift due to small differences in motor characteristics, wheel diameter variation, and surface friction asymmetry. Without correction, a nominal straight-line drive accumulates heading error at a rate that becomes visible within a few hundred millimeters of travel.

The gyroscope heading correction loop runs as a concurrent task alongside the main drive task. It reads the hub's yaw angular velocity, integrates it into a cumulative heading estimate, and feeds the heading error into a proportional correction that trims the left and right motor speeds differentially. If the robot is turning right unintentionally, the heading estimate drifts positive, the correction term increases left motor speed and decreases right motor speed, and the trajectory bends back to straight. The tuning parameter is the heading correction proportional gain — high enough to cancel drift promptly, low enough that it does not create a weaving path by overcorrecting.

    hub = TechnicHub()
    hub.imu.reset_heading(0)

    async def drive_straight(distance_deg, nominal_speed):
        target = nominal_speed
        while motor_left.angle() < distance_deg:
            heading_error = hub.imu.heading()
            correction = heading_error * 1.2          # Kp = 1.2 deg/s per degree
            motor_left.run(target + correction)
            motor_right.run(target - correction)
            await wait(10)
        motor_left.stop()
        motor_right.stop()

This pattern — IMU feedback driving differential speed correction — is structurally identical to the outer loop of a full robot navigation controller. At Technic scale it is sufficient to produce straight-line drives accurate to within a few millimeters over a meter of travel on a flat surface, with no external sensors required.

Taken together, the patterns in this lesson — homing sequences, proportional deceleration, state-machine sensor logic, gyroscope heading correction, and PID gain awareness — constitute the core practitioner vocabulary for motorized Technic. Each pattern addresses a specific class of physical problem: uncertainty in starting position, uncertainty in final position, complexity of multi-state behavior, environmental disturbance, and hardware variability. Mastery of motorized Technic is not mastery of a programming language; it is mastery of the physical world the program must negotiate, using the language as the medium through which that negotiation happens.
