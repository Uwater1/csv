import pandas as pd
import numpy as np
from tools.data_loader import DataLoader
import matplotlib.pyplot as plt

def identify_bottoms(df, window=63):
    """
    Identifies days where the Low is the minimum of the *previous* 'window' days.
    """
    # rolling min of previous days (shift 1 to not include current day in calculation,
    # but we want to check if current is lower than previous window)
    # Actually, usually "3 month low" means lowest in last 3 months INCLUDING today.
    # So if Low[t] <= min(Low[t-63:t]), it's a 3 month low.

    rolling_min = df['Low'].rolling(window=window).min()
    # Mask where current low equals the rolling min
    is_bottom = (df['Low'] == rolling_min)
    return is_bottom

def backtest_strategy(ticker, df):
    is_bottom = identify_bottoms(df)
    bottom_dates = df.index[is_bottom]

    trades = []

    # We need to skip bottoms that are too close to each other or process them sequentially.
    # For simplicity, let's treat every signal independently, but be careful of overlap.
    # However, "Stop falling" implies a reversal.

    # Let's iterate through bottom dates
    # To avoid many consecutive bottom signals (stock keeps falling), we might only take the *first* one in a sequence?
    # Or we look for the pattern *after* the low.

    # Refined logic:
    # 1. Identify a 3-month low.
    # 2. Look ahead up to 5 days.
    # 3. If Close > High of the bottom day, TRIGGER.
    # 4. Buy next day Open.

    # To handle consecutive lows: if today is a low, and tomorrow is lower, tomorrow is the new bottom.
    # We are looking for the *reversal*.

    i = 0
    while i < len(df) - 25: # Ensure room for pattern + trade
        # check if today is a 3-month low
        if not is_bottom.iloc[i]:
            i += 1
            continue

        # Found a low at index i
        bottom_idx = i
        bottom_price_high = df['High'].iloc[bottom_idx]
        bottom_price_low = df['Low'].iloc[bottom_idx]

        # Search for pattern in next 5 days
        pattern_found = False
        entry_idx = -1

        for j in range(1, 6):
            if (bottom_idx + j) >= len(df):
                break

            # Check if price keeps falling (new 3-month low)
            # If we make a NEW 3-month low, reset the bottom reference?
            # User said "locate the bottom ... then study pattern around this".
            # If it keeps falling, it hasn't stopped falling.
            # So if Low[bottom_idx + j] < bottom_price_low, update bottom?
            # Let's keep it simple: strict definition of pattern relative to the identified low.
            # But if a lower low occurs, the previous low wasn't the "bottom".

            curr_idx = bottom_idx + j
            curr_low = df['Low'].iloc[curr_idx]

            if curr_low < bottom_price_low:
                # New low established, discard previous "bottom" candidate
                # Loop will naturally find this new low later if we advance i carefully?
                # Actually, simply aborting this search is safest.
                # We update i to this new low index to start searching from there?
                # No, just break and let the main loop handle it.
                break

            curr_close = df['Close'].iloc[curr_idx]

            # Hypothesis 1: Close > High of the bottom day
            if curr_close > bottom_price_high:
                pattern_found = True
                entry_idx = curr_idx + 1 # Buy next day open
                break

        if pattern_found and entry_idx < len(df):
            # Trade execution
            entry_price = df['Open'].iloc[entry_idx]
            entry_date = df.index[entry_idx]

            # Exit after 20 days
            exit_idx = entry_idx + 20
            if exit_idx < len(df):
                exit_price = df['Close'].iloc[exit_idx]
                exit_date = df.index[exit_idx]

                ret = (exit_price - entry_price) / entry_price
                trades.append({
                    'Ticker': ticker,
                    'BottomDate': df.index[bottom_idx],
                    'EntryDate': entry_date,
                    'EntryPrice': entry_price,
                    'ExitDate': exit_date,
                    'ExitPrice': exit_price,
                    'Return': ret
                })

                # Skip past this trade to avoid overlapping trades for the same bottom sequence
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

    print(f"Analyzing {len(tickers)} tickers...")

    for ticker in tickers:
        try:
            df = loader.load_data(ticker)
            if len(df) < 100:
                continue
            trades = backtest_strategy(ticker, df)
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

    # Save to CSV for inspection
    results_df.to_csv('backtest_results_1.csv', index=False)

    # Also create a text summary
    with open('backtest_results_1.txt', 'w') as f:
        f.write(f"Total Trades: {len(results_df)}\n")
        f.write(f"Average Return: {avg_return:.2%}\n")
        f.write(f"Win Rate: {win_rate:.2%}\n")

if __name__ == "__main__":
    main()
