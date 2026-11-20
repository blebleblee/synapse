# Operational Verification Labs: Algorithmic Trading

## Objective & Operational Lab Setup

Algorithmic trading represents the intersection of quantitative finance, software engineering, and operational risk management. This laboratory sequence prepares practitioners to design, backtest, and operationalize systematic trading strategies under realistic market microstructure constraints. The exercises progress from foundational momentum strategies through regime-adaptive execution algorithms, culminating in stress testing protocols that simulate liquidity crises, flash crashes, and regulatory circuit breakers.

The operational environment for these labs integrates Python-based quantitative analysis with Excel-based performance attribution and risk decomposition. Unlike academic simulations that assume frictionless markets and infinite liquidity, these exercises embed transaction costs, slippage models, position limits, and margin requirements directly into strategy logic. Each lab produces executable trading algorithms alongside compliance documentation suitable for internal risk committee review or regulatory examination.

The practitioner must establish a working analytical environment with Python 3.10 or later, pandas 2.0+, numpy 1.24+, and matplotlib 3.7+. Market data sources include Yahoo Finance for historical equity prices, Alpha Vantage for intraday tick data, and FRED (Federal Reserve Economic Data) for macroeconomic regime indicators. Excel workbooks serve as the primary interface for performance reporting, drawdown analysis, and Sharpe ratio decomposition. All code modules are production-grade with error handling, logging, and parameter validation suitable for live trading deployment.

The lab environment assumes a simulated portfolio with $1,000,000 initial capital, commission structure of $0.005 per share with $1.00 minimum per trade, and margin requirements of 25% for long positions and 50% for short positions. Position sizing follows the Kelly Criterion with fractional Kelly coefficients between 0.10 and 0.25 to prevent overleveraging. Risk limits include maximum position concentration of 10% of portfolio value per single name, maximum sector exposure of 30%, and maximum portfolio volatility target of 15% annualized.

Each exercise follows a consistent workflow: strategy specification, backtesting implementation, performance attribution, risk decomposition, and operational documentation. Strategy specifications define entry and exit rules, position sizing logic, and stop-loss protocols in pseudocode before implementation. Backtesting engines incorporate realistic execution assumptions including market-on-close fills, bid-ask spread costs, and overnight gap risk. Performance attribution separates alpha generation from beta exposure, transaction costs, and slippage drag. Risk decomposition calculates Value-at-Risk (VaR), Conditional Value-at-Risk (CVaR), and maximum drawdown with 95% confidence intervals.

The operational reference section at the end consolidates parameter lookup tables, diagnostic flowcharts, and regulatory compliance checklists. These artifacts mirror internal controls documentation required by broker-dealers under SEC Rule 15c3-5 (Market Access Rule) and FINRA Rule 3110 (Supervision). Practitioners working in regulated entities must adapt these templates to their firm's specific compliance framework, but the fundamental structure aligns with industry-standard risk management practices.

## Exercise 1: Foundational Practical Implementation

This exercise implements a dual momentum strategy combining relative strength momentum (cross-sectional) with absolute momentum (time-series trend following). The strategy universe consists of nine sector SPDR ETFs: XLB (Materials), XLE (Energy), XLF (Financials), XLI (Industrials), XLK (Technology), XLP (Consumer Staples), XLU (Utilities), XLV (Health Care), and XLY (Consumer Discretionary). The benchmark is SPY (S&P 500 ETF). The operational workflow begins with data acquisition, progresses through signal generation and position sizing, executes simulated trades with realistic cost models, and concludes with performance attribution and risk reporting.

Begin by creating a project directory structure with separate folders for data, code, results, and documentation. The data folder stores historical price series in CSV format with columns for date, open, high, low, close, adjusted close, and volume. The code folder contains modular Python scripts for data processing, signal generation, backtesting, and reporting. The results folder accumulates trade logs, equity curves, and performance metrics. The documentation folder maintains strategy specifications, parameter justification memos, and compliance attestations.

The data acquisition script fetches daily adjusted close prices for all ETFs from Yahoo Finance spanning January 1, 2010 through December 31, 2024. This fifteen-year period captures multiple market regimes including the 2011 European debt crisis, the 2015-2016 commodity collapse, the 2018 Q4 drawdown, the 2020 pandemic crash, and the 2022 inflation-driven bear market. The script implements exponential backoff retry logic to handle API rate limits and validates data quality by checking for missing values, split adjustments, and dividend reinvestment consistency.

```python
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(tickers, start_date, end_date, max_retries=3):
    """
    Fetch adjusted close prices with exponential backoff retry logic.
    
    Parameters:
    -----------
    tickers : list
        List of ticker symbols
    start_date : str
        Start date in 'YYYY-MM-DD' format
    end_date : str
        End date in 'YYYY-MM-DD' format
    max_retries : int
        Maximum number of retry attempts
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with date index and ticker columns containing adjusted close prices
    """
    price_data = pd.DataFrame()
    
    for ticker in tickers:
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                logging.info(f"Fetching {ticker} (attempt {retry_count + 1}/{max_retries})")
                ticker_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                
                if ticker_data.empty:
                    raise ValueError(f"No data returned for {ticker}")
                
                # Validate data quality
                if ticker_data['Adj Close'].isna().sum() > 0:
                    logging.warning(f"{ticker} contains {ticker_data['Adj Close'].isna().sum()} missing values")
                    ticker_data['Adj Close'].fillna(method='ffill', inplace=True)
                
                price_data[ticker] = ticker_data['Adj Close']
                success = True
                logging.info(f"Successfully fetched {ticker}: {len(ticker_data)} bars")
                
            except Exception as e:
                retry_count += 1
                logging.error(f"Error fetching {ticker}: {str(e)}")
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to fetch {ticker} after {max_retries} attempts")
                    raise
    
    # Final data quality checks
    initial_rows = len(price_data)
    price_data.dropna(how='all', inplace=True)
    dropped_rows = initial_rows - len(price_data)
    
    if dropped_rows > 0:
        logging.warning(f"Dropped {dropped_rows} rows with all missing values")
    
    logging.info(f"Final dataset: {len(price_data)} bars across {len(tickers)} tickers")
    
    return price_data

# Execute data acquisition
tickers = ['XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'XLV', 'XLY', 'SPY']
start_date = '2010-01-01'
end_date = '2024-12-31'

prices = fetch_price_data(tickers, start_date, end_date)
prices.to_csv('data/sector_etf_prices.csv')
```

With price data acquired and validated, the next step constructs momentum signals using a dual-filter approach. The relative momentum component ranks all nine sector ETFs by their trailing twelve-month total return, selecting the top three performers for long positions. The absolute momentum filter overlays a trend-following rule: a sector qualifies for inclusion only if its current price exceeds its ten-month simple moving average. This absolute momentum overlay prevents long exposure during bear markets when all sectors exhibit negative momentum. The strategy rebalances monthly on the last trading day, selling current holdings and buying the new top-three qualified sectors with equal weight.

