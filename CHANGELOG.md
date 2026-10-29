# Changelog

## 0.1.0 - 2026-10-29

### Added

- Planner, worker, and verifier roles with a retry loop.
- Git checkpoints under `refs/maxcode/` and the `undo` command.
- OpenAI-compatible provider support.
- Cost and token reporting, including partial results.
- JSONL run logs.
- Repository check detection for Python, Node, Rust, and Go.
- Benchmark runner with 20 tasks and a report script.
- Four-page static marketing site.

### Notes

- T0 live runs on `qwen/qwen3-coder-next` and `deepseek/deepseek-v3.2` are recorded
  in `SPIKE.md` once an API key is available.
- Publish to PyPI with `uv publish` after the trademark and legal review.
