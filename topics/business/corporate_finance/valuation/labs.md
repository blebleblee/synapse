# Operational Verification Labs: Valuation

## Objective & Operational Lab Setup

This lab sequence develops the hands-on mechanics of corporate valuation from the ground up, forcing you to build, test, and break real financial models rather than simply interpret pre-built outputs. The three exercises that follow treat valuation as an empirical engineering discipline: you assemble the instruments, calibrate them against observable market data, vary the parameters systematically, and then deliberately destroy your assumptions to understand where the model's load-bearing walls actually sit.

The practitioner's core insight is that a valuation is not a number. It is a probability distribution with a defensible central tendency. Every DCF you have ever seen that produced a single-point output was concealing enormous analytical uncertainty behind a false precision that served the investment banker's or buyer's narrative. Your job is to surface that uncertainty, quantify it, and make it legible to a decision-maker.

### Analytical Environment Configuration

You will work in Microsoft Excel or Google Sheets throughout. No specialized software is required, but your spreadsheet must be configured for precision work. In Excel, navigate to File → Options → Formulas and confirm that workbook calculation is set to Automatic, iteration is disabled (maximum iterations = 0 unless you are modeling a revolver with circular references), and precision is at Displayed Precision off, meaning the model carries full floating-point precision internally. In Google Sheets, confirm Tools → Spreadsheet settings → Calculation is set to On change and every minute.

Create a single workbook with the following eight tab structure before beginning Exercise 1. Name the tabs exactly as follows: `Inputs`, `IncomeStatement`, `BalanceSheet`, `CashFlow`, `DCF`, `Comps`, `Sensitivity`, and `Audit`. The `Inputs` tab is the single source of truth for every hard-coded assumption: revenue growth rates, margin assumptions, tax rates, capital structure, beta, risk-free rate, and comparable company multiples. Every formula in every other tab must reference back to `Inputs` using absolute references. No hardcoded numbers are permitted outside the `Inputs` tab. This discipline is non-negotiable because it is the only way Exercise 2's parameter variation can be executed cleanly and without corrupting the model's logic chain.

Establish a color convention on the `Inputs` tab that you will carry through all three exercises. Blue font on a white background marks a hard-coded input that the analyst controls. Black font on a white background marks a formula. Gray background marks a cell that feeds directly into the final valuation output. This three-color system is the standard at every bulge-bracket bank and top-tier PE shop because it makes auditing a stranger's model take ten minutes rather than two hours.

---

## Exercise 1: Foundational Practical Implementation

### The Subject Company

The company you are valuing is a fictional but structurally realistic mid-market B2B SaaS business called **Meridian Analytics, Inc.** It closed its most recent fiscal year (Year 0, which you treat as the last historical year) with $48.2 million in revenue, 71% gross margins, 18% EBITDA margins, $4.1 million in capital expenditures, $6.8 million in depreciation and amortization, a 25% cash tax rate on EBIT, and $22 million in net debt (total debt of $28 million minus $6 million in cash). It has 12.5 million fully diluted shares outstanding at a current market price of $31.40 per share, giving it a market capitalization of $392.5 million and an implied enterprise value of $414.5 million. These numbers belong in your `Inputs` tab now, each labeled clearly and formatted consistently.

### Building the Three-Statement Model (Years 1 through 5)

The income statement is the engine. Begin by projecting revenue. Enter the following annual growth rate assumptions in `Inputs`: Year 1 = 22%, Year 2 = 19%, Year 3 = 16%, Year 4 = 13%, Year 5 = 11%. These rates reflect a growth deceleration curve that is empirically consistent with mid-market SaaS companies scaling from $40 to $80 million in ARR, where land-and-expand economics begin to mature and new logo acquisition costs rise with market penetration. In `IncomeStatement`, cell B3, enter the formula `=Inputs!B4*(1+Inputs!C4)` where `Inputs!B4` is Year 0 revenue and `Inputs!C4` is the Year 1 growth rate. Carry this forward through Year 5 by incrementing the year reference but always anchoring to the prior year's revenue output, not to `Inputs!B4` directly, so the compounding logic is preserved.

