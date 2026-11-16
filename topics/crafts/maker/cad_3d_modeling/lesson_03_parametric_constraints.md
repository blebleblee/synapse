# Lesson 3: Parametric Constraints in Design

## 1. First-Principles Intuition & Invariants

There is a moment every maker experiences, usually around the third or fourth revision of a part, when the full cost of designing without constraints becomes visceral. You change the mounting hole diameter by half a millimeter and suddenly the bolt pattern spacing is wrong, the wall thickness violates your minimum printable threshold, and the mating bracket you designed last week no longer fits. You rebuild each feature by hand, hunting down every hardcoded dimension like a syntax error buried in ten thousand lines of code. This is not a workflow problem. It is a philosophical one: you designed *geometry* when you should have designed *intent*.

Parametric constraint-driven modeling is the discipline of encoding the rules that govern a shape, not just the shape itself. When a Fusion 360 sketch carries a fully defined constraint set, the model understands that the bolt circle diameter is always twice the boss outer diameter, that the wall thickness is always 1.5 times the nozzle width, and that the mounting tab length scales with the housing it serves. Change one governing dimension and the entire model reflows correctly, every dependent feature recalculating in topological order. This is what distinguishes a *parametric model* from a *digital drawing*.

The theoretical foundation rests on a branch of computational geometry called constraint satisfaction. Every sketch entity — a line, an arc, a point — carries degrees of freedom. A free point in 2D has two degrees of freedom: it can translate in X and Y. Constraining it to lie on a horizontal centerline removes one degree of freedom. Constraining its X position with a dimension removes the second, and the point is fully defined. A free line segment in 2D has four degrees of freedom: two endpoints, each with two. A horizontal constraint collapses both Y values to equality, removing one. A fixed-length dimension removes another. Anchoring one endpoint removes two more. The line is now fully constrained with four constraints applied across four degrees of freedom, and no amount of dragging will move it. This counting discipline — tracking how many degrees of freedom remain versus how many constraints have been applied — is the first invariant every parametric modeler must internalize.

The critical distinction between *underconstrained* and *overconstrained* sketches matters enormously in a maker context. An underconstrained sketch has remaining degrees of freedom: it will solve, but it will also drift. Regenerate the model after an upstream change, and underconstrained geometry relocates to wherever the solver's minimization algorithm deposits it, often somewhere geometrically valid but semantically wrong. A wall drifts off-center. A fillet origin migrates. The part looks correct until you print it. Overconstraining is the opposite failure: you apply a dimension that conflicts with an existing geometric constraint — dimensioning an angle that is already locked to 90° by perpendicularity, for instance — and the solver throws a conflict error. Both failure modes are recoverable, but neither should reach a finished model. A fully defined sketch, where every entity is constrained to exactly zero remaining degrees of freedom, is the invariant you must enforce before proceeding to any 3D operation.

Beyond sketch-level constraints, parametric design operates at the level of *feature dependencies*. A pad or extrusion references a sketch. A fillet references an edge produced by that pad. A pocket references both a secondary sketch and the face produced by the pad. These relationships form a directed acyclic graph — the model's feature tree — where each node depends on those upstream of it and propagates changes downstream. When you edit the pad's depth, the fillet and pocket recalculate because they reference geometry whose position just changed. This propagation is automatic and instantaneous in modern parametric CAD kernels, but it is not magical: it is a topological sort of the dependency graph, executed in order. Understanding this graph is what allows you to design models that change *correctly* instead of models that change *surprisingly*.

The practical invariant governing all of this is called *design intent*: the set of geometric relationships, dimensional hierarchies, and behavioral rules that describe what the part is *supposed to do* at every scale of modification. A well-constrained parametric model encodes design intent so completely that a collaborator who has never seen the part can open it, change a single global parameter, and trust that the resulting geometry remains valid. For makers building modular systems — parametric enclosures that accept different PCB footprints, adjustable motor mounts that accommodate multiple stator sizes, furniture joinery scaled to different stock thicknesses — design intent is not an abstraction. It is the difference between a reusable asset library and a folder of one-off files.

---

## 2. Core Architecture & Mechanics

