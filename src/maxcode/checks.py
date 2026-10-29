# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Detect repository checks and run them as child processes."""

import contextlib
import json
import os
import signal
import subprocess
import time
from collections.abc import Iterable, Iterator
from pathlib import Path

from maxcode.config import Config
from maxcode.errors import CheckError
from maxcode.schemas import CheckResult

NAMED_CHECKS = ("test", "build", "lint")
OUTPUT_LIMIT = 4000
SKIP_DIRS = frozenset({".git", ".venv", "node_modules", ".maxcode"})
PYTHON_MARKERS = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini")


def _walk(root: Path, pattern: str) -> Iterator[Path]:
    for path in root.rglob(pattern):
        if path.is_file() and not SKIP_DIRS.intersection(path.parts):
            yield path


def _has_python_tests(repo: Path) -> bool:
    if (repo / "tests").is_dir() and any(_walk(repo / "tests", "*.py")):
        return True
    return any(_walk(repo, "test_*.py")) or any(_walk(repo, "*_test.py"))


def _has_ruff(repo: Path) -> bool:
    if (repo / "ruff.toml").is_file() or (repo / ".ruff.toml").is_file():
        return True
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        return "[tool.ruff" in pyproject.read_text(encoding="utf-8", errors="replace")
    return False


def _python_checks(repo: Path) -> dict[str, str]:
    if not any((repo / marker).is_file() for marker in PYTHON_MARKERS):
        return {}
    checks: dict[str, str] = {}
    if _has_python_tests(repo):
        checks["test"] = "python -m pytest -q"
    if _has_ruff(repo):
        checks["lint"] = "ruff check ."
    if (repo / "src").is_dir() and any(_walk(repo / "src", "*.py")):
        checks["build"] = "python -m compileall -q src"
    return checks


def _node_checks(repo: Path) -> dict[str, str]:
    package_path = repo / "package.json"
    if not package_path.is_file():
        return {}
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = package.get("scripts") if isinstance(package, dict) else None
    if not isinstance(scripts, dict):
        return {}
    checks: dict[str, str] = {}
    if "test" in scripts:
        checks["test"] = "npm test"
    if "build" in scripts:
        checks["build"] = "npm run build"
    if "lint" in scripts:
        checks["lint"] = "npm run lint"
    return checks


def _rust_checks(repo: Path) -> dict[str, str]:
    if not (repo / "Cargo.toml").is_file():
        return {}
    return {
        "test": "cargo test",
        "build": "cargo build",
        "lint": "cargo clippy --all-targets",
    }


def _go_checks(repo: Path) -> dict[str, str]:
    if not (repo / "go.mod").is_file():
        return {}
    return {
        "test": "go test ./...",
        "build": "go build ./...",
        "lint": "go vet ./...",
    }


def detect_checks(repo: str | Path) -> dict[str, str]:
    """Detect test, build, and lint commands in repository order."""
    root = Path(repo)
    for detector in (_python_checks, _node_checks, _rust_checks, _go_checks):
        checks = detector(root)
        if checks:
            return checks
    return {}


def available_check_names(cfg: Config, detected: dict[str, str]) -> list[str]:
    """Return named checks that are either configured or detected."""
    return [
        name
        for name in NAMED_CHECKS
        if getattr(cfg.checks, name) or name in detected
    ]


def resolve_checks(
    requested: Iterable[str], cfg: Config, detected: dict[str, str]
) -> list[tuple[str, str]]:
    """Turn plan check names into commands, skipping unavailable ones."""
    resolved: list[tuple[str, str]] = []
    for item in requested:
        if item.startswith("cmd:"):
            name, command = item, item[4:].strip()
        else:
            name = item
            command = getattr(cfg.checks, item, "") or detected.get(item, "")
        pair = (name, command)
        if command and pair not in resolved:
            resolved.append(pair)
    return resolved


def run_check(name: str, cmd: str, repo: str | Path, timeout_s: float) -> CheckResult:
    """Run one shell command and keep the last 4000 characters of output."""
    if not cmd.strip():
        raise CheckError(
            f"Check '{name}' has no command.",
            "The configured or planned command is empty.",
            "Set the command in maxcode.toml or remove the check from the plan.",
        )
    if timeout_s <= 0:
        raise CheckError(
            f"Check '{name}' has an invalid timeout.",
            f"The timeout is {timeout_s} seconds.",
            "Set a positive timeout in seconds.",
        )
    start = time.monotonic()
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        raise CheckError(
            f"Could not start check '{name}'.",
            str(exc),
            "Check the command and the repository path, then retry.",
        ) from exc
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout_s)
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
        exit_code = 124
    seconds = time.monotonic() - start
    text = output or ""
    if timed_out:
        text = f"Command timed out after {timeout_s} seconds.\n{text}"
    return CheckResult(
        name=name,
        command=cmd,
        passed=exit_code == 0,
        exit_code=exit_code,
        output_tail=text[-OUTPUT_LIMIT:],
        seconds=seconds,
    )
