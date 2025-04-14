import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from tabulate import tabulate
from termcolor import colored
import requests
from bs4 import BeautifulSoup

# ====== PARAMETERS ======
initial_capital = 100000
start_date = '2021-12-01'
end_date = '2024-12-01'
rebalance_freq = 'M'  # Monthly rebalancing
momentum_lookback = 63  # 3 months (trading days)
top_n_stocks = 5  # Number of top momentum stocks to consider

# ====== ASSET UNIVERSE ======
def get_universe():
    """Get diverse asset universe including stocks, ETFs, and safe havens"""
    try:
        # S&P 500 stocks - only take first 50 for efficiency and reliability
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        # Filter out problematic tickers (those with periods)
        stocks = [ticker.replace('.', '-') for ticker in sp500['Symbol'].tolist() if '.' not in ticker][:50]
    except:
        # Fallback if web scraping fails
        print("Warning: Could not get S&P 500 list, using fallback list")
        stocks = [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'PG',
            'UNH', 'HD', 'MA', 'DIS', 'BAC', 'ADBE', 'CRM', 'NFLX', 'CMCSA', 'PFE',
            'KO', 'PEP', 'TMO', 'ABT', 'MRK', 'CSCO', 'VZ', 'INTC', 'WMT', 'JNJ'
        ]
    
    # Sector ETFs
    sectors = [
        'XLY', 'XLP', 'XLE', 'XLF', 'XLV',  # Consumer Discretionary, Staples, Energy, Financials, Healthcare
        'XLI', 'XLB', 'XLRE', 'XLK', 'XLU',  # Industrials, Materials, Real Estate, Tech, Utilities
        'SPY', 'QQQ', 'IWM'  # Major indexes
    ]
    
    # Safe havens
    safe_assets = {
        'TLT': '20+ Year Treasuries',
        'IEF': '7-10 Year Treasuries',
        'SHY': '1-3 Year Treasuries',
        'GLD': 'Gold',
        'BIL': '1-3 Month Treasuries'
    }
    
    return stocks + sectors + list(safe_assets.keys()), safe_assets

# ====== DATA DOWNLOAD ======
def download_prices(tickers):
    """Robust price download with error handling"""
    data = {}
    failed = []
    
    # First try to download all at once for efficiency
    try:
        all_data = yf.download(
            tickers,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True
        )
        
        # If single ticker was passed, structure is different
        if isinstance(all_data.columns, pd.MultiIndex):
            for ticker in all_data['Close'].columns:
                series = all_data['Close'][ticker].copy()
                if not series.empty and not series.isnull().all():
                    data[ticker] = series
                else:
                    failed.append(ticker)
        else:
            if not all_data.empty:
                data[tickers] = all_data['Close']
            else:
                failed.append(tickers)
    except Exception as e:
        print(f"Bulk download failed: {str(e)}")
        # Fall back to individual downloads
        for ticker in tickers:
            try:
                df = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=True
                )
                if not df.empty and not df['Close'].isnull().all():
                    data[ticker] = df['Close']
                else:
                    failed.append(ticker)
            except Exception as e:
                print(f"{ticker} download failed: {str(e)}")
                failed.append(ticker)
    
    if failed:
        print(f"Failed to download: {failed[:10]}..." if len(failed) > 10 else f"Failed to download: {failed}")
    
    # Make sure we have some data
    if not data:
        raise ValueError("No price data could be downloaded. Check internet connection or tickers.")
    
    # Create DataFrame and forward fill missing values
    prices_df = pd.DataFrame(data)
    return prices_df.ffill()

