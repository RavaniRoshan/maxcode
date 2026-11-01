# maxcode 0.1.0-alpha.1

Released 2026-11-01. Not published to PyPI.

## What it does

maxcode is a terminal coding agent that plans a task, edits a repository through
an engine process, and closes a step only when the repository's own checks exit
0. A failed check goes back to the worker; when the retries run out the run
stops at the git checkpoint it wrote before the step. Every run writes a JSONL
log with check exit codes, token counts, and cost.

The demo run in this repository is the shortest evidence of that loop:
`step_end` is `passed: true` with `unverified: false`, and `run_end` is
`passed: true` after `python3 -m pytest -q` printed `1 passed in 0.00s`
([`docs/demo/run.jsonl`](../docs/demo/run.jsonl)). The recording is
[`docs/demo/demo.cast`](../docs/demo/demo.cast), and
[`docs/demo/README.txt`](../docs/demo/README.txt) lists the environment it ran
in.

## What is verified live

Each item below links to the raw log from the run that produced it. All live
runs used local Ollama 0.31.1 models; no hosted provider was funded.

- The full loop closed one step only after `pytest` passed, on `qwen2.5:3b`
  ([`spike/ollama-qwen2.5-3b/reverify-2026-11-01/maxcode-run/run.jsonl`](../spike/ollama-qwen2.5-3b/reverify-2026-11-01/maxcode-run/run.jsonl))
  and on `llama3.2:3b` ([`spike/ollama-llama3.2-3b/maxcode-run/run.jsonl`](../spike/ollama-llama3.2-3b/maxcode-run/run.jsonl)).
- The engine created files on disk and emitted `turn.completed` usage on both
  models:
  [`spike/ollama-qwen2.5-3b/reverify-2026-11-01/hello-engine/stdout.jsonl`](../spike/ollama-qwen2.5-3b/reverify-2026-11-01/hello-engine/stdout.jsonl)
  and
  [`spike/ollama-llama3.2-3b/reverify-2026-11-01/hello-engine/stdout.jsonl`](../spike/ollama-llama3.2-3b/reverify-2026-11-01/hello-engine/stdout.jsonl).
- Stock Codex 0.165.0 and `maxcode-engine` emitted the same event types on the
  same task ([`spike/engine-comparison/reverify-2026-11-01/event-types.diff`](../spike/engine-comparison/reverify-2026-11-01/event-types.diff)).
- `qwen3:1.7b` is not a dependable worker: one success on 2026-10-31, then three
  failures on 2026-11-01
  ([`spike/ollama-qwen3-1.7b/reverify-2026-11-01/`](../spike/ollama-qwen3-1.7b/reverify-2026-11-01/)).

## What is mock-verified

- The provider client, the planner and worker prompts, check detection, git
  checkpoints, cost accounting, the loop state machine, and every CLI exit code
  are covered by tests that use fakes and temporary directories only. The run is
  in [`docs/release/2026-11-01-checks.txt`](2026-11-01-checks.txt): 166 passed,
  1 deselected, with ruff and mypy clean.
- The OpenAI-compatible request shape is tested against a mock transport
  ([`tests/test_provider.py`](../tests/test_provider.py), included in that run).
  No provider-specific wire shape was tested beyond the local endpoints.

## What is not verified

- Live runs on the hosted providers the project originally targeted. OpenRouter,
  Hugging Face, and DeepSeek had no credential in this environment and failed
  before a model call
  ([`spike/openrouter-qwen3-coder-next/codex-stderr.txt`](../spike/openrouter-qwen3-coder-next/codex-stderr.txt),
  [`spike/huggingface-qwen2.5-1.5b/codex-stderr.txt`](../spike/huggingface-qwen2.5-1.5b/codex-stderr.txt),
  [`spike/deepseek-deepseek-chat/codex-stderr.txt`](../spike/deepseek-deepseek-chat/codex-stderr.txt)).
- Any benchmark advantage. The one published run scores 3/3 in both arms, a
  0.0-point gain, with the verifier-on arm timing out before verification
  ([`docs/bench/2026-10-31/report.txt`](../docs/bench/2026-10-31/report.txt)).
- A full-suite benchmark with a reliable planner. The 2026-11-01 probe run is
  blocked; every planner probe and its exit code is in
  [`docs/bench/2026-11-01/planner-probes/`](../docs/bench/2026-11-01/planner-probes/).

## Known limits

- The engine must be Codex 0.165.0 or newer, or `maxcode-engine`. On this
  machine the installed `maxcode-engine` reports 0.163.0, which `maxcode doctor`
  rejects; the demo recording used stock Codex 0.165.0 from a temporary prefix.
- Ollama 0.31.1 rejects a thinking request for `qwen2.5:3b`, so runs set
  `MAXCODE_REASONING_EFFORT=none`. The README demo and the live logs do this.
- Stock Codex cannot create its sandbox helper when its home directory is under
  `/tmp`, and a repository under `/tmp` is discouraged for the same reason. The
  failed comparison run is kept in
  [`spike/engine-comparison/reverify-2026-11-01/stock-codex-tmp-home-failure/`](../spike/engine-comparison/reverify-2026-11-01/stock-codex-tmp-home-failure/).
- Small local workers choose tools unreliably. The recorded demo prompt names
  the edit command for that reason: it shows the loop's plumbing, not the
  model's ability to find a fix.
- Cost is reported as `partial` when the config has no pricing entry for a
  model. The demo run shows `$0.0000` with that notice
  ([`docs/demo/run.jsonl`](../docs/demo/run.jsonl)).

## Install

From a checkout:

```bash
git clone https://github.com/RavaniRoshan/maxcode.git
cd maxcode
uv sync
uv run maxcode --help
```

These commands were run on a clean clone on 2026-11-01; the output is in
[`docs/release/2026-11-01-clean-clone.txt`](2026-11-01-clean-clone.txt).

Then install an engine (stock `@openai/codex` 0.165.0 or newer) and write a
`maxcode.toml`. The README's Configure and Demo sections are the working
reference.

## Benchmark

The harness ships with the repository; the results, failures, and the reason
the published run shows no advantage are in [`docs/BENCH.md`](../docs/BENCH.md).
