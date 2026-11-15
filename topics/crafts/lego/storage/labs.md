# Operational Verification Labs: Storage

## Objective & Operational Lab Setup

Storage in Lego engineering is not a passive concern. Every serious builder confronts it eventually: a collection that began as a few hundred pieces has become tens of thousands, spanning dozens of colors, dozens of part families, and an ever-expanding taxonomy of specialized Technic connectors, axles, pins, and panels. The builder who cannot retrieve the correct 3L axle with stop, or who confuses a light-bluish-gray 2×4 plate for a flat-silver one under poor lighting, is not slower by a small margin — they are functionally paralyzed at the workbench. These labs treat storage as a precision engineering discipline, applying the same empirical rigor to part organization that a machinist applies to tool crib management or a pharmacist applies to dispensary layout.

The objective across all three exercises is to build, measure, and stress-test a complete Lego storage system using analytical methods native to the craft. You will inventory real parts, construct quantitative spreadsheet models, audit retrieval performance against empirical rubrics, and push the system to failure boundaries so you understand exactly where it breaks down and how to recover. No part of this guide is abstract: every table you build will reflect your actual collection, every retrieval time you log will come from your hands moving through real bins, and every failure mode you encounter will have a documented recovery procedure.

### Physical Setup

Before the first exercise begins, clear a dedicated workspace of at least 1.2 m × 0.6 m — a standard folding table is sufficient. You will need the following on hand throughout all three labs.

**Sorting and containment hardware:** A minimum of 40 small parts bins or compartmentalized drawer units (Akro-Mils 10164, Raaco Combiboxx, or equivalent), plus six medium bins for bulk storage of large panels and baseplate-class pieces. Stackable drawer towers like the IRIS USA 44-drawer unit or the Raaco 55 series are ideal because they allow vertical compression of floor space while keeping all drawers accessible without unstacking.

**Measurement and documentation tools:** A digital kitchen scale accurate to 1 g (for bulk-weight inventory estimation), a printed or digital spreadsheet template pre-formatted with the column schema defined in Exercise 1, a timer or stopwatch application, a USB lamp or daylight-balanced LED panel for color discrimination, and a loupe or magnifying glass (5× minimum) for identifying part number engravings molded into the undersides of Technic beams, plates, and specialized connectors.

**Reference materials:** BrickLink's Part Catalog (bricklink.com/catalogTree.asp) open in a browser, Rebrickable's set inventory tool for cross-referencing parts against set numbers, and a local backup of the LDraw parts library (ldraw.org/library/updates/) installed in BrickLink Studio 2.0 or LDCad for digital verification of part geometry when physical identification is ambiguous.

**Labeling supplies:** A label maker (Brother P-Touch PT-D210 or equivalent) loaded with 12 mm white TZe tape, plus a black fine-tip permanent marker for hand-labeling oversize bins. Every bin in your system must carry both the BrickLink part number and a plain-language description before Exercise 1 is considered complete.

### Spreadsheet Environment

Open a new workbook in your preferred spreadsheet application — Google Sheets, LibreOffice Calc, or Microsoft Excel. Create three sheets named **Master Inventory**, **Retrieval Log**, and **Failure Audit**. The Master Inventory sheet will be populated during Exercise 1. The Retrieval Log will be populated during Exercise 2. The Failure Audit will be populated during Exercise 3. This workbook is your primary diagnostic instrument for all three labs, and its completeness is non-negotiable: every measurement you take must be recorded before you move to the next step.

---

## Exercise 1: Foundational Practical Implementation

### Phase 1 — The Physical Sort

The goal of this phase is to convert an unsorted or semi-sorted collection into a taxonomically coherent physical arrangement, documented in the Master Inventory sheet with enough precision that any part can be located in under 20 seconds. That 20-second threshold is not arbitrary: it is derived from the ergonomic research literature on tool crib retrieval and represents the point at which retrieval friction begins to compound into meaningful build-time loss. A builder interrupted every two minutes by a 45-second part search loses more than time — they lose the gestalt of what they were building.

Begin with a full dump. Empty every container, bag, and set box onto a clean sorting surface. Resist the temptation to sort as you dump; complete the dump first so you have a true population census rather than a biased sample. If your collection exceeds roughly 5,000 parts, perform the dump in batches by source container, keeping each batch in a labeled staging zone so you do not lose provenance information.

