#!/usr/bin/env python3
"""W3-B block bootstrap for generated real_beta and bei_beta regressors."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import regime_rotation_pilot as rp


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "w3"
LOG = ROOT / "logs" / "w3_robustness.log"

W0 = pd.Period("2003-01", "M")
W1 = pd.Period("2021-12", "M")
MIN_N = 120
DRAWS = 1000
BLOCK_LENGTHS = [6, 12]
RNG_SEED = 20260706
X2_COLS = ["real_beta", "bei_beta", "mkt_beta", "pre_vol", "pub_year", "is_tstat"]


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
    return out.apply(pd.to_numeric, errors="coerce")


def draw_block_indices(n: int, block_len: int, rng: np.random.Generator) -> np.ndarray:
    picks: list[int] = []
    while len(picks) < n:
        start = int(rng.integers(0, n))
        picks.extend((start + k) % n for k in range(block_len))
    return np.array(picks[:n], dtype=int)


def estimate_draw_betas(
    ret_matrix: np.ndarray,
    macro_matrix: np.ndarray,
    signals: list[str],
    sample_idx: np.ndarray,
) -> pd.DataFrame:
    x_full = macro_matrix[sample_idx, :]
    rows: dict[str, dict[str, float]] = {}
    x_ok = np.isfinite(x_full).all(axis=1)
    for j, sig in enumerate(signals):
        y_full = ret_matrix[sample_idx, j]
        ok = x_ok & np.isfinite(y_full)
        if int(ok.sum()) < MIN_N:
            continue
        X = np.column_stack([np.ones(int(ok.sum())), x_full[ok, :]])
        y = y_full[ok]
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        rows[sig] = {"real_beta": float(beta[1]), "bei_beta": float(beta[2])}
    return pd.DataFrame.from_dict(rows, orient="index")


def fit_x2(base: pd.DataFrame, betas: pd.DataFrame) -> dict[str, float | int | str]:
    d = base.join(betas, how="inner")
    d = d[["post_mean"] + X2_COLS].dropna()
    if len(d) <= len(X2_COLS) + 2:
        return {"N": int(len(d)), "coef": np.nan, "t": np.nan, "p": np.nan, "status": "too_few_obs"}
    X = sm.add_constant(d[X2_COLS].astype(float))
    fit = sm.OLS(d["post_mean"].astype(float), X).fit(cov_type="HC1")
    return {
        "N": int(fit.nobs),
        "coef": float(fit.params["real_beta"]),
        "t": float(fit.tvalues["real_beta"]),
        "p": float(fit.pvalues["real_beta"]),
        "status": "ok",
    }


def summarize(block_len: int, coefs: np.ndarray, tvals: np.ndarray, ns: np.ndarray, skipped: int) -> dict[str, float | int]:
    lo, hi = np.percentile(coefs, [2.5, 97.5])
    return {
        "block_length": block_len,
        "draws_requested": DRAWS,
        "draws_completed": int(len(coefs)),
        "skipped": int(skipped),
        "mean_N": float(np.mean(ns)),
        "mean_coef": float(np.mean(coefs)),
        "bootstrap_se": float(np.std(coefs, ddof=1)),
        "p2_5": float(lo),
        "p97_5": float(hi),
        "share_coef_gt_0": float(np.mean(coefs > 0)),
        "share_t_gt_2": float(np.mean(tvals > 2)),
    }


def write_report(rows: list[dict[str, float | int]]) -> None:
    lines = [
        "# W3-B Generated-Regressor Block Bootstrap",
        "",
        "Design: resample the 2003-01..2021-12 beta-estimation months in contiguous monthly blocks, re-estimate real_beta and bei_beta for each signal, and re-run the X2 cross-section with fixed second-stage controls.",
        "",
        "| Block length | Draws | Mean coef | Boot SE | 2.5 pct | 97.5 pct | Share coef > 0 | Share t > 2 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {int(row['block_length'])} | {int(row['draws_completed'])} | "
            f"{row['mean_coef']:.4f} | {row['bootstrap_se']:.4f} | "
            f"{row['p2_5']:.4f} | {row['p97_5']:.4f} | "
            f"{row['share_coef_gt_0']:.3f} | {row['share_t_gt_2']:.3f} |"
        )
    lines.append("")
    if all(float(row["p2_5"]) > 0 for row in rows):
        lines.append("Bootstrap conclusion: both block-length intervals exclude zero.")
    else:
        lines.append("Bootstrap conclusion: at least one block-length interval includes zero; report this as a limit.")
    (OUT_DIR / "generated_regressor_bootstrap_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log("Running W3-B generated-regressor block bootstrap.")
    rng = np.random.default_rng(RNG_SEED)

    base0 = pd.read_csv(ROOT / "w1x_signal_level.csv", index_col=0)
    base = base0[["post_mean", "mkt_beta", "pre_vol", "pub_year", "is_tstat"]].dropna().copy()
    ls = rp.load_ls_returns()
    signals = [sig for sig in base.index.astype(str) if sig in ls.columns]
    months = pd.period_range(W0, W1, freq="M")
    macro = load_real_bei_changes().reindex(months)
    ret_matrix = ls.reindex(months)[signals].to_numpy(dtype=float)
    macro_matrix = macro[["d_real", "d_bei"]].to_numpy(dtype=float)
    base = base.loc[signals]

    rows: list[dict[str, float | int]] = []
    for block_len in BLOCK_LENGTHS:
        coefs: list[float] = []
        tvals: list[float] = []
        ns: list[int] = []
        skipped = 0
        for draw in range(DRAWS):
            sample_idx = draw_block_indices(len(months), block_len, rng)
            betas = estimate_draw_betas(ret_matrix, macro_matrix, signals, sample_idx)
            res = fit_x2(base, betas)
            if res["status"] == "ok" and pd.notna(res["coef"]):
                coefs.append(float(res["coef"]))
                tvals.append(float(res["t"]))
                ns.append(int(res["N"]))
            else:
                skipped += 1
            if (draw + 1) % 100 == 0:
                print(f"[progress] block={block_len}, draw={draw + 1}/{DRAWS}")
        row = summarize(block_len, np.array(coefs), np.array(tvals), np.array(ns), skipped)
        rows.append(row)
        log(
            f"W3-B block={block_len}: draws={row['draws_completed']}, "
            f"coef={row['mean_coef']:.4f}, ci=[{row['p2_5']:.4f}, {row['p97_5']:.4f}]"
        )

    pd.DataFrame(rows).to_csv(OUT_DIR / "generated_regressor_bootstrap.csv", index=False)
    write_report(rows)
    log("Wrote outputs/w3/generated_regressor_bootstrap.csv")
    log("Wrote outputs/w3/generated_regressor_bootstrap_report.md")
    print(f"[saved] {OUT_DIR / 'generated_regressor_bootstrap.csv'}")
    print(f"[saved] {OUT_DIR / 'generated_regressor_bootstrap_report.md'}")


if __name__ == "__main__":
    main()
