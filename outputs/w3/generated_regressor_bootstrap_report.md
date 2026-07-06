# W3-B Generated-Regressor Block Bootstrap

Design: resample the 2003-01..2021-12 beta-estimation months in contiguous monthly blocks, re-estimate real_beta and bei_beta for each signal, and re-run the X2 cross-section with fixed second-stage controls.

| Block length | Draws | Mean coef | Boot SE | 2.5 pct | 97.5 pct | Share coef > 0 | Share t > 2 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 1000 | 0.1465 | 0.0587 | 0.0270 | 0.2511 | 0.988 | 0.832 |
| 12 | 1000 | 0.1575 | 0.0590 | 0.0235 | 0.2558 | 0.985 | 0.866 |

Bootstrap conclusion: both block-length intervals exclude zero.
