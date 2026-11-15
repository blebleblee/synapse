# Lesson 1: Structural Integrity Fundamentals

## 1. First-Principles Intuition & Invariants

Every house is a managed argument between gravity and material resistance. The roof wants to fall, the floors want to sag, and the walls want to buckle outward under the lateral pressure of wind and seismic load. The only reason a house stands for a century is that a network of members — each one doing a specific mechanical job — continuously wins that argument. When you approach a home repair as a maker-practitioner, your first obligation is not to reach for tools but to read that argument. You must understand what each member is doing before you cut, patch, or reinforce anything.

The fundamental vocabulary here is force path, sometimes called load path. A load path is the continuous chain of structural members through which gravity and lateral forces travel from their point of application down to the soil. A roof loaded with snow transfers that weight into rafters, which bear against a ridge beam or collar tie, then push down into top plates, which transfer load into wall studs, which press against bottom plates, which sit on a sill bolted to the foundation, which distributes pressure into the footing, which spreads it into bearing soil. Break any link in that chain — rot a sill plate, cut through a stud to run a pipe, or crack a footing — and the members above that break must find an alternate path or begin to deflect. When they deflect enough, they fail.

Understanding this chain requires you to internalize the difference between three fundamental stress states. Compression is the state of a column, a stud, or a footing: material is being squeezed along its axis, and the failure mode is buckling when the slenderness ratio of the member becomes too high. A wood stud at standard 8-foot ceiling height has a slenderness ratio well within safe limits; notch it deeply to route conduit, and that ratio changes, and buckling becomes a real risk. Tension is the state of a rafter collar tie or a floor joist chord: material is being pulled along its axis, and the failure mode is rupture at the weakest cross-section or at a fastened connection. Shear is the state of a beam web, a plywood sheathing panel, or the web of an engineered joist: material is being forced to slide along a plane perpendicular to the main axis, and the failure mode is delamination, splitting, or fastener withdrawal. Most structural members in a house experience some combination of all three simultaneously, which is why a floor joist under a point load is a beam in bending — its top edge in compression, its bottom edge in tension, and its web in shear — and why any repair to a joist must respect all three stress states, not just the most visible one.

The invariant that every advanced practitioner must carry is this: **structural members have design capacity that is defined by their geometry, species, grade, span, and connection detail.** Change any one of those variables, and you change the capacity. A doubled 2×10 header spanning 4 feet over a door opening has a specific allowable load. That same doubled 2×10 spanning 6 feet because a previous owner moved a wall does not simply carry less load — it carries *proportionally far less*, because bending moment scales with the square of the span. Double the span, and the bending moment at mid-span quadruples. This is the most dangerous intuition failure a DIY practitioner brings to structural work, and it explains why seemingly minor changes to openings and spans produce failures that appear disproportionate to the modification.

Moisture is the silent partner in almost every residential structural failure. Wood is a hygroscopic material: it absorbs and releases water vapor in response to its environment, and it does so at different rates in different grain orientations. More critically for structural integrity, wood held at moisture content above 19 percent for sustained periods supports fungal decay. Decay does not announce itself on the surface with the same urgency it operates internally — a floor joist can retain a sound-looking outer shell while its core has been reduced to a crumbling, fiber-free mass that has lost 80 percent of its mechanical strength. The practical implication is that in any moisture-exposed area — crawl spaces, rim joists, sill plates, exterior wall bottom plates, areas around plumbing — your structural assessment must include a physical probe test, not just a visual inspection.

---

## 2. Core Architecture & Mechanics

### Platform Frame Construction: The Dominant System

The overwhelming majority of residential construction built after 1940 in North America uses platform framing, in which each floor is built as a complete platform before the walls of the next story are erected on top of it. Understanding this system in mechanical detail is prerequisite to any structural repair work.