```python
def calculate_momentum_signals(prices, lookback_months=12, ma_months=10, top_n=3):
    """
    Generate dual momentum signals combining relative strength and absolute trend.
    
    Parameters:
    -----------
    prices : pd.DataFrame
        Price data with date index and ticker columns
    lookback_months : int
        Lookback period for relative momentum ranking (months)
    ma_months : int
        Moving average period for absolute momentum filter (months)
    top_n : int
        Number of top-ranked sectors to hold
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with date index and ticker columns containing position weights
    """
    # Exclude SPY from sector universe
    sector_tickers = [col for col in prices.columns if col != 'SPY']
    
    # Calculate monthly returns for momentum ranking
    monthly_prices = prices.resample('M').last()
    
    # Relative momentum: trailing 12-month return
    relative_momentum = monthly_prices[sector_tickers].pct_change(lookback_months)
    
    # Absolute momentum: price vs 10-month SMA
    ma_period_days = ma_months * 21  # Approximate trading days per month
    sma = prices[sector_tickers].rolling(window=ma_period_days).mean()
    absolute_momentum = prices[sector_tickers] > sma
    
    # Resample absolute momentum to monthly
    absolute_momentum_monthly = absolute_momentum.resample('M').last()
    
    # Initialize weights DataFrame
    weights = pd.DataFrame(0.0, index=monthly_prices.index, columns=sector_tickers)
    
    # Generate signals
    for date in relative_momentum.index:
        if pd.isna(relative_momentum.loc[date]).all():
            continue
        
        # Rank sectors by relative momentum
        momentum_rank = relative_momentum.loc[date].rank(ascending=False)
        
        # Filter by absolute momentum
        if date in absolute_momentum_monthly.index:
            absolute_filter = absolute_momentum_monthly.loc[date]
        else:
            continue
        
        # Select top N sectors that pass both filters
        qualified_sectors = []
        for sector in momentum_rank.sort_values().index:
            if absolute_filter[sector] and len(qualified_sectors) < top_n:
                qualified_sectors.append(sector)
        
        # Equal weight allocation
        if len(qualified_sectors) > 0:
            weight_per_sector = 1.0 / len(qualified_sectors)
            for sector in qualified_sectors:
                weights.loc[date, sector] = weight_per_sector
    
    # Forward fill weights to daily frequency
    weights_daily = weights.reindex(prices.index, method='ffill').fillna(0.0)
    
    return weights_daily

# Generate signals
weights = calculate_momentum_signals(prices)
weights.to_csv('data/momentum_weights.csv')
```

The backtesting engine simulates portfolio execution with transaction cost modeling that captures both commission fees and market impact slippage. Commission costs apply the $0.005 per share structure with $1.00 minimum, calculated based on share quantity at execution prices. Market impact slippage models the bid-ask spread cost and price movement caused by order execution. For liquid ETFs trading over one million shares daily, the slippage model applies a linear function of 0.05% of trade value plus 0.10% multiplied by the ratio of trade size to average daily volume. This captures the reality that larger orders incur greater market impact.

Position sizing translates target weights into share quantities while respecting fractional share constraints and minimum trade thresholds. The engine calculates required trades by comparing current holdings to target weights, converting dollar amounts to share quantities, and rounding to integer shares. Trades below $100 are suppressed to avoid excessive commission drag. The execution sequence sells all exiting positions first to free capital, then buys new positions in descending order of target weight to ensure priority allocation if capital constraints bind.

```python
def backtest_strategy(prices, weights, initial_capital=1000000, commission_per_share=0.005, 
                     min_commission=1.0, slippage_fixed=0.0005, slippage_variable=0.001):
    """
    Backtest momentum strategy with realistic transaction costs.
    
    Parameters:
    -----------
    prices : pd.DataFrame
        Daily price data
    weights : pd.DataFrame
        Daily target weights
    initial_capital : float
        Starting portfolio value
    commission_per_share : float
        Commission rate per share
    min_commission : float
        Minimum commission per trade
    slippage_fixed : float
        Fixed slippage as fraction of trade value
    slippage_variable : float
        Variable slippage as fraction of trade value
    
    Returns:
    --------
    tuple
        (equity_curve DataFrame, trades DataFrame, holdings DataFrame)
    """
    # Initialize portfolio state
    cash = initial_capital
    holdings = pd.Series(0, index=weights.columns)
    equity = initial_capital
    
    # Storage for results
    equity_curve = []
    trades_list = []
    holdings_history = []
    
    # Get rebalance dates (monthly)
    rebalance_dates = weights.resample('M').last().index
    
    for date in prices.index:
        # Mark-to-market current holdings
        if date in prices.index:
            holdings_value = (holdings * prices.loc[date]).sum()
            equity = cash + holdings_value
            
            equity_curve.append({
                'date': date,
                'equity': equity,
                'cash': cash,
                'holdings_value': holdings_value
            })
            
            holdings_history.append({
                'date': date,
                **holdings.to_dict()
            })
        
        # Check for rebalance
        if date in rebalance_dates:
            target_weights = weights.loc[date]
            target_value = {ticker: equity * weight for ticker, weight in target_weights.items()}
            current_value = (holdings * prices.loc[date]).to_dict()
            
            # Calculate required trades
            trades = {}
            for ticker in weights.columns:
                target = target_value[ticker]
                current = current_value.get(ticker, 0)
                trade_value = target - current
                
                if abs(trade_value) > 100:  # Minimum trade threshold
                    target_shares = int(target / prices.loc[date, ticker])
                    current_shares = holdings[ticker]
                    trade_shares = target_shares - current_shares
                    trades[ticker] = trade_shares
            
            # Execute sells first
            for ticker, shares in trades.items():
                if shares < 0:  # Sell
                    execution_price = prices.loc[date, ticker]
                    trade_value = abs(shares) * execution_price
                    
                    # Calculate costs
                    commission = max(min_commission, abs(shares) * commission_per_share)
                    slippage = trade_value * (slippage_fixed + slippage_variable * min(abs(shares) / 1000000, 1.0))
                    total_cost = commission + slippage
                    
                    # Update state
                    cash += trade_value - total_cost
                    holdings[ticker] += shares
                    
                    trades_list.append({
                        'date': date,
                        'ticker': ticker,
                        'shares': shares,
                        'price': execution_price,
                        'value': trade_value,
                        'commission': commission,
                        'slippage': slippage,
                        'side': 'SELL'
                    })
            
            # Execute buys
            for ticker, shares in trades.items():
                if shares > 0:  # Buy
                    execution_price = prices.loc[date, ticker]
                    trade_value = shares * execution_price
                    
                    # Calculate costs
                    commission = max(min_commission, shares * commission_per_share)
                    slippage = trade_value * (slippage_fixed + slippage_variable * min(shares / 1000000, 1.0))
                    total_cost = commission + slippage
                    
                    # Check capital availability
                    if cash >= trade_value + total_cost:
                        cash -= (trade_value + total_cost)
                        holdings[ticker] += shares
                        
                        trades_list.append({
                            'date': date,
                            'ticker': ticker,
                            'shares': shares,
                            'price': execution_price,
                            'value': trade_value,
                            'commission': commission,
                            'slippage': slippage,
                            'side': 'BUY'
                        })
                    else:
                        logging.warning(f"{date}: Insufficient cash for {ticker} trade")
    
    equity_df = pd.DataFrame(equity_curve).set_index('date')
    trades_df = pd.DataFrame(trades_list)
    holdings_df = pd.DataFrame(holdings_history).set_index('date')
    
    return equity_df, trades_df, holdings_df

# Run backtest
equity_curve, trades, holdings = backtest_strategy(prices, weights)

equity_curve.to_csv('results/equity_curve.csv')
trades.to_csv('results/trades.csv')
holdings.to_csv('results/holdings.csv')
```

Performance attribution decomposes portfolio returns into components: strategy alpha, market beta, transaction costs, and cash drag. The attribution framework begins with total portfolio return calculated from the equity curve. Market beta return comes from multiplying portfolio beta (estimated via regression against SPY returns) by SPY return. Transaction costs sum all commissions and slippage paid during the period. Cash drag represents the opportunity cost of holding cash rather than invested capital, calculated as the risk-free rate multiplied by average cash balance. Strategy alpha is the residual return after subtracting beta, costs, and cash drag from total return.

