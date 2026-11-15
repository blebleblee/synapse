# Operational Verification Labs: Fpga

## Objective & Operational Lab Setup

Field-Programmable Gate Arrays represent reconfigurable digital logic hardware that bridges the gap between application-specific integrated circuits and general-purpose microprocessors. Unlike software executing on a von Neumann architecture with sequential instruction fetch and decode, FPGA designs instantiate parallel datapaths, finite state machines, and custom arithmetic units directly in silicon fabric. The operational verification methodology for FPGA development demands a rigorous discipline combining hardware description language synthesis, static timing analysis, behavioral simulation, and in-circuit validation with logic analyzers and oscilloscopes.

This laboratory guide establishes a practitioner-first workflow grounded in the Xilinx Vivado Design Suite targeting the Artix-7 FPGA family, specifically the XC7A35T device commonly found on the Basys3 development board. The Artix-7 architecture provides 33,280 logic cells organized into Configurable Logic Blocks (CLBs) containing six-input Look-Up Tables (LUTs) and flip-flops, 1,800 Kbit of Block RAM, 90 DSP48E1 slices for arithmetic operations, and 210 user I/O pins. The verification exercises progress from combinatorial logic synthesis through synchronous finite state machine implementation, culminating in high-speed serial protocol validation where setup and hold time violations manifest as real-world bit errors.

The laboratory bench requires specific hardware instrumentation and software toolchains. Procure a Digilent Basys3 board with integrated 100 MHz crystal oscillator, sixteen slide switches, sixteen LEDs, seven-segment displays, and USB-JTAG programming interface. Acquire a Rigol DS1054Z oscilloscope with 50 MHz bandwidth and four analog channels for observing clock signals and propagation delays. Install Xilinx Vivado Design Suite 2023.2 with the free WebPACK license supporting Artix-7 devices. Configure the Ubuntu 22.04 LTS host environment with USB-JTAG cable drivers via the Vivado installation script located at `/opt/Xilinx/Vivado/2023.2/data/xicom/cable_drivers/lin64/install_script/install_drivers/install_drivers`. Execute the driver installation with root privileges and verify successful enumeration of the Digilent USB Device in `dmesg` output showing vendor ID `0x0403` and product ID `0x6010` for the FTDI FT2232H dual-channel USB-to-serial bridge.

Establish a project directory structure separating HDL source files, constraint files, simulation testbenches, and synthesis outputs. Create the hierarchy `/fpga_labs/exercise_01_combinatorial/`, `/fpga_labs/exercise_02_sequential/`, and `/fpga_labs/exercise_03_timing/` with subdirectories `rtl/`, `sim/`, `constraints/`, and `reports/` within each exercise folder. The constraint files employ Xilinx Design Constraints (XDC) syntax derived from Synopsys Design Constraints (SDC) with FPGA-specific extensions for pin assignments, voltage standards, and clock domain definitions. The RTL design language will alternate between Verilog-2001 and VHDL-2008 to expose practitioners to both dominant industry syntaxes, recognizing that Verilog's C-like procedural blocks contrast sharply with VHDL's strongly-typed entity-architecture separation.

Power the Basys3 board via the USB micro-B connector providing 5V at 500mA through the host computer interface. The onboard voltage regulators generate 3.3V VCC for I/O banks and 1.0V VCCINT for core logic. Verify correct power sequencing by observing the green POWER LED illumination and measuring voltage rails with a multimeter at test points adjacent to the FPGA package. Configure Vivado to target the exact device part number `xc7a35tcpg236-1` where the speed grade `-1` indicates nominal propagation delay specifications. The CPG236 package denotes the 236-ball Chip-Scale Ball Grid Array with 0.8mm ball pitch requiring careful constraint file correlation between schematic net names and physical ball locations documented in the Basys3 reference manual.

The verification workflow implements a four-stage methodology: behavioral simulation with ModelSim or Vivado XSIM, RTL synthesis producing a netlist of LUTs and flip-flops, implementation performing placement and routing within CLB matrix, and bitstream generation encoding configuration memory for the FPGA fabric. Each stage introduces potential failure modes ranging from syntax errors during elaboration to catastrophic timing violations post-route. The practitioner must internalize the distinction between logical correctness verified through simulation and physical realizability validated through static timing analysis. A design passing simulation may fail implementation if combinatorial path delays exceed clock period constraints or if routing congestion prevents legal wire placement between CLB sites.

## Exercise 1: Foundational Practical Implementation

The first laboratory exercise constructs a four-bit binary counter with synchronous reset and enable control driving the Basys3 onboard LEDs. This design establishes fundamental competencies in clocked sequential logic, constraint file syntax for pin mapping, and synthesis optimization trade-offs between area and speed. The counter architecture instantiates four D flip-flops clocked by the 100 MHz system oscillator with combinatorial increment logic feeding the flip-flop inputs. The synchronous reset signal connected to the center BTNC pushbutton forces all counter bits to zero on the rising clock edge when asserted, while the enable input gated by switch SW0 freezes the counter state when deasserted.

Navigate to the exercise directory `/fpga_labs/exercise_01_combinatorial/rtl/` and create the Verilog source file `counter_4bit.v` containing the following complete module definition. The code employs non-blocking assignments within the always block triggered by `posedge clk` to ensure correct flip-flop inference during synthesis. The reset signal uses an asynchronous active-high assertion model matching the pushbutton electrical characteristics where mechanical closure pulls the signal to VCCIO through a 10kΩ pull-up resistor.

```verilog
module counter_4bit (
    input wire clk,
    input wire rst,
    input wire enable,
    output reg [3:0] count
);

    always @(posedge clk) begin
        if (rst) begin
            count <= 4'b0000;
        end else if (enable) begin
            count <= count + 4'b0001;
        end
    end

endmodule
```

The module declaration establishes a clear interface boundary with three input ports and one output register. The `reg` type for the `count` output indicates that this signal is assigned within a procedural always block and will synthesize to flip-flop storage elements. The 4-bit width specified by `[3:0]` creates a bus representing bits 0 through 3 in little-endian convention where bit 0 is the least significant position. The addition operation `count + 4'b0001` instantiates a four-bit ripple-carry adder during synthesis with carry propagation through each bit position.

