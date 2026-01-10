"""
Script to download historical stock data from yfinance.
Reads symbols from 20260105.csv and nq100_unique_symbols.txt.
Downloads data with period="10y" and interval="1d".
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import time
import os


def read_symbols_from_csv(csv_path: str) -> set:
    """Read symbols from CSV file with 'Symbol' column."""
    symbols = set()
    df = pd.read_csv(csv_path)
    if 'Symbol' in df.columns:
        symbols.update(df['Symbol'].dropna().astype(str).str.strip().tolist())
    return symbols


def read_symbols_from_txt(txt_path: str) -> set:
    """Read symbols from plain text file (one per line)."""
    symbols = set()
    with open(txt_path, 'r') as f:
        for line in f:
            symbol = line.strip()
            if symbol:
                symbols.add(symbol)
    return symbols


def download_stock_data(symbols: set, period: str = "10y", interval: str = "1d") -> dict:
    """
    Download historical stock data for given symbols.
    
    Args:
        symbols: Set of stock tickers
        period: Time period (e.g., "10y")
        interval: Data interval (e.g., "1d")
    
    Returns:
        Dictionary mapping symbol to DataFrame
    """
    results = {}
    failed = []
    
    print(f"Downloading data for {len(symbols)} symbols...")
    
    for i, symbol in enumerate(sorted(symbols), 1):
        try:
            print(f"[{i}/{len(symbols)}] Downloading {symbol}...", end=" ")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                df['Symbol'] = symbol
                results[symbol] = df
                print(f"OK ({len(df)} rows)")
            else:
                failed.append(symbol)
                print("No data")
        except Exception as e:
            failed.append(symbol)
            print(f"Error: {e}")
        
        # Rate limiting to avoid API issues
        time.sleep(0.2)
    
    if failed:
        print(f"\nFailed to download: {failed}")
    
    return results


def save_to_csv(data: dict, output_dir: str = "price"):
    """Save downloaded data to CSV files."""
    Path(output_dir).mkdir(exist_ok=True)
    
    for symbol, df in data.items():
        filepath = os.path.join(output_dir, f"{symbol}.csv")
        df.to_csv(filepath)
        print(f"Saved: {filepath}")


def main():
    # File paths
    csv_file = "code-temp/20260105.csv"
    txt_file = "code-temp/nq100_unique_symbols.txt"
    output_dir = "price"
    
    # Read symbols from both files
    print("Reading symbols from files...")
    csv_symbols = read_symbols_from_csv(csv_file)
    txt_symbols = read_symbols_from_txt(txt_file)
    
    # Combine unique symbols
    all_symbols = csv_symbols.union(txt_symbols)
    print(f"Found {len(csv_symbols)} symbols from CSV")
    print(f"Found {len(txt_symbols)} symbols from TXT")
    print(f"Total unique symbols: {len(all_symbols)}")
    
    # Download data
    data = download_stock_data(all_symbols, period="10y", interval="1d")
    
    print(f"\nSaving data to {output_dir}...")
    save_to_csv(data, output_dir)
    
    print(f"\nCompleted! Downloaded data for {len(data)} symbols.")


if __name__ == "__main__":
    main()
