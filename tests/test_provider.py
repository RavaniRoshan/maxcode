# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the OpenAI-compatible provider."""

from typing import Any

import httpx
import pytest

from maxcode.errors import ProviderError
from maxcode.providers.openai_compat import OpenAICompatProvider

MESSAGES = [{"role": "user", "content": "hello"}]


def make_provider(handler: Any) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        "https://api.example.com/v1/",
        "sk-secret",
        transport=httpx.MockTransport(handler),
    )


def test_chat_returns_text_and_token_counts() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["authorization"]
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "hi there"}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 4},
            },
        )

    provider = make_provider(handler)
    result = provider.chat(MESSAGES, "test-model")
    assert result.text == "hi there"
    assert result.input_tokens == 11
    assert result.output_tokens == 4
    assert captured["url"] == "https://api.example.com/v1/chat/completions"
    assert captured["auth"] == "Bearer sk-secret"
    assert b'"model":"test-model"' in captured["body"]
    provider.close()


def test_http_500_raises_provider_error() -> None:
    provider = make_provider(lambda request: httpx.Response(500, text="upstream boom"))
    with pytest.raises(ProviderError) as excinfo:
        provider.chat(MESSAGES, "m")
    message = str(excinfo.value)
    assert "500" in message
    assert "Next:" in message
    provider.close()


def test_error_body_redacts_key() -> None:
    provider = make_provider(
        lambda request: httpx.Response(401, text="invalid key sk-secret")
    )
    with pytest.raises(ProviderError) as excinfo:
        provider.chat(MESSAGES, "m")
    assert "sk-secret" not in str(excinfo.value)
    provider.close()


def test_timeout_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("too slow", request=request)

    provider = make_provider(handler)
    with pytest.raises(ProviderError) as excinfo:
        provider.chat(MESSAGES, "m")
    assert "timed out" in str(excinfo.value).lower()
    provider.close()


def test_malformed_response_raises_provider_error() -> None:
    provider = make_provider(lambda request: httpx.Response(200, json={"nope": True}))
    with pytest.raises(ProviderError):
        provider.chat(MESSAGES, "m")
    provider.close()
