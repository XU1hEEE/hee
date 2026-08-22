"""OpenAI client for online chat and embeddings."""

from __future__ import annotations

from typing import Any
from openai import OpenAI

from hee_bot.config import SETTINGS


class OpenAIError(RuntimeError):
    """Raised when OpenAI requests fail."""


class OpenAIClient:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=SETTINGS.openai_api_key,
            base_url=SETTINGS.openai_base_url,
        )

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        try:
            response = self.client.chat.completions.create(
                model=SETTINGS.openai_chat_model,
                messages=messages,
                temperature=temperature,
            )
            return str(response.choices[0].message.content).strip()
        except Exception as exc:
            raise OpenAIError(f"OpenAI chat request failed: {exc}") from exc

    def embed(self, text: str) -> list[float]:
        try:
            response = self.client.embeddings.create(
                model=SETTINGS.openai_embedding_model,
                input=text,
            )
            return [float(value) for value in response.data[0].embedding]
        except Exception as exc:
            raise OpenAIError(f"OpenAI embedding request failed: {exc}") from exc