Gross profit is revenue multiplied by the gross margin assumption. Enter a gross margin of 71% in `Inputs` for Years 1 and 2, then 72% for Years 3 and 4, and 73% for Year 5, reflecting modest scale-driven improvement in hosting and support costs as a percentage of revenue. EBITDA margin expands from 18% in Year 1 to 19% in Year 2, 20% in Year 3, 21% in Year 4, and 22% in Year 5. This expansion is consistent with operating leverage on R&D and G&A as the sales and marketing investment as a percentage of revenue stabilizes. EBIT is EBITDA minus D&A, and you will grow D&A at a fixed rate of 8% per year from the Year 0 base of $6.8 million, reflecting the capitalized software amortization schedule of a maturing SaaS platform. NOPAT (Net Operating Profit After Tax) equals EBIT multiplied by (1 minus the 25% cash tax rate). This is the correct entry point for unlevered free cash flow because it strips out the financing tax shield, which belongs in WACC, not in the cash flow numerator.

On the `BalanceSheet` tab, build a working capital schedule. For Meridian, the relevant working capital accounts are accounts receivable (DSO of 45 days), deferred revenue (DPO equivalent of 30 days of forward revenue), and accounts payable (DPO of 35 days). The working capital driver formula for accounts receivable is `=(DSO/365)*Revenue`. Deferred revenue for a SaaS company is a liability, not an asset, and it represents a source of cash when it grows. The change in deferred revenue therefore enters the free cash flow bridge as a positive when revenue is growing, a structural advantage of subscription businesses that is frequently mispriced in public market comps. Build the net working capital line as current operating assets minus current operating liabilities, then compute the change in NWC period over period. This change line flows directly into the `CashFlow` tab.

Capital expenditures grow at 6% per year from the Year 0 base of $4.1 million. This assumption is entered in `Inputs` and referenced in both the `CashFlow` and `BalanceSheet` tabs. The debt schedule carries the existing $28 million at an interest rate of 6.5% per year, with no principal repayment modeled in the base case (a bullet maturity assumption). Cash interest expense flows to the income statement below EBIT but is excluded from the unlevered FCF build.

Unlevered free cash flow for each year is therefore: NOPAT plus D&A minus change in NWC minus CapEx. Build this in the `DCF` tab. For Year 1, the formula chain resolves as follows. Revenue of $58.804 million (Year 0's $48.2 million grown at 22%) produces EBITDA of $10.585 million (18% margin), EBIT of $4.145 million (after subtracting Year 1 D&A of $7.344 million, which is $6.8 million grown at 8%), NOPAT of $3.109 million (at 25% tax), plus D&A add-back of $7.344 million, minus change in NWC (compute from your working capital schedule; in Year 1 this will be approximately negative $1.2 million, meaning NWC increased, which is a cash outflow), minus CapEx of $4.346 million (Year 0's $4.1 million grown at 6%). Year 1 unlevered FCF is therefore approximately $5.907 million. Build Years 2 through 5 identically.

### Calculating WACC

WACC is the discount rate that reflects the blended cost of Meridian's capital structure on an after-tax, market-value-weighted basis. It is not an art; it is a mechanical calculation with four inputs that each require justification.

