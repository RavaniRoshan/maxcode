# maxcode — alpha launch post

An open-source coding CLI whose "done" is decided by your tests, not by the model. Alpha.

maxcode splits a task into steps, lets an engine process edit the repository,
and then runs the checks your project already uses: `pytest`, `npm test`,
`cargo test`, `go test`, `ruff`, `mypy`, or a command you configure. A step
closes only when every check exits 0. A failed check goes back to the worker,
and when the retries run out the run stops at the git checkpoint it saved
before the step. `maxcode undo` restores it.

Every run writes a JSONL log with check exit codes, token counts, and cost, so a
"done" claim can be read instead of trusted.

Try it from a checkout:

```bash
git clone https://github.com/RavaniRoshan/maxcode.git
cd maxcode
uv sync
uv run maxcode --help
```

What is unproven: the one published benchmark shows a 0-point gain between
verifier-on and verifier-off, and the live runs so far use local Ollama models.

Repo: https://github.com/RavaniRoshan/maxcode
