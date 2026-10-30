# maxcode

maxcode is an open-source coding CLI. It plans a task, edits code with the maxcode engine, and marks the task done only after checks pass.

## Commands
- Install: `uv sync`
- Test: `uv run pytest -m "not slow"`
- Lint: `uv run ruff check . && uv run mypy src`
- Run: `uv run maxcode --help`

## Rules
- Read the PRD before you start. The PRD is the source of truth.
- Work on one task at a time. Write the failing test first.
- Commit after each task: `T<number>: <summary>`.
- Never invent an engine CLI flag. Read it from the engine source or help output.
- Never copy text, assets, or code from Sarvam. Never inspect a Sarvam binary.
- Never remove LICENSE or NOTICE.
- Never weaken or delete a test to make it pass.
- Never store an API key in a file.
- Keep functions under 40 lines and files under 400 lines.
- Ask the user when the PRD does not decide something.

## Layout
See the repository layout in the PRD, section 20.