```python
def calculate_performance_metrics(equity_curve, trades, prices, risk_free_rate=0.02):
    """
    Calculate comprehensive performance metrics and attribution.
    
    Parameters:
    -----------
    equity_curve : pd.DataFrame
        Time series of portfolio equity
    trades : pd.DataFrame
        Trade log with costs
    prices : pd.DataFrame
        Price data including SPY benchmark
    risk_free_rate : float
        Annual risk-free rate for Sharpe calculation
    
    Returns:
    --------
    dict
        Dictionary of performance metrics
    """
    # Calculate returns
    equity_curve['returns'] = equity_curve['equity'].pct_change()
    spy_returns = prices['SPY'].pct_change()
    
    # Align returns
    returns = equity_curve['returns'].dropna()
    benchmark_returns = spy_returns.reindex(returns.index).dropna()
    aligned_returns = returns.reindex(benchmark_returns.index).dropna()
    
    # Total return
    total_return = (equity_curve['equity'].iloc[-1] / equity_curve['equity'].iloc[0]) - 1
    
    # Annualized return
    years = (equity_curve.index[-1] - equity_curve.index[0]).days / 365.25
    annualized_return = (1 + total_return) ** (1 / years) - 1
    
    # Annualized volatility
    annualized_vol = aligned_returns.std() * np.sqrt(252)
    
    # Sharpe ratio
    excess_return = annualized_return - risk_free_rate
    sharpe_ratio = excess_return / annualized_vol if annualized_vol > 0 else 0
    
    # Maximum drawdown
    cumulative = (1 + aligned_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Beta and alpha
    covariance = np.cov(aligned_returns, benchmark_returns)[0, 1]
    benchmark_variance = benchmark_returns.var()
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
    
    benchmark_annualized = (1 + benchmark_returns.mean()) ** 252 - 1
    alpha = annualized_return - (risk_free_rate + beta * (benchmark_annualized - risk_free_rate))
    
    # Transaction cost analysis
    total_commissions = trades['commission'].sum()
    total_slippage = trades['slippage'].sum()
    total_trade_value = trades['value'].sum()
    commission_drag = total_commissions / equity_curve['equity'].iloc[0]
    slippage_drag = total_slippage / equity_curve['equity'].iloc[0]
    
    # Cash drag
    avg_cash_pct = (equity_curve['cash'] / equity_curve['equity']).mean()
    cash_drag = avg_cash_pct * risk_free_rate * years
    
    # Win rate
    if len(trades) > 0:
        trade_returns = []
        for idx, trade in trades.iterrows():
            if trade['side'] == 'SELL':
                # Find corresponding buy
                ticker = trade['ticker']
                prior_buys = trades[(trades['ticker'] == ticker) & 
                                  (trades['side'] == 'BUY') & 
                                  (trades.index < idx)]
                if len(prior_buys) > 0:
                    buy_price = prior_buys.iloc[-1]['price']
                    sell_price = trade['price']
                    trade_return = (sell_price - buy_price) / buy_price
                    trade_returns.append(trade_return)
        
        win_rate = sum(1 for r in trade_returns if r > 0) / len(trade_returns) if trade_returns else 0
    else:
        win_rate = 0
    
    metrics = {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'annualized_volatility': annualized_vol,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'beta': beta,
        'alpha': alpha,
        'total_commissions': total_commissions,
        'total_slippage': total_slippage,
        'commission_drag_pct': commission_drag * 100,
        'slippage_drag_pct': slippage_drag * 100,
        'cash_drag_pct': cash_drag * 100,
        'avg_cash_allocation_pct': avg_cash_pct * 100,
        'number_of_trades': len(trades),
        'win_rate': win_rate
    }
    
    return metrics

# Calculate metrics
metrics = calculate_performance_metrics(equity_curve, trades, prices)

# Output performance report
print("\n=== MOMENTUM STRATEGY PERFORMANCE REPORT ===\n")
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Annualized Return: {metrics['annualized_return']:.2%}")
print(f"Annualized Volatility: {metrics['annualized_volatility']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
print(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
print(f"\nBeta: {metrics['beta']:.3f}")
print(f"Alpha: {metrics['alpha']:.2%}")
print(f"\nTransaction Costs:")
print(f"  Total Commissions: ${metrics['total_commissions']:,.2f}")
print(f"  Total Slippage: ${metrics['total_slippage']:,.2f}")
print(f"  Commission Drag: {metrics['commission_drag_pct']:.3f}%")
print(f"  Slippage Drag: {metrics['slippage_drag_pct']:.3f}%")
print(f"  Cash Drag: {metrics['cash_drag_pct']:.3f}%")
print(f"\nTrading Activity:")
print(f"  Number of Trades: {metrics['number_of_trades']}")
print(f"  Win Rate: {metrics['win_rate']:.2%}")
print(f"  Average Cash Allocation: {metrics['avg_cash_allocation_pct']:.2f}%")

# Save metrics to Excel for reporting
metrics_df = pd.DataFrame([metrics]).T
metrics_df.columns = ['Value']
metrics_df.to_excel('results/performance_metrics.xlsx')
```

The practitioner must now validate these results against realistic expectations. A well-constructed momentum strategy on sector ETFs should generate annualized returns between 8% and 15%, Sharpe ratios between 0.6 and 1.2, and maximum drawdowns between -20% and -35%. Transaction costs typically consume 0.5% to 1.5% annually for monthly rebalancing strategies. If observed metrics fall outside these ranges, investigate data quality issues, signal construction bugs, or unrealistic execution assumptions.

## Exercise 2: Parameter Variation & Empirical Analysis

Parameter sensitivity analysis reveals which strategy inputs drive performance and which represent arbitrary choices with minimal impact. This exercise systematically varies the momentum lookback period, moving average filter length, and number of positions held, documenting the performance surface across the parameter space. The operational objective is twofold: identify robust parameter regions that perform consistently across variations, and quantify the risk of parameter overfitting where in-sample optimization produces out-of-sample performance degradation.

The parameter grid spans momentum lookback periods from 3 to 18 months in 3-month increments, moving average filter lengths from 6 to 12 months in 2-month increments, and portfolio concentration from 1 to 5 positions. This yields a 6×4×5 grid containing 120 parameter combinations. For computational efficiency, the analysis uses a walk-forward testing framework that simulates realistic out-of-sample conditions. The historical period divides into five equal-length windows of approximately three years each. For each window, the strategy optimizes parameters on the first two years (in-sample) and evaluates performance on the third year (out-of-sample). This mimics the operational reality that practitioners periodically recalibrate strategy parameters based on recent performance.

