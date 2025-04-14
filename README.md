# 100K-Trading-Challenge-FinHack-2025

Smarter ETF Strategies for Beginner Investors

## Overview
This project was developed for the **FinHack 2025 Hackathon** with a clear mission: transform a **$100,000 investment** into optimal returns using simple, yet smart **ETF-based investment strategies**. The focus was on making data-driven investing accessible to **beginner investors**, while balancing risk, simplicity, and practical performance.

## Objective
To simulate and compare four investment strategies using real-world ETF data, backtest them, and evaluate performance across different market conditions. The ultimate goal was to identify a winning strategy that maximizes returns while managing volatility and drawdowns.

## Tools & Technologies
- **Python** (Main language for analysis and modeling)
- **pandas, numpy** (Data manipulation and analysis)
- **yfinance** (ETF price data collection)
- **backtrader** (Backtesting engine)
- **matplotlib** (Visualization)
- **termcolor, tabulate** (Formatted output)
- **Monte Carlo Simulation (numpy-based)** for forward-looking risk analysis

## ETF Descriptions
For clarity, here is what each ETF represents:
- **SPY** – S&P 500 Index ETF (broad U.S. market)
- **QQQ** – Nasdaq-100 Index ETF (tech-heavy growth stocks)
- **GLD** – Gold ETF (commodity hedge)
- **TLT** – Long-Term Treasury Bonds ETF (interest rate sensitivity)
- **VNQ** – Real Estate Investment Trust ETF (real estate sector exposure)

## Strategy Breakdown

### 1. Buy & Hold (SPY)
- Invests the full $100K in **SPY (S&P 500 ETF)** and holds it through the entire backtest period.
- **Total Return**: +37.67%
- A reliable benchmark, but doesn't adapt to market shifts.

### 2. Momentum Rotation
- Monthly rotation into the best performer from: **SPY, QQQ, GLD, TLT, VNQ**.
- Ranking is based on **past 3-month performance**.
- **Total Return**: +112.02%
- **Volatility**: 92.68%
- High returns, but higher risk and drawdowns.

### 3. Risk-Parity (Volatility Weighted)
- Allocates more to ETFs with **lower historical volatility**.
- Monthly rebalancing based on **inverse-volatility weighting**.
- **Total Return**: +20.37%
- Prioritizes capital preservation over aggressive growth.

### 4. Macro-Aware Momentum *(Final Winner)*
- Applies momentum rotation only when **GDP is growing** and **interest rates are stable**.
- Else, shifts to defensive assets like **TLT or cash**.
- Uses basic macroeconomic condition checks from **Fed rates and GDP trends**.
- **Total Return**: +64.86%
- Best balance of return and risk, ideal for new investors.

## Testing Methodology
- **Backtest period**: Dec 2021 to Dec 2024
- **Initial Capital**: $100,000
- Each model was tested using historical ETF data from Yahoo Finance
- Performance metrics computed:
  - Total return
  - Annualized return
  - Volatility (std. deviation of daily returns)
  - Sharpe ratio (**annualized**, using 0% risk-free rate for simplicity)
  - Maximum drawdown (peak-to-trough loss)
- Portfolio values and risk metrics plotted and analyzed

## Monte Carlo Simulations
To further validate robustness, **1-year Monte Carlo simulations** were run for the first three models. These simulations stress-tested performance across **1,000 potential market paths** using:
- **Bootstrapped return sampling** from historical returns
- **Random walk simulations** based on daily return statistics

## Final Verdict
The **Macro-Aware Momentum Strategy** emerged as the top performer:
- Strong performance under good market conditions
- Smart macro filters to reduce downside risk
- Beginner-friendly, yet powerful

- Code included data acquisition, return computation, drawdown analysis, and plotting

## How to Run
1. **Clone this repo** or download the source files.
2. **Install required Python packages**:
```bash
pip install yfinance pandas matplotlib termcolor tabulate
```
3. **Run the scripts**:
   - Open a terminal in the folder containing the files.
   - Execute a strategy script using:
```bash
python "macro aware momentum.py"
python "momentum rotation model.py"
python "risk parity volatility weighted.py"
python "base model testing.py"  # for Buy & Hold
```
4. **Outputs**:
   - Strategy performance and metrics are printed in the terminal.
   - A portfolio value plot is shown visually using matplotlib.

## Future Work
- Add a **streamlit dashboard** for interactive strategy comparison
- Include **real-time macroeconomic API integration**
- Enable **custom ETF basket selection** for user personalization
- Expand simulation framework to include **Value-at-Risk (VaR)** and **Conditional VaR**
