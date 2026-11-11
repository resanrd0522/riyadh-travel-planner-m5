
import ast
import hashlib
from copy import deepcopy
import importlib.util
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile
from unittest.mock import patch

from m5eval import baseline_tools
from m5eval.demo import FixtureBackend
from m5eval.evaluate import ROOT, read_json
from m5eval.experiment import Experiment, RunSettings, golden_cases
from m5eval.generation import (
    GeminiBackend,
    ProviderFailure,
    build_prompt,
    generate,
    make_tools,
    normalize_response,
)

try:
    import httpx
    from google import genai
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


def final_response(trip):
    return {
        "candidates": [{
            "content": {
                "role": "model",
                "parts": [{"text": json.dumps(trip)}],
            },
            "finishReason": "STOP",
        }],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 5,
            "totalTokenCount": 15,
        },
        "modelVersion": "mock-provider-model",
    }


def function_response(case):
    return {
        "candidates": [{
            "content": {
                "role": "model",
                "parts": [
                    {
                        "functionCall": {
                            "name": "find_activities",
                            "args": {"interests": case["interests"]},
                        }
                    },
                    {
                        "functionCall": {
                            "name": "find_restaurants",
                            "args": {"budget_level": case["budget_level"]},
                        }
                    },
                    {
                        "functionCall": {
                            "name": "find_hotels",
                            "args": {"budget_level": case["budget_level"]},
                        }
                    },
                ],
            },
            "finishReason": "STOP",
        }],
        "usageMetadata": {"totalTokenCount": 12},
    }


