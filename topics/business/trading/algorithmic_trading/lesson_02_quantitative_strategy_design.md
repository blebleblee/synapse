# Lesson 2: Quantitative Strategy Design

## 1. First-Principles Intuition & Invariants

The fundamental premise of algorithmic trading rests on a deceptively simple observation: market prices contain statistical regularities. These regularities emerge from the collision of three irreducible forces—information asymmetry, behavioral bias, and structural friction—that create temporary mispricings and exploitable patterns. The trader's task is to identify these patterns with sufficient precision, extract them with minimal latency and slippage, and execute them at a scale where the signal persists after transaction costs and market impact.

This is radically different from fundamental investing. A fundamental analyst seeks to understand intrinsic value and hold for years. A quantitative trader operates in a much narrower epistemic window. The signal must decay within days, hours, or seconds. The holding period is measured in units of time that match the frequency at which the pattern regenerates. This means that quantitative strategy design is fundamentally about **signal timing, statistical robustness, and transaction cost management**—not about finding the "best" company or asset.

The core invariant that governs all quantitative trading is the **signal-to-noise ratio**. Every empirical observation in markets contains both signal (the true predictive edge) and noise (random fluctuations, measurement error, and false patterns). As you backtest a strategy on historical data, the signal is real; the noise appears real in the backtest but will not repeat forward. The difference between a profitable backtest and a profitable live strategy is the researcher's ability to distinguish genuine pattern from historical artifact. This requires both mathematical rigor and operational discipline.

Three foundational principles structure quantitative strategy work. **First, statistical significance requires sample size.** If you observe a pattern in fifty trades, you cannot conclude it is real. A proper alpha signal must demonstrate consistency across thousands of independent observations, adjusted for multiple comparisons. **Second, decay and regime change are inevitable.** Every successful strategy eventually becomes overcrowded. Market participants learn the pattern, trade ahead of it, and extract the alpha themselves. A 2% edge that worked in 2018 may generate 0.2% in 2024 after a hundred quant funds replicate it. This means quantitative trading is inherently a treadmill—you must continuously discover new signals while monitoring the decay of existing ones. **Third, transaction costs are not a secondary concern; they are the primary constraint.** A signal with 3% annual alpha is worthless if you pay 4% in commissions, market impact, and slippage. Every strategic decision—holding period, rebalance frequency, position size, execution algorithm—must be evaluated first through the lens of total transaction cost.

## 2. Core Architecture & Mechanics

A quantitative trading strategy consists of four tightly coupled subsystems: the **signal generation engine**, the **position sizing and portfolio construction layer**, the **execution and risk management system**, and the **backtest and analysis framework**. Each layer operates on different time scales and must be designed with explicit awareness of the others.

### The Signal Generation Engine: From Raw Data to Predictive Features

The signal generation process begins not with trading logic but with **data curation**. Raw market data is contaminated. Corporate actions (splits, dividends) distort price series. Index reconstitution events introduce discontinuities. Delisted securities vanish. Time zones create gaps. Illiquid periods embed artifacts. Before you can build a predictive model, you must clean the data with surgical precision.

Consider a simple example: computing daily returns. A naive researcher might compute returns as `(close_today - close_yesterday) / close_yesterday`. This appears straightforward, but it contains multiple failure modes. If a stock split occurs between close_yesterday and close_today, the return will be artificially extreme. If the security was delisted or suspended, yesterday's close is stale. If you are working with index constituents that change over time, you must decide whether to include delisted securities (they will have extreme returns; excluding them introduces survivorship bias). Professional traders build data pipelines that apply corporate action adjustments backward through the price history, maintain separate date indices for each security's active trading period, and explicitly tag data quality flags for each observation.

Once data is clean, feature engineering begins. Raw prices and volumes are too noisy to trade directly. Instead, the signal generation engine transforms raw market data into **features**—engineered variables that compress information about market microstructure, momentum, mean reversion, and cross-asset relationships into numerical signals.

