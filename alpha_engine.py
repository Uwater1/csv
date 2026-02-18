import pandas as pd
import numpy as np
from alpha_utils import AlphaDataLoader

class AlphaEngine:
    def __init__(self, loader: AlphaDataLoader):
        self.loader = loader

    def run(self, tickers, alphas, start_date=None, end_date=None):
        """
        Run alphas on tickers and calculate metrics.

        Args:
            tickers: List of ticker strings.
            alphas: List of functions (or callables) that take a DataFrame and return a Series.
                    The function should be named, e.g. def alpha_momentum(df): ...
            start_date: Start date string.
            end_date: End date string.

        Returns:
            summary_df: DataFrame with metrics for each alpha.
        """

        all_returns = {}
        all_signals = {alpha.__name__: {} for alpha in alphas}

        print(f"Processing {len(tickers)} tickers...")

        for i, ticker in enumerate(tickers):
            if i % 10 == 0:
                print(f"  {i}/{len(tickers)}...")

            df = self.loader.get_data(ticker, start_date=start_date, end_date=end_date)

            if df is None or df.empty:
                continue

            # Calculate forward returns (1 day)
            # Signal at t uses data up to t. Trade at t (Close) or t+1 (Open).
            # Assuming trading at Close t+1 vs Close t is standard for simple backtests (Return t+1)
            # Shift(-1) gives Return at t+1 aligned to index t.
            # pct_change() gives (P_t - P_t-1)/P_t-1.
            # We want (P_t+1 - P_t)/P_t.
            # So df['Close'].pct_change().shift(-1)

            returns = df['Close'].pct_change().shift(-1)
            all_returns[ticker] = returns

            for alpha in alphas:
                try:
                    signal = alpha(df)
                    # Ensure signal index matches df index
                    if len(signal) != len(df):
                        # Reindex to be safe if alpha dropped NaNs
                        signal = signal.reindex(df.index)
                    all_signals[alpha.__name__][ticker] = signal
                except Exception as e:
                    print(f"Error calculating {alpha.__name__} for {ticker}: {e}")

        print("Aggregating data...")
        # Create DataFrames: Index=Date, Columns=Ticker
        returns_df = pd.DataFrame(all_returns)

        summary_data = []

        for alpha_name, signals_dict in all_signals.items():
            print(f"Evaluating {alpha_name}...")
            signals_df = pd.DataFrame(signals_dict)

            # Align signals and returns
            # Keep only indices present in both
            common_index = returns_df.index.intersection(signals_df.index)
            # Also align columns
            common_cols = returns_df.columns.intersection(signals_df.columns)

            rets = returns_df.loc[common_index, common_cols]
            sigs = signals_df.loc[common_index, common_cols]

            # Remove dates where we don't have enough data
            # e.g. start or end might be NaN

            # Metrics Calculation
            metrics = self.calculate_metrics(sigs, rets)
            metrics['Alpha'] = alpha_name
            summary_data.append(metrics)

        return pd.DataFrame(summary_data).set_index('Alpha')

    def calculate_metrics(self, signals, returns):
        """
        Calculate alpha metrics.
        """
        # 1. IC (Information Coefficient)
        # Rank correlation per day
        ic_series = signals.corrwith(returns, axis=1, method='spearman')

        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        icir = ic_mean / ic_std if ic_std != 0 else np.nan

        # 2. Returns (Long-Short Portfolio)
        # Weights: demeaned and scaled to sum(abs) = 1 (dollar neutral)
        # Note: Simple approach.
        # Demean cross-sectionally
        sigs_demeaned = signals.sub(signals.mean(axis=1), axis=0)
        # Scale
        abs_sum = sigs_demeaned.abs().sum(axis=1)
        weights = sigs_demeaned.div(abs_sum, axis=0).fillna(0)

        # Portfolio return
        port_rets = (weights * returns).sum(axis=1)

        # Filter out NaN returns (days with no trades)
        # Only consider days where we had signals
        valid_days = abs_sum > 0
        port_rets = port_rets[valid_days]

        daily_sharpe = port_rets.mean() / port_rets.std() if port_rets.std() != 0 else 0
        sharpe = daily_sharpe * np.sqrt(252)

        win_rate = (port_rets > 0).mean()

        # Turnover
        # Weight change
        weight_change = weights.diff().abs().sum(axis=1)
        turnover = weight_change.mean()

        # Annualized Return
        # Mean daily return * 252
        ann_return = port_rets.mean() * 252

        return {
            'IC': ic_mean,
            'ICIR': icir,
            'Sharpe': sharpe,
            'WinRate': win_rate,
            'Turnover': turnover,
            'AnnReturn': ann_return
        }
