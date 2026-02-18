import pandas as pd
import numpy as np
from alphas import ALL_ALPHAS

def create_sample_data():
    dates = pd.date_range(start='2020-01-01', periods=200)
    data = {
        'Close': np.cumprod(1 + np.random.randn(200) * 0.02) * 100,
        'Volume': np.random.randint(1000, 10000, 200),
        'NetIncomeLoss': [1000] * 200,
        'Assets': [10000] * 200,
        'GrossProfit': [500] * 200,
        'RevenueFromContractWithCustomerExcludingAssessedTax': [2000] * 200
    }
    df = pd.DataFrame(data, index=dates)
    return df

def test_alphas():
    df = create_sample_data()
    print(f"Sample data created with shape {df.shape}")

    for alpha_func in ALL_ALPHAS:
        name = alpha_func.__name__
        print(f"Testing {name}...", end=" ")
        try:
            signal = alpha_func(df)

            # Check type
            assert isinstance(signal, pd.Series), "Output must be a Series"
            # Check length
            assert len(signal) == len(df), "Output length mismatch"
            # Check index
            assert signal.index.equals(df.index), "Index mismatch"

            # Check for NaNs (some NaNs are expected at the beginning due to rolling/pct_change)
            # But not ALL NaNs
            valid_count = signal.notna().sum()
            if valid_count == 0:
                print("WARNING: All NaNs")
            else:
                print(f"OK (Valid: {valid_count}/{len(signal)})")

        except Exception as e:
            print(f"FAILED: {e}")
            raise e

    print("\nAll alphas executed.")

if __name__ == "__main__":
    test_alphas()
