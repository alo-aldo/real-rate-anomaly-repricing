# Manuscript v2 Audit

## Final Judgment

PASS.

The v2 manuscript is conservative, traceable, and consistent with the W3 defensive robustness evidence. It does not modify prior manuscript versions or verified analysis outputs.

## Mechanical Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Main manuscript word count | PASS | 1,583 words by `Measure-Object -Word` |
| Highlights length | PASS | All four highlights are 58 characters or shorter |
| No Windows absolute paths | PASS | Path scan returned no hits in v2 manuscript files |
| No unresolved placeholder markers | PASS | Placeholder scan returned no hits in v2 manuscript files |
| No untraced numerical claims | PASS | See `manuscript_v2_claim_lint.csv` |

## Claim-Discipline Checks

| Requirement | Result | Notes |
| --- | --- | --- |
| No causal identification claim | PASS | The manuscript uses association, prediction, and regime-break repricing language. |
| No stable monthly real-rate premium claim | PASS | The abstract, Section 3, and conclusion explicitly reject stable month-by-month persistence. |
| No local-rate W2 claim | PASS | W2 is described as U.S. real-rate and BEI shocks used as global regime variables. |
| No definitive BEI risk-appetite claim | PASS | BEI interpretation is described as suggestive and not separately identified. |
| Negative post-2022 panel result present | PASS | Section 3 reports coefficient -0.5937 and t-statistic -2.435. |
| Nominal-rate fragility present | PASS | Introduction and Section 3 report the nominal coefficient weakening after market and volatility controls. |
| W3 results described honestly | PASS | W3 is framed as defensive robustness, not as a new main result. |
| Abstract remains safe | PASS | Abstract unchanged from the locked submission version. |
| Highlights <=85 characters each | PASS | Maximum highlight length is 58 characters. |

## Added W3 Claims

- Pseudo-break placebo: under the same pre-break protocol, 2022 has a real-rate coefficient of 0.1745 with t-statistic 2.99 and is larger than all six 2014-2019 pseudo-break coefficients.
- Generated-regressor bootstrap: first-stage beta uncertainty is addressed with six-month and twelve-month block bootstraps, and both 95 percent intervals remain above zero.
- Multiverse transparency: nominal-rate fragility and the negative monthly panel are classified as limits, while the table finds no unreported contradiction to the narrow regime-break claim.

## Softened Or Preserved Claims

- The v2 manuscript keeps the evidence as predictive and associative rather than causal.
- The negative monthly panel remains a central caveat.
- The international evidence remains framed as exposure to U.S. real-rate regime variables, not local-country real-rate evidence.
- BEI is not equated definitively with risk appetite.

## W3 Results Not Overused

No W3 result was used to broaden the core claim. The placebo sign variation is indirectly disclosed through the reported coefficient range, and the negative panel evidence remains in the main text.
