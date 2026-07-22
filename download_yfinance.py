"""
Script to download historical stock data from yfinance.
Builds the full US equity universe from NYSE/NASDAQ/AMEX symbol directories
and downloads daily OHLCV with period="max".
"""
import argparse
import csv
import io
import os
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd
import yfinance as yf

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqtraded.txt"
OTHERLISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
DELTAS_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/TradingSystemAddsDeletes.txt"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={apikey}"
UNIVERSE_CSV = "universe.csv"
BASE_SYMBOLS_CSV = "code-temp-old/20260105.csv"
BASE_SYMBOLS_TXT = "code-temp-old/nq100_unique_symbols.txt"
DEFAULT_OUTPUT_DIR = "price"

EXCLUDE_NAME_PATTERNS = [
    re.compile(r"\bunits?\b", re.I),
    re.compile(r"\bwarrants?\b", re.I),
    re.compile(r"\bpreferred\b", re.I),
    re.compile(r"\bnon-redeemable\b", re.I),
]


def _is_equity_name(name: str) -> bool:
    if not name:
        return False
    n = name.strip()
    if any(p.search(n) for p in EXCLUDE_NAME_PATTERNS):
        return False
    return True


def _fetch(url: str) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=45) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Warning: failed to fetch {url}: {e}")
        return None


def build_equity_universe() -> pd.DataFrame:
    """
    Build the US equity universe from NASDAQ Trader symbol directories.
    Returns a DataFrame with columns: symbol, exchange, security_name, source.
    """
    print("Building equity universe from NASDAQ Trader symbol directories...")

    nasdaq_text = _fetch(NASDAQ_URL)
    other_text = _fetch(OTHERLISTED_URL)
    deltas_text = _fetch(DELTAS_URL)

    frames = []

    # --- nasdaqtraded.txt ---
    # Header: Nasdaq Traded|Symbol|Security Name|Listing Exchange|Market Category|ETF|Round Lot Size|Test Issue|Financial Status|CQS Symbol|NASDAQ Symbol|NextShares
    if nasdaq_text:
        nasdaq_df = pd.read_csv(io.StringIO(nasdaq_text), sep="|", dtype=str).fillna("")
        nasdaq_df.columns = [c.strip() for c in nasdaq_df.columns]
        valid_nasdaq_exchanges = {"N", "Q", "G", "S", "A", "P", "Z"}
        nasdaq_df = nasdaq_df[
            (nasdaq_df["Nasdaq Traded"].str.upper() == "Y")
            & (nasdaq_df["Test Issue"].str.upper() != "Y")
            & (nasdaq_df["ETF"].str.upper() != "Y")
            & (nasdaq_df["Listing Exchange"].isin(valid_nasdaq_exchanges))
            & (nasdaq_df["Security Name"].apply(_is_equity_name))
        ].copy()
        nasdaq_df["symbol"] = nasdaq_df["Symbol"].str.strip().str.upper()
        nasdaq_rows = nasdaq_df[["symbol", "Listing Exchange", "Security Name"]].rename(
            columns={"Listing Exchange": "exchange", "Security Name": "security_name"}
        )
        nasdaq_rows["source"] = "nasdaq"
        frames.append(nasdaq_rows)

    # --- otherlisted.txt ---
    # Header: ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
    if other_text:
        other_df = pd.read_csv(io.StringIO(other_text), sep="|", dtype=str).fillna("")
        other_df.columns = [c.strip() for c in other_df.columns]
        valid_other_exchanges = {"A", "N", "P", "Z"}
        other_df = other_df[
            (other_df["Test Issue"].str.upper() != "Y")
            & (other_df["ETF"].str.upper() != "Y")
            & (other_df["Exchange"].isin(valid_other_exchanges))
            & (other_df["Security Name"].apply(_is_equity_name))
        ].copy()
        other_df["symbol"] = other_df["ACT Symbol"].str.strip().str.upper()
        other_rows = other_df[["symbol", "Exchange", "Security Name"]].rename(
            columns={"Exchange": "exchange", "Security Name": "security_name"}
        )
        other_rows["source"] = "otherlisted"
        frames.append(other_rows)

    if deltas_text:
        try:
            deltas_df = pd.read_csv(
                io.StringIO(deltas_text), sep="|", dtype=str, skipfooter=1, engine="python"
            ).fillna("")
            if not deltas_df.empty:
                deltas_df.columns = [c.strip() for c in deltas_df.columns]
                action_col = next(
                    (c for c in deltas_df.columns if "Action" in c), None
                )
                if action_col:
                    del_df = deltas_df[
                        deltas_df[action_col].str.upper() == "DELETE"
                    ].copy()
                    del_df["symbol"] = (
                        del_df.get("Symbol", pd.Series(dtype=str))
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.upper()
                    )
                    del_df = del_df[del_df["symbol"].ne("")]
                    del_df["exchange"] = (
                        del_df.get("Primary Listing Market", pd.Series(dtype=str))
                        .fillna("")
                    )
                    del_df["security_name"] = (
                        del_df.get("Company Name", pd.Series(dtype=str)).fillna("")
                    )
                    del_rows = del_df[["symbol", "exchange", "security_name"]]
                    del_rows["source"] = "deleted"
                    frames.append(del_rows)
                    print(f"  Recent delistings: {len(del_rows)}")
        except Exception as e:
            print(f"Warning: failed to parse deltas file: {e}")

    if not frames:
        raise RuntimeError("Unable to fetch any symbol directory data from NASDAQ Trader sources.")

    combined = pd.concat(frames, ignore_index=True)
    combined["symbol"] = combined["symbol"].astype(str).str.strip().str.upper()
    combined = combined[combined["symbol"].ne("") & combined["symbol"].notna()]
    combined = combined.drop_duplicates(subset="symbol").reset_index(drop=True)
    combined = combined.sort_values("symbol").reset_index(drop=True)

    combined.to_csv(UNIVERSE_CSV, index=False)
    print(f"Universe built: {len(combined)} unique equity symbols")
    print(combined.groupby("source").size().to_string())
    print(f"Saved -> {UNIVERSE_CSV}")
    return combined


