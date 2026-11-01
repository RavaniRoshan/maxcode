# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for check detection and execution."""

import json
from pathlib import Path

from maxcode.checks import (
    available_check_commands,
    available_check_names,
    detect_checks,
    resolve_checks,
    run_check,
)
from maxcode.config import Config


def make_config(checks: dict[str, str] | None = None) -> Config:
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
            "checks": checks or {},
        }
    )


def test_python_repository_detection(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["hatchling"]\n\n[tool.ruff]\nline-length = 100\n',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_x(): pass\n", encoding="utf-8")
    checks = detect_checks(tmp_path)
    assert checks["test"] == "python -m pytest -q"
    assert checks["lint"] == "ruff check ."
    assert checks["build"] == "python -m compileall -q src"


def test_python_repository_without_tests(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    checks = detect_checks(tmp_path)
    assert "test" not in checks
    assert checks == {}


def test_node_repository_detection(tmp_path: Path) -> None:
    package = {
        "name": "fixture",
        "scripts": {"test": "jest", "build": "tsc", "lint": "eslint ."},
    }
    (tmp_path / "package.json").write_text(json.dumps(package), encoding="utf-8")
    checks = detect_checks(tmp_path)
    assert checks == {"test": "npm test", "build": "npm run build", "lint": "npm run lint"}


def test_node_repository_only_runs_defined_scripts(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "node test.js"}}), encoding="utf-8"
    )
    assert detect_checks(tmp_path) == {"test": "npm test"}


def test_rust_repository_detection(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")
    assert detect_checks(tmp_path) == {
        "test": "cargo test",
        "build": "cargo build",
        "lint": "cargo clippy --all-targets",
    }


def test_go_repository_detection(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/x\n", encoding="utf-8")
    assert detect_checks(tmp_path) == {
        "test": "go test ./...",
        "build": "go build ./...",
        "lint": "go vet ./...",
    }


def test_empty_repository_has_no_checks(tmp_path: Path) -> None:
    assert detect_checks(tmp_path) == {}


def test_python_wins_when_two_ecosystems_exist(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "jest"}}), encoding="utf-8"
    )
    assert detect_checks(tmp_path) == {"lint": "ruff check ."}


def test_run_check_passes(tmp_path: Path) -> None:
    result = run_check("test", "echo hello", tmp_path, timeout_s=5)
    assert result.passed is True
    assert result.exit_code == 0
    assert "hello" in result.output_tail
    assert result.seconds >= 0


def test_run_check_fails(tmp_path: Path) -> None:
    result = run_check(
        "test", "python -c \"import sys; print('bad'); sys.exit(3)\"", tmp_path, timeout_s=5
    )
    assert result.passed is False
    assert result.exit_code == 3
    assert "bad" in result.output_tail


def test_run_check_timeout_fails(tmp_path: Path) -> None:
    result = run_check("test", "python -c \"import time; time.sleep(5)\"", tmp_path, timeout_s=0.2)
    assert result.passed is False
    assert result.exit_code == 124
    assert "timed out" in result.output_tail.lower()


def test_run_check_keeps_last_4000_characters(tmp_path: Path) -> None:
    result = run_check("test", "python -c \"print('x' * 5000)\"", tmp_path, timeout_s=5)
    assert result.passed is True
    assert len(result.output_tail) <= 4000
    assert result.output_tail.strip().endswith("x")


def test_resolve_checks_uses_config_override(tmp_path: Path) -> None:
    cfg = make_config({"test": "custom-test"})
    assert resolve_checks(["test"], cfg, {"test": "detected"}) == [("test", "custom-test")]


def test_resolve_checks_skips_missing_commands() -> None:
    cfg = make_config()
    assert resolve_checks(["test", "build"], cfg, {}) == []


def test_resolve_checks_keeps_cmd_checks_and_deduplicates() -> None:
    cfg = make_config()
    resolved = resolve_checks(["cmd:echo hi", "cmd:echo hi"], cfg, {})
    assert resolved == [("cmd:echo hi", "echo hi")]


def test_available_check_names_include_overrides_and_detected() -> None:
    cfg = make_config({"build": "make"})
    assert available_check_names(cfg, {"test": "pytest"}) == ["test", "build"]


def test_available_check_commands_include_overrides_and_detected() -> None:
    cfg = make_config({"build": "make"})
    assert available_check_commands(cfg, {"test": "pytest"}) == ["pytest", "make"]
