"""Independent, standard-library-only audit of a supplied formal 20 x 3 cohort.

No model SDK is imported and no provider request is made. Partial cohorts produce
no aggregate statistics. An output file is created only with explicit --output,
exclusively, outside the supplied evidence directory.
"""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
from tempfile import TemporaryDirectory
import zipfile

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("APM", "RBM", "HBM", "IFR", "RTC")
REQUIRED_TOOLS = {"find_activities", "find_restaurants", "find_hotels"}
SEEDS = (11, 22, 33)


class AuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON object key")
        result[key] = value
    return result


def strict_json(text):
    def invalid_constant(value):
        raise AuditError("Non-finite JSON constant")
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def read_json(path):
    return strict_json(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def contained_file(root, relative):
    path = (root / relative).resolve()
    require(root.resolve() in path.parents, "Evidence or source path escapes its directory")
    return path


def datasets():
    result = {}
    for name in ("activities", "restaurants", "hotels"):
        with (ROOT / "data" / f"{name}.csv").open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        ids = [r["place_id"] for r in rows]
        require(all(ids) and len(ids) == len(set(ids)), f"Invalid {name} identifiers")
        result[name] = dict(zip(ids, rows))
    return result


def normalize(text):
    if not isinstance(text, str):
        return None
    value = text.strip()
    if value.startswith("json\n") and value[5:].lstrip().startswith("{"):
        value = value[5:].lstrip()
    if value.startswith("```"):
        value = value.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return value


def independently_score(trip, case, data):
    """Reference implementation; does not import the builder's scorer."""
    scores = {name: 0.0 for name in METRICS if name != "RTC"}
    if not isinstance(trip, dict):
        return scores
    duration = case["trip_duration"]
    days = trip.get("days")
    days = days if isinstance(days, list) else []
    seen, activity_matches, restaurant_matches = set(), 0, 0
    for day in days[:duration]:
        if not isinstance(day, dict):
            continue
        activities = day.get("activities")
        if isinstance(activities, list):
            for pid in activities[:2]:
                if not isinstance(pid, str) or pid in seen:
                    continue
                seen.add(pid)
                row = data["activities"].get(pid)
                activity_matches += bool(row and row["interest_group"] in case["interests"])
        restaurants = day.get("restaurants")
        if isinstance(restaurants, list):
            for pid in restaurants[:2]:
                row = data["restaurants"].get(pid) if isinstance(pid, str) else None
                restaurant_matches += bool(row and row["budget_level"] == case["budget_level"])
    hotel_id = trip.get("hotel_id")
    hotel = data["hotels"].get(hotel_id) if isinstance(hotel_id, str) else None
    scores.update(APM=round(100 * activity_matches / (2 * duration), 2),
                  RBM=round(100 * restaurant_matches / (2 * duration), 2),
                  HBM=100.0 if hotel and hotel["budget_level"] == case["budget_level"] else 0.0)
    valid = bool(hotel) and isinstance(trip.get("days"), list) and len(days) == duration
    all_activities = []
    for index, day in enumerate(days, 1):
        if not isinstance(day, dict):
            valid = False
            continue
        valid = valid and type(day.get("day")) is int and day.get("day") == index
        for field in ("activities", "restaurants"):
            entries = day.get(field)
            if not isinstance(entries, list):
                valid = False
                continue
            valid = valid and len(entries) == 2
            for pid in entries:
                if not isinstance(pid, str) or pid not in data[field]:
                    valid = False
                if field == "activities" and isinstance(pid, str):
                    all_activities.append(pid)
    valid = valid and len(all_activities) == len(set(all_activities))
    scores["IFR"] = 100.0 if valid else 0.0
    return scores


def requested_names(events, attempt=None):
    names = []
    for event in events:
        if event.get("kind") != "http_response" or (attempt is not None and event.get("attempt") != attempt):
            continue
        body = event.get("body")
        candidates = body.get("candidates", []) if isinstance(body, dict) else []
        if not isinstance(candidates, list) or not candidates:
            continue
        first = candidates[0]
        content = first.get("content") if isinstance(first, dict) else None
        parts = content.get("parts", []) if isinstance(content, dict) else []
        for part in parts if isinstance(parts, list) else []:
            call = part.get("functionCall") if isinstance(part, dict) else None
            if isinstance(call, dict) and isinstance(call.get("name"), str):
                names.append(call["name"])
    return names


def response_text(body):
    """Pinned SDK semantics: first candidate, concatenate non-thought text parts."""
    candidates = body.get("candidates", []) if isinstance(body, dict) else []
    first = candidates[0] if isinstance(candidates, list) and candidates else None
    content = first.get("content") if isinstance(first, dict) else None
    parts = content.get("parts", []) if isinstance(content, dict) else []
    text = [part["text"] for part in parts if isinstance(part, dict)
            and isinstance(part.get("text"), str) and part.get("thought") is not True]
    return "".join(text) if text else None


def mean(values):
    values = list(values)
    require(bool(values), "Cannot average an empty group")
    return math.fsum(values) / len(values)


def stdev(values):
    values = list(values)
    require(len(values) >= 2, "Sample SD requires at least two values")
    center = mean(values)
    return math.sqrt(math.fsum((value - center) ** 2 for value in values) / (len(values) - 1))


def numerical_match(first, second):
    if type(first) in (int, float) and type(second) in (int, float):
        return math.isfinite(first) and math.isfinite(second) and abs(first - second) <= 1e-9
    if isinstance(first, dict) and isinstance(second, dict):
        return first.keys() == second.keys() and all(numerical_match(first[k], second[k]) for k in first)
    return first == second


def aggregate(rows, cases):
    result = {}
    for metric in METRICS:
        values = [r[metric] for r in rows]
        seed_means = {str(seed): mean(r[metric] for r in rows if r["seed"] == seed) for seed in SEEDS}
        case_means = {case["case_id"]: mean(r[metric] for r in rows if r["case_id"] == case["case_id"])
                      for case in cases}
        result[metric] = {
            "mean": mean(values),
            "across_runs": {"n": len(values), "sample_sd": stdev(values)},
            "between_seed_means": {"n": 3, "sample_sd": stdev(seed_means.values()), "means": seed_means},
            "between_case_means": {"n": len(cases), "sample_sd": stdev(case_means.values())},
            "per_case": {case["case_id"]: {"mean": case_means[case["case_id"]], "n": 3,
                          "sample_sd": stdev(r[metric] for r in rows if r["case_id"] == case["case_id"])}
                         for case in cases},
        }
    return result


def check_record(directory, case, seed, identity, identity_hash, data):
    label = f"{case['case_id']}_seed{seed}"
    folder = contained_file(directory, label)
    record_path = contained_file(directory, f"{label}/record.json")
    checksum = contained_file(directory, f"{label}/record.sha256")
    request_path = contained_file(directory, f"{label}/request.json")
    if not all(path.is_file() for path in (record_path, checksum, request_path)):
        return None
    require(digest(record_path) == checksum.read_text().strip(), f"{label}: record checksum mismatch")
    record, request = read_json(record_path), read_json(request_path)
    meta, generation = record["metadata"], record["generation_result"]
    require(record["case_id"] == case["case_id"] and type(record["seed"]) is int and record["seed"] == seed
            and record["user_input"] == case and record["run_id"] == label, f"{label}: record inputs differ")
    require(record["experiment_version"] == identity["experiment_version"], f"{label}: experiment version differs")
    require(request["case"] == case and request["seed"] == seed
            and request["experiment_identity_sha256"] == identity_hash, f"{label}: request identity differs")
    require(meta["experiment_identity_sha256"] == identity_hash, f"{label}: manifest identity differs")
    for key in ("source_sha256", "dataset_sha256"):
        require(meta[key] == identity[key], f"{label}: {key} differs")
    require(meta["generation_settings"] == identity["settings"], f"{label}: settings differ")
    require(meta["evidence_mode"] == generation["provider_mode"] == "live", f"{label}: not live evidence")
    require(meta["model"] == generation["model"] == identity["settings"]["model"]
            and meta["temperature"] == 0, f"{label}: model/temperature differs")
    events, attempts = generation["trace"], generation["attempts"]
    require(isinstance(events, list) and bool(events) and isinstance(attempts, list) and bool(attempts),
            f"{label}: missing attempt/trace evidence")
    require([e["event_number"] for e in events] == list(range(1, len(events) + 1)), f"{label}: event sequence differs")
    require([a["number"] for a in attempts] == list(range(1, len(attempts) + 1))
            and len(attempts) <= identity["settings"]["max_attempts"], f"{label}: invalid attempt sequence")
    require(all(type(e["attempt"]) is int and 1 <= e["attempt"] <= len(attempts) for e in events),
            f"{label}: invalid event attempt")
    require([e["attempt"] for e in events if e["kind"] == "attempt_started"] == list(range(1, len(attempts) + 1)),
            f"{label}: attempt-start journal differs")
    require(all(a["status"] == "failed" for a in attempts[:-1])
            and attempts[-1]["status"] in ("failed", "response_received"), f"{label}: unfinished/contradictory attempts")
    journal = contained_file(directory, f"{label}/events.jsonl")
    journal_available = journal.is_file()
    if journal_available:
        observed = [strict_json(line) for line in journal.read_text().splitlines()]
        require(observed == events, f"{label}: journal differs from record trace")
    prompt = generation["prompt"]
    require(isinstance(prompt, str) and hashlib.sha256(prompt.encode()).hexdigest() == generation["prompt_sha256"],
            f"{label}: prompt checksum differs")
    # The frozen prompt is shared across cases; derive its exact text from the
    # preserved reference assignment, without importing/executing a notebook.
    require(prompt == baseline_prompt(case), f"{label}: prompt differs from frozen baseline")
    requests = [e for e in events if e["kind"] == "http_request"]
    responses = [e for e in events if e["kind"] == "http_response"]
    numbers = [e["request_number"] for e in requests]
    require(len(numbers) == len(set(numbers)), f"{label}: duplicate HTTP request numbers")
    response_numbers = [e["request_number"] for e in responses]
    require(len(response_numbers) == len(set(response_numbers)), f"{label}: duplicate HTTP response numbers")
    require(meta["provider_http_requests"] == meta["live_http_requests"] == len(requests), f"{label}: HTTP count differs")
    require(all(e["request_number"] in numbers for e in responses), f"{label}: response without recorded request")
    request_attempts = {e["request_number"]: e["attempt"] for e in requests}
    require(all(e["attempt"] == request_attempts[e["request_number"]] for e in responses),
            f"{label}: HTTP request/response attempt differs")
    for event in requests:
        require("headers" not in event and "?" not in event["path"], f"{label}: unexpected request headers/query")
        require(event["method"] == "POST" and event["path"].endswith(
            f"/models/{identity['settings']['model']}:generateContent"), f"{label}: unexpected HTTP endpoint")
        body = event["body"]
        require(body["generationConfig"]["seed"] == seed and body["generationConfig"]["temperature"] == 0,
                f"{label}: HTTP seed/temperature differs")
        require(body["contents"][0]["parts"][0]["text"] == prompt, f"{label}: HTTP prompt differs")
    raw, normalized = generation.get("raw_text"), generation.get("normalized_text")
    model_events = [e for e in events if e["kind"] == "model_response"]
    if attempts[-1]["status"] == "response_received":
        terminal_responses = [e for e in responses if e["attempt"] == len(attempts) and e["status_code"] == 200]
        require(bool(terminal_responses) and len(model_events) == 1, f"{label}: completed response evidence missing")
        require(response_text(terminal_responses[-1]["body"]) == raw, f"{label}: raw text differs from final HTTP response")
        snapshot = model_events[0]
        require(snapshot["attempt"] == len(attempts) and snapshot["raw_text"] == raw
                and snapshot["normalized_text"] == normalized and snapshot["response"] == generation["response"]
                and snapshot["history"] == generation["provider_history"], f"{label}: model response snapshot differs")
        require(response_text(generation["response"]) == raw, f"{label}: stored provider response text differs")
    else:
        require(not model_events and raw is None, f"{label}: failed provider attempt has unexplained response text")
    require(normalize(raw) == normalized, f"{label}: normalization differs")
    parsed = None
    if isinstance(normalized, str):
        try:
            value = strict_json(normalized)
            parsed = value if isinstance(value, dict) else None
        except (ValueError, TypeError, RecursionError):
            pass
    require(type(record["generation_success"]) is bool
            and generation["generation_success"] is record["generation_success"], f"{label}: success flags differ")
    require(record["generation_success"] == (parsed is not None), f"{label}: parse/success flag differs")
    require(parsed == generation.get("itinerary"), f"{label}: response and itinerary differ")
    if record["generation_success"]:
        require(generation.get("generation_error") is None, f"{label}: stale terminal error on success")
        require(attempts[-1]["status"] == "response_received", f"{label}: success without a completed response")
    else:
        require(isinstance(generation.get("generation_error"), dict), f"{label}: failure without a terminal error")
    scores = independently_score(parsed, case, data)
    names = requested_names(events, len(attempts))
    require(names == generation["tool_calls"], f"{label}: final-attempt requested names differ")
    require(requested_names(events) == generation["all_attempt_tool_calls"], f"{label}: all-attempt names differ")
    executed = [e["name"] for e in events if e["kind"] == "tool_call" and e["attempt"] == len(attempts)]
    require(executed == generation["executed_tool_calls"], f"{label}: executed-tool names differ")
    scores["RTC"] = round(100 * len(set(names) & REQUIRED_TOOLS) / 3, 2)
    for metric in METRICS:
        saved = record["RTC"] if metric == "RTC" else record["evaluation"][metric]
        require(type(saved) in (int, float) and math.isfinite(saved) and saved == scores[metric],
                f"{label}: independently recomputed {metric} differs")
    require(record["evaluation"]["feasible"] is (scores["IFR"] == 100), f"{label}: feasibility flag differs")
    terminal = generation.get("generation_error")
    terminal_summary = {k: terminal[k] for k in ("type", "provider_error_type", "code") if k in terminal} if isinstance(terminal, dict) else None
    return {"case_id": case["case_id"], "seed": seed, **scores,
            "generation_success": record["generation_success"],
            "generation_error": terminal_summary,
            "journal_verified": journal_available, "attempts": len(attempts),
            "http_requests": len(requests), "http_statuses": [e["status_code"] for e in responses],
            "provider_model_versions": sorted({e["body"]["modelVersion"] for e in responses
                                               if isinstance(e.get("body"), dict) and isinstance(e["body"].get("modelVersion"), str)}),
            "record_sha256": digest(record_path)}


def baseline_prompt(case):
    # Independent exact reconstruction of the archived concatenated prompt.
    return ("You are a single-agent Riyadh travel planner. "
            f"Plan a {case['trip_duration']}-day trip. "
            f"User interests: {json.dumps(case['interests'])}. "
            f"Budget level: {case['budget_level']}. "
            "Use all three tools: find_activities, find_restaurants, and find_hotels. "
            "Select exactly one hotel for the whole trip. "
            "Select exactly two activities and two restaurants per day. "
            "Do not repeat activities. Only select place_ids returned by the tools. "
            "Use the requested budget level for hotels and restaurants. "
            "Prioritize activities matching the user's interests. "
            "Return ONLY valid JSON with keys hotel_id and days. "
            "Each day must contain day, activities, and restaurants. "
            "Activities and restaurants must each contain exactly two IDs. "
            "Do not include markdown or explanations.")


def verify_directory(directory):
    directory = Path(directory).resolve()
    manifest = read_json(contained_file(directory, "manifest.json"))
    identity, identity_hash = manifest["identity"], manifest["identity_sha256"]
    require(fingerprint(identity) == identity_hash, "Manifest identity checksum differs")
    reference_path = ROOT / "reference/golden_cases_m5.json"
    reference = read_json(reference_path)
    cases = reference["golden_set"]
    require(len(cases) == 20 and len({c["case_id"] for c in cases}) == 20, "Frozen golden cases are not 20 unique IDs")
    require(identity["cases"] == cases and identity["seeds"] == list(SEEDS),
            "Not the complete formal 20-case/three-seed cohort; pilot/partial declarations are not a baseline")
    require(identity["evidence_mode"] == "live", "Fixture/mock evidence is not a formal live cohort")
    require(identity["scorer_version"] == "m5-offline-v3" and identity["generation_policy"] == "m5-gemini-v3",
            "Unreviewed scoring or generation policy")
    require(identity["settings"]["model"] == "gemini-3.5-flash-lite" and identity["settings"]["temperature"] == 0,
            "Unreviewed model or temperature")
    require(identity["settings"]["max_attempts"] == 3 and identity["settings"]["maximum_remote_calls"] == 10,
            "Formal cohort attempt/remote-call policy differs")
    require(identity["expected_sdk_version"] == identity["python_packages"]["google-genai"] == "1.30.0"
            and identity["csv_float_precision"] == "round_trip", "SDK/CSV parsing policy differs")
    source_files = {str(p.relative_to(ROOT)) for p in (ROOT / "m5eval").glob("*.py")}
    source_files.update({"requirements.txt", "requirements-gemini.txt"})
    require(set(identity["source_sha256"]) == source_files, "Source fingerprint coverage differs")
    for name, expected in identity["source_sha256"].items():
        require(digest(contained_file(ROOT, name)) == expected, f"Source fingerprint differs: {name}")
    for name in ("activities", "restaurants", "hotels"):
        require(digest(ROOT / "data" / f"{name}.csv") == identity["dataset_sha256"][name], f"Dataset differs: {name}")
    data = datasets()
    expected = [(case, seed) for case in cases for seed in SEEDS]
    expected_directories = {f"{case['case_id']}_seed{seed}" for case, seed in expected}
    require(not {p.name for p in directory.iterdir() if p.is_dir()} - expected_directories,
            "Unexpected run directories; do not mix cohorts")
    rows, missing = [], []
    for case, seed in expected:
        row = check_record(directory, case, seed, identity, identity_hash, data)
        if row is None:
            missing.append({"case_id": case["case_id"], "seed": seed})
        else:
            rows.append(row)
    complete = not missing
    stats = aggregate(rows, cases) if complete else None
    saved_summary = directory / "summary.json"
    summary_verified = False
    if complete and saved_summary.is_file():
        summary = read_json(saved_summary)
        require(summary["evidence_mode"] == "live" and summary["records"] == 60
                and summary["is_formal_live_20_case_3_seed_cohort"] is True,
                "Saved summary cohort declaration differs")
        require(numerical_match(summary["statistics"], stats), "Saved summary differs from independent aggregation")
        summary_verified = True
    return {"status": "PASS_EVIDENCE_AUDIT" if complete else "INCOMPLETE",
            "scope": "Independent saved-evidence checks and rescoring, not a model-quality pass or provider attestation",
            "experiment_version": identity["experiment_version"], "identity_sha256": identity_hash,
            "source_files_matching": len(source_files), "datasets_matching": 3,
            "expected_records": 60, "verified_records": len(rows), "missing_or_incomplete_pairs": missing,
            "generation_successes": sum(r["generation_success"] for r in rows),
            "generation_failures": [r for r in rows if not r["generation_success"]],
            "structurally_valid_runs": sum(r["IFR"] == 100 for r in rows),
            "parsed_but_structurally_invalid_pairs": [{"case_id": r["case_id"], "seed": r["seed"]}
                                                     for r in rows if r["generation_success"] and r["IFR"] == 0],
            "provider_model_versions_observed": sorted({version for r in rows for version in r["provider_model_versions"]}),
            "journals_verified": sum(r["journal_verified"] for r in rows),
            "saved_summary_verified": summary_verified, "statistics": stats, "per_run": rows,
            "sd_definition": "sample SD (n-1): 60 run values, 20 case means and 3 seed means, separately",
            "aggregation_method": "independent math.fsum/n mean and explicit squared-deviation/(n-1) sample SD",
            "saved_summary_comparison_tolerance": 1e-9,
            "limits": ["No provider calls were made by this auditor.",
                       "Checksums show internal integrity, not cryptographic provider attestation.",
                       "Requested seed labels do not verify provider seed effectiveness.",
                       "No currency cost or billing token total is inferred.",
                       "New-cohort evidence does not recover original historical V2 outputs.",
                       "Missing separate journals, if any, are reported; checksummed record traces remain the RTC source."]}


def verify(source):
    """Accept an extracted directory or safely inspect the original evidence ZIP."""
    source = Path(source).resolve()
    if source.is_dir():
        return verify_directory(source)
    require(source.is_file() and zipfile.is_zipfile(source), "Expected an extracted cohort directory or ZIP")
    require(source.stat().st_size <= 100_000_000, "Evidence ZIP exceeds 100 MB safety bound")
    with TemporaryDirectory(prefix="m5-cohort-audit-") as temporary:
        destination = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            members = archive.infolist()
            require(len(members) <= 5000, "Evidence ZIP has too many members")
            require(sum(info.file_size for info in members) <= 200_000_000, "Expanded evidence exceeds 200 MB safety bound")
            names = set()
            for info in members:
                member = PurePosixPath(info.filename)
                require(not member.is_absolute() and ".." not in member.parts
                        and "\\" not in info.filename and "\x00" not in info.orig_filename
                        and not re.match(r"^[A-Za-z]:", info.filename), "Unsafe evidence archive path")
                require(not stat.S_ISLNK(info.external_attr >> 16), "Symlink in evidence archive")
                require(not info.flag_bits & 1, "Encrypted evidence members are unsupported")
                require(info.filename not in names, "Duplicate evidence archive member")
                names.add(info.filename)
            archive.extractall(destination)
        candidates = [p.parent for p in destination.rglob("manifest.json")
                      if p.parent.name == "baseline-v3-20261107"]
        require(len(candidates) == 1, "ZIP must contain exactly one baseline-v3-20261107 root; pilot folders are not a cohort")
        report = verify_directory(candidates[0])
        report["archive"] = {"filename": source.name, "sha256": digest(source),
                             "member_count": len(members),
                             "selected_cohort_root": candidates[0].relative_to(destination).as_posix()}
        report["limits"].append("Other archive folders, including a separate pilot, are not merged into cohort statistics.")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=ROOT / "evidence/cohorts/baseline-v3-20261107.zip",
                        help="Formal directory or original ZIP; default: evidence/cohorts/baseline-v3-20261107.zip")
    parser.add_argument("--output", type=Path, help="Create a new JSON audit report; existing files are never overwritten")
    args = parser.parse_args()
    try:
        report = verify(args.directory)
        exit_code = 0 if report["status"] == "PASS_EVIDENCE_AUDIT" else 2
    except (AuditError, OSError, ValueError, TypeError, KeyError, RecursionError, zipfile.BadZipFile) as error:
        # Never print raw evidence, prompts, opaque signatures or arbitrary error values.
        report = {"status": "FAIL", "error_type": type(error).__name__,
                  "message": str(error) if isinstance(error, AuditError) else "Malformed or unavailable evidence; inspect locally",
                  "statistics": None}
        exit_code = 1
    payload = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output is not None:
        destination = args.output.resolve()
        evidence_root = args.directory.resolve()
        require(destination != evidence_root and evidence_root not in destination.parents,
                "Audit output must be outside preserved evidence")
        for name in ("source", "data", "reference", "m5eval", "tests", "scripts", "notebooks"):
            protected = (ROOT / name).resolve()
            require(destination != protected and protected not in destination.parents,
                    "Audit output cannot enter a preserved or code directory")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as file:
            file.write(payload)
    print(payload, end="")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
