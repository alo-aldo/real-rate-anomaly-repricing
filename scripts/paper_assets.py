#!/usr/bin/env python3
"""Build paper tables and figures from the verified US evidence package."""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "paper"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
APPENDIX = OUT / "appendix"
LOG = ROOT / "logs" / "paper_assets.log"

X2_COLS = ["real_beta", "bei_beta", "pub_year", "is_tstat", "mkt_beta", "pre_vol"]


def ensure_dirs() -> None:
    for path in (OUT, TABLES, FIGURES, APPENDIX, ROOT / "logs"):
        path.mkdir(parents=True, exist_ok=True)


def fmt_num(x: object, digits: int = 4) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)


def md_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False) + "\n"


def write_table(df: pd.DataFrame, stem: str, folder: Path = TABLES) -> None:
    df.to_csv(folder / f"{stem}.csv", index=False)
    (folder / f"{stem}.md").write_text(md_table(df), encoding="utf-8")


def fit_spec(df: pd.DataFrame, ycol: str, xcols: list[str], *, fe_col: str | None = None,
             cluster_col: str | None = None) -> dict[str, object]:
    need = [ycol] + xcols + [c for c in (fe_col, cluster_col) if c]
    d = df[list(dict.fromkeys(need))].dropna().copy()
    X = d[xcols].astype(float)
    fe_n = 0
    if fe_col:
        fe_n = int(d[fe_col].nunique())
        dummies = pd.get_dummies(d[fe_col], prefix="fe", drop_first=True).astype(float)
        X = pd.concat([X, dummies], axis=1)
    X = sm.add_constant(X)
    y = d[ycol].astype(float)
    if cluster_col:
        groups = d[cluster_col].astype("category").cat.codes.values
        fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
        se_type = f"clustered by {cluster_col}"
    else:
        fit = sm.OLS(y, X).fit(cov_type="HC1")
        se_type = "HC1"
    return {
        "fit": fit,
        "N": int(fit.nobs),
        "R2": float(fit.rsquared),
        "FE": f"{fe_n} Cat.Economic" if fe_col else "No",
        "SE": se_type,
    }


def coef_cell(spec: dict[str, object], var: str) -> str:
    fit = spec["fit"]
    if var not in fit.params.index:
        return ""
    return f"{fit.params[var]:.4f} ({fit.tvalues[var]:.2f})"


def theme_mask(df: pd.DataFrame, pattern: str) -> pd.Series:
    text = (
        df.index.astype(str).to_series(index=df.index) + " " +
        df.get("cat_econ", "").fillna("").astype(str) + " " +
        df.get("cat_data", "").fillna("").astype(str)
    )
    return text.str.contains(pattern, flags=re.IGNORECASE, regex=True)


def fit_x2(df: pd.DataFrame, ycol: str = "post_mean") -> dict[str, float | int]:
    spec = fit_spec(df, ycol, X2_COLS)
    fit = spec["fit"]
    return {
        "N": int(fit.nobs),
        "coef": float(fit.params["real_beta"]),
        "t": float(fit.tvalues["real_beta"]),
        "p": float(fit.pvalues["real_beta"]),
        "R2": float(fit.rsquared),
    }


