# Lesson 4: Transmission Architecture

## 1. First-Principles Intuition & Invariants

The transmission exists because the internal combustion engine is a fundamentally compromised power source. It produces useful torque only within a narrow band of crankshaft speeds, yet the rear wheel must deliver traction across an enormous range of road speeds — from a standing start to terminal velocity on a straight. The gearbox is the mechanical intelligence that bridges this contradiction. Understanding it at the level a race engineer must means internalizing not just the ratios themselves, but the physics of how power flows through each mesh, how inertia resists every shift, and how the entire drivetrain from primary drive to rear contact patch behaves as a coupled dynamic system.

### The Gear Ratio as a Force Amplifier

Every gear ratio in the gearbox is fundamentally a torque multiplication device paired with a speed reduction. When a rider selects first gear with a ratio of, say, 2.46:1, the output shaft rotates once for every 2.46 revolutions of the input shaft. The tradeoff is exact: torque at the output is multiplied by 2.46 (minus mechanical losses), while rotational velocity at the output is divided by the same factor. This reciprocal relationship is not a convenience of engineering — it is a direct consequence of conservation of energy. No gearbox creates power; it only transforms the relationship between torque and angular velocity while dissipating a small fraction as heat in the gear mesh and bearings.

The practical consequence for a race engineer is this: gear ratio selection determines where in the engine's power curve the rider is operating at any given corner exit, and therefore determines how aggressively the rear tire can be loaded in traction. An engine producing peak torque at 9,500 RPM with a narrow powerband demands tighter ratio spacing so the rider never drops below that threshold between upshifts. A broader torque curve permits wider spacing, which reduces shift frequency and allows the rider to focus on cornering mechanics rather than managing the gearbox.

The total reduction from crankshaft to rear wheel is the product of three cascaded ratio stages: the primary drive ratio, the gearbox internal ratio, and the final drive ratio. For a Superbike-class machine, a typical chain of values might look like a primary drive of 1.84:1 (achieved through the crank sprocket and basket gear), an internal first gear of 2.46:1, and a final drive sprocket combination of 17 teeth driving at the front and 42 at the rear, yielding a final drive ratio of 2.47:1. The overall reduction in first gear is therefore $1.84 \times 2.46 \times 2.47 = 11.17:1$. At 10,000 RPM, the crankshaft is turning 10,000 times per minute, while the rear wheel hub turns at $10{,}000 / 11.17 \approx 895$ RPM. With a rear tire of 190/55 ZR17, the rolling radius is approximately 303 mm, giving a theoretical road speed of roughly 101 km/h in first gear at the rev limiter. These calculations are not academic — they are the foundation of gearbox specification on any bike competing in a sprint series or endurance race.

### The Gear Cluster Architecture: Constant Mesh and Dog Engagement

Unlike the sliding mesh gearboxes of early automotive design, every modern motorcycle gearbox operates on the constant mesh principle. All gear pairs on both the input and output shaft are perpetually in mesh — the teeth never disengage. What changes between ratios is which of those pairs is locked to its shaft for torque transmission. This is achieved through the dog engagement system: each gear wheel has a set of dogs (typically four to six rectangular or profiled projections) machined on its face. A corresponding selector dog ring, splined to the shaft and free to slide axially, carries matching dog pockets. When the selector ring slides into contact with a gear wheel's dogs, the gear wheel becomes rotationally locked to the shaft, and that ratio becomes live.

The critical insight here is that all the other gear pairs on the same shaft are freewheeling on their needle roller bearings at that moment. They are spinning, meshed, and loaded to some degree by windage and bearing friction, but they are not transmitting drive torque. This is why a constant mesh gearbox is mechanically silent in a way that a sliding mesh design is not — the gear teeth never clash during ratio changes, only during the moment of dog engagement.

Dog engagement geometry has profound consequences for shift quality and durability. Standard production bikes use square-cut dogs, which are strong and cheap to manufacture but prone to "jumping out" of gear under load because the flat-faced dogs can ride up over each other when the torque direction reverses (e.g., during aggressive engine braking). Racing gearboxes address this with undercut dogs, where the dog face is angled inward by three to five degrees, creating a self-locking geometry under load. The undercut causes the dogs to pull themselves deeper into engagement rather than skating out. The tradeoff is that undercut dogs require a positive, deliberate shift input to disengage — they will not gracefully tolerate half-engaged positions, which is entirely acceptable in a racing context where the rider commands every shift with intention.

