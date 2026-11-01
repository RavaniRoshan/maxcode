# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the benchmark runner."""

import csv
import json
import os
import subprocess
from pathlib import Path

import pytest

from maxcode.bench.report import summarize
from maxcode.bench.runner import DEFAULT_SUITE, _load_tasks, _repo_pythonpath, run_bench
from maxcode.config import Config
from maxcode.schemas import RunResult, StopReason


def init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def make_config() -> Config:
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


def clone_local(url: str, commit: str, dest: Path) -> None:
    subprocess.run(["git", "clone", "--quiet", url, str(dest)], check=True)


def write_task(suite: Path, repo: Path, score: str) -> None:
    suite.mkdir()
    (suite / "task-001.json").write_text(
        json.dumps(
            {
                "id": "task-001",
                "repo_url": str(repo),
                "commit": "HEAD",
                "task": "do something",
                "score": score,
            }
        ),
        encoding="utf-8",
    )


def read_results(out_dir: Path) -> list[dict[str, str]]:
    with (out_dir / "results.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_repo_pythonpath_adds_and_restores_src(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.delenv("PYTHONPATH", raising=False)
    with _repo_pythonpath(tmp_path):
        assert os.environ["PYTHONPATH"] == str(src)
    assert "PYTHONPATH" not in os.environ


def test_bench_writes_results_and_logs(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    write_task(suite, repo, "test -f marker.txt")

    log_path = tmp_path / "run.jsonl"
    log_path.write_text("", encoding="utf-8")

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
        (Path(repo) / "marker.txt").write_text("ran", encoding="utf-8")
        return RunResult(
            run_id="run1", passed=True, exit_code=0, cost_usd=0.25, log_path=str(log_path)
        )

    out_dir = tmp_path / "out"
    summary = run_bench(
        suite=suite,
        verifier=True,
        root=tmp_path,
        cfg=make_config(),
        out_dir=out_dir,
        run_task_fn=fake_run_task,
        clone_fn=clone_local,
    )
    assert summary.total == 1
    assert summary.passed == 1
    assert summary.invalid == 0
    assert summary.errors == 0
    assert (out_dir / "results.csv").is_file()
    assert (out_dir / "task-001" / "run.jsonl").is_file()
    row = read_results(out_dir)[0]
    assert row["baseline_status"] == "failed"
    assert row["status"] == "pass"


def test_bench_verifier_off_passes_flag(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    write_task(suite, repo, "test -f marker.txt")
    seen = {}

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
        (Path(repo) / "marker.txt").write_text("ran", encoding="utf-8")
        seen["verifier"] = options.verifier
        return RunResult(run_id="run1", passed=True, exit_code=0, cost_usd=0.0, log_path="")

    out_dir = tmp_path / "out"
    run_bench(
        suite=suite,
        verifier=False,
        root=tmp_path,
        cfg=make_config(),
        out_dir=out_dir,
        run_task_fn=fake_run_task,
        clone_fn=clone_local,
    )
    assert seen["verifier"] is False


def test_bench_baseline_pass_excludes_task(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    write_task(suite, repo, "true")
    calls: list[str] = []

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
        calls.append("worker")
        raise AssertionError("worker must not run when the baseline passes")

    out_dir = tmp_path / "out"
    summary = run_bench(
        suite=suite,
        verifier=True,
        root=tmp_path,
        cfg=make_config(),
        out_dir=out_dir,
        run_task_fn=fake_run_task,
        clone_fn=clone_local,
    )
    assert calls == []
    assert summary.total == 0
    assert summary.passed == 0
    assert summary.invalid == 1
    assert summary.errors == 0
    row = read_results(out_dir)[0]
    assert row["baseline_status"] == "passed"
    assert row["status"] == "invalid"
    assert row["excluded_reason"] == "baseline passed"
    report = summarize([out_dir])
    assert "Excluded from N" in report
    assert "task-001" in report


def test_bench_baseline_fail_keeps_task(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    write_task(suite, repo, "test -f marker.txt")

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
        (Path(repo) / "marker.txt").write_text("ran", encoding="utf-8")
        return RunResult(run_id="run1", passed=True, exit_code=0, cost_usd=0.5)

    out_dir = tmp_path / "out"
    summary = run_bench(
        suite=suite,
        verifier=True,
        root=tmp_path,
        cfg=make_config(),
        out_dir=out_dir,
        run_task_fn=fake_run_task,
        clone_fn=clone_local,
    )
    assert summary.total == 1
    assert summary.passed == 1
    assert summary.invalid == 0
    assert summary.errors == 0
    row = read_results(out_dir)[0]
    assert row["baseline_status"] == "failed"
    assert row["status"] == "pass"


def test_bench_worker_timeout_status_error(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    write_task(suite, repo, "test -f marker.txt")

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
        (Path(repo) / "marker.txt").write_text("ran", encoding="utf-8")
        return RunResult(
            run_id="run1",
            passed=False,
            exit_code=3,
            stop_reason=StopReason.ERROR,
        )

    out_dir = tmp_path / "out"
    summary = run_bench(
        suite=suite,
        verifier=True,
        root=tmp_path,
        cfg=make_config(),
        out_dir=out_dir,
        run_task_fn=fake_run_task,
        clone_fn=clone_local,
    )
    assert summary.total == 1
    assert summary.passed == 0
    assert summary.invalid == 0
    assert summary.errors == 1
    row = read_results(out_dir)[0]
    assert row["baseline_status"] == "failed"
    assert row["score_passed"] == "True"
    assert row["status"] == "error"


def test_default_suite_excludes_requests() -> None:
    tasks = _load_tasks(DEFAULT_SUITE)
    pinned = [task for task in tasks if task.get("repo_url")]
    assert len(pinned) == 15
    assert all("psf/requests" not in task["repo_url"] for task in pinned)
