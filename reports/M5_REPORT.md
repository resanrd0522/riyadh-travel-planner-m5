# M5: Evaluation of the Riyadh single-agent travel planner

## Study status

On 7 November 2026, experiment `baseline-v3-20261107` tested twenty fixed cases with seeds 11, 22 and 33, giving sixty run records. The saved records include responses, tool calls, errors and file checksums. Credentials are excluded from the evidence. A separate Python implementation recalculated every score and checked the saved summary against the CSV datasets. All sixty records passed these checks.

The JSON parser accepted 58 responses, and 49 itineraries met the structural rules. One run failed because of a provider quota limit, and another returned invalid JSON. Both failures count in the results for all sixty runs and receive zero for missing outputs. The original V1/V2 results are kept separately. Their missing outputs remain unavailable.

## Purpose and course requirements

M5 defines the evaluation method and measures the single-agent baseline proposed in M2. The planner receives trip duration, interests and a budget category. It must select one hotel and exactly two activities and two restaurants per day, without repeating activities. M6 will compare it with a three-agent system using the same inputs, datasets, model settings and evaluation rules.

The preserved milestone specification, grading rubric, approved M2 and Modules 6/7 establish M5's requirements: at least twenty defensible golden cases, reproducible automated scoring, end-to-end and component evaluation, baseline variation over three seeds, and a trajectory-level metric. LLM judging is supplementary to the four approved numerical outcomes.

We report five measures: Activity Preference Match (APM), Restaurant Budget Match (RBM), Hotel Budget Match (HBM), Itinerary Feasibility Rate (IFR) and Required Tool Coverage (RTC). The first four describe the itinerary; RTC describes tool use during generation.

## Data, golden cases and ground truth

We used the same M4 datasets for all M5 runs. The fixed datasets contain 1,125 activities, 19,345 restaurants and 55 hotels. File checksums match the supplied CSVs and the M4 repository. Reading the CSVs with pandas' round-trip float option also reproduces the saved DataFrame checksums. The M4 files were not changed.

The twenty cases cover trips of one to five days, three budget levels, and single or mixed interests. Each case can have several correct answers. Ground truth therefore consists of the M2 requirements and the eligible places in the datasets. `reports/golden_contract.json` lists the required recommendations, eligible places and maximum possible preference score for each case. We adopted these acceptance rules for all twenty cases, including G05, G08 and G15. The project team reviewed and approved the ground-truth acceptance criteria for all 20 golden cases, as recorded in `reports/golden_contract.json`.
| Case | Matching unique activities | Required slots | Maximum possible APM |
|---|---:|---:|---:|
| G05 | 9 | 10 | 90% |
| G08 | 4 | 6 | 66.67% |
| G15 | 8 | 10 | 80% |

These three cases remain in the evaluation because they test requests with too few matching activities. They do not force IFR to zero: a valid, unique nonmatching activity can fill an otherwise valid plan. The model instead repeated activities in all nine V3 outputs for these cases, so those itineraries failed structural validation. We fixed the cases, metric definitions and scorer before V3. The response normalizer includes repairs introduced during V1.

## Metrics and experimental protocol

We calculate APM (Activity Preference Match) as matching unique activity slots divided by twice the requested trip duration. RBM is restaurant slots matching the requested budget divided by the same required count. HBM is the single hotel's budget match. Missing items count as non-matches. Extra days or slots cannot compensate for missed required slots.

We interpret an activity slot as earning APM credit only when it contains a different, valid place matching an interest. This is the operational interpretation used by the scorer. For example, repeating the same matching activity in both slots of a one-day trip gives APM = 50% and IFR = 0. If repeated matching slots were counted instead, mean APM on the saved outputs would be 96.67%, compared with 93.50% under the adopted rule. We report this as a sensitivity check; the primary scores remain unchanged.