The primary sort axis is **part family**, not color. This is the foundational decision in Lego storage architecture, and it deserves a moment of mechanical reasoning. When you build, you search for a part by function first — you need a 3-stud-long Technic liftarm, not a blue one — and then you select color within that family. Sorting by color first inverts this search path and forces you to visit multiple bins for the same part type. The only exception is SNOT bricks and tiles used for cosmetic cladding on display models, where color is the primary selection criterion; these may be organized in a parallel color-sorted section. For everything else, part family comes first.

The part families that require dedicated bins are as follows. Each entry in this list is a bin assignment, not merely a category:

**Technic Beams:** Separate bins by beam length, from 1-stud beams (Technic brick 1×1 with hole, BrickLink part 6541) through 15-stud beams (part 32278). Odd-length beams (3, 5, 7, 9, 11, 13, 15) go in one physical row; even-length beams (2, 4, 6, 8, 10, 12, 14, 16) go in the adjacent row. L-shaped and T-shaped liftarms (parts 32140, 41239, 60483, 6629) each get their own bin.

**Technic Axles:** Sort by length in studs: 2, 3, 4, 5, 5.5 (with stop), 6, 7, 8, 10, 12. Axles of different lengths are notoriously difficult to distinguish by eye at lengths 6, 7, and 8; this is where your daylight LED panel matters. Stand axles vertically in the bin against a measuring reference card — a strip of paper marked at 2-stud intervals glued to the inside of the bin wall — so you can confirm length at a glance without pulling the axle out.

**Technic Pins:** Separate bins for friction pins (black, BrickLink 2780), frictionless pins (tan/dark-tan, BrickLink 4274), 3L pins (blue, BrickLink 32556), pin-with-stud (BrickLink 4019), and pin joiner combinations. The black vs. tan distinction is functionally critical: friction pins lock beams in position; frictionless pins are used in axle/rotation assemblies. Mixing them is a build error that can be nearly invisible until a mechanism binds or slips unexpectedly.

**Standard Bricks:** Organized by stud count in a grid: 1×1, 1×2, 1×3, 1×4, 1×6, 1×8, 2×2, 2×3, 2×4, 2×6, 2×8, 2×10. Within each size bin, colors are mixed. If your collection has more than roughly 200 pieces in a given size-color combination, subdivide that bin by color.

**Plates, Tiles, and Modified Tiles:** Mirror the brick organization scheme. Cheese slopes (BrickLink 54200), curved slopes (BrickLink 11477, 15068), and jumper plates (BrickLink 3794) each earn dedicated bins because they are retrieved frequently in SNOT work.

**Gears:** Each gear type gets its own bin. 8-tooth spur gear (BrickLink 10928), 12-tooth bevel gear (BrickLink 32270), 16-tooth spur gear (BrickLink 94925), 20-tooth spur gear (BrickLink 32269), 24-tooth spur gear (BrickLink 3648), 36-tooth spur gear (BrickLink 3649), 40-tooth spur gear (BrickLink 3649b), worm gear (BrickLink 4716 or 27938). Gear meshing in Technic builds fails at the assembly stage — not at the design stage — when you reach for a 24-tooth and pull a 20-tooth instead, so dimensional similarity between gear families makes dedicated bins essential.

**Connectors, Joints, and Universals:** Perpendicular connectors (BrickLink 32039, 42003), axle and pin connectors of various angles (157.5°: BrickLink 32015; 112.5°: BrickLink 32192), ball joints and sockets, and CV joint elements. These are small, easy to confuse, and extremely high-retrieval-frequency in complex Technic mechanisms.

Work through each family in sequence, pulling every matching piece from your dump pile and depositing it into the appropriate bin. For any piece you cannot identify, place it in a holding bin labeled **Unknown — Pending ID**. Do not let an inability to identify a piece stall the sort; keep moving and return to the Unknown bin after the primary sort is complete.

### Phase 2 — Identification of Unknown Parts