Proceed to the constraints directory `/fpga_labs/exercise_01_combinatorial/constraints/` and create the XDC file `basys3_counter.xdc` mapping logical port names to physical FPGA pins. The constraint syntax follows the Tcl command structure where `get_ports` returns a port object and `set_property` assigns attributes to that object. The IOSTANDARD property specifies the electrical signaling standard as LVCMOS33 representing Low-Voltage CMOS at 3.3V logic levels. The PACKAGE_PIN property correlates to the ball identifier from the CPG236 package pinout diagram in the Basys3 schematic.

```tcl
# Clock constraint - 100 MHz system oscillator
set_property -dict { PACKAGE_PIN W5 IOSTANDARD LVCMOS33 } [get_ports clk]
create_clock -period 10.000 -name sys_clk_pin -waveform {0.000 5.000} [get_ports clk]

# Reset button - BTNC center pushbutton
set_property -dict { PACKAGE_PIN U18 IOSTANDARD LVCMOS33 } [get_ports rst]

# Enable switch - SW0
set_property -dict { PACKAGE_PIN V17 IOSTANDARD LVCMOS33 } [get_ports enable]

# Counter output LEDs - LD3, LD2, LD1, LD0
set_property -dict { PACKAGE_PIN U16 IOSTANDARD LVCMOS33 } [get_ports {count[0]}]
set_property -dict { PACKAGE_PIN E19 IOSTANDARD LVCMOS33 } [get_ports {count[1]}]
set_property -dict { PACKAGE_PIN U19 IOSTANDARD LVCMOS33 } [get_ports {count[2]}]
set_property -dict { PACKAGE_PIN V19 IOSTANDARD LVCMOS33 } [get_ports {count[3]}]
```

The `create_clock` constraint defines the 100 MHz input clock with 10 nanosecond period and 50% duty cycle specified by the waveform rising edge at 0ns and falling edge at 5ns. This timing constraint propagates through the synthesis and implementation tools to calculate setup and hold margins at every flip-flop in the design. The constraint database uses this clock definition to verify that combinatorial logic delays between sequential elements remain below the 10ns budget minus setup time requirements.

Launch Vivado from the terminal by executing `vivado &` and create a new RTL project targeting the `xc7a35tcpg236-1` device. Add the `counter_4bit.v` source file and the `basys3_counter.xdc` constraint file to the project hierarchy. In the Flow Navigator panel, execute the RTL Analysis step by clicking "Open Elaborated Design" which parses the Verilog syntax, resolves module hierarchy, and generates a schematic representation showing four flip-flops with feedback paths through the increment logic. The elaborated design view does not yet represent physical FPGA resources but rather the logical netlist prior to technology mapping.

Execute synthesis by clicking "Run Synthesis" in the Flow Navigator. The synthesis engine performs multiple optimization passes including constant propagation, dead code elimination, resource sharing, and finite state machine encoding. Monitor the synthesis log file in `runs/synth_1/runme.log` for warning messages indicating unconnected ports, multi-driven nets, or inferred latches from incomplete conditional assignments. The synthesis report accessible via "Open Synthesized Design" provides resource utilization statistics showing four flip-flops instantiated as FDRE primitives (D flip-flop with clock enable and synchronous reset) and combinatorial LUT consumption for the four-bit adder.

Examine the synthesized schematic by selecting Windows → Schematic from the menu bar. The schematic viewer displays the netlist as FPGA primitive components including LUT2 and LUT4 instances implementing the addition logic. Trace the signal path from the `count[0]` flip-flop output through the LUT chain to the `count[3]` flip-flop input. The carry propagation creates a critical path where the worst-case delay depends on the sum of LUT propagation delays and routing wire capacitance. The synthesized design still resides in an abstract netlist representation without physical coordinates in the FPGA fabric.

Proceed to implementation by clicking "Run Implementation" which executes placement, routing, and design rule checking in sequence. The placement algorithm assigns each flip-flop and LUT to a specific CLB site within the Artix-7 fabric using simulated annealing or analytical techniques to minimize wire length and timing violations. The routing phase connects the placed cells using the programmable interconnect matrix consisting of switch boxes and connection blocks with configurable pass transistors. Open the implemented design and select Tools → Timing → Report Timing Summary to generate a detailed timing report showing setup and hold slack values for every path endpoint.

The timing report organizes results by clock domain with the `sys_clk_pin` domain containing all register-to-register paths clocked at 100 MHz. Locate the worst negative slack (WNS) metric indicating the minimum timing margin across all setup checks. A positive WNS value confirms that all combinatorial delays remain below the clock period constraint with margin. A negative WNS indicates timing failure requiring redesign or constraint relaxation. Expand the detailed path report to examine each net segment delay including logic delay through LUTs, net delay through routing wires, and clock uncertainty from jitter and skew.

Generate the bitstream by clicking "Generate Bitstream" which invokes the Xilinx bitgen tool to produce the binary configuration file `counter_4bit.bit` encoding LUT contents, flip-flop initial states, and interconnect switch settings. Connect the Basys3 board via USB and open the Hardware Manager in Vivado. Click "Open Target" and "Auto Connect" to establish JTAG communication with the FPGA. The JTAG chain scan should detect a single device with IDCODE `0x0362D093` corresponding to the XC7A35T. Right-click the device and select "Program Device" specifying the bitstream file path.

Upon successful programming, the FPGA configuration loads into SRAM within 50 milliseconds and the DONE LED illuminates green. The four counter bits drive the onboard LEDs creating a binary count sequence visible to the naked eye after dividing the 100 MHz clock frequency. The counter increments at 100 million counts per second but rolls over every 16 counts in 160 nanoseconds, far exceeding human perception. To observe the count sequence, modify the design to include a clock divider reducing the effective count rate to approximately 1 Hz. Insert the following prescaler module instantiation in the top-level design:

```verilog
module counter_4bit_visible (
    input wire clk,
    input wire rst,
    input wire enable,
    output reg [3:0] count
);

    reg [26:0] prescaler;
    wire clk_1hz;

    always @(posedge clk) begin
        if (rst) begin
            prescaler <= 27'd0;
        end else begin
            prescaler <= prescaler + 27'd1;
        end
    end

    assign clk_1hz = prescaler[26];

    always @(posedge clk_1hz) begin
        if (rst) begin
            count <= 4'b0000;
        end else if (enable) begin
            count <= count + 4'b0001;
        end
    end

endmodule
```

