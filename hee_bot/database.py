"""SQLite persistence for messages and long-term memories."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from hee_bot.models import MemoryRecord


class BotDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path.expanduser()
        self._ensure_parent_dir()
        self._init_db()

    def _ensure_parent_dir(self) -> None:
        if self.db_path.parent != Path("."):
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                self._use_workspace_fallback()

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.db_path)
        except sqlite3.OperationalError as exc:
            if "unable to open database file" not in str(exc).lower():
                raise
            self._use_workspace_fallback()
            connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _use_workspace_fallback(self) -> None:
        fallback_path = Path.cwd() / ".hee-data" / self.db_path.name
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = fallback_path

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add_message(self, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content),
            )

    def get_recent_messages(self, limit: int) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    def add_memory(
        self,
        category: str,
        content: str,
        source: str,
        embedding: list[float],
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO memories (category, content, source, embedding_json)
                VALUES (?, ?, ?, ?)
                """,
                (category, content, source, json.dumps(embedding)),
            )
            return int(cursor.lastrowid)

    def list_memories(self, limit: int = 50) -> list[MemoryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, category, content, source, created_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            MemoryRecord(
                id=int(row["id"]),
                category=str(row["category"]),
                content=str(row["content"]),
                source=str(row["source"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def delete_memory(self, memory_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
            return cursor.rowcount > 0

    def search_memories(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, category, content, source, embedding_json, created_at
                FROM memories
                ORDER BY id DESC
                """
            ).fetchall()

        records: list[dict[str, object]] = []
        for row in rows:
            records.append(
                {
                    "id": int(row["id"]),
                    "category": str(row["category"]),
                    "content": str(row["content"]),
                    "source": str(row["source"]),
                    "created_at": str(row["created_at"]),
                    "embedding": json.loads(str(row["embedding_json"])),
                }
            )
        return records