The simplest features are **univariate momentum and mean reversion indicators**. A momentum signal extracts the idea that recent price movement predicts future price movement. A 20-day momentum feature might compute the log return over the trailing 20 trading days: `momentum_20d = ln(close_today / close_20d_ago)`. This feature is high when prices have risen recently, low when they have fallen. Empirically, momentum tends to persist over periods of 1-3 months in equities; very short-term (1-5 day) momentum also reverses in many markets due to microstructure effects. Mean reversion signals capture the opposite intuition: extreme recent moves will reverse. A mean reversion signal might compute the z-score of returns over a rolling window: `zscore = (return_today - mean_return_20d) / std_return_20d`. When the z-score is extreme (say, more than 2 standard deviations), the signal suggests prices will revert toward the mean.

More sophisticated features combine information across **multiple time scales and cross-asset relationships**. A cross-sectional momentum signal ranks all securities in a universe by their recent returns, then constructs a feature that is high for the best performers and low for the worst performers. This captures the idea that relative performance persists within a sector or asset class. A factor such as "value" is constructed by ranking securities by price-to-earnings or price-to-book ratios, then long the cheapest and short the most expensive. Over long horizons, these factor premiums have been well-documented in academic research and persist as exploitable trading signals.

Cointegration signals operate on the principle that two or more securities with correlated long-term price movements sometimes diverge from their historical relationship. When the divergence becomes extreme, a trader can execute a **pair trade**: long the underperformer, short the outperformer, betting that they will converge. The statistical test for cointegration is the Johansen cointegration test or the Engle-Granger two-step method. The signal is the z-score of the residual from the cointegrating relationship. If the actual price relationship deviates more than 2-3 standard deviations from the fitted relationship, the signal becomes actionable.

Statistical arbitrage strategies leverage cointegration across multiple dimensions. A simple example: suppose you identify that technology stocks and semiconductor stocks are cointegrated—over long periods, they move together, but short-term divergences occur. You might construct a feature that is the residual from a multiple regression of tech stocks on semiconductor stocks. When this residual is extreme, you trade it as a mean-reversion signal. The holding period is short (days to weeks) because the driver is microstructure and sentiment, not fundamental value.

All features must be designed with explicit attention to **look-ahead bias and survivorship bias**. Look-ahead bias occurs when your feature uses information that would not have been available at the time of the trading decision. Computing a z-score requires knowing the mean and standard deviation of returns over the window; this information is only fully known at the end of the window. A trader must compute features using only data available at the time of trading. Survivorship bias occurs when you train signals on a universe of securities that includes only those that survived to the present day. If you backtest a strategy on all S&P 500 constituents as of today, you will overstate returns because you exclude companies that went bankrupt or were delisted. The backtest uses only winners.

### Combining Signals: Alpha Models and Portfolio Construction

A single feature is rarely sufficient. Quantitative traders combine multiple features into a **composite alpha score** using regression. The idea is simple: if you have `n` features, and historical returns are correlated with combinations of these features, you can fit a linear model:

`r_i(t+1) = α + β_1 × f_1(t) + β_2 × f_2(t) + ... + β_n × f_n(t) + ε(t+1)`

where `r_i(t+1)` is the return of security `i` over the next period, `f_j(t)` are the features at time `t`, and `β_j` are the fitted coefficients. This is the **alpha model**. The coefficients β tell you the strength of the relationship between each feature and future returns.

The critical requirement is that this model must be **trained on out-of-sample data and tested on holdout data**. A researcher backtests on data from 2015-2020, then validates the model on 2021-2022 data that was never seen during training. If the model trained on 2015-2020 does not work on 2021-2022, it was overfit—the relationships were spurious.

Once you have an alpha model, you convert it into portfolio weights. The simplest approach is **long-only weighting**: compute the alpha score for each security, then allocate capital proportionally to the alpha scores. If security A has an alpha score of 5 and security B has an alpha score of 2, allocate 5/7 of your capital to A and 2/7 to B. This is pure alpha weighting—you own the securities you believe will outperform.

