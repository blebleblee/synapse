# Lesson 4: Post-Processing Workflows, Material Properties, Safety Protocols

## 1. First-Principles Intuition & Invariants

Resin printing is, at its chemical core, an act of interrupted polymerization. When the UV light source—whether a laser in SLA, a DLP projector, or an LCD panel in MSLA—traces or flashes each layer, it delivers just enough photon energy to initiate crosslinking within the photopolymer resin. Photoinitiator molecules absorb photons and fragment into free radicals, which then attack the carbon-carbon double bonds in the oligomer and monomer chains, stitching them into the dense three-dimensional polymer network we recognize as a solid part. The critical word here is *initiate*. The energy delivered during printing is calibrated for adhesion and dimensional accuracy, not for maximum mechanical performance. What comes off the build plate is a part that is photochemically alive: partially crosslinked, saturated with unreacted monomer, and structurally immature. Every decision made in post-processing either realizes or wastes the mechanical potential locked inside the material.

This distinction between "printable" and "fully cured" is the foundational invariant of the entire post-processing discipline. Practitioners who treat a washed, still-tacky part as finished are leaving 20–40% of achievable tensile strength on the table, depending on resin chemistry. Conversely, practitioners who over-cure—driving the crosslink density past the material's designed optimum—introduce brittleness by eliminating the elastic segments of the polymer network that confer elongation at break and impact resistance. The relationship between cure energy and mechanical output is not linear. It follows a curve with a distinct peak region, and understanding where your specific resin sits on that curve is what separates controlled fabrication from guesswork.

Uncured resin trapped in recesses, inside hollow features, or in the interstices of support structures is not merely an aesthetic problem. It is a chemical hazard and a structural liability simultaneously. Liquid photopolymer resins contain reactive acrylate monomers—commonly tripropylene glycol diacrylate (TPGDA), bisphenol A ethoxylate diacrylate, or urethane acrylate oligomers—that are classified as skin sensitizers under GHS/CLP regulations. Repeated dermal exposure causes cumulative sensitization, and once sensitized, even trace contact triggers an immune response. The IEC 62471 standard governs photobiological hazard classification of the UV sources themselves, but the chemical hazard of the uncured resin is governed by the material's own Safety Data Sheet (SDS) under OSHA Hazard Communication Standard (HCS) 29 CFR 1910.1200. No advanced practitioner should handle resin without reviewing the SDS for each specific formulation, because the toxicological profile of a castable wax resin, a water-washable PLA-blend resin, and an engineering-grade ABS-like resin differs substantially.

The three-stage invariant that governs all resin post-processing is: **remove, cure, finish**. These stages are not interchangeable in order. Attempting to UV-cure a part before washing locks uncured resin onto the surface permanently, creating a tacky, undercured skin that cannot be removed without abrasion. Washing after final cure is equally pointless—the resin has already crosslinked and no solvent will dissolve it. The sequence has a physical logic dictated by reaction chemistry: wash while monomer is mobile, cure when the surface is clean and dry, finish when mechanical properties are stable and predictable.

---

## 2. Core Architecture & Mechanics

### The Washing Stage: Solvent Selection and Mass Transfer

The purpose of washing is to dissolve and carry away unreacted liquid resin from the part's surface and internal features using a solvent that has strong affinity for the monomer chemistry but does not attack the partially-crosslinked polymer matrix. This is a mass-transfer problem governed by solubility parameters—specifically the Hansen Solubility Parameter (HSP) framework, which decomposes solvent-solute affinity into three components: dispersive interactions (δD), polar interactions (δP), and hydrogen bonding (δH). Most acrylate monomers sit in the HSP space with δD around 18–19 MPa½ and moderate δP and δH values, which explains why isopropyl alcohol (IPA), mean alcohol blend solvents, and tripropylene glycol monomethyl ether (TPM) are effective: they fall close enough in HSP space to dissolve the monomer while the crosslinked matrix—now with significantly different effective HSP—resists swelling.

