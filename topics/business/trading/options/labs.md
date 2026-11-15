# Operational Verification Labs: Options

## Objective & Operational Lab Setup

These laboratories construct the operational competence required to price, hedge, and manage options positions in live trading environments. The exercises progress from single-option valuation mechanics through multi-leg strategy construction, volatility surface calibration, and real-time risk management under market stress. Each lab delivers a working analytical artifact—pricing model, risk calculator, or portfolio simulator—that mirrors institutional trading desk infrastructure.

Options markets demand precision in three operational dimensions: valuation accuracy under stochastic volatility, delta-hedging execution to neutralize directional risk, and P&L attribution across Greeks when markets move. Traders who master these mechanics convert theoretical edge into realized profit; those who operate on intuition alone face systematic losses from mispriced volatility, unhedged gamma exposure, and failed risk limits. These labs drill the quantitative rigor and tool fluency that separate professional market makers from retail speculators.

The laboratory environment requires a spreadsheet application with programmatic calculation capability (Microsoft Excel with VBA, Google Sheets with Apps Script, or LibreOffice Calc with Python integration), a statistical computing environment (Python with NumPy/SciPy/Pandas, R, or MATLAB), and access to historical options data (CBOE DataShop, OptionMetrics, or broker API feeds). For real-time simulation, a paper trading account with options approval provides live market data and order execution without capital risk. The setup mirrors a junior trader's workstation: analytical tools for pricing and risk, market data for calibration, and execution infrastructure for strategy implementation.

Begin by constructing a foundational Black-Scholes-Merton pricing model in spreadsheet form. This single-option calculator becomes the reference engine for all subsequent labs, establishing the mechanical relationship between spot price, strike, time to expiration, risk-free rate, dividend yield, and implied volatility. The model outputs option premium, the five primary Greeks (delta, gamma, vega, theta, rho), and break-even spot levels at expiration. Every parameter change triggers immediate recalculation, allowing rapid exploration of how options respond to market shifts. This hands-on interaction builds intuition for non-linear payoffs, time decay acceleration, and volatility sensitivity—concepts that remain abstract until operationalized through direct manipulation.

Establish a standardized options data schema to maintain consistency across exercises. Each option record contains underlying symbol, contract type (call or put), strike price, expiration date, bid price, ask price, mid-market price, implied volatility, open interest, and volume. Historical data includes daily snapshots of these fields plus the underlying spot price, risk-free rate proxy (appropriate Treasury yield), and dividend yield. Organize data in relational tables or structured CSV files, not scattered across ad-hoc spreadsheets. This discipline prevents the data integrity failures that corrupt institutional risk systems during market dislocations.

The laboratories operate under a simulated trading mandate: manage a $1,000,000 options portfolio with maximum 10% value-at-risk at 95% confidence, position size limits of $50,000 per contract, and delta-hedged exposure maintained within ±5 delta per $100,000 portfolio value. These constraints mirror sell-side market maker risk limits and force realistic trade-offs between premium collection, hedging cost, and tail risk. Each exercise tracks realized P&L against theoretical edge, exposing the execution slippage and Greek mis-estimation that erode trading profits in practice.

Proceed through the three core exercises sequentially, as each builds mechanical dependency on prior work. The first exercise establishes single-option valuation and Greek calculation infrastructure. The second exercise extends this foundation to multi-leg strategies with cross-Greek interactions and portfolio-level risk aggregation. The third exercise introduces volatility surface dynamics, correlation breakdown, and margin pressure scenarios that reveal when standard risk models fail. Complete each lab by documenting model assumptions, calibration methodology, and operational constraints in a structured reference guide that functions as a trading desk runbook.

## Exercise 1: Foundational Practical Implementation

Construct a complete Black-Scholes-Merton options pricing model in spreadsheet form, capable of valuing European calls and puts with continuous dividend yield and generating the five primary Greeks. This exercise operationalizes the closed-form solution to the stochastic differential equation governing geometric Brownian motion, translating abstract probability theory into working valuation infrastructure. The model accepts six observable inputs—underlying spot price S, strike price K, time to expiration τ (in years), risk-free rate r, dividend yield q, and implied volatility σ—and returns option premium C (call) or P (put) plus delta Δ, gamma Γ, vega ν, theta Θ, and rho ρ.

Begin by implementing the cumulative standard normal distribution function Φ(x), as the Black-Scholes formula depends on evaluating Φ(d₁) and Φ(d₂) where d₁ and d₂ are intermediate log-moneyness terms adjusted for drift and volatility. Most spreadsheet applications provide a native function: `NORM.S.DIST(x, TRUE)` in Excel, `NORMSDIST(x)` in Google Sheets. For environments lacking this function, implement the Abramowitz and Stegun polynomial approximation with absolute error below 7.5×10⁻⁸, sufficient for all practical trading applications. The approximation evaluates Φ(x) ≈ 1 - φ(x)(a₁k + a₂k² + a₃k³ + a₄k⁴ + a₅k⁵) for x ≥ 0, where φ(x) is the standard normal density (2π)⁻¹/² exp(-x²/2), k = 1/(1 + γx), γ = 0.2316419, and coefficients (a₁, a₂, a₃, a₄, a₅) = (0.319381530, -0.356563782, 1.781477937, -1.821255978, 1.330274429). Extend to x < 0 using symmetry: Φ(-x) = 1 - Φ(x).

Construct the log-moneyness terms d₁ and d₂ as intermediate calculations before evaluating call and put premiums. Define d₁ = [ln(S/K) + (r - q + σ²/2)τ] / (σ√τ) and d₂ = d₁ - σ√τ. These expressions capture the drift-adjusted probability that the option finishes in the money under the risk-neutral measure, scaled by volatility and time. In spreadsheet cells, separate each component—natural logarithm of moneyness ln(S/K), drift term (r - q + σ²/2)τ, volatility scaling σ√τ—as intermediate values for transparency and error checking. Spreadsheet formula for d₁ in cell F2, given inputs S (A2), K (B2), τ (C2), r (D2), q (E2), σ (G2): `=(LN(A2/B2) + (D2 - E2 + G2^2/2)*C2) / (G2*SQRT(C2))`. Cell F3 for d₂: `=F2 - G2*SQRT(C2)`.

Evaluate call premium C using the Black-Scholes formula C = S·exp(-qτ)·Φ(d₁) - K·exp(-rτ)·Φ(d₂). The first term represents the present value of expected stock receipt if exercised, discounted by dividend yield (the holder foregoes dividends). The second term represents the present value of expected strike payment, discounted at the risk-free rate. Spreadsheet formula in cell H2: `=A2*EXP(-E2*C2)*NORM.S.DIST(F2, TRUE) - B2*EXP(-D2*C2)*NORM.S.DIST(F3, TRUE)`. Evaluate put premium P using put-call parity P = C - S·exp(-qτ) + K·exp(-rτ), which is algebraically equivalent to the direct formula P = K·exp(-rτ)·Φ(-d₂) - S·exp(-qτ)·Φ(-d₁) but computationally more stable for deep in-the-money puts. Spreadsheet formula in cell I2: `=H2 - A2*EXP(-E2*C2) + B2*EXP(-D2*C2)`.

