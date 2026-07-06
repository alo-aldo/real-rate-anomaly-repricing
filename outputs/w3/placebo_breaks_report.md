# W3-A Pseudo-Break Placebo Tests

Design: for each pseudo-break year, estimate real_beta and bei_beta using only data before the break, then regress the next 36-month average return on real_beta, bei_beta, market beta, pre volatility, publication year, and in-sample t-stat.

## Comparison
- Actual 2022 real_beta coefficient: 0.1745
- Actual 2022 t-statistic: 2.9902
- Placebo coefficient range: -0.1488 to 0.0724
- Placebos stronger than 2022: 0 of 6
- 2022 stronger than most placebos: YES
- 2022 top quartile versus placebos: YES
- Any placebo sign flip versus 2022: YES

## Break-Level Results

| Break | Type | N | Coef | t | p | Sign |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2014 | placebo | 183 | 0.0724 | 1.7485 | 0.0804 | positive |
| 2015 | placebo | 183 | 0.0101 | 0.2805 | 0.7791 | positive |
| 2016 | placebo | 183 | 0.0388 | 1.0538 | 0.2920 | positive |
| 2017 | placebo | 183 | -0.0389 | -1.2889 | 0.1974 | negative |
| 2018 | placebo | 183 | -0.1488 | -3.3261 | 0.0009 | negative |
| 2019 | placebo | 183 | -0.1324 | -1.5599 | 0.1188 | negative |
| 2022 | actual | 176 | 0.1745 | 2.9902 | 0.0028 | positive |

Placebo conclusion: 2022 is stronger than most pseudo-breaks under the same pre-break estimation protocol.