# ====== MACRO CONDITION ENGINE ======
class MacroEngine:
    def __init__(self):
        # In real implementation, you'd fetch actual macro data
        # For now, we simulate realistic data
        self.gdp_data = self._simulate_gdp()
        self.rate_data = self._simulate_rates()
        
    def _simulate_gdp(self):
        """Simulate quarterly GDP growth with realistic values"""
        dates = pd.date_range(start=start_date, end=end_date, freq='Q')
        # Start with 5.0 (post-covid recovery) and trend downward
        base = 5.0
        trend = -0.4
        noise = np.random.normal(0, 0.5, len(dates))
        values = [max(-2.0, min(7.0, base + trend * i + noise[i])) for i in range(len(dates))]
        return pd.Series(values, index=dates)
    
    def _simulate_rates(self):
        """Simulate interest rate changes, starting low and rising"""
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        # Start at 0.25% in 2022, rise to around 5% by end of 2023, then stabilize
        base_trend = np.array([
            0.25, 0.25, 0.50, 0.75, 1.0, 1.50, 2.00, 2.50, 3.00, 3.50,
            3.75, 4.00, 4.25, 4.50, 4.75, 5.00, 5.25, 5.25, 5.00, 5.00,
            4.75, 4.75, 4.50, 4.25, 4.00, 3.75, 3.75, 3.50, 3.25
        ])
        
        # Pad to match length of dates
        if len(base_trend) < len(dates):
            padding = np.repeat(base_trend[-1], len(dates) - len(base_trend))
            base_trend = np.append(base_trend, padding)
        
        return pd.Series(base_trend[:len(dates)], index=dates)
    
    def get_conditions(self, date):
        """Get GDP growth and rate stability for a given date"""
        # Find the closest date in our GDP data (quarterly)
        closest_gdp_date = self.gdp_data.index[self.gdp_data.index <= date][-1]
        gdp_growth = self.gdp_data.loc[closest_gdp_date]
        
        # Find the closest date in our rate data (monthly)
        closest_rate_date = self.rate_data.index[self.rate_data.index <= date][-1]
        
        # Check if rates are stable or falling
        rate_dates = self.rate_data.index[self.rate_data.index <= closest_rate_date]
        if len(rate_dates) >= 2:
            prev_rate_date = rate_dates[-2]
            rate_change = self.rate_data.loc[closest_rate_date] - self.rate_data.loc[prev_rate_date]
        else:
            rate_change = 0  # Assume stable at the beginning
        
        # Define conditions
        gdp_ok = gdp_growth > 0
        rates_ok = rate_change <= 0.25  # Stable or falling
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'gdp_growth': gdp_growth,
            'rate': self.rate_data.loc[closest_rate_date],
            'rate_change': rate_change,
            'gdp_ok': gdp_ok,
            'rates_ok': rates_ok,
            'regime': 'Risk-On' if gdp_ok and rates_ok else 'Moderate' if gdp_ok else 'Risk-Off'
        }

