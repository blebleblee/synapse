# Operational Verification Labs: Acquisitions

## Objective & Operational Lab Setup

This laboratory manual operationalizes the full acquisition modeling pipeline that a corporate finance practitioner executes during a live transaction. You will build two interconnected models from scratch in a spreadsheet environment: a strategic acquirer's accretion/dilution framework and a private equity sponsor's leveraged buyout debt waterfall with returns attribution. Every exercise uses the same target company so that the strategic and financial buyer perspectives can be directly compared on identical fundamentals.

The case vehicle is Cascade Components Inc., a private industrial components manufacturer with trailing-twelve-month revenue of $800 million and EBITDA of $160 million (20% margin). The acquirer in the strategic scenario is Meridian Industrial Corp., a public company with a $36.00 share price, 100 million shares outstanding, and trailing net income of $240 million (EPS $2.40, P/E 15.0x). The LBO scenario uses the same target but capitalizes the acquisition through a senior secured credit facility, a Term Loan B, and payment-in-kind mezzanine debt, with a sponsor writing an equity check at close.

Set up a single Excel workbook with five worksheets in the following order: `Inputs_A&D`, `A&D_Model`, `LBO_Model`, `Sensitivity`, and `Stress_Test`. Format all currency values in millions with one decimal precision, all percentages to one decimal, and all multiples to one decimal. Use blue font for hard-coded inputs, black font for formulas, and green font for linked inputs from other sheets. This color convention is standard across investment banking and private equity and allows anyone reviewing the model to distinguish assumptions from calculations at a glance.

The analytical instruments you will use are Excel's native Data Table function for sensitivity analysis, Goal Seek for breakeven calculations, and manual scenario overrides for stress testing. No third-party add-ins are required. All formulas below use A1 reference style and assume the cell layout described in each exercise. Where a formula references a cell on another worksheet, the sheet name is prefixed with an exclamation mark.

---

## Exercise 1: Foundational Practical Implementation

### 1.1 Building the Accretion/Dilution Model

The accretion/dilution analysis answers a single question that every corporate development officer presents to the board: does the transaction increase or decrease the acquirer's earnings per share? The answer depends on the interaction between the purchase price, the financing structure, the target's earnings, the amortization of intangible assets created in the purchase price allocation, and the after-tax cost of any new debt. The model you build here isolates each of these drivers so that the board can see not just whether the deal is accretive but why.

Begin on the `Inputs_A&D` worksheet. Enter the acquirer's standalone profile in rows 4 through 20, the target's standalone profile in rows 22 through 34, and the transaction terms in rows 36 through 50. The following table provides every cell entry; format column B for values and column C for the label so the model reads cleanly when printed.

| Cell | Label | Value or Formula |
|---|---|---|
| B4 | Acquirer revenue (LTM) | 2000.0 |
| B5 | Acquirer EBITDA (LTM) | 440.0 |
| B6 | Acquirer EBITDA margin | =B5/B4 |
| B7 | Acquirer D&A (LTM) | 80.0 |
| B8 | Acquirer EBIT (LTM) | =B5-B7 |
| B9 | Acquirer interest expense (LTM) | 40.0 |
| B10 | Acquirer pre-tax income (LTM) | =B8-B9 |
| B11 | Acquirer tax rate | 0.25 |
| B12 | Acquirer tax expense | =B10*B11 |
| B13 | Acquirer net income (LTM) | =B10-B12 |
| B14 | Acquirer shares outstanding (M) | 100.0 |
| B15 | Acquirer EPS (LTM) | =B13/B14 |
| B16 | Acquirer share price | 36.00 |
| B17 | Acquirer market cap | =B16*B14 |
| B18 | Acquirer P/E ratio | =B16/B15 |
| B19 | Acquirer net debt | 600.0 |
| B20 | Acquirer enterprise value | =B17+B19 |
| B22 | Target revenue (LTM) | 800.0 |
| B23 | Target EBITDA (LTM) | 160.0 |
| B24 | Target EBITDA margin | =B23/B22 |
| B25 | Target D&A (LTM) | 40.0 |
| B26 | Target EBIT (LTM) | =B23-B25 |
| B27 | Target interest expense (LTM) | 20.0 |
| B28 | Target pre-tax income (LTM) | =B26-B27 |
| B29 | Target tax rate | 0.25 |
| B30 | Target tax expense | =B28*B29 |
| B31 | Target net income (LTM) | =B28-B30 |
| B32 | Target gross debt | 400.0 |
| B33 | Target cash | 50.0 |
| B34 | Target net debt | =B32-B33 |
| B36 | Purchase multiple (x EBITDA) | 10.0 |
| B37 | Transaction enterprise value | =B23*B36 |
| B38 | Less: target net debt | =B34 |
| B39 | Equity purchase price | =B37-B38 |
| B40 | Transaction costs | 40.0 |
| B41 | Total funding required | =B39+B40 |
| B42 | New debt issued | 600.0 |
| B43 | New debt interest rate | 0.055 |
| B44 | Acquirer cash used | 190.0 |
| B45 | Stock issued (value) | =B41-B42-B44 |
| B46 | Stock issued (shares, M) | =B45/B16 |
| B47 | Pro forma shares (M) | =B14+B46 |

The transaction structure layers three funding sources to cover the $1,290 million total funding requirement: $600 million of new acquisition debt at 5.5%, $190 million of existing acquirer balance sheet cash, and $500 million of newly issued stock priced at $36.00 per share (13.889 million new shares). The target's existing $400 million of debt is assumed, not refinanced, so it remains on the consolidated balance sheet at its original 5.0% rate. The target's $50 million of cash is acquired through consolidation and appears on the pro forma balance sheet but is not used as a transaction funding source.

### 1.2 Purchase Price Allocation Schedule

