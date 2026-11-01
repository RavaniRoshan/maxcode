# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests that the project version is written the same way everywhere."""

import re
import tomllib
from pathlib import Path

from maxcode import __version__

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_version_matches_package() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == __version__


def test_changelog_top_entry_matches_package() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    released = [heading for heading in headings if heading != "Unreleased"]
    assert released[0].split(" - ")[0].strip() == __version__


def test_readme_status_badge_matches_package() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r'status-v[^"]*"[^>]*alt="v([^"]+)"', text)
    assert match is not None
    assert match.group(1) == __version__
