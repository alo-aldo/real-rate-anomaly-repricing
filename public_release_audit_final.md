# Public GitHub Release Audit Final

## Final Judgment

PUBLIC_READY.

The clean replication repository is safe to make public from a sensitive-data and licensing-audit perspective. It is also consistent with the manuscript's Data Availability statement:

`https://github.com/alo-aldo/real-rate-anomaly-repricing`

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| No raw third-party data included | PASS | No committed `data/` directory |
| No cache/raw directories included | PASS | No raw cache directory files are committed |
| No local Windows paths | PASS | Path scan returned no hits outside `.gitignore` patterns |
| No phone numbers | PASS | U.S.-style phone-number scan returned no hits |
| No email addresses | PASS | Email-pattern scan returned no hits |
| No submission-system files | PASS | File scan returned no hits |
| No fee or transaction files | PASS | File scan returned no hits |
| No DOCX/PDF upload package files | PASS | File scan returned no hits |
| No source `.git` history from development repo | PASS | This is a fresh clean repo with its own history |
| No draft/pilot/archive files | PASS | File scan returned no hits |
| README title and repository name match | PASS | README title is `real-rate-anomaly-repricing` |
| README states replication package title | PASS | README names the paper title |
| README describes W3 robustness and v2 status | PASS | README states W3 placebo, generated-regressor bootstrap, and multiverse PASS |
| DATA_LICENSE_NOTICE says raw third-party inputs are not redistributed | PASS | Statement present |
| `requirements.txt` exists | PASS | Present |
| `replication_steps.md` exists | PASS | Present |
| Scripts can be run from repository root in principle | PASS | Python compile check passed |
| `outputs/w3/` exists and includes W3 reports | PASS | Placebo, bootstrap, and multiverse reports present |
| `CITATION.cff` has title and author metadata | PASS | Paper title and repository-owner author metadata present |
| `LICENSE` exists | PASS | MIT license present |
| GitHub URL in Data Availability matches | PASS | URL matches manuscript statement |

## Notes

Raw third-party data are deliberately excluded. Users are directed to regenerate inputs from original public providers using the included scripts. Before public release or DOI minting, the author may replace the repository-owner author metadata in `CITATION.cff` with the preferred formal author name and ORCID.
