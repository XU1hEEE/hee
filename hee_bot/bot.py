"""Core orchestration for the local-first companion bot."""

from __future__ import annotations

import json
import math
from typing import Any

from hee_bot.config import SETTINGS
from hee_bot.database import BotDatabase
from hee_bot.models import AnalysisResult, MemoryRecord
from hee_bot.ollama_client import OllamaClient, OllamaError
from hee_bot.openai_client import OpenAIClient, OpenAIError


SYSTEM_PROMPT = """You are Hee, a private local-first emotional support companion for Marina.

Your style:
- warm, calm, and grounded
- validate feelings before jumping into advice
- ask one gentle follow-up question when helpful
- never sound clinical unless the user asks for that style
- keep responses concise but thoughtful

Safety:
- do not claim to be a therapist
- if there is clear self-harm or crisis intent, encourage immediate human help and emergency resources
- do not invent memories; only use provided memory snippets when relevant

Memory policy:
- treat long-term preferences, important life events, recurring goals, and explicitly requested memories as durable
- avoid storing transient emotions or sensitive details unless the user explicitly asks to remember them
"""


ANALYSIS_PROMPT = """Analyze the user's latest message for supportive conversation memory policy.
Return strict JSON with keys:
- emotion: short label
- intent: short label
- should_store: true or false
- memory_candidate: one sentence max, empty string if nothing should be stored
- reasoning: short explanation

Remember only if it is a durable preference, important event, recurring concern, recurring goal, or explicit remember request.
Avoid storing transient moods, highly sensitive details, or everyday filler.
"""


