#!/usr/bin/env python3
"""Extra robustness checks for the W1-X real_beta result."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import regime_rotation_pilot as rp


ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "outputs" / "w1x_extra_robustness.md"
OUT_CSV = ROOT / "outputs" / "w1x_extra_robustness.csv"
LOG = ROOT / "logs" / "w1x_extra_robustness.log"

X2_COLS = ["real_beta", "bei_beta", "pub_year", "is_tstat", "mkt_beta", "pre_vol"]


def fit_x2(df: pd.DataFrame, ycol: str = "post_mean") -> dict[str, float | int | str]:
    need = [ycol] + X2_COLS
    d = df[need].dropna().copy()
    if len(d) <= len(X2_COLS) + 2:
        return {"N": int(len(d)), "coef": np.nan, "t": np.nan, "p": np.nan, "status": "too_few_obs"}
    X = sm.add_constant(d[X2_COLS].astype(float))
    fit = sm.OLS(d[ycol].astype(float), X).fit(cov_type="HC1")
    return {
        "N": int(fit.nobs),
        "coef": float(fit.params["real_beta"]),
        "t": float(fit.tvalues["real_beta"]),
        "p": float(fit.pvalues["real_beta"]),
        "status": "ok",
    }


def md_table(rows: list[list[object]], headers: list[str]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return out


def fmt(x: float, digits: int = 4) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.{digits}f}"


def theme_mask(df: pd.DataFrame, pattern: str) -> pd.Series:
    text = (
        df.index.astype(str).to_series(index=df.index) + " " +
        df.get("cat_econ", "").fillna("").astype(str) + " " +
        df.get("cat_data", "").fillna("").astype(str)
    )
    return text.str.contains(pattern, flags=re.IGNORECASE, regex=True)


def run_category_collapse(df: pd.DataFrame) -> tuple[dict[str, object], pd.DataFrame]:
    cols = ["post_mean"] + X2_COLS
    collapsed = df.dropna(subset=["cat_econ"]).groupby("cat_econ")[cols].mean(numeric_only=True)
    res = fit_x2(collapsed)
    return res, collapsed


def add_period_means(df: pd.DataFrame) -> pd.DataFrame:
    ls = rp.load_ls_returns()
    out = df.copy()
    sigs = [s for s in out.index if s in ls.columns]
    periods = {
        "post_mean_2022H1": (pd.Period("2022-01", "M"), pd.Period("2022-06", "M")),
        "post_mean_2022H2": (pd.Period("2022-07", "M"), pd.Period("2022-12", "M")),
        "post_mean_2023": (pd.Period("2023-01", "M"), pd.Period("2023-12", "M")),
        "post_mean_2024": (pd.Period("2024-01", "M"), pd.Period("2024-12", "M")),
    }
    for name, (lo, hi) in periods.items():
        block = ls.loc[(ls.index >= lo) & (ls.index <= hi), sigs]
        out.loc[sigs, name] = block.mean()
    for month in pd.period_range("2022-01", "2022-12", freq="M"):
        block = ls.loc[(ls.index >= pd.Period("2022-01", "M")) &
                       (ls.index <= pd.Period("2022-12", "M")) &
                       (ls.index != month), sigs]
        out.loc[sigs, f"post_mean_2022_ex_{month}"] = block.mean()
    return out


def main() -> None:
    ROOT.joinpath("outputs").mkdir(exist_ok=True)
    ROOT.joinpath("logs").mkdir(exist_ok=True)
    rng = np.random.default_rng(20260706)
    lines: list[str] = []
    logs: list[str] = []
    summary_rows: list[dict[str, object]] = []

    df = pd.read_csv(ROOT / "w1x_signal_level.csv", index_col=0)
    base = fit_x2(df)
    summary_rows.append({"check": "base_X2", **base})

    lines.append("# W1-X Extra Robustness")
    lines.append("")
    lines.append("Input: `w1x_signal_level.csv` plus local OSAP returns for period concentration checks.")
    lines.append("")
    lines.append("## Baseline")
    lines.extend(md_table([["X2", base["N"], fmt(base["coef"]), fmt(base["t"]), fmt(base["p"])]],
                          ["Spec", "N", "Coef", "t", "p"]))

    cat_res, collapsed = run_category_collapse(df)
    summary_rows.append({"check": "category_collapse", **cat_res})
    lines.append("")
    lines.append("## Category Collapse")
    lines.extend(md_table([["Cat.Economic means", cat_res["N"], fmt(cat_res["coef"]),
                            fmt(cat_res["t"]), fmt(cat_res["p"])]],
                          ["Spec", "N categories", "Coef", "t", "p"]))

    loo_rows = []
    for cat in sorted(df["cat_econ"].dropna().unique()):
        sub = df[df["cat_econ"] != cat]
        res = fit_x2(sub)
        row = {"check": "leave_one_cat", "category": cat, **res}
        summary_rows.append(row)
        loo_rows.append(row)
    loo = pd.DataFrame(loo_rows)
    sign_flip = loo[loo["coef"] < 0]
    weak = loo[loo["t"].abs() < 2]
    lines.append("")
    lines.append("## Leave-One-Cat.Economic-Out")
    lines.extend(md_table([
        ["coef min/median/max", fmt(loo["coef"].min()), fmt(loo["coef"].median()), fmt(loo["coef"].max())],
        ["t min/median/max", fmt(loo["t"].min()), fmt(loo["t"].median()), fmt(loo["t"].max())],
        ["sign flips", len(sign_flip), "", ""],
        ["abs(t) < 2", len(weak), "", ""],
    ], ["Metric", "Value 1", "Value 2", "Value 3"]))
    if len(sign_flip):
        lines.append("Sign-flip categories: " + ", ".join(sign_flip["category"].astype(str)))
    if len(weak):
        lines.append("Categories dropping below |t| < 2: " + ", ".join(weak["category"].astype(str)))

    themes = {
        "beta_size_liquidity": r"beta|size|dolvol|illiq|liquid|bidask|spread|volume|turnover|zerotrade|price|sharevol",
        "lowvol_lottery": r"vol|maxret|skew|coskew|tail|lottery|idio|realized|var|cpvol|std_turn",
        "rd_intangible_growth": r"\brd\b|rds|rdcap|r&d|intan|patent|citation|growth|gr[a-z]|orgcap|brand|adexp|fgr",
        "momentum_reversal": r"mom|momentum|reversal|rev|streak|surprise|recommendation|recomm",
    }
    lines.append("")
    lines.append("## Theme Exclusions")
    theme_table = []
    theme_kills = 0
    for name, pattern in themes.items():
        mask = theme_mask(df, pattern)
        excluded = sorted(df.index[mask].astype(str))
        sub = df[~mask]
        res = fit_x2(sub)
        killed = (pd.isna(res["coef"]) or res["coef"] <= 0 or abs(res["t"]) < 2)
        theme_kills += int(killed)
        summary_rows.append({"check": f"theme_exclusion_{name}", "excluded_n": len(excluded), **res})
        theme_table.append([name, len(excluded), res["N"], fmt(res["coef"]), fmt(res["t"]), fmt(res["p"]), "YES" if killed else "NO"])
        lines.append("")
        lines.append(f"Excluded signals for `{name}` ({len(excluded)}):")
        lines.append(", ".join(excluded) if excluded else "None")
    lines.append("")
    lines.extend(md_table(theme_table, ["Theme", "Excluded", "N", "Coef", "t", "p", "Killed"]))

    df_period = add_period_means(df)
    lines.append("")
    lines.append("## 2022 Concentration")
    period_rows = []
    for ycol in ["post_mean_2022H1", "post_mean_2022H2", "post_mean_2023", "post_mean_2024"]:
        res = fit_x2(df_period, ycol=ycol)
        summary_rows.append({"check": ycol, **res})
        period_rows.append([ycol, res["N"], fmt(res["coef"]), fmt(res["t"]), fmt(res["p"])])
    lines.extend(md_table(period_rows, ["Period", "N", "Coef", "t", "p"]))

    lomo_rows = []
    for month in pd.period_range("2022-01", "2022-12", freq="M"):
        ycol = f"post_mean_2022_ex_{month}"
        res = fit_x2(df_period, ycol=ycol)
        row = {"check": "leave_one_2022_month", "month_left_out": str(month), **res}
        summary_rows.append(row)
        lomo_rows.append(row)
    lomo = pd.DataFrame(lomo_rows)
    lines.append("")
    lines.append("Leave-one-month-out for 2022:")
    lines.extend(md_table([
        ["coef min/median/max", fmt(lomo["coef"].min()), fmt(lomo["coef"].median()), fmt(lomo["coef"].max())],
        ["t min/median/max", fmt(lomo["t"].min()), fmt(lomo["t"].median()), fmt(lomo["t"].max())],
        ["months with abs(t)<2", int((lomo["t"].abs() < 2).sum()), "", ""],
    ], ["Metric", "Value 1", "Value 2", "Value 3"]))

    d = df[["post_mean"] + X2_COLS].dropna().reset_index(drop=True)
    coefs = []
    skipped = 0
    for _ in range(2000):
        idx = rng.integers(0, len(d), len(d))
        sample = d.iloc[idx].reset_index(drop=True)
        res = fit_x2(sample)
        if res["status"] == "ok" and not pd.isna(res["coef"]):
            coefs.append(float(res["coef"]))
        else:
            skipped += 1
    boot = np.array(coefs)
    boot_mean = float(np.mean(boot))
    boot_se = float(np.std(boot, ddof=1))
    boot_lo, boot_hi = np.percentile(boot, [2.5, 97.5])
    boot_share_pos = float(np.mean(boot > 0))
    summary_rows.append({
        "check": "bootstrap_signals_2000",
        "N": len(d),
        "coef": boot_mean,
        "t": np.nan,
        "p": np.nan,
        "boot_se": boot_se,
        "boot_p2_5": boot_lo,
        "boot_p97_5": boot_hi,
        "share_coef_gt_0": boot_share_pos,
        "skipped": skipped,
    })
    lines.append("")
    lines.append("## Bootstrap")
    lines.extend(md_table([
        ["draws", len(boot)],
        ["skipped", skipped],
        ["mean coef", fmt(boot_mean)],
        ["bootstrap SE", fmt(boot_se)],
        ["2.5 percentile", fmt(float(boot_lo))],
        ["97.5 percentile", fmt(float(boot_hi))],
        ["share(coef > 0)", fmt(boot_share_pos)],
    ], ["Metric", "Value"]))

    pass_category = cat_res["coef"] > 0
    pass_boot = boot_lo > 0
    pass_loo = len(sign_flip) == 0
    pass_theme = theme_kills < len(themes)
    pass_2022 = (lomo["coef"].min() > 0) and ((lomo["t"].abs() < 2).sum() == 0)
    overall = pass_category and pass_boot and pass_loo and pass_theme and pass_2022

    lines.append("")
    lines.append("## PASS/FAIL")
    lines.append("W1-X EXTRA ROBUSTNESS " + ("PASS" if overall else "FAIL"))
    lines.append(f"- Category collapse coefficient positive: {'YES' if pass_category else 'NO'}")
    lines.append(f"- Bootstrap 95% interval excludes zero: {'YES' if pass_boot else 'NO'}")
    lines.append(f"- No single Cat.Economic exclusion flips sign: {'YES' if pass_loo else 'NO'}")
    lines.append(f"- Theme exclusions do not all kill result: {'YES' if pass_theme else 'NO'}")
    lines.append(f"- 2022 effect not entirely one month by leave-one-month-out: {'YES' if pass_2022 else 'NO'}")

    pd.DataFrame(summary_rows).to_csv(OUT_CSV, index=False)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logs.append(f"Read {len(df)} rows from w1x_signal_level.csv")
    logs.append(f"Wrote {OUT_MD}")
    logs.append(f"Wrote {OUT_CSV}")
    logs.append("W1-X EXTRA ROBUSTNESS " + ("PASS" if overall else "FAIL"))
    LOG.write_text("\n".join(logs) + "\n", encoding="utf-8")
    print(f"[saved] {OUT_MD.relative_to(ROOT)}")
    print(f"[saved] {OUT_CSV.relative_to(ROOT)}")
    print(f"[saved] {LOG.relative_to(ROOT)}")
    print("W1-X EXTRA ROBUSTNESS " + ("PASS" if overall else "FAIL"))


if __name__ == "__main__":
    main()
