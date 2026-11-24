# Operational Verification Labs: Plc And Scada

## Objective & Operational Lab Setup

This laboratory manual equips automation practitioners with hands-on verification protocols for Programmable Logic Controller (PLC) and Supervisory Control and Data Acquisition (SCADA) systems deployed in industrial environments. The exercises ground operational theory in real-world simulation frameworks, structured test methodologies, and diagnostic procedures that mirror factory acceptance tests (FAT), site acceptance tests (SAT), and continuous validation routines executed by control systems engineers in manufacturing, utilities, and process industries.

The verification discipline for PLC/SCADA systems demands rigorous functional testing of discrete logic, analog signal conditioning, network communication integrity, and human-machine interface (HMI) visualization accuracy. Unlike general-purpose computing systems, industrial automation platforms operate under hard real-time constraints with cycle times measured in milliseconds, electromagnetic interference from heavy machinery, and safety-critical interlocks that prevent injury or equipment damage. A single misconfigured timer or failed network packet can trigger emergency shutdowns costing hundreds of thousands of dollars per hour, making pre-deployment verification not merely advisable but legally mandated under standards such as IEC 61508 (Functional Safety) and IEC 61131-3 (PLC Programming Languages).

The laboratory environment synthesizes physical hardware constraints through software simulation tools that replicate PLC instruction execution, input/output (I/O) module behavior, and SCADA polling cycles. Modern verification practice balances three complementary approaches: analytical modeling of control logic using state transition diagrams and Petri nets; quantitative simulation through virtual PLC runtimes and plant models; and empirical testing with hardware-in-the-loop (HIL) configurations where actual field devices interface with simulated controllers. This manual prioritizes the middle path—software simulation environments accessible to practitioners without dedicated industrial labs—while maintaining fidelity to physical system behavior through precise timing models and signal characteristics.

**Primary Simulation Environment: CODESYS V3.5 SP19 with Soft PLC Runtime**

CODESYS (Controller Development System) serves as the reference platform because it implements the complete IEC 61131-3 standard, supports all five PLC programming languages (Ladder Diagram, Function Block Diagram, Structured Text, Instruction List, and Sequential Function Chart), and provides a software-based PLC runtime that executes compiled logic with microsecond-resolution timing. The soft PLC architecture emulates Beckhoff, Schneider Electric, and other industrial controllers without requiring physical hardware. Download CODESYS from the official CODESYS Store (free Development System license) and install the CODESYS Control Win V3 soft PLC package, which runs as a Windows service and exposes I/O via OPC UA or MODBUS TCP protocols.

Installation proceeds through the CODESYS Installer package. Launch the installer, select "CODESYS Development System V3.5 SP19 Patch 2," accept the license agreement, and choose the default installation directory `C:\Program Files\CODESYS 3.5.19.20`. During component selection, ensure "CODESYS Control Win V3 (SL)" is checked—this installs the soft PLC runtime with System Manager integration. After installation, open CODESYS Development System, navigate to Tools → Device Repository, and verify that "CODESYS Control Win V3" appears in the available targets list. Configure the runtime by opening Tools → Update CODESYS Control Win V3, selecting "Start as Service" mode, and setting the cycle time to 10 milliseconds (100 Hz task execution frequency). This configuration provides deterministic scan cycle behavior suitable for discrete manufacturing and process control applications.

**SCADA Visualization Platform: Ignition 8.1 with Trial License**

Inductive Automation's Ignition platform delivers industrial-grade SCADA capabilities through a web-based architecture with native OPC UA communication, SQL database historians, and vector-based HMI graphics. The two-hour trial license resets after gateway restart, making it ideal for iterative laboratory exercises. Download Ignition 8.1.32 from the Inductive Automation website, execute the installer, and configure the gateway for localhost operation on port 8088. During setup, initialize the internal SQLite database for tag history and alarm journaling. Install the Perspective module for responsive web-based HMI development and the OPC UA module for direct communication with the CODESYS soft PLC.

Ignition's architecture separates the gateway (Java-based runtime handling I/O drivers, scripting, and database connections) from clients (web browsers rendering Perspective sessions or Vision clients executing Swing-based interfaces). This separation mirrors industrial deployments where a central gateway server polls field devices while multiple operator workstations access synchronized process data. Configure the OPC UA connection by navigating to Config → OPC UA → Connections → Create New OPC UA Connection. Set the endpoint URL to `opc.tcp://127.0.0.1:4840` (CODESYS soft PLC's default OPC UA server), disable security policies for laboratory use, and set the subscription rate to 100 milliseconds to match the PLC cycle time. Verify connectivity through the OPC Browser within Ignition Designer, where you should observe the CODESYS device tree with Application → PLC_PRG variables visible.

**Signal Simulation and Data Injection Tools**

Industrial automation systems respond to discrete inputs (limit switches, pushbuttons, photoelectric sensors) and analog inputs (temperature transmitters, pressure transducers, flow meters). The laboratory replicates these signals through software forcing and mathematical models. CODESYS provides direct variable forcing through the Watch List interface, allowing manual toggle of BOOL inputs and real-time modification of INT, REAL, and DWORD values. For dynamic signal generation, implement waveform generators within PLC code using Structured Text (ST) functions: sinusoidal patterns with `SIN(UDINT_TO_REAL(CURRENT_TIME) * 0.001)` for harmonic analysis, sawtooth ramps with modulo arithmetic for setpoint tracking tests, and Gaussian noise injection through pseudo-random number generators seeded with system time.

For network-layer verification, Wireshark 4.0.6 captures MODBUS TCP and OPC UA traffic between the soft PLC and SCADA gateway. Configure Wireshark to filter `tcp.port == 4840` for OPC UA or `modbus` for MODBUS TCP, enabling packet-level diagnosis of read/write transactions, subscription acknowledgments, and keepalive heartbeats. Industrial protocols operate with strict timing requirements: MODBUS TCP requests typically expect responses within 500 milliseconds, while OPC UA publishing intervals must maintain jitter below 5% to prevent data loss. Wireshark's Statistics → I/O Graph feature quantifies packet rates and latency distributions, exposing network congestion or driver misconfigurations before field deployment.

**Quantitative Analysis Framework: Python 3.11 with Pandas and Matplotlib**

Post-acquisition analysis of logged tag histories and alarm records requires statistical tools for trend identification, outlier detection, and performance benchmarking. Python scripts interface with Ignition's SQL historians via the `pyodbc` library (connecting to SQLite or SQL Server databases) and process time-series data through `pandas` DataFrames. Install Python 3.11.4, create a virtual environment with `python -m venv scada_lab`, activate it, and install dependencies: `pip install pandas==2.0.3 matplotlib==3.7.2 numpy==1.25.1 pyodbc==4.0.39 scipy==1.11.1`. The SciPy library enables control system analysis through Laplace transform functions, Bode plot generation, and PID tuning parameter optimization.

A typical analysis workflow exports tag history from Ignition's Tag Historian through a SQL query: `SELECT t_stamp, floatvalue FROM sqlt_data_1_2023_08 WHERE tagid = 42 ORDER BY t_stamp`. Import this CSV into a pandas DataFrame, resample to uniform intervals with `df.resample('100ms').mean()` to handle clock skew between PLC and historian, and compute rolling statistics like standard deviation `df['value'].rolling(window=100).std()` to quantify process variability. Matplotlib generates publication-quality plots: time-domain traces for setpoint tracking analysis, frequency-domain FFT plots for cyclic disturbance identification, and scatter plots correlating multiple process variables for causality investigation.

**Laboratory Safety and System Integrity Protocols**

Although the exercises utilize software simulation without physical hazards, operational verification demands discipline identical to live plant commissioning. Maintain isolated network segments for PLC and SCADA traffic: configure the CODESYS soft PLC to bind only to the loopback adapter `127.0.0.1`, preventing inadvertent communication with production networks. Document all logic changes through revision control: initialize a Git repository in the CODESYS project directory and commit after each functional modification with descriptive messages like "Add interlock logic for conveyor E-stop chain." Industrial automation projects routinely fail audits due to undocumented logic changes made during late-night troubleshooting sessions.

Backup SCADA gateway configurations before each exercise by exporting the `.gwbk` file through Ignition's Config → Backup/Restore interface. These archives contain tag definitions, alarm configurations, and security policies that require hours to reconstruct after accidental deletion or corruption. Schedule automated backups during actual deployments, but for laboratory work, manual exports before each major configuration change prevent regression. Label backups with timestamps and exercise identifiers: `ignition_gateway_ex2_20250601_1430.gwbk` provides unambiguous recovery points.

Verify PLC cycle time consistency through CODESYS's online view: connect to the soft PLC runtime, navigate to the Task Configuration, and observe the "Actual Cycle Time" metric. Industrial PLCs specify worst-case execution times (WCET) in their datasheets—typically 1-20 milliseconds depending on program complexity and I/O module count. If actual cycle time exceeds configured cycle time, the PLC enters an overrun condition, potentially skipping I/O updates or triggering watchdog resets. Laboratory exercises deliberately induce overruns during stress testing to observe failure modes and implement mitigation strategies like task prioritization and code optimization.

The subsequent exercises progress from foundational ladder logic verification through multi-variable process simulation to boundary failure analysis and recovery protocols. Each exercise builds a complete, deployable automation solution: Exercise 1 implements a three-tank level control system with cascaded pumps and redundant level sensors; Exercise 2 introduces parametric variation for tuning PID controllers and analyzing pump sequencing strategies; Exercise 3 subjects the system to communication failures, sensor faults, and emergency shutdown scenarios while measuring recovery times and data integrity. Practitioners completing this laboratory manual will possess empirical verification skills directly transferable to industrial commissioning projects, with documented test procedures, acceptance criteria, and troubleshooting diagnostics aligned to IEC standards and vendor best practices.

## Exercise 1: Foundational Practical Implementation

This exercise constructs a three-tank water distribution system governed by PLC logic and monitored through SCADA visualization. The system architecture replicates municipal water treatment plants, industrial cooling loops, and chemical batch processes where level control, pump sequencing, and cascade interlocks prevent overflow damage and maintain process continuity. The implementation employs Ladder Diagram (LD) for intuitive interlock visualization and Structured Text (ST) for PID controller computations, demonstrating hybrid programming techniques mandated by IEC 61131-3 for complex automation applications.

**System Specification and Process Description**

The three-tank cascade consists of Tank A (supply reservoir, 10,000-liter capacity), Tank B (intermediate buffer, 5,000 liters), and Tank C (process feed vessel, 3,000 liters). Water flows from Tank A to Tank B via Pump P1 (150 liters/minute nominal flow), then from Tank B to Tank C via Pump P2 (100 liters/minute). Tank C discharges to a simulated process consumer at a variable rate between 50-120 liters/minute. Each tank mounts three level switches: LSH (level switch high) at 90% capacity, LSL (level switch low) at 10% capacity, and LSM (level switch middle) at 50%. Analog level transmitters (LT) provide continuous 4-20 mA signals proportional to 0-100% level, converted to 0-27648 counts by 12-bit analog input modules using the standard industrial conversion formula: `Level_Percent = ((AI_Counts - 6553) / (26214 - 6553)) * 100`.

The control objective maintains Tank C level between 40-60% through coordinated pump operation while preventing Tank A depletion below LSL and Tank B/C overflow above LSH. Pump sequencing implements priority logic: Pump P1 activates when Tank A exceeds LSM and Tank B falls below LSH; Pump P2 activates when Tank B exceeds LSM and Tank C falls below LSH. Emergency interlocks immediately stop pumps when downstream tanks reach LSH or upstream tanks reach LSL, preventing cascading failures. The SCADA interface displays real-time tank levels, pump statuses, alarm conditions, and historical trends with one-minute resolution.

**CODESYS Project Initialization and Hardware Configuration**

Launch CODESYS Development System 3.5 SP19, select File → New Project, choose "Standard Project," name it `ThreeTank_Cascade`, and select "CODESYS Control Win V3 x64" as the device target. The Device Tree appears with "Device (CODESYS Control Win V3 x64)" as the root node. Right-click the device, select "Add Device," navigate to "I/O" category, and add "Ethernet Adapter (localhost)" to establish the software network interface. Under Ethernet Adapter, add three modules: "K-Bus Terminal" for digital I/O, "KL3062 (2-Ch Analog Input 0-10V)" for analog level transmitters, and "KL2622 (2-Ch Relay Output)" for pump contactors.

