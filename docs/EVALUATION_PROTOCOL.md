# Evaluation protocol

## Task and controlled comparison

The task is to produce a Riyadh itinerary from duration, selected interest groups and one budget category. The output contains `hotel_id` and `days`; each numbered day contains two activity IDs and two restaurant IDs. There must be one hotel for the whole trip and no repeated activity IDs. Restaurants may repeat: M2 does not prohibit this.

M2 controls agent architecture and task organization. Baseline and treatment must share inputs, CSV bytes, output requirements, scoring version, generation model and parameters, and the same JSON-safety/parser policy. M6 treatment implementation is separate from this M5 harness.

Sources: `reference/approved_m2.pdf`, page 2; `reference/project_milestones.pdf`, M5 row; `reference/grading_rubric.pdf`, C5.1-C5.4. Module 7 slides 7, 9-12, 15, 18-22, 25 and 27 motivate the protocol. The archived notebooks were inspected without executing their cells.

We use Activity Preference Match (APM), Restaurant Budget Match (RBM), Hotel Budget Match (HBM), Itinerary Feasibility Rate (IFR) and Required Tool Coverage (RTC).

## Ground truth

Each case has multiple valid answers. Ground truth consists of eligible place IDs and the rules for a valid itinerary. A case may have several correct itineraries. `reports/golden_contract.json` lists the unchanged 20 cases, their acceptance conditions, eligible candidate counts and APM ceilings. The rules derive from M2 and frozen dataset labels. We adopted these rules for all twenty cases, including G05, G08 and G15. See `docs/M5_DECISIONS.md` for the approval record.

G05 requires ten activity slots but has nine matching unique activities. G08 requires six and has four; G15 requires ten and has eight. Their APM ceilings are 90%, 66.67% and 80%. Keep these cases to test requests with too few matching activities. A valid nonmatching activity can fill a missing slot while preserving structural IFR, so insufficient matching candidates do not prove structural impossibility. Do not drop these cases or change the denominator after observing the outcomes.

## Numeric outcomes

All scores are percentages. Missing or invalid recommendations contribute zero rather than disappearing from the denominator.

| Metric | Numerator | Denominator |
|---|---|---|
| APM | Unique valid matching activity IDs in the first two slots of each requested day | 2 × requested duration |
| RBM | Valid restaurant IDs with the requested budget in the first two slots of each requested day | 2 × requested duration |
| HBM | One valid hotel ID with the requested budget | 1 |
| IFR | Complete itineraries satisfying structural/dataset rules | Number of evaluated itineraries |

The scorer returns a per-itinerary IFR of 0 or 100; its mean is the itinerary feasibility rate. Interest and budget matching are measured separately and do not enter structural IFR. Extra days or extra slots cannot compensate for missing required slots. Structural failures do not erase valid component matches. Day positions determine which recommendation slots count, as in the frozen M5 scorer; wrong numbering separately fails IFR.

IFR does not establish opening hours, routes, transport cost, booking availability or real-world trip feasibility. Budget categories are dataset labels, not a complete SAR cost calculation. The scoring definitions are retained for both architectures even when a case is difficult.

We adopted the acceptance rules for all twenty cases, including G05, G08 and G15. We count each valid matching activity only once in APM and keep the denominator fixed at twice the requested trip duration. Repetition also fails the separate IFR structure check. We use RTC to measure required-tool coverage, not reasoning or answer quality.

If repeated matching activity slots were counted, mean APM on the saved outputs would be 96.67%, rather than 93.50% under the adopted unique-activity rule. This sensitivity check does not replace the primary result.

## Scorer version and repairs

Historical results retain their original version and are never silently replaced. `m5-offline-v3` implements the existing fixed-denominator rules in a portable module and makes these explicit validation repairs:

- Malformed activity IDs, including lists and dictionaries, produce a clean structural failure. The archived validator raises an unhashable-type exception internally; its M5 wrapper catches that exception and assigns zero IFR.
- A day number must be an integer. Python previously accepted `True` or `1.0` as equal to day 1; V3 rejects both for structural validity.
- Raw JSON with duplicate object keys, non-finite constants or invalid syntax fails parsing. Parsed dictionaries cannot expose duplicate source keys, so raw response text must be retained when available.

The cases, metric definitions and scorer were fixed before V3. Response normalization also retains V1-era repairs for a `json` prefix and non-finite tool-result values. These changes do not alter the four metric definitions. All 20 supplementary sample scores match their recorded seed-11 score rows. Any new experiment must record V3 explicitly; this is not a retroactive reclassification of original V2 generations.

## End-to-end, component and process evaluation

End-to-end scoring evaluates all sixty saved V3 records, with failed generations retained, and separately evaluates the twenty later supplementary itineraries. Component evaluation executes the six unchanged search/wrapper definitions extracted from the baseline notebook, checking dataset membership, interest/budget eligibility, candidate counts, uniqueness, default limits and repeatability. Exclusion handling, zero candidates and rejected invalid inputs receive separate tests. These are deterministic tool-contract checks, not measurements of the model's ability to choose arguments.

For each run, recorded required-tool coverage is `100 × |distinct required names observed| / 3`. The required names are `find_activities`, `find_restaurants`, and `find_hotels`. Repeated calls do not increase coverage. The historical label is RTC. Its basis is the saved name sequence; no complete historical call arguments/results are available. For the new V3 cohort, names come from first-candidate HTTP response messages in the final attempt, with every record trace matched to its separate journal. Both failed final generations still have RTC=100%, illustrating its narrow scope. This is a process metric, not tool correctness, optimal order or full trajectory quality.

## LLM judge

Numerical scores are the main evaluation method. The existing judge rubric and prompt are preserved as supplementary work; no completed judge grades are supplied and none were generated during this repair. If used later, freeze the rubric/model/prompt, identify the sample cohort, blind architecture labels, calibrate a sample with human raters, retain failures, and report coverage. Do not generalize grades on later supplementary samples to the original 60 runs. Do not discard structural failures from numeric results when applying qualitative filters.

## Statistics

All 60 expected case/seed/input records are required; missing or duplicate records and invalid scores fail verification. Report sample SD (n-1) separately across 60 run scores, across 20 case means, and across three seed-level means. Also report each case's three-seed spread. No effect of provider seed support is inferred from labels. Identical score means do not prove identical itineraries.