### Gear Selection Mechanism: The Drum and Fork Assembly

The rider's left foot does not directly move selector dog rings. The gear pedal inputs into a ratchet mechanism that rotates a cylindrical gear selector drum by one indexed position per actuation. Around the circumference of this drum are precision-machined helical grooves — typically three grooves for a six-speed unit, one controlling each pair of selector forks. As the drum rotates, pins riding in these grooves are displaced axially, and the selector forks attached to those pins slide their corresponding dog rings along the shaft to engage the target gear.

The drum groove profiles are not arbitrary. Each groove is a cam profile carefully designed to move the outgoing selector away from its current engagement slightly before the incoming selector reaches full engagement, preventing a momentary simultaneous engagement of two ratios — an event that would lock the gearbox solid and potentially destroy the engine casing. The transition window, the zone where neither gear is fully engaged, is kept as brief as possible to minimize the time during which the transmission has zero torque path.

A sequential gearbox enforces that the drum can only rotate in one-step increments, enforcing the 1-N-2-3-4-5-6 order of a street motorcycle, or in many race applications a 1-2-3-4-5-6 straight sequential pattern without neutral between first and second. This sequential constraint is what distinguishes a motorcycle gearbox from a true transverse sequential unit as found in Formula cars, though the dog-ring engagement principle is identical.

---

## 2. Core Architecture & Mechanics

### Primary Drive: Wet Clutch Basket and Crank Interface

Power leaves the crankshaft through the primary drive before it even reaches the gearbox. On the vast majority of motorcycle engines, this is a straight-cut or helical gear set housed in a wet, oil-bathed chamber on the left side of the engine. The crank-side gear is relatively small, the clutch basket gear is significantly larger, and the ratio between them (typically 1.7:1 to 2.0:1) performs the first stage of reduction. This reduction is fixed and cannot be adjusted at the track without replacing the gears themselves — it is therefore a design parameter rather than a tuning variable. Some older British and Italian designs used a primary chain rather than a gear set, which allowed for ratio adjustment by swapping sprockets, but gear primary drives are universal in modern performance applications due to their precision, low maintenance, and compact packaging.

The clutch basket itself is an aluminum or steel drum that is driven by the primary gear and freewheels on the input shaft until the clutch is engaged. Inside the basket sit the friction plates, which are splined to the basket and therefore rotate with it at all times. Interleaved with the friction plates are the steel drive plates, which are splined to the clutch hub, which is in turn splined to the gearbox input shaft. The clutch spring pack — either coil springs arranged around the pressure plate or a single Belleville washer stack in some racing designs — clamps these two sets of plates together. When clamped, friction coupling between the basket (driven by the crank) and the hub (driving the gearbox) transmits torque. When the lever is pulled, the pressure plate retracts, the plates separate, and the coupling is broken.

```
CRANKSHAFT
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ PRIMARY DRIVE (Fixed Gear Reduction: ~1.84:1)             │
│   Crank Gear ──────────► Clutch Basket Gear               │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ WET MULTI-PLATE CLUTCH                                    │
│   Friction Plates (splined to Basket)                     │
│   Steel Drive Plates (splined to Hub / Input Shaft)       │
│   Spring Pack clamps assembly │ Lever releases pressure   │
└───────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────┐
│ CONSTANT MESH GEARBOX (6 speeds shown)                    │
│                                                           │
│  Input Shaft:  [1st] [3rd] [5th] [2nd] [4th] [6th]       │
│                  │     │     │     │     │     │          │
│                  mesh  mesh  mesh  mesh  mesh  mesh       │
│                  │     │     │     │     │     │          │
│ Output Shaft:  [1st] [3rd] [5th] [2nd] [4th] [6th]       │
│                                                           │
│  Selector Drum ──► Fork A ──► Dog Ring (1st/2nd)          │
│                ──► Fork B ──► Dog Ring (3rd/4th)          │
│                ──► Fork C ──► Dog Ring (5th/6th)          │
└───────────────────────────────────────────────────────────┘
    │
    ▼
OUTPUT SHAFT SPROCKET
    │
    ▼
FINAL DRIVE (Chain, Belt, or Shaft)
    │
    ▼
REAR WHEEL HUB
```