The purchase price allocation determines how much of the total consideration flows into identifiable tangible and intangible assets versus goodwill. This matters for the accretion analysis because the step-up in asset values creates new amortization expense that reduces GAAP earnings, even though the cash outflow behind those assets already occurred at close. Under ASC 805, the purchase consideration equals the transaction enterprise value, and goodwill is the residual after allocating fair value to all identifiable assets.

On the `Inputs_A&D` sheet, continue with the PPA schedule in rows 49 through 72.

| Cell | Label | Value or Formula |
|---|---|---|
| B49 | Purchase consideration (= TEV) | =B37 |
| B50 | Target net assets at book value | 300.0 |
| B51 | PP&E fair value step-up | 100.0 |
| B52 | Inventory fair value step-up | 20.0 |
| B53 | Customer relationships (new intangible) | 250.0 |
| B54 | Technology and IP (new intangible) | 150.0 |
| B55 | Total fair value step-ups | =B51+B52+B53+B54 |
| B56 | Net identifiable assets at FV | =B50+B55 |
| B57 | Goodwill | =B49-B56 |
| B59 | PP&E step-up useful life (years) | 15.0 |
| B60 | Customer relationships life (years) | 10.0 |
| B61 | Technology and IP life (years) | 7.0 |
| B62 | Annual PP&E step-up amortization | =B51/B59 |
| B63 | Annual customer relationship amortization | =B53/B60 |
| B64 | Annual technology amortization | =B54/B61 |
| B65 | Total annual PPA amortization | =B62+B63+B64 |
| B66 | Inventory step-up (Year 1 COGS only) | =B52 |
| B68 | Synergy run-rate: cost | 30.0 |
| B69 | Synergy realization rate (Year 1) | 0.50 |
| B70 | Year 1 cost synergies | =B68*B69 |
| B71 | Synergy run-rate: revenue | 20.0 |
| B72 | Year 1 revenue synergies | =B71*B69 |

The PPA yields $780 million of goodwill ($1,600 million consideration minus $820 million of net identifiable assets at fair value) and $53.1 million of annual amortization expense from the intangible step-ups. The inventory step-up of $20 million flows through cost of goods sold in Year 1 only, creating a one-time drag on reported gross margin. The PP&E step-up amortizes over 15 years ($6.667 million annually), customer relationships over 10 years ($25.0 million), and technology over 7 years ($21.429 million). Transaction costs of $40 million are expensed immediately under ASC 805 and are not capitalized into goodwill.

### 1.3 Pro Forma Income Statement and Accretion Calculation

Move to the `A&D_Model` worksheet to construct the pro forma income statement. Every line item below pulls from the `Inputs_A&D` sheet using direct cell references. The model computes both GAAP EPS (which includes PPA amortization and transaction costs) and adjusted cash EPS (which adds back PPA amortization and excludes transaction costs), because the gap between the two reveals how much of the dilution is non-cash accounting fiction versus real economic cost.

| Cell | Label | Formula |
|---|---|---|
| B4 | Pro forma revenue | ='Inputs_A&D'!B4+'Inputs_A&D'!B22+'Inputs_A&D'!B72 |
| B5 | Pro forma EBITDA (pre-synergy) | ='Inputs_A&D'!B5+'Inputs_A&D'!B23 |
| B6 | Year 1 synergies (EBITDA) | ='Inputs_A&D'!B70+'Inputs_A&D'!B72 |
| B7 | Pro forma EBITDA (post-synergy) | =B5+B6 |
| B8 | Existing D&A (acquirer + target) | ='Inputs_A&D'!B7+'Inputs_A&D'!B25 |
| B9 | PPA amortization | ='Inputs_A&D'!B65 |
| B10 | Total D&A | =B8+B9 |
| B11 | Pro forma EBIT | =B7-B10 |
| B12 | Interest: acquirer existing | ='Inputs_A&D'!B9 |
| B13 | Interest: new acquisition debt | ='Inputs_A&D'!B42*'Inputs_A&D'!B43 |
| B14 | Interest: target assumed debt | ='Inputs_A&D'!B27 |
| B15 | Total pro forma interest | =B12+B13+B14 |
| B16 | Pre-tax income (recurring) | =B11-B15 |
| B17 | Transaction costs (one-time) | ='Inputs_A&D'!B40 |
| B18 | Pre-tax income (GAAP) | =B16-B17 |
| B19 | Tax expense (25%) | =B18*'Inputs_A&D'!B11 |
| B20 | Net income (GAAP) | =B18-B19 |
| B22 | Pro forma shares (M) | ='Inputs_A&D'!B47 |
| B23 | GAAP EPS | =B20/B22 |
| B25 | Standalone EPS (reference) | ='Inputs_A&D'!B15 |
| B26 | GAAP accretion / (dilution) | =(B23-B25)/B25 |
| B28 | Adjusted EBIT (add back PPA amort) | =B11+B9 |
| B29 | Adjusted pre-tax income | =B28-B15 |
| B30 | Adjusted tax expense | =B29*'Inputs_A&D'!B11 |
| B31 | Adjusted net income (cash) | =B29-B30 |
| B32 | Cash EPS | =B31/B22 |
| B33 | Cash accretion / (dilution) | =(B32-B25)/B25 |

When you enter these formulas, the model produces the following results. Pro forma revenue is $2,810 million ($2,000M acquirer plus $800M target plus $10M of Year 1 revenue synergies at 50% realization). Pro forma EBITDA post-synergy is $625 million. Total D&A of $173.1 million combines $120 million of existing depreciation ($80M acquirer plus $40M target) with $53.1 million of PPA amortization. Pro forma EBIT is $451.9 million. Total interest expense of $93 million combines the acquirer's existing $40 million, $33 million on the new $600 million acquisition debt at 5.5%, and $20 million on the target's assumed $400 million debt at 5.0%. Recurring pre-tax income is $358.9 million; after $40 million of transaction costs, GAAP pre-tax income falls to $318.9 million. At a 25% tax rate, GAAP net income is $239.2 million. Divided by 113.889 million pro forma shares, GAAP EPS equals $2.100. Against the standalone $2.40, the deal is 12.5% GAAP-dilutive.

