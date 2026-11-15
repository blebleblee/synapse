# Lesson 4: Derivatives Pricing under Risk-Neutral Valuation

## 1. First-Principles Intuition & Invariants

The fundamental problem confronting a derivatives trader or risk manager is deceptively simple in statement but profound in execution: how do you assign a fair value to a contract whose payoff depends on the future price of an underlying asset, when that future price is unknowable? Classical probability theory offers one answer—compute the expected value under the real-world probability measure, discounting at the risk-free rate. This approach fails catastrophically in practice because it produces prices that violate no-arbitrage constraints and, more critically, because real-world probability measures are unobservable and market-dependent.

The intellectual breakthrough that resolved this paradox emerged in the 1970s and crystallized in the Black-Scholes-Merton framework: the key insight is that derivative prices are not determined by the expected future price under the real-world measure, but rather by the requirement that no arbitrage opportunities exist in the market. This shift from expected-value thinking to arbitrage-free thinking represents one of the most consequential conceptual moves in quantitative finance. What the no-arbitrage principle reveals is that there exists a synthetic probability measure—the risk-neutral measure—under which the discounted price of any tradeable security evolves as a martingale. Pricing derivatives then becomes an exercise in replicating their payoffs using traded instruments, computing expected payoffs under this risk-neutral measure, and discounting at the risk-free rate.

The elegance of this framework rests on a foundation of mathematical structures that we must develop carefully. Begin with a filtered probability space $(\Omega, \mathcal{F}, \{\mathcal{F}_t\}_{t \geq 0}, \mathbb{P})$, where $\mathbb{P}$ represents the real-world (physical) measure under which actual market outcomes evolve. At time $t = 0$, we observe a spot price $S_0$ for the underlying asset. Under the physical measure, the log-return follows some drift $\mu$ and volatility $\sigma$, captured by the stochastic differential equation

$$dS_t = \mu S_t \, dt + \sigma S_t \, dW_t$$

where $W_t$ is a standard Brownian motion. The drift $\mu$ represents our belief about the expected return of the asset. However, the price of a European call option written on this asset should not depend on $\mu$—it should depend only on the current spot price, the strike, the time to maturity, the risk-free rate, and volatility. This is because traders can replicate the option's payoff using a dynamic hedge of the underlying asset and cash, and arbitrage forces the option price to match this replication cost regardless of whether the stock rises or falls.

The mechanism of replication is the key. Suppose we hold $\Delta_t$ shares of the underlying and a cash position worth $B_t$. The value of this replicating portfolio is

$$V_t = \Delta_t S_t + B_t$$

If we choose $\Delta_t$ and $B_t$ carefully, we can ensure that $V_T = \text{Payoff}_T$ at maturity $T$. By the no-arbitrage principle, the option price must equal $V_0$. The remarkable discovery is that the choice of $\Delta_t$ that makes replication work depends only on the underlying's volatility $\sigma$ and the risk-free rate $r$—it does not depend on the drift $\mu$. This is the deepest intuition of risk-neutral valuation: the drift is irrelevant because we are hedging away the directional risk.

This independence from $\mu$ manifests mathematically through a change of measure. The Girsanov theorem states that we can define a new probability measure $\mathbb{Q}$ such that under $\mathbb{Q}$, the process

$$\tilde{W}_t = W_t + \int_0^t \frac{\mu - r}{\sigma} \, ds = W_t + \frac{\mu - r}{\sigma} t$$

is a standard Brownian motion. Under this new measure $\mathbb{Q}$, the underlying asset evolves as

$$dS_t = r S_t \, dt + \sigma S_t \, d\tilde{W}_t$$

Notice that the drift has changed from $\mu$ to $r$. This is the risk-neutral measure: it is the unique measure under which all discounted tradeable security prices evolve as martingales. Under $\mathbb{Q}$, the discounted stock price $e^{-rt} S_t$ is a martingale, meaning

$$E^\mathbb{Q}[e^{-rT} S_T | \mathcal{F}_t] = e^{-rt} S_t$$

or equivalently,

$$S_t = E^\mathbb{Q}[e^{-r(T-t)} S_T | \mathcal{F}_t]$$

The current price equals the risk-neutral expectation of the future discounted price. This is the martingale pricing principle.

For a derivative with payoff $\Phi(S_T)$ at maturity, the no-arbitrage price at time $t$ is

$$C_t = e^{-r(T-t)} E^\mathbb{Q}[\Phi(S_T) | \mathcal{F}_t]$$

