Re-verification: qwen3:4b on Ollama 0.31.1 — FAILED
Date: 2026-11-01
Engine: maxcode-engine 0.1.0 (Codex rust-v0.165.0)
Command: the exact SPIKE.md section 2 command, same hello.txt task.

Result: exit 0, zero command_execution events, hello.txt absent.
The model spent its whole output budget (3025 tokens) on visible reasoning
and printed a text tool call instead of emitting a function_call item.
It is not usable as a maxcode worker in this Ollama build.
