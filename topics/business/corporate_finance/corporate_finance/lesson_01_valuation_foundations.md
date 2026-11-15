# Lesson 1: Valuation Foundations

## 1. First-Principles Intuition & Invariants

Every valuation problem in corporate finance reduces to a single, irreducible question: what is a future cash flow worth to you today? The answer depends on one insight that experienced practitioners internalize so deeply it becomes reflex — a dollar received in the future is worth less than a dollar received now. Not because of inflation alone, though inflation is part of it, but because a dollar today can be deployed immediately into productive capital: lent at interest, invested in a business, or used to retire costly debt. The opportunity cost of waiting is real, measurable, and mathematically precise. That is the time value of money, and it is the load-bearing axiom beneath every discounted cash flow model, every LBO return calculation, and every M&A purchase price negotiation you will ever conduct.

The intuition becomes a formal operator the moment you introduce a discount rate. If you possess a riskless claim on $1,000 payable in one year, and the prevailing riskless rate is 5%, then the present value of that claim is $1,000 / 1.05 = $952.38. The denominator $(1 + r)^t$ is the present value operator — the mechanical device that collapses a future number back through time. Every more complex valuation technique is simply this operator applied repeatedly, summed across multiple periods, and enriched with a principled estimate of what $r$ should be for a specific cash flow stream of a specific risk character.

It is worth pausing on what "risk" means in this context, because practitioners frequently conflate volatility, uncertainty, and credit risk in ways that corrupt their discount rates. In the classical framework descending from Irving Fisher and later formalized by Modigliani, Miller, and Sharpe, the discount rate encodes two distinct pieces of information: the pure time preference of capital (the riskless rate) and a premium demanded by investors to bear exposure to outcomes that covary with the broad economy. An asset whose cash flows move with GDP growth offers investors no hedge against systemic downturns and therefore must offer a higher expected return — which, as a present value operator, means a higher discount rate. An asset whose cash flows are orthogonal to or negatively correlated with the market carries lower systematic risk and justifies a lower rate. This is the core insight of the Capital Asset Pricing Model, and while practitioners have long argued about its empirical limitations, its logic is conceptually irreplaceable for understanding how risk gets priced into the denominator of every present value calculation.

The three invariants that govern all first-principles valuation work are worth establishing with precision before moving to mechanics.

The first invariant is **additive separability**: the present value of a stream of cash flows equals the sum of the present values of each individual cash flow. This seems obvious until you encounter practitioners who try to discount a blended average cash flow at a blended average rate, which is algebraically incorrect and produces meaningfully wrong numbers when cash flows and discount rates both vary across time.

The second invariant is **rate-period consistency**: the discount rate and the compounding period must share the same time unit. An annual discount rate applied to monthly cash flows without conversion introduces a systematic distortion. If your model receives monthly projections but your WACC is annualized at 10%, you must convert to a monthly rate: $(1.10)^{1/12} - 1 = 0.797\%$ per month, not $10\% / 12 = 0.833\%$. The difference compounds meaningfully over long projection horizons.

The third invariant is **terminal value dominance**: in almost every practical DCF on an operating business, the terminal value — the present value of all cash flows beyond the explicit projection period — constitutes 60% to 85% of total enterprise value. This is not a modeling artifact to be corrected; it is a structural property of going-concern businesses with positive growth rates. What it means for practitioners is that assumptions embedded in the terminal value (the long-run growth rate and the terminal-year normalized margin) are the dominant risk factors in the model. Getting the first three years of revenue projections exactly right while anchoring the terminal value to an unrealistic growth rate produces a number that is precise in its near-term inputs and catastrophically wrong in its conclusion.

---

## 2. Core Architecture & Mechanics

### The Present Value Operator in Full Generality

The fundamental formula admits no shortcuts in professional practice. For a discrete cash flow stream with $n$ periods:

$$PV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r)^t}$$

where $CF_t$ is the free cash flow to the firm (or equity, depending on the valuation frame) in period $t$, and $r$ is the period-consistent discount rate. When you extend this to a going concern, you append a terminal value at period $n$:

$$PV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r)^t} + \frac{TV_n}{(1 + r)^n}$$

