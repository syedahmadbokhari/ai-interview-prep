"""Compatibility function for project/entity validation."""

from __future__ import annotations

from rag_assertions import ValidationContext
from rag_assertions.assertions import ProjectExistsAssertion

from .models import EvidenceItem


def assert_project_exists(
    answer: str,
    evidence: list[EvidenceItem],
    project_registry: list[str],
    question: str = "",
):
    return ProjectExistsAssertion().validate(
        answer,
        evidence,
        ValidationContext(known_entities=tuple(project_registry), question=question),
    )
