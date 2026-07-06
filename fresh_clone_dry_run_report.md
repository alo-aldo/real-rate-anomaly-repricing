# Fresh Clone Dry-Run Report

## Final Judgment

PASS.

The clean replication package is understandable and reproducible in principle without hidden local dependencies. Raw third-party inputs are intentionally excluded, so a full rerun requires regenerating or placing those inputs as documented in `README.md` and `replication_steps.md`.

## Dry-Run Setup

| Item | Result |
| --- | --- |
| Source repository | Local clean replication repository |
| Fresh test directory | Separate local dry-run directory |
| Clone/copy method | Local `git clone` |
| Virtual environment | Created successfully |
| Dependency install | `pip install -r requirements.txt` completed successfully |

## Verification

| Check | Result | Notes |
| --- | --- | --- |
| Fresh clone created | PASS | Clone completed into the dry-run directory |
| Requirements install | PASS | All packages installed in the fresh virtual environment |
| Python compile check | PASS | Active scripts under `scripts/` compiled successfully |
| Hidden source-repo path dependency | PASS | No references to the development source path were found |
| W3 reports present | PASS | `outputs/w3/multiverse_report.md` and companion reports exist |
| Required documentation present | PASS | `README.md`, `replication_steps.md`, and `requirements.txt` exist |
| Raw data exclusion behavior | PASS | `scripts/regime_rotation_pilot.py` stops because `data\PredictorLSretWide.csv` is absent, which is expected because raw data are not redistributed |
| Instructions for missing raw data | PASS | README and replication steps instruct users to run `scripts/download_data.py` or manually place OSAP inputs |

## Observed Missing-Data Message

The lightweight rerun of `scripts/regime_rotation_pilot.py` failed at the expected point:

```text
FileNotFoundError: No such file or directory: 'data\\PredictorLSretWide.csv'
```

This is acceptable for the clean release because raw third-party data are intentionally excluded and regeneration routes are documented.

## Conclusion

The clean repository does not depend on hidden files from the development repository. It can be cloned, dependencies can be installed, scripts can be imported/compiled, and the missing raw-data boundary is explicit.
