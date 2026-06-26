"""Editorial figures, driven by the computed model results.

The original notebook hard-coded coefficient values inside each plotting cell.
Here every figure reads from the ``run_all_models`` results dict, so the paper
figures can never drift from the tables. A single theme keeps the paper, poster,
and website visually consistent.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from . import config

P = config.PALETTE


def apply_theme() -> None:
    """Set matplotlib rcParams to the shared editorial style."""
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#B0BEC5",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "font.size": 11,
        "axes.labelcolor": "#37474F",
        "xtick.color": P["axis"],
        "ytick.color": P["axis"],
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "grid.color": "#CFD8DC",
    })


def _save(fig, name: str) -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(config.OUTPUT_DIR / f"{name}.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")


def _coef_panel(ax, items, x_min, x_max, xlabel="Effect on ideal number of children (β)"):
    """Draw a dot-and-CI panel. ``items`` = list of (label, coef, se, sig, color)."""
    ax.axvspan(x_min, 0, color=P["zero_neg"], alpha=0.4, zorder=0)
    ax.axvspan(0, x_max, color=P["zero_pos"], alpha=0.4, zorder=0)
    ax.axvline(0, color=P["axis"], linewidth=1.2, alpha=0.7, zorder=1)

    y_positions = list(range(len(items) - 1, -1, -1))
    for y, (label, coef, se, sig, color) in zip(y_positions, items):
        lo, hi = coef - 1.96 * se, coef + 1.96 * se
        c = color if sig else P["nonsig"]
        alpha = 1.0 if sig else 0.6
        ax.plot([lo, hi], [y, y], color=c, linewidth=4 if sig else 2.5,
                alpha=alpha, solid_capstyle="round", zorder=3)
        ax.scatter(coef, y, s=320 if sig else 180, color=c, zorder=5,
                   edgecolors="white", linewidths=2.5)
        marker = "***" if sig == 3 else "**" if sig == 2 else "*" if sig else ""
        x_text = (max(hi, coef) + (x_max - x_min) * 0.02) if coef >= 0 else (min(lo, coef) - (x_max - x_min) * 0.02)
        ha = "left" if coef >= 0 else "right"
        ax.annotate(f"{coef:.2f}{marker}", xy=(x_text, y), va="center", ha=ha,
                    fontsize=11, fontweight="bold" if sig else "normal",
                    color=c if sig else "#757575", zorder=6)

    ax.set_yticks(y_positions)
    ax.set_yticklabels([it[0] for it in items], fontsize=11)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.6, len(items) - 0.4)
    ax.set_xlabel(xlabel, labelpad=8)


def _sig_level(p):
    return 3 if p < 0.001 else 2 if p < 0.01 else 1 if p < 0.05 else 0


def figure_main_coefficients(res, name="Figure1_Coefficient_Plot"):
    """Hero chart: procedural vs distributive fairness effects on fertility."""
    items = []
    for var in config.FAIRNESS_VARS:
        r = res["main"][var]
        color = P["procedural"] if config.FAIRNESS_TYPE[var] == "procedural" else P["distributive"]
        items.append((config.VAR_LABELS[var], r["coef"], r["se"], _sig_level(r["p"]), color))
    fig, ax = plt.subplots(figsize=(10, 5))
    _coef_panel(ax, items, -0.15, 0.25)
    ax.set_title("Procedural fairness predicts fertility intentions — distributive fairness does not",
                 fontsize=14, color=P["ink"], pad=14, loc="left", wrap=True)
    ax.legend(handles=[
        Line2D([0], [0], marker="o", color="w", markerfacecolor=P["procedural"],
               markersize=11, label="Significant (p < 0.05)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=P["nonsig"],
               markersize=10, label="Not significant"),
    ], loc="lower right", fontsize=9)
    _save(fig, name)
    return fig


def figure_strata(res, key_a, key_b, title, name):
    """Two-panel stratified comparison (urban/rural or male/female)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    for ax, key in zip(axes, (key_a, key_b)):
        stratum = res["strata"][key]
        color = P.get(key, P["procedural"])
        items = []
        for var in config.FAIRNESS_VARS:
            r = stratum["results"][var]
            items.append((config.VAR_LABELS[var], r["coef"], r["se"], _sig_level(r["p"]), color))
        _coef_panel(ax, items, -0.20, 0.38)
        ax.set_title(f"{key.upper()}  (N = {stratum['n']:,})", color=color, pad=10)
    fig.suptitle(title, fontsize=16, fontweight="bold", color=P["ink"], y=1.02)
    _save(fig, name)
    return fig


def figure_sensitivity(res, name="Figure_Sensitivity_OLS_Poisson"):
    """Robustness: OLS betas (left) vs Poisson IRRs (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    items = [(config.VAR_LABELS[v], res["main"][v]["coef"], res["main"][v]["se"],
              _sig_level(res["main"][v]["p"]), P["procedural"]) for v in config.FAIRNESS_VARS]
    _coef_panel(ax1, items, -0.15, 0.25, xlabel="OLS coefficient (β)")
    ax1.set_title("OLS regression", color=P["procedural"])

    # Poisson IRR panel
    ax2.axvspan(0.85, 1.0, color=P["zero_neg"], alpha=0.4, zorder=0)
    ax2.axvspan(1.0, 1.20, color=P["zero_pos"], alpha=0.4, zorder=0)
    ax2.axvline(1.0, color=P["axis"], linewidth=1.2, alpha=0.7, zorder=1)
    y_positions = list(range(len(config.FAIRNESS_VARS) - 1, -1, -1))
    for y, var in zip(y_positions, config.FAIRNESS_VARS):
        r = res["poisson"][var]
        sig = _sig_level(r["p"])
        c = "#7B1FA2" if sig else P["nonsig"]
        ax2.plot([r["irr_ci_lower"], r["irr_ci_upper"]], [y, y], color=c,
                 linewidth=4 if sig else 2.5, alpha=1.0 if sig else 0.6,
                 solid_capstyle="round", zorder=3)
        ax2.scatter(r["irr"], y, s=320 if sig else 180, color=c, zorder=5,
                    edgecolors="white", linewidths=2.5)
        pct = (r["irr"] - 1) * 100
        ax2.annotate(f"{pct:+.1f}%", xy=(r["irr_ci_upper"] + 0.008, y), va="center",
                     ha="left", fontsize=11, fontweight="bold" if sig else "normal",
                     color=c if sig else "#757575", zorder=6)
    ax2.set_yticks(y_positions)
    ax2.set_yticklabels([config.VAR_LABELS[v] for v in config.FAIRNESS_VARS], fontsize=11)
    ax2.set_xlim(0.88, 1.18)
    ax2.set_ylim(-0.6, len(config.FAIRNESS_VARS) - 0.4)
    ax2.set_xlabel("Incidence rate ratio (IRR)", labelpad=8)
    ax2.set_title("Poisson regression", color="#7B1FA2")

    fig.suptitle("Model robustness: consistent findings across specifications",
                 fontsize=16, fontweight="bold", color=P["ink"], y=1.02)
    _save(fig, name)
    return fig


def generate_all(res):
    """Render and save every figure. Returns the list of figure names written."""
    apply_theme()
    figure_main_coefficients(res)
    figure_sensitivity(res)
    figure_strata(res, "urban", "rural",
                  "Two Chinas: urban residents weigh general fairness, rural residents weigh meritocracy",
                  "Figure2_UrbanRural_Heterogeneity")
    figure_strata(res, "male", "female",
                  "Gendered pathways: men show stronger fairness effects than women",
                  "Figure3_Gender_Heterogeneity")
    plt.close("all")
