# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""The provider interface used by the planner and by tests."""

from collections.abc import Sequence
from typing import Protocol

from maxcode.schemas import ChatMessage, ChatResult


class Provider(Protocol):
    """Any OpenAI-compatible text provider."""

    def chat(self, messages: Sequence[ChatMessage], model: str) -> ChatResult:
        """Send one chat request and return text plus token counts."""
        ...

    def close(self) -> None:
        """Release network resources."""
        ...
