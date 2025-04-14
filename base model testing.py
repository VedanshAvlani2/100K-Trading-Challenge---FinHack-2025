import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from termcolor import colored
from tabulate import tabulate

# ====== PARAMETERS ======
initial_capital = 100000  # $100,000
start_date = '2021-12-01'
end_date = '2024-12-01'
ticker = 'SPY'  # S&P 500 ETF

# ====== DATA DOWNLOAD ======
print("Downloading historical data...")
data = yf.download(ticker, start=start_date, end=end_date, progress=False)

# ====== PERFORMANCE CALCULATION ======
# Calculate returns and portfolio value
data['Daily_Return'] = data['Close'].pct_change()
data['Portfolio_Value'] = initial_capital * (1 + data['Daily_Return']).cumprod()

# Total returns
total_return_pct = (data['Portfolio_Value'][-1] / initial_capital - 1) * 100
annualized_return_pct = ((1 + total_return_pct / 100) ** (1/3) - 1) * 100

# Max drawdown
cum_returns = (1 + data['Daily_Return']).cumprod()
peak = cum_returns.cummax()
drawdown = (cum_returns - peak) / peak
max_drawdown_pct = drawdown.min() * 100

# ====== RESULTS ======
print("\n" + "="*80)
print(colored(" PASSIVE BUY-AND-HOLD STRATEGY ", 'white', 'on_blue', attrs=['bold']))
print("="*80)

# Performance table
performance_table = [
    [colored("Initial Investment", 'cyan'), f"${initial_capital:,.0f}"],
    [colored("Final Value", 'cyan'), f"${data['Portfolio_Value'][-1]:,.2f}"],
    [colored("Total Return", 'cyan'), colored(f"{total_return_pct:.2f}%", 'green' if total_return_pct >=0 else 'red')],
    [colored("Annualized Return", 'cyan'), colored(f"{annualized_return_pct:.2f}%", 'green' if annualized_return_pct >=0 else 'red')],
    [colored("Max Drawdown", 'cyan'), colored(f"{max_drawdown_pct:.2f}%", 'red')]
]

print("\n" + colored("PERFORMANCE SUMMARY:", 'blue', attrs=['bold']))
print(tabulate(performance_table, tablefmt="pretty"))

# ====== PLOT ======
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['Portfolio_Value'], label='Portfolio Value', color='blue')
plt.title(f'Passive S&P 500 Investment: ${initial_capital:,} to ${data["Portfolio_Value"][-1]:,.0f}')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.legend()
plt.show()