The cash EPS calculation tells a different story. Adding back the $53.1 million of PPA amortization to EBIT produces adjusted EBIT of $505 million. After $93 million of interest and $103 million of tax, adjusted net income is $309 million. Cash EPS equals $2.713, which is 13.0% accretive to the standalone $2.40. The entire gap between GAAP dilution and cash accretion stems from the non-cash PPA amortization of $53.1 million and the one-time transaction costs of $40 million. This divergence is the single most important analytical output of the exercise, because it determines whether the board should evaluate the deal on a GAAP basis (where it looks value-destructive) or on a cash basis (where it looks value-creating). The answer depends on the board's view of whether PPA amortization represents a real economic cost or an accounting convention. In practice, most corporate development teams present both metrics and let the compensation committee determine which governs the acquirer's internal EPS targets.

### 1.4 Verification Against Analytical Benchmarks

Before proceeding to the sensitivity analysis, verify the model against two hand-computed benchmarks. First, confirm that the sources and uses reconcile: total uses equal $1,290 million ($1,250M equity purchase price plus $40M transaction costs), and total sources equal $1,290 million ($600M debt plus $190M cash plus $500M stock). Second, confirm the PPA goodwill calculation: purchase consideration of $1,600 million minus net identifiable assets at fair value of $820 million equals goodwill of $780 million. If either check fails, trace the formula references back to the inputs sheet and correct the cell mapping.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### 2.1 Building the LBO Debt Waterfall

The leveraged buyout model shifts the analytical lens from the strategic acquirer to a financial sponsor. The sponsor's objective is not operational integration but returns optimization: structure the capital stack to maximize IRR and MOIC over a five-year holding period while maintaining covenant compliance. The debt waterfall is the mechanical core of the model, tracking each tranche's balance, interest accrual, and amortization schedule year by year.

On the `LBO_Model` worksheet, set up a columnar layout with Year 0 (LTM) in column B and Years 1 through 5 in columns C through G. Enter the operating assumptions in rows 4 through 10, the debt schedules in rows 12 through 40, the free cash flow calculation in rows 42 through 56, and the exit and returns analysis in rows 58 through 72.

The LBO transaction terms differ from the strategic deal because the sponsor refinances the target's existing debt rather than assuming it. Total uses are $1,690 million: $1,250 million equity purchase price, $400 million to refinance target debt, and $40 million transaction costs. The capital stack comprises a $150 million Term Loan A at 8.0% with $30 million annual amortization (5-year straight-line), a $450 million Term Loan B at 9.0% with $22.5 million annual amortization (5% of original balance per year), $100 million of mezzanine debt at 12.0% PIK (interest compounds into principal), and $940 million of sponsor equity. Target cash of $50 million is swept at close and applied as a funding source, bringing total sources to $1,690 million.

| Cell | Label | Year 0 (B) | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|---|
| B4 | Revenue | 800.0 | =B4*1.05 | =C4*1.05 | =D4*1.05 | =E4*1.05 | =F4*1.05 |
| B5 | EBITDA margin | 0.20 | =B5 | =B5 | =B5 | =B5 | =B5 |
| B6 | EBITDA | =B4*B5 | =C4*C5 | =D4*D5 | =E4*E5 | =F4*F5 | =G4*G5 |
| B7 | D&A rate (% rev) | 0.05 | =B7 | =B7 | =B7 | =B7 | =B7 |
| B8 | D&A | =B4*B7 | =C4*C7 | =D4*D7 | =E4*E7 | =F4*F7 | =G4*G7 |
| B9 | EBIT | =B6-B8 | =C6-C8 | =D6-D8 | =E6-E8 | =F6-F8 | =G6-G8 |

The Term Loan A schedule uses beginning balance, mandatory amortization, and ending balance rows. The interest rate sits in a dedicated cell referenced by all years.

| Cell | Label | Year 0 (B) | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|---|
| B12 | TLA interest rate | 0.08 | | | | | |
| B13 | TLA beginning balance | | 150.0 | =C15 | =D15 | =E15 | =F15 |
| B14 | TLA mandatory amort | | -30.0 | -30.0 | -30.0 | -30.0 | -30.0 |
| B15 | TLA ending balance | 150.0 | =C13+C14 | =D13+D14 | =E13+E14 | =F13+F14 | =G13+G14 |
| B16 | TLA interest expense | | =C13*$B$12 | =D13*$B$12 | =E13*$B$12 | =F13*$B$12 | =G13*$B$12 |

| Cell | Label | Year 0 (B) | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|---|
| B18 | TLB interest rate | 0.09 | | | | | |
| B19 | TLB beginning balance | | 450.0 | =C21 | =D21 | =E21 | =F21 |
| B20 | TLB mandatory amort | | -22.5 | -22.5 | -22.5 | -22.5 | -22.5 |
| B21 | TLB ending balance | 450.0 | =C19+C20 | =D19+D20 | =E19+E20 | =F19+F20 | =G19+G20 |
| B22 | TLB interest expense | | =C19*$B$18 | =D19*$B$18 | =E19*$B$18 | =F19*$B$18 | =G19*$B$18 |

The mezzanine tranche compounds interest into principal rather than paying cash, which means the balance grows over the holding period. This PIK structure defers cash interest expense but increases the debt balance that must be repaid at exit.

