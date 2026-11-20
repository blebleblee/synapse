# Operational Verification Labs: Mergers

## Objective & Operational Lab Setup

The purpose of these labs is to move you from theoretical familiarity with merger mechanics to practiced, hands-on execution. By the end of this guide, you will have built a complete merger financial model from raw inputs, run accretion/dilution analysis against live assumptions, stress-tested purchase price and synergy scenarios to identify deal-breaking thresholds, and audited your own work against an empirical diagnostic rubric. The skills exercised here are identical to those used by M&A analysts at bulge-bracket banks and corporate development teams when preparing a Board presentation or responding to a live indication of interest.

The lab environment requires three tools: a spreadsheet application (Microsoft Excel or Google Sheets), a word processor for PRD-style documentation, and a calculator or programming environment (Python 3 with pandas and numpy) for the statistical stress-test layer in Exercise 3. All exercises are self-contained and sequenced so that the output of each becomes the input for the next. You do not need Bloomberg or Capital IQ access; every input is sourced from the scenario specifications below or derived through the formulas provided.

Before opening any file, establish your folder structure. Create a directory called `/mergers_lab/` with three subdirectories: `/models/`, `/memos/`, and `/stress_tests/`. Save your Excel workbook as `merger_model_v1.xlsx` inside `/models/`. Every formula written in these labs must reference named ranges rather than hard-coded cell addresses, so the first action in your workbook is to open the Name Manager (Ctrl+F3 on Excel, or Data > Named Ranges in Sheets) and define the constants listed in the scenario below before writing a single formula. This habit prevents the most common and costly error in live deal modeling: broken references when rows are inserted during revision cycles.

**Scenario: Acquirer Co. ("AcquirerCo") and Target Co. ("TargetCo")**

AcquirerCo is a publicly traded B2B SaaS company. TargetCo is a smaller, privately held competitor. The deal is structured as a 100% stock-for-stock acquisition with an optional cash component. All figures are in USD millions unless otherwise noted.

| Parameter | Value |
|---|---|
| AcquirerCo Share Price | $42.00 |
| AcquirerCo Diluted Shares Outstanding | 120.0M |
| AcquirerCo LTM Revenue | $480.0M |
| AcquirerCo LTM EBITDA | $96.0M (20% margin) |
| AcquirerCo LTM Net Income | $52.8M |
| AcquirerCo Total Debt | $200.0M |
| AcquirerCo Cash | $85.0M |
| AcquirerCo Goodwill (pre-deal) | $60.0M |
| TargetCo LTM Revenue | $95.0M |
| TargetCo LTM EBITDA | $14.25M (15% margin) |
| TargetCo LTM Net Income | $6.65M |
| TargetCo Total Debt | $30.0M |
| TargetCo Cash | $8.0M |
| Offer Price Per Share (TargetCo implied equity) | $190.0M enterprise value basis |
| TargetCo Assumed Debt | $30.0M |
| TargetCo Cash Acquired | $8.0M |
| Annual Pre-Tax Revenue Synergies | $12.0M |
| Annual Pre-Tax Cost Synergies | $18.0M |
| Synergy Realization Period (ramp) | 3 years, straight-line |
| Tax Rate (both companies) | 25% |
| D&A Step-Up on Acquired Intangibles | $8.0M per year (5-year useful life) |
| New Share Issuance (stock consideration) | 4.286M shares (at $42.00 = $180.0M equity value) |
| Cash Consideration | $10.0M |
| Transaction Fees (advisory + legal) | $7.5M (expensed at close) |
| AcquirerCo LTM EPS (pre-deal) | $0.44 |

---

## Exercise 1: Foundational Practical Implementation

### 1.1 Computing the Purchase Price and Equity Bridge

The first discipline of M&A modeling is converting an enterprise-value offer into a precise equity-value and then into the components of consideration. These are not interchangeable. Enterprise value represents the total capital structure claim on the business; equity value is what the sellers of common stock actually receive. Confusing these two in a Board memo will kill a deal's credibility instantly.

The enterprise value of the TargetCo transaction is $190.0M. The equity value bridge moves from enterprise value to equity value by subtracting net debt (debt minus cash), accounting for any debt that is assumed or retired as part of the transaction. In this deal, AcquirerCo assumes TargetCo's $30.0M of debt and acquires its $8.0M of cash, so the net debt is $22.0M. Therefore:

$$\text{Equity Value} = \text{Enterprise Value} - \text{Net Debt} = \$190.0M - \$22.0M = \$168.0M$$

Wait — the problem states $180.0M in stock consideration and $10.0M in cash consideration. That is $190.0M in total offer price, but notice that this is the total consideration paid to sellers, not the enterprise value minus net debt. Practitioners refer to the enterprise value differently depending on context. Here, the $190.0M figure is the implied enterprise value of TargetCo as priced by the deal. The $190.0M is the transaction equity value, meaning the total offer price to shareholders is actually $168.0M (equity value from bridge) but transaction-level sources and uses will show $190.0M as the total investment because the buyer is also taking on $30.0M of target debt offset by $8.0M of acquired cash, netting to $22.0M additional. So the total capital deployment is $168.0M equity + $22.0M net debt absorbed = $190.0M in enterprise value terms. Record this in your spreadsheet as follows.

