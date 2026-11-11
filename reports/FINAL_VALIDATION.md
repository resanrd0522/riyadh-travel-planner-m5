# M5 Validation Record 

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
- Successfully parsed outputs: **58**
- Generation failures: **2**
- Structurally valid runs: **49**

The original Baseline V3 evidence and reported scores were not regenerated during this validation.

## 5. Baseline Metrics

The verified saved baseline summary reports:

| Metric | Mean (%) | Sample SD across three seed means |
|---|---:|---:|
| Activity Preference Match (APM) | 93.50 | 2.89 |
| Restaurant Budget Match (RBM) | 96.67 | 2.89 |
| Hotel Budget Match (HBM) | 96.67 | 2.89 |
| Itinerary Feasibility Rate (IFR) | 81.67 | 2.89 |
| Requested Tool Coverage (RTC) | 100.00 | 0.00 |

RTC is the trajectory-level metric based on recorded tool requests. IFR measures structural itinerary feasibility under the defined scoring rules.

## 6. Independent Cohort Audit

The formal Baseline V3 cohort was independently verified using:

`scripts/verify_full_cohort.py`

Final execution results:

- Exit code: **0**
- Audit status: **PASS_EVIDENCE_AUDIT**
- Expected records: **60**
- Verified records: **60**
- Generation successes: **58**
- Structurally valid runs: **49**
- Source files matching: **13/13**
- Datasets matching: **3/3**
- Saved summary verified: **True**

The audit verified the preserved evidence and independently checked the saved results without making new Gemini generation requests.

### Historical Source Verification

Two source files in the current repository, `m5eval/evaluate.py` and `m5eval/experiment.py`, differed from the SHA-256 fingerprints recorded in the original Baseline V3 experiment manifest.

Their historical versions were recovered from the repository's earlier commit history and verified against the recorded SHA-256 fingerprints.

An isolated verification copy was created using the historical versions of these two files. The independent cohort audit was then executed successfully in that isolated copy.

The current repository source files, original datasets, and preserved Baseline V3 evidence were not modified during this process.

## 7. Validation Scope and Reproducibility

This record documents the November 11 offline test run and independent verification of the previously preserved Baseline V3 evidence.

The validation does not claim that the live experiment was rerun, that the provider independently attested the saved outputs, or that all generated itineraries were feasible.

The original datasets must be restored locally for reproducibility because they are not distributed in the GitHub repository.

The independent evidence audit requires source files matching the historical experiment fingerprints. The current repository revision is not directly fingerprint-compatible with the frozen Baseline V3 manifest; the successful audit used a separate historical-source verification copy.

No additional live Gemini generation requests were made during the validation.
