# Lesson 4: Fixed Income Portfolio Construction and Risk Management

## 1. First-Principles Intuition & Invariants

Fixed income portfolio management begins with a deceptively simple observation: a bond is a promise. It is a legally binding commitment from a borrower to deliver a predetermined series of cash flows at specified future dates. The entire architecture of fixed income investing — from the most passive index-replication mandate to the most aggressive macro relative-value book — is built on the question of how much certainty you can extract from that promise, at what price, and over what horizon. Everything else is elaboration.

The foundational invariant of fixed income is the inverse relationship between price and yield. This is not merely a market convention; it is a mathematical identity enforced by discounted cash flow mechanics. If a 10-year Treasury bond pays a fixed 4% coupon and prevailing rates rise to 5%, the bond must trade at a discount because no rational buyer will pay par for a stream of cash flows discounted at 5% that only delivers 4% per period. The magnitude of that price change is governed by duration, and the curvature of the price-yield relationship is governed by convexity. These two measures are not abstract academic constructs; they are the core risk variables that every portfolio manager monitors in real time.

Duration, in its most useful practitioner form, is modified duration: the percentage change in bond price per 100 basis-point change in yield. A portfolio with a modified duration of 7 will lose approximately 7% in market value if rates rise by 100 basis points instantaneously across the entire curve. This linear approximation holds well for small yield moves, but for larger shocks — say, a 200 or 300 basis-point shift — the error introduced by ignoring convexity becomes material. Convexity measures the rate of change of duration itself, and positive convexity means that for large yield moves in either direction, the bond performs better than the linear duration estimate predicts. Callable bonds and mortgage-backed securities exhibit negative convexity at certain yield levels because the embedded optionality works against the holder: when rates fall far enough, prepayments accelerate or the issuer calls the bond, truncating the upside that a straight bond would otherwise enjoy.

The dollar value of a basis point, universally abbreviated DV01 (also written PVBP — price value of a basis point), translates duration into a currency-denominated risk quantity. For a $100 million portfolio with a modified duration of 6 and a price of $98.50 per $100 face value:

$$\text{DV01} = \frac{\text{Modified Duration} \times \text{Dirty Price} \times \text{Face Value}}{10{,}000}$$

$$\text{DV01} = \frac{6 \times 98.50 \times 100{,}000{,}000}{10{,}000} = \$59{,}100$$

This tells the portfolio manager that a one-basis-point move in yield will produce a $59,100 change in portfolio market value. DV01 is the lingua franca of fixed income risk desks — traders quote it, risk limits are set against it, and hedges are sized by it. When a rates desk lays on a Treasury hedge, the trade size is computed directly from the DV01 mismatch between the position and the hedge instrument.

The yield curve itself is not a single rate but a term structure — a continuously shifting surface that maps maturity to yield at every moment. Practitioners decompose curve movements into three dominant modes that together explain roughly 95% of observed variance: parallel shifts (all maturities moving by the same amount), steepening or flattening (the spread between long and short rates widening or narrowing), and butterfly twists (the belly of the curve moving relative to the wings). A portfolio that is duration-matched to its benchmark is insulated against parallel shifts but remains exposed to curvature and twist risk. This is why key rate duration, sometimes called partial duration, is so critical: it measures the price sensitivity of a portfolio to a one-basis-point move at a specific point on the curve — 2-year, 5-year, 10-year, 30-year — holding all other maturities constant. A portfolio can have the same aggregate duration as its benchmark yet carry substantial active risk if its key rate duration profile is concentrated at different maturities.

Credit risk introduces a second dimension of return and risk. The option-adjusted spread (OAS) is the constant spread added to the risk-free discount rate at every node of a binomial or trinomial interest rate tree such that the model price of a bond with embedded options equals its market price. For option-free bonds, OAS collapses to the Z-spread, which is simpler to compute: it is the constant spread over the entire benchmark spot rate curve that equates the present value of cash flows to the observed dirty price. The difference between OAS and Z-spread is entirely attributable to the value of embedded options. When you buy corporate bonds, you are selling credit protection in return for spread income, and the central portfolio construction question is whether the spread you receive compensates adequately for expected default loss, spread volatility, and liquidity risk.

