# Operational Verification Labs: Private Equity

## Objective & Operational Lab Setup

Private equity practice lives in the gap between a theoretical valuation and a closed transaction. The analyst who understands how to build a leveraged buyout model from scratch, run sensitivity tables that expose the real drivers of sponsor returns, and stress-test a capital structure against plausible downside scenarios is the one who gets called into the deal room. These labs are designed to close that gap entirely.

The three exercises that follow progress from construction to interrogation to failure. In Exercise 1, you build a complete five-year LBO model for a fictional but structurally realistic industrial software target, Meridian Field Services Software ("MFSS"), with full three-statement integration, a working debt waterfall, and IRR/MOIC attribution. In Exercise 2, you stress the entry and exit multiple assumptions against EBITDA growth rate and leverage variability to produce a returns matrix that tells you exactly where the deal works and where it breaks. In Exercise 3, you simulate a covenant breach at Year 3, model the amendment mechanics, and execute a recovery protocol that includes a PIK toggle and partial equity cure.

Every formula is written for direct entry into Microsoft Excel or Google Sheets. Every number is stated explicitly. No placeholders appear anywhere in the model. The discipline required to build this correctly, beginning with accurate period references and ending with a balanced balance sheet, is itself the lab.

**Analytical Environment Setup**

Open a new Excel workbook. Create the following sheets in order: `Assumptions`, `Income Statement`, `Balance Sheet`, `Cash Flow`, `Debt Schedule`, `Returns`, `Sensitivity`. Name them exactly as written. Set all currency in thousands of USD. Set the base fiscal year to 2024, with forecast years spanning 2025 through 2029 (Years 1–5). In the `Assumptions` tab, reserve rows 1–5 for a header block containing the deal name ("Meridian Field Services Software LBO"), the analysis date, the sponsor name ("Irongate Capital Partners"), the currency convention, and the rounding convention. All hardcoded inputs must appear in blue font. All formula-driven cells must appear in black. This color discipline is non-negotiable in professional PE shops because it allows any reviewer to instantly distinguish assumptions from derived outputs.

---

## Exercise 1: Foundational Practical Implementation

### The Target Company and Entry Assumptions

Meridian Field Services Software is a vertical SaaS business serving utility inspection and pipeline maintenance contractors. It generates 85% recurring revenue, has 112% net revenue retention, and runs on a mid-market EBITDA margin that makes it an attractive sponsor target. The business profile is designed to reflect the type of asset that a mid-market PE fund raising $1.5B would actually pursue.

In the `Assumptions` tab, enter the following hardcoded inputs exactly as stated. The LTM (last twelve months) revenue entering the transaction is $48,200. LTM EBITDA is $14,460, implying a 30.0% EBITDA margin. The entry EV/EBITDA multiple is 11.5x, producing an enterprise value of $166,290. Net debt at close is $4,100 (cash of $1,200 offset by existing debt of $5,300). Therefore, the equity purchase price is $166,290 minus $4,100 equals $162,190. Irongate's equity check is $65,276. Total debt raised at close is $100,974, structured across two tranches described in full below. The transaction closes on January 1, 2025, so Year 1 is a full calendar year.

Revenue growth rates by year are as follows: Year 1, 14.0%; Year 2, 13.0%; Year 3, 12.0%; Year 4, 11.0%; Year 5, 10.0%. EBITDA margin by year: Year 1, 30.5%; Year 2, 31.0%; Year 3, 31.5%; Year 4, 32.0%; Year 5, 32.5%. D&A as a percentage of revenue: 2.5% every year. CapEx as a percentage of revenue: 2.0% every year. Cash taxes as a percentage of pre-tax income: 26.0%. Changes in net working capital as a percentage of revenue change: 8.0% (meaning that each incremental dollar of revenue requires $0.08 of additional net working capital, a cash use). PPA amortization from acquired intangibles is $4,200 per year, treated as a non-cash tax-deductible expense running straight-line through the income statement.

### The Debt Waterfall

The capital structure at close contains two debt instruments. The first is a Term Loan B (TLB) of $83,274, priced at SOFR plus 475 basis points, with SOFR assumed at a fixed 5.25% for modeling purposes, producing an all-in cash interest rate of 10.00%. The TLB amortizes at 1.0% per year of original principal ($832.74 per year), with the remaining balance due at maturity in Year 5 or upon exit. The second instrument is a Revolving Credit Facility (RCF) with a total commitment of $17,700. The RCF is undrawn at close. The RCF bears interest at SOFR plus 400 basis points (9.25% cash interest) and carries an unused commitment fee of 0.375% per year on the undrawn balance. All free cash flow after mandatory TLB amortization is swept to optional TLB principal prepayment per the cash sweep provision (100% excess cash flow sweep, as is standard in mid-market LBO credit agreements).

