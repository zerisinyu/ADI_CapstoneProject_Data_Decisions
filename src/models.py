"""Regression models pooled across imputations with Rubin's rules.

Provides the estimation primitives (OLS with HC3 robust SEs, Poisson and
Negative Binomial GLMs, interaction tests) plus a single ``run_all_models``
entry point that returns a structured results dictionary consumed by the
table builders, figures, and the web export.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from . import config


# --- Rubin's rules ---------------------------------------------------------
def rubins_rules_pool(estimates, variances):
    """Pool point estimates and variances across M imputations (Rubin 1987).

    Returns (pooled_estimate, pooled_se, df, fmi).
    """
    estimates = np.asarray(estimates, dtype=float)
    variances = np.asarray(variances, dtype=float)
    m = len(estimates)

    q_bar = estimates.mean()              # pooled point estimate
    u_bar = variances.mean()              # within-imputation variance
    b = estimates.var(ddof=1)             # between-imputation variance
    t = u_bar + (1 + 1 / m) * b           # total variance
    pooled_se = np.sqrt(t)

    if b > 0:
        r = (1 + 1 / m) * b / u_bar       # relative increase in variance
        df = (m - 1) * (1 + 1 / r) ** 2   # Rubin degrees of freedom
        fmi = (r + 2 / (df + 3)) / (r + 1)
    else:
        df, fmi = np.inf, 0.0
    return q_bar, pooled_se, df, fmi


def _pvalue(coef, se, df):
    t_stat = coef / se
    return t_stat, 2 * (1 - stats.t.cdf(abs(t_stat), df=min(df, 1000)))


# --- OLS -------------------------------------------------------------------
def _ols_one(imputed_df, dv, ivs, controls):
    formula = f"{dv} ~ " + " + ".join(ivs + controls)
    model = smf.ols(formula, data=imputed_df).fit(cov_type="HC3")
    results = {
        var: {"coef": model.params[var], "var": model.bse[var] ** 2}
        for var in ivs + controls + ["Intercept"] if var in model.params.index
    }
    return results, model.rsquared, model.nobs


def pool_ols(imputed_datasets, dv, ivs, controls):
    """Run OLS on each imputed dataset and pool the coefficients."""
    all_results, r2_values, nobs = [], [], None
    for imp_df in imputed_datasets:
        res, r2, nobs = _ols_one(imp_df, dv, ivs, controls)
        all_results.append(res)
        r2_values.append(r2)

    pooled = {}
    for var in all_results[0]:
        coef, se, df, fmi = rubins_rules_pool(
            [r[var]["coef"] for r in all_results],
            [r[var]["var"] for r in all_results],
        )
        t_stat, p = _pvalue(coef, se, df)
        pooled[var] = {
            "coef": coef, "se": se, "t": t_stat, "p": p, "df": df, "fmi": fmi,
            "ci_lower": coef - 1.96 * se, "ci_upper": coef + 1.96 * se,
        }
    return pooled, float(np.mean(r2_values)), nobs


def pool_standardized_ols(imputed_datasets, dv, ivs, controls):
    """Pool OLS on z-scored continuous variables for standardized betas."""
    std_datasets = []
    for imp_df in imputed_datasets:
        std = imp_df.copy()
        for var in config.CONTINUOUS_VARS:
            if var in std.columns:
                std[var] = (std[var] - std[var].mean()) / std[var].std()
        std_datasets.append(std)
    return pool_ols(std_datasets, dv, ivs, controls)


# --- Count models (Poisson / Negative Binomial) ----------------------------
def _glm_one(imputed_df, dv, ivs, controls, family):
    y = imputed_df[dv].astype(int)
    X = sm.add_constant(imputed_df[ivs + controls].copy())
    model = sm.GLM(y, X, family=family).fit(cov_type="HC3")
    results = {
        var: {"coef": model.params[var], "var": model.bse[var] ** 2}
        for var in ["const"] + ivs + controls if var in model.params.index
    }
    return results, model.pseudo_rsquared(), model.nobs


def pool_glm(imputed_datasets, dv, ivs, controls, family):
    """Pool a GLM (Poisson/NegBin); coefficients returned as IRRs."""
    all_results, r2_values, nobs = [], [], None
    for imp_df in imputed_datasets:
        res, r2, nobs = _glm_one(imp_df, dv, ivs, controls, family)
        all_results.append(res)
        r2_values.append(r2)

    pooled = {}
    for var in all_results[0]:
        coef, se, df, fmi = rubins_rules_pool(
            [r[var]["coef"] for r in all_results],
            [r[var]["var"] for r in all_results],
        )
        _, p = _pvalue(coef, se, df)
        pooled[var] = {
            "coef": coef, "se": se, "p": p, "fmi": fmi,
            "irr": np.exp(coef),
            "irr_ci_lower": np.exp(coef - 1.96 * se),
            "irr_ci_upper": np.exp(coef + 1.96 * se),
        }
    return pooled, float(np.mean(r2_values)), nobs


def pool_poisson(imputed_datasets, dv, ivs, controls):
    return pool_glm(imputed_datasets, dv, ivs, controls, sm.families.Poisson())


def pool_negbin(imputed_datasets, dv, ivs, controls):
    return pool_glm(imputed_datasets, dv, ivs, controls, sm.families.NegativeBinomial(alpha=1.0))


# --- Interactions & FDR ----------------------------------------------------
def pool_interaction(imputed_datasets, dv, iv, moderator, controls):
    """Test a single iv x moderator interaction, pooled across imputations."""
    int_term = f"{iv}_x_{moderator}"
    estimates, variances = [], []
    for imp_df in imputed_datasets:
        d = imp_df.copy()
        d[int_term] = d[iv] * d[moderator]
        formula = f"{dv} ~ " + " + ".join([iv, moderator, int_term] + controls)
        model = smf.ols(formula, data=d).fit(cov_type="HC3")
        estimates.append(model.params[int_term])
        variances.append(model.bse[int_term] ** 2)
    coef, se, df, _ = rubins_rules_pool(estimates, variances)
    _, p = _pvalue(coef, se, df)
    return coef, se, p


def benjamini_hochberg(pvals):
    """Return FDR-adjusted p-values (Benjamini-Hochberg), preserving input order."""
    pvals = np.asarray(pvals, dtype=float)
    n = len(pvals)
    order = np.argsort(pvals)
    adjusted = np.empty(n)
    adj_sorted = pvals[order] * n / (np.arange(n) + 1)
    for i in range(n - 2, -1, -1):
        adj_sorted[i] = min(adj_sorted[i], adj_sorted[i + 1])
    adjusted[order] = np.minimum(adj_sorted, 1.0)
    return adjusted


def stratify(imputed_datasets, column, value):
    """Subset each imputed dataset where ``column == value``."""
    return [d[d[column] == value].copy() for d in imputed_datasets]


# --- Top-level orchestration ----------------------------------------------
def run_all_models(imputed_datasets, dv=config.DV,
                   fairness_vars=config.FAIRNESS_VARS,
                   control_vars=config.CONTROL_VARS):
    """Run every model in the paper and return a structured results dict."""
    controls_no_gender = [c for c in control_vars if c != "female"]
    controls_no_urban = [c for c in control_vars if c != "urban"]

    main, main_r2, n = pool_ols(imputed_datasets, dv, fairness_vars, control_vars)
    std, _, _ = pool_standardized_ols(imputed_datasets, dv, fairness_vars, control_vars)
    poisson, _, _ = pool_poisson(imputed_datasets, dv, fairness_vars, control_vars)
    negbin, _, _ = pool_negbin(imputed_datasets, dv, fairness_vars, control_vars)

    male, _, n_male = pool_ols(stratify(imputed_datasets, "female", 0), dv, fairness_vars, controls_no_gender)
    female, _, n_female = pool_ols(stratify(imputed_datasets, "female", 1), dv, fairness_vars, controls_no_gender)
    urban, _, n_urban = pool_ols(stratify(imputed_datasets, "urban", 1), dv, fairness_vars, controls_no_urban)
    rural, _, n_rural = pool_ols(stratify(imputed_datasets, "urban", 0), dv, fairness_vars, controls_no_urban)

    interactions = []
    for iv in fairness_vars:
        for moderator in ("female", "urban"):
            mod_controls = [c for c in control_vars if c != moderator]
            coef, se, p = pool_interaction(imputed_datasets, dv, iv, moderator, mod_controls)
            interactions.append({"iv": iv, "moderator": moderator, "coef": coef, "se": se, "p": p})
    fdr = benjamini_hochberg([r["p"] for r in interactions])
    for r, q in zip(interactions, fdr):
        r["p_fdr"] = float(q)

    return {
        "main": main, "main_r2": main_r2, "n": int(n),
        "standardized": std, "poisson": poisson, "negbin": negbin,
        "strata": {
            "male": {"results": male, "n": int(n_male)},
            "female": {"results": female, "n": int(n_female)},
            "urban": {"results": urban, "n": int(n_urban)},
            "rural": {"results": rural, "n": int(n_rural)},
        },
        "interactions": interactions,
    }


# --- Table builders (reproduce the appendix CSVs) --------------------------
def main_results_table(res, fairness_vars=config.FAIRNESS_VARS) -> pd.DataFrame:
    rows = []
    for var in fairness_vars:
        o, s = res["main"][var], res["standardized"][var]
        p, nb = res["poisson"][var], res["negbin"][var]
        rows.append({
            "Variable": var, "OLS_β": o["coef"], "OLS_SE": o["se"], "OLS_p": o["p"],
            "Std_β": s["coef"], "Poisson_IRR": p["irr"], "Poisson_p": p["p"],
            "NegBin_IRR": nb["irr"], "NegBin_p": nb["p"], "FMI": o["fmi"],
        })
    return pd.DataFrame(rows)


def stratified_table(res, fairness_vars=config.FAIRNESS_VARS) -> pd.DataFrame:
    male, female = res["strata"]["male"]["results"], res["strata"]["female"]["results"]
    urban, rural = res["strata"]["urban"]["results"], res["strata"]["rural"]["results"]
    rows = []
    for var in fairness_vars:
        rows.append({
            "Variable": var,
            "Male_β": male[var]["coef"], "Male_p": male[var]["p"],
            "Female_β": female[var]["coef"], "Female_p": female[var]["p"],
            "Gender_Diff": female[var]["coef"] - male[var]["coef"],
            "Urban_β": urban[var]["coef"], "Urban_p": urban[var]["p"],
            "Rural_β": rural[var]["coef"], "Rural_p": rural[var]["p"],
            "Residence_Diff": rural[var]["coef"] - urban[var]["coef"],
        })
    return pd.DataFrame(rows)
