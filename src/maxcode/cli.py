# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Command line entry point for maxcode."""

from pathlib import Path
from typing import Any

import typer

from maxcode import __version__
from maxcode.checkpoints import delete_ref, latest_ref, restore
from maxcode.config import load_config
from maxcode.cost import CostMeter
from maxcode.errors import ConfigError, MaxcodeError, NotAGitRepo
from maxcode.loop import _repo_summary, run_task
from maxcode.roles.planner import make_plan
from maxcode.runlog import read_events
from maxcode.schemas import RunOptions

app = typer.Typer(
    name="maxcode",
    help="Plan a task, edit code, and finish only when checks pass.",
    no_args_is_help=True,
)


def _print_error(error: MaxcodeError) -> None:
    typer.echo(str(error), err=True)


def _exit_code_for(error: MaxcodeError) -> int:
    if isinstance(error, (ConfigError, NotAGitRepo)):
        return 2
    return 3


def _load_config(config: Path | None) -> Any:
    try:
        return load_config(config)
    except ConfigError as error:
        _print_error(error)
        raise typer.Exit(code=2) from error


def _require_git(root: Path) -> None:
    from maxcode.checkpoints import is_git_repo

    if not is_git_repo(root):
        error = NotAGitRepo(
            f"'{root}' is not a git repository.",
            "maxcode needs a git repository to create checkpoints.",
            "Run 'git init' in the project directory, then run the command again.",
        )
        _print_error(error)
        raise typer.Exit(code=2)


def _render_plan(plan: Any) -> str:
    lines = [f"Task: {plan.task}", ""]
    for step in plan.steps:
        lines.append(f"Step {step.id}: {step.goal}")
        if step.files:
            lines.append(f"  files: {', '.join(step.files)}")
        lines.append(f"  checks: {', '.join(step.checks) if step.checks else 'none'}")
        lines.append(f"  edits_tests: {str(step.edits_tests).lower()}")
    return "\n".join(lines)


def _print_run_result(result: Any) -> None:
    typer.echo(
        f"steps: {result.steps_done}/{result.total_steps}  "
        f"cost: ${result.cost_usd:.4f}  "
        f"tokens: {result.tokens_in} in / {result.tokens_out} out"
    )
    if result.partial:
        typer.echo("cost is partial: some calls lacked a price or a token count")
    if result.unverified_steps:
        typer.echo("unverified: " + ", ".join(str(item) for item in result.unverified_steps))
    if result.stop_reason is not None:
        typer.echo(f"stopped: {result.stop_reason}")
    if result.error:
        typer.echo(result.error)
    if result.exit_code != 0:
        typer.echo("run 'maxcode undo' to restore the last checkpoint")


@app.command()
def run(
    task: str,
    yes: bool = typer.Option(False, "--yes", help="Skip plan approval."),
    config: Path | None = typer.Option(None, "--config", help="Path to maxcode.toml."),
    max_cost: float | None = typer.Option(None, "--max-cost", help="Cost cap in USD."),
) -> None:
    """Plan, edit, and verify a task."""
    cfg = _load_config(config)
    root = Path.cwd()
    _require_git(root)
    options = RunOptions(yes=yes, max_cost_usd=max_cost, verifier=True)
    meter_cap = max_cost if max_cost is not None else cfg.limits.max_cost_usd_per_task
    meter = CostMeter(cfg.pricing, meter_cap)

    def approve(plan: Any) -> bool:
        if yes:
            return True
        typer.echo(_render_plan(plan))
        return typer.confirm("Approve this plan?", default=False)

    try:
        result = run_task(
            task,
            cfg,
            options,
            repo=root,
            approve=approve,
            meter=meter,
        )
    except MaxcodeError as error:
        _print_error(error)
        raise typer.Exit(code=_exit_code_for(error)) from error
    except KeyboardInterrupt:
        raise typer.Exit(code=130) from None
    _print_run_result(result)
    raise typer.Exit(code=result.exit_code)


