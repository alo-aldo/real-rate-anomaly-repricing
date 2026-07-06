#!/usr/bin/env python3
"""W2 international out-of-sample replication using JKP factor returns."""
from __future__ import annotations

import csv
import hashlib
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups


ROOT = Path(__file__).resolve().parents[1]
JKP = ROOT / "data" / "jkp_cache"
OUT = ROOT / "outputs" / "w2"
LOG = ROOT / "logs" / "w2_international.log"

S3 = "https://jkpfactors-data.s3.amazonaws.com"
URLS = {
    "availability": f"{S3}/public/availability.json",
    "all_countries_all_factors": f"{S3}/public/%5Ball_countries%5D_%5Ball_factors%5D_%5Bmonthly%5D_%5Bvw_cap%5D.zip",
    "all_countries_mkt": f"{S3}/public/%5Ball_countries%5D_%5Bmkt%5D_%5Bmonthly%5D_%5Bvw_cap%5D.zip",
    "factor_details": "https://raw.githubusercontent.com/bkelly-lab/jkp-data/main/src/jkp/data/resources/factor_details.xlsx",
    "country_classification": "https://raw.githubusercontent.com/bkelly-lab/jkp-data/main/src/jkp/data/resources/country_classification.xlsx",
}

MIN_PRE = 120
MIN_POST = 18
PRE0 = pd.Period("2003-01", "M")
PRE1 = pd.Period("2021-12", "M")
POST0 = pd.Period("2022-01", "M")


