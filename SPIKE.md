# SPIKE: Phase 0

Status: Complete (wrapper decision; live runs skipped by user). Codex `v0.165.0` source build restarted in `/tmp/opencode/codex-src`.

- Date: 2026-10-29
- Codex tag: `rust-v0.165.0`
- Codex commit: `360319d`
- Task repository: `/tmp/opencode/t0/<model>/repo` (temporary; logs will be copied into `spike/`)

## 1. Wrapper or fork

Decision: **fork** (minimal). The wrapper approach was provisional; the project now ships a minimal fork named `maxcode-engine` built from Codex v0.165.0.

Codex supports user-defined OpenAI-compatible providers through `model_providers.<id>` in the user config, and the provider can be selected with `model_provider`. The provider entry supports `base_url`, `env_key`, and `wire_api`. No Codex source change is needed to point it at a custom URL.

Source path:

- `codex-rs/config/src/config_toml.rs`: `model_provider` and `model_providers` fields.
- `codex-rs/core/src/config/mod.rs`: merges built-in providers with configured providers, then selects `model_provider_id`.
- `codex-rs/model-provider-info/src/lib.rs`: `ModelProviderInfo` fields, `api_key()` reads the environment variable, and `to_api_provider()` builds the HTTP provider.

OpenRouter's own `Ori` harness already ships a Codex launcher with the same provider shape. The installed `ori` binary (v0.15.x) builds this command line for `ori codex`:

```text
-c model_provider=openrouter
-c model_providers.openrouter.name='OpenRouter'
-c model_providers.openrouter.base_url='https://openrouter.ai/api/v1'
-c model_providers.openrouter.wire_api='responses'
-c model_providers.openrouter.env_http_headers.X-Session-Id='ORI_OPENROUTER_SESSION_ID'
-c model_providers.openrouter.auth.command='sh'
-c model_providers.openrouter.auth.args=['-c','echo $OPENROUTER_API_KEY']
-m <model>
-c model_reasoning_effort=<effort>
```

That is confirmation from OpenRouter's own tooling that stock Codex plus OpenRouter's Responses API is a supported combination, and it uses the same `model_providers.openrouter` entry. Our runner uses `env_key` instead of an `auth.command`; both are supported by the Codex source, and `env_key` avoids spawning a shell to print the secret.

This is not final until both models complete a multi-turn tool-calling task. The compatibility risk is real:

- Codex `v0.165.0` removed `wire_api = "chat"`. Only the Responses API is supported.
- OpenRouter exposes a Responses API at `https://openrouter.ai/api/v1/responses`, and both chosen models advertise tool support.
- OpenRouter's Responses API is stateless. Codex sends `store: false`, which matches that requirement.
- OpenRouter requires `id` and `status` on assistant messages in later turns. Codex has optional `id`/`status` fields and may omit them. A live multi-turn run must prove this is accepted.

If the live test fails, the fallback order is:

1. Pin an older Codex tag that still supports Chat Completions, if one is compatible with the chosen models.
2. Fork Codex and add the provider/wire change. The first patch must stay under 500 changed lines.
3. Use a translation proxy only if the first two options fail.

### Wire-format dry run against a strict mock (2026-10-29)

The two live model runs are still blocked on the API key, so the wire format was tested against a local mock of the OpenRouter Responses API. The mock rejects `store` values other than `false` and rejects any assistant message replayed in a later turn that is missing `id` or `status`. It logs every request body.

Result with the Codex binary already installed on this machine (`codex-cli 0.163.0`):

```text
exit=0
{"type":"item.completed","item":{"id":"item_2","type":"agent_message","text":"I will create the file now."}}
{"type":"item.started","item":{"id":"item_3","type":"command_execution","command":"/bin/bash -lc \"printf 'hello from mock\\n' > hello.txt\"",...}}
{"type":"item.completed","item":{"id":"item_3","type":"command_execution",...,"exit_code":0,"status":"completed"}}
{"type":"turn.completed","usage":{"input_tokens":84,"cached_input_tokens":0,"cache_write_tokens":0,"output_tokens":14,"reasoning_output_tokens":0}}
```

Observations from the captured requests:

- Both requests sent `store: false` and `stream: true`.
- Request 2 replayed the assistant preamble as `{"type":"message","status":"completed","id":"msg_mock_preamble","role":"assistant",...}`. The `id` and `status` survived the round trip, so the documented OpenRouter requirement is satisfied when the provider supplies both fields.
- The `function_call` item and the `function_call_output` item round-tripped with the same `call_id`.
- Codex executed the tool call and produced a second model turn, so the multi-turn path works.
- `turn.completed` reported usage in the shape Codex documents.

This is not a substitute for the live OpenRouter run. It removes the wire-format objection, but it used Codex `0.163.0`, not the required source build of `v0.165.0`, and it did not prove either model emits usable tool calls. The same mock test must be repeated with the built binary, followed by the two live runs.

OpenRouter's published OpenAPI document (`https://openrouter.ai/openapi.json`, fetched 2026-10-29) was also checked against the request Codex sends. Every field in the captured request maps to the schema:

- `store` is `const: false`.
- `include` accepts `reasoning.encrypted_content`.
- `prompt_cache_key`, `parallel_tool_calls`, `tool_choice`, `stream`, and `reasoning` are defined fields.
- `reasoning.effort` accepts `max`, `xhigh`, `high`, `medium`, `low`, `minimal`, `none`, or null.
- `tools` accepts function tools with `defer_loading` and `output_schema`, `namespace` tools, and `web_search` server tools.
- `previous_response_id` is explicitly rejected when non-null, which matches Codex sending `store: false` and full history.

