# Changelog

## Unreleased

## 0.1.0-alpha.1 - 2026-11-01

### Added

- Live evidence on local open-weight models: `qwen3:1.7b` and `llama3.2:3b`
  completed multi-turn tool-calling tasks and full `maxcode run` loops with the
  verifier on. Logs and commands are in `spike/`; the analysis is in `SPIKE.md`.
- The engine adapter falls back to stock `codex` 0.165+ on `PATH`.
- `MAXCODE_REASONING_EFFORT` and `MAXCODE_MODEL_CONTEXT_WINDOW` environment
  overrides for providers with different reasoning or context settings.
- The benchmark runner puts a repository's `src/` on `PYTHONPATH`, so pinned
  src-layout projects can run their own tests and score commands.
- Planner, worker, and verifier roles with a retry loop.
- Git checkpoints under `refs/maxcode/` and the `undo` command.
- OpenAI-compatible provider support.
- Cost and token reporting, including partial results.
- JSONL run logs.
- Repository check detection for Python, Node, Rust, and Go.
- Benchmark runner with 20 runs across four pinned Python projects and a report script.
- Three-page static marketing site with the Max mascot.

### Changed

- The engine is now a full rebrand: `maxcode-engine`, `maxcode-*` crates,
  `MAXCODE_HOME`, and maxcode help/TUI strings.
- Disabled web search and multi-agent tools in the worker command; Ollama 0.31.1
  loses function names when those tool types are present.
- The README, SPIKE, and site now distinguish live-verified, mock-verified, and
  unverified claims.
- README, site, and mascot assets were rebuilt around Max and the verifier loop.
- The site is three pages (Home, Docs, Benchmark); GitHub is an external link.

### Fixed

- The TUI welcome animation no longer morphs an OpenAI logo.
- Package metadata points at the correct GitHub repository.

### Notes

- The original OpenRouter models (`qwen/qwen3-coder-next`,
  `deepseek/deepseek-v3.2`) remain unverified because no funded credential is
  available. The 2026-10-31 live runs use local Ollama models and are recorded in
  `SPIKE.md`.
- Publish to PyPI with `uv publish` after the trademark and legal review.
