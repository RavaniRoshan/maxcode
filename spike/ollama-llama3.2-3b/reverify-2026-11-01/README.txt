Re-verification: llama3.2:3b on Ollama 0.31.1
Date: 2026-11-01
Engine: maxcode-engine 0.1.0 (dev-small build from Codex rust-v0.165.0)

hello-engine/ is the exact SPIKE.md section 2 command on the hello.txt task.
Result: exit 0, 4 command_execution items, turn.completed usage
2748 input / 379 output tokens, hello.txt contains "hello".
See hello-engine/command.txt, stdout.jsonl, stderr.txt, exit-code.txt.

The same model was not reliable in two stock-Codex attempts on the same day:
one run produced no tool call and one produced a malformed function call.
Those failures are recorded under
spike/engine-comparison/reverify-2026-11-01/.