The gear pairs are intentionally arranged in an interleaved order on each shaft (1st, 3rd, 5th on the input side; 2nd, 4th, 6th adjacent) so that consecutive ratios are never axially adjacent to one another. This arrangement shortens the axial travel required of each fork during sequential shifts and provides sufficient clearance between dog ring positions to prevent simultaneous engagement.

### Clutch Engagement Theory: Slip, Friction, and Heat

Clutch engagement is a controlled slip event. The energy dissipated during engagement equals the product of the torque transmitted, the differential angular velocity between basket and hub, and the duration of that differential. At race starts, this energy is enormous — a 190 kg Superbike launching from a 12,000 RPM clutch drop can dissipate tens of kilojoules of energy into the friction plates in under two seconds. The oil bath provides cooling, the aluminum basket provides thermal mass, and the friction material — typically a sintered bronze or paper-based compound — is engineered to maintain a stable friction coefficient across this temperature range.

The friction coefficient $\mu$ of the clutch plates is not a fixed value. It is a function of contact pressure, surface velocity, oil type, oil temperature, and surface topography. At low contact pressure and high slip velocity (the condition at the onset of a launch), $\mu$ is lower than at high pressure and low slip velocity. This is why a progressive clutch engagement feels smooth — the initial low-$\mu$ phase controls the initial torque ramp, and as the plates come up to speed and pressure increases, $\mu$ rises and the coupling stiffens. A rider who dumps the clutch lever abruptly forces the system through this curve instantaneously, which either stalls the engine (if the inertia of the motorcycle exceeds the peak clutch torque at that RPM) or produces a violent rear-wheel spike that breaks traction.

Race teams managing launch control map this engagement curve in the ECU not to replace clutch control but to assist it. The ignition cut or throttle reduction in the first 50–200 milliseconds of a launch is calibrated to match the progressive torque delivery of a skilled clutch release. The clutch itself is not automated — the rider still commands engagement — but the engine torque output is shaped to match what the contact patch can accept given the measured wheel speed delta and launch RPM.

### Slipper Clutch and Back-Torque Limiting

Under aggressive downshifting into a corner, the engine acts as a brake through the drivetrain. If the rider selects a gear whose ratio demands a much higher crankshaft speed than the current engine RPM, the drivetrain fights the rear wheel — the engine tries to slow the wheel below the speed the chassis dynamics and the tire's current slip angle can support. The result is rear wheel hop, chatter, or a snap oversteer event as the rear tire momentarily locks and then rebounds.

The slipper clutch, also called a back-torque limiter, addresses this by allowing the clutch to slip in one torque direction only. A ramp mechanism built into the clutch hub generates an axial separation force under back-torque conditions (engine braking direction), partially unloading the pressure plate and allowing the plates to slip just enough to limit the decelerating torque transmitted to the rear wheel. Under drive torque (the normal direction), the ramp loads the clutch harder, increasing clamping force above the mechanical spring preload. This means a slipper clutch transmits higher peak drive torque than its spring rating alone would suggest, which is a secondary benefit often overlooked.

The ramp angle determines the aggressiveness of the slip onset. Shallow ramp angles (28–32°) produce an earlier, gentler slip onset — appropriate for lower-powered machines or wet conditions. Steeper ramp angles (38–45°) allow more back-torque to reach the rear wheel before slipping, which some riders prefer for engine braking feel and cornering stability. MotoGP teams take this further with hydraulically actuated slipper systems that allow real-time adjustment of back-torque limiting from the handlebar, independent of the ramp geometry.

### Final Drive Options: Chain, Belt, and Shaft

The output shaft sprocket connects to the rear wheel through one of three final drive configurations, each with distinct mechanical characteristics, maintenance demands, and dynamic behaviors that matter deeply to anyone setting up a performance motorcycle.

The roller chain remains the dominant choice in performance and racing applications for one compelling reason: ratio flexibility. Changing the rear sprocket by one tooth changes the final drive ratio, and therefore the character of every gear in the box, in under ten minutes. This adjustability is irreplaceable at a circuit where gearing strategy depends on the longest straight, the slowest corner, and the powerband characteristics of the engine on that day's temperature and atmospheric pressure. A chain drive also absorbs small drivetrain shocks through the elastic deformation of the link side plates and the compliance of the rubber O-ring seals between link plates, acting as a torsional damper with a time constant in the millisecond range. The mass of the chain is low, contributing minimally to rotational inertia at the rear wheel.