```
                    ┌──────────────────────────────────┐
                    │         ROOF ASSEMBLY            │
                    │  Ridge Board / LVL Ridge Beam    │
                    │  Rafters or Engineered Trusses   │
                    └────────────┬─────────────────────┘
                                 │ compression / thrust
                    ┌────────────▼─────────────────────┐
                    │       TOP PLATE (doubled)        │
                    │  load distribution / lateral tie │
                    └────────────┬─────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │            WALL STUDS                   │
              │   16" or 24" o.c., compression members  │
              │   Sheathing provides shear resistance   │
              └──────────────────┬──────────────────────┘
                                 │
                    ┌────────────▼─────────────────────┐
                    │       BOTTOM PLATE               │
                    │   transfers stud load to floor   │
                    └────────────┬─────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │            RIM JOIST                   │
              │   perimeter band, shear + uplift tie   │
              │                                        │
              │   FLOOR JOISTS  ═══════════════════╗  │
              │   bending members (tension bottom,  ║  │
              │   compression top, shear web)       ║  │
              └─────────────────────────────────────╫──┘
                                                    ║
              ┌─────────────────────────────────────╩──┐
              │            SILL PLATE                  │
              │   anchor bolted to foundation wall     │
              │   primary moisture / decay risk zone   │
              └────────────────────────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │        FOUNDATION WALL                  │
              │   poured concrete or CMU block          │
              │   lateral soil pressure resistance      │
              └──────────────────┬──────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │            FOOTING                     │
              │   spreads load over bearing area       │
              │   below frost line                     │
              └────────────────────────────────────────┘
```

Each transition in this diagram is a connection point, and connection points are where structural failures initiate in the vast majority of cases. The sill-to-foundation connection fails when anchor bolts corrode or were never installed with adequate embedment. The joist-to-rim connection fails when rim joist decay allows the floor system to drop off its bearing. The stud-to-top-plate connection fails under seismic or wind uplift when toe-nail fastening alone is insufficient and hurricane ties were omitted.

### Wall Framing Anatomy and Load Transfer Mechanics

A load-bearing wall is distinguished from a partition wall by whether it sits in the load path described above — that is, whether it carries weight from floors or roof above it down to the foundation below. The practical test for a wall's bearing status is never purely visual. You must trace the framing above: if joists or rafters are running perpendicular to the wall and sitting on top of it, or if a beam above terminates into it, it is load-bearing. If joists run parallel to it and simply pass by it, it is more likely a partition, though even this requires verification at the foundation level to confirm there is not a girder or post below transmitting load upward.

A standard platform-framed wall consists of a bottom plate, vertical studs at 16 or 24 inches on center, a doubled top plate, and at any opening, a header spanning the gap. The header is the most frequently undersized or damaged element in residential framing, because every rough opening for a window or door represents a deliberate interruption of the stud pattern, forcing the floor or roof load that would have been distributed across those missing studs to arc around the opening and transfer through the header into the king studs and jack studs on either side. The jack stud (sometimes called a trimmer) transfers the vertical reaction of the header down to the bottom plate. The king stud ties the assembly laterally. If either the jack or king stud is missing, poorly fastened, or rotted at its base, the header will deflect under load, and the opening will rack.

Header sizing follows span tables derived from the tributary load the header must carry, the species and grade of lumber, and whether the wall is a single or double story. The critical insight for repair work is that a header carrying only one story of load above a window in a single-story exterior wall requires dramatically less section depth than the same-width opening in a two-story bearing wall directly below a ridge. Installing the same doubled 2×6 header in both situations — common in older construction — is a sizing error that produces measurable deflection over decades.

### Foundation Assessment: Reading the Evidence

A foundation communicates its condition through a legible vocabulary of cracks, displacement, and moisture. The practitioner's job is to read that vocabulary accurately, distinguishing cosmetic distress from active structural failure.

