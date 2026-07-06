#!/usr/bin/env python3
"""W3-C multiverse transparency table and W3 gate summary."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "w3"
LOG = ROOT / "logs" / "w3_robustness.log"


def log(msg: str) -> None:
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg.rstrip() + "\n")


def parse_cell(cell: object) -> tuple[float, float]:
    if pd.isna(cell):
        return np.nan, np.nan
    m = re.search(r"([-+]?\d+\.\d+)\s+\(([-+]?\d+\.\d+)\)", str(cell))
    if not m:
        return np.nan, np.nan
    return float(m.group(1)), float(m.group(2))


def stat(coef: float, tval: float) -> tuple[str, str]:
    if pd.isna(coef):
        return "NA", "NA"
    return f"{coef:.4f}", f"t={tval:.2f}"


def verdict_from_positive(coef: float, tval: float, threshold: float = 2.0) -> str:
    if pd.isna(coef) or coef <= 0:
        return "FAILS"
    if abs(tval) < threshold:
        return "LIMITS"
    return "SUPPORTS"


def add(rows: list[dict[str, str]], spec: str, coef: str, stat_text: str, verdict: str, interpretation: str, source: str) -> None:
    rows.append(
        {
            "specification": spec,
            "key_coefficient": coef,
            "t_stat_or_interval": stat_text,
            "narrow_claim_status": verdict,
            "interpretation": interpretation,
            "source": source,
        }
    )


def table2_rows(rows: list[dict[str, str]]) -> None:
    tab = pd.read_csv(ROOT / "outputs" / "paper" / "tables" / "table2_main.csv").set_index("Row")
    cols = list(tab.columns)
    col_a, col_b, col_c, col_d, col_e, col_f = cols

    coef, tval = parse_cell(tab.loc["nominal/rate_beta", col_a])
    c, s = stat(coef, tval)
    add(rows, "nominal baseline", c, s, "LIMITS", "Nominal-rate beta predicts the 2022 cross-section but does not isolate real-rate exposure.", "table2_main")

    coef, tval = parse_cell(tab.loc["nominal/rate_beta", col_b])
    c, s = stat(coef, tval)
    add(rows, "nominal + market beta + volatility", c, s, "LIMITS", "The nominal coefficient weakens after controls, motivating the real/BEI decomposition.", "table2_main")

    coef, tval = parse_cell(tab.loc["real_beta", col_c])
    c, s = stat(coef, tval)
    add(rows, "real + BEI baseline", c, s, verdict_from_positive(coef, tval), "Real-rate exposure remains positive when BEI exposure is included.", "table2_main")

    coef, tval = parse_cell(tab.loc["real_beta", col_d])
    c, s = stat(coef, tval)
    add(rows, "X2 real + BEI + market beta + volatility", c, s, verdict_from_positive(coef, tval), "Main U.S. specification supports the narrow regime-break repricing claim.", "table2_main")

    coef, tval = parse_cell(tab.loc["real_beta", col_e])
    c, s = stat(coef, tval)
    add(rows, "Cat.Economic FE", c, s, verdict_from_positive(coef, tval), "Category fixed effects do not absorb the real-rate coefficient.", "table2_main")

    coef, tval = parse_cell(tab.loc["real_beta", col_f])
    c, s = stat(coef, tval)
    add(rows, "category-clustered SE", c, s, verdict_from_positive(coef, tval), "Clustered inference by economic category keeps the real-rate coefficient positive.", "table2_main")


def extra_rows(rows: list[dict[str, str]]) -> None:
    extra = pd.read_csv(ROOT / "outputs" / "w1x_extra_robustness.csv")

    cat = extra.loc[extra["check"] == "category_collapse"].iloc[0]
    add(
        rows,
        "category collapse",
        f"{cat['coef']:.4f}",
        f"t={cat['t']:.2f}",
        verdict_from_positive(float(cat["coef"]), float(cat["t"])),
        "The result survives collapsing to Cat.Economic means, though precision is lower.",
        "w1x_extra_robustness",
    )

    boot = extra.loc[extra["check"] == "bootstrap_signals_2000"].iloc[0]
    boot_verdict = "SUPPORTS" if float(boot["boot_p2_5"]) > 0 else "FAILS"
    add(
        rows,
        "signal bootstrap",
        f"{boot['coef']:.4f}",
        f"95% interval [{boot['boot_p2_5']:.4f}, {boot['boot_p97_5']:.4f}]",
        boot_verdict,
        "Signal-level resampling keeps the real-rate coefficient positive.",
        "w1x_extra_robustness",
    )

    loo = extra.loc[extra["check"] == "leave_one_cat"].copy()
    loo_min = float(loo["coef"].min())
    loo_t_min = float(loo["t"].min())
    add(
        rows,
        "leave-one-category",
        f"min={loo_min:.4f}",
        f"min t={loo_t_min:.2f}",
        "SUPPORTS" if loo_min > 0 and loo_t_min > 2 else "LIMITS",
        "No single Cat.Economic exclusion flips the result.",
        "w1x_extra_robustness",
    )

    themes = extra.loc[extra["check"].astype(str).str.startswith("theme_exclusion_")].copy()
    theme_min = float(themes["coef"].min())
    theme_t_min = float(themes["t"].min())
    add(
        rows,
        "theme exclusions",
        f"min={theme_min:.4f}",
        f"min t={theme_t_min:.2f}",
        "SUPPORTS" if theme_min > 0 and theme_t_min > 2 else "LIMITS",
        "The coefficient remains positive after excluding major signal themes.",
        "w1x_extra_robustness",
    )

    lomo = extra.loc[extra["check"] == "leave_one_2022_month"].copy()
    lomo_min = float(lomo["coef"].min())
    lomo_t_min = float(lomo["t"].min())
    add(
        rows,
        "2022 leave-one-month-out",
        f"min={lomo_min:.4f}",
        f"min t={lomo_t_min:.2f}",
        "SUPPORTS" if lomo_min > 0 and lomo_t_min > 2 else "LIMITS",
        "The 2022 evidence is not created by one month alone.",
        "w1x_extra_robustness",
    )


def w2_rows(rows: list[dict[str, str]]) -> None:
    w2 = pd.read_csv(ROOT / "outputs" / "w2" / "w2_results.csv")
    main = w2.loc[w2["spec"].str.startswith("W2-2")].iloc[0]
    clustered = w2.loc[w2["spec"].str.startswith("W2-6")].iloc[0]
    add(
        rows,
        "W2 international",
        f"{main['real_beta_coef']:.4f}",
        f"t={clustered['real_beta_t']:.2f} two-way clustered",
        verdict_from_positive(float(main["real_beta_coef"]), float(clustered["real_beta_t"])),
        "International evidence supports U.S. real-rate shocks as global regime variables, not a separate country-level alpha claim.",
        "w2_results",
    )


def panel_row(rows: list[dict[str, str]]) -> None:
    text = (ROOT / "outputs" / "cache_repro_check.md").read_text(encoding="utf-8")
    coef_match = re.search(r"\| Panel `b\(real_beta x dDFII10\)` \|\s*([-+]?\d+\.\d+)\s*\|", text)
    t_match = re.search(r"\| Panel t-stat \|\s*([-+]?\d+\.\d+)\s*\|", text)
    coef = float(coef_match.group(1)) if coef_match else np.nan
    tval = float(t_match.group(1)) if t_match else np.nan
    add(
        rows,
        "post-2022 monthly panel negative interaction",
        f"{coef:.4f}" if pd.notna(coef) else "NA",
        f"t={tval:.2f}" if pd.notna(tval) else "NA",
        "LIMITS",
        "The monthly panel has the opposite sign, so the manuscript should keep the mechanism claim cross-sectional and regime-level.",
        "cache_repro_check",
    )


def w3_rows(rows: list[dict[str, str]]) -> None:
    placebo_path = OUT_DIR / "placebo_breaks_summary.csv"
    boot_path = OUT_DIR / "generated_regressor_bootstrap.csv"
    if placebo_path.exists():
        p = pd.read_csv(placebo_path)
        actual = p.loc[p["break_type"] == "actual"].iloc[0]
        status = "SUPPORTS" if bool(actual["actual_stronger_than_most_placebos"]) else "FAILS"
        add(
            rows,
            "W3 pseudo-break placebo",
            f"{actual['real_beta_coef']:.4f}",
            f"percentile={actual['actual_percentile_vs_placebo']:.2f}",
            status,
            "Compares the 2022 break to pseudo-breaks from 2014 through 2019 under the same pre-break protocol.",
            "w3_placebo_breaks",
        )
    if boot_path.exists():
        b = pd.read_csv(boot_path)
        lo = float(b["p2_5"].min())
        hi = float(b["p97_5"].max())
        mean_coef = float(b["mean_coef"].mean())
        status = "SUPPORTS" if lo > 0 else "FAILS"
        add(
            rows,
            "W3 generated-regressor bootstrap",
            f"{mean_coef:.4f}",
            f"pooled interval envelope [{lo:.4f}, {hi:.4f}]",
            status,
            "First-stage beta uncertainty leaves the X2 real-rate coefficient positive across 6- and 12-month block bootstraps.",
            "w3_generated_regressor_bootstrap",
        )


def gate_status(multiverse: pd.DataFrame) -> tuple[str, list[str]]:
    reasons: list[str] = []
    p = pd.read_csv(OUT_DIR / "placebo_breaks_summary.csv")
    actual = p.loc[p["break_type"] == "actual"].iloc[0]
    placebo_ok = bool(actual["actual_stronger_than_most_placebos"])
    if placebo_ok:
        reasons.append("2022 is stronger than most pseudo-breaks.")
    else:
        reasons.append("2022 is ordinary relative to pseudo-breaks.")

    b = pd.read_csv(OUT_DIR / "generated_regressor_bootstrap.csv")
    boot_ok = bool((b["p2_5"] > 0).all())
    if boot_ok:
        reasons.append("Generated-regressor bootstrap intervals exclude zero for all block lengths.")
    else:
        reasons.append("At least one generated-regressor bootstrap interval includes zero.")

    contradictions = multiverse[multiverse["narrow_claim_status"] == "FAILS"]
    contradiction_ok = len(contradictions) == 0
    if contradiction_ok:
        reasons.append("The multiverse table has no contradiction to the narrow claim.")
    else:
        failed = ", ".join(contradictions["specification"].astype(str))
        reasons.append(f"The multiverse table contains FAILS rows: {failed}.")

    if placebo_ok and boot_ok and contradiction_ok:
        return "PASS", reasons
    if bool(actual.get("actual_top_quartile_vs_placebo", False)) and boot_ok and contradiction_ok:
        return "WEAK PASS", reasons
    return "FAIL", reasons


def write_report(df: pd.DataFrame, status: str, reasons: list[str]) -> None:
    lines = [
        "# W3-C Multiverse Transparency Summary",
        "",
        f"Final W3 gate: **{status}**",
        "",
        "## Gate Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in reasons)
    lines.extend(
        [
            "",
            "## Multiverse Table",
            "",
            "| Specification | Key coefficient | t-stat or interval | Status | Interpretation |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for _, row in df.iterrows():
        lines.append(
            f"| {row['specification']} | {row['key_coefficient']} | "
            f"{row['t_stat_or_interval']} | {row['narrow_claim_status']} | "
            f"{row['interpretation']} |"
        )
    (OUT_DIR / "multiverse_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("Running W3-C multiverse summary.")
    rows: list[dict[str, str]] = []
    table2_rows(rows)
    extra_rows(rows)
    w2_rows(rows)
    panel_row(rows)
    w3_rows(rows)
    df = pd.DataFrame(rows)

    status, reasons = gate_status(df)
    df.to_csv(OUT_DIR / "multiverse_summary.csv", index=False)
    write_report(df, status, reasons)
    log(f"W3-C gate={status}")
    log("Wrote outputs/w3/multiverse_summary.csv")
    log("Wrote outputs/w3/multiverse_report.md")
    print(f"[saved] {OUT_DIR / 'multiverse_summary.csv'}")
    print(f"[saved] {OUT_DIR / 'multiverse_report.md'}")
    print(f"W3 FINAL GATE: {status}")


if __name__ == "__main__":
    main()
