"""
llm_client.py — Thin wrapper around the OpenAI-compatible OpenRouter API.

OpenRouter (openrouter.ai) exposes an endpoint that speaks the exact same
wire format as the OpenAI Chat Completions API, so the official `openai` SDK
is reused here purely as an HTTP client — pointed at OpenRouter's base_url
with an OPENROUTER_API_KEY. No OpenAI account, key, or model is involved.

Used by prompt_builder.py to generate the story bible and per-scene image
prompts via an LLM.
"""

import os
import time
from typing import Optional

from openai import OpenAI


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "z-ai/glm-5.2@preset/main"
DEFAULT_TEMPERATURE = 0.8
DEFAULT_API_KEY_ENV = "OPENROUTER_API_KEY"


class LLMClient:
    """A small chat-completions client over OpenRouter (OpenAI-compatible)."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        api_key_env: str = DEFAULT_API_KEY_ENV,
        max_retries: int = 3,
    ):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self._api_key = os.environ.get(api_key_env, "")
        self._client: Optional[OpenAI] = None
        if self._api_key:
            self._client = OpenAI(
                base_url=base_url,
                api_key=self._api_key,
            )

    @classmethod
    def from_config(cls, cfg: dict) -> "LLMClient":
        """Build an LLMClient from the `prompt_builder` config block."""
        cfg = cfg or {}
        return cls(
            base_url=cfg.get("base_url", DEFAULT_BASE_URL),
            model=cfg.get("model", DEFAULT_MODEL),
            temperature=float(cfg.get("temperature", DEFAULT_TEMPERATURE)),
            api_key_env=cfg.get("api_key_env", DEFAULT_API_KEY_ENV),
        )

    def is_available(self) -> bool:
        """True if an API key was found and the client is usable."""
        return self._client is not None

    def chat(self, system: str, user: str) -> str:
        """
        Send a single chat completion request and return the assistant's text.

        Retries with exponential backoff on transient errors (rate limits,
        server errors, network hiccups). Raises on persistent failure.
        """
        if self._client is None:
            raise RuntimeError(
                "LLMClient has no API key set — cannot make an LLM call."
            )

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                content = resp.choices[0].message.content
                return (content or "").strip()
            except Exception as e:  # noqa: BLE001 — retry broadly on network/API hiccups
                last_err = e
                # Back off: 1s, 2s, 4s ...
                time.sleep(2 ** attempt)

        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_err}")
