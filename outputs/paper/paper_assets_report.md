# Paper Assets Report

## Inputs
- `w1x_signal_level.csv`
- `w1_signal_level.csv`
- `w1_summary.csv`
- `w1x_summary.csv`
- `outputs/w1x_extra_robustness.csv`
- `data/external_cache/manifest.csv`

## Key Coefficients
- Preferred real-rate specification: coef=0.2112, t=4.06
- Category-fixed-effects specification: coef=0.1848, t=2.85
- Category-clustered specification: coef=0.2112, t=3.37

## Verification
- Main table coefficients match the verified U.S. evidence summaries up to rounding.
- Robustness entries are read from the verified extra robustness CSV.
- No existing research logic or result files were modified.

## Caveat
- The post-2022 monthly panel interaction remains negative: b(real_beta x dDFII10) = -0.5937, t = -2.435. Interpret the result as regime-break repricing, not stable month-by-month real-rate exposure persistence.

## Created Outputs
- `outputs\paper\tables\table1_sample_signal_summary.md`
- `outputs\paper\tables\table1_sample_signal_summary.csv`
- `outputs\paper\tables\table2_main.md`
- `outputs\paper\tables\table2_main.csv`
- `outputs\paper\tables\table3_robustness_summary.md`
- `outputs\paper\tables\table3_robustness_summary.csv`
- `outputs\paper\appendix\appendix_bootstrap_summary.md`
- `outputs\paper\appendix\appendix_bottom20_bei_beta.md`
- `outputs\paper\appendix\appendix_bottom20_real_beta.md`
- `outputs\paper\appendix\appendix_leave_one_category_out.md`
- `outputs\paper\appendix\appendix_rotated_signals.md`
- `outputs\paper\appendix\appendix_theme_exclusion_signal_lists.md`
- `outputs\paper\appendix\appendix_top20_bei_beta.md`
- `outputs\paper\appendix\appendix_top20_real_beta.md`
- `outputs\paper\appendix\appendix_bootstrap_summary.csv`
- `outputs\paper\appendix\appendix_bottom20_bei_beta.csv`
- `outputs\paper\appendix\appendix_bottom20_real_beta.csv`
- `outputs\paper\appendix\appendix_leave_one_category_out.csv`
- `outputs\paper\appendix\appendix_rotated_signals.csv`
- `outputs\paper\appendix\appendix_theme_exclusion_signal_lists.csv`
- `outputs\paper\appendix\appendix_top20_bei_beta.csv`
- `outputs\paper\appendix\appendix_top20_real_beta.csv`
- `outputs\paper\figures\fig1_real_beta_vs_post_mean.png`
- `outputs\paper\figures\fig2_period_coefficients.png`
- `outputs\paper\figures\fig3_nominal_vs_decomposed.png`
- `outputs\paper\figures\figA1_bootstrap_distribution.png`
