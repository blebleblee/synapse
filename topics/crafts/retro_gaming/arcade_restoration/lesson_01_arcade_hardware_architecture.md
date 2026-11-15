# Lesson 1: Arcade Hardware Architecture

## 1. First-Principles Intuition & Invariants

There is a particular quality of silence inside a powered-down arcade cabinet that the experienced restorer learns to read like a text. The way the monitor's neck board holds residual charge long after the coin door was last opened, the faint smell of rosin flux baked into a PCB that has sat in a warehouse for thirty years, the specific sag of a control panel overlay whose foam backing has finally surrendered to humidity — these are not incidental details. They are the first diagnostic data your senses receive before a single meter probe touches a terminal.

Understanding arcade hardware at the architectural level means understanding a class of machine that was engineered under constraints that have no modern equivalent. By the late 1970s and through the 1980s, arcade manufacturers were building embedded real-time systems that had to operate in the harshest commercial environments imaginable: coin-fed public machines subjected to deliberate abuse, temperature swings, spilled beverages, and the continuous electromagnetic noise of fluorescent lighting and deflection yokes. Every design decision — the weight of the cabinet, the gauge of the power harness, the topology of the monitor chassis — was made under the dual pressure of minimizing manufacturing cost and maximizing mean time between failures in a revenue-generating context. When a machine went dark on the floor of an arcade, it stopped making money by the minute. Reliability was not an engineering virtue; it was a commercial survival requirement.

This context explains the most important invariant the restorer must internalize before touching a single component: **arcade systems were not designed as integrated products in the modern sense.** They were assembled from semi-independent subsystems — cabinet, power supply, monitor chassis, PCB, control panel harness, and coin mechanism — each of which could be sourced, replaced, or repaired independently. A Jamma-era technician in 1988 could swap a monitor chassis from one manufacturer into a cabinet from another, wire a PCB from a third vendor, and have a revenue-generating machine on the floor within an hour. This modularity is the gift that makes restoration possible decades later. It is also the source of nearly every diagnostic complexity you will encounter, because those subsystems were never required to speak a common electrical language beyond a minimum viable interface standard.

The physical taxonomy of arcade cabinets divides into three broadly recognized forms. The **upright**, sometimes called a standard or dedicated cabinet, is the vertical freestanding enclosure most people picture when they think of an arcade machine — a wooden box roughly 170 cm tall, 60 cm wide, and 70 cm deep, with the monitor mounted at an angle behind a bezel, the control panel at waist height, and the PCB and power supply tucked in the lower cabinet behind a lockable door. The **cocktail** cabinet lays the monitor horizontally under a glass tabletop, with control panels on opposing ends and the game logic flipped for alternating-player orientation — a form factor that places entirely different demands on monitor geometry and player ergonomics. The **cabaret** or mini-upright is a shorter, shallower variant of the standard upright, common in locations with ceiling height constraints or operators who needed to stack more machines per square meter. Each form factor dictates different cable routing paths, different monitor mounting hardware, different sight-line angles for the bezel opening, and different weight distributions that affect the structural engineering of the cabinet itself.

The majority of cabinets produced from roughly 1983 onward were built from medium-density fiberboard or particle board, finished with vinyl laminate or painted over a lacquer primer. Earlier dedicated cabinets and higher-end titles through the mid-1980s used plywood, which is structurally superior, holds fasteners more reliably, and resists moisture-induced swelling far better. The restorer who opens a Pac-Man upright will find plywood construction; the restorer who opens a mid-tier 1990 Jamma conversion cabinet will typically find MDF, which has already begun to delaminate at the bottom corners where decades of floor moisture have wicked upward. This distinction matters immediately when you are evaluating whether a cabinet can be restored in place or whether structural sections need to be rebuilt before any electrical work begins.

