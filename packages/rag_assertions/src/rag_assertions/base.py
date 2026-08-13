"""Public assertion interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from .models import AssertionResult, EvidenceItem, ValidationContext


class AssertionProtocol(Protocol):
    """Protocol implemented by all assertions accepted by AssertionRunner."""

    name: str

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        """Validate an answer against supplied evidence."""


class BaseAssertion:
    """Convenience base class for custom deterministic assertions."""

    name = "base"
    severity = "error"

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        """Validate an answer. Subclasses must override this method."""

        raise NotImplementedError

    def pass_result(
        self,
        claim: str,
        reason: str,
        evidence: Sequence[EvidenceItem] | None = None,
        *,
        skipped: bool = False,
    ) -> AssertionResult:
        """Create a passing or skipped result for this assertion."""

        return AssertionResult(
            assertion=self.name,
            passed=True,
            claim=claim,
            reason=reason,
            evidence=list(evidence or []),
            severity=self.severity,
            skipped=skipped,
        )

    def fail_result(
        self,
        claim: str,
        reason: str,
        evidence: Sequence[EvidenceItem] | None = None,
    ) -> AssertionResult:
        """Create a failing result for this assertion."""

        return AssertionResult(
            assertion=self.name,
            passed=False,
            claim=claim,
            reason=reason,
            evidence=list(evidence or []),
            severity=self.severity,
        )
