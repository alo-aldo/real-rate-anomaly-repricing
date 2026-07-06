#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regime_rotation_pilot.py
========================
Gate-2 파일럿: "사전(pre-2022) 금리민감도가 post-2022 anomaly 성과의
횡단면을 예측하는가?" (Regime Rotation — FRL 파일럿, 무료 데이터만 사용)

준비물 (./data/ 폴더에 넣기):
  1) PredictorLSretWide.csv
       - Open Source Asset Pricing (openassetpricing.com) → Data
         → 신호별 롱숏 '월수익률' wide 포맷 CSV.
       - 릴리스마다 파일명이 조금 다를 수 있음. wide 포맷(열=신호, 행=월)
         롱숏 수익률 파일이면 이 이름으로 저장하면 됨.
  2) SignalDoc.csv
       - 같은 사이트의 신호 메타데이터(발표연도 Year, in-sample t-stat 등).
  3) (선택) DGS2.csv
       - FRED 2년물 국채수익률. 없으면 pandas_datareader로 자동 다운로드 시도.
       - 수동: fred.stlouisfed.org/series/DGS2 → Download CSV

실행:
  pip install pandas numpy statsmodels matplotlib pandas_datareader
  python regime_rotation_pilot.py

출력:
  results_cross_section.csv   신호별 금리베타·pre/post 성과·회전 플래그
  fig_rotation_scatter.png    사전 금리베타 vs post-2022 성과 산점도
  콘솔                        횡단면 회귀 3본 + GO/NO-GO 요약
