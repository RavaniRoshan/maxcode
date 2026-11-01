# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Run controller: the planner, worker, and verifier state machine."""

import contextlib
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from maxcode.checkpoints import create, is_git_repo, repo_head, restore
from maxcode.checks import (
    available_check_names,
    detect_checks,
    verify_step,
)
from maxcode.config import Config
from maxcode.cost import CostMeter
from maxcode.errors import NotAGitRepo, PlanError
from maxcode.roles.planner import make_plan
from maxcode.roles.worker import do_step
from maxcode.runlog import RunLog, new_run_id
from maxcode.schemas import (
    Plan,
    RunOptions,
    RunResult,
    StepVerification,
    StopReason,
)

SKIP_DIRS = frozenset({".git", ".venv", "node_modules", ".maxcode", "__pycache__"})


class _Stop(Exception):
    """Internal control-flow exception for a clean stop."""

    def __init__(self, reason: StopReason, exit_code: int, restore_ref: str | None = None) -> None:
        self.reason = reason
        self.exit_code = exit_code
        self.restore_ref = restore_ref


@dataclass
class LoopDeps:
    """Injectable side effects for run_task."""

    plan: Callable[[str, str], Plan]
    work: Callable[[object, str | None], object]
    checkpoint_create: Callable[[str, int], str]
    checkpoint_restore: Callable[[str], None]
    verify: Callable[[object, str], StepVerification]
    diff_stats: Callable[[str], tuple[list[str], int]]
    detect_checks: Callable[[], dict[str, str]]
    repo_summary: Callable[[], str]
    approve_plan: Callable[[Plan], bool]


def _ensure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    if ".maxcode/" not in lines:
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n.maxcode/\n")


def _repo_summary(root: Path) -> str:
    lines: list[str] = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        try:
            relative = current.relative_to(root)
        except ValueError:
            continue
        depth = len(relative.parts)
        dirnames[:] = sorted(
            name for name in dirnames if name not in SKIP_DIRS and not name.startswith(".")
        )
        if depth >= 3:
            dirnames[:] = []
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            lines.append(str(relative / name) if str(relative) != "." else name)
            count += 1
            if count >= 200:
                break
        if count >= 200:
            break
    tree = "\n".join(lines)
    readme = ""
    for candidate in ("README.md", "README.rst", "README.txt", "README"):
        path = root / candidate
        if path.is_file():
            readme = path.read_text(encoding="utf-8", errors="replace")[:2000]
            break
    return f"Files:\n{tree}\n\nREADME:\n{readme}"