For each piece in your Unknown bin, the identification procedure is as follows. Hold the piece under your loupe and look for the BrickLink part number molded into the ABS. On plates and bricks, this is typically on the underside inside the tube cavity. On Technic beams, it is usually on the flat inner face. On small connectors and pins, it may be on a single face of the stud or axle hole surround, often as a 4–5 digit number.

If you locate a number, search it directly on BrickLink (bricklink.com/v2/catalog/catalogitem.page?P=XXXXX) to confirm. If no number is visible, use BrickLink's visual Parts Catalog: navigate to the part family by shape, filter by stud count or length, and compare the thumbnail grid visually. For ambiguous Technic connectors, BrickLink Studio's Part Palette search is faster — type a physical description ("connector perpendicular 3L") and inspect the 3D rendered thumbnails.

Once identified, label the piece's bin and add it to the Master Inventory.

### Phase 3 — Populating the Master Inventory Spreadsheet

The Master Inventory sheet must have exactly the following columns, in this order:

| Column | Header | Format |
|--------|--------|--------|
| A | BrickLink Part No. | Text (e.g., 32278) |
| B | Part Description | Text (e.g., Technic Beam 1×15) |
| C | Part Family | Text (e.g., Technic Beam) |
| D | Color (BrickLink Name) | Text (e.g., Light Bluish Gray) |
| E | Count (Physical) | Integer |
| F | Bin ID | Text (e.g., T-B-15 for Technic-Beam-15stud) |
| G | Bin Location | Text (e.g., Drawer Unit 2, Row 3, Position 4) |
| H | Date Last Verified | Date |
| I | Notes | Text |

The Bin ID scheme follows a prefix-family-descriptor convention. The prefix T designates Technic, S designates Standard (System bricks/plates), G designates Gear, C designates Connector, and X designates Miscellaneous or Specialty. A bin containing 8-tooth spur gears is therefore **G-SP-08**; a bin containing 5.5L axles with stop is **T-AX-5.5S**. This scheme is arbitrary in its specifics but non-negotiable in its consistency: pick a convention before you begin labeling and do not deviate from it.

Enter every identified bin as a row in the Master Inventory. For part count, perform a physical hand-count for bins containing fewer than 50 pieces. For bins containing more than 50 pieces, use the bulk-weight estimation method: weigh 10 representative pieces on your digital scale to establish a per-piece average mass in grams, then weigh the full bin contents (tare the bin first) and divide. This introduces a small error — typically 3–8% — which is acceptable for large-count bins and can be noted in Column I.

When the Master Inventory is fully populated, apply a conditional formatting rule to Column E: highlight any cell where the count is 0 in red and any cell where the count is below 5 in yellow. These are stock-out warnings. A part count of zero means your physical sort produced no instances of a bin you created — either the bin is premature (you expected the part but do not own it) or a piece was miscategorized. A count below 5 on a high-usage part family like friction pins or 2×4 plates is a signal to replenish before it becomes a mid-build problem.

The exercise is complete when every physical bin has a corresponding row in the Master Inventory with a non-empty Bin ID and Location, and when every row has a physical count value greater than zero.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### The Retrieval Time Audit

A storage system that looks well-organized is not necessarily well-optimized. Optimization is an empirical question: given a specific retrieval task, how long does it take to locate the correct part and return it to the build surface? This exercise constructs a controlled retrieval experiment, logs the data, and uses it to identify bottlenecks that are invisible from the outside of the system.

Open the Retrieval Log sheet in your workbook and create the following columns:

| Column | Header |
|--------|--------|
| A | Trial No. |
| B | Part Requested (description) |
| C | BrickLink Part No. |
| D | Color Requested |
| E | Start Time (hh:mm:ss) |
| F | Bin Located Time (hh:mm:ss) |
| G | Part In Hand Time (hh:mm:ss) |
| H | Retrieval Time — Locate (sec) |
| I | Retrieval Time — Extract (sec) |
| J | Total Retrieval Time (sec) |
| K | Error Made (Y/N) |
| L | Error Description |
| M | Notes |

Columns H, I, and J are calculated: H = F − E, I = G − F, J = G − E. The distinction between locate time (finding the bin) and extract time (finding the specific piece within the bin) is analytically important. If your locate times are high, your bin labeling or layout is the problem. If your extract times are high, your bin density or in-bin organization is the problem. These are different interventions.