Implement the five Greeks as partial derivatives of the option premium with respect to input parameters. Delta measures sensitivity to spot price changes: Δ_call = exp(-qτ)·Φ(d₁), Δ_put = -exp(-qτ)·Φ(-d₁) = Δ_call - exp(-qτ). Spreadsheet formula for call delta in cell J2: `=EXP(-E2*C2)*NORM.S.DIST(F2, TRUE)`. Put delta in cell K2: `=J2 - EXP(-E2*C2)`. Gamma measures delta sensitivity to spot changes (convexity): Γ = exp(-qτ)·φ(d₁)/(S·σ√τ), identical for calls and puts. Spreadsheet formula in cell L2: `=EXP(-E2*C2)*NORM.S.DIST(F2, FALSE) / (A2*G2*SQRT(C2))`, where `NORM.S.DIST(F2, FALSE)` evaluates the standard normal density φ(d₁).

Vega measures sensitivity to volatility changes: ν = S·exp(-qτ)·φ(d₁)·√τ, again identical for calls and puts. Spreadsheet formula in cell M2: `=A2*EXP(-E2*C2)*NORM.S.DIST(F2, FALSE)*SQRT(C2)`. Note that vega is often quoted per 1% volatility change (σ shift of 0.01), so divide by 100 for basis-point sensitivity or scale output accordingly. Theta measures time decay: Θ_call = -[S·φ(d₁)·σ·exp(-qτ)/(2√τ)] + q·S·Φ(d₁)·exp(-qτ) - r·K·exp(-rτ)·Φ(d₂). Spreadsheet formula in cell N2: `=-(A2*NORM.S.DIST(F2, FALSE)*G2*EXP(-E2*C2)/(2*SQRT(C2))) + E2*A2*NORM.S.DIST(F2, TRUE)*EXP(-E2*C2) - D2*B2*EXP(-D2*C2)*NORM.S.DIST(F3, TRUE)`. Put theta uses Θ_put = Θ_call - q·S·exp(-qτ) + r·K·exp(-rτ). Theta is conventionally quoted as daily decay (per-calendar-day change), so divide by 365 if τ is measured in years.

Rho measures sensitivity to interest rate changes: ρ_call = K·τ·exp(-rτ)·Φ(d₂), ρ_put = -K·τ·exp(-rτ)·Φ(-d₂). Spreadsheet formula for call rho in cell O2: `=B2*C2*EXP(-D2*C2)*NORM.S.DIST(F3, TRUE)`. Rho is the least significant Greek for short-dated equity options but becomes material for long-dated options and interest rate derivatives. Scale rho output per 1% rate change (r shift of 0.01) for intuitive interpretation.

Validate the model against published option quotes by sourcing a reference trade: SPY (S&P 500 ETF) call option, strike $450, expiring in 30 calendar days, when SPY trades at $455. Use current 1-month Treasury yield as risk-free rate (assume 4.50% = 0.045), SPY dividend yield approximately 1.30% (0.013), and solve for implied volatility σ such that the model call premium matches the market mid-price. If the market quote is $8.50 bid / $8.70 ask (mid $8.60), iterate σ until the model output C equals $8.60 within $0.01 tolerance. This reverse-engineering process—solving for the volatility input that reconciles model price to market price—defines implied volatility, the market's forward-looking assessment of realized volatility over the option's life.

Implement implied volatility calculation using Newton-Raphson root-finding. The objective function is f(σ) = C_model(σ) - C_market, and the derivative is f'(σ) = ν (vega). The iteration formula is σ_new = σ_old - f(σ_old)/ν(σ_old). Initialize σ at a reasonable guess (0.20 for equity options), compute call premium and vega, update σ, and repeat until |f(σ)| < 0.01 or 10 iterations elapse. In spreadsheet VBA, implement as a custom function `ImpliedVolatilityCall(S, K, tau, r, q, C_market)` that encapsulates this loop. For Google Sheets Apps Script, write a parallel custom function. This capability transforms the pricing model into a two-way tool: forward pricing given volatility, or implied volatility extraction given market price.

Extend the model to handle American options via binomial tree approximation, as closed-form solutions exist only for European exercise. Construct a Cox-Ross-Rubinstein (CRR) binomial tree with N time steps (start with N = 100 for 30-day options), where the underlying moves up by factor u = exp(σ√Δt) or down by d = 1/u each step, with risk-neutral probability p = [exp((r - q)Δt) - d] / (u - d), where Δt = τ/N. At expiration (step N), option value is intrinsic: max(S - K, 0) for calls, max(K - S, 0) for puts. Step backward through the tree, computing option value at each node as the discounted expected value under the risk-neutral measure, but enforce early exercise: V(node) = max(intrinsic, exp(-rΔt)[p·V(up) + (1-p)·V(down)]). The American premium emerges at the root node (step 0).

Implement the binomial tree in a separate spreadsheet tab with N+1 columns (time steps) and N+1 rows (price levels at final step). Initialize spot price S₀ at the root, compute u and d, and propagate prices forward: S(i,j) = S₀·uʲ·dⁱ⁻ʲ where i is the step number (0 to N) and j is the up-move count (0 to i). Populate the final column with intrinsic values, then iterate backward column-by-column, row-by-row, applying the continuation vs. exercise comparison. This brute-force approach is computationally expensive (O(N²) complexity) but conceptually transparent and fully general for any payoff structure.

For the foundational exercise, price the following reference options using your completed Black-Scholes model and binomial tree American extension:

1. **SPY European Call**: S = $455.00, K = $450.00, τ = 30/365 = 0.0822 years, r = 0.045, q = 0.013, σ = 0.18. Compute call premium, all five Greeks, and implied volatility by reverse-engineering the model premium as "market" input.

2. **SPY American Put**: S = $455.00, K = $460.00, τ = 30/365, r = 0.045, q = 0.013, σ = 0.18. Compare European put premium (Black-Scholes) vs. American put premium (binomial tree, N = 100). Quantify the early exercise premium (American - European).

3. **AAPL European Call**: S = $185.00, K = $190.00, τ = 60/365 = 0.1644 years, r = 0.045, q = 0.005, σ = 0.30. Compute call premium and Greeks. Observe higher vega and theta magnitude vs. SPY due to longer maturity and higher volatility.

4. **GLD American Call (gold ETF)**: S = $195.00, K = $200.00, τ = 90/365 = 0.2466 years, r = 0.045, q = 0.000 (gold pays no dividend), σ = 0.16. Compare European vs. American call premium. Verify that American ≈ European for calls on non-dividend-paying assets (early exercise never optimal).

Compile a summary table with columns: Underlying, Contract Type, Strike, Expiration, European Premium, American Premium (if applicable), Delta, Gamma, Vega, Theta, Rho. Validate that call delta ranges (0, 1), put delta ranges (-1, 0), gamma is always positive, vega is always positive, theta is typically negative for long options, and rho is positive for calls, negative for puts. These sign conventions are foundational; violations indicate implementation errors.

Document model assumptions and limitations in a structured appendix. The Black-Scholes-Merton framework assumes continuous trading, no transaction costs, constant volatility and interest rates, log-normal price diffusion, and European exercise. Real markets violate all these assumptions: volatility exhibits term structure and skew, jumps occur during earnings and macro events, transaction costs and margin requirements constrain hedging, and American options dominate equity markets. The model nonetheless provides a reference price and risk sensitivities that traders adjust via bid-ask spreads, volatility surface interpolation, and jump overlays. Understanding where the model breaks down is as critical as mastering its mechanics.

