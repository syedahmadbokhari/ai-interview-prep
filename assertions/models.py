"""Compatibility exports for the extracted rag_assertions package."""

from __future__ import annotations

from typing import Any, Mapping

from rag_assertions import AssertionResult, ValidationContext, ValidationResult
from rag_assertions import EvidenceItem as _EvidenceItem


class EvidenceItem(_EvidenceItem):
    """Backward-compatible EvidenceItem accepting the old positional order."""

    def __init__(
        self,
        citation: str,
        project: str | None,
        text: str,
        score: float | None = None,
        tool_name: str | None = None,
        query: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        merged_metadata = dict(metadata or {})
        if tool_name is not None:
            merged_metadata["tool_name"] = tool_name
        if query is not None:
            merged_metadata["query"] = query
        super().__init__(
            text=text,
            source=citation,
            entity=project,
            score=score,
            metadata=merged_metadata,
        )


__all__ = [
    "AssertionResult",
    "EvidenceItem",
    "ValidationContext",
    "ValidationResult",
]
