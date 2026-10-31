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
  <img src="https://img.shields.io/badge/status-v0.1.0--alpha.1-8D99AB.svg" alt="v0.1.0-alpha.1">
</p>

<p align="center"><a href="https://ravaniroshan.github.io/maxcode/">Website</a> · <a href="https://ravaniroshan.github.io/maxcode/docs/">Docs</a></p>

---

## The problem

Most coding tools stop when the model stops talking. The change may compile. It
may even look right. But nobody ran the tests, so "done" is a guess.

maxcode separates **doing the work** from **declaring it finished**. A planner
splits the task into steps. A worker edits one step at a time. A verifier runs
the repository's own checks. Only a clean verifier run closes the step.

Real output from a local Ollama run with the configuration below
([`spike/ollama-llama3.2-3b/maxcode-run/`](spike/ollama-llama3.2-3b/maxcode-run/)):

```text
$ maxcode run --yes "Edit app.py so add(a, b) returns a + b. Use the exec_command
tool to run sed -i 's/return a - b/return a + b/' app.py. Then run python -m pytest -q
to confirm. Do not change tests."

steps: 1/1  cost: $0.0000  tokens: 7182 in / 1067 out
cost is partial: some calls lacked a price or a token count
```

The run log records `test: passed` and `run_end.passed = true`. The demo
repository has one test, not six. The same loop also passed with
`qwen3:1.7b` (7152 input / 1264 output tokens,
[`spike/ollama-qwen3-1.7b/`](spike/ollama-qwen3-1.7b/)).

## What maxcode guarantees

| Question | maxcode's answer |
|---|---|
| **When is a step done?** | Only when every configured or detected check exits 0. |
| **What happens on failure?** | The step retries from its git checkpoint, up to the limit, then stops. |
| **What is the evidence?** | A JSONL run log with check exit codes, token usage, and cost. |
| **Can I undo?** | `maxcode undo` restores the last checkpoint. |
| **Which model?** | Any OpenAI-compatible Responses endpoint. |
| **Where is the key?** | Environment variables only. |

These are guarantees about what maxcode does, not claims about other tools. As
of the 2026-10-29 GitHub search recorded in [`SPIKE.md`](SPIKE.md), **no widely
used open coding CLI makes an independent pass/fail gate its core product**.
Similar ideas exist as add-ons and internal retry loops.

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

maxcode calls a separate engine process for each step. **Stock Codex 0.165 or
newer is the one-minute path:**

```bash
npm install -g @openai/codex@0.165.0
codex --version
```

The adapter looks for an engine in this order:

1. `MAXCODE_ENGINE_BIN`, when set.
2. `maxcode-engine` on `PATH`.
3. `codex` on `PATH`, when its version is 0.165.0 or newer.

Stock Codex and `maxcode-engine` produced the same event types on the same live
task; the comparison is in [`SPIKE.md`](SPIKE.md) and
[`spike/engine-comparison/`](spike/engine-comparison/).

The fork is optional. It is useful only if you want the rebranded binary or a
future engine patch:

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

If the binary lives somewhere else:

```bash
export MAXCODE_ENGINE_BIN="$HOME/.local/bin/maxcode-engine"
```

No hidden download, and no key baked into the binary.

## Configure

Create `maxcode.toml` in your project. The provider can be OpenRouter, Together,
Groq, Fireworks, a local server, or anything that speaks the OpenAI-compatible
Responses API. Codex 0.165 removed Chat Completions support, so the engine side
must expose `/v1/responses`.

This is the configuration that produced the live logs in `spike/`:

```toml
[provider.pollinations]
base_url    = "https://text.pollinations.ai/openai"
api_key_env = "POLLINATIONS_KEY"

[provider.local]
base_url    = "http://127.0.0.1:11434/v1"
api_key_env = "OLLAMA_API_KEY"

[planner]
provider = "pollinations"
model    = "openai"          # the service's alias for gpt-oss-20b

[worker]
provider = "local"
model    = "llama3.2:3b"

[limits]
max_retries_per_step  = 3
max_cost_usd_per_task = 2.00
max_diff_lines        = 400
max_steps             = 12
```

```bash
ollama pull llama3.2:3b
export POLLINATIONS_KEY=anonymous   # the anonymous tier needs a non-empty value
export OLLAMA_API_KEY=local         # Ollama ignores the value
```

maxcode reads each key from the environment at run time. It never writes the key
to a config file, a log, or a checkpoint. The OpenRouter example is not shown
because no funded OpenRouter credential was available for a live log; the same
`[provider.<id>]` shape is used for it, but it was not live-verified here.

