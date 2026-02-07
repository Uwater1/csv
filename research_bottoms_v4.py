import pandas as pd
import numpy as np
from tools.data_loader import DataLoader

def identify_bottoms(df, window=63):
    rolling_min = df['Low'].rolling(window=window).min()
    is_bottom = (df['Low'] == rolling_min)
    return is_bottom

def is_hammer(row):
    body = abs(row['Close'] - row['Open'])
    upper_shadow = row['High'] - max(row['Close'], row['Open'])
    lower_shadow = min(row['Close'], row['Open']) - row['Low']
    rng = row['High'] - row['Low']

    if rng == 0:
        return False

    cond1 = lower_shadow >= 1.5 * body
    cond2_alt = upper_shadow <= 0.1 * rng

    return cond1 and cond2_alt

def backtest_strategy_v4(ticker, df):
    is_bottom = identify_bottoms(df)

    trades = []
    i = 0

    while i < len(df) - 25:
        if not is_bottom.iloc[i]:
            i += 1
            continue

        bottom_idx = i

        if is_hammer(df.iloc[bottom_idx]):
            entry_idx = bottom_idx + 1
            if entry_idx < len(df):
                entry_price = df['Open'].iloc[entry_idx]
                exit_idx = entry_idx + 20
                if exit_idx < len(df):
                    exit_price = df['Close'].iloc[exit_idx]
                    ret = (exit_price - entry_price) / entry_price
                    trades.append({
                        'Ticker': ticker,
                        'BottomDate': df.index[bottom_idx],
                        'EntryDate': df.index[entry_idx],
                        'ExitDate': df.index[exit_idx],
                        'Return': ret
                    })
                    i = exit_idx
                    continue

        i += 1

    return trades

def main():
    loader = DataLoader()
    tickers = loader.get_all_tickers()

    all_trades = []
    print(f"Analyzing {len(tickers)} tickers with Hammer Pattern...")

    for ticker in tickers:
        try:
            df = loader.load_data(ticker)
            if len(df) < 100:
                continue
            trades = backtest_strategy_v4(ticker, df)
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
