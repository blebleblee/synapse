# Lesson 1: Metallurgical Fundamentals of Fusion Welding

## 1. First-Principles Intuition & Invariants

Every weld bead is a miniature metallurgical event compressed into seconds. What looks from the outside like a simple fusion of two metal edges is, at the atomic scale, a cascade of crystal destruction, liquid chaos, and controlled re-solidification. To weld well is to understand what you are asking the metal to do — and why it sometimes refuses.

Metals derive their mechanical properties almost entirely from the arrangement of their atoms. At room temperature, most structural metals exist as polycrystalline solids: vast populations of individual crystalline grains, each a geometrically ordered lattice of atoms, all oriented at slightly different angles to their neighbors. The boundaries between these grains are regions of atomic misfit, slightly higher in energy than the grain interiors, and they exert a profound influence on how metal deforms, fractures, and responds to heat. When a welder strikes an arc, the first metallurgical act is the obliteration of this grain structure in a small region, replacing it with a pool of liquid metal that has no crystalline order at all.

The three principal crystal structures in engineering metals are body-centered cubic (BCC), face-centered cubic (FCC), and hexagonal close-packed (HCP). Low-carbon steel at room temperature adopts a BCC arrangement called ferrite, in which iron atoms occupy the corners of a cube with one atom at the geometric center. This structure is relatively open — the packing factor is about 68% — which means carbon atoms can sit in the interstitial gaps, though with limited solubility (roughly 0.025 wt% at room temperature). Heat that same steel above 912°C and the iron transforms allotropically to austenite, an FCC structure. The FCC arrangement packs atoms more tightly (74% packing factor) but, counterintuitively, it dissolves carbon far more readily, up to about 2.1 wt% at 1148°C. This transformation — the eutectoid reaction and the full iron-carbon phase diagram — is the master key to understanding everything that happens in a steel weld.

The iron-carbon phase diagram is not an abstract academic artifact. It is a roadmap that every weld bead traverses in real time. As the arc moves forward, every point in the surrounding base metal experiences a unique thermal cycle depending on its distance from the fusion line. Metal very close to the arc reaches temperatures approaching 1500°C and re-enters the fully liquid (liquidus) region. Metal a few millimeters further sits in the solid-state austenite field. Metal further still passes through the two-phase ferrite-plus-austenite region without ever melting. And metal beyond a threshold distance — perhaps 15–30 mm for a typical structural steel weld, depending on heat input — experiences no phase transformation at all, though it still accumulates residual stress from the thermal expansion and contraction cycle. The practitioner who can mentally walk a temperature profile through the phase diagram, correlating each isothermal contour to a metallurgical outcome, has a diagnostic tool of extraordinary power.

Solidification theory governs what happens as the weld pool cools back to solid. Liquid metal does not freeze uniformly; it nucleates and grows. In a casting, nucleation typically begins at the mold wall where heterogeneous nucleation sites (surface irregularities, particles) provide energy-efficient starting points. In a fusion weld, something more elegant occurs: the existing grain structure of the base metal at the fusion boundary acts as a template. Columnar grains epitaxially nucleate from the partially melted grains at the fusion line and grow competitively inward, each grain extending in the direction of maximum heat extraction — which is perpendicular to the fusion boundary and therefore generally toward the weld centerline. Grains oriented with their preferred growth direction (the ⟨100⟩ crystallographic direction in cubic metals) aligned with the heat flux outcompete their neighbors and grow longer. The result is a classic columnar dendritic structure with grains that look, under a macro-etch, like elongated fingers pointing toward the weld center. Where columnar grains from opposing sides of the pool meet at the weld centerline, a zone of impurity segregation and geometric misfit forms, which is exactly where centerline solidification cracking initiates when sulfur or phosphorus contents are elevated.

The solidification temperature range is a critical concept. Pure metals freeze at a single temperature. Alloys freeze over a range bounded by the liquidus (last liquid disappears below this) and the solidus (last solid disappears above this). The wider this range, the longer the metal spends as a semi-solid "mushy zone," and the more opportunity there is for the columnar dendrite tips to be starved of liquid as surrounding metal contracts. This starvation is the mechanistic root of hot cracking, also called solidification cracking. For this reason, high-sulfur steels, free-machining grades, and certain high-strength aluminum alloys (particularly those in the 7xxx series with their wide freezing ranges) demand either process accommodations or the selection of filler metals that deliberately add elements to modify the solidification mode.