In the `Debt Schedule` tab, build the following structure. Columns represent Years 1 through 5. Rows are organized by instrument.

For the TLB, the beginning balance in Year 1 is $83,274. Mandatory amortization in every year is $832.74. The optional prepayment (cash sweep) is calculated as: `=MAX(0, Excess_Cash_Flow)`, where Excess Cash Flow equals operating cash flow minus mandatory amortization minus CapEx. Enter the formula in Year 1 as `=MAX(0, 'Cash Flow'!D18 - 832.74 - 'Income Statement'!D15)`, adjusting column references for each subsequent year. The ending balance equals beginning balance minus mandatory amortization minus optional prepayment. The beginning balance in each subsequent year references the prior year's ending balance. Cash interest expense equals the average of beginning and ending balance multiplied by 10.00%, entered as `=(B5+B6)/2*0.10` where B5 is beginning balance and B6 is ending balance.

The RCF balance remains zero in all years under the base case, so interest expense on the RCF is zero. The unused commitment fee is computed as `=17700*0.00375` per year, which equals $66.38 per year, booked as interest expense on the income statement.

### The Income Statement

In the `Income Statement` tab, build five forecast columns (Years 1–5) plus an LTM column for reference. Each row is defined as follows, with Year 1 formulas stated explicitly.

**Revenue** (Row 5): Year 1 = `=48200*(1+'Assumptions'!B8)`, where B8 contains 14.0%. This produces $54,948.

**EBITDA** (Row 6): Year 1 = `='Income Statement'!B5*'Assumptions'!B13`, where B13 contains 30.5%. This produces $16,759.

**D&A** (Row 7): Year 1 = `='Income Statement'!B5*'Assumptions'!B18`. This is 2.5% of revenue, producing $1,374.

**PPA Amortization** (Row 8): Year 1 = $4,200. This is a hardcoded annual figure from the `Assumptions` tab.

**EBIT** (Row 9): Year 1 = `='Income Statement'!B6-'Income Statement'!B7-'Income Statement'!B8`, producing $11,185.

**Total Interest Expense** (Row 10): Year 1 references the total interest line from the `Debt Schedule`: `='Debt Schedule'!B15`. This equals TLB cash interest plus RCF unused commitment fee.

**Pre-Tax Income** (Row 11): Year 1 = `='Income Statement'!B9-'Income Statement'!B10`.

**Cash Taxes** (Row 12): Year 1 = `=MAX(0,'Income Statement'!B11*'Assumptions'!B22)`, where B22 is 26.0%. The MAX(0,…) wrapper prevents negative taxes in a loss year.

**Net Income** (Row 13): Year 1 = `='Income Statement'!B11-'Income Statement'!B12`.

**D&A Add-Back** (Row 14): Year 1 = `='Income Statement'!B7+'Income Statement'!B8`. This adds back all non-cash charges.

**CapEx** (Row 15): Year 1 = `='Income Statement'!B5*'Assumptions'!B20`. This is 2.0% of revenue, entering the cash flow statement as a negative figure.

Populating this structure through Year 5 produces the following key outputs. Year 1 revenue is $54,948; Year 2, $62,091; Year 3, $69,541; Year 4, $77,191; Year 5, $84,910. Year 5 EBITDA is $27,596, representing 32.5% margin on Year 5 revenue.

### The Cash Flow Statement

In the `Cash Flow` tab, build the indirect method statement. The first section reconciles from net income to operating cash flow.

**Net Income** (Row 5): Reference from `Income Statement`.

**Add: D&A and PPA Amortization** (Row 6): Reference from `Income Statement` Row 14.

**Change in Net Working Capital** (Row 7): Year 1 = `=-('Income Statement'!B5-48200)*'Assumptions'!B25`, where B25 is 8.0%. For Year 2 onward, the revenue reference in the parenthetical shifts to the prior year's revenue. This is a cash outflow (negative) when revenue grows, since working capital must increase.

**Operating Cash Flow** (Row 8): Sum of Rows 5 through 7.

