# Benchmark: verifier on vs off

**The absolute gain in this run is 0 percentage points: both arms scored 3/3
(100%) on the final score command.** The verifier-on arm did not reach its
verification step in any task because the local worker hit the 300-second engine
timeout; the repositories were unchanged, so the same final score still passed.
This run therefore does not show a verifier advantage. It measures a ceiling:
the pinned repositories already pass their own tests, and the worker made no
changes.

- Date: 2026-10-31
- Suite: 3 tasks from the default 20-run suite (one each from
  `pallets/click`, `pallets/itsdangerous`, `pallets/markupsafe`)
- Planner: `qwen2.5-coder:1.5b` through Ollama 0.31.1
- Worker: `qwen3:1.7b` through Ollama 0.31.1
- Engine: `maxcode-engine` 0.1.0 (Codex `rust-v0.165.0`)
- Raw logs: [`docs/bench/2026-10-31/`](bench/2026-10-31/)
- Report: [`docs/bench/2026-10-31/report.txt`](bench/2026-10-31/report.txt)

## Method

Both arms clone the same pinned commit for each task, run `maxcode` with
`RunOptions(yes=True, verifier=on|off)`, and then run the task's `score` command
outside the loop. The score command is the same string in both arms:

| Task | Repository | Commit | Score command |
|---|---|---|---|
| task-001 | pallets/click | `2247b35ea1c47c727d7a06e51fa280e12a863ff6` | `python -m pytest tests/test_basic.py -q` |
| task-002 | pallets/itsdangerous | `672971d66a2ef9f85151e53283113f33d642dabd` | `python -m pytest tests/ -q` |
| task-003 | pallets/markupsafe | `4e111271b1494995708a9e878a10829b5e10c7ba` | `python -m pytest tests/ -q` |

N = 3 per arm.

**The score command is not passed to the worker.** `run_bench` passes only
`task["task"]` to `run_task`; `_run_score` runs the separate `score` field after
the loop (`src/maxcode/bench/runner.py`, `run_bench`). The engine session logs
for the runs contain the task text but not the score string. The score commands
for task-001/task-002 do not appear in
`docs/bench/2026-10-31/verifier-off/task-*/engine-session.jsonl`.

The pinned repositories use a `src/` layout. The bench runner now adds
`<repo>/src` to `PYTHONPATH` for the run and the score command; without that,
`pytest` cannot import the repository under test. This behavior is covered by
`tests/test_bench.py::test_repo_pythonpath_adds_and_restores_src`.

The benchmark used an isolated virtualenv with `pytest`, `pytest-httpbin`,
`pytest-mock`, `trustme`, `freezegun`, `ruff`, `urllib3`, `certifi`,
`charset_normalizer`, `idna`, and `cryptography`. The worker environment set
`MAXCODE_REASONING_EFFORT=none` and `MAXCODE_MODEL_CONTEXT_WINDOW=16384`, the
settings that make the Ollama Responses API usable with Codex 0.165.

## Results

| Verifier | Tasks | Score passes | Score pass rate | Run passes | Tokens in | Tokens out | API cost | Unverified |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| on | 3 | 3 | 100.0% | 0 | 5,613 | 580 | $0.0000 | 0 |
| off | 3 | 3 | 100.0% | 3 | 125,320 | 3,918 | $0.0000 | 0 |

Absolute gain: **0.0 percentage points**.

The `on` arm's `run_passed` is false for all three tasks: task-001 and task-002
record a `worker_call` with `seconds = 300.0` and null token counts, then stop;
task-003 has no `worker_call`. No `check_result` event was written in that arm.
The final score still passed because the worker left the repositories unchanged.

The `off` arm's steps are marked passed without running checks, by design
(`loop.py`, `options.verifier` false). The worker reported `diff_lines: 0` for
every step, so the score command ran against an unchanged repository.

Cost per completed task is `$0.0000` in both arms: the run is local Ollama, with
no API charge, and the configuration has no `[pricing]` entry, so maxcode marks
the cost report `partial`. Tokens are the meaningful cost here: 2,064
input+output tokens per task on, 43,079 per task off. The off arm used more
tokens because its worker turns ran to completion instead of hitting the
timeout.

## Failures and exclusions

- **Verifier-on worker timeout.** All three on-arm worker calls reached the
  300-second `do_step` timeout (or failed before a call). The verifier never ran.
  This is the main reason the on arm cannot support a gain claim.
- **No diffs.** The worker produced no edits in either arm. The benchmark tasks
  ask "Ensure the project's test suite passes" on repositories that already pass,
  so there is nothing for the verifier to catch.
- **Planner quality.** A dry run with the same planner produced a three-step plan
  that invented unavailable linters (`pylama`, `flake8`, `black`, `isort`). The
  verifier correctly rejected those checks. The planner is a 1.5B model and is
  the weakest part of this setup. The successful live demo used a stronger
  planner (`gpt-oss-20b`) and an explicit edit instruction.
- **Requests excluded.** `psf/requests` at
  `3c7baaa05ab4aa49cc819ce3a819d260de19c157` fails 4 tests on a clean checkout in
  this environment (`TestTimeout::test_connect_timeout` and
  `TestTimeout::test_total_timeout_connect`, two cases each). Its score command
  cannot pass regardless of the model, so it is not a valid verifier task and is
  excluded from N. It was not silently counted as a pass or a fail.
- **No funded providers.** OpenRouter, Hugging Face, and DeepSeek have no
  credential in this environment. Their exact errors are in `SPIKE.md` and
  `spike/`.

## Reproduce

```bash
# Prerequisites: Ollama 0.31.1, the two models, stock Codex 0.165+ or maxcode-engine
ollama pull qwen2.5-coder:1.5b
ollama pull qwen3:1.7b

export OLLAMA_API_KEY=local
export MAXCODE_REASONING_EFFORT=none
export MAXCODE_MODEL_CONTEXT_WINDOW=16384

maxcode bench --verifier on  --suite docs/bench/2026-10-31/suite3
maxcode bench --verifier off --suite docs/bench/2026-10-31/suite3
uv run python -m maxcode.bench.report .maxcode/bench
```

The raw `results.csv`, per-task `run.jsonl`, and engine session transcripts are
in `docs/bench/2026-10-31/`. No number in this file comes from an uncommitted
run.

## What would change the result

- A task suite whose pinned commits fail before the worker starts, so the
  verifier has something to catch.
- A worker that reliably edits within the timeout, or a longer
  `do_step` timeout for local CPU models.
- A planner that uses only available checks (`test`, `build`, `lint`) instead of
  inventing tools.
- A funded hosted provider, so the same suite can run on the original OpenRouter
  models.