The concept of carbon equivalent (CE) encodes much of this phase-diagram reasoning into a single practitioner-ready number. The most widely used formula is:

$$CE = C + \frac{Mn}{6} + \frac{Cr + Mo + V}{5} + \frac{Ni + Cu}{15}$$

Each alloying element is weighted by its effect on hardenability — that is, its tendency to suppress the diffusion-controlled austenite decomposition and instead allow hard, brittle martensite to form on rapid cooling. When CE exceeds approximately 0.40–0.45 for mild and low-alloy steels, the weld thermal cycle becomes capable of producing enough martensite in the heat-affected zone to cause hydrogen-induced cracking under restraint. Preheat is the practitioner's primary countermeasure: by raising the base metal temperature before welding, you slow the cooling rate, buying diffusion time for benign ferrite-pearlite transformations rather than the diffusionless shear transformation to martensite. The required preheat temperature climbs nonlinearly with CE, and for restrained thick-section joints in high-strength steel, 150–250°C preheat is not uncommon. Measuring preheat with a contact pyrometer or Tempilstik crayon before striking the arc is not bureaucratic box-checking; it is the difference between a weld that serves its design life and one that cracks within days under service stress.

---

## 2. Core Architecture & Mechanics

### The Thermal Architecture of a Fusion Weld

The weld cross-section is not a uniform mass of re-solidified metal. It is a precisely stratified set of zones, each defined by the peak temperature it reached during the thermal cycle and the subsequent cooling rate. Understanding this architecture is prerequisite to reading a macro-etch, interpreting a failed weld, or specifying a post-weld heat treatment.

```
WELD CROSS-SECTION — ZONE MAP (transverse view, single-pass butt weld)
═══════════════════════════════════════════════════════════════════════

   BASE METAL          HAZ                  WELD METAL
   (unaffected)  ←─────────────────────→  (fusion zone)
   ─────────────┬───┬────┬────┬────┬────┬──────────────────
                │ A │ B  │ C  │ D  │ E  │
   ─────────────┴───┴────┴────┴────┴────┴──────────────────
                 │    │    │    │    │
                 │    │    │    │    └─ E: Subcritical HAZ
                 │    │    │    │       (Tp < Ac1, ~600–720°C)
                 │    │    │    │       Stress-relief range; carbide
                 │    │    │    │       coarsening in prior-tempered steels
                 │    │    │    │
                 │    │    │    └─ D: Intercritical HAZ
                 │    │    │       (Tp ~720–820°C, Ac1–Ac3)
                 │    │    │       Partial austenitization; mixed
                 │    │    │       ferrite + fresh martensite (embrittlement risk)
                 │    │    │
                 │    │    └─ C: Fine-Grained HAZ (FGHAZ)
                 │    │       (Tp ~900–1100°C, above Ac3)
                 │    │       Full austenitization, fine recrystallized grains;
                 │    │       often toughest HAZ sub-zone
                 │    │
                 │    └─ B: Coarse-Grained HAZ (CGHAZ)
                 │       (Tp ~1100–1450°C, near fusion line)
                 │       Prior austenite grains grow rapidly;
                 │       highest hardenability; worst toughness
                 │
                 └─ A: Fusion Boundary / Partial Melt Zone
                    (Tp ~1450–1500°C)
                    Constitutional liquation possible;
                    epitaxial nucleation site for columnar grains
```

The coarse-grained heat-affected zone (CGHAZ) commands the most attention from a failure-analysis standpoint. When steel is heated above roughly 1100°C, austenite grain boundary migration becomes rapid, and the grain-boundary pinning particles — typically titanium nitrides (TiN) or aluminum oxides — either dissolve into the matrix or coarsen beyond the point where they can retard boundary motion. The result is a dramatic increase in prior austenite grain size. Because hardenability scales directly with austenite grain size (larger grains mean longer diffusion paths for carbon during cooling, reducing the kinetics of pearlite formation and increasing the tendency toward martensite), the CGHAZ of high-CE steels is precisely where hydrogen-induced cold cracking initiates. The fracture path follows prior austenite grain boundaries, and the fracture surface has a characteristic intergranular, faceted appearance when viewed under a scanning electron microscope.

The grain growth mechanism is well-described by the Arrhenius-type relationship:

$$d^2 - d_0^2 = K \cdot t \cdot e^{-Q / RT}$$

