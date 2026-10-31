# SPIKE: Phase 0

Status: **complete, live-verified on a local open-weight model.** On 2026-10-31,
`maxcode-engine` completed multi-turn tool-calling tasks against Ollama 0.31.1
with `qwen3:1.7b` and `llama3.2:3b`, emitted `turn.completed` usage, and created
the requested files on disk. The full `maxcode run` loop also passed its
verifier with both models. The two originally planned OpenRouter models remain unverified because
no funded key exists in this environment; their exact failure is in section 5.

- Date of live runs: 2026-10-31
- Engine: `maxcode-engine` 0.1.0, built from Codex `rust-v0.165.0` (commit `360319d`)
- Stock comparison: `@openai/codex` 0.165.0 from npm, run in a temporary prefix
- Local provider: Ollama 0.31.1 at `http://127.0.0.1:11434/v1`
- Raw evidence: [`spike/`](spike/)

## 1. Wrapper or fork

Decision: **fork is available, but it is not required.** The engine adapter now
selects, in order:

1. `MAXCODE_ENGINE_BIN`, when set.
2. `maxcode-engine` on `PATH`.
3. `codex` on `PATH`, when its `--version` is 0.165.0 or newer.

Stock Codex 0.165.0 accepts a custom OpenAI-compatible provider through
`model_providers.<id>` with `wire_api = "responses"`. Stock Codex and
`maxcode-engine` produced the same event types on the same live task (section 8).
The fork remains useful only if a future Codex change blocks a provider we need,
or if we need to patch the engine itself.

Codex source paths:

- `maxcode-rs/config/src/config_toml.rs`: `model_provider` and `model_providers`.
- `maxcode-rs/core/src/config/mod.rs`: merges built-in providers with configured
  providers, then selects `model_provider_id`.
- `maxcode-rs/model-provider-info/src/lib.rs`: `ModelProviderInfo` fields,
  `api_key()` reads the environment variable, and `to_api_provider()` builds the
  HTTP provider. This file also lists `ollama` as a reserved built-in provider ID.

OpenRouter's own `Ori` harness ships a Codex launcher with the same provider
shape. That is evidence that stock Codex plus a custom Responses provider is a
supported combination. Our runner uses `env_key` instead of `auth.command`; both
are supported by the Codex source, and `env_key` avoids spawning a shell to print
a secret.

The compatibility risk is real and version-specific:

- Codex `v0.165.0` removed `wire_api = "chat"`. Only the Responses API is supported.
  Source: `model-provider-info/src/lib.rs`, `CHAT_WIRE_API_REMOVED_ERROR`.
- `ollama` is a reserved built-in provider ID. A custom entry named `ollama` fails
  at config load. Use another id, for example `ollama-local`.
- Ollama 0.31.1 rejects `reasoning.effort = "minimal"` and accepts
  `none`, `low`, `medium`, `high`, or `max`.
- Ollama 0.31.1 loses function names when the Codex request contains a
  `type: "namespace"` tool (`multi_agent_v1`) or a `type: "web_search"` tool.
  The engine then logs `unsupported call:`. Disabling both tools fixes it.
  Evidence: `spike/ollama-qwen3-1.7b/streaming-name-bug.txt`.
- Ollama 0.31.1 drops some function calls when the model spends its streamed
  output budget on long reasoning. Setting `model_reasoning_effort = "none"`
  avoids that path and produced stable tool calls.
- The Responses API is stateless. Codex sends `store: false`, which matches it.
- OpenRouter requires `id` and `status` on assistant messages in later turns.
  Codex includes them when the provider supplies them; the local Ollama run
  round-tripped the conversation without that requirement.

## 2. Exact non-interactive command and flags

The live command is `exec --json`, using the custom-provider shape from the
original spike plus the Ollama compatibility overrides:

```bash
MAXCODE_HOME="$RUN_DIR/maxcode-home" \
  "$ENGINE_BIN" exec \
  --json \
  --skip-git-repo-check \
  -C "$REPO" \
  -s workspace-write \
  -m "$MODEL" \
  -c model_provider=ollama-local \
  -c 'model_providers.ollama-local.name="Ollama local"' \
  -c 'model_providers.ollama-local.base_url="http://127.0.0.1:11434/v1"' \
  -c 'model_providers.ollama-local.env_key="OLLAMA_API_KEY"' \
  -c 'model_providers.ollama-local.wire_api="responses"' \
  -c "model_context_window=$CONTEXT" \
  -c 'model_reasoning_effort="none"' \
  -c 'web_search="disabled"' \
  -c agents.enabled=false \
  "$PROMPT"
```

Flag sources (confirmed from `exec --help` and the source):

- `maxcode-rs/exec/src/cli.rs`: `--json`, `--skip-git-repo-check`, `-C`, `-s`,
  `-m`, `-c`.
- `maxcode-rs/utils/cli/src/shared_options.rs`: `-C`, `-s`, `-m`, `-c`.
- `maxcode-rs/utils/cli/src/config_override.rs`: `-c key=value`; the value is
  parsed as TOML, with a raw-string fallback.
- `maxcode-rs/config/src/config_toml.rs`: `web_search`, `agents.enabled`.
- `maxcode-rs/core/src/client.rs`: `model_reasoning_effort`; `stream` is always
  true for the Responses API.

`--oss --local-provider ollama` also exists in `exec --help`, but the live
evidence here uses the explicit custom-provider shape above. The built-in path
uses the same Responses wire API and therefore has the same Ollama limitations.

When the engine adapter calls Codex from Python it sets `stdin=subprocess.DEVNULL`.
Without that, Codex prints `Reading additional input from stdin...` and waits for
input when the parent process is not a TTY. That line still appears on stderr in
some runs, but the process does not block.

## 3. Does Codex report token counts?

Yes, confirmed live.

`exec --json` emits a `turn.completed` event. Its `usage` object contains:

- `input_tokens`
- `cached_input_tokens`
- `cache_write_input_tokens`
- `output_tokens`
- `reasoning_output_tokens`

Source: `codex-rs/exec/src/exec_events.rs`, `TurnCompletedEvent` and `Usage`.

Live values from `spike/ollama-qwen3-1.7b/hello-engine/stdout.jsonl`:

```text
{"type":"turn.completed","usage":{"input_tokens":8204,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":202,"reasoning_output_tokens":0}}
```

The full `maxcode run` log records `tokens_in: 7152`, `tokens_out: 1264`, and
`cost_usd: 0.0000` with `partial` cost reporting, because the config has no
`[pricing]` entry for the local model. The token counts are real; the dollar
amount is not an API bill.

## 4. How to pass the provider URL and key

- Provider URL: `model_providers.<id>.base_url = "http://127.0.0.1:11434/v1"`.
- Key: `model_providers.<id>.env_key = "OLLAMA_API_KEY"`. Codex reads the
  variable from the child process environment at request time. The key never
  enters a config file, the repository, or the run log. Ollama ignores the value,
  so the live runs used the placeholder `local`.
- Wire API: `model_providers.<id>.wire_api = "responses"`. `chat` is a hard error
  in Codex 0.165.
- Auth: `requires_openai_auth` defaults to `false`, so no ChatGPT login is needed.
- Config location: project `.codex/config.toml` is not allowed to override
  `model_provider` or `model_providers`. The adapter uses CLI `-c` overrides and
  a dedicated `MAXCODE_HOME`.
- Context: `model_context_window=16384` matches the small local models used here.
  The adapter reads `MAXCODE_MODEL_CONTEXT_WINDOW` and omits the override when
  the variable is unset.
- Reasoning: the adapter defaults to `low` and reads `MAXCODE_REASONING_EFFORT`.
  The live runs set `none`.

## 5. Live provider attempt matrix (2026-10-31)

