"""Load CGSS 2023 microdata and construct analysis variables.

All recoding logic is lifted verbatim from the original analysis notebook so
that results are unchanged; it is reorganized into named, documented functions
that the rest of the pipeline (and a thin notebook) can import.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


# --- Recode maps (kept module-level for transparency) ---------------------
EDU_RECODE = {
    1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 4, 8: 4,
    9: 5, 10: 5, 11: 6, 12: 6, 13: 7, 14: np.nan, -3: np.nan,
}
RESIDENCE_RECODE = {1: "Urban", 2: "Urban", 3: "Town", 4: "Rural", -3: np.nan, -2: np.nan}
HUKOU_RECODE = {1: "Rural", 3: "Rural", 2: "Urban", 4: "Urban"}


def load_raw(path=None) -> pd.DataFrame:
    """Read the raw CGSS 2023 CSV."""
    path = path or config.RAW_DATA
    return pd.read_csv(path)


def _assign_cohort(year: float) -> float | str:
    if pd.isna(year) or year < 0:
        return np.nan
    if year < 1965:
        return "Pre-1965"
    if year < 1980:
        return "1965-1979"
    if year < 1995:
        return "1980-1994"
    return "1995+"


def build_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Construct the dependent variable, fairness measures, and controls.

    Returns a copy of ``df`` with all derived columns added.
    """
    df = df.copy()

    # Dependent variable: ideal number of children (valid range 0-10).
    df["ideal_children"] = df["a371"].where((df["a371"] >= 0) & (df["a371"] <= 10), np.nan)

    # --- Fairness measures ---
    df["general_fairness"] = df["a35"].where(df["a35"].between(1, 5), np.nan)

    # Meritocracy index: mean of two effort-reward items, recoded so higher =
    # stronger meritocracy belief (original 1=agree -> 2, 2=disagree -> 1).
    df["b1811_fair"] = np.where(df["b1811"] == 1, 2, np.where(df["b1811"] == 2, 1, np.nan))
    df["b1814_fair"] = np.where(df["b1814"] == 1, 2, np.where(df["b1814"] == 2, 1, np.nan))
    df["meritocracy_index"] = (df["b1811_fair"] + df["b1814_fair"]) / 2

    # Income fairness (binary, higher = fairer).
    df["income_fairness"] = np.where(df["b1810"] == 1, 2, np.where(df["b1810"] == 2, 1, np.nan))

    # --- Controls ---
    df["age"] = 2023 - df["a3a"]
    df.loc[(df["a3a"] < 0) | (df["age"] < 18) | (df["age"] > 100), "age"] = np.nan

    df["female"] = np.where(df["a2"] == 2, 1, np.where(df["a2"] == 1, 0, np.nan))
    df["education"] = df["a7a"].map(EDU_RECODE)
    df["married"] = np.where(df["a69"].isin([2, 3, 4]), 1,
                             np.where(df["a69"].isin([1, 5, 6, 7]), 0, np.nan))

    df["income"] = df["a8a"].where((df["a8a"] >= 0) & (df["a8a"] < 9999996), np.nan)
    df["log_income"] = np.log1p(df["income"])

    df["residence_type"] = df["a25a"].map(RESIDENCE_RECODE)
    df["urban"] = np.where(df["residence_type"] == "Urban", 1,
                           np.where(df["residence_type"].isin(["Town", "Rural"]), 0, np.nan))

    df["hukou_type"] = df["a18"].map(HUKOU_RECODE)
    df["urban_hukou"] = np.where(df["hukou_type"] == "Urban", 1,
                                 np.where(df["hukou_type"] == "Rural", 0, np.nan))

    df["n_sons"] = df["a681"].where(df["a681"] >= 0, np.nan)
    df["n_daughters"] = df["a682"].where(df["a682"] >= 0, np.nan)
    df["n_children"] = df["n_sons"].fillna(0) + df["n_daughters"].fillna(0)
    df.loc[df["n_sons"].isna() & df["n_daughters"].isna(), "n_children"] = np.nan

    df["cohort"] = df["a3a"].apply(_assign_cohort)
    return df


def filter_young(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict to Millennials and Gen Z (born 1980+), the prospective cohorts."""
    return df[df["cohort"].isin(config.YOUNG_COHORTS)].copy()


def prepare_data(path=None) -> pd.DataFrame:
    """End-to-end: load raw data, build variables, return the young-cohort frame."""
    df = load_raw(path)
    df = build_variables(df)
    return filter_young(df)