Many institutional traders use **long-short weighting**: you go long the securities with the highest alpha scores and simultaneously short the securities with the lowest (most negative) alpha scores. This creates a **market-neutral** portfolio that is hedged against broad market movements. If the market rises 5%, your longs rise 6% (because of your alpha edge) and your shorts fall 4% (because you are short the underperformers), netting to roughly +1% from alpha regardless of market direction. This is the architecture of a **130/30 fund** (130% long, 30% short, net 100% long) or a pure **market-neutral hedge fund** (50% long, 50% short, net zero).

The portfolio construction step must account for **constraints**: concentration limits, sector exposure limits, and risk budgets. A trader might decide that no single position exceeds 5% of the portfolio, that total long-short imbalance does not exceed 10%, and that the portfolio's tracking error versus the benchmark does not exceed 3% annually. These constraints ensure that the portfolio remains diversified and that concentrated bets do not dominate returns.

One of the most important frameworks for portfolio construction is **risk factor decomposition**. Instead of thinking of the portfolio as a collection of individual securities, you decompose it into exposure to systematic risk factors: market beta, size, value, momentum, volatility, and sector biases. A researcher computes the portfolio's exposure to each factor, then rebalances to ensure exposures align with the strategy's intended risk profile. A mean reversion strategy should be market-neutral (zero market beta) and neutral to momentum (because mean reversion and momentum are opposing forces). A momentum strategy should have positive momentum factor exposure.

### Execution and Transaction Costs: The Silent Constraint

The alpha model and portfolio construction deliver you a set of target positions. Execution is the process of acquiring those positions while minimizing market impact and slippage.

Market impact is the price movement caused by your own trading. If you want to buy 1,000 shares of a stock with daily volume of 100,000 shares, you represent 1% of daily volume. Buying aggressively will drive prices up; a sophisticated execution algorithm will spread the order across the entire trading day or even multiple days, trading opportunistically when prices dip. The cost of market impact is typically modeled as proportional to the square of your trade size divided by volume: `impact ∝ (order_size / volume)^2`. If you trade passively over time, impact is minimal. If you demand immediacy, impact is severe.

Slippage is the difference between the price at which you decide to trade and the price at which your order executes. If the market is bid/ask at 100.00 / 100.05 and you send a market buy order, you execute at 100.05. If you send a limit order at 100.02, you might not fill immediately, and you might miss the move. There is a tradeoff between execution certainty and execution price.

Professional traders model the total cost of a trade as:

`Total Cost = Bid-Ask Spread + Market Impact + Commissions + Borrowing Costs (if short)`

For a trade that takes 2 hours to complete at a typical broker, you might pay:
- Bid-ask spread: 0.5 basis points (0.005%)
- Market impact: 1-3 basis points, depending on the aggressiveness of execution
- Commissions: 0.5 basis points
- Total: roughly 2-4 basis points per round-trip (entry and exit)

If your alpha signal generates 5 basis points of edge per day and you rebalance daily, you earn 5 bp minus 4 bp of costs, leaving 1 bp net. Over a year with 250 trading days, this compounds to roughly 0.25% annual return (highly simplified; volatility and compounding matter). This is the reality: a seemingly attractive alpha signal becomes marginal after costs.

This is why frequency matters. A strategy that rebalances daily must have alpha signals that generate at least 3-5 basis points daily to justify the cost. A strategy that rebalances weekly can survive on 20-30 basis points of alpha per week. A strategy that rebalances quarterly can operate on basis points that scale to roughly 50-100 basis points annually. As you move to higher frequencies, you must have tighter edge and better execution.

### The Backtest Framework: Avoiding Overfitting and Illusion

A backtest is a simulation of how a strategy would have performed in the past. The researcher constructs a time-indexed dataset of prices and features, then simulates trading by computing the signal at each time step, constructing the portfolio, and measuring the return. The key output is the **strategy's P&L** (profit and loss), and from this, you derive the **Sharpe ratio** (excess return divided by volatility), the **maximum drawdown** (the largest cumulative loss from peak to trough), the **win rate** (percentage of profitable trades), and other metrics.