Liquidity deserves its own first-principles treatment because it is chronically underpriced until it matters enormously. In fixed income, bid-ask spreads are the most visible measure of transaction cost, but they vastly understate true liquidity risk in stress scenarios. Investment-grade corporate bonds can have bid-ask spreads of 3 to 5 basis points in normal markets; during the March 2020 liquidity crunch, those spreads blew out to 50 basis points or more for nominally liquid names. Market depth — the quantity that can be transacted without moving the market — is equally important. A portfolio manager overseeing a $5 billion investment-grade mandate cannot model the execution of a $50 million block trade in a single off-the-run corporate at the mid-price. Transaction cost analysis in fixed income therefore must account for market impact, the price concession required to execute a given size, which is a function of issue size, age, credit quality, and prevailing dealer balance sheet capacity.

The invariant that ties all of this together is the law of one price, enforced through arbitrage: two instruments with identical cash flows in every state of the world must trade at the same price, or else a riskless profit opportunity exists. This principle constrains the relative pricing of Treasuries, agency bonds, and swaps through the swap spread and the basis; it constrains the pricing of on-the-run versus off-the-run Treasuries through the repo market and the specialness premium; and it constrains the pricing of bond futures relative to their cheapest-to-deliver underlying through the net basis. Every active fixed income manager, whether explicitly or implicitly, is taking a view on deviations from this law of one price and betting on their mean reversion.

---

## 2. Core Architecture & Mechanics

### Portfolio Construction: The Stratified Sampling and Optimization Engines

Fixed income portfolio construction operates on a spectrum from pure replication of an index to unconstrained active management, and the mechanical architecture differs substantially across this spectrum. Understanding the machinery at each point is essential before combining or adapting these techniques.

Passive index replication in fixed income cannot be achieved by simply purchasing every constituent of the benchmark at its index weight. A broad aggregate index like the Bloomberg U.S. Aggregate Bond Index contains over 10,000 individual securities, many of which are illiquid, expensive to source, or available only in minimum denominations that make exact weighting impossible for all but the largest institutions. The practitioner solution is stratified sampling: partition the index into risk factor cells defined by combinations of duration bucket, credit quality, sector (government, agency, investment-grade corporate, securitized), and coupon type, then purchase representative bonds from each cell in proportions that match the cell weights in the index. The objective function is to minimize tracking error — the standard deviation of the return difference between the portfolio and the benchmark — subject to practical constraints on the number of positions, minimum lot sizes, and transaction costs.

A more rigorous approach uses quadratic programming to minimize tracking error analytically. The tracking error of a portfolio relative to its benchmark is:

$$\sigma_{TE}^2 = (\mathbf{w} - \mathbf{b})^T \mathbf{\Sigma} (\mathbf{w} - \mathbf{b})$$

where $\mathbf{w}$ is the vector of portfolio weights, $\mathbf{b}$ is the vector of benchmark weights, and $\mathbf{\Sigma}$ is the factor covariance matrix. In practice, $\mathbf{\Sigma}$ is estimated from a multi-factor risk model such as Bloomberg MARS, Axioma Fixed Income, or BarraOne, which decomposes bond returns into exposure to systematic factors (level, slope, curvature, credit spread changes by sector and rating, prepayment surprises for MBS) and idiosyncratic residuals. The portfolio optimizer finds the weight vector that minimizes $\sigma_{TE}^2$ subject to whatever constraints the mandate imposes — sector tilts, duration bands, minimum credit quality, turnover limits.

Active managers extend this framework by introducing alpha views: forward-looking expectations about yield curve movements, sector spread widening or tightening, and individual issuer credit performance. The Black-Litterman model, adapted from equities, is widely used to combine these views with the prior distribution implied by the benchmark's risk premia, producing a posterior expected return vector that feeds the optimizer. The practical value of this approach is that it prevents the optimizer from making extreme concentrated bets on individual views with high expressed confidence but noisy underlying signals.