Concrete and masonry crack for three primary reasons: shrinkage during curing (cosmetic), differential settlement from non-uniform soil bearing (potentially structural), and lateral soil pressure from hydrostatic buildup or expansive clay (structural and urgent). Shrinkage cracks are typically hairline, random in direction, relatively uniform in width along their length, and do not correlate with displacement. Settlement cracks are typically diagonal, initiating at the corners of windows and doors, wider at one end than the other, and correlate with observable differential movement — meaning one side of the crack has moved up or down relative to the other. Lateral pressure cracks run horizontally across a basement wall, often at mid-height where the bending moment from soil pressure is highest, and they are the most serious failure mode because they indicate the wall is actively failing in flexion.

The key diagnostic instrument for foundation assessment is a 4-foot spirit level and a sharp eye for displacement, combined with a crack gauge or even a simple steel rule and a felt-tip pen to mark crack endpoints with a date. Active cracks grow; cosmetic cracks do not. Marking a crack and returning in 30 days tells you definitively whether you are dealing with a historical event or an ongoing process. A digital level with 0.05° resolution (the Bosch GIM60L or equivalent) allows you to quantify floor slope across a room, which is the surface expression of differential foundation settlement.

### Identifying Settlement and Failure Modes in the Field

Settlement produces a recognizable pattern of secondary symptoms throughout the house that an experienced practitioner can read like a diagnostic report. Doors that have begun to rack in their frames — gaps that are wide at one corner and tight at the opposite corner — indicate that the rough opening framing has been distorted by movement in the structure below. Floor surfaces that slope toward an exterior wall, combined with a gap opening between the baseboard and the floor along that wall, indicate that the sill plate or rim joist in that area has softened and compressed, allowing the floor system to drop locally. Stair-step cracking along mortar joints in a brick veneer exterior — running diagonally up from a foundation corner — is one of the most reliable indicators of differential settlement at that corner, because brick veneer has very low tensile strength and cracks precisely where the substrate beneath it has moved.

The critical distinction between elastic and inelastic deformation governs the urgency of your response. A floor joist deflecting under live load that springs back when the load is removed is behaving elastically and within design parameters, assuming the deflection is within L/360 (where L is the span in inches divided by 360 gives the allowable midspan deflection in inches). A floor system that has taken a permanent set — a permanent midspan sag that does not recover — has experienced inelastic deformation, meaning fibers have been permanently damaged or connections have yielded, and the capacity of the system has been reduced. This is the boundary between repair and replacement, and an advanced practitioner must have the diagnostic tools to determine which side of that boundary they are on before committing to a repair strategy.

---

## 3. High-Performance Optimization & Failure Modes

### The Practitioner's Assessment Protocol

Before any structural repair proceeds, a disciplined site assessment must be completed. This is not paperwork — it is the foundation of every decision you will make with a saw, a hydraulic jack, or a fastener gun. The sequence below is non-negotiable in terms of its ordering, because each step reveals information that may change the scope and method of subsequent steps.

**Step 1 — Establish the load path from roof to footing.** Walk the structure vertically: attic first, then each floor, then the crawl space or basement. In the attic, determine whether you have rafter construction or engineered trusses. Trusses carry their load to bearing walls at the perimeter; stick-framed roofs may carry intermediate loads to bearing walls inside the floor plan. Photograph the framing connections at every bearing point.

**Step 2 — Probe all wood members in moisture-exposed zones.** Use a sharp awl or a stiff scratch tool, not a moisture meter alone. A moisture meter confirms elevated moisture content; it cannot tell you that the wood is mechanically sound. Drive the awl perpendicular to the grain at the sill plate, rim joist, and bottom plate of any exterior wall. Sound wood resists penetration; decayed wood allows the tip to sink more than 3mm with hand pressure alone. Any member that fails this probe must be treated as mechanically absent — it is contributing zero capacity to the load path.

