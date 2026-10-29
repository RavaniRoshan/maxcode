# maxcode

maxcode is an open-source terminal coding agent. It plans a task, edits code,
and marks the task done only after an independent set of checks passes.

* **Planner** turns one task into small, ordered steps.
* **Worker** edits files for one step at a time.
* **Verifier** runs tests, builds, and lint commands. It ignores what the worker
  says and decides pass or fail from real command output.

Every step starts from a git checkpoint, every run writes a JSONL log, and every
run reports token use and cost. `undo` restores the last checkpoint.

Status: version 0.1 is in development. The install and demo sections below are
filled in by task T17; the architecture is documented in `PRD.md`.

## Requirements

* Python 3.12
* [uv](https://docs.astral.sh/uv/)
* git
* An OpenAI-compatible provider and an API key in an environment variable

## Development

```bash
uv sync
uv run pytest -m "not slow"
uv run ruff check .
uv run mypy src
```

## License

Apache-2.0. See `LICENSE` and `NOTICE`. maxcode is an independent project and
is not affiliated with OpenAI or Sarvam AI.
