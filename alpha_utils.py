import pandas as pd
import json
import os
from pathlib import Path

class AlphaDataLoader:
    def __init__(self, price_dir='price', fact_dir='factCsv', ticker_map_path='ticker_map.json'):
        self.price_dir = Path(price_dir)
        self.fact_dir = Path(fact_dir)
        self.ticker_map = {}

        if os.path.exists(ticker_map_path):
            with open(ticker_map_path, 'r') as f:
                self.ticker_map = json.load(f)
        else:
            print(f"Warning: {ticker_map_path} not found. Fundamental data loading might fail.")

    def load_price_data(self, ticker):
        filepath = self.price_dir / f"{ticker}.csv"
        if not filepath.exists():
            print(f"Price file not found for {ticker}")
            return None

        try:
            df = pd.read_csv(filepath)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], utc=True)
                df.set_index('Date', inplace=True)
                df.sort_index(inplace=True)
            return df
        except Exception as e:
            print(f"Error loading price data for {ticker}: {e}")
            return None

    def load_fundamental_data(self, ticker):
        if ticker not in self.ticker_map:
            # print(f"No mapping found for {ticker}")
            return None

        filename = self.ticker_map[ticker]
        filepath = self.fact_dir / filename

        if not filepath.exists():
            print(f"Fundamental file not found: {filepath}")
            return None

        try:
            # Read CSV
            # The format is: fact_unit, date1, date2, ...
            # row1: MetricName, val1, val2, ...
            df = pd.read_csv(filepath)

            # Transpose
            # Set the first column (metric names) as index temporarily to transpose correctly
            df.set_index(df.columns[0], inplace=True)
            df_t = df.transpose()

            # The index of df_t is now the dates.
            # Convert index to datetime
            df_t.index = pd.to_datetime(df_t.index, utc=True, errors='coerce')
            df_t.sort_index(inplace=True)

            # Remove rows with NaT index (if any weird columns existed)
            df_t = df_t[df_t.index.notnull()]

            # Clean column names (metrics)
            # Example: "AccountsPayableCurrent / USD" -> "AccountsPayableCurrent"
            clean_cols = {col: col.split(' / ')[0] for col in df_t.columns}
            df_t.rename(columns=clean_cols, inplace=True)

            # Convert columns to numeric
            for col in df_t.columns:
                df_t[col] = pd.to_numeric(df_t[col], errors='coerce')

            return df_t

        except Exception as e:
            print(f"Error loading fundamental data for {ticker}: {e}")
            return None

    def get_data(self, ticker, start_date=None, end_date=None):
        """
        Loads price and fundamental data, merges them.
        Fundamental data is forward filled.
        """
        price_df = self.load_price_data(ticker)
        if price_df is None:
            return None

        fact_df = self.load_fundamental_data(ticker)

        if fact_df is not None:
            # Merge
            # We want to keep all price dates.
            # We align fundamental data to price data.
            # Since fundamental data is sparse, we join on index (Date) using 'outer'
            # to include fundamental dates that might not be trading days (though less likely if reporting date)
            # Actually, usually we reindex fundamental to price index with ffill.

            # Reindex fact_df to price_df.index using method='ffill'
            # But fact_df might have dates not in price_df (weekends).
            # Better approach: concat and sort, then ffill, then trim to price_df index.

            # A safer way usually:
            # 1. Join price and fact (outer)
            # 2. Ffill fact columns
            # 3. Filter to days where price exists.

            merged = price_df.join(fact_df, how='outer', rsuffix='_fact')

            # Forward fill fundamental columns
            # Identify fundamental columns: those from fact_df
            fact_cols = fact_df.columns
            merged[fact_cols] = merged[fact_cols].ffill()

            # Filter back to rows where we have price data (Close is not NaN)
            merged = merged[merged['Close'].notna()]
        else:
            merged = price_df

        if start_date:
            merged = merged[merged.index >= pd.to_datetime(start_date, utc=True)]
        if end_date:
            merged = merged[merged.index <= pd.to_datetime(end_date, utc=True)]

        return merged

    def get_all_tickers(self):
        """Returns list of all tickers available in price directory"""
        files = self.price_dir.glob("*.csv")
        return sorted([f.stem for f in files])

    def get_mapped_tickers(self):
        """Returns list of tickers that have fundamental data mapped"""
        # Filter price tickers that are in the map
        price_tickers = self.get_all_tickers()
        return [t for t in price_tickers if t in self.ticker_map]
