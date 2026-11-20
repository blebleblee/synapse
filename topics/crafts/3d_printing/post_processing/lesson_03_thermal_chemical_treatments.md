# Lesson 3: Thermal and Chemical Treatments

## 1. First-Principles Intuition & Invariants

Every 3D-printed part carries the history of its fabrication inside it. FDM parts are, at the microscopic level, a stack of partially-fused polymer beads, each bead bonded to the layer beneath it only across the narrow contact zone where the melt briefly exceeded the glass-transition or crystallization temperature before the ambient air stole the heat away. SLA and MSLA photopolymers present a different but equally important internal incompleteness: the UV exposure during printing initiates crosslinking but rarely drives it to completion, leaving reactive monomer pockets distributed through the matrix like unlit fuses. Even the most carefully dialed print, one with optimal layer times, well-calibrated exposure, and controlled ambient temperature, emerges from the machine as a metastable object. Thermal and chemical post-processing treatments exist to resolve that metastability: to push the material from the state it was printed in toward the state it is theoretically capable of occupying.

Understanding what these treatments accomplish requires a brief but honest reckoning with polymer physics. When a semi-crystalline thermoplastic such as PLA, PETG, PA12, or POM is printed, the rapid cooling through the melt prevents the polymer chains from fully organizing into the low-energy crystalline structures the material would form under slow, controlled solidification. The chains freeze in a partially amorphous configuration. Amorphous domains are not defects in a catastrophic sense—they give the material ductility and toughness—but they also define its ceiling. Creep resistance, dimensional stability under sustained load, and thermal deflection temperature (HDT) are all governed by how much crystalline order the matrix contains. Annealing is fundamentally the process of returning the polymer chains to thermal mobility, below the melt point but above the glass-transition temperature T_g, so they can find and settle into those crystalline configurations. The reward is a measurable increase in HDT and stiffness, often dramatic: a PLA part annealed at 80–90 °C for 90 minutes can see its heat deflection temperature rise from roughly 55 °C to over 100 °C.

The chemical dimension operates on a parallel logic. Vapor smoothing with acetone or ethyl acetate does not simply dissolve the surface—it temporarily plasticizes it. Solvent molecules penetrate the outermost polymer chains, depress the local T_g below ambient, and allow surface tension to drive chain mobility and layer-line reflow. When the solvent evaporates, the surface re-vitrifies as a continuous, nearly monolithic skin. The underlying physics is the Flory-Huggins interaction parameter χ between solvent and polymer: when χ is small, the solvent is thermodynamically compatible with the polymer matrix, and penetration is rapid and uniform. When χ is large, the solvent is incompatible and nothing happens. This is why acetone dissolves ABS and ASA but does nothing to PLA; why dichloromethane attacks nylon and polycarbonate but leaves PETG nearly untouched; and why ethyl acetate is the preferred solvent for PLA, sitting at a χ close enough to equilibrium plasticization without catastrophic chain scission.

UV post-curing for resin parts follows yet another first principle: photoinitiator exhaustion. During MSLA printing, the light source exposes each layer for a few seconds, activating photoinitiators that generate free radicals and begin chain crosslinking. The process is mass-transfer limited: once surface oxygen quenches the radicals and the layer is no longer illuminated, the reaction stalls, often at 60–80% crosslink conversion. A proper post-cure station continues the reaction by flooding the part with broadband UV, typically centered at 365–405 nm, in an oxygen-depleted environment. The final degree of crosslink conversion governs every mechanical property—tensile strength, Shore hardness, chemical resistance—so this step is not cosmetic. It is completion of the manufacturing process itself.

These treatments share a common invariant that the advanced practitioner must internalize before touching any part: material identity is non-negotiable. Every thermal and chemical treatment has a material-specific operating window, and operating outside that window produces outcomes ranging from warped geometry to catastrophic chain degradation. A PLA part placed in an acetone chamber will show no smoothing whatsoever—you will have wasted time and solvent. A PLA part annealed at 110 °C will soften and slump. PETG exposed to ethyl acetate will slowly craze and cloud. The material compatibility matrix is not a convenience reference; it is the invariant that structures every decision in this lesson.

