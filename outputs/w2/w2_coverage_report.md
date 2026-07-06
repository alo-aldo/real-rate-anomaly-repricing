# W2 Coverage Report

## Official Data Structure
- Factor returns endpoint: `public/[region]_[theme]_[frequency]_[weight].zip`.
- Baseline file: `[all_countries]_[all_factors]_[monthly]_[vw_cap].zip`.
- Market file: `[all_countries]_[mkt]_[monthly]_[vw_cap].zip`.
- Country development classification: `country_classification.xlsx`, field `msci_development`.
- Factor theme mapping: `factor_details.xlsx`, fields `abr_jkp` and `group`.
- Returns are USD excess returns according to the official JKP data page.

## Target Sample
- Developed non-US countries in classification and factor file: 22.
- Countries: aus, aut, bel, can, che, deu, dnk, esp, fin, fra, gbr, hkg, irl, isr, ita, jpn, nld, nor, nzl, prt, sgp, swe
- Raw factor rows: 2712097
- Raw market rows: 36395
- Estimated factor-country observations after filters: 3251
- Countries after filters: 22
- Factors after filters: 153
- Themes after filters: 7
- Pre window: 2003-01..2021-12, minimum 120 months.
- Post window: 2022-01 onward, minimum 18 months.
- Unmapped factors: 0

## Manifest
| name                      | source_url                                                                                                           | retrieval_timestamp_utc          | path                                                            |   size_bytes | sha256                                                           |
|:--------------------------|:---------------------------------------------------------------------------------------------------------------------|:---------------------------------|:----------------------------------------------------------------|-------------:|:-----------------------------------------------------------------|
| availability              | https://jkpfactors-data.s3.amazonaws.com/public/availability.json                                                    | 2026-07-06T08:19:11.102819+00:00 | data\jkp_cache\availability.json                                |       273362 | 9cf0c7accdc4b393c4f2345d06ccfe12888a0266d73cd0c2bf5f0633b91bcf22 |
| all_countries_all_factors | https://jkpfactors-data.s3.amazonaws.com/public/%5Ball_countries%5D_%5Ball_factors%5D_%5Bmonthly%5D_%5Bvw_cap%5D.zip | 2026-07-06T08:19:45.862344+00:00 | data\jkp_cache\raw_all_countries_all_factors_monthly_vw_cap.zip |     45548226 | c0c68ebfc6122a3b1f6e937fa2e55a55dd869b822e70399a1ae689c054f90d8e |
| all_countries_mkt         | https://jkpfactors-data.s3.amazonaws.com/public/%5Ball_countries%5D_%5Bmkt%5D_%5Bmonthly%5D_%5Bvw_cap%5D.zip         | 2026-07-06T08:19:47.694222+00:00 | data\jkp_cache\raw_all_countries_mkt_monthly_vw_cap.zip         |       544532 | 5e2c34a8e0112cc4e97c8b3bcd5abca82ca794d7d9efdde87dfb3297a37bb935 |
| factor_details            | https://raw.githubusercontent.com/bkelly-lab/jkp-data/main/src/jkp/data/resources/factor_details.xlsx                | 2026-07-06T08:19:48.149844+00:00 | data\jkp_cache\factor_details.xlsx                              |        40330 | 4c579e4dcb93eed0897941d8f5f84e9cc784a2d3fc696be68a29a24e68206141 |
| country_classification    | https://raw.githubusercontent.com/bkelly-lab/jkp-data/main/src/jkp/data/resources/country_classification.xlsx        | 2026-07-06T08:19:48.598867+00:00 | data\jkp_cache\country_classification.xlsx                      |        11702 | d296bc25737592b80afc5558f6f217cb399d37295e1c73585aeea44cee906822 |