Enter these inputs in `Inputs`. The risk-free rate is 4.35%, which corresponds to the current U.S. 10-year Treasury yield (use the actual current rate when you run this exercise; the structural logic does not change). The equity risk premium (ERP) is 5.5%, consistent with Damodaran's implied ERP for the U.S. market. Beta is 1.25, estimated by unlevering the median observed beta of a peer group of publicly traded B2B SaaS companies at comparable revenue scale (between $40 million and $100 million ARR), then re-levering to Meridian's target capital structure of 20% debt to total capital. The cost of debt pre-tax is 6.5% (Meridian's existing facility rate), and the tax rate is 25%.

The cost of equity using CAPM is: `=Inputs!RiskFreeRate + Inputs!Beta * Inputs!ERP`, which resolves to 4.35% + (1.25 × 5.5%) = 4.35% + 6.875% = **11.225%**. The after-tax cost of debt is `=Inputs!CostOfDebt * (1 - Inputs!TaxRate)` = 6.5% × 0.75 = **4.875%**. WACC is `=(0.80 * Inputs!CostOfEquity) + (0.20 * Inputs!AfterTaxCostOfDebt)` = (0.80 × 11.225%) + (0.20 × 4.875%) = 8.98% + 0.975% = **9.955%**, which you round to **9.96%** in the model.

### Terminal Value and Equity Value Bridge

The terminal value captures everything the business produces after Year 5. Use the Gordon Growth Model applied to Year 5 unlevered FCF. Enter a terminal growth rate of 3.5% in `Inputs`, reflecting long-run nominal GDP growth for a software business with durable recurring revenue. The terminal value formula is: `=DCF!Year5_FCF * (1 + Inputs!TerminalGrowthRate) / (Inputs!WACC - Inputs!TerminalGrowthRate)`.

Discount each year's FCF and the terminal value back to present value using the mid-year convention, which assumes cash flows arrive at the midpoint of each year rather than at year-end. The mid-year discount factor for Year $n$ is $(1 + \text{WACC})^{-(n - 0.5)}$. In Excel: `=1/((1+Inputs!WACC)^(B1-0.5))` where `B1` contains the year number. Sum the present values of Years 1 through 5 and the present value of the terminal value to arrive at Enterprise Value.

The equity bridge subtracts net debt from enterprise value: `=DCF!EnterpriseValue - Inputs!NetDebt`. Divide by fully diluted shares outstanding to arrive at the implied share price. Record the implied enterprise value, implied equity value, and implied share price in the `Audit` tab. At the base case assumptions, your model should produce an enterprise value of approximately $412 to $425 million, an implied share price of approximately $30.50 to $32.50, which is a healthy sanity check against Meridian's observed market price of $31.40 per share. If your output deviates from this range by more than 5%, audit your FCF build line by line before proceeding.

### Trading Comps Cross-Check

Navigate to the `Comps` tab. A DCF result that cannot be validated against observable market pricing is analytically incomplete. The comparable companies for Meridian are mid-market B2B SaaS businesses. Use the following peer group with their current EV/NTM Revenue and EV/NTM EBITDA multiples drawn from a representative market environment, noting that you should substitute live market data when you run this exercise.

| Company | EV/NTM Revenue | EV/NTM EBITDA |
|---|---|---|
| Peer A | 6.8x | 28.4x |
| Peer B | 7.2x | 31.1x |
| Peer C | 5.9x | 25.6x |
| Peer D | 8.1x | 34.7x |
| Peer E | 6.4x | 27.3x |
| **Median** | **6.8x** | **28.4x** |
| **25th Percentile** | **6.1x** | **26.5x** |
| **75th Percentile** | **7.6x** | **32.9x** |

Apply the median EV/NTM Revenue multiple to Meridian's Year 1 projected revenue of $58.804 million: 6.8 × $58.804 million = **$399.9 million**. Apply the median EV/NTM EBITDA multiple to Year 1 EBITDA of $10.585 million: 28.4 × $10.585 million = **$300.6 million**. The revenue multiple produces an implied enterprise value that is directionally consistent with the DCF, while the EBITDA multiple produces a lower figure, which is structurally expected because Meridian's 18% EBITDA margin is below the peer group median, which is typically 22 to 26% at this revenue scale. Record both comps-implied enterprise values in the `Audit` tab alongside your DCF output to form the beginning of a football field.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Constructing the Sensitivity Analysis

A model that produces one number is a tool designed to sell a decision rather than interrogate it. Systematic parameter variation reveals which assumptions actually drive value and which are noise, and this knowledge is precisely what separates a practitioner from a spreadsheet operator.

Navigate to the `Sensitivity` tab. You will build two sensitivity tables and one scenario analysis block.

The first sensitivity table holds revenue growth constant at the base case rates and varies WACC on the horizontal axis against terminal growth rate on the vertical axis. Build a 7×7 matrix. WACC ranges from 8.0% to 11.0% in steps of 0.5%. Terminal growth rate ranges from 2.0% to 5.0% in steps of 0.5%. The output of each cell is the implied enterprise value. In Excel, use the Data → What-If Analysis → Data Table function. The row input cell is the WACC cell in `Inputs`; the column input cell is the terminal growth rate cell in `Inputs`. The formula in the top-left corner of the matrix must reference the enterprise value output in `DCF` directly.

The resulting matrix will show you that at the base WACC of 9.96% and terminal growth of 3.5%, enterprise value is approximately $418 million. At WACC of 11.0% and terminal growth of 2.0%, enterprise value compresses to approximately $298 million. At WACC of 8.0% and terminal growth of 5.0%, enterprise value expands to approximately $641 million. This 2.1× spread between the stress case and the optimistic case is the actual answer to the question "what is Meridian worth?" — not the single-point DCF output. Apply conditional formatting to this table: green for values above $450 million, yellow for $350 to $450 million, and red for below $350 million, so the distribution of outcomes is visually immediate.

The second sensitivity table holds WACC and terminal growth at base case and varies Year 1 through Year 5 revenue growth (applying a uniform upward or downward shift to all five years simultaneously) on one axis against EBITDA margin in Year 5 on the other. Revenue growth shift ranges from negative 6 percentage points to positive 6 percentage points in steps of 2 percentage points. Year 5 EBITDA margin ranges from 17% to 27% in steps of 2 percentage points. This table captures the two operational variables a buyer or investor can most directly influence through post-acquisition strategy: top-line acceleration and cost structure optimization.

To build a uniform growth shift, add a single cell in `Inputs` labeled `GrowthShift` initialized to 0%. In each year's revenue growth formula in `IncomeStatement`, add `+Inputs!GrowthShift` to the existing rate reference. The Data Table row input is now `Inputs!GrowthShift` and the column input is `Inputs!Year5EBITDAMargin`. This architecture is what makes the sensitivity table live: change either input manually and the entire income statement, FCF build, and enterprise value recalculate without breaking any formula chain.

### Scenario Analysis: Three Structured Cases

Scenario analysis differs from sensitivity analysis in that it moves multiple assumptions simultaneously in a correlated and narratively coherent way. Enter three named scenarios in `Inputs` with the following complete parameter sets.

The **Base Case** reflects the assumptions already built: 22% Year 1 revenue growth decelerating to 11% by Year 5, EBITDA margin expanding from 18% to 22%, D&A growing at 8% per year, CapEx at 6% growth, WACC of 9.96%, terminal growth of 3.5%. This case represents the consensus extrapolation of Meridian's current trajectory with modest operating leverage realization.

The **Bull Case** reflects accelerated enterprise adoption driven by a successful channel partnership program that management has in late-stage negotiation. Revenue growth rates are 28%, 24%, 20%, 17%, and 14% for Years 1 through 5. EBITDA margins are 19%, 21%, 23%, 25%, and 27%, reflecting faster-than-expected G&A leverage as headcount growth lags revenue growth. WACC compresses to 9.3% because the company executes a secondary offering that reduces leverage, lowering beta re-levering. Terminal growth is 4.0% because the channel program creates durable annuity revenue with high switching costs. CapEx grows at 4% per year because the channel model shifts hosting costs partially to partners. D&A grows at 7% per year.

The **Bear Case** reflects competitive pricing pressure from a well-funded new entrant and a macro slowdown that delays enterprise buying decisions. Revenue growth rates are 14%, 11%, 9%, 7%, and 6%. EBITDA margins contract from 18% to 16% in Year 1 as the company increases sales and marketing spend to defend market share, then recover only to 17%, 18%, 19%, and 20% by Year 5. WACC rises to 10.8% because credit markets tighten and the equity risk premium on high-growth software compresses. Terminal growth is 2.5%. CapEx grows at 8% per year as the company invests in product differentiation.

Build the scenario toggle using Excel's CHOOSE function in `Inputs`. Add a cell labeled `ScenarioSwitch` with value 1, 2, or 3 for Base, Bull, and Bear respectively. Each growth rate and margin assumption in the tab is then written as `=CHOOSE(Inputs!ScenarioSwitch, BaseValue, BullValue, BearValue)`. With this architecture, changing `ScenarioSwitch` from 1 to 3 rebuilds the entire model in one keystroke.

The three scenarios produce the following enterprise value outputs. Base Case: approximately $418 million. Bull Case: approximately $618 million. Bear Case: approximately $271 million. The midpoint of the Bear-to-Bull range is $444 million, which is modestly above the base case due to the asymmetric upside structure of a subscription revenue model where expansion revenue has very low incremental cost. Record these in the `Audit` tab.

### Empirical Regression: Does Multiple Expansion Track Growth?

This sub-exercise builds a simple regression model in the `Comps` tab to test whether the EV/NTM Revenue multiples in your peer group are systematically explained by NTM revenue growth rates, as theory predicts. If a faster-growing SaaS company commands a higher revenue multiple, the coefficient on growth should be positive and statistically significant.

Extend your peer group table with two additional columns: NTM Revenue Growth (%) and EV/NTM Revenue (the multiple itself, which you already have). Use the following data, which represents a realistic 10-company B2B SaaS peer universe.

| Company | NTM Rev Growth (%) | EV/NTM Revenue |
|---|---|---|
| Peer A | 24% | 6.8x |
| Peer B | 28% | 7.2x |
| Peer C | 19% | 5.9x |
| Peer D | 33% | 8.1x |
| Peer E | 22% | 6.4x |
| Peer F | 31% | 7.8x |
| Peer G | 17% | 5.4x |
| Peer H | 26% | 7.0x |
| Peer I | 20% | 6.1x |
| Peer J | 29% | 7.5x |

In Excel, use the LINEST function to fit an OLS regression of EV/NTM Revenue (dependent variable) on NTM Revenue Growth (independent variable). The array formula is `=LINEST(C2:C11, B2:B11, TRUE, TRUE)` entered with Ctrl+Shift+Enter. LINEST returns a 5×2 array: the first row contains the slope and intercept, the second row contains standard errors for each, the third row contains R² and standard error of the regression, the fourth row contains the F-statistic and degrees of freedom, and the fifth row contains regression SS and residual SS.

Your regression should produce a slope of approximately 0.185, meaning that for each 1 percentage point increase in NTM revenue growth, the EV/Revenue multiple expands by approximately 0.185 turns. The intercept is approximately 2.15. R² should be approximately 0.97, confirming that growth rate explains nearly all of the cross-sectional variation in revenue multiples within this peer group. The practical implication is that you can back-solve for the implied growth rate the market is pricing into Meridian at its current $414.5 million EV: `=(CurrentEVRevMultiple - Intercept) / Slope` = `=(7.04 - 2.15) / 0.185` = approximately **26.4%**. If Meridian's actual NTM growth is 22%, the market is pricing in slight growth acceleration or a premium for some quality factor not captured by growth alone. This is a conversation-starter for a buy-side analyst, not a conclusion.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### The Purpose of Deliberate Model Destruction

Professional-grade valuation work requires knowing where your model breaks down structurally, not just where the numbers become uncomfortable. A model that cannot survive stress testing will fail in front of a creditor, a board, or a counterparty at exactly the moment when the stakes are highest. This exercise systematically introduces eight failure conditions, documents the model behavior, and builds recovery logic into the model architecture.

### Failure Condition 1: Terminal Growth Rate Exceeds WACC

Navigate to `Inputs` and change the terminal growth rate to 10.5%. This exceeds WACC of 9.96%, which causes the Gordon Growth Model denominator `(WACC - g)` to become negative. The terminal value formula produces a large negative enterprise value, which is mathematically correct but economically nonsensical: no asset with positive free cash flows can have a negative present value. The model does not crash; it silently produces a wrong answer. 

The recovery protocol is an input validation guard. In the terminal value formula cell in `DCF`, wrap the calculation in an IFERROR and an IF check: `=IF(Inputs!TerminalGrowthRate >= Inputs!WACC, "ERROR: g ≥ WACC", DCF!Year5_FCF * (1 + Inputs!TerminalGrowthRate) / (Inputs!WACC - Inputs!TerminalGrowthRate))`. Add a matching alert in the `Audit` tab: `=IF(Inputs!TerminalGrowthRate >= Inputs!WACC, "CRITICAL: Terminal Growth Exceeds WACC", "PASS")`. Reset terminal growth to 3.5% after verifying the guard fires correctly.

### Failure Condition 2: Revenue Growth Rates Become Negative

Change all five revenue growth rates to negative 15%, simulating a severe demand destruction scenario such as a major platform deprecation event or the loss of a largest-customer contract. Trace through the income statement. With 71% gross margins on a revenue base that is declining 15% per year, Meridian's EBITDA turns negative in Year 2 when fixed cost leverage works in reverse. NOPAT becomes negative. Unlevered FCF turns negative in Years 2 through 5.

A DCF with multiple negative cash flow years is not automatically wrong, but it demands scrutiny because the terminal value is now carrying essentially the entire weight of the enterprise value. Compute the percentage of total enterprise value attributable to terminal value in this stress scenario: `=PV_TerminalValue / TotalEnterpriseValue`. In the base case, this ratio is approximately 72%, which is already high. In the negative growth scenario, it typically exceeds 115%, meaning the present value of the near-term cash flows is actually subtracting from enterprise value. At this point, the DCF is no longer a valuation tool; it is a solvency assessment, and the analyst should shift to a distressed credit framework using liquidation value and recovery analysis. Document this boundary condition in the `Audit` tab as a named test: "Revenue Decline Stress — DCF Validity Breaks When Terminal Value Exceeds 100% of EV." Reset growth rates to base case.

### Failure Condition 3: Circular Reference in Debt Schedule

Add a simple revolving credit facility to the balance sheet to model a more realistic capital structure. The revolver draws when cash falls below $3 million and repays when cash exceeds $8 million. This introduces a circularity: the revolver balance affects interest expense, which affects net income, which affects ending cash, which determines the revolver balance. Enable iteration in Excel (File → Options → Formulas → Enable Iterative Calculation, Maximum Iterations = 100, Maximum Change = 0.001). The model will now converge through iteration rather than failing with a circular reference error.

The diagnostic check is in the `Audit` tab: add a cell that computes `=ABS(Inputs!Cash_End - Inputs!Cash_End_Prior_Iteration)` and flags a warning if this exceeds $1,000, which would indicate non-convergence. In practice, the revolver circular reference in a well-structured model converges in 3 to 5 iterations. If your model fails to converge, the most common cause is that the revolver formula is not bounded correctly and is oscillating. The fix is to cap the revolver draw at the facility limit (`=MIN(MaxFacility, MAX(0, MinCashThreshold - BeginningCash))`) and ensure the repayment formula mirrors this structure exactly.

### Failure Condition 4: Working Capital Assumption Flip

Change Meridian's deferred revenue assumption from 30 days to 0 days, simulating a contract renegotiation from annual upfront billing to monthly in-arrears billing. This single change eliminates the deferred revenue liability and converts what was a cash source into a neutral item. Recompute the change in NWC for Year 1 through Year 5. You will find that Year 1 FCF drops by approximately $3.2 million, Year 2 drops by approximately $2.8 million, and Years 3 through 5 drop by progressively smaller amounts as the annual increment to deferred revenue was already decelerating. The enterprise value impact is approximately negative $14 to $18 million at WACC of 9.96%, a meaningful 3.5 to 4.5% reduction in total enterprise value from a single billing terms change. This is not a trivial modeling exercise: it is exactly the kind of contractual covenant a PE buyer's legal team negotiates in a purchase agreement, and knowing the value impact in advance is what makes a practitioner commercially effective.

### Failure Condition 5: Beta Estimation Error

In the WACC build, change beta from 1.25 to 0.75, simulating an analyst who used a trailing 5-year beta from a period when Meridian was a slower-growth, lower-multiple business before its SaaS transition. Cost of equity falls to `=4.35% + 0.75 × 5.5%` = 8.475%. WACC drops to `=(0.80 × 8.475%) + (0.20 × 4.875%)` = 6.78% + 0.975% = **7.755%**. Enterprise value increases to approximately $571 million. This is a 36.6% inflation of enterprise value from a single input error. The recovery protocol is to document the beta estimation methodology in the `Audit` tab: source (Bloomberg raw beta vs. Damodaran industry beta vs. peer-group median), the unlevering formula used (`Levered Beta / (1 + (1 - Tax Rate) × D/E)`), the re-levering formula applied (`Unlevered Beta × (1 + (1 - Tax Rate) × Target D/E)`), and the date the peer group was sourced. Any DCF where the beta methodology is not documented should be treated as unaudited. Reset beta to 1.25.

### Failure Condition 6: Tax Rate Shock

Change the cash tax rate from 25% to 35%, simulating a U.S. federal tax rate increase plus state taxes in a high-tax jurisdiction. NOPAT in each year declines by approximately 13.3% (from 75% to 65% of EBIT). Recompute FCF for all five years and observe the enterprise value impact: a compression of approximately $38 to $45 million, or roughly 9 to 11% of base enterprise value. This matters in cross-border M&A where the target's historical effective tax rate may not reflect the buyer's post-acquisition tax structure. The `Audit` tab should include a cross-check: `=IncomeStatement!TaxExpense / IncomeStatement!PreTaxIncome` for each year, confirming that the effective tax rate in the income statement matches the assumption in `Inputs`. Reset tax rate to 25%.

### Failure Condition 7: CapEx Reclassification

Change CapEx from $4.1 million base growing at 6% per year to $12.5 million base growing at 10% per year, simulating a scenario where management has committed to a large data center buildout that was disclosed in the footnotes of the most recent 10-K but not reflected in the base model. FCF across the five-year projection period is reduced by a cumulative $51.4 million, and enterprise value decresses by approximately $37 to $42 million on a present-value basis. The recovery protocol is to build a CapEx audit row in the `IncomeStatement` tab: CapEx as a percentage of revenue for each year, with a threshold alert if CapEx/Revenue exceeds 15%, which would signal a capital intensity level inconsistent with a pure-play SaaS business and warrant reclassification into an infrastructure or hybrid software-hardware category with different comparable company multiples. Reset CapEx to base case.

### Failure Condition 8: Net Debt Double-Count

Intentionally create an error in the equity bridge by subtracting gross debt ($28 million) but failing to add back cash ($6 million), resulting in net debt of $28 million instead of $22 million. The implied share price decreases by `=$6M / 12.5M shares` = $0.48 per share. While $0.48 per share sounds small, at scale this error on a $1 billion deal with $250 million in cash on the balance sheet represents a $250 million misstatement in equity value allocation, which is the kind of error that generates legal liability in a signed fairness opinion. The `Audit` tab should contain a mandatory reconciliation row: `=DebtSchedule!TotalGrossDebt - IncomeStatement!CashEndOfYear5` validated against `Inputs!NetDebt`. If these two figures differ by more than $100,000, the cell flags red. Reset to correct net debt of $22 million.

---

## Operational Reference Guide & Diagnostic Checklist

### Model Audit Protocol

Before presenting any valuation output to a decision-maker, work through the following verification sequence in the order it appears. Each step is a gate: if the check fails, the model is not ready.

The first audit checks structural integrity. Confirm that every formula in `IncomeStatement`, `BalanceSheet`, `CashFlow`, and `DCF` traces back to `Inputs` with no hardcoded values outside that tab. In Excel, use Formulas → Trace Precedents on five randomly selected formula cells to verify the reference chain. The color convention (blue for inputs, black for formulas, gray for outputs) must be consistently applied.

The second audit checks accounting identity. The balance sheet must balance: total assets must equal total liabilities plus equity for every projected year. Build this check in the `BalanceSheet` tab: `=IF(ABS(TotalAssets - TotalLiabilitiesAndEquity) > 1, "BS DOES NOT BALANCE", "PASS")`. A common source of balance sheet imbalance is omitting the ending cash balance from the asset side when modeling a revolver, or failing to close retained earnings from the income statement.

The third audit checks FCF sign logic. Build a flag in `DCF` that checks whether unlevered FCF in any year is more negative than negative $20 million: `=IF(MIN(Year1FCF:Year5FCF) < -20000, "REVIEW: Deeply Negative FCF", "PASS")`. Deeply negative FCF years are not automatically wrong, but they require an explanatory note documenting why they occur.

The fourth audit checks terminal value proportion. `=PV_TerminalValue / TotalEnterpriseValue` must be between 55% and 85% for a healthy growth-stage SaaS business. Below 55% suggests the near-term projection period is too long and the model may be double-counting terminal growth within the explicit forecast. Above 85% suggests either an over-aggressive terminal growth rate or a projection period that terminates too early before the business reaches its steady state.

The fifth audit checks WACC vs. comparable cost of capital. Retrieve the WACC implied by your peer group using each company's capital structure and beta. If your Meridian WACC deviates from the peer group median WACC by more than 150 basis points without a documented justification (such as a materially different leverage ratio or unique geographic risk), revisit your beta estimation.

The sixth audit checks the football field completeness. The `Audit` tab must contain at minimum four enterprise value data points before a valuation can be presented: DCF base case, DCF bear case, DCF bull case, and trading comps (both EV/Revenue and EV/EBITDA midpoints). The range between the lowest and highest data point should be explicitly labeled "Valuation Range" and presented as the deliverable, not the single-point DCF output.

### Critical Formula Reference

The following formulas are the mechanical load-bearing elements of the entire model. Each is presented exactly as it must appear in a cell, with the assumption that `Inputs!` references correspond to the named cells built in Exercise 1.

**Unlevered Free Cash Flow:**
`= NOPAT + D&A - Change_in_NWC - CapEx`

where NOPAT = `EBIT × (1 - Inputs!TaxRate)` and Change_in_NWC = `NWC_CurrentYear - NWC_PriorYear` (positive change means cash outflow).

**Mid-Year Discount Factor for Year n:**
`= 1 / ((1 + Inputs!WACC)^(n - 0.5))`

**Terminal Value (Gordon Growth, Mid-Year Convention):**
`= (Year5_FCF × (1 + Inputs!TerminalGrowthRate) / (Inputs!WACC - Inputs!TerminalGrowthRate)) × (1 / ((1 + Inputs!WACC)^4.5))`

The 4.5-year discount exponent reflects discounting from the end of Year 5 (year 4.5 under mid-year convention, since the terminal value itself represents Year 6 and beyond but is capitalized at the Year 5 period-end).

**WACC:**
`= (E/(D+E)) × Ke + (D/(D+E)) × Kd × (1 - Inputs!TaxRate)`

**Cost of Equity (CAPM):**
`= Inputs!RiskFreeRate + Inputs!Beta × Inputs!ERP`

**Re-Levered Beta:**
`= Inputs!UnleveredBeta × (1 + (1 - Inputs!TaxRate) × (Inputs!NetDebt / Inputs!MarketCapEquity))`

**Net Revenue Retention (for SaaS cross-check):**
`= (Beginning_ARR + Expansion_ARR - Churned_ARR) / Beginning_ARR`

A NRR above 110% is a signal that Meridian's subscriber base is growing through expansion alone, which structurally supports a terminal growth rate above 3.5% because existing customers are driving organic compounding without new customer acquisition cost. This metric does not appear in the DCF directly, but it calibrates the terminal growth assumption with an observable operational data point.

**EV to Equity Bridge:**
`= EnterpriseValue - TotalDebt + CashAndEquivalents - MinorityInterest - PreferredStock`

For Meridian's simple capital structure, this reduces to `EnterpriseValue - NetDebt`.

### Common Failure Modes and Their Diagnostic Signatures

When a valuation model produces an output that is implausible relative to observable market pricing, the cause is almost always one of five structural errors. Terminal value exceeds 85% of enterprise value is almost always a sign that WACC is too low or the explicit projection period is too short. Enterprise value from the DCF exceeds the trading comps range by more than 30% typically signals an over-optimistic growth assumption or a terminal growth rate that creates a near-perpetuity in the numerator. A DCF enterprise value that is below the trading comps floor by more than 20% usually indicates a beta that is too high, a tax rate that is punitive relative to the actual structure, or CapEx that includes maintenance expenditures already captured in EBITDA margins (a common error when EBITDA is used as a proxy for cash EBITDA without stripping out capitalized software development). A negative equity value from the bridge is mechanically possible for a highly leveraged company, but if Meridian shows a negative equity value at base case, the most likely cause is that net debt has been computed as gross debt without netting cash. A valuation range so wide that it is analytically useless (for example, $200 million to $900 million) is a signal that the model is not stress-tested but rather miscalibrated: the scenario inputs are not economically correlated, and the analyst is running parameter combinations that cannot occur simultaneously in the real world.

The practitioner's standard is that a finished valuation deliverable must include a written one-page assumption memo accompanying the model. This memo states the basis for every key input in `Inputs`: where the revenue growth rates came from (management guidance, historical CAGR, or sell-side consensus), why the WACC beta was set at a specific level (peer group composition and unlevering methodology), what the terminal growth rate reflects about long-run competitive positioning, and what the most consequential single assumption is in the model (almost always the Year 5 EBITDA margin, because it determines both the terminal FCF numerator and the implicit steady-state competitive positioning of the business). Without this memo, the model is a calculation. With it, it is a valuation.
