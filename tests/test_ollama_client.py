from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from hee_bot.ollama_client import OllamaClient, OllamaError


class OllamaClientTests(unittest.TestCase):
    @patch("hee_bot.ollama_client.requests.post")
    def test_chat_wraps_network_errors(self, mock_post: Mock) -> None:
        mock_post.side_effect = requests.ConnectionError("connection refused")
        with self.assertRaisesRegex(OllamaError, "Unable to reach Ollama"):
            OllamaClient().chat([{"role": "user", "content": "hello"}])

    @patch("hee_bot.ollama_client.requests.post")
    def test_chat_wraps_invalid_responses(self, mock_post: Mock) -> None:
        mock_post.return_value.json.return_value = {"error": "missing model"}
        with self.assertRaises(OllamaError):
            OllamaClient().chat([{"role": "user", "content": "hello"}])

    @patch("hee_bot.ollama_client.requests.post")
    def test_chat_returns_model_reply(self, mock_post: Mock) -> None:
        mock_post.return_value.json.return_value = {"message": {"content": "Hello!"}}
        self.assertEqual(OllamaClient().chat([{"role": "user", "content": "hello"}]), "Hello!")
