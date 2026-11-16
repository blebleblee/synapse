# Operational Verification Labs: Bitcoin

## Objective & Operational Lab Setup

Bitcoin represents the first successfully deployed decentralized digital currency operating without a central monetary authority, instead relying on cryptographic proof and distributed consensus protocols to enforce scarcity and transaction validity. From a finance and economics perspective, Bitcoin functions simultaneously as a speculative asset, a potential store of value competing with gold and sovereign bonds, and a payment rail with unique monetary policy characteristics. This laboratory sequence trains you to perform rigorous empirical analysis of Bitcoin's market microstructure, its role in portfolio construction, its behavioral dynamics as a non-traditional asset class, and its macroeconomic implications as an inflation hedge or risk asset depending on prevailing market regimes.

Your operational objective is threefold. First, you will construct Bitcoin return series from raw exchange data and perform foundational statistical characterization including volatility clustering, tail risk quantification, and autocorrelation structure. Second, you will embed Bitcoin within a mean-variance optimization framework alongside traditional equities, bonds, and commodities, analyzing correlation dynamics across market regimes and stress scenarios. Third, you will stress-test portfolio allocation models by simulating Bitcoin drawdown scenarios, liquidity shocks, and regulatory intervention events, then evaluate recovery protocols and hedging strategies. These exercises demand fluency in time-series econometrics, optimization under uncertainty, and real-time data pipeline construction using tools standard to quantitative finance departments: Python with pandas, NumPy, statsmodels, and cvxpy for convex optimization, combined with spreadsheet models for rapid sensitivity analysis and presentation to non-technical stakeholders.

Before commencing laboratory work, establish a standardized analytical environment. Install Python 3.10 or later with a virtual environment to isolate dependencies. Within this environment, install the required packages via pip: `pandas` for time-series manipulation, `numpy` for numerical computation, `matplotlib` and `seaborn` for visualization, `statsmodels` for econometric modeling including GARCH volatility models, `scipy` for statistical distributions and hypothesis testing, `cvxpy` for convex portfolio optimization, and `yfinance` for retrieving historical Bitcoin price data from Yahoo Finance as a no-cost proxy for institutional data feeds. Additionally, prepare a spreadsheet environment—either Microsoft Excel with Solver add-in or Google Sheets with optimization scripts—for rapid scenario modeling and parameter sensitivity sweeps that can be presented to investment committees or risk management teams.

Your data foundation consists of daily Bitcoin USD closing prices spanning at minimum five years to capture multiple market cycles, including the 2017 speculative bubble, the 2020–2021 institutional adoption rally, and the 2022 deleveraging collapse. Supplement Bitcoin data with daily returns for the S&P 500 equity index (SPY ETF), 10-year U.S. Treasury bonds (IEF ETF), gold (GLD ETF), and the VIX volatility index to contextualize Bitcoin's behavior relative to established asset classes and market fear gauges. Store all data in standardized CSV format with date index, adjusted closing prices, and computed log returns to ensure reproducibility and facilitate rapid experimentation.

Establish a project directory structure as follows: `bitcoin_labs/` containing subdirectories `data/` for raw price CSVs, `notebooks/` for Jupyter analysis scripts, `models/` for saved optimization results and statistical model objects, and `reports/` for generated plots and summary tables. This structure mirrors institutional quantitative research workflows and ensures that each exercise builds upon prior results in a traceable, auditable manner.

## Exercise 1: Foundational Practical Implementation

### Objective and Scope

This exercise constructs the empirical foundation for all subsequent Bitcoin analysis. You will retrieve historical Bitcoin price data, compute continuously compounded returns, and perform comprehensive statistical characterization to identify Bitcoin's risk-return profile, distributional properties, and volatility dynamics. The analysis culminates in fitting a GARCH(1,1) model to capture volatility clustering—the empirical regularity that large price movements tend to be followed by large movements and small movements by small movements—a phenomenon critical for risk management and option pricing.

### Data Retrieval and Return Calculation

Begin by retrieving Bitcoin daily price data using the `yfinance` library, which provides a Python interface to Yahoo Finance historical data. Open a Jupyter notebook or Python script and execute the following data acquisition routine, which fetches Bitcoin USD prices (ticker symbol BTC-USD), along with comparative asset data for the S&P 500, Treasury bonds, and gold. The date range spans from January 1, 2018, through December 31, 2023, capturing six full years including multiple bull and bear market cycles.

```python
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from arch import arch_model
from scipy import stats

# Set display options for clarity
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)
sns.set_style('whitegrid')

# Define tickers and date range
tickers = ['BTC-USD', 'SPY', 'IEF', 'GLD', '^VIX']
start_date = '2018-01-01'
end_date = '2023-12-31'

# Download adjusted closing prices
price_data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Adj Close']
price_data.columns = ['Bitcoin', 'SP500', 'Bonds_10Y', 'Gold', 'VIX']

# Handle missing data via forward fill (cryptocurrency markets trade 24/7, traditional assets do not)
price_data = price_data.fillna(method='ffill').dropna()

# Compute log returns (continuously compounded)
returns = np.log(price_data / price_data.shift(1)).dropna()
returns.columns = ['BTC_ret', 'SPY_ret', 'IEF_ret', 'GLD_ret', 'VIX_ret']

# Save processed data
price_data.to_csv('data/bitcoin_prices.csv')
returns.to_csv('data/bitcoin_returns.csv')

print("Data retrieval complete. Shape:", returns.shape)
print("\nFirst 5 rows of return series:")
print(returns.head())
```