The standard professional workflow for IPA washing involves two sequential baths, not one. The first bath, the "dirty wash," removes the bulk of uncured resin from the part's surface and reduces the monomer concentration sharply. The second bath, the "clean wash," penetrates finer features and achieves the low residual monomer concentration that clean cure chemistry requires. Bath contamination is not a minor concern: IPA saturated beyond roughly 25–30% resin by volume loses washing efficiency dramatically, and curing a part washed in exhausted solvent produces a surface with diminished gloss and uneven hardness because the residual monomer crosslinks in situ as a contaminating layer.

For practitioners using **Anycubic Wash & Cure** stations or **Elegoo Mercury Plus** units, the agitation cycle should be set to 3–4 minutes per bath at a wash temperature between 20–25°C. Cold IPA below 15°C has measurably higher viscosity and lower diffusivity, extending the time needed to clear resin from deep holes or lattice structures. A common failure mode is washing intricate parts in cold workshop IPA in winter and finding tacky residue at the base of blind holes after cure—a direct consequence of insufficient mass transfer time, not insufficient wash volume.

Water-washable resins replace the acrylate monomers with water-dispersible polyethylene glycol (PEG)-based monomers that allow simple soap-and-water washing. The tradeoff is mechanical: PEG-modified resin networks are inherently more hydrophilic, which means parts absorb atmospheric moisture over time and exhibit measurably lower long-term tensile strength and increased creep compared to solvent-washed standard resins. For prototyping applications this is acceptable; for functional mechanical parts intended for outdoor or humid environments, standard engineering resins washed with IPA or TPM are the correct choice.

The wash-to-cure pipeline in process flow form looks like this:

```
Build plate removal
       │
       ▼
Pre-drain: hold part over vat 60 sec
       │
       ▼
Dirty wash bath (IPA, 3–4 min agitation)
       │
       ▼
Clean wash bath (fresh IPA, 2–3 min agitation)
       │
       ▼
Air dry or compressed air purge (critical: no moisture on surface)
       │
       ▼
Inspect surface under UV penlight for tacky zones
       │
       ▼
UV post-cure station (time + temperature controlled)
       │
       ▼
Support removal
       │
       ▼
Surface finishing
```

The UV penlight inspection step deserves emphasis. A 365–405 nm penlight held at an oblique angle over a washed part causes any residual uncured resin to fluoresce with a faint blue-violet glow. This non-destructive check catches wash failures before cure locks them in. Practitioners who skip it and go straight from wash to cure discover the problem only after the fact, when the part surface shows a glossy irregular skin or remains tacky to the touch in specific zones.

### UV Post-Cure: Photochemical Kinetics and the Dose-Response Relationship

Post-cure is not simply "more light." It is controlled delivery of photon energy (expressed as dose, in mJ/cm²) at the correct wavelength to bring the degree of conversion (DoC)—the fraction of reactive double bonds that have crosslinked—from the printed value (~50–70%) to the material's target maximum (~85–95%). The relationship between cure dose and mechanical output follows the curve shown conceptually below:

```
Tensile        │                   ___________
Strength       │               __/             \
(MPa)          │           __/                  \___
               │       __/                           (embrittlement)
               │   __/
               │__/
               └──────────────────────────────────────────
                           Cure Dose (mJ/cm²)

                  Undercure    Optimal     Overcure
                  Region       Window      Region
```

The optimal window is resin-specific and must be found empirically or taken from the manufacturer's datasheet. Sirayatech Blu, for example, specifies 2–4 minutes in a 405 nm station at 36W equivalent. Elegoo ABS-Like resin reaches peak flexural modulus at approximately 90 seconds under a comparable source. Beyond the optimum, additional crosslinking consumes the flexible chain segments that contribute to elongation at break—the part becomes harder on the Shore D scale but snaps under impact load rather than deforming. This is the mechanism behind the classic failure mode of over-cured dental models: dimensionally accurate, visually perfect, catastrophically brittle.

