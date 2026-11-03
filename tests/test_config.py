from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from hee_bot import config


class ConfigTests(unittest.TestCase):
    def tearDown(self) -> None:
        importlib.reload(config)

    def test_default_database_is_in_project_root(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            self.assertEqual(Path(config.DATABASE_PATH), Path(config.ROOT_DIR) / "hee_database.db")

    def test_database_override_expands_home_directory(self) -> None:
        with patch.dict(os.environ, {"HEE_SQLITE_PATH": "~/custom/hee.sqlite"}):
            importlib.reload(config)
            self.assertEqual(Path(config.DATABASE_PATH), Path("~/custom/hee.sqlite").expanduser())