```
Active Fixed Income Portfolio Construction Flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Benchmark                  Alpha Research
  (Bloomberg                 (Macro/Credit/
   US Agg Index)              Relative Value)
       │                           │
       ▼                           ▼
  ┌─────────────────────────────────────────┐
  │   Factor Risk Model                     │
  │   (BarraOne / Bloomberg MARS)           │
  │                                         │
  │   Σ: Factor Covariance Matrix           │
  │   β: Security Factor Exposures         │
  └────────────────┬────────────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────────────┐
  │   Portfolio Optimizer (QP)              │
  │                                         │
  │   min  (w - b)ᵀ Σ (w - b)             │
  │   s.t. duration band: ± 0.5 yrs        │
  │        DV01 within risk budget          │
  │        OAS spread: benchmark ± 10bps   │
  │        sector weights: ± 5% benchmark  │
  │        min lot size: $1MM face         │
  └────────────────┬────────────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────────────┐
  │   Portfolio                             │
  │   (~150-300 bonds for $1Bn mandate)    │
  └─────────────────────────────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────────────┐
  │   Daily Risk Analytics                  │
  │   • Aggregate DV01                      │
  │   • Key Rate DV01 by tenor             │
  │   • OAS contribution by sector         │
  │   • Tracking error (ex ante)           │
  │   • Spread duration vs. benchmark     │
  └─────────────────────────────────────────┘
```

### Immunization and Dedication: Liability-Driven Construction

Immunization and dedication are the foundational techniques for liability-driven investing (LDI), where the portfolio's objective is not to outperform a market index but to fund a specific set of future liabilities with high reliability. Insurance companies funding annuity obligations, pension funds hedging their defined-benefit liabilities, and corporations pre-funding debt service sinking funds all operate in this framework.

Classical duration immunization, developed by Frank Redington in 1952, establishes three conditions for a portfolio to be immune to small, instantaneous, parallel shifts in the yield curve. First, the present value of portfolio assets must equal the present value of liabilities. Second, the duration of the asset portfolio must equal the duration of the liability stream. Third, the convexity of the asset portfolio must exceed the convexity of the liability stream. The intuition behind the third condition is subtle: it ensures that for yield moves in either direction, the asset portfolio gains more (or loses less) than the liabilities, creating a surplus cushion. A portfolio that satisfies conditions one and two but violates condition three will see its surplus erode for large yield moves in either direction — the worst of all possible outcomes for a liability-driven investor.

In practice, Redington's conditions provide protection only against parallel shifts. For a corporate pension fund with liabilities concentrated in the 15 to 30-year segment of the curve and an asset portfolio that is merely duration-matched at the aggregate level, a flattening of the 10/30 spread can produce a substantial funding ratio deterioration even though aggregate duration is matched. Modern LDI therefore matches not just aggregate duration but the full key rate duration profile of the liability stream. If 60% of the liability PV is sensitive to the 20-year point and 30% to the 30-year point, the asset portfolio's key rate durations must mirror that distribution.

Cash flow matching, often called dedication, is a more conservative alternative that eliminates interest rate risk almost entirely by purchasing bonds whose coupon and principal payments exactly match the timing and magnitude of each liability cash flow. The dedicated portfolio is constructed by working backward from the final liability: select a bond maturing at or just before the last payment date that provides sufficient cash to meet it; subtract those cash flows from the remaining liability schedule; repeat for the second-to-last liability; and continue until all liabilities are funded. The linear programming formulation of this problem minimizes the initial cost of the dedicated portfolio subject to the constraint that in every period, cumulative cash receipts plus reinvested surplus must exceed cumulative liability payments:

$$\min_{\mathbf{x}} \sum_{i} P_i x_i$$

$$\text{s.t.} \quad \sum_{i} C_{i,t} x_i + (1 + r_f) \cdot S_{t-1} \geq L_t \quad \forall t$$

where $x_i$ is the face amount of bond $i$ purchased, $P_i$ is its price, $C_{i,t}$ is its cash flow in period $t$, $S_{t-1}$ is the surplus carried from the prior period, $r_f$ is the assumed reinvestment rate on that surplus, and $L_t$ is the liability in period $t$. The practical limitation of dedication is that it locks in the full present value of liabilities at prevailing market yields and forfeits any potential for investment outperformance. For a pension fund that is already well-funded, this cost is worth paying for the certainty; for an underfunded plan, dedication can accelerate the fund's distress by eliminating any path to recovery through investment returns.

### Interest Rate Risk Management: Hedging Mechanics

Hedging interest rate risk in a fixed income portfolio is an exercise in delta-neutral construction across the yield curve. The goal is to construct an offsetting DV01 position such that for any specified yield curve movement, the net change in portfolio value approaches zero. The primary instruments for achieving this are Treasury futures, interest rate swaps, and Treasury options.

