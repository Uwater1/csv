import pandas as pd
import numpy as np
from tools.data_loader import DataLoader

def identify_bottoms(df, window=63):
    rolling_min = df['Low'].rolling(window=window).min()
    is_bottom = (df['Low'] == rolling_min)
    return is_bottom

def backtest_strategy_v2(ticker, df):
    # Calculate Volume SMA
    df['VolSMA20'] = df['Volume'].rolling(window=20).mean()

    is_bottom = identify_bottoms(df)

    trades = []
    i = 0
    # Ensure we have enough data for SMA calculation
    start_idx = max(20, 0)

    while i < len(df) - 25:
        if i < start_idx:
            i += 1
            continue

        if not is_bottom.iloc[i]:
            i += 1
            continue

        bottom_idx = i
        bottom_price_high = df['High'].iloc[bottom_idx]
        bottom_price_low = df['Low'].iloc[bottom_idx]

        pattern_found = False
        entry_idx = -1

        for j in range(1, 6):
            if (bottom_idx + j) >= len(df):
                break

            curr_idx = bottom_idx + j

            # Check if new low invalidates
            if df['Low'].iloc[curr_idx] < bottom_price_low:
                break

            curr_close = df['Close'].iloc[curr_idx]
            curr_vol = df['Volume'].iloc[curr_idx]
            curr_vol_sma = df['VolSMA20'].iloc[curr_idx]

            # Hypothesis 2: Close > High AND Volume > 1.2 * AvgVol
            # Also handle case where SMA might be NaN or 0? (Should be handled by start_idx, but 0 volume exists)
            # Safe division not strictly needed if we multiply

            if curr_close > bottom_price_high and curr_vol > (1.2 * curr_vol_sma):
                pattern_found = True
                entry_idx = curr_idx + 1
                break

        if pattern_found and entry_idx < len(df):
            entry_price = df['Open'].iloc[entry_idx]

            exit_idx = entry_idx + 20
            if exit_idx < len(df):
                exit_price = df['Close'].iloc[exit_idx]

                ret = (exit_price - entry_price) / entry_price
                trades.append({
                    'Ticker': ticker,
                    'Return': ret
                })
                i = exit_idx
            else:
                i += 1
        else:
            i += 1

    return trades

def main():
    loader = DataLoader()
    tickers = loader.get_all_tickers()

    all_trades = []
    print(f"Analyzing {len(tickers)} tickers with Volume Filter...")

    for ticker in tickers:
        try:
            df = loader.load_data(ticker)
            if len(df) < 100:
                continue
            trades = backtest_strategy_v2(ticker, df)
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

    results_df.to_csv('backtest_results_2.csv', index=False)

    with open('backtest_results_2.txt', 'w') as f:
        f.write(f"Total Trades: {len(results_df)}\n")
        f.write(f"Average Return: {avg_return:.2%}\n")
        f.write(f"Win Rate: {win_rate:.2%}\n")

if __name__ == "__main__":
    main()