We use the M2 name Itinerary Feasibility Rate (IFR) for the percentage of plans that pass the structural checks: correct day numbering, one valid hotel, exactly two valid activities and restaurants per day, no repeated activities, and IDs present in the appropriate frozen datasets. It does not establish travel times, opening hours, booking availability or physical-route feasibility. APM, RBM and HBM measure interest and budget matches separately.

We use RTC (Required Tool Coverage) as the trajectory metric: distinct requested names among `find_activities`, `find_restaurants` and `find_hotels`, divided by three. For V3, we count the tools requested in the model's first response candidate during its final attempt. Calls from earlier attempts are excluded from this score. The record also lists the tools that actually executed. RTC measures tool coverage; it does not check whether the arguments, recommendations or final answer are correct.

V3 uses `gemini-3.5-flash-lite`, temperature zero, seeds 11/22/33, google-genai 1.30.0, and the original baseline prompt and search tools. Each run allows up to three generation attempts, ten remote calls per attempt and a 30-second timeout per request. The scorer, `m5-offline-v3`, checks strict JSON syntax and integer day numbers. These checks were fixed before V3 and were not relaxed for its failed response. Earlier V1 repairs handled a `json` prefix and converted non-finite tool-result values such as NaN before sending them to the model.

The saved experiment settings and file checksums identify the code, data and inputs used. The full record is described in `docs/REPRODUCIBILITY.md`. We requested the three seed values, but their effect at the provider has not been verified.

Execution began with three-record chunks on the existing free-tier project. After an exhausted per-minute 429 error, execution resumed only unstarted pairs with twelve-second pauses between records. Generation settings remained fixed. A malformed response was inspected and retained without retrying that saved pair. The scheduling change and snapshots are documented in `audit/COHORT_EXECUTION_NOTES.md`. Pauses reduce request bursts but do not guarantee quota availability.

## Primary V3 results

All twenty cases have a record for each of the three seeds. Tables display two decimal places; the saved numerical files retain their original precision. Means use the per-run scores saved by the scorer. The means below include both failed runs. Sample standard deviations (SD) use n−1 and are reported separately across runs, case means and seed means.

| Metric | Mean (%) | Across-run sample SD (n=60) | Across-case-mean sample SD (n=20) | Between-seed-mean sample SD (n=3) |
|---|---:|---:|---:|---:|
| APM | 93.50 | 19.44 | 16.56 | 2.89 |
| RBM | 96.67 | 18.10 | 14.91 | 2.89 |
| HBM | 96.67 | 18.10 | 14.91 | 2.89 |
| IFR | 81.67 | 39.02 | 38.20 | 2.89 |
| RTC | 100.00 | 0.00 | 0.00 | 0.00 |

| Requested seed | APM (%) | RBM (%) | HBM (%) | IFR (%) | RTC (%) |
|---|---:|---:|---:|---:|---:|
| 11 | 91.83 | 95.00 | 95.00 | 80.00 | 100.00 |
| 22 | 91.83 | 95.00 | 95.00 | 80.00 | 100.00 |
| 33 | 96.83 | 100.00 | 100.00 | 85.00 | 100.00 |

The SD across seed means is about 2.89 percentage points for the four output metrics and zero for RTC. The two G07 failures occurred under seeds 11 and 22 and lowered those seed means. This difference cannot be attributed to random seeds alone. Variation between cases and variation between seed means describe different aspects of the results.

In all 58 parsed responses, RBM and HBM were 100%, and APM reached the maximum possible score for each case. These measures therefore have little room to improve on the current cases. M6 may show a clearer difference in avoiding repeated activities and completing outputs reliably. We will keep the shared evaluation rules and report this limitation when interpreting the comparison.

Machine-readable results are in `reports/v3_summary.json` and `reports/full_cohort_audit.json`. The original downloaded ZIP is retained unchanged at `evidence/cohorts/baseline-v3-20261107.zip`, with all 247 file-member checksums in `audit/full_cohort_import_manifest.json`. Its separate pilot folder is excluded from the formal cohort.