Under the risk-neutral measure with constant volatility $\sigma$, the stock price at time $T$ is log-normally distributed. Conditioning on $S_t = s$, we have

$$S_T = s \exp\left[\left(r - \frac{\sigma^2}{2}\right)(T-t) + \sigma \sqrt{T-t} \, Z\right]$$

where $Z \sim N(0,1)$ under $\mathbb{Q}$. For a European call option with strike $K$ and maturity $T$, the payoff is $\max(S_T - K, 0)$. Computing the expectation under the log-normal distribution yields the Black-Scholes formula:

$$C(S, K, T, r, \sigma) = S \Phi(d_+) - K e^{-rT} \Phi(d_-)$$

where 

$$d_\pm = \frac{\ln(S/K) + (r \pm \sigma^2/2)T}{\sigma\sqrt{T}}$$

and $\Phi(\cdot)$ is the cumulative standard normal distribution function. Critically, this formula depends only on the current spot price $S$, the strike $K$, time to maturity $T$, the risk-free rate $r$, and the volatility $\sigma$. The real-world drift $\mu$ appears nowhere. The market price of risk has been eliminated through the change of measure.

The existence and uniqueness of the risk-neutral measure rests on the fundamental theorem of asset pricing. In a frictionless market with no arbitrage opportunities, there exists a probability measure $\mathbb{Q}$ (the risk-neutral measure) such that every tradeable asset's discounted price is a $\mathbb{Q}$-martingale. Conversely, if such a measure exists, the market is arbitrage-free. This theorem establishes that no-arbitrage and the existence of a risk-neutral measure are equivalent concepts. In practice, this means we can price any derivative by simulating future paths under $\mathbb{Q}$, computing payoffs, averaging them, and discounting.

The complete market hypothesis strengthens this further: if the number of independent sources of randomness (Brownian motions) equals or is less than the number of traded securities, the market is complete. In a complete market, every derivative can be perfectly replicated using a dynamic trading strategy in the underlying assets, and the risk-neutral measure is unique. The Black-Scholes world assumes completeness: one Brownian motion drives the stock, and two traded securities (the stock and a risk-free bond) allow us to replicate any European derivative. In higher-dimensional models with multiple sources of risk (e.g., stochastic volatility, stochastic interest rates, jump risk), markets become incomplete, and multiple risk-neutral measures may exist.

## 2. Core Architecture & Mechanics

### The Black-Scholes-Merton Framework in Practice

The core architecture of derivatives pricing in practice begins with the discretization of the risk-neutral SDE and implementation of the valuation and hedging workflows. Consider the discrete evolution of the underlying under the risk-neutral measure:

$$S_{t+\Delta t} = S_t \exp\left[\left(r - \frac{\sigma^2}{2}\right)\Delta t + \sigma \sqrt{\Delta t} \, Z\right]$$

where $Z \sim N(0,1)$. This is the log-Euler discretization, which preserves the log-normality of the stock price. A practitioner implementing a pricing library must choose between closed-form solutions (for vanilla options), finite-difference methods (for American options and early-exercise features), Monte Carlo simulation (for path-dependent or high-dimensional payoffs), and lattice methods (for structured products with embedded optionality).

For European vanilla options, the Black-Scholes formula is computed directly. However, most production trading systems cannot rely solely on closed-form solutions because real market derivatives deviate from the Black-Scholes world in systematic ways. Volatility is not constant; it depends on both the underlying price level (local volatility) and time. Interest rates are stochastic. Jump risk exists. To accommodate these complexities while maintaining computational efficiency, practitioners layer extensions onto the core framework.

The concept of implied volatility is essential here. In practice, traders do not observe the Black-Scholes parameters directly from prices; instead, they invert the Black-Scholes formula to extract the volatility that would produce the observed market price. This implied volatility $\sigma_{\text{imp}}$ varies across strike prices and maturities, forming the volatility surface. If the Black-Scholes model were accurate, the volatility surface would be flat—the same volatility everywhere. Instead, we observe the volatility smile (higher volatility at out-of-the-money strikes) and term structure effects (volatility that varies with maturity). These deviations from flat volatility are priced into the market and must be accounted for in any realistic pricing model.

The Greeks—the partial derivatives of option price with respect to model parameters—form the operational language of hedging in trading desks. The delta $\Delta$ measures sensitivity to the underlying price:

$$\Delta = \frac{\partial C}{\partial S} = \Phi(d_+)$$

