# Hands-On Operational Lab: Moc Building
## Objective & Lab Prerequisites

### Objective
This lab guide will walk you through the process of building and operating a MOC (My Own Creation) using Lego bricks. You will learn the fundamentals of MOC building, from designing and planning to building and testing.

### Lab Prerequisites

* Familiarity with Lego bricks and basic building techniques
* Access to a computer with a terminal or command prompt
* Lego bricks and a building surface (optional but recommended)

## Lab Level 1 (Beginner): Exploration, Diagnostics & System State Inspection

### Objective
In this level, you will explore the Lego brick ecosystem, learn basic building techniques, and practice system state inspection using diagnostic tools.

### Step 1: Explore the Lego Brick Ecosystem

* Install the Lego Digital Designer (LDD) software on your computer using the following command:
```bash
sudo apt-get install lego-digital-designer
```
* Launch LDD and explore the interface. Familiarize yourself with the toolbars, menus, and basic building techniques.

### Step 2: Build a Simple MOC

* Create a new project in LDD and build a simple MOC, such as a small house or a car.
* Use the following command to generate a parts list:
```bash
lego-digital-designer --parts-list <project_name>
```
* Inspect the parts list and identify the required bricks.

### Step 3: Inspect System State

* Use the following command to inspect the system state:
```bash
lego-digital-designer --system-state
```
* Analyze the output and identify the current build status.

### Expected Output
The expected output for the `--parts-list` command is a list of required bricks, including their quantities and colors. The expected output for the `--system-state` command is a summary of the current build status, including the number of bricks used and the build time.

## Lab Level 2 (Intermediate): Building, Configuring & Deploying a Production Scenario

### Objective
In this level, you will build a more complex MOC, configure it for production, and deploy it to a test environment.

### Step 1: Build a Complex MOC

* Create a new project in LDD and build a more complex MOC, such as a large castle or a spaceship.
* Use the following command to generate a parts list:
```bash
lego-digital-designer --parts-list <project_name>
```
* Inspect the parts list and identify the required bricks.

### Step 2: Configure for Production

* Use the following command to configure the MOC for production:
```bash
lego-digital-designer --configure-production <project_name>
```
* Analyze the output and identify the configuration settings.

### Step 3: Deploy to Test Environment

* Use the following command to deploy the MOC to a test environment:
```bash
lego-digital-designer --deploy-test <project_name>
```
* Inspect the deployment output and verify that the MOC is deployed correctly.

### Expected Output
The expected output for the `--configure-production` command is a summary of the configuration settings, including the build time and the number of bricks used. The expected output for the `--deploy-test` command is a confirmation message indicating that the MOC is deployed to the test environment.

## Lab Level 3 (Advanced): Fault Injection, Failure Analysis & Root-Cause Debugging

### Objective
In this level, you will inject faults into the MOC, analyze the failures, and debug the root cause.

### Step 1: Inject Faults

* Use the following command to inject faults into the MOC:
```bash
lego-digital-designer --inject-faults <project_name>
```
* Analyze the output and identify the injected faults.

### Step 2: Analyze Failures

* Use the following command to analyze the failures:
```bash
lego-digital-designer --analyze-failures <project_name>
```
* Inspect the output and identify the root cause of the failures.

### Step 3: Debug Root Cause

* Use the following command to debug the root cause:
```bash
lego-digital-designer --debug-root-cause <project_name>
```
* Analyze the output and identify the solution to the problem.

### Expected Output
The expected output for the `--inject-faults` command is a list of injected faults, including their severity and impact. The expected output for the `--analyze-failures` command is a summary of the failures, including the root cause and the recommended solution. The expected output for the `--debug-root-cause` command is a detailed analysis of the root cause and the solution.

## Lab Level 4 (Master Challenge): Independent Advanced Scenarios

### Objective
In this level, you will design and implement your own advanced MOC building scenarios, using the skills and knowledge acquired in the previous levels.

### Step 1: Design Advanced Scenario

* Design a complex MOC building scenario, including multiple components and interactions.
* Use the following command to generate a parts list:
```bash
lego-digital-designer --parts-list <project_name>
```
* Inspect the parts list and identify the required bricks.

### Step 2: Implement Advanced Scenario

* Use the following command to implement the advanced scenario:
```bash
lego-digital-designer --implement-advanced-scenario <project_name>
```
* Analyze the output and identify the implementation details.

### Step 3: Test and Verify

* Use the following command to test and verify the advanced scenario:
```bash
lego-digital-designer --test-advanced-scenario <project_name>
```
* Inspect the output and verify that the scenario is implemented correctly.

### Expected Output
The expected output for the `--implement-advanced-scenario` command is a summary of the implementation details, including the build time and the number of bricks used. The expected output for the `--test-advanced-scenario` command is a confirmation message indicating that the scenario is implemented and tested correctly.

Note: The expected outputs are provided as examples and may vary depending on the specific MOC building scenario and the Lego brick ecosystem.
