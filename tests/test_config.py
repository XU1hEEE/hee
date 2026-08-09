from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch


class ConfigTests(unittest.TestCase):
    def test_default_sqlite_path_uses_explicit_override(self) -> None:
        with patch.dict(
            os.environ,
            {"HEE_SQLITE_PATH": "~/custom/hee.sqlite"},
            clear=False,
        ):
            config = importlib.import_module("hee_bot.config")
            importlib.reload(config)
            self.assertEqual(config._default_sqlite_path(), Path("~/custom/hee.sqlite").expanduser())

    def test_default_data_dir_prefers_configured_data_dir(self) -> None:
        with patch.dict(
            os.environ,
            {"HEE_DATA_DIR": "~/hee-data"},
            clear=False,
        ):
            config = importlib.import_module("hee_bot.config")
            importlib.reload(config)
            self.assertEqual(config._default_data_dir(), Path("~/hee-data").expanduser())


if __name__ == "__main__":
    unittest.main()