```python
def walk_forward_analysis(prices, param_grid, train_months=24, test_months=12):
    """
    Perform walk-forward parameter optimization and testing.
    
    Parameters:
    -----------
    prices : pd.DataFrame
        Price data
    param_grid : dict
        Dictionary with 'lookback', 'ma_period', 'top_n' lists
    train_months : int
        In-sample training period (months)
    test_months : int
        Out-of-sample test period (months)
    
    Returns:
    --------
    pd.DataFrame
        Results for each parameter combination and window
    """
    results = []
    
    # Create time windows
    start_date = prices.index[0]
    end_date = prices.index[-1]
    total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    window_months = train_months + test_months
    num_windows = total_months // window_months
    
    for window in range(num_windows):
        window_start = start_date + pd.DateOffset(months=window * window_months)
        train_end = window_start + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        
        if test_end > end_date:
            break
        
        print(f"\n=== Window {window + 1}: Train {window_start.date()} to {train_end.date()}, "
              f"Test {train_end.date()} to {test_end.date()} ===")
        
        train_prices = prices.loc[window_start:train_end]
        test_prices = prices.loc[train_end:test_end]
        
        # In-sample optimization
        best_sharpe = -np.inf
        best_params = None
        
        for lookback in param_grid['lookback']:
            for ma_period in param_grid['ma_period']:
                for top_n in param_grid['top_n']:
                    try:
                        # Generate signals on training data
                        train_weights = calculate_momentum_signals(
                            train_prices, 
                            lookback_months=lookback, 
                            ma_months=ma_period, 
                            top_n=top_n
                        )
                        
                        # Backtest on training data
                        train_equity, train_trades, _ = backtest_strategy(train_prices, train_weights)
                        train_metrics = calculate_performance_metrics(train_equity, train_trades, train_prices)
                        
                        # Track best in-sample Sharpe
                        if train_metrics['sharpe_ratio'] > best_sharpe:
                            best_sharpe = train_metrics['sharpe_ratio']
                            best_params = (lookback, ma_period, top_n)
                        
                    except Exception as e:
                        logging.warning(f"Failed for params ({lookback}, {ma_period}, {top_n}): {str(e)}")
                        continue
        
        # Out-of-sample test with best parameters
        if best_params is not None:
            lookback_best, ma_best, top_n_best = best_params
            print(f"Best in-sample params: lookback={lookback_best}, ma={ma_best}, top_n={top_n_best}, Sharpe={best_sharpe:.3f}")
            
            # Generate signals on test data using optimized parameters
            test_weights = calculate_momentum_signals(
                test_prices, 
                lookback_months=lookback_best, 
                ma_months=ma_best, 
                top_n=top_n_best
            )
            
            # Backtest on test data
            test_equity, test_trades, _ = backtest_strategy(test_prices, test_weights)
            test_metrics = calculate_performance_metrics(test_equity, test_trades, test_prices)
            
            print(f"Out-of-sample Sharpe: {test_metrics['sharpe_ratio']:.3f}")
            
            results.append({
                'window': window + 1,
                'train_start': window_start,
                'train_end': train_end,
                'test_start': train_end,
                'test_end': test_end,
                'lookback': lookback_best,
                'ma_period': ma_best,
                'top_n': top_n_best,
                'is_sharpe': best_sharpe,
                'oos_sharpe': test_metrics['sharpe_ratio'],
                'oos_return': test_metrics['annualized_return'],
                'oos_volatility': test_metrics['annualized_volatility'],
                'oos_max_drawdown': test_metrics['max_drawdown'],
                'oos_alpha': test_metrics['alpha'],
                'oos_beta': test_metrics['beta'],
                'oos_trades': test_metrics['number_of_trades']
            })
    
    return pd.DataFrame(results)

# Define parameter grid
param_grid = {
    'lookback': [3, 6, 9, 12, 15, 18],
    'ma_period': [6, 8, 10, 12],
    'top_n': [1, 2, 3, 4, 5]
}

# Run walk-forward analysis
wf_results = walk_forward_analysis(prices, param_grid)
wf_results.to_csv('results/walk_forward_results.csv', index=False)

# Calculate overfitting metrics
wf_results['sharpe_degradation'] = wf_results['is_sharpe'] - wf_results['oos_sharpe']
wf_results['sharpe_retention'] = wf_results['oos_sharpe'] / wf_results['is_sharpe']

print("\n=== OVERFITTING ANALYSIS ===\n")
print(f"Average In-Sample Sharpe: {wf_results['is_sharpe'].mean():.3f}")
print(f"Average Out-of-Sample Sharpe: {wf_results['oos_sharpe'].mean():.3f}")
print(f"Average Sharpe Degradation: {wf_results['sharpe_degradation'].mean():.3f}")
print(f"Average Sharpe Retention: {wf_results['sharpe_retention'].mean():.2%}")
print(f"\nWorst Window (Sharpe Retention): {wf_results['sharpe_retention'].min():.2%}")
print(f"Best Window (Sharpe Retention): {wf_results['sharpe_retention'].max():.2%}")
```

Parameter stability analysis examines whether optimal parameters remain consistent across walk-forward windows or shift dramatically, indicating regime-dependent behavior. A robust strategy exhibits stable optimal parameters where the best lookback period varies by no more than 3 months across windows, and the optimal number of positions remains within ±1 position. Excessive parameter drift suggests the strategy lacks economic foundation and merely exploits statistical noise.

```python
def analyze_parameter_stability(wf_results):
    """
    Analyze stability of optimal parameters across walk-forward windows.
    
    Parameters:
    -----------
    wf_results : pd.DataFrame
        Walk-forward analysis results
    
    Returns:
    --------
    dict
        Parameter stability metrics
    """
    lookback_std = wf_results['lookback'].std()
    lookback_range = wf_results['lookback'].max() - wf_results['lookback'].min()
    
    ma_period_std = wf_results['ma_period'].std()
    ma_period_range = wf_results['ma_period'].max() - wf_results['ma_period'].min()
    
    top_n_std = wf_results['top_n'].std()
    top_n_range = wf_results['top_n'].max() - wf_results['top_n'].min()
    
    # Calculate transition frequency (how often parameters change)
    lookback_changes = (wf_results['lookback'].diff() != 0).sum()
    ma_changes = (wf_results['ma_period'].diff() != 0).sum()
    top_n_changes = (wf_results['top_n'].diff() != 0).sum()
    
    total_transitions = len(wf_results) - 1
    
    stability_metrics = {
        'lookback_std': lookback_std,
        'lookback_range': lookback_range,
        'lookback_change_rate': lookback_changes / total_transitions if total_transitions > 0 else 0,
        'ma_period_std': ma_period_std,
        'ma_period_range': ma_period_range,
        'ma_change_rate': ma_changes / total_transitions if total_transitions > 0 else 0,
        'top_n_std': top_n_std,
        'top_n_range': top_n_range,
        'top_n_change_rate': top_n_changes / total_transitions if total_transitions > 0 else 0
    }
    
    return stability_metrics

stability = analyze_parameter_stability(wf_results)

print("\n=== PARAMETER STABILITY ANALYSIS ===\n")
print(f"Lookback Period:")
print(f"  Standard Deviation: {stability['lookback_std']:.2f} months")
print(f"  Range: {stability['lookback_range']:.0f} months")
print(f"  Change Rate: {stability['lookback_change_rate']:.0%}")
print(f"\nMoving Average Period:")
print(f"  Standard Deviation: {stability['ma_period_std']:.2f} months")
print(f"  Range: {stability['ma_period_range']:.0f} months")
print(f"  Change Rate: {stability['ma_change_rate']:.0%}")
print(f"\nNumber of Positions:")
print(f"  Standard Deviation: {stability['top_n_std']:.2f}")
print(f"  Range: {stability['top_n_range']:.0f}")
print(f"  Change Rate: {stability['top_n_change_rate']:.0%}")
```

Monte Carlo simulation provides confidence intervals for performance metrics by generating synthetic return paths that preserve statistical properties of observed returns while introducing randomness. The simulation resamples historical daily returns with replacement (bootstrap sampling), reconstructing equity curves from these synthetic return sequences. Running 10,000 simulations produces a distribution of terminal wealth, maximum drawdown, and Sharpe ratio outcomes, enabling calculation of 5th and 95th percentiles as confidence bounds.