Configure the digital I/O mapping by expanding the K-Bus Terminal node, adding sixteen input channels, and assigning symbols: `Tank_A_LSH` (Input 0), `Tank_A_LSM` (Input 1), `Tank_A_LSL` (Input 2), `Tank_B_LSH` (Input 3), `Tank_B_LSM` (Input 4), `Tank_B_LSL` (Input 5), `Tank_C_LSH` (Input 6), `Tank_C_LSM` (Input 7), `Tank_C_LSL` (Input 8), `Pump_P1_Running` (Input 9), `Pump_P2_Running` (Input 10), `Emergency_Stop` (Input 11). Add four output channels: `Pump_P1_Start` (Output 0), `Pump_P1_Stop` (Output 1), `Pump_P2_Start` (Output 2), `Pump_P2_Stop` (Output 3). Industrial best practice separates start and stop commands rather than using single-coil latching to comply with safety standards requiring explicit de-energization paths.

Map the analog input module KL3062 to `Tank_A_Level_AI` (Channel 0), `Tank_B_Level_AI` (Channel 1), and add a second KL3062 for `Tank_C_Level_AI` (Channel 0). Configure each channel's scaling parameters by right-clicking the channel, selecting "Channel Properties," and setting the engineering units: Input Range = "0-27648 counts," Physical Range = "0-100 %," Data Type = "REAL." CODESYS automatically applies linearization during the I/O scan cycle, presenting scaled values directly to application code.

Right-click "Application" in the Device Tree, select "Add Object → POU (Program Organization Unit)," name it `PRG_Tank_Control`, and select "Ladder Diagram (LD)" as the implementation language. This POU contains the primary control logic. Add a second POU named `FB_Tank_Simulation` with "Function Block (FB)" type and "Structured Text (ST)" implementation—this function block simulates the hydraulic dynamics for software-in-the-loop testing without external plant models.

**Hydraulic Simulation Function Block Implementation**

Open `FB_Tank_Simulation` and declare the function block interface with input, output, and internal variables. The simulation integrates flow rates numerically using Euler forward approximation with fixed time steps matching the PLC cycle time. This approach trades integration accuracy for computational simplicity, acceptable for automation verification where physical plant dynamics typically operate at timescales much slower than PLC cycle rates.

```text
FUNCTION_BLOCK FB_Tank_Simulation
VAR_INPUT
    Pump_P1_Command : BOOL;      // Pump P1 start command from PLC
    Pump_P2_Command : BOOL;      // Pump P2 start command from PLC
    Process_Demand  : REAL;      // Process consumption rate [L/min]
    Reset           : BOOL;      // Reset simulation to initial conditions
END_VAR

VAR_OUTPUT
    Tank_A_Level    : REAL;      // Tank A level [%]
    Tank_B_Level    : REAL;      // Tank B level [%]
    Tank_C_Level    : REAL;      // Tank C level [%]
    Tank_A_LSH      : BOOL;      // Tank A high level switch
    Tank_A_LSM      : BOOL;      // Tank A medium level switch
    Tank_A_LSL      : BOOL;      // Tank A low level switch
    Tank_B_LSH      : BOOL;
    Tank_B_LSM      : BOOL;
    Tank_B_LSL      : BOOL;
    Tank_C_LSH      : BOOL;
    Tank_C_LSM      : BOOL;
    Tank_C_LSL      : BOOL;
    Pump_P1_Flow    : REAL;      // Actual P1 flow rate [L/min]
    Pump_P2_Flow    : REAL;      // Actual P2 flow rate [L/min]
END_VAR

VAR
    Tank_A_Volume   : REAL := 5000.0;  // Initial volume [L]
    Tank_B_Volume   : REAL := 2500.0;
    Tank_C_Volume   : REAL := 1500.0;
    
    Tank_A_Capacity : REAL := 10000.0; // Tank capacities [L]
    Tank_B_Capacity : REAL := 5000.0;
    Tank_C_Capacity : REAL := 3000.0;
    
    P1_Nominal_Flow : REAL := 150.0;   // Pump nominal flows [L/min]
    P2_Nominal_Flow : REAL := 100.0;
    
    Cycle_Time_Sec  : REAL := 0.01;    // PLC cycle time [s], 10ms = 0.01s
    
    P1_Flow_Actual  : REAL;
    P2_Flow_Actual  : REAL;
END_VAR

// Reset logic
IF Reset THEN
    Tank_A_Volume := 5000.0;
    Tank_B_Volume := 2500.0;
    Tank_C_Volume := 1500.0;
END_IF

// Pump flow calculation with hysteresis and startup delay
IF Pump_P1_Command AND Tank_A_Volume > (Tank_A_Capacity * 0.02) THEN
    P1_Flow_Actual := P1_Nominal_Flow;
ELSE
    P1_Flow_Actual := 0.0;
END_IF

IF Pump_P2_Command AND Tank_B_Volume > (Tank_B_Capacity * 0.02) THEN
    P2_Flow_Actual := P2_Nominal_Flow;
ELSE
    P2_Flow_Actual := 0.0;
END_IF

// Tank A volume integration: inflow (none, supply reservoir) - outflow (P1)
Tank_A_Volume := Tank_A_Volume - (P1_Flow_Actual * Cycle_Time_Sec * (60.0 / 1.0));
IF Tank_A_Volume < 0.0 THEN Tank_A_Volume := 0.0; END_IF
IF Tank_A_Volume > Tank_A_Capacity THEN Tank_A_Volume := Tank_A_Capacity; END_IF

// Tank B volume integration: inflow (P1) - outflow (P2)
Tank_B_Volume := Tank_B_Volume + (P1_Flow_Actual * Cycle_Time_Sec * (60.0 / 1.0)) 
                                - (P2_Flow_Actual * Cycle_Time_Sec * (60.0 / 1.0));
IF Tank_B_Volume < 0.0 THEN Tank_B_Volume := 0.0; END_IF
IF Tank_B_Volume > Tank_B_Capacity THEN Tank_B_Volume := Tank_B_Capacity; END_IF

// Tank C volume integration: inflow (P2) - outflow (process demand)
Tank_C_Volume := Tank_C_Volume + (P2_Flow_Actual * Cycle_Time_Sec * (60.0 / 1.0))
                                - (Process_Demand * Cycle_Time_Sec * (60.0 / 1.0));
IF Tank_C_Volume < 0.0 THEN Tank_C_Volume := 0.0; END_IF
IF Tank_C_Volume > Tank_C_Capacity THEN Tank_C_Volume := Tank_C_Capacity; END_IF

// Convert volumes to percentages
Tank_A_Level := (Tank_A_Volume / Tank_A_Capacity) * 100.0;
Tank_B_Level := (Tank_B_Volume / Tank_B_Capacity) * 100.0;
Tank_C_Level := (Tank_C_Volume / Tank_C_Capacity) * 100.0;

// Level switch logic with hysteresis (±2%)
Tank_A_LSH := Tank_A_Level >= 90.0;
Tank_A_LSM := Tank_A_Level >= 48.0 AND Tank_A_Level <= 52.0;
Tank_A_LSL := Tank_A_Level <= 10.0;

Tank_B_LSH := Tank_B_Level >= 90.0;
Tank_B_LSM := Tank_B_Level >= 48.0 AND Tank_B_Level <= 52.0;
Tank_B_LSL := Tank_B_Level <= 10.0;

Tank_C_LSH := Tank_C_Level >= 90.0;
Tank_C_LSM := Tank_C_Level >= 48.0 AND Tank_C_Level <= 52.0;
Tank_C_LSL := Tank_C_Level <= 10.0;

// Output actual flow rates for monitoring
Pump_P1_Flow := P1_Flow_Actual;
Pump_P2_Flow := P2_Flow_Actual;
```

This function block encapsulates the physical plant behavior, isolating control logic from simulation mechanics. The numerical integration assumes constant flow rates within each cycle period, introducing integration error proportional to cycle time squared. For 10-millisecond cycles, this error remains negligible compared to real-world sensor measurement uncertainties and pump flow variations. The hysteresis on level switches prevents chattering when liquid levels oscillate near thresholds due to surface turbulence or sloshing.

**Ladder Diagram Control Logic Implementation**

Open `PRG_Tank_Control` and declare global variables at the top of the program. CODESYS ladder logic follows IEC 61131-3 conventions: left power rail (implicit TRUE), contact symbols (—| |— for normally open, —|/|— for normally closed), coil symbols (—( )— for output energization, —(S)— for set-latch, —(R)— for reset-unlatch), and right power rail (implicit evaluation termination). Each rung implements a discrete control function, progressing from safety interlocks to pump sequencing logic.

Declare the following variables in the declaration section:
```text
PROGRAM PRG_Tank_Control
VAR
    Sim : FB_Tank_Simulation;           // Hydraulic simulation instance
    
    Process_Demand_Input : REAL := 75.0; // Process consumption [L/min]
    
    Pump_P1_Interlock_OK : BOOL;        // P1 safe to run
    Pump_P2_Interlock_OK : BOOL;        // P2 safe to run
    
    Pump_P1_Start_Cmd : BOOL;           // P1 start command
    Pump_P1_Stop_Cmd  : BOOL;           // P1 stop command
    Pump_P2_Start_Cmd : BOOL;           // P2 start command
    Pump_P2_Stop_Cmd  : BOOL;           // P2 stop command
    
    Pump_P1_Running   : BOOL;           // P1 status latch
    Pump_P2_Running   : BOOL;           // P2 status latch
    
    Emergency_Stop    : BOOL := FALSE;  // E-stop pushbutton
    System_Reset      : BOOL := FALSE;  // Reset button
    
    Tank_A_Level_Pct  : REAL;           // Tank levels for SCADA
    Tank_B_Level_Pct  : REAL;
    Tank_C_Level_Pct  : REAL;
END_VAR
```

Implement the ladder logic rungs in the graphical LD editor. Each rung is described here with symbolic notation; translate to graphical ladder symbols in CODESYS:

**Rung 1-3: Simulation Function Block Call**
The first three rungs invoke the hydraulic simulation and map outputs to process variables. In LD, function block calls appear as rectangular boxes with input pins on the left and output pins on the right.
```text
(* Rung 1: Call simulation FB *)
Sim(
    Pump_P1_Command := Pump_P1_Running,
    Pump_P2_Command := Pump_P2_Running,
    Process_Demand := Process_Demand_Input,
    Reset := System_Reset
);

(* Rung 2: Map tank levels *)
Tank_A_Level_Pct := Sim.Tank_A_Level;
Tank_B_Level_Pct := Sim.Tank_B_Level;
Tank_C_Level_Pct := Sim.Tank_C_Level;
```

**Rung 4-5: Pump P1 Interlock Logic**
Pump P1 operates only when Tank A has sufficient volume (above LSL) and Tank B has capacity to receive flow (below LSH). Emergency stop immediately disables interlocks.
```text
(* Rung 4: P1 interlock conditions *)
—|/|—Emergency_Stop—| |—Sim.Tank_A_LSL—|/|—Sim.Tank_B_LSH—( )—Pump_P1_Interlock_OK
    (NOT E-stop)    (NOT A_LSL)       (NOT B_LSH)
```

**Rung 6-7: Pump P1 Start/Stop Command Generation**
Start P1 when interlock permits, Tank A above medium level, and Tank B below medium level. Stop P1 when interlock fails or Tank B reaches high level.
```text
(* Rung 6: P1 start conditions *)
—| |—Pump_P1_Interlock_OK—| |—Sim.Tank_A_LSM—|/|—Sim.Tank_B_LSM—( )—Pump_P1_Start_Cmd
                                            (B below medium)

(* Rung 7: P1 stop conditions *)
—|/|—Pump_P1_Interlock_OK—( )—Pump_P1_Stop_Cmd
     (interlock fail)
—| |—Sim.Tank_B_LSH—( )—Pump_P1_Stop_Cmd
     (B high level)
```

