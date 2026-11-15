# Lesson 1: Motor Types, Power Sources, Electrical Fundamentals

## 1. First-Principles Intuition & Invariants

Every motorized LEGO creation begins with the same deceptively simple question: where does the motion come from, and how much of it can you sustain before the system collapses under its own ambition? Before you route a single axle or snap a gear to a motor shaft, you need to build a physical intuition for what a DC brushed motor actually is — not as an abstract circuit component, but as a machine that trades electrical energy for mechanical rotation, always at a cost.

A brushed DC motor operates on the Lorentz force principle. When current flows through a coil of wire sitting inside a magnetic field, the interaction between the current-carrying conductor and the field generates a force perpendicular to both. In a motor, this force produces a torque that spins the armature. The brushes — small carbon contacts — maintain electrical continuity between the stationary power supply and the rotating coil by rubbing against a segmented copper commutator ring. This continuous commutation is what sustains rotation, but it also introduces resistive losses as heat, mechanical wear, and electromagnetic noise. Every LEGO motor from the original 9V train motors of the 1990s through the latest Powered Up Smart Hub actuators uses this same fundamental architecture at its core.

The critical invariant every practitioner must internalize is the torque-speed tradeoff. A DC motor's behavior is governed by two extreme operating points: stall torque and free-run speed. At stall — when the motor shaft is physically prevented from turning — current draw is at its maximum and torque output is highest, but rotational speed is zero. At free-run — when the shaft spins completely unloaded — speed is at its maximum but torque output drops to nearly zero. Between these two extremes, every real operating condition lives on a linear torque-speed curve. Understanding where your design forces the motor to operate on that curve is the difference between a build that runs smoothly under load and one that browses, stutters, and browns out the battery pack in thirty seconds.

LEGO has iterated on motor design across four distinct electrical generations, and each generation imposes its own constraints on voltage, current, and system compatibility. The original 9V system, introduced in 1991, ran motors and lights from a dedicated 9V battery box and used flat metallic contacts embedded into studded surfaces to deliver power through the brick matrix itself. It was elegant but fragile — contact resistance increased with contamination, and the topology limited routing flexibility. The Power Functions (PF) system launched in 2007 replaced conductive bricks with a cable-based four-wire connector carrying two power lines and two reserved lines for future use. Power Functions standardized on 9V from a fresh AA battery box (six AAs in series), offering a clean, robust interconnect that could tolerate the mechanical abuse of LEGO builds. The Powered Up (PU) system, introduced with LEGO Boost and later Technic Control+ sets around 2018, made the decisive shift to smart motors and digital communication. Rather than receiving raw voltage and spinning at whatever rate physics dictates, Powered Up motors contain integrated encoders that report shaft position back to the hub, enabling closed-loop speed and position control. The connector physically resembles the PF connector but is electrically incompatible — a decision that frustrated many practitioners during the transition period, though third-party adapter cables are now widely available.

Understanding polarity is non-negotiable before you wire anything. LEGO DC motors are reversible: swap the positive and negative supply leads, and the shaft spins in the opposite direction. This is not a feature to discover accidentally inside a finished model. The PF and PU connectors encode polarity by their physical key shape, but once you are driving motors from a custom Power Functions IR receiver or a third-party BuWizz hub, you must verify shaft direction before integrating the motor into a drivetrain. A reversed motor in a differential or a rack-and-pinion mechanism does not simply spin backward — it fights against the mechanical linkage, dramatically increasing current draw and potentially stripping gears.

---

## 2. Core Architecture & Mechanics

### The LEGO Motor Family: Specifications and Character

The M-Motor (part 8883 in PF, and the similarly sized motor in Powered Up form as part 88008) is the workhorse of compact LEGO builds. It is small enough to integrate into tight chassis geometries, draws approximately 100–150 mA under moderate load, and produces enough torque for light-to-medium drivetrain applications when geared appropriately. Its free-run speed at 9V is roughly 380 RPM at the output shaft. For a vehicle build, this is typically too fast for direct drive and too slow for high-speed racing without a gear-up stage — which is exactly the kind of tradeoff that makes motor selection an architectural decision, not an afterthought.

The L-Motor (part 88003 in Powered Up, formerly 8882 in Power Functions) is the standard choice for primary drive and actuation duties. It is physically larger, with a wider stator cross-section that allows more copper windings and a stronger magnetic circuit. At 9V it produces substantially more torque than the M-Motor — approximately 40 N·cm at stall versus the M-Motor's roughly 14 N·cm — but its free-run speed drops to around 175 RPM at the output shaft. The implication is straightforward: the L-Motor delivers more torque per gram of motor mass, making it appropriate for mechanisms that must move structural loads, lift payloads, or drive large-wheeled vehicles that encounter terrain resistance. Its current draw under load can reach 400–500 mA, which matters significantly when planning a battery budget.