Temperature during post-cure materially accelerates the reaction. The Arrhenius relationship governs all thermally activated kinetic processes, and free-radical propagation is no exception. Curing a part at 60°C instead of room temperature roughly doubles the reaction rate, achieving equivalent DoC in half the exposure time and—more importantly—allowing crosslinks to form in the rubbery state above the resin's glass transition temperature (Tg), which typically lies between 45–70°C for standard photopolymers. When chains crosslink in the rubbery state, they do so without the internal stress accumulation that occurs when crosslinking is forced in the glassy state at room temperature. The practical result is a part with higher elongation at break and lower internal stress concentration around support nub sites. The Form Cure (Formlabs) and Elegoo Mercury Plus both support heated cure cycles. Practitioners using homemade cure stations from UV nail lamp arrays should use a temperature-controlled enclosure with a heat mat and digital thermostat to replicate this condition.

The wavelength match between your cure station and your resin's photoinitiator absorption spectrum is non-negotiable. Standard photopolymers peak at 385–405 nm. If you use a 365 nm station with a resin formulated for 405 nm (or vice versa), you will either severely undercure the material or risk degrading photoinitiators that have absorption cutoffs below 380 nm. Always verify photoinitiator wavelength from the SDS or manufacturer technical data sheet before choosing a cure light source.

### Support Removal: Mechanical Timing and Tool Selection

The timing of support removal relative to the cure stage governs whether the process is controlled or destructive. There are two schools of practice: pre-cure removal (while the part retains some flexibility) and post-cure removal (after mechanical properties are fully developed). Each has a correct application domain.

Pre-cure support removal is appropriate for thin, flexible parts—dental aligners, flexible TPU-analog resins, and large flat panels where post-cure rigidity would cause the part to crack at support attachment points when stressed by clip cutters. The partially-crosslinked matrix has measurably lower elastic modulus and higher elongation, which allows the support nub to flex away from the surface without propagating a crack into the part geometry. The window for this is narrow: typically 15–30 minutes after washing, before residual photoinitiators in the matrix have undergone dark-state reaction (a slow background crosslinking that continues even without UV, driven by residual radicals).

Post-cure support removal is correct for rigid engineering resins where dimensional accuracy is paramount. Removing supports before cure can cause micro-deflection at support attachment sites, particularly on overhanging flat surfaces, which then cure in a slightly deformed geometry. Flush cutters (Xuron 90° tip flush cutters, or the Tamiya equivalent) are the correct tool for support removal on cured parts. Position the flat face of the cutter against the part surface, not the blade side, to minimize the witness mark. For support nubs that remain proud of the surface after cutting, a progression through 220, 400, and 800 grit wet/dry sandpaper removes material at a controlled rate without introducing deep scratches that resist subsequent finishing.

Large support trees on complex parts benefit from a targeted scoring approach before removal: use a curved-tip flush cutter to sever the support column at mid-height first, reducing the lever arm and the bending moment applied to the attachment point, then trim flush. Attempting to remove a full-height support tree in one cut applies the full column length as a lever, often tearing a chunk of the part surface with it—a failure mode experienced by every practitioner who has worked with large SLA parts at least once.

---

## 3. High-Performance Optimization & Failure Modes

### Maximizing Tensile Strength and Elongation Through Process Control

The practitioner who treats post-processing as a fixed recipe rather than a parameterized process will consistently underperform the material's data sheet values. Advanced workflow optimization begins with understanding which mechanical properties are limited by chemistry (inherent to the resin formulation) and which are limited by process (recoverable through post-processing control).

Tensile strength and flexural modulus are primarily chemistry-limited: once you have selected a resin, there is a ceiling set by the crosslink density and backbone stiffness of the polymer network. However, the degree to which you approach that ceiling is entirely process-controlled. The principal process variables are cure dose, cure temperature, and wash completeness. A practitioner running controlled experiments with a Shore D durometer, a digital caliper, and simple three-point bend tests can empirically map the cure dose vs. flexural strength curve for any resin in a single afternoon, eliminating dependence on manufacturer spec sheets that are often measured under idealized lab conditions.