The backtest infrastructure must be architected to prevent several catastrophic errors. The first is **look-ahead bias**. Features must be computed using only information available at the trading decision point. If you compute a feature at 3 PM using data up to 3 PM, you can trade at 3 PM or later, but not at 2:59 PM. Many researchers inadvertently compute features at 4 PM and trade at 3 PM, inflating returns.

The second is **survivorship bias**. When you backtest on the S&P 500, you must account for the fact that the index composition changes over time. A proper backtest includes all constituents that were in the index at each point in history, accounting for when securities were added and removed. A naive approach uses current constituents, which biases results upward because it excludes companies that went bankrupt.

The third is **overfitting**. A researcher with enough features and enough flexibility can fit any historical dataset. If you have 100 features and you fit a regression to predict returns, you will find spurious correlations by chance alone (this is the multiple comparisons problem). You will then backtest this overfitted model on the same data it was trained on, observing stellar returns. But the relationships are not real; they are artifacts of noise. Forward performance will be disappointing.

The defense against overfitting is **rigorous out-of-sample testing**. The standard approach is time-series cross-validation:

1. Select a training window (e.g., 2015-2019).
2. Fit the alpha model on the training window.
3. Test the model on a holdout period immediately following (e.g., 2020).
4. Roll the window forward: train on 2016-2020, test on 2021, etc.
5. Report the aggregate statistics across all holdout periods.

If the strategy performs well on training data but poorly on holdout data, it is overfit. If it performs consistently across all training and holdout periods, the signal is likely real.

A more sophisticated approach is **walk-forward optimization**. Instead of fitting the model once and holding coefficients constant, you refit the model periodically (e.g., every quarter). This allows the strategy to adapt to changing market regimes while still preventing look-ahead bias.

Another critical tool is **permutation testing and Monte Carlo simulation**. If you generate the strategy's returns randomly by shuffling prices, you can construct a null distribution of returns under the hypothesis that the signal is pure noise. If your backtest returns fall far into the right tail of this distribution (with p-value < 0.05), you have evidence that the signal is real, not due to chance. This is more rigorous than simply observing a high Sharpe ratio.

## 3. High-Performance Optimization & Failure Modes

### Realistic Assumptions and Cost Models

The gap between backtest results and live performance is often enormous. A researcher might backtest a strategy and observe a 10% annual return with a 2.0 Sharpe ratio. In live trading, the strategy generates 2% annual returns with a 0.4 Sharpe ratio. The difference is caused by violated assumptions in the backtest.

A common failure is assuming **instantaneous execution at the mid-price**. The backtest assumes you can buy or sell at exactly the mid-market price with no slippage. In reality, you pay the ask when buying and receive the bid when selling. For illiquid securities, the bid-ask spread is 10-50 basis points; for liquid ones, 1-2 basis points. A strategy backtested on illiquid securities will fail when the bid-ask spread alone eats the alpha.

Another failure is **zero market impact**. The backtest assumes you can trade 10 million shares of a security without moving the price. If the security has daily volume of 50 million shares, trading 10 million (20% of daily volume) will generate substantial market impact, easily 1-2% on execution. The backtest shows profit; reality shows loss.

A third failure is **ignoring failed trades**. In live trading, your limit orders sometimes do not fill. In the backtest, you assume they do. If you place a limit order to buy at 100.00 but the price rises to 100.05 before the order fills, you miss the trade. The backtest counts this as a win (you avoided buying at 100.05); reality is that you wanted to be long and you are not. The backtest overstates the win rate.

To avoid these failures, the backtest must incorporate realistic cost models. Include the bid-ask spread explicitly: when you buy, you pay the ask; when you sell, you receive the bid. Model market impact proportional to order size divided by volume. Set a maximum order size (e.g., no single order exceeds 5% of daily volume) and break larger orders into smaller chunks executed over multiple days. Set a fill assumption (e.g., limit orders fill 80% of the time if they remain in the book for more than 1 minute).

