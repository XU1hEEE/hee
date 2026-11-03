from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hee_bot.database import Database
from hee_bot.models import MemoryRecord


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name) / "memories.db")
        self.db = Database(self.path)
        self.db.initialize()

    def tearDown(self) -> None:
        self.db.close()
        self.directory.cleanup()

    def test_memories_stay_in_their_space_and_survive_reopening(self) -> None:
        space = self.db.add_memory_space("Work", "Work context")
        self.db.add_memory(space, MemoryRecord(id=0, memory_type="semantic", content="Use Python", source_message="I prefer Python"))
        self.assertEqual(self.db.find_memories(1, ""), [])
        self.db.close()
        self.db = Database(self.path)
        memory = self.db.get_enriched_memories(space)[0]
        self.assertEqual(memory.content, "Use Python")
        self.assertEqual(memory.source_message, "I prefer Python")
        self.assertIn("CREATE", memory.history)

    def test_updates_and_deletions_keep_audit_history(self) -> None:
        memory_id = self.db.add_memory(1, MemoryRecord(id=0, memory_type="semantic", content="Tea"))
        self.db.update_memory(memory_id, "Coffee")
        self.assertEqual(self.db.find_memories(1, "")[0].content, "Coffee")
        self.db.delete_memory(memory_id)
        self.assertEqual(self.db.find_memories(1, ""), [])
        with self.db.cursor() as cursor:
            cursor.execute("SELECT operation, old_content FROM memory_history WHERE memory_id = ? ORDER BY id", (memory_id,))
            history = cursor.fetchall()
        self.assertEqual([row["operation"] for row in history], ["CREATE", "UPDATE", "DELETE"])
        self.assertEqual(history[-1]["old_content"], "Coffee")