---

## 2. Core Architecture & Mechanics

### Annealing: Mechanism, Equipment, and Execution

The practical machinery of annealing a printed thermoplastic part is deceptively simple—an oven, a support medium, a thermocouple—but the execution requires precise control of three variables: soak temperature, ramp rate, and media support. Getting any one of these wrong ruins the part.

The soak temperature must sit between T_g and the cold crystallization peak T_cc, the temperature at which chain mobility is high enough for crystalline nucleation but below the onset of melt flow. For PLA, T_g sits at approximately 58–62 °C depending on the specific formulation and residual plasticizer content, and T_cc peaks around 95–110 °C. Practical annealing for PLA targets 80–90 °C, leaving a comfortable margin below the crystallization exotherm. PETG has a T_g near 80 °C and responds well to annealing at 90–95 °C. Nylon 12 (PA12), with T_g near 40 °C and a melting point of 175 °C, tolerates annealing at 150–160 °C and benefits most dramatically from the treatment. Polycarbonate, T_g ≈ 147 °C, requires 120–130 °C for stress relief without dimensional distortion. These temperatures are soak targets, not ramp endpoints.

Ramp rate matters because a rapid temperature increase creates a thermal gradient across the part cross-section: the outer surface expands before the interior reaches equilibrium, and differential thermal expansion stresses the inter-layer bonds. For parts thicker than 10 mm in any dimension, a ramp of 1–2 °C per minute from ambient to soak temperature is advisable. Thinner parts tolerate 5 °C per minute without noticeable cracking.

The critical practical variable that most practitioners underestimate is media support. During annealing, thermoplastic parts soften sufficiently that gravity will distort any unsupported surface over the soak duration. Burying the part in a thermally inert, fine-grained media prevents this. The two best-performing options are playground sand (100–200 µm grain size, kiln-dried to remove moisture) and crushed glass bead media. The part is placed in a metal tray, packed in sand up to or beyond its midpoint, and the entire tray enters the oven. The sand conducts heat evenly into the part while providing isostatic resistance to creep. Ceramic beads and table salt are acceptable alternatives; table salt should be oven-dried at 200 °C for 30 minutes before use to remove hygroscopic moisture that would otherwise introduce steam near the part surface.

The following table provides a consolidated annealing reference for the most common FDM materials.

| Material | T_g (°C) | Soak Temp (°C) | Soak Duration | Cooling Rate | Support Media Required |
|---|---|---|---|---|---|
| PLA | 58–62 | 80–90 | 60–90 min | 1 °C/min to 40 °C | Yes, mandatory |
| PETG | 78–82 | 90–95 | 60–90 min | 1 °C/min to 50 °C | Yes, mandatory |
| ABS | 100–108 | 80–100 | 90–120 min | 2 °C/min to 60 °C | Recommended |
| ASA | 100–108 | 80–100 | 90–120 min | 2 °C/min to 60 °C | Recommended |
| PA12 (Nylon 12) | 40–45 | 150–160 | 120–180 min | 1 °C/min to 60 °C | Yes, mandatory |
| PC | 145–150 | 120–130 | 120 min | 2 °C/min to 70 °C | Yes, mandatory |
| PEI (Ultem) | 215 | 180–200 | 120 min | 1 °C/min to 100 °C | Yes, mandatory |

After the soak, the oven should be allowed to cool with the door cracked, never opened fully—thermal shock at this stage reintroduces residual stress that the entire annealing cycle was intended to eliminate. For tolerance-critical parts, reserve an extra 0.3–0.5% dimensional budget in the original CAD model to absorb the small isotropic shrinkage the crystallization process introduces.

### Heat-Setting Threaded Inserts