The single most important electrical invariant in the entire field of arcade restoration is the distinction between **dedicated hardware and the JAMMA standard**. Before 1985, virtually every arcade title ran on a PCB designed specifically for one cabinet — Galaga's hardware was wired to a Galaga harness, Donkey Kong's board to a Donkey Kong cabinet, with no expectation of interoperability. The JAMMA standard, formalized by the Japan Amusement Machine and Marketing Association in 1985, defined a 56-pin edge connector that established a common electrical interface for power rails, video signals, audio output, control inputs, and coin mechanism signals. From 1985 onward, an operator could take any JAMMA-compliant PCB, plug it into any JAMMA-compliant cabinet, and expect a working machine — provided the cabinet's power supply, monitor, and harness were all within specification. This interoperability defined the economics of arcade operation through the 1990s and is the reason so many cabinets survived: they were worth keeping because they could always be reflashed with new content. For the restorer, JAMMA compliance is both a convenience and a diagnostic framework. When a JAMMA machine misfires, the standard tells you exactly which pin carries which signal, which eliminates guesswork and allows systematic fault isolation.

---

## 2. Core Architecture & Mechanics

### Cabinet Construction and Structural Mechanics

The structural load path of an upright cabinet runs from the monitor shelf — which bears roughly 15 to 25 kg of CRT assembly — through the vertical side panels, into the base. In original factory construction, this shelf is dadoed or rabbeted into the side panels and secured with glue and staples, with corner blocks added in higher-quality builds. After thirty-plus years, the adhesive has typically failed and the fasteners have worked loose, leaving the monitor shelf resting primarily on friction. Before reinstalling any monitor, the restorer must verify that the shelf is mechanically sound. This means probing every glue joint with a flat screwdriver, feeling for movement, and re-gluing and re-blocking as necessary. A monitor shelf that fails under a 20 kg chassis will destroy the tube, the PCB below it, and potentially injure whoever is standing in front of the machine.

The coin door assembly is bolted to the front panel and carries the coin mechanism, the coin return button, and in many cabinets, the service switches and test button. The door itself is typically 18-gauge cold-rolled steel, hinged on one side, with a tumbler lock. The hinge pins are a consistent wear point — after years of daily opening and closing during cash collections, the hinge barrel elongates and the door sags, which prevents the door switch from making clean contact. This matters electrically because the coin door switch on most cabinets is wired in series with the cabinet's AC power or with the high-voltage enable line of the monitor, as a safety interlock. A sagging door that holds the switch in an ambiguous state can cause the monitor to fail to light, which is frequently misdiagnosed as a monitor fault.

### Power Distribution Architecture

The power system in a typical arcade cabinet begins at the IEC or hardwired AC inlet, passes through a fuse holder and line filter, and terminates at a switching or linear power supply that produces the DC rails the game logic requires. Pre-JAMMA and early JAMMA hardware predominantly used **linear power supplies** — transformer-rectifier-filter-regulator assemblies that are heavy, thermally inefficient, and entirely serviceable with basic electronics skills. The transformer steps the mains voltage down, a full-wave bridge rectifier converts AC to pulsating DC, a large filter capacitor bank smooths the ripple, and a series pass regulator (or a bank of them) holds the output voltage stable under varying load.

The DC rails produced vary by platform, but the most common configuration for JAMMA hardware provides +5 V for logic, +12 V for audio amplification and motor drives, and in many cabinets a -5 V rail for older TTL logic families that require it. Some platforms (notably many Konami and early Capcom boards) also require a -12 V rail. The JAMMA standard allocates specific pins for each rail, and the restorer's first act when bringing a new PCB into a cabinet should be to measure all rails at the JAMMA connector with the board disconnected, before making contact. A +5 V rail that reads 5.8 V will destroy CMOS logic within minutes. The acceptable operating range for most game logic is +4.95 V to +5.10 V measured at the connector with the board drawing full current — not at the power supply output terminals, where resistive drop in the harness will make the rail appear higher than the board actually sees.

Switching power supplies became common in arcade cabinets from the late 1980s onward and are the type most restorers encounter in JAMMA conversion cabinets. They are more efficient and lighter than linears, but their failure modes are subtler. A failing switching supply will often produce correct output voltage under no-load bench measurement but sag catastrophically under the full current draw of a CPU board, or it will produce correct average voltage but with high-frequency ripple that upsets sensitive analog circuits. The correct diagnostic instrument here is an oscilloscope, not a multimeter. Set the scope to DC coupling, probe the +5 V rail at the JAMMA connector with the game board fully loaded, and look for ripple amplitude. Anything above 50 mV peak-to-peak warrants supply replacement or recapping.

