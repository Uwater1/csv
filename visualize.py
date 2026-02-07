import pandas as pd
import mplfinance as mpf
from tools.data_loader import DataLoader
import os

def plot_trade(trade, loader, save_path):
    ticker = trade['Ticker']
    bottom_date = pd.to_datetime(trade['BottomDate'], utc=True)
    entry_date = pd.to_datetime(trade['EntryDate'], utc=True)
    exit_date = pd.to_datetime(trade['ExitDate'], utc=True)

    df = loader.load_data(ticker)

    # Define plot window
    start_date = bottom_date - pd.Timedelta(days=20)
    end_date = exit_date + pd.Timedelta(days=10)

    mask = (df.index >= start_date) & (df.index <= end_date)
    plot_df = df[mask].copy()

    if plot_df.empty:
        print(f"No data for {ticker} around trade dates.")
        return

    # Add buy and sell markers
    # Create marker series with NaNs
    buy_signals = [float('nan')] * len(plot_df)
    sell_signals = [float('nan')] * len(plot_df)
    bottom_signals = [float('nan')] * len(plot_df)

    # We need to find the exact index location
    try:
        if bottom_date in plot_df.index:
            bottom_signals[plot_df.index.get_loc(bottom_date)] = plot_df.loc[bottom_date, 'Low'] * 0.98

        if entry_date in plot_df.index:
            buy_signals[plot_df.index.get_loc(entry_date)] = plot_df.loc[entry_date, 'Low'] * 0.99

        if exit_date in plot_df.index:
            sell_signals[plot_df.index.get_loc(exit_date)] = plot_df.loc[exit_date, 'High'] * 1.01
    except Exception as e:
        print(f"Error finding indices for plotting: {e}")

    # Create additional plots
    apds = [
        mpf.make_addplot(buy_signals, type='scatter', markersize=100, marker='^', color='g'),
        mpf.make_addplot(sell_signals, type='scatter', markersize=100, marker='v', color='r'),
        mpf.make_addplot(bottom_signals, type='scatter', markersize=50, marker='o', color='orange')
    ]

    title = f"{ticker} Trade | Return: {trade['Return']:.2%}"

    mpf.plot(plot_df, type='candle', style='yahoo',
             title=title,
             addplot=apds,
             volume=True,
             savefig=save_path,
             figscale=1.2)

    print(f"Saved plot to {save_path}")

def main():
    if not os.path.exists('backtest_results_4.csv'):
        print("Results file not found. Run research_bottoms_v4.py first.")
        return

    df_results = pd.read_csv('backtest_results_4.csv')
    df_results.sort_values('Return', ascending=False, inplace=True)

    top_wins = df_results.head(3)
    worst_losses = df_results.tail(3)

    loader = DataLoader()

    print("Generating plots for Top 3 Wins...")
    for i, (idx, trade) in enumerate(top_wins.iterrows()):
        plot_trade(trade, loader, f"win_{i+1}_{trade['Ticker']}.png")

    print("Generating plots for Worst 3 Losses...")
    for i, (idx, trade) in enumerate(worst_losses.iterrows()):
        plot_trade(trade, loader, f"loss_{i+1}_{trade['Ticker']}.png")

if __name__ == "__main__":
    main()
