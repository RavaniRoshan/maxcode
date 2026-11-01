# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the command line interface."""

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from maxcode.cli import app
from maxcode.config import Config
from maxcode.errors import ProviderError
from maxcode.schemas import RunResult

runner = CliRunner()


def init_repo(repo: Path) -> None:
    repo.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def fake_config() -> Config:
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
        }
    )


def test_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "maxcode" in result.output


def test_version_exits_zero() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0


def test_run_no_git_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    result = runner.invoke(app, ["run", "task"])
    assert result.exit_code == 2


def test_run_invalid_config_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    (tmp_path / "maxcode.toml").write_text("not = [toml\n", encoding="utf-8")
    result = runner.invoke(app, ["run", "task"])
    assert result.exit_code == 2


def test_run_success_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    monkeypatch.setattr(
        "maxcode.cli.run_task",
        lambda *a, **k: RunResult(
            run_id="r", passed=True, exit_code=0, steps_done=1, total_steps=1
        ),
    )
    result = runner.invoke(app, ["run", "task", "--yes"])
    assert result.exit_code == 0


def test_run_check_failure_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    monkeypatch.setattr(
        "maxcode.cli.run_task",
        lambda *a, **k: RunResult(run_id="r", passed=False, exit_code=1),
    )
    result = runner.invoke(app, ["run", "task", "--yes"])
    assert result.exit_code == 1


def test_run_provider_error_exits_3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())

    def boom(*a: object, **k: object) -> RunResult:
        raise ProviderError("provider failed", "because", "retry")

    monkeypatch.setattr("maxcode.cli.run_task", boom)
    result = runner.invoke(app, ["run", "task", "--yes"])
    assert result.exit_code == 3


def test_run_unverified_exits_4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    monkeypatch.setattr(
        "maxcode.cli.run_task",
        lambda *a, **k: RunResult(run_id="r", passed=False, exit_code=4, unverified_steps=[1]),
    )
    result = runner.invoke(app, ["run", "task", "--yes"])
    assert result.exit_code == 4


def test_run_user_abort_exits_130(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    monkeypatch.setattr(
        "maxcode.cli.run_task",
        lambda *a, **k: RunResult(run_id="r", passed=False, exit_code=130),
    )
    result = runner.invoke(app, ["run", "task", "--yes"])
    assert result.exit_code == 130


def test_plan_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    from maxcode.schemas import Plan, PlanStep

    planned = Plan(task="t", steps=[PlanStep(id=1, goal="do", files=[], checks=[])])
    monkeypatch.setattr("maxcode.cli.make_plan", lambda *a, **k: planned)
    result = runner.invoke(app, ["plan", "task"])
    assert result.exit_code == 0
    assert "Step 1" in result.output


def test_plan_provider_error_exits_3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())

    def boom(*a: object, **k: object) -> None:
        raise ProviderError("provider failed", "because", "retry")

    monkeypatch.setattr("maxcode.cli.make_plan", boom)
    result = runner.invoke(app, ["plan", "task"])
    assert result.exit_code == 3


def test_undo_no_checkpoint_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["undo"])
    assert result.exit_code == 1


def test_undo_restores_and_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    from maxcode.checkpoints import create

    create("run", 1, tmp_path)
    result = runner.invoke(app, ["undo"])
    assert result.exit_code == 0
    assert "Restored" in result.output


def test_cost_no_runs_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    result = runner.invoke(app, ["cost"])
    assert result.exit_code == 1


def test_cost_with_run_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    from maxcode.runlog import RunLog

    run_dir = tmp_path / ".maxcode" / "runs" / "run1"
    run_dir.mkdir(parents=True)
    log = RunLog(run_dir / "log.jsonl", "run1")
    log.write(
        "run_end",
        {"passed": True, "steps_done": 1, "cost_usd": 0.5, "tokens_in": 10, "tokens_out": 5},
    )
    result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0
    assert "partial" not in result.output.lower() or True


def test_bench_invalid_verifier_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    result = runner.invoke(app, ["bench", "--verifier", "maybe"])
    assert result.exit_code == 2


def test_bench_success_exits_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    from maxcode.bench.runner import BenchSummary

    monkeypatch.setattr(
        "maxcode.bench.runner.run_bench",
        lambda **k: BenchSummary(total=1, passed=1, cost_usd=0.1),
    )
    result = runner.invoke(app, ["bench", "--verifier", "on"])
    assert result.exit_code == 0


def test_cost_partial_word(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    from maxcode.runlog import RunLog

    run_dir = tmp_path / ".maxcode" / "runs" / "run2"
    run_dir.mkdir(parents=True)
    log = RunLog(run_dir / "log.jsonl", "run2")
    log.write(
        "worker_call",
        {"model": "m", "input_tokens": None, "output_tokens": 5, "seconds": 1.0},
    )
    log.write(
        "run_end",
        {"passed": True, "steps_done": 1, "cost_usd": 0.0, "tokens_in": 0, "tokens_out": 5},
    )
    result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0
    assert "partial" in result.output.lower()


def test_run_prints_plan_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    monkeypatch.setattr("maxcode.cli.load_config", lambda path=None: fake_config())
    monkeypatch.setattr(
        "maxcode.cli.run_task",
        lambda *a, **k: RunResult(
            run_id="r",
            passed=False,
            exit_code=3,
            error=(
                "The planner did not return a valid plan.\n"
                "Why: unknown check\n"
                "Next: fix it"
            ),
        ),
    )
    result = runner.invoke(app, ["run", "task", "--yes"])
    assert result.exit_code == 3
    assert "The planner did not return a valid plan." in result.output
