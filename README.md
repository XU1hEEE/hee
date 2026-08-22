# Hee

Hee is a private, local-first companion bot for supportive conversations, now supporting hybrid local/cloud orchestration.

It runs on your computer with:

- `Streamlit` for the UI
- `Python` for orchestration
- `Ollama` for local chat and embeddings
- `OpenAI GPT API` for cloud-based chat and embeddings
- `SQLite` for local memory storage
- `Continual Memory Architecture` for dynamic user state modeling

## Architecture

```text
Browser (Streamlit)
        |
        v
Python bot orchestration
  - conversation handling
  - emotion / intent analysis
  - memory management (ADD, UPDATE, MERGE, KEEP, FORGET)
        |
   +----+-------------------+
   |         |              |
   v         v              v
Ollama     OpenAI         SQLite
Qwen       GPT-4o         messages + memories
```

## Features

- **Hybrid Chat Modes**:
  - Local chat with `qwen2.5:7b` via Ollama.
  - Cloud chat with `gpt-4o` via OpenAI API.
- **Continual Memory Architecture**:
  - Models user information as evolving **Semantic**, **Episodic**, and **Temporal** states.
  - Uses a lightweight memory-management logic to perform **ADD**, **UPDATE**, **MERGE**, **KEEP**, and **FORGET** operations.
  - Resolves conflicts between new observations and existing memories.
- **Explicit Memory Controls**:
  - `/remember I prefer being comforted before advice`
  - `/forget 3`
  - `/memory`
- **Memory Policy**:
  - Prefers long-term preferences, important life events, and recurring goals.
  - Memory retrieval based on semantic similarity using local or cloud embeddings.

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

3. (Optional) Start Ollama and pull the local models:

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
ollama serve
```

4. (Optional) Configure OpenAI API in your `.env` file:
```bash
OPENAI_API_KEY=your_key_here
```

5. Run the app:

```bash
streamlit run app.py
```

## Data Storage

- By default, Hee stores its SQLite database outside the project directory.
- macOS default: `~/Library/Application Support/Hee/hee_bot.db`
- Linux default: `~/.local/share/Hee/hee_bot.db`
- Windows default: `%APPDATA%\Hee\hee_bot.db`
- In restricted environments that cannot write outside the workspace, Hee falls back to `.hee-data/hee_bot.db`.

## Environment Variables

Optional configuration:

```bash
# Ollama Settings
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_CHAT_MODEL=qwen2.5:7b
export OLLAMA_EMBED_MODEL=nomic-embed-text

# OpenAI Settings
export OPENAI_API_KEY=your_api_key
export OPENAI_CHAT_MODEL=gpt-4o
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Storage & Policy Settings
export HEE_DATA_DIR="$HOME/Library/Application Support/Hee"
export HEE_SQLITE_PATH="$HEE_DATA_DIR/hee_bot.db"
export HEE_MAX_HISTORY_MESSAGES=12
export HEE_MAX_MEMORIES=4
export HEE_MEMORY_SCORE_THRESHOLD=0.35
```

## Memory Policy

Hee implements a **Continual Memory Architecture** to ensure your personal assistant grows with you.

### Operations
- **ADD**: Captures new, durable information.
- **UPDATE**: Refines existing memories with new context.
- **MERGE**: Consolidates related memory fragments into cohesive concepts.
- **FORGET**: Removes outdated or conflicting information.

### Memory Types
- **Semantic**: General facts and stable preferences.
- **Episodic**: Specific life events and experiences.
- **Temporal**: Time-based patterns and evolving habits.

## Notes

- All memory stays in the local SQLite database you configure.
- If Ollama is not reachable, Hee falls back safely and returns an actionable error message instead of crashing.
- The app uses Ollama's local embedding API for semantic memory search.

## Release Notes

| Version | Date | Feature Update | Description |
| :--- | :--- | :--- | :--- |
| **v1.2.0** | 2026-08-22 | **Continual Memory Architecture** | Implemented evolving state modeling (Semantic, Episodic, Temporal) with dynamic operations (ADD, UPDATE, MERGE, FORGET) for conflict resolution. |
| **v1.1.0** | 2026-08-21 | **Hybrid GPT-4o Support** | Integrated OpenAI API for cloud-based chat and embeddings, allowing seamless switching between local Ollama and cloud GPT models. |
| **v1.0.0** | 2026-08-20 | **Initial Release** | Core local-first companion bot with Ollama (Qwen) support, SQLite storage, and basic semantic memory retrieval. |
