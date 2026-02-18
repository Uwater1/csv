from tools.data_loader import DataLoader

def main():
    loader = DataLoader()

    # Test getting all tickers
    tickers = loader.get_all_tickers()
    print(f"Found {len(tickers)} tickers.")
    if 'AAPL' in tickers:
        print("AAPL found in tickers list.")

    # Test loading AAPL
    try:
        df = loader.load_data('AAPL')
        print("Successfully loaded AAPL data.")
        print(f"Shape: {df.shape}")
        print("Head:")
        print(df.head())
        print("Tail:")
        print(df.tail())
    except Exception as e:
        print(f"Error loading AAPL: {e}")

if __name__ == "__main__":
    main()
