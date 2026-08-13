"""Compatibility function for date grounding."""

from __future__ import annotations

from rag_assertions import ValidationContext
from rag_assertions.assertions import NoFabricatedDatesAssertion

from .models import EvidenceItem


def assert_no_fabricated_dates(
    answer: str,
    evidence: list[EvidenceItem],
    project_registry: list[str],
):
    return NoFabricatedDatesAssertion().validate(
        answer,
        evidence,
        ValidationContext(known_entities=tuple(project_registry)),
    )