Heat-setting is a targeted form of thermal treatment applied to bosses designed to accept metal inserts. The insert—most commonly a knurled brass M2 through M8 threaded cylinder—is pressed into an undersized boss bore using a temperature-controlled soldering iron fitted with an insert tip. The iron heats the insert, which locally softens the surrounding polymer above T_g, allows the insert to press into the bore while the knurling displaces and reforms the polymer around it, and then the assembly cools rapidly as the iron is removed, re-solidifying the polymer in intimate mechanical contact with the insert knurling.

The process requires the bore diameter to be sized precisely at the insert's outer diameter minus 0.3–0.5 mm for PLA and PETG, minus 0.4–0.6 mm for ABS. The iron temperature should sit at T_g + 60–80 °C: approximately 180–200 °C for PLA, 200–220 °C for PETG, 220–240 °C for ABS. Too cool, and the insert stalls and bends the boss rather than pressing through. Too hot, and the polymer flows excessively, reducing the contact surface area that provides pull-out resistance. The insert should descend at a steady, slow pace over three to five seconds with no rotation—rotation shears the displaced polymer rather than compressing it radially. Apply alignment verification with a machinist's square held against the insert face before the polymer cools; there is a five-second window to correct angular misalignment before re-solidification locks the insert permanently.

### Vapor Smoothing: Chemistry, Equipment, and Process Control

A vapor smoothing chamber is conceptually straightforward: a sealed vessel with a small pool of solvent at the bottom, a part suspended above the liquid, and a heat source that drives solvent evaporation and maintains saturation. In practice, the solvent reservoir should represent no more than 2–5 mL of liquid for a standard 300 mm × 300 mm chamber. Larger volumes produce uncontrolled saturation and cause the part to run—the solvent attacks faster than surface tension can reflow uniformly, leaving drips and loss of fine detail.

The process architecture for ABS/ASA acetone vapor smoothing proceeds as follows. The part is suspended on a stainless steel or aluminum wire rack inside the chamber, never placed on a surface. A measured acetone volume is placed in a metal cup at the chamber bottom. The chamber lid is sealed, and if a heated chamber is used, it is brought to 40–50 °C using a heat pad, which accelerates vapor generation without reaching acetone's boiling point (56 °C). Exposure time is the primary control variable, and it scales with feature resolution requirements. A five-to-seven-minute exposure will reflow layer lines while preserving sharp edges; ten to fifteen minutes will produce an injection-molded surface finish but will round features below 0.5 mm. The practitioner should prepare two identical test coupons with known feature geometry and run them at different exposure intervals before committing a production part.

For PLA parts, ethyl acetate replaces acetone. Ethyl acetate has a boiling point of 77 °C, which makes heated-chamber operation more important for reliable vapor generation. The process runs identically to acetone smoothing, with soak times reduced by roughly 30% because ethyl acetate's interaction with PLA achieves plasticization faster at equivalent saturation. MEK (methyl ethyl ketone) is an effective alternative for PLA with slightly more aggressive surface attack; it narrows the exposure window and demands tighter timing control.

The process flow from print to finished part looks like this:

```text
Print → Support Removal → Sand to 220 grit (optional) → Clean with IPA → 
Vapor Chamber Exposure → 15–30 min outgas in ventilated area → 
Final inspection → Secondary sanding if needed (600+ grit)
```

Smooth-top sealing—applying a thin layer of XTC-3D epoxy or spray filler primer before smoothing—fills surface pits that solvent alone cannot reflow. The epoxy layer is sanded at 220 grit after cure and then vapor treated to unify the surface further. This two-stage approach is standard for display-quality figurines and functional enclosures where both appearance and surface hardness matter.

### UV Post-Curing: Photopolymer Completion Chemistry

