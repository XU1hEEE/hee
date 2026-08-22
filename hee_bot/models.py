"""Data models used across the local bot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryRecord:
    id: int
    category: str
    content: str
    source: str
    created_at: str
    updated_at: str
    memory_type: str  # semantic, episodic, temporal
    score: float = 0.0


@dataclass
class AnalysisResult:
    emotion: str
    intent: str
    should_store: bool
    memory_candidate: str
    reasoning: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AnalysisResult":
        return cls(
            emotion=str(payload.get("emotion", "unknown")).strip() or "unknown",
            intent=str(payload.get("intent", "general_support")).strip() or "general_support",
            should_store=bool(payload.get("should_store", False)),
            memory_candidate=str(payload.get("memory_candidate", "")).strip(),
            reasoning=str(payload.get("reasoning", "")).strip(),
        )
