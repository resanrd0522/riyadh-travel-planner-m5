# Riyadh Travel Planner — M5 Evaluation

This project evaluates a **single-agent travel planner for Riyadh**. The planner uses Gemini and local datasets to recommend a hotel, activities, and restaurants. M5 evaluates the baseline planner using fixed travel requests, automated scoring, component-level tests, and saved execution evidence.

The project investigates whether a coordinated multi-agent travel planner can improve itinerary quality and feasibility compared with a single-agent baseline. **This repository documents the M5 baseline evaluation, not the three-agent M6 treatment results.**

## What We Tested

- **20 golden travel requests** covering different trip durations, interests, and budget levels.
- **3 requested seeds** per case: 11, 22, and 33, producing **60 archived runs**.
- The same activity, restaurant, and hotel datasets used in M4.
- End-to-end itinerary outputs and the search tools supporting the planning process.
- Automated scoring, component-level tests, and trajectory-level tool coverage.

The 20 golden cases and their acceptance criteria were reviewed and approved by the project team. See [`reports/golden_contract.json`](reports/golden_contract.json).

The three structured user inputs are:

1. **Trip Duration:** Number of days.
2. **Interests/Preferences:** Selected activity interest categories.
3. **Budget Level:** Low, Medium, or High.

The baseline uses these inputs to select one hotel for the trip and recommend two activities and two restaurants per day.

## M5 Results

The following results are based on the preserved **Baseline V3** evaluation.

| Metric | Average |
| --- | ---: |
| Activity Preference Match (APM) | 93.50% |
| Restaurant Budget Match (RBM) | 96.67% |
| Hotel Budget Match (HBM) | 96.67% |
| Itinerary Feasibility Rate (IFR) | 81.67% |
| Required Tool Coverage (RTC) | 100.00% |

Across the 60 archived runs:

- **58 runs** successfully generated a final JSON plan.
- **49 runs** passed the structural feasibility checks.
- **9 runs** contained repeated activities that caused structural failures.
- **2 runs** failed to produce a valid final JSON plan.

All 60 runs, including failed generations and structurally invalid outputs, are included in the reported averages according to the evaluation protocol.

**Metric limitations:**

- **IFR** evaluates structural feasibility and dataset ID validity. It does not verify actual driving time, opening hours, or booking availability.
- **RTC** evaluates whether the required search tools were requested during the agent trajectory. It does not guarantee successful tool execution or final-answer correctness.
- The requested seeds were passed to the model provider, but their exact effect on generation is not independently confirmed.

For detailed metric definitions, see [`docs/EVALUATION_PROTOCOL.md`](docs/EVALUATION_PROTOCOL.md).

## Verified Offline Evaluation

The saved M5 baseline evidence was independently verified in Google Colab using:

[`notebooks/M5_Baseline_Verification_Clean.ipynb`](notebooks/M5_Baseline_Verification_Clean.ipynb)

The cleaned verification notebook was executed successfully, producing the following results:

| Verification Check | Result |
| --- | --- |
| Automated unit and integration tests | 53/53 passed |
| Test suite exit code | 0 |
| Independent evidence audit | `PASS_EVIDENCE_AUDIT` |
| Archived records verified | 60/60 |
| Successful generations | 58/60 |
| Structurally valid runs | 49/60 |
| Saved summary verification | Passed |
| Historical source fingerprints | 13/13 matched |
| Dataset fingerprints | 3/3 matched |
| Evidence audit exit code | 0 |

The verification was performed **without generating new Gemini responses or modifying the preserved Baseline V3 results**.

### Historical Source Verification

The full-cohort evidence audit requires the historical source versions associated with the archived Baseline V3 experiment.

Two current source files differ from their historical versions:

- `m5eval/evaluate.py`
- `m5eval/experiment.py`

To preserve the current repository while verifying the archived experiment, the cleaned notebook:

1. Loads the original project and datasets.
2. Verifies the SHA-256 fingerprints of the three datasets.
3. Runs the automated test suite.
4. Loads the two historical source files supplied separately.
5. Verifies their SHA-256 fingerprints against the recorded historical versions.
6. Creates an isolated project copy.
7. Restores the two historical files inside that isolated copy only.
8. Runs `scripts/verify_full_cohort.py` against the isolated copy.

The original project source files remain unchanged.

The successful audit confirms **saved-evidence integrity and offline scoring reproducibility**. It does not represent a fresh provider run, provider-side attestation, or proof that every itinerary satisfies real-world travel constraints.

## How to Verify the Saved Results

### Option 1: Google Colab — Verified Workflow

The recommended workflow for reproducing the successful offline verification is:

[`notebooks/M5_Baseline_Verification_Clean.ipynb`](notebooks/M5_Baseline_Verification_Clean.ipynb)

The notebook requires the following external files:

- `riyadh-travel-planner-m5-main.zip` — the project ZIP downloaded from GitHub.
- `riyadh_m4_datasets.zip` — the original M4 dataset archive.
- `evaluate.txt` — the historical `evaluate.py` source file.
- `experiment.txt` — the historical `experiment.py` source file.

The historical files must match the SHA-256 fingerprints specified in the notebook.

The notebook verifies the original datasets, installs the required dependencies, executes the automated tests, creates an isolated historical verification copy, and audits the 60 archived runs.

**No Gemini API key is required for this workflow.**

The external ZIP archives and historical source files are not embedded in the notebook and must be supplied separately.

### Option 2: Local Automated Tests