def fetch_alphavantage_symbols(apikey: str) -> set:
    """
    Supplementary source: Alpha Vantage LISTING_STATUS.
    Returns active US exchange-listed equities not already in universe.csv.
    """
    url = ALPHA_VANTAGE_URL.format(apikey=apikey)
    text = _fetch(url)
    if not text:
        print("Warning: Alpha Vantage fetch failed. Skipping.")
        return set()
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    valid_exchanges = {"NASDAQ", "NYSE", "AMEX", "NYSE ARCA", "NYSE MKT", "BATS", "OTC"}
    stocks = {
        r["symbol"].strip().upper()
        for r in rows
        if r.get("assetType", "").strip() == "Stock"
        and r.get("exchange", "").strip() in valid_exchanges
        and r.get("status", "").strip() == "Active"
    }
    print(f"Alpha Vantage provided {len(rows)} total rows, {len(stocks)} stocks on US equity exchanges")

    # deduplicate against existing universe
    existing = set()
    if os.path.exists(UNIVERSE_CSV):
        with open(UNIVERSE_CSV) as f:
            reader2 = csv.DictReader(f)
            existing = {r["symbol"].strip().upper() for r in reader2 if r.get("symbol")}
    added = sorted(stocks - existing)
    print(f"Alpha Vantage adds {len(added)} new symbols beyond NASDAQ universe")
    if added:
        print(f"  Sample: {added[:20]}")
    return set(added)


def read_symbols_from_csv(csv_path: str) -> set:
    symbols = set()
    if not os.path.exists(csv_path):
        return symbols
    df = pd.read_csv(csv_path)
    if "Symbol" in df.columns:
        symbols.update(df["Symbol"].dropna().astype(str).str.strip().tolist())
    return symbols


def read_symbols_from_txt(txt_path: str) -> set:
    symbols = set()
    if not os.path.exists(txt_path):
        return symbols
    with open(txt_path, "r") as f:
        for line in f:
            s = line.strip()
            if s:
                symbols.add(s)
    return symbols


def load_existing_symbols(output_dir: str) -> set:
    path = Path(output_dir)
    if not path.exists():
        return set()
    return {p.stem for p in path.glob("*.csv") if p.is_file() and p.stat().st_size > 0}