```
AC Mains (120/240V)
        │
   [Line Fuse]
        │
 [EMI Line Filter]
        │
  [Power Switch]
        │
  ┌─────┴──────────────────────────────────────────────────────┐
  │                    Power Supply Unit                        │
  │  Transformer ──► Bridge Rectifier ──► Filter Caps ──► Reg  │
  └──────┬────────────────────┬─────────────────────┬──────────┘
         │                    │                     │
       +5 VDC              +12 VDC               -5 VDC
         │                    │                     │
  [JAMMA Edge Connector - Pins A/B 1–28, C/D 1–28]
         │
    [PCB Logic]──[Audio Amp]──[Coin Mechanism]──[Controls]
```

The ground architecture deserves more attention than most restoration guides give it. Arcade machines were among the first consumer-facing products to operate at high voltages (the monitor anode runs at 25–30 kV) in a metal-and-wood enclosure accessible to the public. The chassis ground — the metal frame of the cabinet, the coin door, the monitor chassis mounting brackets — must be bonded together and connected to earth ground through the AC inlet's protective earth conductor. This is not optional and not merely a regulatory formality. A floating chassis ground means that any leakage current from the monitor's flyback transformer or the AC power supply has no defined return path. That path will be found by the first person who touches the coin door while standing on a concrete floor.

The correct grounding topology for a restored cabinet connects the AC inlet protective earth to the cabinet chassis, bonds the monitor chassis mounting bracket to that same chassis ground with a dedicated 14-AWG or heavier wire, and ensures the JAMMA harness ground pins (which carry DC common from the power supply) are connected to the same ground reference. Ground loops — where two portions of the chassis are connected to ground through paths of different impedance — manifest as a 60 Hz hum in the audio amplifier output, random video noise or rolling lines on the monitor, or in severe cases, interaction artifacts between the deflection circuits and the game logic.

### Monitor Chassis Types and Signal Topology

The monitor is simultaneously the most valuable, most dangerous, and most electrically demanding subsystem in the cabinet. CRT monitors used in arcade machines fall into three broad categories defined by their deflection frequency: **fixed-frequency monitors**, **medium-resolution monitors**, and **multi-sync or multi-frequency monitors**.

Fixed-frequency monitors, which dominated the industry through the mid-1980s, are designed to sync to exactly one horizontal and vertical frequency — typically 15.75 kHz horizontal and 60 Hz vertical, the same as standard NTSC composite video. Wells-Gardner, Electrohome, and Sanyo produced the most common variants of this type. These monitors expect a 1 V peak-to-peak composite sync or separate H/V sync signals within a narrow tolerance window; feed them the wrong frequency and the deflection circuits will simply refuse to lock, producing a collapsed or wildly scrolling raster.

Medium-resolution monitors, which became common from roughly 1986 with the spread of hardware running 24 kHz horizontal scan rates (Atari System 1, early Capcom, and many Neo-Geo titles), require a chassis designed for that frequency range and will not accept standard 15 kHz signals. The practical consequence for the restorer is that a PCB and a monitor chassis that are both individually functional can produce no image at all when combined, because their sync frequencies are incompatible. Before connecting any PCB to a cabinet, verify the board's video output frequency against the monitor chassis's rated scan range. This information is available in the chassis service manual and in the PCB's technical documentation.

The Wells-Gardner K7000 and the Electrohome G07 are the two chassis types a working restorer will encounter more than any other, and they merit specific understanding. The G07 is a fixed-frequency chassis with a reputation for reliability disrupted by one endemic failure: the solder joints on the deflection yoke connector and the high-voltage transformer secondary develop cold joints over time due to the thermal cycling from the chassis's proximity to its own heat sources. The symptom is an intermittent collapsed vertical or a raster that folds on one side — not a component failure, just a solder joint that needs to be reflowed. The K7000 family has a different characteristic failure in the vertical output IC, typically a TDA1170 or equivalent, that fails thermally. The IC runs hot, the original thermal compound dries out, the junction temperature climbs until the device fails short, and the vertical deflection collapses to a single bright horizontal line. That bright line, left unaddressed, will burn a permanent phosphor stripe across the face of the tube within minutes.

### PCB Slot Configurations and the JAMMA Connector