The prescaler accumulator implements a 27-bit counter exploiting the property that a binary counter's most significant bit toggles at half the rollover frequency. A 27-bit counter clocked at 100 MHz rolls over every 2^27 clock cycles requiring 134.2 milliseconds, producing a 26th bit toggle rate of 0.746 Hz approximating one count per second. Resynthesize, implement, and program this modified design to observe the LED count sequence advancing at a human-perceptible rate. Verify correct operation by asserting the reset button to zero all LEDs and toggling the enable switch to freeze the count state.

Measure the actual clock frequency using the oscilloscope by probing the CLK input at FPGA pin W5. Configure the oscilloscope for 10 MHz bandwidth limit to reduce high-frequency noise and set the timebase to 50 ns/div to display two complete clock periods. Trigger on the rising edge with 1.65V threshold representing the LVCMOS33 midpoint voltage. The waveform should display a 10 nanosecond period with 5 nanosecond high and low phases confirming the 100 MHz specification. Observe the finite rise and fall times typically measuring 2-3 nanoseconds due to PCB trace inductance and FPGA pin capacitance.

## Exercise 2: Parameter Variation & Empirical Analysis

The second laboratory exercise implements a parameterized finite state machine controlling a traffic light controller with configurable timing intervals. This design introduces state encoding optimization, one-hot versus binary encoding trade-offs, and the impact of state transition logic complexity on maximum clock frequency. The traffic light controller cycles through four states: North-South Green (NSG), North-South Yellow (NSY), East-West Green (EWG), and East-West Yellow (EWY) with dwell times specified by generic parameters allowing runtime reconfiguration without RTL modification.

The state machine architecture employs two separate always blocks following the recommended FSM coding style for FPGA synthesis. The first always block implements the state register updating the current state on each clock edge. The second combinatorial always block computes the next state and output logic based on the current state and timer expiration signals. This separation enables the synthesis tool to recognize the FSM structure and apply encoding optimizations including state reachability analysis and unreachable state elimination.

Navigate to `/fpga_labs/exercise_02_sequential/rtl/` and create the Verilog module `traffic_fsm.v` implementing the complete state machine with parameterized timing:

```verilog
module traffic_fsm #(
    parameter NSG_TICKS = 100_000_000,  // 1 second at 100 MHz
    parameter NSY_TICKS = 30_000_000,   // 0.3 seconds
    parameter EWG_TICKS = 100_000_000,  // 1 second
    parameter EWY_TICKS = 30_000_000    // 0.3 seconds
) (
    input wire clk,
    input wire rst,
    output reg [2:0] ns_lights,  // {Red, Yellow, Green}
    output reg [2:0] ew_lights
);

    localparam STATE_NSG = 2'b00;
    localparam STATE_NSY = 2'b01;
    localparam STATE_EWG = 2'b10;
    localparam STATE_EWY = 2'b11;

    reg [1:0] state, next_state;
    reg [26:0] timer;
    reg timer_expired;

    // State register
    always @(posedge clk) begin
        if (rst) begin
            state <= STATE_NSG;
            timer <= 27'd0;
        end else begin
            state <= next_state;
            if (state != next_state) begin
                timer <= 27'd0;
            end else begin
                timer <= timer + 27'd1;
            end
        end
    end

    // Timer expiration logic
    always @(*) begin
        case (state)
            STATE_NSG: timer_expired = (timer >= NSG_TICKS);
            STATE_NSY: timer_expired = (timer >= NSY_TICKS);
            STATE_EWG: timer_expired = (timer >= EWG_TICKS);
            STATE_EWY: timer_expired = (timer >= EWY_TICKS);
            default:   timer_expired = 1'b0;
        endcase
    end

    // Next state logic
    always @(*) begin
        case (state)
            STATE_NSG: next_state = timer_expired ? STATE_NSY : STATE_NSG;
            STATE_NSY: next_state = timer_expired ? STATE_EWG : STATE_NSY;
            STATE_EWG: next_state = timer_expired ? STATE_EWY : STATE_EWG;
            STATE_EWY: next_state = timer_expired ? STATE_NSG : STATE_EWY;
            default:   next_state = STATE_NSG;
        endcase
    end

    // Output logic
    always @(*) begin
        case (state)
            STATE_NSG: begin
                ns_lights = 3'b001;  // Green
                ew_lights = 3'b100;  // Red
            end
            STATE_NSY: begin
                ns_lights = 3'b010;  // Yellow
                ew_lights = 3'b100;  // Red
            end
            STATE_EWG: begin
                ns_lights = 3'b100;  // Red
                ew_lights = 3'b001;  // Green
            end
            STATE_EWY: begin
                ns_lights = 3'b100;  // Red
                ew_lights = 3'b010;  // Yellow
            end
            default: begin
                ns_lights = 3'b100;
                ew_lights = 3'b100;
            end
        endcase
    end

endmodule
```

The module declaration includes parameter definitions using the `parameter` keyword with default values representing one-second green light intervals and 300 millisecond yellow transitions. The parameter values employ underscores for readability in large decimal literals corresponding to clock cycle counts at 100 MHz. The state encoding uses binary representation with `2'b00` through `2'b11` requiring only two flip-flops compared to one-hot encoding requiring four flip-flops but potentially reducing combinatorial logic complexity.

Create the simulation testbench file `traffic_fsm_tb.v` in the `/fpga_labs/exercise_02_sequential/sim/` directory to verify correct state transitions and output assignments:

```verilog
`timescale 1ns / 1ps

module traffic_fsm_tb;

    reg clk;
    reg rst;
    wire [2:0] ns_lights;
    wire [2:0] ew_lights;

    // Instantiate with reduced timing for simulation
    traffic_fsm #(
        .NSG_TICKS(10),
        .NSY_TICKS(5),
        .EWG_TICKS(10),
        .EWY_TICKS(5)
    ) dut (
        .clk(clk),
        .rst(rst),
        .ns_lights(ns_lights),
        .ew_lights(ew_lights)
    );

    // Clock generation - 10ns period (100 MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Stimulus
    initial begin
        rst = 1;
        #25;
        rst = 0;
        
        #500;
        
        $display("Simulation complete");
        $finish;
    end

    // Monitor state changes
    always @(posedge clk) begin
        $display("Time=%0t ns_lights=%b ew_lights=%b", $time, ns_lights, ew_lights);
    end

