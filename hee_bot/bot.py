"""Core bot logic for Hee."""

from __future__ import annotations

from typing import Any, Dict

from hee_bot.database import Database
from hee_bot.memory_manager import MemoryManager
from hee_bot.ollama_client import OllamaClient
from hee_bot.config import DATABASE_PATH
from hee_bot.models import MemoryRecord
from hee_bot.ollama_client import OllamaError


class LocalCompanionBot:
    def __init__(self, db_path: str = DATABASE_PATH) -> None:
        self.db = Database(db_path)
        self.db.initialize()
        self.llm_client = OllamaClient()
        self.memory_manager = MemoryManager(self.llm_client)

    def handle_input(self, user_input: str, space_id: int) -> Dict[str, Any]:
        user_input = user_input.strip()
        if not user_input:
            return {"reply": "Tell me what is on your mind."}
        # Simple command handling
        if user_input.startswith("/"):
            return self._handle_command(user_input, space_id)

        # Regular chat
        relevant_memories = self.db.find_memories(space_id, user_input)
        context = "\n".join([mem.content for mem in relevant_memories])

        prompt = (
            f"You are Hee, a local-first AI companion. "
            f"Your user is talking to you. Here are some relevant memories:\n{context}"
            f"\n\nUser: {user_input}"
        )

        # Generate response
        messages = [{"role": "system", "content": prompt}]
        try:
            response = self.llm_client.chat(messages)
        except OllamaError:
            return {"reply": "I couldn't reach the local AI model. Start Ollama and run `ollama pull mistral`, then try again. You can still save memories with /remember."}

        # Update memories
        self._update_memories(user_input, space_id, relevant_memories)

        return {"reply": response}

    def _handle_command(self, command: str, space_id: int) -> Dict[str, Any]:
        parts = command.split(" ", 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/remember":
            args = args.strip()
            if not args:
                return {"reply": "Use /remember followed by the information to save."}
            memory_record = MemoryRecord(
                id=0,
                memory_type="semantic",
                content=args,
                source_message=f"Manual entry via {command}",
            )
            self.db.add_memory(space_id, memory_record)
            return {"reply": f"I will remember: {args}"}

        elif cmd == "/clear":
            # This is a simplistic implementation. A real one would be more careful.
            memories = self.db.find_memories(space_id, "")
            for mem in memories:
                self.db.delete_memory(mem.id)
            return {"reply": "I have cleared my memories for this space."}

        return {"reply": "Unknown command. Try /remember or /clear."}

    def _update_memories(
        self, user_input: str, space_id: int, relevant_memories: list
    ) -> None:
        # Simplified: just add a new memory for now
        # A real implementation would use the MemoryManager to decide
        # whether to ADD, UPDATE, MERGE, etc.
        self.db.add_memory(
            space_id,
            MemoryRecord(id=0, memory_type="episodic", content=user_input, source_message=user_input),
        )