The JAMMA edge connector is a 2×28 position (56-pin total) PCB edge connector with 2.54 mm pin spacing, designed to mate with a standard 0.062-inch PCB edge. The pinout allocates power rails on the first several positions of each side, then transitions to video signals, audio, coin inputs, player controls, and service switches. The video signals carried are analog RGB — separate red, green, and blue signals each at approximately 0 to 5 V — along with a composite sync signal. This is a fundamentally different signal topology from consumer composite or S-Video; a JAMMA PCB cannot be directly connected to a consumer television without an active RGB-to-composite converter.

The control inputs on the JAMMA connector are active-low logic signals. Each button or joystick direction connects between the JAMMA pin and cabinet ground; when the button is pressed, it closes the circuit and pulls the signal to ground, which the PCB's input logic reads as a logic LOW and interprets as an active input. This means that any break in the ground path — a corroded connector pin, a broken wire in the harness, a failed crimp — manifests as a permanently inactive control, while a short to ground manifests as a permanently active one. Diagnosing a stuck-left joystick condition, for example, begins by measuring continuity from the joystick microswitch common terminal to the cabinet chassis ground, not by measuring voltage at the JAMMA pin.

```
JAMMA Connector Partial Pinout (Component Side / Solder Side)

Component Side (A)          |  Pin  |  Solder Side (B)
----------------------------|-------|-----------------------------
GND                         |   1   |  GND
GND                         |   2   |  GND
+5 VDC                      |   3   |  +5 VDC
+5 VDC                      |   4   |  +5 VDC
-5 VDC                      |   5   |  -5 VDC
+12 VDC                     |   6   |  +12 VDC
Key (no pin)                |   7   |  Key (no pin)
Coin Counter 2              |   8   |  Coin Counter 1
Coin Lockout 2              |   9   |  Coin Lockout 1
Speaker (-)                 |  10   |  Speaker (+)
Video Green                 |  11   |  Video Red
Video Sync                  |  12   |  Video Blue
Service Switch              |  13   |  Video GND
Tilt Switch                 |  14   |  Test Switch
Coin Switch 2               |  15   |  Coin Switch 1
P2 Start                    |  16   |  P1 Start
P2 Up                       |  17   |  P1 Up
P2 Down                     |  18   |  P1 Down
P2 Left                     |  19   |  P1 Left
P2 Right                    |  20   |  P1 Right
P2 Button 1                 |  21   |  P1 Button 1
P2 Button 2                 |  22   |  P1 Button 2
P2 Button 3                 |  23   |  P1 Button 3
GND                         |  28   |  GND
```

Beyond standard JAMMA, several platform-specific extensions add non-standard signals through the same connector or through secondary connectors. Capcom's CPS-1 and CPS-2 systems add a kick harness — a secondary 10-pin connector that breaks out buttons 4 through 6 for each player — which the standard JAMMA pinout does not accommodate. Neo-Geo MVS adds memory card and mahjong panel interfaces through secondary connectors on the motherboard. Konami's System 573 uses a CD-ROM drive and security cartridge. Each of these platform extensions requires the restorer to source or fabricate the appropriate secondary harness in addition to the standard JAMMA connection.

### Coin Mechanism Operation

The coin mechanism is an electromechanical assembly that accepts, validates, and counts currency. The mechanism performs three physical operations in sequence: it accepts the coin and routes it down a chute past a validation gate, the validation gate rejects slugs and foreign coins by testing diameter, thickness, and in more sophisticated mechanisms, electrical conductivity, and upon accepting a valid coin, it mechanically actuates a microswitch that sends a momentary ground pulse to the JAMMA Coin Switch pin. The coin counter solenoid — a separate circuit that advances a physical electromechanical counter for revenue accounting — is simultaneously pulsed from the JAMMA Coin Counter pin.

Mech failures divide into two categories. Physical failures — worn rejection fingers, bent chute guides, broken actuator levers — require disassembly, inspection, and either parts replacement or gentle reshaping with needle-nose pliers. Electrical failures are almost always the microswitch itself: the contacts oxidize after years of operation and the switch fails to make clean contact on coin insertion, leaving the game registering no credit despite the coin physically passing through. Resistance across the switch contacts should measure below 0.5 Ω in the closed position; anything above 2 Ω indicates contact oxidation that can frequently be remediated by working the switch through several hundred actuations with a small amount of contact cleaner applied to the gap.

---

## 3. High-Performance Optimization & Failure Modes

### Systematic Power-Up Protocol

