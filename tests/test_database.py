from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from hee_bot.database import BotDatabase


class BotDatabaseTests(unittest.TestCase):
    def test_uses_workspace_fallback_when_default_directory_is_blocked(self) -> None:
        connection = MagicMock()
        sqlite_context = MagicMock()
        sqlite_context.__enter__.return_value = connection
        sqlite_context.__exit__.return_value = False

        restricted_parent = Path("/restricted")
        real_mkdir = Path.mkdir

        def fake_mkdir(path_obj: Path, *args: object, **kwargs: object) -> None:
            if path_obj == restricted_parent:
                raise PermissionError("blocked")
            return real_mkdir(path_obj, *args, **kwargs)

        with patch("sqlite3.connect", return_value=sqlite_context), patch(
            "pathlib.Path.mkdir",
            autospec=True,
            side_effect=fake_mkdir,
        ):
            database = BotDatabase(restricted_parent / "hee_bot.db")

        self.assertEqual(database.db_path, Path.cwd() / ".hee-data" / "hee_bot.db")


if __name__ == "__main__":
    unittest.main()
