# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Pydantic models shared by the planner, worker, verifier, and loop."""

from enum import StrEnum
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field, field_validator

NAMED_CHECKS = frozenset({"test", "build", "lint"})


class ChatMessage(TypedDict):
    """One message in an OpenAI chat request."""

    role: Literal["system", "user", "assistant"]
    content: str


class ChatResult(BaseModel):
    """Text and token counts from one provider call."""

    text: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class PlanStep(BaseModel):
    """One step in a plan."""

    id: int = Field(ge=1)
    goal: str = Field(min_length=1)
    files: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    edits_tests: bool = False

    @field_validator("checks")
    @classmethod
    def validate_checks(cls, values: list[str]) -> list[str]:
        for value in values:
            if value in NAMED_CHECKS:
                continue
            if value.startswith("cmd:") and value[4:].strip():
                continue
            raise ValueError(
                f"invalid check '{value}'; use test, build, lint, or cmd:<command>"
            )
        return values


class Plan(BaseModel):
    """The planner output."""

    task: str = Field(min_length=1)
    steps: list[PlanStep] = Field(min_length=1)

    @field_validator("steps")
    @classmethod
    def validate_unique_ids(cls, steps: list[PlanStep]) -> list[PlanStep]:
        ids = [step.id for step in steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")
        return steps


class EngineResult(BaseModel):
    """The result of one worker engine call."""

    exit_code: int
    transcript: str = ""
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    seconds: float = Field(default=0.0, ge=0)
    timed_out: bool = False

    @property
    def failed(self) -> bool:
        """True when the engine did not finish successfully."""
        return self.timed_out or self.exit_code != 0


class CheckResult(BaseModel):
    """The result of one command check."""

    name: str
    command: str
    passed: bool
    exit_code: int
    output_tail: str = ""
    seconds: float = Field(default=0.0, ge=0)


class StepVerification(BaseModel):
    """The verifier verdict for one step."""

    step_id: int
    passed: bool
    diff_lines: int = 0
    results: list[CheckResult] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    unverified: bool = False
    failure_output: str = ""


class RunOptions(BaseModel):
    """Options that change how one run behaves."""

    yes: bool = False
    max_cost_usd: float | None = Field(default=None, gt=0)
    verifier: bool = True


class StopReason(StrEnum):
    """Allowed values of the stop event reason."""

    RETRY_LIMIT = "retry_limit"
    COST_CAP = "cost_cap"
    STEP_CAP = "step_cap"
    USER_ABORT = "user_abort"
    ERROR = "error"


class RunResult(BaseModel):
    """The outcome of one run."""

    run_id: str
    passed: bool
    exit_code: int
    steps_done: int = 0
    total_steps: int = 0
    unverified_steps: list[int] = Field(default_factory=list)
    cost_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    partial: bool = False
    stop_reason: StopReason | None = None
    log_path: str = ""


class RunEvent(BaseModel):
    """One line of the JSONL run log."""

    ts: str
    run_id: str
    type: str
    data: dict[str, Any]
