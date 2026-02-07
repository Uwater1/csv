import pandas as pd
import numpy as np
from tools.data_loader import DataLoader

def calculate_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))

    # Wilder's Smoothing
    avg_gain = gain.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def identify_bottoms(df, window=63):
    rolling_min = df['Low'].rolling(window=window).min()
    is_bottom = (df['Low'] == rolling_min)
    return is_bottom

def backtest_strategy_v3(ticker, df):
    # Calculate RSI
    df['RSI'] = calculate_rsi(df)

    is_bottom = identify_bottoms(df)

    trades = []
    i = 0
    start_idx = 20

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
        rsi_at_bottom = df['RSI'].iloc[bottom_idx]

        # Hypothesis 3: RSI < 30 at bottom
        if rsi_at_bottom >= 30: # If not oversold, skip
            i += 1
            continue

        pattern_found = False
        entry_idx = -1

        for j in range(1, 6):
            if (bottom_idx + j) >= len(df):
                break

            curr_idx = bottom_idx + j

            if df['Low'].iloc[curr_idx] < bottom_price_low:
                break

            curr_close = df['Close'].iloc[curr_idx]

            # Reversal Pattern: Close > Bottom High
            if curr_close > bottom_price_high:
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
    print(f"Analyzing {len(tickers)} tickers with RSI Filter...")

    for ticker in tickers:
        try:
            df = loader.load_data(ticker)
            if len(df) < 100:
                continue
            trades = backtest_strategy_v3(ticker, df)
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

    results_df.to_csv('backtest_results_3.csv', index=False)

    with open('backtest_results_3.txt', 'w') as f:
        f.write(f"Total Trades: {len(results_df)}\n")
        f.write(f"Average Return: {avg_return:.2%}\n")
        f.write(f"Win Rate: {win_rate:.2%}\n")

if __name__ == "__main__":
    main()
