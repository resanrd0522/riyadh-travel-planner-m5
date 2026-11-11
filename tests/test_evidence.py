from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from m5eval.evaluate import ROOT, V2, read_json, verify_import
from m5eval.records import build_record, save_record
from m5eval.scoring import load_datasets, score_itinerary
from m5eval.statistics import summarize
from test_scoring import fixture


class EvidenceTests(unittest.TestCase):
    def test_preserved_files(self):
        self.assertEqual(verify_import(), 78)

    def test_saved_statistics_keep_aggregation_levels_separate(self):
        cases = read_json(V2 / "baseline_v2_implementation_reference.json")["golden_set"]
        records = read_json(V2 / "baseline_results_v2.json")
        stats = summarize(records, cases)
        self.assertAlmostEqual(stats["APM"]["mean"], 96.8335)
        self.assertAlmostEqual(stats["IFR"]["across_runs"]["sample_sd"], 36.00847357902755)
        self.assertEqual(stats["IFR"]["between_seed_means"]["sample_sd"], 0)
        self.assertEqual(stats["IFR"]["between_case_means"]["n"], 20)
        for bad in (records[:-1], records + [records[0]]):
            with self.assertRaises(ValueError):
                summarize(bad, cases)
        changed = deepcopy(records)
        changed[0]["APM"] = None
        with self.assertRaises(ValueError):
            summarize(changed, cases)

    def test_later_samples_match_recorded_scores_without_identity_claim(self):
        datasets = load_datasets(ROOT / "data")
        records = read_json(V2 / "baseline_results_v2.json")
        cases = read_json(V2 / "baseline_v2_implementation_reference.json")["golden_set"]
        for case in cases:
            with self.subTest(case=case["case_id"]):
                sample = read_json(ROOT / f"source/05_M5_Evaluation/llm_judge_evaluation/baseline_samples/baseline_{case['case_id']}_seed11.json")
                score = score_itinerary(sample["generation_result"]["itinerary"], case, datasets)
                expected = next(r for r in records if r["case_id"] == case["case_id"] and r["seed"] == 11)
                for metric in ("APM", "RBM", "HBM", "IFR"):
                    self.assertEqual(score[metric], expected[metric])

    def test_future_record_preserves_actual_evidence_and_refuses_overwrite(self):
        datasets, case, trip = fixture()
        generation = {"generation_success": True, "itinerary": trip, "raw_text": json.dumps(trip),
                      "tool_calls": ["find_hotels"], "trace": [{"name": "find_hotels", "arguments": {"budget_level": "Low"}, "result": [{"place_id": "H1"}]}]}
        metadata = {"model": "recorded-model", "temperature": 0, "code_commit": "recorded-commit",
                    "dataset_sha256": {}, "api_key": "do-not-store", "latency_ms": None}
        record = build_record(case, 11, generation, datasets, metadata, experiment_version="test-v3", run_id="test-1")
        self.assertEqual(record["generation_result"], generation)
        self.assertEqual(record["metadata"]["api_key"], "[REDACTED]")
        self.assertIsNone(record["metadata"]["latency_ms"])
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            save_record(path, record)
            self.assertEqual(json.loads(path.read_text())["generation_result"]["itinerary"], trip)
            with self.assertRaises(FileExistsError):
                save_record(path, record)

    def test_failure_records_are_zero_and_success_is_not_inferred(self):
        datasets, case, _ = fixture()
        metadata = {"model": "test", "temperature": 0, "code_commit": "test", "dataset_sha256": {}}
        record = build_record(case, 11, {"generation_success": False, "error": "recorded failure"}, datasets,
                              metadata, experiment_version="test", run_id="failed")
        self.assertFalse(record["generation_success"])
        self.assertTrue(all(record["evaluation"][m] == 0 for m in ("APM", "RBM", "HBM", "IFR")))
        with self.assertRaises(ValueError):
            build_record(case, 11, {}, datasets, metadata, experiment_version="test", run_id="missing")

    def test_credential_text_refused_before_write(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "secret.json"
            with self.assertRaises(ValueError):
                save_record(path, {"raw_text": "AIza" + "x"*35})
            self.assertFalse(path.exists())

    def test_reviewer_credential_alias_regression(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            metadata = {"client_secret": "example-private-client-value", "refresh_token": "example-refresh-token-value",
                        "Access-Token": "example-access-token-value"}
            with self.assertRaises(ValueError):
                save_record(path, {"metadata": metadata, "raw_text": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456"})
            self.assertFalse(path.exists())
            save_record(path, {"metadata": metadata})
            self.assertEqual(set(json.loads(path.read_text())["metadata"].values()), {"[REDACTED]"})

    def test_reviewer_contradictory_failure_regression(self):
        datasets, case, trip = fixture()
        metadata = {"model": "test", "temperature": 0, "code_commit": "test", "dataset_sha256": {}}
        with self.assertRaises(ValueError):
            build_record(case, 11, {"generation_success": False, "itinerary": trip, "error": "failed"},
                         datasets, metadata, experiment_version="test", run_id="contradiction")

    def test_reviewer_tuple_sanitation_regression(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tuple.json"
            with self.assertRaises(ValueError):
                save_record(path, {"nested": ({"api_key": "example-private-key"},),
                                   "raw": ("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456",)})
            self.assertFalse(path.exists())
            save_record(path, {"nested": ({"api_key": "example-private-key"},)})
            self.assertEqual(json.loads(path.read_text())["nested"], [{"api_key": "[REDACTED]"}])


if __name__ == "__main__":
    unittest.main()