Treasury futures are the most liquid rate hedging instrument in the U.S. market. The 10-year Treasury note futures contract (TY) traded on the CME has a notional of $100,000 per contract and a DV01 of approximately $63 per basis point at par, though this varies with the cheapest-to-deliver (CTD) bond and the futures price. The hedge ratio is calculated by computing the DV01 of the position to be hedged and dividing by the DV01 of the futures contract, adjusted for the conversion factor of the CTD:

$$N = \frac{\text{DV01}_{\text{portfolio}}}{\text{DV01}_{\text{futures}}} = \frac{\text{DV01}_{\text{portfolio}}}{\text{DV01}_{\text{CTD}} / \text{CF}_{\text{CTD}}}$$

where $\text{CF}_{\text{CTD}}$ is the conversion factor of the cheapest-to-deliver bond. If the portfolio DV01 is $500,000 and the adjusted futures DV01 is $62 per contract, the manager needs to sell approximately 8,065 contracts to achieve a full hedge — a notional position of $806 million. In practice, most active managers hedge only a fraction of their duration exposure, retaining the portion that represents a deliberate alpha view on the direction of rates.

Interest rate swaps offer a more precise alternative because they can be structured to match any maturity and notional, eliminating the basis risk inherent in futures hedging. In a standard pay-fixed swap, the portfolio manager pays a fixed rate and receives SOFR (or the agreed floating rate), effectively shortening the duration of the portfolio by the present value sensitivity of the fixed leg. The DV01 of a pay-fixed $100 million 10-year swap at current market rates is approximately $80,000 to $85,000, since the fixed leg has the duration profile of a 10-year bond while the floating leg resets approximately every payment period and has minimal duration. Swaps carry counterparty credit risk (now substantially mitigated by central clearing through the LCH or CME), variation margin requirements, and additional complexity in accounting treatment under FASB ASC 815, but they are the preferred hedge for insurance companies and pension funds because they can be tailored to match liability key rate durations precisely.

### Basis Risk: The Residual That Cannot Be Eliminated

Basis risk is the residual interest rate risk that persists after a hedge has been applied, arising from the imperfect correlation between the instrument being hedged and the hedging instrument. In fixed income, basis risk manifests across several distinct channels, and experienced portfolio managers track each separately.

The swap-Treasury basis, often called the swap spread, is the difference between the fixed rate on an interest rate swap and the yield on the on-the-run Treasury of matching maturity. This spread is not constant — it widens during periods of credit stress and financial market volatility (as corporate counterparty risk premia increase), tightens during periods of abundant central bank liquidity, and can even go negative (as it did persistently in the post-2008 era for maturities beyond 10 years) due to regulatory balance sheet constraints on dealers. A portfolio manager who hedges a corporate bond position with Treasury futures retains exposure to the swap spread and to the OAS of the bond itself — neither of which is captured by the duration hedge.

The futures basis is the difference between the market price of a bond and its theoretical futures delivery value. For Treasury futures, this is defined as:

$$\text{Basis} = \text{Cash Price} - (\text{Futures Price} \times \text{Conversion Factor})$$

The gross basis reflects the full carry advantage of holding the cash bond and financing it in repo versus holding the futures contract, plus the value of the delivery options embedded in the futures contract (the option to choose which bond to deliver, when to deliver during the delivery month, and the accrued interest wild-card play). The net basis, also called the option-adjusted basis or OAB, isolates the value of the delivery options by subtracting the carry:

$$\text{Net Basis} = \text{Gross Basis} - \text{Carry}$$

A portfolio manager who is long cash bonds and short futures to hedge has sold the delivery options embedded in the contract — a negative convexity position that is typically fairly priced but can produce unexpected losses if volatility spikes and the value of those options rises sharply.

---

## 3. High-Performance Optimization & Failure Modes

### Performance Attribution: Decomposing Returns to Their Sources

Performance attribution is the analytical process of explaining the difference between a portfolio's actual return and its benchmark return in terms of specific investment decisions. Without rigorous attribution, a portfolio manager cannot distinguish skill from luck, cannot identify which strategies are generating alpha, and cannot communicate meaningfully with clients or oversight committees. For fixed income, attribution is more complex than equity attribution because bond returns decompose into multiple distinct and partially correlated components.

