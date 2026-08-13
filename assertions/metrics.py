"""Compatibility function for metric grounding."""

from __future__ import annotations

from rag_assertions import ValidationContext
from rag_assertions.assertions import MetricsGroundedAssertion

from .models import EvidenceItem


def assert_metrics_grounded(
    answer: str,
    evidence: list[EvidenceItem],
    project_registry: list[str],
):
    return MetricsGroundedAssertion().validate(
        answer,
        evidence,
        ValidationContext(known_entities=tuple(project_registry)),
    )