**Rung 8: Pump P1 Status Latch**
Implement seal-in logic with set/reset coils. Start command sets the latch, stop command resets it.
```text
(* Rung 8: P1 latch *)
—| |—Pump_P1_Start_Cmd—(S)—Pump_P1_Running
—| |—Pump_P1_Stop_Cmd—(R)—Pump_P1_Running
```

**Rung 9-13: Pump P2 Interlock and Control (Parallel Structure)**
Replicate the P1 logic structure for P2, substituting Tank B/C level switches.
```text
(* Rung 9: P2 interlock *)
—|/|—Emergency_Stop—| |—Sim.Tank_B_LSL—|/|—Sim.Tank_C_LSH—( )—Pump_P2_Interlock_OK

(* Rung 10: P2 start *)
—| |—Pump_P2_Interlock_OK—| |—Sim.Tank_B_LSM—|/|—Sim.Tank_C_LSM—( )—Pump_P2_Start_Cmd

(* Rung 11-12: P2 stop *)
—|/|—Pump_P2_Interlock_OK—( )—Pump_P2_Stop_Cmd
—| |—Sim.Tank_C_LSH—( )—Pump_P2_Stop_Cmd

(* Rung 13: P2 latch *)
—| |—Pump_P2_Start_Cmd—(S)—Pump_P2_Running
—| |—Pump_P2_Stop_Cmd—(R)—Pump_P2_Running
```

**Rung 14: System Reset Logic**
The reset button clears all latches and reinitializes simulation volumes. Implement as a one-shot (rising edge detection) to prevent continuous reset during button hold.
```text
VAR
    Reset_Button : BOOL;
    Reset_Trigger : R_TRIG;  // Rising edge detector
END_VAR

(* Rung 14: Reset one-shot *)
Reset_Trigger(CLK := Reset_Button);
System_Reset := Reset_Trigger.Q;
```

Compile the project by pressing F11 or selecting Build → Build. The CODESYS compiler performs type checking, memory allocation, and instruction optimization. Review the "Messages" pane for errors or warnings. Common issues include undeclared variables, type mismatches (BOOL assigned to REAL), and circular dependencies in function block calls. Industrial PLC projects routinely contain 10,000+ lines of code across hundreds of POUs; establish naming conventions and modular architecture early to manage complexity.

**OPC UA Server Configuration and Tag Export**

CODESYS embeds an OPC UA server within the soft PLC runtime, exposing PLC variables as OPC UA nodes accessible to SCADA systems. Configure the server by navigating to Device → CODESYS Control Win V3 x64 → Symbol Configuration. Enable "Support OPC UA Features" and select "Export all application variables." This publishes every VAR and VAR_GLOBAL declaration as OPC UA nodes under the namespace `Application/PRG_Tank_Control/`. Variables nested within function block instances appear hierarchically: `Sim.Tank_A_Level` maps to node `Application/PRG_Tank_Control/Sim/Tank_A_Level`.

Set security policies for laboratory use by editing the OPC UA server configuration file located at `C:\ProgramData\CODESYS\CODESYSControlWinV3\OpcUaServer.xml`. Modify the `<SecurityPolicies>` section to include `None` policy, disabling encryption and authentication for local testing:
```xml
<SecurityPolicies>
    <SecurityPolicy>
        <Uri>http://opcfoundation.org/UA/SecurityPolicy#None</Uri>
        <Mode>SignAndEncrypt</Mode>
    </SecurityPolicy>
</SecurityPolicies>
```
Production deployments mandate encryption (Basic256Sha256) and certificate-based authentication, but laboratory exercises prioritize rapid iteration over security hardening. Save the configuration and restart the CODESYS Control Win V3 service through Windows Services Manager (`services.msc`).

Download the PLC application by clicking "Login" (green plug icon), selecting "CODESYS Control Win V3" as the target, and clicking "Download" when prompted. The soft PLC transitions to "Stop" mode. Switch to "Run" mode by clicking the "Start" button (green arrow). The PLC begins executing the task configuration at 10-millisecond intervals, updating I/O and evaluating ladder logic rungs sequentially from top to bottom each cycle.

Open the Watch List by selecting View → Watch and Debug Windows → Watch List. Add variables to monitor runtime values: right-click in the Watch List, select "Add Variable," and enter `PRG_Tank_Control.Tank_A_Level_Pct`, `PRG_Tank_Control.Pump_P1_Running`, `PRG_Tank_Control.Pump_P2_Running`. Force variables to simulate external conditions: right-click `PRG_Tank_Control.Reset_Button`, select "Force Value," enter `TRUE`, and click "Force All Values." The simulation resets to initial conditions. Release the force by unchecking the force checkbox. Toggle `Process_Demand_Input` between 50.0 and 120.0 to observe pump sequencing responses.

**Ignition SCADA Project Configuration and HMI Development**

Launch a web browser and navigate to `http://localhost:8088` to access the Ignition Gateway interface. Log in with default credentials (username: `admin`, password: `password`). Click "Config" in the left navigation menu, then "OPC UA → Connections." Verify the CODESYS connection created during setup shows "Connected" status with green indicator. If disconnected, click "Edit," verify the endpoint URL matches `opc.tcp://127.0.0.1:4840`, and test the connection.

Open Ignition Designer by clicking "Designer" in the gateway home page, selecting the "Create New Project" option, naming it `ThreeTank_SCADA`, and choosing "Perspective" as the primary visualization module. Perspective uses responsive web components rendered in modern browsers, replacing legacy Java-based clients with HTML5/JavaScript architecture suitable for mobile operator interfaces.

**Tag Provider and Historian Configuration**

Navigate to Config → Tags in the gateway interface. Create a new Tag Provider named `PLC_Tags` with default settings (memory tags with no historical logging). Under the PLC_Tags provider, create a folder structure: `Tanks/Tank_A`, `Tanks/Tank_B`, `Tanks/Tank_C`, `Pumps/Pump_P1`, `Pumps/Pump_P2`, `System`. Within each folder, create OPC UA tags by right-clicking, selecting "New Tag → OPC Tag," and browsing the CODESYS OPC UA server's address space.

Create the following tags with exact OPC UA node paths:
- `Tanks/Tank_A/Level`: Node path `[OPC UA Connection]ns=4;s=|var|CODESYS Control Win V3 x64.Application.PRG_Tank_Control.Tank_A_Level_Pct`, Data Type `Float`, Scan Class `Default (1000ms)`
- `Tanks/Tank_A/LSH`: Node path ending `.Sim.Tank_A_LSH`, Data Type `Boolean`
- `Tanks/Tank_A/LSM`: Node path ending `.Sim.Tank_A_LSM`, Data Type `Boolean`
- `Tanks/Tank_A/LSL`: Node path ending `.Sim.Tank_A_LSL`, Data Type `Boolean`

Repeat for Tank B and Tank C. Create pump status tags:
- `Pumps/Pump_P1/Running`: Node path ending `.Pump_P1_Running`, Data Type `Boolean`
- `Pumps/Pump_P1/Flow`: Node path ending `.Sim.Pump_P1_Flow`, Data Type `Float`

Configure tag history by right-clicking each level and flow tag, selecting "Edit Tag," and enabling "History" with the following parameters: Storage Provider `Default Historical`, Sample Mode `On Change by Value`, Deadband `0.5` (suppress historian writes for changes less than 0.5%), Max Time Between Samples `60 seconds`. This configuration balances historian database growth against trend resolution: small level fluctuations don't generate excessive records, but significant changes log immediately, and quiescent periods still record at least one sample per minute for alarm auditing.

**Perspective HMI View Construction**

Open Designer, navigate to the Perspective section, and create a new view named `Main_Overview` with portrait orientation (1920×1080 resolution). The Perspective canvas uses flexbox-based responsive layout; components automatically adapt to screen sizes from desktop monitors to tablets. Add a "Coordinate Container" from the component palette to enable absolute positioning suitable for mimics (process graphics resembling P&ID diagrams).

Drag three "Tank" components from the Symbols palette into the coordinate container, positioning them horizontally at coordinates (200, 300), (600, 300), and (1000, 300). Configure each tank's bindings: right-click Tank A, select "Bindings," and add a "Tag Binding" to `Tank_A/Level` with bidirectional mode disabled (read-only). Set the tank's `fillPercent` property to `{Tank_A/Level.value}`. Change the tank color property to a conditional expression:
```text
if({Tank_A/LSH.value}, "red", if({Tank_A/LSL.value}, "yellow", "blue"))
```
This expression renders the tank red during high-level alarm, yellow during low-level alarm, and blue during normal operation, providing immediate situational awareness.

Add "Label" components above each tank displaying the tank identifier ("Tank A") and below each tank displaying the numeric level value with formatting: `{Tank_A/Level.value}%` with number format `0.0` (one decimal place). Position "LED" indicator components adjacent to each tank, binding them to LSH, LSM, and LSL tags with color mappings: LSH = red, LSM = yellow, LSL = green when active.

Drag two "Motor" symbols from the Industrial Symbols palette, positioning them between tanks to represent pumps P1 and P2. Bind the motor `running` property to `{Pump_P1/Running.value}`. The motor symbol animates with rotation when the binding evaluates to TRUE, providing dynamic visual feedback. Add numeric displays below each motor showing actual flow rates.

Create "Button" components for operator control: "Reset System" button calling a script that writes TRUE to the PLC's reset tag, "Emergency Stop" button with red background, and "Increase/Decrease Demand" buttons modifying the process demand setpoint. Implement the Reset button's onClick event with a Gateway Script:
```python
system.tag.writeBlocking(["[PLC_Tags]System/Reset_Button"], [True])
system.util.invokeLater(lambda: system.tag.writeBlocking(["[PLC_Tags]System/Reset_Button"], [False]), 100)
```
This script writes TRUE, waits 100 milliseconds, then writes FALSE, generating the rising edge required by the PLC's one-shot logic.

Add a "Table" component at the bottom of the view displaying alarm history. Bind the table data property to a Named Query that retrieves the 20 most recent alarm events from the Ignition alarm journal:
```sql
SELECT evt_eventtime, displaypath, eventstate, notes 
FROM alarm_events 
ORDER BY evt_eventtime DESC 
LIMIT 20
```

Configure alarms on critical tags by editing Tank_A/Level, navigating to the "Alarms" tab, and adding two alarms: "Tank A High Level" with setpoint 90.0, priority "High," mode "Above Setpoint," and "Tank A Low Level" with setpoint 10.0, priority "Medium," mode "Below Setpoint." Repeat for all tanks. Alarm pipelines route notifications to the central alarm journal and optionally send email/SMS alerts via configured notification profiles.

Add a "Power Chart" component spanning the right third of the view for real-time trending. Configure the pen set with six pens: Tank A/B/C levels (left Y-axis, 0-100%), Pump P1/P2 flows (right Y-axis, 0-200 L/min). Set the time range to "Last 10 Minutes" with auto-scrolling enabled. Operators use this chart to diagnose oscillations, identify steady-state operation, and correlate pump starts with level responses.

Save the view and launch a Perspective Session by clicking "Tools → Launch Project → Run" in Designer. The browser opens a new tab rendering the HMI in real-time. Watch tank levels rise and fall as pumps sequence according to PLC logic. Trigger alarms by forcing Tank A level to 95% in CODESYS Watch List; observe the tank symbol turn red, LED indicators activate, and alarm table populates with timestamped events.

**Functional Verification Test Procedure**

Execute the following test sequence while recording observations in a laboratory notebook or structured test report. Document PLC variable values, SCADA screen captures, and timing measurements for regulatory compliance and troubleshooting reference.

**Test 1: Normal Operation Steady State**
Set process demand to 75 L/min (equal to P1 and P2 flow differential). Observe Tank C level stabilize at approximately 50% after transient settling (typically 5-10 minutes simulation time). Verify Pump P2 runs continuously, Pump P1 cycles based on Tank A/B levels. Measure pump cycle times: Pump P1 on-time should equal approximately (Tank_B_Capacity × 0.4) / (P1_Flow - P2_Flow) = (5000 × 0.4) / (150 - 100) = 40 minutes. Record actual cycle time from SCADA trend; deviations indicate simulation parameter mismatches or integration errors.

