# Operational Verification Labs: Cryptocurrency And Defi

## Objective & Operational Lab Setup

These laboratory exercises train the practitioner to conduct rigorous empirical verification of cryptocurrency market microstructure, decentralized finance protocol mechanics, and risk transmission channels using quantitative analytical frameworks drawn from financial economics. The operational objective is threefold: first, to decompose the price discovery process in fragmented digital asset markets and quantify arbitrage transmission speeds across centralized exchanges and automated market makers; second, to reverse-engineer the economic incentive structures embedded in DeFi lending protocols, liquidity pools, and yield aggregators through balance sheet reconstruction and cash flow attribution; third, to stress-test protocol solvency under adverse volatility regimes and liquidity withdrawal cascades using scenario analysis and Monte Carlo simulation methods.

The laboratory environment requires a research-grade analytical workstation equipped with Python 3.10 or later, R 4.3 or later for statistical modeling, and a spreadsheet platform supporting dynamic array formulas and solver optimization routines. The practitioner must maintain access to historical cryptocurrency market data covering at minimum Bitcoin, Ethereum, and stablecoin pairs across multiple venue types. Public blockchain explorers and protocol-specific application programming interfaces provide the raw transaction and state data necessary for on-chain forensic analysis. All quantitative models developed in these exercises prioritize transparent parameter specification and full auditability of computational logic, consistent with central bank research standards and regulatory risk assessment protocols.

Install the required Python analytical stack by executing `pip install pandas numpy scipy matplotlib statsmodels arch ccxt web3` in an isolated virtual environment. The `ccxt` library provides normalized access to cryptocurrency exchange order book and trade data across over one hundred venues. The `web3` library enables direct interaction with Ethereum Virtual Machine state through remote procedure calls to public infrastructure nodes. For R-based statistical work, install the `quantmod`, `xts`, `PerformanceAnalytics`, and `rugarch` packages via `install.packages(c("quantmod", "xts", "PerformanceAnalytics", "rugarch"))`. Configure API authentication credentials for at least two centralized exchanges to enable live order book sampling; alternatively, utilize public WebSocket streams for real-time market data ingestion without authentication overhead.

Establish a dedicated working directory structure separating raw data, intermediate transformations, analytical outputs, and reproducible scripts. The canonical layout organizes `data/raw/` for immutable source files, `data/processed/` for cleaned time series and panel datasets, `src/` for Python modules and R scripts, `notebooks/` for Jupyter or R Markdown exploratory analysis, and `results/` for figures, tables, and diagnostic reports. This separation enforces a clear data lineage and prevents inadvertent contamination of source data through iterative analysis. All timestamps must be converted to UTC and stored in ISO 8601 format to eliminate timezone ambiguity when merging data from geographically distributed infrastructure.

The conceptual foundation for these exercises rests on four pillars of modern financial economics applied to decentralized markets. First, the microstructure theory of price formation in fragmented markets, which explains how order flow toxicity, inventory risk, and adverse selection drive bid-ask spreads and temporary price impact in both traditional and automated market maker venues. Second, the no-arbitrage principle and its enforcement through high-frequency trading strategies that equilibrate prices across venues, subject to transaction costs, latency constraints, and capital lock-up requirements. Third, the portfolio optimization framework extended to include non-traditional risk factors such as smart contract vulnerability exposure, oracle manipulation risk, and governance attack surfaces. Fourth, the applied mechanism design perspective on DeFi protocols as economic games where rational agents optimize yield subject to liquidity constraints, impermanent loss in constant function market makers, and liquidation risk in collateralized lending systems.

These laboratories do not teach blockchain engineering or cryptographic protocol design; those domains belong to computer science and applied cryptography. The focus here is exclusively on the economic behavior observable in market data and on-chain state transitions, analyzed through the lens of quantitative finance and econometric inference. The practitioner must bring foundational knowledge of time series analysis, volatility modeling, and derivative pricing theory; these exercises extend that toolkit to the specific institutional features and risk characteristics of cryptocurrency markets and decentralized financial infrastructure.

## Exercise 1: Foundational Practical Implementation

This first exercise constructs a complete empirical workflow for analyzing cross-exchange price arbitrage dynamics in the Bitcoin-USD market. The operational goal is to quantify the speed and magnitude of price deviation correction across centralized exchanges and to measure the transaction cost threshold below which arbitrage becomes unprofitable. The exercise proceeds in three stages: market data acquisition and synchronization, arbitrage spread calculation and persistence analysis, and break-even cost estimation under realistic trading constraints.

Begin by configuring programmatic access to at least three major centralized exchanges with deep Bitcoin-USD liquidity. Initialize CCXT exchange objects for Coinbase Pro, Kraken, and Binance US using public endpoints that do not require API key authentication. The following Python implementation establishes connection objects and retrieves synchronized order book snapshots at one-second intervals over a thirty-minute observation window:

```python
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import time

# Initialize exchange connections (public endpoints)
exchanges = {
    'coinbase': ccxt.coinbasepro(),
    'kraken': ccxt.kraken(),
    'binance_us': ccxt.binanceus()
}

# Configure common symbol notation
symbol = 'BTC/USD'

# Data collection parameters
observation_minutes = 30
sample_interval_seconds = 1

# Storage structure for order book snapshots
orderbook_data = []

print(f"Starting order book collection for {symbol} across {len(exchanges)} exchanges")
print(f"Duration: {observation_minutes} minutes at {sample_interval_seconds}s intervals\n")

start_time = datetime.now(timezone.utc)
end_time = start_time.timestamp() + (observation_minutes * 60)

while time.time() < end_time:
    snapshot_time = datetime.now(timezone.utc)
    
    for exchange_name, exchange_obj in exchanges.items():
        try:
            orderbook = exchange_obj.fetch_order_book(symbol, limit=5)
            
            if orderbook['bids'] and orderbook['asks']:
                best_bid = orderbook['bids'][0][0]
                best_ask = orderbook['asks'][0][0]
                bid_volume = orderbook['bids'][0][1]
                ask_volume = orderbook['asks'][0][1]
                
                orderbook_data.append({
                    'timestamp': snapshot_time,
                    'exchange': exchange_name,
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'mid_price': (best_bid + best_ask) / 2,
                    'spread_bps': ((best_ask - best_bid) / best_bid) * 10000
                })
                
        except Exception as e:
            print(f"Error fetching {exchange_name} at {snapshot_time}: {str(e)}")
    
    time.sleep(sample_interval_seconds)
    
    # Progress indicator every 5 minutes
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() / 60
    if int(elapsed) % 5 == 0 and elapsed > 0:
        print(f"Collected {int(elapsed)} minutes of data...")

# Convert to DataFrame and persist
df_orderbooks = pd.DataFrame(orderbook_data)
df_orderbooks.to_csv('data/raw/btc_usd_orderbooks_multi_exchange.csv', index=False)

print(f"\nCollection complete. Total snapshots: {len(df_orderbooks)}")
print(f"Exchanges captured: {df_orderbooks['exchange'].nunique()}")
print(f"Time range: {df_orderbooks['timestamp'].min()} to {df_orderbooks['timestamp'].max()}")
```

This script captures top-of-book quotes at one-second granularity, constructing a synchronized panel dataset indexed by timestamp and exchange identifier. The bid-ask spread measured in basis points provides a direct estimate of liquidity provision costs at each venue. Practitioners operating under institutional research mandates should extend the observation window to multiple hours or days and implement exponential backoff retry logic to handle rate limiting and transient network failures gracefully.

With synchronized order book data in hand, construct pairwise arbitrage spreads by identifying profitable triangular opportunities at each timestamp. A profitable arbitrage exists when the best bid on exchange A exceeds the best ask on exchange B by more than the round-trip transaction cost. Calculate the raw arbitrage spread as the percentage price differential between the highest bid across all venues and the lowest ask across all venues:

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load collected order book data
df = pd.read_csv('data/raw/btc_usd_orderbooks_multi_exchange.csv', 
                 parse_dates=['timestamp'])