### Constructing the Test Part List

Generate a 30-item retrieval test list drawn from the following categories, ensuring representation across all major part families in your collection. This is your complete test protocol:

1. Technic Beam 1×5 (BrickLink 32316) — any color
2. Technic Beam 1×9 (BrickLink 40490) — any color
3. Technic Axle 6L (BrickLink 3706) — any color
4. Technic Axle 3L (BrickLink 4519) — any color
5. Technic Axle 5.5L with Stop (BrickLink 55013) — any color
6. Technic Pin, Friction (BrickLink 2780) — black
7. Technic Pin, Frictionless (BrickLink 4274) — tan
8. Technic Gear, 24 Tooth (BrickLink 3648) — light bluish gray
9. Technic Gear, 8 Tooth (BrickLink 10928) — any color
10. Technic Worm Gear (BrickLink 4716 or 27938) — any color
11. Technic Liftarm 1×3 Thin (BrickLink 6632) — any color
12. Technic Connector, Perpendicular 3L (BrickLink 42003) — any color
13. Technic Connector, Angle #4 (112.5°, BrickLink 32192) — any color
14. Plate 2×4 (BrickLink 3020) — red
15. Plate 1×2 (BrickLink 3023) — yellow
16. Tile 1×4 (BrickLink 2431) — dark bluish gray
17. Brick 2×4 (BrickLink 3001) — white
18. Brick 1×2 (BrickLink 3004) — black
19. Cheese Slope 1×1×2/3 (BrickLink 54200) — dark tan
20. Curved Slope 1×2 (BrickLink 11477) — light bluish gray
21. Jumper Plate 1×2 (BrickLink 3794) — tan
22. Technic Beam 1×13 (BrickLink 41239) — dark bluish gray
23. Technic Ball Joint (BrickLink 32474) — any color
24. Technic CV Joint (BrickLink 61903) — any color
25. Axle Pin (BrickLink 3749) — any color
26. Technic Gear, 16 Tooth (BrickLink 94925) — any color
27. Plate 1×6 (BrickLink 3666) — blue
28. Stud Shooter / Clip-Bar Plate 1×1 (BrickLink 4085) — any color
29. Technic Beam, Bent 53° 4×4 (BrickLink 32140) — any color
30. Brick 1×1 Round (BrickLink 3062b) — orange

If your collection does not contain a listed part, substitute the nearest equivalent from the same part family and log the substitution in Column M. Do not skip the trial, because the absence of a part is itself a data point about collection gaps.

### Executing the Retrieval Trials

Station yourself at your storage system in your normal build posture. Have a partner call out each retrieval task from the list, or use your phone's timer and read each task from the list yourself — the key constraint is that you must start the timer before looking at the bins and stop it only when the part is physically in your hand and confirmed correct. Do not stop the timer when you reach a bin and then deliberate; deliberation time is part of the measurement.

Run all 30 trials in sequence without reorganizing bins between trials. Record all timestamps in real time, logging errors immediately when they occur: an error is any trial where you pulled the wrong part initially, opened the wrong bin, or could not locate the bin within 60 seconds (which counts as a 60-second locate failure and a forced reset where you use your spreadsheet to find the bin location).

After all 30 trials are complete, calculate the following summary statistics in a summary block below your data table:

**Mean Total Retrieval Time** = AVERAGE(J2:J31)

**90th Percentile Retrieval Time** = PERCENTILE(J2:J31, 0.9)

**Mean Locate Time** = AVERAGE(H2:H31)

**Mean Extract Time** = AVERAGE(I2:I31)

**Error Rate** = COUNTIF(K2:K31,"Y") / 30 × 100 (expressed as a percentage)

**Slowest 5 Trials** = LARGE(J2:J31,1) through LARGE(J2:J31,5), with associated part names pulled via INDEX/MATCH.

A well-organized system of moderate size (up to roughly 15,000 parts) should produce a mean total retrieval time under 18 seconds and a 90th percentile under 35 seconds. An error rate above 10% (3 or more errors in 30 trials) indicates a labeling, bin density, or color-discrimination problem that requires structural intervention before the system is considered operational.

### Parameter Variation: Testing Bin Density and Label Visibility