Use **Python 3.11 or 3.12**.

Place the unchanged original M4 datasets in the `data/` directory:

- `data/activities.csv`
- `data/restaurants.csv`
- `data/hotels.csv`

Then run:

```bash
python -m pip install -r requirements.txt
python scripts/run_checks.py
```

Some optional Gemini SDK tests may be skipped unless the additional dependencies are installed:

```bash
python -m pip install -r requirements-gemini.txt
```

The verified Colab environment used:

| Package | Version |
| --- | --- |
| `google-genai` | 1.30.0 |
| `httpx` | 0.28.1 |
| `pydantic` | 2.14.3 |

In the verified Colab execution, all **53 tests passed**.

### Important Note About Full-Cohort Verification

The following command is the full-cohort evidence verifier:

```bash
python scripts/verify_full_cohort.py
```

However, running it directly against the current repository may fail historical source fingerprint checks because two source files have changed since the archived Baseline V3 experiment.

For the independently verified procedure, use the cleaned Colab notebook, which restores the matching historical versions in an isolated copy before executing the verifier.

Do not replace the current repository source files merely to reproduce the historical audit.

## Main Files and Folders

| Folder or File | What It Contains |
| --- | --- |
| `m5eval/` | Evaluation, scoring, and experiment code |
| `tests/` | Automated component, scoring, integration, and evidence tests |
| `data/` | Original M4 datasets, supplied locally |
| `reports/` | M5 evaluation reports, results, and statistics |
| `evidence/` | Archived run records and tool traces |
| `docs/` | Evaluation protocol and execution instructions |
| `notebooks/M5_Colab_Run.ipynb` | Colab notebook for project execution |
| `notebooks/M5_Baseline_Verification_Clean.ipynb` | Independently tested offline verification notebook |
| `audit/` | Verification records and checksums |
| `scripts/` | Automated checks and evidence verification scripts |

## Reports and Supporting Documentation

The main project documentation includes:

- [M5 Evaluation Report](reports/M5_REPORT.md) — evaluation design, results, rubric mapping, and limitations.
- [Evaluation Protocol](docs/EVALUATION_PROTOCOL.md) — operational metric definitions and scoring rules.
- [Validation Report](reports/FINAL_VALIDATION.md) — automated testing and independent evidence audit results.
- [Results History](reports/README.md) — explanation of archived evaluation versions.
- [LLM Judge Report](reports/llm_judge/JUDGE_REPORT.md) — supplementary LLM-based evaluation and limitations.
- [Colab Runbook](docs/COLAB_RUNBOOK.md) — instructions for running the project.

**Baseline V3 is the primary M5 result. V2 is preserved as historical evidence.**

The supplementary LLM judge evaluation does not replace the primary deterministic scoring metrics.

## Running Gemini Again (Optional)

The saved M5 evaluation can be verified without calling Gemini.

To generate new plans, follow [`docs/COLAB_RUNBOOK.md`](docs/COLAB_RUNBOOK.md) and use:

`notebooks/M5_Colab_Run.ipynb`

Store the Gemini API key in **Colab Secrets** or an environment variable. Never include credentials in GitHub files, notebooks, logs, or archived evidence.

Live generation is disabled by default. Do not execute archived generation notebooks using **Run all** without reviewing their configuration.

New generation runs are separate from the preserved Baseline V3 evidence and should not overwrite the archived results.

## Required Local Datasets

The original M4 datasets are intentionally excluded from this repository package until redistribution permissions are confirmed.

The following unchanged CSV files are required:

- `data/activities.csv`
- `data/restaurants.csv`
- `data/hotels.csv`

Do not replace them with alternative datasets. The verification procedure checks dataset identities and SHA-256 fingerprints.

Without the original files, the full-cohort offline verifier and live generation cannot complete.

## Scope and Limitations

This repository documents the **M5 evaluation of the single-agent baseline**, not a completed comparison against the three-agent treatment.

The reported results are based on 20 golden cases evaluated across three requested seeds.

The automated evaluation measures preference matching, budget-category matching, structural feasibility, and required tool coverage. It does not establish complete real-world itinerary feasibility.

The historical V2 scores remain preserved, although some original V2 outputs are missing.

The cleaned verification notebook confirms the integrity and reproducibility of the saved Baseline V3 evaluation. It does not independently confirm provider-side execution details.

## Submission Rubric Cross-Reference

The project addresses the following M5 evaluation requirements:

| Requirement | Supporting Evidence |
| --- | --- |
| C5.1 — Golden Set | 20 golden cases and documented acceptance criteria |
| C5.2 — Automated Scoring | Deterministic scoring implementation and automated tests |
| C5.3 — End-to-End and Component-Level Evaluation | Itinerary metrics, component tests, and tool-trajectory evaluation |
| C5.4 — Baseline Results Across Three Seeds | 60 archived runs, aggregated metrics, and seed-level statistics |
| Trajectory-Level Metric | Required Tool Coverage (RTC) |

For detailed evidence mapping, see the **Grading rubric evidence map** and **Component-level versus end-to-end evaluation** sections in [`reports/M5_REPORT.md`](reports/M5_REPORT.md).

## Public Release Notes

The original CSV datasets, course PDFs, and historical source notebooks are not redistributed in this package because redistribution permissions have not been established.

Saved evidence may contain model responses and tool traces and should be reviewed before public publication.

Do not commit API keys, credentials, or other sensitive information.

For dataset availability and redistribution details, see PUBLIC_RELEASE_NOTES.md.