This script downloads daily adjusted closing prices, handles missing data through forward-filling (a pragmatic choice given Bitcoin's 24/7 trading versus traditional market hours), computes log returns as $r_t = \ln(P_t / P_{t-1})$, and persists both price and return series to disk for reproducibility. Log returns are preferred over simple returns because they are time-additive and better approximate normality under the Central Limit Theorem for moderate return magnitudes.

### Descriptive Statistics and Distributional Analysis

With return series in hand, compute comprehensive descriptive statistics to quantify Bitcoin's risk-return profile relative to traditional assets. The following code block calculates annualized mean return, annualized volatility (standard deviation), Sharpe ratio assuming a zero risk-free rate for simplicity, skewness, excess kurtosis, and maximum drawdown. These statistics provide the foundational inputs for portfolio optimization and risk budgeting exercises.

```python
# Annualization factors
trading_days = 365  # Bitcoin trades 24/7
risk_free_rate = 0.0  # Assume zero for Sharpe ratio

# Compute annualized statistics
ann_mean = returns.mean() * trading_days
ann_vol = returns.std() * np.sqrt(trading_days)
sharpe = ann_mean / ann_vol
skew = returns.skew()
kurt = returns.kurtosis()  # Excess kurtosis

# Maximum drawdown calculation
def max_drawdown(return_series):
    cum_returns = (1 + return_series).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    return drawdown.min()

max_dd = returns.apply(max_drawdown)

# Compile statistics table
stats_table = pd.DataFrame({
    'Annual Return': ann_mean,
    'Annual Volatility': ann_vol,
    'Sharpe Ratio': sharpe,
    'Skewness': skew,
    'Excess Kurtosis': kurt,
    'Max Drawdown': max_dd
})

print("\nDescriptive Statistics (Annualized):")
print(stats_table.round(4))
```

Examine the output statistics carefully. Bitcoin typically exhibits annualized volatility in the range of 60–80%, vastly exceeding equity volatility (15–20% for the S&P 500) and bond volatility (5–8% for 10-year Treasuries). Despite this extreme volatility, Bitcoin often delivers Sharpe ratios competitive with or superior to equities during bull market phases, justifying its inclusion in speculative growth allocations. However, the skewness statistic frequently reveals negative skew (fat left tail), indicating asymmetric crash risk, while excess kurtosis significantly exceeds zero, confirming fat tails and the inadequacy of Gaussian models for tail risk estimation. Maximum drawdown statistics for Bitcoin routinely exceed 50% during bear markets, compared to 20–30% for equities and single-digit percentages for bonds, underscoring the need for rigorous position sizing and stop-loss discipline.

### Volatility Clustering and GARCH Modeling

Bitcoin returns exhibit pronounced volatility clustering, a stylized fact across financial time series where periods of high volatility persist due to information arrival processes and trader behavior feedback loops. To formally model this phenomenon, estimate a GARCH(1,1) model on Bitcoin returns. The GARCH specification allows conditional variance to depend on past squared residuals (ARCH effect) and past conditional variances (GARCH effect), capturing the empirical reality that volatility is predictable in the short run.

The GARCH(1,1) model for return $r_t$ is specified as:

$$r_t = \mu + \epsilon_t, \quad \epsilon_t = \sigma_t z_t, \quad z_t \sim N(0,1)$$

$$\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$$

where $\omega > 0$, $\alpha \geq 0$, $\beta \geq 0$, and $\alpha + \beta < 1$ ensures stationarity. The parameter $\alpha$ governs the reaction to past shocks (ARCH effect), while $\beta$ controls persistence (GARCH effect). Estimate this model using maximum likelihood via the `arch` package.

```python
# Isolate Bitcoin returns and scale to percentage for numerical stability
btc_returns = returns['BTC_ret'] * 100

# Specify and fit GARCH(1,1) model with constant mean
garch_model = arch_model(btc_returns, vol='Garch', p=1, q=1, mean='constant', dist='normal')
garch_fit = garch_model.fit(disp='off')

print("\nGARCH(1,1) Model Summary:")
print(garch_fit.summary())

# Extract conditional volatility
conditional_vol = garch_fit.conditional_volatility / 100  # Convert back to decimals

# Plot return series and conditional volatility
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axes[0].plot(returns.index, returns['BTC_ret'], linewidth=0.5, color='black', alpha=0.7)
axes[0].set_ylabel('Daily Log Return')
axes[0].set_title('Bitcoin Daily Returns')
axes[0].axhline(0, color='red', linestyle='--', linewidth=0.8)

axes[1].plot(returns.index, conditional_vol, linewidth=1, color='blue')
axes[1].set_ylabel('Conditional Volatility')
axes[1].set_xlabel('Date')
axes[1].set_title('GARCH(1,1) Conditional Volatility')

plt.tight_layout()
plt.savefig('reports/bitcoin_garch_volatility.png', dpi=300)
plt.show()
```

Inspect the GARCH model output. Typical Bitcoin parameter estimates show $\alpha$ in the range of 0.05–0.15 and $\beta$ in the range of 0.80–0.90, implying high persistence ($\alpha + \beta \approx 0.95$) where volatility shocks decay slowly. The conditional volatility plot reveals clear clustering: the 2020 COVID crash, the 2021 leverage flush, and the 2022 bear market all exhibit sustained high-volatility regimes. This persistence has critical implications for risk management—short-term volatility forecasts are far more reliable than long-term forecasts, and position sizing must adapt dynamically to realized volatility regimes rather than relying on unconditional historical volatility estimates.

### Correlation Analysis Across Market Regimes

Bitcoin's correlation with traditional assets is unstable and regime-dependent, a phenomenon that undermines static portfolio optimization models. Compute rolling 90-day correlation between Bitcoin and the S&P 500 to visualize how this relationship evolves through market cycles. During risk-on growth regimes, Bitcoin often exhibits positive correlation with equities as both are driven by liquidity conditions and risk appetite. During tail-risk events, correlations can spike toward one as all risk assets sell off simultaneously, violating diversification assumptions.

```python
# Compute rolling 90-day correlation between Bitcoin and S&P 500
window = 90
rolling_corr = returns['BTC_ret'].rolling(window).corr(returns['SPY_ret'])

# Plot rolling correlation
plt.figure(figsize=(12, 6))
plt.plot(rolling_corr.index, rolling_corr, linewidth=1, color='purple')
plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
plt.axhline(rolling_corr.mean(), color='red', linestyle='--', linewidth=0.8, 
            label=f'Mean Correlation: {rolling_corr.mean():.3f}')
plt.ylabel('Rolling 90-Day Correlation')
plt.xlabel('Date')
plt.title('Bitcoin vs S&P 500 Rolling Correlation')
plt.legend()
plt.tight_layout()
plt.savefig('reports/bitcoin_sp500_rolling_correlation.png', dpi=300)
plt.show()

print(f"\nMean Rolling Correlation (BTC vs SPY): {rolling_corr.mean():.4f}")
print(f"Standard Deviation of Rolling Correlation: {rolling_corr.std():.4f}")
```

Observe how correlation varies substantially over time, often ranging from near-zero to 0.6 or higher. This instability implies that Bitcoin's diversification benefit is not constant and may evaporate precisely when needed most—during systemic market stress. Portfolio construction must therefore incorporate scenario-based correlation assumptions rather than relying on historical averages, and stress testing must explicitly model correlation breakdown scenarios.

### Tail Risk Quantification via Value at Risk

Quantify Bitcoin's tail risk using historical Value at Risk (VaR) and Expected Shortfall (ES, also called Conditional VaR). VaR at confidence level $\alpha$ represents the maximum loss expected with probability $1 - \alpha$, while ES represents the expected loss conditional on exceeding VaR, providing a coherent risk measure that accounts for tail thickness. Compute both at 95% and 99% confidence levels.

```python
# Historical VaR and Expected Shortfall
confidence_levels = [0.95, 0.99]

for conf in confidence_levels:
    var = returns['BTC_ret'].quantile(1 - conf)
    es = returns['BTC_ret'][returns['BTC_ret'] <= var].mean()
    
    print(f"\n{conf*100:.0f}% Confidence Level:")
    print(f"  Value at Risk (VaR): {var:.4f} ({var*100:.2f}%)")
    print(f"  Expected Shortfall (ES): {es:.4f} ({es*100:.2f}%)")
    
    # Annualized equivalents (approximate for single-day VaR)
    print(f"  Annualized VaR: {var * np.sqrt(trading_days):.4f}")
    print(f"  Annualized ES: {es * np.sqrt(trading_days):.4f}")
```

Typical results show 99% daily VaR for Bitcoin in the range of -8% to -12%, meaning that on the worst 1% of days, losses exceed this threshold. Expected Shortfall at 99% confidence often reaches -10% to -15%, indicating that tail losses are significantly more severe than VaR alone suggests. These statistics underscore the necessity of strict position sizing limits for Bitcoin exposure—institutional portfolios typically cap Bitcoin allocations at 1–5% of total capital to ensure that even extreme tail events cannot jeopardize overall portfolio solvency.

This completes the foundational empirical characterization. You have constructed Bitcoin's return distribution, modeled its volatility dynamics, analyzed its time-varying correlation with equities, and quantified tail risk. These statistics form the input layer for portfolio optimization and stress testing exercises.

## Exercise 2: Parameter Variation & Empirical Analysis

### Objective and Scope

This exercise embeds Bitcoin within a multi-asset portfolio optimization framework to determine optimal allocation weights under mean-variance efficiency criteria. You will construct efficient frontiers with and without Bitcoin, analyze the shift in the risk-return tradeoff induced by Bitcoin inclusion, and perform sensitivity analysis across varying expected return assumptions and correlation scenarios. The exercise concludes with a regime-conditional analysis that compares optimal allocations during low-volatility versus high-volatility market regimes, revealing how Bitcoin's portfolio role evolves with market conditions.

### Mean-Variance Portfolio Optimization with Bitcoin

Portfolio optimization under the Markowitz mean-variance framework solves for the weight vector $\mathbf{w}$ that minimizes portfolio variance $\mathbf{w}^T \Sigma \mathbf{w}$ subject to achieving a target expected return $\mathbf{w}^T \mathbf{\mu} = \mu_p$ and the budget constraint $\mathbf{1}^T \mathbf{w} = 1$, where $\Sigma$ is the covariance matrix and $\mathbf{\mu}$ is the vector of expected returns. For practical implementation, construct the efficient frontier by solving this optimization across a grid of target returns and compare the frontier with and without Bitcoin in the asset universe.

Begin by computing the sample covariance matrix and expected return vector from historical data. Use the full six-year sample to estimate these parameters, acknowledging that this assumes return and covariance stationarity, a strong and often violated assumption that we will relax in subsequent sensitivity analysis.

```python
import cvxpy as cp

# Select asset universe: Bitcoin, S&P 500, Bonds, Gold
asset_returns = returns[['BTC_ret', 'SPY_ret', 'IEF_ret', 'GLD_ret']].copy()
asset_names = ['Bitcoin', 'S&P 500', '10Y Treasury', 'Gold']

# Compute annualized mean returns and covariance matrix
mu = asset_returns.mean() * trading_days
Sigma = asset_returns.cov() * trading_days

print("Expected Annual Returns:")
print(mu)
print("\nAnnualized Covariance Matrix:")
print(Sigma)

# Define efficient frontier optimization function
def efficient_frontier(mu, Sigma, target_returns, short_sales=False):
    n_assets = len(mu)
    weights_list = []
    volatilities = []
    
    for target_ret in target_returns:
        w = cp.Variable(n_assets)
        objective = cp.Minimize(cp.quad_form(w, Sigma.values))
        constraints = [
            cp.sum(w) == 1,
            w @ mu.values == target_ret
        ]
        if not short_sales:
            constraints.append(w >= 0)
        
        problem = cp.Problem(objective, constraints)
        problem.solve()
        
        if problem.status == 'optimal':
            weights_list.append(w.value)
            volatilities.append(np.sqrt(problem.value))
        else:
            weights_list.append(None)
            volatilities.append(None)
    
    return np.array(weights_list), np.array(volatilities)

# Generate target return grid from minimum to maximum asset returns
target_returns = np.linspace(mu.min(), mu.max(), 50)

# Compute efficient frontier WITH Bitcoin
weights_with_btc, vol_with_btc = efficient_frontier(mu, Sigma, target_returns, short_sales=False)

# Compute efficient frontier WITHOUT Bitcoin (exclude first asset)
mu_no_btc = mu[1:]
Sigma_no_btc = Sigma.iloc[1:, 1:]
target_returns_no_btc = np.linspace(mu_no_btc.min(), mu_no_btc.max(), 50)
weights_no_btc, vol_no_btc = efficient_frontier(mu_no_btc, Sigma_no_btc, target_returns_no_btc, short_sales=False)

# Plot efficient frontiers
plt.figure(figsize=(12, 8))
plt.plot(vol_no_btc * 100, target_returns_no_btc * 100, 'b-', linewidth=2, label='Efficient Frontier (No Bitcoin)')
plt.plot(vol_with_btc * 100, target_returns * 100, 'r-', linewidth=2, label='Efficient Frontier (With Bitcoin)')

# Plot individual assets
for i, name in enumerate(asset_names):
    plt.scatter(np.sqrt(Sigma.iloc[i, i]) * 100, mu.iloc[i] * 100, s=100, label=name, zorder=5)

plt.xlabel('Annualized Volatility (%)')
plt.ylabel('Expected Annual Return (%)')
plt.title('Efficient Frontier: Impact of Bitcoin Inclusion')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('reports/efficient_frontier_bitcoin.png', dpi=300)
plt.show()
```

Examine the efficient frontier plots. The inclusion of Bitcoin typically shifts the efficient frontier upward and to the right, expanding the feasible risk-return space. At high target return levels, Bitcoin enables portfolios to achieve returns unattainable with traditional assets alone, albeit at substantially higher volatility. At moderate target returns, Bitcoin may provide marginal efficiency gains if its high return compensates for the increased variance it introduces. However, at low target returns near the minimum-variance portfolio, Bitcoin is typically excluded entirely as its volatility contribution dominates its return benefit.

### Optimal Allocation Analysis and Sensitivity

Identify the maximum Sharpe ratio portfolio, which represents the tangency portfolio in mean-variance space and maximizes risk-adjusted return. Extract the optimal weights and analyze Bitcoin's allocation across different optimization scenarios.

```python
# Find maximum Sharpe ratio portfolio WITH Bitcoin
sharpe_ratios_with_btc = target_returns / vol_with_btc
max_sharpe_idx = np.nanargmax(sharpe_ratios_with_btc)
optimal_weights_with_btc = weights_with_btc[max_sharpe_idx]
optimal_return_with_btc = target_returns[max_sharpe_idx]
optimal_vol_with_btc = vol_with_btc[max_sharpe_idx]
optimal_sharpe_with_btc = sharpe_ratios_with_btc[max_sharpe_idx]

print("\nMaximum Sharpe Ratio Portfolio (With Bitcoin):")
for i, name in enumerate(asset_names):
    print(f"  {name}: {optimal_weights_with_btc[i]*100:.2f}%")
print(f"Expected Return: {optimal_return_with_btc*100:.2f}%")
print(f"Volatility: {optimal_vol_with_btc*100:.2f}%")
print(f"Sharpe Ratio: {optimal_sharpe_with_btc:.4f}")

# Find maximum Sharpe ratio portfolio WITHOUT Bitcoin
sharpe_ratios_no_btc = target_returns_no_btc / vol_no_btc
max_sharpe_idx_no_btc = np.nanargmax(sharpe_ratios_no_btc)
optimal_weights_no_btc = weights_no_btc[max_sharpe_idx_no_btc]
optimal_return_no_btc = target_returns_no_btc[max_sharpe_idx_no_btc]
optimal_vol_no_btc = vol_no_btc[max_sharpe_idx_no_btc]
optimal_sharpe_no_btc = sharpe_ratios_no_btc[max_sharpe_idx_no_btc]

print("\nMaximum Sharpe Ratio Portfolio (Without Bitcoin):")
for i, name in enumerate(asset_names[1:]):
    print(f"  {name}: {optimal_weights_no_btc[i]*100:.2f}%")
print(f"Expected Return: {optimal_return_no_btc*100:.2f}%")
print(f"Volatility: {optimal_vol_no_btc*100:.2f}%")
print(f"Sharpe Ratio: {optimal_sharpe_no_btc:.4f}")

# Compute improvement from Bitcoin inclusion
sharpe_improvement = (optimal_sharpe_with_btc - optimal_sharpe_no_btc) / optimal_sharpe_no_btc * 100
print(f"\nSharpe Ratio Improvement from Bitcoin: {sharpe_improvement:.2f}%")
```

Typical results show Bitcoin allocations in the maximum Sharpe portfolio ranging from 2% to 10% depending on the sample period, with higher allocations during bull markets when Bitcoin's historical return is elevated. The Sharpe ratio improvement from Bitcoin inclusion often ranges from 5% to 30%, justifying its consideration in growth-oriented portfolios despite its volatility. However, these results are critically dependent on the input parameters—small changes in expected return assumptions can dramatically alter optimal weights due to Bitcoin's extreme volatility.

Perform sensitivity analysis by varying Bitcoin's expected return assumption across a plausible range while holding other parameters constant. This reveals the allocation's sensitivity to return forecasts, a crucial consideration given the uncertainty in estimating Bitcoin's forward-looking return.

```python
# Sensitivity analysis: vary Bitcoin expected return
btc_return_scenarios = np.linspace(0.0, 0.50, 11)  # 0% to 50% annual return
btc_allocations = []
portfolio_sharpes = []

for btc_ret in btc_return_scenarios:
    mu_scenario = mu.copy()
    mu_scenario.iloc[0] = btc_ret  # Override Bitcoin expected return
    
    # Find maximum Sharpe portfolio for this scenario
    target_rets_scenario = np.linspace(mu_scenario.min(), mu_scenario.max(), 50)
    weights_scenario, vol_scenario = efficient_frontier(mu_scenario, Sigma, target_rets_scenario, short_sales=False)
    sharpe_scenario = target_rets_scenario / vol_scenario
    max_sharpe_idx_scenario = np.nanargmax(sharpe_scenario)
    
    btc_allocations.append(weights_scenario[max_sharpe_idx_scenario][0] * 100)
    portfolio_sharpes.append(sharpe_scenario[max_sharpe_idx_scenario])

# Plot sensitivity results
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].plot(btc_return_scenarios * 100, btc_allocations, 'o-', linewidth=2, markersize=6)
axes[0].set_xlabel('Bitcoin Expected Annual Return (%)')
axes[0].set_ylabel('Optimal Bitcoin Allocation (%)')
axes[0].set_title('Allocation Sensitivity to Return Assumption')
axes[0].grid(True, alpha=0.3)

axes[1].plot(btc_return_scenarios * 100, portfolio_sharpes, 'o-', linewidth=2, markersize=6, color='red')
axes[1].set_xlabel('Bitcoin Expected Annual Return (%)')
axes[1].set_ylabel('Portfolio Sharpe Ratio')
axes[1].set_title('Sharpe Ratio vs Bitcoin Return Assumption')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('reports/bitcoin_allocation_sensitivity.png', dpi=300)
plt.show()
```

The sensitivity plots reveal that Bitcoin allocation rises sharply with expected return assumptions, often reaching portfolio cap constraints (e.g., 10% maximum allocation) at modest return assumptions of 20–30% annually. This high sensitivity underscores the danger of over-optimizing on historical returns—if Bitcoin's future return reverts closer to traditional asset levels, the historical optimal allocation could be severely misspecified. Institutional practice therefore often imposes hard allocation caps (e.g., 1–5%) determined by risk budgeting rather than unconstrained mean-variance optimization.

### Regime-Conditional Optimization

Bitcoin's risk and return characteristics vary dramatically across market volatility regimes. Construct regime-conditional portfolios by segmenting the return sample into low-volatility and high-volatility periods based on VIX levels, then re-optimize within each regime. This approach better reflects the non-stationary nature of financial markets and provides actionable guidance for dynamic allocation strategies.

```python
# Define volatility regimes based on VIX median
vix_median = price_data['VIX'].median()
low_vol_periods = returns.index[price_data['VIX'] <= vix_median]
high_vol_periods = returns.index[price_data['VIX'] > vix_median]

# Compute regime-specific statistics
returns_low_vol = asset_returns.loc[low_vol_periods]
returns_high_vol = asset_returns.loc[high_vol_periods]

mu_low_vol = returns_low_vol.mean() * trading_days
Sigma_low_vol = returns_low_vol.cov() * trading_days

mu_high_vol = returns_high_vol.mean() * trading_days
Sigma_high_vol = returns_high_vol.cov() * trading_days

print("\nLow Volatility Regime Statistics:")
print("Expected Returns:", mu_low_vol.values)
print("Volatilities:", np.sqrt(np.diag(Sigma_low_vol.values)))

print("\nHigh Volatility Regime Statistics:")
print("Expected Returns:", mu_high_vol.values)
print("Volatilities:", np.sqrt(np.diag(Sigma_high_vol.values)))

# Optimize for each regime
target_rets_low = np.linspace(mu_low_vol.min(), mu_low_vol.max(), 50)
weights_low_vol, vol_low_vol = efficient_frontier(mu_low_vol, Sigma_low_vol, target_rets_low, short_sales=False)
sharpe_low_vol = target_rets_low / vol_low_vol
max_sharpe_idx_low = np.nanargmax(sharpe_low_vol)
optimal_weights_low_vol = weights_low_vol[max_sharpe_idx_low]

target_rets_high = np.linspace(mu_high_vol.min(), mu_high_vol.max(), 50)
weights_high_vol, vol_high_vol = efficient_frontier(mu_high_vol, Sigma_high_vol, target_rets_high, short_sales=False)
sharpe_high_vol = target_rets_high / vol_high_vol
max_sharpe_idx_high = np.nanargmax(sharpe_high_vol)
optimal_weights_high_vol = weights_high_vol[max_sharpe_idx_high]

# Compare allocations
regime_comparison = pd.DataFrame({
    'Low Volatility Regime': optimal_weights_low_vol * 100,
    'High Volatility Regime': optimal_weights_high_vol * 100
}, index=asset_names)

print("\nOptimal Allocations by Volatility Regime (%):")
print(regime_comparison.round(2))
```

Regime analysis typically reveals that Bitcoin allocations should be reduced or eliminated during high-volatility regimes when its correlation with equities increases and its diversification benefit diminishes. Conversely, during low-volatility periods, Bitcoin may command higher allocations as its asymmetric return profile and lower correlation provide effective diversification against equity market complacency. This finding supports dynamic tactical allocation frameworks that adjust Bitcoin exposure in response to realized volatility and correlation rather than maintaining static strategic weights.

### Correlation Stress Testing

Perform a stress test by artificially increasing Bitcoin's correlation with equities to 0.8 (near perfect correlation during market crashes) and re-optimize the portfolio. This scenario models the tail risk that Bitcoin fails to provide diversification precisely when needed most.

```python
# Construct stressed covariance matrix with elevated Bitcoin-equity correlation
Sigma_stressed = Sigma.copy()
btc_vol = np.sqrt(Sigma_stressed.iloc[0, 0])
spy_vol = np.sqrt(Sigma_stressed.iloc[1, 1])
stressed_cov = 0.8 * btc_vol * spy_vol  # Correlation = 0.8
Sigma_stressed.iloc[0, 1] = stressed_cov
Sigma_stressed.iloc[1, 0] = stressed_cov

# Optimize under stressed correlation
target_rets_stressed = np.linspace(mu.min(), mu.max(), 50)
weights_stressed, vol_stressed = efficient_frontier(mu, Sigma_stressed, target_rets_stressed, short_sales=False)
sharpe_stressed = target_rets_stressed / vol_stressed
max_sharpe_idx_stressed = np.nanargmax(sharpe_stressed)
optimal_weights_stressed = weights_stressed[max_sharpe_idx_stressed]

# Compare base case vs stressed allocations
stress_comparison = pd.DataFrame({
    'Base Case': optimal_weights_with_btc * 100,
    'Stressed Correlation (0.8)': optimal_weights_stressed * 100
}, index=asset_names)

print("\nAllocation Comparison: Base vs Stressed Correlation (%):")
print(stress_comparison.round(2))
```

Under elevated correlation stress, optimal Bitcoin allocation typically drops by 50% or more as the optimizer recognizes that Bitcoin no longer provides differentiated risk exposure. This result justifies the use of correlation-adjusted risk limits and dynamic hedging strategies that reduce Bitcoin exposure when realized correlation with equities trends upward.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Objective and Scope

This exercise subjects Bitcoin portfolio allocations to extreme stress scenarios that test the robustness of optimization-based strategies under tail events, liquidity shocks, and regulatory interventions. You will simulate Bitcoin crash scenarios with varying severity and speed, analyze the impact on portfolio value and recovery time, and develop quantitative protocols for dynamic de-risking and rebalancing. The exercise concludes with a recovery protocol framework that specifies trigger conditions and position adjustment rules designed to preserve capital during extended Bitcoin drawdowns.

### Scenario 1: Bitcoin Crash with Varying Severity

Simulate a range of Bitcoin price crash scenarios from -30% to -80% and compute the resulting portfolio drawdown for various initial Bitcoin allocation levels. This analysis quantifies the relationship between Bitcoin position size and portfolio tail risk, informing risk budgeting decisions.

```python
# Define crash scenarios and initial allocations
crash_scenarios = np.array([-0.30, -0.50, -0.70, -0.80])  # -30% to -80%
initial_allocations = np.array([0.01, 0.03, 0.05, 0.10, 0.20])  # 1% to 20%

# Assume remaining portfolio is 60% equities, 30% bonds, 10% gold
remaining_weights = np.array([0.60, 0.30, 0.10])

# Simulate portfolio drawdowns (assume other assets remain flat for simplicity)
drawdown_matrix = np.zeros((len(crash_scenarios), len(initial_allocations)))

for i, crash in enumerate(crash_scenarios):
    for j, btc_alloc in enumerate(initial_allocations):
        portfolio_return = btc_alloc * crash + (1 - btc_alloc) * 0.0  # Other assets flat
        drawdown_matrix[i, j] = portfolio_return

# Convert to DataFrame for clarity
drawdown_df = pd.DataFrame(
    drawdown_matrix * 100,
    index=[f"{crash*100:.0f}% BTC Crash" for crash in crash_scenarios],
    columns=[f"{alloc*100:.0f}% BTC Allocation" for alloc in initial_allocations]
)

print("\nPortfolio Drawdown Matrix (%): Bitcoin Crash Scenarios")
print(drawdown_df.round(2))

# Visualize drawdown heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(drawdown_df, annot=True, fmt='.2f', cmap='Reds', cbar_kws={'label': 'Portfolio Drawdown (%)'})
plt.title('Portfolio Drawdown: Bitcoin Crash Severity vs Allocation')
plt.tight_layout()
plt.savefig('reports/bitcoin_crash_drawdown_heatmap.png', dpi=300)
plt.show()
```

The drawdown matrix reveals a linear relationship between Bitcoin allocation and portfolio loss for a given crash magnitude, as expected. A 5% Bitcoin allocation experiencing an 80% crash generates a 4% portfolio drawdown, manageable within institutional risk tolerance. However, a 20% Bitcoin allocation under the same scenario produces a 16% portfolio drawdown, approaching or exceeding typical risk limits. This analysis justifies the common institutional practice of capping Bitcoin exposure at 5% or less to ensure that even catastrophic Bitcoin-specific events remain portfolio-tolerable.

### Scenario 2: Liquidity Shock and Forced Deleveraging

Model a liquidity shock scenario where Bitcoin crashes 50% over 48 hours and the investor must liquidate 50% of their Bitcoin position at a 10% discount to prevailing market prices due to order book depth constraints and exchange dysfunction. Compute the realized loss and compare to the theoretical mark-to-market loss assuming frictionless liquidation.

```python
# Parameters
initial_btc_allocation = 0.05  # 5% of portfolio
btc_crash = -0.50  # 50% price decline
forced_liquidation_fraction = 0.50  # Must sell half of position
liquidation_discount = 0.10  # 10% slippage penalty

# Portfolio value (normalize to 100)
initial_portfolio_value = 100.0
initial_btc_value = initial_portfolio_value * initial_btc_allocation

# Scenario A: Hold entire position (mark-to-market loss)
btc_value_post_crash_hold = initial_btc_value * (1 + btc_crash)
other_assets_value = initial_portfolio_value * (1 - initial_btc_allocation)
portfolio_value_hold = btc_value_post_crash_hold + other_assets_value
drawdown_hold = (portfolio_value_hold - initial_portfolio_value) / initial_portfolio_value

# Scenario B: Forced liquidation with slippage
btc_value_post_crash_before_liq = initial_btc_value * (1 + btc_crash)
btc_value_liquidated = btc_value_post_crash_before_liq * forced_liquidation_fraction * (1 - liquidation_discount)
btc_value_remaining = btc_value_post_crash_before_liq * (1 - forced_liquidation_fraction)
cash_from_liquidation = btc_value_liquidated
portfolio_value_forced_liq = btc_value_remaining + cash_from_liquidation + other_assets_value
drawdown_forced_liq = (portfolio_value_forced_liq - initial_portfolio_value) / initial_portfolio_value

# Additional loss from slippage
slippage_loss = btc_value_post_crash_before_liq * forced_liquidation_fraction * liquidation_discount
slippage_loss_pct = slippage_loss / initial_portfolio_value

print("\nLiquidity Shock Scenario Analysis:")
print(f"Initial Bitcoin Allocation: {initial_btc_allocation*100:.1f}%")
print(f"Bitcoin Crash Magnitude: {btc_crash*100:.0f}%")
print(f"\nScenario A: Hold Position (No Liquidation)")
print(f"  Portfolio Value: ${portfolio_value_hold:.2f}")
print(f"  Portfolio Drawdown: {drawdown_hold*100:.2f}%")
print(f"\nScenario B: Forced Liquidation (50% of BTC at 10% Discount)")
print(f"  Portfolio Value: ${portfolio_value_forced_liq:.2f}")
print(f"  Portfolio Drawdown: {drawdown_forced_liq*100:.2f}%")
print(f"  Additional Loss from Slippage: {slippage_loss_pct*100:.2f}%")
print(f"\nSlippage Penalty vs Hold Strategy: {(drawdown_forced_liq - drawdown_hold)*100:.2f}%")
```

This scenario demonstrates that forced liquidation during crashes significantly amplifies losses beyond the mark-to-market decline due to slippage and market impact costs. The slippage penalty of 0.25–0.5% of total portfolio value may seem modest but compounds across multiple liquidation events during sustained bear markets. This finding supports pre-positioning stop-loss orders or maintaining dedicated cash reserves to avoid forced selling into illiquid markets, as well as sizing Bitcoin positions such that no liquidation is required even under severe stress.

### Scenario 3: Regulatory Intervention and Repatriation

Simulate a regulatory intervention scenario where a government bans cryptocurrency trading, forcing investors to liquidate all Bitcoin positions within 90 days. Model the price impact of forced selling by the investor base and compute the realized portfolio loss under different assumptions about market depth absorption capacity.

```python
# Parameters
initial_btc_allocation = 0.05
regulatory_forced_sale_period_days = 90
price_impact_per_day = -0.005  # Assume 0.5% daily price decline from forced selling

# Simulate daily price path during liquidation period
days = np.arange(0, regulatory_forced_sale_period_days + 1)
cumulative_price_decline = 1 + (days * price_impact_per_day)
cumulative_price_decline = np.maximum(cumulative_price_decline, 0.30)  # Floor at 70% decline

# Assume investor liquidates pro-rata daily
daily_liquidation_fraction = 1.0 / regulatory_forced_sale_period_days
btc_value_remaining = initial_portfolio_value * initial_btc_allocation
cash_from_liquidation = 0.0

for day in range(1, len(days)):
    daily_btc_value_before_liq = btc_value_remaining * cumulative_price_decline[day]
    daily_liquidation_value = daily_btc_value_before_liq * daily_liquidation_fraction * (1.0 / (1 - daily_liquidation_fraction * (day - 1)))
    cash_from_liquidation += daily_liquidation_value
    btc_value_remaining -= btc_value_remaining * daily_liquidation_fraction

final_portfolio_value = cash_from_liquidation + (initial_portfolio_value * (1 - initial_btc_allocation))
final_drawdown = (final_portfolio_value - initial_portfolio_value) / initial_portfolio_value

# Compare to immediate liquidation at day-0 price
immediate_liquidation_value = initial_portfolio_value * initial_btc_allocation + (initial_portfolio_value * (1 - initial_btc_allocation))
immediate_drawdown = (immediate_liquidation_value - initial_portfolio_value) / initial_portfolio_value

print("\nRegulatory Intervention Scenario: Forced Liquidation Over 90 Days")
print(f"Initial Bitcoin Allocation: {initial_btc_allocation*100:.1f}%")
print(f"Assumed Daily Price Impact: {price_impact_per_day*100:.2f}%")
print(f"\nGradual Liquidation (Pro-Rata Daily):")
print(f"  Final Portfolio Value: ${final_portfolio_value:.2f}")
print(f"  Portfolio Drawdown: {final_drawdown*100:.2f}%")
print(f"\nImmediate Liquidation (Day 0):")
print(f"  Portfolio Drawdown: {immediate_drawdown*100:.2f}%")
print(f"\nIncremental Loss from Delayed Liquidation: {(final_drawdown - immediate_drawdown)*100:.2f}%")

# Plot price path
plt.figure(figsize=(10, 6))
plt.plot(days, cumulative_price_decline, linewidth=2)
plt.axhline(1.0, color='red', linestyle='--', linewidth=1, label='Initial Price')
plt.xlabel('Days Since Regulatory Announcement')
plt.ylabel('Bitcoin Price (Normalized to 1.0)')
plt.title('Bitcoin Price Decline Under Forced Liquidation Scenario')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('reports/regulatory_forced_liquidation_price_path.png', dpi=300)
plt.show()
```

This regulatory scenario illustrates the danger of concentrated liquidation events. Delaying liquidation in hopes of price recovery can backfire if forced selling by the broader investor base drives prices down monotonically. The optimal strategy depends critically on beliefs about market depth and the fraction of total Bitcoin holders subject to the same regulatory constraint. If the constrained population is large relative to market liquidity, immediate liquidation minimizes losses; if small, waiting for panic selling to subside may be optimal. This scenario underscores the importance of jurisdictional diversification and maintaining liquid off-ramps.

### Recovery Protocol Development

Develop a quantitative protocol for dynamic Bitcoin position management during drawdown events. The protocol specifies trigger conditions based on realized drawdown magnitude and volatility regime, with corresponding position adjustment rules designed to preserve capital while maintaining optionality for mean reversion.

```python
# Define recovery protocol trigger rules
def recovery_protocol(current_btc_allocation, btc_drawdown_from_peak, current_vol_regime):
    """
    Dynamic Bitcoin position management protocol.
    
    Parameters:
    - current_btc_allocation: Current Bitcoin weight (0 to 1)
    - btc_drawdown_from_peak: Bitcoin drawdown from recent high (negative value)
    - current_vol_regime: 'low' or 'high' based on VIX threshold
    
    Returns:
    - target_allocation: Recommended Bitcoin allocation
    - action: Description of position adjustment
    """
    
    # Trigger thresholds
    drawdown_threshold_moderate = -0.30  # -30%
    drawdown_threshold_severe = -0.50    # -50%
    
    # Baseline allocation by volatility regime
    baseline_allocation_low_vol = 0.05   # 5% in low vol
    baseline_allocation_high_vol = 0.02  # 2% in high vol
    
    # Determine baseline target
    if current_vol_regime == 'low':
        baseline = baseline_allocation_low_vol
    else:
        baseline = baseline_allocation_high_vol
    
    # Apply drawdown adjustments
    if btc_drawdown_from_peak > drawdown_threshold_moderate:
        # Normal regime: maintain baseline
        target_allocation = baseline
        action = f"Maintain baseline allocation ({target_allocation*100:.1f}%)"
    
    elif drawdown_threshold_severe < btc_drawdown_from_peak <= drawdown_threshold_moderate:
        # Moderate stress: reduce by 50%
        target_allocation = baseline * 0.50
        action = f"Moderate drawdown detected. Reduce allocation to {target_allocation*100:.1f}%"
    
    else:
        # Severe stress: reduce to minimum (1%)
        target_allocation = 0.01
        action = f"Severe drawdown detected. Reduce to minimum allocation (1%)"
    
    return target_allocation, action

# Simulate protocol application across historical drawdown events
btc_prices = price_data['Bitcoin'].copy()
btc_cummax = btc_prices.cummax()
btc_drawdown = (btc_prices - btc_cummax) / btc_cummax

# Determine volatility regime
vol_regime = np.where(price_data['VIX'] <= vix_median, 'low', 'high')

# Initialize protocol simulation
initial_allocation = 0.05
protocol_allocations = []
protocol_actions = []

for i in range(len(btc_drawdown)):
    if i == 0:
        current_allocation = initial_allocation
    else:
        current_allocation = protocol_allocations[-1]
    
    target_alloc, action = recovery_protocol(
        current_allocation,
        btc_drawdown.iloc[i],
        vol_regime[i]
    )
    
    protocol_allocations.append(target_alloc)
    protocol_actions.append(action)

protocol_df = pd.DataFrame({
    'Date': btc_drawdown.index,
    'BTC_Price': btc_prices.values,
    'BTC_Drawdown': btc_drawdown.values,
    'Vol_Regime': vol_regime,
    'Target_Allocation': protocol_allocations
})

# Plot protocol allocation over time
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

axes[0].plot(protocol_df['Date'], protocol_df['BTC_Price'], linewidth=1, color='black')
axes[0].set_ylabel('Bitcoin Price ($)')
axes[0].set_title('Bitcoin Price')
axes[0].set_yscale('log')

axes[1].plot(protocol_df['Date'], protocol_df['BTC_Drawdown'] * 100, linewidth=1, color='red')
axes[1].axhline(-30, color='orange', linestyle='--', linewidth=1, label='-30% Threshold')
axes[1].axhline(-50, color='darkred', linestyle='--', linewidth=1, label='-50% Threshold')
axes[1].set_ylabel('Drawdown (%)')
axes[1].set_title('Bitcoin Drawdown from Peak')
axes[1].legend()

axes[2].plot(protocol_df['Date'], protocol_df['Target_Allocation'] * 100, linewidth=1.5, color='blue')
axes[2].set_ylabel('Target Allocation (%)')
axes[2].set_xlabel('Date')
axes[2].set_title('Dynamic Bitcoin Allocation (Recovery Protocol)')

plt.tight_layout()
plt.savefig('reports/bitcoin_recovery_protocol_backtest.png', dpi=300)
plt.show()

# Compute protocol performance summary
print("\nRecovery Protocol Backtest Summary:")
print(f"Average Allocation: {protocol_df['Target_Allocation'].mean()*100:.2f}%")
print(f"Allocation Volatility (Std Dev): {protocol_df['Target_Allocation'].std()*100:.2f}%")
print(f"Number of Drawdown Reduction Events: {(protocol_df['Target_Allocation'] < initial_allocation).sum()}")
```

The recovery protocol backtest demonstrates how dynamic allocation rules can systematically reduce exposure during severe stress while maintaining presence for recovery participation. During the 2022 Bitcoin bear market, for example, the protocol would have reduced allocation from 5% to 1% as drawdowns exceeded 50%, limiting portfolio losses while preserving optionality. During subsequent recovery phases, allocations gradually return to baseline levels as drawdown metrics improve.

### Portfolio Rebalancing Simulation with Transaction Costs

Simulate a complete portfolio rebalancing cycle incorporating realistic transaction costs and tax considerations. Model quarterly rebalancing where Bitcoin has drifted from its 5% target allocation due to price movements, and compute the optimal rebalancing trade accounting for bid-ask spreads and short-term capital gains taxes.

```python
# Rebalancing simulation parameters
initial_portfolio_value = 1000000  # $1M portfolio
target_btc_allocation = 0.05
rebalancing_frequency_days = 90  # Quarterly
bid_ask_spread = 0.003  # 30 bps spread
short_term_cap_gains_tax = 0.37  # 37% for gains held < 1 year

# Simulate one rebalancing event
btc_price_initial = 40000  # Initial BTC price
btc_price_at_rebalancing = 50000  # Price after 90 days (25% gain)

# Initial position
initial_btc_value = initial_portfolio_value * target_btc_allocation
initial_btc_quantity = initial_btc_value / btc_price_initial

# Value at rebalancing date (before rebalancing)
current_btc_value = initial_btc_quantity * btc_price_at_rebalancing
current_portfolio_value = current_btc_value + (initial_portfolio_value * (1 - target_btc_allocation))
current_btc_allocation = current_btc_value / current_portfolio_value

# Target rebalancing trade
target_btc_value_post_rebalancing = current_portfolio_value * target_btc_allocation
rebalancing_trade_value = target_btc_value_post_rebalancing - current_btc_value
rebalancing_trade_quantity = rebalancing_trade_value / btc_price_at_rebalancing

# Transaction costs (assume selling, so incur bid-ask spread)
if rebalancing_trade_value < 0:  # Selling Bitcoin
    transaction_cost = abs(rebalancing_trade_value) * bid_ask_spread
else:  # Buying Bitcoin
    transaction_cost = abs(rebalancing_trade_value) * bid_ask_spread

# Tax on capital gains (if selling)
if rebalancing_trade_value < 0:
    capital_gain = (btc_price_at_rebalancing - btc_price_initial) * abs(rebalancing_trade_quantity)
    capital_gains_tax = capital_gain * short_term_cap_gains_tax if capital_gain > 0 else 0
else:
    capital_gains_tax = 0

# Total rebalancing cost
total_rebalancing_cost = transaction_cost + capital_gains_tax
rebalancing_cost_pct = total_rebalancing_cost / current_portfolio_value

print("\nPortfolio Rebalancing Simulation:")
print(f"Initial Portfolio Value: ${initial_portfolio_value:,.0f}")
print(f"Target Bitcoin Allocation: {target_btc_allocation*100:.1f}%")
print(f"\nInitial Positions:")
print(f"  Bitcoin Quantity: {initial_btc_quantity:.4f} BTC at ${btc_price_initial:,.0f}")
print(f"  Bitcoin Value: ${initial_btc_value:,.0f}")
print(f"\nAt Rebalancing Date (90 Days Later):")
print(f"  Bitcoin Price: ${btc_price_at_rebalancing:,.0f} ({(btc_price_at_rebalancing/btc_price_initial - 1)*100:+.1f}%)")
print(f"  Current Bitcoin Value: ${current_btc_value:,.0f}")
print(f"  Current Portfolio Value: ${current_portfolio_value:,.0f}")
print(f"  Current Bitcoin Allocation: {current_btc_allocation*100:.2f}%")
print(f"\nRebalancing Trade Required:")
print(f"  Trade Value: ${rebalancing_trade_value:,.0f} ({'SELL' if rebalancing_trade_value < 0 else 'BUY'})")
print(f"  Trade Quantity: {abs(rebalancing_trade_quantity):.4f} BTC")
print(f"\nRebalancing Costs:")
print(f"  Transaction Cost (Bid-Ask Spread): ${transaction_cost:,.2f}")
print(f"  Capital Gains Tax: ${capital_gains_tax:,.2f}")
print(f"  Total Rebalancing Cost: ${total_rebalancing_cost:,.2f}")
print(f"  Cost as % of Portfolio: {rebalancing_cost_pct*100:.3f}%")
```

This simulation quantifies the friction costs of maintaining target allocations. For a $1M portfolio, quarterly rebalancing a 5% Bitcoin allocation with 25% price drift incurs approximately $2,500–$5,000 in combined transaction costs and taxes, or 0.25–0.5% of portfolio value annually. These costs must be weighed against the risk reduction benefits of rebalancing. When Bitcoin exhibits strong momentum, a disciplined rebalancing strategy may underperform a buy-and-hold approach, but it provides critical downside protection by systematically harvesting gains during rallies and reducing exposure before crashes.

## Operational Reference Guide & Diagnostic Checklist

This reference section provides condensed command sequences, diagnostic heuristics, and troubleshooting protocols for Bitcoin portfolio analysis and risk management. Use this guide as a quick-reference companion during live trading and portfolio review sessions.

### Data Acquisition and Validation Checklist

Before commencing any Bitcoin analysis, verify data integrity through the following diagnostic sequence. First, confirm that Bitcoin price data exhibits no gaps exceeding 24 hours, as extended gaps indicate exchange downtime or data feed failures that corrupt return calculations. Execute a missing data audit: `price_data.isnull().sum()` should return zero for Bitcoin; forward-fill only when confident that missing values represent non-trading days for traditional assets. Second, verify that Bitcoin prices do not contain obvious errors such as flash crashes or exchange-specific glitches. Plot the full price series and visually inspect for anomalous single-day spikes exceeding 50% that are not corroborated by news events; if found, replace with linear interpolation or exclude the affected period. Third, confirm that computed returns exhibit no arithmetic errors: the sum of log returns should approximately equal the log of the cumulative price ratio, i.e., $\sum_{t=1}^T r_t \approx \ln(P_T / P_0)$ within numerical precision.

### Statistical Model Diagnostic Protocol

When estimating GARCH models or other time-series specifications, confirm model validity through residual diagnostics. After fitting a GARCH(1,1) model, extract standardized residuals via `garch_fit.std_resid` and perform the following checks. First, test for remaining autocorrelation in standardized residuals using the Ljung-Box Q-statistic at 10 lags; the p-value should exceed 0.05, indicating no remaining serial dependence. Second, test for remaining ARCH effects in squared standardized residuals using the same Ljung-Box test; again, p-value should exceed 0.05. Third, visually inspect the QQ-plot of standardized residuals against the standard normal distribution; deviations in the tails indicate fat-tailed distributions requiring Student-t or GED error distributions rather than Gaussian. If any diagnostic fails, re-estimate the model with higher lag orders (GARCH(2,2)) or alternative error distributions until residuals are well-behaved.

### Portfolio Optimization Solver Diagnostics

When executing mean-variance optimization via `cvxpy`, solver failures or infeasibility errors indicate misspecified constraints or numerically unstable covariance matrices. Apply the following diagnostic sequence. First, verify that the covariance matrix is positive definite by computing its eigenvalues: `np.linalg.eigvals(Sigma.values)` should return all positive values. If negative eigenvalues appear, the covariance matrix is ill-conditioned, likely due to perfect multicollinearity or insufficient sample size; regularize by adding a small ridge term, e.g., `Sigma_reg = Sigma + 0.0001 * np.eye(n_assets)`. Second, confirm that target return constraints are feasible by checking that the requested target return lies between the minimum and maximum asset returns; if not, the problem is infeasible and the optimizer will fail. Third, when optimizations succeed but produce extreme corner solutions (e.g., 100% allocation to a single asset), impose minimum and maximum allocation constraints to enforce diversification, e.g., `constraints.append(w >= 0.01)` and `constraints.append(w <= 0.20)`.

### Real-Time Monitoring and Alert Triggers

For operational Bitcoin portfolio management, establish automated monitoring alerts based on the following trigger conditions. First, implement a drawdown alert that fires when Bitcoin drawdown from recent 30-day high exceeds 20%, signaling elevated crash risk and potential need for position reduction per recovery protocol. Second, implement a correlation alert that fires when 30-day rolling correlation between Bitcoin and S&P 500 exceeds 0.6, indicating breakdown of diversification benefit and justifying tactical allocation reduction. Third, implement a volatility regime alert that fires when 30-day realized Bitcoin volatility exceeds 100% annualized, indicating entry into a high-volatility regime warranting reduced position sizing. Configure these alerts to trigger daily at market close and route notifications to portfolio managers via email or SMS for immediate review.

### Recovery Protocol Decision Tree

When Bitcoin drawdowns exceed protocol thresholds, execute the following decision sequence to determine appropriate position adjustments. Step one: measure current Bitcoin drawdown from 90-day high; if exceeds -30% but remains above -50%, reduce allocation by 50% of baseline target. Step two: assess current volatility regime by comparing 30-day VIX average to historical median; if in high-volatility regime, apply additional 50% reduction factor to target allocation computed in step one. Step three: compute required trade size to reach target allocation and estimate total transaction costs including bid-ask spread and potential tax liability; if transaction costs exceed 0.5% of portfolio value, defer rebalancing by one week and re-evaluate. Step four: execute trade using limit orders placed within 1% of current market price to avoid adverse selection and market impact; if orders do not fill within 24 hours, reassess market conditions and consider breaking trade into smaller tranches over multiple days.

### Stress Test Result Interpretation Framework

When reviewing stress test outputs, apply the following interpretation framework to translate numerical results into actionable portfolio adjustments. For crash scenarios: if simulated portfolio drawdown exceeds institutional risk tolerance (typically 15–20% for moderate-risk mandates), reduce Bitcoin allocation proportionally such that worst-case stress scenario produces acceptable drawdown. For liquidity shock scenarios: if forced liquidation costs exceed 1% of portfolio value, maintain higher cash buffer (3–5% of portfolio) to avoid distressed selling, or negotiate pre-arranged credit lines to bridge temporary liquidity needs. For regulatory intervention scenarios: if simulated losses from forced liquidation exceed 3% of portfolio, consider jurisdictional diversification by splitting Bitcoin holdings across multiple legal entities in different regulatory regimes, reducing concentration of forced-sale risk.

### Code Execution Troubleshooting Guide

Common technical issues during Bitcoin analysis labs and their resolutions: (1) `yfinance` download failures due to Yahoo Finance rate limiting—implement retry logic with exponential backoff or switch to alternative data sources such as CoinGecko API or institutional Bloomberg terminals. (2) `cvxpy` optimization timeout errors—reduce efficient frontier granularity by decreasing number of target return points from 50 to 20, or switch to faster solver backends such as ECOS or OSQP via `problem.solve(solver=cp.ECOS)`. (3) GARCH model convergence failures—increase maximum iterations via `garch_model.fit(options={'maxiter': 1000})` or initialize parameters closer to expected values using `garch_model.fit(starting_values=...)`. (4) Memory overflow errors when processing multi-year daily data—downsample to weekly frequency via `price_data.resample('W').last()` for exploratory analysis before returning to daily frequency for final models. (5) Pandas future warnings about deprecated methods—update forward-fill syntax from `fillna(method='ffill')` to `ffill()` to maintain compatibility with pandas 2.0+.
