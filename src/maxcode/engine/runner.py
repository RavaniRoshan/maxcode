# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Run one step through the maxcode engine and parse its JSON event stream."""

import contextlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from maxcode.config import ProviderConfig
from maxcode.errors import EngineError
from maxcode.schemas import EngineResult

MIN_CODEX_VERSION = (0, 165)


def _engine_version(binary: str) -> tuple[int, int, int] | None:
    """Read a three-part version from '<binary> --version'."""
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout + result.stderr)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _binary() -> str:
    override = os.environ.get("MAXCODE_ENGINE_BIN")
    if override:
        return override
    found = shutil.which("maxcode-engine")
    if found:
        return found
    stock = shutil.which("codex")
    if stock:
        version = _engine_version(stock)
        if version is not None and version >= MIN_CODEX_VERSION:
            return stock
        shown = ".".join(str(part) for part in version) if version else "unknown"
        raise EngineError(
            "The Codex CLI on PATH is too old.",
            f"Found '{stock}' reporting version {shown}; maxcode needs 0.165 or newer.",
            "Install Codex 0.165 or newer, or set MAXCODE_ENGINE_BIN to a compatible binary.",
        )
    raise EngineError(
        "No engine binary was found.",
        "maxcode looks for MAXCODE_ENGINE_BIN, 'maxcode-engine' on PATH, then 'codex' 0.165+.",
        "Build maxcode-engine, install Codex 0.165+, or set MAXCODE_ENGINE_BIN.",
    )


def _context_override(value: str) -> str | None:
    """Turn MAXCODE_MODEL_CONTEXT_WINDOW into a Codex override."""
    if not value.strip():
        return None
    try:
        window = int(value)
    except ValueError as exc:
        raise EngineError(
            "MAXCODE_MODEL_CONTEXT_WINDOW is not an integer.",
            f"The value {value!r} cannot be parsed as a whole number.",
            "Set it to a positive integer, or unset it.",
        ) from exc
    if window <= 0:
        raise EngineError(
            "MAXCODE_MODEL_CONTEXT_WINDOW must be positive.",
            f"The value {window} is not a positive number of tokens.",
            "Set it to a positive integer, or unset it.",
        )
    return f"model_context_window={window}"


def _build_command(
    binary: str, repo: Path, provider: ProviderConfig, model: str, prompt: str
) -> list[str]:
    reasoning = os.environ.get("MAXCODE_REASONING_EFFORT", "low")
    command = [
        binary,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "-C",
        str(repo),
        "-s",
        "workspace-write",
        "-m",
        model,
        "-c",
        "model_provider=maxcode",
        "-c",
        'model_providers.maxcode.name="maxcode"',
        "-c",
        f"model_providers.maxcode.base_url={json.dumps(provider.base_url)}",
        "-c",
        f"model_providers.maxcode.env_key={json.dumps(provider.api_key_env)}",
        "-c",
        'model_providers.maxcode.wire_api="responses"',
        "-c",
        f"model_reasoning_effort={json.dumps(reasoning)}",
        "-c",
        'web_search="disabled"',
        "-c",
        "agents.enabled=false",
    ]
    context = _context_override(os.environ.get("MAXCODE_MODEL_CONTEXT_WINDOW", ""))
    if context is not None:
        command.extend(["-c", context])
    command.append(prompt)
    return command


def run_step(
    prompt: str,
    repo: str | Path,
    provider: ProviderConfig,
    model: str,
    timeout_s: float,
) -> EngineResult:
    """Run maxcode in non-interactive mode and return its exit code and output."""
    root = Path(repo).resolve()
    if timeout_s <= 0:
        raise EngineError(
            "The engine timeout must be positive.",
            f"The timeout is {timeout_s} seconds.",
            "Set a positive timeout in seconds.",
        )
    if not root.is_dir():
        raise EngineError(
            f"Repository '{root}' does not exist.",
            "maxcode needs an existing working directory.",
            "Check the repository path and run the command again.",
        )
    binary = _binary()
    command = _build_command(binary, root, provider, model, prompt)
    env = os.environ.copy()
    home = Path(env.setdefault("MAXCODE_HOME", str(root / ".maxcode" / "engine-home")))
    with contextlib.suppress(OSError):
        home.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    timed_out = False
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=True,
        )
    except OSError as exc:
        raise EngineError(
            "Could not start the maxcode engine.",
            str(exc),
            "Check MAXCODE_ENGINE_BIN and file permissions, then retry.",
        ) from exc
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, 9)
        stdout_raw = exc.stdout
        stderr_raw = exc.stderr
        stdout = stdout_raw if isinstance(stdout_raw, str) else (stdout_raw or b"").decode(
            "utf-8", "replace"
        )
        stderr = stderr_raw if isinstance(stderr_raw, str) else (stderr_raw or b"").decode(
            "utf-8", "replace"
        )
        process.communicate()
    seconds = time.monotonic() - start
    exit_code = 124 if timed_out else process.returncode
    events = _parse_events(stdout)
    transcript = _build_transcript(events, stdout, stderr, exit_code)
    input_tokens, output_tokens = _usage(events)
    return EngineResult(
        exit_code=exit_code,
        transcript=transcript,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        seconds=seconds,
        timed_out=timed_out,
    )


def _parse_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def _build_transcript(
    events: list[dict[str, Any]], stdout: str, stderr: str, exit_code: int
) -> str:
    parts: list[str] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind == "agent_message" and item.get("text"):
            parts.append(str(item["text"]))
        elif kind == "command_execution":
            output = item.get("aggregated_output") or item.get("output")
            if output:
                parts.append(str(output))
    if not parts and stdout.strip():
        parts.append(stdout.strip())
    if exit_code != 0 and stderr.strip():
        parts.append(stderr.strip()[-1000:])
    return "\n".join(parts)


def _usage(events: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    found = False
    input_tokens = 0
    output_tokens = 0
    for event in events:
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue
        if "input_tokens" not in usage and "output_tokens" not in usage:
            continue
        found = True
        input_tokens += int(usage.get("input_tokens") or 0)
        output_tokens += int(usage.get("output_tokens") or 0)
    if not found:
        return None, None
    return input_tokens, output_tokens
