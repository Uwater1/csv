from alpha_engine import AlphaEngine
from alpha_utils import AlphaDataLoader
from alphas import ALL_ALPHAS
import pandas as pd
import datetime

def main():
    print("Starting Alpha Mining...")

    # 1. Setup
    loader = AlphaDataLoader()
    engine = AlphaEngine(loader)

    # 2. Get Tickers
    tickers = loader.get_mapped_tickers()
    print(f"Loaded {len(tickers)} tickers for analysis.")

    # 3. Define Period
    # Last 5 years approx.
    start_date = '2020-01-01'
    end_date = '2024-12-31'
    print(f"Period: {start_date} to {end_date}")

    # 4. Run Engine
    results = engine.run(tickers, ALL_ALPHAS, start_date=start_date, end_date=end_date)

    # 5. Assessment and Filtering
    print("\nAll Alpha Results:")
    print(results.sort_values('IC', ascending=False))

    # Save raw results
    results.to_csv("alpha_mining_results.csv")

    # Filter for "Usable"
    # Criteria: IC > 0.02 (or < -0.02 if reversed), |ICIR| > 0.5, Sharpe > 0.5
    # Note: Alphas might be inverse (negative IC). If so, we should inverse the signal.
    # For now, I'll just list them.

    usable = results[
        (results['IC'].abs() > 0.005) &
        (results['ICIR'].abs() > 0.05)
    ].sort_values('Sharpe', ascending=False)

    print("\nCandidate Usable Alphas (IC > 0.005, ICIR > 0.05):")
    print(usable)

    usable.to_csv("usable_alphas.csv")
    print("\nResults saved to alpha_mining_results.csv and usable_alphas.csv")

if __name__ == "__main__":
    main()