The toothed belt, as used in Buell and Harley-Davidson touring applications, offers lower maintenance, quieter operation, and no lubrication requirement. The rubber-reinforced belt cannot match the load capacity of a chain at equivalent cross-section for high-output engines above approximately 100 Nm, and ratio adjustment requires swapping both sprockets (called pulleys in belt systems), making trackside gearing changes slow and expensive. Belts are therefore absent from competition contexts where gearing agility matters.

The shaft drive, found on BMW Boxer twins, the Honda Gold Wing, and large-displacement tourers, eliminates the chain and sprocket entirely in favor of a bevel gear set at the rear wheel. The engineering tradeoffs are significant in both directions, and the shaft drive's torque reaction effect on chassis dynamics deserves detailed treatment.

### Shaft Drive Torque Reaction: Paralever and the Physics of the Lurch

When torque is transmitted through a driveshaft to a bevel ring gear at the rear axle, Newton's third law imposes a reaction torque on the final drive housing — and therefore on the rear subframe and swingarm. This reaction torque acts around the longitudinal axis of the shaft. Under acceleration, the reaction tries to rotate the left side of the motorcycle downward and the right side upward, manifesting as a visible rear squat on the left and suspension extension on the right. Under deceleration, the reaction reverses. The rider experiences this as a rhythmic pitching or lurching sensation during throttle transitions that has no equivalent on a chain-drive machine.

BMW's Paralever system (introduced in 1987 on the R80GS) addresses this by separating the torque-transmitting bevel gear housing from the swingarm pivot axis. A secondary link arm connects the rear axle carrier to the main frame, distributing the torque reaction across a geometry that cancels the lurching moment rather than transmitting it into the chassis. The result is a shaft-drive motorcycle whose handling under throttle transitions much more closely approximates the neutral behavior of a chain-drive machine. Moto Guzzi's CARC (Compact Reactive Chassis) system takes a similar geometric approach with a different implementation, using a single-sided swingarm with an integrated bevel housing that pivots on a torque reaction arm.

For a race engineer evaluating a shaft-drive platform, the key diagnostic is to measure longitudinal acceleration sensitivity of rear ride height under step throttle inputs. A well-implemented Paralever shows less than 5 mm of ride height change between full off-throttle and full on-throttle at a given speed. A poorly calibrated or worn system can show 15–20 mm of variation, which directly corrupts the aerodynamic pitch attitude and rear contact patch load, undermining tire performance consistency.

---

## 3. High-Performance Optimization & Failure Modes

### Gear Ratio Stacking Strategy: Circuit-Specific Gearing Optimization

The process of selecting final drive and gearbox ratios for a specific circuit begins with a minimum-corner-speed analysis. The race engineer pulls the data logger's GPS speed trace and identifies the five lowest-speed points on the lap — these are the apexes from which the engine must pull hardest. The objective is to place the engine at or just above its peak torque RPM at each of those apex speeds in the gear the rider will select at that point. This minimizes the chance that the rider arrives at an apex in a gear that puts the engine in a torque trough.

The calculation is straightforward: given a corner apex speed $v_{apex}$, a tire rolling radius $r$, a desired engine RPM $N_{target}$, and a fixed primary drive ratio $R_p$, the required overall gearing ratio is:

$$R_{total} = \frac{N_{target} \cdot 2\pi r}{60 \cdot v_{apex}}$$

Dividing $R_{total}$ by the primary drive ratio gives the required product of internal gear ratio and final drive ratio. If the internal gear is fixed (e.g., second gear is always 1.78:1), then the final drive ratio is the tuning variable, and the sprocket combination is selected accordingly.

In practice, this optimization cannot be perfect for every corner simultaneously — the gearbox has a finite number of ratios, and the final drive is a single multiplier applied to all of them. The engineer must therefore prioritize. On a circuit like Mugello, with its long Rettifilo straight, the top gear ratio is constrained by the need to reach maximum speed without hitting the rev limiter before the braking zone. On a technical circuit like Jerez, with its slow, power-sensitive corners, the first three gears carry greater priority. When there is genuine tension between these objectives, some engineers carry a looser final drive (larger rear sprocket) for qualifying — accepting a lower top speed to maximize corner-exit acceleration and improve lap time where it matters for a single flying lap — and shift to a taller final drive for the race to reduce wear and manage tire temperatures on the straights.

