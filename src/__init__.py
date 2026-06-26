"""CGSS 2023 fairness-and-fertility analysis package.

Pipeline modules:
    config       - paths, constants, variable lists, palette
    data_prep    - load microdata and construct analysis variables
    imputation   - multiple imputation (M=20, Rubin's rules)
    descriptives - descriptive and bivariate statistics
    models       - pooled OLS / Poisson / NegBin, stratified + interaction tests
    figures      - editorial figures driven by the model results
    export_web   - pre-aggregated JSON for the website
"""