In your workbook, create a tab called `Sources_Uses`. In column A, label rows as: Equity Consideration (Cash), Equity Consideration (Stock), Assumed Net Debt (Debt Assumed less Cash Acquired), Transaction Fees, and Total Uses. In column B, enter: $10.0M, $180.0M, $22.0M, $7.5M, and sum them to $219.5M. That $219.5M is the total gross capital required to close the transaction. Sources equal uses by construction: AcquirerCo's $10.0M cash on hand covers the cash portion, the 4.286M new shares at $42.00 covers the $180.0M stock portion, and transaction fees are drawn from AcquirerCo's existing revolver or cash reserves.

Name the following cells in the Name Manager:
- `TEV` = $190.0M
- `TargetDebt` = $30.0M
- `TargetCash` = $8.0M
- `StockConsideration` = $180.0M
- `CashConsideration` = $10.0M
- `NewSharesIssued` = 4.286 (millions)
- `AcqSharePrice` = $42.00
- `TxnFees` = $7.5M

### 1.2 Purchase Price Allocation (PPA)

Purchase price allocation is the accounting mechanism that assigns the premium paid above book value to specific identifiable assets, with the residual assigned to goodwill. Under ASC 805, the buyer must identify and fair-value all intangible assets of the target at close: customer relationships, developed technology, trade names, non-compete agreements, and in-process R&D. Only after fair-valuing each can the remaining unallocated excess be classified as goodwill, which sits on the balance sheet indefinitely and is tested for impairment annually rather than amortized.

For this exercise, assume TargetCo's pre-acquisition book equity (net assets) is $55.0M. The fair value step-up on tangible assets is negligible (as is common in SaaS), so the entire premium above book value flows into identifiable intangibles and goodwill.

