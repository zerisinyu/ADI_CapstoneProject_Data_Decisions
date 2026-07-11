# Perceived Fairness and Fertility Intentions in China

A capstone research project for the [Applied Data Institute '25](https://equitechfutures.com) cohort, exploring whether perceptions of social fairness are associated with how many children young Chinese adults say they want.

Using the 2023 Chinese General Social Survey (CGSS, N = 4,889 respondents born 1980+), the analysis finds that **procedural fairness** — whether people feel the system is fair and that effort is rewarded — is positively associated with ideal number of children, while **distributive fairness** (perceived income equality) is not. The project also documents a sharp generational gap: Gen Z respondents report an average of 1.22 ideal children compared to 1.79 for Millennials.

These are correlational findings from cross-sectional survey data, not causal claims. The paper discusses limitations in detail.

## Interactive data story

An accompanying scrollytelling website presents the key findings in a more accessible format:

**[Fair Play, Over Fair Pay?](https://zerisinyu.github.io/ADI_CapstoneProject_Data_Decisions/)** — a data-driven narrative exploring why young China is saying no to babies, built with D3.js and Scrollama.

## Summary of findings

| Finding | Detail |
| --- | --- |
| Procedural fairness is associated with fertility intentions | General fairness β = 0.100 (p < 0.001); meritocracy β = 0.118 (p = 0.024) |
| Distributive fairness is not | Income fairness β = −0.031 (n.s.) |
| Generational gap | Gen Z 1.22 vs Millennials 1.79 ideal children (d = 0.56) |
| Urban–rural differences | Urban residents respond to general fairness (β = 0.117); rural to meritocracy (β = 0.201) |
| Gender differences | General fairness effect is stronger for men (0.119) than women (0.076) |

## Methods

- **Sample:** CGSS 2023 respondents born 1980 or later (Millennials + Gen Z).
- **Missing data:** the split-questionnaire design leaves 53–73% missing on fairness items; addressed with multiple imputation (M = 20) pooled via Rubin's rules.
- **Models:** OLS with HC3 robust standard errors; Poisson and Negative Binomial as robustness checks.
- **Heterogeneity:** stratified analyses by gender and urban/rural residence, with Benjamini–Hochberg FDR correction on interaction tests.

## Reproduce

```bash
pip install -r requirements.txt
# Place the CGSS 2023 microdata at data/CGSS2023.csv — see data/README.md
python run_analysis.py          # full pipeline (M = 20)
python run_analysis.py --quick  # smoke test (M = 3)
```

The full pipeline reproduces the appendix tables in `outputs/` to three decimal places.

## Repository structure

```
src/                  Modular analysis pipeline
  config.py             paths, constants, variable lists
  data_prep.py          load CGSS + construct variables
  imputation.py         multiple imputation (M = 20, Rubin's rules)
  descriptives.py       descriptive + bivariate statistics
  models.py             pooled OLS / Poisson / NegBin, stratified, interactions
  figures.py            editorial figures (driven by model results)
  export_web.py         pre-aggregated JSON for the website
run_analysis.py       one-command orchestrator
notebooks/            Narrative notebook
outputs/              Figures + appendix tables
site/                 Interactive data-story website
paper/                Capstone paper (markdown)
data/                 Codebooks + questionnaires (microdata not included)
```

## Data access

The CGSS microdata requires free individual registration and is not redistributed here. Codebooks and questionnaires are included. See [`data/README.md`](data/README.md) for how to obtain the data.

## Citation

If you reference this work, please cite the paper in [`paper/`](paper/ADI2025_CapstoneResearch_Sinyu-2.md) and cite CGSS per the survey provider's requirements.