The terminal value itself is computed using one of two methods: the Gordon Growth Model (perpetuity with growth) or an exit multiple applied to a terminal-year operating metric. The Gordon Growth Model is the theoretically cleaner approach and is defined as:

$$TV_n = \frac{CF_{n+1}}{r - g} = \frac{CF_n \cdot (1 + g)}{r - g}$$

where $g$ is the perpetual nominal growth rate of free cash flows. The constraint $r > g$ is not merely a mathematical convenience — it is an economic requirement. If a firm grew its free cash flows forever at a rate exceeding the discount rate, its present value would be infinite, which is a reductio ad absurdum that tells you the assumption itself is internally inconsistent with an equilibrium economy.

Practitioners who default to exit multiples for terminal value are essentially substituting a market-derived comparative shortcut for a first-principles perpetuity calculation. The exit multiple method applies a terminal EV/EBITDA multiple to the final-year EBITDA:

$$TV_n = EBITDA_n \times \text{Exit Multiple}$$

The professional discipline is to triangulate both methods and explain the spread. If your Gordon Growth Model terminal value implies a 10.2x EV/EBITDA multiple but comparable public companies trade at 7.5x to 8.5x, you have an assumption problem — most likely a growth rate or margin that is too generous — and the cross-check has just saved you from presenting a flawed valuation.

### Perpetuity Mathematics and Their Structural Properties

A perpetuity is a cash flow stream that pays a fixed amount in every period forever. Its present value derivation is elegant and worth understanding from the algebra rather than memorizing as a formula:

$$PV = \frac{C}{1+r} + \frac{C}{(1+r)^2} + \frac{C}{(1+r)^3} + \cdots$$

This is an infinite geometric series with first term $a = C/(1+r)$ and common ratio $k = 1/(1+r)$, so:

$$PV = \frac{a}{1-k} = \frac{C/(1+r)}{1 - 1/(1+r)} = \frac{C}{r}$$

The growing perpetuity simply introduces a growth factor $g$ on each term:

$$PV = \frac{C}{1+r} + \frac{C(1+g)}{(1+r)^2} + \frac{C(1+g)^2}{(1+r)^3} + \cdots = \frac{C}{r - g}$$

These formulas underpin the Gordon Growth Model used for terminal values, the dividend discount model used for equity valuation of mature businesses, and the capitalization rate arithmetic of commercial real estate. What practitioners frequently misapply is the timing convention: $C$ in the perpetuity formula is the cash flow arriving at the end of the first period from the valuation date, not the current-period cash flow. When computing $TV_n$, you are standing at the end of period $n$ and looking forward, so $C = CF_{n+1} = CF_n \times (1+g)$.

### Risk-Adjusted Rate Construction: Building a WACC from First Principles

The Weighted Average Cost of Capital is the discount rate appropriate for unlevered free cash flows to the firm — cash flows before financing effects but after the tax shield embedded in the firm's capital structure. Its construction requires five distinct calculations, each with specific data requirements and known failure modes.

The WACC formula in its standard form is:

$$WACC = \frac{E}{E+D} \cdot k_e + \frac{D}{E+D} \cdot k_d \cdot (1 - \tau)$$

where $E$ is equity market value, $D$ is interest-bearing debt at market value, $k_e$ is the cost of equity, $k_d$ is the pre-tax cost of debt, and $\tau$ is the marginal corporate tax rate.

**Step 1: Cost of Debt.** For an investment-grade issuer with publicly traded bonds, $k_d$ is the yield to maturity on outstanding long-duration senior unsecured debt — the blended yield you observe from market pricing, not the coupon rate from the original issuance. For a leveraged company or a private target, you infer $k_d$ from the credit spread implied by the company's leverage ratio and interest coverage, benchmarked against the leveraged loan or high-yield index appropriate for its credit quality. Using book-value coupon rates is a frequent error that understates the true cost of capital for distressed credits.

**Step 2: Cost of Equity via CAPM.** The standard CAPM construction is:

$$k_e = r_f + \beta \cdot (E[r_m] - r_f) + \text{Size Premium} + \text{Specific Risk Premium}$$

