# Bottom Pattern Research Log

## Goal
Identify a "stop falling" pattern in stock prices using S&P 500 data.

## Methodology
We defined a "bottom" as the lowest low price in a rolling 63-day window (approx. 3 months). We tested various confirmation patterns following this low to signal a reversal ("Stop Falling").

### Iteration 1: Simple Reversal
*   **Definition**: Close > High of 3-month Low day (within 5 days).
*   **Results**: 10,275 trades, **58.8% Win Rate**, **1.64% Avg Return**.
*   **Note**: High frequency, reliable positive expectancy.

### Iteration 2: Volume Confirmation
*   **Definition**: Simple Reversal + High Volume (> 1.2x SMA20).
*   **Results**: 6,392 trades, 57.8% Win Rate, 1.45% Avg Return.
*   **Note**: Worse performance. Volume noise?

### Iteration 3: RSI Oversold
*   **Definition**: RSI < 30 at Low.
*   **Results**: 4,627 trades, 57.9% Win Rate, 1.07% Avg Return.
*   **Note**: Oversold conditions often persist in strong downtrends.

### Iteration 4: Hammer Candlestick (Final Choice)
*   **Definition**:
    1.  Price hits a 63-day Low.
    2.  The daily candle is a **Hammer**:
        *   Lower Shadow >= 1.5 * Body Length.
        *   Upper Shadow <= 0.1 * Total Range.
*   **Results**: 2,392 trades over 10 years (500 tickers).
    *   **Win Rate**: 58.19%
    *   **Average Return (20-day hold)**: 2.25%
*   **Conclusion**: The Hammer pattern is less frequent but offers a significantly better Average Return per trade compared to simple price action. This implies a higher quality reversal signal.

## Final Result
The research identifies the **Hammer Candlestick at a 3-month Low** as a high-quality "Stop Falling" pattern.

*   **Confidence Level**: Moderate-High (~58% Win Rate).
*   **Code**: `research_bottoms_v4.py` contains the detection and backtest logic.
*   **Visualization**: See `win_*.png` and `loss_*.png` for examples.
