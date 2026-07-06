# Public Release Audit

## Final Judgment

PASS for private GitHub upload.

This repository is a clean replication copy. It does not include the source development git history, raw third-party data, local upload packages, submission-system records, or fee/transaction records.

## Source State

- Source commit used for release copy: `050a3f5 add W3 robustness and v2 manuscript`
- Release file count: 81 files
- Files larger than 5 MB: none

## Included File Groups

- Root documentation: `README.md`, `replication_steps.md`, `data_availability_statement.md`, `DATA_LICENSE_NOTICE.md`, `LICENSE`, `CITATION.cff`
- Scripts: active replication, robustness, audit, and paper-asset scripts under `scripts/`
- Manifests: `manifests/external_cache_manifest.csv`, `manifests/w2_download_manifest.csv`
- Outputs: `outputs/paper/`, `outputs/w2/`, `outputs/w3/`, plus selected reproducibility reports
- Figures: paper figures under `figures/`
- Manuscript: submission manuscript, v2 manuscript, highlights, references, and v2 audit files under `manuscript/`

## Excluded File Groups

- Source `.git` history
- Raw third-party data and local caches under `data/`
- Raw JKP archives and raw FRED/Fama-French files
- Development archives
- Draft v0 and pilot scratch files
- Submission DOCX files and local upload packages
- Submission-system PDFs, manuscript numbers, fee receipts, and transaction records
- Private logs from the development repository

## Audit Checks

| Check | Result | Notes |
| --- | --- | --- |
| No local Windows paths | PASS | Path scan returned no hits. |
| No phone-number-like strings | PASS | U.S.-style phone pattern scan returned no hits. |
| No raw data directories | PASS | No committed `data/` directory. |
| No draft v0 files | PASS | File scan returned no hits. |
| No pilot scratch files | PASS | File scan returned no hits. |
| No submission-system files | PASS | File scan returned no hits. |
| No fee or transaction files | PASS | File scan returned no hits. |
| No Word/PDF/ZIP/bundle upload artifacts | PASS | File scan returned no hits. |
| No untracked large files | PASS | No files exceed 5 MB. |
| README reproduction commands work in principle | PASS | Script layout was adjusted for `scripts/` and Python compile checks passed. |
| Data availability consistent with excluded raw data | PASS | Raw data are excluded and regeneration routes are documented. |

## Notes

The repository is currently prepared for private GitHub upload. Public release should wait until author metadata, final repository visibility, and any Zenodo DOI decision are confirmed.
