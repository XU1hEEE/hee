from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from hee_bot.bot import LocalCompanionBot
from hee_bot.ollama_client import OllamaError


class BotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.bot = LocalCompanionBot(db_path=str(Path(self.directory.name) / "bot.db"))
        self.bot.llm_client = Mock()

    def tearDown(self) -> None:
        self.bot.db.close()
        self.directory.cleanup()

    def test_remember_and_clear_do_not_call_the_model_or_affect_other_spaces(self) -> None:
        work = self.bot.db.add_memory_space("Work", "Work context")
        self.bot.handle_input("/remember I prefer tea", 1)
        self.bot.handle_input("/remember Use Python", work)
        self.bot.handle_input("/clear", 1)
        self.assertEqual(self.bot.db.find_memories(1, ""), [])
        self.assertEqual(self.bot.db.find_memories(work, "")[0].content, "Use Python")
        self.bot.llm_client.chat.assert_not_called()

    def test_chat_uses_space_context_and_saves_the_message(self) -> None:
        self.bot.handle_input("/remember I prefer tea", 1)
        self.bot.llm_client.chat.return_value = "Let's make tea."
        self.assertEqual(self.bot.handle_input("What should I drink?", 1)["reply"], "Let's make tea.")
        prompt = self.bot.llm_client.chat.call_args[0][0][0]["content"]
        self.assertIn("I prefer tea", prompt)
        memories = self.bot.db.find_memories(1, "")
        self.assertEqual(len(memories), 2)
        self.assertTrue(any(m.content == "What should I drink?" and m.memory_type == "episodic" for m in memories))

    def test_unavailable_backend_returns_actionable_reply_without_saving_message(self) -> None:
        self.bot.llm_client.chat.side_effect = OllamaError("unavailable")
        self.assertIn("Start Ollama", self.bot.handle_input("Hello", 1)["reply"])
        self.assertEqual(self.bot.db.find_memories(1, ""), [])

    def test_empty_remember_does_not_save_blank_memory(self) -> None:
        self.bot.handle_input("/remember  ", 1)
        self.assertEqual(self.bot.db.find_memories(1, ""), [])
