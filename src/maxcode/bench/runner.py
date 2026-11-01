# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Run the benchmark suite and write results.csv plus per-task logs."""

import contextlib
import csv
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from maxcode.config import Config
from maxcode.loop import run_task
from maxcode.runlog import new_run_id
from maxcode.schemas import RunOptions, StopReason

DEFAULT_SUITE = Path(__file__).parent / "tasks"


@dataclass
class BenchSummary:
    """Aggregate result of one benchmark run."""

    total: int = 0
    passed: int = 0
    cost_usd: float = 0.0
    unverified: int = 0
    invalid: int = 0
    errors: int = 0
    csv_path: str = ""
    out_dir: str = ""


@dataclass
class TaskResult:
    """One task's baseline, worker, and score outcome."""

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
    baseline_status: str = "error"
    baseline_exit_code: int = -1
    status: str = "error"
    excluded_reason: str = ""


@contextlib.contextmanager
def _repo_pythonpath(repo: Path) -> Iterator[None]:
    """Put a src-layout repository on PYTHONPATH for checks and scoring."""
    src = repo / "src"
    if not src.is_dir():
        yield
        return
    previous = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = str(src) if not previous else f"{src}{os.pathsep}{previous}"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous


def _load_tasks(suite: Path) -> list[dict[str, Any]]:
    paths = sorted({*suite.glob("*.json"), *suite.rglob("task.json")})
    tasks: list[dict[str, Any]] = []
    for path in paths:
        task = json.loads(path.read_text(encoding="utf-8"))
        task["_base_dir"] = str(path.parent)
        tasks.append(task)
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


def _materialize_repo(source: Path, dest: Path) -> None:
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")
    shutil.copytree(source, dest, ignore=ignore)
    commands = [
        ["git", "init", "-q", "-b", "main"],
        ["git", "config", "user.email", "bench@example.com"],
        ["git", "config", "user.name", "maxcode bench"],
        ["git", "add", "-A"],
        ["git", "commit", "-q", "-m", "bench baseline"],
    ]
    for command in commands:
        subprocess.run(
            command,
            cwd=dest,
            check=True,
            capture_output=True,
            text=True,
        )


def _prepare_repo(
    task: dict[str, Any],
    task_dir: Path,
    clone_fn: Callable[[str, str, Path], None],
) -> Path:
    repo = task_dir / "repo"
    repo_dir = task.get("repo_dir")
    if repo_dir:
        source = (Path(str(task["_base_dir"])) / str(repo_dir)).resolve()
        _materialize_repo(source, repo)
    else:
        clone_fn(str(task.get("repo_url", "")), str(task.get("commit", "")), repo)
    return repo


def _score_env(task: dict[str, Any]) -> dict[str, str] | None:
    hidden = task.get("hidden_tests")
    if not hidden:
        return None
    root = Path(str(task["_base_dir"]))
    env = os.environ.copy()
    env["MAXCODE_HIDDEN_TESTS"] = str((root / str(hidden)).resolve())
    return env


def _run_score(
    command: str,
    repo: Path,
    env: dict[str, str] | None = None,
) -> tuple[bool, int, str]:
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
            env=env,
        )
    except subprocess.TimeoutExpired:
        return False, 124, "timeout"
    tail = (result.stdout + result.stderr)[-2000:]
    return result.returncode == 0, result.returncode, tail


def _score_task(task: dict[str, Any], repo: Path) -> tuple[bool, int, str]:
    command = str(task.get("score") or task.get("score_command") or "")
    return _run_score(command, repo, _score_env(task))


def _baseline_check(
    task: dict[str, Any],
    repo: Path,
    task_dir: Path,
) -> tuple[str, int]:
    baseline_repo = task_dir / "baseline-repo"
    shutil.copytree(repo, baseline_repo, symlinks=True)
    with _repo_pythonpath(baseline_repo):
        passed, code, _ = _score_task(task, baseline_repo)
    return ("passed" if passed else "failed"), code


def _final_status(run_result: Any | None, run_error: bool, score_passed: bool) -> str:
    if run_error:
        return "error"
    if getattr(run_result, "stop_reason", None) == StopReason.ERROR:
        return "error"
    return "pass" if score_passed else "fail"


def _write_results(results: list[TaskResult], csv_path: Path) -> None:
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
                "baseline_status",
                "baseline_exit_code",
                "status",
                "excluded_reason",
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
                    item.baseline_status,
                    item.baseline_exit_code,
                    item.status,
                    item.excluded_reason,
                ]
            )


def _run_one_task(
    task: dict[str, Any],
    verifier: bool,
    task_dir: Path,
    cfg: Config,
    run_task_fn: Callable[..., Any],
    clone_fn: Callable[[str, str, Path], None],
) -> TaskResult:
    result = TaskResult(
        task_id=str(task.get("id", "")),
        repo_url=str(task.get("repo_url", "")),
        commit=str(task.get("commit", "")),
        verifier=verifier,
    )
    try:
        repo = _prepare_repo(task, task_dir, clone_fn)
    except Exception as exc:  # noqa: BLE001
        result.error = f"prepare failed: {exc}"
        return result

    try:
        baseline_status, baseline_code = _baseline_check(task, repo, task_dir)
    except Exception as exc:  # noqa: BLE001
        result.error = f"baseline failed: {exc}"
        return result
    result.baseline_status = baseline_status
    result.baseline_exit_code = baseline_code
    if baseline_status == "passed":
        result.status = "invalid"
        result.excluded_reason = "baseline passed"
        return result

    run_result: Any | None = None
    run_error = False
    with _repo_pythonpath(repo):
        try:
            run_result = run_task_fn(
                str(task.get("task", "")),
                cfg,
                RunOptions(yes=True, verifier=verifier),
                repo=repo,
            )
            result.run_passed = bool(run_result.passed)
            result.cost_usd = float(run_result.cost_usd)
            result.tokens_in = int(run_result.tokens_in)
            result.tokens_out = int(run_result.tokens_out)
            result.unverified = len(run_result.unverified_steps)
            result.log_path = str(run_result.log_path)
            if run_result.log_path and Path(run_result.log_path).is_file():
                shutil.copyfile(run_result.log_path, task_dir / "run.jsonl")
                result.log_path = str(task_dir / "run.jsonl")
        except Exception as exc:  # noqa: BLE001
            result.error = f"run failed: {exc}"
            run_error = True
        try:
            passed, code, _ = _score_task(task, repo)
        except Exception as exc:  # noqa: BLE001
            result.error = result.error or f"score failed: {exc}"
            run_error = True
            passed, code = False, 1
        result.score_passed = passed
        result.score_exit_code = code

    result.status = _final_status(run_result, run_error, passed)
    if result.status == "error" and not result.error:
        result.error = f"run stopped: {getattr(run_result, 'stop_reason', 'error')}"
    return result


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
        suite = DEFAULT_SUITE
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
        task_dir = out_dir / str(task.get("id", ""))
        task_dir.mkdir(parents=True, exist_ok=True)
        results.append(_run_one_task(task, verifier, task_dir, cfg, run_task_fn, clone_fn))

    csv_path = out_dir / "results.csv"
    _write_results(results, csv_path)

    valid = [item for item in results if item.status != "invalid"]
    summary = BenchSummary(
        total=len(valid),
        passed=sum(1 for item in valid if item.status == "pass"),
        cost_usd=sum(item.cost_usd for item in valid),
        unverified=sum(item.unverified for item in valid),
        invalid=len(results) - len(valid),
        errors=sum(1 for item in valid if item.status == "error"),
        csv_path=str(csv_path),
        out_dir=str(out_dir),
    )
    return summary
