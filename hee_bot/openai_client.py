"""Client for interacting with the OpenAI API."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import openai

class OpenAIClient:
    """A client for interacting with the OpenAI API."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the OpenAI client."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")
        openai.api_key = self.api_key

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Get a chat completion from the OpenAI API."""
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error from OpenAI: {e}"