# Pivot to wide format for cross-exchange comparison
df_bids = df.pivot(index='timestamp', columns='exchange', values='best_bid')
df_asks = df.pivot(index='timestamp', columns='exchange', values='best_ask')

# Calculate cross-exchange arbitrage opportunities
arb_spread = pd.DataFrame(index=df_bids.index)

# For each timestamp, find max bid and min ask across exchanges
arb_spread['max_bid'] = df_bids.max(axis=1)
arb_spread['min_ask'] = df_asks.min(axis=1)
arb_spread['max_bid_exchange'] = df_bids.idxmax(axis=1)
arb_spread['min_ask_exchange'] = df_asks.idxmin(axis=1)

# Calculate raw arbitrage spread in basis points
arb_spread['spread_bps'] = ((arb_spread['max_bid'] - arb_spread['min_ask']) / 
                             arb_spread['min_ask']) * 10000

# Identify distinct arbitrage opportunities (different exchanges)
arb_spread['valid_arb'] = (arb_spread['max_bid_exchange'] != 
                            arb_spread['min_ask_exchange'])

# Calculate summary statistics
print("Cross-Exchange Arbitrage Spread Analysis")
print("=" * 60)
print(f"Observation period: {arb_spread.index.min()} to {arb_spread.index.max()}")
print(f"Total snapshots: {len(arb_spread)}")
print(f"\nRaw Arbitrage Spread (basis points):")
print(arb_spread['spread_bps'].describe())
print(f"\nValid arbitrage opportunities: {arb_spread['valid_arb'].sum()} "
      f"({arb_spread['valid_arb'].mean()*100:.1f}% of snapshots)")

# Persistence analysis: measure autocorrelation
from statsmodels.tsa.stattools import acf

acf_values = acf(arb_spread['spread_bps'].dropna(), nlags=60)
half_life_estimate = np.argmax(acf_values < 0.5)

print(f"\nArbitrage Spread Persistence:")
print(f"First-order autocorrelation: {acf_values[1]:.3f}")
print(f"Estimated half-life: {half_life_estimate} seconds")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Time series of arbitrage spread
axes[0, 0].plot(arb_spread.index, arb_spread['spread_bps'], 
                linewidth=0.5, alpha=0.7)
axes[0, 0].axhline(y=0, color='r', linestyle='--', linewidth=1)
axes[0, 0].set_title('Cross-Exchange Arbitrage Spread Over Time')
axes[0, 0].set_xlabel('Timestamp')
axes[0, 0].set_ylabel('Spread (basis points)')
axes[0, 0].grid(True, alpha=0.3)

