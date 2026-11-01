# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the configured worker timeout."""

import subprocess
from pathlib import Path

import pytest

from maxcode.config import Config
from maxcode.loop import LoopDeps, run_task
from maxcode.schemas import EngineResult, Plan, PlanStep, RunOptions, StopReason


def init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def make_config(worker_timeout_s: float = 600.0) -> Config:
    return Config.model_validate(
        {
            "provider": {
                "main": {
                    "base_url": "https://api.example.com/v1",
                    "api_key_env": "MAXCODE_TEST_KEY",
                }
            },
            "planner": {"provider": "main", "model": "m"},
            "worker": {"provider": "main", "model": "m"},
            "limits": {"worker_timeout_s": worker_timeout_s, "max_steps": 1},
            "checks": {"test": "true"},
        }
    )


def make_plan() -> Plan:
    return Plan(task="t", steps=[PlanStep(id=1, goal="fix", checks=["test"])])


def test_loop_passes_configured_worker_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    seen: dict[str, float] = {}

    def fake_do_step(step, failure, cfg, **kwargs):
        seen["timeout_s"] = kwargs["timeout_s"]
        return EngineResult(exit_code=0, transcript="ok")

    monkeypatch.setattr("maxcode.loop.do_step", fake_do_step)
    monkeypatch.setattr("maxcode.loop.make_plan", lambda *args, **kwargs: make_plan())

    class FakeProvider:
        def close(self) -> None:
            pass

    result = run_task(
        "task",
        make_config(42.0),
        RunOptions(yes=True),
        repo=repo,
        provider=FakeProvider(),
    )
    assert result.exit_code == 0
    assert seen["timeout_s"] == 42.0


def test_worker_timeout_exits_3(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    restored: list[str] = []
    timed_out = EngineResult(exit_code=124, transcript="timeout", timed_out=True)

    def checkpoint_create(run_id: str, step_id: int) -> str:
        return f"refs/maxcode/{run_id}/{step_id}"

    def checkpoint_restore(ref: str) -> None:
        restored.append(ref)

    def verify(step, ref):
        raise AssertionError("verify must not run after a timeout")

    deps = LoopDeps(
        plan=lambda task, summary: make_plan(),
        work=lambda step, failure: timed_out,
        checkpoint_create=checkpoint_create,
        checkpoint_restore=checkpoint_restore,
        verify=verify,
        diff_stats=lambda ref: ([], 0),
        detect_checks=lambda: {"test": "true"},
        repo_summary=lambda: "summary",
        approve_plan=lambda plan: True,
    )
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=repo,
        deps=deps,
    )
    assert result.exit_code == 3
    assert result.stop_reason == StopReason.ERROR
    assert len(restored) == 1
    assert restored[0].endswith("/1")
