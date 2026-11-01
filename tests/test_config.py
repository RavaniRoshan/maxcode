# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest

from maxcode.config import Config, find_config, load_config
from maxcode.errors import ConfigError

VALID_CONFIG = """
[provider.main]
base_url = "https://api.example.com/v1"
api_key_env = "MAXCODE_TEST_KEY"

[planner]
provider = "main"
model = "planner-model"

[worker]
provider = "main"
model = "worker-model"

[limits]
max_retries_per_step = 2
max_cost_usd_per_task = 1.5
max_diff_lines = 100
max_steps = 5

[checks]
test = "pytest -q"

[protected]
paths = ["**/*.lock"]

[pricing."planner-model"]
input_per_mtok_usd = 0.1
output_per_mtok_usd = 0.2
"""


def write_config(tmp_path: Path, text: str = VALID_CONFIG) -> Path:
    path = tmp_path / "maxcode.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret-value")
    cfg = load_config(write_config(tmp_path))
    assert isinstance(cfg, Config)
    assert cfg.planner.model == "planner-model"
    assert cfg.worker.provider == "main"
    assert cfg.limits.max_retries_per_step == 2
    assert cfg.checks.test == "pytest -q"
    assert cfg.checks.build == ""
    assert cfg.pricing["planner-model"].input_per_mtok_usd == 0.1
    assert "**/*.lock" in cfg.protected.paths


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as excinfo:
        load_config(tmp_path / "absent.toml")
    message = str(excinfo.value)
    assert "absent.toml" in message
    assert "Next:" in message


def test_bad_key_names_the_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret-value")
    text = VALID_CONFIG.replace("max_steps = 5", "max_steps = 5\nnot_a_real_key = 1")
    with pytest.raises(ConfigError) as excinfo:
        load_config(write_config(tmp_path, text))
    assert "limits.not_a_real_key" in str(excinfo.value)


def test_missing_environment_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAXCODE_TEST_KEY", raising=False)
    with pytest.raises(ConfigError) as excinfo:
        load_config(write_config(tmp_path))
    message = str(excinfo.value)
    assert "MAXCODE_TEST_KEY" in message
    assert "export MAXCODE_TEST_KEY" in message


def test_unknown_role_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret-value")
    text = VALID_CONFIG.replace(
        '[planner]\nprovider = "main"', '[planner]\nprovider = "other"'
    )
    with pytest.raises(ConfigError) as excinfo:
        load_config(write_config(tmp_path, text))
    assert "other" in str(excinfo.value)


def test_default_config_path_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    local = write_config(tmp_path)
    assert find_config(None) == local
    local.unlink()
    user = tmp_path / "xdg" / "maxcode" / "maxcode.toml"
    user.parent.mkdir(parents=True)
    user.write_text(VALID_CONFIG, encoding="utf-8")
    assert find_config(None) == user


def test_no_config_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    with pytest.raises(ConfigError) as excinfo:
        find_config(None)
    assert "maxcode.toml" in str(excinfo.value)


def test_api_key_for_reports_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAXCODE_TEST_KEY", raising=False)
    cfg = Config.model_validate(
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
    with pytest.raises(ConfigError):
        cfg.api_key_for("main")


def test_worker_timeout_defaults_to_600(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret-value")
    cfg = load_config(write_config(tmp_path))
    assert cfg.limits.worker_timeout_s == 600.0


def test_worker_timeout_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAXCODE_TEST_KEY", "secret-value")
    text = VALID_CONFIG.replace("max_steps = 5", "max_steps = 5\nworker_timeout_s = 42.5")
    cfg = load_config(write_config(tmp_path, text))
    assert cfg.limits.worker_timeout_s == 42.5