**CapEx** (Row 9): Reference from `Income Statement` Row 15, entered as a negative number.

**Free Cash Flow to Firm** (Row 10): Sum of Rows 8 and 9.

**Mandatory TLB Amortization** (Row 11): `=-832.74` in every year.

**Optional TLB Prepayment (Cash Sweep)** (Row 12): Temporarily set to zero; this will be resolved through circular reference handling or a manual iteration approach described below.

**Excess Cash Flow** (Row 13): Sum of Rows 10, 11, and 12.

The cash sweep creates a mild circularity: interest expense depends on ending debt balance, ending debt balance depends on the cash sweep, and the cash sweep depends on free cash flow, which is after interest expense. Resolve this by enabling iterative calculation in Excel under File → Options → Formulas → Enable Iterative Calculation, with Maximum Iterations set to 100 and Maximum Change set to 0.001. Once enabled, enter the optional prepayment in Row 12 of the `Cash Flow` tab as `=MIN('Debt Schedule'!B6, MAX(0,'Cash Flow'!B13))`, where B6 is the TLB ending balance before sweep (so prepayment never exceeds remaining principal) and B13 is the pre-sweep excess cash flow. The circular reference will resolve within the iteration tolerance.

### The Balance Sheet

In the `Balance Sheet` tab, build the opening balance sheet as of transaction close (January 1, 2025) using purchase accounting. The opening balance sheet reflects the acquisition at the enterprise value of $166,290, with assets stepped up to fair value.

**Opening Assets:** Cash is $1,200 (acquired). Accounts receivable is $4,820 (10.0% of LTM revenue). Prepaid and other current assets is $965. Total current assets: $6,985. PP&E net is $3,374 (stepped up to fair value). Acquired intangibles (customer relationships, developed technology) are $42,000, amortized straight-line over 10 years ($4,200/year, matching the PPA amortization assumption). Goodwill is the balancing figure: Total assets acquired at fair value are $6,985 plus $3,374 plus $42,000 = $52,359. Total consideration is enterprise value of $166,290. Goodwill = $166,290 minus $52,359 = $113,931. Goodwill is not amortized for GAAP purposes but is tested annually for impairment. Total opening assets: $166,290 plus net cash acquired of $1,200: $167,490. (This includes cash on the asset side before netting against debt.)

**Opening Liabilities:** Accounts payable is $1,448. Accrued liabilities are $2,172. Total current liabilities: $3,620. TLB principal: $83,274. RCF: $0. Total debt: $83,274. Total liabilities: $86,894.

**Opening Equity:** Sponsor equity check: $65,276. The balance sheet must balance: $167,490 total assets equals $86,894 total liabilities plus equity; therefore opening equity is $80,596. Note that the equity check of $65,276 plus goodwill and purchase price premium effects produce retained earnings of zero at close, with the difference flowing into additional paid-in capital. For a clean model, record sponsor equity check as common equity of $65,276 and assign the remaining $15,320 to PPA-related book adjustments within additional paid-in capital. Total equity: $80,596.

For each forecast year, the balance sheet rolls forward using the following mechanics. Retained earnings increases by net income and decreases by zero (no dividends in an LBO; all cash is swept to debt). Cash at year end equals prior cash plus excess cash flow after the sweep (in the base case, this will be close to zero because of the full cash sweep). Acquired intangibles decrease by $4,200 per year. PP&E decreases by D&A from operations ($1,374 in Year 1) and increases by CapEx. Accounts receivable equals 10.0% of current year revenue. Accounts payable equals 3.0% of current year revenue. TLB balance references `Debt Schedule` ending balance. Total assets must equal total liabilities plus equity; build a check cell that computes `=Total_Assets - Total_Liabilities_And_Equity` and format it to display "BALANCED" if zero or "ERROR" if nonzero using `=IF(ABS(B_check)<0.5,"BALANCED","ERROR — "&TEXT(ABS(B_check),"$#,##0"))`.

### Returns Analysis

In the `Returns` tab, model the exit at the end of Year 5. The base case exit multiple is 11.0x EBITDA, applied to Year 5 EBITDA of $27,596, producing an exit enterprise value of $303,556. Exit equity value equals exit enterprise value minus remaining net debt at exit. Remaining TLB balance at Year 5 end (after the full cash sweep) can be read directly from `Debt Schedule`!F7. Compute exit equity value as `=303556 - 'Debt Schedule'!F7`.