Elongation at break—the measure of how far a material stretches before fracturing—is more sensitive to overcure than any other mechanical property. For flexible resins (Siraya Tenacious, Elegoo flexible series), elongation values of 180–280% are achievable at optimal cure doses, dropping to under 60% with aggressive overcure. The practical consequence is a part that looks correct but shatters under snap loading instead of deforming. For any application requiring impact or flex resistance, cure dose minimization (achieving DoC sufficiency, not maximization) is the correct strategy. Cure time should be treated as a variable to be tuned downward from the manufacturer recommendation, not a floor to work up from.

Hardness (Shore D) increases monotonically with cure dose up to the crosslink saturation point, which makes it a poor proxy for overall mechanical fitness. A part can be hard and brittle simultaneously. Practitioners who use hardness as their sole quality metric—common in dental lab environments—will optimize for the wrong output variable. The correct triad of quality metrics for a functional resin part is tensile strength (structural integrity), elongation at break (toughness), and dimensional accuracy, measured against the designed geometry with calipers or a surface plate.

### Surface Finishing: Achieving Optical and Functional Surface Quality

A fully cured, support-removed resin part carries layer lines that, depending on the printer's Z-resolution and the layer thickness setting, range from nearly invisible at 25 µm layers to clearly visible at 100 µm layers. Surface finishing addresses both the layer artifact and the matte or semi-matte surface texture typical of MSLA prints.

Wet sanding is the foundational technique. Use wet/dry silicon carbide paper starting at 220 grit if significant layer lines are present, 400 grit for light lines, and progress through 600, 800, 1200, and 2000 grit. Each grit removes the scratch pattern of the previous grit rather than removing bulk material, so there is no value in jumping from 400 directly to 2000—the coarser scratches simply remain visible under the finer surface texture. Lubricate with water and a drop of dish soap to prevent clogging and reduce heat generation. Wet sanding resin dry generates respirable particulate containing crosslinked acrylate polymer fragments, which represent a respiratory hazard; always wet sand or use an N95 P100 respirator in still-air conditions.

