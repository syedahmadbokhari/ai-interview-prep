"""Typed public models for deterministic grounding validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

JsonDict = dict[str, Any]


class AssertionStatus(str, Enum):
    """Machine-readable assertion status."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class EvidenceItem:
    """A piece of retrieved evidence used to validate an LLM answer.

    The model is framework-agnostic: evidence can come from FAISS, Chroma,
    Pinecone, pgvector, Elasticsearch, files, or any custom retriever.
    """

    text: str
    source: str | None = None
    entity: str | None = None
    chunk_id: str | None = None
    score: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def citation(self) -> str:
        """Compatibility-friendly citation string."""

        return self.source or str(self.metadata.get("citation", ""))

    @property
    def project(self) -> str | None:
        """Compatibility alias for applications that use project terminology."""

        return self.entity or self.metadata.get("project")

    def to_dict(self) -> JsonDict:
        """Return a JSON-compatible dictionary."""

        return {
            "text": self.text,
            "source": self.source,
            "entity": self.entity,
            "chunk_id": self.chunk_id,
            "score": self.score,
            "metadata": dict(self.metadata),
            "citation": self.citation,
            "project": self.project,
        }


@dataclass(frozen=True)
class ValidationContext:
    """Optional context shared by assertions during one validation run."""

    known_entities: tuple[str, ...] = ()
    question: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssertionResult:
    """Result from a single assertion."""

    assertion: str
    passed: bool
    claim: str
    reason: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    severity: str = "error"
    skipped: bool = False

    @property
    def status(self) -> AssertionStatus:
        """Return PASS, FAIL, or SKIP."""

        if self.skipped:
            return AssertionStatus.SKIP
        return AssertionStatus.PASS if self.passed else AssertionStatus.FAIL

    @property
    def project(self) -> str | None:
        """Compatibility alias for older application code."""

        return self.metadata.get("project") or self.metadata.get("entity")

    def to_dict(self) -> JsonDict:
        """Return a JSON-compatible dictionary."""

        data = asdict(self)
        data["status"] = self.status.value
        data["evidence"] = [item.to_dict() for item in self.evidence]
        data["metadata"] = dict(self.metadata)
        data["project"] = self.project
        return data


@dataclass(frozen=True)
class ValidationResult:
    """Aggregate validation result from an AssertionRunner."""

    results: list[AssertionResult]

    @property
    def passed(self) -> bool:
        """True when no non-skipped assertion failed."""

        return self.failed_count == 0

    @property
    def all_passed(self) -> bool:
        """Compatibility alias for passed."""

        return self.passed

    @property
    def checks_run(self) -> int:
        """Number of assertions that were not skipped."""

        return sum(1 for result in self.results if not result.skipped)

    @property
    def passed_count(self) -> int:
        """Number of non-skipped passing assertions."""

        return sum(1 for result in self.results if result.passed and not result.skipped)

    @property
    def failed_count(self) -> int:
        """Number of non-skipped failing assertions."""

        return sum(1 for result in self.results if not result.passed and not result.skipped)

    @property
    def skipped_count(self) -> int:
        """Number of skipped assertions."""

        return sum(1 for result in self.results if result.skipped)

    @property
    def failures(self) -> list[AssertionResult]:
        """Failing assertion results."""

        return [result for result in self.results if not result.passed and not result.skipped]

    @property
    def failed(self) -> list[AssertionResult]:
        """Compatibility alias for failures."""

        return self.failures

    def to_dict(self) -> JsonDict:
        """Return a JSON-compatible dictionary."""

        return {
            "passed": self.passed,
            "all_passed": self.all_passed,
            "checks_run": self.checks_run,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "results": [result.to_dict() for result in self.results],
        }
