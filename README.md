# Riyadh Travel Planner — M5 Evaluation

This project evaluates a **single-agent travel planner for Riyadh**. The planner uses Gemini and local datasets to recommend a hotel, activities, and restaurants. M5 tests the planner with fixed requests and automated scoring.

## What we tested

- **20 travel requests** with different trip lengths, interests, and budget levels.
- **3 requested seeds** per request: 11, 22, and 33 (**60 runs** total).
- The same activity, restaurant, and hotel datasets used in M4 (not redistributed in this public-review package).
- Both the final travel plans and the search tools used to create them.

## M5 results

| Metric | Average |
| --- | ---: |
| Activity Preference Match (APM) | 93.50% |
| Restaurant Budget Match (RBM) | 96.67% |
| Hotel Budget Match (HBM) | 96.67% |
| Itinerary Feasibility Rate (IFR) | 81.67% |
| Required Tool Coverage (RTC) | 100.00% |

Out of 60 runs, **49** plans passed the structural checks, **9** repeated activities, and **2** did not produce a valid final JSON plan. All 60 runs, including the failures, are included in the averages.

**Important:** IFR checks plan structure and dataset IDs. It does **not** verify driving time, opening hours, or booking availability. RTC checks whether the required tools were requested; it does not guarantee a correct final answer.

## How to check the saved results

Use **Python 3.11 or 3.12**. First place the three original M4 datasets in `data/` as described below. Then open a terminal in the main folder and run:

```bash
python scripts/verify_full_cohort.py
```

This verifies the saved 60-run evidence. **No Gemini API key is needed.**

To run the tests:

```bash
python -m pip install -r requirements.txt
python scripts/run_checks.py
```

Some optional Gemini SDK tests are skipped unless you also install `requirements-gemini.txt`. The saved-results check does not need the SDK.

## Main files

| Folder | What it contains |
| --- | --- |
| `m5eval/` | Evaluation and scoring code |
| `tests/` | Automated tests |
| `data/` | Original M4 datasets must be supplied locally; excluded pending redistribution permission |
| `reports/` | M5 report, results, and statistics |
| `evidence/` | Saved run records and tool traces |
| `docs/` | Evaluation rules and run instructions |
| `notebooks/` | Google Colab notebook |
| `audit/` | Verification records and checksums |



For full details, read [`reports/M5_REPORT.md`](reports/M5_REPORT.md). For scoring definitions, read [`docs/EVALUATION_PROTOCOL.md`](docs/EVALUATION_PROTOCOL.md). For earlier results, read [`reports/README.md`](reports/README.md) first: **V3 is the main M5 result; V2 is historical.**

## Running Gemini again (optional)

The saved evaluation can be checked without running the model. If you want to generate new plans, follow [`docs/COLAB_RUNBOOK.md`](docs/COLAB_RUNBOOK.md) and use `notebooks/M5_Colab_Run.ipynb`. Keep your API key in **Colab Secrets** or an environment variable. Do not add it to GitHub. Live generation is disabled by default; do not run archived notebooks using **Run all**.

## Notes

This is the **M5 baseline evaluation**, not the three-agent M6 treatment. The requested seeds were passed to the provider, but their exact effect is not independently confirmed. Historical V2 scores are preserved, although some original V2 outputs are missing.

Public-release precaution: the original CSV datasets, course PDFs, and historical source notebooks are not redistributed in this package because redistribution permissions have not been established. Saved evidence may contain model responses and tool traces; review before publication. Do not commit credentials.

## Submission rubric cross-reference

See the **Grading rubric evidence map** and **Component-level versus end-to-end evaluation** sections of [`reports/M5_REPORT.md`](reports/M5_REPORT.md). Supplementary LLM judge results and limitations are documented in [`reports/llm_judge/JUDGE_REPORT.md`](reports/llm_judge/JUDGE_REPORT.md). The primary V3 metrics and original saved runs remain unchanged.

## Required local datasets (not included)

Copy the **unchanged original M4 CSV files** into `data/activities.csv`, `data/restaurants.csv`, and `data/hotels.csv`. Do not substitute other data: saved evidence verification checks dataset identities and hashes. Without these files, the offline full-cohort verifier and live generation cannot complete. These files are intentionally excluded until redistribution rights are confirmed.

See `PUBLIC_RELEASE_NOTES.md` before publishing.
