import pandas as pd
import matplotlib.pyplot as plt
from tools.data_loader import DataLoader
import os

def plot_trade(trade, loader, save_path):
    ticker = trade['Ticker']
    bottom_date = pd.to_datetime(trade['BottomDate'], utc=True)
    entry_date = pd.to_datetime(trade['EntryDate'], utc=True)
    exit_date = pd.to_datetime(trade['ExitDate'], utc=True)

    df = loader.load_data(ticker)

    # Define plot window
    start_date = bottom_date - pd.Timedelta(days=30)
    end_date = exit_date + pd.Timedelta(days=10)

    mask = (df.index >= start_date) & (df.index <= end_date)
    plot_df = df[mask]

    if plot_df.empty:
        print(f"No data for {ticker} around trade dates.")
        return

    plt.figure(figsize=(12, 6))

    # Plot Candles (Simple Line for now, or bars)
    # Let's do simple line of Close, and Markers for Bottom/Entry/Exit
    plt.plot(plot_df.index, plot_df['Close'], label='Close Price', color='black', linewidth=1)

    # Highlight Bottom (Hammer)
    if bottom_date in plot_df.index:
        plt.scatter(bottom_date, plot_df.loc[bottom_date, 'Low'], color='orange', label='Hammer Bottom', s=100, marker='^')

    # Highlight Entry
    if entry_date in plot_df.index:
        plt.scatter(entry_date, plot_df.loc[entry_date, 'Open'], color='green', label='Buy', s=100, marker='o')

    # Highlight Exit
    if exit_date in plot_df.index:
        color = 'blue' if trade['Return'] > 0 else 'red'
        plt.scatter(exit_date, plot_df.loc[exit_date, 'Close'], color=color, label='Sell', s=100, marker='x')

    plt.title(f"Trade: {ticker} | Return: {trade['Return']:.2%}")
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path)
    plt.close()
    print(f"Saved plot to {save_path}")

def main():
    if not os.path.exists('backtest_results_4.csv'):
        print("Results file not found.")
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