### Chain Tension Dynamics, Sprocket Wear, and Drivetrain Harmonics

Chain tension is not static. As the rear suspension compresses and extends, the distance between the gearbox output sprocket and the rear axle changes unless the swingarm pivot is perfectly concentric with the output sprocket — which it never is in practice, because a swingarm pivot concentric with the output sprocket would eliminate the ability to adjust chain tension. The result is a chain tension that varies sinusoidally with suspension travel. At one extreme of suspension travel, the chain is tightest; at the other, it is slackest.

Setting chain slack is therefore a compromise between preventing the chain from going slack at full suspension compression (slack allows the chain to whip, potentially derailing it or causing the lower run to contact the swingarm) and preventing excessive tension at full suspension extension (overtight chains create a binding load path that effectively increases suspension rate by adding a tensile spring between axle and frame). The standard setting of 25–30 mm of free play measured at the midpoint of the lower chain run with the motorcycle on a paddock stand represents years of collective experience optimizing this tradeoff.

For racing applications, some engineers fine-tune chain slack based on the circuit's curb characteristics and the aggressiveness of the suspension setup. A very stiff setup with limited travel permits a tighter chain setting because the tension variation across the smaller travel arc is proportionally lower. A soft endurance setup with more travel demands generous slack. The chain adjustment should always be re-verified with the rider sitting on the motorcycle, since sag compresses the rear suspension and tightens the chain relative to the static measurement.

Drivetrain harmonics become a failure mode on high-horsepower four-cylinder engines where the firing interval creates a torque pulse at twice the crankshaft frequency per revolution (for a firing-order-based analysis on a four-cylinder, the dominant harmonic is at 2× engine order). This torque pulse propagates through the gearbox and excites the chain at a frequency that is a function of engine RPM, gearbox ratio, and chain pitch. If this excitation frequency coincides with the natural frequency of the chain's hanging catenary, resonant vibration develops in the lower chain run. The symptoms are audible as a low-frequency thrum at specific RPM points and visible in high-speed footage as a standing wave in the chain. The mitigation is a chain guide or tensioner slipper on the lower run, which damps the vibration amplitude before it can cause chain side plate fatigue cracking.

Sprocket wear manifests as tooth profile asymmetry. Under drive torque, the chain engages the drive face of each tooth; under engine braking, the trailing face. High-performance applications with aggressive on/off throttle cycling wear both faces, but the drive face typically wears faster due to the higher sustained loads. When the tooth profile develops the characteristic hooked or shark-fin profile, the chain engages inconsistently, creating a velocity variation in the lower run that the slipper clutch may misinterpret as a drive torque reversal, triggering unintended slip events. Sprockets should be examined under a straight edge at every service interval; replace the chain and both sprockets as a matched set, never just one component.

### Clutch Fade, Plate Glazing, and Launch Burn Events

The two distinct failure modes of the wet multi-plate clutch are thermal fade and mechanical glazing, and they present very differently in the cockpit. Thermal fade occurs when sustained slip events — a long, poorly executed launch, repeated slow-speed maneuvering, or a racetrack incident requiring extended clutch holding — raise the oil and plate temperature to the point where the friction material's coefficient drops sharply. The rider perceives this as a clutch that slips under hard acceleration even when the lever is fully released, and the characteristic smell of burnt friction material is unmistakable. Recovery requires cooling: a few laps of normal riding or a pit stop to allow the clutch pack to dissipate heat back into the oil. If the temperature was extreme enough to carbonize the friction material surface, the plates must be replaced.

Mechanical glazing is a slower, cumulative failure mode caused by repeated engagement at low slip velocities and low contact pressures — the conditions of gentle, careful riding. Paradoxically, a race machine that is frequently ridden gently in pit lane accumulates a polished, low-$\mu$ surface on the friction plates that reduces total clamping capacity. The fix is a controlled bedding procedure: several deliberate hard engagement events that abrade the glazed surface and restore the micro-topographic roughness that generates friction. The clutch spring preload should also be verified against the manufacturer's installed height specification; worn springs with reduced preload directly reduce clamping force and exacerbate both fade and glazing tendencies.