A trader who is long a call option and short $\Delta$ shares of stock has delta-hedged their position, meaning the portfolio value is insensitive to small moves in the underlying. As the stock price changes, delta changes (this is gamma), so the trader must continuously rebalance to maintain the hedge. The gamma $\Gamma$ is

$$\Gamma = \frac{\partial^2 C}{\partial S^2} = \frac{\phi(d_+)}{S \sigma \sqrt{T}}$$

where $\phi$ is the standard normal density. Gamma is the cost of delta hedging; it represents the tracking error that accumulates when the underlying price moves and the hedge must be rebalanced at a realized price different from the previous hedge price.

Vega $\nu$ measures sensitivity to volatility:

$$\nu = \frac{\partial C}{\partial \sigma} = S \phi(d_+) \sqrt{T}$$

A trader who buys an option is long vega—they profit if volatility rises (even if the stock price stays flat). A trader who sells an option is short vega and hedges by holding short gamma positions or by buying other options with higher vega. Theta $\Theta$ measures decay as time passes:

$$\Theta = -\frac{\partial C}{\partial T} = -\frac{S \phi(d_+) \sigma}{2\sqrt{T}} - r K e^{-rT} \Phi(d_-)$$

Time decay on long options is negative (theta decay erodes value), while short options benefit from theta decay. The Greeks are the atomic units of derivatives trading; every position is decomposed into a Greeks vector, and trading systems track and rebalance Greek exposures continuously.

### Stochastic Volatility and Local Volatility

The simplest extension to the Black-Scholes framework introduces stochastic volatility, recognizing that the market's uncertainty about future returns is not constant but evolves over time. The Heston model is the canonical framework here:

$$dS_t = r S_t \, dt + \sqrt{v_t} S_t \, dW_t^S$$
$$dv_t = \kappa(\theta - v_t) \, dt + \xi \sqrt{v_t} \, dW_t^v$$

where $v_t$ is the variance (instantaneous squared volatility), $\kappa$ is the mean-reversion speed, $\theta$ is the long-run mean variance, and $\xi$ is the volatility of volatility. The two Brownian motions $W_t^S$ and $W_t^v$ are correlated with coefficient $\rho$. The negative correlation (typically $\rho \in [-0.9, -0.5]$) captures the empirical leverage effect: when stock prices fall, volatility tends to rise, reflecting increased uncertainty and risk. Conversely, when prices rise, volatility tends to fall.

The Heston model is incomplete—there are two sources of randomness but only one traded security (the stock). The bond market is risk-free, so to complete the market, we must assume a market price of volatility risk, denoted $\lambda_v$. Under the risk-neutral measure, the volatility risk premium adjusts the volatility equation to

$$dv_t = [\kappa(\theta - v_t) - \lambda_v \sqrt{v_t}] \, dt + \xi \sqrt{v_t} \, dW_t^v$$

The term $\lambda_v \sqrt{v_t}$ is an additional drift that accounts for the fact that traders demand compensation for bearing volatility risk. In practice, $\lambda_v$ is not observed directly; it is calibrated to fit market prices of traded options.

A tangential but important concept is local volatility, introduced by Dupire. Rather than assuming volatility is a stochastic process with its own dynamics, local volatility assumes that volatility is a deterministic function of the underlying price and time, $\sigma(S_t, t)$. While this may sound like a step backward from the realism of stochastic volatility, local volatility models have a critical advantage: they exactly reproduce the observed volatility surface by construction. The Dupire formula relates the local volatility function to the implied volatility surface:

$$\sigma^2(K, T) = \frac{\frac{\partial C}{\partial T} + r K \frac{\partial C}{\partial K}}{\frac{1}{2} K^2 \frac{\partial^2 C}{\partial K^2}}$$

Given market prices for calls across strikes and maturities, this formula can be inverted to extract the local volatility surface. A trader can then price any exotic derivative by simulating paths under this local volatility function and computing expected payoffs. The local volatility approach is computationally efficient and calibration is straightforward, making it the workhorse for many exotic derivatives desks. However, local volatility has a limitation: it does not capture volatility mean reversion or the term structure of volatility risk premia, so it can misprice derivatives that are highly sensitive to future volatility levels.

Stochastic-local volatility models (SLV) attempt to combine the strengths of both approaches. The underlying evolves as

$$dS_t = r S_t \, dt + L(S_t, t) \sqrt{v_t} S_t \, dW_t^S$$