This phase tests two specific variables that have the largest empirical impact on retrieval performance in Lego storage systems: bin fill density and label type.

**Bin density test:** Select the five bins that produced the longest extract times in your trial data. For each of these bins, count the number of parts currently in the bin, measure the bin's internal volume in cubic centimeters (length × width × depth), and calculate parts-per-cm³. Record these five density figures in a small table in your spreadsheet. Then, physically halve the fill density of each bin by splitting it into two bins of the same part type, redistributing the parts evenly. Re-run the extract-only portion of those five trials (measure only from bin-open to part-in-hand), log the new extract times in a "Post-Split" column, and calculate the percentage improvement. In practice, extract time improvements of 30–60% are typical when overloaded small-parts bins are split, because the hand can sweep through fewer parts to locate the target piece.

**Label visibility test:** For the five bins that produced the longest locate times, evaluate whether the problem is label format or bin position. Temporarily relabel each bin using a full-line label printed on your Brother P-Touch with 12 mm font height — this is the maximum font the 12 mm tape supports cleanly — including both the BrickLink number and the plain-language name on the same label. If the bin is in a position where you approach it from above (top-opening drawer), orient the label horizontally across the front face. If you approach from the front (shelf-mounted bin), orient the label vertically centered on the front face. Re-run the locate-only trials for those five bins and record the new locate times. Document whether the improvement was due to font size, label content, or label orientation, based on your subjective observation during the trial — this qualitative note belongs in Column M.

Enter all variation data into the Retrieval Log with a clear header row separating the baseline trials from the variation trials. The exercise is complete when all 30 baseline trials are logged, all five density-split re-trials are logged, and all five label-variation re-trials are logged, with summary statistics calculated for all three datasets.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### The Purpose of Deliberate Failure

Every storage system has failure modes, and the worst time to discover them is in the middle of a complex build. This exercise intentionally induces the four most common failure modes in Lego storage systems — bin overflow, color misidentification, phantom inventory (recorded count does not match physical count), and location drift (a part is in a different bin than the Master Inventory records) — and documents exactly what happens to retrieval performance and build continuity when each one occurs. The recovery protocol you write at the end of this exercise is the most valuable output of the entire lab sequence.

### Failure Mode 1: Bin Overflow

Select the five highest-count bins in your Master Inventory (sorted descending by Column E). For each bin, add parts until the bin is filled to within 10 mm of its rim. Use overflow stock from your general spare parts supply, or temporarily borrow parts from adjacent bins. The goal is a physically overcrowded bin where parts pile above the natural fill line and the hand cannot sweep the bottom without first moving surface parts.

Now run a timed retrieval trial for each of the five target parts, following the same protocol as Exercise 2. Log these in the Failure Audit sheet with Failure Mode = "Overflow". In a separate column, log whether the part was found, whether any parts fell out of the bin during the search, and whether adjacent bins were disturbed.

The quantitative failure threshold for overflow is defined as any trial exceeding 2.5× the baseline extract time for that bin from Exercise 2, or any trial where parts escaped the bin onto adjacent surfaces. Document the actual multiplier for each of the five bins in a column labeled **Overflow Severity Factor** (actual time ÷ baseline extract time).

The recovery intervention for overflow is bin splitting, already practiced in Exercise 2. For this exercise, split each of the five overflow bins and document the number of new bins required, the revised bin ID assignments, the updated rows in the Master Inventory, and the revised 90th percentile extract time measured after splitting.

### Failure Mode 2: Color Misidentification

This failure mode is subtle and persistently underestimated by builders who have not measured it empirically. The Lego color system includes several pairs and triples of colors that are visually very similar under common artificial lighting: Light Bluish Gray vs. Medium Stone Gray (which are the same color — this is a naming ambiguity that catches newcomers), Tan vs. Dark Tan, Dark Bluish Gray vs. Black in deep bin shadows, Red vs. Dark Red, Yellow vs. Bright Yellow vs. Chrome Yellow, and Old Light Gray vs. Light Bluish Gray (a production-era distinction with enormous parts-catalog implications).

For this failure mode, construct a color discrimination test using 20 parts drawn from the following six pairs, two parts per pair from each of the two colors:

