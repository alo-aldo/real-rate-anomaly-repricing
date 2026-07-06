# Data Availability Statement

This clean replication repository does not redistribute raw third-party data. The analysis uses public data sources that users should obtain from the original providers:

| Source | Files or series | Reproduction route | Redistribution note |
| --- | --- | --- | --- |
| Open Asset Pricing | OSAP anomaly returns and signal documentation | `python scripts/download_data.py` or manual download from Open Asset Pricing | Follow Open Asset Pricing terms before redistributing raw files. |
| FRED | DGS2, DGS10, DFII10 | `python scripts/cache_external_data.py` | Public source data; regenerate locally from FRED. |
| Kenneth French Data Library | Fama-French Mkt-RF | `python scripts/cache_external_data.py` | Follow the data library terms before redistributing raw files. |
| JKP Global Factor Data | International factor and market returns, factor details, country classification | `python scripts/w2_international.py` | JKP data are provided under their stated license terms; preserve attribution and restrictions. |

Generated outputs, paper tables, figures, manifests, and manuscript files are included in this repository. The manifests document the verified source inputs used in the analysis:

- `manifests/external_cache_manifest.csv`
- `manifests/w2_download_manifest.csv`

Interpretation caveats:

- The international validation uses U.S. real-rate and BEI shocks as global regime variables, not local country-level real-rate shocks.
- The post-2022 monthly panel interaction is negative, so the evidence should be interpreted as regime-break repricing rather than stable monthly real-rate exposure persistence.
