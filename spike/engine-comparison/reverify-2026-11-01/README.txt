Engine comparison re-verification: stock Codex 0.165.0 vs maxcode-engine 0.1.0
Date: 2026-11-01
Model: qwen2.5:3b on Ollama 0.31.1
Task: the exact SPIKE.md section 2 hello.txt task.
Provider settings: identical custom Responses provider in both runs.

Binaries:
  stock:  /tmp/codex0165/node_modules/.bin/codex (npm @openai/codex 0.165.0),
          CODEX_HOME outside /tmp (see the /tmp failure note below).
  fork:   maxcode-engine 0.1.0, dev-small build from Codex rust-v0.165.0,
          MAXCODE_HOME in a temporary directory.

Repeated trials, fresh repository and home per trial:
  stock Codex 0.165.0: 3/3 exit 0, hello.txt created.
  maxcode-engine 0.1.0: 2/2 exit 0, hello.txt created.
  Both also emitted turn.completed with usage.

Representative logs:
  stock-codex-0.165-qwen2.5-3b/  (4 command_execution events, 4140 in / 189 out
  in the first attempt; the representative stock-1 trial is 4 events)
  maxcode-engine-0.1.0-qwen2.5-3b/ (2 command_execution events, 8663 in / 215 out)
  event-types.diff shows the only difference is the number of
  command_execution items. The event vocabulary and order are identical;
  the model chose a different number of shell commands.

Notes and failures:
- A stock Codex run with CODEX_HOME under /tmp could not spawn
  codex-linux-sandbox: Codex refuses to create helper binaries under a
  temporary directory. The run exited 0 but executed no commands.
  See stock-codex-tmp-home-failure/.
- The first stock qwen2.5:3b attempt failed with
  "failed to parse function arguments: invalid type: null, expected u64";
  repeated trials succeeded, so this was model sampling, not a schema
  difference between the binaries.
- Two stock llama3.2:3b attempts also failed (one emitted no tool call, one
  emitted malformed arguments). The fork completed the same llama task once
  on 2026-11-01. Small-model tool calling is not deterministic.
- The globally installed `codex` on this machine is 0.163.0, below the
  adapter's 0.165 minimum. The comparison therefore used the pinned npm
  package in /tmp/codex0165.