endmodule
```

The testbench instantiates the DUT (device under test) with parameter overrides reducing the dwell times to 10 and 5 clock cycles enabling complete state machine traversal within a 500 nanosecond simulation window. The clock generation block uses the `forever` construct creating an infinite loop toggling the clock signal every 5 nanoseconds. The stimulus block applies reset for 25 nanoseconds then releases the state machine to autonomous operation. The monitor block prints the light outputs on every clock edge providing a transcript of state transitions.

Execute behavioral simulation in Vivado by adding the testbench file to the simulation sources and clicking "Run Simulation" in the Flow Navigator. The ModelSim or XSIM waveform viewer displays the clock, reset, state register, and output signal traces. Verify that the state machine progresses through the sequence NSG → NSY → EWG → EWY → NSG with correct timer reset on each transition. Measure the cycle time for a complete four-state traversal confirming 30 clock cycles corresponding to 10+5+10+5 ticks.

Zoom into the state transition from NSG to NSY observing the combinatorial propagation delay between the timer expiration signal assertion and the next state change. The waveform displays the timer reaching the NSG_TICKS threshold at the positive clock edge followed by the next_state signal updating combinatorially within the same delta cycle. The state register updates on the subsequent clock edge capturing the new state value. This timing relationship demonstrates the synchronous state machine operation where state transitions occur only on active clock edges despite combinatorial logic computing next states continuously.

Create the constraint file `/fpga_labs/exercise_02_sequential/constraints/basys3_traffic.xdc` mapping the six light outputs to twelve consecutive LEDs on the Basys3 board:

```tcl
set_property -dict { PACKAGE_PIN W5 IOSTANDARD LVCMOS33 } [get_ports clk]
create_clock -period 10.000 -name sys_clk_pin -waveform {0.000 5.000} [get_ports clk]

set_property -dict { PACKAGE_PIN U18 IOSTANDARD LVCMOS33 } [get_ports rst]

# North-South lights: Red, Yellow, Green
set_property -dict { PACKAGE_PIN U16 IOSTANDARD LVCMOS33 } [get_ports {ns_lights[2]}]
set_property -dict { PACKAGE_PIN E19 IOSTANDARD LVCMOS33 } [get_ports {ns_lights[1]}]
set_property -dict { PACKAGE_PIN U19 IOSTANDARD LVCMOS33 } [get_ports {ns_lights[0]}]

# East-West lights: Red, Yellow, Green
set_property -dict { PACKAGE_PIN V19 IOSTANDARD LVCMOS33 } [get_ports {ew_lights[2]}]
set_property -dict { PACKAGE_PIN W18 IOSTANDARD LVCMOS33 } [get_ports {ew_lights[1]}]
set_property -dict { PACKAGE_PIN U15 IOSTANDARD LVCMOS33 } [get_ports {ew_lights[0]}]
```

Synthesize and implement the design following the workflow from Exercise 1. Examine the post-implementation timing report focusing on the critical path from the timer counter through the comparison logic to the next state decoder. The timing analysis identifies the longest combinatorial path determining the maximum clock frequency. For this design, the critical path typically originates at the 27-bit counter most significant bits, propagates through the magnitude comparator, continues through the case statement decoder computing next state, and terminates at a state register D input.

Calculate the maximum achievable clock frequency from the timing report by inverting the critical path delay. If the worst negative slack reports -2.15ns with a 10ns clock period constraint, the actual critical path requires 10ns + 2.15ns = 12.15ns. The maximum frequency equals 1 / 12.15ns = 82.3 MHz indicating the design fails timing at the specified 100 MHz clock rate. This timing violation necessitates design optimization through pipelining, logic restructuring, or frequency reduction.

Implement a pipelined timer comparison by registering the comparison result reducing combinatorial path length:

```verilog
    reg timer_expired_d1;
    
    always @(posedge clk) begin
        case (state)
            STATE_NSG: timer_expired_d1 <= (timer >= NSG_TICKS);
            STATE_NSY: timer_expired_d1 <= (timer >= NSY_TICKS);
            STATE_EWG: timer_expired_d1 <= (timer >= EWG_TICKS);
            STATE_EWY: timer_expired_d1 <= (timer >= EWY_TICKS);
            default:   timer_expired_d1 <= 1'b0;
        endcase
    end
    
    assign timer_expired = timer_expired_d1;
