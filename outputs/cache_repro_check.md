# Cache Reproducibility Check

Branch: `cache-reproducibility`
Baseline tag: `repro-pass-v1`
Run log: `logs/cache_repro_run.log`

## Goal

Make the analysis runnable without live online downloads by using files in
`data/external_cache/` first. The original research logic, windows, regression
specifications, and output definitions were not changed.

## Scripts Modified

| Script | Cache-first change |
| --- | --- |
| `regime_rotation_pilot.py` | `load_rates()` now reads `data/external_cache/clean_fred_DGS2_monthly.csv` first. If the cache is missing, it stops unless `--download` is passed. |
| `w1_robustness.py` | `fred_monthly_change()` and `load_mktrf()` now read cached DGS10, DFII10, and Mkt-RF first. If the cache is missing, they stop unless `--download` is passed. |
| `w1x_decomposition.py` | DGS10 and DFII10 monthly levels now load from cached cleaned FRED files first. If the cache is missing, the script stops unless `--download` is passed. |

## Commands Run

No `--download` flag was passed.

```powershell
python regime_rotation_pilot.py
python w1_robustness.py
python w1x_decomposition.py
```

## Completion

| Script | Exit code | Result |
| --- | ---: | --- |
| `regime_rotation_pilot.py` | 0 | PASS |
| `w1_robustness.py` | 0 | PASS |
| `w1x_decomposition.py` | 0 | PASS |

## Comparison to `repro-pass-v1`

| File | Comparison |
| --- | --- |
| `w1_summary.csv` | Byte-identical numeric CSV output |
| `w1x_summary.csv` | Byte-identical numeric CSV output |
| `results_cross_section.csv` | Same shape; max numeric absolute difference `2.6645352591003757e-15` |
| `w1_signal_level.csv` | Same shape; max numeric absolute difference `2.6645352591003757e-15` |
| `w1x_signal_level.csv` | Same shape; max numeric absolute difference `2.6645352591003757e-15` |
| `fig_rotation_scatter.png` | Regenerated PNG differs by 8 bytes; regression numbers are unchanged |

The tiny CSV differences are machine-precision float serialization differences
from reading cached CSV inputs rather than live in-memory `pandas_datareader`
objects.

## Key Numbers

From the cache-only run:

| Quantity | Value |
| --- | ---: |
| W1-X corr(`real_beta`, `mkt_beta`) | 0.313 |
| W1-X corr(`bei_beta`, `mkt_beta`) | 0.845 |
| W1-X corr(`real_beta`, `bei_beta`) | 0.341 |
| W1-X X2 `real_beta` coef | 0.2112 |
| W1-X X2 `real_beta` t-stat | 4.06 |
| W1-X X3 `real_beta` t-stat | 2.85 |
| W1-X X4 Cat.Economic cluster t-stat | 3.37 |
| Panel `b(real_beta x dDFII10)` | -0.5937 |
| Panel t-stat | -2.435 |

## PASS/FAIL

CACHE REPRO PASS.

- The scripts completed without `--download`.
- The modified loaders use local cached files when present.
- The main W1 and W1-X coefficients and t-statistics match `repro-pass-v1` up to numerical precision.
- No live network download is required for the active W1/W1-X path when `data/external_cache/` is present.