```python
def monte_carlo_simulation(returns, initial_capital=1000000, num_simulations=10000, horizon_days=252):
    """
    Generate Monte Carlo simulations via bootstrap resampling.
    
    Parameters:
    -----------
    returns : pd.Series
        Historical daily returns
    initial_capital : float
        Starting portfolio value
    num_simulations : int
        Number of simulation paths
    horizon_days : int
        Simulation horizon in trading days
    
    Returns:
    --------
    dict
        Dictionary with simulation results and confidence intervals
    """
    np.random.seed(42)
    
    # Remove NaN and infinite values
    clean_returns = returns.dropna()
    clean_returns = clean_returns[np.isfinite(clean_returns)]
    
    terminal_values = []
    max_drawdowns = []
    sharpe_ratios = []
    
    for sim in range(num_simulations):
        # Bootstrap resample returns
        simulated_returns = np.random.choice(clean_returns, size=horizon_days, replace=True)
        
        # Generate equity curve
        equity_curve = initial_capital * (1 + simulated_returns).cumprod()
        terminal_value = equity_curve[-1]
        
        # Calculate maximum drawdown
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        max_dd = drawdown.min()
        
        # Calculate Sharpe ratio
        ann_return = (terminal_value / initial_capital) ** (252 / horizon_days) - 1
        ann_vol = simulated_returns.std() * np.sqrt(252)
        sharpe = (ann_return - 0.02) / ann_vol if ann_vol > 0 else 0
        
        terminal_values.append(terminal_value)
        max_drawdowns.append(max_dd)
        sharpe_ratios.append(sharpe)
    
    # Calculate confidence intervals
    tv_5th = np.percentile(terminal_values, 5)
    tv_50th = np.percentile(terminal_values, 50)
    tv_95th = np.percentile(terminal_values, 95)
    
    dd_5th = np.percentile(max_drawdowns, 5)
    dd_50th = np.percentile(max_drawdowns, 50)
    dd_95th = np.percentile(max_drawdowns, 95)
    
    sharpe_5th = np.percentile(sharpe_ratios, 5)
    sharpe_50th = np.percentile(sharpe_ratios, 50)
    sharpe_95th = np.percentile(sharpe_ratios, 95)
    
    results = {
        'terminal_value_5th': tv_5th,
        'terminal_value_median': tv_50th,
        'terminal_value_95th': tv_95th,
        'max_drawdown_5th': dd_5th,
        'max_drawdown_median': dd_50th,
        'max_drawdown_95th': dd_95th,
        'sharpe_5th': sharpe_5th,
        'sharpe_median': sharpe_50th,
        'sharpe_95th': sharpe_95th,
        'terminal_values': terminal_values,
        'max_drawdowns': max_drawdowns,
        'sharpe_ratios': sharpe_ratios
    }
    
    return results

# Run Monte Carlo simulation
mc_results = monte_carlo_simulation(equity_curve['returns'])

print("\n=== MONTE CARLO CONFIDENCE INTERVALS (1-year horizon) ===\n")
print(f"Terminal Value:")
print(f"  5th Percentile: ${mc_results['terminal_value_5th']:,.0f}")
print(f"  Median: ${mc_results['terminal_value_median']:,.0f}")
print(f"  95th Percentile: ${mc_results['terminal_value_95th']:,.0f}")
print(f"\nMaximum Drawdown:")
print(f"  5th Percentile (worst): {mc_results['max_drawdown_5th']:.2%}")
print(f"  Median: {mc_results['max_drawdown_median']:.2%}")
print(f"  95th Percentile (best): {mc_results['max_drawdown_95th']:.2%}")
print(f"\nSharpe Ratio:")
print(f"  5th Percentile: {mc_results['sharpe_5th']:.3f}")
print(f"  Median: {mc_results['sharpe_median']:.3f}")
print(f"  95th Percentile: {mc_results['sharpe_95th']:.3f}")

# Visualize distributions
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].hist(mc_results['terminal_values'], bins=50, edgecolor='black', alpha=0.7)
axes[0].axvline(mc_results['terminal_value_5th'], color='red', linestyle='--', label='5th %ile')
axes[0].axvline(mc_results['terminal_value_median'], color='green', linestyle='--', label='Median')
axes[0].axvline(mc_results['terminal_value_95th'], color='blue', linestyle='--', label='95th %ile')
axes[0].set_xlabel('Terminal Portfolio Value')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Terminal Value Distribution')
axes[0].legend()

axes[1].hist(mc_results['max_drawdowns'], bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(mc_results['max_drawdown_5th'], color='red', linestyle='--', label='5th %ile')
axes[1].axvline(mc_results['max_drawdown_median'], color='green', linestyle='--', label='Median')
axes[1].axvline(mc_results['max_drawdown_95th'], color='blue', linestyle='--', label='95th %ile')
axes[1].set_xlabel('Maximum Drawdown')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Maximum Drawdown Distribution')
axes[1].legend()

axes[2].hist(mc_results['sharpe_ratios'], bins=50, edgecolor='black', alpha=0.7)
axes[2].axvline(mc_results['sharpe_5th'], color='red', linestyle='--', label='5th %ile')
axes[2].axvline(mc_results['sharpe_median'], color='green', linestyle='--', label='Median')
axes[2].axvline(mc_results['sharpe_95th'], color='blue', linestyle='--', label='95th %ile')
axes[2].set_xlabel('Sharpe Ratio')
axes[2].set_ylabel('Frequency')
axes[2].set_title('Sharpe Ratio Distribution')
axes[2].legend()

plt.tight_layout()
plt.savefig('results/monte_carlo_distributions.png', dpi=300)
```

The practitioner must interpret these confidence intervals in context of capital requirements and risk tolerance. If the 5th percentile maximum drawdown exceeds -40%, the strategy poses unacceptable bankruptcy risk for undercapitalized accounts. If the 5th percentile Sharpe ratio falls below 0.3, the strategy lacks robust edge and may underperform during unfavorable market conditions. Institutional investors typically require 95% confidence that maximum drawdown stays above -30% and Sharpe ratio remains above 0.5 before allocating capital.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

Stress testing evaluates strategy behavior during extreme market conditions that lie outside the historical sample. This exercise simulates five crisis scenarios: the 1987 Black Monday crash, the 2008 financial crisis, the 2010 flash crash, the 2020 pandemic crash, and a hypothetical liquidity freeze where bid-ask spreads widen to 2% and market impact increases tenfold. The operational objective is to quantify tail risk exposure and develop contingency protocols for position liquidation, margin calls, and trading halts.

The historical crisis analysis replays the strategy on actual crisis periods, calculating intraday drawdown profiles and recovery times. The 1987 crash simulation focuses on October 19, 1987, when the S&P 500 dropped 20.5% intraday. The 2008 crisis spans September 15 (Lehman bankruptcy) through March 9, 2009 (market bottom), capturing an 18-month drawdown exceeding 50%. The 2010 flash crash concentrates on May 6, 2010, when the Dow Jones fell 1,000 points in minutes before recovering. The 2020 pandemic crash covers February 19 through March 23, 2020, a 33-day period with -34% drawdown.