| Cell | Label | Year 0 (B) | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|---|
| B24 | Mezz interest rate (PIK) | 0.12 | | | | | |
| B25 | Mezz beginning balance | | 100.0 | =C27 | =D27 | =E27 | =F27 |
| B26 | Mezz PIK interest | | =C25*$B$24 | =D25*$B$24 | =E25*$B$24 | =F25*$B$24 | =G25*$B$24 |
| B27 | Mezz ending balance | 100.0 | =C25+C26 | =D25+D26 | =E25+E26 | =F25+F26 | =G25+G26 |

The free cash flow calculation follows the standard LBO waterfall: EBIT minus cash interest equals pre-tax income, less taxes equals net income, plus D&A, minus capital expenditures, minus the change in net working capital, minus mandatory debt amortization. The residual is the cash available for optional debt paydown or accumulation on the balance sheet. CapEx is set at 4% of revenue and the NWC change at 10% of the change in revenue.

| Cell | Label | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|
| C30 | EBIT | =C9 | =D9 | =E9 | =F9 | =G9 |
| C31 | Cash interest (TLA + TLB) | =C16+C22 | =D16+D22 | =E16+E22 | =F16+F22 | =G16+G22 |
| C32 | Pre-tax income | =C30-C31 | =D30-D31 | =E30-E31 | =F30-F31 | =G30-G31 |
| C33 | Tax (25%) | =C32*0.25 | =D32*0.25 | =E32*0.25 | =F32*0.25 | =G32*0.25 |
| C34 | Net income | =C32-C33 | =D32-D33 | =E32-E33 | =F32-F33 | =G32-G33 |
| C35 | D&A | =C8 | =D8 | =E8 | =F8 | =G8 |
| C36 | CapEx (4% of revenue) | =C4*0.04 | =D4*0.04 | =E4*0.04 | =F4*0.04 | =G4*0.04 |
| C37 | Change in NWC (10% of Δrev) | =(C4-B4)*0.10 | =(D4-C4)*0.10 | =(E4-D4)*0.10 | =(F4-E4)*0.10 | =(G4-F4)*0.10 |
| C38 | TLA mandatory amort | 30.0 | 30.0 | 30.0 | 30.0 | 30.0 |
| C39 | TLB mandatory amort | 22.5 | 22.5 | 22.5 | 22.5 | 22.5 |
| C40 | Free cash flow | =C34+C35-C36-C37-C38-C39 | =D34+D35-D36-D37-D38-D39 | =E34+E35-E36-E37-E38-E39 | =F34+F35-F36-F37-F38-F39 | =G34+G35-G36-G37-G38-G39 |

The cash balance accumulates FCF each year, starting from $0 (target cash was swept at close).

| Cell | Label | Year 0 (B) | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|---|
| B43 | Beginning cash | | 0.0 | =C45 | =D45 | =E45 | =F45 |
| B44 | Free cash flow | | =C40 | =D40 | =E40 | =F40 | =G40 |
| B45 | Ending cash | 0.0 | =C43+C44 | =D43+D44 | =E43+E44 | =F43+F44 | =G43+G44 |

The exit valuation and returns analysis complete the model. The exit assumes the sponsor sells the company at Year 5 at a multiple of Year 5 EBITDA, and the exit equity value equals exit enterprise value minus total debt plus accumulated cash.

| Cell | Label | Value or Formula |
|---|---|---|
| B48 | Exit EBITDA (Year 5) | =G6 |
| B49 | Exit multiple | 10.0 |
| B50 | Exit enterprise value | =B48*B49 |
| B51 | TLA ending balance (Year 5) | =G15 |
| B52 | TLB ending balance (Year 5) | =G21 |
| B53 | Mezz ending balance (Year 5) | =G27 |
| B54 | Total debt at exit | =B51+B52+B53 |
| B55 | Cash at exit | =G45 |
| B56 | Net debt at exit | =B54-B55 |
| B57 | Exit equity value | =B50-B56 |
| B59 | Sponsor equity invested (Year 0) | 940.0 |
| B60 | MOIC | =B57/B59 |
| B61 | IRR | =(B57/B59)^(1/5)-1 |

When you complete the model, the base case produces the following trajectory. Revenue grows from $800 million to $1,021 million over five years at 5% annual growth. EBITDA grows from $160 million to $204.2 million at a constant 20% margin. The Term Loan A amortizes to zero by Year 5. The Term Loan B declines from $450 million to $337.5 million. The mezzanine balance compounds from $100 million to $176.2 million through PIK accrual. Free cash flow grows from $7.0 million in Year 1 to $41.6 million in Year 5 as interest expense declines with debt paydown. Cumulative cash accumulation reaches $120.3 million. At a 10.0x exit multiple, the exit enterprise value is $2,042 million. Net debt at exit is $393.4 million ($513.7M total debt minus $120.3M cash). Exit equity value is $1,648.6 million. The MOIC is 1.754x and the IRR is 11.9%.

### 2.2 Sensitivity Analysis: Exit Multiple and Margin Expansion

The base case IRR of 11.9% falls below the typical institutional sponsor return threshold of 15 to 20%. The sensitivity analysis identifies which operational and market levers can close that gap. The two most powerful drivers are the exit multiple and the Year 5 EBITDA margin, because both compound through the enterprise value calculation. To build a two-dimensional Data Table in Excel, place the IRR formula cell reference in the top-left corner of a blank range on the `Sensitivity` sheet, enter exit multiples (9.0, 9.5, 10.0, 10.5, 11.0, 12.0) across the top row, enter Year 5 EBITDA margins (19.0%, 20.0%, 21.0%, 22.0%, 23.0%, 24.0%, 25.0%) down the left column, then select the range and navigate to Data > What-If Analysis > Data Table. Set the row input cell to the exit multiple input cell on the LBO sheet and the column input cell to the Year 5 EBITDA margin assumption. Excel iterates the model across all 42 combinations and populates the table.

