# Real-Rate Exposure and the Repricing of Equity Anomalies

Gibeom An

Independent researcher

Corresponding author: Gibeom An, angibeom0814@gmail.com

## Keywords

Equity anomalies; Real rates; Asset pricing; Factor returns; Regime shifts; Anomaly decay; International validation

## JEL Codes

G12; G11; E43; E44; C58

## Abstract

We study whether the 2022 real-rate regime shift is associated with the repricing of documented equity anomalies. For U.S. anomaly portfolios, we estimate each signal's pre-2022 exposure to real-rate and inflation-expectation shocks and ask whether these exposures predict post-2022 long-short returns. Pre-2022 real-rate exposure predicts post-2022 anomaly performance: in the main U.S. specification the real-rate beta coefficient is 0.2112 with a t-statistic of 4.06. The result remains positive with anomaly-category fixed effects and category-clustered standard errors. In contrast, nominal-rate exposure is fragile once market beta and volatility are included. International tests using developed non-U.S. JKP factor-country returns and the same U.S. real-rate and BEI shocks provide out-of-sample evidence consistent with the U.S. finding: the corresponding coefficient is 0.0624 with a t-statistic of 7.72. A monthly panel test is negative, so the evidence is better interpreted as regime-break repricing than as stable month-by-month real-rate exposure persistence.

## Highlights

- Real-rate beta predicts post-2022 anomaly returns.
- Nominal-rate beta is fragile after market controls.
- Results survive category, bootstrap, and international tests.
- Evidence supports regime-break repricing, not persistence.

## 1. Introduction

The sharp rise in real rates after 2022 offers an informative empirical setting for equity anomalies. If anomalies differ in their exposure to real-rate shocks before the regime change, then the post-2022 cross-section of anomaly returns can show whether those exposures predict subsequent performance. The question is narrow: Pre-2022 real-rate exposure predicts the post-2022 cross-section of anomaly returns.

The answer is yes, but with an important qualification. The evidence is better interpreted as regime-break repricing than as stable month-by-month real-rate exposure persistence. This distinction matters because anomaly returns can move with macro shocks for several reasons. A signal may be exposed to discount-rate news, inflation-expectation news, market risk, publication effects, or implementation conditions. A nominal-rate beta alone mixes these channels. The empirical design therefore decomposes nominal-rate exposure into real-rate and breakeven-inflation components and then tests whether the pre-2022 components predict post-2022 long-short returns.

The main U.S. result is economically direct. Across 176 U.S. signal observations, the real-rate beta coefficient is 0.2112 with a t-statistic of 4.06 after controlling for breakeven-inflation beta, market beta, pre-period volatility, publication year, and the original in-sample t-statistic. The relation remains statistically meaningful after adding Cat.Economic fixed effects, where the real-rate beta t-statistic is 2.85, and under category-clustered standard errors, where the t-statistic is 3.37. These estimates are consistent with anomalies with higher pre-2022 real-rate exposure earning higher post-2022 average returns.

The nominal-rate evidence is deliberately reported rather than hidden. In a simple baseline, nominal-rate exposure is significant, with a coefficient of -0.1607 and a t-statistic of -4.62. Once market beta and pre-period volatility are included, however, the nominal-rate coefficient shrinks to -0.0816 with a t-statistic of -1.37. The contrast is the core identification point: the nominal rate appears to bundle together real-rate, inflation-expectation, and market-risk components, while the real-rate decomposition separates the component that predicts the post-2022 cross-section. The interpretation of BEI exposure as related to inflation-expectation or risk-appetite components is suggestive and not separately identified.

The paper contributes to related literatures. First, it complements work on anomaly decay by showing that post-publication erosion is not the only way documented anomalies change out of sample. Second, it connects anomaly returns to macro-finance work on equity duration and real-rate sensitivity. Third, it uses international factor data as out-of-sample evidence rather than as a local-rate design. The international tests use U.S. real-rate and BEI shocks as global regime variables, not local country-level real-rate shocks.

## 2. Data and empirical design

The U.S. analysis uses documented anomaly long-short returns and signal documentation from Open Asset Pricing (Chen and Zimmermann, 2022) and constructs pre-2022 exposure measures before observing post-2022 performance. Nominal-rate beta is estimated over 1990-01 to 2021-12. Real-rate and breakeven-inflation betas are estimated over 2003-01 to 2021-12, matching the availability of the real-rate series. The outcome is each signal's post-2022 average long-short return, measured from 2022-01 onward. The data-integrity audit confirms that beta windows end in 2021-12 and do not use post-2022 information.

The baseline cross-sectional regression relates post-2022 average returns to pre-2022 real-rate beta and breakeven-inflation beta. The preferred U.S. specification also controls for market beta, pre-period volatility, publication year, and the original in-sample t-statistic. Additional specifications add Cat.Economic fixed effects or cluster standard errors by Cat.Economic category.