## Component and trajectory evidence

All sixty search-tool checks passed. They tested eligibility, filtering, dataset membership, uniqueness, default result counts and repeatability. These checks used 120 offline tool calls. Additional tests check exclusions and cases with no eligible candidates. This evaluates the search components separately from final itinerary scoring.

Replaying the recorded calls against the fixed datasets reproduced all 189 tool results, including calls from earlier attempts. All recommendations in the 58 parsed itineraries appeared in the final attempt's tool results. These checks are recorded in `reports/v3_tool_trace_checks.json`. A separate review repeated the ranking and field checks for all 189 results using an independent CSV implementation. A second script recalculated all scores and statistics without using the main scorer. Technical details are in `audit/FULL_COHORT_REVIEW.md`.

Each run's event log matches its saved record. RTC is 100% even for the two failed final generations: both trajectories requested the required tools but did not deliver a parseable final plan. Tool coverage therefore needs to be reported alongside output quality.

## Component-level versus end-to-end evaluation

Component-level checks assess the three search functions (`find_activities`, `find_restaurants`, `find_hotels`) independently for dataset eligibility, filters, uniqueness, and repeatability; they also replay and verify the saved tool results. The trajectory-level RTC metric measures whether the model **requested** each required tool, not whether its output was correct. End-to-end scoring instead assesses the completed itinerary using APM, RBM, HBM, and structurally defined IFR, with failed generations retained as zero-output runs. These are complementary checks: successful tool calls do not imply a valid final itinerary (as the two failed G07 runs demonstrate). The component checks are offline tests, not separately measured production agent success rates. See `reports/v3_tool_trace_checks.json` and `audit/FULL_COHORT_REVIEW.md`.

## Grading rubric evidence map

| Criterion | Evidence in this submission | Scope / qualification |
|---|---|---|
| C5.1 — Golden set and defensible ground truth | `reports/golden_contract.json`, `docs/M5_DECISIONS.md`, `docs/EVALUATION_PROTOCOL.md` | 20 fixed cases; rule-based eligible-set ground truth; known preference-capacity limits |
| C5.2 — Automated, reproducible scoring | `m5eval/`, `tests/`, `scripts/verify_full_cohort.py`, `reports/v3_summary.json` | Offline recomputation from frozen datasets and saved records; no API key required |
| C5.3 — End-to-end and component-level evaluation | `reports/v3_tool_trace_checks.json`, `audit/FULL_COHORT_REVIEW.md`, primary results above | Search components tested separately; itinerary-level APM/RBM/HBM/IFR; RTC is trajectory coverage |
| C5.4 — Baseline score and variance over three seeds | `reports/v3_summary.json`, `reports/M5_REPORT.md`, `evidence/cohorts/baseline-v3-20261107.zip` | 20 × 3 records; means and sample SD; seed effect not independently verified |

The supplementary LLM-as-a-Judge assessment is additional qualitative evidence, not a replacement for any of C5.1–C5.4.

## Failure analysis and reliability

| Observed outcome | Records | Treatment in the primary analysis |
|---|---:|---|
| Parsed and structurally valid | 49 | Score every required slot and retain full evidence |
| Parsed with repeated activities (G05/G08/G15, each at three seeds) | 9 | Preserve partial matching credit; IFR=0 |
| G07/seed11: terminal HTTP 429 after bounded retries | 1 | Preserve attempts; missing-output metrics=0 |
| G07/seed22: unexpected text prefix before JSON | 1 | Preserve raw text; frozen parser rejects it; missing-output metrics=0 |

The journals contain 132 attempted HTTP requests: 122 responses with status 200, five with 429, four with 503 and one with 504. Some requests succeeded after a retry. HTTP errors and failed runs have different counts because one run can contain several requests. Both failed run records were retained.

