# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the run loop state machine."""

from pathlib import Path

import pytest

from maxcode.config import Config
from maxcode.cost import CostMeter
from maxcode.loop import LoopDeps, run_task
from maxcode.runlog import RunLog
from maxcode.schemas import EngineResult, Plan, PlanStep, RunOptions, StepVerification


def init_repo(repo: Path) -> None:
    repo.mkdir()
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def make_config(max_steps: int = 12, max_retries: int = 3) -> Config:
    return Config.model_validate(
        {
            "provider": {
                "main": {
                    "base_url": "https://api.example.com/v1",
                    "api_key_env": "MAXCODE_TEST_KEY",
                }
            },
            "planner": {"provider": "main", "model": "m"},
            "worker": {"provider": "main", "model": "m"},
            "limits": {"max_steps": max_steps, "max_retries_per_step": max_retries},
            "checks": {"test": "true"},
        }
    )


def make_plan(steps: int = 1) -> Plan:
    return Plan(
        task="t",
        steps=[
            PlanStep(id=i + 1, goal=f"step {i + 1}", files=[], checks=["test"])
            for i in range(steps)
        ],
    )


def make_deps(
    tmp_path: Path,
    *,
    plan: Plan | None = None,
    work_results: list[EngineResult] | None = None,
    verify_results: list[StepVerification] | None = None,
    approved: bool = True,
    detected: dict[str, str] | None = None,
    meter: CostMeter | None = None,
) -> tuple[LoopDeps, dict[str, list]]:
    repo = tmp_path / "repo"
    init_repo(repo)
    runlog = RunLog(tmp_path / "log.jsonl", "run-test")
    created: list[str] = []
    restored: list[str] = []
    work_calls: list[tuple] = []
    verify_calls: list = []

    if work_results is None:
        work_results = [EngineResult(exit_code=0, transcript="ok", input_tokens=1, output_tokens=1)]
    if verify_results is None:
        verify_results = [StepVerification(step_id=1, passed=True, diff_lines=1, unverified=False)]

    def checkpoint_create(run_id: str, step_id: int) -> str:
        ref = f"refs/maxcode/{run_id}/{step_id}"
        created.append(ref)
        return ref

    def checkpoint_restore(ref: str) -> None:
        restored.append(ref)

    work_iter = iter(work_results)
    verify_iter = iter(verify_results)

    def work(step, failure):
        work_calls.append((step.id, failure))
        return next(work_iter)

    def verify(step, ref):
        verify_calls.append((step.id, ref))
        result = next(verify_iter)
        result.step_id = step.id
        return result

    deps = LoopDeps(
        plan=lambda t, s: plan if plan is not None else make_plan(1),
        work=work,
        checkpoint_create=checkpoint_create,
        checkpoint_restore=checkpoint_restore,
        verify=verify,
        diff_stats=lambda ref: (["README.md"], 1),
        detect_checks=lambda: detected if detected is not None else {"test": "true"},
        repo_summary=lambda: "summary",
        approve_plan=lambda p: approved,
    )
    state = {
        "repo": repo,
        "runlog": runlog,
        "created": created,
        "restored": restored,
        "work_calls": work_calls,
        "verify_calls": verify_calls,
    }
    return deps, state


def events(runlog: RunLog) -> list[dict]:
    return [e.model_dump() for e in runlog.read_events() if False] or __import__(
        "maxcode.runlog", fromlist=["read_events"]
    ).read_events(runlog.path)


def test_init_not_git_raises(tmp_path: Path) -> None:
    from maxcode.errors import NotAGitRepo

    with pytest.raises(NotAGitRepo):
        run_task("task", make_config(), RunOptions(yes=True), repo=tmp_path / "nogit")


def test_plan_parsed_runs_to_done(tmp_path: Path) -> None:
    deps, state = make_deps(tmp_path)
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
        meter=CostMeter(make_config().pricing, 10.0),
    )
    assert result.exit_code == 0
    assert result.passed is True
    assert result.steps_done == 1
    reader = __import__("maxcode.runlog", fromlist=["read_events"]).read_events
    types = [e.type for e in reader(state["runlog"].path)]
    assert types == [
        "run_start",
        "plan",
        "step_start",
        "worker_call",
        "step_end",
        "run_end",
    ]


def test_plan_invalid_twice_exits_3(tmp_path: Path) -> None:
    deps, state = make_deps(tmp_path)
    deps.plan = lambda t, s: (_ for _ in ()).throw(Exception("bad"))
    # make plan raise PlanError instead
    from maxcode.errors import PlanError

    deps.plan = lambda t, s: (_ for _ in ()).throw(PlanError("x", "y", "z"))
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 3
    assert result.stop_reason == "error"
    assert "x" in result.error


