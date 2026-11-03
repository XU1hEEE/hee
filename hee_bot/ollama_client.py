"""Client for interacting with the Ollama API."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests


class OllamaError(RuntimeError):
    """An unavailable or invalid response from the local model service."""


class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434") -> None:
        self.host = host

    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.8) -> str:
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": "mistral",
                    "messages": messages,
                    "options": {"temperature": temperature},
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Expected text content")
            return content
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise OllamaError("Unable to reach Ollama or read its response.") from exc

    def embeddings(self, text: str) -> List[float]:
        response = requests.post(
            f"{self.host}/api/embeddings",
            json={"model": "mistral", "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]