Mean recorded adapter time was 5,386.64 ms per run, with a range of 1,275.29–35,178.40 ms. These timings include the adapter's attempts/retry waits but exclude inter-run pacing, setup and download time; they are not end-to-end cohort throughput. Raw observable response metadata sums to 153,718 prompt tokens and 18,339 candidate tokens. These are logged usage counts, not a billing receipt. Currency cost remains null. No billing upgrade or purchase was performed.

## Historical evidence and qualitative material

The original project archive contained 75 source files and three unchanged CSV datasets. These materials are retained in the private project archive but are not redistributed in the GitHub review package. The repository preserves the selected evaluation code, reports, and saved evidence. Historical V2 has sixty score records with matching saved inputs, but its original full itineraries and argument/result traces were not recovered from available backups, notebook outputs or Desktop copies. Its score arithmetic can be checked; the original outputs cannot be independently rescored.

| Historical V2 metric | Recorded mean (%) | Across-run sample SD (n=60) | Between-seed-mean SD (n=3) |
|---|---:|---:|---:|
| APM | 96.83 | 8.47 | 0 |
| RBM | 100 | 0 | 0 |
| HBM | 100 | 0 | 0 |
| IFR | 85 | 36.01 | 0 |
| RTC | 100 | 0 | 0 |

Twenty later supplementary itineraries were independently rescored; all eighty output-metric comparisons agree with recorded seed-11 score rows. Matching scores do not establish identity with the missing original generations. The earlier G01/seed11 pilot is separately preserved and audited, and is not substituted into V3.

The archived qualitative rubric, judge prompt and twenty evidence bundles are preserved. **At the time of the original V3 review (7 November 2026), the initial judge requests had failed and no grades were available.** A subsequent supplementary judge run on 10 November 2026 successfully scored all 58 generated V3 itineraries, including a retry of one judge API failure. The new results are documented in the supplementary section below and in `reports/llm_judge/JUDGE_REPORT.md`. No independent human calibration was carried out. The five primary numerical and trajectory results do not depend on the supplementary judge scores.

## Reproducibility and limitations

We verified the code with 49 tests in the pinned SDK environment. They use saved files and simulated responses, without calling the live model. The notebook's default path was also tested locally. See `README.md` for the commands and `reports/README.md` for the scope of each results file and test log.

Run `python scripts/verify_full_cohort.py` to audit the saved V3 ZIP without any model request. This verifies complete coverage, code/data identities, record checksums, HTTP-text-to-itinerary linkage, trace/journal agreement, independent CSV-based scoring and three-level statistics. Checksums detect changes to the saved files; they do not independently authenticate the provider. The independent review and exact checks are in `audit/FULL_COHORT_REVIEW.md`.

The evaluation uses dataset labels for interests and budget. A structurally valid itinerary may still have practical problems that these datasets cannot reveal. The existing preference-capacity cases and the observed service/parser failures limit interpretation. M6 must preserve the shared evaluation and generation conditions, disclose service scheduling/retries and report failures consistently across architectures. V3's fuller evidence does not retroactively validate V2 or establish a baseline-versus-treatment improvement.

We have adopted the case rules, current APM calculation and RTC definition. The cases, code and sixty saved baseline runs remain unchanged. Before submission, we will check the required file format and complete any course-required attribution and contribution statements. The datasets remain in the private project until their redistribution terms are confirmed. 


## Supplementary LLM judge results (10 November 2026)

An additional **qualitative, supplementary** saved-itinerary evaluation using `gemini-3.1-flash-lite` scored all 58 generated plans on four equally weighted 1–5 criteria (mean 4.522/5). The two baseline generation failures were excluded. This is separate from the five frozen primary metrics and is subject to judge consistency and evidence limitations. Full protocol, results, limitations, and notebook are in [`reports/llm_judge/JUDGE_REPORT.md`](llm_judge/JUDGE_REPORT.md).
