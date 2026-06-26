# Data

This analysis uses the **2023 Chinese General Social Survey (CGSS 2023)**.

## What is in this folder

| File | Tracked in git? | Description |
|---|---|---|
| `CGSS2023_Codebook_English.csv` | ✅ yes | English codebook (variable names, labels, value labels) |
| `CGSS_codebook.csv` | ✅ yes | Supplementary codebook |
| `CGSS2023编码表.xlsx` | ✅ yes | Official coding table (Chinese) |
| `CGSS2023居民问卷（入户调查）.pdf` | ✅ yes | Resident questionnaire — household survey |
| `CGSS2023居民问卷（电话调查）.pdf` | ✅ yes | Resident questionnaire — telephone survey |
| `CGSS2023.csv` | ❌ **no** (git-ignored) | Raw respondent-level microdata |
| `CGSS2023.dta` | ❌ **no** (git-ignored) | Same microdata in Stata format |

The **microdata is not redistributed here.** CGSS is released by the survey
provider under terms that require individual registration, so only the public
codebooks and questionnaires are committed. The analysis is fully reproducible
once you obtain the microdata yourself (see below).

## How to obtain the microdata

CGSS is conducted by the National Survey Research Center (NSRC) at Renmin
University of China and distributed through the **China National Survey Data
Archive (CNSDA)**.

1. Go to the CNSDA portal: <http://cnsda.ruc.edu.cn> (or the official CGSS site
   <http://cgss.ruc.edu.cn>).
2. Register for a free account and agree to the data-use agreement.
3. Download the **CGSS 2023** resident survey dataset.
4. Export / save it as `CGSS2023.csv` (UTF-8) and place it at:

   ```
   data/CGSS2023.csv
   ```

   The pipeline reads this path directly (see `src/config.py` → `RAW_DATA`).
   A `.dta` (Stata) copy may also be placed at `data/CGSS2023.dta`; it is not
   required by the Python pipeline.

Once the file is in place:

```bash
make install   # install pinned dependencies
make all       # reproduce tables, figures, and web data
```

## Key variables used

The analysis derives its measures from these raw CGSS items (full details in the
codebook). Recoding logic lives in `src/data_prep.py`.

| Concept | Raw item(s) | Notes |
|---|---|---|
| Ideal number of children (DV) | `a371` | valid range 0–10 |
| General social fairness | `a35` | 1–5 scale (higher = fairer) |
| Meritocracy index | `b1811`, `b1814` | mean of two effort-reward items, recoded so higher = stronger belief (range 1–2) |
| Income fairness | `b1810` | binary, recoded higher = fairer (1–2) |
| Age | `a3a` (birth year) | `2023 − a3a` |
| Sex | `a2` | recoded to `female` |
| Education | `a7a` | recoded to 7 ordered categories |
| Marital status | `a69` | recoded to `married` |
| Income | `a8a` | log-transformed |
| Residence (urban/rural) | `a25a` | |
| Hukou type | `a18` | |
| Number of children | `a681`, `a682` | sons + daughters |

## Citation

If you use CGSS data, cite the survey per the provider's requirements, e.g.:

> Chinese General Social Survey (CGSS) 2023. National Survey Research Center,
> Renmin University of China.
