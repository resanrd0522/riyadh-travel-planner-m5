# Independent Codex review — 2026-11-06

A separate reviewer inspected actual artifacts read-only.

## Confirmed issues
- Original V1/V2 score records omit itineraries and raw response text (main notebook physical cells 56 and 84). Aggregate arithmetic cannot independently establish original scores.
- Judge notebook physical cells 21–23 generate later supplementary samples; these cannot replace original V2 outputs.
- validate_itinerary has an unhashable activity-ID exception path; the M5 IFR wrapper catches the exception and returns zero. This finding is static, not a Python reproduction.

## Risks
G05/G08/G15 have limited matching activity capacity, which does not prove structural infeasibility. Tool-name lists support coverage, not tool correctness. Judge results are absent. Original requirements and rubric are missing.

## Executed verification
Separately written JavaScript reference scoring on all 20 supplementary sample itineraries and the three CSV datasets: 80 APM/RBM/HBM/IFR score comparisons and 20 validity flags agree with saved seed-11 V2 score rows. This verifies supplementary samples only, not identity with original V2 generations. The exact script is verify_supplementary_samples.mjs.

## Verdict
PASS WITH CONDITIONS for preservation/import, not a full M5 scientific-validation PASS. No notebook execution, installs or model API calls.