where $L(S_t, t)$ is a leverage function that modulates the stochastic volatility $\sqrt{v_t}$ to match the local volatility surface. By construction, SLV models exactly reproduce both the observed volatility surface and the term structure of volatility mean reversion implicit in option prices. In practice, SLV models are calibrated by first extracting the local volatility surface from the market, then fitting stochastic volatility parameters, and finally determining the leverage function to enforce consistency.

### Jump-Diffusion Models and Event Risk

The Poisson jump-diffusion model, formalized by Merton, extends the framework to account for discontinuous price movements that occur infrequently but with large magnitude. Under this model, the stock price evolves as

$$dS_t = (\mu - \lambda k) S_t \, dt + \sigma S_t \, dW_t + (J - 1) S_{t-} \, dN_t$$

where $N_t$ is a Poisson process with intensity $\lambda$ (the expected number of jumps per unit time), and $J$ is the jump size (multiplicative factor applied to the stock price upon a jump). The term $\lambda k$ in the drift accounts for the jump risk; it is the compensation that the stock must earn for the possibility of jumps.

The critical insight is that jumps introduce risk that cannot be hedged away with continuous trading in the underlying stock alone. If a jump occurs, the trader who is holding options will experience a gap in the replicating portfolio's value. Under the risk-neutral measure, the jump component is calibrated to match the observed market price of jump risk. The jump intensity $\lambda$, the mean jump size, and the jump distribution are all calibrated to fit market prices of out-of-the-money options, which are most sensitive to tail risk.

In the risk-neutral framework with jumps, option prices are computed by integrating over both the diffusive paths (where no jump occurs) and the jumped paths (where a jump occurs). For a European option, this leads to

$$C = E^\mathbb{Q}\left[e^{-rT} \Phi(S_T)\right] = \sum_{n=0}^{\infty} e^{-\lambda^* T} \frac{(\lambda^* T)^n}{n!} C_n$$

where $C_n$ is the option price in the scenario where exactly $n$ jumps occur, and $\lambda^*$ is the risk-neutral jump intensity. In practice, the infinite sum is truncated after a few terms because the probability of many jumps is vanishingly small over typical option lifetimes.

### Monte Carlo Valuation in Action