A purpose-built UV curing station for resin printing achieves two things simultaneously: it maintains uniform UV irradiance across the part geometry, and it optionally purges oxygen from the curing environment. Oxygen inhibition is the primary cause of incomplete crosslinking in ambient post-cure workflows. Free radicals generated by the photoinitiator react preferentially with dissolved oxygen rather than with monomer double bonds, consuming radicals nonproductively. A curing chamber that floods the interior with nitrogen or CO₂ before UV exposure suppresses this reaction, allowing the same irradiance to deliver meaningfully higher crosslink conversion.

For practitioners without access to inert-gas purging, the workaround is submerging small parts in deionized water during curing. Water restricts oxygen diffusion to the part surface more effectively than air, improving surface hardness and tack elimination, though it does not approach inert-atmosphere performance for interior mass conversion.

Wavelength matching is the technical variable that separates competent post-cure workflows from mediocre ones. Most standard 405 nm resins (Elegoo, Anycubic, Siraya Tech) have photoinitiator absorption peaks that extend from 365 nm through 420 nm. A curing station equipped only with 405 nm LEDs is effective but misses absorption efficiency at the 365 nm peak where many photoinitiators have their primary absorption band. Dual-wavelength stations (commonly marketed as "405 + 365 nm") drive completion crosslinking more efficiently and reduce total cure time by 20–35% for equivalent final conversion, as measured by Shore D hardness or DSC residual enthalpy analysis.

Cure time and temperature interact. Post-curing at 40–45 °C elevates chain mobility, reduces viscosity in the partially-crosslinked matrix, and allows reactive groups to find each other more readily. Most Wash & Cure stations include a low-wattage heater for exactly this purpose. Standard cure protocols for the most common resin categories:

| Resin Type | UV Wavelength | Cure Time (40 °C) | Cure Time (25 °C) | Notes |
|---|---|---|---|---|
| Standard 405 nm ABS-like | 405 nm | 3–4 min per side | 6–8 min per side | Flip halfway |
| Water-washable 405 nm | 405 nm | 2–3 min per side | 4–6 min per side | Over-cure causes brittleness |
| ABS-like 8K high-res | 365+405 nm | 3–5 min per side | 7–10 min per side | High initiator load; verify hardness |
| Engineering resin (rigid, high-temp) | 365+405 nm | 5–8 min per side | 10–15 min per side | Often requires thermal post-cure at 80 °C |
| Flexible/elastomeric | 405 nm | 2 min per side | 4 min per side | Monitor closely; excess curing degrades elasticity |
| Castable (wax blend) | 405 nm | 1–2 min per side | 2–3 min per side | Fragile; handle with lint-free gloves |

The diagnostic for complete cure is not primarily visual. Surface tack absence is a necessary but insufficient criterion—the part can be tack-free with significant uncured interior mass. The reliable field test is Shore D durometer reading against the manufacturer's published cured hardness specification. If a durometer is not available, the scratch test against a fingernail provides a rough indication: a fully cured standard resin should leave no mark under moderate nail pressure.

---

## 3. High-Performance Optimization & Failure Modes

### Annealing Failure Analysis

The most common annealing failure is warpage, and it almost always traces back to one of two causes: insufficient media support, or cooling rate that was too fast during the initial phase of the ramp-down. When a part warps despite adequate sand packing, the diagnosis shifts to print orientation: parts printed with long, continuous inter-layer seams oriented parallel to the print bed have asymmetric residual stress distributions that sand packing cannot fully counteract. The mitigation is to redesign the print orientation so that the longest continuous seam intersects the neutral bending axis, or to use a 45° oblique orientation that distributes residual stress isotropically across all three axes before annealing.

Craze cracking during annealing is a different failure mode. It presents as a network of fine surface cracks that propagate along layer boundaries and indicates that the ramp rate exceeded the material's stress-relaxation rate during heating: the outer layers were driven above T_g before the interior, and the resulting differential expansion exceeded the tensile strength of the inter-layer bond. The fix is to reduce the ramp rate below 1 °C per minute for affected parts and to verify oven calibration with an independent thermocouple; most consumer toaster ovens are poorly regulated and exhibit ±10–15 °C swings at their setpoint, which is catastrophic for annealing precision.