MOIC (Multiple of Invested Capital) = Exit Equity Value / Entry Equity Check = `=Returns!B5 / 65276`.

IRR (Internal Rate of Return) is computed using Excel's XIRR function. Build a cash flow schedule with the entry equity check as a negative outflow on January 1, 2025, and the exit equity value as a positive inflow on December 31, 2029. The formula is `=XIRR({-65276, Returns!B5}, {"2025-01-01","2029-12-31"})`. Because XIRR requires date-formatted cells, place the outflow in C5 and C6 referencing date cells D5 and D6 respectively, then write `=XIRR(C5:C6, D5:D6)`.

Under the base case, the model should produce an exit equity value in the range of $230,000–$250,000 (depending on debt repayment pace), a MOIC of approximately 3.5x–3.8x, and an IRR in the range of 28%–32%. If your numbers fall materially outside these ranges, audit the debt schedule cash sweep logic and confirm that interest expense is calculating on average balances rather than beginning balances.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Constructing the Returns Sensitivity Matrix

A single-point IRR estimate tells you almost nothing useful about deal risk. What matters is the distribution of returns across the realistic range of entry multiples, exit multiples, and EBITDA growth trajectories. This exercise builds a full two-dimensional sensitivity matrix and a three-way scenario grid, then applies empirical interpretation to identify the deal's true risk spine.

In the `Sensitivity` tab, build two separate sensitivity tables. The first is a 7×7 matrix of IRR as a function of entry EV/EBITDA multiple (ranging from 9.5x to 12.5x in 0.5x steps) and exit EV/EBITDA multiple (ranging from 9.0x to 12.0x in 0.5x steps). The second is a 5×5 matrix of MOIC as a function of Year 5 EBITDA margin (ranging from 29.5% to 33.5% in 1.0-point steps) and revenue CAGR (ranging from 8.0% to 16.0% in 2.0-point steps across all five years uniformly).

To build the first matrix, use Excel's two-variable Data Table function. Place the IRR formula from the `Returns` tab in a reference cell, say `Sensitivity!C3`, as `='Returns'!IRR_cell`. Place the row inputs (exit multiples 9.0x through 12.0x) in row 4 starting at D4. Place the column inputs (entry multiples 9.5x through 12.5x) in column C starting at C5. Select the range C4:J11 (the full 7×7 grid plus headers), then navigate to Data → What-If Analysis → Data Table. Set the row input cell to `Assumptions!B5` (entry multiple) and the column input cell to `Assumptions!Exit_Multiple` (you will need to add an exit multiple assumption cell, initially set to 11.0x, in the `Assumptions` tab, and then modify the exit enterprise value formula in `Returns` to reference it as `='Assumptions'!Exit_Multiple * 'Income Statement'!F6`). Click OK. Excel will populate all 49 cells simultaneously using the full model chain.

Format the IRR matrix using conditional color scaling: red below 20%, yellow at 20%–25%, light green at 25%–30%, and dark green above 30%. In Excel, select the data range, navigate to Home → Conditional Formatting → Color Scales → More Rules, and define the three-point scale with 20% as minimum, 25% as midpoint, and 30% as maximum.

For the MOIC matrix, repeat the Data Table process with Year 5 EBITDA margin and revenue growth CAGR as the two variables. Add a uniform CAGR assumption cell in the `Assumptions` tab; replace the five individual year growth rates temporarily with `='Assumptions'!B_CAGR` during the sensitivity run, then restore after. The resulting matrix reveals where the deal is linear versus convex in its return response, an analytically important observation discussed below.

### Reading the Empirical Output

When you examine the completed IRR matrix, the most important observation is not the range of outcomes but the shape of the gradient. If IRR is more sensitive to a 0.5x move in exit multiple than to a 0.5x move in entry multiple at the same price point, that tells you the deal's risk is concentrated in exit-side uncertainty (buyer market conditions at Year 5) rather than in entry discipline. In mid-market software LBOs, this relationship is common: the sponsor pays a disciplined entry multiple but cannot control whether public market software valuations will be at 10x or 14x EV/EBITDA in five years.