The Campisi attribution model, widely regarded as the most practically useful framework for fixed income, decomposes total return into five components. The income return is the coupon income earned over the measurement period, divided by the beginning market value. The Treasury return is the return attributable to the change in Treasury yields (the pure interest rate component), calculated by repricing the portfolio using yield changes in the benchmark Treasury curve and isolating this effect. The spread return is the return attributable to changes in the OAS of each bond, holding Treasury yields constant. The currency return applies for unhedged or partially hedged mandates. And the residual captures trading gains, timing effects, and anything not explained by the first four components.

For a U.S. investment-grade portfolio measured over a one-month period, a sample attribution might look like this: the benchmark returned +0.42%, while the portfolio returned +0.67%, producing 25 basis points of outperformance. The attribution reveals that the income return contributed +35 basis points (identical for both portfolio and benchmark, assuming similar coupon profiles), the Treasury return contributed −18 basis points (rates rose slightly, hurting both), the spread return contributed +20 basis points for the portfolio versus +10 basis points for the benchmark (the portfolio's overweight to financials tightened more than the benchmark's sector allocation implied), and security selection within the industrial sector contributed +8 basis points of residual alpha from specific issuer spread compression. This level of decomposition tells the manager exactly where the outperformance was generated and whether it is attributable to a systematic structural tilt or to genuine security-level insight.

Formally, the spread return for a single bond is approximated as:

$$R_{\text{spread}} \approx -\text{Spread Duration} \times \Delta\text{OAS}$$

For a portfolio, this aggregates across all holdings weighted by market value. A portfolio overweight to 10-year BBB-rated corporate bonds relative to its benchmark, with a spread duration of 8 on that overweight, will gain approximately 8 basis points per basis point of OAS tightening in that sector — and lose the same for each basis point of widening. The spread duration of an overweight is therefore the risk quantity that governs the volatility of the credit alpha component in the attribution.

The key rate attribution variant extends this decomposition to the yield curve dimension by attributing Treasury return to each key rate separately. A portfolio with a deliberate overweight to the 2-year point relative to its benchmark will show positive attribution from the 2-year key rate return if the 2-year yield falls, and negative attribution if it rises. This granularity is essential for evaluating curve positioning strategies: a manager who flattened the portfolio (overweight the long end, underweight the short end) and was correct will see positive 10-year and 30-year key rate contributions offset by negative 2-year and 5-year contributions, with the net being the flattening trade's P&L.

### Failure Modes and Structural Vulnerabilities

The most consequential failure mode in fixed income portfolio management is the assumption of yield curve parallelism embedded in simple duration hedging. In practice, the yield curve rarely shifts in parallel; it twists, flattens, steepens, and humps, and a portfolio hedged purely on aggregate duration can suffer substantial losses from these non-parallel movements. The October 2023 bond market episode illustrates this vividly: the 10-year Treasury yield rose by over 100 basis points between August and October, but the move was disproportionately concentrated in real yields and in the 10 to 30-year segment of the curve. Portfolios that had duration-matched using short-duration instruments to reach their aggregate target — a common strategy when the 2-year/10-year curve was deeply inverted — found their hedges dramatically underperforming relative to expectations because the shape of the move violated the parallel-shift assumption embedded in their hedging ratios.

Convexity drift is a subtler but persistent failure mode. As rates move, the duration of a bond changes, meaning that a hedge that was correctly sized at the beginning of a period becomes mis-sized as the period progresses. This requires dynamic rebalancing — the frequency of which must be calibrated against transaction costs. A portfolio manager who rebalances duration daily will incur substantial transaction costs in a volatile rate environment; one who rebalances monthly may allow the hedge ratio to drift to a point where it provides inadequate protection during a large intramonth rate move. The practitioner solution is a threshold-based rebalancing rule: rebalance when the DV01 mismatch between portfolio and benchmark (or hedge) exceeds a specified dollar threshold, say $10,000, rather than on a fixed calendar schedule.