def ensure_dirs() -> None:
    for path in (JKP, OUT, ROOT / "logs"):
        path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def read_zip_csv(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != 1:
            raise RuntimeError(f"Expected one CSV in {path}, found {names}")
        with z.open(names[0]) as f:
            return pd.read_csv(f)


def period_month(s: pd.Series) -> pd.PeriodIndex:
    return pd.to_datetime(s, errors="coerce").dt.to_period("M")


def cache_inputs() -> pd.DataFrame:
    rows = []
    targets = {
        "availability": JKP / "availability.json",
        "all_countries_all_factors": JKP / "raw_all_countries_all_factors_monthly_vw_cap.zip",
        "all_countries_mkt": JKP / "raw_all_countries_mkt_monthly_vw_cap.zip",
        "factor_details": JKP / "factor_details.xlsx",
        "country_classification": JKP / "country_classification.xlsx",
    }
    for key, path in targets.items():
        download(URLS[key], path)
        rows.append({
            "name": key,
            "source_url": URLS[key],
            "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "path": str(path.relative_to(ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(OUT / "w2_download_manifest.csv", index=False)
    return manifest


def clean_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    factors = read_zip_csv(JKP / "raw_all_countries_all_factors_monthly_vw_cap.zip")
    mkt = read_zip_csv(JKP / "raw_all_countries_mkt_monthly_vw_cap.zip")
    for df in (factors, mkt):
        df["month"] = period_month(df["date"])
        df["location"] = df["location"].astype(str).str.lower()
        df["name"] = df["name"].astype(str)
        df["ret"] = pd.to_numeric(df["ret"], errors="coerce")
    factors.assign(month=factors["month"].astype(str)).to_csv(
        JKP / "clean_all_countries_all_factors_monthly_vw_cap.csv", index=False)
    mkt.assign(month=mkt["month"].astype(str)).to_csv(
        JKP / "clean_all_countries_mkt_monthly_vw_cap.csv", index=False)

    country = pd.read_excel(JKP / "country_classification.xlsx")
    country["location"] = country["excntry"].astype(str).str.lower()
    country.to_csv(JKP / "clean_country_classification.csv", index=False)

    details = pd.read_excel(JKP / "factor_details.xlsx")
    details["name"] = details["abr_jkp"].astype(str)
    details = details[details["abr_jkp"].notna()].copy()
    details["theme"] = details["group"].astype(str).str.lower()
    details[["name", "theme", "direction"]].to_csv(JKP / "clean_factor_details.csv", index=False)
    return factors, mkt, country, details


def load_macro() -> pd.DataFrame:
    bei = pd.read_csv(ROOT / "data" / "external_cache" / "clean_bei_dgs10_minus_dfii10_monthly.csv")
    bei["month"] = pd.PeriodIndex(bei["month"], freq="M")
    return bei.set_index("month")[["dDFII10", "dBEI"]].rename(
        columns={"dDFII10": "d_real", "dBEI": "d_bei"})


def hac_fit(y: pd.Series, x: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    X = sm.add_constant(x.astype(float))
    return sm.OLS(y.astype(float), X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})


def estimate_signal_panel(factors: pd.DataFrame, mkt: pd.DataFrame, country: pd.DataFrame,
                          details: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    developed = set(country.loc[
        country["msci_development"].astype(str).str.lower() == "developed", "location"
    ])
    developed.discard("usa")
    available = set(factors["location"].unique())
    target_locations = sorted(developed & available)

    theme_map = details.set_index("name")["theme"].to_dict()
    market = mkt[mkt["name"].eq("mkt")].copy()
    market_map = {
        loc: g.set_index("month")["ret"].sort_index()
        for loc, g in market.groupby("location")
    }

    rows = []
    xpre = macro.loc[(macro.index >= PRE0) & (macro.index <= PRE1), ["d_real", "d_bei"]]
    for (loc, name), g in factors[factors["location"].isin(target_locations)].groupby(["location", "name"]):
        s = g.set_index("month")["ret"].sort_index().dropna()
        pre = s.loc[(s.index >= PRE0) & (s.index <= PRE1)]
        post = s.loc[s.index >= POST0]
        joint = pd.concat([pre.rename("ret"), xpre], axis=1, join="inner").dropna()
        if len(joint) < MIN_PRE or len(post.dropna()) < MIN_POST:
            continue
        fit = hac_fit(joint["ret"], joint[["d_real", "d_bei"]])

        mkt_series = market_map.get(loc)
        mkt_beta = np.nan
        if mkt_series is not None:
            mj = pd.concat([pre.rename("ret"), mkt_series.rename("mkt")], axis=1, join="inner").dropna()
            if len(mj) >= MIN_PRE:
                mfit = hac_fit(mj["ret"], mj[["mkt"]])
                mkt_beta = float(mfit.params["mkt"])

        rows.append({
            "country": loc,
            "factor": name,
            "theme": theme_map.get(name, "unmapped"),
            "real_beta": float(fit.params["d_real"]),
            "real_beta_t": float(fit.tvalues["d_real"]),
            "bei_beta": float(fit.params["d_bei"]),
            "bei_beta_t": float(fit.tvalues["d_bei"]),
            "mkt_beta": mkt_beta,
            "pre_mean": float(pre.mean()),
            "pre_vol": float(pre.std()),
            "post_mean": float(post.mean()),
            "n_pre": int(len(joint)),
            "n_post": int(post.notna().sum()),
            "post_mean_2022": float(s.loc[(s.index >= pd.Period("2022-01", "M")) &
                                           (s.index <= pd.Period("2022-12", "M"))].mean()),
            "post_mean_2023": float(s.loc[(s.index >= pd.Period("2023-01", "M")) &
                                           (s.index <= pd.Period("2023-12", "M"))].mean()),
            "post_mean_2024": float(s.loc[(s.index >= pd.Period("2024-01", "M")) &
                                           (s.index <= pd.Period("2024-12", "M"))].mean()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "w2_signal_country_level.csv", index=False)
    return out


def add_fe(X: pd.DataFrame, d: pd.DataFrame, col: str) -> pd.DataFrame:
    dum = pd.get_dummies(d[col], prefix=col, drop_first=True).astype(float)
    return pd.concat([X, dum], axis=1)


def run_reg(df: pd.DataFrame, label: str, xcols: list[str], *, country_fe: bool = False,
            theme_fe: bool = False, cluster: str | None = None,
            twoway: bool = False) -> dict[str, object]:
    need = ["post_mean"] + xcols + ["country", "theme", "factor"]
    d = df[need].dropna().copy()
    X = d[xcols].astype(float)
    if country_fe:
        X = add_fe(X, d, "country")
    if theme_fe:
        X = add_fe(X, d, "theme")
    X = sm.add_constant(X)
    model = sm.OLS(d["post_mean"].astype(float), X)

    se_type = "HC1"
    note = ""
    if twoway:
        fit = model.fit()
        g1 = d["country"].astype("category").cat.codes.values
        g2 = d["factor"].astype("category").cat.codes.values
        cov_both, _, _ = cov_cluster_2groups(fit, g1, g2)
        params = fit.params
        se = pd.Series(np.sqrt(np.diag(cov_both)), index=params.index)
        tvals = params / se
        pvals = pd.Series(2 * stats.norm.sf(np.abs(tvals)), index=params.index)
        se_type = "two-way country/factor cluster"
    elif cluster:
        groups = d[cluster].astype("category").cat.codes.values
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
        params, tvals, pvals = fit.params, fit.tvalues, fit.pvalues
        se_type = f"clustered by {cluster}"
    else:
        fit = model.fit(cov_type="HC1")
        params, tvals, pvals = fit.params, fit.tvalues, fit.pvalues

    return {
        "spec": label,
        "N": int(fit.nobs),
        "countries": int(d["country"].nunique()),
        "factors": int(d["factor"].nunique()),
        "themes": int(d["theme"].nunique()),
        "real_beta_coef": float(params["real_beta"]),
        "real_beta_t": float(tvals["real_beta"]),
        "real_beta_p": float(pvals["real_beta"]),
        "bei_beta_coef": float(params["bei_beta"]),
        "bei_beta_t": float(tvals["bei_beta"]),
        "mkt_beta_coef": float(params["mkt_beta"]) if "mkt_beta" in params.index else np.nan,
        "mkt_beta_t": float(tvals["mkt_beta"]) if "mkt_beta" in params.index else np.nan,
        "pre_vol_coef": float(params["pre_vol"]) if "pre_vol" in params.index else np.nan,
        "pre_vol_t": float(tvals["pre_vol"]) if "pre_vol" in params.index else np.nan,
        "R2": float(fit.rsquared),
        "country_FE": country_fe,
        "theme_FE": theme_fe,
        "SE": se_type,
        "note": note,
    }


def collapse_reg(df: pd.DataFrame, col: str) -> dict[str, object]:
    cols = ["post_mean", "real_beta", "bei_beta", "mkt_beta", "pre_vol"]
    d = df.dropna(subset=[col])[cols + [col]].groupby(col).mean(numeric_only=True).reset_index()
    res = run_reg(d.assign(country="collapsed", factor=d[col].astype(str), theme=d[col].astype(str)),
                  f"{col}-level collapse", ["real_beta", "bei_beta", "mkt_beta", "pre_vol"])
    res["spec"] = f"{col}-level collapse"
    return res


def bootstrap(df: pd.DataFrame, n: int = 2000) -> dict[str, object]:
    rng = np.random.default_rng(20260706)
    d = df[["post_mean", "real_beta", "bei_beta", "mkt_beta", "pre_vol", "country", "theme", "factor"]].dropna()
    coefs = []
    for _ in range(n):
        sample = d.iloc[rng.integers(0, len(d), len(d))].reset_index(drop=True)
        try:
            coefs.append(run_reg(sample, "bootstrap", ["real_beta", "bei_beta", "mkt_beta", "pre_vol"],
                                 country_fe=True)["real_beta_coef"])
        except Exception:
            pass
    arr = np.array(coefs)
    return {
        "draws": len(arr),
        "mean": float(arr.mean()),
        "se": float(arr.std(ddof=1)),
        "p2_5": float(np.percentile(arr, 2.5)),
        "p97_5": float(np.percentile(arr, 97.5)),
        "share_gt_0": float((arr > 0).mean()),
    }


def write_reports(manifest: pd.DataFrame, factors: pd.DataFrame, mkt: pd.DataFrame,
                  country: pd.DataFrame, details: pd.DataFrame, panel: pd.DataFrame,
                  results: pd.DataFrame, robustness: pd.DataFrame,
                  boot: dict[str, object], gate: str, gate_reasons: list[str]) -> None:
    developed = set(country.loc[country["msci_development"].astype(str).str.lower() == "developed", "location"])
    developed.discard("usa")
    available = set(factors["location"].unique())
    target = sorted(developed & available)
    unmapped = sorted(set(panel["factor"]) - set(details["name"]))

    coverage = [
        "# W2 Coverage Report",
        "",
        "## Official Data Structure",
        "- Factor returns endpoint: `public/[region]_[theme]_[frequency]_[weight].zip`.",
        "- Baseline file: `[all_countries]_[all_factors]_[monthly]_[vw_cap].zip`.",
        "- Market file: `[all_countries]_[mkt]_[monthly]_[vw_cap].zip`.",
        "- Country development classification: `country_classification.xlsx`, field `msci_development`.",
        "- Factor theme mapping: `factor_details.xlsx`, fields `abr_jkp` and `group`.",
        "- Returns are USD excess returns according to the official JKP data page.",
        "",
        "## Target Sample",
        f"- Developed non-US countries in classification and factor file: {len(target)}.",
        f"- Countries: {', '.join(target)}",
        f"- Raw factor rows: {len(factors)}",
        f"- Raw market rows: {len(mkt)}",
        f"- Estimated factor-country observations after filters: {len(panel)}",
        f"- Countries after filters: {panel['country'].nunique()}",
        f"- Factors after filters: {panel['factor'].nunique()}",
        f"- Themes after filters: {panel['theme'].nunique()}",
        f"- Pre window: {PRE0}..{PRE1}, minimum {MIN_PRE} months.",
        f"- Post window: {POST0} onward, minimum {MIN_POST} months.",
        f"- Unmapped factors: {len(unmapped)}",
        "",
        "## Manifest",
    ]
    coverage.extend(manifest.to_markdown(index=False).splitlines())
    (OUT / "w2_coverage_report.md").write_text("\n".join(coverage) + "\n", encoding="utf-8")

    summary = [
        "# W2 Results Summary",
        "",
        "## Main Regressions",
        results.to_markdown(index=False),
        "",
        "## Robustness",
        robustness.to_markdown(index=False),
        "",
        "## Bootstrap",
        pd.DataFrame([boot]).to_markdown(index=False),
        "",
        "## Gate",
        gate,
    ]
    summary.extend(f"- {r}" for r in gate_reasons)
    (OUT / "w2_results_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    logs = ["Starting W2 international replication"]
    manifest = cache_inputs()
    factors, mkt, country, details = clean_inputs()
    macro = load_macro()
    panel = estimate_signal_panel(factors, mkt, country, details, macro)

    main_results = []
    x1 = ["real_beta", "bei_beta"]
    x2 = ["real_beta", "bei_beta", "mkt_beta", "pre_vol"]
    main_results.append(run_reg(panel, "W2-1 real+BEI + country FE", x1, country_fe=True))
    main_results.append(run_reg(panel, "W2-2 + mkt_beta + pre_vol + country FE", x2, country_fe=True))
    main_results.append(run_reg(panel, "W2-3 W2-2 + theme FE", x2, country_fe=True, theme_fe=True))
    main_results.append(run_reg(panel, "W2-4 W2-2 country-clustered SE", x2, country_fe=True, cluster="country"))
    main_results.append(run_reg(panel, "W2-5 W2-2 factor-clustered SE", x2, country_fe=True, cluster="factor"))
    try:
        main_results.append(run_reg(panel, "W2-6 W2-2 two-way clustered SE", x2, country_fe=True, twoway=True))
    except Exception as e:
        row = main_results[-1].copy()
        row["spec"] = "W2-6 W2-2 two-way clustered SE"
        row["note"] = f"two-way clustering failed: {e}"
        main_results.append(row)
    results = pd.DataFrame(main_results)
    results.to_csv(OUT / "w2_results.csv", index=False)

    robustness_rows = []
    for country_code in sorted(panel["country"].unique()):
        sub = panel[panel["country"] != country_code]
        res = run_reg(sub, f"leave_one_country_{country_code}", x2, country_fe=True)
        robustness_rows.append(res)
    for theme in sorted(panel["theme"].dropna().unique()):
        sub = panel[panel["theme"] != theme]
        res = run_reg(sub, f"leave_one_theme_{theme}", x2, country_fe=True)
        robustness_rows.append(res)
    robustness_rows.append(collapse_reg(panel, "country"))
    robustness_rows.append(collapse_reg(panel, "theme"))
    for year in (2022, 2023, 2024):
        tmp = panel.copy()
        tmp["post_mean"] = tmp[f"post_mean_{year}"]
        robustness_rows.append(run_reg(tmp, f"{year} only W2-2", x2, country_fe=True))
    robustness = pd.DataFrame(robustness_rows)
    robustness.to_csv(OUT / "w2_robustness.csv", index=False)

    boot = bootstrap(panel, 2000)
    pd.DataFrame([boot]).to_csv(OUT / "w2_bootstrap_summary.csv", index=False)

    w22 = results[results["spec"].str.startswith("W2-2")].iloc[0]
    w23 = results[results["spec"].str.startswith("W2-3")].iloc[0]
    w24 = results[results["spec"].str.startswith("W2-4")].iloc[0]
    w25 = results[results["spec"].str.startswith("W2-5")].iloc[0]
    flips_country = robustness[robustness["spec"].str.startswith("leave_one_country_") & (robustness["real_beta_coef"] < 0)]
    flips_theme = robustness[robustness["spec"].str.startswith("leave_one_theme_") & (robustness["real_beta_coef"] < 0)]
    reasons = [
        f"W2-2 real_beta coef={w22['real_beta_coef']:.4f}, t={w22['real_beta_t']:.2f}",
        f"W2-3 real_beta coef={w23['real_beta_coef']:.4f}, t={w23['real_beta_t']:.2f}",
        f"country-cluster real_beta t={w24['real_beta_t']:.2f}",
        f"factor-cluster real_beta t={w25['real_beta_t']:.2f}",
        f"leave-one-country sign flips={len(flips_country)}",
        f"leave-one-theme sign flips={len(flips_theme)}",
        f"bootstrap 95% CI=[{boot['p2_5']:.4f}, {boot['p97_5']:.4f}], share>0={boot['share_gt_0']:.3f}",
    ]
    if (w22["real_beta_coef"] > 0 and w22["real_beta_t"] >= 2 and
            w23["real_beta_coef"] > 0 and w24["real_beta_coef"] > 0 and
            w25["real_beta_coef"] > 0 and len(flips_country) == 0 and len(flips_theme) == 0):
        gate = "W2 STRONG PASS"
    elif w22["real_beta_coef"] > 0 and w23["real_beta_coef"] > 0:
        gate = "W2 WEAK PASS"
    else:
        gate = "W2 FAIL"

    write_reports(manifest, factors, mkt, country, details, panel, results, robustness, boot, gate, reasons)
    logs.extend(reasons)
    logs.append(gate)
    LOG.write_text("\n".join(logs) + "\n", encoding="utf-8")
    print(gate)
    print(f"[saved] {OUT / 'w2_coverage_report.md'}")
    print(f"[saved] {OUT / 'w2_results_summary.md'}")
    print(f"[saved] {OUT / 'w2_results.csv'}")
    print(f"[saved] {LOG}")


if __name__ == "__main__":
    main()