```

This modification introduces one clock cycle of latency in the timer expiration signal but breaks the critical path into two shorter segments. Resynthesize and examine the timing report confirming positive slack indicating the design now meets timing at 100 MHz. The one-cycle latency increases state dwell times by 10 nanoseconds representing a negligible error in the multi-second timing intervals.

Perform a parameter sweep analysis quantifying the relationship between state count and maximum frequency. Modify the FSM to include six states (adding North-South Left Turn Arrow and East-West Left Turn Arrow) observing the impact on critical path delay. Generate timing reports for 4-state, 6-state, 8-state, and 10-state configurations compiling maximum frequency data into a spreadsheet. Plot the frequency versus state count curve revealing the logarithmic relationship where each doubling of state count adds approximately 15% delay due to increased decoder complexity.

Analyze alternative state encoding schemes by adding synthesis directives controlling FSM optimization. Insert the following attribute before the state register declaration:

```verilog
(* fsm_encoding = "one_hot" *) reg [3:0] state, next_state;
```

The one-hot encoding directive instructs the synthesis tool to use four flip-flops with exactly one bit high per state eliminating the binary-to-one-hot decoder at the cost of additional register resources. Synthesize both binary and one-hot variants comparing resource utilization and timing. The one-hot encoding typically consumes 2-4 additional flip-flops but reduces LUT count by 20-30% in the next state logic producing marginally higher maximum frequencies in large state machines.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The final laboratory exercise implements a high-speed serial UART transmitter operating at 921,600 baud challenging the FPGA timing closure and I/O slew rate specifications. This design explores clock domain crossing, asynchronous input synchronization, metastability mitigation through dual-rank flip-flop chains, and bit error rate measurement under process-voltage-temperature variation. The UART transmitter accepts parallel byte data and serializes it into start bit, eight data bits, and stop bit framing at the specified baud rate requiring precise timing derived from the 100 MHz system clock.

The baud rate generation divides the system clock by a computed divisor calculating the cycles per bit period. For 921,600 baud operation, each bit period spans 1.085 microseconds requiring 108.5 clock cycles at 100 MHz. The fractional cycle count necessitates a fractional-N divider or baud rate clock enable generator producing a one-cycle pulse every 108 or 109 clock cycles alternating to achieve the average ratio. The transmitter state machine advances through eleven states corresponding to idle, start bit, eight data bits, and stop bit outputting the appropriate serial value on each baud tick.

Create the UART transmitter module in `/fpga_labs/exercise_03_timing/rtl/uart_tx.v`:

```verilog
module uart_tx #(
    parameter CLK_FREQ = 100_000_000,
    parameter BAUD_RATE = 921_600
) (
    input wire clk,
    input wire rst,
    input wire [7:0] tx_data,
    input wire tx_valid,
    output reg tx_ready,
    output reg tx_serial
);

    localparam CYCLES_PER_BIT = CLK_FREQ / BAUD_RATE;
    
    localparam STATE_IDLE  = 4'd0;
    localparam STATE_START = 4'd1;
    localparam STATE_DATA0 = 4'd2;
    localparam STATE_DATA1 = 4'd3;
    localparam STATE_DATA2 = 4'd4;
    localparam STATE_DATA3 = 4'd5;
    localparam STATE_DATA4 = 4'd6;
    localparam STATE_DATA5 = 4'd7;
    localparam STATE_DATA6 = 4'd8;
    localparam STATE_DATA7 = 4'd9;
    localparam STATE_STOP  = 4'd10;

    reg [3:0] state;
    reg [7:0] shift_reg;
    reg [7:0] baud_counter;
    
    always @(posedge clk) begin
        if (rst) begin
            state <= STATE_IDLE;
            tx_serial <= 1'b1;
            tx_ready <= 1'b1;
            baud_counter <= 8'd0;
            shift_reg <= 8'd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    tx_serial <= 1'b1;
                    tx_ready <= 1'b1;
                    baud_counter <= 8'd0;
                    if (tx_valid) begin
                        shift_reg <= tx_data;
                        state <= STATE_START;
                        tx_ready <= 1'b0;
                    end
                end
                
                STATE_START: begin
                    tx_serial <= 1'b0;
                    if (baud_counter == CYCLES_PER_BIT - 1) begin
                        baud_counter <= 8'd0;
                        state <= STATE_DATA0;
                    end else begin
                        baud_counter <= baud_counter + 8'd1;
                    end
                end
                
                STATE_DATA0, STATE_DATA1, STATE_DATA2, STATE_DATA3,
                STATE_DATA4, STATE_DATA5, STATE_DATA6, STATE_DATA7: begin
                    tx_serial <= shift_reg[0];
                    if (baud_counter == CYCLES_PER_BIT - 1) begin
                        baud_counter <= 8'd0;
                        shift_reg <= {1'b0, shift_reg[7:1]};
                        state <= state + 4'd1;
                    end else begin
                        baud_counter <= baud_counter + 8'd1;
                    end
                end
                
                STATE_STOP: begin
                    tx_serial <= 1'b1;
                    if (baud_counter == CYCLES_PER_BIT - 1) begin
                        baud_counter <= 8'd0;
                        state <= STATE_IDLE;
                    end else begin
                        baud_counter <= baud_counter + 8'd1;
                    end
                end
                
                default: state <= STATE_IDLE;
            endcase
        end
    end

endmodule
```

The module implements a simple handshake protocol where the `tx_valid` input signal indicates parallel data availability and the `tx_ready` output acknowledges the transmitter's idle state. The state machine deasserts `tx_ready` upon capturing the input byte and maintains the busy state throughout the eleven-bit transmission period spanning approximately 11.9 microseconds at 921.6 kbaud. The shift register right-shifts on each data bit state transition outputting the least significant bit to the serial line following UART little-endian convention.

Create a loopback test wrapper instantiating the transmitter and a simple byte pattern generator:

```verilog
module uart_loopback_test (
    input wire clk,
    input wire rst,
    output wire tx_serial,
    output wire [7:0] debug_data
);

    reg [7:0] test_pattern;
    reg tx_valid;
    wire tx_ready;
    
    uart_tx #(
        .CLK_FREQ(100_000_000),
        .BAUD_RATE(921_600)
    ) uart_inst (
        .clk(clk),
        .rst(rst),
        .tx_data(test_pattern),
        .tx_valid(tx_valid),
        .tx_ready(tx_ready),
        .tx_serial(tx_serial)
    );
    
    assign debug_data = test_pattern;
    
    always @(posedge clk) begin
        if (rst) begin
            test_pattern <= 8'h55;
            tx_valid <= 1'b0;
        end else begin
            if (tx_ready && !tx_valid) begin
                tx_valid <= 1'b1;
                test_pattern <= test_pattern + 8'd1;
            end else begin
                tx_valid <= 1'b0;
            end
        end
    end

endmodule
```

The test pattern generator initializes with the value `0x55` (binary `01010101`) producing maximal signal transitions on the serial line for bit error detection. The generator increments the pattern on each transmission creating a continuous ascending byte sequence. The handshake logic asserts `tx_valid` for one clock cycle when the transmitter reports ready status initiating back-to-back transmissions with minimal inter-frame gap.

Create the constraint file mapping the serial output to a PMOD connector for oscilloscope observation and the debug data to LEDs for visual pattern verification:

```tcl
set_property -dict { PACKAGE_PIN W5 IOSTANDARD LVCMOS33 } [get_ports clk]
create_clock -period 10.000 -name sys_clk_pin -waveform {0.000 5.000} [get_ports clk]

set_property -dict { PACKAGE_PIN U18 IOSTANDARD LVCMOS33 } [get_ports rst]

# UART TX output - PMOD JA1
set_property -dict { PACKAGE_PIN J1 IOSTANDARD LVCMOS33 SLEW FAST } [get_ports tx_serial]

