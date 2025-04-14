import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from termcolor import colored
from tabulate import tabulate

# ====== PARAMETERS ======
initial_capital = 100000
start_date = '2021-12-01'
end_date = '2024-12-01'
tickers = ['SPY', 'QQQ', 'TLT', 'GLD', 'VNQ']
lookback = 3  # Months for volatility calculation

# ====== DATA DOWNLOAD ======
print("Downloading asset prices...")
data = yf.download(tickers, start=start_date, end=end_date)['Close']
monthly_prices = data.resample('M').last()
monthly_returns = monthly_prices.pct_change().dropna()

# ====== STRATEGY IMPLEMENTATION ======
portfolio_value = pd.Series(index=monthly_returns.index, dtype='float64')
portfolio_value.iloc[0] = initial_capital
weights_df = pd.DataFrame(index=monthly_returns.index, columns=tickers)

for i in range(1, len(monthly_returns)):
    if i < lookback:
        weights = np.array([1/len(tickers)]*len(tickers))
    else:
        past_returns = monthly_returns.iloc[i-lookback:i]
        vol = past_returns.std()
        weights = (1/vol) / (1/vol).sum()
    
    weights_df.iloc[i] = weights
    portfolio_value.iloc[i] = portfolio_value.iloc[i-1] * (1 + np.nansum(weights * monthly_returns.iloc[i]))

portfolio_value = portfolio_value.ffill()

# ====== PERFORMANCE METRICS ======
returns = portfolio_value.pct_change().dropna()
total_return = portfolio_value.iloc[-1] / initial_capital - 1
annualized_return = (1 + total_return) ** (1/3) - 1
volatility = returns.std() * np.sqrt(12)
sharpe = returns.mean() / returns.std() * np.sqrt(12)
drawdown = (portfolio_value / portfolio_value.cummax() - 1).min()

# ====== RESULTS ======
print("\n" + "="*80)
print(colored(" RISK-PARITY VOLATILITY WEIGHTED STRATEGY ", 'white', 'on_blue', attrs=['bold']))
print("="*80)

# Performance table
performance_table = [
    [colored("Final Value", 'cyan'), f"${portfolio_value.iloc[-1]:,.0f}"],
    [colored("Total Return", 'cyan'), colored(f"{total_return:.2%}", 'green' if total_return >=0 else 'red')],
    [colored("Annualized Return", 'cyan'), colored(f"{annualized_return:.2%}", 'green' if annualized_return >=0 else 'red')],
    [colored("Volatility", 'cyan'), f"{volatility:.2%}"],
    [colored("Sharpe Ratio", 'cyan'), f"{sharpe:.2f}"],
    [colored("Max Drawdown", 'cyan'), colored(f"{drawdown:.2%}", 'red')]
]

print("\n" + colored("PERFORMANCE SUMMARY:", 'blue', attrs=['bold']))
print(tabulate(performance_table, tablefmt="pretty"))

# ====== PLOT ======
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
ax1.plot(portfolio_value, label='Risk-Parity', color='#6a0dad', linewidth=2)
ax1.set_title('Risk-Parity Portfolio Performance', pad=20)
ax1.grid(True)
ax1.legend()

weights_df.plot.area(ax=ax2, stacked=True, alpha=0.7)
ax2.set_title('Asset Allocation Weights')
ax2.legend(bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.show()