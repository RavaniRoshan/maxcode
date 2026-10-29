# Contributing to maxcode

Thanks for helping. This repository follows the product requirement document in
`PRD.md`; it is the source of truth.

## Development setup

```bash
uv sync
uv run pytest -m "not slow"
uv run ruff check .
uv run mypy src
```

## Rules

* Work on one task at a time and write the failing test first.
* Keep functions under 40 lines and files under 400 lines.
* Add a type hint to every function.
* Write each error message in three parts: what failed, why, and what to do next.
* Never store an API key in a file, a test fixture, or a log.
* Never weaken or delete a test to make it pass.
* Do not copy text, assets, or code from Sarvam AI, and do not inspect a Sarvam
  binary.
* Keep `LICENSE` and `NOTICE` in the repository.

## Commits

Use `T<number>: <summary>` for build-task commits, for example
`T6: detect and run repository checks`.

## Pull requests

Run the lint, type, and test commands above. Describe the user-visible change
and the tests that prove it. Security issues go through `SECURITY.md`, not a
public issue.
