"""Configuration for Hee."""

from __future__ import annotations

import os

# Get the absolute path of the project's root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the database path relative to the root directory
DATABASE_PATH = os.path.abspath(os.path.expanduser(
    os.environ.get("HEE_SQLITE_PATH", os.path.join(ROOT_DIR, "hee_database.db"))
))
