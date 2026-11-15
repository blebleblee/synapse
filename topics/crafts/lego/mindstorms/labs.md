# Operational Verification Labs: Mindstorms

## Objective & Operational Lab Setup

The objective of this lab manual is to transition the practitioner from theoretical robotics to empirical operational verification using the LEGO Mindstorms hardware platform. We will utilize the SPIKE Prime hub and motor ecosystem, programmed via the Pybricks MicroPython environment, to establish a rigorous, data-driven testing framework. The focus is on characterizing mechanical performance, tuning control algorithms, and diagnosing failure modes through quantitative analysis. The lab treats the LEGO system not as a toy, but as a modular mechatronic platform subject to the same physical laws and control theory constraints as industrial machinery.

Before commencing, establish the analytical environment. You will need a flat, level testing surface of at least two meters in length, a precision tape measure marked in millimeters, a digital protractor or angle gauge, and a spreadsheet application (e.g., Excel, Google Sheets) configured to import CSV data. The physical rig for these exercises is a standard two-wheeled differential drive chassis. Construct the chassis frame using two 15-module Technic beams as longitudinal rails, separated by cross-beams at the extreme front and rear. To prevent the torque reaction from the drive motors from skewing the frame into a parallelogram, incorporate a diagonal brace using 5-12-13 Pythagorean triangle geometry. This triangulation locks the frame geometrically, transferring shear loads into tension and compression along the beams rather than bending the pin connections.

Mount the SPIKE Prime Large Motors directly into the frame using the motor's integrated pin holes. Avoid cantilevering the wheels off the motor shafts alone; support the outboard side of the wheel axle with a bushing secured to a Technic beam. This dual-supported configuration eliminates the radial runout that introduces sinusoidal odometry errors in single-supported drives. The standard SPIKE wheel has a nominal diameter of 56mm, but manufacturing tolerances and tire compression mean the effective rolling diameter must be verified empirically. Ensure the Pybricks firmware is flashed to the hub and connect via USB or Bluetooth for code deployment.

## Exercise 1: Foundational Practical Implementation

This exercise establishes a baseline of mechanical reliability by verifying the odometric accuracy of the drive system. We will execute a linear displacement routine and compare the commanded distance against the physically measured distance. The theory rests on the conversion of motor encoder degrees to linear millimeters via the wheel radius. Any discrepancy between the calculated and actual distance reveals mechanical slip, tire deformation, or frame misalignment that must be corrected before higher-level autonomous routines can be trusted.

Practically, begin by downloading the following Pybricks script to the hub. This code commands the chassis to drive forward exactly 500 millimeters at a moderate speed of 200 mm/s, stop, and hold position. The routine uses the `run_target` method, which engages the motor's internal PID controller to reach the specified encoder angle. We set `wait=False` on the first motor so both motors start simultaneously, preventing rotational drift caused by staggered start times.

```python
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait

hub = PrimeHub()
left_motor = Motor(Port.E, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.A, Direction.CLOCKWISE)

# Nominal wheel diameter in millimeters
WHEEL_DIAMETER = 56.0

def drive_straight(distance_mm, speed_mm_s):
    # Convert linear speed to angular speed (deg/s)
    speed_deg_s = (speed_mm_s / (WHEEL_DIAMETER * 3.14159)) * 360.0
    
    # Calculate target rotations in degrees
    target_angle = (distance_mm / (WHEEL_DIAMETER * 3.14159)) * 360.0
    
    # Reset encoders to establish a zero state
    left_motor.reset_angle(0)
    right_motor.reset_angle(0)
    
    # Start motors simultaneously
    left_motor.run_target(speed_deg_s, target_angle, wait=False)
    right_motor.run_target(speed_deg_s, target_angle, wait=True)
    
    # Brief pause to allow settling
    wait(100)

# Execute 500mm drive
drive_straight(500, 200)
```

