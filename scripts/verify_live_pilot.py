"""Audit the supplied pilot evidence without making provider requests."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from m5eval.experiment import fingerprint, golden_cases
from m5eval.generation import build_prompt, make_tools, normalize_response, requested_tool_names
from m5eval.scoring import load_datasets, score_itinerary, tool_coverage


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    run = directory / "G01_seed11"
    record = json.loads((run / "record.json").read_text())
    generation = record["generation_result"]
    events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
    check(digest(run / "record.json") == (run / "record.sha256").read_text().strip(), "Record checksum mismatch")
    check(fingerprint(manifest["identity"]) == manifest["identity_sha256"] == record["metadata"]["experiment_identity_sha256"], "Manifest identity mismatch")
    identity = manifest["identity"]
    check(identity["cases"] == [golden_cases()[0]] and identity["seeds"] == [11], "Unexpected pilot cohort")
    case = identity["cases"][0]
    check(record["user_input"] == case and record["case_id"] == "G01" and record["seed"] == 11, "Input mismatch")
    request = json.loads((run / "request.json").read_text())
    check(request["case"] == case and request["seed"] == 11 and request["experiment_identity_sha256"] == manifest["identity_sha256"], "Request identity mismatch")
    for path, expected in identity["source_sha256"].items():
        target = (ROOT / path).resolve()
        check(ROOT in target.parents, "Source fingerprint path escapes repository")
        check(digest(target) == expected, f"Source fingerprint mismatch: {path}")
    for name in ("activities", "restaurants", "hotels"):
        check(digest(ROOT / "data" / f"{name}.csv") == identity["dataset_sha256"][name], "Dataset fingerprint mismatch")
    check(identity["dataset_sha256"] == record["metadata"]["dataset_sha256"], "Record dataset identity mismatch")
    check(identity["source_sha256"] == record["metadata"]["source_sha256"], "Record source identity mismatch")
    check(identity["settings"] == record["metadata"]["generation_settings"], "Settings mismatch")
    check(identity["settings"]["model"] == "gemini-3.5-flash-lite" and identity["settings"]["temperature"] == 0, "Model settings mismatch")
    check(generation["prompt"] == build_prompt(case), "Prompt differs from baseline")
    check(hashlib.sha256(generation["prompt"].encode()).hexdigest() == generation["prompt_sha256"], "Prompt checksum mismatch")
    check(events == generation["trace"], "Journal differs from final trace")
    check([e["event_number"] for e in events] == list(range(1, len(events)+1)), "Event sequence mismatch")
    check(all(e["attempt"] == 1 for e in events), "Unexpected pilot retry")
    requests = [e for e in events if e["kind"] == "http_request"]
    responses = [e for e in events if e["kind"] == "http_response"]
    check(len(requests) == len(responses) == record["metadata"]["provider_http_requests"] == record["metadata"]["live_http_requests"] == 2, "HTTP count mismatch")
    check([e["request_number"] for e in requests] == [e["request_number"] for e in responses] == [1, 2], "HTTP request/response pair mismatch")
    for request in requests:
        config = request["body"]["generationConfig"]
        check(config["seed"] == 11 and config["temperature"] == 0, "HTTP generation settings mismatch")
        check("headers" not in request and "?" not in request["path"], "Unexpected header/query evidence")
        check("gemini-3.5-flash-lite:generateContent" in request["path"], "Unexpected model endpoint")
    check(all(e["status_code"] == 200 and e["body"]["modelVersion"] == "gemini-3.5-flash-lite" for e in responses), "Unexpected provider status/model version")
    tool_calls = [e for e in events if e["kind"] == "tool_call"]
    tool_results = [e for e in events if e["kind"] == "tool_result"]
    check(len(tool_calls) == len(tool_results) == 3, "Tool event count mismatch")
    local_events = []
    tools = {f.__name__: f for f in make_tools(ROOT / "data", local_events.append)}
    for call, result in zip(tool_calls, tool_results):
        check(call["name"] == result["name"] and result["status"] == "success", "Tool event pairing mismatch")
        check(tools[call["name"]](**call["arguments"]) == result["result"], "Recorded tool result differs from frozen data search")
    by_name = {event["name"]: event["result"] for event in tool_results}
    trip = generation["itinerary"]
    check(trip["hotel_id"] in {r["place_id"] for r in by_name["find_hotels"]}, "Hotel was not returned by tool")
    for day in trip["days"]:
        check(set(day["activities"]) <= {r["place_id"] for r in by_name["find_activities"]}, "Activity was not returned by tool")
        check(set(day["restaurants"]) <= {r["place_id"] for r in by_name["find_restaurants"]}, "Restaurant was not returned by tool")
    check(normalize_response(generation["raw_text"]) == generation["normalized_text"], "Response normalization mismatch")
    check(json.loads(generation["normalized_text"]) == trip, "Saved itinerary differs from response")
    evaluation = score_itinerary(trip, case, load_datasets(ROOT / "data"))
    check(evaluation == record["evaluation"], "Recomputed scores differ")
    check(requested_tool_names(events, attempt=1) == generation["tool_calls"], "RTC name provenance mismatch")
    check(tool_coverage(generation["tool_calls"]) == record["RTC"] == 100, "RTC mismatch")
    check(identity["evidence_mode"] == record["metadata"]["evidence_mode"] == generation["provider_mode"] == "live", "Evidence mode mismatch")
    check(record["generation_success"] and generation["generation_error"] is None, "Generation is not successful")
    patterns = [r"AIza[0-9A-Za-z_-]{30,}", r"(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}", r"sk-[A-Za-z0-9_-]{20,}",
                r"AKIA[0-9A-Z]{16}", r"(?i:Bearer)\s+[A-Za-z0-9_.~+/-]{16,}", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    for file in directory.rglob("*"):
        if file.is_file():
            text = file.read_text()
            check(not any(re.search(pattern, text) for pattern in patterns), f"Credential-like content requires inspection: {file.name}")
    return {"status": "PASS for supplied pilot evidence consistency and offline recomputation",
            "case_id": "G01", "seed": 11, "evidence_mode": "live",
            "source_files_matching": len(identity["source_sha256"]), "datasets_matching": 3,
            "http_requests_recorded": 2, "successful_http_responses_recorded": 2,
            "tool_results_reproduced": 3, "all_recommendations_returned_by_tools": True,
            "evaluation": evaluation, "RTC": record["RTC"],
            "wall_time_ms_recorded": record["metadata"]["wall_time_ms"],
            "cost_usd": record["metadata"]["cost_usd"],
            "limits": ["One pilot, not a completed 20-case/three-seed cohort.",
                       "Internal consistency of supplied logs is verified, not cryptographic provider attestation.",
                       "Provider seed effectiveness, billing cost and historical V2 outputs remain unverified."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=ROOT / "evidence/pilots/pilot-v3-20261107")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory), indent=2))


if __name__ == "__main__":
    main()
