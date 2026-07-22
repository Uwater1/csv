"""
Collect delisted US stocks from multiple sources and build the master stock registry.
Sources:
  1. NASDAQ Trader TradingSystemAddsDeletes.txt (recent delistings)
  2. yfinance probing of universe with no data (historical delistings)
  3. Alpha Vantage LISTING_STATUS (if key provided)
  4. FINRA OTCBB/OTCQX lists
Output: stock_master.csv with symbol, name, exchange, status, and metadata.
"""
import argparse
import csv
import io
import json
import os
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd
import yfinance as yf
from download_yfinance import (
    DELTAS_URL,
    UNIVERSE_CSV,
    DEFAULT_OUTPUT_DIR,
    _fetch,
    load_existing_symbols,
    download_stock_data,
)


def fetch_nasdaq_delistings() -> pd.DataFrame:
    rows = []
    text = _fetch(DELTAS_URL)
    if not text:
        print("nasdaq deltas: fetch failed")
        return pd.DataFrame()
    try:
        df = pd.read_csv(io.StringIO(text), sep="|", dtype=str, skipfooter=1, engine="python").fillna("")
        if df.empty:
            return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        action_col = next((c for c in df.columns if "Action" in c), None)
        if not action_col:
            return pd.DataFrame()
        del_df = df[df[action_col].str.upper() == "DELETE"].copy()
        del_df["symbol"] = del_df.get("Symbol", pd.Series(dtype=str)).fillna("").astype(str).str.strip().str.upper()
        del_df = del_df[del_df["symbol"].ne("")]
        for _, r in del_df.iterrows():
            rows.append({
                "symbol": r["symbol"],
                "name": r.get("Company Name", ""),
                "exchange": r.get("Primary Listing Market", ""),
                "status": "delisted",
                "source": "nasdaq_deltas",
                "effective_date": r.get("Effective Date", ""),
            })
    except Exception as e:
        print(f"nasdaq deltas parse error: {e}")
    return pd.DataFrame(rows)


def probe_yfinance_delisted(symbols: set, output_dir: str = DEFAULT_OUTPUT_DIR, batch_size: int = 500) -> pd.DataFrame:
    rows = []
    existing = load_existing_symbols(output_dir)
    missing = sorted(symbols - existing)
    print(f"Probing {len(missing)} missing symbols via yfinance to detect delistings...")

    for i, sym in enumerate(missing, 1):
        try:
            t = yf.Ticker(sym)
            df = t.history(period="5d", interval="1d")
            if df.empty:
                rows.append({"symbol": sym, "status": "delisted_or_inactive", "source": "yfinance_probe"})
        except Exception:
            pass
        if i % batch_size == 0:
            print(f"  probed {i}/{len(missing)}")
        time.sleep(0.05)

    print(f"  Candidates identified: {len(rows)}")
    return pd.DataFrame(rows)


def fetch_otc_pink_sheets() -> pd.DataFrame:
    rows = []
    urls = {
        "otcbb": "https://www.otcmarkets.com/otcapi/otc/securities/otcbb?pageSize=10000&page=1",
        "ocx": "https://www.otcmarkets.com/otcapi/otc/securities/ox?pageSize=10000&page=1",
        "pink": "https://www.otcmarkets.com/otcapi/otc/securities/pink?pageSize=10000&page=1",
    }
    for mkt, url in urls.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
            securities = data.get("records", [])
            for sec in securities:
                sym = str(sec.get("symbol", "")).strip().upper()
                name = str(sec.get("name", "")).strip()
                if sym and re.match(r'^[A-Z][A-Z0-9\.]{0,4}$', sym):
                    rows.append({
                        "symbol": sym,
                        "name": name,
                        "exchange": f"OTC_{mkt.upper()}",
                        "status": "active_otc",
                        "source": f"otcmarkets_{mkt}",
                    })
            print(f"  {mkt}: {len(securities)}")
        except Exception as e:
            print(f"  {mkt} fetch error: {e}")
    return pd.DataFrame(rows)


