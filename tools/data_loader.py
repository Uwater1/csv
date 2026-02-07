import pandas as pd
from pathlib import Path
from typing import List

class DataLoader:
    """
    A class to handle loading and preprocessing of stock data from CSV files.
    """
    def __init__(self, data_dir: str = 'price'):
        """
        Initialize the DataLoader.

        Args:
            data_dir (str): Path to the directory containing stock CSV files.
        """
        self.data_dir = Path(data_dir)

    def load_data(self, ticker: str) -> pd.DataFrame:
        """
        Loads data for a specific ticker.

        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            pd.DataFrame: A DataFrame containing the stock data with 'Date' as index.

        Raises:
            FileNotFoundError: If the data file for the ticker does not exist.
            ValueError: If the CSV does not contain a 'Date' column.
        """
        filepath = self.data_dir / f"{ticker}.csv"
        if not filepath.exists():
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

    def get_all_tickers(self) -> List[str]:
        """
        Returns a list of all available tickers in the price directory.

        Returns:
            List[str]: Sorted list of ticker symbols.
        """
        if not self.data_dir.exists():
            return []

        files = self.data_dir.glob("*.csv")
        tickers = [f.stem for f in files]
        return sorted(tickers)