# Debug pattern outputs
set_property -dict { PACKAGE_PIN U16 IOSTANDARD LVCMOS33 } [get_ports {debug_data[0]}]
set_property -dict { PACKAGE_PIN E19 IOSTANDARD LVCMOS33 } [get_ports {debug_data[1]}]
set_property -dict { PACKAGE_PIN U19 IOSTANDARD LVCMOS33 } [get_ports {debug_data[2]}]
set_property -dict { PACKAGE_PIN V19 IOSTANDARD LVCMOS33 } [get_ports {debug_data[3]}]
set_property -dict { PACKAGE_PIN W18 IOSTANDARD LVCMOS33 } [get_ports {debug_data[4]}]
set_property -dict { PACKAGE_PIN U15 IOSTANDARD LVCMOS33 } [get_ports {debug_data[5]}]
set_property -dict { PACKAGE_PIN U14 IOSTANDARD LVCMOS33 } [get_ports {debug_data[6]}]
set_property -dict { PACKAGE_PIN V14 IOSTANDARD LVCMOS33 } [get_ports {debug_data[7]}]
```

The `SLEW FAST` attribute configures the output buffer for maximum drive strength and minimum rise/fall time reducing edge jitter at high baud rates. The fast slew setting increases electromagnetic emissions and power supply noise but proves necessary for reliable 921.6 kbaud operation over PMOD cable lengths exceeding 15 centimeters.

Synthesize and implement the design examining the post-implementation timing report with particular attention to clock-to-out delays on the `tx_serial` output. The timing report includes output delay paths from the flip-flop driving `tx_serial` through the IOB (Input/Output Block) to the package pin. Locate the maximum clock-to-out specification typically reporting 3-4 nanoseconds for the LVCMOS33 standard with fast slew rate. This delay represents the minimum time from clock edge to valid data at the FPGA pin establishing the bit edge timing uncertainty budget.

Program the bitstream and connect the oscilloscope probe to the PMOD JA1 pin observing the UART serial waveform. Configure the oscilloscope for DC coupling, 500 mV/div vertical scale, and 2 microseconds/div horizontal scale capturing multiple complete frames. Trigger on the falling edge representing the start bit with threshold voltage 1.65V. The waveform displays the idle state at logic high, start bit low transition, eight data bits with varying levels encoding the current pattern value, and stop bit high transition.

Enable infinite persistence mode on the oscilloscope accumulating hundreds of frames and observe edge jitter manifesting as waveform thickness at bit transitions. The accumulated trace reveals timing variations from clock jitter, power supply noise, and thermal effects. Measure the edge jitter by placing cursors at the thinnest and thickest portions of a rising edge at the bit transitions. Typical jitter measurements range from 100 to 300 picoseconds peak-to-peak representing 0.01-0.03% of the 1.085 microsecond bit period providing substantial margin below the UART receiver's sampling window.

Implement bit error rate testing by connecting a USB-to-serial adapter configured for 921600 baud, 8 data bits, no parity, and 1 stop bit to the UART output pin. Use a Python script with the pyserial library to capture the continuous byte stream and verify ascending pattern sequence:

```python
import serial
import sys

