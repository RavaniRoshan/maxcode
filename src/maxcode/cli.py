# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Command line entry point.

The full command set is added in task T13. This module exists in T1 so the
installed console script and the smoke test are real from the first commit.
"""

import typer

from maxcode import __version__

app = typer.Typer(
    name="maxcode",
    help="Plan a task, edit code, and finish only when checks pass.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Run maxcode commands."""


@app.command()
def version() -> None:
    """Show the installed version."""
    typer.echo(f"maxcode {__version__}")