Finalize the foundational implementation by stress-testing the model's numerical stability. Test extreme inputs: very deep in-the-money (S/K = 2.0), very deep out-of-the-money (S/K = 0.5), very short expiration (τ = 1/365), very long expiration (τ = 2.0), very low volatility (σ = 0.05), very high volatility (σ = 1.00). Verify that the model does not produce negative premiums, delta outside [-1, 1], or other violations of arbitrage bounds. For near-expiry options (τ < 0.01), the model may exhibit numerical noise in Greeks; this reflects the reality that options approaching expiration become binary bets where small spot moves trigger large delta swings. Traders respond by widening markets and reducing position size in the final days before expiration.

## Exercise 2: Parameter Variation & Empirical Analysis

Construct a multi-leg options strategy analyzer that aggregates individual option positions into portfolio-level Greeks, computes P&L attribution across risk factors, and simulates strategy performance under systematic spot and volatility shifts. This exercise operationalizes the superposition principle for linear Greek exposures and exposes the non-linear interactions (gamma-theta trade-offs, vega-gamma correlations) that govern complex position risk. The analyzer ingests a position file specifying each leg's contract details, quantity (positive for long, negative for short), and entry premium, then outputs aggregated Greeks, break-even spot levels, maximum profit/loss, and P&L scenarios for a grid of market outcomes.

Begin by defining a standardized position file format as a CSV with columns: Symbol, Contract Type (C/P), Strike, Expiration Date, Quantity, Entry Premium, Current Implied Vol. Example position for an iron condor on SPY:

```
Symbol,Type,Strike,Expiration,Quantity,EntryPremium,ImpliedVol
SPY,P,440,2025-03-21,-10,2.15,0.16
SPY,P,445,2025-03-21,10,3.40,0.17
SPY,C,465,2025-03-21,10,3.20,0.17
SPY,C,470,2025-03-21,-10,1.95,0.16
```

This iron condor sells the 440/445 put spread and the 465/470 call spread, collecting net premium (10×3.40 - 10×2.15 + 10×3.20 - 10×1.95) × 100 = $6,500 (options are quoted per share but trade in 100-share contracts). The position profits if SPY remains between 445 and 465 at expiration, loses maximum $5,000 if SPY closes below 440 or above 470, and breaks even at approximately 445 + 0.65 = 445.65 and 465 - 0.65 = 464.35.

Load the position file into a spreadsheet or Python script, iterate through each row, and invoke the Black-Scholes pricing model from Exercise 1 to compute current Greeks for each leg. For the first leg (short 10 puts, strike 440), evaluate put premium and Greeks at current spot S (assume $455), current date (30 days to expiration), current risk-free rate (4.5%), dividend yield (1.3%), and leg-specific implied volatility (16%). Multiply each Greek by the leg quantity and contract multiplier (100): portfolio contribution is -10 × 100 × Δ_leg for delta, -10 × 100 × Γ_leg for gamma, etc. Aggregate across all four legs to compute portfolio-level Greeks: Δ_portfolio = Σ(Quantity × 100 × Δ_leg), and similarly for gamma, vega, theta, rho.

Compute aggregated Greeks for the iron condor example. With SPY at $455, the short 440 put (15 points out-of-the-money) has low delta (approximately -0.10) and low gamma; the long 445 put (10 points OTM) has slightly higher delta (-0.15); the long 465 call (10 points OTM) has delta (+0.15); the short 470 call (15 points OTM) has delta (+0.10). Net portfolio delta is approximately -10×100×(-0.10) + 10×100×(-0.15) + 10×100×(0.15) + (-10)×100×(0.10) = +100 - 150 + 150 - 100 = 0. The position is delta-neutral by construction, as both spreads are symmetric around the current spot. Portfolio gamma is negative (short gamma), as the position is short options at strikes closer to the money (445 and 465) relative to the strikes farther away (440 and 470). Portfolio theta is positive (long theta), earning time decay as the sold options erode faster than the purchased options. Portfolio vega is negative (short vega), losing value if volatility rises.

Implement a P&L attribution engine that decomposes portfolio value changes into contributions from delta (spot movement), gamma (spot convexity), vega (volatility shift), and theta (time decay). The first-order P&L approximation is ΔP&L ≈ Δ·ΔS + ½Γ·(ΔS)² + ν·Δσ + Θ·Δt, where ΔS is the spot price change, Δσ is the implied volatility change (in absolute terms), and Δt is the time elapsed. This Taylor expansion captures the dominant risk factors but omits higher-order cross-Greeks (vanna, volga, charm) and correlation effects. For single-day P&L attribution, the approximation typically explains 95%+ of realized P&L; for large moves or multi-day periods, re-pricing each leg at the new market state provides exact P&L.

Build a scenario analysis matrix that computes P&L for a grid of (spot, volatility) outcomes. Define spot range from -10% to +10% in 2% increments (11 scenarios), and volatility range from -5 points to +5 points in 1-point increments (11 scenarios), yielding a 11×11 = 121-cell matrix. For each cell (S_scenario, σ_scenario), re-price all four iron condor legs using the Black-Scholes model with updated spot and volatility, compute new portfolio value, and subtract initial portfolio value to determine P&L. Present the matrix as a heatmap with spot scenarios on the x-axis, volatility scenarios on the y-axis, and cell color intensity representing P&L magnitude (green for profit, red for loss).

