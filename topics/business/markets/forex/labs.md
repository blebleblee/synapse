# Operational Verification Labs: Forex

## Objective & Operational Lab Setup

These labs are designed for the practitioner who needs to move beyond reading about currency markets and into the mechanics of pricing, risk quantification, and position management. The three exercises that follow are structured as a progressive curriculum: you will build a live cross-rate pricing model from first principles, stress-test it against empirical volatility regimes, and then construct a carry trade portfolio with a full drawdown recovery protocol. Every formula is complete, every spreadsheet column is specified, and every diagnostic check has a pass/fail threshold.

The working assumption is that you have access to a standard analytical environment: Microsoft Excel or Google Sheets with the ability to write array formulas, a Python 3.10+ environment with `pandas`, `numpy`, `scipy`, and `yfinance` installed, and a free account on either OANDA or Interactive Brokers paper trading for real-time quote verification. All market data referenced in these exercises can be sourced from the Federal Reserve's FRED database (`https://fred.stlouisfed.org`) for interest rate differentials, from the Bank for International Settlements for historical spot data, and from Yahoo Finance via the `yfinance` library for intraday tick approximation.

Before beginning, establish your directory structure and install the Python dependencies. From a terminal, run:

```
pip install pandas numpy scipy yfinance matplotlib openpyxl statsmodels
```

Create a working directory called `forex_labs/` with three subdirectories: `data/`, `models/`, and `outputs/`. Every lab artifact should be saved there by name as specified in each exercise. This ensures your verification diagnostics in the final section map cleanly to your produced outputs.

The theoretical backbone threading through all three exercises is the Covered Interest Rate Parity (CIP) condition and its empirical violations, the mechanics of the bid-ask spread as a function of liquidity and volatility, and the statistical properties of currency carry returns under different volatility regimes. Where theory is introduced, it is introduced to explain a mechanical anomaly you will observe in your own data, not to substitute for it.

---

## Exercise 1: Foundational Practical Implementation

### Building a Live Cross-Rate Pricing Engine and Spread Decomposition Model

The first task every practitioner must master is the arithmetic of cross-rate construction, because the most common source of pricing error in