The following table presents the IRR results for the key intersection points. The margins represent the Year 5 exit margin, achieved through a linear ramp from the 20% base. Each margin level changes EBITDA in every projection year, which cascades through the FCF calculation, the debt paydown capacity, the cash accumulation, and ultimately the exit equity value.

| Year 5 Margin | 9.0x | 9.5x | 10.0x | 10.5x | 11.0x | 12.0x |
|---|---|---|---|---|---|---|
| 20.0% | 8.9% | 10.4% | 11.9% | 13.3% | 14.5% | 17.0% |
| 22.0% | 12.2% | 13.6% | 15.1% | 16.4% | 17.7% | 20.1% |
| 25.0% | 16.5% | 17.9% | 19.3% | 20.7% | 21.9% | 24.2% |

The base case sits at the intersection of 10.0x exit and 20.0% margin, producing 11.9%. To reach a 20% IRR, the sponsor needs either a 12.0x exit at flat margins or a 25.0% exit margin at a 10.0x exit multiple. A 22.0% margin combined with an 11.0x exit yields 17.7%, which approaches the institutional threshold. The table reveals that margin expansion is the more powerful lever at lower exit multiples, because each percentage point of margin improvement increases EBITDA directly, which both increases FCF for debt paydown and increases the exit enterprise value. Multiple expansion is more powerful at higher margin levels because the absolute dollar increase in enterprise value from each turn of multiple is larger when EBITDA is higher.

### 2.3 Returns Attribution

Returns attribution decomposes the total value creation into its constituent drivers so the sponsor can identify whether returns come from operational improvement, market timing, or financial engineering. The decomposition formula isolates three components: EBITDA growth (the change in EBITDA multiplied by the entry multiple), multiple expansion (exit EBITDA multiplied by the change in multiple), and net debt reduction (the difference between entry and exit net debt). Transaction costs represent a fourth component that reduces value.

On the `LBO_Model` sheet, enter the attribution schedule in rows 64 through 72.

| Cell | Label | Formula |
|---|---|---|
| B64 | Entry EBITDA | =B6 |
| B65 | Exit EBITDA | =G6 |
| B66 | EBITDA change | =B65-B64 |
| B67 | Entry multiple | =B49 |
| B68 | Exit multiple | =B49 |
| B69 | Value from EBITDA growth | =B66*B67 |
| B70 | Value from multiple expansion | =B65*(B68-B67) |
| B71 | Value from debt paydown | =(700.0-B56) |
| B72 | Less: transaction costs | -40.0 |
| B73 | Total value creation | =B69+B70+B71+B72 |
| B74 | Total value creation (check) | =B57-B59 |

The base case attribution shows $442.1 million of value from EBITDA growth ($44.2 million of EBITDA expansion multiplied by the 10.0x entry multiple), zero from multiple expansion (entry and exit multiples are identical at 10.0x), $306.6 million from net debt reduction ($700.0M entry net debt minus $393.4M exit net debt), and negative $40.0 million from transaction costs. The total value creation of $708.6 million reconciles to the difference between exit equity ($1,648.6M) and initial equity ($940.0M). EBITDA growth contributes 62.4% of value creation, debt paydown contributes 43.3%, and transaction costs consume 5.6%. The negative multiple expansion component reflects the base case assumption that the sponsor exits at the same multiple as entry. In practice, sponsor returns typically require at least one of multiple expansion or margin expansion to exceed institutional thresholds, because debt paydown alone is mathematically capped by the initial leverage.

### 2.4 Accretion/Dilution Sensitivity: Purchase Multiple and Financing Mix

Return to the `A&D_Model` sheet to build a parallel sensitivity for the strategic acquirer. The two-variable Data Table varies the purchase multiple (rows: 6.0x, 8.0x, 10.0x, 12.0x) against the stock financing percentage (columns: 0%, 25%, 50%, 75%, 100%), where stock percentage is defined as the proportion of total funding (after acquirer cash) raised through equity issuance. The table output is the GAAP accretion/dilution percentage.

| Purchase Multiple | 0% Stock | 25% Stock | 50% Stock | 75% Stock | 100% Stock |
|---|---|---|---|---|---|
| 6.0x | +2.1% | +0.8% | -0.3% | -1.5% | -2.5% |
| 8.0x | -3.4% | -5.2% | -6.8% | -8.3% | -9.6% |
| 10.0x | -8.9% | -11.0% | -12.8% | -14.4% | -15.8% |
| 12.0x | -14.4% | -16.6% | -18.3% | -19.8% | -21.2% |

The GAAP table shows that the deal is dilutive at every combination above 6.0x, and that increasing the stock component worsens dilution because the acquirer's 15.0x P/E is below the effective earnings yield of the target at any purchase multiple above 6.0x. The cash EPS sensitivity tells a different story.

| Purchase Multiple | 0% Stock | 25% Stock | 50% Stock | 75% Stock | 100% Stock |
|---|---|---|---|---|---|
| 6.0x | +31.2% | +29.0% | +27.0% | +25.1% | +23.3% |
| 8.0x | +25.7% | +22.4% | +19.4% | +16.7% | +14.3% |
| 10.0x | +20.2% | +16.0% | +12.5% | +9.3% | +6.5% |
| 12.0x | +14.7% | +9.9% | +5.9% | +2.6% | -0.3% |

