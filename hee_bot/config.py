"""Configuration for the local-first companion bot."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _default_data_dir() -> Path:
    configured = os.getenv("HEE_DATA_DIR")
    if configured:
        return Path(configured).expanduser()

    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Hee"
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "Hee"
        return home / "AppData" / "Roaming" / "Hee"
    return Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share")) / "Hee"


def _default_sqlite_path() -> Path:
    configured = os.getenv("HEE_SQLITE_PATH")
    if configured:
        return Path(configured).expanduser()
    return _default_data_dir() / "hee_bot.db"


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b")
    embedding_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    sqlite_path: Path = _default_sqlite_path()
    max_history_messages: int = int(os.getenv("HEE_MAX_HISTORY_MESSAGES", "12"))
    max_memories: int = int(os.getenv("HEE_MAX_MEMORIES", "4"))
    memory_score_threshold: float = float(os.getenv("HEE_MEMORY_SCORE_THRESHOLD", "0.35"))
    request_timeout_seconds: int = int(os.getenv("HEE_REQUEST_TIMEOUT_SECONDS", "120"))


SETTINGS = Settings()
