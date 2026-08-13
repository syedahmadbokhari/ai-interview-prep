"""Compatibility function for scope grounding."""

from __future__ import annotations

from rag_assertions import ValidationContext
from rag_assertions.assertions import ScopeBoundedAssertion

from .models import EvidenceItem


def assert_scope_bounded(
    answer: str,
    evidence: list[EvidenceItem],
    project_registry: list[str],
):
    return ScopeBoundedAssertion().validate(
        answer,
        evidence,
        ValidationContext(known_entities=tuple(project_registry)),
    )
