# Lesson 2: Wood Material Science

## 1. First-Principles Intuition & Invariants

Wood is not a material in the engineering sense of a homogeneous solid. It is an engineered biological structure, the product of a tree's vascular system laid down cell by cell across decades, optimized by evolution to conduct water, store starch, and resist mechanical loads specific to the species and its growing environment. Every decision a miller makes — blade selection, feed rate, drying schedule, final orientation of a board — is downstream of that cellular architecture. To mill lumber with consistent, predictable results, you must develop an intuition for what wood actually is at the structural level, because the material will punish any assumption that it behaves like steel or plastic.

### The Cellular Foundation

At the microscopic scale, wood is composed primarily of three types of cells: tracheids and vessel elements that form the primary conductive pathways, fiber cells that provide structural rigidity, and ray cells that run radially outward from the pith, transporting nutrients laterally. In softwoods like Douglas fir or Sitka spruce, the tracheids perform both conductive and structural roles simultaneously, their walls thickened with cellulose microfibrils wound in a tight helical pattern that gives the cell extraordinary tensile strength relative to its mass. This is why a Sitka spruce guitar brace can support compressive loads far in excess of what its weight would suggest. In hardwoods, these functions are separated: large-diameter vessel elements called pores handle water transport, while smaller, denser fiber cells provide structural support. The distribution and size of those pores is what creates the visible figure in ring-porous species like white oak and ash, where the earlywood pores are dramatically larger than the latewood, versus diffuse-porous species like maple and cherry, where pore sizes remain roughly consistent across the growth ring.

The cell walls themselves are not solid. They are built from three distinct laminae — the primary wall, the outer secondary wall (S1), the middle secondary wall (S2), and the inner secondary wall (S3) — each layer reinforcing the last with cellulose microfibrils oriented at different angles. The S2 layer is by far the thickest and dominates the mechanical behavior of the cell. Its microfibril angle, commonly called the MFA, varies considerably between species and even between juvenile and mature wood within the same tree. Juvenile wood, found in the core of the stem within roughly the first ten to fifteen growth rings from the pith, has a high MFA — sometimes 30 to 45 degrees — which makes the cells more flexible and extensible but significantly less stiff. Mature wood, laid down in the outer rings as the tree ages, has a low MFA in the range of 5 to 15 degrees, aligning the cellulose more closely with the cell's long axis and producing the high stiffness-to-weight ratio that makes old-growth timber so prized by instrument makers and structural engineers alike. When you mill a large-diameter log, you are navigating a gradient from flexible, unstable juvenile core wood to stiff, predictable mature outer wood, and planning your cuts to minimize the proportion of juvenile wood in structural or high-tolerance applications is a fundamental milling decision.

### Moisture Content: The Governing Variable

Of all the variables that determine how a piece of wood will behave on the mill, in the shop, and in its final application, moisture content is the most consequential. Wood is hygroscopic. Its cell walls absorb and desorb water molecules as a direct function of the relative humidity of the surrounding environment, expanding when they take on moisture and shrinking when they release it, and they will do this for the entire service life of the wood. Understanding this process mechanically — not just conceptually — is what separates a machinist from a true woodworker.

Water exists in wood in two distinct states. Free water occupies the lumens, the hollow interiors of the cells, and has essentially no effect on the cell wall dimensions. Bound water, by contrast, is chemically adsorbed into the cell wall material itself, nestled between the cellulose microfibrils and the surrounding hemicellulose matrix. It is the bound water that drives dimensional change. The transition point between these two states is called the fiber saturation point, or FSP, which for most temperate hardwoods and softwoods falls between 25 and 30 percent moisture content by weight. Above the FSP, drying a piece of wood removes only free water and causes zero dimensional change. Below the FSP, every percentage point of moisture content reduction corresponds to measurable, directionally asymmetric shrinkage across the board. This asymmetry is the central fact of wood movement, and it has no equivalent in metalworking or composites.

Shrinkage occurs at three rates depending on the anatomical direction: longitudinal (along the grain), radial (across the growth rings), and tangential (parallel to the growth rings). Longitudinal shrinkage from FSP to oven-dry is typically less than 0.5 percent for most species, which is why the length of a board remains stable in service. Radial shrinkage ranges from roughly 2 to 6 percent depending on species. Tangential shrinkage is almost always roughly twice the radial value, commonly falling between 4 and 12 percent. It is this 2:1 tangential-to-radial ratio that explains the characteristic distortion patterns you see in flat-sawn lumber during drying: cupping, bowing, and the "banana" deformation that frustrates every woodworker who tries to glue up a panel from improperly dried stock.

