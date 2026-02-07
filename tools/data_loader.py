import pandas as pd
import os

class DataLoader:
    def __init__(self, data_dir='price'):
        self.data_dir = data_dir

    def load_data(self, ticker):
        """Loads data for a specific ticker."""
        filepath = os.path.join(self.data_dir, f"{ticker}.csv")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Data for ticker {ticker} not found at {filepath}")

        df = pd.read_csv(filepath)

        # Ensure Date column is parsed
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
        else:
            raise ValueError("CSV must contain a 'Date' column")

        return df

    def get_all_tickers(self):
        """Returns a list of all available tickers in the price directory."""
        files = os.listdir(self.data_dir)
        tickers = [f.replace('.csv', '') for f in files if f.endswith('.csv')]
        return sorted(tickers)