| Provider | Model | Endpoint | Result | Evidence |
|---|---|---|---|---|
| OpenRouter | `qwen/qwen3-coder-next` | `https://openrouter.ai/api/v1` | No credential in env; engine exits 1 with `Missing environment variable: OPENROUTER_API_KEY`. Unauthenticated HTTP probe: 401 `No cookie auth credentials found`. | `spike/openrouter-qwen3-coder-next/` |
| Hugging Face Router | `Qwen/Qwen2.5-1.5B-Instruct` | `https://router.huggingface.co/v1` | No credential in env; engine exits 1 with `Missing environment variable: HF_TOKEN`. Unauthenticated HTTP probe: 401 (HTML login page). | `spike/huggingface-qwen2.5-1.5b/` |
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com/v1` | No credential in env; engine exits 1 with `Missing environment variable: DEEPSEEK_API_KEY`. Unauthenticated HTTP probe: 401 `Authentication Fails (governor)`. | `spike/deepseek-deepseek-chat/` |
| Pollinations AI | `gpt-oss-20b` (`openai`) | `https://text.pollinations.ai/openai` | Chat Completions works anonymously (HTTP 200). Its `/v1/responses` path returns a chat-completion body, and `/v1/responses` returns 404, so it cannot serve Codex 0.165. Anonymous tier: one reply per 45 s. | `spike/pollinations-gpt-oss-20b/` |
| Ollama 0.31.1 | `qwen3:1.7b` | `http://127.0.0.1:11434/v1` | **Success.** Multi-turn tool calls, `turn.completed` usage, `hello.txt` created, full loop passed. | `spike/ollama-qwen3-1.7b/` |
| Ollama 0.31.1 | `llama3.2:3b` | `http://127.0.0.1:11434/v1` | **Success.** Multi-turn tool calls, `turn.completed` usage, `hello.txt` created, full loop passed. | `spike/ollama-llama3.2-3b/` |
| Ollama 0.31.1 | `qwen2.5-coder:1.5b` | `http://127.0.0.1:11434/v1` | Model does not emit structured tool calls; it returns the call as text. Not usable as a worker. | `spike/ollama-qwen2.5-coder-1.5b/` |

The earlier OpenRouter HTTP 402 (`insufficient credits`) is retained in the
history below. It cannot be re-run without the original key, and no key is
present in this environment.

## Run log: model 1 (success)

Model: `qwen3:1.7b` (open weights) via Ollama 0.31.1.

Raw engine task:

```text
Create a file named hello.txt containing exactly the text hello and nothing else.
Run cat hello.txt and confirm the output is hello. Only change hello.txt.
```

Result (`spike/ollama-qwen3-1.7b/hello-engine/`):

- exit code 0
- two `command_execution` items: `echo hello > hello.txt` and `cat hello.txt`
- `turn.completed` usage: 8204 input tokens, 202 output tokens
- `hello.txt` exists on disk and contains `hello`
- event sequence: `thread.started`, `turn.started`, `command_execution` x2,
  `agent_message`, `turn.completed`

Full loop (`spike/ollama-qwen3-1.7b/maxcode-run/`):

- planner: Pollinations `gpt-oss-20b` (Chat Completions)
- worker: `qwen3:1.7b` through `maxcode-engine`
- verifier: `python -m pytest -q`
- command: `maxcode run --yes --config maxcode-live.toml "Edit app.py so add(a, b)
  returns a + b ..."`
- result: exit 0, `steps: 1/1`, check `test` passed (`1 passed in 0.01s`),
  `run_end.passed = true`, `app.py` changed from `return a - b` to `return a + b`
- tokens: 7152 input, 1264 output; dollar cost `0.0000` (no pricing entry,
  reported as partial)

## Run log: model 2 (success)

Model: `llama3.2:3b` (open weights) via Ollama 0.31.1.

Raw engine task: the same `hello.txt` task as model 1. Result
(`spike/ollama-llama3.2-3b/hello-engine/`):

- exit code 0
- three `command_execution` items, including `echo hello > hello.txt` and
  `cat hello.txt`
- `turn.completed` usage: 2625 input tokens, 309 output tokens
- `hello.txt` exists on disk and contains `hello`

Full loop (`spike/ollama-llama3.2-3b/maxcode-run/`):

- planner: Pollinations `gpt-oss-20b`
- worker: `llama3.2:3b` through `maxcode-engine`
- verifier: `python -m pytest -q`
- result: exit 0, `steps: 1/1`, check `test` passed, `run_end.passed = true`,
  `app.py` changed from `return a - b` to `return a + b`
