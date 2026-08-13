"""Deterministic assertion runner."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .assertions import (
    MetricsGroundedAssertion,
    NoFabricatedDatesAssertion,
    ProjectExistsAssertion,
    ScopeBoundedAssertion,
    TechStackGroundedAssertion,
)
from .base import AssertionProtocol
from .models import AssertionResult, EvidenceItem, ValidationContext, ValidationResult


@dataclass
class AssertionRunner:
    """Run a deterministic set of assertions over an answer and evidence.

    The runner does not call LLMs, retrievers, or provider SDKs. Applications
    own generation, retrieval, retry, refusal, logging, and UI behavior.
    """

    assertions: list[AssertionProtocol] = field(default_factory=list)
    disabled_assertions: set[str] = field(default_factory=set)
    raise_on_error: bool = False

    def __post_init__(self) -> None:
        if not self.assertions:
            self.assertions = [
                ProjectExistsAssertion(),
                TechStackGroundedAssertion(),
                MetricsGroundedAssertion(),
                NoFabricatedDatesAssertion(),
                ScopeBoundedAssertion(),
            ]
        names = [_canonical_name(assertion.name) for assertion in self.assertions]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"Duplicate assertion names are not allowed: {', '.join(duplicates)}")

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem] | None = None,
        context: ValidationContext | None = None,
        *,
        retrieved_context: Sequence[EvidenceItem] | None = None,
        project_registry: Sequence[str] | None = None,
        question: str = "",
    ) -> ValidationResult:
        """Validate an answer.

        `retrieved_context` and `project_registry` are compatibility keyword
        aliases for the Interview Prep Assistant and older callers.
        """

        actual_evidence = list(evidence if evidence is not None else retrieved_context or [])
        actual_context = context or ValidationContext(
            known_entities=tuple(project_registry or ()),
            question=question,
        )
        disabled = {_canonical_name(name) for name in self.disabled_assertions}

        results = []
        for assertion in self.assertions:
            name = _canonical_name(assertion.name)
            try:
                result = assertion.validate(answer, actual_evidence, actual_context)
            except Exception as exc:
                if self.raise_on_error:
                    raise
                result = AssertionResult(
                    assertion=assertion.name,
                    passed=False,
                    claim="assertion execution error",
                    reason=f"{type(exc).__name__}: {exc}",
                    metadata={"error_type": type(exc).__name__},
                )
            if name in disabled:
                result = AssertionResult(
                    assertion=result.assertion,
                    passed=True,
                    claim=result.claim,
                    reason="Assertion disabled for this evaluation run.",
                    evidence=result.evidence,
                    metadata=result.metadata,
                    severity=result.severity,
                    skipped=True,
                )
            results.append(result)
        return ValidationResult(results)


def _canonical_name(name: str) -> str:
    aliases = {
        "date": "no_fabricated_dates",
        "dates": "no_fabricated_dates",
        "dates_grounded": "no_fabricated_dates",
        "entity": "project_exists",
        "entity_exists": "project_exists",
        "metric": "metrics_grounded",
        "metrics": "metrics_grounded",
        "project": "project_exists",
        "scope": "scope_bounded",
        "tech": "tech_stack_grounded",
        "technology": "tech_stack_grounded",
        "technology_grounded": "tech_stack_grounded",
    }
    return aliases.get(name, name)
