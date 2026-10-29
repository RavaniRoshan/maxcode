# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Smoke test: the package imports and the CLI responds."""

from typer.testing import CliRunner

import maxcode
from maxcode.cli import app


def test_package_imports() -> None:
    assert maxcode.__version__ == "0.1.0"


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "maxcode" in result.output
