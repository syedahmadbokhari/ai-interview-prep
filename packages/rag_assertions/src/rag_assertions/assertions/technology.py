"""Technology/tool grounding assertion."""

from __future__ import annotations

import re
from collections.abc import Sequence

from rag_assertions.base import BaseAssertion
from rag_assertions.models import AssertionResult, EvidenceItem, ValidationContext

TECH_STOPWORDS = {
    "Answer",
    "Business",
    "Data",
    "Platform",
    "Project",
    "Question",
    "Sources",
    "That",
    "The",
    "This",
}

TECH_HINTS = re.compile(
    r"\b(uses?|used|built with|stack|technology|technologies|tool|tools|via|on top of)\b",
    re.IGNORECASE,
)


class TechnologyGroundedAssertion(BaseAssertion):
    """Validate that technology/tool claims appear in supplied evidence."""

    name = "technology_grounded"

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        claims = _technology_claims(answer)
        if not claims:
            return self.pass_result(
                "no technology claim detected",
                "No technology/tool claim was detected.",
                skipped=True,
            )

        failures = []
        support: list[EvidenceItem] = []
        for tech in claims:
            matched = _evidence_for_term(tech, evidence)
            if matched:
                support.extend(matched[:2])
            else:
                failures.append(tech)

        if failures:
            return self.fail_result(
                ", ".join(failures),
                "Claimed technology was not found in the supplied evidence.",
                support[:5],
            )

        return self.pass_result(
            ", ".join(claims),
            "Claimed technologies appear in supplied evidence.",
            support[:5],
        )


class TechStackGroundedAssertion(TechnologyGroundedAssertion):
    """Compatibility name used by the Interview Prep Assistant."""

    name = "tech_stack_grounded"


def _technology_claims(answer: str) -> list[str]:
    claims: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        if not TECH_HINTS.search(sentence):
            continue
        candidates = re.findall(
            r"\b(?:[A-Z][A-Za-z0-9.+#-]{1,}|[A-Z]{2,}[A-Za-z0-9.+#-]*)\b",
            sentence,
        )
        for candidate in candidates:
            cleaned = candidate.strip(".,;:()[]")
            if cleaned in TECH_STOPWORDS or cleaned.lower() in {"sources"}:
                continue
            if cleaned not in claims:
                claims.append(cleaned)
    return claims


def _evidence_for_term(term: str, evidence: Sequence[EvidenceItem]) -> list[EvidenceItem]:
    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    return [item for item in evidence if pattern.search(item.text)]
