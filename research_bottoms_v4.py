import pandas as pd
import numpy as np
from tools.data_loader import DataLoader
from typing import List, Dict

def identify_bottoms(df: pd.DataFrame, window: int = 63) -> pd.Series:
    """
    Identifies days where the Low is the minimum of the rolling window.
    """
    rolling_min = df['Low'].rolling(window=window).min()
    is_bottom = (df['Low'] == rolling_min)
    return is_bottom

def identify_hammers(df: pd.DataFrame) -> pd.Series:
    """
    Identifies Hammer candlestick patterns in a vectorized manner.
    """
    body = (df['Close'] - df['Open']).abs()
    upper_shadow = df['High'] - df[['Close', 'Open']].max(axis=1)
    lower_shadow = df[['Close', 'Open']].min(axis=1) - df['Low']
    rng = df['High'] - df['Low']

    # Avoid division by zero if needed, though mostly comparison
    # Conditions:
    # 1. Lower shadow >= 1.5 * Body
    # 2. Upper shadow <= 0.1 * Range

    cond1 = lower_shadow >= 1.5 * body
    cond2 = upper_shadow <= 0.1 * rng

    # Ensure range is non-zero to be a valid candle for this pattern
    valid_range = rng > 0

    return cond1 & cond2 & valid_range

def backtest_strategy_optimized(ticker: str, df: pd.DataFrame) -> List[Dict]:
    """
    Vectorized backtest of the Hammer-at-Bottom strategy.
    """
    if len(df) < 63:
        return []

    # 1. Identify Signals
    is_bottom = identify_bottoms(df)
    is_hammer_candle = identify_hammers(df)

    # Signal = Is Bottom AND Is Hammer
    signals = is_bottom & is_hammer_candle

    # Get indices of signals
    signal_indices = np.where(signals)[0]

    trades = []

    # We still iterate through signals to handle trade management (holding period),
    # but we skip non-signals efficiently.

    last_exit_idx = -1

    for entry_idx in signal_indices:
        # We assume we detect pattern at Close of day `entry_idx`.
        # We buy at Open of day `entry_idx + 1`.

        trade_entry_idx = entry_idx + 1

        if trade_entry_idx >= len(df):
            continue

        # Avoid overlapping trades? The prompt didn't specify strict non-overlap,
        # but typical backtests might manage cash. Here we just log all valid signals
        # or skip if we are already in a trade?
        # Let's stick to the previous logic: if we are in a trade, we ignore new signals until exit.

        if trade_entry_idx <= last_exit_idx:
            continue

        trade_exit_idx = trade_entry_idx + 20

        if trade_exit_idx >= len(df):
            continue

        entry_price = df['Open'].iloc[trade_entry_idx]
        exit_price = df['Close'].iloc[trade_exit_idx]

        ret = (exit_price - entry_price) / entry_price

        trades.append({
            'Ticker': ticker,
            'BottomDate': df.index[entry_idx],
            'EntryDate': df.index[trade_entry_idx],
            'ExitDate': df.index[trade_exit_idx],
            'Return': ret
        })

        last_exit_idx = trade_exit_idx

    return trades

def main():
    loader = DataLoader()
    tickers = loader.get_all_tickers()

    all_trades = []
    print(f"Analyzing {len(tickers)} tickers with Vectorized Hammer Pattern...")

    for ticker in tickers:
        try:
            df = loader.load_data(ticker)
            trades = backtest_strategy_optimized(ticker, df)
            all_trades.extend(trades)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    if not all_trades:
        print("No trades generated.")
        return

    results_df = pd.DataFrame(all_trades)

    avg_return = results_df['Return'].mean()
    win_rate = (results_df['Return'] > 0).mean()

    print(f"Total Trades: {len(results_df)}")
    print(f"Average Return: {avg_return:.2%}")
    print(f"Win Rate: {win_rate:.2%}")

    results_df.to_csv('backtest_results_4.csv', index=False)

if __name__ == "__main__":
    main()