def test_uart_ber(port, baud_rate, test_duration):
    ser = serial.Serial(port, baud_rate, timeout=1)
    expected = 0x55
    errors = 0
    total_bytes = 0
    
    print(f"Testing UART at {baud_rate} baud on {port}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            data = ser.read(1)
            if len(data) == 1:
                received = data[0]
                if received != expected:
                    errors += 1
                    print(f"Error at byte {total_bytes}: expected 0x{expected:02X}, got 0x{received:02X}")
                
                expected = (expected + 1) & 0xFF
                total_bytes += 1
                
                if total_bytes % 10000 == 0:
                    ber = errors / total_bytes if total_bytes > 0 else 0
                    print(f"Bytes: {total_bytes}, Errors: {errors}, BER: {ber:.2e}")
    
    except KeyboardInterrupt:
        print(f"\nTest completed: {total_bytes} bytes, {errors} errors")
        final_ber = errors / total_bytes if total_bytes > 0 else 0
        print(f"Final BER: {final_ber:.2e}")
    
    finally:
        ser.close()

if __name__ == "__main__":
    test_uart_ber("/dev/ttyUSB0", 921600, 60)
```

Execute the script for extended duration capturing millions of bytes to establish statistically significant error rates. In a well-designed system with proper signal integrity, the bit error rate should remain below 10^-9 (one error per billion bits). Elevated error rates indicate timing violations, insufficient output drive strength, or impedance mismatches requiring design iteration.

Perform thermal stress testing by monitoring bit error rate while varying ambient temperature. Use a heat gun to elevate the FPGA junction temperature observing error rate increase as propagation delays grow with temperature. The Artix-7 datasheet specifies timing derating of approximately 0.4% per degree Celsius above 25°C. At 85°C junction temperature, setup times increase by 24% potentially causing timing violations in marginally-met designs. Implement thermal monitoring by reading the FPGA's internal XADC (Xilinx Analog-to-Digital Converter) temperature sensor through the JTAG interface.

Instantiate the XADC primitive in the design for continuous junction temperature measurement:

```verilog
module uart_with_thermal_monitor (
    input wire clk,
    input wire rst,
    output wire tx_serial,
    output wire [11:0] temperature
);

    wire [15:0] temperature_raw;
    
    uart_loopback_test uart_inst (
        .clk(clk),
        .rst(rst),
        .tx_serial(tx_serial),
        .debug_data()
    );
    
    xadc_wiz_0 xadc_inst (
        .dclk_in(clk),
        .reset_in(rst),
        .vp_in(1'b0),
        .vn_in(1'b0),
        .user_temp_alarm_out(),
        .channel_out(),
        .eoc_out(),
        .alarm_out(),
        .eos_out(),
        .busy_out(),
        .temp_out(temperature_raw)
    );
    
    // Convert from XADC format: Temp(°C) = (ADC * 503.975 / 4096) - 273.15
    assign temperature = temperature_raw[15:4];  // Simplified: raw ADC / 16

endmodule
```

The XADC wizard-generated IP core samples the internal temperature sensor at the specified clock frequency producing a 16-bit ADC result in the upper 12 bits. The conversion formula translates the raw ADC code to degrees Celsius requiring fixed-point multiplication and subtraction. For simplified monitoring, output the raw 12-bit value to the debug LEDs or transmit via UART to the host computer for real-time logging.

Correlate bit error rate with junction temperature by recording both metrics during the thermal stress test. Plot BER versus temperature revealing the exponential relationship where each 10°C increase doubles the error rate approaching the critical temperature where timing violations become systematic. This characterization data informs operating margin analysis determining safe junction temperature limits for field deployment.

Implement adaptive baud rate correction by incorporating a frequency-locked loop adjusting the baud divisor based on received frame timing measurements. This advanced technique compensates for clock frequency drift due to crystal aging and temperature variation maintaining bit timing accuracy over component lifetime. The correction algorithm measures the time interval between start bit edges across multiple frames computing the average actual baud rate and updating the divisor register dynamically.

## Operational Reference Guide & Diagnostic Checklist

### Critical Design Constraints Verification Protocol

Before declaring any FPGA design complete, execute the mandatory seven-point verification checklist ensuring synthesis correctness, timing closure, and implementation validity. First, inspect the elaborated RTL schematic confirming that all intended flip-flops infer as sequential elements rather than latches. Unintended latches appear as level-sensitive storage elements typically resulting from incomplete case statement coverage or missing assignments in combinatorial always blocks. The schematic viewer represents latches with the LDCE or LDPE primitives distinguished from FDRE flip-flops by the lack of clock input symbols.

Second, analyze the synthesis report warning messages filtering for critical issues including multi-driven nets, unconnected ports, and timing constraint exceptions. Multi-driven nets indicate multiple drivers competing for the same signal potentially causing electrical contention during configuration. Unconnected output ports waste routing resources and may indicate incomplete design integration. Timing constraint exceptions for paths marked as false paths or multicycle paths require manual verification confirming the designer's intent matches the actual circuit behavior.

Third, execute static timing analysis post-implementation examining setup slack, hold slack, and pulse width checks across all clock domains. Setup slack quantifies the available margin between data arrival time and clock edge minus setup time requirement. Negative setup slack indicates timing failure requiring frequency reduction, logic optimization, or pipeline insertion. Hold slack measures the margin between clock edge and data departure time plus hold time requirement. Hold violations prove more insidious than setup violations because they cannot be corrected by frequency reduction, only by adding delay buffers or restructuring placement.

Fourth, verify I/O timing constraints including input delay, output delay, and maximum transition time specifications. Input delay constraints specify the external device setup time relative to the FPGA clock establishing required data arrival times at input pads. Output delay constraints specify the external device hold time relative to the FPGA clock establishing maximum allowable clock-to-out delays. Maximum transition time limits slew rate controlling electromagnetic emission and signal integrity particularly critical for high-speed interfaces exceeding 100 MHz edge rates.

Fifth, perform power analysis using the Xilinx Power Estimator (XPE) or Vivado Power Report estimating static leakage, dynamic switching, and I/O power consumption. The power report aggregates contributions from logic switching, clock tree distribution, block RAM access, DSP operations, and I/O driver currents. Compare the estimated power against the supply capability noting that the Basys3 USB interface provides 500mA at 5V yielding 2.5W budget with approximately 0.5W consumed by non-FPGA circuitry leaving 2W for the FPGA core.

Sixth, validate clock domain crossing (CDC) topologies ensuring all asynchronous path crossings implement proper synchronization. Dual-rank synchronizer chains represent the minimum safe CDC structure where an input signal passes through two cascaded flip-flops in the destination clock domain with the first flip-flop marked with the ASYNC_REG property preventing optimization. The second flip-flop captures the synchronized value with metastability resolved through the two-register pipeline settling time. Multi-bit CDC requires additional techniques including gray code encoding for counters or handshake protocols for data buses.

Seventh, execute functional verification through simulation with comprehensive testbenches covering normal operation, boundary conditions, and error injection scenarios. The testbench must exercise all state machine states, verify all combinatorial logic paths, and confirm correct reset behavior. Code coverage analysis quantifies the percentage of RTL statements executed during simulation with industry targets demanding 95% line coverage and 90% branch coverage for safety-critical applications.

### Common Failure Modes and Diagnostic Procedures

**Synthesis Failures**: Syntax errors during elaboration typically manifest as Verilog or VHDL parsing failures with line number references. The error messages frequently cite undefined identifiers, type mismatches between assignments, or unresolved module instantiations. Verify that all modules reference existing source files and that port connections match instantiation widths. Implicit net declarations in Verilog often cause confusion where undeclared signals default to one-bit wire type potentially masking bus width mismatches.

**Timing Violations Post-Implementation**: Negative slack in the timing report indicates critical path delays exceeding clock period constraints. Diagnose the failing path by expanding the detailed timing report examining each logic level and routing segment. Common critical paths originate in wide arithmetic operations (multipliers, comparators), deeply nested multiplexers, or excessive fanout nets driving hundreds of downstream gates. Remediation strategies include pipeline register insertion, operator tree restructuring, or clock frequency reduction.

**Bitstream Download Failures**: JTAG communication errors during programming manifest as device detection failures or verification mismatches. Confirm proper USB cable connection with the Basys3 power LED illuminated and the FPGA unpowered from external sources. Verify JTAG chain integrity by executing boundary scan tests through Vivado's Hardware Manager. Check that the target device IDCODE matches the constraint file specification preventing programming attempts on wrong silicon variants.

**Non-Functional Hardware After Programming**: Successful bitstream download with non-operational circuit behavior suggests incorrect constraint mapping or design logic errors. Verify constraint file pin assignments by measuring voltage levels at physical pins using a multimeter or oscilloscope. Confirm clock signal presence by probing the system oscillator output. Implement internal logic analyzer (ILA) IP cores providing virtual oscilloscope channels sampling internal signals synchronized to the system clock enabling real-time debugging without external instrumentation.

**Intermittent Errors Under Temperature or Voltage Variation**: Designs exhibiting temperature-dependent failures indicate marginal timing closure with positive slack insufficient to accommodate worst-case conditions. Rerun static timing analysis with worst-case commercial temperature range specifications (0°C to 85°C) and voltage corners (±10% supply variation). Increase clock constraints conservatively to 110% of the target frequency ensuring adequate margin. Implement voltage monitoring using the XADC primitive tracking VCCINT and VCCAUX rails detecting supply droop during transient load conditions.

### FPGA Resource Utilization Analysis

The Artix-7 architecture organizes silicon resources into a hierarchical fabric with CLBs as the fundamental building block. Each CLB contains two slices and each slice contains four six-input LUTs, eight flip-flops, multiplexers, and carry chain logic. The synthesis tool maps RTL combinatorial logic to LUT functions and sequential logic to flip-flops with optimization objectives balancing area (resource minimization) versus speed (critical path minimization). The utilization report breaks down consumed resources by type including LUT logic, LUT RAM, flip-flops, BRAM tiles, DSP slices, and I/O.

LUT utilization percentage indicates the fraction of available logic consumed by the design with values exceeding 85% triggering placement congestion and routing difficulties. High LUT consumption designs benefit from resource sharing optimizations where synthesis identifies common subexpressions and multiplexes shared logic across mutually-exclusive code paths. The retiming optimization shifts flip-flops across combinatorial clouds reducing critical path depths at the cost of increased register count.

BRAM consumption represents dedicated memory blocks organized as dual-port 36-kilobit tiles configurable in various width-depth ratios. The Artix-7 XC7A35T provides 50 BRAM tiles totaling 1,800 kilobits suitable for buffer storage, lookup tables, and embedded processor memories. Designs requiring larger memory capacities exceed FPGA resources necessitating external DRAM interfaces or memory controller IP cores.

DSP slice utilization measures consumption of dedicated arithmetic units implementing 25×18-bit signed multipliers, 48-bit accumulators, and pre-adder logic optimized for signal processing operations. Inferring DSP primitives requires specific Verilog coding styles including registered inputs and outputs surrounding multiply-accumulate operations. Unoptimized arithmetic expressions synthesize to LUT-based implementations consuming excessive area and speed.

I/O bank assignments group pins sharing common VCCO voltage supplies with each bank supporting one voltage standard. The Basys3 board configures all banks for LVCMOS33 operation simplifying constraint files but limiting voltage translation options. High-pin-count designs must balance I/O assignments across banks preventing oversubscription where pin counts exceed bank capacity triggering implementation failures.

### Advanced Timing Closure Techniques

Designs failing timing closure despite architectural optimization require advanced implementation techniques manipulating placement and routing algorithms. Floorplanning directives constrain specific logic modules to rectangular regions within the FPGA fabric reducing wire lengths and improving routability. Create floorplan pblocks in Vivado by selecting logic hierarchies and assigning bounding box coordinates through the Tcl command `create_pblock` followed by `add_cells_to_pblock` and `resize_pblock` for dimensional specification.

Directed routing constraints control wire path selection for critical nets requiring specific routing resources. The DIRECTED_ROUTING attribute applies to net objects specifying routing tiles and interconnect segments enforcing designer-controlled paths. This technique proves useful for clock distribution where manual routing through dedicated clock spines reduces skew below automated router results.

Physical synthesis optimizations execute after initial placement replicating high-fanout drivers reducing routing congestion and improving timing. Enable physical synthesis through synthesis strategy selection in Vivado specifying area optimization, timing optimization, or power optimization objectives. The physical synthesis engine performs retiming, logic replication, register duplication, and LUT combining transformations considering physical placement coordinates.

Multi-corner multi-mode timing analysis validates designs across process, voltage, and temperature corners ensuring operation under all specified conditions. The worst-case slow-slow corner with high temperature, low voltage, and slow process models maximum delays. The best-case fast-fast corner with low temperature, high voltage, and fast process models minimum delays relevant for hold time analysis. Specify additional timing corners through XDC constraints using set_operating_conditions commands.

### Signal Integrity and PCB Layout Considerations

High-speed FPGA I/O operation demands careful attention to PCB transmission line effects, termination schemes, and power distribution networks. Signals exceeding 50 MHz edge rates exhibit non-lumped behavior where interconnect electrical length approaches signal wavelength necessitating controlled impedance design. The Basys3 board implements four-layer stackup with dedicated ground and power planes providing low-inductance return paths for high-speed signals.

LVCMOS33 single-ended signaling lacks differential noise immunity limiting reliable operation to approximately 400 MHz edge rates over short traces. Higher performance interfaces employ LVDS (Low-Voltage Differential Signaling) transmitting complementary signals on twisted pairs with 100-ohm differential impedance. The Artix-7 HP (High Performance) I/O banks support LVDS requiring external termination resistors matched to trace impedance.

Simultaneous switching noise (SSN) arises when multiple I/O drivers transition simultaneously inducing transient currents through bonding wire and package lead inductances. The resulting ground bounce and power rail droop introduce noise margins potentially causing false logic transitions. Mitigate SSN by staggering output transitions, reducing slew rates via SLOW attribute, and providing adequate decoupling capacitance at each VCCO supply pin.

Clock distribution introduces deterministic and random jitter degrading timing margins in high-speed synchronous designs. Deterministic jitter originates from crosstalk, power supply modulation, and intersymbol interference while random jitter derives from thermal noise and phase noise in oscillators. The FPGA global clock buffers (BUFG primitives) provide low-skew distribution with matched delays across the fabric suitable for frequencies exceeding 500 MHz.

### Metastability Analysis and Mitigation

Clock domain crossing events introduce metastability risk where a flip-flop samples an input violating setup or hold time requirements causing the output to hover in an indeterminate voltage region before eventually resolving to logic 0 or 1. The metastable state exhibits exponential decay with time constant determined by flip-flop gain-bandwidth product typically ranging from 50 to 100 picoseconds. Insufficient settling time permits metastable outputs to propagate through downstream logic potentially causing system failure.

The dual-rank synchronizer topology provides two sequential clock cycles for metastability resolution reducing failure probability to acceptable levels. The mean time between failures (MTBF) for metastability quantifies expected reliability with acceptable values exceeding millions of years. Calculate MTBF using the formula: MTBF = e^(tr/τ) / (T₀ × f_clk × f_data) where tr represents resolution time, τ denotes flip-flop time constant, T₀ indicates vulnerability window, f_clk specifies destination clock frequency, and f_data represents input transition frequency.

Mark synchronizer flip-flops with ASYNC_REG attributes preventing optimization tools from collapsing redundant registers or moving logic between synchronization stages. Apply false path timing constraints from source to first synchronizer register disabling static timing analysis on the asynchronous path while preserving timing checks through subsequent synchronous stages. Implement the constraint using: `set_false_path -from [get_clocks src_clk] -to [get_pins sync_reg_1/D]`.

Gray code encoding for multi-bit CDC scenarios ensures only one bit transitions per count increment eliminating transient multi-bit errors during asynchronous sampling. Convert binary counters to Gray code before crossing clock domains and reconvert in the destination domain. Handshake protocols provide robust multi-bit CDC through request-acknowledge signaling where the source asserts request after updating data and the destination acknowledges after sampling completing a four-phase transaction tolerating arbitrary clock frequency ratios.
