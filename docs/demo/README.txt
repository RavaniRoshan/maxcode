Recording of the README demo, 2026-11-01.

- `demo.cast` — asciinema 2.4.0 recording, unedited.
- `demo.txt` — the same bytes rendered as text: escape sequences removed and
  cursor moves applied, no content changed.
- `run.jsonl` — the run log maxcode wrote during the recording.
- `app.py.after` — `app.py` when the run finished.

Environment used for the recording:

- command: the `maxcode run` line from the README demo
- engine: stock `@openai/codex` 0.165.0 installed in a temporary prefix and
  selected with `MAXCODE_ENGINE_BIN`
- `CODEX_HOME`: a temporary directory outside `/tmp`
- worker: Ollama 0.31.1, `qwen2.5:3b`
- planner: Pollinations AI, `gpt-oss-20b`
- `MAXCODE_REASONING_EFFORT=none`, `MAXCODE_MODEL_CONTEXT_WINDOW=16384`
- `POLLINATIONS_KEY` and `OLLAMA_API_KEY` held placeholder values; no key is in
  this directory.

Result: exit 0, steps 1/1, check `cmd:python3 -m pytest -q` passed
(`1 passed in 0.00s`), `run_end.passed=true`, `diff_lines=2`,
7442 input / 754 output tokens, cost `0.0000` (partial: the config has no
pricing entry).
