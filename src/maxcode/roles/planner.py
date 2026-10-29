# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""The planner role: turn one task into a validated list of steps."""

import json
from collections.abc import Callable, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from maxcode.config import Config
from maxcode.errors import PlanError
from maxcode.providers.base import Provider
from maxcode.providers.openai_compat import OpenAICompatProvider
from maxcode.schemas import ChatMessage, ChatResult, Plan

UsageSink = Callable[[str, int, int], None]
PROMPT_PATH = Path(__file__).parent / "prompts" / "planner.md"
NAMED_CHECKS = ("test", "build", "lint")


@lru_cache(maxsize=1)
def _prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_plan_prompt(
    task: str,
    repo_summary: str,
    max_steps: int,
    available_checks: Sequence[str],
    schema: dict[str, Any],
) -> str:
    """Fill the planner prompt from section 24 of the PRD."""
    checks = ", ".join(available_checks)
    return _prompt_template().format(
        max_steps=max_steps,
        available_checks=checks,
        schema=json.dumps(schema, indent=2),
        task=task,
        repo_summary=repo_summary,
    )


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object found in the planner output")
    return cleaned[start : end + 1]


def _parse_plan(text: str) -> Plan:
    try:
        return Plan.model_validate(json.loads(_strip_fences(text)))
    except (json.JSONDecodeError, ValidationError) as exc:
        detail = str(exc).strip().splitlines()[0][:500]
        raise ValueError(f"invalid plan JSON: {detail}") from exc


class Planner:
    """Build a plan by calling the configured planner model."""

    def __init__(
        self,
        provider: Provider,
        cfg: Config,
        usage_sink: UsageSink | None = None,
    ) -> None:
        self._provider = provider
        self._cfg = cfg
        self._usage_sink = usage_sink

    def _available(self, detected: Sequence[str] | None) -> list[str]:
        if detected is None:
            names = [name for name in NAMED_CHECKS if getattr(self._cfg.checks, name)]
            names = names or list(NAMED_CHECKS)
        else:
            names = list(detected)
        return [*dict.fromkeys([*names, "cmd:<command>"])]

    def make_plan(
        self,
        task: str,
        repo_summary: str,
        *,
        available_checks: Sequence[str] | None = None,
    ) -> Plan:
        """Call the provider and retry once when the JSON is invalid."""
        prompt = build_plan_prompt(
            task=task,
            repo_summary=repo_summary,
            max_steps=self._cfg.limits.max_steps,
            available_checks=self._available(available_checks),
            schema=Plan.model_json_schema(),
        )
        messages: list[ChatMessage] = [{"role": "user", "content": prompt}]
        last_error = ""
        for attempt in range(2):
            result = self._provider.chat(messages, self._cfg.planner.model)
            self._report(result)
            try:
                return _parse_plan(result.text)
            except ValueError as exc:
                last_error = str(exc)
                if attempt == 0:
                    messages.append({"role": "assistant", "content": result.text})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"Your output was invalid: {last_error}\n"
                                "Output the JSON only."
                            ),
                        }
                    )
        raise PlanError(
            "The planner did not return a valid plan after two attempts.",
            f"Last error: {last_error}",
            "Check the planner model and provider, then run the task again.",
        )

    def _report(self, result: ChatResult) -> None:
        if self._usage_sink is not None:
            self._usage_sink(self._cfg.planner.model, result.input_tokens, result.output_tokens)


def make_plan(
    task: str,
    repo_summary: str,
    cfg: Config,
    provider: Provider | None = None,
    *,
    usage_sink: UsageSink | None = None,
    available_checks: Sequence[str] | None = None,
) -> Plan:
    """Public planner entry point. Builds a provider when none is supplied."""
    owned = provider is None
    if provider is None:
        provider_config = cfg.provider[cfg.planner.provider]
        provider = OpenAICompatProvider(
            provider_config.base_url, cfg.api_key_for(cfg.planner.provider)
        )
    try:
        planner = Planner(provider, cfg, usage_sink)
        return planner.make_plan(task, repo_summary, available_checks=available_checks)
    finally:
        if owned:
            provider.close()