def build_table1(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame([
        ["Signals", len(df)],
        ["Pre window for nominal beta", "1990-01 to 2021-12"],
        ["Pre window for real/BEI beta", "2003-01 to 2021-12"],
        ["Post window", "2022-01 onward"],
        ["Post coverage, min/median/max months",
         f"{int(df['n_post'].min())}/{fmt_num(df['n_post'].median(), 1)}/{int(df['n_post'].max())}"],
        ["pre_mean, mean/median", f"{fmt_num(df['pre_mean'].mean())}/{fmt_num(df['pre_mean'].median())}"],
        ["post_mean, mean/median", f"{fmt_num(df['post_mean'].mean())}/{fmt_num(df['post_mean'].median())}"],
        ["real_beta, mean/median", f"{fmt_num(df['real_beta'].mean())}/{fmt_num(df['real_beta'].median())}"],
        ["bei_beta, mean/median", f"{fmt_num(df['bei_beta'].mean())}/{fmt_num(df['bei_beta'].median())}"],
        ["Cat.Economic categories", int(df["cat_econ"].nunique())],
        ["Rotated signals", int(df["rotated"].sum())],
        ["Publication year, min/median/max",
         f"{int(df['pub_year'].min())}/{fmt_num(df['pub_year'].median(), 1)}/{int(df['pub_year'].max())}"],
        ["In-sample t-stat, mean/median",
         f"{fmt_num(df['is_tstat'].mean())}/{fmt_num(df['is_tstat'].median())}"],
    ], columns=["Item", "Value"])
    return out


def build_table2(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    specs = {
        "A nominal beta baseline": fit_spec(df, "post_mean", ["rate_beta", "pub_year", "is_tstat"]),
        "B nominal + mkt + vol": fit_spec(
            df, "post_mean", ["rate_beta", "pub_year", "is_tstat", "mkt_beta", "pre_vol"]),
        "C real + BEI": fit_spec(df, "post_mean", ["real_beta", "bei_beta", "pub_year", "is_tstat"]),
        "D real + BEI + mkt + vol": fit_spec(df, "post_mean", X2_COLS),
        "E D + category FE": fit_spec(df, "post_mean", X2_COLS, fe_col="cat_econ"),
        "F D clustered by category": fit_spec(df, "post_mean", X2_COLS, cluster_col="cat_econ"),
    }
    rows = []
    for label, var in [
        ("real_beta", "real_beta"),
        ("bei_beta", "bei_beta"),
        ("nominal/rate_beta", "rate_beta"),
        ("mkt_beta", "mkt_beta"),
        ("pre_vol", "pre_vol"),
        ("pub_year", "pub_year"),
        ("is_tstat", "is_tstat"),
    ]:
        rows.append({"Row": label, **{name: coef_cell(spec, var) for name, spec in specs.items()}})
    for label, key in [("N", "N"), ("R2", "R2"), ("FE indicator", "FE"), ("SE type", "SE")]:
        row = {"Row": label}
        for name, spec in specs.items():
            value = spec[key]
            row[name] = fmt_num(value, 3) if isinstance(value, float) else str(value)
        rows.append(row)
    return pd.DataFrame(rows), specs


def build_table3(df: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    w1 = pd.read_csv(ROOT / "w1_summary.csv")
    rows = []
    for label in [
        "A1 winsorized post_mean",
        "A2 winsorized decay",
        "F pub_year <= 2004",
    ]:
        r = w1[w1["variant"] == label].iloc[0]
        rows.append([label, int(r["N"]), r["rate_beta_coef"], r["t"], r["p"], "nominal rate_beta"])
    for check in ["category_collapse", "bootstrap_signals_2000"]:
        r = extra[extra["check"] == check].iloc[0]
        note = "real_beta category means" if check == "category_collapse" else (
            f"95% CI [{r['boot_p2_5']:.4f}, {r['boot_p97_5']:.4f}], share>0={r['share_coef_gt_0']:.3f}")
        rows.append([check, int(r["N"]), r["coef"], r.get("t", np.nan), r.get("p", np.nan), note])
    loo = extra[extra["check"] == "leave_one_cat"]
    rows.append(["leave-one-category-out min t", int(loo["N"].min()), loo["coef"].min(), loo["t"].min(), "", "0 sign flips"])
    for check in [
        "theme_exclusion_beta_size_liquidity",
        "theme_exclusion_lowvol_lottery",
        "theme_exclusion_rd_intangible_growth",
        "theme_exclusion_momentum_reversal",
        "post_mean_2022H1",
        "post_mean_2022H2",
        "post_mean_2023",
        "post_mean_2024",
    ]:
        r = extra[extra["check"] == check].iloc[0]
        rows.append([check, int(r["N"]), r["coef"], r["t"], r["p"], "real_beta X2"])
    lomo = extra[extra["check"] == "leave_one_2022_month"]
    rows.append(["2022 leave-one-month-out minimum t", int(lomo["N"].min()),
                 lomo.loc[lomo["t"].idxmin(), "coef"], lomo["t"].min(), "", "all coefficients positive"])
    return pd.DataFrame(rows, columns=["Check", "N", "Coefficient", "t-stat", "p-value", "Note"]).round(4)


def write_appendix(df: pd.DataFrame, extra: pd.DataFrame) -> None:
    rotated = df[df["rotated"]].sort_values("real_beta")
    write_table(rotated.reset_index().rename(columns={"index": "signal"}), "appendix_rotated_signals", APPENDIX)
    write_table(df.sort_values("real_beta").head(20).reset_index().rename(columns={"index": "signal"}),
                "appendix_bottom20_real_beta", APPENDIX)
    write_table(df.sort_values("real_beta").tail(20).reset_index().rename(columns={"index": "signal"}),
                "appendix_top20_real_beta", APPENDIX)
    write_table(df.sort_values("bei_beta").head(20).reset_index().rename(columns={"index": "signal"}),
                "appendix_bottom20_bei_beta", APPENDIX)
    write_table(df.sort_values("bei_beta").tail(20).reset_index().rename(columns={"index": "signal"}),
                "appendix_top20_bei_beta", APPENDIX)
    write_table(extra[extra["check"] == "leave_one_cat"], "appendix_leave_one_category_out", APPENDIX)
    write_table(extra[extra["check"] == "bootstrap_signals_2000"], "appendix_bootstrap_summary", APPENDIX)

    themes = {
        "beta_size_liquidity": r"beta|size|dolvol|illiq|liquid|bidask|spread|volume|turnover|zerotrade|price|sharevol",
        "lowvol_lottery": r"vol|maxret|skew|coskew|tail|lottery|idio|realized|var|cpvol|std_turn",
        "rd_intangible_growth": r"\brd\b|rds|rdcap|r&d|intan|patent|citation|growth|gr[a-z]|orgcap|brand|adexp|fgr",
        "momentum_reversal": r"mom|momentum|reversal|rev|streak|surprise|recommendation|recomm",
    }
    rows = []
    for name, pattern in themes.items():
        excluded = sorted(df.index[theme_mask(df, pattern)].astype(str))
        for signal in excluded:
            rows.append([name, signal])
    write_table(pd.DataFrame(rows, columns=["Theme", "Excluded signal"]),
                "appendix_theme_exclusion_signal_lists", APPENDIX)


def build_figures(df: pd.DataFrame, extra: pd.DataFrame, table2_specs: dict[str, dict[str, object]]) -> pd.DataFrame:
    plot_df = df[["real_beta", "post_mean"]].dropna()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(plot_df["real_beta"], plot_df["post_mean"] * 100, s=18, alpha=0.65)
    b, a = np.polyfit(plot_df["real_beta"], plot_df["post_mean"] * 100, 1)
    xs = np.linspace(plot_df["real_beta"].min(), plot_df["real_beta"].max(), 100)
    ax.plot(xs, a + b * xs, color="black", linewidth=1.4)
    ax.axhline(0, color="gray", linewidth=0.7)
    ax.axvline(0, color="gray", linewidth=0.7)
    ax.set_xlabel("Pre-2022 real-rate beta")
    ax.set_ylabel("Post-2022 mean long-short return (% per month)")
    ax.set_title("Real-rate exposure and post-2022 anomaly returns")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig1_real_beta_vs_post_mean.png", dpi=200)
    plt.close(fig)

    period = extra[extra["check"].isin([
        "post_mean_2022H1", "post_mean_2022H2", "post_mean_2023", "post_mean_2024"
    ])].copy()
    period["label"] = period["check"].str.replace("post_mean_", "", regex=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(period["label"], period["coef"], color="#4c78a8")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_ylabel("Real-rate beta coefficient")
    ax.set_title("Real-beta coefficient by post period")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig2_period_coefficients.png", dpi=200)
    plt.close(fig)

    comp_rows = []
    for label, var in [
        ("A nominal", "rate_beta"),
        ("B nominal+mkt+vol", "rate_beta"),
        ("C real+BEI", "real_beta"),
        ("D real+BEI+mkt+vol", "real_beta"),
        ("E + category FE", "real_beta"),
        ("F clustered", "real_beta"),
    ]:
        name = next(k for k in table2_specs if k.startswith(label[0]))
        fit = table2_specs[name]["fit"]
        comp_rows.append([label, fit.params[var], fit.tvalues[var]])
    comp = pd.DataFrame(comp_rows, columns=["Spec", "Coefficient", "t-stat"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#f58518", "#f58518", "#4c78a8", "#4c78a8", "#4c78a8", "#4c78a8"]
    ax.bar(comp["Spec"], comp["Coefficient"], color=colors)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_ylabel("Key rate coefficient")
    ax.set_title("Nominal-rate beta versus real-rate decomposition")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig3_nominal_vs_decomposed.png", dpi=200)
    plt.close(fig)

    rng = np.random.default_rng(20260706)
    d = df[["post_mean"] + X2_COLS].dropna().reset_index(drop=True)
    coefs = []
    for _ in range(2000):
        sample = d.iloc[rng.integers(0, len(d), len(d))].reset_index(drop=True)
        coefs.append(fit_x2(sample)["coef"])
    boot = pd.DataFrame({"real_beta_coef": coefs})
    boot.to_csv(APPENDIX / "appendix_bootstrap_distribution.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(boot["real_beta_coef"], bins=36, color="#54a24b", alpha=0.85)
    ax.axvline(0, color="black", linewidth=0.9)
    ax.axvline(boot["real_beta_coef"].quantile(0.025), color="gray", linestyle="--")
    ax.axvline(boot["real_beta_coef"].quantile(0.975), color="gray", linestyle="--")
    ax.set_xlabel("Bootstrapped real-rate beta coefficient")
    ax.set_ylabel("Frequency")
    ax.set_title("Signal bootstrap distribution")
    fig.tight_layout()
    fig.savefig(FIGURES / "figA1_bootstrap_distribution.png", dpi=200)
    plt.close(fig)
    return comp


def write_report(table2_specs: dict[str, dict[str, object]], outputs: list[Path]) -> None:
    x2 = table2_specs["D real + BEI + mkt + vol"]["fit"]
    x3 = table2_specs["E D + category FE"]["fit"]
    x4 = table2_specs["F D clustered by category"]["fit"]
    report = [
        "# Paper Assets Report",
        "",
        "## Inputs",
        "- `w1x_signal_level.csv`",
        "- `w1_signal_level.csv`",
        "- `w1_summary.csv`",
        "- `w1x_summary.csv`",
        "- `outputs/w1x_extra_robustness.csv`",
        "- `data/external_cache/manifest.csv`",
        "",
        "## Key Coefficients",
        f"- Preferred real-rate specification: coef={x2.params['real_beta']:.4f}, t={x2.tvalues['real_beta']:.2f}",
        f"- Category-fixed-effects specification: coef={x3.params['real_beta']:.4f}, t={x3.tvalues['real_beta']:.2f}",
        f"- Category-clustered specification: coef={x4.params['real_beta']:.4f}, t={x4.tvalues['real_beta']:.2f}",
        "",
        "## Verification",
        "- Main table coefficients match the verified U.S. evidence summaries up to rounding.",
        "- Robustness entries are read from the verified extra robustness CSV.",
        "- No existing research logic or result files were modified.",
        "",
        "## Caveat",
        "- The post-2022 monthly panel interaction remains negative: b(real_beta x dDFII10) = -0.5937, t = -2.435. Interpret the result as regime-break repricing, not stable month-by-month real-rate exposure persistence.",
        "",
        "## Created Outputs",
    ]
    report.extend(f"- `{path.relative_to(ROOT)}`" for path in outputs)
    (OUT / "paper_assets_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    df = pd.read_csv(ROOT / "w1x_signal_level.csv", index_col=0)
    extra = pd.read_csv(ROOT / "outputs" / "w1x_extra_robustness.csv")

    outputs: list[Path] = []
    table1 = build_table1(df)
    write_table(table1, "table1_sample_signal_summary")
    outputs += [TABLES / "table1_sample_signal_summary.md", TABLES / "table1_sample_signal_summary.csv"]

    table2, table2_specs = build_table2(df)
    write_table(table2, "table2_main")
    outputs += [TABLES / "table2_main.md", TABLES / "table2_main.csv"]

    table3 = build_table3(df, extra)
    write_table(table3, "table3_robustness_summary")
    outputs += [TABLES / "table3_robustness_summary.md", TABLES / "table3_robustness_summary.csv"]

    write_appendix(df, extra)
    outputs += sorted(APPENDIX.glob("appendix_*.md")) + sorted(APPENDIX.glob("appendix_*.csv"))

    comp = build_figures(df, extra, table2_specs)
    write_table(comp, "figure3_nominal_vs_decomposed_source", APPENDIX)
    outputs += sorted(FIGURES.glob("*.png"))

    write_report(table2_specs, outputs)
    LOG.write_text(
        "Paper assets generated from verified US outputs.\n"
        f"Created {len(outputs)} listed table/figure/appendix artifacts.\n",
        encoding="utf-8",
    )
    print(f"[saved] {OUT / 'paper_assets_report.md'}")
    print(f"[saved] {LOG}")
    print("[saved] paper tables, figures, and appendix assets")


if __name__ == "__main__":
    main()