### Position Sizing and Leverage

A profitable alpha signal can be scaled by increasing leverage. If a signal generates 1% monthly return with 10% monthly volatility (Sharpe ratio of 0.1), you can double the position size, achieving 2% monthly return at 20% volatility, with the same Sharpe ratio. But leverage introduces drawdown risk and margin calls.

A 20-leverage trader with $1 million in capital controls $20 million in positions. If positions decline 5% in a day, the portfolio loses $1 million—a total loss of capital. A 5% daily move is rare in most markets but not impossible. The trader must maintain a buffer: at minimum, you need enough capital to sustain the largest realistic drawdown without a margin call.

The typical framework is the **Value at Risk (VaR) or Expected Shortfall constraint**. A trader might set a rule: the portfolio's 1-day 95% VaR does not exceed 2% of capital. This means that on a bad day (the 5% worst-case day), the portfolio should not lose more than 2%. Using this constraint, you compute the maximum position size such that VaR is satisfied, then you set leverage accordingly.

A more pragmatic approach is **volatility targeting**. You compute the portfolio's recent realized volatility, then scale positions so that the portfolio's daily volatility is constant (say, 1% daily or 16% annualized). If volatility increases, you reduce position size; if volatility decreases, you increase it. This smooths returns and prevents catastrophic leverage during volatile periods.

### Decay, Overcrowding, and Strategy Lifecycle Management

Every profitable strategy eventually decays. The initial discovery phase often yields the highest returns: 5-10% annually. As the strategy accumulates capital and other traders discover the same pattern, capacity fills. The return per dollar declines. After 2-3 years, the strategy might generate only 1-2% annually. After 5 years, it may be flat.

This decay is not failure; it is inevitability. Once 100 quantitative funds are trading the same mean reversion signal in a specific sector, the arbitrage is competed away. Prices adjust faster. The signal loses predictive power. The trader must either accept lower returns or rotate into new signals.

Effective quantitative trading organizations maintain a **pipeline of signals at different stages of maturity**. Newly discovered signals (in year 1-2) generate high returns but may have high failure risk. Mature signals (in year 3-5) generate lower returns but are stable and well-understood. Legacy signals (in year 5+) may be fully decayed but still deployed because they are low-friction. The portfolio strategy is a mix: allocate capital to a small number of new signals with high uncertainty but high potential return, a larger allocation to proven signals with consistent mid-range returns, and maintain legacy signals as diversifiers.

Monitoring for decay requires rigorous **out-of-sample performance tracking**. Every quarter, you retrain the alpha model and compare the new coefficients and Sharpe ratio to prior quarters. If the Sharpe ratio has declined by more than 20% year-over-year, investigate: Is the market regime changing? Have other traders adopted the same strategy? Is the feature becoming correlated with a known factor premium that is currently out of favor? The answers determine whether to double down (if the decay is temporary), rotate to new signals (if the decay is permanent), or retire the strategy entirely.

### Regime Change and Factor Crowding

One of the harshest realities of quantitative trading is regime change. A strategy that works well in a rising market may fail in a falling market. A strategy that profits from mean reversion in stable periods will be destroyed during a financial crisis when means shift dramatically.

A simple example illustrates the severity. A mean reversion strategy in equities from 2010-2020 would have been profitable: the market was stable, and mean reversion worked. But in March 2020, when the COVID crash occurred, all correlations went to 1. Equities crashed 30% in three weeks. A mean reversion strategy that was long recently beaten-down stocks and short recently outperforming stocks would have lost 20-30% as the crash accelerated. The "reversal" never came because the regime changed fundamentally.

The defense is **regime detection**. A quantitative trading system monitors statistical properties of markets (volatility, correlation structure, the autocorrelation of returns) to detect when regime is shifting. When detection fires, the system either:

1. Reduces position size (de-risk until the new regime stabilizes).
2. Suspends the strategy (stop trading until you can retrain on new data).
3.
