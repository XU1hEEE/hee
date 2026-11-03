"""Core data models for Hee."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryRecord:
    """Represents a single memory unit."""
    id: int
    memory_type: str
    content: str
    source_message: Optional[str] = None
    last_updated_at: Optional[str] = None


@dataclass
class EnrichedMemoryRecord:
    """A memory record with additional context, like its history."""
    id: int
    memory_type: str
    content: str
    space_id: int
    space_name: str
    created_at: str
    source_message: Optional[str] = None
    last_updated_at: Optional[str] = None
    history: Optional[str] = None


@dataclass
class MemorySpace:
    """Represents a container for memories."""
    id: int
    name: str
    description: str
    created_at: str