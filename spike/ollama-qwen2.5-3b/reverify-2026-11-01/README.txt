Re-verification: qwen2.5:3b on Ollama 0.31.1
Date: 2026-11-01
Engine: maxcode-engine 0.1.0 (dev-small build from Codex rust-v0.165.0)
Provider: http://127.0.0.1:11434/v1, Responses API
Environment names only (no credentials):
  OLLAMA_API_KEY=<placeholder>
  MAXCODE_HOME=<temporary directory>
  MAXCODE_REASONING_EFFORT=none
  MAXCODE_MODEL_CONTEXT_WINDOW=16384

hello-engine/
  The exact command from SPIKE.md section 2, on the hello.txt task.
  Result: exit 0, 4 command_execution items, turn.completed usage
  8663 input / 215 output tokens, hello.txt contains "hello".

maxcode-run/
  Full maxcode run: planner gpt-oss-20b through Pollinations (anonymous),
  worker qwen2.5:3b through maxcode-engine, check `python3 -m pytest -q`.
  Result: exit 0, steps 1/1, test passed (1 passed), app.py changed from
  `return a - b` to `return a + b`, 7393 input / 1293 output tokens.
  The run log shows the planner put the sed edit in a `cmd:` check, so the
  approved check performed the edit and the worker call was short. The
  separate hello-engine run proves the worker edit path.
