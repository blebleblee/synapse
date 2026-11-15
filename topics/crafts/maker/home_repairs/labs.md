# Operational Verification Labs: Home Repairs

## Objective & Operational Lab Setup

This guide treats your home as a living diagnostic subject. Every leaking faucet, loose hinge, and hairline drywall crack is a system failure with a measurable cause, a correct repair sequence, and a verifiable outcome. The goal of these labs is to move you from reactive patch-up work to the methodical precision of a practitioner who understands why each repair succeeds or fails at the material level.

The analytical environment for home repair work is not a software IDE — it is a calibrated inspection workflow backed by physical measurement, structured documentation, and empirical pass/fail criteria. You will use an audit rubric spreadsheet (detailed below) to log baseline conditions before any repair, track parameter choices during the repair, and verify outcomes against measurable thresholds after the work is complete. This discipline transforms intuition into repeatable process.

**Workbench and tool inventory before you begin any lab.** Your core toolkit for these exercises must include: a 16-foot Stanley FatMax tape measure, a digital caliper (0.01 mm resolution, any reputable brand), a 4-foot and a 2-foot level (magnetic base preferred), a torque screwdriver set (1–10 Nm range), a stud finder with AC-detect mode (Zircon MultiScanner or equivalent), a caulking gun with a 10:1 thrust ratio for consistent bead control, a drywall taping knife set (4-inch, 6-inch, and 10-inch), a multimeter (Fluke 101 or equivalent), a slip-joint plier set, an adjustable basin wrench, and a 12-volt cordless drill with a clutch-indexed driver mode. Every measurement you take should be recorded in your running audit spreadsheet before the repair begins. If you skip the baseline, you lose the ability to verify whether your intervention actually worked.

**Audit Spreadsheet Setup.** Open a new spreadsheet (Google Sheets, LibreOffice Calc, or Excel) and create the following column headers across row 1: `Repair Zone`, `Failure Mode`, `Pre-Repair Measurement`, `Unit`, `Target Value`, `Tolerance`, `Post-Repair Measurement`, `Pass/Fail`, `Materials Used`, `Date`, `Notes`. Every lab exercise in this guide produces rows that belong in this sheet. You will reference it continuously. Save the file as `home_repair_audit_log.xlsx` and keep it open throughout all three exercises.

---

## Exercise 1: Foundational Practical Implementation

### Lab 1-A: Drywall Crack Repair and Surface Verification

Drywall cracks originate from one of three mechanisms: thermal cycling causing the paper-faced gypsum panel to expand and contract across framing joints, structural settlement loading fasteners beyond their shear capacity, and moisture infiltration softening the gypsum core until the paper face delaminates. Correctly diagnosing the type determines the repair material you select. A hairline crack running parallel to a seam is almost always a tape failure caused by insufficient initial compound coverage. A diagonal crack emanating from a window or door corner is a stress fracture driven by settlement or seasonal racking, and it will return unless the underlying movement has stopped. Before you apply any compound, you must determine which category your crack belongs to, because the material spec differs meaningfully between them.

Begin by probing the crack edges with a 4-inch taping knife held nearly flat. If the edges flex or the paper face lifts cleanly away from the core, you have tape bond failure, and you must remove all loose material before proceeding. Use the knife to cut back the damaged tape in both directions until you reach a firmly bonded section, then sand the transition with 120-grit to feather the edge to zero. If the edges are rigid and the crack is narrower than 1/8 inch (3.2 mm — verify with your caliper), you are dealing with a surface-only fracture and can proceed with pre-mixed lightweight all-purpose joint compound without mesh tape. Cracks wider than 3.2 mm or any crack that has visible step displacement between the two sides requires fiberglass mesh tape plus setting-type compound (USG Durabond 45 or Durabond 90, depending on working time needed), because mesh tape has tensile strength that paper tape lacks, and setting compounds cure by chemical hydration rather than air drying, reaching compressive strengths above 2,000 psi compared to the roughly 300 psi of dried all-purpose compound.

**Step-by-step repair sequence for a taped seam failure (the most common case):**