The riskless rate $r_f$ is the yield on a 10-year or 20-year US Treasury matched to the duration of the asset's expected cash flows. Using a 3-month T-bill rate introduces a maturity mismatch. The equity risk premium $(E[r_m] - r_f)$ is estimated from long-run historical data (the Damodaran database publishes annual updates showing a range of 4.5% to 6.5% for US markets depending on the estimation period) or implied from current market valuations using a reverse DCF on the S&P 500. The former is simpler; the latter is more theoretically sound in a low-rate environment.

Beta requires careful handling in private company and M&A contexts where the target has no traded equity. The professional approach is the Hamada equation, which unlevered and relevered beta to strip out capital structure differences between the subject company and its comparables:

$$\beta_L = \beta_U \cdot \left(1 + (1 - \tau) \cdot \frac{D}{E}\right)$$

You collect the levered betas of comparable public companies, unlever each one using that company's own leverage ratio and tax rate to arrive at $\beta_U$, compute the median or mean $\beta_U$ across the peer set, and then relever at the target company's capital structure. This produces a beta that reflects the business risk of the subject asset with its own financial structure — not the financial leverage of an arbitrary comparable.

**Step 3: Capital Structure Weights.** Use market values, not book values. For equity, this is straightforward: shares outstanding multiplied by the current share price. For debt, the market value is approximated by the present value of contractual cash flows discounted at the current yield — though for investment-grade issuers in normal markets, book value is a reasonable proxy. The error of using book equity — which may be negative for highly leveraged companies or deeply mature asset-heavy businesses — produces WACC calculations that are economically meaningless.

The following diagram captures the signal flow of a complete DCF model, from raw revenue projections through to equity value per share:

```
Revenue Projections (by segment, by year)
            │
            ▼
    Operating Expense Build
    (COGS, SG&A, R&D as % of revenue)
            │
            ▼
         EBITDA
            │
    Less: D&A (from PP&E schedule)
            │
            ▼
         EBIT  ──────────────────────────────────────────┐
            │                                            │
    Less: Taxes (EBIT × τ)                               │
            │                                        Tax Shield
            ▼                                        (from Debt)
        NOPAT (Net Operating Profit After Tax)            │
            │                                            │
    Plus: D&A                                            │
    Less: ΔWorking Capital                               │
    Less: Capital Expenditures                           │
            │                                            │
            ▼                                            │
    Unlevered Free Cash Flow (UFCF)         WACC embeds this implicitly
            │
            ▼
    Discount at WACC: PV(UFCF) for years 1–n
            │
    Plus: Terminal Value discounted at WACC
            │
            ▼
      Enterprise Value (EV)
            │
    Less: Net Debt
    Less: Minority Interest
    Plus: Associates / Investments
            │
            ▼
       Equity Value
            │
    Divide by: Diluted Shares Outstanding
            │
            ▼
    Intrinsic Value Per Share
```

Each arrow in this flow represents a modeling dependency that must be maintained with live cell references in a spreadsheet model. Hard-coding interim outputs is the most common execution error in analyst work and renders sensitivity analysis impossible.

### The Three-Statement Integration Requirement

A standalone DCF built on a projection of EBIT minus taxes plus D&A minus capex minus working capital changes is mechanically correct but operationally fragile. Professional-grade DCF models are anchored to a fully integrated three-statement model — income statement, balance sheet, and cash flow statement — because integration enforces an internal consistency that catch errors automatically.

The income statement drives revenue, gross profit, EBITDA, EBIT, interest expense (linked to the debt schedule), and net income. Net income flows into the balance sheet as an addition to retained earnings in equity. The cash flow statement reconciles the balance sheet change in cash by starting with net income, adding back non-cash charges, and capturing changes in working capital accounts and financing activities. When the balance sheet balances — total assets equal total liabilities plus equity — across every projected period, you have mechanical proof that no cash has been created or destroyed by modeling error.

