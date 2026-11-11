# M5 Validation Record — 11 November 2026

## 1. Automated Test Results

The M5 evaluation harness was tested in Google Colab using Python unittest.

Command:

`python -m unittest discover -s tests -v`

Results:

- Total tests: **53**
- Passed: **53**
- Failed: **0**
- Errors: **0**
- Skipped: **0**
- Exit code: **0**
- Execution time: **8.016 seconds**

The tests covered component behavior, scoring, saved evidence integrity, integration behavior, and mocked Gemini SDK interactions.

The deterministic activity-search test was updated to compare results using `pandas.testing.assert_frame_equal`, preserving exact value and row-order checks while handling matching missing values.

## 2. Test Environment

- Platform: Google Colab
- Gemini SDK: `google-genai==1.30.0`
- HTTPX: `httpx==0.28.1`
- Pydantic: `pydantic==2.14.3`

The automated test suite used local fixtures and mocked HTTP responses. No live Gemini generation requests were required.

## 3. Dataset Integrity

The original activity, restaurant, and hotel CSV files were verified against their recorded SHA-256 hashes.

All three datasets matched their expected hashes.

## 4. Preserved Baseline Evidence

The formal Baseline V3 evidence contains:

- Golden cases: **20**
- Seeds: **11, 22, 33**
- Archived runs: **60**
- Parsed outputs: **58**
- Generation failures: **2**

The original Baseline V3 evidence and reported scores were not regenerated during this validation.

## 5. Baseline Metrics

The saved baseline summary reports:

| Metric | Mean (%) | Sample SD across three seed means |
|---|---:|---:|
| Activity Preference Match (APM) | 93.50 | 2.89 |
| Restaurant Budget Match (RBM) | 96.67 | 2.89 |
| Hotel Budget Match (HBM) | 96.67 | 2.89 |
| Itinerary Feasibility Rate (IFR) | 81.67 | 2.89 |
| Requested Tool Coverage (RTC) | 100.00 | 0.00 |

RTC is the trajectory-level metric based on recorded tool requests.

## 6. Independent Cohort Audit

The independent full-cohort verifier is available at:

`scripts/verify_full_cohort.py`

Its latest execution result should be confirmed separately before recording a new audit pass.

## 7. Validation Scope

This record documents the November 11 offline test run and previously preserved baseline results. It does not claim that the live Baseline V3 experiment was rerun.

The original datasets must be restored locally for reproducibility because they are not distributed in the GitHub repository.