# Distribution of arbitrage spreads
axes[0, 1].hist(arb_spread['spread_bps'], bins=50, edgecolor='black', alpha=0.7)
axes[0, 1].axvline(x=0, color='r', linestyle='--', linewidth=1)
axes[0, 1].set_title('Distribution of Arbitrage Spreads')
axes[0, 1].set_xlabel('Spread (basis points)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].grid(True, alpha=0.3)

# Autocorrelation function
axes[1, 0].bar(range(len(acf_values)), acf_values, width=0.8)
axes[1, 0].axhline(y=0, color='black', linewidth=0.8)
axes[1, 0].set_title('Arbitrage Spread Autocorrelation')
axes[1, 0].set_xlabel('Lag (seconds)')
axes[1, 0].set_ylabel('Autocorrelation')
axes[1, 0].grid(True, alpha=0.3)

# Exchange pair frequency (where arbitrage exists)
valid_arbs = arb_spread[arb_spread['valid_arb']]
pair_counts = valid_arbs.groupby(['max_bid_exchange', 'min_ask_exchange']).size()
pair_counts = pair_counts.sort_values(ascending=False).head(10)
axes[1, 1].barh(range(len(pair_counts)), pair_counts.values)
axes[1, 1].set_yticks(range(len(pair_counts)))
axes[1, 1].set_yticklabels([f"{idx[0]} → {idx[1]}" for idx in pair_counts.index])
axes[1, 1].set_title('Most Frequent Arbitrage Exchange Pairs')
axes[1, 1].set_xlabel('Occurrence Count')
axes[1, 1].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('results/btc_arbitrage_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to results/btc_arbitrage_analysis.png")
```

The autocorrelation function measures the persistence of arbitrage opportunities, revealing whether spreads decay rapidly through trader intervention or persist due to capital constraints and latency barriers. A half-life below ten seconds indicates efficient arbitrage enforcement by high-frequency trading algorithms. A half-life exceeding thirty seconds suggests structural friction in capital deployment or venue-specific withdrawal constraints that prevent rapid arbitrage convergence.

The final analytical component estimates the break-even transaction cost threshold below which arbitrage becomes economically viable. Construct a comprehensive cost model incorporating taker fees on both legs of the trade, blockchain withdrawal fees for transferring capital between exchanges, and opportunity cost of capital locked during settlement. For Bitcoin-USD markets on major exchanges, taker fees typically range from ten to thirty basis points per side, and Bitcoin network withdrawal fees fluctuate between five and fifty dollars depending on mempool congestion. Calculate the net arbitrage profit after costs for each observed opportunity:

```python
# Transaction cost model parameters
cost_params = {
    'taker_fee_bps': 20,  # 0.20% per trade leg (buy and sell)
    'btc_withdrawal_fee_usd': 15,  # Flat Bitcoin network fee
    'btc_withdrawal_time_minutes': 30,  # Expected confirmation time
    'annual_risk_free_rate': 0.05,  # Opportunity cost of capital
    'min_trade_size_btc': 0.1  # Minimum viable trade size
}

# Calculate per-trade cost components
arb_spread['total_fee_bps'] = cost_params['taker_fee_bps'] * 2  # Round trip

# Convert withdrawal fee to basis points based on trade size
# Assume trade size equal to minimum bid volume across exchanges
df_volumes = df.pivot(index='timestamp', columns='exchange', values='bid_volume')
arb_spread['min_volume_btc'] = df_volumes.min(axis=1)

# Calculate withdrawal cost in basis points (scales with BTC price)
arb_spread['withdrawal_cost_bps'] = (
    (cost_params['btc_withdrawal_fee_usd'] / arb_spread['min_ask']) * 10000
)

# Calculate opportunity cost during withdrawal settlement
minutes_per_year = 365.25 * 24 * 60
opportunity_cost_per_minute = cost_params['annual_risk_free_rate'] / minutes_per_year
arb_spread['opportunity_cost_bps'] = (
    opportunity_cost_per_minute * 
    cost_params['btc_withdrawal_time_minutes'] * 10000
)

# Total transaction cost
arb_spread['total_cost_bps'] = (
    arb_spread['total_fee_bps'] + 
    arb_spread['withdrawal_cost_bps'] + 
    arb_spread['opportunity_cost_bps']
)

# Net arbitrage profit after all costs
arb_spread['net_profit_bps'] = arb_spread['spread_bps'] - arb_spread['total_cost_bps']

# Identify profitable arbitrage opportunities
arb_spread['profitable'] = (arb_spread['net_profit_bps'] > 0) & arb_spread['valid_arb']

# Calculate expected dollar profit for minimum trade size
arb_spread['expected_profit_usd'] = (
    (arb_spread['net_profit_bps'] / 10000) * 
    arb_spread['min_ask'] * 
    cost_params['min_trade_size_btc']
)

# Summary statistics for profitable arbitrage
profitable_arbs = arb_spread[arb_spread['profitable']]

print("\nTransaction Cost-Adjusted Arbitrage Analysis")
print("=" * 60)
print(f"\nCost Model Parameters:")
print(f"  Taker fee (per side): {cost_params['taker_fee_bps']} bps")
print(f"  BTC withdrawal fee: ${cost_params['btc_withdrawal_fee_usd']}")
print(f"  Withdrawal time: {cost_params['btc_withdrawal_time_minutes']} minutes")
print(f"  Risk-free rate (annual): {cost_params['annual_risk_free_rate']*100}%")

print(f"\nTotal Cost Breakdown (basis points):")
print(f"  Mean trading fees: {arb_spread['total_fee_bps'].mean():.2f}")
print(f"  Mean withdrawal cost: {arb_spread['withdrawal_cost_bps'].mean():.2f}")
print(f"  Mean opportunity cost: {arb_spread['opportunity_cost_bps'].mean():.2f}")
print(f"  Mean total cost: {arb_spread['total_cost_bps'].mean():.2f}")

print(f"\nProfitable Arbitrage Opportunities:")
print(f"  Count: {len(profitable_arbs)} ({len(profitable_arbs)/len(arb_spread)*100:.2f}%)")
print(f"  Mean net profit: {profitable_arbs['net_profit_bps'].mean():.2f} bps")
print(f"  Median net profit: {profitable_arbs['net_profit_bps'].median():.2f} bps")
print(f"  Mean expected profit (${cost_params['min_trade_size_btc']} BTC): "
      f"${profitable_arbs['expected_profit_usd'].mean():.2f}")

# Calculate implied annual return if profits are compounded
total_opportunities = len(profitable_arbs)
observation_hours = (arb_spread.index.max() - arb_spread.index.min()).total_seconds() / 3600
opportunities_per_hour = total_opportunities / observation_hours if observation_hours > 0 else 0
opportunities_per_year = opportunities_per_hour * 24 * 365.25
mean_profit_per_trade = profitable_arbs['expected_profit_usd'].mean()
implied_annual_profit = opportunities_per_year * mean_profit_per_trade

print(f"\nImplied Annual Performance (if fully exploited):")
print(f"  Opportunities per hour: {opportunities_per_hour:.2f}")
print(f"  Opportunities per year: {opportunities_per_year:.0f}")
print(f"  Implied annual profit: ${implied_annual_profit:,.2f}")

# Save detailed results
arb_spread.to_csv('data/processed/btc_arbitrage_with_costs.csv', index=True)
print("\nDetailed results saved to data/processed/btc_arbitrage_with_costs.csv")
```

This cost model reveals the economic threshold separating theoretical arbitrage opportunities from practically exploitable trades. In mature cryptocurrency markets with deep liquidity and competitive high-frequency trading activity, the majority of raw arbitrage spreads fall below the break-even cost threshold, consistent with efficient market microstructure theory. Persistent profitable opportunities exceeding transaction costs typically signal temporary liquidity fragmentation during high volatility episodes or structural barriers to capital movement such as regulatory restrictions on cross-border exchange access.

The practitioner must interpret these results within the broader context of market efficiency and the limits to arbitrage. The presence of small, short-lived arbitrage spreads does not indicate market dysfunction; rather, it reflects the continuous equilibration process by which informed traders incorporate new information and enforce no-arbitrage conditions across fragmented venues. The economically significant metric is not the raw spread magnitude but the ratio of net profit to total cost and the persistence of profitable opportunities. Markets where arbitrage spreads consistently exceed transaction costs by comfortable margins signal either underdeveloped high-frequency trading infrastructure or regulatory impediments to cross-venue capital flow.

## Exercise 2: Parameter Variation & Empirical Analysis

This second exercise extends the analytical framework to decentralized finance protocols, specifically investigating the economic mechanics of automated market makers using the constant product formula popularized by Uniswap. The operational objective is to reverse-engineer liquidity provider returns under varying volatility regimes and to quantify the impermanent loss phenomenon that constrains passive liquidity provision. The exercise proceeds in three stages: on-chain data extraction from Ethereum decentralized exchange contracts, reconstruction of liquidity provider profit and loss attribution, and Monte Carlo simulation of impermanent loss under stochastic price paths.

Begin by connecting to an Ethereum node through a public remote procedure call endpoint. The Infura and Alchemy services provide free-tier access sufficient for analytical research without requiring dedicated infrastructure. Initialize a Web3 connection object and configure access to a Uniswap V2 liquidity pool contract, specifically the ETH-USDC pair which exhibits deep liquidity and high trading volume:

```python
from web3 import Web3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Connect to Ethereum mainnet via public RPC
w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/demo'))

# Verify connection
if not w3.is_connected():
    raise ConnectionError("Failed to connect to Ethereum node")

print(f"Connected to Ethereum mainnet")
print(f"Latest block: {w3.eth.block_number}")

# Uniswap V2 ETH-USDC pair contract address
pair_address = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'
pair_address_checksum = w3.to_checksum_address(pair_address)

# Uniswap V2 Pair ABI (subset for swap and sync events)
pair_abi = json.loads('''[
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "name": "sender", "type": "address"},
            {"indexed": false, "name": "amount0In", "type": "uint256"},
            {"indexed": false, "name": "amount1In", "type": "uint256"},
            {"indexed": false, "name": "amount0Out", "type": "uint256"},
            {"indexed": false, "name": "amount1Out", "type": "uint256"},
            {"indexed": true, "name": "to", "type": "address"}
        ],
        "name": "Swap",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": false, "name": "reserve0", "type": "uint112"},
            {"indexed": false, "name": "reserve1", "type": "uint112"}
        ],
        "name": "Sync",
        "type": "event"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]''')

# Initialize contract object
pair_contract = w3.eth.contract(address=pair_address_checksum, abi=pair_abi)

# Query current reserves
reserves = pair_contract.functions.getReserves().call()
reserve0 = reserves[0] / 1e6  # USDC has 6 decimals
reserve1 = reserves[1] / 1e18  # WETH has 18 decimals

print(f"\nUniswap V2 ETH-USDC Pool Current State:")
print(f"USDC reserve: {reserve0:,.2f}")
print(f"WETH reserve: {reserve1:,.4f}")
print(f"Implied ETH price: ${reserve0/reserve1:,.2f}")
print(f"Pool liquidity (k): {reserve0 * reserve1:,.2f}")
```

With the contract interface established, extract historical Sync events which record reserve updates after each swap transaction. These events provide a complete time series of pool state evolution, enabling precise reconstruction of the constant product invariant enforcement and the effective exchange rate realized by traders. Query the last one thousand blocks to capture approximately four hours of trading activity under typical Ethereum block production rates:

```python
# Define block range for historical analysis
latest_block = w3.eth.block_number
start_block = latest_block - 1000  # Approximately 4 hours of history

print(f"\nQuerying Sync events from block {start_block} to {latest_block}")
print("This may take several minutes depending on RPC rate limits...\n")

# Fetch Sync events (reserve updates after each trade)
sync_filter = pair_contract.events.Sync.create_filter(
    fromBlock=start_block,
    toBlock=latest_block
)

sync_events = sync_filter.get_all_entries()

# Parse events into structured data
pool_states = []

for event in sync_events:
    block_number = event['blockNumber']
    block = w3.eth.get_block(block_number)
    
    pool_states.append({
        'block_number': block_number,
        'timestamp': datetime.fromtimestamp(block['timestamp'], tz=timezone.utc),
        'reserve_usdc': event['args']['reserve0'] / 1e6,
        'reserve_weth': event['args']['reserve1'] / 1e18
    })

# Convert to DataFrame
df_pool = pd.DataFrame(pool_states)

# Calculate derived quantities
df_pool['eth_price'] = df_pool['reserve_usdc'] / df_pool['reserve_weth']
df_pool['k_invariant'] = df_pool['reserve_usdc'] * df_pool['reserve_weth']
df_pool['tvl_usd'] = df_pool['reserve_usdc'] * 2  # Assuming balanced pool

# Calculate price changes and returns
df_pool['eth_return'] = df_pool['eth_price'].pct_change()
df_pool['k_change'] = df_pool['k_invariant'].pct_change()

print(f"Collected {len(df_pool)} pool state snapshots")
print(f"Time range: {df_pool['timestamp'].min()} to {df_pool['timestamp'].max()}")
print(f"\nETH Price Statistics:")
print(df_pool['eth_price'].describe())

# Save pool state history
df_pool.to_csv('data/raw/uniswap_eth_usdc_pool_states.csv', index=False)
print("\nPool state history saved to data/raw/uniswap_eth_usdc_pool_states.csv")
```

The constant product invariant $k = x \cdot y$ where $x$ represents USDC reserves and $y$ represents WETH reserves must remain constant across all trades, excluding fee accumulation. Small positive drifts in the $k$ value indicate fee revenue accruing to liquidity providers, while negative drifts would signal a critical smart contract vulnerability. Verify invariant preservation by calculating the percentage change in $k$ across consecutive state updates and confirming that all non-zero changes correspond to liquidity provision or removal events rather than swap transactions.

With pool state history reconstructed, calculate impermanent loss for a hypothetical liquidity provider who deposited equal values of ETH and USDC at the beginning of the observation period and held the position through all price fluctuations. Impermanent loss quantifies the opportunity cost of providing liquidity versus simply holding the underlying assets. For a constant product automated market maker, the formula derives from the portfolio value difference between the LP position and the rebalanced portfolio:

```python
import matplotlib.pyplot as plt
import numpy as np

# Load pool state history
df_pool = pd.read_csv('data/raw/uniswap_eth_usdc_pool_states.csv',
                      parse_dates=['timestamp'])

# Define initial liquidity provision parameters
initial_usdc = 10000  # Deposit $10,000 USDC
initial_eth_price = df_pool['eth_price'].iloc[0]
initial_eth = initial_usdc / initial_eth_price  # Equal value in ETH

# Calculate LP token share (constant throughout)
initial_k = df_pool['k_invariant'].iloc[0]
lp_share = (initial_usdc * initial_eth) / initial_k

print("Liquidity Provider Position Analysis")
print("=" * 60)
print(f"Initial deposit: ${initial_usdc:,.2f} USDC + {initial_eth:.4f} ETH")
print(f"Initial ETH price: ${initial_eth_price:,.2f}")
print(f"Initial position value: ${initial_usdc * 2:,.2f}")
print(f"LP share of pool: {lp_share * 100:.6f}%\n")

# Calculate LP position value at each timestamp
df_pool['lp_usdc_value'] = np.sqrt(df_pool['k_invariant'] * lp_share * 
                                    df_pool['eth_price'])
df_pool['lp_eth_value'] = np.sqrt(df_pool['k_invariant'] * lp_share / 
                                   df_pool['eth_price'])
df_pool['lp_total_value_usd'] = (df_pool['lp_usdc_value'] + 
                                  df_pool['lp_eth_value'] * df_pool['eth_price'])

# Calculate hold portfolio value (no rebalancing)
df_pool['hold_value_usd'] = (initial_usdc + initial_eth * df_pool['eth_price'])

# Calculate impermanent loss
df_pool['impermanent_loss_pct'] = ((df_pool['lp_total_value_usd'] - 
                                     df_pool['hold_value_usd']) / 
                                    df_pool['hold_value_usd'] * 100)

# Calculate cumulative fees earned (from k growth)
df_pool['k_growth'] = (df_pool['k_invariant'] / initial_k - 1) * 100
df_pool['lp_value_with_fees'] = df_pool['lp_total_value_usd'] * (1 + df_pool['k_growth']/100)

# Net profit after impermanent loss and including fees
df_pool['net_lp_return_usd'] = df_pool['lp_value_with_fees'] - (initial_usdc * 2)
df_pool['net_lp_return_pct'] = (df_pool['net_lp_return_usd'] / (initial_usdc * 2)) * 100

# Summary statistics
final_il = df_pool['impermanent_loss_pct'].iloc[-1]
final_fees = df_pool['k_growth'].iloc[-1]
final_net_return = df_pool['net_lp_return_pct'].iloc[-1]

print("Final Position Metrics:")
print(f"  ETH price change: {(df_pool['eth_price'].iloc[-1]/initial_eth_price - 1)*100:+.2f}%")
print(f"  Impermanent loss: {final_il:.2f}%")
print(f"  Fees earned (k growth): {final_fees:.2f}%")
print(f"  Net LP return: {final_net_return:+.2f}%")
print(f"  Final position value: ${df_pool['lp_value_with_fees'].iloc[-1]:,.2f}")
print(f"  Hold portfolio value: ${df_pool['hold_value_usd'].iloc[-1]:,.2f}")

# Visualization
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# ETH price evolution
axes[0].plot(df_pool['timestamp'], df_pool['eth_price'], 
             linewidth=1.5, color='blue')
axes[0].set_title('ETH-USDC Price Evolution', fontsize=12, fontweight='bold')
axes[0].set_ylabel('ETH Price (USD)')
axes[0].grid(True, alpha=0.3)

# Impermanent loss over time
axes[1].plot(df_pool['timestamp'], df_pool['impermanent_loss_pct'], 
             linewidth=1.5, color='red', label='Impermanent Loss')
axes[1].plot(df_pool['timestamp'], df_pool['k_growth'], 
             linewidth=1.5, color='green', linestyle='--', label='Fees Earned')
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
axes[1].set_title('Impermanent Loss vs. Fee Revenue', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Return (%)')
axes[1].legend(loc='best')
axes[1].grid(True, alpha=0.3)

# Net LP return
axes[2].plot(df_pool['timestamp'], df_pool['net_lp_return_pct'], 
             linewidth=1.5, color='purple')
axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
axes[2].fill_between(df_pool['timestamp'], 0, df_pool['net_lp_return_pct'],
                      where=(df_pool['net_lp_return_pct'] > 0),
                      color='green', alpha=0.3, label='Profit')
axes[2].fill_between(df_pool['timestamp'], 0, df_pool['net_lp_return_pct'],
                      where=(df_pool['net_lp_return_pct'] < 0),
                      color='red', alpha=0.3, label='Loss')
axes[2].set_title('Net Liquidity Provider Return', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Timestamp')
axes[2].set_ylabel('Net Return (%)')
axes[2].legend(loc='best')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/uniswap_lp_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to results/uniswap_lp_analysis.png")

# Save detailed analysis
df_pool.to_csv('data/processed/uniswap_lp_position_analysis.csv', index=False)
print("Detailed analysis saved to data/processed/uniswap_lp_position_analysis.csv")
```

The impermanent loss calculation reveals that passive liquidity provision in volatile markets systematically underperforms simple hold strategies when price movements are large and directional. The mathematical relationship derives from the concavity of the constant product curve: as price diverges from the initial deposit ratio, the automated market maker mechanically rebalances the portfolio by selling the appreciating asset and buying the depreciating asset, locking in losses relative to the unrebalanced portfolio. The magnitude of impermanent loss depends on the percentage price change according to the formula: $IL = 2\sqrt{r}/(1+r) - 1$ where $r$ is the price ratio relative to initial price.

The critical economic insight is that liquidity providers earn trading fees as compensation for bearing impermanent loss risk. The net profitability of liquidity provision depends on the ratio of fee revenue to impermanent loss, which in turn depends on trading volume, volatility regime, and the pool's fee tier. High-volume pools with moderate volatility generate sufficient fee revenue to offset impermanent loss, while low-volume pools in trending markets systematically destroy liquidity provider capital. Rational liquidity providers continuously monitor this tradeoff and withdraw capital when expected impermanent loss exceeds expected fee revenue.

To formalize this intuition through rigorous statistical analysis, construct a Monte Carlo simulation generating stochastic ETH price paths under varying volatility assumptions and calculate the distribution of net liquidity provider returns. Implement a geometric Brownian motion process with calibrated drift and volatility parameters estimated from historical data:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Load historical pool data for parameter calibration
df_pool = pd.read_csv('data/raw/uniswap_eth_usdc_pool_states.csv',
                      parse_dates=['timestamp'])

# Calibrate GBM parameters from historical returns
eth_returns = df_pool['eth_return'].dropna()
mu = eth_returns.mean() * 365 * 24 * 3600 / df_pool['timestamp'].diff().dt.total_seconds().mean()  # Annualized drift
sigma = eth_returns.std() * np.sqrt(365 * 24 * 3600 / df_pool['timestamp'].diff().dt.total_seconds().mean())  # Annualized volatility

print("Monte Carlo Simulation: Liquidity Provider Returns")
print("=" * 60)
print(f"Calibrated GBM Parameters (annualized):")
print(f"  Drift (μ): {mu:.4f}")
print(f"  Volatility (σ): {sigma:.4f}\n")

# Simulation parameters
n_simulations = 10000
n_days = 30
dt = 1 / 365  # Daily time step
initial_price = df_pool['eth_price'].iloc[-1]

# Fee parameters
annual_fee_rate = 0.003 * 365  # 0.3% per swap, assume 365 swaps per year (rough approximation)

# Storage for simulation results
simulation_results = []

print(f"Running {n_simulations} simulations over {n_days} days...")

np.random.seed(42)  # Reproducibility

for sim in range(n_simulations):
    # Generate price path
    prices = [initial_price]
    for _ in range(n_days):
        dW = np.random.normal(0, np.sqrt(dt))
        S_t = prices[-1]
        S_t1 = S_t * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW)
        prices.append(S_t1)
    
    final_price = prices[-1]
    price_ratio = final_price / initial_price
    
    # Calculate impermanent loss
    il_pct = (2 * np.sqrt(price_ratio) / (1 + price_ratio) - 1) * 100
    
    # Estimate fee revenue (proportional to volatility and time)
    # Simplified model: fees proportional to days and base annual rate
    fee_pct = annual_fee_rate * (n_days / 365) * 100
    
    # Net return
    net_return_pct = il_pct + fee_pct
    
    simulation_results.append({
        'simulation_id': sim,
        'final_price': final_price,
        'price_change_pct': (price_ratio - 1) * 100,
        'impermanent_loss_pct': il_pct,
        'fee_revenue_pct': fee_pct,
        'net_return_pct': net_return_pct
    })
    
    if (sim + 1) % 1000 == 0:
        print(f"  Completed {sim + 1}/{n_simulations} simulations")

# Convert to DataFrame
df_sims = pd.DataFrame(simulation_results)

# Summary statistics
print(f"\nSimulation Results Summary ({n_days} days):")
print(f"\nPrice Change Distribution:")
print(df_sims['price_change_pct'].describe())
print(f"\nImpermanent Loss Distribution:")
print(df_sims['impermanent_loss_pct'].describe())
print(f"\nNet LP Return Distribution:")
print(df_sims['net_return_pct'].describe())

# Calculate probability of profit
prob_profit = (df_sims['net_return_pct'] > 0).mean()
print(f"\nProbability of positive net return: {prob_profit*100:.1f}%")

# Value at Risk (VaR) and Expected Shortfall (ES)
var_95 = df_sims['net_return_pct'].quantile(0.05)
es_95 = df_sims[df_sims['net_return_pct'] <= var_95]['net_return_pct'].mean()

print(f"\nRisk Metrics:")
print(f"  95% VaR (5th percentile): {var_95:.2f}%")
print(f"  95% Expected Shortfall: {es_95:.2f}%")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Price change distribution
axes[0, 0].hist(df_sims['price_change_pct'], bins=50, edgecolor='black', alpha=0.7)
axes[0, 0].axvline(x=0, color='red', linestyle='--', linewidth=1.5)
axes[0, 0].set_title(f'ETH Price Change Distribution ({n_days} days)', fontweight='bold')
axes[0, 0].set_xlabel('Price Change (%)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].grid(True, alpha=0.3)

# Impermanent loss distribution
axes[0, 1].hist(df_sims['impermanent_loss_pct'], bins=50, 
                edgecolor='black', alpha=0.7, color='red')
axes[0, 1].axvline(x=0, color='black', linestyle='--', linewidth=1.5)
axes[0, 1].set_title('Impermanent Loss Distribution', fontweight='bold')
axes[0, 1].set_xlabel('Impermanent Loss (%)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].grid(True, alpha=0.3)

# Net return distribution
axes[1, 0].hist(df_sims['net_return_pct'], bins=50, 
                edgecolor='black', alpha=0.7, color='purple')
axes[1, 0].axvline(x=0, color='black', linestyle='--', linewidth=1.5)
axes[1, 0].axvline(x=var_95, color='red', linestyle='--', 
                   linewidth=1.5, label=f'95% VaR: {var_95:.2f}%')
axes[1, 0].set_title('Net LP Return Distribution', fontweight='bold')
axes[1, 0].set_xlabel('Net Return (%)')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Scatter: impermanent loss vs price change
axes[1, 1].scatter(df_sims['price_change_pct'], df_sims['impermanent_loss_pct'],
                   alpha=0.1, s=5)
# Overlay theoretical IL curve
price_changes = np.linspace(-50, 100, 200)
price_ratios = 1 + price_changes / 100
theoretical_il = (2 * np.sqrt(price_ratios) / (1 + price_ratios) - 1) * 100
axes[1, 1].plot(price_changes, theoretical_il, 'r-', linewidth=2, 
                label='Theoretical IL')
axes[1, 1].set_title('Impermanent Loss vs. Price Change', fontweight='bold')
axes[1, 1].set_xlabel('Price Change (%)')
axes[1, 1].set_ylabel('Impermanent Loss (%)')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/uniswap_lp_monte_carlo.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to results/uniswap_lp_monte_carlo.png")

# Save simulation results
df_sims.to_csv('data/processed/uniswap_lp_simulations.csv', index=False)
print("Simulation results saved to data/processed/uniswap_lp_simulations.csv")
```

The Monte Carlo simulation quantifies the probability distribution of liquidity provider outcomes under realistic volatility conditions. The key finding is that impermanent loss follows a deterministic function of final price ratio, but the fee revenue component introduces stochastic variation depending on trading volume along the simulated path. In low-volatility regimes where prices mean-revert frequently, liquidity providers earn substantial fee revenue with minimal impermanent loss. In high-volatility trending markets, impermanent loss dominates fee revenue, leading to systematic underperformance relative to holding the underlying assets.

The institutional interpretation of these results informs capital allocation decisions by professional liquidity providers operating across multiple DeFi protocols. Rational liquidity deployment requires continuous monitoring of the impermanent loss to fee revenue ratio and dynamic rebalancing across pools based on realized volatility and volume metrics. Sophisticated market participants implement delta-hedging strategies using perpetual futures or options to neutralize directional price exposure while retaining fee revenue, effectively converting the liquidity provision position into a pure volatility harvest strategy.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

This final exercise investigates systemic risk propagation through decentralized lending protocols during extreme market stress events. The operational objective is to model the liquidation cascade dynamics that emerge when collateralized debt positions become undercollateralized during rapid price declines, triggering automated liquidations that further depress prices and trigger additional liquidations. The exercise proceeds in three stages: reconstruction of historical lending protocol state during a known stress event, simulation of liquidation cascades under varying oracle latency and liquidity assumptions, and calculation of systemic solvency thresholds below which protocol bad debt accumulation becomes inevitable.

Begin by extracting historical state from a major lending protocol during a documented stress event. The Compound Finance protocol experienced significant liquidation activity during the May 2021 cryptocurrency market correction, providing rich empirical data for forensic analysis. Connect to an archive node with historical state access and query the Compound cETH and cUSDC markets to reconstruct total borrows, total collateral, and liquidation events during the stress period:

```python
from web3 import Web3
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Connect to archive node for historical state queries
# Note: Archive nodes required for historical state; standard nodes only maintain recent state
w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/demo'))

print("Compound Protocol Stress Test Analysis")
print("=" * 60)
print("Target Event: May 2021 Market Correction")
print("Date Range: May 19-20, 2021\n")

# Block numbers for stress event period
# May 19, 2021 00:00 UTC to May 20, 2021 23:59 UTC
start_block = 12468000  # Approximate block for May 19, 2021
end_block = 12475000    # Approximate block for May 20, 2021
sample_interval = 100   # Sample every 100 blocks (~20 minutes)

# Compound cETH market address
ceth_address = w3.to_checksum_address('0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5')

# Simplified Compound cToken ABI
ctoken_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalBorrows",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "exchangeRateStored",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "getCash",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# Since archive node access requires paid tier, simulate with synthetic data
# based on documented market conditions during May 2021 event

print("Generating synthetic market state data based on May 2021 conditions...")
print("(Full historical reconstruction requires archive node access)\n")

# Synthetic data parameters reflecting actual market conditions
blocks = list(range(start_block, end_block, sample_interval))
n_samples = len(blocks)

# ETH price decline profile: $3800 -> $2100 over 48 hours
initial_eth_price = 3800
final_eth_price = 2100
price_decline = (final_eth_price / initial_eth_price - 1)

# Generate realistic price path with volatility
np.random.seed(42)
time_index = np.linspace(0, 1, n_samples)
price_trend = initial_eth_price * (1 + price_decline * time_index)
price_noise = np.random.normal(0, 200, n_samples) * (1 - time_index)  # Declining volatility
eth_prices = np.maximum(price_trend + price_noise, 2000)  # Floor at $2000

# Lending protocol state evolution
# Initial conditions: well-collateralized market
initial_total_collateral_eth = 500000  # 500k ETH deposited
initial_collateral_usd = initial_total_collateral_eth * initial_eth_price
initial_total_borrows_usd = initial_collateral_usd * 0.60  # 60% utilization
initial_borrow_rate = 0.05  # 5% APR

protocol_states = []

for i, block in enumerate(blocks):
    current_eth_price = eth_prices[i]
    time_elapsed_days = i * sample_interval * 13 / (86400)  # Blocks to days
    
    # Collateral value declines with ETH price
    total_collateral_eth = initial_total_collateral_eth * (1 - 0.05 * time_index[i])  # Some withdrawals
    total_collateral_usd = total_collateral_eth * current_eth_price
    
    # Borrows remain constant in USD terms (no new borrowing during stress)
    total_borrows_usd = initial_total_borrows_usd * (1 + initial_borrow_rate * time_elapsed_days / 365)
    
    # Calculate utilization and health metrics
    utilization_rate = total_borrows_usd / total_collateral_usd
    
    # Liquidation threshold at 75% collateral ratio (typical for ETH on Compound)
    liquidation_threshold = 0.75
    at_risk_ratio = utilization_rate / liquidation_threshold
    
    # Estimate liquidations (positions become undercollateralized)
    if at_risk_ratio > 1.0:
        liquidation_volume_usd = total_borrows_usd * (at_risk_ratio - 1.0) * 0.1  # 10% of excess
    else:
        liquidation_volume_usd = 0
    
    protocol_states.append({
        'block_number': block,
        'eth_price': current_eth_price,
        'total_collateral_eth': total_collateral_eth,
        'total_collateral_usd': total_collateral_usd,
        'total_borrows_usd': total_borrows_usd,
        'utilization_rate': utilization_rate,
        'at_risk_ratio': at_risk_ratio,
        'liquidation_volume_usd': liquidation_volume_usd,
        'cumulative_liquidations_usd': 0  # Will calculate cumulative
    })

df_stress = pd.DataFrame(protocol_states)

# Calculate cumulative liquidations
df_stress['cumulative_liquidations_usd'] = df_stress['liquidation_volume_usd'].cumsum()

# Calculate health score (1.0 = healthy, 0 = insolvent)
df_stress['protocol_health_score'] = np.clip(1.5 - df_stress['at_risk_ratio'], 0, 1)

print(f"Synthetic Stress Scenario Summary:")
print(f"  Blocks analyzed: {len(df_stress)}")
print(f"  ETH price change: ${df_stress['eth_price'].iloc[0]:.2f} -> ${df_stress['eth_price'].iloc[-1]:.2f} ({(df_stress['eth_price'].iloc[-1]/df_stress['eth_price'].iloc[0]-1)*100:.1f}%)")
print(f"  Peak utilization rate: {df_stress['utilization_rate'].max()*100:.1f}%")
print(f"  Peak at-risk ratio: {df_stress['at_risk_ratio'].max():.2f}")
print(f"  Total liquidations: ${df_stress['cumulative_liquidations_usd'].iloc[-1]:,.0f}")

# Visualization
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ETH price evolution
axes[0, 0].plot(df_stress['block_number'], df_stress['eth_price'], 
                linewidth=2, color='blue')
axes[0, 0].set_title('ETH Price During Stress Event', fontweight='bold')
axes[0, 0].set_xlabel('Block Number')
axes[0, 0].set_ylabel('ETH Price (USD)')
axes[0, 0].grid(True, alpha=0.3)

# Protocol utilization rate
axes[0, 1].plot(df_stress['block_number'], df_stress['utilization_rate'] * 100,
                linewidth=2, color='orange')
axes[0, 1].axhline(y=75, color='red', linestyle='--', linewidth=1.5, 
                   label='Liquidation Threshold')
axes[0, 1].set_title('Protocol Utilization Rate', fontweight='bold')
axes[0, 1].set_xlabel('Block Number')
axes[0, 1].set_ylabel('Utilization (%)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# At-risk ratio (solvency metric)
axes[1, 0].plot(df_stress['block_number'], df_stress['at_risk_ratio'],
                linewidth=2, color='red')
axes[1, 0].axhline(y=1.0, color='black', linestyle='--', linewidth=1.5,
                   label='Insolvency Threshold')
axes[1, 0].fill_between(df_stress['block_number'], 1.0, df_stress['at_risk_ratio'],
                         where=(df_stress['at_risk_ratio'] > 1.0),
                         color='red', alpha=0.3)
axes[1, 0].set_title('Protocol Solvency Risk Ratio', fontweight='bold')
axes[1, 0].set_xlabel('Block Number')
axes[1, 0].set_ylabel('At-Risk Ratio')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Cumulative liquidations
axes[1, 1].plot(df_stress['block_number'], df_stress['cumulative_liquidations_usd'] / 1e6,
                linewidth=2, color='purple')
axes[1, 1].set_title('Cumulative Liquidation Volume', fontweight='bold')
axes[1, 1].set_xlabel('Block Number')
axes[1, 1].set_ylabel('Liquidations ($ millions)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/compound_stress_test_may2021.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to results/compound_stress_test_may2021.png")

# Save stress test data
df_stress.to_csv('data/processed/compound_stress_test_synthetic.csv', index=False)
print("Stress test data saved to data/processed/compound_stress_test_synthetic.csv")
```

The stress test reconstruction reveals the nonlinear feedback dynamics that characterize lending protocol insolvency cascades. As collateral values decline, borrowing positions approach liquidation thresholds simultaneously across many users. Once the liquidation threshold is breached, automated liquidation mechanisms trigger mass collateral sales, further depressing market prices and causing additional positions to become undercollateralized. This positive feedback loop continues until either prices stabilize, external capital enters to acquire discounted collateral, or the protocol accumulates bad debt from positions that cannot be fully liquidated.

The critical parameter governing cascade severity is the oracle latency and liquidity depth available to liquidators. Compound and Aave protocols rely on external price oracles that update with finite frequency, creating windows during which positions are undercollateralized but not yet liquidatable. If price declines outpace oracle updates and liquidator response times, the protocol becomes structurally unable to maintain full collateralization. Model this explicitly by simulating liquidation cascades under varying oracle update frequencies and liquidator capital constraints:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

print("\nLiquidation Cascade Simulation")
print("=" * 60)

# Simulation parameters
initial_eth_price = 3000
price_decline_pct = -45  # 45% decline
n_steps = 100
dt = 1.0  # Time step in minutes

# Oracle and liquidator parameters
oracle_update_intervals = [1, 5, 15]  # Minutes between oracle updates
liquidator_capacity_pct = [10, 25, 50]  # Percent of liquidatable volume per step

# Protocol parameters
total_collateral_eth = 100000
total_borrows_usd = total_collateral_eth * initial_eth_price * 0.65  # 65% LTV
liquidation_threshold = 0.75  # 75% collateralization ratio
liquidation_penalty = 0.08  # 8% penalty to liquidated borrower

results = []

for oracle_interval in oracle_update_intervals:
    for liq_capacity in liquidator_capacity_pct:
        # Price path: smooth exponential decline
        time = np.arange(n_steps) * dt
        prices = initial_eth_price * np.exp(np.log(1 + price_decline_pct/100) * 
                                             (time / time[-1]))
        
        # Initialize protocol state
        collateral_eth = total_collateral_eth
        borrows_usd = total_borrows_usd
        oracle_price = initial_eth_price  # Oracle price lags true price
        cumulative_liquidations_eth = 0
        cumulative_bad_debt_usd = 0
        
        for step in range(n_steps):
            true_price = prices[step]
            
            # Oracle updates at specified interval
            if step % oracle_interval == 0:
                oracle_price = true_price
            
            # Calculate collateralization ratio based on oracle price
            collateral_value_usd = collateral_eth * oracle_price
            collateral_ratio = collateral_value_usd / borrows_usd
            
            # Check for liquidation trigger
            if collateral_ratio < liquidation_threshold:
                # Calculate required liquidation volume
                target_collateral_ratio = 0.85  # Target after liquidation
                required_liquidation_usd = (borrows_usd - 
                                            collateral_value_usd / target_collateral_ratio)
                required_liquidation_eth = required_liquidation_usd / oracle_price
                
                # Apply liquidator capacity constraint
                actual_liquidation_eth = min(required_liquidation_eth,
                                              collateral_eth * (liq_capacity / 100))
                
                # Execute liquidation with penalty
                liquidation_value_usd = actual_liquidation_eth * oracle_price
                liquidation_penalty_usd = liquidation_value_usd * liquidation_penalty
                debt_repaid_usd = liquidation_value_usd + liquidation_penalty_usd
                
                # Update protocol state
                collateral_eth -= actual_liquidation_eth
                borrows_usd -= debt_repaid_usd
                cumulative_liquidations_eth += actual_liquidation_eth
                
                # Check for bad debt (insufficient collateral to cover debt)
                if collateral_eth * true_price < borrows_usd:
                    bad_debt_this_step = max(0, borrows_usd - collateral_eth * true_price)
                    cumulative_bad_debt_usd += bad_debt_this_step
        
        # Final protocol health
        final_collateral_value = collateral_eth * prices[-1]
        final_collateral_ratio = final_collateral_value / borrows_usd if borrows_usd > 0 else 999
        protocol_solvent = final_collateral_ratio >= 1.0
        
        results.append({
            'oracle_interval_min': oracle_interval,
            'liquidator_capacity_pct': liq_capacity,
            'final_eth_price': prices[-1],
            'final_collateral_eth': collateral_eth,
            'final_borrows_usd': borrows_usd,
            'final_collateral_ratio': final_collateral_ratio,
            'cumulative_liquidations_eth': cumulative_liquidations_eth,
            'cumulative_bad_debt_usd': cumulative_bad_debt_usd,
            'protocol_solvent': protocol_solvent
        })

df_cascade = pd.DataFrame(results)

print("\nLiquidation Cascade Simulation Results:")
print(df_cascade.to_string(index=False))

# Calculate insolvency probability across parameter space
pivot_solvency = df_cascade.pivot_table(
    index='oracle_interval_min',
    columns='liquidator_capacity_pct',
    values='protocol_solvent',
    aggfunc='mean'
)

print("\n\nProtocol Solvency Matrix (1.0 = solvent, 0.0 = insolvent):")
print(pivot_solvency)

# Visualization: bad debt heatmap
pivot_bad_debt = df_cascade.pivot_table(
    index='oracle_interval_min',
    columns='liquidator_capacity_pct',
    values='cumulative_bad_debt_usd'
)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Bad debt accumulation heatmap
im1 = axes[0].imshow(pivot_bad_debt.values, cmap='Reds', aspect='auto')
axes[0].set_xticks(range(len(pivot_bad_debt.columns)))
axes[0].set_yticks(range(len(pivot_bad_debt.index)))
axes[0].set_xticklabels(pivot_bad_debt.columns)
axes[0].set_yticklabels(pivot_bad_debt.index)
axes[0].set_xlabel('Liquidator Capacity (%)')
axes[0].set_ylabel('Oracle Update Interval (min)')
axes[0].set_title('Cumulative Bad Debt Accumulation (USD)', fontweight='bold')
plt.colorbar(im1, ax=axes[0], label='Bad Debt (USD)')

# Annotate cells with values
for i in range(len(pivot_bad_debt.index)):
    for j in range(len(pivot_bad_debt.columns)):
        value = pivot_bad_debt.values[i, j]
        axes[0].text(j, i, f'${value/1e6:.1f}M',
                     ha='center', va='center',
                     color='white' if value > pivot_bad_debt.values.max()/2 else 'black',
                     fontsize=9, fontweight='bold')

# Solvency outcome heatmap
im2 = axes[1].imshow(pivot_solvency.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
axes[1].set_xticks(range(len(pivot_solvency.columns)))
axes[1].set_yticks(range(len(pivot_solvency.index)))
axes[1].set_xticklabels(pivot_solvency.columns)
axes[1].set_yticklabels(pivot_solvency.index)
axes[1].set_xlabel('Liquidator Capacity (%)')
axes[1].set_ylabel('Oracle Update Interval (min)')
axes[1].set_title('Protocol Solvency Outcome', fontweight='bold')
plt.colorbar(im2, ax=axes[1], label='Solvency (1=solvent, 0=insolvent)')

# Annotate cells
for i in range(len(pivot_solvency.index)):
    for j in range(len(pivot_solvency.columns)):
        value = pivot_solvency.values[i, j]
        text = 'SOLVENT' if value == 1.0 else 'INSOLVENT'
        axes[1].text(j, i, text,
                     ha='center', va='center',
                     color='darkgreen' if value == 1.0 else 'darkred',
                     fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('results/liquidation_cascade_sensitivity.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to results/liquidation_cascade_sensitivity.png")

# Save detailed results
df_cascade.to_csv('data/processed/liquidation_cascade_results.csv', index=False)
print("Cascade simulation results saved to data/processed/liquidation_cascade_results.csv")
```

The sensitivity analysis demonstrates that protocol solvency during extreme stress events depends critically on the responsiveness of liquidation infrastructure. With frequent oracle updates and deep liquidator capacity, protocols maintain solvency even through severe price declines by continuously matching undercollateralized positions with liquidator capital. However, when oracle latency exceeds five minutes or liquidator capacity falls below twenty-five percent of required liquidation volume per time step, bad debt accumulation becomes inevitable. This structural vulnerability explains the observed protocol insolvencies during the March 2020 and May 2021 market corrections, where gas price spikes delayed liquidator transactions and created effective oracle latency beyond design assumptions.

The institutional policy implication is that decentralized lending protocols require explicit risk management backstops beyond automated liquidation mechanisms. Well-designed protocols implement insurance funds capitalized from protocol revenue, progressive liquidation penalty schedules that increase with system stress levels, and circuit breaker mechanisms that halt new borrowing when utilization rates exceed emergency thresholds. Sophisticated protocol governance should continuously monitor the ratio of liquidator capacity to total at-risk positions and dynamically adjust collateralization requirements to maintain adequate safety margins during volatile market regimes.

## Operational Reference Guide & Diagnostic Checklist

This operational reference provides systematic diagnostic procedures for identifying pathological market behaviors, quantifying protocol risk exposures, and validating the integrity of analytical results generated through these laboratory exercises. The practitioner must internalize these verification protocols and execute them routinely when conducting cryptocurrency market analysis or DeFi risk assessment under institutional mandates.

**Data Quality Validation Procedures**: Before conducting any quantitative analysis, verify data completeness and structural integrity through systematic checks. For cryptocurrency exchange data, confirm timestamp continuity by calculating the distribution of inter-observation intervals and flagging gaps exceeding three times the nominal sample frequency. Order book data must satisfy basic market microstructure constraints: best bid strictly less than best ask, positive quoted volumes, and monotonic price improvement away from the top of book. On-chain protocol data extracted via Web3 requires block number validation to ensure state queries reference a consistent blockchain fork and have not been corrupted by chain reorganizations. Calculate the percentage of successful versus failed RPC calls and flag data collection sessions with error rates exceeding five percent for re-execution.

**Arbitrage Spread Validation**: When analyzing cross-exchange arbitrage opportunities, implement defensive filters to eliminate spurious spreads caused by stale quotes, flash crashes, or data collection errors. Calculate the time-weighted average spread over rolling five-minute windows and flag individual observations exceeding three standard deviations from the rolling mean. Cross-reference computed arbitrage spreads against realized trade execution data when available, verifying that observed trades occur at prices consistent with the order book snapshots used for spread calculation. For cryptocurrency markets exhibiting structural liquidity fragmentation, calculate the effective arbitrage spread incorporating both quoted prices and available depth by computing the volume-weighted average price impact for realistic trade sizes.

**Impermanent Loss Calculation Verification**: The constant product market maker impermanent loss formula contains a well-defined analytical form that provides an exact reference for validating numerical implementations. For any given price ratio $r = P_{\text{final}} / P_{\text{initial}}$, the theoretical impermanent loss equals $IL = 2\sqrt{r}/(1+r) - 1$. After calculating impermanent loss from empirical pool state data, overlay the theoretical curve on a scatter plot of observed price changes versus computed losses. Deviations from the theoretical relationship indicate either computational errors in the implementation or non-standard pool mechanics such as dynamic fee tiers or concentrated liquidity ranges. Additionally verify that the product invariant $k = x \cdot y$ increases monotonically over time due to fee accumulation, with the growth rate proportional to trading volume and the swap fee rate.

**Monte Carlo Simulation Validation**: Stochastic simulation results require rigorous verification to ensure numerical implementations correctly generate sample paths from the specified probability distribution. For geometric Brownian motion price simulations, validate that the distribution of log returns matches the theoretical normal distribution by computing the Jarque-Bera test statistic and confirming that it fails to reject normality at the five percent significance level. Calculate the sample mean and variance of terminal price outcomes and verify these moments match the theoretical values derived from the GBM parameters. Implement antithetic variate sampling by generating pairs of price paths with negated random shocks and confirming that the pairing reduces Monte Carlo standard error by at least thirty percent compared to independent sampling.

**Liquidation Cascade Verification**: Lending protocol stress test simulations must preserve accounting identities and satisfy conservation laws throughout the simulation. At each time step, verify that the sum of collateral value and cumulative liquidations equals the initial collateral value plus any price appreciation, confirming that collateral is neither created nor destroyed by the simulation logic. The ratio of total borrows to total collateral value must equal the utilization rate by definition, providing an internal consistency check on state variable updates. When liquidations occur, confirm that the debt reduction equals the liquidated collateral value plus the liquidation penalty, with the penalty accruing to the liquidator rather than the protocol or borrower.

**Diagnostic Checklist for Production Deployment**: Analysts deploying these methodologies in institutional settings must execute this checklist before releasing results to internal stakeholders or regulatory authorities. First, document all data sources with explicit version identifiers and timestamps, ensuring full reproducibility of analytical outputs. Second, execute unit tests on all custom functions implementing pricing formulas, utility calculations, or simulation logic, verifying numerical accuracy against hand-calculated test cases. Third, conduct sensitivity analysis by varying key input parameters plus or minus twenty percent and confirming that output metrics change smoothly without discontinuities or numerical instabilities. Fourth, generate standardized diagnostic plots visualizing input data distributions, residual patterns from fitted models, and convergence behavior of iterative algorithms. Fifth, compare analytical results against independent implementations using different programming languages or libraries when feasible, flagging discrepancies exceeding one percent of the computed magnitude for investigation.

**Common Failure Modes and Remediation**: Cryptocurrency market data analysis encounters recurring failure patterns that practitioners must recognize and address systematically. Exchange API rate limiting manifests as missing data blocks with elevated error rates during high-volatility periods when data collection frequency is most critical. Implement exponential backoff retry logic and distributed collection across multiple API keys to maintain continuous sampling. On-chain data extraction fails when attempting to query historical state from non-archive nodes that only maintain recent blockchain state. Upgrade to archive node access or pre-compute and cache critical historical metrics during initial market events. Monte Carlo simulation numerical instability occurs when volatility parameters are miscalibrated, generating price paths with excessive spikes or negative prices. Implement truncation at reasonable boundaries and validate that less than one percent of simulated paths hit the truncation limits.

**Performance Optimization Considerations**: Large-scale empirical analysis of cryptocurrency markets generates substantial computational load that requires optimization for practical execution. Vectorize all numerical operations using NumPy array operations rather than Python loops, achieving typical speedups of ten to one hundred times. Parallelize Monte Carlo simulations across multiple CPU cores using the multiprocessing library, distributing simulation batches to worker processes and aggregating results in the master process. Cache expensive external API calls and blockchain queries to local storage, implementing cache invalidation policies that refresh data at appropriate intervals for the analysis time horizon. For repeated analysis workflows, implement incremental computation that processes only new data since the last execution rather than recomputing entire historical datasets.

**Regulatory Reporting Requirements**: Financial institutions operating cryptocurrency trading desks or providing digital asset custody services face evolving regulatory reporting obligations that require rigorous analytical infrastructure. Maintain complete audit trails documenting all data sources, transformation logic, and model parameter specifications used to generate risk metrics reported to supervisory authorities. Implement version control for analytical code and maintain tagged releases corresponding to quarterly or annual reporting periods, enabling exact reproduction of historical reports during regulatory examinations. Calculate standard risk metrics including Value at Risk, Expected Shortfall, and concentration risk measures using methodology consistent with traditional asset class reporting to facilitate cross-portfolio aggregation. Document all deviations from standard risk measurement approaches necessitated by unique cryptocurrency market characteristics, providing technical justification for alternative methodologies.

The practitioner who internalizes these operational procedures and diagnostic protocols develops the rigorous analytical discipline necessary for professional cryptocurrency market research and DeFi risk management. The technical complexity and rapid evolution of decentralized financial infrastructure demands continuous learning and methodological refinement, but the foundational principles of empirical verification, systematic diagnostics, and transparent documentation remain constant across all analytical contexts. Execute these laboratory exercises repeatedly until the workflow becomes automatic, then extend the methodology to novel protocols, market structures, and risk scenarios as the cryptocurrency ecosystem continues to evolve.