### Selector Drum Wear and Missed Shifts Under Load

The gear selector drum's helical grooves carry significant side loads from the fork pins during shifts. In a production motorcycle with a street-focused shift quality target, these grooves are relatively wide and the fork pins ride with generous clearance, allowing some slop that the rider perceives as a notchy but forgiving shift. In a close-ratio racing gearbox, the groove width is tighter, the engagement window is shorter, and the mechanical advantage of the foot lever is calibrated for a short, positive shift stroke. Under these conditions, any wear that widens the groove or rounds the fork pin generates a delayed engagement — the fork pin rattles in the groove before engaging the detent, and the shift completes late or not at all.

A missed shift under hard acceleration is not merely inconvenient. If the dog ring exits first gear but fails to engage second, the gearbox is momentarily in neutral while the engine races to the rev limiter. The subsequent engagement of second gear at over-speed creates a shock load on the dog faces that is a multiple of the normal engagement shock, frequently chipping or rounding the dogs. After the first missed shift, every subsequent upshift on that gear pair carries a slightly higher risk of recurrence, because the damaged dogs no longer present a clean rectangular face for engagement. The correct response after a suspected missed shift event is an immediate inspection of the affected dog ring and gear wheel at the next service interval, before the motorcycle completes another competitive session.

Gear selector forks themselves can bend under extreme loads — either from mis-shifts or from the mechanical loads imposed during a rear wheel lockup and sudden release, where the drivetrain shock propagates backward through the gearbox. A bent fork does not necessarily prevent engagement, but it alters the axial position of the dog ring, potentially causing engagement at a point where the dogs are only partially overlapping. This half-engagement condition is a catastrophic failure precursor; the dogs will strip under load, leaving the transmission locked in that ratio or effectively neutral, depending on how the debris distributes in the case. Inspection protocol after any significant drivetrain shock event must include physical verification of fork straightness using the manufacturer's tolerance gauge.

### Quickshifter Integration: Cut Timing Calibration and Dog Load Management

The quickshifter eliminates the need to close the throttle or pull the clutch during upshifts by momentarily interrupting ignition or fuel delivery, which unloads the gear dogs sufficiently for the selector to disengage and re-engage the next ratio. The technical subtlety that separates a well-calibrated quickshifter from a poorly calibrated one is the duration of the interrupt, measured in milliseconds. Too short an interrupt and the dogs are still under load when the shift is commanded — the selector fork cannot move the dog ring because the dog faces are carrying torque and cannot disengage. The rider feels a blocked, resistant shift. Too long an interrupt and the engine falls off the powerband before the new ratio is engaged, creating a stumble and a loss of exit speed.

The optimal interrupt duration is a function of engine inertia, the current gear ratio, and the engine RPM at the moment of shift. At high RPM in a low gear, the engine has high angular momentum and the interrupt must be slightly longer to allow that momentum to bleed off and unload the dogs. At lower RPM or in a higher gear with more inertia buffer from the drivetrain itself, a shorter interrupt suffices. Modern ECU-based quickshifters derive this map empirically, using a load cell in the shift linkage or a strain gauge on the shift rod to detect the onset of the shift force, then applying a RPM-indexed interrupt duration map that the engineer programs against measured dyno and telemetry data.

The gearbox oil specification is not a neutral variable in this system. A heavier gear oil (80W-90) provides better film thickness on the dog faces under load but adds viscous drag that slows the axial movement of the fork during the interrupt window — in extreme cases, the fork does not complete its travel before the interrupt ends and the engine torque re-engages. Many racing teams operating in warm conditions switch to a lighter 75W oil specifically to allow faster fork travel during quickshifter-initiated shifts, accepting slightly higher wear rates on the dog faces as a consequence of the reduced film thickness.

The diagnostic workflow for a rider reporting blocked or incomplete upshifts is systematic: first verify the shift rod load cell calibration with a bench force gauge to confirm the trigger threshold is within specification; second, check the interrupt duration map against the RPM and gear at which the problem occurs; third, verify gear oil specification and temperature at the time of the incident from the ECU's oil temperature channel if equipped; fourth, physically inspect the dog rings on the affected ratio for rounding or chipping. This sequence progresses from the least invasive check to the most invasive, minimizing the risk of unnecessary disassembly while ensuring the root cause is identified before the motorcycle returns to competition.