The XL-Motor (part 8882 in Power Functions, 88014 in Powered Up) is the high-torque outlier in the LEGO catalog. Its stall torque exceeds 50 N·cm, and it is the correct choice when you are driving very high gear reduction systems, powering a winch under tension, or running a large tracked vehicle with significant rolling resistance. However, the XL-Motor demands respect in power budgeting. Under stall conditions or sustained heavy load, it can draw close to 1A from the supply rail — a figure that, when two XL-Motors share a single battery box, can discharge a fresh set of AA alkaline cells in under fifteen minutes of active use. Building with XL-Motors without understanding battery capacity is how ambitious projects die mid-demonstration.

The Powered Up Smart Motors deserve their own conceptual category, because they do not behave like passive actuators. The Powered Up Medium Linear Motor (88008) and the Technic Large Angular Motor (88013) each contain a quadrature encoder — a pair of optical or magnetic sensors that detect shaft rotation in discrete increments. This encoder data is transmitted back to the hub over the connector's data lines, allowing the hub's firmware to implement position control. When you command a Powered Up motor to rotate 90 degrees and hold, the hub is running a software PID loop: it reads encoder position, computes the error between actual and target position, and adjusts motor drive voltage to close that error. This closed-loop behavior is what makes Powered Up builds capable of repeatable, precise movements that Power Functions systems simply cannot achieve without external sensors.

```
Motor Family Specification Reference

┌────────────────────────┬──────────────┬────────────────┬──────────────┬─────────────────┐
│ Motor                  │ System       │ Stall Torque   │ No-Load RPM  │ Rated Current   │
├────────────────────────┼──────────────┼────────────────┼──────────────┼─────────────────┤
│ M-Motor (8883/88008)   │ PF / PU      │ ~14 N·cm       │ ~380 RPM     │ ~100–150 mA     │
│ L-Motor (8882/88003)   │ PF / PU      │ ~40 N·cm       │ ~175 RPM     │ ~300–500 mA     │
│ XL-Motor (8882/88014)  │ PF / PU      │ ~50+ N·cm      │ ~100 RPM     │ ~600–900 mA     │
│ Servo Motor (88004)    │ PU           │ ~18 N·cm       │ N/A (±90°)   │ ~250 mA         │
│ Angular Motor (88013)  │ PU (Control+)│ ~25 N·cm       │ ~135 RPM     │ ~300–400 mA     │
└────────────────────────┴──────────────┴────────────────┴──────────────┴─────────────────┘

All values at nominal 9V / 7.4V LiPo supply. Measured under moderate resistive load.
Stall torque figures are at the output shaft, after internal gear reduction where present.
```

### Battery Systems and Power Budgeting

The battery source defines the ceiling of everything your motorized system can do. LEGO offers three primary power configurations that practitioners work with in real builds: the AA battery box, the Powered Up Smart Hub's integrated LiPo pack, and third-party hubs such as the BuWizz 3.0 or SBrick Plus.

The standard six-AA Power Functions battery box (part 8881) delivers a nominal 9V from fresh alkaline cells. In practice, alkaline AA cells under load drop their terminal voltage quickly. A fresh set of Duracell AA cells measures close to 9.1V at no load; under a 500 mA drain from a single L-Motor at moderate load, that voltage sags toward 7.5–8V within the first few minutes. As the cells discharge toward depletion, the voltage continues to drop, and your motors slow down perceptibly. For build demonstrations and static testing, this is acceptable. For competitions, exhibitions, or any build where consistent motor speed matters, you must either use lithium AA cells (which hold their voltage curve far more flatly across discharge) or switch to a LiPo-based hub.

The Powered Up Smart Hub (88009) houses an integrated 7.3V lithium polymer cell with approximately 1000 mAh capacity. LiPo cells have a flatter discharge curve than alkaline chemistry, meaning your motors receive a more consistent voltage supply until the cell approaches exhaustion, at which point it drops quickly. The 1000 mAh capacity with two L-Motors running at moderate load — drawing perhaps 400 mA combined — gives you roughly 90 to 120 minutes of active run time, though high-torque applications with XL-Motors can cut this to under 45 minutes. The Smart Hub charges via USB-C, which makes field recharging practical in a way that AA battery boxes are not.

The BuWizz 3.0 is a third-party hub that is physically compatible with Power Functions connectors but delivers a programmable output voltage from 3.5V up to 11.1V from an internal LiPo pack. At maximum voltage, LEGO motors significantly exceed their rated speed — an L-Motor that runs at 175 RPM at 9V will approach 215 RPM at 11V, and stall torque increases proportionally with voltage. This is the preferred configuration for competitive builds where maximum speed or force output is required, but the practitioner must understand that running motors above their design voltage accelerates brush wear and thermal stress. It is a deliberate tradeoff, not a free upgrade.

### Circuit Completion and Connector Architecture

The Power Functions connector uses a four-pin Dupont-style arrangement
