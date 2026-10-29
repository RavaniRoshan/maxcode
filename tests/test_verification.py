# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for step verification: protected paths and diff size."""

import subprocess
from pathlib import Path

from maxcode.checkpoints import create
from maxcode.checks import verify_step
from maxcode.config import Config
from maxcode.schemas import PlanStep


def init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def make_config(max_diff_lines: int = 400) -> Config:
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
            "limits": {"max_diff_lines": max_diff_lines},
            "checks": {"test": "true"},
        }
    )


def test_protected_path_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / ".github").mkdir()
    (repo / ".github" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    subprocess.run(["git", "add", ".github/ci.yml"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "ci"], cwd=repo, check=True)
    ref = create("run", 1, repo)
    (repo / ".github" / "ci.yml").write_text("name: changed\n", encoding="utf-8")
    step = PlanStep(id=1, goal="x", files=[], checks=["test"], edits_tests=False)
    result = verify_step(step, make_config(), repo, ref, {}, 5.0)
    assert result.passed is False
    assert ".github/ci.yml" in result.changed_files
    assert "protected" in result.failure_output


def test_test_path_allowed_with_edits_tests(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    ref = create("run", 1, repo)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    step = PlanStep(id=1, goal="x", files=[], checks=["test"], edits_tests=True)
    result = verify_step(step, make_config(), repo, ref, {}, 5.0)
    assert result.passed is True
    assert result.unverified is False


def test_test_path_rejected_without_edits_tests(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    ref = create("run", 1, repo)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
    step = PlanStep(id=1, goal="x", files=[], checks=["test"], edits_tests=False)
    result = verify_step(step, make_config(), repo, ref, {}, 5.0)
    assert result.passed is False
    assert "protected" in result.failure_output


def test_diff_over_limit_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    ref = create("run", 1, repo)
    (repo / "README.md").write_text("# demo\n" + "line\n" * 5, encoding="utf-8")
    step = PlanStep(id=1, goal="x", files=[], checks=["test"], edits_tests=False)
    result = verify_step(step, make_config(max_diff_lines=1), repo, ref, {}, 5.0)
    assert result.passed is False
    assert "diff" in result.failure_output
    assert result.diff_lines > 1


def test_zero_checks_is_unverified(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    ref = create("run", 1, repo)
    step = PlanStep(id=1, goal="x", files=[], checks=[], edits_tests=False)
    result = verify_step(step, make_config(), repo, ref, {}, 5.0)
    assert result.passed is False
    assert result.unverified is True


def test_all_checks_pass(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    ref = create("run", 1, repo)
    step = PlanStep(id=1, goal="x", files=[], checks=["test"], edits_tests=False)
    result = verify_step(step, make_config(), repo, ref, {}, 5.0)
    assert result.passed is True
    assert result.results[0].passed is True
