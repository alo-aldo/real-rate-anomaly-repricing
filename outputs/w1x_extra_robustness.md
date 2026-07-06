# W1-X Extra Robustness

Input: `w1x_signal_level.csv` plus local OSAP returns for period concentration checks.

## Baseline
| Spec | N | Coef | t | p |
| --- | --- | --- | --- | --- |
| X2 | 176 | 0.2112 | 4.0648 | 0.0000 |

## Category Collapse
| Spec | N categories | Coef | t | p |
| --- | --- | --- | --- | --- |
| Cat.Economic means | 33 | 0.3509 | 2.0085 | 0.0446 |

## Leave-One-Cat.Economic-Out
| Metric | Value 1 | Value 2 | Value 3 |
| --- | --- | --- | --- |
| coef min/median/max | 0.1748 | 0.2110 | 0.2478 |
| t min/median/max | 3.1382 | 4.0435 | 5.1865 |
| sign flips | 0 |  |  |
| abs(t) < 2 | 0 |  |  |

## Theme Exclusions

Excluded signals for `beta_size_liquidity` (61):
AnnouncementReturn, Beta, BetaFP, BetaLiquidityPS, BetaTailRisk, BidAskSpread, ChAssetTurnover, CoskewACX, Coskewness, DolVol, FirmAgeMom, High52, IdioVol3F, IdioVolAHT, Illiquidity, IndMom, IndRetBig, IntMom, LRreversal, MRreversal, MaxRet, Mom12m, Mom12mOffSeason, Mom6m, Mom6mJunk, MomOffSeason, MomOffSeason06YrPlus, MomOffSeason11YrPlus, MomOffSeason16YrPlus, MomRev, MomSeason, MomSeason06YrPlus, MomSeason11YrPlus, MomSeason16YrPlus, MomSeasonShort, MomVol, NetDebtPrice, OptionVolume1, OptionVolume2, Price, PriceDelayRsq, PriceDelaySlope, PriceDelayTstat, RIO_Turnover, RealizedVol, ResidualMomentum, ReturnSkew, ReturnSkew3F, STreversal, ShareVol, Size, TrendFactor, VolMkt, VolSD, VolumeTrend, betaVIX, retConglomerate, std_turn, zerotrade12M, zerotrade1M, zerotrade6M

Excluded signals for `lowvol_lottery` (22):
BetaTailRisk, CoskewACX, Coskewness, DolVol, ForecastDispersion, IdioVol3F, IdioVolAHT, MaxRet, MomVol, OptionVolume1, OptionVolume2, RIO_Volatility, RealizedVol, ReturnSkew, ReturnSkew3F, ShareVol, VarCF, VolMkt, VolSD, VolumeTrend, betaVIX, std_turn

Excluded signals for `rd_intangible_growth` (31):
AdExp, AssetGrowth, BrandInvest, ChAssetTurnover, ChInvIA, CitationsRD, EarningsConsistency, EarningsStreak, EarningsSurprise, GrAdExp, GrLTNOA, GrSaleToGrInv, GrSaleToGrOverhead, IntanBM, IntanCFP, IntanEP, IntanSP, InvGrowth, MeanRankRevGrowth, NumEarnIncrease, OrderBacklog, OrgCap, RD, RDIPO, RDS, RDcap, RevenueSurprise, SurpriseRD, fgr5yrLag, grcapx, grcapx3y

Excluded signals for `momentum_reversal` (44):
AnalystRevision, ChangeInRecommendation, ConsRecomm, CustomerMomentum, DownRecomm, EarningsStreak, EarningsSurprise, FirmAgeMom, High52, IndMom, IntMom, IntanBM, IntanCFP, IntanEP, IntanSP, LRreversal, MRreversal, MeanRankRevGrowth, Mom12m, Mom12mOffSeason, Mom6m, Mom6mJunk, MomOffSeason, MomOffSeason06YrPlus, MomOffSeason11YrPlus, MomOffSeason16YrPlus, MomRev, MomSeason, MomSeason06YrPlus, MomSeason11YrPlus, MomSeason16YrPlus, MomSeasonShort, MomVol, REV6, Recomm_ShortInterest, ResidualMomentum, RevenueSurprise, STreversal, ShareVol, SurpriseRD, TrendFactor, UpRecomm, iomom_cust, iomom_supp

| Theme | Excluded | N | Coef | t | p | Killed |
| --- | --- | --- | --- | --- | --- | --- |
| beta_size_liquidity | 61 | 117 | 0.1783 | 3.4099 | 0.0006 | NO |
| lowvol_lottery | 22 | 154 | 0.2522 | 4.8510 | 0.0000 | NO |
| rd_intangible_growth | 31 | 152 | 0.2028 | 3.7789 | 0.0002 | NO |
| momentum_reversal | 44 | 139 | 0.2858 | 5.4433 | 0.0000 | NO |

## 2022 Concentration
| Period | N | Coef | t | p |
| --- | --- | --- | --- | --- |
| post_mean_2022H1 | 176 | 0.4801 | 4.2584 | 0.0000 |
| post_mean_2022H2 | 176 | 0.4335 | 5.5138 | 0.0000 |
| post_mean_2023 | 176 | 0.1564 | 2.7822 | 0.0054 |
| post_mean_2024 | 174 | 0.0209 | 0.3441 | 0.7307 |

Leave-one-month-out for 2022:
| Metric | Value 1 | Value 2 | Value 3 |
| --- | --- | --- | --- |
| coef min/median/max | 0.3621 | 0.4593 | 0.5714 |
| t min/median/max | 4.6623 | 5.6379 | 6.0619 |
| months with abs(t)<2 | 0 |  |  |

## Bootstrap
| Metric | Value |
| --- | --- |
| draws | 2000 |
| skipped | 0 |
| mean coef | 0.2156 |
| bootstrap SE | 0.0522 |
| 2.5 percentile | 0.1172 |
| 97.5 percentile | 0.3213 |
| share(coef > 0) | 1.0000 |

## PASS/FAIL
W1-X EXTRA ROBUSTNESS PASS
- Category collapse coefficient positive: YES
- Bootstrap 95% interval excludes zero: YES
- No single Cat.Economic exclusion flips sign: YES
- Theme exclusions do not all kill result: YES
- 2022 effect not entirely one month by leave-one-month-out: YES
