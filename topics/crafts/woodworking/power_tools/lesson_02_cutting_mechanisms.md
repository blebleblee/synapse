# Lesson 2: Cutting Geometry, Blade Dynamics, and Material Interaction

## 1. First-Principles Intuition & Invariants

Wood is not a uniform material. It is a biological composite of cellulose microfibrils bound in a lignin matrix, organized into growth rings whose density, moisture content, and grain orientation vary continuously across a single board. Before a craftsman can read a blade failure or dial in a feed rate, they must internalize this fundamental asymmetry: the wood is always fighting back, and the geometry of the cutting edge determines whether the tool wins that fight cleanly or loses it in tearout, burning, and deflection.

Every powered cutting operation in woodworking — table saw ripping, circular saw crosscutting, bandsaw resawing, router profiling — reduces to a single physical event: a wedge-shaped edge is forced through a solid material faster than the material can escape. The three geometric variables that govern the quality of that event are hook angle, clearance angle (also called relief angle), and kerf width. These are not arbitrary design choices. They encode centuries of empirical and later analytical understanding of how cellulose fibers respond to shear stress.

**Hook angle** (sometimes called rake angle in metalworking literature, though the terms are not perfectly equivalent) describes the angle between the leading face of a tooth and a radial line drawn from the blade's center. A positive hook angle means the tooth face tilts forward in the direction of rotation, aggressively scooping material out of the cut. A negative hook angle tilts the face backward, forcing the tooth to scrape rather than slice. This distinction has enormous practical consequences. A 20° positive hook carbide blade attacking a rip cut along long-grain pine will tear through fibers efficiently, with the chip lifting and curling ahead of the tooth. That same blade applied to a 10-inch crosscut sled operation on figured maple will rip fibers perpendicular to the grain rather than sever them cleanly, and the result is a ragged, lifted edge. For crosscutting hardwoods and melamine-faced sheet goods, a 5°–10° positive or even a slightly negative hook forces the tooth to shear fibers in compression rather than lifting them, dramatically reducing tearout on the bottom face.

**Clearance angle** is the relief ground behind the cutting edge, the gap that prevents the tooth's body from rubbing against the freshly cut surface. Without adequate clearance, the tooth heel drags along the kerf wall, generating friction, heat, and resin buildup. For carbide-tipped circular saw blades, clearance angles of 10°–15° are standard, with harder, denser materials (teak, ipe, hickory) benefiting from slightly reduced clearance — roughly 10°–12° — to maintain edge support and reduce chipping of the brittle carbide tip. Softer, resinous materials like Douglas fir or wet pine tolerate and even benefit from larger clearances (up to 18°) because the softer fibers spring back more aggressively, requiring more relief to prevent rubbing.

**Kerf width** is the total material removed per pass, determined by the set of the teeth (the alternating outward deflection of successive teeth in many blade designs) and the thickness of the carbide tips. A full-kerf blade runs at 1/8 inch (3.2 mm). A thin-kerf blade runs at 3/32 inch (2.4 mm). The power consumption difference between these two widths is not trivial: at a 10-inch table saw running 48 teeth, a thin-kerf blade can reduce motor load by 20–30%, which matters enormously on a 1.5 HP contractor saw with a belt-drive running at the edge of its capacity. The tradeoff is blade body stiffness. Thinner blade bodies are more susceptible to lateral flex under asymmetric side load — the kind produced when ripping a bowed board without a featherboard — and that flex translates directly into a curved kerf, binding, and kickback risk.

Underlying all three variables is a physical invariant that every experienced practitioner carries implicitly: **cutting force is a vector, not a scalar**. When a tooth engages the wood, it is simultaneously pushing forward (tangential cutting force), pushing the blade away from the workpiece (radial thrust), and generating a lateral force proportional to hook angle and material density. A table saw blade experiencing lateral force from a bowed board will deflect within its plate, changing the effective hook angle in real time and altering the chip geometry. This is why blade tensioning — the slight dishing rolled into the blade plate at the factory — is not decorative. It pre-stresses the plate so that thermal expansion at the rim during cutting is resisted by hoop stress, maintaining flatness and tracking true through the cut.

