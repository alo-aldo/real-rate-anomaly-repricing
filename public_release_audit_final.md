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
| No unintended email addresses | PASS | The only email-pattern hit is the manuscript's intentional corresponding-author email |
| No submission-system files | PASS | File scan returned no hits |
| No fee or transaction files | PASS | File scan returned no hits |
| No DOCX/PDF upload package files | PASS | File scan returned no hits |
| No source `.git` history from development repo | PASS | This is a fresh clean repo with its own history |
| No draft/pilot/archive files | PASS | File scan returned no hits |
| README title and repository name match | PASS | README title is `real-rate-anomaly-repricing` |
| README states replication package title | PASS | README names the paper title |
| README describes defensive robustness and v2 status | PASS | README states pseudo-break placebo, generated-regressor bootstrap, and multiverse PASS |
| DATA_LICENSE_NOTICE says raw third-party inputs are not redistributed | PASS | Statement present |
| `requirements.txt` exists | PASS | Present |
| `replication_steps.md` exists | PASS | Present |
| Scripts can be run from repository root in principle | PASS | Python compile check passed |
| `outputs/w3/` exists and includes W3 reports | PASS | Placebo, bootstrap, and multiverse reports present |
| Public figure labels are descriptive | PASS | Figure 2 and Figure A1 use real-rate beta labels with no internal `X2` label |
| `CITATION.cff` has title and author metadata | PASS | Paper title and `Gibeom An` author metadata present |
| `LICENSE` exists | PASS | MIT license present |
| GitHub URL in Data Availability matches | PASS | URL matches manuscript statement |

## Notes

Raw third-party data are deliberately excluded. Users are directed to regenerate inputs from original public providers using the included scripts. The manuscript files intentionally include the corresponding-author email so that the public replication package matches the submission metadata.

The labels `w2` and `w3` remain in script names, output-directory names, and audit-trace files only. Public-facing manuscript text uses descriptive language such as international validation, pseudo-break placebo tests, generated-regressor bootstrap, and defensive robustness.