### The Constraint Solver and the Feature Tree

Modern parametric CAD tools — Fusion 360, FreeCAD with its Part Design workbench, Onshape — all share a common internal architecture at the sketch level. The constraint solver operates on a system of equations. Each geometric entity contributes unknowns (the coordinates of its defining points) and each constraint contributes equations (relationships those coordinates must satisfy). The solver, typically a variant of Newton-Raphson iterative solving or a direct algebraic solver depending on the kernel, finds the unique solution satisfying all equations simultaneously. When you drag a vertex in an underconstrained sketch and it snaps into a geometrically plausible but slightly wrong position, you are watching the solver's minimization behavior in real time, seeking the nearest valid configuration rather than the intended one.

The feature tree sits above the sketch solver and manages the parametric history. Its architecture looks like this:

```
Root
└── Origin Planes (XY, XZ, YZ)
    └── Sketch_Base
        └── Pad_Body (extrude 40 mm)
            ├── Sketch_MountingHoles
            │   └── Pocket_M3Holes (through-all)
            ├── Fillet_TopEdge (R2 mm)
            └── Sketch_SlotFeature
                └── Pocket_CableSlot (depth 3 mm)
```

Every indented child node references geometry produced by its parent. The Pocket_M3Holes operation references faces and a sketch that only exist because Pad_Body executed first. If you suppress Pad_Body, everything downstream becomes invalid. This is why feature ordering matters: operations that create reference geometry must precede operations that consume it.

The dependency relationships in Fusion 360 are made explicit through the parametric table (Modify → Change Parameters). In FreeCAD, the same role is served by the Spreadsheet workbench linked to model properties. Both systems allow you to define named variables — `wall_thickness = 2.4`, `pcb_width = 68.6`, `standoff_height = 5.0` — and reference those variables as dimension values in any sketch or feature anywhere in the file. The model then becomes a function: its geometry is the output, the named parameters are the inputs, and the feature tree is the computation graph connecting them.

### Geometric Constraints Taxonomy

Fusion 360's sketch toolbar exposes the full constraint vocabulary a maker needs. Each constraint type eliminates a specific degree of freedom or enforces a specific geometric relationship, and understanding exactly what each one does allows you to constrain sketches efficiently rather than by trial-and-error dimension application.

A **coincident** constraint forces two points to occupy the same location: it is how you close open contours and attach arcs to line endpoints, eliminating two degrees of freedom (the independent XY position of one point relative to the other). A **collinear** constraint forces two separate lines to share the same infinite line, useful for aligning features across separate sketch regions. **Parallel** and **perpendicular** constraints govern angular relationships between lines without fixing any position, each consuming one rotational degree of freedom. **Tangent** applied between a line and an arc forces the arc to depart the endpoint tangentially, eliminating the angular discontinuity that would otherwise create a crease in a fillet profile.

**Equal** constraints are among the most powerful for makers. Applied to two lines, they lock their lengths to match — change one and the other follows. Applied to two arcs or circles, they lock radii. A bolt circle sketch with four mounting holes benefits enormously from equal radius and equal angular spacing constraints rather than four independent dimension pairs: when you need to adjust the hole size, one radius dimension changes all four simultaneously.

**Symmetric** constraints about a centerline enforce bilateral symmetry, ensuring that a housing sketch mirrors correctly about its own center axis. This matters most when your design must achieve both aesthetic symmetry and mechanical balance: a symmetric constraint guarantees both properties without requiring you to manually maintain two sets of matching dimensions.

The **fix** constraint is a tool to use deliberately and sparingly. It pins a point or entity to its current absolute position in the sketch coordinate system, consuming all its remaining degrees of freedom in a single operation. Fixing sketch geometry to the origin is good practice — it anchors the model in world space and prevents the entire sketch from floating when upstream references change. Fixing arbitrary mid-sketch points is an anti-pattern: it embeds absolute coordinates into what should be a relational geometry, and those absolute values become constraints that fight against downstream parametric changes.

### Dimensional Constraints and the Parameter Table

