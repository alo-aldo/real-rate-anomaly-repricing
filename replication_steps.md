# Replication Steps

These commands assume PowerShell from the repository root.

## 1. Environment

```powershell
python -m pip install -r requirements.txt
```

## 2. Raw Inputs

Raw third-party data are intentionally not committed. Generate or place the required inputs under `data/`.

```powershell
python scripts/download_data.py
```

If automatic Open Asset Pricing download fails, follow the manual instructions printed by the script and place:

```text
data/PredictorLSretWide.csv
data/SignalDoc.csv
```

## 3. U.S. Macro And Market Cache

```powershell
python scripts/cache_external_data.py
```

Expected generated manifest:

```text
data/external_cache/manifest.csv
```

The release copy also includes the verified source manifest at:

```text
manifests/external_cache_manifest.csv
```

## 4. Data Integrity

```powershell
python scripts/checks_data_integrity.py
```

Expected outputs:

```text
outputs/data_integrity_report.md
logs/data_integrity.log
```

## 5. U.S. Evidence

```powershell
python scripts/regime_rotation_pilot.py
python scripts/w1_robustness.py
python scripts/w1x_decomposition.py
python scripts/w1x_extra_robustness.py
```

Expected outputs include:

```text
results_cross_section.csv
w1_summary.csv
w1_signal_level.csv
w1x_summary.csv
w1x_signal_level.csv
outputs/w1x_extra_robustness.csv
outputs/w1x_extra_robustness.md
```

## 6. Paper Tables And Figures

```powershell
python scripts/paper_assets.py
```

Expected outputs:

```text
outputs/paper/tables/
outputs/paper/figures/
outputs/paper/appendix/
```

## 7. International Validation

```powershell
python scripts/w2_international.py
```

Expected outputs:

```text
outputs/w2/w2_download_manifest.csv
outputs/w2/w2_coverage_report.md
outputs/w2/w2_results.csv
outputs/w2/w2_results_summary.md
outputs/w2/w2_robustness.csv
outputs/w2/w2_bootstrap_summary.csv
outputs/w2/w2_signal_country_level.csv
```

## 8. Defensive Robustness

```powershell
python scripts/w3_placebo_breaks.py
python scripts/w3_generated_regressor_bootstrap.py
python scripts/w3_multiverse_summary.py
```

Expected outputs:

```text
outputs/w3/placebo_breaks_summary.csv
outputs/w3/placebo_breaks_report.md
outputs/w3/generated_regressor_bootstrap.csv
outputs/w3/generated_regressor_bootstrap_report.md
outputs/w3/multiverse_summary.csv
outputs/w3/multiverse_report.md
```

## 9. Manuscript Audit

The v2 manuscript audit artifacts are included:

```text
manuscript/manuscript_v2_audit.md
manuscript/manuscript_v2_claim_lint.csv
manuscript/claim_audit_table_v2.csv
```

The final v2 audit judgment is PASS.