Measure the partial sensitivity explicitly. For the base case entry of 11.5x, compute the IRR at exit multiples of 9.0x and 12.0x and record the spread: that spread is your multiple compression/expansion risk premium. Then hold exit at 11.0x and move entry from 9.5x to 12.5x and record the equivalent spread. Divide each spread by the input range (3.0 turns of multiple in both cases) to produce IRR per turn of multiple. If exit multiple sensitivity is 4.2% IRR per turn and entry multiple sensitivity is 2.1% IRR per turn, the deal is exactly 2× more sensitive to exit conditions, a quantitative fact you can place directly into an investment committee memo.

The MOIC matrix reveals the operational risk dimension. The revenue CAGR axis captures whether the sponsor's growth thesis plays out; the EBITDA margin axis captures whether the management team's operational leverage investment (typically sales and marketing spending and product development) translates into margin accretion. Any cell in the matrix with MOIC below 2.0x represents a capital loss in real return terms for a typical mid-market fund (which requires a blended portfolio return above 2.0x net to generate carried interest). Identify the boundary contour where MOIC = 2.0x and annotate it on the matrix. That contour defines the minimum viable operating envelope for the deal.

### Three-Scenario Stress Framework

Augment the matrices with three named scenarios entered directly in the `Assumptions` tab using a dropdown selector. Create a data validation dropdown in cell B30 with the options "Base Case", "Bull Case", and "Bear Case". Use `INDEX/MATCH` or `CHOOSE` logic to populate each assumption cell based on the scenario selection. The three scenarios are defined as follows.

In the base case, revenue CAGR averages 12.0% (declining from 14.0% to 10.0% as already modeled), EBITDA margin exits at 32.5%, and exit multiple is 11.0x. This produces the baseline IRR and MOIC computed in Exercise 1.

In the bull case, revenue CAGR averages 15.0% (Year 1: 17%, Year 2: 16%, Year 3: 15%, Year 4: 14%, Year 5: 13%), EBITDA margin exits at 34.0%, and exit multiple is 12.5x (reflecting sector re-rating or strategic buyer premium). Under these inputs, Year 5 EBITDA approaches $38,000, and exit equity value should produce an IRR in the range of 42%–48% and a MOIC above 5.0x, a venture-tier return from a leveraged buyout, explaining why software LBOs attracted enormous capital in the 2018–2021 vintage.

In the bear case, the company misses growth in Years 2–3 due to implementation churn (a common risk in vertical SaaS), revenue CAGR averages 7.0% (Year 1: 10%, Year 2: 7%, Year 3: 6%, Year 4: 7%, Year 5: 7%), EBITDA margin contracts to 28.0% at exit due to increased customer success spending to manage churn, and exit multiple compresses to 9.5x reflecting the deteriorated growth profile. Set these inputs by entering the year-specific growth rates as: `=IF($B$30="Bear Case",bear_rate,IF($B$30="Bull Case",bull_rate,base_rate))`. Under the bear case, Year 5 EBITDA falls to approximately $15,900, exit enterprise value is $151,050, and remaining debt (largely unprepaid because weak FCF never triggered the full sweep) absorbs most of the equity value. Compute the resulting MOIC explicitly: if remaining TLB balance is approximately $78,000, exit equity value is $151,050 minus $78,000 = $73,050, producing a MOIC of $73,050 / $65,276 = 1.12x, and an IRR of approximately 2.3%. This is a near-total-loss outcome by PE return standards despite the business remaining technically solvent, illustrating why PE risk analysis cannot stop at "can the company service its debt" and must extend to "do equity holders receive a meaningful return."

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Simulating a Year 3 Covenant Breach

Mid-market LBO credit agreements contain financial maintenance covenants tested quarterly. The most common is a leverage covenant, defined as Total Net Debt divided by LTM EBITDA, with a maximum permitted ratio typically set at 0.25–0.50 turns above the closing leverage level, stepping down annually. For MFSS, model the following covenant schedule in the `Debt Schedule` tab: Year 1 maximum total leverage of 6.5x, Year 2 maximum 6.0x, Year 3 maximum 5.5x, Year 4 maximum 5.0x, Year 5 maximum 4.5x.