```python
def stress_test_historical_crisis(prices, weights, crisis_periods):
    """
    Backtest strategy during historical crisis periods.
    
    Parameters:
    -----------
    prices : pd.DataFrame
        Price data
    weights : pd.DataFrame
        Strategy weights
    crisis_periods : dict
        Dictionary mapping crisis names to (start_date, end_date) tuples
    
    Returns:
    --------
    dict
        Crisis performance metrics for each period
    """
    crisis_results = {}
    
    for crisis_name, (start_date, end_date) in crisis_periods.items():
        print(f"\n=== Stress Test: {crisis_name} ===")
        print(f"Period: {start_date} to {end_date}")
        
        # Extract crisis period data
        crisis_prices = prices.loc[start_date:end_date]
        crisis_weights = weights.loc[start_date:end_date]
        
        if len(crisis_prices) == 0:
            print(f"No data available for {crisis_name}")
            continue
        
        # Run backtest
        crisis_equity, crisis_trades, _ = backtest_strategy(crisis_prices, crisis_weights)
        
        # Calculate crisis metrics
        crisis_return = (crisis_equity['equity'].iloc[-1] / crisis_equity['equity'].iloc[0]) - 1
        
        # Intraday drawdown profile
        cumulative = crisis_equity['equity'] / crisis_equity['equity'].iloc[0]
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Recovery time
        recovery_mask = cumulative >= running_max.loc[max_dd_date]
        recovery_dates = crisis_equity.index[recovery_mask]
        if len(recovery_dates) > 0:
            recovery_date = recovery_dates[0]
            recovery_days = (recovery_date - max_dd_date).days
        else:
            recovery_date = None
            recovery_days = None
        
        # Volatility spike
        daily_returns = crisis_equity['equity'].pct_change()
        crisis_vol = daily_returns.std() * np.sqrt(252)
        
        # Compare to benchmark
        spy_crisis = prices['SPY'].loc[start_date:end_date]
        spy_return = (spy_crisis.iloc[-1] / spy_crisis.iloc[0]) - 1
        
        crisis_results[crisis_name] = {
            'start_date': start_date,
            'end_date': end_date,
            'strategy_return': crisis_return,
            'benchmark_return': spy_return,
            'outperformance': crisis_return - spy_return,
            'max_drawdown': max_drawdown,
            'max_dd_date': max_dd_date,
            'recovery_date': recovery_date,
            'recovery_days': recovery_days,
            'annualized_vol': crisis_vol,
            'number_of_trades': len(crisis_trades)
        }
        
        print(f"Strategy Return: {crisis_return:.2%}")
        print(f"Benchmark Return: {spy_return:.2%}")
        print(f"Outperformance: {(crisis_return - spy_return):.2%}")
        print(f"Maximum Drawdown: {max_drawdown:.2%} on {max_dd_date.date()}")
        if recovery_days is not None:
            print(f"Recovery Time: {recovery_days} days")
        else:
            print(f"No recovery within crisis period")
        print(f"Annualized Volatility: {crisis_vol:.2%}")
    
    return crisis_results

# Define crisis periods
crisis_periods = {
    '2008 Financial Crisis': ('2008-09-15', '2009-03-09'),
    '2010 Flash Crash': ('2010-05-06', '2010-05-07'),
    '2020 Pandemic Crash': ('2020-02-19', '2020-03-23'),
    'Q4 2018 Selloff': ('2018-10-01', '2018-12-24'),
    '2022 Bear Market': ('2022-01-03', '2022-10-12')
}

# Run historical stress tests
crisis_results = stress_test_historical_crisis(prices, weights, crisis_periods)

# Convert to DataFrame for reporting
crisis_df = pd.DataFrame(crisis_results).T
crisis_df.to_csv('results/crisis_stress_tests.csv')
```

The hypothetical liquidity freeze scenario models extreme market conditions beyond historical precedent. In this scenario, bid-ask spreads widen from typical 0.01% to 2%, market impact increases from the baseline 0.05% to 0.5%, and position liquidation requires selling 20% of holdings per day over five days rather than immediate full liquidation. This simulates forced deleveraging during systemic credit events where market makers withdraw liquidity and trading venues impose position limits.

```python
def liquidity_freeze_scenario(prices, weights, freeze_start, freeze_duration_days=5,
                              elevated_spread=0.02, elevated_impact=0.005):
    """
    Simulate strategy performance during liquidity freeze.
    
    Parameters:
    -----------
    prices : pd.DataFrame
        Price data
    weights : pd.DataFrame
        Strategy weights
    freeze_start : str
        Date when liquidity freeze begins
    freeze_duration_days : int
        Number of days for forced liquidation
    elevated_spread : float
        Bid-ask spread during freeze
    elevated_impact : float
        Market impact during freeze
    
    Returns:
    --------
    dict
        Liquidation scenario results
    """
    # Find last rebalance before freeze
    rebalance_dates = weights.resample('M').last().index
    freeze_date = pd.Timestamp(freeze_start)
    prior_rebalance = rebalance_dates[rebalance_dates < freeze_date][-1]
    
    # Get positions at start of freeze
    freeze_weights = weights.loc[prior_rebalance]
    initial_capital = 1000000
    
    # Calculate share holdings
    freeze_prices = prices.loc[prior_rebalance]
    holdings = {}
    for ticker in freeze_weights.index:
        if freeze_weights[ticker] > 0:
            position_value = initial_capital * freeze_weights[ticker]
            shares = int(position_value / freeze_prices[ticker])
            holdings[ticker] = shares
    
    # Simulate forced liquidation over freeze period
    cash = 0
    liquidation_log = []
    
    for day in range(freeze_duration_days):
        liquidation_date = freeze_date + pd.Timedelta(days=day)
        if liquidation_date not in prices.index:
            continue
        
        # Liquidate 20% of remaining positions each day
        for ticker, shares in list(holdings.items()):
            if shares > 0:
                shares_to_sell = max(1, int(shares * 0.20))
                execution_price = prices.loc[liquidation_date, ticker]
                
                # Apply elevated transaction costs
                gross_proceeds = shares_to_sell * execution_price
                spread_cost = gross_proceeds * elevated_spread
                impact_cost = gross_proceeds * elevated_impact
                net_proceeds = gross_proceeds - spread_cost - impact_cost
                
                cash += net_proceeds
                holdings[ticker] -= shares_to_sell
                
                liquidation_log.append({
                    'day': day + 1,
                    'date': liquidation_date,
                    'ticker': ticker,
                    'shares_sold': shares_to_sell,
                    'execution_price': execution_price,
                    'gross_proceeds': gross_proceeds,
                    'spread_cost': spread_cost,
                    'impact_cost': impact_cost,
                    'net_proceeds': net_proceeds,
                    'shares_remaining': holdings[ticker]
                })
    
    # Calculate final liquidation value
    final_date = freeze_date + pd.Timedelta(days=freeze_duration_days)
    if final_date in prices.index:
        remaining_value = sum(holdings[ticker] * prices.loc[final_date, ticker] 
                            for ticker in holdings if holdings[ticker] > 0)
    else:
        remaining_value = 0
    
    final_value = cash + remaining_value
    liquidation_loss = (final_value - initial_capital) / initial_capital
    
    total_spread_cost = sum(log['spread_cost'] for log in liquidation_log)
    total_impact_cost = sum(log['impact_cost'] for log in liquidation_log)
    total_transaction_cost = total_spread_cost + total_impact_cost
    transaction_drag = total_transaction_cost / initial_capital
    
    results = {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'liquidation_loss_pct': liquidation_loss * 100,
        'total_spread_cost': total_spread_cost,
        'total_impact_cost': total_impact_cost,
        'transaction_drag_pct': transaction_drag * 100,
        'cash_recovered': cash,
        'remaining_position_value': remaining_value,
        'liquidation_log': pd.DataFrame(liquidation_log)
    }
    
    return results

# Simulate liquidity freeze
freeze_results = liquidity_freeze_scenario(prices, weights, freeze_start='2020-03-15')

print("\n=== LIQUIDITY FREEZE SCENARIO ===\n")
print(f"Initial Capital: ${freeze_results['initial_capital']:,.0f}")
print(f"Final Value: ${freeze_results['final_value']:,.0f}")
print(f"Liquidation Loss: {freeze_results['liquidation_loss_pct']:.2f}%")
print(f"\nTransaction Costs:")
print(f"  Spread Cost: ${freeze_results['total_spread_cost']:,.2f}")
print(f"  Impact Cost: ${freeze_results['total_impact_cost']:,.2f}")
print(f"  Total Transaction Drag: {freeze_results['transaction_drag_pct']:.2f}%")
print(f"\nLiquidation Breakdown:")
print(f"  Cash Recovered: ${freeze_results['cash_recovered']:,.0f}")
print(f"  Remaining Position Value: ${freeze_results['remaining_position_value']:,.0f}")

freeze_results['liquidation_log'].to_csv('results/liquidity_freeze_log.csv', index=False)
```

Recovery protocol development establishes operational procedures for resuming trading after a crisis-induced halt. The protocol addresses three decision points: when to resume systematic signal generation, how to rebuild positions without excessive market impact, and what risk limits to impose during the recovery phase. A prudent recovery protocol waits for volatility to decline below 25% annualized before resuming trading, scales position sizes to 50% of target for the first month, and tightens stop-loss levels from -5% to -3% per position.

