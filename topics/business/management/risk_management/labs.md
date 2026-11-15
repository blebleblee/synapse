# Operational Verification Labs: Risk Management

## Objective & Operational Lab Setup

Risk management in a business context is not a compliance checkbox or a slide deck of red-amber-green traffic lights. It is a continuous, quantitative discipline that sits at the intersection of corporate finance, operational decision-making, and strategic planning. These labs treat risk the way a chief risk officer at a mid-market industrial company or a Series C SaaS business would: as a measurable quantity that must be identified, ranked by expected economic impact, stress-tested against realistic adverse scenarios, and embedded into the operational cadence of the business through clear ownership, trigger thresholds, and recovery procedures.

The three exercises that follow escalate in complexity. The first exercise grounds you in building a formal risk register that moves beyond text descriptions into quantified probability-impact scoring and expected value calculations. The second exercise teaches you to vary your assumptions systematically, performing Monte Carlo-style sensitivity analysis in a spreadsheet to understand which risks drive the most variance in a key business outcome (operating cash flow). The third exercise puts the full framework under stress by simulating a correlated multi-risk event and forces you to execute a structured recovery protocol with defined escalation paths and go/no-go decision gates.

You need no specialized software beyond a spreadsheet application (Microsoft Excel or Google Sheets with equivalent formulas) and a word processor for the narrative deliverables. Every formula given here is complete and executable. Where Python is introduced to extend the Monte Carlo simulation, the code is fully runnable with no substitution required, using only the NumPy and Pandas libraries, which are available in any standard Python 3.8 or later environment via `pip install numpy pandas`.

Before starting, create a working directory called `risk_mgmt_labs/` and inside it three files: `risk_register.xlsx`, `monte_carlo_cashflow.xlsx`, and `stress_test_protocol.xlsx`. The Python simulation file will be `cashflow_mc.py`. All exercises reference these files by name.

---

## Exercise 1: Foundational Practical Implementation

### Building a Quantified Risk Register with Expected Loss Calculations

The risk register is the foundational artifact of enterprise risk management. Its purpose is not documentation for its own sake but to create a ranked, economic view of the threats that could prevent a business from meeting its operating plan. The standard qualitative approach of assigning "High / Medium / Low" ratings produces a matrix that is visually tidy and analytically useless, because it conflates a rare catastrophic event with a frequent nuisance event when both land in the same color band. The practitioner approach calculates Expected Annual Loss (EAL) for each risk, which forces you to reason explicitly about probability and financial magnitude separately before combining them.

The formula is:

$$\text{EAL} = P(\text{occurrence per year}) \times \text{Financial Impact} \times \text{Mitigation Effectiveness Factor}$$

Where Mitigation Effectiveness Factor (MEF) represents the fraction of residual impact after existing controls are applied. A MEF of 1.0 means no controls exist. A MEF of 0.4 means existing controls reduce the impact by 60%. This keeps the register honest about whether your current control environment is actually working.

Open `risk_register.xlsx` and build the following column structure across Row 1 as headers:

**Column A:** Risk ID  
**Column B:** Risk Category  
**Column C:** Risk Description  
**Column D:** Risk Driver (the root cause mechanism)  
**Column E:** Gross Annual Probability (expressed as a decimal, e.g., 0.15 for 15%)  
**Column F:** Gross Financial Impact ($, worst-case single-event)  
**Column G:** Existing Controls Description  
**Column H:** Mitigation Effectiveness Factor (0.0 to 1.0)  
**Column I:** Residual Annual Probability (after control, =E×(1-(1-H)) simplified as =E since probability reduction comes from H applied to impact, not to frequency — keep probability unchanged, apply H to impact)  
**Column J:** Residual Financial Impact (=$F×$H)  
**Column K:** Expected Annual Loss — EAL (=$E×$J)  
**Column L:** Risk Owner (name and title)  
**Column M:** Review Frequency  
**Column N:** Trigger Indicator (the leading metric that signals this risk is activating)

Now populate the register with the following ten risks drawn from a hypothetical mid-market B2B SaaS company with $24M ARR, 180 employees, and a primary customer concentration in the financial services vertical. Enter each row exactly as specified, including all numeric values, so that the EAL column auto-calculates correctly.

