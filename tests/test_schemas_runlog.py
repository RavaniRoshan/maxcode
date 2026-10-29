# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the data schemas and the JSONL run log."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from maxcode.errors import RunLogError
from maxcode.runlog import RunLog, new_run_id, read_events
from maxcode.schemas import CheckResult, EngineResult, Plan, PlanStep, RunOptions


def test_plan_accepts_named_and_command_checks() -> None:
    plan = Plan.model_validate(
        {
            "task": "fix it",
            "steps": [
                {
                    "id": 1,
                    "goal": "add a failing test",
                    "files": ["tests/test_x.py"],
                    "checks": ["test", "lint", "cmd:pytest tests/test_x.py -q"],
                    "edits_tests": True,
                }
            ],
        }
    )
    assert plan.steps[0].checks[2] == "cmd:pytest tests/test_x.py -q"


@pytest.mark.parametrize("bad_check", ["tests", "cmd:", "CMD:pytest", ""])
def test_plan_rejects_bad_check_names(bad_check: str) -> None:
    with pytest.raises(ValidationError):
        PlanStep(id=1, goal="x", files=[], checks=[bad_check])


def test_plan_requires_at_least_one_step() -> None:
    with pytest.raises(ValidationError):
        Plan(task="x", steps=[])


def test_engine_result_allows_missing_tokens() -> None:
    result = EngineResult(exit_code=0, transcript="done", seconds=1.25)
    assert result.input_tokens is None
    assert result.timed_out is False


def test_check_result_keeps_tail() -> None:
    result = CheckResult(
        name="test", command="pytest", passed=False, exit_code=1, output_tail="boom", seconds=0.1
    )
    assert result.output_tail == "boom"


def test_run_options_defaults() -> None:
    options = RunOptions()
    assert options.yes is False
    assert options.verifier is True
    assert options.max_cost_usd is None


def test_runlog_writes_and_reads_three_events(tmp_path: Path) -> None:
    path = tmp_path / ".maxcode" / "runs" / "run1" / "log.jsonl"
    log = RunLog(path, "run1")
    log.write("run_start", {"task": "hello", "config_hash": "abc", "repo_head": "dead"})
    log.write("plan", {"steps": [{"id": 1}]})
    log.write("stop", {"reason": "cost_cap"})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    raw = [json.loads(line) for line in lines]
    assert [item["type"] for item in raw] == ["run_start", "plan", "stop"]
    assert all(set(item) == {"ts", "run_id", "type", "data"} for item in raw)
    assert all(item["run_id"] == "run1" for item in raw)

    events = read_events(path)
    assert [event.type for event in events] == ["run_start", "plan", "stop"]
    assert events[2].data == {"reason": "cost_cap"}


def test_runlog_flushes_each_line(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    log = RunLog(path, "r")
    log.write("retry", {"step_id": 1, "attempt": 2})
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_new_run_id_is_unique_and_sortable() -> None:
    first = new_run_id()
    second = new_run_id()
    assert first != second
    assert first[:8].isdigit()


def test_read_events_rejects_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(RunLogError, match="log.jsonl"):
        read_events(path)
