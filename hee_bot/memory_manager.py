"""Memory management logic for continual learning."""

from __future__ import annotations

import json
from typing import Any, List, Optional
from dataclasses import dataclass
from hee_bot.models import MemoryRecord

MEMORY_MANAGEMENT_PROMPT = """You are a lightweight memory management unit for a local AI companion.
Your task is to manage long-term user memories based on new observations.

Operations:
- ADD: Create a new memory if the information is new and durable.
- UPDATE: Update an existing memory if the new info refines or changes it.
- MERGE: Combine multiple related memories into a single cohesive one.
- KEEP: Do nothing if the existing memory is still accurate and sufficient.
- FORGET: Remove a memory if it's outdated, incorrect, or superseded.

Memory Types:
- semantic: General facts, preferences, and concepts (e.g., "Marina likes tea").
- episodic: Specific events or experiences (e.g., "Marina had a busy day at work on 2024-05-20").
- temporal: Time-based patterns or evolving states (e.g., "Marina usually feels more creative in the mornings").

Input:
1. New Observation: A candidate memory derived from the latest user message.
2. Existing Relevant Memories: A list of potentially related memories.

Output:
Return a JSON list of operations to perform. Each operation should have:
- op: "ADD", "UPDATE", "MERGE", "KEEP", or "FORGET"
- memory_type: "semantic", "episodic", or "temporal"
- content: The updated or new content (for ADD, UPDATE, MERGE)
- target_id: The ID of the memory to update, forget, or one of the IDs to merge.
- merge_ids: A list of IDs to merge (only for MERGE).
- reasoning: Why this operation is performed.

Focus on conflict resolution and selective consolidation. If new info contradicts old info, prefer UPDATE or FORGET for the old info.
"""

@dataclass
class MemoryOperation:
    op: str
    memory_type: str
    content: str
    reasoning: str
    target_id: Optional[int] = None
    merge_ids: Optional[List[int]] = None

class MemoryManager:
    def __init__(self, llm_client: Any) -> None:
        self.llm = llm_client

    def plan_operations(
        self, 
        observation: str, 
        relevant_memories: list[MemoryRecord]
    ) -> list[MemoryOperation]:
        if not observation:
            return []

        memories_str = "\n".join([
            f"ID: {m.id}, Type: {m.memory_type}, Content: {m.content}"
            for m in relevant_memories
        ])

        prompt = (
            f"New Observation: {observation}\n\n"
            f"Existing Relevant Memories:\n{memories_str or 'None'}\n\n"
            "Plan memory operations:"
        )

        messages = [
            {"role": "system", "content": MEMORY_MANAGEMENT_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            raw = self.llm.chat(messages, temperature=0.1)
            payload = self._extract_json(raw)
            if isinstance(payload, dict):
                payload = [payload]
            
            ops = []
            for item in payload:
                ops.append(MemoryOperation(
                    op=item.get("op", "KEEP"),
                    memory_type=item.get("memory_type", "semantic"),
                    content=item.get("content", ""),
                    target_id=item.get("target_id"),
                    merge_ids=item.get("merge_ids"),
                    reasoning=item.get("reasoning", ""),
                ))
            return ops
        except Exception:
            # Fallback to ADD if anything fails, provided we have an observation
            return [MemoryOperation(
                op="ADD",
                memory_type="semantic",
                content=observation,
                reasoning="Fallback to ADD due to processing error."
            )]

    def _extract_json(self, text: str) -> Any:
        start = text.find("[")
        if start == -1:
            start = text.find("{")
        
        end = text.rfind("]")
        if end == -1:
            end = text.rfind("}")
            
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON found")
            
        return json.loads(text[start : end + 1])