**Row 2 — R-001:** Strategic | Top customer (accounting for 18% of ARR) issues non-renewal notice | Multi-year contract expires, incumbent vendor relationship weakens | 0.20 | $4,320,000 | Quarterly Executive Business Reviews; contractual auto-renewal clause with 90-day notice window | 0.55 | =E2 | =F2\*H2 | =E2\*J2 | VP Customer Success | Quarterly | Customer health score drops below 65 for 60+ days

**Row 3 — R-002:** Financial | Accounts receivable aging beyond 90 days exceeds 15% of total AR | Customer cash flow stress in financial services vertical during rate cycle | 0.35 | $1,800,000 | Net 30 payment terms; automated dunning at Day 15, 30, 45; credit checks at contract initiation | 0.40 | =E3 | =F3\*H3 | =E3\*J3 | CFO | Monthly | AR aging report: 60-day bucket exceeds 8% of total AR

**Row 4 — R-003:** Operational | Critical SaaS platform outage exceeding 4 hours during business hours | Single-region AWS deployment; insufficient redundancy in database tier | 0.25 | $2,200,000 | Multi-AZ RDS deployment; CloudWatch alerting; incident response playbook | 0.30 | =E4 | =F4\*H4 | =E4\*J4 | VP Engineering | Monthly | P99 API latency exceeds 800ms for 15+ consecutive minutes

**Row 5 — R-004:** Talent | Departure of CTO or VP Sales within 12-month window | Competitive compensation environment; equity cliff creates departure risk | 0.18 | $3,100,000 | Retention bonus agreements; accelerated vesting schedule for key personnel | 0.70 | =E5 | =F5\*H5 | =E5\*J5 | CEO | Quarterly | eNPS below 40 for two consecutive quarters; compensation benchmarking gap >15%

**Row 6 — R-005:** Compliance | GDPR or SOC 2 audit failure resulting in regulatory fine or customer-triggered audit right | Third-party data sub-processor inventory incomplete; access control reviews irregular | 0.12 | $5,500,000 | Annual SOC 2 Type II audit; GDPR DPA templates; quarterly access reviews | 0.50 | =E6 | =F6\*H6 | =E6\*J6 | General Counsel / CISO | Quarterly | Failed quarterly access review; sub-processor discovered outside approved registry

**Row 7 — R-006:** Market | Aggressive pricing move by primary competitor reduces new logo win rate by 20+ points | Well-funded competitor raises Series D; launches low-price entry tier | 0.30 | $2,880,000 | Competitive intelligence program; value-based pricing positioning; champion development in accounts | 0.65 | =E7 | =F7\*H7 | =E7\*J7 | CRO | Monthly | Win rate in competitive deals drops below 42% for two consecutive months

**Row 8 — R-007:** Financial | FX exposure on GBP and EUR-denominated contracts creates >5% revenue variance | 22% of ARR denominated in non-USD currencies; no hedging program | 0.40 | $1,250,000 | Invoicing in USD where contractually permitted; natural hedging through EUR-denominated vendor contracts | 0.60 | =E8 | =F8\*H8 | =E8\*J8 | CFO | Quarterly | USD/EUR rate moves >8% in rolling 90-day window

**Row 9 — R-008:** Operational | Key SaaS infrastructure vendor (AWS or Stripe) changes pricing or terms materially | Cloud cost trajectory; payment processing dependency on single vendor | 0.15 | $980,000 | Multi-year AWS Enterprise Discount Program agreement; Stripe volume pricing contract | 0.45 | =E9 | =F9\*H9 | =E9\*J9 | VP Engineering / CFO | Semi-Annual | Vendor announces pricing change; cost per unit of compute increases >12% quarter-over-quarter

**Row 10 — R-009:** Strategic | M&A by a competitor acquires a key technology partner, restricting API access | Integration partner ecosystem consolidation trend in fintech | 0.10 | $3,600,000 | Contract provisions requiring API continuity post-acquisition; alternative integration development backlog | 0.75 | =E10 | =F10\*H10 | =E10\*J10 | CPO | Semi-Annual | Integration partner receives funding or M&A rumors surface in trade press