Equilibrium moisture content, or EMC, is the moisture level a piece of wood reaches when left in a stable environment indefinitely. At 70°F and 50 percent relative humidity — a typical interior workshop environment in temperate climates — wood equilibrates to roughly 9 percent MC. At 30 percent RH, it settles near 6 percent. At 80 percent RH, it climbs above 16 percent. When you mill lumber, your target final moisture content is set not by the kiln or the mill but by the EMC of the environment where the finished piece will live. A dining table installed in a dry, centrally heated home in Minneapolis will cycle between roughly 5 and 8 percent MC across the seasons. If you mill and machine that tabletop at 12 percent MC, it will lose significant moisture and shrink considerably before reaching equilibrium — enough to open visible gaps in a solid-wood panel or crack a heavily glued rail-and-stile assembly that wasn't designed with adequate movement allowance.

The practical invariant is this: mill to a moisture content slightly above your target EMC, allow final equalization in the shop environment, then machine to final dimension. Any workflow that inverts this sequence introduces uncontrolled movement into the finished work.

---

## 2. Core Architecture & Mechanics

### Grain Geometry and Its Effect on Milling Cuts

The growth ring geometry relative to the saw kerf determines the character of every board that comes off the mill. The three primary orientations — flat-sawn, quarter-sawn, and rift-sawn — are not merely aesthetic choices. They are structural decisions with direct consequences for dimensional stability, surface figure, and workability.

```
                        Cross-section of a log showing cut orientations:

                              ┌───────────────────────────────┐
                              │         PITH (center)         │
                              │               ·               │
                              │         ·    / \    ·         │
                              │    ·   /  RIFT  \   ·        │
                              │       / (45–60°) \           │
                              │  ────/────────────\────       │
                              │  FLAT-SAWN boards  \         │
                              │  (rings run flat,   \        │
                              │   tangential face)   \       │
                              │                       \      │
                              │       QUARTER-SAWN          │
                              │  (rings perpendicular        │
                              │   to face, 60–90°)           │
                              └───────────────────────────────┘

   Growth ring angle to face:
   ┌─────────────────┬────────────────────┬──────────────────┐
   │   Cut Method    │  Ring Angle (°)    │  Tangential Face │
   ├─────────────────┼────────────────────┼──────────────────┤
   │  Flat-sawn      │  0 – 30            │  Yes (wide)      │
   │  Rift-sawn      │  30 – 60           │  Partial         │
   │  Quarter-sawn   │  60 – 90           │  No (radial)     │
   └─────────────────┴────────────────────┴──────────────────┘
```

A flat-sawn board presents its tangential face to the surface. Because tangential shrinkage is roughly double the radial value, flat-sawn boards move more and move asymmetrically — the outer face (furthest from the pith) shrinks more than the inner face, which is what induces cupping. The figure is typically cathedral-shaped, broad, and visually dramatic. A quarter-sawn board presents its radial face, exposing medullary rays and producing the distinctive ray fleck figure in species like white oak and sycamore. More importantly, the radial face is the dimensionally stable face. Quarter-sawn white oak used in Arts & Crafts furniture has survived more than a century of seasonal cycling with minimal distortion, specifically because of the radial orientation.

Rift-sawn material, cut at approximately 30 to 60 degrees to the growth rings, produces boards with straight, vertical grain on both face and edge, minimal figure, and movement behavior intermediate between flat- and quarter-sawn. It is the preferred orientation for furniture legs and drawer sides, where consistent straight grain prevents the visual distraction of ray fleck and maximizes mechanical resistance to racking.

### How Cellular Architecture Governs Tool Behavior

The practical mechanics of milling — why a dull planer blade tears grain in one species but not another, why a router bit chatters on figured maple, why ripping along the grain requires far less force than crosscutting — are all direct expressions of the cellular structure described above.

Wood's tensile strength parallel to the grain can exceed 10,000 psi in many hardwoods, while its tensile strength perpendicular to the grain may be only 500 to 1,500 psi. This extreme anisotropy means that crosscutting severs fibers across their strongest axis while ripping splits them along their weakest lateral bonding. A sharp saw tooth crosscutting dense oak must do real work to fracture individual fiber cells cleanly. If the tooth geometry is designed for ripping — with minimal rake angle and large gullets for chip evacuation — it will crush and tear the wood surface rather than sever it cleanly, producing a rough, bruised kerf that telegraphs into any subsequent jointing or planing operation.