For derivatives with path-dependent payoffs (e.g., Asian options whose payoff depends on the average stock price over the option's life) or high-dimensional payoffs (e.g., basket options whose payoff depends on multiple underlying assets), closed-form solutions do not exist, and numerical methods are essential. Monte Carlo simulation is the most flexible approach.

The procedure is straightforward in principle: (1) simulate $M$ independent paths of the underlying asset under the risk-neutral measure, from $t=0$ to $t=T$, using the discretized SDE; (2) for each path, compute the payoff at maturity; (3) compute the sample average of all payoffs; (4) discount at the risk-free rate. The result is an unbiased estimator of the option price. The standard error decreases as $1/\sqrt{M}$, so to achieve one additional decimal place of accuracy requires ten times more simulations.

Consider a practical example: pricing an Asian call option with payoff $\max(\frac{1}{T}\int_0^T S_t \, dt - K, 0)$. Since the average is discretized in practice, we observe $S$ at $N$ equally-spaced times $t_i = i \Delta t$ for $i = 1, \ldots, N$, and approximate the average as $\bar{S} = \frac{1}{N} \sum_{i=1}^N S_{t_i}$. For each of the $M$ simulated paths:

$$S_{t_{i+1}} = S_{t_i} \exp\left[\left(r - \frac{\sigma^2}{2}\right) \Delta t + \sigma \sqrt{\Delta t} \, Z_{i}\right]$$

where $Z_i \sim N(0,1)$. After simulating all paths, we compute the payoff for each path as $\Phi_m = \max(\bar{S}_m - K, 0)$, and the option price is

$$C = e^{-rT} \frac{1}{M} \sum_{m=1}^M \Phi_m$$

The beauty of Monte Carlo is its generality: virtually any payoff structure can be valued by simulating paths and computing payoffs. The drawback is computational cost; valuing a portfolio of options requires simulating paths for each option separately (or jointly, if they share underlyings), which can be computationally intensive for real-time pricing on trading desks.

## 3. High-Performance Optimization & Failure Modes

### Calibration and Model Risk

In all of these frameworks—Black-Scholes, stochastic volatility, local volatility, jump-diffusion—parameters must be calibrated to market data. This is where theory meets practice, and where significant challenges emerge. The task of calibration is to find parameters such that the model prices for a set of liquid benchmark instruments (typically vanilla calls and puts across a range of strikes and maturities) match the observed market prices as closely as possible.

The calibration problem is generally non-convex and high-dimensional. For the Heston model with six parameters ($r$, $\kappa$, $\theta$, $\xi$, $\rho$, $v_0$), the calibration landscape is rugged with multiple local minima. A naive optimization algorithm starting from an arbitrary initial guess may converge to a sub-optimal solution. In production, practitioners use careful initialization heuristics, multi-start optimization, and sensitivity analysis to ensure calibration robustness. The risk that calibrated parameters are unstable and sensitive to small changes in market data is model risk—it is one of the most insidious sources of trading losses.

A related phenomenon is the smile dynamics problem. The volatility smile—the pattern of implied volatilities across strikes—shifts daily as market conditions change. When a trader calibrates a model to today's smile and then prices a derivative, the model's prediction for tomorrow's smile is often inaccurate. This introduces basis risk: the trader's hedging ratios computed today may be suboptimal by tomorrow. One practical mitigation is to calibrate not just to vanilla option prices but also to incorporate implied volatility surface dynamics into the model. This is the philosophy behind stochastic volatility models with realistic mean reversion: such models naturally incorporate the empirically observed slow-moving shifts in the volatility surface.

### The Greeks and Hedge Rebalancing

Once a model is calibrated and option prices are computed, the Greeks—sensitivities to model parameters—must be computed accurately. In the Black-Scholes world, the Greeks have closed forms; in more complex models, they must be computed numerically. Computing Greeks by finite difference (bumping a parameter by a small amount, recomputing the price, and taking the difference) is simple but can introduce severe numerical errors if the bump is too large (truncation error) or too small (rounding error).

Algorithmic differentiation (automatic differentiation) offers a principled alternative. The idea is to decompose the pricing computation into elementary operations (addition, multiplication, exponential, etc.) and apply the chain rule from calculus to each operation automatically. Forward-mode differentiation traces how a small change in an input propagates through the computation to the output. Reverse-mode (backpropagation) traces how a unit of sensitivity at the output flows back through the computation to each input. For a single-output function (option price with respect to many inputs), reverse-mode is more efficient. Modern pricing libraries use automatic differentiation for robust, accurate Greeks computation.

In practice, a trading desk computes Greeks for every position at market open and throughout the day. For a portfolio containing thousands of options, this is a significant computational burden. Practitioners use approximations to accelerate Greeks computation: Greeks are cached and only recomputed if the underlying price has moved by more than a threshold, or Greeks are interpolated from a pre-computed surface. The delta-hedging frequency is chosen as a balance between hedging costs (transaction costs, bid-ask spreads) and tracking error. Too frequent rehedging erodes profits through transaction costs; too infrequent rehedging allows positions to drift and become unhedged.

### Monte Carlo Variance Reduction

The statistical error in Monte Carlo valuation—the standard deviation of the price estimate—scales as $1/\sqrt{M}$, where $M$ is the number of paths. For high-accuracy pricing (e.g., computing Greeks, pricing deep out-of-the-money options), $M$ can be in the millions, making computation slow. Variance reduction techniques accelerate convergence.

Antithetic variates exploit symmetry: if we simulate a path using random numbers $Z$, we also simulate the path using $-Z$ (the antithetic path). Both paths have the same distribution, and their payoff difference tends to have lower variance than using $M/2$ independent paths. By pairing paths this way, variance is roughly halved, equivalent to quadrupling the number of paths at no additional computational cost.

Control variates use the known value of a related quantity to reduce variance. For instance, when pricing an Asian option with $M$ paths, we compute both the payoff of the Asian option and the payoff of a European option on the same underlying (whose analytical price is known via Black-Scholes). Let $\Phi_m^{\text{Asian}}$ and $\Phi_m^{\text{Euro}}$ be the payoffs on path $m$. The price estimate is

$$C_{\text{Asian}} \approx e^{-rT} \left[\frac{1}{M} \sum_{m=1}^M \Phi_m^{\text{Asian}} - c \left(\frac{1}{M} \sum_{m=1}^M \Phi_m^{\text{Euro}} - C_{\text{Euro}}\right)\right]$$

where $c$ is chosen to minimize variance. The term in parentheses is the pricing error of the European option, which is zero in expectation; subtracting a multiple of it reduces the variance of the Asian price estimate without biasing it. In practice, optimal variance reduction often reduces the standard error by factors of 5 to 50, enabling orders of magnitude speedup in computation.

### Failure Mode: The Greeks Blowup Under Discontinuity

A subtle but critical failure mode arises when option Greeks are computed near certain boundary conditi
