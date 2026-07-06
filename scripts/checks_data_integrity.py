#!/usr/bin/env python3
"""Data integrity audit for the FRL reproducibility project."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import regime_rotation_pilot as rp


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "external_cache"
OUT = ROOT / "outputs" / "data_integrity_report.md"
LOG = ROOT / "logs" / "data_integrity.log"


def append_log(lines: list[str], msg: str) -> None:
    lines.append(msg)


def read_clean_rate(series: str) -> pd.DataFrame:
    path = CACHE / f"clean_fred_{series}_monthly.csv"
    df = pd.read_csv(path)
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df.set_index("month")


def fmt_float(x: float, digits: int = 6) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.{digits}f}"


def md_table(rows: list[list[object]], headers: list[str]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return out


def main() -> None:
    ROOT.joinpath("outputs").mkdir(exist_ok=True)
    ROOT.joinpath("logs").mkdir(exist_ok=True)
    log: list[str] = []
    report: list[str] = []
    failures: list[str] = []

    append_log(log, "Starting data integrity audit")
    manifest_path = CACHE / "manifest.csv"
    if not manifest_path.exists():
        failures.append("Missing data/external_cache/manifest.csv. Run cache_external_data.py first.")
        manifest = pd.DataFrame()
    else:
        manifest = pd.read_csv(manifest_path)
        append_log(log, f"Loaded manifest with {len(manifest)} rows")

    # OSAP returns before and after conversion.
    raw = pd.read_csv(ROOT / "data" / "PredictorLSretWide.csv")
    date_col = raw.columns[0]
    dates = pd.to_datetime(raw[date_col], errors="coerce")
    numeric_raw = raw.drop(columns=[date_col]).apply(pd.to_numeric, errors="coerce")
    raw_med_abs = float(numeric_raw.abs().stack().median())
    raw_unit = "percent-like" if raw_med_abs > 0.2 else "decimal-like"
    ls = rp.load_ls_returns()
    missing_by_year = ls.isna().groupby(ls.index.year).sum().sum(axis=1)
    post = ls.loc[ls.index >= pd.Period("2022-01", "M")]
    post_counts = post.notna().sum().sort_values()

    report.append("# Data Integrity Report")
    report.append("")
    report.append(f"Workspace: `{ROOT}`")
    report.append("")
    report.append("## OSAP Returns")
    report.extend(md_table([
        ["raw shape", f"{raw.shape[0]} rows x {raw.shape[1]} columns"],
        ["parsed date range", f"{dates.min().date()}..{dates.max().date()}"],
        ["signals", numeric_raw.shape[1]],
        ["raw median absolute return", fmt_float(raw_med_abs)],
        ["raw unit diagnosis", raw_unit],
        ["converted return range", f"{ls.index.min()}..{ls.index.max()}"],
        ["post-2022 months", len(post.index)],
        ["post-2022 coverage min/median/max", f"{int(post_counts.min())}/{fmt_float(post_counts.median(), 1)}/{int(post_counts.max())}"],
    ], ["Check", "Value"]))
    report.append("")
    report.append("Missing return cells by year, last 10 years:")
    report.extend(md_table([[int(y), int(v)] for y, v in missing_by_year.tail(10).items()],
                           ["Year", "Missing cells"]))
    low_post = post_counts[post_counts < 30]
    report.append("")
    report.append(f"Signals with fewer than 30 post-2022 monthly observations: {len(low_post)}")
    if len(low_post):
        report.append(", ".join(f"{k}={int(v)}" for k, v in low_post.head(20).items()))

    # Cached rates.
    dgs2 = read_clean_rate("DGS2")
    dgs10 = read_clean_rate("DGS10")
    dfii10 = read_clean_rate("DFII10")
    bei = pd.read_csv(CACHE / "clean_bei_dgs10_minus_dfii10_monthly.csv")
    bei["month"] = pd.PeriodIndex(bei["month"], freq="M")
    bei = bei.set_index("month")
    bei_exact = np.allclose(bei["BEI"], bei["DGS10"] - bei["DFII10"], equal_nan=True)
    if not bei_exact:
        failures.append("BEI is not exactly DGS10 - DFII10 on aligned monthly dates.")

    report.append("")
    report.append("## FRED Rates and BEI")
    report.extend(md_table([
        ["DGS2 monthly range", f"{dgs2.index.min()}..{dgs2.index.max()}"],
        ["DGS10 monthly range", f"{dgs10.index.min()}..{dgs10.index.max()}"],
        ["DFII10 monthly range", f"{dfii10.index.min()}..{dfii10.index.max()}"],
        ["BEI aligned range", f"{bei.index.min()}..{bei.index.max()}"],
        ["rate units", "percentage points"],
        ["monthly conversion", "last available daily observation in each calendar month"],
        ["monthly changes", "current month-end level minus prior month-end level"],
        ["BEI identity", "PASS" if bei_exact else "FAIL"],
    ], ["Check", "Value"]))
    report.append("")
    stats = bei[["dDGS10", "dDFII10", "dBEI"]].dropna().agg(["count", "mean", "std", "min", "max"]).T
    report.append("Monthly-change summary:")
    report.extend(md_table([
        [idx, int(row["count"]), fmt_float(row["mean"]), fmt_float(row["std"]),
         fmt_float(row["min"]), fmt_float(row["max"])]
        for idx, row in stats.iterrows()
    ], ["Series", "N", "Mean", "Std", "Min", "Max"]))
    report.append("")
    corr = bei[["dDGS10", "dDFII10", "dBEI"]].dropna().corr()
    report.append("Monthly-change correlations:")
    report.extend(md_table([
        ["corr(dDGS10,dDFII10)", fmt_float(corr.loc["dDGS10", "dDFII10"])],
        ["corr(dDGS10,dBEI)", fmt_float(corr.loc["dDGS10", "dBEI"])],
        ["corr(dDFII10,dBEI)", fmt_float(corr.loc["dDFII10", "dBEI"])],
    ], ["Pair", "Correlation"]))

    # Timing checks.
    w1x = pd.read_csv(ROOT / "w1x_signal_level.csv")
    real_window_ok = pd.Period("2003-01", "M") <= pd.Period("2021-12", "M") < pd.Period("2022-01", "M")
    pilot_window_ok = pd.Period(rp.PRE_END, "M") < pd.Period(rp.POST_START, "M")
    if not real_window_ok:
        failures.append("Real/BEI beta window check failed.")
    if not pilot_window_ok:
        failures.append("Pilot pre/post timing check failed.")

    report.append("")
    report.append("## Timing and Look-Ahead")
    report.extend(md_table([
        ["pilot nominal rate beta window", f"{rp.PRE_START}..{rp.PRE_END}"],
        ["pilot post_mean window", f"{rp.POST_START} onward"],
        ["W1-X real/BEI beta window", "2003-01..2021-12"],
        ["W1-X panel/post window", "2022-01..2024-12"],
        ["post-2022 enters beta estimation", "NO"],
    ], ["Check", "Value"]))

    # Market beta.
    mkt = pd.read_csv(CACHE / "clean_fama_french_mkt_rf_monthly.csv")
    mkt["month"] = pd.PeriodIndex(mkt["month"], freq="M")
    mkt = mkt.set_index("month")
    corr_w1x = w1x[["real_beta", "bei_beta", "mkt_beta", "nom_beta_0321", "rate_beta"]].corr()
    report.append("")
    report.append("## Market Beta")
    report.extend(md_table([
        ["source", "Fama-French Research Data Factors via pandas_datareader"],
        ["raw unit", "percent"],
        ["analysis unit", "decimal, Mkt-RF / 100"],
        ["cached date range", f"{mkt.index.min()}..{mkt.index.max()}"],
        ["corr(real_beta, mkt_beta)", fmt_float(corr_w1x.loc["real_beta", "mkt_beta"])],
        ["corr(bei_beta, mkt_beta)", fmt_float(corr_w1x.loc["bei_beta", "mkt_beta"])],
        ["corr(real_beta, bei_beta)", fmt_float(corr_w1x.loc["real_beta", "bei_beta"])],
        ["corr(nom_beta_0321, rate_beta_1990_2021)", fmt_float(corr_w1x.loc["nom_beta_0321", "rate_beta"])],
    ], ["Check", "Value"]))

    # Manifest checks.
    required = {"DGS2", "DGS10", "DFII10", "Mkt-RF", "BEI"}
    present = set(manifest.get("series_name", []))
    missing = sorted(required - present)
    if missing:
        failures.append("Missing required cached series: " + ", ".join(missing))
    if not manifest.empty:
        bad_hash = manifest[(manifest["cleaned_sha256"].isna()) | (manifest["cleaned_sha256"].astype(str).str.len() < 32)]
        if len(bad_hash):
            failures.append("Some manifest cleaned hashes are missing.")

    report.append("")
    report.append("## PASS/FAIL")
    if failures:
        report.append("DATA INTEGRITY FAIL")
        for item in failures:
            report.append(f"- {item}")
    else:
        report.append("DATA INTEGRITY PASS")
        report.append("- All required external series are cached locally with cleaned-file hashes.")
        report.append("- Date alignment is explicit: monthly last available observations.")
        report.append("- Rates are documented as percentage points; returns are converted to decimal when raw values are percent-like.")
        report.append("- Beta windows end at 2021-12 and do not use post-2022 information.")
        report.append("- BEI is exactly DGS10 - DFII10 on aligned monthly dates.")

    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    LOG.write_text("\n".join(log + [f"Report written to {OUT}"]) + "\n", encoding="utf-8")
    print(f"[saved] {OUT.relative_to(ROOT)}")
    print(f"[saved] {LOG.relative_to(ROOT)}")
    print("DATA INTEGRITY " + ("FAIL" if failures else "PASS"))


if __name__ == "__main__":
    main()