```
   Cutting force vectors relative to grain:

   Rip cut (parallel to grain):
   ────────────────────────────────────────
   ↓ tooth force     grain fibers ║║║║║║║║
   Splits inter-cell bonding; lower force, risk of tearout on interlocked grain

   Crosscut (perpendicular to grain):
   ══════════════════════════════════════
   ↓ tooth force     grain fibers ═══════
   Severs fibers transversely; higher force, clean cut with correct geometry

   Grain direction relative to cut path (planing/routing):
                    ┌──────────────────────────────────┐
                    │  ↗ Cutting with the grain:       │
                    │    Fibers supported at the tip;   │
                    │    clean, shearing cut            │
                    │                                  │
                    │  ↙ Cutting against the grain:    │
                    │    Fibers unsupported, lever up  │
                    │    before the cut, tearout occurs │
                    └──────────────────────────────────┘
```

Interlocked grain, common in tropical hardwoods like sapele, utile, and certain mahoganies, presents a specific challenge at the mill. The fibers reverse their helical angle every few growth rings, alternating between left-hand and right-hand spirals. Any fixed planer configuration will cut with the grain for half the board and against it for the other half, producing alternating bands of torn surface that cannot be eliminated by adjusting feed rate or blade depth alone. The correct response is to reduce the cutting angle dramatically — using a high-angle plane set to 55 to 60 degrees, or a spiral-head jointer/planer with carbide inserts, which produces a slicing cut rather than a scraping or planing cut and attacks the interlocked fibers from an angle that minimizes leveraging.

### Drying Mechanics: Stress Gradients from Shell to Core

Drying is not simply the removal of water. It is a time-dependent diffusion process that creates internal stress gradients within the board as the shell dries faster than the core, and those stresses can remain locked into the wood long after the target moisture content is reached. Understanding this gradient is essential to diagnosing and preventing the most common milling defects: surface checking, end-checking, honeycombing, and case hardening.

```
   Moisture gradient during early kiln drying (cross-section of a 4/4 board):

   Surface (dry)   ├────────────────────────────────────────┤  Surface (dry)
                   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ~ 8–10% MC
                   │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│  ~ 15–18% MC
                   │████████████████████████████████████████│  ~ 20–25% MC (core)
   Center          └────────────────────────────────────────┘

   Stress state:
   Shell below FSP → wants to shrink → TENSILE stress at surface (early drying)
   Core above FSP  → resists shrinkage → COMPRESSIVE stress at core (early drying)

   After conditioning:
   Shell above FSP → stress reversal occurs
   Shell in COMPRESSION, core in TENSION → classic case-hardening signature
```

In the early stages of drying, the shell falls below the FSP and tries to shrink. The wet core prevents this, placing the shell in tension. If the drying schedule is too aggressive, this tension exceeds the wood's modulus of rupture in tension perpendicular to the grain, and surface checks open. As drying progresses and the core also falls below the FSP, it tries to shrink but is now restrained by the already-set shell. This reverses the stress state: the core goes into tension, the shell into compression. The board has essentially dried into a compressed spring, and you will not see this stress until you rip the board in half — at which point the two halves will immediately bow outward (indicating case hardening) or inward (indicating reverse case hardening in poorly managed schedules). Milling casehardened lumber produces boards that spring open on the saw, binding against the blade and potentially causing dangerous kickback.

The diagnostic test for case hardening is the prong test: rip a cross-section slab from the board, then saw it into a prong pattern. If the prongs splay outward, case hardening is confirmed. If they close inward, the core is still wetter than the shell. Neither result is acceptable for precision milling, and both require conditioning — a final kiln phase at elevated humidity that allows the shell to regain some moisture and relieve the stress gradient before the lumber is released for processing.

---

## 3. High-Performance Optimization & Failure Modes

### Milling Strategy Relative to Moisture State

The timing of each machining operation relative to the board's moisture content determines whether the final dimensions are stable or will drift unpredictably in service. The highest-performance workflow follows a strict sequencing logic: rough mill to remove warp and establish reference faces, then stack and sticker the lumber in your shop environment for equalization, then perform final dimensioning. The gap between rough milling and final milling is not idle time — it is the most important phase in the process.

When rough milling, leave a minimum of 1/8 inch of thickness and 1/4 inch of width beyond your target final dimensions on 4/4 to 6/4 stock. For thicker slabs (8/4 and above), increase this to 3/16 inch on thickness. These allowances exist because the stress relief from jointing and planing opens the board's internal gradient, and the board will often move measurably within hours of the first cut. Attempting to final-dimension a board that has just had its first face jointed is a reliable way to produce a twisted, bowed part that is out of tolerance before the glue is even applied.

Moisture meters are the primary diagnostic instrument at every stage. A pin-type meter (Wagner MMC220, Delmhorst BD-10, or equivalent) driven to 1/4 to 1/3 of the board's thickness gives a core reading that is more representative of the true average moisture content than a surface reading. For planks above 8/4 in thickness, the differential between a surface reading and a 1/2-depth reading will tell you whether a moisture gradient still exists and whether the board has finished conditioning. A differential of more than 2 percentage points indicates an active gradient, and the board is not ready for final milling.

