# V3 live cohort execution notes

Date: 7 November 2026, Asia/Riyadh. The project lead authorized proceeding with the existing free-tier Gemini project. The project tier was inspected in AI Studio before execution. No billing upgrade or purchase was made.

## Fixed experimental conditions

The cohort is `baseline-v3-20261107`: all twenty frozen cases, seeds 11/22/33, gemini-3.5-flash-lite, temperature zero, three outer attempts, ten remote calls per attempt, pinned google-genai 1.30.0, 30-second request timeout, and a 90-request cap per backend/chunk. The manifest fixes thirteen source/dependency files and the three datasets. Neither the pilot nor historical V2 is substituted into this cohort.

## Scheduling and observed interruptions

The existing hosted Colab notebook was reconnected. The initial chunk produced G01 for all three seeds. After inspecting those saved successful records, execution continued in three-record chunks. G07/seed11 exhausted its three attempts with HTTP 429; the provider reported its free-tier limit as 15 requests per minute. The run stopped and a 19-record snapshot was downloaded. This error did not establish a daily quota exhaustion.

The unstarted pairs resumed after a 30-second pause, one record per chunk with twelve seconds between chunks. Backend settings and the manifest identity remained unchanged. G07/seed22 returned text with an unexpected prefix before its JSON object. The frozen parser rejected the response; the record stores a ParseError and missing-output scores. The scheduling cell stopped for inspection and a 20-record snapshot was downloaded.

After inspecting that text, execution resumed only unstarted pairs, with the same twelve-second spacing. Provider/request-limit errors stop execution; parse failures and invalid itineraries remain measured outcomes. Completed failures are never overwritten or silently regenerated. Changing scheduling did not change the prompt, tools, model parameters, parser or scorer. The timing adjustment must be disclosed when comparing conditions; service failures are distinct from itinerary quality.

## Evidence handling

Each downloaded ZIP is preserved byte-for-byte in local private storage with its SHA-256. Reviewed cohort files are imported separately under evidence/cohorts/. Manifests, raw responses subject to credential redaction, request/response journals, unsuccessful records and checksums are retained. A complete cohort means all expected case/seed records exist; it does not mean every generation or itinerary passed.

This execution log records observed scheduling and interruptions. The machine-readable cohort audit and independent review establish final coverage, scores and remaining limitations. No billing amount, seed effectiveness or unobserved execution is inferred.