Pair 1: Tan (BrickLink color ID 2) vs. Dark Tan (BrickLink color ID 69) — use 1×4 bricks or 2×4 plates.
Pair 2: Dark Bluish Gray (BrickLink color ID 85) vs. Black (BrickLink color ID 11) — use 2×4 plates.
Pair 3: Red (BrickLink color ID 5) vs. Dark Red (BrickLink color ID 59) — use 1×6 bricks.
Pair 4: Light Bluish Gray (BrickLink color ID 86) vs. Old Light Gray (BrickLink color ID 9) — use Technic beams.
Pair 5: Light Bluish Gray vs. White — under warm (2700K) incandescent lighting, without daylight supplement.
Pair 6: Yellow (BrickLink color ID 3) vs. Bright Light Yellow (BrickLink color ID 226) — use 1×2 plates.

Mix all 20 parts in a single unlabeled bin. Without referring to your Master Inventory or any reference source, sort them back into their correct color pairs in a single timed session. Record the time and the number of misclassification errors in the Failure Audit sheet under Failure Mode = "Color Discrimination".

Then repeat the test under three different lighting conditions: your normal workspace light only, your workspace light supplemented with the daylight-balanced LED panel positioned at 45° to the bin, and an overhead warm-white bulb with no daylight supplement. Record error counts and sort times under each condition. The purpose is to establish empirically which lighting condition your storage environment requires to maintain color accuracy, and to encode that lighting standard as a mandatory setup step in your build workflow.

The recovery protocol for color misidentification is threefold: standardize workspace lighting at 5000–6500K color temperature (daylight range, minimum 500 lux at bin level), store visually similar colors in physically separated bin locations (not adjacent), and add a physical color reference swatch — a 1×1 flat tile in the correct color — mounted on the outside face of each bin that contains a visually ambiguous color family.

### Failure Mode 3: Phantom Inventory

Phantom inventory occurs when the Master Inventory count for a part is greater than the actual physical count. This happens through part loss (pieces falling behind furniture), undocumented use (building with parts and not updating the count), and measurement error from the bulk-weight estimation method used in Exercise 1.

To induce this failure mode, select 10 bins at random from your Master Inventory. Without looking at Column E, physically count every part in each bin and record the actual count in a temporary column in the Failure Audit sheet. Then compare against Column E. The discrepancy rate is the number of bins where the actual count differs from the recorded count by more than 5% (for bins with counts ≥ 50) or by more than 2 parts absolute (for bins with counts < 50).

For each discrepancy, classify it into one of three types: Overage (physical count exceeds recorded count, typically caused by parts being deposited in the wrong bin), Shortage (physical count is below recorded count, the classic phantom inventory scenario), or Zero (the bin is physically empty despite a nonzero recorded count, the most critical case because it means a part you believe you have is actually unavailable).

Document all discrepancies in the Failure Audit sheet with columns for Bin ID, Recorded Count, Actual Count, Discrepancy Type, and Magnitude. Calculate the **Inventory Accuracy Rate** = (number of bins with no discrepancy) / 10 × 100%. A well-maintained system should achieve ≥ 90% accuracy on a random 10-bin audit. Below 80% indicates that the inventory discipline of the Master Inventory has broken down and a full re-count is warranted.

The recovery protocol establishes two procedures. First, a **Build Deduction Discipline**: whenever you remove a part from a bin to use in a build, update Column E before you leave the storage area. This is a friction-creating step that many builders resist, but the alternative is an inventory that becomes unreliable within a few build sessions. If you use BrickLink Studio to design before you build physically, the Studio parts list can serve as a structured deduction ledger — export the parts list, verify each row against your Master Inventory, and update counts in bulk before the physical build begins. Second, a **Quarterly Spot Audit**: schedule a recurring audit of a random 10% of bins each quarter, using exactly the protocol above, and log the results with the date in Column H of the Master Inventory.

### Failure Mode 4: Location Drift