### Vapor Smoothing Optimization and Over-Exposure Recovery

Over-exposed vapor smoothing cannot be reversed, but it can often be salvaged. If a part has begun to run or has lost sharp feature definition due to excessive exposure time, remove it from the chamber immediately and blot the surface gently with a lint-free cloth to absorb pooled solvent. Direct a compressed air stream across the surface at approximately 2–3 bar to accelerate solvent evaporation and re-solidify the surface before gravity can cause further flow. For parts with fine thread features, chamfered edges, or engraved text, the standard discipline is to make the first chamber run at 50% of the target exposure, inspect, and then run a second exposure to close the gap. This two-stage protocol consumes more time but recovers lost geometry in the first stage rather than committing to irreversibility.

A subtler optimization involves print surface preparation before vapor smoothing. Vapor smoothing has a maximum effective penetration depth of approximately 0.1–0.3 mm—it cannot fill pits or undercuts deeper than the solvent can penetrate and reflow in the available time. Layer lines are typically 0.05–0.15 mm deep in well-calibrated FDM prints and are fully eliminated by vapor treatment. However, elephant-foot artifacts, delamination gaps, or stringing scars are deeper structural defects that vapor treatment will smooth over but not eliminate mechanically. The correct workflow is to address these defects mechanically first with 220-grit sandpaper, then apply vapor treatment. Reversing the order traps solvent in mechanical pits under a re-vitrified skin, which eventually off-gasses and creates bubble defects.

### Dyeing Thermoplastics: Chemistry and Execution

Dyeing printed nylon and TPU parts is an underutilized workflow that produces a colorfast, through-body result superior to spray paint in abrasion resistance. Nylon is particularly well-suited to acid dye chemistry: PA12 and PA6 both present amine groups at the polymer chain termini that form ionic bonds with acid dye molecules in acidic aqueous solution. iDye Poly (polyester-reactive dye) dissolved in water acidified with white vinegar (5% acetic acid) to pH 4–5 produces excellent results. The dye bath is heated to 85–95 °C, and the part is submerged for 20–60 minutes depending on desired saturation depth.

The practical constraint is dimensional: PA12 absorbs water at the dye bath temperature and swells. For precision-fit parts, the standard mitigation is to design 0.1–0.15 mm of dye allowance into interference-fit surfaces, knowing that the dyeing process and subsequent drying will return the part to near-nominal dimensions. Drying must be thorough: 60 °C in an oven for two hours before testing dimensional compliance. TPU parts can be dyed with direct fiber reactive dyes (Procion MX series) at 60 °C with sodium carbonate fixative, producing vibrant colors with moderate wash fastness.

PLA accepts Rit DyeMore synthetic-fiber dye in a hot bath (90–95 °C), but the thermal exposure begins to approach PLA's T_g, creating a risk of distortion for thin-walled parts. The mitigation is a media-supported dye bath: pack the dye vessel with clean sand around the part, limiting thermal distortion through isostatic support during the dye soak, then cool slowly.

### Structural Reinforcement: Fiber Infusion, Epoxy Coating, and Rebar Integration

Vapor smoothing increases surface finish quality but does not meaningfully increase inter-layer tensile strength, which remains the principal structural liability of FDM parts. The inter-layer bond in a standard PLA print achieves roughly 50–65% of the bulk tensile strength of the filament, measured Z-axis. Two structural reinforcement strategies close this gap significantly.

The first is external epoxy coating with structural two-part systems such as System Three MirrorCoat or Smooth-On XTC-3D. Applied at 100–150 g/m² and cured at room temperature, a 1–2 mm epoxy shell increases the surface flexural stiffness by forming a continuous, amorphous cross-linked network that bridges layer interfaces. The epoxy does not penetrate deeply into the print (penetration is < 0.5 mm), but it acts structurally as a tension skin—analogous to a fiberglass laminate facing on a foam core—and dramatically increases resistance to delamination failure under bending loads. Thin parts (wall thickness < 3 mm) show 30–60% improvement in flexural load at first failure after a single XTC-3D coat.