**Test 2: Low-Level Interlock Activation**
Force Tank A level to 5% via CODESYS Watch List or reduce Tank A initial volume in simulation FB. Observe Pump P1 stop immediately when Tank_A_LSL activates, preventing dry-run cavitation damage. Verify Tank B level decreases as Pump P2 continues transferring to Tank C. When Tank B reaches LSL, Pump P2 should also stop. Tank C continues draining until process demand is satisfied or level reaches minimum. Capture alarm journal entries showing cascaded low-level alarms with timestamps demonstrating sequential propagation.

**Test 3: High-Level Interlock Activation**
Set process demand to 0 L/min, simulating process shutdown while pumps run. Observe Tank C fill until LSH activates at 90%, stopping Pump P2. Tank B subsequently fills, eventually reaching LSH and stopping Pump P1. Verify no overflow occurs (levels do not exceed 100%). Measure response time from LSH activation to pump stop: should be less than one PLC cycle time (10 milliseconds) plus pump motor coast-down (typically 500 milliseconds for small pumps, not modeled in basic simulation). Industrial applications require faster response for hazardous materials, implementing redundant safety relays independent of PLC logic.

**Test 4: Pump Sequencing Coordination**
Set process demand to 140 L/min (exceeding combined pump capacity of P1 + P2 net flow). Observe Tank C level gradually deplete despite both pumps running, demonstrating capacity limitations. Tank C reaches LSL, triggering low-level alarm. Increase process demand further to 200 L/min; verify system remains stable (tanks don't go negative in simulation due to IF clamp logic). This test validates graceful degradation under load conditions exceeding design specifications.

**Test 5: Emergency Stop and System Reset**
During normal operation, activate emergency stop via SCADA button or force PLC variable. All pumps should stop immediately regardless of level conditions. Attempt to restart pumps by toggling start conditions; verify interlocks prevent pump operation while emergency stop remains active. Release emergency stop and click System Reset button. Observe simulation reinitialize to default volumes (Tank A = 50%, B = 50%, C = 50%). Pumps resume sequencing based on reset level conditions.

Record test results in a table format:

| Test ID | Description | Expected Result | Actual Result | Pass/Fail | Notes |
|---------|-------------|-----------------|---------------|-----------|-------|
| T1.1    | Steady-state operation 75 L/min | Tank C stable ±5% | Tank C at 49.2%, ±1.3% variation | PASS | P1 cycle time 38.5 min |
| T2.1    | Tank A low-level interlock | P1 stops at LSL | P1 stopped at 9.8% level | PASS | Response < 20ms |
| T3.1    | Tank C high-level interlock | P2 stops at LSH | P2 stopped at 90.2% level | PASS | No overflow observed |

Documentation for industrial commissioning requires photographic evidence (SCADA screenshots), signed witness statements from client representatives, and calibration certificates for physical instruments. Laboratory exercises substitute screen recordings and timestamped log files, but practitioners should develop documentation discipline transferable to regulated environments (FDA pharmaceutical, nuclear power, aerospace).

## Exercise 2: Parameter Variation & Empirical Analysis

This exercise introduces parametric sensitivity analysis and control tuning through systematic variation of PLC timing parameters, pump flow rates, and SCADA alarming thresholds. Industrial automation systems operate across wide parameter spaces: batch processes handle recipes with different ingredient densities and reaction kinetics; utility systems accommodate seasonal demand swings and equipment degradation. Empirical analysis quantifies how parameter changes affect key performance indicators (KPIs) like setpoint tracking error, pump cycle frequency (maintenance cost driver), and alarm rate (operator distraction metric).

The methodology combines design-of-experiments (DOE) principles with time-series statistical analysis. Rather than exhaustive parameter sweeps computationally expensive for real-time simulation, the exercise employs fractional factorial designs isolating main effects and two-factor interactions. Data collection leverages Ignition's SQL historian and Python-based post-processing to compute performance metrics from tag trends. Practitioners completing this exercise will possess quantitative tuning skills applicable to loop optimization, energy minimization, and equipment protection strategies.

**Parametric Design Matrix and Experimental Setup**

Identify five critical parameters governing system behavior: (1) PLC cycle time `T_cycle` [5, 10, 20 milliseconds]; (2) Pump P1 nominal flow `Q_P1` [120, 150, 180 L/min]; (3) Process demand setpoint `Q_demand` [60, 90, 120 L/min]; (4) Tank C LSH threshold `LSH_C` [85, 90, 95 %]; (5) SCADA historian deadband `DB_hist` [0.5, 1.0, 2.0 %]. The baseline configuration from Exercise 1 corresponds to center-point values: [10 ms, 150 L/min, 90 L/min, 90%, 1.0%].

Construct a two-level fractional factorial design (2^(5-1) resolution V) requiring 16 experimental runs plus three center-point replicates for curvature detection. Use statistical software (Minitab, JMP, or Python's `pyDOE2` library) to generate the run matrix with alias structure preventing confounding of main effects with two-factor interactions. Each run simulates 120 minutes of operation (allowing 4-6 pump cycles for steady-state statistics), logging historian data at one-second resolution.

Install `pyDOE2` and generate the design matrix:
```python
import numpy as np
from pyDOE2 import fracfact
import pandas as pd

# Define the 2^(5-1) fractional factorial design with generator E = ABCD
design = fracfact("a b c d abcd")

# Map coded values (-1, +1) to actual parameter ranges
param_ranges = {
    'T_cycle': [5, 20],
    'Q_P1': [120, 180],
    'Q_demand': [60, 120],
    'LSH_C': [85, 95],
    'DB_hist': [0.5, 2.0]
}

def coded_to_actual(coded_val, param_range):
    return param_range[0] + (coded_val + 1) / 2 * (param_range[1] - param_range[0])

# Create run matrix
runs = []
for i, row in enumerate(design):
    run = {
        'Run_ID': i + 1,
        'T_cycle_ms': coded_to_actual(row[0], param_ranges['T_cycle']),
        'Q_P1_Lpm': coded_to_actual(row[1], param_ranges['Q_P1']),
        'Q_demand_Lpm': coded_to_actual(row[2], param_ranges['Q_demand']),
        'LSH_C_pct': coded_to_actual(row[3], param_ranges['LSH_C']),
        'DB_hist_pct': coded_to_actual(row[4], param_ranges['DB_hist'])
    }
    runs.append(run)

# Add center point replicates
center_point = {
    'Run_ID': 'CP',
    'T_cycle_ms': 10.0,
    'Q_P1_Lpm': 150.0,
    'Q_demand_Lpm': 90.0,
    'LSH_C_pct': 90.0,
    'DB_hist_pct': 1.0
}
runs.extend([center_point] * 3)

df_runs = pd.DataFrame(runs)
df_runs.to_csv('DOE_run_matrix.csv', index=False)
print(df_runs)
```

This script produces a CSV file with 19 rows specifying parameter combinations for each experimental run. The fractional factorial structure enables estimation of all five main effects and ten two-factor interactions with only 16 runs, dramatically reducing test time compared to full factorial (32 runs) or one-factor-at-a-time approaches (requiring >50 runs for equivalent statistical power).

**CODESYS Project Parameterization and Batch Execution**

Modify the `PRG_Tank_Control` program to read parameters from global variables rather than hard-coded constants. Create a new Global Variable List (GVL) named `GVL_Parameters`:
```text
VAR_GLOBAL
    PARAM_Cycle_Time_ms : REAL := 10.0;
    PARAM_P1_Flow_Lpm   : REAL := 150.0;
    PARAM_Demand_Lpm    : REAL := 90.0;
    PARAM_LSH_C_pct     : REAL := 90.0;
END_VAR
```

Edit `FB_Tank_Simulation` to use `GVL_Parameters.PARAM_P1_Flow_Lpm` instead of the local `P1_Nominal_Flow` constant. Similarly, update the LSH comparison threshold for Tank C from hard-coded 90.0 to `GVL_Parameters.PARAM_LSH_C_pct`. Recompile and download the modified project. The PLC cycle time requires modification in the Task Configuration: navigate to Application → Task Configuration, double-click "Task," and set "Cycle Time" to reference `GVL_Parameters.PARAM_Cycle_Time_ms` (requires conversion from milliseconds to microseconds: multiply by 1000).

Implement a data collection script in Ignition's Gateway Scripting to automate run execution and historian extraction. Create a Gateway Event Script triggered by a "Start DOE Run" tag transition:

```python
# Gateway Event Script: DOE_Run_Controller
import system.tag
import system.db
import csv
import time

def execute_doe_run(run_id, params):
    # Write parameters to PLC tags
    param_tags = [
        "[PLC_Tags]System/PARAM_Cycle_Time_ms",
        "[PLC_Tags]System/PARAM_P1_Flow_Lpm",
        "[PLC_Tags]System/PARAM_Demand_Lpm",
        "[PLC_Tags]System/PARAM_LSH_C_pct"
    ]
    param_values = [
        params['T_cycle_ms'],
        params['Q_P1_Lpm'],
        params['Q_demand_Lpm'],
        params['LSH_C_pct']
    ]
    system.tag.writeBlocking(param_tags, param_values)
    
    # Reset PLC simulation
    system.tag.writeBlocking(["[PLC_Tags]System/Reset_Button"], [True])
    time.sleep(0.2)
    system.tag.writeBlocking(["[PLC_Tags]System/Reset_Button"], [False])
    
    # Wait for simulation to stabilize (15 minutes) then collect 120 minutes
    time.sleep(15 * 60)
    
    # Mark data collection window in historian
    start_time = system.date.now()
    system.tag.writeBlocking(["[PLC_Tags]System/DOE_Run_Active"], [run_id])
    
    time.sleep(120 * 60)  # 120 minute data collection
    
    end_time = system.date.now()
    system.tag.writeBlocking(["[PLC_Tags]System/DOE_Run_Active"], [0])
    
    # Extract historian data for analysis
    query = """
        SELECT t_stamp, intvalue, floatvalue, stringvalue, tagid
        FROM sqlt_data_1_2023_08
        WHERE tagid IN (
            SELECT id FROM sqlth_te WHERE tagpath LIKE '%Tank_C/Level%'
            OR tagpath LIKE '%Pump_P1/Running%'
        )
        AND t_stamp BETWEEN ? AND ?
        ORDER BY t_stamp
    """
    data = system.db.runPrepQuery(query, [start_time, end_time], "Historian")
    
    # Save to CSV for post-processing
    csv_path = "C:/DOE_Results/Run_{}_data.csv".format(run_id)
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'tagid', 'value'])
        for row in data:
            writer.writerow(row)
    
    return csv_path

# Main execution loop
run_matrix = system.file.readFileAsString("C:/DOE_Results/DOE_run_matrix.csv")
runs = csv.DictReader(run_matrix.split('\n'))

for run in runs:
    if run['Run_ID'] != 'CP':
        run_id = int(run['Run_ID'])
    else:
        run_id = 'CP' + str(time.time())  # Unique CP identifiers
    
    execute_doe_run(run_id, run)
```

This automation script eliminates manual parameter entry and ensures consistent data collection windows across all runs. Industrial DOE studies for complex processes like distillation columns or polymerization reactors may require days of continuous operation per run; automated orchestration prevents operator errors and maintains experimental rigor during overnight or weekend testing.

**Historian Data Post-Processing and KPI Calculation**

After completing all 19 experimental runs, the `C:/DOE_Results/` directory contains CSV files with raw historian time-series data. Each file requires post-processing to compute performance metrics for statistical analysis. Develop a Python analysis script that calculates five KPIs per run:

1. **Tank C Level Tracking Error (RMSE)**: Root-mean-square deviation from 50% setpoint
2. **Pump P1 Cycle Frequency**: Number of start/stop cycles per hour
3. **Alarm Rate**: High/low level alarms triggered per hour
4. **Historian Database Size**: Total records written (storage cost proxy)
5. **Steady-State Settling Time**: Time required to reach ±2% of setpoint after reset

Implement the analysis script:
```python
import pandas as pd
import numpy as np
import glob
from scipy import signal

def calculate_kpis(run_id, csv_path):
    # Load historian data
    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    
    # Separate tags
    tank_c_level = df[df['tagid'] == 42]['value'].values  # Assuming tagid 42 = Tank C Level
    pump_p1_run = df[df['tagid'] == 50]['value'].values   # tagid 50 = Pump P1 Running
    
    # KPI 1: Tank C RMSE from 50% setpoint
    setpoint = 50.0
    tracking_error = tank_c_level - setpoint
    rmse = np.sqrt(np.mean(tracking_error**2))
    
    # KPI 2: Pump P1 cycle frequency
    # Detect rising edges (pump starts)
    pump_starts = np.sum(np.diff(np.concatenate(([0], pump_p1_run))) > 0.5)
    runtime_hours = len(tank_c_level) / 3600  # Assuming 1-second sampling
    cycle_freq = pump_starts / runtime_hours
    
    # KPI 3: Alarm rate (level > 90% or < 10%)
    high_alarms = np.sum(tank_c_level > 90.0)
    low_alarms = np.sum(tank_c_level < 10.0)
    alarm_rate = (high_alarms + low_alarms) / runtime_hours
    
    # KPI 4: Historian record count (proxy for DB size)
    record_count = len(df)
    
    # KPI 5: Settling time to ±2% band
    # Find first index where level enters and remains in [48, 52] band
    in_band = np.abs(tank_c_level - setpoint) <= 2.0
    # Use convolution to find sustained entry (>5 minutes continuous)
    kernel = np.ones(300)  # 300 seconds = 5 minutes
    sustained = signal.convolve(in_band.astype(float), kernel, mode='same') >= 300
    if np.any(sustained):
        settling_idx = np.argmax(sustained)
        settling_time = settling_idx / 60.0  # Convert to minutes
    else:
        settling_time = np.inf  # Never settled
    
    return {
        'Run_ID': run_id,
        'RMSE_Level': rmse,
        'Pump_Cycles_per_Hour': cycle_freq,
        'Alarm_Rate_per_Hour': alarm_rate,
        'Historian_Records': record_count,
        'Settling_Time_min': settling_time
    }

# Process all runs
results = []
for csv_file in glob.glob("C:/DOE_Results/Run_*_data.csv"):
    run_id = csv_file.split('_')[1]
    kpis = calculate_kpis(run_id, csv_file)
    results.append(kpis)

df_results = pd.DataFrame(results)
df_results.to_csv('C:/DOE_Results/KPI_Summary.csv', index=False)
print(df_results.describe())
```

This script transforms raw time-series data into scalar metrics suitable for regression modeling and main effects plots. The settling time calculation employs a convolution-based approach to distinguish transient oscillations (briefly entering the band then exiting) from true steady-state convergence. Industrial process control engineers routinely compute similar metrics for loop performance assessment during commissioning audits and annual calibration verifications.

**Statistical Analysis and Pareto Ranking**

Merge the KPI results with the original run matrix to enable regression analysis correlating parameters with performance outcomes. Use Python's `statsmodels` library to fit linear regression models and identify significant factors:

```python
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Merge run matrix with KPI results
df_merged = pd.merge(df_runs, df_results, on='Run_ID')

# Fit regression model for RMSE (key performance metric)
model_rmse = ols('RMSE_Level ~ T_cycle_ms + Q_P1_Lpm + Q_demand_Lpm + LSH_C_pct + DB_hist_pct', 
                 data=df_merged).fit()
print(model_rmse.summary())

# Extract standardized coefficients for Pareto ranking
coefficients = model_rmse.params[1:]  # Exclude intercept
abs_coefficients = np.abs(coefficients)
pareto_rank = pd.DataFrame({
    'Parameter': coefficients.index,
    'Effect': coefficients.values,
    'Abs_Effect': abs_coefficients.values
}).sort_values('Abs_Effect', ascending=False)

print("\nPareto Ranking of Parameter Effects on RMSE:")
print(pareto_rank)

# Generate main effects plot
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
parameters = ['T_cycle_ms', 'Q_P1_Lpm', 'Q_demand_Lpm', 'LSH_C_pct', 'DB_hist_pct']

for i, param in enumerate(parameters):
    ax = axes[i // 3, i % 3]
    
    # Compute mean RMSE at low and high levels
    low_level = df_merged[df_merged[param] == param_ranges[param.replace('_ms', '').replace('_Lpm', '').replace('_pct', '')][0]]
    high_level = df_merged[df_merged[param] == param_ranges[param.replace('_ms', '').replace('_Lpm', '').replace('_pct', '')][1]]
    
    ax.plot([param_ranges[param.replace('_ms', '').replace('_Lpm', '').replace('_pct', '')][0], 
             param_ranges[param.replace('_ms', '').replace('_Lpm', '').replace('_pct', '')][1]], 
            [low_level['RMSE_Level'].mean(), high_level['RMSE_Level'].mean()], 
            marker='o', linewidth=2)
    ax.set_xlabel(param)
    ax.set_ylabel('Mean RMSE (%)')
    ax.set_title(f'Main Effect: {param}')
    ax.grid(True)

plt.tight_layout()
plt.savefig('C:/DOE_Results/Main_Effects_Plot.png', dpi=300)
plt.show()
```

The regression model quantifies how each parameter influences tracking performance. For example, the model might reveal that increasing `Q_P1_Lpm` from 120 to 180 L/min reduces RMSE by 1.2%, while increasing `T_cycle_ms` from 5 to 20 ms increases RMSE by 0.8%. The Pareto ranking identifies the vital few parameters dominating performance: the 80/20 rule typically manifests with two or three parameters explaining 80% of outcome variance. Practitioners prioritize tuning efforts on high-leverage parameters, ignoring low-impact factors that waste engineering time without measurable benefit.

Main effects plots visualize how response variables change across parameter ranges. A steep slope indicates high sensitivity requiring tight operational tolerances, while flat slopes suggest robustness to parameter variation. Industrial applications use these plots for specification development: if product quality remains acceptable across wide parameter bands, looser incoming material specifications reduce procurement costs without jeopardizing output.

**Interaction Effects and Response Surface Modeling**

Beyond main effects, two-factor interactions reveal non-additive parameter relationships where combined effects differ from summed individual effects. For instance, increasing both `Q_P1_Lpm` and `Q_demand_Lpm` simultaneously might produce disproportionately higher alarm rates than predicted by independent adjustments due to resonance between pump cycles and demand oscillations.

Generate interaction plots for the top two parameters identified by Pareto ranking:
```python
from mpl_toolkits.mplot3d import Axes3D

# Assume Q_P1_Lpm and Q_demand_Lpm are top two factors
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Create mesh grid for response surface
q_p1_range = np.linspace(120, 180, 20)
q_demand_range = np.linspace(60, 120, 20)
Q_P1, Q_demand = np.meshgrid(q_p1_range, q_demand_range)

# Predict RMSE using regression model (holding other factors at center point)
Z_rmse = np.zeros_like(Q_P1)
for i in range(Q_P1.shape[0]):
    for j in range(Q_P1.shape[1]):
        pred_data = pd.DataFrame({
            'T_cycle_ms': [10.0],
            'Q_P1_Lpm': [Q_P1[i, j]],
            'Q_demand_Lpm': [Q_demand[i, j]],
            'LSH_C_pct': [90.0],
            'DB_hist_pct': [1.0]
        })
        Z_rmse[i, j] = model_rmse.predict(pred_data)[0]

surf = ax.plot_surface(Q_P1, Q_demand, Z_rmse, cmap='viridis', alpha=0.8)
ax.set_xlabel('Pump P1 Flow (L/min)')
ax.set_ylabel('Process Demand (L/min)')
ax.set_zlabel('RMSE Level (%)')
ax.set_title('Response Surface: RMSE vs Flow Parameters')
fig.colorbar(surf, shrink=0.5)

plt.savefig('C:/DOE_Results/Response_Surface.png', dpi=300)
plt.show()
```

The response surface reveals optimal operating regions: valleys in the surface indicate parameter combinations minimizing RMSE, while ridges show conditions producing poor performance. For processes with multiple competing objectives (minimize RMSE while maximizing throughput and minimizing energy consumption), multi-objective optimization using Pareto frontiers identifies tradeoff boundaries where improving one metric necessarily degrades another.

**Operational Recommendations and Tuning Guidelines**

Synthesize the statistical analysis into actionable tuning recommendations documented in a commissioning report format:

**Parameter Optimization Summary for Three-Tank Cascade System**

*Objective*: Minimize Tank C level tracking error (RMSE) while maintaining alarm rate below 2 events/hour and pump cycle frequency below 6 cycles/hour (maintenance constraint).

*Key Findings*:
1. **Process Demand Setpoint (`Q_demand_Lpm`)** exhibits the strongest effect on RMSE (standardized coefficient β = 0.64, p < 0.001). Increasing demand from 60 to 120 L/min increases RMSE by 2.1%. Maintain demand setpoint at or below 90 L/min for nominal operation.

2. **Pump P1 Flow Rate (`Q_P1_Lpm`)** shows moderate negative effect (β = -0.38, p = 0.012). Higher P1 flow reduces RMSE by improving Tank B buffer capacity, but increases pump cycling frequency. Optimal setting: 165 L/min balances performance and maintenance cost.

3. **PLC Cycle Time (`T_cycle_ms`)** demonstrates minimal effect (β = 0.09, p = 0.421). Performance remains acceptable across 5-20 ms range. Recommend 10 ms for compatibility with standard industrial PLCs without unnecessary computational overhead.

4. **LSH Threshold (`LSH_C_pct`)** and **Historian Deadband (`DB_hist_pct`)** exhibit negligible main effects but significant interaction (β_interaction = -0.31, p = 0.023). Lowering LSH to 85% combined with increasing deadband to 2.0% reduces alarm rate by 40% with only 0.3% RMSE penalty—recommended for systems with high alarm fatigue.

*Optimized Parameter Set*:
- T_cycle_ms: 10.0 (unchanged from baseline)
- Q_P1_Lpm: 165.0 (+10% from baseline)
- Q_demand_Lpm: 85.0 (-5.6% from baseline)
- LSH_C_pct: 87.0 (-3% from baseline)
- DB_hist_pct: 1.5% (+50% from baseline)

*Predicted Performance*:
- RMSE: 1.8% (32% improvement vs baseline 2.65%)
- Alarm Rate: 1.2 events/hour (40% reduction vs baseline 2.0 events/hour)
- Pump Cycles: 5.1 cycles/hour (within maintenance target)
- Historian Storage: -22% records/day (database cost savings)

*Implementation Procedure*:
1. Schedule parameter update during planned maintenance window
2. Update PLC global variables via CODESYS download or HMI setpoint interface
3. Perform controlled restart per Exercise 1 reset procedure
4. Monitor for 48 hours, logging KPIs via Ignition historian
5. Compare actual performance against predicted values; if deviation >15%, re-run characterization subset

This format mirrors industry-standard commissioning documentation required for FDA validation protocols, ISO 9001 quality management audits, and warranty compliance. The quantitative predictions enable objective performance acceptance: if actual RMSE exceeds predicted value by statistical tolerance margins, troubleshooting focuses on implementation errors (incorrect parameter entry, sensor calibration drift) rather than control algorithm deficiencies.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

This exercise subjects the three-tank system to failure modes and degraded operating conditions encountered in industrial environments: communication network outages, sensor failures, actuator malfunctions, and emergency shutdown scenarios. Stress testing validates that control logic implements safe failure modes, prevents cascading equipment damage, and enables rapid recovery to normal operation. The methodology replicates factory acceptance test (FAT) protocols mandated by engineering standards like ISA-18.2 (Alarm Management) and ISA-84 (Safety Instrumented Systems), where systematic fault injection proves that protective interlocks function correctly under every credible failure scenario.

Industrial automation failures rarely result from single-point events; cascading failures propagate when protective layers fail sequentially. A pressure sensor drift triggers false high-pressure alarms, operators override the alarm to continue production, then a relief valve sticks closed, and actual pressure exceeds vessel ratings causing rupture. This exercise trains practitioners to identify protective layer interactions, quantify failure probabilities, and verify that multiple independent protection layers (MIPS) prevent single failures from escalating into catastrophic events.

**Failure Mode Catalog and Hazard Analysis**

Construct a Failure Modes and Effects Analysis (FMEA) table enumerating potential failures, their causes, effects on system operation, and designed safeguards. The FMEA methodology originates in aerospace engineering but applies universally to safety-critical automation systems. Each failure mode receives a Risk Priority Number (RPN) computed as RPN = Severity × Occurrence × Detection, where scores range 1-10 for each dimension. High RPN values (>200) mandate additional protective measures before system acceptance.

| Failure Mode | Cause | Effect | Safeguard | Severity (1-10) | Occurrence (1-10) | Detection (1-10) | RPN |
|--------------|-------|--------|-----------|-----------------|-------------------|------------------|-----|
| Tank C level sensor fails high (stuck at 95%) | Transmitter electronics failure, corroded wiring | PLC reads falsely high level, stops Pump P2 prematurely, Tank C depletes, process starves | Redundant sensor voting, rate-of-change validation | 7 (process disruption) | 3 (moderate, typical sensor MTBF ~100k hours) | 4 (detected by rate alarm within 2 min) | 84 |
| Pump P1 contactor welds closed | Contact arcing from inrush current, contamination | Pump P1 runs continuously regardless of PLC stop command, Tank B overflows, flood damage | Hardwired flow switch, independent safety relay monitoring contactor auxiliary contact | 9 (flood, equipment damage) | 2 (rare, contactor MTBF ~500k operations) | 3 (detected by flow/level discrepancy within 1 min) | 54 |
| SCADA-PLC communication failure | Ethernet switch failure, fiber cut, network congestion | Operator loses visibility, alarms not annunciated, blind operation | PLC operates autonomously, local alarm beacons, network heartbeat monitoring | 6 (reduced situational awareness) | 4 (occasional, network MTBF ~10k hours) | 2 (detected immediately by Ignition gateway connection status) | 48 |
| Simultaneous Tank A & B low level | Upstream supply interruption, supply pump failure | Both pumps interlock, Tank C starves, process shutdown | Supply pressure monitoring, upstream pump redundancy (N+1) | 8 (process shutdown, production loss) | 2 (rare, requires multiple upstream failures) | 2 (detected immediately by level switches) | 32 |
| Emergency stop button activation during high flow | Operator panic, accidental bump, maintenance testing | All pumps stop, may cause water hammer in piping, pressure transients | Soft-stop sequencing with ramp-down, pressure relief valves | 5 (pressure transient, within design limits) | 5 (frequent during testing/commissioning) | 1 (deliberate action, always detected) | 25 |

The FMEA table guides test scenario development by prioritizing high-RPN failure modes for empirical verification. Some failures (welded contactor) prove impractical to induce in laboratory simulation but receive special attention during physical commissioning. Software-simulatable failures (sensor faults, communication outages) constitute the focus of this exercise.

**Test Scenario 1: Level Sensor Hard Failure (Fail-Safe Validation)**

Simulate a Tank C level transmitter catastrophic failure by forcing the analog input to a constant value independent of actual tank level. In CODESYS, add a sensor health monitoring function block that compares the rate-of-change of level readings against physical plausibility limits. Water levels in closed vessels cannot change instantaneously; typical maximum rates equal pump flow divided by tank cross-sectional area. For Tank C with 3000L capacity and 2-meter diameter (3.14 m² area), maximum fill rate with P2 running equals (100 L/min) / (3140 L/m) = 0.0318 m/min = 1.91 m/hour ≈ 95% per hour for a 2m tall tank. Any rate exceeding 2%/second indicates sensor failure rather than physical level change.

Implement the sensor validation function block:
```text
FUNCTION_BLOCK FB_Sensor_Validator
VAR_INPUT
    Raw_Value      : REAL;      // Raw sensor reading [%]
    Enable         : BOOL;      // Validation enable
    Max_Rate       : REAL;      // Maximum plausible rate [%/sec]
END_VAR

VAR_OUTPUT
    Validated_Value : REAL;     // Output value (frozen if fault detected)
    Fault_Detected  : BOOL;     // TRUE if sensor failed validation
END_VAR

VAR
    Last_Value     : REAL;      // Previous cycle value
    Last_Valid     : REAL;      // Last known good value
    Cycle_Time     : REAL := 0.01;  // PLC cycle time [sec]
    Rate_Of_Change : REAL;
END_VAR

IF Enable THEN
    // Calculate rate of change
    Rate_Of_Change := ABS(Raw_Value - Last_Value) / Cycle_Time;
    
    // Check plausibility
    IF Rate_Of_Change > Max_Rate THEN
        Fault_Detected := TRUE;
        Validated_Value := Last_Valid;  // Freeze at last good value
    ELSE
        Fault_Detected := FALSE;
        Validated_Value := Raw_Value;
        Last_Valid := Raw_Value;
    END_IF
    
    Last_Value := Raw_Value;
ELSE
    Validated_Value := Raw_Value;  // Bypass validation when disabled
    Fault_Detected := FALSE;
END_IF
```

Integrate this function block into the main control program by replacing direct sensor reads with validated values. Add an alarm in the ladder logic:
```text
(* Rung: Tank C Sensor Fault Alarm *)
VAR
    Tank_C_Validator : FB_Sensor_Validator;
    Tank_C_Sensor_Fault_Alarm : BOOL;
END_VAR

Tank_C_Validator(
    Raw_Value := Sim.Tank_C_Level,
    Enable := TRUE,
    Max_Rate := 2.0
);

Tank_C_Sensor_Fault_Alarm := Tank_C_Validator.Fault_Detected;

// Use validated value for control decisions
Tank_C_Level_Pct := Tank_C_Validator.Validated_Value;
```

**Test Execution Procedure**:
1. Start system in normal operation with Tank C level stabilized at 50%
2. At T = 60 seconds, force `Sim.Tank_C_Level` to 95.0 in CODESYS Watch List (simulating sensor failure to high value)
3. Observe PLC response within one cycle time: `Tank_C_Sensor_Fault_Alarm` should activate
4. Verify Tank_C_Level_Pct freezes at 50% (last valid value before fault)
5. Confirm Pump P2 continues operating based on frozen value, preventing false interlock trip
6. Check SCADA alarm annunciation: "Tank C Level Sensor Fault" appears in alarm table with high priority
7. At T = 180 seconds, release the forced value, simulating sensor replacement
8. Observe fault clears within 10 seconds as new readings pass validation
9. Verify system resumes normal tracking without manual intervention

**Acceptance Criteria**:
- Sensor fault detection latency < 100 milliseconds (one PLC cycle)
- No false positive faults during normal operation (test with aggressive demand changes producing 1.5%/sec rates)
- Alarm annunciation delay < 500 milliseconds (SCADA poll cycle)
- Pump P2 maintains operation during fault (prevents cascading Tank C depletion)
- Automatic fault clearance when sensor recovers (no manual reset required)

Document results with timestamped screenshots showing alarm activation and PLC Watch List demonstrating frozen validated value. Industrial systems require these documented tests as evidence for insurance underwriting, regulatory compliance (EPA environmental permits often mandate sensor health monitoring), and liability protection during incident investigations.

**Test Scenario 2: Communication Network Failure (Autonomous Operation Verification)**

Simulate complete loss of Ethernet connectivity between the SCADA gateway and PLC by disabling the network interface or inserting a firewall rule blocking OPC UA traffic. The PLC must continue autonomous operation, executing interlocks and control logic without SCADA supervision. Operators lose visibility into process state but the physical system remains protected by local control logic. This scenario replicates fiber optic cable cuts, switch failures, and cyberattacks disrupting monitoring infrastructure.

**Pre-Test Configuration**:
Configure Ignition to log a "Communication Failure" alarm when the OPC UA connection enters disconnected state. Navigate to Gateway → Config → Alarm Notification → Pipelines, and create a new pipeline "Critical Infrastructure Alarms" with immediate email notifications sent to the commissioning engineer. Attach this pipeline to the CODESYS connection watchdog tag created in the gateway scope:
```python
# Project Library script "plc" (Ignition runs it as Jython; `system` is built in)
def connection_state():
    state = system.opc.getServerState("OPC UA Connection")  # e.g. "CONNECTED", "FAULTED"
    return "Connected" if state == "CONNECTED" else "Disconnected"
```

```text
# Gateway Tag: System/PLC_Connection_Status (Expression Tag)
# Expression (calls the library function every 5000 ms):
runScript("plc.connection_state()", 5000)

# Alarm Configuration:
# Tag: System/PLC_Connection_Status
# Alarm Name: PLC Communication Failure
# Alarm Setpoint: "Disconnected" (equality check)
# Priority: Critical
# Pipeline: Critical Infrastructure Alarms
```

**Test Execution Procedure**:
1. Start system in normal operation with all three tanks at 50% levels
2. Verify SCADA displays live updating tank levels and pump statuses (refresh rate ~1 second)
3. At T = 60 seconds, disconnect network by executing Windows command: `netsh interface set interface "Ethernet" admin=disable`
4. Observe Ignition Gateway connection status transition to "Disconnected" within 5 seconds (OPC UA keepalive timeout)
5. Verify SCADA displays freeze at last received values; tag qualities show "Bad: Device Not Connected"
6. Confirm alarm "PLC Communication Failure" activates and triggers email notification
7. Monitor PLC operation through CODESYS (which uses a separate communication channel): verify tank levels continue updating, pumps sequence according to interlocks, level switches operate correctly
8. Introduce disturbances: manually change `Process_Demand_Input` via CODESYS Watch List from 75 to 110 L/min
9. Verify PLC responds appropriately (increased P1/P2 activity) without SCADA connectivity
10. At T = 600 seconds, restore network: `netsh interface set interface "Ethernet" admin=enable`
11. Observe Ignition reconnection within 10 seconds, SCADA displays resynchronize to current PLC state
12. Verify no alarms generated during the disconnected period appear retroactively (historian gaps documented but not false alarms)
13. Check historian data integrity: confirm gap in trends from T=60 to T=600, no spurious data points

**Acceptance Criteria**:
- PLC continues uninterrupted operation during communication outage (zero process disruption)
- SCADA detects disconnection within one keepalive interval (5 seconds)
- Alarm notification delivered within 30 seconds of disconnection
- Upon reconnection, SCADA resynchronizes to actual PLC state without restart or manual intervention
- Historian accurately records gap with boundary timestamps (last good value before outage, first good value after restoration)
- No data corruption or false historical values recorded during outage

Measure communication recovery time using Wireshark packet captures. The reconnection sequence involves OPC UA session re-establishment (client requests new session ID), subscription recreation (client resubscribes to monitored items), and initial data transfer (server publishes current values). Typical recovery times range 2-8 seconds depending on subscription count and server load. Systems requiring faster recovery implement redundant network paths with automatic failover (< 1 second using protocols like Parallel Redundancy Protocol per IEC 62439-3).

**Test Scenario 3: Cascading Failure with Emergency Shutdown (Recovery Time Quantification)**

Simulate a worst-case scenario combining multiple simultaneous failures: Tank A supply depletion (simulating upstream pump failure), Pump P2 mechanical seizure (simulating bearing failure), and operator emergency stop activation. This compound failure tests whether the system degrades gracefully without escalating to catastrophic outcomes like Tank C overflow or dry-run pump damage.

**Test Execution Procedure**:
1. Start system in steady operation with Tank A at 30% (near low-level threshold)
2. Set process demand to 120 L/min (high load condition)
3. At T = 0, force Tank A level to decrease at accelerated rate by modifying simulation FB: `Tank_A_Volume := Tank_A_Volume - 500.0` (500L per cycle, approximately 5%/second depletion)
4. Observe Tank A reach LSL within 60 seconds
5. Verify Pump P1 interlock activates, stopping P1 immediately
6. Tank B begins depleting as P2 continues transferring to Tank C
7. At T = 120 seconds, force Pump P2 to stop by overriding its command despite PLC output energized: `Sim.Pump_P2_Command := FALSE` (simulating mechanical failure)
8. Tank B continues depleting from Tank C draw, Tank C level begins falling
9. At T = 180 seconds, activate emergency stop via SCADA button
10. Verify all pump commands de-energize, all process control outputs de-energize
11. Observe Tank C continue depleting from process demand (uncontrolled discharge simulating gravity-fed downstream equipment)
12. Tank C reaches LSL at approximately T = 360 seconds, triggering low-level alarm
13. Document system state: all tanks in alarm condition, all pumps stopped, emergency stop engaged

**Recovery Procedure**:
1. Reset emergency stop (simulate operator acknowledging fault and preparing restart)
2. Manually restore Tank A to 50% volume via CODESYS by editing `Sim.Tank_A_Volume := 5000.0`
3. Re-enable Pump P2 mechanical operation by releasing forced condition on `Sim.Pump_P2_Command`
4. Activate System Reset button in SCADA
5. Observe simulation reinitialize to default levels
6. Verify all alarms clear within 30 seconds as tanks return to normal ranges
7. Confirm pumps resume automatic sequencing without manual intervention
8. Measure time from reset activation to steady-state operation (Tank C at 50% ±2%): typical target < 15 minutes

**Quantitative Recovery Metrics**:
- **Emergency Response Time**: Time from initiating event (Tank A LSL) to emergency stop activation: 180 seconds
- **Process Shutdown Duration**: Time in emergency-stopped state before recovery initiation: variable (operator-dependent)
- **Restart Sequence Duration**: Time from reset activation to pumps running: < 10 seconds (demonstrates rapid recovery capability)
- **Return to Normal**: Time from reset to steady-state at setpoint: 840 seconds (14 minutes, acceptable for non-critical processes)
- **Alarm Flooding Duration**: Time with >5 active alarms: 180 seconds during cascading failure, 25 seconds during recovery (within ISA-18.2 acceptable limits of < 10 alarms per 10 minutes per operator)

**Data Collection for Post-Event Analysis**:
Export alarm journal and tag history covering the entire test sequence (T = -60 to T = 1200 seconds). Generate a timeline plot using Python matplotlib showing key events:
```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load historian data
df_historian = pd.read_csv('C:/Test_Results/Scenario3_historian.csv', parse_dates=['timestamp'])
df_alarms = pd.read_csv('C:/Test_Results/Scenario3_alarms.csv', parse_dates=['evt_eventtime'])

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# Plot tank levels
ax1.plot(df_historian['timestamp'], df_historian['Tank_A_Level'], label='Tank A', linewidth=2)
ax1.plot(df_historian['timestamp'], df_historian['Tank_B_Level'], label='Tank B', linewidth=2)
ax1.plot(df_historian['timestamp'], df_historian['Tank_C_Level'], label='Tank C', linewidth=2, color='red')
ax1.axhline(y=90, color='orange', linestyle='--', label='LSH Threshold')
ax1.axhline(y=10, color='purple', linestyle='--', label='LSL Threshold')
ax1.set_ylabel('Tank Level (%)')
ax1.set_title('Cascading Failure Test - Tank Levels')
ax1.legend()
ax1.grid(True)

# Plot pump status
ax2.plot(df_historian['timestamp'], df_historian['Pump_P1_Running']*100, label='Pump P1', linewidth=2, drawstyle='steps-post')
ax2.plot(df_historian['timestamp'], df_historian['Pump_P2_Running']*100, label='Pump P2', linewidth=2, drawstyle='steps-post')
ax2.set_ylabel('Pump Status (0=Off, 100=On)')
ax2.set_title('Pump Operation During Failure Sequence')
ax2.legend()
ax2.grid(True)

# Plot alarm events as vertical lines
for idx, row in df_alarms.iterrows():
    ax3.axvline(x=row['evt_eventtime'], color='red', alpha=0.5, linewidth=1)
    ax3.text(row['evt_eventtime'], idx, row['displaypath'], rotation=90, fontsize=8)
ax3.set_ylabel('Alarm Events')
ax3.set_xlabel('Time')
ax3.set_title('Alarm Chronology')
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

plt.tight_layout()
plt.savefig('C:/Test_Results/Scenario3_Timeline.png', dpi=300)
plt.show()
```

This timeline visualization serves multiple purposes: engineering review during commissioning to validate interlock timing, operator training to build mental models of failure propagation, and regulatory documentation for safety case development. The plot should clearly show Tank A depletion preceding Pump P1 trip, Tank B depletion preceding Pump P2 trip, and Tank C depletion continuing until emergency stop, followed by recovery sequence restoring normal levels.

**Failure Propagation Analysis**:
Calculate the time constants governing cascading failures by modeling the system as coupled differential equations. Tank B depletion rate after P1 stops equals `dV_B/dt = -Q_P2` (assuming constant P2 flow and zero inflow). Time to deplete from 50% to LSL (10%) equals:
```text
t_deplete = (0.50 - 0.10) × V_B_capacity / Q_P2
t_deplete = 0.40 × 5000 L / 100 L/min = 20 minutes
```

This calculation quantifies the time buffer available for corrective action before secondary failures occur. Industrial operators use these time constants for alarm prioritization: failures with short time horizons (< 5 minutes to catastrophic outcome) receive highest priority and immediate automatic responses, while slower failures (>30 minutes) permit operator assessment and manual intervention.

**Test Scenario 4: Partial Sensor Failure with Voting Logic (Redundancy Validation)**

Extend the system with triple-redundant level sensors on Tank C, implementing 2-out-of-3 (2oo3) voting logic to tolerate single sensor failures without false trips. Industrial safety systems (Safety Instrumented Systems, SIS) per IEC 61511 mandate redundant sensors for high-consequence protection functions. This test validates that voting logic correctly handles sensor failures, providing continuous protection while alerting operators to degraded redundancy.

**Sensor Redundancy Implementation**:
Modify `FB_Tank_Simulation` to output three independent sensor readings with injected random noise and calibration offsets:
```text
VAR_OUTPUT
    Tank_C_Level_Sensor_A : REAL;
    Tank_C_Level_Sensor_B : REAL;
    Tank_C_Level_Sensor_C : REAL;
END_VAR

VAR
    Noise_Generator : DRAND;  // Pseudo-random number generator
    Calibration_Offset_A : REAL := 0.5;   // +0.5% offset
    Calibration_Offset_B : REAL := -0.3;  // -0.3% offset
    Calibration_Offset_C : REAL := 0.1;   // +0.1% offset
END_VAR

// Generate noise and offsets for realistic sensor simulation
Noise_Generator(SEED := UDINT_TO_REAL(CURRENT_TIME));
Tank_C_Level_Sensor_A := Tank_C_Level + Calibration_Offset_A + (Noise_Generator.Num - 0.5) * 0.4;
Tank_C_Level_Sensor_B := Tank_C_Level + Calibration_Offset_B + (Noise_Generator.Num - 0.5) * 0.4;
Tank_C_Level_Sensor_C := Tank_C_Level + Calibration_Offset_C + (Noise_Generator.Num - 0.5) * 0.4;
```

Implement the 2oo3 voting logic function block:
```text
FUNCTION_BLOCK FB_2oo3_Voter
VAR_INPUT
    Sensor_A : REAL;
    Sensor_B : REAL;
    Sensor_C : REAL;
    Voting_Tolerance : REAL := 2.0;  // Sensors within ±2% considered agreeing
END_VAR

VAR_OUTPUT
    Voted_Value : REAL;
    Sensor_A_Fault : BOOL;
    Sensor_B_Fault : BOOL;
    Sensor_C_Fault : BOOL;
    Degraded_Mode : BOOL;  // TRUE if one sensor failed
END_VAR

VAR
    AB_Agree : BOOL;
    AC_Agree : BOOL;
    BC_Agree : BOOL;
    Fault_Count : INT;
END_VAR

// Determine agreement between sensor pairs
AB_Agree := ABS(Sensor_A - Sensor_B) <= Voting_Tolerance;
AC_Agree := ABS(Sensor_A - Sensor_C) <= Voting_Tolerance;
BC_Agree := ABS(Sensor_B - Sensor_C) <= Voting_Tolerance;

// Voting logic: use median or average of agreeing sensors
IF AB_Agree AND AC_Agree THEN
    // All three agree, use average
    Voted_Value := (Sensor_A + Sensor_B + Sensor_C) / 3.0;
    Sensor_A_Fault := FALSE;
    Sensor_B_Fault := FALSE;
    Sensor_C_Fault := FALSE;
    Degraded_Mode := FALSE;
ELSIF AB_Agree THEN
    // A and B agree, C is outlier
    Voted_Value := (Sensor_A + Sensor_B) / 2.0;
    Sensor_A_Fault := FALSE;
    Sensor_B_Fault := FALSE;
    Sensor_C_Fault := TRUE;
    Degraded_Mode := TRUE;
ELSIF AC_Agree THEN
    // A and C agree, B is outlier
    Voted_Value := (Sensor_A + Sensor_C) / 2.0;
    Sensor_A_Fault := FALSE;
    Sensor_B_Fault := TRUE;
    Sensor_C_Fault := FALSE;
    Degraded_Mode := TRUE;
ELSIF BC_Agree THEN
    // B and C agree, A is outlier
    Voted_Value := (Sensor_B + Sensor_C) / 2.0;
    Sensor_A_Fault := TRUE;
    Sensor_B_Fault := FALSE;
    Sensor_C_Fault := FALSE;
    Degraded_Mode := TRUE;
ELSE
    // No agreement between any pair: total failure, use last good value or trip
    Voted_Value := 0.0;  // Or implement more sophisticated failure mode
    Sensor_A_Fault := TRUE;
    Sensor_B_Fault := TRUE;
    Sensor_C_Fault := TRUE;
    Degraded_Mode := TRUE;
END_IF

// Count faults for diagnostic purposes
Fault_Count := TO_INT(Sensor_A_Fault) + TO_INT(Sensor_B_Fault) + TO_INT(Sensor_C_Fault);
```

**Test Execution Procedure**:
1. Start system with all three sensors operating normally
2. Verify voted value equals average of three sensors (within ±0.5% due to noise)
3. At T = 60 seconds, force Sensor_B to fail high: set `Sim.Tank_C_Level_Sensor_B := 95.0`
4. Observe voting logic within one cycle: Sensor_B_Fault flag activates, Degraded_Mode TRUE
5. Verify voted value now equals average of Sensor_A and Sensor_C only
6. Confirm control logic continues normal operation using voted value (no false interlock trips)
7. Check SCADA displays "Tank C Sensor B Fault - System Operating in Degraded Mode" alarm
8. At T = 180 seconds, force Sensor_C to also fail: set `Sim.Tank_C_Level_Sensor_C := 10.0`
9. Observe voting logic detect no agreeing pair
10. Verify system enters safe state: Pump P2 stops (fail-safe mode), critical alarm annunciates "Multiple Tank C Sensor Failure - Manual Intervention Required"
11. At T = 240 seconds, restore both sensors by releasing forced values
12. Observe automatic recovery: fault flags clear, degraded mode deactivates, voted value resynchronizes
13. Verify Pump P2 automatically restarts per normal sequencing logic

**Acceptance Criteria**:
- Single sensor failure tolerated with continuous operation and < 10ms voting latency
- Voted value accuracy within ±1.0% of true level during single-sensor fault
- Degraded mode alarm generates operator notification within 1 second
- Double sensor failure triggers fail-safe shutdown within 100ms
- Automatic recovery when sensors restored (no manual reset required for single fault, manual review required for double fault per safety protocols)

Document the voting statistics by logging the voted value, individual sensor values, and fault flags at 100ms resolution during the test. Post-test analysis computes voting latency (time from sensor deviation exceeding tolerance to fault flag activation) and false positive rate (spurious fault detections due to transient noise). Industrial systems target voting latencies < 50ms and false positive rates < 0.1% (fewer than one spurious fault per 1000 operating hours).

## Operational Reference Guide & Diagnostic Checklist

This section consolidates troubleshooting procedures, diagnostic workflows, and operational best practices for PLC/SCADA systems derived from the preceding exercises. Practitioners reference this guide during commissioning, routine maintenance, and emergency troubleshooting to systematically diagnose issues ranging from simple configuration errors to complex timing interactions.

**Pre-Commissioning Verification Checklist**

Execute this checklist before energizing any PLC or SCADA system in a production environment. Each item requires documented verification and sign-off by the responsible engineer.

**Electrical and Hardware Verification**:
- [ ] All field wiring terminated per approved loop diagrams with wire labels matching P&ID tag numbers
- [ ] Continuity tests passed on all I/O circuits (24VDC inputs show open-circuit voltage, outputs show relay coil resistance)
- [ ] Grounding verified: PLC chassis bonded to facility ground grid with < 1Ω resistance
- [ ] Power supply loading: I/O modules draw < 80% of supply rated current (measure with clamp ammeter)
- [ ] Network infrastructure: Ethernet switches configured for IGMP snooping to prevent multicast flooding, spanning tree protocol disabled on industrial VLANs (deterministic latency requirement)
- [ ] Physical security: PLC enclosure locked with tamper-evident seals, network switch accessible only to authorized personnel

**Software Configuration Verification**:
- [ ] PLC firmware version matches Bill of Materials specification (vendor-recommended version for target hardware)
- [ ] Task configuration: cycle time set per design specification, watchdog timer enabled with 200% of maximum cycle time
- [ ] I/O module addressing matches hardware installation (compare CODESYS I/O mapping to field installation photos)
- [ ] Safety logic verified: emergency stop circuits hardwired, independent of PLC (relay logic failsafe)
- [ ] SCADA tag definitions imported from PLC symbol table (no manual transcription errors)
- [ ] Alarm deadbands configured per ISA-18.2: ±2% for level, ±5% for flow, ±1% for temperature to prevent chattering
- [ ] Historian retention policy: high-frequency tags (analog levels) sampled on change with 0.5% deadband, low-frequency tags (pump statuses) sampled on change with 1-second minimum interval, archive retention 1 year for regulatory compliance

**Functional Testing Verification**:
- [ ] Execute Exercise 1 baseline test: system achieves steady-state operation at 50% Tank C level within 15 minutes
- [ ] Execute interlock tests per Exercise 3: all high/low level interlocks trip within 100ms of threshold
- [ ] Emergency stop response time: all outputs de-energize within 50ms (measure with oscilloscope on output terminals)
- [ ] Communication recovery: SCADA reconnects to PLC within 10 seconds after network cable disconnect/reconnect
- [ ] Historian data integrity: export 24 hours of tag history, verify no duplicate timestamps or out-of-order records (sort by timestamp, compare adjacent rows)
- [ ] Alarm response: generate test alarm (force Tank C level to 92%), verify annunciation on SCADA HMI, confirm alarm email delivered to designated recipients, measure total latency < 5 seconds

**Common Diagnostic Procedures**

**Symptom: PLC shows "Cycle Time Overrun" error**

Root Causes:
1. Program complexity exceeds available cycle time (WCET > configured cycle time)
2. Communication tasks consuming excessive CPU time (OPC UA server handling many subscriptions)
3. Infinite loop or blocking function call in user code

Diagnostic Steps:
1. Open CODESYS Task Configuration, observe "Actual Cycle Time" metric: if consistently >90% of configured cycle time, overrun imminent
2. Enable task execution profiling: Tools → Task Monitor, identify POUs with highest execution time
3. Review recent code changes: look for nested loops without exit conditions, blocking serial communication (RS232 read without timeout)
4. Measure OPC UA subscription count: Config → OPC UA → Current Sessions, if >500 monitored items, consider reducing SCADA poll rate or distributing across multiple PLCs

Resolution Strategies:
- Increase cycle time (e.g., 10ms to 20ms) if application tolerates higher latency
- Offload communication to separate lower-priority task: create "Communication" task at 100ms, move OPC UA to this task, keep control logic at 10ms
- Optimize code: replace multiple IF-THEN statements with CASE structure (faster opcode), move complex calculations to periodic background task
- Disable unused diagnostic features: symbol tables consume scan time even if not accessed

**Symptom: SCADA displays show intermittent "Bad Quality" on tags**

Root Causes:
1. Network packet loss due to congestion or marginal Ethernet cable
2. OPC UA subscription rate faster than PLC can publish (backlog builds up)
3. Tag definitions reference non-existent PLC variables (typo in symbol name)

Diagnostic Steps:
1. Check Ignition gateway status: Config → Status → Connections, observe "Comm Errors" counter
2. Capture network traffic with Wireshark: filter `opcua`, analyze "Publish Response" packets for dropped sequence numbers
3. Measure network latency: `ping 127.0.0.1 -t` if local, or `ping <PLC_IP>` if remote, verify < 10ms average, < 50ms maximum
4. Verify tag paths: Config → Tags, browse PLC_Tags provider, compare tag OPC Node Path against CODESYS symbol configuration

Resolution Strategies:
- Reduce SCADA poll rate: increase default scan class from 1000ms to 2000ms for non-critical tags
- Replace Ethernet cable if latency spikes observed: industrial CAT5e rated for motion applications, test with cable tester for split pairs or excessive crosstalk
- Increase OPC UA queue size: edit `OpcUaServer.xml`, set `<MaxQueueSize>` to 10000 (default 1000), restart PLC service
- Implement tag value caching in SCADA: configure Ignition to hold last good value for 5 seconds before displaying "Bad Quality"

**Symptom: Pumps fail to start despite PLC output energized**

Root Causes:
1. Motor starter contactor coil failed or control power fuse blown
2. Overload relay tripped due to motor overcurrent
3. Permissive interlock open (external safety relay, local hand/off/auto switch in "Off")
4. Control voltage insufficient (measure < 18VDC on 24VDC system indicates power supply overload or high resistance connection)

Diagnostic Steps:
1. Measure voltage at PLC output terminals: should read 24VDC when output command active
2. If voltage present at PLC, trace circuit to motor starter: measure voltage at contactor coil terminals
3. Check auxiliary contacts on motor starter: measure continuity of "Run" feedback contact to PLC input
4. Observe current draw with clamp ammeter: motor running at rated current (e.g., 5A for 1HP pump) indicates mechanical load, zero current indicates electrical open circuit

Resolution Strategies:
- Replace blown fuse or reset tripped overload relay: investigate root cause of overcurrent (bearing seizure, fluid viscosity higher than design)
- Bypass external interlocks temporarily (WITH SAFETY PRECAUTIONS) to isolate cause: if pump starts, trace open interlock circuit
- Measure voltage drop across long cable runs: if >2V drop, upgrade wire gauge or add local power supply
- Verify control logic: use CODESYS online view to force output TRUE, observe field device response in real-time

**Symptom: Historian shows unexpected gaps in trend data**

Root Causes:
1. PLC was in "Stop" mode during gap period (no data published to OPC UA server)
2. Network disconnection between SCADA and PLC
3. Ignition gateway database full or locked (SQLite file size limit 2GB, SQL Server disk space exhausted)
4. Historian deadband too large, suppressing small process changes

Diagnostic Steps:
1. Query alarm journal for communication alarms during gap period: `SELECT * FROM alarm_events WHERE evt_eventtime BETWEEN <start> AND <end>`
2. Check gateway logs: Config → Status → Logs, filter by "SQLBridge" component, look for "Failed to insert historical data" errors
3. Measure database size: navigate to historian database file location, check file size against configured retention policies
4. Review tag historian configuration: verify sample mode set to "On Change by Value" with reasonable deadband (0.5-1.0% for analog, all changes for digital)

Resolution Strategies:
- Implement database partitioning: split historian tables by year/month, archive old partitions to separate storage
- Increase database disk allocation: for SQL Server, expand MDF file maximum size, add secondary data files on separate disks
- Adjust deadband for critical tags: reduce to 0.1% for precise trending, increase to 2.0% for non-critical tags to reduce storage
- Configure cold storage: export trends older than 90 days to CSV files for long-term archival, delete from active database

**Performance Benchmarking Metrics**

Industrial automation systems should meet the following quantitative performance targets. Measure these metrics during commissioning and quarterly maintenance to identify degradation trends before failures occur.

| Metric | Target | Measurement Method | Acceptance Criteria |
|--------|--------|-------------------|---------------------|
| PLC Cycle Time Utilization | < 70% | CODESYS Task Monitor | Consistent < 80%, peaks < 90% |
| SCADA-PLC Communication Latency | < 100ms | Wireshark round-trip time | Mean < 50ms, 95th percentile < 200ms |
| Alarm Rate | < 6 alarms/hour/operator | Ignition alarm journal query | Per ISA-18.2: < 10/10min, < 1/10min standing alarms |
| Tag Quality Percentage | >99.5% | Tag historian quality statistics | "Good" quality >99.5% uptime, < 0.5% "Bad" samples |
| Historian Write Throughput | >1000 samples/sec | Database I/O statistics | No write queue backlog >10 seconds |
| HMI Screen Refresh Rate | >1 Hz | Browser performance profiler | All screens update < 2 seconds |
| Backup Completion Time | < 15 minutes | Gateway backup duration log | Full gateway backup completes < 30 minutes |

Establish baseline measurements during commissioning and trending plots tracking metrics over time. Gradual degradation (e.g., PLC cycle time increasing from 55% to 75% over six months) indicates pending issues like firmware bugs triggering memory leaks, accumulated diagnostic logs consuming flash memory, or hardware component aging. Proactive replacement before failure prevents unplanned downtime during critical production periods.

**Emergency Response Procedures**

**Scenario: Complete SCADA Failure (Server Hardware Fault)**

Immediate Actions:
1. Verify PLC continues autonomous operation: check local indicator LEDs on PLC rack (Run/Stop status)
2. Notify operations management: estimate duration of reduced monitoring capability
3. Station operator at PLC rack with laptop running CODESYS to monitor critical tags

Short-Term Mitigation (First Hour):
1. Deploy backup laptop with Ignition Edge (lightweight SCADA runtime) connecting to PLC OPC UA server
2. Create minimal HMI view displaying only safety-critical tags: Tank C level, Pump run statuses, emergency stop status
3. Export recent alarm journal from failed server's database (if accessible) for continuity

Long-Term Recovery (Within 24 Hours):
1. Restore Ignition gateway from most recent `.gwbk` backup file to replacement server hardware
2. Verify database connectivity: test SQL connection strings, restore historian tables from backup
3. Execute post-restore verification: compare tag values to PLC state, ensure no configuration drift
4. Resume normal operations after 4-hour monitoring period confirming stable SCADA performance

**Scenario: PLC Crash or Unresponsive (Watchdog Timer Expiration)**

Immediate Actions:
1. Activate manual control: switch motor starters to "Hand" position, operate pumps manually to maintain critical process levels
2. Document PLC state before power cycle: photograph indicator LEDs, note any diagnostic codes on display

Recovery Procedure:
1. Power cycle PLC: disconnect 24VDC power for 10 seconds, reconnect
2. If PLC fails to restart, download application from CODESYS project backup: File → Open → <Project_Backup> → Login → Download
3. Verify PLC memory integrity: check battery voltage on processor module (should be >2.8VDC), replace battery if low
4. Compare current PLC state to expected state: check all tag values match physical field conditions (e.g., if Tank C is physically at 50%, PLC variable should read ~50%)

Post-Incident Analysis:
1. Extract diagnostic buffer from PLC: CODESYS Tools → Log, export system event log
2. Identify root cause: look for patterns preceding crash (memory errors, illegal instruction exceptions, watchdog expirations)
3. Contact PLC vendor support: provide diagnostic logs, firmware version, application complexity metrics
4. Implement corrective action: firmware upgrade, code optimization, hardware replacement per vendor recommendation

This laboratory manual provides practitioners with comprehensive verification skills for PLC/SCADA systems spanning foundational implementation, empirical tuning, and failure recovery protocols. The exercises balance theoretical rigor with practical execution, preparing engineers for industrial commissioning projects where safety, reliability, and regulatory compliance demand systematic verification methodologies grounded in quantitative analysis and documented procedures.
