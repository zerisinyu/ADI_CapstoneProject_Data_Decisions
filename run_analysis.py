"""Reproduce the full analysis end to end.

    python run_analysis.py            # full pipeline
    python run_analysis.py --quick    # M=3 imputations for a fast smoke test

Outputs:
    outputs/Appendix_Table_MI_MainResults.csv
    outputs/Appendix_Table_MI_Stratified.csv
    outputs/Figure*.{png,pdf}
    site/data/*.json
"""
from __future__ import annotations

import argparse

from src import config, data_prep, descriptives, export_web, figures, imputation, models


def main(quick: bool = False) -> None:
    config.ensure_dirs()
    m = 3 if quick else config.M_IMPUTATIONS

    print("1/5  Preparing data ...")
    df_young = data_prep.prepare_data()
    print(f"     Young-cohort sample: N = {len(df_young):,}")

    print(f"2/5  Multiple imputation (M = {m}) ...")
    imputed = imputation.multiple_impute(df_young, m=m)

    print("3/5  Computing descriptives ...")
    summary = descriptives.overall_summary(df_young)
    print(f"     Mean ideal children = {summary['mean_ideal']:.2f}; "
          f"Gen Z {summary['cohort']['Gen Z']['mean']:.2f} vs "
          f"Millennials {summary['cohort']['Millennials']['mean']:.2f} "
          f"(d = {summary['cohort']['cohens_d']:.2f})")

    print("4/5  Fitting models (OLS / Poisson / NegBin / stratified / interactions) ...")
    res = models.run_all_models(imputed)
    main_tbl = models.main_results_table(res)
    strat_tbl = models.stratified_table(res)
    main_tbl.to_csv(config.OUTPUT_DIR / "Appendix_Table_MI_MainResults.csv", index=False)
    strat_tbl.to_csv(config.OUTPUT_DIR / "Appendix_Table_MI_Stratified.csv", index=False)
    print(main_tbl.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    print("5/5  Rendering figures and web data ...")
    figures.generate_all(res)
    written = export_web.export(res, summary)
    print(f"     Wrote site data: {', '.join(written)}")
    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="Use M=3 imputations for a fast smoke test")
    args = parser.parse_args()
    main(quick=args.quick)