On a cash basis, the deal is accretive at every combination up to 10.0x regardless of financing mix, and remains accretive at 12.0x as long as the stock component stays below 75%. The divergence between the GAAP and cash tables quantifies the PPA amortization effect: at 10.0x with 50% stock, the GAAP dilution of 12.8% and the cash accretion of 12.5% differ by 25.3 percentage points, which corresponds to the after-tax PPA amortization per share ($53.1M times 0.75 divided by 115.3 million shares equals $0.345 per share, which against $2.40 standalone EPS represents a 14.4% drag) plus the after-tax transaction cost per share ($40M times 0.75 divided by 115.3 million shares equals $0.260 per share, representing a 10.8% one-time drag).

To find the exact breakeven purchase multiple where the deal flips from accretive to dilutive on a cash basis at a given financing mix, use Excel's Goal Seek function. Set the target cell to the cash accretion/dilution percentage, set the target value to zero, and set the changing cell to the purchase multiple input. At 50% stock, Goal Seek returns a breakeven multiple of approximately 11.4x. At 100% stock, the breakeven drops to 11.9x, reflecting the higher cost of equity financing relative to debt at the acquirer's 15.0x P/E.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### 3.1 Downside Scenario Construction

The stress test models a combined downside scenario in which three adverse conditions hit simultaneously: revenue contracts by 5% per year instead of growing 5%, the EBITDA margin compresses from 20% to 17%, and interest rates rise 200 basis points across all debt tranches. This scenario is not a probabilistic forecast but a boundary test designed to answer whether the capital structure survives a severe but plausible deterioration in operating conditions.

On the `Stress_Test` worksheet, replicate the LBO model structure but override three input cells. Set the revenue growth rate in the Year 1 formula to `=B4*0.95` and propagate the 0.95 multiplier across all years. Set the EBITDA margin to 0.17. Set the Term Loan A rate to 0.10, the Term Loan B rate to 0.11, and the revolver rate to 0.105 (SOFR at 7% plus 350 basis points). Also add a $50 million undrawn revolver facility in rows 48 through 52, which the model draws automatically when FCF turns negative.

| Cell | Label | Year 0 (B) | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|---|
| B4 | Revenue (stress) | 800.0 | =B4*0.95 | =C4*0.95 | =D4*0.95 | =E4*0.95 | =F4*0.95 |
| B5 | EBITDA margin (stress) | 0.17 | =B5 | =B5 | =B5 | =B5 | =B5 |
| B6 | EBITDA (stress) | =B4*B5 | =C4*C5 | =D4*D5 | =E4*E5 | =F4*F5 | =G4*G5 |

Under the stress scenario, Year 1 revenue falls to $760 million, EBITDA compresses to $129.2 million, and the EBIT drops to $91.2 million after $38 million of D&A. Cash interest expense of $64.5 million (TLA $15M at 10% plus TLB $49.5M at 11%) consumes 50% of EBITDA, leaving pre-tax income of only $26.7 million. After tax of $6.7 million, net income is $20.0 million. Adding back $38 million of D&A, subtracting $30.4 million of CapEx, adding $4.0 million from NWC release (revenue is declining, so working capital frees up), and subtracting $52.5 million of mandatory amortization produces a free cash flow of negative $20.9 million. The company draws $20.9 million on the revolver to cover the shortfall.

In Year 2, revenue falls further to $722 million and EBITDA to $122.7 million. Cash interest increases to $61.2 million because the revolver balance now accrues interest at 10.5%. Pre-tax income falls to $25.4 million. Free cash flow remains negative at negative $22.4 million, and the revolver balance grows to $43.3 million. By Year 3, EBITDA has fallen to $116.3 million and the cumulative cash burn continues.

### 3.2 Covenant Compliance Testing

The LBO credit agreement imposes two maintenance covenants tested at the end of each fiscal year. The leverage covenant requires total debt to EBITDA of no more than 6.0x. The interest coverage covenant requires EBITDA to cash interest of at least 2.0x. Enter the covenant tests on the `Stress_Test` sheet in rows 54 through 60.

| Cell | Label | Year 1 (C) | Year 2 (D) | Year 3 (E) | Year 4 (F) | Year 5 (G) |
|---|---|---|---|---|---|---|
| C54 | Total debt (TLA + TLB + Mezz + Revolver) | =C15+C21+C27+C52 | =D15+D21+D27+D52 | =E15+E21+E27+E52 | =F15+F21+F27+F52 | =G15+G21+G27+G52 |
| C55 | EBITDA | =C6 | =D6 | =E6 | =F6 | =G6 |
| C56 | Leverage ratio | =C54/C55 | =D54/D55 | =E54/E55 | =F54/F55 | =G54/G55 |
| C57 | Leverage covenant threshold | 6.0 | 6.0 | 6.0 | 6.0 | 6.0 |
| C58 | Leverage covenant headroom | =C57-C56 | =D57-D56 | =E57-E56 | =F57-F56 | =G57-G56 |
| C59 | Cash interest coverage | =C55/C31 | =D55/D31 | =E55/E31 | =F55/F31 | =G55/G31 |
| C60 | Coverage covenant threshold | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |

The stress test reveals the covenant breach boundary. In Year 1, the leverage ratio reaches 5.27x ($680.4M total debt including the revolver draw divided by $129.2M EBITDA), which remains below the 6.0x threshold with 0.73x of headroom. The interest coverage ratio sits at exactly 2.00x ($129.2M EBITDA divided by $64.5M cash interest), right at the covenant boundary. In Year 2, the interest coverage ratio drops to 1.94x ($122.7M EBITDA divided by $63.4M cash interest including revolver interest), which breaches the 2.0x minimum. The leverage ratio rises to 5.41x, still below the 6.0x threshold but tightening. By Year 3, with EBITDA falling to $116.3 million and the revolver balance growing, both covenants come under severe pressure.

### 3.3 Boundary Mapping: Revenue Decline and Margin Compression