"""

import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

DATA_DIR   = "data"
CACHE_DIR  = os.path.join(DATA_DIR, "external_cache")
PRE_START  = "1990-01"   # 금리베타 추정 시작(데이터 있으면)
PRE_END    = "2021-12"   # pre 기간 끝 (ZIRP 시대 포함)
POST_START = "2022-01"   # post 기간 시작 (긴축 체제)
MIN_PRE_M  = 120         # 최소 pre 관측월
MIN_POST_M = 18          # 최소 post 관측월 (OSAP 릴리스가 짧으면 낮추기)


# ---------------------------------------------------------------- 데이터 로드
def _parse_dates(series):
    v = series.astype(str).str.replace(r"\.0$", "", regex=True)
    if v.str.fullmatch(r"\d{6}").all():           # yyyymm 형식
        return pd.to_datetime(v, format="%Y%m")
    return pd.to_datetime(v, errors="coerce")


def load_ls_returns():
    path = os.path.join(DATA_DIR, "PredictorLSretWide.csv")
    df = pd.read_csv(path)
    # long 포맷(signal/date/ret)이면 wide로 자동 피벗
    low = {c.lower(): c for c in df.columns}
    sig_c = next((low[k] for k in low if "signal" in k), None)
    ret_c = next((low[k] for k in low if k in ("ret", "return", "lsret")), None)
    dat_c = next((low[k] for k in low if k in ("date", "month", "yyyymm")), None)
    if sig_c and ret_c and dat_c:
        print("[info] long 포맷 감지 → wide로 피벗합니다.")
        df = df.pivot_table(index=dat_c, columns=sig_c, values=ret_c).reset_index()
    cand = [c for c in df.columns if c.lower() in ("date", "month", "yyyymm")]
    date_col = cand[0] if cand else df.columns[0]
    df[date_col] = _parse_dates(df[date_col])
    df = df.dropna(subset=[date_col]).set_index(date_col).sort_index()
    df.index = df.index.to_period("M")
    df = df.apply(pd.to_numeric, errors="coerce")
    # 수익률이 %단위(예: 1.2 = 1.2%)로 오는 릴리스도 있음 → 소수로 통일
    med_abs = df.abs().stack().median()
    if med_abs > 0.2:   # 월수익률 중앙값이 20%를 넘을 리 없음 → %단위로 판단
        df = df / 100.0
        print("[info] 수익률이 % 단위로 보여 100으로 나눠 소수로 변환했습니다.")
    return df


def load_rates():
    """DGS2(2년물 국채수익률) → 월말 → 월간 변화(Δ%p)."""
    cache = os.path.join(CACHE_DIR, "clean_fred_DGS2_monthly.csv")
    if os.path.exists(cache):
        r = pd.read_csv(cache)
        r["month"] = pd.PeriodIndex(r["month"], freq="M")
        d = pd.to_numeric(r.set_index("month")["delta"], errors="coerce")
        d = d.dropna()
        d.name = "d_rate"
        return d

    if "--download" not in sys.argv[1:]:
        raise FileNotFoundError(
            "Missing data/external_cache/clean_fred_DGS2_monthly.csv. "
            "Run cache_external_data.py or rerun with --download.")

    csv = os.path.join(DATA_DIR, "DGS2.csv")
    if os.path.exists(csv):
        r = pd.read_csv(csv)
        r.columns = [c.upper() for c in r.columns]
        dcol = "DATE" if "DATE" in r.columns else r.columns[0]
        vcol = "DGS2" if "DGS2" in r.columns else r.columns[-1]
        r[dcol] = pd.to_datetime(r[dcol], errors="coerce")
        s = pd.to_numeric(r.set_index(dcol)[vcol], errors="coerce")
    else:
        from pandas_datareader import data as pdr
        s = pdr.DataReader("DGS2", "fred", start="1985-01-01")["DGS2"]
    try:
        m = s.resample("ME").last()   # pandas >= 2.2
    except ValueError:
        m = s.resample("M").last()    # older pandas
    d = m.diff().dropna()
    d.index = d.index.to_period("M")
    d.name = "d_rate"
    return d


def load_signaldoc():
    path = os.path.join(DATA_DIR, "SignalDoc.csv")
    if not os.path.exists(path):
        print("[warn] SignalDoc.csv 없음 → 발표연도/IS t-stat 통제 생략")
        return None
    doc = pd.read_csv(path)
    acr  = next((c for c in doc.columns if c.lower().startswith("acronym")),
                doc.columns[0])
    year = next((c for c in doc.columns if c.strip().lower() == "year"), None)
    tcol = next((c for c in doc.columns if "stat" in c.lower()), None)
    keep = {acr: "signal"}
    if year: keep[year] = "pub_year"
    if tcol: keep[tcol] = "is_tstat"
    out = doc[list(keep)].rename(columns=keep)
    out["signal"] = out["signal"].astype(str)
    for c in ("pub_year", "is_tstat"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.drop_duplicates("signal").set_index("signal")


# ------------------------------------------------------------ 신호별 통계량
def per_signal_stats(ls, d_rate):
    rows = []
    p0, p1, q0 = (pd.Period(PRE_START, "M"), pd.Period(PRE_END, "M"),
                  pd.Period(POST_START, "M"))
    for sig in ls.columns:
        s = ls[sig].dropna()
        pre  = s[(s.index >= p0) & (s.index <= p1)]
        post = s[s.index >= q0]
        if len(pre) < MIN_PRE_M or len(post) < MIN_POST_M:
            continue
        xr   = d_rate.reindex(pre.index).dropna()
        pre2 = pre.reindex(xr.index).dropna()
        xr   = xr.reindex(pre2.index)
        if len(pre2) < MIN_PRE_M:
            continue
        X = sm.add_constant(xr.values)
        try:
            fit = sm.OLS(pre2.values, X).fit(cov_type="HAC",
                                             cov_kwds={"maxlags": 6})
        except Exception:
            continue
        rows.append({
            "signal": sig,
            "rate_beta":   fit.params[1],
            "rate_beta_t": fit.tvalues[1],
            "pre_mean":  pre.mean(),
            "pre_t":     pre.mean() / pre.std() * np.sqrt(len(pre)),
            "post_mean": post.mean(),
            "post_t":    post.mean() / post.std() * np.sqrt(len(post)),
            "n_pre": len(pre), "n_post": len(post),
        })
    df = pd.DataFrame(rows).set_index("signal")
    df["decay"]   = df["post_mean"] - df["pre_mean"]
    df["rotated"] = ((df["pre_t"].abs() >= 2)
                     & (np.sign(df["post_mean"]) != np.sign(df["pre_mean"])))
    return df


# ------------------------------------------------------------- 횡단면 회귀
def cross_section(res):
    def run(y, xcols, label):
        d = res[[y] + xcols].dropna()
        if len(d) < 30:
            print(f"[skip] {label}: N={len(d)} 너무 작음")
            return None
        X = sm.add_constant(d[xcols].astype(float))
        fit = sm.OLS(d[y].astype(float), X).fit(cov_type="HC1")
        print(f"\n--- {label}  (N={len(d)}) ---")
        print(fit.summary().tables[1])
        return fit

    ctrl = [c for c in ("pub_year", "is_tstat") if c in res.columns]
    f1 = run("post_mean", ["rate_beta"], "(1) post_mean ~ rate_beta")
    f2 = (run("post_mean", ["rate_beta"] + ctrl,
              "(2) post_mean ~ rate_beta + 발표연도/IS-t 통제") if ctrl else f1)
    run("decay", ["rate_beta"] + ctrl, "(3) decay ~ rate_beta (+통제)")
    return f2 if f2 is not None else f1


def make_plot(res):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[warn] matplotlib 없음 → 그림 생략")
        return
    d = res[["rate_beta", "post_mean"]].dropna()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(d["rate_beta"], d["post_mean"] * 100, s=14, alpha=.6)
    b = np.polyfit(d["rate_beta"], d["post_mean"] * 100, 1)
    xs = np.linspace(d["rate_beta"].min(), d["rate_beta"].max(), 50)
    ax.plot(xs, b[0] * xs + b[1], lw=1.5)
    ax.axhline(0, lw=.5, color="k"); ax.axvline(0, lw=.5, color="k")
    ax.set_xlabel("Pre-2022 rate beta  (LS return on Δ2Y yield)")
    ax.set_ylabel("Post-2022 mean LS return (%/month)")
    ax.set_title("Regime rotation: pre-estimated rate sensitivity "
                 "vs post-2022 performance")
    fig.tight_layout()
    fig.savefig("fig_rotation_scatter.png", dpi=150)
    print("\n[saved] fig_rotation_scatter.png")


# ----------------------------------------------------------------------- main
def main():
    ls = load_ls_returns()
    print(f"데이터 커버리지: {ls.index.min()} ~ {ls.index.max()} "
          f"(신호 {ls.shape[1]}개)")
    if ls.index.max() < pd.Period("2023-06", "M"):
        print("[warn] post-2022 구간이 짧습니다. OSAP 최신 릴리스인지 확인하고,"
              " 모자라면 JKP(jkpfactors.com)로 최근 구간을 보강하세요.")
    d_rate = load_rates()
    doc = load_signaldoc()

    df = per_signal_stats(ls, d_rate)
    if doc is not None:
        df = df.join(doc, how="left")
    print(f"필터 통과 신호 수: {len(df)}")

    fit_main = cross_section(df)
    df.sort_values("rate_beta").to_csv("results_cross_section.csv")
    print("[saved] results_cross_section.csv")
    make_plot(df)

    n_rot   = int(df["rotated"].sum())
    n_up    = int((df["rotated"] & (df["post_mean"] > 0)).sum())
    n_down  = n_rot - n_up
    print("\n================  GO / NO-GO  ================")
    print(f"부호 회전 신호 수 (pre |t|>=2 & post 부호 반전): {n_rot}"
          f"  (상방 회전 {n_up} / 하방 회전 {n_down})")
    if fit_main is not None and "rate_beta" in fit_main.tvalues.index:
        t = fit_main.tvalues["rate_beta"]
        print(f"통제 후 rate_beta t-stat: {t:.2f}")
    print("GO 조건: |t| >= 2.5  그리고  회전 사례가 양방향 모두 존재")
    print("NO-GO면: Anomaly Time 국제 재현(기존 2순위)으로 이동. 새 메뉴 없음.")
    print("===============================================")


if __name__ == "__main__":
    main()