The single most consequential workflow decision a restorer makes is the order in which they energize a machine during initial restoration. Connecting a fully loaded JAMMA harness to an unknown PCB and throwing the breaker is an approach that destroys components and obscures the actual fault source. The correct sequence proceeds in stages, verifying each subsystem before introducing load from the next.

Begin by powering the cabinet with the PCB disconnected from the JAMMA harness. With a calibrated digital multimeter set to DC volts, measure each power rail at the JAMMA connector pins with the full cabinet load — monitor, coin mechanism solenoids, any lighting — drawing current, but without the PCB. The +5 V rail must read between 4.95 V and 5.10 V. The +12 V rail must read between 11.8 V and 12.2 V. If you have a negative rail, verify -5 V is within ±0.1 V. Any deviation from these ranges must be corrected before the PCB is connected. On adjustable switching supplies, there is typically a small trimmer potentiometer accessible through a hole in the supply housing; adjust it with a ceramic-tipped trimmer tool (never a metal screwdriver, which risks shorting to live conductors) while monitoring the output with the meter. On linear supplies, the regulation is set by the regulator IC itself; voltage deviation on a linear supply under load indicates either a failing pass transistor or more commonly, dried-out filter capacitors that have lost sufficient capacitance to suppress ripple adequately.

Before connecting the PCB, use a smoke stopper — a series-connected incandescent lamp of 60 to 100 W in line with the +5 V supply — during first power-on with the board installed. If the board has a dead short anywhere on its +5 V rail, the lamp will illuminate brightly and clamp the voltage before the PCB's traces or components suffer thermal damage. If the board draws normal current, the lamp will illuminate dimly or not at all, and you can proceed to bypass it. This is not a step to skip because the PCB "looks clean." Dead shorts from failed bypass capacitors, shorted voltage regulator ICs, or damaged RAM are not visible to the naked eye.

### Harness Inspection and Recrimping

The wiring harness is the spinal cord of the machine and is treated with insufficient respect in most restoration documentation. After thirty years, the PVC insulation on the harness wires becomes brittle and cracks when flexed, exposing conductors that can short against each other or against the metal cabinet chassis. The connector housings — typically Molex KK or AMP/TE series — develop oxidation on the contact surfaces and lose spring tension, producing high-resistance connections that cause intermittent control inputs, voltage sag under load, and audio noise.

A thorough harness inspection begins at the JAMMA connector itself. Remove the connector from the PCB edge and examine every contact under magnification. Contacts should be bright and free of green or white oxidation. Each contact's retention tang should be properly seated in the housing. Measure resistance from each power and ground pin through to the corresponding terminal at the power supply — anything above 0.3 Ω on a power or ground conductor is excessive and indicates either a corroded crimp or a damaged wire that must be re-terminated. For control wiring, continuity from each JAMMA control pin through the harness to the corresponding microswitch common terminal should read below 1 Ω.

When re-terminating connectors, use the correct Molex or AMP hand crimping tool for the contact type rather than general-purpose crimpers. The correct tool produces a gas-tight cold-weld between the wire conductor and the contact barrel that cannot be reproduced with pliers or incorrect tooling. A crimp connection made with incorrect tooling may read acceptable resistance initially but will develop high resistance within months as the mechanical grip relaxes and oxidation forms at the interface.

### Monitor High-Voltage Safety and Chassis Failure Modes

Working inside a CRT monitor chassis is the highest-risk procedure in arcade restoration and demands explicit safety practices. The flyback transformer produces the anode voltage — typically 25,000 to 30,000 V DC — that is stored in the aquadag capacitance of the CRT itself. This charge persists for hours or days after the monitor is powered down. Before any contact with internal monitor components, discharge the anode by inserting the probe of an HV discharge tool (a resistor of approximately 1 MΩ in series with an alligator clip connected to chassis ground) under the suction cup anode connector until no spark is produced. Then verify with a high-voltage probe that the anode reads below 500 V before proceeding. A 25 kV discharge through the hand and across the chest is not a survivable event.

