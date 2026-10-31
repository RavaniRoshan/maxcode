# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the maxcode engine adapter."""

import os
import stat
from pathlib import Path

import pytest

from maxcode.config import ProviderConfig
from maxcode.engine.runner import _binary, _build_command, run_step
from maxcode.errors import EngineError
from maxcode.schemas import EngineResult

FAKE_ENGINE = Path(__file__).parent / "fixtures" / "fake_engine.py"


def make_provider() -> ProviderConfig:
    return ProviderConfig(base_url="https://api.example.com/v1", api_key_env="MAXCODE_TEST_KEY")


def write_executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_engine_binary_prefers_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(FAKE_ENGINE))
    monkeypatch.setenv("PATH", str(tmp_path))
    assert _binary() == str(FAKE_ENGINE)


def test_engine_binary_finds_maxcode_engine_on_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = write_executable(tmp_path / "maxcode-engine", "#!/bin/sh\nexit 0\n")
    monkeypatch.delenv("MAXCODE_ENGINE_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert _binary() == str(binary)


def test_engine_binary_falls_back_to_codex_0165(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = write_executable(
        tmp_path / "codex",
        '#!/bin/sh\n[ "$1" = "--version" ] && echo "codex-cli 0.165.0"\nexit 0\n',
    )
    monkeypatch.delenv("MAXCODE_ENGINE_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert _binary() == str(binary)


def test_engine_binary_rejects_old_codex(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_executable(
        tmp_path / "codex",
        '#!/bin/sh\n[ "$1" = "--version" ] && echo "codex-cli 0.163.0"\nexit 0\n',
    )
    monkeypatch.delenv("MAXCODE_ENGINE_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(EngineError, match="too old"):
        _binary()


def test_engine_command_uses_local_compat_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_REASONING_EFFORT", "none")
    monkeypatch.setenv("MAXCODE_MODEL_CONTEXT_WINDOW", "16384")
    command = _build_command("engine", Path("/tmp/repo"), make_provider(), "m", "prompt")
    assert 'model_reasoning_effort="none"' in command
    assert 'web_search="disabled"' in command
    assert "agents.enabled=false" in command
    assert "model_context_window=16384" in command
    assert command[-1] == "prompt"


def test_engine_command_rejects_bad_context_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_MODEL_CONTEXT_WINDOW", "wide")
    with pytest.raises(EngineError, match="not an integer"):
        _build_command("engine", Path("/tmp/repo"), make_provider(), "m", "prompt")


def test_engine_parses_fake_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(FAKE_ENGINE))
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_ENGINE, os.stat(FAKE_ENGINE).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "test-model", 10.0)
    assert isinstance(result, EngineResult)
    assert result.exit_code == 0
    assert result.input_tokens == 7
    assert result.output_tokens == 3
    assert "editing" in result.transcript
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "hello from fake engine"


def test_engine_creates_missing_maxcode_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(FAKE_ENGINE))
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    monkeypatch.delenv("MAXCODE_HOME", raising=False)
    os.chmod(FAKE_ENGINE, os.stat(FAKE_ENGINE).st_mode | stat.S_IXUSR)
    run_step("do it", tmp_path, make_provider(), "test-model", 10.0)
    assert (tmp_path / ".maxcode" / "engine-home").is_dir()


def test_engine_reports_missing_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAXCODE_ENGINE_BIN", raising=False)
    monkeypatch.setenv("PATH", "")
    with pytest.raises(EngineError):
        run_step("do it", tmp_path, make_provider(), "m", 10.0)


def test_engine_handles_nonzero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(FAKE_ENGINE))
    monkeypatch.setenv("FAKE_ENGINE_MODE", "exit1")
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_ENGINE, os.stat(FAKE_ENGINE).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "m", 10.0)
    assert result.exit_code == 1
    assert result.failed is True
    assert "boom" in result.transcript


def test_engine_handles_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(FAKE_ENGINE))
    monkeypatch.setenv("FAKE_ENGINE_MODE", "timeout")
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_ENGINE, os.stat(FAKE_ENGINE).st_mode | stat.S_IXUSR)
    result = run_step("do it", tmp_path, make_provider(), "m", 0.2)
    assert result.timed_out is True
    assert result.exit_code == 124


def test_engine_marks_missing_usage_as_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", str(FAKE_ENGINE))
    monkeypatch.setenv("FAKE_ENGINE_MODE", "no_usage")
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret")
    os.chmod(FAKE_ENGINE, os.stat(FAKE_ENGINE).st_mode | stat.S_IXUSR)
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
    engine_bin = os.environ.get("MAXCODE_ENGINE_BIN") or "maxcode-engine"
    monkeypatch.setenv("MAXCODE_ENGINE_BIN", engine_bin)
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
