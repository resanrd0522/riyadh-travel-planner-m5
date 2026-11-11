# Reproducibility and evidence

## Existing artifacts

`audit/import_manifest.json` records checksums for all supplied files and the three extracted datasets. `reference/manifest.json` records checksums for the original course documents used to define the evaluation. The raw results file is also checked against the archived official summary. Twelve frozen function-source fingerprints are verified. The six tool definitions in `m5eval/baseline_tools.py` were extracted without changing their function bodies; `audit/tool_source_provenance.json` records notebook cells and hashes.

The offline evaluation command uses repository-relative paths and does not mount Drive, read credentials, import a model SDK or execute archived notebook cells. Tests use fixtures, frozen CSVs and saved supplementary outputs; optional integration tests use the real SDK with mocked HTTP. The new Colab/live entry point is separate and explicitly guarded. Derived reports are written outside the preserved directories.

## CSV parsing

The historical implementation reference hashes pandas DataFrame JSON, not CSV bytes. In the tested local environment, default pandas CSV float parsing reproduced the activity and hotel fingerprints but not the restaurant fingerprint. Explicit `float_precision='round_trip'` reproduces all three historical canonical hashes. The harness records and checks this policy. This demonstrates a reproducible parse for the saved reference; it does not establish which parser implementation the historical server used. No CSV was modified. The standard-library outcome scorer uses identifier/category/budget strings rather than floating-point coordinates.

## Recovery search

The supplied archive, nested backups, saved notebook outputs and existing Desktop/M5 copies were searched. The independent reviewer inspected 213 Desktop/M5 files including 180 JSON files and three notebook copies. Main notebook cells 123-142 preserve status logs for all 60 V2 pairs but no complete itineraries. Cell 54 has a pilot itinerary, not V2 evidence. Cells 103-104 and the G15 diagnostic JSON retain a truncated diagnostic response, not the full official output. Later supplementary samples remain separate.

Consequently, original V2 outputs cannot be independently rescored from the available records. Historical generation-success flags and aggregate values are reported as recorded evidence. Cost, tokens, latency and exact generated outputs are not reconstructed or estimated. The repeated score equality is not presented as proof of deterministic generation.

## Future approved runs

Do not repeat paid experiments until the project lead approves their scope and cost. Use a new experiment directory/version. Keep V1/V2 immutable and do not use successful replacements to erase failures. Baseline and treatment must use the same frozen protocol.

For each run retain:

- Experiment version, unique run ID, actual case input and requested seed.
- Exact generation model identifier, temperature and other actual generation settings; code commit and dataset byte hashes.
- Actual full prompt/context, response text, parsed itinerary, parse/generation errors and retry attempts.
- Available tool-call messages, including arguments and results. A list of tool names alone is recorded as partial evidence.
- Actual timing, tokens, cost and provider metadata when returned; otherwise explicit null/unavailable values.
- Scorer version, scores and validation errors.

`build_record` accepts already-produced evidence; it does not run the model. `save_record` refuses overwrite. Known credential fields are redacted, and credential-like free text is rejected before file creation. Review raw prompts and responses for personal information and credentials before sharing; automated patterns are only a safeguard. Keep real credentials outside the repository.

Example recording sequence, after an approved generator has returned actual values:

```python
from m5eval.records import build_record, save_record

record = build_record(case, seed, generation, datasets, metadata,
                      experiment_version=experiment_version, run_id=run_id)
save_record(destination, record)
```

The caller must supply actual values, including explicit `generation_success`. A failed generation with a completed itinerary is rejected as contradictory evidence. The adapter and Colab notebook now integrate this recorder. The pinned SDK was tested through a mocked HTTP transport, and the complete local fixture path was tested. That initial development verification made no live provider call. It has since been followed by the separately preserved pilot and completed V3 cohort described below. See COLAB_RUNBOOK.md for explicit approval controls and resume rules.

## Review

Inspect the independent review in `audit/OFFLINE_HARNESS_REVIEW.md`. The offline harness can be verified without reproducing the unavailable original model calls. We adopted the case rules, APM policy and RTC definition on 7 November 2026; see `docs/M5_DECISIONS.md`. Any course-required assistance disclosure, provider-side seed support and optional qualitative evaluation remain separate checks. Reviews are saved in the repository and do not depend on automatic GitHub review settings. Merging requires project-lead approval.

## Completed V3 evidence

The new baseline-v3-20261107 cohort has all sixty records and journals. The original ZIP is retained byte-for-byte under evidence/cohorts/ and every member's checksum is listed in audit/full_cohort_import_manifest.json. Run `python scripts/verify_full_cohort.py` for independent CSV-based scores, HTTP-text/itinerary linkage, code/data hashes and three-level statistics without model requests. The saved V3 summary is copied unchanged to reports/v3_summary.json. This is a new cohort; the original V2 limitations above remain.

The initial unpaced execution hit a per-minute 429. Subsequent unstarted pairs were paced twelve seconds apart. Neither that failed record nor the later malformed-JSON record was replaced. All outcomes are included in the denominator of sixty. See audit/COHORT_EXECUTION_NOTES.md. Per-run adapter timing excludes scheduling pauses and is not end-to-end throughput. Provider seed behavior and actual billing costs remain unverified.
