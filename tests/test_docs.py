# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Check that the documented developer commands match the ones CI runs."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _ci_commands() -> list[str]:
    text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    return [
        command
        for command in re.findall(r"^\s+run: (\S.*)$", text, re.MULTILINE)
        if command.startswith("uv run ")
    ]


def _block_commands(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
        lines.extend(line.strip() for line in block.splitlines() if line.strip())
    return lines


def test_contributing_runs_the_ci_commands() -> None:
    documented = _block_commands(ROOT / "CONTRIBUTING.md")
    for command in _ci_commands():
        assert command in documented


def test_contributing_documents_no_other_check_command() -> None:
    documented = {
        line for line in _block_commands(ROOT / "CONTRIBUTING.md") if line.startswith("uv run ")
    }
    assert documented == set(_ci_commands())


def test_readme_development_section_matches_contributing() -> None:
    contributing = _block_commands(ROOT / "CONTRIBUTING.md")
    readme = _block_commands(ROOT / "README.md")
    for command in contributing:
        assert command in readme, f"README.md does not document {command!r}"
