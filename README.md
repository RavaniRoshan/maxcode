# maxcode

[![CI](https://github.com/RavaniRoshan/maxcode/actions/workflows/ci.yml/badge.svg)](https://github.com/RavaniRoshan/maxcode/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**maxcode** is an open-source terminal coding agent. It plans a task, edits code
with an engine, and marks the task done **only after an independent set of checks
passes**.

> Forked from the Codex CLI (Apache-2.0). maxcode is an independent project and
> is not affiliated with, endorsed by, or sponsored by OpenAI or Sarvam AI.

## Why maxcode

Most coding tools report a task as done when it is not done. The user finds the
failure by hand. maxcode adds a verifier loop: a planner splits the task into
steps, a worker edits files for one step, and a verifier runs tests, builds, and
lint commands. A step is done only when every check passes. Every step starts
from a git checkpoint, every run writes a JSONL log, and every run reports token
use and cost.

## Features

- **Planner / Worker / Verifier** roles with a retry loop (default 3 tries).
- **Git checkpoints** under `refs/maxcode/` and a one-command `undo`.
- **OpenAI-compatible provider** layer (any endpoint, including open-weight models).
- **Cost and token reporting**, including partial results when counts are missing.
- **JSONL run logs** for reproducible evidence.
- **Check detection** for Python, Node, Rust, and Go repositories.
- **Benchmark runner** with 20 tasks and a report script.
- **Four-page static site** hosted on GitHub Pages.
- No API key is ever stored; keys come from environment variables only.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- git
- An OpenAI-compatible provider and an API key in an environment variable

## Install

```bash
git clone https://github.com/RavaniRoshan/maxcode.git
cd maxcode
uv sync
uv run maxcode --help
```

## Configure

Create `maxcode.toml` in your project:

```toml
[provider.main]
base_url    = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"

[planner]
provider = "main"
model    = "qwen/qwen3-coder-next"

[worker]
provider = "main"
model    = "deepseek/deepseek-v3.2"

[limits]
max_retries_per_step  = 3
max_cost_usd_per_task = 2.00
max_diff_lines        = 400
max_steps             = 12
```

```bash
export OPENROUTER_API_KEY=...
```

## Five-minute demo

```bash
mkdir demo && cd demo
git init -b main
mkdir -p tests
cat > app.py <<'PY'
def add(a, b):
    return a - b
PY
cat > tests/test_app.py <<'PY'
from app import add

def test_add():
    assert add(2, 3) == 5
PY
cat > maxcode.toml <<'TOML'
[provider.main]
base_url    = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"

[planner]
provider = "main"
model    = "qwen/qwen3-coder-next"

[worker]
provider = "main"
model    = "deepseek/deepseek-v3.2"
TOML
uv run --project .. maxcode run "fix add so the test passes"
```

The run exits 0 only after `tests/test_app.py` passes. If a step fails, run
`uv run --project .. maxcode undo` to restore the last checkpoint.

## Commands

| Command | Action |
|---|---|
| `maxcode run TASK` | Plan, edit, and verify a task. |
| `maxcode plan TASK` | Show the plan and stop. |
| `maxcode undo` | Restore the last checkpoint. |
| `maxcode cost [RUN_ID]` | Show the cost of a run. |
| `maxcode bench` | Run the benchmark suite. |

Options: `run --yes`, `run --config PATH`, `run --max-cost USD`,
`plan --config PATH`, `bench --verifier on|off`, `bench --suite PATH`.

## Benchmark

Twenty small tasks, run twice: once with the verifier on and once with it off.
Results and logs are written under `.maxcode/bench/`.

```bash
maxcode bench --verifier on
maxcode bench --verifier off
uv run python -m maxcode.bench.report .maxcode/bench
```

The report prints pass rate, cost per completed task, and the unverified count.

## Engine

maxcode calls an engine as a child process. By default it looks for
`maxcode-engine` on `PATH`, then falls back to `codex`. Set `MAXCODE_ENGINE_BIN`
to override the binary path. The engine is a minimal fork of the Codex CLI.

## Development

```bash
uv sync
uv run pytest -m "not slow"
uv run ruff check .
uv run mypy src
```

## Project layout

See `PRD.md` section 20. Source lives in `src/maxcode/`, tests in `tests/`,
and the marketing site in `site/`.

## Legal

Apache-2.0. See `LICENSE` and `NOTICE`. maxcode is an independent project and
is not affiliated with OpenAI or Sarvam AI. Trademark and legal review are tracked
in `docs/LEGAL.md`.

## Status

Version 0.1. Live runs on open-weight models require an OpenRouter (or
compatible) API key and are recorded in `SPIKE.md`.
