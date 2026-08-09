from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from hee_bot.ollama_client import OllamaClient, OllamaError


class OllamaClientTests(unittest.TestCase):
    @patch("hee_bot.ollama_client.requests.post")
    def test_chat_wraps_network_errors(self, mock_post: Mock) -> None:
        mock_post.side_effect = requests.ConnectionError("connection refused")

        client = OllamaClient()

        with self.assertRaises(OllamaError) as context:
            client.chat([{"role": "user", "content": "hello"}])

        self.assertIn("Unable to reach Ollama", str(context.exception))

    @patch("hee_bot.ollama_client.requests.post")
    def test_embed_falls_back_to_legacy_endpoint(self, mock_post: Mock) -> None:
        not_found = Mock()
        not_found.ok = False
        not_found.status_code = 404
        not_found.json.return_value = {"error": "not found"}

        legacy_ok = Mock()
        legacy_ok.ok = True
        legacy_ok.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

        mock_post.side_effect = [not_found, legacy_ok]

        client = OllamaClient()
        result = client.embed("hello")

        self.assertEqual(result, [0.1, 0.2, 0.3])
        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