The directionality of wood grain introduces two additional invariants that override simple material hardness as predictors of cutting behavior. Cutting **with** the grain (long-grain ripping) allows the tooth to split fibers along their natural boundaries, requiring relatively low specific cutting energy per unit volume removed. Cutting **across** the grain (crosscutting) requires the tooth to sever each fiber individually, which demands higher specific energy but, with the right tooth geometry, produces a smoother surface because the fibers are transected rather than torn. The worst-case scenario is **against the grain** at a shallow angle — the climbing cut that occurs when routing in the wrong direction around a workpiece, or when a hand-held circular saw exits a cut at an angle to the grain. Here, the cutting edge pries fibers upward from below the surface before severing them, and no amount of blade sharpness fully eliminates the resulting grain-following tearout. The correct response is climb cutting in a controlled router context (taking a final light pass against normal feed direction), or reversing the workpiece, not changing the blade.

## 2. Core Architecture & Mechanics

### Tooth Geometry and Blade Typology

Understanding how a blade's macro-geometry converts rotational power into linear cutting action requires tracing the signal path from motor spindle to chip ejection. The following diagram maps that flow for a standard carbide-tipped table saw blade.

```
Motor Torque (N·m)
        │
        ▼
Arbor → Blade Body (tensioned steel plate)
        │
        ├─── Rim Speed: V = π × D × RPM / 60  (m/s)
        │
        ├─── Tooth Engagement:
        │       ┌─────────────────────────────────────────┐
        │       │  Hook Angle (θ_h): chip lift vector     │
        │       │  Clearance Angle (θ_c): heel relief     │
        │       │  Top Bevel (θ_b): fiber shear plane     │
        │       │  Tooth Pitch: gullet depth & chip load  │
        │       └─────────────────────────────────────────┘
        │
        ▼
  Chip Formation
        │
        ├─── Type 1: Continuous chip (soft long-grain)
        ├─── Type 2: Segmented chip (hardwood crosscut)
        └─── Type 3: Powder/dust (MDF, compressed material)
        │
        ▼
  Surface Quality
  (governed by chip thickness × tooth count × feed rate)
```

The tooth configurations found on modern blades are not interchangeable; each is optimized for a specific chip formation regime. The **ATB (Alternate Top Bevel)** configuration grinds successive teeth with opposing top-bevel angles, typically 10°–20°. As the blade rotates, the left-bevel tooth scores the left fiber wall of the kerf and the right-bevel tooth scores the right wall, with the actual bottom of the kerf cleaned by the intersection of both bevels at the center. This double-scoring action severs surface fibers before the tooth body reaches them, which is exactly why a fresh 60-tooth ATB blade produces a glassy crosscut surface on hard maple: the fibers are pre-cut, not torn.

The **FTG (Flat Top Grind)** tooth presents a flat, chisel-like face. It removes material aggressively, produces a coarser surface, and ejects large chips through deep gullets efficiently. These are ripping teeth, optimized for the scenario where long-grain splitting action is preferred over surface quality. A well-sharpened 24-tooth FTG rip blade at 15° positive hook running at 4,500 RPM on a cabinet saw will rip a 2-inch-thick white oak board without bogging — the gullets are deep enough to evacuate the large chip before the next tooth engages.

The **TCG (Triple Chip Grind)** pairs a chamfered "raker" tooth with a flat-top tooth in alternation. The chamfered tooth makes the initial cut, displacing material from the center of the kerf, and the following flat tooth cleans the floor to width. TCG is the standard configuration for non-ferrous metals, laminates, and engineered composites like melamine particleboard, where the alternating stress cycling of ATB would chip the brittle surface coating. Crucially, TCG provides carbide edge support through the chamfer: at the brittle-hard boundary of a melamine face, the chamfered tooth distributes cutting force over a longer contact arc rather than concentrating it at a point, which is precisely the condition that causes carbide micro-chipping on ATB blades cutting hard laminates.

### Feed Rate Mechanics and Chip Load

Feed rate and blade speed are linked through a single governing quantity: **chip load per tooth**, defined as the thickness of material each tooth removes per pass. The formula is:

$$f_z = \frac{\text{Feed Rate (mm/min)}}{\text{RPM} \times N_t}$$

