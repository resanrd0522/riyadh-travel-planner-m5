# Independent review of supplied Colab pilot evidence

Review date: 2026-11-07 (Asia/Riyadh). Verdict: **PASS WITH CONDITIONS for this one supplied pilot record**. The saved evidence is internally consistent and its itinerary scores reproduce independently. No additional model request was made during this review.

## Evidence and fingerprints

- Supplied experiment: `pilot-v3-20261107`, case G01, seed 11.
- Preserved outer ZIP SHA-256: `8b079582734fc6e09a6d0653a36d746524d67bbcbe3af917aab217af5be18d87`.
- `G01_seed11/record.json` SHA-256: `c9ca1117cb941ef740a01131ef5d5ab91ddb76bb167cd76eff122430403ea501`; this matches `record.sha256`.
- Recomputed manifest identity SHA-256: `f950a15228684cf10f5622c064cc7147f10c0d894d4f43c45b9c3bfaff34b858`; it matches the manifest, request and record metadata.
- All **13 recorded implementation/dependency-file hashes** match the corresponding current `m5_import` files. All **three recorded dataset byte hashes** match the frozen CSV files. The record and manifest agree on their hash maps.
- `code_commit` is null, consistent with a ZIP-based environment; no commit identifier has been invented.

The reviewer read the original copied ZIP/extracted files without changing them. Only this reviewer artifact was written.

## Protocol and request checks

Request, manifest and record agree on a one-day trip, Shopping interest, Low budget, G01 and seed 11. The complete prompt equals the archived baseline prompt expression for this case, its recorded SHA-256 matches, and the first saved HTTP request contains that same prompt.

The evidence records **one outer attempt and two POST requests**, each with HTTP status **200**, targeting `gemini-3.5-flash-lite:generateContent`. Both request bodies explicitly contain temperature zero and seed 11; both saved response bodies report the same model version. Settings retain one outer attempt and the manifest records a four-request client cap. No retry, model fallback or terminal error appears in this pilot.

`record.generation_result.trace` equals all **12 events** in `events.jsonl`, in order, with consecutive event numbers and attempt 1. The journal contains two request/response pairs, three tool calls, three successful tool results, attempt start and final model-response evidence. Request bodies, SDK history, raw final response text, normalized response text and parsed itinerary are retained. Both saved text forms parse to the stored itinerary, and the final HTTP response text equals the saved raw text.

## Independent tool and itinerary verification

The reviewer wrote separate standard-library CSV checks, rather than relying on the builder's scoring functions or trusting the reported numbers.

- Recorded tool calls are `find_hotels(Low, limit=5)`, `find_restaurants(Low, limit=10)` and `find_activities([Shopping], limit=30)`.
- Independent eligibility filtering and sorting by descending numeric rating, descending rating evidence, then ascending identifier reproduce **all 5 hotel, 10 restaurant and 30 activity candidate IDs in order**.
- Returned candidate fields match their frozen dataset records, including numeric values checked at floating-point tolerance.
- The second HTTP request's three function-response result lists equal the recorded local tool-result lists. Requested tool names/arguments agree with the observed calls; omitted limits are accounted for by the original defaults.
- The selected hotel, both activities and both restaurants occur in their corresponding returned candidate lists and frozen datasets.
- The itinerary has exactly one valid hotel, exactly one correctly numbered day, two activities, two restaurants and no repeated activities. Both activities match Shopping; restaurant and hotel budget labels match Low.

| Independently recomputed metric | Result |
|---|---:|
| APM | 100% |
| RBM | 100% |
| HBM | 100% |
| Structural/dataset IFR | 100% |
| Required-tool-name coverage (RTC) | 100% |

All five values agree with the saved record. This IFR establishes structural/dataset validity, not route, opening-hours, booking or real-world feasibility.

## Thought signatures and secret handling

Opaque thought-signature values were not printed or copied into this report. The first model response's function-call content is replayed in the second request. Its signature changes only from standard to URL-safe Base64 representation: decoding both yields **the same 98 bytes**. Function-call content otherwise matches. Thus the recorded signature evidence is preserved semantically; textual Base64 inequality alone is not a corruption finding.

The saved journal omits request headers and URL queries. A read-only scan found no matches for the tested Google/GitHub/OpenAI key, private-key or generic Bearer-token patterns. This is a limited pattern check, not a guarantee against every possible secret. No real API key was retrieved by the reviewer.

## Verdict and limits

**PASS WITH CONDITIONS. No actionable inconsistency was found in this supplied pilot.** It provides independently rescored evidence of one successful G01 seed-11 run through the new generation, recording and scoring path.

- One pilot is not the 20-case, three-seed baseline; it supports no general success-rate, variance or comparative-performance claim.
- Saved evidence labels itself live and contains provider-shaped HTTP data. Local checksums and matching hashes establish internal integrity/provenance consistency, not cryptographic attestation that a provider issued the files.
- The requested seed is recorded. Provider seed effectiveness, reproducibility across fresh calls and model immutability were not tested.
- Per-response usage metadata and recorded elapsed time are preserved evidence, not independently verified billing or a latency benchmark. No cost or billable-token total is inferred; cost remains null.
- This pilot does not recover missing original V2 itineraries/traces or establish identity with later supplementary samples, even if identifiers/scores coincide.
- Human ground-truth signoff and any separately approved new cohort remain outstanding. No additional paid call, merge, billing change or model fallback is authorized by this review.