where $d$ is the final grain diameter, $d_0$ the initial diameter, $K$ a material constant, $t$ the time at temperature, $Q$ the activation energy for grain boundary migration, $R$ the gas constant, and $T$ absolute temperature. What this equation tells the practitioner is that both peak temperature and time at peak temperature drive coarsening. High heat input welds — slow travel speed, high amperage — have shallower thermal gradients and expose the CGHAZ to elevated temperatures for longer, producing more severe grain coarsening than the same joint welded at lower heat input. This is a central reason why the AWS D1.1 Structural Welding Code and most pressure vessel codes impose maximum as well as minimum heat input limits: the minimum prevents lack of fusion and cracking, the maximum prevents excessive HAZ degradation.

### The Residual Stress Engine

Residual stresses are locked-in stresses that persist after the heat source has moved on and the joint has returned to room temperature. They form because the weld metal and surrounding HAZ attempt to contract on cooling but are physically restrained by the surrounding cold base metal. The mechanism unfolds in two stages that are worth understanding precisely, because misidentifying the stage leads to wrong remediation.

During the heating phase, the metal near the arc expands thermally. The surrounding cold metal — essentially infinite in thermal mass compared to the weld zone — prevents this expansion. The hot metal, unable to expand freely, is compressed plastically. Because metals are weaker at elevated temperature, this plastic compression requires relatively low stress. During the cooling phase, that same metal tries to contract, but it has been permanently plastically compressed, so it now has less volume than it "wants." As it cools and gains strength, the contraction generates tensile stress that the now-stronger metal cannot relax by further plastic deformation. The result is biaxial or triaxial tensile residual stress in the weld and adjacent HAZ, potentially approaching the yield strength of the material.

The distribution of these stresses follows a characteristic pattern. Longitudinal stresses (parallel to the weld axis) are highest directly over the weld, reaching values near the yield strength in a narrow band, then transitioning to balancing compressive stresses in the outer regions of the plate. Transverse stresses (perpendicular to the weld axis) are more uniform but can be significantly elevated by joint restraint — a weld made between two rigidly clamped plates will carry far higher transverse residual stress than the same weld made on freely supported plates.

```
RESIDUAL STRESS DISTRIBUTION — Longitudinal Stress Profile
(transverse cross-section, single-pass butt weld in steel plate)

  Stress
  (+Tensile)
     │
 +Fy ┤           ╭──────────╮
     │          ╱            ╲
     │         ╱              ╲
   0 ┤─────╮──╯                ╰──╭─────────────────
     │      ╲                    ╱
     │       ╲                  ╱
 -Fc ┤        ╰────────────────╯
     │
  (-Compressive)
     └───────────────────────────────────────────────
       Plate edge   Weld CL    HAZ    Base metal far field

  Fy = Approximate yield strength (tension peak in weld metal)
  Fc = Balancing compressive stress in base metal
```

Distortion is the visible, geometric consequence of these same thermal strains. Angular distortion in a butt weld occurs because the weld reinforcement on the crown contracts more than the root, rotating the plate edges upward. Longitudinal bowing occurs because the weld contracts along its length, bowing a long weldment into a slight arc. Transverse shrinkage reduces the total joint width by a predictable amount — roughly 1–3 mm for a single-pass butt weld in 10 mm mild steel — which must be accounted for in precise fabrication. Skilled fabricators pre-set their joints with a deliberate angular offset in the direction opposite the expected distortion, so the assembly springs into geometric tolerance as it cools.

### Transformation and Phase Path in a TIG-Welded Low-Carbon Steel

Walking a specific point in the CGHAZ of a low-carbon steel (0.18 wt% C, CE ≈ 0.42) through its full thermal cycle makes the abstract mechanisms concrete. At peak temperature, say 1250°C, the structure is single-phase austenite with a prior austenite grain size of perhaps 80–120 µm (compared to 10–20 µm in the base metal). As the arc passes and cooling begins, the phase diagram trajectory passes through the Ac3 temperature (roughly 850°C) and into the two-phase field. For this CE value, the critical question is whether the cooling rate at 800–500°C (the t8/5 cooling time, measured in seconds) exceeds the critical cooling rate for martensite formation, which can be read from the continuous cooling transformation (CCT) diagram for the specific alloy.