The endemic failure modes of the two most common chassis types bear systematic cataloging for the working restorer. The Electrohome G07 fails predictably at three nodes: the degaussing thermistor develops open-circuit failure that leaves the monitor with persistent purity errors (color non-uniformity across the face), the vertical output section fails thermally due to insufficient original heatsinking, and the focus/screen voltage divider network in the flyback assembly drifts with age, producing a raster that cannot be focused to a sharp image regardless of the focus potentiometer adjustment. The vertical failure in the G07 presents as a 2 to 3 cm horizontal bright stripe across the center of the display rather than a full collapsed line, distinguishing it from the K7000's TDA1170 failure which produces a single-pixel-width line.

The Wells-Gardner K7000 family has its own consistent failure signature: the HOT (Horizontal Output Transistor), typically a 2SC3688 or equivalent, fails when the high-voltage section's B+ regulation drifts. The symptom is a sudden loss of image with the chassis going into protective shutdown, sometimes accompanied by a sharp crack from the flyback region. Before replacing the HOT, measure B+ voltage at the collector of the existing transistor (carefully, with the chassis energized via an isolation transformer and all appropriate precautions) — it should read between 115 V and 125 V. A reading above 130 V indicates a drifted B+ regulator that must be corrected before the replacement transistor is installed, or the new part will fail within the same operating cycle.

### Control Panel Wiring Standards and Ground Loop Elimination

The control panel wiring standard on JAMMA machines uses a common ground bus running the full length of the control panel, with individual wires from each microswitch's normally-open terminal routing back to the JAMMA connector. The common terminal of each switch connects to the ground bus, and the normally-open terminal connects to its assigned JAMMA control pin. When the switch closes, it pulls the JAMMA pin to ground.

The most common failure pattern is a broken or corroded connection in the ground bus itself, which can manifest as multiple simultaneous control inputs failing. Because the ground bus is shared, a single broken point in the chain disables every switch downstream of the break. When diagnosing multiple simultaneous control failures, measure continuity from the JAMMA ground pin (pins 1, 2, and 28) through to the switch common terminals, rather than individually probing each control signal. Restoring this ground continuity frequently resolves what appeared to be multiple independent failures.

Hum bars and rolling interference in the monitor image, when correlated with control input activity, indicate that the control panel ground bus is not bonded to the cabinet chassis ground at the same node as the monitor chassis ground. This creates a small but measurable ground potential difference between the two subsystems, which modulates the monitor's sync signals at the frequency of the interference. The fix is to add a dedicated bonding wire from the control panel ground bus to the cabinet chassis metal, ensuring all ground references converge at a single star-ground point before connecting to the power supply common.

### PCB Fault Diagnosis Workflow

A systematic fault diagnosis workflow for a non-booting JAMMA PCB proceeds in a defined sequence that avoids the random component-replacement approach that wastes time and destroys evidence.

First, power the board via the smoke stopper and observe. A brightly lit stopper indicates a hard short on the +5 V rail; scope the rail to identify which supply node is shorted by lifting sections of the board's supply distribution. Second, if the board powers without obvious current fault but produces no video, verify the video signals at the JAMMA pins with an oscilloscope: you should see analog RGB signals between 0 and 5 V with appropriate waveform activity, and a sync signal on the composite sync pin. The absence of all video signal activity with correct power rails points to the CPU section — a failed CPU, a failed program ROM, or a failed address decoder. The presence of video signals that are static (non-changing waveforms) points to a CPU that is running but not executing code, which is typically caused by failed RAM.

The logic probe is an underused tool in arcade diagnostics. Connected between the PCB's +5 V and GND rails, it distinguishes between logic high, logic low, and pulsing states on individual IC pins. Apply it to the CPU's clock input first — a non-pulsing clock input means the oscillator circuit has failed and the entire board is static regardless of the state of any other component. Apply it next to the CPU's /RESET pin; this should pulse briefly at power-on and then settle to a logic high state. A /RESET pin that remains low indicates that the reset supervisor circuit is holding the CPU in reset, which is usually caused by the +5 V rail reading below the reset supervisor's threshold voltage — which returns the diagnosis to the power supply section.

This recursive, signal-path-following approach — always tracing from the power rails outward through the clock and reset network into the CPU execution path, then into the memory bus, then into the video generation section — transforms arcade PCB diagnosis from an exercise in guesswork into a systematic engineering workflow. It is the approach that distinguishes the restorer who reliably brings machines back to life from the one who replaces parts until something works. The machine always has a reason it is not functioning, and that reason is always traceable if you follow the signals.