Under the bear case assumptions from Exercise 2, compute the actual leverage ratio at Year 3 as: Remaining TLB balance at Year 3 end divided by Year 3 LTM EBITDA (which is the same as Year 3 annual EBITDA in this model). In the bear case, Year 3 revenue is approximately $55,500 and EBITDA margin of 29.0% (margin is compressing) produces EBITDA of approximately $16,100. The TLB balance at Year 3 end under weak FCF is approximately $80,200 (minimal sweep due to low free cash flow). Actual leverage: $80,200 / $16,100 = 4.98x. The covenant maximum at Year 3 is 5.5x. This does not breach at Year 3 under the bear case as defined. To create a breach, modify the bear case to include a one-time working capital deterioration in Year 2 of $3,500 (a step-change in accounts receivable due to a billing system migration), which you model as an additional cash outflow in the `Cash Flow` tab Year 2 column. This reduces Year 2 FCF available for the cash sweep, leaving the TLB balance at Year 2 end at $82,900 instead of the base sweep amount.

Furthermore, model a Year 3 EBITDA shortfall by reducing Year 3 EBITDA margin to 27.5% under the breach scenario. Year 3 EBITDA becomes $55,500 times 27.5% = $15,263. Net debt at Year 3 end is TLB balance of $82,100 (minimal prepayment from low FCF). Actual leverage: $82,100 / $15,263 = 5.38x. This exceeds the Year 3 covenant maximum of 5.5x? No, 5.38x remains inside 5.5x. Tighten the covenant to reflect a grid with 25-basis-point stepdowns every two quarters, so the Year 3 tested covenant (at the Q3 test date) is 5.25x. Now 5.38x exceeds 5.25x, and the breach is live.

Build the covenant test in a dedicated row in `Debt Schedule`: `Actual Leverage` = `='Debt Schedule'!TLB_End_Year3 / 'Income Statement'!Year3_EBITDA`. Build a breach flag: `=IF(Actual_Leverage > Covenant_Max, "BREACH — CURE REQUIRED", "PASS")`. Under the breach scenario, this flag should read "BREACH — CURE REQUIRED."

### Amendment and Cure Mechanics

When a borrower breaches a leverage covenant, the credit agreement prescribes three permitted remedies: a full waiver from the required lender threshold (typically 50.1% of outstanding commitments), an equity cure injection, or a PIK toggle on a portion of the interest if the credit agreement contains that provision.

Model all three in sequence to understand their impact on the capital structure.

**Equity Cure:** The equity cure provision (standard in sponsor-backed credit agreements) allows the sponsor to inject additional equity capital, which is added to LTM EBITDA for covenant testing purposes, up to the amount required to bring the ratio back into compliance. The cure amount needed is the EBITDA required to satisfy the 5.25x covenant minus actual EBITDA. Required EBITDA: $82,100 / 5.25 = $15,638. Actual EBITDA: $15,263. Cure EBITDA shortfall: $15,638 minus $15,263 = $375. Add a "Sponsor Equity Cure" row in `Debt Schedule`. When the breach flag is active, the formula inputs $375 as an equity injection reflected as cash on the balance sheet and treated as EBITDA for covenant purposes only (not flowing through the income statement). The cure injection costs Irongate $375K and prevents default, but it is dilutive to returns: total sponsor equity invested becomes $65,276 plus $375 = $65,651, and MOIC recalculates accordingly.

**PIK Toggle:** If the credit agreement includes a PIK toggle, the borrower can elect to pay a portion of the Year 3 and Year 4 interest in kind (adding accrued interest to outstanding principal) rather than in cash. This preserves cash for operations but increases the ultimate principal balance and is treated as an event of default avoidance mechanism only under tight market conditions. Model a 50% PIK toggle on Year 3 TLB interest. Year 3 cash interest at 10% on average balance of approximately $82,500 is $8,250. Under the PIK toggle, cash interest paid is $4,125, and $4,125 is added to outstanding principal. Year 3 ending TLB balance after PIK: $82,100 plus $4,125 = $86,225. This worsens Year 4 leverage but improves Year 3 cash flow by exactly $4,125, potentially allowing greater voluntary amortization in Year 4 as cash flow recovers.

Build the PIK toggle as a switch in the `Assumptions` tab: a cell named `PIK_Toggle_Year3` with value 0 (off) or 1 (on). In the `Debt Schedule`, Year 3 cash interest becomes `='Debt Schedule'!Year3_Avg_Balance * 0.10 * (1-'Assumptions'!PIK_Toggle_Year3*0.5)` and PIK accrual becomes `='Debt Schedule'!Year3_Avg_Balance * 0.10 * 'Assumptions'!PIK_Toggle_Year3*0.5`, added to the Year 3 ending principal balance.

