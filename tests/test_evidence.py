
"""Tests for preserved V3 evidence and safe record handling."""

import hashlib
import json
import statistics
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from m5eval.evaluate import ROOT
from m5eval.records import build_record, save_record
from test_scoring import fixture


ARCHIVE = ROOT / "evidence" / "cohorts" / "baseline-v3-20261107.zip"
PREFIX = "baseline-v3-20261107/"
SEEDS = (11, 22, 33)
METRICS = ("APM", "RBM", "HBM", "IFR", "RTC")


def read_archive_json(archive, path):
    return json.loads(archive.read(path))


def load_v3_records(archive):
    records = []

    for number in range(1, 21):
        case_id = f"G{number:02d}"

        for seed in SEEDS:
            path = f"{PREFIX}{case_id}_seed{seed}/record.json"
            records.append(read_archive_json(archive, path))

    return records


def metric_value(record, metric):
    if metric == "RTC":
        return record["RTC"]

    return record["evaluation"][metric]


class EvidenceTests(unittest.TestCase):

    def test_v3_saved_records_and_checksums(self):
        self.assertTrue(ARCHIVE.is_file())

        with ZipFile(ARCHIVE) as archive:
            self.assertIsNone(archive.testzip())

            manifest = read_archive_json(
                archive, PREFIX + "manifest.json"
            )

            identity = manifest["identity"]
            cases = identity["cases"]
            seeds = identity["seeds"]

            self.assertEqual(
                identity["experiment_version"],
                "baseline-v3-20261107"
            )
            self.assertEqual(len(cases), 20)
            self.assertEqual(sorted(seeds), list(SEEDS))

            expected = {
                (f"G{number:02d}", seed)
                for number in range(1, 21)
                for seed in SEEDS
            }

            self.assertEqual(
                {case["case_id"] for case in cases},
                {f"G{number:02d}" for number in range(1, 21)}
            )

            actual = set()
            names = set(archive.namelist())

            for case_id, seed in sorted(expected):
                folder = f"{PREFIX}{case_id}_seed{seed}/"

                for filename in (
                    "record.json",
                    "record.sha256",
                    "events.jsonl",
                    "request.json",
                ):
                    self.assertIn(folder + filename, names)

                raw = archive.read(folder + "record.json")
                calculated_hash = hashlib.sha256(raw).hexdigest()

                saved_hash = archive.read(
                    folder + "record.sha256"
                ).decode("utf-8").strip()

                self.assertEqual(calculated_hash, saved_hash)

                record = json.loads(raw)

                self.assertEqual(record["case_id"], case_id)
                self.assertEqual(record["seed"], seed)
                self.assertEqual(
                    record["experiment_version"],
                    "baseline-v3-20261107"
                )

                actual.add((record["case_id"], record["seed"]))

            self.assertEqual(actual, expected)
            self.assertEqual(len(actual), 60)

    def test_v3_saved_statistics(self):
        with ZipFile(ARCHIVE) as archive:
            summary = read_archive_json(
                archive, PREFIX + "summary.json"
            )
            records = load_v3_records(archive)

        self.assertEqual(len(records), 60)
        self.assertEqual(summary["records"], 60)
        self.assertTrue(
            summary["is_formal_live_20_case_3_seed_cohort"]
        )

        for metric in METRICS:
            with self.subTest(metric=metric):
                values = [
                    metric_value(record, metric)
                    for record in records
                ]

                saved = summary["statistics"][metric]

                self.assertAlmostEqual(
                    statistics.mean(values),
                    saved["mean"],
                    places=6
                )

                self.assertEqual(
                    saved["across_runs"]["n"], 60
                )

                self.assertAlmostEqual(
                    statistics.stdev(values),
                    saved["across_runs"]["sample_sd"],
                    places=6
                )

                seed_means = [
                    statistics.mean(
                        metric_value(record, metric)
                        for record in records
                        if record["seed"] == seed
                    )
                    for seed in SEEDS
                ]

                self.assertEqual(
                    saved["between_seed_means"]["n"], 3
                )

                self.assertAlmostEqual(
                    statistics.stdev(seed_means),
                    saved["between_seed_means"]["sample_sd"],
                    places=6
                )

                case_means = [
                    statistics.mean(
                        metric_value(record, metric)
                        for record in records
                        if record["case_id"] == f"G{number:02d}"
                    )
                    for number in range(1, 21)
                ]

                self.assertEqual(
                    saved["between_case_means"]["n"], 20
                )

                self.assertAlmostEqual(
                    statistics.stdev(case_means),
                    saved["between_case_means"]["sample_sd"],
                    places=6
                )

        expected_means = {
            "APM": 93.50016666666667,
            "RBM": 96.66666666666667,
            "HBM": 96.66666666666667,
            "IFR": 81.66666666666667,
            "RTC": 100.0,
        }

        for metric, expected in expected_means.items():
            self.assertAlmostEqual(
                summary["statistics"][metric]["mean"],
                expected,
                places=4
            )

    def test_v3_failure_records_are_preserved(self):
        with ZipFile(ARCHIVE) as archive:
            records = load_v3_records(archive)

        failures = set()

        for record in records:
            if not record["generation_success"]:
                failures.add(
                    (record["case_id"], record["seed"])
                )

                for metric in ("APM", "RBM", "HBM", "IFR"):
                    self.assertEqual(
                        record["evaluation"][metric], 0
                    )

        self.assertEqual(
            failures,
            {("G07", 11), ("G07", 22)}
        )

        self.assertEqual(
            sum(record["generation_success"] for record in records),
            58
        )

    def test_future_record_preserves_actual_evidence_and_refuses_overwrite(self):
        datasets, case, trip = fixture()

        generation = {
            "generation_success": True,
            "itinerary": trip,
            "raw_text": json.dumps(trip),
            "tool_calls": ["find_hotels"],
            "trace": [{
                "name": "find_hotels",
                "arguments": {"budget_level": "Low"},
                "result": [{"place_id": "H1"}]
            }]
        }

        metadata = {
            "model": "recorded-model",
            "temperature": 0,
            "code_commit": "recorded-commit",
            "dataset_sha256": {},
            "api_key": "do-not-store",
            "latency_ms": None
        }

        record = build_record(
            case, 11, generation, datasets, metadata,
            experiment_version="test-v3",
            run_id="test-1"
        )

        self.assertEqual(record["generation_result"], generation)
        self.assertEqual(
            record["metadata"]["api_key"], "[REDACTED]"
        )
        self.assertIsNone(record["metadata"]["latency_ms"])

        with TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"

            save_record(path, record)

            self.assertEqual(
                json.loads(path.read_text())[
                    "generation_result"
                ]["itinerary"],
                trip
            )

            with self.assertRaises(FileExistsError):
                save_record(path, record)

    def test_failure_records_are_zero_and_success_is_not_inferred(self):
        datasets, case, _ = fixture()

        metadata = {
            "model": "test",
            "temperature": 0,
            "code_commit": "test",
            "dataset_sha256": {}
        }

        record = build_record(
            case, 11,
            {
                "generation_success": False,
                "error": "recorded failure"
            },
            datasets,
            metadata,
            experiment_version="test",
            run_id="failed"
        )

        self.assertFalse(record["generation_success"])

        self.assertTrue(
            all(
                record["evaluation"][metric] == 0
                for metric in ("APM", "RBM", "HBM", "IFR")
            )
        )

        with self.assertRaises(ValueError):
            build_record(
                case, 11, {}, datasets, metadata,
                experiment_version="test",
                run_id="missing"
            )

    def test_credential_text_refused_before_write(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "secret.json"

            with self.assertRaises(ValueError):
                save_record(
                    path,
                    {"raw_text": "AIza" + "x" * 35}
                )

            self.assertFalse(path.exists())

    def test_reviewer_credential_alias_regression(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"

            metadata = {
                "client_secret": "example-private-client-value",
                "refresh_token": "example-refresh-token-value",
                "Access-Token": "example-access-token-value"
            }

            with self.assertRaises(ValueError):
                save_record(
                    path,
                    {
                        "metadata": metadata,
                        "raw_text":
                            "Authorization: Bearer "
                            "abcdefghijklmnopqrstuvwxyz123456"
                    }
                )

            self.assertFalse(path.exists())

            save_record(path, {"metadata": metadata})

            saved = json.loads(path.read_text())

            self.assertEqual(
                set(saved["metadata"].values()),
                {"[REDACTED]"}
            )

    def test_reviewer_contradictory_failure_regression(self):
        datasets, case, trip = fixture()

        metadata = {
            "model": "test",
            "temperature": 0,
            "code_commit": "test",
            "dataset_sha256": {}
        }

        with self.assertRaises(ValueError):
            build_record(
                case, 11,
                {
                    "generation_success": False,
                    "itinerary": trip,
                    "error": "failed"
                },
                datasets,
                metadata,
                experiment_version="test",
                run_id="contradiction"
            )

    def test_reviewer_tuple_sanitation_regression(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tuple.json"

            with self.assertRaises(ValueError):
                save_record(
                    path,
                    {
                        "nested": (
                            {"api_key": "example-private-key"},
                        ),
                        "raw": (
                            "Authorization: Bearer "
                            "abcdefghijklmnopqrstuvwxyz123456",
                        )
                    }
                )

            self.assertFalse(path.exists())

            save_record(
                path,
                {
                    "nested": (
                        {"api_key": "example-private-key"},
                    )
                }
            )

            saved = json.loads(path.read_text())

            self.assertEqual(
                saved["nested"],
                [{"api_key": "[REDACTED]"}]
            )


if __name__ == "__main__":
    unittest.main()