# ====== STRATEGY ENGINE ======
def run_strategy():
    print("Initializing strategy...")
    tickers, safe_assets = get_universe()
    print(f"Downloading price data for {len(tickers)} assets...")
    prices = download_prices(tickers)
    print(f"Successfully downloaded data for {prices.shape[1]} assets")
    
    macro = MacroEngine()
    
    # Initialize portfolio tracking dataframe
    portfolio = pd.DataFrame(index=prices.index)
    portfolio['Position'] = None
    portfolio['Position_Name'] = None
    portfolio['Capital'] = initial_capital
    portfolio['Shares'] = 0
    portfolio['Entry_Date'] = None  # Track entry date for each position
    
    investment_log = []
    macro_log = []
    
    current_pos = None
    entry_date = None
    entry_price = None
    shares_held = 0
    
    # Start with default position in short-term treasuries
    default_pos = 'SHY'
    
    # Find first valid date where we have data for our default position
    if default_pos in prices.columns:
        first_valid_idx = prices[prices[default_pos].notnull()].index[0]
        current_pos = default_pos
        entry_date = first_valid_idx
        entry_price = prices[current_pos].loc[entry_date]
        shares_held = initial_capital / entry_price
        
        # Set initial position
        portfolio.loc[entry_date:, 'Position'] = current_pos
        portfolio.loc[entry_date:, 'Position_Name'] = safe_assets.get(current_pos, current_pos)
        portfolio.loc[entry_date:, 'Shares'] = shares_held
        portfolio.loc[entry_date:, 'Entry_Date'] = entry_date
    
    # Rebalance dates (make sure they're within our data range)
    rebalance_dates = pd.date_range(start=prices.index[0], end=prices.index[-1], freq=rebalance_freq)
    rebalance_dates = [date for date in rebalance_dates if date in prices.index]
    
    print(f"Running strategy with {len(rebalance_dates)} rebalance dates...")
    
    # Rebalance on schedule
    for date in rebalance_dates:
        # Skip dates too close to the beginning
        lookback_start_idx = prices.index.get_loc(date) - momentum_lookback
        if lookback_start_idx < 0:
            continue
            
        # Get macro conditions
        macro_status = macro.get_conditions(date)
        macro_log.append(macro_status)
        
        # Decide on allocation based on regime
        if macro_status['gdp_ok'] and macro_status['rates_ok']:
            # Risk-on: Select top momentum stocks
            lookback_start = prices.index[lookback_start_idx]
            
            # Calculate returns for lookback period
            period_returns = prices.loc[lookback_start:date].pct_change(periods=momentum_lookback).iloc[-1]
            
            # Filter out NaN and get top performers
            valid_returns = period_returns.dropna()
            if len(valid_returns) > 0:
                top_stocks = valid_returns.nlargest(min(top_n_stocks, len(valid_returns)))
                
                # Pick the top performer
                if len(top_stocks) > 0:
                    new_pos = top_stocks.index[0]
                    new_pos_name = f"Top Momentum: {new_pos}"
                else:
                    new_pos, new_pos_name = default_pos, safe_assets.get(default_pos, default_pos)
            else:
                new_pos, new_pos_name = default_pos, safe_assets.get(default_pos, default_pos)
                
        elif macro_status['gdp_ok']:
            # Moderate risk: Best safe asset
            safe_keys = [k for k in safe_assets.keys() if k in prices.columns]
            if safe_keys and len(prices) >= 21:
                safe_perf = prices[safe_keys].loc[:date].iloc[-21:].pct_change(periods=20).iloc[-1]
                valid_safe_perf = safe_perf.dropna()
                if len(valid_safe_perf) > 0:
                    new_pos = valid_safe_perf.idxmax()
                    new_pos_name = safe_assets.get(new_pos, new_pos)
                else:
                    new_pos, new_pos_name = default_pos, safe_assets.get(default_pos, default_pos)
            else:
                new_pos, new_pos_name = default_pos, safe_assets.get(default_pos, default_pos)
        else:
            # Risk-off: Cash equivalents
            new_pos, new_pos_name = default_pos, safe_assets.get(default_pos, default_pos)
        
        # Ensure the new position exists in our price data
        if new_pos not in prices.columns:
            print(f"Warning: Selected position {new_pos} not found in price data. Using default.")
            new_pos, new_pos_name = default_pos, safe_assets.get(default_pos, default_pos)
            
        # Check if we need to rebalance
        if new_pos != current_pos:
            # Record the trade for the previous position
            if current_pos is not None and entry_date is not None and current_pos in prices.columns:
                # Get the exit price
                exit_price = prices[current_pos].loc[date]
                days_held = (date - entry_date).days
                
                # Calculate the return
                if entry_price > 0:
                    pct_change = (exit_price/entry_price - 1) * 100
                else:
                    pct_change = 0
                
                # Update portfolio value based on shares held
                current_value = shares_held * exit_price
                
                investment_log.append({
                    'entry_date': entry_date.strftime('%Y-%m-%d'),
                    'exit_date': date.strftime('%Y-%m-%d'),
                    'days_held': days_held,
                    'asset': portfolio.at[entry_date, 'Position_Name'],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return_pct': pct_change,
                    'regime': macro_status['regime']
                })
                
                # Use the current value to buy the new position
                entry_price = prices[new_pos].loc[date]
                shares_held = current_value / entry_price
            else:
                # Initialize with our starting capital
                entry_price = prices[new_pos].loc[date]
                shares_held = initial_capital / entry_price
            
            # Update tracking variables
            current_pos = new_pos
            entry_date = date
            
            # Update portfolio tracking
            portfolio.loc[date:, 'Position'] = new_pos
            portfolio.loc[date:, 'Position_Name'] = new_pos_name
            portfolio.loc[date:, 'Shares'] = shares_held
            portfolio.loc[date:, 'Entry_Date'] = entry_date
    
    # Calculate daily portfolio value
    for idx, row in portfolio.iterrows():
        if row['Position'] is not None and row['Position'] in prices.columns:
            # Get the day's price for the current position
            day_price = prices[row['Position']].loc[idx]
            # Calculate the day's portfolio value
            portfolio.at[idx, 'Capital'] = row['Shares'] * day_price
    
    # Fill forward any missing values
    portfolio = portfolio.ffill()
    
    # Save the last entry date for reporting
    last_entry_date = portfolio['Entry_Date'].iloc[-1]
    
    return portfolio, investment_log, macro_log, prices, last_entry_date

