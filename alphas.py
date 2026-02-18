import pandas as pd
import numpy as np

def _get_fundamental_col(df, possible_names):
    for col in possible_names:
        if col in df.columns:
            return df[col]
    return None

def alpha_reversal_5d(df):
    """
    Short-term reversal: -1 * 5-day return.
    """
    returns_5d = df['Close'].pct_change(5)
    return -1 * returns_5d

def alpha_momentum_21d(df):
    """
    Short-term momentum: 21-day return.
    """
    return df['Close'].pct_change(21)

def alpha_momentum_126d(df):
    """
    Medium-term momentum: 126-day return.
    """
    return df['Close'].pct_change(126)

def alpha_volatility_20d(df):
    """
    Low volatility anomaly: -1 * 20-day volatility.
    """
    returns = df['Close'].pct_change()
    vol = returns.rolling(window=20).std()
    return -1 * vol

def alpha_rsi_14(df):
    """
    RSI 14. Mean reversion signal: 100 - RSI (so high RSI -> low signal).
    """
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # We want to buy when RSI is low (oversold) -> higher signal
    # So we return -1 * RSI (or similar).
    # Normalized: 50 - RSI. (Positive if RSI < 50, Negative if RSI > 50)
    return 50 - rsi

def alpha_return_on_assets(df):
    """
    ROA: Net Income / Assets.
    """
    # Fundamental data is forward filled.
    net_income = _get_fundamental_col(df, ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'NetIncome'])
    assets = _get_fundamental_col(df, ['Assets', 'TotalAssets'])

    if net_income is None or assets is None:
        return pd.Series(np.nan, index=df.index)

    return net_income / assets

def alpha_gross_margin(df):
    """
    Gross Margin: Gross Profit / Revenue.
    """
    gross_profit = _get_fundamental_col(df, ['GrossProfit'])
    revenue = _get_fundamental_col(df, ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues', 'Revenue'])

    if gross_profit is None or revenue is None:
        return pd.Series(np.nan, index=df.index)

    return gross_profit / revenue

def alpha_mom_vol(df):
    """
    Momentum scaled by volatility.
    """
    mom = alpha_momentum_21d(df)
    vol = df['Close'].pct_change().rolling(window=21).std()

    return mom / vol

ALL_ALPHAS = [
    alpha_reversal_5d,
    alpha_momentum_21d,
    alpha_momentum_126d,
    alpha_volatility_20d,
    alpha_rsi_14,
    alpha_return_on_assets,
    alpha_gross_margin,
    alpha_mom_vol
]