- tokens: 7182 input, 1067 output; dollar cost `0.0000` (partial)

## Run log: model 3 (tool-call failure)

Model: `qwen2.5-coder:1.5b` (open weights) via Ollama 0.31.1.

The model returned a normal assistant message whose text was a JSON snippet
(`{"name": "run_command", "arguments": ...}`), not a `function_call` item. The
native `/api/chat` tool probe behaved the same way: no `message.tool_calls`.
Evidence: `spike/ollama-qwen2.5-coder-1.5b/responses-tool-probe.json` and
`native-chat-tool-probe.json`.

Conclusion: the model is not usable as a maxcode worker in this Ollama build.
The failure is the model, not the wire format: `qwen3:1.7b` emitted proper
`function_call` items through the same endpoint.

## Engine comparison: stock Codex 0.165 vs maxcode-engine 0.1.0

Same task, same model, same provider settings:

- Stock: `@openai/codex` 0.165.0 from npm, `CODEX_HOME` in a temp directory.
- Fork: `maxcode-engine` 0.1.0, `MAXCODE_HOME` in a temp directory.

Both exited 0, created `hello.txt` containing `hello`, and emitted
`turn.completed`. The event-type sequences are identical
(`spike/engine-comparison/event-types.diff`); the only difference was an extra
failed `nano hello.txt` command in the stock run, which is a model choice, not a
schema difference.

| Binary | Input tokens | Output tokens | File created |
|---|---:|---:|---|
| stock Codex 0.165.0 | 10491 | 182 | yes |
| maxcode-engine 0.1.0 | 8204 | 202 | yes |

The adapter's unit tests cover all three selection paths:
`MAXCODE_ENGINE_BIN`, `maxcode-engine` on `PATH`, and `codex` 0.165+ on `PATH`.
A `codex` older than 0.165 is rejected with an actionable error.

## Assumption A1: GitHub search

Searches run on 2026-10-29:

| Query | GitHub result count | Main finding |
|---|---:|---|
| `verifier coding agent` | 5,539 | Top results are a security-audit skill, observability tools, challenge courses, and an LLM-as-verifier framework. None is a mainstream coding CLI with a pass/fail gate as its core product. |
| `coding agent verifier loop` | 550 | Harness books, long-horizon harnesses, and workflow frameworks. Not a coding CLI product. |
| `code agent test gate` | 562 | Skills and quality-gate add-ons for existing agents. Not a core gate. |
| `autonomous coding agent tests pass` | 34 | Small prototypes, not widely used tools. |

A web search also found:

- Aider's internal verify-fix loop. It is a feature of the agent, not an
  independent pass/fail gate that owns task completion.
- A pydantic-ai feature request for a `VerificationLoop` capability.
- `verifier-gate`, a small project that only ships what a program verifies.
- An article describing an OpenCode + CI verification gate pattern.

Conclusion: A1 holds for mainstream open coding CLIs. The idea exists in
components and small projects, so the public claim must be precise: **no widely
used open coding CLI makes an independent pass/fail gate its core product**.
The benchmark should test the claimed advantage, not absolute novelty.

## Blockers

- The originally supplied OpenRouter key returned HTTP 402 (insufficient
  credits), and free model slugs returned HTTP 404. No funded OpenRouter,
  Hugging Face, or DeepSeek credential is present in this environment.
- Live runs on `qwen/qwen3-coder-next` and `deepseek/deepseek-v3.2` therefore
  remain unverified. The local Ollama runs in this file are the substitute
  evidence, and they use open-weight models.
- Ollama 0.31.1's streaming Responses implementation is not fully compatible
  with Codex when non-function tools or long reasoning are present. The working
  configuration is documented in sections 1 and 2. A production adapter for
  Ollama should keep those overrides.

## T0 completion note

T0's exit rule was "one task completes on a non-OpenAI model". That is now met:
`qwen3:1.7b` completed a coding task through `maxcode-engine`, and the full
`maxcode run` loop closed a step only after `pytest` passed. The run was local,
free of API charges, and used temp directories only. No key was written to a
file, log, checkpoint, or commit.