**Step 3 — Quantify floor slope and differential elevation.** Establish a reference datum — a single laser reference line from a rotary level set at a consistent height — and measure the floor surface relative to it at a grid of points, minimum 2 feet on center across the full floor area. Record the data in a simple grid sketch. Any slope exceeding ½ inch over 8 feet (0.5% grade) is perceptible and potentially symptomatic. Any slope exceeding 1 inch over 8 feet warrants foundation assessment. Any isolated depression of more than ¾ inch at a single joist bay indicates localized joist failure.

**Step 4 — Map all visible cracking in the foundation.** Photograph, measure width and length of each crack, and note whether displacement is visible across the crack faces. Apply dated crack monitors (commercial products or DIY paper bridges glued across the crack) to any crack wider than 1/16 inch. Return in 30 days before proceeding with repairs in that area.

### Temporary Shoring: The Most Critical Skill Before Any Structural Repair

The single most dangerous failure mode in structural repair work is removing or weakening a load-bearing element without first transferring its load to a temporary support. This kills people. It is worth stating with that directness.

Temporary shoring for residential work uses adjustable steel columns (Acrow props or equivalent) on a continuous load spreader — a doubled 2×10 or an engineered LVL plank — placed parallel to and within 18 inches of the member being repaired, transferring the load above to the floor below and, by extension, to the foundation. The spreader distributes point loads from the shore heads across multiple floor joists, preventing the shore from punching through the floor system. Never place a shore on a single floor joist without a spreader.

The correct procedure is to load the shores before cutting. Install the spreaders above and below, position the Acrow props, and tighten them hand-tight plus three full turns of the adjusting collar. The intent is not to jack the structure up — it is to take the existing load and hold it steady while the compromised member is replaced. If the shore lifts the floor or ceiling even a fraction before the damaged member is removed, you are over-loading the shore's tributary area and creating secondary stress in adjacent framing. Firm contact is the target, not elevation.

### Header Repair and Replacement Workflow

When a header has failed — through undersizing, rot, or damage — its replacement requires maintaining the load path above it continuously throughout the repair. This is the application of the shoring principle above. With shores in place carrying the load from the floor or roof above the opening, the header replacement proceeds as follows:

The jack studs on each side of the opening must be verified as sound before the new header bears on them. If they have compressed or rotted at their base where they contact the bottom plate, the header repair is insufficient — the vertical load path continues to have a break below the header, and the new header will simply re-distribute load into a compromised column. The jack studs and their bearing surfaces must be repaired as part of the same scope.

New header sizing should be calculated from the actual tributary load and span, not assumed from the existing member. For a simple reference, a doubled 2×10 Douglas Fir #2 spanning 6 feet in a one-story bearing wall condition carries roughly 4,500 lbs of allowable load in the Southern Pine/Douglas Fir species group under residential loading assumptions — but this number changes with species, grade, actual span, and tributary area, and the IRC span tables (Table R602.7) must be consulted for the specific jurisdiction and loading condition. Using an LVL (laminated veneer lumber) header of equivalent nominal depth increases capacity by approximately 25-40% and eliminates the creep and moisture movement of solid sawn lumber, making it the preferred choice for any opening wider than 4 feet.

### Joist Sistering: The Primary Repair for Span-Level Failures

The standard repair for a failed, cracked, or notched floor joist is sistering — cutting a new joist of equal or greater dimension, length, and species to full span length, positioning it directly against the damaged joist, and fastening the two together so they act compositely. The composite action is critical: a sister that spans the full bay and bears on both the sill or beam at each end acts as a full replacement of the damaged member's capacity. A sister that only spans part of the bay — a "scab" — does not restore span capacity and addresses only localized damage.

Composite action between a damaged joist and a sister depends on the fastening schedule. The standard schedule for a sistered joist in residential construction is 10d (3-inch) nails in a staggered pattern, two rows, 12 inches on center, plus three nails clustered at each end within 12 inches of the bearing. This creates the shear transfer between the two members that allows them to deflect together as a unit. If the nailing schedule is insufficient, the members simply deflect independently, and the sister provides far less benefit than intended.

