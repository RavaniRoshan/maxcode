# Changelog

## Unreleased

### Changed

- The engine is now a full rebrand: `maxcode-engine`, `maxcode-*` crates,
  `MAXCODE_HOME`, and maxcode help/TUI strings.
- The Python adapter finds only `maxcode-engine`; set `MAXCODE_ENGINE_BIN` or
  put the binary on `PATH`. No fallback binary is used.
- README, site, and mascot assets were rebuilt around Max and the verifier loop.
- The site is three pages (Home, Docs, Benchmark); GitHub is an external link.

### Fixed

- The TUI welcome animation no longer morphs an OpenAI logo.
- Package metadata points at the correct GitHub repository.

## 0.1.0 - 2026-10-29

### Added

- Planner, worker, and verifier roles with a retry loop.
- Git checkpoints under `refs/maxcode/` and the `undo` command.
- OpenAI-compatible provider support.
- Cost and token reporting, including partial results.
- JSONL run logs.
- Repository check detection for Python, Node, Rust, and Go.
- Benchmark runner with 20 runs across four pinned Python projects and a report script.
- Three-page static marketing site with the Max mascot.

### Notes

- T0 live runs on `qwen/qwen3-coder-next` and `deepseek/deepseek-v3.2` are recorded
  in `SPIKE.md` once an API key is available.
- Publish to PyPI with `uv publish` after the trademark and legal review.
