"""
Build a comprehensive master stock registry CSV with as much metadata as possible.
Sources:
  - universe.csv: active universe from NASDAQ Trader
  - FinanceDataReader: NASDAQ/NYSE/AMEX listings with industry
  - investpy: US stock names/ISINs
  - code-temp-old/20260105.csv: S&P 500 snapshot (sector, CIK, etc.)
  - NASDAQ deltas: recent delistings
  - yfinance: probe missing symbols for delisted/inactive status (optional, slow)
"""
import os
import time
from pathlib import Path

import pandas as pd
import yfinance as yf
from download_yfinance import (
    DELTAS_URL,
    UNIVERSE_CSV,
    DEFAULT_OUTPUT_DIR,
    _fetch,
    load_existing_symbols,
)


def build_master_csv(output_path: str = "stock_master.csv", universe_path: str = UNIVERSE_CSV, output_dir: str = DEFAULT_OUTPUT_DIR, do_yfinance_probe: bool = False):
    print("Building master stock registry...")
    Path(output_dir).mkdir(exist_ok=True)
    existing = load_existing_symbols(output_dir)
    print(f"Existing price files: {len(existing)}")

    # --- Active universe from NASDAQ Trader ---
    if not Path(universe_path).exists():
        print(f"Warning: {universe_path} not found.")
        return

    u = pd.read_csv(universe_path)
    u["symbol"] = u["symbol"].astype(str).str.strip().str.upper()
    u = u[u["symbol"].ne("")].copy()
    u["status"] = "active"
    u = u.rename(columns={"security_name": "name"})
    print(f"Universe active: {len(u)}")

    # --- Enrich with S&P 500 metadata (sector, CIK, etc.) ---
    sp500_path = "code-temp-old/20260105.csv"
    if Path(sp500_path).exists():
        sp = pd.read_csv(sp500_path)
        sp.columns = [c.strip() for c in sp.columns]
        sp["symbol"] = sp["Symbol"].astype(str).str.strip().str.upper()
        meta_cols = {}
        if "Security" in sp.columns:
            meta_cols["Security"] = "sp500_name"
        if "GICS Sector" in sp.columns:
            meta_cols["GICS Sector"] = "sector"
        if "GICS Sub-Industry" in sp.columns:
            meta_cols["GICS Sub-Industry"] = "industry_gics"
        if "Headquarters Location" in sp.columns:
            meta_cols["Headquarters Location"] = "headquarters"
        if "CIK" in sp.columns:
            meta_cols["CIK"] = "cik"
        if "Founded" in sp.columns:
            meta_cols["Founded"] = "founded"
        sp = sp[["symbol"] + list(meta_cols.keys())].rename(columns=meta_cols)
        u = u.merge(sp, on="symbol", how="left")
        print(f"  Enriched with S&P 500 metadata: {u['sector'].notna().sum()} rows with sector")

    # --- Enrich with FinanceDataReader (IndustryCode/Industry) ---
    fdr_path = "/tmp/fdr_us_stocks.csv"
    if Path(fdr_path).exists():
        fdr = pd.read_csv(fdr_path)
        fdr = fdr.rename(columns={"name": "fdr_name", "industry": "industry_fdr"})
        fdr["symbol"] = fdr["symbol"].astype(str).str.strip().str.upper()
        before = len(u)
        u = u.merge(fdr[["symbol", "fdr_name", "industry_code", "industry_fdr"]], on="symbol", how="left")
        u["name"] = u["name"].fillna(u["fdr_name"])
        u = u.drop(columns=["fdr_name"], errors="ignore")
        print(f"  Enriched with FinanceDataReader industry: {u['industry_fdr'].notna().sum()} rows with industry")

    # --- Enrich with investpy ---
    investpy_path = "/tmp/us_stocks_investpy.csv"
    if Path(investpy_path).exists():
        inv = pd.read_csv(investpy_path)
        inv = inv.rename(columns={"name": "investpy_name", "full_name": "investpy_full_name", "isin": "isin"})
        inv["symbol"] = inv["symbol"].astype(str).str.strip().str.upper()
        u = u.merge(inv[["symbol", "investpy_name", "investpy_full_name", "isin"]], on="symbol", how="left")
        u["name"] = u["name"].fillna(u["investpy_name"]).fillna(u["investpy_full_name"])
        u = u.drop(columns=["investpy_name", "investpy_full_name"], errors="ignore")
        print(f"  Enriched with investpy ISIN: {u['isin'].notna().sum()} rows with ISIN")

    # --- Download status ---
    u["has_price_csv"] = u["symbol"].isin(existing)
    u["downloaded_rows"] = 0
    for sym in u.loc[u["has_price_csv"], "symbol"]:
        try:
            p = Path(output_dir) / f"{sym}.csv"
            if p.exists():
                with open(p) as f:
                    rows = sum(1 for _ in f) - 1
                u.loc[u["symbol"] == sym, "downloaded_rows"] = rows
        except Exception:
            pass

    # --- Recent delistings from NASDAQ deltas ---
    del_rows = []
    text = _fetch(DELTAS_URL)
    if text:
        try:
            import io
            df = pd.read_csv(io.StringIO(text), sep="|", dtype=str, skipfooter=1, engine="python").fillna("")
            if not df.empty:
                df.columns = [c.strip() for c in df.columns]
                action_col = next((c for c in df.columns if "Action" in c), None)
                if action_col:
                    del_df = df[df[action_col].str.upper() == "DELETE"].copy()
                    del_df["symbol"] = del_df.get("Symbol", pd.Series(dtype=str)).fillna("").astype(str).str.strip().str.upper()
                    del_df = del_df[del_df["symbol"].ne("")]
                    for _, r in del_df.iterrows():
                        p = Path(output_dir) / f"{r['symbol']}.csv"
                        del_rows.append({
                            "symbol": r["symbol"],
                            "name": r.get("Company Name", ""),
                            "exchange": r.get("Primary Listing Market", ""),
                            "status": "delisted",
                            "source": "nasdaq_deltas",
                            "effective_date": r.get("Effective Date", ""),
                            "security_type": "",
                            "has_price_csv": p.exists(),
                            "downloaded_rows": sum(1 for _ in open(p)) - 1 if p.exists() else 0,
                        })
        except Exception as e:
            print(f"Warning: deltas parse error: {e}")

    del_df = pd.DataFrame(del_rows)
    print(f"Recent delistings: {len(del_df)}")

    # --- yfinance probing of known missing symbols to find delisted/inactive ---
    inactive_df = pd.DataFrame()
    if do_yfinance_probe:
        missing = sorted(set(u.loc[~u["has_price_csv"], "symbol"].tolist()))
        inactive_rows = []
        if missing:
            print(f"Probing {len(missing)} missing symbols for delisted/inactive status...")
            for i, sym in enumerate(missing, 1):
                try:
                    t = yf.Ticker(sym)
                    df = t.history(period="5d", interval="1d")
                    if df.empty:
                        inactive_rows.append({"symbol": sym, "status": "delisted_or_inactive", "source": "yfinance_probe"})
                except Exception:
                    pass
                if i % 500 == 0:
                    print(f"  probed {i}/{len(missing)}")
                time.sleep(0.02)

            inactive_df = pd.DataFrame(inactive_rows).drop_duplicates(subset="symbol")
            print(f"Identified {len(inactive_df)} missing/inactive symbols via yfinance probe")

    # --- Combine ---
    final_cols = ["symbol", "name", "exchange", "status", "source", "security_type", "sector", "industry_gics", "industry_fdr", "industry_code", "headquarters", "cik", "founded", "isin", "has_price_csv", "downloaded_rows", "effective_date"]

    master = u.copy()

    # Add delisted from NASDAQ
    if not del_df.empty:
        already = set(master["symbol"])
        del_add = del_df[~del_df["symbol"].isin(already)].copy()
        for c in final_cols:
            if c not in del_add.columns:
                del_add[c] = ""
        master = pd.concat([master, del_add[final_cols]], ignore_index=True)

    # Add inactive from yfinance probe
    if not inactive_df.empty:
        already = set(master["symbol"])
        inact_add = inactive_df[~inactive_df["symbol"].isin(already)].copy()
        for c in final_cols:
            if c not in inact_add.columns:
                inact_add[c] = ""
        name_map = dict(zip(master["symbol"], master["name"]))
        inact_add["name"] = inact_add["symbol"].map(name_map).fillna("")
        inact_add["exchange"] = inact_add["symbol"].map(dict(zip(master["symbol"], master["exchange"]))).fillna("")
        master = pd.concat([master, inact_add[final_cols]], ignore_index=True)

    # deduplicate
    master["symbol"] = master["symbol"].astype(str).str.strip().str.upper()
    master = master[master["symbol"].ne("")]
    master = master.drop_duplicates(subset="symbol", keep="first").reset_index(drop=True)

    # Ensure final columns exist
    for c in final_cols:
        if c not in master.columns:
            master[c] = ""
    master = master[final_cols]

    master.to_csv(output_path, index=False)
    print(f"\nMaster registry: {len(master)} symbols -> {output_path}")
    print("By status:")
    print(master.groupby("status").size().to_string())
    print("By source:")
    print(master.groupby("source").size().to_string())
    print(f"Active with sector info: {master[master['status']=='active']['sector'].notna().sum()}")
    print(f"With CIK: {master['cik'].notna().sum()}")
    print(f"With ISIN: {master['isin'].notna().sum()}")
    print(f"With industry_fdr: {master['industry_fdr'].notna().sum()}")
    print(f"With price CSV: {master['has_price_csv'].sum()}")
    return master


if __name__ == "__main__":
    build_master_csv(do_yfinance_probe=False)
