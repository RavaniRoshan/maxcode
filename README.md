<p align="center">
  <img src="assets/max.svg" width="132" height="149" alt="Max, the maxcode mascot: a silver pixel cursor with a white tick">
</p>

<h1 align="center">maxcode</h1>

<p align="center"><strong>Done means the checks passed.</strong></p>

<p align="center">
  An open-source terminal coding agent that plans the task, edits your repo,<br>
  and runs your tests before it says the work is finished.
</p>

<p align="center">
  <a href="https://github.com/RavaniRoshan/maxcode/actions/workflows/ci.yml"><img src="https://github.com/RavaniRoshan/maxcode/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-D9DEE5.svg" alt="Apache-2.0"></a>
  <img src="https://img.shields.io/badge/python-3.12%2B-0A0F1E.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/status-v0.1-8D99AB.svg" alt="v0.1">
</p>

---

## The problem

Most coding tools stop when the model stops talking. The change may compile. It
may even look right. But nobody ran the tests, so "done" is a guess.

maxcode separates **doing the work** from **declaring it finished**. A planner
splits the task into steps. A worker edits one step at a time. A verifier runs
the repository's own checks. Only a clean verifier run closes the step.

```text
$ maxcode run "fix add so the tests pass"

  plan   3 steps
  step   1/3  read app.py and tests/test_app.py          pass
  step   2/3  fix add() to return a + b                  pass
  check  pytest -q                                       pass  6 passed
  check  ruff check .                                    pass
  done   all checks passed                               0 failures
```

## Why it is different

| | Typical agent | maxcode |
|---|---|---|
| **Definition of done** | The model stops | The verifier passes |
| **Failure handling** | Retry the prompt | Retry from a git checkpoint |
| **Evidence** | Chat transcript | JSONL run log with tokens and cost |
| **Undo** | Manual | `maxcode undo` |
| **Model choice** | Vendor-locked | Any OpenAI-compatible endpoint |
| **Secrets** | Often stored | Environment variables only |

The verifier is not another model opinion. It is the command your project already
trusts: `pytest`, `npm test`, `cargo test`, `go test`, `ruff`, `mypy`, or a
command you configure.

## Install

### 1. The `maxcode` CLI

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and git.

```bash
uvx --from git+https://github.com/RavaniRoshan/maxcode maxcode --help
```

Or work from a checkout:

```bash
git clone https://github.com/RavaniRoshan/maxcode.git
cd maxcode
uv sync
uv run maxcode --help
```

### 2. The engine

maxcode calls a separate engine process for each step. Build the engine once:

```bash
git clone https://github.com/RavaniRoshan/maxcode-engine.git
cd maxcode-engine/maxcode-rs
cargo build --release -p maxcode-cli --bin maxcode-engine
install -m 755 target/release/maxcode-engine ~/.local/bin/maxcode-engine
```

On a low-RAM machine, use the lighter profile:

```bash
cargo build --profile dev-small -p maxcode-cli --bin maxcode-engine
install -m 755 target/dev-small/maxcode-engine ~/.local/bin/maxcode-engine
```

Verify both pieces:

```bash
maxcode-engine --version
maxcode version
```

If the engine lives somewhere else, point to it explicitly:

```bash
export MAXCODE_ENGINE_BIN="$HOME/.local/bin/maxcode-engine"
```

No fallback binary, no hidden download, no key baked into the binary.

## Configure

Create `maxcode.toml` in your project. The provider can be OpenRouter,
Together, Groq, Fireworks, a local server, or anything that speaks the
OpenAI-compatible API.

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
export OPENROUTER_API_KEY="..."
```

maxcode reads the key from the environment at run time. It never writes the key
to a config file, a log, or a checkpoint. Free model availability changes; if a
`:free` slug is unavailable, use a model your account can access.

## Five-minute demo

```bash
mkdir demo && cd demo
git init -b main
mkdir tests

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

maxcode run "fix add so the test passes"
```

Exit code `0` means the verifier passed. Anything else means the work is not
done. If a step exhausts its retries, the run stops at the last checkpoint:

```bash
maxcode undo
```

## How a run works

```text
        task
          |
      [ planner ]  splits into ordered steps
          |
          v
   +--> [ worker ]  edits the repo for one step
   |      |
   |      v
   |  [ verifier ]  runs tests, build, lint
   |      |
   |      +-- pass --> checkpoint --> next step
   |      |
   +------+-- fail --> retry (max 3) --> checkpoint restore
```

1. **Plan.** The planner turns the request into a small, ordered plan.
2. **Work.** The worker edits files inside the repo, using the engine.
3. **Verify.** The verifier runs detected and configured checks in a clean
   subprocess, outside the model.
4. **Checkpoint.** Every step starts from a git ref under `refs/maxcode/`.
5. **Report.** The run writes JSONL events and a cost summary.

## Commands

| Command | What it does |
|---|---|
| `maxcode run TASK` | Plan, edit, verify, and checkpoint a task |
| `maxcode plan TASK` | Print the plan without editing |
| `maxcode undo` | Restore the last checkpoint |
| `maxcode cost [RUN_ID]` | Show token and cost totals |
| `maxcode bench` | Run the benchmark suite |
| `maxcode version` | Print the installed version |

Useful flags: `run --yes`, `run --config PATH`, `run --max-cost USD`,
`plan --config PATH`, `bench --verifier on|off`, `bench --suite PATH`.

## What gets checked

maxcode detects the project type and runs the checks it finds:

- **Python** — pytest, ruff, mypy
- **Node** — the package manager's test, lint, and build scripts
- **Rust** — cargo test, cargo clippy
- **Go** — go test ./...

You can add or override checks in `maxcode.toml`. Checks run with a timeout and
their full output is kept in the run log, so a failure is reproducible.

## Benchmark

The repository ships a benchmark harness, not a leaderboard. It runs the same
task suite twice: once with the verifier on, once with it off. The default suite
is four pinned Python projects repeated five times each, so it measures
consistency rather than breadth. Results and raw logs land in `.maxcode/bench/`.

```bash
maxcode bench --verifier on
maxcode bench --verifier off
uv run python -m maxcode.bench.report .maxcode/bench
```

The report prints pass rate, cost per completed task, and the unverified count.
Numbers depend on the model, provider, and repository; this README does not
publish a score without the matching log.

## Architecture

```text
src/maxcode/
  cli.py            command line and exit codes
  config.py         maxcode.toml, providers, limits
  loop.py           plan -> work -> verify -> checkpoint
  roles/            planner, worker, verifier roles
  engine/           adapter for the maxcode-engine process
  providers/        OpenAI-compatible chat client
  bench/            task suite, runner, report
```

The Python CLI owns the loop and the user experience. The engine owns file edits
and command execution. The verifier is a separate subprocess, so a model cannot
mark its own work as passing.

## Development

```bash
uv sync
uv run pytest -m "not slow"
uv run ruff check .
uv run mypy src
```

`-m "not slow"` skips tests that need a live provider or a real engine. The
engine has its own build notes in
[`maxcode-engine`](https://github.com/RavaniRoshan/maxcode-engine).

## Status

v0.1. The planner/worker/verifier loop, checkpoints, cost reporting, benchmark
harness, and static site are implemented. Live provider runs require your own
API key. The project is deliberately small enough to audit.

## Legal

maxcode is an independent fork of the Codex CLI (Apache-2.0) and is not
affiliated with OpenAI. The original license and notice are preserved in
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
