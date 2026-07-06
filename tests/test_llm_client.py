"""Tests for llm_client.py — OpenRouter (OpenAI-compatible) wrapper.

No network calls: the OpenAI client is swapped for a MagicMock before chat().
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from llm_client import LLMClient


def _fake_response(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def test_from_config_defaults(monkeypatch):
    # No key set → client unavailable, but config still constructs.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    c = LLMClient.from_config({})
    assert c.model  # has a default model
    assert c.is_available() is False


def test_from_config_overrides(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    cfg = {"base_url": "http://x", "model": "some/model", "temperature": 0.3,
           "api_key_env": "OPENROUTER_API_KEY"}
    c = LLMClient.from_config(cfg)
    assert c.model == "some/model"
    assert c.temperature == 0.3
    assert c.is_available() is True


def test_is_available_with_and_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert LLMClient().is_available() is False

    monkeypatch.setenv("OPENROUTER_API_KEY", "abc")
    assert LLMClient().is_available() is True


def test_chat_returns_content(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    client = LLMClient()

    mock = MagicMock()
    mock.chat.completions.create.return_value = _fake_response("hello world")
    client._client = mock  # bypass real OpenAI client

    assert client.chat("sys", "usr") == "hello world"
    mock.chat.completions.create.assert_called_once()
    # Confirm the request used the configured model + system/user messages
    kwargs = mock.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == client.model
    assert kwargs["messages"][0]["role"] == "system"
    assert kwargs["messages"][1]["role"] == "user"


def test_chat_strips_whitespace(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    client = LLMClient()
    mock = MagicMock()
    mock.chat.completions.create.return_value = _fake_response("  trimmed  ")
    client._client = mock
    assert client.chat("s", "u") == "trimmed"


def test_chat_raises_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = LLMClient()
    with pytest.raises(RuntimeError):
        client.chat("s", "u")


def test_chat_retries_on_transient_error(monkeypatch):
    """A failing first attempt should be retried, then succeed."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    client = LLMClient(max_retries=3)

    mock = MagicMock()
    mock.chat.completions.create.side_effect = [
        RuntimeError("transient"),
        _fake_response("ok"),
    ]
    client._client = mock

    # Avoid real sleeping in tests.
    monkeypatch.setattr("llm_client.time.sleep", lambda _s: None)

    assert client.chat("s", "u") == "ok"
    assert mock.chat.completions.create.call_count == 2
