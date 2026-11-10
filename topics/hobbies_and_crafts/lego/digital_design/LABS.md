# Hands-On Operational Lab: Digital Design
## Objective & Lab Prerequisites

### Objective
This lab will guide you through the process of designing, building, and deploying a digital model using LEGO Mindstorms. You will learn how to use the LEGO Mindstorms software to create a simple robot, deploy it, and troubleshoot common issues.

### Prerequisites
- LEGO Mindstorms EV3 kit
- LEGO Mindstorms EV3 software installed on your computer
- Basic understanding of programming concepts
- Basic understanding of LEGO building techniques

## Exercise 1: Exploration, Diagnostics & System State Inspection

### Step 1: Install LEGO Mindstorms EV3 Software
Ensure that the LEGO Mindstorms EV3 software is installed on your computer. If not, download it from the official LEGO website.

### Step 2: Connect the LEGO Mindstorms EV3 Brick
1. Connect the EV3 brick to your computer using a USB cable.
2. Open the LEGO Mindstorms EV3 software.
3. Click on the "Connect" button to establish a connection with the EV3 brick.

**Expected Output:**
- The software should display a connection status indicating that the EV3 brick is connected.

### Step 3: Explore the Software Interface
- Familiarize yourself with the software interface, including the programming blocks and the model view.
- Use the "Model" tab to view and manipulate the physical model of your robot.

### Step 4: System State Inspection
- Use the "View" menu to enable the "Sensors" and "Motors" panels.
- Observe the sensor and motor readings while moving the robot's parts manually.

**State Inspection Steps:**
- Ensure that the sensor readings change as you move the robot's parts.
- Verify that the motor readings reflect the motor's actions.

## Exercise 2: Building, Configuring & Deploying a Production Scenario

### Step 1: Build the Robot
1. Follow the instructions in the LEGO Mindstorms EV3 software to build a simple robot.
2. Use the provided parts list and assembly guide to ensure accuracy.

**Parts List:**
- 1x Large Motor
- 1x Medium Motor
- 2x Touch Sensors
- 1x Color Sensor
- 1x Ultrasonic Sensor
- Various LEGO bricks and connectors

### Step 2: Configure the Robot
1. Open the "Model" tab and configure the sensors and motors.
2. Assign ports to the sensors and motors based on their physical connections.

**Expected Output:**
- The software should display the correct sensor and motor configurations.

### Step 3: Program the Robot
1. Use the programming blocks to create a simple program for your robot.
2. For example, create a program that makes the robot move forward until it detects an obstacle using the ultrasonic sensor.

**Sample Code:**
```plaintext
BEGIN
    WHILE TRUE
        IF UltrasonicSensor < 10 THEN
            STOP
        ELSE
            LargeMotor FORWARD
        ENDIF
    ENDWHILE
END
```

### Step 4: Deploy the Program
1. Click on the "Download and Run" button to deploy the program to the EV3 brick.
2. Observe the robot's behavior and ensure it follows the programmed instructions.

**Expected Output:**
- The robot should move forward until it detects an obstacle, at which point it should stop.

## Exercise 3: Fault Injection, Failure Analysis & Debugging

### Step 1: Inject a Fault
1. Introduce a fault in the robot's configuration or program.
2. For example, disconnect one of the sensors or change the motor port assignment.

### Step 2: Observe the Failure
1. Deploy the program to the EV3 brick.
2. Observe the robot's behavior and identify the failure.

**Expected Output:**
- The robot may not respond correctly or may not move as expected.

### Step 3: Debug the Failure
1. Use the "View" menu to enable the "Sensors" and "Motors" panels.
2. Inspect the sensor and motor readings to identify the issue.
3. Correct the fault in the robot's configuration or program.

**Debugging Workflow:**
- Check the sensor connections and ensure they are properly attached.
- Verify that the motor ports are correctly assigned.
- Review the program logic and ensure it is correct.

### Step 4: Verify the Fix
1. Deploy the corrected program to the EV3 brick.
2. Observe the robot's behavior and ensure it functions as expected.

**Expected Output:**
- The robot should now respond correctly and move as expected.

## Challenge Lab: Independent Advanced Scenarios

### Scenario 1: Line Following Robot
1. Build a robot that can follow a black line on a white surface.
2. Use the color sensor to detect the line and adjust the robot's direction accordingly.

**Hints:**
- Use the color sensor to detect the line.
- Use the large motors to control the robot's direction.
- Program the robot to turn left or right based on the color sensor readings.

### Scenario 2: Obstacle Avoidance Robot
1. Build a robot that can navigate around obstacles.
2. Use the ultrasonic sensor to detect obstacles and adjust the robot's path accordingly.

**Hints:**
- Use the ultrasonic sensor to detect obstacles.
- Use the large motors to control the robot's direction.
- Program the robot to turn left or right when an obstacle is detected.

### Scenario 3: Sumo Robot
1. Build a robot that can push another robot out of a circular arena.
2. Use the touch sensors to detect collisions and adjust the robot's direction accordingly.

**Hints:**
- Use the touch sensors to detect collisions.
- Use the large motors to control the robot's direction.
- Program the robot to move forward and turn when a collision is detected.

**AI Mentor:**
- Use the AI mentor to receive guidance and feedback on your progress.
- The AI mentor can provide hints, suggestions, and solutions to common issues.

**Expected Output:**
- The robot should successfully complete the challenge scenario.

---

This lab guide provides a comprehensive hands-on experience in digital design using LEGO Mindstorms. By following the exercises and challenge scenarios, you will gain a deeper understanding of the software and hardware components involved in building and deploying digital models.