The working capital schedule deserves particular attention because it is the most common source of free cash flow distortion in analyst models. Working capital is defined here as operating current assets minus operating current liabilities, excluding cash and short-term debt (which belong to the financing section). The key line items are accounts receivable (driven by days sales outstanding applied to revenue), inventory (driven by days inventory outstanding applied to COGS), and accounts payable (driven by days payable outstanding applied to COGS). An increase in receivables is a use of cash; an increase in payables is a source of cash. When a business grows rapidly, working capital typically increases, absorbing cash that would otherwise flow to investors — a dynamic that many simplified DCF templates ignore entirely, overstating free cash flow in high-growth scenarios.

---

## 3. High-Performance Optimization & Failure Modes

### Sensitivity Analysis as a First-Class Output

The single most important optimization a practitioner can build into a DCF model is a fully dynamic sensitivity table. Because terminal value constitutes the dominant share of enterprise value, a two-variable sensitivity table across the terminal growth rate ($g$) and the WACC produces the most decision-relevant output in any valuation. In Excel or Google Sheets, this is implemented using a Data Table with one row input cell referencing the WACC assumption and one column input cell referencing the growth rate assumption, with the output cell pointing to the enterprise value or intrinsic price per share formula. A professionally structured sensitivity table covers WACC in 25-basis-point increments from WACC − 100bps to WACC + 100bps across the columns, and $g$ in 25-basis-point increments from $g$ − 100bps to $g$ + 100bps down the rows. The resulting 9×9 matrix displays 81 distinct valuation outcomes and immediately communicates the range of reasonable enterprise value conclusions given uncertainty in the two most consequential assumptions.

Practitioners who present a point estimate from a DCF as though it were a precise answer have misunderstood what the model is for. A DCF is a machine for converting assumptions into implications. Its value is in disciplining your assumptions and understanding which levers matter most — not in producing a single number to defend in a board presentation.

### Failure Mode: Circular References in WACC Construction

The WACC formula requires capital structure weights based on market values of debt and equity. But equity market value in a DCF-derived valuation is precisely what you are trying to calculate — which creates a circular reference when WACC is used to discount cash flows that produce the equity value used in the WACC. This is not a theoretical problem; it materializes in every leveraged buyout model and any situation where target capital structure differs substantially from current capital structure.

There are two clean resolutions. The first is iteration: most spreadsheet environments can handle circular references through iterative calculation settings, where the solver recalculates until the implied equity value converges to the equity value used in the WACC. Enable this only after confirming the model logic is correct, because iterative calculation also silently absorbs other circular errors. The second, more robust approach is Adjusted Present Value (APV), which separates the unlevered firm value from the present value of financing effects. Under APV:

$$APV = V_U + PV(\text{Tax Shield}) - PV(\text{Distress Costs})$$

where $V_U$ is the value of the unlevered firm discounted at the unlevered cost of equity (cost of equity at zero leverage), and $PV(\text{Tax Shield})$ is the present value of the annual interest tax shields, discounted at the cost of debt (if the debt is permanent) or the unlevered cost of equity (if the debt follows a rebalancing policy). APV is particularly powerful in LBO models where the debt schedule is predetermined and the tax shield timing is known with high precision, because it allows you to value each financing component separately at its appropriate risk level rather than blending everything into a single WACC.

### Failure Mode: Terminal Growth Rate Anchoring Bias

The most systematic error in practitioner DCF work is selecting a terminal growth rate that is implicitly inconsistent with the macroeconomic environment. A terminal growth rate represents the nominal rate at which the subject business's free cash flows will grow in perpetuity. In an economy where long-run nominal GDP growth is approximately 4% to 5% (roughly 2% to 3% real growth plus 2% inflation), no business in a competitive market can sustain indefinite nominal growth in excess of that rate without eventually claiming an economically impossible share of the total economy. The practical ceiling for $g$ in a stable mature business is 2% to 3% nominal. For high-quality businesses with durable competitive advantages, some practitioners justify up to 3.5%, but anything beyond that in a standard going-concern DCF is implicitly assuming that the subject company will grow larger than the economy — a claim that requires explicit justification rather than quiet assumption.

The correct diagnostic is to compute the implied reinvestment rate at your terminal growth assumption. Under the two-stage DCF framework, the terminal year's return on invested capital (ROIC) and growth rate jointly imply a reinvestment rate:

$$\text{Reinvestment Rate} = \frac{g}{ROIC}$$

If your model assumes $g = 4\%$ and $ROIC = 8\%$, you are implying that the firm reinvests 50% of its NOPAT in perpetuity. If your model simultaneously shows the terminal year as a mature, cash-generative business with minimal capex needs, those two assumptions are contradictory. The reinvestment rate check forces internal consistency between growth, profitability, and cash generation that the top-line growth rate alone cannot reveal.

### Failure Mode: Nominal-Real Rate Confusion

A DCF model must be internally consistent in its treatment of inflation. Nominal cash flows — projections that include the effect of price-level changes over time — must be discounted at a nominal discount rate. Real cash flows — projections stated in today's purchasing power — must be discounted at a real discount rate. The Fisher equation defines the relationship between the two:

$$(1 + r_{nominal}) = (1 + r_{real}) \cdot (1 + \pi)$$

where $\pi$ is the expected inflation rate. Mixing frames — discounting nominal cash flows at a real WACC, or real cash flows at a nominal WACC — produces a systematic bias in present value that scales with the projection horizon. For a 10-year horizon with 2.5% inflation and a 2.5% inflation component in the WACC, this error compounds to roughly a 28% overstatement or understatement of terminal value, depending on direction. The correct discipline is to build the model entirely in nominal terms (revenue growing at nominal rates, all costs in nominal dollars, WACC constructed from nominal rate inputs) and to hold that convention consistently from the first projection period through the terminal value.

### Optimization: Mid-Period Discounting Convention

Standard DCF formulas discount all cash flows as though they arrive at the end of each period — December 31 of each projected year. For businesses with relatively smooth, recurring cash flows distributed throughout the year, this convention undervalues the asset because it ignores that some cash arrives in January, some in June, and some in December. The mid-period discounting adjustment corrects for this by treating each year's cash flow as though it arrives at the midpoint of the period rather than at year-end. The practical implementation is a simple adjustment to the discount exponent:

$$PV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r)^{t - 0.5}}$$

The $(t - 0.5)$ exponent shifts each year's discounting by half a period, increasing present values by a factor of approximately $\sqrt{1+r}$ relative to end-of-period convention. For a business with $r = 10\%$, this produces an enterprise value roughly 4.9% higher — material in any competitive auction where your valuation determines the ceiling on your bid. Mid-period discounting is standard practice in investment banking DCF analysis, and analysts who default to end-of-period convention without explicit justification are systematically undervaluing their subjects.

### Optimization: Stress-Testing the Discount Rate Against Market Implied Returns

The reverse DCF is an underused but powerful diagnostic tool that inverts the valuation question entirely. Rather than asking "what is this business worth given my cash flow projections?", it asks "what cash flow trajectory must this business sustain to justify its current market price?" You set the enterprise value equal to the company's current observed market capitalization plus net debt, then solve for the implied growth rate or margin profile that makes the model balance at the current WACC. If the implied growth rate is 25% per year for eight years from a business in a market growing at 8% per year, you have a quantitative basis for concluding the market is pricing in an outcome that requires the company to capture implausibly large market share — and that the current price embeds a materially higher risk than the discount rate alone suggests.

This technique is particularly valuable in M&A contexts. When a seller is demanding a 15x EV/EBITDA multiple for a business in a 5x to 8x peer-group trading range, running the reverse DCF on the implied premium tells you precisely what operational outperformance the buyer's model must generate to earn an acceptable return. If the implied margin expansion and growth acceleration required to justify the price exceeds what the management team has achieved historically by a factor of two, that is a data point about deal risk that belongs in the investment committee presentation — not buried in a footnote.

The arc from time value of money to full DCF construction to WACC engineering is not a progression from simple to complex; it is a progression from abstract to concrete. Every formula introduced in this lesson reappears in the LBO debt waterfalls, accretion/dilution analyses, and capital allocation frameworks of the subsequent lessons. The practitioner who can build a clean three-statement DCF from scratch, construct a WACC without lookup tables, and explain what the terminal value is actually claiming about the future of a business has acquired the foundational instrument of all corporate finance work. Everything else is a variation on this theme.
