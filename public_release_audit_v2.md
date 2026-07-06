# Public Release Audit v2

## Final Judgment

PASS for linking in the FRL v2 data availability statement, subject to the repository remaining accessible to editors and reviewers.

## Repository

- Local clean repository: `real-rate-anomalies-replication`
- GitHub repository: `https://github.com/alo-aldo/real-rate-anomaly-repricing`
- Current release commit before this audit update: `f2f0ebb initial clean replication release`

## Checks

| Check | Result | Notes |
| --- | --- | --- |
| README describes v2 and W3 robustness | PASS | README identifies the v2 manuscript and W3 PASS components. |
| Data availability statement matches repo contents | PASS | Raw third-party data are excluded and regeneration routes are listed. |
| No raw third-party data included | PASS | No committed `data/` directory. |
| No local Windows paths | PASS | Path scan returned no hits. |
| No phone-number-like strings | PASS | U.S.-style phone pattern scan returned no hits. |
| No submission-system files | PASS | File scan returned no hits. |
| No submission DOCX/PDF files | PASS | File scan returned no hits. |
| No fee or private files | PASS | File scan returned no hits. |
| `scripts/` paths work from repo root | PASS | Python compile check passed after `ROOT` was adjusted for `scripts/`. |
| `outputs/w3/` exists and includes W3 reports | PASS | Placebo, generated-regressor bootstrap, and multiverse reports are present. |
| `CITATION.cff` title and author metadata are set | PASS | Title is the paper title; author metadata is set to the current repository owner pending public-release name confirmation. |
| `LICENSE` and `DATA_LICENSE_NOTICE.md` present | PASS | Both files are present. |
| `public_release_audit.md` present | PASS | Initial audit file remains present. |

## Notes

The repository is ready for private-review linking. Before making it public or minting a DOI, replace the repository-owner author metadata in `CITATION.cff` with the final preferred author name and optional ORCID.