Place the robot at the zero mark on your tape measure. Execute the script. Once the robot stops, measure the actual distance traveled from the center of the wheel axis to the stopping point. Record this value in the empirical audit table below. If the robot deviates more than 5mm from the 500mm target, adjust the `WHEEL_DIAMETER` variable in the code. A smaller value increases the computed encoder counts per millimeter, causing the robot to travel further; a larger value does the opposite. Iterate this process until the physical error is less than 2mm.

**Odometry Calibration Audit Rubric**

| Trial | Commanded (mm) | Measured (mm) | Error (mm) | Adjusted `WHEEL_DIAMETER` |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 500 | | | 56.0 (Nominal) |
| 2 | 500 | | | (Calculated) |
| 3 | 1000 | | | (Verified) |

## Exercise 2: Parameter Variation & Empirical Analysis

Having established a reliable linear drive, we now introduce a steering mechanism via a proportional-integral-derivative (PID) control loop for line following. This exercise varies the proportional gain ($K_p$) to analyze the system's oscillatory response and settling characteristics. The theory here relies on the PID controller's ability to minimize the error between the Color Sensor's reflection value and a target threshold representing the edge of a black line. The proportional term generates a steering correction proportional to the error. If $K_p$ is too low, the robot fails to track the curve; if $K_p$ is too high, the system overshoots and oscillates.

Construct a line-following track using black electrical tape on a white surface. Configure the robot with a SPIKE Prime Color Sensor mounted 10-12mm above the surface, angled at 45 degrees toward the line. This SNOT (Studs Not On Top) configuration utilizes a 2x2 bracket to establish a stable viewing angle that maximizes contrast and rejects ambient light interference. Download the parameterized line-following script below.

```python
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait

hub = PrimeHub()
left_motor = Motor(Port.E, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.A, Direction.CLOCKWISE)
color_sensor = ColorSensor(Port.C)

def line_follow(kp, base_speed, duration_ms):
    # Target reflection value for the edge of the line
    target = 50 
    start_time = wait(0) # Get current time
    
    while wait(0) - start_time < duration_ms:
        error = color_sensor.reflection() - target
        correction = int(error * kp)
        
        left_motor.run(base_speed - correction)
        right_motor.run(base_speed + correction)
        wait(10)
        
    left_motor.brake()
    right_motor.brake()

# Execute line following with varying Kp values
# We will test Kp = 0.5, 1.0, and 1.5
line_follow(kp=0.5, base_speed=150, duration_ms=5000)
```

Execute the routine across three distinct $K_p$ values: 0.5, 1.0, and 1.5. Observe the robot's behavior on a straight section of the line and a 90-degree curve. Record the empirical data in the spreadsheet. Measure the maximum lateral deviation from the line center and count the number of visible oscillations (wobbles) per second. A well-tuned system will track the curve with minimal deviation and zero sustained oscillation on the straightaway. The integral and derivative terms are omitted here to isolate the effect of the proportional gain, but in a full implementation, $K_i$ would be added to eliminate steady-state error and $K_d$ to dampen the oscillation you are observing here.

**PID Variation Audit Rubric**

| $K_p$ Value | Base Speed (deg/s) | Max Deviation (mm) | Oscillation Frequency (Hz) | Track Completion (Y/N) |
| :--- | :--- | :--- | :--- | :--- |
| 0.5 | 150 | | | |
| 1.0 | 150 | | | |
| 1.5 | 150 | | | |

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The final exercise pushes the mechanical and electrical systems to their failure thresholds to test the robustness of a diagnostic recovery protocol. We will construct an incline ramp to stress the drivetrain against gravitational resistance. As the angle of the incline increases, the required torque from the motors increases proportionally to the sine of the angle. When the required torque exceeds the motor's stall limit, or when the tractive force exceeds the static friction between the tires and the ramp, the robot will slip or stall. This creates a spike in electrical current draw, which we can monitor in real-time to trigger a recovery routine.

