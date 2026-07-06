# Real-Rate Exposure and the Repricing of Equity Anomalies

Clean replication repository for the paper "Real-Rate Exposure and the Repricing of Equity Anomalies."

## Status

This repository is a clean release copy. It does not include the source development history, raw third-party data, submission-system files, fee records, or local upload packages.

Core finding: pre-2022 real-rate exposure predicts the post-2022 cross-section of equity anomaly returns, consistent with regime-break repricing rather than stable month-by-month real-rate exposure persistence.

## Repository Structure

- `scripts/`: replication, robustness, audit, and paper-asset scripts.
- `manifests/`: source-data manifests and download manifests.
- `outputs/paper/`: paper-ready tables, figures, and appendix outputs.
- `outputs/w2/`: international JKP validation outputs.
- `outputs/w3/`: defensive robustness outputs.
- `figures/`: paper figures copied for easy upload or inspection.
- `manuscript/`: manuscript files, references, and v2 audit artifacts.

## Data

Raw third-party data are not redistributed in this repository. Regenerate inputs from public providers using the scripts:

- Open Asset Pricing anomaly returns and signal documentation: `scripts/download_data.py`
- FRED DGS2, DGS10, DFII10, and Fama-French Mkt-RF cache: `scripts/cache_external_data.py`
- JKP international factor and market data: `scripts/w2_international.py`

See `DATA_LICENSE_NOTICE.md` and `data_availability_statement.md` for details.

## Reproduction

Run commands from the repository root.

```powershell
python -m pip install -r requirements.txt
python scripts/download_data.py
python scripts/cache_external_data.py
python scripts/checks_data_integrity.py
python scripts/regime_rotation_pilot.py
python scripts/w1_robustness.py
python scripts/w1x_decomposition.py
python scripts/w1x_extra_robustness.py
python scripts/paper_assets.py
python scripts/w2_international.py
python scripts/w3_placebo_breaks.py
python scripts/w3_generated_regressor_bootstrap.py
python scripts/w3_multiverse_summary.py
```

`replication_steps.md` gives the same workflow with expected outputs.

## Key Outputs

- `outputs/paper/tables/table2_main.csv`
- `outputs/w2/w2_results.csv`
- `outputs/w3/placebo_breaks_report.md`
- `outputs/w3/generated_regressor_bootstrap_report.md`
- `outputs/w3/multiverse_report.md`
- `manuscript/frl_manuscript_v2.md`
- `manuscript/manuscript_v2_audit.md`

## Interpretation Caveats

- The evidence is predictive and associative, not a causal identification claim.
- The post-2022 monthly panel interaction is negative, so the result should not be interpreted as stable month-by-month real-rate exposure persistence.
- W2 uses U.S. real-rate and BEI shocks as global regime variables, not local country-level real-rate shocks.
- BEI/risk-appetite interpretation is suggestive and not separately identified.
