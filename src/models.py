from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class DocumentSection:
    """Extracted logical section of a source document."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TextChunk:
    """Chunk ready to be embedded and indexed."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Chunk returned by semantic search."""

    text: str
    metadata: dict[str, Any]
    distance: float


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Human-readable reference attached to an answer."""

    source: str
    category: str
    location: str
    citation_id: int = 1
    source_path: str = ""
    excerpt: str = ""
    distance: float = 0.0


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """Final answer plus traceable source references."""

    answer: str
    sources: tuple[SourceReference, ...] = ()