Interpret the iron condor P&L surface. At current spot ($455) and volatility (17%), the position has been established for net credit $6,500, so current P&L is approximately $0 (ignoring mark-to-market on the individual legs). As spot drifts toward the break-even points (445.65 or 464.35), time decay accumulates positive theta P&L, but adverse spot movement generates negative delta-gamma P&L. If spot remains near $455, the position profits maximally at expiration (full $6,500 credit retained). If spot moves to $440 or $470, the position loses the spread width minus credit ($50,000 - $6,500 = $43,500 per spread, totaling $5,000 loss as one spread expires worthless and the other reaches maximum loss of $50,000 - $6,500 = $43,500, wait, recompute: iron condor max loss is spread width minus net credit = $5 - $0.65 = $4.35 per share × 1000 shares = $4,350). Correct computation: max loss occurs when spot closes outside either spread. For the put spread, max loss is (445 - 440 - net put credit) × 1000 = ($5 - $1.25) × 1000 = $3,750. For the call spread, max loss is (470 - 465 - net call credit) × 1000 = ($5 - $1.25) × 1000 = $3,750. Total iron condor max loss is $3,750 (one spread loses, the other expires worthless, but the condor's max loss is limited to the width minus credit of the breached spread). Verify by pricing at expiration: if S = $440, the 440/445 put spread is worth $5, costing $5,000 to close, minus $3,400 collected on entry, net loss $1,600. The call spread expires worthless, contributing $3,200 credit. Net position P&L is -$1,600 + $3,200 = $1,600 profit. Wait, this contradicts standard iron condor mechanics; recompute carefully.

Iron condor components: short 440 put collected $2.15, long 445 put paid $3.40, net debit $1.25 per share × 1000 = $1,250 for put spread. Short 465 call collected $3.20, long 470 call paid $1.95, net credit $1.25 per share × 1000 = $1,250 for call spread. Total net credit for full iron condor is $1,250 (call spread) - $1,250 (put spread) = $0. This is unusual; recalculate entry premiums to ensure net credit. Typical iron condor sells both spreads for net credit. Adjust example: short 440 put at $2.15, long 445 put at $3.40 means paying $1.25 net (debit spread). This is incorrect for an iron condor leg. Correct structure: sell 445 put at $3.40, buy 440 put at $2.15, collect $1.25 credit. Sell 465 call at $3.20, buy 470 call at $1.95, collect $1.25 credit. Total credit $2.50 per share × 1000 shares = $2,500. Max loss occurs if spot closes below 440 or above 470: the threatened spread reaches max loss of spread width = $5 per share × 1000 = $5,000, minus the $2,500 credit collected, net loss $2,500.

Rebuild the position file with corrected iron condor structure:

```
Symbol,Type,Strike,Expiration,Quantity,EntryPremium,ImpliedVol
SPY,P,445,2025-03-21,-10,3.40,0.17
SPY,P,440,2025-03-21,10,2.15,0.16
SPY,C,465,2025-03-21,-10,3.20,0.17
SPY,C,470,2025-03-21,10,1.95,0.16
```

Negative quantity indicates short position (sold option), positive indicates long position (purchased option). Net credit is (3.40 + 3.20 - 2.15 - 1.95) × 10 contracts × 100 shares = $2,500. Max profit is the net credit $2,500 if SPY closes between 445 and 465. Max loss is $2,500 if SPY closes outside 440–470 range (one spread reaches $5 width, costing $5,000, minus $2,500 credit, net -$2,500). Break-even points are 445 - 0.25 = 444.75 on downside, 465 + 0.25 = 465.25 on upside.

Compute Greeks for the corrected iron condor. The short 445 put and short 465 call have highest absolute delta (approximately ±0.30 each), while the long 440 put and long 470 call have lower delta (±0.15). Net portfolio delta is -10×100×(-0.30) + 10×100×(-0.15) + (-10)×100×(0.30) + 10×100×(0.15) = +300 - 150 - 300 + 150 = 0. Portfolio gamma is negative, concentrated at the short strikes (445 and 465) where gamma peaks. Portfolio vega is negative, approximately -10×100×(ν₄₄₅_put + ν₄₆₅_call) + 10×100×(ν₄₄₀_put + ν₄₇₀_call). Since ATM options have highest vega and the short strikes are closer to ATM, the position is net short vega. Portfolio theta is positive, as the short options decay faster than the long options due to higher gamma.

Execute the scenario analysis matrix for the iron condor. Populate a spreadsheet with spot scenarios from $440 to $470 in $3 increments (11 scenarios), and volatility scenarios from 12% to 22% in 1% increments (11 scenarios). For each of the 121 cells, reprice all four legs and compute total position value minus initial credit of $2,500. Observe that P&L is maximized when spot remains between 445 and 465 and volatility declines (positive theta plus vega contraction). P&L is minimized when spot breaches 440 or 470 thresholds and volatility spikes (short spreads reach max loss, exacerbated by negative vega). The P&L surface resembles a plateau with steep cliffs at the break-even points, characteristic of short-volatility income strategies.

Extend the analyzer to compute portfolio margin requirements under Regulation T initial margin (50% of underlying value for uncovered options, reduced for defined-risk spreads) and SPAN margining (portfolio-based risk assessment). For the iron condor, Regulation T margin is the maximum loss of either spread, $2,500, since the spreads are defined-risk and cannot lose more than the width minus credit. SPAN margin evaluates the portfolio across 16 scenarios (spot ±3 standard deviations, volatility ±volatility of volatility) and charges the worst-case loss, typically similar to the defined-risk maximum. Margin efficiency improves with tighter spreads and higher credit collected, incentivizing traders to sell options closer to the money where gamma and vega are concentrated but risk of assignment increases.

Analyze a second multi-leg strategy: long straddle for volatility expansion. Structure: buy 1 ATM call and 1 ATM put on SPY, strike $455, expiration in 30 days, each option costs $8.50, total debit $17.00 per share × 100 = $1,700 per straddle. Position file:

```
Symbol,Type,Strike,Expiration,Quantity,EntryPremium,ImpliedVol
SPY,C,455,2025-03-21,1,8.50,0.18
SPY,P,455,2025-03-21,1,8.50,0.18
```

Compute portfolio Greeks. Delta is Δ_call + Δ_put ≈ 0.50 + (-0.50) = 0 (ATM call and put have deltas summing to zero by put-call parity). Gamma is Γ_call + Γ_put ≈ 2Γ_ATM, positive and large (long gamma). Vega is ν_call + ν_put ≈ 2ν_ATM, positive and large (long vega). Theta is Θ_call + Θ_call ≈ 2Θ_ATM, negative and large (suffering time decay). The straddle profits from large spot moves or volatility increases, and loses from rangebound markets and time decay. Break-even spot levels are $455 ± $17 = $438 and $472; the underlying must move beyond these thresholds by expiration to overcome the premium paid.

Perform scenario analysis for the long straddle across the same (spot, volatility) grid. The P&L surface exhibits a valley at the current spot ($455) where theta decay dominates, and rises steeply as spot deviates or volatility expands. The vega exposure transforms volatility increases into immediate P&L gains, enabling profitable exit even if spot has not yet moved significantly. This "long vol" profile contrasts sharply with the iron condor's "short vol" profile, demonstrating the gamma-theta and vega-theta trade-offs central to options strategy selection.

Implement a portfolio rebalancing protocol that maintains delta neutrality as spot moves. For the initial iron condor (portfolio delta = 0), a $5 spot increase shifts each option's delta, increasing portfolio delta to approximately +30 (negative gamma causes delta to become more positive as spot rises into the short call spread). To restore delta neutrality, sell 0.30 units of the underlying (30 shares of SPY) or add short call delta via additional contracts. Re-compute portfolio Greeks after the hedge adjustment and verify delta returns to near-zero. This dynamic hedging process is the operational foundation of market making: scalpers continuously adjust delta to isolate gamma and vega P&L while eliminating directional exposure.

Quantify the hedging cost for the long straddle. Each $1 spot move increases the straddle's delta from 0 toward +1 (if spot rises) or -1 (if spot falls) due to positive gamma. To maintain delta neutrality, the trader must buy underlying as spot falls (buying high after the stock has risen) and sell underlying as spot rises (selling low after the stock has fallen), realizing a loss on each hedge adjustment. The cumulative hedging cost over the option's life approximates ½Γ·(realized variance) × (number of rebalances), eroding the theoretical gamma profit if realized volatility falls short of implied volatility priced into the straddle premium. This "vol carry" reconciles the paradox that long gamma positions lose money in practice despite positive convexity: hedging costs exceed gamma gains when realized vol < implied vol.

Document the parameter variation empirical results in a structured summary table:

| Strategy       | Entry Cost | Max Profit | Max Loss | Portfolio Delta | Portfolio Gamma | Portfolio Vega | Portfolio Theta | Break-Even Spot |
|----------------|------------|------------|----------|-----------------|-----------------|----------------|-----------------|-----------------|
| Iron Condor    | -$2,500 credit | $2,500   | $2,500   | 0               | -150            | -800           | +40             | 444.75, 465.25  |
| Long Straddle  | $1,700 debit   | Unlimited | $1,700   | 0               | +50             | +600           | -60             | 438.00, 472.00  |

Interpret the trade-offs: the iron condor collects premium and profits from time decay and low realized volatility, but faces limited upside and defined maximum loss. The straddle pays premium and suffers time decay, but profits from large moves or volatility expansion with unlimited upside. Institutional traders layer both strategies in market-neutral books, selling condors in stable regimes to finance straddle purchases ahead of known events (earnings, FOMC, elections), exploiting the term structure of implied volatility.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

Construct a volatility surface calibration engine that fits implied volatility to market option prices across strikes and expirations, then stress-test the calibrated surface under gap openings, volatility spikes, correlation breakdown, and margin liquidation scenarios that expose model risk and operational limits. This exercise operationalizes the distinction between model price and realizable price during market dislocations, forcing recognition of liquidity constraints, bid-ask width explosions, and systemic hedging failures that destroy theoretical edge. The stress framework generates risk reports triggering pre-defined de-risking protocols: position size reductions, hedge ratio adjustments, and emergency liquidation sequences that mirror institutional crisis playbooks.

Begin by sourcing a complete options chain for a liquid underlying (SPY or QQQ) with at least three expiration months and ten strike prices per expiration spanning 80% to 120% of spot. The dataset should include bid/ask quotes, open interest, and volume for each contract. Format as a CSV with columns: Underlying, Type (C/P), Strike, Expiration, Bid, Ask, Open Interest, Volume, Spot Price, Risk-Free Rate, Dividend Yield. Download from broker API (Interactive Brokers, TD Ameritrade ThinkorSwim) or market data vendor (CBOE DataShop provides delayed quotes). Record the timestamp; options data becomes stale within minutes during volatile sessions.

Compute implied volatility for each contract by inverting the Black-Scholes model (Exercise 1) against the mid-market price (Bid + Ask)/2. Implement Newton-Raphson iteration as described in Exercise 1, initializing at 20% volatility and iterating until convergence. Flag contracts where implied volatility fails to converge (deep out-of-the-money options with bid near zero, or illiquid contracts with stale quotes). Exclude these contracts from surface fitting; illiquid options reflect stale market-maker quotes rather than true price discovery. Typical equity options chains yield 80-100 valid implied volatilities across three expirations and ten strikes per expiration after filtering.

Visualize the implied volatility surface as a 3D mesh with strike (x-axis), expiration (y-axis), and implied volatility (z-axis). The surface exhibits characteristic features: volatility smile or skew (volatility higher for OTM puts than ATM calls, reflecting crash risk premium), term structure (longer expirations have higher or lower volatility depending on forward variance expectations), and ATM volatility level (central reference point anchoring the surface). For SPY, the smile is pronounced with OTM put implied volatilities 5-10 percentage points above ATM, while OTM call volatilities decline more gradually. The term structure is typically upward-sloping during calm regimes (longer expirations price higher uncertainty) and inverted during crises (near-term volatility spikes but mean-reverts over time).

Fit a parametric volatility surface model to the observed implied volatilities, enabling interpolation to arbitrary strikes and expirations. Implement the Stochastic Volatility Inspired (SVI) parameterization, which expresses implied variance w(k) as a function of log-moneyness k = ln(K/F) where F is the forward price. The SVI formula is w(k) = a + b[ρ(k - m) + √((k - m)² + σ²)], with parameters (a, b, ρ, m, σ) calibrated per expiration via nonlinear least-squares minimization. The parameter a controls ATM variance level, b controls the slope of the smile, ρ controls skewness (negative for equity puts), m shifts the smile left or right, and σ controls the smile's curvature. Calibrate each expiration independently (slice-by-slice calibration), then interpolate across expirations using variance swaps or cubic spline on total variance √w.

Implement the SVI calibration in Python using SciPy's `optimize.least_squares`. Define the objective function as the sum of squared errors between observed implied variance w_market = (σ_implied)² × τ and model variance w_SVI(k; parameters). For the i-th expiration, compute forward price F = S × exp((r - q)τ), convert strikes K to log-moneyness k = ln(K/F), and minimize:

```python
import numpy as np
from scipy.optimize import least_squares

def svi_variance(k, a, b, rho, m, sigma):
    return a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))

def svi_objective(params, k_market, w_market):
    a, b, rho, m, sigma = params
    w_model = svi_variance(k_market, a, b, rho, m, sigma)
    return w_model - w_market

# For expiration τ, strikes K, implied vols σ, spot S, rate r, yield q:
F = S * np.exp((r - q) * tau)
k_market = np.log(K / F)
w_market = sigma_implied**2 * tau

# Initial guess: a = ATM variance, b = 0.1, rho = -0.5, m = 0, sigma = 0.1
initial_params = [w_market[len(w_market)//2], 0.1, -0.5, 0.0, 0.1]
result = least_squares(svi_objective, initial_params, args=(k_market, w_market))
a_fit, b_fit, rho_fit, m_fit, sigma_fit = result.x
```

Validate the fitted SVI parameters by recomputing implied volatilities at each observed strike and comparing to market values. Calculate root-mean-square error (RMSE) across strikes; acceptable RMSE for liquid equity options is below 1 percentage point (0.01 in volatility terms). Plot the fitted SVI curve overlaid on market implied volatilities to visually confirm the smile shape. If RMSE exceeds 2 percentage points or the fitted curve deviates systematically (crossing market points, failing to capture wings), recalibrate with tighter parameter bounds or switch to a more flexible model (SSVI for joint calibration across expirations, or Gatheral's natural SVI with no-arbitrage constraints).

Stress-test the calibrated volatility surface by simulating a gap opening: spot drops 10% overnight, implied volatilities across all strikes increase 20% (absolute increase of 20 percentage points × 0.18 = 3.6 percentage points, or relative increase of 20% × 18% = 3.6 percentage points; clarify: a 20% relative increase means multiplying by 1.20, so 18% becomes 21.6%). Reprice the iron condor and long straddle positions from Exercise 2 using the shocked volatility surface. For the iron condor, the short 445 put moves deeper in-the-money as spot falls to $409.50, and implied volatility increases from 17% to 20.4%. The put's intrinsic value is now $35.50, and time value collapses as delta approaches -1.00. The position loses approximately the width of the put spread ($5,000 max loss) minus the premium collected ($2,500), net loss $2,500 plus adverse vega exposure from the short volatility position.

Compute exact P&L via re-pricing. Load the shocked market state: S = $409.50, σ_shocked = 1.20 × σ_calibrated for each strike. Reprice all four iron condor legs using the Black-Scholes model with shocked inputs, sum the new position value, and subtract the initial value (net credit of $2,500). The short 445 put now trades at intrinsic $35.50 plus remaining time value (approximately $1.00 with 30 days to expiration but deep ITM), totaling $36.50. The long 440 put trades at intrinsic $30.50 plus minimal time value, totaling $31.00. The put spread is worth $36.50 - $31.00 = $5.50 per share × 1000 shares = $5,500, versus the initial net credit of $1,250, for a realized loss of $4,250 on the put spread. The call spread (originally worth $1,250 credit) decays toward zero as both strikes are now far out-of-the-money, contributing $1,250 profit. Net portfolio loss is -$4,250 + $1,250 = -$3,000, exceeding the nominal max loss of $2,500 due to the vega impact of the volatility spike compounding the spot move.

Contrast with the long straddle's performance under the same shock. The straddle's long 455 put moves from ATM to deeply in-the-money (intrinsic value $45.50), and the positive vega exposure benefits from the volatility increase. Reprice the put at S = $409.50, σ = 21.6%, yielding intrinsic $45.50 plus approximately $2.00 time value, totaling $47.50. The long 455 call is now far OTM but retains some value due to the elevated volatility, approximately $0.50. Total straddle value is $47.50 + $0.50 = $48.00 per share × 100 shares = $4,800, versus the initial cost of $1,700, for a realized profit of $3,100. The long gamma captured the 10% spot move, and the long vega captured the volatility spike, demonstrating the straddle's effectiveness as crash insurance.

Implement a liquidity stress scenario where bid-ask spreads widen to 10% of mid-market price (vs. typical 1-2% in calm markets). This spread blowout reflects market makers withdrawing liquidity during volatility spikes, forcing traders to cross wide markets when exiting positions. For the iron condor emergency liquidation, selling the short 445 put requires hitting the bid (10% below mid), and buying back the long 440 put requires lifting the offer (10% above mid), imposing a round-trip transaction cost of 20% of mid-market value. Calculate the liquidation P&L by repricing each leg at the shocked volatility surface, then apply the bid-ask penalty: sell at bid = 0.90 × mid for short options, buy at ask = 1.10 × mid for long options. The liquidity penalty adds approximately $500-$1,000 to the realized loss, transforming a -$3,000 model P&L into a -$4,000 realized P&L after execution costs.

Model a correlation breakdown scenario common during systemic sell-offs. Under normal conditions, SPY and individual stocks exhibit correlation ρ ≈ 0.70, allowing index options to hedge single-name exposure efficiently. During crashes, correlations spike toward 1.0 ("everything sells off together"), but implied volatility correlation between index and single names can deviate, causing hedge ratios to fail. Construct a portfolio hedged via SPY options: long 1000 shares of AAPL (spot $185, beta 1.2), hedged by short SPY call options with delta-equivalent exposure (1000 shares × 1.2 beta / 100 shares per contract = 12 contracts). Under the 10% SPY drop, AAPL falls 12% (beta-adjusted move) to $162.80. The hedge produces profit of 12 contracts × 100 shares × $45.50 delta gain ≈ $54,600 (each call loses $45.50, and we're short, so profit). The AAPL stock position loses 1000 shares × $22.20 = $22,200. Net hedge profit is $54,600 - $22,200 = $32,400, seemingly effective. But if AAPL's beta spikes to 1.5 during the sell-off (correlation breakdown), AAPL falls 15% to $157.25, losing 1000 × $27.75 = $27,750, versus the unchanged hedge profit of $54,600... wait, the hedge profit remains $54,600 only if SPY options behave as predicted. Recalculate: SPY drops 10% from $455 to $409.50. The short SPY call (strike $455) is now OTM, so the profit is the premium collected initially. This hedge structure is incorrect; correct hedge for long stock is long puts or short calls at appropriate strikes. Revise: hedge 1000 shares AAPL via long SPY put options with delta-equivalent exposure, not short calls.

Rebuild the correlation breakdown example. Long 1000 shares AAPL (spot $185, beta 1.2), hedged by long 15 SPY put contracts (strike $455, delta -0.50, equivalent to short 15 × 100 × 0.50 = 750 shares of SPY, scaled by beta 1.2 to hedge 750 / 1.2 = 625 shares of AAPL; adjust to 1000 shares by buying 1000 / 625 × 15 = 24 contracts). Under a 10% SPY drop, the 455 puts move in-the-money by $45.50, gaining 24 contracts × 100 shares × $45.50 = $109,200. AAPL drops 12% (beta 1.2 × 10%) to $162.80, losing 1000 × $22.20 = $22,200. Net hedge profit is $109,200 - $22,200 = $87,000, over-hedging due to the put's gamma and vega gains exceeding the linear beta-adjusted spot move. If AAPL's beta spikes to 1.5, AAPL falls 15% to $157.25, losing $27,750. The SPY puts still gain $109,200, yielding net profit $81,450. The hedge remains effective but over-delivers, suggesting the initial hedge ratio was mis-specified or the options' convexity outperformed linear expectations.

The correlation breakdown stress reveals that beta-hedging via index options introduces basis risk when single-name and index implied volatilities diverge or realized correlations deviate from historical norms. Institutional desks monitor rolling correlation and adjust hedge ratios dynamically, or switch to single-name options when available, accepting higher transaction costs for tighter basis risk.

Implement a margin liquidation cascade scenario. Assume the iron condor position is margined under Regulation T portfolio margin, initially requiring $2,500 margin (the defined risk max loss). After the 10% spot drop and volatility spike, the position's marked-to-market loss is $4,000 (including liquidity penalty). If the account equity is $10,000, the new equity is $10,000 - $4,000 = $6,000. Regulation T margin requirement remains $2,500 (defined risk unchanged), so the account is not in margin call ($6,000 > $2,500). However, if the initial equity was only $5,000 (using 2:1 leverage), the new equity is $5,000 - $4,000 = $1,000, below the $2,500 requirement, triggering forced liquidation. The broker sells the position at prevailing bid prices, locking in the realized loss plus execution slippage.

Model the margin cascade mathematically. Define account equity E, initial margin requirement M_init, maintenance margin requirement M_maint (typically 25% of initial margin for options), and position P&L. After adverse market move, new equity is E_new = E - |P&L|. Margin call occurs if E_new < M_maint. If triggered, the broker liquidates sufficient positions to restore equity above M_maint, selling at disadvantageous prices during volatility spikes. The forced liquidation crystallizes losses that could have recovered if the position was held to expiration or hedged dynamically. This cascade risk explains why institutional traders maintain equity buffers 2-3× the initial margin requirement, accepting lower leverage to avoid forced unwinds.

Develop a pre-defined de-risking protocol that triggers when portfolio-level risk metrics exceed thresholds. Define thresholds: (1) portfolio delta exceeds ±500 per $1M notional, (2) portfolio gamma magnitude exceeds 5,000 per $1M notional, (3) portfolio vega magnitude exceeds 10,000 per $1M notional, (4) daily P&L loss exceeds 5% of equity. When any threshold is breached, execute the following sequence:

1. **Immediate delta neutralization**: compute required hedge size in underlying shares to restore portfolio delta to zero. Execute as market order for immediate fill, accepting transaction costs.

2. **Vega reduction**: close 50% of farthest out-of-the-money options (lowest gamma, highest vega per dollar) to reduce net vega exposure by half. These options are most liquid and have minimal gamma impact.

3. **Gamma reduction**: close ATM straddles or strangles (highest gamma concentration) if gamma exceeds threshold, or if delta hedging frequency has exceeded 10 rebalances per day (hedging cost unsustainable).

4. **Emergency liquidation**: if P&L loss reaches 10% of equity, liquidate entire portfolio at market prices to prevent further deterioration. Accept execution slippage as the cost of catastrophe avoidance.

Simulate the de-risking protocol on the iron condor position during the 10% spot drop stress. Initial portfolio delta is 0, gamma is -150, vega is -800, theta is +40. After the 10% drop, recalculate Greeks at the shocked state (S = $409.50, σ = 21.6%). The short 445 put now has delta -0.95 (deep ITM), gamma near zero (delta approaching limit), vega near zero (no time value). The long 440 put has delta -0.92, gamma and vega near zero. The call spread is far OTM with negligible Greeks. New portfolio delta is -10×100×(-0.95) + 10×100×(-0.92) + (call spread deltas ≈ 0) = +950 - 920 + 0 = +30. New portfolio gamma is near zero (all options at delta extremes). New portfolio vega is near zero. The position has collapsed from a short-vol neutral structure into a directional long-delta exposure with no remaining convexity or volatility sensitivity.

The de-risking protocol would trigger threshold (4) as the P&L loss (-$3,000 to -$4,000 depending on execution) likely exceeds 5% of a typical $50,000-$100,000 account. Execute emergency liquidation: sell the long 440 put at bid, buy the short 445 put at ask, buy the short 465 call at ask, sell the long 470 call at bid. Compute liquidation P&L with 10% bid-ask penalty. The short 445 put costs $36.50 × 1.10 = $40.15 to buy back. The long 440 put sells at $31.00 × 0.90 = $27.90. Put spread liquidation cost is 10 contracts × 100 shares × ($40.15 - $27.90) = $12,250. Subtract the initial $1,250 credit, net loss $11,000 on the put spread. The call spread liquidation captures near-zero value with transaction costs of approximately $200, adding $1,250 credit retained minus $200 costs = $1,050 profit. Total liquidation P&L is -$11,000 + $1,050 = -$9,950, catastrophically worse than the model P&L of -$3,000 due to the compounding of intrinsic losses, volatility impact, and liquidity penalties.

This stress scenario underscores the critical operational reality: model P&L is a theoretical construct that assumes continuous hedging, zero transaction costs, and liquid markets. Realized P&L during crises deviates systematically due to discrete hedging, bid-ask spreads, and forced liquidations. Professional traders price in this "model risk" by demanding higher premium on short-volatility strategies and maintaining equity buffers sufficient to survive multiple-standard-deviation moves without forced unwinds.

Document the stress test results in a comprehensive risk report:

| Scenario                | Spot Change | Vol Change | Model P&L | Liquidity-Adjusted P&L | Margin Violation | De-Risking Action         |
|-------------------------|-------------|------------|-----------|------------------------|------------------|---------------------------|
| Baseline                | 0%          | 0%         | $0        | $0                     | No               | None                      |
| Gap Down 10%            | -10%        | +20%       | -$3,000   | -$4,000                | No (if E>$10K)   | Delta hedge, vega reduce  |
| Gap Down 10% + Cascade  | -10%        | +20%       | -$3,000   | -$9,950                | Yes (if E<$5K)   | Emergency liquidation     |
| Vol Spike Only          | 0%          | +50%       | -$1,200   | -$1,800                | No               | Vega reduce 50%           |
| Correlation Breakdown   | -10% (SPY)  | -15% (AAPL)| Hedge model: $87K profit, realized: $81K | No | Recompute beta hedge ratio |

Interpret the operational lessons. The iron condor's defined-risk profile provides downside protection in model space but fails catastrophically when liquidity evaporates and forced liquidation occurs at distressed prices. The long straddle, despite negative theta, demonstrates resilience during tail events, profiting from both spot moves and volatility expansion. The correlation breakdown stress reveals that cross-asset hedging introduces basis risk requiring continuous monitoring. The margin cascade demonstrates why capital allocation (equity buffer) is as critical as position structuring for survival.

## Operational Reference Guide & Diagnostic Checklist

This reference guide consolidates the analytical infrastructure, risk protocols, and diagnostic checklists required for operational options trading. Maintain this guide as a living document, updated as market conditions evolve and regulatory requirements change.

**Black-Scholes-Merton Model Implementation Checklist**:
- Cumulative normal distribution function Φ(x) validated against Excel NORM.S.DIST() for x ∈ [-5, 5] with error < 1×10⁻⁶
- Log-moneyness terms d₁ and d₂ computed with intermediate cell references for transparency
- Call premium C and put premium P satisfy put-call parity: C - P = S·exp(-qτ) - K·exp(-rτ) within $0.01 tolerance
- Delta satisfies bounds: 0 < Δ_call < 1, -1 < Δ_put < 0, Δ_call - Δ_put = exp(-qτ) within 0.01
- Gamma is always positive, peaks at-the-money, approaches zero in-the-money and out-of-the-money
- Vega is always positive, peaks at-the-money, scales with √τ
- Theta is negative for long calls and puts (time decay), positive for short positions
- Rho is positive for calls, negative for puts, scaled per 1% rate change
- Implied volatility iteration converges within 10 steps for |f(σ)| < $0.01
- American option binomial tree (N=100 steps) yields premium within $0.05 of Black-Scholes European premium for non-dividend calls

**Position File Data Schema**:
```
Symbol: underlying ticker (string)
Type: C (call) or P (put) (char)
Strike: strike price (float, USD)
Expiration: expiration date (date, YYYY-MM-DD)
Quantity: position size in contracts (int, negative for short, positive for long)
EntryPremium: premium at entry (float, USD per share)
ImpliedVol: current implied volatility (float, decimal, e.g., 0.18 for 18%)
```

**Portfolio-Level Greek Aggregation Formulas**:
- Δ_portfolio = Σ(Quantity_i × 100 × Δ_i) across all legs i
- Γ_portfolio = Σ(Quantity_i × 100 × Γ_i)
- ν_portfolio = Σ(Quantity_i × 100 × ν_i)
- Θ_portfolio = Σ(Quantity_i × 100 × Θ_i)
- ρ_portfolio = Σ(Quantity_i × 100 × ρ_i)
- Convert Greeks to per-$1M notional by dividing by portfolio value in $M

**P&L Attribution First-Order Approximation**:
ΔP&L ≈ Δ·ΔS + ½Γ·(ΔS)² + ν·Δσ + Θ·Δt

Where:
- ΔS = spot price change (USD)
- Δσ = implied volatility change (absolute, e.g., 0.03 for 3 percentage point increase)
- Δt = time elapsed (years, e.g., 1/365 for one day)

For multi-day P&L or large moves, reprice all legs exactly rather than relying on Taylor expansion.

**SVI Volatility Surface Parameterization**:
Implied variance: w(k) = a + b[ρ(k - m) + √((k - m)² + σ²)]

Log-moneyness: k = ln(K/F) where F = S·exp((r - q)τ)

Parameters per expiration:
- a: ATM variance level (positive float)
- b: slope of variance smile (positive float)
- ρ: skewness (-1 to 1, typically negative for equity puts)
- m: smile shift (float, typically near zero)
- σ: smile curvature (positive float)

Calibration: minimize Σ(w_model(k_i) - w_market(k_i))² via scipy.optimize.least_squares

Validation: RMSE < 0.01 in volatility terms, visual inspection confirms smile/skew captured

**Risk Limit Thresholds (per $1M Notional)**:
- Portfolio delta: -500 to +500 (delta-neutral ±5%)
- Portfolio gamma: magnitude < 5,000
- Portfolio vega: magnitude < 10,000
- Daily P&L loss: < 5% of account equity (warning), < 10% (emergency liquidation)
- Hedging frequency: < 10 delta rebalances per day (hedging cost acceptable)

**De-Risking Protocol Trigger and Response**:
1. **Delta breach (|Δ_portfolio| > 500 per $1M)**: hedge via underlying shares, execute as market order, restore delta to zero within 15 minutes
2. **Vega breach (|ν_portfolio| > 10,000 per $1M)**: close 50% of OTM options (lowest gamma per vega), execute as limit orders at mid-market, timeout 30 minutes then market orders
3. **Gamma breach (|Γ_portfolio| > 5,000 per $1M)**: close ATM straddles/strangles, execute as limit orders within 20% of mid-market, timeout 15 minutes then market orders
4. **Daily loss breach (P&L < -5% equity)**: initiate de-risk sequence (delta hedge, vega reduce); if P&L < -10% equity, emergency liquidate entire portfolio at market prices within 10 minutes

**Bid-Ask Spread Liquidity Stress Assumptions**:
- Normal market: 1-2% bid-ask spread
- Volatility spike (VIX +10 points): 5-10% spread
- Liquidity crisis (VIX +20 points, major index -5% intraday): 10-20% spread
- Emergency liquidation execution: sell at bid = 0.90 × mid, buy at ask = 1.10 × mid for 10% spread regime

**Margin Requirement Calculations**:
- Regulation T initial margin for defined-risk spread: max loss of the spread (strike width × quantity × 100 - net credit collected)
- Regulation T maintenance margin: 25% of initial margin
- Portfolio margin (SPAN): worst-case loss across 16 scenarios (±1σ, ±2σ, ±3σ spot; ±1 vol; 8 combinations × 2 for time decay), computed via exchange SPAN calculator or broker API
- Equity buffer recommendation: maintain equity ≥ 2.5× initial margin requirement to avoid forced liquidations during normal volatility; ≥ 5× during elevated volatility

**Options Data Quality Checks**:
- Bid < Ask (no crossed markets; if violated, data is stale or corrupted)
- Call premium ≥ intrinsic value max(S - K, 0) (no arbitrage)
- Put premium ≥ intrinsic value max(K - S, 0) (no arbitrage)
- Put-call parity: |C - P - (S·exp(-qτ) - K·exp(-rτ))| < $0.10 for liquid strikes (wider tolerance for illiquid contracts)
- Open interest > 100 contracts and volume > 10 contracts today (liquidity filter)
- Implied volatility converges within 10 iterations; if not, flag as illiquid and exclude from surface fitting
- Timestamp within 15 minutes (real-time) or clearly marked as delayed (15-minute delay or end-of-day)

**Break-Even Calculation for Common Strategies**:
- Long call: S_breakeven = K + Premium
- Long put: S_breakeven = K - Premium
- Long straddle: S_breakeven_up = K + Total Premium, S_breakeven_down = K - Total Premium
- Short straddle: same break-evens, but max profit (premium collected) occurs at S = K
- Iron condor: S_breakeven_down = K_put_long + Net Credit, S_breakeven_up = K_call_short - Net Credit
- Vertical spread (bull call, bear put): max profit = spread width - net debit; max loss = net debit; break-even = long strike + net debit (call spread) or short strike - net debit (put spread)

**Greeks Interpretation and Hedging Rules**:
- Delta: directional exposure. Hedge via underlying shares (long shares to neutralize negative delta, short shares for positive delta) or opposite-signed options. Target: |Δ_portfolio| < 1% of notional.
- Gamma: convexity exposure. Positive gamma (long options) benefits from volatility; negative gamma (short options) loses from large moves. Cannot directly hedge gamma without trading options; manage by position sizing and avoiding excessive short gamma concentration.
- Vega: volatility exposure. Positive vega (long options) gains when implied vol rises; negative vega (short options) gains when vol falls. Hedge via opposite-signed vega in different expirations or underlyings (VIX futures, variance swaps). Target: |ν_portfolio| < 5% of notional.
- Theta: time decay. Positive theta (short options) earns decay; negative theta (long options) pays decay. Theta is not hedged; it is the trade-off for gamma and vega exposure. Monitor theta as daily P&L baseline expectation.
- Rho: interest rate sensitivity. Typically negligible for short-dated equity options; material for long-dated options (LEAPS) and interest rate derivatives. Hedge via interest rate swaps or Treasury futures if rho exposure is unwanted.

**Volatility Surface Arbitrage Checks**:
- Calendar spread arbitrage: forward variance (w₂ - w₁)/(τ₂ - τ₁) must be positive (variance is non-decreasing in time)
- Butterfly arbitrage: for any three strikes K₁ < K₂ < K₃, the call price curve must be convex: C₂ ≤ (K₃ - K₂)/(K₃ - K₁)·C₁ + (K₂ - K₁)/(K₃ - K₁)·C₃
- Put-call parity: already validated in data quality checks
- If arbitrage violations detected, recalibrate surface with constraints or exclude offending strikes

**Historical Volatility vs. Implied Volatility Comparison**:
- Compute 30-day realized volatility: σ_realized = √(252) × std(log returns over past 30 days)
- Compare to 30-day ATM implied volatility σ_implied
- Vol risk premium: VRP = σ_implied - σ_realized
- Typical equity VRP: +2 to +5 percentage points (implied > realized, options are "expensive")
- Negative VRP (implied < realized) signals underpriced volatility; consider long straddles/strangles
- Positive VRP > +10 points: overpriced volatility; consider short straddles/iron condors

**Crisis Scenario Historical Benchmarks**:
- Black Monday (Oct 1987): S&P 500 -20% in one day, VIX not yet invented but implied vol > 100%
- Flash Crash (May 2010): S&P 500 -9% intraday, recovered within minutes, options bid-ask spreads 20-50% of mid
- COVID Crash (Mar 2020): S&P 500 -34% peak-to-trough over 23 days, VIX peak 82.69, options trading halted multiple times due to liquidity
- Use these events as stress test scenarios: -10% to -20% spot, +20 to +50 vol points, bid-ask spreads 10-20%, margin calls assume equity drops 30-50%

**Daily Operational Checklist for Active Options Portfolios**:
□ Pre-market (08:00-09:30 ET): review overnight spot moves, recalculate portfolio Greeks, identify delta hedges needed at open
□ Market open (09:30): execute delta hedges, verify fills, recompute Greeks post-hedge
□ Mid-morning (10:30): check for risk limit breaches, review P&L attribution (delta, gamma, vega, theta components), confirm realized P&L vs. model P&L within 20%
□ Midday (12:00): update volatility surface with latest market quotes, recalibrate SVI parameters if RMSE degrades, reprice all positions at mid-market
□ Mid-afternoon (14:00): re-check Greeks, execute any required rebalancing, verify margin requirements remain satisfied
□ Pre-close (15:30): final Greek check, plan overnight hedges, review expiring contracts (if expiration Friday)
□ Post-close (16:00-17:00): mark-to-market all positions at settlement prices, reconcile P&L vs. broker statements, document any execution slippage or data discrepancies, prepare risk report for next session

This operational guide equips the practitioner with the mechanical procedures, formulas, risk limits, and crisis protocols required to manage options portfolios through both routine conditions and extreme market dislocations. Internalize the checklists as reflex; options trading rewards systematic discipline and punishes improvisation.
