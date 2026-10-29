# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Run one step through the Codex CLI and parse its JSON event stream."""

import contextlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from maxcode.config import ProviderConfig
from maxcode.errors import EngineError
from maxcode.schemas import EngineResult


def _binary() -> str:
    override = os.environ.get("MAXCODE_CODEX_BIN")
    if override:
        return override
    found = shutil.which("codex")
    if found:
        return found
    raise EngineError(
        "The Codex engine binary was not found.",
        "maxcode looks for 'codex' on PATH or in MAXCODE_CODEX_BIN.",
        "Install Codex, or set MAXCODE_CODEX_BIN to the binary path.",
    )


def _build_command(
    binary: str, repo: Path, provider: ProviderConfig, model: str, prompt: str
) -> list[str]:
    import json as _json

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
        f"model_providers.maxcode.base_url={_json.dumps(provider.base_url)}",
        "-c",
        f"model_providers.maxcode.env_key={_json.dumps(provider.api_key_env)}",
        "-c",
        'model_providers.maxcode.wire_api="responses"',
        "-c",
        'model_reasoning_effort="minimal"',
        prompt,
    ]
    return command


def run_step(
    prompt: str,
    repo: str | Path,
    provider: ProviderConfig,
    model: str,
    timeout_s: float,
) -> EngineResult:
    """Run Codex in non-interactive mode and return its exit code and output."""
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
            "Codex needs an existing working directory.",
            "Check the repository path and run the command again.",
        )
    binary = _binary()
    command = _build_command(binary, root, provider, model, prompt)
    env = os.environ.copy()
    env.setdefault("CODEX_HOME", str(root / ".maxcode" / "codex-home"))
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
            "Could not start the Codex engine.",
            str(exc),
            "Check MAXCODE_CODEX_BIN and file permissions, then retry.",
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