```python
def recovery_protocol(prices, crisis_end_date, vol_threshold=0.25, scaling_factor=0.5,
                     scaling_duration_days=30, tight_stop_loss=-0.03):
    """
    Implement post-crisis recovery trading protocol.
    
    Parameters:
    -----------
    prices : pd.DataFrame
        Price data
    crisis_end_date : str
        Date when crisis is deemed over
    vol_threshold : float
        Volatility threshold for resuming trading
    scaling_factor : float
        Position size multiplier during recovery
    scaling_duration_days : int
        Days to maintain reduced position sizing
    tight_stop_loss : float
        Tighter stop-loss during recovery
    
    Returns:
    --------
    dict
        Recovery protocol implementation results
    """
    recovery_start = pd.Timestamp(crisis_end_date)
    
    # Calculate rolling volatility
    spy_returns = prices['SPY'].pct_change()
    rolling_vol = spy_returns.rolling(window=20).std() * np.sqrt(252)
    
    # Find date when volatility drops below threshold
    post_crisis_vol = rolling_vol.loc[recovery_start:]
    resume_dates = post_crisis_vol[post_crisis_vol < vol_threshold].index
    
    if len(resume_dates) > 0:
        resume_date = resume_dates[0]
        wait_days = (resume_date - recovery_start).days
        resume_vol = rolling_vol.loc[resume_date]
    else:
        resume_date = None
        wait_days = None
        resume_vol = None
    
    results = {
        'crisis_end_date': crisis_end_date,
        'vol_threshold': vol_threshold,
        'resume_date': resume_date,
        'wait_days': wait_days,
        'resume_volatility': resume_vol,
        'scaling_factor': scaling_factor,
        'scaling_duration_days': scaling_duration_days,
        'stop_loss': tight_stop_loss
    }
    
    return results

# Develop recovery protocol for 2020 pandemic
recovery = recovery_protocol(prices, crisis_end_date='2020-03-23')

print("\n=== POST-CRISIS RECOVERY PROTOCOL ===\n")
print(f"Crisis End Date: {recovery['crisis_end_date']}")
print(f"Volatility Threshold: {recovery['vol_threshold']:.0%}")
if recovery['resume_date'] is not None:
    print(f"Trading Resume Date: {recovery['resume_date'].date()}")
    print(f"Wait Period: {recovery['wait_days']} days")
    print(f"Volatility at Resume: {recovery['resume_volatility']:.2%}")
else:
    print(f"Volatility never declined below threshold in available data")
print(f"\nRecovery Phase Parameters:")
print(f"  Position Scaling Factor: {recovery['scaling_factor']:.0%}")
print(f"  Scaling Duration: {recovery['scaling_duration_days']} days")
print(f"  Stop-Loss Level: {recovery['stop_loss']:.0%}")
```

The final component of stress testing calculates Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR) using both parametric and historical simulation methods. The parametric VaR assumes normally distributed returns and calculates the 5th percentile loss as 1.645 standard deviations below the mean. The historical VaR sorts actual historical returns and selects the 5th percentile directly. CVaR (Expected Shortfall) averages all losses worse than the VaR threshold, capturing tail risk severity.

```python
def calculate_var_cvar(returns, confidence_level=0.95, horizon_days=1):
    """
    Calculate Value-at-Risk and Conditional Value-at-Risk.
    
    Parameters:
    -----------
    returns : pd.Series
        Historical daily returns
    confidence_level : float
        Confidence level (e.g., 0.95 for 95% VaR)
    horizon_days : int
        Risk horizon in trading days
    
    Returns:
    --------
    dict
        VaR and CVaR metrics using multiple methods
    """
    clean_returns = returns.dropna()
    
    # Scale to horizon
    horizon_returns = clean_returns * np.sqrt(horizon_days)
    
    # Parametric VaR (assumes normality)
    mean_return = horizon_returns.mean()
    std_return = horizon_returns.std()
    z_score = -1.645 if confidence_level == 0.95 else -2.326  # 95% or 99%
    parametric_var = mean_return + z_score * std_return
    
    # Historical VaR
    historical_var = horizon_returns.quantile(1 - confidence_level)
    
    # Conditional VaR (Expected Shortfall)
    var_threshold = historical_var
    tail_losses = horizon_returns[horizon_returns <= var_threshold]
    historical_cvar = tail_losses.mean() if len(tail_losses) > 0 else historical_var
    
    # Cornish-Fisher VaR (accounts for skewness and kurtosis)
    from scipy import stats
    skewness = stats.skew(horizon_returns)
    kurtosis = stats.kurtosis(horizon_returns)
    
    cf_adjustment = (z_score + 
                    (z_score**2 - 1) * skewness / 6 +
                    (z_score**3 - 3*z_score) * kurtosis / 24 -
                    (2*z_score**3 - 5*z_score) * skewness**2 / 36)
    
    cornish_fisher_var = mean_return + cf_adjustment * std_return
    
    results = {
        'confidence_level': confidence_level,
        'horizon_days': horizon_days,
        'parametric_var': parametric_var,
        'historical_var': historical_var,
        'historical_cvar': historical_cvar,
        'cornish_fisher_var': cornish_fisher_var,
        'mean_return': mean_return,
        'std_return': std_return,
        'skewness': skewness,
        'kurtosis': kurtosis
    }
    
    return results

# Calculate VaR/CVaR for strategy
var_metrics = calculate_var_cvar(equity_curve['returns'], confidence_level=0.95, horizon_days=1)

print("\n=== VALUE-AT-RISK AND CONDITIONAL VALUE-AT-RISK ===\n")
print(f"Confidence Level: {var_metrics['confidence_level']:.0%}")
print(f"Horizon: {var_metrics['horizon_days']} day(s)")
print(f"\nVaR Estimates:")
print(f"  Parametric VaR: {var_metrics['parametric_var']:.2%}")
print(f"  Historical VaR: {var_metrics['historical_var']:.2%}")
print(f"  Cornish-Fisher VaR: {var_metrics['cornish_fisher_var']:.2%}")
print(f"\nConditional VaR (Expected Shortfall):")
print(f"  Historical CVaR: {var_metrics['historical_cvar']:.2%}")
print(f"\nDistribution Properties:")
print(f"  Mean Daily Return: {var_metrics['mean_return']:.3%}")
print(f"  Daily Volatility: {var_metrics['std_return']:.3%}")
print(f"  Skewness: {var_metrics['skewness']:.3f}")
print(f"  Excess Kurtosis: {var_metrics['kurtosis']:.3f}")

# Portfolio VaR in dollar terms
portfolio_value = equity_curve['equity'].iloc[-1]
dollar_var = portfolio_value * abs(var_metrics['historical_var'])
dollar_cvar = portfolio_value * abs(var_metrics['historical_cvar'])

print(f"\nPortfolio Risk Metrics:")
print(f"  Current Portfolio Value: ${portfolio_value:,.0f}")
print(f"  1-Day 95% VaR: ${dollar_var:,.0f}")
print(f"  1-Day 95% CVaR: ${dollar_cvar:,.0f}")
```

The practitioner must integrate these stress test results into risk management dashboards and operational run books. A complete operational protocol includes pre-trade risk checks (VaR limit verification before order submission), intraday monitoring (real-time drawdown tracking with circuit breakers at -10% and -15%), and post-crisis recovery procedures (volatility-based trading resumption and scaled position rebuilding). These protocols must be tested quarterly through tabletop exercises where the trading team walks through crisis scenarios and verifies that monitoring systems, kill switches, and escalation procedures function correctly.

## Operational Reference Guide & Diagnostic Checklist