def run_task(
    task: str,
    cfg: Config,
    options: RunOptions,
    *,
    repo: str | Path = ".",
    provider: Any | None = None,
    engine: Any | None = None,
    meter: CostMeter | None = None,
    runlog: RunLog | None = None,
    approve: Callable[[Plan], bool] | None = None,
    deps: LoopDeps | None = None,
) -> RunResult:
    """Run the full state machine for one task."""
    root = Path(repo).resolve()
    if not is_git_repo(root):
        raise NotAGitRepo(
            f"'{root}' is not a git repository.",
            "maxcode needs a git repository to create checkpoints.",
            "Run 'git init' in the project directory, then run the command again.",
        )

    from maxcode.checkpoints import diff_stats as real_diff_stats
    from maxcode.engine.runner import run_step as real_run_step
    from maxcode.providers.openai_compat import OpenAICompatProvider

    if meter is None:
        cap = (
            options.max_cost_usd
            if options.max_cost_usd is not None
            else cfg.limits.max_cost_usd_per_task
        )
        meter = CostMeter(cfg.pricing, cap)
    run_id = runlog.run_id if runlog is not None else new_run_id()
    if runlog is None:
        runlog = RunLog(root / ".maxcode" / "runs" / run_id / "log.jsonl", run_id)
    _ensure_gitignore(root)

    detected = detect_checks(root)
    available = available_check_names(cfg, detected)

    if provider is None and deps is None:
        pcfg = cfg.provider[cfg.planner.provider]
        provider = OpenAICompatProvider(pcfg.base_url, cfg.api_key_for(cfg.planner.provider))

    owned_provider = provider is not None and deps is None

    if deps is None:
        plan_provider = provider

        def plan(task_text: str, summary: str) -> Plan:
            return make_plan(
                task_text,
                summary,
                cfg,
                plan_provider,
                usage_sink=meter.add,
                available_checks=available,
            )

        def work(step: Any, failure: str | None) -> Any:
            return do_step(
                step,
                failure,
                cfg,
                task=task,
                repo=root,
                engine=engine if engine is not None else real_run_step,
                meter=meter,
                timeout_s=cfg.limits.worker_timeout_s,
            )

        def checkpoint_create(run: str, step_id: int) -> str:
            return create(run, step_id, root)

        def checkpoint_restore(ref: str) -> None:
            restore(ref, root)

        def verify(step: object, ref: str) -> StepVerification:
            return verify_step(step, cfg, root, ref, detected)

        def diff_stats_for(ref: str) -> tuple[list[str], int]:
            return real_diff_stats(ref, root)

        deps = LoopDeps(
            plan=plan,
            work=work,
            checkpoint_create=checkpoint_create,
            checkpoint_restore=checkpoint_restore,
            verify=verify,
            diff_stats=diff_stats_for,
            detect_checks=lambda: detected,
            repo_summary=lambda: _repo_summary(root),
            approve_plan=approve if approve is not None else (lambda _plan: options.yes),
        )

    unverified_steps: list[int] = []
    steps_done = 0
    total_steps = 0
    current_ref: str | None = None
    stop_reason: StopReason | None = None
    exit_code = 0
    current_plan: Plan | None = None

    try:
        head = repo_head(root)
        runlog.write(
            "run_start",
            {"task": task, "config_hash": cfg.config_hash(), "repo_head": head},
        )

        try:
            current_plan = deps.plan(task, deps.repo_summary())
        except PlanError as exc:
            raise _Stop(StopReason.ERROR, 3) from exc

        if meter.cap_reached:
            raise _Stop(StopReason.COST_CAP, 1)
        assert current_plan is not None
        if len(current_plan.steps) > cfg.limits.max_steps:
            raise _Stop(StopReason.STEP_CAP, 1)

        runlog.write("plan", {"steps": [step.model_dump() for step in current_plan.steps]})
        total_steps = len(current_plan.steps)

        approved = deps.approve_plan(current_plan)
        if not approved:
            raise _Stop(StopReason.USER_ABORT, 130)

        for step in current_plan.steps:
            if steps_done + len(unverified_steps) + 1 > cfg.limits.max_steps:
                raise _Stop(StopReason.STEP_CAP, 1)

            ref = deps.checkpoint_create(run_id, step.id)
            current_ref = ref
            runlog.write("step_start", {"step_id": step.id, "checkpoint_ref": ref})

            attempt = 1
            failure_output: str | None = None
            step_passed = False
            step_unverified = False
            diff_lines = 0

            while True:
                if meter.cap_reached:
                    raise _Stop(StopReason.COST_CAP, 1, ref)

                try:
                    engine_result: Any = deps.work(step, failure_output)
                except Exception as exc:  # noqa: BLE001
                    raise _Stop(StopReason.ERROR, 3, ref) from exc

                runlog.write(
                    "worker_call",
                    {
                        "model": cfg.worker.model,
                        "input_tokens": engine_result.input_tokens,
                        "output_tokens": engine_result.output_tokens,
                        "seconds": engine_result.seconds,
                    },
                )

                if getattr(engine_result, "failed", False) or getattr(
                    engine_result, "timed_out", False
                ):
                    raise _Stop(StopReason.ERROR, 3, ref)

                if meter.cap_reached:
                    raise _Stop(StopReason.COST_CAP, 1, ref)

                if options.verifier:
                    verification = deps.verify(step, ref)
                    diff_lines = verification.diff_lines
                    for check_result in verification.results:
                        runlog.write(
                            "check_result",
                            {
                                "step_id": step.id,
                                "check": check_result.name,
                                "passed": check_result.passed,
                                "exit_code": check_result.exit_code,
                                "output_tail": check_result.output_tail,
                            },
                        )
                    if "protected path changed" in verification.failure_output:
                        runlog.write(
                            "check_result",
                            {
                                "step_id": step.id,
                                "check": "protected",
                                "passed": False,
                                "exit_code": 1,
                                "output_tail": verification.failure_output,
                            },
                        )
                    if "diff exceeds limit" in verification.failure_output:
                        runlog.write(
                            "check_result",
                            {
                                "step_id": step.id,
                                "check": "diff",
                                "passed": False,
                                "exit_code": 1,
                                "output_tail": verification.failure_output,
                            },
                        )
                    if verification.unverified:
                        step_passed = False
                        step_unverified = True
                    elif verification.passed:
                        step_passed = True
                        step_unverified = False
                    else:
                        step_unverified = verification.unverified
                        if attempt < cfg.limits.max_retries_per_step:
                            runlog.write("retry", {"step_id": step.id, "attempt": attempt + 1})
                            failure_output = verification.failure_output[-4000:]
                            attempt += 1
                            continue
                        raise _Stop(StopReason.RETRY_LIMIT, 1, ref)
                else:
                    step_passed = True
                    _, diff_lines = deps.diff_stats(ref)

                break

            steps_done += 1 if step_passed else 0
            if step_unverified:
                unverified_steps.append(step.id)
            runlog.write(
                "step_end",
                {
                    "step_id": step.id,
                    "passed": step_passed,
                    "diff_lines": diff_lines,
                    "unverified": step_unverified,
                },
            )
            current_ref = None

    except _Stop as stop:
        stop_reason = stop.reason
        exit_code = stop.exit_code
        if stop.restore_ref is not None:
            with contextlib.suppress(Exception):
                deps.checkpoint_restore(stop.restore_ref)
    except KeyboardInterrupt:
        stop_reason = StopReason.USER_ABORT
        exit_code = 130
    except Exception:
        stop_reason = StopReason.ERROR
        exit_code = 3
        if current_ref is not None:
            with contextlib.suppress(Exception):
                deps.checkpoint_restore(current_ref)

    if stop_reason is None:
        stop_reason = None

    passed = stop_reason is None and not unverified_steps and steps_done == total_steps
    if exit_code == 0 and unverified_steps:
        exit_code = 4

    runlog.write(
        "run_end",
        {
            "passed": passed,
            "steps_done": steps_done,
            "cost_usd": meter.total_usd,
            "tokens_in": meter.tokens_in,
            "tokens_out": meter.tokens_out,
        },
    )

    if owned_provider and provider is not None:
        with contextlib.suppress(Exception):
            provider.close()

    return RunResult(
        run_id=run_id,
        passed=passed,
        exit_code=exit_code,
        steps_done=steps_done,
        total_steps=total_steps,
        unverified_steps=unverified_steps,
        cost_usd=meter.total_usd,
        tokens_in=meter.tokens_in,
        tokens_out=meter.tokens_out,
        partial=meter.partial,
        stop_reason=stop_reason,
        log_path=str(runlog.path),
    )
