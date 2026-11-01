# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Check the local maxcode setup and report actionable failures."""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import httpx

from maxcode.checkpoints import is_git_repo
from maxcode.checks import detect_checks
from maxcode.config import Config, load_config
from maxcode.engine.runner import _binary, _engine_version
from maxcode.errors import ConfigError, EngineError, ProviderError
from maxcode.providers.openai_compat import OpenAICompatProvider
from maxcode.schemas import ChatMessage


@dataclass
class DoctorResult:
    """One doctor check result."""

    name: str
    status: str
    detail: str
    fix: str = ""


def check_git() -> DoctorResult:
    """Check git installation and repository state."""
    git = shutil.which("git")
    if git is None:
        return DoctorResult(
            "git",
            "FAIL",
            "git is not installed.",
            "Install git and rerun maxcode doctor.",
        )
    root = Path.cwd()
    if not is_git_repo(root):
        return DoctorResult(
            "git",
            "FAIL",
            f"{root} is not a git repository.",
            "Run git init in this folder and rerun maxcode doctor.",
        )
    version = subprocess.run(
        [git, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (version.stdout or version.stderr).strip() or "git found"
    return DoctorResult("git", "PASS", f"{detail}; {root} is a git repository")


def check_engine() -> DoctorResult:
    """Check the engine binary and its version."""
    try:
        binary = _binary()
    except EngineError as exc:
        return DoctorResult("engine", "FAIL", f"{exc.what} {exc.why}", exc.next_step)
    version = _engine_version(binary)
    if version is None:
        return DoctorResult(
            "engine",
            "FAIL",
            f"Could not read the version of '{binary}'.",
            "Check that the engine binary runs with --version.",
        )
    shown = ".".join(str(part) for part in version)
    if version < (0, 165, 0):
        return DoctorResult(
            "engine",
            "FAIL",
            f"{binary} reports {shown}.",
            "Install Codex 0.165 or newer, or rebuild maxcode-engine from v0.165.0.",
        )
    return DoctorResult("engine", "PASS", f"{binary} ({shown})")


def check_config() -> tuple[DoctorResult, Config | None]:
    """Check the config file and the environment keys."""
    try:
        cfg = load_config(None, require_env=False)
    except ConfigError as exc:
        return DoctorResult("config", "FAIL", exc.what, exc.next_step), None
    missing: list[ConfigError] = []
    for role in (cfg.planner, cfg.worker):
        try:
            cfg.api_key_for(role.provider)
        except ConfigError as exc:
            missing.append(exc)
    if missing:
        details = list(dict.fromkeys(error.what for error in missing))
        return DoctorResult("config", "FAIL", "; ".join(details), missing[0].next_step), cfg
    return (
        DoctorResult(
            "config",
            "PASS",
            "config loaded; planner and worker keys are present",
        ),
        cfg,
    )


def _redact(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "[redacted]")


def check_planner(
    cfg: Config | None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> DoctorResult:
    """Check the planner's /chat/completions endpoint."""
    if cfg is None:
        return DoctorResult(
            "planner",
            "FAIL",
            "config did not load.",
            "Fix the config first, then rerun maxcode doctor.",
        )
    try:
        key = cfg.api_key_for(cfg.planner.provider)
    except ConfigError as exc:
        return DoctorResult("planner", "FAIL", exc.what, exc.next_step)
    provider_config = cfg.provider[cfg.planner.provider]
    provider = OpenAICompatProvider(provider_config.base_url, key, transport=transport)
    messages: list[ChatMessage] = [{"role": "user", "content": "Reply with ok."}]
    try:
        provider.chat(messages, cfg.planner.model)
    except ProviderError as exc:
        return DoctorResult("planner", "FAIL", exc.what, exc.next_step)
    finally:
        provider.close()
    return DoctorResult(
        "planner",
        "PASS",
        f"{provider_config.base_url}/chat/completions answered",
    )


def check_worker(
    cfg: Config | None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> DoctorResult:
    """Check the worker's /responses endpoint."""
    if cfg is None:
        return DoctorResult(
            "worker",
            "FAIL",
            "config did not load.",
            "Fix the config first, then rerun maxcode doctor.",
        )
    try:
        key = cfg.api_key_for(cfg.worker.provider)
    except ConfigError as exc:
        return DoctorResult("worker", "FAIL", exc.what, exc.next_step)
    provider_config = cfg.provider[cfg.worker.provider]
    url = f"{provider_config.base_url.rstrip('/')}/responses"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": cfg.worker.model,
        "input": "Reply with ok.",
        "max_output_tokens": 16,
    }
    try:
        with httpx.Client(timeout=30.0, transport=transport) as client:
            response = client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        return DoctorResult(
            "worker",
            "FAIL",
            f"the worker request failed: {exc}",
            "Check the worker base URL and network, then retry.",
        )
    if response.status_code != 200:
        body = " ".join(_redact(response.text, key).split())[-200:]
        return DoctorResult(
            "worker",
            "FAIL",
            f"{url} returned HTTP {response.status_code}: {body}",
            "Check the worker base URL and model, then retry.",
        )
    try:
        response.json()
    except ValueError:
        return DoctorResult(
            "worker",
            "FAIL",
            f"{url} returned invalid JSON.",
            "Use an endpoint that implements the Responses API.",
        )
    return DoctorResult("worker", "PASS", f"{url} answered")


def check_checks() -> DoctorResult:
    """Check whether the repository has detectable checks."""
    detected = detect_checks(Path.cwd())
    if not detected:
        return DoctorResult(
            "checks",
            "WARN",
            "no test, build, or lint checks detected",
            "Add tests or configure [checks] in maxcode.toml.",
        )
    detail = ", ".join(f"{name}={command}" for name, command in detected.items())
    return DoctorResult("checks", "PASS", detail)


def run_doctor(*, transport: httpx.BaseTransport | None = None) -> list[DoctorResult]:
    """Run every doctor check in order."""
    git_result = check_git()
    engine_result = check_engine()
    config_result, cfg = check_config()
    return [
        git_result,
        engine_result,
        config_result,
        check_planner(cfg, transport=transport),
        check_worker(cfg, transport=transport),
        check_checks(),
    ]
