# maxcode

maxcode is an open-source terminal coding agent. It plans a task, edits code,
and marks the task done only after an independent set of checks passes.

- **Planner** turns one task into small, ordered steps.
- **Worker** edits files for one step at a time.
- **Verifier** runs tests, builds, and lint commands. It ignores what the worker
  says and decides pass or fail from real command output.

Every step starts from a git checkpoint, every run writes a JSONL log, and every
run reports token use and cost. `maxcode undo` restores the last checkpoint.

maxcode is an independent project. It is not affiliated with, endorsed by, or
sponsored by OpenAI or Sarvam AI.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- git
- An OpenAI-compatible provider and an API key in an environment variable

## Install

```bash
git clone https://github.com/roshanravani/maxcode.git
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

Set the key in your shell:

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

The run ends with exit code 0 only after `tests/test_app.py` passes. If a step
fails, run `uv run --project .. maxcode undo`.

## Commands

| Command | Action |
|---|---|
| `maxcode run TASK` | Plan, edit, and verify a task. |
| `maxcode plan TASK` | Show the plan and stop. |
| `maxcode undo` | Restore the last checkpoint. |
| `maxcode cost [RUN_ID]` | Show the cost of a run. |
| `maxcode bench` | Run the benchmark suite. |

Options: `run --yes`, `run --config PATH`, `run --max-cost USD`, `plan --config PATH`,
`bench --verifier on|off`, `bench --suite PATH`.

## Benchmark

The benchmark runs 20 small tasks twice: once with the verifier on and once with
it off. Results and logs are written under `.maxcode/bench/`.

```bash
maxcode bench --verifier on
maxcode bench --verifier off
uv run python -m maxcode.bench.report .maxcode/bench
```

The report prints pass rate, cost per completed task, and the unverified count.
Published logs live in the repository under the benchmark output directory.

## Development

```bash
uv sync
uv run pytest -m "not slow"
uv run ruff check .
uv run mypy src
```

## Legal

Apache-2.0. See `LICENSE` and `NOTICE`. maxcode is an independent project and
is not affiliated with OpenAI or Sarvam AI.
