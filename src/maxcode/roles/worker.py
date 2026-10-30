# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""The worker role: build a prompt and run one step through the engine."""

from collections.abc import Callable, Sequence
from pathlib import Path

from maxcode.config import Config, ProviderConfig
from maxcode.cost import CostMeter
from maxcode.engine.runner import run_step
from maxcode.schemas import EngineResult, PlanStep

FAILURE_LIMIT = 4000


def _protected_list(cfg: Config, protected_paths: Sequence[str] | None) -> list[str]:
    if protected_paths is not None:
        return list(protected_paths)
    paths = list(cfg.protected.paths)
    paths.extend(cfg.protected.test_paths)
    return list(dict.fromkeys(paths))


def build_worker_prompt(
    step: PlanStep,
    task: str,
    failure: str | None,
    protected_paths: Sequence[str],
) -> str:
    """Build the worker prompt from section 24 of the PRD."""
    if failure:
        failure_block = (
            "The last attempt failed these checks. Fix the cause.\n"
            + failure[-FAILURE_LIMIT:]
        )
    else:
        failure_block = ""
    files = ", ".join(step.files) if step.files else "any"
    paths = ", ".join(protected_paths) if protected_paths else "none"
    return (
        "You are the worker for a coding tool.\n"
        "Complete this one step. Do not work on other steps.\n"
        f"Step goal: {step.goal}\n"
        f"Files to focus on: {files}\n"
        f"Task context: {task}\n"
        "Rules:\n"
        "1. Change only what the step needs.\n"
        f"2. Do not edit these paths: {paths}.\n"
        "3. Do not disable, skip, or delete any existing test.\n"
        "4. Do not claim the step is done. A separate program checks your work.\n"
        "5. Stop when you finish the edits.\n"
        f"{failure_block}"
    )


def do_step(
    step: PlanStep,
    failure: str | None,
    cfg: Config,
    *,
    task: str = "",
    repo: str | Path = ".",
    engine: Callable[[str, Path, ProviderConfig, str, float], EngineResult] | None = None,
    meter: CostMeter | None = None,
    timeout_s: float = 300.0,
    protected_paths: Sequence[str] | None = None,
) -> EngineResult:
    """Build the prompt and run one step through the engine."""
    if engine is None:
        engine = run_step
    paths = _protected_list(cfg, protected_paths)
    prompt = build_worker_prompt(step, task, failure, paths)
    provider = cfg.provider[cfg.worker.provider]
    provider_config = ProviderConfig(
        base_url=provider.base_url,
        api_key_env=provider.api_key_env,
    )
    result = engine(
        prompt,
        Path(repo),
        provider_config,
        cfg.worker.model,
        timeout_s,
    )
    if meter is not None:
        meter.add(cfg.worker.model, result.input_tokens, result.output_tokens)
    return result
