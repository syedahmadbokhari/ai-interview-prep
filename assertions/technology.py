"""Compatibility function for technology grounding."""

from __future__ import annotations

from rag_assertions import ValidationContext
from rag_assertions.assertions import TechStackGroundedAssertion

from .models import EvidenceItem


def assert_tech_stack_grounded(
    answer: str,
    evidence: list[EvidenceItem],
    project_registry: list[str],
):
    return TechStackGroundedAssertion().validate(
        answer,
        evidence,
        ValidationContext(known_entities=tuple(project_registry)),
    )