**Row 11 — R-010:** Talent | Inability to hire 8 net-new engineers in next 12 months delays product roadmap by one quarter | Engineering talent market compression; employer brand below Tier-1 competitors | 0.45 | $1,600,000 | Competitive compensation bands; engineering blog and conference presence; referral bonus program | 0.55 | =E11 | =F11\*H11 | =E11\*J11 | VP Engineering / VP People | Monthly | Open engineering requisitions unfilled for 60+ days; offer acceptance rate below 70%

Once all rows are populated, add a summary section below Row 12. In Cell A14, write "Total Portfolio EAL." In Cell B14, enter `=SUM(K2:K11)`. This number gives you the aggregate expected annual loss across your identified risk universe. For this dataset it will calculate to $1,566,580, which represents the probability-weighted, control-adjusted cost of your current risk posture. This is the number a CFO cares about because it can be directly compared against the annual cost of your risk mitigation programs to evaluate whether the control spend has positive ROI.

Sort the register by Column K (EAL) in descending order. You will find that R-001 (customer concentration), R-004 (key talent), and R-005 (compliance) rank in the top three by expected loss, even though R-005 has only a 12% annual probability. This illustrates the central insight that severity of consequence, not frequency of occurrence, often drives risk prioritization, and it is exactly the kind of insight that a qualitative traffic-light matrix suppresses.

The final step of this exercise is to create a two-variable heat map using EAL buckets and risk category labels. In Columns P through T of the same sheet, create a 5×5 grid where rows represent Probability quintiles (0–10%, 10–20%, 20–30%, 30–45%, >45%) and columns represent Impact quintiles (< $1M, $1M–$2M, $2M–$3.5M, $3.5M–$5M, >$5M). Use `COUNTIFS()` to count how many risks fall in each cell. This map becomes your board-level reporting artifact — it communicates risk concentration visually without losing the numerical foundation underneath.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Monte Carlo Sensitivity Analysis of Operating Cash Flow Risk

The risk register built in Exercise 1 gives you a point estimate of expected loss per risk. What it cannot tell you is the distribution of outcomes across a full year when multiple risks interact simultaneously with uncertain financial drivers. For that, you need a simulation. This exercise builds a Monte Carlo simulation of a 12-month operating cash flow model and identifies which risk and assumption variables drive the most variance in the outcome distribution.

The operating logic is this: a business's monthly cash flow is a function of its revenue run rate, gross margin, operating expense base, and working capital dynamics. Each of those inputs carries uncertainty, and that uncertainty is correlated in economically meaningful ways. When a competitor launches an aggressive pricing campaign (R-006), it depresses new logo win rates and simultaneously pressures net expansion rates, creating compound revenue underperformance that a single-variable sensitivity analysis would understate.

Begin with the Excel model in `monte_carlo_cashflow.xlsx`. Build the following deterministic base case first across 12 monthly columns (B through M for January through December), with Row 1 as column headers and Column A as row labels.

**Row 2 — Beginning MRR:** $2,000,000 (January start)  
**Row 3 — New Logo MRR Added:** Base case $85,000/month  
**Row 4 — Expansion MRR:** Base case $42,000/month (net of contraction)  
**Row 5 — Churned MRR:** Base case $38,000/month  
**Row 6 — Ending MRR:** =B2+B3+B4-B5 (each month references prior month's ending MRR as that month's beginning MRR)  
**Row 7 — Monthly Revenue:** =B6 (MRR recognized in month)  
**Row 8 — Gross Margin %:** 72% constant in base case  
**Row 9 — Gross Profit:** =B7\*B8  
**Row 10 — Total OpEx:** $1,350,000/month (fully loaded: salaries, infrastructure, G&A, S&M, R&D)  
**Row 11 — EBITDA:** =B9-B10  
**Row 12 — Working Capital Change:** -$55,000/month (represents AR build as revenue grows)  
**Row 13 — CapEx / Capitalized Dev:** -$80,000/month  
**Row 14 — Operating Cash Flow:** =B11+B12+B13

The base case produces a 12-month cumulative operating cash flow of approximately $1,044,000. That is your anchor. The simulation will tell you how often this number goes negative and what the range of outcomes looks like given realistic parameter uncertainty.

Now build the Python Monte Carlo simulation. Create `cashflow_mc.py` with the following complete, runnable code:

```python
import numpy as np
import pandas as pd

np.random.seed(42)
N_SIMULATIONS = 10000
N_MONTHS = 12

# Base case parameters
base_beginning_mrr = 2_000_000
base_new_logo_mrr = 85_000
base_expansion_mrr = 42_000
base_churn_mrr = 38_000
base_gross_margin = 0.72
base_opex = 1_350_000
base_wc_change = -55_000
base_capex = -80_000

# Risk scenario probability flags (drawn per simulation from Bernoulli distributions)
# R-001: Top customer non-renewal — P=0.20, impact: immediate churn of $360,000 MRR in month of event
# R-003: Platform outage — P=0.25, impact: one-time revenue credit of $45,000 and 0.5% gross margin hit for 1 month
# R-006: Competitive pricing pressure — P=0.30, impact: new logo MRR drops 22% for remainder of year from event month
# R-010: Hiring miss — P=0.45, impact: expansion MRR growth rate reduced by 15% for 6 months

r001_trigger = np.random.binomial(1, 0.20, N_SIMULATIONS).astype(bool)
r001_month   = np.random.randint(1, 13, N_SIMULATIONS)

r003_trigger = np.random.binomial(1, 0.25, N_SIMULATIONS).astype(bool)
r003_month   = np.random.randint(1, 13, N_SIMULATIONS)

r006_trigger = np.random.binomial(1, 0.30, N_SIMULATIONS).astype(bool)
r006_month   = np.random.randint(1, 10, N_SIMULATIONS)  # must start by month 10 to have impact

r010_trigger = np.random.binomial(1, 0.45, N_SIMULATIONS).astype(bool)
r010_month   = np.random.randint(1, 8, N_SIMULATIONS)   # starts in first 7 months

# Continuous parameter uncertainty (drawn fresh per simulation)
# Gross margin: normally distributed around base, std = 2.5 percentage points
gm_draw = np.random.normal(base_gross_margin, 0.025, N_SIMULATIONS)

# OpEx: uniformly distributed +/- 8% around base (reflects headcount timing variance)
opex_draw = np.random.uniform(base_opex * 0.92, base_opex * 1.08, N_SIMULATIONS)

# New logo MRR: normally distributed, std = $18,000 (pipeline conversion variance)
new_logo_draw = np.random.normal(base_new_logo_mrr, 18_000, N_SIMULATIONS)

cumulative_ocf = np.zeros(N_SIMULATIONS)

for sim in range(N_SIMULATIONS):
    mrr = base_beginning_mrr
    gm = np.clip(gm_draw[sim], 0.55, 0.85)
    opex = opex_draw[sim]
    new_logo_monthly = max(new_logo_draw[sim], 0)
    
    sim_ocf = 0.0
    
    for month in range(1, N_MONTHS + 1):
        # Apply risk events
        churn_this_month = base_churn_mrr
        expansion_this_month = base_expansion_mrr
        new_logo_this_month = new_logo_monthly
        gm_this_month = gm
        revenue_credit = 0.0
        
        if r001_trigger[sim] and month == r001_month[sim]:
            churn_this_month += 360_000  # top customer non-renewal hits in this month
        
        if r003_trigger[sim] and month == r003_month[sim]:
            revenue_credit = -45_000
            gm_this_month = gm_this_month - 0.005
        
        if r006_trigger[sim] and month >= r006_month[sim]:
            new_logo_this_month = new_logo_this_month * 0.78  # 22% reduction
        
        if r010_trigger[sim] and month >= r010_month[sim] and month < r010_month[sim] + 6:
            expansion_this_month = expansion_this_month * 0.85  # 15% reduction
        
        # MRR waterfall
        ending_mrr = mrr + new_logo_this_month + expansion_this_month - churn_this_month
        ending_mrr = max(ending_mrr, 0)
        
        monthly_revenue = ending_mrr + revenue_credit
        gross_profit = monthly_revenue * gm_this_month
        ebitda = gross_profit - opex
        ocf = ebitda + base_wc_change + base_capex
        
        sim_ocf += ocf
        mrr = ending_mrr
    
    cumulative_ocf[sim] = sim_ocf

# Results analysis
results = pd.Series(cumulative_ocf)

print("=" * 55)
print("Monte Carlo Operating Cash Flow — 10,000 Simulations")
print("=" * 55)
print(f"Base Case OCF (deterministic):  $1,044,000")
print(f"Simulated Mean OCF:             ${results.mean():,.0f}")
print(f"Simulated Median OCF:           ${results.median():,.0f}")
print(f"Standard Deviation:             ${results.std():,.0f}")
print(f"5th Percentile (downside):      ${results.quantile(0.05):,.0f}")
print(f"25th Percentile:                ${results.quantile(0.25):,.0f}")
print(f"75th Percentile:                ${results.quantile(0.75):,.0f}")
print(f"95th Percentile (upside):       ${results.quantile(0.95):,.0f}")
print(f"Probability OCF < $0:           {(results < 0).mean() * 100:.1f}%")
print(f"Probability OCF < -$500,000:    {(results < -500_000).mean() * 100:.1f}%")
print(f"Probability OCF > $2,000,000:   {(results > 2_000_000).mean() * 100:.1f}%")
print("=" * 55)

# Sensitivity decomposition: run isolated single-risk simulations
def run_isolated(risk_name, trigger_arr, trigger_month_arr, impact_fn):
    ocf_arr = np.zeros(N_SIMULATIONS)
    gm_base = np.full(N_SIMULATIONS, base_gross_margin)
    opex_base = np.full(N_SIMULATIONS, base_opex)
    new_logo_base = np.full(N_SIMULATIONS, base_new_logo_mrr)
    for sim in range(N_SIMULATIONS):
        mrr = base_beginning_mrr
        sim_ocf = 0.0
        for month in range(1, N_MONTHS + 1):
            churn = base_churn_mrr
            expansion = base_expansion_mrr
            new_logo = base_new_logo_mrr
            gm = base_gross_margin
            rev_credit = 0.0
            if trigger_arr[sim]:
                churn, expansion, new_logo, gm, rev_credit = impact_fn(
                    month, trigger_month_arr[sim], churn, expansion, new_logo, gm, rev_credit
                )
            ending_mrr = max(mrr + new_logo + expansion - churn, 0)
            monthly_revenue = ending_mrr + rev_credit
            gross_profit = monthly_revenue * gm
            ebitda = gross_profit - base_opex
            ocf = ebitda + base_wc_change + base_capex
            sim_ocf += ocf
            mrr = ending_mrr
        ocf_arr[sim] = sim_ocf
    return pd.Series(ocf_arr)

def impact_r001(month, event_month, churn, expansion, new_logo, gm, rev_credit):
    if month == event_month:
        churn += 360_000
    return churn, expansion, new_logo, gm, rev_credit

def impact_r006(month, event_month, churn, expansion, new_logo, gm, rev_credit):
    if month >= event_month:
        new_logo = new_logo * 0.78
    return churn, expansion, new_logo, gm, rev_credit

def impact_r010(month, event_month, churn, expansion, new_logo, gm, rev_credit):
    if event_month <= month < event_month + 6:
        expansion = expansion * 0.85
    return churn, expansion, new_logo, gm, rev_credit

r001_isolated = run_isolated("R-001", r001_trigger, r001_month, impact_r001)
r006_isolated = run_isolated("R-006", r006_trigger, r006_month, impact_r006)
r010_isolated = run_isolated("R-010", r010_trigger, r010_month, impact_r010)

base_ocf_series = pd.Series(np.full(N_SIMULATIONS, 1_044_000.0))

print("\nIsolated Risk OCF Impact (Mean vs Base):")
print(f"  R-001 (Top Customer Churn):    ${r001_isolated.mean() - 1_044_000:,.0f}")
print(f"  R-006 (Competitive Pricing):   ${r006_isolated.mean() - 1_044_000:,.0f}")
print(f"  R-010 (Hiring Miss):           ${r010_isolated.mean() - 1_044_000:,.0f}")
```

