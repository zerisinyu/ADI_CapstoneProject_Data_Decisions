"""Descriptive and bivariate statistics on the young-cohort sample.

These feed both the paper's Results 3.1-3.3 and the web story (cohort gap,
urban-rural gap, fairness-fertility correlations). Functions return plain
dicts/DataFrames so they can be serialized for the site or printed in a notebook.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config


def _cohens_d(a, b):
    """Pooled-SD Cohen's d for the difference (mean_a - mean_b)."""
    return (a.mean() - b.mean()) / np.sqrt((a.std() ** 2 + b.std() ** 2) / 2)


def cohort_distribution(df: pd.DataFrame) -> dict:
    """Ideal-children distribution and mean for Gen Z vs Millennials."""
    out = {}
    label = {"1995+": "Gen Z", "1980-1994": "Millennials"}
    for cohort in ("1995+", "1980-1994"):
        data = df.loc[df["cohort"] == cohort, "ideal_children"].dropna()
        counts = data.value_counts(normalize=True).sort_index()
        out[label[cohort]] = {
            "mean": float(data.mean()),
            "sd": float(data.std()),
            "n": int(len(data)),
            "dist": {int(k): float(v) for k, v in counts.items()},
        }
    genz = df.loc[df["cohort"] == "1995+", "ideal_children"].dropna()
    mill = df.loc[df["cohort"] == "1980-1994", "ideal_children"].dropna()
    out["cohens_d"] = float(_cohens_d(mill, genz))
    return out


def group_means(df: pd.DataFrame, column: str, mapping: dict) -> dict:
    """Mean ideal children + t-test across a binary grouping (e.g. urban/rural)."""
    groups = {}
    series = []
    for value, name in mapping.items():
        data = df.loc[df[column] == value, "ideal_children"].dropna()
        groups[name] = {"mean": float(data.mean()), "sd": float(data.std()), "n": int(len(data))}
        series.append(data)
    t, p = stats.ttest_ind(*series)
    groups["t"], groups["p"] = float(t), float(p)
    return groups


def fairness_correlations(df: pd.DataFrame) -> dict:
    """Pairwise correlations of ideal children with each fairness measure."""
    out = {}
    for var in config.FAIRNESS_VARS:
        common = df[["ideal_children", var]].dropna()
        r, p = stats.pearsonr(common["ideal_children"], common[var])
        out[var] = {"r": float(r), "p": float(p), "n": int(len(common))}
    return out


def overall_summary(df: pd.DataFrame) -> dict:
    """Headline numbers used across the paper, poster, and site."""
    ideal = df["ideal_children"].dropna()
    return {
        "n": int(len(df)),
        "mean_ideal": float(ideal.mean()),
        "pct_zero": float((ideal == 0).mean() * 100),
        "cohort": cohort_distribution(df),
        "by_residence": group_means(df, "urban", {1: "Urban", 0: "Rural"}),
        "by_gender": group_means(df, "female", {0: "Male", 1: "Female"}),
        "correlations": fairness_correlations(df),
    }
