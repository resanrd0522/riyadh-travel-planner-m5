# Gemini and M5 in Colab

## Current status — 7 November 2026

The hosted V3 cohort is complete: all sixty expected records are saved, including one terminal quota failure and one parse failure. Its independent audit passed, with 58 parsed generations and 49 structurally valid itineraries. The unchanged downloaded ZIP is under evidence/cohorts/; `python scripts/verify_full_cohort.py` audits it without model calls. See reports/M5_REPORT.md and audit/FULL_COHORT_REVIEW.md.

The earlier G01/seed11 pilot is preserved separately and is excluded from the cohort. The original V2 outputs remain missing; V3 does not recover them. Local mock/fixture tests remain development checks, distinct from these actual hosted results. Do not rerun the cohort merely to read its scores.

The steps below describe a separately approved future reproduction. They are not required to inspect the completed evidence. Use a new version for a new experiment; no saved failed pair may be replaced.

## Prepare the notebook

1. Download the current repository development branch using GitHub **Code → Download ZIP**. The teammate's original archive is preserved evidence, not the runnable repository ZIP.
2. Open `notebooks/M5_Colab_Run.ipynb` in Colab.
3. Set `UPLOAD_REPOSITORY_ZIP = True`, run the controls/upload cells and choose the repository ZIP. Paths and symlinks are checked before extraction.
4. Set `INSTALL_DEPENDENCIES = True` for initial setup and run the installation cell. This downloads Python packages but does not call Gemini. Restart the runtime after installation if it already imported a different SDK/NumPy/pandas version, then reload the repository.
5. Keep both live approval flags false. Run the offline checks and fixture demonstration. Fixture output is labelled test data and must never be reported as model experiment results.

Local equivalents:

```sh
python -m pip install -r requirements-gemini.txt
python scripts/run_checks.py
python scripts/smoke_colab.py
```

Without the optional Gemini dependencies, SDK tests are explicitly skipped, not passed. The smoke script executes the default notebook code cells and forbids live-client construction. It does not verify hosted Colab behavior.

## One approved live pilot

Add `GEMINI_API_KEY` through Colab Secrets and enable this notebook's access. Never paste it into a code cell, GitHub or a chat. A local environment variable is supported. The key is read only inside an enabled live branch. Request headers and client objects are never serialized.

The pilot is G01, seed 11, temperature zero, historical model ID `gemini-3.5-flash-lite`. It uses the exact preserved prompt, tool signatures, filters/ranking, limits 30/10/5 and JSON-safe results. Scope: one generation attempt, at most four outbound HTTP attempts and a 30-second timeout per HTTP request. Tool use can require several HTTP requests. These limits bound the number of requests. They do not set a monetary budget or guarantee service availability.

Only after project-lead approval set `APPROVE_LIVE_PILOT = True`. Inspect the actual saved generation status, evaluation, error and journal. A parseable output may still fail IFR; retain it. A 404 stops without choosing another model. A paid tier does not guarantee recovery from a 503 service outage.

Re-running a completed pilot reads the existing record without generating again. An incomplete run requires inspection and a separately approved recovery version. Keep its existing journal when reviewing the interruption.

## New full experiment

The full cohort is a separate V3 experiment on all twenty unchanged cases and seeds 11/22/33. It neither recovers nor overwrites V2. Keep `APPROVE_FULL_EXPERIMENT = False` until scope, cost and comparison policy are approved.

Each default chunk starts at most three new runs, with twelve-second pauses between new records to reduce bursts. Pauses do not guarantee quota availability. Each run allows three outer attempts and ten SDK remote requests per attempt. Outer retries for 429/500/502/503/504 wait 5 and 10 seconds. SDK-internal retries are disabled so every outgoing attempt is recorded. The client/chunk HTTP cap is 90; an exhausted provider error or request cap stops the chunk. These are request limits, not a monetary cap or completion-time guarantee.

Use one chunk/session at a time. Resume validates inputs, settings, evidence mode, source hashes, dependency versions, dataset hashes and completed-record checksums. Saved successes and failures are skipped and retained. Incomplete runs are blocked for review. Changed conditions require a new version.

`Experiment.summary()` requires every expected record. Partial cohorts do not produce a full-baseline summary. Pilot and fixture summaries remain labelled separately. Do not silently combine a new cohort with historical V2 scores.

## Saved evidence

```text
runs/<version>/
  manifest.json
  G01_seed11/
    request.json
    events.jsonl
    record.json
    record.sha256
```

The manifest fixes cases, seeds, generation/scorer policy, source-file hashes, dataset hashes, dependency versions and the commit ID if actually available. A repository ZIP may have no Git metadata; commit ID is then null and source-file hashes remain available. 

The flushed journal retains observed request/response bodies and status, tool arguments/results, attempt numbers and retry waits. It omits request headers and URL queries. Explicit key values and recognizable credential-like provider text are redacted. The final record keeps raw text subject to those redactions, normalized text, parsed itinerary, terminal error, all attempt evidence, available SDK history, wall time and scores. A recovered retry clears the terminal error while preserving the earlier error in its attempt and journal.

Requested function names and executed wrappers are separate. RTC uses model-requested names from the final attempt's first-candidate HTTP responses, consistent with the historical name-coverage interpretation. Earlier abandoned attempts cannot inflate it. Fixtures instead use explicitly labelled local tool events. Names do not establish correct arguments/results.

Raw usage metadata is retained per HTTP response. Currency cost remains null; run-total tokens/cost are not inferred from the last response. Outbound HTTP counts are attempted requests, not billing receipts. Requested seeds are logged; provider seed behavior remains unverified.

Colab local storage is temporary. Inspect and download `runs/` with `DOWNLOAD_RUNS = True` before ending the runtime. Include incomplete journals. The default run folder and evidence ZIP are ignored by Git until deliberately reviewed/imported. Journaling is not a guarantee of recovery from storage failure.

## External checks

No billing purchase, model fallback, LLM judging or merge is performed by this notebook by default. Original V2 outputs remain missing. The current case rules, APM policy and RTC definition were adopted; see `docs/M5_DECISIONS.md`. Submission-format review remains. The completed pilot/cohort are documented above; any future live cohort still needs its own approval.

Implementation references: [Google SDK documentation](https://googleapis.github.io/python-genai/) and [v1.30.0 source](https://github.com/googleapis/python-genai/tree/v1.30.0). The adapter preserves v1.30.0 and explicitly closes its synchronous HTTP client; current SDK examples must not be assumed compatible with that older version.
