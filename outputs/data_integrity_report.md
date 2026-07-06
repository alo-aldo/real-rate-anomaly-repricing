# Data Integrity Report

Workspace: clean replication repository root

## OSAP Returns
| Check | Value |
| --- | --- |
| raw shape | 1188 rows x 213 columns |
| parsed date range | 1926-01-30..2024-12-31 |
| signals | 212 |
| raw median absolute return | 1.642618 |
| raw unit diagnosis | percent-like |
| converted return range | 1926-01..2024-12 |
| post-2022 months | 36 |
| post-2022 coverage min/median/max | 0/36.0/36 |

Missing return cells by year, last 10 years:
| Year | Missing cells |
| --- | --- |
| 2015 | 54 |
| 2016 | 48 |
| 2017 | 48 |
| 2018 | 54 |
| 2019 | 60 |
| 2020 | 60 |
| 2021 | 60 |
| 2022 | 54 |
| 2023 | 137 |
| 2024 | 180 |

Signals with fewer than 30 post-2022 monthly observations: 14
Activism2=0, Activism1=0, Governance=0, ProbInformedTrading=0, PatentsRD=12, SmileSlope=13, RIVolSpread=13, CPVolSpread=13, dVolCall=13, dVolPut=13, skew1=13, dCPVolSpread=13, OptionVolume2=21, OptionVolume1=21

## FRED Rates and BEI
| Check | Value |
| --- | --- |
| DGS2 monthly range | 1976-06..2026-07 |
| DGS10 monthly range | 1985-01..2026-07 |
| DFII10 monthly range | 2003-01..2026-07 |
| BEI aligned range | 2003-01..2026-07 |
| rate units | percentage points |
| monthly conversion | last available daily observation in each calendar month |
| monthly changes | current month-end level minus prior month-end level |
| BEI identity | PASS |

Monthly-change summary:
| Series | N | Mean | Std | Min | Max |
| --- | --- | --- | --- | --- | --- |
| dDGS10 | 282 | 0.001702 | 0.253691 | -1.080000 | 0.950000 |
| dDFII10 | 282 | 0.000213 | 0.221621 | -0.630000 | 1.010000 |
| dBEI | 282 | 0.001489 | 0.167251 | -0.730000 | 1.030000 |

Monthly-change correlations:
| Pair | Correlation |
| --- | --- |
| corr(dDGS10,dDFII10) | 0.760381 |
| corr(dDGS10,dBEI) | 0.509264 |
| corr(dDFII10,dBEI) | -0.171712 |

## Timing and Look-Ahead
| Check | Value |
| --- | --- |
| pilot nominal rate beta window | 1990-01..2021-12 |
| pilot post_mean window | 2022-01 onward |
| W1-X real/BEI beta window | 2003-01..2021-12 |
| W1-X panel/post window | 2022-01..2024-12 |
| post-2022 enters beta estimation | NO |

## Market Beta
| Check | Value |
| --- | --- |
| source | Fama-French Research Data Factors via pandas_datareader |
| raw unit | percent |
| analysis unit | decimal, Mkt-RF / 100 |
| cached date range | 1985-01..2026-05 |
| corr(real_beta, mkt_beta) | 0.313060 |
| corr(bei_beta, mkt_beta) | 0.844540 |
| corr(real_beta, bei_beta) | 0.340738 |
| corr(nom_beta_0321, rate_beta_1990_2021) | 0.838631 |

## PASS/FAIL
DATA INTEGRITY PASS
- All required external series are cached locally with cleaned-file hashes.
- Date alignment is explicit: monthly last available observations.
- Rates are documented as percentage points; returns are converted to decimal when raw values are percent-like.
- Beta windows end at 2021-12 and do not use post-2022 information.
- BEI is exactly DGS10 - DFII10 on aligned monthly dates.
