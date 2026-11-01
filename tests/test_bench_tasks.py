# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Baseline checks for the synthetic benchmark tasks."""

import shutil
import subprocess
from pathlib import Path

from maxcode.bench.runner import (
    DEFAULT_SUITE,
    _load_tasks,
    _materialize_repo,
    _run_score,
    _score_env,
)

TASKS = DEFAULT_SUITE / "synthetic"


def load_synthetic() -> list[dict]:
    return _load_tasks(TASKS)


def materialize(task: dict, dest: Path) -> Path:
    source = (Path(task["_base_dir"]) / str(task["repo_dir"])).resolve()
    repo = dest / "repo"
    _materialize_repo(source, repo)
    return repo


def test_default_suite_has_eight_synthetic_tasks() -> None:
    tasks = load_synthetic()
    assert len(tasks) == 8
    assert {task["id"] for task in tasks} == {f"task-{index}" for index in range(101, 109)}


def test_synthetic_tasks_fail_at_baseline(tmp_path: Path) -> None:
    for task in load_synthetic():
        task_dir = tmp_path / task["id"]
        task_dir.mkdir()
        repo = materialize(task, task_dir)

        visible = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        visible_output = visible.stdout + visible.stderr
        print(f"=== {task['id']} visible (exit {visible.returncode}) ===")
        print(visible_output)
        assert visible.returncode != 0, f"{task['id']} visible tests passed at baseline"
        assert "failed" in visible_output, visible_output

        baseline_repo = task_dir / "baseline-repo"
        shutil.copytree(repo, baseline_repo, symlinks=True)
        passed, code, output = _run_score(
            str(task["score"]),
            baseline_repo,
            _score_env(task),
        )
        print(f"=== {task['id']} hidden score (exit {code}) ===")
        print(output)
        assert not passed, f"{task['id']} score passed at baseline"
        assert "failed" in output, output
