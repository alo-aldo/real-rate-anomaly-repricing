#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
w1_robustness.py — W1 robustness battery for the Gate-2 regime-rotation pilot.

Reuses regime_rotation_pilot.py (unmodified, imported) for data loading and
the per-signal rate-beta estimation (pre 1990-01..2021-12, HAC maxlags=6,
MIN_PRE_M=120 / MIN_POST_M=18). Baseline spec = pilot spec (2):
    post_mean ~ rate_beta + pub_year + is_tstat   (HC1)

Variants:
  A  winsorize dep var (1%/99%): post_mean, decay
  B  category FE: Cat.Economic, Cat.Data
  C  + mkt_beta (pre-2022 LS beta on Mkt-RF, HAC) + pre_vol; full spec adds
     Cat.Economic FE
  D  yearly post_mean: 2022 / 2023 / 2024
  E  alternative rate variables: dDGS10 (1990-2021), dDFII10 (2003-2021)
  F  pub_year <= 2004 subsample
  G  cluster SE by Cat.Economic
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import regime_rotation_pilot as rp  # pilot logic, unmodified

SUMMARY_CSV = "w1_summary.csv"
ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "external_cache"

P0 = pd.Period(rp.PRE_START, "M")
P1 = pd.Period(rp.PRE_END, "M")


# --------------------------------------------------------------- data pieces
def load_doc_full():
    doc = pd.read_csv("data/SignalDoc.csv")
    out = doc[["Acronym", "Year", "T-Stat", "Cat.Economic", "Cat.Data"]].rename(
        columns={"Acronym": "signal", "Year": "pub_year", "T-Stat": "is_tstat",
                 "Cat.Economic": "cat_econ", "Cat.Data": "cat_data"})
    out["signal"] = out["signal"].astype(str)
    out["pub_year"] = pd.to_numeric(out["pub_year"], errors="coerce")
    out["is_tstat"] = pd.to_numeric(out["is_tstat"], errors="coerce")
    return out.drop_duplicates("signal").set_index("signal")


def fred_monthly_change(series_id, start):
    cache = CACHE_DIR / f"clean_fred_{series_id}_monthly.csv"
    if cache.exists():
        r = pd.read_csv(cache)
        r["month"] = pd.PeriodIndex(r["month"], freq="M")
        d = pd.to_numeric(r.set_index("month")["delta"], errors="coerce")
        d = d.dropna()
        d.name = f"d_{series_id.lower()}"
        return d

    if "--download" not in sys.argv[1:]:
        raise FileNotFoundError(
            f"Missing {cache}. Run cache_external_data.py or rerun with --download.")

    from pandas_datareader import data as pdr
    s = pdr.DataReader(series_id, "fred", start=start)[series_id]
    try:
        m = s.resample("ME").last()
    except ValueError:
        m = s.resample("M").last()
    d = m.diff().dropna()
    d.index = d.index.to_period("M")
    d.name = f"d_{series_id.lower()}"
    return d


def load_mktrf():
    cache = CACHE_DIR / "clean_fama_french_mkt_rf_monthly.csv"
    if cache.exists():
        r = pd.read_csv(cache)
        r["month"] = pd.PeriodIndex(r["month"], freq="M")
        mkt = pd.to_numeric(r.set_index("month")["mkt_rf_decimal"],
                            errors="coerce").dropna()
        mkt.name = "Mkt-RF"
        return mkt

    if "--download" not in sys.argv[1:]:
        raise FileNotFoundError(
            f"Missing {cache}. Run cache_external_data.py or rerun with --download.")

    from pandas_datareader import data as pdr
    ff = pdr.DataReader("F-F_Research_Data_Factors", "famafrench",
                        start="1985-01-01")[0]
    mkt = ff["Mkt-RF"] / 100.0  # percent -> decimal, matches LS units
    mkt.index = pd.PeriodIndex(mkt.index, freq="M")
    return mkt