@app.command()
def plan(
    task: str,
    config: Path | None = typer.Option(None, "--config", help="Path to maxcode.toml."),
) -> None:
    """Show a plan without running it."""
    cfg = _load_config(config)
    root = Path.cwd()
    _require_git(root)
    from maxcode.checks import available_check_names, detect_checks

    detected = detect_checks(root)
    available = available_check_names(cfg, detected)
    pcfg = cfg.provider[cfg.planner.provider]
    from maxcode.providers.openai_compat import OpenAICompatProvider

    provider = OpenAICompatProvider(pcfg.base_url, cfg.api_key_for(cfg.planner.provider))
    try:
        planned = make_plan(task, _repo_summary(root), cfg, provider, available_checks=available)
    except MaxcodeError as error:
        _print_error(error)
        raise typer.Exit(code=_exit_code_for(error)) from error
    finally:
        provider.close()
    typer.echo(_render_plan(planned))


@app.command()
def undo() -> None:
    """Restore the last checkpoint."""
    root = Path.cwd()
    _require_git(root)
    ref = latest_ref(root)
    if ref is None:
        typer.echo("No checkpoint to undo.", err=True)
        raise typer.Exit(code=1)
    try:
        restore(ref, root)
        delete_ref(ref, root)
    except MaxcodeError as error:
        _print_error(error)
        raise typer.Exit(code=_exit_code_for(error)) from error
    typer.echo(f"Restored {ref}.")


@app.command()
def cost(run_id: str | None = typer.Argument(None, help="Run id to inspect.")) -> None:
    """Show the cost of a run."""
    root = Path.cwd()
    _require_git(root)
    cfg = _load_config(None)
    runs_dir = root / ".maxcode" / "runs"
    if run_id is None:
        if not runs_dir.is_dir():
            typer.echo("No runs found.", err=True)
            raise typer.Exit(code=1)
        candidates = sorted(path for path in runs_dir.iterdir() if path.is_dir())
        if not candidates:
            typer.echo("No runs found.", err=True)
            raise typer.Exit(code=1)
        run_dir = candidates[-1]
        run_id = run_dir.name
    else:
        run_dir = runs_dir / run_id
    log_path = run_dir / "log.jsonl"
    if not log_path.is_file():
        typer.echo(f"Run log not found: {log_path}", err=True)
        raise typer.Exit(code=2)
    events = read_events(log_path)
    tokens_in = 0
    tokens_out = 0
    cost_usd = 0.0
    partial = False
    run_end = None
    for event in events:
        if event.type == "worker_call":
            model = event.data.get("model")
            in_tokens = event.data.get("input_tokens")
            out_tokens = event.data.get("output_tokens")
            if in_tokens is None or out_tokens is None:
                partial = True
            else:
                tokens_in += int(in_tokens)
                tokens_out += int(out_tokens)
            price = cfg.pricing.get(model) if model else None
            if price is None or in_tokens is None or out_tokens is None:
                partial = True
            else:
                cost_usd += (
                    int(in_tokens) * price.input_per_mtok_usd / 1_000_000
                    + int(out_tokens) * price.output_per_mtok_usd / 1_000_000
                )
        elif event.type == "run_end":
            run_end = event.data
    if run_end is not None:
        typer.echo(
            f"run {run_id}: cost ${run_end.get('cost_usd', cost_usd):.4f}  "
            f"tokens {run_end.get('tokens_in', tokens_in)} in / "
            f"{run_end.get('tokens_out', tokens_out)} out"
        )
    else:
        typer.echo(f"run {run_id}: cost ${cost_usd:.4f}  tokens {tokens_in} in / {tokens_out} out")
    if partial:
        typer.echo("partial")


@app.command()
def bench(
    verifier: str = typer.Option("on", "--verifier", help="on or off."),
    suite: Path | None = typer.Option(None, "--suite", help="Suite directory."),
) -> None:
    """Run the benchmark suite."""
    if verifier not in {"on", "off"}:
        typer.echo("verifier must be on or off", err=True)
        raise typer.Exit(code=2)
    from maxcode.bench.runner import run_bench

    cfg = _load_config(None)
    root = Path.cwd()
    _require_git(root)
    try:
        summary = run_bench(
            suite=suite,
            verifier=verifier == "on",
            root=root,
            cfg=cfg,
        )
    except MaxcodeError as error:
        _print_error(error)
        raise typer.Exit(code=_exit_code_for(error)) from error
    typer.echo(
        f"tasks: {summary.passed}/{summary.total}  "
        f"invalid: {summary.invalid}  errors: {summary.errors}  "
        f"cost: ${summary.cost_usd:.4f}"
    )


@app.command()
def version() -> None:
    """Show the installed version."""
    typer.echo(f"maxcode {__version__}")