Location drift occurs when a part is physically in a different bin than the Bin Location recorded in Column G of the Master Inventory. This happens when parts are returned to wrong bins after use, when bins are reorganized without updating the spreadsheet, or when a bin is split (as in Exercise 2's density correction) and the new bin's location is not recorded.

To measure current drift in your system, select 15 rows at random from the Master Inventory. For each row, navigate to the recorded location in Column G and verify that the bin at that location contains the part described in Column B with the BrickLink number in Column A. Record a hit (part found at recorded location) or miss (part not found at recorded location) in the Failure Audit sheet.

For each miss, search for the displaced part systematically: check the adjacent bins in the same drawer unit first (most common cause: returned to the wrong adjacent slot), then check the most recently used bins from your Retrieval Log (a part may have been misdeposited after the Exercise 2 trials), then check the Unknown holding bin from Exercise 1. Record how long the search took and in which location the part was eventually found.

Calculate the **Location Accuracy Rate** = (number of hits) / 15 × 100%. A location accuracy rate below 85% means your system is drifting faster than your maintenance discipline can compensate.

The structural recovery for location drift is **bin anchoring**: physically attach a label to the drawer or shelf position itself, not only to the bin, so that the position carries the identity even when the bin is removed and replaced. When a bin is taken out for splitting, its original position label prevents the wrong bin from being re-seated there. Additionally, establish a **bin-return protocol**: every part removed from a bin during a build should be returned to its recorded location within 60 seconds of the decision to not use it, before it has a chance to migrate to the build surface and be forgotten.

### Writing the Recovery Protocol Document

The final deliverable of Exercise 3 is a one-page Recovery Protocol document. Create a new sheet in your workbook named **Recovery Protocol** and populate it with the following four sections, each corresponding to a failure mode. These sections are not generic advice — they must reference the specific Overflow Severity Factors, error counts, Inventory Accuracy Rates, and Location Accuracy Rates you measured in this exercise. The document should read as a living operational standard for your specific system, grounded in your specific empirical data.

The first section states your bin overflow threshold (the fill level at which extract time exceeds 2.0× baseline for your bin type) and the standard split procedure: which bin sizes you use, how you reassign Bin IDs, and how you update the Master Inventory. The second section states the minimum lighting standard for color-critical retrieval work (color temperature, lux level, and supplementary lamp positioning) derived from your lighting condition test. The third section states your inventory audit schedule, your build deduction procedure, and the trigger condition for a full re-count (a spot audit accuracy rate below 80%). The fourth section states your bin anchoring procedure, your bin-return time limit, and the procedure for updating Column G after any bin reorganization.

The exercise is complete when all four failure modes have been tested, all data is logged in the Failure Audit sheet with no blank cells in the core metric columns, and the Recovery Protocol document is fully populated with values derived from your measurements.

---

## Operational Reference Guide & Diagnostic Checklist

### Bin ID Scheme Reference

The following table documents the complete Bin ID prefix convention established in Exercise 1. Every bin in the system must have an ID that matches this scheme exactly.

| Prefix | Family | Example Descriptor | Full Bin ID Example |
|--------|--------|--------------------|---------------------|
| T-AX | Technic Axle | 6L (length in studs) | T-AX-6L |
| T-AX | Technic Axle with Stop | 5.5S | T-AX-5.5S |
| T-BM | Technic Beam (straight) | 15 (stud count) | T-BM-15 |
| T-BM | Technic Beam (bent/angular) | B4×4 | T-BM-B4×4 |
| T-BM | Technic Beam (L/T shape) | LT3×3 | T-BM-LT3×3 |
| T-PN | Technic Pin (friction) | FRC | T-PN-FRC |
| T-PN | Technic Pin (frictionless) | FLS | T-PN-FLS |
| T-PN | Technic Pin 3L | 3L | T-PN-3L |
| T-PN | Technic Pin with Stud | STD | T-PN-STD |
| T-CN | Technic Connector (perpendicular) | PP-3L | T-CN-PP-3L |
| T-CN | Technic Connector (angle) | A112 (degrees) | T-CN-A112 |
| T-CN | Technic CV Joint | CVJ | T-CN-CVJ |
| T-CN | Technic Ball Joint | BJ | T-CN-BJ |
| G-SP | Gear (spur) | 08 (tooth count) | G-SP-08 |
| G-SP | Gear (spur) | 24 | G-SP-24 |
| G-BV | Gear (bevel) | 12 | G-BV-12 |
| G-WM | Gear (worm) | WM | G-WM-WM |
| S-BR | Standard Brick | 2×4 | S-BR-2×4 |
| S-PL | Standard Plate | 1×2 | S-PL-1×2 |
| S-TL | Standard Tile | 1×4 | S-TL-1×4 |
| S-SL | Slope / Cheese Slope | CS1×1 | S-SL-CS1×1 |
| S-JP | Jumper Plate | 1×2 | S-JP-1×2 |
| X-BS | Baseplate | 32×32 | X-BS-32×32 |
| X-MS | Miscellaneous / Specialty | (plain-language tag) | X-MS-TURNTABLE |

### Performance Benchmark Table

The following benchmarks define operational thresholds for a healthy, mid-scale Lego storage system (5,000–20,000 parts). Values below the minimum threshold indicate a structural problem requiring intervention. Values at or above the target threshold indicate a well-tuned system.

| Metric | Minimum Threshold | Target Threshold | Measurement Method |
|--------|------------------|------------------|--------------------|
| Mean Total Retrieval Time | < 25 sec | < 15 sec | AVERAGE of J column, 30-trial audit |
| 90th Percentile Retrieval Time | < 45 sec | < 30 sec | PERCENTILE(J,0.9) |
| Mean Locate Time | < 12 sec | < 7 sec | AVERAGE of H column |
| Mean Extract Time | < 13 sec | < 8 sec | AVERAGE of I column |
| Error Rate | < 10% | < 3% | COUNTIF(K,"Y")/30 × 100 |
| Inventory Accuracy Rate (spot audit) | ≥ 80% | ≥ 95% | 10-bin random audit |
| Location Accuracy Rate | ≥ 85% | ≥ 95% | 15-row random audit |
| Bin Overflow Severity Factor | < 2.0× | < 1.3× | Actual ÷ baseline extract time |
| Color Discrimination Error Rate | < 10% | 0% | 20-part color sort under target lighting |

### Diagnostic Checklist

The following checklist serves as a rapid-assessment instrument to run at the start of each build session and in full at the conclusion of each quarterly audit. Work through every item sequentially; a "No" response on any item triggers the corresponding intervention from the Recovery Protocol document.

The workspace lighting check comes first: confirm that the daylight-balanced lamp is positioned at 45° to the primary bin area and that the ambient color temperature at bin level is 5000 K or above. A warm-white environment is not acceptable for color-critical retrieval work, and this is the single highest-impact environmental factor in your system.

Before pulling any parts, visually inspect the five highest-traffic bins — the ones you open most frequently during a typical build session. Confirm that none are filled above the 80% mark of their physical capacity, that the label is fully legible and matches the current Bin ID in your Master Inventory, and that no foreign parts (parts belonging to a different bin) are visible on the top layer. A foreign part on the top layer is a reliable indicator of return-protocol breakdown, and it compounds quickly.

Confirm that your Master Inventory spreadsheet is open and accessible from your build station, either on a tablet mounted at eye level or on a laptop positioned adjacent to your build surface. The spreadsheet is not useful if it requires a context-switch to a different room or device; it must be as accessible as a physical reference card.

After each build session, run the deduction update: open the Master Inventory, find each row corresponding to a part you consumed in the session, and decrement Column E by the quantity used. This takes under three minutes for a typical session and is the single most important maintenance action in the system. Do not defer it to the next session. Parts consumed but not deducted are phantom inventory in formation.

Once per quarter, run the 10-bin spot audit from Exercise 3 on a randomly selected set of bins, log the results in the Failure Audit sheet with the current date, and compare the Inventory Accuracy Rate against the minimum threshold of 80%. If the rate falls below threshold, halt all build activity on parts-dependent projects until a full re-count of affected bin families is complete. This is not a bureaucratic requirement; it is a build-quality control gate. A builder who proceeds with an inventory they cannot trust will substitute parts mid-build, introduce structural compromises, and spend more time debugging mechanical failures than they would have spent on the re-count.

The final item on the checklist is the location drift spot-check: once per month, select five rows at random from the Master Inventory and physically navigate to the recorded bin locations to confirm the parts are present. Five minutes once a month will catch drift before it reaches the 15% threshold that Exercise 3 defines as the boundary of system health. Early detection of drift is always cheaper than late recovery.