where $N_t$ is the number of teeth. This quantity determines whether the tooth is cutting or rubbing. At too low a feed rate (or equivalently, too high a tooth count for the application), the chip becomes thinner than the edge radius of even a sharp carbide tip, and the tooth is effectively plowing through the material rather than slicing it. This is the mechanical cause of burning on a table saw: the craftsman slows down through a difficult knot, the chip load per tooth drops below the minimum effective cutting threshold, friction dominates over shear, and the blade's rim speed converts almost entirely to heat rather than chip removal.

At excessive feed rate, the chip load exceeds the structural capacity of both the tooth and the material: carbide corners chip under the impulsive load, the workpiece can deflect away from the fence, and on a router table the bit may stall or kick back. For a 10-inch 40-tooth ATB blade at 4,000 RPM, a practical chip load target for hardwood crosscutting is 0.08–0.12 mm per tooth. That corresponds to a feed rate of roughly 3,200–4,800 mm/min, or 125–190 inches per minute — a brisk walking pace across the table. Many hobbyists feed at 40–60 inches per minute and produce burned edges as a result.

The relationship between cutting circle diameter and chip geometry adds another layer of nuance. As a blade's usable diameter decreases through repeated sharpenings (a 10-inch blade may eventually run as a 9.75-inch blade after several resharpening cycles), the arc of engagement at any given depth of cut changes. A smaller diameter means a steeper engagement angle, slightly higher radial cutting force per tooth, and, for the same RPM, a lower rim speed. All three effects push toward coarser surface quality, which is worth monitoring in a production environment where consistency matters across a long run.

### Router Bit Geometry and Spiral Dynamics

In router operations, the same first principles apply but the geometry is fully three-dimensional. A straight two-flute bit and an upcut spiral bit have nearly identical cross-sectional profiles, but their chip evacuation behavior could not be more different. The upcut spiral's helical flutes pull chips upward and out of the cut — ideal for through-cuts in solid wood where the top surface is the finished face, since chip evacuation prevents re-cutting of swarf. However, that upward thrust also lifts the workpiece fibers just ahead of the cutting zone, creating tearout on the top face. The **downcut spiral** pushes chips downward, holding fibers in compression as they are cut and producing a clean top face — the right choice for spoilboard work and veneered panels where the top surface must remain pristine. The **compression spiral**, which runs an upcut geometry on the lower half and a downcut geometry on the upper half, is the production solution for routing through 3/4-inch veneered MDF: it cleans both faces simultaneously by shearing the bottom fibers upward and the top fibers downward, meeting in the middle of the substrate.

```
Router Bit Helix Comparison (cross-section view, cutting in X):

  Upcut Spiral:          Downcut Spiral:        Compression:
  ┌──────────┐           ┌──────────┐           ┌──────────┐
  │ ↑ chips  │           │ ↓ chips  │           │ ↓ top    │
  │  ejected │           │  ejected │           ├──────────┤
  │  upward  │           │ downward │           │ ↑ bottom │
  └──────────┘           └──────────┘           └──────────┘
  Clean bottom face      Clean top face         Clean both faces
  Tearout at top         Tearout at bottom      Optimal for veneers
```