# ====== EXECUTION & VISUALIZATION ======
if __name__ == "__main__":
    try:
        print("\n" + "="*80)
        print(colored(" UNIVERSAL MACRO-AWARE MOMENTUM STRATEGY ", 'white', 'on_blue', attrs=['bold']))
        print("="*80 + "\n")
        
        portfolio, investments, macro_log, prices, last_entry_date = run_strategy()
        
        # Performance Analysis
        initial_date = portfolio.index[0]
        final_date = portfolio.index[-1]
        initial_value = portfolio['Capital'].iloc[0]
        final_value = portfolio['Capital'].iloc[-1]
        total_return = (final_value/initial_value - 1)*100

        # Calculate SPY return if available
        spy_return = np.nan
        if 'SPY' in prices.columns:
            spy_start = prices['SPY'].loc[initial_date] 
            spy_end = prices['SPY'].loc[final_date]
            if not np.isnan(spy_start) and not np.isnan(spy_end):
                spy_return = (spy_end/spy_start - 1)*100
                
        # Format investment log for printing
        invest_table = []
        for trade in investments:
            invest_table.append([
                trade['entry_date'],
                trade['exit_date'],
                trade['days_held'],
                trade['asset'],
                f"${trade['entry_price']:.2f}",
                f"${trade['exit_price']:.2f}",
                colored(f"{trade['return_pct']:+.2f}%", 'green' if trade['return_pct'] >= 0 else 'red'),
                colored(trade['regime'], 'green' if trade['regime'] == 'Risk-On' else 'yellow' if trade['regime'] == 'Moderate' else 'red')
            ])
        
        # Print Results
        print("\n" + colored("INVESTMENT HISTORY:", 'blue', attrs=['bold']))
        print(tabulate(invest_table, 
            headers=['Entry Date', 'Exit Date', 'Days', 'Asset', 'Entry Price', 'Exit Price', 'Return', 'Market Regime'],
            tablefmt='pretty',
            numalign="right"
        ))
        
        # Macro Summary
        print("\n" + colored("MACRO ENVIRONMENT SUMMARY:", 'blue', attrs=['bold']))
        macro_summary = []
        for log in macro_log:
            macro_summary.append([
                log['date'],
                f"{log['gdp_growth']:.2f}%",
                f"{log['rate']:.2f}%",
                f"{log['rate_change']:+.2f}" if 'rate_change' in log else "N/A",
                colored("✓", 'green') if log['gdp_ok'] else colored("✗", 'red'),
                colored("✓", 'green') if log['rates_ok'] else colored("✗", 'red'),
                colored(log['regime'], 'green' if log['regime'] == 'Risk-On' else 'yellow' if log['regime'] == 'Moderate' else 'red')
            ])
        
        print(tabulate(macro_summary[:], 
            headers=['Date', 'GDP Growth', 'Interest Rate', 'Rate Change', 'GDP OK?', 'Rates OK?', 'Regime'],
            tablefmt='pretty',
            numalign="right"
        ))
        
        # Performance metrics
        print("\n" + colored("PERFORMANCE METRICS:", 'blue', attrs=['bold']))
        print(f"{'Time Period:':<25} {initial_date.strftime('%Y-%m-%d')} to {final_date.strftime('%Y-%m-%d')}")
        print(f"{'Initial Investment:':<25} ${initial_value:,.2f}")
        print(f"{'Final Portfolio Value:':<25} {colored(f'${final_value:,.2f}', 'green' if final_value >= initial_value else 'red')}")
        print(f"{'Total Return:':<25} {colored(f'{total_return:+.2f}%', 'green' if total_return >= 0 else 'red')}")
        print(f"{'SPY Buy & Hold:':<25} {colored(f'{spy_return:+.2f}%' if not np.isnan(spy_return) else 'N/A', 'green' if spy_return >= 0 else 'red')}")
        
        # Current position
        print(f"\n{'Current Position:':<25} {colored(portfolio['Position_Name'].iloc[-1], 'cyan')}")
        print(f"{'Shares Held:':<25} {portfolio['Shares'].iloc[-1]:.2f}")
        print(f"{'Entry Date:':<25} {last_entry_date.strftime('%Y-%m-%d')}")
        print(f"{'Days in Position:':<25} {(final_date - last_entry_date).days}")
        
        # Plot
        plt.figure(figsize=(14, 7))
        plt.plot(portfolio.index, portfolio['Capital'], label='Strategy', linewidth=2)
        if 'SPY' in prices.columns:
            plt.plot(prices.index, prices['SPY']/prices['SPY'].iloc[0]*initial_capital, 
                    '--', label='SPY Buy & Hold', alpha=0.7)
        plt.title('Universal Macro-Aware Momentum Strategy', pad=20, size=14)
        plt.xlabel('Date', size=12)
        plt.ylabel('Portfolio Value ($)', size=12)
        plt.legend()
        plt.grid(True)
        plt.show()
        
    except Exception as e:
        import traceback
        print(colored(f"\nError: {str(e)}", 'red'))
        print(traceback.format_exc())
        print("\nTroubleshooting Tips:")
        print("- Check internet connection")
        print("- Try a smaller asset universe")
        print("- Verify date range is valid")
        print("- Some tickers may be delisted")