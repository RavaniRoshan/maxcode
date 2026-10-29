# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""OpenAI-compatible Chat Completions provider."""

from collections.abc import Sequence
from typing import Any

import httpx
from pydantic import ValidationError

from maxcode.errors import ProviderError
from maxcode.schemas import ChatMessage, ChatResult


def _tail(text: str, limit: int = 600) -> str:
    return text[-limit:] if len(text) > limit else text


def _redact(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "[redacted]")


class OpenAICompatProvider:
    """A small client for any endpoint that implements /chat/completions."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_s: float = 120.0,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            transport=transport,
        )

    def chat(self, messages: Sequence[ChatMessage], model: str) -> ChatResult:
        """Send one chat request and return text plus token counts."""
        payload = {"model": model, "messages": list(messages)}
        try:
            response = self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError(
                "The provider request timed out.",
                f"No response arrived within the configured timeout for model '{model}'.",
                "Check the provider status page and the network, then retry.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            body = _redact(_tail(exc.response.text), self._api_key)
            raise ProviderError(
                f"The provider returned HTTP {exc.response.status_code}.",
                f"The request for model '{model}' failed. Response: {body}",
                "Check the base URL, the model name, and the API key, then retry.",
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(
                "The provider request failed.",
                _redact(str(exc), self._api_key),
                "Check the base URL and the network connection, then retry.",
            ) from exc
        return self._parse(response, model)

    def _parse(self, response: httpx.Response, model: str) -> ChatResult:
        try:
            data: Any = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data["usage"]
            return ChatResult(
                text=str(content),
                input_tokens=int(usage["prompt_tokens"]),
                output_tokens=int(usage["completion_tokens"]),
            )
        except (ValueError, KeyError, IndexError, TypeError, ValidationError) as exc:
            body = _redact(_tail(response.text), self._api_key)
            raise ProviderError(
                "The provider returned an unusable response.",
                f"Model '{model}' did not return choices[0].message.content and usage. "
                f"Response: {body}",
                "Use an OpenAI-compatible chat endpoint that returns text and usage, then retry.",
            ) from exc

    def close(self) -> None:
        """Close the HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "OpenAICompatProvider":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