A dimensional constraint is a constraint expressed as a numeric value rather than a geometric relationship. Where a perpendicularity constraint says "these two lines meet at 90 degrees," a dimensional constraint says "this line is exactly 24.5 mm long." Both eliminate a degree of freedom, but only the dimensional constraint exposes a value that can be driven parametrically.

The highest-leverage workflow in Fusion 360 is to define all governing dimensions as named user parameters before sketching the first entity. Open Modify → Change Parameters and define your design vocabulary:

| Parameter Name | Expression | Value | Description |
|---|---|---|---|
| `wall_t` | `2.4 mm` | 2.4 mm | Minimum printable wall at 0.4 mm nozzle |
| `pcb_w` | `68.6 mm` | 68.6 mm | PCB width with 0.2 mm tolerance |
| `pcb_l` | `53.3 mm` | 53.3 mm | PCB length with 0.2 mm tolerance |
| `standoff_h` | `5.0 mm` | 5.0 mm | PCB standoff height above floor |
| `lid_gap` | `0.25 mm` | 0.25 mm | Sliding fit clearance, lid to body |
| `m3_clear` | `3.4 mm` | 3.4 mm | M3 clearance hole diameter |
| `m3_boss_od` | `6.5 mm` | 6.5 mm | M3 brass insert boss outer diameter |
| `fillet_r` | `1.5 mm` | 1.5 mm | Interior corner fillet radius |

When you now draw the housing base sketch and dimension the interior width, you type `pcb_w + wall_t * 2` rather than `73.4`. Fusion resolves the expression to 73.4 mm at current parameter values, but if you later discover the PCB footprint is actually 70.1 mm, changing `pcb_w` causes the housing interior, the lid, the standoff pattern, and every downstream feature to recalculate correctly in a single edit. This is design intent made executable.

Expressions in the parameter table support arithmetic operators, trigonometric functions, and cross-parameter references. A mounting hole pitch circle radius can be expressed as `(m3_boss_od / 2) + 1.5 mm`, ensuring adequate wall stock between the boss perimeter and the nearest internal edge regardless of what boss size you later select. A chamfer depth can reference `wall_t * 0.3` so it always proportions correctly to wall thickness.

### Feature Dependencies and Topological Naming