Before the sister is installed, the damaged joist must be loaded back to its neutral position. If the joist has taken a permanent set at midspan — a visible sag — a hydraulic jack under a temporary beam (a doubled 2×10 spanning perpendicular across the floor bay) can be used to bring the joist back toward level before the sister is nailed. Do not over-jack: the target is the original elevation, not a correction beyond it, which would introduce new stress into the floor system above. Use the rotary level datum established during your assessment to target the original floor height within ¼ inch.

### Critical Failure Mode: The Notched and Bored Joist

One of the most common structural deficiencies found in older residential construction is the over-notched joist — a full-span floor joist that has been notched on its top or bottom edge, or bored with a large hole through its web, to accommodate plumbing or electrical runs. The IRC provides clear geometric limits for this: notches in the top or bottom of a joist may not exceed one-sixth the joist depth, and notches may not be located in the middle third of the span, where bending moment is highest. Holes bored through the web may not exceed one-third the joist depth, must maintain at least 2 inches of edge distance from both top and bottom edges, and may not be closer than 2 inches to any notch.

The mechanical reason for these limits connects directly to beam bending theory. The extreme fibers of a joist — the top and bottom edges — carry the highest bending stress. Removing material from these locations via notching is structurally equivalent to reducing the joist's depth by twice the notch height, which reduces the section modulus — the geometric property governing bending capacity — by the square of the depth reduction. A notch that removes one-quarter of the joist depth from the bottom edge (the tension face) reduces the section modulus by roughly 44%, cutting bending capacity nearly in half at that cross-section. A plumber who notched that joist because it was convenient has effectively halved your floor capacity at that location, and the evidence years later is a soft, springy floor that the homeowner assumes is simply "old."

The repair for an over-notched joist is sistering with a full-span member as described above, supplemented by a metal repair plate (a notch reinforcement plate rated for the specific notch geometry) if the notch cannot be bypassed by routing. Never fill a notch with wood glue and a wood patch and consider it repaired: the stress concentration at the notch root is a fracture initiation point, and the patch does not reconstitute the fiber continuity that carries tension.

### Foundation Repair Decisions: Where the Practitioner Stops

The advanced maker-practitioner operating in the domain of home structural repair must have a clear and disciplined boundary: foundation crack injection for dormant, non-displacing shrinkage and settlement cracks is within scope; active horizontal cracking in a basement wall indicating lateral soil pressure failure, significant differential settlement exceeding 2 inches across the foundation perimeter, or any sign of footing undermining (visible voids below the footing, soil erosion at the foundation base) are outside the scope of tool-based repair and require a licensed structural engineer before any work proceeds. This is not a liability hedge — it is the application of the same first-principles reasoning that guides all structural work. Those failure modes involve soil mechanics, hydrostatic pressure, and reinforcing steel capacity that cannot be evaluated without site investigation instrumentation and structural calculation beyond what hand tools and jobsite assessment can resolve.

What you can do at the foundation level is document, monitor, control moisture, and stabilize — stopping the conditions that cause ongoing deterioration while the professional assessment proceeds. Installing proper exterior grading (minimum 6-inch drop in the first 10 feet from the foundation), extending downspouts 6 feet from the foundation wall, and ensuring crawl space vapor barrier coverage is complete and lapped at seams all address the moisture input that drives the majority of residential foundation decay. These are not trivial contributions: the majority of residential structural distress is initiated by moisture, and removing the moisture source is often the most consequential intervention available, outperforming any amount of reactive repair work applied to already-damaged members.

The practitioner who understands load paths, can read the language of cracks and settlement, knows how to shore a structure before cutting it, and can accurately determine where their scope ends and an engineer's scope begins is equipped for the full range of residential structural repair. These fundamentals underlie every subsequent lesson in this curriculum — framing repairs, foundation waterproofing, floor system restoration, and lateral load upgrades all proceed from exactly the mechanical and diagnostic framework established here.
