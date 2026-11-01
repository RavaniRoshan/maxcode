# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the worker role."""

from pathlib import Path

from maxcode.config import Config
from maxcode.roles.worker import build_worker_prompt, do_step
from maxcode.schemas import PlanStep

CFG = Config.model_validate(
    {
        "provider": {
            "main": {
                "base_url": "https://api.example.com/v1",
                "api_key_env": "MAXCODE_TEST_KEY",
            }
        },
        "planner": {"provider": "main", "model": "planner-model"},
        "worker": {"provider": "main", "model": "worker-model"},
        "protected": {"paths": ["**/*.lock"], "test_paths": ["tests/**"]},
    }
)

STEP = PlanStep(
    id=1,
    goal="fix the parser",
    files=["src/parser.py", "tests/test_parser.py"],
    checks=["test"],
    edits_tests=True,
)


def test_prompt_matches_section_24() -> None:
    prompt = build_worker_prompt(STEP, "add the feature", None, CFG.protected.paths)
    assert prompt.startswith("You are the worker for a coding tool.\n")
    assert "Complete this one step. Do not work on other steps." in prompt
    assert "Step goal: fix the parser" in prompt
    assert "Files to focus on: src/parser.py, tests/test_parser.py" in prompt
    assert "Task context: add the feature" in prompt
    assert "1. Change only what the step needs." in prompt
    assert "2. Do not edit these paths: **/*.lock" in prompt
    assert "3. Do not disable, skip, or delete any existing test." in prompt
    assert "4. Do not claim the step is done. A separate program checks your work." in prompt
    assert "5. Stop when you finish the edits." in prompt
    assert "The last attempt failed" not in prompt


def test_failure_block_appears_only_after_attempt_one() -> None:
    first = build_worker_prompt(STEP, "task", None, CFG.protected.paths)
    second = build_worker_prompt(STEP, "task", "AssertionError: expected 2", CFG.protected.paths)
    assert "The last attempt failed these checks." not in first
    assert "The last attempt failed these checks. Fix the cause." in second
    assert "AssertionError: expected 2" in second


def test_failure_output_is_cut_to_4000_characters() -> None:
    long_failure = "x" * 5000
    prompt = build_worker_prompt(STEP, "task", long_failure, CFG.protected.paths)
    assert "x" * 4000 in prompt
    assert "x" * 4001 not in prompt


def test_do_step_calls_engine_and_reports_usage(tmp_path: Path) -> None:
    from unittest.mock import patch

    from maxcode.schemas import EngineResult

    fake_result = EngineResult(exit_code=0, transcript="done", input_tokens=4, output_tokens=2)
    with patch("maxcode.roles.worker.run_step", return_value=fake_result) as mock_run:
        from maxcode.cost import CostMeter

        meter = CostMeter(CFG.pricing, cap_usd=10.0)
        result = do_step(STEP, None, CFG, task="task", repo=tmp_path, meter=meter)
        assert result is fake_result
        assert mock_run.called
        assert meter.tokens_in == 4
        assert meter.tokens_out == 2


def test_do_step_forwards_timeout(tmp_path: Path) -> None:
    from unittest.mock import patch

    from maxcode.schemas import EngineResult

    fake_result = EngineResult(exit_code=0, transcript="done")
    with patch("maxcode.roles.worker.run_step", return_value=fake_result) as mock_run:
        do_step(STEP, None, CFG, task="task", repo=tmp_path, timeout_s=42.0)
    assert mock_run.call_args.args[4] == 42.0