For a t8/5 of approximately 15 seconds — representative of a low heat input pass with preheat to 100°C on 20 mm plate — this composition will produce primarily bainite with some martensite, hardness in the CGHAZ around 320–380 HV. For a t8/5 of 30 seconds (higher heat input, or 150°C preheat), the microstructure shifts toward upper bainite and ferrite, hardness drops to 250–300 HV, and toughness improves substantially. At t8/5 of 8 seconds (no preheat, rapid cooling on thick plate), martensite dominates, hardness exceeds 400 HV, and the structure is brittle and susceptible to hydrogen cracking. The Vickers hardness limit of 350 HV in the HAZ is specified in standards such as ISO 15614 and BS 7910 precisely because it represents the empirical boundary below which hydrogen-induced cracking risk becomes manageable.

---

## 3. High-Performance Optimization & Failure Modes

### Heat Input Control as the Primary Process Variable

Heat input is the single lever that most directly controls HAZ width, grain coarsening severity, cooling rate, and distortion simultaneously. It is calculated as:

$$Q = \frac{\eta \cdot V \cdot I}{v}$$

where $Q$ is heat input in joules per millimeter, $\eta$ is the process thermal efficiency (approximately 0.60 for GTAW/TIG, 0.80 for SMAW, 0.85 for GMAW/MIG), $V$ is arc voltage in volts, $I$ is welding current in amperes, and $v$ is travel speed in millimeters per second. The efficiency factor $\eta$ accounts for the fact that not all electrical energy deposited by the arc is transferred to the workpiece; some radiates to the surroundings. TIG welding is less thermally efficient than MIG precisely because the non-consumable tungsten electrode and the relatively diffuse arc lose more heat to the shielding gas and surroundings.

Optimizing heat input for a specific application requires knowing what constraint is binding. In structural steel welded to AWS D1.1, the concern is usually maximum heat input to avoid HAZ toughness degradation. For a Grade 50 (ASTM A572) steel, keeping Q below 2.5 kJ/mm preserves acceptable CGHAZ toughness in most cases. For a quenched-and-tempered high-strength steel like A514 (yield strength 690 MPa), the tempering temperature of roughly 600°C means the subcritical HAZ can be over-tempered by even modest heat inputs, and maximum heat input is strictly enforced. Some offshore structural codes for high-strength steels specify a maximum of 1.5 kJ/mm for multi-pass welds.

In the shop, controlling heat input means more than setting machine parameters. It means maintaining consistent travel speed, which is the variable most practitioners have least discipline about. A skilled TIG welder who slows down to renegotiate a tricky joint configuration may double or triple the local heat input at that point. Using a marked weld coupon as a travel speed calibration tool — welding along a ruled line and measuring bead length per unit time before welding the actual joint — adds a few minutes of setup that eliminates significant variability.

### Hydrogen Management: The Cold Cracking Protocol

Hydrogen-induced cracking (HIC), also called cold cracking or delayed cracking, is the most consequential failure mode in structural steel welding. It requires three simultaneous conditions: a susceptible microstructure (martensite or hard bainite), a sufficient concentration of diffusible hydrogen, and tensile stress (which residual stress alone is sufficient to supply). Remove any one of the three and cracking cannot occur. In practice, the practitioner attacks all three.

Diffusible hydrogen enters the weld pool from moisture in electrode coatings, shielding gas contamination, surface hydrocarbon contamination, or rust on the base metal. Low-hydrogen electrodes (E7016, E7018) are manufactured with controlled baking schedules to keep their coverings below 4 ml/100g of diffusible hydrogen, classified as H4 or H8 in the AWS classification system. Moisture re-absorption is rapid — an E7018 electrode left exposed to 70% relative humidity can exceed its hydrogen limit within four hours. A portable holding oven set to 120–150°C, with electrodes placed into it directly from the hermetically sealed container, is not optional equipment; it is a process control device. When welding with GMAW or FCAW-G, the shielding gas cylinder and all hose connections must be leak-free, since atmospheric nitrogen and moisture ingress through micro-leaks at fittings raise diffusible hydrogen levels in FCAW-G consumables substantially.

