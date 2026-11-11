# Independent offline harness review

Review date: 2026-11-06. Scope: actual `m5eval/`, `tests/`, frozen artifacts and generated reports. The reviewer did not modify builder implementation files or execute any notebook/model API calls.

## Verification executed

- Bundled Python: `python3 -m unittest discover -s tests` — final re-review: 30 tests passed.
- `python3 -m m5eval` — completed successfully, verifying 78 imported artifacts, 60 historical score rows, 20 supplementary samples and 60 case/tool contracts.
- Independent AST comparison: all six extracted search-tool definitions match the preserved notebook exactly.
- Independent CSV canonicalization with pandas 2.2.3 and `float_precision="round_trip"` reproduces all three frozen DataFrame hashes: activities `c4a6420190dc949b1b6daba7550bd71809ef9f03b3bd8582f134c56c3296ea70`; restaurants `2d53972ef3b35a6283a2c8ef491d66f1ce5f4c90badfc3d82e00e0aa92f67ec7`; hotels `ab28eaa83991c9ad13807ff518f18ce9c60e3478ad1d16bba2ab0ebf56371259`.
- Executed 45 additional malformed-container/identifier/day variants against the frozen scoring definitions. The only numeric difference was deliberate strict day-type validation: historical `day=True` earns IFR 100; v3 rejects it and earns IFR 0. This hardening must remain explicitly versioned; no historical rows were rescored or changed.
- The independently written JavaScript sample scorer separately reproduced all 80 metric values and 20 validity flags on the later supplementary samples. This does not establish identity with original V2 outputs.

## Findings and fixes verified

1. The builder fixed credential-field aliases and generic Bearer detection; regression tests now cover these paths.
2. The builder fixed contradictory `generation_success=False` records containing an itinerary by rejecting them, rather than redefining the scientific metric denominators.

## Additional finding fixed and verified

**P2 — tuple containers bypassed evidence sanitation in the earlier builder revision.** `_safe` recursed into dictionaries and lists only, while `json.dumps` also serialized tuples. This synthetic reproducer previously wrote both credential values unchanged:

```python
save_record(path, {
    "nested": ({"api_key": "example-private-key"},),
    "raw": ("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456",),
})
```

The builder now traverses tuples as lists and added a regression test. Independent re-execution of the exact reproducer raised `ValueError` before destination creation. A separate nested-tuple test confirmed `api_key` and `refresh_token` values become `[REDACTED]`. UTF-8 serialization is checked before destination creation. This finding concerned the future-record helper, not a demonstrated leak in imported artifacts. No known actionable code findings remain from this review; sanitation is a layered guard, not a guarantee against every possible credential format.

The reviewer also read `README.md` and `docs/EVALUATION_PROTOCOL.md`. They distinguish original historical rows, later supplementary outputs, structural IFR and actual tool-contract evaluation. Strict day types/JSON parsing are explicitly disclosed as versioned hardening. Hash parity under round-trip parsing is reported without asserting the cause of historical parser differences.

## Evidence limits and conditions

- The 60 historical V2 rows contain scores and saved tool-name sequences, but no original itineraries/raw responses. Their aggregate arithmetic can be checked; original outputs cannot be independently rescored.
- Desktop recovery search found status logs for all 60 V2 pairs in notebook cells 123–142, but no original full itineraries there. A complete G01 pilot in cell 54 and a truncated G15 diagnostic preview are separate evidence and must not be substituted.
- The 20 supplementary seed-11 outputs were generated later by judge-notebook cells 21–23. Matching scores do not establish original-run identity.
- Ground-truth acceptance rules still require team human signoff. G05/G08/G15 are preference-capacity limited, not necessarily structurally impossible.
- RTC measures saved required-tool-name coverage, not argument/result correctness or full trace authenticity.
- Judge evaluation remains supplementary and unfinished; no completed judge score or model availability was verified.
- Canonical hash parity under round-trip parsing is established. The cause of any historical runtime parsing differences is not established.

## Verdict

**PASS WITH CONDITIONS** for the offline harness after the three targeted evidence-writer fixes and final 30-test run. No imported original artifacts were rewritten. This is not a scientific-validation PASS for missing original V2 outputs/traces, a completed human ground-truth signoff, or an approval to merge or make model API calls.
