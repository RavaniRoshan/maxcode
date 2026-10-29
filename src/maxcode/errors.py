# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Error types.

Every user-facing error message has three parts: what failed, why it failed,
and what to do next.
"""


class MaxcodeError(Exception):
    """Base class for all maxcode errors."""

    def __init__(self, what: str, why: str, next_step: str) -> None:
        self.what = what
        self.why = why
        self.next_step = next_step
        super().__init__(f"{what}\nWhy: {why}\nNext: {next_step}")


class ConfigError(MaxcodeError):
    """The configuration file or the command line is invalid."""


class ProviderError(MaxcodeError):
    """A model provider call failed."""


class EngineError(MaxcodeError):
    """The Codex engine failed to start or to finish."""


class PlanError(MaxcodeError):
    """The planner did not return a usable plan."""


class CheckError(MaxcodeError):
    """A check could not be run."""


class CheckpointError(MaxcodeError):
    """A git checkpoint could not be created or restored."""


class NotAGitRepo(CheckpointError):
    """The working directory is not inside a git repository."""
