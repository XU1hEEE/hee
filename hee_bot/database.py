"""Database interactions for Hee, the AI companion."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any, Generator, List

from hee_bot.models import EnrichedMemoryRecord, MemoryRecord, MemorySpace

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_spaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    space_id INTEGER NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    source_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (space_id) REFERENCES memory_spaces (id)
);

CREATE TABLE IF NOT EXISTS memory_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    operation TEXT NOT NULL, -- 'CREATE', 'UPDATE', 'DELETE'
    old_content TEXT,
    new_content TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES memories (id)
);
"""


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        if self._conn:
            self._conn.close()

    @contextmanager
    def cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        if not self._conn:
            raise sqlite3.OperationalError("Database connection is not open.")

        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def initialize(self) -> None:
        with self.cursor() as cur:
            cur.executescript(DB_SCHEMA)
            cur.execute("SELECT COUNT(*) FROM memory_spaces")
            if cur.fetchone()[0] == 0:
                self.add_memory_space("Default", "Default memory space.")

    def add_memory_space(self, name: str, description: str) -> int:
        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO memory_spaces (name, description) VALUES (?, ?)",
                (name, description),
            )
            return cur.lastrowid

    def get_memory_spaces(self) -> List[MemorySpace]:
        with self.cursor() as cur:
            cur.execute("SELECT id, name, description, created_at FROM memory_spaces")
            return [MemorySpace(**row) for row in cur.fetchall()]

    def add_memory(self, space_id: int, memory: MemoryRecord) -> int:
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO memories (space_id, memory_type, content, source_message)
                   VALUES (?, ?, ?, ?)""",
                (space_id, memory.memory_type, memory.content, memory.source_message),
            )
            memory_id = cur.lastrowid
            self._log_history(cur, memory_id, "CREATE", new_content=memory.content)
            return memory_id

    def _log_history(
        self,
        cur: sqlite3.Cursor,
        memory_id: int,
        operation: str,
        old_content: str | None = None,
        new_content: str | None = None,
    ) -> None:
        cur.execute(
            """INSERT INTO memory_history (memory_id, operation, old_content, new_content)
               VALUES (?, ?, ?, ?)""",
            (memory_id, operation, old_content, new_content),
        )

    def find_memories(self, space_id: int, query: str) -> List[MemoryRecord]:
        with self.cursor() as cur:
            cur.execute(
                """SELECT id, memory_type, content, source_message, last_updated_at
                   FROM memories WHERE space_id = ? ORDER BY last_updated_at DESC""",
                (space_id,),
            )
            return [MemoryRecord(**row) for row in cur.fetchall()]

    def update_memory(self, memory_id: int, new_content: str) -> None:
        with self.cursor() as cur:
            cur.execute("SELECT content FROM memories WHERE id = ?", (memory_id,))
            old_content = cur.fetchone()["content"]

            cur.execute(
                "UPDATE memories SET content = ?, last_updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_content, memory_id),
            )
            self._log_history(
                cur,
                memory_id,
                "UPDATE",
                old_content=old_content,
                new_content=new_content,
            )

    def delete_memory(self, memory_id: int) -> None:
        with self.cursor() as cur:
            cur.execute("SELECT content FROM memories WHERE id = ?", (memory_id,))
            old_content = cur.fetchone()["content"]
            cur.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self._log_history(cur, memory_id, "DELETE", old_content=old_content)

    def get_enriched_memories(self, space_id: int) -> List[EnrichedMemoryRecord]:
        query = """
            SELECT
                m.id,
                m.space_id,
                ms.name as space_name,
                m.memory_type,
                m.content,
                m.source_message,
                m.created_at,
                m.last_updated_at,
                (SELECT GROUP_CONCAT(printf('%s: %s -> %s', operation, old_content, new_content), '\n')
                 FROM memory_history mh
                 WHERE mh.memory_id = m.id) as history
            FROM memories m
            JOIN memory_spaces ms ON m.space_id = ms.id
            WHERE m.space_id = ?
            ORDER BY m.last_updated_at DESC;
        """
        with self.cursor() as cur:
            cur.execute(query, (space_id,))
            rows = cur.fetchall()
            return [EnrichedMemoryRecord(**row) for row in rows]
