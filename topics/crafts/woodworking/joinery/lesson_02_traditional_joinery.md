# Lesson 2: Traditional Joinery Taxonomy, Mortise-Tenon Systems, Dovetails

## 1. First-Principles Intuition & Invariants

Wood is an anisotropic material, meaning its mechanical properties change depending on the direction of applied force relative to its grain structure. Along the grain, wood possesses immense tensile and compressive strength; across the grain, it is weak, prone to crushing, and highly susceptible to dimensional changes driven by fluctuations in ambient humidity. The entire taxonomy of traditional joinery is born from the necessity to connect discrete wooden members while navigating this anisotropy. A joint must maximize long-grain to long-grain adhesive contact, minimize cross-grain constraints that will tear themselves apart as the wood expands and contracts, and provide mechanical interlock that resists the specific vector forces a structure will encounter over its lifespan. 

The primary structural invariants across all joint families are shear resistance, tensile withdrawal resistance, and racking resistance. When a load is applied to a frame, it generates racking forces—lateral pressure attempting to parallelize two previously perpendicular components. Mortise and tenon joints counter racking through the deep insertion of a sized male projection (the tenon) into a tightly matching female cavity (the mortise), relying on the shear strength of the tenon cheeks and the compressive strength of the mortise walls. Dovetail joints, conversely, are designed to defeat tensile withdrawal forces. The trapezoidal geometry of the pins and tails creates a mechanical lock that renders the joint impossible to pull apart in one axis, regardless of the adhesive used. Box joints provide a simplified mechanical lock maximizing long-grain glue surface for peripheral applications, while bridle joints offer an open-faced mortise configuration for mid-span frame intersections where a through-tenon is structurally unnecessary or visually undesirable. Understanding these invariants dictates the selection of a joint not by aesthetic tradition, but by the mechanical demands of the load path.

## 2. Core Architecture & Mechanics

The architecture of a mortise and tenon joint is a study in material allocation. The mortise removes material from the primary member, while the tenon shapes the end of the secondary member to fill that void. The structural integrity relies almost entirely on the long-grain cheek surfaces of the tenon pressing against the long-grain walls of the mortise. 

```text
[Mortise & Tenon Geometry]

       |     | <- Shoulder (cross-grain, bears tension down)
       |     |
  _____|_____|_____
 |     |     |     | 
 |     | TENON     | <- Cheek (long-grain, primary glue surface)
 |_____|_____|_____|
       |     |
       |     | <- Haunch (optional, resists twisting)
       |     |
```

To execute a standard mortise and tenon, the mortise width should typically be set to one-third the thickness of the mortised member. This leaves two-thirds of the surrounding material intact, preventing the sidewalls from blowing out during assembly or shrinking unevenly. The tenon is then sized to match this width, with its length generally extending to roughly two-thirds the width of the apron or leg it is joining. When laying out the mortise, a marking gauge is used to scribe the width on both faces to ensure the chisel registration is perfectly centered. The waste is chopped using a mortise chisel—characterized by a thick, heavy blade and a deep bevel designed to lever out chips—driven by a mallet. The tenon is cut on the mating piece using a tenon saw (a stiff-backed saw with relatively large rip-filed teeth) to establish the cheeks, followed by a crosscut saw to define the shoulders. The fit must be hand-pressure tight on the cheeks, with a 0.1 mm tolerance to allow for adhesive squeeze-out, while the edges are left slightly proud to be flushed after glue-up.

Dovetail architecture abandons the parallel cheek in favor of an angled interface, introducing a wedge geometry that physically prevents withdrawal. The angle of this wedge is critical. If the angle is too shallow, the joint loses its mechanical lock and behaves like a plain box joint; if too steep, the fragile tail board will split along the short grain. 

```text
[Dovetail Angle Invariants]

  1:8 Ratio (Hardwoods: ~7.1 degrees)
  +------------+
  |            | 1
  +------------+
     \        /
      \      /  8
       \    /
        \  /
         \/
```

For dense hardwoods like oak or maple, an 1:8 ratio (approximately seven degrees from vertical) provides sufficient lock without compromising the short-grain strength of the tails. For softwoods like pine or cedar, a steeper 1:6 ratio (approximately nine and a half degrees) is required because the softer wood would otherwise crush and deform under the wedge action of a tighter angle. To execute a through dovetail, the tails are laid out using a sliding bevel set to the chosen ratio. The baseline is gauged at the exact depth of the pin board thickness. The tails are cut with a dovetail saw, strictly following a sequence: cut the left side of every tail, reposition, and cut the right side, maintaining a slight outward angle to ensure the inside of the waste falls away cleanly. The waste is removed with a coping saw and pared flush to the baseline with a sharp chisel. The pin board is then placed vertically in the vise, the tail board is laid over it, and the tails are scribed directly onto the end grain of the pin board using a striking knife. This direct transfer eliminates cumulative layout errors. The pins are cut, waste removed, and the two are dry-fitted. A properly cut dovetail should hold together firmly by friction alone before any adhesive is applied.

## 3. High-Performance Optimization & Failure Modes

The most catastrophic failure mode in traditional joinery is cross-grain wood movement. When a wide, flat-sawn panel is trapped between two narrow frame components using a rigid mortise and tenon, the panel will expand across its grain during humid months. Because the frame restricts this movement, the panel will buckle, or the frame joints will be blown apart. The optimization for this is the "haunched" tenon combined with a paneled door construction, where the panel floats in a groove, and the tenon is shortened (haunched) to fill the top of the groove, preventing racking while allowing the panel to move. 

Drawboring represents the ultimate mechanical optimization of the mortise and tenon. Rather than relying solely on modern PVA adhesives, which can creep under constant shear load, drawboring uses a hardwood peg to mechanically pin the tenon. The hole is bored through the mortised member and the tenon while the joint is dry-fitted. The tenon is then removed, and the hole in the tenon only is offset toward the shoulder by approximately 1.5 mm. When the joint is assembled and a tapered hardwood peg is driven into the offset hole, it violently pulls the tenon deeper into the mortise, generating massive compression between the cheek and wall. This joint will outlast the wood itself, as the mechanical lock does not degrade with humidity-induced glue failure. 

Dovetail failure modes almost exclusively stem from layout inaccuracies or poor sawing technique. If the saw kerf is not strictly square to the face of the board, the joint will gap on the inside or outside corner. When gaps appear during dry assembly, the practitioner must resist the urge to force the joint together with a mallet, which will crush the delicate short-grain fibers of the tails. Instead, a sharp paring chisel is used to shave the high spots on the pins until the joint seats by hand pressure. In box joint construction, where the mechanical interlock is minimal and adhesive surface is paramount, tear-out on the cross-grain shoulders during table-saw dadoing is the primary failure. This is mitigated by using a zero-clearance throat plate and a high-quality crosscut blade, or by scoring the shoulder baseline with a marking knife prior to power tool execution. 

### Drawboring Execution Sequence

1. Dry-fit the mortise and tenon.
2. Mark the peg location on the mortised face, offset 15 mm from the edge. 
3. Bore a 8 mm hole straight through the mortised member and into the tenon.
4. Disassemble the joint. 
5. Offset the bore in the tenon only: use a doweling jig to drill a new 8 mm hole in the tenon, shifted 1.5 mm toward the tenon shoulder.
6. Reassemble the joint, applying adhesive to the cheeks only.
7. Taper the end of an 8 mm hardwood peg and drive it through the straight hole in the mortise wall into the offset hole in the tenon, drawing the joint tight.
8. Saw the peg flush and pare it smooth to the face.
