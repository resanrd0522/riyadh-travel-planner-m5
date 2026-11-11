# M5 import audit — 2026-11-06

## Update after course-resource review and offline repairs

The original M2 proposal, project milestones, grading rubric and Modules 6/7 were subsequently located in the course folder and inspected. Unchanged copies and hashes are now in reference/. Earlier statements below about missing assignment documents describe the initial archive-only audit and are superseded by this update; the archive itself still has empty requirement folders.

The new m5-offline-v3 harness, tests, component checks and derived reports live outside source/. Historical V1/V2 files remain unchanged. Python is available through the bundled runtime; the earlier system-Python failure does not prevent the new offline checks. Explicit round-trip CSV float parsing reproduces all three frozen DataFrame hashes. See docs/EVALUATION_PROTOCOL.md, reports/M5_REPORT.md and audit/OFFLINE_HARNESS_REVIEW.md for current status. Original V2 itineraries/full traces remain missing. Ground-truth rules await team signoff; no paid model calls or merges occurred.

## Initial import status
The actual teammate archive is now available and inspected. This replaces the earlier source-availability report. All 75 supplied files, including notebooks, saved outputs and five ZIP files, are preserved byte-for-byte under source/. Three CSV datasets are additionally extracted under data/. No experimental code, metrics, golden cases or historical result files were changed.

Original ZIP: Riyadh_Travel_Planner_M5_Master-20261106T161745Z-1-001.zip
Bytes: 3255489
SHA-256: 192652fd17256d3b50667c406fdbbd3aacbd003bbddcdeadfaa5e58e2f092a43
An unchanged private local copy and extraction are retained outside the import directory. The original archive on the user's Desktop was not modified.

## Security and provenance
Checked top-level and nested ZIP member paths and symlinks before extraction. Inspected 206 file occurrences including nested copies. Pattern scans covered Google/OpenAI/GitHub/AWS key formats, bearer tokens, private-key markers and literal credential assignments, plus sensitive filenames. No matches requiring redaction were found. Notebooks were parsed as data including source, outputs and metadata. This is a documented pattern scan, not a guarantee that every possible credential or sensitive datum is absent.
All imported originals are unchanged: no redactions or output stripping. See import_manifest.json for byte sizes, SHA-256 values, nested members and empty directories. Never commit private_originals/ or the outer ZIP automatically.

Extracted datasets contain 1125 activities, 19345 restaurants and 55 hotels. Their Git blob hashes match the directly inspected M4 repository:
- activities: aafcc75332aa909ca631ff673048fcf5fdfa6ac3
- restaurants: f33be2c18d2a4e324bafc97337fb9e4eb976014d
- hotels: 5145f84d1530d1425e09fa9f996c8eade5c34e9e

The implementation-reference hashes use pandas DataFrame JSON serialization (M5 notebook physical cell 154); they must not be compared directly with file-byte SHA-256 values. Canonical DataFrame-hash reproduction has not been run.

## What your teammate completed
- Main M5 notebook (154 cells) and judge notebook (40 cells), including historical outputs.
- 20 distinct golden input cases, a constraint-based ground-truth feasibility report, numeric scoring functions and 60 V2 case/seed score records.
- V1 archive, V2 configuration and summary, parser and recovery diagnostics, and backup exports.
- 20 later supplementary baseline itineraries with dataset evidence, a judge rubric, prompt and model configurations.
- No saved judge evaluations. Judge notebook cells 32–40 record failed requests, configuration changes and readiness diagnostics. These are historical outputs, not new observations of provider availability.