This reference section consolidates essential parameters, diagnostic procedures, and regulatory compliance templates for algorithmic trading operations. The material is organized into quick-reference tables and decision flowcharts suitable for lamination and posting in trading rooms.

### Parameter Lookup Tables

**Momentum Strategy Parameter Ranges**

| Parameter | Conservative | Moderate | Aggressive |
|-----------|-------------|----------|------------|
| Lookback Period | 12-18 months | 9-12 months | 3-6 months |
| MA Filter Length | 10-12 months | 8-10 months | 6-8 months |
| Number of Positions | 5 | 3 | 1-2 |
| Rebalance Frequency | Quarterly | Monthly | Weekly |
| Position Size Cap | 15% | 20% | 33% |
| Stop-Loss | -3% | -5% | -7% |

**Transaction Cost Model Parameters**

| Cost Component | Liquid ETFs | Mid-Cap Stocks | Small-Cap Stocks |
|----------------|-------------|----------------|------------------|
| Commission per Share | $0.005 | $0.005 | $0.005 |
| Minimum Commission | $1.00 | $1.00 | $1.00 |
| Bid-Ask Spread | 0.01% | 0.05% | 0.15% |
| Market Impact (fixed) | 0.05% | 0.10% | 0.20% |
| Market Impact (variable) | 0.10% per $1M | 0.25% per $1M | 0.50% per $1M |

**Risk Limit Framework**

| Metric | Yellow Alert | Red Alert | Circuit Breaker |
|--------|--------------|-----------|-----------------|
| Intraday Drawdown | -5% | -10% | -15% |
| Daily VaR Breach | 1.5x limit | 2.0x limit | 2.5x limit |
| Position Concentration | 25% | 30% | 35% |
| Leverage Ratio | 1.5x | 1.8x | 2.0x |
| Volatility Spike | 30% ann. | 40% ann. | 50% ann. |

### Diagnostic Flowchart: Strategy Underperformance

```text
Is Sharpe Ratio < 0.5 for 6+ months?
├── YES: Proceed to next check
│   └── Is Win Rate < 45%?
│       ├── YES: Signal quality degradation
│       │   └── Actions:
│       │       - Review momentum ranking algorithm
│       │       - Check data quality and adjustments
│       │       - Recalibrate lookback periods
│       └── NO: Transaction cost drag
│           └── Actions:
│               - Reduce rebalancing frequency
│               - Increase minimum trade size
│               - Negotiate lower commissions
└── NO: Is Max Drawdown > -30%?
    ├── YES: Risk management failure
    │   └── Actions:
    │       - Tighten position sizing
    │       - Implement stop-loss discipline
    │       - Add volatility targeting overlay
    └── NO: Monitor and continue
```

### Regulatory Compliance Checklist (SEC Rule 15c3-5)

**Pre-Trade Risk Controls**

- [ ] Order price reasonably related to current market (within 10%)
- [ ] Position size does not exceed 10% of ADV (Average Daily Volume)
- [ ] Aggregate exposure below firm capital limits
- [ ] Margin requirement calculated and available
- [ ] Restricted list screening completed
- [ ] Duplicate order detection active

**Intraday Monitoring**

- [ ] Real-time P&L tracking operational
- [ ] Position limit monitoring functional
- [ ] Kill switch tested and accessible
- [ ] Error account segregation configured
- [ ] Regulatory reporting queue monitored

**Post-Trade Review**

- [ ] All executions matched to intended orders
- [ ] Transaction cost analysis completed
- [ ] Exception reports reviewed and resolved
- [ ] Daily VaR calculation performed
- [ ] Performance attribution documented

### Pre-Flight Verification: Backtest Quality Audit

Execute this checklist before presenting backtest results to investment committees or allocating live capital:

**Data Integrity Checks**

- [ ] Survivorship bias eliminated (includes delisted securities)
- [ ] Look-ahead bias prevented (signals use only prior data)
- [ ] Adjusted for corporate actions (splits, dividends, mergers)
- [ ] Volume filters applied (exclude illiquid periods)
- [ ] Missing data handled appropriately (no forward fill across gaps > 5 days)

**Execution Realism Verification**

- [ ] Commission structure matches broker terms
- [ ] Slippage model calibrated to actual fills
- [ ] Market impact function validated against execution analytics
- [ ] Order timing constraints enforced (no inter-bar execution)
- [ ] Short-sale restrictions applied correctly

**Risk Management Validation**

- [ ] Margin requirements calculated correctly
- [ ] Position limits enforced throughout backtest
- [ ] Stop-loss execution realistic (no perfect fills at stop price)
- [ ] Overnight gaps accounted for (no stop protection across close)
- [ ] Leverage constraints applied consistently

**Statistical Robustness Assessment**

- [ ] Sample size adequate (minimum 100 trades)
- [ ] Out-of-sample period constitutes ≥ 30% of data
- [ ] Walk-forward analysis shows < 30% Sharpe degradation
- [ ] Monte Carlo 5th percentile Sharpe > 0.3
- [ ] Parameter stability confirmed (< 50% change rate)

### Crisis Response Protocol Matrix

| Crisis Indicator | Response Level 1 | Response Level 2 | Response Level 3 |
|------------------|------------------|------------------|------------------|
| VIX > 30 | Increase monitoring frequency to hourly | Reduce position sizes by 25% | Liquidate 50% of portfolio |
| Drawdown > -10% | Halt new position entries | Implement defensive stops at -3% | Activate full liquidation protocol |
| Liquidity Decline (ADV < 50% normal) | Increase execution horizon to 2 days | Increase to 5 days | Suspend trading until liquidity normalizes |
| Margin Call | Liquidate lowest-conviction 20% | Liquidate lowest-conviction 50% | Full liquidation to meet margin |
| Circuit Breaker Triggered | Suspend automated trading | Manual review all open positions | No action until markets reopen |

### Performance Metrics Interpretation Guide

**Sharpe Ratio Bands**

- **> 1.5:** Exceptional performance, likely unsustainable, check for overfitting
- **1.0 - 1.5:** Excellent performance, suitable for institutional allocation
- **0.7 - 1.0:** Good performance, monitor consistency
- **0.4 - 0.7:** Acceptable performance, evaluate fee impact
- **< 0.4:** Marginal performance, insufficient risk compensation

**Maximum Drawdown Assessment**

- **-10% to -20%:** Normal range for equity momentum strategies
- **-20% to -30%:** High but acceptable with strong recovery
- **-30% to -40%:** Severe stress, requires risk limit review
- **> -40%:** Unacceptable, strategy redesign required

**Win Rate Context**

- **Momentum Strategies:** 45-55% typical (large wins, small losses)
- **Mean Reversion:** 60-70% typical (small wins, large losses)
- **Trend Following:** 35-45% typical (very large wins, frequent small losses)

### Code Maintenance Schedule

**Daily Operations**

- Data download and validation (pre-market)
- Signal generation and order creation (9:00 AM)
- Execution monitoring and fill verification (intraday)
- P&L reconciliation and position verification (post-market)

**Weekly Reviews**

- Transaction cost analysis vs. model assumptions
- Parameter drift detection (optimal values vs. current values)
- Correlation structure stability check
- New data series availability assessment

**Monthly Audits**

- Full backtest refresh with latest data
- Walk-forward analysis update
- Performance attribution decomposition
- Risk metrics recalculation (VaR, CVaR, beta)

**Quarterly Enhancements**

- Strategy logic review and potential improvements
- Technology stack updates (libraries, APIs)
- Disaster recovery testing
- Compliance documentation review and updates

This operational reference guide should remain accessible to all trading personnel and updated whenever strategy logic, risk limits, or regulatory requirements change. The diagnostic procedures must be practiced regularly through simulation drills to ensure team proficiency during actual market stress events.