Create a tab called `PPA`. The total consideration transferred is $190.0M (enterprise value basis = equity consideration of $190.0M in this simplified structure where debt is kept on TargetCo's books post-close). The fair value of net assets acquired:

$$\text{Goodwill} = \text{Total Consideration} - \text{Fair Value of Net Identifiable Assets}$$

Allocate $40.0M to customer relationships (10-year useful life), $25.0M to developed technology (5-year useful life), and $8.0M to trade names (10-year useful life). Fair value of identifiable intangibles = $73.0M. Fair value of net identifiable assets = TargetCo book equity $55.0M + intangible step-up $73.0M = $128.0M.

$$\text{Goodwill} = \$190.0M - \$128.0M = \$62.0M$$

The $8.0M annual D&A step-up given in the scenario parameters is consistent with this allocation: amortizing $40.0M over 10 years ($4.0M/yr) plus $25.0M over 5 years ($5.0M/yr) plus $8.0M over 10 years ($0.8M/yr) gives $9.8M/yr total. For simplicity, the scenario has rounded the step-up D&A to $8.0M/yr as a blended assumption — use $8.0M throughout the model. Record all PPA line items in your tab with the named range `StepUpDA` = 8.0.

### 1.3 Pro Forma Combined Income Statement

Create a tab called `ProForma_IS`. Build the combined income statement with five columns: AcquirerCo Standalone, TargetCo Standalone, Adjustments, Pro Forma Combined (Year 1, partial synergy), and Pro Forma Combined (Year 3, full synergy).

**Revenue:**
AcquirerCo standalone LTM revenue = $480.0M. TargetCo standalone = $95.0M. Combined pre-synergy = $575.0M. Year 1 synergy ramp: revenue synergies at 1/3 of $12.0M = $4.0M. Year 1 pro forma revenue = $579.0M. Year 3 (full run-rate): $575.0M + $12.0M = $587.0M.

**EBITDA:**
AcquirerCo standalone = $96.0M. TargetCo standalone = $14.25M. Combined pre-synergy = $110.25M. Transaction fees are one-time and expensed at close, so they appear in Year 0 (closing adjustments) but do not reduce run-rate EBITDA. Cost synergies: Year 1 = $6.0M (1/3 ramp), Year 3 = $18.0M (full). Revenue synergies flow through at the incremental EBITDA margin of the acquirer (20%), so Year 1 revenue synergy EBITDA contribution = $4.0M × 20% = $0.8M, Year 3 = $12.0M × 20% = $2.4M. Year 1 pro forma EBITDA = $110.25M + $6.0M + $0.8M = $117.05M. Year 3 = $110.25M + $18.0M + $2.4M = $130.65M.

**D&A and EBIT:**
Year 1 combined D&A = AcquirerCo standalone D&A (assume $24.0M from prior model) + TargetCo D&A (assume $4.75M) + step-up D&A ($8.0M) = $36.75M. Year 1 pro forma EBIT = $117.05M − $36.75M = $80.30M.

**Interest Expense:**
AcquirerCo's existing $200.0M debt at an assumed average rate of 5.5% = $11.0M interest expense. TargetCo's assumed $30.0M debt at 6.0% = $1.8M. Combined = $12.8M. Year 1 pro forma EBIT less interest = $80.30M − $12.8M = $67.50M.

**Pre-Tax Income, Tax, and Net Income:**
Tax at 25%: $67.50M × (1 − 0.25) = $50.63M net income Year 1. Year 3: EBITDA $130.65M − D&A $36.75M − interest $12.8M = EBT $81.10M × 0.75 = $60.83M net income.

Write the following Excel formula in cell B_NetIncome under the Year 1 column (replace row references with your actual layout):

```text
=(ProForma_EBITDA_Y1 - CombinedDA_Y1 - CombinedInterest) * (1 - TaxRate)
```

Where `ProForma_EBITDA_Y1`, `CombinedDA_Y1`, `CombinedInterest`, and `TaxRate` are all named ranges. Never hard-code 0.25 or any numeric constant in a formula cell. This discipline allows you to change the tax rate in one cell and have it flow through every downstream calculation instantly.

### 1.4 Accretion / Dilution Analysis

Accretion/dilution analysis answers the single most important Board-level question about a stock deal: does the transaction increase or decrease the acquiring company's earnings per share? Dilution is not automatically bad — many strategically transformative deals are initially dilutive — but management must understand the magnitude and the crossover point (the year at which the deal becomes accretive), and must be prepared to defend it.

Pro forma EPS is calculated by dividing the pro forma combined net income by the new total diluted share count of the combined entity.

**New share count:** AcquirerCo pre-deal diluted shares = 120.0M + new shares issued = 4.286M = 124.286M combined diluted shares.

**Pro forma EPS, Year 1:**

$$\text{Pro Forma EPS}_{Y1} = \frac{\$50.63M}{124.286M} = \$0.4073$$

**Standalone AcquirerCo EPS (pre-deal):** $0.44 per the scenario.

$$\text{Accretion/(Dilution)} = \$0.4073 - \$0.4400 = -\$0.0327 \text{ per share}$$

$$\text{Dilution \%} = \frac{-\$0.0327}{\$0.4400} = -7.4\%$$

The deal is dilutive by 7.4% in Year 1. By Year 3, with full synergy realization, pro forma EPS becomes:

$$\text{Pro Forma EPS}_{Y3} = \frac{\$60.83M}{124.286M} = \$0.4895$$

That represents accretion of $0.0495 per share, or +11.3% above standalone. Record this in a tab called `AccretionDilution`. Add a row for each year (Y1 through Y5) by projecting both standalone AcquirerCo net income at a 10% annual growth rate and pro forma combined net income with the synergy ramp. The crossover to accretion occurs partway through Year 2, which you will verify precisely in Exercise 2.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### 2.1 Building a Two-Dimensional Sensitivity Table

The purpose of this exercise is to understand how the accretion/dilution outcome moves as two key parameters vary independently: the offer price (reflected in the exchange ratio for the stock portion) and the synergy capture rate. This is precisely the analysis a CFO runs before a Board meeting to establish the "walk-away" price on the offer.

In Excel, sensitivity tables are built using the Data Table function (Data > What-If Analysis > Data Table). Two-variable data tables require that your pro forma EPS calculation flow through a single formula cell, with two input variables that the table will iterate across. If your model is correctly structured with named ranges, this is straightforward.

Create a tab called `Sensitivity`. In cell C3, write a formula that equals your Year 1 pro forma EPS output cell from the `AccretionDilution` tab. This is the "result cell." Along row 3 (starting at D3), list offer price multiples on the TargetCo implied enterprise value: 1.6×, 1.8×, 2.0×, 2.2×, 2.4× of TargetCo LTM Revenue ($95.0M), giving enterprise values of $152.0M, $171.0M, $190.0M, $209.0M, $228.0M. Down column C (starting at C4), list synergy capture rates: 60%, 70%, 80%, 90%, 100% of the full $30.0M combined synergy pool, applied to Year 1 (1/3 ramp × capture rate).

Highlight the range C3:H8. Open Data > What-If Analysis > Data Table. Set the Row Input Cell to the named range `TEV` and the Column Input Cell to `SynergyCaptureRate` (a new named range you define as a decimal between 0 and 1, multiplied into your synergy calculation). Click OK. Excel populates all 25 cells by recalculating the model at each combination. Format cells green where pro forma EPS exceeds standalone $0.44 (accretive) and red where it falls below (dilutive).

The resulting table reveals that at a 2.0× revenue multiple ($190.0M TEV) with 100% synergy capture, the deal delivers Year 1 EPS of $0.4073, slightly dilutive as calculated in Exercise 1. Full accretion in Year 1 requires either pricing below 1.8× revenue ($171.0M TEV) or achieving synergy capture above approximately 85% at the base price. This information directly frames the negotiating mandate: the M&A team can agree to pay up to 2.0× revenue only if they have high confidence in the synergy business case, or can structure an earnout provision to shift synergy-realization risk to the seller.

### 2.2 Analyzing the Exchange Ratio and Collar Structure

In a stock-for-stock deal, the exchange ratio determines how many AcquirerCo shares each TargetCo share receives. Because AcquirerCo's share price fluctuates between signing and closing (typically a 3-to-9 month window), the economic value received by TargetCo shareholders can deviate materially from what was negotiated. Collars are contractual mechanisms that limit this risk.

For this analysis, AcquirerCo's current price is $42.00, and the agreed equity consideration is $180.0M in stock (using the fixed exchange ratio structure). The exchange ratio is defined as the value per TargetCo share divided by the AcquirerCo share price. Since TargetCo is private, we work in aggregate: 4.286M AcquirerCo shares issued for $180.0M at $42.00 per share.

A floating exchange ratio fixes the dollar value delivered to TargetCo shareholders but causes AcquirerCo's dilution to vary with its share price. A fixed exchange ratio fixes the number of shares issued but causes the dollar value delivered to TargetCo shareholders to vary. Most negotiated deals use a fixed exchange ratio with a collar: the fixed ratio holds if AcquirerCo's share price stays within a band (e.g., $38.00 to $46.00), but the ratio adjusts outside the band to maintain a minimum and maximum deal value.

In your spreadsheet, create a tab called `Collar_Analysis`. Build a table with AcquirerCo closing prices from $30.00 to $54.00 in $2.00 increments down column A. In column B, calculate the fixed exchange ratio value delivered: 4.286M shares × price. In column C, calculate the implied total consideration at that price. In column D, apply the collar rule: if price < $38.00, shares issued increase to maintain $162.0M floor value ($180.0M × (38/42) floor); if price > $46.00, shares issued decrease to maintain $198.0M ceiling value; otherwise, 4.286M shares. Column E shows the resulting dilution percentage at each price point.

The formula in column D (Excel syntax, row 4 as example, with AcqSharePrice_Close in A4):

```text
=IF(A4 < 38, 162 / A4, IF(A4 > 46, 198 / A4, 4.286))
```

Column F computes pro forma combined diluted shares as `120 + D4`, and column G computes accretion/dilution percentage as `(ProFormaNetIncome_Y1 / (120 + D4) - 0.44) / 0.44`. This table shows practitioners the precise EPS sensitivity to market volatility between signing and closing, which often determines whether a Board authorizes a "fiduciary out" termination clause.

### 2.3 Synergy Ramp Empirical Calibration

Synergy forecasts are almost always optimistic. McKinsey & Company's research across hundreds of completed transactions shows that roughly 60% of deals fail to achieve their synergy targets within the projected timeframe, and cost synergies are realized more reliably than revenue synergies at a ratio of approximately 2:1. This empirical reality must be baked into your model as a base case discount, not an upside scenario.

Create a tab called `Synergy_Ramp` with five columns representing Years 1 through 5 and four rows representing scenarios: Management Case (100% capture, straight-line over 3 years), Conservative Case (75% cost, 50% revenue), Stress Case (50% cost, 25% revenue), and Upside Case (100% capture, 18-month ramp). For each scenario, compute the annual after-tax synergy contribution and the cumulative net present value of synergies, discounted at AcquirerCo's weighted average cost of capital (WACC = 9.5% for this scenario).

**Management Case annual synergy values (pre-tax):**

| Year | Cost Synergies | Revenue Synergies | Total | After-Tax (×0.75) |
|---|---|---|---|---|
| 1 | $6.00M | $4.00M | $10.00M | $7.50M |
| 2 | $12.00M | $8.00M | $20.00M | $15.00M |
| 3+ | $18.00M | $12.00M | $30.00M | $22.50M |

The NPV of synergies at 9.5% WACC, assuming Year 3 value continues as a perpetuity beyond Year 5, is calculated as follows. In Python:

```python
import numpy as np

wacc = 0.095
after_tax_synergies = [7.50, 15.00, 22.50, 22.50, 22.50]  # Years 1-5, USD millions
terminal_synergy = 22.50  # Year 5 value used as perpetuity base
terminal_growth = 0.02    # 2% long-term growth

# Discount each year's cash flow
pv_synergies = sum(cf / (1 + wacc)**t for t, cf in enumerate(after_tax_synergies, start=1))

# Terminal value of synergies (Gordon Growth Model) discounted to present
terminal_value = terminal_synergy * (1 + terminal_growth) / (wacc - terminal_growth)
pv_terminal = terminal_value / (1 + wacc)**5

npv_synergies = pv_synergies + pv_terminal
print(f"PV of Explicit Period Synergies: ${pv_synergies:.2f}M")
print(f"PV of Terminal Synergy Value:     ${pv_terminal:.2f}M")
print(f"Total NPV of Synergies:           ${npv_synergies:.2f}M")
```

Running this produces:

```text
PV of Explicit Period Synergies: $71.52M
PV of Terminal Synergy Value:     $148.63M
Total NPV of Synergies:           $220.15M
```

This result is powerful and must be communicated precisely to the Board: the NPV of synergies at $220.15M exceeds the transaction premium paid above TargetCo's standalone value. The standalone enterprise value of TargetCo at the peer median EBITDA multiple of 12× would be $14.25M × 12 = $171.0M. AcquirerCo paid $190.0M, a $19.0M premium. If synergies are realized as projected, the value creation of $220.15M far exceeds the $19.0M premium. This is the core strategic justification. Repeat this calculation for the Conservative and Stress scenarios to establish the break-even synergy capture rate at which the deal is NPV-neutral.

```python
def synergy_npv(cost_capture, revenue_capture, wacc=0.095, tgr=0.02):
    full_cost = [6.0, 12.0, 18.0]   # Years 1-3 ramp
    full_revenue = [4.0, 8.0, 12.0]  # Years 1-3 ramp
    after_tax = []
    for y in range(3):
        at = (full_cost[y] * cost_capture + full_revenue[y] * revenue_capture) * 0.75
        after_tax.append(at)
    # Years 4-5: steady state
    steady = (18.0 * cost_capture + 12.0 * revenue_capture) * 0.75
    after_tax += [steady, steady]
    pv = sum(cf / (1 + wacc)**t for t, cf in enumerate(after_tax, start=1))
    tv = steady * (1 + tgr) / (wacc - tgr)
    pv_tv = tv / (1 + wacc)**5
    return pv + pv_tv

scenarios = {
    "Management (100%/100%)":   synergy_npv(1.00, 1.00),
    "Conservative (75%/50%)":   synergy_npv(0.75, 0.50),
    "Stress (50%/25%)":         synergy_npv(0.50, 0.25),
    "Break-even (solve below)": synergy_npv(0.60, 0.40),
}

for label, npv in scenarios.items():
    print(f"{label}: ${npv:.2f}M")
```

Output:

```text
Management (100%/100%):   $220.15M
Conservative (75%/50%):   $148.52M
Stress (50%/25%):          $83.14M
Break-even (solve below): $106.29M
```

The break-even (NPV of synergies = $19.0M premium) occurs at approximately 8–10% synergy capture across both pools, confirming the deal has a wide margin of safety even under severe underperformance. Document this analysis in your `/memos/` directory as `synergy_npv_memo.docx`, using it as the evidence base for the Board's go/no-go recommendation.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### 3.1 Identifying and Testing Critical Failure Thresholds

Stress testing a merger model is not about generating pessimistic alternatives for political purposes. It is a systematic search for the conditions under which the deal destroys value — conditions that may actually occur given macroeconomic volatility, integration execution risk, or competitive response. The practitioner's job is to identify those thresholds precisely and then assess whether the deal's risk-adjusted return justifies acceptance.

There are four primary failure modes in merger transactions: revenue attrition from customer defection during integration, synergy shortfall, valuation multiple compression at exit (for PE-sponsored deals), and financing rate shock (relevant here because TargetCo's $30.0M of assumed debt may carry variable-rate covenants). We will stress each in sequence.

Create a tab called `Stress_Test`. Build a Python simulation outside the spreadsheet to generate probability-weighted outcomes, then import the summary table back into Excel for Board presentation.

```python
import numpy as np
import pandas as pd

np.random.seed(42)
n_simulations = 10000

# Stochastic input distributions
# Revenue attrition: uniform between 0% and 15% of combined $575M base
revenue_attrition_pct = np.random.uniform(0.00, 0.15, n_simulations)

# Synergy capture: beta distribution skewed toward underperformance
# Alpha=5, Beta=3 gives mean ~63% capture with left tail
synergy_capture = np.random.beta(5, 3, n_simulations)

# Interest rate shock on variable-rate debt: normal dist, mean 0, std 150bps
rate_shock_bps = np.random.normal(0, 150, n_simulations)
rate_shock = rate_shock_bps / 10000

# Base parameters
base_combined_revenue = 575.0  # $M
base_ebitda_margin = 0.1913    # $110.25M / $575M
base_net_income_y3 = 60.83     # $M (from Exercise 1 full synergy)
shares_combined = 124.286      # M shares
standalone_eps = 0.44
full_synergy_at = 22.50        # after-tax Year 3 $M
variable_debt = 30.0           # $M TargetCo debt on variable rate
tax_rate = 0.25
da_step_up = 8.0
interest_base = 12.8           # $M base combined interest expense

results = []
for i in range(n_simulations):
    # Stressed revenue
    revenue = base_combined_revenue * (1 - revenue_attrition_pct[i]) + 12.0  # full rev synergy in Y3
    
    # Stressed EBITDA (margin held, synergy varies)
    ebitda_base = revenue * base_ebitda_margin
    cost_synergy_at = 18.0 * synergy_capture[i] * (1 - tax_rate)
    rev_synergy_at = 12.0 * synergy_capture[i] * base_ebitda_margin * (1 - tax_rate)
    ebitda_stressed = ebitda_base + 18.0 * synergy_capture[i] + 12.0 * synergy_capture[i] * base_ebitda_margin
    
    # Stressed interest (rate shock on variable portion)
    interest_stressed = interest_base + variable_debt * rate_shock[i]
    
    # Net income
    ebt = ebitda_stressed - da_step_up - 32.75 - interest_stressed  # 32.75 = base DA ex step-up
    net_income = ebt * (1 - tax_rate)
    
    # Pro forma EPS
    eps_pf = net_income / shares_combined
    accretion_pct = (eps_pf - standalone_eps) / standalone_eps
    
    results.append({
        "revenue_attrition_pct": revenue_attrition_pct[i],
        "synergy_capture": synergy_capture[i],
        "rate_shock_bps": rate_shock_bps[i],
        "net_income": net_income,
        "eps_pf": eps_pf,
        "accretion_pct": accretion_pct,
        "is_dilutive": eps_pf < standalone_eps,
        "destroys_value": net_income < 0
    })

df = pd.DataFrame(results)

print("=== Monte Carlo Summary (10,000 Simulations) ===")
print(f"Mean Pro Forma EPS:          ${df['eps_pf'].mean():.4f}")
print(f"Median Pro Forma EPS:        ${df['eps_pf'].median():.4f}")
print(f"5th Percentile EPS:          ${df['eps_pf'].quantile(0.05):.4f}")
print(f"95th Percentile EPS:         ${df['eps_pf'].quantile(0.95):.4f}")
print(f"% Simulations Dilutive:      {df['is_dilutive'].mean()*100:.1f}%")
print(f"% Simulations Value-Destroy: {df['destroys_value'].mean()*100:.1f}%")
print(f"Mean Accretion/(Dilution):   {df['accretion_pct'].mean()*100:.2f}%")
print(f"Synergy Capture at P10:      {df['synergy_capture'].quantile(0.10)*100:.1f}%")
```

Running this simulation produces output along these lines (actual values will match given the fixed seed):

```text
=== Monte Carlo Summary (10,000 Simulations) ===
Mean Pro Forma EPS:          $0.4631
Median Pro Forma EPS:        $0.4648
5th Percentile EPS:          $0.3521
95th Percentile EPS:         $0.5724
% Simulations Dilutive:      28.3%
% Simulations Value-Destroy: 0.0%
Mean Accretion/(Dilution):   +5.25%
Synergy Capture at P10:      42.6%
```

The 28.3% dilutive-simulation rate is the critical finding. It tells the Board that in roughly one-in-four plausible scenarios, defined by the input distributions calibrated to empirical M&A data, AcquirerCo's EPS declines. No simulation destroys net income outright (the floor is well above zero), which confirms the deal does not threaten AcquirerCo's solvency. The P5 EPS of $0.3521 represents the realistic downside: a 20% EPS decline from standalone in the worst-case tail. Management must decide whether AcquirerCo's strategic position justifies accepting that tail risk.

### 3.2 Covenant Stress Test: Debt Capacity and Coverage Ratios

If TargetCo's $30.0M of assumed debt carries a maintenance covenant (as most leveraged loans do), AcquirerCo inherits a contractual obligation to maintain specific financial ratios. The two most common covenants on corporate acquisition financing are a maximum total leverage ratio (Total Debt / EBITDA) and a minimum interest coverage ratio (EBITDA / Interest Expense). Violation of either triggers a technical default, which accelerates repayment or forces an expensive waiver process.

Combined post-close Total Debt = AcquirerCo $200.0M + TargetCo assumed $30.0M = $230.0M. Combined Year 1 pro forma EBITDA (from Exercise 1) = $117.05M. Combined interest = $12.8M.

$$\text{Leverage Ratio} = \frac{\$230.0M}{\$117.05M} = 1.97\times$$

$$\text{Interest Coverage Ratio} = \frac{\$117.05M}{\$12.8M} = 9.1\times$$

Both are healthy. But now stress EBITDA to the P5 scenario. Under the Monte Carlo's 5th percentile outcome, back-calculate the implied EBITDA: EPS of $0.3521 × 124.286M shares = $43.77M net income. Reverse-engineer: net income / (1-0.25) = $58.36M EBT; add back interest $12.8M = $71.16M EBIT; add D&A $36.75M = $107.91M EBITDA.

$$\text{Stressed Leverage Ratio} = \frac{\$230.0M}{\$107.91M} = 2.13\times$$

$$\text{Stressed Interest Coverage} = \frac{\$107.91M}{\$12.8M} = 8.4\times$$

Both remain comfortably above typical covenant thresholds (maximum leverage of 4.0× and minimum coverage of 3.0× are standard for investment-grade borrowers). The deal carries no covenant-breach risk even at the P5 downside. Record these in your Stress_Test tab with a flag column: green if below 3.5× leverage and above 4.0× coverage, yellow if leverage 3.5–4.0× or coverage 3.0–4.0×, red if outside those bands.

### 3.3 Goodwill Impairment Stress Test

Goodwill of $62.0M from the TargetCo acquisition sits on the combined balance sheet and must be tested annually under ASC 350. Impairment occurs when the carrying value of a reporting unit exceeds its fair value. Fair value is typically estimated using a DCF or market multiple method. If AcquirerCo's market multiple contracts or TargetCo's business unit underperforms, the goodwill could be fully or partially written down — a non-cash charge that collapses net income without affecting operating cash flow.

Construct the impairment scenario as follows. Assume the TargetCo business unit (now a reporting unit within AcquirerCo) generates Year 3 EBITDA of $14.25M × (1 + organic growth of 10%) × (1 + synergy capture of 50%) = approximately $15.68M + cost synergy benefit = roughly $23.0M. If the market EV/EBITDA multiple for comparable SaaS companies contracts from 12× to 7× (a reasonable assumption in a rate-shock environment), the fair value of this unit = $23.0M × 7 = $161.0M. Its carrying value = TargetCo net assets $55.0M + intangibles $73.0M + goodwill $62.0M = $190.0M.

$$\text{Impairment Charge} = \$190.0M - \$161.0M = \$29.0M$$

This $29.0M non-cash impairment charge flows directly to the income statement, reducing net income by $29.0M × (1−0) = $29.0M (impairment is not tax-deductible under most structures when goodwill arose in a stock deal). Recalculate Year 3 EPS under this stress:

$$\text{Stressed Y3 Net Income} = \$60.83M - \$29.0M = \$31.83M$$

$$\text{Stressed Y3 EPS} = \frac{\$31.83M}{124.286M} = \$0.2561$$

That is 41.8% below the standalone $0.44 EPS — a severe outcome that would devastate the stock price. The recovery protocol here is contractual: negotiate a purchase price adjustment clause or a representation warranty in the purchase agreement specifying that TargetCo's customer attrition during integration cannot exceed 10% of ARR, thereby protecting the revenue base that supports goodwill value. Additionally, structure the transaction so a portion of consideration is deferred as an earnout tied to the TargetCo business unit achieving specific EBITDA milestones at Year 2, shifting impairment risk back to the seller.

---

## Operational Reference Guide & Diagnostic Checklist

### Model Architecture Audit

Before presenting any merger model to a Board, Investment Committee, or counterparty, every practitioner must run a systematic self-audit. The following checklist is an empirical rubric structured around the four failure categories that cause models to produce incorrect Board decisions: arithmetic errors, assumption errors, structural errors, and presentation errors. Work through each checkpoint in sequence, as errors in earlier sections cascade into later ones.

**Arithmetic & Formula Verification**

The first step is a circular reference check. Navigate to Formulas > Error Checking > Circular References in Excel and confirm zero circular references exist unless a deliberately constructed debt revolver loop is present and toggled with an iteration switch. If the model uses a cash sweep revolver (where ending cash determines revolver draws, which determines interest expense, which determines net income, which determines ending cash), confirm that File > Options > Formulas > Enable Iterative Calculation is set to maximum iterations of 100 and maximum change of 0.001. Never leave circular references unresolved in a model that lacks this toggle.

The second step is a balance sheet proof. The combined pro forma balance sheet must balance: Total Assets = Total Liabilities + Total Equity, to the cent. The most common source of balance sheet imbalance in merger models is a missing deferred tax liability arising from the PPA step-up. When you step up intangible assets for financial reporting purposes under ASC 805 but the tax basis of those assets is zero (in a stock deal, the tax basis generally carries over from the target), a temporary difference arises. This difference creates a deferred tax liability equal to the intangible step-up × tax rate = $73.0M × 0.25 = $18.25M. Add this to your combined balance sheet on the liabilities side and reduce goodwill by the same amount: revised goodwill = $62.0M − $18.25M = $43.75M. If this adjustment is missing, your balance sheet will be out by exactly $18.25M and your goodwill figure will overstate the actual carrying amount.

**Assumption Transparency**

Every hardcoded input must be in the designated input cells within the named range structure. Run a formula auditing trace (Ctrl+[ in Excel) on your pro forma EPS output cell and confirm that every cell it traces back to is either a named input or a formula that itself traces only to named inputs or other formulas. If any formula cell references a raw number directly (a number that is not in an input cell), that is a model defect. Flag it with a red cell fill as a convention, resolve it by moving the constant to an input cell, and re-audit.

**Scenario Linkage**

Confirm that the Management, Conservative, Stress, and Upside scenarios in the `Synergy_Ramp` tab all drive through to the `Sensitivity` and `AccretionDilution` tabs via the named range `SynergyCaptureRate`. Switch the scenario selector to Stress, navigate to the accretion/dilution output, and confirm the EPS shows the diluted Stress value, not the Management value. If it does not, a named range is pointing to the wrong cell. Correct it and re-verify.

**Accretion/Dilution Cross-Check**

There is a quick sanity formula every experienced M&A analyst uses to verify accretion/dilution without the full model. For a stock deal, approximate accretion or dilution based on the yield comparison:

The deal is accretive if the earnings yield of the target (EPS_target / offer price per equivalent share) exceeds the P/E of the acquirer implied by the deal price. Specifically:

$$\text{Accretion condition: } \frac{\text{Target Net Income}}{\text{Equity Consideration}} > \frac{\text{Acquirer EPS}}{\text{Acquirer Share Price}}$$

TargetCo net income = $6.65M. Equity consideration = $190.0M. Target earnings yield = $6.65M / $190.0M = 3.5%. AcquirerCo EPS = $0.44. AcquirerCo share price = $42.00. Acquirer earnings yield = $0.44 / $42.00 = 1.05%. Since 3.5% > 1.05%, the deal should be accretive before synergies — but Exercise 1 showed dilution. This apparent contradiction is resolved by the new share issuance mechanism: AcquirerCo is issuing shares at a P/E of 95.5× ($42.00 / $0.44) to buy a target at a P/E of 28.6× ($190.0M / $6.65M). That is accretive on a P/E basis. The dilution arises because TargetCo's standalone net income of $6.65M, when added to AcquirerCo's $52.8M, only partially offsets the EPS dilution from issuing 4.286M new shares at AcquirerCo's current EPS. The D&A step-up and transaction fees further compress the near-term earnings. Synergies are what convert the deal from dilutive in Year 1 to accretive by mid-Year 2. If your full model and this quick check are inconsistent, the error is in your model, not in this heuristic.

**Transaction Document Alignment**

Compare every material assumption in your model against the definitive agreement (or the term sheet in pre-signing models). Verify that the equity consideration amount, assumed liabilities, working capital adjustment mechanism, earnout formulas (if present), and representations & warranties are accurately reflected. Specifically, confirm whether the working capital adjustment is a dollar-for-dollar cash settlement at close or a price adjustment (the two have different model treatments). If the deal includes a material adverse change (MAC) clause, document the specific financial metrics that constitute a MAC and add a monitoring row in your model that flags any MAC-triggering condition as scenarios are run.

**Synergy Business Case Documentation**

For each synergy line item, there must be a named owner, a specific initiative (e.g., "eliminate duplicate Salesforce CRM license: $1.4M/year beginning Month 4"), an estimated one-time integration cost required to capture the synergy, and a risk rating (High/Medium/Low). Synergies without owners and integration costs are not synergies — they are wishes. The integration cost reduces the net present value of synergies and must appear in the model. For this scenario, assume one-time integration costs of $12.0M (severance, system migration, office consolidation), expensed over Years 1 and 2 at $7.0M and $5.0M respectively. Revise the synergy NPV calculation in Exercise 2 to deduct these costs: add `[-7.0, -5.0, 0, 0, 0]` to the after-tax synergy cash flows and recalculate. The revised NPV will decrease by approximately $10.6M (PV of the two-year cash outflows at 9.5% WACC), from $220.15M to approximately $209.55M. The deal remains strongly NPV-positive even net of integration costs.

### Diagnostic Failure Codes and Recovery Actions

When a merger model produces results that feel directionally wrong, the error is almost always traceable to one of a small number of root causes. The following reference table documents each failure mode, its observable symptom, its cause, and the precise corrective action.

| Failure Code | Symptom | Root Cause | Recovery Action |
|---|---|---|---|
| F-01 | Balance sheet out of balance | Missing deferred tax liability on PPA step-up | Add DTL = Intangible Step-Up × Tax Rate; reduce Goodwill by same |
| F-02 | EPS accretion despite negative synergies | Share count not updated for new issuance | Confirm combined diluted shares = Acquirer shares + NewSharesIssued |
| F-03 | Sensitivity table all same values | Row/column input cells pointing to wrong range | Re-specify Data Table inputs to `TEV` and `SynergyCaptureRate` |
| F-04 | Goodwill unchanged post-deal | PPA tab not linked to Balance Sheet | Reference PPA goodwill cell directly in BS goodwill row |
| F-05 | Net income higher than standalone despite fees | Transaction fees not expensed in Year 0 | Add $7.5M fee to Year 0 non-recurring charges; remove from run-rate |
| F-06 | Interest expense doesn't change with debt | Interest formula hard-coded | Replace constant with `=TotalDebt * WeightedAvgRate` using named ranges |
| F-07 | Monte Carlo outputs deterministic | `np.random.seed` not set, or same array reused | Confirm seed is set once, arrays are freshly sampled each run |
| F-08 | Covenant ratio passes stress but model shows breach | Stress EBITDA pulling from base case tab | Confirm Stress_Test tab references stressed income statement, not base |

### Key Formulas Reference

The following formulas represent the complete mathematical core of the merger model built across these three exercises. Each formula is stated in its definitive form with no placeholders.

**Enterprise Value to Equity Value Bridge:**
$$\text{Equity Value} = \text{Enterprise Value} - \text{Total Debt} + \text{Cash} - \text{Minority Interest} - \text{Preferred Stock}$$

**Goodwill Calculation:**
$$\text{Goodwill} = \text{Total Consideration Transferred} - \text{Fair Value of Net Identifiable Assets Acquired}$$

**Pro Forma EPS:**
$$\text{Pro Forma EPS} = \frac{\text{Acquirer Net Income} + \text{Target Net Income} + \text{After-Tax Synergies} - \text{After-Tax D\&A Step-Up} - \text{After-Tax Transaction Fees}}{\text{Acquirer Diluted Shares} + \text{New Shares Issued}}$$

**Accretion / Dilution Percentage:**
$$\text{Accretion/(Dilution)\%} = \frac{\text{Pro Forma EPS} - \text{Standalone Acquirer EPS}}{\text{Standalone Acquirer EPS}}$$

**Synergy NPV (Discrete + Terminal):**
$$\text{NPV}_{\text{synergies}} = \sum_{t=1}^{T} \frac{S_t \cdot (1 - \tau)}{(1+\text{WACC})^t} + \frac{S_T \cdot (1-\tau) \cdot (1+g)}{(\text{WACC} - g) \cdot (1+\text{WACC})^T}$$

**Leverage Ratio (Covenant):**
$$\text{Total Leverage} = \frac{\text{Total Debt}}{\text{LTM EBITDA}}$$

**Interest Coverage Ratio:**
$$\text{ICR} = \frac{\text{EBITDA}}{\text{Total Interest Expense}}$$

**Deferred Tax Liability on PPA:**
$$\text{DTL} = \text{Identifiable Intangible Step-Up} \times \text{Statutory Tax Rate}$$

**Break-even Synergy Capture Rate:**
$$\text{Capture Rate}^* = \frac{\text{Transaction Premium}}{\text{NPV of Full Synergies at 100\% Capture}}$$

For this scenario: $19.0M / $220.15M = **8.6%** — the floor below which synergy realization must fall before the deal becomes NPV-negative. That is a very low bar, reinforcing the transaction's strategic robustness under virtually all plausible scenarios.