def fetch_finra_otc() -> pd.DataFrame:
    rows = []
    urls = [
        "https://www.finra.org/compliance/technology/products/thomson-reuters/otcbb-pink-sheets",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=20).read().decode()
            for m in re.finditer(r'\b([A-Z]{1,5})\b', html):
                sym = m.group(1)
                if sym not in {"FINRA", "HTTP", "HTTPS", "HTML", "BODY", "DIV", "SPAN", "TABLE", "HEAD", "META", "TITLE", "LINK", "SCRIPT"}:
                    rows.append({
                        "symbol": sym,
                        "name": "",
                        "exchange": "FINRA_OTC",
                        "status": "unknown_otc",
                        "source": "finra_web",
                    })
        except Exception as e:
            print(f"finra fetch error: {e}")
    print(f"  finra candidates: {len(rows)}")
    return pd.DataFrame(rows)


def build_master_csv(output_path: str = "stock_master.csv", universe_path: str = UNIVERSE_CSV, output_dir: str = DEFAULT_OUTPUT_DIR):
    print("Building master stock registry...")
    frames = []

    # 1) Active universe
    if Path(universe_path).exists():
        u = pd.read_csv(universe_path)
        u["status"] = "active"
        u["source"] = "nasdaq_trader"
        u["effective_date"] = ""
        u = u.rename(columns={"security_name": "name"})
        frames.append(u[[c for c in ["symbol", "name", "exchange", "security_type", "status", "source", "effective_date"] if c in u.columns]])
        print(f"Universe: {len(u)}")

    # 2) Recent delistings
    del_df = fetch_nasdaq_delistings()
    if not del_df.empty:
        frames.append(del_df)
        print(f"Delistings: {len(del_df)}")

    # 3) Active universe symbols we already know are active
    already = set()
    if frames:
        already = set(pd.concat(frames)["symbol"].dropna().astype(str).str.strip().tolist())

    # 4) OTC / Pink sheets from otcmarkets.com
    otc_df = fetch_otc_pink_sheets()
    if not otc_df.empty:
        otc_df = otc_df[~otc_df["symbol"].isin(already)]
        frames.append(otc_df)
        already.update(otc_df["symbol"].tolist())
        print(f"OTC/Pink: {len(otc_df)}")

    # 5) FINRA OTC scrape (very heuristic, low quality)
    finra_df = fetch_finra_otc()
    if not finra_df.empty:
        finra_df = finra_df[~finra_df["symbol"].isin(already)]
        frames.append(finra_df.head(5000))
        already.update(finra_df["symbol"].tolist())
        print(f"FINRA OTC: {len(finra_df)}")

    if not frames:
        print("No data collected.")
        return pd.DataFrame()

    master = pd.concat(frames, ignore_index=True)
    master["symbol"] = master["symbol"].astype(str).str.strip().str.upper()
    master = master[master["symbol"].ne("")]
    master = master.drop_duplicates(subset="symbol").reset_index(drop=True)

    # Add columns for downloaded status
    existing = load_existing_symbols(output_dir)
    master["downloaded"] = master["symbol"].isin(existing)
    master["has_price_csv"] = master["symbol"].isin(existing)

    # Final column order
    cols = ["symbol", "name", "exchange", "status", "source", "effective_date", "downloaded", "has_price_csv"]
    cols = [c for c in cols if c in master.columns]
    master = master[cols]

    master.to_csv(output_path, index=False)
    print(f"Master registry: {len(master)} symbols -> {output_path}")
    print(master.groupby("status").size().to_string())
    print(master.groupby("source").size().to_string())
    return master


def main():
    parser = argparse.ArgumentParser(description="Build master stock registry with delisted symbols")
    parser.add_argument("--output", default="stock_master.csv")
    parser.add_argument("--universe", default=UNIVERSE_CSV)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--yfinance-probe", action="store_true", help="Probe missing symbols via yfinance")
    args = parser.parse_args()

    master = build_master_csv(args.output, args.universe, args.output_dir)

    if args.yfinance_probe and not master.empty:
        candidates = set(master[master["status"] == "active"]["symbol"].tolist())
        # We don't want to probe already downloaded ones
        del_df = probe_yfinance_delisted(candidates, args.output_dir)
        if not del_df.empty:
            # Merge delisted status into master
            update = {r["symbol"]: r["status"] for _, r in del_df.iterrows()}
            master["status"] = master.apply(lambda r: update.get(r["symbol"], r["status"]), axis=1)
            master.to_csv(args.output, index=False)
            print(f"Updated master with {len(del_df)} yfinance-probed delistings")


if __name__ == "__main__":
    main()
