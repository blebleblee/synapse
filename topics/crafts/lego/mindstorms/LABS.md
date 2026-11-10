# Hands-On Operational Lab: Mindstorms
## Objective & Lab Prerequisites

### Objective
The objective of this lab is to provide a comprehensive hands-on experience with LEGO Mindstorms. You will learn how to explore, diagnose, configure, deploy, and debug a Mindstorms robot. By the end of this lab, you will be able to build, program, and troubleshoot a Mindstorms robot independently.

### Lab Prerequisites
- LEGO Mindstorms EV3 kit
- Computer with EV3 software installed (LEGO MINDSTORMS EV3 Home Edition or Education Edition)
- USB cable to connect the EV3 brick to the computer
- Basic understanding of programming concepts (preferably in EV3-G or Python)

## Exercise 1: Exploration, Diagnostics & System State Inspection

### Step 1: Connect the EV3 Brick to the Computer
1. Connect the EV3 brick to your computer using the USB cable.
2. Open the EV3 software on your computer.

**Expected Output:**
- The EV3 software should recognize the EV3 brick and display its status as "Connected."

### Step 2: Explore the EV3 Brick
1. Use the EV3 software to explore the sensors and motors connected to the EV3 brick.
2. Check the battery level and firmware version of the EV3 brick.

**State Inspection Steps:**
- Ensure all sensors and motors are functioning correctly.
- Verify the battery level is above 50%.
- Confirm the firmware version is up to date.

## Exercise 2: Building, Configuring & Deploying a Production Scenario

### Step 1: Build a Simple Robot
1. Follow the instructions in the LEGO Mindstorms EV3 kit to build a simple robot, such as the "Bee-bot."
2. Connect the motors and sensors to the appropriate ports on the EV3 brick.

**Expected Output:**
- The robot should be assembled according to the kit instructions.

### Step 2: Program the Robot
1. Open the EV3 software and create a new project.
2. Use the EV3-G programming environment to create a simple program that makes the robot move forward and backward.

**Code Script:**
```ev3-g
// EV3-G Code Example
MotorOnForSeconds(OUT_A, 50, 2); // Move forward
MotorOnForSeconds(OUT_A, -50, 2); // Move backward
```

### Step 3: Deploy the Program to the Robot
1. Connect the EV3 brick to your computer using the USB cable.
2. Click the "Download and Run" button in the EV3 software to deploy the program to the robot.

**Expected Output:**
- The robot should move forward for 2 seconds and then backward for 2 seconds.

## Exercise 3: Fault Injection, Failure Analysis & Debugging

### Step 1: Introduce a Fault
1. Disconnect one of the motors from the EV3 brick.
2. Deploy the program to the robot.

**Expected Output:**
- The robot will not move as expected due to the disconnected motor.

### Step 2: Diagnose the Fault
1. Check the connections of all motors and sensors.
2. Use the EV3 software to verify the status of the disconnected motor.

**State Inspection Steps:**
- Ensure all motors and sensors are properly connected.
- Confirm the disconnected motor is not recognized by the EV3 software.

### Step 3: Fix the Fault
1. Reconnect the disconnected motor to the EV3 brick.
2. Deploy the program to the robot again.

**Expected Output:**
- The robot should move forward and backward as expected.

## Challenge Lab: Independent Advanced Scenarios

### Scenario 1: Obstacle Avoidance Robot
1. Build an obstacle avoidance robot using the LEGO Mindstorms EV3 kit.
2. Program the robot to detect obstacles using the ultrasonic sensor and adjust its path accordingly.

**Code Script:**
```ev3-g
// EV3-G Code Example for Obstacle Avoidance
While (true) {
    If (UltrasonicSensorDistance(CM) < 20) {
        MotorOnForSeconds(OUT_A, -50, 1); // Move backward
        MotorOnForSeconds(OUT_B, 50, 1); // Turn
    } Else {
        MotorOn(OUT_A, 50); // Move forward
        MotorOn(OUT_B, 50); // Move forward
    }
}
```

### Scenario 2: Line Following Robot
1. Build a line following robot using the LEGO Mindstorms EV3 kit.
2. Program the robot to follow a black line on a white surface using the color sensor.

**Code Script:**
```ev3-g
// EV3-G Code Example for Line Following
While (true) {
    If (ColorSensorColor() == COLOR_BLACK) {
        MotorOn(OUT_A, 50); // Move forward
        MotorOnForSeconds(OUT_B, 50, 0.5); // Turn right
    } Else {
        MotorOnForSeconds(OUT_A, 50, 0.5); // Turn left
        MotorOn(OUT_B, 50); // Move forward
    }
}
```

### Scenario 3: Sumo Robot
1. Build a sumo robot using the LEGO Mindstorms EV3 kit.
2. Program the robot to push an opponent robot out of a circular arena using the touch sensor.

**Code Script:**
```ev3-g
// EV3-G Code Example for Sumo Robot
While (true) {
    If (TouchSensorPressed()) {
        MotorOnForSeconds(OUT_A, -50, 1); // Move backward
        MotorOnForSeconds(OUT_B, 50, 1); // Turn
    } Else {
        MotorOn(OUT_A, 50); // Move forward
        MotorOn(OUT_B, 50); // Move forward
    }
}
```

**Note:** These scenarios are designed to be challenging and require independent thinking and problem-solving skills. Use the AI mentor to assist you in debugging and optimizing your programs.
