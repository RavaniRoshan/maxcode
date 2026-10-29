# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Codex engine adapter."""

import os
import stat
from pathlib import Path

import pytest

from maxcode.config import ProviderConfig
from maxcode.engine.codex import run_step
from maxcode.errors import EngineError
from maxcode.schemas import EngineResult

FAKE_CODEX = Path(__file__).parent / "fixtures" / "fake_codex.py"


def make_provider() -> ProviderConfig:
    return ProviderConfig(base_url="https://api.example.com/v1", api_key_env="MAXCODE_TEST_KEY")


def test_engine_parses_fake_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_CODEX_BIN", str(FAKE_CODEX))
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_CODEX, os.stat(FAKE_CODEX).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "test-model", 10.0)
    assert isinstance(result, EngineResult)
    assert result.exit_code == 0
    assert result.input_tokens == 7
    assert result.output_tokens == 3
    assert "editing" in result.transcript
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "hello from fake codex"


def test_engine_reports_missing_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAXCODE_CODEX_BIN", raising=False)
    monkeypatch.setenv("PATH", "")
    with pytest.raises(EngineError):
        run_step("do it", tmp_path, make_provider(), "m", 10.0)


def test_engine_handles_nonzero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_CODEX_BIN", str(FAKE_CODEX))
    monkeypatch.setenv("FAKE_CODEX_MODE", "exit1")
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_CODEX, os.stat(FAKE_CODEX).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "m", 10.0)
    assert result.exit_code == 1
    assert result.failed is True
    assert "boom" in result.transcript


def test_engine_handles_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_CODEX_BIN", str(FAKE_CODEX))
    monkeypatch.setenv("FAKE_CODEX_MODE", "timeout")
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_CODEX, os.stat(FAKE_CODEX).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "m", 0.2)
    assert result.timed_out is True
    assert result.exit_code == 124


def test_engine_marks_missing_usage_as_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAXCODE_CODEX_BIN", str(FAKE_CODEX))
    monkeypatch.setenv("FAKE_CODEX_MODE", "no_usage")
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_CODEX, os.stat(FAKE_CODEX).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "m", 10.0)
    assert result.input_tokens is None
    assert result.output_tokens is None


@pytest.mark.slow
def test_engine_creates_hello_with_real_provider(tmp_path: Path) -> None:
    base_url = os.environ.get("MAXCODE_BASE_URL")
    api_key = os.environ.get("MAXCODE_API_KEY")
    if not base_url or not api_key:
        pytest.skip("MAXCODE_BASE_URL and MAXCODE_API_KEY are required")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("MAXCODE_TEST_KEY", api_key)
    provider = ProviderConfig(base_url=base_url, api_key_env="MAXCODE_TEST_KEY")
    codex_bin = os.environ.get("MAXCODE_CODEX_BIN") or "codex"
    monkeypatch.setenv("MAXCODE_CODEX_BIN", codex_bin)
    result = run_step(
        "Create hello.txt containing exactly 'hello' and nothing else. Only change hello.txt.",
        tmp_path,
        provider,
        os.environ.get("MAXCODE_MODEL", "qwen/qwen3-coder-next"),
        120.0,
    )
    assert result.exit_code == 0
    assert (tmp_path / "hello.txt").is_file()
    assert "hello" in (tmp_path / "hello.txt").read_text(encoding="utf-8")
    monkeypatch.undo()
