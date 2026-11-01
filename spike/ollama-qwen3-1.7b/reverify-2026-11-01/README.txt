Re-verification: qwen3:1.7b on Ollama 0.31.1 — FAILED
Date: 2026-11-01
Engine: maxcode-engine 0.1.0 (dev-small build from Codex rust-v0.165.0)
Command: the exact SPIKE.md section 2 command, same hello.txt task.
Three attempts, each in a fresh repository and a fresh MAXCODE_HOME.

attempt1: exit 0, zero command_execution events, hello.txt absent.
  The model asked for approval that a non-interactive "Never" policy
  cannot grant. stderr records the rejected escalated command.
attempt2: exit 0, one `cat hello.txt` command that failed because the file
  did not exist yet; the model then stopped and suggested `touch`.
attempt3: exit 0, zero command_execution events, same approval message.

This model completed the task on 2026-10-31 (see the parent directory's
hello-engine/ and maxcode-run/ logs). On 2026-11-01 it did not reproduce
3 out of 3 times. Treat it as unstable, not as a dependable worker.
