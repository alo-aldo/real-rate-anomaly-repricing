#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
w1x_decomposition.py — W1-X nominal vs real rate decomposition test.

Reuses (unmodified, via import):
  regime_rotation_pilot.py  loaders, pilot universe/filters, HAC estimation
  w1_robustness.py          SignalDoc loader, mkt_beta/pre_vol (1990-2021),
                            FRED monthly-change helper, yearly post means

New estimation window 2003-01..2021-12 (DFII10 starts 2003):
  bivariate : LSret ~ dDFII10 + dBEI   -> real_beta, bei_beta
  univariate: LSret ~ dDGS10           -> nom_beta_0321
  (BEI = DGS10 - DFII10, month-end levels, monthly differences)

GATE 0: if |corr(real_beta, mkt_beta)| > 0.6 -> stop after correlation table.

Cross-sections (HC1 unless noted), dep = post_mean unless noted:
  X1: real_beta + bei_beta + pub_year + is_tstat
  X2: X1 + mkt_beta + pre_vol                      (main gate)
  X3: X2 + Cat.Economic FE
  X4: X2, cluster SE by Cat.Economic
  X5: nom_beta_0321 + pub_year + is_tstat          (window-fragility check)
  X6: X2 on post_mean_2022 / 2023 / 2024

Panel mechanism test (post 2022-01..2024-12):
  LS_ret_it = signal FE + month FE + b*(real_beta_i x dDFII10_t) + e
  SE clustered by month. Prediction: b > 0.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import regime_rotation_pilot as rp
import w1_robustness as w1

W0 = pd.Period("2003-01", "M")
W1P = pd.Period("2021-12", "M")
MIN_N = 120                      # same minimum used throughout W1
GATE0_LIMIT = 0.6

POST0 = pd.Period("2022-01", "M")
POST1 = pd.Period("2024-12", "M")

SUMMARY_CSV = "w1x_summary.csv"
SIGNAL_CSV = "w1x_signal_level.csv"
ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "external_cache"


def load_monthly_rate_level(series_id, start):
    cache = CACHE_DIR / f"clean_fred_{series_id}_monthly.csv"
    if cache.exists():
        r = pd.read_csv(cache)
        r["month"] = pd.PeriodIndex(r["month"], freq="M")
        s = pd.to_numeric(r.set_index("month")["level"], errors="coerce")
        s.name = series_id
        return s.dropna()

    if "--download" not in sys.argv[1:]:
        raise FileNotFoundError(
            f"Missing {cache}. Run cache_external_data.py or rerun with --download.")

    from pandas_datareader import data as pdr
    s = pdr.DataReader(series_id, "fred", start=start)[series_id]
    try:
        m = s.resample("ME").last()
    except ValueError:
        m = s.resample("M").last()
    m.index = m.index.to_period("M")
    return m.dropna()


def window_betas(ls, xdf, universe):
    """Per-signal HAC(6) betas of LS returns on columns of xdf, 2003-2021."""
    xcols = list(xdf.columns)
    rows = {}
    for sig in universe:
        s = ls[sig].dropna()
        pre = s[(s.index >= W0) & (s.index <= W1P)].rename("ret")
        j = pd.concat([pre, xdf], axis=1, join="inner").dropna()
        if len(j) < MIN_N:
            continue
        X = sm.add_constant(j[xcols].astype(float))
        fit = sm.OLS(j["ret"].astype(float), X).fit(
            cov_type="HAC", cov_kwds={"maxlags": 6})
        r = {"n_win": len(j)}
        for c in xcols:
            r[f"b_{c}"] = fit.params[c]
            r[f"t_{c}"] = fit.tvalues[c]
        rows[sig] = r
    return pd.DataFrame.from_dict(rows, orient="index")


RESULTS = []


