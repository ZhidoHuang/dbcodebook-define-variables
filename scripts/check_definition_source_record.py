"""Validate source-search evidence before running a CHARLS definition."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


READY_STATUS = "READY"
LOGIC_RESULTS = {"clear", "reported_and_resolved"}
RESOLVED_ISSUE_STATUSES = {"resolved", "reported_and_resolved"}
EXPLORATION_ACTIONS = {
    "directory_open",
    "ordinary_search",
    "detail_open",
    "candidate_decision",
}
CANDIDATE_DECISIONS = {"include", "exclude", "partial"}
REQUIRED_LOGIC_CHECKS = (
    "period_coverage_checked",
    "same_name_drift_checked",
    "meaning_change_checked",
    "formula_or_derivation_checked",
    "naming_checked",
)


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        fail("source record must be a JSON object")
    return value


def nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be non-empty text")
    return value.strip()


def read_raw_vars(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "newname" not in reader.fieldnames:
            fail("raw_codebook.csv must contain a newname column")
        values = [(row.get("newname") or "").strip() for row in reader]
    if not values or any(not value for value in values):
        fail("raw_codebook.csv contains an empty newname")
    if len(values) != len(set(values)):
        fail("raw_codebook.csv contains duplicate newname values")
    return values


def extract_r_vector(source: str, object_name: str) -> list[str]:
    match = re.search(
        rf"(?ms)^\s*{re.escape(object_name)}\s*<-\s*c\((.*?)\)\s*$",
        source,
    )
    if not match:
        fail(f"R script does not define {object_name} <- c(...)")
    values = re.findall(r'["\']([^"\']+)["\']', match.group(1))
    if not values:
        fail(f"{object_name} is empty")
    return values


def extract_summary_paths(source: str) -> list[str]:
    return re.findall(
        r"""summary_path_part\(\s*["']([^"']+)["']\s*\)""",
        source,
    )


def validate_record(
    record_path: Path,
    r_script_path: Path,
    raw_codebook_path: Path,
    topic_id: str,
) -> dict:
    record = load_json(record_path)
    source = r_script_path.read_text(encoding="utf-8")

    schema_version = record.get("schema_version")
    if schema_version not in {1, 2}:
        fail("schema_version must be 1 or 2")
    if str(record.get("topic_id", "")).zfill(3) != topic_id:
        fail(f"topic_id must be {topic_id}")
    if record.get("status") != READY_STATUS:
        fail(f"status must be {READY_STATUS}")
    url = nonempty_text(record.get("dbcodebook_url"), "dbcodebook_url")
    if not re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?/", url):
        fail("dbcodebook_url must point to the local dbCodeBook website")
    nonempty_text(record.get("searched_at"), "searched_at")

    exploration_steps: set[int] = set()
    if schema_version == 2:
        if record.get("recording_mode") != "contemporaneous":
            fail("schema v2 recording_mode must be contemporaneous")
        exploration_log = record.get("exploration_log")
        if not isinstance(exploration_log, list) or not exploration_log:
            fail("schema v2 exploration_log must record the actual exploration sequence")
        for expected_step, item in enumerate(exploration_log, start=1):
            if not isinstance(item, dict):
                fail(f"exploration_log[{expected_step}] must be an object")
            step = item.get("step")
            if step != expected_step:
                fail("exploration_log steps must be consecutive and start at 1")
            action = item.get("action")
            if action not in EXPLORATION_ACTIONS:
                fail(
                    f"exploration_log[{expected_step}].action must be one of "
                    f"{sorted(EXPLORATION_ACTIONS)}"
                )
            for field in ("input", "observed", "decision", "reason"):
                nonempty_text(
                    item.get(field), f"exploration_log[{expected_step}].{field}"
                )
            exploration_steps.add(step)

    directories = record.get("directory_entries")
    if not isinstance(directories, list) or not directories:
        fail("directory_entries must contain at least one verified directory")
    directory_paths: set[str] = set()
    for index, item in enumerate(directories, start=1):
        if not isinstance(item, dict):
            fail(f"directory_entries[{index}] must be an object")
        full_path = nonempty_text(
            item.get("full_path"), f"directory_entries[{index}].full_path"
        )
        if not full_path.startswith("Core data >"):
            fail(f"directory_entries[{index}].full_path is not a full Core data path")
        if item.get("verified_in_ui") is not True:
            fail(f"directory_entries[{index}] was not verified in the website UI")
        nonempty_text(item.get("purpose"), f"directory_entries[{index}].purpose")
        directory_paths.add(full_path)

    searches = record.get("normal_searches")
    if not isinstance(searches, list) or not searches:
        fail("normal_searches must record the actual ordinary-search step")
    search_keywords: set[str] = set()
    for index, item in enumerate(searches, start=1):
        if not isinstance(item, dict):
            fail(f"normal_searches[{index}] must be an object")
        if item.get("performed") is True:
            keyword = nonempty_text(
                item.get("keyword"), f"normal_searches[{index}].keyword"
            )
            nonempty_text(item.get("result"), f"normal_searches[{index}].result")
            search_keywords.add(keyword)
        else:
            nonempty_text(item.get("reason"), f"normal_searches[{index}].reason")

    groups = record.get("source_groups")
    if not isinstance(groups, list) or not groups:
        fail("source_groups must contain at least one source group")
    recorded_raw: list[str] = []
    for index, item in enumerate(groups, start=1):
        if not isinstance(item, dict):
            fail(f"source_groups[{index}] must be an object")
        nonempty_text(item.get("concept"), f"source_groups[{index}].concept")
        variables = item.get("raw_variables")
        if not isinstance(variables, list) or not variables:
            fail(f"source_groups[{index}].raw_variables must not be empty")
        for variable in variables:
            recorded_raw.append(nonempty_text(variable, "raw variable"))
        years = item.get("years")
        if not isinstance(years, list) or not years:
            fail(f"source_groups[{index}].years must not be empty")
        if item.get("detail_verified") is not True:
            fail(f"source_groups[{index}] lacks website detail verification")
        if schema_version == 2:
            nonempty_text(
                item.get("selection_reason"),
                f"source_groups[{index}].selection_reason",
            )
            evidence_steps = item.get("evidence_steps")
            if not isinstance(evidence_steps, list) or not evidence_steps:
                fail(f"source_groups[{index}].evidence_steps must not be empty")
            if any(step not in exploration_steps for step in evidence_steps):
                fail(f"source_groups[{index}] references an unknown exploration step")
        discovery = item.get("discovery")
        if not isinstance(discovery, dict):
            fail(f"source_groups[{index}].discovery must be an object")
        mode = discovery.get("mode")
        value = nonempty_text(
            discovery.get("value"), f"source_groups[{index}].discovery.value"
        )
        if mode == "directory":
            if value not in directory_paths:
                fail(f"source_groups[{index}] uses an unrecorded directory")
        elif mode == "ordinary_search":
            if value not in search_keywords:
                fail(f"source_groups[{index}] uses an unrecorded search keyword")
        else:
            fail(f"source_groups[{index}].discovery.mode is invalid")

    if len(recorded_raw) != len(set(recorded_raw)):
        fail("source_groups contain duplicate raw variables")
    raw_vars = read_raw_vars(raw_codebook_path)
    if set(recorded_raw) != set(raw_vars):
        missing = sorted(set(raw_vars) - set(recorded_raw))
        extra = sorted(set(recorded_raw) - set(raw_vars))
        fail(f"source_groups/raw_codebook mismatch; missing={missing}, extra={extra}")

    if schema_version == 2:
        candidate_decisions = record.get("candidate_decisions")
        if not isinstance(candidate_decisions, list) or not candidate_decisions:
            fail("schema v2 candidate_decisions must not be empty")
        selected_candidates: list[str] = []
        for index, item in enumerate(candidate_decisions, start=1):
            if not isinstance(item, dict):
                fail(f"candidate_decisions[{index}] must be an object")
            nonempty_text(item.get("concept"), f"candidate_decisions[{index}].concept")
            decision = item.get("decision")
            if decision not in CANDIDATE_DECISIONS:
                fail(
                    f"candidate_decisions[{index}].decision must be one of "
                    f"{sorted(CANDIDATE_DECISIONS)}"
                )
            selected = item.get("selected_raw")
            excluded = item.get("excluded_raw")
            if not isinstance(selected, list) or not isinstance(excluded, list):
                fail(
                    f"candidate_decisions[{index}] selected_raw/excluded_raw "
                    "must be lists"
                )
            selected = [
                nonempty_text(value, "selected candidate raw") for value in selected
            ]
            excluded = [
                nonempty_text(value, "excluded candidate raw") for value in excluded
            ]
            if decision == "include" and not selected:
                fail(f"candidate_decisions[{index}] include decision selects no raw")
            if decision == "exclude" and selected:
                fail(f"candidate_decisions[{index}] exclude decision selects raw")
            if set(selected) & set(excluded):
                fail(f"candidate_decisions[{index}] selects and excludes the same raw")
            nonempty_text(item.get("reason"), f"candidate_decisions[{index}].reason")
            evidence_steps = item.get("evidence_steps")
            if not isinstance(evidence_steps, list) or not evidence_steps:
                fail(f"candidate_decisions[{index}].evidence_steps must not be empty")
            if any(step not in exploration_steps for step in evidence_steps):
                fail(
                    f"candidate_decisions[{index}] references an unknown exploration step"
                )
            selected_candidates.extend(selected)
        if len(selected_candidates) != len(set(selected_candidates)):
            fail("candidate_decisions select duplicate raw variables")
        if set(selected_candidates) != set(raw_vars):
            missing = sorted(set(raw_vars) - set(selected_candidates))
            extra = sorted(set(selected_candidates) - set(raw_vars))
            fail(
                "candidate_decisions/raw_codebook mismatch; "
                f"missing={missing}, extra={extra}"
            )

    approved_names = record.get("approved_analysis_vars")
    if not isinstance(approved_names, list) or not approved_names:
        fail("approved_analysis_vars must not be empty")
    approved_names = [
        nonempty_text(value, "approved analysis variable") for value in approved_names
    ]
    if len(approved_names) != len(set(approved_names)):
        fail("approved_analysis_vars contains duplicates")
    r_analysis_vars = extract_r_vector(source, "analysis_vars")
    if approved_names != r_analysis_vars:
        fail(
            "analysis_vars differs from the approved naming list; "
            f"approved={approved_names}, R={r_analysis_vars}"
        )

    r_summary_paths = extract_summary_paths(source)
    unrecorded_paths = sorted(set(r_summary_paths) - directory_paths)
    if unrecorded_paths:
        fail(f"R summary uses directories absent from source evidence: {unrecorded_paths}")

    logic_review = record.get("logic_review")
    if not isinstance(logic_review, dict):
        fail("logic_review must be an object")
    for field in REQUIRED_LOGIC_CHECKS:
        if logic_review.get(field) is not True:
            fail(f"logic_review.{field} must be true")
    result = logic_review.get("result")
    if result not in LOGIC_RESULTS:
        fail(f"logic_review.result must be one of {sorted(LOGIC_RESULTS)}")

    issues = record.get("logic_issues")
    if not isinstance(issues, list):
        fail("logic_issues must be a list")
    for index, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            fail(f"logic_issues[{index}] must be an object")
        nonempty_text(issue.get("description"), f"logic_issues[{index}].description")
        nonempty_text(issue.get("impact"), f"logic_issues[{index}].impact")
        status = issue.get("status")
        if status not in RESOLVED_ISSUE_STATUSES:
            fail(f"logic_issues[{index}] is unresolved and must be reported")
        nonempty_text(issue.get("reported_to_user_at"), "reported_to_user_at")
        nonempty_text(issue.get("decision"), f"logic_issues[{index}].decision")
    if issues and result != "reported_and_resolved":
        fail("logic_review.result must be reported_and_resolved when issues exist")

    return {
        "ok": True,
        "topic_id": topic_id,
        "schema_version": schema_version,
        "exploration_steps": len(exploration_steps),
        "directories": len(directory_paths),
        "ordinary_searches": len(search_keywords),
        "raw_variables": len(raw_vars),
        "analysis_vars": approved_names,
        "logic_issues": len(issues),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--r-script", required=True, type=Path)
    parser.add_argument("--raw-codebook", required=True, type=Path)
    parser.add_argument("--topic-id", required=True)
    args = parser.parse_args()
    try:
        result = validate_record(
            args.record, args.r_script, args.raw_codebook, args.topic_id.zfill(3)
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"SOURCE_RECORD_FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
