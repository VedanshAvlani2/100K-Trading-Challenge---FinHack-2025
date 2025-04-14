import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from termcolor import colored
from tabulate import tabulate
data = yf.download(['SPY', 'QQQ', 'TLT', 'GLD', 'VNQ'], start='2021-12-1', end='2024-12-1')

def evaluate_strategy(portfolio_values, name="Strategy"):
    returns = portfolio_values.pct_change().dropna()
    total_return = portfolio_values.iloc[-1] / portfolio_values.iloc[0] - 1
    annual_return = (1 + total_return) ** (1/3) - 1
    volatility = returns.std() * np.sqrt(12)
    sharpe = returns.mean() / returns.std() * np.sqrt(12)
    drawdown = (portfolio_values / portfolio_values.cummax() - 1).min()
    print(f"\n{name} Performance:")
    print(f"Total Return: {total_return:.2%}")
    print(f"Annualized Return: {annual_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {drawdown:.2%}")
    return {
        "Strategy": name,
        "Total Return": total_return,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": drawdown,
        "Annual Return": annual_return,
        "Volatility": volatility
    }

tickers = ['SPY', 'QQQ', 'TLT', 'GLD', 'VNQ']
start_date = '2020-01-01'
end_date = '2023-12-31'
initial_capital = 100000
lookback_months = 3
top_k = 2
min_return_threshold = 0.07  # 7%

data = yf.download(tickers, start=start_date, end=end_date)
monthly_prices = data.resample('M').last()
monthly_returns = monthly_prices.pct_change().dropna()

# Shift prices to avoid look-ahead bias
momentum_returns = monthly_prices.pct_change(periods=lookback_months).shift(1)
momentum_volatility = monthly_returns.rolling(lookback_months).std().shift(1)
momentum_score = (momentum_returns / momentum_volatility)

# -----------------------------
#Backtest Strategy
# -----------------------------
portfolio_value = []
dates = []
current_value = initial_capital

for i in range(lookback_months + 1, len(monthly_returns)):
    date = monthly_returns.index[i]
    
    # 1. Apply macro filter (placeholder logic)
    # You can skip trading if VIX or interest rates are high
    macro_ok = True  # ← replace with logic if you fetch macro data

    if macro_ok:
        # 2. Get scores for that month
        scores = momentum_score.iloc[i]
        raw_returns = momentum_returns.iloc[i]
        
        # 3. Filter ETFs with > 7% past return
        qualified = raw_returns[raw_returns > min_return_threshold].index
        scores_filtered = scores[qualified]
        
        # 4. Select top-k by momentum score
        top_etfs = scores_filtered.nlargest(top_k).index.tolist()
        
        if len(top_etfs) > 0:
            month_ret = monthly_returns.iloc[i][top_etfs].mean()
        else:
            month_ret = 0  # stay in cash
    else:
        month_ret = 0  # stay in cash

    current_value *= (1 + month_ret)
    portfolio_value.append(current_value)
    dates.append(date)

# Create Series
enhanced_momentum = pd.Series(portfolio_value, index=dates)

evaluate_strategy(enhanced_momentum, name="📈 Enhanced 3-Month Momentum Strategy")

# -----------------------------
#Plot Portfolio Value
# -----------------------------
plt.figure(figsize=(12, 6))
enhanced_momentum.plot(label='Enhanced Momentum Strategy', color='purple')
plt.axhline(initial_capital, linestyle='--', color='gray', label='Initial Capital')
plt.title("📈 Enhanced 3-Month Volatility-Adjusted Momentum Strategy")
plt.xlabel("Date")
plt.ylabel("Portfolio Value ($)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()