**Lender Amendment (Covenant Reset):** The third path is a formal amendment to the credit agreement, negotiated with the lending syndicate. Model this as a 30 basis point spread increase on the TLB (a consent fee effectively captured through pricing rather than a separate fee for simplicity) and a one-turn relaxation of the Year 3 and Year 4 covenant maximums. After amendment, Year 3 maximum is 6.25x (the original 5.25x plus one turn) and Year 4 maximum is 5.75x. The TLB rate increases from 10.00% to 10.30%. Model the amended rate by replacing the hardcoded 10.00% interest rate assumption with `='Assumptions'!TLB_Rate_Base + 'Assumptions'!Amendment_Spread_Addon`, initially 0.00% and set to 0.30% when amendment is active. The annual incremental interest cost is $82,100 times 0.30% = $246 per year, a small economic cost relative to the alternative of default.

### Recovery Protocol Validation

After applying any one of the three cure mechanisms (the equity cure is the cheapest in this case at $375), validate the recovery by rebuilding the Year 4 and Year 5 projections under the assumption that EBITDA growth recovers to the original bear case trajectory (7.0% revenue growth, margin recovering to 29.5% by Year 4 and 30.0% by Year 5). Recompute the Year 5 exit scenario with exit multiple of 10.0x (a 1.0x reduction from the base case to reflect the credit history impairment and growth rate reset).

Year 5 revenue under recovery: $55,500 (Year 3) × 1.07 × 1.07 = $63,540. Year 5 EBITDA: $63,540 × 30.0% = $19,062. Exit enterprise value: $19,062 × 10.0x = $190,620. Remaining TLB balance at Year 5 (with PIK added, partially amortized in recovery years): approximately $81,000. Exit equity value: $190,620 minus $81,000 = $109,620. Total sponsor equity invested (with cure): $65,651. Recovery MOIC: $109,620 / $65,651 = 1.67x. Recovery IRR: `=XIRR({-65651,109620},{"2025-01-01","2029-12-31"})` = approximately 10.8%.

This 10.8% IRR is below any PE fund's hurdle rate (typically 8.0% preferred return with a 20% carry above that threshold), meaning Irongate earns a return on this deal but no carry, and the fund LP receives slightly above their hurdle before the GP captures economics. The investment is a disappointment but not a catastrophic loss. This outcome range, 1.5x–1.7x MOIC on a stressed deal that avoided covenant default through cure, represents the realistic floor for a well-structured mid-market software LBO with covenant protections intact.

Build a final validation dashboard in the `Returns` tab that displays a 3×4 table comparing IRR, MOIC, Exit Equity Value, and Total Equity Invested across the four scenarios: Base Case, Bull Case, Bear Case (pre-cure), and Bear Case (post-cure). This table is the deliverable you would present to an investment committee to demonstrate that the deal has been fully stress-tested.

---

## Operational Reference Guide & Diagnostic Checklist

### Model Architecture Diagnostic

The first diagnostic step when receiving any LBO model, whether you built it or inherited it, is to verify the balance sheet check. Navigate to the last column of your `Balance Sheet` and confirm that the balance check cell reads "BALANCED" in every period. A balance sheet that fails to balance is structurally compromised; every output it generates, including IRR and MOIC, is unreliable. If the check fails, the most common causes in LBO models are: (1) the sponsor equity check is not wired to absorb the residual between transaction value and debt raised; (2) PPA intangibles were added to the asset side without a corresponding goodwill computation; (3) the cash sweep is prepaying more principal than exists on the instrument; or (4) PIK accruals were added to debt but not removed from cash flow, double-counting the cash impact.

### Debt Schedule Diagnostic

The debt schedule is the mechanical heart of an LBO model and the most common source of errors. Run the following checks in sequence. Confirm that the opening TLB balance equals exactly the amount stated in the sources and uses table. Confirm that interest expense is computing on average balances (beginning plus end divided by two) rather than beginning balances; using beginning-only balances understates interest expense by approximately half a year's worth of amortization and cash sweep, inflating free cash flow by a material amount. Confirm that the cash sweep is capped at the outstanding balance, so the TLB cannot go negative. Confirm that the total sources (debt plus equity check) in the sources and uses schedule equals the total uses (equity purchase price plus transaction fees plus closing adjustments). The standard transaction fee load for a mid-market LBO is 2.0%–3.5% of enterprise value; for MFSS at $166,290 EV, fees of approximately $4,000–$5,800 would be realistic and should appear as a use of funds financed by the equity check.

