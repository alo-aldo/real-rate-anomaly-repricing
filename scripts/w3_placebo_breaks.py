#!/usr/bin/env python3
"""W3-A pseudo-break placebo tests for the real-rate repricing result."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import regime_rotation_pilot as rp
import w1_robustness as w1


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "w3"
LOG = ROOT / "logs" / "w3_robustness.log"

PRE_START = pd.Period("2003-01", "M")
MIN_PRE = 120
MIN_POST = 18
PSEUDO_YEARS = [2014, 2015, 2016, 2017, 2018, 2019]
X2_COLS = ["real_beta", "bei_beta", "mkt_beta", "pre_vol", "pub_year", "is_tstat"]


def start_log() -> None:
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(
        f"W3 robustness run started {datetime.now().isoformat(timespec='seconds')}\n",
        encoding="utf-8",
    )


def log(msg: str) -> None:
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg.rstrip() + "\n")


def load_real_bei_changes() -> pd.DataFrame:
    path = ROOT / "data" / "external_cache" / "clean_bei_dgs10_minus_dfii10_monthly.csv"
    df = pd.read_csv(path)
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    out = df.set_index("month")[["dDFII10", "dBEI"]].rename(
        columns={"dDFII10": "d_real", "dBEI": "d_bei"}
    )
    return out.apply(pd.to_numeric, errors="coerce").dropna()


def fit_first_stage(ret: pd.Series, xdf: pd.DataFrame) -> dict[str, float] | None:
    j = pd.concat([ret.rename("ret"), xdf], axis=1, join="inner").dropna()
    if len(j) < MIN_PRE:
        return None
    X = sm.add_constant(j[["d_real", "d_bei"]].astype(float))
    fit = sm.OLS(j["ret"].astype(float), X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    return {
        "real_beta": float(fit.params["d_real"]),
        "bei_beta": float(fit.params["d_bei"]),
        "n_pre": int(fit.nobs),
    }


def fit_x2(df: pd.DataFrame) -> dict[str, float | int | str]:
    d = df[["post_mean"] + X2_COLS].dropna().copy()
    if len(d) <= len(X2_COLS) + 2:
        return {
            "N": int(len(d)),
            "real_beta_coef": np.nan,
            "real_beta_t": np.nan,
            "real_beta_p": np.nan,
            "status": "too_few_obs",
        }
    X = sm.add_constant(d[X2_COLS].astype(float))
    fit = sm.OLS(d["post_mean"].astype(float), X).fit(cov_type="HC1")
    return {
        "N": int(fit.nobs),
        "real_beta_coef": float(fit.params["real_beta"]),
        "real_beta_t": float(fit.tvalues["real_beta"]),
        "real_beta_p": float(fit.pvalues["real_beta"]),
        "status": "ok",
    }


def build_break_frame(
    year: int,
    ls: pd.DataFrame,
    macro: pd.DataFrame,
    mkt: pd.Series,
    doc: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    pre_end = pd.Period(f"{year - 1}-12", "M")
    post_start = pd.Period(f"{year}-01", "M")
    post_end = pd.Period(f"{year + 2}-12", "M")
    macro_pre = macro.loc[(macro.index >= PRE_START) & (macro.index <= pre_end)]
    rows: dict[str, dict[str, float | int]] = {}

    for sig in ls.columns:
        s = ls[sig].dropna()
        pre = s[(s.index >= PRE_START) & (s.index <= pre_end)]
        post = s[(s.index >= post_start) & (s.index <= post_end)]
        if len(post.dropna()) < MIN_POST:
            continue
        betas = fit_first_stage(pre, macro_pre)
        if betas is None:
            continue
        mkt_beta = w1.hac_beta(pre, mkt.loc[(mkt.index >= PRE_START) & (mkt.index <= pre_end)], MIN_PRE)
        rows[sig] = {
            **betas,
            "post_mean": float(post.mean()),
            "n_post": int(post.notna().sum()),
            "mkt_beta": float(mkt_beta) if pd.notna(mkt_beta) else np.nan,
            "pre_vol": float(pre.std()) if len(pre) > 1 else np.nan,
        }

    frame = pd.DataFrame.from_dict(rows, orient="index")
    frame = frame.join(doc[["pub_year", "is_tstat"]], how="left")
    return frame, fit_x2(frame)


def comparison_columns(results: pd.DataFrame) -> pd.DataFrame:
    out = results.copy()
    actual = out.loc[out["break_type"] == "actual"].iloc[0]
    placebo = out.loc[out["break_type"] == "placebo"].copy()
    actual_coef = float(actual["real_beta_coef"])
    stronger_count = int((placebo["real_beta_coef"] < actual_coef).sum())
    placebo_n = int(placebo["real_beta_coef"].notna().sum())
    percentile = stronger_count / placebo_n if placebo_n else np.nan
    out["actual_2022_coef"] = actual_coef
    out["actual_percentile_vs_placebo"] = percentile
    out["placebo_stronger_count"] = int((placebo["real_beta_coef"] > actual_coef).sum())
    out["placebo_n"] = placebo_n
    out["actual_stronger_than_most_placebos"] = bool(stronger_count > placebo_n / 2)
    out["actual_top_quartile_vs_placebo"] = bool(percentile >= 0.75) if pd.notna(percentile) else False
    out["any_placebo_sign_flip_vs_2022"] = bool(
        ((placebo["real_beta_coef"] * actual_coef) < 0).any()
    )
    return out


def fmt(x: object, digits: int = 4) -> str:
    if pd.isna(x):
        return "NA"
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.{digits}f}"
    return str(x)


def write_report(results: pd.DataFrame) -> None:
    actual = results.loc[results["break_type"] == "actual"].iloc[0]
    placebo = results.loc[results["break_type"] == "placebo"].copy()
    lines = [
        "# W3-A Pseudo-Break Placebo Tests",
        "",
        "Design: for each pseudo-break year, estimate real_beta and bei_beta using only data before the break, then regress the next 36-month average return on real_beta, bei_beta, market beta, pre volatility, publication year, and in-sample t-stat.",
        "",
        "## Comparison",
        f"- Actual 2022 real_beta coefficient: {fmt(actual['real_beta_coef'])}",
        f"- Actual 2022 t-statistic: {fmt(actual['real_beta_t'])}",
        f"- Placebo coefficient range: {fmt(placebo['real_beta_coef'].min())} to {fmt(placebo['real_beta_coef'].max())}",
        f"- Placebos stronger than 2022: {int(actual['placebo_stronger_count'])} of {int(actual['placebo_n'])}",
        f"- 2022 stronger than most placebos: {'YES' if actual['actual_stronger_than_most_placebos'] else 'NO'}",
        f"- 2022 top quartile versus placebos: {'YES' if actual['actual_top_quartile_vs_placebo'] else 'NO'}",
        f"- Any placebo sign flip versus 2022: {'YES' if actual['any_placebo_sign_flip_vs_2022'] else 'NO'}",
        "",
        "## Break-Level Results",
        "",
        "| Break | Type | N | Coef | t | p | Sign |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in results.sort_values(["break_year", "break_type"]).iterrows():
        sign = "positive" if row["real_beta_coef"] > 0 else "negative"
        lines.append(
            f"| {int(row['break_year'])} | {row['break_type']} | {int(row['N'])} | "
            f"{fmt(row['real_beta_coef'])} | {fmt(row['real_beta_t'])} | "
            f"{fmt(row['real_beta_p'])} | {sign} |"
        )
    lines.append("")
    if bool(actual["actual_stronger_than_most_placebos"]):
        lines.append("Placebo conclusion: 2022 is stronger than most pseudo-breaks under the same pre-break estimation protocol.")
    else:
        lines.append("Placebo conclusion: 2022 is ordinary relative to pseudo-breaks; do not strengthen the claim without saying so.")
    (OUT_DIR / "placebo_breaks_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    start_log()
    log("Running W3-A pseudo-break placebo tests.")

    ls = rp.load_ls_returns()
    macro = load_real_bei_changes()
    mkt = w1.load_mktrf()
    doc = w1.load_doc_full()
    rows: list[dict[str, float | int | str]] = []

    for year in PSEUDO_YEARS + [2022]:
        frame, res = build_break_frame(year, ls, macro, mkt, doc)
        break_type = "actual" if year == 2022 else "placebo"
        row = {
            "break_year": year,
            "break_type": break_type,
            "signals_with_betas": int(len(frame)),
            **res,
        }
        rows.append(row)
        log(
            f"W3-A {year}: type={break_type}, N={row['N']}, "
            f"coef={fmt(row['real_beta_coef'])}, t={fmt(row['real_beta_t'])}"
        )

    results = comparison_columns(pd.DataFrame(rows))
    results.to_csv(OUT_DIR / "placebo_breaks_summary.csv", index=False)
    write_report(results)
    log("Wrote outputs/w3/placebo_breaks_summary.csv")
    log("Wrote outputs/w3/placebo_breaks_report.md")
    print(f"[saved] {OUT_DIR / 'placebo_breaks_summary.csv'}")
    print(f"[saved] {OUT_DIR / 'placebo_breaks_report.md'}")


if __name__ == "__main__":
    main()