The most common source of parametric model instability in maker workflows is *topological naming fragility* — the tendency of edge, face, and vertex references to break when upstream features change. When a fillet operation references "Edge< 14>" and an upstream feature edit renumbers that edge to "Edge< 17>", the fillet either attaches to the wrong edge or throws a reference error. Both Fusion 360 and FreeCAD have partial mitigations for this (Fusion uses persistent IDs and adaptive topology matching; FreeCAD's TNP fix in version 1.0 addresses it at the kernel level), but the most reliable mitigation remains architectural: structure your features so that references flow cleanly from stable geometry toward dependent geometry, and use datum planes and construction geometry as intermediaries rather than referencing transient edge IDs directly.

The data flow through a well-structured parametric model follows this pattern:

```
Parameter Table (named variables)
        │
        ▼
Anchor Sketch on Origin Plane
(fully constrained, all dims reference parameters)
        │
        ▼
Primary Solid Body (Pad/Extrude)
        │
        ├──► Datum Planes offset from body faces
        │           │
        │           ▼
        │    Secondary Sketches on Datum Planes
        │    (reference parameters, not edge IDs)
        │           │
        │           ▼
        │    Pocket / Boss Features
        │
        └──► Fillet / Chamfer (applied last, to finished geometry)
```

Fillets and chamfers applied at the end of the feature tree are the least fragile because they reference a finished body's edges rather than intermediate construction geometry. Applied mid-tree, they generate new edges that subsequent operations reference, multiplying the topological naming surface area and increasing the risk of reference failures on regeneration.

---

## 3. High-Performance Optimization & Failure Modes

### Designing for Regeneration Speed and Robustness

A parametric model's usefulness is proportional to how reliably and quickly it regenerates when parameters change. In practice, regeneration failures and unexpected geometry are the two modes that erode trust in a parametric workflow and cause makers to abandon it in favor of direct modeling — a costly regression that eliminates the model's adaptability entirely.

The single most effective optimization for regeneration robustness is **sketch economy**: use the minimum number of sketch entities and constraints necessary to define the intended geometry. Overcrowded sketches with hundreds of entities that could be decomposed into multiple simpler sketches regenerate more slowly and are harder to debug when a constraint conflict arises. A body sketch should capture the outer profile. Mounting feature sketches should live in their own sketches on datum planes. Structural cutout sketches should be separate again. Each sketch solves independently, the solver time per sketch scales better than it does for a monolithic sketch, and debugging a constraint error in a 12-entity sketch is orders of magnitude easier than hunting it in a 200-entity one.

**Symmetric design exploitation** significantly reduces constraint count. If your housing is bilaterally symmetric about both its length and width centerlines, model only one quadrant, constrain it fully, then use Fusion's Mirror feature or a symmetric pattern rather than constraining four separate instances. This is not just aesthetic efficiency — it means that when you change a mounting hole position, all four holes move correctly by definition rather than by four independent dimension edits that you might forget to synchronize.

For maker projects with families of related parts — a parametric NEMA motor mount library covering NEMA 14, 17, 23, and 34 footprints, for instance — the multi-body configuration workflow in Fusion 360 (or Variants in Onshape) allows a single file to host all configurations. The parameter table drives a configuration table where each row sets `motor_flange_w`, `pilot_bore_d`, and `bolt_circle_d` to the appropriate NEMA-standard values. Switching configurations regenerates the correct geometry without opening a separate file. The alternative — maintaining separate files per motor size — produces a maintenance burden that compounds every time you need to change the mounting plate thickness.

### Failure Mode: The Sketch Drift Problem

Underconstrained sketches that appear to work correctly during initial design are the primary source of a failure mode that surfaces only on parametric edit: sketch drift. The sketch solves to a geometrically plausible but semantically incorrect configuration when an upstream dimension changes, because the underconstrained entity has freedom to migrate and the solver's minimization deposits it somewhere unexpected.

The diagnostic workflow is straightforward. In Fusion 360, underconstrained entities display in blue; fully constrained entities display in black. A finished sketch should show no blue entities except intentional construction geometry that you are leaving free for reference purposes (which is a rare and deliberate choice). If blue entities remain, right-click each one and inspect which degrees of freedom are still active. Apply constraints to eliminate them before proceeding to the 3D operation. The 10 seconds this takes per sketch saves hours of debugging after the first parametric edit.

FreeCAD's Part Design workbench displays a degree-of-freedom count directly in the solver status panel: a fully constrained sketch shows "Fully constrained (0 redundant)." Redundant constraints are the overconstrained case — a conflict that FreeCAD will refuse to close the sketch with. Fusion 360 is more permissive: it will accept a sketch with redundant constraints if the conflicting constraints are dimensionally consistent (two dimensions that agree on the same value), but this is false comfort. When a parameter change makes those dimensions disagree, the solver fails mid-regeneration.

### Failure Mode: Topological Reference Breakage

When a feature reports a missing or invalid reference after a parametric edit, the repair workflow requires tracing the dependency graph upstream. In Fusion 360, right-click the failed feature in the timeline and select "Edit Feature" — the reference that has broken will be highlighted in red or shown as "undefined" in the feature dialog. You must reselect the intended reference geometry. If the edge or face you intended to reference no longer exists because an upstream change removed it, the design itself may need to be revised — the parametric logic implied a geometry that the new parameters cannot produce.

The mitigation at design time is to prefer **face references over edge references** where possible, since faces persist more reliably through topology changes than edges do, and to prefer **construction axis and datum plane references** over direct body geometry references when you need to locate features relative to the design's coordinate system rather than relative to a specific solid feature's output.

### Failure Mode: Circular References in Parameter Expressions

The parameter table is a directed dependency graph, and circular references — where parameter A's expression references parameter B, whose expression references A — will cause the solver to report a circular dependency error and refuse to evaluate. This most commonly happens when a maker attempts to define toleranced dimensions: `inner_dim = outer_dim - wall_t * 2`, and then separately `outer_dim = inner_dim + wall_t * 2`. Both expressions are mathematically correct in isolation, but together they form a cycle with no base value. The resolution is always to identify one dimension as the independent *driver* and express all others as *driven* functions of it. In this case, `pcb_w` is measured from the physical PCB, so it is the driver. `housing_inner_w = pcb_w + 0.4 mm` is derived. `housing_outer_w = housing_inner_w + wall_t * 2` is derived from that. The dependency flows in one direction: physical measurement → interior clearance → exterior dimension.

### Practical Workflow: Parametric Enclosure from Parameters to Printable Body

The following procedure builds a fully parametric 3D-printable enclosure in Fusion 360, demonstrating every constraint principle from this lesson in sequence.

**Step 1 — Define the parameter table.** Open Modify → Change Parameters. Add `wall_t = 2.4 mm`, `pcb_w = 68.6 mm`, `pcb_l = 53.3 mm`, `standoff_h = 5.0 mm`, `lid_gap = 0.25 mm`, `m3_clear = 3.4 mm`, `m3_boss_od = 6.5 mm`, `body_h = 20.0 mm`, `fillet_r = 1.5 mm`. Close the table.

**Step 2 — Sketch the base profile.** Select the XY origin plane. Draw a rectangle centered on the origin. Apply a **Fix** constraint to the sketch origin point to anchor it. Apply a **Symmetric** constraint to both pairs of opposite lines about the X and Y centerlines. Dimension the width as `pcb_w + wall_t * 2 + 1.6 mm` (adding 0.8 mm per side of PCB-to-wall clearance). Dimension the length as `pcb_l + wall_t * 2 + 1.6 mm`. Confirm the sketch shows black entities and zero remaining degrees of freedom. Close the sketch.

**Step 3 — Extrude the base body.** Extrude the profile to `body_h`. This creates the primary solid.

**Step 4 — Shell the body.** Apply Shell (Modify → Shell) with thickness `wall_t`, selecting the top face as the face to remove. The body is now a hollow box open at the top.

**Step 5 — Create the lid rail sketch.** Create a new sketch on the top face of the shell's side walls. Sketch the rail profile as a rectangular notch, dimensioning the gap width as `lid_gap` from the outer wall face. Extrude-cut the rail.

**Step 6 — Sketch the standoff pattern.** Create an offset construction plane at `wall_t` above the interior floor using Construct → Offset Plane, with offset expression `wall_t`. On this plane, sketch four circles of diameter `m3_boss_od`. Position them symmetrically: dimension their X offset from the sketch centerline as `(pcb_w / 2) - 2.75 mm`, dimension their Y offset as `(pcb_l / 2) - 2.75 mm`. Apply Equal constraints to all four circle diameters. Apply Symmetric about both centerlines. Extrude the circles to `standoff_h` as a Join operation.

**Step 7 — Drill the M3 clearance holes.** Create a new sketch on the top face of the standoffs. Project the standoff circles as construction geometry, then sketch four circles of diameter `m3_clear` concentric with the projected circles, using Coincident constraints at each center. Apply Equal to all four. Extrude-cut through-all.

**Step 8 — Apply fillets last.** Apply a fillet of radius `fillet_r` to all interior vertical edges of the shell. Apply `fillet_r * 2` to all exterior vertical edges. Because fillets are the last feature in the tree, they reference the finished body geometry with the lowest possible risk of topological naming fragility.

**Step 9 — Test parametric regeneration.** Change `pcb_w` to `100.0 mm`. Every dependent dimension — housing width, standoff X positions, lid rail — should recalculate correctly with no errors in the timeline. If any feature shows a warning, the referenced geometry has changed ID: edit that feature, reselect the intended face or edge, and close. Change `pcb_w` back to `68.6 mm` and confirm the model returns to its original geometry. The model now functions as a reusable parametric enclosure generator for any PCB in its size class.

The parametric model you have built is not a static artifact. It is a machine for generating correct geometry across a continuous design space, constrained by the physical realities you encoded at the outset: minimum wall thickness, clearance tolerances, standoff height, hardware sizing. Every maker project that might need to change — and they all do — benefits from this architecture from the first sketch. The constraint-first mindset is not overhead. It is the foundation on which every subsequent revision stands.
