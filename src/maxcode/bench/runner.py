# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Run the benchmark suite and write results.csv plus per-task logs."""

import csv
import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from maxcode.config import Config
from maxcode.loop import run_task
from maxcode.runlog import new_run_id
from maxcode.schemas import RunOptions


@dataclass
class BenchSummary:
    """Aggregate result of one benchmark run."""

    total: int = 0
    passed: int = 0
    cost_usd: float = 0.0
    unverified: int = 0
    csv_path: str = ""
    out_dir: str = ""


@dataclass
class TaskResult:
    task_id: str = ""
    repo_url: str = ""
    commit: str = ""
    verifier: bool = True
    run_passed: bool = False
    score_passed: bool = False
    score_exit_code: int = 1
    cost_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    unverified: int = 0
    log_path: str = ""
    error: str = ""


def _load_tasks(suite: Path) -> list[dict[str, Any]]:
    tasks = []
    for path in sorted(suite.glob("*.json")):
        tasks.append(json.loads(path.read_text(encoding="utf-8")))
    return tasks


def _default_clone(url: str, commit: str, dest: Path) -> None:
    subprocess.run(
        ["git", "clone", "--quiet", url, str(dest)],
        check=True,
        capture_output=True,
        text=True,
    )
    if commit:
        subprocess.run(
            ["git", "checkout", "--quiet", commit],
            cwd=dest,
            check=True,
            capture_output=True,
            text=True,
        )


def _run_score(command: str, repo: Path) -> tuple[bool, int, str]:
    if not command:
        return True, 0, ""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return False, 124, "timeout"
    tail = (result.stdout + result.stderr)[-2000:]
    return result.returncode == 0, result.returncode, tail


def run_bench(
    suite: Path | None = None,
    verifier: bool = True,
    root: Path | None = None,
    cfg: Config | None = None,
    out_dir: Path | None = None,
    run_task_fn: Callable[..., Any] | None = None,
    clone_fn: Callable[[str, str, Path], None] | None = None,
    limit: int | None = None,
) -> BenchSummary:
    """Run every task in the suite and write results.csv."""
    if root is None:
        root = Path.cwd()
    if cfg is None:
        from maxcode.config import load_config

        cfg = load_config(None)
    if suite is None:
        suite = Path(__file__).parent / "tasks"
    if run_task_fn is None:
        run_task_fn = run_task
    if clone_fn is None:
        clone_fn = _default_clone
    if out_dir is None:
        out_dir = root / ".maxcode" / "bench" / new_run_id()
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = _load_tasks(suite)
    if limit is not None:
        tasks = tasks[:limit]

    results: list[TaskResult] = []
    for task in tasks:
        task_result = TaskResult(
            task_id=task.get("id", ""),
            repo_url=task.get("repo_url", ""),
            commit=task.get("commit", ""),
            verifier=verifier,
        )
        task_dir = out_dir / task_result.task_id
        repo = task_dir / "repo"
        task_dir.mkdir(parents=True, exist_ok=True)
        try:
            clone_fn(task_result.repo_url, task_result.commit, repo)
        except Exception as exc:  # noqa: BLE001
            task_result.error = f"clone failed: {exc}"
            results.append(task_result)
            continue
        try:
            run_result = run_task_fn(
                task.get("task", ""),
                cfg,
                RunOptions(yes=True, verifier=verifier),
                repo=repo,
            )
            task_result.run_passed = bool(run_result.passed)
            task_result.cost_usd = float(run_result.cost_usd)
            task_result.tokens_in = int(run_result.tokens_in)
            task_result.tokens_out = int(run_result.tokens_out)
            task_result.unverified = len(run_result.unverified_steps)
            task_result.log_path = str(run_result.log_path)
            if run_result.log_path and Path(run_result.log_path).is_file():
                shutil.copyfile(
                    run_result.log_path, task_dir / "run.jsonl"
                )
                task_result.log_path = str(task_dir / "run.jsonl")
        except Exception as exc:  # noqa: BLE001
            task_result.error = f"run failed: {exc}"
        score_command = task.get("score") or task.get("score_command") or ""
        passed, code, _ = _run_score(score_command, repo)
        task_result.score_passed = passed
        task_result.score_exit_code = code
        results.append(task_result)

    csv_path = out_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "task",
                "repo_url",
                "commit",
                "verifier",
                "run_passed",
                "score_passed",
                "score_exit_code",
                "cost_usd",
                "tokens_in",
                "tokens_out",
                "unverified",
                "log",
                "error",
            ]
        )
        for item in results:
            writer.writerow(
                [
                    item.task_id,
                    item.repo_url,
                    item.commit,
                    "on" if item.verifier else "off",
                    item.run_passed,
                    item.score_passed,
                    item.score_exit_code,
                    f"{item.cost_usd:.6f}",
                    item.tokens_in,
                    item.tokens_out,
                    item.unverified,
                    item.log_path,
                    item.error,
                ]
            )

    summary = BenchSummary(
        total=len(results),
        passed=sum(1 for item in results if item.score_passed),
        cost_usd=sum(item.cost_usd for item in results),
        unverified=sum(item.unverified for item in results),
        csv_path=str(csv_path),
        out_dir=str(out_dir),
    )
    return summary
