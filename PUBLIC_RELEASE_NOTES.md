# Public Release Notes

This document describes the contents and limitations of the public version of the Riyadh Travel Planner M5 Evaluation repository.

## Included Materials

The repository includes:

- Evaluation and scoring code.
- Automated tests and verification scripts.
- Google Colab notebooks.
- Evaluation methodology and documentation.
- Baseline V3 results and saved experiment evidence.

## Excluded Materials

The following materials are intentionally excluded:

- `data/*.csv`: Original M4 datasets. Redistribution permissions have not been established, and the original files must be supplied locally for full evidence verification.
- `reference/`: Instructor materials, course documents, and project proposals.
- `source/`: Historical notebooks, archives, and working copies.
- Internal handoff documents and private working notes.

## Reproducibility

The repository provides the evaluation code, automated tests, archived evidence, and verification instructions.

However, full verification requires the original M4 datasets and the historical source versions associated with Baseline V3.

The repository is therefore not fully self-contained.

The cleaned verification notebook documents the independently tested offline verification workflow.

## Data and Privacy

The repository does not intentionally redistribute the original M4 datasets or private course materials.

Before public release, repository files and Git history should be reviewed for credentials, sensitive information, and third-party content that may require redistribution permission.

API keys and other credentials must never be committed.

## Evaluation Scope

The published results represent the preserved M5 single-agent baseline evaluation.

The offline verification confirms the integrity of archived evidence and scoring reproducibility. It does not represent a new Gemini generation run or a completed evaluation of the three-agent treatment.