Liquidity crises expose the fundamental tension between mark-to-market accounting and investment horizon. When corporate bond spreads widen sharply — as in March 2020 or the fourth quarter of 2018 — the manager who is forced to sell into a dislocated market to meet redemptions realizes losses that the manager who can hold to maturity (or at least to spread normalization) will recoup through carry. This dynamic is the core argument for matching portfolio liquidity to the liquidity of the underlying investor base. An open-end bond mutual fund holding significant allocations to leveraged loans, high-yield bonds, or BBB-rated private placements is structurally vulnerable to run risk: investors can redeem daily at NAV, forcing asset sales at distressed prices that further depressNAV, triggering further redemptions in a classic negative feedback spiral. The 2019 suspension of the Woodford Equity Income Fund and the 2022 LDI crisis in the U.K. gilt market, where pension funds faced margin calls on leveraged rate swaps, are extreme examples of liquidity mismatch overwhelming otherwise sound structural strategies.

Model risk in fixed income is particularly acute for instruments with embedded optionality. MBS prepayment models — the engines that convert observed interest rate paths into projected cash flow scenarios for mortgage-backed securities — are notoriously sensitive to behavioral assumptions about borrower refinancing and default rates. During the 2003 mortgage refinancing wave, prepayment speeds on many agency MBS pools ran 300 to 400% of their PSA benchmark speed as millions of borrowers refinanced simultaneously, devastating investors who had purchased premium-priced bonds expecting gradual paydown. OAS models for callable corporate bonds are equally sensitive to volatility inputs: a corporate bond callable in five years at par has an OAS that changes materially depending on whether the model uses 60 basis points or 80 basis points of implied rate volatility in the binomial tree. If the volatility surface used to price the bond is inconsistent with the volatility embedded in the swaption market, the OAS will be systematically biased, and the apparent spread pickup will be an illusion masking underpriced optionality.

Tracking error targeting introduces its own failure mode: the optimizer's tendency to reach for marginal tracking error reduction through concentrated positions in recently high-performing assets, precisely when those assets are most likely to mean-revert. A well-calibrated covariance matrix is crucial, but historical covariance matrices are inherently backward-looking and compress dramatically during risk-off episodes because correlations collapse toward one — all spread products sell off together, eliminating the diversification that the matrix predicted. Many practitioners therefore augment historical covariance estimation with stress-tested scenarios: explicitly modeling portfolio behavior under a 2008-style credit freeze, a 1994-style rate shock, and a 2020-style liquidity crunch, treating these as binding constraints on allowable portfolio construction rather than as tail risks to be monitored passively.

### Practical Workflow: Running the Full Portfolio Process

Pulling these mechanics together into a practitioner workflow, consider how a $2 billion investment-grade corporate bond portfolio is managed on a day-to-day basis. The morning begins with the overnight P&L attribution and risk report, which shows the portfolio's DV01 by key rate bucket relative to the benchmark, the OAS contribution by sector, and the ex-ante tracking error from the risk model. The portfolio manager reviews whether any of these have drifted outside their active risk budget — perhaps overnight Treasury yields rose 5 basis points on a strong payrolls number, moving the duration slightly short relative to the benchmark, or a large new issue in the financial sector created an index weight change that the portfolio has not yet reflected.

The core decision is whether to act on observed deviations. For a 3-basis-point duration drift, the transaction cost of rebalancing almost certainly exceeds the expected risk benefit for a mandate with a 25-basis-point tracking error target — the signal-to-noise ratio is unfavorable. For a 15-basis-point drift, the manager may need to add duration by purchasing longer bonds or receiving fixed on a swap. If a new IG corporate bond is pricing in the primary market — a $1 billion 10-year issue from a single-A-rated industrial — the manager must run three analyses simultaneously: does the new issue represent fair value relative to the issuer's existing curve and comparable peers (spread analysis using CDS basis and Z-spread comparison), does participating in the issue bring the portfolio's sector and credit allocation closer to the optimal active tilt (portfolio fit analysis), and can the position be executed at the expected concession given order book dynamics and minimum allocation sizes (transaction mechanics)?

By the end of the trading day, all executed trades are reconciled against the order management system, the new DV01 and OAS profile is recalculated on the post-trade portfolio, and the daily P&L is decomposed into income, rate, and spread components for the attribution log. This attribution log, accumulated over a quarter, becomes the input to the QBR with the oversight committee or investment consultant — an evidence-based narrative of exactly which decisions generated alpha, in what size, and with what consistency. That is the standard to which every element of this workflow is ultimately held accountable.
