# Independent Gemini and Colab integration review

Review date: 2026-11-07 (Asia/Riyadh). Verdict: **PASS WITH CONDITIONS** for local implementation and mocked-provider verification. This is not verification of a live Gemini run, hosted Colab behavior, provider seed effectiveness, or completed M5 experimental evidence.

## Scope

Inspected actual `m5eval/generation.py`, `experiment.py`, `demo.py`, `records.py`, `tests/test_integration.py`, `requirements-gemini.txt`, `notebooks/M5_Colab_Run.ipynb`, `scripts/build_colab_notebook.py`, `scripts/smoke_colab.py`, README and Colab runbook. Compared the adapter policy with the frozen baseline prompt, seeded configuration, JSON-safe wrappers and prefix/fence normalization. Builder files were not edited by the reviewer.

## Verification executed

Used the bundled Python 3.12 runtime with the separately installed pinned SDK available through `PYTHONPATH=/private/tmp/m5-gemini-sdk`.

```sh
python3 -m unittest discover -s tests
python3 scripts/smoke_colab.py
```

- **49 tests passed, none skipped** with `google-genai==1.30.0` and `httpx.MockTransport`. SDK tests replace socket connection creation with a failure guard; they use synthetic keys and mocked responses, not real credentials/provider requests.
- The notebook smoke check executed all seven default code cells locally, including the 49-test suite, preserved-artifact verification, offline report rebuild and fixture demonstration. No live backend was constructed. Both live approval branches stayed off; the key-reading function was defined but not invoked. Upload, installation and download switches also stayed off.
- The clean notebook has 14 cells, null execution counts, empty saved code outputs and default-off live flags. This establishes local execution of its default path, not a hosted Colab session or the dependency-install/upload branches.
- Exact prompt parity is tested against the archived prompt expression for all 20 golden cases. Original tool names, signatures and defaults 30/10/5 are retained. Per-instance tool namespaces avoid mutating baseline globals.
- Actual SDK mock tests exercise automatic tool calls, HTTP request/response evidence, original/normalized text, provider history, zero-score parse failures, bounded 503 retries, 404 without model fallback, request-cap exhaustion, key redaction, final-attempt coverage and recovered-retry continuation.
- Resume tests verify that completed records are reused without generating again, while incomplete, changed-identity and checksum-mismatched runs are blocked. Storage-boundary regression rejects a final version-directory symlink into preserved source.

## Findings raised and corrected

1. **P2 — stale terminal error after retry recovery.** A mocked 503 followed by a valid 200 response previously left `generation_error.code=503` in a successful record and prematurely stopped the batch. The adapter now clears terminal provider error on a received parseable response, preserves earlier errors in attempt/journal evidence, assigns a separate ParseError when appropriate, and batch stopping depends on failed generation. The new regression confirms two requested runs complete after the first recovers.
2. **P2 — final version-directory symlink bypass.** Resolving only the destination before appending a version allowed a symlink version directory to redirect writes into protected storage. The complete destination/version path is now resolved before preservation checks, and the regression confirms rejection before writing.
3. Direct generator entry now enforces frozen temperature zero, matching Experiment settings validation.
4. Requested function names and executed wrapper calls are now separate. RTC uses names observed in the final attempt's first-candidate HTTP response bodies. Bad-argument requested calls therefore do not disappear merely because a wrapper did not execute. Earlier attempts remain in evidence but cannot inflate final-attempt coverage. Fixtures explicitly use local tool events and remain labelled as fixtures.

No further actionable code findings remained in the reviewed implementation after these fixes. Sanitation and checksums are safeguards, not claims of universal secret detection or cryptographic attestation of provider behavior.

## Policy and evidence assessment

- Model calls require explicit backend approval; notebook pilot/full-experiment switches default to false. No default key read or billable request was observed.
- Prompt text, requested seed, temperature, original search behavior and minimal parser policy are preserved. Strict V3 JSON/day-type validation remains disclosed and versioned. No automatic model substitution occurs.
- HTTP evidence omits request headers and URL queries, records attempted requests rather than billing receipts, and retains available usage metadata without inventing run-total tokens or monetary cost.
- Attempt journals and final records preserve observed evidence. Original response text is subject to documented credential redactions; it is not represented as an untouched secret-bearing archive.
- Completed failures remain part of the cohort. Incomplete runs are blocked rather than silently regenerated. The full summary requires the complete expected record set.
- Live model availability, permissions, timeouts and Colab dependency/runtime compatibility remain external checks. Request caps bound requests, not monetary spend.

## Conditions and remaining scientific limits

1. An explicitly approved, request-capped live pilot is still required to establish actual Gemini availability and hosted execution. No live key or provider request was used in this review.
2. Any new 20-case/three-seed cohort needs separate scope/cost approval, a new version and consistent frozen settings. Do not treat fixture/mock data as model results or mix new results into historical V2.
3. Original V2 itineraries and full argument/result traces remain unrecovered. Their saved aggregate arithmetic can be checked, but those original outputs cannot be independently rescored.
4. The later supplementary samples remain distinct from original V2 generations even when their scores match.
5. Ground-truth acceptance rules still need team human signoff. RTC establishes narrow requested-tool-name coverage, not correct arguments/results or optimal trajectory quality.
6. Optional LLM judging has no completed grades in the supplied artifacts and was not run by this integration review.
7. This review does not approve merging, credential sharing, billing changes or paid experiment execution.

Reference for pinned SDK AFC behavior: [Google python-genai v1.30.0 generation implementation](https://github.com/googleapis/python-genai/blob/v1.30.0/google/genai/models.py#L5682-L5736). A single SDK invocation can perform multiple remote requests; an outer attempt is not synonymous with one provider request.