The second approach is fiber reinforcement in discrete channels. By printing parts with 1.5–2 mm diameter channels running parallel to the primary stress axis (typically the Z-axis for column-loaded parts or the XY plane for shelf-loaded parts), the practitioner can wet-lay 3K or 6K carbon fiber tow, cure with thin-viscosity cyanoacrylate or laminating epoxy, and plug the channel exit. The resulting composite part has a fiber-reinforced core anchored in the polymer matrix. This approach is standard in functional fixture applications: jigs, end-of-arm tooling, structural brackets, and load-bearing drone frame components. Carbon tow channels should be sized to 1.6× the tow bundle diameter, and the channel should run continuously without bends sharper than 15° to prevent kinking during thread-through.

### Material Compatibility Matrix and Safety Protocols

The following matrix summarizes chemical treatment compatibility across the primary FDM and resin printing materials. No treatment should be applied without confirming the intersection below is designated safe.

| Material | Acetone | Ethyl Acetate | MEK | DCM | Acid Dye (Nylon bath) | Anneal Safe | UV Post-Cure |
|---|---|---|---|---|---|---|---|
| PLA | ✗ | ✓ | ✓ | Moderate | ✗ | ✓ (80–90 °C) | N/A |
| ABS | ✓ | ✗ | ✓ | Moderate | ✗ | ✓ (80–100 °C) | N/A |
| ASA | ✓ | ✗ | ✓ | Moderate | ✗ | ✓ (80–100 °C) | N/A |
| PETG | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (90–95 °C) | N/A |
| PA12 (Nylon) | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ (150–160 °C) | N/A |
| TPU/TPE | ✗ | ✗ | ✗ | ✗ | ✓ (mod.) | ✗ (distorts) | N/A |
| Standard 405 nm Resin | ✗ | ✗ | ✗ | ✗ | ✗ | N/A | ✓ |
| ABS-like Engineering Resin | ✗ | ✗ | ✗ | ✗ | ✗ | N/A | ✓ |
| Flexible Resin | ✗ | ✗ | ✗ | ✗ | ✗ | N/A | ✓ (limited) |
| PC | ✗ | ✗ | Moderate | ✓ | ✗ | ✓ (120–130 °C) | N/A |

Safety engineering for these processes must be treated with the same rigor as the processes themselves. Acetone and ethyl acetate are both Class IB flammable liquids (flash point below 23 °C). Vapor smoothing operations must be conducted in a ventilated workspace with no ignition sources within three meters, and the chamber must be non-sparking (glass or polypropylene). Waste solvent and solvent-contaminated paper must be disposed of in sealed metal containers, not plastic waste bins, and not poured down drains.

Liquid resin is a sensitizing compound. Uncured photopolymer contains acrylate monomers that cause contact dermatitis on repeated skin exposure, and sensitization is cumulative and irreversible once established—there is no therapeutic desensitization. Nitrile gloves rated for acrylate monomer service (minimum 0.15 mm thickness, 4H rating), UV-blocking safety glasses, and a ventilated enclosure are mandatory for all resin handling, washing, and curing operations. IPA wash solvent contaminated with uncured resin must be cured by UV exposure before disposal; this converts the reactive monomer fraction into inert crosslinked polymer that can then be disposed of as solid waste in many jurisdictions, though local regulations should be verified.

The mastery of thermal and chemical post-processing ultimately rests on a single discipline: treating each operation not as a finishing step but as a continuation of the manufacturing process, governed by the same material-science logic that informed the original print parameters. The material does not change its physics when it leaves the printer; your decisions about temperature, solvent exposure, and time must remain as precisely considered as the layer height and wall count settings that produced the part in the first place.
