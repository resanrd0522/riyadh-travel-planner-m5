# Independent formal-cohort review

Review date: 2026-11-07 (Asia/Riyadh).

**Final status: PASS_EVIDENCE_AUDIT for all 60 expected V3 records.** This endorses evidence consistency, independent outcome rescoring and aggregation, not universal itinerary success or provider attestation. The earlier partial checkpoints below are superseded by this final audit.

## Final evidence and verified coverage

The exact supplied archive is preserved as `evidence/cohorts/baseline-v3-20261107.zip`, 901,624 bytes, SHA-256 `920d7dcc64f087f3217012a2c6608d081783eb17598c04a72cab46b643f92ecc`. Its 310 ZIP members include directories; all 247 file-member sizes and hashes match `audit/full_cohort_import_manifest.json`. The separate pilot folder was not included in formal-cohort statistics.

The reviewer independently ran:

```sh
python3 scripts/verify_full_cohort.py evidence/cohorts/baseline-v3-20261107.zip --output reports/full_cohort_audit.json
```

The command completed with exit code 0 and wrote the audit report exclusively. All **60 expected case/seed pairs**, **60 record checksums**, **60 journals**, **13 source/dependency-file hashes** and **three dataset byte hashes** passed. There are no missing or duplicate pairs. All records belong to the unchanged 20-case suite and requested seeds 11/22/33, temperature zero, requested model `gemini-3.5-flash-lite`, frozen generation policy and V3 scorer. The independently recomputed summary matches the supplied saved summary; `reports/v3_summary.json` is byte-identical to that summary in the archive.

**58 records parsed successfully, 49 passed structural IFR, and two generation failures remain in the primary 60-record denominator.** Nine parsed itineraries failed structure. This is a complete observed cohort, not a claim that all tasks succeeded.

## Independently verified final results

All values below use all 60 planned records, including both failures. SD means sample SD with denominator n-1; units are percentage points.

| Metric | Mean (%) | Run SD (n=60) | Case-mean SD (n=20) | Seed-mean SD (n=3) |
|---|---:|---:|---:|---:|
| APM | 93.5001666667 | 19.4403898520 | 16.5599019149 | 2.8867513459 |
| RBM | 96.6666666667 | 18.1020334719 | 14.9071198500 | 2.8867513459 |
| HBM | 96.6666666667 | 18.1020334719 | 14.9071198500 | 2.8867513459 |
| IFR | 81.6666666667 | 39.0204929499 | 38.1977005523 | 2.8867513459 |
| RTC | 100.0000000000 | 0 | 0 | 0 |

Seed-level means, ordered 11/22/33:

- APM: 91.8335%, 91.8335%, 96.8335%.
- RBM/HBM: 95%, 95%, 100%.
- IFR: 80%, 80%, 85%.
- RTC: 100%, 100%, 100%.

Only G07 has nonzero within-case spread in the four outcome metrics. The seed-mean spread reflects its two retained failures; it is not evidence that requested seeds caused stochastic model differences. Equal scores elsewhere do not establish identical generated itineraries.

## Failure and trace inspection

- **G07/seed11:** terminal ProviderFailure/ClientError code 429 after three outer attempts. Five HTTP responses are retained, in attempt/status order: (1,429), (2,200), (2,429), (3,200), (3,429). The final attempt requested the required tools before its terminal error, so narrow name-coverage RTC is 100% while all four output metrics are zero. No replacement run was substituted.
- **G07/seed22:** two HTTP 200 responses, followed by ParseError. The model text has an unexpected non-JSON prefix, which remains in normalized text and is rejected by the frozen parser. The itinerary is absent and all four output metrics are zero; required-tool-name coverage remains 100%. No parser relaxation or silent regeneration was applied.
- **G05, G08 and G15, all three seeds:** the nine parsed structural failures are repeated-activity failures. G05 fills ten slots with nine unique activities and earns APM 90%; G08 fills six slots with four unique activities and earns 66.67%; G15 fills ten slots with eight unique activities and earns 80%. Each has IFR zero. These preference-capacity cases were not removed or renormalized.

An additional independently written standard-library CSV probe reproduced **all 189 recorded successful tool-result lists**, including ranking, identifiers and returned fields, across all attempts. Every recommendation in all **58 parsed itineraries** belonged to the corresponding **final-attempt** returned candidate lists. This probe did not call the builder's search functions.

The reviewer independently counted **132 recorded HTTP responses: 122 status 200, five status 429, four status 503 and one status 504**. Recovered transient errors remain visible; two terminal failed generations must not be confused with the larger number of non-200 HTTP responses. Fifty-four records used one outer attempt, three used two and three used three.

Available usage metadata across 122 responses sums to 153,718 prompt, 18,339 candidate and 172,057 total reported tokens. These are recorded response fields, not independently verified billing quantities; no currency cost is inferred. Recorded adapter wall times have mean 5,386.6404 ms, minimum 1,275.2922 ms and maximum 35,178.4035 ms. Their scope includes per-run work/retry waits but excludes inter-run pacing and UI delays; this is not total cohort throughput or a controlled model-latency benchmark.

No additional model call, key retrieval, frozen-source change or raw-result modification occurred during this final review.

## Earlier partial checkpoints (superseded)

Two overlapping snapshots of `baseline-v3-20261107` were inspected read-only:

- Archive SHA-256 `ca8472c01d7227edd8b6af001b78dc0765ebec3ad4f6dafd9f54fa12479b304f`: 19 completed record bundles, 18 successful parsing flags and one retained G07/seed11 provider failure with code 429.
- Archive SHA-256 `dae83ad4678afaa44f821f96e0bce073ae5bc93547e05b88d71ce26e96d9495a`, computed directly from the preserved ZIP: this 20-record snapshot contains the same 19 records plus G07/seed22, whose frozen parser rejected its response and recorded a ParseError. Eighteen parsing successes and both failed records remain present.

These snapshots overlap; they are not 39 independent runs. The largest reviewed snapshot has **20 of the 60 expected records** and **40 missing pairs**. All 20 available journals match their checksummed final-record traces. The auditor correctly returns `INCOMPLETE` with `statistics: null` for both snapshots.

## Independent auditor implementation

`scripts/verify_full_cohort.py` imports only the Python standard library. It does not import the builder's scorer, statistics implementation, search tools or model SDK, and does not invoke a provider.

The reviewer wrote a separate CSV-based fixed-slot scorer: APM counts unique matching activity identifiers in required slots; RBM counts budget-matching restaurant slots; HBM checks the one hotel; IFR separately checks structure, day numbers, identifier membership, counts and activity uniqueness. Missing/invalid outputs score zero. Final-attempt RTC is independently derived from first-candidate function-call names in actual saved HTTP responses; executed-wrapper names are checked separately.

Mean and SD use explicit independent formulas, `math.fsum(values)/n` and `sqrt(fsum((x-mean)**2)/(n-1))`. Complete-cohort aggregation keeps 60 run values, 20 case means and three seed means separate and includes failed runs. A supplied saved summary is compared with a stated absolute numerical tolerance of 1e-9. Partial cohorts never receive aggregate statistics.

## Checks executed against actual partial evidence

- Manifest identity, all 13 recorded implementation/dependency-file hashes and all three dataset hashes matched the reviewed local artifacts.
- Every available record checksum, request/record/manifest identity, frozen case input, seed, generation policy, source/data map and prompt was checked.
- Journal events equal record traces, event/attempt numbering is consistent, HTTP request and response numbers are unique, and response attempt tags match requests.
- The completed response path links final HTTP 200 first-candidate non-thought text to saved raw text, normalized text, strict parsing and the saved itinerary. Provider-failure records with no completed response are handled separately. The G07/seed22 ParseError remained a failed observation; its prefix was not repaired.
- Independently recomputed APM/RBM/HBM/IFR/RTC agree for all 20 available records. The 429 failure and parser failure are retained; no success-only filtering is performed.
- Directory and original ZIP inputs produce the same per-run audit results. ZIP processing uses temporary storage, bounds member count/expanded size, rejects unsafe paths and symlinks, and selects only the formal baseline root. A separate pilot folder is never merged into cohort statistics.

## Additional verification probes executed

- An actual pilot declaration is rejected as a formal 20-case/three-seed baseline.
- Absolute, parent-traversal, backslash and Windows-drive ZIP paths, plus a symlink member, are rejected before extraction.
- An explicit `--output` partial audit creates a new report and exits with code 2. Output defaults to stdout; existing output files are never overwritten, and evidence/code directories are protected from output writes.
- A temporary copy with an altered APM value and a freshly recomputed record checksum is still rejected by the independent scorer. Raw supplied evidence was not edited.
- Small synthetic function-level tests verified sample-SD arithmetic, separation of aggregation levels and malformed-ID/required-slot behavior. These are unit probes only, not experimental model outputs and not additions to the cohort.

## Scheduling change reviewed

The reviewer inspected the small notebook-builder change that adds 12-second pauses between individually started new records within a chunk. It preserves the client cap, original run settings, saved-failure handling and stop conditions for provider/request-cap failures. It changes no file in the 13-entry frozen implementation/dependency fingerprint map.

The builder reported a post-change local smoke run with **49 tests passing** and all default notebook code cells completing without a live backend. The reviewer inspected the scheduling diff but did **not** independently rerun that post-change 49-test smoke run. The earlier independently executed 49-test integration/smoke verification is documented separately in `COLAB_INTEGRATION_REVIEW.md`.

The operational history must remain visible in the eventual report: the cohort began without this pacing, encountered a 429, then continued with pauses while retaining that failed observation. Per-run generation wall time excludes inter-run pauses; it must not be described as total cohort throughput. No failed pair should be replaced to erase the rate-limit or parse failure.

## Earlier checkpoint verdict and final conditions

At the earlier checkpoint the verdict was **PASS for 20 available records; INCOMPLETE for the formal cohort**. The final 60-record audit above supersedes that coverage limit.

All 60 expected pairs and their complete saved traces have now been audited and both failures remain in the primary denominator. A separate follow-up retry experiment, if later authorized, must not overwrite this cohort or be silently substituted into its results.

The optional LLM judge is not required to finish the core M5 numeric/trajectory evaluation. Human ground-truth signoff remains a submission condition. Checksums establish internal integrity, not cryptographic provider attestation; requested seeds do not verify provider seed effectiveness. No currency cost or billable-token total is inferred. New evidence does not recover original V2 outputs. Model identity is the requested/observed label, not a guarantee of immutable provider weights. Free-tier rate limits and the mid-cohort pacing adjustment are threats to clean architectural attribution in a future M6 comparison and must remain disclosed.

No API key was retrieved, no model request was made, and no frozen implementation, dataset or raw result was modified by this reviewer.