Helix angle also governs cutting force direction. A 30° helix concentrates more of the tangential cutting force into the axial direction (along the router bit's shaft), increasing collet pull-out force and demanding higher runout tolerance from the router's bearings. A 15° helix keeps more force in the radial plane, reducing bearing wear but producing a rougher surface at equivalent feed rates. High-helix bits (45°–60°) are found on finishing spiral bits designed for aluminum and plastics, where smooth surface finish and low cutting temperature dominate the design requirements.

## 3. High-Performance Optimization & Failure Modes

### Diagnosing and Eliminating Tearout

Tearout is the most common surface defect in power tool woodworking and also the most diagnostic: its character, location, and severity tell a precise story about which element of the cutting geometry is failing. Tearout at the **exit face** of a crosscut (the bottom of a table saw cut, the trailing edge of a router pass) indicates that surface fibers are being pried upward just before they are severed, a symptom of insufficient tooth scoring ahead of the main cutting action. The first corrective measure is a zero-clearance insert, which supports the wood fibers immediately adjacent to the blade on both sides of the kerf, providing a mechanical backstop against the prying action. If tearout persists after installing a zero-clearance insert, the blade hook angle is too aggressive for the material, and a blade with a reduced hook (5°–8° positive rather than 15°–20°) is the correct response, not simply slowing the feed rate.

Tearout at the **entry face** of a router pass — the face the bit first contacts — usually indicates climb cutting at too high a chip load, or that the router is moving in the conventional direction through difficult reverse grain. The practical solution is to take a 1.5 mm roughing pass in the conventional direction, then make a 0.5 mm finishing pass as a controlled climb cut. The climb pass reduces chip load to nearly zero, and because there is no material to actually tear out at that depth, the bit merely skims the surface and leaves a clean finish. This technique is standard in high-end custom millwork shops but rarely taught explicitly in beginner instruction.

Tearout on the **back face of a rip cut** — the vertical face parallel to the rip fence — almost always indicates a dull blade. The mechanism is specific: as carbide edges wear, the edge radius grows from a theoretical zero to a measurable 20–50 microns of rounding. At that radius, the tooth no longer shears fibers; it crushes and displaces them. The crushed fibers spring back after the tooth passes, creating a rough, burnished surface with a characteristic glazed appearance. No adjustment of feed rate or hook angle compensates for a worn edge. The blade must be resharpened or replaced.

### Vibration, Resonance, and Plate Dynamics

A table saw blade spinning at 4,500 RPM is a high-speed rotating disk, and like any disk, it has natural resonant frequencies at which small excitation forces produce large amplitude vibrations. If a blade's resonant frequency falls within the range of its tooth engagement frequency — defined as $f_e = RPM/60 \times N_t$ — the blade will ring and chatter in the cut. A 40-tooth blade at 4,500 RPM has an engagement frequency of 3,000 Hz. If the blade's first radial mode sits near 3,000 Hz, every tooth impact drives the resonance, the blade vibrates laterally within the kerf, and the cut surface shows a characteristic washboard ripple pattern at a spacing proportional to the feed rate divided by the engagement frequency.

The industry solution to resonance is **expansion slots**, the radial cuts with copper or brass plugs visible on quality blades. These slots interrupt the continuous hoop of the blade plate, changing the stress distribution and shifting the natural frequencies away from the engagement frequency. The plugged tips of the slots prevent stress concentration fractures from propagating. A blade without expansion slots is not inherently inferior — many thin-kerf blades omit them to maintain plate rigidity — but those blades are typically designed with plate geometries that place their resonant frequencies well clear of the operational engagement range.

Blade wobble (lateral runout) compounds resonance effects by ensuring that every rotation, the tooth path traces a slightly different plane. Total indicated runout (TIR) greater than 0.003 inches at the rim of a 10-inch blade produces a kerf that is effectively 0.006 inches wider than the blade's designed kerf — an invisible but measurable width that matters in precision dado work and tenon fitting. Measuring runout requires a dial test indicator mounted on a magnetic base, zeroed against the flat of the blade plate (not the tooth tips) at a consistent radial distance, with the spindle turned by hand through a full 360°. If runout exceeds 0.003 inches, the arbor flange should be inspected for debris or damage before condemning the blade itself.

### Feed Rate Optimization Across Density Gradients

Hardwood boards are not homogeneous. A single 8-foot board of black walnut may pass through two or three density gradients corresponding to early wood and late wood rings, crotch figure, or sapwood inclusions. When a table saw or router encounters a sudden density increase — say, a compressed late-wood band 3 mm wide — the cutting force spikes, the feed rate momentarily drops if the operator is hand-feeding, and the chip load per tooth drops with it. That momentary underfeed produces a local burned stripe exactly 3 mm wide that is frustrating and difficult to explain without understanding the underlying mechanics.

The practitioner-level solution on a table saw is a consistent, deliberate feed rate maintained by body mechanics rather than grip. Leaning into the cut with the hip against the fence rail while maintaining hand contact with the board — rather than pushing with the arms — provides proprioceptive feedback about resistance without varying the feed rate. On a CNC router, this problem is addressed programmatically by reducing feed rate in the program header for high-density species and implementing a chip-thinning compensation formula when the radial depth of cut drops below 50% of the bit diameter:

$$f_{\text{adj}} = f_{\text{nominal}} \times \sqrt{\frac{D}{2 \times a_e}}$$

where $D$ is bit diameter and $a_e$ is radial engagement. This formula compensates for the geometric thinning of chips that occurs at shallow radial engagements, ensuring that the actual chip thickness (and therefore cutting action rather than rubbing) is maintained even as the stepover percentage decreases.

### Blade Selection Reference

The following reference table consolidates the blade geometry selections discussed above for common production scenarios in solid wood and sheet goods work.

| Application | Tooth Count | Hook Angle | Grind | Kerf | Notes |
|---|---|---|---|---|---|
| Hardwood ripping (oak, maple) | 24–30 | +15° to +18° | FTG | Full | Deep gullets essential; featherboard mandatory |
| Softwood ripping (pine, fir) | 24 | +20° | FTG | Full or thin | High hook handles resinous species |
| Hardwood crosscutting | 60–80 | +5° to +8° | ATB | Full | Zero-clearance insert required |
| Melamine / laminate | 60–80 | +5° | TCG | Full | TCG prevents carbide chipping at brittle face |
| Plywood, sheet goods | 40 | +10° | ATB | Thin | Thin kerf reduces splintering on veneers |
| Non-ferrous / plastics | 60–80 | 0° to –5° | TCG | Full | Negative hook prevents grab and kickback |
| General purpose | 40 | +10° to +15° | ATB or combo | Full | Compromise between rip and cross quality |

### Critical Failure Modes and Remediation

The most dangerous failure mode in powered blade operation is **kickback**, and its geometry is precisely describable: kickback occurs when the trailing teeth of a table saw blade contact the rear kerf wall of a workpiece that has closed in on the blade due to internal stress relief or fence misalignment. The trailing teeth, running at rim speeds of 100–130 mph, catch the workpiece and propel it rearward along the trajectory defined by the top of the blade arc — directly at the operator. Riving knives and spreaders exist for exactly this reason, maintaining kerf width behind the blade and preventing closure. A riving knife set to within 3 mm of the blade's rear arc eliminates the mechanical precondition for kickback; a spreader fixed to the blade guard provides partial protection but does not rise and fall with the blade, leaving a gap at shallow cut depths. For any rip operation in solid wood, the riving knife is non-negotiable.

Bearing failure in routers presents a subtler but equally consequential hazard. As router bearings develop play, the bit experiences orbital runout in addition to the designed cutting path. At 20,000 RPM — a standard router speed — even 0.002 inches of orbital runout causes the bit to strike the same point on the kerf wall twice per revolution with a significant impulsive force. This impulsive loading accelerates carbide fatigue and can fracture carbide bits without warning, particularly at the shank-to-flute transition where stress concentration is highest. The diagnostic is a router that sounds rough or hollow at speed, particularly under load. The correct response is immediate bearing replacement, not continued operation at reduced depth.

Undercutting a router template at high speed — taking the full profile depth in one pass rather than in staged 6–8 mm increments — introduces a scenario where the bit is engaged over its full flute length. Full-length engagement maximizes deflection at the tip, since the bit behaves as a cantilever beam with the collet as its fixed end. At deflections above 0.1 mm, the tool path error is visible in the finished profile as a taper from top to bottom, and the increased side load on the collet can cause micro-slippage, allowing the bit to pull down incrementally through the collet during a long cut. Setting bit projection to no more than 2× the cutting diameter before staging passes prevents both failure modes.

The cumulative picture that emerges from examining blade geometry, chip load mechanics, grain dynamics, and failure modes is not a checklist but a physical intuition: every adjustment to hook angle, feed rate, tooth count, or depth of cut is a manipulation of the same fundamental event — a wedge passing through a fibrous composite under controlled conditions. The practitioner who understands why a 60-tooth ATB blade at 8° hook leaves a glassy crosscut on quartersawn white oak does not need to memorize a blade chart. They can derive the correct selection from first principles and confirm it at the workbench in a single test pass.