class IntegrationTests(unittest.TestCase):

    def setUp(self):
        self.case = golden_cases()[0]

    def test_prompts_match_archived_baseline_for_all_twenty_cases(self):
        archive = (
            ROOT
            / "evidence"
            / "cohorts"
            / "baseline-v3-20261107.zip"
        )
        self.assertTrue(
            archive.is_file(),
            "The frozen V3 evidence archive is required",
        )

        cases = golden_cases()
        self.assertEqual(len(cases), 20)
        self.assertEqual(
            len({case["case_id"] for case in cases}),
            20,
        )

        with ZipFile(archive) as evidence:
            manifest = json.loads(
                evidence.read(
                    "baseline-v3-20261107/manifest.json"
                )
            )
            self.assertEqual(
                manifest["identity"]["cases"],
                cases,
            )
            self.assertEqual(
                manifest["identity"]["seeds"],
                [11, 22, 33],
            )

            for case in cases:
                for seed in (11, 22, 33):
                    path = (
                        f"baseline-v3-20261107/"
                        f"{case['case_id']}_seed{seed}/record.json"
                    )
                    record = json.loads(evidence.read(path))

                    self.assertEqual(
                        record["user_input"],
                        case,
                    )
                    self.assertEqual(
                        record["seed"],
                        seed,
                    )

                    generated = record["generation_result"]
                    expected = build_prompt(case)

                    self.assertEqual(
                        generated["prompt"],
                        expected,
                    )
                    self.assertEqual(
                        generated["prompt_sha256"],
                        hashlib.sha256(
                            expected.encode("utf-8")
                        ).hexdigest(),
                    )

    def test_tool_signatures_and_json_safe_results(self):
        events = []
        tools = make_tools(ROOT / "data", events.append)

        for wrapped in tools:
            self.assertEqual(
                inspect.signature(wrapped),
                inspect.signature(
                    getattr(
                        baseline_tools,
                        wrapped.__name__,
                    )
                ),
            )

        outputs = [
            tools[0](["Culture & History"]),
            tools[1]("High"),
            tools[2]("High"),
        ]

        json.dumps(outputs, allow_nan=False)

        self.assertEqual(
            [e["kind"] for e in events],
            ["tool_call", "tool_result"] * 3,
        )
        self.assertEqual(
            events[0]["arguments"],
            {
                "interests": ["Culture & History"],
                "limit": 30,
            },
        )

    def test_live_gate_precedes_client_initialization(self):
        with patch(
            "importlib.metadata.version",
            side_effect=AssertionError(
                "SDK should not load"
            ),
        ):
            with self.assertRaises(PermissionError):
                GeminiBackend("offline-test-key")

    def test_fixture_end_to_end_and_resume_does_not_repeat_generation(self):
        with TemporaryDirectory() as directory:
            backend = FixtureBackend(self.case)

            experiment = Experiment(
                directory,
                "fixture",
                [self.case],
                [11],
                backend,
                settings=RunSettings(max_attempts=1),
            )

            record = experiment.run_case("G01", 11)

            self.assertEqual(
                record["evaluation"]["IFR"],
                100,
            )
            self.assertEqual(
                record["metadata"]["evidence_mode"],
                "fixture",
            )
            self.assertEqual(
                record["metadata"]["live_http_requests"],
                0,
            )
            self.assertIsNone(
                record["metadata"]["cost_usd"]
            )
            self.assertTrue(
                record["generation_result"]["raw_text"]
            )

            self.assertEqual(
                experiment.run_case("G01", 11),
                record,
            )
            self.assertEqual(backend.calls, 1)
            self.assertEqual(
                experiment.summary()["status"],
                "pilot only; not a three-seed baseline summary",
            )
            self.assertTrue(
                (
                    experiment.root
                    / "G01_seed11/events.jsonl"
                ).is_file()
            )

    def test_changed_settings_or_source_identity_cannot_resume(self):
        with TemporaryDirectory() as directory:
            Experiment(
                directory,
                "fixed",
                [self.case],
                [11],
                FixtureBackend(self.case),
            )

            with self.assertRaises(ValueError):
                Experiment(
                    directory,
                    "fixed",
                    [self.case],
                    [11],
                    FixtureBackend(self.case),
                    settings=RunSettings(
                        max_attempts=1
                    ),
                )

    def test_incomplete_and_tampered_runs_are_not_rerun(self):
        with TemporaryDirectory() as directory:
            backend = FixtureBackend(self.case)

            experiment = Experiment(
                directory,
                "incomplete",
                [self.case],
                [11],
                backend,
            )

            (
                experiment.root / "G01_seed11"
            ).mkdir()

            with self.assertRaises(ValueError):
                experiment.run_case("G01", 11)

            self.assertEqual(backend.calls, 0)

        with TemporaryDirectory() as directory:
            backend = FixtureBackend(self.case)

            experiment = Experiment(
                directory,
                "tampered",
                [self.case],
                [11],
                backend,
            )

            experiment.run_case("G01", 11)

            (
                experiment.root
                / "G01_seed11/record.json"
            ).write_text("{}")

            with self.assertRaises(ValueError):
                experiment.run_case("G01", 11)

            self.assertEqual(backend.calls, 1)

    def test_parse_failure_is_preserved_with_zero_scores(self):
        with TemporaryDirectory() as directory:
            backend = FixtureBackend(
                self.case,
                text_override="not JSON",
            )

            experiment = Experiment(
                directory,
                "bad-json",
                [self.case],
                [11],
                backend,
            )

            record = experiment.run_case("G01", 11)

            self.assertFalse(
                record["generation_success"]
            )
            self.assertEqual(
                record["generation_result"]["raw_text"],
                "not JSON",
            )
            self.assertEqual(
                record["evaluation"]["IFR"],
                0,
            )
            self.assertEqual(
                record["RTC"],
                100,
            )
            self.assertEqual(
                record,
                experiment.run_case("G01", 11),
            )

    def test_normalization_preserves_only_archived_repairs(self):
        for text in (
            "{}",
            "json\n{}",
            "```json\n{}\n```",
        ):
            self.assertEqual(
                normalize_response(text),
                "{}",
            )

        self.assertEqual(
            normalize_response("explanation {}"),
            "explanation {}",
        )
        self.assertEqual(
            normalize_response("JSON\n{}"),
            "JSON\n{}",
        )

    def test_config_validation_before_calls(self):
        with self.assertRaises(ValueError):
            RunSettings(temperature=0.5)

        with self.assertRaises(ValueError):
            RunSettings(max_attempts=4)

        with TemporaryDirectory() as directory:
            experiment = Experiment(
                directory,
                "valid",
                [self.case],
                [11],
                FixtureBackend(self.case),
            )

            with self.assertRaises(ValueError):
                experiment.run_case("G01", 22)

            with self.assertRaises(ValueError):
                experiment.run_batch(
                    max_new_runs=0
                )

        with self.assertRaises(ValueError):
            Experiment(
                ROOT / "source",
                "forbidden",
                [self.case],
                [11],
                FixtureBackend(self.case),
            )

        with self.assertRaises(ValueError):
            generate(
                self.case,
                11,
                FixtureBackend(self.case),
                ROOT / "data",
                lambda event: None,
                temperature=0.1,
            )

    def test_clean_notebook_has_safe_defaults_and_compiles(self):
        notebook = read_json(
            ROOT
            / "notebooks"
            / "M5_Colab_Run.ipynb"
        )

        code_cells = [
            cell
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        ]

        flags = {}

        for node in ast.parse(
            "".join(code_cells[0]["source"])
        ).body:
            if isinstance(node, ast.Assign):
                flags[node.targets[0].id] = (
                    ast.literal_eval(node.value)
                )

        for flag in (
            "APPROVE_LIVE_PILOT",
            "APPROVE_FULL_EXPERIMENT",
            "UPLOAD_REPOSITORY_ZIP",
            "INSTALL_DEPENDENCIES",
        ):
            self.assertIs(flags[flag], False)

        for cell in code_cells:
            self.assertIsNone(
                cell["execution_count"]
            )
            self.assertEqual(
                cell["outputs"],
                [],
            )
            compile(
                "".join(cell["source"]),
                "clean-notebook-cell",
                "exec",
            )

    def test_final_version_symlink_cannot_redirect_to_preserved_source(self):
        with TemporaryDirectory() as directory:
            (
                Path(directory) / "alias"
            ).symlink_to(
                ROOT / "source",
                target_is_directory=True,
            )

            with self.assertRaises(ValueError):
                Experiment(
                    directory,
                    "alias",
                    [self.case],
                    [11],
                    FixtureBackend(self.case),
                )