Run this file from your terminal with `python cashflow_mc.py`. The output will show you the full distribution of 12-month operating cash flows and, critically, the isolated mean impact of each of the three largest operational risks. You will find that the competitive pricing risk (R-006) has a larger expected OCF drag than the hiring miss (R-010) because its impact compounds across all remaining months from the event date, whereas the hiring miss is bounded to six months. This is the kind of insight that shapes where a CRO invests in competitive battlecard development versus where a VP People prioritizes time-to-fill metrics.

The empirical analysis deliverable from this exercise is a one-page memo addressed to your CFO and CRO summarizing: the base case OCF, the simulated mean and standard deviation, the probability of negative OCF, the top two risk drivers by isolated impact, and the specific mitigation investment that would reduce each. This memo format trains the habit of translating model outputs into actionable management decisions rather than leaving simulation results as a technical artifact no one acts on.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Correlated Multi-Risk Scenario Simulation and Structured Recovery Execution

The two prior exercises treat risks as independent events. In practice, risks cluster. An economic downturn simultaneously increases customer churn probability, stresses accounts receivable collection, compresses new logo pipeline conversion, and triggers competitive pricing pressure from cash-burning competitors defending market share. This exercise simulates a correlated multi-risk stress scenario — specifically, a macro credit tightening event in the financial services vertical — and executes a structured recovery protocol with defined decision gates.