Post-weld heat treatment (PWHT), typically a soaking at 580–650°C for carbon and low-alloy steels, serves multiple metallurgical functions simultaneously. It relieves residual stress by allowing plastic relaxation at temperatures where the yield strength has dropped to approximately 10–15% of its room-temperature value. It also promotes diffusion of dissolved hydrogen out of the metal — the diffusivity of hydrogen in BCC ferrite at 600°C is roughly six orders of magnitude higher than at 20°C, meaning hydrogen that would take days or weeks to escape at room temperature exits the section in hours during PWHT. Additionally, PWHT tempers martensite formed in the CGHAZ, converting the brittle body-centered tetragonal (BCT) martensite to a mixture of ferrite and fine carbides with dramatically improved toughness. The PWHT soak time is typically one hour per 25 mm of section thickness, with controlled heating and cooling rates (usually 100–150°C/hour above 300°C) to prevent thermal shock gradients that would re-introduce stress.

### Solidification Cracking: Filler Metal Selection as a Countermeasure

Hot cracking at the weld centerline or along columnar grain boundaries during solidification is governed by two compositional parameters above all others: the sulfur-to-manganese ratio and the net carbon content. Sulfur forms iron-sulfide films (FeS) with a melting point around 988°C, far below the solidification completion temperature of steel. These films wet the columnar grain boundaries and remain liquid as the surrounding metal contracts, providing a path of zero cohesion along which shrinkage strain accumulates and tears the boundary open. Manganese counters this by scavenging sulfur to form manganese sulfide (MnS), which has a higher melting point, a globular morphology, and negligible grain-boundary wetting tendency. The safe threshold is generally considered a Mn:S ratio exceeding 20:1. Checking the mill certificate (Material Test Report, or MTR) for the actual sulfur content of the base metal, and specifying filler metals with low sulfur and adequate manganese, is the first-line prevention.

For austenitic stainless steels, the dominant cracking mode is also solidification cracking, but the metallurgical mechanism involves ferrite content rather than sulfur. Austenitic filler metals that solidify in a primary ferrite mode (FA mode, typically 3–10 FN on the Ferrite Number scale measured with a Magne-Gage or Fischer Feritscope) are substantially more resistant to solidification cracking than fully austenitic deposits. The Schaeffler and WRC-1992 diagrams, plotting chromium equivalent against nickel equivalent to predict the solidification mode and resultant room-temperature microstructure, are the working tools for selecting stainless steel filler metals. The practical workflow is to calculate the chromium and nickel equivalents of the filler from its certified composition, plot the point on the WRC-1992 diagram, and confirm it falls in the FA solidification mode region before specifying the consumable for a critical joint.

### Reading Failure: The Macro-Etch and Hardness Traverse

When a weld joint fails in service or fails a code-required mechanical test, the diagnostic sequence starts at the bench with a macro-etch and a Vickers hardness traverse. The macro-etch — typically 10% ammonium persulfate solution applied with a cotton swab to a cross-sectioned and polished weld sample, or nital (2–4% nitric acid in ethanol) for steels — reveals the fusion boundary, HAZ width, bead geometry, root penetration, and any visible cracks or lack-of-fusion defects at 1:1 to 5:1 magnification. What you are looking for first is geometry: excessive reinforcement height (promotes stress concentration), convex root bead (indicates lack of sidewall fusion below), or incomplete root penetration (a planar stress concentrator worse than a rounded defect of equivalent size).

The Vickers hardness traverse, performed at 0.5–1 mm intervals across the weld metal, through the CGHAZ and FGHAZ, and into the base metal, produces a hardness profile that maps to the microstructural zones described earlier. A sharp hardness peak at the fusion line exceeding 350 HV on a carbon steel weld produced without prescribed preheat is not a statistical outlier; it is a martensite flag and a cold cracking risk. Cross-correlating the hardness peak location with the macro-etch zone boundaries allows the practitioner to calculate the HAZ width, estimate the peak temperature experienced by the hardest point using empirical correlations with austenite grain size, and determine whether the thermal cycle was within the range defined in the qualifying procedure qualification record (PQR). A weld that passes visual and radiographic examination can still harbor a critically hard HAZ — which is precisely why hardness testing is mandatory in pressure vessel codes (ASME Section IX, PW-39), offshore structural codes (DNV-GL-OS-C401), and pipeline fabrication standards (API 1104).

The logic running through all of these techniques is the same: the microstructure is the record. Heat, time, composition, and stress leave evidence encoded in grain size, phase distribution, hardness, and fracture morphology. The welder who understands what the metal is doing during the thermal cycle, and the inspector who can read the metallurgical evidence afterward, are both exercising the same fundamental literacy — a literacy built on the first principles of crystal structure, phase equilibria, and thermally activated diffusion that this lesson has laid out as its foundation.