def run_spec(df, label, ycol, xcols, key, fe_col=None, cluster_col=None,
             detail=False):
    need = [ycol] + xcols + [c for c in (fe_col, cluster_col) if c]
    d = df[list(dict.fromkeys(need))].dropna()
    X = d[xcols].astype(float)
    extra = ""
    if fe_col:
        X = pd.concat([X, pd.get_dummies(d[fe_col], prefix="fe",
                                         drop_first=True).astype(float)],
                      axis=1)
        extra = f"{d[fe_col].nunique()} categories"
    X = sm.add_constant(X)
    y = d[ycol].astype(float)
    if cluster_col:
        g = d[cluster_col].astype("category").cat.codes.values
        fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": g})
        extra = f"{d[cluster_col].nunique()} clusters"
    else:
        fit = sm.OLS(y, X).fit(cov_type="HC1")
    RESULTS.append({
        "variant": label, "N": int(fit.nobs), "key_var": key,
        "coef": fit.params[key], "t": fit.tvalues[key],
        "p": fit.pvalues[key], "note": extra,
    })
    if detail:
        print(f"\n--- detail: {label} (N={int(fit.nobs)}) ---")
        for v in fit.params.index:
            if v.startswith("fe_"):
                continue
            print(f"  {v:>14s}: coef={fit.params[v]: .5f}  "
                  f"t={fit.tvalues[v]: .3f}  p={fit.pvalues[v]:.4f}")
    return fit


def panel_test(ls, real_beta, d_real):
    """Signal FE + month FE panel with real_beta x dDFII10 interaction."""
    sigs = real_beta.dropna().index
    post = ls.loc[(ls.index >= POST0) & (ls.index <= POST1), sigs]
    long = post.stack().rename("ret").reset_index()
    long.columns = ["month", "signal", "ret"]
    long["rb"] = long["signal"].map(real_beta)
    long["dr"] = long["month"].map(d_real)
    long = long.dropna(subset=["ret", "rb", "dr"])
    long["inter"] = long["rb"] * long["dr"]

    X = pd.concat([
        long[["inter"]].astype(float),
        pd.get_dummies(long["signal"], prefix="s", drop_first=True),
        pd.get_dummies(long["month"].astype(str), prefix="m", drop_first=True),
    ], axis=1).astype(float)
    X = sm.add_constant(X)
    g = long["month"].astype(str).astype("category").cat.codes.values
    fit = sm.OLS(long["ret"].astype(float), X).fit(
        cov_type="cluster", cov_kwds={"groups": g})
    return fit, long


