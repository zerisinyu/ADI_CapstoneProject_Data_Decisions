"""Project-wide configuration: paths, constants, variable lists, and palette.

Centralizing these here keeps the analysis modules free of magic strings and
makes the pipeline reproducible regardless of the working directory it is run
from (paths are resolved relative to the repository root, not the caller).
"""
from __future__ import annotations

from pathlib import Path

# --- Paths (resolved relative to repo root, so scripts work from anywhere) ---
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
SITE_DATA_DIR = ROOT / "site" / "data"

RAW_DATA = DATA_DIR / "CGSS2023.csv"

# --- Reproducibility ---
SEED = 2025
M_IMPUTATIONS = 20

# --- Model specification ---
DV = "ideal_children"
FAIRNESS_VARS = ["general_fairness", "meritocracy_index", "income_fairness"]
CONTROL_VARS = [
    "age", "female", "education", "married", "urban", "urban_hukou",
    "log_income", "n_children",
]
# Variables fed to the imputation model (analysis vars + auxiliaries).
IMPUTATION_VARS = [DV] + FAIRNESS_VARS + CONTROL_VARS

# Continuous variables that get z-scored for standardized coefficients.
CONTINUOUS_VARS = [
    "ideal_children", "general_fairness", "meritocracy_index",
    "income_fairness", "age", "education", "log_income", "n_children",
]

YOUNG_COHORTS = ["1980-1994", "1995+"]

# Human-readable labels used across tables, figures, and the web export.
VAR_LABELS = {
    "general_fairness": "General Fairness",
    "meritocracy_index": "Meritocracy Index",
    "income_fairness": "Income Fairness",
}
# Which fairness dimensions are procedural vs distributive (the paper's thesis).
FAIRNESS_TYPE = {
    "general_fairness": "procedural",
    "meritocracy_index": "procedural",
    "income_fairness": "distributive",
}

# --- Editorial palette (shared by matplotlib figures and the web CSS) ---
PALETTE = {
    "procedural": "#1565C0",   # deep blue  -> significant procedural effects
    "distributive": "#BDBDBD", # muted grey -> the null distributive effect
    "nonsig": "#BDBDBD",
    "urban": "#1565C0",
    "rural": "#2E7D32",
    "male": "#1565C0",
    "female": "#AD1457",
    "zero_neg": "#FBE9E7",
    "zero_pos": "#E8F5E9",
    "ink": "#1A1A2E",
    "axis": "#546E7A",
}


def ensure_dirs() -> None:
    """Create output directories if they do not already exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