Build a ramp with a smooth surface, hinged at one end so the angle can be adjusted. Use a digital protractor to verify the angle. The coefficient of static friction ($\mu_s$) between standard SPIKE Prime rubber tires and a smooth ABS surface typically falls between 0.4 and 0.6, predicting a slip angle between 22 and 31 degrees. We will verify this empirically. The script below commands the robot to drive forward at full power while monitoring the motor current. If the current spikes above 600mA and the motor speed drops near zero, indicating a stall, the robot will execute a backup and turn sequence to attempt a different path.

```python
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait

hub = PrimeHub()
left_motor = Motor(Port.E, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.A, Direction.CLOCKWISE)

def climb_or_recover():
    base_speed = 900 # Max speed in deg/s
    stall_current_ma = 600 # Threshold for stall detection
    stall_speed_deg_s = 50 # Speed threshold to confirm stall
    
    while True:
        left_motor.run(base_speed)
        right_motor.run(base_speed)
        wait(50)
        
        # Read motor diagnostics
        left_current = left_motor.current()
        right_current = right_motor.current()
        left_speed = left_motor.speed()
        right_speed = right_motor.speed()
        
        # Evaluate stall condition
        if left_current > stall_current_ma or right_current > stall_current_ma:
            if left_speed < stall_speed_deg_s and right_speed < stall_speed_deg_s:
                print("Stall detected! Current: ", left_current, "mA")
                
                # Recovery protocol: back up and turn
                left_motor.run(-base_speed/2)
                right_motor.run(-base_speed/2)
                wait(500)
                
                left_motor.run(-base_speed/2)
                right_motor.run(base_speed/2)
                wait(300)
                
                # Resume climb
                left_motor.brake()
                right_motor.brake()
                wait(100)

# Execute the test
climb_or_recover()
```

Place the robot at the base of the ramp set to a 15-degree incline. Execute the script. The robot should climb successfully. Increase the angle in 5-degree increments. At a certain threshold, the robot will either lose traction and spin its wheels, or stall completely. If the wheels spin without forward progress, the friction limit has been reached. If the robot stops and the recovery protocol triggers, the torque limit has been reached. Record the critical failure angle and the behavior mode in the diagnostic table.

**Stress Test Audit Rubric**

| Ramp Angle (deg) | Motor Current (mA) | Speed (deg/s) | Behavior (Climb/Slip/Stall) | Recovery Triggered? |
| :--- | :--- | :--- | :--- | :--- |
| 15 | | | | |
| 20 | | | | |
| 25 | | | | |
| 30 | | | | |

## Operational Reference Guide & Diagnostic Checklist

When diagnosing anomalous behavior in the Mindstorms system, proceed through the following checks systematically. Do not adjust software parameters until mechanical integrity is confirmed.

**1. Mechanical Frame Verification:** Inspect all pin connections for play. A frame that is loose will skew the wheelbase, causing the robot to pull to one side during straight-line travel. Use cross-bracing to eliminate any parallelogram deformation. Verify that the axles are supported on both sides; a cantilevered axle will introduce runout that manifests as inconsistent odometry readings.

**2. Sensor Calibration:** The Color Sensor's reflection values are highly dependent on ambient light. Before any line-following exercise, place the sensor over the white surface and record the value, then over the black line and record the value. The target threshold in your PID loop should be the average of these two values. If the environment changes, this calibration must be repeated.

**3. Motor Encoder Integrity:** If the robot turns inconsistently despite correct code, reset the motor encoders manually via the hub interface. Ensure the `reset_angle(0)` command is called at the start of every routine to establish a known zero state. If a motor reports inconsistent speed readings under load, inspect the internal gearing for dirt or wear.

**4. Power Supply Stability:** The SPIKE Prime hub relies on a rechargeable battery. As the battery discharges, the maximum available torque decreases. If the stall current threshold in Exercise 3 is not being reached, check the battery level indicator on the hub display. A low battery will cause the PID controllers to behave sluggishly, mimicking a poorly tuned system.