To map the exact boundary at which each covenant fails, build a two-variable Data Table that varies the revenue growth rate (from positive 5% down to negative 15%) and the EBITDA margin (from 20% down to 13%) against the Year 2 interest coverage ratio, since Year 2 is where the first breach occurs. The following table shows the Year 2 coverage ratio at each combination, with cells in bold representing covenant breaches (below 2.0x).

| EBITDA Margin | +5% Rev Growth | 0% Growth | -5% Growth | -10% Growth | -15% Growth |
|---|---|---|---|---|---|
| 20.0% | 3.20x | 2.66x | 2.21x | 1.85x | 1.55x |
| 18.0% | 2.88x | 2.39x | 1.99x | 1.66x | 1.39x |
| 17.0% | 2.72x | 2.26x | 1.88x | 1.57x | 1.32x |
| 15.0% | 2.40x | 1.99x | 1.66x | 1.38x | 1.16x |
| 13.0% | 2.08x | 1.73x | 1.44x | 1.20x | 1.01x |

The interest coverage covenant holds as long as revenue growth stays above negative 5% at a 20% margin, but it breaches immediately if the margin falls to 17% and revenue is flat. At a 15% margin, the covenant breaches even with positive revenue growth. The leverage covenant is more permissive: it does not breach until revenue declines by more than 10% combined with margin compression below 17%, because the denominator (EBITDA) has to fall dramatically while debt stays high. The coverage covenant is the binding constraint, which is typical for LBO structures where mandatory amortization is light and interest expense is the primary fixed cost.

### 3.4 Recovery Protocol

When the covenant breaches in Year 2, the sponsor must execute a recovery protocol to return the business to compliance and protect the equity value. The recovery plan combines four levers, each modeled as an override on the `Stress_Test` sheet.

**Lever 1: Operational cost reduction.** Reduce the operating expense base by 10% through headcount reduction and supplier renegotiation, which improves the EBITDA margin from 17.0% to approximately 18.5%. Model this by changing the EBITDA margin input from 0.17 to 0.185. In Year 2, this raises EBITDA from $122.7 million to $133.6 million, which lifts the interest coverage ratio from 1.94x to 2.11x, clearing the covenant threshold. The cost reduction is assumed to require $15 million of one-time severance and restructuring costs in Year 1, modeled as a deduction from EBITDA in that year only.

**Lever 2: CapEx deferral.** Reduce the CapEx rate from 4% of revenue to 2%, which is the maintenance floor. In Year 2, this frees $14.5 million of cash flow ($28.9M original CapEx minus $14.4M reduced CapEx). Combined with the cost reduction, Year 2 FCF improves from negative $22.4 million to approximately $0.2 million, essentially breakeven. The CapEx deferral risks underinvestment in the asset base, so the model should track the cumulative deferred CapEx as a liability that the sponsor must fund before exit.

**Lever 3: Asset sale and debt paydown.** Identify $50 million of non-core assets that can be sold at the end of Year 2 at a 6.0x EBITDA multiple (assuming the divested assets generate $8.3 million of EBITDA). The proceeds are applied to optional Term Loan B paydown, reducing the TLB balance from $405 million to $355 million. This reduces Year 3 interest expense by $4.95 million ($55M at 9.0% in the base stress, minus $4.95M after paydown), which further improves the coverage ratio in subsequent years.

**Lever 4: Sponsor equity cure.** If the operational and portfolio actions are insufficient, the sponsor injects $50 million of additional equity at the end of Year 2 to pay down the revolver balance and eliminate the revolver interest expense. This is the most dilutive action for the sponsor's IRR because it increases the equity basis from $940 million to $990 million without increasing the exit value proportionally. The IRR impact depends on the exit multiple: at 10.0x, the $50 million equity cure reduces the IRR by approximately 1.5 percentage points, from 11.9% to 10.4% in the base case.

To model the full recovery scenario, apply Levers 1 and 2 simultaneously and recalculate the covenant tests. Year 2 EBITDA rises to $133.6 million, cash interest remains at $63.4 million (the revolver balance is unchanged because the recovery actions take effect at the start of Year 2), and the coverage ratio improves to 2.11x, which clears the 2.0x covenant. Year 2 FCF improves to $0.2 million, which stops the revolver draw from growing. In Year 3, the lower CapEx rate and improved margin generate positive FCF of $8.4 million, which begins to pay down the revolver. By Year 4, the revolver is fully repaid and the company returns to mandatory amortization on the Term Loans. The recovery protocol successfully stabilizes the capital structure without requiring a sponsor equity cure, preserving the original $940 million equity basis.

The table below summarizes the covenant metrics under the base case, the stress case, and the recovery scenario for Year 2, the breach year.

| Metric | Base Case (Y2) | Stress Case (Y2) | Recovery (Y2) |
|---|---|---|---|
| Revenue | $882.0M | $722.0M | $722.0M |
| EBITDA margin | 20.0% | 17.0% | 18.5% |
| EBITDA | $176.4M | $122.7M | $133.6M |
| Cash interest | $48.1M | $63.4M | $63.4M |
| Interest coverage | 3.67x | 1.94x | 2.11x |
| Total debt | $659.5M | $663.7M | $663.7M |
| Leverage ratio | 3.74x | 5.41x | 4.97x |
| Free cash flow | $15.3M | -$22.4M | $0.2M |
| Covenant status | Compliant | Breached | Compliant |

---

## Operational Reference Guide & Diagnostic Checklist

### Accretion/Dilution Model Diagnostic Checklist

Run through the following verification sequence after completing or modifying the accretion/dilution model. Each check isolates a specific mechanical error that practitioners encounter in live deal modeling.

**Sources and uses reconciliation.** Confirm that total sources equal total uses by summing the new debt, acquirer cash, and stock issued values and comparing to the equity purchase price plus transaction costs. If the two do not match, the stock issuance formula is incorrect or the acquirer cash input is wrong. The stock issued value cell should contain the formula `=Total_Funding - New_Debt - Acquirer_Cash`, and the stock issued shares cell should divide this by the acquirer share price.

