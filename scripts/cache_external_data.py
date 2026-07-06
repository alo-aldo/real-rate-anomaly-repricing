#!/usr/bin/env python3
"""Cache external time series used by the FRL reproducibility audit.

This script does not modify the analysis scripts or existing result files.
It freezes the external inputs that W1/W1-X depend on and records hashes.
"""
from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandas_datareader import data as pdr


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "external_cache"
MANIFEST = CACHE / "manifest.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def month_end_last(s: pd.Series) -> pd.Series:
    try:
        out = s.resample("ME").last()
    except ValueError:
        out = s.resample("M").last()
    out.index = out.index.to_period("M")
    return out


def date_range_str(index: pd.Index) -> str:
    if len(index) == 0:
        return ""
    return f"{index.min()}..{index.max()}"


def write_fred(series: str, start: str, rows: list[dict[str, object]]) -> pd.DataFrame:
    raw = pdr.DataReader(series, "fred", start=start)[series].dropna()
    raw_df = raw.rename(series).reset_index()
    raw_df.columns = ["date", series]
    raw_path = CACHE / f"raw_fred_{series}.csv"
    raw_df.to_csv(raw_path, index=False)

    monthly = month_end_last(raw).rename("level")
    clean = pd.DataFrame({
        "month": monthly.index.astype(str),
        "level": monthly.values,
        "delta": monthly.diff().values,
    })
    clean_path = CACHE / f"clean_fred_{series}_monthly.csv"
    clean.to_csv(clean_path, index=False)

    rows.append({
        "series_name": series,
        "source": f"FRED via pandas_datareader, start={start}",
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_file_path": str(raw_path.relative_to(ROOT)),
        "cleaned_file_path": str(clean_path.relative_to(ROOT)),
        "date_range": date_range_str(raw.index),
        "frequency": "daily raw; monthly last available cleaned",
        "n_observations": int(len(raw)),
        "raw_sha256": sha256(raw_path),
        "cleaned_sha256": sha256(clean_path),
        "notes": "Rates are percentage points. Cleaned delta is monthly change in percentage points.",
    })
    return clean.set_index(pd.PeriodIndex(clean["month"], freq="M"))


def cache_local_dgs2(rows: list[dict[str, object]]) -> pd.DataFrame:
    src = ROOT / "data" / "DGS2.csv"
    if not src.exists():
        return write_fred("DGS2", "1976-01-01", rows)

    raw = pd.read_csv(src)
    raw_path = CACHE / "raw_fred_DGS2_from_local.csv"
    raw.to_csv(raw_path, index=False)
    cols = {c.upper(): c for c in raw.columns}
    date_col = cols.get("DATE") or cols.get("OBSERVATION_DATE") or raw.columns[0]
    val_col = cols.get("DGS2") or raw.columns[-1]
    s = pd.to_numeric(raw.set_index(pd.to_datetime(raw[date_col], errors="coerce"))[val_col],
                      errors="coerce").dropna()
    monthly = month_end_last(s).rename("level")
    clean = pd.DataFrame({
        "month": monthly.index.astype(str),
        "level": monthly.values,
        "delta": monthly.diff().values,
    })
    clean_path = CACHE / "clean_fred_DGS2_monthly.csv"
    clean.to_csv(clean_path, index=False)
    rows.append({
        "series_name": "DGS2",
        "source": "local data/DGS2.csv copied into cache",
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_file_path": str(raw_path.relative_to(ROOT)),
        "cleaned_file_path": str(clean_path.relative_to(ROOT)),
        "date_range": date_range_str(s.index),
        "frequency": "daily raw; monthly last available cleaned",
        "n_observations": int(len(s)),
        "raw_sha256": sha256(raw_path),
        "cleaned_sha256": sha256(clean_path),
        "notes": "This is the exact local FRED CSV used by regime_rotation_pilot.py.",
    })
    return clean.set_index(pd.PeriodIndex(clean["month"], freq="M"))


def cache_fama_french(rows: list[dict[str, object]]) -> pd.DataFrame:
    ff = pdr.DataReader("F-F_Research_Data_Factors", "famafrench",
                        start="1985-01-01")[0]
    raw = ff.copy()
    raw.index = pd.PeriodIndex(raw.index, freq="M").astype(str)
    raw.index.name = "month"
    raw_path = CACHE / "raw_fama_french_research_factors_monthly.csv"
    raw.to_csv(raw_path)

    clean = pd.DataFrame({
        "month": raw.index,
        "mkt_rf_percent": raw["Mkt-RF"].astype(float).values,
        "mkt_rf_decimal": (raw["Mkt-RF"].astype(float) / 100.0).values,
    })
    clean_path = CACHE / "clean_fama_french_mkt_rf_monthly.csv"
    clean.to_csv(clean_path, index=False)
    rows.append({
        "series_name": "Mkt-RF",
        "source": "Kenneth French data library via pandas_datareader famafrench",
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_file_path": str(raw_path.relative_to(ROOT)),
        "cleaned_file_path": str(clean_path.relative_to(ROOT)),
        "date_range": date_range_str(pd.PeriodIndex(clean["month"], freq="M")),
        "frequency": "monthly",
        "n_observations": int(len(clean)),
        "raw_sha256": sha256(raw_path),
        "cleaned_sha256": sha256(clean_path),
        "notes": "Raw Mkt-RF is percent. Cleaned decimal divides by 100 to match LS returns.",
    })
    return clean.set_index(pd.PeriodIndex(clean["month"], freq="M"))


def cache_bei(dgs10: pd.DataFrame, dfii10: pd.DataFrame,
              rows: list[dict[str, object]]) -> None:
    left = dgs10[["level"]].rename(columns={"level": "DGS10"})
    right = dfii10[["level"]].rename(columns={"level": "DFII10"})
    joined = left.join(right, how="inner")
    joined["BEI"] = joined["DGS10"] - joined["DFII10"]
    joined["dDGS10"] = joined["DGS10"].diff()
    joined["dDFII10"] = joined["DFII10"].diff()
    joined["dBEI"] = joined["BEI"].diff()
    out = joined.reset_index().rename(columns={"index": "month"})
    out["month"] = out["month"].astype(str)
    clean_path = CACHE / "clean_bei_dgs10_minus_dfii10_monthly.csv"
    out.to_csv(clean_path, index=False)

    rows.append({
        "series_name": "BEI",
        "source": "derived as DGS10 - DFII10 from cached FRED monthly levels",
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_file_path": "data/external_cache/raw_fred_DGS10.csv + data/external_cache/raw_fred_DFII10.csv",
        "cleaned_file_path": str(clean_path.relative_to(ROOT)),
        "date_range": date_range_str(joined.index),
        "frequency": "monthly derived",
        "n_observations": int(len(joined)),
        "raw_sha256": "",
        "cleaned_sha256": sha256(clean_path),
        "notes": "BEI is exact monthly DGS10 minus DFII10 on aligned month-end dates.",
    })


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    cache_local_dgs2(rows)
    dgs10 = write_fred("DGS10", "1985-01-01", rows)
    dfii10 = write_fred("DFII10", "2002-06-01", rows)
    cache_fama_french(rows)
    cache_bei(dgs10, dfii10, rows)

    fieldnames = [
        "series_name", "source", "retrieval_timestamp_utc", "raw_file_path",
        "cleaned_file_path", "date_range", "frequency", "n_observations",
        "raw_sha256", "cleaned_sha256", "notes",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[saved] {MANIFEST.relative_to(ROOT)}")
    for row in rows:
        print(f"[cached] {row['series_name']}: {row['date_range']} n={row['n_observations']}")


if __name__ == "__main__":
    main()
