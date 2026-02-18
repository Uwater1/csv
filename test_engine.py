from alpha_engine import AlphaEngine
from alpha_utils import AlphaDataLoader
import pandas as pd
import numpy as np

def alpha_random(df):
    return pd.Series(np.random.randn(len(df)), index=df.index)

def alpha_momentum_5d(df):
    return df['Close'].pct_change(5)

def test_engine():
    loader = AlphaDataLoader()
    engine = AlphaEngine(loader)

    # Get a few tickers
    tickers = loader.get_mapped_tickers()[:5]
    print(f"Testing with tickers: {tickers}")

    alphas = [alpha_random, alpha_momentum_5d]

    # Test with recent data to make it faster
    results = engine.run(tickers, alphas, start_date='2023-01-01', end_date='2023-12-31')

    print("\nResults:")
    print(results)

    # Assertions
    assert not results.empty
    assert 'IC' in results.columns
    assert 'Sharpe' in results.columns
    assert 'alpha_random' in results.index
    assert 'alpha_momentum_5d' in results.index

    print("\nTest passed!")

if __name__ == "__main__":
    test_engine()
