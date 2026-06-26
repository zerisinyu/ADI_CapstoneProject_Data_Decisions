"""Multiple imputation for the split-questionnaire missing data.

Uses scikit-learn's IterativeImputer (BayesianRidge, ``sample_posterior=True``)
to generate M imputed datasets that are later pooled with Rubin's rules. The
logic mirrors the original notebook; the global seed makes it reproducible.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401  (enables import)
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

from . import config


def _clip_and_round(imputed_df: pd.DataFrame) -> pd.DataFrame:
    """Round count/categorical variables and clip all variables to valid ranges."""
    imputed_df["ideal_children"] = imputed_df["ideal_children"].round().clip(0, 10)
    imputed_df["n_children"] = imputed_df["n_children"].round().clip(0, None)
    # Education is recoded to 7 categories (7 = doctorate); clip to the full range
    # so observed master's/doctorate respondents are not truncated to associate.
    imputed_df["education"] = imputed_df["education"].round().clip(1, 7)
    for binary in ["female", "married", "urban", "urban_hukou"]:
        imputed_df[binary] = imputed_df[binary].round().clip(0, 1)
    # Clip each fairness measure to its own valid range:
    # general_fairness 1-5, meritocracy_index 1-2 (mean of two 1-2 items),
    # income_fairness 1-2 (binary). Wider bounds let the imputer leak out of range.
    imputed_df["general_fairness"] = imputed_df["general_fairness"].clip(1, 5)
    imputed_df["meritocracy_index"] = imputed_df["meritocracy_index"].clip(1, 2)
    imputed_df["income_fairness"] = imputed_df["income_fairness"].clip(1, 2)
    return imputed_df


def multiple_impute(df_young: pd.DataFrame,
                    m: int = config.M_IMPUTATIONS,
                    seed: int = config.SEED,
                    verbose: bool = True) -> list[pd.DataFrame]:
    """Return ``m`` imputed datasets restricted to the imputation variables."""
    df_impute = df_young[config.IMPUTATION_VARS].copy()
    np.random.seed(seed)

    imputed_datasets: list[pd.DataFrame] = []
    for i in range(m):
        imputer = IterativeImputer(
            estimator=BayesianRidge(),
            max_iter=50,
            random_state=i,
            sample_posterior=True,  # proper between-imputation variance
        )
        imputed = imputer.fit_transform(df_impute)
        imputed_df = pd.DataFrame(imputed, columns=config.IMPUTATION_VARS, index=df_impute.index)
        imputed_datasets.append(_clip_and_round(imputed_df))
        if verbose and (i + 1) % 5 == 0:
            print(f"  Completed imputation {i + 1}/{m}")

    if verbose:
        print(f"\nCreated {m} imputed datasets "
              f"(remaining missing: {imputed_datasets[0].isnull().sum().sum()})")
    return imputed_datasets
