# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Load and validate the maxcode TOML configuration."""

import hashlib
import os
import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from maxcode.errors import ConfigError

DEFAULT_PROTECTED_PATHS = ["**/*.lock", ".github/**"]
DEFAULT_TEST_PATHS = ["tests/**", "**/test_*.py", "**/*.test.*"]
CONFIG_FILENAME = "maxcode.toml"


class StrictModel(BaseModel):
    """Base model that rejects unknown keys so typos are reported."""

    model_config = ConfigDict(extra="forbid")


class ProviderConfig(StrictModel):
    """One OpenAI-compatible endpoint."""

    base_url: str
    api_key_env: str = Field(min_length=1)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return value.rstrip("/")


class RoleConfig(StrictModel):
    """The provider and model for one role."""

    provider: str
    model: str = Field(min_length=1)


class Limits(StrictModel):
    """Run limits."""

    max_retries_per_step: int = Field(default=3, ge=1)
    max_cost_usd_per_task: float = Field(default=2.0, gt=0)
    max_diff_lines: int = Field(default=400, ge=1)
    max_steps: int = Field(default=12, ge=1)


class ChecksConfig(StrictModel):
    """Command overrides. An empty string means auto-detect."""

    test: str = ""
    build: str = ""
    lint: str = ""


class ProtectedConfig(StrictModel):
    """Glob patterns that the verifier treats as protected."""

    paths: list[str] = Field(default_factory=lambda: list(DEFAULT_PROTECTED_PATHS))
    test_paths: list[str] = Field(default_factory=lambda: list(DEFAULT_TEST_PATHS))


class Pricing(StrictModel):
    """Price per million tokens for one model."""

    input_per_mtok_usd: float = Field(ge=0)
    output_per_mtok_usd: float = Field(ge=0)


class Config(StrictModel):
    """The validated maxcode configuration."""

    provider: dict[str, ProviderConfig]
    planner: RoleConfig
    worker: RoleConfig
    limits: Limits = Field(default_factory=Limits)
    checks: ChecksConfig = Field(default_factory=ChecksConfig)
    protected: ProtectedConfig = Field(default_factory=ProtectedConfig)
    pricing: dict[str, Pricing] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_role_providers(self) -> Self:
        for role_name in ("planner", "worker"):
            role = getattr(self, role_name)
            if role.provider not in self.provider:
                raise ValueError(
                    f"{role_name} references unknown provider '{role.provider}'; "
                    f"known providers: {', '.join(sorted(self.provider))}"
                )
        return self

    def api_key_for(self, provider_id: str) -> str:
        """Read a provider key from the environment, never from a file."""
        provider = self.provider.get(provider_id)
        if provider is None:
            raise ConfigError(
                f"Provider '{provider_id}' is not configured.",
                "The selected role names a provider that has no [provider.<id>] table.",
                f"Add [provider.{provider_id}] to maxcode.toml or fix the role's provider name.",
            )
        value = os.environ.get(provider.api_key_env, "")
        if not value.strip():
            raise ConfigError(
                f"Environment variable {provider.api_key_env} is not set.",
                f"The provider '{provider_id}' needs an API key from that variable.",
                f"Export it in the shell that starts maxcode: export {provider.api_key_env}=...",
            )
        return value

    def config_hash(self) -> str:
        """Return a stable hash of the validated configuration."""
        payload = self.model_dump_json(exclude_none=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def user_config_path() -> Path:
    """Return the per-user config path."""
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "maxcode" / CONFIG_FILENAME


def find_config(path: str | Path | None = None) -> Path:
    """Find the config file: explicit path, then ./maxcode.toml, then user config."""
    if path is not None:
        candidate = Path(path).expanduser()
        if not candidate.is_file():
            raise ConfigError(
                f"Configuration file '{candidate}' does not exist.",
                "The path given to --config does not point to a readable file.",
                "Check the path, or omit --config to use ./maxcode.toml or the user config.",
            )
        return candidate.resolve()
    local = Path.cwd() / CONFIG_FILENAME
    if local.is_file():
        return local.resolve()
    user = user_config_path()
    if user.is_file():
        return user.resolve()
    raise ConfigError(
        f"No {CONFIG_FILENAME} file found.",
        f"Looked for {local} and {user}.",
        f"Create {CONFIG_FILENAME} in the repository root; see README.md for an example.",
    )


def _validation_message(exc: ValidationError) -> tuple[str, str, str]:
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first["loc"]) or "config"
    detail = first["msg"]
    return (
        f"Invalid configuration key '{location}': {detail}.",
        "The configuration file does not match the maxcode schema.",
        "Fix that key in maxcode.toml and run the command again.",
    )


def _check_environment(cfg: Config) -> None:
    for role in (cfg.planner, cfg.worker):
        cfg.api_key_for(role.provider)


def load_config(path: str | Path | None = None, *, require_env: bool = True) -> Config:
    """Load, validate, and optionally check the environment keys."""
    config_path = find_config(path)
    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(
            f"Could not read configuration file '{config_path}'.",
            str(exc),
            "Check file permissions and run the command again.",
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f"Configuration file '{config_path}' is not valid TOML.",
            str(exc),
            "Fix the TOML syntax and run the command again.",
        ) from exc
    try:
        cfg = Config.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(*_validation_message(exc)) from exc
    if require_env:
        _check_environment(cfg)
    return cfg
