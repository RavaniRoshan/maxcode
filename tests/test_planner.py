# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the planner role."""

import json
from pathlib import Path

import pytest

from maxcode.config import Config
from maxcode.errors import PlanError
from maxcode.roles.planner import build_plan_prompt, make_plan
from maxcode.schemas import ChatResult, Plan

VALID_PLAN = {
    "task": "fix the bug",
    "steps": [
        {
            "id": 1,
            "goal": "add a failing test",
            "files": ["tests/test_bug.py"],
            "checks": ["test"],
            "edits_tests": True,
        },
        {
            "id": 2,
            "goal": "fix the bug",
            "files": ["src/app.py"],
            "checks": ["test", "lint"],
            "edits_tests": False,
        },
    ],
}

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
        "limits": {"max_steps": 4},
    }
)


class FakeProvider:
    def __init__(self, results: list[ChatResult]) -> None:
        self.results = results
        self.calls: list[tuple[list[dict[str, str]], str]] = []

    def chat(self, messages: list[dict[str, str]], model: str) -> ChatResult:
        self.calls.append((list(messages), model))
        return self.results.pop(0)

    def close(self) -> None:
        pass


def test_prompt_file_has_the_contract_placeholders() -> None:
    path = Path(__file__).parents[1] / "src" / "maxcode" / "roles" / "prompts" / "planner.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("You are the planner for a coding tool.\n")
    for placeholder in (
        "{max_steps}",
        "{available_checks}",
        "{schema}",
        "{task}",
        "{repo_summary}",
    ):
        assert placeholder in text
    assert "Output one JSON object. Output nothing else." in text


def test_build_plan_prompt_fills_every_placeholder() -> None:
    prompt = build_plan_prompt(
        task="add a feature",
        repo_summary="src/app.py",
        max_steps=7,
        available_checks=["test", "lint"],
        schema={"type": "object"},
    )
    assert "add a feature" in prompt
    assert "src/app.py" in prompt
    assert "at most 7 steps" in prompt
    assert "test, lint" in prompt
    assert '"type": "object"' in prompt
    assert "{task}" not in prompt


def test_valid_json_returns_a_plan() -> None:
    provider = FakeProvider(
        [ChatResult(text=json.dumps(VALID_PLAN), input_tokens=10, output_tokens=5)]
    )
    usage: list[tuple[str, int, int]] = []
    plan = make_plan(
        "fix the bug",
        "tree",
        CFG,
        provider,
        usage_sink=lambda model, i, o: usage.append((model, i, o)),
    )
    assert isinstance(plan, Plan)
    assert len(plan.steps) == 2
    assert plan.steps[0].edits_tests is True
    assert usage == [("planner-model", 10, 5)]
    assert len(provider.calls) == 1


def test_code_fences_are_removed() -> None:
    fenced = "```json\n" + json.dumps(VALID_PLAN) + "\n```"
    provider = FakeProvider([ChatResult(text=fenced, input_tokens=1, output_tokens=2)])
    plan = make_plan("task", "summary", CFG, provider)
    assert plan.steps[0].id == 1


def test_invalid_then_valid_retries_once() -> None:
    provider = FakeProvider(
        [
            ChatResult(text="not json", input_tokens=3, output_tokens=1),
            ChatResult(text=json.dumps(VALID_PLAN), input_tokens=4, output_tokens=2),
        ]
    )
    usage: list[tuple[str, int, int]] = []
    plan = make_plan(
        "task",
        "summary",
        CFG,
        provider,
        usage_sink=lambda model, i, o: usage.append((model, i, o)),
    )
    assert plan.task == "fix the bug"
    assert len(provider.calls) == 2
    retry_messages = provider.calls[1][0]
    assert "Output the JSON only." in retry_messages[-1]["content"]
    assert len(usage) == 2


def test_invalid_twice_raises_plan_error() -> None:
    provider = FakeProvider(
        [
            ChatResult(text="nope", input_tokens=1, output_tokens=1),
            ChatResult(text="still nope", input_tokens=1, output_tokens=1),
        ]
    )
    with pytest.raises(PlanError) as excinfo:
        make_plan("task", "summary", CFG, provider)
    assert "Next:" in str(excinfo.value)
    assert len(provider.calls) == 2


def test_empty_steps_are_rejected() -> None:
    empty = {"task": "x", "steps": []}
    provider = FakeProvider(
        [
            ChatResult(text=json.dumps(empty), input_tokens=1, output_tokens=1),
            ChatResult(text=json.dumps(empty), input_tokens=1, output_tokens=1),
        ]
    )
    with pytest.raises(PlanError):
        make_plan("task", "summary", CFG, provider)


def plan_with_checks(checks: list[str]) -> dict:
    return {
        "task": "fix the bug",
        "steps": [
            {
                "id": 1,
                "goal": "fix it",
                "files": ["app.py"],
                "checks": checks,
                "edits_tests": False,
            }
        ],
    }


def test_unavailable_check_retries_with_valid_checks() -> None:
    provider = FakeProvider(
        [
            ChatResult(
                text=json.dumps(plan_with_checks(["build"])),
                input_tokens=1,
                output_tokens=1,
            ),
            ChatResult(
                text=json.dumps(plan_with_checks(["test"])),
                input_tokens=1,
                output_tokens=1,
            ),
        ]
    )
    plan = make_plan("task", "summary", CFG, provider, available_checks=["test"])
    assert plan.steps[0].checks == ["test"]
    assert len(provider.calls) == 2
    retry = provider.calls[1][0][-1]["content"]
    assert "check 'build' is not available" in retry
    assert "Valid checks: test, cmd:<command>" in retry


def test_unavailable_check_twice_raises_plan_error() -> None:
    provider = FakeProvider(
        [
            ChatResult(
                text=json.dumps(plan_with_checks(["lint"])),
                input_tokens=1,
                output_tokens=1,
            ),
            ChatResult(
                text=json.dumps(plan_with_checks(["lint"])),
                input_tokens=1,
                output_tokens=1,
            ),
        ]
    )
    with pytest.raises(PlanError) as excinfo:
        make_plan("task", "summary", CFG, provider, available_checks=["test"])
    message = str(excinfo.value)
    assert "lint" in message
    assert "Valid checks: test, cmd:<command>" in message
    assert len(provider.calls) == 2


def test_schema_rejects_invented_named_check_then_retries() -> None:
    provider = FakeProvider(
        [
            ChatResult(
                text=json.dumps(plan_with_checks(["flake8"])),
                input_tokens=1,
                output_tokens=1,
            ),
            ChatResult(
                text=json.dumps(plan_with_checks(["test"])),
                input_tokens=1,
                output_tokens=1,
            ),
        ]
    )
    plan = make_plan("task", "summary", CFG, provider, available_checks=["test"])
    assert plan.steps[0].checks == ["test"]
    assert len(provider.calls) == 2
    retry = provider.calls[1][0][-1]["content"]
    assert "flake8" in retry
    assert "Valid checks: test, cmd:<command>" in retry