def main():
    ls = rp.load_ls_returns()
    d2 = rp.load_rates()
    st = rp.per_signal_stats(ls, d2)   # pilot universe, rate_beta 1990-2021
    uni = st.index.tolist()
    doc = w1.load_doc_full()
    mkt = w1.load_mktrf()
    df = st.join(doc, how="left")
    df = df.join(w1.per_signal_extras(ls, mkt, uni))
    df = df.join(w1.yearly_post_means(ls, uni))

    # rate series, month-end levels -> monthly differences
    m10 = load_monthly_rate_level("DGS10", "2002-06-01")
    mr = load_monthly_rate_level("DFII10", "2002-06-01")
    mbei = (m10 - mr).rename("bei")
    xdf = pd.concat([mr.diff().rename("d_real"),
                     mbei.diff().rename("d_bei")], axis=1).dropna()
    d_nom10 = m10.diff().rename("d_nom10").dropna()

    bv = window_betas(ls, xdf, uni)
    uv = window_betas(ls, d_nom10.to_frame(), uni)
    df["real_beta"] = bv["b_d_real"]
    df["bei_beta"] = bv["b_d_bei"]
    df["nom_beta_0321"] = uv["b_d_nom10"]
    df.to_csv(SIGNAL_CSV)

    # ---------------- correlation table first (GATE 0) ----------------
    print("\n================  W1-X CORRELATIONS  ================")
    pairs = [
        ("real_beta", "mkt_beta"),
        ("bei_beta", "mkt_beta"),
        ("real_beta", "bei_beta"),
        ("nom_beta_0321", "rate_beta"),
    ]
    corr = {}
    for a, b in pairs:
        corr[(a, b)] = df[[a, b]].corr().iloc[0, 1]
        print(f"  corr({a:>13s}, {b:>9s}) = {corr[(a, b)]: .3f}")
    n_est = int(df["real_beta"].notna().sum())
    print(f"  (estimated on N={n_est} signals, window 2003-01..2021-12, "
          f"min {MIN_N} months)")

    gate0 = abs(corr[("real_beta", "mkt_beta")])
    if gate0 > GATE0_LIMIT:
        print(f"\nGATE 0 FAILED: |corr(real_beta, mkt_beta)| = {gate0:.3f} "
              f"> {GATE0_LIMIT}")
        print("Not discriminable from market beta. Stopping before "
              "cross-sections per pre-registered gate.")
        print(f"[saved] {SIGNAL_CSV}")
        sys.exit(0)
    print(f"\nGATE 0 PASSED: |corr(real_beta, mkt_beta)| = {gate0:.3f} "
          f"<= {GATE0_LIMIT}")

    # ---------------- cross-sections ----------------
    ctrl = ["pub_year", "is_tstat"]
    x1 = ["real_beta", "bei_beta"] + ctrl
    x2 = ["real_beta", "bei_beta"] + ctrl + ["mkt_beta", "pre_vol"]
    run_spec(df, "X1 real+bei", "post_mean", x1, "real_beta", detail=True)
    run_spec(df, "X2 MAIN GATE: X1 + mkt_beta + pre_vol", "post_mean", x2,
             "real_beta", detail=True)
    run_spec(df, "X3 X2 + Cat.Economic FE", "post_mean", x2, "real_beta",
             fe_col="cat_econ")
    run_spec(df, "X4 X2, cluster SE (Cat.Economic)", "post_mean", x2,
             "real_beta", cluster_col="cat_econ")
    f5 = run_spec(df, "X5 nom_beta_0321 base spec", "post_mean",
                  ["nom_beta_0321"] + ctrl, "nom_beta_0321")
    if f5.params["nom_beta_0321"] > 0:
        print("\n[flag] X5: nominal beta on the 2003-2021 window is POSITIVE "
              "-> part of the E2 flip is window, not real-vs-nominal.")
    for yr in (2022, 2023, 2024):
        run_spec(df, f"X6 {yr} only (X2 spec)", f"post_mean_{yr}", x2,
                 "real_beta")

    res = pd.DataFrame(RESULTS)
    for c, r in (("coef", 4), ("t", 2), ("p", 4)):
        res[c] = res[c].round(r)
    print("\n================  W1-X SUMMARY  ================")
    print(res.to_string(index=False))
    res.to_csv(SUMMARY_CSV, index=False)
    print(f"[saved] {SUMMARY_CSV}")

    # ---------------- panel mechanism test ----------------
    fit, long = panel_test(ls, df["real_beta"], xdf["d_real"])
    print("\n================  PANEL MECHANISM TEST  ================")
    print(f"  N obs = {int(fit.nobs)}, signals = {long['signal'].nunique()}, "
          f"months = {long['month'].nunique()} (SE clustered by month)")
    print(f"  b(real_beta x dDFII10) = {fit.params['inter']:.4f}  "
          f"t = {fit.tvalues['inter']:.3f}  p = {fit.pvalues['inter']:.4f}"
          f"   [prediction: b > 0]")
    cum = xdf.loc[(xdf.index >= POST0) & (xdf.index <= POST1), "d_real"]
    print("  cumulative dDFII10 by year:",
          {y: round(float(cum[cum.index.year == y].sum()), 2)
           for y in (2022, 2023, 2024)})
    print(f"[saved] {SIGNAL_CSV}")


if __name__ == "__main__":
    main()
