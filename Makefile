# Reproduce the CGSS 2023 fairness-and-fertility analysis.
# Usage:
#   make install   # install pinned dependencies
#   make quick     # fast smoke test (M=3 imputations)
#   make all       # full pipeline: tables, figures, and web data (M=20)

.PHONY: install quick all clean

install:
	python3 -m pip install -r requirements.txt

quick:
	python3 run_analysis.py --quick

all:
	python3 run_analysis.py

clean:
	rm -f outputs/Figure*.png outputs/Figure*.pdf outputs/Appendix_Table_*.csv
	rm -f site/data/*.json
