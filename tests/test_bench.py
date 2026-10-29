# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the benchmark runner."""

import json
import subprocess
from pathlib import Path

from maxcode.bench.runner import run_bench
from maxcode.config import Config
from maxcode.schemas import RunResult


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


def test_bench_writes_results_and_logs(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    suite.mkdir()
    (suite / "task-001.json").write_text(
        json.dumps(
            {
                "id": "task-001",
                "repo_url": str(repo),
                "commit": "HEAD",
                "task": "do something",
                "score": "true",
            }
        ),
        encoding="utf-8",
    )

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
        (Path(repo) / "marker.txt").write_text("ran", encoding="utf-8")
        return RunResult(run_id="run1", passed=True, exit_code=0, cost_usd=0.25, log_path="")

    # provide a log file
    log_path = tmp_path / "run.jsonl"
    log_path.write_text("", encoding="utf-8")

    def fake_run_task2(task, cfg, options, repo=None, **kwargs):
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
        run_task_fn=fake_run_task2,
        clone_fn=lambda url, commit, dest: subprocess.run(
            ["git", "clone", "--quiet", url, str(dest)], check=True
        ),
    )
    assert summary.total == 1
    assert summary.passed == 1
    assert (out_dir / "results.csv").is_file()
    assert (out_dir / "task-001" / "run.jsonl").is_file()


def test_bench_verifier_off_passes_flag(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    init_repo(repo)
    suite = tmp_path / "suite"
    suite.mkdir()
    (suite / "task-001.json").write_text(
        json.dumps(
            {
                "id": "task-001",
                "repo_url": str(repo),
                "commit": "HEAD",
                "task": "do something",
                "score": "true",
            }
        ),
        encoding="utf-8",
    )
    seen = {}

    def fake_run_task(task, cfg, options, repo=None, **kwargs):
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
        clone_fn=lambda url, commit, dest: subprocess.run(
            ["git", "clone", "--quiet", url, str(dest)], check=True
        ),
    )
    assert seen["verifier"] is False
