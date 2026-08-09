"""Minimal Ollama client for local chat and embeddings."""

from __future__ import annotations

from typing import Any

import requests

from hee_bot.config import SETTINGS


class OllamaError(RuntimeError):
    """Raised when Ollama requests fail."""


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = SETTINGS.ollama_base_url.rstrip("/")
        self.timeout = SETTINGS.request_timeout_seconds

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.4) -> str:
        payload = {
            "model": SETTINGS.chat_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = self._post("/api/chat", payload)
        data = response.json()
        try:
            return str(data["message"]["content"]).strip()
        except KeyError as exc:
            raise OllamaError(f"Unexpected Ollama chat response: {data}") from exc

    def embed(self, text: str) -> list[float]:
        payload = {"model": SETTINGS.embedding_model, "input": text}
        last_error = ""

        for endpoint in ("/api/embed", "/api/embeddings"):
            try:
                response = self._post(endpoint, payload)
            except OllamaError as exc:
                last_error = str(exc)
                continue

            if response.ok:
                data = response.json()
                if "embeddings" in data and data["embeddings"]:
                    return [float(value) for value in data["embeddings"][0]]
                if "embedding" in data:
                    return [float(value) for value in data["embedding"]]
                last_error = f"Unexpected Ollama embedding response: {data}"

        raise OllamaError(
            "Unable to fetch embeddings from Ollama. "
            f"Make sure model '{SETTINGS.embedding_model}' is available locally. "
            f"Details: {last_error or 'No compatible embedding endpoint responded.'}"
        )

    def _post(self, endpoint: str, payload: dict[str, Any]) -> requests.Response:
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise OllamaError(f"Unable to reach Ollama at {self.base_url}: {exc}") from exc
        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.ok:
            return

        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise OllamaError(f"Ollama request failed ({response.status_code}): {detail}")
