# Extend Price Fact CSV to Full US Equity Universe

## Goal
Maximize coverage of US stocks in `price/*.csv` with the longest possible historical window.

## Universe: All active NYSE, NASDAQ, and AMEX common equities
- Target ~4k–5k tickers (up from current ~514)
- Source authoritative active ticker lists with exchange + security type metadata

## Duration: Max possible history
- `yfinance.Ticker.history(period="max", interval="1d")` already returns yahoo’s full history for each ticker
- **Remove** the `df.index >= '2002-01-01'` filter in `download_yfinance.py` so oldest available data is retained
- Update downstream consumers (`alpha_utils.py`, `tools/data_loader.py`) to handle pre-2002 dates gracefully (they already use DatetimeIndex so should be fine)

## Ticker List Generation
Create a helper that builds the universe from authoritative sources:

1. **NASDAQ**: `nasdaqtraded.txt` from `https://ftp.nasdaqtrader.com/symboldirectory/nasdaqtraded.txt`
   - Filter: `Exchange` in `N` and `Test Issue != Y` and security-type classes that are equity (common stock, ETF excluded)
   - Note: NASDAQ’s FTP is official but includes funds/warrants; filter by `Security Name` patterns or `ETF` flag where available. If precise filtering is unreliable, keep it simple: all NASDAQ-listed tickers excluding clear non-equity categories.

2. **NYSE / AMEX**: `otherlisted.txt` from same FTP
   - Filter: `Exchange` = `A` (AMEX) or `N` (NYSE)
   - Exclude ETFs or preferred shares if identifiable via `Security Name` or `ETF` column

3. **Deduplicate** across sources.

4. **Persist** to `universe.csv` with columns: `symbol`, `exchange`, `security_type`

5. **Incremental skip**: only download tickers that don’t already exist in `price/*.csv`, unless `--force` is passed.

## Changes to `download_yfinance.py`

1. Add `build_equity_universe()` that fetches/parses `nasdaqtraded.txt` and `otherlisted.txt`, filters to equities, and writes `universe.csv`.
2. Merge universe symbols with `code-temp-old/20260105.csv` and `nq100_unique_symbols.txt` (existing tickers take precedence).
3. **Remove** the `df.index >= '2002-01-01'` date filter.
4. Add skip logic: if `{output_dir}/{symbol}.csv` exists and is non-empty, skip unless `--force`.
5. Improve rate limiting: use `time.sleep(0.3)` (better balance for ~5k tickers; 5k * 0.3s ≈ 25 min).
6. Add retry on transient errors (1 retry with exponential backoff after 2s).
7. Preserve `failed` symbols list for reporting.

## Runtime Estimates
- ~5k tickers * 0.3s sleep = ~25 minutes on clean run
- Delta run (only new tickers) = minutes
- Max history per ticker on avg is 50 KB → ~250 MB total for ~5k tickers

## Validation
1. After run, `price/` should contain ~5k files (vs current 514).
2. Spot-check `AAPL.csv`, `MSFT.csv`, and a newly added ticker to verify oldest date is pre-2002.
3. Verify no duplicate ticker symbols in `universe.csv`.
4. Verify `alpha_utils.py` and `tools/data_loader.py` load extended CSV without changes (DatetimeIndex-based logic is exchange-agnostic).
5. Run `test_loader.py` and `test_engine.py`.

## Out of Scope
- Fractional shares / adjusted vs unadjusted price
- Re-downloading partial data for already-present tickers without `--force`
- Fundamental fact CSV enrichment (separate SEC EDGAR pipeline)

## Files Changed
- `download_yfinance.py` — main changes
- `universe.csv` — new generated file (not checked in by default, treat as artifact)