class LocalCompanionBot:
    def __init__(self, provider: str = "ollama") -> None:
        self.db = BotDatabase(SETTINGS.sqlite_path)
        self.provider = provider
        if provider == "openai":
            self.llm = OpenAIClient()
        else:
            self.llm = OllamaClient()

    def handle_input(self, user_input: str) -> dict[str, Any]:
        normalized = user_input.strip()
        if not normalized:
            return {"reply": "Tell me what is on your mind.", "command": "empty"}

        if normalized.startswith("/remember "):
            memory_text = normalized[len("/remember ") :].strip()
            return self._remember(memory_text, source="explicit_command", category="explicit_preference")

        if normalized.startswith("/forget "):
            target = normalized[len("/forget ") :].strip()
            return self._forget(target)

        if normalized == "/memory":
            memories = self.db.list_memories(limit=20)
            return {"reply": self._format_memory_list(memories), "command": "memory"}

        if normalized == "/help":
            return {"reply": self._help_text(), "command": "help"}

        self.db.add_message("user", normalized)
        analysis = self._analyze_message(normalized)
        memories = self._retrieve_relevant_memories(normalized)
        reply = self._generate_reply(normalized, analysis, memories)
        self.db.add_message("assistant", reply)

        stored_memory = None
        if analysis.should_store and analysis.memory_candidate:
            stored_memory = self._remember(
                analysis.memory_candidate,
                source="policy_auto",
                category=analysis.intent,
                persist_message=False,
            )

        response: dict[str, Any] = {
            "reply": reply,
            "command": "chat",
            "analysis": analysis,
            "memories": memories,
        }
        if stored_memory:
            response["memory_update"] = stored_memory["reply"]
        return response

    def _help_text(self) -> str:
        return (
            "Commands:\n"
            "/remember <text> - save a long-term preference or important fact\n"
            "/forget <id or text> - delete a memory by id or matching text\n"
            "/memory - list saved memories\n"
            "/help - show commands"
        )

    def _remember(
        self,
        memory_text: str,
        source: str,
        category: str,
        persist_message: bool = True,
    ) -> dict[str, str]:
        if not memory_text:
            return {"reply": "There is nothing to remember yet.", "command": "remember"}

        embedding = self.llm.embed(memory_text)
        memory_id = self.db.add_memory(
            category=category,
            content=memory_text,
            source=source,
            embedding=embedding,
        )
        if persist_message:
            self.db.add_message("assistant", f"Stored memory #{memory_id}: {memory_text}")
        return {
            "reply": f"Stored memory #{memory_id}: {memory_text}",
            "command": "remember",
        }

    def _forget(self, target: str) -> dict[str, str]:
        if not target:
            return {"reply": "Tell me which memory to forget.", "command": "forget"}

        if target.isdigit():
            deleted = self.db.delete_memory(int(target))
            if deleted:
                return {"reply": f"Forgot memory #{target}.", "command": "forget"}
            return {"reply": f"I could not find memory #{target}.", "command": "forget"}

        memories = self.db.list_memories(limit=100)
        for memory in memories:
            if target.lower() in memory.content.lower():
                self.db.delete_memory(memory.id)
                return {
                    "reply": f"Forgot memory #{memory.id}: {memory.content}",
                    "command": "forget",
                }
        return {"reply": "I could not find a matching memory to forget.", "command": "forget"}

    def _format_memory_list(self, memories: list[MemoryRecord]) -> str:
        if not memories:
            return "No long-term memories saved yet."
        lines = ["Saved memories:"]
        for memory in memories:
            lines.append(f"#{memory.id} [{memory.category}] {memory.content}")
        return "\n".join(lines)

    def _analyze_message(self, user_input: str) -> AnalysisResult:
        messages = [
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": user_input},
        ]
        try:
            raw = self.llm.chat(messages, temperature=0.1)
            payload = self._extract_json(raw)
            return AnalysisResult.from_payload(payload)
        except (OllamaError, OpenAIError, ValueError, json.JSONDecodeError):
            return self._fallback_analysis(user_input)

    def _generate_reply(
        self,
        user_input: str,
        analysis: AnalysisResult,
        memories: list[MemoryRecord],
    ) -> str:
        history = self.db.get_recent_messages(limit=SETTINGS.max_history_messages)
        memory_block = self._render_memory_context(memories)
        analysis_block = (
            f"Emotion: {analysis.emotion}\n"
            f"Intent: {analysis.intent}\n"
            f"Memory recommendation: {analysis.memory_candidate or 'none'}"
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[:-1])
        messages.append(
            {
                "role": "system",
                "content": (
                    "Relevant memory context:\n"
                    f"{memory_block}\n\n"
                    "Conversation analysis:\n"
                    f"{analysis_block}"
                ),
            }
        )
        messages.append({"role": "user", "content": user_input})
        try:
            return self.llm.chat(messages, temperature=0.5)
        except (OllamaError, OpenAIError) as exc:
            provider_name = "OpenAI" if self.provider == "openai" else "Ollama"
            model_name = SETTINGS.openai_chat_model if self.provider == "openai" else SETTINGS.chat_model
            return (
                f"I couldn't reach {provider_name} just now. "
                f"Check your settings and that model '{model_name}' is available. "
                f"Details: {exc}"
            )

    def _retrieve_relevant_memories(self, user_input: str) -> list[MemoryRecord]:
        try:
            query_embedding = self.llm.embed(user_input)
        except (OllamaError, OpenAIError):
            return []

        scored: list[MemoryRecord] = []
        for row in self.db.search_memories():
            score = self._cosine_similarity(query_embedding, list(row["embedding"]))
            if score >= SETTINGS.memory_score_threshold:
                scored.append(
                    MemoryRecord(
                        id=int(row["id"]),
                        category=str(row["category"]),
                        content=str(row["content"]),
                        source=str(row["source"]),
                        created_at=str(row["created_at"]),
                        score=score,
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: SETTINGS.max_memories]

    def _render_memory_context(self, memories: list[MemoryRecord]) -> str:
        if not memories:
            return "No relevant memories."
        return "\n".join(
            f"- ({memory.category}, score={memory.score:.2f}) {memory.content}"
            for memory in memories
        )

    def _fallback_analysis(self, user_input: str) -> AnalysisResult:
        lowered = user_input.lower()
        should_store = False
        intent = "general_support"
        emotion = "unknown"
        candidate = ""

        if any(token in lowered for token in ("stress", "stressed", "anxious", "worried", "overwhelmed")):
            emotion = "stressed"
        elif any(token in lowered for token in ("sad", "down", "upset", "lonely")):
            emotion = "sad"
        elif any(token in lowered for token in ("happy", "excited", "proud", "relieved")):
            emotion = "positive"

        if lowered.startswith("remember ") or "please remember" in lowered:
            should_store = True
            intent = "explicit_memory"
            candidate = user_input.removeprefix("remember ").strip()
        elif any(token in lowered for token in ("i prefer", "i like", "i don't like", "i do not like")):
            should_store = True
            intent = "preference"
            candidate = user_input.strip()
        elif any(token in lowered for token in ("my goal", "i want to", "i'm trying to", "training results")):
            should_store = True
            intent = "recurring_goal"
            candidate = user_input.strip()

        return AnalysisResult(
            emotion=emotion,
            intent=intent,
            should_store=should_store,
            memory_candidate=candidate,
            reasoning="Fallback heuristic analysis.",
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in analysis response.")
        return json.loads(text[start : end + 1])

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