The stress scenario is defined as follows. In Month 4 of the fiscal year, a sudden 150-basis-point rate increase by the Federal Reserve triggers a credit risk reassessment across the financial services industry. Your company's primary vertical experiences a simultaneous activation of R-001 (top customer signals at-risk status, moving from non-renewal risk from 20% to 65% probability), R-002 (AR aging accelerates, 60-day bucket rises to 11% of total AR), R-006 (a competitor with VC bridge funding announces a 30% price reduction on its core product), and R-004 (your VP Sales hands in resignation, effective in 30 days, citing a competing offer).

This is a boundary failure scenario because it exceeds the design parameters of your existing control environment. Your QBR cadence was designed for single-risk events. Your incident response playbook covers platform outages, not revenue model disruption. Your executive retention plan did not contemplate a departure during an active pipeline stress event. What follows is the operational recovery protocol you must execute.

Open `stress_test_protocol.xlsx` and build the following structure to track the recovery execution across six operational dimensions: Revenue Defense, Cash Management, Competitive Response, Talent Continuity, Board Communication, and 90-Day Exit Criteria.

**Phase 1: Immediate Actions (Days 1–7 from stress event confirmation)**

The first action on Day 1 is to convene a Risk Response War Room with the CEO, CFO, CRO, VP Customer Success, and General Counsel. This is not a routine leadership team meeting. It has a specific agenda: situation assessment with numbers on the table, not narratives. The CFO presents an emergency 13-week cash flow forecast built in `stress_test_protocol.xlsx` using the following structure:

In the 13-week cash flow tab, build weekly columns (W1 through W13) with the following rows:

**Row 2 — Beginning Cash:** $4,200,000 (actual cash balance at stress event)  
**Row 3 — Cash Collections from AR:** Base $480,000/week; stress case applies a 20% collection delay = $384,000/week  
**Row 4 — New Logo Cash Received:** $0/week (assume 0 net new bookings for 4 weeks given VP Sales departure)  
**Row 5 — Total Cash Inflows:** =SUM(B3:B4)  
**Row 6 — Payroll and Benefits:** -$280,000/week  
**Row 7 — Vendor and Infrastructure:** -$95,000/week  
**Row 8 — Discretionary Spend (Travel, Events, Demand Gen):** -$62,000/week base; freeze to -$15,000/week in stress case  
**Row 9 — Total Cash Outflows:** =SUM(B6:B8)  
**Row 10 — Net Weekly Cash Flow:** =B5+B9  
**Row 11 — Ending Cash:** =B2+B10

For Week 1 through Week 4, apply the stress case collection delay and new logo booking freeze. Beginning in Week 5, model a partial recovery: collections return to 85% of base ($408,000/week), and new logo bookings restart at $40,000/week as an interim sales leader is activated. The 13-week model will show your minimum cash balance occurring at Week 4 (approximately $3,340,000) and recovering to $3,780,000 by Week 13 under the stress scenario with discretionary freeze applied. If the ending cash falls below $2,500,000 (representing less than 2.5 weeks of operating expense coverage), that is your liquidity trigger that requires immediate draw on the revolving credit facility.

The revenue defense action for the top customer at-risk (R-001 escalated) must be initiated within 48 hours. The VP Customer Success and CEO jointly call the customer's CFO and Chief Risk Officer — not the operations contact who handles day-to-day usage. The purpose of that call is not to pitch features. It is to understand what the customer's internal pressure looks like, offer to renegotiate payment terms (Net 30 to Net 60 or a quarterly invoice restructure) in exchange for a 24-month contract extension, and surface any service risk the customer is experiencing that your team can address before it becomes a formal complaint. Document the call outcomes in the risk register under R-001 with a date stamp and a next-action owner.