@unittest.skipUnless(
    SDK_AVAILABLE,
    "Install requirements-gemini.txt to test the pinned SDK with a mock HTTP transport",
)
class SDKIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.case = golden_cases()[0]

        archive = (
            ROOT
            / "evidence"
            / "cohorts"
            / "baseline-v3-20261107.zip"
        )

        with ZipFile(archive) as evidence:
            self.sample = json.loads(
                evidence.read(
                    "baseline-v3-20261107/G01_seed11/record.json"
                )
            )

        self.assertEqual(
            self.sample["user_input"],
            self.case,
        )
        self.assertTrue(
            self.sample["generation_success"]
        )

        self.trip = self.sample[
            "generation_result"
        ]["itinerary"]

        self.network_guard = patch(
            "socket.create_connection",
            side_effect=AssertionError(
                "Real network is forbidden in integration tests"
            ),
        )
        self.network_guard.start()
        self.addCleanup(
            self.network_guard.stop
        )

    def backend(self, handler, cap=10):
        backend = GeminiBackend(
            "offline-test-key",
            allow_live=True,
            max_http_requests=cap,
            mock_transport=httpx.MockTransport(
                handler
            ),
        )
        self.addCleanup(backend.close)
        return backend

    def test_actual_sdk_calls_tools_and_stores_http_history_and_scores(self):
        requests = []

        def handler(request):
            body = json.loads(request.content)
            requests.append(body)

            response = (
                function_response(self.case)
                if len(requests) == 1
                else final_response(self.trip)
            )
            return httpx.Response(
                200,
                json=response,
            )

        with TemporaryDirectory() as directory:
            backend = self.backend(handler)

            experiment = Experiment(
                directory,
                "sdk-mock",
                [self.case],
                [11],
                backend,
            )

            record = experiment.run_case("G01", 11)

            self.assertEqual(
                backend.request_count,
                2,
            )
            self.assertEqual(
                record["evaluation"]["IFR"],
                100,
            )
            self.assertEqual(
                record["metadata"]["evidence_mode"],
                "sdk_mock",
            )
            self.assertEqual(
                record["metadata"]["live_http_requests"],
                0,
            )
            self.assertEqual(
                record["metadata"]["provider_http_requests"],
                2,
            )
            self.assertEqual(
                record["RTC"],
                100,
            )
            self.assertEqual(
                len(
                    record["generation_result"]["tool_calls"]
                ),
                3,
            )
            self.assertTrue(
                record["generation_result"]["provider_history"]
            )
            self.assertEqual(
                requests[0]["generationConfig"]["seed"],
                11,
            )
            self.assertEqual(
                requests[0]["generationConfig"]["temperature"],
                0,
            )

            serialized = (
                experiment.root
                / "G01_seed11/record.json"
            ).read_text()

            self.assertNotIn(
                "offline-test-key",
                serialized,
            )
            self.assertNotIn(
                "x-goog-api-key",
                serialized.lower(),
            )

            events = [
                json.loads(line)
                for line in (
                    experiment.root
                    / "G01_seed11/events.jsonl"
                ).read_text().splitlines()
            ]

            self.assertEqual(
                sum(
                    e["kind"] == "http_request"
                    for e in events
                ),
                2,
            )
            self.assertTrue(
                any(
                    e["kind"] == "tool_result"
                    and e["result"]
                    for e in events
                )
            )

    def test_503_retry_is_bounded_and_failed_attempts_remain_visible(self):
        backend = self.backend(
            lambda request: httpx.Response(
                503,
                json={
                    "error": {
                        "code": 503,
                        "message": "temporarily unavailable",
                        "status": "UNAVAILABLE",
                    }
                },
            )
        )

        delays = []
        events = []

        generation = generate(
            self.case,
            11,
            backend,
            ROOT / "data",
            events.append,
            sleep=delays.append,
        )

        self.assertFalse(
            generation["generation_success"]
        )
        self.assertEqual(
            backend.request_count,
            3,
        )
        self.assertEqual(
            delays,
            [5, 10],
        )
        self.assertEqual(
            [
                a["status"]
                for a in generation["attempts"]
            ],
            ["failed"] * 3,
        )
        self.assertEqual(
            sum(
                e["kind"] == "http_response"
                and e["status_code"] == 503
                for e in events
            ),
            3,
        )

    def test_404_stops_without_fallback(self):
        paths = []

        def handler(request):
            paths.append(request.url.path)
            return httpx.Response(
                404,
                json={
                    "error": {
                        "code": 404,
                        "message": "model not found",
                        "status": "NOT_FOUND",
                    }
                },
            )

        generation = generate(
            self.case,
            11,
            self.backend(handler),
            ROOT / "data",
            lambda event: None,
            sleep=lambda n: self.fail(
                "404 must not retry"
            ),
        )

        self.assertEqual(
            generation["generation_error"]["code"],
            404,
        )
        self.assertEqual(len(paths), 1)
        self.assertIn(
            "gemini-3.5-flash-lite",
            paths[0],
        )

    def test_retry_coverage_uses_final_attempt_not_union(self):
        calls = []

        def handler(request):
            calls.append(request)

            if len(calls) == 1:
                return httpx.Response(
                    200,
                    json=function_response(self.case),
                )

            if len(calls) == 2:
                return httpx.Response(
                    503,
                    json={
                        "error": {
                            "code": 503,
                            "message": "busy",
                            "status": "UNAVAILABLE",
                        }
                    },
                )

            return httpx.Response(
                200,
                json=final_response(self.trip),
            )

        generation = generate(
            self.case,
            11,
            self.backend(handler),
            ROOT / "data",
            lambda event: None,
            sleep=lambda n: None,
        )

        self.assertTrue(
            generation["generation_success"]
        )
        self.assertEqual(
            generation["tool_calls"],
            [],
        )
        self.assertEqual(
            len(
                generation["all_attempt_tool_calls"]
            ),
            3,
        )
        self.assertEqual(
            len(generation["attempts"]),
            2,
        )

    def test_http_cap_stops_automatic_function_calling(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(
                200,
                json=function_response(self.case),
            )

        generation = generate(
            self.case,
            11,
            self.backend(handler, cap=1),
            ROOT / "data",
            lambda event: None,
            sleep=lambda n: None,
        )

        self.assertFalse(
            generation["generation_success"]
        )
        self.assertEqual(
            len(calls),
            1,
        )
        self.assertEqual(
            generation["generation_error"]["type"],
            "RequestBudgetExceeded",
        )

    def test_error_key_is_redacted(self):
        backend = self.backend(
            lambda request: httpx.Response(
                403,
                json={
                    "error": {
                        "code": 403,
                        "message": "invalid offline-test-key",
                        "status": "PERMISSION_DENIED",
                    }
                },
            )
        )

        events = []

        generation = generate(
            self.case,
            11,
            backend,
            ROOT / "data",
            events.append,
        )

        self.assertNotIn(
            "offline-test-key",
            json.dumps(generation),
        )
        self.assertNotIn(
            "offline-test-key",
            json.dumps(events),
        )

    def test_recovered_503_clears_terminal_error_and_batch_continues(self):
        calls = []

        def handler(request):
            calls.append(request)

            if len(calls) == 1:
                return httpx.Response(
                    503,
                    json={
                        "error": {
                            "code": 503,
                            "message": "busy",
                            "status": "UNAVAILABLE",
                        }
                    },
                )

            return httpx.Response(
                200,
                json=final_response(self.trip),
            )

        with TemporaryDirectory() as directory:
            backend = self.backend(handler)

            experiment = Experiment(
                directory,
                "recovered",
                [self.case],
                [11, 22],
                backend,
            )

            with patch(
                "m5eval.generation.time.sleep"
            ):
                original = experiment.run_case

                experiment.run_case = (
                    lambda case_id, seed: original(
                        case_id,
                        seed,
                        sleep=lambda seconds: None,
                    )
                )

                records = experiment.run_batch(
                    max_new_runs=2
                )

            self.assertEqual(
                len(records),
                2,
            )
            self.assertTrue(
                all(
                    r["generation_success"]
                    for r in records
                )
            )
            self.assertIsNone(
                records[0]["generation_result"]["generation_error"]
            )
            self.assertEqual(
                records[0]["generation_result"]["attempts"][0]["status"],
                "failed",
            )
            self.assertEqual(
                backend.request_count,
                3,
            )

    def test_requested_tool_coverage_is_distinct_from_successful_execution(self):
        requests = []

        def handler(request):
            requests.append(request)

            if len(requests) == 1:
                body = function_response(
                    self.case
                )
                body["candidates"][0]["content"]["parts"] = [
                    {
                        "functionCall": {
                            "name": "find_hotels",
                            "args": {},
                        }
                    }
                ]
                return httpx.Response(
                    200,
                    json=body,
                )

            return httpx.Response(
                200,
                json=final_response(self.trip),
            )

        generation = generate(
            self.case,
            11,
            self.backend(handler),
            ROOT / "data",
            lambda event: None,
        )

        self.assertTrue(
            generation["generation_success"]
        )
        self.assertEqual(
            generation["tool_calls"],
            ["find_hotels"],
        )
        self.assertEqual(
            generation["executed_tool_calls"],
            [],
        )


if __name__ == "__main__":
    unittest.main()

