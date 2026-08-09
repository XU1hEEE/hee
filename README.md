# Hee

Hee is a private, local-first companion bot for supportive conversations.

It runs fully on your computer with:

- `Streamlit` for the UI
- `Python` for orchestration
- `Ollama` for local chat and embeddings
- `SQLite` for local memory

## Architecture

```text
Browser (Streamlit)
        |
        v
Python bot orchestration
  - conversation handling
  - emotion / intent analysis
  - memory policy
        |
   +----+----+
   |         |
   v         v
Ollama     SQLite
Qwen       messages + memories
```

## Features

- Local chat with `qwen2.5:7b`
- Local embeddings with `nomic-embed-text`
- Explicit memory controls:
  - `/remember I prefer being comforted before advice`
  - `/forget 3`
  - `/memory`
- Memory policy that prefers:
  - long-term preferences
  - important life events
  - recurring goals or concerns
- Memory retrieval based on semantic similarity

## Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Start Ollama and pull the local models:

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
ollama serve
```

4. Run the app:

```bash
streamlit run app.py
```

## Data Storage

- By default, Hee stores its SQLite database outside the project directory.
- macOS default: `~/Library/Application Support/Hee/hee_bot.db`
- Linux default: `~/.local/share/Hee/hee_bot.db`
- Windows default: `%APPDATA%\\Hee\\hee_bot.db`
- In restricted environments that cannot write outside the workspace, Hee falls back to `.hee-data/hee_bot.db`.
- If you already have a local `hee_bot.db` in this folder, set `HEE_SQLITE_PATH` to keep using it or move it to your preferred data directory before publishing.

## Environment Variables

Optional configuration:

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_CHAT_MODEL=qwen2.5:7b
export OLLAMA_EMBED_MODEL=nomic-embed-text
export HEE_DATA_DIR="$HOME/Library/Application Support/Hee"
export HEE_SQLITE_PATH="$HEE_DATA_DIR/hee_bot.db"
export HEE_MAX_HISTORY_MESSAGES=12
export HEE_MAX_MEMORIES=4
export HEE_MEMORY_SCORE_THRESHOLD=0.35
```

## Memory Policy

Hee is designed to avoid remembering everything automatically.

It should remember:

- long-term preferences
- important events
- recurring goals
- recurring concerns
- anything you explicitly save with `/remember`

It should avoid remembering:

- transient emotions
- highly sensitive details unless explicitly requested
- routine filler conversation

## Notes

- All memory stays in the local SQLite database you configure.
- If Ollama is not reachable, Hee falls back safely and returns an actionable error message instead of crashing.
- The app uses Ollama's local embedding API for semantic memory search.