**PPA goodwill sanity check.** Goodwill must be non-negative. If the formula produces a negative value, the net identifiable assets at fair value exceed the purchase consideration, which means either the purchase multiple is too low or the intangible step-ups are too high relative to the deal price. In practice, this occurs when the acquirer buys a distressed asset at below replacement cost, and the accounting treatment requires recording a bargain purchase gain rather than goodwill.

**PPA amortization tie-out.** Sum the individual amortization lines and confirm they match the total. The PP&E step-up amortization equals the step-up divided by 15 years ($100M / 15 = $6.667M). The customer relationship amortization equals $250M / 10 = $25.0M. The technology amortization equals $150M / 7 = $21.429M. The total of $53.095M should match the PPA amortization input to the pro forma income statement. A common error is to include the inventory step-up in the annual amortization; the inventory step-up flows through COGS in Year 1 only, not through the amortization line.

**Pro forma interest expense reconciliation.** Confirm that total pro forma interest equals the sum of the acquirer's existing interest, the new debt interest (new debt multiplied by the new debt rate), and the target's assumed debt interest. A common error is to double-count the target's interest by including both the target's standalone interest and the assumed debt interest; the target's standalone interest expense already reflects the debt being assumed, so the model should include only the assumed debt interest, not the target's standalone interest line.

**GAAP-to-cash EPS bridge.** The difference between GAAP EPS and cash EPS should equal the after-tax PPA amortization per share plus the after-tax transaction cost per share. Verify: PPA amortization of $53.095M times (1 - 0.25) divided by 113.889M shares equals $0.349 per share. Transaction costs of $40M times (1 - 0.25) divided by 113.889M shares equals $0.263 per share. Total bridge: $0.612 per share. GAAP EPS of $2.100 plus $0.612 equals $2.712, which should match the cash EPS of $2.713 (rounding difference of $0.001).

### LBO Model Diagnostic Checklist

**Debt waterfall integrity.** Each tranche's ending balance must equal the beginning balance plus amortization (a negative number) plus any draws or repayments. For the Term Loan A, the ending balance in Year 5 must be zero (fully amortized). For the Term Loan B, the ending balance in Year 5 must equal the original balance minus cumulative amortization ($450M minus 5 times $22.5M equals $337.5M). For the mezzanine, the ending balance must equal the original balance plus cumulative PIK interest. If any tranche's ending balance does not match, trace the amortization formula and confirm that the beginning balance references the prior year's ending balance, not the original balance.

**PIK interest calculation.** The mezzanine PIK interest in each year must equal the beginning balance multiplied by the PIK rate. A common error is to calculate PIK interest on the original balance rather than the beginning balance, which understates the interest accrual as the balance compounds. Verify Year 2: beginning balance of $112M times 12% equals $13.44M, which matches the PIK interest formula. The ending balance of $125.44M should equal the beginning balance plus the PIK interest ($112M plus $13.44M).

**FCF sign convention.** All outflows in the FCF calculation should be negative: CapEx, change in NWC (when revenue is growing), and mandatory amortization. D&A is added back as a positive number. If FCF is consistently negative in the base case with positive revenue growth and stable margins, the most likely cause is that mandatory amortization exceeds the company's debt service capacity, which means the capital structure is too aggressively amortizing for the cash flow profile.

**Exit equity reconciliation.** Exit equity value must equal exit enterprise value minus total debt at exit plus cash at exit. Total debt at exit includes all tranches: Term Loan A ending balance, Term Loan B ending balance, and mezzanine ending balance. If the revolver has been drawn, include the revolver balance. Cash at exit is the cumulative FCF from all years, not just the Year 5 FCF. A common error is to use only the final year's cash balance rather than the cumulative balance.

**Returns attribution reconciliation.** The sum of the four attribution components (EBITDA growth, multiple expansion, debt paydown, and transaction costs) must equal the difference between exit equity and initial equity. If the attribution does not reconcile, the most common cause is an incorrect entry net debt figure. Entry net debt should be the total debt at close (TLA plus TLB plus mezzanine) minus the target cash that was swept at close ($700M minus $50M equals $650M). If the model uses a different entry net debt figure, the debt paydown component will be misstated.

### Stress Test Diagnostic Checklist

**Covenant formula verification.** The leverage ratio must use total debt including the revolver balance, not just the Term Loans and mezzanine. The interest coverage ratio must use cash interest only (TLA interest plus TLB interest plus revolver interest), not total interest including PIK. PIK interest does not require a cash payment, so it does not affect the coverage ratio. A common error is to include the mezzanine PIK interest in the coverage calculation, which understates the ratio and triggers false covenant breaches.

**Revolver draw logic.** The revolver should only be drawn when FCF is negative, and the draw amount should equal the FCF shortfall. The revolver balance should accumulate across years and accrue interest at the revolver rate. If the model shows a revolver balance in the base case (positive FCF scenario), the draw logic is incorrect. The revolver formula should be `=MAX(0, -FCF)` in each year, added to the prior year's balance.

**Recovery scenario isolation.** When modeling the recovery protocol, apply only the specific levers being tested and confirm that all other inputs remain at stress levels. A common error is to inadvertently restore the base case revenue growth or margin when modifying the recovery inputs, which overstates the recovery effect. Use a separate worksheet column for each recovery scenario so that the stress case and recovery case can be compared side by side without overwriting formulas.

**Equity cure IRR impact.** When modeling a sponsor equity cure, increase the initial equity investment by the cure amount and recalculate the IRR. The exit equity value does not change (the cure pays down debt, which reduces net debt at exit, but the equity cure itself