### Returns Verification Diagnostic

The MOIC formula must reference total equity invested, not just the initial equity check. If the equity cure in Exercise 3 adds $375 to sponsor capital, the denominator of the MOIC calculation must reflect $65,651, not $65,276. This is a systematic error that inflates returns in breach scenarios and is frequently found in models where the cure mechanics were added after the initial returns framework was built. Verify that XIRR is receiving exactly one negative inflow (the initial equity investment) and one positive outflow (the exit equity value). If the sponsor makes any add-on acquisitions, management fee offsets, or recapitalization distributions during the holding period, those must appear as intermediate cash flows in the XIRR schedule with their precise dates. For this model there are none, but the architecture should accommodate them.

The IRR should satisfy a simple sanity check against the Rule of 72: at a 30% IRR over 5 years, capital should approximately double every 2.4 years, suggesting a rough 3.1x–3.5x MOIC over 5 years. If your base case IRR of 30% produces a MOIC outside this range, the error is almost always in the period convention: XIRR requires actual calendar dates, and if the exit date is entered as 5 years but actually spans 4.5 calendar years due to a mid-year close, the IRR will be overstated.

### Sensitivity Table Diagnostic

Data Tables in Excel will not update automatically if Excel's calculation mode is set to Manual. If the sensitivity matrices show uniform values across all cells (all reading the base case output), navigate to Formulas → Calculation Options → Automatic and press F9 to force recalculation. Confirm that each row and column input cell reference in the Data Table dialog points to the exact cell that feeds the model's assumption chain, not to a display cell or an intermediary reference. The input cells must be on the `Assumptions` tab and must directly drive the revenue growth and EBITDA margin formulas in the `Income Statement` tab without any intermediate lookup or conditional logic that could break the data table's row/column substitution mechanism.

### Key Formula Reference Table

The following table provides the exact formulas for the six most critical calculations in the model, written in cell-reference notation where column B represents Year 1.

| Metric | Formula |
|---|---|
| Revenue Year N | `=Prior_Year_Revenue * (1 + Growth_Rate_N)` |
| EBITDA Year N | `=Revenue_N * EBITDA_Margin_N` |
| TLB Avg Balance | `=(TLB_Beg + TLB_End) / 2` |
| Cash Interest | `=TLB_Avg_Balance * Interest_Rate` |
| Cash Sweep | `=MIN(TLB_End_Before_Sweep, MAX(0, FCF - Mandatory_Amort))` |
| IRR | `=XIRR({-Equity_In, Equity_Out}, {Entry_Date, Exit_Date})` |
| MOIC | `=Exit_Equity_Value / Total_Equity_Invested` |
| Leverage Ratio | `=Net_Debt_End / LTM_EBITDA` |
| Exit EV | `=Exit_Multiple * Exit_Year_EBITDA` |
| PPA Amort (annual) | `=Acquired_Intangibles_At_Close / Amort_Life` |

### Professional Execution Standards

A complete, institutionally viable LBO model for investment committee presentation must satisfy three standards beyond mechanical correctness. First, every hardcoded assumption must be sourced: either from public comparable transaction data, the target company's audited financials, or the credit agreement term sheet. For MFSS, the 11.5x entry multiple should be benchmarked against precedent transactions in vertical SaaS (Roper Technologies' acquisitions, Vista Equity portfolio entries, and Thoma Bravo deal multiples from 2019–2023 cluster between 10x and 15x EV/EBITDA for businesses with 85%+ recurring revenue and NRR above 110%, placing the 11.5x entry squarely within the realistic range). Second, the sensitivity analysis must be presented before the base case in investment committee materials, not after, because the range of outcomes defines the investment thesis more rigorously than any single-point estimate. Third, the breach and recovery analysis must always be run before closing, because the information asymmetry between sponsor and lender around covenant compliance is a structural feature of LBO credit markets, and a sponsor who has pre-modeled the breach mechanics is in a materially stronger negotiating position than one who has not.

The model you have built in these three exercises is not a teaching toy. It is a working analytical instrument. The MFSS numbers are fictional, but the architecture, formula chain, covenant mechanics, and return attribution logic are identical to what a Vice President at a mid-market PE fund uses to decide whether to present a deal to their partners. The difference between that VP and an analyst who merely understands the concepts is exactly what these labs are designed to eliminate: the ability to sit down, open Excel, and build it without being told what to do next.