1. Remove all loose tape and compound within 25 mm of the crack boundary using the 4-inch knife. Score the edges with the knife tip held at 45° to prevent undercutting.
2. Sand the exposed area with 120-grit wrapped on a sanding block until the transition from existing surface to bare gypsum paper is smooth and you cannot feel a ridge with your fingertip.
3. Vacuum dust completely. Apply a thin skim coat of all-purpose compound with the 6-inch knife to prime the gypsum paper, then immediately embed a strip of paper tape centered on the seam. Apply firm pressure along the full length with the knife at 15° to the wall, forcing compound through the tape perforations.
4. Apply a second, slightly wider coat (switch to the 10-inch knife) over the tape, keeping the coat thickness under 2 mm. Record the knife width and coat thickness in your audit sheet.
5. Allow to dry completely — a minimum of 24 hours at 20°C and 50% relative humidity. Drying time scales with coat thickness; a 3 mm coat at 60% humidity can take 36 to 48 hours. Do not rush this. Compound shrinks approximately 15–20% by volume as it dries, and this is normal and expected. It is not a repair failure.
6. Apply a third feathering coat with the 10-inch knife, extending 50–75 mm beyond the second coat on each side. Thickness should not exceed 1.5 mm at the center.
7. After final drying, sand with 120-grit on a pole sander, then 220-grit for finish. Use a raking flashlight held at 10° to the wall surface to reveal any ridges or depressions. Any surface variation you can see under raking light will telegraph through paint.

**Verification criteria.** The repaired surface must pass three checks before it is finished. First, run your open hand across the repair zone — you should feel no transition from the repaired area to the surrounding surface. Second, hold the 4-foot level diagonally across the repair; the gap between the level and the wall should be less than 1 mm at any point within the repair zone (measure with a feeler gauge or a folded piece of copy paper, which is approximately 0.1 mm thick, as a rough standard). Third, in your audit spreadsheet, record `Pre-Repair Measurement` as the crack width in mm (from your caliper reading), `Target Value` as 0 mm, `Tolerance` as ±0.5 mm at the surface, and `Post-Repair Measurement` as your post-sanding reading. The repair passes if the post-measurement is 0.0 to 0.5 mm — meaning you have achieved surface flush within tolerance. Any reading above 0.5 mm requires another feathering coat.

---

### Lab 1-B: Compression Faucet Washer Replacement and Flow Verification

A dripping compression faucet wastes between 15 and 50 liters of water per day depending on supply pressure and the degree of washer degradation. The mechanism is straightforward: the stem assembly screws a rubber washer down against a brass seat. When the washer deforms, hardens, or the seat corrodes, the seal fails under supply pressure (typically 275–550 kPa in residential systems). Your job is to verify which component has failed before ordering parts, because replacing a washer against a pitted seat will return a drip within days.