def test_review_rejected_exits_130(tmp_path: Path) -> None:
    deps, state = make_deps(tmp_path, approved=False)
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=False),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 130
    assert result.stop_reason == "user_abort"


def test_worker_failure_exits_3_and_restores(tmp_path: Path) -> None:
    bad = EngineResult(exit_code=1, transcript="boom", input_tokens=1, output_tokens=1)
    deps, state = make_deps(tmp_path, work_results=[bad])
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 3
    assert state["restored"] == state["created"]


def test_verify_failure_retries_then_passes(tmp_path: Path) -> None:
    fail = StepVerification(
        step_id=1, passed=False, diff_lines=1, unverified=False, failure_output="assertion failed"
    )
    ok = StepVerification(step_id=1, passed=True, diff_lines=1, unverified=False)
    deps, state = make_deps(
        tmp_path,
        work_results=[
            EngineResult(exit_code=0, transcript="ok", input_tokens=1, output_tokens=1),
            EngineResult(exit_code=0, transcript="ok", input_tokens=1, output_tokens=1),
        ],
        verify_results=[fail, ok],
    )
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 0
    assert len(state["work_calls"]) == 2
    reader = __import__("maxcode.runlog", fromlist=["read_events"]).read_events
    types = [e.type for e in reader(state["runlog"].path)]
    assert "retry" in types


def test_retry_limit_exits_1_and_restores(tmp_path: Path) -> None:
    fail = StepVerification(
        step_id=1, passed=False, diff_lines=1, unverified=False, failure_output="nope"
    )
    deps, state = make_deps(
        tmp_path,
        work_results=[
            EngineResult(exit_code=0, transcript="ok", input_tokens=1, output_tokens=1),
            EngineResult(exit_code=0, transcript="ok", input_tokens=1, output_tokens=1),
            EngineResult(exit_code=0, transcript="ok", input_tokens=1, output_tokens=1),
        ],
        verify_results=[fail, fail, fail],
    )
    result = run_task(
        "task",
        make_config(max_retries=3),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 1
    assert result.stop_reason == "retry_limit"
    assert state["restored"] == state["created"]


def test_multi_step_runs_all(tmp_path: Path) -> None:
    plan = make_plan(2)
    ok = StepVerification(step_id=1, passed=True, diff_lines=1, unverified=False)
    deps, state = make_deps(tmp_path, plan=plan, verify_results=[ok, ok])
    # work_results needs two
    deps.work = lambda step, failure: EngineResult(
        exit_code=0, transcript="ok", input_tokens=1, output_tokens=1
    )
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 0
    assert result.steps_done == 2


def test_cost_cap_exits_1_and_restores(tmp_path: Path) -> None:
    from maxcode.cost import CostMeter

    meter = CostMeter(make_config().pricing, cap_usd=0.0)
    # make meter already at cap before run by adding a call
    meter.add("m", 1000, 1000)
    deps, state = make_deps(tmp_path, meter=meter)
    # work also updates meter but cap already reached; check before work triggers
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
        meter=meter,
    )
    assert result.exit_code == 1
    assert result.stop_reason == "cost_cap"


def test_step_cap_exits_1(tmp_path: Path) -> None:
    plan = make_plan(3)
    deps, state = make_deps(tmp_path, plan=plan)
    result = run_task(
        "task",
        make_config(max_steps=2),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 1
    assert result.stop_reason == "step_cap"


def test_keyboard_interrupt_exits_130_and_keeps_files(tmp_path: Path) -> None:
    deps, state = make_deps(tmp_path)

    def boom(step, failure):
        raise KeyboardInterrupt()

    deps.work = boom
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 130
    assert result.stop_reason == "user_abort"
    assert state["restored"] == []  # keep files


def test_unverified_step_exits_4(tmp_path: Path) -> None:
    unverified = StepVerification(step_id=1, passed=False, diff_lines=1, unverified=True)
    deps, state = make_deps(tmp_path, verify_results=[unverified])
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True, verifier=True),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 4
    assert 1 in result.unverified_steps


def test_verifier_off_skips_verify(tmp_path: Path) -> None:
    deps, state = make_deps(tmp_path)
    # replace verify with one that would fail if called
    deps.verify = lambda step, ref: (_ for _ in ()).throw(AssertionError("should not verify"))
    result = run_task(
        "task",
        make_config(),
        RunOptions(yes=True, verifier=False),
        repo=state["repo"],
        runlog=state["runlog"],
        deps=deps,
    )
    assert result.exit_code == 0
    reader = __import__("maxcode.runlog", fromlist=["read_events"]).read_events
    types = [e.type for e in reader(state["runlog"].path)]
    assert "check_result" not in types
