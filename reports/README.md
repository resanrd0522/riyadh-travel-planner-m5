# Which results should I read?

## Current V3 experiment

- `M5_REPORT.md`: method, primary V3 results, limitations and historical comparison.
- `v3_summary.json`: saved V3 statistics at their original precision.
- `full_cohort_audit.json`: verification and separate recalculation of all sixty records.
- `v3_tool_trace_checks.json`: checks of recorded tool results.

## Historical and supplementary checks

- `RESULTS.md` and `evaluation.json`: historical V2 arithmetic and offline component/supplementary checks. They are not the V3 experiment summary. Their statements about no model calls refer to the offline check command.
- `verification.log`: an earlier run of 30 tests. This is an unchanged historical log, not the latest test count.
- `colab_integration_verification.log`: later integration verification; the tests use the pinned SDK with simulated HTTP responses. The documented 49-test result does not mean every environment will run all SDK tests without their optional dependencies.
- `live_pilot_audit.json`: the earlier one-case pilot, separate from the formal sixty runs.

Running the frozen evaluation pipeline can regenerate `RESULTS.md` under its original generic heading. This index remains the guide to its historical scope. Original logs and experiment files are not rewritten to look newer.