## CONFIRMED ISSUES
1. Original V1/V2 records omit itineraries and response text. Main notebook physical cells 56 and 84 construct score records without saving the generated itinerary. All 60 V2 records have unique expected case/seed pairs, but recomputing their aggregate arithmetic cannot establish that the recorded scores match the original generated trips.
2. Judge notebook cells 21–23 explicitly generate new supplementary itineraries. They are not recovered original V2 outputs. Matching scores and seed labels do not establish output identity.
3. Frozen validate_itinerary checks ID type but later builds set(all_activities), so a dictionary/list activity ID causes an unhashable-value exception. The M5 score_itinerary_feasibility wrapper catches it and returns zero. This is a static source finding; Python execution was not performed.
4. Tool-name lists support required-tool coverage, not independent verification of tool arguments, outputs or correctness. Coverage is not a full trajectory audit.

## Independently checked saved-record arithmetic
Sample SD uses n-1. Across-run n=60; between-seed SD uses the three seed-level means (n=3).

| Metric | Mean % | Across-run sample SD | Between-seed sample SD |
|---|---:|---:|---:|
| APM | 96.8335 | 8.468349 | 0 |
| RBM | 100 | 0 | 0 |
| HBM | 100 | 0 | 0 |
| IFR | 85 | 36.008474 | 0 |
| RTC (tool coverage) | 100 | 0 | 0 |

These reproduce saved arithmetic, not original-output rescoring. The saved raw-results checksum and all 12 saved function-source checksums match. All 20 inputs and all 60 expected case/seed pairs were checked. Reported successful-generation flags total 60, which is a saved claim, not an independently witnessed execution count.

## Ground-truth limitations
G05 has 9 matching unique activities for 10 required slots; G08 has 4 for 6; G15 has 8 for 10. Maximum matching scores are 90%, 66.67% and 80%. The teammate already documents these limits; preserve these cases and denominators.
This does NOT imply IFR must be zero: the validator permits valid nonmatching activities. The supplementary samples actually repeat activities, producing structural failures. Preference-capacity limits and structural impossibility must remain distinct.

## Independent review
A separate Codex reviewer inspected actual local artifacts and independently implemented scoring for the 20 supplementary itineraries. APM/RBM/HBM/structural IFR match the seed-11 V2 score rows for all 20, and validity flags agree. This verifies supplementary sample calculations only, not identity with the original runs.
No cloud @codex review has been triggered; automatic review settings were not changed. See INDEPENDENT_REVIEW.md and verify_supplementary_samples.mjs for the independent pass and reproducer.

## Remaining evidence gaps
The archive includes EMPTY folders named 01_Requirements_and_Rubric and 02_M4_Baseline (also empty labs/course folders). Official M2 requirements, grading rubric and M4 decision records are not supplied here. The recovered contract comes from repository instructions, Plan M5 Evaluation and the actual reference notebook. Original assignment compliance cannot yet receive a final PASS.
No provider seed-support claim is established by labels or identical score means. Full trace correctness, original-run rescoring and full end-to-end notebook reproducibility remain unverified.

## VERIFICATION TESTS
Executed offline via the bundled Node runtime:
- audit/verify_saved_records.mjs: PASS for 78 imported-file checksums, saved function hashes, raw-results hash, 60 expected case/seed/input records, statistics and preference-capacity checks.
- audit/verify_supplementary_samples.mjs: independent sample-scoring verification (see reviewer report).
For a standard Node installation: node audit/verify_saved_records.mjs and node audit/verify_supplementary_samples.mjs.
No notebook cells, package installers or live experiments were run. Local system Python is unavailable; no setup changes were made.

## SUGGESTED NEXT STEPS
Keep this PR as the auditable original import; do not rewrite historical artifacts. Independently review the diff and the evidence limits. Recover original requirement documents and any original itineraries/traces from existing storage before considering reruns. A subsequent small change can harden malformed-ID handling and improve future logging, with regression tests and explicitly versioned behavior. Do not retroactively alter V1/V2, replace hard cases or treat supplementary outputs as recovered originals.
Paid model calls and merging require the user's approval.

## VERDICT
PASS WITH CONDITIONS for preservation/import. M5 scientific validation remains incomplete because original outputs, full traces and original assignment documents are missing; judge evaluation is unfinished.