The only captured field not named in the schema is `client_metadata`. The request object does not set `additionalProperties: false`, so it is allowed. OpenRouter's own Codex launcher sends the same Codex payload, which is further evidence that the field is accepted.

## 2. Exact non-interactive command and flags

The source-built binary is used through `codex exec`:

```bash
CODEX_HOME="$RUN_DIR/codex-home" \
  "$CODEX_BIN" exec \
  --json \
  --skip-git-repo-check \
  -C "$REPO" \
  -s workspace-write \
  -m "$MODEL" \
  -c model_provider=openrouter \
  -c 'model_providers.openrouter.name="OpenRouter"' \
  -c 'model_providers.openrouter.base_url="https://openrouter.ai/api/v1"' \
  -c 'model_providers.openrouter.env_key="OPENROUTER_API_KEY"' \
  -c 'model_providers.openrouter.wire_api="responses"' \
  -c "model_context_window=$CONTEXT" \
  -c 'model_reasoning_effort="minimal"' \
  "$PROMPT"
```

Flag sources:

- `codex-rs/exec/src/cli.rs`: `--json`, `--skip-git-repo-check`, `-C`, `-s`, `-m`, `-c`.
- `codex-rs/utils/cli/src/shared_options.rs`: `-C`, `-s`, `-m`, `-c`.
- `codex-rs/utils/cli/src/config_override.rs`: `-c key=value`; the value is parsed as TOML, with a raw-string fallback.

`model_reasoning_effort` is set to `minimal`, not `none`. OpenRouter's Responses API documents `minimal`, `low`, `medium`, and `high`; `none` is not in its documented set, even though Codex accepts it. A mock run confirmed Codex emits `reasoning: {"effort": "minimal", "summary": "auto"}` for this setting. If OpenRouter rejects the `reasoning` object for a non-reasoning model, the fallback is to omit the override entirely; Codex then sends `reasoning: {"summary": "auto"}`.

When the engine adapter calls Codex from Python, it must set `stdin=subprocess.DEVNULL`. Without that, Codex prints `Reading additional input from stdin...` and waits for input when the parent process is not a TTY.

## 3. Does Codex report token counts?

Yes, source-confirmed.

`codex exec --json` emits a `turn.completed` event. Its `usage` object contains:

- `input_tokens`
- `cached_input_tokens`
- `cache_write_input_tokens`
- `output_tokens`
- `reasoning_output_tokens`

Source: `codex-rs/exec/src/exec_events.rs`, `TurnCompletedEvent` and `Usage`.

The live OpenRouter logs must confirm that OpenRouter returns usage in the shape Codex expects.

## 4. How to pass the provider URL and key

- Provider URL: `model_providers.openrouter.base_url = "https://openrouter.ai/api/v1"`.
- Key: `model_providers.openrouter.env_key = "OPENROUTER_API_KEY"`. Codex reads the variable from the child process environment at request time. The key never enters a config file, the repository, or the run log.
- Wire API: `model_providers.openrouter.wire_api = "responses"`. `chat` is a hard error in this Codex version.
- Auth: `requires_openai_auth` defaults to `false`, so no ChatGPT login is needed for this provider.
- Config location: project `.codex/config.toml` is not allowed to override `model_provider` or `model_providers`. The adapter must use CLI `-c` overrides or a dedicated `CODEX_HOME` with a user-level `config.toml`.
- The `-c` parser accepts TOML. Individual dotted keys avoid quoting problems with a large inline table.

## Run log: model 1

Model: `qwen/qwen3-coder-next`

Status: Pending live run.

Task prompt:

```text
Create a file named greet.py with a function greet(name: str) -> str that returns "Hello, {name}!". Create check_greet.py that imports greet, asserts greet("maxcode") == "Hello, maxcode!", prints "ok", and exits 0. Run python3 check_greet.py and confirm it prints "ok". Only change those two files.
```

## Run log: model 2

Model: `deepseek/deepseek-v3.2`

Status: Pending live run.

Task prompt: same as model 1.

## Assumption A1: GitHub search

Searches run on 2026-10-29:

| Query | GitHub result count | Main finding |
|---|---:|---|
| `verifier coding agent` | 5,539 | Top results are a security-audit skill, observability tools, challenge courses, and an LLM-as-verifier framework. None is a mainstream coding CLI with a pass/fail gate as its core product. |
| `coding agent verifier loop` | 550 | Harness books, long-horizon harnesses, and workflow frameworks. Not a coding CLI product. |
| `code agent test gate` | 562 | Skills and quality-gate add-ons for existing agents. Not a core gate. |
| `autonomous coding agent tests pass` | 34 | Small prototypes, not widely used tools. |

A web search also found:

- Aider's internal verify-fix loop. It is a feature of the agent, not an independent pass/fail gate that owns task completion.
- A pydantic-ai feature request for a `VerificationLoop` capability.
- `verifier-gate`, a small project that only ships what a program verifies.
- An article describing an OpenCode + CI verification gate pattern.

Conclusion: A1 holds for mainstream open coding CLIs. The idea exists in components and small projects, so the public claim must be precise: **no widely used open coding CLI makes an independent pass/fail gate its core product**. The benchmark should test the claimed advantage, not absolute novelty.

## Blockers

- `OPENROUTER_API_KEY` is not visible to the OpenCode process. Export it in the shell that launches OpenCode and restart OpenCode.
- The source build must finish before the live runs can start.

## T0 completion note

Live runs on `qwen/qwen3-coder-next` and `deepseek/deepseek-v3.2` were skipped
by the user. The wire format was validated against the strict mock with Codex
0.163.0, and the OpenRouter OpenAPI schema was checked against Codex's payload.
The wrapper decision stands. When an API key is available, run the exact command
in section 2 with `MAXCODE_CODEX_BIN` pointing at the source-built Codex binary.
