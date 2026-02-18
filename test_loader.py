from alpha_utils import AlphaDataLoader
import pandas as pd

def test_loader():
    loader = AlphaDataLoader()

    # Test 1: Get all tickers
    tickers = loader.get_all_tickers()
    print(f"Total tickers: {len(tickers)}")

    mapped_tickers = loader.get_mapped_tickers()
    print(f"Mapped tickers: {len(mapped_tickers)}")

    if not mapped_tickers:
        print("No mapped tickers found. Aborting test.")
        return

    # Test 2: Load data for a specific ticker (e.g., AAPL)
    ticker = 'AAPL'
    if ticker not in mapped_tickers:
        ticker = mapped_tickers[0] # Fallback

    print(f"Testing loading for {ticker}...")
    df = loader.get_data(ticker)

    if df is None:
        print("Failed to load data.")
        return

    print(f"Data shape: {df.shape}")
    print(f"Columns: {df.columns[:10]}") # Print first few columns

    # Check for price columns
    required_price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_price_cols:
        assert col in df.columns, f"Missing price column: {col}"

    # Check for fundamental columns
    # We expect some fundamental columns if the mapping worked
    # Example from Apple_Inc.csv: AccountsPayableCurrent
    found_fundamental = False
    possible_fund_cols = ['AccountsPayableCurrent', 'NetIncomeLoss', 'Assets', 'Liabilities']

    for col in df.columns:
        if col in possible_fund_cols:
            found_fundamental = True
            print(f"Found fundamental column: {col}")
            # Check if it has non-null values
            valid_count = df[col].notna().sum()
            print(f"  Valid values: {valid_count}/{len(df)}")
            break

    if not found_fundamental:
        print("Warning: No common fundamental columns found. Check column names.")
        print("Available columns:", df.columns.tolist())

    # Check index
    print(f"Index type: {type(df.index)}")
    print(f"Start date: {df.index[0]}")
    print(f"End date: {df.index[-1]}")

    assert isinstance(df.index, pd.DatetimeIndex), "Index is not DatetimeIndex"
    assert df.index.is_monotonic_increasing, "Index is not sorted"

    print("Test passed!")

if __name__ == "__main__":
    test_loader()