For high-gloss optical finishes on SLA parts—common in jewelry casting masters, miniature sculpture, and display models—progress wet sanding to 2000–3000 grit, then apply a plastic polishing compound (Novus 2, Meguiar's PlastX) on a soft cloth in circular motions, followed by Novus 1 for final gloss restoration. This process, executed correctly, produces a surface that is indistinguishable by eye from injection-molded acrylic.

Filler primer (Rustoleum 2X filler primer, Tamiya Fine Surface Primer) applied in thin coats before fine sanding fills micro-pores and residual layer line valleys that mechanical sanding cannot reach efficiently. The primer acts as a sacrificial fill material: apply, let cure for 2–4 hours, sand at 400–600 grit, repeat. Two primer-sand cycles are typically sufficient to achieve a surface suitable for topcoat paint adhesion without visible subsurface texture.

Resin-compatible UV-activated spot fill resins (such as Bondic or dedicated resin gap fillers) allow precise filling of support witness marks, chip voids, or surface defects before final sanding. Apply a micro-drop, cure for 30 seconds with a 405 nm penlight, then sand flush. The repaired area has the same cure chemistry as the substrate and sands identically, unlike cyanoacrylate fills which create a harder spot visible in raking light.

### Toxicity Handling and Ventilation Engineering

The chemical hazard of photopolymer resins is concentrated in two states: liquid (uncured) and aerosolized (from wash vapor or sanding). The crosslinked solid state is largely inert to casual handling, though dermal contact with cured resin dust during dry sanding still warrants PPE.

Nitrile gloves are the correct barrier for liquid resin handling. Standard latex gloves have inadequate acrylate monomer resistance—acrylates permeate latex at measurable rates within minutes of contact. Use 4–6 mil nitrile gloves minimum, and double-glove for extended handling or pour operations. Change gloves when contaminated rather than wiping—wiping spreads the sensitizing monomer to new contact areas. Splash goggles (not safety glasses) protect the eyes from vat overflow events and splatter during build plate removal.

Ventilation is the primary engineering control for vapor exposure. The key vapor-phase hazard is the mixture of acrylate monomers (TPGDA, HDDA, and similar) volatilizing from open vats, wash containers, and drying parts. OSHA does not publish a specific PEL for TPGDA, but the ACGIH Threshold Limit Value (TLV-TWA) for general acrylate esters is 2–10 ppm depending on specific compound, and even a small desktop SLA printer in a poorly ventilated room will routinely exceed these values during active printing and washing. A dedicated enclosure with a carbon-activated air filtration unit exhausted outdoors, or at minimum a high-flow carbon filter capable of 10+ air changes per hour in the workspace, is the correct engineering solution. Consumer-grade "air purifiers" with HEPA-only filtration do not capture organic vapor; activated carbon is mandatory.

Skin sensitization is a threshold phenomenon with a one-way ratchet: once sensitized, there is no desensitization. Practitioners who have worked with resins unprotected and developed contact dermatitis are permanently restricted in their exposure tolerance. This is not a recoverable condition. The discipline of consistent PPE use from the first session, not after a reaction event, is the correct professional posture.

### Disposal Regulations and Environmental Compliance

Uncured liquid resin is classified as hazardous waste in most jurisdictions. In the United States, waste resin falls under EPA RCRA characterization (D001 ignitability for IPA-rich wash waste, and potentially D003 or specific listed waste depending on formulation). Pouring uncured resin or contaminated IPA down household drains is illegal and environmentally harmful—acrylate monomers are acutely toxic to aquatic organisms at concentrations as low as 1–10 mg/L.

The standard compliant disposal workflow uses the sun-curing method for small-volume waste: pour contaminated IPA into a wide, clear container and expose to direct sunlight for 6–8 hours (or 2–4 hours in a 405 nm cure station) until the resin solids have fully polymerized and precipitated to the bottom. The supernatant IPA, now depleted of reactive monomer, can be re-evaluated under local solvent disposal regulations—in many jurisdictions, once the resin solids are separated, the IPA fraction qualifies for disposal as standard organic solvent waste rather than reactive hazardous waste. The cured resin solids, now fully crosslinked and chemically inert, can be disposed of with solid waste in most jurisdictions, though local regulations must be verified. Never dispose of solid-waste resin without confirming complete cure: a tacky, partially-cured mass is still a reactive material.

Large-volume professional waste (more than 1 gallon per week) must be collected by a licensed hazardous waste contractor. Many commercial photopolymer resin suppliers offer take-back programs, and several regional hazardous waste collection facilities accept small-quantity generator (SQG) resin waste under EPA's simplified SQG regulations enacted in the 2020 Generator Improvements Rule. Document all waste disposal with manifests and retain records for a minimum of three years, the standard RCRA record retention period for SQGs.

Wash station IPA management is best handled through a closed-loop system: dirty wash becomes the second bath after a solar cure cycle removes the resin fraction, then cycles to dirty wash status again. This extends solvent life by 3–5x compared to single-use disposal, reduces total waste volume, and decreases the frequency of compliant disposal events. Advanced fabrication shops using high-throughput resin printing often invest in rotary evaporators or solvent recovery stills to reclaim IPA from wash waste at purities exceeding 95%, a practice that is both economically and environmentally rational at scale.

The practitioner who commands the full post-processing pipeline—chemically informed wash technique, dose-controlled UV cure, careful support removal, competent surface finishing, rigorous hazard management, and legally compliant disposal—transforms resin printing from a novelty output process into a disciplined fabrication methodology capable of producing parts that meet professional tolerances, safety standards, and environmental obligations simultaneously. The chemistry will not forgive shortcuts, but it rewards methodical practitioners with mechanical performance and surface quality that rival any other manufacturing process available at the desktop scale.