The international validation uses JKP monthly value-weighted factor returns for developed non-U.S. countries. After filters, the validation sample contains 3,251 factor-country observations, 22 countries, 153 factors, and 7 themes. The exposure construction mirrors the U.S. design: factor-country returns are related to U.S. real-rate and breakeven-inflation shocks before 2022, and the post-2022 cross-section is then tested out of sample. This design is not local-country real-rate evidence. It asks whether exposure to the U.S. real-rate regime shift is associated with the cross-section of international factor returns measured in the JKP data.

## 3. U.S. evidence

Table 1 shows that real-rate exposure, not nominal-rate exposure, carries the post-2022 cross-section. In the preferred decomposition with market beta and volatility controls, the real-rate beta coefficient is 0.2112 with a t-statistic of 4.06. The breakeven-inflation beta enters separately, and the real-rate coefficient remains the central positive predictor. Adding Cat.Economic fixed effects reduces the coefficient but leaves the real-rate beta t-statistic at 2.85. Clustering standard errors by Cat.Economic category gives a real-rate beta t-statistic of 3.37.

Robustness checks point in the same direction. Aggregating to the category level yields a coefficient of 0.3509 with a t-statistic of 2.01. A signal bootstrap gives a 95 percent interval of [0.1172, 0.3213]. Leave-one-category tests produce no sign flips, and leave-one-month-out checks within 2022 keep the coefficient positive with a minimum t-statistic of 4.66. These checks do not establish a structural asset-pricing model; they show that the cross-sectional result is not mechanically driven by a single category, month, or resampling draw.

In post-2022 monthly panel regressions, the interaction between pre-2022 real-rate beta and contemporaneous real-rate changes is negative. The coefficient is -0.5937 with a t-statistic of -2.435. Therefore the evidence should not be interpreted as stable month-by-month real-rate exposure persistence. The conservative interpretation is regime-break repricing: signals with higher pre-2022 real-rate exposure earned different post-2022 average returns after the level and macro relevance of real rates changed.

## 4. International validation and robustness

The international JKP exercise provides out-of-sample evidence consistent with the U.S. finding. In the developed non-U.S. factor-country sample, the international specification with country fixed effects, market beta, and pre-period volatility produces a real-rate beta coefficient of 0.0624 with a t-statistic of 7.72. Adding theme fixed effects leaves the real-rate beta t-statistic at 6.14. Inference remains positive under country-clustered, factor-clustered, and two-way country/factor clustered standard errors, with t-statistics of 3.63, 5.80, and 3.35.

This evidence should be interpreted carefully. The international tests use U.S. real-rate and BEI shocks as global regime variables, not local country-level real-rate shocks. The validation therefore does not estimate each country's local real-rate exposure. Instead, it asks whether international factor returns line up with exposure to U.S. real-rate and breakeven-inflation shocks around the same regime break. This is a narrower claim than a full local macro-finance test.

Together, the U.S. and international evidence support the same empirical message. A nominal-rate beta is too coarse because it combines real discount-rate news, inflation-expectation news, and market-risk exposure. The real-rate decomposition produces a more robust cross-sectional predictor of post-2022 anomaly performance. The negative monthly panel result prevents a stronger persistence claim, but it does not undermine the regime-break interpretation.

## 5. Conclusion

Pre-2022 real-rate exposure predicts the post-2022 cross-section of equity anomaly returns. The result survives controls for breakeven-inflation exposure, market beta, volatility, publication variables, category fixed effects, clustered inference, category aggregation, bootstrap resampling, and international validation using JKP factor returns. The main qualification is equally important: the evidence does not support stable month-by-month real-rate exposure persistence. It supports a narrower and more defensible claim that the 2022 real-rate regime shift is associated with anomaly-return repricing in proportion to pre-existing real-rate exposure.

## Declaration of Generative AI and AI-Assisted Technologies in the Manuscript Preparation Process

During the preparation of this work, the author used AI-assisted tools, including Claude, OpenAI Codex, and ChatGPT, to assist with code development, reproducibility checks, manuscript drafting, and language editing. After using these tools, the author reviewed and edited the content, verified the empirical outputs against local scripts and cached data, and takes full responsibility for the content of the manuscript.

## References

Chen, A. Y., and Zimmermann, T. (2022). Open source cross-sectional asset pricing. Critical Finance Review 11, 207-264.

Gormsen, N. J., and Lazarus, E. (2023). Duration-driven returns. Journal of Finance 78, 1393-1447.

Jensen, T. I., Kelly, B. T., and Pedersen, L. H. (2023). Is there a replication crisis in finance? Journal of Finance 78, 2465-2518.

McLean, R. D., and Pontiff, J. (2016). Does academic research destroy stock return predictability? Journal of Finance 71, 5-32.
