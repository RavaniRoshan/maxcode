# Verifier-on smoke run, 2026-11-01

One task, `task-101`, with the verifier on. Planner: Ollama `llama3.2:3b`.
Worker: Ollama `qwen2.5:3b`. Engine: `maxcode-engine`. The task's baseline
score fails (exit 1) in both runs; the hidden score fails after the worker.

## Run 600s: `run-600s/`

`results.csv` records `baseline_status=failed`, `status=error`, and
`score_passed=False`. `run.jsonl` records:

- `plan` with checks `test` and `cmd:check tests/test_discounts.py`.
- `check_result` for `test`: `passed=false`, the visible assertion
  `assert 200.0 == 190.0`.
- `check_result` for `cmd:check tests/test_discounts.py`: exit 127,
  `/bin/sh: 1: check: not found`.
- `retry` with `attempt=2`.
- a second `worker_call` with `seconds=600.0753217930005`, null tokens.
- `run_end` with `passed=false`.

The second worker call reached the configured `worker_timeout_s = 600` and was
recorded as `status=error`. This run did not point `MAXCODE_HOME`/`CODEX_HOME`
at a temporary directory, so its engine sessions are not in this log.

## Session capture: `session-capture/`

This run uses `maxcode-90s.toml`; the only difference from `maxcode.toml` is
`worker_timeout_s = 90`. `results.csv` records `baseline_status=failed`,
`status=fail`, and `score_passed=False`. `run.jsonl` records:

- the same plan shape, with `test` and a different planner-invented
  `cmd:run tests with --failfast` check (`/bin/sh: 1: run: not found`).
- first `check_result` for `test`: `passed=false`, the same visible assertion
  `assert 200.0 == 190.0`.
- `retry` with `attempt=2`.
- second `worker_call`: `seconds=33.82011793699985`, `input_tokens=28385`,
  `output_tokens=1911`.
- second `check_result` for `test`: `passed=false`, the same visible assertion.
- `run_end` with `passed=false`. The retry limit ended the run.

`engine-session-attempt-1.jsonl` is the first worker prompt. It has no failure
block. `engine-session-attempt-2.jsonl` is the second worker prompt. Its user
message contains:

```text
The last attempt failed these checks. Fix the cause.
test: F. ... assert 200.0 == 190.0 ...
```

This is the direct confirmation that the verifier ran, recorded a failing
check, and the worker received the failure output on the retry. The second
worker attempt did not fix the bug; the final status is `fail`, not `error`.

## Planner attempts: `planner-attempts/`

- `qwen2.5-3b-plan.txt` and `qwen2.5-coder-1.5b-plan.txt`: planner schema
  failures.
- `qwen2.5-coder-1.5b-raw.txt`: the raw plan; `goal` was a list, not a string.
- `llama3.2-3b-plan.txt` and `llama3.2-3b-raw.txt`: valid plans.
- `bench-run-1/`: the first bench run, which stopped at the planner with
  `status=error` before the worker ran.

The smoke confirms the verifier/retry plumbing. It does not show a verifier
advantage: the 600s run timed out on retry and the 90s run hit the retry limit.
`docs/BENCH.md` and the 2026-10-31 result are unchanged.