def hac_beta(y, x, min_n):
    """Slope of y on x (aligned, HAC maxlags=6) — mirrors pilot estimation."""
    xr = x.reindex(y.index).dropna()
    y2 = y.reindex(xr.index).dropna()
    xr = xr.reindex(y2.index)
    if len(y2) < min_n:
        return np.nan
    X = sm.add_constant(xr.values)
    fit = sm.OLS(y2.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    return fit.params[1]


def per_signal_extras(ls, mkt, universe):
    """pre-2022 market beta and pre-period vol for each signal in universe."""
    rows = {}
    for sig in universe:
        s = ls[sig].dropna()
        pre = s[(s.index >= P0) & (s.index <= P1)]
        rows[sig] = {
            "mkt_beta": hac_beta(pre, mkt, rp.MIN_PRE_M),
            "pre_vol": pre.std() if len(pre) > 1 else np.nan,
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def yearly_post_means(ls, universe):
    out = {}
    for year in (2022, 2023, 2024):
        lo, hi = pd.Period(f"{year}-01", "M"), pd.Period(f"{year}-12", "M")
        block = ls.loc[(ls.index >= lo) & (ls.index <= hi), universe]
        out[f"post_mean_{year}"] = block.mean()
        out[f"n_{year}"] = block.notna().sum()
    return pd.DataFrame(out)


def winsor(s, lo=0.01, hi=0.99):
    ql, qh = s.quantile([lo, hi])
    return s.clip(ql, qh)


# --------------------------------------------------------------- regression
RESULTS = []


def run_spec(df, label, ycol, xcols, fe_col=None, cluster_col=None,
             note="", detail=False):
    need = [ycol] + xcols + [c for c in (fe_col, cluster_col) if c]
    d = df[list(dict.fromkeys(need))].dropna()
    X = d[xcols].astype(float)
    extra = ""
    if fe_col:
        dum = pd.get_dummies(d[fe_col], prefix="fe", drop_first=True)
        X = pd.concat([X, dum.astype(float)], axis=1)
        extra = f"{d[fe_col].nunique()} categories"
    X = sm.add_constant(X)
    y = d[ycol].astype(float)
    if cluster_col:
        groups = d[cluster_col].astype("category").cat.codes.values
        fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
        extra = f"{d[cluster_col].nunique()} clusters"
    else:
        fit = sm.OLS(y, X).fit(cov_type="HC1")
    key = xcols[0]  # rate-beta variable is always listed first
    RESULTS.append({
        "variant": label, "N": int(fit.nobs),
        "rate_beta_coef": fit.params[key],
        "t": fit.tvalues[key], "p": fit.pvalues[key],
        "note": (note + (" | " if note and extra else "") + extra).strip(),
    })
    if detail:
        print(f"\n--- detail: {label} (N={int(fit.nobs)}) ---")
        for v in fit.params.index:
            if v.startswith("fe_"):
                continue
            print(f"  {v:>10s}: coef={fit.params[v]: .5f}  "
                  f"t={fit.tvalues[v]: .3f}  p={fit.pvalues[v]:.4f}")
    return fit


def main():
    ls = rp.load_ls_returns()
    d2 = rp.load_rates()
    st = rp.per_signal_stats(ls, d2)          # pilot universe + rate_beta
    doc = load_doc_full()
    df = st.join(doc, how="left")
    uni = df.index.tolist()
    print(f"[universe] {len(uni)} signals (pilot filters)")
    print(f"[missing ] is_tstat: {int(df['is_tstat'].isna().sum())}, "
          f"pub_year: {int(df['pub_year'].isna().sum())}, "
          f"cat_econ: {int(df['cat_econ'].isna().sum())}")

    mkt = load_mktrf()
    df = df.join(per_signal_extras(ls, mkt, uni))
    df = df.join(yearly_post_means(ls, uni))

    d10 = fred_monthly_change("DGS10", "1985-01-01")
    dr10 = fred_monthly_change("DFII10", "2003-01-01")
    st10 = rp.per_signal_stats(ls, d10)["rate_beta"].rename("rate_beta_dgs10")
    str10 = rp.per_signal_stats(ls, dr10)["rate_beta"].rename("rate_beta_dfii10")
    df = df.join(st10).join(str10)

    df["post_mean_w"] = winsor(df["post_mean"])
    df["decay_w"] = winsor(df["decay"])

    ctrl = ["pub_year", "is_tstat"]
    base_x = ["rate_beta"] + ctrl

    run_spec(df, "base: pilot spec(2) replication", "post_mean", base_x)
    run_spec(df, "A1 winsorized post_mean", "post_mean_w", base_x)
    run_spec(df, "A2 winsorized decay", "decay_w", base_x)
    run_spec(df, "B1 + Cat.Economic FE", "post_mean", base_x, fe_col="cat_econ")
    run_spec(df, "B2 + Cat.Data FE", "post_mean", base_x, fe_col="cat_data")
    run_spec(df, "C1 + mkt_beta + pre_vol", "post_mean",
             base_x + ["mkt_beta", "pre_vol"], detail=True)
    run_spec(df, "C2 full: + mkt_beta + pre_vol + Cat.Economic FE",
             "post_mean", base_x + ["mkt_beta", "pre_vol"],
             fe_col="cat_econ", detail=True)
    for yr in (2022, 2023, 2024):
        run_spec(df, f"D post_mean {yr} only", f"post_mean_{yr}", base_x)
    run_spec(df, "E1 rate var = dDGS10 (1990-2021)", "post_mean",
             ["rate_beta_dgs10"] + ctrl)
    run_spec(df, "E2 rate var = dDFII10 (2003-2021)", "post_mean",
             ["rate_beta_dfii10"] + ctrl)
    run_spec(df[df["pub_year"] <= 2004], "F pub_year <= 2004", "post_mean",
             base_x)
    run_spec(df, "G cluster SE (Cat.Economic)", "post_mean", base_x,
             cluster_col="cat_econ")

    res = pd.DataFrame(RESULTS)
    res["rate_beta_coef"] = res["rate_beta_coef"].round(4)
    res["t"] = res["t"].round(2)
    res["p"] = res["p"].round(4)
    print("\n================  W1 SUMMARY  ================")
    print(res.to_string(index=False))
    res.to_csv(SUMMARY_CSV, index=False)
    print(f"\n[saved] {SUMMARY_CSV}")

    # anomalies / diagnostics
    print("\n--- diagnostics ---")
    for yr in (2022, 2023, 2024):
        short = (df[f"n_{yr}"] < 12).sum()
        print(f"  {yr}: signals with <12 months = {int(short)}")
    print(f"  dDGS10 universe: {int(df['rate_beta_dgs10'].notna().sum())}, "
          f"dDFII10 universe: {int(df['rate_beta_dfii10'].notna().sum())}")
    print(f"  corr(rate_beta, mkt_beta) = "
          f"{df[['rate_beta', 'mkt_beta']].corr().iloc[0, 1]:.3f}")
    print(f"  corr(rate_beta, dDGS10 beta) = "
          f"{df[['rate_beta', 'rate_beta_dgs10']].corr().iloc[0, 1]:.3f}")
    df.to_csv("w1_signal_level.csv")
    print("[saved] w1_signal_level.csv")


if __name__ == "__main__":
    main()