def download_stock_data(
    symbols: set,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    period: str = "max",
    interval: str = "1d",
    force: bool = False,
) -> dict:
    """
    Download historical stock data for given symbols.
    Skips symbols that already have a non-empty CSV in output_dir unless force=True.
    Retries once on transient errors.
    """
    if not symbols:
        print("No symbols to download.")
        return {}

    existing = set() if force else load_existing_symbols(output_dir)
    symbols_to_download = sorted(symbols - existing)
    skipped = len(symbols) - len(symbols_to_download)

    print(f"Requested: {len(symbols)} | Skipped (already present): {skipped} | To download: {len(symbols_to_download)}")
    Path(output_dir).mkdir(exist_ok=True)
    results = {}
    failed = []

    for i, symbol in enumerate(symbols_to_download, 1):
        downloaded = False
        for attempt in range(2):
            try:
                print(f"[{i}/{len(symbols_to_download)}] {symbol} ...", end=" ", flush=True)
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                if not df.empty:
                    df_to_save = df.drop(columns=["Symbol"], errors="ignore")
                    numeric_cols = df_to_save.select_dtypes(include=["float64", "float32"]).columns
                    df_to_save[numeric_cols] = df_to_save[numeric_cols].round(5)
                    filepath = os.path.join(output_dir, f"{symbol}.csv")
                    df_to_save.to_csv(filepath)
                    results[symbol] = df_to_save
                    print(f"OK ({len(df_to_save)} rows)")
                    downloaded = True
                else:
                    failed.append(symbol)
                    print("No data")
                break
            except Exception as e:
                print(f"Error: {e}")
                if attempt == 0:
                    time.sleep(2)
                    print("  retrying ...", end=" ", flush=True)
                else:
                    failed.append(symbol)
        time.sleep(0.3)

    if failed:
        print(f"\nFailed ({len(failed)}): {failed}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Download full US equity price history from yfinance")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--force", action="store_true", help="Re-download even if file exists")
    parser.add_argument("--no-build-universe", action="store_true", help="Skip universe.csv rebuild")
    parser.add_argument("--alpha-vantage-key", default="", help="Alpha Vantage API key (optional)")
    parser.add_argument("--include-recent-delisted", action="store_true", help="Include recent delistings from NASDAQ deltas")
    args = parser.parse_args()

    if not args.no_build_universe:
        build_equity_universe()

    if not os.path.exists(UNIVERSE_CSV):
        print(f"Error: {UNIVERSE_CSV} not found. Run without --no-build-universe first.")
        return

    universe_df = pd.read_csv(UNIVERSE_CSV)
    universe_symbols = set(universe_df["symbol"].dropna().astype(str).str.strip())

    csv_symbols = read_symbols_from_csv(BASE_SYMBOLS_CSV)
    txt_symbols = read_symbols_from_txt(BASE_SYMBOLS_TXT)
    base_symbols = csv_symbols.union(txt_symbols)

    # Optionally add recent delistings from NASDAQ deltas file
    delisted_symbols = set()
    if args.include_recent_delisted:
        deltas_text = _fetch(DELTAS_URL)
        if deltas_text:
            try:
                deltas_df = pd.read_csv(
                    io.StringIO(deltas_text), sep="|", dtype=str, skipfooter=1, engine="python"
                ).fillna("")
                if not deltas_df.empty:
                    deltas_df.columns = [c.strip() for c in deltas_df.columns]
                    action_col = next((c for c in deltas_df.columns if "Action" in c), None)
                    if action_col:
                        del_list = deltas_df[deltas_df[action_col].str.upper() == "DELETE"]
                        delisted_symbols = set(del_list.get("Symbol", pd.Series(dtype=str)).fillna("").astype(str).str.strip().str.upper())
                        print(f"Recent delistings added: {len(delisted_symbols)}")
            except Exception as e:
                print(f"Warning: failed to parse deltas file: {e}")

    # Optionally add Alpha Vantage symbols
    av_symbols = set()
    if args.alpha_vantage_key:
        av_symbols = fetch_alphavantage_symbols(args.alpha_vantage_key)

    all_symbols = universe_symbols.union(base_symbols).union(delisted_symbols).union(av_symbols)
    print(f"Universe symbols: {len(universe_symbols)}")
    print(f"Base S&P500+NQ100 (already in universe): {len(universe_symbols & base_symbols)}")
    print(f" Additional base tickers: {len(base_symbols - universe_symbols)}")
    print(f"Recent delisted tickers: {len(delisted_symbols)}")
    print(f"Alpha Vantage supplemental tickers: {len(av_symbols)}")
    print(f"Total unique symbols to process: {len(all_symbols)}")

    data = download_stock_data(
        all_symbols, output_dir=args.output_dir, period="max", interval="1d", force=args.force
    )
    print(f"\nDone. Downloaded {len(data)} symbols.")


if __name__ == "__main__":
    main()