The planner must return the JSON plan. A 1.5B planner
(`qwen2.5-coder:1.5b`) returned plans that invented unavailable linters in the
benchmark; choose a planner that can follow the schema. The worker can be a
smaller model: both `qwen3:1.7b` and `llama3.2:3b` produced live edits.

## Demo

The commands below are the ones that produced the live logs. The model pull is
the slow part; after it finishes, the run takes about a minute.

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
[provider.pollinations]
base_url    = "https://text.pollinations.ai/openai"
api_key_env = "POLLINATIONS_KEY"

[provider.local]
base_url    = "http://127.0.0.1:11434/v1"
api_key_env = "OLLAMA_API_KEY"

[planner]
provider = "pollinations"
model    = "openai"

[worker]
provider = "local"
model    = "llama3.2:3b"

[checks]
test = "python -m pytest -q"
TOML

ollama pull llama3.2:3b
export POLLINATIONS_KEY=anonymous OLLAMA_API_KEY=local

maxcode run --yes "Edit app.py so add(a, b) returns a + b. Use the exec_command tool to run sed -i 's/return a - b/return a + b/' app.py. Then run python -m pytest -q to confirm. Do not change tests."
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

- **Python** — pytest; ruff when the project configures it; compileall for `src/`
- **Node** — the package manager's test, lint, and build scripts, when present
- **Rust** — cargo test, cargo build, cargo clippy
- **Go** — go test ./..., go build ./..., go vet ./...

You can add or override checks in `maxcode.toml`. Checks run with a timeout and
their full output is kept in the run log, so a failure is reproducible.

## Benchmark

The repository ships a benchmark harness, not a leaderboard. It runs the same
task suite twice: once with the verifier on, once with it off. Results and raw
logs are published in [`docs/BENCH.md`](docs/BENCH.md) and
[`docs/bench/2026-10-31/`](docs/bench/2026-10-31/).

The 2026-10-31 run used a 3-task subset of the default suite (one task each from
`pallets/click`, `pallets/itsdangerous`, `pallets/markupsafe`), planner
`qwen2.5-coder:1.5b`, and worker `qwen3:1.7b`, both through Ollama 0.31.1:

| Verifier | Score pass rate | Run passed | Tokens in / out |
|---|---:|---:|---:|
| on | 3/3 (100%) | 0/3 | 5,613 / 580 |
| off | 3/3 (100%) | 3/3 | 125,320 / 3,918 |

**The absolute gain is 0 percentage points.** The verifier-on arm hit the
300-second worker timeout before verification, and the repositories were
unchanged, so the final score still passed. This is a ceiling effect, not
evidence of an advantage. `psf/requests` is excluded because its pinned commit
already fails 4 tests on a clean checkout. Read
[`docs/BENCH.md`](docs/BENCH.md) for every failure.

```bash
maxcode bench --verifier on
maxcode bench --verifier off
uv run python -m maxcode.bench.report .maxcode/bench
```

The default suite is four pinned Python projects repeated five times each. A
published score must link to its raw log; this README does not publish one
without it.

## Architecture

```text
src/maxcode/
  cli.py            command line and exit codes
  config.py         maxcode.toml, providers, limits
  loop.py           plan -> work -> verify -> checkpoint
  roles/            planner, worker, verifier roles
  engine/           adapter for stock Codex or maxcode-engine
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

v0.1.0-alpha.1.

**Live-verified** (logs in [`spike/`](spike/)):

- planner -> worker -> verifier loop on Ollama `qwen3:1.7b` and `llama3.2:3b`;
- multi-turn tool calls, file edits that land on disk, and `turn.completed` usage;
- the verifier gate (`1 passed in 0.01s`) and `run_end.passed = true`;
- stock Codex 0.165 and `maxcode-engine` produce the same event types on the
  same task.

**Mock/offline-verified:**

- the full CLI state machine and 115 offline tests;
- OpenRouter, Hugging Face, and DeepSeek wire shapes, without a funded credential.

**Not verified:**

- live runs on the original OpenRouter models `qwen/qwen3-coder-next` and
  `deepseek/deepseek-v3.2`; no funded credential exists in this environment;
- a benchmark gain above 10 points. See [`docs/BENCH.md`](docs/BENCH.md).

The badge stays alpha until a funded-provider run and a wider benchmark exist.
The project is deliberately small enough to audit.

## Legal

maxcode is an independent fork of the Codex CLI (Apache-2.0) and is not
affiliated with OpenAI. The original license and notice are preserved in
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