Species variation drives significant differences in the acceptable milling workflow. White oak, with roughly 5.6 percent radial and 10.5 percent tangential shrinkage from FSP to oven-dry, is a moderate mover. Hard maple is more severe: 4.8 percent radial and 9.9 percent tangential, but with significantly higher density and a less permeable structure that slows moisture diffusion through the cell walls. Maple dried too fast develops severe surface checking that can penetrate several millimeters into the face, well below what any subsequent planing pass can remove. Softwoods like western red cedar have comparatively low shrinkage coefficients — roughly 2.4 percent radial and 5.0 percent tangential — and forgive faster drying schedules. Teak and other oily tropical species present a different problem: the natural silica content and embedded oils dramatically reduce the speed at which moisture diffuses out of the cell walls, making slow, low-temperature air drying superior to aggressive kiln schedules that would cause the shell to outrun the core by an untenable margin.

### Failure Mode Analysis and Diagnostic Response

The most common milling failure modes fall into predictable categories, each traceable to a specific point in the cellular or moisture dynamics described above.

**Tearout** is the fracture of wood fibers below the intended cut surface, leaving a rough, pitted finish. The root cause is always the same: the cutting tool is levering fibers upward and breaking them at a point below the cut line rather than severing them cleanly at the tool tip. This occurs when cutting against the grain, when blade geometry is too aggressive (too high a rake angle for the density of the species), when the cutting edge is dull, or when the support geometry is inadequate — a chip breaker set too far back from the edge of a bench plane, for example, allows long fibers to lever before the blade terminates them. The fix on the mill is to identify grain direction before every pass, orient the board accordingly, reduce depth of cut, or switch to a spiral head. In hand tool practice, cambering the iron's edge slightly and reducing the throat opening dramatically reduces tearout in difficult grain.

**Winding and bowing after milling** indicates either a moisture gradient that has not equalized or the release of growth stress. All trees contain residual growth stresses that accumulated as the living stem loaded itself under gravity and wind. These stresses are compressive in the outer wood and tensile in the core, and they equilibrate partially during drying but are never fully released until the material is cut. A board milled from near the pith, particularly juvenile wood, will often bow dramatically as the internal compressive stress in the outer fibers is relieved by sawing. The diagnostic test is to compare the behavior of boards from the outer log versus those from the core: if outer boards are stable and core boards are moving, growth stress is the cause. The only remediation is to leave greater rough-milling allowances and re-dimension after the stress has had days or weeks to stabilize at ambient conditions.

**End checking** is surface-to-core cracking at the end grain, driven by the dramatically faster moisture loss from the exposed end grain surface relative to the face and edge. End grain exposed cells lose moisture at roughly 10 to 15 times the rate of face grain, creating a severe local moisture gradient at every end. The conventional response is end-sealing with wax emulsion (Anchorseal being the industry standard) immediately after crosscutting any log or slab that will be air- or kiln-dried. The sealer slows but does not eliminate end-grain moisture loss, forcing the drying front to migrate from the face and edge, reducing the differential rate and minimizing the stress concentration that initiates checks. A related failure, honeycombing, occurs in the interior of thick stock when the core dries faster than expected — typically in species with open, permeable structure — causing internal collapse of the cellular structure. Honeycombed stock looks acceptable on the surface but reveals a crumbled, irregular interior when resawn, destroying any usable thickness.

**Case hardening in service** manifests as a finished piece that moves dramatically out of seasonal equilibrium after installation, even when the shop moisture content appeared correct. The diagnostic is usually a geographic mismatch: lumber conditioned in a coastal Pacific Northwest shop at 12 percent MC and installed in a Denver interior at 6 to 7 percent EMC will lose 5 percentage points of moisture content after installation. At 10 percent tangential shrinkage per percentage point (for a species like beech), that represents a 0.5 percent linear shrinkage across the tangential dimension — easily 1/8 inch across a 24-inch wide tabletop. The correct workflow is to research the target installation environment's average RH, calculate the corresponding EMC, and mill to that target. The EMC tables published by the USDA Forest Products Laboratory (Wood Handbook, Chapter 4) provide species-specific relationships between relative humidity, temperature, and equilibrium moisture content and should be treated as a mandatory reference instrument, as essential to precision milling as a moisture meter or dial indicator.

The practitioner who internalizes these cellular and moisture dynamics — not as abstract knowledge but as a constant physical intuition that informs every cut, every scheduling decision, and every species selection — is operating with a qualitatively different level of control over the material than one who simply follows received rules of thumb. Wood will always move. The goal of expert milling is not to prevent movement but to predict it, design around it, and sequence every operation so that the material's inevitable response to its environment has already been accounted for before the final parts come off the machine.
