Both binaries ran the same task, model (Ollama qwen3:1.7b), and provider settings:
  "Create a file named hello.txt containing exactly the text hello and nothing else.
   Run cat hello.txt and confirm the output is hello. Only change hello.txt."

stock-codex-0.165: /tmp/codex0165/node_modules/.bin/codex (npm @openai/codex 0.165.0), CODEX_HOME temp.
maxcode-engine-0.1.0: maxcode-engine dev-small (Codex rust-v0.165.0 + rebrand), MAXCODE_HOME temp.

Both exited 0, created hello.txt with "hello", and emitted the same event types
(see event-types.diff; the only difference is an extra failed `nano` command in
the stock run, a model choice, not a schema difference). Both emitted
turn.completed usage.
