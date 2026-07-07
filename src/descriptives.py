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


def extra_findings(df: pd.DataFrame) -> dict:
    """Additional descriptive nuggets used by the data-story website.

    All computed on the raw (pre-imputation) young-cohort sample; each share
    reports its own valid N because of the split-questionnaire design.
    """
    def pct_zero(sub):
        s = sub["ideal_children"].dropna()
        return {"pct": round(float((s == 0).mean() * 100), 1), "n": int(len(s))}

    def mean_n(sub):
        s = sub["ideal_children"].dropna()
        return {"mean": round(float(s.mean()), 2), "n": int(len(s))}

    gf = df["general_fairness"].dropna()
    inc = df["income_fairness"].dropna()
    grad = df.groupby("general_fairness")["ideal_children"].agg(["mean", "count"])

    return {
        "zero_pref": {
            "overall": pct_zero(df),
            "genz": pct_zero(df[df.cohort == "1995+"]),
            "millennial": pct_zero(df[df.cohort == "1980-1994"]),
            "female": pct_zero(df[df.female == 1]),
            "male": pct_zero(df[df.female == 0]),
            "urban": pct_zero(df[df.urban == 1]),
            "rural": pct_zero(df[df.urban == 0]),
        },
        "general_fairness_dist": {
            str(int(k)): round(float(v), 4)
            for k, v in gf.value_counts(normalize=True).sort_index().items()
        },
        "general_fairness_n": int(len(gf)),
        "hardwork_agree_pct": round(float((df["b1811_fair"] == 2).sum() / df["b1811_fair"].notna().sum() * 100), 1),
        "effort_agree_pct": round(float((df["b1814_fair"] == 2).sum() / df["b1814_fair"].notna().sum() * 100), 1),
        "income_fair_pct": round(float((inc == 2).mean() * 100), 1),
        "income_n": int(len(inc)),
        "means": {
            "urban_hukou": mean_n(df[df.urban_hukou == 1]),
            "rural_hukou": mean_n(df[df.urban_hukou == 0]),
            "married": mean_n(df[df.married == 1]),
            "single": mean_n(df[df.married == 0]),
            "college": mean_n(df[df.education >= 5]),
            "no_college": mean_n(df[df.education < 5]),
        },
        "meritocracy_mean_urban": round(float(df.loc[df.urban == 1, "meritocracy_index"].dropna().mean()), 2),
        "meritocracy_mean_rural": round(float(df.loc[df.urban == 0, "meritocracy_index"].dropna().mean()), 2),
        "gradient": [
            {"level": int(k), "mean": round(float(r["mean"]), 2), "n": int(r["count"])}
            for k, r in grad.iterrows()
        ],
    }


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