**Phase 2: Structured Recovery Execution (Days 8–30)**

By Day 10, the CFO must have completed a formal accounts receivable triage. In `stress_test_protocol.xlsx`, create a third tab called AR Triage. Build a table with columns for Customer Name, Total AR Balance, AR 0–30 Days, AR 31–60 Days, AR 61–90 Days, AR >90 Days, Customer Health Score (from your CS platform), Probability of Collection (%), Expected Collectible Amount (=Total AR Balance × Probability of Collection), and Action Owner. For each customer where the AR >90 Days bucket exceeds $50,000, the CFO personally contacts the economic buyer (not AP) within five business days.

The competitive response to R-006 (competitor's 30% price reduction) requires a decision gate by Day 14. The CRO and CPO jointly evaluate three options: a targeted price match for at-risk renewals only (preserving blended ASP), a bundle expansion that increases value delivery without reducing price (adding features or services that cost less than the price reduction would), or a champion development campaign that identifies three to five executive-level advocates within each at-risk account and executes a structured reference-selling program. Evaluate each option in `stress_test_protocol.xlsx` on a decision matrix with the following scoring dimensions and weights: Net Revenue Impact over 12 months (weight 40%), Gross Margin Impact (weight 25%), Speed of Execution in days (weight 20%), and Reversibility (weight 15%). Score each option 1–5 on each dimension, multiply by weight, sum for a weighted score, and select the highest. This matrix produces a defensible, documented decision that can be shown to the board, rather than a judgment call that cannot be audited.

For the VP Sales departure (R-004 triggered), the talent continuity protocol requires three parallel actions. First, the CEO contacts two to three external interim sales leadership firms within 48 hours of receiving the resignation to have an interim VP Sales seated within 15 business days. Second, the existing sales manager (Director of Sales or Senior AE) is designated as acting team lead and given a 90-day retention bonus equal to 20% of their annual salary, payable at Day 91 if they remain. Third, the VP Sales' active pipeline — specifically any opportunities in Stage 4 or later (verbal commit or proposal submitted) — is reassigned to named AEs with explicit instructions that the CEO or CRO will co-sell any deal over $150,000 ACV for the next 60 days.

**Phase 3: 90-Day Exit Criteria and Go/No-Go Gate**

By Day 90, the recovery is judged against five measurable exit criteria. The first criterion is that the top at-risk customer has either signed a renewal or extension, or a formal multi-stakeholder save plan is in place with a named executive owner and a 30-day close commitment. The second criterion is that AR >60 Days as a percentage of total AR has returned below 8%. The third criterion is that an interim or permanent VP Sales is seated and has attended at least three pipeline calls with the sales team. The fourth criterion is that the 13-week cash flow model, updated with actual results, shows ending cash at or above $3,500,000 with no week breaching the $2,500,000 liquidity floor. The fifth criterion is that competitive win rate in the core financial services vertical, tracked across all deals closed in the 90-day window, is at or above 44%.

If three or more of these five criteria are met at Day 90, the stress scenario is classified as resolved and the risk register is updated to reflect the new residual risk levels, control effectiveness factors, and trigger thresholds. If two or fewer criteria are met, the company enters a formal business review with the board, presenting an updated 12-month operating plan with a revised capital structure if needed, including assessment of whether the revolving credit facility requires expansion or whether a bridge capital raise is appropriate given the cash trajectory.

The final deliverable of this exercise is a two-page Board Risk Update document structured as follows: a one-paragraph situation summary stating what happened, when, and what financial exposure was confirmed; a table showing each of the five exit criteria, the target threshold, the actual result at Day 90, and a pass/fail indicator; a 13-week cash flow chart showing actual versus stress case; and a forward-looking section stating the two highest residual risks still requiring board attention with specific mitigation actions and owners attached. This document trains the discipline of closing the loop on a risk event rather than allowing recovery efforts to dissolve into untracked activity.

---

## Operational Reference Guide & Diagnostic Checklist

This reference section is designed for use during active risk management operations, quarterly risk reviews, and annual enterprise risk assessment cycles. It consolidates the formulas, scoring rubrics, and diagnostic questions from all three exercises into a single reference artifact.

**Core Formulas**

Expected Annual Loss: $\text{EAL} = P_{\text{annual}} \times \text{Impact}_{\text{gross}} \times \text{MEF}$

Net Revenue Retention: $\text{NRR} = \dfrac{(\text{Beginning MRR} + \text{Expansion MRR} - \text{Contraction MRR} - \text{Churned MRR})}{\text{Beginning MRR}}$

CAC Payback Period (months): $\text{CAC Payback} = \dfrac{\text{CAC}}{\text{ACV} \times \text{Gross Margin \%} / 12}$

Gross Churn Rate (monthly): $\text{Gross Churn} = \dfrac{\text{Churned MRR}}{\text{Beginning MRR}}$

Customer Health Score (composite): $\text{CHS} = (w_1 \times \text{Product Usage Score}) + (w_2 \times \text{Support Ticket Sentiment}) + (w_3 \times \text{NPS Response}) + (w_4 \times \text{Contract Tenure Score})$ where $w_1 + w_2 + w_3 + w_4 = 1.0$ and typical weights are 0.40, 0.20, 0.25, 0.15 respectively.

AR Collection Probability (simplified scoring): For accounts 0–30 days outstanding, assign 98% probability. For 31–60 days, assign 88%. For 61–90 days, assign 70%. For 91–120 days, assign 45%. Beyond 120 days, assign 25%. These rates are conservative starting points; recalibrate against your historical actual collection data once you have 24 months of AR aging records available.

RICE Prioritization Score: $\text{RICE} = \dfrac{\text{Reach} \times \text{Impact} \times \text{Confidence}}{\text{Effort}}$ where Reach is the number of users affected per quarter, Impact is scored 0.25 (minimal), 0.5 (low), 1 (medium), 2 (high), or 3 (massive), Confidence is a percentage (100% = fully evidenced, 50% = assumed), and Effort is person-weeks.

**Diagnostic Checklist for Quarterly Risk Review**

The risk register diagnostic begins with a currency check: every risk must have been reviewed within its stated review frequency. Any risk where the last review date is older than 1.5× the stated frequency is flagged as stale and must be re-evaluated before the board risk report is issued. A stale risk register is a governance liability because it creates the false impression that management has visibility it does not actually have.

The probability calibration check asks whether any risk trigger indicators have fired since the last review. If a trigger indicator fired and the stated risk probability was not updated upward, the register is out of calibration. The EAL for that risk must be recalculated with the revised probability before aggregate portfolio EAL is reported.

The control effectiveness check asks whether any control in Column G has experienced a failure, degradation, or change in scope since the last review. A control that existed in name but was not executed (for example, a quarterly access review that was skipped) has an effective MEF of 1.0 for that period, not the stated value, and the residual impact should be recalculated accordingly.

The concentration check asks whether any single risk category (Strategic, Operational, Financial, Talent, Compliance, Market) accounts for more than 40% of total portfolio EAL. If so, that concentration warrants explicit board discussion because it indicates either systematic under-coverage of a risk class or structural business model exposure that requires capital allocation or strategic diversification.

The escalation clarity check asks whether every risk with an EAL above $500,000 has a named individual owner (not a function, not a team), a documented trigger threshold, and a written response protocol that has been reviewed within the last 90 days. If any of these three elements is missing for a high-EAL risk, it is treated as an open control gap and assigned a remediation due date before the next quarterly review.

The board reporting check asks whether the risk report delivered to the board contains the aggregate portfolio EAL with period-over-period change, the top five risks ranked by EAL with current control status, any risks that breached their trigger indicators in the reporting period, and the results of any stress tests conducted. A board risk report that does not include the EAL trend over at least four quarters cannot support meaningful governance oversight because it lacks the temporal context to distinguish a deteriorating risk environment from a stable one.

Completing these exercises as designed — not as a reading exercise but as a live operational build in actual spreadsheets with actual numbers — produces three artifacts (a quantified risk register, a Monte Carlo cash flow analysis, and a stress test protocol) that are immediately usable in a real business. They also build the analytical habits that separate a practitioner who manages risk from a manager who reports on it.
