# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the doctor command."""

import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from maxcode.cli import app
from maxcode.config import Config
from maxcode.doctor import (
    DoctorResult,
    check_checks,
    check_config,
    check_engine,
    check_git,
    check_planner,
    check_worker,
    run_doctor,
)

runner = CliRunner()

CONFIG_TEXT = """
[provider.main]
base_url = "https://api.example.com/v1"
api_key_env = "MAXCODE_TEST_KEY"

[planner]
provider = "main"
model = "planner-model"

[worker]
provider = "main"
model = "worker-model"
"""


def init_repo(repo: Path) -> None:
    repo.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def write_config(root: Path) -> Path:
    path = root / "maxcode.toml"
    path.write_text(CONFIG_TEXT, encoding="utf-8")
    return path


def make_config() -> Config:
    return Config.model_validate(
        {
            "provider": {
                "main": {
                    "base_url": "https://api.example.com/v1",
                    "api_key_env": "MAXCODE_TEST_KEY",
                }
            },
            "planner": {"provider": "main", "model": "planner-model"},
            "worker": {"provider": "main", "model": "worker-model"},
        }
    )


def chat_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        },
    )


def responses_response() -> httpx.Response:
    return httpx.Response(200, json={"id": "resp_1", "output": []})


def endpoint_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/chat/completions"):
        return chat_response()
    if request.url.path.endswith("/responses"):
        return responses_response()
    return httpx.Response(404)


def write_engine(path: Path, version: str) -> Path:
    path.write_text(f'#!/bin/sh\necho "codex-cli {version}"\n', encoding="utf-8")
    path.chmod(0o755)
    return path


def test_doctor_check_git_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_repo(tmp_path / "repo")
    monkeypatch.chdir(tmp_path / "repo")
    result = check_git()
    assert result.status == "PASS"
    assert "git repository" in result.detail


def test_doctor_check_git_fails_outside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = check_git()
    assert result.status == "FAIL"
    assert "not a git repository" in result.detail
    assert "git init" in result.fix


def test_doctor_check_git_fails_without_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("maxcode.doctor.shutil.which", lambda name: None)
    monkeypatch.chdir(tmp_path)
    result = check_git()
    assert result.status == "FAIL"
    assert "not installed" in result.detail


def test_doctor_check_engine_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = write_engine(tmp_path / "engine", "0.165.0")
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(engine))
    result = check_engine()
    assert result.status == "PASS"
    assert "0.165.0" in result.detail


def test_doctor_check_engine_fails_old_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = write_engine(tmp_path / "engine", "0.163.0")
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(engine))
    result = check_engine()
    assert result.status == "FAIL"
    assert "0.163.0" in result.detail
    assert "0.165" in result.fix


def test_doctor_check_engine_fails_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAXCODE_ENGINE_BIN", raising=False)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    result = check_engine()
    assert result.status == "FAIL"
    assert "No engine binary" in result.detail


def test_doctor_check_config_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    result, cfg = check_config()
    assert result.status == "FAIL"
    assert "No maxcode.toml" in result.detail
    assert cfg is None


def test_doctor_check_config_missing_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    write_config(tmp_path)
    monkeypatch.delenv("MAXCODE_TEST_KEY", raising=False)
    result, cfg = check_config()
    assert result.status == "FAIL"
    assert "MAXCODE_TEST_KEY" in result.detail
    assert cfg is not None


def test_doctor_check_config_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    write_config(tmp_path)
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    result, cfg = check_config()
    assert result.status == "PASS"
    assert cfg is not None


def test_doctor_planner_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    transport = httpx.MockTransport(endpoint_handler)
    result = check_planner(make_config(), transport=transport)
    assert result.status == "PASS"
    assert "/chat/completions" in result.detail


def test_doctor_planner_fails_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
    result = check_planner(make_config(), transport=transport)
    assert result.status == "FAIL"
    assert "500" in result.detail


def test_doctor_planner_redacts_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(401, text="invalid key sk-secret")
    )
    result = check_planner(make_config(), transport=transport)
    assert result.status == "FAIL"
    assert "sk-secret" not in result.detail


def test_doctor_planner_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAXCODE_TEST_KEY", raising=False)
    result = check_planner(make_config())
    assert result.status == "FAIL"
    assert "MAXCODE_TEST_KEY" in result.detail


def test_doctor_planner_without_config() -> None:
    result = check_planner(None)
    assert result.status == "FAIL"
    assert "config did not load" in result.detail


def test_doctor_worker_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers["authorization"]
        captured["body"] = request.read()
        return responses_response()

    result = check_worker(make_config(), transport=httpx.MockTransport(handler))
    assert result.status == "PASS"
    assert captured["path"] == "/v1/responses"
    assert captured["auth"] == "Bearer sk-secret"
    assert b'"input"' in captured["body"]


def test_doctor_worker_fails_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
    result = check_worker(make_config(), transport=transport)
    assert result.status == "FAIL"
    assert "500" in result.detail


def test_doctor_worker_fails_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text="not json")
    )
    result = check_worker(make_config(), transport=transport)
    assert result.status == "FAIL"
    assert "invalid JSON" in result.detail


def test_doctor_worker_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAXCODE_TEST_KEY", raising=False)
    result = check_worker(make_config())
    assert result.status == "FAIL"
    assert "MAXCODE_TEST_KEY" in result.detail


def test_doctor_worker_without_config() -> None:
    result = check_worker(None)
    assert result.status == "FAIL"
    assert "config did not load" in result.detail


def test_doctor_check_checks_warn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = check_checks()
    assert result.status == "WARN"
    assert "no test" in result.detail


def test_doctor_check_checks_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.0.0"\n', encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    result = check_checks()
    assert result.status == "PASS"
    assert "test" in result.detail


def test_run_doctor_all_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    write_config(repo)
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.0.0"\n', encoding="utf-8"
    )
    (repo / "tests").mkdir()
    (repo / "tests" / "test_x.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    engine = write_engine(tmp_path / "engine", "0.165.0")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(engine))
    monkeypatch.setenv("MAXCODE_TEST_KEY", "sk-secret")
    results = run_doctor(transport=httpx.MockTransport(endpoint_handler))
    assert [item.name for item in results] == [
        "git",
        "engine",
        "config",
        "planner",
        "worker",
        "checks",
    ]
    assert all(item.status == "PASS" for item in results)


def test_doctor_command_shows_fail_and_fix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "maxcode.cli.run_doctor",
        lambda: [
            DoctorResult("git", "PASS", "ok"),
            DoctorResult("config", "FAIL", "bad config", "create maxcode.toml"),
        ],
    )
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "PASS git: ok" in result.output
    assert "FAIL config: bad config" in result.output
    assert "fix: create maxcode.toml" in result.output


def test_doctor_command_warn_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "maxcode.cli.run_doctor",
        lambda: [
            DoctorResult("git", "PASS", "ok"),
            DoctorResult("checks", "WARN", "none found", "add tests"),
        ],
    )
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "WARN checks: none found" in result.output