Turn off the supply valve under the sink (or at the main if no isolation valve exists), then open the faucet handle to relieve line pressure and drain the standpipe. Remove the decorative cap from the handle, unscrew the handle screw (typically Phillips #2 or slotted 3/16 inch), and pull the handle off the stem. Use an adjustable wrench to unscrew the packing nut — typically 7/8 inch or 1 inch hex — and thread the entire stem assembly out by hand in the same direction as loosening.

With the stem on a clean surface, examine the rubber washer at the base. A washer that has been used to failure will show one of three wear patterns: uniform compression-set flattening (the washer has taken a permanent set and no longer springs back to its original thickness — measure it with your caliper and compare to a new washer of the same nominal size), edge chunking (pieces have been sheaved off under seat contact, indicating a rough or pitted seat), or cup-shape deformation (the center has extruded outward, indicating the brass retaining screw was over-torqued on the previous installation, crushing the washer into the cup rather than allowing it to seat flat). Record your finding in the audit log under `Failure Mode`.

If you find edge chunking, you must inspect the seat with a flashlight and a fingernail. Run your nail around the circumference of the seat; any roughness or catching indicates pitting, and you need to resurface it with a seat wrench and seat grinder before a new washer will seal. If the seat wrench confirms the seat is removable (many are), replace it entirely rather than grinding — a new brass seat costs under $3 and takes 60 seconds to thread in, while grinding requires care and an additional tool.

Replace the washer with an exact-size match — measure the outer diameter, inner diameter (the brass retaining screw hole), and thickness with your caliper. Common sizes are 1/2-inch flat washer (12.7 mm OD), 3/8-inch (9.5 mm OD), and 7/16-inch (11.1 mm OD). Seat the new washer flat in its cup and tighten the brass retaining screw finger-tight plus 1/4 turn — no more. Over-torquing here is the number one cause of immediate re-failure. Lubricate the stem threads and packing area with plumber's grease (silicone-based, not petroleum-based, which degrades rubber), reassemble in reverse order, and tighten the packing nut to finger-tight plus 1/2 turn.

**Verification.** Restore supply pressure, let the faucet run for 30 seconds to clear air and debris, then close the handle to its normal closed position with moderate hand pressure only — do not crank it. After 10 minutes, return and inspect the spout and base for any drip. Record the result in the audit log. If a drip persists at a reduced rate, your seat has a pit that the new washer bridged partially — you will need to address the seat. If water weeps from around the packing nut, tighten the nut in 1/8-turn increments until it stops; re-verify that the stem still turns freely after each increment.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Lab 2-A: Door Hinge Adjustment — Mapping Fit Against Shimming Parameters

A door that binds, rattles, or fails to latch consistently is almost always a geometry problem: the relationship between the door's hinge stile, the jamb, and the strike plate has drifted from its installation parameters. The gap specification for a properly hung interior door is 3 mm on the hinge side, 3 mm on the latch side, and 3 mm at the top — these are the values you are restoring the door to, and they are the target values in your audit spreadsheet. The gap at the bottom depends on floor covering type: 10–12 mm over carpet, 6–8 mm over hard flooring, 20–25 mm over a threshold with a weatherstrip. Measure your existing gaps with a tape measure or a set of business cards (each card is approximately 0.3 mm — stack them to measure) before touching anything.

The first variable to explore is hinge screw engagement. The most common failure mechanism for a sagging door, which produces a tight top-latch corner and a gap at the bottom-latch corner, is that the top hinge screws have stripped their mortise. Inspect the hinge leaf screws: if any turn freely without gripping, the hole is stripped. The standard repair is to remove the screw, inject a small amount of wood glue into the hole, tap in a wooden toothpick or matchstick, let it cure for 60 minutes, trim flush, and re-drive the original screw. For the top hinge specifically, replace at least two of the three screws with 76 mm (3-inch) #9 wood screws that reach through the jamb and into the structural king stud — this is the single most effective anti-sag fix and it costs essentially nothing.

The second variable is hinge mortise depth. A hinge that sits proud of the jamb surface (because the mortise is too shallow, or the door has swollen from humidity) causes the door to rack toward the stop on the hinge side, compressing the gap there to zero while creating an oversize gap at the latch side. Conversely, a hinge mortised too deeply causes the door to pull away from the stop. Measure mortise depth with your caliper: the target depth is exactly equal to the hinge leaf thickness — typically 2.0 to 2.4 mm for a standard residential butt hinge. If the mortise is too shallow, deepen it with a sharp 1-inch chisel: score the perimeter line first, then pare horizontally across the grain in passes no deeper than 0.5 mm each. If the mortise is too deep, shim behind the hinge leaf with a piece of cardstock (0.3 mm) or thin cardboard cut to the exact shape of the hinge leaf.

**Parameter variation experiment:** Set up your audit spreadsheet with four trial rows. In the first row, record the door gap measurements before any intervention. In the second row, correct only the stripped screws as described and re-measure. In the third row, add the 76 mm screws to the top hinge and re-measure. In the fourth row, correct the mortise depth if needed and re-measure. By recording the gap at each stage, you build an empirical model of which intervention contributed most to restoring spec. This is the same parametric sensitivity analysis a machinist runs when dialing in a CNC fixture — you change one variable at a time and measure the effect before moving to the next.

**Strike plate adjustment.** Once the door hangs correctly, verify that the latch bolt engages the strike cleanly. Hold the door closed by hand at its final resting position and look at the latch bolt alignment through the strike plate hole. If the bolt is high or low by more than 1.5 mm, the strike needs to move. For small corrections (1.5 to 3 mm), file the edge of the strike opening with a flat needle file — mark the high-contact side with a felt-tip pen first, then file until the bolt centers in the opening. For corrections larger than 3 mm, the strike plate must be re-mortised. Record the original and final latch centerline position in the audit sheet.

---

### Lab 2-B: Toilet Fill Valve Diagnosis and Float Adjustment

A running toilet can waste 200 liters per day — more than a leaking faucet — and the diagnostic process is a classic parameter-variation exercise. There are exactly two failure modes for a running toilet: the fill valve is not shutting off because the float height is miscalibrated, or the flapper is not sealing because it has deformed, its seat is pitted, or the chain has incorrect slack. You will test both variables systematically.

Add several drops of food coloring to the tank (not the bowl) and wait five minutes without flushing. If color appears in the bowl, the flapper is failing. If the water level in the tank rises to the overflow tube and water runs down it continuously, the fill valve float is set too high. Both can occur simultaneously, so test for the flapper first because a faulty flapper will deplete the tank and trigger the fill valve to run continuously, masking the fill valve's true behavior.

For flapper diagnosis, turn off the supply valve, flush to empty the tank, then press down on the flapper seat with two fingers and watch whether the water level in the bowl changes. If you get a rush of water from the tank to the bowl when you press the flapper, the flapper ring is deformed and needs replacement. Measure the flapper seat diameter with your caliper (60 mm, 70 mm, and 100 mm are the three standard residential sizes) and purchase an exact match — universal flappers work but create chain length problems because they are thicker than OEM parts. Install the new flapper by hooking the ears over the overflow tube pegs and verifying that the chain has 10–15 mm of slack when the flush handle is at rest. Too much slack means the flapper won't open fully when flushed; too little means it won't seal fully after flushing. This is a direct parameter calibration exercise.

For float calibration, modern fill valves (Fluidmaster 400A style) use a rotating adjustment on the valve shaft rather than a float arm. The target water level is 25 mm below the top of the overflow tube — mark this on the overflow tube with a felt-tip pen, then run the fill cycle and observe where the water level settles. If it's above your mark, turn the adjustment shaft on the fill valve one full counter-clockwise rotation and test again. If it's below, rotate clockwise. Each full rotation of the Fluidmaster 400A adjustment shifts the shutoff level by approximately 10 mm. Record the adjustment rotation count and resulting water level in the audit sheet until you converge on a level 25 ± 5 mm below the overflow tube. That is your target band.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Lab 3-A: Ceramic Tile Repair — Detecting Subsurface Failure Before Surface Failure

Tile failure is almost never a surface-level problem. A cracked or hollow tile is the visible symptom of a substrate failure that began weeks or months earlier. The substrate could be a debonded mortar bed, a flexing subfloor, or a compromised waterproofing layer behind a wet installation. If you replace the tile without correcting the substrate condition, the new tile will crack or debond on the same timeline as the original.

The diagnostic instrument for tile work is a solid hardwood or metal sounding rod — a wooden dowel, the handle of a screwdriver, or even a quarter coin held loosely between two fingers. Tap across each tile in a 100 mm grid pattern and listen to the acoustic response. A properly bonded tile produces a solid, dense tick. A debonded tile over a hollow void produces a dull, papery thud. Mark every suspect tile with a piece of masking tape immediately so you can map the failure zone before removing anything. In your audit spreadsheet, create a simple grid sketch in the Notes column showing which tiles are bonded (B), hollow at center (HC), or hollow at edge (HE). Edge hollows are common and often acceptable; center hollows are not, because they indicate the tile lacks central support and will flex under point load until it cracks.

**Tile removal sequence.** Begin by removing the grout surrounding the target tile using a rotary tool fitted with a carbide grout removal bit at 10,000–15,000 RPM, or by hand with a carbide grout saw. Work the grout removal to the full depth of the grout joint — typically 3 to 6 mm for floor tile — without touching the adjacent tile edges. Once the perimeter is clear, insert a stiff 4-inch taping knife or a tile chisel under one corner of the tile at 20° and strike the handle with a rubber mallet in short, controlled taps. The goal is to break the bond at the mortar/tile interface without cracking adjacent tiles. If the tile shatters rather than releasing cleanly, work in smaller pieces: score an X across the tile face with an angle grinder and a diamond blade, then chisel out the quadrants individually.

After tile removal, scrape the substrate back to bare cement board, concrete, or mortar bed using a wide chisel and a wire brush. Measure the surface flatness with your 2-foot level — the substrate must be flat within 3 mm over 2 feet (the ANSI A108 specification) before new tile is set. Any high spot must be ground down with a small angle grinder using a segmented diamond cup wheel; any low spot must be filled with floor-leveling compound and allowed to cure per manufacturer specs before tiling.

**Thinset parameter calibration.** For floor tile over cement board, use a polymer-modified thinset mortar (Mapei Ultraflex 2 or equivalent) mixed to a no-sag consistency: the mortar should hold a sharp ridge from the notched trowel without slumping. For wall tile in wet areas, add a non-sag admixture. Use a 6 mm × 6 mm × 6 mm V-notch trowel for tiles smaller than 100 × 100 mm; a 10 mm × 10 mm × 10 mm square-notch trowel for tiles 150 to 300 mm; and a 12 mm × 12 mm × 12 mm square-notch trowel for tiles larger than 300 mm. These trowel sizes are not arbitrary — the notch geometry determines the mortar coverage percentage. The TCNA standard for wet areas requires 95% mortar coverage (meaning 95% of the tile back is in contact with mortar); achieving this requires back-buttering the tile in addition to troweling the substrate. Apply thinset to the substrate, comb it in one consistent direction, then apply a thin skim to the tile back and press it in with a slight twisting motion as you place it. Use a rubber mallet and a beating block to fully embed the tile.

**Post-set verification.** After the thinset has cured for 24 hours (do not grout sooner), perform the sounding test again on the new tile. It must respond with the same dense tick as the surrounding bonded tiles. Any hollow response means the tile must come up and be re-set before grouting. Record the sounding result in the audit sheet as `Pass` or `Fail`. Grout only after a confirmed Pass.

---

### Lab 3-B: Electrical Outlet Replacement — Boundary Failure at the Wiring Termination

Replacing a failed receptacle is within the scope of DIY repair in most jurisdictions for like-for-like swap in an existing box — but boundary failure here is not mechanical, it is electrical, and it is dangerous. The boundary conditions you are stress-testing are correct wire identification, secure termination, and ground continuity. All three must pass before the outlet is energized.

Before touching any wiring, turn off the circuit breaker at the panel and verify de-energization at the outlet with your multimeter set to AC voltage, 600V range. Test all three conductor combinations: hot to neutral (should read 0V), hot to ground (0V), and neutral to ground (0V). Do not proceed if any reading is non-zero — trace the circuit back to the panel and confirm the correct breaker is off.

Remove the cover plate and unscrew the receptacle from the box. Pull the assembly forward to expose the wiring. Before disconnecting anything, photograph the wiring configuration with your phone. Standard 15A residential wiring in a 120V single-gang box will have a black (hot) conductor, a white (neutral) conductor, and a bare copper or green (ground) conductor. In an older home you may find aluminum wiring (dull gray, slightly larger diameter) — if you see aluminum, stop and consult an electrician, because aluminum-to-device terminations require specifically rated connectors and devices marked CO/ALR, and a standard replacement receptacle is not rated for this.

For copper wiring, use a new 15A or 20A receptacle (match the amperage to the circuit breaker rating and the wire gauge — 14 AWG wire is a 15A circuit, 12 AWG is a 20A circuit). Connect the black wire to the brass-colored terminal (hot side), the white wire to the silver-colored terminal (neutral side), and the bare copper to the green grounding screw. Use the screw terminals rather than the back-stab (push-in) terminals — screw terminations have a measured pull-out resistance of over 50N compared to roughly 15N for back-stab connections, and they are significantly more reliable under thermal cycling. Tighten each terminal screw to the torque value stamped on the receptacle body — most residential receptacles specify 1.1 to 1.4 Nm. Use your torque screwdriver and dial in 1.2 Nm as the target. Under-torqued connections arc; over-torqued connections crack the terminal. Record the final torque in the audit log.

**Recovery protocol for a wiring anomaly.** If, after de-energizing the circuit and pulling the receptacle, you discover that the box contains more than one cable (a switch loop, a feed-through, or a pigtailed neutral bar), do not guess at conductor identification. Use your multimeter in continuity mode to ring out each conductor to its panel origin. With the breaker off and the wires disconnected from the outlet, touch one probe to a conductor at the box end and ask a second person to touch the other probe to each breaker terminal in the panel one at a time. When you get a continuity beep (resistance under 1 ohm), you have identified the circuit. Only after all conductors are positively identified should you proceed with the replacement. Document every wire color, its conductor identity, and its panel circuit number in the audit log.

**Verification.** After full assembly, restore power and test the outlet with a simple GFCI/outlet tester (Klein RT105 or equivalent, available for under $15). The correct indication for a standard wired outlet is two amber lights on the right and one amber on the left in the Klein tester's lamp configuration, which corresponds to `Correct` on the label. Any other indication — open ground, open neutral, open hot, reversed polarity, or reversed hot/ground — is a wiring fault that must be corrected before use. Record the tester indication in the audit log. This is a binary pass/fail criterion with no tolerance band.

---

## Operational Reference Guide & Diagnostic Checklist

This reference section is the persistent companion to your audit spreadsheet. Keep it on your workbench — it encodes the pass/fail thresholds and decision logic from all three labs into a form you can query in the middle of a repair without re-reading the full exercise.

**Surface Repair Parameters**

| Repair Type | Compound | Max Single-Coat Thickness | Drying Time (20°C, 50% RH) | Surface Tolerance (Pass) |
|---|---|---|---|---|
| Hairline crack (<3.2 mm) | All-purpose lightweight | 2.0 mm | 24 hr | ≤0.5 mm proud or proud |
| Tape bond failure | All-purpose + paper tape | 2.0 mm per coat | 24 hr per coat | ≤0.5 mm |
| Structural crack (>3.2 mm) | Durabond 45 + mesh tape | 3.0 mm | 45–60 min set | ≤0.5 mm |
| Feathering coat | All-purpose lightweight | 1.5 mm | 24 hr | 0 mm (flush) |

**Plumbing Repair Decision Tree**

A dripping faucet after washer replacement indicates either an undersized replacement washer (re-measure with caliper and verify OD/thickness match) or a pitted seat (inspect with a flashlight; resurface or replace). A weeping packing nut after reassembly indicates either under-torqued packing nut (tighten in 1/8-turn increments, test after each) or degraded packing material (replace packing string or O-ring). A toilet that runs after flapper replacement indicates either chain slack outside the 10–15 mm target band or a worn flapper seat (measure seat diameter, replace fill valve seat ring if available). A toilet that runs with correct flapper but overfills indicates float height set too high (adjust per the 25 ± 5 mm below overflow tube standard).

**Door Hardware Thresholds**

| Gap Location | Target | Minimum Acceptable | Maximum Acceptable |
|---|---|---|---|
| Hinge side (all hinges) | 3.0 mm | 2.0 mm | 4.0 mm |
| Latch side | 3.0 mm | 2.0 mm | 4.0 mm |
| Top of door | 3.0 mm | 2.0 mm | 4.5 mm |
| Bottom over hard floor | 7.0 mm | 6.0 mm | 8.0 mm |
| Bottom over carpet | 11.0 mm | 10.0 mm | 13.0 mm |
| Hinge mortise depth | = leaf thickness | -0.2 mm | +0.0 mm |

**Tile Setting Parameters**

| Tile Size | Trowel Notch | Coverage Target | Cure Before Grout | Cure Before Load |
|---|---|---|---|---|
| <100 mm | 6×6×6 mm V-notch | 80% dry / 95% wet | 24 hr | 24 hr |
| 100–300 mm | 10×10×10 mm square | 80% dry / 95% wet | 24 hr | 72 hr |
| >300 mm | 12×12×12 mm square | 95% all locations | 24 hr | 72 hr |

**Electrical Verification Checklist**

Before any wiring work: confirm 0V across all three conductor combinations (H-N, H-G, N-G) with a calibrated multimeter. After termination: confirm all screw terminals torqued to 1.1–1.4 Nm. After energizing: confirm `Correct` indication on a three-lamp outlet tester. After GFCI outlet installation in a wet area: confirm the Test button trips the outlet and the Reset button restores it. Any indication other than `Correct` on the outlet tester is an unconditional fail — de-energize and rediagnose before the outlet is used.

**Audit Log Pass/Fail Summary Criteria**

A repair is complete and verified when every row in the audit spreadsheet corresponding to that repair zone shows a `Pass` in the `Pass/Fail` column. A `Pass` requires that the `Post-Repair Measurement` falls within the range defined by `Target Value ± Tolerance` for quantitative checks, or that a binary outcome (outlet tester, sounding test, dye test) shows the correct result. Any row showing `Fail` triggers a re-entry into the diagnostic sequence for that specific variable — not a full restart of the repair. Isolate the failing parameter, correct it in isolation, and re-verify. This is the same closed-loop correction discipline used in precision machining: measure, adjust the smallest necessary variable, re-measure, and converge on target.

The audit spreadsheet is not paperwork. It is your single source of truth for whether a repair is done or whether it only appears done.
