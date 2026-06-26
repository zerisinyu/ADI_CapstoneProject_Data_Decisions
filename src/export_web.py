"""Export small, pre-aggregated JSON for the D3 + Scrollama website.

The browser never touches the raw CGSS microdata; it only loads these compact
artifacts derived from the analysis. Run as part of the pipeline so the site
can never drift from the paper.
"""
from __future__ import annotations

import json

from . import config


def _coef_records(results, fairness_vars=config.FAIRNESS_VARS):
    """Serialize a pooled-OLS results dict into web-friendly records."""
    records = []
    for var in fairness_vars:
        r = results[var]
        records.append({
            "variable": var,
            "label": config.VAR_LABELS[var],
            "type": config.FAIRNESS_TYPE[var],
            "coef": round(r["coef"], 4),
            "se": round(r["se"], 4),
            "ci_lower": round(r["ci_lower"], 4),
            "ci_upper": round(r["ci_upper"], 4),
            "p": round(r["p"], 5),
            "significant": bool(r["p"] < 0.05),
        })
    return records


def export(res, summary, site_dir=config.SITE_DATA_DIR):
    """Write coefficients.json, cohort_dist.json, and summary.json."""
    site_dir.mkdir(parents=True, exist_ok=True)

    coefficients = {
        "main": _coef_records(res["main"]),
        "strata": {
            key: {"n": res["strata"][key]["n"],
                  "coefficients": _coef_records(res["strata"][key]["results"])}
            for key in ("urban", "rural", "male", "female")
        },
    }
    (site_dir / "coefficients.json").write_text(json.dumps(coefficients, indent=2))
    (site_dir / "cohort_dist.json").write_text(json.dumps(summary["cohort"], indent=2))
    (site_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    return ["coefficients.json", "cohort_dist.json", "summary.json"]
